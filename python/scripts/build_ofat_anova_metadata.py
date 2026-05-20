"""
build_ofat_anova_metadata.py
============================

Construct metadata CSVs for the OFAT cross-check and the ANOVA 4-way SLR
H-S decomposition. Both metadata CSVs feed `run_mimibrick_paired_explicit.jl`.

Conventions in column values:
  rff_idx:      1-indexed (matches the Phase A cube's rffs.npy values 1..2000)
  fair_cfg_idx: 0-indexed (Python-side; the Julia driver adds 1)
  seed_idx:     0-indexed (0..9 for Phase A)
  post_idx:     1-indexed (matches Julia / posterior CSV row indexing 1..10000)

Centroid (mid-point reference for OFAT):
  rff_idx_0     = 1000  (middle of 1..2000)
  fair_cfg_0    = 420   (middle of 0..840)
  seed_0        = 0
  post_idx_0    = 5000  (middle of 1..10000)

OFAT design (4 axes × N samples each, holding the other 3 at centroid):
  vary_rff:  250 random rffs in [1, 2000]
  vary_cfg:  250 random cfgs in [0, 840]
  vary_seed: 10  (use all Phase A seeds 0..9)
  vary_post: 250 random posts in [1, 10000]
  axis column tags each row's group

ANOVA design (factorial):
  100 rffs × 15 random cfgs PER RFF (different cfgs per rff) × 3 seeds × 3 posts
  = 13,500 rows total
  Random cfgs differ across rffs so the cfg space is well-covered.

Outputs:
  outputs/ofat_metadata.csv     ~760 rows
  outputs/anova_metadata.csv   ~13,500 rows
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
N_RFF, N_CFG, N_SEED, N_POST = 2000, 841, 10, 10_000
RFF_0, CFG_0, SEED_0, POST_0 = 1000, 420, 0, 5000

# OFAT
OFAT_N_PER_AXIS = 250
OFAT_RNG_SEED = 2026

# ANOVA factorial sizes
ANOVA_N_RFF, ANOVA_N_CFG_PER_RFF, ANOVA_N_SEED, ANOVA_N_POST = 100, 15, 3, 3
ANOVA_RNG_SEED = 2027


# ----------------------------------------------------------------------------
def build_ofat():
    rng = np.random.default_rng(OFAT_RNG_SEED)
    rows = []

    # axis = "centroid": a single replicate at the centroid (useful baseline)
    rows.append({"axis": "centroid", "rff_idx": RFF_0, "fair_cfg_idx": CFG_0,
                 "seed_idx": SEED_0, "post_idx": POST_0})

    # axis = "vary_rff"
    rff_samples = rng.choice(np.arange(1, N_RFF + 1), size=OFAT_N_PER_AXIS, replace=False)
    for r in rff_samples:
        rows.append({"axis": "vary_rff", "rff_idx": int(r),
                     "fair_cfg_idx": CFG_0, "seed_idx": SEED_0, "post_idx": POST_0})

    # axis = "vary_cfg"
    cfg_samples = rng.choice(np.arange(0, N_CFG), size=OFAT_N_PER_AXIS, replace=False)
    for c in cfg_samples:
        rows.append({"axis": "vary_cfg", "rff_idx": RFF_0,
                     "fair_cfg_idx": int(c), "seed_idx": SEED_0, "post_idx": POST_0})

    # axis = "vary_seed" -- Phase A only has 10 seeds, use all of them
    for s in range(N_SEED):
        rows.append({"axis": "vary_seed", "rff_idx": RFF_0,
                     "fair_cfg_idx": CFG_0, "seed_idx": s, "post_idx": POST_0})

    # axis = "vary_post"
    post_samples = rng.choice(np.arange(1, N_POST + 1), size=OFAT_N_PER_AXIS, replace=False)
    for p in post_samples:
        rows.append({"axis": "vary_post", "rff_idx": RFF_0,
                     "fair_cfg_idx": CFG_0, "seed_idx": SEED_0, "post_idx": int(p)})

    df = pd.DataFrame(rows, columns=["axis", "rff_idx", "fair_cfg_idx", "seed_idx", "post_idx"])
    out_path = OUT / "ofat_metadata.csv"
    df.to_csv(out_path, index=False)
    print(f"OFAT metadata: {len(df)} rows -> {out_path}")
    print(df.groupby("axis").size())
    return df


# ----------------------------------------------------------------------------
def build_anova():
    rng = np.random.default_rng(ANOVA_RNG_SEED)
    rows = []

    # Random subset of RFFs
    rff_samples = rng.choice(np.arange(1, N_RFF + 1), size=ANOVA_N_RFF, replace=False)

    for r in rff_samples:
        # Different random cfg subset PER RFF — explores cfg space
        cfg_samples = rng.choice(np.arange(0, N_CFG), size=ANOVA_N_CFG_PER_RFF, replace=False)
        for c in cfg_samples:
            # SHARED posts across all seeds within this (rff, cfg) cell. This is
            # required for the nested ANOVA V_internal to be unbiased: if each
            # seed sampled its own 3 posts, the "across-seed" variance of the
            # per-seed mean ΔSLR is dominated by Var_post/3 (the random-post
            # sampling contribution) instead of true seed-state-dependence.
            # Diagnostic on the pre-fix CSV (May 15 2026) showed V_internal in
            # the marginal-SLR decomp was ~100% post-sampling artifact; total-
            # SLR decomp the same. With shared posts the 4-way decomp recovers
            # an orthogonal seed×post factorial within each (rff, cfg) cell.
            post_samples = rng.choice(np.arange(1, N_POST + 1), size=ANOVA_N_POST, replace=False)
            for s in range(ANOVA_N_SEED):
                for p in post_samples:
                    rows.append({"axis": "anova", "rff_idx": int(r),
                                 "fair_cfg_idx": int(c), "seed_idx": s, "post_idx": int(p)})

    df = pd.DataFrame(rows, columns=["axis", "rff_idx", "fair_cfg_idx", "seed_idx", "post_idx"])
    out_path = OUT / "anova_metadata.csv"
    df.to_csv(out_path, index=False)
    print(f"\nANOVA metadata: {len(df)} rows -> {out_path}")
    print(f"  rffs={ANOVA_N_RFF}, cfgs/rff={ANOVA_N_CFG_PER_RFF}, seeds={ANOVA_N_SEED}, posts={ANOVA_N_POST}")
    print(f"  unique rffs={df['rff_idx'].nunique()}, unique cfgs={df['fair_cfg_idx'].nunique()}, "
          f"unique posts={df['post_idx'].nunique()}")
    print(f"  rows per rff: {df.groupby('rff_idx').size().describe()}")
    return df


# ----------------------------------------------------------------------------
def main():
    build_ofat()
    build_anova()


if __name__ == "__main__":
    main()
