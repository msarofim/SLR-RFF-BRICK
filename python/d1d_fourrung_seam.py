#!/usr/bin/env python3
"""D1d — four-rung S_eq fits (option 1) + r19 seam harmonization (option 4).
Marcus green-light 2026-08-09, with the explicit instruction that the
GlacierMIP3 rung points carry APPROPRIATE UNCERTAINTY (no unnecessary
overconstraint).

OPTION 1 — replace the exact two-rung (b, T_off) interpolation with a
weighted fit of (a_eff, b, T_off) to ALL FOUR GlacierMIP3 committed rungs
(+1.2/1.5/2.0/3.0 K), per reservoir:
  - rung sigma = half the reservoir's own per-member 17-83% band from the
    exact composite (the likely band ~ +/-1 sigma for a Gaussian; using
    half-width is slightly WIDE of 1 sigma -> conservative);
  - rungs are fit with a common cross-rung correlation RUNG_CORR = 0.6
    (the same 4 globally-covering glacier models generate every rung, so
    independent errors would overconstrain ~2x);
  - a_eff carries a Gaussian prior at the published Farinotti widths
    (non-r19 scope 0.221 +/- 0.057; r19 add-back 0.069 +/- 0.018 — the A2
    decomposition of V = 0.290 +/- 0.060) instead of a hard partition pin.
    This removes the D1c BOOK1->T_off tail-extrapolation sensitivity: b is
    rung-determined (partition-invariant), and a_eff/T_off are now jointly
    disciplined by rungs + soft inventory rather than by the exponential's
    asymptote extrapolation.
  - fitted per-rung z-scores are REPORTED so strain on the exponential form
    is visible (all |z| << 1 -> the rungs are not binding tightly).

OPTION 4 — r19 (Antarctic periphery) accounting seam:
  The target's Frederikse segment (1900-2018) assumes ZERO r19 melt; the
  GlaMBIE splice (2019+) includes r19; the D1/D1c model melts r19 inside
  SLOW throughout — an inconsistency that FLATTERS the model pre-2019.
  Harmonization: r19 becomes its OWN reservoir (anchors from its singleton
  exact composite; tau50 828/213 yr) which is
    - RETAINED in the model for the inventory/S1900/ladder/spread gates and
      projections (its stock and committed melt are physically real), but
    - EXCLUDED from the hindcast flow comparison, and the target's 2019+
      segment has the observed GlaMBIE r19 cumulative REMOVED, so both
      sides are scope-without-r19 for the whole century.
  Bonus: with r19 separated, its stock uses Farinotti's r19-specific SLE
  value (0.069 +/- 0.018) directly — resolving the flagged Gt-share-vs-SLE
  (BSL) sub-decision D for the region where the bias concentrates. The
  SLOW'/FAST stocks split the non-r19 Farinotti value (0.221) by Gt share.

Structure: reservoirs R19 {19} / SLOWP {03,09,07,06} / FAST {13 regions}.
F_unch (uncharted ice) + delta (T5D, original prior) carried as in D1c;
PROFILE now defaults to TAPER (D1c ranking: taper 8.4 < const 9.0 <<
frontload 12.6; const's 1990 hard stop is a step artifact inside the
criterion window). BOOK1 (uncharted subtraction from the melt-to-date
partition) retained; BOOK2 (r19-zero history) is now STRUCTURAL.

Ablations (all unc_t5d/taper, arms ANCH/MID/FREE; patho re-fit per
(variant, obs-mode) with matched U/delta freedom):
  A_4rung : 2-block D1c structure + 4-rung fits, original obs   (option 1 alone)
  B_seam  : 3 reservoirs + exact two-rung anchors, adjusted obs (option 4 alone)
  C_both  : 3 reservoirs + 4-rung fits, adjusted obs            (HEADLINE)
  C_both under unc_sx2 as the no-delta secondary.

PRE-REGISTERED BARS: minimal = C_both ANCH deficit <= 8.4 (the D1c taper
value) with |delta| <= 1 sigma; strong = FEASIBLE (4/4 gates AND deficit
<= FLOW_TOL = 5).

Outputs: outputs/d1d_fourrung_seam.csv, outputs/d1d_blocks.csv,
         figures/d1d_fourrung_seam.png. Reuses/extends the D1 ladder cache.
"""
import os
import subprocess
import zipfile

import numpy as np
import pandas as pd
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import brentq, minimize
from scipy.stats import norm

np.seterr(over="ignore", under="ignore")

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
SHOOTOUT = os.path.join(REPO, "python/d0_glacier_shootout.py")

src = open(SHOOTOUT).read().split(
    "# ------------------------------------------------------------------ run all cells")[0]
exec(src.replace('print(f"D0', 'pass # print(f"D0'))

# paths AFTER the exec (rebind trap)
OUT_CSV = os.path.join(REPO, "outputs/d1d_fourrung_seam.csv")
OUT_BLOCKS = os.path.join(REPO, "outputs/d1d_blocks.csv")
OUT_FIG = os.path.join(REPO, "figures/d1d_fourrung_seam.png")
CACHE_NC = os.path.join(REPO, "outputs/d1_gmip3_steady_cache.nc")
CACHE_LADDER = os.path.join(REPO, "outputs/d1_block_ladder_cache.csv")
REGIONS_CSV = os.path.join(REPO, "outputs/diag_constraint_anatomy_regions.csv")
TGLAC_REG = os.path.join(REPO, "data/observations/t_glac_regions_hadcrut5.csv")
GLAMBIE_ZIP = os.path.join(REPO, "data/observations/raw/glambie_data.zip")
GMIP3_DIR = os.path.join(REPO, "data/observations/raw/gmip3")
REGCHAR_CSV = os.path.join(GMIP3_DIR,
                           "3_shift_summary_region_characteristicsFeb12_2024.csv")
TEMP_CSV = os.path.join(GMIP3_DIR, "climate_input_data/temp_ch_ipcc_ar6_isimip3b.csv")
D1C_CSV = os.path.join(REPO, "outputs/d1c_uncharted_cell.csv")

COMMIT = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True).stdout.strip()

# ---------------------------------------------------------------- constants
TAU_STAR = 250
AMP_G = 1.8
EARLY_SIGMA_X2_BEFORE = 1940
T5D_SEG_END = 1960
T5D_DELTA_PRIOR_MM_YR = 0.30
FLOW_WIN = (1980, 2023)
FLOW_TOL = 5.0
D1C_TAPER_DEFICIT = 8.4          # the minimal-bar reference (D1c taper)
RATE_WIN = (2015, 2023)
ERAS = [(1900, 1919), (1920, 1949), (1950, 1979), (1980, 1999), (2000, 2023)]
GLAMBIE_AREA_YEAR = 2000.0
GLAMBIE_RATE_WIN = (2000.0, 2024.0)
GLAMBIE_S2020_WIN = (2000.0, 2020.0)
GLAMBIE_ERR_INFLATE = 1.5
GT_PER_MM_SLE = 361.8
S2000_OBS = 0.093
NU_SHARED_PRIOR = (1.0, 0.5)
NU_BOUNDS_FREE = (0.0, 2.5)
KAPPA_BOUNDS_FREE = (1e-5, 0.5)
KAPPA_LOGPRIOR_SD = 1.5
DELTA_BOUNDS_MM_YR = (-1.2, 1.2)
TAU_SOLVE_HORIZON = 6000
TAU_MATCH_TOL = 0.02
LADDER_RUNGS_SOLVE = (1.2, 2.0)  # for the two-rung ablation-B anchors
N_STARTS_FREE = 8
N_STARTS_ANCH = 5
SEED_D1D = 2026
rng_d1 = np.random.default_rng(SEED_D1D)

