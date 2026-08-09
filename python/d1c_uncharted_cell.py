#!/usr/bin/env python3
"""D1c — uncharted-ice cell (Marcus green-light 2026-08-08).

Premise (memo_2026-08-08_geometry_drift_literature.md, PRIMARY-source verified):
the Frederikse-2020-based GSIC target INCLUDES the Parkes & Marzeion 2018
uncharted-glacier contribution ("we account for missing ... and disappeared
glaciers ... uniformly sample between the upper- and lower-bound estimates",
ref 16 = P&M 2018), i.e. 16.7-48.0 mm SLE over 1901-2015 (expected ~32 mm)
of melt from ice that is STRUCTURALLY OUTSIDE the model's present-RGI stock
(V=0.290) and outside GlacierMIP3's committed/response-time data. The D1/D1b
century-integral gap (~50 mm, topology-invariant) should therefore be closed
mostly by SCOPE RECONCILIATION, not physics changes.

Model: the D1 anchored 2-block structure UNCHANGED (tau*=250; per-block
(a,b,T_off) from data partitions + two-rung exact composites; (kappa,nu) from
GlacierMIP3 response times) + an exogenous uncharted-ice cumulative term on
the model side of the target comparison:

    F_unch(t) = U_scope * clip((t - 1901)/(1990 - 1901), 0, 1)      [primary]

  - constant-rate profile 1901-1990: P&M's own rate framing (0.17-0.53 mm/yr
    vs the 1901-1990 budget window) implies the contribution is essentially
    complete by 1990 (rate*90yr reproduces the 1901-2015 totals).
    Sensitivity: FRONTLOAD profile 1 - (1-x)^2 (linearly declining rate).
  - U_scope = U_global * (1 - R5_MELT_SHARE): Frederikse regionalizes
    uncharted melt "by the regional relative contribution from the large
    glaciers"; r5's melt lives in the GIS target, so its uncharted share is
    excluded here (R5_MELT_SHARE = GlaMBIE 2000-23 r5 share ~0.13).
  - U_global FREE with a FLAT prior on [16.7, 48.0] mm — mirroring
    Frederikse's own uniform sampling. No prior penalty inside the bounds.
  - F_unch enters ONLY the flow likelihood (m_cm). Gates, inventory,
    Leclercq, S(1900), ladder, spread are evaluated on the BLOCK model alone
    (uncharted ice is exhausted by ~1990 and absent from the modeled stock by
    construction; F starts 1901 so S(1900) is untouched).

Bookkeeping fixes (provenance-grounded, Frederikse Methods):
  BOOK1 (uncharted subtraction): the inventory-scope melt-to-date used in the
    a_b partition is S2000_inv = S2000_OBS - U_BOOK (central scope value);
    anchors are built at the CENTRAL U (free-U feedback on anchors is
    second-order within +/-9 mm and is not iterated — documented).
  BOOK2 (r19-zero history): "we assume no mass loss from the Antarctic
    peripheral glaciers" — the historical (1850-2000) target melt split
    assigns r19 a ZERO share (Hugonnet shares renormalized over the rest);
    post-2000 GlaMBIE block increments keep r19 (inventory-scope obs).

Ablation arms (all ANCH + MID + FREE; pathological reference re-fit per
variant WITH matched U/delta freedom so the criterion stays apples-to-apples):
  repro    : U=0, no bookfixes, sigma-x2  -> must reproduce D1 exactly
  book     : U=0, BOTH bookfixes, sigma-x2 -> isolates the bookkeeping
  unc_sx2  : +U, bookfixes, sigma-x2
  unc_t5d  : +U, bookfixes, sigma-x1 + T5D delta at the ORIGINAL prior
             (sd 0.30) — the HEADLINE arm. Segment 1900-1960 = exactly the
             pure-Marzeion-2015 window per the Frederikse Methods.
Pre-registered prediction (memo §4): unc_t5d ANCH is FEASIBLE (4/4 gates AND
flow-window deficit <= 5) with |delta| <= ~1 sigma (0.30 mm/yr).

Criteria: unchanged D1 standard (4 adopted-anchor gates + 1980-2023 flow
within FLOW_TOL of the pathological optimum).

Outputs: outputs/d1c_uncharted_cell.csv, outputs/d1c_blocks.csv,
         figures/d1c_uncharted_cell.png. Reuses D1 caches (nc + ladder).
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
OUT_CSV = os.path.join(REPO, "outputs/d1c_uncharted_cell.csv")
OUT_BLOCKS = os.path.join(REPO, "outputs/d1c_blocks.csv")
OUT_FIG = os.path.join(REPO, "figures/d1c_uncharted_cell.png")
CACHE_NC = os.path.join(REPO, "outputs/d1_gmip3_steady_cache.nc")
CACHE_LADDER = os.path.join(REPO, "outputs/d1_block_ladder_cache.csv")
REGIONS_CSV = os.path.join(REPO, "outputs/diag_constraint_anatomy_regions.csv")
TGLAC_REG = os.path.join(REPO, "data/observations/t_glac_regions_hadcrut5.csv")
GLAMBIE_ZIP = os.path.join(REPO, "data/observations/raw/glambie_data.zip")
GMIP3_DIR = os.path.join(REPO, "data/observations/raw/gmip3")
REGCHAR_CSV = os.path.join(GMIP3_DIR,
                           "3_shift_summary_region_characteristicsFeb12_2024.csv")
TEMP_CSV = os.path.join(GMIP3_DIR, "climate_input_data/temp_ch_ipcc_ar6_isimip3b.csv")
D1_CSV = os.path.join(REPO, "outputs/d1_multireservoir_cell.csv")

COMMIT = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True).stdout.strip()

# ---------------------------------------------------------------- constants (= D1)
TAU_STAR = 250
AMP_G = 1.8
EARLY_SIGMA_X2_BEFORE = 1940
T5D_SEG_END = 1960              # = the pure-M15 window end (Frederikse Methods)
T5D_DELTA_PRIOR_MM_YR = 0.30    # ORIGINAL Roe-motivated prior (unchanged)
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
LADDER_RUNGS_SOLVE = (1.2, 2.0)
N_STARTS_FREE = 8
N_STARTS_ANCH = 5
SEED_D1C = 2026
rng_d1 = np.random.default_rng(SEED_D1C)

# --------- D1c-specific constants (Parkes & Marzeion 2018; Frederikse Methods)
UNCH_BOUNDS_GLOBAL_MM = (16.7, 48.0)    # P&M 1901-2015 total, global (Nature 563)
UNCH_CENTRAL_GLOBAL_MM = sum(UNCH_BOUNDS_GLOBAL_MM) / 2      # Frederikse uniform mean
UNCH_WIN = (1901, 1990)                 # constant-rate window (P&M rate framing)
TAPER_FLAT_END, TAPER_ZERO = 1970, 2005   # 'taper': const rate to 1970, linear->0 by 2005
R5_MELT_SHARE = 0.13                    # GlaMBIE 2000-23 r5 share; r5 lives in GIS
UNCH_SCOPE_FAC = 1 - R5_MELT_SHARE
U_BOOK_MM = UNCH_CENTRAL_GLOBAL_MM * UNCH_SCOPE_FAC   # central for anchor bookkeeping
UNCH_BOUNDS_SCOPE_MM = tuple(u * UNCH_SCOPE_FAC for u in UNCH_BOUNDS_GLOBAL_MM)
PROFILES = {"const": lambda x: x, "frontload": lambda x: 1 - (1 - x) ** 2}
PROFILE_PRIMARY = "const"
SENS_PROFILES = ["frontload", "taper"]  # taper: no 1990 step INSIDE the criterion
                                        # window (the const profile's cutoff is a
                                        # 0.3 mm/yr one-year discontinuity at 1990)

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

_ladder_cache = pd.read_csv(CACHE_LADDER)


def block_ladder(members):
    """D1's exact-estimator ladders — MUST hit the cache (no moepy in D1c)."""
    key = "-".join(sorted(members))
    sub = _ladder_cache[_ladder_cache.key == key]
    assert len(sub), f"ladder cache miss for {key} — run d1 first"
    sub = sub.set_index("level_K")
    return ({L: float(sub.loc[L, "central"]) for L in GMIP3_LEVELS},
            {L: (float(sub.loc[L, "lo"]), float(sub.loc[L, "hi"]))
             for L in GMIP3_LEVELS})


