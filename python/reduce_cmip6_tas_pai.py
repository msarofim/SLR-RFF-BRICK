#!/usr/bin/env python
"""Reduce CMIP6 tas to annual global-mean + AIS-mean series for the PAI-vs-time diagnostic.

Streams Amon tas from the public Pangeo/Google-Cloud CMIP6 zarr archive (anonymous);
nothing raw is stored — output is one small tidy CSV per model in OUT_DIR:
  columns: year, scenario, tas_global, tas_ais   (Kelvin, annual month-length-weighted means)

AIS proxy: land (sftlf >= SFTLF_MIN %) south of AIS_LAT_MAX, area-weighted by cos(lat).
(Xie et al. 2022, Sci Rep 12:16548, define the region only as "the Antarctic Ice Sheet";
this land-south-of-60S proxy is our explicit stand-in. Ice-shelf treatment differs across
models' sftlf — immaterial at the precision used here.)

Models: every source_id in the catalog with Amon tas for ALL of EXPERIMENTS on a regular
1-D lat/lon grid, a matching-grid sftlf, and a single member available in all experiments
(preferring MEMBER_PREF), capped at MAX_MODELS (alphabetical — no cherry-picking).
Resumable: models with an existing output CSV are skipped.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pai_series import align_sftlf_to, assert_global_plausible
import time
import warnings
import numpy as np
import pandas as pd
import xarray as xr
import gcsfs

CATALOG_URL  = "https://storage.googleapis.com/cmip6/cmip6-zarr-consolidated-stores.csv"
OUT_DIR      = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/data/cmip6_pai"
EXPERIMENTS  = ["historical", "ssp245", "ssp585"]
MEMBER_PREF  = "r1i1p1f1"
SFTLF_MIN    = 50.0      # % land fraction threshold for the AIS mask
AIS_LAT_MAX  = -60.0     # AIS proxy = land south of this latitude
MAX_MODELS   = 36
GRIDS_OK     = ("gn", "gr", "gr1", "gr2")

warnings.filterwarnings("ignore")
os.makedirs(OUT_DIR, exist_ok=True)
fs = gcsfs.GCSFileSystem(token="anon")

def openz(zstore):
    return xr.open_zarr(fs.get_mapper(zstore), consolidated=True)

def pick_member(sub):
    """Members present in ALL experiments; prefer MEMBER_PREF, else first sorted."""
    sets = [set(sub[sub.experiment_id == e].member_id) for e in EXPERIMENTS]
    common = set.intersection(*sets) if sets else set()
    if not common: return None
    return MEMBER_PREF if MEMBER_PREF in common else sorted(common)[0]

def annual_means(ds, wg, wa):
    """Month-length-weighted annual means of area-weighted global/AIS tas."""
    tas = ds["tas"]
    glob = tas.weighted(wg).mean(("lat", "lon"))
    ais  = tas.weighted(wa).mean(("lat", "lon"))
    dim  = xr.DataArray(ds.time.dt.days_in_month.values, dims="time",
                        coords={"time": ds.time})
    yr   = ds.time.dt.year
    out  = {}
    for name, series in (("tas_global", glob), ("tas_ais", ais)):
        num = (series * dim).groupby(yr).sum()
        den = dim.groupby(yr).sum()
        out[name] = (num / den).to_series()
    return pd.DataFrame(out)

print("loading catalog ...", flush=True)
cat = pd.read_csv(CATALOG_URL)
tas = cat[(cat.table_id == "Amon") & (cat.variable_id == "tas")
          & (cat.experiment_id.isin(EXPERIMENTS)) & (cat.grid_label.isin(GRIDS_OK))]
lf  = cat[(cat.variable_id == "sftlf") & (cat.grid_label.isin(GRIDS_OK))]

models = sorted(m for m in tas.source_id.unique()
                if set(EXPERIMENTS) <= set(tas[tas.source_id == m].experiment_id)
                and m in set(lf.source_id))
print(f"{len(models)} candidate models with {EXPERIMENTS} + sftlf; cap {MAX_MODELS}", flush=True)

done = 0
for model in models:
    if done >= MAX_MODELS: break
    out_csv = os.path.join(OUT_DIR, f"tas_series_{model}.csv")
    if os.path.exists(out_csv):
        print(f"SKIP {model} (exists)"); done += 1; continue
    t0 = time.time()
    try:
        sub = tas[tas.source_id == model]
        member = pick_member(sub)
        if member is None:
            print(f"PASS {model}: no common member"); continue

        # sftlf on a grid matching one of this model's tas grid_labels
        tgrids = set(sub.grid_label)
        lfsub = lf[(lf.source_id == model) & (lf.grid_label.isin(tgrids))]
        if lfsub.empty:
            print(f"PASS {model}: no matching-grid sftlf"); continue
        glabel = sorted(lfsub.grid_label)[0]
        sftlf = openz(lfsub[lfsub.grid_label == glabel].zstore.iloc[0])["sftlf"]
        if sftlf.lat.ndim != 1:
            print(f"PASS {model}: non-regular grid"); continue
        ## Some models ship sftlf with a singleton time/member dim; drop it so the mask
        ## broadcasts cleanly against tas. A no-op where there is nothing to squeeze.
        sftlf = sftlf.squeeze(drop=True)

        ## WEIGHTS ARE BUILT PER EXPERIMENT, ON THAT DATASET'S OWN COORDS.
        ## Building them once from sftlf and reusing them was a real bug: xarray's
        ## .weighted() ALIGNS on coordinate VALUES, so a lat vector differing in the
        ## last float digit silently reduces both the global mean AND the AIS mask to
        ## a partial grid -- 7.4 K on MPI-ESM1-2-LR. See python/pai_series.py.
        frames = []
        for exp in EXPERIMENTS:
            row = sub[(sub.experiment_id == exp) & (sub.member_id == member)
                      & (sub.grid_label == glabel)]
            if row.empty:  # member exists on another grid label; take any grid for this exp
                row = sub[(sub.experiment_id == exp) & (sub.member_id == member)]
            ds = openz(row.zstore.iloc[0])
            if ds.lat.ndim != 1:
                raise ValueError("non-regular tas grid")
            lf_here = align_sftlf_to(sftlf, ds, f"{model}/{exp}")
            wg = np.cos(np.deg2rad(ds.lat)) * xr.ones_like(ds.lon, dtype=float)
            wa = wg.where((lf_here >= SFTLF_MIN) & (lf_here.lat <= AIS_LAT_MAX), 0.0)
            if float(wa.sum()) == 0.0:
                raise ValueError(f"empty AIS mask ({exp})")
            df = annual_means(ds, wg, wa)
            assert_global_plausible(df.tas_global, f"{model}/{exp}")
            df["scenario"] = exp
            frames.append(df)
        allf = pd.concat(frames).reset_index().rename(columns={"index": "year", "time": "year"})
        allf.insert(1, "member", member)
        allf.to_csv(out_csv, index=False)
        done += 1
        print(f"OK   {model} ({member}, {glabel}) {len(allf)} rows in {time.time()-t0:.0f}s "
              f"[{done}/{MAX_MODELS}]", flush=True)
    except Exception as e:
        print(f"FAIL {model}: {type(e).__name__}: {e}", flush=True)

print(f"DONE: {done} models reduced -> {OUT_DIR}", flush=True)
