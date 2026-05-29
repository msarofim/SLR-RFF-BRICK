"""Re-render hybrid total_slr H-S figure from cached diagnostic CSV.

Reads outputs/substack/v5_hybrid_decomp_diagnostic.csv (year-by-year absolute
variances from hybrid_hs_total_slr.py) and re-emits the figure with updated
labels per Marcus's 2026-05-27 conventions:
  - Simple parentheticals: (RFF-SP), (FaIR configs), (BRICK configs), (FaIR seeds)
  - Residual: (likely FaIR and BRICK config interactions plus tipping point nonlinearity)
  - Title: short. Methodology details in figure caption below the plot.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path("/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/outputs/substack")
d = pd.read_csv(OUT / "v5_hybrid_decomp_diagnostic.csv")
years = d.year.values

v_emi   = d.V_emissions.values
v_clim  = d.V_climate.values
v_brick = d.V_BRICK_modelfree.values
v_seed  = d.V_seed_modelfree.values
v_resid = d.V_residual_interactions.values
denom = v_emi + v_clim + v_brick + v_seed + v_resid

ax_cols = ["internal", "brick", "climate", "emissions", "residual"]
fracs = {
    "internal":  v_seed / denom,
    "brick":     v_brick / denom,
    "climate":   v_clim / denom,
    "emissions": v_emi / denom,
    "residual":  v_resid / denom,
}
# guard against year 2020 (V_total = 0)
for k in fracs:
    fracs[k] = np.nan_to_num(fracs[k], nan=0.0)

labels = {
    "internal":  "Internal variability (FaIR seeds)",
    "brick":     "BRICK posterior (BRICK configs)",
    "climate":   "Climate response (FaIR configs)",
    "emissions": "Emissions (RFF-SP)",
    "residual":  "Unattributed (likely FaIR and BRICK config interactions "
                  "plus tipping point nonlinearity)",
}
colors = {
    "emissions": "#d95f02",
    "climate":   "#7570b3",
    "brick":     "#e7298a",
    "internal":  "#1b9e77",
    "residual":  "#999999",
}

fig, ax = plt.subplots(figsize=(11, 5.8))
ax.stackplot(years, *[fracs[c] for c in ax_cols],
              labels=[labels[c] for c in ax_cols],
              colors=[colors[c] for c in ax_cols],
              alpha=0.88, edgecolor="white", linewidth=0.4)
ax.set_xlim(years.min(), years.max())
ax.set_ylim(0, 1)
ax.set_xlabel("Year", fontsize=11)
ax.set_ylabel("Fraction of ΔSLR variance", fontsize=11)
ax.set_title("Total ΔSLR (relative to 2020)",
              fontsize=13, fontweight="bold", color="#1F4E79")
h_, l_ = ax.get_legend_handles_labels()
ax.legend(h_[::-1], l_[::-1], loc="center right", fontsize=9.5, framealpha=0.92)
ax.grid(True, axis="y", alpha=0.3)

caption = ("Hybrid Hawkins-Sutton variance decomposition of total ΔSLR. "
            "Internal variability (FaIR seeds) and BRICK posterior are model-free "
            "estimates from within-cell variance across augmentation runs "
            "(10 seeds × 200 cells; 10 BRICK posts × 10,000 cells). "
            "Climate response (FaIR configs) and emissions (RFF-SP) come from "
            "Shapley TreeExplainer attribution on cfg + RFF features. "
            "Residual is V_total minus the four attributed axes.")
fig.text(0.5, -0.02, caption, ha="center", va="top", wrap=True,
          fontsize=8.5, color="#444444", style="italic")

fig.tight_layout()
fig.savefig(OUT / "shapley_hs_total_slr_hybrid.png", dpi=300, bbox_inches="tight")
fig.savefig(OUT / "shapley_hs_total_slr_hybrid.pdf", bbox_inches="tight")
print(f"wrote {OUT}/shapley_hs_total_slr_hybrid.{{png,pdf}}")
