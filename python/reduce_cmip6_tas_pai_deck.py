#!/usr/bin/env python
"""Reduce CMIP6 DECK idealized runs for the level-vs-time amplification test.

For every model with Amon tas in ALL of {1pctCO2, abrupt-4xCO2, piControl} plus sftlf,
stream one member (1pctCO2 and abrupt-4xCO2 must share a member, preferring MEMBER_PREF;
piControl prefers the same member, else first available) and write
tas_series_deck_<model>.csv with columns year, member, scenario, tas_global, tas_ais.
`year` is YEARS SINCE BRANCH (1-based position), not nominal calendar year (nominal
epochs differ across models). abrupt-4xCO2 capped at ABRUPT_MAX_YRS; piControl at
PICTRL_YRS (used downstream only as the anomaly baseline mean — drift not removed).
Same AIS proxy as the scenario reduction: land (sftlf >= 50%) south of 60S, cos(lat)
weighted. Resumable.
"""
import glob, os, time, warnings
import numpy as np
import pandas as pd
import xarray as xr
import gcsfs

CATALOG_URL   = "https://storage.googleapis.com/cmip6/cmip6-zarr-consolidated-stores.csv"
OUT_DIR       = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/data/cmip6_pai"
EXPS          = ["1pctCO2", "abrupt-4xCO2", "piControl"]
MEMBER_PREF   = "r1i1p1f1"
ABRUPT_MAX_YRS = 300
PICTRL_YRS    = 200
SFTLF_MIN     = 50.0
AIS_LAT_MAX   = -60.0
GRIDS_OK      = ("gn", "gr", "gr1", "gr2")

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
    df = pd.DataFrame(out).reset_index(drop=True)
    df.index = df.index + 1          # years since branch, 1-based
    df.index.name = "year"
    return df

print("loading catalog ...", flush=True)
cat = pd.read_csv(CATALOG_URL)
tas = cat[(cat.table_id == "Amon") & (cat.variable_id == "tas")
          & (cat.experiment_id.isin(EXPS)) & (cat.grid_label.isin(GRIDS_OK))]
lf  = cat[(cat.variable_id == "sftlf") & (cat.grid_label.isin(GRIDS_OK))]

models = sorted(m for m in tas.source_id.unique()
                if set(EXPS) <= set(tas[tas.source_id == m].experiment_id)
                and m in set(lf.source_id))
print(f"{len(models)} candidate models with {EXPS} + sftlf", flush=True)

for model in models:
    out_csv = os.path.join(OUT_DIR, f"tas_series_deck_{model}.csv")
    if os.path.exists(out_csv):
        print(f"SKIP {model} (exists)"); continue
    t0 = time.time()
    try:
        sub = tas[tas.source_id == model]
        idl = set(sub[sub.experiment_id == "1pctCO2"].member_id) \
            & set(sub[sub.experiment_id == "abrupt-4xCO2"].member_id)
        if not idl:
            print(f"PASS {model}: no shared 1pct/abrupt member"); continue
        member = MEMBER_PREF if MEMBER_PREF in idl else sorted(idl)[0]
        pic_members = set(sub[sub.experiment_id == "piControl"].member_id)
        pic_member = member if member in pic_members else sorted(pic_members)[0]

        lfsub = lf[(lf.source_id == model) & (lf.grid_label.isin(set(sub.grid_label)))]
        if lfsub.empty:
            print(f"PASS {model}: no matching-grid sftlf"); continue
        glabel = sorted(lfsub.grid_label)[0]
        sftlf = openz(lfsub[lfsub.grid_label == glabel].zstore.iloc[0])["sftlf"]
        if sftlf.lat.ndim != 1:
            print(f"PASS {model}: non-regular grid"); continue
        wg = np.cos(np.deg2rad(sftlf.lat)) * xr.ones_like(sftlf.lon, dtype=float)
        wa = wg.where((sftlf >= SFTLF_MIN) & (sftlf.lat <= AIS_LAT_MAX), 0.0)
        if float(wa.sum()) == 0.0:
            print(f"PASS {model}: empty AIS mask"); continue

        frames = []
        for exp in EXPS:
            mem = pic_member if exp == "piControl" else member
            row = sub[(sub.experiment_id == exp) & (sub.member_id == mem)
                      & (sub.grid_label == glabel)]
            if row.empty:
                row = sub[(sub.experiment_id == exp) & (sub.member_id == mem)]
            ds = openz(row.zstore.iloc[0])
            if ds.lat.ndim != 1:
                raise ValueError(f"non-regular tas grid ({exp})")
            cap = {"abrupt-4xCO2": ABRUPT_MAX_YRS, "piControl": PICTRL_YRS}.get(exp)
            if cap is not None:
                ds = ds.isel(time=slice(0, 12 * cap))
            df = annual_means(ds, wg, wa)
            df["scenario"] = exp
            df["member"] = mem
            frames.append(df)
        allf = pd.concat(frames).reset_index()
        allf.to_csv(out_csv, index=False)
        yrs = {f.scenario.iloc[0]: len(f) for f in frames}
        print(f"OK   {model} ({member}/pic {pic_member}, {glabel}) "
              + " ".join(f"{k}:{v}" for k, v in yrs.items())
              + f" in {time.time()-t0:.0f}s", flush=True)
    except Exception as e:
        print(f"FAIL {model}: {type(e).__name__}: {e}", flush=True)
print("DONE deck reduction", flush=True)
