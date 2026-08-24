#!/usr/bin/env python
"""Re-reduce the AIS/global tas series for the two MPI models, and MEASURE the defect.

`data/cmip6_pai/tas_series_MPI-ESM1-2-{LR,HR}.csv` are corrupt: their 1850-1900
global means read 279.31 / 279.44 K against 285.5-288 K for the other 33 models,
and the error survives rebasing (handoff 2026-08-24 sec 3). The mechanism is the one
`reduce_cmip6_tas_glac.py` names in its own comment: xarray's `.weighted()` ALIGNS on
coordinate VALUES, so weights built once and reused against a dataset whose lat/lon
differ in the last float digit silently intersect to a PARTIAL grid.

`reduce_cmip6_tas_pai.py` builds BOTH weight fields -- `wg` (global) and `wa` (the AIS
mask) -- once from **sftlf**'s coordinates and then applies them to every experiment's
`tas`. So the intersection, whatever it dropped, dropped it from the AIS numerator too.
The published `tas_ais` for these two models sits inside the ensemble's range, which
LOOKS reassuring and is not evidence: the retained subset that makes a global mean 7 K
cold is one skewed hard toward cold cells, and Antarctica is where those live. Whether
the numerator is also wrong cannot be read off the CSV. THIS FILE MEASURES IT, rather
than patching the denominator and assuming the numerator was fine.

WHAT IS HELD FIXED: the AIS mask recipe (land sftlf >= SFTLF_MIN south of AIS_LAT_MAX),
the cos-lat area weighting, the month-length-weighted annual mean, the member choice
rule, and the experiment set -- all copied from `reduce_cmip6_tas_pai.py` so the ONLY
difference is the alignment. A changed recipe would make the two series incomparable and
the whole point is the difference.

THE FIX: reindex sftlf onto each experiment dataset's OWN coordinates before building
weights, per experiment. Gated three ways --
  [SHAPE] sftlf and tas must have the same grid shape; a genuine regrid is not a
          float-noise repair and must not be silently performed here.
  [DRIFT] the coordinate difference being repaired must be FLOAT NOISE (< COORD_TOL);
          a real offset means these are different grids and the repair is wrong.
  [XCHK]  our corrected global must reproduce `data/cmip6_glac/`'s independent,
          already-corrected reduction for the same model to XCHK_TOL_K. That reduction
          shares no weight-construction code path with this one, so agreement is a real
          cross-check -- unlike the advisory gate in the glac reducer, which could only
          compare against the corrupt file this script exists to replace.

  python3 python/reduce_cmip6_tas_pai_fix_mpi.py
Writes outputs/diag_pai_mpi_repair_series/tas_series_<model>.csv plus
outputs/diag_pai_mpi_repair.{csv,md}.

THIS IS A MEASUREMENT, NOT THE REPAIR PATH. The repair now lives in the reducers
themselves -- `pai_series.align_sftlf_to()` puts sftlf on each experiment dataset's own
coordinates, and `pai_series.assert_global_plausible()` is the rail that should have
caught this in the first place. Both are wired into reduce_cmip6_tas_pai.py, _deck.py and
_ext.py, which between them held SEVEN corrupt files, not two (the DECK set also caught
MPI-ESM-1-2-HAM). Pre-fix files and the full write-up:
outputs/quarantine/20260824_cmip6_pai_mpi_lat_align/.
"""
import os
import sys
import time

import numpy as np
import pandas as pd
import xarray as xr
import gcsfs

REPO         = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK"
CATALOG_URL  = "https://storage.googleapis.com/cmip6/cmip6-zarr-consolidated-stores.csv"
OLD_DIR      = os.path.join(REPO, "data/cmip6_pai")
GLAC_DIR     = os.path.join(REPO, "data/cmip6_glac")
## NOT under data/ on purpose. These series are a MEASUREMENT artefact, and the
## canonical files now live at data/cmip6_pai/ (the fix is in the reducers, via
## pai_series.align_sftlf_to). A partial second copy of two of the seven repaired
## files sitting beside the canonical directory is exactly the stale-retrieval trap
## the quarantine convention exists to prevent.
OUT_DIR      = os.path.join(REPO, "outputs/diag_pai_mpi_repair_series")
OUT_CSV      = os.path.join(REPO, "outputs/diag_pai_mpi_repair.csv")
OUT_MD       = os.path.join(REPO, "outputs/diag_pai_mpi_repair.md")

