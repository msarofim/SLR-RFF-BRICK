#!/usr/bin/env python3
"""
plot_gis_rate_power_scan.py — companion figure to scope_gis_rate_power_vs_literature.py.

  figures/gis_rate_power_scan_<TAG>.png

LEFT PANEL   the headline invariant: the ssp585/ssp245 ratio at 2300 across the
    (k, p) surface, one line per commitment scale k, colored by a single-hue
    sequential ramp (k is a magnitude). The literature band is shaded. The
    surface PEAKS in p and falls back — convexity's differential-equilibration
    boost self-limits because ssp245's 2300 driver also sits far above the
    anchor — and the peak never reaches the band.

RIGHT PANEL  why the peak cell is not a fix anyway: at the best k, raising p
    lifts ssp585 into its 2300 band only while pushing SSP1-2.6 and SSP2-4.5
    OVER theirs (and 2100 breaks, annotated). The three scenarios share one law;
    the literature separation would need a threshold BETWEEN their 2300 driver
    temperatures, not smooth convexity anchored at ~2 K.

Inputs  outputs/scope_gis_rate_power_vs_literature.csv   (run the scope first)

  python3 python/plot_gis_rate_power_scan.py [--tag L12]
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
FIGDIR = os.path.join(REPO, "figures")
SCAN = os.path.join(REPO, "outputs/scope_gis_rate_power_vs_literature.csv")

# --- named constants; every label and filename derives from these ------------
LADRILLO_TAG = "L12"
FIGSTEM = "gis_rate_power_scan"
LAW_LABEL = r"$r_f(T)=\alpha_f\bar{T}\,(\max(T,0)/\bar{T})^p+\beta_f$, slow channel unchanged"
K_SHOWN = [1.0, 3.0, 5.0, 8.0, 14.0, 22.6, 50.0]   # subset; full grid in the CSV
K_DIRECT_LABELED = [1.0, 14.0, 50.0]               # <=4 direct labels, rest legend
BEST_K = 14.0                                      # the peak-ratio k from the scan
## 2300 target bands. IMPORTED 2026-08-21g, not copied: this file used to carry
## its own literals, so correcting the ssp585 band (the PROTECT x2300 family at
## 13.8 K vs our ssp585's 7.8 K) could not reach it. `--targets=lit|matched`
## selects the set and the FIGURE FILENAME carries it, so a matched-set figure
## cannot be mistaken for the published literature-set one.
import gis_targets  # noqa: E402
LIT_2300_M, TARGET_SET = gis_targets.from_argv(sys.argv)
TARGET_WORD = gis_targets.SET_WORD[TARGET_SET]
# house Ladrillo SSP palette (plot_ladrillo_memo_figures.py) — color follows
# the entity across the figure set; every curve is also direct-labeled
SSP_COLOR = {"SSP1-2.6": "#1b7837", "SSP2-4.5": "#2166ac", "SSP5-8.5": "#b2182b"}
K_CMAP, K_CMAP_LO, K_CMAP_HI = "Blues", 0.35, 0.95  # single-hue ramp for k
LIT_BAND_COLOR = "0.55"
RATIO_AXIS = "ssp585 / ssp245 loss ratio at 2300"
LOSS_AXIS = "Greenland loss at 2300 (m SLE rel. 1995-2014)"
P_AXIS = "fast-channel rate exponent p (p=1 = incumbent linear law)"


def k_color(k):
    ks = np.log(K_SHOWN)
    t = (np.log(k) - ks.min()) / (ks.max() - ks.min())
    return plt.get_cmap(K_CMAP)(K_CMAP_LO + t * (K_CMAP_HI - K_CMAP_LO))


def panel_ratio(ax, d):
    lit_lo = LIT_2300_M["SSP5-8.5"][0] / LIT_2300_M["SSP2-4.5"][1]
    lit_hi = LIT_2300_M["SSP5-8.5"][1] / LIT_2300_M["SSP2-4.5"][0]
    ax.axhspan(lit_lo, lit_hi, color=LIT_BAND_COLOR, alpha=0.18, lw=0)
    ax.text(d.p.max(), lit_lo * 1.06, f"literature demands {lit_lo:.1f}-{lit_hi:.1f}x  ",
            ha="right", va="bottom", fontsize=7.5, color="0.30")
    for k in K_SHOWN:
        g = d[d.k == k].sort_values("p")
        ax.plot(g.p, g.ratio_585_over_245, color=k_color(k), lw=1.8,
                label=f"k = {k:g}", zorder=3)
        if k in K_DIRECT_LABELED:
            ax.annotate(f"k={k:g}", (g.p.iloc[-1], g.ratio_585_over_245.iloc[-1]),
                        textcoords="offset points", xytext=(4, 0), fontsize=7,
                        color=k_color(k), va="center")
    best = d.loc[d.ratio_585_over_245.idxmax()]
    ax.plot(best.p, best.ratio_585_over_245, "o", ms=6, mfc="none", mew=1.4,
            color="0.15", zorder=5)
    ax.annotate(f"peak {best.ratio_585_over_245:.2f}x\n(k={best.k:g}, p={best.p:g})",
                (best.p, best.ratio_585_over_245), textcoords="offset points",
                xytext=(8, 8), fontsize=7.5, color="0.15")
    ax.set_yscale("log")
    ax.set_yticks([1, 2, 3, 5, 8, 16, 32])
    ax.set_yticklabels(["1x", "2x", "3x", "5x", "8x", "16x", "32x"])
    ax.set_xlabel(P_AXIS)
    ax.set_ylabel(RATIO_AXIS)
    ax.set_title("The invariant: convexity lifts the ratio, then gives it back\n"
                 "(hindcast re-solved at every cell; the peak never reaches the band)",
                 fontsize=8.5, loc="left")
    ax.legend(fontsize=7, loc="upper left", frameon=False, ncol=2,
              title="commitment scale", title_fontsize=7)
    ax.grid(alpha=0.25, lw=0.5)


def panel_best_k(ax, d):
    g = d[d.k == BEST_K].sort_values("p")
    for lab, col in SSP_COLOR.items():
        lo, hi = LIT_2300_M[lab]
        ax.axhspan(lo, hi, color=col, alpha=0.12, lw=0)
        ax.plot(g.p, g[f"m2300_{lab}"], color=col, lw=1.8, zorder=3)
        ax.annotate(f" {lab}", (g.p.iloc[-1], g[f"m2300_{lab}"].iloc[-1]),
                    fontsize=7.5, color=col, va="center")
        ax.annotate(f"  band", (g.p.iloc[0], hi), fontsize=6, color=col,
                    va="bottom", ha="left")
    pk = g.loc[g.ratio_585_over_245.idxmax()]
    ax.axvline(pk.p, color="0.35", lw=0.9, ls=":", zorder=2)
    ax.annotate(f"peak-ratio cell:\n2100 spread {pk.g4_rel_to_ref:.1f}x its\n"
                f"accepted value (>15% = broken)",
                (pk.p, LIT_2300_M["SSP1-2.6"][0]), textcoords="offset points",
                xytext=(6, 2), fontsize=7, color="0.25", va="bottom")
    ax.set_yscale("log")
    ax.set_xlabel(P_AXIS)
    ax.set_ylabel(LOSS_AXIS)
    ax.set_title(f"At the best k (= {BEST_K:g}): one law moves all three scenarios\n"
                 "ssp585 enters its band only while the cooler two sit far over theirs",
                 fontsize=8.5, loc="left")
    ax.grid(alpha=0.25, lw=0.5, axis="y")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default=LADRILLO_TAG)
    args = ap.parse_args()

    d = pd.read_csv(SCAN)
    d = d[d.tag == args.tag]
    if not len(d):
        raise SystemExit(f"{SCAN} carries no rows tagged {args.tag} — "
                         f"run scope_gis_rate_power_vs_literature.py first")

    os.makedirs(FIGDIR, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.6))
    panel_ratio(axes[0], d)
    panel_best_k(axes[1], d)
    fig.suptitle(f"Greenland: a convex fast-channel rate cannot reach the "
                 f"literature's scenario separation   —   Ladrillo {args.tag}, "
                 f"median params, offline\n{LAW_LABEL}",
                 fontsize=9.5, x=0.005, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    out = gis_targets.out_path(
        os.path.join(FIGDIR, f"{FIGSTEM}_{args.tag}.png"), TARGET_SET)
    fig.savefig(out, dpi=180)
    plt.close(fig)
    print(f"wrote {os.path.relpath(out, REPO)}")


if __name__ == "__main__":
    main()
