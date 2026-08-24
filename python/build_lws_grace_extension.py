#!/usr/bin/env python3
"""
build_lws_grace_extension.py -- extend the LWS (terrestrial water storage) target past
2018 with GRACE/GRACE-FO, replacing the hold-flat fiat.

WHY. LWS is the ONE component of the recalibration target set with no modern extension:
Frederikse's TWS ensemble ends 2018 and `prep_recalib_targets_ext.py:311` holds lws, lws_lo
and lws_hi at their 2018 values through 2026 by fiat. That is not cosmetic -- LWS enters the
likelihood TWICE, both on the total stream (`calibrate_mcmc_ext.jl:1387` adds observed LWS to
the MODELLED total, and `:568` folds its band into the total's observation sigma), so for
2019+ the fit is told as data that land water storage contributed exactly zero, with a
real-data error bar. Marcus, 2026-08-24: build it from the JPL mascons (option 1).

WHAT IT PRODUCES. An annual LWS series in cm of sea-level equivalent, on the same convention
and the same 1995-2005 reference frame as every other component target.

  LWS = (GRACE land mass, ice sheets masked out) - (GlaMBIE glaciers, 17 regions)

⚠ IT DOES NOT WIRE ITSELF IN. `outputs/recalib_targets_ext.csv` is left UNCHANGED and the
calibration still sees the fiat. Marcus 2026-08-24: "wait to recalibrate until we have
something else worth recalibrating" -- swapping a fitted target is a recalibration trigger,
and the measured level change does not justify one on its own (see [RESULT] below). This file
exists so that when a recalibration IS run for other reasons, the LWS extension is ready.

THE SCOPE RULE (Marcus, 2026-08-24): exclude any glacier region that loses mass over the
period, since its melt is indistinguishable from LWS in the gravity field. Measured on
GlaMBIE's own per-region files: ALL 19 RGI regions lose mass over 2019-2023, so the
"regions we can assume don't melt" set is EMPTY and the rule resolves to "mask all glaciers".

⚠ AND GLACIERS CANNOT BE MASKED SPATIALLY. The GTN-G o1 files are REGION outlines, not
glacier outlines: region 16 "Low Latitudes" spans a 134 Mkm2 bbox for 1770 km2 of glacier
(75000:1), region 10 spans 41 Mkm2 for 2270 km2. Masking those polygons would delete the
tropics and most of Eurasia -- i.e. the whole signal. So the ICE SHEETS are masked spatially
(ice covers those landmasses, and the masks GATE against JPL's own published series) and the
GLACIERS are removed by subtracting GlaMBIE region by region. Region 5 falls inside the
Greenland mask and region 19 has ZERO land cells at 0.5 deg, so exactly 17 regions are
subtracted -- no double-count, no gap.

  python3 python/build_lws_grace_extension.py [--tag=L14]
Writes outputs/lws_grace_extension_<tag>.csv, outputs/lws_grace_extension_<tag>.png,
       outputs/log_lws_grace_extension_<tag>.txt (via shell redirect)
"""
import glob
import os
import sys

import numpy as np
import pandas as pd
import shapefile
import xarray as xr
from matplotlib.path import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--tag=")), "L14")

# ---- provenance: every label and filename below derives from these -------------
MASCON_GLOB = os.path.join(REPO, "data/observations/raw", "GRCTellus.JPL.*.GLO.RL06.3M.MSCNv04CRI.nc")
MASCON_NAME = "JPL GRACE/GRACE-FO mascon RL06.3Mv04 CRI"
MASCON_DOI = "10.5067/TEMSC-3JC634"
GTNG = os.path.join(REPO, "data/observations/raw/GlacReg_2023/GTN-G_202307_o1regions")
GTNG_DOI = "10.5904/gtng-glacreg-2023-07"
GLAMBIE_DIR = os.path.join(REPO, "data/observations/raw/glambie_calendar_years")
GLAMBIE_NAME = "GlaMBIE 2025"
TARGETS = os.path.join(REPO, "outputs", "recalib_targets_ext.csv")
FRED_NAME = "Frederikse 2020 TWS"

# ---- physical / grid constants -------------------------------------------------
R_EARTH_KM = 6371.0072
CM_KM2_TO_GT = 1e-5        # 1 cm of water over 1 km2 = 1e4 m3 = 1e7 kg = 1e-5 Gt.
                           # ⚠ getting this wrong by 1e3 makes the Greenland gate read 0.0010.
GT_PER_CM_SLE = 3620.0     # 362 Gt/mm, the repo convention (prep_recalib_targets_ext.py)
EARTH_AREA_KM2 = 5.101e8   # for the [AREA] gate

