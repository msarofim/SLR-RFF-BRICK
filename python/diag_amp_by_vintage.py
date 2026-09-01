#!/usr/bin/env python3
"""
diag_amp_by_vintage.py — `ais_gmst_amp` posterior centre by refit, ON ONE ESTIMATOR,
                         WITH THE MEDIAN'S OWN ERROR BAR.

WHY THIS EXISTS (2026-09-01)
  The L21->L23 story turns on a 2x2 of `ais_gmst_amp` medians, and L25 was launched to read
  against two of its cells. Reading L25 with a different estimator than produced them would
  answer a different question (`like_for_like_forcing`) -- and that risk turned out to be
  real twice over.

  MEASURED, and the answer is an ERROR BAR, not a discrepancy. The published 2x2
  (`notes/scoping_2026-09-01_ais_identifiability.md`) quotes L21 0.9455, L22 0.9434,
  L23 1.0865, L23b 1.0850 as "pooled posterior median". Recomputed over all 4M post-burn
  draws, with a batch-means se on each:

      published   L21 0.9455   L22 0.9434   L23 1.0865   L23b 1.0850
      pooled 4M   L21 0.9438   L22 0.9465   L23 1.0824   L23b 1.0896
        batch se      0.0018       0.0021       0.0037       0.0029
       gap in se        -0.9         +1.5         -1.1         +1.6

  ⚠ Every published cell is within 1.6 se of the recomputed one, so the two AGREE -- the
  published table was almost certainly read off a ~10k thinned pool, whose median carries
  exactly this much noise. What does NOT survive is the precision it was quoted to, and
  one cell's SIGN with it. Published L21->L22 was -0.0021, read as "the steric cap is not
  the cause"; recomputed it is +0.0026 ± 0.0027, i.e. 1.0 se from zero. Both readings are
  consistent with NO DIFFERENCE, and neither determines a sign. The conclusion is
  STRENGTHENED, not damaged -- but a four-decimal delta whose bar is bigger than itself
  should never have been printed as a measurement (`curvature_needs_an_error_bar`).

  ⚠ The i.i.d. formula would have hidden this. A bootstrap at n = 10,000 gives
  se(median) = 0.0012 (analytic 1.253*sd/sqrt(n) = 0.00125), 1.5-3x too small: these are
  autocorrelated MCMC draws in a sampler where 18 of L21's marginals fail R-hat. The se
  below is BATCH MEANS over blocks long enough to swamp the autocorrelation time.

  What IS resolved on this estimator: the L21->L23 span is +0.1386 ± 0.0041, about 34 se,
  and L23b (RNG-only replicate of L23) sits +0.0072 ± 0.0047 beyond L23. The span is real;
  the sampler noise is two orders below it.

  So this script does two things the 2x2 did not. It fixes ONE estimator -- pooled median
  over post-burn draws from every chain, burning the FIRST HALF exactly as
  `postprocess_mcmc_ext.jl:47` does -- and it carries a BATCH-MEANS standard error on that
  median, so no future delta gets quoted past its precision. The reference for a new tag is
  L21/L23 RECOMPUTED HERE, never the published constants.

  python python/diag_amp_by_vintage.py [L21 L22 L23 L23b L25 ...] [--no-cache]
Reads   outputs/mcmc/chain_<TAG>_seed*_n*.csv        (the amp column only, streamed)
        data/MimiBRICK/parameters_subsample_brick_mengel_<TAG>.csv   (cross-check)
Caches  outputs/mcmc/ampcol_<TAG>_seed<SEED>.npy     (~45 s/chain to build, instant after)
Writes  outputs/diag_amp_by_vintage.csv
"""
import glob
import os
import re
import subprocess
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCMC = os.path.join(REPO, "outputs", "mcmc")
OUT = os.path.join(REPO, "outputs", "diag_amp_by_vintage.csv")
PARAM = "ais_gmst_amp"

# The prior these refits were SAMPLED under. ⚠ NOT the driver default (0.180 since
# `165a860`): L21/L22/L23/L23b/L25 all pass --amp-sigma=0.10, so z must use 0.10 or every
# published z on this arc changes meaning.
AMP_MU, AMP_SIGMA = 1.09, 0.10

