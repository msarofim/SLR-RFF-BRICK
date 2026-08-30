"""
diag_d2_steric_prior_binding.py

ANSWERS OPEN 1 OF handoff_2026-08-29_l22_and_coulon_integral.md: WHY DOES L22
DECLINE THE 48% OF THE TE RESIDUAL THAT D2 COULD NOW REMOVE?

The handoff named three candidates and proposed a REFIT with the steric D2
coefficients freed from their prior as the cheapest test. Two of the three are
refutable by READING THE LIKELIHOOD, and the third is answerable in CLOSED FORM,
so no refit is needed to predict what a refit would do.

  STRUCTURE (calibrate_mcmc_ext.jl, verified 2026-08-29). d2_steric_1/_2 are
  `comp=:likelihood_only, sym=:none` -- they touch NO Mimi parameter. The `d2`
  closure is applied ONLY inside the per-component steric term (line 1447), and
  `tot_full = ais + gsic_tot + gis + te` (line 1439) sums the RAW te. So:
    * the TOTAL/dang term does NOT see the steric delta -- it cannot pull against it;
    * GlaMBIE / rung / SMB / inventory / ledger are glacier+AIS terms and never
      see it either;
    * the gsic stream has its OWN coefficients and its OWN basis (D2_BASIS[st]),
      so "coupling to gsic, which shares the D2 machinery" is a shared FUNCTION,
      not a shared PARAMETER.
  d2_steric therefore enters the posterior in EXACTLY TWO PLACES: the steric
  AR(1) likelihood term, and its own N(0, D2_BASIS_SD) prior.

  CONSEQUENCE. Conditional on everything else, the posterior in c = (c1, c2) is
  EXACTLY Gaussian: -0.5 (r + Bc)' P (r + Bc) - 0.5 c'c/sd^2. Its precision is
  Lam_lik + Lam_pr with Lam_lik = B'PB and Lam_pr = I/sd^2, both computable. The
  prior's SHARE of that precision is the whole answer to "is the prior binding",
  and it is a number, not a run.

⚠ THE RESIDUAL IN THE POSTPRED FILES IS NOT THE RESIDUAL THE LIKELIHOOD SCORES.
  posterior_predictive_ladrillo.jl contains no d2 (grepped), so `te_p50 - te_obs`
  -- the 0.889 cm / 17.79 sigma headline -- is the residual BEFORE the discrepancy
  term the fit itself applies. Everything downstream of that file, INCLUDING the
  "48.2% removable" in diag_te_residual_onto_shape.py, is computed on the raw
  residual. So "the fit declines 48%" may be a reporting artefact rather than a
  behaviour. This script prices both.

  source ~/climate-env/bin/activate && python python/diag_d2_steric_prior_binding.py
"""
import os
import sys
import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
# reuse the EXISTING port rather than making a second one that can drift
from diag_te_residual_onto_shape import d2_basis, ar1_precision, FITTED

TARGETS      = os.path.join(REPO, "outputs/recalib_targets_ext.csv")
OHC          = os.path.join(REPO, "data/observations/fair_mean_ohc_ssp245harm.csv")
OUT          = os.path.join(REPO, "outputs/diag_d2_steric_prior_binding.csv")
ARMS         = ["L21", "L22"]
D2_BASIS_SD  = 0.5        # calibrate_mcmc_ext.jl:691 -- prior sd, cm, per coefficient
D2_BASIS_N   = 2          # calibrate_mcmc_ext.jl:690
EPS_FLOOR    = 0.05       # the epsband floor the likelihood applies
EPS_Z        = 1.645      # the target band is 90%, not 95%
HEADLINE_Y   = 2025       # the year the 17.8 sigma headline is quoted at
PROFILE_Y    = [1900, 1950, 2000, 2018, 2025]   # the rows postpred_*_bias.csv reports
COEFS        = [f"d2_steric_{k}" for k in range(1, D2_BASIS_N + 1)]
BINDING_PCT  = 5.0        # prior share of posterior precision above which we call it BINDING


