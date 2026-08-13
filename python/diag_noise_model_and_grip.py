#!/usr/bin/env python3
"""
diag_noise_model_and_grip.py — is the per-series AR(1) noise model the right
specification, are the five streams independent, and where does the total
target actually bind under the gate-3.1 sigma?

VINTAGE-SELECTABLE since 2026-08-14 (thread 4 item 1.0). Written against extC;
`--vintage extC` reproduces exactly that. The DEFAULT is now L10 (Ladrillo 1.0,
Greenland A+B inside the joint likelihood), because the noise model for the next
calibration is designed from these numbers and the extC ones predate the module
that is shipped. Output paths and figure titles carry the vintage tag.

Three questions that turned out to be one story, run as one diagnostic
(Marcus, 2026-08-12). They were separately: item 6.1 of
notes/note_2026-08-12_vivek_joint_calibration_artifacts.md (Vivek's R-matrix
drops rho_gmsl 0.960 -> 0.883), the caveat flagged in
python/prep_recalib_targets_ext.py that an anchor-shaped closure sigma may
double-count level correlation given rho ~ 0.97, and item 4.3 of
notes/handoff_2026-08-11_greenland_pass1_complete.md (re-check TE against a
modern OHC target).

-----------------------------------------------------------------------------
PRE-REGISTERED QUESTIONS -- stated before any number is computed
-----------------------------------------------------------------------------
A  STRUCTURAL DEPENDENCE. calibrate_mcmc_ext.jl scores four component streams
   AND a total stream, where the modelled total IS the sum of the modelled
   components plus observed LWS. So the five residual series cannot be
   independent. Is the dependence exact and algebraic, or only approximate?
   The test: dang_resid - sum(component resids) should equal a pure DATA term
   (the budget closure) plus the two model terms that differ between the
   component and total scopes (R19 glaciers, and the delta ramp applied to the
   gsic obs). PASS = the identity closes to numerical slop.

   READ THE CAVEAT (2026-08-14). This section is computed on POSTERIOR MEDIANS,
   and a median is not additive: median(sum) != sum(medians). The dependence
   itself is EXACT PER DRAW and can be read straight off the source --
   calibrate_mcmc_ext.jl builds tot_full = ais + gsic_tot + gis + te and scores
   it against the total target with observed LWS added, while the gsic
   COMPONENT channel scores gsic_flow (hindcast scope), so per draw
      total_model - sum(component_models) = gsic_tot - gsic_flow = the R19 seam,
   exactly, with no residual slack. posterior_predictive_ladrillo.jl assembles
   its `total` column the same way. So the "variance of the total residual
   explained by the identity" printed below is a p50-level SHADOW of an exact
   identity, contaminated by median non-additivity, and it is not a measure of
   the redundancy: it read 55.9% on extC and -322% on L10 (the L10 total
   residual is half the size, so the same non-additivity swamps it) while the
   underlying algebra did not change at all. The redundancy is 100% by
   construction; what the total channel adds beyond the components is ONE model
   term (the R19 seam) plus observed LWS plus its own likelihood weight.

B  EMPIRICAL CROSS-STREAM CORRELATION, on levels and on AR(1) innovations,
   plus the variance share of the leading principal component. If one common
   factor dominates, an independent per-series likelihood has nowhere to put
   it and must express it as within-series persistence.

C  IS AR(1) THE RIGHT SPECIFICATION? Six covariance models, each carrying the
   SAME diag(band^2) measurement term the calibrator uses, compared by BIC on
   the identical residual vector:
     white, AR(1) [incumbent], AR(2), ARMA(1,1),
     local level (random walk + noise -- the rho -> 1 limit),
     linear trend + AR(1) [is the "noise" actually a systematic drift?]
   Plus, for the incumbent: whitened-residual diagnostics (Ljung-Box and
   normality on L^-1 r, which is iid N(0,1) iff the model is right) and a
   profile of rho up to 1 to see whether a random walk is excluded at all.

D  DOES THE PERSISTENCE SURVIVE COMMON-FACTOR REMOVAL? Project the leading PC
   out of the residual matrix and re-estimate rho per series. If rho_gis falls
   from 0.985, Vivek's result carries to Ladrillo and the step-5
   pre-registration has to state both structures.

E  WHERE DOES THE TOTAL ACTUALLY BIND under the gate-3.1 sigma? Fisher
   information for a localised offset, s' Sigma^-1 s, by window, with and
   without the closure term -- reported as the sigma on a window-mean offset,
   which is the interpretable quantity.

F  ITEM 4.3 -- TE. The posterior samples thermal_alpha. Compare the
   implied expansion efficiency against the same quantity measured from the
   observations we hold, rather than against the recollection that Wong's
   te_alpha was "3x below physics".

THE RE-REFERENCING CAVEAT, stated up front because it cuts across C and E.
Every target and every model series is re-referenced to 1995-2005, so each
residual is pinned near zero in that window BY CONSTRUCTION and free to wander
away from it in both directions. That manufactures apparent persistence. The
calibrator's likelihood does not account for it, so section C's headline
comparison does not either -- and then repeats itself WITH the re-referencing
projection applied to every model, to show whether the verdict depends on it.

  python3 python/diag_noise_model_and_grip.py [--vintage=L10|extC]
                                             [--post-source=subsample|chains]
Writes (VINTAGE is the tag):
  outputs/diag_noise_model_streams_VINTAGE.csv     per-series noise-model comparison
  outputs/diag_noise_model_crosscorr_VINTAGE.csv   cross-stream correlation matrices
  outputs/diag_noise_model_grip_VINTAGE.csv        window-by-window grip of each stream
  outputs/diag_noise_model_summary_VINTAGE.md
  figures/diag_noise_model_and_grip_VINTAGE.png
"""
import argparse
import os

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import chi2, kurtosis, norm, skew

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
OBS = os.path.join(REPO, "data/observations")
TARGETS_CSV = os.path.join(REPO, "outputs/recalib_targets_ext.csv")

