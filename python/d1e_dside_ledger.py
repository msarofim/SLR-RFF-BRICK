#!/usr/bin/env python3
"""D1e — Option D: model-side ledger for the Leclercq S(1900) datum.
Marcus ruling 2026-08-09 ("go ahead with D"): the datum stays at its
published family envelope N(20, 9) mm; everything the present-inventory
model does not represent is held SEPARATELY on the model side of the
comparison, mirroring the F_unch convention on the flow target.
Spec + P&M 2018 primary receipts: notes/memo_2026-08-09_d_ledger_target_spec.md.

Ledger (datum basis: 1850-1900 melt, excl r19, incl r5):
    S_ledger(1900) = S_inv(1900)   SLOWP+FAST 1850->1900 melt (model)
                   + S_r5          charted r5 melt set-aside, N(2.5, 2.0) mm [0, 8]
                   + U_pre         pre-1901 melt of ice absent from the present
                                   inventory (P&M uncharted stock + pre-1901-
                                   vanished glaciers), flat [0, 25] mm
    ll_lec = Normal(LEC_MU, LEC_SIG).logpdf(S_ledger)
    gate g_lec = |z_ledger| <= 2      (replaces g_s1900 in npass/feasible;
                                       the legacy S_all value + 10-30 box
                                       verdict are still reported)

U_pre prior derivation (P&M 2018 receipts, see spec memo section 3):
  stock@1901 = loss + 2015 remainder = 18.8 (lower) - 50.4 (upper) mm SLE;
  early-20th-c uncharted rate up to ~0.6 mm/yr ("largest early"); pre-1900/
  early-20th rate ratio m in [0.25, 1.0]; 50yr x m x rate ~ [2, 30], capped
  at 25 by stock self-consistency. The 0 edge IS the charted-scope reading
  of Leclercq (T1 memo) - not padding. No x0.87: the datum includes r5.

Structures/anchors/obs machinery are exec-inherited from d1d (which itself
execs the d0 prefix). Structures are built in d1d's exact order (A, B, C)
so the seeded rng stream reproduces the d1d block parameters; only C_both
configs are RUN (the 2-block ablation cannot separate r19, so the ledger
is undefined there).

SANITY (evaluation-based): [1] obs_adj identity (inherited); [2] structures
reproduce d1d_blocks.csv; [3] stored d1d C_both/ANCH thetas evaluated under
the inherited legacy loglik reproduce the stored flow_win/S1900/logJ;
[4] ledger arithmetic identity.

PRE-REGISTERED (spec memo section 4):
  P1  ANCH deficit unchanged (8.21 +/- 0.05) - ledger params separable.
  P2  ledger fits interior (U_pre ~ 6-11, S_r5 within prior, z_lec ~ 0)
      -> ANCH/MID npass 4/4.
  P3  FREE decouples from the Leclercq pull: legacy S1900 drops from ~27-28
      toward the ANCH range; spread still fails.
  WATCH (not a prediction): C_both/MID/unc_sx2 deficit 5.07 vs tol 5.
  BARS: minimal = ANCH deficit <= 8.4, |delta| <= 1 sigma, 4/4 gates;
  strong = FEASIBLE (4/4 AND <= 5) - NOT expected (D does not touch flow).

Outputs: outputs/d1e_dside_ledger.csv, figures/d1e_dside_ledger.png.
"""
import os

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import norm

REPO_D1E = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
D1D_SRC = os.path.join(REPO_D1E, "python/d1d_fourrung_seam.py")

_src = open(D1D_SRC).read()
_MARKER = "# ---------------------------------------------------------------- run\n"
assert _src.count(_MARKER) == 1, "d1d run marker not unique - refusing to exec"
exec(_src.split(_MARKER)[0])

# paths AFTER the exec (rebind trap)
OUT_CSV = os.path.join(REPO, "outputs/d1e_dside_ledger.csv")
OUT_FIG = os.path.join(REPO, "figures/d1e_dside_ledger.png")
D1D_CSV = os.path.join(REPO, "outputs/d1d_fourrung_seam.csv")
D1D_BLOCKS_CSV = os.path.join(REPO, "outputs/d1d_blocks.csv")

