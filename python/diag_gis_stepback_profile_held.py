"""HOW IDENTIFIED is the (L_inf, tau) split on each held arm? 200 yr of a ~1000 yr
exponential determines the PRODUCT L_inf/tau far better than either factor. Profile
tau, refit L_inf at each, report rmse -- do not let argmax stand in for identification."""
import os,sys
import numpy as np, pandas as pd
REPO=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,os.path.join(REPO,"python")); os.chdir(REPO)
import scope_gis_shape_all_scenarios as A
ann=pd.read_csv("outputs/protect_greenland_gis_annual.csv"); V0=7.42
GSAT={("ssp126","r2300"):1.95,("ssp245","r2300"):2.98,("ssp585","r2300"):5.61}
TAUS=[100,150,218,300,500,995,2000,5000,20000]
for (ssp,fam),T in GSAT.items():
    lab={'ssp126':'SSP1-2.6','ssp245':'SSP2-4.5','ssp585':'SSP5-8.5'}[ssp]
    q=A.protect_band(ann,lab,fam).groupby("year").gis_cm.median()
    q=q[(q.index>=2100)&(q.index<=2300)]; t=q.index.values-2100.0; y=q.values; L0=y[0]
    # ensemble spread as the yardstick for "how much misfit is meaningless"
    d=A.protect_band(ann,lab,fam); sp=d[d.year==2300].gis_cm
    spread=float(sp.quantile(.95)-sp.quantile(.05))
    print(f"\n{lab} {fam}  GSAT {T} K   (p05-p95 spread at 2300 = {spread:.1f} cm)")
    print(f"   {'tau_yr':>8}{'L_inf_cm':>10}{'L_inf/V0':>9}{'L_inf/tau cm/cy':>16}{'rmse_cm':>9}")
    for tau in TAUS:
        b=1.0-np.exp(-t/tau)            # y = L0 + (L_inf-L0)*b  -> least squares in (L_inf-L0)
        A_=b; r=y-L0
        amp=float(A_@r/(A_@A_)); Linf=L0+amp
        rmse=float(np.sqrt(np.mean((L0+amp*b-y)**2)))
        print(f"   {tau:8d}{Linf:10.1f}{Linf/(V0*100):9.3f}{Linf/tau*100:16.1f}{rmse:9.3f}")
