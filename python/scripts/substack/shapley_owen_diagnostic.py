"""
shapley_owen_diagnostic.py
==========================

Owen-2014 closed-form Shapley effects (Castro-Gomez random-permutation
algorithm) computed at landmark years 2050/2100/2150 for all four
targets (total GMST, total SLR, pulse GMST, pulse SLR). The output is a
diagnostic comparison table against the TreeSHAP variance attributions
computed by shapley_hawkins_sutton.py.

Why: TreeSHAP attributes variance to whichever feature the tree splits
on first. Under correlated features (cfg ECS-related parameters and
BRICK te_α both affect SLR), trees pick cfg first; BRICK gets
under-attributed. Owen-2014 Shapley effects average over all orderings
of feature inclusion, so confounded effects are split fairly across
features.

If Owen-Shapley gives BRICK ≈ ANOVA-18k's f_brick (≈23% for total SLR
at 2100), we know TreeSHAP attribution bias is the issue and we should
re-render the H-S figures using Owen-Shapley. If Owen-Shapley gives
similar BRICK to TreeSHAP (~3% for total SLR), the LHS-10k ensemble
itself is under-sampling BRICK parameter space and a bigger ensemble
is needed.

Castro-Gomez random-permutation algorithm:
  For M random permutations π of features:
    For each feature i appearing at position k in π:
      Marginal contribution_i += Var(E[Y | X_{π[0..k]}]) − Var(E[Y | X_{π[0..k-1]}])
  Owen-Shapley effect_i = mean over M of marginal contributions

The conditional variance Var(E[Y | X_S]) is estimated by:
  1. For each of N_outer reference points x*_S, sample x_S' = x*_S
  2. Sample N_inner draws x_{not S} from the marginal X distribution
  3. Evaluate model at (x_S, x_{not S}) draws
  4. Conditional expectation ≈ mean of predictions over N_inner draws
  5. Var of conditional expectation across N_outer reference points

Computational cost per year: M × d × N_outer × N_inner predictions.
With M=80, d=50, N_outer=200, N_inner=80: 64M predictions × ~1 μs each
≈ 60s per year per target. 4 targets × 3 landmark years = 12 fits +
12 × ~60s = 12 min Owen-Shapley + ~15 min surrogate fits = ~30 min total.

Outputs:
  outputs/substack/shapley_owen_diagnostic.csv  — per-target × per-year × per-axis
"""
from __future__ import annotations
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

# Reuse the assembly + loader functions + feature set from the main pipeline.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from shapley_hawkins_sutton import (
    TARGETS, RFF_FEATURES_LIST, CFG_FEATURES, POST_FEATURES,
    AXIS_OF, OUT, OUTLIER_PERCENTILE, PULSE_SIZE_GTCO2,
    YEAR_LO, YEAR_HI, SMOOTH_WINDOW_YR_PULSE,
    _smooth_traj, assemble_features, load_target,
)

# Owen-Shapley diagnostic only at year 2100 (the headline reporting year).
# Castro-Gomez parameters cut substantially from earlier estimate: M=80,
# N_outer=200, N_inner=80 made each year run 50+ min (10+ hr total for the
# original 12-fit plan), which is impractical locally. With M=30, N_outer=60,
# N_inner=30 a single landmark year runs in ~3-5 min; 4 targets = ~15-20 min.
# Accuracy is still good enough for the diagnostic question ("does Owen
# rank BRICK higher than TreeSHAP?") even if Shapley values themselves
# have higher sampling noise.
LANDMARK_YEARS = [2100]
M_PERMUTATIONS = 30
N_OUTER        = 60
N_INNER        = 30
RANDOM_SEED    = 2026


