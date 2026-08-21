#!/usr/bin/env python3
"""
build_protect_x2300_forcing.py — the GMST path that FORCED the PROTECT-Greenland
`x2300` arm, on this repo's GMST convention, as a Ladrillo driver.

WHY THIS EXISTS (2026-08-21)
  notes/handoff_2026-08-21_protect_greenland.md reported that our tapped Greenland
  cell reproduces the PROTECT x2300 ensemble at 2300 to 1.4% and undershoots it at
  2150 by 38%, and read that as "the onset is too late". That reading assumed the
  two were driven by the same warming. They are NOT:

      11-yr GSAT, C vs 1850-1900     2100   2150   2300
      ours (fair_mean_gmst_ssp585)   4.70   6.40   7.78
      PROTECT x2300 forcing GCMs     6.61   9.86  13.64      (n-weighted, below)

  So the comparison has to be redone at MATCHED forcing before any cell moves.
  This script builds the driver that makes that possible.

THE n-WEIGHTING
  The 18 long ssp585-x2300 runs (outputs/protect_greenland_gis_runs.csv) split
  12 IPSL-CM6A-LR / 6 CESM2-WACCM, so the ensemble's effective forcing is the
  12:6 weighted mean of the two GCM paths, NOT their unweighted average. Weights
  are recomputed from the runs table, never hardcoded.

TWO ARMS, because the splice convention is a real choice and is priced, not assumed
  `spliced`  our FaIR ssp585 GMST through 2014, then the GCM anomaly re-referenced
             to its own 1995-2014 mean and added to ours. Changes ONLY the future
             path, leaves the hindcast anchor identical to the shipped run. This is
             the controlled experiment and the one to read.
  `raw`      the GCM path on its own 1850-1900 baseline for all years. Carries the
             GCMs' historical too, so it also moves the hindcast anchor. Reported
             as the sensitivity on the splice choice.
  Each arm is written both RAW-annual and 11-yr centred. The tap consumes `gmt`
  UNSMOOTHED (brick_mengel.jl update_gis3_tap!), and our reference driver is an
  ensemble MEAN (already smooth) while these are ONE member each, so the smoothed
  column is the like-for-like one and the raw column prices that choice too.

CESM2-WACCM ends at 2299. Its 2300 is held at 2299 and FLAGGED in the output
(`held_last_year`); the path is flat there (2290-2299 trend +0.006 C/yr), so this
is worth <0.01 C and is not silently swept in.

WRITES outputs/protect_x2300_forcing_gmst.csv
  python3 python/build_protect_x2300_forcing.py
"""
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GSAT = os.path.join(REPO, "outputs/cmip6_ssp585ext_gsat.csv")
RUNS = os.path.join(REPO, "outputs/protect_greenland_gis_runs.csv")
OURS = os.path.join(REPO, "data/observations/fair_mean_gmst_ssp585.csv")
OUT = os.path.join(REPO, "outputs/protect_x2300_forcing_gmst.csv")

Y0, Y1 = 1850, 2300
SPLICE_YEAR = 2014                  # last year taken from our own path in the spliced arm
REF0, REF1 = 1995, 2014             # splice offset window — multi-year, never one year
SMOOTH = 11

ours = pd.read_csv(OURS).set_index("year").gmst_C.loc[Y0:Y1]
assert ours.index.equals(pd.Index(range(Y0, Y1 + 1))), "our GMST driver has gaps"

runs = pd.read_csv(RUNS)
x = runs[runs.exp.str.contains("x2300") & runs.long & runs.y2300.notna()]
x = x[x.ssp == "SSP5-8.5"]
w = x.exp.str.split("_").str[0].value_counts()
print(f"x2300 ssp585 run weights (n={int(w.sum())}): " +
      ", ".join(f"{k} {v}" for k, v in w.items()))

g = pd.read_csv(GSAT)
paths, held = {}, {}
for model in w.index:
    s = g[g.model == model].set_index("year").gsat_anom_C
    held[model] = int(s.index.max()) if s.index.max() < Y1 else None
    s = s.reindex(range(Y0, Y1 + 1)).ffill()      # only ever extends the LAST year
    assert s.notna().all(), f"{model}: gap inside {Y0}-{Y1}, ffill would hide it"
    paths[model] = s
    if held[model]:
        print(f"  {model}: ends {held[model]}, held flat to {Y1} "
              f"({Y1 - held[model]} yr; 2290-{held[model]} trend "
              f"{np.polyfit(range(2290, held[model]+1), s.loc[2290:held[model]], 1)[0]:+.4f} C/yr)")

gcm = sum(paths[m] * w[m] for m in w.index) / w.sum()

off = ours.loc[REF0:REF1].mean() - gcm.loc[REF0:REF1].mean()
spliced = pd.concat([ours.loc[:SPLICE_YEAR], gcm.loc[SPLICE_YEAR + 1:] + off])
print(f"splice offset over {REF0}-{REF1}: {off:+.3f} C "
      f"(ours {ours.loc[REF0:REF1].mean():.3f}, GCM {gcm.loc[REF0:REF1].mean():.3f})")
assert abs(spliced.loc[SPLICE_YEAR + 1] - spliced.loc[SPLICE_YEAR]) < 0.35, \
    "splice step is large — the offset window is not doing its job"

out = pd.DataFrame({"year": range(Y0, Y1 + 1)}).set_index("year")
out["gmst_ours"] = ours
out["gmst_raw"] = gcm
out["gmst_spliced"] = spliced
for c in ("gmst_ours", "gmst_raw", "gmst_spliced"):
    out[f"{c}_{SMOOTH}yr"] = out[c].rolling(SMOOTH, center=True, min_periods=1).mean()
out["n_runs"] = int(w.sum())
out["weights"] = "|".join(f"{k}:{v}" for k, v in w.items())
out["held_last_year"] = "|".join(f"{k}:{held[k]}" for k in w.index if held[k]) or "none"
out["basis"] = "C vs 1850-1900; spliced = ours <=2014 then GCM re-referenced on 1995-2014"
out.reset_index().to_csv(OUT, index=False)

print(f"\n{'year':>5} {'ours':>7} {'raw':>7} {'spliced':>8}   (11-yr centred)")
for y in (2050, 2100, 2150, 2200, 2300):
    r = out.loc[y]
    print(f"{y:>5} {r.gmst_ours_11yr:7.2f} {r.gmst_raw_11yr:7.2f} {r.gmst_spliced_11yr:8.2f}")
print(f"\nwrote {os.path.relpath(OUT, REPO)}")