# ---------------------------------------------------------------- blocks
GTSHARE = (regs.mass_gt / regs.mass_gt.sum()).to_dict()
MELT_SHARE = regs.melt_share.to_dict()


def hist_shares(r19_zero):
    sh = dict(MELT_SHARE)
    if r19_zero:
        sh["19"] = 0.0
        tot = sum(sh.values())
        sh = {r: v / tot for r, v in sh.items()}
    return sh


def build_blocks(bookfix):
    """D1 2-block structure; bookfix toggles BOOK1 (uncharted subtraction from
    the melt-to-date partition) + BOOK2 (r19-zero historical share)."""
    s2000_inv = S2000_OBS - (U_BOOK_MM / 1000.0 if bookfix else 0.0)
    sh = hist_shares(r19_zero=bookfix)
    slow = [r for r in regs.index if regs.loc[r, "resp_time_15C_yr"] >= TAU_STAR]
    fast = [r for r in regs.index if r not in slow]
    blocks = {}
    for name, members in [("SLOW", slow), ("FAST", fast)]:
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
        s2000 = sum(sh[r] for r in members) * s2000_inv
        com, bands = block_ladder(members)
        a_b = gtshare * INV_V + s2000
        s2020 = s2000 + cum20
        L1, L2 = LADDER_RUNGS_SOLVE
        S1 = s2020 + com[L1] / 100 * (a_b - s2020)
        S2 = s2020 + com[L2] / 100 * (a_b - s2020)
        T1, T2 = amp_b * L1, amp_b * L2
        b_b = (np.log(1 - S1 / a_b) - np.log(1 - S2 / a_b)) / (T2 - T1)
        T_off_b = T1 + np.log(1 - S1 / a_b) / b_b
        blocks[name] = dict(name=name, members=members, driver_obs=drv, amp_b=amp_b,
                            tau15=tau15, tau30=tau30, glambie_rate=rate,
                            glambie_rate_sd=rate_sd, gtshare=gtshare,
                            a=a_b, b=b_b, T_off=T_off_b,
                            S2000_data=s2000, S2020_data=s2020, com=com,
                            com_bands=bands, bookfix=bookfix)
    return blocks


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


