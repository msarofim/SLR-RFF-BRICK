#!/usr/bin/env python3
"""diag_ais_rate_2002_per_draw.py -- the post-2002 Antarctic rate, PER DRAW, against both observational products
(GMD queued item 7: "disclose the 2002-2021 Antarctic rate deficit; compute per-draw rates for two windows first").

  python3 python/diag_ais_rate_2002_per_draw.py [--tag=L27]

Writes outputs/diag_ais_rate_2002_per_draw_<TAG>.csv. Reads committed hindcast residuals; runs no model.

WHY. On 2026-10-02 (Lin et al. 2026, whose emulator is calibrated to a 2002-2021 Antarctic rate) a median-PATH OLS
rate over 2002-2021 put Ladrillo at 0.29 mm/yr against its own target's 0.42. That number was never committed, and a
rate of the median path is not the median of the per-draw rates. Its follow-up showed the gap depends on the end year
(the target's 2002-x rate falls from 0.42 to 0.37 between 2021 and 2025), so each window here is reported, not one.

MODEL PATHS. outputs/ic_hindcast_residuals_{ladrillo_<TAG>,brick20}.csv hold residual = model - obs (cm, 1995-2005
reference) for every posterior row, on the calibration driver (FaIR mean, ssp245harm), 1900-2026. model = residual +
obs, with obs = outputs/ic_hindcast_obs_sigma.csv ais_obs (= recalib_targets_ext.csv ais).
[PATH-IDENTITY] the median of rows 1:5:N reconstructed this way must equal postpred_<TAG>_components_timeseries.csv
ais_p50 (the Fig. 1 median), to 1e-9 cm.

OBSERVATIONS. target = the series Ladrillo is fitted to (Frederikse 1900-2018 + GRACE offset-matched, from 2019).
IMBIE 2026 (Otosaka et al., 2026) = outputs/diag_imbie2026_vs_targets_L27.csv imbie_level_cm (annual, cm SLE, + = rise),
which ENDS IN 2023; a window past 2023 has no IMBIE rate. IMBIE is out of sample for L27.

RATES are OLS slopes over every year of the window, in mm/yr. Observation rates carry two standard errors: iid
(residual scatter about the line) and AR(1)-inflated (n_eff = n (1 - r1) / (1 + r1), r1 the lag-1 autocorrelation of the
residuals). Both treat the year-to-year scatter as the only error. The published level uncertainties are not used:
a near-constant level sigma mostly cancels in a slope, and how much survives depends on its unknown correlation.
"""
import os
import subprocess
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--tag=")), "L27")
OUTD = os.path.join(REPO, "outputs")
RESID = {"Ladrillo " + TAG: os.path.join(OUTD, f"ic_hindcast_residuals_ladrillo_{TAG}.csv"),
         "BRICK 2.0": os.path.join(OUTD, "ic_hindcast_residuals_brick20.csv")}
OBS = os.path.join(OUTD, "ic_hindcast_obs_sigma.csv")
POSTPRED = os.path.join(OUTD, f"postpred_{TAG}_components_timeseries.csv")
IMBIE = os.path.join(OUTD, f"diag_imbie2026_vs_targets_{TAG}.csv")
OUT = os.path.join(OUTD, f"diag_ais_rate_2002_per_draw_{TAG}.csv")
Y0 = 2002
END_YEARS = [2021, 2023, 2025]        # 2021: Lin et al.'s calibration window; 2023: IMBIE's last year; 2025: the target's
QUANTILES = [0.05, 0.17, 0.5, 0.83, 0.95]
PATH_TOL_CM = 1e-9
CM_YR_TO_MM_YR = 10.0


