#!/bin/bash
## L27 PRODUCTION (2026-09-20, Marcus "Do the recommendations"): L26 + the A/C/D reduction of
## notes/note_2026-09-20_ais_reduction_and_L26_vs_L24.md — 50 parameters.
##   --cut-fastdyn  lambda/T_crit not sampled (likelihood exactly flat; paleo medians held; projections attach JOINT paleo draws)
##   --fix-gamma    gamma at its paleo median (flat, no projection leverage)
##   --no-ledger    the two glacier set-asides integrated out under their priors
## Starts: overdispersed_starts_L27.csv = L26 seed2026 2nd-half draws at ais_iceflow0 quantiles (the L27tune chain from the
## MAP start was still burning its Greenland noise init sd=1.0 down at 500k — start from the converged mode, not the MAP).
## Proposal seed: L26's postprocess covariance, named header (adapted_cov_L26_named.csv).
## The rest of the L26 description follows.
##   --paleo-priors      eight DAIS parameters on the DAISfastdyn paleo marginals; thermal_alpha Uniform(0.05, 0.3)
##                       (L24's outputs/param_priors.csv was BRICK 2.0's POSTERIOR mean/sd truncated at +-2 sd)
##   --no-delta          the M15 early-segment target ramp is not sampled (the raw target is scored)
##   --no-d2-gsic        the two glacier discrepancy coefficients are not sampled
##   --obs-corr-len=100  the published bands enter as a correlated error, e-folding 100 yr. L26d sampled L on
##                       [5, 100] and it railed at 100 (99.0 [95.6, 99.9]); a cumulative-reconstruction band IS a
##                       level-like error, so the bound the data push to is the physically sensible one. Fixed,
##                       not sampled (one parameter fewer); L = 20 / 50 are the single-chain sensitivities (L26a/c).
##   --toff-lo=-4        the glacier equilibrium-offset bound (L24's -3 clipped 23 % of SLOWG's posterior)
##   --precip-reparam    u = log P0 + kappa * Tbar sampled in the precip slot (the r = +0.96 ridge)
## 55 parameters (L24: 58). Starts: outputs/mcmc/overdispersed_starts_L26.csv (L26d 2nd-half draws at
## ais_iceflow0 quantiles 0.02/0.35/0.65/0.98); proposal seed: L26d's adapted covariance (named header).
set -e
cd "$(dirname "$0")"
NITER="${1:-2000000}"
TAG="${TAG:-L27}"
ADCOV=adapted_cov_L26_named.csv
STARTS=outputs/mcmc/overdispersed_starts_L27.csv
FLAGS="--gis-ordered --gis-basins2 --amp-mu=1.09 --amp-sigma=0.180 --paleo-priors --no-delta --no-d2-gsic --obs-corr-len=100 --toff-lo=-4 --precip-reparam --cut-fastdyn --fix-gamma --no-ledger"
[[ -f "$STARTS" ]] || { echo "MISSING $STARTS"; exit 1; }
[[ -f "outputs/mcmc/$ADCOV" ]] || { echo "MISSING outputs/mcmc/$ADCOV"; exit 1; }
echo "$TAG: 4 chains x $NITER (seeds 2026 2027 2028 2029) — $FLAGS ; adcov=$ADCOV starts=$STARTS ; commit $(git rev-parse --short HEAD)"
for SEED in 2026 2027 2028 2029; do
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
    julia --project=julia_v2 --threads=1 julia/calibrate_mcmc_ext.jl "$NITER" "$SEED" \
        --tag=$TAG --overdisperse --starts=$STARTS --adcov=$ADCOV $FLAGS \
        > "outputs/mcmc/log_${TAG}_seed${SEED}.txt" 2>&1 &
done
wait
echo "=== ARM VERIFICATION — do not trust the run until this matches ==="
for SEED in 2026 2027 2028 2029; do
  echo "  seed$SEED: $(tr '\r' '\n' < outputs/mcmc/log_${TAG}_seed${SEED}.txt | grep -a -m1 'L26 structure flags')"
  echo "           $(tr '\r' '\n' < outputs/mcmc/log_${TAG}_seed${SEED}.txt | grep -a -m1 'MCMC:')"
done
echo "  EXPECT: paleo-priors=true no-delta=true no-d2-gsic=true obs-corr-len=100.0 precip-reparam=true + cut-fastdyn fix-gamma no-ledger; 50 free params."
