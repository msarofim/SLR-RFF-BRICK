#!/usr/bin/env python3
"""
ENSEMBLE SSP GMSL projections to 2100 — v2.0.0 posterior band + recalibration shift.

The v2.0.0 ensemble (real 10k-draw posterior) is the robust uncertainty band and
smooths the single-draw DAIS-MICI step. The "new" (preliminary recalibration) is
shown as a MEDIAN-ONLY shift: its central knobs are applied ensemble-wide, which
shifts the median sensibly but DISTORTS the tails (e.g. SSP1-1.9 new p05 14.9 cm is
an artifact of forcing central gsic_v0/teq/te_alpha onto draws they don't suit), so
its band is not a clean posterior and is not drawn. A proper new-calibration band
needs the recalibration re-fit per draw.

Panels:
  (a) total GMSL @2100 by SSP: v2.0.0 median + 5-95 band, new median marker, vs AR6;
  (b) v2.0.0 ensemble trajectories 2000-2100 with 5-95 bands;
  (c) recalibration effect on the MEDIAN (new p50 - v2.0.0 p50) per SSP.

Inputs: outputs/proj_ssps_ensemble_{summary,timeseries}.csv (cm, rel AR6 1995-2014).
"""
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
AR6 = {"SSP1-1.9": 38, "SSP1-2.6": 44, "SSP2-4.5": 56, "SSP3-7.0": 68, "SSP5-8.5": 77}

def row(ssp, cal):
    return S[(S.ssp_label == ssp) & (S.calib == cal)].iloc[0]

fig, (axa, axb, axc) = plt.subplots(1, 3, figsize=(18, 5.6))
x = np.arange(len(ORDER))

# ---- (a) v2.0.0 median bar + 5-95 band; new median marker; AR6 ----
p50 = [row(s, "v2.0.0").p50 for s in ORDER]
lo = [row(s, "v2.0.0").p50 - row(s, "v2.0.0").p05 for s in ORDER]
hi = [row(s, "v2.0.0").p95 - row(s, "v2.0.0").p50 for s in ORDER]
axa.bar(x, p50, 0.6, color="#9aa7b3", label="v2.0.0 median",
        yerr=[lo, hi], capsize=4, error_kw=dict(lw=1.2, ecolor="0.3"))
axa.scatter(x, [row(s, "new").p50 for s in ORDER], marker="D", s=55, color="#1763b8",
            zorder=6, label="new (prelim.) median")
axa.scatter(x, [AR6.get(s, np.nan) for s in ORDER], marker="_", s=460, color="crimson",
            lw=2.5, label="AR6 median (approx)", zorder=6)
for xi, s in enumerate(ORDER):
    axa.text(xi, row(s, "v2.0.0").p95 + 2, f"{row(s,'v2.0.0').p50:.0f}", ha="center", fontsize=8)
axa.set_xticks(x); axa.set_xticklabels(ORDER, rotation=30, ha="right")
axa.set_ylabel("GMSL @2100 (cm, rel 1995-2014)")
axa.set_title(f"(a) Total GMSL @2100  (v2.0.0 median + 5–95%, {NDRAWS:,} draws)")
axa.legend(fontsize=8, loc="upper left"); axa.grid(axis="y", alpha=0.25)

# ---- (b) v2.0.0 ensemble trajectories + bands ----
for s in ORDER:
    d = T[(T.ssp_label == s) & (T.calib == "v2.0.0")].sort_values("year")
    axb.fill_between(d.year, d.p05, d.p95, color=COL[s], alpha=0.13, lw=0)
    axb.plot(d.year, d.p50, color=COL[s], lw=2, label=s)
axb.set_title("(b) GMSL trajectory 2000–2100, v2.0.0 ensemble\n(median + 5–95% band)")
axb.set_xlabel("year"); axb.set_ylabel("GMSL (cm, rel 1995-2014)")
axb.set_xlim(2000, 2100); axb.legend(fontsize=8, ncol=2); axb.grid(alpha=0.25)

# ---- (c) recalibration effect on the median ----
dmed = [row(s, "new").p50 - row(s, "v2.0.0").p50 for s in ORDER]
axc.bar(x, dmed, 0.6, color="#1763b8")
for xi, v in enumerate(dmed):
    axc.text(xi, v + 0.05, f"{v:+.1f}", ha="center", fontsize=8)
axc.axhline(0, color="k", lw=0.6)
axc.set_xticks(x); axc.set_xticklabels(ORDER, rotation=30, ha="right")
axc.set_ylabel("Δ median GMSL @2100 (cm)")
axc.set_title("(c) Recalibration effect on the MEDIAN\n(new − v2.0.0; AIS↑ vs GSIC↓ nearly cancel)")
axc.grid(axis="y", alpha=0.25)

fig.suptitle(f"BRICK GMSL projections to 2100 — {NDRAWS:,}-draw posterior ensemble, FaIR v1.4.5-forced\n"
             "v2.0.0 band is the robust posterior (smooths the DAIS-MICI step); the preliminary "
             "recalibration shifts the MEDIAN only by +0.4 to +2.3 cm (its full band needs a per-draw re-fit)",
             fontsize=10.5)
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(OUT, dpi=140)
print(f"[wrote {OUT}]")
