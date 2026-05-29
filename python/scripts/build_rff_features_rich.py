"""
build_rff_features_rich.py
==========================

Richer per-RFF emissions features for the Group-Sobol H-S surrogate. The
8-summary feature set (build_rff_summary_features.py) capped surrogate OOF R2
at ~0.7 for SLR because it cannot encode the emissions PATHWAY SHAPE that drives
intermediate-year SLR. Here we add decadal cumulative CO2 + CH4 checkpoints and
a few N2O checkpoints. All remain in the "emissions" group, so group-Sobol stays
valid (within-group collinearity is handled by joint pick-and-freeze).

RFF-SP samples only CO2, CH4, N2O across draws (other species infilled common),
so richer features target those three.

Output: outputs/rff_features_rich.csv keyed by rff_idx.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
EMISSIONS_DIR = ROOT / "data" / "RFF-SP-emissions" / "csv"
OUT_CSV = ROOT / "outputs" / "rff_features_rich.csv"

YEAR_LO, YEAR_HI = 2015, 2300
SP_CO2_FFI   = "AR6 climate diagnostics|Emissions|CO2|Energy and Industrial Processes"
SP_CO2_AFOLU = "AR6 climate diagnostics|Emissions|CO2|AFOLU"
SP_CH4       = "AR6 climate diagnostics|Emissions|CH4"
SP_N2O       = "AR6 climate diagnostics|Emissions|N2O"

CO2_DECADES = list(range(2020, 2301, 10))   # 29 checkpoints
CH4_DECADES = list(range(2020, 2301, 20))   # 15 checkpoints
N2O_CHECKS  = [2050, 2100, 2200, 2300]


def _per_file(path: Path) -> dict:
    df = pd.read_csv(path)
    years = [str(y) for y in range(YEAR_LO, YEAR_HI + 1)]
    yarr = np.array([int(y) for y in years])
    def row(sp):
        r = df[df.variable == sp]
        if len(r) != 1:
            raise RuntimeError(f"{path}: {sp} count {len(r)}")
        return r[years].iloc[0].to_numpy(dtype=float)
    co2 = (row(SP_CO2_FFI) + row(SP_CO2_AFOLU)) / 1000.0   # Mt -> Gt CO2/yr
    ch4 = row(SP_CH4)                                       # Tg CH4/yr
    n2o = row(SP_N2O)                                       # kt N2O/yr (RFF unit)

    out = {"rff_idx": int(df.scenario.iloc[0])}
    # decadal cumulative CO2 / CH4 (cumulative from 2015 up to each checkpoint)
    for y in CO2_DECADES:
        out[f"cum_co2_{y}"] = float(co2[yarr <= y].sum())
    for y in CH4_DECADES:
        out[f"cum_ch4_{y}"] = float(ch4[yarr <= y].sum())
    for y in N2O_CHECKS:
        out[f"cum_n2o_{y}"] = float(n2o[yarr <= y].sum())
    # shape descriptors (kept from the original 8 for continuity)
    out["peak_co2_emissions"] = float(co2.max())
    out["peak_co2_year"] = int(yarr[int(np.argmax(co2))])
    m = (yarr >= 2050) & (yarr <= 2100)
    out["slope_co2_2050_2100"] = float(np.polyfit(yarr[m], co2[m], 1)[0]) if m.sum() >= 2 else 0.0
    mp = yarr >= 2050
    out["frac_negative_post_2050"] = float((co2[mp] < 0).mean()) if mp.sum() else 0.0
    return out


def main():
    files = sorted(EMISSIONS_DIR.glob("emissions*.csv"))
    if not files:
        sys.exit(f"no emission CSVs in {EMISSIONS_DIR}")
    print(f"found {len(files)} RFF-SP emission CSVs", flush=True)
    rows = []
    for i, f in enumerate(files):
        rows.append(_per_file(f))
        if (i + 1) % 1000 == 0:
            print(f"  {i+1:5d}/{len(files)}", flush=True)
    df = pd.DataFrame(rows).sort_values("rff_idx").reset_index(drop=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    print(f"\nwrote {OUT_CSV}  ({len(df)} rows x {df.shape[1]} cols)", flush=True)
    # variance check: drop any near-constant feature (e.g. if a species is fixed)
    feat_cols = [c for c in df.columns if c != "rff_idx"]
    stds = df[feat_cols].std()
    const = stds[stds < 1e-9].index.tolist()
    print(f"near-constant features (will be useless): {const}", flush=True)
    print(df[feat_cols].describe().T[["mean", "std", "min", "max"]].round(3).to_string(), flush=True)


if __name__ == "__main__":
    main()
