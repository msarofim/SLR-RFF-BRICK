#!/usr/bin/env python3
"""
SSP GMSL projections to 2100 — MCMC-calibrated BRICK-Mengel posterior ensemble.

Successor to plot_ssp_projections_ensemble.py (which plotted the OLD posterior with
a v2.0.0-vs-knob split + Dangendorf weighting). The Mengel MCMC posterior IS the
calibration and is already Dangendorf-conditioned, so there is ONE unweighted band.

Panels:
  (a) @2100 dot-and-whisker by SSP: BRICK-Mengel median + 5-95% PARAMETRIC band,
      vs OLD BRICK (stock single-reservoir glacier, old posterior) and vs AR6
      median + likely (17-83%) range. The AR6 likely range makes explicit that our
      parametric band (parameter unc. only) is NARROWER than AR6's multi-method
      range — it excludes structural + obs-noise uncertainty.
  (b) ensemble trajectories 2000-2100 with 5-95% bands.
  (c) 2100 component decomposition (median, cm) for SSP1-1.9 / SSP2-4.5 / SSP5-8.5,
      paired Mengel vs OLD BRICK. Headline: the Mengel 2-tau glacier projects far
      LESS glacier (GSIC) loss than the old single-reservoir model (which over-
      commits melt) — ~6 cm vs ~11-16 cm @2100.

LWS note: the landwater_storage contribution is NOT calibrated here — it is the
MimiBRICK v2.0.0 default component (net groundwater depletion - reservoir
impoundment), identical between old BRICK and Mengel, ~2.3-2.9 cm and climate-
independent.

Inputs: outputs/proj_ssps_mengel{SUF}_{summary,timeseries}.csv (Mengel posterior),
        outputs/proj_ssps_ensemble_summary.csv (old BRICK, v2.0.0 unweighted).
        All cm, rel 1995-2014.
Output: outputs/ssp_projections_2100_mengel{SUF}.png

  python python/plot_ssp_projections_mengel.py [TAG]   # ""=2018-baseline (default) | "ext"=extended
"""
import os, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.lines as ml

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
TAG  = sys.argv[1] if len(sys.argv) > 1 else ""           # ""=2018-baseline; "ext"=post-2018-extended
SUF  = "" if TAG == "" else f"_{TAG}"
CALLABEL = "2018-baseline" if TAG == "" else "post-2018-extended (GRACE-FO/GlaMBIE/NOAA)"
S = pd.read_csv(os.path.join(REPO, f"outputs/proj_ssps_mengel{SUF}_summary.csv"))
T = pd.read_csv(os.path.join(REPO, f"outputs/proj_ssps_mengel{SUF}_timeseries.csv"))
# OLD BRICK (stock single-reservoir glacier, old posterior): v2.0.0 unweighted rows
O = pd.read_csv(os.path.join(REPO, "outputs/proj_ssps_ensemble_summary.csv"))
O = O[(O.calib == "v2.0.0") & (O.weighting == "unweighted")]
OUT = os.path.join(REPO, f"outputs/ssp_projections_2100_mengel{SUF}.png")
NDRAWS = pd.read_csv(os.path.join(REPO, f"data/MimiBRICK/parameters_subsample_brick_mengel{SUF}.csv")).shape[0]

ORDER = ["SSP1-1.9", "SSP1-2.6", "SSP2-4.5", "SSP4-6.0", "SSP3-7.0", "SSP5-8.5"]
COL = dict(zip(ORDER, plt.cm.viridis(np.linspace(0.05, 0.92, len(ORDER)))))
# AR6 medium-confidence GMSL @2100 rel 1995-2014 (cm): median, (likely 17-83 lo, hi). No SSP4-6.0.
AR6 = {"SSP1-1.9": (38, 28, 55), "SSP1-2.6": (44, 32, 62), "SSP2-4.5": (56, 44, 76),
       "SSP3-7.0": (68, 55, 90), "SSP5-8.5": (77, 63, 101)}

def get(ssp): return S[S.ssp_label == ssp].iloc[0]
def getold(ssp): return O[O.ssp_label == ssp].iloc[0]

fig, (axa, axb, axc) = plt.subplots(1, 3, figsize=(18, 5.7))
x = np.arange(len(ORDER))
BLUE, RED, GREY = "#1763b8", "crimson", "#8a97a3"

