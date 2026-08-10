#!/usr/bin/env python3
"""
build_t_gis.py — the Greenland ice-sheet temperature driver for BRICK-F*.

Produces the observed regional temperature series that replaces global mean
temperature as the driver of the Greenland module (option A of
notes/scoping_2026-08-10_greenland_options.md), plus the cross-product
amplification statistics the projection splice and the equilibrium-ladder
frame conversion both need.

WHY A REGIONAL DRIVER (scoping §4, verified)
    Greenland warmed ~1.2 C during 1920-45 while the globe warmed +0.22, then
    cooled at -1.8 C/century from 1940 to 1990 while the globe warmed +0.4 --
    which is exactly the 1942-1982 window BRICK-F* misses. Melt-rate
    correlation with the observed target: global +0.21, Greenland regional
    +0.77.

ZONE (scoping §9, Marcus 2026-08-10)
    Headline  = southern Greenland, 59-70 N, annual, land-masked.
    Sensitivity arm (pre-registered) = whole ice sheet, 59-84 N, annual.
    NOT JJA: summer temperature is worse observed than annual in anomaly space
    (every JJA cross-product spread exceeds its annual counterpart), and the
    physical case for melt-season temperature only bites in a positive-degree-day
    formulation, not in an anomaly-driven relaxation model.

MASK -- this is the substantive change from python/scope_greenland_zones.py
    The scoping diagnostic used land-masked latitude bands over a lon/lat box.
    Two problems with that as a production driver:
      1. the box (lon -73..-11) contains ICELAND (-25..-13 E, 63-67 N) inside
         the southern band, and Baffin/Ellesmere inside the northern ones;
      2. the land mask was only actually applied to Berkeley Earth -- the
         HadCRUT5 and GISTEMP loaders passed land=None, so those two zone
         series were land+ocean blends over the whole box.
    Here every product gets the SAME mask: fractional overlap of each grid cell
    with (GTN-G 2023 first-order region 05 "Greenland Periphery" polygon) AND
    (Berkeley Earth 1-deg land fraction). Region 05 tiles Iceland into region 06,
    Baffin into 04 and Ellesmere into 03, so the intersection is Greenland land
    and nothing else. Verified by point test before use.
    Caveat retained: this is a LAND mask, not an ice-sheet or ablation-zone mask.
    At 1-5 deg the difference is the narrow ice-free margin.
    Second caveat, unavoidable: HadCRUT5 cells are a CRUTEM5-land/HadSST4-ocean
    blend at 5 deg, so a partially-land Greenland cell carries ocean signal that
    no mask can remove. Berkeley Earth at 1 deg does not have this problem. That
    is why all three products are built and compared rather than one assumed.

AMPLIFICATION
    Through-origin fit of the zone anomaly on the same product's global mean
    anomaly. Reported over three windows because they disagree by 2x and the
    choice matters (see the AMP_WINDOWS note below and the provenance file).

  python3 python/build_t_gis.py
Writes:
  data/observations/t_gis_zones.csv             headline driver (per zone), full precision
  data/observations/t_gis_zones_allproducts.csv every product x zone series
  outputs/gis_driver_constants.csv              amplification + relevance table
  data/observations/t_gis_provenance.md
  figures/t_gis_driver.png
"""
import os
import subprocess

import netCDF4
import numpy as np
import pandas as pd
import shapefile as pyshp
from matplotlib.path import Path as MplPath

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(REPO, "data/observations/raw")
OBS = os.path.join(REPO, "data/observations")

HAD_NC = os.path.join(RAW, "HadCRUT.5.0.2.0.analysis.anomalies.ensemble_mean.nc")
BERK_NC = os.path.join(RAW, "Land_and_Ocean_LatLong1.nc")
GIST_NC = os.path.join(RAW, "gistemp1200_GHCNv4_ERSSTv5.nc")
SHP = os.path.join(RAW, "GlacReg_2023/GTN-G_202307_o1regions.shp")
TARGETS_CSV = os.path.join(REPO, "outputs/recalib_targets_ext.csv")

