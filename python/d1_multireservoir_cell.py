#!/usr/bin/env python3
"""D1 — offline multi-reservoir (regional-block) feasibility cell for T5a
(handoff_2026-08-07_t5a_multireservoir_lead.md §3; D0-successor pattern).

Question: can 2 Nauels-nu reservoirs with REGIONAL IDENTITY — a SLOW block
(long-response, high-committed regions) and a FAST block (short-response,
ETCW-forced regions), each with its own DRIVER, its own S_eq frame anchored to
the block's OWN GlacierMIP3 committed ladder, and its own transient — jointly
satisfy the aggregate constraint set that every one-excess-path law failed
(T1: 0/110; extB3: 0/4 gates)?

Structure per block b:  dS_b/dt = min(kappa_b*exc_b^nu_b, 1)*(S_eq,b - S_b)
  S_eq,b = a_b*(1 - exp(-b_b*(T_b - T_off_b)))     [Mengel exponential, per block]
  T_b(t) = GlaMBIE-year-2000-AREA-weighted mean of member-region HadCRUT5
           series (t_glac_regions_hadcrut5.csv), spliced forward with
           amp_b * scenario GMST (anchor = last SPLICE_ANCHOR_N obs years).
  GSIC = sum of blocks. Aggregate flow/inventory/Leclercq likelihoods as in T1.

Block assignment (sub-decision A): GlacierMIP3 50%-response time at ~1.5C
(S1a), threshold TAU_STAR; default 250 yr, scan {200, 250, 300} (250 and 300
give the same partition; 200 moves r04 into SLOW).

Anchors per block (data, not fit):
  a_b     = GTSHARE_b * V(0.290) + S2000_b        [sub-decision D: S3-2020-Gt shares]
  S2000_b = HIST_SLOW_SHARE split of aggregate S2000_OBS=0.093
            [sub-decision H — NOT in the handoff, flagged: the 1850-2000 melt
             partition is unconstrained on disk; default = Hugonnet 2000-19
             melt shares, scanned {0.25, default, 0.50}]
  S2020_b = S2000_b + GlaMBIE block cumulative 2000-2020 (exact, on disk)
  (b_b, T_off_b): CLOSED FORM from the block's own two-rung ladder —
            S_eq,b(amp_b*1.2) and S_eq,b(amp_b*2.0) = the block's committed
            fractions from the EXACT per-experiment GlacierMIP3 composite
            (T2 machinery: model-median steady state, scope=block, moepy
            quantile-LOWESS with the paper's frac auto-selection)
            [sub-decision G: exact estimator, as recommended]
  amp_b   = area-weighted regchar median_reg_vs_glob_temp_ch_1.5_3.0
            [per handoff; ISIMIP3-basis caveat noted; obs-fit printed for
             comparison — sub-decision B]

Transient arms:
  ANCH (the interesting one): (kappa_b, nu_b) solved so the block ODE's
       50%-response times under constant amp_b*{1.5, 3.0} forcing reproduce
       the block's GlacierMIP3 tau50 values (mass-weighted member composite).
       The hindcast is then an OUT-OF-SAMPLE TEST: only (sigma, rho[, delta])
       are fitted.
  FREE (extB3-style fallback): kappa_b free (log-prior centered 1/tau50_b),
       shared nu ~ N(1.0, 0.5) [sub-decision C], sigma, rho[, delta] fitted.
  MID  (POST-HOC diagnostic, NOT in the pre-registered handoff menu — added
       after the first D1 pass showed ANCH fails on the century integral while
       FREE rails nu->0): kappa_b FREE (same log-prior as FREE), nu_b FIXED at
       the ANCH-solved values. Isolates whether the response-time KAPPA anchor
       or the nu-spread mechanism carries the residual flow deficit. Reported
       separately; the pre-registered verdict counts ANCH/FREE only.

Likelihood variants (both run; sub-decision F):
  sx2 : pre-1940 flow-target sigma x2 (extB3b/c standing convention)
  t5d : sigma x1 + fitted 1900-1960 rate-bias term delta on the
        Marzeion-2015-derived segment, prior N(0, T5D_DELTA_PRIOR_MM_YR)
        (Roe 2021 initialization-artifact critique; obs_corr(t) =
        obs(t) + delta*(1960-t), levels anchored unchanged >= 1960)

Pre-registered criteria (handoff §3.3, T1 standard, ADOPTED scope-corrected
anchors): 4 aggregate gates (A2 inventory |z|<1; S(1900) 10-30 mm; aggregate
ladder inside likely bands; SSP126-585 spread @2100 in 4.5-13.5 cm) AND
1980-2023 flow logL within FLOW_TOL=5 of the pathological free-single-N
optimum (recomputed in-script per likelihood variant; T1 sx2 value 52.82).
Failure signature (§3.4): ANCH misses flow by >>5 AND FREE passes only by
block collapse (kappa_s -> kappa_f, spread dying) = the P2 signature.

Reports (not gates): per-block modern-rate split vs GlaMBIE block sums;
per-block ladder vs the block's own composite; block S(1900) shares.
Sanity battery: blocks-sum identity vs single-N at matched params; nu=0
linear-relaxation nesting; driver-swap control (aggregate T_glac on the same
structure — the D0 Gobs lesson).

Outputs: outputs/d1_multireservoir_cell.csv,
         outputs/d1_multireservoir_blocks.csv (block anchor table),
         figures/d1_multireservoir_cell.png,
         outputs/d1_gmip3_steady_cache.nc (nc steady-state cache),
         outputs/d1_block_ladder_cache.csv (per-regionset LOWESS cache)
"""
import os
import subprocess
import zipfile

import numpy as np
import pandas as pd
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import brentq, minimize
from scipy.stats import norm

np.seterr(over="ignore", under="ignore")   # logistic bound-transform saturates by design

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
SHOOTOUT = os.path.join(REPO, "python/d0_glacier_shootout.py")

src = open(SHOOTOUT).read().split(
    "# ------------------------------------------------------------------ run all cells")[0]
exec(src.replace('print(f"D0', 'pass # print(f"D0'))

