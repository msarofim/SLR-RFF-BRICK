#!/usr/bin/env python3
"""
plot_protect_forcing_matched.py — the PROTECT x2300 comparison, done at MATCHED
forcing, which is the only version of it that is about the ice sheet.

WHY (2026-08-21, notes/handoff_2026-08-21_protect_greenland.md)
  The handoff compared our tapped Greenland against the PROTECT x2300 physics
  ensemble and read "2300 agrees to 1.4%, 2150 is 38% low" as "the tap onset is
  too late". Both arms of that comparison were run at different warming: ours
  reaches 7.8 C at 2300, the x2300 forcing GCMs reach 13.6. This figure re-runs
  ours on THEIR forcing and shows what is left.

PANELS
  (a) the forcing gap, and where each path crosses the 6.5 K onset
  (b) Greenland at matched forcing: PROTECT p05-p95, our base (tap off), our
      shipped cell. The 2150 relation reverses.
  (c) what the tap must supply (PROTECT minus our base) against what the shipped
      exponential does supply. Front-loaded and saturating vs back-loaded and
      still accelerating -- a shape mismatch, not a mis-set onset.

Inputs   outputs/protect_x2300_forcing_gmst.csv
         outputs/protect_greenland_gis_annual.csv
         outputs/diag_protect_forcing_matched_L14{,_untapped}.csv
Output   figures/protect_forcing_matched.png
  python3 python/plot_protect_forcing_matched.py
"""
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = "L14"
OUT = os.path.join(REPO, "figures/protect_forcing_matched.png")

## LABELS DERIVE FROM THESE — a changed constant must move every caption with it.
ONSET_K = 6.5
TAU_YR = 50
V_M = 2.0
BASIS = "cm rel 1995-2014"
## PROTECT reports rel 2015; this is our own gis(2015) on the 1995-2014 base, so
## adding it puts their series on ours. Measured, not assumed — see below.
ARM = "spliced"          # ours <=2014 then PROTECT; `raw` is the sensitivity arm
XLIM = (2015, 2300)

f = pd.read_csv(os.path.join(REPO, "outputs/protect_x2300_forcing_gmst.csv")).set_index("year")
ann = pd.read_csv(os.path.join(REPO, "outputs/protect_greenland_gis_annual.csv"))
tap = pd.read_csv(os.path.join(REPO, f"outputs/diag_protect_forcing_matched_{TAG}.csv"))
unt = pd.read_csv(os.path.join(REPO, f"outputs/diag_protect_forcing_matched_{TAG}_untapped.csv"))

x = ann[ann.exp.str.contains("ssp585-x2300")]
## n is RUNS, not experiment ids: 18 runs share 12 ids across the CISM
## configurations, and the quantiles below are over runs. Counting ids would
## under-report the ensemble by a third.
N = len(x.groupby(["group", "model", "exp"]))
GCMS = " + ".join(sorted(x.exp.str.split("_").str[0].unique()))
P = x.groupby("year").gis_cm
p05, p50, p95 = P.quantile(.05), P.median(), P.quantile(.95)

sel = lambda d, a: d[(d.component == "gis") & (d.arm == a)].set_index("year")
T, U, O = sel(tap, ARM).med, sel(unt, ARM).med, sel(unt, "ours").med
OFFSET = float(sel(unt, "ours").med.loc[2015])       # our gis(2015) on the 1995-2014 base
p05, p50, p95 = p05 + OFFSET, p50 + OFFSET, p95 + OFFSET

C_P, C_U, C_T, C_O = "#1a5c2a", "#1763b8", "#c1272d", "0.55"
fig, ax = plt.subplots(1, 3, figsize=(16.5, 5.2))

# (a) the forcing gap ---------------------------------------------------------
ax[0].plot(f.index, f.gmst_ours_11yr, color=C_O, lw=2.2, label="ours (fair_mean_gmst_ssp585)")
ax[0].plot(f.index, f[f"gmst_{ARM}_11yr"], color=C_P, lw=2.2,
           label="PROTECT x2300 forcing\n" +
                 f.weights.iloc[0].replace("|", ", ").replace(":", " × "))
