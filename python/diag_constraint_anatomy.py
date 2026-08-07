#!/usr/bin/env python3
"""Constraint anatomy for the glacier structural decision (Marcus 2026-08-07:
"set out what the drivers are ... and describe why it is so hard given the
constraints for there to be a good solution with our current equation
structure") — the quantitative backbone for
notes/memo_2026-08-08_glacier_constraint_anatomy.md.

Part 1 — the one-reservoir arithmetic, on the adopted (scope-corrected) anchor:
  At the SC point the Nauels law is rate = kappa * (a-S)(1-exp(-b*exc)) * exc^nu
  with exc = T_glac - T_eq(S): gap and excess are BOTH functions of the single
  state S, so the committed-gap constraint (ladder) pins exc(2020), and the law
  then makes the century-scale rate path a monotone function of the excess
  path. Two branches are integrated and tabulated per era:
    A "fit-history":     kappa (+sigma,rho) ML under the sigma-x2 flow target
    B "fit-modern-rate": kappa bisected so the 2015-2023 mean rate = obs 0.6
  and each branch's era rates / stock checkpoints / spread show which
  constraints it breaks.

Part 2 — where the constraints physically live (per-region data on disk):
  stock share (table S3 masses), committed share at +1.2K (S1a), modern melt
  share (Hugonnet 2000-2019 dvol/dt, regchar), response times (S1a 1.5C and
  regchar 3.0C — note the warming-level collapse), and 2000-2019 regional
  warming (regchar). Mass-weighted vs melt-weighted response times quantify
  the fast/slow separation the single global reservoir (and the T1 pool
  splits sharing one driver+frame) cannot express.

Outputs: outputs/diag_constraint_anatomy_{eras,regions}.csv,
         figures/diag_constraint_anatomy.png
"""
import os
import re
import subprocess

import numpy as np
import pandas as pd
from scipy.optimize import brentq, minimize
from scipy.stats import norm

np.seterr(over="ignore", under="ignore")

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
SHOOTOUT = os.path.join(REPO, "python/d0_glacier_shootout.py")
GMIP3_DIR = os.path.join(REPO, "data/observations/raw/gmip3")

src = open(SHOOTOUT).read().split(
    "# ------------------------------------------------------------------ run all cells")[0]
exec(src.replace('print(f"D0', 'pass # print(f"D0'))

# NB: the exec rebinds OUT_CSV/OUT_FIG to the shootout's paths — set ours AFTER it
OUT_ERAS = os.path.join(REPO, "outputs/diag_constraint_anatomy_eras.csv")
OUT_REGS = os.path.join(REPO, "outputs/diag_constraint_anatomy_regions.csv")
OUT_CORNERS = os.path.join(REPO, "outputs/diag_constraint_anatomy_corners.csv")
OUT_FIG = os.path.join(REPO, "figures/diag_constraint_anatomy.png")

COMMIT = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True).stdout.strip()

AMP_G = 1.8
EARLY_SIGMA_X2_BEFORE = 1940
ERAS = [(1900, 1919), (1920, 1949), (1950, 1979), (1980, 1999), (2000, 2023)]
RATE_WIN = (2015, 2023)
NU_REF = 1.0
S2000_OBS, S2020_OBS = 0.093, 0.107

# modern-rate reference DERIVED from the calibration target itself (the number
# the likelihood actually sees), not the handoff's ~0.6 GlaMBIE-2020 figure —
# the target's 2015-2023 window includes the record 2022/23 loss years
_tgt_g = pd.Series(obs, index=fit_years)
OBS_MODERN_RATE_MM_YR = float(10 * (_tgt_g.loc[RATE_WIN[1]] - _tgt_g.loc[RATE_WIN[0]])
                              / (RATE_WIN[1] - RATE_WIN[0]))

eps_x2 = eps * np.where(fit_years < EARLY_SIGMA_X2_BEFORE, 2.0, 1.0)
Tarr = extend_obs(tglac_obs, fair_rb, AMP_G).to_numpy()[:-1]