# The two posterior vintages this diagnostic can be run against. extC is the
# quarantined 2026-08-10 posterior with stock-SIMPLE Greenland (see
# outputs/quarantine/20260813_extc_vintage/README.md); L10 is Ladrillo 1.0.
VINTAGES = {
    "L10": dict(
        postpred=os.path.join(REPO, "outputs/postpred_L10_components_timeseries.csv"),
        chain="outputs/mcmc/chain_L10_seed{seed}_n2000000.csv",
        subsample=os.path.join(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_L10.csv"),
        label="L10 (Ladrillo 1.0; Greenland A+B in the joint likelihood)",
    ),
    "extC": dict(
        postpred=os.path.join(REPO, "outputs/quarantine/20260813_extc_vintage/"
                                    "postpred_extC_components_timeseries.csv"),
        chain="outputs/mcmc/chain_extC_seed{seed}_n2000000.csv",
        subsample=os.path.join(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_extC.csv"),
        label="extC (superseded 2026-08-13; stock-SIMPLE Greenland)",
    ),
}
CHAIN_SEEDS = [2026, 2027, 2028, 2029]
BURN_FRAC = 0.5
# The subsample is postprocess_mcmc_ext.jl's uniform stride over the pooled
# post-burn draws, so its marginal medians ARE the pooled medians -- verified
# 2026-08-14 against a stride-100 read of the four L10 chains: thermal_alpha and
# every sd_*/rho_* median agreed to < 0.01 posterior sd, at 10 MB not 8.8 GB.
POST_SOURCES = ("subsample", "chains")

_ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
_ap.add_argument("--vintage", choices=sorted(VINTAGES), default="L10")
_ap.add_argument("--post-source", choices=POST_SOURCES, default="subsample")
ARGS = _ap.parse_args()
VINTAGE = ARGS.vintage
VLABEL = VINTAGES[VINTAGE]["label"]
POSTPRED_CSV = VINTAGES[VINTAGE]["postpred"]
CHAIN_GLOB = VINTAGES[VINTAGE]["chain"]
SUBSAMPLE_CSV = VINTAGES[VINTAGE]["subsample"]

OHC_CSV = os.path.join(OBS, "ohc_spliced_zanna_igcc.csv")
OHC_ALT_CSV = os.path.join(OBS, "ohc_spliced_zanna_cheng.csv")
NOAA_STERIC = os.path.join(OBS, "raw/noaa_thermosteric_w0-2000m_yearly.dat")

OUT_STREAMS = os.path.join(REPO, f"outputs/diag_noise_model_streams_{VINTAGE}.csv")
OUT_XCORR = os.path.join(REPO, f"outputs/diag_noise_model_crosscorr_{VINTAGE}.csv")
OUT_GRIP = os.path.join(REPO, f"outputs/diag_noise_model_grip_{VINTAGE}.csv")
OUT_MD = os.path.join(REPO, f"outputs/diag_noise_model_summary_{VINTAGE}.md")
OUT_PNG = os.path.join(REPO, f"figures/diag_noise_model_and_grip_{VINTAGE}.png")

# ---- frame ------------------------------------------------------------------
SERIES = ["ais", "gsic", "gis", "steric", "dang"]
COMPONENTS = ["ais", "gsic", "gis", "steric"]
TOTAL = "dang"
# postpred column stem -> target column
PP_STEM = {"ais": "ais", "gsic": "glaciers", "gis": "gis", "steric": "te", "dang": "total"}
REF_WIN = (1995, 2005)          # the re-reference window every series shares
BAND_Z = 1.645
EPS_FLOOR = 0.05
CLOSURE_SIG_COL = "dang_closure_sig"
LJUNGBOX_LAGS = 10
RHO_PROFILE = np.concatenate([np.linspace(0.0, 0.98, 50),
                              1 - np.geomspace(2e-2, 1e-4, 25)])
# Windows for the grip audit (E). The first three are gate 3.1's own windows.
GRIP_WINDOWS = [(1900, 1930), (1942, 1982), (1950, 1980), (1993, 2018), (2000, 2024)]

# ---- F: thermal expansion ----------------------------------------------------
# te_sea_level[t] = te_sea_level[t-1] + dOHC[J] * te_alpha / (te_A * te_C * te_rho^2)
# MimiBRICK defaults, src/MimiBRICK.jl lines 121-123.
TE_A = 3.619e14                 # m^2, global ocean surface area
TE_C = 3991.86795711963         # J kg^-1 C^-1
TE_RHO = 1027.0                 # kg m^-3
# te_alpha is rho * alpha_v, so the physics range follows from the volumetric
# expansion coefficient of seawater, ~1.5-2.0e-4 /C at ocean-mean conditions.
ALPHA_V_RANGE = (1.5e-4, 2.0e-4)
NOAA_STERIC_COL = "WO"          # world ocean 0-2000 m, mm
TE_FIT_WIN = (2005, 2024)       # NOAA thermosteric coverage


def band_sigma(tg, col):
    """Per-year obs sigma exactly as make_series() builds it in
    calibrate_mcmc_ext.jl -- including the total's LWS and budget-closure terms
    (see python/diag_gis_likelihood_leverage.py for the same correction)."""
    if col == TOTAL:
        eps_lws = np.maximum((tg["lws_hi"] - tg["lws_lo"]) / (2 * BAND_Z), EPS_FLOOR)
        s2 = tg["dang_sig"] ** 2 + eps_lws ** 2
        if CLOSURE_SIG_COL in tg.columns:
            s2 = s2 + tg[CLOSURE_SIG_COL].fillna(0.0) ** 2
        return np.maximum(np.sqrt(s2), EPS_FLOOR)
    s = (tg[col + "_hi"] - tg[col + "_lo"]) / (2 * BAND_Z)
    return np.maximum(s, EPS_FLOOR)


def band_sigma_noclosure(tg):
    eps_lws = np.maximum((tg["lws_hi"] - tg["lws_lo"]) / (2 * BAND_Z), EPS_FLOOR)
    return np.maximum(np.sqrt(tg["dang_sig"] ** 2 + eps_lws ** 2), EPS_FLOOR)


# =============================================================================
# covariance models -- all carry the same diag(eps^2) measurement term
# =============================================================================
def _toeplitz(gam):
    n = len(gam)
    h = np.abs(np.subtract.outer(np.arange(n), np.arange(n)))
    return gam[h]


def cov_white(n, eps, p):
    return p[0] ** 2 * np.eye(n) + np.diag(eps ** 2)


def cov_ar1(n, eps, p):
    sd, rho = p
    gam = sd ** 2 / (1 - rho ** 2) * rho ** np.arange(n)
    return _toeplitz(gam) + np.diag(eps ** 2)


def cov_ar2(n, eps, p):
    sd, f1, f2 = p
    den = (1 + f2) * ((1 - f2) ** 2 - f1 ** 2)
    if den <= 0:
        return None
    g0 = sd ** 2 * (1 - f2) / den
    gam = np.empty(n)
    gam[0] = g0
    if n > 1:
        gam[1] = g0 * f1 / (1 - f2)
    for h in range(2, n):
        gam[h] = f1 * gam[h - 1] + f2 * gam[h - 2]
    return _toeplitz(gam) + np.diag(eps ** 2)


def cov_arma11(n, eps, p):
    sd, phi, th = p
    g0 = sd ** 2 * (1 + 2 * phi * th + th ** 2) / (1 - phi ** 2)
    g1 = sd ** 2 * (1 + phi * th) * (phi + th) / (1 - phi ** 2)
    gam = np.empty(n)
    gam[0], gam[1] = g0, g1
    for h in range(2, n):
        gam[h] = phi * gam[h - 1]
    return _toeplitz(gam) + np.diag(eps ** 2)


def cov_locallevel(n, eps, p):
    """Random walk plus noise -- the rho -> 1 limit of AR(1), nonstationary."""
    i = np.arange(1, n + 1)
    return p[0] ** 2 * np.minimum.outer(i, i) + np.diag(eps ** 2)


MODELS = {
    #  name:        (cov builder, n params, x0, bounds, mean-model dof)
    "white":        (cov_white, 1, [0.1], [(1e-4, 20)], 0),
    "AR(1)":        (cov_ar1, 2, [0.05, 0.9], [(1e-4, 20), (0.0, 0.9999)], 0),
    "AR(2)":        (cov_ar2, 3, [0.05, 0.9, 0.0],
                     [(1e-4, 20), (-1.99, 1.99), (-0.99, 0.99)], 0),
    "ARMA(1,1)":    (cov_arma11, 3, [0.05, 0.9, 0.2],
                     [(1e-4, 20), (0.0, 0.9999), (-0.99, 0.99)], 0),
    "local level":  (cov_locallevel, 1, [0.02], [(1e-6, 5)], 0),
    "trend+AR(1)":  (cov_ar1, 2, [0.05, 0.9], [(1e-4, 20), (0.0, 0.9999)], 2),
}


def gls_logl(r, cov, ndrift):
    """Gaussian log-likelihood, profiling out a polynomial mean of ndrift terms
    (0 = none, 2 = intercept + linear trend) by GLS."""
    n = len(r)
    try:
        L = np.linalg.cholesky(cov)
    except np.linalg.LinAlgError:
        return None
    logdet = 2.0 * np.sum(np.log(np.diag(L)))
    z = np.linalg.solve(L, r)
    if ndrift:
        t = np.linspace(-1, 1, n)
        X = np.vstack([t ** (k + 1) for k in range(ndrift)]).T if ndrift == 1 \
            else np.vstack([t ** k for k in range(ndrift)]).T
        Zx = np.linalg.solve(L, X)
        beta, *_ = np.linalg.lstsq(Zx, z, rcond=None)
        z = z - Zx @ beta
    return -0.5 * (n * np.log(2 * np.pi) + logdet + z @ z)


def fit_model(name, r, eps):
    build, npar, x0, bounds, ndrift = MODELS[name]
    n = len(r)

    def nll(p):
        cov = build(n, eps, p)
        if cov is None:
            return 1e12
        ll = gls_logl(r, cov, ndrift)
        return 1e12 if ll is None else -ll

    best, bv = None, np.inf
    for jitter in range(6):
        s = np.array(x0, float)
        if jitter:
            rng = np.random.default_rng(1000 + jitter)
            s = np.array([np.clip(v * np.exp(rng.normal(0, 0.5)), lo, hi)
                          for v, (lo, hi) in zip(x0, bounds)])
        res = minimize(nll, s, method="L-BFGS-B", bounds=bounds)
        if res.fun < bv:
            best, bv = res.x, res.fun
    k = npar + ndrift
    return dict(model=name, logl=-bv, k=k, bic=2 * bv + k * np.log(n), params=best)


def whiten(r, cov):
    L = np.linalg.cholesky(cov)
    return np.linalg.solve(L, r)


def ljung_box(z, lags=LJUNGBOX_LAGS):
    n = len(z)
    zc = z - z.mean()
    denom = np.sum(zc ** 2)
    q, out = 0.0, []
    for k in range(1, lags + 1):
        rk = np.sum(zc[k:] * zc[:-k]) / denom
        q += rk ** 2 / (n - k)
        out.append(rk)
    Q = n * (n + 2) * q
    return Q, chi2.sf(Q, lags), np.array(out)


def fit_ar1_rho(r, eps):
    """ML rho for the incumbent model, and the profile over RHO_PROFILE."""
    f = fit_model("AR(1)", r, eps)
    prof = []
    n = len(r)
    for rho in RHO_PROFILE:
        def nll(s):
            return -(gls_logl(r, cov_ar1(n, eps, [s[0], rho]), 0) or -1e12)
        res = minimize(nll, [max(f["params"][0], 1e-3)], method="L-BFGS-B",
                       bounds=[(1e-4, 20)])
        prof.append((rho, -res.fun))
    return f, np.array(prof)


def reref_basis(n, years, win):
    """Orthonormal basis B (n x n-1) of the range of the re-referencing operator
    P r = r - mean(r over win).

    P is a rank-(n-1) oblique projector, so P Sigma P' is SINGULAR and a naive
    Gaussian likelihood on it diverges -- the first run of this script returned
    BIC differences of -79,000 before this was handled. The fix is the standard
    REML device: transform to y = B' r, which is full rank, and compare every
    model on that same y."""
    m = ((years >= win[0]) & (years <= win[1])).astype(float)
    m = m / m.sum()
    P = np.eye(n) - np.outer(np.ones(n), m)
    # P is idempotent with range = m-perp, so an orthonormal basis of m-perp is
    # fixed by P. (The centring matrix I - 11'/n has range 1-perp, which is a
    # DIFFERENT subspace unless the reference window is the whole record -- the
    # first version of this used it and the assertion below caught it.)
    U, S, Vt = np.linalg.svd(m.reshape(1, n))
    B = Vt[1:].T
    assert B.shape[1] == n - 1, f"basis rank {B.shape[1]} != {n-1}"
    assert np.max(np.abs(P @ B - B)) < 1e-8, "basis is not in the range of P"
    return B


def selftest_machinery(n=126, sd=0.30, rho=0.5, band=0.05, seed=7):
    """MUTATION-STYLE SELF-TEST of section C's machinery, run before the real
    data. Simulate from AR(1)+band with KNOWN parameters and require that
    (1) the fitter recovers rho, (2) the Cholesky-whitened residuals pass
    Ljung-Box, and (3) BIC prefers the true model to the local level.

    Without this, section C's verdicts are indistinguishable from a broken
    whitener. NB the test is run at rho = 0.5, where the models ARE
    distinguishable; resolution_probe() below establishes where they stop
    being so, which is itself one of this script's findings."""
    rng = np.random.default_rng(seed)
    # The band term must not swamp the process, or the test fails for reasons
    # that have nothing to do with the machinery: at sd=0.1/band=0.2 the first
    # version of this test "failed" purely on signal-to-noise.
    eps = np.full(n, band)
    r = np.linalg.cholesky(cov_ar1(n, eps, [sd, rho])) @ rng.standard_normal(n)
    f = fit_model("AR(1)", r, eps)
    Q, p, _ = ljung_box(whiten(r, cov_ar1(n, eps, f["params"])))
    fl = fit_model("local level", r, eps)
    ok = (abs(f["params"][1] - rho) < 0.2, p > 0.01, f["bic"] < fl["bic"])
    print(f"  [self-test] AR(1)+band sd={sd} rho={rho} band={band}: recovered rho="
          f"{f['params'][1]:.3f} {'OK' if ok[0] else 'FAIL'}; Ljung-Box p={p:.3f} "
          f"{'OK' if ok[1] else 'FAIL'}; BIC prefers AR(1) by "
          f"{fl['bic']-f['bic']:.1f} {'OK' if ok[2] else 'FAIL'}")
    assert all(ok), ("the section-C machinery cannot recover a process it "
                     "generated itself; its verdicts would be meaningless")


def resolution_probe(n=126, stat_sd=0.35, band=0.05, reps=12, seed=11):
    """How persistent must a series be before BIC can no longer tell an AR(1)
    from a random walk at this record length? Calibrates section C: a verdict
    of 'local level beats AR(1)' means nothing at a rho where the probe shows
    the comparison is already saturated. Returns the table."""
    rng = np.random.default_rng(seed)
    eps = np.full(n, band)
    rows = []
    for rho in (0.5, 0.8, 0.9, 0.95, 0.97, 0.99, 0.995):
        # hold the STATIONARY sd fixed, not the innovation sd: otherwise the
        # process variance explodes as rho -> 1 and the comparison is confounded
        # by amplitude rather than persistence.
        sd = stat_sd * np.sqrt(1 - rho ** 2)
        picks, dbics = 0, []
        for _ in range(reps):
            r = np.linalg.cholesky(cov_ar1(n, eps, [sd, rho])) @ rng.standard_normal(n)
            fa, fl = fit_model("AR(1)", r, eps), fit_model("local level", r, eps)
            dbics.append(fl["bic"] - fa["bic"])
            picks += fa["bic"] < fl["bic"]
        rows.append(dict(rho_true=rho, frac_bic_picks_ar1=picks / reps,
                         median_dbic=float(np.median(dbics))))
        print(f"    rho={rho:<6.3f} BIC picks the TRUE AR(1) in "
              f"{picks}/{reps} draws   median dBIC(local level - AR1) "
              f"{np.median(dbics):+7.1f}")
    return pd.DataFrame(rows)


# =============================================================================
def main():
    print(f"diag_noise_model_and_grip | vintage {VINTAGE} — {VLABEL}")
    print(f"  posterior medians from the {ARGS.post_source} | "
          f"reref {REF_WIN[0]}-{REF_WIN[1]}")
    selftest_machinery()
    print("  [resolution probe] where does BIC stop telling AR(1) from a random walk?")
    probe = resolution_probe()
    tg = pd.read_csv(TARGETS_CSV).set_index("year")
    pp = pd.read_csv(POSTPRED_CSV).set_index("year")

    # ---- residuals, on each series' own valid years -------------------------
    res, epss, yrs, band_ratio = {}, {}, {}, {}
    for s in SERIES:
        stem = PP_STEM[s]
        ok = np.isfinite(tg[s].values) & np.isfinite(
            pp[f"{stem}_p50"].reindex(tg.index).values)
        y = tg.index.values[ok]
        res[s] = (pp[f"{stem}_p50"].reindex(tg.index).values[ok] - tg[s].values[ok])
        epss[s] = band_sigma(tg, s).values[ok]
        yrs[s] = y
        # resid sd / band sigma is the discriminator for section C: a stream whose
        # residual sits well INSIDE its own observation band gives the noise model
        # nothing to do, so "AR(1) vs white" on it is a comparison of two terms
        # that are both dominated by diag(band^2). Only streams with ratio ~1 put
        # the noise specification under load.
        band_ratio[s] = res[s].std() / epss[s].mean()
        print(f"  {s:7s} {y.min()}-{y.max()} ({len(y)} yr)  "
              f"resid mean {res[s].mean():+.3f} sd {res[s].std():.3f} cm  "
              f"band sigma mean {epss[s].mean():.3f}  "
              f"resid/band {band_ratio[s]:.2f}"
              f"{'   <-- noise model under load' if band_ratio[s] > 0.5 else ''}")

    common = sorted(set.intersection(*[set(yrs[s]) for s in SERIES]))
    ci = {s: np.isin(yrs[s], common) for s in SERIES}
    R = np.column_stack([res[s][ci[s]] for s in SERIES])
    print(f"\n  common years for the cross-stream work: {common[0]}-{common[-1]} "
          f"({len(common)})")

    md = []
    md.append(f"# Noise-model specification, stream dependence and target grip "
              f"({VINTAGE})\n")
    md.append(f"Vintage: **{VLABEL}**; posterior medians from the "
              f"{ARGS.post_source}; residual = model - target, cm; "
              f"common window {common[0]}-{common[-1]}.\n")

    # =====================================================================
    # A. structural dependence
    # =====================================================================
    print("\n[A] STRUCTURAL DEPENDENCE — is the total stream algebraically tied "
          "to the components?")
    tgc = tg.loc[common]
    closure = (tgc[COMPONENTS].sum(axis=1).values + tgc["lws"].values
               - tgc[TOTAL].values)
    lhs = R[:, SERIES.index(TOTAL)]
    # resid = model - target, so
    #   dang_resid = sum(comp_model) + lws_obs - dang_target
    #              = sum(comp_resid) + [sum(comp_target) + lws_obs - dang_target]
    #              = sum(comp_resid) + closure
    rhs = R[:, [SERIES.index(c) for c in COMPONENTS]].sum(axis=1) + closure
    gap = lhs - rhs
    print(f"  dang_resid            mean {lhs.mean():+.4f}  sd {lhs.std():.4f} cm")
    print(f"  sum(comp_resid)-closure  mean {rhs.mean():+.4f}  sd {rhs.std():.4f} cm")
    print(f"  UNEXPLAINED GAP       mean {gap.mean():+.4f}  sd {gap.std():.4f} cm "
          f"(expected: R19 glaciers + the gsic delta ramp, both real model terms)")
    print(f"  corr(dang_resid, sum(comp_resid)) = "
          f"{np.corrcoef(lhs, R[:, [SERIES.index(c) for c in COMPONENTS]].sum(axis=1))[0,1]:+.4f}")
    frac = 1 - np.var(gap) / np.var(lhs)
    print(f"  p50-level variance of the total residual 'explained' by the identity: "
          f"{frac:6.1%}")
    print("  CAVEAT: the identity is EXACT PER DRAW (tot_full = ais+gsic_tot+gis+te,"
          " scored\n          with observed LWS; the gsic COMPONENT channel uses"
          " gsic_flow, so the per-draw\n          difference is exactly the R19 seam)."
          " This number is a p50 shadow of it,\n          contaminated by median"
          " non-additivity, and is NOT a measure of the redundancy.")
    md.append(f"\n## A. The five streams are not independent — by construction\n\n"
              f"Per draw the tie is EXACT: `calibrate_mcmc_ext.jl` scores "
              f"`tot_full = ais + gsic_tot + gis + te` plus observed LWS against the "
              f"total target, while the gsic component channel scores `gsic_flow` "
              f"(hindcast scope), so `total_model − Σ(component_models)` is exactly "
              f"the R19 seam. The total stream is **100% redundant with the "
              f"components** apart from that one model term, the observed LWS, and "
              f"its own likelihood weight.\n\n"
              f"The p50-level statistic below is a SHADOW of that identity, not a "
              f"measure of it: medians are not additive, so it reads "
              f"**{frac:.1%}** here over {common[0]}-{common[-1]} with a gap of sd "
              f"{gap.std():.4f} cm. It was 55.9% on extC and −322% on L10 with the "
              f"algebra unchanged — the L10 total residual is half the size, so the "
              f"same non-additivity swamps it. Do not quote it as the redundancy.\n")

    # =====================================================================
    # B. cross-stream correlation
    # =====================================================================
    print("\n[B] CROSS-STREAM CORRELATION")
    C_lev = np.corrcoef(R.T)
    # AR(1) innovations at each series' own ML rho
    rho_ml = {}
    innov = []
    for j, s in enumerate(SERIES):
        f = fit_model("AR(1)", res[s], epss[s])
        rho_ml[s] = f["params"][1]
        x = R[:, j]
        innov.append(x[1:] - rho_ml[s] * x[:-1])
    C_inn = np.corrcoef(np.column_stack(innov).T)
    hdr = "        " + "".join(f"{s:>9s}" for s in SERIES)
    print("  residual LEVELS")
    print(hdr)
    for i, s in enumerate(SERIES):
        print(f"  {s:6s}" + "".join(f"{C_lev[i,j]:+9.3f}" for j in range(len(SERIES))))
    print("  AR(1) INNOVATIONS (at each series' own ML rho)")
    print(hdr)
    for i, s in enumerate(SERIES):
        print(f"  {s:6s}" + "".join(f"{C_inn[i,j]:+9.3f}" for j in range(len(SERIES))))
    Z = (R - R.mean(0)) / R.std(0)
    ev = np.linalg.eigvalsh(np.cov(Z.T))[::-1]
    pc1 = ev[0] / ev.sum()
    print(f"  leading PC of the standardised residual matrix: {pc1:.1%} of variance")
    md.append(f"\n## B. Cross-stream correlation\n\n"
              f"Leading PC of the standardised residuals carries **{pc1:.1%}** of the "
              f"variance. Correlation of the AR(1) innovations (levels correlation is "
              f"inflated by the shared persistence) is tabulated in "
              f"`outputs/diag_noise_model_crosscorr.csv`.\n")
    pd.concat([
        pd.DataFrame(C_lev, index=SERIES, columns=SERIES).assign(kind="levels"),
        pd.DataFrame(C_inn, index=SERIES, columns=SERIES).assign(kind="innovations"),
    ]).to_csv(OUT_XCORR)

    # =====================================================================
    # C. is AR(1) the right specification?
    # =====================================================================
    print("\n[C] NOISE-MODEL COMPARISON (BIC; lower is better; Delta vs AR(1))")
    print(f"  {'series':8s} " + "".join(f"{m:>14s}" for m in MODELS))
    rows, profiles = [], {}
    for s in SERIES:
        fits = {m: fit_model(m, res[s], epss[s]) for m in MODELS}
        b0 = fits["AR(1)"]["bic"]
        print(f"  {s:8s} " + "".join(f"{fits[m]['bic']-b0:+14.1f}" for m in MODELS))
        for m, f in fits.items():
            # Whitened-residual test for EVERY model, not just the incumbent:
            # the claim "no member of this family whitens the residuals" needs
            # to be evidence, not an inference from the AR(1) row alone.
            build, _, _, _, nd = MODELS[m]
            cv = build(len(res[s]), epss[s], f["params"])
            try:
                Qm, pm, _ = ljung_box(whiten(res[s], cv))
            except np.linalg.LinAlgError:
                Qm, pm = np.nan, np.nan
            rows.append(dict(series=s, model=m, resid_over_band=band_ratio[s],
                             logl=f["logl"], k=f["k"],
                             bic=f["bic"], dbic_vs_ar1=f["bic"] - b0,
                             ljungbox_Q=Qm, ljungbox_p=pm,
                             params="; ".join(f"{v:.6g}" for v in f["params"])))
        # incumbent diagnostics
        fa, prof = fit_ar1_rho(res[s], epss[s])
        profiles[s] = prof
        z = whiten(res[s], cov_ar1(len(res[s]), epss[s], fa["params"]))
        Q, p, _ = ljung_box(z)
        lo = prof[prof[:, 1] >= prof[:, 1].max() - 1.92, 0]
        print(f"           ML rho {fa['params'][1]:.4f}   whitened-resid "
              f"Ljung-Box Q={Q:6.1f} p={p:.4f}   skew {skew(z):+.2f} "
              f"kurt {kurtosis(z):+.2f}   rho 95% profile [{lo.min():.3f}, "
              f"{lo.max():.4f}]{'  <-- INCLUDES 1' if lo.max() > 0.9985 else ''}")
    streams = pd.DataFrame(rows)
    streams.to_csv(OUT_STREAMS, index=False)
    loaded = [s for s in SERIES if band_ratio[s] > 0.5]
    md.append(f"\n## C. Which streams put the noise model under load\n\n"
              f"resid sd / mean band σ: "
              + ", ".join(f"{s} {band_ratio[s]:.2f}" for s in SERIES)
              + f". Only **{', '.join(loaded) if loaded else 'none'}** exceed 0.5, "
              f"i.e. only there does the residual approach its own observation band; "
              f"on the rest the likelihood is band-dominated and 'AR(1) vs white' "
              f"compares two terms that barely enter. Full BIC table in "
              f"`{os.path.basename(OUT_STREAMS)}`.\n")
    print("\n  [C1b] Ljung-Box p on the whitened residuals, EVERY model "
          "(the self-test returns p=0.84 on data it generated, so a p here is "
          "a statement about the model, not the test)")
    print(f"  {'series':8s} " + "".join(f"{m:>14s}" for m in MODELS))
    for s in SERIES:
        sub = streams[streams.series == s].set_index("model")
        print(f"  {s:8s} " + "".join(f"{sub.loc[m,'ljungbox_p']:14.4f}" for m in MODELS))

    # re-referencing sensitivity
    print("\n  [C2] same comparison with the 1995-2005 re-referencing projection "
          "applied to every model")
    print(f"  {'series':8s} " + "".join(f"{m:>14s}" for m in MODELS))
    for s in SERIES:
        n = len(res[s])
        B = reref_basis(n, yrs[s], REF_WIN)
        y = B.T @ res[s]
        out = {}
        for m in MODELS:
            build, npar, x0, bounds, ndrift = MODELS[m]
            # the re-referencing annihilates a constant, so an intercept term
            # carries no information under the transform -- drop it
            nd = max(ndrift - 1, 0)

            def nll(p, build=build, nd=nd, n=n, s=s, B=B, y=y):
                cov = build(n, epss[s], p)
                if cov is None:
                    return 1e12
                ll = gls_logl(y, B.T @ cov @ B, nd)
                return 1e12 if ll is None else -ll
            best, bv = None, np.inf
            for j in range(4):
                st = np.array(x0, float)
                if j:
                    rng = np.random.default_rng(500 + j)
                    st = np.array([np.clip(v * np.exp(rng.normal(0, 0.5)), lo, hi)
                                   for v, (lo, hi) in zip(x0, bounds)])
                rr = minimize(nll, st, method="L-BFGS-B", bounds=bounds)
                if rr.fun < bv:
                    best, bv = rr.x, rr.fun
            out[m] = 2 * bv + (npar + nd) * np.log(n - 1)
        b0 = out["AR(1)"]
        print(f"  {s:8s} " + "".join(f"{out[m]-b0:+14.1f}" for m in MODELS))

    # =====================================================================
    # D. does the persistence survive common-factor removal?
    # =====================================================================
    print("\n[D] rho AFTER PROJECTING OUT THE LEADING COMMON FACTOR")
    U, S, Vt = np.linalg.svd(Z - Z.mean(0), full_matrices=False)
    pc = U[:, 0]
    print(f"  {'series':8s} {'rho (as calibrated)':>20s} {'rho ML':>9s} "
          f"{'rho after PC1 removed':>23s}")
    dstats = []
    for j, s in enumerate(SERIES):
        x = R[:, j]
        beta = np.dot(pc, x) / np.dot(pc, pc)
        xr = x - beta * pc
        e = epss[s][ci[s]]
        f_before = fit_model("AR(1)", x, e)
        f_after = fit_model("AR(1)", xr, e)
        dstats.append(dict(series=s, rho_ml=f_before["params"][1],
                           rho_pc_removed=f_after["params"][1],
                           pc1_loading=beta))
        print(f"  {s:8s} {rho_ml[s]:20.4f} {f_before['params'][1]:9.4f} "
              f"{f_after['params'][1]:23.4f}")
    dd = pd.DataFrame(dstats)

    # =====================================================================
    # E. where does the total actually bind?
    # =====================================================================
    print("\n[E] GRIP — sigma on a window-MEAN offset, cm (smaller = tighter)")
    print(f"  {'window':12s} " + "".join(f"{s:>10s}" for s in SERIES)
          + f"{'dang (no closure)':>20s}")
    griprows = []
    for w in GRIP_WINDOWS:
        line = f"  {w[0]}-{w[1]:4d} "
        for s in SERIES:
            y = yrs[s]
            sig = np.zeros(len(y))
            sig[(y >= w[0]) & (y <= w[1])] = 1.0
            if sig.sum() == 0:
                line += f"{'-':>10s}"
                continue
            f = fit_model("AR(1)", res[s], epss[s])
            cov = cov_ar1(len(y), epss[s], f["params"])
            info = sig @ np.linalg.solve(cov, sig)
            line += f"{1/np.sqrt(info):10.3f}"
            griprows.append(dict(window=f"{w[0]}-{w[1]}", series=s,
                                 sigma_offset_cm=1 / np.sqrt(info), closure="on"))
        # the total without the closure term
        y = yrs[TOTAL]
        e0 = band_sigma_noclosure(tg).values[np.isin(tg.index.values, y)]
        sig = np.zeros(len(y))
        sig[(y >= w[0]) & (y <= w[1])] = 1.0
        f0 = fit_model("AR(1)", res[TOTAL], e0)
        cov0 = cov_ar1(len(y), e0, f0["params"])
        info0 = sig @ np.linalg.solve(cov0, sig)
        line += f"{1/np.sqrt(info0):20.3f}"
        griprows.append(dict(window=f"{w[0]}-{w[1]}", series=TOTAL,
                             sigma_offset_cm=1 / np.sqrt(info0), closure="off"))
        print(line)
    grip = pd.DataFrame(griprows)
    grip.to_csv(OUT_GRIP, index=False)

    # =====================================================================
    # F. item 4.3 -- thermal expansion efficiency
    # =====================================================================
    print("\n[F] ITEM 4.3 — TE expansion efficiency vs the observations we hold")
    cols = ["thermal_alpha"]
    if ARGS.post_source == "subsample":
        ta = pd.read_csv(SUBSAMPLE_CSV, usecols=cols)["thermal_alpha"]
    else:
        frames = []
        for sd in CHAIN_SEEDS:
            d = pd.read_csv(os.path.join(REPO, CHAIN_GLOB.format(seed=sd)), usecols=cols)
            frames.append(d.iloc[int(len(d) * BURN_FRAC):])
        ta = pd.concat(frames, ignore_index=True)["thermal_alpha"]
    q = ta.quantile([0.05, 0.5, 0.95]).values
    eff = lambda a: a / (TE_A * TE_C * TE_RHO ** 2) * 1e22 * 100.0   # cm per 1e22 J
    print(f"  {VINTAGE} thermal_alpha  p05/p50/p95 = {q[0]:.4f} / {q[1]:.4f} / "
          f"{q[2]:.4f} kg m^-3 C^-1  (n={len(ta):,})")
    print(f"  implied efficiency  p05/p50/p95 = {eff(q[0]):.4f} / {eff(q[1]):.4f} / "
          f"{eff(q[2]):.4f} cm per 1e22 J")
    phys = [r * TE_RHO for r in ALPHA_V_RANGE]
    print(f"  physics range (alpha_v {ALPHA_V_RANGE[0]:.1e}-{ALPHA_V_RANGE[1]:.1e} /C "
          f"x rho): te_alpha {phys[0]:.4f}-{phys[1]:.4f}  -> "
          f"{eff(phys[0]):.4f}-{eff(phys[1]):.4f} cm per 1e22 J")

    # empirical efficiency: regress NOAA thermosteric on observed OHC
    ns = pd.read_csv(NOAA_STERIC, sep=r"\s+")
    ns["year"] = np.floor(ns["YEAR"]).astype(int)
    steric_obs = ns.groupby("year")[NOAA_STERIC_COL].mean() / 10.0    # mm -> cm
    emp = {}
    for tag, path in (("Zanna+IGCC", OHC_CSV), ("Zanna+Cheng", OHC_ALT_CSV)):
        oh = pd.read_csv(path, comment="#")
        ycol = [c for c in oh.columns if c.lower().startswith("year")][0]
        vcol = [c for c in oh.columns if c != ycol][0]
        o = pd.Series(oh[vcol].values, index=oh[ycol].astype(int).values)
        yy = sorted(set(steric_obs.index) & set(o.index)
                    & set(range(TE_FIT_WIN[0], TE_FIT_WIN[1] + 1)))
        if len(yy) < 5:
            continue
        x = o.loc[yy].values
        y = steric_obs.loc[yy].values
        slope = np.polyfit(x, y, 1)[0]                                # cm per 1e22 J
        emp[tag] = slope
        print(f"  OBSERVED efficiency, {tag:12s} {TE_FIT_WIN[0]}-{TE_FIT_WIN[1]} "
              f"(n={len(yy)}): {slope:.4f} cm per 1e22 J")

    md.append(f"\n## F. Item 4.3 — thermal expansion\n\n"
              f"{VINTAGE} `thermal_alpha` p50 = **{q[1]:.4f}** kg m^-3 C^-1 "
              f"(90% {q[0]:.4f}-{q[2]:.4f}), i.e. **{eff(q[1]):.4f} cm per 1e22 J**. "
              f"Physics range {eff(phys[0]):.4f}-{eff(phys[1]):.4f}. Observed "
              + "; ".join(f"{k} {v:.4f}" for k, v in emp.items()) + " cm per 1e22 J.\n")

    with open(OUT_MD, "w") as fh:
        fh.write("".join(md))
    make_figure(SERIES, res, yrs, epss, profiles, C_inn, dd, grip)
    for p in (OUT_STREAMS, OUT_XCORR, OUT_GRIP, OUT_MD, OUT_PNG):
        print(f"wrote {os.path.relpath(p, REPO)}")


def make_figure(series, res, yrs, epss, profiles, C_inn, dd, grip):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(2, 2, figsize=(15, 9))
    a = ax[0, 0]
    for s in series:
        a.plot(yrs[s], res[s], lw=1.4, label=s)
    a.axhline(0, color="k", lw=0.8)
    a.axvspan(REF_WIN[0], REF_WIN[1], color="0.85", zorder=0)
    a.set_title(f"{VINTAGE} residuals (model − target), cm\n"
                f"grey = the {REF_WIN[0]}–{REF_WIN[1]} re-reference window")
    a.set_xlabel("year"); a.set_ylabel("cm"); a.legend(fontsize=8); a.grid(alpha=0.3)

    a = ax[0, 1]
    for s in series:
        p = profiles[s]
        a.plot(1 - p[:, 0], p[:, 1] - p[:, 1].max(), lw=1.4, label=s)
    a.axhline(-1.92, color="crimson", ls="--", lw=1.2, label="95% (−1.92)")
    a.set_xscale("log"); a.invert_xaxis()
    a.set_xlabel(r"$1-\rho$   (right edge = random walk)")
    a.set_ylabel("profile log-likelihood − max")
    a.set_title(r"AR(1) $\rho$ profile: is a random walk excluded?")
    a.set_ylim(-12, 0.5); a.legend(fontsize=8); a.grid(alpha=0.3)

    a = ax[1, 0]
    im = a.imshow(C_inn, vmin=-1, vmax=1, cmap="RdBu_r")
    a.set_xticks(range(len(series))); a.set_xticklabels(series, rotation=45)
    a.set_yticks(range(len(series))); a.set_yticklabels(series)
    for i in range(len(series)):
        for j in range(len(series)):
            a.text(j, i, f"{C_inn[i,j]:+.2f}", ha="center", va="center", fontsize=8)
    a.set_title("cross-stream correlation of AR(1) innovations")
    fig.colorbar(im, ax=a, fraction=0.046)

    a = ax[1, 1]
    g = grip[grip.closure == "on"].pivot(index="window", columns="series",
                                         values="sigma_offset_cm")
    g.plot(kind="bar", ax=a, width=0.8)
    a.set_ylabel("σ on a window-mean offset (cm)")
    a.set_title("grip by window — smaller is a tighter constraint")
    a.tick_params(axis="x", rotation=30); a.grid(alpha=0.3, axis="y")
    a.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    main()