def subsample(tag):
    return pd.read_csv(os.path.join(
        REPO, f"data/MimiBRICK/parameters_subsample_brick_mengel_{tag}.csv"))


def main():
    tg  = pd.read_csv(TARGETS).dropna(subset=["steric"])
    yrs = tg.year.astype(int).values
    eps = np.maximum((tg.steric_hi - tg.steric_lo).values / (2 * EPS_Z), EPS_FLOOR)
    S   = pd.read_csv(OHC).set_index("year")["ohc_1e22J"].reindex(yrs).values
    B, _ = d2_basis(yrs, [np.ones(len(yrs)), S])
    iy   = int(np.where(yrs == HEADLINE_Y)[0][0])
    e_hd = eps[iy]

    print(f"\n{'='*84}\nIS THE D2 PRIOR WHAT STOPS THE FIT REMOVING THE TE RESIDUAL?"
          f"\n  steric window {yrs[0]}-{yrs[-1]}, n={len(yrs)} | prior sd {D2_BASIS_SD} cm"
          f" | headline year {HEADLINE_Y} (eps={e_hd:.4f} cm)\n{'='*84}")

    rows = []
    for arm in ARMS:
        pp = pd.read_csv(os.path.join(
            REPO, f"outputs/postpred_{arm}_components_timeseries.csv")).set_index("year")
        r_raw = (pp["te_p50"] - pp["te_obs"]).reindex(yrs).values
        ss    = subsample(arm)
        c_fit = np.array([ss[c].median() for c in COEFS])
        sg, rh = FITTED[arm]
        P = ar1_precision(eps, sg, rh)

        # --- the exact conditional Gaussian in c -------------------------------
        Lam_lik = B.T @ P @ B                       # likelihood precision on c
        Lam_pr  = np.eye(D2_BASIS_N) / D2_BASIS_SD ** 2
        g       = B.T @ P @ r_raw                   # gradient term
        c_LS    = -np.linalg.solve(Lam_lik, g)              # prior FREED
        c_MAP   = -np.linalg.solve(Lam_lik + Lam_pr, g)     # prior as shipped
        chi     = lambda c: float((r_raw + B @ c) @ P @ (r_raw + B @ c))
        pr_share = np.diag(Lam_pr) / np.diag(Lam_lik + Lam_pr) * 100

        print(f"\n  ── {arm} ──  sigma={sg:.4f} rho={rh:.4f}")
        print(f"     {'coefficient':<14}{'fitted':>10}{'post sd':>10}"
              f"{'MAP(cond)':>11}{'LS(no prior)':>13}{'prior share of precision':>27}")
        for k, c in enumerate(COEFS):
            print(f"     {c:<14}{c_fit[k]:>+10.4f}{ss[c].std():>10.4f}"
                  f"{c_MAP[k]:>+11.4f}{c_LS[k]:>+13.4f}{pr_share[k]:>25.2f} %")

        # --- what the likelihood ACTUALLY scores ------------------------------
        d_fit = float(B[iy] @ c_fit)
        print(f"\n     {HEADLINE_Y} residual   RAW (what postpred/bias reports): "
              f"{r_raw[iy]:+.4f} cm = {r_raw[iy]/e_hd:+.2f} sigma")
        print(f"     {HEADLINE_Y} residual   EFFECTIVE (raw + fitted delta):    "
              f"{r_raw[iy]+d_fit:+.4f} cm = {(r_raw[iy]+d_fit)/e_hd:+.2f} sigma"
              f"   [delta = {d_fit:+.4f} cm]")

        # --- how much of the removable chi-square the fit already took --------
        chi0, chi_fit, chi_map, chi_ls = chi(np.zeros(2)), chi(c_fit), chi(c_MAP), chi(c_LS)
        taken = (chi0 - chi_fit) / (chi0 - chi_ls) * 100
        print(f"\n     chi2  at c=0 {chi0:10.2f} | at fitted {chi_fit:10.2f} | "
              f"at MAP {chi_map:10.2f} | at LS {chi_ls:10.2f}")
        print(f"     removable by D2 = {100*(chi0-chi_ls)/chi0:5.1f}% of chi2;"
              f"  THE FIT HAS ALREADY TAKEN {taken:5.1f}% OF IT")

        # --- the effective bias profile, per-draw ------------------------------
        # WARNING, APPROXIMATION NAMED: te_p50 is the per-year MEDIAN across draws and
        # c_fit is the median of c, so eff = median(r) + median(delta) is not exactly
        # median(r + delta). The per-draw delta band below is EXACT (same draws, same
        # order as the postpred `post` table); an exact effective median would need
        # posterior_predictive_ladrillo.jl to emit the delta-applied series itself.
        C = ss[COEFS].values                       # ndraw x 2, the SAME draws postpred used
        D = C @ B.T                                # ndraw x nyear, per-draw delta
        print(f"\n     TE BIAS: RAW (what postpred reports) vs EFFECTIVE (raw + the d2"
              f" delta the likelihood applies)")
        print(f"     {'year':>6}{'eps':>8}{'raw cm':>9}{'raw sig':>9}{'delta p50':>11}"
              f"{'delta p05..p95':>20}{'eff cm':>9}{'eff sig':>9}")
        for y in PROFILE_Y:
            i = int(np.where(yrs == y)[0][0])
            d50, d05, d95 = np.percentile(D[:, i], [50, 5, 95])
            print(f"     {y:>6}{eps[i]:>8.3f}{r_raw[i]:>9.3f}{r_raw[i]/eps[i]:>9.2f}"
                  f"{d50:>11.3f}{f'{d05:+.3f}..{d95:+.3f}':>20}"
                  f"{r_raw[i]+d50:>9.3f}{(r_raw[i]+d50)/eps[i]:>9.2f}")
            rows.append(dict(arm=arm, coef=f"__bias_{y}__", resid_raw_cm=r_raw[i],
                             resid_raw_sigma=r_raw[i]/eps[i], delta_p50_cm=d50,
                             delta_p05_cm=d05, delta_p95_cm=d95,
                             resid_eff_cm=r_raw[i]+d50,
                             resid_eff_sigma=(r_raw[i]+d50)/eps[i]))

        # --- what freeing the prior would buy ---------------------------------
        d_free = float(B[iy] @ (c_LS - c_MAP))
        print(f"     FREEING THE PRIOR would move c by {np.abs(c_LS-c_MAP)}"
              f" -> {HEADLINE_Y} residual by {d_free:+.4f} cm "
              f"= {d_free/e_hd:+.3f} sigma")
        verdict = ("BINDING" if pr_share.max() >= BINDING_PCT else
                   f"NOT BINDING (< {BINDING_PCT:g}% of precision on every coefficient)")
        print(f"     VERDICT: the D2 prior is {verdict}")

        for k, c in enumerate(COEFS):
            rows.append(dict(arm=arm, coef=c, fitted=c_fit[k], post_sd=ss[c].std(),
                             c_map_cond=c_MAP[k], c_ls_noprior=c_LS[k],
                             prior_share_precision_pct=pr_share[k]))
        rows.append(dict(arm=arm, coef="__summary__",
                         resid_raw_cm=r_raw[iy], resid_eff_cm=r_raw[iy] + d_fit,
                         resid_raw_sigma=r_raw[iy] / e_hd,
                         resid_eff_sigma=(r_raw[iy] + d_fit) / e_hd,
                         chi2_c0=chi0, chi2_fit=chi_fit, chi2_map=chi_map, chi2_ls=chi_ls,
                         removable_pct=100 * (chi0 - chi_ls) / chi0, taken_pct=taken,
                         free_prior_move_sigma=d_free / e_hd))

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\n  wrote {OUT}\n")


if __name__ == "__main__":
    main()
