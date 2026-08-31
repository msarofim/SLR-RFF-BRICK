#!/usr/bin/env python3
"""Glacier (GSIC) melt to 2300 under the seven van Vuuren CMIP7 markers: Wigley-Raper (BRICK 2.0) vs Mengel.

SIBLING of plot_ssps_gsic_wr_vs_mengel.py, which draws the same comparison on the six SSPs.

WHY THIS SET IS THE BETTER COMMITMENT TEST, and why it is a sibling rather than a flag:
  * FOUR of the seven markers PEAK AND DECLINE (Very Low, Low-to-Neg, Medium-to-Low,
    High-to-Low) against the SSP set's one (ssp119). The commitment question -- does glacier
    melt stabilize once temperature stops rising, or keep going? -- is exactly the question a
    decline pathway asks, and four of them ask it at four different PEAK levels (1.76, 1.90,
    2.37 and 2.96 K), which is a gradient the SSP set cannot supply.
  * It needs NO external comparator, so nothing is lost by leaving FACTS and MAGICC-SLR
    behind (they cannot be driven on van Vuuren -- see vv_model_comparison.py).
  * ⚠ IT DISSOLVES THE SSP FIGURE'S MIXED-VINTAGE CAVEAT. There, ssp126/245/585 are calib
    1.6.0 while ssp119/370/460 are still 1.4.5, so that figure's headline "spread @2300"
    straddles two calibrations and has to carry a dagger. All seven markers here come from
    ONE build on ONE calibration, which the provenance gate below ASSERTS rather than
    declares -- see _PROVENANCE_RULE.

Reads outputs/vv_gsic_2300{,_mengel,_mengel_b052}.csv, produced by
  julia --project=julia_v2 julia/project_ssps_gsic_2300.jl        --set=vv
  julia --project=julia_v2 julia/project_ssps_gsic_2300_mengel.jl --set=vv
"""
import os
import subprocess
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

_SRC = {"WR (vv_gsic_2300)":            "outputs/vv_gsic_2300.csv",
        "Mengel (vv_gsic_2300_mengel)": "outputs/vv_gsic_2300_mengel.csv",
        "Mengel b052":                  "outputs/vv_gsic_2300_mengel_b052.csv"}

## Marker order, labels, and colours all derive from ONE table, so a panel cannot be drawn
## in one order and legended in another. `decline` marks the peak-and-decline pathways --
## panel (d), the commitment panel, is built from exactly this flag and never from a
## hand-typed list, which is what went wrong in the SSP figure's "low SSPs" wording.
MARKERS = [
    ("Very Low",      "vvVL", "#00a9cf", True),
    ("Low-to-Neg",    "vvLN", "#1f78b4", True),
    ("Low",           "vvL",  "#003466", False),
    ("Medium-to-Low", "vvML", "#f69320", True),
    ("Medium",        "vvM",  "#c8a000", False),
    ("High-to-Low",   "vvHL", "#df0000", True),
    ("High",          "vvH",  "#7a0002", False),
]
LABELS = [m[0] for m in MARKERS]
KEY = {m[0]: m[1] for m in MARKERS}
COL = {m[0]: m[2] for m in MARKERS}
DECLINE = [m[0] for m in MARKERS if m[3]]
SPREAD_LO, SPREAD_HI = "Very Low", "High"
X0, X1 = 2000, 2300
OUTPNG = "figures/vv_gsic_wr_vs_mengel_2300.png"

## ---------------------------------------------------------------------------
## VINTAGE GATE, carried over from the SSP figure unchanged in intent. This figure's whole
## claim is "the same GMST drives all three arms", and on 2026-08-30 that stopped being
## true on the SSP side WITHOUT ANY EDIT TO THAT FILE. The gate reads the CAUSE: every
## input carries its own `gmst` column, so the forcing it was actually built on is
## checkable against the current fair_mean files. It prints the row count it compared, so
## a gate that matches nothing cannot report a pass.
def _forcing_delta(df):
    """max |file's own gmst - the CURRENT fair_mean gmst|, and how many rows matched."""
    d = df.drop_duplicates(["ssp", "year"])
    worst, n = 0.0, 0
    for lab, g in d.groupby("ssp"):
        key = KEY.get(lab)
        if key is None:
            continue
        f = "data/observations/fair_mean_gmst_%s.csv" % key
        if not os.path.exists(f):
            continue
        m = pd.read_csv(f).set_index("year")["gmst_C"].reindex(g.year.values).values
        ok = ~np.isnan(m)
        if not ok.any():
            continue
        worst = max(worst, float(np.nanmax(np.abs(g.gmst.values[ok] - m[ok]))))
        n += int(ok.sum())
    return worst, n


