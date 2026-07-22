#!/usr/bin/env python
"""Extend the PAI reduction with additional scenarios (ssp119, ssp126, ssp370).

For each model already reduced by reduce_cmip6_tas_pai.py (tas_series_<model>.csv),
stream the SAME member's tas for the extra experiments and write
tas_series_ext_<model>.csv (scenarios only — historical lives in the base file, and
anomaly baselines must come from the same member, so a scenario is skipped for a model
whose base member lacks it). Resumable: models with an existing _ext CSV are skipped.
"""
import glob, os, time, warnings
import numpy as np
import pandas as pd
import xarray as xr
import gcsfs

CATALOG_URL = "https://storage.googleapis.com/cmip6/cmip6-zarr-consolidated-stores.csv"
OUT_DIR     = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/data/cmip6_pai"
EXPS_EXT    = ["ssp119", "ssp126", "ssp370"]
SFTLF_MIN   = 50.0
AIS_LAT_MAX = -60.0
GRIDS_OK    = ("gn", "gr", "gr1", "gr2")

warnings.filterwarnings("ignore")
fs = gcsfs.GCSFileSystem(token="anon")
openz = lambda z: xr.open_zarr(fs.get_mapper(z), consolidated=True)

def annual_means(ds, wg, wa):
    tas = ds["tas"]
    glob = tas.weighted(wg).mean(("lat", "lon"))
    ais  = tas.weighted(wa).mean(("lat", "lon"))
    dim  = xr.DataArray(ds.time.dt.days_in_month.values, dims="time",
                        coords={"time": ds.time})
    yr   = ds.time.dt.year
    out  = {}
    for name, series in (("tas_global", glob), ("tas_ais", ais)):
        out[name] = ((series * dim).groupby(yr).sum() / dim.groupby(yr).sum()).to_series()
    return pd.DataFrame(out)

print("loading catalog ...", flush=True)
cat = pd.read_csv(CATALOG_URL)
tas = cat[(cat.table_id == "Amon") & (cat.variable_id == "tas")
          & (cat.experiment_id.isin(EXPS_EXT)) & (cat.grid_label.isin(GRIDS_OK))]
lf  = cat[(cat.variable_id == "sftlf") & (cat.grid_label.isin(GRIDS_OK))]

base_files = sorted(f for f in glob.glob(os.path.join(OUT_DIR, "tas_series_*.csv"))
                    if "_ext_" not in f)
for f in base_files:
    model = os.path.basename(f)[len("tas_series_"):-len(".csv")]
    out_csv = os.path.join(OUT_DIR, f"tas_series_ext_{model}.csv")
    if os.path.exists(out_csv):
        print(f"SKIP {model} (exists)"); continue
    t0 = time.time()
    try:
        member = pd.read_csv(f, usecols=["member"]).member.iloc[0]
        sub = tas[(tas.source_id == model) & (tas.member_id == member)]
        if sub.empty:
            print(f"PASS {model}: member {member} has none of {EXPS_EXT}"); continue
        lfsub = lf[(lf.source_id == model) & (lf.grid_label.isin(set(sub.grid_label)))]
        if lfsub.empty:
            lfsub = lf[lf.source_id == model]
        glabel = sorted(lfsub.grid_label)[0]
        sftlf = openz(lfsub[lfsub.grid_label == glabel].zstore.iloc[0])["sftlf"]
        wg = np.cos(np.deg2rad(sftlf.lat)) * xr.ones_like(sftlf.lon, dtype=float)
        wa = wg.where((sftlf >= SFTLF_MIN) & (sftlf.lat <= AIS_LAT_MAX), 0.0)
        frames = []
        got = []
        for exp in EXPS_EXT:
            row = sub[(sub.experiment_id == exp) & (sub.grid_label == glabel)]
            if row.empty:
                row = sub[sub.experiment_id == exp]
            if row.empty: continue
            ds = openz(row.zstore.iloc[0])
            if ds.lat.ndim != 1: continue
            df = annual_means(ds, wg, wa); df["scenario"] = exp
            frames.append(df); got.append(exp)
        if not frames:
            print(f"PASS {model}: no ext experiments on usable grids"); continue
        allf = pd.concat(frames).reset_index().rename(columns={"index": "year", "time": "year"})
        allf.insert(1, "member", member)
        allf.to_csv(out_csv, index=False)
        print(f"OK   {model} ({member}) {'+'.join(got)} {len(allf)} rows in "
              f"{time.time()-t0:.0f}s", flush=True)
    except Exception as e:
        print(f"FAIL {model}: {type(e).__name__}: {e}", flush=True)
print("DONE ext reduction", flush=True)
