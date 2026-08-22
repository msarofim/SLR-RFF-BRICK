"""THE MISSING CRITERION. Every tap/reservoir cell so far was scored on LEVELS
(2100, 2150, 2300 bands) and on an RMS of log-levels. None was scored on the RATE
at the last horizon -- so a cell can land on the 2300 level with the wrong slope and
be wrong again by 2400. Add the 2250-2300 rate, per arm, at matched forcing, and
re-rank the shipped reservoir cell against the literature-anchored alternative.

  cell A  V=1.0 m, onset 4.69 K, tau  800 yr   -- the offline optimum (2026-08-22a)
  cell B  V=6.0 m, onset 4.69 K, tau 2200 yr   -- whole-sheet commitment on a 2-3 kyr
                                                 clock, the value the equilibrium
                                                 literature implies (Van Breedam 2020
                                                 ~2 kyr at high forcing; Greve &
                                                 Chambers 2022 1.79 m by 3000)
NOTE V=6 m EXCEEDS V_MAX_M=2.73 (the NO+NE Mouginot inventory), so cell B cannot be
charged to the high basin. It is a WHOLE-SHEET object. That is a real constraint on
where it can be wired, not a detail.
"""
import os,sys
import numpy as np, pandas as pd
REPO=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,os.path.join(REPO,"python")); os.chdir(REPO)
import scope_gis_shape_all_scenarios as A
from scope_gis_ridge_vs_protect import basin2_series, rebase_cm
from scope_gis_leq_ridge_vs_literature import gis_tbar
from scope_gis_2300_relaxation import DRIVER_BASE, YEARS, gis_shape_table, regional_driver
from scope_gis_reservoir_offline import reservoir_unit, CM_PER_M, V_MAX_M
post=pd.read_csv(A.POST); tbar=gis_tbar()
rs=np.exp(post["gis_slow_ell"].to_numpy())
post["gis_alpha_s"]=post["gis_slow_w"].to_numpy()*rs/tbar
post["gis_beta_s"]=(1.0-post["gis_slow_w"].to_numpy())*rs
S=gis_shape_table(); ibd=(YEARS>=DRIVER_BASE[0])&(YEARS<=DRIVER_BASE[1])
idx={y:int(np.where(YEARS==y)[0][0]) for y in (2015,2100,2150,2250,2300)+A.HIND}
gm,drv={},{}
for ssp,lab,fam,stem in A.ARMS:
    g=pd.read_csv(f"outputs/{stem}.csv").set_index("year")["gmst_spliced"].reindex(YEARS).to_numpy()
    gm[(ssp,fam)]=g-g[ibd].mean(); drv[(ssp,fam)]=regional_driver(gm[(ssp,fam)],post["gis_amp"].to_numpy(),S)
ours={}
for ssp,lab in (("ssp126","SSP1-2.6"),("ssp245","SSP2-4.5"),("ssp585","SSP5-8.5")):
    g=pd.read_csv(f"data/observations/fair_mean_gmst_{ssp}.csv").set_index("year")["gmst_C"].reindex(YEARS).to_numpy()
    ours[lab]=(g-g[ibd].mean(), regional_driver(g-g[ibd].mean(),post["gis_amp"].to_numpy(),S))
tgt=pd.read_csv(A.TARGETS).set_index("year")["gis"]; want=float(tgt.loc[A.HIND[1]]-tgt.loc[A.HIND[0]])
Th=drv[A.HIND_ARM]; lo,hi=np.full(len(post),1e-4),np.full(len(post),1e3)
for _ in range(80):
    mid=np.sqrt(lo*hi); L=basin2_series(Th,post,1.0,mid)
    b=100.0*(L[:,idx[A.HIND[1]]]-L[:,idx[A.HIND[0]]])<want
    lo,hi=np.where(b,mid,lo),np.where(b,hi,mid)
s=np.sqrt(lo*hi)
base={k:np.median(rebase_cm(basin2_series(v,post,1.0,s)),axis=0) for k,v in drv.items()}
base_o={k:np.median(rebase_cm(basin2_series(v[1],post,1.0,s)),axis=0) for k,v in ours.items()}
ann=pd.read_csv("outputs/protect_greenland_gis_annual.csv")
CELLS=[("base (no reservoir)",0.0,0.0,1.0),
       ("A  V=1.0 onset 4.69 tau 800",1.0,4.69,800.0),
       ("B  V=6.0 onset 4.69 tau 2200",6.0,4.69,2200.0),
       ("B' V=3.0 onset 4.69 tau 1100",3.0,4.69,1100.0)]
print(f"RATE at 2250-2300, cm/century, per arm at MATCHED forcing (V_MAX_M={V_MAX_M} m)\n")
print(f"{'cell':30}"+"".join(f"{lab[-3:]+' '+fam[:2]:>11}" for _,lab,fam,_ in A.ARMS)+"   | our ssp585 2300 cm")
row=lambda nm,vals,extra: print(f"{nm:30}"+"".join(f"{v:11.1f}" for v in vals)+f"   | {extra}")
pr=[]
for ssp,lab,fam,_ in A.ARMS:
    q=A.protect_band(ann,lab,fam).groupby("year").gis_cm.median(); pr.append((q[2300]-q[2250])/50*100)
row("PROTECT (target)",pr,"matched p50 98.5")
for nm,V,on,tau in CELLS:
    vals=[]
    for ssp,lab,fam,_ in A.ARMS:
        add=CM_PER_M*V*reservoir_unit(gm[(ssp,fam)],on,tau) if V else np.zeros(len(YEARS))
        L=base[(ssp,fam)]+add; vals.append((L[idx[2300]]-L[idx[2250]])/50*100)
    a5=CM_PER_M*V*reservoir_unit(ours["SSP5-8.5"][0],on,tau) if V else np.zeros(len(YEARS))
    L5=base_o["SSP5-8.5"]+a5
    ac=CM_PER_M*V*reservoir_unit(ours["SSP2-4.5"][0],on,tau) if V else np.zeros(len(YEARS))
    d21=(a5[idx[2100]] if V else 0.0)
    row(nm,vals,f"{L5[idx[2300]]:6.1f}  d2100 {d21:+.4f}  ssp245 dev {ac[idx[2300]]:+.3f}"
        + ("  [V>inventory]" if V>V_MAX_M else ""))