OUT_DRIVER = os.path.join(OBS, "t_gis_zones.csv")
OUT_ALLPROD = os.path.join(OBS, "t_gis_zones_allproducts.csv")
OUT_CONSTANTS = os.path.join(REPO, "outputs/gis_driver_constants.csv")
OUT_PRIORS = os.path.join(REPO, "outputs/gis_amp_prior.csv")
OUT_PROV = os.path.join(OBS, "t_gis_provenance.md")
OUT_FIG = os.path.join(REPO, "figures/t_gis_driver.png")

# ---- zones -----------------------------------------------------------------
GTNG_REGION = "05"                  # "Greenland Periphery" -- the region polygon
ZONES = {
    "south": (59.0, 70.0),          # HEADLINE: the ablation-dominated south
    "all": (59.0, 84.0),            # pre-registered sensitivity arm
}
# Carried through the confidence/relevance table only -- they are not written to
# the driver file. They exist so the zone choice is re-validated on THIS mask
# rather than inherited from the box-masked scoping table it corrects.
DIAG_ZONES = {"central": (70.0, 77.0), "north": (77.0, 84.0)}
HEADLINE_ZONE = "south"

# ---- construction constants ------------------------------------------------
SUBGRID = 5                         # SUBGRID^2 point-in-polygon samples per cell
LAND_FRAC_FLOOR = 0.0               # land fraction used as a WEIGHT, not a threshold
MIN_MONTHS = 12                     # calendar-year completeness
BASE = (1850, 1900)                 # driver anomaly baseline (multi-year baseline rule)
BASE_COMMON = (1880, 1900)          # baseline all three products can supply (GISTEMP@1880)
# Amplification windows. These disagree by ~2x and the disagreement is physical,
# not noise: the early era is a through-origin fit over decades when the global
# anomaly was near zero while Greenland swung +/-1 C (the early-twentieth-century
# warm period), which inflates the ratio. "full" is the window the glacier
# module's amp_obsfit uses (brickf_data.AMP_FIT_WIN) and is the like-for-like
# choice; "modern" is the one that describes the projection era.
AMP_WINDOWS = {"full": (1901, 2024), "early": (1901, 1960), "modern": (1961, 2024)}
AMP_WINDOW_HEADLINE = "full"        # matches brickf_data.AMP_FIT_WIN
CORR_WIN = (1900, 2018)             # the Frederikse GIS target window
SMOOTH = 11                         # melt-rate smoothing, years

PRODUCT_BASELINE = {                # first year each product can be rebased from
    "HadCRUT5": BASE, "BerkeleyEarth": BASE, "GISTEMP": BASE_COMMON,
}

COMMIT = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True).stdout.strip()


# =============================================================================
# 1. the Greenland-land mask, shared by every product
# =============================================================================
def region_paths(region):
    """Closed rings of one GTN-G first-order region as matplotlib Paths."""
    sf = pyshp.Reader(SHP)
    fields = [f[0] for f in sf.fields[1:]]
    key = fields.index("o1region")
    out = []
    for sr in sf.shapeRecords():
        if str(sr.record[key]).zfill(2) != region:
            continue
        parts = list(sr.shape.parts) + [len(sr.shape.points)]
        for i in range(len(sr.shape.parts)):
            ring = np.asarray(sr.shape.points[parts[i]:parts[i + 1]])
            if len(ring) >= 3:
                out.append(MplPath(ring))
    if not out:
        raise ValueError(f"GTN-G region {region} not found in {SHP}")
    return out


def berkeley_land_lookup():
    """Nearest-neighbour land-fraction lookup on Berkeley's 1-deg mask."""
    d = netCDF4.Dataset(BERK_NC)
    blat = np.asarray(d.variables["latitude"][:], dtype=float)
    blon = np.asarray(d.variables["longitude"][:], dtype=float)
    lm = np.asarray(d.variables["land_mask"][:], dtype=float)

    def land_at(lon, lat):
        i = np.clip(np.searchsorted(blat, lat) - 0, 0, len(blat) - 1)
        i = np.clip(np.rint(lat - blat[0]).astype(int), 0, len(blat) - 1)
        j = np.clip(np.rint(lon - blon[0]).astype(int), 0, len(blon) - 1)
        return lm[i, j]

    return land_at


