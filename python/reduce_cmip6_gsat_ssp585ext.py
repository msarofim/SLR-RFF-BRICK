#!/usr/bin/env python3
"""
reduce_cmip6_gsat_ssp585ext.py — annual GLOBAL-mean and GREENLAND-region surface
air temperature for the two GCMs that force the PROTECT-Greenland `x2300` arm,
spliced 1850-2300.

WHY THIS EXISTS (2026-08-21)
  notes/handoff_2026-08-21_protect_greenland.md section 5 item 1. The PROTECT
  x2300 physics ensemble reproduces our tapped Greenland cell at 2300 to 1.4% and
  the cell undershoots the ensemble at 2150 by 38%. Before anyone re-cells the tap
  on that, the x2300 FORCING PATH has to be checked against ours -- a 2300 match
  under a hotter forcing is not the same evidence as a 2300 match under our own.

  The x2300 arm is forced by exactly two GCMs
  (data/comparison/protect_greenland/info_p11/exps_pxx_uniqc.txt):
      IPSL-CM6A-LR ssp585-x2300   MARv3.13-e05 (8 runs), MARv3.13-e55 (8 runs)
      CESM2-WACCM  ssp585-x2300   SDBN1        (6 runs)
  The PROTECT scalar files carry ice variables ONLY (ivol/ivaf/lim/slc/sle) -- no
  climate variable at all -- so GSAT must come from the source CMIP6 runs.

HOW THE SERIES IS BUILT
  1850-2100  data/cmip6_gis/tas_series_gis_<model>.csv, `tas_global`/`tas_gis_all`, member
             r1i1p1f1, historical + ssp585. Already in the repo; built by
             reduce_cmip6_tas_gis.py with cos(lat) area weights and month-length
             annual weighting.
  2101-2300  ESGF ssp585 extension files (scripts/fetch_cmip6_ssp585ext.sh),
             reduced HERE with the SAME weightings -- cos(lat) for global, and the
             repo's OWN Greenland mask (build_t_gis rings x Berkeley land fraction,
             ZONES["all"]) via reduce_cmip6_tas_gis.zone_weight_da, so the splice
             is not a method change disguised as a signal. The overlap is empty by
             construction (the extension files start 2101-01), so no year is
             double-counted and no join offset is applied.

BASELINE
  Anomalies are taken against each model's OWN historical 1850-1900 mean, a
  51-year window from the same member -- the multi-year-baseline convention.
  That is the same convention as the repo's GMST driver
  (data/observations/fair_mean_gmst_ssp585.csv, which reads 0.036 C at 1750).
  Absolute Kelvin is carried alongside so the anomaly can be re-based later.

CAVEAT CARRIED INTO THE OUTPUT
  THE GREENLAND COLUMN IS WHY THIS MATTERS BEYOND GSAT. Ladrillo amplifies global
  to Greenland at LADRILLO_GIS_AMP = 1.92 (modulated by the S(warming level) law).
  If these two GCMs amplify less, then a run at MATCHED GLOBAL temperature still
  feeds Greenland a hotter regional signal than the PROTECT ice sheet actually saw,
  and a "matched forcing" comparison is only matched at the global level. The
  `amp` column measures that directly, at the warming levels that matter.

  One member per model (r1i1p1f1) -- the only member either model extended past
  2100. Internal variability is therefore NOT sampled; single years are noisy and
  the 11-year centred mean columns are the ones to compare against.

WRITES outputs/cmip6_ssp585ext_gsat.csv
  python3 python/reduce_cmip6_gsat_ssp585ext.py
"""
import glob
import os
import sys
import warnings

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_t_gis as BTG
from reduce_cmip6_tas_gis import zone_weight_da

warnings.filterwarnings("ignore")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT_DIR = os.path.join(REPO, "data/cmip6_gsat_ext")
GIS_DIR = os.path.join(REPO, "data/cmip6_gis")
OUT = os.path.join(REPO, "outputs/cmip6_ssp585ext_gsat.csv")

MODELS = ["IPSL-CM6A-LR", "CESM2-WACCM"]
MEMBER = "r1i1p1f1"
SCENARIO = "ssp585"
BASE_LO, BASE_HI = 1850, 1900          # 51-yr baseline; never a single year
SMOOTH = 11                            # centred window for the comparison columns
SPLICE_YEAR = 2101                     # first year taken from the extension files


RINGS = BTG.region_paths(BTG.GTNG_REGION)
LAND_AT = BTG.berkeley_land_lookup()
ZONE_ALL = BTG.ZONES["all"]


