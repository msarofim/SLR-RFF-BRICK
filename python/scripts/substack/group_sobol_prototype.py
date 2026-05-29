"""
group_sobol_prototype.py
========================

Prototype: group-Sobol variance decomposition for total ΔSLR at landmark
years, on the v5 LHS-10k_s cube.

Why: TreeSHAP under-attributes correlated within-axis features (RFF emissions
features are highly collinear; same for cfg ocean-heat parameters). At year
2150 the SHAP V_emi for SLR came out ~8.6%, while the ANOVA-18k model-free
main effect was ~43%. The Sobol main-effect index for grouped features is
the mathematically correct quantity for the Hawkins-Sutton decomposition.

Pick-and-freeze Saltelli estimator with empirical (cell-based) joint
sampling, so within-group correlations are preserved exactly:

  A, B  : two independent batches of N cells drawn (with replacement, Wong-
          weighted) from the v5 cube. Each "draw" provides a (rff, cfg, post)
          coordinate trio.
  AB_g  : take A but swap group g's features with B's.
  Y_*   : surrogate predictions at each sample.
  S_g (first order) = (1/N) Σ Y_B (Y_AB_g − Y_A) / Var(Y)
  ST_g (total order) = (1/(2N)) Σ (Y_A − Y_AB_g)² / Var(Y)

Internal variability (seed) is *not* in the surrogate — V_internal comes
from the seed-augmentation as before (model-free, ~0.7% at 2150).

Outputs:
  outputs/substack/sobol_proto_total_slr.csv  (per-year per-axis S, ST)
"""
from __future__ import annotations
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shapley_hawkins_sutton import (
    KEY_COLS, RFF_FEATURES_LIST as RFF_FEATS, CFG_FEATURES, POST_FEATURES,
    assemble_features,
)

ROOT = Path(__file__).resolve().parents[3]
OUT  = ROOT / "outputs" / "substack"
SLIM_BASE = ROOT / "outputs/brick_v145_slim/brick_lhs10ks_baseline_to2300_weighted.csv"

ANCHOR  = 2020
LANDMARKS = [2050, 2100, 2150]
N_SOBOL = 8192   # base sample size; total evals = 5*N per year
SEED    = 2026

GROUPS = {
    "emissions": RFF_FEATS,
    "climate":   CFG_FEATURES,
    "brick":     POST_FEATURES,
}
GROUP_NAMES = list(GROUPS.keys())


