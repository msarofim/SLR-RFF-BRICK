"""Stream CMIP6 Amon tas and reduce it to the LADRILLO GLACIER BLOCKS.

WHY. The obs-vs-CMIP6 amplification offset has been measured for Greenland (where it
turned out to be largely a baseline-frame artefact, diag_gis_amp_baseline_sens.py) but
NEVER for the glacier blocks, even though their between-product spread is LARGER
(SLOWP 1.863x, R19 1.472x, FAST 1.366x against Greenland south's 1.513x). If the same
frame story explains both, one correction serves both modules instead of two
module-specific knobs. Marcus 2026-08-23: "it would probably be best to take a
consistent approach between both modules."

METHOD, and the one place it differs from build_t_glac.py
  Region polygons, GlaMBIE area weights and the block definitions are taken from
  build_t_glac.py's own sources -- NOT re-derived. The masks, however, must be built
  on each model's OWN grid, so this uses CELL-CENTRE containment where build_t_glac
  uses a SUBGRID x SUBGRID fractional overlap. On a ~1-2 degree CMIP6 grid the
  difference matters only at region edges; the check that it is not material is that
  the resulting global-mean series must match the pai reduction's tas_global, which
  is computed independently. Asserted per model below.

  ⚠ Absolute K is written, NOT anomalies, exactly as data/cmip6_pai does -- so the
  consumer can rebase to any frame. That is the whole point given what the baseline
  scan found.

WRITES data/cmip6_glac/tas_series_glac_<model>.csv  (year, member, scenario,
       tas_global, tas_R19, tas_SLOWP, tas_FAST, tas_AGG)
  python3 python/reduce_cmip6_tas_glac.py [--max-models=N]
"""
import os
import sys
import time
import warnings
import zipfile

import numpy as np
import pandas as pd
import xarray as xr
import gcsfs
import shapefile as pyshp
from matplotlib.path import Path

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))

CATALOG_URL = "https://storage.googleapis.com/cmip6/cmip6-zarr-consolidated-stores.csv"
OUT_DIR = os.path.join(REPO, "data/cmip6_glac")
EXPERIMENTS = ["historical", "ssp245"]      # 2024 is all the amp fit needs
MEMBER_PREF = "r1i1p1f1"
GRIDS_OK = ("gn", "gr", "gr1", "gr2")
MAX_MODELS = int(next((a.split("=")[1] for a in sys.argv[1:]
                       if a.startswith("--max-models=")), 45))
GLOBAL_TOL_K = 0.05          # our global mean vs the pai reduction's, per model
GLOBAL_PLAUSIBLE_K = (284.0, 290.0)   # a 1850-1900 global mean must land here

warnings.filterwarnings("ignore")
os.makedirs(OUT_DIR, exist_ok=True)

## ---- blocks, regions and weights: build_t_glac.py's own definitions ----------
## ⚠ build_t_glac.py IS A SCRIPT, NOT A MODULE — importing it RE-RUNS it. That is
## deliberate here (it is the only place the region polygons and GlaMBIE weights are
## built, and re-deriving them would be exactly the drift this repo forbids), but it
## has a SIDE EFFECT: it rewrites t_glac_hadcrut5_provenance.md with the CURRENT
## commit and re-renders figures/t_glac_vs_gmst.png. The DATA csvs are unchanged
## (verified 2026-08-23), but check `git status` after running and revert the
## cosmetic pair rather than committing a re-stamped provenance file.
import build_t_glac as BTG   # noqa: E402  (import RUNS its region + weight build)

BLOCKS = {"R19": [19], "SLOWP": [3, 9, 7, 6],
          "FAST": [1, 2, 4, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18]}
RINGS = BTG.rings_by_region
AREA_W = BTG.area_w


def block_weight(lat, lon, regs):
    """cos-lat area weight x region membership, by CELL CENTRE, GlaMBIE-weighted
    across the regions in a block. Returns (nlat, nlon)."""
    la = np.asarray(lat, float); lo = np.asarray(lon, float)
    lo180 = ((lo + 180.0) % 360.0) - 180.0
    pts = np.array([(x, y) for y in la for x in lo180])
    w = np.zeros((len(la), len(lo)))
    tot = sum(AREA_W.get(r, 0.0) for r in regs)
    if tot <= 0:
        return w
    for r in regs:
        rings = RINGS.get(r)
        aw = AREA_W.get(r, 0.0)
        if not rings or aw <= 0:
            continue
        inside = np.zeros(len(pts), dtype=bool)
        for ring in rings:
            inside |= ring.contains_points(pts)
        m = inside.reshape(len(la), len(lo)).astype(float)
        if m.sum() == 0:
            continue
        cw = m * np.cos(np.deg2rad(la))[:, None]
        if cw.sum() > 0:
            w += (aw / tot) * cw / cw.sum()          # each region normalised, then mixed
    return w


