#!/usr/bin/env python3
"""
Validation figure for the full joint MAP calibration of BRICK-Mengel.
MAP-calibrated component trajectories vs Frederikse components + Dangendorf total.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
TR = pd.read_csv(os.path.join(REPO, "outputs/calib_full_joint_trajectories.csv"))
TG = pd.read_csv(os.path.join(REPO, "outputs/recalib_targets.csv")).set_index("year")
P = pd.read_csv(os.path.join(REPO, "outputs/calib_full_joint_params.csv"))
OUT = os.path.join(REPO, "outputs/full_joint_calibration.png")
yr = TR["year"].values

def band(ax, obs):
    ax.fill_between(TG.index, TG[obs + "_lo"], TG[obs + "_hi"], color="0.75", alpha=0.6, lw=0, label="Frederikse 2020")
    ax.plot(TG.index, TG[obs], color="0.35", lw=1.2)

fig, axes = plt.subplots(2, 3, figsize=(15, 8.4))
panels = [("Antarctic Ice Sheet", "ais", "ais"), ("Glaciers (Mengel)", "gsic", "gsic"),
          ("Greenland", "gis", "gis"), ("Steric / Thermal exp.", "te", "steric")]
for ax, (title, col, obs) in zip(axes.flat[:4], panels):
    band(ax, obs)
    ax.plot(yr, TR[col], color="#1763b8", lw=2.0, label="MAP calibration")
    ax.set_title(title, fontsize=11); ax.axhline(0, color="k", lw=0.4, alpha=0.4)
    ax.grid(alpha=0.25); ax.set_ylabel("cm (rel 1995-2005)", fontsize=8); ax.legend(fontsize=8, loc="lower left")
    ax.set_xlim(1900, 2018)

# total vs Dangendorf
axt = axes.flat[4]
axt.fill_between(TG.index, TG["dang"] - 1.645*TG["dang_sig"], TG["dang"] + 1.645*TG["dang_sig"],
                 color="0.75", alpha=0.6, lw=0, label="Dangendorf 2024")
axt.plot(TG.index, TG["dang"], color="0.35", lw=1.2)
axt.plot(yr, TR["total"], color="#c0504d", lw=2.0, label="MAP total (+ LWS budget)")
axt.set_title("TOTAL GMSL", fontsize=11); axt.grid(alpha=0.25); axt.set_xlim(1900, 2018)
axt.set_ylabel("cm (rel 1995-2005)", fontsize=8); axt.legend(fontsize=8, loc="lower left")

# parameter shifts panel
axp = axes.flat[5]
mv = P.reindex(P.moved_sigmas.abs().sort_values(ascending=True).index).tail(12)
axp.barh(range(len(mv)), mv.moved_sigmas, color=["#c0504d" if v < 0 else "#1763b8" for v in mv.moved_sigmas])
axp.set_yticks(range(len(mv))); axp.set_yticklabels(mv.param, fontsize=6.5)
axp.axvline(0, color="k", lw=0.6); axp.axvline(1, color="0.6", ls=":", lw=0.8); axp.axvline(-1, color="0.6", ls=":", lw=0.8)
axp.set_xlabel("MAP shift from prior (σ)", fontsize=8)
axp.set_title("Largest parameter shifts\n(rest held near prior)", fontsize=10); axp.grid(axis="x", alpha=0.25)

fig.suptitle("Full joint MAP calibration of BRICK-Mengel — 27 free params, FaIR-forced, prior-regularized\n"
             "AIS/GIS/Steric within obs; GSIC undershoots @1900 (single-τ glacier + global-LIA T_lia prior); "
             "MICI threshold unconstrained by historical data (held at prior → projection uncertainty in the ensemble)",
             fontsize=10)
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(OUT, dpi=140)
print(f"[wrote {OUT}]")
