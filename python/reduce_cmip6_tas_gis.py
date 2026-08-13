#!/usr/bin/env python
"""Reduce CMIP6 tas to annual global-mean + GREENLAND-zone-mean series.

Greenland counterpart of python/reduce_cmip6_tas_pai.py. Feeds
python/diag_gis_amp_cmip6.py, which builds the warming-level-dependent Greenland
amplification law amp(dT) that Ladrillo 1.0 needs for projections (handoff
2026-08-12c section 1: the calibrated gis_amp is a CONSTANT fitted to the
historical record, and applying it unchanged to 2100 is almost certainly wrong).

Streams Amon tas from the public Pangeo/Google-Cloud CMIP6 zarr archive
(anonymous); nothing raw is stored -- output is one small tidy CSV per model:
  year, member, tas_global, tas_gis_south, tas_gis_all, scenario   (Kelvin)

MASK -- deliberately the SAME mask as the observed prior
    The zone weights come from build_t_gis.cell_weights: the GTN-G "Greenland
    Periphery" (o1region 05) polygon, point-in-polygon at SUBGRID^2 samples per
    cell, weighted by the Berkeley 1-deg land FRACTION and cos(lat), restricted
    to a latitude band. Importing them (rather than re-deriving) is the point:
    outputs/gis_amp_prior.csv and this file must be like-for-like or the
    CMIP6-vs-observed comparison measures the mask, not the physics.

    We use the BERKELEY land fraction rather than each model's own sftlf, again
    for like-for-like: it is the same land definition the observed prior used,
    and it is identical across models, so inter-model spread is physics and
    not land-mask convention. (reduce_cmip6_tas_pai.py used per-model sftlf
    because its Antarctic mask had no observational counterpart to match.)

    Caveat inherited from build_t_gis: this is a LAND mask, not an ice-sheet or
    ablation-zone mask.

SCENARIOS
    historical + ssp126/245/585. ssp370 is EXCLUDED deliberately -- it was
    excluded from the Antarctic analysis as an aerosol outlier with an SH
    forcing-mix confound (memory project_pai_cmip6_time_diagnostic). For
    Greenland the aerosol concern is if anything sharper, since NH sulfate
    directly cools the Greenland sector as well as the global denominator.

Models: every source_id with Amon tas for ALL of EXPERIMENTS on a regular 1-D
lat/lon grid and a single member available in all experiments (preferring
MEMBER_PREF), capped at MAX_MODELS (alphabetical -- no cherry-picking).
Resumable: models with an existing output CSV are skipped.
"""
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd
import xarray as xr
import gcsfs

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_t_gis as BTG  # mask machinery + zone definitions, imported for parity

CATALOG_URL = "https://storage.googleapis.com/cmip6/cmip6-zarr-consolidated-stores.csv"
OUT_DIR = os.path.join(BTG.REPO, "data/cmip6_gis")
EXPERIMENTS = ["historical", "ssp126", "ssp245", "ssp585"]
MEMBER_PREF = "r1i1p1f1"
MAX_MODELS = 40
GRIDS_OK = ("gn", "gr", "gr1", "gr2")

# Zones taken from build_t_gis so they cannot drift from the observed prior.
ZONE_SOUTH = BTG.ZONES["south"]      # (59, 70) -- HEADLINE, ablation-dominated
ZONE_ALL = BTG.ZONES["all"]          # (59, 84) -- pre-registered sensitivity arm

warnings.filterwarnings("ignore")
os.makedirs(OUT_DIR, exist_ok=True)
fs = gcsfs.GCSFileSystem(token="anon")


def openz(zstore):
    return xr.open_zarr(fs.get_mapper(zstore), consolidated=True)


def pick_member(sub):
    """Members present in ALL experiments; prefer MEMBER_PREF, else first sorted."""
    sets = [set(sub[sub.experiment_id == e].member_id) for e in EXPERIMENTS]
    common = set.intersection(*sets) if sets else set()
    if not common:
        return None
    return MEMBER_PREF if MEMBER_PREF in common else sorted(common)[0]


def zone_weight_da(lat, lon, rings, land_at, band):
    """build_t_gis.cell_weights on this model's grid, as an xr.DataArray."""
    w = BTG.cell_weights(np.asarray(lat), np.asarray(lon), rings, land_at,
                         band[0], band[1])
    return xr.DataArray(w, dims=("lat", "lon"), coords={"lat": lat, "lon": lon})