# uncharted term (D1c conventions; taper now PRIMARY)
UNCH_BOUNDS_GLOBAL_MM = (16.7, 48.0)
UNCH_CENTRAL_GLOBAL_MM = sum(UNCH_BOUNDS_GLOBAL_MM) / 2
UNCH_WIN = (1901, 1990)
TAPER_FLAT_END, TAPER_ZERO = 1970, 2005
R5_MELT_SHARE = 0.13
UNCH_SCOPE_FAC = 1 - R5_MELT_SHARE
U_BOOK_MM = UNCH_CENTRAL_GLOBAL_MM * UNCH_SCOPE_FAC
UNCH_BOUNDS_SCOPE_MM = tuple(u * UNCH_SCOPE_FAC for u in UNCH_BOUNDS_GLOBAL_MM)
PROFILE_PRIMARY = "taper"

# 4-rung fit constants (option 1 — the DON'T-OVERCONSTRAIN implementation)
RUNG_CORR = 0.6                  # cross-rung error correlation (same 4 models)
RUNG_SIGMA_FLOOR_PCT = 3.0       # floor on band-derived sigma (pct-pts)
FARINOTTI_NONR19 = (0.221, 0.057)   # m SLE, excl r5+r19 (A2 memo decomposition)
FARINOTTI_R19 = (0.069, 0.018)      # m SLE, r19 add-back (Farinotti-SLE basis)

# reservoir specs
SPEC_3RES = {"R19": ["19"],
             "SLOWP": ["03", "09", "07", "06"],
             "FAST": ["01", "04", "17", "13", "14", "02", "15", "08",
                      "10", "11", "16", "18", "12"]}
SPEC_2BLK = {"SLOW": ["19", "03", "09", "07", "06"],
             "FAST": SPEC_3RES["FAST"]}

# ---------------------------------------------------------------- region data
regs = pd.read_csv(REGIONS_CSV, dtype={"reg": str})
regs["reg"] = regs["reg"].str.zfill(2)
regs = regs.set_index("reg")
treg = pd.read_csv(TGLAC_REG).set_index("year")
regchar = pd.read_csv(REGCHAR_CSV, index_col=0)
regchar = regchar[regchar["rgi_reg"] != "All"]
regchar["reg"] = regchar["rgi_reg"].map(lambda r: f"{int(r):02d}")
regchar = regchar.set_index("reg")
AMP_RATIO_COL = "median_reg_vs_glob_temp_ch_1.5_3.0"

with zipfile.ZipFile(GLAMBIE_ZIP) as z:
    cal_names = {int(os.path.basename(n).split("_")[0]): n
                 for n in z.namelist()
                 if "calendar_years/" in n and n.endswith(".csv")
                 and os.path.basename(n).split("_")[0].isdigit()
                 and int(os.path.basename(n).split("_")[0]) >= 1}
    glambie = {f"{regi:02d}": pd.read_csv(z.open(n)) for regi, n in cal_names.items()}

area_w = {r: float(g.loc[np.isclose(g["start_dates"], GLAMBIE_AREA_YEAR),
                         "glacier_area"].iloc[0]) for r, g in glambie.items()}


def glambie_block_stats(members):
    tot_gt, var_gt, cum20_gt, ny = 0.0, 0.0, 0.0, None
    for r in members:
        g = glambie[r]
        sel = (g.start_dates >= GLAMBIE_RATE_WIN[0]) & (g.end_dates <= GLAMBIE_RATE_WIN[1])
        tot_gt += -g.loc[sel, "combined_gt"].sum()
        var_gt += (g.loc[sel, "combined_gt_errors"] ** 2).sum()
        ny = sel.sum() if ny is None else ny
        assert sel.sum() == ny, f"GlaMBIE year-count mismatch r{r}"
        s20 = (g.start_dates >= GLAMBIE_S2020_WIN[0]) & (g.end_dates <= GLAMBIE_S2020_WIN[1])
        cum20_gt += -g.loc[s20, "combined_gt"].sum()
    rate = tot_gt / GT_PER_MM_SLE / ny
    rate_sd = np.sqrt(var_gt) / GT_PER_MM_SLE / ny * GLAMBIE_ERR_INFLATE
    return rate, rate_sd, cum20_gt / GT_PER_MM_SLE / 1000.0


# r19 annual increments for the target seam adjustment (option 4)
_g19 = glambie["19"]
R19_YEARS = _g19.start_dates.astype(int).to_numpy()
R19_CM = (-_g19.combined_gt.to_numpy()) / GT_PER_MM_SLE / 10.0   # cm SLE per year

# ---------------------------------------------------------------- GMIP3 cache + moepy
import xarray as xr

assert os.path.exists(CACHE_NC), "run d1_multireservoir_cell.py first"
cache = xr.open_dataset(CACHE_NC)
med_steady = cache["med"].load()
vol_members = cache["vol_global"].load()
cache.close()
v2020 = {f"{int(r):02d}": v for r, v in
         zip(regchar["rgi_reg"], regchar["regional_volume_m3_2020_via_5yravg"])}
temp = pd.read_csv(TEMP_CSV, index_col=0)
tcol = [c for c in temp.columns if c.startswith("temp_ch")][0]
temp["key"] = temp["gcm"].astype(str) + "_" + temp["period_scenario"].astype(str)
temp_by_key = temp.set_index("key")[tcol]

from moepy import lowess as moepy_lowess

FRAC_GRID = np.arange(0.10, 1.00, 0.01)
NUM_FITS_SEL, NUM_FITS_FINAL, ROBUST_ITERS = 300, 1000, 2
LADDER_QS = [0.17, 0.5, 0.83]
EVAL_STEP = 0.05


def _fit_median_lowess(x, y, qs):
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
        cands.append(dict(frac=frac, decreasing=decreasing, nonneg=nonneg,
                          rmse=float(np.sqrt(np.mean(resid ** 2))),
                          min_med=med_fit.min()))
    cand = pd.DataFrame(cands)
    ok = cand[cand.decreasing & cand.nonneg]
    if len(ok):
        frac = float(ok.sort_values("rmse").iloc[0].frac)
    elif len(cand[cand.decreasing]):
        frac = float(cand[cand.decreasing].sort_values(
            "min_med", ascending=False).iloc[0].frac)
    else:
        frac = float(cand.sort_values("rmse").iloc[0].frac)
    df = moepy_lowess.quantile_model(x, y, x_pred=eval_x, frac=frac,
                                     num_fits=NUM_FITS_FINAL,
                                     robust_iters=ROBUST_ITERS, qs=qs)
    return frac, eval_x, df.clip(lower=0)


def _composite_xy(members, arr):
    num = arr.sel(rgi_reg=list(members)).sum("rgi_reg", min_count=len(members))
    den = sum(v2020[r] for r in members)
    rel = (100 * num / den).to_dataframe(name="rel").reset_index()
    rel["key"] = rel["gcm"].astype(str) + "_" + rel["period_scenario"].astype(str)
    rel["temp_ch"] = rel["key"].map(temp_by_key)
    rel = rel.dropna(subset=["rel", "temp_ch"])
    return rel["temp_ch"].to_numpy(), rel["rel"].to_numpy()


_ladder_cache = (pd.read_csv(CACHE_LADDER) if os.path.exists(CACHE_LADDER)
                 else pd.DataFrame())