# NB: the exec rebinds OUT_CSV/OUT_FIG to the shootout's paths — set ours AFTER it
OUT_CSV = os.path.join(REPO, "outputs/d1_multireservoir_cell.csv")
OUT_BLOCKS = os.path.join(REPO, "outputs/d1_multireservoir_blocks.csv")
OUT_FIG = os.path.join(REPO, "figures/d1_multireservoir_cell.png")
CACHE_NC = os.path.join(REPO, "outputs/d1_gmip3_steady_cache.nc")
CACHE_LADDER = os.path.join(REPO, "outputs/d1_block_ladder_cache.csv")
REGIONS_CSV = os.path.join(REPO, "outputs/diag_constraint_anatomy_regions.csv")
TGLAC_REG = os.path.join(REPO, "data/observations/t_glac_regions_hadcrut5.csv")
GLAMBIE_ZIP = os.path.join(REPO, "data/observations/raw/glambie_data.zip")
GMIP3_DIR = os.path.join(REPO, "data/observations/raw/gmip3")
NC_SHIFTED = os.path.join(
    GMIP3_DIR, "GMIP3_reg_glacier_model_data",
    "all_shifted_glacierMIP3_Feb12_2024_models_all_rgi_regions_sum_scaled_"
    "extended_repeat_last_101yrs_via_5yravg.nc")
REGCHAR_CSV = os.path.join(GMIP3_DIR,
                           "3_shift_summary_region_characteristicsFeb12_2024.csv")
TEMP_CSV = os.path.join(GMIP3_DIR, "climate_input_data/temp_ch_ipcc_ar6_isimip3b.csv")

COMMIT = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True).stdout.strip()

# ---------------------------------------------------------------- D1 constants
TAU_STAR_DEFAULT = 250          # yr; block threshold on tau50@~1.5C (sub-dec A)
TAU_STAR_SCAN = [200, 250, 300]
AMP_G = 1.8                     # aggregate calibrator convention (control rows)
EARLY_SIGMA_X2_BEFORE = 1940    # sx2 variant (extB3b/c standing)
T5D_SEG_END = 1960              # t5d variant: bias on the Marzeion-derived segment
T5D_DELTA_PRIOR_MM_YR = 0.30    # prior sd for the 1900-1960 rate bias (Roe 2021
                                #  critique scale: allows ~1/3 of the 0.9 mm/yr
                                #  early rate to be initialization artifact)
FLOW_WIN = (1980, 2023)         # criterion window (T1 standard)
FLOW_TOL = 5.0
RATE_WIN = (2015, 2023)
ERAS = [(1900, 1919), (1920, 1949), (1950, 1979), (1980, 1999), (2000, 2023)]
GLAMBIE_AREA_YEAR = 2000.0      # driver weights = glacier_area at this start_date
GLAMBIE_RATE_WIN = (2000.0, 2024.0)   # block modern-rate term window (start_dates)
GLAMBIE_S2020_WIN = (2000.0, 2020.0)  # block melt increment for S2020_b
GLAMBIE_ERR_INFLATE = 1.5       # correlated-error conservatism on the rate sd
GT_PER_MM_SLE = 361.8
S2000_OBS, S2020_OBS = 0.093, 0.107   # aggregate melt-to-date (d0_final convention)
HIST_SLOW_SHARE_SCAN = [0.25, None, 0.50]   # None -> Hugonnet melt-share default (H)
NU_SHARED_PRIOR = (1.0, 0.5)    # FREE arm shared nu (extB3 prior)
NU_BOUNDS_FREE = (0.0, 2.5)
KAPPA_BOUNDS_FREE = (1e-5, 0.5)
KAPPA_LOGPRIOR_SD = 1.5         # FREE arm: log kappa_b ~ N(log(1/tau50_b), 1.5)
DELTA_BOUNDS_MM_YR = (-1.2, 1.2)
TAU_SOLVE_HORIZON = 6000        # yr, constant-forcing integration for tau50
TAU_MATCH_TOL = 0.02            # relative tolerance on achieved vs target tau50
STEADY_YEARS = (4900, 5000)     # T2 steady-state slice
GLACIER_MODELS_8 = ["PyGEM-OGGM_v13", "GloGEMflow", "GloGEMflow3D", "OGGM_v16",
                    "GLIMB", "Kraaijenbrink", "GO", "CISM2"]
FRAC_GRID = np.arange(0.10, 1.00, 0.01)
NUM_FITS_SEL, NUM_FITS_FINAL, ROBUST_ITERS = 300, 1000, 2   # reduced vs T2 (anchor
LADDER_QS = [0.17, 0.5, 0.83]                               #  precision, not paper-grade)
EVAL_STEP = 0.05
LADDER_RUNGS_SOLVE = (1.2, 2.0)         # the two-rung (b_b, T_off_b) solve
N_STARTS_FREE = 8
N_STARTS_ANCH = 4
SEED_D1 = 2026
rng_d1 = np.random.default_rng(SEED_D1)

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
    glambie = {}
    for regi, n in cal_names.items():
        df = pd.read_csv(z.open(n))
        glambie[f"{regi:02d}"] = df

area_w = {r: float(g.loc[np.isclose(g["start_dates"], GLAMBIE_AREA_YEAR),
                         "glacier_area"].iloc[0]) for r, g in glambie.items()}


def glambie_block_stats(members):
    """(rate 2000-23 mm SLE/yr, rate sd, cumulative 2000-2020 m SLE) for a block."""
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
    rate = tot_gt / GT_PER_MM_SLE / ny                       # mm SLE/yr
    rate_sd = np.sqrt(var_gt) / GT_PER_MM_SLE / ny * GLAMBIE_ERR_INFLATE
    return rate, rate_sd, cum20_gt / GT_PER_MM_SLE / 1000.0  # m SLE


# ---------------------------------------------------------------- GMIP3 steady cache
import xarray as xr

if os.path.exists(CACHE_NC):
    cache = xr.open_dataset(CACHE_NC)
    med_steady = cache["med"].load()
    vol_members = cache["vol_global"].load()
    GLOBAL_MODELS = list(cache.attrs["global_models"].split(";"))
    cache.close()
else:
    print(f"  building GMIP3 steady-state cache from {os.path.basename(NC_SHIFTED)} ...")
    ds = xr.open_dataset(NC_SHIFTED)
    use_models = [m for m in GLACIER_MODELS_8 if str(m) in
                  [str(x) for x in ds.model_author.values]]
    vol = (ds["volume_m3"].sel(model_author=use_models)
           .sel(year_after_2020=slice(*STEADY_YEARS)).mean("year_after_2020").load())
    ds.close()
    med_steady = vol.median("model_author", skipna=True)
    _cov = vol.notnull().sum(["gcm", "period_scenario"])
    _nexp = vol.notnull().any("rgi_reg").sum(["gcm", "period_scenario"])
    GLOBAL_MODELS = [str(m) for m in vol.model_author.values
                     if bool((_cov.sel(model_author=m) >=
                              0.5 * _nexp.sel(model_author=m)).all())]
    vol_members = vol.sel(model_author=GLOBAL_MODELS)
    xr.Dataset(dict(med=med_steady, vol_global=vol_members),
               attrs=dict(global_models=";".join(GLOBAL_MODELS),
                          steady_years=str(STEADY_YEARS), commit=COMMIT)
               ).to_netcdf(CACHE_NC)

