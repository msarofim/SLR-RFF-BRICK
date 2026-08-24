#!/usr/bin/env python
"""
diag_curvature_deficit_errorbar.py — PUT AN ERROR BAR ON THE MODEL'S OWN
                                     CURVATURE DEFICITS

THE FINDING UNDER TEST.  Three numbers started the whole curvature arc and none
of them has ever carried an error bar:

    gis    accel ratio 0.629x     (`gis_obs_accel_deficit`)
    ais    accel ratio 0.727x     (`ais_curvature_deficit_shared`)
    total  accel ratio 0.571x     (`curvature_deficit_is_recon_gap`)

`handoff_2026-08-24f` §6 then attached a bar to the TARGET-side numbers and found
the arc's other claims sit at 0.02-1.78 sigma.  Its §9 item 1, restated as item 1
of `-24g` §7 and still top: *"if these are 1-sigma effects the conclusion changes
from 'explained by the reconstruction gap' to 'never measurable in the first
place'."*  This script settles that.

WHAT WAS MISSING, AND WHERE EACH BAR COMES FROM.  `diag_curvature_deficit_2x2.jl`
runs 2000 posterior draws and then collapses them to a MEDIAN trajectory before
measuring, so the model's own posterior width never reaches the ratio.  Three
independent sources of uncertainty are assembled here:

  [A] OUR posterior spread          -- per-draw accel, from the Julia panel's new
                                       `..._perdraw_<tag>.csv`.  This is the bar
                                       item 1 actually asks for.
  [B] OBS estimator scatter         -- AR(1)-inflated OLS se of 2*b2, transcribed
                                       from `diag_curvature_postsplice_halving.py`
                                       (same estimator, same MC gate, same seed)
                                       so the numbers compose with -24f §6.
  [C] OBS published band            -- the targets' own `_lo`/`_hi`.  Its year-to-
                                       year correlation is unknown, so it is
                                       BRACKETED by two arms that bound it:
                                       perfectly correlated (a common z) and
                                       perfectly independent.  [B] is a LOWER
                                       bound precisely because it omits [C].

A DELIBERATE NON-CHOICE.  [B] and [C] are two accounts of the SAME observational
uncertainty, not two independent sources, so they are reported side by side and
their quadrature sum is labelled `conservative`, never treated as the estimate.

THE RATIO IS NOT SCORED BY DIVIDING ENDPOINTS (`endpoint_division_is_not_a_ratio_band`).
The DIFFERENCE ours-obs carries the verdict; the ratio's band is Monte-Carlo, and
the fraction of draws in which the DENOMINATOR changes sign is reported, because a
ratio band straddling a near-zero denominator is unbounded and reads as agreement.

    source ~/climate-env/bin/activate
    python python/diag_curvature_deficit_errorbar.py [--tag=L14]

Reads   outputs/diag_curvature_deficit_perdraw_<tag>.csv
        outputs/diag_curvature_deficit_2x2_<tag>.csv
        outputs/recalib_targets_ext.csv
Writes  outputs/diag_curvature_deficit_errorbar_{summary,ratio,chain}_<tag>.csv
        outputs/log_curvature_deficit_errorbar_<tag>.txt
"""
import os
import sys
import csv
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# CONSTANTS -- every label, filename and printed window derives from these.
# ---------------------------------------------------------------------------
TAG = next((a[6:] for a in sys.argv[1:] if a.startswith("--tag=")), "L14")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERDRAW = os.path.join(REPO, "outputs", f"diag_curvature_deficit_perdraw_{TAG}.csv")
PANEL = os.path.join(REPO, "outputs", f"diag_curvature_deficit_2x2_{TAG}.csv")
TARGETS = os.path.join(REPO, "outputs", "recalib_targets_ext.csv")
OUT_SUM = os.path.join(REPO, "outputs", f"diag_curvature_deficit_errorbar_summary_{TAG}.csv")
OUT_RAT = os.path.join(REPO, "outputs", f"diag_curvature_deficit_errorbar_ratio_{TAG}.csv")
OUT_CHN = os.path.join(REPO, "outputs", f"diag_curvature_deficit_errorbar_chain_{TAG}.csv")

