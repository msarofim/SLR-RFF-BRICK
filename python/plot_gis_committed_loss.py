#!/usr/bin/env python3
"""
plot_gis_committed_loss.py — the companion figure to diag_gis_committed_loss.py.

  figures/gis_committed_loss_<TAG>.png

LEFT PANEL   the Bochow-2023 equilibrium ladder, both model families, drawn as
    the STEP functions they are. Rungs are the only places either model was run;
    the segments between them are drawn flat rather than sloped so the figure
    cannot suggest a resolution the ladder does not have. Each family's own
    unresolved transition interval is shaded, and the SSP warming levels are
    marked where they fall.

RIGHT PANEL  the committed loss beside the sea level actually realised by the
    horizon year, per SSP. The committed bars span the bracketing rungs; the
    realised marker carries the posterior 5-95 band. Log axis, because the two
    quantities differ by one to two orders of magnitude — which IS the finding.

The two panels answer different questions and are deliberately not merged: the
left is a multi-millennial equilibrium, the right puts it beside a 2300
projection. Nothing here is a projection of the commitment being realised.

Inputs  outputs/diag_gis_committed_loss.csv   (run diag_gis_committed_loss.py first)
        data/observations/greenland_equilibrium_bochow2023.csv

  python3 python/plot_gis_committed_loss.py [--tag L12]
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
from diag_ladder_transition_resolution import (  # noqa: E402
    GMT_COL, LOSS_COL, transition_report,
)

FIGDIR = os.path.join(REPO, "figures")
LADDER = os.path.join(REPO, "data/observations/greenland_equilibrium_bochow2023.csv")
DIAG = os.path.join(REPO, "outputs/diag_gis_committed_loss.csv")

# --- named constants; every label and filename derives from these ------------
LADRILLO_TAG = "L12"
FIGSTEM = "gis_committed_loss"
EQUILIBRIUM_LABEL = "committed loss, multi-millennial equilibrium"
REALISED_LABEL = "realised by"
LADDER_CITE = "Bochow et al. 2023, Nature 622:528"
GMT_AXIS = "sustained GMT (K, rel. 1850-1900)"
LOSS_AXIS = "Greenland sea-level equivalent (m)"
PLOT_LEVEL = "y2300"        # which evaluation level the right panel shows
COLOR = {"PISM-dEBM": "#1f6fb4", "Yelmo-REMBO": "#c1442e"}
LADDER_YMAX = 8.6           # left-panel y limit; the label positions derive from it
UNRESOLVED_LABEL_Y = 0.28 * LADDER_YMAX
SSP_LABEL_Y = 0.985 * LADDER_YMAX
REALISED_COLOR = "#222222"
SSP_ORDER = ["SSP1-2.6", "SSP2-4.5", "SSP5-8.5"]


def panel_ladder(ax, fams, jumps, d):
    for m, g in fams.items():
        T = g[GMT_COL].to_numpy()
        L = g[LOSS_COL].to_numpy()
        # flat between rungs: the model was only ever run AT the rungs
        ax.step(np.append(T, T[-1] + 0.6), np.append(L, L[-1]),
                where="post", color=COLOR[m], lw=1.8, label=m, zorder=3)
        ax.plot(T, L, "o", color=COLOR[m], ms=3.5, zorder=4)
        j = jumps[m]
        ax.axvspan(j["jump_lo_K"], j["jump_hi_K"], color=COLOR[m],
                   alpha=0.18, lw=0, zorder=1)
        # sits in the open band between the two families' steps, so the label
        # never collides with the curves, the SSP marks or the title
        ax.text(0.5 * (j["jump_lo_K"] + j["jump_hi_K"]), UNRESOLVED_LABEL_Y,
                "transition unresolved", color=COLOR[m], fontsize=6.5,
                ha="center", va="bottom", rotation=90, zorder=5)

    lv = d[d.level == PLOT_LEVEL].drop_duplicates("ssp").set_index("ssp")
    for s in SSP_ORDER:
        T = float(lv.loc[s, "gmt_K"])
        ax.axvline(T, color="0.35", lw=0.9, ls=":", zorder=2)
        ax.text(T, SSP_LABEL_Y, f"{s} ", rotation=90, fontsize=7,
                color="0.25", ha="right", va="top", zorder=5)

    ax.set_xlabel(GMT_AXIS)
    ax.set_ylabel(LOSS_AXIS)
    ax.set_title(f"The equilibrium ladder ({LADDER_CITE})\n"
                 "steps, not curves: rungs are the only levels either model was run at",
                 fontsize=8.5, loc="left")
    ax.set_xlim(0.2, 8.2)
    ax.set_ylim(0, LADDER_YMAX)
    ax.legend(fontsize=7.5, loc="lower right", frameon=False)
    ax.grid(alpha=0.25, lw=0.5)


def panel_compare(ax, d, horizon):
    lv = d[d.level == PLOT_LEVEL]
    models = list(COLOR)
    width = 0.26
    for i, s in enumerate(SSP_ORDER):
        sub = lv[lv.ssp == s]
        for k, m in enumerate(models):
            r = sub[sub.model == m].iloc[0]
            lo, hi = float(r.committed_lo_m), float(r.committed_hi_m)
            x = i + (k - 1) * width
            if r.saturated:
                ax.plot([x], [lo], marker="_", ms=16, mew=2.5, color=COLOR[m])
                ax.annotate("sat.", (x, lo), textcoords="offset points",
                            xytext=(0, 6), ha="center", fontsize=6, color=COLOR[m])
            else:
                ax.bar(x, hi - lo, bottom=lo, width=width * 0.85,
                       color=COLOR[m], alpha=0.75,
                       label=m if i == 0 else None)
                if r.straddles_transition:
                    ax.annotate("straddles the\nunresolved step", (x, hi),
                                textcoords="offset points", xytext=(0, 5),
                                ha="center", fontsize=6, color=COLOR[m])
        r = sub.iloc[0]
        x = i + width
        ax.errorbar([x], [r.realised_horizon_m],
                    yerr=[[r.realised_horizon_m - r.realised_horizon_p05_m],
                          [r.realised_horizon_p95_m - r.realised_horizon_m]],
                    fmt="o", ms=5, color=REALISED_COLOR, capsize=3, lw=1.4,
                    label=f"{REALISED_LABEL} {horizon} ({LADRILLO_TAG}, 5-95%)"
                    if i == 0 else None, zorder=5)
        ax.annotate(f"{100 * sub.frac_discharged_by_horizon.min():.1f}–"
                    f"{100 * sub.frac_discharged_by_horizon.max():.1f}%",
                    (x, r.realised_horizon_p05_m), textcoords="offset points",
                    xytext=(0, -14), ha="center", fontsize=7,
                    color=REALISED_COLOR)

    ax.set_yscale("log")
    ax.set_xticks(range(len(SSP_ORDER)))
    ax.set_xticklabels(SSP_ORDER)
    ax.set_ylabel(LOSS_AXIS)
    ax.set_ylim(0.03, 30)
    ax.set_title(f"{EQUILIBRIUM_LABEL} vs sea level realised by {horizon}\n"
                 "percentage = the fraction of the commitment discharged by then",
                 fontsize=8.5, loc="left")
    ax.legend(fontsize=7, loc="upper left", frameon=False, ncol=1)
    ax.grid(alpha=0.25, lw=0.5, axis="y")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default=LADRILLO_TAG)
    args = ap.parse_args()

    d = pd.read_csv(DIAG)
    d = d[d.ladrillo_tag == args.tag]
    if not len(d):
        raise SystemExit(f"{DIAG} carries no rows tagged {args.tag} — "
                         f"run diag_gis_committed_loss.py --tag {args.tag} first")
    horizon = int(d.horizon_year.iloc[0])

    ladder = pd.read_csv(LADDER)
    fams = {m: g.sort_values(GMT_COL).reset_index(drop=True)
            for m, g in ladder.groupby("model")}
    jumps = {m: transition_report(m, g) for m, g in fams.items()}

    os.makedirs(FIGDIR, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.6))
    panel_ladder(axes[0], fams, jumps, d)
    panel_compare(axes[1], d, horizon)
    fig.suptitle(f"Greenland: what is committed, and what is realised by {horizon}"
                 f"   —   Ladrillo {args.tag}",
                 fontsize=10.5, x=0.005, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    out = os.path.join(FIGDIR, f"{FIGSTEM}_{args.tag}.png")
    fig.savefig(out, dpi=180)
    plt.close(fig)
    print(f"wrote {os.path.relpath(out, REPO)}")


if __name__ == "__main__":
    main()