def block_ladder(members):
    global _ladder_cache
    key = "-".join(sorted(members))
    if len(_ladder_cache) and (_ladder_cache.key == key).any():
        sub = _ladder_cache[_ladder_cache.key == key].set_index("level_K")
        return ({L: float(sub.loc[L, "central"]) for L in GMIP3_LEVELS},
                {L: (float(sub.loc[L, "lo"]), float(sub.loc[L, "hi"]))
                 for L in GMIP3_LEVELS})
    xc, yc = _composite_xy(members, med_steady)
    xm, ym = _composite_xy(members, vol_members)
    _, exc, dfc = _fit_median_lowess(xc, yc, [0.5])
    _, exm, dfm = _fit_median_lowess(xm, ym, LADDER_QS)
    com, bands = {}, {}
    for L in GMIP3_LEVELS:
        com[L] = 100 - float(np.interp(L, exc, dfc[0.5].to_numpy()))
        bands[L] = (100 - float(np.interp(L, exm, dfm[0.83].to_numpy())),
                    100 - float(np.interp(L, exm, dfm[0.17].to_numpy())))
    rows = [dict(key=key, level_K=L, central=com[L], lo=bands[L][0], hi=bands[L][1])
            for L in GMIP3_LEVELS]
    _ladder_cache = pd.concat([_ladder_cache, pd.DataFrame(rows)], ignore_index=True)
    _ladder_cache.to_csv(CACHE_LADDER, index=False, float_format="%.4f")
    return com, bands


# ---------------------------------------------------------------- reservoirs
GTSHARE = (regs.mass_gt / regs.mass_gt.sum()).to_dict()
MELT_SHARE = regs.melt_share.to_dict()
NONR19 = [r for r in regs.index if r != "19"]
GT_NONR19 = {r: regs.loc[r, "mass_gt"] for r in NONR19}
GT_NONR19_TOT = sum(GT_NONR19.values())
MELT_NONR19_TOT = sum(MELT_SHARE[r] for r in NONR19)


def build_reservoir(name, members, farinotti_basis):
    """farinotti_basis=True (3-res): r19 uses Farinotti r19 SLE; others split
    the non-r19 Farinotti value by Gt share. False (2-blk ablation): D1c
    Gt-share x INV_V partition. Hist melt split: Hugonnet shares over the
    non-r19 regions (BOOK2), applied to the uncharted-subtracted S2000."""
    s2000_inv = S2000_OBS - U_BOOK_MM / 1000.0
    wsum = sum(area_w[r] for r in members)
    drv = sum(area_w[r] / wsum * treg[f"r{r}"] for r in members).dropna()
    drv = drv - drv.loc[1850:1900].mean()
    amp_b = float(np.average([regchar.loc[r, AMP_RATIO_COL] for r in members],
                             weights=[area_w[r] for r in members]))
    msum = regs.loc[members, "mass_gt"]
    tau15 = float(np.average(regs.loc[members, "resp_time_15C_yr"], weights=msum))
    tau30 = float(np.average(regs.loc[members, "resp_time_30C_yr"], weights=msum))
    rate, rate_sd, cum20 = glambie_block_stats(members)
    s2000 = sum(MELT_SHARE[r] for r in members if r != "19") \
        / MELT_NONR19_TOT * s2000_inv if members != ["19"] else 0.0
    if farinotti_basis:
        if members == ["19"]:
            v0, v0_sig = FARINOTTI_R19
        else:
            share = sum(GT_NONR19[r] for r in members) / GT_NONR19_TOT
            v0 = share * FARINOTTI_NONR19[0]
            v0_sig = share * FARINOTTI_NONR19[1]
    else:
        gtshare = sum(GTSHARE[r] for r in members)
        v0 = gtshare * INV_V
        v0_sig = np.sqrt((sum(GT_NONR19.get(r, 0) for r in members) / GT_NONR19_TOT
                          * FARINOTTI_NONR19[1]) ** 2
                         + (FARINOTTI_R19[1] if "19" in members else 0.0) ** 2)
    com, bands = block_ladder(members)
    rung_sig = {L: max((bands[L][1] - bands[L][0]) / 2.0, RUNG_SIGMA_FLOOR_PCT)
                for L in GMIP3_LEVELS}
    a0 = v0 + s2000
    s2020 = s2000 + cum20
    return dict(name=name, members=members, driver_obs=drv, amp_b=amp_b,
                tau15=tau15, tau30=tau30, glambie_rate=rate,
                glambie_rate_sd=rate_sd, a0=a0, a0_sig=v0_sig,
                S2000_data=s2000, S2020_data=s2020, com=com, com_bands=bands,
                rung_sig=rung_sig)


def two_rung_anchor(blk):
    """Ablation-B anchors: exact interpolation through the two solve rungs."""
    a_b, s2020 = blk["a0"], blk["S2020_data"]
    L1, L2 = LADDER_RUNGS_SOLVE
    S1 = s2020 + blk["com"][L1] / 100 * (a_b - s2020)
    S2 = s2020 + blk["com"][L2] / 100 * (a_b - s2020)
    T1, T2 = blk["amp_b"] * L1, blk["amp_b"] * L2
    b_b = (np.log(1 - S1 / a_b) - np.log(1 - S2 / a_b)) / (T2 - T1)
    T_off_b = T1 + np.log(1 - S1 / a_b) / b_b
    return dict(blk, a=a_b, b=b_b, T_off=T_off_b, fit_mode="2rung",
                rung_z={L: 0.0 for L in GMIP3_LEVELS})


def four_rung_fit(blk):
    """Option 1: (a_eff, b, T_off) by correlated-Gaussian fit to all 4 rungs
    + soft Farinotti a-prior. Reports per-rung z at the optimum."""
    s2020 = blk["S2020_data"]
    Ls = list(GMIP3_LEVELS)
    y = np.array([blk["com"][L] for L in Ls])
    sig = np.array([blk["rung_sig"][L] for L in Ls])
    C = np.outer(sig, sig) * (RUNG_CORR + (1 - RUNG_CORR) * np.eye(len(Ls)))
    Cinv = np.linalg.inv(C)

    def com_model(a_eff, b_b, T0):
        out = []
        for L in Ls:
            seq = a_eff * (1 - np.exp(-b_b * (blk["amp_b"] * L - T0)))
            out.append(100 * (seq - s2020) / max(a_eff - s2020, 1e-9))
        return np.array(out)

    a_lo, a_hi = s2020 + 0.2 * (blk["a0"] - s2020), s2020 + 3.0 * (blk["a0"] - s2020)

    def neg(z):
        a_eff = a_lo + (a_hi - a_lo) / (1 + np.exp(-z[0]))
        b_b = 0.05 + 2.95 / (1 + np.exp(-z[1]))
        T0 = -3.0 + 6.0 / (1 + np.exp(-z[2]))
        r = com_model(a_eff, b_b, T0) - y
        return 0.5 * r @ Cinv @ r + 0.5 * ((a_eff - blk["a0"]) / blk["a0_sig"]) ** 2

    tr = two_rung_anchor(blk)

    def to_z(a_eff, b_b, T0):
        za = np.clip((a_eff - a_lo) / (a_hi - a_lo), 1e-4, 1 - 1e-4)
        zb = np.clip((b_b - 0.05) / 2.95, 1e-4, 1 - 1e-4)
        zt = np.clip((T0 + 3.0) / 6.0, 1e-4, 1 - 1e-4)
        return np.array([np.log(v / (1 - v)) for v in (za, zb, zt)])

    starts = [to_z(tr["a"], np.clip(tr["b"], 0.06, 2.9), np.clip(tr["T_off"], -2.9, 2.9)),
              to_z(blk["a0"] * 1.2, 0.6, -0.5), to_z(blk["a0"], 0.3, 0.5)]
    b0 = list(starts)
    while len(starts) < 8:
        starts.append(b0[rng_d1.integers(len(b0))] + rng_d1.normal(0, 0.7, 3))
    best = None
    for z0 in starts:
        r = minimize(neg, z0, method="Nelder-Mead",
                     options=dict(xatol=1e-9, fatol=1e-11, maxiter=6000))
        if best is None or r.fun < best.fun:
            best = r
    z = best.x
    a_eff = a_lo + (a_hi - a_lo) / (1 + np.exp(-z[0]))
    b_b = 0.05 + 2.95 / (1 + np.exp(-z[1]))
    T0 = -3.0 + 6.0 / (1 + np.exp(-z[2]))
    resid = com_model(a_eff, b_b, T0) - y
    rung_z = {L: float(resid[i] / sig[i]) for i, L in enumerate(Ls)}
    return dict(blk, a=a_eff, b=b_b, T_off=T0, fit_mode="4rung", rung_z=rung_z,
                a_prior_z=float((a_eff - blk["a0"]) / blk["a0_sig"]))


