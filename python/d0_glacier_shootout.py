#!/usr/bin/env python3
"""
D0 — offline glacier structural shootout (handoff_2026-08-06 §3), BEFORE any
Julia surgery or MCMC.

Cells = {transient structure} x {driver}:
  transient M = current Mengel 2-tau relaxation  (params a, b, T_off, f, tau_f, tau_s)
  transient N = Nauels 2017 Eq.3 single-reservoir dS/dt = kappa*(S_eq-S)*(T-T_eq(S))_+^nu
                (params a, b, T_off, kappa, nu; nu=0 == Mengel single-tau, kappa=1/tau;
                 positive-part clamp on the temperature excess — Nauels does not state a
                 convention, non-integer nu forces it; verified Table 2 calibrated values
                 kappa 0.0079-0.0131, nu 0.096-0.445 vs smooth CMIP5-forced Marzeion
                 projections, so nu>1 has NO published-value precedent, only the FORM
                 (FRISIA p=1.5 is the published >1 exponent precedent))
  driver Gfair = fair_mean_gmst_ssp245harm (the calibrator forcing; smooth model mean)
  driver Gobs  = HadCRUT5 analysis global annual (obs; tests obs-variability alone)
  driver Tglac = t_glac_hadcrut5.csv (glacier-area-weighted obs T; the ETCW driver,
                 Option D)  [Gobs column isolates "obs wiggles" from "regional shape"]

All drivers re-baselined to 1850-1900 = 0 inside this script (report notes the
frame shift vs the calibrator's raw gmst_C frame).

Joint objective per cell (maximized, Nelder-Mead multi-start):
  GSIC flow AR(1) heteroscedastic logL, years 1900-2023, sigma/rho FITTED
  + A2 inventory     a - S_raw(2000)      ~ N(0.290, 0.060)   [calibrate_mcmc_ext.jl]
  + A2b Leclercq     S_raw(1900)-S_raw(1850) ~ N(0.020, 0.009)
  + calibrator priors on a, b, T_off (+ f, tau_f, tau_s for M; weak lognormal/normal
    priors for kappa, nu — Nauels Table-2-informed, deliberately wide)
GlacierMIP3 ladder + scenario spread are EVALUATION-ONLY gates (never in the
objective), per Marcus's standing ruling.

Pre-registered gates (handoff §3): inventory |z|<~1; S(1900) in 10-30 mm;
GlacierMIP3 committed ladder inside likely ranges unforced; params off bounds;
SSP scenario spread @2100 in the FACTS/AR6 family.

Outputs: outputs/d0_glacier_shootout.csv, figures/d0_glacier_shootout.png,
console verdict table.
"""
import os
import subprocess

import numpy as np
import pandas as pd
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import minimize
from scipy.stats import norm

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
GMST_FAIR = os.path.join(REPO, "data/observations/fair_mean_gmst_ssp245harm.csv")
TGLAC = os.path.join(REPO, "data/observations/t_glac_hadcrut5.csv")
TARGETS = os.path.join(REPO, "outputs/recalib_targets_ext.csv")
SSP_FILES = {s: os.path.join(REPO, f"data/observations/fair_mean_gmst_{s}.csv")
             for s in ["ssp126", "ssp245", "ssp585"]}
OUT_CSV = os.path.join(REPO, "outputs/d0_glacier_shootout.csv")
OUT_FIG = os.path.join(REPO, "figures/d0_glacier_shootout.png")

