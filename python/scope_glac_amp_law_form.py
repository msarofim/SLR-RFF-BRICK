#!/usr/bin/env python3
"""
scope_glac_amp_law_form.py — IS THERE A "FUTURE SHAPE" IN CMIP6 WORTH BORROWING FOR THE
                             GLACIER BLOCKS?

THE QUESTION (Marcus 2026-08-28): can we anchor the amplification LEVEL on historical
observations — which we can check — and take the future SHAPE from CMIP6, which is the only
thing with a future? Greenland already works this way (a projection-side amplification law
anchored to an OBSERVED level, diag_glac_amp_cmip6_offset.py header), so the pattern exists;
this asks whether it has any CONTENT for glaciers.

⚠ THE DESIGN ONLY HAS CONTENT IF CMIP6 SAYS THE AMPLIFICATION ACTUALLY CHANGES WITH WARMING.
If CMIP6's block amplification is flat in dT, there is no shape to borrow and an obs-anchored
"law" would be an obs-anchored CONSTANT — exactly what is already shipped, with extra
machinery. So this measures the shape FIRST and only then asks what anchoring would do.

METHOD — deliberately the same as scope_ais_amp_law_form.py [A], which settled the identical
question for Antarctica and answered NO:
  * per model, block amplification as a SECANT (level ratio, not a trend) in rolling windows
  * regress that secant on the model's own dT_global
  * RESTRICT TO dT >= DT_MIN, "where the denominator is not noise" — the rule
    diag_pai_cmip6_time.py uses, because a secant divided by a small dT is unbounded noise
  * report the per-model slope distribution: median, se on the mean, z, and — the number that
    decides it — WHAT THE SLOPE IS WORTH over the projection range against the BETWEEN-MODEL
    spread. A shape 6-9x smaller than the spread is not a shape, it is a rounding error.
    (That is exactly the ratio that killed amp(dT) for Antarctica.)

⚠ SECANT, NOT TREND. BRICK's amplification multiplies a LEVEL anomaly, so the secant is the
BRICK-relevant statistic. The trend ratio (Xie's PAI1) behaves OPPOSITELY with warming and
using it here would repeat a documented sign error.

    source ~/climate-env/bin/activate
    python python/scope_glac_amp_law_form.py
Reads   data/cmip6_glac/tas_series_glac_*.csv  (45 models, absolute K, per block)
Writes  outputs/scope_glac_amp_law_form.csv
"""
import os, glob, subprocess
import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CMIP_DIR = os.path.join(REPO, "data/cmip6_glac")
OUT = os.path.join(REPO, "outputs/scope_glac_amp_law_form.csv")
COMMIT = subprocess.check_output(["git","-C",REPO,"rev-parse","--short","HEAD"],text=True).strip()

BLOCKS = ["R19", "SLOWP", "FAST"]
BASE = (1850, 1900)          # anomaly frame, both sides rebased to their own window mean
DT_MIN = 1.0                 # "where the denominator is not noise"
WIN = 21                     # rolling window for the secant, years
PROJ_RANGE = (1.0, 4.0)      # the range a law would have to act over
PRIOR_SD = {"R19": 0.15, "SLOWP": 0.45, "FAST": 0.15}   # calibrate_mcmc_ext.jl AMP_PRIOR

rows, per_model = [], {b: [] for b in BLOCKS}
files = sorted(glob.glob(os.path.join(CMIP_DIR, "tas_series_glac_*.csv")))
for f in files:
    d = pd.read_csv(f)
    d = d[d.scenario.isin(["historical", "ssp245", "ssp585"])]
    if d.empty: continue
    for scen in [s for s in ("ssp245","ssp585") if s in set(d.scenario)]:
        hist = d[d.scenario=="historical"]
        fut  = d[d.scenario==scen]
        s = pd.concat([hist, fut]).drop_duplicates(subset="year").sort_values("year")
        base = s[(s.year>=BASE[0]) & (s.year<=BASE[1])]
        if len(base) < 30: continue
        g = (s.tas_global.to_numpy() - base.tas_global.mean())
        for b in BLOCKS:
            col = f"tas_{b}"
            if col not in s: continue
            y = (s[col].to_numpy() - base[col].mean())
            # rolling-window secants
            dts, amps = [], []
            for i in range(0, len(g)-WIN, 5):
                gg, yy = g[i:i+WIN], y[i:i+WIN]
                dt = gg.mean()
                if dt < DT_MIN: continue
                denom = (gg**2).sum()
                if denom <= 0: continue
                dts.append(dt); amps.append(float((gg*yy).sum()/denom))
            if len(dts) < 4: continue
            sl = np.polyfit(dts, amps, 1)[0]
            per_model[b].append((os.path.basename(f), scen, sl, float(np.mean(amps))))

print(f"GLACIER AMPLIFICATION — IS THERE A CMIP6 'SHAPE' TO BORROW?   [commit {COMMIT}]")
print(f"{len(files)} model files | secant, {WIN}-yr windows | dT >= {DT_MIN} K | "
      f"anomaly frame {BASE[0]}-{BASE[1]}\n")
print(f"{'block':<7} {'n':>4} {'slope/K':>10} {'se':>8} {'z':>7} {'worth over 1-4K':>17} "
       f"{'between-model sd':>17} {'ratio':>8}  VERDICT")
print("-"*104)
for b in BLOCKS:
    v = per_model[b]
    if len(v) < 5:
        print(f"{b:<7} {len(v):>4}  too few models"); continue
    sl = np.array([x[2] for x in v]); lev = np.array([x[3] for x in v])
    med = float(np.median(sl)); se = float(sl.std(ddof=1)/np.sqrt(len(sl)))
    z = med/se if se>0 else np.nan
    worth = med*(PROJ_RANGE[1]-PROJ_RANGE[0])
    bmsd = float(lev.std(ddof=1))
    ratio = abs(worth)/bmsd if bmsd>0 else np.nan
    resolved = abs(z) >= 2.0
    verdict = ("SHAPE IS REAL and material" if resolved and ratio >= 0.5 else
               "resolved but NEGLIGIBLE vs the spread" if resolved else
               "UNRESOLVED — no shape to borrow")
    print(f"{b:<7} {len(sl):>4} {med:+10.4f} {se:8.4f} {z:+7.2f} {worth:+17.3f} "
          f"{bmsd:17.3f} {ratio:8.2f}  {verdict}")
    rows.append(dict(block=b, n_model_scen=len(sl), slope_per_K=med, se=se, z=z,
                     worth_over_1_4K=worth, between_model_sd=bmsd, ratio=ratio,
                     prior_sd=PRIOR_SD[b], worth_over_prior_sd=abs(worth)/PRIOR_SD[b],
                     verdict=verdict))
pd.DataFrame(rows).to_csv(OUT, index=False)
print(f"\nFor scale, the SAME test on Antarctica (scope_ais_amp_law_form.py) returned")
print(f"  ssp245 slope -0.0065/K z=-0.59, ssp585 +0.0091/K z=+1.43 — OPPOSITE SIGNS, both")
print(f"  UNRESOLVED, worth 0.02-0.03 against a between-model sd of ~0.18, and amp(dT) was")
print(f"  NOT built. Read this table against that precedent.")
print(f"\nwrote {os.path.relpath(OUT, REPO)}")
