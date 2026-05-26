"""
build_rff_summary_features.py
=============================

Compute per-RFF emissions summary statistics from the 10,000 RFF-SP
emissions CSVs in data/RFF-SP-emissions/csv/. Output a single
outputs/rff_summary_features.csv keyed by rff_idx with continuous
per-draw covariates suitable for use as Shapley features.

Per-RFF features (8 statistics):
  cum_co2_2030          GtCO2, cumulative CO2 FFI+AFOLU 2015-2030
  cum_co2_2100          GtCO2, cumulative 2015-2100
  cum_co2_2300          GtCO2, cumulative 2015-2300
  peak_co2_emissions    GtCO2/yr, max annual CO2 FFI+AFOLU
  peak_co2_year         year of peak emissions
  slope_co2_2050_2100   GtCO2/yr per decade, linear fit
  frac_negative_post_2050  fraction of years 2050-2300 with negative CO2
  cum_ch4_2100          Tg CH4, cumulative CH4 emissions 2015-2100
"""
from __future__ import annotations
import csv
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
EMISSIONS_DIR = ROOT / "data" / "RFF-SP-emissions" / "csv"
OUT_CSV = ROOT / "outputs" / "rff_summary_features.csv"

YEAR_LO = 2015
YEAR_HI = 2300
SPECIES_CO2_FFI = "AR6 climate diagnostics|Emissions|CO2|Energy and Industrial Processes"
SPECIES_CO2_AFOLU = "AR6 climate diagnostics|Emissions|CO2|AFOLU"
SPECIES_CH4 = "AR6 climate diagnostics|Emissions|CH4"


def _per_file_summary(path: Path) -> dict:
    df = pd.read_csv(path)
    years = [str(y) for y in range(YEAR_LO, YEAR_HI + 1)]
    # CO2 FFI + AFOLU (in Mt CO2/yr in RFF-SP convention, convert to GtCO2/yr)
    ffi = df[df.variable == SPECIES_CO2_FFI]
    afolu = df[df.variable == SPECIES_CO2_AFOLU]
    ch4 = df[df.variable == SPECIES_CH4]
    if len(ffi) != 1 or len(afolu) != 1 or len(ch4) != 1:
        raise RuntimeError(f"{path}: unexpected species count "
                            f"(ffi={len(ffi)}, afolu={len(afolu)}, ch4={len(ch4)})")
    co2 = (ffi[years].iloc[0].to_numpy(dtype=float)
            + afolu[years].iloc[0].to_numpy(dtype=float)) / 1000.0  # Mt → Gt
    ch4_traj = ch4[years].iloc[0].to_numpy(dtype=float)  # Tg CH4/yr in RFF-SP
    years_arr = np.array([int(y) for y in years])

    # Summary stats
    cum_2030 = float(co2[years_arr <= 2030].sum())
    cum_2100 = float(co2[years_arr <= 2100].sum())
    cum_2300 = float(co2.sum())
    peak_emi = float(co2.max())
    peak_year = int(years_arr[int(np.argmax(co2))])
    mask_5100 = (years_arr >= 2050) & (years_arr <= 2100)
    if mask_5100.sum() >= 2:
        slope_5100, _ = np.polyfit(years_arr[mask_5100], co2[mask_5100], 1)
    else:
        slope_5100 = 0.0
    mask_post50 = years_arr >= 2050
    frac_neg = float((co2[mask_post50] < 0).mean()) if mask_post50.sum() else 0.0
    cum_ch4_2100 = float(ch4_traj[years_arr <= 2100].sum())
    return {
        "rff_idx":               int(df.scenario.iloc[0]),
        "cum_co2_2030":          cum_2030,
        "cum_co2_2100":          cum_2100,
        "cum_co2_2300":          cum_2300,
        "peak_co2_emissions":    peak_emi,
        "peak_co2_year":         peak_year,
        "slope_co2_2050_2100":   float(slope_5100),
        "frac_negative_post_2050": frac_neg,
        "cum_ch4_2100":          cum_ch4_2100,
    }


def main():
    if not EMISSIONS_DIR.exists():
        sys.exit(f"missing RFF-SP emissions dir at {EMISSIONS_DIR}")
    files = sorted(EMISSIONS_DIR.glob("emissions*.csv"))
    print(f"found {len(files)} RFF-SP emission CSVs", flush=True)
    rows = []
    for i, f in enumerate(files):
        rows.append(_per_file_summary(f))
        if (i + 1) % 1000 == 0:
            print(f"  {i+1:5d}/{len(files)}", flush=True)
    df = pd.DataFrame(rows).sort_values("rff_idx").reset_index(drop=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    print(f"\nwrote {OUT_CSV}  ({len(df)} rows × {df.shape[1]} cols)")
    print("\nDistribution preview:")
    print(df.describe().T[["mean", "std", "min", "50%", "max"]].round(2))


if __name__ == "__main__":
    main()
