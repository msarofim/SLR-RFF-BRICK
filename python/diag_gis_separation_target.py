"""WHAT IS THE GREENLAND 2300 SCENARIO-SEPARATION TARGET, ACTUALLY?

The reservoir exists to buy between-scenario separation (Marcus 2026-08-23: "we
aren't trying to match between-model spread ... just between-scenario spreads"), and
this repo has quoted two separation numbers for years:

    ssp585/ssp245 = 7.9-31.9x   from LIT_2300_M
    ssp585/ssp245 = 2.00-13.68x from MATCHED_2300_M

NEITHER IS A RATIO DISTRIBUTION. Both are the band's endpoints DIVIDED -- hi585/lo245
and lo585/hi245 -- which is the outer envelope you get by assuming the two scenarios'
uncertainties are independent. They are not: every anchor past 2100 is NORCE-CISM, so
a run's ssp585 and its ssp126 share an ice-sheet model, a parameter set and a drift
correction. Dividing endpoints therefore produces a band far wider than the ensemble's
own spread of ratios, and a model can sit "inside" it while matching nothing.

THREE CONSTRUCTIONS, ALL REPORTED, because they disagree and the disagreement is the
finding:

  [A] ENDPOINT DIVISION      what has been quoted. Kept so the old numbers stay
                             reproducible and their width is visible next to the others.
  [B] MATCHED p50 RATIO      the ratio of the forcing-matched central estimates. This
                             is the like-for-like CENTRAL target: MATCHED_2300_P50_M is
                             PCHIP'd to OUR OWN forcing integral, so it answers "what
                             separation does the physics imply for OUR scenarios".
  [C] GCM-PAIRED RATIOS      for each GCM present in BOTH scenarios, that GCM's own
                             ssp585/cool ratio. A real ratio distribution with the
                             shared-model term cancelled -- but at each GCM's OWN
                             scenario contrast, not ours, so it is a SHAPE check, not
                             a level target. Reported with its n, because n is 2-3.

READ-ONLY. Writes one CSV.
  python3 python/diag_gis_separation_target.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
os.chdir(REPO)

import gis_targets  # noqa: E402
import scope_gis_shape_all_scenarios as A  # noqa: E402

OUT = os.path.join(REPO, "outputs/diag_gis_separation_target.csv")
Y = 2300
PAIRS = [("SSP5-8.5", "SSP2-4.5"), ("SSP5-8.5", "SSP1-2.6")]
## The GCM alias map, from build_protect_r2300_forcing.py -- the SAME GCM appears
## under different run names across scenarios, and pairing on the raw name would
## silently drop the only two pairs that exist.
ALIAS = {"CESM2-Leo": "CESM2", "UKESM1-0-LL-Robin": "UKESM1-0-LL"}
## The model arms to place against the target. Greenland median @2300, cm, from
## outputs/diag_gis_cell_vs_priority_ladder.csv (the like-for-like Julia run).
LADDER_CSV = os.path.join(REPO, "outputs/diag_gis_cell_vs_priority_ladder.csv")


def main():
    lit, mat = gis_targets.LIT_2300_M, gis_targets.MATCHED_2300_M
    p50 = gis_targets.MATCHED_2300_P50_M
    rows = []

    print(f"=== THE GREENLAND {Y} SCENARIO-SEPARATION TARGET, THREE WAYS ===\n")
    print("  [A] ENDPOINT DIVISION of the 2300 bands — what this repo has been quoting.")
    print("      An outer envelope under an INDEPENDENCE assumption the ensemble does")
    print("      not satisfy; reported so its width is visible, not as the target.\n")
    print(f"      {'pair':22}{'literature':>22}{'forcing-matched':>24}")
    for hi, lo in PAIRS:
        L = (lit[hi][0] / lit[lo][1], lit[hi][1] / lit[lo][0])
        M = (mat[hi][0] / mat[lo][1], mat[hi][1] / mat[lo][0])
        print(f"      {hi + '/' + lo:22}{f'{L[0]:.2f}-{L[1]:.1f}x':>22}"
              f"{f'{M[0]:.2f}-{M[1]:.1f}x':>24}")
        rows += [dict(pair=f"{hi}/{lo}", construction="endpoint_div_lit",
                      lo=L[0], mid=np.nan, hi=L[1], n=np.nan),
                 dict(pair=f"{hi}/{lo}", construction="endpoint_div_matched",
                      lo=M[0], mid=np.nan, hi=M[1], n=np.nan)]

    print("\n  [B] MATCHED p50 RATIO — the like-for-like CENTRAL target.")
    print("      MATCHED_2300_P50_M is PCHIP'd to OUR OWN 2015-2300 forcing integral,")
    print("      so this is the separation the physics implies for OUR scenarios.\n")
    print(f"      {'pair':22}{'p50 ratio':>12}   from p50 cm")
    for hi, lo in PAIRS:
        r = p50[hi] / p50[lo]
        print(f"      {hi + '/' + lo:22}{r:11.2f}x   {100*p50[hi]:.1f} / {100*p50[lo]:.1f}")
        rows.append(dict(pair=f"{hi}/{lo}", construction="matched_p50_ratio",
                         lo=np.nan, mid=r, hi=np.nan, n=np.nan))

    print("\n  [C] GCM-PAIRED RATIOS — a real ratio distribution, shared-model term")
    print("      cancelled. At each GCM's OWN scenario contrast, so this is a SHAPE")
    print("      check and not a level target. n is small and is printed for that reason.\n")
    ann = pd.read_csv(A.ANN)
    s = ann[ann.year == Y].copy()
    s["gcm"] = s.exp.str.split("_").str[0].replace(ALIAS)
    s["fam"] = s.exp.str.extract(r"(r2300|x2300)")
    med = s.groupby(["ssp", "fam", "gcm"]).gis_cm.median()
    print(f"      {'pair':22}{'family':>8}{'GCM':>20}{'ratio':>10}")
    for hi, lo in PAIRS:
        vals = []
        for fam in ("r2300", "x2300"):
            common = sorted(set(med.get((hi, fam), pd.Series(dtype=float)).index)
                            & set(med.get((lo, fam), pd.Series(dtype=float)).index))
            for g in common:
                r = med[(hi, fam, g)] / med[(lo, fam, g)]
                vals.append(r)
                print(f"      {hi + '/' + lo:22}{fam:>8}{g:>20}{r:9.2f}x")
                rows.append(dict(pair=f"{hi}/{lo}",
                                 construction=f"gcm_paired_{fam}_{g}",
                                 lo=np.nan, mid=r, hi=np.nan, n=1))
        if vals:
            print(f"      {'':22}{'':>8}{'--> range':>20}"
                  f"{min(vals):9.2f}-{max(vals):.2f}x   (n={len(vals)} GCM pairs)")
            rows.append(dict(pair=f"{hi}/{lo}", construction="gcm_paired_range",
                             lo=min(vals), mid=float(np.median(vals)), hi=max(vals),
                             n=len(vals)))

    # --- where the model arms sit ------------------------------------------------
    if os.path.isfile(LADDER_CSV):
        d = pd.read_csv(LADDER_CSV)
        g = d[d.quantity == f"gis_{Y}_cm"]
        arms = [a for a in g.arm.unique()]
        print(f"\n=== WHERE EACH ARM SITS (Greenland median @{Y}, cm) ===\n")
        hdr = "".join(f"{h + '/' + l:>18}" for h, l in PAIRS)
        print(f"  {'arm':32}{'126':>8}{'245':>8}{'585':>8}{hdr}")
        for a in arms:
            sub = g[g.arm == a].set_index("ssp").value
            if not {"SSP1-2.6", "SSP2-4.5", "SSP5-8.5"} <= set(sub.index):
                continue
            line = f"  {a:32}{sub['SSP1-2.6']:8.1f}{sub['SSP2-4.5']:8.1f}{sub['SSP5-8.5']:8.1f}"
            for hi, lo in PAIRS:
                r = sub[hi] / sub[lo]
                tgt = p50[hi] / p50[lo]
                line += f"{f'{r:.2f}x ({r/tgt:.2f})':>18}"
                rows.append(dict(pair=f"{hi}/{lo}", construction=f"arm::{a}",
                                 lo=np.nan, mid=r, hi=np.nan, n=np.nan))
            print(line)
        print("  (parenthesis = ratio / the matched p50 ratio [B])")

        ## WHERE THE DISCREPANCY LIVES. A separation ratio can be off because the warm
        ## arm is wrong or because the cool one is; the ratio alone cannot say which,
        ## and that distinction decides what to fix.
        print(f"\n  PER-SCENARIO vs the matched p50 — which arm carries the ratio error")
        print(f"  {'arm':32}" + "".join(f"{s:>14}" for s in
                                        ("SSP1-2.6", "SSP2-4.5", "SSP5-8.5")))
        for a in arms:
            sub = g[g.arm == a].set_index("ssp").value
            if not {"SSP1-2.6", "SSP2-4.5", "SSP5-8.5"} <= set(sub.index):
                continue
            print(f"  {a:32}" + "".join(f"{sub[s] / (100 * p50[s]):13.2f}x"
                                        for s in ("SSP1-2.6", "SSP2-4.5", "SSP5-8.5")))

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
