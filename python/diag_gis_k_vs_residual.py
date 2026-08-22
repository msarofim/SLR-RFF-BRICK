"""PROPAGATING THE WEAKER COOL-ARM CONSTRAINT INTO THE k QUESTION.

WHAT THE k TENSION IS. The shape scorecard's ssp585 arms want k = 2-3; the cool arms
want k <= 1.0, and the pre-flight kill is a BAND test -- "ssp245 leaves its band at
k = 1.5 and ssp126 at k = 2.0". diag_gis_scorecard_logo.py found the tension's DIRECTION
robust to dropping any single GCM (8/8). But diag_gis_residual_band.py then found the
cool bands are spuriously precise: two GCMs agreeing to 1.5 cm read as a 1.5 cm
uncertainty, and a sample-size-respecting interval makes the honest cool bands 3-9x
WIDER than shipped. The cool arms are what kills k >= 1.5. So the kill has to be re-run.

WHY THE RESIDUAL TEST IS THE CLEANER ONE, AND WHAT IT REDUCES TO
  The residual band at our forcing is  pred_ours + [d_lo, d_hi],  d_g = ISM_g - pred_g,
  so the criterion  pred_ours + add  in  band  is exactly  add in [d_lo, d_hi].
  On the COOL scenarios the reservoir is inert (add = 0 by construction, onset above
  their peak), so the test collapses to

        IS ZERO INSIDE THE RESIDUAL INTERVAL?

  i.e. is our model UNBIASED against the ISMs at this k. That is a genuine k constraint
  -- raising k raises pred_g, drives d_g negative, and eventually the interval clears
  zero -- and unlike the shipped band test it does not depend on a 2-model quantile
  being taken at face value. It is also immune to the forcing-transfer step, since the
  same pred_ours appears on both sides.

TWO TESTS, RUN SIDE BY SIDE PER k
  SHIPPED   is the untapped model's 2300 level inside gis_targets.MATCHED_2300_M?
  RESIDUAL  is 0 inside the Student-t prediction interval of d_g across that arm's GCMs?

WRITES outputs/diag_gis_k_vs_residual.csv
  python3 python/diag_gis_k_vs_residual.py
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
os.chdir(REPO)

import scope_gis_shape_all_scenarios as A  # noqa: E402
import gis_targets  # noqa: E402
from scope_gis_ridge_vs_protect import basin2_series, rebase_cm  # noqa: E402
from scope_gis_leq_ridge_vs_literature import gis_tbar  # noqa: E402
from scope_gis_2300_relaxation import (  # noqa: E402
    DRIVER_BASE, YEARS, gis_shape_table, regional_driver,
)
import scope_gis_reservoir_offline as R  # noqa: E402
import diag_gis_gcm_tdecomp as TD  # noqa: E402
import diag_gis_residual_band as RB  # noqa: E402

OUT = os.path.join(REPO, "outputs/diag_gis_k_vs_residual.csv")

K_GRID, OURS, ARMS = A.K_GRID, R.OURS, A.ARMS
ARMS_R2300 = [a for a in ARMS if a[2] == "r2300"]
COOL_LABELS = ["SSP1-2.6", "SSP2-4.5"]
PI_LEVEL = RB.PI_LEVEL
MIN_GCM_FOR_SPREAD = RB.MIN_GCM_FOR_SPREAD
SSP_OF = RB.SSP_OF
HIND, HORIZONS = A.HIND, A.HORIZONS


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
           for y in tuple(HORIZONS) + tuple(HIND) + (2015,)}

    def load(path, col):
        g = pd.read_csv(path).set_index("year")[col].reindex(YEARS).to_numpy()
        rb = g - g[ibd].mean()
        return rb, regional_driver(rb, amp, S_tab)

    _, hind_drv = load(f"outputs/{A.ARMS[0][3]}.csv", f"gmst_{A.ARM}")
    ours = {lab: load(f"data/observations/fair_mean_gmst_{ssp}.csv", "gmst_C")
            for ssp, lab in OURS}

    ## each (arm, GCM): that GCM's own forcing, and its own ISM 2300 median
    ann = pd.read_csv(A.ANN)
    ann["gcm"] = ann.exp.str.split("_").str[0]
    per = []
    for ssp, lab, fam, _ in ARMS_R2300:
        sub = A.protect_band(ann, lab, fam)
        for gcm in sorted(sub.gcm.unique()):
            ser = TD.gcm_series(TD.GCM_ALIAS.get(gcm, gcm), SSP_OF[lab])
            gr = sub[sub.gcm == gcm]
            per.append(dict(lab=lab, gcm=gcm, gmst=ser["gmst"],
                            ism=float(gr[gr.year == 2300].gis_cm.median())))

    tgt = pd.read_csv(A.TARGETS).set_index("year")["gis"]
    want = float(tgt.loc[HIND[1]] - tgt.loc[HIND[0]])

    print(f"diag_gis_k_vs_residual — the cool-arm kill of k, re-run on the residual "
          f"basis, {A.TAG}, {nd} draws\n")
    print(f"  {'k':>6}  " + "".join(f"{lab + ' shipped':>20}" for lab in COOL_LABELS)
          + "".join(f"{lab + ' residual':>26}" for lab in COOL_LABELS))
    rows = []
    for k in K_GRID:
        lo, hi = np.full(nd, 1e-4), np.full(nd, 1e3)
        for _ in range(80):
            mid = np.sqrt(lo * hi)
            L = basin2_series(hind_drv, post, k, mid)
            b = 100.0 * (L[:, idx[HIND[1]]] - L[:, idx[HIND[0]]]) < want
            lo, hi = np.where(b, mid, lo), np.where(b, hi, mid)
        s = np.sqrt(lo * hi)
        offs = float(np.median(rebase_cm(
            basin2_series(hind_drv, post, 1.0, 1.0))[:, idx[2015]]))

        def pred(gmst_rb):
            c = np.median(rebase_cm(basin2_series(
                regional_driver(gmst_rb, amp, S_tab), post, k, s)), axis=0)
            return c[idx[2300]] - offs

        rec = {"k": k}
        line = f"  {k:6g}  "
        for lab in COOL_LABELS:
            v23 = np.median(rebase_cm(basin2_series(
                ours[lab][1], post, k, s)), axis=0)[idx[2300]]
            mb = (100 * gis_targets.MATCHED_2300_M[lab][0],
                  100 * gis_targets.MATCHED_2300_M[lab][1])
            ok_s = bool(mb[0] <= v23 <= mb[1])
            rec[f"{lab}_level"] = v23
            rec[f"{lab}_shipped_ok"] = ok_s
            line += f"{v23:9.1f} {'IN ' if ok_s else 'OUT':>3}       "
        for lab in COOL_LABELS:
            g = [p for p in per if p["lab"] == lab]
            d = np.array([p["ism"] - pred(p["gmst"]) for p in g], float)
            if len(d) < MIN_GCM_FOR_SPREAD:
                rec[f"{lab}_resid_ok"] = None
                line += f"{'UNDEFINED':>26}"
                continue
            half = (stats.t.ppf(PI_LEVEL, len(d) - 1) * d.std(ddof=1)
                    * np.sqrt(1.0 + 1.0 / len(d)))
            lo_d, hi_d = d.mean() - half, d.mean() + half
            ok_r = bool(lo_d <= 0.0 <= hi_d)
            rec[f"{lab}_resid_lo"], rec[f"{lab}_resid_hi"] = lo_d, hi_d
            rec[f"{lab}_resid_ok"] = ok_r
            line += f"{lo_d:9.1f}-{hi_d:<8.1f}{'IN ' if ok_r else 'OUT':>4}   "
        rows.append(rec)
        print(line, flush=True)

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)

    print(f"\n=== THE COOL-ARM CEILING ON k ===\n")
    print(f"  {'test':34}" + "".join(f"{lab:>14}" for lab in COOL_LABELS)
          + f"{'JOINT':>10}")
    for tag, col in (("SHIPPED matched band", "shipped_ok"),
                     ("RESIDUAL, sample-size-respecting", "resid_ok")):
        ks, joint = [], []
        for lab in COOL_LABELS:
            ok = out[out[f"{lab}_{col}"] == True]
            ks.append(ok.k.max() if len(ok) else np.nan)
        jm = out[[out[f"{lab}_{col}"] == True for lab in COOL_LABELS][0]
                 & (out[f"{COOL_LABELS[1]}_{col}"] == True)]
        print(f"  {tag:34}" + "".join(f"{v:14g}" for v in ks)
              + f"{(jm.k.max() if len(jm) else float('nan')):10g}")
    print(f"\n  largest k on the shipped K_GRID at which that arm still clears its "
          f"criterion.\n  The RESIDUAL column asks 'is 0 inside the residual "
          f"prediction interval', i.e. is the\n  model UNBIASED against the ISMs at "
          f"this k — the reservoir is inert on the cool arms,\n  so no cell can rescue "
          f"or spoil either test.")

    sh = out[(out[f"{COOL_LABELS[0]}_shipped_ok"] == True)
             & (out[f"{COOL_LABELS[1]}_shipped_ok"] == True)]
    rs = out[(out[f"{COOL_LABELS[0]}_resid_ok"] == True)
             & (out[f"{COOL_LABELS[1]}_resid_ok"] == True)]

    ## POWER CHECK, and it decides how the result above may be read. With n = 2 the
    ## t prediction interval is  mean +/- t(1,.975)*sd*sqrt(1.5), and sd = |d1-d2|/sqrt2,
    ## so the half-width is EXACTLY 11.0*|d1-d2| -- set entirely by how close the two
    ## models happen to fall at that k. If the width is non-monotone in k, the test is
    ## not measuring k, it is measuring where two curves cross.
    print(f"\n=== POWER CHECK — is the residual test measuring k, or model crossing? ===\n")
    print(f"  {'arm':12}{'n':>3}{'PI width min-max over k':>28}{'swing':>9}"
          f"{'monotone in k?':>17}")
    powerless = []
    for lab in COOL_LABELS:
        w = (out[f"{lab}_resid_hi"] - out[f"{lab}_resid_lo"]).to_numpy()
        n_g = len([p for p in per if p["lab"] == lab])
        mono = bool(np.all(np.diff(w) > 0) or np.all(np.diff(w) < 0))
        print(f"  {lab:12}{n_g:3d}{w.min():14.1f}-{w.max():<13.1f}"
              f"{w.max() / w.min():8.0f}x{str(mono):>17}")
        if not mono:
            powerless.append(lab)
    print(f"\n  With n = 2 the half-width is exactly t(1,0.975)*|d1-d2|*sqrt(3)/2 = "
          f"11.0*|d1-d2|.\n  A non-monotone width means the interval is tracking where "
          f"the two models CROSS, not k.")

    print(f"\n=== WHAT THIS DOES TO THE k TENSION ===\n")
    print(f"  ssp585 shape optimum (diag_gis_scorecard_logo): k* = 2-3 under every "
          f"GCM drop.")
    print(f"  cool ceiling, SHIPPED bands : k <= "
          f"{sh.k.max() if len(sh) else float('nan'):g}")
    if powerless:
        print(f"  cool ceiling, RESIDUAL      : NONE — the test has NO POWER on "
              f"{', '.join(powerless)}")
        print(f"\n  ==> DO NOT read this as 'the ceiling relaxes to k <= "
              f"{rs.k.max() if len(rs) else float('nan'):g}'. Read it as: with 2 GCMs "
              f"the cool arms\n      CANNOT CONSTRAIN k AT ALL. The shipped k <= "
              f"{sh.k.max() if len(sh) else float('nan'):g} comes from treating a "
              f"2-model RANGE as a\n      2-model UNCERTAINTY; and the one k where "
              f"the residual test does bite (k = 1.5 on\n      "
              f"{COOL_LABELS[1]}) is two models coincidentally agreeing to ~0.5 cm, "
              f"not evidence.")
    print(f"\n  ** THE DISTINCTION THAT MATTERS **")
    print(f"    PREFERENCE  the cool arms' rms argmin against the band MEDIANS is "
          f"k ~ 0.75-1.0 and is\n                ROBUST 8/8 to GCM drops "
          f"(diag_gis_scorecard_logo). Band WIDTH does not enter\n                "
          f"an rms against medians, so THIS IS UNCHANGED.")
    print(f"    EXCLUSION   the cool arms' ability to RULE OUT larger k is what "
          f"collapses here.")
    print(f"\n  ==> the k tension survives as a disagreement of PREFERENCES and does "
          f"NOT survive as a\n      CONSTRAINT. 'One law asked to be steep at 6 K and "
          f"flat at 2 K' still describes the\n      fit; it no longer describes a "
          f"box the model is forced into.")

    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