# ------------------------------------------------------------- D1e constants
UPRE_BOUNDS_MM = (0.0, 25.0)     # flat prior; spec memo section 3 (P&M receipts)
SR5_PRIOR_MM = (2.5, 2.0)        # charted r5 1850-1900: 13% share x ~20 mm
SR5_BOUNDS_MM = (0.0, 8.0)
LEC_Z_GATE = 2.0                 # |z_ledger| gate half-width
P1_DEFICIT_REF, P1_TOL = 8.21059, 0.05   # d1d C_both/ANCH/unc_t5d
MID_SX2_WATCH = 5.06701          # d1d C_both/MID/unc_sx2 deficit (watch vs tol)
LEC_MU_MM, LEC_SIG_MM = 1000 * LEC_MU, 1000 * LEC_SIG

RES_NAMES_3 = list(SPEC_3RES)    # ["R19", "SLOWP", "FAST"]
HIND_D1E = ["SLOWP", "FAST"]

CONFIGS_D1E = [("C_both", "unc_t5d", "obs_adj", HIND_D1E),   # HEADLINE
               ("C_both", "unc_sx2", "obs_adj", HIND_D1E)]   # no-delta secondary


def param_bounds_d(nm):
    if nm == "u_pre_mm":
        return UPRE_BOUNDS_MM
    if nm == "s_r5_mm":
        return SR5_BOUNDS_MM
    return param_bounds(nm)


def ledger_mm(s_hind_1900_m, th):
    return 1000 * s_hind_1900_m + th["u_pre_mm"] + th["s_r5_mm"]


def loglik_d(reservoirs, th, variant, arm, hind_names, base_obs,
             profile=PROFILE_PRIMARY):
    """d1d loglik with the D-ledger Leclercq term. hind_names must exclude
    R19 (asserted at run start): the datum basis excludes r19."""
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
    # D-ledger: datum untouched; set-asides on the model side (mm scale)
    ll_lec = norm.logpdf(ledger_mm(s_hind[i1900], th), LEC_MU_MM, LEC_SIG_MM)
    ll_blk = 0.0
    ir0, ir1 = np.searchsorted(years, 2000), np.searchsorted(years, 2024)
    for name in hind_names:
        blk = reservoirs[name]
        mrate = 1000 * (per[name][ir1] - per[name][ir0]) / (ir1 - ir0)
        if arm in ("FREE", "MID"):
            ll_blk += norm.logpdf(mrate, blk["glambie_rate"], blk["glambie_rate_sd"])
    ll_pr = norm.logpdf(th["s_r5_mm"], *SR5_PRIOR_MM)   # U_pre flat: bounds only
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


def optimize_arm_d(reservoirs, variant, arm, anchored, hind_names, base_obs,
                   profile=PROFILE_PRIMARY):
    v = VARIANTS[variant]
    names = list(reservoirs)
    free = ["sigma", "rho", "u_mm", "u_pre_mm", "s_r5_mm"] \
        + (["delta"] if v["has_delta"] else [])
    if arm == "FREE":
        free = [f"kappa_{n}" for n in names] + ["nu_shared"] + free
    elif arm == "MID":
        free = [f"kappa_{n}" for n in names] + free
    nstart = N_STARTS_ANCH if arm == "ANCH" else N_STARTS_FREE

    def mk(z):
        th = {}
        for nm, zz in zip(free, z):
            lo, hi = param_bounds_d(nm)
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
        t = loglik_d(reservoirs, mk(z), variant, arm, hind_names, base_obs, profile)
        return np.inf if t is None else -t["logJ"]

    seeds = []
    base = dict(sigma=0.03, rho=0.6, delta=0.0, u_mm=U_BOOK_MM,
                u_pre_mm=9.0, s_r5_mm=SR5_PRIOR_MM[0])
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
        seeds.append(dict(base, sigma=0.02, rho=0.3, u_pre_mm=2.0,
                          u_mm=UNCH_BOUNDS_SCOPE_MM[1] * 0.95))
    starts = []
    for sd in seeds:
        z = []
        for nm in free:
            lo, hi = param_bounds_d(nm)
            x = np.clip((sd[nm] - lo) / (hi - lo), 1e-4, 1 - 1e-4)
            z.append(np.log(x / (1 - x)))
        starts.append(np.array(z))
    b0 = list(starts)
    while len(starts) < nstart:
        starts.append(b0[rng_d1.integers(len(b0))] + rng_d1.normal(0, 0.6, len(free)))
    best = None
    for z0 in starts:
        r = minimize(neg, z0, method="Nelder-Mead",
                     options=dict(xatol=1e-7, fatol=1e-9, maxiter=11000, maxfev=16000))
        if best is None or r.fun < best.fun:
            best = r
    r = minimize(neg, best.x, method="Nelder-Mead",
                 options=dict(xatol=1e-8, fatol=1e-10, maxiter=11000, maxfev=16000))
    return mk((r if r.fun < best.fun else best).x)


