#!/usr/bin/env python3
"""
extract_protect_greenland.py — the PROTECT-Greenland physics ensemble (Goelzer
2025) reduced to a per-scenario, per-year Greenland SLR contribution table on
THIS repo's basis.

WHY THIS EXISTS (2026-08-21)
  The tap's admissible set is 25 cells, and the question of whether to narrow it
  on 2150 turned on what evidence exists at that horizon. Until now the answer was
  "FACTS only", i.e. an ISMIP6 EMULATOR (FittedISMIP) plus STRUCTURED EXPERT
  JUDGMENT (bamber19) -- emuGrIS and MAGICC-SLR both stop at 2100. This dataset is
  the only physics-based Greenland source in the repo with ANNUAL series past 2100.

THE COVERAGE CAVEAT, WHICH IS THE WHOLE POINT — DO NOT SKIP IT
  The headline "1472 projections / four ice sheet models" is a 2100 result. Of
  1568 scalar files, 1297 STOP AT 2100. Every one of the 209 runs reaching 2150+
  is NORCE-CISM. So past 2100 this is ONE ice sheet model under many climate
  forcings (14 GCMs x MAR/RACMO/SDBN x five retreat percentiles), and its spread
  is dominated by CLIMATE forcing, not by ice-sheet structural uncertainty. Using
  its p17-p83 as a hard cut would therefore be TIGHTER than the evidence warrants.
  Reported per-model so this cannot be lost.

THREE CORRECTIONS APPLIED, each of which changes the number
  1. CONTROL DRIFT REMOVED. ISMIP6 convention: an unforced ctrl-proj run does not
     sit still, and its drift is model error, not signal. Each experiment is paired
     with the ctrl-proj of its OWN group/model directory and the control's
     contribution is subtracted year by year. Runs with no matching control are
     REPORTED AND DROPPED, never silently kept.
  2. SIGN. `sle`/`slc` are sea-level-equivalent MASS and DECREASE as ice is lost
     (the dataset README flags this twice). Contribution = -(x - x[0]).
     `slc` is preferred where present -- it is the Goelzer & Coulon 2020 corrected
     variable that accounts for ice below flotation and bedrock adjustment.
  3. BASELINE. The series start at end-2015; this repo reports rel. 1995-2014.
     The dataset CANNOT supply that offset (it has no pre-2015 data), so it is NOT
     invented here. The output carries `basis = "rel 2015"` and the offset is left
     to the consumer, which must state it. Adding an unsourced ~1 cm would be
     exactly the single-year-baselining artefact the standing conventions forbid.

WRITES outputs/protect_greenland_gis_summary.csv  (per scenario x year quantiles)
       outputs/protect_greenland_gis_runs.csv     (per run, for auditing)

  python3 python/extract_protect_greenland.py
"""
import glob
import os
import sys

import numpy as np
import pandas as pd
import xarray as xr

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data/comparison/protect_greenland")
OUT_SUM = os.path.join(REPO, "outputs/protect_greenland_gis_summary.csv")
OUT_RUN = os.path.join(REPO, "outputs/protect_greenland_gis_runs.csv")

YEAR0 = 2015                 # dataset README: first entry = end of 2015
BASIS = "rel 2015"           # NOT re-baselined to 1995-2014; see docstring item 3
REPORT_YEARS = (2100, 2150, 2200, 2300)
MIN_YEARS_LONG = 136         # 2015 + 136 - 1 = 2150
CM_PER_M = 100.0
QUANTILES = (0.05, 0.17, 0.50, 0.83, 0.95)


def scenario_of(exp):
    """SSP label from the ISMIP6 expid <gcm>-<scenario>_<rcm>_<retreat pct>."""
    for key, lab in (("ssp585", "SSP5-8.5"), ("rcp85", "SSP5-8.5"),
                     ("ssp245", "SSP2-4.5"), ("ssp126", "SSP1-2.6")):
        if key in exp:
            return lab
    return None


