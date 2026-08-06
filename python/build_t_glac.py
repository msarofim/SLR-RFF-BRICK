#!/usr/bin/env python3
"""
build_t_glac.py — glacier-area-weighted observed temperature series T_glac(t).

Option D data-prep (handoff_2026-08-06_glacier_structural_nu_decision.md §2):
the decadal glacier-melt shape is not a GMST shape (ETCW: Arctic warming
3-4x global by 1930-40 on most of the world's glacier area — memo §3d), so
we build the temperature the GLACIERS saw, to drive the Mengel/Nauels glacier
component historically in the D0 shootout.

Construction (all choices explicit; see PROVENANCE block written alongside):
  * Temperature field: HadCRUT5.0.2.0 ANALYSIS (statistically infilled)
    ensemble-mean monthly anomalies, 5-deg grid, 1850-present, rel 1961-1990.
    (Analysis variant chosen for pre-1930 Arctic coverage; the infilling is
    heaviest exactly in the early-Arctic window — documented caveat.)
  * Regions: GTN-G Glacier Regions 2023 first-order polygons
    (DOI 10.5904/gtng-glacreg-2023-07). The 2023 scheme splits RGI6 region 19
    into 19 (Subantarctic islands) + 20 (Antarctic mainland periphery); both
    are merged back into "r19" to match the RGI6 / GlaMBIE scope.
  * Region -> grid: fractional overlap of each 5-deg cell with the region
    polygon, via a SUBGRID x SUBGRID point-in-polygon test per cell
    (small regions like Iceland would otherwise catch zero cell centres).
  * Scope: regions 1-18 minus 5, plus 19 — the excl-r5-incl-r19 scope of the
    A2 inventory V = 0.290 (memo §2c; r5 lives in the GIS target).
  * Weights (headline): GlaMBIE per-region glacier area at year 2000
    (on-disk glambie_data.zip, DOI 10.5904/wgms-glambie-2024-07).
    Sensitivity: |cumulative 2000-2023 mass loss| share (melt-flux weights).
  * Annual = calendar-year mean of the 12 monthly values (per the
    Berkeley-parser calendar-year discipline); year kept only if >= MIN_MONTHS.
  * Baseline: anomalies re-referenced to 1850-1900 (multi-year baseline rule).

Outputs:
  data/observations/t_glac_hadcrut5.csv          (year, t_glac_C, t_glac_massloss_C, gmst_hadcrut5_C)
  data/observations/t_glac_regions_hadcrut5.csv  (year, r01..r19 annual anomalies rel 1850-1900)
  data/observations/t_glac_hadcrut5_provenance.md
  figures/t_glac_vs_gmst.png
"""
import os
import subprocess
import zipfile

import numpy as np
import pandas as pd

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
HAD_NC = os.path.join(REPO, "data/observations/raw/HadCRUT.5.0.2.0.analysis.anomalies.ensemble_mean.nc")
SHP = os.path.join(REPO, "data/observations/raw/GlacReg_2023/GTN-G_202307_o1regions.shp")
GLAMBIE_ZIP = os.path.join(REPO, "data/observations/raw/glambie_data.zip")
OUT_CSV = os.path.join(REPO, "data/observations/t_glac_hadcrut5.csv")
OUT_REG = os.path.join(REPO, "data/observations/t_glac_regions_hadcrut5.csv")
OUT_PROV = os.path.join(REPO, "data/observations/t_glac_hadcrut5_provenance.md")
OUT_FIG = os.path.join(REPO, "figures/t_glac_vs_gmst.png")