ax[0].axhline(ONSET_K, color="k", ls=":", lw=1.2)
for s, c in ((f.gmst_ours_11yr, C_O), (f[f"gmst_{ARM}_11yr"], C_P)):
    yr = int(s[s >= ONSET_K].index[0])
    ax[0].plot(yr, ONSET_K, "o", color=c, ms=8, zorder=5)
    ax[0].annotate(str(yr), (yr, ONSET_K), textcoords="offset points",
                   xytext=(4, -14), color=c, fontsize=10, fontweight="bold")
ax[0].text(2020, ONSET_K + 0.25, f"tap onset {ONSET_K} K", fontsize=9)
ax[0].set_ylabel("GSAT, °C vs 1850-1900 (11-yr)")
ax[0].set_title("(a) the two runs were never the same world", loc="left", fontsize=11)
ax[0].legend(fontsize=8.5, loc="upper left")

# (b) Greenland at matched forcing --------------------------------------------
ax[1].fill_between(p50.index, p05, p95, color=C_P, alpha=.18,
                   label=f"PROTECT x2300 p05-p95 (n={N})")
ax[1].plot(p50.index, p50, color=C_P, lw=2.4, label="PROTECT x2300 median")
ax[1].plot(U.index, U, color=C_U, lw=2.2, label="ours, tap OFF")
ax[1].plot(T.index, T, color=C_T, lw=2.2,
           label=f"ours, shipped cell ({ONSET_K} K, {V_M} m, τ={TAU_YR} yr)")
ax[1].plot(O.index, O, color=C_O, lw=1.6, ls="--", label="ours, tap OFF, OUR forcing")
for yr in (2150, 2300):
    ax[1].axvline(yr, color="k", lw=.6, alpha=.3)
ax[1].set_ylabel(f"Greenland contribution, {BASIS}")
ax[1].set_title("(b) all three curves under the PROTECT forcing", loc="left", fontsize=11)
ax[1].legend(fontsize=8.5, loc="upper left")

# (c) the shape of what the tap must do ---------------------------------------
## The two series have different spans (PROTECT starts 2015, ours 1990), so they
## are aligned on their common index before differencing — an unaligned subtract
## would silently drop years into NaN.
yrs = p50.index.intersection(U.index).intersection(T.index)
need, give = (p50.loc[yrs] - U.loc[yrs]), (T.loc[yrs] - U.loc[yrs])
ax[2].axhline(0, color="k", lw=.8)
ax[2].plot(need.index, need, color=C_P, lw=2.4, label="NEEDED: PROTECT − our base")
ax[2].plot(give.index, give, color=C_T, lw=2.4, label="GIVEN: shipped exponential")
ax[2].fill_between(yrs, need.values, give.values, where=give.values >= need.values,
                   color=C_T, alpha=.13)
## The crossing is the LAST year the physics still wants LESS than our base, not
## the first year the difference is non-negative — the series starts at ~0, so
## first-non-negative returns the first year of the record.
cross = int(need[need < 0].index[-1]) + 1
ax[2].axvline(cross, color=C_P, ls=":", lw=1.4)
ax[2].annotate(f"physics wants nothing\nfrom the tap until {cross}",
               (cross, give.max() * .62), textcoords="offset points",
               xytext=(-142, 0), color=C_P, fontsize=9.5, fontweight="bold")
ax[2].set_ylabel(f"tap contribution, {BASIS}")
ax[2].set_title("(c) front-loaded and saturating vs back-loaded and accelerating",
                loc="left", fontsize=11)
ax[2].legend(fontsize=8.5, loc="upper left")

for a in ax:
    a.set_xlim(*XLIM)
    a.set_xlabel("year")
    a.grid(alpha=.25, lw=.6)

fig.suptitle(
    f"PROTECT-Greenland x2300 vs Ladrillo {TAG}, AT MATCHED FORCING — GIS only "
    f"(OHC left on ours) | PROTECT rel 2015 shifted +{OFFSET:.2f} cm onto {BASIS} | "
    f"n={N}, ONE ice sheet model (NORCE-CISM), {ARM} arm",
    fontsize=10.5, y=1.005)
fig.tight_layout()
fig.savefig(OUT, dpi=160, bbox_inches="tight")
print("wrote", os.path.relpath(OUT, REPO))
