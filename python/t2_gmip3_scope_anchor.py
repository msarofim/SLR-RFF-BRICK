#!/usr/bin/env python3
"""T2 — GlacierMIP3 ladder-anchor scope correction (decision menu T2,
handoff_2026-08-07_extB3_falsified_modern_flow_tension.md §5).

The calibrator's GlacierMIP3 ladder gate uses the paper's FULL-RGI global
committed-loss numbers (central 39/47/63/77 % of 2020 mass at +1.2/1.5/2/3 K
global, likely [15-55]/[20-64]/[43-76]/[60-85]), but the model's glacier stock
is the excl-r5-incl-r19 scope (V = 0.290 m SLE; Greenland-periphery r5 lives in
the GIS target). This script recomputes the anchor + likely ranges for OUR
scope by REPLICATING THE PAPER'S OWN 'All' PIPELINE on a reduced region set:

  per-region steady state (mean of simulation years 4900-5000, = the script's
  101-yr centered rolling mean at its last full window) -> MEDIAN across the 8
  glacier models -> SUM of absolute volumes over the scope regions -> % of the
  scope's 2020 volume (Farinotti+Hugonnet 2020 estimates) -> moepy LOWESS
  quantile fit vs global warming with the paper's frac auto-selection
  (GlacierMIP/GlacierMIP3: lowess_percentile_interval_fit_per_region_added_
  uncertainties.py; frac grid 0.10-0.99, selection = min RMSE among
  non-negative-and-decreasing median fits, final refit num_fits=2000).

  The published 'All' CENTRAL comes from that median pipeline, but the
  published 'All' BOUNDS were REPLACED downstream (0d_lowess_fit_advanced_
  aggregation_uncertainty.ipynb): uncertainties aggregated from five
  sub-aggregates (global-model groups + r06 + r11), which the authors verify
  is "only slightly larger than if we just use the global models" (their
  cell-9 note; confirmed here: the only_global_models file's 'All' bounds
  match the main file's within ~1.5 pts). So this script replicates:
    central -> median pipeline (validates within ~1 pt at every rung);
    bounds  -> per-member composite over the globally-covering models,
               quantile-LOWESS (validates against published 'All' bounds).
  FINAL anchors are DELTA-TRANSFERRED: published + (scope - full) under the
  matching replicated estimator, which cancels replication noise. A naive
  mass-weighted composite of per-region marginal quantiles over-disperses
  the bounds (the authors' own "conservative regional sum" caveat; kept as
  a labeled cross-check arm).

Data: Zekollari, Schuster et al. 2025 Science (DOI 10.1126/science.adu4675),
GlacierMIP3 Zenodo archive v2 (DOI 10.5281/zenodo.15046588, concept
10.5281/zenodo.14045268), under data/observations/raw/gmip3/:
  all_shifted_...repeat_last_101yrs_via_5yravg.nc (1.47 GB, UNTRACKED — the
    re-fetch recipe is in data/observations/raw/README_modern_extensions.md)
  3_shift_summary_region_characteristicsFeb12_2024.csv (2020 volumes)
  climate_input_data/temp_ch_ipcc_ar6_isimip3b.csv (per-experiment warming)
  lowess_fit_rel_2020_101yr_avg_steady_state_Feb12_2024.csv (published fits)
  table_S1a.csv / table_S3.csv (published tables, cross-checks)

Validation gate: the replicated pipeline on the FULL 19-region scope must
reproduce the published 'All' ladder (central + likely at every gate rung)
within VALID_TOL_PCT before the excl-r5 numbers are trusted.

Also re-solves the D0 SC point (d0_final_selfconsistent.py convention) under
each anchor and reports the demanded committed-but-unmelted gap + the implied
modern GSIC flow rate at nu=1 (the extB3 tension metric: kappa*exc*gap vs
observed GlaMBIE-scope ~0.6 mm/yr).

Outputs: outputs/t2_gmip3_scope_anchor.csv, figures/t2_gmip3_scope_anchor.png
"""
import os
import re
import subprocess