Y0, Y1 = 1850, 2026            # calibrator model window
BASE0, BASE1 = 1995, 2005      # GSIC target reref window (cm anomalies)
FRAME0, FRAME1 = 1850, 1900    # driver anomaly frame used throughout this script
FIT_START = 1900
EPS_FLOOR_CM = 0.05
INV_V, INV_SIG, INV_YEAR = 0.290, 0.060, 2000          # A2 (calibrate_mcmc_ext.jl)
LEC_MU, LEC_SIG = 0.020, 0.009                         # A2b Leclercq S(1900)-S(1850)
S2020_YEAR = 2020                                      # GlacierMIP3 denominator year
GMIP3_LEVELS = [1.2, 1.5, 2.0, 3.0]                    # global K rel 1850-1900
# SCOPE-CORRECTED anchors (Marcus 2026-08-07): excl-r5-incl-r19 scope, from
# python/t2_gmip3_scope_anchor.py (validated replication of Zekollari 2025 /
# Zenodo 15046588; outputs/t2_gmip3_scope_anchor.csv method=anchor_final;
# notes/handoff_2026-08-07_t2_scope_anchor_t1_two_reservoir.md §1).
# Published full-RGI values (gates as originally pre-registered, superseded):
#   central {1.2: 39, 1.5: 47, 2.0: 63, 3.0: 77}
#   likely  {1.2: (15,55), 1.5: (20,64), 2.0: (43,76), 3.0: (60,85)}; sens 85
GMIP3_LIKELY = {1.2: (11.8, 54.0), 1.5: (17.2, 63.2),
                2.0: (41.5, 75.5), 3.0: (58.5, 83.9)}
GMIP3_CENTRAL = {1.2: 37.4, 1.5: 46.3, 2.0: 63.0, 3.0: 75.5}
GMIP3_SENS_MM = 95                                     # committed 1.5->3K, mm SLE
#   (scope raw-Gt basis; full-RGI raw 109, S1b BSL-corrected 98 — old 85 was low)
S1900_GATE_MM = (10.0, 30.0)
PROJ_BASE = (1995, 2014)                               # AR6-style baseline for dS@2100
AR6_GLAC_2100 = {"ssp126": 9.0, "ssp245": 12.0, "ssp585": 18.0}   # cm (memo B3)
AMP_VARIANTS = {"ampfit": None, "amp1.8": 1.8}         # None -> through-origin fit below
AMP_FIT_WIN = (1901, 2024)
SPLICE_ANCHOR_N = 11                                   # yrs for anchor-preserving splice
N_STARTS = 12
SEED = 2026

# parameter bounds (calibrate_mcmc_ext.jl for the M block; kappa/nu D0 choices)
BOUNDS = dict(a=(0.25, 0.70), b=(0.15, 1.20), T_off=(-2.00, -0.10),
              f=(0.02, 0.98), tau_f=(5., 80.), tau_s=(80., 800.),
              kappa=(1e-4, 0.5), nu=(0.0, 4.0),
              sigma=(0.005, 0.5), rho=(0.0, 0.99))
PRIORS = dict(a=(0.45, 0.08), b=(0.52, 0.25), T_off=(-1.00, 0.50),
              f=(0.50, 0.30), tau_f=(40., 30.), tau_s=(300., 200.))
KAPPA_LOGPRIOR = (np.log(0.0106), 1.5)   # Nauels Table 2 mean-set, very wide
NU_PRIOR = (1.0, 1.5)                    # wide; spans Nauels 0.08-0.45 and FRISIA 1.5

COMMIT = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True).stdout.strip()
rng = np.random.default_rng(SEED)

# ------------------------------------------------------------------ drivers
years = np.arange(Y0, Y1 + 1)

def rebase(s):
    return s - s.loc[FRAME0:FRAME1].mean()

fair = pd.read_csv(GMST_FAIR).set_index("year")["gmst_C"]
FRAME_SHIFT_FAIR = fair.loc[FRAME0:FRAME1].mean()      # for back-conversion of T_off
fair_rb = rebase(fair)

tg = pd.read_csv(TGLAC).set_index("year")
tglac_obs = tg["t_glac_C"]                             # already rel 1850-1900
gobs = tg["gmst_hadcrut5_C"]

sel_amp = (tg.index >= AMP_FIT_WIN[0]) & (tg.index <= AMP_FIT_WIN[1])
AMP_FIT = float((tglac_obs[sel_amp] * gobs[sel_amp]).sum() / (gobs[sel_amp] ** 2).sum())
AMP_VARIANTS["ampfit"] = AMP_FIT