# ---------------------------------------------------------------- SC point
SC_A = INV_V + S2000_OBS
SLOPE_GLAC = 0.133 / AMP_FIT
COM12 = GMIP3_CENTRAL[1.2] / 100.0     # scope-corrected anchor (adopted)


def solve_sc(com12):
    tgt_seq = com12 * (SC_A - S2020_OBS) + S2020_OBS

    def f(toff):
        b = -np.log(1 - tgt_seq / SC_A) / (AMP_FIT * 1.2 - toff)
        return SC_A * b * np.exp(b * toff) - SLOPE_GLAC

    toff = brentq(f, -1.9, -0.2)
    b = -np.log(1 - tgt_seq / SC_A) / (AMP_FIT * 1.2 - toff)
    return dict(a=SC_A, b=b, T_off=toff)


SC = solve_sc(COM12)
print(f"diag_constraint_anatomy | commit={COMMIT} | anchor com12={100 * COM12:.1f}% "
      f"(scope-corrected) | SC a={SC['a']:.3f} b={SC['b']:.3f} T_off={SC['T_off']:.3f}")

# ---------------------------------------------------------------- branches


def run_N(kappa, nu=NU_REF):
    th = dict(SC, kappa=kappa, nu=nu)
    s_raw = integrate_N(Tarr, th["a"], th["b"], th["T_off"], kappa, nu)
    return th, s_raw


def flow_ll(s_raw, sig, rho_):
    m_cm = 100 * (s_raw - s_raw[ybase].mean())
    r = m_cm[yfit_idx] - obs
    nfit_ = len(fit_years)
    H_ = np.abs(np.subtract.outer(np.arange(nfit_), np.arange(nfit_)))
    Sig = (sig ** 2 / (1 - rho_ ** 2)) * rho_ ** H_ + np.diag(eps_x2 ** 2)
    from scipy.linalg import cho_factor, cho_solve
    try:
        cf = cho_factor(Sig)
    except np.linalg.LinAlgError:
        return -np.inf
    logdet = 2 * np.sum(np.log(np.diag(cf[0])))
    return -0.5 * (nfit_ * np.log(2 * np.pi) + logdet + r @ cho_solve(cf, r))


def fit_branch_A():
    def neg(z):
        kap = np.exp(z[0])
        sig = 0.005 + 0.495 / (1 + np.exp(-z[1]))
        rho_ = 0.99 / (1 + np.exp(-z[2]))
        _, s_raw = run_N(kap)
        ll = flow_ll(s_raw, sig, rho_)
        ll += norm.logpdf(np.log(kap), *KAPPA_LOGPRIOR)
        return -ll if np.isfinite(ll) else np.inf

    best = None
    for z0 in ([np.log(0.006), 0.0, 0.5], [np.log(0.003), -1.0, 0.0],
               [np.log(0.012), 0.0, 1.0]):
        r = minimize(neg, np.array(z0), method="Nelder-Mead",
                     options=dict(xatol=1e-8, fatol=1e-10, maxiter=6000))
        if best is None or r.fun < best.fun:
            best = r
    return np.exp(best.x[0])


def modern_rate(s_raw):
    i0, i1 = np.searchsorted(years, RATE_WIN[0]), np.searchsorted(years, RATE_WIN[1])
    return 1000 * (s_raw[i1] - s_raw[i0]) / (RATE_WIN[1] - RATE_WIN[0])


KAPPA_A = fit_branch_A()
_, sA = run_N(KAPPA_A)
KAPPA_B = brentq(lambda k: modern_rate(run_N(k)[1]) - OBS_MODERN_RATE_MM_YR,
                 1e-4, KAPPA_A)
_, sB = run_N(KAPPA_B)
print(f"  obs modern rate (target {RATE_WIN[0]}-{RATE_WIN[1]}): "
      f"{OBS_MODERN_RATE_MM_YR:.2f} mm/yr (handoff GlaMBIE-2020 figure was ~0.6)")
print(f"  branch A (fit-history)     kappa={KAPPA_A:.5f}  rate2015-23="
      f"{modern_rate(sA):.2f} mm/yr = {modern_rate(sA) / OBS_MODERN_RATE_MM_YR:.2f}x obs")
