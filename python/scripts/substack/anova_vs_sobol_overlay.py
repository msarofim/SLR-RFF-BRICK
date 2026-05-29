"""
anova_vs_sobol_overlay.py
=========================

Cross-check figure: model-free balanced-factorial ANOVA (324k BRICK runs) vs the
Group-Sobol surrogate attribution of total ΔSLR variance. Side-by-side stacked
bars at landmark years show the two independent methods agree on the emissions,
climate, and internal shares (the headline validation), and that the
BRICK-related variance is the same total in both — they only split it differently
(ANOVA folds tipping/interactions into a single main-effect BRICK wedge).

Inputs (outputs/substack/):
  shapley_hs_per_axis_total_slr_anova324k.csv          (model-free ANOVA)
  shapley_hs_per_axis_total_slr_hybrid_tipping.csv     (Group-Sobol)

Output:
  outputs/substack/anova_vs_sobol_total_slr.{png,pdf}
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs" / "substack"

ANOVA_CSV = OUT / "shapley_hs_per_axis_total_slr_anova324k.csv"
SOBOL_CSV = OUT / "shapley_hs_per_axis_total_slr_hybrid_tipping.csv"
OUT_STEM = "anova_vs_sobol_total_slr"

LANDMARK_YEARS = [2050, 2100, 2150]
ANOVA_N_BRICK = "324,000"   # balanced factorial: rff300 × cfg60 × seed3 × post6

LABELS = {
    "internal":     "Internal variability (FaIR seeds)",
    "brick":        "BRICK posterior",
    "climate":      "Climate response (FaIR configs)",
    "emissions":    "Emissions (RFF-SP)",
    "tipping":      "AIS tipping nonlinearity",
    "interactions": "Interactions",
}
COLORS = {
    "emissions":    "#d95f02",
    "climate":      "#7570b3",
    "brick":        "#e7298a",
    "internal":     "#1b9e77",
    "tipping":      "#b15928",
    "interactions": "#999999",
}
# bottom→top stacking order (matches render_hybrid_tipping_split.py)
ORDER = ["internal", "brick", "climate", "emissions", "tipping", "interactions"]


def row_at(df: pd.DataFrame, year: int) -> dict:
    r = df[df.year == year].iloc[0]
    return {k: float(r[k]) if k in df.columns else 0.0 for k in ORDER}


def main() -> None:
    anova = pd.read_csv(ANOVA_CSV)
    sobol = pd.read_csv(SOBOL_CSV)

    fig, ax = plt.subplots(figsize=(9.0, 5.6))
    bar_w = 0.36
    gap = 0.06           # gap between the ANOVA/Sobol pair within a year
    group_centers = np.arange(len(LANDMARK_YEARS)) * 1.3

    method_specs = [("ANOVA", anova, -1), ("Sobol", sobol, +1)]

    bar_positions, bar_labels = [], []
    blended = ax.get_xaxis_transform()   # x in data coords, y in axes fraction
    for yi, year in enumerate(LANDMARK_YEARS):
        gc = group_centers[yi]
        for label, df, side in method_specs:
            x = gc + side * (bar_w / 2 + gap / 2)
            bar_positions.append(x)
            bar_labels.append(label)
            shares = row_at(df, year)
            bottom = 0.0
            for axis in ORDER:
                h = shares[axis]
                if h <= 0:
                    continue
                ax.bar(x, h, bar_w, bottom=bottom, color=COLORS[axis],
                       edgecolor="white", linewidth=0.4, alpha=0.9)
                bottom += h
        # year label as a lower second row, centered under the pair
        ax.text(gc, -0.115, str(year), transform=blended, ha="center",
                va="top", fontsize=12, fontweight="bold", color="#1F4E79")

    ax.set_xticks(bar_positions)
    ax.set_xticklabels(bar_labels, fontsize=8.5, color="#444444")
    ax.tick_params(axis="x", length=0)
    ax.set_ylabel("Share of total ΔSLR variance", fontsize=11)
    ax.set_ylim(0, 1.0)
    ax.set_xlim(group_centers[0] - 0.85, group_centers[-1] + 0.85)
    ax.spines[["top", "right"]].set_visible(False)

    fig.suptitle("Total ΔSLR variance attribution: model-free ANOVA vs Group-Sobol",
                 fontsize=13, fontweight="bold", color="#1F4E79", y=0.99)
    ax.set_title(
        f"Independent cross-check — ANOVA on a balanced {ANOVA_N_BRICK}-run BRICK "
        "factorial (no surrogate);\nGroup-Sobol from the importance-weighted HistGB surrogate.",
        fontsize=8.5, color="#444444", style="italic", pad=8)

    handles = [Patch(facecolor=COLORS[a], edgecolor="white", label=LABELS[a])
               for a in ["emissions", "climate", "brick", "interactions",
                         "tipping", "internal"]]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.18),
              ncol=3, frameon=False, fontsize=8.5)

    fig.tight_layout(rect=(0, 0.02, 1, 0.95))
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"{OUT_STEM}.{ext}", dpi=200, bbox_inches="tight")
    print(f"wrote {OUT}/{OUT_STEM}.{{png,pdf}}")

    # console summary of the agreement
    print("\n  agreement (emissions / climate / internal) and BRICK-bucket split:")
    for year in LANDMARK_YEARS:
        a = row_at(anova, year)
        s = row_at(sobol, year)
        a_brick_bucket = a["brick"] + a["interactions"] + a["tipping"]
        s_brick_bucket = s["brick"] + s["interactions"] + s["tipping"]
        print(f"    {year}: emi A={a['emissions']:.3f}/S={s['emissions']:.3f}  "
              f"clim A={a['climate']:.3f}/S={s['climate']:.3f}  "
              f"int A={a['internal']:.3f}/S={s['internal']:.3f}  "
              f"| BRICK-bucket A={a_brick_bucket:.3f}/S={s_brick_bucket:.3f}")


if __name__ == "__main__":
    main()
