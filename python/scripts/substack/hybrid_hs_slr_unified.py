"""
hybrid_hs_slr_unified.py
========================

Unified hybrid Hawkins-Sutton decomposition for SLR (total + pulse) with an
optional tipping-vs-interactions split via p99 clipping.

For each (target, clip) combination, computes:
  V_total          — variance across cells of cell-level metric
  V_seed_modelfree — within-(rff,cfg,post) variance across 10 seeds (200 cells
                     × 10 seeds via seedaug). PULSE: 0 by matched-seed.
  V_BRICK_modelfree — within-cell variance across 10 BRICK posts (10000 cells
                     × 10 posts via postaug)
  V_emi, V_clim    — SHAP TreeExplainer attribution on per-year surrogate
                     (cfg + RFF features only)
  V_residual       — V_total minus the four attributed axes

Tipping vs interactions split:
  Run unclipped + p99-clipped versions. The residual difference between them
  is variance lost to tipping nonlinearity (cells with extreme AIS tipping).
  Split residual into:
    V_tipping = V_residual_unclipped - V_residual_clipped
    V_interactions = V_residual_clipped

Outputs (per target):
  outputs/substack/v5_hybrid_<target>_decomp.csv  (year-by-year absolute vars)
  outputs/substack/shapley_hs_<target>_hybrid_tipping_split.{png,pdf}
"""
from __future__ import annotations
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shapley_hawkins_sutton import (
    KEY_COLS, RFF_FEATURES_LIST as RFF_FEATS, CFG_FEATURES,
    YEAR_LO, YEAR_HI, AXIS_COLOR, assemble_features,
)

ROOT = Path("/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK")
FAI  = Path("/Users/MarcusMarcus/Documents/2026/CodeProjects/FaIRtoFrEDI")
OUT  = ROOT / "outputs/substack"

V5_SLIM_BASE  = ROOT / "outputs/brick_v145_slim/brick_lhs10ks_baseline_to2300_weighted.csv"
V5_SLIM_PULSE = ROOT / "outputs/brick_v145_slim/brick_lhs10ks_pulse_co2_pos_001gt_to2300.csv"
POSTAUG_BASE  = ROOT / "outputs/brick_v145_lhs10ks/brick_lhs10ks_baseline_postaugment.csv"
POSTAUG_PULSE = ROOT / "outputs/brick_v145_lhs10ks/brick_lhs10ks_pulse_co2_pos_001gt_postaugment.csv"
SEEDAUG_BASE  = ROOT / "outputs/brick_v145_lhs10ks/brick_lhs10ks_seedaugment.csv"
SEEDAUG_META  = ROOT / "outputs/lhs10ks_seedaugment_brick_metadata.csv"

YEARS = np.arange(YEAR_LO, YEAR_HI + 1)
ANCHOR = 2020
PULSE_SIZE_GTCO2 = 0.01


# --------------------------------------------------------------------------
# Loaders
# --------------------------------------------------------------------------
def load_baseline_v5():
    """Returns (cells_df, slr_array shape (n_cells, n_yr))."""
    year_cols = [str(y) for y in YEARS]
    df = pd.read_csv(V5_SLIM_BASE, usecols=KEY_COLS + ["w_norm"] + year_cols)
    df = df.sort_values(KEY_COLS).reset_index(drop=True)
    slr = df[year_cols].to_numpy()  # cells × yr
    return df, slr


def load_pulse_v5():
    year_cols = [str(y) for y in YEARS]
    df = pd.read_csv(V5_SLIM_PULSE, usecols=KEY_COLS + year_cols)
    df = df.sort_values(KEY_COLS).reset_index(drop=True)
    slr = df[year_cols].to_numpy()
    return df, slr


def load_postaug(csv_path):
    """Returns dataframe with (key cols + slr_<y>) sorted by key."""
    year_cols = [f"slr_{y}" for y in YEARS]
    df = pd.read_csv(csv_path, usecols=KEY_COLS + year_cols)
    df = df.sort_values(KEY_COLS).reset_index(drop=True)
    return df


