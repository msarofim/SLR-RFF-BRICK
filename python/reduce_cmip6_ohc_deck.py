#!/usr/bin/env python
"""Reduce an OHC proxy (zostoga = global thermosteric sea level) for the DECK runs, to
test whether OHC carries the Antarctic time-component that GMST alone misses.

zostoga (Omon) is a per-timestep global scalar directly proportional to ocean heat content
(depth-integrated thermal expansion) — the same quantity BRICK's thermal-expansion
component ingests, and the natural slow-integrating predictor. For each model already in
tas_series_deck_<model>.csv, stream the SAME member's zostoga for
{1pctCO2, abrupt-4xCO2, piControl} and write tas_series_ohc_deck_<model>.csv:
  year (1-based since branch), scenario, ohc  (zostoga, m).
Resumable.
"""
import glob, os, time, warnings
import numpy as np
import pandas as pd
import xarray as xr
import gcsfs

CATALOG_URL   = "https://storage.googleapis.com/cmip6/cmip6-zarr-consolidated-stores.csv"
OUT_DIR       = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/data/cmip6_pai"
EXPS          = ["1pctCO2", "abrupt-4xCO2", "piControl"]
ABRUPT_MAX_YRS = 300; PICTRL_YRS = 200
VARS          = ["zostoga"]          # OHC proxy (Omon global scalar)

warnings.filterwarnings("ignore")
fs = gcsfs.GCSFileSystem(token="anon")
openz = lambda z: xr.open_zarr(fs.get_mapper(z), consolidated=True)

def annual(ds, var):
    v = ds[var]
    # zostoga is (time,) global scalar in most models; if it carries stray dims, mean them
    extra = [d for d in v.dims if d != "time"]
    if extra:
        v = v.mean(extra)
    dim = xr.DataArray(ds.time.dt.days_in_month.values, dims="time", coords={"time": ds.time})
    yr = ds.time.dt.year
    s = ((v * dim).groupby(yr).sum() / dim.groupby(yr).sum()).to_series().reset_index(drop=True)
    s.index = s.index + 1
    return s

cat = pd.read_csv(CATALOG_URL)
oc = cat[(cat.table_id == "Omon") & (cat.variable_id.isin(VARS))
         & (cat.experiment_id.isin(EXPS))]

for f in sorted(glob.glob(os.path.join(OUT_DIR, "tas_series_deck_*.csv"))):
    model = os.path.basename(f)[len("tas_series_deck_"):-len(".csv")]
    out_csv = os.path.join(OUT_DIR, f"tas_series_ohc_deck_{model}.csv")
    if os.path.exists(out_csv):
        print(f"SKIP {model}"); continue
    t0 = time.time()
    try:
        dm = pd.read_csv(f)
        member = dm[dm.scenario == "1pctCO2"].member.iloc[0]
        sub = oc[(oc.source_id == model) & (oc.member_id == member)]
        have = set(sub.experiment_id)
        if not ({"1pctCO2", "abrupt-4xCO2"} <= have):
            print(f"PASS {model}: zostoga missing for member {member} ({sorted(have)})"); continue
        frames = []
        for exp in EXPS:
            row = sub[sub.experiment_id == exp]
            if row.empty: continue
            ds = openz(sorted(row.zstore)[0] if len(row) else row.zstore.iloc[0])
            cap = {"abrupt-4xCO2": ABRUPT_MAX_YRS, "piControl": PICTRL_YRS}.get(exp)
            if cap is not None:
                ds = ds.isel(time=slice(0, 12 * cap))
            s = annual(ds, "zostoga").rename("ohc").to_frame()
            s["scenario"] = exp; s = s.reset_index().rename(columns={"index": "year"})
            frames.append(s)
        allf = pd.concat(frames)
        allf.to_csv(out_csv, index=False)
        got = allf.scenario.unique()
        print(f"OK   {model} ({member}) {'+'.join(got)} in {time.time()-t0:.0f}s", flush=True)
    except Exception as e:
        print(f"FAIL {model}: {type(e).__name__}: {e}", flush=True)
print("DONE ohc reduction", flush=True)