def extend_obs(series, scen_gmst_rb, amp, idx=None):
    """Anchor-preserving splice of amp*scenario-GMST onto an obs series' tail."""
    idx = years if idx is None else idx
    out = series.reindex(idx)
    last = int(series.index.max())
    anchor_years = np.arange(last - SPLICE_ANCHOR_N + 1, last + 1)
    off = series.loc[anchor_years].mean() - amp * scen_gmst_rb.loc[anchor_years].mean()
    missing = idx[idx > last]
    out.loc[missing] = amp * scen_gmst_rb.loc[missing] + off
    return out

# historical drivers on the model window (fill 2025-26 tails from ssp245harm)
DRIVERS = {
    "Gfair": fair_rb.reindex(years),
    "Gobs": extend_obs(gobs, fair_rb, 1.0),
    "Tglac": extend_obs(tglac_obs, fair_rb, AMP_FIT),
}
for k, v in DRIVERS.items():
    assert not v.isna().any(), f"driver {k} has gaps in {Y0}-{Y1}"

ssp_rb = {}
for s, fpath in SSP_FILES.items():
    g = pd.read_csv(fpath).set_index("year")["gmst_C"]
    ssp_rb[s] = rebase(g)

# ------------------------------------------------------------------ targets
tgt = pd.read_csv(TARGETS).set_index("year")
gsic_ok = tgt.index[(tgt.index >= FIT_START) & tgt["gsic"].notna()]
fit_years = np.arange(gsic_ok.min(), gsic_ok.max() + 1)
assert np.all(np.isin(fit_years, gsic_ok)), "GSIC target year gap"
obs = tgt.loc[fit_years, "gsic"].to_numpy()
eps = np.maximum((tgt.loc[fit_years, "gsic_hi"] - tgt.loc[fit_years, "gsic_lo"]).to_numpy()
                 / (2 * 1.645), EPS_FLOOR_CM)
nfit = len(fit_years)
H = np.abs(np.subtract.outer(np.arange(nfit), np.arange(nfit)))

ybase = (years >= BASE0) & (years <= BASE1)
yfit_idx = np.searchsorted(years, fit_years)
i1900 = np.searchsorted(years, 1900)
i_inv = np.searchsorted(years, INV_YEAR)
i2020 = np.searchsorted(years, S2020_YEAR)

# ------------------------------------------------------------------ forward models
def integrate_M(Tarr, a, b, T_off, f, tau_f, tau_s, n=None):
    n = len(Tarr) + 1 if n is None else n
    out = np.empty(n)
    sf = ss = 0.0
    out[0] = 0.0
    for k in range(n - 1):
        seq = a * (1 - np.exp(-b * (Tarr[k] - T_off)))
        sf += (f * seq - sf) / tau_f
        ss += ((1 - f) * seq - ss) / tau_s
        out[k + 1] = sf + ss
    return out

## Regrowth runs at 1/R of the melt rate. Must equal GIC_REGROW_R in
## glaciers_nu3_component.jl -- validate_glaciers_nu3.jl compares the two at 1e-9.
GIC_REGROW_R = 1.0


def integrate_N(Tarr, a, b, T_off, kappa, nu, n=None):
    n = len(Tarr) + 1 if n is None else n
    out = np.empty(n)
    S = 0.0
    out[0] = 0.0
    for k in range(n - 1):
        # FLOOR + BOUNDED REGROWTH (2026-08-31). Mirrors glaciers_nu3_component.jl
        # `_nu_step` exactly -- this function is the PORT GROUND TRUTH that
        # validate_glaciers_nu3.jl checks the Julia module against at 1e-9, so the two must
        # change together or the gate stops testing port fidelity and starts hiding a
        # divergence. Rationale and price live in the Julia file.
        seq = max(a * (1 - np.exp(-b * (Tarr[k] - T_off))), 0.0)
        frac_left = max(1.0 - S / a, 1e-12)
        T_eq = T_off - np.log(frac_left) / b
        d = Tarr[k] - T_eq
        mult = min(kappa * abs(d) ** nu, 1.0)    # no equilibrium overshoot in one step
        if d < 0.0:
            mult /= GIC_REGROW_R
        S += mult * (seq - S)
        out[k + 1] = S
    return out

