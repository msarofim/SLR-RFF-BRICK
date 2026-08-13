#!/usr/bin/env python3
"""
diag_iceflow0_identifiability.py — is `ais_iceflow0` a RIDGE, a MULTIMODALITY, or
simply UNIDENTIFIED?

WHY THIS EXISTS
    The standing hypothesis (handoff 2026-08-13 section 3) was that
    `ais_iceflow0` rides a correlated ridge with the rest of the AIS geometry
    block and that the fix is a reparameterisation along it, as `ais_runoff_Ton`
    did for the (h0, c) pair. `python/diag_block_ridge.py` falsifies that: the
    worst-mixing direction between the four chains is
    `ais_iceflow0 +1.00` with every other loading <= 0.06, the within-chain
    correlation matrix of the geometry block has condition number 8, and no pair
    reaches |r| = 0.8. It is not a ridge. A rotation would not touch it.

    That leaves three candidate diagnoses, which imply completely different fixes:

      A. UNIDENTIFIED. The likelihood is nearly flat in this parameter over its
         prior range; each chain is diffusing slowly through the PRIOR and they
         happen to be in different places. Fix: say so — fix the parameter, or
         accept the pooled marginal as (approximately) the prior and stop calling
         it a posterior. A better sampler buys nothing real.
      B. MULTIMODAL. Genuinely separated posterior modes (plausible here: the AIS
         is bimodal in tipped/not-tipped, and iceflow0 sets the grounding-line
         flux). Fix: mode-jumping or tempering. A longer chain in one mode is
         worthless.
      C. IDENTIFIED BUT SLOW. A single well-defined mode with a badly scaled
         proposal along this axis. Fix: proposal scaling. This is the only one of
         the three where "run it better" is the answer.

FOUR TESTS THAT SEPARATE THEM
    1. POOLED WIDTH vs PRIOR WIDTH. If the pooled marginal is about as wide as
       the prior, the data are not constraining the parameter (A). Reported
       against the paleo prior sd the calibrator actually uses.
    2. WITHIN-CHAIN WIDTH vs POOLED. Each chain narrow, the pool wide = chains in
       different places (A or B); each chain as wide as the pool = mixing (C).
    3. TRACE SHAPE. Decile means across the post-burn half. A monotone DRIFT is
       diffusion (A/C); discrete JUMPS between levels with dwell time in each is
       multimodality (B).
    4. LIKELIHOOD GRIP. Correlation of the parameter with `log_post` within a
       chain, and the spread of `log_post` across chains. If the chains sit at
       different iceflow0 with the SAME log-posterior, the objective genuinely
       cannot tell them apart (A).

  python3 python/diag_iceflow0_identifiability.py [--param=ais_iceflow0]
Outputs:
  outputs/diag_iceflow0_identifiability.md
"""
import os
import subprocess
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAIN = os.path.join(REPO, "outputs/mcmc/chain_{tag}_seed{seed}_n{n}.csv")
TAG, NITER = "L10", 2000000
SEEDS = [2026, 2027, 2028, 2029]
NBURN_FRAC = 0.5
THIN = 50
N_DECILE = 10
GEO_PRIOR_FILE = os.path.join(REPO, "outputs/paleo_geo_prior_ton.csv")
# one file per parameter tested, so a second --param cannot silently
# overwrite the first one's verdict
OUT_MD_FMT = os.path.join(REPO, "outputs/diag_identifiability_{param}.md")

PARAM = "ais_iceflow0"
for a in sys.argv[1:]:
    if a.startswith("--param="):
        PARAM = a.split("=")[1]

COMMIT = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True).stdout.strip()


# The Greenland priors live in calibrate_mcmc_ext.jl, not the paleo file, so the
# same test can be pointed at a gis_* parameter with --param.
GIS_PRIOR = {"gis_c1": (0.032766, 0.050, 0.0, 4.0), "gis_c0": (0.040429, 0.100, 0.0, 4.0),
             "gis_f": (0.782569, 0.30, 0.02, 0.98),
             "gis_alpha_f": (0.0028487, 0.020, 0.0, 0.5),
             "gis_beta_f": (0.0073684, 0.050, 1e-6, 0.5),
             "gis_alpha_s": (0.0070727, 0.020, 0.0, 0.2),
             "gis_beta_s": (0.0010000, 0.020, 1e-6, 0.2)}


def prior_moments(name):
    if name in GIS_PRIOR:
        m, sd, lo, hi = GIS_PRIOR[name]
        return dict(mean=m, sd=sd, lo=lo, hi=hi)
    rows = [l.strip().split(",") for l in open(GEO_PRIOR_FILE)
            if l.strip() and not l.startswith("#")]
    names = next(r[1:] for r in rows if r[0] in ("name", "names"))
    if name not in names:
        return None
    i = names.index(name)
    g = lambda k: float(next(r[1:] for r in rows if r[0] == k)[i])
    return dict(mean=g("mean"), sd=g("sd"), lo=g("lo"), hi=g("hi"))


