"""
diag_coulon_mask_consistency.py

IS THE all_cells COLUMN OF outputs/diag_coulon_domain_sensitivity.csv A
CONSISTENT ANOMALY, OR DOES IT MIX MASKS?

WHY THIS IS URGENT. The Coulon domain ruling (report both masks as a bound) and
the reachability result behind it (1 of 4 vs 2 of 4 models reachable) both rest
on that column. But `reduce_cmip6_tas_coulon.py` takes its <=2100 leg from
`data/cmip6_pai/tas_series_<model>.csv`, which is ALREADY REDUCED UNDER THE LAND
MASK, and only UKESM1-0-LL is rebuilt end to end from NetCDF. Locally we hold
post-2100 ssp files for all four but a `historical` file only for UKESM. So for
IPSL / CESM2-WACCM / MRI an all-cells 2300 value could easily have been
differenced against a LAND-masked 1995-2014 baseline -- an anomaly that mixes
two spatial domains and is wrong by their baseline difference.

THE TEST. For each model, compute the 1995-2014 Antarctic-mean tas under BOTH
masks (historical, from the Pangeo zarr the pai series were built from) and the
2300 value under BOTH masks (from the local ESGF NetCDF). Then form all four
differences and see which one reproduces the published table:

    consistent : allcells(2300) - allcells(1995-2014)
    MIXED      : allcells(2300) - land(1995-2014)

If the table matches the MIXED form, the reachability result must be redone.

  source ~/climate-env/bin/activate && python python/diag_coulon_mask_consistency.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd, xarray as xr, gcsfs
from pai_series import align_sftlf_to

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT  = "https://storage.googleapis.com/cmip6/cmip6-zarr-consolidated-stores.csv"
EXT  = os.path.join(REPO, "data/cmip6_coulon_ext")
OUT  = os.path.join(REPO, "outputs/diag_coulon_mask_consistency.csv")
REF0, REF1 = 1995, 2014
TARGET_YEAR = 2300
LAT_MAX, SFTLF_MIN = -60.0, 50.0
MEMBERS = {"MRI-ESM2-0": "r1i1p1f1", "CESM2-WACCM": "r1i1p1f1",
           "IPSL-CM6A-LR": "r1i1p1f1", "UKESM1-0-LL": "r4i1p1f2"}


def masks(ds, sftlf, label):
    lf = align_sftlf_to(sftlf, ds, label)
    wg = np.cos(np.deg2rad(ds.lat)) * xr.ones_like(ds.lon, dtype=float)
    land = wg.where((lf >= SFTLF_MIN) & (lf.lat <= LAT_MAX), 0.0)
    allc = wg.where(lf.lat <= LAT_MAX, 0.0)
    return land, allc


def wmean(da, w):
    return float((da * w).sum() / w.sum())


def main():
    cat = pd.read_csv(CAT); fs = gcsfs.GCSFileSystem(token="anon")
    rows = []
    for model, mem in MEMBERS.items():
        print(f"\n── {model} ({mem})", flush=True)
        lf_r = cat[(cat.variable_id == "sftlf") & (cat.source_id == model)]
        if lf_r.empty:
            print("   no sftlf on Pangeo; skipped"); continue
        sftlf = xr.open_zarr(fs.get_mapper(lf_r.zstore.iloc[0]), consolidated=True)["sftlf"].squeeze(drop=True)
        h = cat[(cat.variable_id == "tas") & (cat.table_id == "Amon") & (cat.source_id == model)
                & (cat.experiment_id == "historical") & (cat.member_id == mem)]
        if h.empty:
            print(f"   no historical {mem} on Pangeo; skipped"); continue
        ds = xr.open_zarr(fs.get_mapper(h.zstore.iloc[0]), consolidated=True)
        # ⚠ SELECT BY YEAR, NOT A DATE-STRING SLICE. UKESM1-0-LL is on a 360-day
        # calendar, where "2014-12-31" is not a valid date and cftime raises. Year
        # filtering is calendar-agnostic and is what the ext leg below already does.
        # ⚠ .dt.year, NOT a list comprehension over .values. Pangeo hands back
        # numpy.datetime64 for MRI-ESM2-0 and cftime objects for the 360-day
        # models, and only the xarray accessor covers both.
        hy = ds["time"].dt.year.values
        sl = ds.tas.isel(time=np.where((hy >= REF0) & (hy <= REF1))[0])
        dm = sl.time.dt.days_in_month
        base = (sl * dm).sum("time") / dm.sum("time")        # month-length weighted
        land, allc = masks(ds, sftlf, f"{model}/hist")
        b_land, b_all = wmean(base, land), wmean(base, allc)
        print(f"   baseline {REF0}-{REF1}:  land {b_land:8.3f} K | all-cells {b_all:8.3f} K "
              f"| diff {b_all-b_land:+.3f}", flush=True)

        import glob
        pats = sorted(glob.glob(os.path.join(EXT, f"tas_Amon_{model}_ssp585_{mem}_*.nc")))
        if not pats:
            print("   no local post-2100 ssp585 NetCDF; skipped"); continue
        parts = [xr.open_dataset(p, use_cftime=True)[["tas"]] for p in pats]
        de = xr.concat(parts, dim="time") if len(parts) > 1 else parts[0]
        yrs = de["time"].dt.year.values
        ty = TARGET_YEAR if TARGET_YEAR in yrs else int(yrs.max())
        sel = de.tas.isel(time=np.where(yrs == ty)[0])
        dm2 = sel.time.dt.days_in_month
        tgt = (sel * dm2).sum("time") / dm2.sum("time")
        land2, allc2 = masks(de, sftlf, f"{model}/ext")
        t_land, t_all = wmean(tgt, land2), wmean(tgt, allc2)
        print(f"   {ty}:              land {t_land:8.3f} K | all-cells {t_all:8.3f} K", flush=True)
        cons, mixed = t_all - b_all, t_all - b_land
        print(f"   ANOMALY  consistent all-cells {cons:6.2f} K | MIXED (all-cells - land base) "
              f"{mixed:6.2f} K | land-land {t_land-b_land:6.2f} K", flush=True)
        rows.append(dict(model=model, year=ty, base_land=b_land, base_allcells=b_all,
                         tgt_land=t_land, tgt_allcells=t_all,
                         anom_consistent_allcells=cons, anom_mixed=mixed,
                         anom_land=t_land - b_land))
    d = pd.DataFrame(rows); d.to_csv(OUT, index=False)
    pub = pd.read_csv(os.path.join(REPO, "outputs/diag_coulon_domain_sensitivity.csv"))
    print("\n  VERSUS THE PUBLISHED TABLE")
    print(f"  {'model':>14} {'published all':>14} {'consistent':>11} {'MIXED':>8} {'-> matches':>12}")
    for _, r in d.iterrows():
        p = pub[(pub.model == r.model) & (pub["mask"] == "all_cells")]
        if p.empty: continue
        pv = float(p.tant_2300_degC.iloc[0])
        which = ("consistent" if abs(pv - r.anom_consistent_allcells) < abs(pv - r.anom_mixed)
                 else "⚠ MIXED")
        print(f"  {r.model:>14} {pv:14.2f} {r.anom_consistent_allcells:11.2f} "
              f"{r.anom_mixed:8.2f} {which:>12}")
    print(f"\n  wrote {OUT}\n")


if __name__ == "__main__":
    main()