# The reference tags a new vintage is read against, RECOMPUTED here on this estimator.
REF_OLD_LAW, REF_NEW_LAW = "L21", "L23"

# Published 2x2 cells, kept only as a cross-check to be REPORTED, never as the reference.
PUBLISHED = {"L21": 0.9455, "L22": 0.9434, "L23": 1.0865, "L23b": 1.0850}
PUBLISHED_SRC = "notes/scoping_2026-09-01_ais_identifiability.md"

# Batch-means blocks per chain. Each block must be much longer than the parameter's
# autocorrelation time; amp is one of the CONVERGED marginals (it is absent from L21's
# 18-param not-converged list), so tau <= n/ESS_min = 1e6/400 = 2500, against blocks of
# 200,000. Fewer, longer blocks is the safe direction here.
BLOCKS_PER_CHAIN = 5

DEFAULT_TAGS = ["L21", "L22", "L23", "L23b", "L25"]


def chain_files(tag):
    return sorted(glob.glob(os.path.join(MCMC, f"chain_{tag}_seed*_n*.csv")))


def amp_column(path, use_cache=True):
    """Post-burn `ais_gmst_amp` from one chain, cached as .npy.

    awk rather than pandas: a chain is ~2.3 GB and one of 60 columns is wanted. The column
    INDEX comes from that file's OWN header, never assumed -- the chain layout has moved
    more than once on this arc.
    """
    seed = re.search(r"_seed(\d+)_", os.path.basename(path)).group(1)
    tag = re.search(r"chain_(.+?)_seed", os.path.basename(path)).group(1)
    cache = os.path.join(MCMC, f"ampcol_{tag}_seed{seed}.npy")
    if use_cache and os.path.exists(cache) and \
            os.path.getmtime(cache) >= os.path.getmtime(path):
        return np.load(cache)
    with open(path) as f:
        header = f.readline().rstrip("\n").split(",")
    if PARAM not in header:
        raise SystemExit(f"{os.path.basename(path)} has no {PARAM} column")
    col = header.index(PARAM) + 1
    txt = subprocess.run(["awk", "-F,", f"NR>1{{print ${col}}}", path],
                         capture_output=True, text=True, check=True).stdout
    v = np.fromstring(txt, sep="\n")
    v = v[len(v) // 2:]                 # burn the FIRST HALF (postprocess_mcmc_ext.jl:47)
    np.save(cache, v)
    return v


def median_se(chains, blocks=BLOCKS_PER_CHAIN):
    """Batch-means standard error of the POOLED median.

    Non-parametric and autocorrelation-aware: split each chain into equal blocks, take the
    median of each, and read the spread of those block medians. An i.i.d. formula
    (1.253*sd/sqrt(n)) would understate this by sqrt(n/ESS) and is not used.
    """
    meds = []
    for v in chains:
        k = len(v) // blocks
        meds += [float(np.median(v[i * k:(i + 1) * k])) for i in range(blocks)]
    meds = np.asarray(meds)
    return float(meds.std(ddof=1) / np.sqrt(len(meds))), len(meds)


def rhat(chains):
    """Split-free Gelman-Rubin across chains, on the raw parameter."""
    m, n = len(chains), min(len(c) for c in chains)
    x = np.vstack([c[:n] for c in chains])
    W = x.var(axis=1, ddof=1).mean()
    B = n * x.mean(axis=1).var(ddof=1)
    return float(np.sqrt(((n - 1) / n * W + B / n) / W)) if W > 0 else np.nan


def subsample_median(tag):
    p = os.path.join(REPO, "data/MimiBRICK", f"parameters_subsample_brick_mengel_{tag}.csv")
    if not os.path.exists(p):
        return np.nan, 0
    d = pd.read_csv(p, usecols=[PARAM])
    return float(np.median(d[PARAM])), len(d)


def main():
    args = sys.argv[1:]
    use_cache = "--no-cache" not in args
    tags = [a for a in args if not a.startswith("-")] or DEFAULT_TAGS
    print("=" * 100, flush=True)
    print(f"{PARAM} POSTERIOR CENTRE BY REFIT — pooled post-burn median, "
          f"batch-means se", flush=True)
    print("=" * 100, flush=True)
    print(f"\n  prior N({AMP_MU}, {AMP_SIGMA}) AS SAMPLED (--amp-sigma=0.10, not the driver "
          f"default 0.180)\n  burn: first half of each chain (postprocess_mcmc_ext.jl:47)"
          f"\n  se: {BLOCKS_PER_CHAIN} blocks/chain, spread of block medians\n", flush=True)
    print(f"{'tag':6s} {'ch':>3s} {'post-burn n':>12s} {'pooled med':>11s} {'se':>8s} "
          f"{'z':>7s} {'R-hat':>7s} {'10k subsam':>11s} {'published':>10s} "
          f"{'gap/se':>8s}", flush=True)
    rows, med = [], {}
    for tag in tags:
        fs = chain_files(tag)
        if not fs:
            print(f"{tag:6s} {'—':>3s}   no chain_{tag}_seed*_n*.csv on disk", flush=True)
            continue
        chains = [amp_column(f, use_cache) for f in fs]
        v = np.concatenate(chains)
        m = float(np.median(v))
        se, nb = median_se(chains)
        r = rhat(chains)
        sub, nsub = subsample_median(tag)
        pub = PUBLISHED.get(tag)
        gse = "" if pub is None or se == 0 else f"{(m - pub) / se:+.1f}"
        med[tag] = (m, se)
        print(f"{tag:6s} {len(fs):3d} {len(v):12,d} {m:11.4f} {se:8.5f} "
              f"{(m - AMP_MU) / AMP_SIGMA:+7.2f} {r:7.3f} {sub:11.4f} "
              f"{pub if pub is not None else float('nan'):10.4f} {gse:>8s}", flush=True)
        rows.append(dict(tag=tag, n_chains=len(fs), n_postburn=len(v), pooled_median=m,
                         median_se=se, n_blocks=nb, z_prior_sd=(m - AMP_MU) / AMP_SIGMA,
                         rhat=r, subsample_median=sub, n_subsample=nsub,
                         published=pub if pub is not None else np.nan))

    # --------------------------------------------------- the reading, on ONE estimator
    if REF_OLD_LAW in med and REF_NEW_LAW in med:
        (a, sa), (b, sb) = med[REF_OLD_LAW], med[REF_NEW_LAW]
        print(f"\n  REFERENCE, recomputed here (NOT the published constants):")
        print(f"    {REF_OLD_LAW} {a:.4f} ± {sa:.4f}   {REF_NEW_LAW} {b:.4f} ± {sb:.4f}"
              f"   span {b - a:+.4f} = {(b - a) / AMP_SIGMA:+.2f} prior sd")
        for tag, (m, se) in med.items():
            if tag in (REF_OLD_LAW, REF_NEW_LAW):
                continue
            f = (m - a) / (b - a)
            print(f"    {tag} {m:.4f} ± {se:.4f}  sits {f:5.2f} of the way from "
                  f"{REF_OLD_LAW} to {REF_NEW_LAW}  "
                  f"(d{REF_OLD_LAW} {m - a:+.4f} ± {np.hypot(se, sa):.4f}, "
                  f"d{REF_NEW_LAW} {m - b:+.4f} ± {np.hypot(se, sb):.4f})")
    else:
        print(f"\n  ⚠ {REF_OLD_LAW} and {REF_NEW_LAW} are the reference and BOTH must be in "
              f"the run. Without them a new tag has nothing like-for-like to sit against.")

    print(f"\n  ⚠ The `published` column ({PUBLISHED_SRC}) is a CROSS-CHECK, not the "
          f"reference. Every\n    cell agrees within 1.6 se, so it is the SAME estimate on "
          f"a noisier (~10k thinned)\n    pool -- but its L21->L22 delta of -0.0021 is "
          f"smaller than its own bar, and the\n    recomputed delta has the opposite sign "
          f"and is also consistent with zero. Read that\n    cell as NO DIFFERENCE, not as "
          f"a signed number. See this file's header.")
    if rows:
        pd.DataFrame(rows).to_csv(OUT, index=False)
        print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