# --------------------------------------------------------------------------
# Model-free V_BRICK for total OR pulse marginal
# --------------------------------------------------------------------------
def compute_v_brick_total(v5_base, slr_base_v5, postaug_base, clip_p99=False):
    """Within-cell variance across 10 baseline posts at each year, weighted
    mean across cells. When clip_p99=True, clip per-year deltas across all
    100,000 baseline cells at year-specific p99 before per-cell variance."""
    year_cols = [f"slr_{y}" for y in YEARS]
    v5_stacked = v5_base[KEY_COLS].copy()
    v5_stacked[year_cols] = slr_base_v5 - slr_base_v5[:, [int(np.where(YEARS == ANCHOR)[0][0])]]
    aug_anchor = postaug_base[f"slr_{ANCHOR}"].to_numpy()
    aug_delta = postaug_base[year_cols].to_numpy() - aug_anchor[:, None]
    aug_stacked = postaug_base[KEY_COLS].copy()
    aug_stacked[year_cols] = aug_delta
    all_base = pd.concat([v5_stacked, aug_stacked], ignore_index=True)

    arr = all_base[year_cols].to_numpy()
    if clip_p99:
        caps = np.percentile(arr, 99.0, axis=0)
        arr = np.minimum(arr, caps[None, :])

    cells = all_base.groupby(["rff_idx","fair_cfg_idx","seed_idx"])
    sizes = cells.size()
    print(f"  [V_BRICK_total] cells: {len(sizes)}  reps/cell min/max: {sizes.min()}/{sizes.max()}  "
          f"clip_p99={clip_p99}")
    w_by_cell = v5_base.set_index(["rff_idx","fair_cfg_idx","seed_idx"])["w_norm"].to_dict()
    out = np.zeros(len(YEARS))
    grp_keys = list(cells.groups.keys())
    cell_w = np.array([w_by_cell[k] for k in grp_keys])
    cell_w /= cell_w.sum()

    for iy in range(len(YEARS)):
        col = arr[:, iy]
        v = cells.apply(lambda idx: np.var(col[idx.index], ddof=1)).to_numpy()
        out[iy] = (v * cell_w).sum()
    return out


def compute_v_brick_pulse(v5_base, slr_base_v5, v5_pulse, slr_pulse_v5,
                            postaug_base, postaug_pulse, clip_p99=False):
    """Per-cell marginal across 10 BRICK posts: marg = (slr_pulse - slr_base) /
    pulse_size. Within-cell variance across 10 posts at each year, weighted
    mean across cells.

    clip_p99: when True, clip per-year marginals across ALL 100000 cells (v5 +
    postaug) at the year-specific 99th percentile BEFORE computing per-cell
    variance. Suppresses AIS tipping outliers — same convention as the original
    pulse_slr figure (which clips total_slr_pulse_marginal at p99). Critical
    here because BRICK posterior members combined with extreme cfgs can push
    the pulse marginal past the AIS tipping threshold, producing per-cell
    variances of O(1e+3) (cm/GtCO2)² in long-tail cells — utterly dominating
    the mean over cells and rendering V_BRICK_pulse uninterpretable."""
    year_cols = [f"slr_{y}" for y in YEARS]
    i_anchor = int(np.where(YEARS == ANCHOR)[0][0])
    base_v5_delta = slr_base_v5 - slr_base_v5[:, [i_anchor]]
    pulse_v5_delta = slr_pulse_v5 - slr_pulse_v5[:, [i_anchor]]
    marg_v5 = (pulse_v5_delta - base_v5_delta) / PULSE_SIZE_GTCO2  # cells × yr

    aug_base_anchor = postaug_base[f"slr_{ANCHOR}"].to_numpy()
    aug_base_delta = postaug_base[year_cols].to_numpy() - aug_base_anchor[:, None]
    aug_pulse_anchor = postaug_pulse[f"slr_{ANCHOR}"].to_numpy()
    aug_pulse_delta = postaug_pulse[year_cols].to_numpy() - aug_pulse_anchor[:, None]
    assert (postaug_base[KEY_COLS].to_numpy() == postaug_pulse[KEY_COLS].to_numpy()).all(), \
        "postaug base and pulse metadata rows mis-aligned"
    marg_aug = (aug_pulse_delta - aug_base_delta) / PULSE_SIZE_GTCO2

    keys_v5 = v5_base[KEY_COLS].copy()
    keys_aug = postaug_base[KEY_COLS].copy()
    all_keys = pd.concat([keys_v5, keys_aug], ignore_index=True)
    all_marg = np.vstack([marg_v5, marg_aug])

    if clip_p99:
        caps = np.percentile(all_marg, 99.0, axis=0)  # per-year p99 across all 100k
        all_marg = np.minimum(all_marg, caps[None, :])

    cells = all_keys.groupby(["rff_idx","fair_cfg_idx","seed_idx"])
    sizes = cells.size()
    print(f"  [V_BRICK_pulse] cells: {len(sizes)}  reps/cell min/max: {sizes.min()}/{sizes.max()}  "
          f"clip_p99={clip_p99}")

    w_by_cell = v5_base.set_index(["rff_idx","fair_cfg_idx","seed_idx"])["w_norm"].to_dict()
    grp_keys = list(cells.groups.keys())
    cell_w = np.array([w_by_cell[k] for k in grp_keys])
    cell_w /= cell_w.sum()

    out = np.zeros(len(YEARS))
    for iy in range(len(YEARS)):
        col = all_marg[:, iy]
        v = cells.apply(lambda idx: np.var(col[idx.index], ddof=1)).to_numpy()
        out[iy] = (v * cell_w).sum()
    return out