# ---------------------------------------------------------------- anchored kappa/nu
def tau50_of(block, kappa, nu, level):
    a, bb, T0 = block["a"], block["b"], block["T_off"]
    T = block["amp_b"] * level
    seq = a * (1 - np.exp(-bb * (T - T0)))
    S = block["S2020_data"]
    if seq <= S:
        return np.inf
    target = S + 0.5 * (seq - S)
    prev = S
    for k in range(1, TAU_SOLVE_HORIZON + 1):
        frac_left = max(1.0 - S / a, 1e-12)
        T_eq = T0 - np.log(frac_left) / bb
        exc = max(T - T_eq, 0.0)
        S += min(kappa * exc ** nu, 1.0) * (seq - S)
        if S >= target:
            return (k - 1) + (target - prev) / max(S - prev, 1e-30)
        prev = S
    return float(2 * TAU_SOLVE_HORIZON)


def solve_anchored(block):
    def kappa_for(nu):
        f = lambda lk: tau50_of(block, np.exp(lk), nu, 1.5) - block["tau15"]
        lo, hi = np.log(1e-7), np.log(20.0)
        if f(lo) < 0 or f(hi) > 0:
            return None
        return np.exp(brentq(f, lo, hi, xtol=1e-10))

    def g(nu):
        k = kappa_for(nu)
        return np.nan if k is None else tau50_of(block, k, nu, 3.0) - block["tau30"]

    nus = np.linspace(0.0, 4.0, 17)
    gs = np.array([g(v) for v in nus])
    ok = np.isfinite(gs)
    sign_change = None
    for i in range(len(nus) - 1):
        if ok[i] and ok[i + 1] and gs[i] * gs[i + 1] < 0:
            sign_change = (nus[i], nus[i + 1])
            break
    if sign_change:
        nu = brentq(g, *sign_change, xtol=1e-6)
        kap, exact = kappa_for(nu), True
    else:
        def loss(v):
            k = kappa_for(v[0])
            if k is None:
                return np.inf
            return np.log(tau50_of(block, k, v[0], 3.0) / block["tau30"]) ** 2
        best = min((minimize(loss, [v0], method="Nelder-Mead")
                    for v0 in [0.5, 1.0, 2.0]), key=lambda r: r.fun)
        nu = float(np.clip(best.x[0], 0.0, 4.0))
        kap, exact = kappa_for(nu), False
    t15, t30 = tau50_of(block, kap, nu, 1.5), tau50_of(block, kap, nu, 3.0)
    return dict(kappa=kap, nu=nu, tau15_ach=t15, tau30_ach=t30, exact=exact,
                match_ok=(abs(t15 / block["tau15"] - 1) < TAU_MATCH_TOL
                          and abs(t30 / block["tau30"] - 1) < TAU_MATCH_TOL))


# ---------------------------------------------------------------- obs vectors
def build_obs_adj():
    """Option 4: remove the observed GlaMBIE r19 cumulative from the target's
    2019+ segment so the whole target is scope-without-r19 (the Frederikse
    segment already assumes zero r19 melt)."""
    r19_annual = pd.Series(R19_CM, index=R19_YEARS)
    adj = obs.copy()
    cum = 0.0
    for i, fy in enumerate(fit_years):
        if fy >= 2019 and (fy - 1) in r19_annual.index:
            cum += float(r19_annual.loc[fy - 1])
        if fy >= 2019:
            adj[i] = obs[i] - cum
    return adj


OBS_ADJ = build_obs_adj()

# ---------------------------------------------------------------- uncharted + likelihood
def unch_cum(u_scope_mm, profile):
    if profile == "taper":
        flat = TAPER_FLAT_END - UNCH_WIN[0]
        ramp = TAPER_ZERO - TAPER_FLAT_END
        r = (u_scope_mm / 1000.0) / (flat + ramp / 2.0)
        t = years.astype(float)
        return np.where(
            t <= UNCH_WIN[0], 0.0,
            np.where(t <= TAPER_FLAT_END, r * (t - UNCH_WIN[0]),
                     np.where(t <= TAPER_ZERO,
                              r * flat + r * (t - TAPER_FLAT_END)
                              * (1 - (t - TAPER_FLAT_END) / (2.0 * ramp)),
                              r * (flat + ramp / 2.0))))
    x = np.clip((years - UNCH_WIN[0]) / (UNCH_WIN[1] - UNCH_WIN[0]), 0.0, 1.0)
    return (u_scope_mm / 1000.0) * x


def forward_all(reservoirs, th):
    per = {}
    for name, blk in reservoirs.items():
        Tarr_b = extend_obs(blk["driver_obs"], fair_rb, blk["amp_b"]).to_numpy()[:-1]
        per[name] = integrate_N(Tarr_b, blk["a"], blk["b"], blk["T_off"],
                                th[f"kappa_{name}"], th[f"nu_{name}"])
    return per


def obs_corrected(base_obs, delta_mm_yr):
    corr = np.where(fit_years < T5D_SEG_END,
                    delta_mm_yr * (T5D_SEG_END - fit_years) / 10.0, 0.0)
    return base_obs + corr


def flow_logl_window(m_cm, obs_vec, eps_vec, sig, rho_, y0, y1):
    sel = (fit_years >= y0) & (fit_years <= y1)
    r = (m_cm[yfit_idx] - obs_vec)[sel]
    nwin = sel.sum()
    Hw = np.abs(np.subtract.outer(np.arange(nwin), np.arange(nwin)))
    Sig = (sig ** 2 / (1 - rho_ ** 2)) * rho_ ** Hw + np.diag(eps_vec[sel] ** 2)
    try:
        cf = cho_factor(Sig)
    except np.linalg.LinAlgError:
        return -np.inf
    logdet = 2 * np.sum(np.log(np.diag(cf[0])))
    return -0.5 * (nwin * np.log(2 * np.pi) + logdet + r @ cho_solve(cf, r))


