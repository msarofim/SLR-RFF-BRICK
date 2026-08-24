#!/usr/bin/env python
"""Does the mid-century amplification-ratio noise come from the GLOBAL denominator?

Hypothesis (Marcus): NH sulfate aerosols depressed global-mean warming mid-century, so
the denominator (ΔT_glob) was small/noisy, blowing up the Antarctic amplification ratio;
Antarctica is aerosol-light, so referencing Antarctic warming to the SOUTHERN-HEMISPHERE
mean (which shares little NH-aerosol suppression) should be far less noisy.

Test: for each model, the Antarctic amplification ratio vs GLOBAL mean and vs SH mean,
30-yr running means rel. 1850-1900, ssp245. Compare (i) the multi-model spread of the
ratio through time (noise), and (ii) the size of the two denominators mid-century.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pai_series import model_series_files
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

IN_DIR    = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/data/cmip6_pai"
OUT_PNG   = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/outputs/diag_pai_denominator.png"
OUT_MD    = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/outputs/diag_pai_denominator_summary.md"
BASELINE  = (1850, 1900); SMOOTH = 30; SMOOTH_MINP = 15; SCEN = "ssp245"

def load(model):
    base = pd.read_csv(os.path.join(IN_DIR, f"tas_series_{model}.csv"))
    hemf = os.path.join(IN_DIR, f"tas_series_hemis_{model}.csv")
    if not os.path.exists(hemf): return None
    hem = pd.read_csv(hemf)
    def series(df, col, scen):
        s = pd.concat([df[(df.scenario == "historical") & (df.year <= 2014)],
                       df[df.scenario == scen]]).sort_values("year").set_index("year")
        return s[~s.index.duplicated()][col].loc[:2100]
    ais = series(base, "tas_ais", SCEN); glob = series(base, "tas_global", SCEN)
    sh = series(hem, "tas_sh", SCEN)
    b_ais = base[(base.scenario=="historical") & base.year.between(*BASELINE)].tas_ais.mean()
    b_glob= base[(base.scenario=="historical") & base.year.between(*BASELINE)].tas_global.mean()
    b_sh  = hem[(hem.scenario=="historical")   & hem.year.between(*BASELINE)].tas_sh.mean()
    sm = lambda x: x.rolling(SMOOTH, center=True, min_periods=SMOOTH_MINP).mean()
    dA, dG, dS = sm(ais-b_ais), sm(glob-b_glob), sm(sh-b_sh)
    return pd.DataFrame({"dG": dG, "dS": dS,
                         "R_glob": (dA/dG).where(dG>0.1),
                         "R_sh":   (dA/dS).where(dS>0.1)}).loc[1900:]

models = sorted(model_series_files(IN_DIR))   # shared resolver, python/pai_series.py
D = {m: load(m) for m in models}; D = {m: d for m, d in D.items() if d is not None}
print(f"{len(D)} models")

def med_iqr(key):
    alld = pd.concat([d[key].rename(m) for m, d in D.items()], axis=1)
    return alld.median(axis=1), alld.quantile(.25, axis=1), alld.quantile(.75, axis=1), alld

for label, key in (("vs GLOBAL", "R_glob"), ("vs SH", "R_sh")):
    med, q1, q3, _ = med_iqr(key)
    for yr in (1960, 1980, 2000, 2050, 2090):
        if yr in med.index:
            print(f"  {label} @{yr}: median {med[yr]:.2f}  IQR width {q3[yr]-q1[yr]:.2f}")
# denominator sizes mid-century
mg, *_ = med_iqr("dG"); ms, *_ = med_iqr("dS")
print("\ndenominator (median ΔT rel PI):")
for yr in (1960, 1980, 2000):
    print(f"  @{yr}: global {mg[yr]:.2f} K   SH {ms[yr]:.2f} K   (SH/global {ms[yr]/mg[yr]:.2f})")

fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
for ax, (label, key, col) in zip(axes, [("Antarctic / GLOBAL", "R_glob", "#0d7c8c"),
                                        ("Antarctic / SH", "R_sh", "#6d5b9c")]):
    med, q1, q3, alld = med_iqr(key)
    for m in alld.columns:
        ax.plot(alld.index, alld[m], color=col, alpha=.13, lw=.7)
    ax.fill_between(med.index, q1, q3, color=col, alpha=.22, lw=0)
    ax.plot(med.index, med, color=col, lw=2.2, label="multi-model median")
    ax.axhline(1.0, color="k", lw=.6, alpha=.4)
    ax.set(title=f"{label} warming ratio (SSP2-4.5)", xlabel="year",
           ylabel="amplification ratio", xlim=(1900, 2100), ylim=(0.4, 2.2))
    ax.legend(frameon=False, fontsize=8)
fig.suptitle(f"Denominator test: global vs Southern-Hemisphere reference "
             f"({len(D)} models, 30-yr means)", fontsize=11)
fig.tight_layout(); fig.savefig(OUT_PNG, dpi=160)
print(f"wrote {OUT_PNG}")

with open(OUT_MD, "w") as f:
    mgm, *_ = med_iqr("R_glob"); msm, *_ = med_iqr("R_sh")
    f.write(f"# Denominator test ({len(D)} models, SSP2-4.5)\n\n"
            f"Antarctic amplification ratio referenced to GLOBAL vs SOUTHERN-HEMISPHERE mean.\n\n"
            "| year | R (vs global) | R (vs SH) | IQR(global) | IQR(SH) |\n|---|---|---|---|---|\n")
    for yr in (1960, 1980, 2000, 2050, 2090):
        g, gq1, gq3, _ = med_iqr("R_glob"); s, sq1, sq3, _ = med_iqr("R_sh")
        f.write(f"| {yr} | {g[yr]:.2f} | {s[yr]:.2f} | {gq3[yr]-gq1[yr]:.2f} | {sq3[yr]-sq1[yr]:.2f} |\n")
print(f"wrote {OUT_MD}")
