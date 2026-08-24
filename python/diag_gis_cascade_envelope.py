"""THE CASCADE CELL-CHOICE ENVELOPE ON GREENLAND @2300 — the last unreported uncertainty.

WHAT THIS CLOSES. The tap cell is a PRIOR SPECIFICATION chosen from an admissible set,
not a fit, so the deliverable's posterior p05-p95 is not the dominant uncertainty on
tapped Greenland@2300. For the FIRST-ORDER form that was quantified and it was large:
118.0 cm, 4.4x the sampled spread, "the LARGER of the two uncertainties". When the form
moved to a 2-stage cascade (2026-08-23) the envelope was NOT re-priced, and every
handoff since has carried "UNQUANTIFIED for the cascade -- never quote the quarantined
one". This is that number.

THE SET. python/diag_gis_cascade_rate_crit.py --scan already grids 72 cascade cells at
the shipped onset (V x tau x stages in {2,3}) with a pass/fail on all four gates:
2100 inertness, both 2150 bands, the matched 2300 level, and the 2250-2300 melt rate.
16 clear everything. This reads that scan rather than re-deriving it.

⚠ THE GRID DOES NOT CONTAIN THE SHIPPED CELL, AND THAT IS NOT A DETAIL. V = 5.64 m was
SOLVED by bisection as the largest V clearing the rate band at tau = 800, n = 2; the
grid's V axis jumps 4.5 -> 6.0, so it brackets the shipped cell without containing it
(4.5 passes at 86.5 cm; 6.0 fails at 98.6). Reading the envelope off the grid alone
would report an admissible maximum of 86.5 cm for a model that ships 95.7 -- i.e. it
would place the shipped value OUTSIDE its own admissible set. The shipped cell is
therefore added explicitly as what it is: the solved upper boundary of admissibility.

CONSEQUENCE, and it is the point of the file: the envelope is NOT symmetric about the
shipped value. The shipped cell is at the TOP of the admissible range by construction,
because it was chosen as the largest V that clears. Anyone quoting +/- half the
envelope around 95.7 cm would be wrong in both directions.

WRITES outputs/diag_gis_cascade_envelope.csv
  python3 python/diag_gis_cascade_envelope.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
os.chdir(REPO)
import gis_targets  # noqa: E402

SCAN = os.path.join(REPO, "outputs/diag_gis_cascade_rate_crit_scan.csv")
DELIV = "outputs/ssps_components_2300_L14_tap4p69K_V5p64m_tau800_n2_ws.csv"
OUT = os.path.join(REPO, "outputs/diag_gis_cascade_envelope.csv")
## The shipped cell's own Greenland@2300, from the WIRED deliverable at 2000 draws --
## not from the offline grid, because that is the number that actually ships.
CELL = gis_targets.tap_cell()


def main():
    d = pd.read_csv(SCAN)
    dl = pd.read_csv(os.path.join(REPO, DELIV))
    g = dl[(dl.ssp == "SSP5-8.5") & (dl.component == "gis") & (dl.year == 2300)].iloc[0]
    shipped, sampled = float(g.med), float(g.p95 - g.p05)

    rows = []
    for label, sub in (("n=2 (shipped form)", d[d.stages == 2]),
                       ("n=2 and n=3 pooled", d)):
        a = sub[sub.all_pass]
        v = list(a.our2300)
        ## The grid's own maximum, then the same set WITH the solved boundary cell.
        for name, vals in (("grid only", v), ("grid + shipped cell", v + [shipped])):
            lo, hi = min(vals), max(vals)
            rows.append(dict(form=label, set=name, n_cells=len(vals),
                             lo_cm=lo, med_cm=float(np.median(vals)), hi_cm=hi,
                             envelope_cm=hi - lo,
                             envelope_over_sampled=(hi - lo) / sampled,
                             shipped_cm=shipped,
                             shipped_pctile=float(100.0 * np.mean(
                                 np.array(vals) <= shipped))))
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)

    print("Cascade cell-choice envelope — Greenland ssp585 @2300\n")
    print(f"  shipped cell {gis_targets.tap_cell_label()}")
    print(f"  ships at {shipped:.1f} cm, sampled p05-p95 {sampled:.2f} cm "
          f"(wired, 2000 draws)\n")
    print(f"  {'form':22}{'set':22}{'n':>4}{'min':>8}{'med':>8}{'max':>8}"
          f"{'envelope':>10}{'/sampled':>10}{'ship pct':>10}")
    for _, r in out.iterrows():
        print(f"  {r['form']:22}{r['set']:22}{r.n_cells:4d}{r.lo_cm:8.1f}"
              f"{r.med_cm:8.1f}{r.hi_cm:8.1f}{r.envelope_cm:10.1f}"
              f"{r.envelope_over_sampled:10.2f}{r.shipped_pctile:9.0f}%")

    hdr = out[(out.form == "n=2 (shipped form)") & (out.set == "grid + shipped cell")]
    r = hdr.iloc[0]
    print(f"\n  HEADLINE (shipped form, boundary cell included):")
    print(f"    envelope {r.envelope_cm:.1f} cm = {r.envelope_cm/100:.2f} m, "
          f"{r.envelope_over_sampled:.2f}x the sampled p05-p95")
    print(f"    range {r.lo_cm:.1f}-{r.hi_cm:.1f} cm; the shipped value is the "
          f"MAXIMUM ({r.shipped_pctile:.0f}th pctile)")
    print(f"    admissible MEDIAN is {r.med_cm:.1f} cm — the shipped cell is "
          f"{shipped/r.med_cm:.2f}x it")
    print(f"\n  vs the FIRST-ORDER predecessor: 118.0 cm = 4.4x sampled.")
    print(f"  The cascade envelope is {118.0/r.envelope_cm:.1f}x SMALLER in cm and "
          f"drops from the\n  larger of the two uncertainties to roughly the size of "
          f"the sampled one.")
    print(f"\n  ⚠ REPORT IT ONE-SIDED. The shipped cell was chosen as the largest V "
          f"clearing the\n    rate band, so it sits at the TOP of the admissible "
          f"range BY CONSTRUCTION. The\n    cell-choice uncertainty on Greenland@2300 "
          f"runs DOWNWARD from {shipped:.1f} cm, to\n    {r.lo_cm:.1f} cm. A symmetric "
          f"+/- band around the shipped value is wrong both ways.")
    print(f"\n  ⚠ OFFLINE vs WIRED. The set's values are the offline emulator's; the "
          f"shipped\n    value is the wired deliverable's. The port was measured at "
          f"0.4% on the cell,\n    which is far below the envelope, but they are not "
          f"the same code path.")
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