def cell_weights(lat, lon, rings, land_at, lat_lo, lat_hi):
    """
    Per-cell weight = cos(lat) * (fraction of the cell that is Greenland land
    inside [lat_lo, lat_hi]), by SUBGRID^2 point sampling.
    """
    dlat = float(np.abs(np.diff(lat)).mean())
    dlon = float(np.abs(np.diff(lon)).mean())
    off = (np.arange(SUBGRID) + 0.5) / SUBGRID - 0.5
    w = np.zeros((len(lat), len(lon)))
    for i, la in enumerate(lat):
        sub_la = la + off * dlat
        if sub_la.max() < lat_lo - dlat or sub_la.min() > lat_hi + dlat:
            continue
        for j, lo in enumerate(lon):
            lo180 = ((lo + 180.0) % 360.0) - 180.0
            sub_lo = lo180 + off * dlon
            pts = np.array([(x, y) for y in sub_la for x in sub_lo])
            keep = (pts[:, 1] >= lat_lo) & (pts[:, 1] <= lat_hi)
            if not keep.any():
                continue
            inside = np.zeros(len(pts), dtype=bool)
            for ring in rings:
                inside |= ring.contains_points(pts)
            frac_land = np.array([land_at(x, y) for x, y in pts])
            hit = keep & inside & (frac_land > LAND_FRAC_FLOOR)
            if hit.any():
                w[i, j] = float((frac_land[hit]).sum() / len(pts)) * \
                    float(np.cos(np.deg2rad(la)))
    return w


# =============================================================================
# 2. product loaders -> (values[time, lat, lon], year, month, lat, lon)
# =============================================================================
def load_hadcrut5():
    d = netCDF4.Dataset(HAD_NC)
    lat = np.asarray(d.variables["latitude"][:], dtype=float)
    lon = np.asarray(d.variables["longitude"][:], dtype=float)
    tv = d.variables["time"]
    dates = netCDF4.num2date(tv[:], tv.units, getattr(tv, "calendar", "standard"))
    yr = np.array([x.year for x in dates])
    mo = np.array([x.month for x in dates])
    v = np.ma.filled(d.variables["tas_mean"][:].astype(float), np.nan)
    return v, yr, mo, lat, lon


def load_berkeley():
    d = netCDF4.Dataset(BERK_NC)
    lat = np.asarray(d.variables["latitude"][:], dtype=float)
    lon = np.asarray(d.variables["longitude"][:], dtype=float)
    t = np.asarray(d.variables["time"][:], dtype=float)
    yr = np.floor(t + 1e-6).astype(int)
    mo = np.rint((t - yr) * 12 - 0.5).astype(int) + 1
    v = np.ma.filled(d.variables["temperature"][:].astype(float), np.nan)
    return v, yr, mo, lat, lon


def load_gistemp():
    d = netCDF4.Dataset(GIST_NC)
    lat = np.asarray(d.variables["lat"][:], dtype=float)
    lon = np.asarray(d.variables["lon"][:], dtype=float)
    tv = d.variables["time"]
    dates = netCDF4.num2date(tv[:], tv.units, getattr(tv, "calendar", "standard"))
    yr = np.array([x.year for x in dates])
    mo = np.array([x.month for x in dates])
    v = np.ma.filled(d.variables["tempanomaly"][:].astype(float), np.nan)
    return v, yr, mo, lat, lon


PRODUCTS = {"HadCRUT5": load_hadcrut5, "BerkeleyEarth": load_berkeley,
            "GISTEMP": load_gistemp}


# =============================================================================
# 3. weighted annual series
# =============================================================================
def annual_weighted(v, yr, mo, w):
    """Calendar-year mean of the w-weighted spatial mean; NaN cells drop out of
    both numerator and denominator, so partial coverage is handled correctly."""
    wf = w[None, :, :]
    ok = np.isfinite(v)
    num = np.nansum(np.where(ok, v, 0.0) * wf, axis=(1, 2))
    den = np.sum(np.where(ok, 1.0, 0.0) * wf, axis=(1, 2))
    m = np.where(den > 0, num / np.where(den > 0, den, 1.0), np.nan)
    df = pd.DataFrame({"year": yr, "month": mo, "v": m})
    g = df.dropna().groupby("year")["v"]
    s = g.mean()
    return s[g.count() >= MIN_MONTHS]


