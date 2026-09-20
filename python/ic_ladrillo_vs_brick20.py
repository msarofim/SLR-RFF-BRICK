#!/usr/bin/env python3
"""
ic_ladrillo_vs_brick20.py — information-criterion test of the Ladrillo-vs-BRICK 2.0
hindcast: is the RMSE improvement (Table 4 of the L24 deliverable) more than the
23 extra parameters buy?

THE QUESTION AIC ANSWERS HERE. AIC = 2k - 2 ln L charges one unit of log-likelihood
per parameter; BIC = k ln N - 2 ln L charges (ln N)/2 units. If the log-likelihood
gain of Ladrillo over BRICK 2.0 on the SAME data and the SAME likelihood is larger
than the charge for its extra parameters, the parameter count cannot be what buys
the fit. The penalty is applied at its FULL count (every sampled parameter of each
model, physical + noise), which is the most conservative charge against Ladrillo.

WHAT IT DOES NOT ANSWER, stated up front: Ladrillo was CALIBRATED to these targets
and BRICK 2.0 was not (Wong's CW11-era targets). In-sample vs out-of-sample is a
separate axis from parameter count; AIC corrects for the optimism of a fitted
model's own likelihood, not for a comparator fitted to different data. The clean
structure test — a BRICK 2.0 arm recalibrated on the extended targets — is named
in notes/note_2026-08-14_ladrillo_vs_brick20_scorecard.md and is not this script.

INPUTS (julia/ic_hindcast_residuals.jl): per-draw residuals (model - obs, cm) of
NDRAW evenly-thinned posterior draws of each model, on ONE common target set
(recalib_targets_ext.csv + the r19-seam-adjusted glacier target), 1900-2026,
re-referenced 1995-2005, forcing ssp245harm. The per-draw medians reproduce the
two postpred p50 series (gated in the Julia driver), so these residuals are the
residuals behind Table 4.

TWO LIKELIHOOD ARMS, both scored identically on both models:
  obs_iid   independent Gaussian with the per-year OBSERVATIONAL sigma only
            (ln L = sum -r^2/(2 eps^2) - ln eps - ln(2 pi)/2). No fitted noise
            parameters, so k = physical parameters. Overstates the evidence when
            residuals are autocorrelated (they are) -- the LENIENT arm.
  ar1_prof  the calibrator's own form (hetero_logl_ar1 in calibrate_mcmc_ext.jl):
            stationary AR(1) with marginal variance sd^2/(1-rho^2) plus the
            observational diagonal. sd and rho are PROFILED (maximised) per series
            per draw for BOTH models, and charged as 2 parameters per series on
            both (Ladrillo's 8 fitted noise params; BRICK 2.0's 8 are on different
            series -- glaciers/greenland/antarctic/gmsl -- so its own cannot be
            used like-for-like). Autocorrelation shrinks the effective N, so this
            is the STRICT arm and the headline.
For each arm and model: ln L at every draw; the maximum over draws (the
approximate MLE -- a LOWER bound on the true maximum for both, since neither
posterior was optimised for this likelihood); AIC, AICc, BIC at that draw; the
posterior-mean deviance and Gelman's p_V = var(D)/2 for a DIC-style effective
parameter count; and the log-likelihood of the posterior-MEDIAN series (the
Table 4 basis, no parameter vector behind it -- reference only).

THE TOTAL is reported separately: out-of-sample for BOTH (Ladrillo never scores
it -- DROP_TOTAL; BRICK 2.0 was fit to CW11, not Dangendorf), and its residual
carries the Frederikse/NOAA non-closure both models inherit.

  python3 python/ic_ladrillo_vs_brick20.py [--tag=L24]
Writes:
  outputs/ic_ladrillo_vs_brick20_<TAG>.csv        one row per (arm, model, statistic)
  outputs/ic_ladrillo_vs_brick20_<TAG>_perdraw.csv  ln L per draw, per arm, per series
  outputs/ic_ladrillo_vs_brick20_<TAG>.md         the table with its reading
"""
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from scipy.optimize import minimize

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--tag=")), "L24")
IN_L = os.path.join(REPO, f"outputs/ic_hindcast_residuals_ladrillo_{TAG}.csv")
IN_B = os.path.join(REPO, "outputs/ic_hindcast_residuals_brick20.csv")
IN_S = os.path.join(REPO, "outputs/ic_hindcast_obs_sigma.csv")