# ---------------------------------------------------------------- uncharted term
def unch_cum(u_scope_mm, profile):
    """Cumulative uncharted melt (m SLE) on the model-year grid."""
    if profile == "taper":
        # rate r constant 1901-TAPER_FLAT_END, linear to 0 by TAPER_ZERO;
        # integral = r*(flat + ramp/2) = U  -> smooth landing, no in-window step
        flat = TAPER_FLAT_END - UNCH_WIN[0]
        ramp = TAPER_ZERO - TAPER_FLAT_END
        r = (u_scope_mm / 1000.0) / (flat + ramp / 2.0)
        t = years.astype(float)
        cum = np.where(
            t <= UNCH_WIN[0], 0.0,
            np.where(t <= TAPER_FLAT_END, r * (t - UNCH_WIN[0]),
                     np.where(t <= TAPER_ZERO,
                              r * flat + r * (t - TAPER_FLAT_END)
                              * (1 - (t - TAPER_FLAT_END) / (2.0 * ramp)),
                              r * (flat + ramp / 2.0))))
        return cum
    x = np.clip((years - UNCH_WIN[0]) / (UNCH_WIN[1] - UNCH_WIN[0]), 0.0, 1.0)
    return (u_scope_mm / 1000.0) * PROFILES[profile](x)


# ---------------------------------------------------------------- likelihood
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
# variant registry: repro must equal D1 ANCH/sx2 bit-for-bit in spirit
VARIANTS = {
    "repro":   dict(eps_vec=eps_sx2, has_delta=False, has_u=False, bookfix=False),
    "book":    dict(eps_vec=eps_sx2, has_delta=False, has_u=False, bookfix=True),
    "unc_sx2": dict(eps_vec=eps_sx2, has_delta=False, has_u=True, bookfix=True),
    "unc_t5d": dict(eps_vec=eps, has_delta=True, has_u=True, bookfix=True),
}


def total_m_cm(s_blocks, th, profile):
    """Model-side series compared to the target: blocks + uncharted term."""
    s_tot = s_blocks + unch_cum(th.get("u_mm", 0.0), profile)
    return 100 * (s_tot - s_tot[ybase].mean())


