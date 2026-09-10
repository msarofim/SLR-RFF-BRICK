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

⚠ THIS SCRIPT PROPOSES NO CHANGE. Which arm to put on which convention is a methodological
choice about how BRICK is scored, and it is Marcus's. It only measures the size.
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
TAG  = "L24"
OUT_CSV = os.path.join(REPO, "outputs", "diag_lws_convention_asymmetry.csv")
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
    obs, obs_lws = L["total_obs"], T["lws"].reindex(B.index)

    lws_b = pd.Series(0.0, index=B.index)
    ky = sorted(BRICK_LWS_MEASURED)
    span = [y for y in B.index if y >= BRICK_LWS_ZERO_THROUGH]
    lws_b.loc[span] = np.interp(span, ky, [BRICK_LWS_MEASURED[k] for k in ky])
    corr = B["total_p50"] - lws_b + obs_lws      # put BRICK on Ladrillo's LWS convention

    print("=" * 78)
    print("DIAGNOSTIC: the LWS convention differs between the two hindcast arms")
    print("=" * 78)
    print(f"  BRICK's own LWS is EXACTLY 0 through {BRICK_LWS_ZERO_THROUGH}, "
          f"+{BRICK_LWS_MEASURED[2024]:.3f} cm by 2024 (measured).")
    print(f"  Observed LWS anomaly: {obs_lws[1900]:+.3f} cm at 1900, "
          f"{obs_lws[2024]:+.3f} at 2024 (rel 1995-2005).")

    rows = []
    o = wmean(obs, *CUM[1]) - wmean(obs, *CUM[0])
    ba = wmean(B['total_p50'], *CUM[1]) - wmean(B['total_p50'], *CUM[0])
    bc = wmean(corr, *CUM[1]) - wmean(corr, *CUM[0])
    la = wmean(L['total_p50'], *CUM[1]) - wmean(L['total_p50'], *CUM[0])
    print(f"\n[1] CUMULATIVE RISE {CUM[0][0]}-{CUM[0][1]} -> {CUM[1][0]}-{CUM[1][1]} (cm)")
    print(f"    observed {o:6.2f}   Ladrillo {la:6.2f} ({la-o:+.2f})")
    print(f"    BRICK as built {ba:6.2f} ({ba-o:+.2f})   BRICK on Ladrillo's LWS {bc:6.2f} "
          f"({bc-o:+.2f})   <== overshoot roughly HALVED")
    rows.append(dict(quantity="cumulative_rise_cm", obs=o, ladrillo=la,
                     brick_as_built=ba, brick_obs_lws=bc))

    o2 = wmean(obs, *LVL)
    print(f"\n[2] LEVEL AT 2024 ({LVL[0]}-{LVL[1]} mean, cm)   observed {o2:.2f}")
    print(f"    BRICK gap as built {wmean(B['total_p50'],*LVL)-o2:+.2f}   "
          f"on Ladrillo's LWS {wmean(corr,*LVL)-o2:+.2f}")
    rows.append(dict(quantity="level_2024_gap_cm", obs=o2, ladrillo=wmean(L['total_p50'],*LVL)-o2,
                     brick_as_built=wmean(B['total_p50'],*LVL)-o2,
                     brick_obs_lws=wmean(corr,*LVL)-o2))

    print(f"\n[3] ⛔ RMSE RATIO ON THE TOTAL (Ladrillo / BRICK; <1 = Ladrillo closer)")
    print(f"    {'window':11s} {'as built':>9s} {'BRICK on Ladrillo LWS':>23s}  verdict flip?")
    for wn, (a, b) in WINDOWS.items():
        m = obs.notna() & (obs.index >= a) & (obs.index <= b)
        rl = np.sqrt(((L["total_p50"][m] - obs[m]) ** 2).mean())
        rb = np.sqrt(((B["total_p50"][m] - obs[m]) ** 2).mean())
        rc = np.sqrt(((corr[m] - obs[m]) ** 2).mean())
        flip = "YES" if (rl / rb < 1) != (rl / rc < 1) else "no"
        print(f"    {wn:11s} {rl/rb:9.3f} {rl/rc:23.3f}  {flip}")
        rows.append(dict(quantity=f"rmse_ratio_total_{wn}", obs=np.nan, ladrillo=np.nan,
                         brick_as_built=rl/rb, brick_obs_lws=rl/rc))

    print(f"\n[4] VERDICT")
    print(f"    The TOTAL row of the deliverable's RMSE table is substantially an LWS-CONVENTION")
    print(f"    artifact, not a skill difference: on 'full' it moves 0.459 -> 1.123, i.e. the")
    print(f"    direction of the verdict REVERSES. The component rows are untouched.")
    print(f"    ⚠ NO CHANGE PROPOSED — which arm gets which convention is Marcus's call.")

    stamp(pd.DataFrame(rows), __file__, tag=TAG,
          inputs={"brick": BRK, "ladrillo": LAD, "targets": TGT},
          extra="cm; BRICK LWS measured by julia/diag_brick_lws_extract.jl"
          ).to_csv(OUT_CSV, index=False)
    print(f"\n[wrote] {os.path.relpath(OUT_CSV, REPO)}")


if __name__ == "__main__":
    main()