CELLS = [(tr, dr) for tr in ["M", "N"] for dr in ["Gfair", "Gobs", "Tglac"]]
PNAMES = {"M": ["a", "b", "T_off", "f", "tau_f", "tau_s", "sigma", "rho"],
          "N": ["a", "b", "T_off", "kappa", "nu", "sigma", "rho"]}

def forward(tr, Tarr, th, n=None):
    if tr == "M":
        return integrate_M(Tarr, th["a"], th["b"], th["T_off"], th["f"],
                           th["tau_f"], th["tau_s"], n=n)
    return integrate_N(Tarr, th["a"], th["b"], th["T_off"], th["kappa"], th["nu"], n=n)

# ------------------------------------------------------------------ objective
def loglik_terms(tr, Tarr, th):
    s_raw = forward(tr, Tarr, th)
    m_cm = 100 * (s_raw - s_raw[ybase].mean())
    r = m_cm[yfit_idx] - obs
    sig, rho = th["sigma"], th["rho"]
    Sig = (sig ** 2 / (1 - rho ** 2)) * rho ** H + np.diag(eps ** 2)
    try:
        cf = cho_factor(Sig)
    except np.linalg.LinAlgError:
        return None
    logdet = 2 * np.sum(np.log(np.diag(cf[0])))
    ll_flow = -0.5 * (nfit * np.log(2 * np.pi) + logdet + r @ cho_solve(cf, r))
    ll_inv = norm.logpdf(th["a"] - s_raw[i_inv], INV_V, INV_SIG)
    ll_lec = norm.logpdf(s_raw[i1900], LEC_MU, LEC_SIG)
    ll_pr = 0.0
    for p in ("a", "b", "T_off") + (("f", "tau_f", "tau_s") if tr == "M" else ()):
        mu, sd = PRIORS[p]
        ll_pr += norm.logpdf(th[p], mu, sd)
    if tr == "N":
        ll_pr += norm.logpdf(np.log(th["kappa"]), *KAPPA_LOGPRIOR)
        ll_pr += norm.logpdf(th["nu"], *NU_PRIOR)
    return dict(ll_flow=ll_flow, ll_inv=ll_inv, ll_lec=ll_lec, ll_prior=ll_pr,
                logJ=ll_flow + ll_inv + ll_lec + ll_pr, s_raw=s_raw, m_cm=m_cm)

def to_theta(tr, z):
    th = {}
    for name, zz in zip(PNAMES[tr], z):
        lo, hi = BOUNDS[name]
        th[name] = lo + (hi - lo) / (1 + np.exp(-zz))
    return th

def to_z(tr, th):
    z = []
    for name in PNAMES[tr]:
        lo, hi = BOUNDS[name]
        x = np.clip((th[name] - lo) / (hi - lo), 1e-4, 1 - 1e-4)
        z.append(np.log(x / (1 - x)))
    return np.array(z)

def optimize_cell(tr, dr):
    Tarr = DRIVERS[dr].to_numpy()[:-1]
    def negJ(z):
        t = loglik_terms(tr, Tarr, to_theta(tr, z))
        return np.inf if t is None else -t["logJ"]
    base_M = dict(a=0.45, b=0.52, T_off=-1.10, f=0.34, tau_f=72., tau_s=300.,
                  sigma=0.04, rho=0.70)
    base_N = dict(a=0.45, b=0.52, T_off=-1.10, kappa=0.0106, nu=0.15,
                  sigma=0.04, rho=0.70)
    starts = []
    for seedth in ([base_M, dict(base_M, a=0.398, b=0.431, T_off=-1.66)] if tr == "M"
                   else [base_N, dict(base_N, nu=1.5, kappa=0.05),
                         dict(base_N, nu=2.5, kappa=0.02, T_off=-0.60)]):
        starts.append(to_z(tr, seedth))
    seeds = list(starts)
    while len(starts) < N_STARTS:
        starts.append(seeds[rng.integers(len(seeds))] + rng.normal(0, 0.8, len(PNAMES[tr])))
    best = None
    for z0 in starts:
        r = minimize(negJ, z0, method="Nelder-Mead",
                     options=dict(xatol=1e-7, fatol=1e-9, maxiter=8000, maxfev=12000))
        if best is None or r.fun < best.fun:
            best = r
    r = minimize(negJ, best.x, method="Nelder-Mead",
                 options=dict(xatol=1e-8, fatol=1e-10, maxiter=8000, maxfev=12000))
    if r.fun < best.fun:
        best = r
    th = to_theta(tr, best.x)
    terms = loglik_terms(tr, DRIVERS[dr].to_numpy()[:-1], th)
    return th, terms