# ---- (a) dot-and-whisker @2100: OLD BRICK vs BRICK-Mengel vs AR6 ----
for s in ORDER:
    xi = ORDER.index(s); r = get(s); o = getold(s)
    # old BRICK (grey, left)
    axa.plot([xi-0.24]*2, [o.p05, o.p95], color=GREY, lw=2.4, solid_capstyle="round", zorder=2)
    axa.plot(xi-0.24, o.p50, "s", color=GREY, ms=6, zorder=3)
    # BRICK-Mengel (blue, center)
    axa.plot([xi]*2, [r.p05, r.p95], color=BLUE, lw=2.4, solid_capstyle="round", zorder=2)
    axa.plot(xi, r.p50, "o", color=BLUE, ms=7, zorder=3)
    axa.text(xi, r.p95 + 2.5, f"{r.p50:.0f}", ha="center", fontsize=8, color=BLUE)
    # AR6 (red, right)
    if s in AR6:
        med, lo, hi = AR6[s]
        axa.plot([xi+0.24]*2, [lo, hi], color=RED, lw=2.4, solid_capstyle="round", zorder=2, alpha=0.8)
        axa.plot(xi+0.24, med, "D", color=RED, ms=6, zorder=3)
axa.legend(handles=[
    ml.Line2D([], [], color=GREY, marker="s", lw=2.4, label="old BRICK (single-res. glacier, old post.; 5–95%)"),
    ml.Line2D([], [], color=BLUE, marker="o", lw=2.4, label="BRICK-Mengel (median, 5–95% parametric)"),
    ml.Line2D([], [], color=RED, marker="D", lw=2.4, label="AR6 medium-conf. (median, likely 17–83%)"),
], fontsize=7.6, loc="upper left")
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

# ---- (c) 2100 component decomposition (median): Mengel vs OLD BRICK, 3 scenarios ----
SEL = ["SSP1-1.9", "SSP2-4.5", "SSP5-8.5"]
comps = [("ais", "AIS", "#1763b8"), ("gsic", "GSIC", "#0f9b6c"), ("gis", "GIS", "#b8480f"),
         ("te", "TE", "#9b1fb8"), ("lws", "LWS", "#8a97a3")]
xc = np.arange(len(SEL)); bw = 0.36
MAJOR = {"ais", "gsic", "gis", "te"}    # label the 4 major contributions in-block (skip small LWS)
for off, src, tag in [(-bw/2-0.01, get, "Mengel"), (+bw/2+0.01, getold, "old")]:
    bottom = np.zeros(len(SEL))
    for key, lab, c in comps:
        vals = np.array([src(s)[key] for s in SEL])
        axc.bar(xc + off, vals, bw, bottom=bottom, color=c,
                label=lab if tag == "Mengel" else None,
                hatch=("" if tag == "Mengel" else "///"), edgecolor="white", linewidth=0.3)
        if key in MAJOR:
            for i in range(len(SEL)):
                if vals[i] >= 2.5:      # only when the block is tall enough to fit the number
                    axc.text(xc[i] + off, bottom[i] + vals[i]/2, f"{vals[i]:.0f}",
                             ha="center", va="center", fontsize=6.5, color="white", fontweight="bold")
        bottom += vals
    for i, s in enumerate(SEL):
        tot = sum(src(s)[k] for k, _, _ in comps)
        axc.text(xc[i] + off, tot + 1.5, f"{tot:.0f}", ha="center", fontsize=7.5, color="0.2")
axc.set_xticks(xc); axc.set_xticklabels(SEL)
axc.set_ylabel("GMSL @2100 component (cm, median)")
axc.set_title("(c) 2100 component decomposition (median)\nMengel (solid) vs old BRICK (hatched): "
              "Mengel glacier (GSIC) << old single-reservoir")
# component legend + a hatched proxy explaining old BRICK
handles, labels = axc.get_legend_handles_labels()
handles.append(ml.Line2D([], [], color="0.4", marker="s", lw=0, markersize=9,
                         markerfacecolor="0.7", label="/// = old BRICK"))
axc.legend(handles=handles, fontsize=7.6, loc="upper left", ncol=2)
axc.grid(axis="y", alpha=0.25)

fig.suptitle(f"BRICK-Mengel GMSL projections to 2100 — {CALLABEL} calibration, {NDRAWS:,}-draw MCMC posterior, FaIR v1.4.5-forced (unweighted)\n"
             "Posterior already Dangendorf-conditioned (no importance weighting). High-forcing median runs high vs "
             "AR6 via the per-draw AIS-MICI threshold; low-forcing runs below AR6 (GIS/GSIC undershoot)",
             fontsize=10.5)
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(OUT, dpi=140)
print(f"[wrote {OUT}]")