# ---- masking / scope -----------------------------------------------------------
GIS_REGION = "05"          # GTN-G Greenland; the polygon covers the ice sheet + periphery
AIS_REGION = "20"          # GTN-G Antarctic Mainland
AIS_SWEEP_LAT = -60.0      # ⚠ the region-20 polygon MISSES land cells; see [ANT-SWEEP]
GLACIER_EXCLUDE = {"5", "19"}   # 5 is inside the GIS mask; 19 has no land cells at 0.5 deg

# ---- time handling -------------------------------------------------------------
N_HARMONICS = 2            # annual + semi-annual, for [SEAS]
MIN_MONTHS = 4             # a year needs this many samples even after deseasonalising
OVERLAP = (2003, 2018)     # offset-match window; Frederikse's TWS ends 2018
SPLICE_FROM = 2019
GLAMBIE_LAST = 2023        # GlaMBIE ends here -> see HOLD_LAST
HOLD_LAST = 2024           # Marcus 2026-08-24: hold 2024 flat from 2023 rather than drop it
EXT_LAST = 2026            # the target file's own horizon

# ---- gate thresholds -----------------------------------------------------------
ICE_GATE_TOL = 0.02        # |ratio-1| against JPL's own published ice-sheet series
AREA_GATE_TOL = 0.001
OUT_CSV = os.path.join(REPO, "outputs", f"lws_grace_extension_{TAG}.csv")
OUT_PNG = os.path.join(REPO, "outputs", f"lws_grace_extension_{TAG}.png")

print(f"LWS GRACE EXTENSION | tag {TAG}")
print(f"  source   {MASCON_NAME}  doi {MASCON_DOI}")
print(f"  regions  GTN-G 2023 o1  doi {GTNG_DOI}")
print(f"  glaciers {GLAMBIE_NAME}, all regions except {sorted(GLACIER_EXCLUDE)}")
print(f"  splice   {SPLICE_FROM}-{GLAMBIE_LAST}, then HELD FLAT through {HOLD_LAST} "
      f"({GLAMBIE_NAME} ends {GLAMBIE_LAST})")
print(f"  ⚠ this script does NOT modify {os.path.basename(TARGETS)} -- see the module docstring")

src = sorted(glob.glob(MASCON_GLOB))
if not src:
    raise SystemExit(f"no mascon file matching {MASCON_GLOB}")
ds = xr.open_dataset(src[-1])
print(f"  file     {os.path.basename(src[-1])} ({ds.sizes['time']} months)")

lat, lon = ds.lat.values, ds.lon.values
lon180 = np.where(lon > 180, lon - 360, lon)
LON, LAT = np.meshgrid(lon180, lat)
pts = np.column_stack([LON.ravel(), LAT.ravel()])
land = ds.land_mask.values == 1
lwe = ds.lwe_thickness.values
lb = ds.lat_bounds.values
dlon_deg = float(abs(np.diff(np.sort(lon))[0]))
area = (R_EARTH_KM ** 2 * np.deg2rad(dlon_deg)
        * (np.sin(np.deg2rad(lb[:, 1])) - np.sin(np.deg2rad(lb[:, 0]))))[:, None] \
       * np.ones((1, len(lon)))
t = pd.to_datetime(ds.time.values)
tdec = t.year + (t.dayofyear - 1) / 365.25


def region_mask(code):
    """Union of all polygon parts of one GTN-G o1 region, on the mascon grid."""
    sf = shapefile.Reader(GTNG)
    m = np.zeros(len(pts), bool)
    for s, r in zip(sf.shapes(), sf.records()):
        if str(r[0]) != code:
            continue
        parts = list(s.parts) + [len(s.points)]
        for a, b in zip(parts[:-1], parts[1:]):
            if b - a >= 3:
                m |= Path(np.asarray(s.points[a:b])).contains_points(pts)
    return m.reshape(LAT.shape)


def mass_gt(mask):
    """Mass anomaly time series over a mask, Gt."""
    return np.nansum(lwe * (area * mask)[None, :, :], axis=(1, 2)) * CM_KM2_TO_GT


print("\n" + "=" * 78 + "\nGATES\n" + "=" * 78)
ok_area = abs(area.sum() / EARTH_AREA_KM2 - 1) < AREA_GATE_TOL
print(f"[AREA]  grid sums to {area.sum():.4e} km2 vs {EARTH_AREA_KM2:.4e} -> "
      f"{'PASS' if ok_area else 'FAIL'}")
assert ok_area

