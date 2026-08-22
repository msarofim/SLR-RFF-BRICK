"""ARITHMETIC PRE-CHECK, no scan. If the LINEAR commitment law cannot reach an arm's
2300 median even at phi = 1 (fully equilibrated), then NO rate law -- gamma, a longer
tau, a different r(T) -- can fix that arm. Compute the phi=1 ceiling per arm, per draw,
on the model's own rebased basis."""
import os,sys
import numpy as np, pandas as pd
REPO=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,os.path.join(REPO,"python")); os.chdir(REPO)
import scope_gis_shape_all_scenarios as A
from scope_gis_ridge_vs_protect import basin2_series, rebase_cm, K_SOUTH, K_HIGH, GIS_V0_M
from scope_gis_leq_ridge_vs_literature import gis_tbar
from scope_gis_2300_relaxation import DRIVER_BASE, YEARS, gis_shape_table, regional_driver
post=pd.read_csv(A.POST); tbar=gis_tbar()
rs=np.exp(post["gis_slow_ell"].to_numpy())
post["gis_alpha_s"]=post["gis_slow_w"].to_numpy()*rs/tbar
post["gis_beta_s"]=(1.0-post["gis_slow_w"].to_numpy())*rs
S=gis_shape_table(); ibd=(YEARS>=DRIVER_BASE[0])&(YEARS<=DRIVER_BASE[1])
i15=int(np.where(YEARS==2015)[0][0]); i23=int(np.where(YEARS==2300)[0][0])
ann=pd.read_csv("outputs/protect_greenland_gis_annual.csv")
c1=post["gis_c1"].to_numpy(); c0=post["gis_c0"].to_numpy()
print(f"{'arm':24}{'GSAT@2300':>10}{'phi=1 ceiling':>15}{'PROTECT median':>16}{'ratio':>9}")
for ssp,lab,fam,stem in A.ARMS:
    g=pd.read_csv(f"outputs/{stem}.csv").set_index("year")["gmst_spliced"].reindex(YEARS).to_numpy()
    T=regional_driver(g-g[ibd].mean(),post["gis_amp"].to_numpy(),S)
    # phi=1 ceiling: BOTH basins fully equilibrated at the 2300 driver, minus the 2015 level
    ceil=np.zeros(len(post))
    for kb in (K_SOUTH,K_HIGH):
        ceil+=np.clip(kb*(c1*T[:,i23]+c0),0.0,kb*GIS_V0_M)
    L15=np.zeros(len(post))
    for kb in (K_SOUTH,K_HIGH):
        L15+=np.clip(kb*(c1*T[:,i15]+c0),0.0,kb*GIS_V0_M)
    # rebase: the model reports rel the 1995-2014 mean; use the 2015 EQUILIBRIUM level as
    # a conservative (i.e. ceiling-FAVOURING) proxy for what is subtracted
    top=100.0*np.median(ceil-L15)
    med=float(A.protect_band(ann,lab,fam).groupby("year").gis_cm.median()[2300])
    print(f"{lab+' '+fam:24}{g[i23]:10.2f}{top:15.1f}{med:16.1f}{med/top:8.2f}x")
print("\nratio > 1 => the arm's own 2300 median is ABOVE what the LINEAR commitment law")
print("can deliver even at phi = 1. For those arms the defect is the COMMITMENT law and")
print("no rate law can reach them.")