import numpy as np
import pandas as pd
import xarray as xr
from moepy import lowess as moepy_lowess
from scipy.optimize import brentq

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
GMIP3_DIR = os.path.join(REPO, "data/observations/raw/gmip3")
NC_SHIFTED = os.path.join(
    GMIP3_DIR, "GMIP3_reg_glacier_model_data",
    "all_shifted_glacierMIP3_Feb12_2024_models_all_rgi_regions_sum_scaled_"
    "extended_repeat_last_101yrs_via_5yravg.nc")
REGCHAR_CSV = os.path.join(GMIP3_DIR,
                           "3_shift_summary_region_characteristicsFeb12_2024.csv")
TEMP_CSV = os.path.join(GMIP3_DIR, "climate_input_data/temp_ch_ipcc_ar6_isimip3b.csv")
LOWESS_CSV = os.path.join(GMIP3_DIR,
                          "lowess_fit_rel_2020_101yr_avg_steady_state_Feb12_2024.csv")
TABLE_S1A = os.path.join(GMIP3_DIR, "table_S1a.csv")
TABLE_S3 = os.path.join(GMIP3_DIR, "table_S3.csv")
TGLAC = os.path.join(REPO, "data/observations/t_glac_hadcrut5.csv")
OUT_CSV = os.path.join(REPO, "outputs/t2_gmip3_scope_anchor.csv")
OUT_FIG = os.path.join(REPO, "figures/t2_gmip3_scope_anchor.png")

LEVELS = [1.2, 1.5, 2.0, 2.7, 3.0]        # global K rel 1850-1900 (AR6 defn)
GATE_LEVELS = [1.2, 1.5, 2.0, 3.0]        # the 4 ladder-gate rungs
EXCLUDE_REGION = "05"                     # Greenland periphery (in the GIS target)
GLACIER_MODELS_8 = ["PyGEM-OGGM_v13", "GloGEMflow", "GloGEMflow3D", "OGGM_v16",
                    "GLIMB", "Kraaijenbrink", "GO", "CISM2"]   # paper's 8 (README)
STEADY_YEARS = (4900, 5000)               # = script's rolling-101 last full window
QS = [0.05, 0.17, 0.25, 0.5, 0.75, 0.83, 0.95]
Q_LO, Q_MED, Q_HI = 0.83, 0.5, 0.17       # remaining-mass q -> committed lo/med/hi
FRAC_GRID = np.arange(0.10, 1.00, 0.01)   # paper's frac auto-selection grid
NUM_FITS_SEL, NUM_FITS_FINAL, ROBUST_ITERS = 500, 2000, 2
EVAL_STEP = 0.05
GT_PER_MM_SLE = 361.8
RHO_ICE_KG_M3 = 900.0                     # volume (m3) -> mass, GlacierMIP convention
VALID_TOL_PCT = 3.0                       # replication must hit 'All' within this
SEED_T2 = 2026

# published full-RGI anchors currently hard-coded in d0_glacier_shootout.py
GMIP3_CENTRAL_PUB = {1.2: 39, 1.5: 47, 2.0: 63, 3.0: 77}
GMIP3_LIKELY_PUB = {1.2: (15, 55), 1.5: (20, 64), 2.0: (43, 76), 3.0: (60, 85)}

# SC-point solve constants (d0_final_selfconsistent.py conventions)
S2000_OBS = 0.093       # target melt 1900-2000 (7.3 cm) + Leclercq S(1900) 0.020
S2020_OBS = 0.107
INV_V = 0.290
AMP_FIT_WIN = (1901, 2024)
KAPPA_D0 = 0.00607      # D0 C_nu1.0 fitted kappa (the falsified-handoff metric)
EXC_WINDOW = (2016, 2020)   # T_glac averaging window for the modern-excess metric
OBS_MODERN_RATE_MM_YR = 0.6  # GlaMBIE-scope observed GSIC rate ~2020 (handoff §3)