def main():
    print("[load] v5 slim baseline + features")
    feat = assemble_features()
    slim = pd.read_csv(SLIM_BASE,
                        usecols=KEY_COLS + ["w_norm"] +
                                [str(y) for y in [ANCHOR] + LANDMARKS])
    df = slim.merge(feat[KEY_COLS + RFF_FEATS + CFG_FEATURES + POST_FEATURES],
                     on=KEY_COLS).sort_values(KEY_COLS).reset_index(drop=True)
    n_cells = len(df)
    print(f"  cells: {n_cells:,}")

    # Group → list of column names
    feature_cols = RFF_FEATS + CFG_FEATURES + POST_FEATURES
    group_of_col = {**{f: "emissions" for f in RFF_FEATS},
                     **{f: "climate"   for f in CFG_FEATURES},
                     **{f: "brick"     for f in POST_FEATURES}}
    X_all = df[feature_cols].to_numpy(dtype=np.float64)
    w = df["w_norm"].to_numpy(dtype=np.float64)
    w_p = w / w.sum()

    # Per-group col indices (positions in X_all)
    col_of = {f: i for i, f in enumerate(feature_cols)}
    group_idx = {g: np.array([col_of[f] for f in flist], dtype=int)
                  for g, flist in GROUPS.items()}

    rng = np.random.default_rng(SEED)

    rows = []
    for y in LANDMARKS:
        print(f"\n=== year {y} ===")
        t0 = time.time()
        target = (df[str(y)].to_numpy(dtype=np.float64) -
                   df[str(ANCHOR)].to_numpy(dtype=np.float64))

        # ---- fit surrogate (high capacity for the SLR problem; OOF-honest
        # via 5-fold not needed here since we just need predictions) ----
        from sklearn.ensemble import HistGradientBoostingRegressor
        m = HistGradientBoostingRegressor(
            max_iter=600, max_leaf_nodes=63, learning_rate=0.03,
            min_samples_leaf=20, l2_regularization=0.5, random_state=SEED,
        )
        m.fit(X_all, target, sample_weight=w)
        yhat = m.predict(X_all)
        wsum = w.sum()
        mu_y = (target * w).sum() / wsum
        v_total = ((target - mu_y) ** 2 * w).sum() / wsum
        ss_res = (((target - yhat) ** 2) * w).sum() / wsum
        r2_in = 1.0 - ss_res / max(v_total, 1e-30)
        print(f"  surrogate fit: V_total={v_total:.2f} R²_in={r2_in:.3f} "
              f"({time.time()-t0:.1f}s)")

        # ---- Saltelli pick-and-freeze with empirical cell sampling ----
        N = N_SOBOL
        # A & B: independent importance-weighted draws of N cell indices
        idx_A = rng.choice(n_cells, size=N, replace=True, p=w_p)
        idx_B = rng.choice(n_cells, size=N, replace=True, p=w_p)
        X_A = X_all[idx_A].copy()
        X_B = X_all[idx_B].copy()
        Y_A = m.predict(X_A)
        Y_B = m.predict(X_B)
        var_Y = np.var(np.concatenate([Y_A, Y_B]))
        if var_Y == 0:
            print("  V_total=0, skipping"); continue

        S_first = {}
        S_total = {}
        for g in GROUP_NAMES:
            X_ABg = X_A.copy()
            cols = group_idx[g]
            X_ABg[:, cols] = X_B[:, cols]
            Y_ABg = m.predict(X_ABg)
            # First-order Saltelli (Jansen 1999 / Saltelli 2010 estimator)
            S_first[g] = float(np.mean(Y_B * (Y_ABg - Y_A)) / var_Y)
            # Total-order (Jansen 1999)
            S_total[g] = float(np.mean((Y_A - Y_ABg) ** 2) / (2 * var_Y))
        sum_first = sum(S_first.values())
        sum_total = sum(S_total.values())
        # Residual / unattributed = 1 - sum_first (the interactions + noise)
        # Truncate at [0, 1] for display sanity
        print(f"  Sobol (N={N}; total evals = {5*N}): "
              f"S_first sum = {sum_first:.3f}, ST sum = {sum_total:.3f}")
        for g in GROUP_NAMES:
            print(f"    {g:10s}: S_first = {S_first[g]:+.3f}   ST = {S_total[g]:+.3f}")

        row = dict(year=y, V_total_v5=v_total, R2_in=r2_in)
        for g in GROUP_NAMES:
            row[f"S_first_{g}"] = S_first[g]
            row[f"S_total_{g}"] = S_total[g]
        row["sum_S_first"] = sum_first
        row["interactions_or_residual"] = 1.0 - sum_first
        rows.append(row)

    out = pd.DataFrame(rows)
    out.to_csv(OUT / "sobol_proto_total_slr.csv", index=False)
    print(f"\nwrote {OUT}/sobol_proto_total_slr.csv")

    # Compare to ANOVA-18k headline (model-free, factorial)
    print()
    print("=== Comparison to ANOVA-18k model-free main effects ===")
    print(f"{'year':>4s}  {'axis':>10s}  {'Sobol S_first':>14s}  {'ANOVA main':>11s}")
    anova_ref = {
        2050: dict(emissions=0.045, climate=0.515, brick=0.246),
        2100: dict(emissions=0.294, climate=0.415, brick=0.192),
        2150: dict(emissions=0.434, climate=0.353, brick=0.074),
    }
    for y in LANDMARKS:
        r = next(rr for rr in rows if rr["year"] == y)
        for g in GROUP_NAMES:
            print(f"{y:>4d}  {g:>10s}  {r[f'S_first_{g}']:>13.3f}  {anova_ref[y][g]:>10.3f}")


if __name__ == "__main__":
    main()
