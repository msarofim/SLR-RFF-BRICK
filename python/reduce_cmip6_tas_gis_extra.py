"""Fetch NAMED extra CMIP6 models into a SEPARATE directory, reusing
reduce_cmip6_tas_gis.py's own mask and reduction machinery unchanged.

WHY THIS IS A SEPARATE SCRIPT AND A SEPARATE DIRECTORY
  reduce_cmip6_tas_gis.py caps at MAX_MODELS = 40 ALPHABETICALLY, and the list stops
  at NorESM2-MM. UKESM1-0-LL was therefore never fetched -- not a data problem, a cap.
  But diag_gis_amp_cmip6.py builds the SHIPPED amplification law by GLOBbing
  data/cmip6_gis/tas_series_gis_*.csv (line 275), so dropping a 41st file into that
  directory would silently change gis_amp_shape.csv the next time anyone re-derived it.
  The reducer's own EXISTING_ONLY pin exists for exactly this reason.

  So: identical machinery, DIFFERENT directory. The shipped 40-model panel and every
  product built from it are untouched and still reproduce. Consumers that WANT the
  extra models must opt in by looking here explicitly.

WHY UKESM1-0-LL SPECIFICALLY, and why this is not cherry-picking
  It is the forcing GCM behind UKESM1-0-LL-Robin, one of the five GCMs in the PROTECT
  ssp585 r2300 arm, and the arm's HIGHEST member (106.7 cm at 2300). It is fetched
  because PROTECT used it, i.e. on a like-for-like requirement fixed before any result
  was seen -- not because of anything about its values. That distinction is the whole
  reason the parent reducer sorts alphabetically, so it is worth stating.

  NOTE UKESM1-0-LL has NO r1i1p1f1 -- it is an f2-forcing model -- so the parent's
  MEMBER_PREF cannot match and pick_member() falls through to sorted(common)[0]. That
  is the parent's own documented fallback, used unchanged.

  Post-2100 is NOT available here and is NOT needed: the r2300 arms hold forcing at
  the 2081-2100 mean [[pangeo_cmip6_no_ext]].

  python3 python/reduce_cmip6_tas_gis_extra.py [MODEL ...]
"""
import os
import sys
import time

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))

import build_t_gis as BTG  # noqa: E402
import reduce_cmip6_tas_gis as RED  # noqa: E402

# --- named constants ---------------------------------------------------------
OUT_DIR = os.path.join(REPO, "data/cmip6_gis_extra")
SHIPPED_DIR = RED.OUT_DIR
## Named, with the reason, so the file records WHY each extra model is here.
WANTED = {"UKESM1-0-LL": "PROTECT ssp585 r2300 forcing GCM (UKESM1-0-LL-Robin); "
                         "the arm's highest member, 106.7 cm at 2300"}
EXPERIMENTS = RED.EXPERIMENTS
EXPECTED_COLS = RED.EXPECTED_COLS


def main():
    models = sys.argv[1:] or sorted(WANTED)
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"reduce_cmip6_tas_gis_extra — {len(models)} named model(s) into "
          f"{os.path.relpath(OUT_DIR, REPO)}")
    print(f"  shipped panel at {os.path.relpath(SHIPPED_DIR, REPO)} "
          f"({len(os.listdir(SHIPPED_DIR))} files) is NOT touched.\n")
    for m in models:
        print(f"  {m}: {WANTED.get(m, 'requested on the command line')}")

    print("\nbuilding the Greenland mask rings (GTN-G region "
          f"{BTG.GTNG_REGION}) — imported from build_t_gis, so the mask is "
          "bit-identical to the shipped panel's ...", flush=True)
    rings = BTG.region_paths(BTG.GTNG_REGION)
    land_at = BTG.berkeley_land_lookup()

    cat = pd.read_csv(RED.CATALOG_URL)
    tas = cat[(cat.table_id == "Amon") & (cat.variable_id == "tas")
              & (cat.experiment_id.isin(EXPERIMENTS))
              & (cat.grid_label.isin(RED.GRIDS_OK))]

    for model in models:
        out = os.path.join(OUT_DIR, f"tas_series_gis_{model}.csv")
        clash = os.path.join(SHIPPED_DIR, f"tas_series_gis_{model}.csv")
        if os.path.exists(clash):
            print(f"\nSKIP {model}: already in the SHIPPED panel — use that one, "
                  f"not a second copy.")
            continue
        if os.path.exists(out):
            print(f"\nSKIP {model}: already fetched at "
                  f"{os.path.relpath(out, REPO)}")
            continue
        sub = tas[tas.source_id == model]
        if not set(EXPERIMENTS) <= set(sub.experiment_id):
            print(f"\nPASS {model}: missing "
                  f"{sorted(set(EXPERIMENTS) - set(sub.experiment_id))}")
            continue
        mem = RED.pick_member(sub)
        if mem is None:
            print(f"\nPASS {model}: no member common to all of {EXPERIMENTS}")
            continue
        print(f"\n{model}: member {mem} "
              f"({'MEMBER_PREF' if mem == RED.MEMBER_PREF else 'fallback sorted(common)[0]'})",
              flush=True)
        t0 = time.time()
        frames, weights = [], None
        for exp in EXPERIMENTS:
            row = sub[(sub.experiment_id == exp) & (sub.member_id == mem)]
            if row.empty:
                print(f"  PASS: no {exp} for {mem}")
                frames = None
                break
            ds = RED.openz(sorted(row.zstore)[0])
            if ds.lat.ndim != 1 or ds.lon.ndim != 1:
                print(f"  PASS {model}: non-regular grid")
                frames = None
                break
            if weights is None:
                weights = {
                    "tas_gis_south": RED.zone_weight_da(ds.lat, ds.lon, rings,
                                                        land_at, RED.ZONE_SOUTH),
                    "tas_gis_all": RED.zone_weight_da(ds.lat, ds.lon, rings,
                                                      land_at, RED.ZONE_ALL),
                    "tas_gis_central": RED.zone_weight_da(ds.lat, ds.lon, rings,
                                                          land_at, RED.ZONE_CENTRAL),
                    "tas_gis_north": RED.zone_weight_da(ds.lat, ds.lon, rings,
                                                        land_at, RED.ZONE_NORTH),
                }
                w = np.cos(np.deg2rad(ds.lat))
                weights["tas_global"] = w.broadcast_like(ds["tas"].isel(time=0))
            df = RED.annual_means(ds, weights)
            df["scenario"] = exp
            df["member"] = mem
            df.index.name = "year"
            frames.append(df.reset_index())
            print(f"  {exp}: {len(df)} yr, to {int(df.index.max())} "
                  f"[{time.time() - t0:.0f}s]", flush=True)
        if not frames:
            continue
        d = pd.concat(frames, ignore_index=True)[EXPECTED_COLS]
        d.to_csv(out, index=False)
        print(f"  wrote {os.path.relpath(out, REPO)}  ({len(d)} rows, "
              f"{time.time() - t0:.0f}s)")

    print(f"\nDONE. Consumers must opt in to {os.path.relpath(OUT_DIR, REPO)} "
          f"explicitly;\nanything globbing {os.path.relpath(SHIPPED_DIR, REPO)} is "
          f"unchanged and still reproduces.")


if __name__ == "__main__":
    main()