COMMIT = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True).stdout.strip()
np.random.seed(SEED_T2)

# ---------------------------------------------------------------- load
regions = [f"{i:02d}" for i in range(1, 20)]
scope_ours = [r for r in regions if r != EXCLUDE_REGION]

regchar = pd.read_csv(REGCHAR_CSV, index_col=0)
regchar = regchar[regchar["rgi_reg"] != "All"]
v2020 = {f"{int(r):02d}": v for r, v in
         zip(regchar["rgi_reg"], regchar["regional_volume_m3_2020_via_5yravg"])}
assert len(v2020) == 19

temp = pd.read_csv(TEMP_CSV, index_col=0)
tcol = [c for c in temp.columns if c.startswith("temp_ch")][0]
temp["key"] = temp["gcm"].astype(str) + "_" + temp["period_scenario"].astype(str)
temp_by_key = temp.set_index("key")[tcol]

low_pub = pd.read_csv(LOWESS_CSV, index_col=0, dtype={"region": str})

print(f"T2 GlacierMIP3 scope anchor (exact pipeline) | commit={COMMIT}")
print(f"  loading steady-state slice {STEADY_YEARS} of {os.path.basename(NC_SHIFTED)}")
ds = xr.open_dataset(NC_SHIFTED)
models_in_file = [str(m) for m in ds.model_author.values]
use_models = [m for m in GLACIER_MODELS_8 if m in models_in_file]
print(f"  model_author in file: {models_in_file}")
print(f"  using the paper's 8: {use_models} ({len(use_models)} present)")
vol = (ds["volume_m3"]
       .sel(model_author=use_models)
       .sel(year_after_2020=slice(*STEADY_YEARS))
       .mean("year_after_2020")
       .load())
ds.close()

# median across glacier models per (region, gcm, scenario) — the paper's 'All' input
med = vol.median("model_author", skipna=True)

# globally-covering models (data in every region for >= half their experiments)
# — the bounds estimator per the 0d notebook's only-global equivalence
_cov = vol.notnull().sum(["gcm", "period_scenario"])
_nexp_any = vol.notnull().any("rgi_reg").sum(["gcm", "period_scenario"])
GLOBAL_MODELS = [str(m) for m in vol.model_author.values
                 if bool((_cov.sel(model_author=m) >=
                          0.5 * _nexp_any.sel(model_author=m)).all())]
print(f"  globally-covering models (bounds estimator): {GLOBAL_MODELS}")


def composite_xy(scope):
    """80-experiment (x = global warming, y = remaining % of 2020) composite
    of the per-region model-MEDIAN — the paper's 'All' CENTRAL estimator."""
    num = med.sel(rgi_reg=list(scope)).sum("rgi_reg", min_count=len(scope))
    den = sum(v2020[r] for r in scope)
    rel = (100 * num / den).to_dataframe(name="rel").reset_index()
    rel["key"] = rel["gcm"].astype(str) + "_" + rel["period_scenario"].astype(str)
    rel["temp_ch"] = rel["key"].map(temp_by_key)
    rel = rel.dropna(subset=["rel", "temp_ch"])
    return rel["temp_ch"].to_numpy(), rel["rel"].to_numpy()


def member_xy(scope):
    """Per-member (model x gcm x scenario) scope composites over the
    globally-covering models — the paper-equivalent BOUNDS estimator."""
    v = vol.sel(model_author=GLOBAL_MODELS)
    num = v.sel(rgi_reg=list(scope)).sum("rgi_reg", min_count=len(scope))
    den = sum(v2020[r] for r in scope)
    rel = (100 * num / den).to_dataframe(name="rel").reset_index()
    rel["key"] = rel["gcm"].astype(str) + "_" + rel["period_scenario"].astype(str)
    rel["temp_ch"] = rel["key"].map(temp_by_key)
    rel = rel.dropna(subset=["rel", "temp_ch"])
    return rel["temp_ch"].to_numpy(), rel["rel"].to_numpy()