print(f"  branch B (fit-modern-rate) kappa={KAPPA_B:.5f}  rate2015-23="
      f"{modern_rate(sB):.2f} mm/yr")


def exc_path(s_raw):
    S = s_raw[:-1]
    T_eq = SC["T_off"] - np.log(np.maximum(1 - S / SC["a"], 1e-12)) / SC["b"]
    return np.maximum(Tarr - T_eq, 0.0)


def era_table():
    rows = []
    tgt_cm = pd.Series(obs, index=fit_years)
    for (y0e, y1e) in ERAS:
        sel_y = (years >= y0e) & (years <= y1e)
        i0, i1 = np.searchsorted(years, y0e), np.searchsorted(years, y1e)
        obs_rate = 10 * (tgt_cm.loc[min(y1e, tgt_cm.index.max())]
                         - tgt_cm.loc[max(y0e, tgt_cm.index.min())]) / (y1e - y0e)
        rows.append(dict(
            era=f"{y0e}-{y1e}",
            t_glac_C=float(pd.Series(Tarr, index=years[:-1])[sel_y[:-1]].mean()),
            exc_A_K=float(exc_path(sA)[sel_y[:-1]].mean()),
            obs_rate_mm_yr=obs_rate,
            rate_A_mm_yr=1000 * (sA[i1] - sA[i0]) / (y1e - y0e),
            rate_B_mm_yr=1000 * (sB[i1] - sB[i0]) / (y1e - y0e),
        ))
    return pd.DataFrame(rows)


eras = era_table()
print("\n== era table (obs vs branch A fit-history vs branch B fit-modern-rate) ==")
print(eras.to_string(index=False, float_format=lambda x: f"{x:7.2f}"))

# stock checkpoints + spread per branch
for name, s_raw, kap in [("A", sA, KAPPA_A), ("B", sB, KAPPA_B)]:
    th = dict(SC, kappa=kap, nu=NU_REF)
    ds = scenario_ds2100("N", "Tglac", th, AMP_G)
    spread = ds["ssp585"] - ds["ssp126"]
    print(f"  branch {name}: S(1900)={1000 * s_raw[i1900]:.1f} mm (Leclercq 20+/-9) | "
          f"S(2020)={1000 * s_raw[i2020]:.1f} mm (obs ~107) | "
          f"inv_z={(SC['a'] - s_raw[i_inv] - INV_V) / INV_SIG:+.2f} | "
          f"spread@2100={spread:.1f} cm (gate 4.5-13.5)")

law_acc = eras.rate_A_mm_yr.iloc[-1] / eras.rate_A_mm_yr.iloc[1]
obs_acc = eras.obs_rate_mm_yr.iloc[-1] / eras.obs_rate_mm_yr.iloc[1]
print(f"\n  law-implied acceleration (2000-23 / 1920-49): {law_acc:.2f}x | "
      f"observed: {obs_acc:.2f}x")

# ---------------------------------------------------------------- Part 2: regions
s1a = pd.read_csv(os.path.join(GMIP3_DIR, "table_S1a.csv"), header=None, skiprows=3)
s3 = pd.read_csv(os.path.join(GMIP3_DIR, "table_S3.csv"), index_col=0)
s3 = s3[s3["rgi_reg"] != "global"]
regchar = pd.read_csv(os.path.join(GMIP3_DIR,
                                   "3_shift_summary_region_characteristicsFeb12_2024.csv"),
                      index_col=0)
regchar = regchar[regchar["rgi_reg"] != "All"]
regchar["reg"] = regchar["rgi_reg"].map(lambda r: f"{int(r):02d}")
regchar = regchar.set_index("reg")

mass = {f"{int(r):02d}": m for r, m in
        zip(s3["rgi_reg"], s3["Glacier mass in 2020$^b$ (Gt)"])}


def parse_committed(cell):
    m = re.match(r"\s*(-?\d+)\s*\[", str(cell))
    return float(m.group(1)) if m else np.nan


def parse_resp(cell):
    m = re.match(r"\s*(-?\d+)\s*\[", str(cell))
    return float(m.group(1)) if m else np.nan


