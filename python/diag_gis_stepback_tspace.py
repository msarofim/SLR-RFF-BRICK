"""EXPLORATORY, offline, writes nothing to the repo.

TEST OF A FUNCTIONAL FORM. Hypothesis: Greenland loss is a relaxation in TEMPERATURE
space, not in volume space --

    dL/dt = c * ( T(t) - Theta(L) )_+ ,     Theta = Leq^{-1}

with ONE rate constant c and ONE equilibrium curve Leq(T). This STRICTLY NESTS the
shipped model: if Leq(T) = c1*T + c0 then Theta(L) = (L-c0)/c1 and the equation
collapses to dL/dt = (c/c1)*(Leq - L), a fixed-tau relaxation with tau = c1/c. So the
shipped model is the LINEAR-Leq special case, and its fixed tau is a CONSEQUENCE of
that linearity, not an independent assumption.

The prediction that makes it testable: tau_eff(T) = Leq'(T)/c. A sigmoidal Leq gives a
SHORT tau where the curve is flat (cool), a LONG tau on the steep limb, and a SHORT tau
again once it saturates -- which is the non-monotone tau_eff the five arms show
(218 yr at 2-3 K, ~1000+ yr at 5.6 K, back to <=350 yr at 13.6 K).

Leq(T) = V0 * (1 - exp(-(T/Tc)^q)).  Three parameters: c, Tc, q.
Fit to all five arms' MEDIAN annual trajectories, 2015-2300, on each arm's OWN GSAT.
"""
import os,sys
import numpy as np, pandas as pd
from scipy.optimize import least_squares
REPO=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,os.path.join(REPO,"python")); os.chdir(REPO)
import scope_gis_shape_all_scenarios as A

V0_CM=742.0
ann=pd.read_csv("outputs/protect_greenland_gis_annual.csv")
arms=[]
for ssp,lab,fam,stem in A.ARMS:
    g=pd.read_csv(f"outputs/{stem}.csv").set_index("year")["gmst_spliced"]
    y=A.protect_band(ann,lab,fam).groupby("year").gis_cm.median()
    yr=np.arange(2015,2301)
    arms.append((f"{lab} {fam}", g.reindex(yr).to_numpy(), y.reindex(yr).to_numpy(), yr))

def run(c,Tc,q,T):
    L=np.zeros_like(T)
    for i in range(1,len(T)):
        frac=min(max(L[i-1]/V0_CM,0.0),0.999999)
        Th=Tc*(-np.log(1.0-frac))**(1.0/q) if frac>0 else 0.0
        L[i]=L[i-1]+c*max(T[i-1]-Th,0.0)
    return L

def resid_fixed(c,Tc,q):
    return np.concatenate([(run(c,Tc,q,T)-y)/max(np.nanmax(y),1.0) for nm,T,y,yr in arms])


def resid(p):
    c,Tc,q=np.exp(p)
    r=[]
    for nm,T,y,yr in arms:
        L=run(c,Tc,q,T)
        r.append((L-y)/max(np.nanmax(y),1.0))   # per-arm relative, so 13.6 K does not dominate
    return np.concatenate(r)

best=None
for p0 in ([np.log(0.1),np.log(4.0),np.log(2.0)],[np.log(0.05),np.log(3.0),np.log(3.0)],
           [np.log(0.2),np.log(6.0),np.log(1.5)],[np.log(0.02),np.log(2.5),np.log(4.0)]):
    s=least_squares(resid,p0,method="lm",max_nfev=20000)
    if best is None or s.cost<best.cost: best=s
c,Tc,q=np.exp(best.x)
print(f"FIT: c = {c:.4f} cm/yr/K   Tc = {Tc:.3f} K   q = {q:.3f}   (cost {best.cost:.4g})\n")
print(f"{'arm':22}{'2100':>16}{'2150':>16}{'2200':>16}{'2300':>16}   (fit vs PROTECT median, cm)")
for nm,T,y,yr in arms:
    L=run(c,Tc,q,T); ix={v:int(np.where(yr==v)[0][0]) for v in (2100,2150,2200,2300)}
    print(f"{nm:22}"+"".join(f"{L[ix[v]]:8.1f}/{y[ix[v]]:<7.1f}" for v in (2100,2150,2200,2300)))
print()
print("IMPLIED EQUILIBRIUM CURVE  Leq(T) = V0*(1-exp(-(T/Tc)^q)):")
for T in (1.5,2,2.5,3,4,5,6,8,10):
    print(f"   {T:5.1f} K -> {V0_CM*(1-np.exp(-(T/Tc)**q)):7.1f} cm "
          f"= {(1-np.exp(-(T/Tc)**q))*100:5.1f}% of the sheet")
print()
print("IMPLIED tau_eff(T) = Leq'(T)/c   [the testable prediction]:")
for T in (2,3,4,5,5.6,8,13.6):
    d=V0_CM*np.exp(-(T/Tc)**q)*q*(T/Tc)**(q-1)/Tc
    print(f"   {T:5.1f} K -> tau_eff {d/c:8.0f} yr")

# ---- IDENTIFIABILITY: how much of Leq do 285 yr of transient actually see? -----
print("\n=== (Tc,q) GRID with c REFIT at every node. cost, and the committed fraction")
print("=== at 5 K each node implies. If the cost is flat across very different Leq")
print("=== curves, PROTECT does NOT identify the equilibrium curve and the literature")
print("=== has to supply it. [profile, not argmax]")
from scipy.optimize import minimize_scalar
hdr=f"{'Tc\\q':>6}"+"".join(f"{q:>9.1f}" for q in (1.5,2,2.5,3,4,6))
print(hdr)
for Tc in (2.0,3.0,4.0,6.0,8.0,12.0,20.0):
    row=f"{Tc:6.1f}"
    for q in (1.5,2,2.5,3,4,6):
        f=lambda lc: float(np.sum(resid_fixed(np.exp(lc),Tc,q)**2))
        r=minimize_scalar(f,bounds=(np.log(1e-4),np.log(10)),method="bounded")
        row+=f"{r.fun:9.2f}"
    print(row)
print("\n   committed fraction at 5 K implied by each node (%):")
print(hdr)
for Tc in (2.0,3.0,4.0,6.0,8.0,12.0,20.0):
    print(f"{Tc:6.1f}"+"".join(f"{100*(1-np.exp(-(5.0/Tc)**q)):9.1f}" for q in (1.5,2,2.5,3,4,6)))
