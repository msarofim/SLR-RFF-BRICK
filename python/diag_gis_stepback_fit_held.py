"""What (L_inf, tau) pair does each HELD-forcing PROTECT arm imply, if you insist on
ONE exponential? Fit 2100-2300 annual median; report the fit AND its misfit, because
the misfit is the point (a single exponential is what we are testing, not assuming)."""
import os,sys
import numpy as np, pandas as pd
from scipy.optimize import curve_fit
REPO=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,os.path.join(REPO,"python")); os.chdir(REPO)
import scope_gis_shape_all_scenarios as A
ann=pd.read_csv("outputs/protect_greenland_gis_annual.csv")
V0=7.42
GSAT={("ssp126","r2300"):1.95,("ssp245","r2300"):2.98,("ssp585","r2300"):5.61}
print("ONE-EXPONENTIAL FIT to each HELD arm, 2100-2300 annual median (cm rel 2015)")
print(f"{'arm':16}{'GSAT':>6}{'L2100':>8}{'L_inf':>9}{'L_inf/V0':>9}{'tau_yr':>9}{'rmse_cm':>9}  {'L_inf/tau (cm/century)':>22}")
for (ssp,fam),T in GSAT.items():
    lab={'ssp126':'SSP1-2.6','ssp245':'SSP2-4.5','ssp585':'SSP5-8.5'}[ssp]
    q=A.protect_band(ann,lab,fam).groupby("year").gis_cm.median()
    q=q[(q.index>=2100)&(q.index<=2300)]
    t=q.index.values-2100.0; y=q.values; L0=y[0]
    f=lambda t,Linf,tau: Linf-(Linf-L0)*np.exp(-t/tau)
    try:
        p,_=curve_fit(f,t,y,p0=[y[-1]*2,300],maxfev=40000,bounds=([L0,10],[V0*100,1e5]))
    except Exception as e:
        print(lab,fam,"fit failed",e); continue
    Linf,tau=p; res=np.sqrt(np.mean((f(t,*p)-y)**2))
    print(f"{lab+' '+fam:16}{T:6.2f}{L0:8.1f}{Linf:9.1f}{Linf/(V0*100):9.3f}{tau:9.0f}{res:9.3f}  {Linf/tau*100:22.1f}")
print()
print("OUR MODEL for comparison: L_eq(T) = c1*(amp*GSAT) + c0, amp=1.9, c1=0.046 m/K, c0=0.061 m")
for T in (1.95,2.98,5.61,13.63):
    Leq=0.046*1.9*T+0.061
    print(f"   GSAT {T:5.2f} K -> our committed loss {Leq*100:6.1f} cm = {Leq/V0:.3f} of the sheet")
