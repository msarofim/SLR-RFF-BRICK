#!/usr/bin/env python3
"""M3 pre-check: quantify the tension between the REAL Dangendorf 2024 GMSL
reconstruction and the Frederikse 2020 ensemble (total + component sum).

Context: dangendorf_2024_gmsl.csv in this repo is actually Frederikse 2020
(download_obs.py pulled global_basin_timeseries.xlsx from within Dangendorf's
Zenodo record 10621070). This script uses the actual Dangendorf reconstruction
(KalmanSmootherHR_Global.nc) and the full 5000-member Frederikse GMSL/component
ensemble (GMSL_ensembles_F20.nc, redistributed in the same record) to answer:
if we swap the calibration's "total" likelihood term from Frederikse to
Dangendorf, how much does the historical target actually move, relative to
the Frederikse ensemble spread?

Outputs: outputs/diag_dangendorf_vs_frederikse.png + _summary.md
"""

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

# ----------------------------------------------------------------------------
# Named constants (labels below derive from these)
# ----------------------------------------------------------------------------
REPO = Path(__file__).resolve().parents[1]
# NOTE the Global nc in Dangendorf's Zenodo record is MIS-WRITTEN upstream: its "GMSLHR"
# slot holds the BARYSTATIC global mean (verified: cos-weighted mean of the Fields nc
# "Bary" field reproduces it to 0.000 mm), and the GMSSLHR/GBSLHR slots are fill values.
# The true GMSL must be computed from the Fields nc: cos-lat-weighted mean of "HR",
# exactly as the record's own Master_Final.m (line 26) does. Validated against the paper:
# 1900-2021 trend 1.52 vs published 1.5±0.19; 1993-2021 3.17 vs 3.4±0.42 mm/yr.
DANG_FIELDS_NC = REPO / "data/observations/raw/dangendorf2024_KalmanSmootherHR_Fields.nc"
DANG_GLOBAL_NC = REPO / "data/observations/raw/dangendorf2024_KalmanSmootherHR_Global.nc"
DANG_GRID_CSV = REPO / "data/observations/raw/dangendorf2024_grid_lonlat.csv"
DANG_OUT_CSV = REPO / "data/observations/dangendorf2024_gmsl_annual.csv"
FRED_ENS_NC = REPO / "data/observations/raw/frederikse2020_GMSL_ensembles.nc"
ALTIMETRY_CSV = REPO / "data/observations/nasa_gmsl_annual.csv"

REF_WINDOW = (1995, 2005)  # matches prep_recalib_targets_ext.py re-referencing
TREND_WINDOWS = [(1900, 2018), (1930, 1970), (1971, 2018), (1993, 2018)]
BAND_PCTL = (5.0, 95.0)  # ensemble band percentiles
COMPONENTS = ["Glaciers", "GrIS", "AIS", "TWS", "Steric"]  # BRICK-relevant sum

OUT_PNG = REPO / "outputs/diag_dangendorf_vs_frederikse.png"
OUT_MD = REPO / "outputs/diag_dangendorf_vs_frederikse_summary.md"

REF_LABEL = f"{REF_WINDOW[0]}–{REF_WINDOW[1]}"


# ----------------------------------------------------------------------------
def wquantile(x, w, q):
    """Weighted quantile(s) of x (1-D) with weights w; q in percent."""
    idx = np.argsort(x)
    xs, ws = x[idx], w[idx]
    cw = np.cumsum(ws) - 0.5 * ws
    cw /= np.sum(ws)
    return np.interp(np.asarray(q, dtype=float) / 100.0, cw, xs)


def wmean_sd(x, w):
    m = np.average(x, weights=w)
    sd = np.sqrt(np.average((x - m) ** 2, weights=w))
    return m, sd


def ols_trend(years, vals):
    """OLS slope in mm/yr over the given points (NaNs dropped)."""
    ok = np.isfinite(vals)
    return np.polyfit(years[ok], vals[ok], 1)[0]


def reref(vals, years, window):
    """Subtract the mean over the reference window (single common offset)."""
    sel = (years >= window[0]) & (years <= window[1])
    return vals - np.nanmean(vals[sel])


# ----------------------------------------------------------------------------
# Load Dangendorf 2024: true GMSL = cos-lat-weighted mean of the HR field
# (m -> mm), annual 1900-2021. SE caveat: the Global nc's "GMSLHRSE" cannot be
# unambiguously attributed (same slot-shift bug); used as indicative only.
# ----------------------------------------------------------------------------
grid = pd.read_csv(DANG_GRID_CSV)
wlat = np.cos(np.deg2rad(grid["lat"].values))
fields = xr.open_dataset(DANG_FIELDS_NC, decode_times=False)
d_years = np.arange(1900, 2022)
d_gmsl = (np.asarray(fields["HR"]) @ wlat) / wlat.sum() * 1000.0
d_se = np.asarray(xr.open_dataset(DANG_GLOBAL_NC)["GMSLHRSE"])[0] * 1000.0
pd.DataFrame({"year": d_years, "gmsl_mm": d_gmsl, "se_mm_indicative": d_se}).to_csv(
    DANG_OUT_CSV, index=False)