def main():
    pri = prior_moments(PARAM)
    data = {}
    for sd in SEEDS:
        f = CHAIN.format(tag=TAG, seed=sd, n=NITER)
        d = pd.read_csv(f, usecols=[PARAM, "log_post"])
        d = d.iloc[int(len(d) * NBURN_FRAC)::THIN].reset_index(drop=True)
        data[sd] = d
        print(f"  seed{sd}: {len(d)} draws", flush=True)

    pooled = pd.concat([d[PARAM] for d in data.values()])
    within = np.mean([d[PARAM].std() for d in data.values()])

    L = [f"# Is `{PARAM}` a ridge, a multimodality, or unidentified?", "",
         f"- commit `{COMMIT}`; tag `{TAG}`; {len(SEEDS)} chains, first "
         f"{NBURN_FRAC:.0%} burned, thinned 1-in-{THIN}",
         f"- `diag_block_ridge.py` already ruled out RIDGE: the worst-mixing "
         f"direction is `{PARAM} +1.00`, every other loading <= 0.06, block "
         f"correlation condition number 8.", ""]

    # ---- test 1 + 2 --------------------------------------------------------
    L += ["## 1-2. Widths — is the pool the prior, and is each chain narrower?", "",
          "| quantity | value |", "|---|---|",
          f"| prior sd | {pri['sd']:.4f} |" if pri else "| prior sd | (not found) |",
          f"| pooled posterior sd | {pooled.std():.4f} |",
          f"| mean WITHIN-chain sd | {within:.4f} |"]
    if pri:
        L += [f"| pooled / prior | **{pooled.std() / pri['sd']:.2f}** |",
              f"| within / pooled | **{within / pooled.std():.2f}** |",
              f"| prior mean, range | {pri['mean']:.3f}, [{pri['lo']:.3f}, {pri['hi']:.3f}] |"]
    L += ["", "| chain | p05 | p50 | p95 | sd |", "|---|---|---|---|---|"]
    for sd in SEEDS:
        v = data[sd][PARAM]
        L.append(f"| seed{sd} | {v.quantile(.05):.3f} | {v.quantile(.5):.3f} | "
                 f"{v.quantile(.95):.3f} | {v.std():.3f} |")
    L.append(f"| POOLED | {pooled.quantile(.05):.3f} | {pooled.quantile(.5):.3f} | "
             f"{pooled.quantile(.95):.3f} | {pooled.std():.3f} |")
    L.append("")

    # ---- test 3 ------------------------------------------------------------
    L += [f"## 3. Trace shape — drift (diffusion) or jumps (modes)?", "",
          f"Decile means across the post-burn half, per chain. A monotone walk is "
          f"diffusion; a step between levels with dwell time is a mode change.", "",
          "| chain | " + " | ".join(f"d{i+1}" for i in range(N_DECILE)) + " | monotone? |",
          "|---" * (N_DECILE + 2) + "|"]
    for sd in SEEDS:
        v = data[sd][PARAM].values
        dec = [float(np.mean(c)) for c in np.array_split(v, N_DECILE)]
        dif = np.diff(dec)
        mono = "yes" if (all(dif > 0) or all(dif < 0)) else "no"
        L.append(f"| seed{sd} | " + " | ".join(f"{x:.2f}" for x in dec) + f" | {mono} |")
    L.append("")

    # ---- test 4 ------------------------------------------------------------
    L += ["## 4. Likelihood grip — do the chains differ in log-posterior?", "",
          "| chain | corr(param, log_post) | mean log_post | sd log_post |",
          "|---|---|---|---|"]
    for sd in SEEDS:
        d = data[sd]
        L.append(f"| seed{sd} | {d[PARAM].corr(d['log_post']):+.3f} | "
                 f"{d['log_post'].mean():.2f} | {d['log_post'].std():.2f} |")
    lp = [data[s]["log_post"].mean() for s in SEEDS]
    lp_within = np.mean([data[s]["log_post"].std() for s in SEEDS])
    L += ["", f"Spread of chain-mean log_post: **{np.std(lp):.2f}** against a "
          f"within-chain sd of {lp_within:.2f} "
          f"(range {min(lp):.2f} to {max(lp):.2f}).", ""]

    # ---- verdict -----------------------------------------------------------
    pool_prior = pooled.std() / pri["sd"] if pri else np.nan
    narrow = within / pooled.std()
    same_lp = np.std(lp) < lp_within
    L += ["## VERDICT", ""]
    if pri and pool_prior > 0.75 and narrow < 0.75 and same_lp:
        L += [f"**UNIDENTIFIED (diagnosis A).** The pooled marginal is "
              f"{pool_prior:.2f} of the prior width while each chain is only "
              f"{narrow:.2f} of the pool, and the chains sit at different "
              f"`{PARAM}` with log-posteriors that differ by less than their own "
              f"within-chain scatter. The objective cannot tell these values apart.",
              "",
              "**Consequences.** (i) A reparameterisation is the WRONG fix — there is "
              "no ridge to rotate, and rotating an unidentified axis leaves it "
              "unidentified. (ii) So is a longer chain: it would sample the prior more "
              "thoroughly. (iii) The honest options are to FIX the parameter at a "
              "defensible value and say so, to report the pooled marginal as "
              "approximately the prior rather than as a posterior, or to add "
              "information that grips it (an observational constraint on the "
              "grounding-line flux). (iv) R-hat on this axis is not a sampler failure "
              "to be engineered away; it is the correct report that the data are silent."]
    elif narrow < 0.5 and not same_lp:
        L += ["**MULTIMODAL or basin-separated (diagnosis B).** Chains are narrow, "
              "the pool is wide, and they do NOT agree on log-posterior — they are in "
              "different basins of different quality. Mode-jumping or tempering; a "
              "longer chain in one basin is worthless."]
    else:
        L += ["**Not cleanly separated by these tests.** Read the tables above rather "
              "than a label: widths, trace shape and log-posterior spread point "
              "different ways, which usually means more than one thing is happening."]
    L.append("")

    out_md = OUT_MD_FMT.format(param=PARAM)
    with open(out_md, "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"\nwrote {out_md}", flush=True)


if __name__ == "__main__":
    main()
