"""
fair_brick_vs_obs_gmst_gmsl.py
==============================

Two-panel substack figure comparing the v1.4.5 FaIR/BRICK pipeline to
observations:

  Top   — Global mean surface temperature (FaIR v1.4.5 LHS-10k baseline
          vs. IGCC 2024 4-dataset mean + Berkeley Earth annual).
  Bottom — Global mean sea level (BRICK v1.4.5 LHS-10k baseline, AR6
          bias-corrected, vs. Dangendorf 2024 + Church & White 2011
          (CSIRO Recons) + IGCC 2024 GMSL ensemble).

Conventions:
  - GMST baseline: 1850-1900 mean (pre-industrial reference, AR6).
  - GMSL baseline: 1995-2014 mean (AR6 recent-period reference).
  - Each model draw is rebaselined at its own window mean, then the
    ensemble is collapsed to median + 5-95 % band — preserves draw-to-draw
    variance correctly across the rebaselining step.
  - Each obs series is rebaselined to the same window; for years before
    the obs coverage starts, the series simply doesn't appear on the plot
    (no extrapolation).

Output: outputs/substack/fair_brick_vs_obs_gmst_gmsl.{png,pdf}
"""
from __future__ import annotations
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "outputs" / "substack"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---- Model inputs -----------------------------------------------------------
# FaIR LHS-10k baseline cube — 10,000 (rff, cfg, seed) trajectories of GMST
# (and OHC) on the v1.4.5 calibration. Used here for the GMST band.
CUBE_PATH = (Path.home() / "Documents/2026/CodeProjects/FaIRtoFrEDI/"
             "fair_outputs/cubes_v145/cube_v145_lhs10k_baseline.npz")

# BRICK v1.4.5 slim baseline weighted CSV (LHS-10k baseline arm, Wong-weighted).
BRICK_CSV = ROOT / "outputs" / "brick_v145_slim" / "brick_lhs10k_baseline_to2300_weighted.csv"

# ---- Obs inputs -------------------------------------------------------------
IGCC_GMST_CSV   = ROOT / "data" / "observations" / "igcc2024_gmst_4dataset_mean.csv"
BE_CSV          = ROOT / "data" / "observations" / "berkeley_earth_annual.csv"
DANGENDORF_CSV  = ROOT / "data" / "observations" / "dangendorf_2024_gmsl.csv"
CHURCH_CSV      = ROOT / "data" / "calibration" / "CSIRO_Recons_gmsl_yr_2015.csv"
IGCC_GMSL_CSV   = (ROOT / "data" / "observations" / "raw" / "igcc2024"
                   / "ClimateIndicator-data-2cd2409" / "data" / "sea_level_rise"
                   / "IGCC_GMSL_ensemble.csv")

# ---- Baseline windows -------------------------------------------------------
GMST_BASE = (1850, 1900)   # AR6 pre-industrial
GMSL_BASE = (1995, 2014)   # AR6 recent-period

# ---- Plot range -------------------------------------------------------------
PLOT_START = 1900
PLOT_END   = 2100
BAND_LOW_Q, BAND_HIGH_Q = 0.05, 0.95

# ---- Colors (consistent with the other substack figures) --------------------
COLOR_MODEL    = "#1F4E79"
COLOR_IGCC     = "#000000"
COLOR_BE       = "#9C2727"
COLOR_DANGEN   = "#4B0082"
COLOR_CHURCH   = "#2E7D32"
COLOR_IGCC_SLR = "#000000"


# =============================================================================
# Helpers
# =============================================================================
def rebaseline_per_row(arr: np.ndarray, years: np.ndarray,
                        beg: int, end: int) -> np.ndarray:
    """Rebaseline each row of `arr` (n_draws, n_year) so its [beg, end] mean = 0."""
    mask = (years >= beg) & (years <= end)
    if not mask.any():
        raise ValueError(f"baseline window {beg}-{end} not in year grid")
    return arr - arr[:, mask].mean(axis=1, keepdims=True)


