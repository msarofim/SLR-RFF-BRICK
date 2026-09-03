#!/usr/bin/env python3
"""verify_magicc_regrowth_attribution.py -- split the MAGICC-vs-Ladrillo GLACIER REGROWTH
gap into a MODULE-STRUCTURE part and a CLIMATE-DRIVER part.

  python3 python/verify_magicc_regrowth_attribution.py [--tag=L24] [--forcing=spliced]

Writes outputs/verify_magicc_regrowth_attribution_<TAG>.csv
SCOPING/VERIFICATION ONLY: reads shipped arm files, runs no model.

THE QUESTION (Marcus, 2026-09-03). The deliverable states that MAGICC regrows substantially
more glacier ice than Ladrillo and that "about 3/4 of that is model structure and 1/4 the
climate module." That sentence had no receipt. Marcus's stated intent for the split is:

    compare (MAGICC vs FaIR-driven Ladrillo) against (MAGICC vs MAGICC-driven Ladrillo)

which is exactly the decomposition below -- but computed on REGROWTH, not on level and not
on equilibrium. Which quantity you use changes the answer, so this script computes the one
the sentence is about and says so.

⚠ THREE DIFFERENT QUANTITIES GIVE THREE DIFFERENT ANSWERS. Do not quote one for another:
  * REGROWTH (this script)            -- peak-to-2300 drawdown. What "regrows" means.
  * LEVEL   (scope_ladrillo_on_magicc_climate.py) -- cm at a horizon. Confounds how much
    melted in the first place with how much came back; gives ~50/50 at vvLN.
  * EQUILIBRIUM (verify_ladrillo_vs_magicc_equilibrium.py) -- the committed target S_eq,
    not what is realised. Gives a 5-10% structure share on the in-domain markers.

THE THREE ARMS, identical posterior/tap/draws across the two Ladrillo ones; only the climate
driving them changes (the reverse arm -- MAGICC-SLR on FaIR's climate -- is IMPOSSIBLE, not
merely unbuilt: MAGICC-SLR consumes MAGICC's own climate module).

    A  ladrillo_fair      Ladrillo on FaIR's climate      the shipped deliverable arm
    B  ladrillo_magicc    Ladrillo on MAGICC's climate    one axis swapped
    C  magicc_own         MAGICC-SLR's own reported value both axes

    total gap      = C - A      the gap as quoted all along
    structure part = C - B      what survives once the climate difference is removed
    climate part   = B - A      what the climate swap alone buys
    structure_share = (C - B) / (C - A)

⚠ THE DENOMINATOR CAN BE NEAR ZERO, and then the share is meaningless, not large
(`curvature_needs_an_error_bar`'s near-zero-denominator case). A marker whose total gap is
below GAP_FLOOR_CM reports share = NaN and verdict NO_GAP rather than a ratio.

⚠ THIS IS A MEDIAN-TRAJECTORY STATISTIC, not the median of a per-draw statistic. The shipped
paths files carry med/p05/p95 only, so peak-to-2300 is measured on the median path. Peak-of-
median is not median-of-peak; the two differ whenever the peak YEAR varies across draws. Say
which one a number is when quoting it.

⚠ REGROWTH IS ONLY DEFINED WHERE THE PATH TURNS. A marker still rising at 2300 has no peak
inside the horizon and reports regrowth 0.0 with verdict NO_DECLINE -- it is not evidence of
a module that cannot regrow, only of a scenario that never asks it to.
"""
import argparse
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTD = os.path.join(REPO, "outputs")
MAGICC_MED = os.path.join(REPO, "data/comparison/magicc_nauels_components_vv.csv")

## THE ARM. The tapped file is the shipped deliverable arm; the tap does not touch glaciers
## but mixing arms across the three columns would not be like-for-like on anything else.
TAP_SUFFIX = "_tap4p69K_V5p64m_tau800"
COMPONENT = "glaciers"
LADRILLO_ARM = "joint"          # posterior x FaIR-forcing, the width-comparable band
END_YEAR = 2300
MIN_YEAR = 2000                 # ignore the hindcast; the peak of interest is projected
GAP_FLOOR_CM = 0.25             # below this the share is NaN, not a ratio
VV = ["vvVL", "vvLN", "vvL", "vvML", "vvM", "vvHL", "vvH"]


def _peak_to_end(year, val):
    """Regrowth on one median path: max within [MIN_YEAR, END_YEAR] minus the END_YEAR value.

    Returns (regrowth_cm, peak_year, peak_cm, end_cm). Regrowth is >= 0 by construction; a
    path still rising at END_YEAR peaks AT END_YEAR and returns exactly 0.0."""
    m = (year >= MIN_YEAR) & (year <= END_YEAR)
    year, val = np.asarray(year)[m], np.asarray(val)[m]
    if not len(year) or END_YEAR not in set(year):
        return None
    i = int(np.argmax(val))
    end = float(val[year == END_YEAR][0])
    return float(val[i] - end), int(year[i]), float(val[i]), end


