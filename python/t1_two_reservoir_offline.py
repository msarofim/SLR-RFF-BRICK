#!/usr/bin/env python3
"""T1 — offline two-reservoir-nu feasibility test (decision menu T1,
handoff_2026-08-07_extB3_falsified_modern_flow_tension.md §5).

Question: can a fast/slow split — Nauels-nu transient on a FAST pool, long-tau
linear relaxation on a SLOW pool holding most of the committed ice — decouple
the GlacierMIP3-committed ladder from the observed modern (GlaMBIE-scope) melt
rate, where the single-reservoir-nu law could not? Falsification standard from
the handoff: a config must (i) pass ALL 4 pre-registered gates (A2 inventory,
S(1900), GlacierMIP3 ladder, scenario spread) and (ii) fit 1980-2023 flow
within ~FLOW_TOL logL of the pathological (free single-N) optimum.

Structure (offline D0-style cell, no Julia surgery; extends the
d0e_nu_kappa_map pattern with an inner optimization per grid cell):
  transient P (primary) : S = S_f + S_s
      dS_f/dt = kappa*(phi*S_eq - S_f)*max(T - T_eq_f(S_f), 0)^nu   (Nauels-nu)
      dS_s/dt = ((1-phi)*S_eq - S_s)/tau_s                          (Mengel linear)
      T_eq_f = inverse of phi*S_eq at S_f (same formula as N with a -> phi*a).
      phi = fast share of equilibrium; nu=0*, phi=1 nests single-N.
  transient R (secondary): dS/dt = min(kappa*(S_eq-S)*exc^nu, RMAX) — explicit
      rate cap, the handoff's alternative device.
  S_eq fixed at the SC point (a, b, T_off re-solved per ladder anchor).

Anchors: 'pub' = full-RGI published GlacierMIP3 ladder (the extB3 gate);
't2'  = the excl-r5-incl-r19 scope-corrected ladder from
python/t2_gmip3_scope_anchor.py (exact per-experiment recompute). Both run.

Conventions: pre-1940 flow-target sigma x2 (the standing extB3b/c likelihood,
'--gsic-early-sigma-x2'); tau_s prior centered on the GlacierMIP3 global
response timescale 463 [216-805] yr (table S1a); flow criterion evaluated as
the MARGINAL AR(1) logL of the 1980-2023 window at each candidate's own fitted
(sigma, rho), compared to the pathological optimum's same-window value.
Ladder + scenario-spread gates evaluated at AMP_G = 1.8 with the calibrator's
splice convention (matching eval_chain_gates.py, NOT the D0 ampfit variant);
the SC solve keeps AMP_FIT for the historical slope conversion (D0 convention).

Outputs: outputs/t1_two_reservoir_offline.csv, figures/t1_two_reservoir_offline.png
"""
import os
import subprocess

import numpy as np
import pandas as pd
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import brentq, minimize
from scipy.stats import norm

np.seterr(over="ignore", under="ignore")   # logistic bound-transform saturates by design

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
SHOOTOUT = os.path.join(REPO, "python/d0_glacier_shootout.py")
OUT_CSV_T1 = os.path.join(REPO, "outputs/t1_two_reservoir_offline.csv")
OUT_FIG_T1 = os.path.join(REPO, "figures/t1_two_reservoir_offline.png")

src = open(SHOOTOUT).read().split(
    "# ------------------------------------------------------------------ run all cells")[0]
exec(src.replace('print(f"D0', 'pass # print(f"D0'))

COMMIT = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True).stdout.strip()

# ---------------------------------------------------------------- T1 constants
AMP_G = 1.8                    # ladder/scenario amp, calibrator convention (locked)
EARLY_SIGMA_X2_BEFORE = 1940   # pre-1940 flow-target sigma x2 (extB3b/c standing)
FLOW_WIN = (1980, 2023)        # the modern-flow criterion window (handoff §5 T1)
FLOW_TOL = 5.0                 # "within ~5 logL of the pathological optimum"
ERAS = [(1900, 1919), (1920, 1949), (1950, 1979), (1980, 1999), (2000, 2023)]
RMAX_BOUNDS = (2e-4, 5e-3)     # rate-cap arm: m SLE/yr (0.2-5 mm/yr)
# nu is NOT identified by the hindcast (D0) and a free optimizer rails it to 0,
# killing the spread gate — the T1 question is EXISTENCE, so nu is scanned:
PHI_GRID = [0.20, 0.30, 0.40, 0.50, 0.65, 0.80]
TAUS_GRID = [150., 300., 463., 700., 1000.]
NU_GRID_P = [0.5, 1.0, 1.5]
RATE_WIN = (2015, 2023)        # modern-rate diagnostic window (obs ~0.6 mm/yr)
TAUS_PRIOR = (463., 300.)      # GlacierMIP3 global response timescale S1a: 463 [216-805]
PHI_PRIOR = (0.30, 0.25)       # weak; mass-weighted fast share from resp-time data ~0.2-0.3
N_INNER_STARTS = 5
SEED_T1 = 2026

