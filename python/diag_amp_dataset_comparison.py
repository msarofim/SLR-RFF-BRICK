#!/usr/bin/env python3
"""diag_amp_dataset_comparison.py — cross-dataset robustness check of the
per-block glacier-region amplification ratios (amp_obsfit).

Question (Marcus 2026-08-09): the extC amp_obsfit constants come from HadCRUT5
analysis (statistically infilled); earlier HadCRUT generations handled the
poorly-observed Arctic badly. Do Berkeley Earth and GISTEMP reproduce the
per-block through-origin amps — especially SLOWP (2.48, Arctic-heavy) and
R19 (0.61, Antarctic periphery data void)?

Machinery REPLICATED (not reinvented) from python/build_t_glac.py +
python/d1d_fourrung_seam.py build_reservoir + d1f obs_amp_of:
  * GTN-G 2023 first-order region polygons, region 20 merged into 19.
  * Region->grid: fractional overlap by point-in-polygon subsampling per cell.
    DEVIATION 1: the subgrid factor is scaled per dataset so the subsample
    point spacing stays ~1 deg (HadCRUT5 5deg grid -> SUBGRID 5, exactly as
    build_t_glac; GISTEMP 2deg -> 3; Berkeley 1deg -> 2). Vectorised with a
    bbox prefilter; dateline shifts (+-360) are OR-ed in unconditionally
    (build_t_glac only retried shifts for cells with zero unshifted hits —
    superset behaviour, self-test below bounds the effect).
  * Per-region monthly series: frac x cos(lat) weights over finite cells.
  * Global series: cos-lat mean of the SAME dataset's full finite field.
  * Annual = calendar-year mean, all 12 months required (MIN_MONTHS).
  * Missing region-YEARS filled by per-region OLS on the dataset's own global
    series in the NATIVE frame (identical to build_t_glac fill).
  * Baseline: 1850-1900 (HadCRUT5, Berkeley).
    DEVIATION 2: GISTEMP starts 1880 -> baseline 1880-1900; for apples-to-
    apples, HadCRUT5 and Berkeley are ALSO reported on the 1880-1900 baseline
    (suffix rows) so the GISTEMP amps can be compared like-for-like.
  * Blocks (d1d SPEC_3RES): GlaMBIE year-2000 glacier_area-weighted average of
    member region series, re-baselined; AGG = area-weighted all 18 scope
    regions (excl r5 incl r19), the t_glac_hadcrut5.csv construction.
  * amp = sum(g*y)/sum(g*g), through-origin, windows AMP_WINDOWS.

Sensitivity arm BerkeleyE_5deg: Berkeley Earth block-averaged onto the 5-deg
HadCRUT5 grid before masking, isolating grid-footprint effects (coarse coastal
cells blend more SST into region averages) from dataset-content differences.

Self-test: HadCRUT5 amps must reproduce outputs/extc_block_constants.csv
amp_obsfit (R19 0.6149, SLOWP 2.4840, FAST 1.4036) and the provenance
aggregate 1.595 / 1.561 to ~0.01.

Outputs (nothing committed):
  outputs/diag_amp_dataset_comparison.csv   (dataset, baseline, block, window, amp, n_years)
  outputs/diag_amp_dataset_comparison_coverage.csv  (early-coverage + divergence diagnostics)
"""
import os
import zipfile

import numpy as np
import pandas as pd
import netCDF4
import shapefile as pyshp
from matplotlib.path import Path

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
RAW = os.path.join(REPO, "data/observations/raw")
SHP = os.path.join(RAW, "GlacReg_2023/GTN-G_202307_o1regions.shp")
GLAMBIE_ZIP = os.path.join(RAW, "glambie_data.zip")
OUT_CSV = os.path.join(REPO, "outputs/diag_amp_dataset_comparison.csv")
OUT_COV = os.path.join(REPO, "outputs/diag_amp_dataset_comparison_coverage.csv")
REF_CONST = os.path.join(REPO, "outputs/extc_block_constants.csv")

