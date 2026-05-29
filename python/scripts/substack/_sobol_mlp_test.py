"""Is the SLR R2 ceiling HGB-specific or irreducible? Test MLP + RF + ExtraTrees
+ KNN surrogates on total_slr (clipped) at 2100/2150. OOF (80/20) R2 only.
If a smooth high-capacity model breaks ~0.71, the ceiling was tree-specific."""
import sys, time, warnings
from pathlib import Path
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from shapley_hawkins_sutton import (KEY_COLS, RFF_FEATURES_LIST as RFF8,
    CFG_FEATURES as CFG, POST_FEATURES as POST, SLIM_BASE_CSV, CFG_PARAMS_CSV, POST_PARAMS_CSV)
from hybrid_hs_slr_unified import load_baseline_v5, clip_per_year, YEARS, ANCHOR
from sklearn.neural_network import MLPRegressor
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

ROOT = Path("/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK")
v5, slr = load_baseline_v5()
i_a = int(np.where(YEARS == ANCHOR)[0][0])
target = clip_per_year(slr - slr[:, [i_a]], q=99.0)
w = v5["w_norm"].to_numpy(float)

slim = pd.read_csv(SLIM_BASE_CSV, usecols=KEY_COLS + ["w_norm"])
rff = pd.read_csv(ROOT/"outputs/rff_summary_features.csv")
cfg = pd.read_csv(CFG_PARAMS_CSV, usecols=lambda c: c == "" or c in CFG)
cfg = cfg.reset_index().rename(columns={"index": "fair_cfg_idx"})[["fair_cfg_idx"]+CFG]
post = pd.read_csv(POST_PARAMS_CSV, usecols=POST).reset_index().rename(columns={"index":"post_idx"})
df = slim.merge(rff,on="rff_idx").merge(cfg,on="fair_cfg_idx").merge(post,on="post_idx")
df = df.sort_values(KEY_COLS).reset_index(drop=True)
assert (df[KEY_COLS].to_numpy()==v5[KEY_COLS].to_numpy()).all()
X = df[RFF8+CFG+POST].to_numpy(float)

def r2oof(model, y):
    rng=np.random.default_rng(2026); perm=rng.permutation(len(X)); nte=len(X)//5
    te,tr=perm[:nte],perm[nte:]
    model.fit(X[tr],y[tr]); yh=model.predict(X[te])
    wte=w[te]; mu=(y[te]*wte).sum()/wte.sum()
    return 1-(wte*(y[te]-yh)**2).sum()/max((wte*(y[te]-mu)**2).sum(),1e-30)

MODELS = {
 "HGB600":      lambda: HistGradientBoostingRegressor(max_iter=600,max_leaf_nodes=63,learning_rate=0.03,min_samples_leaf=20,l2_regularization=0.5,random_state=2026),
 "RF800":       lambda: RandomForestRegressor(n_estimators=800,min_samples_leaf=3,n_jobs=-1,random_state=2026),
 "ExtraTrees":  lambda: ExtraTreesRegressor(n_estimators=800,min_samples_leaf=3,n_jobs=-1,random_state=2026),
 "MLP_256_128_64": lambda: make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(256,128,64),activation="relu",alpha=1e-3,learning_rate_init=1e-3,max_iter=800,early_stopping=True,n_iter_no_change=25,random_state=2026)),
 "MLP_512_256":   lambda: make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(512,256),activation="relu",alpha=1e-3,learning_rate_init=1e-3,max_iter=800,early_stopping=True,n_iter_no_change=25,random_state=2026)),
 "KNN50":       lambda: make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=50,weights="distance")),
}
for yr in (2100, 2150):
    it=int(np.where(YEARS==yr)[0][0]); y=target[:,it].astype(float)
    print(f"\n===== {yr} =====")
    for name,mk in MODELS.items():
        t0=time.time()
        try: r=r2oof(mk(),y); print(f"  {name:16s} R2oof={r:6.3f}  [{time.time()-t0:.0f}s]")
        except Exception as e: print(f"  {name:16s} ERR {e}")