v2020 = {f"{int(r):02d}": v for r, v in
         zip(regchar["rgi_reg"], regchar["regional_volume_m3_2020_via_5yravg"])}
temp = pd.read_csv(TEMP_CSV, index_col=0)
tcol = [c for c in temp.columns if c.startswith("temp_ch")][0]
temp["key"] = temp["gcm"].astype(str) + "_" + temp["period_scenario"].astype(str)
temp_by_key = temp.set_index("key")[tcol]

from moepy import lowess as moepy_lowess


def _fit_median_lowess(x, y, qs):
    """T2's frac auto-selection + final quantile LOWESS (reduced num_fits)."""
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
    """Committed % of block 2020 mass at the gate rungs, exact per-experiment
    composite (central = model-median pipeline; bands = per-member pipeline)."""
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


# ---------------------------------------------------------------- block builder
GTSHARE = (regs.mass_gt / regs.mass_gt.sum()).to_dict()          # sub-dec D default
MELT_SHARE = regs.melt_share.to_dict()                           # Hugonnet 2000-19


def build_blocks(tau_star, hist_slow_share=None):
    slow = [r for r in regs.index if regs.loc[r, "resp_time_15C_yr"] >= tau_star]
    fast = [r for r in regs.index if r not in slow]
    blocks = {}
    melt_slow = sum(MELT_SHARE[r] for r in slow)
    s_slow = melt_slow if hist_slow_share is None else hist_slow_share
    for name, members in [("SLOW", slow), ("FAST", fast)]:
        wsum = sum(area_w[r] for r in members)
        w = {r: area_w[r] / wsum for r in members}
        drv = sum(w[r] * treg[f"r{r}"] for r in members).dropna()
        drv = drv - drv.loc[1850:1900].mean()
        amp_b = float(np.average([regchar.loc[r, AMP_RATIO_COL] for r in members],
                                 weights=[area_w[r] for r in members]))
        msum = regs.loc[members, "mass_gt"]
        tau15 = float(np.average(regs.loc[members, "resp_time_15C_yr"], weights=msum))
        tau30 = float(np.average(regs.loc[members, "resp_time_30C_yr"], weights=msum))
        rate, rate_sd, cum20 = glambie_block_stats(members)
        gtshare = sum(GTSHARE[r] for r in members)
        s2000 = (s_slow if name == "SLOW" else 1 - s_slow) * S2000_OBS
        com, bands = block_ladder(members)
        a_b = gtshare * INV_V + s2000
        s2020 = s2000 + cum20
        # closed-form two-rung solve for (b_b, T_off_b)
        L1, L2 = LADDER_RUNGS_SOLVE
        S1 = s2020 + com[L1] / 100 * (a_b - s2020)
        S2 = s2020 + com[L2] / 100 * (a_b - s2020)
        T1, T2 = amp_b * L1, amp_b * L2
        b_b = (np.log(1 - S1 / a_b) - np.log(1 - S2 / a_b)) / (T2 - T1)
        T_off_b = T1 + np.log(1 - S1 / a_b) / b_b
        blocks[name] = dict(
            name=name, members=members, w=w, driver_obs=drv, amp_b=amp_b,
            tau15=tau15, tau30=tau30, glambie_rate=rate, glambie_rate_sd=rate_sd,
            glambie_cum20=cum20, gtshare=gtshare, a=a_b, b=b_b, T_off=T_off_b,
            S2000_data=s2000, S2020_data=s2020, com=com, com_bands=bands,
            hist_slow_share=s_slow)
    return blocks


# ---------------------------------------------------------------- anchored transient
def tau50_of(block, kappa, nu, level):
    """Years to lose 50% of committed loss under constant amp_b*level forcing,
    starting from the block's DATA S2020 (GlacierMIP3 response-time defn)."""
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
    """(kappa_b, nu_b) from the block's two response times (tau15 @1.5, tau30 @3.0)."""
    def kappa_for(nu):
        f = lambda lk: tau50_of(block, np.exp(lk), nu, 1.5) - block["tau15"]
        lo, hi = np.log(1e-7), np.log(20.0)
        if f(lo) < 0 or f(hi) > 0:                 # unbracketable
            return None
        return np.exp(brentq(f, lo, hi, xtol=1e-10))

    def g(nu):
        k = kappa_for(nu)
        if k is None:
            return np.nan
        return tau50_of(block, k, nu, 3.0) - block["tau30"]

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
        kap = kappa_for(nu)
        exact = True
    else:                                           # fall back: best log-sq error
        def loss(v):
            k = kappa_for(v[0])
            if k is None:
                return np.inf
            t30 = tau50_of(block, k, v[0], 3.0)
            return np.log(t30 / block["tau30"]) ** 2
        best = min((minimize(loss, [v0], method="Nelder-Mead")
                    for v0 in [0.5, 1.0, 2.0]), key=lambda r: r.fun)
        nu = float(np.clip(best.x[0], 0.0, 4.0))
        kap = kappa_for(nu)
        exact = False
    t15 = tau50_of(block, kap, nu, 1.5)
    t30 = tau50_of(block, kap, nu, 3.0)
    return dict(kappa=kap, nu=nu, tau15_ach=t15, tau30_ach=t30, exact=exact,
                match_ok=(abs(t15 / block["tau15"] - 1) < TAU_MATCH_TOL
                          and abs(t30 / block["tau30"] - 1) < TAU_MATCH_TOL))


# ---------------------------------------------------------------- forward model
def block_driver_hind(block, control_global=False):
    if control_global:
        return extend_obs(tglac_obs, fair_rb, AMP_G).to_numpy()[:-1]
    return extend_obs(block["driver_obs"], fair_rb, block["amp_b"]).to_numpy()[:-1]


def forward_blocks(blocks, th, control_global=False, drivers=None):
    """Sum of per-block Nauels-nu integrations on the model window."""
    tot = np.zeros(len(years))
    per = {}
    for name, blk in blocks.items():
        Tarr_b = (drivers[name] if drivers is not None
                  else block_driver_hind(blk, control_global))
        s = integrate_N(Tarr_b, blk["a"], blk["b"], blk["T_off"],
                        th[f"kappa_{name}"], th[f"nu_{name}"])
        per[name] = s
        tot = tot + s
    return tot, per


def obs_corrected(delta_mm_yr):
    """t5d: rate-bias delta on the 1900-1960 Marzeion-derived segment;
    levels at years >= T5D_SEG_END unchanged (cm units: mm/yr * yr / 10)."""
    corr = np.where(fit_years < T5D_SEG_END,
                    delta_mm_yr * (T5D_SEG_END - fit_years) / 10.0, 0.0)
    return obs + corr


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
VARIANTS = {"sx2": dict(eps_vec=eps_sx2, has_delta=False),
            "t5d": dict(eps_vec=eps, has_delta=True)}