def optimize_patho_d(variant, base_obs, profile=PROFILE_PRIMARY):
    """Matched freedom: the pathological comparator gains (u_pre, s_r5) too.
    Its single aggregate reservoir cannot separate r19 (~1-2 mm asymmetry
    vs the ledger's excl-r19 basis, << sigma 9 mm - documented, not
    parameterized)."""
    v = VARIANTS[variant]
    free = PATHO_BASE + ["u_pre_mm", "s_r5_mm"] + (["delta"] if v["has_delta"] else [])
    pb = dict(BOUNDS, delta=DELTA_BOUNDS_MM_YR, u_mm=UNCH_BOUNDS_SCOPE_MM,
              u_pre_mm=UPRE_BOUNDS_MM, s_r5_mm=SR5_BOUNDS_MM)

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
        ll += norm.logpdf(ledger_mm(s_raw[i1900], th), LEC_MU_MM, LEC_SIG_MM)
        ll += norm.logpdf(th["s_r5_mm"], *SR5_PRIOR_MM)
        ll += sum(norm.logpdf(th[p], *PRIORS[p]) for p in ("a", "b", "T_off"))
        ll += norm.logpdf(np.log(th["kappa"]), *KAPPA_LOGPRIOR)
        ll += norm.logpdf(th["nu"], *NU_PRIOR)
        if v["has_delta"]:
            ll += norm.logpdf(th["delta"], 0.0, T5D_DELTA_PRIOR_MM_YR)
        return -ll

    seeds = [dict(a=0.298, b=0.320, T_off=-2.0, kappa=0.0085, nu=0.10,
                  sigma=0.005, rho=0.05, delta=0.0, u_mm=U_BOOK_MM,
                  u_pre_mm=9.0, s_r5_mm=SR5_PRIOR_MM[0]),
             dict(a=0.33, b=0.35, T_off=-1.8, kappa=0.006, nu=0.12,
                  sigma=0.01, rho=0.3, delta=0.0, u_mm=UNCH_BOUNDS_SCOPE_MM[0] * 1.05,
                  u_pre_mm=2.0, s_r5_mm=1.0),
             dict(a=0.45, b=0.52, T_off=-1.10, kappa=0.0106, nu=0.15,
                  sigma=0.04, rho=0.70, delta=0.0, u_mm=UNCH_BOUNDS_SCOPE_MM[1] * 0.95,
                  u_pre_mm=20.0, s_r5_mm=4.0)]
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
                     options=dict(xatol=1e-7, fatol=1e-9, maxiter=11000, maxfev=16000))
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


def era_rate(series_m, y0, y1):
    """Endpoint-difference mean rate (mm/yr) of a cumulative m-SLE series on
    the `years` grid."""
    ia, ib = np.searchsorted(years, y0), np.searchsorted(years, y1)
    return 1000 * (series_m[ib] - series_m[ia]) / (y1 - y0)


def obs_era_rate(vec_cm, y0, y1):
    ia = int(np.searchsorted(fit_years, y0))
    ib = int(np.searchsorted(fit_years, y1))
    return 10 * (vec_cm[ib] - vec_cm[ia]) / (y1 - y0)


