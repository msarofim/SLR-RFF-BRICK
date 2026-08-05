#!/usr/bin/env python3
"""
A0 — Mengel glacier degenerate-direction profile (offline, no MCMC).

Tests the handoff-2026-08-05 §1 diagnosis BEFORE any recalibration:
the extA108 posterior rails gic_a (floor), gic_b (ceiling) and gic_T_lia
(floor) together because history constrains only TWO combinations —
slope@0 = a·b·exp(b·T_lia) and committed melt C = a·(1−exp(b·T_lia)) —
leaving one unidentified direction that the box, not the data, closes.

Three parts:
  P1 (algebraic): fix (slope@0, C) at their posterior medians, sweep
     T_lia, solve (a, b) exactly; forward-integrate for S(2020) and the
     Farinotti inventory residual a − S(2020) − V_inv.
     PREDICTION: one well-behaved curve crossing inventory-consistency
     near T_lia ≈ −1.1 to −1.2.
  P2 (profile likelihood): at each T_lia, maximize the GSIC AR(1)
     likelihood over (a, b) — (i) full 1900+ window, (ii) with the
     early-20th-century years (< EARLY_CUT_YEAR) removed.
     PREDICTION: (i) improves monotonically past the −1.00 floor with
     committed melt pinned ~0.20 m; (ii) the committed-melt demand
     collapses and the profile flattens.
  P3 (A4 quick test): (i) again but with gic_sl0 freed — does an
     initial-disequilibrium state absorb the committed-melt demand?

Scope/limitations (deliberate):
  * GSIC component AR(1) term ONLY — the calibrator's total-SLR (dang)
    term also sees glaciers but is dominated by the other components;
    this profile is the clean single-component read.
  * (f, tau_fast, tau_slow) and the AR(1) noise (sigma, rho) are HELD at
    their posterior medians: this is a slice-profile over (a, b | T_lia),
    per the handoff A0 spec, not a full profile over all six params.
  * Forward model verified against Julia to <0.3 cm (side session
    2026-08-05, project_ssps_gsic_2300_mengel.jl).

Outputs: outputs/a0_mengel_profile.csv, figures/a0_mengel_profile.png,
console verdicts on P1/P2/P3.
"""
import os
import subprocess

import numpy as np
import pandas as pd
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import brentq, minimize

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
POSTERIOR = os.path.join(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_extA108.csv")
GMST_FILE = os.path.join(REPO, "data/observations/fair_mean_gmst_ssp245harm.csv")  # calibrator forcing
TARGETS = os.path.join(REPO, "outputs/recalib_targets_ext.csv")
OUT_CSV = os.path.join(REPO, "outputs/a0_mengel_profile.csv")
OUT_FIG = os.path.join(REPO, "figures/a0_mengel_profile.png")

Y0, Y1 = 1850, 2026            # calibrate_mcmc_ext.jl model window
BASE0, BASE1 = 1995, 2005      # reref window (cm anomalies)
FIT_START = 1900               # first GSIC target year
EARLY_CUT_YEAR = 1950          # "early-20th-c removed" = fit years >= this
INVENTORY_M = 0.32             # Farinotti-2019 value used as the gic_a floor (A2 will re-check scope)
INV_YEAR = 2020                # inventory reference year: a − S(INV_YEAR) vs INVENTORY_M
TLIA_GRID = np.round(np.arange(-2.50, -0.099, 0.02), 4)
TLIA_FLOOR, B_CEIL = -1.00, 1.00        # current prior box (calibrate_mcmc_ext.jl:153-154)
MENGEL_PUB_A, MENGEL_PUB_B = 0.47, 0.52  # Mengel 2016 multi-model medians
EPS_FLOOR_CM = 0.05            # per-year obs sigma floor (matches calibrator)

# ---------------------------------------------------------------- provenance
COMMIT = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True).stdout.strip()
print(f"A0 Mengel profile | posterior={os.path.basename(POSTERIOR)} | "
      f"forcing={os.path.basename(GMST_FILE)} | targets={os.path.basename(TARGETS)} | "
      f"commit={COMMIT}")

