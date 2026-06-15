#!/usr/bin/env python3
"""
Headline figure (Step 7) for the CO2/CH4 pulse->SLR / 3-BRICK-version study:
weighted marginal sea-level rise per unit pulse, decomposed by component, for
three BRICK versions.

Layout: 2 rows (species: CO2, CH4) x 3 cols (horizon: 2100, 2150, 2300).
Each panel shows, for x = {Total, AIS, GSIC, GIS, TE}, three grouped bars (one
per BRICK version) at the WEIGHTED median; the Total bars carry a weighted
5-95 % whisker (the headline marginal distribution). LWS is omitted (its
marginal is identically 0 -- the deterministic land-water add-on cancels in the
pulse-minus-baseline difference). Grouped-by-version medians (not a stacked
mean) are used deliberately because the marginals are heavily right-skewed
(mean >> median in the AIS-tipping tail), so a mean-stack would misrepresent the
central estimate.

Weights: pre93 + brick2 are Wong-importance-weighted to Dangendorf (ESS/N=0.5);
BRICK-Mengel is EQUAL-weighted (its posterior was MCMC-calibrated directly to
Dangendorf, so Wong would double-count).

Input : outputs/pulse3brick_v145/marginals_summary.csv (from
        python/scripts/extract_pulse_marginals_3brick.py)
Output: outputs/pulse3brick_marginals.png

All chart labels derive from the named constants below.
"""
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# --------------------------------------------------------------------------
# Named constants — every label/title/filename derives from these.
# --------------------------------------------------------------------------
REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
SUMMARY_CSV = os.path.join(REPO, "outputs/pulse3brick_v145/marginals_summary.csv")
OUT_PNG = os.path.join(REPO, "outputs/pulse3brick_marginals.png")

# Version order, display labels, colors, and weighting note.
VERSIONS = ["pre93", "brick2", "mengel"]
VERSION_LABEL = {
    "pre93":  "pre-#93 (BRICK v1.2.1)",
    "brick2": "BRICK 2.0 (v2.0.0)",
    "mengel": "BRICK-Mengel (v2.0.0)",
}
VERSION_COLOR = {
    "pre93":  "#c44e52",   # muted red
    "brick2": "#4c72b0",   # muted blue
    "mengel": "#55a868",   # muted green
}
WEIGHT_NOTE = {
    "pre93":  "Wong",
    "brick2": "Wong",
    "mengel": "equal",
}

# Species rows: pulse size + per-unit label.
SPECIES = ["co2", "ch4"]
SPECIES_TITLE = {"co2": "CO₂ pulse (0.01 GtCO₂)",
                 "ch4": "CH₄ pulse (1 TgCH₄)"}
SPECIES_UNIT = {"co2": "marginal SLR  (cm / GtCO₂)",
                "ch4": "marginal SLR  (cm / TgCH₄)"}

# Horizon columns.
YEARS = [2100, 2150, 2300]

# Component x-axis order + display labels (LWS omitted: marginal==0).
COMPONENTS = ["total", "ais", "gsic", "gis", "te"]
COMPONENT_LABEL = {"total": "Total", "ais": "AIS", "gsic": "GSIC",
                   "gis": "GIS", "te": "TE"}

FIG_SUPTITLE = ("Marginal sea-level rise per unit pulse, by component and BRICK version "
                "(FaIR-RFF LHS-10k, paired; weighted medians, Total 5–95 %)")


def main():
    df = pd.read_csv(SUMMARY_CSV)

    nrow, ncol = len(SPECIES), len(YEARS)
    fig, axes = plt.subplots(nrow, ncol, figsize=(15.0, 8.4))

    n_ver = len(VERSIONS)
    bar_w = 0.8 / n_ver
    xbase = np.arange(len(COMPONENTS))

    for r, sp in enumerate(SPECIES):
        for c, yr in enumerate(YEARS):
            ax = axes[r, c]
            sub = df[(df.species == sp) & (df.year == yr)]
            for vi, ver in enumerate(VERSIONS):
                s = sub[sub.version == ver].set_index("component")
                med = np.array([s.loc[comp, "q50"] for comp in COMPONENTS])
                xs = xbase + (vi - (n_ver - 1) / 2) * bar_w
                ax.bar(xs, med, width=bar_w, color=VERSION_COLOR[ver],
                       edgecolor="white", linewidth=0.4, zorder=2,
                       label=(f"{VERSION_LABEL[ver]} [{WEIGHT_NOTE[ver]}]" if (r == 0 and c == 0) else None))
                # 5-95 whisker on the Total bar only (the headline distribution).
                tot = s.loc["total"]
                ax.errorbar(xs[0], tot["q50"],
                            yerr=[[max(tot["q50"] - tot["q05"], 0)],
                                  [max(tot["q95"] - tot["q50"], 0)]],
                            fmt="none", ecolor="0.25", elinewidth=1.1,
                            capsize=2.5, zorder=3)

            ax.axhline(0, color="0.6", lw=0.6, zorder=1)
            ax.set_xticks(xbase)
            ax.set_xticklabels([COMPONENT_LABEL[c2] for c2 in COMPONENTS], fontsize=9)
            ax.set_title(f"{SPECIES_TITLE[sp].split(' pulse')[0]} — {yr}", fontsize=10.5)
            ax.grid(axis="y", color="0.9", lw=0.6, zorder=0)
            if c == 0:
                ax.set_ylabel(SPECIES_UNIT[sp], fontsize=9.5)
            ax.margins(x=0.02)
            ax.tick_params(labelsize=8.5)

    # Single legend (top), suptitle, methods footnote.
    handles = [Patch(facecolor=VERSION_COLOR[v], edgecolor="white",
                     label=f"{VERSION_LABEL[v]} [{WEIGHT_NOTE[v]}-weighted]")
               for v in VERSIONS]
    handles.append(plt.Line2D([0], [0], color="0.25", lw=1.1,
                              marker="_", label="Total 5–95 %"))
    fig.legend(handles=handles, loc="upper center", ncol=4, fontsize=9,
               frameon=False, bbox_to_anchor=(0.5, 0.975))
    fig.suptitle(FIG_SUPTITLE, fontsize=12, y=1.0)

    foot = ("Paired per-cell marginals (pulse − baseline) over the FaIR-RFF LHS-10k ensemble, "
            "differenced per BRICK posterior member and ÷ pulse size; LWS omitted (marginal≡0). "
            "pre-#93 & BRICK 2.0 Wong-weighted to Dangendorf 2024 (ESS/N=0.5); BRICK-Mengel equal-weighted. "
            "[ narrative / interpretation: placeholder for Marcus ]")
    fig.text(0.5, 0.005, foot, ha="center", va="bottom", fontsize=7.6, color="0.35")

    fig.tight_layout(rect=[0, 0.03, 1, 0.94])
    fig.savefig(OUT_PNG, dpi=200, bbox_inches="tight")
    print(f"wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