def ladrillo_path(marker, tag, forcing, climate):
    """Median glacier path for one Ladrillo arm. climate is 'fair' or 'magicc'."""
    clim = "" if climate == "fair" else "_magiccclim"
    p = os.path.join(OUTD, "scope_slr_fairunc_paths_%s_%s%s_%s%s.csv"
                     % (marker, forcing, clim, tag, TAP_SUFFIX))
    if not os.path.exists(p):
        return None, os.path.basename(p)
    d = pd.read_csv(p)
    d = d[(d.component == COMPONENT) & (d.arm == LADRILLO_ARM)].sort_values("year")
    if not len(d):
        return None, os.path.basename(p) + " (no %s/%s rows)" % (COMPONENT, LADRILLO_ARM)
    return _peak_to_end(d.year.values, d.med_cm.values), os.path.basename(p)


def magicc_path(marker):
    d = pd.read_csv(MAGICC_MED)
    d = d[(d.scenario == marker) & (d.component == COMPONENT)].sort_values("year")
    if not len(d):
        return None
    return _peak_to_end(d.year.values, d.med.values)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="L24")
    ap.add_argument("--forcing", default="spliced", choices=["spliced", "raw"])
    a = ap.parse_args()

    rows, missing = [], []
    for mk in VV:
        A, pa = ladrillo_path(mk, a.tag, a.forcing, "fair")
        B, pb = ladrillo_path(mk, a.tag, a.forcing, "magicc")
        C = magicc_path(mk)
        if A is None or B is None or C is None:
            missing.append((mk, pa if A is None else pb if B is None else "MAGICC " + mk))
            continue
        (ra, ya, _, _), (rb, yb, _, _), (rc, yc, _, _) = A, B, C
        total, struct, clim = rc - ra, rc - rb, rb - ra
        if abs(total) < GAP_FLOOR_CM:
            share, verdict = np.nan, "NO_GAP"
        elif ya == END_YEAR and yb == END_YEAR and yc == END_YEAR:
            share, verdict = np.nan, "NO_DECLINE"
        else:
            share = struct / total
            verdict = ("STRUCTURE" if share >= 0.6 else
                       "CLIMATE" if share <= 0.4 else "BOTH")
        rows.append(dict(tag=a.tag, forcing=a.forcing, marker=mk,
                         ladrillo_fair_regrowth_cm=ra, ladrillo_fair_peak_year=ya,
                         ladrillo_magiccclim_regrowth_cm=rb, ladrillo_magiccclim_peak_year=yb,
                         magicc_own_regrowth_cm=rc, magicc_own_peak_year=yc,
                         total_gap_cm=total, structure_part_cm=struct, climate_part_cm=clim,
                         structure_share=share, verdict=verdict))

    if missing:
        for mk, p in missing:
            print("[MISSING] %-6s %s" % (mk, p))
    if not rows:
        raise SystemExit("[FATAL] no marker had all three arms")

    df = pd.DataFrame(rows)
    hdr = ("GLACIER REGROWTH ATTRIBUTION -- %s, %s forcing, %s arm, median path, "
           "peak->%d" % (a.tag, a.forcing, LADRILLO_ARM, END_YEAR))
    print("\n" + "=" * 104 + "\n" + hdr + "\n" + "=" * 104)
    print("  regrowth cm = max(median path, %d-%d) - value(%d)\n" % (MIN_YEAR, END_YEAR, END_YEAR))
    print("  %-6s %10s %10s %10s | %9s %9s %9s %7s  %s"
          % ("marker", "Lad/FaIR", "Lad/MAGcl", "MAGICC", "total", "struct", "climate",
             "share", "verdict"))
    for _, r in df.iterrows():
        print("  %-6s %10.3f %10.3f %10.3f | %9.3f %9.3f %9.3f %7s  %s"
              % (r.marker, r.ladrillo_fair_regrowth_cm, r.ladrillo_magiccclim_regrowth_cm,
                 r.magicc_own_regrowth_cm, r.total_gap_cm, r.structure_part_cm,
                 r.climate_part_cm,
                 "  n/a" if not np.isfinite(r.structure_share) else "%6.3f" % r.structure_share,
                 r.verdict))

    ok = df[np.isfinite(df.structure_share)]
    if len(ok):
        w = ok.structure_part_cm.sum() / ok.total_gap_cm.sum()
        print("\n  POOLED over the %d marker(s) with a real gap: structure %.1f%% / climate "
              "%.1f%%" % (len(ok), 100 * w, 100 * (1 - w)))
        print("  (pooled = sum(struct)/sum(total), NOT the mean of per-marker shares -- a "
              "marker with a\n   tiny gap must not weigh the same as one with a large one.)")
    else:
        print("\n  NO marker has a gap above GAP_FLOOR_CM=%.2f; no share is defined."
              % GAP_FLOOR_CM)

    out = os.path.join(OUTD, "verify_magicc_regrowth_attribution_%s.csv" % a.tag)
    df.to_csv(out, index=False)
    print("\nwrote %s" % os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