def metrics_d(reservoirs, th, variant, arm, patho_fw, patho_fw_d1dref, hind_names,
              base_obs, profile=PROFILE_PRIMARY, label=""):
    t = loglik_d(reservoirs, th, variant, arm, hind_names, base_obs, profile)
    if t is None:
        return None
    per, s_all, s_hind = t["per"], t["s_all"], t["s_hind"]
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
    # --- D ledger + legacy reporting
    s_inv1900 = 1000 * s_hind[i1900]
    ledger = ledger_mm(s_hind[i1900], th)
    lec_z = (ledger - LEC_MU_MM) / LEC_SIG_MM
    s1900_legacy = 1000 * s_all[i1900]
    g_box_legacy = S1900_GATE_MM[0] <= s1900_legacy <= S1900_GATE_MM[1]
    a_tot = sum(b["a"] for b in reservoirs.values())
    invz = (a_tot - s_all[i_inv] - INV_V) / INV_SIG
    fw = flow_logl_window(t["m_cm"], t["obs_vec"], v["eps_vec"], th["sigma"],
                          th["rho"], FLOW_WIN[0], FLOW_WIN[1])
    era_ll = {f"flow_{a}_{b}": flow_logl_window(t["m_cm"], t["obs_vec"], v["eps_vec"],
                                                th["sigma"], th["rho"], a, b)
              for a, b in ERAS}
    # --- era-rate emitters (T2 cheap item)
    F = unch_cum(th.get("u_mm", 0.0), profile)
    era_rates = {}
    for a, b in ERAS:
        era_rates[f"rate_hind_{a}_{b}"] = era_rate(s_hind, a, b)
        era_rates[f"rate_tot_{a}_{b}"] = era_rate(s_hind + F, a, b)
    res_rates = {}
    for name in reservoirs:
        res_rates[f"rate0023_{name}"] = era_rate(per[name], 2000, 2023)
        res_rates[f"rate1523_{name}"] = era_rate(per[name], RATE_WIN[0], RATE_WIN[1])
    ir0, ir1 = np.searchsorted(years, RATE_WIN[0]), np.searchsorted(years, RATE_WIN[1])
    rate_modern_hind = 1000 * (s_hind[ir1] - s_hind[ir0]) / (RATE_WIN[1] - RATE_WIN[0])
    gates = dict(g_inv=abs(invz) < 1,
                 g_lec=abs(lec_z) <= LEC_Z_GATE,
                 g_lad=all(GMIP3_LIKELY[L][0] <= com_agg[L] <= GMIP3_LIKELY[L][1]
                           for L in GMIP3_LEVELS),
                 g_spread=4.5 <= spread <= 13.5)
    u_mm = th.get("u_mm", 0.0)
    row = dict(label=label, arm=arm, variant=variant, profile=profile,
               nres=len(reservoirs), hind="+".join(hind_names),
               sigma=th["sigma"], rho=th["rho"], delta=th.get("delta", 0.0),
               u_mm=u_mm, delta_sigmas=abs(th.get("delta", 0.0)) / T5D_DELTA_PRIOR_MM_YR,
               u_pre_mm=th["u_pre_mm"], s_r5_mm=th["s_r5_mm"],
               s1900_inv_mm=s_inv1900, s1900_ledger_mm=ledger, lec_z=lec_z,
               s1900_legacy_mm=s1900_legacy, g_s1900_legacy_box=g_box_legacy,
               logJ=t["logJ"], ll_flow=t["ll_flow"],
               flow_win=fw, flow_win_deficit=patho_fw - fw,
               deficit_d1dref=patho_fw_d1dref - fw,
               rate_modern_hind=rate_modern_hind,
               inv_z=invz, S2020_all_mm=1000 * s_all[i2020],
               **{f"com{str(L).replace('.', 'p')}": com_agg[L] for L in GMIP3_LEVELS},
               ds126=ds["ssp126"], ds245=ds["ssp245"], ds585=ds["ssp585"],
               spread=spread, **era_ll, **era_rates, **res_rates, **gates,
               npass=sum(gates.values()),
               feasible=(sum(gates.values()) == 4 and (patho_fw - fw) <= FLOW_TOL))
    for name in reservoirs:
        row[f"kappa_{name}"] = th[f"kappa_{name}"]
        row[f"nu_{name}"] = th[f"nu_{name}"]
    return row, per, t


