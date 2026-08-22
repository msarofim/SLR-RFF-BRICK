"""DOES A LIKE-FOR-LIKE DRIVER FIX THE 2100 OVER-PREDICTION, AND WHAT DOES IT COST AT 2300?

THE CORRECTION THIS SCRIPT OPENS WITH. diag_gis_gcm_tdecomp.py reported that our law
applies a "NORTH-sized amplification to a SOUTH-zone driver". That reading was WRONG.
The 1.33x gap decomposes as

    1.2864x   obs_amp_full / r_anchor -- the law is anchored to the OBSERVED south
              amplification 1.9222 while CMIP6's own south secant at the anchor is
              1.4942. That is memory ladrillo_gis_amp item 3, "KEEP THE OBSERVED
              LEVEL", a DOCUMENTED DESIGN CHOICE, not an error.
    ~1.04x    flat-hold above 2.75 K against the measured decline (sub-choice 1).

  It is not a zone mistake. My own measurement also RECONCILES with the repo's own
  per-window secant on the same models (CESM2 1.05 vs 1.11, CNRM 1.12 vs 1.15,
  IPSL 1.347 vs 1.339, MPI 1.30 vs 1.24), so neither estimator is at fault.

BUT THE LIKE-FOR-LIKE PROBLEM IS REAL, AND SHARPER. Keeping the observed level is
defensible for REAL-WORLD projection -- the models may understate Greenland
amplification. It is NOT defensible when scoring against a PROTECT run that a specific
GCM forced: that ice sheet saw THAT GCM's Greenland warming, not the observed-anchored
one. Memory like_for_like_forcing: forcing trajectory first.

THE EXPERIMENT
  Per (arm, GCM), our model at 2100 AND 2300 under two drivers, against that GCM's own
  ISM runs at the same two horizons:
    SHIPPED    regional_driver(GMST_gcm, amp draws, S)   -- observed-anchored
    LIKEFORLIKE that GCM's OWN south-Greenland anomaly spliced directly
  The prior (handoff section 8) is that we run 20-45 % FAST before 2100 and SHORT at
  2300. If the like-for-like driver fixes 2100 it should also WORSEN 2300 -- which
  would be the "steep at 6 K, flat at 2 K" shape problem restated on the driver rather
  than on k, and would say the two defects are ONE defect.

WHY THERE IS NO REFIT TO DO, and this is the honest answer to "correct and refit"
  c1/c0 are constrained by the HISTORICAL fit, whose driver is OBSERVED south-Greenland
  temperature through 2024 -- gis_offline_cell.py's objective is history-only (its
  PROJ_* block is "G4 EVALUATION ONLY, never in the objective", line 206). A
  projection-side amplification law therefore cannot move them, and the rate-scale
  bisection targets the same observed window, so it does not move either. Changing the
  projected driver is a PURE PROJECTION change; there is nothing to refit offline, and
  a refit that DID respond would have to be the MCMC chain, which this does not touch.

WRITES outputs/diag_gis_amp_likeforlike_2100.csv
  python3 python/diag_gis_amp_likeforlike_2100.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
os.chdir(REPO)

import scope_gis_shape_all_scenarios as A  # noqa: E402
from scope_gis_ridge_vs_protect import basin2_series, rebase_cm  # noqa: E402
from scope_gis_leq_ridge_vs_literature import gis_tbar  # noqa: E402
from scope_gis_2300_relaxation import (  # noqa: E402
    DRIVER_BASE, YEARS, gis_shape_table, regional_driver,
)
import diag_gis_gcm_tdecomp as TD  # noqa: E402

OUT = os.path.join(REPO, "outputs/diag_gis_amp_likeforlike_2100.csv")

TAG, ARMS = A.TAG, A.ARMS
ARMS_R2300 = [a for a in ARMS if a[2] == "r2300"]
SSP_OF = TD.SSP_OF
HORIZONS_TEST = (2100, 2300)
K_FIXED = 1.0
OBS_AMP_FULL, R_ANCHOR = 1.9221976385152952, 1.4942493826789536
LEVEL_OFFSET = OBS_AMP_FULL / R_ANCHOR


def main():
    post = pd.read_csv(A.POST)
    tbar = gis_tbar()
    r_s = np.exp(post["gis_slow_ell"].to_numpy())
    post["gis_alpha_s"] = post["gis_slow_w"].to_numpy() * r_s / tbar
    post["gis_beta_s"] = (1.0 - post["gis_slow_w"].to_numpy()) * r_s
    amp = post["gis_amp"].to_numpy()
    S_tab = gis_shape_table()
    nd = len(post)
    ibd = (YEARS >= DRIVER_BASE[0]) & (YEARS <= DRIVER_BASE[1])
    idx = {y: int(np.where(YEARS == y)[0][0])
           for y in HORIZONS_TEST + tuple(A.HIND) + (2015,)}

    g = pd.read_csv(f"outputs/{ARMS[0][3]}.csv").set_index(
        "year")[f"gmst_{A.ARM}"].reindex(YEARS).to_numpy()
    hind_drv = regional_driver(g - g[ibd].mean(), amp, S_tab)
    tgt = pd.read_csv(A.TARGETS).set_index("year")["gis"]
    want = float(tgt.loc[A.HIND[1]] - tgt.loc[A.HIND[0]])
    lo, hi = np.full(nd, 1e-4), np.full(nd, 1e3)
    for _ in range(80):
        mid = np.sqrt(lo * hi)
        L = basin2_series(hind_drv, post, K_FIXED, mid)
        b = 100.0 * (L[:, idx[A.HIND[1]]] - L[:, idx[A.HIND[0]]]) < want
        lo, hi = np.where(b, mid, lo), np.where(b, hi, mid)
    s = np.sqrt(lo * hi)
    offs = float(np.median(rebase_cm(
        basin2_series(hind_drv, post, 1.0, 1.0))[:, idx[2015]]))

    def curve(drv):
        c = np.median(rebase_cm(basin2_series(drv, post, K_FIXED, s)), axis=0)
        return {y: c[idx[y]] - offs for y in HORIZONS_TEST}

    ann = pd.read_csv(A.ANN)
    ann["gcm"] = ann.exp.str.split("_").str[0]

    print(f"diag_gis_amp_likeforlike_2100 — does a like-for-like driver fix 2100? "
          f"{TAG}, {nd} draws")
    print(f"  the law's built-in LEVEL OFFSET vs CMIP6 = obs_amp_full/r_anchor = "
          f"{LEVEL_OFFSET:.4f}x (BY DESIGN)\n")
    rows = []
    for ssp, lab, fam, _ in ARMS_R2300:
        sub = A.protect_band(ann, lab, fam)
        for gcm in sorted(sub.gcm.unique()):
            ser = TD.gcm_series(TD.GCM_ALIAS.get(gcm, gcm), SSP_OF[lab])
            gr = sub[sub.gcm == gcm]
            ism = {y: float(gr[gr.year == y].gis_cm.median()) for y in HORIZONS_TEST}
            sh = curve(regional_driver(ser["gmst"], amp, S_tab))
            lf = curve(TD.driver_from_regional(ser["reg"], nd))
            rows.append(dict(arm=f"{lab} {fam}", gcm=gcm,
                             **{f"ism_{y}": ism[y] for y in HORIZONS_TEST},
                             **{f"shipped_{y}": sh[y] for y in HORIZONS_TEST},
                             **{f"likeforlike_{y}": lf[y] for y in HORIZONS_TEST}))
    out = pd.DataFrame(rows)
    for y in HORIZONS_TEST:
        out[f"r_shipped_{y}"] = out[f"shipped_{y}"] / out[f"ism_{y}"]
        out[f"r_lfl_{y}"] = out[f"likeforlike_{y}"] / out[f"ism_{y}"]
    out.to_csv(OUT, index=False)

    for y in HORIZONS_TEST:
        print(f"=== {y} — ours / ISM (1.00 = perfect; >1 = we run FAST) ===\n")
        print(f"  {'arm':22}{'GCM':20}{'ISM':>8}{'shipped':>9}{'ratio':>8}"
              f"{'like4like':>11}{'ratio':>8}")
        for _, r in out.iterrows():
            print(f"  {r.arm:22}{r.gcm:20}{r[f'ism_{y}']:8.1f}{r[f'shipped_{y}']:9.1f}"
                  f"{r[f'r_shipped_{y}']:8.2f}{r[f'likeforlike_{y}']:11.1f}"
                  f"{r[f'r_lfl_{y}']:8.2f}")
        print()

    print(f"=== THE VERDICT ===\n")
    print(f"  {'horizon':10}{'driver':14}{'median ours/ISM':>18}{'range':>18}"
          f"{'|log| mean':>13}")
    summ = {}
    for y in HORIZONS_TEST:
        for nm, c in (("shipped", f"r_shipped_{y}"), ("like-for-like", f"r_lfl_{y}")):
            v = out[c]
            summ[(y, nm)] = float(np.mean(np.abs(np.log(v))))
            print(f"  {y:<10}{nm:14}{v.median():18.2f}{v.min():9.2f}-{v.max():<8.2f}"
                  f"{summ[(y, nm)]:13.3f}")
    print(f"\n  |log| mean is the scale-free error: 0 is perfect, and it treats a "
          f"factor 2 high\n  and a factor 2 low alike.\n")
    for y in HORIZONS_TEST:
        a, b = summ[(y, "shipped")], summ[(y, "like-for-like")]
        verdict = "IMPROVES" if b < a else "WORSENS"
        print(f"  {y}: like-for-like {verdict} the fit, {a:.3f} -> {b:.3f} "
              f"({a / b:.2f}x)")
    d21 = summ[(2100, "shipped")] - summ[(2100, "like-for-like")]
    d23 = summ[(2300, "shipped")] - summ[(2300, "like-for-like")]
    if d21 > 0 and d23 < 0:
        print(f"\n  ==> THE TWO DEFECTS ARE ONE DEFECT. The like-for-like driver fixes "
              f"2100 and costs\n      2300 — the SAME trade the k tension describes "
              f"(steep at 6 K, flat at 2 K),\n      now visible on the DRIVER rather "
              f"than on k. A single amplification level cannot\n      serve both "
              f"horizons, exactly as a single k cannot serve both ends of the\n      "
              f"scenario range.")
    elif d21 > 0 and d23 > 0:
        print(f"\n  ==> the like-for-like driver improves BOTH horizons. The "
              f"observed-level anchor is\n      then simply too high for scoring "
              f"against GCM-forced ISM runs, with no trade.")
    else:
        print(f"\n  ==> the like-for-like driver does NOT fix 2100. The amplification "
              f"hypothesis for the\n      2100 over-prediction is REFUTED; look "
              f"elsewhere.")
    print(f"\n  NO REFIT IS INVOLVED, and none is available: c1/c0 are fixed by the "
          f"HISTORICAL fit,\n  whose driver is OBSERVED through 2024, and the "
          f"rate-scale bisection targets the same\n  window. A projection-side "
          f"amplification law cannot move either. Anything that DID\n  respond would "
          f"have to be the MCMC chain.")
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
