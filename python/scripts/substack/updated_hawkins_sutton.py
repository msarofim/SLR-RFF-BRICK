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
DET_CUBE = ROOT / "outputs" / "lhs_pilot_gmst_full_N200_to2300.npz"
STOCH_CUBE = ROOT / "outputs" / "lhs_pilot_gmst_full_stoch_test.npz"
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
    """Year-by-year V_internal(t) computed from real FaIR stochastic seeds.

    Returns an array aligned with det_years.  For years past the stoch cube's
    coverage (typically beyond 2100), the mean of the last 11 stoch years
    (2090-2100) is held constant — FaIR's stochastic GMST σ is approximately
    time-stationary at long horizons.
    """
    nz = np.load(stoch_cube_path)
    sy = nz["years"]
    sg = nz["gmst_traj_rff"]               # (n_rff, n_cfg, n_seed, n_year)
    assert sg.ndim == 4, f"stoch cube must be 4D; got {sg.shape}"

    # Anchor each trajectory to its own value at baseline_year (so V_internal
    # is the variance of GMST(t) − GMST(baseline) across seeds, holding the
    # rest fixed — same anchoring as the deterministic cube below).
    if baseline_year in sy:
        ib = int(np.where(sy == baseline_year)[0][0])
        sg_anom = sg.astype(np.float64) - sg[:, :, :, ib][:, :, :, None]
    else:
        sg_anom = sg.astype(np.float64)

    # V_internal(t) = E_{rff,cfg}[ Var_seed[GMST_anom(t)] ]
    v_seed = sg_anom.var(axis=2)           # (n_rff, n_cfg, n_year)
    v_internal_stoch = v_seed.mean(axis=(0, 1))   # (n_year_stoch,)

    # Reindex to det_years
    v_internal_out = np.zeros(len(det_years))
    sy_min, sy_max = int(sy.min()), int(sy.max())
    # Tail fill from mean of last 11 stoch years
    tail_mean = float(v_internal_stoch[sy >= (sy_max - 10)].mean())
    for k, y in enumerate(det_years):
        y = int(y)
        if sy_min <= y <= sy_max:
            v_internal_out[k] = float(v_internal_stoch[int(np.where(sy == y)[0][0])])
        elif y > sy_max:
            v_internal_out[k] = tail_mean
        else:
            v_internal_out[k] = float(v_internal_stoch[0])
    return v_internal_out


def main():
    # ---- Emissions × climate from the deterministic 398-RFF × 841-cfg cube ----
    nz = np.load(DET_CUBE)
    years = nz["years"]
    cube  = nz["gmst_traj_rff"]            # (n_rff, n_cfg, n_year)
    n_rff, n_cfg, n_yr = cube.shape
    print(f"loaded det cube: {n_rff} RFFs × {n_cfg} configs × {n_yr} years")

    # AR6 bias correction: anchor each trajectory at its own RECENT_BASELINE
    # decadal mean, then shift by IGCC observed anchor to express on a rel-PI
    # axis.  Variance decomposition itself is anchor-invariant.
    recent_mask = (years >= RECENT_BASELINE[0]) & (years <= RECENT_BASELINE[1])
    traj_recent = cube[:, :, recent_mask].mean(axis=2)
    cube_anom   = cube - traj_recent[:, :, None] + OBS_RECENT_REL_PI
    i_base      = int(np.where(years == BASELINE_YEAR)[0][0])  # for stoch cube helper

    var_total     = np.zeros(n_yr)
    var_emissions = np.zeros(n_yr)
    var_climate   = np.zeros(n_yr)
    mean_traj     = np.zeros(n_yr)
    p5_traj       = np.zeros(n_yr)
    p95_traj      = np.zeros(n_yr)
    for t in range(n_yr):
        slab = cube_anom[:, :, t].astype(np.float64)   # (n_rff, n_cfg)
        var_total[t] = float(np.var(slab))
        var_emissions[t] = float(np.var(slab.mean(axis=1)))
        var_climate[t]   = float(np.var(slab, axis=1).mean())
        flat = slab.ravel()
        mean_traj[t] = float(flat.mean())
        p5_traj[t]   = float(np.percentile(flat, 5))
        p95_traj[t]  = float(np.percentile(flat, 95))

    # ---- REAL internal variability from stochastic FaIR seeds ----
    print(f"loading stochastic cube for V_internal: {STOCH_CUBE}")
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
