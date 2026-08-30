#!/usr/bin/env python3
"""
SSP GMSL projections to 2100 — v2.0.0 vs preliminary recalibration (FaIR-forced).

Three panels:
  (a) total GMSL @2100 by SSP, both calibrations, with approx AR6 medians for sanity;
  (b) total GMSL time series 2000-2100, 6 SSPs (new solid, v2.0.0 dashed);
  (c) component breakdown @2100 (new calibration), showing the DAIS MICI jump.

Inputs: outputs/proj_ssps_2100_{summary,timeseries}.csv  (cm, rel AR6 1995-2014).
"""
## ⚠ VINTAGE 2026-08-30: this figure reads a FROZEN 2026-06 input set, so its labels
## (BRICK-Mengel, Mengel 2-tau, calib 1.4.5) correctly describe THAT arm and NOT the
## champion. L21 is the champion (calib 1.6.0 + CMIP7, 3-block glacier R19/SLOWP/FAST,
## 2-basin Greenland). Do not repoint this at a current arm without rewriting the labels.

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
S = pd.read_csv(os.path.join(REPO, "outputs/proj_ssps_2100_summary.csv"))
T = pd.read_csv(os.path.join(REPO, "outputs/proj_ssps_2100_timeseries.csv"))
OUT = os.path.join(REPO, "outputs/ssp_projections_2100.png")

# scenario order (by forcing) + colors
ORDER = ["SSP1-1.9", "SSP1-2.6", "SSP2-4.5", "SSP4-6.0", "SSP3-7.0", "SSP5-8.5"]
COL = dict(zip(ORDER, plt.cm.viridis(np.linspace(0.05, 0.92, len(ORDER)))))
# approx AR6 WG1 medium-confidence GMSL 2100 medians, rel 1995-2014 (cm); SSP4-6.0 not reported
AR6 = {"SSP1-1.9": 38, "SSP1-2.6": 44, "SSP2-4.5": 56, "SSP3-7.0": 68, "SSP5-8.5": 77}

fig, (axa, axb, axc) = plt.subplots(1, 3, figsize=(18, 5.6))

# ---- (a) grouped bars: total @2100 ----
x = np.arange(len(ORDER)); w = 0.38
v20 = [S[(S.ssp_label == s) & (S.calib == "v2.0.0")].total.values[0] for s in ORDER]
new = [S[(S.ssp_label == s) & (S.calib == "new")].total.values[0] for s in ORDER]
axa.bar(x - w/2, v20, w, label="v2.0.0 calibration", color="#9aa7b3")
axa.bar(x + w/2, new, w, label="new (prelim.) calibration", color="#1763b8")
axa.scatter(x, [AR6.get(s, np.nan) for s in ORDER], marker="_", s=420, color="crimson",
            lw=2.5, label="AR6 median (approx)", zorder=5)
for xi, s in enumerate(ORDER):
    axa.text(xi, max(v20[xi], new[xi]) + 2, f"{new[xi]:.0f}", ha="center", fontsize=8)
axa.set_xticks(x); axa.set_xticklabels(ORDER, rotation=30, ha="right")
axa.set_ylabel("GMSL @2100 (cm, rel 1995-2014)")
axa.set_title("(a) Total GMSL @2100 by SSP")
axa.legend(fontsize=8, loc="upper left"); axa.grid(axis="y", alpha=0.25)
axa.axvspan(2.5, 5.5, color="orange", alpha=0.06)
axa.text(4.0, 5, "DAIS MICI threshold\ncrossed (~3 °C)", fontsize=7.5, color="0.3", ha="center")

# ---- (b) time series ----
for s in ORDER:
    for cal, ls, lw, a in [("new", "-", 2.0, 1.0), ("v2.0.0", "--", 1.3, 0.8)]:
        d = T[(T.ssp_label == s) & (T.calib == cal)].sort_values("year")
        axb.plot(d.year, d.total, ls=ls, lw=lw, color=COL[s], alpha=a,
                 label=(s if cal == "new" else None))
axb.set_title("(b) GMSL trajectory 2000-2100\n(solid = new, dashed = v2.0.0)")
axb.set_xlabel("year"); axb.set_ylabel("GMSL (cm, rel 1995-2014)")
axb.set_xlim(2000, 2100); axb.legend(fontsize=8, ncol=2); axb.grid(alpha=0.25)

# ---- (c) component breakdown (new calib) ----
comps = ["te", "gsic", "gis", "lws", "ais"]
clab = {"te": "Thermal exp.", "gsic": "Glaciers", "gis": "Greenland", "lws": "Land water", "ais": "Antarctic"}
ccol = {"te": "#d98a3d", "gsic": "#6db5c9", "gis": "#7fa86b", "lws": "#b0a0c8", "ais": "#c0504d"}
bottom = np.zeros(len(ORDER))
for cp in comps:
    vals = [S[(S.ssp_label == s) & (S.calib == "new")][cp].values[0] for s in ORDER]
    axc.bar(x, vals, 0.6, bottom=bottom, label=clab[cp], color=ccol[cp])
    bottom += np.array(vals)
axc.set_xticks(x); axc.set_xticklabels(ORDER, rotation=30, ha="right")
axc.set_ylabel("contribution @2100 (cm)")
axc.set_title("(c) Component breakdown (new calib.)\nnote Antarctic jump above ~3 °C")
axc.legend(fontsize=8, loc="upper left"); axc.grid(axis="y", alpha=0.25)

fig.suptitle("BRICK GMSL projections to 2100 — v2.0.0 vs preliminary recalibration, FaIR 2.2.4 (calib 1.4.5)-forced (central/medoid draw)\n"
             "CAVEAT: central draw only; the Antarctic MICI threshold (~3 °C) makes the high-end AIS draw-specific — ensemble needed for robust high-end SLR",
             fontsize=10.5)
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(OUT, dpi=140)
print(f"[wrote {OUT}]")