def fit_quantiles(x, y):
    """Paper's frac auto-selection + final quantile LOWESS (moepy)."""
    eval_x = np.arange(np.round(x.min(), 1), x.max() * 1.001, EVAL_STEP)
    x_pred = np.concatenate([eval_x, x])
    cands = []
    for frac in FRAC_GRID:
        df = moepy_lowess.quantile_model(x, y, x_pred=x_pred, frac=frac,
                                         num_fits=NUM_FITS_SEL,
                                         robust_iters=ROBUST_ITERS, qs=[0.5])
        med_fit = df[0.5].iloc[:len(eval_x)].to_numpy()
        med_clip = np.clip(med_fit, 0, None)
        decreasing = (med_clip[:-1] - med_clip[1:]).min() >= 0
        nonneg = med_fit.min() >= 0
        resid = df[0.5].iloc[len(eval_x):].to_numpy() - y
        rmse = float(np.sqrt(np.mean(resid ** 2)))
        cands.append(dict(frac=frac, decreasing=decreasing, nonneg=nonneg, rmse=rmse,
                          min_med=med_fit.min()))
    cand = pd.DataFrame(cands)
    ok = cand[cand.decreasing & cand.nonneg]
    if len(ok):
        frac = float(ok.sort_values("rmse").iloc[0].frac)
    elif len(cand[cand.decreasing]):
        frac = float(cand[cand.decreasing].sort_values("min_med",
                                                       ascending=False).iloc[0].frac)
    else:
        frac = float(cand.sort_values("rmse").iloc[0].frac)
    df = moepy_lowess.quantile_model(x, y, x_pred=eval_x, frac=frac,
                                     num_fits=NUM_FITS_FINAL,
                                     robust_iters=ROBUST_ITERS, qs=QS)
    df = df.clip(lower=0)
    return frac, eval_x, df


def ladder_from_fit(eval_x, df):
    out = {}
    for L in LEVELS:
        rem = {q: float(np.interp(L, eval_x, df[q].to_numpy())) for q in QS}
        out[L] = dict(central=100 - rem[Q_MED], lo=100 - rem[Q_LO],
                      hi=100 - rem[Q_HI])
    return out


def published_all_row(level):
    d = low_pub[low_pub.region == "All"].sort_values("temp_ch")
    rem = {q: float(np.interp(level, d.temp_ch.to_numpy(),
                              d[str(q)].to_numpy())) for q in QS}
    return dict(central=100 - rem[Q_MED], lo=100 - rem[Q_LO], hi=100 - rem[Q_HI])


# ---------------------------------------------------------------- run both scopes
x_full, y_full = composite_xy(regions)          # central estimator (median comp.)
x_ours, y_ours = composite_xy(scope_ours)
xm_full, ym_full = member_xy(regions)           # bounds estimator (per-member)
xm_ours, ym_ours = member_xy(scope_ours)
print(f"  central-estimator points: full {len(y_full)} | ours {len(y_ours)}"
      f"  || bounds-estimator points: full {len(ym_full)} | ours {len(ym_ours)}")

frac_full, ex_full, df_full = fit_quantiles(x_full, y_full)
frac_ours, ex_ours, df_ours = fit_quantiles(x_ours, y_ours)
fracm_full, exm_full, dfm_full = fit_quantiles(xm_full, ym_full)
fracm_ours, exm_ours, dfm_ours = fit_quantiles(xm_ours, ym_ours)
lad_full = ladder_from_fit(ex_full, df_full)      # trust: central
lad_ours = ladder_from_fit(ex_ours, df_ours)
ladm_full = ladder_from_fit(exm_full, dfm_full)   # trust: lo/hi
ladm_ours = ladder_from_fit(exm_ours, dfm_ours)
print(f"  selected frac: central full {frac_full:.2f} (paper 'All' 0.23) / "
      f"ours {frac_ours:.2f} | bounds full {fracm_full:.2f} / ours {fracm_ours:.2f}")

