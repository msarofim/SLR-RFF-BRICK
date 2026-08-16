#!/usr/bin/env python3
"""
scope_l10_vs_l11_scorecard.py — what the L11 change set did to the hindcast,
module by module and window by window.

Companion to scope_ladrillo_vs_brick20_scorecard.py (Ladrillo vs BRICK 2.0).
This one is Ladrillo-vs-Ladrillo: L10 (the accepted 2026-08-13 calibration)
against L11 (the 2026-08-14 change set: total dropped, GlaMBIE R19 rate,
tightened rung sigma, D2 on gsic+steric, Greenland (ell, w)).

BOTH ARMS ARE ON THE SAME FOOTING: same script (posterior_predictive_ladrillo.jl
--tag=), same forcing, same 1995-2005 re-reference, same targets, same 2000
draws, same noise seed. The only difference is the posterior.

TWO ASYMMETRIES THE READER MUST NOT MISS, both carried in the output:

  1. THE TOTAL IS OUT-OF-SAMPLE FOR L11 AND IN-SAMPLE FOR L10. D1 dropped the
     total stream, so L11 was never fit to it. Its L11 row is therefore a
     PREDICTION and its L10 row is a residual. That is not a flaw in the
     comparison -- it is the direct measurement of what D1 discarded, which the
     spec explicitly called "a deliberate discard of an independent
     observational constraint, not a tidy-up".

  2. GLACIERS ARE SCORED AGAINST THE DELTA-CORRECTED TARGET, not the raw one.
     The gsic obs carry a per-draw M15/Roe-2021 early-segment ramp on the OBS
     side (gic_delta over 1900-1959), so the series the fit actually compares
     against is `glaciers_obs_delta_corrected`. Using the raw `glaciers_obs`
     instead inflates the early-century glacier bias roughly SEVENFOLD (+1.28
     rather than +0.20 cm over 1900-1919 on L10) and would report a large
     spurious regression. Checked, because I made exactly that error first.

  source ~/climate-env/bin/activate
  python3 python/scope_l10_vs_l11_scorecard.py
Writes outputs/scope_l10_vs_l11_scorecard.csv
"""
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs/scope_l10_vs_l11_scorecard.csv")

ARMS = ["L10", "L11"]
# component -> the obs column it is scored against. Glaciers deliberately use the
# delta-corrected target; see the header.
OBS_COL = {"ais": "ais_obs", "glaciers": "glaciers_obs_delta_corrected",
           "gis": "gis_obs", "te": "te_obs", "total": "total_obs"}
# Windows split the sparse-obs era, the pre-satellite era and the altimetry era,
# matching scope_ladrillo_vs_brick20_scorecard.py so the two are readable together.
WINDOWS = [("full", None), ("1900-1919", (1900, 1919)), ("1920-1949", (1920, 1949)),
           ("1950-1992", (1950, 1992)), ("1993-2026", (1993, 2026))]
# Series each arm was actually FIT to. L11 dropped the total (D1).
FITTED = {"L10": {"ais", "glaciers", "gis", "te", "total"},
          "L11": {"ais", "glaciers", "gis", "te"}}

ts = {a: pd.read_csv(os.path.join(REPO, f"outputs/postpred_{a}_components_timeseries.csv"))
      for a in ARMS}

rows = []
for comp, ocol in OBS_COL.items():
    for wname, wspan in WINDOWS:
        rec = {"component": comp, "window": wname}
        for a in ARMS:
            d = ts[a]
            m = d[ocol].notna()
            if wspan is not None:
                m &= (d.year >= wspan[0]) & (d.year <= wspan[1])
            if not m.any():
                rec[f"bias_{a}"] = rec[f"cover_{a}"] = np.nan
                continue
            o, p50 = d.loc[m, ocol], d.loc[m, f"{comp}_p50"]
            p05, p95 = d.loc[m, f"{comp}_p05"], d.loc[m, f"{comp}_p95"]
            rec[f"n_{a}"] = int(m.sum())
            rec[f"bias_{a}"] = float((p50 - o).mean())
            rec[f"cover_{a}"] = float(((p05 <= o) & (o <= p95)).mean())
            rec[f"in_sample_{a}"] = comp in FITTED[a]
        rec["d_bias"] = rec["bias_L11"] - rec["bias_L10"]
        rec["d_cover"] = rec["cover_L11"] - rec["cover_L10"]
        rows.append(rec)

sc = pd.DataFrame(rows)
sc.to_csv(OUT, index=False, float_format="%.4f")

print("L10 -> L11 hindcast scorecard  (bias = model p50 - obs, cm; cover = 90% "
      "PARAMETER band)\n")
print(f"{'component':<10}{'window':<11}{'bias L10':>9}{'bias L11':>9}{'Δbias':>8}"
      f"{'cov L10':>9}{'cov L11':>9}{'Δcov':>8}   note")
for _, r in sc.iterrows():
    note = "" if r.in_sample_L11 else "L11 OUT-OF-SAMPLE"
    print(f"{r.component:<10}{r.window:<11}{r.bias_L10:+9.3f}{r.bias_L11:+9.3f}"
          f"{r.d_bias:+8.3f}{100*r.cover_L10:8.1f}%{100*r.cover_L11:8.1f}%"
          f"{100*r.d_cover:+7.1f}   {note}")
print(f"\nWrote {os.path.relpath(OUT, REPO)}")