def loglik(blocks, th, variant, arm, profile=PROFILE_PRIMARY):
    v = VARIANTS[variant]
    obs_vec = obs_corrected(th["delta"]) if v["has_delta"] else obs
    s_blocks, per = forward_blocks(blocks, th)
    m_cm = total_m_cm(s_blocks, th, profile)
    ll_flow = flow_logl_window(m_cm, obs_vec, v["eps_vec"], th["sigma"], th["rho"],
                               fit_years[0], fit_years[-1])
    if not np.isfinite(ll_flow):
        return None
    a_tot = sum(b["a"] for b in blocks.values())
    ll_inv = norm.logpdf(a_tot - s_blocks[i_inv], INV_V, INV_SIG)   # blocks only
    ll_lec = norm.logpdf(s_blocks[i1900], LEC_MU, LEC_SIG)          # F starts 1901
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
    # U prior: FLAT within the P&M scope bounds (Frederikse's own sampling) — no term
    return dict(ll_flow=ll_flow, ll_inv=ll_inv, ll_lec=ll_lec, ll_blk=ll_blk,
                ll_prior=ll_pr, logJ=ll_flow + ll_inv + ll_lec + ll_blk + ll_pr,
                s_blocks=s_blocks, per=per, m_cm=m_cm, obs_vec=obs_vec)


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


def optimize_arm(blocks, variant, arm, anchored=None, profile=PROFILE_PRIMARY):
    v = VARIANTS[variant]
    names = list(blocks)
    free = ["sigma", "rho"]
    if v["has_delta"]:
        free.append("delta")
    if v["has_u"]:
        free.append("u_mm")
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
        th.setdefault("u_mm", 0.0)
        return th

    def neg(z):
        t = loglik(blocks, mk(z), variant, arm, profile)
        return np.inf if t is None else -t["logJ"]

    seeds = []
    base = dict(sigma=0.03, rho=0.6, delta=0.0, u_mm=U_BOOK_MM)
    if arm == "FREE":
        for scale, nu in [(1.0, 1.0), (3.0, 0.5), (0.3, 1.5)]:
            sd = dict(base, nu_shared=nu)
            for n in names:
                sd[f"kappa_{n}"] = scale / blocks[n]["tau15"]
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
                     options=dict(xatol=1e-7, fatol=1e-9, maxiter=8000, maxfev=12000))
        if best is None or r.fun < best.fun:
            best = r
    r = minimize(neg, best.x, method="Nelder-Mead",
                 options=dict(xatol=1e-8, fatol=1e-10, maxiter=8000, maxfev=12000))
    return mk((r if r.fun < best.fun else best).x)


# ------------------------------------------------ pathological (matched U/delta freedom)
Tarr_agg = extend_obs(tglac_obs, fair_rb, AMP_G).to_numpy()[:-1]
PATHO_BASE = ["a", "b", "T_off", "kappa", "nu", "sigma", "rho"]


def optimize_patho(variant, profile=PROFILE_PRIMARY):
    v = VARIANTS[variant]
    free = PATHO_BASE + (["delta"] if v["has_delta"] else []) \
        + (["u_mm"] if v["has_u"] else [])
    pb = dict(BOUNDS, delta=DELTA_BOUNDS_MM_YR, u_mm=UNCH_BOUNDS_SCOPE_MM)

    def mk(z):
        th = {}
        for nm, zz in zip(free, z):
            lo, hi = pb[nm]
            th[nm] = lo + (hi - lo) / (1 + np.exp(-zz))
        th.setdefault("delta", 0.0)
        th.setdefault("u_mm", 0.0)
        return th

    def neg(z):
        th = mk(z)
        s_raw = integrate_N(Tarr_agg, th["a"], th["b"], th["T_off"],
                            th["kappa"], th["nu"])
        s_tot = s_raw + unch_cum(th["u_mm"], profile)
        m_cm = 100 * (s_tot - s_tot[ybase].mean())
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
                     options=dict(xatol=1e-7, fatol=1e-9, maxiter=8000, maxfev=12000))
        if best is None or r.fun < best.fun:
            best = r
    th = mk(best.x)
    s_raw = integrate_N(Tarr_agg, th["a"], th["b"], th["T_off"], th["kappa"], th["nu"])
    s_tot = s_raw + unch_cum(th["u_mm"], profile)
    m_cm = 100 * (s_tot - s_tot[ybase].mean())
    obs_vec = obs_corrected(th["delta"]) if v["has_delta"] else obs
    fw = flow_logl_window(m_cm, obs_vec, v["eps_vec"], th["sigma"], th["rho"],
                          FLOW_WIN[0], FLOW_WIN[1])
    return th, fw