SCOPE_REGIONS = [r for r in range(1, 20) if r != 5]   # excl r5, incl r19 (V=0.290 scope)
MERGE_INTO_19 = {20}          # GTN-G 2023 splits RGI6 r19 into 19+20; merge back
SUBGRID = 5                   # per-5deg-cell fractional-overlap subsampling (SUBGRID^2 pts)
BASE0, BASE1 = 1850, 1900     # anomaly baseline
MIN_MONTHS = 12               # calendar-year completeness required
AMP_WINDOWS = [(1901, 2024), (1970, 2024)]   # amp_g regression windows (rel-baseline anomalies)
ETCW_WIN = (1930, 1940)       # ETCW reporting window
GLAMBIE_AREA_YEAR = 2000.0    # weight = glacier_area at this start_date

COMMIT = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True).stdout.strip()

# ------------------------------------------------------------------ regions
import shapefile as pyshp                     # pyshp
from matplotlib.path import Path

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

# ------------------------------------------------------------------ grid masks
import netCDF4

nc = netCDF4.Dataset(HAD_NC)
VAR = "tas_mean"
lat = nc.variables["latitude"][:]
lon = nc.variables["longitude"][:]
tv = nc.variables["time"]
dates = netCDF4.num2date(tv[:], tv.units, getattr(tv, "calendar", "standard"))
yr_m = np.array([d.year for d in dates])
mo_m = np.array([d.month for d in dates])

dlat = np.abs(np.diff(lat)).mean()
dlon = np.abs(np.diff(lon)).mean()
off = (np.arange(SUBGRID) + 0.5) / SUBGRID - 0.5

frac = {}     # region -> (nlat, nlon) fractional overlap
for reg, rings in sorted(rings_by_region.items()):
    f = np.zeros((len(lat), len(lon)))
    for i, la in enumerate(lat):
        sub_la = la + off * dlat
        for j, lo in enumerate(lon):
            sub_lo = lo + off * dlon
            pts = np.array([(x, y) for y in sub_la for x in sub_lo])
            inside = np.zeros(len(pts), dtype=bool)
            for ring in rings:
                inside |= ring.contains_points(pts)
            # dateline wrap: retry shifted copies for polygons stored in 0..360 or crossing
            if not inside.any():
                for shift in (360.0, -360.0):
                    pts2 = pts.copy(); pts2[:, 0] += shift
                    for ring in rings:
                        inside |= ring.contains_points(pts2)
            f[i, j] = inside.mean()
    frac[reg] = f

# ------------------------------------------------------------------ weights
with zipfile.ZipFile(GLAMBIE_ZIP) as z:
    names = {int(os.path.basename(n).split("_")[0]): n
             for n in z.namelist()
             if "calendar_years/" in n and n.endswith(".csv")
             and os.path.basename(n).split("_")[0].isdigit()
             and int(os.path.basename(n).split("_")[0]) >= 1}
    area_w, loss_w = {}, {}
    for reg, n in names.items():
        df = pd.read_csv(z.open(n))
        row0 = df.loc[np.isclose(df["start_dates"], GLAMBIE_AREA_YEAR)]
        area_w[reg] = float(row0["glacier_area"].iloc[0])
        loss_w[reg] = abs(float(df["combined_gt"].sum()))

def normalize(w):
    tot = sum(w[r] for r in SCOPE_REGIONS)
    return {r: w[r] / tot for r in SCOPE_REGIONS}

W_AREA = normalize(area_w)
W_LOSS = normalize(loss_w)

# ------------------------------------------------------------------ per-region series
tas = nc.variables[VAR][:]                     # (time, lat, lon), masked array
tas = np.ma.filled(tas, np.nan)
coslat = np.cos(np.deg2rad(lat))[:, None]

reg_monthly = {}
cov_report = {}
for reg in sorted(frac):
    w2d = frac[reg] * coslat
    wsum_full = w2d.sum()
    if wsum_full == 0:
        raise RuntimeError(f"region {reg:02d}: polygon captured no grid area")
    wt = np.where(np.isfinite(tas), w2d[None, :, :], 0.0)
    num = np.nansum(np.where(np.isfinite(tas), tas, 0.0) * w2d[None, :, :], axis=(1, 2))
    den = wt.sum(axis=(1, 2))
    series = np.where(den > 0, num / np.maximum(den, 1e-12), np.nan)
    reg_monthly[reg] = series
    cov_report[reg] = (float((frac[reg] > 0).sum()), float(den.min() / wsum_full),
                       float(den[yr_m < 1900].mean() / wsum_full) if (yr_m < 1900).any() else np.nan)