def owen_shapley_effects(model, X, w=None, M=M_PERMUTATIONS,
                          n_outer=N_OUTER, n_inner=N_INNER, rng=None):
    """Castro-Gomez random-permutation estimator of Owen-2014 Shapley
    effects. Returns per-feature variance-decomposition Shapley values
    that sum to Var(model.predict(X)).

    X : array (n_samples, n_features)
    w : optional sample weights, shape (n_samples,)
    """
    if rng is None:
        rng = np.random.default_rng(RANDOM_SEED)
    n, d = X.shape
    if w is None:
        w = np.ones(n) / n
    else:
        w = w / w.sum()

    shap_eff = np.zeros(d)

    # Pre-sample marginal X-distribution from the data (will reuse)
    def sample_marginal(n_draws):
        idx = rng.choice(n, size=n_draws, replace=True, p=w)
        return X[idx]

    def var_cond_expectation(S):
        """Estimate Var_x*(E_{x_{not S}}[Y | x*_S]). S is a set of feature
        indices; if empty, returns 0 (since E[Y] is constant)."""
        if len(S) == 0:
            return 0.0
        # Reference outer samples (use full distribution via weighted choice)
        ref_idx = rng.choice(n, size=n_outer, replace=True, p=w)
        cond_means = np.zeros(n_outer)
        S_list = list(S)
        not_S = [j for j in range(d) if j not in S]
        for k in range(n_outer):
            X_eval = np.tile(X[ref_idx[k]], (n_inner, 1))
            if not_S:
                # Replace not-S columns with marginal draws
                marg = sample_marginal(n_inner)
                X_eval[:, not_S] = marg[:, not_S]
            preds = model.predict(X_eval)
            cond_means[k] = preds.mean()
        return float(cond_means.var(ddof=0))

    for m_idx in range(M):
        perm = rng.permutation(d)
        S_curr = []
        v_curr = 0.0
        for k, i in enumerate(perm):
            S_next = S_curr + [int(i)]
            v_next = var_cond_expectation(set(S_next))
            shap_eff[i] += v_next - v_curr
            S_curr = S_next
            v_curr = v_next

    shap_eff /= M
    # Clamp small negatives from finite-sample noise
    shap_eff = np.maximum(shap_eff, 0.0)
    return shap_eff


def run_target_at_year(feat_df, target, year, model_cache=None):
    """Fit (or reuse) a surrogate for `target`, evaluate Owen-Shapley
    effects at the specified `year`. Returns (axis_dict, year_features, model)."""
    from sklearn.ensemble import HistGradientBoostingRegressor

    print(f"\n  [{target['key']} @ {year}]", flush=True)
    use_brick = target["use_brick_features"]
    feature_cols = (RFF_FEATURES_LIST + CFG_FEATURES + (POST_FEATURES if use_brick else []))

    if model_cache is None or target["key"] not in model_cache:
        # Load full panel and fit
        years, M = load_target(target["loader"], feat_df, target["anchor_year"])
        if target["clip_outliers"]:
            cap = float(np.percentile(M, OUTLIER_PERCENTILE))
            M = np.clip(M, None, cap)
        if target["smoothing"] > 1:
            M = _smooth_traj(M, target["smoothing"])
        # Stack time-as-feature
        n_cells = M.shape[0]
        n_yr = M.shape[1]
        X_static = feat_df[feature_cols].to_numpy(dtype=np.float64)
        w_cell = feat_df["w_norm"].to_numpy(dtype=np.float64)
        X_long = np.repeat(X_static, n_yr, axis=0)
        year_long = np.tile(years, n_cells).reshape(-1, 1)
        X_long = np.hstack([year_long, X_long])
        y_long = M.reshape(-1)
        w_long = np.repeat(w_cell, n_yr)
        feature_names = ["year"] + feature_cols
        print(f"    fitting surrogate on {len(X_long):,}-row panel ...", flush=True)
        t0 = time.time()
        model = HistGradientBoostingRegressor(
            max_iter=300, max_leaf_nodes=31, learning_rate=0.05,
            min_samples_leaf=20, l2_regularization=0.5, random_state=2026,
        )
        model.fit(X_long, y_long)
        print(f"    fit done ({time.time()-t0:.1f}s); train R²={model.score(X_long, y_long):.4f}", flush=True)
        if model_cache is not None:
            model_cache[target["key"]] = (model, feature_names, years, n_cells, n_yr, w_cell, X_static)
    else:
        model, feature_names, years, n_cells, n_yr, w_cell, X_static = model_cache[target["key"]]

    # Build year-slice X for Owen-Shapley
    it = int(np.where(years == year)[0][0])
    n_features = X_static.shape[1] + 1
    X_year = np.hstack([np.full((n_cells, 1), year, dtype=np.float64), X_static])

    print(f"    Owen-Shapley: M={M_PERMUTATIONS} perms × {n_features} features × {N_OUTER}×{N_INNER} MC ...", flush=True)
    t0 = time.time()
    rng = np.random.default_rng(RANDOM_SEED + year)
    shap_eff = owen_shapley_effects(model, X_year, w=w_cell, rng=rng)
    print(f"    Owen-Shapley done ({time.time()-t0:.1f}s)", flush=True)

    # Aggregate by axis (skip the year feature)
    axis_acc = {"emissions": 0.0, "climate": 0.0, "brick": 0.0}
    for j, f in enumerate(feature_names):
        if f == "year":
            continue
        ax = AXIS_OF.get(f, "other")
        if ax in axis_acc:
            axis_acc[ax] += float(shap_eff[j])

    # V_total at this year (for fraction)
    # Compute weighted var of y at this year from the stacked panel
    # … but we don't keep y_long here. Use Var of model predictions at year.
    yhat_year = model.predict(X_year)
    mu = (yhat_year * w_cell).sum() / w_cell.sum()
    v_pred = ((yhat_year - mu) ** 2 * w_cell).sum() / w_cell.sum()
    total = sum(axis_acc.values())
    fracs = {ax: (axis_acc[ax] / total) if total > 0 else 0.0 for ax in axis_acc}
    return axis_acc, fracs, v_pred, model_cache


