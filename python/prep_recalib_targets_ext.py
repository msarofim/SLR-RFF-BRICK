#!/usr/bin/env python3
"""
Prep EXTENDED recalibration targets: Frederikse 2020 (1900-2018) spliced with
modern reconciled products to extend each SLR component past 2018.

Motivation (Marcus, 2026-06-13): test how post-2018 observations -- especially
the post-2020 Antarctic GRACE-FO "pause" -- shift the BRICK-Mengel calibration,
and extend Greenland / thermal-expansion / glaciers at the same time.

Extension data (all reconciled multi-method products; see README in raw/):
  - AIS : GRACE-FO JPL mascon RL06.3Mv4 Antarctic mass (2002-2026), DOI 10.5067/TEMSC-3JC634
  - GIS : GRACE-FO JPL mascon RL06.3Mv4 Greenland mass (2002-2026), same DOI
  - GSIC: GlaMBIE 2025 global glacier mass (2000-2023), DOI 10.5904/wgms-glambie-2024-07
  - TE  : NOAA NCEI World-Ocean 0-2000m thermosteric sea level (2005-2025)
  - TOT : real Dangendorf 2024 GMSL reconstruction (1900-2021) spliced with NOAA STAR
          altimetry (2022-2024). [M3 rework 2026-07-20: was Frederikse-total + STAR;
          Frederikse is now COMPONENTS-only, the total is the independent Dangendorf.]
  - IMBIE 2023 (Otosaka et al., 1992-2020) AIS+GIS used only as an INDEPENDENT
    cross-check on the GRACE splices over the overlap (not fed to the fit).

Component band σ (2026-07-20): from the Frederikse 5000-member weighted ensemble
(FRED_ENS_NC), re-referenced per member -- the statistically correct band that shrinks
toward the 1995-2005 window, finishing the 2026-07-19 σ fix.

Method (each component, matching prep_recalib_targets.py conventions):
  1. Frederikse component re-referenced to the common 1995-2005 window mean (cm).
  2. Modern product converted to cm sea-level-equivalent (mass: -Gt/GT_PER_CM_SLE;
     steric/altimetry: mm/10), then OFFSET-matched (pure level shift, no rescale --
     both measure the same physical SLE) so its mean over the component's overlap
     window equals Frederikse's mean over the same window.
  3. Frederikse years 1900-2018, then the spliced modern product for 2019..end.

Decisions baked in (Marcus 2026-06-13, see handoff_2026-06-13_..._ais_extension):
  - Total extended with NOAA STAR altimetry (budget stays closed).
  - LWS held constant at its 2018 value for 2019+ (Frederikse TWS ends 2018; the
    post-2018 LWS change is <=0.1cm, within the altimetry annual sigma). FLAGGED.
  - Heterogeneous end years per component (AIS/GIS 2026, GSIC 2023, TE 2025, TOT 2024);
    the per-series AR(1) likelihood in calibrate_mcmc_ext.jl handles different lengths.

Output: outputs/recalib_targets_ext.csv (1900-2026; NaN where a component has no data)
        outputs/recalib_targets_ext_splice_diagnostic.png
"""
import os
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
RAW  = os.path.join(REPO, "data/observations/raw")
OBS  = os.path.join(REPO, "data/observations")
OUT_CSV = os.path.join(REPO, "outputs/recalib_targets_ext.csv")
OUT_PNG = os.path.join(REPO, "outputs/recalib_targets_ext_splice_diagnostic.png")

# Frederikse 5000-member weighted component ENSEMBLE (redistributed in Dangendorf's Zenodo
# record 10621070). This is the object the 2026-07-19 σ-fix flagged as missing: it lets us
# compute the statistically correct re-referenced per-year band σ = weighted sd of members
# each re-referenced to the BASE window, which SHRINKS toward the window (reconstruction
# errors are correlated in time) instead of the raw-band-width over-statement.
FRED_ENS_NC = os.path.join(RAW, "frederikse2020_GMSL_ensembles.nc")
# ensemble var -> target key
FRED_ENS_VAR = {"AIS": "ais", "Glaciers": "gsic", "GrIS": "gis",
                "Steric": "steric", "TWS": "lws", "GMSL": "dang"}

