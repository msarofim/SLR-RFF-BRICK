#!/usr/bin/env python3
"""
scope_gis_tap_shape.py — can ANY tap functional form reproduce the PROTECT-Greenland
x2300 trajectory, and what would it do to our own SSP5-8.5?

WHY (2026-08-21, notes/handoff_2026-08-21b_protect_matched_forcing.md §3)
  At matched forcing the shipped exponential tap overshoots the physics at 2150 by
  3.4-3.5x while landing at 2300, because the physics residual is BACK-LOADED and
  still accelerating at 2300 and a relaxation toward a SATURATING target is not.
  Before proposing a replacement form, price the candidates offline. Emulating the
  tap in numpy is exact -- `tap_unit` carries no posterior dependence, which is why
  the tap is prior-propagated -- so this needs no Julia run and no refit.

THE TARGET
  residual(t) = PROTECT x2300 median - our tap-OFF base, BOTH under the PROTECT
  forcing (outputs/diag_protect_forcing_matched_L14_untapped.csv, `spliced` arm).
  It is NEGATIVE before ~2147 because our base is 1.57x the physics at 2100. No tap
  can be negative, so that early gap is a BASE-MODEL bias and is reported, never
  fitted away.

THE FORMS
  A  current      S_eq = clip((T-T_on)/w, 0, 1);  dS = (S_eq - S)/tau     -> V*S
     The target SATURATES at 1 once T > T_on + w, so past that it is a plain
     exponential approach to V. That saturation is the thing under test.
  B  unsaturating S_eq = (T-T_on)+/w  with NO upper clip; dS = (S_eq - S)/tau
     Minimal change: same machinery, one clip removed. The target keeps growing
     with T, so the tap keeps accelerating while the world keeps warming.
  C  excess-rate  dV/dt = k * (T - T_on)+      (cumulative warming above onset)
     No stock, no timescale: the rate itself tracks the forcing.
  D  power law    V = V_max * ((t - t_on)/(2300 - t_on))^p
     Phenomenological and TEMPERATURE-BLIND after onset, included only to show
     what a pure shape fix costs: it cannot tell SSP5-8.5 from SSP2-4.5.

THE TWO-SIDED TEST, which is the whole point
  A form is only a candidate if it BOTH (i) tracks the physics under the PROTECT
  forcing and (ii) still fires on OUR ssp585, which peaks at 7.81 K. The exponential
  fails (ii) whenever it is retuned to pass (i): moving the onset late is its only
  route to back-loading, and onset > 7.81 K is exactly inert on our own scenario.

WRITES outputs/scope_gis_tap_shape.csv, figures/gis_tap_shape_candidates.png
  python3 python/scope_gis_tap_shape.py
"""
import os

import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import minimize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = "L14"
## Imported, not retyped — a shape scan run at a different ramp width than the
## priced grid used is a scan of a different tap. Asserted at import.
from scope_gis_tap_l13 import TAP_RAMP_W_K as RAMP_W_K
assert RAMP_W_K == 1.0, f"TAP_RAMP_W_K moved to {RAMP_W_K}; re-read this scan's conclusions"
ONSET_SHIPPED, V_SHIPPED, TAU_SHIPPED = 6.5, 2.0, 50.0
FIT_YEARS = (2150, 2200, 2250, 2300)   # the horizons the physics actually constrains
OUR_PEAK_K = 7.815                  # fair_mean_gmst_ssp585 max — the (ii) constraint

f = pd.read_csv(os.path.join(REPO, "outputs/protect_x2300_forcing_gmst.csv")).set_index("year")
unt = pd.read_csv(os.path.join(REPO, f"outputs/diag_protect_forcing_matched_{TAG}_untapped.csv"))
ann = pd.read_csv(os.path.join(REPO, "outputs/protect_greenland_gis_annual.csv"))

base = unt[(unt.component == "gis") & (unt.arm == "spliced")].set_index("year").med
OFFSET = float(unt[(unt.component == "gis") & (unt.arm == "ours")].set_index("year").med.loc[2015])
x = ann[ann.exp.str.contains("ssp585-x2300")]
phys = x.groupby("year").gis_cm.median() + OFFSET

yrs = np.array(sorted(set(base.index) & set(phys.index) & set(f.index)))
T_prot = f.loc[yrs, "gmst_spliced_11yr"].to_numpy()
T_ours = f.loc[yrs, "gmst_ours"].to_numpy()
resid = (phys.loc[yrs] - base.loc[yrs]).to_numpy()          # cm the tap must supply
fit_i = np.array([int(np.where(yrs == y)[0][0]) for y in FIT_YEARS])

CM = 100.0                                                  # V is in m SLE


