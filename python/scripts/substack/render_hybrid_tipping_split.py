"""Render hybrid H-S figures with tipping-vs-interactions split.

Reads unclipped + p99-clipped hybrid decompositions and emits 6-wedge figures:
  internal (FaIR seeds) — bottom
  BRICK posterior (BRICK configs)
  Climate response (FaIR configs)
  Emissions (RFF-SP)
  Tipping nonlinearity (V_residual_unclipped - V_residual_clipped)
  Unattributed interactions (V_residual_clipped) — top
"""
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path("/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/outputs/substack")

# Display-only temporal smoothing to suppress per-year Sobol Monte-Carlo jitter.
# The underlying variance fractions evolve on decadal scales; sub-decadal wiggle
# is estimation noise. Raw per-year CSVs are unchanged. Set to 1 to disable.
SMOOTH_WIN = 11


def _smooth(a, win=SMOOTH_WIN):
    a = np.asarray(a, float)
    if win <= 1 or a.size < win:
        return a
    pad = win // 2
    ap = np.pad(a, (pad, pad), mode="edge")
    return np.convolve(ap, np.ones(win) / win, mode="valid")[:a.size]

LABELS = {
    "internal":     "Internal variability (FaIR seeds)",
    "brick":        "BRICK posterior (BRICK configs)",
    "climate":      "Climate response (FaIR configs)",
    "emissions":    "Emissions (RFF-SP)",
    "tipping":      "AIS tipping nonlinearity",
    "interactions": "Interactions (climate × BRICK, emissions × BRICK)",
}
COLORS = {
    "emissions":    "#d95f02",
    "climate":      "#7570b3",
    "brick":        "#e7298a",
    "internal":     "#1b9e77",
    "tipping":      "#b15928",
    "interactions": "#999999",
}
ORDER = ["internal", "brick", "climate", "emissions", "tipping", "interactions"]


def render(target_name, title_text, caption_text):
    """Decomposition framework:
       - V_emi, V_clim, V_BRICK, V_seed, V_residual_interactions all from
         the p99-CLIPPED hybrid run (so within-linear-regime quantities).
       - V_tipping = V_total_unclipped - V_total_clipped (variance lost to
         the top-1% tipping tail).
       - Denominator = V_total_unclipped, so the six wedges sum to exactly
         V_total_unclipped.
       Why use clipped axes: unclipped V_BRICK on the pulse marginal is
       dominated by a tiny tail of AIS-tipping cells (per-cell variance
       O(1e+3) (cm/GtCO2)²), which makes the within-linear-regime BRICK
       contribution invisible. Clipping isolates the linear-regime answer
       (~45% BRICK in pulse), then the tipping tail becomes its own wedge."""
    unc = pd.read_csv(OUT / f"v5_hybrid_decomp_{target_name}_unclip.csv")
    clp = pd.read_csv(OUT / f"v5_hybrid_decomp_{target_name}_clip.csv")
    years = unc.year.values

    v_emi   = clp.V_emissions.values
    v_clim  = clp.V_climate.values
    v_brick = clp.V_brick.values
    v_seed  = clp.V_seed.values
    v_resid_clp = clp.V_residual.values
    v_total_unc = unc.V_total.values
    v_total_clp = clp.V_total.values

    v_tipping = np.maximum(v_total_unc - v_total_clp, 0.0)
    v_interactions = v_resid_clp

    parts = dict(internal=v_seed, brick=v_brick, climate=v_clim, emissions=v_emi,
                  tipping=v_tipping, interactions=v_interactions)
    parts = {k: _smooth(v) for k, v in parts.items()}   # display smoothing
    denom = sum(parts.values())
    fracs = {k: np.nan_to_num(parts[k] / denom, nan=0.0) for k in parts}

    fig, ax = plt.subplots(figsize=(11, 5.8))
    ax.stackplot(years, *[fracs[c] for c in ORDER],
                  labels=[LABELS[c] for c in ORDER],
                  colors=[COLORS[c] for c in ORDER],
                  alpha=0.88, edgecolor="white", linewidth=0.4)
    ax.set_xlim(years.min(), years.max())
    ax.set_ylim(0, 1)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("Fraction of variance", fontsize=11)
    ax.set_title(title_text, fontsize=13, fontweight="bold", color="#1F4E79")
    h_, l_ = ax.get_legend_handles_labels()
    ax.legend(h_[::-1], l_[::-1], loc="center right", fontsize=9.0, framealpha=0.92)
    ax.grid(True, axis="y", alpha=0.3)
    fig.text(0.5, -0.02, caption_text, ha="center", va="top", wrap=True,
              fontsize=8.5, color="#444444", style="italic")
    fig.tight_layout()
    fig.savefig(OUT / f"shapley_hs_{target_name}_slr_hybrid_tipping.png",
                  dpi=300, bbox_inches="tight")
    fig.savefig(OUT / f"shapley_hs_{target_name}_slr_hybrid_tipping.pdf",
                  bbox_inches="tight")
    print(f"wrote {OUT}/shapley_hs_{target_name}_slr_hybrid_tipping.{{png,pdf}}")

    # Fraction CSV
    frac_df = pd.DataFrame(dict(year=years, **fracs))
    frac_df.to_csv(OUT / f"shapley_hs_per_axis_{target_name}_slr_hybrid_tipping.csv", index=False)

    # Headline numbers
    print(f"  Fractions at landmark years ({target_name}):")
    for y in [2025, 2050, 2100, 2150]:
        if y not in years: continue
        i = int(np.where(years == y)[0][0])
        s = " ".join([f"{c}={fracs[c][i]:.3f}" for c in ORDER])
        print(f"    {y}: {s}")


CAPTION_TOTAL = (
    "Group-Sobol Hawkins-Sutton variance decomposition of total ΔSLR. "
    "Emissions (RFF-SP), climate response (FaIR configs), and BRICK posterior are "
    "grouped first-order Sobol indices from a HistGB surrogate (Saltelli pick-and-"
    "freeze, importance weighted); interactions = aggregate total-minus-first-order "
    "(climate × BRICK, emissions × BRICK). Internal variability (FaIR seeds) is "
    "the model-free seed-augmentation estimate. AIS tipping nonlinearity = variance "
    "lost when the target is p99-clipped per year. Shares are normalized to the "
    "surrogate-explained variance (OOF R² ≈ 0.8→0.7 over 2050→2150); the residual "
    "model-unresolved variance is not shown."
)
CAPTION_PULSE = (
    "Group-Sobol Hawkins-Sutton variance decomposition of pulse-marginal ΔSLR "
    "(per GtCO₂, 2030 pulse). Matched-seed paired difference cancels internal "
    "variability by construction (V_internal = 0). Emissions (RFF-SP), climate "
    "(FaIR configs), and BRICK posterior are grouped first-order Sobol indices "
    "from a HistGB surrogate (Saltelli, importance weighted); interactions = total-"
    "minus-first-order. AIS tipping nonlinearity = variance lost when the target "
    "is p99-clipped per year. Shares normalized to the surrogate-explained variance; "
    "the residual model-unresolved variance is not shown."
)


if __name__ == "__main__":
    render("total", "Total ΔSLR (relative to 2020)", CAPTION_TOTAL)
    render("pulse", "Pulse-marginal ΔSLR (per GtCO₂, 2030 pulse)", CAPTION_PULSE)