print("\n== validation vs published 'All': central via median pipeline, "
      "bounds via per-member pipeline ==")
max_err_c = max_err_b = 0.0
for L in LEVELS:
    pub = published_all_row(L)
    errc = abs(lad_full[L]["central"] - pub["central"])
    errb = max(abs(ladm_full[L]["lo"] - pub["lo"]), abs(ladm_full[L]["hi"] - pub["hi"]))
    max_err_c, max_err_b = max(max_err_c, errc), max(max_err_b, errb)
    print(f"  +{L:>3}K  central {lad_full[L]['central']:5.1f} (pub {pub['central']:5.1f}, "
          f"err {errc:3.1f}) | bounds [{ladm_full[L]['lo']:5.1f},{ladm_full[L]['hi']:5.1f}]"
          f" (pub [{pub['lo']:5.1f},{pub['hi']:5.1f}], err {errb:3.1f})")
VALID_OK = (max_err_c <= VALID_TOL_PCT) and (max_err_b <= VALID_TOL_PCT)
print(f"  -> max err: central {max_err_c:.2f} / bounds {max_err_b:.2f} pct-pts "
      f"({'PASS' if VALID_OK else 'FAIL'} at tol {VALID_TOL_PCT})")

# final anchors: delta-transfer the published numbers by the replicated scope
# delta under the matching estimator (cancels residual replication noise)
anchor_final = {}
print(f"\n== FINAL scope-corrected ladder (excl r{EXCLUDE_REGION}, incl r19; "
      "published + replicated delta) ==")
rows = []
for L in LEVELS:
    pub = published_all_row(L)
    d_c = lad_ours[L]["central"] - lad_full[L]["central"]
    d_lo = ladm_ours[L]["lo"] - ladm_full[L]["lo"]
    d_hi = ladm_ours[L]["hi"] - ladm_full[L]["hi"]
    fin = dict(central=pub["central"] + d_c, lo=pub["lo"] + d_lo,
               hi=pub["hi"] + d_hi)
    anchor_final[L] = fin
    gate = "gate" if L in GATE_LEVELS else "report"
    print(f"  +{L:>3}K  pub {pub['central']:5.1f} [{pub['lo']:5.1f},{pub['hi']:5.1f}]"
          f"  + d({d_c:+4.1f},[{d_lo:+4.1f},{d_hi:+4.1f}])"
          f"  ->  {fin['central']:5.1f} [{fin['lo']:5.1f},{fin['hi']:5.1f}]  ({gate})")
    rows.append(dict(level_K=L, scope="full_rgi", method="exact", **lad_full[L]))
    rows.append(dict(level_K=L, scope=f"excl_r{EXCLUDE_REGION}", method="exact",
                     **lad_ours[L]))
    rows.append(dict(level_K=L, scope="full_rgi", method="member_bounds",
                     **ladm_full[L]))
    rows.append(dict(level_K=L, scope=f"excl_r{EXCLUDE_REGION}",
                     method="member_bounds", **ladm_ours[L]))
    rows.append(dict(level_K=L, scope=f"excl_r{EXCLUDE_REGION}",
                     method="anchor_final", **fin))

# cross-check arm: naive mass-weighted comonotonic composite of per-region
# marginal quantiles (FAILS validation on the bounds — kept for the record)
mass_gt = {r: v2020[r] * RHO_ICE_KG_M3 / 1e12 for r in regions}


def marginal_composite(level, include):
    Mtot = sum(mass_gt[r] for r in include)
    rem = {}
    for q in QS:
        tot = 0.0
        for r in include:
            d = low_pub[low_pub.region == r].sort_values("temp_ch")
            tot += mass_gt[r] * np.interp(level, d.temp_ch.to_numpy(),
                                          d[str(q)].to_numpy())
        rem[q] = tot / Mtot
    return dict(central=100 - rem[Q_MED], lo=100 - rem[Q_LO], hi=100 - rem[Q_HI])