# ------------------------------------------------------------------ evaluation gates
def near_bound(th):
    hits = []
    for name, v in th.items():
        lo, hi = BOUNDS[name]
        if (v - lo) < 0.02 * (hi - lo) or (hi - v) < 0.02 * (hi - lo):
            hits.append(name)
    return hits

def seq_of(th, T):
    return th["a"] * (1 - np.exp(-th["b"] * (T - th["T_off"])))

def ladder(th, s2020, amp_used):
    com, sens = {}, np.nan
    for L in GMIP3_LEVELS:
        Tg = amp_used * L
        com[L] = 100 * (seq_of(th, Tg) - s2020) / max(th["a"] - s2020, 1e-9)
    sens = 1000 * (seq_of(th, amp_used * 3.0) - seq_of(th, amp_used * 1.5))
    return com, sens

def scenario_ds2100(tr, dr, th, amp_used):
    out = {}
    proj_years = np.arange(Y0, 2151)
    for s, g in ssp_rb.items():
        if dr == "Gfair":
            drv = g.reindex(proj_years)
        elif dr == "Gobs":
            drv = extend_obs(gobs, g, 1.0, idx=proj_years)
        else:
            drv = extend_obs(tglac_obs, g, amp_used, idx=proj_years)
        assert not drv.isna().any(), f"scenario driver gap {s}/{dr}"
        s_raw = forward(tr, drv.to_numpy()[:-1], th, n=len(proj_years))
        sb = (proj_years >= PROJ_BASE[0]) & (proj_years <= PROJ_BASE[1])
        out[s] = 100 * (s_raw[proj_years == 2100][0] - s_raw[sb].mean())
        out[s + "_2150"] = 100 * (s_raw[proj_years == 2150][0] - s_raw[sb].mean())
    return out

# ------------------------------------------------------------------ run all cells
print(f"D0 glacier shootout | commit={COMMIT} | drivers rel {FRAME0}-{FRAME1} "
      f"(fair frame shift {FRAME_SHIFT_FAIR:+.4f} C) | amp_fit={AMP_FIT:.3f}")
print(f"  objective: GSIC AR(1) {fit_years[0]}-{fit_years[-1]} (sigma,rho fitted) "
      f"+ A2 inv N({INV_V},{INV_SIG})@{INV_YEAR} + A2b Leclercq N({LEC_MU},{LEC_SIG}) + priors")

