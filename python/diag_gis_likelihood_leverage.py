#!/usr/bin/env python3
"""GATE 3.1, part 2 — how much likelihood grip does each target series actually
have, and what does a mid-century Greenland correction cost or buy?

VINTAGE-SELECTABLE since 2026-08-14 (thread 4 item 1.0).  This file was written
against extC and its argument below is stated in extC's terms; `--vintage extC`
still reproduces exactly that.  The DEFAULT is now L10 (Ladrillo 1.0, Greenland
A+B inside the joint likelihood), because the noise-model design for the next
calibration rests on these numbers and the extC ones predate the module that is
shipped.  Every output path and figure title carries the vintage tag, so the two
cannot be confused on disk.

What the vintage change does to the argument, stated up front:
  - extC's Greenland was stock SIMPLE and MISSED mid-century, and section 1's
    headline was that rho_gis = 0.985 reclassified that miss as correlated
    noise (n_eff 0.93).  Under L10 the A+B module fits that window, so the
    same measurement is now a TEST of whether the pathology was the module or
    the noise model.
  - section 3 asks what a correction that closed the REMAINING gis residual
    would cost and buy.  Under extC that correction was "what A+B would add";
    under L10, A+B is already in, so it is the leverage still on the table.
  - the 1942-1982 window is HELD FIXED across vintages so the numbers compare;
    the realised-correction table reports what the residual in it actually is.

Motivation.  diag_target_conflict.py shows the component-vs-total conflict is
NOT a splice artefact and NOT Dangendorf-vs-Frederikse: it is Frederikse's own
mid-century budget non-closure, and it is small relative to the total target's
own sigma.  That leaves the red team's outcome 3 -- "the joint calibration is
what limits Greenland" -- needing a mechanism.  This script tests the obvious
candidate: the per-series AR(1) noise model in calibrate_mcmc_ext.jl, whose
sigma AND rho are both sampled (half-normal(0,5) prior on sigma).  A rho near 1
reclassifies a decades-long systematic miss as correlated noise, which is nearly
free.

Two quantities, both computed at the pooled posterior medians of
(sd_series, rho_series) -- i.e. CONDITIONAL on the noise parameters, which is
the honest first cut; the sampler can additionally inflate sigma, so these are
UPPER bounds on the grip:

  1. n_eff -- effective independent observations in each series, from the AR(1)
     correlation time.  Mirrors the CarbonCycleEmulator finding that an AR(1)
     channel had n_eff ~ 0.8.

  2. delta log-likelihood for a systematic residual of amplitude A over the
     window where the Greenland target sits above the model, evaluated under
     three covariances: (a) the real AR(1)+band likelihood, (b) band sigma only
     (iid -- what the sigma column alone would suggest), (c) AR(1) only, band
     removed.  The three separate what the AR(1) absorbs from what the band
     retains.  CAUTION on n_eff: the n(1-rho)/(1+rho) formula describes the
     AR(1) TERM ALONE and therefore UNDERSTATES the grip, because diag(eps^2)
     contributes independent information at every year.  Comparison (c) is what
     makes that quantitative; (a) is the number to trust.

     Both a hard STEP and a smooth raised-cosine RAMP are evaluated: a step has
     sharp edges an AR(1) cannot absorb, which inflates its apparent cost, so
     the ramp is the conservative (lower-leverage) case.

  3. The REALISED correction -- the same calculation driven by the actual
     posterior-median residuals rather than a synthetic shape.  This matters
     because the model currently sits BELOW the total target in mid-century, so
     adding Greenland melt moves the total through the target rather than away
     from it, and the incremental cost is smaller than a from-zero step implies.
     Approximation: the dang channel's likelihood in calibrate_mcmc_ext.jl adds
     an lws term to the model total; the residual used here is taken straight
     from the postpred timeseries, which already carries it.

  python3 python/diag_gis_likelihood_leverage.py [--vintage=L10|extC]
                                                 [--post-source=subsample|chains]
Outputs (VINTAGE is the tag):
         outputs/diag_gis_likelihood_leverage_VINTAGE.csv
         outputs/diag_gis_likelihood_leverage_VINTAGE_summary.md
         figures/diag_gis_likelihood_leverage_VINTAGE.png
"""
import argparse
import os
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import multivariate_normal