def global_annual(v, yr, mo, lat, lon):
    w = np.repeat(np.cos(np.deg2rad(lat))[:, None], len(lon), axis=1)
    return annual_weighted(v, yr, mo, w)


def rebase(s, base):
    seg = s.loc[base[0]:base[1]]
    if len(seg) == 0:
        raise ValueError("empty baseline segment")
    return s - seg.mean()


def amp_through_origin(zone, glob, win):
    x = glob.loc[win[0]:win[1]]
    y = zone.reindex(x.index)
    ok = x.notna() & y.notna()
    if ok.sum() < 20:
        return np.nan
    return float((x[ok] * y[ok]).sum() / (x[ok] ** 2).sum())


def melt_rate_target():
    tgt = pd.read_csv(TARGETS_CSV).set_index("year")
    return tgt["gis"].dropna().diff().rolling(SMOOTH, center=True).mean()


def corr_with_meltrate(s, melt_rate):
    win = np.arange(CORR_WIN[0], CORR_WIN[1] + 1)
    sm = s.rolling(SMOOTH, center=True).mean().reindex(win)
    both = pd.concat([sm, melt_rate.reindex(win)], axis=1).dropna()
    if len(both) <= 30:
        return np.nan
    return float(np.corrcoef(both.iloc[:, 0], both.iloc[:, 1])[0, 1])


# =============================================================================
# 4. build
# =============================================================================
def build():
    rings = region_paths(GTNG_REGION)
    # Guard the mask before it is used anywhere (the box-mask bug this replaces
    # was invisible precisely because nobody tested a point).
    for name, (x, y), want in [("Iceland", (-19.0, 65.0), False),
                               ("Baffin", (-70.0, 68.0), False),
                               ("Ellesmere", (-75.0, 79.0), False),
                               ("S-Greenland", (-45.0, 62.0), True),
                               ("C-Greenland", (-40.0, 72.0), True)]:
        got = any(r.contains_point((x, y)) for r in rings)
        assert got == want, f"GTN-G region {GTNG_REGION} mask: {name} inside={got}"
    land_at = berkeley_land_lookup()

    series, globals_, weights = {}, {}, {}
    all_zones = {**ZONES, **DIAG_ZONES}
    for pname, loader in PRODUCTS.items():
        v, yr, mo, lat, lon = loader()
        base = PRODUCT_BASELINE[pname]
        globals_[pname] = rebase(global_annual(v, yr, mo, lat, lon), base)
        for zname, (lo, hi) in all_zones.items():
            w = cell_weights(lat, lon, rings, land_at, lo, hi)
            weights[(pname, zname)] = w
            series[(pname, zname)] = rebase(annual_weighted(v, yr, mo, w), base)
        print(f"  {pname:14s} grid {len(lat)}x{len(lon)}  "
              + "  ".join(f"{z}: {int((weights[(pname, z)] > 0).sum())} cells"
                          for z in ZONES))
    return series, globals_, weights


def amp_prior(con, zone, window):
    """Cross-product amplification prior for one zone: mean, sd, and the
    product range it spans. sd is the population sd over the three products --
    the products are the uncertainty here, and there are only three of them."""
    v = con[con.zone == zone][f"amp_{window}"].to_numpy(dtype=float)
    return dict(zone=zone, window=window, mean=float(v.mean()),
                sd=float(v.std(ddof=0)), lo=float(v.min()), hi=float(v.max()),
                spread_ratio=float(v.max() / v.min()))