# ---------------------------------------------------------------- sanity (D1e)
def sanity_d1e(structures_, anchors_, d1d_rows):
    print("\n== sanity battery (D1e, evaluation-based) ==")
    ok = []
    # [1] inherited obs_adj invariants
    pre = fit_years < 2019
    ok.append(np.array_equal(OBS_ADJ[pre], obs[pre]) and (obs[-1] - OBS_ADJ[-1]) > 0)
    print(f"  [1] obs_adj identity pre-2019 + net r19 removal: "
          f"{'PASS' if ok[-1] else 'FAIL'}")
    # [2] structures reproduce d1d_blocks.csv
    blk_ref = pd.read_csv(D1D_BLOCKS_CSV)
    worst = 0.0
    for sname, resv in structures_.items():
        for bname, blk in resv.items():
            ref = blk_ref[(blk_ref.structure == sname) & (blk_ref.block == bname)]
            assert len(ref) == 1, f"missing d1d block row {sname}/{bname}"
            ref = ref.iloc[0]
            anch = anchors_[sname][bname]
            for col, val in [("a", blk["a"]), ("b", blk["b"]), ("T_off", blk["T_off"]),
                             ("kappa_anch", anch["kappa"]), ("nu_anch", anch["nu"])]:
                worst = max(worst, abs(val - ref[col]))
    ok.append(worst < 1e-4)
    print(f"  [2] structures reproduce d1d_blocks.csv (max |diff| = {worst:.2e}): "
          f"{'PASS' if ok[-1] else 'FAIL'}")
    # [3] legacy evaluation identity: stored d1d C_both/ANCH thetas under the
    #     INHERITED d1d loglik reproduce stored flow_win / S1900 / logJ
    worst3 = {}
    for variant in ("unc_t5d", "unc_sx2"):
        ref = d1d_rows[d1d_rows.label == f"C_both/ANCH/{variant}"].iloc[0]
        th = dict(sigma=ref["sigma"], rho=ref["rho"], delta=ref["delta"],
                  u_mm=ref["u_mm"])
        for n in RES_NAMES_3:
            th[f"kappa_{n}"] = ref[f"kappa_{n}"]
            th[f"nu_{n}"] = ref[f"nu_{n}"]
        t = loglik(structures_["C_both"], th, variant, "ANCH", HIND_D1E, OBS_ADJ)
        fw = flow_logl_window(t["m_cm"], t["obs_vec"], VARIANTS[variant]["eps_vec"],
                              th["sigma"], th["rho"], FLOW_WIN[0], FLOW_WIN[1])
        worst3[variant] = dict(fw=abs(fw - ref["flow_win"]),
                               s1900=abs(1000 * t["s_all"][i1900] - ref["S1900_mm"]),
                               logJ=abs(t["logJ"] - ref["logJ"]))
    w3 = max(max(d.values()) for d in worst3.values())
    ok.append(all(d["fw"] < 0.1 and d["s1900"] < 0.1 and d["logJ"] < 0.5
                  for d in worst3.values()))
    print(f"  [3] d1d theta evaluation identity (max |diff| = {w3:.2e}): "
          f"{'PASS' if ok[-1] else 'FAIL'}")
    # [4] ledger arithmetic identity
    th4 = dict(u_pre_mm=7.0, s_r5_mm=2.0)
    lz = (ledger_mm(0.008, th4) - LEC_MU_MM) / LEC_SIG_MM
    ok.append(abs(lz - ((8.0 + 7.0 + 2.0 - 20.0) / 9.0)) < 1e-12)
    print(f"  [4] ledger z arithmetic identity: {'PASS' if ok[-1] else 'FAIL'}")
    if not all(ok):
        raise SystemExit("SANITY BATTERY FAILED - do not trust results")


# ---------------------------------------------------------------- run
print(f"D1e Option-D ledger | commit={COMMIT} | datum N({LEC_MU_MM:.0f},{LEC_SIG_MM:.0f})mm "
      f"UNTOUCHED | U_pre flat[{UPRE_BOUNDS_MM[0]:.0f},{UPRE_BOUNDS_MM[1]:.0f}]mm | "
      f"S_r5 N{SR5_PRIOR_MM}mm [{SR5_BOUNDS_MM[0]:.0f},{SR5_BOUNDS_MM[1]:.0f}] | "
      f"gate |z|<={LEC_Z_GATE}")
print(f"  spec: notes/memo_2026-08-09_d_ledger_target_spec.md | P1 deficit ref "
      f"{P1_DEFICIT_REF} +/- {P1_TOL} | MID/sx2 watch {MID_SX2_WATCH} vs tol {FLOW_TOL}")