def loglik_blocks(blocks, th, variant, arm, control_global=False):
    v = VARIANTS[variant]
    obs_vec = obs_corrected(th["delta"]) if v["has_delta"] else obs
    s_raw, per = forward_blocks(blocks, th, control_global)
    m_cm = 100 * (s_raw - s_raw[ybase].mean())
    ll_flow = flow_logl_window(m_cm, obs_vec, v["eps_vec"], th["sigma"], th["rho"],
                               fit_years[0], fit_years[-1])
    if not np.isfinite(ll_flow):
        return None
    a_tot = sum(b["a"] for b in blocks.values())
    ll_inv = norm.logpdf(a_tot - s_raw[i_inv], INV_V, INV_SIG)
    ll_lec = norm.logpdf(s_raw[i1900], LEC_MU, LEC_SIG)
    ll_blk = 0.0
    ir0, ir1 = np.searchsorted(years, 2000), np.searchsorted(years, 2024)
    for name, blk in blocks.items():
        mrate = 1000 * (per[name][ir1] - per[name][ir0]) / (ir1 - ir0)
        if arm in ("FREE", "MID"):
            ll_blk += norm.logpdf(mrate, blk["glambie_rate"], blk["glambie_rate_sd"])
    ll_pr = 0.0
    if arm in ("FREE", "MID"):
        for name, blk in blocks.items():
            ll_pr += norm.logpdf(np.log(th[f"kappa_{name}"]),
                                 np.log(1.0 / blk["tau15"]), KAPPA_LOGPRIOR_SD)
    if arm == "FREE":
        ll_pr += norm.logpdf(th["nu_SLOW"], *NU_SHARED_PRIOR)   # shared nu
    if v["has_delta"]:
        ll_pr += norm.logpdf(th["delta"], 0.0, T5D_DELTA_PRIOR_MM_YR)
    return dict(ll_flow=ll_flow, ll_inv=ll_inv, ll_lec=ll_lec, ll_blk=ll_blk,
                ll_prior=ll_pr, logJ=ll_flow + ll_inv + ll_lec + ll_blk + ll_pr,
                s_raw=s_raw, per=per, m_cm=m_cm, obs_vec=obs_vec)


# ---------------------------------------------------------------- optimizers
D1_BOUNDS = dict(sigma=BOUNDS["sigma"], rho=BOUNDS["rho"],
                 kappa_SLOW=KAPPA_BOUNDS_FREE, kappa_FAST=KAPPA_BOUNDS_FREE,
                 nu_shared=NU_BOUNDS_FREE,
                 delta=(DELTA_BOUNDS_MM_YR[0], DELTA_BOUNDS_MM_YR[1]))


def optimize_arm(blocks, variant, arm, anchored=None, control_global=False,
                 nstart=None):
    """ANCH: free (sigma, rho[, delta]); FREE: + kappa_SLOW/FAST + shared nu."""
    v = VARIANTS[variant]
    free = ["sigma", "rho"] + (["delta"] if v["has_delta"] else [])
    if arm == "FREE":
        free = ["kappa_SLOW", "kappa_FAST", "nu_shared"] + free
    elif arm == "MID":
        free = ["kappa_SLOW", "kappa_FAST"] + free
    nstart = nstart or (N_STARTS_ANCH if arm == "ANCH" else N_STARTS_FREE)

    def mk(z):
        th = {}
        for nm, zz in zip(free, z):
            lo, hi = D1_BOUNDS[nm]
            th[nm] = lo + (hi - lo) / (1 + np.exp(-zz))
        if arm == "ANCH":
            for name in blocks:
                th[f"kappa_{name}"] = anchored[name]["kappa"]
                th[f"nu_{name}"] = anchored[name]["nu"]
        elif arm == "MID":
            for name in blocks:
                th[f"nu_{name}"] = anchored[name]["nu"]
        else:
            th["nu_SLOW"] = th["nu_FAST"] = th.pop("nu_shared")
        th.setdefault("delta", 0.0)
        return th

    def neg(z):
        t = loglik_blocks(blocks, mk(z), variant, arm, control_global)
        return np.inf if t is None else -t["logJ"]

    seeds = []
    base = dict(sigma=0.03, rho=0.6, delta=0.0)
    if arm == "FREE":
        for ks, kf, nu in [(1.0 / blocks["SLOW"]["tau15"], 1.0 / blocks["FAST"]["tau15"], 1.0),
                           (0.003, 0.02, 0.5), (0.0005, 0.008, 1.5)]:
            seeds.append(dict(base, kappa_SLOW=ks, kappa_FAST=kf, nu_shared=nu))
    elif arm == "MID":
        for ks, kf in [(anchored["SLOW"]["kappa"], anchored["FAST"]["kappa"]),
                       (0.003, 0.02), (0.01, 0.05)]:
            seeds.append(dict(base, kappa_SLOW=ks, kappa_FAST=kf))
    else:
        seeds.append(dict(base))
        seeds.append(dict(base, sigma=0.02, rho=0.3))
    starts = []
    for sd in seeds:
        z = []
        for nm in free:
            lo, hi = D1_BOUNDS[nm]
            x = np.clip((sd[nm] - lo) / (hi - lo), 1e-4, 1 - 1e-4)
            z.append(np.log(x / (1 - x)))
        starts.append(np.array(z))
    b0 = list(starts)
    while len(starts) < nstart:
        starts.append(b0[rng_d1.integers(len(b0))] + rng_d1.normal(0, 0.6, len(free)))
    best = None
    for z0 in starts:
        r = minimize(neg, z0, method="Nelder-Mead",
                     options=dict(xatol=1e-7, fatol=1e-9, maxiter=6000, maxfev=9000))
        if best is None or r.fun < best.fun:
            best = r
    r = minimize(neg, best.x, method="Nelder-Mead",
                 options=dict(xatol=1e-8, fatol=1e-10, maxiter=6000, maxfev=9000))
    return mk((r if r.fun < best.fun else best).x)


# pathological reference: FREE single-N (a/b/T_off free) on the aggregate
# driver, per likelihood variant — the T1 machinery, sx2 reference 52.82
Tarr_agg = extend_obs(tglac_obs, fair_rb, AMP_G).to_numpy()[:-1]
PATHO_FREE = ["a", "b", "T_off", "kappa", "nu", "sigma", "rho"]


