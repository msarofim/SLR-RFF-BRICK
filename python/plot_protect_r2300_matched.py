#!/usr/bin/env python3
"""
plot_protect_r2300_matched.py — the r2300 matched-forcing arm, and the pattern it
shares with x2300: our Greenland is not CONVEX ENOUGH in time.

WHY (2026-08-21, notes/handoff_2026-08-21b_protect_matched_forcing.md §5 item 2)
  x2300 tests the model at 9.8-13.6 K, far outside our own 4.7-7.8 K. r2300 holds
  each GCM's 2100 forcing to 2300 (Goelzer 2025), plateaus at 5.58 K, and carries
  FIVE usable forcing GCMs against x2300's two. It is the closer analogue and the
  wider climate sample.

  ITS PLATEAU IS BELOW THE 6.5 K ONSET, SO THE TAP NEVER FIRES: verified, tapped
  and untapped agree to 0.00e+00 cm at every year. This arm is therefore a clean
  test of the BASE model, which is the half the x2300 arm could not isolate from
  the tap.

WHAT IT SHOWS
  Our base tracks the physics near 2150 and diverges in BOTH directions away from
  it — too high early, too low late — on both families independently:

      ours / PROTECT median      2100   2150   2300
      x2300 (2 GCMs, 9.8-13.6 K) 1.63   0.97   0.38
      r2300 (5 GCMs, 5.58 K)     1.18   0.89   0.49

  Under CONSTANT forcing the physics is still climbing at 2300 while ours has
  nearly stopped — the late-rate ratio in panel (c) is the diagnosis: our slow
  channel equilibrates far too fast.

Inputs   outputs/protect_r2300_forcing_gmst.csv, protect_greenland_gis_annual.csv,
         outputs/diag_protect_forcing_matched_L14{,_r2300}{,_untapped}.csv
Output   figures/protect_r2300_matched.png
  python3 python/plot_protect_r2300_matched.py
"""
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = "L14"
ARM = "spliced"
DROP_GCM = "ACCESS1.3"      # CMIP5; dropped from BOTH the forcing and the band
RATE_WIN = 100              # yr, the late-rate window ending at 2300
OUT = os.path.join(REPO, "figures/protect_r2300_matched.png")

ann = pd.read_csv(os.path.join(REPO, "outputs/protect_greenland_gis_annual.csv"))
fR = pd.read_csv(os.path.join(REPO, "outputs/protect_r2300_forcing_gmst.csv")).set_index("year")
fX = pd.read_csv(os.path.join(REPO, "outputs/protect_x2300_forcing_gmst.csv")).set_index("year")
uR = pd.read_csv(os.path.join(REPO, f"outputs/diag_protect_forcing_matched_{TAG}_r2300_untapped.csv"))
uX = pd.read_csv(os.path.join(REPO, f"outputs/diag_protect_forcing_matched_{TAG}_untapped.csv"))
sel = lambda d, a: d[(d.component == "gis") & (d.arm == a)].set_index("year").med
OFFSET = float(sel(uX, "ours").loc[2015])

r = ann[ann.exp.str.contains("r2300") & ann.exp.str.contains("ssp585|rcp85")]
r = r[~r.exp.str.startswith(DROP_GCM)]
x = ann[ann.exp.str.contains("ssp585-x2300")]
nR = len(r.groupby(["group", "model", "exp"]))
nX = len(x.groupby(["group", "model", "exp"]))
qR, qX = r.groupby("year").gis_cm, x.groupby("year").gis_cm
bR, bX = sel(uR, ARM), sel(uX, ARM)

C_P, C_U, C_X = "#1a5c2a", "#1763b8", "#8c6d1f"
fig, ax = plt.subplots(1, 3, figsize=(16.5, 5.0))

ax[0].plot(fR.index, fR.gmst_ours_11yr, "0.55", lw=2.2, label="ours (ssp585)")
ax[0].plot(fR.index, fR[f"gmst_{ARM}_11yr"], color=C_P, lw=2.2,
           label=f"r2300 forcing HELD from 2101\n({fR.n_runs.iloc[0]} runs, 5 GCMs)")
ax[0].plot(fX.index, fX[f"gmst_{ARM}_11yr"], color=C_X, lw=2.2, ls="--",
           label=f"x2300 forcing ({fX.n_runs.iloc[0]} runs, 2 GCMs)")
ax[0].axhline(6.5, color="k", ls=":", lw=1.2)
ax[0].text(2020, 6.7, "tap onset 6.5 K", fontsize=9)
ax[0].set_ylabel("GSAT, °C vs 1850-1900 (11-yr)")
ax[0].set_title("(a) r2300 is the closer analogue — and never fires the tap",
                loc="left", fontsize=11)
ax[0].legend(fontsize=8.5, loc="upper left")

ax[1].fill_between(qR.median().index, qR.quantile(.05) + OFFSET, qR.quantile(.95) + OFFSET,
                   color=C_P, alpha=.18, label=f"PROTECT r2300 p05-p95 (n={nR})")
ax[1].plot(qR.median().index, qR.median() + OFFSET, color=C_P, lw=2.4, label="r2300 median")
ax[1].plot(bR.index, bR, color=C_U, lw=2.2, label="ours (tap never fires here)")
ax[1].set_ylabel("Greenland contribution, cm rel 1995-2014")
ax[1].set_title("(b) under the r2300 forcing: ours flattens, the physics does not",
                loc="left", fontsize=11)
ax[1].legend(fontsize=8.5, loc="upper left")

for lab, b, q, n, c, ls in (("x2300 (2 GCMs)", bX, qX, nX, C_X, "--"),
                            ("r2300 (5 GCMs)", bR, qR, nR, C_P, "-")):
    yy = b.index.intersection(q.median().index)
    yy = yy[yy >= 2040]
    ax[2].plot(yy, (b.loc[yy] / (q.median().loc[yy] + OFFSET)).to_numpy(),
               color=c, lw=2.4, ls=ls, label=f"{lab}, n={n}")
ax[2].axhline(1.0, color="k", lw=1.0)
ax[2].set_ylabel("ours ÷ PROTECT median")
ax[2].set_title("(c) too high early, too low late — on BOTH families", loc="left", fontsize=11)
ax[2].legend(fontsize=8.5, loc="upper right")

for a in ax:
    a.set_xlim(2015, 2300); a.set_xlabel("year"); a.grid(alpha=.25, lw=.6)

rate = lambda s: (s.loc[2300] - s.loc[2300 - RATE_WIN]) / RATE_WIN * 100
fig.suptitle(
    f"PROTECT r2300 at matched forcing — plateau {fR[f'gmst_{ARM}'].iloc[-1]:.2f} K, "
    f"tap inert (tapped − untapped = 0.00 cm at every year) | "
    f"{2300-RATE_WIN}-2300 rate: physics {rate(qR.median()):.1f} vs ours {rate(bR):.1f} cm/century",
    fontsize=10.5, y=1.01)
fig.tight_layout()
fig.savefig(OUT, dpi=160, bbox_inches="tight")
print(f"{2300-RATE_WIN}-2300 rate, cm/century: r2300 physics {rate(qR.median()):.1f}, "
      f"ours {rate(bR):.1f}  ({rate(qR.median())/rate(bR):.1f}x)")
print(f"                             x2300 physics {rate(qX.median()):.1f}, ours {rate(bX):.1f}"
      f"  ({rate(qX.median())/rate(bX):.1f}x)")
print("wrote", os.path.relpath(OUT, REPO))
