#!/usr/bin/env python3
"""
ENSEMBLE SSP GMSL projections to 2100 — v2.0.0 posterior, unweighted vs
Dangendorf importance-weighted, + the preliminary-recalibration median shift.

Panels:
  (a) @2100 dot-and-whisker by SSP: v2.0.0 unweighted (median + 5-95), v2.0.0
      Dangendorf-weighted (median + 5-95), new-calib median, AR6 median.
  (b) v2.0.0 unweighted ensemble trajectories 2000-2100 with 5-95 bands.
  (c) two small effects: recalibration on the median (new - v2.0.0) and importance
      weighting on the upper tail (p95 weighted - unweighted).

The "new" (preliminary recalibration) is MEDIAN-ONLY: its central knobs are applied
ensemble-wide, which shifts the median sensibly but distorts the tails, so no band.
The post-#93 posterior is equal-weighted MCMC, so "unweighted" already = posterior;
"dangendorf" additionally importance-weights by per-draw fit to observed historical
GMSL (ESS ~ 600 / 10k). AR6 reports no SSP4-6.0, so that marker is blank.

Inputs: outputs/proj_ssps_ensemble_{summary,timeseries}.csv (cm, rel 1995-2014).
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
S = pd.read_csv(os.path.join(REPO, "outputs/proj_ssps_ensemble_summary.csv"))
T = pd.read_csv(os.path.join(REPO, "outputs/proj_ssps_ensemble_timeseries.csv"))
OUT = os.path.join(REPO, "outputs/ssp_projections_2100_ensemble.png")
NDRAWS = pd.read_csv(os.path.join(REPO, "data/MimiBRICK/parameters_subsample_brick.csv")).shape[0]

ORDER = ["SSP1-1.9", "SSP1-2.6", "SSP2-4.5", "SSP4-6.0", "SSP3-7.0", "SSP5-8.5"]
COL = dict(zip(ORDER, plt.cm.viridis(np.linspace(0.05, 0.92, len(ORDER)))))
AR6 = {"SSP1-1.9": 38, "SSP1-2.6": 44, "SSP2-4.5": 56, "SSP3-7.0": 68, "SSP5-8.5": 77}  # no SSP4-6.0

def get(ssp, cal, wt):
    return S[(S.ssp_label == ssp) & (S.calib == cal) & (S.weighting == wt)].iloc[0]

fig, (axa, axb, axc) = plt.subplots(1, 3, figsize=(18, 5.7))
x = np.arange(len(ORDER))
GREY, TEAL, BLUE, RED = "#8a97a3", "#1b9e8f", "#1763b8", "crimson"

# ---- (a) dot-and-whisker @2100 ----
for s in ORDER:
    xi = ORDER.index(s)
    u = get(s, "v2.0.0", "unweighted"); w = get(s, "v2.0.0", "dangendorf")
    n = get(s, "new", "unweighted")
    # v2.0.0 unweighted (grey, left)
    axa.plot([xi-0.22]*2, [u.p05, u.p95], color=GREY, lw=2.2, solid_capstyle="round", zorder=2)
    axa.plot(xi-0.22, u.p50, "o", color=GREY, ms=7, zorder=3)
    # v2.0.0 Dangendorf-weighted (teal, center)
    axa.plot([xi]*2, [w.p05, w.p95], color=TEAL, lw=2.2, solid_capstyle="round", zorder=2)
    axa.plot(xi, w.p50, "o", color=TEAL, ms=7, zorder=3)
    # new-calib median (blue diamond, right) — median only
    axa.plot(xi+0.22, n.p50, "D", color=BLUE, ms=7, zorder=4)
    # AR6 median (red dash, behind)
    if s in AR6:
        axa.plot([xi-0.30, xi+0.30], [AR6[s]]*2, color=RED, lw=2.5, zorder=1)
    axa.text(xi, u.p95 + 3, f"{u.p50:.0f}", ha="center", fontsize=8, color="0.25")
# legend proxies
import matplotlib.lines as ml
axa.legend(handles=[
    ml.Line2D([], [], color=GREY, marker="o", lw=2.2, label="v2.0.0 unweighted (median, 5–95%)"),
    ml.Line2D([], [], color=TEAL, marker="o", lw=2.2, label="v2.0.0 Dangendorf-weighted (median, 5–95%)"),
    ml.Line2D([], [], color=BLUE, marker="D", lw=0, label="new (prelim.) median — median only"),
    ml.Line2D([], [], color=RED, lw=2.5, label="AR6 median (approx; no SSP4-6.0)"),
], fontsize=7.6, loc="upper left")
axa.set_xticks(x); axa.set_xticklabels(ORDER, rotation=30, ha="right")
axa.set_ylabel("GMSL @2100 (cm, rel 1995-2014)")
axa.set_title(f"(a) Total GMSL @2100  ({NDRAWS:,}-draw posterior; number = unweighted median)")
axa.grid(axis="y", alpha=0.25)

# ---- (b) v2.0.0 unweighted trajectories + bands ----
TU = T[(T.calib == "v2.0.0") & (T.weighting == "unweighted")]
for s in ORDER:
    d = TU[TU.ssp_label == s].sort_values("year")
    axb.fill_between(d.year, d.p05, d.p95, color=COL[s], alpha=0.13, lw=0)
    axb.plot(d.year, d.p50, color=COL[s], lw=2, label=s)
axb.set_title("(b) GMSL trajectory 2000–2100, v2.0.0 ensemble\n(median + 5–95% band)")
axb.set_xlabel("year"); axb.set_ylabel("GMSL (cm, rel 1995-2014)")
axb.set_xlim(2000, 2100); axb.legend(fontsize=8, ncol=2); axb.grid(alpha=0.25)

# ---- (c) small effects: recalibration on median, weighting on p95 ----
d_recal = [get(s, "new", "unweighted").p50 - get(s, "v2.0.0", "unweighted").p50 for s in ORDER]
d_weight = [get(s, "v2.0.0", "dangendorf").p95 - get(s, "v2.0.0", "unweighted").p95 for s in ORDER]
ww = 0.38
axc.bar(x - ww/2, d_recal, ww, color=BLUE, label="recalibration → Δ median (new − v2.0.0)")
axc.bar(x + ww/2, d_weight, ww, color=TEAL, label="Dangendorf wt → Δ p95 (wtd − unwtd)")
axc.axhline(0, color="k", lw=0.6)
axc.set_xticks(x); axc.set_xticklabels(ORDER, rotation=30, ha="right")
axc.set_ylabel("Δ GMSL @2100 (cm)")
axc.set_title("(c) Magnitude of the two adjustments\n(both small vs the MICI-driven spread)")
axc.legend(fontsize=7.6, loc="lower left"); axc.grid(axis="y", alpha=0.25)

fig.suptitle(f"BRICK GMSL projections to 2100 — {NDRAWS:,}-draw posterior ensemble, FaIR 2.2.4 (calib 1.4.5)-forced  ·  "
             "unweighted vs Dangendorf-weighted, + preliminary recalibration (median only)\n"
             "v2.0.0 median runs high vs AR6 for SSP2-4.5+ (median draw crosses DAIS-MICI ~2.7 °C); "
             "weighting trims the upper tail only; recalibration shifts the median by ≤2.3 cm",
             fontsize=10.5)
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(OUT, dpi=140)
print(f"[wrote {OUT}]")
