#!/usr/bin/env python3
"""
DIAGNOSTIC — the two hindcast arms do NOT treat land-water storage the same way, and the
TOTAL row of the L24 comparison is substantially a consequence of that.

Found 2026-09-10 from Marcus's question "why isn't there a BRICK dashed line in Figure 1e?".

THE ANSWER TO THAT QUESTION is mundane: `plot_hindcast_components.py` maps BRK_COL["lws"]=None
and LAD_COL["lws"]=None, and neither postpred CSV carries an lws column. Panel 1e is
observations-only for both arms.

⛔⛔ WHAT IT EXPOSES IS NOT MUNDANE. The two arms build their TOTAL from different LWS:
    Ladrillo (posterior_predictive_ladrillo.jl:175)  tot = ... + lws_OBS      <- the OBSERVED series
    BRICK 2.0 (posterior_predictive_oldbrick.jl:73)  total = ... + lws        <- BRICK'S OWN
and BRICK's own LWS is IDENTICALLY ZERO until 2019 by MimiBRICK calibration design (Wong's CW11
target had LWS removed before fitting). Measured directly, not inferred:
`julia/diag_brick_lws_extract.jl` gives 0.0000 at 1900/1950/2000/2015/2018 across 20 draws, first
nonzero 2019, +0.19 cm by 2024.

⇒ the Dangendorf total target INCLUDES LWS. Ladrillo is handed the observed value, so it cannot
get LWS wrong. BRICK is handed zero, so it carries the full omission as error. The observed LWS
anomaly is +1.57 cm at 1900 on the 1995-2005 baseline (20th-century impoundment), so this is a
~1.5 cm systematic head start at the early end of the record — the era where the deliverable
claims Ladrillo's largest gain.

This is the apples-to-oranges the `mimibrick-quirks` skill (item 6) warns about, and its remedy:
"add a Wada-style post-hoc LWS correction to BRICK historical, or subtract a Frederikse 2020 LWS
series from the obs." Our pipeline applies the remedy to ONE arm.

⭐ RULED AND IMPLEMENTED 2026-09-10 (Marcus): BRICK now takes the OBSERVED LWS at source, in
`posterior_predictive_oldbrick.jl`, so both arms are on one convention and every consumer inherits
it. ⛔ THAT MAKES THE COMPARISON BELOW SELF-REFERENTIAL — `postpred_oldbrick...csv` is now the
CORRECTED arm, so "as built" and "with obs LWS" would be the same series and the script would
report a null difference against itself ([[gate_reads_its_own_output]]).
⇒ this script is now a REGRESSION TEST, not a proposal: it asserts the convention is live, by
checking that BRICK's implied LWS tracks the observed series. The sizes the decision rested on are
in the 2026-09-10 commit and in memory [[lws_convention_asymmetry]]; they are NOT recomputed here,
because the arm they measured no longer exists on disk.
⚠ Only the TOTAL is affected — LWS enters no component, so the AIS/GIS/glacier/TE rows stand.
⚠ Pre-2019 the correction is EXACT (BRICK's LWS is exactly 0). Over 1993-2026 it interpolates the
measured 2019-2026 ramp, so that window alone carries a small approximation.

WRITES only outputs/. Reports only.
"""
import os
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from provenance import stamp

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
## --tag= (default L24, the vintage this was first run on); a literal tag here reported L24 under any name (09-20).
TAG = next((a[len("--tag="):] for a in sys.argv[1:] if a.startswith("--tag=")), "L24")
OUT_CSV = os.path.join(REPO, "outputs", f"diag_lws_convention_asymmetry_{TAG}.csv")
BRK = os.path.join(REPO, "outputs", "postpred_oldbrick_components_timeseries.csv")
LAD = os.path.join(REPO, "outputs", f"postpred_{TAG}_components_timeseries.csv")
TGT = os.path.join(REPO, "outputs", "recalib_targets_ext.csv")

# BRICK's OWN LWS, cm rel 1995-2005, MEASURED by julia/diag_brick_lws_extract.jl (identical
# across 20 draws — the LWS sample is drawn once at get_model under the 2026 seed).
BRICK_LWS_MEASURED = {2018: 0.0, 2019: 0.0439, 2020: 0.0982, 2024: 0.1892, 2026: 0.2556}
BRICK_LWS_ZERO_THROUGH = 2018
WINDOWS = {"1900-1919": (1900, 1919), "1920-1949": (1920, 1949), "1950-1992": (1950, 1992),
           "1993-2026": (1993, 2026), "full": (1900, 2026)}
CUM = ((1900, 1904), (2020, 2024))
LVL = (2022, 2024)


def wmean(s, a, b):
    yy = [y for y in range(a, b + 1) if y in s.index and np.isfinite(s.get(y, np.nan))]
    return s.loc[yy].mean()


def main():
    B = pd.read_csv(BRK).set_index("year")
    L = pd.read_csv(LAD).set_index("year")
    T = pd.read_csv(TGT).set_index("year")
    obs_lws = T["lws"].reindex(B.index)

    print("=" * 78)
    print("REGRESSION TEST: both hindcast arms carry the OBSERVED land-water storage")
    print("=" * 78)
    imp_b = B["total_p50"] - (B["ais_p50"] + B["gsic_p50"] + B["gis_p50"] + B["te_p50"])
    imp_l = L["total_p50"] - (L["ais_p50"] + L["glaciers_p50"] + L["gis_p50"] + L["te_p50"])
    print(f"  {'year':>6} {'BRICK implied lws':>18} {'Ladrillo implied lws':>21} {'obs lws':>9}")
    rows, worst = [], 0.0
    for y in (1900, 1950, 2000, 2018, 2024):
        o = float(obs_lws[y])
        print(f"  {y:>6} {imp_b[y]:18.3f} {imp_l[y]:21.3f} {o:9.3f}")
        worst = max(worst, abs(imp_b[y] - o))
        rows.append(dict(year=y, brick_implied_lws=imp_b[y], ladrillo_implied_lws=imp_l[y],
                         obs_lws=o))
    # ⚠ implied != obs exactly: total_p50 is the quantile of the SUM, not the sum of quantiles.
    # The bound is scaled to that spread, not typed to a round number.
    tol = 0.15 * float(obs_lws.loc[1900:2024].abs().max())
    print(f"\n  [GATE LWS CONVENTION] max |BRICK implied lws - obs lws| = {worst:.3f} cm "
          f"against a tolerance of {tol:.3f}")
    print("    (tolerance = 15% of the observed LWS range, not a typed constant; the residual is "
          "the\n     quantile-of-sum vs sum-of-quantiles gap, which no exact test can remove)")
    if worst > tol:
        raise SystemExit("[GATE LWS CONVENTION] FAILED - BRICK's total does not track the "
                         "observed LWS. The arms are back on different conventions.")
    print("    => PASS. Both arms are on one LWS convention.")

    stamp(pd.DataFrame(rows), __file__, tag=TAG,
          inputs={"brick": BRK, "ladrillo": LAD, "targets": TGT},
          extra="cm rel 1995-2005; regression test of the shared LWS convention"
          ).to_csv(OUT_CSV, index=False)
    print(f"\n[wrote] {os.path.relpath(OUT_CSV, REPO)}")


if __name__ == "__main__":
    main()
