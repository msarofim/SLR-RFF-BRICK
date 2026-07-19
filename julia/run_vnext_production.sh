#!/usr/bin/env bash
# v-next BRICK-Mengel production: 4 chains, N_ITER iterations each (see N_ITER below),
# SSP2-4.5 harmonized forcing. Seeded from the adapted 35x35 covariance.
set -u
cd "$(dirname "$0")/.."
N_ITER=2000000
export OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2   # 4 chains x 2 threads on 10 cores
for SEED in 2026 2027 2028 2029; do
  echo "launching seed $SEED: $N_ITER iterations"
  julia --project=julia_v2 julia/calibrate_mcmc_ext.jl $N_ITER $SEED --overdisperse \
      > outputs/mcmc/log_ext_seed${SEED}.txt 2>&1 &
done
wait
echo "ALL 4 CHAINS DONE"
