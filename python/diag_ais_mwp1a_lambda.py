#!/usr/bin/env python3
"""
diag_ais_mwp1a_lambda.py -- MELTWATER PULSE 1A AS AN OBSERVATIONAL RATE CONSTRAINT
                            ON THE DAIS FAST-DYNAMICS PARAMETER

WHY THIS EXISTS. `dais_paleo_is_four_levels` established that the calibration behind
`antarctic_lambda` (Ruckert et al. 2017) uses FOUR LEVEL constraints -- LIG, LGM,
mid-Holocene, instrumental -- with NO rate constraint anywhere in the set, and that
MWP-1A falls between the LGM and MH anchors and is simply not sampled. lambda is a
RATE parameter. MWP-1A is the one observational constraint on rapid Antarctic
disintegration that exists, and it is the right SHAPE for the parameter.

This is deliberately NOT an expert elicitation and NOT a fit to another model
ensemble (which `between_scenario_not_model` rules out as a between-model criterion
in disguise). It is sea-level data, reduced by two independent published analyses
that DISAGREE -- and that disagreement is carried through rather than averaged away.

THE CONVERSION AND ITS THREE BIASES, ALL STATED, NONE CORRECTED.
  SLE rate = lambda * 24.78e15 / V0  (antarctic_icesheet_component.jl:181 + :196),
  ~= 0.92 * lambda m/yr at the present-day V0.
  (1) UPPER BOUND, because MWP-1A's Antarctic share includes the SMOOTH channel
      (surface mass balance + ice flux) as well as fast dynamics; attributing all of
      it to lambda over-attributes.
  (2) UPPER BOUND ALSO from the duration: the published durations (340 / 500 yr) are
      the event's, and the implied rate assumes the sheet was above `temperature_
      threshold` for ALL of it. Any sub-window shortens the duration and RAISES the
      implied lambda -- so this bias runs the other way. NET SIGN NOT ESTABLISHED.
  (3) SCALE: V0 was LARGER at 14.6 ka (glacial AIS), so 24.78e15/V0 was smaller and a
      given SLE rate implies a LARGER lambda than today's 0.92 factor gives.
  => treat the implied lambda as ORDER-OF-MAGNITUDE placement, not a calibration.
  The AIS-2300 propagation itself is NOT approximate: it reads the measured ladder
  from `scope_ais_three_tests.jl`, i.e. real model runs, not the linear law.

  python3 python/diag_ais_mwp1a_lambda.py [--tag=L14]
WRITES outputs/diag_ais_mwp1a_lambda_<tag>.csv
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = next((a[6:] for a in sys.argv[1:] if a.startswith("--tag=")), "L14")
LADDER_CSV = os.path.join(REPO, "outputs", f"scope_ais_three_tests_ladder_{TAG}.csv")
PALEO_CSV = os.path.join(REPO, "data/dais_paleo/daisfastdyn_lambda_tcrit.csv")
PRIORS_CSV = os.path.join(REPO, "outputs/param_priors.csv")
OUT_CSV = os.path.join(REPO, "outputs", f"diag_ais_mwp1a_lambda_{TAG}.csv")

# SLE metres per unit lambda per year, at present-day V0. See bias (3) above.
SLE_PER_LAMBDA = 0.92
SSP, HORIZON = "ssp585", 2300

# ---------------------------------------------------------------------------
# The published MWP-1A Antarctic estimates. Two independent analyses that
# DISAGREE; both are carried. Durations are each paper's own.
# ---------------------------------------------------------------------------
MWP1A = [
    # label, AIS metres SLE (lo, mid, hi), duration yr, citation
    ("Lin+2021 fingerprinting", 0.0, 1.3, 5.9, 500,
     "Lin et al. 2021, Nat Commun 12:2015, doi:10.1038/s41467-021-21990-y "
     "(95% range; 0-35% of total, 'strong preference for <15%')"),
    ("Liu+2016 low branch", 0.0, 3.45, 6.9, 340,
     "Liu et al. 2016, Nature Geosci 9:130, doi:10.1038/ngeo2616 "
     "(95% allowable, NAIS estimate A; mid = range midpoint, NOT a published median)"),
    ("Liu+2016 high branch", 4.1, 7.05, 10.0, 340,
     "Liu et al. 2016, ibid (95% allowable, NAIS estimate B; mid = range midpoint)"),
]


def ladder_interp(ladder, ssp, horizon, col="median_cm"):
    """Linear interpolation of the MEASURED lambda ladder. Not the fitted law --
    the ladder is 15 real model runs and interpolating it keeps whatever curvature
    it has, rather than assuming the linear fit that Test 3 reports."""
    s = ladder[(ladder.scenario == ssp) & (ladder.horizon == horizon)].sort_values("lambda")
    x, y = s["lambda"].to_numpy(), s[col].to_numpy()
    return lambda lam: float(np.interp(lam, x, y)), (x.min(), x.max())


def main():
    if not os.path.exists(LADDER_CSV):
        sys.exit(f"missing {LADDER_CSV} -- run julia/scope_ais_three_tests.jl first")
    ladder = pd.read_csv(LADDER_CSV)
    f_med, (lo_x, hi_x) = ladder_interp(ladder, SSP, HORIZON)
    f_p95, _ = ladder_interp(ladder, SSP, HORIZON, "p95_cm")

    paleo = pd.read_csv(PALEO_CSV)["lambda"].to_numpy()
    pri = pd.read_csv(PRIORS_CSV).set_index("param")
    box_hi = float(pri.loc["antarctic_lambda", "hi"])
    pri_mean = float(pri.loc["antarctic_lambda", "mean"])

    print("=" * 96)
    print("TEST 3 -- MWP-1A AS AN OBSERVATIONAL RATE CONSTRAINT ON lambda")
    print("=" * 96)
    print(f"  paleo ensemble support [{paleo.min():.6f}, {paleo.max():.6f}]  "
          f"prior box top {box_hi:.6f}  prior mean {pri_mean:.6f}")
    print(f"  SLE conversion {SLE_PER_LAMBDA} m/yr per unit lambda "
          f"(present-day V0; see header for the three biases)")
    print(f"  AIS@{HORIZON} read from the MEASURED {SSP} ladder, "
          f"lambda in [{lo_x:.6f}, {hi_x:.6f}]\n")

    rows = []
    hdr = (f"{'estimate':26s} {'AIS m SLE':>18s} {'yr':>4s} {'cm/yr':>13s} "
           f"{'implied lambda':>22s} {'pctile in paleo':>16s} {'AIS2300 med cm':>16s}")
    print(hdr)
    print("-" * len(hdr))
    for label, m_lo, m_mid, m_hi, dur, cite in MWP1A:
        lams, cms, pcts, rates = [], [], [], []
        for m in (m_lo, m_mid, m_hi):
            rate_cm_yr = 100.0 * m / dur
            lam = (rate_cm_yr / 100.0) / SLE_PER_LAMBDA
            lams.append(lam)
            rates.append(rate_cm_yr)
            pcts.append(100.0 * (paleo < lam).mean())
            cms.append(f_med(min(max(lam, lo_x), hi_x)))
        flag = "" if lams[2] <= paleo.max() else f"  <- hi is {lams[2]/paleo.max():.2f}x paleo max"
        print(f"{label:26s} {m_lo:5.1f}-{m_mid:4.1f}-{m_hi:5.1f} {dur:4d} "
              f"{rates[0]:4.2f}-{rates[2]:5.2f} "
              f"{lams[0]:.5f}-{lams[2]:.5f} {pcts[0]:6.1f}-{pcts[2]:5.1f} "
              f"{cms[0]:6.1f}-{cms[2]:6.1f}{flag}")
        for m, lam, pct, cm, r in zip((m_lo, m_mid, m_hi), lams, pcts, cms, rates):
            rows.append(dict(estimate=label, ais_m_sle=m, duration_yr=dur,
                             rate_cm_yr=r, implied_lambda=lam,
                             paleo_pctile=pct, ais2300_ssp585_median_cm=cm,
                             above_paleo_max=lam > paleo.max(),
                             above_prior_box=lam > box_hi, citation=cite))

    print()
    print("WHAT THE SHIPPED PRIOR IMPLIES, ON THE SAME AXIS")
    print(f"{'':26s} {'lambda':>10s} {'cm/yr':>8s} "
          f"{'m in 340 yr':>12s} {'m in 500 yr':>12s}")
    for nm, lam in [("posterior median", 0.010567), ("prior box top", box_hi),
                    ("paleo max", float(paleo.max()))]:
        r = 100 * SLE_PER_LAMBDA * lam
        print(f"  {nm:24s} {lam:10.5f} {r:8.3f} "
              f"{SLE_PER_LAMBDA*lam*340:12.2f} {SLE_PER_LAMBDA*lam*500:12.2f}")

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)
    print(f"\nwrote {os.path.relpath(OUT_CSV, REPO)}")

    # --- the verdict, stated as a placement, not a calibration ---------------
    all_lam = df.implied_lambda
    print("\n" + "=" * 96)
    print("VERDICT")
    print("=" * 96)
    print(f"  MWP-1A-implied lambda spans {all_lam.min():.5f} - {all_lam.max():.5f}; "
          f"the paleo support is {paleo.min():.5f} - {paleo.max():.5f}.")
    inside = ((all_lam >= paleo.min()) & (all_lam <= paleo.max())).mean()
    print(f"  {100*inside:.0f}% of the published estimates fall INSIDE the paleo support "
          f"=> MWP-1A does NOT, on its own, demand a prior outside it.")
    print(f"  But the two analyses disagree by {MWP1A[2][3]/max(MWP1A[0][2],1e-9):.1f}x on the "
          f"upper bound ({MWP1A[0][3]:.1f} vs {MWP1A[2][3]:.1f} m), so it does not "
          f"NARROW the prior either.")


if __name__ == "__main__":
    main()
