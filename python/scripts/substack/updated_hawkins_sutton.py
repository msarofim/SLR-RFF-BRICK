"""
updated_hawkins_sutton.py
=========================

Substack figure (revisits Sarofim et al. 2024 Fig 4):
Hawkins-Sutton-style variance decomposition of GMST, anchored to the FIRST
PLOT YEAR (2020) rather than preindustrial.

The original Fig 4 (Sarofim 2024, Nat Commun) baselined anomalies to
preindustrial (1850-1900), so the year-2015 variance already had a big
climate-sensitivity contribution from differences in pre-2015 warming
between FaIR configs.  The standard Hawkins-Sutton convention is to
anchor at the first year of the plot, so V_climate at that year is zero
and internal variability dominates the initial budget.  We also start the
plot at the emissions-divergence year (RFF-SPs begin to spread ~2020).

Methodological note: Sarofim 2024 used REAL FaIR stochastic seed variance
for V_internal, sampled OFAT (one factor at a time — varying the seed
around a fixed (rff, cfg) centroid).  This figure uses the ANOVA factorial
approach: V_internal(t) is the expectation over the full (rff, cfg) grid
of Var across seeds, which integrates over the response surface rather
than measuring sensitivity at one operating point.

Source cubes:
  Emissions × climate variance from the deterministic 398-RFF × 841-cfg cube
  outputs/lhs_pilot_gmst_full_N200_to2300.npz (1850-2300).

  Internal variability from the local stochastic FaIR run
  outputs/lhs_pilot_gmst_full_stoch_test.npz
  (10 RFFs × 841 configs × 10 seeds × 251 years, 1850-2100).  V_internal(t) is
  E_{rff,cfg}[ Var_seed[GMST(t)] ] computed on this 4D cube.  For years
  past 2100 (beyond the stoch cube's coverage) the 2090-2100 mean is held
  constant — FaIR's stochastic GMST σ is roughly time-stationary at long
  horizons (~0.33 °C through 2050-2100).

Decomposition:
  V_emissions(t)  = Var_rff[ E_cfg[GMST(t)] ]                  (deterministic cube)
  V_climate(t)    = E_rff[ Var_cfg[GMST(t)] ]                  (deterministic cube)
  V_internal(t)   = E_{rff,cfg}[ Var_seed[GMST(t)] ]           (stochastic cube)
  V_total         = sum of the three (assumed independent)

Output:
  outputs/substack/updated_hawkins_sutton.{png,pdf}
  outputs/substack/updated_hawkins_sutton_data.csv
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
# v1.4.5 cubes (flat schema). LHS-10k provides emissions+climate variance via
# 10000 unique (rff, cfg, seed) cells from the canonical 10k-RFF inventory.
# ANOVA-18k provides seed-variance for V_internal via the 3-seed factorial.
DET_CUBE   = (Path.home() / "Documents/2026/CodeProjects/FaIRtoFrEDI"
              / "fair_outputs/cubes_v145/cube_v145_lhs10k_baseline.npz")
STOCH_CUBE = (Path.home() / "Documents/2026/CodeProjects/FaIRtoFrEDI"
              / "fair_outputs/cubes_v145/cube_v145_anova18k_baseline.npz")
OUT  = ROOT / "outputs" / "substack"
OUT.mkdir(parents=True, exist_ok=True)

BASELINE_YEAR  = 2020          # anchor for the stochastic cube V_internal calc
                               #  (anchor-invariant for variance; used as a
                               #  convenience single-year index inside that helper)
PLOT_START     = 2020
PLOT_END       = 2150
# AR6-style bias correction: rebaseline each trajectory to its own recent
# observed decadal mean, then express absolute warming on a rel-PI axis using
# the observed Berkeley Earth value over that period.  FaIR v2.2.4 runs ~0.29 °C
# cooler than BE at 2015-2024 on the ensemble median; bias correction respects
# observed present and aligns with AR6's projection framing.
RECENT_BASELINE  = (2015, 2024)
OBS_RECENT_REL_PI = 1.254        # IGCC 2024 4-dataset consensus 2015-2024 mean
                                 # rel 1850-1900 (Forster et al. 2025 ESSD,
                                 # Walsh GMST timeseries, total_p50 mean of
                                 # HadCRUT5 + Berkeley Earth + GISTEMP + NOAA;
                                 # 5-95% obs uncertainty: [+1.151, +1.342] °C).
                                 # Replaced BE-only +1.323 °C on 2026-05-19
                                 # since FaIR-calibrate v1.4.1 is constrained
                                 # against the AR6/IGCC observational ensemble.

# Decomp colors (match poster Panel C palette)
COLORS = {
    "emissions": "#d95f02",
    "climate":   "#7570b3",
    "internal":  "#1b9e77",
}


def compute_real_internal(stoch_cube_path, det_years, baseline_year):
    """Year-by-year V_internal(t) from the v1.4.5 ANOVA-18k cube's
    seed-dimension variance.

    ANOVA-18k schema: cells_meta is (n_cells, 3) = (rff, cfg, seed); gmst_traj
    is (n_cells, n_year). Each (rff, cfg) appears with multiple seeds, so we
    can group by (rff, cfg) and compute Var_seed.

    Returns an array aligned with det_years. ANOVA-18k covers 1850-2300 like
    the LHS-10k cube, so no tail-fill needed.
    """
    nz = np.load(stoch_cube_path, allow_pickle=True)
    sy = np.asarray(nz["years"], dtype=np.int64)
    cm = np.asarray(nz["cells_meta"], dtype=np.int64)
    sg = np.asarray(nz["gmst_traj"], dtype=np.float64)
    assert sg.ndim == 2, f"v145 ANOVA cube should be 2D (n_cells, n_year); got {sg.shape}"

    # Anchor each trajectory to its own baseline_year value so V_internal is
    # the variance of (GMST(t) − GMST(baseline)) across seeds at each (rff, cfg).
    if baseline_year in sy:
        ib = int(np.where(sy == baseline_year)[0][0])
        sg_anom = sg - sg[:, [ib]]
    else:
        sg_anom = sg

    # Group cells by (rff, cfg) and compute per-(rff, cfg, year) Var_seed.
    df = pd.DataFrame({"rff": cm[:, 0], "cfg": cm[:, 1]})
    # Build a per-(rff, cfg) list of cell indices
    groups = df.groupby(["rff", "cfg"], sort=False).indices  # dict (rff,cfg) -> array of row idxs
    n_yr = sg.shape[1]
    v_seed_per_rc = np.zeros((len(groups), n_yr))
    for k, idxs in enumerate(groups.values()):
        if len(idxs) > 1:
            v_seed_per_rc[k, :] = sg_anom[idxs, :].var(axis=0, ddof=0)
    v_internal_stoch = v_seed_per_rc.mean(axis=0)  # E_{rff,cfg}[ Var_seed ]

    # Re-index to det_years.  ANOVA cube years should match LHS cube years exactly.
    v_internal_out = np.zeros(len(det_years))
    for k, y in enumerate(det_years):
        y = int(y)
        idx = np.where(sy == y)[0]
        if len(idx):
            v_internal_out[k] = float(v_internal_stoch[idx[0]])
        else:
            # Should not happen if both cubes are 1850-2300; defensive fallback.
            v_internal_out[k] = float(v_internal_stoch[-1])
    return v_internal_out


def main():
    # ---- Variance decomp + envelope from the v1.4.5 ANOVA-18k factorial ----
    # The flat cube has cells_meta = (rff_idx, fair_cfg_idx, seed_idx) per row,
    # gmst_traj is (n_cells, n_year). 400 RFFs × 15 cfgs × 3 seeds = 18000.
    # We grouped by (rff) to get V_emissions, then by (rff, cfg) for V_climate,
    # then by (rff, cfg) again for V_internal across seeds.
    nz = np.load(DET_CUBE, allow_pickle=True)
    years = np.asarray(nz["years"], dtype=np.int64)
    n_yr = len(years)
    # ANOVA-18k cube is used for the variance components.  LHS-10k could be
    # used for the envelope only, but ANOVA-18k 400-RFF gives consistent
    # baseline statistics (verified ±8% vs LHS-10k in project_v145_anova_sample_stability).
    nz_a = np.load(STOCH_CUBE, allow_pickle=True)
    years_a = np.asarray(nz_a["years"], dtype=np.int64)
    assert (years == years_a).all(), "LHS-10k and ANOVA-18k year grids must match"
    cm = np.asarray(nz_a["cells_meta"], dtype=np.int64)
    cube = np.asarray(nz_a["gmst_traj"], dtype=np.float64)
    n_cells = cube.shape[0]
    print(f"loaded ANOVA-18k cube for variance decomp: {n_cells} cells × {n_yr} years")

    # AR6 bias correction: anchor each trajectory at its own RECENT_BASELINE
    # decadal mean, then shift by IGCC observed anchor to express on a rel-PI
    # axis.  Variance decomposition itself is anchor-invariant.
    recent_mask = (years >= RECENT_BASELINE[0]) & (years <= RECENT_BASELINE[1])
    traj_recent = cube[:, recent_mask].mean(axis=1, keepdims=True)
    cube_anom   = cube - traj_recent + OBS_RECENT_REL_PI

    var_total     = np.zeros(n_yr)
    var_emissions = np.zeros(n_yr)
    var_climate   = np.zeros(n_yr)
    mean_traj     = np.zeros(n_yr)
    p5_traj       = np.zeros(n_yr)
    p95_traj      = np.zeros(n_yr)

    # Build group indices once
    df_keys = pd.DataFrame({"rff": cm[:, 0], "cfg": cm[:, 1]})
    rff_groups = df_keys.groupby("rff", sort=False).indices            # rff -> idx
    rc_groups  = df_keys.groupby(["rff","cfg"], sort=False).indices    # (rff, cfg) -> idx

    for t in range(n_yr):
        v = cube_anom[:, t]
        var_total[t] = float(v.var(ddof=0))
        # E_{cfg, seed} v | rff   →   Var_rff
        rff_means = np.array([v[idxs].mean() for idxs in rff_groups.values()])
        var_emissions[t] = float(rff_means.var(ddof=0))
        # E_seed v | (rff, cfg)   →   Var_cfg within rff   →   E_rff
        rc_means = np.array([v[idxs].mean() for idxs in rc_groups.values()])
        # Map back to (rff, cfg) labels for grouping by rff
        rc_keys = list(rc_groups.keys())
        df_rc = pd.DataFrame({"rff":[r for r, _ in rc_keys],
                              "cfg":[c for _, c in rc_keys],
                              "mean":rc_means})
        v_cfg_per_rff = df_rc.groupby("rff", sort=False)["mean"].var(ddof=0)
        var_climate[t] = float(v_cfg_per_rff.mean())
        mean_traj[t] = float(v.mean())
        p5_traj[t]   = float(np.percentile(v, 5))
        p95_traj[t]  = float(np.percentile(v, 95))

    # V_internal: seed variance per (rff, cfg), averaged.
    print(f"computing V_internal from ANOVA-18k seed dimension ...")
    var_internal = compute_real_internal(STOCH_CUBE, years, BASELINE_YEAR)
    var_modelled = var_emissions + var_climate + var_internal

    # ---- save data ----
    df = pd.DataFrame({
        "year":            years,
        "mean":            mean_traj,
        "p5":              p5_traj,
        "p95":             p95_traj,
        "var_total":       var_total,
        "var_emissions":   var_emissions,
        "var_climate":     var_climate,
        "var_internal":    var_internal,
        "var_modelled":    var_modelled,
    })
    df.to_csv(OUT / "updated_hawkins_sutton_data.csv", index=False)

    # ---- plot ----
    mask = (years >= PLOT_START) & (years <= PLOT_END)
    yp = years[mask]
    fig, (ax_t, ax_b) = plt.subplots(2, 1, figsize=(9.5, 8.5),
                                     sharex=True,
                                     gridspec_kw={"height_ratios": [3, 2]})

    # Top: GMST trajectory envelope (bias-corrected rel-PI axis)
    ax_t.fill_between(yp, p5_traj[mask], p95_traj[mask],
                      color="#e0e0e0",
                      label="5–95% across all (RFF × configs)")
    ax_t.fill_between(yp,
                      mean_traj[mask] - np.sqrt(var_total[mask]),
                      mean_traj[mask] + np.sqrt(var_total[mask]),
                      color="#bbbbbb",
                      label="$\\pm 1\\sigma$ total variance")
    ax_t.plot(yp, mean_traj[mask], color="black", linewidth=2.2,
              label="Ensemble mean")
    ax_t.axvspan(RECENT_BASELINE[0], RECENT_BASELINE[1],
                 color="#A6361C", alpha=0.10,
                 label=f"Recent baseline ({RECENT_BASELINE[0]}–{RECENT_BASELINE[1]})")
    ax_t.axhline(OBS_RECENT_REL_PI, color="#A6361C", linewidth=0.7,
                 linestyle=":", alpha=0.7,
                 label=f"IGCC observed {RECENT_BASELINE[0]}–{RECENT_BASELINE[1]} "
                       f"(+{OBS_RECENT_REL_PI:.2f} °C)")
    ax_t.set_ylabel("GMST anomaly (°C, rel. preindustrial 1850–1900)\n"
                    "AR6-style bias-corrected", fontsize=11)
    ax_t.legend(loc="upper left", fontsize=9.5, framealpha=0.92)
    ax_t.set_title("Updated Hawkins-Sutton — GMST anomaly + variance "
                   f"decomposition\n(AR6 bias-corrected to IGCC 2024 "
                   f"{RECENT_BASELINE[0]}–{RECENT_BASELINE[1]} consensus = "
                   f"+{OBS_RECENT_REL_PI:.2f} °C rel PI)",
                   fontsize=12.5, fontweight="bold", color="#1F4E79")
    ax_t.grid(alpha=0.3, linewidth=0.5)

    # Bottom: stacked variance FRACTIONS
    f_emi  = var_emissions[mask] / var_modelled[mask]
    f_clim = var_climate[mask]   / var_modelled[mask]
    f_int  = var_internal[mask]  / var_modelled[mask]
    ax_b.stackplot(yp, f_int, f_clim, f_emi,
                   labels=["Internal variability (FaIR stochastic seed)",
                           "Climate configs (FaIR v2.2.4)",
                           "Emissions (RFF-SP)"],
                   colors=[COLORS["internal"], COLORS["climate"],
                           COLORS["emissions"]],
                   alpha=0.85, edgecolor="white", linewidth=0.4)
    ax_b.set_xlim(PLOT_START, PLOT_END)
    ax_b.set_ylim(0, 1)
    ax_b.set_xlabel("Year", fontsize=11)
    ax_b.set_ylabel("Fraction of total variance", fontsize=11)
    # Reverse legend so legend order matches the visual top→bottom stack:
    # emissions (top), climate, internal (bottom).
    h_, l_ = ax_b.get_legend_handles_labels()
    ax_b.legend(h_[::-1], l_[::-1],
                loc="center right", fontsize=10, framealpha=0.92)
    ax_b.grid(True, axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUT / "updated_hawkins_sutton.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / "updated_hawkins_sutton.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT / 'updated_hawkins_sutton.png'}")

    # Print headline numbers for the Substack (bias-corrected rel-PI)
    print()
    print("Key values for the Substack text (°C rel preindustrial, AR6 bias-corrected):")
    for y in [2020, 2030, 2050, 2075, 2100, 2150]:
        if y not in years: continue
        ix = int(np.where(years == y)[0][0])
        print(f"  {y}: mean={mean_traj[ix]:+.2f} °C  "
              f"P5-P95=[{p5_traj[ix]:+.2f}, {p95_traj[ix]:+.2f}]  "
              f"f_emi={var_emissions[ix]/var_modelled[ix]:.2f}  "
              f"f_clim={var_climate[ix]/var_modelled[ix]:.2f}  "
              f"f_int={var_internal[ix]/var_modelled[ix]:.2f}")


if __name__ == "__main__":
    main()
