"""
Build a spliced observed OHC time series (Zanna 2019 PNAS + IGCC 2024).

Parallel to `build_ohc_spliced.py` (which uses Cheng IAPv4.2 for the modern
era). The IGCC variant is preferred for pipeline internal consistency with
our IGCC GMST input — same Palmer/von Schuckmann compilation methodology
across both inputs.

Output frame: cumulative OHC since 1750 (FaIR's internal reference year),
units 10^22 J.

Pipeline:
  1850-1869:    FaIR ensemble-mean OHC trajectory (mean over LHS-10k baseline cube).
  1870-1970:    Zanna 2019 OHC_2000m, shifted so Zanna(1871) ≈ FaIR_mean(1871).
  1971-2024:    IGCC ocean_0-2000m (0-700m + 700-2000m), spliced via a
                centered N-year window mean onto Zanna_aligned.

The splice transition is at 1970→1971 (IGCC's start year). The window for
the offset computation is centered on 1970 with halfwindow ±2 yrs
(1968-1972), mirroring the Cheng-splice convention.

Inputs:
  data/observations/raw/zanna2019_OHC_GF_1870_2018.nc
  data/observations/raw/igcc2024/.../earth_energy_imbalance.csv
  outputs/rff_baseline_stoch_to2300.npz   (FaIR baseline cube)

Output:
  data/observations/ohc_spliced_zanna_igcc.csv      (parallel canonical)

Refs:
  Zanna L. et al. 2019. PNAS 116:1126-1131. doi:10.1073/pnas.1808838115
  Forster P. et al. 2025 (IGCC 2024). ESSD 17:2641-...
    Palmer/von Schuckmann ocean-heat compilation,
    Zenodo doi:10.5281/zenodo.15744430.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr

# --- Configuration (named constants per project convention) -----------------
REPO_ROOT = Path("/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK")
ZANNA_NC = REPO_ROOT / "data/observations/raw/zanna2019_OHC_GF_1870_2018.nc"
IGCC_CSV = (REPO_ROOT / "data/observations/raw/igcc2024/"
                       "ClimateIndicator-data-2cd2409/data/earth_energy_imbalance/"
                       "earth_energy_imbalance.csv")
FAIR_CUBE_NPZ = REPO_ROOT / "outputs/rff_baseline_stoch_to2300.npz"

OUT_CSV = REPO_ROOT / "data/observations/ohc_spliced_zanna_igcc.csv"

ZANNA_DEPTH_VAR = "OHC_2000m"
ZANNA_ERR_VAR = "error_OHC_2000"

ANCHOR_YEAR = 1871                       # earliest Zanna year with non-zero OHC
# IGCC starts 1971, so the splice must be ≥1973 for a ±2 yr window. Pick
# 1980 to put the offset comparison in the modern era where IGCC and Zanna
# have higher signal-to-noise.
SPLICE_YEAR = 1980
SPLICE_OFFSET_HALFWINDOW = 2             # 5-year centered window for offset

START_YEAR_OUT = 1850

ZANNA_UNIT_TO_BRICK = 0.1                # Zanna ZJ -> 1e22 J
IGCC_UNIT_TO_BRICK = 0.1                 # IGCC ZJ -> 1e22 J


def load_zanna(nc_path: Path) -> pd.DataFrame:
    ds = xr.open_dataset(nc_path)
    year = ds["time"].values.astype(int)
    ohc_zj = ds[ZANNA_DEPTH_VAR].values
    err_zj = ds[ZANNA_ERR_VAR].values
    df = pd.DataFrame({
        "year": year,
        "zanna_ohc_1e22J": ohc_zj * ZANNA_UNIT_TO_BRICK,
        "zanna_err_1e22J": err_zj * ZANNA_UNIT_TO_BRICK,
    }).set_index("year")
    return df


def load_igcc(csv_path: Path) -> pd.DataFrame:
    """Read IGCC EEI CSV, return 0-2000m and full-depth OHC + propagated
    error in 10^22 J, indexed by integer year."""
    df = pd.read_csv(csv_path)
    df["year"] = df["time"].astype(int)
    df = df.set_index("year")
    out = pd.DataFrame(index=df.index)
    out["igcc_0_2000m_1e22J"] = (df["ocean_0-700m"] + df["ocean_700-2000m"]) * IGCC_UNIT_TO_BRICK
    # Error: combine 0-700m and 700-2000m in quadrature (assume independent)
    out["igcc_0_2000m_err_1e22J"] = (
        np.sqrt(df["ocean_0-700m_error"]**2 + df["ocean_700-2000m_error"]**2)
        * IGCC_UNIT_TO_BRICK
    )
    out["igcc_full_1e22J"] = df["ocean_full-depth"] * IGCC_UNIT_TO_BRICK
    out["igcc_full_err_1e22J"] = df["ocean_full-depth_error"] * IGCC_UNIT_TO_BRICK
    return out


def load_fair_mean_ohc(cube_path: Path) -> pd.Series:
    with np.load(cube_path, mmap_mode="r") as z:
        years = z["years"][:]
        ohc = z["ohc_traj_rff"]
        mean_ohc = ohc.mean(axis=(0, 1))
    return pd.Series(mean_ohc.astype(np.float64), index=years, name="fair_mean_ohc_1e22J")


def splice_series(zanna: pd.DataFrame, igcc: pd.DataFrame,
                  fair_mean: pd.Series, splice_year: int,
                  start_year: int, igcc_col: str = "igcc_0_2000m_1e22J") -> pd.DataFrame:
    zanna_shift = fair_mean.loc[ANCHOR_YEAR] - zanna.loc[ANCHOR_YEAR, "zanna_ohc_1e22J"]
    zanna_aligned = zanna["zanna_ohc_1e22J"] + zanna_shift

    w = SPLICE_OFFSET_HALFWINDOW
    win = np.arange(splice_year - w, splice_year + w + 1)
    win_zanna = [y for y in win if y in zanna_aligned.index]
    win_igcc = [y for y in win if y in igcc.index]
    if len(win_zanna) < 2 * w + 1 or len(win_igcc) < 2 * w + 1:
        # IGCC starts in 1971 so a window centered on 1970 would extend to 1972;
        # IGCC has 1971,1972 → 2 of needed 3 if w=2 with center=1970.
        # Reduce halfwindow if needed.
        raise ValueError(f"Splice window {win[0]}-{win[-1]} not fully covered "
                         f"by both products (Zanna: {len(win_zanna)}, "
                         f"IGCC: {len(win_igcc)})")
    zanna_win_mean = zanna_aligned.loc[win_zanna].mean()
    igcc_win_mean = igcc.loc[win_igcc, igcc_col].mean()
    igcc_offset = zanna_win_mean - igcc_win_mean
    igcc_aligned = igcc[igcc_col] + igcc_offset

    end_year = int(igcc_aligned.index.max())
    out_index = np.arange(start_year, end_year + 1)
    out = pd.DataFrame(index=out_index)
    out.index.name = "year"

    pre_zanna = (out.index >= start_year) & (out.index < 1870)
    out.loc[pre_zanna, "ohc_1e22J"] = fair_mean.reindex(out.index[pre_zanna]).values
    out.loc[pre_zanna, "source"] = "fair_mean"

    zanna_range = (out.index >= 1870) & (out.index <= splice_year)
    out.loc[zanna_range, "ohc_1e22J"] = zanna_aligned.reindex(out.index[zanna_range]).values
    out.loc[zanna_range, "source"] = "zanna_aligned"

    igcc_range = out.index > splice_year
    out.loc[igcc_range, "ohc_1e22J"] = igcc_aligned.reindex(out.index[igcc_range]).values
    out.loc[igcc_range, "source"] = "igcc_aligned"

    out.attrs = {
        "zanna_shift_1e22J": float(zanna_shift),
        "igcc_offset_1e22J": float(igcc_offset),
        "anchor_year": ANCHOR_YEAR,
        "splice_year": splice_year,
        "splice_window": f"{int(win[0])}-{int(win[-1])}",
        "igcc_col": igcc_col,
    }
    return out


def main() -> None:
    print(f"Loading Zanna 2019: {ZANNA_NC.name}")
    zanna = load_zanna(ZANNA_NC)
    print(f"  rows: {len(zanna)}, years: {int(zanna.index.min())}-{int(zanna.index.max())}")

    print(f"Loading IGCC EEI: {IGCC_CSV.name}")
    igcc = load_igcc(IGCC_CSV)
    print(f"  rows: {len(igcc)}, years: {int(igcc.index.min())}-{int(igcc.index.max())}")

    print(f"Loading FaIR baseline cube...")
    fair_mean = load_fair_mean_ohc(FAIR_CUBE_NPZ)
    print(f"  rows: {len(fair_mean)}")

    print(f"\nBuilding canonical Zanna+IGCC splice (year={SPLICE_YEAR}, IGCC 0-2000m)")
    canonical = splice_series(zanna, igcc, fair_mean, SPLICE_YEAR, START_YEAR_OUT,
                              igcc_col="igcc_0_2000m_1e22J")
    for k, v in canonical.attrs.items():
        print(f"  {k}: {v}")

    pre = canonical.loc[SPLICE_YEAR, "ohc_1e22J"]
    post = canonical.loc[SPLICE_YEAR + 1, "ohc_1e22J"]
    print(f"  splice point: OHC({SPLICE_YEAR})={pre:.3f}, OHC({SPLICE_YEAR+1})={post:.3f}, "
          f"Δ={post-pre:+.3f}")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    canonical_out = canonical.reset_index()
    header = (
        f"# Spliced observed OHC (cumulative since FaIR 1750-zero), units 1e22 J\n"
        f"# Zanna 2019 PNAS (1870-{SPLICE_YEAR}, OHC_2000m, anchored to FaIR mean at {ANCHOR_YEAR}); "
        f"IGCC 2024 ocean_0-2000m ({SPLICE_YEAR+1}-{int(igcc.index.max())}, "
        f"5-yr windowed offset at {SPLICE_YEAR}; Palmer/von Schuckmann compilation)\n"
        f"# 1850-1869 filled from FaIR ensemble-mean\n"
        f"# zanna_shift_1e22J={canonical.attrs['zanna_shift_1e22J']:.6f}, "
        f"igcc_offset_1e22J={canonical.attrs['igcc_offset_1e22J']:.6f}\n"
    )
    with open(OUT_CSV, "w") as f:
        f.write(header)
        canonical_out.to_csv(f, index=False, float_format="%.6f")
    print(f"\nwrote {OUT_CSV}  ({len(canonical)} rows, "
          f"{int(canonical.index.min())}-{int(canonical.index.max())})")


if __name__ == "__main__":
    main()
