"""
hybrid_hs_total_slr.py
======================

Hybrid Hawkins-Sutton decomposition for total ΔSLR (relative to 2020).

The pure-Shapley approach fails for SLR because the HistGradientBoosting
surrogate's R² drops with time (0.96 → 0.71 at 2050 → 2150). The residual
contains BRICK + cfg×post interactions + tipping non-linearity, mis-labeled
as "internal variability" in the v5 figure (which then implausibly grows
with time).

The hybrid fix uses model-free within-cell variance for the two harder
axes (BRICK posterior, FaIR seed noise) and keeps Shapley for the
emissions / climate axes that the surrogate handles well.

Inputs (all should be present locally after the augmentation runs):
  v5 cube + slim weighted:
    fair_outputs/cubes_v145/cube_v145_lhs10ks_baseline_flat2015.npz
    outputs/brick_v145_slim/brick_lhs10ks_baseline_to2300_weighted.csv
  BRICK post-augmentation (10000 cells × 9 extra posts):
    outputs/brick_v145_lhs10ks/brick_lhs10ks_baseline_postaugment.csv
  FaIR seed-augmentation + paired BRICK (200 cells × 9 extra seeds):
    outputs/brick_v145_lhs10ks/brick_lhs10ks_seedaugment.csv
  Augmentation metadata (for cell matching):
    outputs/lhs10ks_brick_metadata.csv               (original v5 BRICK)
    outputs/lhs10ks_brick_postaugment_metadata.csv   (90k augmentation rows)
    outputs/lhs10ks_seedaugment_brick_metadata.csv   (1800 seedaug rows)

Decomposition at each year:
  V_total       — from v5 slim baseline (importance-weighted)
  V_BRICK       — model-free: avg over cells of within-cell variance across
                  10 BRICK posts; uses v5's full 841-cfg / 10000-rff coverage
  V_seed        — model-free: avg over the 200 augmented cells of within-cell
                  variance across 10 seeds (parent + 9 augments)
  V_emi+V_clim  — SHAP variances from per-year surrogate fit (cfg+RFF only)
  V_residual    — V_total - (V_emi + V_clim + V_BRICK + V_seed)
                  Labeled as "BRICK×cfg interactions + tipping non-linearity"

Outputs:
  outputs/substack/shapley_hs_total_slr_hybrid.{png,pdf}
  outputs/substack/shapley_hs_per_axis_total_slr_hybrid.csv
  outputs/substack/v5_hybrid_decomp_diagnostic.csv (year-by-year breakdown)
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Pull the shared constants and helpers
sys.path.insert(0, str(Path(__file__).resolve().parent))
from shapley_hawkins_sutton import (
    KEY_COLS, RFF_FEATURES_LIST as RFF_FEATS, CFG_FEATURES, POST_FEATURES,
    YEAR_LO, YEAR_HI, AXIS_COLOR,
    assemble_features,
)

ROOT = Path("/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK")
FAI  = Path("/Users/MarcusMarcus/Documents/2026/CodeProjects/FaIRtoFrEDI")
OUT  = ROOT / "outputs/substack"

V5_SLIM        = ROOT / "outputs/brick_v145_slim/brick_lhs10ks_baseline_to2300_weighted.csv"
V5_BRICK_META  = ROOT / "outputs/lhs10ks_brick_metadata.csv"
POSTAUG_CSV    = ROOT / "outputs/brick_v145_lhs10ks/brick_lhs10ks_baseline_postaugment.csv"
POSTAUG_META   = ROOT / "outputs/lhs10ks_brick_postaugment_metadata.csv"
SEEDAUG_CSV    = ROOT / "outputs/brick_v145_lhs10ks/brick_lhs10ks_seedaugment.csv"
SEEDAUG_META   = ROOT / "outputs/lhs10ks_seedaugment_brick_metadata.csv"

YEARS = np.arange(YEAR_LO, YEAR_HI + 1)  # 2020..2150
ANCHOR = 2020

# --------------------------------------------------------------------------
# Model-free V_BRICK: average within-cell variance across 10 posts
# --------------------------------------------------------------------------
def compute_v_brick_modelfree():
    """For each v5 cell, gather K=10 BRICK realizations (1 original + 9 aug);
    compute within-cell variance across the 10 posts at each year; average
    across cells weighted by importance weights."""
    print("[V_BRICK modelfree] loading v5 + postaug SLR slr_<y> columns ...")
    year_cols = [f"slr_{y}" for y in YEARS]
    v5 = pd.read_csv(V5_SLIM, usecols=KEY_COLS + ["w_norm"] + [str(y) for y in YEARS])
    # rename bare year cols → slr_<y> for consistency with the augmentation CSVs
    v5 = v5.rename(columns={str(y): f"slr_{y}" for y in YEARS})
    v5["axis"] = "orig"
    aug = pd.read_csv(POSTAUG_CSV, usecols=KEY_COLS + year_cols)
    aug["w_norm"] = np.nan  # postaug rows borrow weight from parent cell
    aug["axis"] = "postaug"
    print(f"  v5 cells: {len(v5)}, postaug rows: {len(aug)}")

    # Merge augmentation rows with parent's w_norm via (rff, cfg, seed)
    parent_w = v5[["rff_idx","fair_cfg_idx","seed_idx","w_norm"]].copy()
    aug = aug.drop(columns=["w_norm"]).merge(parent_w, on=["rff_idx","fair_cfg_idx","seed_idx"], how="left")
    assert aug.w_norm.notna().all(), "postaug rows missing parent weight"

    all_brick = pd.concat([v5, aug], ignore_index=True)
    base = all_brick["slr_2020"].to_numpy()
    delta = all_brick[year_cols].to_numpy() - base[:, None]  # cells × years
    cell_key = list(zip(all_brick.rff_idx, all_brick.fair_cfg_idx, all_brick.seed_idx))
    df = pd.DataFrame(dict(rff_idx=all_brick.rff_idx, fair_cfg_idx=all_brick.fair_cfg_idx,
                            seed_idx=all_brick.seed_idx, w_norm=all_brick.w_norm))
    n_total = len(df)
    df_group_sizes = df.groupby(["rff_idx","fair_cfg_idx","seed_idx"]).size()
    print(f"  per-cell BRICK reps: min={df_group_sizes.min()} max={df_group_sizes.max()} "
          f"mean={df_group_sizes.mean():.1f}  (target: 10)")

    # Within-cell variance per year: groupby on cell key
    # Bias-corrected: multiply by N/(N-1) where N is reps per cell
    print(f"  computing within-cell variance × N/(N-1) per year ...")
    out_v_brick = np.zeros(len(YEARS))
    cells = df.groupby(["rff_idx","fair_cfg_idx","seed_idx"])
    # We need: for each cell, V_within = (1/N) sum (x-mean)² (population var, then * N/(N-1))
    # = sample variance ddof=1. Then take importance-weighted mean across cells.
    grp_keys = list(cells.groups.keys())
    cell_w = np.array([df.iloc[g[0]].w_norm for g in cells.groups.values()])
    cell_w /= cell_w.sum()
    # build per-cell variance arrays vectorized year by year
    for iy in range(len(YEARS)):
        col = delta[:, iy]
        v = cells.apply(lambda idx: np.var(col[idx.index], ddof=1)).to_numpy()
        out_v_brick[iy] = (v * cell_w).sum()
    return YEARS, out_v_brick


# --------------------------------------------------------------------------
# Model-free V_seed: average within-cell variance across 10 seeds
# --------------------------------------------------------------------------
def compute_v_seed_modelfree():
    """Group seedaug cells by (rff, cfg, post_idx) — the augmentation kept
    these fixed and only varied seed. Add the v5 parent cell (1 entry per
    parent), then compute within-cell variance across the 10 seeds."""
    print("[V_seed modelfree] loading seedaug + matched v5 parents ...")
    year_cols = [f"slr_{y}" for y in YEARS]
    seedaug = pd.read_csv(SEEDAUG_CSV, usecols=KEY_COLS + year_cols)
    seedaug["axis"] = "seedaug"
    seedaug_meta = pd.read_csv(SEEDAUG_META)
    print(f"  seedaug rows: {len(seedaug)}")

    # Identify parent cells: distinct (rff, cfg, post) groups in seedaug.
    parent_keys = seedaug_meta[["rff_idx","fair_cfg_idx","post_idx"]].drop_duplicates()
    print(f"  parent groups (rff, cfg, post): {len(parent_keys)}")

    # The parent v5 entry has the SAME (rff, cfg, post) but parent's seed_idx
    # is one of the v5 cells. Pull parent rows from v5 by matching (rff, cfg, post).
    v5 = pd.read_csv(V5_SLIM, usecols=KEY_COLS + ["w_norm"] + [str(y) for y in YEARS])
    v5 = v5.rename(columns={str(y): f"slr_{y}" for y in YEARS})
    parents = v5.merge(parent_keys, on=["rff_idx","fair_cfg_idx","post_idx"], how="inner")
    print(f"  matched parents from v5: {len(parents)}")

    parents["axis"] = "parent"
    all_seed = pd.concat([parents, seedaug.assign(w_norm=np.nan)], ignore_index=True)
    # Tile parent weight onto seedaug
    pw = parents[["rff_idx","fair_cfg_idx","post_idx","w_norm"]].rename(columns={"w_norm":"w_norm_p"})
    all_seed = all_seed.merge(pw, on=["rff_idx","fair_cfg_idx","post_idx"], how="left")
    all_seed["w_norm"] = all_seed["w_norm"].fillna(all_seed["w_norm_p"])
    all_seed = all_seed.drop(columns=["w_norm_p"])
    assert all_seed["w_norm"].notna().all()

    base = all_seed["slr_2020"].to_numpy()
    delta = all_seed[year_cols].to_numpy() - base[:, None]
    grp = all_seed.groupby(["rff_idx","fair_cfg_idx","post_idx"])
    sizes = grp.size()
    print(f"  per-(rff,cfg,post) reps: min={sizes.min()} max={sizes.max()} mean={sizes.mean():.1f} (target: 10)")

    cell_w = np.array([all_seed.iloc[g[0]].w_norm for g in grp.groups.values()])
    cell_w /= cell_w.sum()
    out_v_seed = np.zeros(len(YEARS))
    for iy in range(len(YEARS)):
        col = delta[:, iy]
        v = grp.apply(lambda idx: np.var(col[idx.index], ddof=1)).to_numpy()
        out_v_seed[iy] = (v * cell_w).sum()
    return YEARS, out_v_seed


# --------------------------------------------------------------------------
# Shapley V_emi + V_climate (cfg+RFF features ONLY; no post features)
# --------------------------------------------------------------------------
def compute_v_emi_clim_shap(years):
    """Per-year HistGB surrogate on cfg + RFF features (NO post features).
    SHAP variance summed by axis."""
    from sklearn.ensemble import HistGradientBoostingRegressor
    import shap

    print("[V_emi/V_clim Shapley] loading slim + features ...")
    feat = assemble_features()  # 10000 cells × features
    X = feat[RFF_FEATS + CFG_FEATURES].to_numpy(dtype=np.float64)
    w = feat["w_norm"].to_numpy(dtype=np.float64)

    # Load SLR target trajectory from v5 slim
    slim = pd.read_csv(V5_SLIM, usecols=KEY_COLS + [str(y) for y in years])
    slim = slim.merge(feat[KEY_COLS], on=KEY_COLS).sort_values(KEY_COLS).reset_index(drop=True)
    base = slim["2020"].to_numpy()
    M = slim[[str(y) for y in years]].to_numpy() - base[:, None]

    v_emi = np.zeros(len(years))
    v_clim = np.zeros(len(years))
    v_total = np.zeros(len(years))
    n_rff = len(RFF_FEATS)
    n_cfg = len(CFG_FEATURES)
    print(f"  fitting {len(years)} per-year surrogates (cfg+RFF only, {n_rff+n_cfg} features) ...")
    import time
    t0 = time.time()
    for it in range(len(years)):
        y_target = M[:, it]
        m = HistGradientBoostingRegressor(max_iter=200, max_leaf_nodes=15, learning_rate=0.05,
                                           min_samples_leaf=30, l2_regularization=1.0,
                                           random_state=2026)
        m.fit(X, y_target, sample_weight=w)
        explainer = shap.TreeExplainer(m)
        sh = explainer.shap_values(X)
        wsum = w.sum()
        mu_y = (y_target * w).sum() / wsum
        v_total[it] = ((y_target - mu_y) ** 2 * w).sum() / wsum
        mu_sh = (sh * w[:, None]).sum(axis=0) / wsum
        sh_var = ((sh - mu_sh) ** 2 * w[:, None]).sum(axis=0) / wsum
        v_emi[it]  = sh_var[:n_rff].sum()
        v_clim[it] = sh_var[n_rff:n_rff+n_cfg].sum()
        if (it+1) % 20 == 0 or it == 0 or it == len(years)-1:
            print(f"    year {years[it]}: V_emi={v_emi[it]:.2f}  V_clim={v_clim[it]:.2f}  "
                  f"V_total={v_total[it]:.2f}  [{time.time()-t0:.0f}s]")
    return v_emi, v_clim, v_total


def main():
    years, v_brick = compute_v_brick_modelfree()
    _, v_seed = compute_v_seed_modelfree()
    v_emi, v_clim, v_total = compute_v_emi_clim_shap(years)

    sum_attr = v_emi + v_clim + v_brick + v_seed
    v_resid = np.maximum(v_total - sum_attr, 0.0)  # interactions + tipping nonlinearity

    df = pd.DataFrame(dict(
        year=years, V_total=v_total,
        V_emissions=v_emi, V_climate=v_clim,
        V_BRICK_modelfree=v_brick, V_seed_modelfree=v_seed,
        V_residual_interactions=v_resid,
    ))
    df.to_csv(OUT / "v5_hybrid_decomp_diagnostic.csv", index=False)
    print(f"\nwrote {OUT}/v5_hybrid_decomp_diagnostic.csv")

    # Per-axis fractions
    denom = v_emi + v_clim + v_brick + v_seed + v_resid
    frac = pd.DataFrame(dict(
        year=years,
        internal=v_seed/denom,
        brick=v_brick/denom,
        climate=v_clim/denom,
        emissions=v_emi/denom,
        residual=v_resid/denom,
    ))
    frac.to_csv(OUT / "shapley_hs_per_axis_total_slr_hybrid.csv", index=False)

    print("\nFractions at landmark years:")
    for y in [2025, 2050, 2100, 2150]:
        if y not in frac.year.values: continue
        r = frac[frac.year == y].iloc[0]
        print(f"  {y}: internal={r.internal:.3f}  brick={r.brick:.3f}  "
              f"climate={r.climate:.3f}  emissions={r.emissions:.3f}  "
              f"residual={r.residual:.3f}")

    # Render
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ax_cols = ["internal", "brick", "climate", "emissions", "residual"]
    labels = {
        "internal":  "Internal variability (FaIR seed; model-free)",
        "brick":     "BRICK posterior (model-free)",
        "climate":   "Climate response (FaIR cfg; SHAP)",
        "emissions": "Emissions (RFF-SP; SHAP)",
        "residual":  "Unattributed (cfg×post interactions + tipping nonlinearity)",
    }
    colors = {**AXIS_COLOR, "residual": "#999999"}

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.stackplot(years, *[frac[c].to_numpy() for c in ax_cols],
                  labels=[labels[c] for c in ax_cols],
                  colors=[colors[c] for c in ax_cols],
                  alpha=0.88, edgecolor="white", linewidth=0.4)
    ax.set_xlim(years.min(), years.max())
    ax.set_ylim(0, 1)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("Fraction of ΔSLR variance", fontsize=11)
    ax.set_title("Total ΔSLR (relative to 2020) — hybrid decomposition\n"
                  "V_seed/V_BRICK from augmentation runs (model-free); "
                  "V_emi/V_climate from Shapley TreeExplainer (cfg+RFF only)",
                  fontsize=12, fontweight="bold", color="#1F4E79")
    h_, l_ = ax.get_legend_handles_labels()
    ax.legend(h_[::-1], l_[::-1], loc="center right", fontsize=9.5, framealpha=0.92)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "shapley_hs_total_slr_hybrid.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / "shapley_hs_total_slr_hybrid.pdf", bbox_inches="tight")
    print(f"wrote {OUT}/shapley_hs_total_slr_hybrid.{{png,pdf}}")


if __name__ == "__main__":
    main()