reg_rows = []
for _, row in s1a.iterrows():
    reg = str(row.iloc[10]).strip()
    if reg in ("global", "nan"):
        continue
    reg = f"{int(reg):02d}"
    if reg == "05":
        continue                                # excluded from our scope
    reg_rows.append(dict(
        reg=reg,
        mass_gt=mass[reg],
        committed12_pct=parse_committed(row.iloc[2]),
        resp_time_15C_yr=parse_resp(row.iloc[9]),
        resp_time_30C_yr=float(regchar.loc[reg, "resp_time_-50%_3_0_deg"]),
        warming_2000_19_K=float(regchar.loc[reg, "temp_ch_avg_2000-2019_vs_1901-1920"]),
        melt_rate_gt_yr=-float(regchar.loc[reg, "dvoldt_m3_hugonnet"]) * 900.0 / 1e12,
    ))
regs = pd.DataFrame(reg_rows)
regs["stock_share"] = regs.mass_gt / regs.mass_gt.sum()
regs["committed_share"] = (regs.committed12_pct / 100 * regs.mass_gt)
regs["committed_share"] /= regs["committed_share"].sum()
regs["melt_share"] = regs.melt_rate_gt_yr / regs.melt_rate_gt_yr.sum()
regs = regs.sort_values("mass_gt", ascending=False)

w = lambda v, wt: float(np.average(v, weights=wt))
print("\n== per-region anatomy (our scope, excl r5; sorted by 2020 mass) ==")
print(regs.to_string(index=False, float_format=lambda x: f"{x:8.2f}"))
print(f"\n  response time (50%, ~1.5C): stock-weighted {w(regs.resp_time_15C_yr, regs.mass_gt):.0f} yr"
      f" | committed-weighted {w(regs.resp_time_15C_yr, regs.committed_share):.0f} yr"
      f" | modern-melt-weighted {w(regs.resp_time_15C_yr, regs.melt_share):.0f} yr")
print(f"  response time (50%, ~3.0C): stock-weighted {w(regs.resp_time_30C_yr, regs.mass_gt):.0f} yr"
      f" | modern-melt-weighted {w(regs.resp_time_30C_yr, regs.melt_share):.0f} yr")
print(f"  2000-19 warming vs 1901-20: stock-weighted {w(regs.warming_2000_19_K, regs.mass_gt):.2f} K"
      f" | committed-weighted {w(regs.warming_2000_19_K, regs.committed_share):.2f} K"
      f" | modern-melt-weighted {w(regs.warming_2000_19_K, regs.melt_share):.2f} K")

eras.to_csv(OUT_ERAS, index=False, float_format="%.4f")
regs.to_csv(OUT_REGS, index=False, float_format="%.4f")

# ------------------------------------------- Part 3: com12 corner scan
# Is the tension driven by the anchor CENTRAL (soft — an SC point at the
# ladder's lower likely bound would shrink the demanded gap ~3x) or by the
# whole gate BAND (hard — the 2K/3K rung floors and the spread gate re-bind)?
print("\n== com12 corner scan (SC re-solved per anchor; branch-A kappa fit each) ==")
corner_rows = []
for com12_c in [GMIP3_LIKELY[1.2][0] / 100, 0.20, 0.28, COM12]:
    try:
        sc_c = solve_sc(com12_c)
    except ValueError:
        print(f"  com12={100 * com12_c:4.1f}%  SC solve FAILED (no consistent T_off)")
        corner_rows.append(dict(com12_pct=100 * com12_c, solved=False))
        continue
    SC_save = dict(SC)
    SC.update(sc_c)
    kap_c = fit_branch_A()
    _, s_c = run_N(kap_c)
    th_c = dict(SC, kappa=kap_c, nu=NU_REF)
    com_c, sens_c = ladder(th_c, s_c[i2020], AMP_G)
    ds_c = scenario_ds2100("N", "Tglac", th_c, AMP_G)
    spread_c = ds_c["ssp585"] - ds_c["ssp126"]
    lad_ok = all(GMIP3_LIKELY[L][0] <= com_c[L] <= GMIP3_LIKELY[L][1]
                 for L in GMIP3_LEVELS)
    print(f"  com12={100 * com12_c:4.1f}%  b={sc_c['b']:.3f} T_off={sc_c['T_off']:+.3f}"
          f"  rate15-23={modern_rate(s_c):.2f} mm/yr"
          f"  ladder@1.2/1.5/2/3K={com_c[1.2]:.0f}/{com_c[1.5]:.0f}/"
          f"{com_c[2.0]:.0f}/{com_c[3.0]:.0f} ({'PASS' if lad_ok else 'FAIL'})"
          f"  spread={spread_c:.1f} ({'PASS' if 4.5 <= spread_c <= 13.5 else 'FAIL'})"
          f"  S2020={1000 * s_c[i2020]:.0f} mm")
    corner_rows.append(dict(com12_pct=100 * com12_c, solved=True, b=sc_c["b"],
                            T_off=sc_c["T_off"], kappa=kap_c,
                            rate_modern_mm_yr=modern_rate(s_c),
                            **{f"com{str(L).replace('.', 'p')}": com_c[L]
                               for L in GMIP3_LEVELS},
                            ladder_pass=lad_ok, spread_cm=spread_c,
                            spread_pass=4.5 <= spread_c <= 13.5,
                            S2020_mm=1000 * s_c[i2020],
                            S1900_mm=1000 * s_c[i1900]))
    SC.update(SC_save)