def relax(T, t_on, tau, clip_top):
    seq = (T - t_on) / RAMP_W_K
    seq = np.clip(seq, 0.0, 1.0) if clip_top else np.clip(seq, 0.0, None)
    S = np.zeros_like(T)
    for i in range(1, len(T)):
        S[i] = S[i - 1] + (seq[i - 1] - S[i - 1]) / tau
    return S


def form(name, p, T):
    if name == "A":  return CM * p[0] * relax(T, p[1], p[2], True)
    if name == "B":  return CM * p[0] * relax(T, p[1], p[2], False)
    if name == "C":  return CM * p[0] * np.cumsum(np.clip(T - p[1], 0.0, None))
    if name == "D":
        on = np.searchsorted(T, p[1])
        s = np.clip((np.arange(len(T)) - on) / max(len(T) - 1 - on, 1), 0.0, None)
        return CM * p[0] * s ** p[2]
    raise KeyError(name)


SPECS = {  # name: (label, x0, bounds)
    "A": ("A current (saturating target)",      [2.0, 6.5, 50.0],  [(0.5, 6), (4.0, 12.0), (5, 400)]),
    "B": ("B unsaturating target",              [0.5, 6.5, 50.0],  [(0.02, 6), (4.0, 12.0), (5, 400)]),
    "C": ("C rate ~ warming excess",            [0.01, 6.5],       [(1e-5, 1), (4.0, 12.0)]),
    "D": ("D power law in time (T-blind)",      [2.0, 6.5, 3.0],   [(0.5, 6), (4.0, 12.0), (0.5, 8)]),
}

## TWO FIT MODES, and the PINNED one is the decisive test.
##   free   the onset is a free parameter. Every stock-based form "solves" the
##          back-loading by pushing the onset past 7.81 K, which is precisely the
##          failure already measured in the --scan arm: exactly inert on our own
##          scenario. A good `free` fit is therefore NOT evidence for a form.
##   pinned the onset is held at the SHIPPED 6.5 K. This asks the question that
##          matters: can the FORM alone back-load, without moving the onset out of
##          our scenario's reach?
rows = []
curves = {}
for k, (label, x0, bnds) in SPECS.items():
    for mode in ("free", "pinned"):
        b = list(bnds)
        xx = list(x0)
        if mode == "pinned":
            b[1] = (ONSET_SHIPPED, ONSET_SHIPPED)
            xx[1] = ONSET_SHIPPED
        cost = lambda p: float(np.sum((form(k, p, T_prot)[fit_i] - resid[fit_i]) ** 2))
        r = minimize(cost, xx, bounds=b, method="L-BFGS-B")
        p = r.x
        v_prot, v_ours = form(k, p, T_prot), form(k, p, T_ours)
        curves[(k, mode)] = (label, p, v_prot, v_ours)
        rows.append(dict(form=k, mode=mode, label=label,
                         rmse_cm=float(np.sqrt(r.fun / len(fit_i))),
                         par="|".join(f"{q:.4g}" for q in p),
                         tap2150=v_prot[fit_i[0]], tap2300=v_prot[-1],
                         tot2150=base.loc[2150] + v_prot[fit_i[0]],
                         tot2300=base.loc[2300] + v_prot[-1],
                         onset_K=p[1], fires_on_ours=bool(p[1] < OUR_PEAK_K),
                         ours_tap2300=v_ours[-1]))

out = pd.DataFrame(rows)
out.to_csv(os.path.join(REPO, "outputs/scope_gis_tap_shape.csv"), index=False)

print(f"target: PROTECT median minus our tap-OFF base, both on the PROTECT forcing")
print(f"  residual at 2100 {resid[np.where(yrs==2100)[0][0]]:+.1f} cm "
      f"(NEGATIVE = our base is already above the physics; no tap can fix that)")
print(f"  residual at 2150 {resid[fit_i[0]]:+.1f}, at 2300 {resid[-1]:+.1f} cm\n")
for mode in ("free", "pinned"):
    print(f"--- onset {mode.upper()}" +
          (f" at the shipped {ONSET_SHIPPED} K" if mode == "pinned" else " (free parameter)"))
    print(f"{'form':36} {'rmse':>6} {'tap@2150':>9} {'tap@2300':>9} {'onset':>6} "
          f"{'fires?':>7} {'ours tap@2300':>13}")
    for r in out[out["mode"] == mode].itertuples():
        print(f"{r.label:36} {r.rmse_cm:6.1f} {r.tap2150:9.1f} {r.tap2300:9.1f} "
              f"{r.onset_K:6.2f} {str(r.fires_on_ours):>7} {r.ours_tap2300:13.1f}")
    print()
print(f"\nshipped cell for reference: tap@2150 116.1, tap@2300 195.9 cm "
      f"(target {resid[fit_i[0]]:.1f} and {resid[-1]:.1f})")

