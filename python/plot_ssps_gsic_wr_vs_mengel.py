#!/usr/bin/env python3
"""Glacier (GSIC) melt to 2300 under all SSPs: Wigley-Raper (BRICK 2.0) vs Mengel — commitment + spread.

Same FaIR 2.2.4 (calib1.4.5) SSP GMST drives all. (b) WR keeps melting even where T plateaus/declines
(no finite equilibrium). (c) Mengel posterior stabilizes but its SCENARIO SPREAD is anomalously
compressed — the calibrated gic_b→0.89 (railed at its 1.0 bound) saturates S_eq by ~1.3 deg C; the
dashed b=0.52 counterfactual (Mengel-published b, a rescaled to keep each draw's historical a*b) restores
the physically-expected spread. Reads outputs/ssps_gsic_2300{,_mengel,_mengel_b052}.csv.
"""
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

WR    = pd.read_csv("outputs/ssps_gsic_2300.csv")
MEN   = pd.read_csv("outputs/ssps_gsic_2300_mengel.csv")
MENCF = pd.read_csv("outputs/ssps_gsic_2300_mengel_b052.csv")
SSPS = ["SSP1-1.9","SSP1-2.6","SSP2-4.5","SSP4-6.0","SSP3-7.0","SSP5-8.5"]
COL = {"SSP1-1.9":"#00a9cf","SSP1-2.6":"#003466","SSP2-4.5":"#f69320",
       "SSP4-6.0":"#c8a000","SSP3-7.0":"#df0000","SSP5-8.5":"#7a0002"}
X0, X1 = 2000, 2300

def series(df, ssp):
    d = df[df.ssp == ssp].sort_values("year"); m = (d.year >= X0)
    return d.year[m].values, d[m]

fig, ax = plt.subplots(4, 1, figsize=(8.6, 12.2), sharex=True,
                       gridspec_kw=dict(height_ratios=[0.85, 1.2, 1.2, 0.95], hspace=0.13))

# ---- (a) GMST forcing ----
for s in SSPS:
    yr, d = series(WR, s)
    ax[0].plot(yr, d.gmst, color=COL[s], lw=1.8, label=s)
ax[0].set_ylabel("GMST (°C rel. PI)")
ax[0].set_title("Glacier (GSIC) melt to 2300 — Wigley–Raper (BRICK 2.0) vs Mengel, identical SSP temperatures",
                fontsize=11, fontweight="bold", loc="left")
ax[0].legend(ncol=3, fontsize=8, frameon=False, loc="upper left")
ax[0].annotate("SSP1-1.9 peaks ~2050,\nthen declines", xy=(2205, 1.05), fontsize=7.5,
               color=COL["SSP1-1.9"], ha="center")

ymax = max(WR.gsic_hi.max(), MENCF.gsic_hi.max()) * 1.02

# ---- (b) Wigley–Raper ----
for s in SSPS:
    yr, d = series(WR, s)
    ax[1].plot(yr, d.gsic_med, color=COL[s], lw=1.9)
    if s == "SSP1-1.9":
        ax[1].fill_between(yr, d.gsic_lo, d.gsic_hi, color=COL[s], alpha=0.15, lw=0)
ax[1].text(0.012, 0.93, "(b)  Wigley–Raper (BRICK 2.0) — keeps melting toward a common ceiling",
           transform=ax[1].transAxes, fontsize=9.5, fontweight="bold", va="top")

# ---- (c) Mengel: posterior (solid) + b=0.52 counterfactual (dashed) ----
for s in SSPS:
    yr, d  = series(MEN, s)
    _,  dc = series(MENCF, s)
    ax[2].plot(yr, d.gsic_med,  color=COL[s], lw=1.9, ls="-")
    ax[2].plot(yr, dc.gsic_med, color=COL[s], lw=1.6, ls="--")
ax[2].text(0.012, 0.93, "(c)  Mengel — posterior spread is too small; b=0.52 restores it",
           transform=ax[2].transAxes, fontsize=9.5, fontweight="bold", va="top")
sp_post = MEN[(MEN.year==2300)&(MEN.ssp=="SSP5-8.5")].gsic_med.values[0] - MEN[(MEN.year==2300)&(MEN.ssp=="SSP1-1.9")].gsic_med.values[0]
sp_cf   = MENCF[(MENCF.year==2300)&(MENCF.ssp=="SSP5-8.5")].gsic_med.values[0] - MENCF[(MENCF.year==2300)&(MENCF.ssp=="SSP1-1.9")].gsic_med.values[0]
ax[2].legend(handles=[Line2D([],[],color="0.3",ls="-", label=f"extA108 (b→0.89): {sp_post:.1f} cm spread @2300"),
                      Line2D([],[],color="0.3",ls="--",label=f"b=0.52 (Mengel-pub): {sp_cf:.1f} cm spread @2300")],
             fontsize=8, frameon=False, loc="lower right")

for a in (ax[1], ax[2]):
    a.set_ylim(0, ymax); a.axvline(2100, color="0.6", lw=0.8, ls=":")
    a.set_ylabel("cumulative glacier\nmelt (cm SLE, rel 1995–2014)")

# ---- (d) melt rate, low SSPs: WR vs Mengel (the commitment/stabilization signal) ----
for s in ["SSP1-1.9", "SSP1-2.6"]:
    for df, ls in [(WR, "-"), (MEN, "--")]:
        yr, d = series(df, s)
        ax[3].plot(yr, np.gradient(d.gsic_med.values, yr)*100, color=COL[s], lw=1.8, ls=ls)
ax[3].axhline(0, color="0.6", lw=0.8); ax[3].axvline(2100, color="0.6", lw=0.8, ls=":")
ax[3].set_ylabel("melt rate\n(cm / century)"); ax[3].set_xlabel("year"); ax[3].set_xlim(X0, X1)
ax[3].text(0.012, 0.93, "(d)  melt rate, low SSPs — WR solid stays high, Mengel dashed falls toward zero",
           transform=ax[3].transAxes, fontsize=9.5, fontweight="bold", va="top")
ax[3].legend(handles=[Line2D([],[],color=COL["SSP1-1.9"],label="SSP1-1.9"),
                      Line2D([],[],color=COL["SSP1-2.6"],label="SSP1-2.6")],
             fontsize=8, frameon=False, loc="center right")

fig.text(0.5, 0.004,
         "BRICK 2.0 WR posterior (parameters_subsample_brick.csv) vs Mengel gic_* (BRICK-AM extA108); 1000 draws each, "
         "FaIR 2.2.4 (calib1.4.5) SSP GMST.\nHistory constrains a·b, not b alone → the extA108 b saturates S_eq and "
         "compresses the scenario spread. Absolute magnitudes differ by calibration — the SHAPE is the point.",
         fontsize=6.6, ha="center", color="0.35")
fig.savefig("figures/ssps_gsic_wr_vs_mengel_2300.png", dpi=150, bbox_inches="tight")
print("wrote figures/ssps_gsic_wr_vs_mengel_2300.png")
