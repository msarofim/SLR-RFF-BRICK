#!/usr/bin/env python3
"""
Does BRICK's GSIC stop melting when temperature stabilizes?

Integrates the standalone BRICK glacier recursion
    SLE[t] = SLE[t-1] + beta0*(T-teq)*(1 - SLE[t-1]/V0)^n   (capped at V0)
forward from 1850 (FaIR-mean GMST to 2020) and then holds T constant at several
stabilization levels to 2500, using the medoid central draw's calibrated GSIC
parameters.

Point: BRICK DOES self-limit melt — via the finite reservoir V0 and the
depletion factor (1 - SLE/V0)^n, the rate -> 0 as SLE -> V0. BUT the equilibrium
volume does NOT depend on temperature: for ANY sustained T > teq the model
commits the ENTIRE reservoir V0 to melt (temperature only sets the RATE). There
is no temperature-dependent "vulnerable fraction" that survives at a given
warming, which is the physically expected behavior.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
row = pd.read_csv(os.path.join(REPO, "outputs/recalib_central_row.csv")).iloc[0]
B0, V0, N, S0 = row.glaciers_beta0, row.glaciers_v0, row.glaciers_n, row.glaciers_s0
GMST = pd.read_csv(os.path.join(REPO, "data/observations/fair_mean_gmst.csv")).set_index("year")["gmst_C"]
TEQ = -0.15            # default frozen glacier equilibrium temperature
Y_BRANCH, Y_END = 2020, 2500
TSTARS = [0.5, 1.0, 1.5, 2.0, 3.0]
OUT = os.path.join(REPO, "outputs/gsic_stabilization_demo.png")

def integrate(teq, Tstab):
    yrs = np.arange(1850, Y_END + 1)
    sle = np.empty(len(yrs)); s = float(S0)
    for i, y in enumerate(yrs):
        sle[i] = s
        T = GMST.loc[y] if (y <= Y_BRANCH and y in GMST.index) else Tstab
        if s < V0:
            s = s + B0 * (T - teq) * (1 - s / V0) ** N
        else:
            s = V0
    return yrs, sle

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.2))
cmap = plt.cm.viridis(np.linspace(0.15, 0.9, len(TSTARS)))
for Tstab, c in zip(TSTARS, cmap):
    yrs, sle = integrate(TEQ, Tstab)
    rate = np.gradient(sle) * 100      # cm/yr
    ax1.plot(yrs, sle * 100, color=c, lw=2, label=f"T* = {Tstab:.1f} °C  ({sle[-1]/V0*100:.0f}% of V₀ by 2500)")
    ax2.plot(yrs, rate, color=c, lw=2, label=f"T* = {Tstab:.1f} °C")

ax1.axhline(V0 * 100, color="crimson", ls="--", lw=1.5, label=f"V₀ = {V0*100:.0f} cm (total reservoir)")
ax1.axvline(Y_BRANCH, color="0.6", ls=":", lw=1)
ax1.set_xlim(1900, Y_END); ax2.set_xlim(1900, Y_END)   # start plots in 1900
ax1.set_title("Cumulative GSIC sea-level contribution\n(T held constant after 2020)", fontsize=11)
ax1.set_xlabel("year"); ax1.set_ylabel("GSIC SLE (cm)")
ax1.legend(fontsize=7.5, loc="lower right"); ax1.grid(alpha=0.25)

ax2.axvline(Y_BRANCH, color="0.6", ls=":", lw=1)
ax2.set_title("GSIC melt RATE → 0 only as the reservoir empties\n(not at a temperature-dependent equilibrium)", fontsize=11)
ax2.set_xlabel("year"); ax2.set_ylabel("melt rate (cm/yr)")
ax2.legend(fontsize=7.5, loc="upper right"); ax2.grid(alpha=0.25)

fig.suptitle("BRICK GSIC under stabilized temperature — finite reservoir, but NO temperature-dependent equilibrium\n"
             f"medoid params: β₀={B0:.4g} m/°C/yr, V₀={V0:.3g} m, n={N:.3g}, teq={TEQ} °C  ·  "
             "every T* > teq eventually melts the WHOLE reservoir", fontsize=10.5)
fig.tight_layout(rect=[0, 0, 1, 0.92])
fig.savefig(OUT, dpi=140)
print(f"[wrote {OUT}]")
# numeric summary
for Tstab in TSTARS:
    _, sle = integrate(TEQ, Tstab)
    print(f"  T*={Tstab}: SLE@2500 = {sle[-1]*100:.1f} cm = {sle[-1]/V0*100:.0f}% of V₀ ; "
          f"rate@2500 = {(sle[-1]-sle[-2])*100:.4f} cm/yr")
