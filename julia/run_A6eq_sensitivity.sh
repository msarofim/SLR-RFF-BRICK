#!/usr/bin/env bash
# A6 SENSITIVITY run: identical to the phase-2 production run EXCEPT the GMST->AIS
# amplification is pinned at the old equilibrium value (1.19546) instead of the CMIP6-
# transient N(0.95,0.10) prior. Isolates A6's effect on the SLR headline (production had
# SLR@2100 ~down from 76 to ~40 cm in the tuning preview, mostly from A6).
#
# Prereqs (same as production): outputs/mcmc/overdispersed_starts.csv (39-param) and
# adapted_cov_ext.csv (39x39). Outputs infix "extA6eq" so chains do NOT collide with, or
# match the glob of, the production "chain_ext_seed*". RUN AFTER production finishes — the
# machine is swap-bound and 8 parallel 2M chains would thrash.
set -u
cd "$(dirname "$0")/.."
N_ITER=2000000
export OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2
for SEED in 2026 2027 2028 2029; do
  echo "launching A6eq seed $SEED: $N_ITER iterations (amp pinned at equilibrium)"
  julia --project=julia_v2 julia/calibrate_mcmc_ext.jl $N_ITER $SEED --overdisperse --amp-equilibrium \
      > outputs/mcmc/log_extA6eq_seed${SEED}.txt 2>&1 &
done
wait
echo "ALL 4 A6eq CHAINS DONE"