m_gis = region_mask(GIS_REGION) & land
m_ais_poly = region_mask(AIS_REGION) & land
m_south = land & (lat[:, None] < AIS_SWEEP_LAT)
m_ais = m_ais_poly | m_south

# [ANT-SWEEP] the GTN-G Antarctic polygon does not cover every Antarctic land cell at 0.5 deg.
missed = m_south & ~m_ais_poly
A = np.vstack([np.ones(len(tdec)), tdec - tdec[0]]).T
tr_missed = np.linalg.lstsq(A, mass_gt(missed), rcond=None)[0][1]
print(f"[ANT-SWEEP] the region-{AIS_REGION} polygon misses {missed.sum()} land cells worth "
      f"{tr_missed:+.2f} Gt/yr -> swept in via lat < {AIS_SWEEP_LAT}")

# [GRL]/[ANT] -- the masks must reproduce JPL's OWN published series from the SAME solution.
for code, name, ref, mask in (("GRL", "Greenland", "grace_greenland_mass.txt", m_gis),
                              ("ANT", "Antarctica", "grace_antarctica_mass.txt", m_ais)):
    r = np.loadtxt(os.path.join(REPO, "data/observations/raw", ref), comments="HDR")
    idx = np.array([np.argmin(abs(r[:, 0] - x)) for x in tdec])
    sel = np.array([abs(r[i, 0] - x) < 0.02 for i, x in zip(idx, tdec)])
    v = mass_gt(mask)
    ours = v[sel] - v[sel][0]
    theirs = r[idx[sel], 1] - r[idx[sel], 1][0]
    Ag = np.vstack([np.ones(sel.sum()), tdec[sel] - tdec[sel][0]]).T
    bo = np.linalg.lstsq(Ag, ours, rcond=None)[0][1]
    bt = np.linalg.lstsq(Ag, theirs, rcond=None)[0][1]
    good = abs(bo / bt - 1) < ICE_GATE_TOL
    print(f"[{code}]   {name:10s} our trend {bo:8.2f} vs JPL {bt:8.2f} Gt/yr | ratio "
          f"{bo / bt:.4f} | rms {np.sqrt(((ours - theirs) ** 2).mean()):5.1f} Gt -> "
          f"{'PASS' if good else 'FAIL'}")
    assert good, f"{name} mask does not reproduce the published series"

ice = m_gis | m_ais
dom = land & ~ice
print(f"[DOMAIN] LWS domain {dom.sum()} cells, {area[dom].sum() / 1e6:.2f} Mkm2 "
      f"(global land minus both ice sheets)")

# [SCOPE] region 19 must contribute no land cells, or the GlaMBIE exclusion below is wrong.
n19 = (region_mask("19") & dom).sum()
print(f"[SCOPE] region-19 land cells inside the domain: {n19} -> "
      f"{'PASS (nothing to subtract)' if n19 == 0 else 'FAIL'}")
assert n19 == 0

# [SEAS] deseasonalise BEFORE annual means: 2011-2018 have as few as 5 months, and a raw
# annual mean over those averages the wrong SEASONS, not a year.
g = mass_gt(dom)
frac = (t.dayofyear - 1) / 365.25
X = np.column_stack([np.ones(len(t))] +
                    [f(2 * np.pi * k * frac) for k in range(1, N_HARMONICS + 1)
                     for f in (np.sin, np.cos)])
seas = X[:, 1:] @ np.linalg.lstsq(X, g, rcond=None)[0][1:]
gd = pd.Series(g - seas, index=t.year)
print(f"[SEAS]  removed a {seas.max() - seas.min():.0f} Gt peak-to-peak annual cycle "
      f"({N_HARMONICS} harmonics)")
ann, nmo = gd.groupby(level=0).mean(), gd.groupby(level=0).count()
yrs = np.array([y for y in range(2003, HOLD_LAST + 1)
                if nmo.get(y, 0) >= MIN_MONTHS and y <= GLAMBIE_LAST])

# ---- glaciers: GlaMBIE, region by region ---------------------------------------
gl = {}
for f in sorted(glob.glob(os.path.join(GLAMBIE_DIR, "*.csv"))):
    code = os.path.basename(f)[:-4].split("_")[0]
    if code == "0" or code in GLACIER_EXCLUDE:
        continue
    d = pd.read_csv(f)
    gl[code] = d.set_index(d.start_dates.astype(int))["combined_gt"]
glac_cum = pd.DataFrame(gl).sum(axis=1).cumsum()
print(f"[GLAC]  subtracting {len(gl)} {GLAMBIE_NAME} regions (all but "
      f"{sorted(GLACIER_EXCLUDE)}); {SPLICE_FROM}-{GLAMBIE_LAST} loss "
      f"{pd.DataFrame(gl).loc[SPLICE_FROM:GLAMBIE_LAST].sum().sum():.0f} Gt")

