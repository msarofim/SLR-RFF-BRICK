"""Diagnostic: sweep surrogate configs for total_slr clipped target at a few
years. Isolate the effect of (weighted fit) x (monotonic) x (capacity) on
OOF R2 and on grouped Sobol S_emi/S_clim/S_brick. Throwaway harness."""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from shapley_hawkins_sutton import (KEY_COLS, RFF_FEATURES_LIST as RFF, CFG_FEATURES as CFG,
                                     POST_FEATURES as POST, assemble_features)
from hybrid_hs_slr_unified import load_baseline_v5, clip_per_year, YEARS, ANCHOR
from sklearn.ensemble import HistGradientBoostingRegressor

GROUPS = {"emissions": RFF, "climate": CFG, "brick": POST}
N = 8192
MONO = {"cum_co2_2030":1,"cum_co2_2100":1,"cum_co2_2300":1,"peak_co2_emissions":1,
        "cum_ch4_2100":1,"frac_negative_post_2050":-1}

v5, slr = load_baseline_v5()
i_a = int(np.where(YEARS==ANCHOR)[0][0])
target = clip_per_year(slr - slr[:,[i_a]], q=99.0)
feat = assemble_features()
assert (feat[KEY_COLS].to_numpy()==v5[KEY_COLS].to_numpy()).all()
cols = RFF+CFG+POST
X = feat[cols].to_numpy(float)
w = v5["w_norm"].to_numpy(float); w_p = w/w.sum()
col_of = {f:i for i,f in enumerate(cols)}
gidx = {g:np.array([col_of[f] for f in fl],int) for g,fl in GROUPS.items()}
mono_arr = np.array([MONO.get(f,0) for f in cols],int)

def sobol(m, rng):
    iA=rng.choice(len(X),N,True,p=w_p); iB=rng.choice(len(X),N,True,p=w_p)
    XA,XB=X[iA].copy(),X[iB].copy(); YA,YB=m.predict(XA),m.predict(XB)
    vY=np.var(np.concatenate([YA,YB])); S={}
    for g in GROUPS:
        XX=XA.copy(); XX[:,gidx[g]]=XB[:,gidx[g]]; Yg=m.predict(XX)
        S[g]=float(np.mean(YB*(Yg-YA))/vY)
    return S

def r2oof(weighted, mono, kw, y):
    rng=np.random.default_rng(2026); perm=rng.permutation(len(X)); nte=len(X)//5
    te,tr=perm[:nte],perm[nte:]
    m=HistGradientBoostingRegressor(monotonic_cst=(mono_arr if mono else None),**kw)
    m.fit(X[tr],y[tr],sample_weight=(w[tr] if weighted else None))
    yh=m.predict(X[te]); wte=w[te]; mu=(y[te]*wte).sum()/wte.sum()
    r2=1-(wte*(y[te]-yh)**2).sum()/max((wte*(y[te]-mu)**2).sum(),1e-30)
    return r2

CONFIGS = [
    ("weighted,nomono,600/63",   True, False, dict(max_iter=600,max_leaf_nodes=63,learning_rate=0.03,min_samples_leaf=20,l2_regularization=0.5,random_state=2026)),
    ("unweighted,nomono,600/63", False,False, dict(max_iter=600,max_leaf_nodes=63,learning_rate=0.03,min_samples_leaf=20,l2_regularization=0.5,random_state=2026)),
    ("unweighted,mono,600/63",   False,True,  dict(max_iter=600,max_leaf_nodes=63,learning_rate=0.03,min_samples_leaf=20,l2_regularization=0.5,random_state=2026)),
    ("weighted,nomono,1500/127", True, False, dict(max_iter=1500,max_leaf_nodes=127,learning_rate=0.02,min_samples_leaf=10,l2_regularization=0.1,random_state=2026)),
    ("unweighted,nomono,1500/127",False,False,dict(max_iter=1500,max_leaf_nodes=127,learning_rate=0.02,min_samples_leaf=10,l2_regularization=0.1,random_state=2026)),
]

for yr in (2050, 2100, 2150):
    it=int(np.where(YEARS==yr)[0][0]); y=target[:,it].astype(float)
    print(f"\n===== year {yr}  (V_total={np.var(y):.3g}) =====")
    for name,wt,mo,kw in CONFIGS:
        t0=time.time()
        r2=r2oof(wt,mo,kw,y)
        m=HistGradientBoostingRegressor(monotonic_cst=(mono_arr if mo else None),**kw)
        m.fit(X,y,sample_weight=(w if wt else None))
        rng=np.random.default_rng(7); S=sobol(m,rng)
        print(f"  {name:28s} R2oof={r2:5.3f}  S_emi={S['emissions']:.3f} "
              f"S_clim={S['climate']:.3f} S_brick={S['brick']:.3f} "
              f"sumS={sum(S.values()):.3f}  [{time.time()-t0:.0f}s]")