# component -> target column, matching PANEL in diag_curvature_deficit_2x2.jl
TARGET_COL = {"ais": "ais", "gis": "gis", "gsic_hind": "gsic",
              "te": "steric", "total": "dang"}
# the shipped deficits this script exists to score
SHIPPED_RATIO = {"gis": 0.629, "ais": 0.727, "total": 0.571}
BAND_Z = 1.96             # the targets' _lo/_hi are 95% bounds
MC_SEED = 2026            # [SE-MC] and [RATIO-MC] are gates, so their draws are fixed
MC_N = 20000
RATIO_MC_N = 200000
PERM_N = 4000             # [EXCH] between-chain exchangeability permutation test
PERM_ALPHA = 0.05
QUANTILES = [2.5, 16.0, 50.0, 84.0, 97.5]
SIG_LEVEL = 2.0           # |z| above which a difference is called RESOLVED
DENOM_FLIP_ALERT = 0.01   # fraction of MC draws flipping the denominator's sign


def _design(x):
    return np.vstack([np.ones_like(x), x, x ** 2]).T


def accel_of(v, yrs, w):
    """Quadratic-fit acceleration of a cumulative series, cm/yr^2.
    Transcribed from julia/diag_curvature_deficit_2x2.jl:84 via
    python/diag_curvature_postsplice_halving.py:89 -- NaN on any NaN in window."""
    i0, i1 = np.where(yrs == w[0])[0], np.where(yrs == w[1])[0]
    if len(i0) == 0 or len(i1) == 0:
        return np.nan
    sl = slice(i0[0], i1[0] + 1)
    x = (yrs[sl] - w[0]).astype(float)
    y = np.asarray(v[sl], dtype=float)
    if np.isnan(y).any():
        return np.nan
    return 2.0 * np.linalg.lstsq(_design(x), y, rcond=None)[0][2]


def accel_se(v, yrs, w):
    """(accel, ols se, AR(1)-inflated se) -- same estimator as accel_of."""
    i0, i1 = np.where(yrs == w[0])[0], np.where(yrs == w[1])[0]
    if len(i0) == 0 or len(i1) == 0:
        return (np.nan,) * 4
    sl = slice(i0[0], i1[0] + 1)
    x = (yrs[sl] - w[0]).astype(float)
    y = np.asarray(v[sl], dtype=float)
    if np.isnan(y).any():
        return (np.nan,) * 4
    A = _design(x)
    b = np.linalg.lstsq(A, y, rcond=None)[0]
    r = y - A @ b
    s2 = r @ r / (len(x) - 3)
    se = 2.0 * np.sqrt(s2 * np.linalg.inv(A.T @ A)[2, 2])
    rho = np.corrcoef(r[:-1], r[1:])[0, 1]
    return (2.0 * b[2], se, se * np.sqrt(max((1 + rho) / (1 - rho), 1.0)), rho)


def _se_mc(v, yrs, w, seed=MC_SEED, n=MC_N):
    """Matched Monte Carlo the analytic se must not under-state. Verbatim from
    diag_curvature_postsplice_halving.py:392."""
    i0, i1 = np.where(yrs == w[0])[0][0], np.where(yrs == w[1])[0][0]
    x = (yrs[i0:i1 + 1] - w[0]).astype(float)
    y = np.asarray(v[i0:i1 + 1], dtype=float)
    A = _design(x)
    r = y - A @ np.linalg.lstsq(A, y, rcond=None)[0]
    rho, sd, m = np.corrcoef(r[:-1], r[1:])[0, 1], r.std(ddof=3), len(x)
    rng = np.random.default_rng(seed)
    e = np.empty((n, m))
    e[:, 0] = rng.standard_normal(n) * sd
    sh = rng.standard_normal((n, m)) * sd * np.sqrt(max(1 - rho ** 2, 0.0))
    for t in range(1, m):
        e[:, t] = rho * e[:, t - 1] + sh[:, t]
    return float((2.0 * (e @ np.linalg.pinv(A)[2])).std())