lws = pd.Series(-(ann.loc[yrs].values - glac_cum.reindex(yrs).values) / GT_PER_CM_SLE,
                index=yrs)

# ---- splice onto the Frederikse frame ------------------------------------------
tg = pd.read_csv(TARGETS).set_index("year")
ov = [y for y in yrs if OVERLAP[0] <= y <= OVERLAP[1]]
off = tg["lws"].loc[ov].mean() - lws.loc[ov].mean()
lws = lws + off
res = lws.loc[ov] - tg["lws"].loc[ov]
print(f"[OVERLAP] {ov[0]}-{ov[-1]} (n={len(ov)}), offset {off:+.3f} cm, rms "
      f"{np.sqrt((res ** 2).mean()):.3f}, max|res| {abs(res).max():.3f} cm")
print(f"  ⚠ NOT AN INDEPENDENT VALIDATION -- {FRED_NAME}'s natural-TWS term comes from a")
print(f"    GRACE-calibrated reconstruction, so the two share a source over this window.")
print(f"    Read it as 'the splice introduces no discontinuity', nothing more.")

# ---- hold 2024 flat (Marcus 2026-08-24) ----------------------------------------
out = pd.Series(index=range(2003, EXT_LAST + 1), dtype=float)
out.loc[lws.index] = lws.values
for y in range(GLAMBIE_LAST + 1, HOLD_LAST + 1):
    out.loc[y] = out.loc[GLAMBIE_LAST]
print(f"[HOLD]  {GLAMBIE_LAST + 1}-{HOLD_LAST} held flat at the {GLAMBIE_LAST} value "
      f"({out.loc[GLAMBIE_LAST]:.3f} cm) -- {GLAMBIE_NAME} ends {GLAMBIE_LAST}. "
      f"1 fiat year, against 6 in the shipped target.")

print("\n" + "=" * 78 + "\n[RESULT] GRACE vs the shipped hold-flat fiat\n" + "=" * 78)
print(f"  {'year':>5} {'GRACE':>8} {'fiat':>8} {'diff':>8}")
d = []
for y in range(SPLICE_FROM, HOLD_LAST + 1):
    if y in out.index and np.isfinite(out[y]):
        print(f"  {y:5d} {out[y]:8.3f} {tg['lws'][y]:8.3f} {out[y] - tg['lws'][y]:8.3f}")
        d.append(out[y] - tg["lws"][y])
d = np.array(d)
print(f"\n  mean {d.mean():+.3f} cm | sd {d.std():.3f} | max|.| {abs(d).max():.3f}")
print("  ⇒ the hold-flat got the LEVEL right. What it removed is the INTERANNUAL variance,")
print("    which is what a last-window quadratic coefficient is most sensitive to.")

pd.DataFrame({"year": out.index, "lws_grace_cm": out.values,
              "is_held_flat": [(y > GLAMBIE_LAST) for y in out.index]}).to_csv(OUT_CSV, index=False)

fig, ax = plt.subplots(figsize=(9, 4.2))
ax.plot(tg.index, tg["lws"], color="0.55", lw=2.4, label=f"shipped target ({FRED_NAME} + fiat hold)")
ax.plot(out.index[out.index <= GLAMBIE_LAST], out[out.index <= GLAMBIE_LAST], color="C0", lw=1.6,
        label=f"{MASCON_NAME} - {GLAMBIE_NAME}")
ax.plot(out.index[out.index >= GLAMBIE_LAST], out[out.index >= GLAMBIE_LAST], color="C0", lw=1.6, ls=":",
        label=f"held flat {GLAMBIE_LAST + 1}-{HOLD_LAST}")
ax.axvline(2018.5, color="k", lw=0.8, ls="--")
ax.set_xlim(2000, EXT_LAST); ax.set_xlabel("year"); ax.set_ylabel("LWS (cm SLE, rel 1995-2005)")
ax.set_title(f"LWS extension | {MASCON_NAME} | tag {TAG}", fontsize=10)
ax.legend(fontsize=7.5, loc="upper left"); fig.tight_layout(); fig.savefig(OUT_PNG, dpi=150)

print(f"\nwrote {os.path.relpath(OUT_CSV, REPO)}")
print(f"wrote {os.path.relpath(OUT_PNG, REPO)}")
print(f"\n{os.path.basename(TARGETS)} is UNCHANGED -- recalibration deferred (Marcus 2026-08-24).")