# ladder anchors: committed % of 2020 mass at global {1.2,1.5,2,3} K.
# 'pub' = Zekollari 2025 full-RGI (the extB3 gate constants, d0_glacier_shootout).
# 't2'  = excl-r5-incl-r19 scope, exact per-experiment recompute
#         (python/t2_gmip3_scope_anchor.py -> outputs/t2_gmip3_scope_anchor.csv).
T2_CSV = os.path.join(REPO, "outputs/t2_gmip3_scope_anchor.csv")
ANCHORS = {
    "pub": dict(central={1.2: 39, 1.5: 47, 2.0: 63, 3.0: 77},
                likely={1.2: (15, 55), 1.5: (20, 64), 2.0: (43, 76), 3.0: (60, 85)}),
}


def load_t2_anchor():
    if not os.path.exists(T2_CSV):
        return None
    t2 = pd.read_csv(T2_CSV)
    if "validation_pass" in t2 and not bool(t2["validation_pass"].iloc[0]):
        print("WARNING: t2 exact-pipeline validation FAILED -> ignoring t2 anchor")
        return None
    scope = t2[t2.scope.astype(str).str.startswith("excl_r")]
    if "method" in scope:
        scope = scope[scope.method == "anchor_final"]
    scope = scope[scope.level_K.isin(GMIP3_LEVELS) & scope.central.notna()]
    if len(scope) < len(GMIP3_LEVELS):
        return None
    g = scope.set_index("level_K")
    return dict(central={L: float(g.loc[L, "central"]) for L in GMIP3_LEVELS},
                likely={L: (float(g.loc[L, "lo"]), float(g.loc[L, "hi"]))
                        for L in GMIP3_LEVELS})


_t2 = load_t2_anchor()
if _t2 is not None:
    ANCHORS["t2"] = _t2
else:
    print("WARNING: t2 scope anchor CSV missing/incomplete -> running 'pub' only")

rng_t1 = np.random.default_rng(SEED_T1)
# hindcast driver in the CALIBRATOR convention (AMP_G tail splice, 2014-2024
# anchor) — differs from DRIVERS["Tglac"] (ampfit tail) only in 2025-26
Tarr = extend_obs(tglac_obs, fair_rb, AMP_G).to_numpy()[:-1]

# pre-1940 sigma x2 on the flow target (overrides the shootout's uninflated eps)
eps_t1 = eps * np.where(fit_years < EARLY_SIGMA_X2_BEFORE, 2.0, 1.0)

# ---------------------------------------------------------------- SC point per anchor


def solve_sc(com12):
    """d0_final_selfconsistent solve: slope@0 + inventory + committed@+1.2K."""
    S2000_OBS = 0.093
    S2020_OBS = 0.107
    sc_a = INV_V + S2000_OBS
    slope_glac = 0.133 / AMP_FIT
    tgt_seq = com12 * (sc_a - S2020_OBS) + S2020_OBS

    def f(toff):
        b = -np.log(1 - tgt_seq / sc_a) / (AMP_FIT * 1.2 - toff)
        return sc_a * b * np.exp(b * toff) - slope_glac

    toff = brentq(f, -1.9, -0.2)
    b = -np.log(1 - tgt_seq / sc_a) / (AMP_FIT * 1.2 - toff)
    return dict(a=sc_a, b=b, T_off=toff)