def optimize_patho(variant):
    v = VARIANTS[variant]
    free = PATHO_FREE + (["delta"] if v["has_delta"] else [])
    pb = dict(BOUNDS, delta=D1_BOUNDS["delta"])

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
        m_cm = 100 * (s_raw - s_raw[ybase].mean())
        obs_vec = obs_corrected(th["delta"]) if v["has_delta"] else obs
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
                  sigma=0.005, rho=0.05, delta=0.0),
             dict(a=0.33, b=0.35, T_off=-1.8, kappa=0.006, nu=0.12,
                  sigma=0.01, rho=0.3, delta=0.0),
             dict(a=0.45, b=0.52, T_off=-1.10, kappa=0.0106, nu=0.15,
                  sigma=0.04, rho=0.70, delta=0.0)]
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
                     options=dict(xatol=1e-7, fatol=1e-9, maxiter=8000, maxfev=12000))
        if best is None or r.fun < best.fun:
            best = r
    th = mk(best.x)
    s_raw = integrate_N(Tarr_agg, th["a"], th["b"], th["T_off"], th["kappa"], th["nu"])
    m_cm = 100 * (s_raw - s_raw[ybase].mean())
    obs_vec = obs_corrected(th["delta"]) if v["has_delta"] else obs
    fw = flow_logl_window(m_cm, obs_vec, v["eps_vec"], th["sigma"], th["rho"],
                          FLOW_WIN[0], FLOW_WIN[1])
    return th, fw


# ---------------------------------------------------------------- metrics
def metrics(blocks, th, variant, arm, patho_fw, control_global=False, label=""):
    t = loglik_blocks(blocks, th, variant, arm, control_global)
    if t is None:
        return None
    s, per = t["s_raw"], t["per"]
    v = VARIANTS[variant]
    # aggregate ladder at per-block amp_b (model S2020 in the denominator,
    # matching eval_chain_gates' use of the model state)
    num = {L: 0.0 for L in GMIP3_LEVELS}
    den = 0.0
    sens = 0.0
    com_blk = {}
    for name, blk in blocks.items():
        s20_m = per[name][i2020]
        den += blk["a"] - s20_m
        cb = {}
        for L in GMIP3_LEVELS:
            seq = blk["a"] * (1 - np.exp(-blk["b"] * (blk["amp_b"] * L - blk["T_off"])))
            num[L] += seq - s20_m
            cb[L] = 100 * (seq - s20_m) / max(blk["a"] - s20_m, 1e-9)
        com_blk[name] = cb
        sens += 1000 * (blk["a"] * (1 - np.exp(-blk["b"] * (blk["amp_b"] * 3.0 - blk["T_off"])))
                        - blk["a"] * (1 - np.exp(-blk["b"] * (blk["amp_b"] * 1.5 - blk["T_off"]))))
    com_agg = {L: 100 * num[L] / max(den, 1e-9) for L in GMIP3_LEVELS}
    # scenario spread @2100, per-block amp_b splices (control: aggregate driver)
    proj_years = np.arange(Y0, 2151)
    ds = {}
    for sname, g in ssp_rb.items():
        drvs = {}
        for name, blk in blocks.items():
            if control_global:
                drvs[name] = extend_obs(tglac_obs, g, AMP_G,
                                        idx=proj_years).to_numpy()[:-1]
            else:
                drvs[name] = extend_obs(blk["driver_obs"], g, blk["amp_b"],
                                        idx=proj_years).to_numpy()[:-1]
        stot = np.zeros(len(proj_years))
        for name, blk in blocks.items():
            stot += integrate_N(drvs[name], blk["a"], blk["b"], blk["T_off"],
                                th[f"kappa_{name}"], th[f"nu_{name}"],
                                n=len(proj_years))
        sb = (proj_years >= PROJ_BASE[0]) & (proj_years <= PROJ_BASE[1])
        ds[sname] = 100 * (stot[proj_years == 2100][0] - stot[sb].mean())
    spread = ds["ssp585"] - ds["ssp126"]
    s1900 = 1000 * s[i1900]
    a_tot = sum(b["a"] for b in blocks.values())
    invz = (a_tot - s[i_inv] - INV_V) / INV_SIG
    fw = flow_logl_window(t["m_cm"], t["obs_vec"], v["eps_vec"], th["sigma"],
                          th["rho"], FLOW_WIN[0], FLOW_WIN[1])
    era_ll = {f"flow_{a}_{b}": flow_logl_window(t["m_cm"], t["obs_vec"], v["eps_vec"],
                                                th["sigma"], th["rho"], a, b)
              for a, b in ERAS}
    ir0, ir1 = np.searchsorted(years, RATE_WIN[0]), np.searchsorted(years, RATE_WIN[1])
    rate_modern = 1000 * (s[ir1] - s[ir0]) / (RATE_WIN[1] - RATE_WIN[0])
    i00, i24 = np.searchsorted(years, 2000), np.searchsorted(years, 2024)
    blk_rates = {name: 1000 * (per[name][i24] - per[name][i00]) / (i24 - i00)
                 for name in blocks}
    gates = dict(g_inv=abs(invz) < 1,
                 g_s1900=S1900_GATE_MM[0] <= s1900 <= S1900_GATE_MM[1],
                 g_lad=all(GMIP3_LIKELY[L][0] <= com_agg[L] <= GMIP3_LIKELY[L][1]
                           for L in GMIP3_LEVELS),
                 g_spread=4.5 <= spread <= 13.5)
    row = dict(label=label, arm=arm, variant=variant,
               control="global" if control_global else "perblock",
               tau_star=blocks["SLOW"].get("tau_star", np.nan),
               hist_slow_share=blocks["SLOW"]["hist_slow_share"],
               kappa_SLOW=th["kappa_SLOW"], kappa_FAST=th["kappa_FAST"],
               nu_SLOW=th["nu_SLOW"], nu_FAST=th["nu_FAST"],
               kappa_ratio=th["kappa_FAST"] / th["kappa_SLOW"],
               sigma=th["sigma"], rho=th["rho"], delta=th.get("delta", 0.0),
               logJ=t["logJ"], ll_flow=t["ll_flow"], ll_blk=t["ll_blk"],
               flow_win=fw, flow_win_deficit=patho_fw - fw,
               rate_modern_mm_yr=rate_modern,
               rate_SLOW=blk_rates["SLOW"], rate_FAST=blk_rates["FAST"],
               glambie_SLOW=blocks["SLOW"]["glambie_rate"],
               glambie_FAST=blocks["FAST"]["glambie_rate"],
               S1900_mm=s1900,
               S1900_share_SLOW=per["SLOW"][i1900] / max(s[i1900], 1e-12),
               inv_z=invz, S2020_mm=1000 * s[i2020],
               **{f"com{str(L).replace('.', 'p')}": com_agg[L] for L in GMIP3_LEVELS},
               **{f"comS{str(L).replace('.', 'p')}": com_blk["SLOW"][L]
                  for L in GMIP3_LEVELS},
               **{f"comF{str(L).replace('.', 'p')}": com_blk["FAST"][L]
                  for L in GMIP3_LEVELS},
               sens_mm=sens, ds126=ds["ssp126"], ds245=ds["ssp245"],
               ds585=ds["ssp585"], spread=spread, **era_ll, **gates,
               npass=sum(gates.values()),
               feasible=(sum(gates.values()) == 4 and (patho_fw - fw) <= FLOW_TOL))
    return row, per, t


