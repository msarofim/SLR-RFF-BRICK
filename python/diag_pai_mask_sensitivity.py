#!/usr/bin/env python
"""Mask-sensitivity check for the PAI diagnostic: does the region definition explain the
~+0.15 offset of our full-window PAI1 vs Xie et al. 2022 (0.95 ssp245 / 1.03 ssp585)?

Computes full-window (2015-2100) PAI1 = trend(T_region)/trend(T_global) for N_TEST
diverse models under three Antarctic masks:
  land60 : land (sftlf>=50%) south of 60S   (the diagnostic's AIS proxy)
  cap60  : ALL points south of 60S (incl. Southern Ocean)
  cap66  : ALL points south of the Antarctic Circle (66.5S)
Streams tas once per model-scenario and reduces all masks in the same pass.
"""
import warnings
import numpy as np
import pandas as pd
import xarray as xr
import gcsfs

CATALOG_URL = "https://storage.googleapis.com/cmip6/cmip6-zarr-consolidated-stores.csv"
TEST_MODELS = ["ACCESS-ESM1-5", "CESM2", "CanESM5", "GFDL-ESM4", "MIROC6", "UKESM1-0-LL"]
EXPERIMENTS = ["historical", "ssp245", "ssp585"]
MEMBER_PREF = "r1i1p1f1"
SFTLF_MIN   = 50.0
WINDOW      = (2015, 2100)
GRIDS_OK    = ("gn", "gr", "gr1", "gr2")

warnings.filterwarnings("ignore")
fs = gcsfs.GCSFileSystem(token="anon")
openz = lambda z: xr.open_zarr(fs.get_mapper(z), consolidated=True)
cat = pd.read_csv(CATALOG_URL)
tas = cat[(cat.table_id == "Amon") & (cat.variable_id == "tas")
          & (cat.experiment_id.isin(EXPERIMENTS)) & (cat.grid_label.isin(GRIDS_OK))]
lf  = cat[(cat.variable_id == "sftlf") & (cat.grid_label.isin(GRIDS_OK))]
trend = lambda y: np.polyfit(np.arange(len(y)), y, 1)[0]

rows = []
for model in TEST_MODELS:
    sub = tas[tas.source_id == model]
    common = set.intersection(*[set(sub[sub.experiment_id == e].member_id) for e in EXPERIMENTS])
    member = MEMBER_PREF if MEMBER_PREF in common else sorted(common)[0]
    lfsub = lf[(lf.source_id == model) & (lf.grid_label.isin(set(sub.grid_label)))]
    glabel = sorted(lfsub.grid_label)[0]
    sftlf = openz(lfsub[lfsub.grid_label == glabel].zstore.iloc[0])["sftlf"]
    wg = np.cos(np.deg2rad(sftlf.lat)) * xr.ones_like(sftlf.lon, dtype=float)
    masks = {"land60": wg.where((sftlf >= SFTLF_MIN) & (sftlf.lat <= -60), 0.0),
             "cap60":  wg.where(sftlf.lat <= -60.0, 0.0),
             "cap66":  wg.where(sftlf.lat <= -66.5, 0.0)}
    ann = {}
    for exp in EXPERIMENTS:
        row = sub[(sub.experiment_id == exp) & (sub.member_id == member)
                  & (sub.grid_label == glabel)]
        if row.empty:
            row = sub[(sub.experiment_id == exp) & (sub.member_id == member)]
        ds = openz(row.zstore.iloc[0])
        dim = xr.DataArray(ds.time.dt.days_in_month.values, dims="time", coords={"time": ds.time})
        yr = ds.time.dt.year
        d = {}
        for name, w in [("glob", wg)] + list(masks.items()):
            s = ds["tas"].weighted(w).mean(("lat", "lon"))
            d[name] = ((s * dim).groupby(yr).sum() / dim.groupby(yr).sum()).to_series()
        ann[exp] = pd.DataFrame(d)
    for sc in ("ssp245", "ssp585"):
        s = pd.concat([ann["historical"], ann[sc]]).sort_index().loc[WINDOW[0]:WINDOW[1]]
        for mk in masks:
            rows.append(dict(model=model, scenario=sc, mask=mk,
                             pai=trend(s[mk].values) / trend(s["glob"].values)))
    print(f"done {model}", flush=True)

df = pd.DataFrame(rows)
piv = df.pivot_table(index="mask", columns="scenario", values="pai", aggfunc="mean")
print(f"\nfull-window {WINDOW} PAI1, mean over {len(TEST_MODELS)} models:")
print(piv.round(3).to_string())
print("\nXie et al. 2022 Table 1: ssp245 0.95, ssp585 1.03")
df.to_csv("/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/outputs/diag_pai_mask_sensitivity.csv", index=False)