# ---------------------------------------------------------------- integrators
def integrate_P(Tarr_, a, b, T_off, phi, tau_s, kappa, nu, n=None):
    """Two-reservoir: Nauels-nu fast pool (share phi) + linear slow pool."""
    n = len(Tarr_) + 1 if n is None else n
    out = np.empty(n)
    a_f = phi * a
    sf = ss = 0.0
    out[0] = 0.0
    for k in range(n - 1):
        seq = a * (1 - np.exp(-b * (Tarr_[k] - T_off)))
        if a_f > 0:
            frac_left = max(1.0 - sf / a_f, 1e-12)
            T_eq = T_off - np.log(frac_left) / b
            exc = max(Tarr_[k] - T_eq, 0.0)
            mult = min(kappa * exc ** nu, 1.0)
            sf += mult * (phi * seq - sf)
        ss += ((1 - phi) * seq - ss) / tau_s
        out[k + 1] = sf + ss
    return out


def integrate_R(Tarr_, a, b, T_off, kappa, nu, rmax, n=None):
    """Single reservoir with an explicit melt-rate cap rmax (m SLE/yr)."""
    n = len(Tarr_) + 1 if n is None else n
    out = np.empty(n)
    S = 0.0
    out[0] = 0.0
    for k in range(n - 1):
        seq = a * (1 - np.exp(-b * (Tarr_[k] - T_off)))
        frac_left = max(1.0 - S / a, 1e-12)
        T_eq = T_off - np.log(frac_left) / b
        exc = max(Tarr_[k] - T_eq, 0.0)
        dS = min(kappa * exc ** nu * (seq - S), rmax) if seq > S else \
            max(kappa * exc ** nu * (seq - S), -rmax)
        S += dS
        out[k + 1] = S
    return out


T1_PNAMES = {"P": ["phi", "tau_s", "kappa", "nu", "sigma", "rho"],
             "R": ["kappa", "nu", "rmax", "sigma", "rho"],
             "N1": ["kappa", "nu", "sigma", "rho"]}
T1_BOUNDS = dict(BOUNDS, phi=(0.02, 0.98), tau_s=(80., 2000.), rmax=RMAX_BOUNDS)


def forward_t1(tr, Tarr_, sc, th, n=None):
    if tr == "P":
        return integrate_P(Tarr_, sc["a"], sc["b"], sc["T_off"], th["phi"],
                           th["tau_s"], th["kappa"], th["nu"], n=n)
    if tr == "R":
        return integrate_R(Tarr_, sc["a"], sc["b"], sc["T_off"], th["kappa"],
                           th["nu"], th["rmax"], n=n)
    return integrate_N(Tarr_, sc["a"], sc["b"], sc["T_off"], th["kappa"],
                       th["nu"], n=n)


# ---------------------------------------------------------------- likelihood
def flow_logl_window(m_cm, sig, rho_, y0, y1, eps_vec):
    sel = (fit_years >= y0) & (fit_years <= y1)
    r = (m_cm[yfit_idx] - obs)[sel]
    nwin = sel.sum()
    Hw = np.abs(np.subtract.outer(np.arange(nwin), np.arange(nwin)))
    Sig = (sig ** 2 / (1 - rho_ ** 2)) * rho_ ** Hw + np.diag(eps_vec[sel] ** 2)
    try:
        cf = cho_factor(Sig)
    except np.linalg.LinAlgError:
        return -np.inf
    logdet = 2 * np.sum(np.log(np.diag(cf[0])))
    return -0.5 * (nwin * np.log(2 * np.pi) + logdet + r @ cho_solve(cf, r))


def loglik_t1(tr, sc, th):
    s_raw = forward_t1(tr, Tarr, sc, th)
    m_cm = 100 * (s_raw - s_raw[ybase].mean())
    ll_flow = flow_logl_window(m_cm, th["sigma"], th["rho"],
                               fit_years[0], fit_years[-1], eps_t1)
    if not np.isfinite(ll_flow):
        return None
    ll_inv = norm.logpdf(sc["a"] - s_raw[i_inv], INV_V, INV_SIG)
    ll_lec = norm.logpdf(s_raw[i1900], LEC_MU, LEC_SIG)
    ll_pr = 0.0
    if tr in ("P",):
        ll_pr += norm.logpdf(th["phi"], *PHI_PRIOR)
        ll_pr += norm.logpdf(th["tau_s"], *TAUS_PRIOR)
    if "kappa" in th:
        ll_pr += norm.logpdf(np.log(th["kappa"]), *KAPPA_LOGPRIOR)
    if "nu" in th:
        ll_pr += norm.logpdf(th["nu"], *NU_PRIOR)
    return dict(ll_flow=ll_flow, ll_inv=ll_inv, ll_lec=ll_lec, ll_prior=ll_pr,
                logJ=ll_flow + ll_inv + ll_lec + ll_pr, s_raw=s_raw, m_cm=m_cm)