pd.DataFrame(corner_rows).to_csv(OUT_CORNERS, index=False, float_format="%.4f")

# ---------------------------------------------------------------- figure
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), constrained_layout=True)
axA, axB, axC = axes

tgt_cm = pd.Series(obs, index=fit_years)
obs_rate_annual = 10 * tgt_cm.diff().rolling(11, center=True).mean()
axA.plot(obs_rate_annual.index, obs_rate_annual, color="k", lw=1.6,
         label="obs flow (11-yr mean)")
for s_raw, nm, c in [(sA, f"A fit-history (κ={KAPPA_A:.4f})", "tab:red"),
                     (sB, f"B fit-modern-rate (κ={KAPPA_B:.4f})", "tab:blue")]:
    axA.plot(years[1:], 1000 * np.diff(s_raw), color=c, lw=1.4, label=nm)
axA.axhline(OBS_MODERN_RATE_MM_YR, color="0.5", lw=0.8, ls=":")
axA.set(xlim=(1900, 2026), xlabel="year", ylabel="GSIC flow (mm SLE/yr)",
        title=f"one-reservoir ν={NU_REF:.0f} at the SC point: fit history OR modern rate")
axA.legend(fontsize=8)

axB.plot(years[:-1], exc_path(sA), color="tab:red", lw=1.4, label="excess T (branch A)")
axB.plot(years[:-1], Tarr, color="k", lw=1.0, ls="--", label="T_glac driver")
axB.set(xlim=(1900, 2026), xlabel="year", ylabel="K (glacier frame)",
        title="the excess path: monotone rise the law must convert to flow")
axB.legend(fontsize=8)

sc = axC.scatter(regs.warming_2000_19_K, regs.resp_time_15C_yr,
                 s=2000 * regs.stock_share, c=regs.committed12_pct,
                 cmap="viridis", alpha=0.85)
for _, r in regs.iterrows():
    if r.stock_share > 0.04:
        axC.annotate(f"r{r.reg}", (r.warming_2000_19_K, r.resp_time_15C_yr),
                     fontsize=7, xytext=(4, 3), textcoords="offset points")
fig.colorbar(sc, ax=axC, label="committed @+1.2K (% of 2020 mass)")
axC.set(xlabel="2000-19 regional warming vs 1901-20 (K)",
        ylabel="response time, 50% @~1.5C (yr)",
        title="where stock/committed/flow live (size = stock share; our scope)")
fig.suptitle(f"constraint anatomy — scope-corrected anchor com12={100 * COM12:.1f}% | "
             f"commit {COMMIT}", fontsize=10)
fig.savefig(OUT_FIG, dpi=150)
print(f"\nWrote {os.path.relpath(OUT_ERAS, REPO)}, {os.path.relpath(OUT_REGS, REPO)}, "
      f"{os.path.relpath(OUT_FIG, REPO)}")