# ---------------------------------------------------------------- inputs
post = pd.read_csv(POSTERIOR)
gmst = pd.read_csv(GMST_FILE).set_index("year")["gmst_C"]
tg = pd.read_csv(TARGETS).set_index("year")

gsic_ok = tg.index[(tg.index >= FIT_START) & tg["gsic"].notna()]
fit_years = np.arange(gsic_ok.min(), gsic_ok.max() + 1)
assert np.all(np.isin(fit_years, gsic_ok)), "GSIC target has a year gap (AR(1) assumes unit spacing)"
obs = tg.loc[fit_years, "gsic"].to_numpy()
eps = np.maximum((tg.loc[fit_years, "gsic_hi"] - tg.loc[fit_years, "gsic_lo"]).to_numpy() / (2 * 1.645),
                 EPS_FLOOR_CM)

med = post.median(numeric_only=True)
F_MED, TF_MED, TS_MED = med["gic_f"], med["gic_tau_fast"], med["gic_tau_slow"]
SIG_MED, RHO_MED = med["sd_gsic"], med["rho_gsic"]

years = np.arange(Y0, Y1 + 1)
T_arr = gmst.reindex(years[:-1]).to_numpy()   # step into year t uses T[t-1]
assert not np.isnan(T_arr).any(), "GMST forcing missing years in the model window"

# ------------------------------------------------- posterior cross-check (§1 numbers)
slope0 = post["gic_a"] * post["gic_b"] * np.exp(post["gic_b"] * post["gic_T_lia"])
committed = post["gic_a"] * (1 - np.exp(post["gic_b"] * post["gic_T_lia"]))
SLOPE0_MED, COMMITTED_MED = slope0.median(), committed.median()
rail_a = (post["gic_a"] < 0.32 + 0.002).mean()
rail_b = (post["gic_b"] > 1.00 - 0.002).mean()
rail_t = (post["gic_T_lia"] < -1.00 + 0.002).mean()
print(f"\nPosterior cross-check (n={len(post)}):")
print(f"  slope@0  median {SLOPE0_MED:.4f} m/K  (handoff: 0.1329)")
print(f"  committed median {COMMITTED_MED:.4f} m    (handoff: 0.1999)")
print(f"  railing: a@floor {100*rail_a:.1f}%  b@ceiling {100*rail_b:.1f}%  T_lia@floor {100*rail_t:.1f}%")

# ---------------------------------------------------------------- forward model
def integrate(a, b, T_lia, f=F_MED, tf=TF_MED, ts=TS_MED, sl0=0.0):
    """Annual 2-tau integration on the calibrator window; returns S(years) in m."""
    sf, ss = f * sl0, (1 - f) * sl0
    out = np.empty(len(years))
    out[0] = sl0
    for k, T in enumerate(T_arr):
        seq = a * (1 - np.exp(-b * (T - T_lia)))
        sf += (f * seq - sf) / tf
        ss += ((1 - f) * seq - ss) / ts
        out[k + 1] = sf + ss
    return out

ybase = (years >= BASE0) & (years <= BASE1)
yfit_idx = np.searchsorted(years, fit_years)
inv_idx = np.searchsorted(years, INV_YEAR)

def model_cm(a, b, T_lia, sl0=0.0):
    s = integrate(a, b, T_lia, sl0=sl0)
    return 100 * (s - s[ybase].mean()), s