rows, fits = [], {}
for tr, dr in CELLS:
    th, terms = optimize_cell(tr, dr)
    s_raw = terms["s_raw"]
    s1900_mm = 1000 * s_raw[i1900]
    inv_res = th["a"] - s_raw[i_inv]
    bounds_hit = near_bound(th)
    for ampname, ampval in (AMP_VARIANTS.items() if dr == "Tglac" else [("global", 1.0)]):
        amp_used = ampval
        com, sens = ladder(th, s_raw[i2020], amp_used)
        ds = scenario_ds2100(tr, dr, th, amp_used)
        spread = ds["ssp585"] - ds["ssp126"]
        gates = dict(
            g_inv=abs(inv_res - INV_V) / INV_SIG < 1.0,
            g_s1900=S1900_GATE_MM[0] <= s1900_mm <= S1900_GATE_MM[1],
            g_ladder=all(GMIP3_LIKELY[L][0] <= com[L] <= GMIP3_LIKELY[L][1]
                         for L in GMIP3_LEVELS),
            g_bounds=len(bounds_hit) == 0,
            g_spread=4.5 <= spread <= 13.5,     # AR6 spread 9 cm +/- 50%
        )
        rows.append(dict(cell=f"{tr}x{dr}", transient=tr, driver=dr, amp_variant=ampname,
                         amp_used=amp_used, logJ=terms["logJ"], ll_flow=terms["ll_flow"],
                         ll_inv=terms["ll_inv"], ll_lec=terms["ll_lec"],
                         ll_prior=terms["ll_prior"],
                         n_params=len(PNAMES[tr]),
                         AIC=2 * len(PNAMES[tr]) - 2 * terms["logJ"],
                         **{k: th.get(k, np.nan) for k in
                            ["a", "b", "T_off", "f", "tau_f", "tau_s", "kappa", "nu",
                             "sigma", "rho"]},
                         S1900_mm=s1900_mm, inv_resid=inv_res,
                         inv_z=(inv_res - INV_V) / INV_SIG,
                         S2020_m=s_raw[i2020],
                         **{f"com{str(L).replace('.', 'p')}": com[L] for L in GMIP3_LEVELS},
                         sens_1p5_3_mm=sens,
                         ds2100_ssp126=ds["ssp126"], ds2100_ssp245=ds["ssp245"],
                         ds2100_ssp585=ds["ssp585"], spread2100=spread,
                         ds2150_ssp245=ds["ssp245_2150"], ds2150_spread=ds["ssp585_2150"] - ds["ssp126_2150"],
                         bounds_hit=";".join(bounds_hit),
                         **gates,
                         gates_passed=sum(gates.values()),
                         ))
    fits[(tr, dr)] = (th, terms)
    g = rows[-1]
    print(f"\n  [{tr} x {dr}] logJ={terms['logJ']:.2f} (flow {terms['ll_flow']:.2f} "
          f"inv {terms['ll_inv']:.2f} lec {terms['ll_lec']:.2f} pr {terms['ll_prior']:.2f})")
    print(f"    a={th['a']:.3f} b={th['b']:.3f} T_off={th['T_off']:.3f} "
          + (f"f={th['f']:.2f} tau_f={th['tau_f']:.0f} tau_s={th['tau_s']:.0f} "
             if tr == "M" else f"kappa={th['kappa']:.4f} nu={th['nu']:.2f} ")
          + f"sigma={th['sigma']:.3f} rho={th['rho']:.2f}")
    print(f"    S(1900)={s1900_mm:.1f} mm | inv resid={inv_res:.3f} (z={g['inv_z']:+.2f}) "
          f"| bounds hit: {bounds_hit or 'none'}")
    print(f"    ladder committed% @1.2/1.5/2/3K: "
          + "/".join(f"{g[f'com{str(L).replace('.', 'p')}']:.0f}" for L in GMIP3_LEVELS)
          + f" (lit {'/'.join(str(GMIP3_CENTRAL[L]) for L in GMIP3_LEVELS)}) "
          f"| sens {g['sens_1p5_3_mm']:.0f} mm (lit ~{GMIP3_SENS_MM})")
    print(f"    dS2100 cm 126/245/585: {g['ds2100_ssp126']:.1f}/{g['ds2100_ssp245']:.1f}/"
          f"{g['ds2100_ssp585']:.1f} (AR6 9/12/18) spread {g['spread2100']:.1f} "
          f"| gates {g['gates_passed']}/5")

res = pd.DataFrame(rows)
os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
res.to_csv(OUT_CSV, index=False, float_format="%.5f")

# ------------------------------------------------------------------ figure
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COLORS = {("M", "Gfair"): "0.45", ("M", "Gobs"): "tab:blue", ("M", "Tglac"): "tab:cyan",
          ("N", "Gfair"): "tab:orange", ("N", "Gobs"): "tab:red", ("N", "Tglac"): "tab:purple"}
fig, axes = plt.subplots(2, 2, figsize=(13, 9.5), constrained_layout=True)
(axA, axB), (axC, axD) = axes