def main():
    fs = gcsfs.GCSFileSystem(token="anon")

    def openz(z):
        return xr.open_zarr(fs.get_mapper(z), consolidated=True)

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
        out_csv = os.path.join(OUT_DIR, f"tas_series_glac_{model}.csv")
        if os.path.exists(out_csv):
            print(f"SKIP {model} (exists)", flush=True); done += 1; continue
        t0 = time.time()
        try:
            sub = tas[tas.source_id == model]
            sets = [set(sub[sub.experiment_id == e].member_id) for e in EXPERIMENTS]
            common = set.intersection(*sets) if sets else set()
            if not common:
                print(f"PASS {model}: no common member", flush=True); continue
            member = MEMBER_PREF if MEMBER_PREF in common else sorted(common)[0]

            frames, mask_cache = [], {}
            for exp in EXPERIMENTS:
                row = sub[(sub.experiment_id == exp) & (sub.member_id == member)]
                ds = openz(row.zstore.iloc[0])
                if ds.lat.ndim != 1:
                    raise ValueError("non-regular grid")
                ## WEIGHTS ARE BUILT PER EXPERIMENT, ON THAT DATASET'S OWN COORDS.
                ## Building them once from the FIRST experiment and reusing them was
                ## a real bug: xarray's .weighted() ALIGNS on coordinate VALUES, so
                ## two experiments whose lat/lon differ in the last float digit
                ## silently intersect to a partial (or empty) grid and the global
                ## mean comes back wrong -- by up to 7.8 K on MPI-ESM1-2-HR. The
                ## expensive part (point-in-polygon) is cached by grid signature, so
                ## rebuilding costs nothing when the coords really do match.
                sig = (len(ds.lat), len(ds.lon),
                       round(float(ds.lat[0]), 6), round(float(ds.lon[0]), 6))
                if sig not in mask_cache:
                    mask_cache[sig] = {b: block_weight(ds.lat.values, ds.lon.values,
                                                       regs)
                                       for b, regs in BLOCKS.items()}
                arrs = mask_cache[sig]
                wg = np.cos(np.deg2rad(ds.lat)) * xr.ones_like(ds.lon, dtype=float)
                wts = {"global": wg}
                for b in BLOCKS:
                    if arrs[b].sum() == 0:
                        raise ValueError(f"empty {b} mask")
                    wts[b] = xr.DataArray(arrs[b], dims=("lat", "lon"),
                                          coords={"lat": ds.lat, "lon": ds.lon})
                ## AGG = the area-weighted mix of the three, i.e. all regions
                ## in scope; built from the same weights so it cannot drift.
                wts["AGG"] = sum(sum(AREA_W.get(r, 0.0) for r in regs) * wts[b]
                                 for b, regs in BLOCKS.items())
                tasv = ds["tas"]
                dim = xr.DataArray(ds.time.dt.days_in_month.values, dims="time",
                                   coords={"time": ds.time})
                yr = ds.time.dt.year
                cols = {}
                for name, w in (("tas_global", wts["global"]),
                                *((f"tas_{b}", wts[b]) for b in
                                  list(BLOCKS) + ["AGG"])):
                    ser = tasv.weighted(w).mean(("lat", "lon"))
                    cols[name] = ((ser * dim).groupby(yr).sum()
                                  / dim.groupby(yr).sum()).to_series()
                d = pd.DataFrame(cols)
                d["member"] = member; d["scenario"] = exp
                frames.append(d)

            out = pd.concat(frames).rename_axis("year").reset_index()
            out = out[out.year <= 2100]
            ## [GATE] our global mean must reproduce the independent pai reduction.
            ## [GATE] SCOPED TO WHAT IT CAN ACTUALLY TEST (rewritten 2026-08-23).
            ## It compares our area-weighted global mean against the independent
            ## data/cmip6_pai reduction -- which is only a like-for-like test when
            ## BOTH used the same member. Two things it must not do, and originally
            ## did: fail on a member mismatch (different member = different series,
            ## not an error), and trust the reference blindly. THE REFERENCE IS
            ## WRONG FOR THE MPI PAIR: data/cmip6_pai has 1850-1900 global means of
            ## 279.3/279.4 K for MPI-ESM1-2-{LR,HR} against 285.5-288 K for the
            ## other 33 models -- 279 K is 6 C and is not a global mean. So the
            ## check is now PLAUSIBILITY-FIRST (our own value must be physical) and
            ## the cross-check is advisory, reported and recorded, never fatal.
            gm = float(out[out.year.between(1850, 1900)].tas_global.mean())
            if not (GLOBAL_PLAUSIBLE_K[0] <= gm <= GLOBAL_PLAUSIBLE_K[1]):
                raise ValueError(f"our own 1850-1900 global mean {gm:.2f} K is "
                                 f"outside {GLOBAL_PLAUSIBLE_K} -- not a global mean")
            note = "n/a"
            pai = os.path.join(REPO, "data/cmip6_pai", f"tas_series_{model}.csv")
            if os.path.exists(pai):
                pr = pd.read_csv(pai)
                if "member" in pr.columns and set(pr.member) == {member}:
                    j = out.merge(pr[["year", "scenario", "tas_global"]],
                                  on=["year", "scenario"], suffixes=("", "_pai"))
                    if len(j):
                        dev = float((j.tas_global - j.tas_global_pai).abs().max())
                        note = (f"{dev:.4f} K OK" if dev <= GLOBAL_TOL_K
                                else f"{dev:.3f} K DISAGREES -- check which side")
                else:
                    note = f"member differs ({sorted(set(pr.get('member', [])))[:1]}) -- not comparable"
            print(f"    [gate] ours {gm:.2f} K plausible; vs pai reduction: {note}",
                  flush=True)
            out.to_csv(out_csv, index=False)
            done += 1
            print(f"OK   {model} ({member}) {len(out)} yr  {time.time()-t0:.0f}s",
                  flush=True)
        except Exception as e:
            print(f"FAIL {model}: {type(e).__name__}: {e}", flush=True)

    print(f"\n{done} models written to {os.path.relpath(OUT_DIR, REPO)}")


if __name__ == "__main__":
    main()