assert "R19" not in HIND_D1E and set(HIND_D1E) == {"SLOWP", "FAST"}

# structures in d1d's exact order (rng-stream alignment for sanity [2])
res3_raw = {n: build_reservoir(n, m, farinotti_basis=True)
            for n, m in SPEC_3RES.items()}
blk2_raw = {n: build_reservoir(n, m, farinotti_basis=False)
            for n, m in SPEC_2BLK.items()}
structures = {}
structures["A_4rung"] = {n: four_rung_fit(b) for n, b in blk2_raw.items()}
structures["B_seam"] = {n: two_rung_anchor(b) for n, b in res3_raw.items()}
structures["C_both"] = {n: four_rung_fit(b) for n, b in res3_raw.items()}
anchors = {s: {n: solve_anchored(b) for n, b in resv.items()}
           for s, resv in structures.items()}

d1d_rows = pd.read_csv(D1D_CSV)
sanity_d1e(structures, anchors, d1d_rows)

# obs-side era rates (printed once; the 0.766 correction computed, not hardcoded)
obs_adj_modern = obs_era_rate(OBS_ADJ, RATE_WIN[0], RATE_WIN[1])
print(f"\n  obs era rates (mm/yr, endpoint-diff): "
      + "  ".join(f"{a}-{b}: {obs_era_rate(obs, a, b):.3f}/{obs_era_rate(OBS_ADJ, a, b):.3f}(adj)"
                  for a, b in ERAS))
print(f"  modern comparator {RATE_WIN}: obs {obs_era_rate(obs, *RATE_WIN):.3f} / "
      f"obs_adj {obs_adj_modern:.3f} mm/yr (T2-memo corrected basis)")

# pathological comparators (matched u_pre/s_r5 freedom) + d1d references
patho, patho_ref = {}, {}
for _, variant, oname, _ in CONFIGS_D1E:
    ref = d1d_rows[d1d_rows.label == f"C_both/ANCH/{variant}"].iloc[0]
    patho_ref[variant] = float(ref["flow_win"] + ref["flow_win_deficit"])
    th_p, fw_p = optimize_patho_d(variant, OBS_ADJ)
    patho[variant] = fw_p
    print(f"patho_d [{variant}]: flow{FLOW_WIN}={fw_p:.2f} "
          f"(d1d ref {patho_ref[variant]:.2f}, delta {fw_p - patho_ref[variant]:+.2f}) "
          f"u_pre={th_p['u_pre_mm']:.1f} s_r5={th_p['s_r5_mm']:.1f}")

rows = []
for sname, variant, oname, hind_names in CONFIGS_D1E:
    resv, anch = structures[sname], anchors[sname]
    print(f"\n== runs [{sname}/{variant}/{oname}] ==")
    for arm in ["ANCH", "MID", "FREE"]:
        th = optimize_arm_d(resv, variant, arm, anch, hind_names, OBS_ADJ)
        m = metrics_d(resv, th, variant, arm, patho[variant], patho_ref[variant],
                      hind_names, OBS_ADJ, label=f"{sname}/{arm}/{variant}")
        if m is None:
            print(f"  [{sname}/{arm}/{variant}] DEGENERATE")
            continue
        row, per, t = m
        rows.append(row)
        print(f"  [{row['label']:24s}] npass={row['npass']}/4 "
              f"[inv{'+' if row['g_inv'] else '-'} lec{'+' if row['g_lec'] else '-'} "
              f"lad{'+' if row['g_lad'] else '-'} spr{'+' if row['g_spread'] else '-'}] "
              f"deficit={row['flow_win_deficit']:6.2f} (d1dref {row['deficit_d1dref']:6.2f}) "
              f"ledger={row['s1900_inv_mm']:.1f}+{row['s_r5_mm']:.1f}+{row['u_pre_mm']:.1f}"
              f"={row['s1900_ledger_mm']:.1f} z={row['lec_z']:+.2f} "
              f"legacy={row['s1900_legacy_mm']:.1f}({'in' if row['g_s1900_legacy_box'] else 'OUT'}) "
              f"rate={row['rate_modern_hind']:.3f} (obs_adj {obs_adj_modern:.3f}) "
              f"U={row['u_mm']:.1f} delta={row['delta']:+.2f}({row['delta_sigmas']:.1f}s) "
              f"FEAS={row['feasible']}")