def band_arms(sig, yrs, w):
    """1-sigma contribution of the target's PUBLISHED band to its accel, under the
    two correlation structures that BRACKET the unknown truth.

      corr  : every year moves together by one common z. The accel shift is then
              z * accel_of(sigma(t)) -- NOT zero, because the band's WIDTH has its
              own curvature (these bands pinch near 2019).
      indep : independent per year -> se = 2*sqrt(sum_t P_t^2 sigma_t^2), P = pinv(A)[2].
    Any real correlation lies between them."""
    i0, i1 = np.where(yrs == w[0])[0], np.where(yrs == w[1])[0]
    if len(i0) == 0 or len(i1) == 0:
        return np.nan, np.nan
    sl = slice(i0[0], i1[0] + 1)
    x = (yrs[sl] - w[0]).astype(float)
    s = np.asarray(sig[sl], dtype=float)
    if np.isnan(s).any():
        return np.nan, np.nan
    P = np.linalg.pinv(_design(x))[2]
    return abs(2.0 * (P @ s)), 2.0 * float(np.sqrt((P ** 2) @ (s ** 2)))


def log(msg=""):
    print(msg)
    LOG.write(msg + "\n")


LOG = open(os.path.join(REPO, "outputs",
                        f"log_curvature_deficit_errorbar_{TAG}.txt"), "w")

# ===========================================================================
# [1] LOAD
# ===========================================================================
log("=" * 92)
log(f"CURVATURE DEFICIT -- WITH AN ERROR BAR | tag {TAG}")
log("=" * 92)
pd_raw = pd.read_csv(PERDRAW)
panel = pd.read_csv(PANEL)
tgt = pd.read_csv(TARGETS)
YRS = tgt["year"].values.astype(int)
log(f"  per-draw : {PERDRAW.split('/')[-1]}  {len(pd_raw)} rows, "
    f"{pd_raw.component.nunique()} components x {pd_raw.draw.nunique()} draws, "
    f"{pd_raw.chain_seed.nunique()} chains")
log(f"  panel    : {PANEL.split('/')[-1]}")
log(f"  targets  : {TARGETS.split('/')[-1]}  {YRS[0]}-{YRS[-1]}")

# ===========================================================================
# [2] MEDIAN-OF-CURVATURE vs CURVATURE-OF-MEDIAN
#     The shipped ratio is accel(median trajectory). The natural posterior
#     summary is median(accel per draw). They are NOT the same statistic and the
#     difference has never been reported. Neither is wrong; the point is which
#     one the 0.65x/0.727x/0.571x are, and by how much the other would move them.
# ===========================================================================
log("\n" + "=" * 92)
log("[2] THE SHIPPED NUMBER IS accel(MEDIAN TRAJECTORY), NOT median(accel PER DRAW)")
log("=" * 92)
log(f"  {'component':11s} {'accel(median)':>14s} {'median(accel)':>14s} {'diff':>11s} {'rel':>8s}")
estim = {}
for _, r in panel.iterrows():
    c = r["component"]
    sub = pd_raw[pd_raw.component == c]
    ma = float(np.nanmedian(sub["accel"].values))
    d = ma - r["ours_accel"]
    estim[c] = (r["ours_accel"], ma)
    log(f"  {c:11s} {r['ours_accel']:14.6f} {ma:14.6f} {d:+11.6f} "
        f"{d / r['ours_accel'] * 100:7.2f}%")
log("  -> the two estimators are reported separately throughout; the ratio column")
log("     labelled `shipped` always uses accel(median), the arc's own convention.")

