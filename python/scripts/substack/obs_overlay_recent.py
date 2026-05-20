"""
obs_overlay_recent.py
=====================

Single-panel companion to obs_overlay.py — same content as that script's
right panel: FaIR ensemble band vs IGCC 2024 consensus + Berkeley Earth
observed GMST, all anchored at the 2015-2024 ten-year mean.

The shown 5-95% band combines THREE sources of FaIR uncertainty per year:
  (1) emissions (RFF-SP, 398 paths),
  (2) climate response (FaIR v2.2.4, 841 v1.4.1-calibrated configs),
  (3) internal variability (FaIR stochastic seeds, 4D cube).
Sources (1)+(2) come from the deterministic 3D cube; (3) is added in
quadrature as a Gaussian widening of the band edges, using
V_internal(t) = E_{rff,cfg}[Var_seed[GMST_anom(t)]] from the 4D stoch cube
with the same 2015-2024 anchor.

Observed series shown:
  - IGCC 2024 consensus LINE: Trewin's raw annual 4-dataset average
    (HadCRUT5 + Berkeley Earth + GISTEMP + NOAAGlobalTemp).  This shows
    ENSO peaks honestly (e.g. the +1.52 °C 2024 spike).  Source file:
    igcc2024_gmst_4dataset_mean.csv.
  - IGCC 2024 obs-uncertainty BAND: 5-95% cross-dataset spread from
    Walsh et al. attribution analysis (igcc2024_gmst_with_uncertainty.csv).
    Walsh's total_p50 is a regression-fitted smooth signal, NOT the raw
    obs — so we apply the band WIDTH (p95 - p5 about p50) centered on
    Trewin's raw annual value, giving an honest annual obs uncertainty
    around the actual observed mean.
  - Berkeley Earth alone, as a single-product reference inside the IGCC
    envelope.

Secondary y-axis: warming rel preindustrial = left-axis + IGCC 2024
2015-2024 anchor (+{OBS_RECENT_REL_PI}).

Inputs:
  outputs/lhs_pilot_gmst_full_N200_to2300.npz       (3D deterministic cube)
  outputs/lhs_pilot_gmst_full_stoch_test.npz        (4D stochastic-seed cube)
  data/observations/berkeley_earth_annual.csv
  data/observations/igcc2024_gmst_4dataset_mean.csv (raw consensus line)
  data/observations/igcc2024_gmst_with_uncertainty.csv (cross-dataset band)

Output:
  outputs/substack/obs_overlay_recent.{png,pdf}
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Reuse the shared helpers from the two-panel script so we don't drift.
from obs_overlay import (
    CUBE, STOCH_CUBE, OBS_BE, OBS_IGCC, OUT,
    RECENT_PERIOD, PLOT_START, PLOT_END,
    per_traj_window_mean, _ensemble_bands,
    v_internal_for_anchor, broaden_band_for_internal_var,
)

# Additional IGCC product: Trewin's raw 4-dataset annual average (preserves
# ENSO swings, including the 2024 peak).  Local path; loaded as the
# consensus line.
ROOT = Path(__file__).resolve().parents[3]
OBS_IGCC_RAW = ROOT / "data" / "observations" / "igcc2024_gmst_4dataset_mean.csv"

# IGCC consensus 2015-2024 mean rel PI — used to label the secondary y-axis
# in the "warming from preindustrial" frame.  Must match OBS_RECENT_REL_PI
# in updated_hawkins_sutton.py / exceedance_*.py.
OBS_RECENT_REL_PI = 1.254


def main():
    nz = np.load(CUBE)
    years = nz["years"]
    cube  = nz["gmst_traj_rff"].astype(np.float64)
    n_rff, n_cfg, n_yr = cube.shape
    print(f"loaded cube: {n_rff} RFFs × {n_cfg} cfgs × {n_yr} years")

    # Berkeley Earth (single product)
    obs = pd.read_csv(OBS_BE)
    be_recent = obs[(obs.year >= RECENT_PERIOD[0])
                    & (obs.year <= RECENT_PERIOD[1])]["value"].mean()
    print(f"Berkeley Earth 2015-2024 mean = {be_recent:+.3f} °C "
          f"(in BE's native 1951-1980 baseline)")

    # IGCC consensus LINE — Trewin's raw 4-dataset annual average (ENSO-honest)
    trewin = pd.read_csv(OBS_IGCC_RAW)
    igcc_line = pd.DataFrame({
        "year":      trewin["time"].apply(np.floor).astype(int),
        "p50_relPI": trewin["GMST"],
    }).drop_duplicates(subset="year").reset_index(drop=True)
    igcc_line_recent = igcc_line[(igcc_line.year >= RECENT_PERIOD[0])
                                & (igcc_line.year <= RECENT_PERIOD[1])]["p50_relPI"].mean()

    # IGCC obs-uncertainty BAND — cross-dataset 5-95% spread from Walsh.
    # We use Walsh's band WIDTH (delta around its own p50) but center the
    # band on Trewin's raw value, so the visible spread is the cross-dataset
    # uncertainty while the line still shows actual ENSO swings.
    walsh = pd.read_csv(OBS_IGCC)
    igcc_band = pd.DataFrame({
        "year":     walsh["time"].apply(np.floor).astype(int),
        "fit_p05":  walsh["total_p05"],
        "fit_p50":  walsh["total_p50"],
        "fit_p95":  walsh["total_p95"],
    }).drop_duplicates(subset="year").reset_index(drop=True)
    # Merge so we can compute Trewin ± (band offset).
    igcc = igcc_line.merge(igcc_band, on="year", how="inner")
    igcc["delta_lo"] = igcc["fit_p50"] - igcc["fit_p05"]
    igcc["delta_hi"] = igcc["fit_p95"] - igcc["fit_p50"]
    igcc["p5_relPI"]  = igcc["p50_relPI"] - igcc["delta_lo"]
    igcc["p95_relPI"] = igcc["p50_relPI"] + igcc["delta_hi"]

    print(f"IGCC 2024 consensus (Trewin raw) 2015-2024 mean rel PI = "
          f"{igcc_line_recent:+.3f} °C")
    print(f"  2024 raw value (should show ENSO peak): "
          f"{igcc[igcc.year == 2024]['p50_relPI'].iloc[0]:+.3f} °C")

    plot_mask = (years >= PLOT_START) & (years <= PLOT_END)
    yp = years[plot_mask]

    # Anchor each trajectory to its own 2015-2024 mean.
    recent_mean_per_traj = per_traj_window_mean(cube, years, *RECENT_PERIOD)
    cube_recent = cube - recent_mean_per_traj[:, :, None]
    p5_det, p50, p95_det, m = _ensemble_bands(cube_recent, years, plot_mask)

    # Rebaseline obs to its own 2015-2024 mean (anchor-invariant by construction).
    obs_recent = obs.copy()
    obs_recent["value_rel"] = obs["value"] - be_recent
    igcc_recent = igcc.copy()
    igcc_recent["value_rel"] = igcc["p50_relPI"]  - igcc_line_recent
    igcc_recent["lo_rel"]    = igcc["p5_relPI"]   - igcc_line_recent
    igcc_recent["hi_rel"]    = igcc["p95_relPI"]  - igcc_line_recent

    # Broaden by FaIR stochastic-seed internal variability (same anchor).
    print(f"loading stochastic cube for V_internal: {STOCH_CUBE}")
    v_int = v_internal_for_anchor(STOCH_CUBE, yp, RECENT_PERIOD)
    p5, _, p95 = broaden_band_for_internal_var(p5_det, p50, p95_det, v_int)
    for y in (1950, 2000, 2024, 2050):
        if y not in yp: continue
        i = int(np.where(yp == y)[0][0])
        print(f"  {y}: det 5-95 width = {(p95_det[i]-p5_det[i]):.3f} °C  ->  "
              f"with seed-var = {(p95[i]-p5[i]):.3f} °C")

    # Plot
    fig, ax = plt.subplots(figsize=(9.0, 5.6))
    ax.fill_between(yp, p5, p95, color="#7570B3", alpha=0.16,
                    label="FaIR 5–95% (RFF × configs × seed)")
    ax.plot(yp, p50, color="#7570B3", linewidth=2.2,
            label="FaIR ensemble median")
    ax.plot(yp, m, color="#7570B3", linewidth=1.0, linestyle="--",
            label="FaIR ensemble mean")
    ax.fill_between(igcc_recent["year"], igcc_recent["lo_rel"], igcc_recent["hi_rel"],
                    color="#A6361C", alpha=0.20,
                    label="IGCC 2024 5–95% (4-dataset obs uncertainty)")
    ax.plot(igcc_recent["year"], igcc_recent["value_rel"],
            color="#A6361C", linewidth=2.0,
            label="IGCC 2024 consensus (4-dataset median)")
    ax.plot(obs_recent["year"], obs_recent["value_rel"],
            color="black", linewidth=1.0, linestyle="--",
            label="Berkeley Earth (single dataset)")
    ax.axhline(0, color="grey", linewidth=0.6)
    ax.axvspan(RECENT_PERIOD[0], RECENT_PERIOD[1],
               color="#A6361C", alpha=0.06)
    ax.set_xlim(PLOT_START, PLOT_END)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel(f"GMST anomaly (°C, rel. {RECENT_PERIOD[0]}–{RECENT_PERIOD[1]} mean)",
                  fontsize=11)
    ax.set_title("FaIR ensemble vs. observed warming, "
                 f"relative to {RECENT_PERIOD[0]}–{RECENT_PERIOD[1]} mean",
                 fontsize=13, fontweight="bold", color="#1F4E79")
    ax.legend(loc="upper left", fontsize=9.5, framealpha=0.92)
    ax.grid(alpha=0.3, linewidth=0.5)

    # Secondary y-axis: warming rel preindustrial = rel-recent + IGCC anchor
    ax_r = ax.twinx()
    yl, yh = ax.get_ylim()
    ax_r.set_ylim(yl + OBS_RECENT_REL_PI, yh + OBS_RECENT_REL_PI)
    ax_r.set_ylabel(f"Warming relative to preindustrial (°C, rel. 1850–1900)\n"
                    f"  + {OBS_RECENT_REL_PI:.2f} °C at "
                    f"{RECENT_PERIOD[0]}–{RECENT_PERIOD[1]} "
                    f"(IGCC 2024 consensus)",
                    fontsize=10, color="#555")
    ax_r.tick_params(labelcolor="#555")

    fig.tight_layout()
    fig.savefig(OUT / "obs_overlay_recent.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / "obs_overlay_recent.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT / 'obs_overlay_recent.png'}")


if __name__ == "__main__":
    main()