def contribution(path):
    """Greenland SLR contribution in cm, sign-corrected, rel. its own year 0."""
    d = xr.open_dataset(path, decode_times=False)
    var = "slc" if "slc" in d.data_vars else "sle"
    a = np.asarray(d[var].values, dtype=float).ravel()
    if a.size == 0 or not np.isfinite(a[0]):
        return None, var
    return -(a - a[0]) * CM_PER_M, var


def main():
    files = sorted(glob.glob(os.path.join(DATA, "*/*/*/scalars_mm_GIS_*.nc")))
    if not files:
        raise SystemExit(
            f"no scalar files under {os.path.relpath(DATA, REPO)}.\n"
            "  Fetch them first:  bash scripts/fetch_protect_greenland.sh")
    print(f"extract_protect_greenland | {len(files)} scalar files")

    # ---- controls, keyed by (group, model) ---------------------------------
    controls = {}
    for f in files:
        p = f.split(os.sep)
        exp, model, group = p[-2], p[-3], p[-4]
        if not exp.startswith("ctrl"):
            continue
        c, _ = contribution(f)
        if c is None:
            continue
        # prefer the longest control available for that model
        k = (group, model)
        if k not in controls or len(c) > len(controls[k]):
            controls[k] = c
    print(f"  control runs found: {len(controls)} (group, model) pairs")

    rows, dropped = [], []
    for f in files:
        p = f.split(os.sep)
        exp, model, group = p[-2], p[-3], p[-4]
        if exp.startswith("ctrl"):
            continue
        ssp = scenario_of(exp)
        if ssp is None:
            continue
        c, var = contribution(f)
        if c is None:
            continue
        ctl = controls.get((group, model))
        if ctl is None:
            dropped.append((group, model, exp, "no matching ctrl-proj"))
            continue
        n = min(len(c), len(ctl))
        corr = c[:n] - ctl[:n]        # ISMIP6 control-drift removal
        rec = dict(group=group, model=model, exp=exp, ssp=ssp, var=var,
                   n_years=n, last_year=YEAR0 + n - 1, long=n >= MIN_YEARS_LONG)
        for y in REPORT_YEARS:
            i = y - YEAR0
            rec[f"y{y}"] = float(corr[i]) if 0 <= i < n else np.nan
        rows.append(rec)

    runs = pd.DataFrame(rows)
    if dropped:
        print(f"  DROPPED {len(dropped)} runs with no matching control:")
        for d in dropped[:6]:
            print(f"    {d[0]}/{d[1]}/{d[2]} — {d[3]}")
    runs.to_csv(OUT_RUN, index=False)

    # ---- summary, and the per-model breakdown that carries the caveat ------
    out = []
    for ssp, g in runs.groupby("ssp"):
        for y in REPORT_YEARS:
            v = g[f"y{y}"].dropna()
            if not len(v):
                continue
            models = sorted(g.loc[v.index, "group"].unique())
            rec = dict(ssp=ssp, year=y, n=len(v), basis=BASIS,
                       n_groups=len(models), groups="+".join(models))
            for q in QUANTILES:
                rec[f"p{int(q*100):02d}"] = float(v.quantile(q))
            out.append(rec)
    summ = pd.DataFrame(out).sort_values(["ssp", "year"])
    summ.to_csv(OUT_SUM, index=False)

    print(f"\nGreenland SLR contribution, cm {BASIS}, control drift REMOVED:")
    print(f"  {'ssp':9s} {'year':>5s} {'n':>4s} {'p05':>7s} {'p17':>7s} "
          f"{'p50':>7s} {'p83':>7s} {'p95':>7s}  models")
    for r in summ.itertuples():
        print(f"  {r.ssp:9s} {r.year:5d} {r.n:4d} {r.p05:7.2f} {r.p17:7.2f} "
              f"{r.p50:7.2f} {r.p83:7.2f} {r.p95:7.2f}  {r.groups}")
    print(f"\n  ⚠ COVERAGE: rows whose `groups` is a single entry are ONE ice "
          f"sheet model.\n    Past 2100 that is NORCE only — climate-forcing "
          f"spread, not structural spread.")
    for p in (OUT_SUM, OUT_RUN):
        print("wrote", os.path.relpath(p, REPO))


if __name__ == "__main__":
    main()