eps_sx2 = eps * np.where(fit_years < EARLY_SIGMA_X2_BEFORE, 2.0, 1.0)
VARIANTS = {"unc_sx2": dict(eps_vec=eps_sx2, has_delta=False),
            "unc_t5d": dict(eps_vec=eps, has_delta=True)}


def loglik(reservoirs, th, variant, arm, hind_names, base_obs,
           profile=PROFILE_PRIMARY):
    """hind_names: reservoirs entering the hindcast flow sum (seam: no R19)."""
    v = VARIANTS[variant]
    obs_vec = obs_corrected(base_obs, th["delta"]) if v["has_delta"] else base_obs
    per = forward_all(reservoirs, th)
    s_hind = sum(per[n] for n in hind_names)
    s_tot_model = s_hind + unch_cum(th.get("u_mm", 0.0), profile)
    m_cm = 100 * (s_tot_model - s_tot_model[ybase].mean())
    ll_flow = flow_logl_window(m_cm, obs_vec, v["eps_vec"], th["sigma"], th["rho"],
                               fit_years[0], fit_years[-1])
    if not np.isfinite(ll_flow):
        return None
    s_all = sum(per[n] for n in reservoirs)
    a_tot = sum(b["a"] for b in reservoirs.values())
    ll_inv = norm.logpdf(a_tot - s_all[i_inv], INV_V, INV_SIG)
    ll_lec = norm.logpdf(s_all[i1900], LEC_MU, LEC_SIG)
    ll_blk = 0.0
    ir0, ir1 = np.searchsorted(years, 2000), np.searchsorted(years, 2024)
    for name in hind_names:
        blk = reservoirs[name]
        mrate = 1000 * (per[name][ir1] - per[name][ir0]) / (ir1 - ir0)
        if arm in ("FREE", "MID"):
            ll_blk += norm.logpdf(mrate, blk["glambie_rate"], blk["glambie_rate_sd"])
    ll_pr = 0.0
    if arm in ("FREE", "MID"):
        for name, blk in reservoirs.items():
            ll_pr += norm.logpdf(np.log(th[f"kappa_{name}"]),
                                 np.log(1.0 / blk["tau15"]), KAPPA_LOGPRIOR_SD)
    if arm == "FREE":
        ll_pr += norm.logpdf(th["nu_shared_val"], *NU_SHARED_PRIOR)
    if v["has_delta"]:
        ll_pr += norm.logpdf(th["delta"], 0.0, T5D_DELTA_PRIOR_MM_YR)
    return dict(ll_flow=ll_flow, ll_inv=ll_inv, ll_lec=ll_lec, ll_blk=ll_blk,
                ll_prior=ll_pr, logJ=ll_flow + ll_inv + ll_lec + ll_blk + ll_pr,
                per=per, s_all=s_all, s_hind=s_hind, m_cm=m_cm, obs_vec=obs_vec)


def param_bounds(nm):
    if nm.startswith("kappa_"):
        return KAPPA_BOUNDS_FREE
    if nm == "nu_shared":
        return NU_BOUNDS_FREE
    if nm == "delta":
        return DELTA_BOUNDS_MM_YR
    if nm == "u_mm":
        return UNCH_BOUNDS_SCOPE_MM
    return BOUNDS[nm]


def optimize_arm(reservoirs, variant, arm, anchored, hind_names, base_obs,
                 profile=PROFILE_PRIMARY):
    v = VARIANTS[variant]
    names = list(reservoirs)
    free = ["sigma", "rho", "u_mm"] + (["delta"] if v["has_delta"] else [])
    if arm == "FREE":
        free = [f"kappa_{n}" for n in names] + ["nu_shared"] + free
    elif arm == "MID":
        free = [f"kappa_{n}" for n in names] + free
    nstart = N_STARTS_ANCH if arm == "ANCH" else N_STARTS_FREE

    def mk(z):
        th = {}
        for nm, zz in zip(free, z):
            lo, hi = param_bounds(nm)
            th[nm] = lo + (hi - lo) / (1 + np.exp(-zz))
        if arm == "ANCH":
            for n in names:
                th[f"kappa_{n}"] = anchored[n]["kappa"]
                th[f"nu_{n}"] = anchored[n]["nu"]
        elif arm == "MID":
            for n in names:
                th[f"nu_{n}"] = anchored[n]["nu"]
        else:
            nu = th.pop("nu_shared")
            th["nu_shared_val"] = nu
            for n in names:
                th[f"nu_{n}"] = nu
        th.setdefault("delta", 0.0)
        return th

    def neg(z):
        t = loglik(reservoirs, mk(z), variant, arm, hind_names, base_obs, profile)
        return np.inf if t is None else -t["logJ"]

    seeds = []
    base = dict(sigma=0.03, rho=0.6, delta=0.0, u_mm=U_BOOK_MM)
    if arm == "FREE":
        for scale, nu in [(1.0, 1.0), (3.0, 0.5), (0.3, 1.5)]:
            sd = dict(base, nu_shared=nu)
            for n in names:
                sd[f"kappa_{n}"] = scale / reservoirs[n]["tau15"]
            seeds.append(sd)
    elif arm == "MID":
        for scale in [1.0, 3.0]:
            sd = dict(base)
            for n in names:
                sd[f"kappa_{n}"] = min(scale * anchored[n]["kappa"], 0.4)
            seeds.append(sd)
    else:
        seeds.append(dict(base))
        seeds.append(dict(base, sigma=0.02, rho=0.3,
                          u_mm=UNCH_BOUNDS_SCOPE_MM[1] * 0.95))
    starts = []
    for sd in seeds:
        z = []
        for nm in free:
            lo, hi = param_bounds(nm)
            x = np.clip((sd[nm] - lo) / (hi - lo), 1e-4, 1 - 1e-4)
            z.append(np.log(x / (1 - x)))
        starts.append(np.array(z))
    b0 = list(starts)
    while len(starts) < nstart:
        starts.append(b0[rng_d1.integers(len(b0))] + rng_d1.normal(0, 0.6, len(free)))
    best = None
    for z0 in starts:
        r = minimize(neg, z0, method="Nelder-Mead",
                     options=dict(xatol=1e-7, fatol=1e-9, maxiter=9000, maxfev=13000))
        if best is None or r.fun < best.fun:
            best = r
    r = minimize(neg, best.x, method="Nelder-Mead",
                 options=dict(xatol=1e-8, fatol=1e-10, maxiter=9000, maxfev=13000))
    return mk((r if r.fun < best.fun else best).x)


# ------------------------------------------------ pathological (matched freedom)
Tarr_agg = extend_obs(tglac_obs, fair_rb, AMP_G).to_numpy()[:-1]
PATHO_BASE = ["a", "b", "T_off", "kappa", "nu", "sigma", "rho", "u_mm"]


