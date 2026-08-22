"""Is 'history and PROTECT want the same c' a real out-of-sample agreement, or is it
driven by the COOL arms, which sit near the historical temperature anyway? Fit c
per arm at the joint (Tc,q) and see whether the WARM arms -- 4-10x hotter than
anything in the record -- independently land on the same constant."""
import os,sys
import numpy as np, pandas as pd
from scipy.optimize import minimize_scalar
REPO=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,os.path.join(REPO,"python")); os.chdir(REPO)
import scope_gis_shape_all_scenarios as A
V0_CM=742.0; Tc,q=8.075,3.281
ann=pd.read_csv("outputs/protect_greenland_gis_annual.csv")
def run(c,T):
    L=np.zeros_like(T)
    for i in range(1,len(T)):
        f=min(max(L[i-1]/V0_CM,0.0),0.999999)
        Th=Tc*(-np.log(1.0-f))**(1.0/q) if f>0 else 0.0
        L[i]=L[i-1]+c*max(T[i-1]-Th,0.0)
    return L
yr=np.arange(2015,2301)
print(f"joint (Tc,q) = ({Tc:.2f} K, {q:.2f}); c refit to EACH ARM ALONE\n")
print(f"{'arm':24}{'GSAT@2300':>10}{'c (cm/yr/K)':>13}{'vs history 0.107':>18}")
for ssp,lab,fam,stem in A.ARMS:
    T=pd.read_csv(f"outputs/{stem}.csv").set_index("year")["gmst_spliced"].reindex(yr).to_numpy()
    y=A.protect_band(ann,lab,fam).groupby("year").gis_cm.median().reindex(yr).to_numpy()
    f=lambda lc: float(np.sum((run(np.exp(lc),T)-y)**2))
    r=minimize_scalar(f,bounds=(np.log(1e-4),np.log(10)),method="bounded")
    c=np.exp(r.x)
    print(f"{lab+' '+fam:24}{T[-1]:10.2f}{c:13.4f}{c/0.1067:17.2f}x")