for _k, _v in _SRC.items():
    if not os.path.exists(_v):
        raise SystemExit(
            "missing %s -- produce the van Vuuren glacier arms first:\n"
            "  julia --project=julia_v2 julia/project_ssps_gsic_2300.jl        --set=vv\n"
            "  julia --project=julia_v2 julia/project_ssps_gsic_2300_mengel.jl --set=vv" % _v)
_loaded = {k: pd.read_csv(v) for k, v in _SRC.items()}
_delta = {k: _forcing_delta(v) for k, v in _loaded.items()}
if any(n == 0 for _, n in _delta.values()):
    raise SystemExit("[VINTAGE] compared ZERO rows for an input -- vacuous, not passing: "
                     + str({k: n for k, (_, n) in _delta.items()}))
_w = [w for w, _ in _delta.values()]
if max(_w) - min(_w) > 1e-6:
    raise SystemExit(
        "[VINTAGE] THE INPUTS ARE ON DIFFERENT FORCING VINTAGES, so 'same GMST drives all' "
        "is FALSE and this figure must not be drawn:\n"
        + "\n".join("    %-34s delta vs current fair_mean = %.4f K  (%d rows)" % (k, w, n)
                    for k, (w, n) in _delta.items())
        + "\n  Regenerate the lagging arm(s) with --set=vv. Do NOT relax this gate.")
## ⚠ THE SPREAD TEST ALONE IS BLIND TO ARMS THAT ARE ALL STALE TOGETHER (found 2026-08-31
## by mutation-testing: pointing one marker at an SSP driver produced a 1.4074 K delta on
## EVERY arm and this gate still printed "all arms share a forcing vintage"). It compares
## the arms against EACH OTHER; if the driver is regenerated after all three were built,
## they go stale in lockstep and the spread stays zero. That is the same failure in its
## all-together form, so the ABSOLUTE delta is now checked as well
## (`two_statistics_can_be_blind`). Both figures measure 0.0000 K today, so this is inert
## now and can only fire on a real regeneration.
_ABS_TOL_K = 1e-6
if max(_w) > _ABS_TOL_K:
    raise SystemExit(
        "[VINTAGE] every arm AGREES WITH THE OTHERS but ALL are stale against the current "
        "fair_mean drivers by up to %.4f K, so 'same GMST drives all' is true of the arms "
        "and FALSE of the figure:\n" % max(_w)
        + "\n".join("    %-34s delta = %.4f K  (%d rows)" % (k, w, n)
                     for k, (w, n) in _delta.items())
        + "\n  Regenerate the arms against the current drivers. Do NOT relax this gate.")
print("[VINTAGE] all %d ARMS share a forcing vintage (delta vs current fair_mean = %.4f K)"
      % (len(_SRC), _w[0]))

## ---------------------------------------------------------------------------
## CROSS-MARKER PROVENANCE GATE. The SSP version of this gate carries a hand-maintained
## table of (ssp -> commit, calibration) because that set genuinely straddles two
## calibrations and someone has to declare the mix. Here the claim is STRONGER and so the
## gate can be too: all seven markers were built by ONE run of build_fair_cube_vv_v160.py,
## so they must share a SINGLE commit -- which is checkable without declaring anything, and
## therefore cannot rot the way a typed table can. If a marker is ever rebuilt on its own,
## this fires and the "one calibration throughout" caption stops being drawable.
_PROVENANCE_RULE = "all seven van Vuuren drivers share one commit (one build, one calibration)"


def _driver_commit(key):
    out = subprocess.run(["git", "log", "-1", "--format=%h", "--",
                          "data/observations/fair_mean_gmst_%s.csv" % key],
                         capture_output=True, text=True)
    return out.stdout.strip()