# ---------------------------------------------------------------- constants
REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
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
BURN_FRAC = 0.5                       # discard first half of each chain
# The subsample is postprocess_mcmc_ext.jl's uniform stride over the pooled
# post-burn draws, so its marginal medians ARE the pooled medians -- verified
# 2026-08-14 against a stride-100 read of the four L10 chains: every sd_*/rho_*
# median agreed to < 0.01 posterior sd, at 10 MB instead of 8.8 GB.
POST_SOURCES = ("subsample", "chains")

SERIES = ["ais", "gsic", "gis", "steric", "dang"]
STEP_SERIES = "gis"                   # the series the Greenland module corrects
PAY_SERIES = "dang"                   # the series that must pay for it
STEP_Y0, STEP_Y1 = 1942, 1982         # window where the GIS target sits above the model
STEP_AMPS = np.arange(0.0, 1.01, 0.05)  # cm
REPORT_AMP = 0.65                     # cm -- centre of the memo's 0.5-0.7 cm miss
EPS_FLOOR = 0.05                      # cm; matches ϵband() in calibrate_mcmc_ext.jl
BAND_Z = 1.645                        # (hi-lo) = 2 * BAND_Z * sigma, matches the prep script
DANG_COL = "dang"                     # the total channel; its sigma is NOT an epsband column
CLOSURE_SIG_COL = "dang_closure_sig"  # gate-3.1 ruling, python/prep_recalib_targets_ext.py

STEP_LABEL = f"{STEP_Y0}-{STEP_Y1}"

# ---------------------------------------------------------------- vintage wiring
_ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
_ap.add_argument("--vintage", choices=sorted(VINTAGES), default="L10")
_ap.add_argument("--post-source", choices=POST_SOURCES, default="subsample",
                 help="where the (sd, rho) medians come from; 'chains' reads "
                      "4 x 2.2 GB, 'subsample' reads 10 MB for the same medians")
ARGS = _ap.parse_args()
VINTAGE = ARGS.vintage
VLABEL = VINTAGES[VINTAGE]["label"]
POSTPRED_CSV = VINTAGES[VINTAGE]["postpred"]
CHAIN_GLOB = VINTAGES[VINTAGE]["chain"]
SUBSAMPLE_CSV = VINTAGES[VINTAGE]["subsample"]

OUT_CSV = os.path.join(REPO, f"outputs/diag_gis_likelihood_leverage_{VINTAGE}.csv")
OUT_MD = os.path.join(REPO, f"outputs/diag_gis_likelihood_leverage_{VINTAGE}_summary.md")
OUT_PNG = os.path.join(REPO, f"figures/diag_gis_likelihood_leverage_{VINTAGE}.png")


def band_sigma(tg, col):
    """Per-year obs sigma exactly as make_series() builds it in calibrate_mcmc_ext.jl.

    CORRECTED 2026-08-12. The `dang` (total) channel is NOT an epsband() column
    there: its σ is the Dangendorf/altimetry SE in QUADRATURE with the LWS band
    term, and since the gate-3.1 ruling also with the per-year Frederikse
    budget-closure σ. Using (hi - lo) / 2z for it returns dang_sig ALONE --
    dang_lo/hi are built as ±z·dang_sig -- which understated the total's σ by
    the LWS term even before the ruling, and now by the closure term as well.
    That biases this diagnostic's `dang` penalty too NEGATIVE, i.e. it
    understates how good a deal the Greenland correction is."""
    if col == DANG_COL:
        eps_lws = np.maximum((tg["lws_hi"] - tg["lws_lo"]) / (2 * BAND_Z), EPS_FLOOR)
        s2 = tg["dang_sig"] ** 2 + eps_lws ** 2
        if CLOSURE_SIG_COL in tg.columns:
            s2 = s2 + tg[CLOSURE_SIG_COL].fillna(0.0) ** 2
        return np.maximum(np.sqrt(s2), EPS_FLOOR)
    s = (tg[col + "_hi"] - tg[col + "_lo"]) / (2 * BAND_Z)
    return np.maximum(s, EPS_FLOOR)


def ar1_cov(n, sigma, rho, eps):
    """Sigma_p * rho^|i-j| + diag(eps^2) -- the hetero_logl_ar1 covariance."""
    h = np.abs(np.subtract.outer(np.arange(n), np.arange(n)))
    return (sigma ** 2 / (1 - rho ** 2)) * rho ** h + np.diag(eps ** 2)