def optimize_t1(tr, sc, free_names, fixed, seeds, nstart=N_INNER_STARTS):
    def mk(z):
        th = dict(fixed)
        for nm, zz in zip(free_names, z):
            lo, hi = T1_BOUNDS[nm]
            th[nm] = lo + (hi - lo) / (1 + np.exp(-zz))
        return th

    def neg(z):
        t = loglik_t1(tr, sc, mk(z))
        return np.inf if t is None else -t["logJ"]

    starts = []
    for sd in seeds:
        z = []
        for nm in free_names:
            lo, hi = T1_BOUNDS[nm]
            x = np.clip((sd[nm] - lo) / (hi - lo), 1e-4, 1 - 1e-4)
            z.append(np.log(x / (1 - x)))
        starts.append(np.array(z))
    base = list(starts)
    while len(starts) < nstart:
        starts.append(base[rng_t1.integers(len(base))]
                      + rng_t1.normal(0, 0.6, len(free_names)))
    best = None
    for z0 in starts:
        r = minimize(neg, z0, method="Nelder-Mead",
                     options=dict(xatol=1e-7, fatol=1e-9, maxiter=5000, maxfev=8000))
        if best is None or r.fun < best.fun:
            best = r
    r = minimize(neg, best.x, method="Nelder-Mead",
                 options=dict(xatol=1e-8, fatol=1e-10, maxiter=5000, maxfev=8000))
    return mk((r if r.fun < best.fun else best).x)


# ---------------------------------------------------------------- evaluation
def scenario_ds2100_t1(tr, sc, th):
    out = {}
    proj_years = np.arange(Y0, 2151)
    for s, g in ssp_rb.items():
        drv = extend_obs(tglac_obs, g, AMP_G, idx=proj_years)
        s_raw = forward_t1(tr, drv.to_numpy()[:-1], sc, th, n=len(proj_years))
        sb = (proj_years >= PROJ_BASE[0]) & (proj_years <= PROJ_BASE[1])
        out[s] = 100 * (s_raw[proj_years == 2100][0] - s_raw[sb].mean())
    return out


def metrics_t1(tr, anchor_name, sc, th, patho_flow_win):
    t = loglik_t1(tr, sc, th)
    if t is None:
        return None
    s = t["s_raw"]
    anc = ANCHORS[anchor_name]
    com, sens = ladder(sc | th, s[i2020], AMP_G)
    ds = scenario_ds2100_t1(tr, sc, th)
    spread = ds["ssp585"] - ds["ssp126"]
    s1900 = 1000 * s[i1900]
    invz = (sc["a"] - s[i_inv] - INV_V) / INV_SIG
    flow_win = flow_logl_window(t["m_cm"], th["sigma"], th["rho"],
                                FLOW_WIN[0], FLOW_WIN[1], eps_t1)
    era_ll = {f"flow_{a}_{b}": flow_logl_window(t["m_cm"], th["sigma"], th["rho"],
                                                a, b, eps_t1) for a, b in ERAS}
    ir0 = np.searchsorted(years, RATE_WIN[0])
    ir1 = np.searchsorted(years, RATE_WIN[1])
    rate_modern = 1000 * (s[ir1] - s[ir0]) / (RATE_WIN[1] - RATE_WIN[0])
    gates = dict(g_s1900=10 <= s1900 <= 30, g_inv=abs(invz) < 1,
                 g_lad=all(anc["likely"][L][0] <= com[L] <= anc["likely"][L][1]
                           for L in GMIP3_LEVELS),
                 g_spread=4.5 <= spread <= 13.5)
    return dict(transient=tr, anchor=anchor_name,
                **{k: th.get(k, np.nan) for k in
                   ["phi", "tau_s", "kappa", "nu", "rmax", "sigma", "rho"]},
                logJ=t["logJ"], ll_flow=t["ll_flow"], ll_prior=t["ll_prior"],
                flow_win=flow_win, flow_win_deficit=patho_flow_win - flow_win,
                rate_modern_mm_yr=rate_modern, **era_ll,
                S1900_mm=s1900, inv_z=invz, S2020_mm=1000 * s[i2020],
                **{f"com{str(L).replace('.', 'p')}": com[L] for L in GMIP3_LEVELS},
                sens_mm=sens, ds126=ds["ssp126"], ds245=ds["ssp245"],
                ds585=ds["ssp585"], spread=spread, **gates,
                npass=sum(gates.values()),
                feasible=(sum(gates.values()) == 4
                          and (patho_flow_win - flow_win) <= FLOW_TOL))