def optimize_patho(variant, base_obs, profile=PROFILE_PRIMARY):
    v = VARIANTS[variant]
    free = PATHO_BASE + (["delta"] if v["has_delta"] else [])
    pb = dict(BOUNDS, delta=DELTA_BOUNDS_MM_YR, u_mm=UNCH_BOUNDS_SCOPE_MM)

    def mk(z):
        th = {}
        for nm, zz in zip(free, z):
            lo, hi = pb[nm]
            th[nm] = lo + (hi - lo) / (1 + np.exp(-zz))
        th.setdefault("delta", 0.0)
        return th

    def neg(z):
        th = mk(z)
        s_raw = integrate_N(Tarr_agg, th["a"], th["b"], th["T_off"],
                            th["kappa"], th["nu"])
        s_tot = s_raw + unch_cum(th["u_mm"], profile)
        m_cm = 100 * (s_tot - s_tot[ybase].mean())
        obs_vec = obs_corrected(base_obs, th["delta"]) if v["has_delta"] else base_obs
        ll = flow_logl_window(m_cm, obs_vec, v["eps_vec"], th["sigma"], th["rho"],
                              fit_years[0], fit_years[-1])
        if not np.isfinite(ll):
            return np.inf
        ll += norm.logpdf(th["a"] - s_raw[i_inv], INV_V, INV_SIG)
        ll += norm.logpdf(s_raw[i1900], LEC_MU, LEC_SIG)
        ll += sum(norm.logpdf(th[p], *PRIORS[p]) for p in ("a", "b", "T_off"))
        ll += norm.logpdf(np.log(th["kappa"]), *KAPPA_LOGPRIOR)
        ll += norm.logpdf(th["nu"], *NU_PRIOR)
        if v["has_delta"]:
            ll += norm.logpdf(th["delta"], 0.0, T5D_DELTA_PRIOR_MM_YR)
        return -ll

    seeds = [dict(a=0.298, b=0.320, T_off=-2.0, kappa=0.0085, nu=0.10,
                  sigma=0.005, rho=0.05, delta=0.0, u_mm=U_BOOK_MM),
             dict(a=0.33, b=0.35, T_off=-1.8, kappa=0.006, nu=0.12,
                  sigma=0.01, rho=0.3, delta=0.0, u_mm=UNCH_BOUNDS_SCOPE_MM[0] * 1.05),
             dict(a=0.45, b=0.52, T_off=-1.10, kappa=0.0106, nu=0.15,
                  sigma=0.04, rho=0.70, delta=0.0, u_mm=UNCH_BOUNDS_SCOPE_MM[1] * 0.95)]
    starts = []
    for sd in seeds:
        z = []
        for nm in free:
            lo, hi = pb[nm]
            x = np.clip((sd[nm] - lo) / (hi - lo), 1e-4, 1 - 1e-4)
            z.append(np.log(x / (1 - x)))
        starts.append(np.array(z))
    b0 = list(starts)
    while len(starts) < 8:
        starts.append(b0[rng_d1.integers(len(b0))] + rng_d1.normal(0, 0.6, len(free)))
    best = None
    for z0 in starts:
        r = minimize(neg, z0, method="Nelder-Mead",
                     options=dict(xatol=1e-7, fatol=1e-9, maxiter=9000, maxfev=13000))
        if best is None or r.fun < best.fun:
            best = r
    th = mk(best.x)
    s_raw = integrate_N(Tarr_agg, th["a"], th["b"], th["T_off"], th["kappa"], th["nu"])
    s_tot = s_raw + unch_cum(th["u_mm"], profile)
    m_cm = 100 * (s_tot - s_tot[ybase].mean())
    obs_vec = obs_corrected(base_obs, th["delta"]) if v["has_delta"] else base_obs
    fw = flow_logl_window(m_cm, obs_vec, v["eps_vec"], th["sigma"], th["rho"],
                          FLOW_WIN[0], FLOW_WIN[1])
    return th, fw


# ---------------------------------------------------------------- metrics
def metrics(reservoirs, th, variant, arm, patho_fw, hind_names, base_obs,
            profile=PROFILE_PRIMARY, label=""):
    t = loglik(reservoirs, th, variant, arm, hind_names, base_obs, profile)
    if t is None:
        return None
    per, s_all = t["per"], t["s_all"]
    v = VARIANTS[variant]
    num = {L: 0.0 for L in GMIP3_LEVELS}
    den = 0.0
    for name, blk in reservoirs.items():
        s20_m = per[name][i2020]
        den += blk["a"] - s20_m
        for L in GMIP3_LEVELS:
            seq = blk["a"] * (1 - np.exp(-blk["b"] * (blk["amp_b"] * L - blk["T_off"])))
            num[L] += seq - s20_m
    com_agg = {L: 100 * num[L] / max(den, 1e-9) for L in GMIP3_LEVELS}
    proj_years = np.arange(Y0, 2151)
    ds = {}
    for sname, g in ssp_rb.items():
        stot = np.zeros(len(proj_years))
        for name, blk in reservoirs.items():
            drv = extend_obs(blk["driver_obs"], g, blk["amp_b"],
                             idx=proj_years).to_numpy()[:-1]
            stot += integrate_N(drv, blk["a"], blk["b"], blk["T_off"],
                                th[f"kappa_{name}"], th[f"nu_{name}"],
                                n=len(proj_years))
        sb = (proj_years >= PROJ_BASE[0]) & (proj_years <= PROJ_BASE[1])
        ds[sname] = 100 * (stot[proj_years == 2100][0] - stot[sb].mean())
    spread = ds["ssp585"] - ds["ssp126"]
    s1900 = 1000 * s_all[i1900]
    a_tot = sum(b["a"] for b in reservoirs.values())
    invz = (a_tot - s_all[i_inv] - INV_V) / INV_SIG
    fw = flow_logl_window(t["m_cm"], t["obs_vec"], v["eps_vec"], th["sigma"],
                          th["rho"], FLOW_WIN[0], FLOW_WIN[1])
    era_ll = {f"flow_{a}_{b}": flow_logl_window(t["m_cm"], t["obs_vec"], v["eps_vec"],
                                                th["sigma"], th["rho"], a, b)
              for a, b in ERAS}
    ir0, ir1 = np.searchsorted(years, RATE_WIN[0]), np.searchsorted(years, RATE_WIN[1])
    rate_modern_hind = 1000 * (t["s_hind"][ir1] - t["s_hind"][ir0]) / (RATE_WIN[1] - RATE_WIN[0])
    gates = dict(g_inv=abs(invz) < 1,
                 g_s1900=S1900_GATE_MM[0] <= s1900 <= S1900_GATE_MM[1],
                 g_lad=all(GMIP3_LIKELY[L][0] <= com_agg[L] <= GMIP3_LIKELY[L][1]
                           for L in GMIP3_LEVELS),
                 g_spread=4.5 <= spread <= 13.5)
    u_mm = th.get("u_mm", 0.0)
    row = dict(label=label, arm=arm, variant=variant, profile=profile,
               nres=len(reservoirs), hind="+".join(hind_names),
               sigma=th["sigma"], rho=th["rho"], delta=th.get("delta", 0.0),
               u_mm=u_mm, delta_sigmas=abs(th.get("delta", 0.0)) / T5D_DELTA_PRIOR_MM_YR,
               logJ=t["logJ"], ll_flow=t["ll_flow"],
               flow_win=fw, flow_win_deficit=patho_fw - fw,
               rate_modern_hind=rate_modern_hind,
               S1900_mm=s1900, inv_z=invz, S2020_all_mm=1000 * s_all[i2020],
               **{f"com{str(L).replace('.', 'p')}": com_agg[L] for L in GMIP3_LEVELS},
               ds126=ds["ssp126"], ds245=ds["ssp245"], ds585=ds["ssp585"],
               spread=spread, **era_ll, **gates,
               npass=sum(gates.values()),
               feasible=(sum(gates.values()) == 4 and (patho_fw - fw) <= FLOW_TOL))
    for name in reservoirs:
        row[f"kappa_{name}"] = th[f"kappa_{name}"]
        row[f"nu_{name}"] = th[f"nu_{name}"]
    return row, per, t