def logl(res, cov):
    return multivariate_normal.logpdf(res, mean=np.zeros(len(res)), cov=cov)


# ---------------------------------------------------------------- posterior noise params
NOISE_COLS = [f"{p}_{c}" for c in SERIES for p in ("sd", "rho")]
if ARGS.post_source == "subsample":
    post = pd.read_csv(SUBSAMPLE_CSV, usecols=NOISE_COLS)
    POST_PROV = (f"{len(post):,}-member posterior subsample "
                 f"({os.path.basename(SUBSAMPLE_CSV)}), a uniform stride over the "
                 f"pooled post-burn draws of seeds {CHAIN_SEEDS}")
else:
    frames = []
    for s in CHAIN_SEEDS:
        d = pd.read_csv(os.path.join(REPO, CHAIN_GLOB.format(seed=s)), usecols=NOISE_COLS)
        frames.append(d.iloc[int(len(d) * BURN_FRAC):])
    post = pd.concat(frames, ignore_index=True)
    POST_PROV = (f"pooled medians over seeds {CHAIN_SEEDS}, last "
                 f"{1 - BURN_FRAC:.0%} of each 2,000,000-step {VINTAGE} chain "
                 f"({len(post):,} draws)")
print(f"diag_gis_likelihood_leverage | vintage {VINTAGE} — {VLABEL}")
print(f"  noise parameters from the {ARGS.post_source}: {POST_PROV}")

# ---------------------------------------------------------------- targets / series extents
tg = pd.read_csv(TARGETS_CSV).set_index("year")

rows = []
for c in SERIES:
    ok = np.isfinite(tg[c].values)
    yrs = tg.index.values[ok]
    n = len(yrs)
    sd = float(post[f"sd_{c}"].median())
    rho = float(post[f"rho_{c}"].median())
    stat_sd = np.sqrt(sd ** 2 / (1 - rho ** 2))
    tau = -1.0 / np.log(rho) if 0 < rho < 1 else np.inf      # e-folding, years
    n_eff = n * (1 - rho) / (1 + rho)                        # AR(1) effective sample size
    eps = band_sigma(tg, c).values[ok]
    rows.append(dict(series=c, n_years=n, y0=yrs.min(), y1=yrs.max(),
                     sd=sd, rho=rho, stat_sd=stat_sd, tau_yr=tau, n_eff=n_eff,
                     band_sigma_mean=float(np.mean(eps))))
grip = pd.DataFrame(rows)

# ---------------------------------------------------------------- step-residual cost curves
def shape(yrs, kind):
    """Unit-amplitude residual over [STEP_Y0, STEP_Y1]: hard step or raised cosine."""
    inwin = (yrs >= STEP_Y0) & (yrs <= STEP_Y1)
    s = np.zeros(len(yrs))
    if kind == "step":
        s[inwin] = 1.0
    else:  # raised cosine, zero at both edges, 1 in the middle
        u = (yrs[inwin] - STEP_Y0) / (STEP_Y1 - STEP_Y0)
        s[inwin] = 0.5 * (1 - np.cos(2 * np.pi * u))
    return s


curves = {}
for c in [STEP_SERIES, PAY_SERIES]:
    ok = np.isfinite(tg[c].values)
    yrs = tg.index.values[ok]
    eps = band_sigma(tg, c).values[ok]
    sd = float(post[f"sd_{c}"].median())
    rho = float(post[f"rho_{c}"].median())
    cov_both = ar1_cov(len(yrs), sd, rho, eps)
    cov_ar1 = ar1_cov(len(yrs), sd, rho, np.zeros(len(yrs)))   # band removed
    base_both = logl(np.zeros(len(yrs)), cov_both)
    base_ar1 = logl(np.zeros(len(yrs)), cov_ar1)
    for kind in ("step", "ramp"):
        sh = shape(yrs, kind)
        d_both, d_iid, d_ar1 = [], [], []
        for a in STEP_AMPS:
            res = a * sh
            d_both.append(logl(res, cov_both) - base_both)
            d_iid.append(-0.5 * np.sum((res / eps) ** 2))
            d_ar1.append(logl(res, cov_ar1) - base_ar1)
        curves[(c, kind)] = dict(yrs=yrs, both=np.array(d_both),
                                 iid=np.array(d_iid), ar1=np.array(d_ar1))