# --------------------------------------------------------------------------
# Model-free V_seed (total only; pulse = 0)
# --------------------------------------------------------------------------
def compute_v_seed_total(v5_base, slr_base_v5):
    print("[V_seed total] loading seedaug ...")
    year_cols = [f"slr_{y}" for y in YEARS]
    seedaug = pd.read_csv(SEEDAUG_BASE, usecols=KEY_COLS + year_cols)
    seedaug_meta = pd.read_csv(SEEDAUG_META)
    parent_keys = seedaug_meta[["rff_idx","fair_cfg_idx","post_idx"]].drop_duplicates()

    parents = v5_base.merge(parent_keys, on=["rff_idx","fair_cfg_idx","post_idx"], how="inner").reset_index(drop=True)
    # parents has the 200 v5 cells matching parent_keys
    print(f"  matched parents: {len(parents)}")
    # delta from anchor
    i_anchor = int(np.where(YEARS == ANCHOR)[0][0])
    year_cols_str = [str(y) for y in YEARS]
    parents_delta_arr = parents[year_cols_str].to_numpy() - parents[str(ANCHOR)].to_numpy()[:, None]
    parents_delta = parents[KEY_COLS].copy()
    parents_delta[year_cols] = parents_delta_arr
    seedaug_anchor = seedaug[f"slr_{ANCHOR}"].to_numpy()
    seedaug_delta = seedaug.copy()
    seedaug_delta[year_cols] = seedaug[year_cols].to_numpy() - seedaug_anchor[:, None]

    all_seed = pd.concat([parents_delta, seedaug_delta[KEY_COLS + year_cols]], ignore_index=True)
    grp = all_seed.groupby(["rff_idx","fair_cfg_idx","post_idx"])
    sizes = grp.size()
    print(f"  reps/(rff,cfg,post) min/max: {sizes.min()}/{sizes.max()}")

    # Parent weight per group
    w_lut = parents.set_index(["rff_idx","fair_cfg_idx","post_idx"])["w_norm"].to_dict()
    grp_keys = list(grp.groups.keys())
    cell_w = np.array([w_lut[k] for k in grp_keys])
    cell_w /= cell_w.sum()
    arr = all_seed[year_cols].to_numpy()
    out = np.zeros(len(YEARS))
    for iy in range(len(YEARS)):
        col = arr[:, iy]
        v = grp.apply(lambda idx: np.var(col[idx.index], ddof=1)).to_numpy()
        out[iy] = (v * cell_w).sum()
    return out


# --------------------------------------------------------------------------
# SHAP V_emi + V_clim on (cfg + RFF) features
# --------------------------------------------------------------------------
def compute_v_emi_clim_shap_on_target(target_per_cell, w_cell):
    """target_per_cell shape (n_cells, n_yr); fits per-year HistGB on
    cfg+RFF features, returns (v_emi, v_clim, v_total) per year."""
    from sklearn.ensemble import HistGradientBoostingRegressor
    import shap

    feat = assemble_features()
    assert len(feat) == target_per_cell.shape[0], (len(feat), target_per_cell.shape)
    X = feat[RFF_FEATS + CFG_FEATURES].to_numpy(dtype=np.float64)
    n_rff = len(RFF_FEATS)
    n_cfg = len(CFG_FEATURES)
    n_yr = target_per_cell.shape[1]

    v_emi = np.zeros(n_yr); v_clim = np.zeros(n_yr); v_total = np.zeros(n_yr)
    t0 = time.time()
    for it in range(n_yr):
        y_target = target_per_cell[:, it]
        if y_target.std() < 1e-20:
            continue
        m = HistGradientBoostingRegressor(max_iter=200, max_leaf_nodes=15, learning_rate=0.05,
                                           min_samples_leaf=30, l2_regularization=1.0, random_state=2026)
        m.fit(X, y_target, sample_weight=w_cell)
        explainer = shap.TreeExplainer(m)
        sh = explainer.shap_values(X)
        wsum = w_cell.sum()
        mu_y = (y_target * w_cell).sum() / wsum
        v_total[it] = ((y_target - mu_y) ** 2 * w_cell).sum() / wsum
        mu_sh = (sh * w_cell[:, None]).sum(axis=0) / wsum
        sh_var = ((sh - mu_sh) ** 2 * w_cell[:, None]).sum(axis=0) / wsum
        v_emi[it]  = sh_var[:n_rff].sum()
        v_clim[it] = sh_var[n_rff:n_rff+n_cfg].sum()
        if (it+1) % 30 == 0 or it == n_yr - 1:
            print(f"    year {YEARS[it]}: V_total={v_total[it]:.3g} V_emi={v_emi[it]:.3g} "
                  f"V_clim={v_clim[it]:.3g}  [{time.time()-t0:.0f}s]")
    return v_emi, v_clim, v_total