# ---------------------------------------------------------------- sanity battery
def sanity_battery(blocks):
    print("\n== sanity battery (climate-modeling skill) ==")
    # 1. blocks-sum identity: equal (b, T_off, kappa, nu) + same driver on both
    #    blocks must equal single-N with a = sum a_b (exact scaling property)
    bs, bf = blocks["SLOW"], blocks["FAST"]
    a_tot = bs["a"] + bf["a"]
    shared = dict(b=0.45, T_off=-0.9, kappa=0.006, nu=1.0)
    Tarr_c = Tarr_agg
    s_single = integrate_N(Tarr_c, a_tot, shared["b"], shared["T_off"],
                           shared["kappa"], shared["nu"])
    s_sum = (integrate_N(Tarr_c, bs["a"], shared["b"], shared["T_off"],
                         shared["kappa"], shared["nu"])
             + integrate_N(Tarr_c, bf["a"], shared["b"], shared["T_off"],
                           shared["kappa"], shared["nu"]))
    err1 = np.max(np.abs(s_sum - s_single))
    ok1 = err1 < 1e-12
    print(f"  [1] blocks-sum identity vs single-N: max|diff| = {err1:.2e} "
          f"{'PASS' if ok1 else 'FAIL'}")
    # 2. nu=0 nesting: block ODE with nu=0 == Mengel single-tau linear relaxation
    #    (exc^0 = 1 even at exc=0, so the relaxation is two-way, kappa=1/tau)
    kap = 0.01
    s_nu0 = integrate_N(Tarr_c, bs["a"], bs["b"], bs["T_off"], kap, 0.0)
    S = 0.0
    s_lin = [0.0]
    for k in range(len(Tarr_c)):
        seq = bs["a"] * (1 - np.exp(-bs["b"] * (Tarr_c[k] - bs["T_off"])))
        S += min(kap, 1.0) * (seq - S)
        s_lin.append(S)
    err2 = np.max(np.abs(s_nu0 - np.array(s_lin)))
    ok2 = err2 < 1e-12
    print(f"  [2] nu=0 linear-relaxation nesting: max|diff| = {err2:.2e} "
          f"{'PASS' if ok2 else 'FAIL'}")
    # 3. reproducibility: forward model twice, bit-identical
    th0 = dict(kappa_SLOW=0.002, kappa_FAST=0.02, nu_SLOW=1.0, nu_FAST=1.0)
    sa, _ = forward_blocks(blocks, th0)
    sb2, _ = forward_blocks(blocks, th0)
    ok3 = np.array_equal(sa, sb2)
    print(f"  [3] forward-model reproducibility: {'PASS' if ok3 else 'FAIL'}")
    if not (ok1 and ok2 and ok3):
        raise SystemExit("SANITY BATTERY FAILED — do not trust results")


# ---------------------------------------------------------------- run
print(f"D1 multi-reservoir cell | commit={COMMIT} | anchors=ADOPTED scope-corrected "
      f"(com12={GMIP3_CENTRAL[1.2]}%) | tau*={TAU_STAR_DEFAULT} (scan {TAU_STAR_SCAN})")
print(f"  basis: Nauels-nu per block; drivers t_glac_regions_hadcrut5 (GlaMBIE-area "
      f"weights); amp_b regchar {AMP_RATIO_COL} (ISIMIP3 basis);")
print(f"  a_b = S3-Gt-share x V({INV_V}) + hist split (sub-dec H, default Hugonnet "
      f"melt share); (b_b,T_off_b) two-rung exact composite; units m SLE, cm targets")

blocks0 = build_blocks(TAU_STAR_DEFAULT)
for name, blk in blocks0.items():
    blk["tau_star"] = TAU_STAR_DEFAULT
sanity_battery(blocks0)

# block anchor table + anchored transient solve
block_rows = []
anchored0 = {}
print("\n== block anchors (tau*=250 default) ==")
amp_check = float(np.average([regchar.loc[r, AMP_RATIO_COL] for r in regs.index],
                             weights=[area_w[r] for r in regs.index]))
print(f"  amp check: area-wt regchar aggregate = {amp_check:.2f} "
      f"(calibrator amp_g convention = {AMP_G}; obs-fit = {AMP_FIT:.2f}) — "
      f"regchar ratios sit LOW vs both; carried per handoff, flagged")
for name, blk in blocks0.items():
    anch = solve_anchored(blk)
    anchored0[name] = anch
    _gx = gobs.loc[1901:2024].to_numpy()
    _by = blk["driver_obs"].loc[1901:2024].to_numpy()
    obs_amp = float((_gx * _by).sum() / (_gx ** 2).sum())   # through-origin, = AMP_FIT conv.
    print(f"  [{name}] regs={'/'.join(blk['members'])}")
    print(f"    a={blk['a']:.3f} b={blk['b']:.3f} T_off={blk['T_off']:.3f} "
          f"amp_b={blk['amp_b']:.2f} (obs-fit {obs_amp:.2f}) "
          f"S2000={1000 * blk['S2000_data']:.0f}mm S2020={1000 * blk['S2020_data']:.0f}mm")
    print(f"    com@1.2/1.5/2/3K = " + "/".join(f"{blk['com'][L]:.0f}" for L in GMIP3_LEVELS)
          + f" (bands {blk['com_bands'][1.2][0]:.0f}-{blk['com_bands'][1.2][1]:.0f} @1.2)"
          + f" | glambie rate {blk['glambie_rate']:.3f}±{blk['glambie_rate_sd']:.3f} mm/yr")
    print(f"    anchored: kappa={anch['kappa']:.5f} nu={anch['nu']:.2f} "
          f"tau15 {anch['tau15_ach']:.0f}/{blk['tau15']:.0f} "
          f"tau30 {anch['tau30_ach']:.0f}/{blk['tau30']:.0f} "
          f"({'exact' if anch['exact'] else 'FALLBACK'}, "
          f"match_ok={anch['match_ok']})")
    block_rows.append(dict(tau_star=TAU_STAR_DEFAULT, block=name,
                           members="/".join(blk["members"]),
                           a=blk["a"], b=blk["b"], T_off=blk["T_off"],
                           amp_b=blk["amp_b"], amp_obs_fit=obs_amp,
                           S2000_mm=1000 * blk["S2000_data"],
                           S2020_mm=1000 * blk["S2020_data"],
                           tau15=blk["tau15"], tau30=blk["tau30"],
                           kappa_anch=anch["kappa"], nu_anch=anch["nu"],
                           tau15_ach=anch["tau15_ach"], tau30_ach=anch["tau30_ach"],
                           anch_exact=anch["exact"], anch_match_ok=anch["match_ok"],
                           glambie_rate=blk["glambie_rate"],
                           glambie_rate_sd=blk["glambie_rate_sd"],
                           **{f"com{str(L).replace('.', 'p')}": blk["com"][L]
                              for L in GMIP3_LEVELS}))
