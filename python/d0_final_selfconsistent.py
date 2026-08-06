#!/usr/bin/env python3
"""
D0-final — the self-consistent glacier-frame solution and the nu-role summary.

Consolidates the D0 follow-up arms (session 2026-08-06/07) into one reproducible
script. Requires d0_glacier_shootout.py (imports its machinery by exec, as the
session snippets did) and t_glac_hadcrut5.csv.

Key objects:
  SC point — solve the glacier-frame consistency directly:
      slope@0_glac = 0.133/amp_fit  (m per glacier-frame K)
      inventory    a - S_obs(2000) = 0.290   (S_obs from the target + Leclercq 20mm)
      ladder       committed@+1.2K global = 39% of 2020 mass
    -> a ~ 0.383, b ~ 0.283, T_off ~ -1.00 glacier-K (~ -0.63 global-K, inside the
       PAGES-2k amplified LIA-minima range — the offset becomes defensible under
       the regional driver; committed@1850 ~ 0.094 m, NOT the 0.20 m the GMST
       driver demanded).
  Arms:
    A. S_eq fixed at SC, transient free (N and M)   — the physics-consistent fit
    B. fully free N x Tglac                          — where the likelihood alone goes
    C. nu-ladder at SC (nu fixed on a grid, kappa/noise free) — the price and
       payoff of nu: S(1900) and scenario spread vs flow logL.

Outputs: outputs/d0_final_selfconsistent.csv, figures/d0_final_selfconsistent.png
"""
import os
import subprocess

import numpy as np
import pandas as pd
from scipy.optimize import minimize

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
SHOOTOUT = os.path.join(REPO, "python/d0_glacier_shootout.py")

src = open(SHOOTOUT).read().split(
    "# ------------------------------------------------------------------ run all cells")[0]
exec(src.replace('print(f"D0', 'pass # print(f"D0'))

# NB: the exec above rebinds OUT_CSV/OUT_FIG to the shootout's paths — set ours AFTER it
OUT_CSV = os.path.join(REPO, "outputs/d0_final_selfconsistent.csv")
OUT_FIG = os.path.join(REPO, "figures/d0_final_selfconsistent.png")

COMMIT = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True).stdout.strip()

# ---------------------------------------------------------------- SC point (solved)
S2000_OBS = 0.093          # target melt 1900-2000 (7.3 cm) + Leclercq S(1900) 0.020
SC_A = INV_V + S2000_OBS   # inventory-consistent stock
SLOPE_GLAC = 0.133 / AMP_FIT
COM12_TARGET = 0.39        # GlacierMIP3 committed fraction at +1.2K global
S2020_OBS = 0.107
seq_at = lambda a, b, toff, T: a * (1 - np.exp(-b * (T - toff)))
# solve (b, T_off): S_eq(amp*1.2) = com*(a-S2020)+S2020 ; a*b*exp(b*T_off) = slope
from scipy.optimize import brentq
def solve_sc():
    tgt_seq = COM12_TARGET * (SC_A - S2020_OBS) + S2020_OBS
    def f(toff):
        b = -np.log(1 - tgt_seq / SC_A) / (AMP_FIT * 1.2 - toff)
        return SC_A * b * np.exp(b * toff) - SLOPE_GLAC
    toff = brentq(f, -1.9, -0.2)
    b = -np.log(1 - tgt_seq / SC_A) / (AMP_FIT * 1.2 - toff)
    return dict(a=SC_A, b=b, T_off=toff)

SC = solve_sc()
print(f"D0-final | commit={COMMIT} | amp_fit={AMP_FIT:.3f}")
print(f"  SC point: a={SC['a']:.3f} b={SC['b']:.3f} T_off={SC['T_off']:.3f} glacier-K "
      f"(~{SC['T_off']/AMP_FIT:.2f} global-K); committed@1850 = "
      f"{seq_at(SC['a'], SC['b'], SC['T_off'], 0.0):.3f} m")

Tarr = DRIVERS["Tglac"].to_numpy()[:-1]
rngf = np.random.default_rng(23)

