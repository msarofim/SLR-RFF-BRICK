"""
diag_coulon_domain_reachability.py

OPTION (c) OF THE COULON DOMAIN HANDOFF, 2026-08-29: does our 841-config
ensemble reach Coulon's four GCMs under EITHER averaging domain?

THE SITUATION. Coulon et al. (Nat. Commun. 16:10385) report +12.0 to +17.0 degC
Antarctic-averaged warming at 2300 under SSP5-8.5 but NEVER STATE THE SPATIAL
AVERAGING DOMAIN -- verified 2026-08-29 against the PMC full text (PMC12680641),
not a summarisation pass: the paper specifies the anomaly construction
("monthly-mean air temperature ... with respect to the 1995-2014 mean seasonal
variations") and the reference period, and nothing about grounded ice vs
shelves vs a latitude band. Our reconstruction of their four GCMs therefore
lands in different places depending on a mask THE SOURCE DOES NOT PIN:

    sftlf>=50 (land proxy)  12.78 - 19.47   OUTSIDE their stated range
    all cells south of 60S  12.47 - 17.12   INSIDE

⚠ CHOOSING THE MASK THAT REPRODUCES THE PUBLISHED NUMBER IS NOT A MEASUREMENT.
That reservation belongs to the handing-off session and is carried forward
verbatim in spirit: "all cells south of 60S" contains a great deal of Southern
Ocean, which is not what an ice-sheet paper means by "Antarctic-averaged"
either. This script does NOT choose. It prices the choice.

WHAT IT MEASURES. The arm selector is the spliced ssp585 GMST anomaly at 2300
vs 1995-2014, per config; T_ant = amp x GMST, so a target is reachable iff
amp >= T_ant / max(selector). That inversion is POSTERIOR-FREE. The L21
`ais_gmst_amp` posterior then says how far into its own tail each target sits.

THE QUESTION IT ANSWERS, in the handoff's own words: "If it does under both, the
domain question does not bind and we proceed honestly. If only under one, the
comparison is domain-sensitive and that is itself the finding."

  source ~/climate-env/bin/activate && python python/diag_coulon_domain_reachability.py
"""
import os
import numpy as np
import pandas as pd

REPO      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN_CSV = os.path.join(REPO, "outputs/diag_coulon_domain_sensitivity.csv")
CUBE      = os.path.join(REPO, "data/observations/fair_cube_gmst_ssp585_spliced.csv")
POST      = os.path.join(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_L21.csv")
OUT       = os.path.join(REPO, "outputs/diag_coulon_domain_reachability.csv")

SSP        = "ssp585"
ARM_YEAR   = 2300
COULON_REF = (1995, 2014)
AMP_COL    = "ais_gmst_amp"
TAG        = "L21"
COULON_PUB = (12.0, 17.0)      # the paper's stated range, for orientation only


def selector():
    c = pd.read_csv(CUBE).set_index("year")
    ref = c.loc[COULON_REF[0]:COULON_REF[1]].mean()
    return (c.loc[ARM_YEAR] - ref).values


def main():
    sel = selector()
    amp = pd.read_csv(POST)[AMP_COL].values
    dom = pd.read_csv(DOMAIN_CSV)
    smax, amed = float(sel.max()), float(np.median(amp))
    print(f"\n{'='*84}\nCOULON DOMAIN x REACHABILITY — does our ensemble reach their GCMs "
          f"under EITHER mask?\n{'='*84}")
    print(f"  selector: spliced {SSP} GMST at {ARM_YEAR} vs {COULON_REF[0]}-{COULON_REF[1]}, "
          f"{len(sel)} configs")
    print(f"    max {smax:.3f} | p95 {np.percentile(sel,95):.3f} | median "
          f"{np.median(sel):.3f} degC")
    print(f"  {TAG} {AMP_COL}: median {amed:.4f}, sd {amp.std():.4f} "
          f"-> T_ant reachable at the median amp only up to {amed*smax:.2f} degC\n")

    rows = []
    for mask in ("sftlf>=50", "all_cells"):
        d = dom[dom["mask"] == mask].sort_values("tant_2300_degC")
        print(f"  MASK {mask}  ({d.note.iloc[0]})")
        print(f"    {'model':>14} {'T_ant':>7} {'amp needed':>11} {'amp %ile':>9} "
              f"{'n cfg @med amp':>15} {'reach @med':>11}")
        nreach = 0
        for _, r in d.iterrows():
            T = float(r.tant_2300_degC)
            need = T / smax
            pct = 100.0 * (amp >= need).mean()          # posterior support for the amp
            ncfg = int((sel * amed >= T).sum())          # configs reaching at the median amp
            ok = ncfg > 0
            nreach += ok
            print(f"    {r.model:>14} {T:7.2f} {need:11.3f} {pct:8.1f}% {ncfg:15d} "
                  f"{'YES' if ok else 'no':>11}")
            rows.append(dict(mask=mask, model=r.model, tant_2300=T, amp_needed=need,
                             amp_posterior_pct_above=pct, n_configs_at_median_amp=ncfg,
                             reachable_at_median_amp=ok))
        print(f"    -> {nreach} of {len(d)} models reachable at the median amp\n")

    r = pd.DataFrame(rows)
    a = r[r["mask"] == "sftlf>=50"].reachable_at_median_amp.sum()
    b = r[r["mask"] == "all_cells"].reachable_at_median_amp.sum()
    print(f"  VERDICT")
    if a == b:
        print(f"    The domain choice does NOT change reachability ({a} of 4 either way).")
        print(f"    The domain question does not bind on this axis; proceed and report it.")
    else:
        print(f"    ⚠ DOMAIN-SENSITIVE, AND THAT IS ITSELF THE FINDING. Reachable at the")
        print(f"      median amp: {a} of 4 under sftlf>=50, {b} of 4 under all_cells.")
        print(f"      The comparison's headline therefore MOVES with a mask the source does")
        print(f"      not specify. It cannot be reported as a single number, and picking the")
        print(f"      mask that agrees with the published range would be choosing the answer.")
        hardest = r.loc[r.groupby('mask').amp_needed.idxmax()]
        print(f"\n      hardest model per mask (amp needed / posterior support):")
        for _, h in hardest.iterrows():
            print(f"        {h['mask']:>10}  {h.model:<14} {h.amp_needed:.3f} "
                  f"({h.amp_posterior_pct_above:.1f}% of the {TAG} amp posterior)")
    print(f"\n  ⚠ the ensemble MAX is ONE DRAW (memory coulon_arm_is_one_draw): calib "
          f"1.4.5->1.6.0\n    left the selector unchanged through p99 but moved the MAX "
          f"21.46 -> 15.40. Read the\n    n-configs column, not the max, when the answer "
          f"depends on the tail.")
    r.to_csv(OUT, index=False)
    print(f"\n  wrote {OUT}\n")


if __name__ == "__main__":
    main()
