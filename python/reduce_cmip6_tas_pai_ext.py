#!/usr/bin/env python
"""Extend the PAI reduction with additional scenarios (ssp119, ssp126, ssp370).

For each model already reduced by reduce_cmip6_tas_pai.py (tas_series_<model>.csv),
stream the SAME member's tas for the extra experiments and write
tas_series_ext_<model>.csv (scenarios only — historical lives in the base file, and
anomaly baselines must come from the same member, so a scenario is skipped for a model
whose base member lacks it). Resumable: models with an existing _ext CSV are skipped.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pai_series import (align_sftlf_to, assert_global_plausible,
                        model_series_files)
import glob
import time
import warnings
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

## Which base files are per-model series comes from the shared resolver -- the old
## `if "_ext_" not in f` test admitted the deck, hemispheric and OHC sibling reductions
## as if they were models, so every run buried its real PASS/FAIL lines under ~100
## spurious ones (and would have written tas_series_ext_deck_<model>.csv had any of
## those pseudo-models carried the extra scenarios).
for model in sorted(model_series_files(OUT_DIR)):
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
        sftlf = openz(lfsub[lfsub.grid_label == glabel].zstore.iloc[0])["sftlf"].squeeze(drop=True)
        ## WEIGHTS ARE BUILT PER EXPERIMENT, ON THAT DATASET'S OWN COORDS -- see
        ## python/pai_series.py. Building them once from sftlf and reusing them silently
        ## reduced BOTH the global mean and the AIS mask to the sftlf/tas coordinate
        ## INTERSECTION on the MPI family (7.4-7.6 K low).
        frames = []
        got = []
        for exp in EXPS_EXT:
            row = sub[(sub.experiment_id == exp) & (sub.grid_label == glabel)]
            if row.empty:
                row = sub[sub.experiment_id == exp]
            if row.empty: continue
            ds = openz(row.zstore.iloc[0])
            if ds.lat.ndim != 1: continue
            lf_here = align_sftlf_to(sftlf, ds, f"{model}/{exp}")
            wg = np.cos(np.deg2rad(ds.lat)) * xr.ones_like(ds.lon, dtype=float)
            wa = wg.where((lf_here >= SFTLF_MIN) & (lf_here.lat <= AIS_LAT_MAX), 0.0)
            if float(wa.sum()) == 0.0:
                raise ValueError(f"empty AIS mask ({exp})")
            df = annual_means(ds, wg, wa)
            assert_global_plausible(df.tas_global, f"{model}/{exp}")
            df["scenario"] = exp
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
