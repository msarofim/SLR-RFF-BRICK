#!/usr/bin/env python3
"""
Validate the 2-TIMESCALE Mengel glacier — does it close the GSIC undershoot?

A single response time τ can't be both fast (early committed melt) and slow
(modern equilibrium tracking). Split into a fast (committed) + slow mode, both
relaxing to their share of the LIA-referenced equilibrium:

  S_eq(T) = a·(1 − exp(−b·(T − T_lia)))
  dS_fast/dt = (f·S_eq − S_fast)/τ_fast
  dS_slow/dt = ((1−f)·S_eq − S_slow)/τ_slow
  S = S_fast + S_slow

Fit (a, b, T_lia, f, τ_fast, τ_slow) to Frederikse total glaciers 1900-2018 +
Dyurgerov ΔGSIC(1961-2003). T_lia bound widened to −1.0 (regional LIA amplification).
Compare to the 1-τ result (RMSE 1.04, @1900 −4.71). Check stabilization.
"""
import os
import numpy as np
import pandas as pd
from scipy.optimize import least_squares

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
GMST = pd.read_csv(os.path.join(REPO, "data/observations/fair_mean_gmst.csv")).set_index("year")["gmst_C"]
TG = pd.read_csv(os.path.join(REPO, "outputs/recalib_targets.csv")).set_index("year")
BASE0, BASE1 = 1995, 2005
FIT0, FIT1 = 1900, 2018
DYU_MU, DYU_SIG = 2.127, 0.148
fred = TG["gsic"]
fred_sig = (TG.loc[1900, "gsic_hi"] - TG.loc[1900, "gsic_lo"]) / (2 * 1.645)
yrs_h = np.arange(FIT0, FIT1 + 1); fred_h = fred.loc[FIT0:FIT1].values

def integrate(a, b, T_lia, f, tf, ts, y_end=2019, Tstab=None, y_branch=2018):
    yy = np.arange(1850, y_end); sf = 0.0; ss = 0.0; out = np.empty(len(yy))
    for k, y in enumerate(yy):
        out[k] = sf + ss
        T = GMST.loc[y] if (y <= y_branch and y in GMST.index) else Tstab
        Seq = a * (1 - np.exp(-b * (T - T_lia)))
        sf += (f * Seq - sf) / tf
        ss += ((1 - f) * Seq - ss) / ts
    return yy, out

def model_window(p):
    yy, s = integrate(*p); s = s * 100
    s -= s[(yy >= BASE0) & (yy <= BASE1)].mean()
    idx = {int(y): k for k, y in enumerate(yy)}
    fit = np.array([s[idx[y]] for y in yrs_h])
    return fit, s[idx[2003]] - s[idx[1961]]

def resid(p):
    fit, dyu = model_window(p)
    r = (fit - fred_h) / fred_sig
    return np.concatenate([r / np.sqrt(len(r)), [3.0 * (dyu - DYU_MU) / DYU_SIG]])

#          a     b    T_lia   f   tau_f  tau_s
lb = [0.32, 0.25, -1.00, 0.0,  5.0,  80.0]
ub = [0.55, 1.00, -0.10, 1.0, 80.0, 800.0]
p0 = [0.45, 0.52, -0.45, 0.4, 30.0, 250.0]
sol = least_squares(resid, p0, bounds=(lb, ub))
a, b, T_lia, f, tf, ts = sol.x
fit, dyu = model_window(sol.x)
rmse = np.sqrt(np.mean((fit - fred_h) ** 2))
ratio = -fit[0] / dyu

print("=== 2-timescale Mengel glacier (LIA-referenced) ===")
print(f"  a={a:.3f} m  b={b:.3f}/K  T_lia={T_lia:.3f}°C")
print(f"  f(fast)={f:.2f}  tau_fast={tf:.0f} yr  tau_slow={ts:.0f} yr")
print(f"\n  @1900: model {fit[0]:+.2f} vs Frederikse {fred_h[0]:+.2f} ± {fred_sig:.2f} cm")
print(f"  ΔGSIC(1961-2003): model {dyu:+.2f} vs Dyurgerov {DYU_MU:+.2f}")
print(f"  RMSE 1900-2018 = {rmse:.2f} cm  (1-τ was 1.04; single-reservoir 1.31 physical)")
print(f"  hist:modern melt ratio = {ratio:.2f}  (obs ~3.4)")

print("\n=== Stabilization regression ===")
for Tstab in [0.5, 1.5, 3.0]:
    Seq = a * (1 - np.exp(-b * (Tstab - T_lia))) * 100
    _, s = integrate(a, b, T_lia, f, tf, ts, y_end=3000, Tstab=Tstab)
    print(f"  hold T*={Tstab} °C: S_eq={Seq:.1f} cm = {Seq/(a*100)*100:.0f}% of a={a*100:.0f}cm; "
          f"S@2999={s[-1]*100:.1f} -> remnant survives")

pd.DataFrame([{"gic_a": a, "gic_b": b, "gic_T_lia": T_lia, "gic_f": f,
               "gic_tau_fast": tf, "gic_tau_slow": ts, "gic_sl0": 0.0}]).to_csv(
    os.path.join(REPO, "outputs/mengel_glacier_2tau_params.csv"), index=False)
print("\nWrote outputs/mengel_glacier_2tau_params.csv")
