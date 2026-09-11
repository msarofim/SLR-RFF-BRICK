#!/usr/bin/env python3
"""diag_magicc_gis_hindcast.py — MAGICC-SLR's Greenland against the observations, on the
scorecard's own metric, over the only window where MAGICC HAS a Greenland hindcast.

Marcus's 9/11 comment [1], first half: does MAGICC's historical Greenland match observations?
MAGICC's Greenland module starts in 1990 (`slr_gis_*_startyear`; diag_magicc_gis_structure.py),
so the comparison can only be made from 1991 on. Scored EXACTLY as scope_ladrillo_vs_brick20_scorecard
scores the two BRICK-lineage arms (median vs obs, RMSE / mean bias / 90 % coverage, matched
years), on the scorecard's 1993-2026 window and on 1991-2026 (MAGICC's full live span), for
all three arms, so the numbers are like-for-like. ⚠ MAGICC is on its OWN climate; Ladrillo and
BRICK 2.0 share the ssp245harm FaIR driver -- a two-variable comparison, as everywhere MAGICC
appears.

  python3 python/diag_magicc_gis_hindcast.py [--tag=L24]
Writes outputs/diag_magicc_gis_hindcast_<TAG>.csv and prints the table.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scope_ladrillo_vs_brick20_scorecard as sc   # noqa: E402  (score(), REF, paths)
from provenance import stamp                        # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = next((a[len("--tag="):] for a in sys.argv[1:] if a.startswith("--tag=")), "L24")
MAG_CSV = os.path.join(REPO, "data/comparison/magicc_nauels_components_hist.csv")
OUT = os.path.join(REPO, "outputs", "diag_magicc_gis_hindcast_%s.csv" % TAG)
WINDOWS = [("1993-2026 (scorecard)", (1993, 2026)), ("1991-2026 (MAGICC live span)", (1991, 2026))]
COMP = "gis"


def main():
    lad, brk, tgt = sc.load()
    mg = pd.read_csv(MAG_CSV)
    mg = mg[mg.component == COMP].set_index("year").sort_index()
    assert (mg.unit == "cm rel %d-%d" % sc.REF).all(), mg.unit.unique()
    obs = tgt[COMP]
    ## Coverage bands: Ladrillo/BRICK per the scorecard's own columns; MAGICC's 5-95 %.
    arms = [("Ladrillo %s" % TAG, lad["%s_p50" % COMP], lad["%s_p05" % COMP], lad["%s_p95" % COMP]),
            ("BRICK 2.0", brk["%s_p50" % COMP], brk["%s_p5" % COMP], brk["%s_p95" % COMP]),
            ("MAGICC-SLR", mg["med"], mg["p05"], mg["p95"])]
    rows = []
    print("Greenland vs observations (Frederikse 2020 + GRACE/GRACE-FO), cm rel %d-%d, "
          "median vs obs on matched years" % sc.REF)
    for wname, win in WINDOWS:
        print("  %s" % wname)
        for name, p50, lo, hi in arms:
            s = sc.score(p50, lo, hi, obs, win)
            if s is None:
                continue
            rows.append(dict(window=wname, arm=name, **s))
            print("    %-14s n=%2d  bias %+6.3f  RMSE %6.3f  max|r| %6.3f  cov90 %4.2f"
                  % (name, s["n"], s["mean_bias"], s["rmse"], s["max_abs"], s["coverage90"]))
        r = {x["arm"]: x["rmse"] for x in rows if x["window"] == wname}
        print("    RMSE ratio: Ladrillo/MAGICC %.2f, BRICK/MAGICC %.2f"
              % (r["Ladrillo %s" % TAG] / r["MAGICC-SLR"], r["BRICK 2.0"] / r["MAGICC-SLR"]))
    print("  ⚠ IN-SAMPLE vs OUT-OF-SAMPLE: Ladrillo is FITTED to this Greenland target (its "
          "RMSE is in-sample); BRICK 2.0 was fitted to its own older target; MAGICC's "
          "Greenland is an offline SICOPOLIS-derived law never fitted to a sea-level record. "
          "The ranking is real but is not three out-of-sample skills.")
    df = pd.DataFrame(rows)
    df = stamp(df, os.path.basename(__file__), tag=TAG,
               inputs={k: os.path.relpath(p, REPO) for k, p in
                       (("ladrillo", sc.L10_TS), ("brick20", sc.B20_TS),
                        ("targets", sc.TARGETS), ("magicc_hist", MAG_CSV))},
               extra="cm rel %d-%d; MAGICC on its own climate, others on ssp245harm; MAGICC "
                     "Greenland starts 1990" % sc.REF)
    df.to_csv(OUT, index=False)
    print("wrote %s" % os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    main()