_actual = {lab: _driver_commit(KEY[lab]) for lab in LABELS}
_missing = sorted(l for l, v in _actual.items() if not v)
if _missing:
    ## FATAL, not a warning. An "unverified" that still draws is the vacuous pass this gate
    ## exists to prevent.
    raise SystemExit(
        "[PROVENANCE] git returned nothing for %d of %d driver(s), so the calibration is "
        "UNVERIFIED and this figure must not be drawn: %s\n"
        "  Run from inside the SLR-RFF-BRICK checkout, with the drivers committed."
        % (len(_missing), len(_actual), _missing))
_commits = sorted(set(_actual.values()))
if len(_commits) != 1:
    raise SystemExit(
        "[PROVENANCE] %s -- but %d commits are present, so this figure's one-calibration "
        "claim is FALSE:\n%s\n  Rebuild the whole marker set in one run "
        "(scripts/build_fair_cube_vv_v160.py) or move the caption to the SSP figure's "
        "declared-mix form. Do NOT drop this gate."
        % (_PROVENANCE_RULE, len(_commits),
           "\n".join("    %-16s %s" % (l, c) for l, c in sorted(_actual.items()))))
_COMMIT = _commits[0]
print("[PROVENANCE] %s: %s (%d drivers verified)" % (_PROVENANCE_RULE, _COMMIT, len(_actual)))
_CALIB_NOTE = ("one build, one calibration throughout (calib 1.6.0 + CMIP7, driver commit %s) "
               "— each marker on its OWN CMIP7 land-use, irrigation and volcanic/solar "
               "forcing, so the marker→SSP mapping approximation is identically zero here"
               % _COMMIT)

WR, MEN, MENCF = (_loaded["WR (vv_gsic_2300)"],
                  _loaded["Mengel (vv_gsic_2300_mengel)"],
                  _loaded["Mengel b052"])


def series(df, lab):
    d = df[df.ssp == lab].sort_values("year")
    m = (d.year >= X0)
    return d.year[m].values, d[m]


def at(df, lab, y, col="gsic_med"):
    return df[(df.year == y) & (df.ssp == lab)][col].values[0]


fig, ax = plt.subplots(4, 1, figsize=(8.6, 12.2), sharex=True,
                       gridspec_kw=dict(height_ratios=[0.85, 1.2, 1.2, 0.95], hspace=0.13))

# ---- (a) GMST forcing ----
for s in LABELS:
    yr, d = series(WR, s)
    ax[0].plot(yr, d.gmst, color=COL[s], lw=1.8, label=s)
ax[0].set_ylabel("GMST (°C rel. PI)")
ax[0].set_title("Glacier (GSIC) melt to 2300 — Wigley–Raper (BRICK 2.0) vs Mengel, "
                "seven van Vuuren CMIP7 markers",
                fontsize=11, fontweight="bold", loc="left")
ax[0].legend(ncol=4, fontsize=7.5, frameon=False, loc="upper left")
_pk = {s: (WR[WR.ssp == s].set_index("year").gmst.loc[2015:2300].idxmax(),
           WR[WR.ssp == s].set_index("year").gmst.loc[2015:2300].max()) for s in DECLINE}
ax[0].annotate("%d peak-and-decline pathways\n(peaks %.2f–%.2f °C, %d–%d)"
               % (len(DECLINE), min(v for _, v in _pk.values()),
                  max(v for _, v in _pk.values()),
                  min(y for y, _ in _pk.values()), max(y for y, _ in _pk.values())),
               xy=(2235, 2.55), fontsize=7.5, color="0.3", ha="center")

ymax = max(WR.gsic_hi.max(), MENCF.gsic_hi.max()) * 1.02

# ---- (b) Wigley–Raper ----
for s in LABELS:
    yr, d = series(WR, s)
    ax[1].plot(yr, d.gsic_med, color=COL[s], lw=1.9)
    if s == SPREAD_LO:
        ax[1].fill_between(yr, d.gsic_lo, d.gsic_hi, color=COL[s], alpha=0.15, lw=0)
ax[1].text(0.012, 0.93, "(b)  Wigley–Raper (BRICK 2.0) — keeps melting toward a common "
           "ceiling even where T declines",
           transform=ax[1].transAxes, fontsize=9.5, fontweight="bold", va="top")

# ---- (c) Mengel: posterior (solid) + b=0.52 counterfactual (dashed) ----
for s in LABELS:
    yr, d = series(MEN, s)
    _, dc = series(MENCF, s)
    ax[2].plot(yr, d.gsic_med, color=COL[s], lw=1.9, ls="-")
    ax[2].plot(yr, dc.gsic_med, color=COL[s], lw=1.6, ls="--")