def annual_means(ds, weights):
    """Month-length-weighted annual means of each area-weighted spatial mean."""
    tas = ds["tas"]
    dim = xr.DataArray(ds.time.dt.days_in_month.values, dims="time",
                       coords={"time": ds.time})
    yr = ds.time.dt.year
    den = dim.groupby(yr).sum()
    out = {}
    for name, w in weights.items():
        series = tas.weighted(w).mean(("lat", "lon"))
        out[name] = ((series * dim).groupby(yr).sum() / den).to_series()
    return pd.DataFrame(out)


def main():
    print("building the Greenland mask rings (GTN-G region "
          f"{BTG.GTNG_REGION}) ...", flush=True)
    rings = BTG.region_paths(BTG.GTNG_REGION)
    land_at = BTG.berkeley_land_lookup()
    print(f"  {len(rings)} polygon rings; Berkeley land lookup ready", flush=True)

    print("loading catalog ...", flush=True)
    cat = pd.read_csv(CATALOG_URL)
    tas = cat[(cat.table_id == "Amon") & (cat.variable_id == "tas")
              & (cat.experiment_id.isin(EXPERIMENTS))
              & (cat.grid_label.isin(GRIDS_OK))]

    models = sorted(m for m in tas.source_id.unique()
                    if set(EXPERIMENTS) <= set(tas[tas.source_id == m].experiment_id))
    print(f"{len(models)} candidate models with {EXPERIMENTS}; cap {MAX_MODELS}",
          flush=True)

    done = 0
    for model in models:
        if done >= MAX_MODELS:
            break
        out_csv = os.path.join(OUT_DIR, f"tas_series_gis_{model}.csv")
        if os.path.exists(out_csv):
            print(f"SKIP {model} (exists)")
            done += 1
            continue
        t0 = time.time()
        try:
            sub = tas[tas.source_id == model]
            member = pick_member(sub)
            if member is None:
                print(f"PASS {model}: no common member", flush=True)
                continue
            glabel = sorted(set(sub[sub.member_id == member].grid_label))[0]

            ref = openz(sub[(sub.member_id == member)
                            & (sub.grid_label == glabel)].zstore.iloc[0])
            if ref.lat.ndim != 1:
                print(f"PASS {model}: non-regular grid", flush=True)
                continue
            lat, lon = ref.lat, ref.lon

            wg = (np.cos(np.deg2rad(lat)) * xr.ones_like(lon, dtype=float))
            w_south = zone_weight_da(lat, lon, rings, land_at, ZONE_SOUTH)
            w_all = zone_weight_da(lat, lon, rings, land_at, ZONE_ALL)
            if float(w_south.sum()) == 0.0:
                print(f"PASS {model}: empty southern-Greenland mask", flush=True)
                continue
            weights = {"tas_global": wg, "tas_gis_south": w_south,
                       "tas_gis_all": w_all}

            frames = []
            for exp in EXPERIMENTS:
                row = sub[(sub.experiment_id == exp) & (sub.member_id == member)
                          & (sub.grid_label == glabel)]
                if row.empty:
                    row = sub[(sub.experiment_id == exp) & (sub.member_id == member)]
                ds = openz(row.zstore.iloc[0])
                if ds.lat.ndim != 1 or len(ds.lat) != len(lat):
                    raise ValueError(f"{exp}: grid does not match the reference grid")
                df = annual_means(ds, weights)
                df["scenario"] = exp
                frames.append(df)

            allf = (pd.concat(frames).reset_index()
                    .rename(columns={"index": "year", "time": "year"}))
            allf.insert(1, "member", member)
            allf.to_csv(out_csv, index=False)
            done += 1
            print(f"OK   {model} ({member}, {glabel}) {len(allf)} rows in "
                  f"{time.time()-t0:.0f}s [{done}/{MAX_MODELS}]", flush=True)
        except Exception as e:
            print(f"FAIL {model}: {type(e).__name__}: {e}", flush=True)

    print(f"DONE: {done} models reduced -> {OUT_DIR}", flush=True)


if __name__ == "__main__":
    main()
