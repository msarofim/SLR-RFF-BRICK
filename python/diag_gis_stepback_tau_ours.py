"""Measure OUR model's held-forcing tau_eff on the SAME arms, the SAME way as PROTECT.
Read-only: imports the published kernel, writes nothing to the repo."""
import os, sys
import numpy as np, pandas as pd
REPO=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO,"python"))
os.chdir(REPO)
import scope_gis_shape_all_scenarios as A
from scope_gis_ridge_vs_protect import basin2_series, rebase_cm
from scope_gis_leq_ridge_vs_literature import gis_tbar
from scope_gis_2300_relaxation import DRIVER_BASE, YEARS, gis_shape_table, regional_driver

post=pd.read_csv(A.POST); tbar=gis_tbar()
r_s=np.exp(post["gis_slow_ell"].to_numpy())
post["gis_alpha_s"]=post["gis_slow_w"].to_numpy()*r_s/tbar
post["gis_beta_s"]=(1.0-post["gis_slow_w"].to_numpy())*r_s
S_tab=gis_shape_table(); ibd=(YEARS>=DRIVER_BASE[0])&(YEARS<=DRIVER_BASE[1])
def load(stem,col):
    g=pd.read_csv(os.path.join(REPO,f"outputs/{stem}.csv")).set_index("year")[col].reindex(YEARS).to_numpy()
    rb=g-g[ibd].mean(); return rb, regional_driver(rb,post["gis_amp"].to_numpy(),S_tab)
drivers={}; gmst={}
for ssp,lab,fam,stem in A.ARMS:
    gmst[(ssp,fam)],drivers[(ssp,fam)]=load(stem,f"gmst_{A.ARM}")
# hindcast bisection exactly as the published scan does
idx={y:int(np.where(YEARS==y)[0][0]) for y in list(A.HORIZONS)+list(A.HIND)+[2015,2050,2250]}
tgt=pd.read_csv(A.TARGETS).set_index("year")["gis"]
want=float(tgt.loc[A.HIND[1]]-tgt.loc[A.HIND[0]]); Th=drivers[A.HIND_ARM]
lo,hi=np.full(len(post),1e-4),np.full(len(post),1e3)
for _ in range(80):
    mid=np.sqrt(lo*hi); L=basin2_series(Th,post,1.0,mid)
    below=100.0*(L[:,idx[A.HIND[1]]]-L[:,idx[A.HIND[0]]])<want
    lo,hi=np.where(below,mid,lo),np.where(below,hi,mid)
s=np.sqrt(lo*hi)
print("OUR MODEL (L14, k=1), same arms, same estimator as the PROTECT table\n")
print(f"{'arm':22} {'2050-2100':>10}{'2100-2150':>10}{'2150-2200':>10}{'2200-2250':>10}{'2250-2300':>10}   tau_eff (yr)")
for ssp,lab,fam,_ in A.ARMS:
    m=np.median(rebase_cm(basin2_series(drivers[(ssp,fam)],post,1.0,s)),axis=0)
    q={y:m[idx[y]] for y in (2050,2100,2150,2200,2250,2300)}
    rates=[(q[a+50]-q[a])/50*100 for a in (2050,2100,2150,2200,2250)]
    r=[x/100 for x in rates[1:]]
    tau=[]
    for i in range(3):
        f=r[i+1]/r[i] if r[i]>0 else np.nan
        tau.append(-50/np.log(f) if (f==f and 0<f<1) else np.inf)
    print(f"{lab+' '+fam:22} "+"".join(f"{x:10.2f}" for x in rates)
          +"   "+" ".join(f"{t:6.0f}" if np.isfinite(t) else "   inf" for t in tau))
