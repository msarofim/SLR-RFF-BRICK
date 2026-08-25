#!/usr/bin/env python3
"""
scope_gis_ssp126_acceptability.py — CAN THE GREENLAND ssp126@2100 SPREAD BE LEFT AS AN
                                    ACCEPTABLE MISS? A decision, with the one question the
                                    pricing never asked: WHICH SIDE of the band is missing.

STATE OF PLAY (`diag_gis_width_anatomy.py`, `bbee082`; addendum 2 of handoff -25c). The
Greenland width deficit survived every attempt to explain it away: it is unimodal (so the
bimodality guard that retracted the ssp126 AIS defect does not apply), it is not our climate
ensemble (thermal expansion is the control at 94-96% forcing and is FLAT across scenarios
while GIS grades 1.9x), and after crediting the out-of-scope ISM structural term at its
LARGER range-based sigma it still misses by 2.30 cm. It was PARKED at "+3.9% of one band",
with the measurement left on record so it could be picked up cheaply.

Marcus, 2026-08-25: *"Evaluate whether we can leave the Greenland ssp126 spread as an
acceptable miss."* This script is that evaluation. It adds three things the pricing did not
have, and each can change the answer:

  [A] THE TWO DELIVERABLES DISAGREED ABOUT emuGrIS, AND NOBODY HAD NOTICED. (FIXED in the
      same change; [A] is now the regression check that they still agree.)
      `benchmark/comparator_classes.csv` deliberately keeps emuGrIS in `model` -- its header
      argues that separating it "needs a receipt" -- so the benchmark scores this cell
      against n=3 (median 9.57 cm) and reports 0.489x. `diag_gis_width_anatomy.py` labels
      emuGrIS "structural" and scores against n=2 (median 8.32 cm), reporting 0.563x. Same
      cell, same draws, two numbers in two committed deliverables. An acceptability decision
      cannot be made on a quantity that is 0.489 in one file and 0.563 in another.

  [B] WHICH SIDE IS MISSING -- never asked, and it is the question that matters.
      A p05-p95 at 0.56x can be missing width BELOW the median (harmless for a risk
      deliverable: it would mean we are over-confident about how LITTLE Greenland does) or
      ABOVE it (consequential: we would be understating the upper tail everything downstream
      is bought to bound). The pricing treated the band as one number. Half-widths separate
      them, and no new model run is needed -- the draws are on disk.

  [C] THE PRICE IN THE UNITS ACTUALLY REPORTED, not band width. What moves in the p95 of the
      TOTAL at this cell -- the number a reader quotes -- if the missing Greenland width is
      restored.

⚠ THIS SCRIPT PROPOSES NO FIX AND RUNS NO MODEL. Greenland is a CLOSED module; reopening it
is a decision, and the point of the exercise is to decide with the price in hand rather than
to start work because a cell is red.

    source ~/climate-env/bin/activate
    python python/scope_gis_ssp126_acceptability.py [--tag=L14]
Reads   outputs/scope_slr_fairunc_draws_<ssp>_spliced_<TAG>.csv
        benchmark/reference/_fixed/literature_rows.csv, benchmark/comparator_classes.csv
        outputs/diag_gis_width_anatomy_<TAG>.csv, outputs/bench_ladrillo_<TAG>.csv
Writes  outputs/scope_gis_ssp126_acceptability_<TAG>.csv
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = next((a[len("--tag="):] for a in sys.argv[1:] if a.startswith("--tag=")), "L14")
OUT = os.path.join(REPO, "outputs", f"scope_gis_ssp126_acceptability_{TAG}.csv")
LIT = os.path.join(REPO, "benchmark", "reference", "_fixed", "literature_rows.csv")
CLASSES = os.path.join(REPO, "benchmark", "comparator_classes.csv")
ANATOMY = os.path.join(REPO, "outputs", f"diag_gis_width_anatomy_{TAG}.csv")
BENCH = os.path.join(REPO, "outputs", f"bench_ladrillo_{TAG}.csv")
DRAWS = os.path.join(REPO, "outputs", "scope_slr_fairunc_draws_{ssp}_spliced_" + TAG + ".csv")

# THE CELL UNDER DECISION -- every label derives from these.
CELL_SSP, CELL_YEAR = "ssp126", 2100
CELL = f"{CELL_SSP}@{CELL_YEAR}"
COMPONENT = "gis"
ARM = "joint"                       # the reported band since 2026-08-25
QLO, QHI = 5, 95                    # the benchmark's spread definition
# The comparator set, read from the file that OWNS the classification. [A] then checks that
# the width-anatomy diagnostic agrees with it -- it did not until this change.
SET_BENCH = ["FittedISMIP", "emuGrIS", "Nauels2025"]     # comparator_classes: all `model`
# ACCEPTANCE CRITERION, stated BEFORE the numbers so it cannot be fitted to them.
# A width miss is acceptable if restoring it moves the reported TOTAL p95 at this cell by
# less than this, AND the missing width is not concentrated in the upper half (which is the
# side a risk deliverable is bought to bound).
ACCEPT_P95_MOVE_PCT = 5.0
ACCEPT_UPPER_SHARE = 0.60

rows = []


def emit(**kw):
    rows.append(kw)


def main():
    lit = pd.read_csv(LIT)
    lit["year"] = lit.year.astype(int)
    cell = lit[(lit.component == COMPONENT) & (lit.scenario == CELL_SSP) &
               (lit.year == CELL_YEAR)].set_index("module")
    d = pd.read_csv(DRAWS.format(ssp=CELL_SSP))
    d = d[(d.horizon == CELL_YEAR) & (d.arm == ARM)]
    gis = d[d.component == COMPONENT].value_cm.values
    tot = d[d.component == "total"].value_cm.values

    print("=" * 100)
    print(f"GREENLAND {CELL} SPREAD — ACCEPTABLE MISS? (tag {TAG}, {ARM} band, n={len(gis)} draws)")
    print("=" * 100)

    # ------------------------------------------- [A] the classification the two files split on
    ours = np.percentile(gis, QHI) - np.percentile(gis, QLO)
    print(f"\n[A] THE COMPARATORS, AND WHETHER THE TWO DELIVERABLES AGREE. ours = {ours:.2f} cm")
    print(f"\n{'comparator':14s} {'spread':>8s}  {'ours/theirs':>11s}")
    for m in SET_BENCH:
        sp = float(cell.loc[m, "p95"]) - float(cell.loc[m, "p05"])
        print(f"{m:14s} {sp:8.2f}  {ours/sp:11.3f}")
        emit(block="A", quantity=f"ours/{m}", value=ours / sp, unit="x",
             note=f"theirs {sp:.2f} cm; classified `model` in comparator_classes.csv",
             verdict="")
    med_b = float(np.median([float(cell.loc[m, "p95"]) - float(cell.loc[m, "p05"])
                             for m in SET_BENCH]))
    bench = pd.read_csv(BENCH)
    b_row = bench[(bench.block == "P") & (bench.component == COMPONENT) &
                  (bench.scenario == CELL_SSP) & (bench.horizon == CELL_YEAR) &
                  (bench.metric == "spread_vs_lit")]
    b_val = float(b_row.value.iloc[0])
    an = pd.read_csv(ANATOMY)
    a_row = an[(an.ssp == CELL_SSP) & (an.horizon == CELL_YEAR) &
               (an.key == "vs_like_for_like")]
    a_val = float(a_row.value.iloc[0])
    print(f"\n    comparator median of n={len(SET_BENCH)}: {med_b:5.2f} cm  =>  ours/median = "
          f"{ours/med_b:.3f}x   ({b_row.verdict.iloc[0]})")
    print(f"\n    AGREEMENT CHECK — the same cell as reported by each committed deliverable:")
    print(f"      bench_ladrillo   spread_vs_lit      {b_val:.3f}x")
    print(f"      width_anatomy    vs_like_for_like   {a_val:.3f}x")
    agree = abs(b_val - a_val) < 1e-3
    print(f"      => {'AGREE' if agree else 'DISAGREE by %.3fx' % abs(b_val - a_val)}"
          + ("" if agree else "  ⚠ one of them is scoring against a line the repo did not draw"))
    print(f"\n    ⚠ THEY DID NOT AGREE UNTIL 2026-08-25. `diag_gis_width_anatomy.py` declared its"
          f"\n      own LIKE_FOR_LIKE/STRUCTURAL sets with emuGrIS as 'structural', giving 0.563x,"
          f"\n      while the benchmark -- which OWNS the classification and whose header argues"
          f"\n      that separating emuGrIS 'needs a receipt' -- gave 0.489x. THE PARK DECISION WAS"
          f"\n      TAKEN ON THE MORE FORGIVING NUMBER. The anatomy now reads"
          f"\n      `benchmark/comparator_classes.csv`; this block is the regression check.")
    emit(block="A", quantity="deliverable agreement (bench vs anatomy)", value=b_val - a_val,
         unit="x", note=f"bench {b_val:.3f}x, anatomy {a_val:.3f}x; both must score the same cell "
                        f"against the same classification",
         verdict="AGREE" if agree else "DISAGREE")

    # -------------------------------------------------- [B] which side of the band is missing
    lo, mid, hi = (np.percentile(gis, QLO), np.percentile(gis, 50), np.percentile(gis, QHI))
    print(f"\n[B] WHICH SIDE IS MISSING? ours: p{QLO} {lo:.2f} / p50 {mid:.2f} / p{QHI} {hi:.2f} cm")
    print(f"\n{'comparator':14s} {'lower half':>11s} {'upper half':>11s} | "
          f"{'ours/theirs lo':>14s} {'ours/theirs hi':>14s}")
    o_lo, o_hi = mid - lo, hi - mid
    shares = []
    for m in SET_BENCH:
        t_med = float(cell.loc[m, "med"])
        t_lo, t_hi = t_med - float(cell.loc[m, "p05"]), float(cell.loc[m, "p95"]) - t_med
        print(f"{m:14s} {t_lo:11.2f} {t_hi:11.2f} | {o_lo/t_lo:14.3f} {o_hi/t_hi:14.3f}")
        gap_lo, gap_hi = max(t_lo - o_lo, 0.0), max(t_hi - o_hi, 0.0)
        shares.append(gap_hi / (gap_lo + gap_hi) if (gap_lo + gap_hi) > 0 else np.nan)
        emit(block="B", quantity=f"half-widths vs {m}", value=o_hi / t_hi, unit="x upper",
             note=f"ours lo {o_lo:.2f} hi {o_hi:.2f}; theirs lo {t_lo:.2f} hi {t_hi:.2f}; "
                  f"missing width is {100*shares[-1]:.0f}% upper-side", verdict="")
    up_share = float(np.nanmedian(shares))
    print(f"\n    ours: lower half {o_lo:.2f} cm, upper half {o_hi:.2f} cm "
          f"(ratio {o_hi/o_lo:.2f}, a comparator median of {np.median([(float(cell.loc[m,'p95'])-float(cell.loc[m,'med']))/(float(cell.loc[m,'med'])-float(cell.loc[m,'p05'])) for m in SET_BENCH]):.2f})")
    print(f"    => {100*up_share:.0f}% of the missing width is on the UPPER side "
          f"(criterion: acceptable below {100*ACCEPT_UPPER_SHARE:.0f}%)")
    emit(block="B", quantity="upper-side share of the missing width", value=up_share,
         unit="fraction", note=f"criterion {ACCEPT_UPPER_SHARE}",
         verdict="ACCEPTABLE" if up_share < ACCEPT_UPPER_SHARE else "CONSEQUENTIAL")

    # ------------------------------------------ [C] the price in the units actually reported
    gap = med_b - ours
    print(f"\n[C] THE PRICE IN THE UNITS A READER QUOTES — the TOTAL p{QHI} at {CELL}")
    print(f"\n    GIS full-band gap vs the benchmark's comparator median: {gap:.2f} cm")
    t_lo, t_mid, t_hi = (np.percentile(tot, QLO), np.percentile(tot, 50),
                         np.percentile(tot, QHI))
    # ⚠ THE FIRST VERSION OF THIS BLOCK WAS WRONG AND ITS OUTPUT SAID SO: it converted the
    # total's p05-p95 to a SYMMETRIC sigma, added the gap in quadrature and rebuilt the
    # percentiles -- and reported the p95 moving DOWN by 7.7% when width was ADDED. Adding
    # width cannot lower an upper percentile (`implausible result = bug`). The cause is that
    # the total at this cell is strongly SKEWED (upper half 16.50 cm against a lower half of
    # 7.82), so a symmetric reconstruction throws away most of the upper tail before adding
    # anything back. The fix is to work on the UPPER HALF-WIDTH directly, which preserves the
    # skew and can only increase.
    t_up, t_dn = t_hi - t_mid, t_mid - t_lo
    g_up = max(float(np.median([float(cell.loc[m, "p95"]) - float(cell.loc[m, "med"])
                                for m in SET_BENCH])) - o_hi, 0.0)
    g_dn = max(float(np.median([float(cell.loc[m, "med"]) - float(cell.loc[m, "p05"])
                                for m in SET_BENCH])) - o_lo, 0.0)
    # Independence is the right default: the missing width would come from Greenland's OWN
    # parameters, which the sampler makes independent of the other components
    # (`diag_gis_width_anatomy` [D]). The perfectly-correlated arm is the upper bound.
    up_new = float(np.hypot(t_up, g_up))
    up_corr = t_up + g_up
    p95_new, p95_corr = t_mid + up_new, t_mid + up_corr
    move = 100 * (p95_new - t_hi) / t_hi
    move_corr = 100 * (p95_corr - t_hi) / t_hi
    print(f"    GIS missing half-widths vs the benchmark's comparator median: "
          f"upper {g_up:.2f} cm, lower {g_dn:.2f} cm")
    print(f"    total now:  p{QLO} {t_lo:.2f}  p50 {t_mid:.2f}  p{QHI} {t_hi:.2f} cm "
          f"(upper half {t_up:.2f}, lower half {t_dn:.2f} -- SKEWED, so half-widths are "
          f"composed, not a symmetric sigma)")
    print(f"    with the GIS upper width restored: p{QHI} {p95_new:.2f} cm (independent) / "
          f"{p95_corr:.2f} cm (perfectly correlated)")
    print(f"    => the reported upper bound moves {move:+.1f}% (independent) / "
          f"{move_corr:+.1f}% (correlated)")
    print(f"       criterion: acceptable below {ACCEPT_P95_MOVE_PCT:.0f}% on the INDEPENDENT arm")
    emit(block="C", quantity=f"total p{QHI} move if GIS upper width restored", value=move,
         unit="%", note=f"{t_hi:.2f} -> {p95_new:.2f} cm independent / {p95_corr:.2f} cm "
                        f"correlated ({move_corr:+.1f}%); GIS upper gap {g_up:.2f} cm; "
                        f"composed on HALF-WIDTHS because the total is skewed "
                        f"({t_up:.2f} up vs {t_dn:.2f} down)",
         verdict="ACCEPTABLE" if abs(move) < ACCEPT_P95_MOVE_PCT else "CONSEQUENTIAL")

    # ------------------------------------------------------------------ [D] the decision
    ok_side = up_share < ACCEPT_UPPER_SHARE
    ok_price = abs(move) < ACCEPT_P95_MOVE_PCT
    print("\n" + "=" * 100)
    print("DECISION")
    print("=" * 100)
    print(f"""
  criterion 1 -- WHICH SIDE:  {100*up_share:.0f}% upper vs a {100*ACCEPT_UPPER_SHARE:.0f}% bar   => {'PASS' if ok_side else 'FAIL'}
  criterion 2 -- THE PRICE :  {move:+.1f}% on the reported total p{QHI} vs a {ACCEPT_P95_MOVE_PCT:.0f}% bar  => {'PASS' if ok_price else 'FAIL'}
                              ({move_corr:+.1f}% on the perfectly-correlated upper bound)

  ⚠ BOTH CRITERIA WERE FIXED IN THE SOURCE BEFORE THE NUMBERS WERE COMPUTED
    (ACCEPT_UPPER_SHARE, ACCEPT_P95_MOVE_PCT at the top of this file), so the decision is
    not fitted to the answer. Change them by editing them, in a commit that says why.

  ⚠ [A] WAS A DEFECT IN ITS OWN RIGHT AND IS FIXED IN THIS CHANGE. Two committed
    deliverables reported 0.489x and 0.563x for this cell, and the earlier PARK decision
    was taken on the more forgiving of the two. `diag_gis_width_anatomy.py` now reads the
    benchmark's classification file instead of declaring its own.

  ⚠ AND RE-RUNNING THE ANATOMY SURFACED A SECOND STALENESS. Its 2150 row was computed
    BEFORE MAGICC was re-extracted to 2300 (`6c6acd4`), so it had one comparator at that
    horizon instead of two. Addendum 2's "the deficit vanishes at ssp585" holds at
    ssp585@2100 (0.92x) but NOT at ssp585@2150, which is 0.46x with MAGICC in -- the
    benchmark already said so; the diagnostic had not been re-run.""")
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
