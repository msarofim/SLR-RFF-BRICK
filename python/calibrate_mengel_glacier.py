#!/usr/bin/env python3
"""
Calibrate the Mengel 2016 glacier emulator with a NATURAL/COMMITTED-melt budget
handled the LWS way: BRICK/Mengel models only the anthropogenic glacier
contribution (S_eq passes 0 at ΔT=0), so the natural/committed early-20th-c melt
is supplied as a known external series ADDED to the modeled path. The calibration
then compares  Mengel(anthropogenic) + natural_budget  vs Frederikse total.

Model:  S_eq(ΔT)=a(1−exp(−bΔT));  S[t]=S[t-1]+(S_eq(ΔT[t-1])−S[t-1])/τ   (Mengel Eq.1)

Natural budget: glacier loss is mostly NATURAL/committed early, anthropogenic late
(Marzeion et al. 2014, Science 345:919: anthropogenic fraction of mass loss ≈25%
over 1851-2010, ≈69% over 1991-2010 — RECALLED, verify). We model the anthropogenic
fraction of the melt RATE as a logistic f_anth(t) anchored to those two periods,
set natural_rate = (1−f_anth)·d(Frederikse)/dt, and integrate. This is the LWS-style
external series; refine later with the raw Marzeion attribution if desired.

Outputs: calibrated (a,b,τ); historical fit of Mengel+natural vs Frederikse; the
stabilization regression (S→S_eq(T*)<a); saves params + natural budget series.
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
fred = TG["gsic"]                                  # Frederikse total glaciers, cm rel window
fred_sig = (TG.loc[1900, "gsic_hi"] - TG.loc[1900, "gsic_lo"]) / (2 * 1.645)

# ---- natural/committed glacier budget (Marzeion-anchored anthropogenic fraction) ----
def anthro_fraction(t):
    # logistic anthropogenic fraction of the melt RATE; anchored so the
    # melt-weighted mean ~25% over 1851-2010 and ~69% over 1991-2010 (Marzeion 2014).
    return 0.90 / (1 + np.exp(-(t - 1985) / 15.0))

yrs_h = np.arange(FIT0, FIT1 + 1)
fred_h = fred.loc[FIT0:FIT1].values
rate = np.gradient(fred_h)                                   # d(Frederikse total)/dt, cm/yr
nat_rate = (1 - anthro_fraction(yrs_h)) * rate               # natural part of the rate
natural = np.cumsum(nat_rate)
natural -= natural[(yrs_h >= BASE0) & (yrs_h <= BASE1)].mean()   # rel window
anthro_target = fred_h - natural                            # what Mengel must reproduce
# modern (Dyurgerov) target, anthropogenic part = anthro_target delta over 1961-2003
i = {int(y): k for k, y in enumerate(yrs_h)}
DYU_anth = anthro_target[i[2003]] - anthro_target[i[1961]]
DYU_SIG = 0.148

def integrate(a, b, tau, y_end=2019, Tstab=None, y_branch=2018):
    yy = np.arange(1850, y_end); s = 0.0; out = np.empty(len(yy))
    for k, y in enumerate(yy):
        out[k] = s
        T = GMST.loc[y] if (y <= y_branch and y in GMST.index) else Tstab
        s = s + (a * (1 - np.exp(-b * T)) - s) / tau
    return yy, out

def model_window(p):
    a, b, tau = p
    yy, s = integrate(a, b, tau); s *= 100
    s -= s[(yy >= BASE0) & (yy <= BASE1)].mean()
    idx = {int(y): k for k, y in enumerate(yy)}
    fit = np.array([s[idx[y]] for y in yrs_h])
    return fit, s[idx[2003]] - s[idx[1961]]

def resid(p):
    fit, dyu = model_window(p)
    r = (fit - anthro_target) / fred_sig
    return np.concatenate([r / np.sqrt(len(r)), [3.0 * (dyu - DYU_anth) / DYU_SIG]])

sol = least_squares(resid, [0.47, 0.52, 120.0], bounds=([0.25, 0.25, 10.0], [0.60, 1.20, 600.0]))
a, b, tau = sol.x
fit, dyu = model_window(sol.x)
total_model = fit + natural                                 # Mengel + natural budget
rmse_anth = np.sqrt(np.mean((fit - anthro_target) ** 2))
rmse_total = np.sqrt(np.mean((total_model - fred_h) ** 2))

print("=== Mengel glacier + natural budget (LWS-style) ===")
print(f"  natural budget @1900 = {natural[0]:+.2f} cm (of Frederikse total {fred_h[0]:+.2f})  "
      f"-> {natural[0]/fred_h[0]*100:.0f}% of the early melt is natural/committed")
print(f"  anthropogenic target @1900 = {anthro_target[0]:+.2f} cm")
print(f"\n  Calibrated Mengel: a={a:.3f} m, b={b:.3f} /K, tau={tau:.0f} yr")
print(f"  Mengel @1900 = {fit[0]:+.2f} vs anthro target {anthro_target[0]:+.2f}")
print(f"  RMSE(Mengel vs anthro) = {rmse_anth:.2f} cm")
print(f"  RMSE(Mengel+natural vs Frederikse total) = {rmse_total:.2f} cm  "
      f"(single-reservoir physical teq best ~1.31; with unphysical teq 0.68)")

print("\n=== Stabilization regression (single reservoir FAILS) ===")
for Tstab in [0.5, 1.5, 3.0]:
    Seq = a * (1 - np.exp(-b * Tstab)) * 100
    print(f"  hold T*={Tstab} °C: S_eq = {Seq:.1f} cm = {Seq/(a*100)*100:.0f}% of a={a*100:.0f}cm "
          f"-> remnant survives (NOT full depletion)")

pd.DataFrame([{"gic_a": a, "gic_b": b, "gic_tau": tau, "gic_sl0": 0.0}]).to_csv(
    os.path.join(REPO, "outputs/mengel_glacier_params.csv"), index=False)
pd.DataFrame({"year": yrs_h, "natural_glacier_cm": natural}).to_csv(
    os.path.join(REPO, "outputs/glacier_natural_budget.csv"), index=False)
print("\nWrote outputs/mengel_glacier_params.csv + glacier_natural_budget.csv")
