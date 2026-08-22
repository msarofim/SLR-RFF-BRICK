"""EXPLORATORY diagnosis figure -- writes only to the scratchpad, nothing to the repo.
All labels derive from the named constants below."""
import os,sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
REPO=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRATCH=os.path.join(REPO,"outputs")
sys.path.insert(0,os.path.join(REPO,"python")); os.chdir(REPO)
import scope_gis_shape_all_scenarios as A
from scope_gis_ridge_vs_protect import basin2_series, rebase_cm
from scope_gis_leq_ridge_vs_literature import gis_tbar
from scope_gis_2300_relaxation import DRIVER_BASE, YEARS, gis_shape_table, regional_driver

TAG="L14"; V0_CM=742.0; AMP=1.9; C1,C0=0.046,0.061      # posterior medians, m/K and m
SRC="PROTECT-Greenland (Goelzer 2025, NORCE-CISM), rel 2015"
WIN=[(2050,2100),(2100,2150),(2150,2200),(2200,2250),(2250,2300)]
COL={"SSP1-2.6":"#2c7fb8","SSP2-4.5":"#f0a202","SSP5-8.5":"#d7191c"}

post=pd.read_csv(A.POST); tbar=gis_tbar()
rs=np.exp(post["gis_slow_ell"].to_numpy())
post["gis_alpha_s"]=post["gis_slow_w"].to_numpy()*rs/tbar
post["gis_beta_s"]=(1.0-post["gis_slow_w"].to_numpy())*rs
S=gis_shape_table(); ibd=(YEARS>=DRIVER_BASE[0])&(YEARS<=DRIVER_BASE[1])
drv={}
for ssp,lab,fam,stem in A.ARMS:
    g=pd.read_csv(f"outputs/{stem}.csv").set_index("year")["gmst_spliced"].reindex(YEARS).to_numpy()
    drv[(ssp,fam)]=regional_driver(g-g[ibd].mean(),post["gis_amp"].to_numpy(),S)
idx={y:int(np.where(YEARS==y)[0][0]) for y in list(range(2050,2301,50))+list(A.HIND)}
tgt=pd.read_csv(A.TARGETS).set_index("year")["gis"]
want=float(tgt.loc[A.HIND[1]]-tgt.loc[A.HIND[0]]); Th=drv[A.HIND_ARM]
lo,hi=np.full(len(post),1e-4),np.full(len(post),1e3)
for _ in range(80):
    mid=np.sqrt(lo*hi); L=basin2_series(Th,post,1.0,mid)
    b=100.0*(L[:,idx[A.HIND[1]]]-L[:,idx[A.HIND[0]]])<want
    lo,hi=np.where(b,mid,lo),np.where(b,hi,mid)
s=np.sqrt(lo*hi)
ann=pd.read_csv("outputs/protect_greenland_gis_annual.csv")
GS={}
rates_p,rates_o,taus_p,taus_o={},{},{},{}
for ssp,lab,fam,stem in A.ARMS:
    g=pd.read_csv(f"outputs/{stem}.csv").set_index("year")["gmst_spliced"]
    GS[(ssp,fam)]=float(g.loc[2300])
    q=A.protect_band(ann,lab,fam).groupby("year").gis_cm.median()
    m=np.median(rebase_cm(basin2_series(drv[(ssp,fam)],post,1.0,s)),axis=0)
    o={y:m[idx[y]] for y in range(2050,2301,50)}
    rates_p[(ssp,fam)]=[(q[b]-q[a])/50*100 for a,b in WIN]
    rates_o[(ssp,fam)]=[(o[b]-o[a])/50*100 for a,b in WIN]
    def tau(r):
        out=[]
        for i in range(1,len(r)-1):
            f=r[i+1]/r[i] if r[i]>0 else np.nan
            out.append(-50/np.log(f) if (f==f and 0<f<1) else np.nan)
        return out
    taus_p[(ssp,fam)]=tau(rates_p[(ssp,fam)]); taus_o[(ssp,fam)]=tau(rates_o[(ssp,fam)])

fig,ax=plt.subplots(2,2,figsize=(13.5,9.5))
x=[(a+b)/2 for a,b in WIN]
for (ssp,fam),r in rates_p.items():
    lab={'ssp126':'SSP1-2.6','ssp245':'SSP2-4.5','ssp585':'SSP5-8.5'}[ssp]
    ls="-" if fam=="r2300" else "--"
    ax[0,0].plot(x,r,ls,color=COL[lab],lw=2.2,marker="o",ms=4)
    ax[0,0].plot(x,rates_o[(ssp,fam)],ls,color=COL[lab],lw=1.4,marker="x",ms=6,alpha=.55)
ax[0,0].set_yscale("log"); ax[0,0].set_ylabel("rate of loss, cm SLE / century")
ax[0,0].set_xlabel("centre of 50-yr window")
ax[0,0].set_title("A. Rate of loss: thick+o = PROTECT, thin+x = Ladrillo $L14$ (k=1)\n"
                  "solid = forcing HELD after 2100 (r2300), dashed = extended (x2300)",fontsize=10)