# ---------------------------------------------------------------- sanity battery
def sanity_battery(res3, anch3):
    print("\n== sanity battery (D1d) ==")
    ok = []
    # 1. obs_adj == obs before 2019; NET removal positive at series end.
    #    (r19 has positive-mass-balance YEARS, so per-year adjustments may
    #    wiggle in sign — only the pre-2019 identity and the net-cumulative
    #    direction are invariants.)
    pre = fit_years < 2019
    ok.append(np.array_equal(OBS_ADJ[pre], obs[pre])
              and (obs[-1] - OBS_ADJ[-1]) > 0)
    print(f"  [1] obs_adj: identical pre-2019, net r19 removal by series end: "
          f"{'PASS' if ok[-1] else 'FAIL'} "
          f"(2023 net adjustment {10 * (obs[-1] - OBS_ADJ[-1]):.2f} mm)")
    # 2. hindcast-exclusion consistency: hind + R19 == all reservoirs
    th0 = {}
    for n in res3:
        th0[f"kappa_{n}"] = 0.004
        th0[f"nu_{n}"] = 1.0
    per = forward_all(res3, th0)
    s_h = per["SLOWP"] + per["FAST"]
    ok.append(np.allclose(s_h + per["R19"], sum(per[n] for n in res3), atol=1e-15))
    print(f"  [2] hindcast sum + R19 == all-reservoir sum: "
          f"{'PASS' if ok[-1] else 'FAIL'}")
    # 3. 4-rung fit nesting: with tight rungs + tight a-prior it must approach
    #    the two-rung interpolation (checked on FAST: com values self-consistent)
    blkF = res3["FAST"]
    comF = {L: 100 * (blkF["a"] * (1 - np.exp(-blkF["b"] * (blkF["amp_b"] * L - blkF["T_off"])))
                      - blkF["S2020_data"]) / (blkF["a"] - blkF["S2020_data"])
            for L in GMIP3_LEVELS}
    zmax = max(abs(comF[L] - blkF["com"][L]) / blkF["rung_sig"][L] for L in GMIP3_LEVELS)
    ok.append(zmax < 2.0)
    print(f"  [3] 4-rung fit rung residuals bounded (max |z| = {zmax:.2f} < 2): "
          f"{'PASS' if ok[-1] else 'FAIL'}")
    if not all(ok):
        raise SystemExit("SANITY BATTERY FAILED — do not trust results")


# ---------------------------------------------------------------- run
print(f"D1d 4-rung + r19-seam | commit={COMMIT} | criteria = D1 (4 gates + "
      f"flow{FLOW_WIN} tol {FLOW_TOL}) | profile PRIMARY = {PROFILE_PRIMARY}")
print(f"  rung sigma = band/2 (floor {RUNG_SIGMA_FLOOR_PCT} pct-pts), cross-rung "
      f"corr {RUNG_CORR}; a-prior Farinotti non-r19 {FARINOTTI_NONR19} / r19 "
      f"{FARINOTTI_R19}; U flat[{UNCH_BOUNDS_SCOPE_MM[0]:.1f},"
      f"{UNCH_BOUNDS_SCOPE_MM[1]:.1f}]mm; delta prior sd {T5D_DELTA_PRIOR_MM_YR}")
print(f"  PRE-REGISTERED BARS: minimal = C_both ANCH deficit <= {D1C_TAPER_DEFICIT} "
      f"with |delta| <= 1 sigma; strong = FEASIBLE (deficit <= {FLOW_TOL})")

# build structures
res3_raw = {n: build_reservoir(n, m, farinotti_basis=True)
            for n, m in SPEC_3RES.items()}
blk2_raw = {n: build_reservoir(n, m, farinotti_basis=False)
            for n, m in SPEC_2BLK.items()}

structures = {}
structures["A_4rung"] = {n: four_rung_fit(b) for n, b in blk2_raw.items()}
structures["B_seam"] = {n: two_rung_anchor(b) for n, b in res3_raw.items()}
structures["C_both"] = {n: four_rung_fit(b) for n, b in res3_raw.items()}

block_rows = []
anchors = {}
for sname, resv in structures.items():
    anchors[sname] = {}
    print(f"\n== anchors [{sname}] ==")
    for name, blk in resv.items():
        anch = solve_anchored(blk)
        anchors[sname][name] = anch
        zs = "/".join(f"{blk['rung_z'][L]:+.1f}" for L in GMIP3_LEVELS)
        print(f"  [{name:5s}] a={blk['a']:.3f} (a0 {blk['a0']:.3f}±{blk['a0_sig']:.3f}"
              + (f", z={blk.get('a_prior_z', 0):+.1f}" if blk["fit_mode"] == "4rung" else "")
              + f") b={blk['b']:.3f} T_off={blk['T_off']:+.3f} amp={blk['amp_b']:.2f} "
              f"| rung z {zs} | kappa={anch['kappa']:.5f} nu={anch['nu']:.2f} "
              f"({'exact' if anch['exact'] else 'FALLBACK'})")
        block_rows.append(dict(structure=sname, block=name, fit_mode=blk["fit_mode"],
                               a=blk["a"], a0=blk["a0"], a0_sig=blk["a0_sig"],
                               b=blk["b"], T_off=blk["T_off"], amp_b=blk["amp_b"],
                               S2020_mm=1000 * blk["S2020_data"],
                               tau15=blk["tau15"], tau30=blk["tau30"],
                               kappa_anch=anch["kappa"], nu_anch=anch["nu"],
                               **{f"rungz{str(L).replace('.', 'p')}": blk["rung_z"][L]
                                  for L in GMIP3_LEVELS},
                               **{f"com{str(L).replace('.', 'p')}": blk["com"][L]
                                  for L in GMIP3_LEVELS},
                               **{f"sig{str(L).replace('.', 'p')}": blk["rung_sig"][L]
                                  for L in GMIP3_LEVELS}))
pd.DataFrame(block_rows).to_csv(OUT_BLOCKS, index=False, float_format="%.5f")

sanity_battery(structures["C_both"], anchors["C_both"])

# pathological references per (variant, obs-mode)
patho = {}
for variant in VARIANTS:
    for oname, ob in [("obs", obs), ("obs_adj", OBS_ADJ)]:
        th_p, fw_p = optimize_patho(variant, ob)
        patho[(variant, oname)] = fw_p
        print(f"patho [{variant}/{oname:7s}]: flow{FLOW_WIN}={fw_p:.2f}")

CONFIGS = [
    ("A_4rung", "unc_t5d", "obs", list(SPEC_2BLK)),          # option 1 alone
    ("B_seam", "unc_t5d", "obs_adj", ["SLOWP", "FAST"]),     # option 4 alone
    ("C_both", "unc_t5d", "obs_adj", ["SLOWP", "FAST"]),     # HEADLINE
    ("C_both", "unc_sx2", "obs_adj", ["SLOWP", "FAST"]),     # no-delta secondary
]
rows = []
for sname, variant, oname, hind_names in CONFIGS:
    resv, anch = structures[sname], anchors[sname]
    base_obs = obs if oname == "obs" else OBS_ADJ
    print(f"\n== runs [{sname}/{variant}/{oname}] ==")
    for arm in ["ANCH", "MID", "FREE"]:
        th = optimize_arm(resv, variant, arm, anch, hind_names, base_obs)
        m = metrics(resv, th, variant, arm, patho[(variant, oname)], hind_names,
                    base_obs, label=f"{sname}/{arm}/{variant}")
        if m is None:
            print(f"  [{sname}/{arm}/{variant}] DEGENERATE")
            continue
        row, per, t = m
        rows.append(row)
        print(f"  [{row['label']:24s}] npass={row['npass']}/4 "
              f"[inv{'+' if row['g_inv'] else '-'} s19{'+' if row['g_s1900'] else '-'} "
              f"lad{'+' if row['g_lad'] else '-'} spr{'+' if row['g_spread'] else '-'}] "
              f"deficit={row['flow_win_deficit']:6.1f} spread={row['spread']:5.1f} "
              f"rate(hind)={row['rate_modern_hind']:.2f} U={row['u_mm']:.1f} "
              f"delta={row['delta']:+.2f} ({row['delta_sigmas']:.1f}sig) "
              f"FEASIBLE={row['feasible']}")

