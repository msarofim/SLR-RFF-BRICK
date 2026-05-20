"""
obs_overlay_slr.py
==================

Substack figure: FaIR × BRICK ensemble band vs observed GMSL.  Companion
to obs_overlay.py (which does the same comparison for GMST).

Three observational series are overlaid:
  • Church & White 2011 (updated to 2013) — BRICK's actual calibration
    target. Source: CSIRO_Recons_gmsl_yr_2015.csv (MimiBRICK package data).
  • Dangendorf et al. 2024 — newer tide-gauge reconstruction, more recent
    methodology. NOT a BRICK calibration target.
  • NOAA STAR satellite altimetry — modern altimetry record (1993+).

The Church & White overlay was added 2026-05-20 in response to Tony Wong's
note that BRICK was never calibrated against Dangendorf, and the "BRICK
underestimates GMSL" finding against Dangendorf is partly a different-
obs-dataset issue rather than a structural BRICK shortcoming. Comparing
against the actual calibration target gives a fairer view of BRICK quality.

All series re-referenced to year 2000 (the project's standard SLR baseline):
  Model: brick_lhs10k_baseline_to2300_weighted.csv stores year-column
         values as 100·(gmsl[t] − gmsl[2000]) in cm.
  Church & White 2011: native is mm with mid-year timestamps (e.g., 1880.5);
                       we floor to integer year and convert mm → cm.
  Dangendorf 2024: native is mm relative to a centred 20th-century baseline;
                   rebaselined to year 2000.
  NOAA STAR altimetry: native is mm relative to a 1993 baseline; rebaselined
                   to year 2000.

The model band is plotted RAW (i.e., NOT AR6-bias-corrected to the
observed anchor — the purpose of this figure is to expose the model-obs
fit; bias correction would make the agreement at 2015-2024 tautological
by construction, identical to the rationale in obs_overlay.py for GMST).

Inputs:
  outputs/brick_lhs10k_baseline_to2300_weighted.csv
  data/calibration/CSIRO_Recons_gmsl_yr_2015.csv          (Church & White)
  data/observations/dangendorf_2024_gmsl.csv
  data/observations/nasa_gmsl_annual.csv

Output:
  outputs/substack/obs_overlay_slr.{png,pdf}
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
MODEL_CSV     = ROOT / "outputs" / "brick_lhs10k_baseline_to2300_weighted.csv"
CW_CSV        = ROOT / "data" / "calibration" / "CSIRO_Recons_gmsl_yr_2015.csv"
DANG_CSV      = ROOT / "data" / "observations" / "dangendorf_2024_gmsl.csv"
NASA_CSV      = ROOT / "data" / "observations" / "nasa_gmsl_annual.csv"
OUT           = ROOT / "outputs" / "substack"
OUT.mkdir(parents=True, exist_ok=True)

PLOT_START = 1900
PLOT_END   = 2050   # extend slightly past observed (2024) to show near-term


def w_quantile(v, w, q):
    o = np.argsort(v); v = v[o]; w = w[o]; cw = np.cumsum(w)
    return v[np.searchsorted(cw, q * cw[-1])]


def model_band(plot_years):
    df = pd.read_csv(MODEL_CSV)
    yc = sorted([c for c in df.columns if c.isdigit()], key=int)
    yrs = np.array([int(c) for c in yc])
    Y = df[yc].to_numpy()              # cm rel year 2000
    w = df.w_norm.to_numpy()
    plot_mask = np.isin(yrs, plot_years)
    Yp = Y[:, plot_mask]
    yrs_p = yrs[plot_mask]
    p5  = np.array([w_quantile(Yp[:, j], w, 0.05) for j in range(Yp.shape[1])])
    p50 = np.array([w_quantile(Yp[:, j], w, 0.50) for j in range(Yp.shape[1])])
    p95 = np.array([w_quantile(Yp[:, j], w, 0.95) for j in range(Yp.shape[1])])
    mn  = np.array([np.average(Yp[:, j], weights=w) for j in range(Yp.shape[1])])
    return yrs_p, p5, p50, p95, mn


def rebase_obs_to_2000_cm(path):
    """Load an obs CSV with columns (year, value [mm], ...) and rebaseline
    to year 2000.  Returns (year_array, value_cm_rel_2000)."""
    df = pd.read_csv(path)
    df = df.sort_values("year").reset_index(drop=True)
    if 2000 not in df.year.values:
        # NOAA STAR & Dangendorf both have year 2000; safety check.
        raise RuntimeError(f"{path.name}: year 2000 not present")
    v2000_mm = float(df.loc[df.year == 2000, "value"].iloc[0])
    df["cm_rel_2000"] = (df["value"] - v2000_mm) / 10.0
    return df.year.to_numpy(), df["cm_rel_2000"].to_numpy()


def load_church_white(path):
    """Load Church & White 2011 reconstruction from the CSIRO-distributed
    CSV.  File has 9 metadata lines, then the header
    'Time,GMSL (mm),GMSL 1-sigma uncertainty (mm)' on line 10, then data.
    Some metadata lines are quoted (starting with '"#') so pandas'
    comment='#' option won't catch all of them — easier to skiprows=9.
    Time column uses mid-year convention (1880.5 = annual mean for 1880).
    Returns (year_int_array, cm_rel_2000_array).
    """
    df = pd.read_csv(path, skiprows=9)
    gmsl_col = [c for c in df.columns if "GMSL" in c and "uncertainty" not in c][0]
    years = np.floor(df["Time"].to_numpy()).astype(int)
    mm = df[gmsl_col].to_numpy(dtype=float)
    if 2000 not in years:
        raise RuntimeError(f"{path.name}: year 2000 not present in floored Time column")
    v2000 = float(mm[years == 2000][0])
    cm_rel_2000 = (mm - v2000) / 10.0
    return years, cm_rel_2000


def main():
    plot_years = np.arange(PLOT_START, PLOT_END + 1)

    yrs_m, p5, p50, p95, mn = model_band(plot_years)
    print(f"Model band: years {yrs_m.min()}-{yrs_m.max()}  "
          f"n_years={len(yrs_m)}")

    cw_y, cw_v = load_church_white(CW_CSV)
    dy, dv = rebase_obs_to_2000_cm(DANG_CSV)
    ny, nv = rebase_obs_to_2000_cm(NASA_CSV)
    print(f"Church & White 2011: years {cw_y.min()}-{cw_y.max()}  "
          f"(2000 by construction = 0, last value = {cw_v[-1]:.2f} cm)")
    print(f"Dangendorf 2024:     years {dy.min()}-{dy.max()}  "
          f"(2000 by construction = 0, last value = {dv[-1]:.2f} cm)")
    print(f"NOAA STAR altimetry: years {ny.min()}-{ny.max()}  "
          f"(2000 by construction = 0, last value = {nv[-1]:.2f} cm)")

    # ---- plot ----
    fig, ax = plt.subplots(figsize=(9.5, 5.6))

    ax.fill_between(yrs_m, p5, p95, color="#7570B3", alpha=0.18,
                    label="FaIR × BRICK 5–95% (RFF × configs × seed × posterior)")
    ax.plot(yrs_m, p50, color="#7570B3", linewidth=2.2,
            label="FaIR × BRICK ensemble median")
    ax.plot(yrs_m, mn, color="#7570B3", linewidth=1.0, linestyle="--",
            label="FaIR × BRICK ensemble mean")

    ax.plot(cw_y, cw_v, color="#1B7837", linewidth=2.0,
            label="Church & White 2011 (BRICK calibration target)")
    ax.plot(dy, dv, color="#A6361C", linewidth=2.0,
            label="Dangendorf et al. 2024 reconstruction")
    ax.plot(ny, nv, color="#000000", linewidth=2.0,
            label="NOAA STAR satellite altimetry")

    ax.axhline(0, color="grey", linewidth=0.6)
    ax.axvline(2000, color="grey", linewidth=0.4, linestyle=":")
    ax.set_xlim(PLOT_START, PLOT_END)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("GMSL anomaly (cm, rel. year 2000)", fontsize=11)
    ax.set_title("FaIR × BRICK ensemble vs. observed GMSL "
                 "(rel. year 2000)",
                 fontsize=13, fontweight="bold", color="#1F4E79")
    ax.legend(loc="upper left", fontsize=9.5, framealpha=0.92)
    ax.grid(alpha=0.3, linewidth=0.5)

    fig.tight_layout()
    fig.savefig(OUT / "obs_overlay_slr.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / "obs_overlay_slr.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT / 'obs_overlay_slr.png'}")

    # Diagnostics at landmark years
    print("\nObs vs model centroid (cm rel year 2000):")
    for y in (1900, 1950, 1980, 2000, 2013, 2020, 2024):
        line = f"  {y}:"
        if y in yrs_m:
            j = int(np.where(yrs_m == y)[0][0])
            line += f"  model_p50={p50[j]:+.2f}  p5={p5[j]:+.2f}  p95={p95[j]:+.2f}"
        if y in cw_y:
            line += f"  C&W={cw_v[list(cw_y).index(y)]:+.2f}"
        if y in dy:
            line += f"  Dangendorf={dv[list(dy).index(y)]:+.2f}"
        if y in ny:
            line += f"  NOAA_STAR={nv[list(ny).index(y)]:+.2f}"
        print(line)


if __name__ == "__main__":
    main()