ax[0,0].axvline(2100,color="k",lw=.7,ls=":")
for lab,c in COL.items(): ax[0,0].plot([],[],color=c,lw=2,label=lab)
ax[0,0].legend(fontsize=8,loc="lower left")

# B. tau_eff vs arm temperature, held arms only
for (ssp,fam) in taus_p:
    if fam!="r2300": continue
    lab={'ssp126':'SSP1-2.6','ssp245':'SSP2-4.5','ssp585':'SSP5-8.5'}[ssp]
    T=GS[(ssp,fam)]
    ax[0,1].plot([T]*len(taus_p[(ssp,fam)]),taus_p[(ssp,fam)],"o",color=COL[lab],ms=9)
    ax[0,1].plot([T]*len(taus_o[(ssp,fam)]),taus_o[(ssp,fam)],"x",color=COL[lab],ms=10,mew=2)
ax[0,1].set_yscale("log"); ax[0,1].set_xlabel("GSAT at 2300, K (held-forcing arms)")
ax[0,1].set_ylabel(r"effective relaxation timescale $\tau_{eff}$, yr")
ax[0,1].set_title(r"B. $\tau_{eff}$ from the decay of the rate under HELD forcing"
                  "\n"r"o = PROTECT (rises with T), x = Ladrillo (FALLS with T)",fontsize=10)
ax[0,1].grid(alpha=.3)

# C. commitment curve
T=np.linspace(0,10,300)
ax[1,0].plot(T,(C1*AMP*T+C0)*100,color="k",lw=2,label="Ladrillo L14: $L_{eq}=c_1(1.9T)+c_0$ (LINEAR)")
Tc,q=8.075,3.281
ax[1,0].plot(T,V0_CM*(1-np.exp(-(T/Tc)**q)),color="#4daf4a",lw=2,
             label=f"fitted to the 5 arms: $V_0(1-e^{{-(T/{Tc:.1f})^{{{q:.1f}}}}})$")
for TT,L,lo_,hi_ in ((1.95,15.4,11.3,186),(2.98,21.4,15.7,264),(5.61,320,100,1456)):
    ax[1,0].plot([TT],[L],"s",color="#d7191c",ms=8)
    ax[1,0].vlines(TT,lo_,hi_,color="#d7191c",lw=3,alpha=.35)
ax[1,0].plot([],[],"s",color="#d7191c",ms=8,
             label=r"per-arm 1-exponential fit; bar = $\tau$ profile 100-5000 yr")
ax[1,0].set_yscale("log"); ax[1,0].set_ylim(1,1500)
ax[1,0].axhline(V0_CM,color="grey",ls=":",lw=1); ax[1,0].text(0.15,V0_CM*1.05,"whole ice sheet",fontsize=8,color="grey")
ax[1,0].set_xlabel("sustained GSAT anomaly, K"); ax[1,0].set_ylabel("committed loss, cm SLE")
ax[1,0].set_title("C. The committed-loss law. Ladrillo's is LINEAR in T;\n"
                  "the arms want something strongly convex",fontsize=10)
ax[1,0].legend(fontsize=8,loc="upper left")

# D. identifiability surface
qs=(1.5,2,2.5,3,4,6); Tcs=(2.0,3.0,4.0,6.0,8.0,12.0,20.0)
Z=np.array([[75.00,73.37,71.36,69.20,64.82,57.10],[74.44,71.92,68.71,65.11,57.44,43.83],
            [73.87,70.41,65.84,60.49,48.65,36.30],[72.71,67.18,59.31,49.40,32.19,156.87],
            [71.52,63.65,51.58,36.46,75.70,296.47],[69.06,55.59,34.86,66.68,264.69,357.06],
            [63.83,41.57,100.67,123.76,160.81,185.61]])
F=np.array([[100*(1-np.exp(-(5.0/tc)**qq)) for qq in qs] for tc in Tcs])
im=ax[1,1].pcolormesh(range(len(qs)),range(len(Tcs)),np.log10(Z),cmap="viridis_r",shading="nearest")
for i,tc in enumerate(Tcs):
    for j,qq in enumerate(qs):
        ax[1,1].text(j,i,f"{F[i,j]:.0f}%",ha="center",va="center",fontsize=8,
                     color="w" if np.log10(Z[i,j])>1.75 else "k")
ax[1,1].set_xticks(range(len(qs)),[str(v) for v in qs]); ax[1,1].set_yticks(range(len(Tcs)),[str(v) for v in Tcs])
ax[1,1].set_xlabel("q (curvature of the commitment law)"); ax[1,1].set_ylabel("$T_c$, K")
ax[1,1].set_title("D. NON-IDENTIFICATION. Colour = misfit to all 5 arms (c refit at every\n"
                  "node); labels = committed fraction at 5 K. Near-equal fits span 3%-100%.",fontsize=10)
plt.colorbar(im,ax=ax[1,1],label="$\\log_{10}$ misfit")
fig.suptitle(f"Greenland: what the five matched-forcing arms actually say   |   "
             f"model {TAG}, targets {SRC}",fontsize=12)
fig.tight_layout(rect=[0,0,1,0.965])
out=os.path.join(SCRATCH,"greenland_shape_diagnosis.png")
fig.savefig(out,dpi=145); print("wrote",out)
