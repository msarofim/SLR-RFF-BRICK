"""
Build FaIR ensemble-mean GMST and OHC trajectories from the LHS-10k baseline
cube and write them as small CSVs in the same schema as the obs files. Lets
the obs-driven BRICK driver run the hybrid (obs-GMST, FaIR-OHC) and
(FaIR-GMST, obs-OHC) diagnostic combinations by just swapping a CSV path.

Cube layout follows python/build_ohc_spliced.py:load_fair_mean_ohc() — mean
over (RFF, cfg) [and seed, if present]. Units: GMST in °C above 1850-1900;
OHC in 10^22 J, cumulative since FaIR's 1750-zero.

Outputs (parallel-schema to data/observations/{igcc2024_gmst_4dataset_mean,
ohc_spliced_zanna_cheng}.csv but spanning the full cube year range):
  data/observations/fair_mean_gmst.csv  — year,gmst_C
  data/observations/fair_mean_ohc.csv   — year,ohc_1e22J
"""

from pathlib import Path
import numpy as np
import pandas as pd

REPO_ROOT = Path("/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK")
FAIR_CUBE_NPZ = REPO_ROOT / "outputs/rff_baseline_stoch_to2300.npz"
OUT_GMST_CSV  = REPO_ROOT / "data/observations/fair_mean_gmst.csv"
OUT_OHC_CSV   = REPO_ROOT / "data/observations/fair_mean_ohc.csv"


def cube_mean(arr: np.ndarray) -> np.ndarray:
    # Cube is (n_rff, n_cfg, [n_seed,] n_year). Mean over all axes except the
    # last (year). Handles both 3D (single-seed, legacy) and 4D (LHS-10k).
    axes_to_mean = tuple(range(arr.ndim - 1))
    return arr.mean(axis=axes_to_mean)


def main() -> None:
    print(f"Loading FaIR cube from {FAIR_CUBE_NPZ} ...")
    with np.load(FAIR_CUBE_NPZ, mmap_mode="r") as z:
        years = z["years"][:]
        gmst_mean = cube_mean(z["gmst_traj_rff"]).astype(np.float64)
        ohc_mean = cube_mean(z["ohc_traj_rff"]).astype(np.float64)
    print(f"  cube years {years[0]}-{years[-1]}  ({len(years)} yrs)")
    print(f"  gmst mean range  {gmst_mean.min():.3f} to {gmst_mean.max():.3f} °C")
    print(f"  ohc  mean range  {ohc_mean.min():.3f} to {ohc_mean.max():.3f} (10^22 J)")

    pd.DataFrame({"year": years, "gmst_C": gmst_mean}).to_csv(OUT_GMST_CSV, index=False)
    pd.DataFrame({"year": years, "ohc_1e22J": ohc_mean}).to_csv(OUT_OHC_CSV, index=False)
    print(f"Wrote {OUT_GMST_CSV}")
    print(f"Wrote {OUT_OHC_CSV}")


if __name__ == "__main__":
    main()
