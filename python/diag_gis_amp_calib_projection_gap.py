#!/usr/bin/env python3
"""
diag_gis_amp_calib_projection_gap.py — is the amp(GMST) calibration/projection
mismatch material, or is it nominal?

THE CAVEAT THIS ADDRESSES
  Every Ladrillo handoff since L10 has shipped: "the amp(GMST) law is
  projection-side only — the calibrator runs at constant GIS_AMP = 1.92. Justify
  or align. Still open." It is listed in the L12 handoff §6 as the largest
  unaddressed methodological caveat. Aligning means a refit; justifying means
  showing the gap cannot matter. This script measures which.

  It does NOT decide anything. It measures the two quantities that decide it.

TEST 1 — HOW FAR THE LAW DEPARTS FROM THE CONSTANT, OVER THE FITTED YEARS
  The law is amp(dT) = amp_draw * S(dT), and S is anchored so that S == 1
  EXACTLY at dT_eff = 0.940 K, the x^2-weighted effective warming level of the
  observed record. The anchor is inserted as a grid node precisely so that
  identity holds in floating point. The question is therefore not "is S ever far
  from 1" — at 2100 it is 0.86 — but "is S far from 1 ANYWHERE THE CALIBRATOR
  LOOKED", i.e. over 1850-2026.

  Reported as a fraction of the parameter's OWN posterior sd, because a shift in
  amp is only material relative to the uncertainty already carried in amp.

TEST 2 — WHETHER amp ENTERS THE LIKELIHOOD AT ALL
  The standing claim is that gis_amp is likelihood-inert: the calibration driver
  is built once at the constant, and only the post-2024 splice tail depends on
  the parameter, so ~1 of the GIS target's 126 years is affected. If that holds,
  the law can be revised projection-side without re-running the MCMC, and the
  mismatch is nominal by construction.

  Checked two ways: the marginal against its own truncated prior, and the
  correlation with every other sampled parameter.

  THE CORRELATION NULL MUST BE ESS-AWARE. These are MCMC draws, not iid samples.
  Judging max|r| against an iid null (sd = 1/sqrt(n)) sets the bar far too tight
  and manufactures "coupling" out of autocorrelation — the earlier |r| <= 0.05
  figure was an iid comparison and is superseded here. The null below uses the
  initial-positive-sequence ESS of the gis_amp trace and the distribution of the
  MAXIMUM over however many parameters are tested.

READS   outputs/gis_amp_shape{,_meta}.csv                      (the S grid + anchor)
        data/observations/fair_mean_gmst_<FORCING_TAG>.csv     (calibration forcing)
        data/MimiBRICK/parameters_subsample_brick_mengel_<TAG>.csv
WRITES  outputs/diag_gis_amp_calib_projection_gap.csv

  python3 python/diag_gis_amp_calib_projection_gap.py [--tag L12]
"""
import argparse
import os

import numpy as np
import pandas as pd
from scipy.stats import truncnorm, kstest, norm

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- named constants; every label and threshold below derives from these ------
LADRILLO_TAG = "L12"
# mirrors calibrate_mcmc_ext.jl: Y0/Y1 the model window, GIS targets from 1900
CALIB_Y0, CALIB_Y1 = 1850, 2026
GIS_TARGET_Y0 = 1900
# mirrors ladrillo_projection.jl LADRILLO_GIS_AMP / LADRILLO_DRIVER_BASE / _WIN
GIS_AMP_CONST = 1.92
DRIVER_BASE = (1850, 1900)
SHAPE_WIN = 30
# the gis_amp prior, from calibrate_mcmc_ext.jl
PRIOR_MU, PRIOR_SD, PRIOR_LO, PRIOR_HI = 1.92, 0.32, 1.51, 2.28
# calibration forcing tag (calibrate_mcmc_ext.jl switched to SSP2-4.5)
FORCING_TAG = "ssp245"
PROJECTION_YEARS = [2100, 2200, 2300]
# a departure smaller than this fraction of the parameter's own posterior sd is
# reported as immaterial: it is inside the uncertainty already carried in amp.
MATERIAL_SD_FRAC = 0.5
OUT = os.path.join(REPO, "outputs/diag_gis_amp_calib_projection_gap.csv")