# ---------------------------------------------------------------- run
print(f"T1 two-reservoir offline | commit={COMMIT} | amp_fit={AMP_FIT:.3f} | "
      f"pre-{EARLY_SIGMA_X2_BEFORE} sigma x2 | flow window {FLOW_WIN} tol {FLOW_TOL}")

# pathological reference: FREE single-N under the same (sigma x2) objective.
# a/b/T_off free too -> where the likelihood alone wants to go (arm-B analogue).
PATHO_FREE = ["a", "b", "T_off", "kappa", "nu", "sigma", "rho"]


def optimize_patho():
    def mk(z):
        th = {}
        for nm, zz in zip(PATHO_FREE, z):
            lo, hi = T1_BOUNDS[nm]
            th[nm] = lo + (hi - lo) / (1 + np.exp(-zz))
        return th

    def neg(z):
        th = mk(z)
        sc = dict(a=th["a"], b=th["b"], T_off=th["T_off"])
        t = loglik_t1("N1", sc, th)
        if t is None:
            return np.inf
        # priors on a/b/T_off as in the shootout objective
        pr = sum(norm.logpdf(th[p], *PRIORS[p]) for p in ("a", "b", "T_off"))
        return -(t["logJ"] + pr)

    seeds = [dict(a=0.298, b=0.320, T_off=-2.0, kappa=0.0085, nu=0.10,
                  sigma=0.005, rho=0.05),
             dict(a=0.33, b=0.35, T_off=-1.8, kappa=0.006, nu=0.12,
                  sigma=0.01, rho=0.3),
             dict(a=0.45, b=0.52, T_off=-1.10, kappa=0.0106, nu=0.15,
                  sigma=0.04, rho=0.70)]
    starts = []
    for sd in seeds:
        starts.append(np.array([np.log(np.clip((sd[nm] - T1_BOUNDS[nm][0])
                                               / (T1_BOUNDS[nm][1] - T1_BOUNDS[nm][0]),
                                               1e-4, 1 - 1e-4)
                                       / (1 - np.clip((sd[nm] - T1_BOUNDS[nm][0])
                                                      / (T1_BOUNDS[nm][1] - T1_BOUNDS[nm][0]),
                                                      1e-4, 1 - 1e-4)))
                                for nm in PATHO_FREE]))
    base = list(starts)
    while len(starts) < 8:
        starts.append(base[rng_t1.integers(len(base))]
                      + rng_t1.normal(0, 0.6, len(PATHO_FREE)))
    best = None
    for z0 in starts:
        r = minimize(neg, z0, method="Nelder-Mead",
                     options=dict(xatol=1e-7, fatol=1e-9, maxiter=8000, maxfev=12000))
        if best is None or r.fun < best.fun:
            best = r
    return mk(best.x)


th_patho = optimize_patho()
sc_patho = dict(a=th_patho["a"], b=th_patho["b"], T_off=th_patho["T_off"])
t_patho = loglik_t1("N1", sc_patho, th_patho)
patho_flow_win = flow_logl_window(t_patho["m_cm"], th_patho["sigma"],
                                  th_patho["rho"], FLOW_WIN[0], FLOW_WIN[1], eps_t1)
print(f"\npathological free-N optimum: a={th_patho['a']:.3f} b={th_patho['b']:.3f} "
      f"T_off={th_patho['T_off']:.3f} kappa={th_patho['kappa']:.4f} "
      f"nu={th_patho['nu']:.2f} | flow(full)={t_patho['ll_flow']:.2f} "
      f"flow{FLOW_WIN}={patho_flow_win:.2f}")