MODELS = ("ladrillo", "brick20")
LABEL = {"ladrillo": f"Ladrillo {TAG}", "brick20": "BRICK 2.0"}
FIT_SERIES = ("ais", "gsic", "gis", "steric")     # the common in-likelihood set
OOS_SERIES = ("total",)                           # out-of-sample for both
SERIES = FIT_SERIES + OOS_SERIES
# Table 4's windows, for the per-window decomposition of the iid arm
WINDOWS = {"1900-2026": (1900, 2026), "1900-1919": (1900, 1919), "1920-1949": (1920, 1949),
           "1950-1992": (1950, 1992), "1993-2026": (1993, 2026)}

# ---- PARAMETER COUNTS, the whole point ---------------------------------------
# Every SAMPLED parameter of each posterior, counted from the posterior file
# headers (58 and 35 columns) and split by role. Ladrillo's 50 physical include 4
# glacier-ledger and 4 discrepancy (d2) coefficients that do not move the series
# scored here; they are CHARGED anyway -- the conservative direction.
def _count_sampled(path):
    """(physical, total) sampled parameters from a posterior file's header: every column that is not an
    AR(1) noise pair, a log-posterior, or a column the loader DERIVES (native Greenland pair). Read from
    the file, never typed: L24 has 50 + 8, L26 (no delta, no glacier d2, precip reparam) has 47 + 8."""
    cols = open(path).readline().rstrip("\n").split(",")
    cols = [c for c in cols if c not in ("log_post", "gis_alpha_s", "gis_beta_s") or path.endswith("parameters_subsample_brick.csv")]
    noise = [c for c in cols if c.startswith("sd_") or c.startswith("rho_")]
    return len(cols) - len(noise), len(cols)
_LAD = os.path.join(REPO, f"data/MimiBRICK/parameters_subsample_brick_mengel_{TAG}.csv")
_BRK = os.path.join(REPO, "data/MimiBRICK/parameters_subsample_brick.csv")
K_PHYS = {"ladrillo": _count_sampled(_LAD)[0], "brick20": _count_sampled(_BRK)[0]}
K_NOISE_PROF = 2 * len(FIT_SERIES)                # sd, rho per scored series, profiled in ar1_prof
K = {"obs_iid": K_PHYS,
     "ar1_prof": {m: K_PHYS[m] + K_NOISE_PROF for m in MODELS}}
K_TOTAL_IN_FILE = {"ladrillo": _count_sampled(_LAD)[1], "brick20": _count_sampled(_BRK)[1]}
assert K_PHYS["brick20"] == 27 and K_TOTAL_IN_FILE["brick20"] == 35, K_PHYS
if TAG == "L24":
    assert K_PHYS["ladrillo"] == 50 and K_TOTAL_IN_FILE["ladrillo"] == 58, K_PHYS   # the 09-16 result

# The AR(1) rho bound. 0.99 is the calibrator's own hard bound (calibrate_mcmc_ext.jl:1393).
# It MATTERS here: BRICK 2.0's residuals are smooth biases, and a rho at the bound turns the
# AR(1) term into a near-random-walk discrepancy that absorbs a smooth bias cheaply, so the
# profiled likelihood gain depends on how much autocorrelation the noise model is allowed.
# --rho-max= overrides it for the sensitivity arms; the outputs then carry a _rho<val> suffix.
RHO_MAX = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--rho-max=")), "0.99"))
RHO_SFX = "" if RHO_MAX == 0.99 else f"_rho{RHO_MAX:g}"
LN2PI = np.log(2 * np.pi)
OUT_CSV = os.path.join(REPO, f"outputs/ic_ladrillo_vs_brick20_{TAG}{RHO_SFX}.csv")
OUT_DRAW = os.path.join(REPO, f"outputs/ic_ladrillo_vs_brick20_{TAG}{RHO_SFX}_perdraw.csv")
OUT_MD = os.path.join(REPO, f"outputs/ic_ladrillo_vs_brick20_{TAG}{RHO_SFX}.md")


