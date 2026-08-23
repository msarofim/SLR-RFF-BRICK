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

---- 2026-08-23: THE CELL LIST GAINS A STAGE COUNT --------------------------------
The first-order FORM is refuted (an n-fold-repeated-integral bound caps its delivery
ratio at 2.89 against the 6.03 the joint 2150/2300 constraint needs), and the SHIPPED
cell is now a 2-STAGE CASCADE: V=6.0 m, onset 4.69 K, tau 800 yr, whole-sheet. The
rate criterion is one of the TWO independent sources that pinned the flux and it had
never been evaluated for n = 2 -- psi = 100*V/tau is a FIRST-ORDER parameterisation
and does not carry over.

  --cells=legacy   (DEFAULT) the four first-order cells above, BYTE-IDENTICAL to
                   every earlier run of this script. The 2026-08-22c verdict rests
                   on it and stays checkable.
  --cells=shipped  the shipped cascade, plus the base and the two n=1 contenders,
                   so the comparison is like-for-like inside one table.

psi IS REPORTED AS MEASURED, NOT AS A FORMULA. The `psi_eff` column is the
RESERVOIR'S OWN 2250-2300 rate contribution in cm/century, read off the trajectory --
form-agnostic, and the only version of the quantity that means the same thing at n=1
and n=2. The closed-form 100*V/tau is printed BESIDE it for the n=1 cells only, where
it is defined; the gap between the two columns is exactly what does not carry over.
"""
import os,sys
import numpy as np, pandas as pd
REPO=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,os.path.join(REPO,"python")); os.chdir(REPO)
import scope_gis_shape_all_scenarios as A
from scope_gis_ridge_vs_protect import basin2_series, rebase_cm
from scope_gis_leq_ridge_vs_literature import gis_tbar
from scope_gis_2300_relaxation import DRIVER_BASE, YEARS, gis_shape_table, regional_driver
from scope_gis_reservoir_offline import (reservoir_unit, reservoir_unit_n,
                                         CM_PER_M, V_MAX_M)

## THE ARM IS IN THE BANNER AND IN EVERY LABEL. A legacy run and a shipped run differ
## in which cells exist, and both print the same table shape.
CELLSET = "legacy"
for _a in sys.argv[1:]:
    if _a.startswith("--cells="):
        CELLSET = _a.split("=", 1)[1]
if CELLSET not in ("legacy", "shipped"):
    sys.exit(f"--cells must be legacy or shipped, got {CELLSET!r}")


def unit(gmt, onset, tau, stages):
    """stages = 1 dispatches to `reservoir_unit` itself, not to reservoir_unit_n's
    n=1 case, so the legacy arm is byte-identical by CONSTRUCTION rather than by a
    claim that the two agree."""
    return (reservoir_unit(gmt, onset, tau) if stages == 1
            else reservoir_unit_n(gmt, onset, tau, stages=stages))
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
LEGACY=[("base (no reservoir)",0.0,0.0,1.0,1),
        ("A  V=1.0 onset 4.69 tau 800",1.0,4.69,800.0,1),
        ("B  V=6.0 onset 4.69 tau 2200",6.0,4.69,2200.0,1),
        ("B' V=3.0 onset 4.69 tau 1100",3.0,4.69,1100.0,1)]
## The shipped arm keeps the base and both n=1 contenders so the cascade is read
## against the cells the earlier verdict was written about, not against nothing.
SHIPPED=[("base (no reservoir)",0.0,0.0,1.0,1),
         ("A  V=1.0 onset 4.69 tau  800 n=1",1.0,4.69,800.0,1),
         ("B  V=6.0 onset 4.69 tau 2200 n=1",6.0,4.69,2200.0,1),
         ("SHIPPED V=6.0 onset 4.69 tau 800 n=2",6.0,4.69,800.0,2)]
CELLS=LEGACY if CELLSET=="legacy" else SHIPPED
print(f"RATE at 2250-2300, cm/century, per arm at MATCHED forcing (V_MAX_M={V_MAX_M} m)")
if CELLSET!="legacy":
    print(f"cells: {CELLSET}   psi_eff = the RESERVOIR'S OWN 2250-2300 rate, cm/century "
          f"(measured); 100V/tau is printed only where it is defined (n=1)")
print()
w=36 if CELLSET!="legacy" else 30
print(f"{'cell':{w}}"+"".join(f"{lab[-3:]+' '+fam[:2]:>11}" for _,lab,fam,_ in A.ARMS)+"   | our ssp585 2300 cm")
row=lambda nm,vals,extra: print(f"{nm:{w}}"+"".join(f"{v:11.1f}" for v in vals)+f"   | {extra}")
pr=[]
for ssp,lab,fam,_ in A.ARMS:
    q=A.protect_band(ann,lab,fam).groupby("year").gis_cm.median(); pr.append((q[2300]-q[2250])/50*100)
row("PROTECT (target)",pr,"matched p50 98.5")
for nm,V,on,tau,ns in CELLS:
    vals=[]
    for ssp,lab,fam,_ in A.ARMS:
        add=CM_PER_M*V*unit(gm[(ssp,fam)],on,tau,ns) if V else np.zeros(len(YEARS))
        L=base[(ssp,fam)]+add; vals.append((L[idx[2300]]-L[idx[2250]])/50*100)
    a5=CM_PER_M*V*unit(ours["SSP5-8.5"][0],on,tau,ns) if V else np.zeros(len(YEARS))
    L5=base_o["SSP5-8.5"]+a5
    ac=CM_PER_M*V*unit(ours["SSP2-4.5"][0],on,tau,ns) if V else np.zeros(len(YEARS))
    d21=(a5[idx[2100]] if V else 0.0)
    extra=f"{L5[idx[2300]]:6.1f}  d2100 {d21:+.4f}  ssp245 dev {ac[idx[2300]]:+.3f}"
    if CELLSET!="legacy":
        ## psi_eff on OUR ssp585, the deliverable's own forcing -- the same series the
        ## 2300 level in this row is read from, so the two cannot be about different arms.
        psi_eff=(a5[idx[2300]]-a5[idx[2250]])/50*100
        cf=f"{100.0*V/tau:6.3f}" if (ns==1 and V) else "     -"
        extra+=f"  psi_eff {psi_eff:6.3f}  100V/tau {cf}"
    row(nm,vals,extra+("  [V>inventory]" if V>V_MAX_M else ""))