MODELS       = ["MPI-ESM1-2-LR", "MPI-ESM1-2-HR"]
EXPERIMENTS  = ["historical", "ssp245", "ssp585"]
GRIDS_OK     = ["gn", "gr", "gr1"]
MEMBER_PREF  = "r1i1p1f1"
## Copied verbatim from reduce_cmip6_tas_pai.py -- the mask recipe is held fixed.
SFTLF_MIN    = 50.0
AIS_LAT_MAX  = -60.0
## Gates. COORD_TOL is generous for float32 lat/lon stored in degrees (~1e-5 deg is
## still ~1 m); anything above it is a different grid, not a rounding difference.
COORD_TOL    = 1e-3     # degrees
XCHK_TOL_K   = 1e-6     # K; the two reductions should agree to float noise
BASELINE     = (1850, 1900)
PLAUSIBLE_K  = (284.0, 290.0)


def annual_means(ds, wg, wa):
    """Month-length-weighted annual means of area-weighted global/AIS tas.

    Verbatim from reduce_cmip6_tas_pai.py so the arithmetic is not a second variable.
    """
    tas = ds["tas"]
    glob = tas.weighted(wg).mean(("lat", "lon"))
    ais = tas.weighted(wa).mean(("lat", "lon"))
    dim = xr.DataArray(ds.time.dt.days_in_month.values, dims="time",
                       coords={"time": ds.time})
    yr = ds.time.dt.year
    out = {}
    for name, ser in (("tas_global", glob), ("tas_ais", ais)):
        out[name] = ((ser * dim).groupby(yr).sum() / dim.groupby(yr).sum()).to_series()
    return pd.DataFrame(out)