def load():
    sig = pd.read_csv(IN_S).set_index("year")
    res = {m: pd.read_csv(p) for m, p in (("ladrillo", IN_L), ("brick20", IN_B))}
    years = sig.index.to_numpy()
    obs = {s: sig[f"{s}_obs"].to_numpy(float) for s in SERIES}
    eps = {s: sig[f"{s}_sigma"].to_numpy(float) for s in SERIES}
    R = {}
    for m, df in res.items():
        R[m] = {s: df[[f"{s}_{y}" for y in years]].to_numpy(float) for s in SERIES}
    draws = {m: res[m]["draw"].to_numpy(int) for m in MODELS}
    prov = {m: res[m]["provenance"].iloc[0] for m in MODELS}
    return years, obs, eps, R, draws, prov


# ---- arm 1: independent Gaussian, observational sigma only --------------------
def ll_iid_series(r, eps):
    """Per-draw ln L over the finite-obs years of one series. r: (ndraw, ny)."""
    fin = np.isfinite(eps) & np.isfinite(r).all(axis=0)
    z = r[:, fin] / eps[fin]
    return -0.5 * (z ** 2).sum(axis=1) - np.log(eps[fin]).sum() - 0.5 * LN2PI * fin.sum()


def ll_iid_window(r, eps, years, w):
    fin = np.isfinite(eps) & np.isfinite(r).all(axis=0) & (years >= w[0]) & (years <= w[1])
    z = r[:, fin] / eps[fin]
    return -0.5 * (z ** 2).sum(axis=1) - np.log(eps[fin]).sum() - 0.5 * LN2PI * fin.sum()


# ---- arm 2: AR(1) + observational diagonal, sd/rho profiled --------------------
def _ar1_logpdf(r, years, eps, sd, rho):
    """hetero_logl_ar1: Sigma = sd^2/(1-rho^2) rho^|yi-yj| + diag(eps^2)."""
    lag = np.abs(years[:, None] - years[None, :])
    S = (sd ** 2 / (1 - rho ** 2)) * rho ** lag + np.diag(eps ** 2)
    L = np.linalg.cholesky(S)
    u = np.linalg.solve(L, r)
    return -0.5 * (u @ u) - np.log(np.diag(L)).sum() - 0.5 * LN2PI * len(r)


def _profile_one(args):
    """Full multistart Nelder-Mead over (log sd, rho) for ONE residual vector — the
    reference optimiser, used to VALIDATE the grid+polish path on a random subset."""
    r, years, eps = args
    best = None
    ## 12 starts, not 6 (2026-09-20, L27): the profiled surface can be BIMODAL -- a plateau at sd -> 0
    ## (obs error alone explains the residual) and a separate peak at the rho bound with a tiny sd.
    ## Starts at 0.3/0.7/0.92 x RHO_MAX from sd 0.1/0.5 all fell onto the plateau for one L27 glacier
    ## draw and the "reference" sat 1.24 ln L BELOW the grid; a near-bound start and a small-sd start
    ## reach the peak.
    for rho0 in (0.3 * RHO_MAX, 0.7 * RHO_MAX, 0.92 * RHO_MAX, 0.995 * RHO_MAX):   # inside the bound whatever it is
        for lsd0 in (np.log(0.01), np.log(0.1), np.log(0.5)):
            o = minimize(lambda x: _nll(x, r, years, eps), [lsd0, rho0], method="Nelder-Mead",
                         options=dict(xatol=1e-5, fatol=1e-7, maxiter=600))
            if best is None or o.fun < best.fun:
                best = o
    return -best.fun, float(np.exp(best.x[0])), float(best.x[1])


