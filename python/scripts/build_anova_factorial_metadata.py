"""
build_anova_factorial_metadata.py
=================================

Build a balanced crossed-factorial metadata pair for a model-free ANOVA
cross-check of the Group-Sobol SLR Hawkins-Sutton attribution.

Because FaIR output is indexed only by (rff, cfg, seed) and BRICK fans over
`post`, we emit TWO metadata CSVs:

  1. FaIR metadata  — unique (rff_idx, fair_cfg_idx, seed_idx) rows
                      = n_rff × n_cfg × n_seed  (the expensive FaIR grid)
  2. BRICK metadata — crossed with post: every FaIR cell × every post
                      = n_rff × n_cfg × n_seed × n_post  (cheap BRICK fan-out)

Nested-post convention (matches build_ofat_anova_metadata.py): the SAME post
set is used for every (rff,cfg,seed) cell, so V_internal (seed) is not
contaminated by post sampling.

Index conventions (match build_lhs10k_metadata.py):
  rff_idx        VALUE, 1-indexed (matches emissions_v145_rff_<NNNNN>.csv)
  fair_cfg_idx   0-indexed (0..840)
  seed_idx       0-indexed (0..n_seed-1)
  post_idx       0-indexed (0..9999) — run_mimibrick_flatcube.jl asserts [0,9999]
                 and adds 1 internally for the 1-based Julia posterior row.

rff levels are drawn from the set that already has v145 emissions files +
validated FaIR runs (the unique rff in outputs/lhs10ks_brick_metadata.csv),
optionally stratified across the cumulative-CO2 distribution so the emissions
factor spans its range.

Usage:
  python build_anova_factorial_metadata.py --n-rff 100 --n-cfg 30 \
      --n-seed 3 --n-post 3 --tag 27k --stratify-rff
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs"
LHS_META = OUT / "lhs10ks_brick_metadata.csv"          # source of valid rff values
RFF_FEAT = OUT / "rff_summary_features.csv"            # for stratification
N_CFG_TOTAL = 841
N_POST_TOTAL = 10_000
SEED = 2026


def pick_levels(values, n, rng):
    """Evenly-spaced (quantile) pick of n distinct levels from a 1-D array."""
    u = np.unique(values)
    if n >= len(u):
        return u
    idx = np.linspace(0, len(u) - 1, n).round().astype(int)
    return u[np.unique(idx)]


def stratified_rff(n_rff, rng, stratify):
    avail = pd.read_csv(LHS_META, usecols=["rff_idx"])["rff_idx"].unique()
    avail = np.sort(avail)
    if not stratify:
        return np.sort(rng.choice(avail, size=min(n_rff, len(avail)), replace=False))
    feat = pd.read_csv(RFF_FEAT, usecols=["rff_idx", "cum_co2_2100"])
    feat = feat[feat.rff_idx.isin(avail)].sort_values("cum_co2_2100").reset_index(drop=True)
    # take n_rff quantile-spaced rows along the emissions axis
    idx = np.linspace(0, len(feat) - 1, min(n_rff, len(feat))).round().astype(int)
    return np.sort(feat.rff_idx.iloc[np.unique(idx)].to_numpy())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-rff", type=int, default=100)
    ap.add_argument("--n-cfg", type=int, default=30)
    ap.add_argument("--n-seed", type=int, default=3)
    ap.add_argument("--n-post", type=int, default=3)
    ap.add_argument("--tag", type=str, required=True)
    ap.add_argument("--stratify-rff", action="store_true")
    a = ap.parse_args()
    rng = np.random.default_rng(SEED)

    rff = stratified_rff(a.n_rff, rng, a.stratify_rff)
    cfg = pick_levels(np.arange(N_CFG_TOTAL), a.n_cfg, rng)
    seed = np.arange(a.n_seed)
    post = pick_levels(np.arange(N_POST_TOTAL), a.n_post, rng)   # 0-indexed (0..9999)

    print(f"levels: rff={len(rff)} cfg={len(cfg)} seed={len(seed)} post={len(post)}")
    print(f"  FaIR cells  = {len(rff)*len(cfg)*len(seed):,}")
    print(f"  BRICK cells = {len(rff)*len(cfg)*len(seed)*len(post):,}")

    # FaIR metadata: unique (rff, cfg, seed)
    R, C, S = np.meshgrid(rff, cfg, seed, indexing="ij")
    fair = pd.DataFrame({"rff_idx": R.ravel(), "fair_cfg_idx": C.ravel(),
                         "seed_idx": S.ravel()})
    fair["axis"] = f"anova{a.tag}_fair"
    fair_csv = OUT / f"anova{a.tag}_fair_metadata.csv"
    fair.to_csv(fair_csv, index=False)
    print(f"wrote {fair_csv}  ({len(fair):,} rows)")

    # BRICK metadata: crossed with post (nested-post: same post set per cell)
    brick = fair.drop(columns="axis").merge(pd.DataFrame({"post_idx": post}), how="cross")
    brick["axis"] = f"anova{a.tag}_brick"
    brick = brick[["rff_idx", "fair_cfg_idx", "seed_idx", "post_idx", "axis"]]
    brick_csv = OUT / f"anova{a.tag}_brick_metadata.csv"
    brick.to_csv(brick_csv, index=False)
    print(f"wrote {brick_csv}  ({len(brick):,} rows)")

    # sanity: full balance
    assert len(brick) == len(rff) * len(cfg) * len(seed) * len(post)
    print("balanced factorial OK")


if __name__ == "__main__":
    main()
