#!/usr/bin/env python
"""Add hemispheric-mean tas (SH, NH) alongside the existing global/AIS reduction, to test
whether a Southern-Hemisphere denominator tames the mid-century amplification-ratio noise
(the aerosol hypothesis: NH aerosols depress global T, shrinking the denominator, while
Antarctica is aerosol-light).

For each model already reduced (tas_series_<model>.csv), stream the SAME member's tas for
historical+ssp245+ssp585 and write tas_series_hemis_<model>.csv with year, scenario,
tas_sh, tas_nh (cos-lat area-weighted means over lat<0 / lat>0; all longitudes, land+ocean).
Resumable.
"""
import glob, os, time, warnings
import numpy as np
import pandas as pd
import xarray as xr
import gcsfs

CATALOG_URL = "https://storage.googleapis.com/cmip6/cmip6-zarr-consolidated-stores.csv"
OUT_DIR     = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/data/cmip6_pai"
EXPS        = ["historical", "ssp245", "ssp585"]
GRIDS_OK    = ("gn", "gr", "gr1", "gr2")

warnings.filterwarnings("ignore")
fs = gcsfs.GCSFileSystem(token="anon")
openz = lambda z: xr.open_zarr(fs.get_mapper(z), consolidated=True)

def annual_hemis(ds, w_sh, w_nh):
    tas = ds["tas"]
    dim = xr.DataArray(ds.time.dt.days_in_month.values, dims="time", coords={"time": ds.time})
    yr = ds.time.dt.year
    out = {}
    for name, w in (("tas_sh", w_sh), ("tas_nh", w_nh)):
        s = tas.weighted(w).mean(("lat", "lon"))
        out[name] = ((s * dim).groupby(yr).sum() / dim.groupby(yr).sum()).to_series()
    return pd.DataFrame(out)

cat = pd.read_csv(CATALOG_URL)
tas = cat[(cat.table_id == "Amon") & (cat.variable_id == "tas")
          & (cat.experiment_id.isin(EXPS)) & (cat.grid_label.isin(GRIDS_OK))]

for f in sorted(glob.glob(os.path.join(OUT_DIR, "tas_series_*.csv"))):
    b = os.path.basename(f)
    if "_ext_" in b or "_deck_" in b or "_hemis_" in b:
        continue
    model = b[len("tas_series_"):-len(".csv")]
    out_csv = os.path.join(OUT_DIR, f"tas_series_hemis_{model}.csv")
    if os.path.exists(out_csv):
        print(f"SKIP {model}"); continue
    t0 = time.time()
    try:
        member = pd.read_csv(f, usecols=["member"]).member.iloc[0]
        sub = tas[(tas.source_id == model) & (tas.member_id == member)]
        if set(EXPS) - set(sub.experiment_id):
            print(f"PASS {model}: member {member} missing an experiment"); continue
        glabel = sorted(sub.grid_label)[0]
        s0 = openz(sub[sub.grid_label == glabel].zstore.iloc[0])
        if s0.lat.ndim != 1:
            print(f"PASS {model}: non-regular grid"); continue
        cl = np.cos(np.deg2rad(s0.lat))
        w = cl * xr.ones_like(s0.lon, dtype=float)
        w_sh = w.where(s0.lat < 0, 0.0); w_nh = w.where(s0.lat > 0, 0.0)
        frames = []
        for exp in EXPS:
            row = sub[(sub.experiment_id == exp) & (sub.grid_label == glabel)]
            if row.empty:
                row = sub[sub.experiment_id == exp]
            ds = openz(row.zstore.iloc[0])
            df = annual_hemis(ds, w_sh, w_nh); df["scenario"] = exp
            frames.append(df)
        allf = pd.concat(frames).reset_index().rename(columns={"index": "year", "time": "year"})
        allf.to_csv(out_csv, index=False)
        print(f"OK   {model} ({member}) {len(allf)} rows in {time.time()-t0:.0f}s", flush=True)
    except Exception as e:
        print(f"FAIL {model}: {type(e).__name__}: {e}", flush=True)
print("DONE hemis reduction", flush=True)
