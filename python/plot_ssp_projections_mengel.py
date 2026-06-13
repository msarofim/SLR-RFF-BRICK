#!/usr/bin/env python3
"""
SSP GMSL projections to 2100 — MCMC-calibrated BRICK-Mengel posterior ensemble.

Successor to plot_ssp_projections_ensemble.py (which plotted the OLD posterior with
a v2.0.0-vs-knob split + Dangendorf weighting). The Mengel MCMC posterior IS the
calibration and is already Dangendorf-conditioned, so there is ONE unweighted band.

Panels:
  (a) @2100 dot-and-whisker by SSP: BRICK-Mengel median + 5-95% PARAMETRIC band,
      vs AR6 median + likely (17-83%) range. The AR6 likely range is shown to make
      explicit that our parametric band (parameter unc. only) is NARROWER than AR6's
      multi-method range — it excludes structural + obs-noise uncertainty.
  (b) ensemble trajectories 2000-2100 with 5-95% bands.
  (c) 2100 component decomposition (median, cm) stacked by SSP.

Inputs: outputs/proj_ssps_mengel_{summary,timeseries}.csv (cm, rel 1995-2014).
Output: outputs/ssp_projections_2100_mengel.png
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.lines as ml

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
S = pd.read_csv(os.path.join(REPO, "outputs/proj_ssps_mengel_summary.csv"))
T = pd.read_csv(os.path.join(REPO, "outputs/proj_ssps_mengel_timeseries.csv"))
OUT = os.path.join(REPO, "outputs/ssp_projections_2100_mengel.png")
NDRAWS = pd.read_csv(os.path.join(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel.csv")).shape[0]

ORDER = ["SSP1-1.9", "SSP1-2.6", "SSP2-4.5", "SSP4-6.0", "SSP3-7.0", "SSP5-8.5"]
COL = dict(zip(ORDER, plt.cm.viridis(np.linspace(0.05, 0.92, len(ORDER)))))
# AR6 medium-confidence GMSL @2100 rel 1995-2014 (cm): median, (likely 17-83 lo, hi). No SSP4-6.0.
AR6 = {"SSP1-1.9": (38, 28, 55), "SSP1-2.6": (44, 32, 62), "SSP2-4.5": (56, 44, 76),
       "SSP3-7.0": (68, 55, 90), "SSP5-8.5": (77, 63, 101)}

def get(ssp): return S[S.ssp_label == ssp].iloc[0]

fig, (axa, axb, axc) = plt.subplots(1, 3, figsize=(18, 5.7))
x = np.arange(len(ORDER))
BLUE, RED = "#1763b8", "crimson"

# ---- (a) dot-and-whisker @2100: BRICK-Mengel vs AR6 ----
for s in ORDER:
    xi = ORDER.index(s); r = get(s)
    axa.plot([xi-0.13]*2, [r.p05, r.p95], color=BLUE, lw=2.4, solid_capstyle="round", zorder=2)
    axa.plot(xi-0.13, r.p50, "o", color=BLUE, ms=7, zorder=3)
    axa.text(xi-0.13, r.p95 + 2.5, f"{r.p50:.0f}", ha="center", fontsize=8, color=BLUE)
    if s in AR6:
        med, lo, hi = AR6[s]
        axa.plot([xi+0.13]*2, [lo, hi], color=RED, lw=2.4, solid_capstyle="round", zorder=2, alpha=0.8)
        axa.plot(xi+0.13, med, "D", color=RED, ms=6, zorder=3)
axa.legend(handles=[
    ml.Line2D([], [], color=BLUE, marker="o", lw=2.4, label="BRICK-Mengel (median, 5–95% parametric)"),
    ml.Line2D([], [], color=RED, marker="D", lw=2.4, label="AR6 medium-conf. (median, likely 17–83%)"),
], fontsize=8, loc="upper left")
axa.set_xticks(x); axa.set_xticklabels(ORDER, rotation=30, ha="right")
axa.set_ylabel("GMSL @2100 (cm, rel 1995-2014)")
axa.set_title(f"(a) Total GMSL @2100  ({NDRAWS:,}-draw posterior)\nparametric band excludes structural/obs-noise unc.")
axa.grid(axis="y", alpha=0.25)

# ---- (b) trajectories + bands ----
for s in ORDER:
    d = T[T.ssp_label == s].sort_values("year")
    axb.fill_between(d.year, d.p05, d.p95, color=COL[s], alpha=0.14, lw=0)
    axb.plot(d.year, d.p50, color=COL[s], lw=2, label=s)
axb.set_title("(b) GMSL trajectory 2000–2100\n(median + 5–95% parametric band)")
axb.set_xlabel("year"); axb.set_ylabel("GMSL (cm, rel 1995-2014)")
axb.set_xlim(2000, 2100); axb.legend(fontsize=8, ncol=2); axb.grid(alpha=0.25)

# ---- (c) 2100 component decomposition (median, cm) ----
comps = [("ais", "AIS", "#1763b8"), ("gsic", "GSIC", "#0f9b6c"), ("gis", "GIS", "#b8480f"),
         ("te", "TE", "#9b1fb8"), ("lws", "LWS", "#8a97a3")]
bottom = np.zeros(len(ORDER))
for key, lab, c in comps:
    vals = np.array([get(s)[key] for s in ORDER])
    axc.bar(x, vals, 0.6, bottom=bottom, color=c, label=lab)
    bottom += vals
axc.set_xticks(x); axc.set_xticklabels(ORDER, rotation=30, ha="right")
axc.set_ylabel("GMSL @2100 component (cm, median)")
axc.set_title("(c) 2100 component decomposition (median)\nAIS-MICI drives the high-forcing rise")
axc.legend(fontsize=8, loc="upper left"); axc.grid(axis="y", alpha=0.25)

fig.suptitle(f"BRICK-Mengel GMSL projections to 2100 — {NDRAWS:,}-draw MCMC posterior, FaIR v1.4.5-forced (unweighted)\n"
             "Posterior already Dangendorf-conditioned (no importance weighting). High-forcing median runs high vs "
             "AR6 via the per-draw AIS-MICI threshold; low-forcing runs below AR6 (GIS/GSIC undershoot)",
             fontsize=10.5)
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(OUT, dpi=140)
print(f"[wrote {OUT}]")
