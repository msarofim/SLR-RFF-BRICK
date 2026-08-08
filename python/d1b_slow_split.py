#!/usr/bin/env python3
"""D1b — SLOW-block split variants (Marcus 2026-08-08, follow-on to D1).

D1 finding: the 2-block SLOW composite {r19,r03,r09,r07,r06} two-rung solve
gives T_off=+0.47 glacier-K (inert until ~1990), yet the block's data-assigned
historical melt is ~33 mm — an internal contradiction. Within the block the
members are heterogeneous in equilibrium proximity: r09/r07/r06 committed@1.2K
= 65/46/61 % (deeply out of equilibrium now -> per-region T_off must be low)
vs r19/r03 = 36/33 % (near equilibrium). One exponential through the composite
is the anatomy-memo aggregation loss reproduced one level down.

Variants (same pre-registered gates + flow criterion as D1, T1 standard):
  A. per-member DIAGNOSTIC: closed-form (b_r, T_off_r) from each SLOW member's
     OWN singleton two-rung composite (diagnostic-grade: fixed LOWESS frac,
     central estimator only) — the direct test of "should not be one block".
  B. D1b-3BLOCK: POLAR {19,03} / SUBPOLAR {09,07,06} / FAST (as D1).
     NB this splits SLOW; the pre-registered 3-block extension in the T5a spec
     split FAST (Arctic-ETCW) — D1's evidence redirects the split.
  C. D1b-REASSIGN: tau*~500 2-block — r09/r07/r06 merged into FAST
     (POLAR {19,03} / FASTX {rest}). Tests Marcus's "reassign" alternative;
     expected weakness: one Nauels pool spanning tau50 104-445 yr.

Arms per variant: ANCH (kappa_b, nu_b solved exactly from the block's two
mass-weighted tau50s; hindcast out-of-sample), MID (kappa free, nu held —
post-hoc-diagnostic class, as in D1), FREE (kappa_b free + shared nu
N(1.0,0.5)). Likelihood variants sx2 / t5d as in D1. Driver-swap control and
hist-split scan SKIPPED (D1 showed ~nil and shallow respectively). Sub-decision
H default (Hugonnet melt shares) carried per block.

Outputs: outputs/d1b_slow_split.csv, outputs/d1b_blocks.csv,
         outputs/d1b_member_twoparam.csv, figures/d1b_slow_split.png.
Caches: reuses outputs/d1_gmip3_steady_cache.nc + d1_block_ladder_cache.csv
        (exact block estimator); singleton diagnostics use a SEPARATE cache
        outputs/d1b_singleton_ladder_cache.csv (different estimator settings).
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
OUT_CSV = os.path.join(REPO, "outputs/d1b_slow_split.csv")
OUT_BLOCKS = os.path.join(REPO, "outputs/d1b_blocks.csv")
OUT_MEMBERS = os.path.join(REPO, "outputs/d1b_member_twoparam.csv")
OUT_FIG = os.path.join(REPO, "figures/d1b_slow_split.png")
CACHE_NC = os.path.join(REPO, "outputs/d1_gmip3_steady_cache.nc")
CACHE_LADDER = os.path.join(REPO, "outputs/d1_block_ladder_cache.csv")
CACHE_SINGLE = os.path.join(REPO, "outputs/d1b_singleton_ladder_cache.csv")
REGIONS_CSV = os.path.join(REPO, "outputs/diag_constraint_anatomy_regions.csv")
TGLAC_REG = os.path.join(REPO, "data/observations/t_glac_regions_hadcrut5.csv")
GLAMBIE_ZIP = os.path.join(REPO, "data/observations/raw/glambie_data.zip")
GMIP3_DIR = os.path.join(REPO, "data/observations/raw/gmip3")
REGCHAR_CSV = os.path.join(GMIP3_DIR,
                           "3_shift_summary_region_characteristicsFeb12_2024.csv")
TEMP_CSV = os.path.join(GMIP3_DIR, "climate_input_data/temp_ch_ipcc_ar6_isimip3b.csv")

COMMIT = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True).stdout.strip()

# ---------------------------------------------------------------- constants (= D1)
AMP_G = 1.8
EARLY_SIGMA_X2_BEFORE = 1940
T5D_SEG_END = 1960
T5D_DELTA_PRIOR_MM_YR = 0.30
FLOW_WIN = (1980, 2023)
FLOW_TOL = 5.0
RATE_WIN = (2015, 2023)
ERAS = [(1900, 1919), (1920, 1949), (1950, 1979), (1980, 1999), (2000, 2023)]
GLAMBIE_AREA_YEAR = 2000.0
GLAMBIE_RATE_WIN = (2000.0, 2024.0)
GLAMBIE_S2020_WIN = (2000.0, 2020.0)
GLAMBIE_ERR_INFLATE = 1.5
GT_PER_MM_SLE = 361.8
S2000_OBS, S2020_OBS = 0.093, 0.107
NU_SHARED_PRIOR = (1.0, 0.5)
NU_BOUNDS_FREE = (0.0, 2.5)
KAPPA_BOUNDS_FREE = (1e-5, 0.5)
KAPPA_LOGPRIOR_SD = 1.5
DELTA_BOUNDS_MM_YR = (-1.2, 1.2)
TAU_SOLVE_HORIZON = 6000
TAU_MATCH_TOL = 0.02
STEADY_YEARS = (4900, 5000)
FRAC_GRID = np.arange(0.10, 1.00, 0.01)
NUM_FITS_SEL, NUM_FITS_FINAL, ROBUST_ITERS = 300, 1000, 2
LADDER_QS = [0.17, 0.5, 0.83]
EVAL_STEP = 0.05
LADDER_RUNGS_SOLVE = (1.2, 2.0)
FRAC_SINGLETON = 0.25          # diagnostic-grade fixed frac (paper 'All' ~0.23)
NUM_FITS_SINGLETON = 500
N_STARTS_FREE = 8
N_STARTS_ANCH = 4
SEED_D1B = 2026
rng_d1 = np.random.default_rng(SEED_D1B)

# block specs (variant B and C) — names must not collide with arm names
SPEC_3BLOCK = {"POLAR": ["19", "03"],
               "SUBPOLAR": ["09", "07", "06"],
               "FAST": ["01", "04", "17", "13", "14", "02", "15", "08",
                        "10", "11", "16", "18", "12"]}
SPEC_REASSIGN = {"POLAR": ["19", "03"],
                 "FASTX": ["09", "07", "06", "01", "04", "17", "13", "14",
                           "02", "15", "08", "10", "11", "16", "18", "12"]}
SLOW_D1 = ["19", "03", "09", "07", "06"]      # the D1 SLOW block (diagnostic set)

# ---------------------------------------------------------------- region data (= D1)
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


# ---------------------------------------------------------------- GMIP3 cache (= D1)
import xarray as xr

assert os.path.exists(CACHE_NC), "run d1_multireservoir_cell.py first (builds the cache)"
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
    """Exact estimator (auto-frac, central + member bands) — shared D1 cache."""
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


_single_cache = (pd.read_csv(CACHE_SINGLE, dtype={"reg": str})
                 if os.path.exists(CACHE_SINGLE) else pd.DataFrame())


def singleton_ladder(reg):
    """Diagnostic-grade: model-median composite, FIXED frac, central only."""
    global _single_cache
    if len(_single_cache) and (_single_cache.reg == reg).any():
        sub = _single_cache[_single_cache.reg == reg].set_index("level_K")
        return {L: float(sub.loc[L, "central"]) for L in GMIP3_LEVELS}
    x, y = _composite_xy([reg], med_steady)
    eval_x = np.arange(np.round(x.min(), 1), x.max() * 1.001, EVAL_STEP)
    df = moepy_lowess.quantile_model(x, y, x_pred=eval_x, frac=FRAC_SINGLETON,
                                     num_fits=NUM_FITS_SINGLETON,
                                     robust_iters=ROBUST_ITERS, qs=[0.5]).clip(lower=0)
    com = {L: 100 - float(np.interp(L, eval_x, df[0.5].to_numpy()))
           for L in GMIP3_LEVELS}
    rows = [dict(reg=reg, level_K=L, central=com[L]) for L in GMIP3_LEVELS]
    _single_cache = pd.concat([_single_cache, pd.DataFrame(rows)], ignore_index=True)
    _single_cache.to_csv(CACHE_SINGLE, index=False, float_format="%.4f")
    return com


# ---------------------------------------------------------------- partitions + solve
GTSHARE = (regs.mass_gt / regs.mass_gt.sum()).to_dict()
MELT_SHARE = regs.melt_share.to_dict()


def two_rung_solve(a_b, s2020, com, amp_b):
    L1, L2 = LADDER_RUNGS_SOLVE
    S1 = s2020 + com[L1] / 100 * (a_b - s2020)
    S2 = s2020 + com[L2] / 100 * (a_b - s2020)
    T1, T2 = amp_b * L1, amp_b * L2
    if not (0 < S1 / a_b < 1 and 0 < S2 / a_b < 1 and S2 > S1):
        return np.nan, np.nan
    b_b = (np.log(1 - S1 / a_b) - np.log(1 - S2 / a_b)) / (T2 - T1)
    T_off_b = T1 + np.log(1 - S1 / a_b) / b_b
    return b_b, T_off_b


def build_block(name, members):
    wsum = sum(area_w[r] for r in members)
    drv = sum(area_w[r] / wsum * treg[f"r{r}"] for r in members).dropna()
    drv = drv - drv.loc[1850:1900].mean()
    amp_b = float(np.average([regchar.loc[r, AMP_RATIO_COL] for r in members],
                             weights=[area_w[r] for r in members]))
    msum = regs.loc[members, "mass_gt"]
    tau15 = float(np.average(regs.loc[members, "resp_time_15C_yr"], weights=msum))
    tau30 = float(np.average(regs.loc[members, "resp_time_30C_yr"], weights=msum))
    rate, rate_sd, cum20 = glambie_block_stats(members)
    gtshare = sum(GTSHARE[r] for r in members)
    s2000 = sum(MELT_SHARE[r] for r in members) * S2000_OBS   # sub-dec H default
    com, bands = block_ladder(members)
    a_b = gtshare * INV_V + s2000
    s2020 = s2000 + cum20
    b_b, T_off_b = two_rung_solve(a_b, s2020, com, amp_b)
    return dict(name=name, members=members, driver_obs=drv, amp_b=amp_b,
                tau15=tau15, tau30=tau30, glambie_rate=rate,
                glambie_rate_sd=rate_sd, glambie_cum20=cum20, gtshare=gtshare,
                a=a_b, b=b_b, T_off=T_off_b, S2000_data=s2000, S2020_data=s2020,
                com=com, com_bands=bands)


def build_spec(spec):
    return {name: build_block(name, members) for name, members in spec.items()}


# ---------------------------------------------------------------- anchored solve (= D1)
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
        kap = kappa_for(nu)
        exact = True
    else:
        def loss(v):
            k = kappa_for(v[0])
            if k is None:
                return np.inf
            return np.log(tau50_of(block, k, v[0], 3.0) / block["tau30"]) ** 2
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


# ---------------------------------------------------------------- forward + likelihood
def forward_blocks(blocks, th):
    tot = np.zeros(len(years))
    per = {}
    for name, blk in blocks.items():
        Tarr_b = extend_obs(blk["driver_obs"], fair_rb, blk["amp_b"]).to_numpy()[:-1]
        s = integrate_N(Tarr_b, blk["a"], blk["b"], blk["T_off"],
                        th[f"kappa_{name}"], th[f"nu_{name}"])
        per[name] = s
        tot = tot + s
    return tot, per


def obs_corrected(delta_mm_yr):
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


def loglik_blocks(blocks, th, variant, arm):
    v = VARIANTS[variant]
    obs_vec = obs_corrected(th["delta"]) if v["has_delta"] else obs
    s_raw, per = forward_blocks(blocks, th)
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
        ll_pr += norm.logpdf(th["nu_shared_val"], *NU_SHARED_PRIOR)
    if v["has_delta"]:
        ll_pr += norm.logpdf(th["delta"], 0.0, T5D_DELTA_PRIOR_MM_YR)
    return dict(ll_flow=ll_flow, ll_inv=ll_inv, ll_lec=ll_lec, ll_blk=ll_blk,
                ll_prior=ll_pr, logJ=ll_flow + ll_inv + ll_lec + ll_blk + ll_pr,
                s_raw=s_raw, per=per, m_cm=m_cm, obs_vec=obs_vec)


def param_bounds(nm):
    if nm.startswith("kappa_"):
        return KAPPA_BOUNDS_FREE
    if nm == "nu_shared":
        return NU_BOUNDS_FREE
    if nm == "delta":
        return DELTA_BOUNDS_MM_YR
    return BOUNDS[nm]


def optimize_arm(blocks, variant, arm, anchored=None):
    v = VARIANTS[variant]
    names = list(blocks)
    free = ["sigma", "rho"] + (["delta"] if v["has_delta"] else [])
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
        t = loglik_blocks(blocks, mk(z), variant, arm)
        return np.inf if t is None else -t["logJ"]

    seeds = []
    base = dict(sigma=0.03, rho=0.6, delta=0.0)
    if arm == "FREE":
        for scale, nu in [(1.0, 1.0), (3.0, 0.5), (0.3, 1.5)]:
            sd = dict(base, nu_shared=nu)
            for n in names:
                sd[f"kappa_{n}"] = scale / blocks[n]["tau15"]
            seeds.append(sd)
    elif arm == "MID":
        for scale in [1.0, 3.0, 10.0]:
            sd = dict(base)
            for n in names:
                sd[f"kappa_{n}"] = min(scale * anchored[n]["kappa"], 0.4)
            seeds.append(sd)
    else:
        seeds.append(dict(base))
        seeds.append(dict(base, sigma=0.02, rho=0.3))
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
                     options=dict(xatol=1e-7, fatol=1e-9, maxiter=8000, maxfev=12000))
        if best is None or r.fun < best.fun:
            best = r
    r = minimize(neg, best.x, method="Nelder-Mead",
                 options=dict(xatol=1e-8, fatol=1e-10, maxiter=8000, maxfev=12000))
    return mk((r if r.fun < best.fun else best).x)


# ---------------------------------------------------------------- pathological (= D1)
Tarr_agg = extend_obs(tglac_obs, fair_rb, AMP_G).to_numpy()[:-1]
PATHO_FREE = ["a", "b", "T_off", "kappa", "nu", "sigma", "rho"]


def optimize_patho(variant):
    v = VARIANTS[variant]
    free = PATHO_FREE + (["delta"] if v["has_delta"] else [])
    pb = dict(BOUNDS, delta=DELTA_BOUNDS_MM_YR)

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
def metrics(blocks, th, variant, arm, patho_fw, label=""):
    t = loglik_blocks(blocks, th, variant, arm)
    if t is None:
        return None
    s, per = t["s_raw"], t["per"]
    v = VARIANTS[variant]
    num = {L: 0.0 for L in GMIP3_LEVELS}
    den = 0.0
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
    com_agg = {L: 100 * num[L] / max(den, 1e-9) for L in GMIP3_LEVELS}
    proj_years = np.arange(Y0, 2151)
    ds = {}
    for sname, g in ssp_rb.items():
        stot = np.zeros(len(proj_years))
        for name, blk in blocks.items():
            drv = extend_obs(blk["driver_obs"], g, blk["amp_b"],
                             idx=proj_years).to_numpy()[:-1]
            stot += integrate_N(drv, blk["a"], blk["b"], blk["T_off"],
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
    kappas = [th[f"kappa_{n}"] for n in blocks]
    gates = dict(g_inv=abs(invz) < 1,
                 g_s1900=S1900_GATE_MM[0] <= s1900 <= S1900_GATE_MM[1],
                 g_lad=all(GMIP3_LIKELY[L][0] <= com_agg[L] <= GMIP3_LIKELY[L][1]
                           for L in GMIP3_LEVELS),
                 g_spread=4.5 <= spread <= 13.5)
    row = dict(label=label, arm=arm, variant=variant, nblocks=len(blocks),
               blocks="+".join(blocks),
               sigma=th["sigma"], rho=th["rho"], delta=th.get("delta", 0.0),
               logJ=t["logJ"], ll_flow=t["ll_flow"], ll_blk=t["ll_blk"],
               flow_win=fw, flow_win_deficit=patho_fw - fw,
               rate_modern_mm_yr=rate_modern,
               kappa_ratio_maxmin=max(kappas) / min(kappas),
               S1900_mm=s1900, inv_z=invz, S2020_mm=1000 * s[i2020],
               **{f"com{str(L).replace('.', 'p')}": com_agg[L] for L in GMIP3_LEVELS},
               ds126=ds["ssp126"], ds245=ds["ssp245"], ds585=ds["ssp585"],
               spread=spread, **era_ll, **gates,
               npass=sum(gates.values()),
               feasible=(sum(gates.values()) == 4 and (patho_fw - fw) <= FLOW_TOL))
    for name in blocks:
        row[f"kappa_{name}"] = th[f"kappa_{name}"]
        row[f"nu_{name}"] = th[f"nu_{name}"]
        row[f"rate00_23_{name}"] = 1000 * (per[name][i24] - per[name][i00]) / (i24 - i00)
        row[f"glambie_{name}"] = blocks[name]["glambie_rate"]
        row[f"S2020_{name}_mm"] = 1000 * per[name][i2020]
    return row, per, t


# ---------------------------------------------------------------- sanity battery
def sanity_battery(blocks):
    print("\n== sanity battery (D1b, 3-block generalization) ==")
    names = list(blocks)
    shared = dict(b=0.45, T_off=-0.9, kappa=0.006, nu=1.0)
    a_tot = sum(blocks[n]["a"] for n in names)
    s_single = integrate_N(Tarr_agg, a_tot, shared["b"], shared["T_off"],
                           shared["kappa"], shared["nu"])
    s_sum = sum(integrate_N(Tarr_agg, blocks[n]["a"], shared["b"], shared["T_off"],
                            shared["kappa"], shared["nu"]) for n in names)
    err1 = np.max(np.abs(s_sum - s_single))
    ok1 = err1 < 1e-12
    print(f"  [1] {len(names)}-blocks-sum identity vs single-N: max|diff| = "
          f"{err1:.2e} {'PASS' if ok1 else 'FAIL'}")
    th0 = {}
    for n in names:
        th0[f"kappa_{n}"] = 0.005
        th0[f"nu_{n}"] = 1.0
    sa, _ = forward_blocks(blocks, th0)
    sb2, _ = forward_blocks(blocks, th0)
    ok2 = np.array_equal(sa, sb2)
    print(f"  [2] forward-model reproducibility: {'PASS' if ok2 else 'FAIL'}")
    if not (ok1 and ok2):
        raise SystemExit("SANITY BATTERY FAILED — do not trust results")


# ---------------------------------------------------------------- run
print(f"D1b SLOW-split variants | commit={COMMIT} | anchors=ADOPTED scope-corrected | "
      f"criteria = D1 pre-registered (4 gates + flow{FLOW_WIN} tol {FLOW_TOL})")
print("  variants: 3BLOCK POLAR/SUBPOLAR/FAST; REASSIGN POLAR/FASTX (tau*~500); "
      "arms ANCH/MID/FREE x sx2/t5d; control + h-scan skipped (D1: nil/shallow)")

# ---- A. per-member two-rung diagnostic (SLOW members; diagnostic-grade frac)
print(f"\n== A. per-member two-rung solve, D1 SLOW members "
      f"(singleton composites, frac={FRAC_SINGLETON} fixed — diagnostic-grade) ==")
mem_rows = []
for r in SLOW_D1:
    com_r = singleton_ladder(r)
    amp_r = float(regchar.loc[r, AMP_RATIO_COL])
    _, _, cum20_r = glambie_block_stats([r])
    s2000_r = MELT_SHARE[r] * S2000_OBS
    a_r = GTSHARE[r] * INV_V + s2000_r
    s2020_r = s2000_r + cum20_r
    b_r, toff_r = two_rung_solve(a_r, s2020_r, com_r, amp_r)
    mem_rows.append(dict(reg=r, a_mm=1000 * a_r, S2020_mm=1000 * s2020_r,
                         amp_b=amp_r, tau15=regs.loc[r, "resp_time_15C_yr"],
                         tau30=regs.loc[r, "resp_time_30C_yr"],
                         com12=com_r[1.2], com15=com_r[1.5], com20=com_r[2.0],
                         com30=com_r[3.0], b=b_r, T_off=toff_r))
    print(f"  r{r}: com@1.2/1.5/2/3 = {com_r[1.2]:5.1f}/{com_r[1.5]:5.1f}/"
          f"{com_r[2.0]:5.1f}/{com_r[3.0]:5.1f} | amp {amp_r:.2f} | "
          f"tau50 {regs.loc[r, 'resp_time_15C_yr']:.0f}/{regs.loc[r, 'resp_time_30C_yr']:.0f}"
          f" -> b={b_r:.3f} T_off={toff_r:+.3f} glac-K")
pd.DataFrame(mem_rows).to_csv(OUT_MEMBERS, index=False, float_format="%.4f")

# ---- build both specs + anchors
all_specs = {"3BLOCK": SPEC_3BLOCK, "REASSIGN": SPEC_REASSIGN}
built, anchors, block_rows = {}, {}, []
for vname, spec in all_specs.items():
    blocks = build_spec(spec)
    built[vname] = blocks
    anchors[vname] = {}
    print(f"\n== block anchors [{vname}] ==")
    for name, blk in blocks.items():
        if not np.isfinite(blk["b"]):
            print(f"  [{name}] TWO-RUNG SOLVE FAILED — check composite")
            continue
        anch = solve_anchored(blk)
        anchors[vname][name] = anch
        print(f"  [{name}] regs={'/'.join(blk['members'])}")
        print(f"    a={blk['a']:.3f} b={blk['b']:.3f} T_off={blk['T_off']:+.3f} "
              f"amp_b={blk['amp_b']:.2f} S2000={1000 * blk['S2000_data']:.0f}mm "
              f"S2020={1000 * blk['S2020_data']:.0f}mm | "
              f"com@1.2/1.5/2/3 = " + "/".join(f"{blk['com'][L]:.0f}"
                                               for L in GMIP3_LEVELS))
        print(f"    glambie {blk['glambie_rate']:.3f}±{blk['glambie_rate_sd']:.3f} mm/yr"
              f" | anchored kappa={anch['kappa']:.5f} nu={anch['nu']:.2f} "
              f"tau {anch['tau15_ach']:.0f}/{blk['tau15']:.0f} + "
              f"{anch['tau30_ach']:.0f}/{blk['tau30']:.0f} "
              f"({'exact' if anch['exact'] else 'FALLBACK'})")
        block_rows.append(dict(variant=vname, block=name,
                               members="/".join(blk["members"]), a=blk["a"],
                               b=blk["b"], T_off=blk["T_off"], amp_b=blk["amp_b"],
                               S2000_mm=1000 * blk["S2000_data"],
                               S2020_mm=1000 * blk["S2020_data"],
                               tau15=blk["tau15"], tau30=blk["tau30"],
                               kappa_anch=anch["kappa"], nu_anch=anch["nu"],
                               anch_exact=anch["exact"],
                               glambie_rate=blk["glambie_rate"],
                               **{f"com{str(L).replace('.', 'p')}": blk["com"][L]
                                  for L in GMIP3_LEVELS}))
pd.DataFrame(block_rows).to_csv(OUT_BLOCKS, index=False, float_format="%.5f")

sanity_battery(built["3BLOCK"])

patho = {}
for variant in VARIANTS:
    th_p, fw_p = optimize_patho(variant)
    patho[variant] = fw_p
    print(f"\npathological free-N [{variant}]: flow{FLOW_WIN}={fw_p:.2f}"
          + (" (T1/D1 ref 52.82)" if variant == "sx2" else " (D1 ref 52.23)"))

rows = []
for vname in all_specs:
    blocks = built[vname]
    print(f"\n== runs [{vname}] ==")
    for variant in VARIANTS:
        for arm in ["ANCH", "MID", "FREE"]:
            th = optimize_arm(blocks, variant, arm, anchored=anchors[vname])
            m = metrics(blocks, th, variant, arm, patho[variant],
                        label=f"{vname}/{arm}/{variant}")
            if m is None:
                print(f"  [{vname}/{arm}/{variant}] DEGENERATE")
                continue
            row, per, t = m
            rows.append(row)
            bl = list(blocks)
            rates = " ".join(f"{n[:4]}:{row[f'rate00_23_{n}']:.2f}"
                             f"/{row[f'glambie_{n}']:.2f}" for n in bl)
            print(f"  [{row['label']:22s}] npass={row['npass']}/4 "
                  f"[inv{'+' if row['g_inv'] else '-'} s19{'+' if row['g_s1900'] else '-'} "
                  f"lad{'+' if row['g_lad'] else '-'} spr{'+' if row['g_spread'] else '-'}] "
                  f"deficit={row['flow_win_deficit']:6.1f} spread={row['spread']:5.1f} "
                  f"S2020={row['S2020_mm']:.0f}mm rate={row['rate_modern_mm_yr']:.2f} "
                  f"| {rates}"
                  + (f" delta={row['delta']:+.2f}" if VARIANTS[variant]["has_delta"] else ""))
            if arm == "ANCH":
                i_e = {e: (np.searchsorted(years, e[0]), np.searchsorted(years, e[1]))
                       for e in ERAS}
                era_str = " ".join(
                    f"{e[0]}s:{1000 * (t['s_raw'][i1] - t['s_raw'][i0]) / (e[1] - e[0]):.2f}"
                    for e, (i0, i1) in i_e.items())
                print(f"      ANCH era rates (mm/yr): {era_str}")

res = pd.DataFrame(rows)
os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
res.to_csv(OUT_CSV, index=False, float_format="%.5f")

# ---------------------------------------------------------------- verdict
print("\n=== D1b verdict (same criteria as D1; D1 2-block references: "
      "ANCH sx2 20.7 / t5d 11.5; MID 20.4/11.9; FREE 15.5/7.7) ===")
feas = res[res.feasible == True]  # noqa: E712
print(f"  {len(feas)}/{len(res)} configs FEASIBLE")
for vname in all_specs:
    sub = res[res.blocks == "+".join(all_specs[vname])]
    if not len(sub):
        continue
    best = sub.sort_values("flow_win_deficit").iloc[0]
    banch = sub[sub.arm == "ANCH"].sort_values("flow_win_deficit")
    print(f"  [{vname}] best: {best['label']} npass={best['npass']} "
          f"deficit={best['flow_win_deficit']:.1f} spread={best['spread']:.1f}"
          + (f" | ANCH best deficit {banch.iloc[0]['flow_win_deficit']:.1f} "
             f"(D1 2-block ANCH {'11.5 t5d' if banch.iloc[0]['variant'] == 't5d' else '20.7 sx2'})"
             if len(banch) else ""))
if len(feas):
    print("  -> FEASIBLE configs exist — the SLOW split changes the D1 verdict.")
else:
    print("  -> still no feasible config; compare deficits above vs D1 to judge "
          "whether the split moves toward feasibility.")

# ---------------------------------------------------------------- figure
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(16.5, 4.8), constrained_layout=True)
axA, axB, axC = axes

MARK = {"ANCH": "*", "FREE": "o", "MID": "D"}
COLS = {"3BLOCK": "tab:green", "REASSIGN": "tab:orange"}
D1_REF = [("ANCH/sx2", 20.7, 4), ("ANCH/t5d", 11.5, 4), ("MID/sx2", 20.4, 4),
          ("MID/t5d", 11.9, 4), ("FREE/sx2", 15.5, 2), ("FREE/t5d", 7.7, 3)]
for lab, d, np_ in D1_REF:
    axA.scatter(d, np_, marker=MARK[lab.split("/")[0]], s=60, color="0.6",
                alpha=0.6, zorder=1)
for _, r in res.iterrows():
    vname = "3BLOCK" if r["blocks"] == "+".join(SPEC_3BLOCK) else "REASSIGN"
    axA.scatter(r["flow_win_deficit"], r["npass"], marker=MARK[r["arm"]],
                s=150 if r["arm"] == "ANCH" else 70, color=COLS[vname],
                edgecolors="k", linewidths=0.4, zorder=2)
axA.axvline(FLOW_TOL, color="k", ls=":", lw=1)
axA.axhline(4, color="k", ls=":", lw=1)
axA.set(xlabel=f"flow {FLOW_WIN[0]}-{FLOW_WIN[1]} logL deficit vs pathological",
        ylabel="gates passed (of 4)",
        title="D1b frontier (grey = D1 2-block references)")
hnd = [plt.Line2D([], [], marker=m, ls="", color="k", label=a) for a, m in MARK.items()]
hnd += [plt.Line2D([], [], marker="s", ls="", color=c, label=v) for v, c in COLS.items()]
axA.legend(handles=hnd, fontsize=7)

mem = pd.DataFrame(mem_rows)
d1blk = pd.read_csv(os.path.join(REPO, "outputs/d1_multireservoir_blocks.csv"))
toff_slow_d1 = float(d1blk[d1blk["block"] == "SLOW"]["T_off"].iloc[0])
axB.bar(mem.reg, mem.T_off, color=["tab:purple" if r in SPEC_3BLOCK["POLAR"]
                                   else "tab:cyan" for r in mem.reg])
axB.axhline(toff_slow_d1, color="k", ls="--", lw=1.2,
            label=f"D1 SLOW composite T_off = {toff_slow_d1:+.2f}")
axB.axhline(0, color="k", lw=0.6)
axB.set(xlabel="region", ylabel="two-rung T_off (glacier-K)",
        title="per-member equilibrium offsets (purple = POLAR, cyan = SUBPOLAR)")
axB.legend(fontsize=8)

best_all = res.sort_values(["feasible", "npass", "flow_win_deficit"],
                           ascending=[False, False, True]).iloc[0]
vbest = "3BLOCK" if best_all["blocks"] == "+".join(SPEC_3BLOCK) else "REASSIGN"
blocks_b = built[vbest]
th_b = {}
for n in blocks_b:
    th_b[f"kappa_{n}"] = best_all[f"kappa_{n}"]
    th_b[f"nu_{n}"] = best_all[f"nu_{n}"]
th_b.update(sigma=best_all["sigma"], rho=best_all["rho"], delta=best_all["delta"])
s_b, per_b = forward_blocks(blocks_b, th_b)
tgt_cm = pd.Series(obs, index=fit_years)
axC.plot(tgt_cm.index, 10 * tgt_cm.diff().rolling(11, center=True).mean(),
         color="k", lw=1.6, label="obs flow (11-yr mean)")
axC.plot(years[1:], 1000 * np.diff(s_b), color="tab:red", lw=1.4, label="model total")
for n, c in zip(blocks_b, ["tab:purple", "tab:cyan", "tab:orange"]):
    axC.plot(years[1:], 1000 * np.diff(per_b[n]), color=c, lw=1.0, label=n)
axC.set(xlim=(1900, 2026), xlabel="year", ylabel="GSIC flow (mm SLE/yr)",
        title=f"block-resolved hindcast — best config ({best_all['label']})")
axC.legend(fontsize=8)
fig.suptitle(f"D1b SLOW-split variants — 3BLOCK vs REASSIGN | ADOPTED anchors | "
             f"commit {COMMIT}", fontsize=10)
os.makedirs(os.path.dirname(OUT_FIG), exist_ok=True)
fig.savefig(OUT_FIG, dpi=150)
print(f"\nWrote {os.path.relpath(OUT_CSV, REPO)}, {os.path.relpath(OUT_BLOCKS, REPO)}, "
      f"{os.path.relpath(OUT_MEMBERS, REPO)}, {os.path.relpath(OUT_FIG, REPO)}")