# ---------------------------------------------------------------- metrics
def metrics(blocks, th, variant, arm, patho_fw, profile=PROFILE_PRIMARY, label=""):
    t = loglik(blocks, th, variant, arm, profile)
    if t is None:
        return None
    s, per = t["s_blocks"], t["per"]
    v = VARIANTS[variant]
    num = {L: 0.0 for L in GMIP3_LEVELS}
    den = 0.0
    for name, blk in blocks.items():
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
    gates = dict(g_inv=abs(invz) < 1,
                 g_s1900=S1900_GATE_MM[0] <= s1900 <= S1900_GATE_MM[1],
                 g_lad=all(GMIP3_LIKELY[L][0] <= com_agg[L] <= GMIP3_LIKELY[L][1]
                           for L in GMIP3_LEVELS),
                 g_spread=4.5 <= spread <= 13.5)
    u_mm = th.get("u_mm", 0.0)
    row = dict(label=label, arm=arm, variant=variant, profile=profile,
               bookfix=VARIANTS[variant]["bookfix"],
               sigma=th["sigma"], rho=th["rho"], delta=th.get("delta", 0.0),
               u_mm=u_mm, u_global_mm=u_mm / UNCH_SCOPE_FAC if u_mm else 0.0,
               delta_sigmas=abs(th.get("delta", 0.0)) / T5D_DELTA_PRIOR_MM_YR,
               logJ=t["logJ"], ll_flow=t["ll_flow"],
               flow_win=fw, flow_win_deficit=patho_fw - fw,
               rate_modern_mm_yr=rate_modern,
               S1900_mm=s1900, inv_z=invz, S2020_mm=1000 * s[i2020],
               S2020_total_mm=1000 * (s[i2020] + unch_cum(u_mm, profile)[i2020]),
               **{f"com{str(L).replace('.', 'p')}": com_agg[L] for L in GMIP3_LEVELS},
               ds126=ds["ssp126"], ds245=ds["ssp245"], ds585=ds["ssp585"],
               spread=spread, **era_ll, **gates,
               npass=sum(gates.values()),
               feasible=(sum(gates.values()) == 4 and (patho_fw - fw) <= FLOW_TOL))
    for name in blocks:
        row[f"kappa_{name}"] = th[f"kappa_{name}"]
        row[f"nu_{name}"] = th[f"nu_{name}"]
    return row, per, t


# ---------------------------------------------------------------- sanity battery
def sanity_battery(blocks_repro):
    print("\n== sanity battery (D1c) ==")
    # 1. U=0 nesting: total_m_cm with u=0 == plain block m_cm
    th0 = {f"kappa_{n}": 0.005 for n in blocks_repro}
    th0.update({f"nu_{n}": 1.0 for n in blocks_repro})
    s_blocks, _ = forward_blocks(blocks_repro, th0)
    m0 = total_m_cm(s_blocks, dict(th0, u_mm=0.0), PROFILE_PRIMARY)
    m_plain = 100 * (s_blocks - s_blocks[ybase].mean())
    ok1 = np.array_equal(m0, m_plain)
    print(f"  [1] U=0 nesting (m_cm identical): {'PASS' if ok1 else 'FAIL'}")
    # 2. uncharted profile endpoints: F(1900)=0, F(1990)=F(2026)=U
    F = unch_cum(28.0, PROFILE_PRIMARY)
    i1901 = np.searchsorted(years, 1901)
    i1990_, iend = np.searchsorted(years, 1990), len(years) - 1
    ok2 = (F[i1901] == 0.0 and abs(F[i1990_] - 0.028) < 1e-12
           and F[iend] == F[i1990_])
    print(f"  [2] F_unch endpoints (0 at 1901, U at 1990, flat after): "
          f"{'PASS' if ok2 else 'FAIL'}")
    # 3. post-1990 invariance: m_cm(t>=1990) unaffected by U (baseline cancels)
    mU = total_m_cm(s_blocks, dict(th0, u_mm=40.0), PROFILE_PRIMARY)
    sel_post = years >= 1990
    ok3 = np.allclose(mU[sel_post], m_plain[sel_post], atol=1e-10)
    print(f"  [3] post-1990 m_cm invariant to U: {'PASS' if ok3 else 'FAIL'}")
    if not (ok1 and ok2 and ok3):
        raise SystemExit("SANITY BATTERY FAILED — do not trust results")


# ---------------------------------------------------------------- run
print(f"D1c uncharted-ice cell | commit={COMMIT} | anchors=ADOPTED | criteria = D1 "
      f"(4 gates + flow{FLOW_WIN} tol {FLOW_TOL})")