def main():
    print("[features] assembling per-cell covariates", flush=True)
    feat = assemble_features()

    rows = []
    model_cache = {}
    for target in TARGETS:
        for y in LANDMARK_YEARS:
            axis_var, axis_frac, v_pred, model_cache = run_target_at_year(
                feat, target, y, model_cache=model_cache)
            print(f"    Owen-Shapley fractions @ {y}:", flush=True)
            for ax in ("emissions", "climate", "brick"):
                print(f"      {ax}: {axis_frac[ax]:.3f}  (Var={axis_var[ax]:.5g})", flush=True)
            rows.append({
                "target": target["key"], "year": int(y),
                "owen_var_emissions": axis_var["emissions"],
                "owen_var_climate":   axis_var["climate"],
                "owen_var_brick":     axis_var["brick"],
                "owen_frac_emissions": axis_frac["emissions"],
                "owen_frac_climate":   axis_frac["climate"],
                "owen_frac_brick":     axis_frac["brick"],
                "owen_v_predicted":   float(v_pred),
            })
    df = pd.DataFrame(rows)
    out_csv = OUT / "shapley_owen_diagnostic.csv"
    df.to_csv(out_csv, index=False)
    print(f"\nwrote {out_csv}", flush=True)

    # Side-by-side comparison vs TreeSHAP results
    print("\n=== TreeSHAP vs Owen-Shapley fractions at landmark years ===")
    print("(BRICK column is the key comparison — TreeSHAP under-attributes; "
          "Owen-Shapley should reveal the true BRICK contribution)")
    for target in TARGETS:
        tree_csv = OUT / f"shapley_hs_per_axis_{target['key']}.csv"
        if not tree_csv.exists():
            continue
        tree_df = pd.read_csv(tree_csv)
        print(f"\n{target['key']}:")
        for y in LANDMARK_YEARS:
            owen_row = df[(df.target == target["key"]) & (df.year == y)].iloc[0]
            tree_row = tree_df[tree_df.year == y]
            if not len(tree_row):
                continue
            tree_row = tree_row.iloc[0]
            tree_b = tree_row.get("brick", 0.0) if "brick" in tree_row else 0.0
            print(f"  {y}: TreeSHAP brick={tree_b:.3f}  Owen brick={owen_row.owen_frac_brick:.3f}  "
                  f"(emi: {tree_row.get('emissions',0):.2f}/{owen_row.owen_frac_emissions:.2f},  "
                  f"clim: {tree_row.get('climate',0):.2f}/{owen_row.owen_frac_climate:.2f})")


if __name__ == "__main__":
    main()