# ---- constants ----
BASE_Y0, BASE_Y1 = 1995, 2005          # common re-reference window (11 yr)
FIT_Y0           = 1900                 # fit start
EXT_Y1           = 2026                 # widest extension (AIS/GIS GRACE end)
GT_PER_CM_SLE    = 3620.0              # 362 Gt/mm * 10 (ocean-area based; <1% on increments)
ALT_SIGMA_MM     = 4.0                 # nominal altimetry annual GMSL 1-sigma (NOAA STAR sigma col empty)
# per-component overlap window for the offset-match splice
OVERLAP = {"ais": (2003, 2018), "gis": (2003, 2018), "gsic": (2003, 2018),
           "steric": (2005, 2018), "dang": (2003, 2018)}

FRED = os.path.join(RAW, "frederikse2020_global_basin_timeseries.xlsx")
FRED_MAP = {"Antarctic Ice Sheet": "ais", "Glaciers": "gsic",
            "Greenland Ice Sheet": "gis", "Steric": "steric",
            "Terrestrial Water Storage": "lws"}


def reref(s, win):
    return s - s.loc[win[0]:win[1]].mean()


def _wquantile_free(vals, w, q):
    idx = np.argsort(vals)
    xs, ws = vals[idx], w[idx]
    cw = (np.cumsum(ws) - 0.5 * ws) / ws.sum()
    return np.interp(q, cw, xs)


def load_ensemble_sigma():
    """Per-year band σ (cm) for each component from the Frederikse 5000-member ensemble.

    σ_t = weighted sd across members of (x_{m,t} − mean_{window} x_{m,·}), i.e. each member
    re-referenced to BASE_Y0..BASE_Y1 with its OWN single offset (band width preserved, but
    the spread correctly collapses toward the reference window). Returns {tgt: Series(cm)}
    indexed by ensemble years (1900-2018).
    """
    ds = xr.open_dataset(FRED_ENS_NC)
    ey = ds["time"].values.astype(int)
    w = ds["likelihood"].values.astype(float)
    win = (ey >= BASE_Y0) & (ey <= BASE_Y1)
    sig = {}
    for var, tgt in FRED_ENS_VAR.items():
        m = ds[var].values                                   # (member, year), mm
        m = m - m[:, win].mean(axis=1, keepdims=True)        # per-member single offset
        mean = np.average(m, axis=0, weights=w)
        sd = np.sqrt(np.average((m - mean) ** 2, axis=0, weights=w))
        sig[tgt] = pd.Series(sd / 10.0, index=ey)            # mm -> cm
    return sig


def annual_mean(t, v, ylo, yhi):
    """Calendar-year mean of an (irregular) monthly series t (decimal yr) -> v."""
    yr = np.floor(t).astype(int)
    out = {}
    for y in range(ylo, yhi + 1):
        m = yr == y
        if m.sum() >= 6:                # require >=6 months for a usable annual mean
            out[y] = float(np.mean(v[m]))
    return pd.Series(out)


def splice_offset(modern_cm, fred_cm, win):
    """Level shift so modern mean == Frederikse mean over the overlap window."""
    yrs = [y for y in range(win[0], win[1] + 1) if y in modern_cm.index and y in fred_cm.index]
    return float(fred_cm.loc[yrs].mean() - modern_cm.loc[yrs].mean()), yrs