def ols(x, y):
    """slope, iid se, AR(1)-inflated se, lag-1 r of the residuals."""
    x = np.asarray(x, float) - x[0]
    A = np.vstack([np.ones_like(x), x]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    res = y - A @ coef
    n = len(y)
    se = np.sqrt(res @ res / (n - 2) / ((x - x.mean()) @ (x - x.mean())))
    r1 = float(np.corrcoef(res[:-1], res[1:])[0, 1])
    n_eff = n * (1 - r1) / (1 + r1) if r1 > 0 else n
    return float(coef[1]), float(se), float(se * np.sqrt((n - 2) / max(n_eff - 2, 1.0))), r1


def slopes(Y, yrs):
    """OLS slope of every row of Y (draws x years) against yrs."""
    x = np.asarray(yrs, float) - yrs[0]
    xc = x - x.mean()
    return (Y - Y.mean(axis=1, keepdims=True)) @ xc / (xc @ xc)


obs = pd.read_csv(OBS).set_index("year").ais_obs
imb = pd.read_csv(IMBIE)
imb = imb[imb.component == "AIS"].set_index("year").imbie_level_cm
pp = pd.read_csv(POSTPRED).set_index("year").ais_p50
commit = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()

rows = []
print("=" * 100)
print(f"ANTARCTIC RATE FROM {Y0}, PER DRAW -- {TAG} and BRICK 2.0 hindcasts, mm/yr (OLS)")
print("=" * 100)
for y1 in END_YEARS:
    yrs = list(range(Y0, y1 + 1))
    for src, s in (("target (Frederikse + GRACE)", obs), ("IMBIE 2026", imb)):
        if not all(y in s.index and np.isfinite(s.loc[y]) for y in yrs):
            print(f"  {Y0}-{y1}  {src:28s}  no rate (record ends {int(s.dropna().index.max())})")
            continue
        b, se, se_ar1, r1 = ols(np.array(yrs), s.loc[yrs].values.astype(float))
        rows.append(dict(window=f"{Y0}-{y1}", series=src, kind="observation", n_draws=np.nan,
                         rate_mm_yr=b * CM_YR_TO_MM_YR, se_iid_mm_yr=se * CM_YR_TO_MM_YR,
                         se_ar1_mm_yr=se_ar1 * CM_YR_TO_MM_YR, resid_lag1_r=r1))
        print(f"  {Y0}-{y1}  {src:28s}  {b * 10:.3f} (se iid {se * 10:.3f}, AR(1) {se_ar1 * 10:.3f}; r1 {r1:+.2f})")

for model, path in RESID.items():
    cols = [f"ais_{y}" for y in range(Y0, max(END_YEARS) + 1)]
    R = pd.read_csv(path, usecols=["draw"] + cols)
    M = R[cols].to_numpy(float) + obs.loc[list(range(Y0, max(END_YEARS) + 1))].to_numpy(float)
    if model.startswith("Ladrillo"):
        ## [PATH-IDENTITY] postpred's p50 is the median of rows 1:5:N; reconstruct it from residual + obs.
        sub = np.median(M[::5], axis=0)
        ref = pp.loc[list(range(Y0, max(END_YEARS) + 1))].to_numpy(float)
        w = float(np.max(np.abs(sub - ref)))
        print(f"\n  [PATH-IDENTITY] median(rows 1:5:N of residual + obs) vs postpred ais_p50: max |d| {w:.2e} cm "
              f"-> {'PASS' if w <= PATH_TOL_CM else 'FAIL'}")
        if w > PATH_TOL_CM:
            raise SystemExit("[PATH-IDENTITY] FAIL: the residual file does not reconstruct the Fig. 1 median")
    for y1 in END_YEARS:
        k = y1 - Y0 + 1
        r = slopes(M[:, :k], list(range(Y0, y1 + 1))) * CM_YR_TO_MM_YR
        q = np.quantile(r, QUANTILES)
        tgt = [x for x in rows if x["window"] == f"{Y0}-{y1}" and x["series"].startswith("target")][0]["rate_mm_yr"]
        row = dict(window=f"{Y0}-{y1}", series=model, kind="model per-draw", n_draws=len(r),
                   **{f"rate_p{int(round(100 * p)):02d}_mm_yr": v for p, v in zip(QUANTILES, q)},
                   rate_mean_mm_yr=float(r.mean()),
                   share_draws_below_target=float((r < tgt).mean()),
                   median_path_rate_mm_yr=float(slopes(np.median(M[:, :k], axis=0)[None, :], list(range(Y0, y1 + 1)))[0]
                                                * CM_YR_TO_MM_YR))
        imb_rows = [x for x in rows if x["window"] == f"{Y0}-{y1}" and x["series"] == "IMBIE 2026"]
        if imb_rows:
            row["share_draws_below_imbie"] = float((r < imb_rows[0]["rate_mm_yr"]).mean())
        rows.append(row)
        print(f"  {Y0}-{y1}  {model:12s} p05 {q[0]:.3f}  p50 {q[2]:.3f}  p95 {q[4]:.3f}  "
              f"(median path {row['median_path_rate_mm_yr']:.3f}; {100 * row['share_draws_below_target']:.1f}% of "
              f"{len(r)} draws below the target"
              + (f", {100 * row['share_draws_below_imbie']:.1f}% below IMBIE)" if imb_rows else ")"))

out = pd.DataFrame(rows)
out["provenance"] = (f"diag_ais_rate_2002_per_draw.py @ {commit} | AIS, cm SLE -> mm/yr, OLS over every year of the window "
                     f"| models: residual + obs from ic_hindcast_residuals_ladrillo_{TAG}.csv (Ladrillo {TAG}, all posterior "
                     f"rows) and ic_hindcast_residuals_brick20.csv (BRICK 2.0, Zenodo 20592337 joint posterior, all rows); "
                     f"calibration driver FaIR 2.2.4 (calib 1.6.0) mean ssp245harm | target = ic_hindcast_obs_sigma.csv ais_obs "
                     f"(Frederikse 1900-2018 + GRACE from 2019) | IMBIE 2026 = diag_imbie2026_vs_targets_{TAG}.csv "
                     f"imbie_level_cm, ends 2023 | obs se: iid and AR(1) n_eff from the residual scatter only")
out.to_csv(OUT, index=False)
print(f"\nwrote {os.path.relpath(OUT, REPO)}")