rows = []
for anchor_name in ANCHORS:
    com12 = ANCHORS[anchor_name]["central"][1.2] / 100
    sc = solve_sc(com12)
    print(f"\n=== anchor '{anchor_name}' (com12={100 * com12:.1f}%): SC point "
          f"a={sc['a']:.3f} b={sc['b']:.3f} T_off={sc['T_off']:.3f} ===")

    # single-N reference at this SC (the falsified baseline, nu=1-ish)
    for nu_fix in [0.5, 1.0]:
        th = optimize_t1("N1", sc, ["kappa", "sigma", "rho"], dict(nu=nu_fix),
                         [dict(kappa=0.006, sigma=0.03, rho=0.6),
                          dict(kappa=0.002, sigma=0.02, rho=0.4)])
        m = metrics_t1("N1", anchor_name, sc, th, patho_flow_win)
        m["arm"] = f"N1_nu{nu_fix}"
        rows.append(m)
        print(f"  [N1 nu={nu_fix}] npass={m['npass']} "
              f"flow-deficit={m['flow_win_deficit']:.1f} spread={m['spread']:.1f}")

    # P grid: (phi, tau_s, nu fixed) x inner opt (kappa, sigma, rho)
    for phi in PHI_GRID:
        for tau_s in TAUS_GRID:
            for nu_fix in NU_GRID_P:
                th = optimize_t1("P", sc, ["kappa", "sigma", "rho"],
                                 dict(phi=phi, tau_s=tau_s, nu=nu_fix),
                                 [dict(kappa=0.012 * 2.0 ** (-nu_fix),
                                       sigma=0.03, rho=0.6),
                                  dict(kappa=0.05 * 2.0 ** (-nu_fix),
                                       sigma=0.02, rho=0.4)], nstart=4)
                m = metrics_t1("P", anchor_name, sc, th, patho_flow_win)
                m["arm"] = "P_grid"
                rows.append(m)
    ngrid = [r for r in rows if r and r.get("arm") == "P_grid"
             and r.get("anchor") == anchor_name]
    n4 = [r for r in ngrid if r["npass"] == 4]
    best4 = min(n4, key=lambda r: r["flow_win_deficit"]) if n4 else None
    print(f"  [P grid] {len(n4)}/{len(ngrid)} cells pass 4/4 gates; "
          + (f"best deficit {best4['flow_win_deficit']:.1f} at phi={best4['phi']:.2f}"
             f" tau_s={best4['tau_s']:.0f} nu={best4['nu']:.1f} "
             f"rate={best4['rate_modern_mm_yr']:.2f} mm/yr" if best4 else "none"))

    # P free: all six free
    th = optimize_t1("P", sc, T1_PNAMES["P"], {},
                     [dict(phi=0.2, tau_s=463., kappa=0.02, nu=1.0,
                           sigma=0.03, rho=0.6),
                      dict(phi=0.1, tau_s=800., kappa=0.05, nu=0.8,
                           sigma=0.02, rho=0.5),
                      dict(phi=0.4, tau_s=250., kappa=0.01, nu=1.5,
                           sigma=0.02, rho=0.5)], nstart=8)
    m = metrics_t1("P", anchor_name, sc, th, patho_flow_win)
    m["arm"] = "P_free"
    rows.append(m)
    print(f"  [P free] phi={th['phi']:.2f} tau_s={th['tau_s']:.0f} "
          f"kappa={th['kappa']:.4f} nu={th['nu']:.2f} npass={m['npass']} "
          f"flow-deficit={m['flow_win_deficit']:.1f} spread={m['spread']:.1f} "
          f"feasible={m['feasible']}")

    # R free: rate cap
    th = optimize_t1("R", sc, T1_PNAMES["R"], {},
                     [dict(kappa=0.006, nu=1.0, rmax=0.001, sigma=0.03, rho=0.6),
                      dict(kappa=0.02, nu=0.5, rmax=0.0007, sigma=0.02, rho=0.4)],
                     nstart=6)
    m = metrics_t1("R", anchor_name, sc, th, patho_flow_win)
    m["arm"] = "R_free"
    rows.append(m)
    print(f"  [R free] kappa={th['kappa']:.4f} nu={th['nu']:.2f} "
          f"rmax={1000 * th['rmax']:.2f} mm/yr npass={m['npass']} "
          f"flow-deficit={m['flow_win_deficit']:.1f} spread={m['spread']:.1f} "
          f"feasible={m['feasible']}")

res = pd.DataFrame([r for r in rows if r is not None])
os.makedirs(os.path.dirname(OUT_CSV_T1), exist_ok=True)
res.to_csv(OUT_CSV_T1, index=False, float_format="%.5f")