# ===========================================================================
# [3] THE OBSERVATIONAL BARS  [B] estimator scatter and [C] published band
# ===========================================================================
log("\n" + "=" * 92)
log("[3] OBSERVATIONAL BARS -- [B] AR(1) estimator scatter, [C] the published band")
log("=" * 92)
obs = {}
for _, r in panel.iterrows():
    c, col = r["component"], TARGET_COL[r["component"]]
    w = tuple(int(t) for t in r["accel_window"].split("-"))
    sub = tgt[["year", col, f"{col}_lo", f"{col}_hi"]].dropna()
    oy = sub["year"].values.astype(int)
    ov = sub[col].values.astype(float)
    sig = ((sub[f"{col}_hi"].values - sub[f"{col}_lo"].values) / 2.0 / BAND_Z)
    a, se_ols, se_ar1, rho = accel_se(ov, oy, w)
    mc = _se_mc(ov, oy, w)
    ok = "PASS" if se_ar1 >= mc else "FAIL"
    b_corr, b_indep = band_arms(sig, oy, w)
    obs[c] = dict(window=w, accel=a, se_ar1=se_ar1, se_ols=se_ols, mc=mc, rho=rho,
                  band_corr=b_corr, band_indep=b_indep)
    log(f"  [SE-MC] {c:11s} {w[0]}-{w[1]}  analytic {se_ar1:.6f} vs MC {mc:.6f} "
        f"= {se_ar1 / mc:.2f}x -> {ok} ({'conservative' if ok == 'PASS' else 'UNDERSTATES'})"
        f"   [rho {rho:+.3f}, inflation {se_ar1 / se_ols:.2f}x]")
    assert se_ar1 >= mc, f"analytic se understates the MC spread for {c}"
log("")
log(f"  {'component':11s} {'obs accel':>11s} {'[B] AR(1)':>11s} "
    f"{'[C] corr':>11s} {'[C] indep':>11s} {'panel obs':>11s}")
for _, r in panel.iterrows():
    o = obs[r["component"]]
    log(f"  {r['component']:11s} {o['accel']:+11.6f} {o['se_ar1']:11.6f} "
        f"{o['band_corr']:11.6f} {o['band_indep']:11.6f} {r['obs_accel']:+11.6f}")
    assert abs(o["accel"] - r["obs_accel"]) < 1e-12, \
        f"[IDENT] obs accel disagrees with the shipped panel for {r['component']}"
log("  [IDENT] obs accel reproduces the shipped panel exactly for all components.")

# ===========================================================================
# [4] THE VERDICT TABLE -- difference ours - obs, with each bar in turn
# ===========================================================================
log("\n" + "=" * 92)
log("[4] IS THE DEFICIT RESOLVED?  difference = ours - obs, z = difference / sigma")
log("=" * 92)
log("  [A] is OUR posterior sd across draws. sigma_B = hypot([A],[B]); sigma_BC adds the")
log("  WIDER band arm in quadrature and is CONSERVATIVE (it double-counts the part of")
log("  the year-to-year scatter the published band already describes).")
log("")
log(f"  {'component':11s} {'window':>9s} {'ours med':>10s} {'[A] sd':>9s} "
    f"{'obs':>10s} {'diff':>10s} {'z_A':>7s} {'z_B':>6s} {'z_BC':>6s} {'z_MC':>6s} "
    f"{'obs pctile':>10s}  verdict")