# --------------------------------------------------- AR(1) heteroscedastic logL
def make_logl(sel):
    n = sel.sum()
    H = np.abs(np.subtract.outer(np.arange(n), np.arange(n)))
    Sigma = (SIG_MED**2 / (1 - RHO_MED**2)) * RHO_MED**H + np.diag(eps[sel]**2)
    cf = cho_factor(Sigma)
    logdet = 2 * np.sum(np.log(np.diag(cf[0])))
    const = -0.5 * (n * np.log(2 * np.pi) + logdet)
    o = obs[sel]
    idx = yfit_idx[sel]
    def logl(a, b, T_lia, sl0=0.0):
        m, _ = model_cm(a, b, T_lia, sl0=sl0)
        r = m[idx] - o
        return const - 0.5 * r @ cho_solve(cf, r)
    return logl

sel_full = np.ones(len(fit_years), dtype=bool)
sel_late = fit_years >= EARLY_CUT_YEAR
logl_full = make_logl(sel_full)
logl_late = make_logl(sel_late)
print(f"  GSIC fit window {fit_years[0]}-{fit_years[-1]} (n={sel_full.sum()}); "
      f"late-only {EARLY_CUT_YEAR}-{fit_years[-1]} (n={sel_late.sum()})")
print(f"  fixed at posterior medians: f={F_MED:.3f} tau_f={TF_MED:.1f} tau_s={TS_MED:.1f} "
      f"sigma={SIG_MED:.3f} rho={RHO_MED:.3f}")

# ---------------------------------------------------------------- P1: algebraic profile
def solve_ab(T_lia):
    """(a,b) holding slope@0 and committed at posterior medians; NaN outside domain."""
    ratio = COMMITTED_MED / SLOPE0_MED          # = (exp(-b*T_lia)-1)/b, increasing in b
    if -T_lia >= ratio:                          # g(b->0+) = -T_lia; no positive-b solution
        return np.nan, np.nan
    g = lambda b: (np.exp(-b * T_lia) - 1) / b - ratio
    b = brentq(g, 1e-8, 200.0)
    a = COMMITTED_MED / (1 - np.exp(b * T_lia))
    return a, b

rows = []
for tl in TLIA_GRID:
    a1, b1 = solve_ab(tl)
    if np.isfinite(a1):
        _, s_raw = model_cm(a1, b1, tl)
        s2020 = s_raw[inv_idx]
        inv_res = a1 - s2020 - INVENTORY_M
        ll_alg = logl_full(a1, b1, tl)
    else:
        s2020 = inv_res = ll_alg = np.nan
    rows.append(dict(T_lia=tl, a_alg=a1, b_alg=b1, S2020_alg=s2020,
                     inv_resid_alg=inv_res, logl_alg=ll_alg))
prof = pd.DataFrame(rows)

ok = prof.dropna(subset=["inv_resid_alg"])
sign_change = np.where(np.diff(np.sign(ok["inv_resid_alg"])))[0]
tlia_cross = np.nan
if len(sign_change):
    i = sign_change[0]
    x0, x1 = ok["T_lia"].iloc[i], ok["T_lia"].iloc[i + 1]
    r0, r1 = ok["inv_resid_alg"].iloc[i], ok["inv_resid_alg"].iloc[i + 1]
    tlia_cross = x0 - r0 * (x1 - x0) / (r1 - r0)
    a_cross, b_cross = solve_ab(tlia_cross)

# ------------------------------------------------- P2/P3: profile likelihood
def profile_opt(logl, tl, x_warm, free_sl0=False):
    """Maximize logl over (log a, log b [, sl0]) at fixed T_lia."""
    if free_sl0:
        fun = lambda x: -logl(np.exp(x[0]), np.exp(x[1]), tl, sl0=x[2])
    else:
        fun = lambda x: -logl(np.exp(x[0]), np.exp(x[1]), tl)
    best = None
    for x0 in x_warm:
        r = minimize(fun, x0, method="Nelder-Mead",
                     options=dict(xatol=1e-6, fatol=1e-8, maxiter=4000))
        if best is None or r.fun < best.fun:
            best = r
    a, b = np.exp(best.x[0]), np.exp(best.x[1])
    sl0 = best.x[2] if free_sl0 else 0.0
    return a, b, sl0, -best.fun

