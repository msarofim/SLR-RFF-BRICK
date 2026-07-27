"""
plot_component_hindcast.py — 5-panel component validation figure for the walkthrough.
BRICK-AM (extA108) and BRICK 2.0 (Wong) posterior p5-p95 bands + p50, overlaid on the
reconciled observations (outputs/recalib_targets_ext.csv), per SLR component. Both models
on the common FaIR-mean SSP2-4.5 forcing (outputs/component_hindcast_bands.csv). cm rel 1995-2005.
"""
import pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

REPO="/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK"
B=pd.read_csv(f"{REPO}/outputs/component_hindcast_bands.csv")
O=pd.read_csv(f"{REPO}/outputs/recalib_targets_ext.csv")

# component -> (title, obs column in recalib_targets_ext.csv)
PANELS=[("ais","Antarctic ice sheet (AIS)","ais"),
        ("gis","Greenland ice sheet (GIS)","gis"),
        ("gsic","Glaciers & small ice caps","gsic"),
        ("te","Thermal expansion (steric)","steric"),
        ("total","Total GMSL","dang")]
C_AM="#b2603b"; C_20="#0d7c8c"; C_OBS="#333333"
X0,X1=1900,2024

fig,axes=plt.subplots(3,2,figsize=(8.6,10.4)); axes=axes.ravel()
for ax,(comp,title,ocol) in zip(axes,PANELS):
    # observations + band
    if ocol in O.columns:
        o=O[["year",ocol,f"{ocol}_lo",f"{ocol}_hi"]].dropna()
        o=o[(o.year>=X0)&(o.year<=X1)]
        ax.fill_between(o.year,o[f"{ocol}_lo"],o[f"{ocol}_hi"],color=C_OBS,alpha=0.18,lw=0,zorder=1)
        ax.plot(o.year,o[ocol],color=C_OBS,lw=1.6,zorder=4,label="Observations")
    # model bands
    for lab,col in [("BRICK2.0",C_20),("BRICK-AM",C_AM)]:
        d=B[(B.model==lab)&(B.component==comp)]; d=d[(d.year>=X0)&(d.year<=X1)]
        ax.fill_between(d.year,d.p5,d.p95,color=col,alpha=0.16,lw=0,zorder=2)
        ax.plot(d.year,d.p50,color=col,lw=1.7,zorder=3)
    ax.set_title(title,fontsize=10.5,fontweight="600")
    ax.set_xlim(X0,X1); ax.axhline(0,color="#bbb",lw=0.6,zorder=0)
    ax.set_ylabel("cm (rel. 1995–2005)",fontsize=8.5); ax.tick_params(labelsize=8)
    ax.grid(True,alpha=0.18,lw=0.5)

# legend in the 6th cell
axL=axes[5]; axL.axis("off")
handles=[Line2D([],[],color=C_OBS,lw=1.8,label="Observations (reconciled targets)"),
         Patch(facecolor=C_OBS,alpha=0.18,label="obs 90% band"),
         Line2D([],[],color=C_AM,lw=1.8,label="BRICK-AM  (median)"),
         Patch(facecolor=C_AM,alpha=0.16,label="BRICK-AM  5–95%"),
         Line2D([],[],color=C_20,lw=1.8,label="BRICK 2.0  (median)"),
         Patch(facecolor=C_20,alpha=0.16,label="BRICK 2.0  5–95%")]
axL.legend(handles=handles,loc="center",fontsize=10,frameon=False,title="Both models on FaIR-mean SSP2-4.5 forcing",title_fontsize=10)
fig.suptitle("Component hindcasts vs the reconciled observations — BRICK-AM and BRICK 2.0",
             fontsize=12.5,fontweight="700",y=0.99)
fig.tight_layout(rect=[0,0,1,0.97])
out=f"{REPO}/notes/fig_component_hindcast.png"
fig.savefig(out,dpi=160,bbox_inches="tight")
print("wrote",out)
# quick numeric check: 2018 medians vs obs
for comp,title,ocol in PANELS:
    try:
        am=float(B[(B.model=='BRICK-AM')&(B.component==comp)&(B.year==2018)].p50)
        w2=float(B[(B.model=='BRICK2.0')&(B.component==comp)&(B.year==2018)].p50)
        ob=float(O[O.year==2018][ocol]) if ocol in O.columns else float('nan')
        print(f"  {comp:6} @2018: obs {ob:6.2f} | BRICK-AM {am:6.2f} | BRICK2.0 {w2:6.2f} cm")
    except Exception as e:
        print(f"  {comp}: {e}")