SCOPE_REGIONS = [r for r in range(1, 20) if r != 5]
MERGE_INTO_19 = {20}
MIN_MONTHS = 12
GLAMBIE_AREA_YEAR = 2000.0
AMP_WINDOWS = [(1901, 2024), (1970, 2024)]
EARLY_WIN = (1901, 1930)          # early-coverage / divergence reporting window
ROLL_YEARS = 11                   # divergence running-mean length (multi-year rule)
SELFTEST_TOL = 0.015              # |amp - reference| tolerance for HadCRUT5

SPEC_3RES = {"R19": [19],
             "SLOWP": [3, 9, 7, 6],
             "FAST": [1, 4, 17, 13, 14, 2, 15, 8, 10, 11, 16, 18, 12]}

# dataset registry: file, netCDF names, native baseline window, subgrid factor
DATASETS = {
    "HadCRUT5": dict(
        path=os.path.join(RAW, "HadCRUT.5.0.2.0.analysis.anomalies.ensemble_mean.nc"),
        var="tas_mean", latname="latitude", lonname="longitude",
        time="cf", baseline=(1850, 1900), subgrid=5,
        note="analysis (infilled) ensemble mean, 5 deg"),
    "BerkeleyEarth": dict(
        path=os.path.join(RAW, "Land_and_Ocean_LatLong1.nc"),
        var="temperature", latname="latitude", lonname="longitude",
        time="decimal_year", baseline=(1850, 1900), subgrid=2,
        note="Land+Ocean 1 deg, air temp above sea ice (default product)"),
    "GISTEMP1200": dict(
        path=os.path.join(RAW, "gistemp1200_GHCNv4_ERSSTv5.nc"),
        var="tempanomaly", latname="lat", lonname="lon",
        time="cf", baseline=(1880, 1900), subgrid=3,
        note="GHCNv4/ERSSTv5, 1200 km smoothing (Arctic-infilled variant), 2 deg, starts 1880"),
    # sensitivity arm: BE block-averaged onto a 5-deg HadCRUT5-like grid.
    # Separates grid-footprint effects (coarse coastal cells blending SST into
    # the region average) from genuine dataset-content differences.
    "BerkeleyE_5deg": dict(
        path=os.path.join(RAW, "Land_and_Ocean_LatLong1.nc"),
        var="temperature", latname="latitude", lonname="longitude",
        time="decimal_year", baseline=(1850, 1900), subgrid=5, coarsen=5,
        note="Berkeley Earth degraded to 5 deg (unweighted nan-aware block mean) — footprint arm"),
}
# apples-to-apples arm: rerun the 1850-start datasets on the GISTEMP baseline
ALT_BASELINE = (1880, 1900)

# ------------------------------------------------------------------ regions
sf = pyshp.Reader(SHP)
fields = [f[0] for f in sf.fields[1:]]
REG_KEY = "o1region" if "o1region" in fields else fields[0]
rings_by_region = {}
for sr in sf.shapeRecords():
    reg = int(sr.record[fields.index(REG_KEY)])
    if reg in MERGE_INTO_19:
        reg = 19
    shp = sr.shape
    parts = list(shp.parts) + [len(shp.points)]
    for i in range(len(shp.parts)):
        ring = np.asarray(shp.points[parts[i]:parts[i + 1]])
        if len(ring) >= 3:
            rings_by_region.setdefault(reg, []).append(Path(ring))

# ------------------------------------------------------------------ weights
with zipfile.ZipFile(GLAMBIE_ZIP) as z:
    names = {int(os.path.basename(n).split("_")[0]): n
             for n in z.namelist()
             if "calendar_years/" in n and n.endswith(".csv")
             and os.path.basename(n).split("_")[0].isdigit()
             and int(os.path.basename(n).split("_")[0]) >= 1}
    area_w = {}
    for reg, n in names.items():
        df = pd.read_csv(z.open(n))
        row0 = df.loc[np.isclose(df["start_dates"], GLAMBIE_AREA_YEAR)]
        area_w[reg] = float(row0["glacier_area"].iloc[0])
