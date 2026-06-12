#!/usr/bin/env python3
"""
Calibrate the Mengel 2016 glacier emulator WITH a Little-Ice-Age disequilibrium
offset, fit DIRECTLY to the Frederikse total glacier series. No anthropogenic/
natural forcing split (the model is driven by total temperature and cannot
disentangle them), no external "natural" budget — the committed/disequilibrium
early-20th-c melt is SIMULATED.

Model:  S_eq(T) = a·(1 − exp(−b·(T − T_lia)));  S[t] = S[t-1] + (S_eq − S[t-1])/τ
T = total GMT anomaly rel 1850-1900 (FaIR-mean). T_lia (<0) = glacier equilibrium
temperature ≈ the colder LIA climate, so the glacier is OUT of equilibrium at
1850-1900 (S_eq(0) = a(1−exp(b·T_lia)) > 0) and melts to catch up = the committed
melt. T_lia is the physical generalization of the single-reservoir gsic_teq;
bounded to a defensible LIA range.

Fit (a, b, τ, T_lia) to Frederikse Glaciers 1900-2018 + Dyurgerov ΔGSIC(1961-2003).
Reports historical fit, the melt ratio, and the stabilization regression.
"""
import os
import numpy as np
import pandas as pd
from scipy.optimize import least_squares

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
GMST = pd.read_csv(os.path.join(REPO, "data/observations/fair_mean_gmst.csv")).set_index("year")["gmst_C"]
TG = pd.read_csv(os.path.join(REPO, "outputs/recalib_targets.csv")).set_index("year")  # cm rel 1995-2005
BASE0, BASE1 = 1995, 2005
FIT0, FIT1 = 1900, 2018
DYU_MU, DYU_SIG = 2.127, 0.148
fred = TG["gsic"]
fred_sig = (TG.loc[1900, "gsic_hi"] - TG.loc[1900, "gsic_lo"]) / (2 * 1.645)
yrs_h = np.arange(FIT0, FIT1 + 1)
fred_h = fred.loc[FIT0:FIT1].values

def integrate(a, b, tau, T_lia, y_end=2019, Tstab=None, y_branch=2018):
    yy = np.arange(1850, y_end); s = 0.0; out = np.empty(len(yy))
    for k, y in enumerate(yy):
        out[k] = s
        T = GMST.loc[y] if (y <= y_branch and y in GMST.index) else Tstab
        s = s + (a * (1 - np.exp(-b * (T - T_lia))) - s) / tau
    return yy, out

def model_window(p):
    a, b, tau, T_lia = p
    yy, s = integrate(a, b, tau, T_lia); s *= 100
    s -= s[(yy >= BASE0) & (yy <= BASE1)].mean()
    idx = {int(y): k for k, y in enumerate(yy)}
    fit = np.array([s[idx[y]] for y in yrs_h])
    return fit, s[idx[2003]] - s[idx[1961]]

def resid(p):
    fit, dyu = model_window(p)
    r = (fit - fred_h) / fred_sig
    return np.concatenate([r / np.sqrt(len(r)), [3.0 * (dyu - DYU_MU) / DYU_SIG]])

# bounds: a = total glacier vol from the LIA state (Farinotti present-day ~0.32 m,
# LIA larger -> ~0.35-0.55); b in Mengel range; tau decades-century; T_lia = LIA
# temperature rel 1850-1900 (PAGES2k/AR6: LIA ~0.3-0.5 C below 1850-1900).
lb = [0.32, 0.25, 10.0, -0.60]
ub = [0.55, 0.99, 600.0, -0.10]
sol = least_squares(resid, [0.45, 0.52, 120.0, -0.35], bounds=(lb, ub))
a, b, tau, T_lia = sol.x
fit, dyu = model_window(sol.x)
rmse = np.sqrt(np.mean((fit - fred_h) ** 2))
hist_melt = -fit[0]
ratio = hist_melt / dyu

print("=== Mengel glacier emulator + LIA disequilibrium (fit to Frederikse TOTAL) ===")
print(f"  a     = {a:.4f} m   (max contribution from LIA state)")
print(f"  b     = {b:.4f} /K")
print(f"  tau   = {tau:.1f} yr")
print(f"  T_lia = {T_lia:.3f} °C  (glacier equilibrium ≈ LIA climate, rel 1850-1900)")
print(f"  S_eq at 1850-1900 baseline (T=0) = {a*(1-np.exp(b*T_lia))*100:.2f} cm  -> committed melt present")
print(f"\n  @1900: model {fit[0]:+.2f} vs Frederikse {fred_h[0]:+.2f} ± {fred_sig:.2f} cm")
print(f"  ΔGSIC(1961-2003): model {dyu:+.2f} vs Dyurgerov {DYU_MU:+.2f} ± {DYU_SIG:.2f} cm")
print(f"  RMSE over {FIT0}-{FIT1} = {rmse:.2f} cm   "
      f"(single-reservoir 1.31 physical / 0.68 unphysical-teq; Mengel+natural-budget was 0.13)")
print(f"  hist:modern melt ratio = {ratio:.2f}  (obs ~3.4)")

print("\n=== Stabilization regression ===")
for Tstab in [0.5, 1.5, 3.0]:
    Seq = a * (1 - np.exp(-b * (Tstab - T_lia))) * 100
    print(f"  hold T*={Tstab} °C: S_eq = {Seq:.1f} cm = {Seq/(a*100)*100:.0f}% of a={a*100:.0f}cm "
          f"-> remnant survives (NOT full depletion)")

pd.DataFrame([{"gic_a": a, "gic_b": b, "gic_tau": tau, "gic_T_lia": T_lia, "gic_sl0": 0.0}]).to_csv(
    os.path.join(REPO, "outputs/mengel_glacier_params.csv"), index=False)
print("\nWrote outputs/mengel_glacier_params.csv")
