"""Test whether rich emissions features raise OOF R2 and shrink the residual
for total_slr (clipped) at landmark years. Unweighted HGB, group-Sobol.
Compares the of-total decomposition old(8-feat) vs rich."""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from shapley_hawkins_sutton import (KEY_COLS, RFF_FEATURES_LIST as RFF8,
    CFG_FEATURES as CFG, POST_FEATURES as POST, SLIM_BASE_CSV, CFG_PARAMS_CSV, POST_PARAMS_CSV)
from hybrid_hs_slr_unified import load_baseline_v5, clip_per_year, YEARS, ANCHOR
from sklearn.ensemble import HistGradientBoostingRegressor

ROOT = Path("/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK")
RICH = ROOT / "outputs/rff_features_rich.csv"
N = 8192
KW = dict(max_iter=600, max_leaf_nodes=63, learning_rate=0.03,
          min_samples_leaf=20, l2_regularization=0.5, random_state=2026)

# target
v5, slr = load_baseline_v5()
i_a = int(np.where(YEARS == ANCHOR)[0][0])
target = clip_per_year(slr - slr[:, [i_a]], q=99.0)
w = v5["w_norm"].to_numpy(float); w_p = w / w.sum()

# feature assembly for a given RFF feature list
def assemble(rff_cols, rff_df):
    slim = pd.read_csv(SLIM_BASE_CSV, usecols=KEY_COLS + ["w_norm"])
    cfg = pd.read_csv(CFG_PARAMS_CSV, usecols=lambda c: c == "" or c in CFG)
    cfg = cfg.reset_index().rename(columns={"index": "fair_cfg_idx"})[["fair_cfg_idx"] + CFG]
    post = pd.read_csv(POST_PARAMS_CSV, usecols=POST).reset_index().rename(columns={"index": "post_idx"})
    df = (slim.merge(rff_df[["rff_idx"] + rff_cols], on="rff_idx")
              .merge(cfg, on="fair_cfg_idx").merge(post, on="post_idx"))
    df = df.sort_values(KEY_COLS).reset_index(drop=True)
    assert (df[KEY_COLS].to_numpy() == v5[KEY_COLS].to_numpy()).all()
    return df

def run(label, rff_cols, rff_df):
    df = assemble(rff_cols, rff_df)
    feature_cols = rff_cols + CFG + POST
    X = df[feature_cols].to_numpy(float)
    col_of = {f: i for i, f in enumerate(feature_cols)}
    groups = {"emissions": rff_cols, "climate": CFG, "brick": POST}
    gidx = {g: np.array([col_of[f] for f in fl], int) for g, fl in groups.items()}
    print(f"\n##### {label}  ({len(rff_cols)} emi feats, {X.shape[1]} total) #####")
    for yr in (2050, 2100, 2150):
        it = int(np.where(YEARS == yr)[0][0]); y = target[:, it].astype(float)
        rng = np.random.default_rng(2026); perm = rng.permutation(len(X)); nte = len(X)//5
        te, tr = perm[:nte], perm[nte:]
        m = HistGradientBoostingRegressor(**KW); m.fit(X[tr], y[tr])
        yh = m.predict(X[te]); wte = w[te]; mu = (y[te]*wte).sum()/wte.sum()
        r2 = 1 - (wte*(y[te]-yh)**2).sum()/max((wte*(y[te]-mu)**2).sum(), 1e-30)
        mf = HistGradientBoostingRegressor(**KW); mf.fit(X, y)
        rng = np.random.default_rng(7)
        iA = rng.choice(len(X), N, True, p=w_p); iB = rng.choice(len(X), N, True, p=w_p)
        XA, XB = X[iA].copy(), X[iB].copy(); YA, YB = mf.predict(XA), mf.predict(XB)
        vY = np.var(np.concatenate([YA, YB])); S = {}
        for g in groups:
            XX = XA.copy(); XX[:, gidx[g]] = XB[:, gidx[g]]; Yg = mf.predict(XX)
            S[g] = float(np.mean(YB*(Yg-YA))/vY)
        r2c = max(r2, 0)
        emi, clim, brk = S["emissions"]*r2c, S["climate"]*r2c, S["brick"]*r2c
        resid = 1 - (emi+clim+brk)   # of-total (internal tiny, ignore here)
        print(f"  {yr}: R2={r2:.3f} sumS={sum(S.values()):.3f} | of-total: "
              f"emi={emi:.3f} clim={clim:.3f} brick={brk:.3f} resid={resid:.3f}")

rich_df = pd.read_csv(RICH)
old_df = pd.read_csv(ROOT/"outputs/rff_summary_features.csv")
rich_cols = [c for c in rich_df.columns if c != "rff_idx"]
run("OLD 8-feature", RFF8, old_df)
run("RICH", rich_cols, rich_df)