print(f"  U_global ~ flat[{UNCH_BOUNDS_GLOBAL_MM[0]}, {UNCH_BOUNDS_GLOBAL_MM[1]}] mm "
      f"(P&M 2018, Frederikse uniform sampling) x scope {UNCH_SCOPE_FAC:.2f} "
      f"(1 - r5 share {R5_MELT_SHARE}) -> [{UNCH_BOUNDS_SCOPE_MM[0]:.1f}, "
      f"{UNCH_BOUNDS_SCOPE_MM[1]:.1f}] | profile {PROFILE_PRIMARY} {UNCH_WIN} | "
      f"U_book {U_BOOK_MM:.1f} mm | delta prior sd {T5D_DELTA_PRIOR_MM_YR} (original)")
print(f"  PREDICTION (pre-registered, memo §4): unc_t5d ANCH feasible with "
      f"|delta| <= ~1 sigma")

blocks_by_book = {False: build_blocks(bookfix=False), True: build_blocks(bookfix=True)}
anch_by_book = {}
block_rows = []
for bf, blocks in blocks_by_book.items():
    anch_by_book[bf] = {}
    print(f"\n== block anchors (bookfix={bf}) ==")
    for name, blk in blocks.items():
        anch = solve_anchored(blk)
        anch_by_book[bf][name] = anch
        print(f"  [{name}] a={blk['a']:.3f} b={blk['b']:.3f} T_off={blk['T_off']:+.3f} "
              f"S2000={1000 * blk['S2000_data']:.0f}mm S2020={1000 * blk['S2020_data']:.0f}mm "
              f"| kappa={anch['kappa']:.5f} nu={anch['nu']:.2f} "
              f"({'exact' if anch['exact'] else 'FALLBACK'}, match={anch['match_ok']})")
        block_rows.append(dict(bookfix=bf, block=name, a=blk["a"], b=blk["b"],
                               T_off=blk["T_off"], amp_b=blk["amp_b"],
                               S2000_mm=1000 * blk["S2000_data"],
                               S2020_mm=1000 * blk["S2020_data"],
                               kappa_anch=anch["kappa"], nu_anch=anch["nu"],
                               anch_exact=anch["exact"],
                               **{f"com{str(L).replace('.', 'p')}": blk["com"][L]
                                  for L in GMIP3_LEVELS}))
pd.DataFrame(block_rows).to_csv(OUT_BLOCKS, index=False, float_format="%.5f")

sanity_battery(blocks_by_book[False])

patho = {}
for variant in VARIANTS:
    th_p, fw_p = optimize_patho(variant)
    patho[variant] = fw_p
    print(f"patho [{variant:8s}]: flow{FLOW_WIN}={fw_p:.2f} "
          f"u={th_p.get('u_mm', 0):.1f} delta={th_p.get('delta', 0):+.2f}"
          + ("  (D1 sx2 ref 52.82)" if variant == "repro" else ""))

rows = []
for variant in VARIANTS:
    bf = VARIANTS[variant]["bookfix"]
    blocks = blocks_by_book[bf]
    anchored = anch_by_book[bf]
    print(f"\n== runs [{variant}] (bookfix={bf}) ==")
    for arm in ["ANCH", "MID", "FREE"]:
        th = optimize_arm(blocks, variant, arm, anchored=anchored)
        m = metrics(blocks, th, variant, arm, patho[variant],
                    label=f"{arm}/{variant}")
        if m is None:
            print(f"  [{arm}/{variant}] DEGENERATE")
            continue
        row, per, t = m
        rows.append(row)
        print(f"  [{row['label']:14s}] npass={row['npass']}/4 "
              f"[inv{'+' if row['g_inv'] else '-'} s19{'+' if row['g_s1900'] else '-'} "
              f"lad{'+' if row['g_lad'] else '-'} spr{'+' if row['g_spread'] else '-'}] "
              f"deficit={row['flow_win_deficit']:6.1f} spread={row['spread']:5.1f} "
              f"S2020(blocks)={row['S2020_mm']:.0f}mm "
              f"U={row['u_mm']:.1f} delta={row['delta']:+.2f} "
              f"({row['delta_sigmas']:.1f}sig) "
              f"FEASIBLE={row['feasible']}")
        if arm == "ANCH":
            F = unch_cum(row["u_mm"], PROFILE_PRIMARY)
            i_e = {e: (np.searchsorted(years, e[0]), np.searchsorted(years, e[1]))
                   for e in ERAS}
            era_str = " ".join(
                f"{e[0]}s:{1000 * ((t['s_blocks'][i1] + F[i1]) - (t['s_blocks'][i0] + F[i0])) / (e[1] - e[0]):.2f}"
                for e, (i0, i1) in i_e.items())
            print(f"      ANCH era rates incl F_unch (mm/yr): {era_str}")

