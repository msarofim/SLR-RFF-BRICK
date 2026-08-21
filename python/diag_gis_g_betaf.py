#!/usr/bin/env python3
"""
diag_gis_g_betaf.py — items 4.1 (decide `g`) and 4.2 (fix or justify `beta_f`)
of notes/handoff_2026-08-11_greenland_pass1_complete.md §4, the two open
prerequisites for Greenland pass-1 step 5.

WHY THIS EXISTS RATHER THAN A READ OF THE EXISTING ARTIFACTS
-----------------------------------------------------------------------------
Both items were to be decided from outputs/gis_offline_cell_{fits,ridge}.csv.
Neither can be:

  1. THE A+B FIT IS NOT CONVERGED. 214 of the 225 points in the (f, beta_f)
     ridge profile -- which FIX two parameters and re-optimise the other six
     with a WEAKER inner optimiser (RIDGE_MAXFEV=1500, single start) -- score
     BELOW the reported 8-parameter optimum of nlp=42.52, by up to 24 units.
     A constrained fit cannot beat an unconstrained one at the same objective.
  2. THE RIDGE GRID IS THE WRONG RANGE. beta_f is profiled over 1e-6 to 3e-5
     only, a factor-30 window built around the railed optimum
     (RIDGE_LOCAL_DECADES=30). Over that window the fast channel is inert at
     either end, so "100% of its local range within Delta<2.3" says nothing
     about a literature SMB rate, which is 3-5 ORDERS OF MAGNITUDE away. The
     inner-optimiser scatter on that grid is +/-6 nlp units, itself larger
     than the 2.3 threshold being applied.

So this script re-establishes both premises: a converged A+B optimum under a
harder protocol, then nested-model comparisons and full-range profiles against
PRE-REGISTERED criteria stated below, before any fitting is run.

The model, objective, data and gates are imported from gis_offline_cell.py --
nothing is re-derived here.

  python3 python/diag_gis_g_betaf.py
Writes:
  outputs/gis_g_betaf_variants.csv   nested-model comparison + gates + projections
  outputs/gis_g_betaf_profiles.csv   converged 1-D profiles of g and beta_f
  figures/gis_g_betaf.png
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.optimize import minimize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gis_offline_cell as goc  # noqa: E402

REPO = goc.REPO
# Zone-tagged through goc.zoned() for the reason stated there: the SOUTH row of
# gis_g_betaf_variants.csv IS the provenance of GIS_OFFLINE_G0 and of the five
# gis_* prior centres in calibrate_mcmc_ext.jl, so a --zone=all run must not
# write over it. The --zone flag is parsed in gis_offline_cell and reaches this
# script through the import.
OUT_VARIANTS = goc.zoned(os.path.join(REPO, "outputs/gis_g_betaf_variants.csv"))
OUT_PROFILES = goc.zoned(os.path.join(REPO, "outputs/gis_g_betaf_profiles.csv"))
OUT_FIG = goc.zoned(os.path.join(REPO, "figures/gis_g_betaf.png"))

CELL = "A+B"                    # the module; handoff decision 4

# The audit's reference is READ FROM the zone's own fits file, not hardcoded.
# It used to be the literal 42.522760, captioned "outputs/gis_offline_cell_fits.csv"
# but frozen at a pre-2026-08-12 vintage -- i.e. from before fit_cell was
# corrected. By 2026-08-21 the real south value was 17.856 and all was 33.629,
# so the audit line reported a spurious "+8.9 improvement" in BOTH zones and
# read as a convergence failure that was not one. Deriving it also makes the
# audit meaningful on a zone whose fits file is not south's.
_FITS_CSV = goc.OUT_FITS        # already zone-tagged by goc.zoned()


def _reported_nlp():
    if not os.path.exists(_FITS_CSV):
        return None             # zone never fitted; audit prints "n/a"
    d = pd.read_csv(_FITS_CSV)
    r = d[d["cell"] == CELL]
    if len(r) != 1:
        return None
    return float(r["neg_log_post"].iloc[0])


REPORTED_NLP = _reported_nlp()

# ---- the harder fitting protocol -------------------------------------------
# The incumbent used 60 Nelder-Mead starts from uniform draws over bounds that
# span 5 orders of magnitude on the rate axes, so most starts land in a flat
# region and stop. Here: more starts, log-scaled draws on the rate axes, and a
# restart-until-no-improvement polish, which is what NM needs to actually
# converge a simplex that has collapsed.
N_START = 240
MAXFEV = 20000
POLISH_ROUNDS = 12
POLISH_TOL = 1e-9
LOG_AXES = ("alpha", "beta", "alpha_f", "beta_f", "alpha_s", "beta_s")
FIT_SEED = 20260812

# ---- PRE-REGISTERED DECISION CRITERIA (stated before any fit is run) -------
# Nested models, so 2*Delta(neg log post) is a likelihood-ratio statistic on
# the dropped parameters. chi2 at p=0.05: 3.841 (1 dof), 5.991 (2 dof).
LR_ALPHA = 0.05
CHI2_1DOF = 3.841
CHI2_2DOF = 5.991
# A parameter "earns its place" only if BOTH: the LR test rejects the
# restriction, AND dropping it moves something we report. The projection
# tolerance is 0.30 cm at 2100 -- the same number as the G2 mid-century gate,
# and ~5% of the 6.3 cm scenario spread the module exists to produce.
PROJ_TOL_CM = 0.30
# beta_f is profiled across its FULL prior range, not a local window.
BETAF_GRID = np.geomspace(1e-6, 0.5, 31)
G_GRID = np.linspace(0.0, 1.0, 21)
# Literature anchor for 4.2. beta_f is the TEMPERATURE-INDEPENDENT part of the
# fast channel's rate 1/tau_f = alpha_f*T + beta_f, i.e. the melt that persists
# at zero temperature anomaly. Two readings are tested rather than assumed:
#   (i)  beta_f = 0: SMB anomaly vanishes at the 1850-1900 baseline climate.
#   (ii) beta_f = 1/tau for a decadal SMB response time, the reading the
#        handoff's "fix it at a literature SMB response time" presumes.
BETAF_ZERO = 1e-6               # the bound floor; tau = 1e6 yr, i.e. off
BETAF_SMB_TAU_YR = 10.0         # decadal SMB adjustment
BETAF_SMB = 1.0 / BETAF_SMB_TAU_YR
T_REF_C = 1.5                   # regional anomaly at which tau_f is quoted

_rng = np.random.default_rng(FIT_SEED)


# =============================================================================
# fitting
# =============================================================================
def build_ctx():
    drv = pd.read_csv(goc.DRIVER_CSV).set_index("year")[goc.DRIVER_ZONE]
    last_obs_year = int(drv.index.max())
    t_reg = goc.extend(drv)
    gmst_hist = goc.extend(goc.load_gmst())
    ty, obs, sig = goc.load_target()
    ctx = dict(t_reg=t_reg, t_gmst=gmst_hist, ty=ty, obs=obs, sig=sig,
               ti=[goc._yi[y] for y in ty])
    return ctx, last_obs_year


def draw_start(names):
    """Uniform on the linear axes, log-uniform on the rate axes."""
    x = np.empty(len(names))
    for i, n in enumerate(names):
        lo, hi = goc.PBOUNDS[n]
        if n in LOG_AXES:
            x[i] = np.exp(_rng.uniform(np.log(max(lo, 1e-6)), np.log(hi)))
        else:
            x[i] = _rng.uniform(lo, hi)
    return x


def fit(ctx, fixed=None, n_start=N_START, x0_extra=()):
    """Fit CELL with `fixed` = {name: value} held. Returns (theta, nlp)."""
    fixed = dict(fixed or {})
    names = goc.cell_params(CELL)
    free = [n for n in names if n not in fixed]

    def expand(xf):
        t, j = np.empty(len(names)), 0
        for i, n in enumerate(names):
            if n in fixed:
                t[i] = fixed[n]
            else:
                t[i], j = xf[j], j + 1
        return t

    def obj(xf):
        return goc.neg_log_post(CELL, expand(xf), ctx)

    def polish(x):
        v = obj(x)
        for _ in range(POLISH_ROUNDS):
            r = minimize(obj, x, method="Nelder-Mead",
                         options=dict(maxiter=MAXFEV, maxfev=MAXFEV,
                                      xatol=1e-11, fatol=1e-11))
            if not (r.fun < v - POLISH_TOL):
                return r.x if r.fun < v else x, min(r.fun, v)
            x, v = r.x, r.fun
        return x, v

    best, best_v = None, np.inf
    starts = [np.array([s[n] for n in free]) for s in x0_extra]
    starts += [draw_start(free) for _ in range(n_start)]
    for x0 in starts:
        r = minimize(obj, x0, method="Nelder-Mead",
                     options=dict(maxiter=MAXFEV, maxfev=MAXFEV,
                                  xatol=1e-9, fatol=1e-9))
        if r.fun < best_v:
            best, best_v = r.x, r.fun
    best, best_v = polish(best)
    return dict(zip(names, expand(best))), best_v


def describe(theta, nlp, ctx, last_obs_year, label, ref_nlp=None, n_fixed=0):
    order = [theta[n] for n in goc.cell_params(CELL)]
    L, Lf = goc.run_cell(CELL, order, ctx["t_reg"], ctx["t_gmst"])
    gates = goc.evaluate_gates(L, ctx)
    proj = goc.project(CELL, order, ctx["t_reg"], ctx["t_gmst"], last_obs_year)
    spread = proj["SSP5-8.5"] - proj["SSP1-2.6"]
    rails = "|".join(n for n in goc.cell_params(CELL)
                     if abs(theta[n] - goc.PBOUNDS[n][0]) < 1e-9
                     or abs(theta[n] - goc.PBOUNDS[n][1]) < 1e-9)
    tau_f = 1.0 / max(theta["alpha_f"] * T_REF_C + theta["beta_f"], 1e-12)
    tau_s = 1.0 / max(theta["alpha_s"] * T_REF_C + theta["beta_s"], 1e-12)
    row = dict(variant=label, n_free=len(goc.cell_params(CELL)) - n_fixed,
               neg_log_post=nlp,
               lr_2delta=np.nan if ref_nlp is None else 2.0 * (nlp - ref_nlp),
               railed=rails, tau_fast_yr=tau_f, tau_slow_yr=tau_s,
               **gates, surface_share=goc.model_surface_share(L, Lf),
               spread_2100_cm=spread,
               gate4_spread=(goc.GATE_SPREAD_RANGE_CM[0] <= spread
                             <= goc.GATE_SPREAD_RANGE_CM[1]),
               **{f"proj_{k}": v for k, v in proj.items()},
               params="; ".join(f"{k}={theta[k]:.6g}"
                                for k in goc.cell_params(CELL)))
    return row, L


def profile(ctx, name, grid, x0):
    """1-D profile: fix `name` on the grid, re-optimise everything else from
    the converged optimum plus fresh starts. Fewer starts than the headline
    fit, but seeded at the optimum, which is what makes it monotone-clean."""
    rows = []
    for v in grid:
        theta, nlp = fit(ctx, fixed={name: float(v)}, n_start=40, x0_extra=(x0,))
        rows.append(dict(parameter=name, value=float(v), nlp=nlp,
                         params="; ".join(f"{k}={theta[k]:.6g}"
                                          for k in goc.cell_params(CELL))))
        print(f"    {name}={v:<12.6g} nlp={nlp:10.4f}")
    return rows


# =============================================================================
def main():
    print(f"diag_gis_g_betaf | commit={goc.COMMIT} | cell={CELL} | "
          f"zone={goc.DRIVER_ZONE} | amp={goc.AMP_MEAN:.7f} "
          f"({goc.AMP_WINDOW} window, derived from gis_amp_prior.csv)")
    print(f"  writes {os.path.relpath(OUT_VARIANTS, REPO)}")
    print(f"  protocol: {N_START} starts (log-scaled on rate axes), "
          f"maxfev={MAXFEV}, polish<={POLISH_ROUNDS} rounds")
    print(f"  PRE-REGISTERED: keep a parameter only if 2*Delta(nlp) > "
          f"{CHI2_1DOF} (1 dof, p={LR_ALPHA}) AND some 2100 projection moves "
          f"more than {PROJ_TOL_CM} cm")
    ctx, last_obs_year = build_ctx()

    print("\n[1] convergence audit — refit the full 8-parameter A+B")
    theta_full, nlp_full = fit(ctx)
    if REPORTED_NLP is None:
        print(f"  reported  nlp = n/a ({os.path.basename(_FITS_CSV)} absent "
              f"or has no {CELL} row)")
        print(f"  converged nlp = {nlp_full:.4f}")
    else:
        print(f"  reported  nlp = {REPORTED_NLP:.4f}   "
              f"(from {os.path.basename(_FITS_CSV)})")
        print(f"  converged nlp = {nlp_full:.4f}   "
              f"(improvement {REPORTED_NLP - nlp_full:+.4f})")
    print("  " + "; ".join(f"{k}={theta_full[k]:.6g}"
                           for k in goc.cell_params(CELL)))

    print("\n[2] nested variants")
    variants = [
        ("full", {}, 0),
        ("g=0", {"g": 0.0}, 1),
        ("beta_f=0", {"beta_f": BETAF_ZERO}, 1),
        (f"beta_f=1/{BETAF_SMB_TAU_YR:.0f}yr", {"beta_f": BETAF_SMB}, 1),
        ("g=0 & beta_f=0", {"g": 0.0, "beta_f": BETAF_ZERO}, 2),
    ]
    rows, series = [], {"year": goc.YEARS}
    for label, fixed, nfix in variants:
        theta, nlp = (theta_full, nlp_full) if not fixed else \
            fit(ctx, fixed=fixed, x0_extra=(theta_full,))
        row, L = describe(theta, nlp, ctx, last_obs_year, label,
                          ref_nlp=None if not fixed else nlp_full, n_fixed=nfix)
        rows.append(row)
        series[f"{label}_hindcast_cm"] = goc.reref(L)
        chi2 = CHI2_1DOF if nfix == 1 else CHI2_2DOF
        verdict = "" if not fixed else (
            f"  LR 2d={row['lr_2delta']:+.3f} vs chi2({nfix})={chi2}"
            f" -> {'REJECT restriction' if row['lr_2delta'] > chi2 else 'restriction OK'}")
        print(f"  {label:16s} nlp={nlp:9.4f} rmse={row['rmse_cm']:.3f} "
              f"spread={row['spread_2100_cm']:5.2f} "
              f"G1{'+' if row['gate1_rate'] else '-'}"
              f"G2{'+' if row['gate2_midcen'] else '-'}"
              f"G3{'+' if row['gate3_shape'] else '-'}{verdict}")

    fitdf = pd.DataFrame(rows)
    fitdf.to_csv(OUT_VARIANTS, index=False)

    print("\n[3] full-range profiles (the ridge redone against a converged reference)")
    prof = profile(ctx, "beta_f", BETAF_GRID, theta_full)
    prof += profile(ctx, "g", G_GRID, theta_full)
    profdf = pd.DataFrame(prof)
    profdf["delta_nlp"] = profdf["nlp"] - nlp_full
    profdf.to_csv(OUT_PROFILES, index=False, float_format="%.9g")

    report(fitdf, profdf, nlp_full)
    make_figure(profdf, series, ctx, nlp_full)
    for p in (OUT_VARIANTS, OUT_PROFILES, OUT_FIG):
        print(f"wrote {os.path.relpath(p, REPO)}")


def report(fitdf, profdf, nlp_full):
    print("\nSUMMARY")
    base = fitdf.set_index("variant")
    for name, fixed_label, chi2 in (("g", "g=0", CHI2_1DOF),
                                    ("beta_f", "beta_f=0", CHI2_1DOF)):
        r = base.loc[fixed_label]
        moved = max(abs(r[f"proj_{s}"] - base.loc["full", f"proj_{s}"])
                    for s in goc.PROJ_SCENARIOS)
        lr_rej = r["lr_2delta"] > chi2
        keep = lr_rej and moved > PROJ_TOL_CM
        print(f"  {name:8s} 2*Delta={r['lr_2delta']:+8.3f} (chi2={chi2}) "
              f"{'REJECT' if lr_rej else 'accept'} restriction; "
              f"max |Delta proj 2100| = {moved:.3f} cm "
              f"({'>' if moved > PROJ_TOL_CM else '<='} {PROJ_TOL_CM}) "
              f"-> {'KEEP FREE' if keep else 'FIX'}")
    p = profdf[profdf.parameter == "beta_f"]
    within = p[p.delta_nlp < goc.RIDGE_DELTA]
    print(f"  beta_f full-range profile: Delta<{goc.RIDGE_DELTA} over "
          f"{within.value.min():.3g} to {within.value.max():.3g} "
          f"({100 * len(within) / len(p):.0f}% of the {p.value.min():.3g}-"
          f"{p.value.max():.3g} grid)")
    q = profdf[profdf.parameter == "g"]
    withing = q[q.delta_nlp < goc.RIDGE_DELTA]
    print(f"  g      full-range profile: Delta<{goc.RIDGE_DELTA} over "
          f"{withing.value.min():.3g} to {withing.value.max():.3g} "
          f"({100 * len(withing) / len(q):.0f}% of [0,1])")


def make_figure(profdf, series, ctx, nlp_full):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(17, 5.0))
    for ax, name, xlabel, logx in (
            (axes[0], "beta_f", r"$\beta_f$  (yr$^{-1}$)", True),
            (axes[1], "g", "$g$  (fraction of the 1850 commitment realised)", False)):
        p = profdf[profdf.parameter == name]
        ax.plot(p.value, p.delta_nlp, "o-", color="#1f4e79", ms=4)
        ax.axhline(goc.RIDGE_DELTA, color="crimson", ls="--", lw=1.2,
                   label=f"$\\Delta$ = {goc.RIDGE_DELTA}")
        ax.axhline(CHI2_1DOF / 2, color="darkorange", ls=":", lw=1.2,
                   label=f"$\\chi^2_1$/2 = {CHI2_1DOF / 2:.2f}")
        if logx:
            ax.set_xscale("log")
            ax.axvline(BETAF_SMB, color="0.4", ls="-.", lw=1.2,
                       label=f"$1/{BETAF_SMB_TAU_YR:.0f}$ yr")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(r"$\Delta$ neg log posterior")
        ax.set_title(f"profile of {name} (converged reference {nlp_full:.2f})")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
        ax.set_ylim(-0.5, min(40, max(5, p.delta_nlp.max() * 1.05)))

    ax = axes[2]
    t = pd.read_csv(goc.TARGETS_CSV).set_index("year")
    g = t[["gis", "gis_lo", "gis_hi"]].dropna().loc[goc.FIT_WIN[0]:goc.FIT_WIN[1]]
    ax.fill_between(g.index, g.gis_lo, g.gis_hi, color="0.85", label="target 90%")
    ax.plot(g.index, g.gis, "k-", lw=2.2, label="target")
    for k, v in series.items():
        if k == "year":
            continue
        ax.plot(series["year"], v, lw=1.3, label=k)
    ax.set_xlim(*goc.FIT_WIN)
    seg = g.loc[goc.FIT_WIN[0]:goc.FIT_WIN[1]]
    ax.set_ylim(seg.gis_lo.min() - 0.5, seg.gis_hi.max() + 0.5)
    ax.set_xlabel("year")
    ax.set_ylabel("GIS contribution (cm, 1995-2005)")
    ax.set_title(f"{CELL} hindcast under each restriction")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_FIG, dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    main()
