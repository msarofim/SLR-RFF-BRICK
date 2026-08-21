#!/usr/bin/env python3
"""
build_gis_matched_targets.py — THE FORCING-MATCHED 2300 TARGET SET.

WHY (2026-08-21g, notes/handoff_2026-08-21d ... §2.1 step 2)
  `LIT_2300_M` is a set of literature bands, each produced at ITS OWN forcing.
  Scoring our model's ssp585 against a band produced at 13.8 K when our ssp585
  reaches 7.8 K is not a comparison -- it is the trap that already inverted the
  2026-08-21a reading of this same dataset. This script builds the band that the
  PROTECT-Greenland physics ensemble implies AT OUR OWN FORCING, for all three
  scenarios, from the measurements in scope_gis_cool_band_forcing.py.

THE METHOD, and why this one
  Five (forcing, GIS SLR@2300) anchors exist -- ssp126 r2300/x2300, ssp245 r2300,
  ssp585 r2300/x2300 -- spanning 1.96-13.80 K and 544-2614 K.yr. Rather than fit a
  parametric response, the anchors are INTERPOLATED directly ([[use real data]]):
  monotone PCHIP through log(SLR) against the predictor, per quantile, evaluated at
  our own scenario's predictor value.

  PREDICTOR = the TIME-INTEGRAL of GSAT over 2015-2300, not the 2300 level. An ice
  sheet integrates forcing: r2300 and x2300 can share a 2300 level and differ by
  centuries of accumulated melt, and conversely. The 2300-LEVEL arm is computed too
  and reported as the stated sensitivity, never silently dropped.

  ANCHORS ARE SORTED AND DEDUPLICATED IN THE PREDICTOR, and non-monotone anchor
  SLR is NOT smoothed away -- PCHIP is monotone in its INTERPOLANT, not in the
  data, so a dip stays a dip and is reported.

WHAT MOVES, stated up front so the result cannot be oversold
  Only ssp585 moves materially. ssp245's forcing integral matches ours to 1.00x and
  ssp126's to 1.10x, so their bands are already forcing-matched -- which is the
  answer to the falsifier the handoff pre-registered, and it means the k <= 1.25
  kill from the pre-flight SURVIVES re-targeting.

THE HULL RULE, and why ssp126 does NOT get the interpolated number
  Our ssp126 integral (495 K.yr) sits BELOW the lowest anchor (544). PCHIP's left
  end-slope there is set by the 544 -> 651 segment, which DECREASES (11.1 -> 9.8 cm
  p50) -- and that decrease is not a forcing response, it is the two anchors being
  different FAMILIES and different GCMs. Extrapolating on it flares the band to
  4.8-25.5 cm, which is an artefact of ensemble composition, not of forcing.
  So the rule, stated once and applied mechanically:

      inside the anchor hull  -> ADOPTED band = the PCHIP interpolation
      outside the anchor hull -> ADOPTED band = the UNION of the bracketing
                                 anchors' own p05-p95, with the direction of our
                                 forcing offset stated

  The interpolated value is still written (`matched_*`) as a diagnostic, never as
  the adopted band. For ssp126 the union is 6.2-15.9 cm and our forcing integral is
  10% BELOW the anchors', so the adopted band is if anything GENEROUS -- which
  matters, because the pre-flight's k <= 1.25 kill is a band-TOP test, and a
  generous band makes that kill harder to obtain, not easier.

BAND WIDTH IS NOW CONSISTENT, WHICH IT WAS NOT BEFORE
  Every adopted band is a p05-p95 of ONE ensemble. `LIT_2300_M`'s cool bands were
  already p05-p95-like (5.8-16.3 vs our extraction's 6.2-15.9) but its ssp585 band
  is a SPAN ACROSS TWO SOURCES (TC 20:309's 0-way 173 cm to TC 19:6887's ext ~313),
  so the three bands were never the same kind of interval. They are now.

THE COVERAGE CAVEAT TRAVELS WITH THE NUMBERS
  Every anchor past 2100 is NORCE-CISM. ONE ice sheet model under many climate
  forcings, so the p05-p95 is CLIMATE-forcing spread, NOT ice-sheet structural
  spread. It is a target, not a hard cut, and any scorecard quoting it must say so.

WRITES outputs/gis_matched_targets_2300.csv
  python3 python/build_gis_matched_targets.py
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))

SRC = os.path.join(REPO, "outputs/scope_gis_cool_band_targets.csv")
OUT = os.path.join(REPO, "outputs/gis_matched_targets_2300.csv")

# --- named constants ---------------------------------------------------------
PRED_PRIMARY = "gmst_int_theirs_Kyr"     # the integral arm -- the one to read
PRED_OURS = "gmst_int_ours_Kyr"
PRED_ALT = "gmst_2300_theirs"            # the 2300-level arm -- stated sensitivity
PRED_ALT_OURS = "gmst_2300_ours"
PRED_LABEL = {PRED_PRIMARY: "GSAT integral 2015-2300 (K.yr)",
              PRED_ALT: "GSAT at 2300 (K)"}
QCOLS = ["slr2300_p05_cm", "slr2300_p17_cm", "slr2300_p50_cm",
         "slr2300_p83_cm", "slr2300_p95_cm"]
BAND_LO, BAND_HI = "slr2300_p05_cm", "slr2300_p95_cm"   # what becomes (lo, hi)
SSP_LABELS = [("ssp126", "SSP1-2.6"), ("ssp245", "SSP2-4.5"), ("ssp585", "SSP5-8.5")]
SOURCE = ("PROTECT-Greenland (Goelzer 2025) doi 10.11582/2025.lf9m2wd0, "
          "NORCE-CISM long runs, control-drift-corrected, rel 2015")


def interp_log(x_anchor, y_anchor, x_at):
    """Monotone PCHIP through log(y) vs x. Returns (value, extrapolated)."""
    o = np.argsort(x_anchor)
    xs, ys = np.asarray(x_anchor)[o], np.asarray(y_anchor)[o]
    f = PchipInterpolator(xs, np.log(ys), extrapolate=True)
    return float(np.exp(f(x_at))), bool(x_at < xs[0] or x_at > xs[-1])


def main():
    t = pd.read_csv(SRC)
    print(f"anchors: {len(t)} (scenario x forcing family) from {os.path.basename(SRC)}")
    print(f"  {'anchor':22} {'int K.yr':>9} {'T2300 K':>8} " +
          "".join(f"{c.split('_')[1]:>7}" for c in QCOLS))
    for _, r in t.sort_values(PRED_PRIMARY).iterrows():
        print(f"  {r.label + ' ' + r.family:22} {r[PRED_PRIMARY]:9.0f} {r[PRED_ALT]:8.2f} " +
              "".join(f"{r[c]:7.1f}" for c in QCOLS))

    mono = t.sort_values(PRED_PRIMARY)["slr2300_p50_cm"].values
    if not np.all(np.diff(mono) > 0):
        bad = np.where(np.diff(mono) <= 0)[0]
        names = t.sort_values(PRED_PRIMARY).label.values + " " + \
                t.sort_values(PRED_PRIMARY).family.values
        print("  NON-MONOTONE p50 across anchors (carried, not smoothed): " +
              ", ".join(f"{names[i]} -> {names[i+1]}" for i in bad))

    rows = []
    for ssp, lab in SSP_LABELS:
        ours_i = float(t.loc[t.label == lab, PRED_OURS].iloc[0])
        ours_T = float(t.loc[t.label == lab, PRED_ALT_OURS].iloc[0])
        rec = {"ssp": ssp, "label": lab, "pred_int_ours_Kyr": ours_i,
               "pred_T2300_ours_C": ours_T}
        ex = False
        for c in QCOLS:
            v, e = interp_log(t[PRED_PRIMARY], t[c], ours_i)
            va, _ = interp_log(t[PRED_ALT], t[c], ours_T)
            rec[c.replace("slr2300", "matched")] = v
            rec[c.replace("slr2300", "matched_Tarm")] = va
            ex |= e
        rec["extrapolated"] = ex
        ## THE HULL RULE. Outside the hull the adopted band is the union of the
        ## bracketing anchors' own p05-p95; inside it, the interpolation.
        lo_a, hi_a = t[PRED_PRIMARY].min(), t[PRED_PRIMARY].max()
        if ours_i < lo_a:
            near = t[t[PRED_PRIMARY] <= t[t[PRED_PRIMARY] > lo_a][PRED_PRIMARY].min()]
        elif ours_i > hi_a:
            near = t[t[PRED_PRIMARY] >= t[t[PRED_PRIMARY] < hi_a][PRED_PRIMARY].max()]
        else:
            near = t.iloc[[int(np.argmin(np.abs(t[PRED_PRIMARY] - ours_i)))]]
        rec["union_anchors"] = "+".join(f"{r.label} {r.family}" for _, r in near.iterrows())
        rec["union_lo_cm"] = float(near[BAND_LO].min())
        rec["union_hi_cm"] = float(near[BAND_HI].max())
        if ex:
            rec["band_lo_cm"], rec["band_hi_cm"] = rec["union_lo_cm"], rec["union_hi_cm"]
            rec["band_rule"] = ("UNION of bracketing anchors (our predictor is "
                                f"{'below' if ours_i < lo_a else 'above'} the anchor hull "
                                f"by {abs(ours_i - (lo_a if ours_i < lo_a else hi_a)) / ours_i:.0%})")
        else:
            rec["band_lo_cm"], rec["band_hi_cm"] = rec["matched_p05_cm"], rec["matched_p95_cm"]
            rec["band_rule"] = "PCHIP interpolation at our forcing (inside the anchor hull)"
        rec["lit_lo_cm"] = 100.0 * float(t.loc[t.label == lab, "lit_lo_m"].iloc[0])
        rec["lit_hi_cm"] = 100.0 * float(t.loc[t.label == lab, "lit_hi_m"].iloc[0])
        rec["source"] = SOURCE
        rec["predictor"] = PRED_LABEL[PRED_PRIMARY]
        rows.append(rec)

    m = pd.DataFrame(rows)
    m.to_csv(OUT, index=False)

    print(f"\nMATCHED targets at OUR forcing, predictor = {PRED_LABEL[PRED_PRIMARY]}")
    print(f"  {'scenario':10} {'ours int':>9} {'MATCHED p05-p95 cm':>22} "
          f"{'p50':>7} {'T-arm p05-p95':>18} {'LIT p05-p95 cm':>18}  shift")
    for _, r in m.iterrows():
        shift = ((r.matched_p05_cm + r.matched_p95_cm) /
                 (r.lit_lo_cm + r.lit_hi_cm))
        print(f"  {r.label:10} {r.pred_int_ours_Kyr:9.0f} "
              f"{r.matched_p05_cm:10.1f}-{r.matched_p95_cm:<11.1f} {r.matched_p50_cm:7.1f} "
              f"{r.matched_Tarm_p05_cm:8.1f}-{r.matched_Tarm_p95_cm:<9.1f} "
              f"{r.lit_lo_cm:8.1f}-{r.lit_hi_cm:<9.1f} {shift:5.2f}x"
              + ("  EXTRAPOLATED" if r.extrapolated else ""))
    print(f"\n  ADOPTED band (what the scorecards import) and the rule that set it:")
    for _, r in m.iterrows():
        print(f"  {r.label:10} {r.band_lo_cm:7.1f}-{r.band_hi_cm:<7.1f} cm  "
              f"vs LIT {r.lit_lo_cm:6.1f}-{r.lit_hi_cm:<6.1f}  "
              f"[{r.band_rule}]")
    print("\n  CAVEAT, carried with every number above: every anchor past 2100 is "
          "NORCE-CISM.\n  ONE ice sheet model -- the spread is CLIMATE forcing, not "
          "ice-sheet structure.")
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
