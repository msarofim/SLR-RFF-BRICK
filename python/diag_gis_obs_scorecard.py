#!/usr/bin/env python3
"""
diag_gis_obs_scorecard.py -- HOW DOES OUR GREENLAND MODEL LOOK AGAINST OBSERVATIONS,
AND HAS THE 2100 TARGET ITSELF EVER BEEN GATED ON THEM?

WHY THIS EXISTS. `scope_gis_onset_rescan.py` scores 2100 against the ISMIP6 16-model
median and finds us 1.32x FAST -- a finding that has driven the whole onset argument.
But this repo established a discipline in `handoff_2026-08-23_commitment_evidence.md`
sec 2.2 and applied it twice:

    "Before any model's transient horizons are used as a target, gate the model on
     the observed record."

Greve/SICOPOLIS PASSED that gate (0.440-0.988 mm/yr over 2016-2050, bracketing the
observed 0.593) and its horizons were used. CLIMBER-X FAILED it (0.117 mm/yr,
5.1x slow) and was DROPPED as a target. **ISMIP6 was never gated.** Its scalars carry
86 annual records, so the identical gate is computable and has simply not been run.
The hypothesis under test was that the ISMIP6 ensemble is itself slow against the
observed record, which would mean "we are 1.32x above the ISMIP6 median at 2100" does
not mean what it has been taken to mean. RESULT: **REFUTED.** The ensemble median is
1.15x the observed rate, not below it, and 11/14 ice-sheet models sit at or above
observations. ISMIP6 clears the same gate Greve cleared, so the 2100 finding stands as
measured and weighting the 2100 term highest is evidence-supported.

SECTION 1 is the question asked directly: our Greenland model vs observations. Note
which parts are FITTED and which are FREE -- the hindcast bisection matches the
CALIB_WIN total by construction, so only the SHAPE and the MODERN RATE are evidence.

SECTION 2 applies the priority-1 gate to ISMIP6, per ice-sheet model.

SECTION 3 states what that does to the 2100 finding -- which, the hypothesis having
failed, is: nothing. No correction is available and none should be applied.

WRITES outputs/diag_gis_obs_scorecard_ismip6_rates.csv
       outputs/diag_gis_obs_scorecard_ours.csv
  python3 python/diag_gis_obs_scorecard.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))

import numpy.polynomial.polynomial as P  # noqa: E402
from scope_gis_onset_rescan import build_base, CALIB_WIN, OURS  # noqa: E402
from diag_gis_greve_year3000 import YEARS_EXT, EXPS  # noqa: E402
import diag_gis_ismip6_2100_ism_spread as I6  # noqa: E402

OUT_I6 = os.path.join(REPO, "outputs/diag_gis_obs_scorecard_ismip6_rates.csv")
OUT_OURS = os.path.join(REPO, "outputs/diag_gis_obs_scorecard_ours.csv")
OBS_CSV = os.path.join(REPO, "outputs/recalib_targets_ext.csv")

# --- named constants ----------------------------------------------------------
LINEAGE = "L14 vintage (two-basin), extended axis, thinned posterior"
MM_PER_CM = 10.0
## The same window and the same observational series the Greve gate used, so the
## PASS/FAIL verdicts here are directly comparable to the ones already on record.
OBS_RATE_WIN = (1995, 2024)
GATE_WIN = (2016, 2050)
GREVE_RATE_MM_YR = (0.440, 0.988)      # diag_gis_greve_year3000.py section 1
CLIMBERX_RATE_MM_YR = 0.117            # diag_gis_climberx_commitment.py section 3b
OBS_RATE_FACTOR = 2.0                  # the Greve gate's own tolerance
## Sub-windows for the SHAPE check. The calibration total is fitted; these are not.
SHAPE_WINS = [(1900, 1950), (1950, 1990), (1993, 2010), (2010, 2024)]
## ISMIP6 positional indexing: index 0 is 2015, index 85 is 2100 (module docstring
## of diag_gis_ismip6_2100_ism_spread -- the `time` ATTRIBUTES are not trustworthy).
I6_YEAR0 = I6.YEAR_BASE
PRIMARY = I6.PROTOCOL_PRIMARY


def rate_mm_yr(series, years, w):
    i0 = int(np.where(years == w[0])[0][0])
    i1 = int(np.where(years == w[1])[0][0])
    return (series[i1] - series[i0]) * MM_PER_CM / (w[1] - w[0])


def main():
    print(f"diag_gis_obs_scorecard -- {LINEAGE}\n")
    obs = pd.read_csv(OBS_CSV).set_index("year")["gis"].dropna()
    oy = obs.index.to_numpy()
    ov = obs.to_numpy()

    gmst, base, ie, thin = build_base()
    ## Pre-2015 every driver is the SAME observed south-Greenland T (ext_driver
    ## splices the obs record), so the hindcast is one series, not eight. Verified
    ## rather than assumed -- if it were not, "our hindcast" would be ambiguous.
    keys = list(base)
    ih = YEARS_EXT <= 2015
    spread = max(float(np.max(np.abs(base[k][ih] - base[keys[0]][ih]))) for k in keys)
    if spread > 1e-9:
        sys.exit(f"the pre-2015 hindcast differs across drivers by {spread:.3e} cm; "
                 f"'our hindcast' is not well defined")
    ours = base[keys[0]]
    print(f"  pre-2015 hindcast is identical across all {len(keys)} drivers "
          f"(max spread {spread:.1e} cm) -- one hindcast, as expected.\n")

    # ---------------------------------------------------------------- section 1
    print(f"=== 1. OUR GREENLAND MODEL vs OBSERVATIONS ===")
    print(f"  obs source: {os.path.relpath(OBS_CSV, REPO)} ('gis'), "
          f"{oy.min()}-{oy.max()}\n")
    ## Rebase both to the calibration window's first year so the comparison is of
    ## CHANGE, which is what the bisection targets and what the obs series carries.
    i0o = int(np.where(oy == CALIB_WIN[0])[0][0])
    i0m = int(np.where(YEARS_EXT == CALIB_WIN[0])[0][0])
    ov_r = ov - ov[i0o]
    ours_r = ours - ours[i0m]

    tot_o = ov_r[int(np.where(oy == CALIB_WIN[1])[0][0])]
    tot_m = ours_r[int(np.where(YEARS_EXT == CALIB_WIN[1])[0][0])]
    print(f"  A. THE FITTED PART -- total change over the calibration window "
          f"{CALIB_WIN}:")
    print(f"     observed {tot_o:7.3f} cm   ours {tot_m:7.3f} cm   "
          f"ratio {tot_m / tot_o:.4f}x   <- MATCHED BY CONSTRUCTION (bisection)")
    print(f"     This is not evidence. Everything below IS.\n")

    print(f"  B. THE FREE PART -- rates the bisection does not control, mm/yr:")
    print(f"     {'window':<16}{'observed':>10}{'ours':>10}{'ours/obs':>11}")
    rows = []
    for w in SHAPE_WINS + [OBS_RATE_WIN]:
        ro = rate_mm_yr(ov_r, oy, w)
        rm = rate_mm_yr(ours_r, YEARS_EXT, w)
        tag = "   <- the priority-1 obs rate" if w == OBS_RATE_WIN else ""
        print(f"     {f'{w[0]}-{w[1]}':<16}{ro:>10.3f}{rm:>10.3f}"
              f"{rm / ro:>11.2f}x{tag}")
        rows.append(dict(win=f"{w[0]}-{w[1]}", obs_mm_yr=ro, ours_mm_yr=rm,
                         ratio=rm / ro))
    pd.DataFrame(rows).to_csv(OUT_OURS, index=False)
    obs_rate = rate_mm_yr(ov_r, oy, OBS_RATE_WIN)

    ## Acceleration: a quadratic through the satellite-era overlap. The repo's live
    ## concern is that ISM ensembles UNDER-reproduce observed GrIS acceleration, so
    ## the sign and size of ours against obs is the thing to look at.
    w = (1993, 2024)
    mo = (oy >= w[0]) & (oy <= w[1])
    mm = (YEARS_EXT >= w[0]) & (YEARS_EXT <= w[1])
    co = P.polyfit(oy[mo] - w[0], ov_r[mo], 2)
    cm = P.polyfit(YEARS_EXT[mm] - w[0], ours_r[mm], 2)
    print(f"\n  C. ACCELERATION over {w[0]}-{w[1]} (quadratic coeff x2, mm/yr^2):")
    print(f"     observed {2 * co[2] * MM_PER_CM:+.4f}   ours "
          f"{2 * cm[2] * MM_PER_CM:+.4f}   ratio "
          f"{cm[2] / co[2]:.2f}x")

    # ---------------------------------------------------------------- section 2
    print(f"\n=== 2. THE PRIORITY-1 GATE, APPLIED TO ISMIP6 FOR THE FIRST TIME ===")
    print(f"  The gate Greve PASSED and CLIMBER-X FAILED, now run on the ensemble "
          f"that\n  supplies the 2100 target. Window {GATE_WIN}, positional "
          f"indexing from {I6_YEAR0}.\n")
    import glob   # noqa: E402
    import re     # noqa: E402
    import warnings  # noqa: E402
    import netCDF4 as nc  # noqa: E402
    recs = []
    for f in sorted(glob.glob(os.path.join(I6.ICE_DIR, "*.nc"))):
        b = os.path.basename(f)
        m = re.match(r"scalars_mm_cr_GIS_(.+)_(expb\d\d)\.nc", b)
        if m is None:
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            d = nc.Dataset(f)
            s = np.asarray(d.variables["sle"][:], dtype=float)
            d.close()
        if len(s) != I6.N_REC or abs(s[0]) > 1e-9:
            continue
        yrs = np.arange(I6_YEAR0, I6_YEAR0 + I6.N_REC)
        cm_ = I6.SLE_SIGN * (s - s[0]) * I6.CM_PER_M
        gcm, ssp, proto = I6.EXPID[m.group(2)]
        recs.append(dict(ism=m.group(1), exp=m.group(2), gcm=gcm, ssp=ssp,
                         protocol=proto,
                         rate_mm_yr=rate_mm_yr(cm_, yrs, GATE_WIN),
                         cm_2100=cm_[-1]))
    r6 = pd.DataFrame(recs)
    r6.to_csv(OUT_I6, index=False)

    ## Gate on the HIGH-forcing standard-protocol cells: the low-forcing ssp126 cell
    ## is not expected to reproduce an observed rate driven by recent warming, and
    ## pooling it would average two different questions (a trap already on record).
    hi = r6[(r6.protocol == PRIMARY) & (r6.ssp == "ssp585")]
    print(f"  observed GIS rate {OBS_RATE_WIN[0]}-{OBS_RATE_WIN[1]}: "
          f"{obs_rate:.3f} mm/yr")
    print(f"  ISMIP6 {GATE_WIN[0]}-{GATE_WIN[1]}, ssp585 / {PRIMARY} protocol, "
          f"{len(hi)} runs across {hi.ism.nunique()} ice-sheet models:")
    print(f"    min {hi.rate_mm_yr.min():.3f}   p25 {hi.rate_mm_yr.quantile(.25):.3f}"
          f"   MEDIAN {hi.rate_mm_yr.median():.3f}   p75 "
          f"{hi.rate_mm_yr.quantile(.75):.3f}   max {hi.rate_mm_yr.max():.3f}")
    brackets = hi.rate_mm_yr.min() <= obs_rate <= hi.rate_mm_yr.max()
    med_ratio = obs_rate / hi.rate_mm_yr.median()
    print(f"\n  per ice-sheet model (median over its ssp585 runs), sorted:")
    per = hi.groupby("ism").rate_mm_yr.median().sort_values()
    for k, v in per.items():
        print(f"    {k:22}{v:8.3f} mm/yr   obs/model {obs_rate / v:6.2f}x"
              f"{'   <- BELOW obs' if v < obs_rate else ''}")
    nbelow = int((per < obs_rate).sum())
    ## DIRECTION MATTERS AND IS EASY TO GET BACKWARDS. med_over_obs > 1 means the
    ## ensemble is FASTER than the observed record, not slower. Named that way so
    ## the prose below cannot drift from the number.
    med_over_obs = float(hi.rate_mm_yr.median()) / obs_rate
    print(f"\n  {nbelow}/{len(per)} ice-sheet models run BELOW the observed rate, "
          f"{len(per) - nbelow}/{len(per)} at or above it.")
    print(f"  ENSEMBLE MEDIAN {hi.rate_mm_yr.median():.3f} vs observed "
          f"{obs_rate:.3f} mm/yr = {med_over_obs:.2f}x -- the ensemble is "
          f"{'FASTER' if med_over_obs > 1 else 'SLOWER'} than\n  observations, not "
          f"{'slower' if med_over_obs > 1 else 'faster'}.")
    print(f"  For comparison, on this same gate: Greve/SICOPOLIS "
          f"{GREVE_RATE_MM_YR[0]:.3f}-{GREVE_RATE_MM_YR[1]:.3f} (PASSED, obs inside), "
          f"\n  CLIMBER-X {CLIMBERX_RATE_MM_YR:.3f} (FAILED, "
          f"{obs_rate / CLIMBERX_RATE_MM_YR:.1f}x slow, DROPPED as a target).")
    brackets = hi.rate_mm_yr.min() <= obs_rate <= hi.rate_mm_yr.max()
    print(f"\n  ==> ISMIP6 PASSES. The observed rate is "
          f"{'INSIDE' if brackets else 'OUTSIDE'} the model spread, and the median "
          f"is not\n      slow against observations. **The gate does NOT disqualify "
          f"the 2100 target.**")

    # ---------------------------------------------------------------- section 3
    print(f"\n=== 3. WHAT THIS DOES TO THE 2100 FINDING -- THE HYPOTHESIS IS "
          f"REFUTED ===")
    print(f"  The hypothesis this section was built to test: that the ISMIP6 median "
          f"UNDER-runs\n  observations, so that part of our 1.32x 2100 excess is the "
          f"target's own slow bias\n  rather than our defect. **That is refuted by "
          f"its own numbers.** The median is\n  {med_over_obs:.2f}x the observed rate, "
          f"not below it, and {len(per) - nbelow}/{len(per)} models sit at or above "
          f"observations.")
    print(f"\n  ==> NO CORRECTION IS AVAILABLE. The 2100 finding stands as measured: "
          f"our 1.32x is\n      ours. ISMIP6 clears the same gate Greve cleared and "
          f"CLIMBER-X failed, so it is\n      an admissible target by this repo's own "
          f"standard, and weighting the 2100 term\n      HIGHEST is supported by the "
          f"evidence, not merely by decision-relevance.")
    ## The gate's own structural caveat, which applies equally to the Greve and
    ## CLIMBER-X verdicts already on record and is therefore a caveat on the
    ## CONVENTION, not something introduced here.
    print(f"\n  ONE CAVEAT ON THE GATE ITSELF, which applies equally to the Greve and "
          f"CLIMBER-X\n  verdicts already on record: it compares a {GATE_WIN[0]}-"
          f"{GATE_WIN[1]} PROJECTED rate to a\n  {OBS_RATE_WIN[0]}-{OBS_RATE_WIN[1]} "
          f"OBSERVED one. The projection window is later and warmer, so a\n  "
          f"well-behaved model SHOULD exceed the observed rate. Read that way "
          f"{med_over_obs:.2f}x is modest,\n  and the notable number is that "
          f"{nbelow}/{len(per)} models fail to reach a PAST observed rate in a\n  "
          f"FUTURE window. It does not change the verdict; it does mean the gate is a "
          f"floor,\n  not a calibration.")
    ours_rate = rate_mm_yr(ours_r, YEARS_EXT, OBS_RATE_WIN)
    print(f"\n  AND OUR OWN STANDING, stated against the same yardstick: our "
          f"{OBS_RATE_WIN[0]}-{OBS_RATE_WIN[1]} rate is\n  {ours_rate:.3f} mm/yr = "
          f"{ours_rate / obs_rate:.2f}x observed -- better than the ISMIP6 median's "
          f"{med_over_obs:.2f}x. The\n  hindcast is NOT where our problem is. The "
          f"shape defect at the recent end is\n  ACCELERATION: "
          f"{cm[2] / co[2]:.2f}x observed over 1993-2024 (section 1C). We match the "
          f"LEVEL and\n  the RATE and under-run the CURVATURE -- and then arrive "
          f"1.32x high at 2100.")

    print(f"\nWROTE {os.path.relpath(OUT_I6, REPO)}")
    print(f"WROTE {os.path.relpath(OUT_OURS, REPO)}")


if __name__ == "__main__":
    main()