years = np.arange(yr_m.min(), yr_m.max() + 1)
def annualize(mseries):
    out = np.full(len(years), np.nan)
    for k, y in enumerate(years):
        sel = yr_m == y
        if sel.sum() >= MIN_MONTHS and np.isfinite(mseries[sel]).all():
            out[k] = mseries[sel].mean()
    return out

reg_annual = {reg: annualize(s) for reg, s in reg_monthly.items()}

# global HadCRUT5 (cos-lat mean of the full field) for amp_g reference
gnum = np.nansum(np.where(np.isfinite(tas), tas, 0.0) * coslat[None, :, :], axis=(1, 2))
gden = np.where(np.isfinite(tas), coslat[None, :, :], 0.0).sum(axis=(1, 2))
gmst_annual = annualize(gnum / np.maximum(gden, 1e-12))

# ---- fill missing region-YEARS (all pre-1898: early Arctic/HMA months with zero
# coverage) by per-region OLS on the global series in the NATIVE (1961-1990) frame:
# region ~ amp_r * global + c_r over all jointly-available years. Keeps every
# region complete back to 1850 so the composite and the 1850-1900 baseline exist;
# filled years carry scaled-global (no regional internal variability) — reported
# and stored in the fill_frac column.
fill_note = {}
fill_mask = {}
for reg, x in reg_annual.items():
    m = np.isfinite(x) & np.isfinite(gmst_annual)
    miss = ~np.isfinite(x) & np.isfinite(gmst_annual)
    fill_mask[reg] = miss
    if miss.any():
        A = np.vstack([gmst_annual[m], np.ones(m.sum())]).T
        amp_r, c_r = np.linalg.lstsq(A, x[m], rcond=None)[0]
        x[miss] = amp_r * gmst_annual[miss] + c_r
        fill_note[reg] = (int(miss.sum()), int(years[miss].min()), int(years[miss].max()),
                          float(amp_r))

def rebase(x):
    sel = (years >= BASE0) & (years <= BASE1)
    return x - np.nanmean(x[sel])

reg_annual = {r: rebase(x) for r, x in reg_annual.items()}
gmst_annual = rebase(gmst_annual)

t_glac_area = np.nansum([W_AREA[r] * reg_annual[r] for r in SCOPE_REGIONS], axis=0)
t_glac_loss = np.nansum([W_LOSS[r] * reg_annual[r] for r in SCOPE_REGIONS], axis=0)
ok = np.all([np.isfinite(reg_annual[r]) for r in SCOPE_REGIONS], axis=0) & np.isfinite(gmst_annual)
t_glac_area[~ok] = np.nan
t_glac_loss[~ok] = np.nan
fill_frac = np.sum([W_AREA[r] * fill_mask[r].astype(float) for r in SCOPE_REGIONS], axis=0)

# ------------------------------------------------------------------ amp_g + ETCW report
def amp_fit(tg, y0, y1):
    sel = ok & (years >= y0) & (years <= y1)
    x, yv = gmst_annual[sel], tg[sel]
    return float(np.sum(x * yv) / np.sum(x * x))     # through-origin (both rel 1850-1900)

print(f"build_t_glac | HadCRUT5.0.2.0 analysis ens-mean | GTN-G 2023 regions | "
      f"GlaMBIE weights | commit={COMMIT}")