pd.DataFrame(block_rows).to_csv(OUT_BLOCKS, index=False, float_format="%.5f")

# pathological references per variant
patho = {}
for variant in VARIANTS:
    th_p, fw_p = optimize_patho(variant)
    patho[variant] = fw_p
    print(f"\npathological free-N [{variant}]: a={th_p['a']:.3f} b={th_p['b']:.3f} "
          f"T_off={th_p['T_off']:.3f} kappa={th_p['kappa']:.4f} nu={th_p['nu']:.2f} "
          f"delta={th_p.get('delta', 0.0):+.2f} | flow{FLOW_WIN}={fw_p:.2f}"
          + (" (T1 ref 52.82)" if variant == "sx2" else ""))

rows = []


def run_config(blocks, anchored, variant, arm, control_global=False, label=""):
    th = optimize_arm(blocks, variant, arm, anchored=anchored,
                      control_global=control_global)
    m = metrics(blocks, th, variant, arm, patho[variant],
                control_global=control_global, label=label)
    if m is None:
        print(f"  [{label}] DEGENERATE (non-finite likelihood)")
        return None
    row, per, t = m
    rows.append(row)
    print(f"  [{label:24s}] npass={row['npass']}/4 "
          f"[inv{'+' if row['g_inv'] else '-'} s19{'+' if row['g_s1900'] else '-'} "
          f"lad{'+' if row['g_lad'] else '-'} spr{'+' if row['g_spread'] else '-'}] "
          f"deficit={row['flow_win_deficit']:6.1f} spread={row['spread']:5.1f} "
          f"rate={row['rate_modern_mm_yr']:.2f} "
          f"(S/F {row['rate_SLOW']:.2f}/{row['rate_FAST']:.2f} "
          f"vs glambie {row['glambie_SLOW']:.2f}/{row['glambie_FAST']:.2f}) "
          f"S1900={row['S1900_mm']:.0f}mm"
          + (f" kappa S/F={row['kappa_SLOW']:.5f}/{row['kappa_FAST']:.4f} "
             f"nu={row['nu_SLOW']:.2f}" if arm == "FREE" else "")
          + (f" delta={row['delta']:+.2f}" if VARIANTS[variant]["has_delta"] else ""))
    return row


print("\n== primary runs (tau*=250, default hist split; MID = POST-HOC diagnostic) ==")
for variant in VARIANTS:
    for arm in ["ANCH", "MID", "FREE"]:
        run_config(blocks0, anchored0, variant, arm,
                   label=f"{arm}/{variant}/t250")

print("\n== driver-swap control (aggregate T_glac on the same structure) ==")
for arm in ["ANCH", "FREE"]:
    run_config(blocks0, anchored0, "sx2", arm, control_global=True,
               label=f"{arm}/sx2/t250/CTRL")

print("\n== tau* scan (distinct partitions only) ==")
seen = {tuple(sorted(blocks0["SLOW"]["members"]))}
for tau_star in TAU_STAR_SCAN:
    b = build_blocks(tau_star)
    key = tuple(sorted(b["SLOW"]["members"]))
    if key in seen:
        print(f"  tau*={tau_star}: same partition as default — skipped")
        continue
    seen.add(key)
    for name, blk in b.items():
        blk["tau_star"] = tau_star
    anch = {name: solve_anchored(blk) for name, blk in b.items()}
    print(f"  tau*={tau_star}: SLOW={'/'.join(b['SLOW']['members'])}")
    for arm in ["ANCH", "FREE"]:
        run_config(b, anch, "sx2", arm, label=f"{arm}/sx2/t{tau_star}")

print("\n== hist-split sensitivity (sub-decision H; tau*=250, sx2) ==")
for s in HIST_SLOW_SHARE_SCAN:
    if s is None:
        continue                                    # default already run
    b = build_blocks(TAU_STAR_DEFAULT, hist_slow_share=s)
    for name, blk in b.items():
        blk["tau_star"] = TAU_STAR_DEFAULT
    anch = {name: solve_anchored(blk) for name, blk in b.items()}
    for arm in ["ANCH", "FREE"]:
        run_config(b, anch, "sx2", arm, label=f"{arm}/sx2/t250/h{s:.2f}")

res = pd.DataFrame(rows)
os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
res.to_csv(OUT_CSV, index=False, float_format="%.5f")

# ---------------------------------------------------------------- verdict
print("\n=== D1 verdict (pre-registered criteria, handoff §3.3/3.4; "
      "MID excluded = post-hoc) ===")
prim = res[(res.control == "perblock") & (res.arm != "MID")]
feas = prim[prim.feasible == True]  # noqa: E712
print(f"  {len(feas)}/{len(prim)} pre-registered configs FEASIBLE "
      f"(4/4 gates AND flow{FLOW_WIN} within {FLOW_TOL} of pathological)")
mid = res[res.arm == "MID"]
for _, r in mid.iterrows():
    print(f"  [post-hoc] {r['label']}: npass={r['npass']} "
          f"deficit={r['flow_win_deficit']:.1f} spread={r['spread']:.1f} "
          f"kappa S/F={r['kappa_SLOW']:.5f}/{r['kappa_FAST']:.4f} "
          f"(anchored {anchored0['SLOW']['kappa']:.5f}/{anchored0['FAST']['kappa']:.4f}) "
          f"feasible={r['feasible']}")
anch_prim = prim[(prim.arm == "ANCH")]
if len(anch_prim):
    ba = anch_prim.sort_values("flow_win_deficit").iloc[0]
    print(f"  ANCH best: {ba['label']} npass={ba['npass']} "
          f"deficit={ba['flow_win_deficit']:.1f} spread={ba['spread']:.1f}")
free_prim = prim[(prim.arm == "FREE")]
if len(free_prim):
    bf = free_prim.sort_values("flow_win_deficit").iloc[0]
    collapse = (0.5 < bf["kappa_ratio"] < 2.0) and (bf["spread"] < 4.5)
    print(f"  FREE best: {bf['label']} npass={bf['npass']} "
          f"deficit={bf['flow_win_deficit']:.1f} spread={bf['spread']:.1f} "
          f"kappa F/S ratio={bf['kappa_ratio']:.1f} "
          f"{'** P2-COLLAPSE SIGNATURE **' if collapse else '(no collapse signature)'}")
