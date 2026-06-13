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
  - TOT : NOAA STAR altimetry GMSL (1993-2024) splicing onto Dangendorf 2024
  - IMBIE 2023 (Otosaka et al., 1992-2020) AIS+GIS used only as an INDEPENDENT
    cross-check on the GRACE splices over the overlap (not fed to the fit).

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
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
RAW  = os.path.join(REPO, "data/observations/raw")
OBS  = os.path.join(REPO, "data/observations")
OUT_CSV = os.path.join(REPO, "outputs/recalib_targets_ext.csv")
OUT_PNG = os.path.join(REPO, "outputs/recalib_targets_ext_splice_diagnostic.png")

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
fred = {}
for fname, tgt in FRED_MAP.items():
    for stat, suf in [("mean", ""), ("lower", "_lo"), ("upper", "_hi")]:
        s = reref(g[f"{fname} [{stat}]"] / 10.0, (BASE_Y0, BASE_Y1))   # mm->cm, rel window
        out[tgt + suf] = s.reindex(years).values
    fred[tgt] = reref(g[f"{fname} [mean]"] / 10.0, (BASE_Y0, BASE_Y1))

# Dangendorf total (rel window)
d = pd.read_csv(os.path.join(OBS, "dangendorf_2024_gmsl.csv")).set_index("year")
out["dang"]     = reref(d["value"] / 10.0, (BASE_Y0, BASE_Y1)).reindex(years).values
out["dang_sig"] = (d["sigma"] / 10.0).reindex(years).values
fred["dang"]    = reref(d["value"] / 10.0, (BASE_Y0, BASE_Y1))

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

# ============================================================ splice 2019..end into out
print(f"{'comp':6s} {'overlap':12s} {'offset_cm':>9s} {'end_yr':>6s}  post-2018 increment (cm)")
splices = {}
for tgt in ["ais", "gis", "gsic", "steric", "dang"]:
    mod_cm, mod_sig = modern[tgt]
    off, yrs = splice_offset(mod_cm, fred[tgt], OVERLAP[tgt])
    spl = mod_cm + off
    end = int(spl.index.max())
    splices[tgt] = (spl, mod_sig)
    for y in range(2019, end + 1):
        if y in spl.index:
            out.loc[y, tgt] = spl[y]
            s = mod_sig.get(y, np.nan)
            s = 0.05 if not np.isfinite(s) else max(s, 0.01)
            out.loc[y, tgt + "_lo"] = spl[y] - 1.645 * s
            out.loc[y, tgt + "_hi"] = spl[y] + 1.645 * s
    if tgt == "dang":
        for y in range(2019, end + 1):
            if y in spl.index:
                out.loc[y, "dang_sig"] = ALT_SIGMA_MM / 10.0
    inc = spl[end] - fred[tgt].get(2018, np.nan)
    print(f"{tgt:6s} {str(OVERLAP[tgt]):12s} {off:9.3f} {end:6d}  {inc:+.3f}")

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
    src[tgt + "_fred"]   = fred[tgt].reindex(years).values                  # Frederikse/Dangendorf (1900-2018)
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
          "steric": "Steric/TE (NOAA NCEI)", "dang": "Total (NOAA STAR altimetry)"}
for a, tgt in zip(ax.ravel(), ["ais", "gis", "gsic", "steric", "dang"]):
    a.plot(fred[tgt].index, fred[tgt].values, color="k", lw=1.5, label="Frederikse/Dangendorf")
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
