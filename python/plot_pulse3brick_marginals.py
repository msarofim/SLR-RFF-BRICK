#!/usr/bin/env python3
"""
Headline figure (Step 7) for the CO2/CH4 pulse->SLR / 3-BRICK-version study:
weighted marginal sea-level rise per unit pulse, decomposed by component, for
three BRICK versions — with CH4 expressed in CO2-EQUIVALENT so the two gases are
directly comparable.

CH4 is converted cm/TgCH4 -> cm/GtCO2eq via x(1000/GWP100_CH4) with the AR6
GWP-100 NON-FOSSIL value (27.0): the FaIR CH4 pulse has no CH4->CO2 oxidation
(verified empirically; the only CO2 response is the climate-carbon feedback,
which AR6 GWP already embeds for both fossil and non-fossil). The FOSSIL CH4
variant is deliberately EXCLUDED from this headline: our fossil construction
co-emits the oxidation CO2 as an instantaneous pulse, whereas a real fossil
pulse releases it gradually over the methane oxidation lifetime; the fossil
sensitivity lives in headline_table_fossil_ch4.md, not here.

Layout: 2 rows (CO2, CH4-as-CO2eq) x 3 cols (horizon 2100/2150/2300). Each panel:
x = {Total, AIS, GSIC, GIS, TE}, grouped bars per BRICK version at the WEIGHTED
median; Total bars carry weighted 5-95% whiskers. Y-axis is SHARED per horizon
column (both gas rows), so bar heights are directly comparable across gases:
CH4-as-CO2eq towers over CO2 near-term and falls below it by 2300 (the
short-lived-forcer crossover). Grouped median bars (not a stacked mean) because
the marginals are heavily right-skewed (mean >> median in the AIS-tipping tail);
LWS omitted (marginal == 0). All labels derive from the named constants below.

Input : outputs/pulse3brick_v145/marginals_summary.csv
Output: outputs/pulse3brick_marginals.png
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

# CH4 -> CO2eq conversion (AR6 WG1 Table 7.15 non-fossil GWP-100).
GWP100_CH4_NONFOSSIL = 27.0
CH4_TO_CO2EQ = 1000.0 / GWP100_CH4_NONFOSSIL    # cm/TgCH4 -> cm/GtCO2eq
SPECIES_SCALE = {"co2": 1.0, "ch4": CH4_TO_CO2EQ}

VERSIONS = ["pre93", "brick2", "mengel"]
VERSION_LABEL = {
    "pre93":  "pre-#93 (BRICK v1.2.1)",
    "brick2": "BRICK 2.0 (v2.0.0)",
    "mengel": "BRICK-Mengel (v2.0.0)",
}
VERSION_COLOR = {"pre93": "#c44e52", "brick2": "#4c72b0", "mengel": "#55a868"}
WEIGHT_NOTE = {"pre93": "Wong", "brick2": "Wong", "mengel": "equal"}

SPECIES = ["co2", "ch4"]
SPECIES_TITLE = {"co2": "CO₂ pulse", "ch4": "CH₄ pulse (as CO₂eq, GWP-100=27)"}
SPECIES_UNIT = {"co2": "marginal SLR  (cm / GtCO₂)",
                "ch4": "marginal SLR  (cm / GtCO₂eq)"}

YEARS = [2100, 2150, 2300]
COMPONENTS = ["total", "ais", "gsic", "gis", "te"]   # LWS omitted (marginal==0)
COMPONENT_LABEL = {"total": "Total", "ais": "AIS", "gsic": "GSIC",
                   "gis": "GIS", "te": "TE"}

FIG_SUPTITLE = ("Marginal sea-level rise per unit pulse, by component and BRICK version "
                "— CO₂ vs CH₄(as CO₂eq)\n(FaIR-RFF LHS-10k, paired; weighted medians, "
                "Total 5–95 %; y-axis shared per horizon)")


def val(df, sp, ver, yr, comp, field):
    s = df[(df.species == sp) & (df.version == ver) & (df.year == yr)
           & (df.component == comp)]
    return float(s[field].iloc[0]) * SPECIES_SCALE[sp]


def main():
    df = pd.read_csv(SUMMARY_CSV)

    nrow, ncol = len(SPECIES), len(YEARS)
    fig, axes = plt.subplots(nrow, ncol, figsize=(15.0, 8.4))
    n_ver = len(VERSIONS)
    bar_w = 0.8 / n_ver
    xbase = np.arange(len(COMPONENTS))

    # Per-horizon-column shared y-limits (across both gas rows), from the data:
    # top = max Total q95 (whisker) and max component q50; bottom = min(0, any neg).
    col_ylim = {}
    for c, yr in enumerate(YEARS):
        tops, bots = [], [0.0]
        for sp in SPECIES:
            for ver in VERSIONS:
                tops.append(val(df, sp, ver, yr, "total", "q95"))
                bots.append(val(df, sp, ver, yr, "total", "q05"))
                for comp in COMPONENTS:
                    tops.append(val(df, sp, ver, yr, comp, "q50"))
                    bots.append(val(df, sp, ver, yr, comp, "q50"))
        top, bot = max(tops), min(bots)
        pad = 0.06 * (top - bot)
        col_ylim[yr] = (bot - pad if bot < 0 else 0.0, top + pad)

    for r, sp in enumerate(SPECIES):
        for c, yr in enumerate(YEARS):
            ax = axes[r, c]
            for vi, ver in enumerate(VERSIONS):
                med = np.array([val(df, sp, ver, yr, comp, "q50") for comp in COMPONENTS])
                xs = xbase + (vi - (n_ver - 1) / 2) * bar_w
                ax.bar(xs, med, width=bar_w, color=VERSION_COLOR[ver],
                       edgecolor="white", linewidth=0.4, zorder=2)
                q05 = val(df, sp, ver, yr, "total", "q05")
                q50 = val(df, sp, ver, yr, "total", "q50")
                q95 = val(df, sp, ver, yr, "total", "q95")
                ax.errorbar(xs[0], q50, yerr=[[max(q50 - q05, 0)], [max(q95 - q50, 0)]],
                            fmt="none", ecolor="0.25", elinewidth=1.1, capsize=2.5, zorder=3)
            ax.axhline(0, color="0.6", lw=0.6, zorder=1)
            ax.set_xticks(xbase)
            ax.set_xticklabels([COMPONENT_LABEL[c2] for c2 in COMPONENTS], fontsize=9)
            ax.set_title(f"{SPECIES_TITLE[sp]} — {yr}", fontsize=10)
            ax.grid(axis="y", color="0.9", lw=0.6, zorder=0)
            ax.set_ylim(*col_ylim[yr])
            if c == 0:
                ax.set_ylabel(SPECIES_UNIT[sp], fontsize=9.5)
            ax.margins(x=0.02)
            ax.tick_params(labelsize=8.5)

    handles = [Patch(facecolor=VERSION_COLOR[v], edgecolor="white",
                     label=f"{VERSION_LABEL[v]} [{WEIGHT_NOTE[v]}-weighted]")
               for v in VERSIONS]
    handles.append(plt.Line2D([0], [0], color="0.25", lw=1.1, marker="_",
                              label="Total 5–95 %"))
    fig.legend(handles=handles, loc="upper center", ncol=4, fontsize=9,
               frameon=False, bbox_to_anchor=(0.5, 0.965))
    fig.suptitle(FIG_SUPTITLE, fontsize=12, y=1.005)

    foot = ("Paired per-cell marginals (pulse − baseline) over the FaIR-RFF LHS-10k ensemble, "
            "÷ pulse size; CH₄ ×(1000/27.0)=×37.04 to CO₂eq (AR6 non-fossil GWP-100; FaIR pulse has "
            "no CH₄→CO₂ oxidation — verified). Fossil CH₄ excluded (instantaneous oxidation-CO₂ is "
            "inexact; see headline_table_fossil_ch4.md). LWS omitted (marginal≡0). pre-#93 & BRICK 2.0 "
            "Wong-weighted to Dangendorf 2024 (ESS/N=0.5); BRICK-Mengel equal-weighted. "
            "[ narrative / interpretation: placeholder for Marcus ]")
    fig.text(0.5, 0.004, foot, ha="center", va="bottom", fontsize=7.4, color="0.35")

    fig.tight_layout(rect=[0, 0.03, 1, 0.93])
    fig.savefig(OUT_PNG, dpi=200, bbox_inches="tight")
    print(f"wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
