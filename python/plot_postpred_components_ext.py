#!/usr/bin/env python3
"""
Posterior-predictive component bands of the EXTENDED-target BRICK-Mengel re-fit,
vs the extended observational targets (Frederikse 1900-2018 spliced with GRACE-FO
AIS/GIS, GlaMBIE GSIC, NOAA NCEI steric, NOAA STAR total through 2023-2026).

2x3 panels: AIS, GSIC, GIS, Steric/TE, Total GMSL + residual (median - obs). The
post-2018 EXTENSION region is shaded so the new data is visually distinct, and the
modern era (where the post-2020 AIS pause + glacier acceleration live) is emphasized.
Bands are the 90% PARAMETRIC band (parameter unc. only; AR(1) obs-noise excluded) so
they are narrow -- persistent offsets (TE high) are calibration tension, not fit bugs.

Inputs:  outputs/postpred_ext_components_timeseries.csv (julia/posterior_predictive_ext.jl)
         outputs/recalib_targets_ext.csv (obs uncertainty bands)
Output:  outputs/postpred_ext_components.png
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
SRC  = os.path.join(REPO, "outputs/postpred_ext_components_timeseries.csv")
TGT  = os.path.join(REPO, "outputs/recalib_targets_ext.csv")
PROV = os.path.join(REPO, "outputs/recalib_targets_ext_sources.csv")   # Frederikse vs modern, separated
OUT  = os.path.join(REPO, "outputs/postpred_ext_components.png")
EXT_Y0 = 2018          # extension starts after this (shaded)

d = pd.read_csv(SRC)
tg = pd.read_csv(TGT).set_index("year")
prov = pd.read_csv(PROV).set_index("year")
yr = d["year"].values
FRED_C, MODERN_C = "0.25", "#c0392b"     # Frederikse = dark grey, modern extension = red

# map panel component -> obs column in recalib_targets_ext (for the uncertainty band)
OBSCOL = {"ais": "ais", "gsic": "gsic", "gis": "gis", "te": "steric", "total": "dang"}
SRCLAB = {"ais": "GRACE-FO", "gsic": "GlaMBIE", "gis": "GRACE-FO", "te": "NOAA NCEI", "total": "NOAA STAR"}
OBS_C, MOD_C = "0.35", "#1763b8"
panels = [
    ("ais",   "Antarctic Ice Sheet — GRACE-FO ext (post-2020 pause)"),
    ("gsic",  "Glaciers (Mengel 2-τ) — GlaMBIE ext (acceleration)"),
    ("gis",   "Greenland — GRACE-FO ext"),
    ("te",    "Steric / Thermal exp. — NOAA NCEI ext"),
    ("total", "TOTAL GMSL — Dangendorf + NOAA STAR ext"),
]

fig, axes = plt.subplots(2, 3, figsize=(16, 8.6))
ax_list = list(axes.flat)

for ax, (c, title) in zip(ax_list[:5], panels):
    oc = OBSCOL[c]
    # obs uncertainty band from the extended targets
    if c == "total":
        olo = (tg["dang"] - 1.645*tg["dang_sig"]).reindex(yr).values
        ohi = (tg["dang"] + 1.645*tg["dang_sig"]).reindex(yr).values
    else:
        olo = tg[f"{oc}_lo"].reindex(yr).values
        ohi = tg[f"{oc}_hi"].reindex(yr).values
    ax.axvspan(EXT_Y0, yr.max(), color="orange", alpha=0.06, lw=0)
    ax.fill_between(yr, olo, ohi, color="0.78", alpha=0.55, lw=0, label="obs unc.")
    # OBS PROVENANCE: Frederikse (1900-2018) vs the offset-matched modern extension,
    # drawn over its FULL range incl. the 2003-2018 overlap (shows it tracks Frederikse
    # then takes over) -- the splice is a clean handoff, not a blend.
    flab = "Dangendorf 2024" if c == "total" else "Frederikse 2020"
    ax.plot(prov.index, prov[f"{oc}_fred"],   color=FRED_C,   lw=1.6, label=flab, zorder=5)
    ax.plot(prov.index, prov[f"{oc}_modern"], color=MODERN_C, lw=1.3, ls="--", zorder=6,
            marker="o", ms=2.5, markevery=2, label=f"{SRCLAB[c]} (ext, offset-matched)")
    ax.axvline(EXT_Y0, color="orange", lw=0.9, ls=":", zorder=4)
    ax.fill_between(yr, d[f"{c}_p5"], d[f"{c}_p95"], color=MOD_C, alpha=0.22, lw=0,
                    label="BRICK-Mengel 90% (param)")
    ax.plot(yr, d[f"{c}_p50"], color=MOD_C, lw=2.0, label="posterior median")
    # end-year bias annotation
    om = d[f"{c}_obs"].dropna(); ey = int(om.index[-1] if om.index.name == "year" else d["year"][om.index[-1]])
    j = d.index[d["year"] == ey][0]
    o_e, m_e = d.loc[j, f"{c}_obs"], d.loc[j, f"{c}_p50"]
    ax.annotate(f"{ey}: obs {o_e:.2f}, mod {m_e:.2f} ({m_e-o_e:+.2f})",
                xy=(0.03, 0.96), xycoords="axes fraction", va="top", ha="left", fontsize=8, color="0.2")
    ax.set_title(title, fontsize=10.5)
    ax.axhline(0, color="k", lw=0.4, alpha=0.4); ax.grid(alpha=0.25)
    ax.set_ylabel("cm (rel 1995-2005)", fontsize=8)
    ax.set_xlim(1950, yr.max())
    ax.legend(fontsize=7, loc="upper left", bbox_to_anchor=(0.0, 0.88))

# residual panel — focus on modern era to expose post-2018 bias evolution
axr = ax_list[5]
res_colors = {"ais": "#1763b8", "gsic": "#0f9b6c", "gis": "#b8480f", "te": "#9b1fb8", "total": "k"}
for c, _ in panels:
    res = d[f"{c}_p50"] - d[f"{c}_obs"]
    axr.plot(yr, res, color=res_colors[c], lw=(2.4 if c == "total" else 1.6),
             label=f"{c} ({res.dropna().iloc[-1]:+.2f})")
axr.axvspan(EXT_Y0, yr.max(), color="orange", alpha=0.06, lw=0)
axr.axhline(0, color="k", lw=0.6)
axr.set_title("Posterior-median residual (model − obs)", fontsize=10.5)
axr.grid(alpha=0.25); axr.set_ylabel("cm", fontsize=8); axr.set_xlim(1980, yr.max())
axr.legend(fontsize=7.5, loc="lower left", title="end-yr Δ (cm)", title_fontsize=7.5)
for ax in axes[1, :]:
    ax.set_xlabel("year")

fig.suptitle("EXTENDED BRICK-Mengel posterior-predictive vs obs — Frederikse (grey) vs modern extension (red dashed) shown separately\n"
             "modern product drawn over its full range incl. the 2003-2018 overlap (tracks Frederikse, then takes over at the 2018 splice, dotted) · "
             "MCMC 4×500k, 27/28 conv · bands = parameter unc. only",
             fontsize=10.5)
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(OUT, dpi=140)
print(f"[wrote {OUT}]")
