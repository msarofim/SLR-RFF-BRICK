"""
build_fredi_inputs_v145.py
==========================

Build the v1.4.5 FrEDI phaseC input CSVs from the v1.4.5 LHS-10k ensemble.

Produces two wide CSVs that the R driver `run_fredi_slr_phaseC_baseline_v145.R`
consumes — drop-in replacement for the legacy v1.4.1 500-cell inputs that have
been quarantined to outputs/quarantine/20260525_pre_v145_fredi/.

Outputs (both wide; one row per draw, year cols 2000-2300):
  outputs/fredi_input_rff_baseline_gmst_v145.csv  (°C rel 1986-2005)
  outputs/fredi_input_rff_baseline_slr_v145.csv   (cm rel 2000)

Each row carries the same metadata columns as the legacy CSVs:
  draw_idx, rff_idx, fair_cfg_idx, seed_idx, post_idx, w_norm

## Methodological choices (explicit per CLAUDE.md)

  N_DRAWS = 1000              — stratified-by-weight (SIR) subsample of LHS-10k
  GMST baseline = 1986-2005   — FrEDI damage-function convention
  SLR baseline  = 2000        — already done by the BRICK driver (slim CSV
                                 stores cm rel 2000)
  GMST source   = LHS-10k baseline FaIR cube (gmst_traj, 1850-2300)
  SLR source    = brick_lhs10k_baseline_to2300_weighted.csv (slim, year cols)

The SIR resample yields equal-weighted draws representative of the
importance-weighted target, so the R driver should pass uniform weights
(w_norm = 1/N) downstream. We carry the resampled cells' original w_norm
in the output CSVs anyway for audit / inspection.

  Stratified-by-weight = "systematic resampling on the cumulative w_norm CDF",
  the standard SIR trick. See e.g. Doucet et al. "On sequential Monte Carlo
  sampling methods" (1998) §2.3.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FAI  = Path.home() / "Documents/2026/CodeProjects/FaIRtoFrEDI"
CUBE = FAI / "fair_outputs/cubes_v145/cube_v145_lhs10k_baseline.npz"
BRICK_SLIM = ROOT / "outputs/brick_v145_slim/brick_lhs10k_baseline_to2300_weighted.csv"

OUT_DIR = ROOT / "outputs"
OUT_GMST = OUT_DIR / "fredi_input_rff_baseline_gmst_v145.csv"
OUT_SLR  = OUT_DIR / "fredi_input_rff_baseline_slr_v145.csv"

N_DRAWS         = 1000
FREDI_YEAR_LO   = 2000
FREDI_YEAR_HI   = 2300
GMST_BASE_LO    = 1986    # FrEDI damage-fn baseline window (inclusive)
GMST_BASE_HI    = 2005    # FrEDI damage-fn baseline window (inclusive)
SEED            = 2026


def main() -> int:
    rng = np.random.default_rng(SEED)

    # ---- load BRICK slim CSV (carries w_norm + per-cell SLR trajectories) ----
    print(f"[load] BRICK slim: {BRICK_SLIM}")
    bs = pd.read_csv(BRICK_SLIM)
    key = ("rff_idx", "fair_cfg_idx", "seed_idx", "post_idx")
    for c in key + ("w_norm",):
        if c not in bs.columns:
            sys.exit(f"BRICK slim missing column '{c}'")
    print(f"  rows: {len(bs):,}; ESS = {(bs.w_norm.sum())**2 / (bs.w_norm**2).sum():.1f}")

    # SLR year columns are bare-string years (legacy slim schema)
    slr_year_cols = [c for c in bs.columns if c.isdigit()]
    slr_years = np.array(sorted(int(c) for c in slr_year_cols))
    print(f"  SLR years: {slr_years.min()}..{slr_years.max()} ({len(slr_years)})")
    assert slr_years.min() <= FREDI_YEAR_LO and slr_years.max() >= FREDI_YEAR_HI, \
        "BRICK slim CSV does not cover FrEDI year window"

    # ---- load LHS-10k baseline cube (GMST trajectory per cell) ----
    print(f"[load] FaIR cube: {CUBE}")
    c = np.load(CUBE, allow_pickle=True)
    cells_meta = np.asarray(c["cells_meta"], dtype=np.int64)  # (n_cells, 3)
    cube_years = np.asarray(c["years"], dtype=np.int64)
    gmst_traj  = np.asarray(c["gmst_traj"], dtype=np.float64)
    n_cells_cube = cells_meta.shape[0]
    print(f"  cube cells: {n_cells_cube:,}; years {cube_years.min()}..{cube_years.max()}")

    # Build cell lookup: (rff, cfg, seed) -> cube row
    cube_idx = {(int(r), int(cf), int(s)): i for i, (r, cf, s) in enumerate(cells_meta)}

    # ---- pair BRICK slim rows to cube cells ----
    bs_keys = list(zip(bs.rff_idx.astype(int),
                        bs.fair_cfg_idx.astype(int),
                        bs.seed_idx.astype(int)))
    cube_rows = np.array([cube_idx.get(k, -1) for k in bs_keys])
    n_unpaired = int((cube_rows < 0).sum())
    if n_unpaired:
        # Slim CSV cells that don't appear in the cube — shouldn't happen
        # because both are LHS-10k. Hard-fail loudly.
        raise RuntimeError(f"{n_unpaired} BRICK slim cells absent from FaIR cube")

    # ---- compute per-cell 1986-2005 GMST mean for FrEDI baselining ----
    base_mask = (cube_years >= GMST_BASE_LO) & (cube_years <= GMST_BASE_HI)
    if base_mask.sum() != (GMST_BASE_HI - GMST_BASE_LO + 1):
        sys.exit(f"cube missing some years in {GMST_BASE_LO}-{GMST_BASE_HI}")
    per_cell_base = gmst_traj[:, base_mask].mean(axis=1)   # (n_cells_cube,)

    # Weighted ensemble-mean 1986-2005 GMST anchor (for log only;
    # we subtract per-cell base, not the ensemble mean).
    w = bs.w_norm.to_numpy()
    ens_mean_base = float(np.average(per_cell_base[cube_rows], weights=w))
    print(f"  weighted ensemble-mean 1986-2005 GMST = {ens_mean_base:.4f} °C "
          "(rel pre-industrial — informational only)")

    # ---- SIR (stratified-by-weight) resample to N_DRAWS ----
    # Systematic resampling: pick u_i = (i + U) / N for i=0..N-1, U~U(0,1),
    # then take the cell whose cumulative weight first exceeds u_i.
    w_norm = w / w.sum()
    cdf = np.cumsum(w_norm)
    U = rng.random()
    targets = (np.arange(N_DRAWS) + U) / N_DRAWS
    picks = np.searchsorted(cdf, targets, side="right")
    picks = np.minimum(picks, len(bs) - 1)
    print(f"[SIR] N_DRAWS={N_DRAWS}; unique cells picked: {len(np.unique(picks))}")

    # ---- assemble metadata + year columns ----
    fredi_years = np.arange(FREDI_YEAR_LO, FREDI_YEAR_HI + 1)
    cube_year_mask = np.isin(cube_years, fredi_years)
    fredi_year_idx = {int(y): int(np.where(cube_years == y)[0][0]) for y in fredi_years}
    fredi_year_cols_cube = [fredi_year_idx[y] for y in fredi_years]

    gmst_rows: list[dict] = []
    slr_rows:  list[dict] = []
    for draw_idx, slim_row in enumerate(picks):
        meta = bs.iloc[int(slim_row)]
        cube_row = int(cube_rows[int(slim_row)])
        gmst_cell = gmst_traj[cube_row, fredi_year_cols_cube] - per_cell_base[cube_row]
        slr_cell  = bs.iloc[int(slim_row)][[str(y) for y in fredi_years]].to_numpy(dtype=np.float64)

        common = {
            "draw_idx":     int(draw_idx),
            "rff_idx":      int(meta.rff_idx),
            "fair_cfg_idx": int(meta.fair_cfg_idx),
            "seed_idx":     int(meta.seed_idx),
            "post_idx":     int(meta.post_idx),
            "w_norm":       1.0 / N_DRAWS,   # SIR: equal weight after resample
        }
        gmst_rows.append({**common, **{str(y): float(g) for y, g in zip(fredi_years, gmst_cell)}})
        slr_rows.append( {**common, **{str(y): float(s) for y, s in zip(fredi_years, slr_cell)}})

    gmst_df = pd.DataFrame(gmst_rows)
    slr_df  = pd.DataFrame(slr_rows)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    gmst_df.to_csv(OUT_GMST, index=False)
    slr_df.to_csv(OUT_SLR,  index=False)
    print(f"[save] {OUT_GMST}  shape={gmst_df.shape}")
    print(f"[save] {OUT_SLR}   shape={slr_df.shape}")

    # ---- spot-check at landmark years ----
    print("\n=== Spot-check (median across N=1,000 resampled draws) ===")
    for y in (2050, 2100, 2150, 2300):
        g_med = float(np.median(gmst_df[str(y)]))
        s_med = float(np.median(slr_df[str(y)]))
        print(f"  {y}: GMST median = {g_med:+.3f} °C (rel 1986-2005)   "
              f"SLR median = {s_med:+.2f} cm (rel 2000)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