if len(feas):
    print("  -> T5a PASSES the offline cell for the feasible configs above.")
else:
    anch_far = (anch_prim["flow_win_deficit"] > 2 * FLOW_TOL).all() if len(anch_prim) else True
    free_collapse_only = all((0.5 < r.kappa_ratio < 2.0) and (r.spread < 4.5)
                             for _, r in free_prim[free_prim.npass == 4].iterrows()) \
        if (free_prim.npass == 4).any() else None
    print(f"  -> NO feasible config. ANCH all-deficits>>tol: {anch_far}; "
          f"FREE 4/4-passers collapse-only: {free_collapse_only} "
          f"(both True = pre-registered T5a offline falsification)")

# ---------------------------------------------------------------- figure
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), constrained_layout=True)
axA, axB, axC = axes
MARK = {"ANCH": "*", "FREE": "o", "MID": "D"}
COLV = {"sx2": "tab:blue", "t5d": "tab:green"}
for _, r in res.iterrows():
    axA.scatter(r["flow_win_deficit"], r["npass"], marker=MARK[r["arm"]],
                s=140 if r["arm"] == "ANCH" else 60,
                color="0.5" if r["control"] == "global" else COLV[r["variant"]],
                alpha=0.9, edgecolors="k", linewidths=0.4)
axA.axvline(FLOW_TOL, color="k", ls=":", lw=1)
axA.axhline(4, color="k", ls=":", lw=1)
axA.set(xlabel=f"flow {FLOW_WIN[0]}-{FLOW_WIN[1]} logL deficit vs pathological",
        ylabel="gates passed (of 4)",
        title="D1 feasibility frontier (upper-left box = pass; T1 pattern)")
hnd = [plt.Line2D([], [], marker=m, ls="", color="k", label=a) for a, m in MARK.items()]
hnd += [plt.Line2D([], [], marker="s", ls="", color=c, label=v) for v, c in COLV.items()]
hnd += [plt.Line2D([], [], marker="s", ls="", color="0.5", label="CTRL (global driver)")]
axA.legend(handles=hnd, fontsize=7)

# best per-block config: block-resolved hindcast flow
best_row = (feas.sort_values("flow_win_deficit").iloc[0] if len(feas)
            else prim.sort_values("flow_win_deficit").iloc[0])
b_best = build_blocks(int(best_row["tau_star"]),
                      hist_slow_share=(None if abs(best_row["hist_slow_share"]
                                                   - blocks0["SLOW"]["hist_slow_share"]) < 1e-9
                                       else best_row["hist_slow_share"]))
th_best = dict(kappa_SLOW=best_row["kappa_SLOW"], kappa_FAST=best_row["kappa_FAST"],
               nu_SLOW=best_row["nu_SLOW"], nu_FAST=best_row["nu_FAST"],
               sigma=best_row["sigma"], rho=best_row["rho"], delta=best_row["delta"])
s_best, per_best = forward_blocks(b_best, th_best)
tgt_cm = pd.Series(obs, index=fit_years)
axB.plot(tgt_cm.index, 10 * tgt_cm.diff().rolling(11, center=True).mean(), color="k",
         lw=1.6, label="obs flow (11-yr mean)")
if VARIANTS[best_row["variant"]]["has_delta"]:
    oc = pd.Series(obs_corrected(best_row["delta"]), index=fit_years)
    axB.plot(oc.index, 10 * oc.diff().rolling(11, center=True).mean(), color="0.5",
             lw=1.0, ls="--", label=f"obs t5d-corrected (delta={best_row['delta']:+.2f})")
axB.plot(years[1:], 1000 * np.diff(s_best), color="tab:red", lw=1.4, label="model total")
axB.plot(years[1:], 1000 * np.diff(per_best["SLOW"]), color="tab:purple", lw=1.1,
         label="SLOW block")
axB.plot(years[1:], 1000 * np.diff(per_best["FAST"]), color="tab:orange", lw=1.1,
         label="FAST block")
axB.set(xlim=(1900, 2026), xlabel="year", ylabel="GSIC flow (mm SLE/yr)",
        title=f"block-resolved hindcast — best config ({best_row['label']})")
axB.legend(fontsize=8)

xs = np.arange(len(GMIP3_LEVELS))
for L, x in zip(GMIP3_LEVELS, xs):
    lo, hi = GMIP3_LIKELY[L]
    axC.fill_between([x - 0.35, x + 0.35], [lo, lo], [hi, hi], color="k", alpha=0.10)
    axC.plot([x - 0.35, x + 0.35], [GMIP3_CENTRAL[L]] * 2, color="k", lw=1.6)
axC.plot(xs, [best_row[f"com{str(L).replace('.', 'p')}"] for L in GMIP3_LEVELS],
         color="tab:red", marker="o", ms=5, lw=1.3, label="aggregate (model)")
axC.plot(xs, [best_row[f"comS{str(L).replace('.', 'p')}"] for L in GMIP3_LEVELS],
         color="tab:purple", marker="^", ms=4, lw=1.0, ls="--", label="SLOW (model)")
axC.plot(xs, [best_row[f"comF{str(L).replace('.', 'p')}"] for L in GMIP3_LEVELS],
         color="tab:orange", marker="v", ms=4, lw=1.0, ls="--", label="FAST (model)")
for name, c in [("SLOW", "tab:purple"), ("FAST", "tab:orange")]:
    axC.scatter(xs, [b_best[name]["com"][L] for L in GMIP3_LEVELS], color=c,
                marker="x", s=40, label=f"{name} composite anchor")
axC.set(xticks=xs, xticklabels=[f"+{L}K" for L in GMIP3_LEVELS],
        ylabel="committed loss, % of 2020 mass",
        title="ladders: aggregate gate (black) + per-block vs own anchors")
axC.legend(fontsize=7)
fig.suptitle(f"D1 multi-reservoir cell — 2 blocks by tau50 (tau*={TAU_STAR_DEFAULT}) | "
             f"ADOPTED anchors | tol {FLOW_TOL} logL | commit {COMMIT}", fontsize=10)
os.makedirs(os.path.dirname(OUT_FIG), exist_ok=True)
fig.savefig(OUT_FIG, dpi=150)
print(f"\nWrote {os.path.relpath(OUT_CSV, REPO)}, {os.path.relpath(OUT_BLOCKS, REPO)}, "
      f"{os.path.relpath(OUT_FIG, REPO)}")