def _nll(x, r, years, eps):
    sd, rho = np.exp(x[0]), x[1]
    if not (0.0 <= rho < RHO_MAX) or sd <= 0:
        return 1e30
    return -_ar1_logpdf(r, years, eps, sd, rho)


def _polish_one(args):
    """Nelder-Mead polish from each of several grid starts; the best result wins. One start (the
    global grid optimum) missed by up to 0.36 ln L on the bimodal glacier draws (2026-09-20, L27)."""
    r, years, eps, starts = args
    best = None
    for lsd0, rho0 in starts:
        o = minimize(lambda x: _nll(x, r, years, eps), [lsd0, rho0], method="Nelder-Mead",
                     options=dict(xatol=1e-5, fatol=1e-7, maxiter=400))
        if best is None or o.fun < best.fun:
            best = o
    return -best.fun, float(np.exp(best.x[0])), float(best.x[1])


# grid for the shared-Cholesky pass: Sigma depends on (sd, rho, eps, years) only, so one
# factorisation serves every draw at that grid point
## near-bound rows are placed RELATIVE TO THE BOUND (2026-09-20, L27): the optimum can sit at rho -> RHO_MAX with
## a finite sd, and with the bound at 0.90 the old grid ended at 0.87 -- the polish from there slid onto the
## sd -> 0 plateau, 0.36 ln L below the reference multistart, on one glacier draw.
GRID_RHO = np.unique(np.concatenate([np.linspace(0.0, 0.90, 31), np.linspace(0.91, 0.989, 20),
                                     RHO_MAX * np.array([0.95, 0.97, 0.98, 0.99, 0.995, 0.999])]))
GRID_RHO = GRID_RHO[GRID_RHO < RHO_MAX]
GRID_LSD = np.log(np.geomspace(0.01, 5.0, 46))
N_VALIDATE = 24                                   # draws re-optimised by full multistart
POLISH_RHO_SPLIT = 0.9 * RHO_MAX                  # the two rho regimes the polish starts from (plateau / near-bound peak), scaled to the bound
VALIDATE_TOL = 0.1                                # ln L units the two paths may differ by (gaps of interest are O(10-100))


