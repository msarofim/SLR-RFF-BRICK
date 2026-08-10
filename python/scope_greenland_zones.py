#!/usr/bin/env python3
"""
scope_greenland_zones.py — which Greenland temperature zone should drive the
new ice-sheet module, judged on the two things that decide it: how much we
trust the observed temperature of each zone, and how well each zone's
temperature explains the observed change in melt rate.

Candidate drivers are built identically from three independent gridded
products, annually and for the summer melt season, then scored on:

  CONFIDENCE   cross-product spread in the zone's warming amplification
               (through-origin fit of zone anomaly on global anomaly), computed
               separately for the early and the modern era. A zone the three
               products disagree about in the early era cannot carry the
               1900-1960 part of the fit, which is exactly where the current
               module fails.

  RELEVANCE    correlation of the zone's temperature with the OBSERVED
               Greenland melt rate (Frederikse GIS target, differenced,
               11-year smoothed), 1900-2018. This is the quantity the driver
               has to explain.

Products (all on disk, all re-referenced to 1850-1900, calendar-year means):
  HadCRUT5.0.2.0 analysis  5 deg, statistically infilled
  Berkeley Earth           1 deg, land+ocean, air temperature above sea ice
  GISTEMP v4               2 deg, 1200 km smoothing

Zones are latitude bands over the Greenland landmass box plus a margin-weighted
series. Greenland is land-only in every product, so the land mask does the work
of an ice-sheet mask reasonably well at these resolutions; a true ice-sheet or
ablation-zone mask is a refinement, flagged in the output.

  python3 python/scope_greenland_zones.py
Writes outputs/scope_greenland_zones.csv
"""
import os

import numpy as np
import pandas as pd
import xarray as xr

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(REPO, "data/observations/raw")
OBS = os.path.join(REPO, "data/observations")
OUT = os.path.join(REPO, "outputs/scope_greenland_zones.csv")

BASE = (1850, 1900)
EARLY = (1901, 1960)
MODERN = (1961, 2024)
CORR_WIN = (1900, 2018)          # the Frederikse GIS target window
SMOOTH = 11
MELT_MONTHS = [6, 7, 8]          # JJA, the Greenland melt season

# Greenland landmass box; the land mask selects the island within it.
GREENLAND_BOX = dict(lat=(59.0, 84.0), lon=(-73.0, -11.0))
ZONES = {
    "all":     (59.0, 84.0),
    "south":   (59.0, 70.0),     # the ablation-dominated south
    "central": (70.0, 77.0),
    "north":   (77.0, 84.0),
}


# ---------------------------------------------------------------------------
# product loaders -> monthly DataArray on (time, lat, lon) with a land mask
# ---------------------------------------------------------------------------
def _years_months(nyear_start, n):
    t0 = np.arange(n)
    return nyear_start + t0 // 12, 1 + t0 % 12


def load_hadcrut5():
    d = xr.open_dataset(os.path.join(RAW, "HadCRUT.5.0.2.0.analysis.anomalies.ensemble_mean.nc"),
                        decode_times=False)
    da = d["tas_mean"].rename(latitude="lat", longitude="lon")
    yr, mo = _years_months(1850, da.sizes["time"])
    return da.assign_coords(year=("time", yr), month=("time", mo)), None


def load_berkeley():
    d = xr.open_dataset(os.path.join(RAW, "Land_and_Ocean_LatLong1.nc"), decode_times=False)
    d = d.rename(latitude="lat", longitude="lon")
    da = d["temperature"]
    yr = np.floor(d["time"].values + 1e-6).astype(int)
    mo = np.rint((d["time"].values - yr) * 12 - 0.5).astype(int) + 1
    return da.assign_coords(year=("time", yr), month=("time", mo)), d["land_mask"]


def load_gistemp():
    d = xr.open_dataset(os.path.join(RAW, "gistemp1200_GHCNv4_ERSSTv5.nc"), decode_times=True)
    da = d["tempanomaly"]
    return da.assign_coords(year=("time", da["time.year"].values),
                            month=("time", da["time.month"].values)), None


PRODUCTS = {"HadCRUT5": load_hadcrut5, "BerkeleyEarth": load_berkeley, "GISTEMP": load_gistemp}


def zone_series(da, land, lat_lo, lat_hi, months=None):
    """Cosine-latitude-weighted annual mean anomaly over a Greenland zone."""
    lon = da["lon"]
    sel = da.sel(lat=slice(lat_lo, lat_hi))
    # normalise longitude convention to [-180, 180]
    if float(lon.max()) > 180:
        sel = sel.assign_coords(lon=(((sel["lon"] + 180) % 360) - 180)).sortby("lon")
    sel = sel.sel(lon=slice(*GREENLAND_BOX["lon"]))
    if land is not None:
        lm = land.sel(lat=slice(lat_lo, lat_hi))
        if float(land["lon"].max()) > 180:
            lm = lm.assign_coords(lon=(((lm["lon"] + 180) % 360) - 180)).sortby("lon")
        sel = sel.where(lm.sel(lon=slice(*GREENLAND_BOX["lon"])) > 0.5)
    if months is not None:
        sel = sel.where(sel["month"].isin(months), drop=True)
    w = np.cos(np.deg2rad(sel["lat"]))
    s = sel.weighted(w.fillna(0)).mean(dim=[d for d in sel.dims if d != "time"], skipna=True)
    return s.groupby("year").mean().to_series().dropna()


