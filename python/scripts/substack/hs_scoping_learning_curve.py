"""
hs_scoping_learning_curve.py
============================

Scoping: how large a new ensemble would need to be for a trustworthy SLR
Hawkins-Sutton decomposition. The production Group-Sobol surrogate ceilings at
OOF R2~0.71 (2150) on the current 10k-cell ensemble. Is that DATA-limited
(more cells -> higher R2) or IRREDUCIBLE (model/structure)? The learning curve
R2_oof(N_train) answers it and lets us extrapolate the N needed for a target R2.

Method:
  - Fixed held-out test set (2000 cells). Train HGB on nested subsets
    N in {500,1000,2000,4000,7000} of the remaining 8000. Repeat over a few
    seeds, average. Plot R2_oof vs N; fit a saturating curve
    R2(N) = R2_inf - C * N^(-p)  and solve for N at target R2.
  - Report for total_slr (2100, 2150) and pulse_slr (2150).

Also prints guidance for ANOVA / Shapley / Sobol data needs.

Output: outputs/substack/hs_scoping_learning_curve.csv + .png
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from shapley_hawkins_sutton import (KEY_COLS, RFF_FEATURES_LIST as RFF, CFG_FEATURES as CFG,
    POST_FEATURES as POST, SLIM_BASE_CSV, CFG_PARAMS_CSV, POST_PARAMS_CSV, OUT)
from hybrid_hs_slr_unified import load_baseline_v5, load_pulse_v5, clip_per_year, YEARS, ANCHOR
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy.optimize import curve_fit

KW = dict(max_iter=600, max_leaf_nodes=63, learning_rate=0.03,
          min_samples_leaf=20, l2_regularization=0.5, random_state=2026)
N_GRID = [500, 1000, 2000, 4000, 7000]
SEEDS = [0, 1, 2]
N_TEST = 2000

# features (8 RFF + cfg + post)
v5, slr = load_baseline_v5()
i_a = int(np.where(YEARS == ANCHOR)[0][0])
slim = pd.read_csv(SLIM_BASE_CSV, usecols=KEY_COLS + ["w_norm"])
cfg = pd.read_csv(CFG_PARAMS_CSV, usecols=lambda c: c == "" or c in CFG)
cfg = cfg.reset_index().rename(columns={"index": "fair_cfg_idx"})[["fair_cfg_idx"]+CFG]
post = pd.read_csv(POST_PARAMS_CSV, usecols=POST).reset_index().rename(columns={"index":"post_idx"})
feat = slim.merge(pd.read_csv("outputs/rff_summary_features.csv"), on="rff_idx") \
           .merge(cfg, on="fair_cfg_idx").merge(post, on="post_idx") \
           .sort_values(KEY_COLS).reset_index(drop=True)
assert (feat[KEY_COLS].to_numpy() == v5[KEY_COLS].to_numpy()).all()
X = feat[RFF+CFG+POST].to_numpy(float)
w = v5["w_norm"].to_numpy(float)

def target_for(kind, yr):
    it = int(np.where(YEARS == yr)[0][0])
    if kind == "total":
        t = clip_per_year(slr - slr[:, [i_a]], 99.0)
    else:
        v5p, slrp = load_pulse_v5()
        t = clip_per_year(((slrp - slrp[:, [i_a]]) - (slr - slr[:, [i_a]])) / 0.01, 99.0)
    return t[:, it].astype(float)

def wr2(y, yh, ww):
    mu = (y*ww).sum()/ww.sum()
    return 1 - (ww*(y-yh)**2).sum()/max((ww*(y-mu)**2).sum(), 1e-30)

def curve(kind, yr):
    y = target_for(kind, yr)
    rows = []
    for N in N_GRID:
        r2s = []
        for s in SEEDS:
            rng = np.random.default_rng(100+s)
            perm = rng.permutation(len(X))
            te = perm[:N_TEST]; pool = perm[N_TEST:]
            tr = pool[:N]
            m = HistGradientBoostingRegressor(**KW); m.fit(X[tr], y[tr])
            r2s.append(wr2(y[te], m.predict(X[te]), w[te]))
        rows.append((N, float(np.mean(r2s)), float(np.std(r2s))))
        print(f"  {kind} {yr}  N={N:5d}  R2oof={np.mean(r2s):.3f} +/- {np.std(r2s):.3f}", flush=True)
    return rows

def extrapolate(rows):
    N = np.array([r[0] for r in rows], float); R = np.array([r[1] for r in rows])
    # R2(N) = Rinf - C * N^-p
    def f(N, Rinf, C, p): return Rinf - C*np.power(N, -p)
    try:
        popt, _ = curve_fit(f, N, R, p0=[0.85, 5.0, 0.4],
                            bounds=([0.5, 0, 0.05], [1.0, 1e6, 2.0]), maxfev=20000)
        Rinf, C, p = popt
        def n_for(target):
            if target >= Rinf: return np.inf
            return (C/(Rinf-target))**(1/p)
        return Rinf, {t: n_for(t) for t in (0.80, 0.85, 0.90)}
    except Exception as e:
        return None, str(e)

def main():
    allrows = []
    for kind, yr in [("total",2100),("total",2150),("pulse",2150)]:
        print(f"\n=== {kind} SLR {yr} ===", flush=True)
        rows = curve(kind, yr)
        Rinf, needs = extrapolate(rows)
        print(f"  fitted R2_inf={Rinf if Rinf is None else round(Rinf,3)}; "
              f"N for R2: {needs}", flush=True)
        for N,m,sd in rows:
            allrows.append(dict(kind=kind, year=yr, N_train=N, R2oof=m, R2sd=sd,
                                R2_inf=(None if Rinf is None else round(Rinf,4))))
    df = pd.DataFrame(allrows)
    df.to_csv(OUT / "hs_scoping_learning_curve.csv", index=False)
    print(f"\nwrote {OUT}/hs_scoping_learning_curve.csv", flush=True)

if __name__ == "__main__":
    main()