W_AREA = {r: area_w[r] / sum(area_w[q] for q in SCOPE_REGIONS) for r in SCOPE_REGIONS}


# ------------------------------------------------------------------ masks
def build_frac_masks(lat, lon, subgrid):
    """Vectorised port of build_t_glac's per-cell fractional-overlap loop."""
    dlat = float(np.abs(np.diff(lat)).mean())
    dlon = float(np.abs(np.diff(lon)).mean())
    off = (np.arange(subgrid) + 0.5) / subgrid - 0.5
    sub_lat = (np.asarray(lat)[:, None] + off[None, :] * dlat).ravel()
    sub_lon = (np.asarray(lon)[:, None] + off[None, :] * dlon).ravel()
    LO, LA = np.meshgrid(sub_lon, sub_lat)
    pts = np.column_stack([LO.ravel(), LA.ravel()])   # (x=lon, y=lat)
    frac = {}
    for reg, rings in sorted(rings_by_region.items()):
        inside = np.zeros(len(pts), dtype=bool)
        for ring in rings:
            bb = ring.get_extents()
            for shift in (0.0, 360.0, -360.0):
                cand = ((pts[:, 0] + shift >= bb.x0) & (pts[:, 0] + shift <= bb.x1)
                        & (pts[:, 1] >= bb.y0) & (pts[:, 1] <= bb.y1)
                        & ~inside)
                if cand.any():
                    p = pts[cand].copy()
                    p[:, 0] += shift
                    inside[cand] |= ring.contains_points(p)
        f = (inside.reshape(len(sub_lat), len(sub_lon))
                   .reshape(len(lat), subgrid, len(lon), subgrid)
                   .mean(axis=(1, 3)))
        if f.sum() == 0:
            raise RuntimeError(f"region {reg:02d}: polygon captured no grid area")
        frac[reg] = f
    return frac


# ------------------------------------------------------------------ loaders
def load_dataset(cfg):
    nc = netCDF4.Dataset(cfg["path"])
    lat = np.asarray(nc.variables[cfg["latname"]][:], dtype=float)
    lon = np.asarray(nc.variables[cfg["lonname"]][:], dtype=float)
    if cfg["time"] == "cf":
        tv = nc.variables["time"]
        dates = netCDF4.num2date(tv[:], tv.units, getattr(tv, "calendar", "standard"))
        yr_m = np.array([d.year for d in dates])
        mo_m = np.array([d.month for d in dates])
    else:                                   # Berkeley decimal year
        t = np.asarray(nc.variables["time"][:], dtype=float)
        yr_m = np.floor(t).astype(int)
        mo_m = (np.floor((t - yr_m) * 12).astype(int) + 1).clip(1, 12)
    tas = np.ma.filled(nc.variables[cfg["var"]][:], np.nan).astype(np.float32)
    nc.close()
    k = cfg.get("coarsen")
    if k:                                   # nan-aware block mean onto k-x grid
        nlat, nlon = len(lat) // k, len(lon) // k
        tas4 = tas.reshape(tas.shape[0], nlat, k, nlon, k)
        fin = np.isfinite(tas4)
        num = np.where(fin, tas4, 0.0).sum(axis=(2, 4))
        den = fin.sum(axis=(2, 4))
        tas = np.where(den > 0, num / np.maximum(den, 1), np.nan).astype(np.float32)
        lat = lat.reshape(nlat, k).mean(axis=1)
        lon = lon.reshape(nlon, k).mean(axis=1)
    return lat, lon, yr_m, mo_m, tas