def optimize(tr, free_names, fixed, seeds, nstart=14):
    def mk(z):
        th = dict(fixed)
        for nm, zz in zip(free_names, z):
            lo, hi = BOUNDS[nm]
            th[nm] = lo + (hi - lo) / (1 + np.exp(-zz))
        return th
    def neg(z):
        t = loglik_terms(tr, Tarr, mk(z))
        return np.inf if t is None else -t["logJ"]
    starts = []
    for sd in seeds:
        z = []
        for nm in free_names:
            lo, hi = BOUNDS[nm]
            x = np.clip((sd[nm] - lo) / (hi - lo), 1e-4, 1 - 1e-4)
            z.append(np.log(x / (1 - x)))
        starts.append(np.array(z))
    base = list(starts)
    while len(starts) < nstart:
        starts.append(base[rngf.integers(len(base))] + rngf.normal(0, 0.6, len(free_names)))
    best = None
    for z0 in starts:
        r = minimize(neg, z0, method="Nelder-Mead",
                     options=dict(xatol=1e-8, fatol=1e-10, maxiter=9000, maxfev=14000))
        if best is None or r.fun < best.fun:
            best = r
    r = minimize(neg, best.x, method="Nelder-Mead",
                 options=dict(xatol=1e-8, fatol=1e-10, maxiter=9000, maxfev=14000))
    return mk((r if r.fun < best.fun else best).x)

def metrics(tr, th, arm, amp_used, ampname):
    t = loglik_terms(tr, Tarr, th)
    s = t["s_raw"]
    com, sens = ladder(th, s[i2020], amp_used)
    ds = scenario_ds2100(tr, "Tglac", th, amp_used)
    spread = ds["ssp585"] - ds["ssp126"]
    s1900 = 1000 * s[i1900]
    invz = (th["a"] - s[i_inv] - INV_V) / INV_SIG
    gates = dict(g_s1900=10 <= s1900 <= 30, g_inv=abs(invz) < 1,
                 g_lad=all(GMIP3_LIKELY[L][0] <= com[L] <= GMIP3_LIKELY[L][1]
                           for L in GMIP3_LEVELS),
                 g_spread=4.5 <= spread <= 13.5)
    return dict(arm=arm, transient=tr, amp_variant=ampname, amp_used=amp_used,
                **{k: th.get(k, np.nan) for k in
                   ["a", "b", "T_off", "f", "tau_f", "tau_s", "kappa", "nu",
                    "sigma", "rho"]},
                logJ=t["logJ"], ll_flow=t["ll_flow"], ll_inv=t["ll_inv"],
                ll_lec=t["ll_lec"], ll_prior=t["ll_prior"],
                S1900_mm=s1900, inv_z=invz, S2020_mm=1000 * s[i2020],
                **{f"com{str(L).replace('.', 'p')}": com[L] for L in GMIP3_LEVELS},
                sens_mm=sens, ds126=ds["ssp126"], ds245=ds["ssp245"],
                ds585=ds["ssp585"], spread=spread, **gates,
                npass=sum(gates.values()))

rows = []
# --- Arm A: S_eq fixed at SC
thA_N = optimize("N", ["kappa", "nu", "sigma", "rho"], SC,
                 [dict(kappa=0.0035, nu=1.3, sigma=0.02, rho=0.5),
                  dict(kappa=0.009, nu=0.5, sigma=0.03, rho=0.6),
                  dict(kappa=0.001, nu=2.0, sigma=0.02, rho=0.4)])
thA_M = optimize("M", ["f", "tau_f", "tau_s", "sigma", "rho"], SC,
                 [dict(f=0.3, tau_f=60, tau_s=350, sigma=0.02, rho=0.5),
                  dict(f=0.05, tau_f=40, tau_s=200, sigma=0.03, rho=0.6)])
# --- Arm B: fully free N
thB = optimize("N", PNAMES["N"], {},
               [dict(SC, kappa=thA_N["kappa"], nu=max(thA_N["nu"], 0.1),
                     sigma=thA_N["sigma"], rho=thA_N["rho"]),
                dict(a=0.298, b=0.320, T_off=-2.0, kappa=0.0085, nu=0.0,
                     sigma=0.005, rho=0.05),
                dict(a=0.40, b=0.45, T_off=-1.2, kappa=0.004, nu=0.8,
                     sigma=0.02, rho=0.5)])