ci = int(np.argmin(np.abs(STEP_AMPS - REPORT_AMP)))
gis_ar1 = curves[(STEP_SERIES, "step")]["both"][ci]
gis_iid = curves[(STEP_SERIES, "step")]["iid"][ci]
pay_ar1 = curves[(PAY_SERIES, "step")]["both"][ci]
pay_iid = curves[(PAY_SERIES, "step")]["iid"][ci]

# ------------------------------------------------- 3. the realised correction
# The GIS correction that would close the REMAINING gis residual exactly, and
# what it does to the total channel, at this vintage's posterior-median fit.
# Under extC that correction was "what the A+B module would add"; under L10 the
# module is already inside the likelihood, so it is the leverage still on offer.
pp = pd.read_csv(POSTPRED_CSV).set_index("year")
# postpred column names differ from target/series names
PP_COL = {"gis": "gis", "dang": "total"}
gis_corr = (pp["gis_obs"] - pp["gis_p50"]).rename("gis_correction")   # closes the gis residual

realised = []
for c in (STEP_SERIES, PAY_SERIES):
    ok = np.isfinite(tg[c].values)
    yrs = tg.index.values[ok]
    eps = band_sigma(tg, c).values[ok]
    sd, rho = float(post[f"sd_{c}"].median()), float(post[f"rho_{c}"].median())
    cov = ar1_cov(len(yrs), sd, rho, eps)
    p = PP_COL[c]
    # residual as the likelihood sees it: model - obs, on the years both cover
    res_now = (pp[f"{p}_p50"] - pp[f"{p}_obs"]).reindex(yrs).values
    corr = gis_corr.reindex(yrs).fillna(0.0).values
    good = np.isfinite(res_now)
    res_now = np.where(good, res_now, 0.0)
    res_after = res_now + np.where(good, corr, 0.0)
    d = logl(res_after, cov) - logl(res_now, cov)
    sel = (yrs >= STEP_Y0) & (yrs <= STEP_Y1)
    realised.append(dict(series=c, dlogl=d,
                         resid_now=float(np.mean(res_now[sel])),
                         resid_after=float(np.mean(res_after[sel])),
                         correction=float(np.mean(corr[sel]))))
realised = pd.DataFrame(realised)
net_realised = float(realised.dlogl.sum())

# ---------------------------------------------------------------- figure
fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
ax = axes[0]
for c, col in [(STEP_SERIES, "tab:blue"), (PAY_SERIES, "tab:red")]:
    ax.plot(STEP_AMPS, -curves[(c, "step")]["both"], color=col, lw=1.8,
            label=f"{c}: AR(1)+band (as calibrated)")
    ax.plot(STEP_AMPS, -curves[(c, "step")]["iid"], color=col, lw=1.2, ls="--",
            label=f"{c}: band sigma only (iid)")
    ax.plot(STEP_AMPS, -curves[(c, "step")]["ar1"], color=col, lw=1.0, ls=":",
            label=f"{c}: AR(1) only, band removed")
    ax.plot(STEP_AMPS, -curves[(c, "ramp")]["both"], color=col, lw=1.4, alpha=0.45,
            label=f"{c}: AR(1)+band, smooth ramp")
ax.axvline(REPORT_AMP, color="k", lw=0.8, ls=":")
ax.set_yscale("symlog", linthresh=1.0)
ax.set_xlabel(f"step residual amplitude over {STEP_LABEL} (cm)")
ax.set_ylabel("log-likelihood penalty (-delta logl)")
ax.set_title(f"Cost of a {STEP_LABEL} systematic offset — {VINTAGE}")
ax.legend(fontsize=8)
ax.grid(alpha=0.3)

ax = axes[1]
o = grip.sort_values("n_eff")
ax.barh(o.series, o.n_eff, color=["tab:blue" if s == STEP_SERIES else "0.6" for s in o.series])
for i, r in enumerate(o.itertuples()):
    ax.text(r.n_eff, i, f"  rho={r.rho:.3f}, n={r.n_years}", va="center", fontsize=8)
ax.set_xscale("log")
ax.set_xlabel("effective independent observations n_eff = n(1-rho)/(1+rho)")
ax.set_title(f"Likelihood grip per target series ({VINTAGE} posterior medians)")
ax.grid(alpha=0.3, axis="x")
fig.tight_layout()
os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
fig.savefig(OUT_PNG, dpi=140)