# ---- figure ----------------------------------------------------------------
fig, ax = plt.subplots(1, 2, figsize=(13.5, 5.2))
ship = CM * V_SHIPPED * relax(T_prot, ONSET_SHIPPED, TAU_SHIPPED, True)
for a, (v_idx, T, lab) in enumerate([(2, T_prot, "under the PROTECT x2300 forcing"),
                                     (3, T_ours, "under OUR ssp585 (peak 7.81 K)")]):
    if a == 0:
        ax[a].plot(yrs, resid, "k", lw=3, label="TARGET: physics − our base")
        ax[a].plot(yrs, ship, color="#c1272d", lw=2, ls="--", label="shipped cell")
    else:
        ax[a].plot(yrs, CM * V_SHIPPED * relax(T_ours, ONSET_SHIPPED, TAU_SHIPPED, True),
                   color="#c1272d", lw=2, ls="--", label="shipped cell")
    for k, c in zip("ABCD", ("#1763b8", "#1a5c2a", "#e08214", "#7b3294")):
        ax[a].plot(yrs, curves[(k, "pinned")][v_idx], color=c, lw=2,
                   label=curves[(k, "pinned")][0])
    ax[a].set_title(lab, loc="left", fontsize=11)
    ax[a].set_xlabel("year"); ax[a].set_ylabel("tap contribution, cm")
    ax[a].grid(alpha=.25, lw=.6); ax[a].legend(fontsize=8.5, loc="upper left")
    ax[a].set_xlim(2015, 2300)
fig.suptitle("Tap forms fitted to the physics residual at "
             f"{FIT_YEARS} with the onset PINNED at the shipped {ONSET_SHIPPED} K — "
             "left: does the form alone back-load; right: what it does to our own ssp585",
             fontsize=10.5, y=1.01)
fig.tight_layout()
fig.savefig(os.path.join(REPO, "figures/gis_tap_shape_candidates.png"), dpi=160,
            bbox_inches="tight")
# ---- what the physics implies for OUR OWN ssp585 ---------------------------
## The x2300 family cannot answer this: it runs at 9.8-13.6 K and we run at
## 4.7-7.8 K. The `r2300` family CAN bracket it from below -- forcing HELD at each
## GCM's 2081-2100 level, i.e. a roughly CONSTANT world. Its ssp585-like arm is 40
## runs across SIX forcing GCMs (vs x2300's two), though through ONE CISM config
## (CISM16t-MAR39-p50) where x2300 spans several -- complementary samples, both
## NORCE-CISM, neither a structural-uncertainty estimate.
##
## The interpolation below is DELIBERATELY CRUDE and is a bracket, not a
## prediction: two points, linear in mean warming, ignoring path dependence (the
## r2300 world plateaus by 2100, ours keeps warming to 2300, and an ice sheet
## integrates the path, not the mean). Quoted to the nearest 10 cm for that reason.
r2300 = ann[ann.exp.str.contains("r2300") & ann.exp.str.contains("ssp585|rcp85")]
R = r2300.groupby("year").gis_cm.quantile([.05, .5, .95]).unstack() + OFFSET
X = x.groupby("year").gis_cm.quantile([.05, .5, .95]).unstack() + OFFSET
T_R, T_X = 5.12, 13.64           # r2300 plateau (4 GCMs available); x2300 at 2290
o = pd.read_csv(os.path.join(REPO, "data/observations/fair_mean_gmst_ssp585.csv")).set_index("year").gmst_C
T_us = float(o.loc[2100:2300].mean())
lo, hi = R.loc[2300, 0.5], X.loc[2300, 0.5]
mid = lo + (hi - lo) * (T_us - T_R) / (T_X - T_R)
print(f"\nWHAT THE PHYSICS IMPLIES FOR OUR OWN ssp585 (mean 2100-2300 warming {T_us:.2f} K)")
print(f"  r2300, forcing HELD at ~{T_R:.2f} K, n=40 / 6 GCMs / 1 CISM config:")
print(f"    Greenland@2300  p05 {R.loc[2300,0.05]:5.1f}  p50 {R.loc[2300,0.5]:5.1f}  p95 {R.loc[2300,0.95]:5.1f} cm")
print(f"  x2300, ~{T_X:.2f} K, n=18 / 2 GCMs: p50 {X.loc[2300,0.5]:.1f} cm")
print(f"  crude two-point interpolation to our {T_us:.2f} K  ->  ~{round(mid,-1):.0f} cm "
      f"(bracket ~{round(R.loc[2300,0.5],-1):.0f}-{round(X.loc[2300,0.5],-1):.0f})")
print(f"  ours UNTAPPED@2300  50.0 cm   |   ours SHIPPED CELL@2300  230.3 cm")
print(f"  => untapped is LOW, the shipped tap is ~{230.3/mid:.1f}x the interpolated central "
      f"and {230.3/R.loc[2300,0.95]:.1f}x the r2300 p95")

print("\nwrote outputs/scope_gis_tap_shape.csv, figures/gis_tap_shape_candidates.png")
