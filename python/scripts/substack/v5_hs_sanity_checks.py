"""
v5 Hawkins-Sutton sanity checks (2026-05-27, response to Marcus's pushback).

Three checks:
  A. total_gmst 5-95 range share (Marcus's specific ask)
      Re-fit emi-only / cfg-only / full surrogates at landmark years; report
      range_int / (range_int + range_emi + range_clim).
  B. total_slr ANOVA-18k V_internal cross-check (model-free reality check)
      Mean within-(rff,cfg) variance across 3 seed replicates → V_internal_anova.
      Compare to v5 surrogate residual at landmark years.
  C. total_slr surrogate capacity test
      Refit total_slr surrogate with 1000 iter / 63 leaves / lower regularization
      at landmark years. If V_residual drops, modeling gap; if unchanged, real.

All on landmark years 2050, 2100, 2150 to keep runtime under a minute total.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path("/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK")
FAI  = Path("/Users/MarcusMarcus/Documents/2026/CodeProjects/FaIRtoFrEDI")

CUBE_BASE_V5    = FAI / "fair_outputs/cubes_v145/cube_v145_lhs10ks_baseline_flat2015.npz"
CUBE_BASE_ANOVA = FAI / "fair_outputs/cubes_v145/cube_v145_anova18k_baseline.npz"
BRICK_LHS10KS   = ROOT / "outputs/brick_v145_lhs10ks/brick_lhs10ks_baseline.csv"
BRICK_ANOVA18K  = ROOT / "outputs/brick_v145/brick_anova18k_baseline.csv"
SLIM_BASE       = ROOT / "outputs/brick_v145_slim/brick_lhs10ks_baseline_to2300_weighted.csv"
RFF_FEATURES    = ROOT / "outputs/rff_summary_features.csv"
CFG_PARAMS      = FAI / "calibration_v145/calibrated_constrained_parameters_1.4.5.csv"
POST_PARAMS     = ROOT / "data/MimiBRICK/parameters_subsample_brick.csv"

LANDMARKS = [2050, 2100, 2150]
ANCHOR_YEAR = 2020

# Feature lists (mirror shapley_hawkins_sutton.py)
CFG_FEATURES = [
    "forcing_4co2",
    "ocean_heat_capacity[0]", "ocean_heat_capacity[1]", "ocean_heat_capacity[2]",
    "ocean_heat_transfer[0]", "ocean_heat_transfer[1]", "ocean_heat_transfer[2]",
    "deep_ocean_efficacy",
    "iirf_0[CO2]", "iirf_uptake[CO2]", "iirf_temperature[CO2]", "iirf_airborne[CO2]",
    "erfari_radiative_efficiency[BC]", "erfari_radiative_efficiency[OC]",
    "erfari_radiative_efficiency[Sulfur]", "erfari_radiative_efficiency[NOx]",
    "erfari_radiative_efficiency[VOC]", "erfari_radiative_efficiency[NH3]",
    "aci_shape[Sulfur]", "aci_shape[BC]", "aci_shape[OC]", "aci_scale",
    "forcing_scale[CH4]", "forcing_scale[N2O]",
    "sigma_eta", "sigma_xi",
]
POST_FEATURES = [
    "thermal_alpha", "thermal_s0",
    "glaciers_beta0", "glaciers_v0", "glaciers_s0", "glaciers_n",
    "greenland_a", "greenland_b", "greenland_alpha", "greenland_beta", "greenland_v0",
    "antarctic_alpha", "antarctic_gamma", "antarctic_mu", "antarctic_nu",
    "antarctic_kappa", "antarctic_precip0", "antarctic_flow0",
    "antarctic_temp_threshold", "anto_alpha", "anto_beta",
]
RFF_FEATS = ["cum_co2_2030", "cum_co2_2100", "cum_co2_2300",
             "peak_co2_emissions", "peak_co2_year",
             "slope_co2_2050_2100", "frac_negative_post_2050",
             "cum_ch4_2100"]
KEY_COLS = ["rff_idx", "fair_cfg_idx", "seed_idx", "post_idx"]


def load_v5_gmst_features():
    """Return DataFrame indexed by row, columns = features + GMST(t) for landmarks."""
    # Cube
    c = np.load(CUBE_BASE_V5, allow_pickle=True)
    cm = np.asarray(c["cells_meta"], dtype=np.int64)
    yrs = np.asarray(c["years"], dtype=np.int64)
    gmst = np.asarray(c["gmst_traj"], dtype=np.float64)
    i_anc = int(np.where(yrs == ANCHOR_YEAR)[0][0])
    dT = {y: gmst[:, int(np.where(yrs == y)[0][0])] - gmst[:, i_anc] for y in LANDMARKS}
    # Slim CSV for keys + weight
    slim = pd.read_csv(SLIM_BASE, usecols=KEY_COLS + ["w_norm"])
    keys = slim.sort_values(KEY_COLS).reset_index(drop=True)
    # Cube key order may differ; merge.
    cube_keys = pd.DataFrame(cm[:, :3], columns=["rff_idx", "fair_cfg_idx", "seed_idx"])
    cube_keys["_cube_row"] = np.arange(len(cube_keys))
    merged = keys.merge(cube_keys, on=["rff_idx", "fair_cfg_idx", "seed_idx"], how="left")
    assert merged["_cube_row"].notna().all()
    perm = merged["_cube_row"].to_numpy(dtype=int)
    # Features
    rff = pd.read_csv(RFF_FEATURES, usecols=["rff_idx"] + RFF_FEATS)
    cfg = pd.read_csv(CFG_PARAMS).reset_index().rename(columns={"index": "fair_cfg_idx"})
    cfg = cfg[["fair_cfg_idx"] + CFG_FEATURES]
    df = keys.merge(rff, on="rff_idx").merge(cfg, on="fair_cfg_idx")
    for y in LANDMARKS:
        df[f"y_{y}"] = dT[y][perm]
    return df


def fit_partial(df, feat_cols, target_col, w_col="w_norm"):
    """Fit a HistGradientBoosting on `feat_cols` to predict `target_col`.
    Return predicted values for all rows (full-data refit)."""
    from sklearn.ensemble import HistGradientBoostingRegressor
    X = df[feat_cols].to_numpy(dtype=np.float64)
    y = df[target_col].to_numpy(dtype=np.float64)
    w = df[w_col].to_numpy(dtype=np.float64)
    m = HistGradientBoostingRegressor(max_iter=200, max_leaf_nodes=15,
                                       learning_rate=0.05, min_samples_leaf=30,
                                       l2_regularization=1.0, random_state=2026)
    m.fit(X, y, sample_weight=w)
    return m.predict(X)


def fit_capacity_test(df, feat_cols, target_col, w_col="w_norm"):
    """Higher-capacity refit for Test B."""
    from sklearn.ensemble import HistGradientBoostingRegressor
    X = df[feat_cols].to_numpy(dtype=np.float64)
    y = df[target_col].to_numpy(dtype=np.float64)
    w = df[w_col].to_numpy(dtype=np.float64)
    m = HistGradientBoostingRegressor(max_iter=1000, max_leaf_nodes=63,
                                       learning_rate=0.03, min_samples_leaf=10,
                                       l2_regularization=0.1, random_state=2026)
    m.fit(X, y, sample_weight=w)
    yhat = m.predict(X)
    # OOF via 5-fold to be honest (not in-sample)
    from sklearn.model_selection import KFold
    kf = KFold(n_splits=5, shuffle=True, random_state=2026)
    yhat_oof = np.zeros_like(y)
    for tr, te in kf.split(X):
        m2 = HistGradientBoostingRegressor(max_iter=1000, max_leaf_nodes=63,
                                            learning_rate=0.03, min_samples_leaf=10,
                                            l2_regularization=0.1, random_state=2026)
        m2.fit(X[tr], y[tr], sample_weight=w[tr])
        yhat_oof[te] = m2.predict(X[te])
    return yhat, yhat_oof


def weighted_quantile(values, q, w):
    """Lower-tail weighted quantile."""
    order = np.argsort(values)
    v = values[order]; wo = w[order]
    cum = np.cumsum(wo) / wo.sum()
    return np.interp(q, cum, v)


def weighted_var(y, w):
    mu = (y * w).sum() / w.sum()
    return ((y - mu) ** 2 * w).sum() / w.sum()


# ----------------------------------------------------------------------
# Check A — total_gmst 5-95 range share
# ----------------------------------------------------------------------
def check_A_total_gmst_range_share():
    print("=" * 70)
    print("CHECK A — total_gmst 5-95 range share (Marcus's ask)")
    print("=" * 70)
    df = load_v5_gmst_features()
    w = df["w_norm"].to_numpy()
    print(f"  n_cells = {len(df)}, sum_w = {w.sum():.2f}")

    rows = []
    for y in LANDMARKS:
        tcol = f"y_{y}"
        target = df[tcol].to_numpy()

        # Full surrogate (emi + cfg)
        yhat_full = fit_partial(df, RFF_FEATS + CFG_FEATURES, tcol)
        residual  = target - yhat_full

        # Emi-only
        yhat_emi = fit_partial(df, RFF_FEATS, tcol)

        # Cfg-only
        yhat_cfg = fit_partial(df, CFG_FEATURES, tcol)

        # Weighted 5-95 ranges
        def rng(z):
            return weighted_quantile(z, 0.95, w) - weighted_quantile(z, 0.05, w)

        r_tot = rng(target)
        r_int = rng(residual)
        r_emi = rng(yhat_emi - yhat_emi.mean())   # demean so it's a range of "contribution"
        r_cfg = rng(yhat_cfg - yhat_cfg.mean())

        # Marcus's specific ratio
        share = r_int / (r_int + r_emi + r_cfg)

        # Variance fractions for comparison
        v_tot = weighted_var(target, w)
        v_int = weighted_var(residual, w)
        v_emi = weighted_var(yhat_emi, w)
        v_cfg = weighted_var(yhat_cfg, w)
        sum_v = v_int + v_emi + v_cfg
        var_frac_int = v_int / sum_v

        rows.append(dict(year=y, range_total=r_tot, range_emi=r_emi,
                          range_cfg=r_cfg, range_int=r_int,
                          range_share_int=share, var_frac_int=var_frac_int,
                          v_total=v_tot, v_internal=v_int, v_emi=v_emi, v_cfg=v_cfg))
        print(f"\n  year {y}:")
        print(f"    5-95 range total = {r_tot:.4f} K")
        print(f"    5-95 range emi   = {r_emi:.4f} K  (var={v_emi:.4f})")
        print(f"    5-95 range cfg   = {r_cfg:.4f} K  (var={v_cfg:.4f})")
        print(f"    5-95 range int   = {r_int:.4f} K  (var={v_int:.4f})")
        print(f"    range_int / sum_ranges    = {share*100:5.2f}%  (Marcus's ask)")
        print(f"    var_int / sum_vars        = {var_frac_int*100:5.2f}%  (matches Shapley fraction)")
    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "outputs/substack/v5_hs_sanity_A_total_gmst_range_share.csv", index=False)
    print(f"\n  wrote {ROOT / 'outputs/substack/v5_hs_sanity_A_total_gmst_range_share.csv'}")
    return out


# ----------------------------------------------------------------------
# Check B — ANOVA-18k V_internal cross-check for total_slr
# ----------------------------------------------------------------------
def check_B_anova18k_vinternal_for_slr():
    print("\n" + "=" * 70)
    print("CHECK B — ANOVA-18k V_internal cross-check for total_slr")
    print("=" * 70)
    if not BRICK_ANOVA18K.exists():
        print(f"  ANOVA-18k BRICK CSV not present at {BRICK_ANOVA18K} — skipping")
        return None
    # Columns we need: keys + slr_<y> for landmarks (relative to 2020)
    landmark_cols = [f"slr_{y}" for y in [ANCHOR_YEAR] + LANDMARKS]
    print(f"  loading ANOVA-18k BRICK CSV (will take ~30 sec; 2.5 GB)...", flush=True)
    df = pd.read_csv(BRICK_ANOVA18K, usecols=KEY_COLS + landmark_cols)
    print(f"  loaded {len(df):,} rows", flush=True)
    print(f"  seeds per (rff, cfg): {df.groupby(['rff_idx','fair_cfg_idx']).size().describe()}")

    base = df[f"slr_{ANCHOR_YEAR}"]
    for y in LANDMARKS:
        df[f"dslr_{y}"] = df[f"slr_{y}"] - base

    # Group by (rff, cfg) → within-bin variance across seeds; mean = V_internal.
    # Bins with <2 seeds get NaN and are dropped.
    rows = []
    for y in LANDMARKS:
        col = f"dslr_{y}"
        grp = df.groupby(["rff_idx", "fair_cfg_idx"])[col]
        within_var = grp.var(ddof=0)               # population var per group
        n_per_grp = grp.size()
        ok = n_per_grp >= 2
        if ok.sum() == 0:
            print(f"  year {y}: no groups with ≥2 seeds!")
            continue
        v_int_anova = within_var[ok].mean()
        v_tot_anova = df[col].var(ddof=0)
        rows.append(dict(year=y, n_groups_used=int(ok.sum()),
                          v_internal_anova=v_int_anova,
                          v_total_anova=v_tot_anova,
                          v_int_frac_of_total=v_int_anova/v_tot_anova))
        print(f"\n  year {y} (ANOVA-18k):")
        print(f"    n (rff,cfg) groups w/ ≥2 seeds: {ok.sum():,}")
        print(f"    mean within-(rff,cfg) variance (= V_internal) = {v_int_anova:.4f} cm²")
        print(f"    total variance across all cells               = {v_tot_anova:.4f} cm²")
        print(f"    V_internal / V_total                           = {v_int_anova/v_tot_anova*100:.2f}%")
    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "outputs/substack/v5_hs_sanity_B_anova18k_vinternal_slr.csv", index=False)
    print(f"\n  wrote {ROOT / 'outputs/substack/v5_hs_sanity_B_anova18k_vinternal_slr.csv'}")
    return out


# ----------------------------------------------------------------------
# Check C — surrogate capacity test on total_slr
# ----------------------------------------------------------------------
def check_C_capacity_test_total_slr():
    print("\n" + "=" * 70)
    print("CHECK C — surrogate capacity test on total_slr")
    print("=" * 70)
    # Load slim weighted + features
    slim = pd.read_csv(SLIM_BASE, usecols=KEY_COLS + ["w_norm"])
    # Need SLR baseline by year. Use the slim CSV's bare-year SLR cols.
    cols_needed = [str(y) for y in [ANCHOR_YEAR] + LANDMARKS]
    slim_full = pd.read_csv(SLIM_BASE, usecols=KEY_COLS + ["w_norm"] + cols_needed)
    rff = pd.read_csv(RFF_FEATURES, usecols=["rff_idx"] + RFF_FEATS)
    cfg = pd.read_csv(CFG_PARAMS).reset_index().rename(columns={"index": "fair_cfg_idx"})
    cfg = cfg[["fair_cfg_idx"] + CFG_FEATURES]
    post = pd.read_csv(POST_PARAMS, usecols=POST_FEATURES).reset_index().rename(columns={"index": "post_idx"})
    df = slim_full.merge(rff, on="rff_idx").merge(cfg, on="fair_cfg_idx").merge(post, on="post_idx")
    df = df.sort_values(KEY_COLS).reset_index(drop=True)
    base = df[str(ANCHOR_YEAR)]
    for y in LANDMARKS:
        df[f"dslr_{y}"] = df[str(y)] - base
    w = df["w_norm"].to_numpy()

    feats = RFF_FEATS + CFG_FEATURES + POST_FEATURES
    rows = []
    for y in LANDMARKS:
        tcol = f"dslr_{y}"
        # Baseline (script-config) surrogate
        yhat_lo = fit_partial(df, feats, tcol)
        v_res_lo = weighted_var(df[tcol].to_numpy() - yhat_lo, w)
        v_tot = weighted_var(df[tcol].to_numpy(), w)
        # High-capacity + OOF
        yhat_hi, yhat_oof = fit_capacity_test(df, feats, tcol)
        v_res_hi = weighted_var(df[tcol].to_numpy() - yhat_hi, w)
        v_res_oof = weighted_var(df[tcol].to_numpy() - yhat_oof, w)
        rows.append(dict(year=y, v_total=v_tot,
                          v_residual_baseline=v_res_lo,
                          v_residual_high_capacity=v_res_hi,
                          v_residual_oof_5fold=v_res_oof,
                          frac_baseline=v_res_lo/v_tot,
                          frac_high_capacity=v_res_hi/v_tot,
                          frac_oof_5fold=v_res_oof/v_tot))
        print(f"\n  year {y} (total_slr V_residual; cm²):")
        print(f"    V_total                          = {v_tot:.2f}")
        print(f"    V_residual baseline (script)     = {v_res_lo:.2f}  ({v_res_lo/v_tot*100:.1f}% of V_total)")
        print(f"    V_residual high-capacity in-samp = {v_res_hi:.2f}  ({v_res_hi/v_tot*100:.1f}%)")
        print(f"    V_residual OOF 5-fold            = {v_res_oof:.2f}  ({v_res_oof/v_tot*100:.1f}%)")
        if v_res_hi < 0.5 * v_res_lo:
            print(f"    >> capacity test: high-capacity surrogate halves V_residual — modeling gap detected")
        elif v_res_oof < 0.7 * v_res_lo:
            print(f"    >> OOF test: 5-fold V_residual lower than baseline — baseline was overfit-biased")
        else:
            print(f"    >> capacity + OOF consistent with baseline — V_residual reflects real noise (internal var)")
    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "outputs/substack/v5_hs_sanity_C_capacity_test_slr.csv", index=False)
    print(f"\n  wrote {ROOT / 'outputs/substack/v5_hs_sanity_C_capacity_test_slr.csv'}")
    return out


if __name__ == "__main__":
    check_A_total_gmst_range_share()
    check_B_anova18k_vinternal_for_slr()
    check_C_capacity_test_total_slr()
    print("\n=== ALL CHECKS DONE ===")