# ============================================================ Frederikse (rel window)
g = pd.read_excel(FRED, "Global").rename(columns={"Unnamed: 0": "year"}).set_index("year")
years = np.arange(FIT_Y0, EXT_Y1 + 1)
out = pd.DataFrame({"year": years}).set_index("year")
ens_sig = load_ensemble_sigma()            # per-year band σ (cm), 1900-2018, per component
fred = {}
for fname, tgt in FRED_MAP.items():
    # VALUE = Frederikse component mean (re-referenced with the mean's single offset).
    off = (g[f"{fname} [mean]"] / 10.0).loc[BASE_Y0:BASE_Y1].mean()    # mm->cm, one offset
    mean_s = (g[f"{fname} [mean]"] / 10.0 - off).reindex(years)
    out[tgt] = mean_s.values
    fred[tgt] = (g[f"{fname} [mean]"] / 10.0) - off
    # BAND σ (2026-07-20): use the ENSEMBLE per-year sd, not the mean/lower/upper band width.
    # This finishes the 2026-07-19 σ fix. The old raw-band approach: (i) needed the mean's
    # single offset to avoid inverting lo>hi (the shrink-by-constant bug), and even fixed it
    # OVER-stated σ near the reference window because the raw band doesn't collapse there.
    # sd over the re-referenced ensemble members DOES collapse toward 1995-2005 (correlated
    # reconstruction errors) -- the statistically correct quantity. _lo/_hi are written as
    # value ∓ 1.645·σ so calibrate_mcmc_ext.jl's ϵband=(hi-lo)/(2·1.645) recovers σ exactly.
    sig = ens_sig[tgt].reindex(years)
    out[tgt + "_lo"] = (mean_s - 1.645 * sig).values
    out[tgt + "_hi"] = (mean_s + 1.645 * sig).values

# "Total" term (rel window). M3 REWORK 2026-07-20 (Marcus): the total is now the REAL
# Dangendorf 2024 reconstruction (1900-2021), NOT Frederikse (which the old file secretly
# was). Dangendorf is an independent-of-Frederikse 20th-c. tide-gauge reconstruction; the
# tension diagnostic (diag_dangendorf_vs_frederikse.py) shows it sits inside Frederikse's
# 5-95% at every trend window (mid-century 6.8th pctl) and agrees with altimetry better in
# the satellite era -- so keeping Frederikse COMPONENTS + a Dangendorf TOTAL introduces <1σ
# of trend inconsistency. σ: Dangendorf's own per-year SE is corrupted upstream (its Zenodo
# Global.nc GMSL slot holds the barystatic mean; the SE column has the same slot-shift), so
# we adopt the Frederikse ensemble GMSL sd as the total-term σ -- a genuine per-year LEVEL sd,
# CONSERVATIVE (larger than a fully-correlated combination of Dangendorf's own basin SEs), and
# reproducible. This only sets the term's WEIGHT; the independent information is in the VALUE.
d = pd.read_csv(os.path.join(OBS, "dangendorf2024_gmsl_annual.csv")).set_index("year")
dang_val = reref(d["gmsl_mm"] / 10.0, (BASE_Y0, BASE_Y1))                 # cm, 1900-2021
out["dang"]  = dang_val.reindex(years).values
fred["dang"] = dang_val
dang_sig = ens_sig["dang"].reindex(years)                                # GMSL ensemble sd (1900-2018)
# ensemble ends 2018; hold its 2018 value for the Dangendorf-only years 2019-2021 (small
# extrapolation, flagged). STAR years (2022+) get ALT_SIGMA_MM below.
dang_sig.loc[2019:] = ens_sig["dang"].loc[2018]
out["dang_sig"] = dang_sig.values
out["dang_lo"]  = (dang_val.reindex(years) - 1.645 * dang_sig).values
out["dang_hi"]  = (dang_val.reindex(years) + 1.645 * dang_sig).values

# ============================================================ modern products -> cm SLE
modern = {}      # tgt -> (Series cm, Series sigma_cm)

# --- AIS / GIS : GRACE-FO mascon (Gt anomaly) ---
for tgt, fn in [("ais", "grace_antarctica_mass.txt"), ("gis", "grace_greenland_mass.txt")]:
    raw = pd.read_csv(os.path.join(RAW, fn), sep=r"\s+", comment="H", header=None,
                      names=["t", "m", "s"]).dropna()
    sle = annual_mean(raw.t.values, -raw.m.values / GT_PER_CM_SLE, 2002, EXT_Y1)
    sig = annual_mean(raw.t.values,  raw.s.values / GT_PER_CM_SLE, 2002, EXT_Y1)
    modern[tgt] = (sle, sig)