def main():
    series, globals_, weights = build()
    melt_rate = melt_rate_target()

    rows = []
    for (pname, zname), s in series.items():
        r = dict(product=pname, zone=zname,
                 baseline=f"{PRODUCT_BASELINE[pname][0]}-{PRODUCT_BASELINE[pname][1]}",
                 year_first=int(s.index.min()), year_last=int(s.index.max()),
                 n_cells=int((weights[(pname, zname)] > 0).sum()),
                 corr_meltrate=corr_with_meltrate(s, melt_rate))
        for wname, win in AMP_WINDOWS.items():
            r[f"amp_{wname}"] = amp_through_origin(s, globals_[pname], win)
        rows.append(r)
    con = pd.DataFrame(rows).sort_values(["zone", "product"]).reset_index(drop=True)
    con.to_csv(OUT_CONSTANTS, index=False)

    priors = pd.DataFrame([amp_prior(con, z, w)
                           for z in list(ZONES) + list(DIAG_ZONES)
                           for w in AMP_WINDOWS])
    priors.to_csv(OUT_PRIORS, index=False)

    # headline driver: every zone, one file, full precision (the Julia port
    # validation compares at 1e-9 and 6-decimal rounding has broken it before)
    hp = "HadCRUT5"
    drv = pd.concat({z: series[(hp, z)] for z in ZONES}, axis=1)
    drv.index.name = "year"
    drv.to_csv(OUT_DRIVER, float_format="%.12f")

    allp = pd.concat({f"{p}_{z}": series[(p, z)] for p in PRODUCTS for z in ZONES},
                     axis=1)
    allp.index.name = "year"
    allp.to_csv(OUT_ALLPROD, float_format="%.12f")

    # ---- report -----------------------------------------------------------
    zorder = list(ZONES) + list(DIAG_ZONES)
    for wname, win in AMP_WINDOWS.items():
        print(f"\nCONFIDENCE -- amplification, through-origin fit of zone on the same "
              f"product's global, {win[0]}-{win[1]}")
        print(f"  {'zone':8s} " + "  ".join(f"{p:>13s}" for p in PRODUCTS) +
              f"   {'spread':>7s}")
        for zname in zorder:
            vals = [float(con[(con.zone == zname) & (con["product"] == p)]
                          .iloc[0][f"amp_{wname}"]) for p in PRODUCTS]
            print(f"  {zname:8s} " + "  ".join(f"{v:13.2f}" for v in vals) +
                  f"   {max(vals) / min(vals):6.2f}x")

    print(f"\nRELEVANCE -- corr with observed melt rate, {CORR_WIN[0]}-{CORR_WIN[1]}, "
          f"{SMOOTH}-yr smoothed")
    print(f"  {'zone':8s} " + "  ".join(f"{p:>13s}" for p in PRODUCTS))
    for zname in zorder:
        print(f"  {zname:8s} " + "  ".join(
            f"{float(con[(con.zone == zname) & (con['product'] == p)].iloc[0].corr_meltrate):13.2f}"
            for p in PRODUCTS))

    print(f"\nAMPLIFICATION PRIOR, zone '{HEADLINE_ZONE}' -- cross-product mean/sd")
    for wname in AMP_WINDOWS:
        pr = amp_prior(con, HEADLINE_ZONE, wname)
        mark = "  <- headline window" if wname == AMP_WINDOW_HEADLINE else ""
        print(f"  {wname:7s} {str(AMP_WINDOWS[wname]):>14s}  "
              f"N({pr['mean']:.2f}, {pr['sd']:.2f})  range "
              f"[{pr['lo']:.2f}, {pr['hi']:.2f}]  {pr['spread_ratio']:.2f}x{mark}")

    write_provenance(con)
    make_figure(series, globals_)
    for p in (OUT_DRIVER, OUT_ALLPROD, OUT_CONSTANTS, OUT_PRIORS, OUT_PROV, OUT_FIG):
        print(f"wrote {os.path.relpath(p, REPO)}")


