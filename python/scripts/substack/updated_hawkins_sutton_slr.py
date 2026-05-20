"""
updated_hawkins_sutton_slr.py
=============================

Substack figure: Hawkins-Sutton-style 4-way variance decomposition of GMSL
(global sea-level rise), with a trajectory envelope on top.  Companion to
updated_hawkins_sutton.py for GMST.

Variance sources (all importance-weighted via Wong 2026 AR(1) likelihood
against Dangendorf 2024 observed GMSL):
  V_emissions   — Var_rff[ E_{cfg, seed, post}[ SLR(t) ] ]
  V_climate     — E_rff[ Var_cfg[ E_{seed, post}[ SLR(t) ] ] ]
  V_internal    — E_{rff, cfg}[ Var_seed[ E_post[ SLR(t) ] ] ]
  V_brick       — E_{rff, cfg, seed}[ Var_post[ SLR(t) ] ]

Plot anchored at 2020 (the first plot year, RFF-SP emissions-divergence
era), so per-source variance at the anchor year is 0 by construction and
internal/BRICK noise dominates the budget at the start.

Inputs:
  outputs/plots/hawkins_sutton_slr_4way.csv  (pre-computed by
                                              python/scripts/run_4way_slr_decomp.py)

Output:
  outputs/substack/updated_hawkins_sutton_slr.{png,pdf}
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
SRC_CSV = ROOT / "outputs" / "plots" / "hawkins_sutton_slr_4way.csv"
OUT     = ROOT / "outputs" / "substack"
OUT.mkdir(parents=True, exist_ok=True)

PLOT_START = 2020
PLOT_END   = 2150

# Observed GMSL anchor at 2020.  Trajectories are anchored at 2020 (Δ=0);
# this scalar lets us also annotate "cm rel year 2000" if desired.  NOAA
# STAR satellite altimetry (data/observations/nasa_gmsl_annual.csv):
# 2020 value rel 2000 ≈ +6.5 cm.
OBS_GMSL_2020_REL_2000_CM = 6.5

# Stacked-source colors (match GMST H-S figure where they line up).
COLORS = {
    "emissions": "#d95f02",
    "climate":   "#7570b3",
    "internal":  "#1b9e77",
    "brick":     "#e7298a",
}


def main():
    df = pd.read_csv(SRC_CSV)
    df = df[(df.year >= PLOT_START) & (df.year <= PLOT_END)].reset_index(drop=True)
    yp = df.year.to_numpy()

    fig, (ax_t, ax_b) = plt.subplots(2, 1, figsize=(9.5, 8.5),
                                     sharex=True,
                                     gridspec_kw={"height_ratios": [3, 2]})

    # ---- Top: trajectory envelope (anchored at 2020) ----
    ax_t.fill_between(yp, df.p5, df.p95, color="#dddddd",
                      label="5–95% across all (RFF × configs × seed × BRICK)")
    sigma = np.sqrt(df.V_total)
    ax_t.fill_between(yp, df["mean"] - sigma, df["mean"] + sigma,
                      color="#bbbbbb", label=r"$\pm 1\sigma$ total variance")
    ax_t.plot(yp, df["mean"], color="black", linewidth=2.2,
              label="Ensemble mean")
    ax_t.plot(yp, df.p50, color="black", linewidth=1.2, linestyle="--",
              label="Median")
    ax_t.axhline(0, color="grey", linewidth=0.6)
    ax_t.axvline(PLOT_START, color="#A6361C", linewidth=0.7, linestyle=":",
                 label=f"Anchor year ({PLOT_START})")
    ax_t.set_ylabel(f"ΔGMSL (cm, rel. {PLOT_START})", fontsize=11)
    ax_t.legend(loc="upper left", fontsize=10, framealpha=0.92)
    ax_t.set_title("Updated Hawkins-Sutton — GMSL envelope + variance "
                   f"decomposition, anchored at {PLOT_START}",
                   fontsize=13, fontweight="bold", color="#1F4E79")
    ax_t.grid(alpha=0.3, linewidth=0.5)

    # Right axis: rel year 2000 (project's standard SLR reference period).
    ax_t_r = ax_t.twinx()
    yl, yh = ax_t.get_ylim()
    ax_t_r.set_ylim(yl + OBS_GMSL_2020_REL_2000_CM, yh + OBS_GMSL_2020_REL_2000_CM)
    ax_t_r.set_ylabel(f"ΔGMSL (cm, rel. year 2000)\n"
                      f"  + {OBS_GMSL_2020_REL_2000_CM:.1f} cm at {PLOT_START} "
                      f"(NOAA STAR observed)",
                      fontsize=10, color="#555")
    ax_t_r.tick_params(labelcolor="#555")

    # ---- Bottom: stacked variance fractions (4-way) ----
    f_emi  = df.f_emissions.to_numpy()
    f_clim = df.f_climate.to_numpy()
    f_int  = df.f_internal.to_numpy()
    f_br   = df.f_brick.to_numpy()
    # Order top→bottom in the stack: emissions, climate, internal, BRICK
    ax_b.stackplot(yp, f_br, f_int, f_clim, f_emi,
                   labels=["BRICK posterior (AIS/GIS/TE sensitivity)",
                           "Internal variability (FaIR stochastic seed)",
                           "Climate configs (FaIR v2.2.4)",
                           "Emissions (RFF-SP)"],
                   colors=[COLORS["brick"], COLORS["internal"],
                           COLORS["climate"], COLORS["emissions"]],
                   alpha=0.85, edgecolor="white", linewidth=0.4)
    ax_b.set_xlim(PLOT_START, PLOT_END)
    ax_b.set_ylim(0, 1)
    ax_b.set_xlabel("Year", fontsize=11)
    ax_b.set_ylabel("Fraction of total variance", fontsize=11)
    # Reverse legend so order matches the visual top→bottom stack.
    h_, l_ = ax_b.get_legend_handles_labels()
    ax_b.legend(h_[::-1], l_[::-1],
                loc="center right", fontsize=9.5, framealpha=0.92)
    ax_b.grid(True, axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUT / "updated_hawkins_sutton_slr.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / "updated_hawkins_sutton_slr.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT / 'updated_hawkins_sutton_slr.png'}")

    # Headline values
    print()
    print("Key SLR values (cm, anchored at 2020):")
    for y in [2030, 2050, 2075, 2100, 2150]:
        if y not in yp: continue
        r = df[df.year == y].iloc[0]
        print(f"  {y}: mean={r['mean']:+.1f}  p5={r.p5:+.1f}  p50={r.p50:+.1f}  "
              f"p95={r.p95:+.1f}  "
              f"f_emi={r.f_emissions:.2f}  f_clim={r.f_climate:.2f}  "
              f"f_int={r.f_internal:.2f}  f_brick={r.f_brick:.2f}")


if __name__ == "__main__":
    main()
