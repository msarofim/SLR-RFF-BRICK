#!/usr/bin/env python3
"""
DIAGNOSTIC — why Ladrillo beats BRICK 2.0 on every component in the early windows and still
loses on the total.

The question is the obvious one to ask of the deliverable's RMSE table, and the answer is
COMPENSATING ERRORS, not a defect in either arm's total:

  BRICK 2.0's component errors are LARGE and MIXED IN SIGN, so they cancel in the sum.
  Ladrillo's are SMALL but nearly all the SAME SIGN, so they accumulate essentially undiminished.

Over 1900-1919, BRICK's Antarctic undershoot (-2.90 cm) very nearly cancels its glacier overshoot
(+3.28), leaving a signed sum of +0.62 from 7.57 cm of absolute error -- 92% cancellation.
Ladrillo's four biases sum to +1.95 from 1.97 cm of absolute error -- 1% cancellation. So the arm
that is closer on every component is further away on their sum.

⚠ THIS IS NOT AN ARTEFACT OF THE TOTAL'S CONSTRUCTION. The observational budget's own
non-closure -- (sum of component targets + lws) - total target -- is a COMMON additive term,
identical for both arms, and it is small in these windows (-0.31 cm over 1900-1919, +0.17 over
1920-1949). It cannot explain a difference between the arms.

⚠ The signed component sum does NOT reproduce each arm's total residual exactly (~0.5 cm at
1900-1919). Two reasons, both structural and both reported rather than hidden: `total_p50` is the
quantile of the SUM, not the sum of the quantiles; and Ladrillo's total carries the glacier series
WITH the uncharted-ice term while the `glaciers_p50` column is the hindcast-scope series. The
cancellation result does not rest on that gap -- it is measured on the component biases directly.

WRITES only outputs/. Reports only.
"""
import os
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from provenance import stamp

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG  = "L24"
TGT  = os.path.join(REPO, "outputs", "recalib_targets_ext.csv")
LAD  = os.path.join(REPO, "outputs", f"postpred_{TAG}_components_timeseries.csv")
BRK  = os.path.join(REPO, "outputs", "postpred_oldbrick_components_timeseries.csv")
OUT_CSV = os.path.join(REPO, "outputs", "diag_component_error_cancellation.csv")

LAD_COL = {"ais": "ais_p50", "gsic": "glaciers_p50", "gis": "gis_p50", "steric": "te_p50"}
BRK_COL = {"ais": "ais_p50", "gsic": "gsic_p50", "gis": "gis_p50", "steric": "te_p50"}
WINDOWS = [(1900, 1919), (1920, 1949), (1950, 1992), (1993, 2026)]


def main():
    T = pd.read_csv(TGT).set_index("year")
    L = pd.read_csv(LAD).set_index("year")
    B = pd.read_csv(BRK).set_index("year")

    closure = (T["ais"] + T["gsic"] + T["gis"] + T["steric"] + T["lws"]) - T["dang"]
    print("=" * 78)
    print("DIAGNOSTIC: compensating component errors in the BRICK 2.0 total")
    print("=" * 78)
    print("\n[1] The observational budget's own non-closure — COMMON to both arms, so it cannot")
    print("    explain a difference between them. (sum of component targets + lws) - total, cm:")
    for a, b in WINDOWS:
        print(f"      {a}-{b}: mean {closure.loc[a:b].mean():+7.3f}")

    rows = []
    print("\n[2] SIGNED mean bias per component (model - obs), cm")
    for a, b in WINDOWS:
        print(f"\n    === {a}-{b} ===")
        print(f"    {'component':10s} {'Ladrillo':>10s} {'BRICK 2.0':>11s}")
        s = {"Ladrillo": 0.0, "BRICK 2.0": 0.0}
        absum = {"Ladrillo": 0.0, "BRICK 2.0": 0.0}
        for k in ("ais", "gsic", "gis", "steric"):
            rl = (L[LAD_COL[k]] - T[k]).loc[a:b].mean()
            rb = (B[BRK_COL[k]] - T[k]).loc[a:b].mean()
            s["Ladrillo"] += rl; s["BRICK 2.0"] += rb
            absum["Ladrillo"] += abs(rl); absum["BRICK 2.0"] += abs(rb)
            print(f"    {k:10s} {rl:+10.3f} {rb:+11.3f}")
            rows.append(dict(window=f"{a}-{b}", component=k, ladrillo_bias_cm=rl,
                             brick_bias_cm=rb))
        print(f"    {'SUM':10s} {s['Ladrillo']:+10.3f} {s['BRICK 2.0']:+11.3f}"
              f"   <- what the total sees")
        print(f"    {'sum|bias|':10s} {absum['Ladrillo']:10.3f} {absum['BRICK 2.0']:11.3f}"
              f"   <- how wrong each is component by component")
        for nm in ("Ladrillo", "BRICK 2.0"):
            frac = abs(s[nm]) / absum[nm] if absum[nm] > 0 else np.nan
            print(f"      {nm:10s} survives {frac:5.1%} of its own absolute error "
                  f"({1-frac:.0%} cancels)")
            rows.append(dict(window=f"{a}-{b}", component=f"__{nm}_summary",
                             ladrillo_bias_cm=s[nm] if nm == "Ladrillo" else np.nan,
                             brick_bias_cm=s[nm] if nm != "Ladrillo" else np.nan))

    print("\n[3] VERDICT")
    print("    BRICK 2.0 is wrong by MORE in every component in the early windows, but its")
    print("    Antarctic undershoot and glacier overshoot are opposite in sign and nearly equal,")
    print("    so ~90% of its error cancels in the sum. Ladrillo's residual errors are small and")
    print("    almost all positive, so essentially none of it cancels. The arm that is closer on")
    print("    every component is therefore further from the total.")
    print("    ⇒ read the component rows as the skill statement; the total row is dominated by")
    print("      whether errors happen to oppose one another.")

    stamp(pd.DataFrame(rows), __file__, tag=TAG,
          inputs={"targets": TGT, "ladrillo": LAD, "brick": BRK},
          extra="cm rel 1995-2005; signed window-mean biases").to_csv(OUT_CSV, index=False)
    print(f"\n[wrote] {os.path.relpath(OUT_CSV, REPO)}")


if __name__ == "__main__":
    main()