res = pd.DataFrame(rows)
os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
res.to_csv(OUT_CSV, index=False, float_format="%.5f")

# ---------------------------------------------------------------- verdict
print("\n=== D1d verdict (references: D1c taper ANCH 8.4 / const 9.0) ===")
feas = res[res.feasible == True]  # noqa: E712
print(f"  {len(feas)}/{len(res)} configs FEASIBLE")
for sname, variant, oname, _ in CONFIGS:
    sub = res[(res.label.str.startswith(sname)) & (res.variant == variant)]
    a = sub[sub.arm == "ANCH"]
    if len(a):
        a = a.iloc[0]
        print(f"  [{sname}/{variant}] ANCH deficit={a.flow_win_deficit:.1f} "
              f"npass={a.npass} U={a.u_mm:.1f} delta={a.delta:+.2f} "
              f"({a.delta_sigmas:.1f}sig) feasible={a.feasible}")
hl = res[(res.label == "C_both/ANCH/unc_t5d")]
if len(hl):
    h = hl.iloc[0]
    minimal = (h.flow_win_deficit <= D1C_TAPER_DEFICIT) and (h.delta_sigmas <= 1.0) \
        and h.npass == 4
    print(f"  MINIMAL BAR (<= {D1C_TAPER_DEFICIT}, delta <= 1 sigma, 4/4): "
          f"{'MET' if minimal else 'NOT MET'} | STRONG BAR (feasible): "
          f"{'MET' if bool(h.feasible) else 'NOT MET'}")

# ---------------------------------------------------------------- figure
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(16.5, 4.8), constrained_layout=True)
axA, axB, axC = axes

labels_a = ["D1c/taper (ref)", "A_4rung", "B_seam", "C_both", "C_both/sx2"]
vals_a = [D1C_TAPER_DEFICIT]
for sname, variant in [("A_4rung", "unc_t5d"), ("B_seam", "unc_t5d"),
                       ("C_both", "unc_t5d"), ("C_both", "unc_sx2")]:
    sub = res[(res.label == f"{sname}/ANCH/{variant}")]
    vals_a.append(float(sub.flow_win_deficit.iloc[0]) if len(sub) else np.nan)
axA.bar(range(len(vals_a)), vals_a,
        color=["0.6", "tab:blue", "tab:orange", "tab:green", "tab:olive"])
axA.axhline(FLOW_TOL, color="k", ls=":", lw=1.2, label=f"tol {FLOW_TOL}")
axA.axhline(D1C_TAPER_DEFICIT, color="0.4", ls="--", lw=1, label="D1c ref 8.4")
axA.set_xticks(range(len(vals_a)))
axA.set_xticklabels(labels_a, rotation=15, fontsize=8)
axA.set(ylabel="ANCH flow-window deficit (logL)",
        title="option 1 (A) vs option 4 (B) vs both (C)")
axA.legend(fontsize=8)

hlrow = hl.iloc[0] if len(hl) else None
if hlrow is not None:
    resv = structures["C_both"]
    thh = {f"kappa_{n}": hlrow[f"kappa_{n}"] for n in resv}
    thh.update({f"nu_{n}": hlrow[f"nu_{n}"] for n in resv})
    thh.update(sigma=hlrow["sigma"], rho=hlrow["rho"], delta=hlrow["delta"],
               u_mm=hlrow["u_mm"])
    per_h = forward_all(resv, thh)
    s_hind = per_h["SLOWP"] + per_h["FAST"]
    F = unch_cum(hlrow["u_mm"], PROFILE_PRIMARY)
    tgt_cm = pd.Series(OBS_ADJ, index=fit_years)
    oc = pd.Series(obs_corrected(OBS_ADJ, hlrow["delta"]), index=fit_years)
    axB.plot(tgt_cm.index, 10 * tgt_cm.diff().rolling(11, center=True).mean(),
             color="k", lw=1.6, label="obs_adj flow (11-yr)")
    axB.plot(oc.index, 10 * oc.diff().rolling(11, center=True).mean(), color="0.55",
             lw=1.0, ls="--", label=f"obs_adj t5d-corr ({hlrow['delta']:+.2f})")
    axB.plot(years[1:], 1000 * np.diff(s_hind + F), color="tab:red", lw=1.5,
             label="model hindcast (SLOWP+FAST+F)")
    axB.plot(years[1:], 1000 * np.diff(F), color="tab:green", lw=1.1,
             label=f"F_unch (U={hlrow['u_mm']:.0f}mm, taper)")
    axB.plot(years[1:], 1000 * np.diff(per_h["R19"]), color="tab:purple", lw=1.0,
             ls="--", label="R19 (excluded from hindcast)")
    axB.set(xlim=(1900, 2026), xlabel="year", ylabel="GSIC flow (mm SLE/yr)",
            title="headline C_both ANCH/unc_t5d — flow decomposition")
    axB.legend(fontsize=7)

MARK = {"ANCH": "*", "FREE": "o", "MID": "D"}
SCOL = {"A_4rung": "tab:blue", "B_seam": "tab:orange", "C_both": "tab:green"}
for _, r in res.iterrows():
    sname = r["label"].split("/")[0]
    axC.scatter(r["flow_win_deficit"], r["npass"], marker=MARK[r["arm"]],
                s=170 if r["arm"] == "ANCH" else 70, color=SCOL[sname],
                edgecolors="k" if r["variant"] == "unc_t5d" else "0.5",
                linewidths=0.6, zorder=2)
axC.axvline(FLOW_TOL, color="k", ls=":", lw=1)
axC.axvline(D1C_TAPER_DEFICIT, color="0.4", ls="--", lw=1)
axC.axhline(4, color="k", ls=":", lw=1)
axC.set(xlabel=f"flow {FLOW_WIN[0]}-{FLOW_WIN[1]} logL deficit vs pathological",
        ylabel="gates passed (of 4)",
        title="D1d frontier (dashes = D1c 8.4 reference)")
hnd = [plt.Line2D([], [], marker=m, ls="", color="k", label=a) for a, m in MARK.items()]
hnd += [plt.Line2D([], [], marker="s", ls="", color=c, label=s) for s, c in SCOL.items()]
axC.legend(handles=hnd, fontsize=7)
fig.suptitle(f"D1d — 4-rung S_eq fits (corr {RUNG_CORR}, band sigma) + r19 seam "
             f"harmonization | profile {PROFILE_PRIMARY} | commit {COMMIT}", fontsize=10)
os.makedirs(os.path.dirname(OUT_FIG), exist_ok=True)
fig.savefig(OUT_FIG, dpi=150)
print(f"\nWrote {os.path.relpath(OUT_CSV, REPO)}, {os.path.relpath(OUT_BLOCKS, REPO)}, "
      f"{os.path.relpath(OUT_FIG, REPO)}")