seed = [np.log(0.45), np.log(0.52)]
warm_f, warm_l, warm_s = [seed], [seed], [seed + [0.0]]
opt_rows = []
for tl in TLIA_GRID:
    af, bf, _, lf = profile_opt(logl_full, tl, warm_f)
    al, bl, _, ll = profile_opt(logl_late, tl, warm_l)
    as_, bs, sl0s, ls = profile_opt(logl_full, tl, warm_s, free_sl0=True)
    warm_f = [[np.log(af), np.log(bf)], seed]
    warm_l = [[np.log(al), np.log(bl)], seed]
    warm_s = [[np.log(as_), np.log(bs), sl0s], seed + [0.0]]
    opt_rows.append(dict(
        T_lia=tl,
        a_full=af, b_full=bf, logl_full=lf,
        committed_full=af * (1 - np.exp(bf * tl)),
        a_late=al, b_late=bl, logl_late=ll,
        committed_late=al * (1 - np.exp(bl * tl)),
        a_sl0=as_, b_sl0=bs, sl0_free=sl0s, logl_sl0=ls,
        committed_sl0=as_ * (1 - np.exp(bs * tl))))
opt = pd.DataFrame(opt_rows)
prof = prof.merge(opt, on="T_lia")
os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
prof.to_csv(OUT_CSV, index=False)

# ---------------------------------------------------------------- verdicts
in_box = prof["T_lia"] >= TLIA_FLOOR
best_all = prof.loc[prof["logl_full"].idxmax()]
best_box = prof.loc[prof.loc[in_box, "logl_full"].idxmax()]
best_late = prof.loc[prof["logl_late"].idxmax()]
com_full_box = prof.loc[in_box, "committed_full"].median()
com_late_box = prof.loc[in_box, "committed_late"].median()
late_range = prof["logl_late"].max() - prof["logl_late"].min()
full_range = prof["logl_full"].max() - prof["logl_full"].min()

print("\n=== P1 (algebraic profile) ===")
if np.isfinite(tlia_cross):
    print(f"  inventory-consistency crossing: T_lia = {tlia_cross:.3f}  "
          f"(a={a_cross:.3f}, b={b_cross:.3f}; handoff predicted ~ -1.1 to -1.2, a=0.479, b=0.476)")
else:
    print("  NO inventory-consistency crossing on the grid — §1 story NOT confirmed")
print(f"  algebraic domain limit: no (a,b) solution for T_lia <= {-COMMITTED_MED/SLOPE0_MED:.3f}")

print("\n=== P2 (profile likelihood over T_lia) ===")
print(f"  full window : optimum T_lia = {best_all['T_lia']:.2f} "
      f"(a={best_all['a_full']:.3f}, b={best_all['b_full']:.3f}, logL={best_all['logl_full']:.2f})")
print(f"  inside box  : optimum T_lia = {best_box['T_lia']:.2f} "
      f"(logL={best_box['logl_full']:.2f}); floor costs "
      f"dlogL = {best_all['logl_full'] - best_box['logl_full']:.2f}")
print(f"  committed melt at in-box optima (median) = {com_full_box:.3f} m")
print(f"  early-20th-c removed: optimum T_lia = {best_late['T_lia']:.2f}; "
      f"profile range dlogL = {late_range:.2f} (vs {full_range:.2f} full) — "
      f"committed at in-box optima (median) = {com_late_box:.3f} m")

print("\n=== P3 (gic_sl0 freed, full window) ===")
best_sl0 = prof.loc[prof["logl_sl0"].idxmax()]
print(f"  optimum T_lia = {best_sl0['T_lia']:.2f}  (a={best_sl0['a_sl0']:.3f}, "
      f"b={best_sl0['b_sl0']:.3f}, sl0={best_sl0['sl0_free']:.3f} m, logL={best_sl0['logl_sl0']:.2f})")