ax[2].text(0.012, 0.93, "(c)  Mengel — posterior spread is too small; b=0.52 restores it",
           transform=ax[2].transAxes, fontsize=9.5, fontweight="bold", va="top")
sp_post = at(MEN, SPREAD_HI, 2300) - at(MEN, SPREAD_LO, 2300)
sp_cf = at(MENCF, SPREAD_HI, 2300) - at(MENCF, SPREAD_LO, 2300)
## NO DAGGER. On the SSP figure this number straddles two calibrations and has to carry
## one; here the provenance gate above has proved it does not.
ax[2].legend(handles=[Line2D([], [], color="0.3", ls="-",
                             label=f"extA108 (b→0.89): {sp_post:.1f} cm spread @2300"),
                      Line2D([], [], color="0.3", ls="--",
                             label=f"b=0.52 (Mengel-pub): {sp_cf:.1f} cm spread @2300")],
             fontsize=8, frameon=False, loc="lower right")

for a in (ax[1], ax[2]):
    a.set_ylim(0, ymax)
    a.axvline(2100, color="0.6", lw=0.8, ls=":")
    a.set_ylabel("cumulative glacier\nmelt (cm SLE, rel 1995–2014)")

# ---- (d) melt rate on the FOUR decline pathways: WR vs Mengel ----
## THE COMMITMENT PANEL. Built from the DECLINE flag in MARKERS, not a typed list, so it
## cannot fall out of step with panel (a). Four peaks spanning 1.76-2.96 K turn the SSP
## figure's single ssp119 anecdote into a gradient.
for s in DECLINE:
    for df, ls in [(WR, "-"), (MEN, "--")]:
        yr, d = series(df, s)
        ax[3].plot(yr, np.gradient(d.gsic_med.values, yr) * 100, color=COL[s], lw=1.8, ls=ls)
ax[3].axhline(0, color="0.6", lw=0.8)
ax[3].axvline(2100, color="0.6", lw=0.8, ls=":")
ax[3].set_ylabel("melt rate\n(cm / century)")
ax[3].set_xlabel("year")
ax[3].set_xlim(X0, X1)
ax[3].text(0.012, 0.93, "(d)  melt rate on the %d peak-and-decline pathways — WR solid "
           "stays high, Mengel dashed falls toward zero" % len(DECLINE),
           transform=ax[3].transAxes, fontsize=9.5, fontweight="bold", va="top")
ax[3].legend(handles=[Line2D([], [], color=COL[s], label=s) for s in DECLINE]
             + [Line2D([], [], color="0.3", ls="-", label="Wigley–Raper"),
                Line2D([], [], color="0.3", ls="--", label="Mengel")],
             fontsize=8, frameon=False, loc="upper right",
             bbox_to_anchor=(1.0, 0.87), ncol=3)

fig.text(0.5, 0.004,
         "BRICK 2.0 WR posterior (parameters_subsample_brick.csv) vs Mengel gic_* (BRICK-AM extA108); "
         "1000 draws each, FaIR 2.2.4 (calib 1.6.0) van Vuuren marker GMST — "
         + _CALIB_NOTE + ".\nHistory constrains a·b, not b alone → the extA108 b saturates S_eq and "
         "compresses the scenario spread. Absolute magnitudes differ by calibration — the SHAPE is the point.",
         fontsize=6.6, ha="center", color="0.35")
fig.savefig(OUTPNG, dpi=150, bbox_inches="tight")
print("wrote " + OUTPNG)

## Console summary -- the numbers a caption would quote, so they never have to be read off
## the pixels.
print("\n%-16s %8s %8s %10s %10s %10s" % ("marker", "peak K", "@yr",
                                          "WR@2300", "Men@2300", "WR rate@2300"))
for s in LABELS:
    g = WR[WR.ssp == s].set_index("year").gmst.loc[2015:2300]
    yr, d = series(WR, s)
    rate = np.gradient(d.gsic_med.values, yr)[-1] * 100
    print("%-16s %8.2f %8d %10.2f %10.2f %10.2f"
          % (s, g.max(), g.idxmax(), at(WR, s, 2300), at(MEN, s, 2300), rate))
