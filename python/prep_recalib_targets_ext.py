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
  - GSIC: GlaMBIE 2025 glacier mass (2000-2023), DOI 10.5904/wgms-glambie-2024-07,
          SCOPE-MATCHED = global MINUS region 5 (r5 is in the GIS target), region 19 KEPT
          (2026-08-06 decision; see the GSIC block below + memo_2026-08-05 §2c/§3)
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

# ---- budget-closure inflation of the TOTAL target's sigma (Marcus, 2026-08-12) ----
# Gate 3.1 established that the five component targets sum +0.74 cm above the independent
# total target over 1950-1980, and that this is Frederikse 2020's OWN mid-century budget
# non-closure (our closure sits at z = +0.006 against their 5000-member ensemble median).
# RULING: carry it as uncertainty on the total, across the WHOLE span rather than a chosen
# window, using the ensemble's OWN per-year closure spread -- no decay function is fitted
# and no window edge is chosen. Members are re-referenced to BASE exactly as the targets
# are, so sigma is smallest at the anchor and grows away from it in both directions; that
# is the correct structure for a level anomaly scored in that frame, and it is why the
# inflation is 1.37x at 1900, 1.11x at 2000 and 1.90x at 2018 rather than monotone.
# CAVEAT ON RECORD: the total channel also carries a sampled AR(1) with rho ~ 0.97, so an
# anchor-shaped sigma may partly double-count level correlation. Flagged, not corrected.
CLOSURE_COMPONENT_VARS = ["AIS", "Glaciers", "GrIS", "Steric", "TWS"]
CLOSURE_TOTAL_VAR = "GMSL"
CLOSURE_SIG_COL = "dang_closure_sig"
# The ensemble ends in 2018 and the total target runs to 2024. Hold flat past the ensemble,
# the same FLAGGED convention already used for LWS.
CLOSURE_HOLD_FLAT_PAST_ENSEMBLE = True

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


def load_closure_sigma():
    """Per-year weighted sd (cm) of Frederikse's OWN budget closure,
    (sum of the five components) - (their GMSL), across the 5000 members.

    Each member is re-referenced to BASE_Y0..BASE_Y1 with its own single offset,
    identically to load_ensemble_sigma() and to the targets themselves, so this
    sigma is in the same frame as the residual the likelihood scores. Indexed by
    ensemble year (1900-2018)."""
    ds = xr.open_dataset(FRED_ENS_NC)
    ey = ds["time"].values.astype(int)
    w = ds["likelihood"].values.astype(float)
    win = (ey >= BASE_Y0) & (ey <= BASE_Y1)

    def reref_members(var):
        m = ds[var].values / 10.0                            # mm -> cm
        return m - m[:, win].mean(axis=1, keepdims=True)

    close = (sum(reref_members(v) for v in CLOSURE_COMPONENT_VARS)
             - reref_members(CLOSURE_TOTAL_VAR))             # (member, year)
    mean = np.average(close, axis=0, weights=w)
    sd = np.sqrt(np.average((close - mean) ** 2, axis=0, weights=w))
    return pd.Series(sd, index=ey)


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
# of trend inconsistency. σ (2026-08-07, Marcus): Dangendorf's OWN per-year SE from the
# CORRECTED Global_v2.nc (S. Dangendorf pers.comm. 2026-08-07; the original Zenodo Global.nc
# was slot-shifted -- GMSL slots held barystatic -- which is why the 2026-07-20 rework had
# substituted the Frederikse ensemble GMSL sd; that workaround claimed conservatism, but the
# corrected SE is 1.3-2x LARGER over 1900-2010 and smaller post-2015, so the substitution is
# RETIRED). SE units are METERS in the file ("the error ... is 3 mm in 2021 ... given in m").
# Covers 1900-2021, so no hold-flat extrapolation; STAR years (2022+) get ALT_SIGMA_MM below.
DANG_V2_NC = os.path.join(RAW, "dangendorf2024_KalmanSmootherHR_Global_v2.nc")
d = pd.read_csv(os.path.join(OBS, "dangendorf2024_gmsl_annual.csv")).set_index("year")
dang_val = reref(d["gmsl_mm"] / 10.0, (BASE_Y0, BASE_Y1))                 # cm, 1900-2021
out["dang"]  = dang_val.reindex(years).values
fred["dang"] = dang_val
with xr.open_dataset(DANG_V2_NC) as dv2:
    dang_sig = pd.Series(dv2["GMSLHRSE"].values.ravel() * 100.0,          # m -> cm
                         index=dv2["t"].values.ravel().astype(int)).reindex(years)
assert abs(dang_sig.loc[2021] - 0.268) < 0.01, "v2 SE(2021) should be ~2.68 mm (units check)"
out["dang_sig"] = dang_sig.values
out["dang_lo"]  = (dang_val.reindex(years) - 1.645 * dang_sig).values
out["dang_hi"]  = (dang_val.reindex(years) + 1.645 * dang_sig).values

# budget-closure inflation of the total's sigma (see the constant block; Marcus 2026-08-12).
# Emitted as its OWN column: dang_lo/dang_hi stay the Dangendorf band, and
# calibrate_mcmc_ext.jl adds this in quadrature alongside the LWS band term.
closure_sig = load_closure_sigma()
_ens_last = int(closure_sig.index.max())
closure_col = closure_sig.reindex(years)
if CLOSURE_HOLD_FLAT_PAST_ENSEMBLE:
    closure_col.loc[_ens_last + 1:] = closure_sig.loc[_ens_last]
