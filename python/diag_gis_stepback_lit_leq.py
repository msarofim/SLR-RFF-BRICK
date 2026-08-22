"""THE TEST THE IDENTIFIABILITY RESULT DEMANDS: stop fitting L_eq, take it from the
equilibrium literature (Bochow 2023, already tracked), and fit ONLY the melt constant c.

  dL/dt = c * (T(t) - Theta(L))_+ ,   Theta = Leq^{-1},  Leq = the Bochow ladder

WHY THIS IS NOT OPTION C. gis_offline_cell.py:25-32 records why A+B+C -- the SAME
Bochow ladder inside a PROPORTIONAL relaxation -- destroyed the fit: "as L_eq grows
20x the proportional rate grows with it", hindcast RMSE 1.675, 72 cm at 2100. In the
T-space form the rate does NOT scale with L_eq; it scales with the temperature excess
over the ice sheet's OWN current equilibrium temperature. L_eq enters through Theta
only. So the 742 cm post-threshold commitment cannot leak into the hindcast, which is
precisely the obstruction that killed option C.
And it is not option D either: D capped the flux at a CONSTANT q, which made L_eq
algebraically irrelevant. Here the cap is c*(T-Theta) -- temperature-dependent AND
L_eq-dependent.
"""
import os,sys
import numpy as np, pandas as pd
from scipy.optimize import minimize_scalar
REPO=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,os.path.join(REPO,"python")); os.chdir(REPO)
import scope_gis_shape_all_scenarios as A
LAD=pd.read_csv("data/observations/greenland_equilibrium_bochow2023.csv")
ann=pd.read_csv("outputs/protect_greenland_gis_annual.csv")
tgt=pd.read_csv("outputs/recalib_targets_ext.csv").set_index("year")["gis"]
YR=np.arange(1900,2301)
## the model integrates TOTAL loss from 1900; PROTECT and the target are rel 2015 and
## rel 1995-2005 respectively, so both are compared as DIFFERENCES, never as levels.
def theta_of(L_cm, lad):
    g=lad["gmt_K"].to_numpy(); l=lad["loss_m_sle"].to_numpy()*100.0
    return np.interp(L_cm, l, g, left=g[0], right=g[-1])
def run(c, T, lad):
    L=np.zeros(len(T))
    for i in range(1,len(T)):
        L[i]=L[i-1]+c*max(T[i-1]-theta_of(L[i-1],lad),0.0)
    return L
hist=pd.read_csv("outputs/protect_r2300_forcing_gmst.csv").set_index("year")["gmst_spliced"]
arms=[]
for ssp,lab,fam,stem in A.ARMS:
    g=pd.read_csv(f"outputs/{stem}.csv").set_index("year")["gmst_spliced"].reindex(YR).to_numpy()
    y=A.protect_band(ann,lab,fam).groupby("year").gis_cm.median().reindex(YR).to_numpy()
    arms.append((f"{lab} {fam}", g, y))
i15=int(np.where(YR==2015)[0][0]); i00=int(np.where(YR==1900)[0][0]); i25=int(np.where(YR==2025)[0][0])
want_hist=float(tgt.loc[2025]-tgt.loc[1900])
for mdl,lad in LAD.groupby("model"):
    lad=lad.sort_values("gmt_K")
    def cost(lc):
        c=np.exp(lc); s=0.0
        for nm,g,y in arms:
            L=run(c,g,lad); d=L-L[i15]; m=~np.isnan(y)
            s+=np.nanmean(((d[m]-y[m])/max(np.nanmax(y[m]),1.0))**2)
        return s
    r=minimize_scalar(cost,bounds=(np.log(1e-4),np.log(5)),method="bounded")
    c=float(np.exp(r.x))
    Lh=run(c,hist.reindex(YR).to_numpy(),lad)
    print(f"\n=== Leq FIXED to {mdl} (equilibrium: {lad.loss_frac_of_volume.iloc[-1]*100:.0f}% of the "
          f"sheet at {lad.gmt_K.iloc[-1]:.1f} K) ===")
    print(f"    c fitted to the 5 arms = {c:.4f} cm/yr/K   (history alone gives 0.107)")
    print(f"    HINDCAST 1900-2025: model {Lh[i25]-Lh[i00]:.2f} cm vs observed {want_hist:.2f} cm "
          f"-> {(Lh[i25]-Lh[i00])/want_hist:.2f}x   [option C broke this: RMSE 1.675 cm]")
    print(f"    {'arm':24}{'2100':>15}{'2200':>15}{'2300':>15}  (model/PROTECT, cm rel 2015)")
    for nm,g,y in arms:
        L=run(c,g,lad); d=L-L[i15]
        ix={v:int(np.where(YR==v)[0][0]) for v in (2100,2200,2300)}
        print(f"    {nm:24}"+"".join(f"{d[ix[v]]:8.1f}/{y[ix[v]]:<6.1f}" for v in (2100,2200,2300)))