print(f"  profile range dlogL = {prof['logl_sl0'].max() - prof['logl_sl0'].min():.2f}; "
      f"committed at optimum = {best_sl0['committed_sl0']:.3f} m")

# ---------------------------------------------------------------- figure
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 2, figsize=(11, 8.5), constrained_layout=True)
(axA, axB), (axC, axD) = axes

axA.plot(prof["T_lia"], prof["a_alg"], color="tab:blue", label="a (algebraic)")
axA.plot(prof["T_lia"], prof["b_alg"], color="tab:red", label="b (algebraic)")
axA.axhline(MENGEL_PUB_A, color="tab:blue", ls=":", lw=1, label=f"Mengel pub a={MENGEL_PUB_A}")
axA.axhline(MENGEL_PUB_B, color="tab:red", ls=":", lw=1, label=f"Mengel pub b={MENGEL_PUB_B}")
axA.axvline(TLIA_FLOOR, color="k", ls="--", lw=1)
if np.isfinite(tlia_cross):
    axA.axvline(tlia_cross, color="tab:green", ls="-.", lw=1.2, label=f"inventory-consistent {tlia_cross:.2f}")
axA.set(xlabel="gic_T_lia (°C)", ylabel="m  |  1/K",
        title="P1: (a,b) holding slope@0 & committed at posterior medians")
axA.legend(fontsize=8)

axB.plot(prof["T_lia"], prof["inv_resid_alg"], color="tab:green")
axB.axhline(0, color="k", lw=0.8)
axB.axvline(TLIA_FLOOR, color="k", ls="--", lw=1, label="current T_lia floor")
if np.isfinite(tlia_cross):
    axB.axvline(tlia_cross, color="tab:green", ls="-.", lw=1.2)
axB.set(xlabel="gic_T_lia (°C)", ylabel="a − S(2020) − 0.32  (m)",
        title=f"P1: Farinotti inventory residual (V={INVENTORY_M} m @ {INV_YEAR})")
axB.legend(fontsize=8)

for col, lab, c in [("logl_full", f"full {fit_years[0]}–{fit_years[-1]}", "tab:blue"),
                    ("logl_late", f"≥{EARLY_CUT_YEAR} only", "tab:orange"),
                    ("logl_sl0", "full, gic_sl0 free", "tab:purple")]:
    axC.plot(prof["T_lia"], prof[col] - prof[col].max(), color=c, label=lab)
axC.axvline(TLIA_FLOOR, color="k", ls="--", lw=1, label="T_lia floor −1.00")
axC.set(xlabel="gic_T_lia (°C)", ylabel="Δ logL (rel. each max)",
        title="P2/P3: GSIC profile likelihood over T_lia", ylim=(-12, 0.5))
axC.legend(fontsize=8)

for col, lab, c in [("committed_full", "full window", "tab:blue"),
                    ("committed_late", f"≥{EARLY_CUT_YEAR} only", "tab:orange"),
                    ("committed_sl0", "gic_sl0 free", "tab:purple")]:
    axD.plot(prof["T_lia"], prof[col], color=c, label=lab)
axD.axhline(COMMITTED_MED, color="k", ls=":", lw=1, label=f"posterior median {COMMITTED_MED:.3f} m")
axD.axvline(TLIA_FLOOR, color="k", ls="--", lw=1)
axD.set(xlabel="gic_T_lia (°C)", ylabel="a·(1−exp(b·T_lia))  (m)",
        title="P2/P3: committed melt at each profile optimum")
axD.legend(fontsize=8)

fig.suptitle(f"A0 Mengel degenerate-direction profile — extA108 posterior, "
             f"{os.path.basename(GMST_FILE)}, commit {COMMIT}", fontsize=10)
os.makedirs(os.path.dirname(OUT_FIG), exist_ok=True)
fig.savefig(OUT_FIG, dpi=150)
print(f"\nWrote {os.path.relpath(OUT_CSV, REPO)} and {os.path.relpath(OUT_FIG, REPO)}")