# ------------------------------------------------------------------ extraction
def extract_native(name, cfg):
    """Per-region + global ANNUAL series in the dataset's NATIVE anomaly frame
    (fills applied), plus coverage diagnostics. Heavy step — run once/dataset."""
    lat, lon, yr_m, mo_m, tas = load_dataset(cfg)
    frac = build_frac_masks(lat, lon, cfg["subgrid"])
    coslat = np.cos(np.deg2rad(lat))

    years = np.arange(yr_m.min(), yr_m.max() + 1)

    def annualize(mseries):
        out = np.full(len(years), np.nan)
        for k, y in enumerate(years):
            sel = yr_m == y
            if sel.sum() >= MIN_MONTHS and np.isfinite(mseries[sel]).all():
                out[k] = mseries[sel].mean()
        return out

    # per-region monthly via sparse cell indexing (memory-safe for 1-deg fields)
    reg_annual, coverage = {}, {}
    for reg in sorted(frac):
        ii, jj = np.nonzero(frac[reg] > 0)
        w = (frac[reg][ii, jj] * coslat[ii]).astype(np.float32)
        sub = tas[:, ii, jj]                       # (ntime, ncell)
        fin = np.isfinite(sub)
        num = np.where(fin, sub, 0.0) @ w
        den = fin @ w
        series = np.where(den > 0, num / np.maximum(den, 1e-12), np.nan)
        reg_annual[reg] = annualize(series)
        # coverage: unweighted cell fraction + weighted fraction, per period
        cov = {}
        for tag, (y0, y1) in [("pre1901", (yr_m.min(), 1900)), ("early", EARLY_WIN)]:
            msel = (yr_m >= y0) & (yr_m <= y1)
            if msel.any():
                cov[tag + "_cellfrac"] = float(fin[msel].mean())
                cov[tag + "_wfrac"] = float((fin[msel] @ w).mean() / w.sum())
            else:
                cov[tag + "_cellfrac"] = np.nan
                cov[tag + "_wfrac"] = np.nan
        cov["ncells"] = len(ii)
        coverage[reg] = cov

    # global cos-lat mean (chunked over time to bound memory on the 1-deg field)
    w2d = np.repeat(coslat[:, None], len(lon), axis=1).astype(np.float32)
    gnum = np.empty(tas.shape[0])
    gden = np.empty(tas.shape[0])
    for s in range(0, tas.shape[0], 240):
        blk = tas[s:s + 240]
        fin = np.isfinite(blk)
        gnum[s:s + 240] = np.where(fin, blk, 0.0).reshape(len(blk), -1) @ w2d.ravel()
        gden[s:s + 240] = fin.reshape(len(blk), -1) @ w2d.ravel()
    gmst_annual = annualize(np.where(gden > 0, gnum / np.maximum(gden, 1e-12), np.nan))

    # fill missing region-years: OLS on global, NATIVE frame (build_t_glac logic)
    fill_note = {}
    for reg, x in reg_annual.items():
        m = np.isfinite(x) & np.isfinite(gmst_annual)
        miss = ~np.isfinite(x) & np.isfinite(gmst_annual)
        if miss.any():
            A = np.vstack([gmst_annual[m], np.ones(m.sum())]).T
            amp_r, c_r = np.linalg.lstsq(A, x[m], rcond=None)[0]
            x[miss] = amp_r * gmst_annual[miss] + c_r
            fill_note[reg] = (int(miss.sum()), int(years[miss].min()),
                              int(years[miss].max()), float(amp_r))
    del tas
    return dict(name=name, years=years, reg_annual=reg_annual,
                gmst=gmst_annual, coverage=coverage, fill_note=fill_note)


# ------------------------------------------------------------------ amps
def block_series(nat, baseline):
    """Rebase to `baseline` and build R19/SLOWP/FAST/AGG + global (build_reservoir
    weighting: GlaMBIE area within members; then re-baseline the composite)."""
    years = nat["years"]
    bsel = (years >= baseline[0]) & (years <= baseline[1])

    def rebase(x):
        return x - np.nanmean(x[bsel])

    reg = {r: rebase(nat["reg_annual"][r]) for r in SCOPE_REGIONS}
    g = rebase(nat["gmst"])
    out = {}
    for bname, members in SPEC_3RES.items():
        wsum = sum(area_w[r] for r in members)
        drv = sum(area_w[r] / wsum * reg[r] for r in members)
        out[bname] = rebase(drv)                  # build_reservoir re-baselines
    agg = sum(W_AREA[r] * reg[r] for r in SCOPE_REGIONS)
    out["AGG"] = rebase(agg)
    ok = np.isfinite(g)
    for bname in out:
        ok = ok & np.isfinite(out[bname])
    return years, out, g, ok


