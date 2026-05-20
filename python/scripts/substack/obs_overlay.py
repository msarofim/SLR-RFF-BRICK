"""
obs_overlay.py
==============

Substack figure: FaIR ensemble bands vs Berkeley Earth observed GMST.

The shown 5-95% band combines THREE sources of FaIR uncertainty per year:
  (1) emissions (RFF-SP, 398 paths),
  (2) climate response (FaIR v2.2.4, 841 v1.4.1-calibrated configs),
  (3) internal variability (FaIR stochastic seeds, from a separate 4D cube).
Sources (1)+(2) come from the deterministic 3D cube (N200_to2300); source
(3) is added in quadrature as a Gaussian widening of the band edges, using
V_internal(t) = E_{rff,cfg}[Var_seed[GMST_anom(t)]] from the 4D stoch cube.
This makes the band a proper "where one realization of the world could
land" envelope rather than just the smooth cross-ensemble spread.

Two side-by-side panels:
  • LEFT  — both relative to PREINDUSTRIAL (1850-1900 mean per trajectory).
            FaIR's 5-95% should bracket observed Berkeley Earth through
            ~2024; centred near +1.25 °C (IGCC 2024 consensus) at the
            2015-2024 recent decade.
  • RIGHT — both relative to the 2015-2024 ten-year mean (per trajectory).
            The recent-mean anchor compresses cross-ensemble spread near
            2015-2024 and lets internal variability dominate the band
            width on either side of the anchor.

Inputs:
  outputs/lhs_pilot_gmst_full_N200_to2300.npz   (3D deterministic cube)
  outputs/lhs_pilot_gmst_full_stoch_test.npz    (4D stochastic-seed cube)
  data/observations/berkeley_earth_annual.csv

Output:
  outputs/substack/obs_overlay.{png,pdf}
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
CUBE = ROOT / "outputs" / "lhs_pilot_gmst_full_N200_to2300.npz"
STOCH_CUBE = ROOT / "outputs" / "lhs_pilot_gmst_full_stoch_test.npz"
OBS_BE       = ROOT / "data" / "observations" / "berkeley_earth_annual.csv"
OBS_IGCC     = ROOT / "data" / "observations" / "igcc2024_gmst_with_uncertainty.csv"
OBS_IGCC_RAW = ROOT / "data" / "observations" / "igcc2024_gmst_4dataset_mean.csv"
OUT  = ROOT / "outputs" / "substack"
OUT.mkdir(parents=True, exist_ok=True)

PI_PERIOD     = (1850, 1900)
RECENT_PERIOD = (2015, 2024)
PLOT_START    = 1900
PLOT_END      = 2050   # extend slightly past observed (2023) to show near-term
# 5-95 → ±z·σ for a Gaussian.  Used to broaden the band edges by FaIR's
# stochastic-seed internal variability, computed from the 4D stoch cube.
Z_5_95        = 1.6448536269514722


def per_traj_window_mean(cube, years, y0, y1):
    """Returns (n_rff, n_cfg) array: mean over [y0, y1] for each trajectory."""
    mask = (years >= y0) & (years <= y1)
    return cube[:, :, mask].mean(axis=2)


def _ensemble_bands(cube_anom, years, plot_mask):
    """Per-year P5/P50/P95 + mean across the (rff, cfg) ensemble."""
    n_rff, n_cfg, n_yr = cube_anom.shape
    sub = cube_anom[:, :, plot_mask].reshape(n_rff * n_cfg, -1)
    p5  = np.percentile(sub, 5,  axis=0)
    p50 = np.percentile(sub, 50, axis=0)
    p95 = np.percentile(sub, 95, axis=0)
    m   = sub.mean(axis=0)
    return p5, p50, p95, m


def v_internal_for_anchor(stoch_cube_path, det_years, anchor_period):
    """V_internal(t) = E_{rff,cfg}[Var_seed[GMST_anchored(t)]] for the given
    multi-year anchor period.  Returns an array aligned with det_years; years
    past the stoch cube's coverage are held flat at the last-decade mean
    (FaIR stochastic σ is roughly time-stationary at long horizons)."""
    nz = np.load(stoch_cube_path)
    sy = nz["years"]
    sg = nz["gmst_traj_rff"].astype(np.float64)  # (rff, cfg, seed, year)
    assert sg.ndim == 4, f"stoch cube must be 4D; got {sg.shape}"
    a_lo, a_hi = anchor_period
    amask = (sy >= a_lo) & (sy <= a_hi)
    if amask.sum() == 0:
        raise RuntimeError(
            f"Stoch cube years {sy.min()}-{sy.max()} don't cover anchor "
            f"period {anchor_period}.")
    anchor_mean = sg[:, :, :, amask].mean(axis=3)              # (rff, cfg, seed)
    sg_anom     = sg - anchor_mean[:, :, :, None]
    # E_{rff,cfg}[ Var_seed[GMST_anom(t)] ]
    v_stoch     = sg_anom.var(axis=2).mean(axis=(0, 1))        # (n_year_stoch,)
    # Reindex onto det_years.  Hold flat past end of stoch coverage.
    v_out = np.zeros(len(det_years))
    sy_min, sy_max = int(sy.min()), int(sy.max())
    tail_mean = float(v_stoch[sy >= (sy_max - 10)].mean())
    for k, y in enumerate(det_years):
        y = int(y)
        if sy_min <= y <= sy_max:
            v_out[k] = float(v_stoch[int(np.where(sy == y)[0][0])])
        elif y > sy_max:
            v_out[k] = tail_mean
        else:
            v_out[k] = float(v_stoch[0])
    return v_out


def broaden_band_for_internal_var(p5, p50, p95, v_internal):
    """Combine the deterministic ensemble (rff × cfg) percentile band with
    the FaIR stochastic-seed internal variability (Gaussian, independent).

    Half-width of the deterministic 5-95% band per year:
        hw_det = (p95 - p5) / 2
    Half-width of an N(0, V_internal) 5-95% band:
        hw_int = z · √V_internal,    z = Φ⁻¹(0.95)
    Independent Gaussians add in quadrature:
        hw_tot = √(hw_det² + hw_int²)
    Median is unchanged (zero-mean noise)."""
    hw_det = (p95 - p5) / 2.0
    hw_int = Z_5_95 * np.sqrt(v_internal)
    hw_tot = np.sqrt(hw_det ** 2 + hw_int ** 2)
    return p50 - hw_tot, p50, p50 + hw_tot


def main():
    nz = np.load(CUBE)
    years = nz["years"]
    cube  = nz["gmst_traj_rff"].astype(np.float64)
    n_rff, n_cfg, n_yr = cube.shape
    print(f"loaded cube: {n_rff} RFFs × {n_cfg} cfgs × {n_yr} years")

    obs = pd.read_csv(OBS_BE)
    print(f"loaded BE obs: {len(obs)} years ({obs.year.min()}-{obs.year.max()})")
    be_pi      = obs[(obs.year >= PI_PERIOD[0]) & (obs.year <= PI_PERIOD[1])]["value"].mean()
    be_recent  = obs[(obs.year >= RECENT_PERIOD[0]) & (obs.year <= RECENT_PERIOD[1])]["value"].mean()
    print(f"Berkeley Earth: 1850-1900 mean = {be_pi:+.3f} °C; "
          f"2015-2024 mean = {be_recent:+.3f} °C  → "
          f"recent vs preindustrial = {be_recent - be_pi:+.3f} °C")

    # IGCC 2024 consensus LINE — Trewin's raw 4-dataset annual average
    # (HadCRUT5 + Berkeley Earth + GISTEMP + NOAAGlobalTemp; Forster et al.
    # 2025 ESSD).  Anomalies natively rel 1850-1900.  This preserves
    # ENSO-driven year-to-year variability honestly, including the 2024
    # peak (+1.52 °C).
    trewin = pd.read_csv(OBS_IGCC_RAW)
    igcc_line = pd.DataFrame({
        "year":      trewin["time"].apply(np.floor).astype(int),
        "p50_relPI": trewin["GMST"],
    }).drop_duplicates(subset="year").reset_index(drop=True)

    # IGCC obs-uncertainty BAND — from Walsh attribution analysis.  Walsh's
    # total_p50 is a regression-fitted SMOOTH signal (ENSO absorbed into the
    # residual term); use only the band WIDTH (p95-p50, p50-p5) about Walsh's
    # own p50, applied as ±delta around Trewin's raw value.  Gives an honest
    # annual cross-dataset uncertainty centered on the actual observed mean.
    walsh = pd.read_csv(OBS_IGCC)
    igcc_walsh = pd.DataFrame({
        "year":    walsh["time"].apply(np.floor).astype(int),
        "fit_p05": walsh["total_p05"],
        "fit_p50": walsh["total_p50"],
        "fit_p95": walsh["total_p95"],
    }).drop_duplicates(subset="year").reset_index(drop=True)
    igcc = igcc_line.merge(igcc_walsh, on="year", how="inner")
    igcc["delta_lo"] = igcc["fit_p50"] - igcc["fit_p05"]
    igcc["delta_hi"] = igcc["fit_p95"] - igcc["fit_p50"]
    igcc["p5_relPI"]  = igcc["p50_relPI"] - igcc["delta_lo"]
    igcc["p95_relPI"] = igcc["p50_relPI"] + igcc["delta_hi"]

    igcc_recent_p50 = igcc[(igcc.year >= RECENT_PERIOD[0])
                          & (igcc.year <= RECENT_PERIOD[1])]["p50_relPI"].mean()
    print(f"IGCC 2024 consensus (Trewin raw): 2015-2024 mean rel PI = "
          f"{igcc_recent_p50:+.3f} °C  "
          f"(2024 raw peak = "
          f"{igcc[igcc.year == 2024]['p50_relPI'].iloc[0]:+.3f} °C)")

    plot_mask = (years >= PLOT_START) & (years <= PLOT_END)
    yp = years[plot_mask]

    # ---- LEFT: anchor to preindustrial (per-trajectory 1850-1900 mean) ----
    pi_mean_per_traj = per_traj_window_mean(cube, years, *PI_PERIOD)
    cube_pi = cube - pi_mean_per_traj[:, :, None]
    p5_pi_det, p50_pi, p95_pi_det, m_pi = _ensemble_bands(cube_pi, years, plot_mask)
    obs_pi = obs.copy()
    obs_pi["value_rel"] = obs["value"] - be_pi
    # IGCC is natively rel 1850-1900, no rebaseline needed
    igcc_pi = igcc.copy()
    igcc_pi["value_rel"] = igcc["p50_relPI"]
    igcc_pi["lo_rel"]    = igcc["p5_relPI"]
    igcc_pi["hi_rel"]    = igcc["p95_relPI"]

    # ---- RIGHT: anchor to recent 10-year mean (per-trajectory 2015-2024) ----
    recent_mean_per_traj = per_traj_window_mean(cube, years, *RECENT_PERIOD)
    cube_recent = cube - recent_mean_per_traj[:, :, None]
    p5_r_det, p50_r, p95_r_det, m_r = _ensemble_bands(cube_recent, years, plot_mask)
    obs_recent = obs.copy()
    obs_recent["value_rel"] = obs["value"] - be_recent
    # IGCC: shift everything by Trewin's 2015-2024 mean.  Trewin line is the
    # raw 4-dataset annual average so ENSO swings appear; Walsh-derived band
    # widths follow the line (same anchor) preserving cross-dataset spread.
    igcc_recent = igcc.copy()
    igcc_recent["value_rel"] = igcc["p50_relPI"] - igcc_recent_p50
    igcc_recent["lo_rel"]    = igcc["p5_relPI"]  - igcc_recent_p50
    igcc_recent["hi_rel"]    = igcc["p95_relPI"] - igcc_recent_p50

    # ---- broaden each band by FaIR stochastic-seed internal variability ----
    # V_internal is anchor-dependent because the per-trajectory anchor mean
    # introduces a small correlation correction; we compute it once per anchor
    # convention, using the SAME anchor as the deterministic cube above.
    print(f"loading stochastic cube for V_internal broadening: {STOCH_CUBE}")
    v_int_pi    = v_internal_for_anchor(STOCH_CUBE, years[plot_mask], PI_PERIOD)
    v_int_recent = v_internal_for_anchor(STOCH_CUBE, years[plot_mask], RECENT_PERIOD)
    p5_pi, _, p95_pi = broaden_band_for_internal_var(p5_pi_det, p50_pi, p95_pi_det, v_int_pi)
    p5_r,  _, p95_r  = broaden_band_for_internal_var(p5_r_det,  p50_r,  p95_r_det,  v_int_recent)
    # Diagnostics: how much did the band widen at a few representative years?
    for label, p5d, p95d, p5n, p95n, yp_local in [
        ("PI",     p5_pi_det, p95_pi_det, p5_pi, p95_pi, years[plot_mask]),
        ("recent", p5_r_det,  p95_r_det,  p5_r,  p95_r,  years[plot_mask]),
    ]:
        for y in (1950, 2000, 2024, 2050):
            if y not in yp_local: continue
            i = int(np.where(yp_local == y)[0][0])
            w_det = p95d[i] - p5d[i]
            w_new = p95n[i] - p5n[i]
            print(f"  {label} {y}: det 5-95 width = {w_det:.3f} °C  ->  "
                  f"with seed-var = {w_new:.3f} °C  (Δ {w_new-w_det:+.3f})")

    # ---- plot ----
    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(15, 5.8),
                                     gridspec_kw=dict(wspace=0.18))

    for ax, p5, p50, p95, m, obs_df, igcc_df, title, ylabel in [
        (ax_l, p5_pi, p50_pi, p95_pi, m_pi,    obs_pi,    igcc_pi,
            f"Relative to preindustrial ({PI_PERIOD[0]}–{PI_PERIOD[1]} mean)",
            "GMST anomaly (°C, rel. preindustrial)"),
        (ax_r, p5_r,  p50_r,  p95_r,  m_r,     obs_recent, igcc_recent,
            f"Relative to recent ({RECENT_PERIOD[0]}–{RECENT_PERIOD[1]} mean)",
            "GMST anomaly (°C, rel. 2015–2024)"),
    ]:
        # FaIR ensemble band (RFF × configs × seed-broadened)
        ax.fill_between(yp, p5, p95, color="#7570B3", alpha=0.16,
                        label="FaIR 5–95% (RFF × configs × seed)")
        ax.plot(yp, p50, color="#7570B3", linewidth=2.2,
                label="FaIR ensemble median")
        ax.plot(yp, m, color="#7570B3", linewidth=1.0, linestyle="--",
                label="FaIR ensemble mean")
        # IGCC 2024 multi-dataset observational uncertainty band + consensus median
        ax.fill_between(igcc_df["year"], igcc_df["lo_rel"], igcc_df["hi_rel"],
                        color="#A6361C", alpha=0.20,
                        label="IGCC 2024 5–95% (4-dataset obs uncertainty)")
        ax.plot(igcc_df["year"], igcc_df["value_rel"],
                color="#A6361C", linewidth=2.0,
                label="IGCC 2024 consensus (4-dataset median)")
        # Berkeley Earth as a single-product reference inside the IGCC envelope
        ax.plot(obs_df["year"], obs_df["value_rel"],
                color="black", linewidth=1.0, linestyle="--",
                label="Berkeley Earth (single dataset)")
        ax.axhline(0, color="grey", linewidth=0.6)
        ax.set_xlim(PLOT_START, PLOT_END)
        ax.set_xlabel("Year", fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_title(title, fontsize=12, fontweight="bold", color="#1F4E79")
        ax.legend(loc="upper left", fontsize=9, framealpha=0.92)
        ax.grid(alpha=0.3, linewidth=0.5)

    fig.suptitle("FaIR ensemble vs. observed warming — two reference periods",
                 fontsize=14, fontweight="bold", color="#1F4E79", y=1.01)
    fig.tight_layout()
    fig.savefig(OUT / "obs_overlay.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / "obs_overlay.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT / 'obs_overlay.png'}")


if __name__ == "__main__":
    main()