d_gmsl = reref(d_gmsl, d_years, REF_WINDOW)

# ----------------------------------------------------------------------------
# Load Frederikse 2020 ensemble (mm), 5000 weighted members, 1900-2018
# ----------------------------------------------------------------------------
f = xr.open_dataset(FRED_ENS_NC)
f_years = f["time"].values.astype(int)
f_w = f["likelihood"].values.astype(float)
f_gmsl_ens = f["GMSL"].values  # (member, year), observed tide-gauge GMSL
f_comp_ens = sum(f[c].values for c in COMPONENTS)  # budget (component sum)

# re-reference every member with its own single offset (band width preserved)
f_gmsl_ens = f_gmsl_ens - f_gmsl_ens[
    :, (f_years >= REF_WINDOW[0]) & (f_years <= REF_WINDOW[1])
].mean(axis=1, keepdims=True)
f_comp_ens = f_comp_ens - f_comp_ens[
    :, (f_years >= REF_WINDOW[0]) & (f_years <= REF_WINDOW[1])
].mean(axis=1, keepdims=True)

f_gmsl_med = np.array([wquantile(f_gmsl_ens[:, i], f_w, 50.0) for i in range(len(f_years))])
f_gmsl_lo = np.array([wquantile(f_gmsl_ens[:, i], f_w, BAND_PCTL[0]) for i in range(len(f_years))])
f_gmsl_hi = np.array([wquantile(f_gmsl_ens[:, i], f_w, BAND_PCTL[1]) for i in range(len(f_years))])
f_comp_med = np.array([wquantile(f_comp_ens[:, i], f_w, 50.0) for i in range(len(f_years))])

# ----------------------------------------------------------------------------
# Altimetry (annual, mm), re-referenced to the same window
# ----------------------------------------------------------------------------
alt = pd.read_csv(ALTIMETRY_CSV)
a_years = alt["year"].values.astype(int)
a_gmsl = reref(alt["value"].values.astype(float), a_years, REF_WINDOW)

# ----------------------------------------------------------------------------
# Trend table: Dangendorf central vs Frederikse ensemble trend distribution
# ----------------------------------------------------------------------------
rows = []
for w0, w1 in TREND_WINDOWS:
    dsel = (d_years >= w0) & (d_years <= w1)
    d_tr = ols_trend(d_years[dsel], d_gmsl[dsel])

    fsel = (f_years >= w0) & (f_years <= w1)
    f_tr_ens = np.array([ols_trend(f_years[fsel], m[fsel]) for m in f_gmsl_ens])
    f_med, (f_lo, f_hi) = wquantile(f_tr_ens, f_w, 50.0), wquantile(f_tr_ens, f_w, list(BAND_PCTL))
    # percentile of the Dangendorf trend within the Frederikse trend distribution
    pctl = 100.0 * np.sum(f_w[f_tr_ens < d_tr]) / np.sum(f_w)
    _, f_sd = wmean_sd(f_tr_ens, f_w)
    z = (d_tr - wmean_sd(f_tr_ens, f_w)[0]) / f_sd

    a_tr = np.nan
    if w0 >= a_years.min():
        asel = (a_years >= w0) & (a_years <= w1)
        a_tr = ols_trend(a_years[asel], a_gmsl[asel])

    rows.append(dict(window=f"{w0}–{w1}", dang=d_tr, fred_med=f_med,
                     fred_lo=f_lo, fred_hi=f_hi, pctl=pctl, z=z, altim=a_tr))

trends = pd.DataFrame(rows)

# ----------------------------------------------------------------------------
# Year-by-year tension: (D - F_median) / F ensemble sd, on common years
# ----------------------------------------------------------------------------
common = np.intersect1d(d_years, f_years)
di = np.searchsorted(d_years, common)
fi = np.searchsorted(f_years, common)
f_sd_t = np.array([wmean_sd(f_gmsl_ens[:, i], f_w)[1] for i in fi])
diff = d_gmsl[di] - f_gmsl_med[fi]
zt = diff / f_sd_t
outside = (d_gmsl[di] < f_gmsl_lo[fi]) | (d_gmsl[di] > f_gmsl_hi[fi])

# ----------------------------------------------------------------------------
# Figure
# ----------------------------------------------------------------------------
fig, axes = plt.subplots(2, 1, figsize=(9, 8), sharex=True,
                         gridspec_kw={"height_ratios": [2, 1]})