res = pd.DataFrame(rows)
os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
res.to_csv(OUT_CSV, index=False, float_format="%.5f")

# ---------------------------------------------------------------- verdict
print("\n=== D1e verdict (pre-registered: spec memo section 4) ===")
hl = res[res.label == "C_both/ANCH/unc_t5d"].iloc[0]
p1 = abs(hl.flow_win_deficit - P1_DEFICIT_REF) <= P1_TOL
print(f"  P1 ANCH deficit unchanged: {hl.flow_win_deficit:.3f} vs {P1_DEFICIT_REF} "
      f"+/- {P1_TOL}: {'CONFIRMED' if p1 else 'NOT CONFIRMED'}")
anchmid = res[res.arm.isin(['ANCH', 'MID'])]
p2 = bool((anchmid.npass == 4).all()) \
    and bool((anchmid.u_pre_mm > UPRE_BOUNDS_MM[0] + 0.5).all()) \
    and bool((anchmid.u_pre_mm < UPRE_BOUNDS_MM[1] - 0.5).all())
print(f"  P2 ledger interior + ANCH/MID 4/4: u_pre "
      f"{anchmid.u_pre_mm.min():.1f}-{anchmid.u_pre_mm.max():.1f} mm, s_r5 "
      f"{anchmid.s_r5_mm.min():.1f}-{anchmid.s_r5_mm.max():.1f} mm, npass "
      f"{sorted(anchmid.npass.unique())}: {'CONFIRMED' if p2 else 'NOT CONFIRMED'}")
fr = res[res.arm == "FREE"]
p3 = bool((fr.s1900_legacy_mm < 20).all()) and bool((~fr.g_spread).all())
print(f"  P3 FREE decoupled (legacy S1900 {fr.s1900_legacy_mm.min():.1f}-"
      f"{fr.s1900_legacy_mm.max():.1f} vs d1d 27-28; spread still fails): "
      f"{'CONFIRMED' if p3 else 'NOT CONFIRMED'}")
watch = res[res.label == "C_both/MID/unc_sx2"]
if len(watch):
    w = watch.iloc[0]
    print(f"  WATCH MID/sx2 deficit: {w.flow_win_deficit:.3f} (d1d {MID_SX2_WATCH}) "
          f"vs tol {FLOW_TOL} -> feasible={w.feasible}")
minimal = (hl.flow_win_deficit <= D1C_TAPER_DEFICIT) and (hl.delta_sigmas <= 1.0) \
    and hl.npass == 4
print(f"  MINIMAL BAR (<= {D1C_TAPER_DEFICIT}, delta <= 1 sigma, 4/4): "
      f"{'MET' if minimal else 'NOT MET'} | STRONG BAR (feasible): "
      f"{'MET' if bool(hl.feasible) else 'NOT MET (expected)'}")
print(f"  {int((res.feasible == True).sum())}/{len(res)} feasible")  # noqa: E712

# ---------------------------------------------------------------- figure
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(16.5, 4.8), constrained_layout=True)
axA, axB, axC = axes

# A: ledger waterfall (headline ANCH + MID/FREE markers)
axA.axhspan(LEC_MU_MM - LEC_SIG_MM, LEC_MU_MM + LEC_SIG_MM, color="tab:blue",
            alpha=0.18, label="datum 20+/-9 (1 sigma)")
axA.axhspan(LEC_MU_MM - 2 * LEC_SIG_MM, LEC_MU_MM + 2 * LEC_SIG_MM, color="tab:blue",
            alpha=0.07)
xpos = np.arange(len(res))
axA.bar(xpos, res.s1900_inv_mm, color="0.45", label="S_inv (SLOWP+FAST)")
axA.bar(xpos, res.s_r5_mm, bottom=res.s1900_inv_mm, color="tab:orange",
        label="S_r5 set-aside")
axA.bar(xpos, res.u_pre_mm, bottom=res.s1900_inv_mm + res.s_r5_mm,
        color="tab:green", label="U_pre set-aside")
axA.scatter(xpos, res.s1900_legacy_mm, marker="x", color="k", zorder=3,
            label="legacy S_all (old basis)")
