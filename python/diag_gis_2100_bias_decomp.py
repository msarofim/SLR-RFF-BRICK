"""THE 2100 FAST BIAS: IS IT THE DRIVER OR IS IT THE RESPONSE?

WHAT IS BEING EXPLAINED. Our Greenland at 2100 is ~1.32x the ISMIP6 16-model median
across the GCM cells, and that finding now drives the whole onset argument. ISMIP6
itself PASSES the priority-1 observational gate (median 1.15x the observed rate, obs
inside the spread), so the bias is OURS -- diag_gis_obs_scorecard.py. What has never
been done is split it.

THE PARADOX THIS EXISTS TO RESOLVE. Against observations we match the LEVEL (fitted),
match the RATE over four free windows (0.95-1.07x), and UNDER-run the ACCELERATION
(0.63x). A model that under-runs curvature while matching the rate should arrive LOW
at 2100, not 1.32x HIGH. Something between 2015 and 2100 more than reverses it, and
the two candidates are separable:

  DRIVER   our regional Greenland temperature rises faster than the GCM's own, because
           `regional_driver` applies amp*S(GMST). diag_gis_gcm_tdecomp measured the amp
           law at 1.64-1.82 against these models' own SOUTH-zone 0.63-1.51 -- a
           NORTH-sized amplification on a SOUTH-zone driver, 1.33x over at the median.
  RESPONSE given the same driver, our ice loses mass faster than the ISMs do.

THE TEST. Run both routes to 2100 on the same GCM cells the ISMIP6 comparison uses:

  GMST route    our production path, regional_driver(GMST_own, amp draws, S)
  DIRECT route  the GCM's OWN Greenland anomaly spliced in place of amp*S*GMST
                (TD.driver_from_regional), bypassing the amp law entirely

If DIRECT lands on ISMIP6 and GMST over-shoots, the defect is the amp law and is
correctable without touching the ice response. If BOTH over-shoot, the response is too
strong and the amp law is a red herring. If DIRECT UNDER-shoots while GMST over-shoots,
the two errors are COMPENSATING -- calibration absorbed the amp error into c1 against
the OBSERVED south driver -- and neither can be fixed alone. That third outcome is the
one the 2300 decomposition already hints at, and it is a different repair.

⚠ EVERYTHING IS 2015->2100 CHANGE, matching the ISMIP6 protocol (sle[0] == 0 at 2015).
A level offset therefore cannot produce any of this.

READ-ONLY. Writes one CSV.
  python3 python/diag_gis_2100_bias_decomp.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
os.chdir(REPO)

import scope_gis_shape_all_scenarios as A  # noqa: E402
import diag_gis_gcm_tdecomp as TD  # noqa: E402
import diag_gis_ismip6_2100_ism_spread as I6  # noqa: E402
from scope_gis_ridge_vs_protect import basin2_series, rebase_cm  # noqa: E402
from scope_gis_leq_ridge_vs_literature import gis_tbar  # noqa: E402
from scope_gis_2300_relaxation import (  # noqa: E402
    DRIVER_BASE, YEARS, gis_shape_table, regional_driver,
)

OUT = os.path.join(REPO, "outputs/diag_gis_2100_bias_decomp.csv")
Y_BASE, Y_TEST = I6.YEAR_BASE, I6.YEAR_TEST      # 2015, 2100
K_FIXED = 1.0
PROTOCOL = I6.PROTOCOL_PRIMARY


def main():
    post = pd.read_csv(A.POST)
    tbar = gis_tbar()
    r_s = np.exp(post["gis_slow_ell"].to_numpy())
    post["gis_alpha_s"] = post["gis_slow_w"].to_numpy() * r_s / tbar
    post["gis_beta_s"] = (1.0 - post["gis_slow_w"].to_numpy()) * r_s
    amp = post["gis_amp"].to_numpy()
    S_tab = gis_shape_table()
    idx = {y: int(np.where(YEARS == y)[0][0])
           for y in (Y_BASE, Y_TEST) + tuple(A.HIND)}
    ibd = (YEARS >= DRIVER_BASE[0]) & (YEARS <= DRIVER_BASE[1])

    # --- the hindcast bisection, identical to every scan in this family ----------
    tgt = pd.read_csv(A.TARGETS).set_index("year")["gis"]
    want = float(tgt.loc[A.HIND[1]] - tgt.loc[A.HIND[0]])
    gh = pd.read_csv(f"outputs/{A.ARMS[0][3]}.csv").set_index(
        "year")[f"gmst_{A.ARM}"].reindex(YEARS).ffill().bfill().to_numpy()
    hind_drv = regional_driver(gh - gh[ibd].mean(), amp, S_tab)
    lo, hi = np.full(len(post), 1e-4), np.full(len(post), 1e3)
    for _ in range(80):
        mid = np.sqrt(lo * hi)
        L = basin2_series(hind_drv, post, K_FIXED, mid)
        b = 100.0 * (L[:, idx[A.HIND[1]]] - L[:, idx[A.HIND[0]]]) < want
        lo, hi = np.where(b, mid, lo), np.where(b, hi, mid)
    s = np.sqrt(lo * hi)

    def change_2015_2100(drv):
        """cm of Greenland loss between 2015 and 2100. Taken as a DIFFERENCE of the
        SAME series, so the 1995-2014 rebase and any level offset cancel exactly --
        which is why this needs no `offs` term and cannot inherit one's error."""
        c = np.median(rebase_cm(basin2_series(drv, post, K_FIXED, s)), axis=0)
        return float(c[idx[Y_TEST]] - c[idx[Y_BASE]])

    ism = I6.load_ism_scalars() if hasattr(I6, "load_ism_scalars") else None
    arms = pd.read_csv(os.path.join(REPO,
                       "outputs/diag_gis_ismip6_2100_ism_spread_arms.csv"))

    print(f"=== THE {Y_BASE}-{Y_TEST} FAST BIAS, SPLIT INTO DRIVER AND RESPONSE ===\n")
    print(f"  All columns are {Y_BASE}->{Y_TEST} CHANGE in cm, ISMIP6 protocol "
          f"({PROTOCOL}).\n")
    print(f"  {'GCM':16}{'ssp':9}{'ISMIP6 med':>11}{'GMST rt':>9}{'DIRECT':>8}"
          f"{'GMST/ISM':>10}{'DIR/ISM':>9}{'amp ours':>10}{'amp GCM':>9}")
    rows = []
    for r in arms.itertuples():
        ser = TD.gcm_series(r.gcm, r.ssp)
        if ser is None:
            print(f"  {r.gcm:16}{r.ssp:9}{r.ism_median:11.1f}"
                  f"{'  — not in data/cmip6_gis, DIRECT route unavailable':>46}")
            continue
        d_gmst = regional_driver(ser["gmst"], amp, S_tab)
        d_dir = TD.driver_from_regional(ser["reg"], len(post))
        v_gmst, v_dir = change_2015_2100(d_gmst), change_2015_2100(d_dir)
        ## THE EFFECTIVE AMPLIFICATION, DERIVED FROM THE DRIVER ITSELF, not the raw
        ## `gis_amp` posterior median. The production law is amp * S(warming level) and
        ## S <= 1, so the raw parameter (1.91) is NOT what gets applied and is not
        ## comparable to the GCM's measured zone amp. Measured here over the SAME
        ## window TD.gcm_series measures the GCM's amp over, so the two columns are
        ## like-for-like by construction rather than by assertion.
        iw = np.isin(YEARS, np.arange(TD.AMP_WIN[0], TD.AMP_WIN[1] + 1))
        ib = np.isin(YEARS, np.arange(DRIVER_BASE[0], DRIVER_BASE[1] + 1))
        dT_reg = float(np.median(d_gmst[:, iw].mean(axis=1)
                                 - d_gmst[:, ib].mean(axis=1)))
        a_ours = dT_reg / ser["dgmst"]
        a_gcm = ser["amp"][TD.GIS_ZONE]
        print(f"  {r.gcm:16}{r.ssp:9}{r.ism_median:11.1f}{v_gmst:9.1f}{v_dir:8.1f}"
              f"{v_gmst / r.ism_median:9.2f}x{v_dir / r.ism_median:8.2f}x"
              f"{a_ours:10.2f}{a_gcm:9.2f}")
        rows.append(dict(gcm=r.gcm, ssp=r.ssp, ism_median=r.ism_median,
                         ism_min=r.ism_min, ism_max=r.ism_max,
                         ours_gmst_route=v_gmst, ours_direct_route=v_dir,
                         r_gmst=v_gmst / r.ism_median, r_direct=v_dir / r.ism_median,
                         amp_gcm_south=a_gcm, amp_ours_effective=a_ours,
                         amp_ours_raw_param=float(np.median(amp))))
    d = pd.DataFrame(rows)
    if d.empty:
        sys.exit("no cells with both an ISMIP6 median and a cmip6_gis series")

    print(f"\n  MEDIAN over {len(d)} cells:  GMST route {d.r_gmst.median():.2f}x ISMIP6"
          f"   |   DIRECT route {d.r_direct.median():.2f}x ISMIP6")
    print(f"  EFFECTIVE amp (amp * S, derived from the driver): ours "
          f"{d.amp_ours_effective.min():.2f}-{d.amp_ours_effective.max():.2f} vs these "
          f"models' own south zone {d.amp_gcm_south.min():.2f}-"
          f"{d.amp_gcm_south.max():.2f} (median {d.amp_gcm_south.median():.2f}); "
          f"the raw gis_amp parameter is {d.amp_ours_raw_param.iloc[0]:.2f}, which is "
          f"NOT what is applied")

    print("\n=== THE VERDICT ===\n")
    g, dr = d.r_gmst.median(), d.r_direct.median()
    if dr > 1.10 and g > 1.10:
        print("  BOTH routes over-shoot ⇒ the defect is in the RESPONSE, not the amp law.")
        print("  Correcting the amplification alone would not fix 2100.")
    elif abs(dr - 1.0) < 0.10 <= abs(g - 1.0):
        print("  DIRECT lands on ISMIP6 and GMST over-shoots ⇒ the defect IS the amp law,")
        print("  and it is correctable without touching the ice response.")
    elif dr < 0.90 and g > 1.10:
        print("  COMPENSATING ERRORS. The amp law over-drives the regional temperature,")
        print("  and the calibration absorbed that into c1 against the OBSERVED south")
        print("  driver -- so removing the amp error alone makes 2100 WORSE, not better.")
        print("  The pair (amp, c1) is what is mis-anchored, and re-anchoring it is a")
        print("  REFIT, not a projection-side prior move. That is a much larger change")
        print("  than any reservoir cell, and it would move the hindcast.")
        print(f"\n  The size of it: GMST route {g:.2f}x, DIRECT route {dr:.2f}x --")
        print(f"  the two bracket ISMIP6, and the ratio between them is {g / dr:.2f}x,")
        print(f"  against an amp ratio of "
              f"{d.amp_ours_median.iloc[0] / d.amp_gcm_south.median():.2f}x.")
    else:
        print(f"  Mixed: GMST {g:.2f}x, DIRECT {dr:.2f}x. Read the per-cell table.")

    print("\n  ⚠ n IS SMALL and the cells are not independent draws of anything: "
          f"{len(d)} GCM cells,\n    one member each, and the DIRECT route needs a "
          "model present in data/cmip6_gis.\n    Marcus's stringency rule applies — "
          "this is GUIDANCE about a direction, not a\n    correction factor to apply.")

    d.to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