def align_report(a, b, name):
    """How many of `a`'s coordinate values an inner join against `b` would KEEP.

    This is the measurement the original reducer never made: `.weighted()` intersects
    silently, so a partial overlap looks exactly like a complete one downstream.
    """
    av, bv = np.asarray(a), np.asarray(b)
    keep = np.intersect1d(av, bv).size
    d = np.nan
    if av.shape == bv.shape:
        d = float(np.max(np.abs(av - bv)))
    return dict(coord=name, n_data=av.size, n_weight=bv.size, n_kept=keep,
                frac_kept=keep / av.size, max_abs_diff=d)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    fs = gcsfs.GCSFileSystem(token="anon")

    def openz(z):
        return xr.open_zarr(fs.get_mapper(z), consolidated=True)

    print("loading catalog ...", flush=True)
    cat = pd.read_csv(CATALOG_URL)
    tas = cat[(cat.table_id == "Amon") & (cat.variable_id == "tas")
              & (cat.experiment_id.isin(EXPERIMENTS))
              & (cat.grid_label.isin(GRIDS_OK))]
    lf = cat[(cat.variable_id == "sftlf") & (cat.grid_label.isin(GRIDS_OK))]

    align_rows, summary_rows = [], []
    for model in MODELS:
        t0 = time.time()
        sub = tas[tas.source_id == model]
        sets = [set(sub[sub.experiment_id == e].member_id) for e in EXPERIMENTS]
        common = set.intersection(*sets) if sets else set()
        if not common:
            raise SystemExit(f"{model}: no common member across {EXPERIMENTS}")
        member = MEMBER_PREF if MEMBER_PREF in common else sorted(common)[0]

        tgrids = set(sub.grid_label)
        lfsub = lf[(lf.source_id == model) & (lf.grid_label.isin(tgrids))]
        if lfsub.empty:
            raise SystemExit(f"{model}: no matching-grid sftlf")
        glabel = sorted(lfsub.grid_label)[0]
        sftlf = openz(lfsub[lfsub.grid_label == glabel].zstore.iloc[0])["sftlf"]
        if sftlf.lat.ndim != 1:
            raise SystemExit(f"{model}: non-regular sftlf grid")
        ## sftlf itself may carry a member/time singleton; squeeze to (lat, lon).
        sftlf = sftlf.squeeze(drop=True)

        frames = []
        for exp in EXPERIMENTS:
            row = sub[(sub.experiment_id == exp) & (sub.member_id == member)
                      & (sub.grid_label == glabel)]
            if row.empty:
                row = sub[(sub.experiment_id == exp) & (sub.member_id == member)]
            ds = openz(row.zstore.iloc[0])
            if ds.lat.ndim != 1:
                raise SystemExit(f"{model}/{exp}: non-regular tas grid")

            for c in ("lat", "lon"):
                r = align_report(ds[c].values, sftlf[c].values, c)
                r.update(model=model, experiment=exp)
                align_rows.append(r)
                print(f"  [align] {model} {exp} {c}: "
                      f"{r['n_kept']}/{r['n_data']} kept ({100*r['frac_kept']:.1f}%), "
                      f"max|diff| {r['max_abs_diff']:.3e}", flush=True)
                ## [SHAPE]
                if r["n_data"] != r["n_weight"]:
                    raise SystemExit(f"{model}/{exp}: {c} sftlf has {r['n_weight']} "
                                     f"points, tas has {r['n_data']} -- different "
                                     f"grids, not a float-noise repair")
                ## [DRIFT]
                if not (r["max_abs_diff"] < COORD_TOL):
                    raise SystemExit(f"{model}/{exp}: {c} differs by "
                                     f"{r['max_abs_diff']:.3e} deg > {COORD_TOL} -- "
                                     f"a real offset, so reindexing would MOVE the mask")

            ## THE REPAIR: put sftlf on THIS dataset's own coordinate values, so the
            ## inner join `.weighted()` performs is the identity.
            lf_here = sftlf.assign_coords(lat=ds.lat.values, lon=ds.lon.values)
            wg = np.cos(np.deg2rad(ds.lat)) * xr.ones_like(ds.lon, dtype=float)
            mask = (lf_here >= SFTLF_MIN) & (lf_here.lat <= AIS_LAT_MAX)
            wa = wg.where(mask, 0.0)
            if float(wa.sum()) == 0.0:
                raise SystemExit(f"{model}/{exp}: empty AIS mask after repair")

            df = annual_means(ds, wg, wa)
            df["scenario"] = exp
            frames.append(df)

        allf = pd.concat(frames).reset_index().rename(columns={"index": "year",
                                                               "time": "year"})
        allf.insert(1, "member", member)
        out_csv = os.path.join(OUT_DIR, f"tas_series_{model}.csv")
        allf.to_csv(out_csv, index=False)

        h = allf[(allf.scenario == "historical") & allf.year.between(*BASELINE)]
        gm, am = float(h.tas_global.mean()), float(h.tas_ais.mean())
        old = pd.read_csv(os.path.join(OLD_DIR, f"tas_series_{model}.csv"))
        ho = old[(old.scenario == "historical") & old.year.between(*BASELINE)]
        gm_old, am_old = float(ho.tas_global.mean()), float(ho.tas_ais.mean())
        glac = pd.read_csv(os.path.join(GLAC_DIR, f"tas_series_glac_{model}.csv"))
        hgl = glac[(glac.scenario == "historical") & glac.year.between(*BASELINE)]
        gm_glac = float(hgl.tas_global.mean())

        if not (PLAUSIBLE_K[0] <= gm <= PLAUSIBLE_K[1]):
            raise SystemExit(f"{model}: repaired global {gm:.2f} K outside {PLAUSIBLE_K}")
        ## [XCHK] -- a REAL cross-check: `data/cmip6_glac` was reduced by a separate
        ## script with its own weight construction and no sftlf at all.
        if abs(gm - gm_glac) > XCHK_TOL_K:
            raise SystemExit(f"{model}: repaired global {gm:.6f} K disagrees with the "
                             f"independent glac reduction {gm_glac:.6f} K by "
                             f"{abs(gm-gm_glac):.2e} > {XCHK_TOL_K}")

        summary_rows.append(dict(model=model, member=member, grid_label=glabel,
                                 glob_old=gm_old, glob_fix=gm, glob_glac=gm_glac,
                                 glob_delta=gm - gm_old,
                                 ais_old=am_old, ais_fix=am, ais_delta=am - am_old,
                                 rows=len(allf)))
        print(f"OK   {model} ({member}, {glabel}) global {gm_old:.2f} -> {gm:.2f} K, "
              f"AIS {am_old:.2f} -> {am:.2f} K, {len(allf)} rows "
              f"in {time.time()-t0:.0f}s", flush=True)

    S = pd.DataFrame(summary_rows)
    A = pd.DataFrame(align_rows)
    S.to_csv(OUT_CSV, index=False)
    with open(OUT_MD, "w") as fh:
        fh.write("# MPI PAI reduction — repair and measurement\n\n")
        fh.write(f"Mask recipe held fixed: sftlf >= {SFTLF_MIN}% south of "
                 f"{AIS_LAT_MAX} deg; baseline {BASELINE[0]}-{BASELINE[1]}.\n\n")
        fh.write("## Coordinate overlap the original reduction silently used\n\n")
        fh.write(A[["model", "experiment", "coord", "n_data", "n_kept", "frac_kept",
                    "max_abs_diff"]].to_markdown(index=False, floatfmt=".4g") + "\n\n")
        fh.write("## Baseline means, K\n\n")
        fh.write(S.to_markdown(index=False, floatfmt=".4f") + "\n")
    print(f"\nwrote {os.path.relpath(OUT_CSV, REPO)} and {os.path.relpath(OUT_MD, REPO)}")
    print(S.to_string(index=False))


if __name__ == "__main__":
    main()
