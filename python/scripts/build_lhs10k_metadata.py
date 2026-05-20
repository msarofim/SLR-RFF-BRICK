"""
build_lhs10k_metadata.py
========================

Generate a 10,000-row LHS metadata CSV for the conditional BRICK ensemble.

Each row is one stratified-sampled triplet:
  (rff_idx, fair_cfg_idx, seed_idx=0, post_idx)

Sampling design:
  - rff_idx: stratified uniform over the cube's unique_rffs (490 distinct
    IDs in the production cube). Each RFF used ~20 times.
  - fair_cfg_idx: stratified uniform over 0..840 (each cfg used ~12 times).
  - post_idx: stratified uniform over 1..10,000. With N=10k, each BRICK
    posterior member is used ~once — full posterior coverage by construction.
  - seed_idx = 0 throughout (cube is 3-D rff×cfg×year; no seed dim).
  - Triplet pairing is randomized (independent permutations of each axis),
    giving an LHS-style design with good 1-D marginal coverage and
    no spurious structural correlations between axes.

The Wong importance weights computed downstream are conditional on the
specific (cfg, post) pairing each row carries — so this metadata + the
existing apply_wong_weights.py pipeline gives the "conditional BRICK"
sampling that the marginal-posterior design was missing.

Convention reminders (match build_ofat_anova_metadata.py):
  rff_idx:      VALUE from unique_rffs (matches cube's rffs.npy row 1-indexing)
  fair_cfg_idx: 0-indexed (Julia driver adds 1)
  seed_idx:     0-indexed
  post_idx:     1-indexed (matches posterior CSV row indexing)

Inputs:
  outputs/rff_baseline_stoch_to2300_rffs.npy   (the 490 unique RFF IDs)

Output:
  outputs/lhs10k_metadata.csv

Usage:
  python python/scripts/build_lhs10k_metadata.py
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT  = ROOT / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

UNIQUE_RFFS_NPY = OUT / "rff_baseline_stoch_to2300_rffs.npy"

N_SAMPLES = 10_000
N_CFG     = 841        # FaIR v1.4.1 posterior
N_POST    = 10_000     # MimiBRICK posterior_subsample_brick rows
SEED      = 2026


def stratified_int(N: int, max_val: int, rng: np.random.Generator) -> np.ndarray:
    """Return N integers in [0, max_val) covering the range via stratified
    uniform sampling (one draw per equal-width stratum)."""
    edges = np.linspace(0, max_val, N + 1)
    u = rng.uniform(size=N)
    samples = (edges[:-1] + u * (edges[1:] - edges[:-1])).astype(int)
    return np.clip(samples, 0, max_val - 1)


def main():
    if not UNIQUE_RFFS_NPY.exists():
        sys.exit(f"Missing input: {UNIQUE_RFFS_NPY}\n"
                 f"Extract it from the Torch cube via "
                 f"np.save(..., np.load(cube)['unique_rffs'].astype(np.int64))")
    unique_rffs = np.load(UNIQUE_RFFS_NPY).astype(int)
    n_rff = len(unique_rffs)
    print(f"unique_rffs: {n_rff} IDs, range [{unique_rffs.min()}, {unique_rffs.max()}]")

    rng = np.random.default_rng(SEED)

    # Stratified within each axis
    rff_strata  = stratified_int(N_SAMPLES, n_rff,  rng)
    cfg_strata  = stratified_int(N_SAMPLES, N_CFG,  rng)
    post_strata = stratified_int(N_SAMPLES, N_POST, rng)
    # Independent permutations for LHS-style decoupling.
    rng.shuffle(rff_strata)
    rng.shuffle(cfg_strata)
    rng.shuffle(post_strata)

    rff_ids   = unique_rffs[rff_strata]
    cfg_idx   = cfg_strata
    post_idx  = post_strata + 1     # 1-indexed for Julia
    seed_idx  = np.zeros(N_SAMPLES, dtype=int)

    meta = pd.DataFrame({
        "sample":       np.arange(N_SAMPLES),
        "draw_id":      np.arange(N_SAMPLES),
        "rff_idx":      rff_ids,
        "fair_cfg_idx": cfg_idx,
        "seed_idx":     seed_idx,
        "post_idx":     post_idx,
        "axis":         "lhs",
    })

    # Coverage stats
    print(f"\n--- coverage ---")
    print(f"unique RFFs used:  {meta.rff_idx.nunique():>5} / {n_rff}    "
          f"(min reuse {meta.rff_idx.value_counts().min()}, "
          f"max reuse {meta.rff_idx.value_counts().max()})")
    print(f"unique cfgs used:  {meta.fair_cfg_idx.nunique():>5} / {N_CFG}    "
          f"(min reuse {meta.fair_cfg_idx.value_counts().min()}, "
          f"max reuse {meta.fair_cfg_idx.value_counts().max()})")
    print(f"unique posts used: {meta.post_idx.nunique():>5} / {N_POST}    "
          f"(min reuse {meta.post_idx.value_counts().min()}, "
          f"max reuse {meta.post_idx.value_counts().max()})")

    out_csv = OUT / "lhs10k_metadata.csv"
    meta.to_csv(out_csv, index=False)
    print(f"\nwrote {out_csv}  ({len(meta)} rows)")
    print("\nFirst 5 rows:")
    print(meta.head().to_string(index=False))


if __name__ == "__main__":
    main()