# ---------------------------------------------------------------- verdict + figure
print("\n=== T1 verdict ===")
for anchor_name in ANCHORS:
    sub = res[(res.anchor == anchor_name)]
    feas = sub[sub.feasible == True]  # noqa: E712
    print(f"  anchor '{anchor_name}': {len(feas)}/{len(sub)} configs feasible "
          f"(4/4 gates AND flow{FLOW_WIN} within {FLOW_TOL} of pathological)")
    if len(feas):
        best = feas.sort_values("flow_win_deficit").iloc[0]
        print(f"    best: {best['arm']} {best['transient']} phi={best['phi']:.2f} "
              f"tau_s={best['tau_s']:.0f} kappa={best['kappa']:.4f} "
              f"nu={best['nu']:.2f} deficit={best['flow_win_deficit']:.1f} "
              f"spread={best['spread']:.1f} S1900={best['S1900_mm']:.1f}")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.6), constrained_layout=True)
axA, axB, axC = axes
MARK = {"N1_nu0.5": "^", "N1_nu1.0": "v", "P_grid": "o", "P_free": "*", "R_free": "s"}
COLA = {"pub": "tab:red", "t2": "tab:blue"}
for _, r in res.iterrows():
    axA.scatter(r["flow_win_deficit"], r["npass"],
                marker=MARK.get(r["arm"], "o"), s=90 if r["arm"] != "P_grid" else 26,
                color=COLA.get(r["anchor"], "k"),
                alpha=0.9 if r["arm"] != "P_grid" else 0.45)
axA.axvline(FLOW_TOL, color="k", ls=":", lw=1)
axA.axhline(4, color="k", ls=":", lw=1)
axA.set(xlabel=f"flow {FLOW_WIN[0]}-{FLOW_WIN[1]} logL deficit vs pathological",
        ylabel="gates passed (of 4)",
        title="feasibility frontier (upper-left box = T1 pass)")
hnd = [plt.Line2D([], [], marker=m, ls="", color="k", label=a)
       for a, m in MARK.items()]
hnd += [plt.Line2D([], [], marker="o", ls="", color=c, label=f"anchor {a}")
        for a, c in COLA.items() if a in ANCHORS]
axA.legend(handles=hnd, fontsize=7)

P = res[(res.arm == "P_grid") & (res.anchor == list(ANCHORS)[-1])]
if len(P):
    # per (phi, tau_s) cell: best deficit among 4/4-gate nu variants, else NaN
    P4 = P[P.npass == 4]
    piv = P4.pivot_table(index="tau_s", columns="phi",
                         values="flow_win_deficit", aggfunc="min")
    piv = piv.reindex(index=TAUS_GRID, columns=PHI_GRID)
    im = axB.pcolormesh(piv.columns, piv.index, piv.values, shading="nearest",
                        cmap="viridis_r")
    fig.colorbar(im, ax=axB, label="best 4/4-gate flow-window deficit")
    npmax = P.groupby(["tau_s", "phi"]).npass.max()
    for (tau_s, phi), np_ in npmax.items():
        axB.text(phi, tau_s, f"{int(np_)}", ha="center", va="center",
                 color="tab:orange" if np_ == 4 else "w",
                 fontsize=8, fontweight="bold")
    axB.set(xlabel="phi (fast share)", ylabel="tau_s (yr)",
            title=f"P grid, anchor '{list(ANCHORS)[-1]}' — best-nu deficit "
                  "(label = max gates over nu)")

for _, r in res[res.arm.isin(["P_free", "R_free", "N1_nu1.0"])].iterrows():
    axC.scatter(r["spread"], r["S1900_mm"], marker=MARK[r["arm"]], s=80,
                color=COLA.get(r["anchor"], "k"))
axC.axvspan(4.5, 13.5, color="tab:red", alpha=0.08)
axC.axhspan(10, 30, color="tab:green", alpha=0.10)
axC.set(xlabel="SSP126-585 spread @2100 (cm)", ylabel="S(1900) mm",
        title="spread vs S(1900) (shaded = gates)")
fig.suptitle(f"T1 offline two-reservoir-nu test at SC S_eq | commit {COMMIT} | "
             f"pre-{EARLY_SIGMA_X2_BEFORE} sigma x2 | tol {FLOW_TOL} logL",
             fontsize=10)
os.makedirs(os.path.dirname(OUT_FIG_T1), exist_ok=True)
fig.savefig(OUT_FIG_T1, dpi=150)
print(f"\nWrote {os.path.relpath(OUT_CSV_T1, REPO)} and {os.path.relpath(OUT_FIG_T1, REPO)}")