def amp_fit(y, g, ok, years, y0, y1):
    sel = ok & (years >= y0) & (years <= y1)
    return float(np.sum(g[sel] * y[sel]) / np.sum(g[sel] ** 2)), int(sel.sum())


# ------------------------------------------------------------------ run
print("diag_amp_dataset_comparison | blocks R19/SLOWP/FAST/AGG | "
      f"windows {AMP_WINDOWS} | through-origin amp on each dataset's own global")

natives = {}
for name, cfg in DATASETS.items():
    print(f"  extracting {name} ({cfg['note']}) ...")
    natives[name] = extract_native(name, cfg)
    fn = natives[name]["fill_note"]
    if fn:
        tot = sum(v[0] for v in fn.values())
        rng = (min(v[1] for v in fn.values()), max(v[2] for v in fn.values()))
        print(f"    filled region-years: {tot} across {len(fn)} regions "
              f"({rng[0]}-{rng[1]}); largest: "
              + ", ".join(f"r{r:02d}={v[0]}yr(amp_r={v[3]:.2f})"
                          for r, v in sorted(fn.items(),
                                             key=lambda kv: -kv[1][0])[:4]))

rows = []
series_store = {}          # (dataset, baseline) -> (years, blocks, g, ok)
runs = [(n, DATASETS[n]["baseline"]) for n in DATASETS]
runs += [(n, ALT_BASELINE) for n in DATASETS
         if DATASETS[n]["baseline"] != ALT_BASELINE]
for name, base in runs:
    years, blocks, g, ok = block_series(natives[name], base)
    series_store[(name, base)] = (years, blocks, g, ok)
    for bname in ["R19", "SLOWP", "FAST", "AGG"]:
        for (y0, y1) in AMP_WINDOWS:
            a, n = amp_fit(blocks[bname], g, ok, years, y0, y1)
            rows.append(dict(dataset=name, baseline=f"{base[0]}-{base[1]}",
                             block=bname, window=f"{y0}-{y1}", amp=a, n_years=n))
res = pd.DataFrame(rows)
os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
res.to_csv(OUT_CSV, index=False, float_format="%.4f")

# ------------------------------------------------------------------ self-test
ref = pd.read_csv(REF_CONST).set_index("block")["amp_obsfit"]
ref_agg = {(1901, 2024): 1.595, (1970, 2024): 1.561}   # t_glac provenance md
print("\n== self-test: HadCRUT5 (1850-1900 baseline) vs committed references ==")
selftest_ok = True
had = res[(res.dataset == "HadCRUT5") & (res.baseline == "1850-1900")]
for bname in ["R19", "SLOWP", "FAST"]:
    a = float(had[(had.block == bname) & (had.window == "1901-2024")]["amp"].iloc[0])
    d = a - float(ref[bname])
    flag = "PASS" if abs(d) <= SELFTEST_TOL else "FAIL"
    selftest_ok &= abs(d) <= SELFTEST_TOL
    print(f"  {bname:5s} 1901-2024: {a:.4f} vs extc {float(ref[bname]):.4f} "
          f"(diff {d:+.4f}) {flag}")
for (y0, y1), rv in ref_agg.items():
    a = float(had[(had.block == "AGG") & (had.window == f"{y0}-{y1}")]["amp"].iloc[0])
    d = a - rv
    flag = "PASS" if abs(d) <= SELFTEST_TOL else "FAIL"
    selftest_ok &= abs(d) <= SELFTEST_TOL
    print(f"  AGG   {y0}-{y1}: {a:.4f} vs provenance {rv:.3f} (diff {d:+.4f}) {flag}")
print(f"  SELF-TEST {'PASSED' if selftest_ok else 'FAILED'} (tol {SELFTEST_TOL})")