print(f"  coverage: obs years {years[ok].min()}-{years[ok].max()}")
print(f"  region cells>0 / min monthly coverage / pre-1900 coverage:")
for reg in sorted(frac):
    ncell, cmin, cpre = cov_report[reg]
    star = "*" if reg in SCOPE_REGIONS else " (excl)"
    print(f"    r{reg:02d}{star}: {int(ncell):4d} cells  min {cmin:.2f}  pre1900 {cpre:.2f}")
print("  weights (area | loss-share), scope excl r5 incl r19:")
for reg in SCOPE_REGIONS:
    print(f"    r{reg:02d}: {100*W_AREA[reg]:5.1f}% | {100*W_LOSS[reg]:5.1f}%")

if fill_note:
    print("  pre-1900 region-year fills (region ~ amp_r*global + c_r, native frame):")
    for reg, (nmiss, y0f, y1f, amp_r) in sorted(fill_note.items()):
        print(f"    r{reg:02d}: {nmiss:2d} yr filled ({y0f}-{y1f}), amp_r={amp_r:.2f}")
    print(f"  max composite fill fraction: {100*fill_frac.max():.1f}% of weight "
          f"(only years <= {max(v[2] for v in fill_note.values())})")

sel_etcw = ok & (years >= ETCW_WIN[0]) & (years <= ETCW_WIN[1])
print(f"\n  ETCW {ETCW_WIN[0]}-{ETCW_WIN[1]} mean anomaly rel {BASE0}-{BASE1}: "
      f"T_glac(area) {np.nanmean(t_glac_area[sel_etcw]):+.3f} C vs global "
      f"{np.nanmean(gmst_annual[sel_etcw]):+.3f} C  (ratio "
      f"{np.nanmean(t_glac_area[sel_etcw])/np.nanmean(gmst_annual[sel_etcw]):.2f}x)")
amps = {}
for (y0, y1) in AMP_WINDOWS:
    amps[(y0, y1)] = (amp_fit(t_glac_area, y0, y1), amp_fit(t_glac_loss, y0, y1))
    print(f"  amp_g (through-origin fit {y0}-{y1}): area {amps[(y0,y1)][0]:.2f}  "
          f"loss-share {amps[(y0,y1)][1]:.2f}   (GlacierMIP3 fixed value: 1.8)")

# ------------------------------------------------------------------ outputs
os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
out = pd.DataFrame({"year": years[ok],
                    "t_glac_C": t_glac_area[ok],
                    "t_glac_massloss_C": t_glac_loss[ok],
                    "gmst_hadcrut5_C": gmst_annual[ok],
                    "fill_frac": fill_frac[ok]})
out.to_csv(OUT_CSV, index=False, float_format="%.5f")

reg_out = pd.DataFrame({"year": years})
for reg in sorted(reg_annual):
    reg_out[f"r{reg:02d}"] = reg_annual[reg]
reg_out = reg_out[np.isfinite(reg_out.drop(columns="year")).any(axis=1).to_numpy()]
reg_out.to_csv(OUT_REG, index=False, float_format="%.5f")