axA.fill_between(fit_years, obs - 1.645 * eps, obs + 1.645 * eps, color="k", alpha=0.12,
                 label="GSIC target ±90%")
axA.plot(fit_years, obs, color="k", lw=1.4, label="GSIC target")
for (tr, dr), (th, terms) in fits.items():
    axA.plot(years, terms["m_cm"], color=COLORS[(tr, dr)], lw=1.1, label=f"{tr}×{dr}")
axA.set(xlim=(1895, 2027), xlabel="year", ylabel=f"cm rel {BASE0}-{BASE1}",
        title="GSIC flow fit (joint-objective optimum per cell)")
axA.legend(fontsize=7, ncol=2)

for (tr, dr), (th, terms) in fits.items():
    axB.plot(years, 1000 * terms["s_raw"], color=COLORS[(tr, dr)], lw=1.1)
axB.axhspan(1000 * (LEC_MU - LEC_SIG), 1000 * (LEC_MU + LEC_SIG), color="tab:green",
            alpha=0.18, label="Leclercq S(1900) ±1σ")
axB.axvline(1900, color="k", ls=":", lw=0.8)
axB.set(xlim=(Y0, 2027), xlabel="year", ylabel="raw cumulative melt since 1850 (mm SLE)",
        title="Raw melt trajectories — the pre-1900 leak & onset shape")
axB.legend(fontsize=8)

xs = np.arange(len(GMIP3_LEVELS))
for L, x in zip(GMIP3_LEVELS, xs):
    lo, hi = GMIP3_LIKELY[L]
    axC.fill_between([x - 0.35, x + 0.35], [lo, lo], [hi, hi], color="k", alpha=0.10)
    axC.plot([x - 0.35, x + 0.35], [GMIP3_CENTRAL[L]] * 2, color="k", lw=1.6)
for _, row in res.iterrows():
    if row["driver"] == "Tglac" and row["amp_variant"] != "ampfit":
        ls = "--"
    else:
        ls = "-"
    key = (row["transient"], row["driver"])
    axC.plot(xs, [row[f"com{str(L).replace('.', 'p')}"] for L in GMIP3_LEVELS],
             color=COLORS[key], ls=ls, marker="o", ms=4, lw=1.1,
             label=f"{row['cell']}" + (f" ({row['amp_variant']})" if row['driver'] == 'Tglac' else ""))
axC.set(xticks=xs, xticklabels=[f"+{L}K" for L in GMIP3_LEVELS],
        ylabel="committed loss, % of 2020 mass",
        title="GlacierMIP3 ladder (evaluation-only; black = Zekollari 2025 central + likely)")
axC.legend(fontsize=7)

for _, row in res.iterrows():
    key = (row["transient"], row["driver"])
    ls = "--" if (row["driver"] == "Tglac" and row["amp_variant"] != "ampfit") else "-"
    axD.plot([9.0, 12.0, 18.0],
             [row["ds2100_ssp126"], row["ds2100_ssp245"], row["ds2100_ssp585"]],
             color=COLORS[key], ls=ls, marker="s", ms=4, lw=1.1)
axD.plot([9, 12, 18], [9, 12, 18], color="k", lw=1.4, label="1:1 (AR6 medians)")
axD.set(xlabel="AR6 glacier median @2100 (cm)", ylabel="cell dS 2100 (cm rel 1995-2014)",
        title="Scenario response vs AR6 (ssp126/245/585)")
axD.legend(fontsize=8)

fig.suptitle(f"D0 glacier structural shootout — {{M 2-τ, Nauels-ν}} × {{Gfair, Gobs, Tglac}} | "
             f"amp_fit={AMP_FIT:.2f} | commit {COMMIT}", fontsize=10)
os.makedirs(os.path.dirname(OUT_FIG), exist_ok=True)
fig.savefig(OUT_FIG, dpi=150)
print(f"\nWrote {os.path.relpath(OUT_CSV, REPO)} and {os.path.relpath(OUT_FIG, REPO)}")