for ampname, ampval in AMP_VARIANTS.items():
    rows.append(metrics("N", thA_N, "A_SC_fixed", ampval, ampname))
    rows.append(metrics("M", thA_M, "A_SC_fixed", ampval, ampname))
    rows.append(metrics("N", thB, "B_free", ampval, ampname))

# --- Arm C: nu ladder at SC (kappa/noise free per nu)
NU_GRID = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]
for nu in NU_GRID:
    th = optimize("N", ["kappa", "sigma", "rho"], dict(SC, nu=nu),
                  [dict(kappa=0.009 * 2.0 ** (-nu), sigma=0.03, rho=0.6),
                   dict(kappa=0.003 * 2.0 ** (-nu), sigma=0.02, rho=0.4)], nstart=8)
    rows.append(metrics("N", th, f"C_nu{nu}", AMP_FIT, "ampfit"))

res = pd.DataFrame(rows)
res.to_csv(OUT_CSV, index=False, float_format="%.5f")

hdr = ["arm", "transient", "amp_variant", "nu", "kappa", "logJ", "ll_flow", "S1900_mm",
       "inv_z", "com1p2", "com2p0", "sens_mm", "ds245", "spread", "npass"]
pd.set_option("display.width", 240)
print("\n" + res[hdr].to_string(index=False,
      float_format=lambda x: f"{x:8.3f}" if abs(x) < 1e4 else f"{x:8.1e}"))

# ---------------------------------------------------------------- figure
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(14, 4.6), constrained_layout=True)
axL, axM_, axR = axes
C = res[res.arm.str.startswith("C_")].sort_values("nu")
axL.plot(C.nu, C.ll_flow, "o-", color="tab:blue")
axL.set(xlabel="ν (S_eq fixed at SC)", ylabel="flow logL", title="the price of ν")
axL2 = axL.twinx()
axL2.plot(C.nu, C.S1900_mm, "s--", color="tab:green")
axL2.axhspan(10, 30, color="tab:green", alpha=0.12)
axL2.set_ylabel("S(1900) mm (band = gate)", color="tab:green")

axM_.plot(C.nu, C.spread, "o-", color="tab:red", label="SSP126→585 spread @2100")
axM_.axhspan(4.5, 13.5, color="tab:red", alpha=0.10, label="AR6-family gate")
axM_.plot(C.nu, C.ds245, "s--", color="tab:orange", label="dS@2100 SSP2-4.5")
axM_.axhline(12, color="tab:orange", lw=0.8, ls=":", label="AR6 ssp245 median 12 cm")
axM_.set(xlabel="ν", ylabel="cm", title="the payoff of ν (scenario response)")
axM_.legend(fontsize=7)

lvls = GMIP3_LEVELS
for L in lvls:
    lo, hi = GMIP3_LIKELY[L]
    axR.fill_between([L - 0.08, L + 0.08], [lo] * 2, [hi] * 2, color="k", alpha=0.10)
    axR.plot([L - 0.08, L + 0.08], [GMIP3_CENTRAL[L]] * 2, color="k", lw=1.6)
rowA = res[(res.arm == "A_SC_fixed") & (res.transient == "N") &
           (res.amp_variant == "ampfit")].iloc[0]
rowB = res[(res.arm == "B_free") & (res.amp_variant == "ampfit")].iloc[0]
axR.plot(lvls, [rowA[f"com{str(L).replace('.', 'p')}"] for L in lvls], "o-",
         color="tab:green", label="SC point (a .383 b .283 T_off −1.0)")
axR.plot(lvls, [rowB[f"com{str(L).replace('.', 'p')}"] for L in lvls], "o-",
         color="tab:red", label="free optimum (pathology)")
axR.set(xlabel="global warming level (K)", ylabel="committed % of 2020 mass",
        title="GlacierMIP3 ladder at the SC point")
axR.legend(fontsize=8)
fig.suptitle(f"D0-final: self-consistent glacier-frame S_eq under the T_glac driver | "
             f"commit {COMMIT}", fontsize=10)
fig.savefig(OUT_FIG, dpi=150)
print(f"\nWrote {os.path.relpath(OUT_CSV, REPO)} and {os.path.relpath(OUT_FIG, REPO)}")