# ------------------------------------------------------------------ diagnostics
print("\n== SLOWP-block series: HadCRUT5 vs alternatives ==")
cov_rows = []
for alt in ["BerkeleyEarth", "GISTEMP1200"]:
    base = ALT_BASELINE if alt == "GISTEMP1200" else DATASETS[alt]["baseline"]
    hyears, hblk, _, hok = series_store[("HadCRUT5", base)]
    ayears, ablk, _, aok = series_store[(alt, base)]
    h = pd.Series(hblk["SLOWP"], index=hyears)[hok]
    a = pd.Series(ablk["SLOWP"], index=ayears)[aok]
    common = h.index.intersection(a.index)
    hc, ac = h.loc[common], a.loc[common]
    r_full = float(np.corrcoef(hc, ac)[0, 1])
    esel = (common >= EARLY_WIN[0]) & (common <= EARLY_WIN[1])
    r_early = float(np.corrcoef(hc[esel], ac[esel])[0, 1])
    diff = (ac - hc).rolling(ROLL_YEARS, center=True).mean()
    dmax_yr = int(diff.abs().idxmax())
    print(f"  {alt} (common {common.min()}-{common.max()}, baseline {base[0]}-{base[1]}):")
    print(f"    corr full {r_full:.3f} | corr {EARLY_WIN[0]}-{EARLY_WIN[1]} {r_early:.3f}"
          f" | max |{ROLL_YEARS}yr-mean diff| {diff.abs().max():.3f} C at {dmax_yr}"
          f" | mean diff {EARLY_WIN[0]}-{EARLY_WIN[1]} {float(ac[esel].mean()-hc[esel].mean()):+.3f} C")
    cov_rows.append(dict(dataset=alt, metric="slowp_corr_full", value=r_full))
    cov_rows.append(dict(dataset=alt, metric="slowp_corr_early", value=r_early))
    cov_rows.append(dict(dataset=alt, metric="slowp_maxdiff_11yr_C", value=float(diff.abs().max())))
    cov_rows.append(dict(dataset=alt, metric="slowp_maxdiff_year", value=dmax_yr))

print("\n== early-period data coverage (fraction of region cells non-missing) ==")
print(f"   periods: pre1901 = dataset start-1900; early = {EARLY_WIN[0]}-{EARLY_WIN[1]}")
for name in DATASETS:
    cov = natives[name]["coverage"]
    for label, regs_ in [("R19", [19]), ("SLOWP", SPEC_3RES["SLOWP"])]:
        for tag in ["pre1901", "early"]:
            cf = np.nanmean([cov[r][tag + "_cellfrac"] for r in regs_])
            wf = np.nanmean([cov[r][tag + "_wfrac"] for r in regs_])
            cov_rows.append(dict(dataset=name, metric=f"{label}_{tag}_cellfrac", value=cf))
            cov_rows.append(dict(dataset=name, metric=f"{label}_{tag}_wfrac", value=wf))
        print(f"  {name:13s} {label:5s}: pre1901 cells "
              f"{np.nanmean([cov[r]['pre1901_cellfrac'] for r in regs_]):.2f} "
              f"(wtd {np.nanmean([cov[r]['pre1901_wfrac'] for r in regs_]):.2f}) | "
              f"early cells {np.nanmean([cov[r]['early_cellfrac'] for r in regs_]):.2f} "
              f"(wtd {np.nanmean([cov[r]['early_wfrac'] for r in regs_]):.2f})")
pd.DataFrame(cov_rows).to_csv(OUT_COV, index=False, float_format="%.4f")

# ------------------------------------------------------------------ table
print("\n== amp comparison (through-origin, each dataset's own global) ==")
piv = res.pivot_table(index=["dataset", "baseline"], columns=["block", "window"],
                      values="amp")
piv = piv.reindex(columns=pd.MultiIndex.from_product(
    [["R19", "SLOWP", "FAST", "AGG"], [f"{a}-{b}" for a, b in AMP_WINDOWS]]))
with pd.option_context("display.width", 160, "display.float_format", "{:.3f}".format):
    print(piv)

print(f"\nWrote {os.path.relpath(OUT_CSV, REPO)}, {os.path.relpath(OUT_COV, REPO)}")