with open(OUT_PROV, "w") as fh:
    fh.write(f"""# t_glac_hadcrut5.csv provenance

Generated by `python/build_t_glac.py`, commit {COMMIT}.

| item | value |
|---|---|
| temperature field | HadCRUT.5.0.2.0 analysis (infilled) ensemble-mean monthly anomalies, 5 deg (Met Office HadOBS, Morice et al. 2021 JGR 126, doi:10.1029/2019JD032361) |
| region polygons | GTN-G Glacier Regions 2023, first order (DOI 10.5904/gtng-glacreg-2023-07); 2023 regions 19+20 merged back to RGI6 r19 |
| region-cell mapping | fractional overlap, {SUBGRID}x{SUBGRID} point-in-polygon subsample per 5-deg cell |
| scope | RGI6 regions 1-18 minus 5, plus 19 (matches A2 inventory V=0.290; r5 belongs to the GIS target) |
| weights (t_glac_C) | GlaMBIE year-{GLAMBIE_AREA_YEAR:.0f} glacier_area per region (DOI 10.5904/wgms-glambie-2024-07) |
| weights (t_glac_massloss_C) | abs cumulative 2000-2023 GlaMBIE combined_gt share (melt-flux sensitivity arm) |
| annualization | calendar-year mean, all {MIN_MONTHS} months required |
| baseline | anomalies re-referenced to {BASE0}-{BASE1} (each region + global separately) |
| gmst_hadcrut5_C | cos-lat global mean of the same field, same baseline (for amp_g fits) |

Missing region-YEARS (all pre-1898: r03 1850-97 is the largest; also r14/r15
pre-1875, r18 pre-1855, r01 1855) are filled with that region's OLS fit on the
global series (native frame) — filled years carry NO regional internal
variability; the per-year weighted fill share is the fill_frac column.
Caveats: pre-1930 Arctic values are heavily statistically infilled (fewest
stations exactly where the weights are largest); blended land+ocean anomalies,
not land-only; annual-mean, not melt-season-weighted. The ETCW pulse is
internal variability — projection drivers must NOT contain such pulses
(splice to amp_g x GMST forward; handoff Option D).

amp_g through-origin fits (T_glac on HadCRUT5 global, both rel {BASE0}-{BASE1}):
""")
    for (y0, y1), (aa, al) in amps.items():
        fh.write(f"  * {y0}-{y1}: area-weight {aa:.3f}, loss-share-weight {al:.3f}\n")
    fh.write(f"  * GlacierMIP3 glacier-area warming ratio (fixed alternative): 1.8\n")

# ------------------------------------------------------------------ figure
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True, constrained_layout=True)
ax1.plot(years[ok], gmst_annual[ok], color="0.3", lw=1.2, label="HadCRUT5 global")
ax1.plot(years[ok], t_glac_area[ok], color="tab:red", lw=1.2,
         label="T_glac (GlaMBIE-area weights, excl r5 incl r19)")
ax1.plot(years[ok], t_glac_loss[ok], color="tab:orange", lw=0.9, alpha=0.7,
         label="T_glac (2000-23 mass-loss-share weights)")
ax1.axvspan(*ETCW_WIN, color="tab:blue", alpha=0.10, label=f"ETCW window {ETCW_WIN[0]}-{ETCW_WIN[1]}")
ax1.axhline(0, color="k", lw=0.6)
ax1.set(ylabel=f"anomaly rel {BASE0}-{BASE1} (C)",
        title="Glacier-area-weighted observed temperature vs global mean (annual)")
ax1.legend(fontsize=8)

d = t_glac_area - gmst_annual
ax2.plot(years[ok], d[ok], color="tab:purple", lw=1.0)
ax2.plot(years[ok], pd.Series(d[ok]).rolling(11, center=True).mean(), color="k", lw=1.6,
         label="11-yr running mean")
ax2.axvspan(*ETCW_WIN, color="tab:blue", alpha=0.10)
ax2.axhline(0, color="k", lw=0.6)
ax2.set(xlabel="year", ylabel="T_glac − global (C)",
        title="Glacier-area excess warming (the ETCW signal the GMST driver misses)")
ax2.legend(fontsize=8)
amp_str = ", ".join(f"{y0}-{y1}: {aa:.2f}" for (y0, y1), (aa, _) in amps.items())
fig.suptitle(f"T_glac build — HadCRUT5.0.2.0 analysis, GTN-G 2023 regions, GlaMBIE weights | "
             f"amp_g fits {amp_str} | commit {COMMIT}", fontsize=9)
os.makedirs(os.path.dirname(OUT_FIG), exist_ok=True)
fig.savefig(OUT_FIG, dpi=150)
print(f"\nWrote {os.path.relpath(OUT_CSV, REPO)}, {os.path.relpath(OUT_REG, REPO)}, "
      f"{os.path.relpath(OUT_PROV, REPO)}, {os.path.relpath(OUT_FIG, REPO)}")