# --- GSIC : GlaMBIE global glacier (annual Gt change -> cumulative) ---
gl = pd.read_csv(os.path.join(RAW, "glambie_global_glacier_mass.csv"))
gl["yr"] = np.floor(gl.start_dates).astype(int)
gl_cum = (-gl.combined_gt.cumsum() / GT_PER_CM_SLE)              # cm SLE, cumulative
gl_sig = (np.sqrt((gl.combined_gt_errors ** 2).cumsum()) / GT_PER_CM_SLE)  # quad-sum cumulative err
modern["gsic"] = (pd.Series(gl_cum.values, index=gl.yr.values),
                  pd.Series(gl_sig.values, index=gl.yr.values))

# --- TE : NOAA NCEI World-Ocean 0-2000m thermosteric SL (mm) ---
st = pd.read_csv(os.path.join(RAW, "noaa_thermosteric_w0-2000m_yearly.dat"),
                 sep=r"\s+", skiprows=1, header=None,
                 names=["t", "WO", "WOse", "NH", "NHse", "SH", "SHse"])
st["yr"] = np.floor(st.t).astype(int)
modern["steric"] = (pd.Series((st.WO / 10.0).values, index=st.yr.values),
                    pd.Series((st.WOse / 10.0).values, index=st.yr.values))

# --- TOTAL : NOAA STAR altimetry GMSL (mm) ---
alt = pd.read_csv(os.path.join(OBS, "nasa_gmsl_annual.csv")).set_index("year")
modern["dang"] = (alt["value"] / 10.0, pd.Series(ALT_SIGMA_MM / 10.0, index=alt.index))

# ============================================================ splice modern products into out
# Splice starts the year AFTER each historical series ends: components extend Frederikse
# (ends 2018) from 2019; the TOTAL extends the real Dangendorf reconstruction (ends 2021)
# with NOAA STAR altimetry from 2022 -- so STAR fills only the years Dangendorf lacks.
SPLICE_FROM = {"ais": 2019, "gis": 2019, "gsic": 2019, "steric": 2019, "dang": 2022}
print(f"{'comp':6s} {'overlap':12s} {'offset_cm':>9s} {'from':>5s} {'end_yr':>6s}  increment to end (cm)")
splices = {}
for tgt in ["ais", "gis", "gsic", "steric", "dang"]:
    mod_cm, mod_sig = modern[tgt]
    off, yrs = splice_offset(mod_cm, fred[tgt], OVERLAP[tgt])
    spl = mod_cm + off
    end = int(spl.index.max())
    splices[tgt] = (spl, mod_sig)
    y0 = SPLICE_FROM[tgt]
    for y in range(y0, end + 1):
        if y in spl.index:
            out.loc[y, tgt] = spl[y]
            s = mod_sig.get(y, np.nan)
            s = 0.05 if not np.isfinite(s) else max(s, 0.01)
            out.loc[y, tgt + "_lo"] = spl[y] - 1.645 * s
            out.loc[y, tgt + "_hi"] = spl[y] + 1.645 * s
    if tgt == "dang":
        for y in range(y0, end + 1):
            if y in spl.index:
                out.loc[y, "dang_sig"] = ALT_SIGMA_MM / 10.0
    inc = spl[end] - fred[tgt].get(y0 - 1, np.nan)
    print(f"{tgt:6s} {str(OVERLAP[tgt]):12s} {off:9.3f} {y0:5d} {end:6d}  {inc:+.3f}")

# LWS: hold constant at 2018 value for 2019+ (FLAGGED choice)
for suf in ["", "_lo", "_hi"]:
    v18 = out.loc[2018, "lws" + suf]
    out.loc[2019:EXT_Y1, "lws" + suf] = v18

out.reset_index().to_csv(OUT_CSV, index=False)
print(f"\nWrote {OUT_CSV}  ({len(out)} yrs {FIT_Y0}-{EXT_Y1})")