ax = axes[0]
ax.fill_between(f_years, f_gmsl_lo, f_gmsl_hi, color="tab:blue", alpha=0.20,
                label=f"Frederikse 2020 ensemble {BAND_PCTL[0]:.0f}–{BAND_PCTL[1]:.0f}%")
ax.plot(f_years, f_gmsl_med, color="tab:blue", lw=1.5,
        label="Frederikse 2020 observed GMSL (weighted median)")
ax.plot(f_years, f_comp_med, color="tab:cyan", lw=1.0, ls="--",
        label="Frederikse component sum (" + "+".join(COMPONENTS) + ")")
ax.fill_between(d_years, d_gmsl - 1.645 * d_se, d_gmsl + 1.645 * d_se,
                color="tab:red", alpha=0.20)
ax.plot(d_years, d_gmsl, color="tab:red", lw=1.5,
        label="Dangendorf 2024 (Kalman smoother ± 1.645 SE)")
ax.plot(a_years, a_gmsl, color="k", lw=1.0, marker=".", ms=3,
        label="Satellite altimetry (annual)")
ax.axvspan(1930, 1970, color="grey", alpha=0.10)
ax.set_ylabel(f"GMSL (mm, rel. {REF_LABEL})")
ax.legend(fontsize=8, loc="upper left")
ax.set_title(f"Dangendorf 2024 vs Frederikse 2020 GMSL (ref {REF_LABEL})")

ax = axes[1]
ax.fill_between(common, f_gmsl_lo[fi] - f_gmsl_med[fi], f_gmsl_hi[fi] - f_gmsl_med[fi],
                color="tab:blue", alpha=0.20,
                label=f"Frederikse {BAND_PCTL[0]:.0f}–{BAND_PCTL[1]:.0f}% half-width")
ax.plot(common, diff, color="tab:red", lw=1.5, label="Dangendorf − Frederikse median")
ax.axhline(0, color="k", lw=0.5)
ax.axvspan(1930, 1970, color="grey", alpha=0.10)
ax.set_ylabel("difference (mm)")
ax.set_xlabel("year")
ax.legend(fontsize=8, loc="upper left")
fig.tight_layout()
OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT_PNG, dpi=150)

# ----------------------------------------------------------------------------
# Summary markdown
# ----------------------------------------------------------------------------
with open(OUT_MD, "w") as fh:
    fh.write("# Dangendorf 2024 vs Frederikse 2020 GMSL — M3 pre-check\n\n")
    fh.write(f"All series re-referenced to {REF_LABEL} "
             "(single offset per series/member; band widths preserved).\n\n")
    fh.write("## Trends (mm/yr)\n\n")
    fh.write(f"| window | Dangendorf | Frederikse median [{BAND_PCTL[0]:.0f}–{BAND_PCTL[1]:.0f}%] "
             "| D percentile in F ens | z | altimetry |\n|---|---|---|---|---|---|\n")
    for r in trends.itertuples():
        alt_s = f"{r.altim:.2f}" if np.isfinite(r.altim) else "—"
        fh.write(f"| {r.window} | {r.dang:.2f} | {r.fred_med:.2f} "
                 f"[{r.fred_lo:.2f}, {r.fred_hi:.2f}] | {r.pctl:.1f}% | {r.z:+.2f} | {alt_s} |\n")
    fh.write("\n## Year-by-year (common years "
             f"{common.min()}–{common.max()})\n\n")
    fh.write(f"- max |D − F_median|: {np.max(np.abs(diff)):.1f} mm "
             f"(year {common[np.argmax(np.abs(diff))]})\n")
    fh.write(f"- max |z| vs F ensemble sd: {np.max(np.abs(zt)):.2f} "
             f"(year {common[np.argmax(np.abs(zt))]})\n")
    fh.write(f"- years D outside F {BAND_PCTL[0]:.0f}–{BAND_PCTL[1]:.0f}% band: "
             f"{outside.sum()} of {len(common)}\n")
    fh.write(f"- coverage: Dangendorf {d_years.min()}–{d_years.max()}, "
             f"Frederikse {f_years.min()}–{f_years.max()}, "
             f"altimetry {a_years.min()}–{a_years.max()}\n")

print(trends.to_string(index=False,
      float_format=lambda v: f"{v:.3f}" if np.isfinite(v) else "-"))
print(f"\nmax |D-F| = {np.max(np.abs(diff)):.1f} mm @ {common[np.argmax(np.abs(diff))]}; "
      f"max |z| = {np.max(np.abs(zt)):.2f} @ {common[np.argmax(np.abs(zt))]}; "
      f"outside {BAND_PCTL[0]:.0f}-{BAND_PCTL[1]:.0f}% band: {outside.sum()}/{len(common)} yr")
print(f"wrote {OUT_PNG}\nwrote {OUT_MD}")