def quantile_band(arr: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return (np.median(arr, axis=0),
            np.percentile(arr, BAND_LOW_Q * 100, axis=0),
            np.percentile(arr, BAND_HIGH_Q * 100, axis=0))


def rebaseline_series(years: np.ndarray, values: np.ndarray,
                       beg: int, end: int) -> np.ndarray:
    mask = (years >= beg) & (years <= end)
    if not mask.any():
        return values  # series doesn't overlap; leave unanchored (won't plot)
    return values - values[mask].mean()


# =============================================================================
# Load
# =============================================================================
def load_fair_gmst() -> tuple[np.ndarray, np.ndarray]:
    """Return (years, gmst_arr) with gmst_arr shape (n_draws, n_year)."""
    c = np.load(CUBE_PATH, allow_pickle=True)
    return np.asarray(c["years"], dtype=int), np.asarray(c["gmst_traj"], dtype=float)


def load_brick_gmsl() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (years, slr_arr (cm), w_norm). slr is anchored to year 2000."""
    df = pd.read_csv(BRICK_CSV)
    years = np.array(sorted(int(c) for c in df.columns if c.isdigit()))
    slr = df[[str(y) for y in years]].to_numpy(dtype=float)  # cm rel 2000
    w = df["w_norm"].to_numpy()
    return years, slr, w


def load_igcc_gmst() -> tuple[np.ndarray, np.ndarray]:
    d = pd.read_csv(IGCC_GMST_CSV)
    return np.floor(d["time"].to_numpy()).astype(int), d["GMST"].to_numpy()


def load_berkeley() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    d = pd.read_csv(BE_CSV)
    return d["year"].to_numpy(int), d["value"].to_numpy(), d["sigma"].to_numpy()


def load_dangendorf() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (years, GMSL_cm, sigma_cm)."""
    d = pd.read_csv(DANGENDORF_CSV)
    return d["year"].to_numpy(int), d["value"].to_numpy() / 10.0, d["sigma"].to_numpy() / 10.0


def load_church() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Church & White (CSIRO Recons), tide-gauge GMSL.  Returns (years, cm, sigma_cm)."""
    # Skip the 9 `#`-prefixed header lines; the 10th line is the column header.
    raw = pd.read_csv(CHURCH_CSV, skiprows=9)
    time_col  = [c for c in raw.columns if c.strip().lower().startswith("time")][0]
    gmsl_col  = [c for c in raw.columns if "GMSL (mm)" in c][0]
    sigma_col = [c for c in raw.columns if "sigma" in c.lower()][0]
    years = np.floor(raw[time_col].to_numpy()).astype(int)
    return years, raw[gmsl_col].to_numpy() / 10.0, raw[sigma_col].to_numpy() / 10.0


def load_igcc_gmsl() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """IGCC 2024 GMSL ensemble — returns (years, mean_cm, std_cm)."""
    d = pd.read_csv(IGCC_GMSL_CSV)
    return (np.floor(d["time"].to_numpy()).astype(int),
            d["mean"].to_numpy() / 10.0,
            d["std"].to_numpy() / 10.0)


# =============================================================================
# Main
# =============================================================================
def main() -> None:
    fig, (ax_t, ax_s) = plt.subplots(
        nrows=2, ncols=1, figsize=(9.5, 8.5), sharex=True)

    # ----- GMST -----
    yrs_m, gmst = load_fair_gmst()
    gmst_n = rebaseline_per_row(gmst, yrs_m, *GMST_BASE)
    med_t, lo_t, hi_t = quantile_band(gmst_n)
    m_t = (yrs_m >= PLOT_START) & (yrs_m <= PLOT_END)
    ax_t.fill_between(yrs_m[m_t], lo_t[m_t], hi_t[m_t],
                       color=COLOR_MODEL, alpha=0.22, linewidth=0,
                       label="FaIR v1.4.5 LHS-10k, 5–95 %")
    ax_t.plot(yrs_m[m_t], med_t[m_t], color=COLOR_MODEL, lw=2.0,
              label="FaIR median")

    yrs_i, gmst_i = load_igcc_gmst()
    gmst_i_n = rebaseline_series(yrs_i, gmst_i, *GMST_BASE)
    m_i = (yrs_i >= PLOT_START) & (yrs_i <= PLOT_END)
    ax_t.plot(yrs_i[m_i], gmst_i_n[m_i], color=COLOR_IGCC, lw=1.6,
              label="IGCC 2024 (4-dataset mean)")

    yrs_b, gmst_b, sig_b = load_berkeley()
    gmst_b_n = rebaseline_series(yrs_b, gmst_b, *GMST_BASE)
    m_b = (yrs_b >= PLOT_START) & (yrs_b <= PLOT_END)
    ax_t.plot(yrs_b[m_b], gmst_b_n[m_b], color=COLOR_BE, lw=1.0, alpha=0.85,
              label="Berkeley Earth")

    ax_t.axhline(0, color="grey", lw=0.5)
    ax_t.set_ylabel(f"GMST anomaly (°C, rel. {GMST_BASE[0]}–{GMST_BASE[1]})",
                     fontsize=10)
    ax_t.set_title("Global mean surface temperature — FaIR v1.4.5 vs. observations",
                    fontsize=11, fontweight="bold", color="#1A1A1A")
    ax_t.grid(alpha=0.3, lw=0.4)
    ax_t.legend(loc="upper left", fontsize=8.5, framealpha=0.92)

    # ----- GMSL -----
    yrs_s, slr_m, w_norm = load_brick_gmsl()
    slr_m_n = rebaseline_per_row(slr_m, yrs_s, *GMSL_BASE)
    # Wong-weighted quantiles per year (model-side band is importance-weighted).
    slr_med = np.zeros(len(yrs_s))
    slr_lo  = np.zeros(len(yrs_s))
    slr_hi  = np.zeros(len(yrs_s))
    order = np.argsort(slr_m_n, axis=0)
    for j in range(len(yrs_s)):
        v = slr_m_n[order[:, j], j]
        cw = np.cumsum(w_norm[order[:, j]])
        cw /= cw[-1]
        slr_lo[j]  = v[np.searchsorted(cw, BAND_LOW_Q)]
        slr_med[j] = v[np.searchsorted(cw, 0.50)]
        slr_hi[j]  = v[np.searchsorted(cw, BAND_HIGH_Q)]
    m_s = (yrs_s >= PLOT_START) & (yrs_s <= PLOT_END)
    ax_s.fill_between(yrs_s[m_s], slr_lo[m_s], slr_hi[m_s],
                       color=COLOR_MODEL, alpha=0.22, linewidth=0,
                       label="BRICK v1.4.5 LHS-10k Wong-weighted, 5–95 %")
    ax_s.plot(yrs_s[m_s], slr_med[m_s], color=COLOR_MODEL, lw=2.0,
              label="BRICK median")

    for loader, color, label in [
        (load_dangendorf, COLOR_DANGEN,   "Dangendorf 2024"),
        (load_church,     COLOR_CHURCH,   "Church & White 2011 (CSIRO Recons)"),
        (load_igcc_gmsl,  COLOR_IGCC_SLR, "IGCC 2024 ensemble"),
    ]:
        y, v, s = loader()
        v_n = rebaseline_series(y, v, *GMSL_BASE)
        m = (y >= PLOT_START) & (y <= PLOT_END)
        ax_s.plot(y[m], v_n[m], color=color, lw=1.4, label=label)
        ax_s.fill_between(y[m], v_n[m] - s[m], v_n[m] + s[m],
                           color=color, alpha=0.10, linewidth=0)

    ax_s.axhline(0, color="grey", lw=0.5)
    ax_s.set_xlim(PLOT_START, PLOT_END)
    ax_s.set_xlabel("Year", fontsize=10)
    ax_s.set_ylabel(f"GMSL (cm, rel. {GMSL_BASE[0]}–{GMSL_BASE[1]})", fontsize=10)
    ax_s.set_title("Global mean sea level — BRICK v1.4.5 vs. observations",
                    fontsize=11, fontweight="bold", color="#1A1A1A")
    ax_s.grid(alpha=0.3, lw=0.4)
    ax_s.legend(loc="upper left", fontsize=8.5, framealpha=0.92)

    fig.tight_layout(rect=[0, 0.04, 1, 0.96])
    fig.suptitle(
        "Latest FaIR / BRICK pipeline vs. observations",
        fontsize=14, fontweight="bold", color="#1A1A1A", y=0.99)
    fig.text(
        0.5, 0.01,
        f"FaIR v1.4.5 (Smith et al. 2024) + MimiBRICK post-PR#93 joint posterior, "
        f"Wong-weighted LHS-10k baseline. "
        f"GMST anomaly rel. {GMST_BASE[0]}–{GMST_BASE[1]}; "
        f"GMSL rel. {GMSL_BASE[0]}–{GMSL_BASE[1]}. "
        f"Each draw rebaselined at its own window mean; obs rebaselined to the same window.",
        ha="center", va="bottom", fontsize=8.5, style="italic", color="#444444",
        wrap=True)

    out_png = OUT_DIR / "fair_brick_vs_obs_gmst_gmsl.png"
    out_pdf = OUT_DIR / "fair_brick_vs_obs_gmst_gmsl.pdf"
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_png}")
    print(f"wrote {out_pdf}")

    # Diagnostic table at landmark years
    print("\n=== Landmark values ===")
    def at(yrs, v, y):
        m = yrs == y
        return float(v[m][0]) if m.any() else float("nan")

    print(f"{'year':>6}  {'FaIR median °C':>16}  {'IGCC °C':>10}  {'BE °C':>10}")
    for y in (1900, 1950, 1980, 2000, 2010, 2020, 2024, 2050, 2100):
        print(f"  {y:>4}  {at(yrs_m, med_t, y):>16.3f}  "
              f"{at(yrs_i, gmst_i_n, y):>10.3f}  {at(yrs_b, gmst_b_n, y):>10.3f}")

    print(f"\n{'year':>6}  {'BRICK median cm':>16}  {'Dangen cm':>10}  {'C&W cm':>10}  {'IGCC cm':>10}")
    yrs_d, dan, _ = load_dangendorf();   dan_n = rebaseline_series(yrs_d, dan, *GMSL_BASE)
    yrs_c, chu, _ = load_church();       chu_n = rebaseline_series(yrs_c, chu, *GMSL_BASE)
    yrs_ig, ig, _ = load_igcc_gmsl();    ig_n  = rebaseline_series(yrs_ig, ig, *GMSL_BASE)
    for y in (1900, 1950, 1980, 2000, 2010, 2020, 2024, 2050, 2100):
        print(f"  {y:>4}  {at(yrs_s, slr_med, y):>16.2f}  "
              f"{at(yrs_d, dan_n, y):>10.2f}  {at(yrs_c, chu_n, y):>10.2f}  "
              f"{at(yrs_ig, ig_n, y):>10.2f}")


if __name__ == "__main__":
    main()