def annual_means(ds):
    """cos(lat) global + Greenland-mask regional, month-length annual weighting —
    the same two reductions reduce_cmip6_tas_gis.py applied to the 2015-2100 half."""
    tas = ds["tas"]
    wg = np.cos(np.deg2rad(ds["lat"])) * xr.ones_like(ds["lon"], dtype=float)
    wr = zone_weight_da(ds["lat"], ds["lon"], RINGS, LAND_AT, ZONE_ALL)
    if float(wr.sum()) == 0.0:
        sys.exit("empty Greenland mask on this grid — refusing to report amp")
    dim = xr.DataArray(ds.time.dt.days_in_month.values, dims="time",
                       coords={"time": ds.time})
    yr = ds.time.dt.year
    den = dim.groupby(yr).sum()
    out = {}
    for name, w in (("tas_global", wg), ("tas_gis_all", wr)):
        series = tas.weighted(w).mean(("lat", "lon"))
        out[name] = ((series * dim).groupby(yr).sum() / den).to_series()
    return pd.DataFrame(out)


rows = []
for model in MODELS:
    base_csv = os.path.join(GIS_DIR, f"tas_series_gis_{model}.csv")
    if not os.path.exists(base_csv):
        sys.exit(f"missing {base_csv} — run reduce_cmip6_tas_gis.py first")
    d = pd.read_csv(base_csv)
    d = d[d.member == MEMBER]
    if d.empty:
        sys.exit(f"{model}: member {MEMBER} not in {base_csv}")

    ext = pd.concat([annual_means(xr.open_dataset(f)) for f in
                     sorted(glob.glob(os.path.join(EXT_DIR,
                            f"tas_Amon_{model}_{SCENARIO}_{MEMBER}_*.nc")))]).sort_index()
    if ext.empty:
        sys.exit(f"{model}: no extension files in {EXT_DIR} — "
                 f"run bash scripts/fetch_cmip6_ssp585ext.sh")
    ext = ext[~ext.index.duplicated()]
    ext = ext[ext.index >= SPLICE_YEAR]

    cols = {}
    for col in ("tas_global", "tas_gis_all"):
        hist = d[d.scenario == "historical"].set_index("year")[col]
        scen = d[d.scenario == SCENARIO].set_index("year")[col]
        if scen.empty:
            sys.exit(f"{model}: no {SCENARIO} rows in {base_csv}")
        overlap = sorted(set(scen.index) & set(ext.index))
        if overlap:
            sys.exit(f"{model}: extension overlaps the 2015-2100 half at {overlap[:5]} — "
                     f"splice assumption violated, do not silently average")
        full = pd.concat([hist, scen, ext[col]]).sort_index()
        dup = full.index[full.index.duplicated()]
        if len(dup):
            sys.exit(f"{model}: duplicated years after splice: {sorted(set(dup))[:5]}")
        base = hist.loc[BASE_LO:BASE_HI]
        if len(base) < (BASE_HI - BASE_LO + 1):
            sys.exit(f"{model}: baseline window incomplete ({len(base)} yr) — refusing "
                     f"to baseline on a short window")
        cols[col] = (full, full - base.mean(), base.mean())

    (full, anom, gbase) = cols["tas_global"]
    (_, ranom, rbase) = cols["tas_gis_all"]
    sm = lambda v: v.rolling(SMOOTH, center=True, min_periods=SMOOTH).mean()
    src = pd.Series("cmip6_gis_csv", index=full.index)
    src.loc[src.index >= SPLICE_YEAR] = "esgf_ext_nc"

    rows.append(pd.DataFrame({
        "year": full.index, "model": model, "member": MEMBER, "scenario": SCENARIO,
        "tas_global_K": full.values,
        "gsat_anom_C": anom.values,
        f"gsat_anom_C_{SMOOTH}yr": sm(anom).values,
        "gis_anom_C": ranom.values,
        f"gis_anom_C_{SMOOTH}yr": sm(ranom).values,
        ## amp on SMOOTHED anomalies: the ratio of two noisy annual series is
        ## unusable near the start, where the denominator passes through zero.
        "amp_11yr": (sm(ranom) / sm(anom)).values,
        "source": src.values,
    }))
    print(f"{model}: {full.index.min()}-{full.index.max()} "
          f"({len(full)} yr, {int((src=='esgf_ext_nc').sum())} from ESGF extension) | "
          f"base glob {gbase:.2f} K / GIS {rbase:.2f} K | "
          f"GSAT 2100 {anom.loc[2100]:+.2f} 2150 {anom.loc[2150]:+.2f} "
          f"{full.index.max()} {anom.loc[full.index.max()]:+.2f} C | "
          f"amp 2100 {(sm(ranom)/sm(anom)).loc[2100]:.2f} "
          f"2150 {(sm(ranom)/sm(anom)).loc[2150]:.2f} "
          f"2290 {(sm(ranom)/sm(anom)).loc[2290]:.2f}", flush=True)

out = pd.concat(rows, ignore_index=True)
out["basis"] = f"anomaly vs own historical {BASE_LO}-{BASE_HI} mean"
out.to_csv(OUT, index=False)
print(f"\nwrote {os.path.relpath(OUT, REPO)}  ({len(out)} rows)")
