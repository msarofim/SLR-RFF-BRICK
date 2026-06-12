#!/usr/bin/env python3
"""
Updated historical component comparison after the quick central recalibration.

2x3 panels (AIS, GSIC, GIS, Steric/TE, LWS, Total). Each panel overlays:
  - observational target band (Frederikse 2020 component; Dangendorf 2024 for total),
  - the central BRICK trajectory BEFORE recalibration (dashed),
  - the central BRICK trajectory AFTER recalibration (solid).
All cm, rel 1995-2005 (the common window used everywhere in this prototype).

Inputs: outputs/recalib_central_trajectories.csv, outputs/recalib_targets.csv,
        outputs/recalib_central_summary.md (for the knob annotation),
        Frederikse xlsx (for the Greenland band, not in the targets CSV).
Output: outputs/recalib_component_comparison.png
"""
import os, re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
TRAJ = os.path.join(REPO, "outputs/recalib_central_trajectories.csv")
TGT  = os.path.join(REPO, "outputs/recalib_targets.csv")
SUMM = os.path.join(REPO, "outputs/recalib_central_summary.md")
FRED = os.path.join(REPO, "data/observations/raw/frederikse2020_global_basin_timeseries.xlsx")
OUT  = os.path.join(REPO, "outputs/recalib_component_comparison.png")
BASE0, BASE1 = 1995, 2005
FIT0, FIT1 = 1900, 2018

tr = pd.read_csv(TRAJ)
tg = pd.read_csv(TGT)

# Frederikse Greenland (not in targets CSV); re-reference to the common window.
g = pd.read_excel(FRED, "Global").rename(columns={"Unnamed: 0": "year"}).set_index("year")
def reref(s):  # mm -> cm, rel 1995-2005
    s = s / 10.0
    return s - s.loc[BASE0:BASE1].mean()
gis_obs = pd.DataFrame({
    "mean": reref(g["Greenland Ice Sheet [mean]"]),
    "lo":   reref(g["Greenland Ice Sheet [lower]"]),
    "hi":   reref(g["Greenland Ice Sheet [upper]"]),
}).reindex(range(FIT0, FIT1 + 1))

# knob annotation: the two headline (frozen equilibrium-temperature) knobs
knob_txt = ""
if os.path.exists(SUMM):
    def cells(l): return [c.strip() for c in l.strip().strip("|").split("|")]
    rows = [l for l in open(SUMM) if l.startswith("| ais_ocean") or l.startswith("| gsic_teq")]
    knob_txt = "   ".join(f"{cells(l)[0]}: {cells(l)[1]}→{cells(l)[2]}" for l in rows)

def band(ax, yr, lo, hi, label):
    ax.fill_between(yr, lo, hi, color="0.75", alpha=0.6, lw=0, label=label)

# FaIR-mean forcing (native units), 1900-2018, for the two forcing panels
fg = pd.read_csv(os.path.join(REPO, "data/observations/fair_mean_gmst.csv")).set_index("year")["gmst_C"]
fo = pd.read_csv(os.path.join(REPO, "data/observations/fair_mean_ohc.csv")).set_index("year")["ohc_1e22J"]
fy = np.arange(FIT0, FIT1 + 1)
PAUSE = (1958, 1972)   # mid-century FaIR-mean GMST plateau (rate ~0 C/decade)

fig, axes = plt.subplots(2, 4, figsize=(19, 8.8), sharex=True)
yr_tr = tr["year"].values
m = (yr_tr >= FIT0) & (yr_tr <= FIT1)
yr = yr_tr[m]

# component panels: (title, before col, after col, obs source)
comp_panels = [
    ("Antarctic Ice Sheet (AIS)",  "before_ais",  "after_ais",  "ais"),
    ("Glaciers (GSIC)",            "before_gsic", "after_gsic", "gsic"),
    ("Greenland (GIS) — not tuned","before_gis",  "after_gis",  "gis"),
    ("Steric / Thermal exp. (TE)", "before_te",   "after_te",   "steric"),
    ("Land water storage (LWS)",   "before_lws",  "after_lws",  "lws"),
    ("TOTAL GMSL",                 "before_total","after_total","dang"),
]
comp_axes = list(axes.flat[:6])
for ax, (title, bcol, acol, obs) in zip(comp_axes, comp_panels):
    if obs == "gis":
        band(ax, gis_obs.index, gis_obs["lo"], gis_obs["hi"], "Frederikse 2020")
        ax.plot(gis_obs.index, gis_obs["mean"], color="0.35", lw=1.2, ls="-")
    elif obs == "dang":
        band(ax, tg["year"], tg["dang"] - 1.645*tg["dang_sig"], tg["dang"] + 1.645*tg["dang_sig"], "Dangendorf 2024")
        ax.plot(tg["year"], tg["dang"], color="0.35", lw=1.2)
    else:
        band(ax, tg["year"], tg[obs + "_lo"], tg[obs + "_hi"], "Frederikse 2020")
        ax.plot(tg["year"], tg[obs], color="0.35", lw=1.2)
    ax.axvspan(*PAUSE, color="orange", alpha=0.10, lw=0)   # mid-century GMST pause
    ax.plot(yr, tr[bcol].values[m], color="#c44", lw=1.8, ls="--", label="BRICK before")
    ax.plot(yr, tr[acol].values[m], color="#1763b8", lw=2.0, ls="-", label="BRICK after (recal.)")
    ax.set_title(title, fontsize=11)
    ax.axhline(0, color="k", lw=0.4, alpha=0.4)
    ax.grid(alpha=0.25)
    ax.set_ylabel("cm (rel 1995-2005)", fontsize=8)
    ax.legend(fontsize=7.5, loc="lower left")

# forcing panels: the two free row-2 slots (components fill [0,0..0,3],[1,0],[1,1])
axg, axo = axes[1, 2], axes[1, 3]
for ax, ser, lab, col in [(axg, fg, "FaIR-mean GMST (°C rel PI)", "#b8480f"),
                          (axo, fo, "FaIR-mean OHC (10²² J)", "#0f6ab8")]:
    ax.axvspan(*PAUSE, color="orange", alpha=0.18, lw=0, label="mid-century\npause")
    ax.plot(fy, ser.reindex(fy).values, color=col, lw=2.0)
    ax.set_title(lab, fontsize=11)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=7.5, loc="upper left")
axg.annotate("warming 1\n1900-1955", (1925, fg.loc[1925]), fontsize=7, color="0.3")
axg.annotate("warming 2\n1970-pres", (1992, fg.loc[1992]), fontsize=7, color="0.3")

for ax in axes[1, :]:
    ax.set_xlabel("year")

fig.suptitle("Quick central BRICK recalibration — historical component comparison + FaIR forcing\n"
             "FaIR-mean forcing · medoid central draw · 8 knobs (incl. gsic_teq, the frozen glacier "
             "equilibrium temp) vs Frederikse + Dangendorf\n" + knob_txt, fontsize=10.5)
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(OUT, dpi=140)
print(f"[wrote {OUT}]")