# ---- provenance sidecar: keep Frederikse and the (offset-matched) modern product
# as SEPARATE columns over their FULL ranges, so the hindcast figure can show which
# obs is Frederikse vs GRACE-FO/GlaMBIE/NOAA (incl. the overlap, where the modern
# product sits on top of Frederikse -- demonstrating the splice is consistent, not blended).
OUT_SRC = os.path.join(REPO, "outputs/recalib_targets_ext_sources.csv")
src = pd.DataFrame({"year": years}).set_index("year")
for tgt in ["ais", "gis", "gsic", "steric", "dang"]:
    src[tgt + "_fred"]   = fred[tgt].reindex(years).values                  # Frederikse (components) / Dangendorf (total)
    src[tgt + "_modern"] = splices[tgt][0].reindex(years).values            # offset-matched modern, full range
src.reset_index().to_csv(OUT_SRC, index=False)
print(f"Wrote {OUT_SRC}  (Frederikse vs modern-extension columns, separated)")

# ============================================================ IMBIE cross-check + plot
imbie = {}
for tgt, fn in [("ais", "imbie_antarctica_2021_mm.csv"), ("gis", "imbie_greenland_2021_mm.csv")]:
    im = pd.read_csv(os.path.join(RAW, fn))
    im["yr"] = np.floor(im["Year"]).astype(int)
    cum = im.groupby("yr")["Cumulative mass balance (mm)"].mean() / 10.0    # mm->cm SLE
    off, _ = splice_offset(cum, fred[tgt], OVERLAP[tgt])
    imbie[tgt] = cum + off

print("\nIMBIE cross-check (cm SLE, spliced to same overlap) vs GRACE splice:")
for tgt in ["ais", "gis"]:
    for y in [2015, 2018, 2020]:
        gr = splices[tgt][0].get(y, np.nan); im = imbie[tgt].get(y, np.nan)
        print(f"  {tgt} {y}:  GRACE {gr:+.3f}   IMBIE {im:+.3f}   diff {gr-im:+.3f}")

fig, ax = plt.subplots(2, 3, figsize=(15, 8))
titles = {"ais": "AIS (GRACE-FO)", "gis": "GIS (GRACE-FO)", "gsic": "GSIC (GlaMBIE)",
          "steric": "Steric/TE (NOAA NCEI)", "dang": "Total (Dangendorf 2024 + STAR)"}
hist_label = {"ais": "Frederikse", "gis": "Frederikse", "gsic": "Frederikse",
              "steric": "Frederikse", "dang": "Dangendorf 2024"}
for a, tgt in zip(ax.ravel(), ["ais", "gis", "gsic", "steric", "dang"]):
    a.plot(fred[tgt].index, fred[tgt].values, color="k", lw=1.5, label=hist_label[tgt])
    spl = splices[tgt][0]
    a.plot(spl.index, spl.values, color="C3", lw=1, alpha=0.7, label="modern (spliced)")
    post = out.loc[2019:, tgt].dropna()
    a.plot(post.index, post.values, "o", color="C3", ms=3, label="extension used")
    if tgt in imbie:
        a.plot(imbie[tgt].index, imbie[tgt].values, color="C0", lw=1, ls="--", label="IMBIE 2023 (xcheck)")
    a.axvspan(OVERLAP[tgt][0], OVERLAP[tgt][1], color="grey", alpha=0.12)
    a.set_xlim(1980, EXT_Y1); a.set_title(titles[tgt]); a.set_ylabel("cm rel 1995-2005")
    a.legend(fontsize=7); a.grid(alpha=0.3)
ax.ravel()[-1].axis("off")
fig.suptitle("Extended recalibration targets: Frederikse spliced with modern reconciled products "
             f"({BASE_Y0}-{BASE_Y1} baseline; grey = splice overlap)", fontsize=11)
fig.tight_layout()
fig.savefig(OUT_PNG, dpi=130)
print(f"Wrote {OUT_PNG}")