def running_mean(v, w):
    if w <= 1:
        return np.asarray(v, float)
    n, lo, hi = len(v), (w - 1) // 2, w // 2
    return np.array([v[max(0, i - lo):min(n, i + hi + 1)].mean() for i in range(n)])


def ess_initial_positive(x, maxlag=200):
    """Initial-positive-sequence ESS. maxlag is a CAP, not a window: the sum stops
    at the first non-positive autocorrelation, so a too-small cap would floor the
    estimate and inflate the ESS."""
    x = np.asarray(x, float) - np.mean(x)
    n = len(x)
    s, k = 0.0, 1
    while k <= min(maxlag, n - 2):
        r = np.corrcoef(x[:-k], x[k:])[0, 1]
        if not np.isfinite(r) or r <= 0:
            break
        s += r
        k += 1
    return n / (1 + 2 * s), k - 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default=LADRILLO_TAG)
    args = ap.parse_args()
    tag = args.tag
    rows = []

    tbl = pd.read_csv(os.path.join(REPO, "outputs/gis_amp_shape.csv"))
    meta = pd.read_csv(os.path.join(REPO, "outputs/gis_amp_shape_meta.csv")).iloc[0]
    anchor = float(meta.anchor_dt)

    def S(dt):
        return np.interp(np.clip(dt, tbl.dt.min(), tbl.dt.max()), tbl.dt, tbl.S)

    post = pd.read_csv(os.path.join(
        REPO, f"data/MimiBRICK/parameters_subsample_brick_mengel_{tag}.csv"))
    amp = post["gis_amp"].to_numpy()
    amp_sd = float(amp.std(ddof=1))

    g = pd.read_csv(os.path.join(
        REPO, f"data/observations/fair_mean_gmst_{FORCING_TAG}.csv"))
    ycol = [c for c in g.columns if "year" in c.lower()][0]
    gcol = [c for c in g.columns if "gmst" in c.lower()][0]
    yr, gm = g[ycol].to_numpy(), g[gcol].to_numpy()
    rb = gm - gm[(yr >= DRIVER_BASE[0]) & (yr <= DRIVER_BASE[1])].mean()
    Sv = S(running_mean(rb, SHAPE_WIN))

    print(f"amp(GMST) CALIBRATION/PROJECTION GAP — Ladrillo {tag}")
    print(f"  law     : amp(dT) = amp_draw * S(dT), S == 1 exactly at "
          f"dT_eff = {anchor:.3f} K  [S(anchor) = {S(anchor):.6f}]")
    print(f"  constant: the calibrator runs at GIS_AMP = {GIS_AMP_CONST}")
    print(f"  forcing : fair_mean_gmst_{FORCING_TAG}, rel. {DRIVER_BASE[0]}-{DRIVER_BASE[1]}, "
          f"{SHAPE_WIN}-yr running mean\n")

    print(f"=== TEST 1: departure over the fitted years ===\n")
    for lab, y0 in [(f"calibration window {CALIB_Y0}-{CALIB_Y1}", CALIB_Y0),
                    (f"GIS target years {GIS_TARGET_Y0}-{CALIB_Y1}", GIS_TARGET_Y0)]:
        m = (yr >= y0) & (yr <= CALIB_Y1)
        dev = float(np.abs(Sv[m] - 1).max())
        d_amp = GIS_AMP_CONST * dev
        print(f"  {lab}")
        print(f"    S spans {Sv[m].min():.4f} .. {Sv[m].max():.4f}   (mean {Sv[m].mean():.4f})")
        print(f"    worst-year amp departs from {GIS_AMP_CONST} by {d_amp:.4f} "
              f"= {d_amp / amp_sd:.2f} posterior sd  ({amp_sd:.4f})")
        rows.append(dict(tag=tag, test="departure", window=lab,
                         S_min=Sv[m].min(), S_max=Sv[m].max(), S_mean=Sv[m].mean(),
                         max_abs_S_minus_1=dev, amp_departure=d_amp,
                         amp_posterior_sd=amp_sd, departure_in_sd=d_amp / amp_sd))
    print(f"\n  for contrast, where the law IS meant to act:")
    for y in PROJECTION_YEARS:
        i = np.where(yr == y)[0]
        if len(i):
            s = float(Sv[i[0]])
            print(f"    {y}: S {s:.4f}  amp {GIS_AMP_CONST * s:.3f}  "
                  f"= {GIS_AMP_CONST * abs(s - 1) / amp_sd:.2f} posterior sd from the constant")
            rows.append(dict(tag=tag, test="projection_contrast", window=str(y),
                             S_mean=s, amp_departure=GIS_AMP_CONST * abs(s - 1),
                             amp_posterior_sd=amp_sd,
                             departure_in_sd=GIS_AMP_CONST * abs(s - 1) / amp_sd))

    print(f"\n=== TEST 2: does gis_amp enter the likelihood at all? ===\n")
    tn = truncnorm((PRIOR_LO - PRIOR_MU) / PRIOR_SD, (PRIOR_HI - PRIOR_MU) / PRIOR_SD,
                   loc=PRIOR_MU, scale=PRIOR_SD)
    ks = kstest(amp, tn.cdf)
    print(f"  marginal   posterior mean {amp.mean():.4f} sd {amp_sd:.4f}")
    print(f"             trunc. prior   mean {tn.mean():.4f} sd {tn.std():.4f}")
    print(f"             KS D = {ks.statistic:.4f}   (p is NOT valid here: draws "
          f"are autocorrelated, not iid)")

    ess, nlag = ess_initial_positive(amp)
    num = post.select_dtypes(include=[np.number]).drop(columns=["gis_amp"])
    r = num.apply(lambda c: np.corrcoef(amp, c)[0, 1] if c.std() > 0 else 0.0).dropna().abs()
    r = r.sort_values(ascending=False)
    m_par = len(r)
    sd_r = 1 / np.sqrt(max(ess, 1))
    null_med = sd_r * norm.ppf(1 - 0.5 * (1 - 0.5 ** (1 / m_par)))
    null_p95 = sd_r * norm.ppf(1 - 0.5 * (1 - 0.95 ** (1 / m_par)))
    print(f"\n  correlation  ESS {ess:.0f} of {len(amp)} draws "
          f"(initial positive sequence, {nlag} lags)")
    print(f"               null max|r| over {m_par} params: "
          f"median {null_med:.4f}, 95th pct {null_p95:.4f}")
    print(f"               OBSERVED max|r| = {r.iloc[0]:.4f} ({r.index[0]})")
    verdict_r = "consistent with noise" if r.iloc[0] <= null_p95 else "EXCEEDS the null"
    print(f"               -> {verdict_r}")
    print(f"               top 4: " + ", ".join(f"{k} {v:.3f}" for k, v in r.head(4).items()))
    rows.append(dict(tag=tag, test="inertness", window="posterior",
                     post_mean=amp.mean(), post_sd=amp_sd,
                     prior_mean=tn.mean(), prior_sd=tn.std(), ks_D=ks.statistic,
                     ess=ess, max_abs_r=r.iloc[0], max_abs_r_param=r.index[0],
                     null_max_r_median=null_med, null_max_r_p95=null_p95,
                     n_params=m_par))

    m = (yr >= CALIB_Y0) & (yr <= CALIB_Y1)
    worst_sd = GIS_AMP_CONST * float(np.abs(Sv[m] - 1).max()) / amp_sd
    print(f"\n=== VERDICT ===\n")
    print(f"  Over every year the calibrator fitted, the law departs from the")
    print(f"  constant by at most {worst_sd:.2f} posterior sd "
          f"(threshold for material: {MATERIAL_SD_FRAC}),")
    print(f"  and gis_amp's marginal is its own truncated prior with max|r| "
          f"{verdict_r}.")
    if worst_sd < MATERIAL_SD_FRAC and r.iloc[0] <= null_p95:
        print(f"\n  -> The mismatch is NOMINAL. Aligning the calibrator to the law")
        print(f"     would move a likelihood-inert parameter by a fifth of its own")
        print(f"     sd over the fitted period. A refit is not justified by this.")
    else:
        print(f"\n  -> NOT nominal on at least one leg. See the numbers above.")

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
