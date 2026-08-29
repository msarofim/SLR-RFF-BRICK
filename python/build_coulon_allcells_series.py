"""
build_coulon_allcells_series.py

The ALL-CELLS companion to data/cmip6_coulon/, so the Coulon comparison can be
bounded on the INTEGRAL under BOTH averaging domains — Marcus's [DECIDED]
2026-08-29 option (c), "report both domains as a bound".

WRITES data/cmip6_coulon_allcells/tas_series_<model>.csv, schema identical to
data/cmip6_coulon/ (year, member, tas_global, tas_ais, scenario; Kelvin).
⚠ A SEPARATE DIRECTORY, ON PURPOSE, and the land-mask files are NEVER touched:
the ruling is to report both, not to replace one with the other.

⚠ WHY THIS IS NOT "a one-line constant change in the reducer". That framing
holds only for the post-2100 leg. `reduce_cmip6_tas_coulon.py` takes its <=2100
leg from data/cmip6_pai/tas_series_<model>.csv, WHICH IS ALREADY REDUCED UNDER
THE LAND MASK, and only UKESM1-0-LL is rebuilt end to end from NetCDF. Flipping
SFTLF_MIN there would splice an all-cells tail onto a land-masked baseline for
IPSL / CESM2-WACCM / MRI. This script therefore re-reduces the <=2100 leg from
the Pangeo zarr under the all-cells mask, and only the post-2100 leg comes from
the local ESGF NetCDFs.

(The published endpoint table is NOT affected by that trap — verified 2026-08-29
by diag_coulon_mask_consistency.py, which reproduces both of its columns exactly
from a consistently-masked calculation.)

REDUCTION CONVENTION, matching reduce_cmip6_tas_coulon.py except for the mask:
cos(lat) global weights; AIS = every surface type south of -60 deg, cos(lat)
weighted; month-length-weighted annual means; weights rebuilt PER DATASET on its
own coords via pai_series.align_sftlf_to.

⚠ PORTABILITY, both of which crash rather than mislead if ignored: UKESM is on a
360-day calendar where a "YYYY-12-31" slice bound is an invalid date, and Pangeo
returns numpy.datetime64 for MRI-ESM2-0 but cftime objects for the 360-day
models — so years come from xarray's .dt.year accessor, never a comprehension.

  source ~/climate-env/bin/activate && python python/build_coulon_allcells_series.py
"""
import os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd, xarray as xr, gcsfs
from pai_series import align_sftlf_to, assert_global_plausible

REPO    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT     = "https://storage.googleapis.com/cmip6/cmip6-zarr-consolidated-stores.csv"
EXT     = os.path.join(REPO, "data/cmip6_coulon_ext")
OUT_DIR = os.path.join(REPO, "data/cmip6_coulon_allcells")
LAT_MAX = -60.0
SPLICE_YEAR = 2100
MEMBERS = {"MRI-ESM2-0": "r1i1p1f1", "CESM2-WACCM": "r1i1p1f1",
           "IPSL-CM6A-LR": "r1i1p1f1", "UKESM1-0-LL": "r4i1p1f2"}
SCENARIOS = ["historical", "ssp585", "ssp126"]


def weights(ds, sftlf, label):
    lf = align_sftlf_to(sftlf, ds, label)
    wg = np.cos(np.deg2rad(ds.lat)) * xr.ones_like(ds.lon, dtype=float)
    wa = wg.where(lf.lat <= LAT_MAX, 0.0)          # ALL surface types
    if float(wa.sum()) == 0.0:
        sys.exit(f"ERROR: {label}: empty AIS mask")
    return wg, wa