# headline-arm profile sensitivities (ANCH only; patho re-fit per profile)
for prof in SENS_PROFILES:
    print(f"\n== profile sensitivity (unc_t5d ANCH, {prof}) ==")
    th = optimize_arm(blocks_by_book[True], "unc_t5d", "ANCH",
                      anchored=anch_by_book[True], profile=prof)
    m = metrics(blocks_by_book[True], th, "unc_t5d", "ANCH",
                optimize_patho("unc_t5d", profile=prof)[1],
                profile=prof, label=f"ANCH/unc_t5d/{prof}")
    if m:
        row = m[0]
        rows.append(row)
        print(f"  [{row['label']}] npass={row['npass']} "
              f"deficit={row['flow_win_deficit']:.1f} U={row['u_mm']:.1f} "
              f"delta={row['delta']:+.2f} ({row['delta_sigmas']:.1f}sig) "
              f"FEASIBLE={row['feasible']}")

res = pd.DataFrame(rows)
os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
res.to_csv(OUT_CSV, index=False, float_format="%.5f")

# ---------------------------------------------------------------- verdict
print("\n=== D1c verdict ===")
d1ref = pd.read_csv(D1_CSV)
d1_anch_sx2 = float(d1ref[(d1ref.label == "ANCH/sx2/t250")]["flow_win_deficit"].iloc[0])
rep = res[res.label == "ANCH/repro"]
if len(rep):
    dd = abs(float(rep.flow_win_deficit.iloc[0]) - d1_anch_sx2)
    print(f"  regression: ANCH/repro deficit {float(rep.flow_win_deficit.iloc[0]):.1f} "
          f"vs D1 ANCH/sx2 {d1_anch_sx2:.1f} (|diff|={dd:.2f} "
          f"{'OK' if dd < 0.5 else '** CHECK **'})")
feas = res[res.feasible == True]  # noqa: E712
print(f"  {len(feas)}/{len(res)} configs FEASIBLE")
hl = res[res.label == "ANCH/unc_t5d"]
if len(hl):
    h = hl.iloc[0]
    pred_ok = bool(h.feasible) and h.delta_sigmas <= 1.0
    print(f"  HEADLINE ANCH/unc_t5d: feasible={h.feasible} "
          f"deficit={h.flow_win_deficit:.1f} npass={h.npass} "
          f"U={h.u_mm:.1f}mm (global {h.u_global_mm:.1f}, bounds "
          f"{UNCH_BOUNDS_GLOBAL_MM}) delta={h.delta:+.2f} ({h.delta_sigmas:.1f} sigma)")
    print(f"  PRE-REGISTERED PREDICTION (feasible AND |delta|<=1 sigma): "
          f"{'CONFIRMED' if pred_ok else 'NOT CONFIRMED'}")

# ---------------------------------------------------------------- figure
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(16.5, 4.8), constrained_layout=True)
axA, axB, axC = axes

order = [r for r in ["ANCH/repro", "ANCH/book", "ANCH/unc_sx2", "ANCH/unc_t5d",
                     "ANCH/unc_t5d/frontload"] if (res.label == r).any()]
cols = ["0.6", "tab:gray", "tab:blue", "tab:green", "tab:olive"]
vals = [float(res[res.label == r].flow_win_deficit.iloc[0]) for r in order]
axA.bar(range(len(order)), vals, color=cols[:len(order)])
axA.axhline(FLOW_TOL, color="k", ls=":", lw=1.2, label=f"tol {FLOW_TOL}")
axA.set_xticks(range(len(order)))
axA.set_xticklabels([r.replace("ANCH/", "") for r in order], rotation=20, fontsize=8)
axA.set(ylabel=f"ANCH flow {FLOW_WIN[0]}-{FLOW_WIN[1]} deficit (logL)",
        title="ablation: D1-repro -> +bookfix -> +U -> +U&delta")
axA.legend(fontsize=8)