# ---------------------------------------------------------------- outputs
grip.to_csv(OUT_CSV, index=False)
with open(OUT_MD, "w") as fh:
    fh.write(f"# Gate 3.1 part 2 — likelihood grip per target series ({VINTAGE})\n\n")
    fh.write(f"Vintage: **{VLABEL}**. Noise parameters: {POST_PROV}.\n\n")
    fh.write("## Effective sample size\n\n")
    fh.write("| series | years | n | rho | AR(1) tau (yr) | n_eff | stationary sd (cm) | "
             "mean band sigma (cm) |\n|---|---|---|---|---|---|---|---|\n")
    for r in grip.itertuples():
        fh.write(f"| {r.series} | {r.y0}-{r.y1} | {r.n_years} | {r.rho:.3f} | {r.tau_yr:.1f} | "
                 f"**{r.n_eff:.2f}** | {r.stat_sd:.3f} | {r.band_sigma_mean:.3f} |\n")
    fh.write(f"\n## Cost of a {REPORT_AMP:.2f} cm systematic residual over {STEP_LABEL}\n\n")
    fh.write("Log-likelihood penalty (positive = worse fit) under three covariances.\n")
    fh.write("n_eff above describes the AR(1) term alone and so understates the grip; "
             "the AR(1)-only column is that understatement made explicit.\n\n")
    fh.write("| series | shape | AR(1)+band (as calibrated) | band only (iid) | "
             "AR(1) only | leverage the AR(1) removes |\n|---|---|---|---|---|---|\n")
    for c in (STEP_SERIES, PAY_SERIES):
        for kind in ("step", "ramp"):
            k = curves[(c, kind)]
            fh.write(f"| {c} | {kind} | {-k['both'][ci]:.2f} | {-k['iid'][ci]:.2f} | "
                     f"{-k['ar1'][ci]:.2f} | {k['iid'][ci] / k['both'][ci]:.0f}x |\n")
    net_step = -gis_ar1 + pay_ar1
    net_ramp = (-curves[(STEP_SERIES, 'ramp')]['both'][ci]
                + curves[(PAY_SERIES, 'ramp')]['both'][ci])
    fh.write(f"\n## The realised correction (actual {VINTAGE} residuals, not a synthetic shape)\n\n")
    fh.write(f"Mean over {STEP_LABEL}, cm; residual = model - obs.\n\n")
    fh.write("| series | residual now | correction applied | residual after | delta logl |\n")
    fh.write("|---|---|---|---|---|\n")
    for r in realised.itertuples():
        fh.write(f"| {r.series} | {r.resid_now:+.3f} | {r.correction:+.3f} | "
                 f"{r.resid_after:+.3f} | **{r.dlogl:+.2f}** |\n")
    fh.write(f"\nNet over both channels: **{net_realised:+.2f} log-likelihood units** "
             "in favour of the Greenland correction.\n")
    fh.write(f"\nNet log-likelihood available to the Greenland fix, as calibrated: "
             f"**{-gis_ar1:+.2f}** gained on {STEP_SERIES} against "
             f"**{pay_ar1:+.2f}** paid on {PAY_SERIES} = **{net_step:+.2f} net** (step), "
             f"**{net_ramp:+.2f} net** (smooth ramp).\n")

print(grip.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
print(f"\n{REPORT_AMP} cm residual over {STEP_LABEL}  (dlogl; negative = penalty)")
print(f"{'series':7s} {'shape':5s} {'AR1+band':>10s} {'iid band':>10s} {'AR1 only':>10s} {'removed':>8s}")
for c in (STEP_SERIES, PAY_SERIES):
    for kind in ("step", "ramp"):
        k = curves[(c, kind)]
        print(f"{c:7s} {kind:5s} {k['both'][ci]:10.3f} {k['iid'][ci]:10.3f} "
              f"{k['ar1'][ci]:10.3f} {k['iid'][ci] / k['both'][ci]:7.0f}x")
print()
print(f"realised correction (actual {VINTAGE} residuals):")
print(realised.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))
print(f"  NET {net_realised:+.2f} logl")
print()
print(f"net available to the Greenland fix: {-gis_ar1 + pay_ar1:+.2f} (step), "
      f"{-curves[(STEP_SERIES,'ramp')]['both'][ci] + curves[(PAY_SERIES,'ramp')]['both'][ci]:+.2f} (ramp)")
print(f"wrote {OUT_CSV}\nwrote {OUT_MD}\nwrote {OUT_PNG}")