def annual(ds, wg, wa):
    """Month-length-weighted annual means, VECTORISED.

    ⚠ The obvious loop -- group the time index by year and .isel each group --
    issues one lazy read PER YEAR against the zarr store, ~165 round trips per
    scenario, and is minutes slower than the whole rest of the reduction. Load
    once, then reduce in memory: the largest of these is ~0.5 GB.
    """
    ds = ds[["tas"]].load()
    w = ds["time"].dt.days_in_month
    num = (ds.tas * w).groupby(ds["time"].dt.year).sum("time")
    den = w.groupby(ds["time"].dt.year).sum("time")
    m = num / den
    # a partial year would be silently mis-weighted, so drop it rather than pad
    n = ds["time"].dt.year.groupby(ds["time"].dt.year).count()
    keep = n.where(n == 12, drop=True).year
    m = m.sel(year=keep)
    g = (m * wg).sum(("lat", "lon")) / wg.sum(("lat", "lon"))
    a = (m * wa).sum(("lat", "lon")) / wa.sum(("lat", "lon"))
    return pd.DataFrame({"tas_global": g.values, "tas_ais": a.values},
                        index=pd.Index(m.year.values.astype(int), name="year"))


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=",".join(MEMBERS),
                    help="subset to build; default all four")
    want = [m.strip() for m in ap.parse_args().models.split(",")]
    os.makedirs(OUT_DIR, exist_ok=True)
    cat = pd.read_csv(CAT); fs = gcsfs.GCSFileSystem(token="anon")
    for model, mem in MEMBERS.items():
        if model not in want:
            continue
        print(f"\n── {model} ({mem})", flush=True)
        lr = cat[(cat.variable_id == "sftlf") & (cat.source_id == model)]
        if lr.empty:
            print("   no sftlf; SKIPPED"); continue
        sftlf = xr.open_zarr(fs.get_mapper(lr.zstore.iloc[0]), consolidated=True)["sftlf"].squeeze(drop=True)
        frames = []
        for exp in SCENARIOS:
            # <= 2100 from the zarr, re-reduced under the all-cells mask
            q = cat[(cat.variable_id == "tas") & (cat.table_id == "Amon")
                    & (cat.source_id == model) & (cat.experiment_id == exp)
                    & (cat.member_id == mem)]
            piece = None
            if not q.empty:
                ds = xr.open_zarr(fs.get_mapper(q.zstore.iloc[0]), consolidated=True)
                wg, wa = weights(ds, sftlf, f"{model}/{exp}")
                piece = annual(ds, wg, wa)
                piece = piece[piece.index <= SPLICE_YEAR]
                assert_global_plausible(piece.tas_global, f"{model}/{exp}")
                print(f"   {exp:<11} zarr   {piece.index.min()}-{piece.index.max()}", flush=True)
            # > 2100 from the local ESGF NetCDFs
            pats = sorted(glob.glob(os.path.join(EXT, f"tas_Amon_{model}_{exp}_{mem}_*.nc")))
            if pats:
                parts = [xr.open_dataset(p, decode_times=xr.coders.CFDatetimeCoder(use_cftime=True))[["tas"]]
                         for p in pats]
                de = xr.concat(parts, dim="time") if len(parts) > 1 else parts[0]
                wg2, wa2 = weights(de, sftlf, f"{model}/{exp}/ext")
                ext = annual(de, wg2, wa2)
                ext = ext[ext.index > SPLICE_YEAR] if piece is not None else ext
                # ⚠ UKESM holds a LOCAL historical NetCDF as well as post-2100 ssp
                # files. Filtered to >2100 that slice is EMPTY, and an empty frame
                # reaches assert_global_plausible as a nan mean — which reports a
                # "coordinate mismatch" and sends you hunting the wrong bug. There
                # is simply no post-2100 leg for a historical experiment.
                if ext.empty:
                    print(f"   {exp:<11} (no post-{SPLICE_YEAR} leg; local file is "
                          f"pre-{SPLICE_YEAR} only)", flush=True)
                    if piece is not None:
                        piece = piece.reset_index(); piece["scenario"] = exp
                        frames.append(piece)
                    continue
                assert_global_plausible(ext.tas_global, f"{model}/{exp}/ext")
                if piece is not None and SPLICE_YEAR in piece.index and (SPLICE_YEAR + 1) in ext.index:
                    j = abs(float(ext.loc[SPLICE_YEAR + 1, "tas_global"])
                            - float(piece.loc[SPLICE_YEAR, "tas_global"]))
                    print(f"   {exp:<11} [JOIN] |{SPLICE_YEAR+1}-{SPLICE_YEAR}| = {j:.3f} K", flush=True)
                piece = ext if piece is None else pd.concat([piece, ext])
                print(f"   {exp:<11} + ESGF -> {piece.index.max()}", flush=True)
            if piece is not None:
                piece = piece.reset_index(); piece["scenario"] = exp
                frames.append(piece)
        if not frames:
            print("   nothing to write"); continue
        allf = pd.concat(frames, ignore_index=True)
        allf.insert(1, "member", mem)
        allf = allf[["year", "member", "tas_global", "tas_ais", "scenario"]]
        dest = os.path.join(OUT_DIR, f"tas_series_{model}.csv")
        allf.to_csv(dest, index=False)
        print(f"   wrote {os.path.basename(dest)}  {len(allf)} rows", flush=True)
    print(f"\nPROVENANCE: AIS = ALL surface types south of {LAT_MAX} deg, cos(lat) weighted. "
          f"<= {SPLICE_YEAR} Pangeo zarr re-reduced here; > {SPLICE_YEAR} local ESGF. "
          f"Companion to data/cmip6_coulon/ (land mask), which is UNTOUCHED.")


if __name__ == "__main__":
    main()