def ll_ar1_profiled(r, years, eps, workers, rng=None):
    """Profiled AR(1)+obs ln L per draw: grid (shared Cholesky across draws) then a
    per-draw Nelder-Mead polish from the grid optimum; validated against the full
    multistart on N_VALIDATE random draws."""
    fin = np.isfinite(eps) & np.isfinite(r).all(axis=0)
    ys, es, rs = years[fin].astype(float), eps[fin], r[:, fin]
    n, nd = fin.sum(), rs.shape[0]
    lag = np.abs(ys[:, None] - ys[None, :])
    ## the grid optimum is kept PER RHO REGIME (below / above POLISH_RHO_SPLIT) and the polish starts
    ## from both: the profiled surface is bimodal on some draws (see _profile_one) and a polish from
    ## the global grid optimum alone lost up to 0.36 ln L to the other mode's basin.
    best = np.full(nd, -np.inf); bi = np.zeros(nd, int); bj = np.zeros(nd, int)
    best2 = np.full(nd, -np.inf); bi2 = np.zeros(nd, int); bj2 = np.zeros(nd, int)   # the other regime's optimum
    for i, rho in enumerate(GRID_RHO):
        P = rho ** lag
        for j, lsd in enumerate(GRID_LSD):
            sd = np.exp(lsd)
            L = np.linalg.cholesky((sd ** 2 / (1 - rho ** 2)) * P + np.diag(es ** 2))
            U = np.linalg.solve(L, rs.T)                       # (n, nd)
            ll = -0.5 * (U ** 2).sum(axis=0) - np.log(np.diag(L)).sum() - 0.5 * LN2PI * n
            if rho < POLISH_RHO_SPLIT:
                m = ll > best; best[m] = ll[m]; bi[m] = i; bj[m] = j
            else:
                m = ll > best2; best2[m] = ll[m]; bi2[m] = i; bj2[m] = j
    grid_best = np.maximum(best, best2)
    with ProcessPoolExecutor(workers) as ex:
        out = list(ex.map(_polish_one, [(rs[d], ys, es, [(GRID_LSD[bj[d]], GRID_RHO[bi[d]]),
                                                        (GRID_LSD[bj2[d]], GRID_RHO[bi2[d]])]) for d in range(nd)],
                          chunksize=32))
    best = grid_best
    ll = np.array([o[0] for o in out]); sd = np.array([o[1] for o in out]); rho = np.array([o[2] for o in out])
    assert np.all(ll >= best - 1e-6), "polish lost the grid optimum"
    # validation: the cheap path must reproduce the reference optimiser
    if nd > 1:
        rng = rng or np.random.default_rng(2026)
        pick = rng.choice(nd, size=min(N_VALIDATE, nd), replace=False)
        ref = np.array([_profile_one((rs[d], ys, es))[0] for d in pick])
        d = ll[pick] - ref                           # >0: grid+polish found the higher optimum
        print(f"    [validate] grid+polish vs multistart on {len(pick)} draws: max|Δ| {np.abs(d).max():.4f} "
              f"(grid+polish higher by up to {d.max():.4f}, lower by up to {-d.min():.4f}) ln L", flush=True)
        assert np.abs(d).max() < VALIDATE_TOL, f"grid+polish differs from multistart by {np.abs(d).max():.4f} ln L"
    return ll, sd, rho


def summarise(ll, k, n, draws):
    """ln L per draw -> the IC row set."""
    i = int(np.argmax(ll)); llmax = float(ll[i])
    D = -2 * ll
    return dict(ll_max=llmax, draw_max=int(draws[i]), ll_mean=float(ll.mean()),
                k=k, n=n, AIC=2 * k - 2 * llmax,
                AICc=2 * k - 2 * llmax + 2 * k * (k + 1) / max(n - k - 1, 1),
                BIC=k * np.log(n) - 2 * llmax,
                D_mean=float(D.mean()), p_V=float(D.var(ddof=1) / 2),
                DIC=float(D.mean() + D.var(ddof=1) / 2))


