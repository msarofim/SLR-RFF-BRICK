"""
build_fair_mean_trajectories_v145.py

Build v1.4.5 FaIR ensemble-mean GMST and OHC trajectories from the new
metadata-driven LHS-10k baseline cube. Writes parallel-schema CSVs to the
v1.4.1 ones so downstream scripts can swap by path.

Source cube (flat schema; replaces the old rectangular `rff_baseline_stoch_to2300.npz`):
    FaIRtoFrEDI/fair_outputs/cubes_v145/cube_v145_lhs10k_baseline.npz
      arrays:
        cells_meta  (n_cells, 3)  int   (rff_idx, fair_cfg_idx, seed_idx)
        years       (n_year,)     int
        gmst_traj   (n_cells, n_year) float32, rel 1850-1900
        ohc_traj    (n_cells, n_year) float32, 10^22 J
        erf_2100    (n_cells,)        float32, W/m^2

We compute simple unweighted-mean trajectories over the n_cells axis. For an
LHS sample, each cell is equally weighted by design (no importance weights
applied here).

Output:
    SLR-RFF-BRICK/data/observations/fair_mean_gmst_v145.csv  — year, gmst_C
    SLR-RFF-BRICK/data/observations/fair_mean_ohc_v145.csv   — year, ohc_1e22J
"""
from __future__ import annotations
from pathlib import Path

import numpy as np
import pandas as pd

CUBE_NPZ = Path(
    "/Users/MarcusMarcus/Documents/2026/CodeProjects/FaIRtoFrEDI/"
    "fair_outputs/cubes_v145/cube_v145_lhs10k_baseline.npz"
)
OUT_DIR  = Path(
    "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/"
    "data/observations"
)
OUT_GMST = OUT_DIR / "fair_mean_gmst_v145.csv"
OUT_OHC  = OUT_DIR / "fair_mean_ohc_v145.csv"


def main():
    print(f"Loading v1.4.5 baseline cube: {CUBE_NPZ}")
    with np.load(CUBE_NPZ) as z:
        years     = z["years"][:]
        gmst_traj = z["gmst_traj"][:].astype(np.float64)
        ohc_traj  = z["ohc_traj"][:].astype(np.float64)
        cells     = z["cells_meta"][:]
    n_cells, n_year = gmst_traj.shape
    print(f"  cube shape: {gmst_traj.shape}  ({n_cells} cells, {n_year} years)")
    print(f"  years: {years[0]} – {years[-1]}")

    gmst_mean = gmst_traj.mean(axis=0)
    ohc_mean  = ohc_traj.mean(axis=0)
    print(f"  GMST mean range: {gmst_mean.min():.3f} to {gmst_mean.max():.3f} °C")
    print(f"  OHC  mean range: {ohc_mean.min():.3f} to {ohc_mean.max():.3f} (10^22 J)")
    print(f"  GMST @ 2024 (rel 1850-1900 as cube's native baseline): "
          f"{gmst_mean[np.where(years == 2024)[0][0]]:+.3f} °C")
    print(f"  OHC  @ 2024 (raw cube units): "
          f"{ohc_mean[np.where(years == 2024)[0][0]]:+.2f} (10^22 J)")

    pd.DataFrame({"year": years, "gmst_C": gmst_mean}).to_csv(OUT_GMST, index=False)
    pd.DataFrame({"year": years, "ohc_1e22J": ohc_mean}).to_csv(OUT_OHC, index=False)
    print(f"\nWrote {OUT_GMST}")
    print(f"Wrote {OUT_OHC}")


if __name__ == "__main__":
    main()