out[CLOSURE_SIG_COL] = closure_col.values

# ============================================================ modern products -> cm SLE
modern = {}      # tgt -> (Series cm, Series sigma_cm)

# --- AIS / GIS : GRACE-FO mascon (Gt anomaly) ---
for tgt, fn in [("ais", "grace_antarctica_mass.txt"), ("gis", "grace_greenland_mass.txt")]:
    raw = pd.read_csv(os.path.join(RAW, fn), sep=r"\s+", comment="H", header=None,
                      names=["t", "m", "s"]).dropna()
    sle = annual_mean(raw.t.values, -raw.m.values / GT_PER_CM_SLE, 2002, EXT_Y1)
    sig = annual_mean(raw.t.values,  raw.s.values / GT_PER_CM_SLE, 2002, EXT_Y1)
    modern[tgt] = (sle, sig)

# --- GSIC : GlaMBIE glacier mass, SCOPE-MATCHED (annual Gt change -> cumulative) ---
# 2026-08-06 scope decision (Marcus; memo_2026-08-05 §3 choice 1c): the GSIC component owns
# RGI regions 1-18-minus-5 PLUS region 19. Region 5 (Greenland periphery) lives in the GIS
# target (Frederikse GrIS = Kjeldsen/Mouginot + r5; GRACE mascon Greenland includes it), so
# the GlaMBIE GLOBAL series must have r5 SUBTRACTED or the splice double-counts it against
# GIS. Region 19 is RETAINED (deliberate zero everywhere else in the chain; inventory
# convention V = 0.290 m SLE). NB the Frederikse 1900-2018 glacier segment lacks r19 flow
# (documented zero in his Methods) -- small known bias (~0.05 mm/yr modern, less earlier).
# Error: r5's sigma quadrature-ADDED to the global sigma (conservative; r5 ~35 vs global
# ~100 Gt/yr, so the change is minor).
gl = pd.read_csv(os.path.join(RAW, "glambie_global_glacier_mass.csv"))
r5 = pd.read_csv(os.path.join(RAW, "glambie_r5_greenland_periphery.csv"))
assert np.array_equal(gl.start_dates.values, r5.start_dates.values), "GlaMBIE global/r5 year mismatch"
gl["yr"] = np.floor(gl.start_dates).astype(int)
gl_net_gt = gl.combined_gt.values - r5.combined_gt.values         # global minus r5 (r19 kept)
gl_net_err = np.sqrt(gl.combined_gt_errors.values ** 2 + r5.combined_gt_errors.values ** 2)
gl_cum = pd.Series(-gl_net_gt, index=gl.yr.values).cumsum() / GT_PER_CM_SLE   # cm SLE, cumulative
gl_sig = pd.Series(np.sqrt((gl_net_err ** 2).cumsum()) / GT_PER_CM_SLE, index=gl.yr.values)
modern["gsic"] = (gl_cum, gl_sig)
print(f"GSIC splice scope: GlaMBIE global - r5 (r19 kept); 2000-2023 cumulative "
      f"{gl_cum.iloc[-1]:+.2f} cm (global would be {-gl.combined_gt.sum()/GT_PER_CM_SLE:+.2f})")

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
# ⚠ A REAL REPLACEMENT NOW EXISTS AND IS DELIBERATELY NOT WIRED IN.
#    `python/build_lws_grace_extension.py` builds LWS 2019-2023 from the JPL mascons minus
#    GlaMBIE glaciers -> `outputs/lws_grace_extension_L14.csv`. It is NOT read here because
#    swapping a fitted target is a recalibration trigger and the level does not justify one on
#    its own: GRACE differs from this hold by mean +0.018 cm (sd 0.076, max 0.123), i.e. the
#    hold got the LEVEL right and only removed interannual variance. Marcus 2026-08-24: "wait
#    to recalibrate until we have something else worth recalibrating." Wire it in THEN, and
#    replace lws_lo/lws_hi at the same time -- they are frozen here too, so the fit currently
#    carries a fiat value with a real-data error bar.
for suf in ["", "_lo", "_hi"]:
    v18 = out.loc[2018, "lws" + suf]
    out.loc[2019:EXT_Y1, "lws" + suf] = v18

# budget-closure inflation, reported against the FINAL sigma columns (post-splice, post
# LWS hold-flat) so the printed numbers are the ones calibrate_mcmc_ext.jl will build.
_eps_lws = ((out["lws_hi"] - out["lws_lo"]) / (2 * 1.645)).clip(lower=0.05)
_cur = np.sqrt(out["dang_sig"] ** 2 + _eps_lws ** 2)
_new = np.sqrt(_cur ** 2 + out[CLOSURE_SIG_COL] ** 2)
print(f"\nTotal-target sigma inflated by Frederikse's own budget-closure spread "
      f"(ensemble {closure_sig.index.min()}-{_ens_last}, held flat after):")
for y in [1900, 1950, 1980, 2000, 2018, 2024]:
    if y in out.index and np.isfinite(_cur.loc[y]) and np.isfinite(out.loc[y, "dang"]):
        print(f"  {y}  closure sd {out.loc[y, CLOSURE_SIG_COL]:5.3f} cm   "
              f"sigma {_cur.loc[y]:5.3f} -> {_new.loc[y]:5.3f} cm  "
              f"({_new.loc[y] / _cur.loc[y]:.2f}x)")

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
titles = {"ais": "AIS (GRACE-FO)", "gis": "GIS (GRACE-FO)", "gsic": "GSIC (GlaMBIE − r5)",
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