def main():
    years, obs, eps, R, draws, prov = load()
    workers = max(1, (os.cpu_count() or 2) - 1)
    nfin = {s: int((np.isfinite(eps[s]) & np.isfinite(R["ladrillo"][s]).all(axis=0)
                    & np.isfinite(R["brick20"][s]).all(axis=0)).sum()) for s in SERIES}
    N_FIT = sum(nfin[s] for s in FIT_SERIES)
    print(f"ic_ladrillo_vs_brick20 | tag {TAG} | draws L {len(draws['ladrillo'])} / B {len(draws['brick20'])} | "
          f"N per series {nfin} | N_fit {N_FIT} | k_phys {K_PHYS} | workers {workers}")

    perdraw = {m: pd.DataFrame({"draw": draws[m]}) for m in MODELS}
    rows = []
    # median-series residual (the Table 4 basis): r_med = median over draws of (model - obs)
    rmed = {m: {s: np.median(R[m][s], axis=0)[None, :] for s in SERIES} for m in MODELS}

    # ---------------- arm 1 ----------------
    for m in MODELS:
        tot = np.zeros(len(draws[m]))
        for s in FIT_SERIES:
            v = ll_iid_series(R[m][s], eps[s]); perdraw[m][f"obs_iid_{s}"] = v; tot += v
            rows.append(dict(arm="obs_iid", model=m, series=s, stat="ll_max", value=float(v.max())))
            rows.append(dict(arm="obs_iid", model=m, series=s, stat="ll_median_series",
                             value=float(ll_iid_series(rmed[m][s], eps[s])[0])))
            for w, wy in WINDOWS.items():
                rows.append(dict(arm="obs_iid", model=m, series=s, stat=f"ll_max_window_{w}",
                                 value=float(ll_iid_window(R[m][s], eps[s], years, wy).max())))
        perdraw[m]["obs_iid_fit"] = tot
        S = summarise(tot, K["obs_iid"][m], N_FIT, draws[m])
        for kk, vv in S.items():
            rows.append(dict(arm="obs_iid", model=m, series="fit4", stat=kk, value=vv))
        rows.append(dict(arm="obs_iid", model=m, series="fit4", stat="ll_median_series",
                         value=float(sum(ll_iid_series(rmed[m][s], eps[s])[0] for s in FIT_SERIES))))
        # per-window totals over the 4 series, at the draw that maximises the FULL-window ll
        imax = int(np.argmax(tot))
        for w, wy in WINDOWS.items():
            v = sum(ll_iid_window(R[m][s], eps[s], years, wy)[imax] for s in FIT_SERIES)
            rows.append(dict(arm="obs_iid", model=m, series="fit4", stat=f"ll_at_maxdraw_window_{w}", value=float(v)))
        for s in OOS_SERIES:
            v = ll_iid_series(R[m][s], eps[s]); perdraw[m][f"obs_iid_{s}"] = v
            rows.append(dict(arm="obs_iid", model=m, series=s, stat="ll_max", value=float(v.max())))
            rows.append(dict(arm="obs_iid", model=m, series=s, stat="ll_at_fit4_maxdraw", value=float(v[imax])))
            rows.append(dict(arm="obs_iid", model=m, series=s, stat="ll_median_series",
                             value=float(ll_iid_series(rmed[m][s], eps[s])[0])))

    # ---------------- arm 2 ----------------
    for m in MODELS:
        tot = np.zeros(len(draws[m])); med_tot = 0.0
        for s in FIT_SERIES:
            print(f"  profiling AR(1) sd/rho: {m} {s} ({len(draws[m])} draws) ...", flush=True)
            v, sd, rho = ll_ar1_profiled(R[m][s], years, eps[s], workers)
            perdraw[m][f"ar1_prof_{s}"] = v; perdraw[m][f"ar1_prof_{s}_sd"] = sd; perdraw[m][f"ar1_prof_{s}_rho"] = rho
            tot += v
            i = int(np.argmax(v))
            rows.append(dict(arm="ar1_prof", model=m, series=s, stat="ll_max", value=float(v[i])))
            rows.append(dict(arm="ar1_prof", model=m, series=s, stat="sd_at_max", value=float(sd[i])))
            rows.append(dict(arm="ar1_prof", model=m, series=s, stat="rho_at_max", value=float(rho[i])))
            vm, sdm, rhom = ll_ar1_profiled(rmed[m][s], years, eps[s], 1)
            rows.append(dict(arm="ar1_prof", model=m, series=s, stat="ll_median_series", value=float(vm[0])))
            med_tot += float(vm[0])
        perdraw[m]["ar1_prof_fit"] = tot
        S = summarise(tot, K["ar1_prof"][m], N_FIT, draws[m])
        for kk, vv in S.items():
            rows.append(dict(arm="ar1_prof", model=m, series="fit4", stat=kk, value=vv))
        imax = int(np.argmax(tot))
        for s in FIT_SERIES:
            for q in ("", "_sd", "_rho"):
                rows.append(dict(arm="ar1_prof", model=m, series=s, stat=f"ll{q}_at_fit4_maxdraw",
                                 value=float(perdraw[m][f"ar1_prof_{s}{q}"].iloc[imax])))
        rows.append(dict(arm="ar1_prof", model=m, series="fit4", stat="ll_median_series", value=float(med_tot)))
        rows.append(dict(arm="ar1_prof", model=m, series="fit4", stat="rho_max", value=RHO_MAX))
        for s in OOS_SERIES:
            v, sd, rho = ll_ar1_profiled(R[m][s], years, eps[s], workers)
            perdraw[m][f"ar1_prof_{s}"] = v
            rows.append(dict(arm="ar1_prof", model=m, series=s, stat="ll_max", value=float(v.max())))
            rows.append(dict(arm="ar1_prof", model=m, series=s, stat="ll_at_fit4_maxdraw",
                             value=float(v[int(np.argmax(tot))])))

    out = pd.DataFrame(rows)
    out["provenance"] = (f"ic_ladrillo_vs_brick20.py | tag {TAG} | k_phys {K_PHYS} + {K_NOISE_PROF} profiled noise in ar1_prof | "
                         f"N_fit {N_FIT} | inputs: " + " || ".join(f"{m}: {prov[m]}" for m in MODELS))
    out.to_csv(OUT_CSV, index=False)
    pd.concat([perdraw[m].assign(model=m) for m in MODELS]).to_csv(OUT_DRAW, index=False)

    # ---------------- the table ----------------
    def g(arm, m, s, stat):
        return float(out[(out.arm == arm) & (out.model == m) & (out.series == s) & (out.stat == stat)].value.iloc[0])
    lines = [f"# Information-criterion test: {LABEL['ladrillo']} vs {LABEL['brick20']} hindcast (tag {TAG})", "",
             f"Common data: the four fitted component series ({', '.join(FIT_SERIES)}), 1900-2026 where observed, "
             f"N = {N_FIT} observation-years ({', '.join(f'{s} {nfin[s]}' for s in FIT_SERIES)}); one target set, one forcing, "
             f"one baseline. Parameter counts are EVERY sampled parameter of each posterior "
             f"(file: {K_TOTAL_IN_FILE}); k below is what each arm charges.", "",
             f"AR(1) arm: rho bounded at {RHO_MAX}.", "",
             "| arm | model | k | ln L (max over draws) | ln L (posterior-median series) | AIC | AICc | BIC |",
             "|---|---|---|---|---|---|---|---|"]
    for arm in ("obs_iid", "ar1_prof"):
        for m in MODELS:
            lines.append(f"| {arm} | {LABEL[m]} | {K[arm][m]} | {g(arm, m, 'fit4', 'll_max'):.1f} | "
                         f"{g(arm, m, 'fit4', 'll_median_series'):.1f} | "
                         f"{g(arm, m, 'fit4', 'AIC'):.1f} | {g(arm, m, 'fit4', 'AICc'):.1f} | {g(arm, m, 'fit4', 'BIC'):.1f} |")
    lines += ["", "## The test", ""]
    for arm in ("obs_iid", "ar1_prof"):
        dll = g(arm, "ladrillo", "fit4", "ll_max") - g(arm, "brick20", "fit4", "ll_max")
        dk = K[arm]["ladrillo"] - K[arm]["brick20"]
        daic = g(arm, "brick20", "fit4", "AIC") - g(arm, "ladrillo", "fit4", "AIC")
        dbic = g(arm, "brick20", "fit4", "BIC") - g(arm, "ladrillo", "fit4", "BIC")
        k_equiv_aic = dll                     # AIC: 1 parameter = 1 unit of ln L
        k_equiv_bic = 2 * dll / np.log(N_FIT)  # BIC: 1 parameter = (ln N)/2 units
        lines.append(f"- **{arm}**: Δln L (Ladrillo − BRICK 2.0) = **{dll:.1f}** for Δk = {dk}. "
                     f"ΔAIC (BRICK − Ladrillo) = **{daic:.1f}**, ΔBIC = **{dbic:.1f}**. "
                     f"The likelihood gain is worth {k_equiv_aic:.0f} parameters under AIC and {k_equiv_bic:.0f} under BIC "
                     f"(ln N = {np.log(N_FIT):.2f}); Ladrillo has {dk} more.")
    lines += ["", f"## Per-series ln L at each model's JOINT maximising draw (ar1_prof, rho ≤ {RHO_MAX}) and the profiled noise there", "",
              "| series | " + " | ".join(f"{LABEL[m]} ln L | sd | ρ" for m in MODELS) + " | Δln L |",
              "|---|" + "---|" * (3 * len(MODELS)) + "---|"]
    for s in FIT_SERIES:
        vals = [(g("ar1_prof", m, s, "ll_at_fit4_maxdraw"), g("ar1_prof", m, s, "ll_sd_at_fit4_maxdraw"),
                 g("ar1_prof", m, s, "ll_rho_at_fit4_maxdraw")) for m in MODELS]
        lines.append(f"| {s} | " + " | ".join(f"{a:.1f} | {b:.3f} | {c:.3f}" for a, b, c in vals) +
                     f" | {vals[0][0] - vals[1][0]:.1f} |")
    lines += ["", "## Per-window decomposition (obs_iid, at each model's own maximising draw)", "",
              "| window | " + " | ".join(LABEL[m] for m in MODELS) + " | Δln L |", "|---|---|---|---|"]
    for w in WINDOWS:
        a = g("obs_iid", "ladrillo", "fit4", f"ll_at_maxdraw_window_{w}")
        b = g("obs_iid", "brick20", "fit4", f"ll_at_maxdraw_window_{w}")
        lines.append(f"| {w} | {a:.1f} | {b:.1f} | {a - b:.1f} |")
    lines += ["", "## The total (out-of-sample for BOTH — not in either likelihood; reference only)", "",
              "| arm | " + " | ".join(f"{LABEL[m]} ln L (max) | at fit4 max-draw" for m in MODELS) + " |",
              "|---|" + "---|" * (2 * len(MODELS))]
    for arm in ("obs_iid", "ar1_prof"):
        lines.append(f"| {arm} | " + " | ".join(f"{g(arm, m, 'total', 'll_max'):.1f} | {g(arm, m, 'total', 'll_at_fit4_maxdraw'):.1f}"
                                                for m in MODELS) + " |")
    lines += ["", "## Reading, and what this does NOT show", "",
              "- ln L (max over draws) is a LOWER bound on each model's true maximum for this likelihood: neither posterior was "
              "optimised for it. Both bounds are from the same draw count.",
              "- DIC / p_V are in the CSV only: p_V = var(D)/2 is an effective parameter count only when the likelihood is "
              "the one the posterior was fitted under, which holds for neither arm here (and for BRICK 2.0 on no arm).",
              f"- In ar1_prof the profiled rho sits AT the {RHO_MAX} bound wherever the residual is a smooth bias (every BRICK 2.0 "
              "series; Ladrillo's steric and gsic): the AR(1) term then acts as a near-random-walk discrepancy that absorbs a smooth "
              "bias cheaply, so this arm's gain is a function of how much autocorrelation the noise model is allowed. See the "
              "--rho-max sensitivity files.",
              "- Ladrillo's thermal-expansion module IS BRICK's (one alpha on the same OHC), so the steric row is a tie by "
              "construction: the two best draws produce the same residual to 3 decimals.",
              "- Ladrillo was calibrated to these targets; BRICK 2.0 to Wong's. AIC/BIC correct for a fitted model's own "
              "optimism, not for a comparator fitted to different data. The structure test that removes that axis is a BRICK 2.0 "
              "arm recalibrated on the extended targets (note_2026-08-14_ladrillo_vs_brick20_scorecard.md).",
              "- obs_iid treats residual years as independent and OVERSTATES the evidence; ar1_prof is the calibrator's own "
              "form and the headline.",
              "", f"Provenance: {out.provenance.iloc[0]}"]
    open(OUT_MD, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote {os.path.relpath(OUT_CSV, REPO)}, {os.path.relpath(OUT_DRAW, REPO)}, {os.path.relpath(OUT_MD, REPO)}")


if __name__ == "__main__":
    main()