for L in LEVELS:
    rows.append(dict(level_K=L, scope="full_rgi", method="marginal_xcheck",
                     **marginal_composite(L, regions)))
    rows.append(dict(level_K=L, scope=f"excl_r{EXCLUDE_REGION}",
                     method="marginal_xcheck", **marginal_composite(L, scope_ours)))

# sensitivity 1.5->3.0 K in mm SLE (raw Gt->SLE, no below-sea-level correction —
# same basis as the model's Farinotti-SLE inventory; S1b global: raw 112, BSL 98)
for scope_name, inc, lad in [("full_rgi", regions, lad_full),
                             (f"excl_r{EXCLUDE_REGION}", scope_ours, lad_ours)]:
    Mtot = sum(mass_gt[r] for r in inc)
    sens_mm = (lad[3.0]["central"] - lad[1.5]["central"]) / 100 * Mtot / GT_PER_MM_SLE
    print(f"  sens 1.5->3K {scope_name}: {sens_mm:.0f} mm SLE "
          f"(raw; S1b global raw 112 / BSL-corr 98; shootout constant 85)")
    rows.append(dict(level_K=np.nan, scope=scope_name, method="exact",
                     central=np.nan, lo=np.nan, hi=np.nan, sens_mm_1p5_3=sens_mm))

# ---------------------------------------------------------------- SC point + tension
tg = pd.read_csv(TGLAC).set_index("year")
tglac_obs = tg["t_glac_C"]
gobs = tg["gmst_hadcrut5_C"]
sel = (tg.index >= AMP_FIT_WIN[0]) & (tg.index <= AMP_FIT_WIN[1])
AMP_FIT = float((tglac_obs[sel] * gobs[sel]).sum() / (gobs[sel] ** 2).sum())
SC_A = INV_V + S2000_OBS
SLOPE_GLAC = 0.133 / AMP_FIT


def solve_sc(com12):
    tgt_seq = com12 * (SC_A - S2020_OBS) + S2020_OBS

    def f(toff):
        b = -np.log(1 - tgt_seq / SC_A) / (AMP_FIT * 1.2 - toff)
        return SC_A * b * np.exp(b * toff) - SLOPE_GLAC

    toff = brentq(f, -1.9, -0.2)
    b = -np.log(1 - tgt_seq / SC_A) / (AMP_FIT * 1.2 - toff)
    return dict(a=SC_A, b=b, T_off=toff)


def tension_metrics(sc, com12):
    seq_at = lambda T: sc["a"] * (1 - np.exp(-sc["b"] * (T - sc["T_off"])))
    gap = com12 * (sc["a"] - S2020_OBS)
    T_eq_2020 = sc["T_off"] - np.log(1 - S2020_OBS / sc["a"]) / sc["b"]
    t_now = float(tglac_obs.loc[EXC_WINDOW[0]:EXC_WINDOW[1]].mean())
    exc = max(t_now - T_eq_2020, 0.0)
    rate = 1000 * KAPPA_D0 * exc * gap
    return dict(committed_1850_m=seq_at(0.0), gap_mm=1000 * gap, exc_K=exc,
                rate_mm_yr=rate, overshoot_x=rate / OBS_MODERN_RATE_MM_YR)


print(f"\n== SC-point re-solve + modern-flow tension (amp_fit={AMP_FIT:.3f}, "
      f"kappa_D0={KAPPA_D0}, exc {EXC_WINDOW}, obs {OBS_MODERN_RATE_MM_YR} mm/yr) ==")