rows = []
for _, r in panel.iterrows():
    c = r["component"]
    o = obs[c]
    draws = pd_raw[pd_raw.component == c]["accel"].values.astype(float)
    draws = draws[np.isfinite(draws)]
    sd_a = float(draws.std(ddof=1))
    med = float(np.median(draws))
    shipped = float(r["ours_accel"])
    diff = med - o["accel"]
    s_b = float(np.hypot(sd_a, o["se_ar1"]))
    s_bc = float(np.hypot(s_b, max(o["band_corr"], o["band_indep"])))
    z_b, z_bc = diff / s_b, diff / s_bc
    ## [B] is required to be conservative (the [SE-MC] gate above), and for `gis` it is
    ## 2.7x the matched MC. So the verdict is also run on the LEAST conservative bar the
    ## gate permits -- the MC spread itself -- to check that "UNRESOLVED" is not an
    ## artefact of an inflated error bar. This arm is a robustness check, not the estimate.
    s_mc = float(np.hypot(sd_a, o["mc"]))
    z_mc = diff / s_mc
    pct = float((draws < o["accel"]).mean() * 100.0)
    ## z_A is the SAME difference divided by our posterior sd ALONE -- no observational
    ## uncertainty at all. It is not a verdict (obs is not known exactly); it is printed
    ## because it is why `obs pctile` saturates at 0/100%, and because the honest reading
    ## of this table is that the deficit is enormous against the MODEL's width and
    ## invisible against the OBSERVATION's.
    z_a = diff / sd_a
    zs = [abs(z_b), abs(z_bc), abs(z_mc)]
    verdict = ("RESOLVED" if min(zs) >= SIG_LEVEL else
               "UNRESOLVED" if max(zs) < SIG_LEVEL else "BAR-DEPENDENT")
    log(f"  {c:11s} {r['accel_window']:>9s} {med:+10.6f} {sd_a:9.6f} "
        f"{o['accel']:+10.6f} {diff:+10.6f} {z_a:7.1f} {z_b:6.2f} {z_bc:6.2f} "
        f"{z_mc:6.2f} {pct:9.1f}%  {verdict}")
    q = np.percentile(draws, QUANTILES)
    rows.append(dict(component=c, window=r["accel_window"],
                     ours_accel_shipped=shipped, ours_accel_median=med,
                     ours_sd=sd_a, **{f"ours_p{p:g}": v for p, v in zip(QUANTILES, q)},
                     obs_accel=o["accel"], obs_se_ar1=o["se_ar1"],
                     obs_band_corr=o["band_corr"], obs_band_indep=o["band_indep"],
                     obs_se_mc=o["mc"],
                     difference=diff, sigma_B=s_b, sigma_BC=s_bc, sigma_MC=s_mc,
                     z_A_model_only=z_a, z_B=z_b, z_BC=z_bc, z_MC=z_mc, obs_percentile_in_ensemble=pct,
                     verdict=verdict,
                     shipped_ratio=SHIPPED_RATIO.get(c, float("nan"))))
with open(OUT_SUM, "w", newline="") as f:
    w_ = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w_.writeheader()
    w_.writerows(rows)
log(f"\n  wrote {os.path.relpath(OUT_SUM, REPO)}")

# ===========================================================================
# [5] THE RATIO, MONTE-CARLO -- never by dividing the endpoints of two bands
# ===========================================================================
log("\n" + "=" * 92)
log("[5] THE RATIO ours/obs, Monte-Carlo")
log("=" * 92)
log(f"  numerator resampled from the {len(pd_raw[pd_raw.component == panel.component[0]])} "
    f"posterior draws (empirical, not Gaussian); denominator ~ N(obs, sigma_B_obs).")
log("  `denom flip` is the fraction of MC draws in which the observed acceleration")
log("  changes SIGN -- above it the ratio band is unbounded and means nothing.")
log("")
log(f"  {'component':11s} {'shipped':>8s} {'MC p50':>8s} {'MC p2.5':>9s} {'MC p97.5':>9s} "
    f"{'denom flip':>10s}  reading")
rng = np.random.default_rng(MC_SEED)
rrows = []
for _, r in panel.iterrows():
    c = r["component"]
    o = obs[c]
    draws = pd_raw[pd_raw.component == c]["accel"].values.astype(float)
    draws = draws[np.isfinite(draws)]
    num = rng.choice(draws, size=RATIO_MC_N, replace=True)
    sig_obs = float(np.hypot(o["se_ar1"], max(o["band_corr"], o["band_indep"])))
    den = o["accel"] + rng.standard_normal(RATIO_MC_N) * sig_obs
    flip = float((np.sign(den) != np.sign(o["accel"])).mean())
    rat = num / den
    p50, lo, hi = np.percentile(rat, [50, 2.5, 97.5])
    if flip > DENOM_FLIP_ALERT:
        reading = f"denominator sign not secure -- band tails meaningless"
    elif lo > 1.0 or hi < 1.0:
        reading = "1.0 EXCLUDED -- ratio resolved"
    else:
        reading = "1.0 inside the band -- ratio NOT resolved"
    log(f"  {c:11s} {r['accel_ratio']:8.3f} {p50:8.3f} {lo:9.3f} {hi:9.3f} "
        f"{flip * 100:9.2f}%  {reading}")
    rrows.append(dict(component=c, window=r["accel_window"],
                      ratio_shipped=r["accel_ratio"], ratio_mc_p50=p50,
                      ratio_mc_p2_5=lo, ratio_mc_p97_5=hi,
                      denom_sign_flip_frac=flip, denom_sigma=sig_obs,
                      reading=reading))
