#!/usr/bin/env python3
"""
build_pooled_adapted_cov.py — POOL THE FOUR SEEDS' ADAPTED PROPOSAL COVARIANCES INTO ONE.

`acceptance_rate_certifies_nothing` (2026-08-24): the four L14 RAM chains all adapted to an
acceptance rate of 0.234 while their adapted proposal SHAPES differ by **347x**. Acceptance
measures the global SCALE; mixing needs the SHAPE. `ais_iceflow0` R-hat 2.244 is a STIFF
direction (`ais_stiff_not_flat`), and the lever for a stiff direction is proposal scaling --
not reparameterisation. Seeding every chain of the next run from ONE seed's adapted shape is
what produced the disagreement; seeding them all from the POOLED shape is the fix.

⚠ POOLED ON THE CORRELATION, NOT ON THE RAW COVARIANCE. The same memory records why: the raw
covariance has condition number 1.9e16 and its leading eigenvector loads 1.000 on the
smallest-scale parameter at BOTH ends -- averaging raw covariances would be dominated by
whichever seed happened to have the largest scale on the largest-scale parameter. Each seed's
matrix is split into (sd, correlation), the CORRELATIONS are averaged, the SDs are averaged in
LOG space (they are scale parameters and differ multiplicatively), and the pair is
reconstituted.

⚠ AND THE RESULT IS GATED, not assumed: symmetry, finiteness, positive-definiteness via a
Cholesky, identical column names and order across all inputs, and the pooled condition number
reported beside the inputs' so a pooled matrix that is WORSE conditioned than its members
cannot ship silently.

    source ~/climate-env/bin/activate
    python python/build_pooled_adapted_cov.py --tag=L14 [--out=L15pool]
Writes outputs/mcmc/adapted_cov_<OUT>_seed2026.csv
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--tag=")), "L14")
OUTTAG = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--out=")), "L15pool")
MCMC = os.path.join(REPO, "outputs", "mcmc")
OUT = os.path.join(MCMC, f"adapted_cov_{OUTTAG}_seed2026.csv")
# The floor on a pooled sd, as a fraction of the median sd for that parameter across seeds.
# Guards against one seed collapsing a direction to ~0 and the log-mean following it down.
SD_FLOOR_FRAC = 0.05


def main():
    files = sorted(glob.glob(os.path.join(MCMC, f"adapted_cov_{TAG}_seed*.csv")))
    if len(files) < 2:
        raise SystemExit(f"need >=2 seed covariances matching adapted_cov_{TAG}_seed*.csv, "
                         f"found {len(files)}")
    mats, names = [], None
    print(f"pooling {len(files)} adapted covariances for tag {TAG}\n")
    print(f"{'file':44s} {'n':>4s} {'cond':>11s} {'sd range':>22s}")
    for f in files:
        d = pd.read_csv(f)
        if names is None:
            names = list(d.columns)
        elif list(d.columns) != names:
            raise SystemExit(f"{os.path.basename(f)}: column names/order differ from "
                             f"{os.path.basename(files[0])} -- pooling by position would "
                             f"give a parameter its neighbour's scale (`nameless_matrix_order`)")
        M = d.to_numpy(float)
        if M.shape[0] != M.shape[1]:
            raise SystemExit(f"{os.path.basename(f)}: not square {M.shape}")
        if not np.allclose(M, M.T, rtol=1e-8, atol=1e-300):
            raise SystemExit(f"{os.path.basename(f)}: not symmetric")
        sd = np.sqrt(np.diag(M))
        print(f"{os.path.basename(f):44s} {M.shape[0]:4d} {np.linalg.cond(M):11.3e} "
              f"{sd.min():10.3e}-{sd.max():.3e}")
        mats.append(M)

    sds = np.array([np.sqrt(np.diag(M)) for M in mats])
    cors = []
    for M, sd in zip(mats, sds):
        s = np.where(sd > 0, sd, 1.0)
        cors.append(M / np.outer(s, s))
    cor = np.mean(cors, axis=0)
    np.fill_diagonal(cor, 1.0)
    cor = 0.5 * (cor + cor.T)
    # log-mean of the sds: they are SCALE parameters and disagree multiplicatively
    med = np.median(sds, axis=0)
    sdp = np.exp(np.mean(np.log(np.maximum(sds, SD_FLOOR_FRAC * med[None, :])), axis=0))
    P = cor * np.outer(sdp, sdp)
    P = 0.5 * (P + P.T)

    # ⚠ THE PER-PARAMETER sd RATIO IS THE WRONG STATISTIC FOR "SHAPE" AND UNDERSTATES IT
    # ~1000x. Marginal sds disagree by at most ~2.4x across these seeds; the DISAGREEMENT
    # THE MEMORY RECORDS (347x) is the generalized-eigenvalue spread of one seed's matrix
    # against another's, i.e. the worst direction. Both are printed, because a reader who
    # sees only the marginals would conclude pooling is unnecessary.
    # ⚠ AND STANDARDIZING MAKES IT LARGER, NOT SMALLER (2711x on the same pair). That
    # qualifies `acceptance_rate_certifies_nothing`'s "standardize first" -- which is advice
    # about not misreading the leading EIGENVECTOR, not a claim that the raw spread is
    # inflated. The correlation structures genuinely disagree by 500-3400x.
    def _gev(A, B):
        w = np.linalg.eigvals(np.linalg.solve(B + 1e-30 * np.eye(len(B)), A)).real
        w = w[w > 1e-12]
        return w.max() / w.min() if len(w) else np.nan
    pairs = [(i, j) for i in range(len(mats)) for j in range(i + 1, len(mats))]
    raws = [_gev(mats[i], mats[j]) for i, j in pairs]
    stds = [_gev(cors[i], cors[j]) for i, j in pairs]
    print(f"\n  SHAPE disagreement between seed pairs (generalized-eigenvalue spread):")
    print(f"    raw          {min(raws):8.1f} - {max(raws):.1f}x")
    print(f"    standardized {min(stds):8.1f} - {max(stds):.1f}x   <= LARGER, not smaller")
    print(f"    => seeding every chain from ONE seed's shape is an arbitrary choice among")
    print(f"       matrices that disagree by up to {max(stds):.0f}x in their worst direction.")

    print(f"\n  shape disagreement across seeds, per parameter (max sd / min sd):")
    ratio = sds.max(axis=0) / np.maximum(sds.min(axis=0), 1e-300)
    worst = np.argsort(ratio)[::-1][:5]
    for i in worst:
        print(f"    {names[i]:28s} {ratio[i]:10.1f}x")
    print(f"    (median over all {len(names)} parameters: {np.median(ratio):.1f}x)")

    # ---- gates
    ok = True
    if not np.all(np.isfinite(P)):
        print("  GATE FAIL: pooled matrix has non-finite entries"); ok = False
    try:
        np.linalg.cholesky(P)
        print(f"\n  GATE positive-definite: PASS (Cholesky succeeded)")
    except np.linalg.LinAlgError:
        print(f"\n  GATE positive-definite: FAIL"); ok = False
    cP, cIn = np.linalg.cond(P), [np.linalg.cond(M) for M in mats]
    print(f"  GATE conditioning: pooled {cP:.3e} vs inputs {min(cIn):.3e}-{max(cIn):.3e} "
          f"=> {'PASS' if cP <= 10 * max(cIn) else 'FAIL (worse than every input)'}")
    ok &= cP <= 10 * max(cIn)
    if not ok:
        raise SystemExit("gates failed -- not written")
    pd.DataFrame(P, columns=names).to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")
    print(f"  use with:  --adcov=adapted_cov_{OUTTAG}_seed2026.csv")


if __name__ == "__main__":
    main()