axA.set_xticks(xpos)
axA.set_xticklabels([lb.replace("C_both/", "") for lb in res.label],
                    rotation=20, fontsize=7)
axA.set(ylabel="mm SLE (1850-1900)",
        title="D ledger: model + set-asides vs untouched datum")
axA.legend(fontsize=7)

# B: flow decomposition (headline)
resv = structures["C_both"]
thh = {f"kappa_{n}": hl[f"kappa_{n}"] for n in resv}
thh.update({f"nu_{n}": hl[f"nu_{n}"] for n in resv})
thh.update(sigma=hl["sigma"], rho=hl["rho"], delta=hl["delta"], u_mm=hl["u_mm"],
           u_pre_mm=hl["u_pre_mm"], s_r5_mm=hl["s_r5_mm"])
per_h = forward_all(resv, thh)
s_hind_h = per_h["SLOWP"] + per_h["FAST"]
F = unch_cum(hl["u_mm"], PROFILE_PRIMARY)
tgt = pd.Series(OBS_ADJ, index=fit_years)
oc = pd.Series(obs_corrected(OBS_ADJ, hl["delta"]), index=fit_years)
axB.plot(tgt.index, 10 * tgt.diff().rolling(11, center=True).mean(), color="k",
         lw=1.6, label="obs_adj flow (11-yr)")
axB.plot(oc.index, 10 * oc.diff().rolling(11, center=True).mean(), color="0.55",
         lw=1.0, ls="--", label=f"obs_adj t5d-corr ({hl['delta']:+.2f})")
axB.plot(years[1:], 1000 * np.diff(s_hind_h + F), color="tab:red", lw=1.5,
         label="model hindcast (SLOWP+FAST+F)")
axB.plot(years[1:], 1000 * np.diff(F), color="tab:green", lw=1.1,
         label=f"F_unch (U={hl['u_mm']:.0f}mm, taper)")
axB.plot(years[1:], 1000 * np.diff(per_h["R19"]), color="tab:purple", lw=1.0,
         ls="--", label="R19 (excluded from hindcast)")
axB.set(xlim=(1900, 2026), xlabel="year", ylabel="GSIC flow (mm SLE/yr)",
        title="headline C_both ANCH/unc_t5d - flow decomposition")
axB.legend(fontsize=7)

# C: era rates - obs vs corrected-obs vs model (the T2 emitter, visualized)
width = 0.2
xs = np.arange(len(ERAS))
obs_r = [obs_era_rate(OBS_ADJ, a, b) for a, b in ERAS]
corr_r = []
for (a, b), o in zip(ERAS, obs_r):
    dcorr = obs_era_rate(obs_corrected(OBS_ADJ, hl["delta"]), a, b)
    corr_r.append(dcorr - era_rate(F, a, b))
hind_r = [hl[f"rate_hind_{a}_{b}"] for a, b in ERAS]
tot_r = [hl[f"rate_tot_{a}_{b}"] for a, b in ERAS]
axC.bar(xs - 1.5 * width, obs_r, width, color="k", label="obs_adj")
axC.bar(xs - 0.5 * width, corr_r, width, color="0.6",
        label="obs_adj - delta - F (blocks' target)")
axC.bar(xs + 0.5 * width, hind_r, width, color="tab:red", label="model blocks")
axC.bar(xs + 1.5 * width, tot_r, width, color="tab:pink", label="model blocks + F")
axC.set_xticks(xs)
axC.set_xticklabels([f"{a}-{b}" for a, b in ERAS], fontsize=8)
axC.set(ylabel="mm SLE/yr", title="era rates: obs vs corrected vs model (headline)")
axC.legend(fontsize=7)

fig.suptitle(f"D1e - Option-D ledger (datum untouched; U_pre flat"
             f"[{UPRE_BOUNDS_MM[0]:.0f},{UPRE_BOUNDS_MM[1]:.0f}], S_r5 "
             f"N{SR5_PRIOR_MM}) | gate |z|<={LEC_Z_GATE} | commit {COMMIT}",
             fontsize=10)
os.makedirs(os.path.dirname(OUT_FIG), exist_ok=True)
fig.savefig(OUT_FIG, dpi=150)
print(f"\nWrote {os.path.relpath(OUT_CSV, REPO)}, {os.path.relpath(OUT_FIG, REPO)}")