for name, com12 in [("pub_39", GMIP3_CENTRAL_PUB[1.2] / 100.0),
                    (f"final_excl_r{EXCLUDE_REGION}",
                     anchor_final[1.2]["central"] / 100.0)]:
    sc = solve_sc(com12)
    tm = tension_metrics(sc, com12)
    print(f"  {name:22s} com12={100 * com12:5.1f}%  b={sc['b']:.3f} "
          f"T_off={sc['T_off']:.3f}  committed@1850={tm['committed_1850_m']:.3f} m  "
          f"gap={tm['gap_mm']:5.1f} mm  rate={tm['rate_mm_yr']:.2f} mm/yr "
          f"= {tm['overshoot_x']:.2f}x obs")
    rows.append(dict(level_K=1.2, scope=name, method="sc_solve",
                     central=100 * com12, sc_b=sc["b"], sc_T_off=sc["T_off"],
                     committed_1850_m=tm["committed_1850_m"], gap_mm=tm["gap_mm"],
                     exc_K=tm["exc_K"], rate_mm_yr=tm["rate_mm_yr"],
                     overshoot_x=tm["overshoot_x"]))

res = pd.DataFrame(rows)
res["validation_pass"] = VALID_OK
os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
res.to_csv(OUT_CSV, index=False, float_format="%.4f")

# ---------------------------------------------------------------- figure
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, (axL, axR) = plt.subplots(1, 2, figsize=(12.5, 4.8), constrained_layout=True)
axL.plot(ex_full, df_full[0.5], color="k", lw=2, label="full-RGI replicated median")
axL.fill_between(exm_full, dfm_full[0.17], dfm_full[0.83], color="k", alpha=0.12)
axL.plot(ex_ours, df_ours[0.5], color="tab:blue", lw=2,
         label=f"excl-r{EXCLUDE_REGION} scope median")
axL.fill_between(exm_ours, dfm_ours[0.17], dfm_ours[0.83], color="tab:blue",
                 alpha=0.18)
dall = low_pub[low_pub.region == "All"].sort_values("temp_ch")
axL.plot(dall.temp_ch, dall["0.5"], color="tab:red", lw=1.2, ls="--",
         label="published 'All' median")
axL.scatter(xm_ours, ym_ours, s=8, color="tab:blue", alpha=0.25, zorder=0)
axL.set(xlim=(0, 4.2), ylim=(0, 130),
        xlabel="global warming level (K, AR6 defn)",
        ylabel="steady-state remaining mass (% of 2020)",
        title="replicated fits (median pipeline; bands = per-member likely)")
axL.legend(fontsize=8)

width = 0.06
for L in GATE_LEVELS:
    fin = anchor_final[L]
    axR.fill_between([L - width * 1.6, L - width * 0.3],
                     [GMIP3_LIKELY_PUB[L][0]] * 2, [GMIP3_LIKELY_PUB[L][1]] * 2,
                     color="k", alpha=0.15)
    axR.plot([L - width * 1.6, L - width * 0.3], [GMIP3_CENTRAL_PUB[L]] * 2,
             color="k", lw=2)
    axR.fill_between([L + width * 0.3, L + width * 1.6], [fin["lo"]] * 2,
                     [fin["hi"]] * 2, color="tab:blue", alpha=0.25)
    axR.plot([L + width * 0.3, L + width * 1.6], [fin["central"]] * 2,
             color="tab:blue", lw=2)
axR.plot([], [], color="k", lw=2, label="published full-RGI (gate constants)")
axR.plot([], [], color="tab:blue", lw=2,
         label=f"excl-r{EXCLUDE_REGION} scope (final anchor)")
axR.set(xlabel="global warming level (K)", ylabel="committed loss, % of 2020 mass",
        title="ladder-gate anchors: published vs scope-corrected (final)")
axR.legend(fontsize=8)
fig.suptitle(f"T2 — GlacierMIP3 anchor scope correction (exact pipeline) | "
             f"Zekollari 2025 / Zenodo 15046588 | commit {COMMIT}", fontsize=10)
os.makedirs(os.path.dirname(OUT_FIG), exist_ok=True)
fig.savefig(OUT_FIG, dpi=150)
print(f"\nWrote {os.path.relpath(OUT_CSV, REPO)} and {os.path.relpath(OUT_FIG, REPO)}")
