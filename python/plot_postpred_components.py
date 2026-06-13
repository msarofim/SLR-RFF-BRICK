#!/usr/bin/env python3
"""
Posterior-predictive component bands of the MCMC-calibrated BRICK-Mengel.

2x3 panels: AIS, GSIC, GIS, Steric/TE, Total GMSL, and a residual panel
(posterior median - obs) that exposes the compensating component biases.
Each component panel overlays:
  - the observational target band (Frederikse 2020 component; Dangendorf 2024
    +/-1.645 sigma for the total),
  - the BRICK-Mengel posterior 90% PARAMETRIC band (5-95% over 10k draws) + median.

The parametric band carries PARAMETER uncertainty only, NOT the AR(1) obs-noise
term in the likelihood -- so it is narrow by construction. A persistent component
offset (e.g. TE high, GIS low) absorbed by the high-rho AR(1) noise shows up here
as a band sitting beside the obs band; that is calibration tension, not a fit bug.
All cm, rel 1995-2005 (the common window used throughout the recalibration).

Input:  outputs/postpred_components_timeseries.csv (from julia/posterior_predictive.jl)
Output: outputs/postpred_components.png
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
SRC  = os.path.join(REPO, "outputs/postpred_components_timeseries.csv")
OUT  = os.path.join(REPO, "outputs/postpred_components.png")
FIT0, FIT1, BASE0, BASE1 = 1900, 2018, 1995, 2005

d = pd.read_csv(SRC)
yr = d["year"].values

OBS_C, MOD_C = "0.35", "#1763b8"
panels = [
    ("ais",   "Antarctic Ice Sheet (AIS)"),
    ("gsic",  "Glaciers (GSIC) — Mengel 2-tau"),
    ("gis",   "Greenland (GIS)"),
    ("te",    "Steric / Thermal exp. (TE)"),
    ("total", "TOTAL GMSL (+ Frederikse LWS budget)"),
]

fig, axes = plt.subplots(2, 3, figsize=(16, 8.6), sharex=True)
ax_list = list(axes.flat)

for ax, (c, title) in zip(ax_list[:5], panels):
    olab = "Dangendorf 2024" if c == "total" else "Frederikse 2020"
    ax.fill_between(yr, d[f"{c}_obs_lo"], d[f"{c}_obs_hi"], color="0.75", alpha=0.6, lw=0, label=olab)
    ax.plot(yr, d[f"{c}_obs"], color=OBS_C, lw=1.3, label="obs mean")
    ax.fill_between(yr, d[f"{c}_p5"], d[f"{c}_p95"], color=MOD_C, alpha=0.25, lw=0,
                    label="BRICK-Mengel 90% (param)")
    ax.plot(yr, d[f"{c}_p50"], color=MOD_C, lw=2.0, label="posterior median")
    o18, m18 = d[f"{c}_obs"].iloc[-1], d[f"{c}_p50"].iloc[-1]
    ax.annotate(f"2018  obs {o18:.2f}\n      mod {m18:.2f}  ({m18-o18:+.2f})",
                xy=(0.03, 0.97), xycoords="axes fraction", va="top", ha="left",
                fontsize=8, color="0.2")
    ax.set_title(title, fontsize=11)
    ax.axhline(0, color="k", lw=0.4, alpha=0.4)
    ax.grid(alpha=0.25)
    ax.set_ylabel("cm (rel 1995-2005)", fontsize=8)
    ax.legend(fontsize=7.5, loc="lower left")

# 6th panel: posterior-median residual (model - obs) per component -> compensating biases
axr = ax_list[5]
res_colors = {"ais": "#1763b8", "gsic": "#0f9b6c", "gis": "#b8480f", "te": "#9b1fb8", "total": "k"}
for c, _ in panels:
    res = d[f"{c}_p50"] - d[f"{c}_obs"]
    axr.plot(yr, res, color=res_colors[c], lw=(2.4 if c == "total" else 1.6),
             ls=("-" if c == "total" else "-"), label=f"{c} ({res.iloc[-1]:+.2f})")
axr.axhline(0, color="k", lw=0.6)
axr.set_title("Posterior-median residual (model − obs)", fontsize=11)
axr.grid(alpha=0.25)
axr.set_ylabel("cm", fontsize=8)
axr.legend(fontsize=7.5, loc="lower left", title="2018 Δ (cm)", title_fontsize=7.5)

for ax in axes[1, :]:
    ax.set_xlabel("year")
axes[0, 0].set_xlim(FIT0, 2020)

fig.suptitle("BRICK-Mengel posterior-predictive vs Frederikse/Dangendorf (FaIR-forced, 1900–2018)\n"
             "MCMC posterior (4×500k, 27/28 converged) · 10k draws · bands = parameter unc. only "
             "(AR(1) obs-noise excluded) · component biases partly cancel in the total",
             fontsize=10.5)
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(OUT, dpi=140)
print(f"[wrote {OUT}]")