def global_series(da, months=None):
    sel = da if months is None else da.where(da["month"].isin(months), drop=True)
    w = np.cos(np.deg2rad(sel["lat"]))
    s = sel.weighted(w.fillna(0)).mean(dim=[d for d in sel.dims if d != "time"], skipna=True)
    return s.groupby("year").mean().to_series().dropna()


def rebase(s):
    return s - s.loc[BASE[0]:BASE[1]].mean()


def amp(zone, glob, win):
    """Through-origin fit of zone anomaly on global anomaly over `win`."""
    x = glob.loc[win[0]:win[1]]
    y = zone.reindex(x.index)
    ok = x.notna() & y.notna()
    if ok.sum() < 20:
        return np.nan
    return float((x[ok] * y[ok]).sum() / (x[ok] ** 2).sum())


def main():
    tgt = pd.read_csv(os.path.join(REPO, "outputs/recalib_targets_ext.csv")).set_index("year")
    melt_rate = tgt["gis"].dropna().diff().rolling(SMOOTH, center=True).mean()
    win = np.arange(CORR_WIN[0], CORR_WIN[1] + 1)

    series = {}   # (product, zone, season) -> rebased annual series
    globals_ = {}
    for pname, loader in PRODUCTS.items():
        da, land = loader()
        for season, months in (("annual", None), ("JJA", MELT_MONTHS)):
            globals_[(pname, season)] = rebase(global_series(da, months))
            for zname, (lo, hi) in ZONES.items():
                series[(pname, zname, season)] = rebase(zone_series(da, land, lo, hi, months))
        print(f"  loaded {pname}")

    # the driver already on disk, for reference: RGI region 5 periphery weighting
    r05 = pd.read_csv(os.path.join(OBS, "t_glac_regions_hadcrut5.csv")).set_index("year")["r05"]
    series[("HadCRUT5", "periphery(r05)", "annual")] = rebase(r05)
    globals_[("HadCRUT5", "annual")] = globals_[("HadCRUT5", "annual")]

    rows = []
    for (pname, zname, season), s in series.items():
        g = globals_[(pname, season)]
        sm = s.rolling(SMOOTH, center=True).mean().reindex(win)
        both = pd.concat([sm, melt_rate.reindex(win)], axis=1).dropna()
        r = (float(np.corrcoef(both.iloc[:, 0], both.iloc[:, 1])[0, 1])
             if len(both) > 30 else np.nan)
        rows.append(dict(product=pname, zone=zname, season=season,
                         amp_early=amp(s, g, EARLY), amp_modern=amp(s, g, MODERN),
                         corr_meltrate=r))
    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)

    print("\nCONFIDENCE — warming amplification vs global, by product "
          f"(early {EARLY[0]}-{EARLY[1]} / modern {MODERN[0]}-{MODERN[1]})")
    print(f"  {'zone':16s} {'season':7s} " +
          "  ".join(f"{p:>21s}" for p in PRODUCTS) + "   spread(early)")
    for season in ("annual", "JJA"):
        for zname in list(ZONES) + ["periphery(r05)"]:
            sub = df[(df.zone == zname) & (df.season == season)]
            if sub.empty:
                continue
            cells, early = [], []
            for p in PRODUCTS:
                r = sub[sub["product"] == p]
                if len(r):
                    cells.append(f"{r.iloc[0].amp_early:9.2f} /{r.iloc[0].amp_modern:9.2f}")
                    if np.isfinite(r.iloc[0].amp_early):
                        early.append(r.iloc[0].amp_early)
                else:
                    cells.append(f"{'—':>21s}")
            rng = (f"{max(early) / min(early):.2f}x" if len(early) > 1 and min(early) > 0
                   else "—")
            print(f"  {zname:16s} {season:7s} " + "  ".join(cells) + f"   {rng:>8s}")

    print("\nRELEVANCE — correlation with the observed Greenland melt rate, "
          f"{CORR_WIN[0]}-{CORR_WIN[1]} ({SMOOTH}-yr smoothed)")
    print(f"  {'zone':16s} " + "  ".join(f"{s:>9s}" for s in ("annual", "JJA")))
    for zname in list(ZONES) + ["periphery(r05)"]:
        cells = []
        for season in ("annual", "JJA"):
            sub = df[(df.zone == zname) & (df.season == season) & (df["product"] == "HadCRUT5")]
            cells.append(f"{sub.iloc[0].corr_meltrate:9.2f}" if len(sub) else f"{'—':>9s}")
        print(f"  {zname:16s} " + "  ".join(cells))
    gl = df[(df.zone == "all") & (df["product"] == "HadCRUT5")]
    print("\n  (global mean temperature, for reference: see scope_greenland_options.py, "
          "r = +0.16)")
    print("\nNOTE: zones are land-masked latitude bands over the Greenland box, not an "
          "ice-sheet\n  or ablation-zone mask. Refining the mask is a separate step.")
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