# --------------------------------------------------------------------------
# p99 clipping helper
# --------------------------------------------------------------------------
def clip_per_year(arr, q=99.0):
    """Clip each year column to its q-th percentile across cells."""
    out = arr.copy()
    for iy in range(arr.shape[1]):
        cap = np.percentile(arr[:, iy], q)
        out[:, iy] = np.minimum(arr[:, iy], cap)
    return out


# --------------------------------------------------------------------------
# Full hybrid pipeline for one target
# --------------------------------------------------------------------------
def hybrid_for_target(target_name, clip_p99=False):
    """target_name: 'total' or 'pulse'. Returns dataframe with per-year variances."""
    print(f"\n=== HYBRID {target_name.upper()} {'(p99 clipped)' if clip_p99 else '(unclipped)'} ===")

    v5_base, slr_base_v5 = load_baseline_v5()
    i_anchor = int(np.where(YEARS == ANCHOR)[0][0])

    if target_name == "total":
        target = slr_base_v5 - slr_base_v5[:, [i_anchor]]
    elif target_name == "pulse":
        v5_pulse, slr_pulse_v5 = load_pulse_v5()
        assert (v5_base[KEY_COLS].to_numpy() == v5_pulse[KEY_COLS].to_numpy()).all()
        target = ((slr_pulse_v5 - slr_pulse_v5[:, [i_anchor]]) -
                   (slr_base_v5 - slr_base_v5[:, [i_anchor]])) / PULSE_SIZE_GTCO2
    else:
        raise ValueError(target_name)

    if clip_p99:
        target = clip_per_year(target, q=99.0)

    w = v5_base["w_norm"].to_numpy(dtype=np.float64)

    # Model-free V_BRICK (pass clip flag through so per-year p99 cap is
    # applied consistently to the augmentation cells)
    print(f"  computing V_BRICK_modelfree ({target_name}, "
          f"{'clipped' if clip_p99 else 'unclipped'}) ...")
    postaug_base  = load_postaug(POSTAUG_BASE)
    if target_name == "total":
        v_brick = compute_v_brick_total(v5_base, slr_base_v5, postaug_base, clip_p99=clip_p99)
    else:
        postaug_pulse = load_postaug(POSTAUG_PULSE)
        v_brick = compute_v_brick_pulse(v5_base, slr_base_v5, v5_pulse, slr_pulse_v5,
                                          postaug_base, postaug_pulse, clip_p99=clip_p99)

    # Model-free V_seed (total only)
    if target_name == "total":
        v_seed = compute_v_seed_total(v5_base, slr_base_v5)
    else:
        v_seed = np.zeros(len(YEARS))  # matched-seed cancellation

    # SHAP V_emi + V_clim
    print(f"  computing V_emi + V_clim via SHAP ({target_name}, "
          f"{'clipped' if clip_p99 else 'unclipped'}) ...")
    v_emi, v_clim, v_total = compute_v_emi_clim_shap_on_target(target, w)

    v_residual = np.maximum(v_total - (v_emi + v_clim + v_brick + v_seed), 0.0)
    df = pd.DataFrame(dict(
        year=YEARS, V_total=v_total,
        V_emissions=v_emi, V_climate=v_clim,
        V_BRICK_modelfree=v_brick, V_seed_modelfree=v_seed,
        V_residual=v_residual,
    ))
    return df


def main():
    out_csvs = {}
    for target_name in ["total", "pulse"]:
        for clip in [False, True]:
            df = hybrid_for_target(target_name, clip_p99=clip)
            tag = f"{target_name}_{'clip' if clip else 'unclip'}"
            csv = OUT / f"v5_hybrid_decomp_{tag}.csv"
            df.to_csv(csv, index=False)
            out_csvs[tag] = csv
            print(f"  wrote {csv}")
    print("\nALL DECOMPOSITIONS DONE — render with render_hybrid_tipping_split.py")


if __name__ == "__main__":
    main()