def write_provenance(con):
    amp = con[con.zone == HEADLINE_ZONE][f"amp_{AMP_WINDOW_HEADLINE}"]
    with open(OUT_PROV, "w") as f:
        f.write(f"""# t_gis_zones provenance

Built by `python/build_t_gis.py` at commit `{COMMIT}`.

## What this is
The observed Greenland regional temperature driver for the BRICK-F\\* Greenland
module (option A, `notes/scoping_2026-08-10_greenland_options.md` §4, §9).
Headline zone **{HEADLINE_ZONE}** ({ZONES[HEADLINE_ZONE][0]:.0f}-{ZONES[HEADLINE_ZONE][1]:.0f} N);
pre-registered sensitivity arm **all** ({ZONES['all'][0]:.0f}-{ZONES['all'][1]:.0f} N).

## Mask
Fractional overlap of each grid cell with **GTN-G 2023 first-order region
{GTNG_REGION} ("Greenland Periphery")** AND **Berkeley Earth 1-deg land
fraction**, sampled {SUBGRID}x{SUBGRID} per cell, then cos(lat) weighted. Land
fraction enters as a weight, not a threshold. The region polygon tiles Iceland
into region 06, Baffin into 04 and Ellesmere into 03; membership is asserted by
point test at build time.

Supersedes the lon/lat box used in `python/scope_greenland_zones.py`, which
(a) admitted Iceland into the southern band and Baffin/Ellesmere into the
northern ones, and (b) applied a land mask only to Berkeley Earth.

## Products, baselines
| product | grid | baseline | note |
|---|---|---|---|
| HadCRUT5.0.2.0 analysis | 5 deg | {BASE[0]}-{BASE[1]} | headline driver; land+ocean blend at 5 deg |
| Berkeley Earth Land+Ocean | 1 deg | {BASE[0]}-{BASE[1]} | genuine land mask, best resolved here |
| GISTEMP v4 (1200 km) | 2 deg | {BASE_COMMON[0]}-{BASE_COMMON[1]} | record starts 1880 |

Annual = calendar-year mean of 12 monthly values; a year is kept only with
>= {MIN_MONTHS} months (the Berkeley calendar-year parsing discipline).

## Amplification
Through-origin fit of the zone anomaly on the same product's global mean
anomaly. Headline window `{AMP_WINDOW_HEADLINE}` = {AMP_WINDOWS[AMP_WINDOW_HEADLINE]},
matching `brickf_data.AMP_FIT_WIN` so the Greenland and glacier amplifications
are like-for-like.

Zone `{HEADLINE_ZONE}`, window `{AMP_WINDOW_HEADLINE}`: mean **{amp.mean():.3f}**,
sd **{amp.std(ddof=0):.3f}**, range {amp.min():.3f}-{amp.max():.3f} across the
three products.

**The windows disagree by about 2x and the disagreement is physical.** The
early window is a through-origin fit over decades when the global anomaly was
near zero while Greenland swung by +/-1 C (the early-twentieth-century warm
period), which inflates the ratio; the modern window describes the projection
era. Which window sets the amplification prior is a live methodological choice
recorded in the handoff, not something this script resolves.

## Units and conventions
Degrees C, anomalies relative to the stated baseline, full precision
(%.12f) because the Julia port validation compares at 1e-9.

## Outputs
- `data/observations/t_gis_zones.csv` -- headline HadCRUT5 driver, one column per zone
- `data/observations/t_gis_zones_allproducts.csv` -- every product x zone
- `outputs/gis_driver_constants.csv` -- amplification + melt-rate correlation
""")


def make_figure(series, globals_):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    colors = {"HadCRUT5": "C0", "BerkeleyEarth": "C1", "GISTEMP": "C2"}
    for ax, zname in zip(axes, ZONES):
        for pname in PRODUCTS:
            s = series[(pname, zname)]
            ax.plot(s.index, s.values, lw=0.7, alpha=0.45, color=colors[pname])
            ax.plot(s.index, s.rolling(SMOOTH, center=True).mean(), lw=2.0,
                    color=colors[pname], label=f"{pname}")
        g = globals_["HadCRUT5"]
        ax.plot(g.index, g.rolling(SMOOTH, center=True).mean(), lw=2.0, color="k",
                ls="--", label="global mean (HadCRUT5)")
        ax.axvspan(1942, 1982, color="0.85", zorder=0)
        ax.set_title(f"Greenland {zname} ({ZONES[zname][0]:.0f}-{ZONES[zname][1]:.0f} N), "
                     f"annual, land-masked, rel {BASE[0]}-{BASE[1]}"
                     f"   [{SMOOTH}-yr smooth; shaded = the 1942-1982 miss]")
        ax.set_ylabel("anomaly, C")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8, ncol=2)
    axes[-1].set_xlabel("year")
    fig.tight_layout()
    fig.savefig(OUT_FIG, dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    main()