hlrow = res[res.label == "ANCH/unc_t5d"].iloc[0] if len(hl) else None
if hlrow is not None:
    blocks = blocks_by_book[True]
    thh = {f"kappa_{n}": hlrow[f"kappa_{n}"] for n in blocks}
    thh.update({f"nu_{n}": hlrow[f"nu_{n}"] for n in blocks})
    thh.update(sigma=hlrow["sigma"], rho=hlrow["rho"], delta=hlrow["delta"],
               u_mm=hlrow["u_mm"])
    s_blocks, per_h = forward_blocks(blocks, thh)
    F = unch_cum(hlrow["u_mm"], PROFILE_PRIMARY)
    tgt_cm = pd.Series(obs, index=fit_years)
    oc = pd.Series(obs_corrected(hlrow["delta"]), index=fit_years)
    axB.plot(tgt_cm.index, 10 * tgt_cm.diff().rolling(11, center=True).mean(),
             color="k", lw=1.6, label="obs flow (11-yr mean)")
    axB.plot(oc.index, 10 * oc.diff().rolling(11, center=True).mean(), color="0.55",
             lw=1.0, ls="--", label=f"obs t5d-corr (delta={hlrow['delta']:+.2f})")
    axB.plot(years[1:], 1000 * np.diff(s_blocks + F), color="tab:red", lw=1.5,
             label="model total (blocks + F_unch)")
    axB.plot(years[1:], 1000 * np.diff(F), color="tab:green", lw=1.2,
             label=f"F_unch (U={hlrow['u_mm']:.0f} mm)")
    axB.plot(years[1:], 1000 * np.diff(per_h["SLOW"]), color="tab:purple", lw=0.9,
             label="SLOW")
    axB.plot(years[1:], 1000 * np.diff(per_h["FAST"]), color="tab:orange", lw=0.9,
             label="FAST")
    axB.set(xlim=(1900, 2026), xlabel="year", ylabel="GSIC flow (mm SLE/yr)",
            title="headline ANCH/unc_t5d — flow decomposition")
    axB.legend(fontsize=7)

MARK = {"ANCH": "*", "FREE": "o", "MID": "D"}
D1_REF = [("ANCH", 20.7, 4), ("ANCH", 11.5, 4), ("MID", 20.4, 4), ("MID", 11.9, 4),
          ("FREE", 15.5, 2), ("FREE", 7.7, 3)]
for a, d, np_ in D1_REF:
    axC.scatter(d, np_, marker=MARK[a], s=60, color="0.65", alpha=0.6, zorder=1)
VCOL = {"repro": "0.4", "book": "tab:gray", "unc_sx2": "tab:blue",
        "unc_t5d": "tab:green"}
for _, r in res.iterrows():
    axC.scatter(r["flow_win_deficit"], r["npass"], marker=MARK[r["arm"]],
                s=170 if r["arm"] == "ANCH" else 70,
                color=VCOL.get(r["variant"], "tab:olive"),
                edgecolors="k", linewidths=0.4, zorder=2)
axC.axvline(FLOW_TOL, color="k", ls=":", lw=1)
axC.axhline(4, color="k", ls=":", lw=1)
axC.set(xlabel=f"flow {FLOW_WIN[0]}-{FLOW_WIN[1]} logL deficit vs pathological",
        ylabel="gates passed (of 4)",
        title="D1c frontier (grey = D1 references)")
hnd = [plt.Line2D([], [], marker=m, ls="", color="k", label=a) for a, m in MARK.items()]
hnd += [plt.Line2D([], [], marker="s", ls="", color=c, label=v) for v, c in VCOL.items()]
axC.legend(handles=hnd, fontsize=7)
fig.suptitle(f"D1c uncharted-ice cell — U flat[{UNCH_BOUNDS_SCOPE_MM[0]:.0f},"
             f"{UNCH_BOUNDS_SCOPE_MM[1]:.0f}]mm scope ({PROFILE_PRIMARY} "
             f"{UNCH_WIN[0]}-{UNCH_WIN[1]}) | delta prior sd {T5D_DELTA_PRIOR_MM_YR} | "
             f"commit {COMMIT}", fontsize=10)
os.makedirs(os.path.dirname(OUT_FIG), exist_ok=True)
fig.savefig(OUT_FIG, dpi=150)
print(f"\nWrote {os.path.relpath(OUT_CSV, REPO)}, {os.path.relpath(OUT_BLOCKS, REPO)}, "
      f"{os.path.relpath(OUT_FIG, REPO)}")
