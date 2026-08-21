#!/usr/bin/env python3
"""
plot_gis_basin_mock.py — companion figure to scope_gis_basin_mock_vs_literature.py.

  figures/gis_basin_mock_<TAG>.png

LEFT PANEL   what the multi-basin structure DOES, on one exemplar passing cell:
    Greenland loss trajectories per SSP, basin model (solid) against the shipped
    A+B (dashed). The dormant basins are inert until ssp585's GMT crosses their
    onsets (marked), so SSP1-2.6 and SSP2-4.5 are bit-identical to the shipped
    model — the fix acts ONLY on the defective column. 2300 literature bands at
    the right edge.

RIGHT PANEL  robustness: how many grid cells pass the full scorecard at each
    (high-basin onset, tau), counted over the volume/share/mid-onset knobs.
    The question is whether the pass region is a plateau or a knife-edge.

Inputs  outputs/scope_gis_basin_mock_vs_literature.csv   (run the scope first)

  python3 python/plot_gis_basin_mock.py [--tag L12]
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
import scope_gis_leq_ridge_vs_literature as ridge  # noqa: E402
from scope_gis_basin_mock_vs_literature import dormant_unit  # noqa: E402
from scope_gis_2300_relaxation import (  # noqa: E402
    IREF, YEARS, gis_shape_table, gmst_rebased, regional_driver,
)

FIGDIR = os.path.join(REPO, "figures")
SCAN = os.path.join(REPO, "outputs/scope_gis_basin_mock_vs_literature.csv")

# --- named constants; every label and filename derives from these ------------
LADRILLO_TAG = "L12"
FIGSTEM = "gis_basin_mock"
## 2300 target bands. IMPORTED 2026-08-21g, not copied: this file used to carry
## its own literals, so correcting the ssp585 band (the PROTECT x2300 family at
## 13.8 K vs our ssp585's 7.8 K) could not reach it. `--targets=lit|matched`
## selects the set and the FIGURE FILENAME carries it, so a matched-set figure
## cannot be mistaken for the published literature-set one.
import gis_targets  # noqa: E402
LIT_2300_M, TARGET_SET = gis_targets.from_argv(sys.argv)
TARGET_WORD = gis_targets.SET_WORD[TARGET_SET]
SSP_COLOR = {"SSP1-2.6": "#1b7837", "SSP2-4.5": "#2166ac", "SSP5-8.5": "#b2182b"}
PLOT_Y0 = 2000                    # left-panel time window start
COUNT_CMAP = "Blues"
LOSS_AXIS = "Greenland loss (m SLE rel. 1995-2014)"


def exemplar_cell(d):
    """The widest-585-margin passing cell — same pick rule as the scope's
    exemplar table (first row)."""
    w = d[d.all_pass].copy()
    mid585 = 0.5 * sum(LIT_2300_M["SSP5-8.5"])
    w["margin"] = -(w["m2300_SSP5-8.5"] - mid585).abs()
    return w.sort_values("margin", ascending=False).iloc[0]


def trajectories(cell):
    """Recompute the exemplar's per-SSP series with the scope's own pieces:
    shipped A+B (k=1, s re-bisected on the hindcast) + the two dormant basins."""
    post = pd.read_csv(ridge.POST)
    tbar = ridge.gis_tbar()
    pa = ridge.native_greenland(post.median(numeric_only=True), tbar)
    S = gis_shape_table()
    tgt = pd.read_csv(ridge.TARGETS).set_index("year")["gis"]
    want_cm = float(tgt.loc[ridge.HIND[1]] - tgt.loc[ridge.HIND[0]])
    ih0 = int(np.where(YEARS == ridge.HIND[0])[0][0])
    ih1 = int(np.where(YEARS == ridge.HIND[1])[0][0])

    drivers, gmt = {}, {}
    for ssp, label in ridge.SSPS:
        _, rb = gmst_rebased(ssp)
        gmt[label] = rb
        drivers[label] = regional_driver(rb, np.array([pa["gis_amp"]]), S)[0]
    Th = drivers[dict(ridge.SSPS)[ridge.HIND_DRIVER]]
    lo, hi = 1e-4, 1e3
    for _ in range(80):
        mid = np.sqrt(lo * hi)
        L = ridge.ab_series(Th, pa, 1.0, mid)[0]
        if 100.0 * (L[ih1] - L[ih0]) < want_cm:
            lo = mid
        else:
            hi = mid
    s1 = float(np.sqrt(lo * hi))

    out = {}
    for _, lab in ridge.SSPS:
        inc = ridge.ab_series(drivers[lab], pa, 1.0, s1)[0]
        inc = inc - inc[IREF].mean()
        dorm = (cell.v_mid * dormant_unit(gmt[lab], cell.t_on_mid, cell.tau)
                + cell.v_high * dormant_unit(gmt[lab], cell.t_on_high, cell.tau))
        out[lab] = (inc, inc + dorm)
    cross = {t: (int(YEARS[np.argmax(gmt["SSP5-8.5"] >= t)])
                 if (gmt["SSP5-8.5"] >= t).any() else None)
             for t in (cell.t_on_mid, cell.t_on_high)}
    return out, cross


def panel_trajectories(ax, cell, series, cross):
    m = YEARS >= PLOT_Y0
    for lab, col in SSP_COLOR.items():
        inc, tot = series[lab]
        ax.plot(YEARS[m], tot[m], color=col, lw=1.9, zorder=3)
        ax.plot(YEARS[m], inc[m], color=col, lw=1.2, ls="--", zorder=2)
        ax.annotate(f" {lab}", (YEARS[-1], tot[-1]), fontsize=7.5, color=col,
                    va="center")
        lo, hi = LIT_2300_M[lab]
        ax.plot([2302, 2302], [lo, hi], color=col, lw=5, alpha=0.45,
                solid_capstyle="butt", zorder=1)
    for t_on, yr in cross.items():
        if yr and yr > PLOT_Y0:
            ax.axvline(yr, color="0.5", lw=0.8, ls=":", zorder=1)
            ax.annotate(f"ssp585 crosses {t_on:g} K\n({yr})", (yr, 0.92),
                        fontsize=6.5, color="0.35", ha="right", va="top",
                        rotation=90, xycoords=("data", "axes fraction"))
    ax.plot([], [], color="0.3", lw=1.9, label="basin model")
    ax.plot([], [], color="0.3", lw=1.2, ls="--", label="shipped A+B")
    ax.set_xlim(PLOT_Y0, 2340)
    ax.set_xlabel("year")
    ax.set_ylabel(LOSS_AXIS)
    ax.set_title("Dormant basins act ONLY on the defective column\n"
                 f"exemplar: onsets {cell.t_on_mid:g}/{cell.t_on_high:g} K GMT, "
                 f"V = {cell.v_tot:g} m ({1 - cell.mid_share:.0%} high), "
                 f"tau = {cell.tau:g} yr  —  bars = 2300 literature bands",
                 fontsize=8.5, loc="left")
    ax.legend(fontsize=7.5, loc="upper left", frameon=False)
    ax.grid(alpha=0.25, lw=0.5)


def panel_region(ax, d):
    t_highs = sorted(d.t_on_high.unique())
    taus = sorted(d.tau.unique())
    cnt = np.zeros((len(taus), len(t_highs)))
    tot = np.zeros_like(cnt)
    for i, tau in enumerate(taus):
        for j, th in enumerate(t_highs):
            sub = d[(d.tau == tau) & (d.t_on_high == th)]
            cnt[i, j] = int(sub.all_pass.sum())
            tot[i, j] = len(sub)
    im = ax.imshow(cnt, cmap=COUNT_CMAP, origin="lower", aspect="auto",
                   vmin=0, vmax=cnt.max())
    for i in range(len(taus)):
        for j in range(len(t_highs)):
            v = int(cnt[i, j])
            ax.text(j, i, f"{v}", ha="center", va="center", fontsize=9,
                    color="white" if v > 0.6 * cnt.max() else "0.15")
    ax.set_xticks(range(len(t_highs)))
    ax.set_xticklabels([f"{t:g}" for t in t_highs])
    ax.set_yticks(range(len(taus)))
    ax.set_yticklabels([f"{t:g}" for t in taus])
    ax.set_xlabel("high-basin onset (K GMT rel. 1850-1900)")
    ax.set_ylabel("basin e-folding time tau (yr)")
    ax.set_title("Passing cells per (onset, tau) — counted over the\n"
                 f"volume / share / mid-onset knobs "
                 f"({int(tot.min())}-{int(tot.max())} combos per cell)",
                 fontsize=8.5, loc="left")
    plt.colorbar(im, ax=ax, shrink=0.85, label="cells passing the full scorecard")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default=LADRILLO_TAG)
    args = ap.parse_args()

    d = pd.read_csv(SCAN)
    d = d[d.tag == args.tag]
    if not len(d):
        raise SystemExit(f"{SCAN} carries no rows tagged {args.tag} — "
                         f"run scope_gis_basin_mock_vs_literature.py first")

    cell = exemplar_cell(d)
    series, cross = trajectories(cell)

    os.makedirs(FIGDIR, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.6),
                             gridspec_kw={"width_ratios": [1.35, 1.0]})
    panel_trajectories(axes[0], cell, series, cross)
    panel_region(axes[1], d)
    fig.suptitle("Greenland as basins: staggered onsets clear the whole 2300 "
                 f"scorecard offline   —   Ladrillo {args.tag} + dormant-basin "
                 "mock, median params",
                 fontsize=10, x=0.005, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    out = gis_targets.out_path(
        os.path.join(FIGDIR, f"{FIGSTEM}_{args.tag}.png"), TARGET_SET)
    fig.savefig(out, dpi=180)
    plt.close(fig)
    print(f"wrote {os.path.relpath(out, REPO)}")


if __name__ == "__main__":
    main()