with open(OUT_RAT, "w", newline="") as f:
    w_ = csv.DictWriter(f, fieldnames=list(rrows[0].keys()))
    w_.writeheader()
    w_.writerows(rrows)
log(f"\n  wrote {os.path.relpath(OUT_RAT, REPO)}")

# ===========================================================================
# [6] BETWEEN-CHAIN SPREAD, in the deliverable's own units
#     `rhat_denominator_forgives`: a convergence verdict is a ratio and forgives a
#     wide band, so the between-chain RANGE of the reported quantity is printed
#     beside it in cm/yr^2 rather than left to an R-hat column.
# ===========================================================================
log("\n" + "=" * 92)
log("[6] BETWEEN-CHAIN SPREAD OF THE REPORTED ACCELERATION (cm/yr^2)")
log("=" * 92)
SEEDS_SORTED = sorted(int(s) for s in pd_raw.chain_seed.unique())
log(f"  {'component':11s} " + " ".join(f"{'seed' + str(s):>11s}" for s in SEEDS_SORTED)
    + f" {'range':>11s} {'/ [A] sd':>9s}")
crows = []
for _, r in panel.iterrows():
    c = r["component"]
    sub = pd_raw[pd_raw.component == c]
    meds = [float(np.nanmedian(sub[sub.chain_seed == s]["accel"].values))
            for s in SEEDS_SORTED]
    sd_a = float(sub["accel"].values.std(ddof=1))
    rng_ = max(meds) - min(meds)
    log(f"  {c:11s} " + " ".join(f"{m:11.6f}" for m in meds) +
        f" {rng_:11.6f} {rng_ / sd_a:9.3f}")
    ## [EXCH] is the between-chain range larger than pooling the draws and relabelling
    ## them at random would give?  A permutation test, because the analytic range of 4
    ## sample medians has no closed form worth trusting at these n.  p is the fraction of
    ## permutations reaching the observed range; small p = the chains have NOT mixed on
    ## THIS quantity, and the deficit's bar is then under-stated, not over-stated.
    prng = np.random.default_rng(MC_SEED)
    a_all = sub["accel"].values.astype(float)
    lab = sub["chain_seed"].values
    sizes = [int((lab == s0).sum()) for s0 in SEEDS_SORTED]
    null = np.empty(PERM_N)
    for b in range(PERM_N):
        pm = prng.permutation(a_all)
        off, ms = 0, []
        for n_ in sizes:
            ms.append(np.nanmedian(pm[off:off + n_]))
            off += n_
        null[b] = max(ms) - min(ms)
    pval = float((null >= rng_).mean())
    mix = "MIXED" if pval > PERM_ALPHA else "NOT MIXED"
    log(f"      [EXCH] permutation p = {pval:.4f} (null median range "
        f"{np.median(null):.6f}, observed {rng_:.6f} = {rng_ / np.median(null):.1f}x) "
        f"-> {mix}")
    crows.append(dict(component=c, **{f"seed{s}": m for s, m in
                                      zip(SEEDS_SORTED, meds)},
                      chain_median_range=rng_, ensemble_sd=sd_a,
                      range_over_sd=rng_ / sd_a,
                      perm_null_median_range=float(np.median(null)),
                      perm_p=pval, mixing=mix))
with open(OUT_CHN, "w", newline="") as f:
    w_ = csv.DictWriter(f, fieldnames=list(crows[0].keys()))
    w_.writeheader()
    w_.writerows(crows)
log(f"\n  wrote {os.path.relpath(OUT_CHN, REPO)}")
LOG.close()
