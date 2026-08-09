#!/bin/bash
# extC production: 4 x 2M overdispersed chains (Marcus green-light 2026-08-09).
# PRECONDITIONS (two-stage launch): the extC1 tuning chain has been postprocessed
# (adapted_cov_extC1*.csv exists) and build_overdispersed_starts_extc.py has
# rebuilt outputs/mcmc/overdispersed_starts.csv with the 52-column extC header.
# --amp-mu=1.08 --amp-sigma=0.15 is MANDATORY (canonical A6 prior; the file
# default is the stale pre-A6 0.95/0.10 — see handoff_2026-08-09_extc_ready_to_launch.md).
set -euo pipefail
cd "$(dirname "$0")/.."
N_ITER=2000000
export OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2   # 4 chains x 2 threads
for SEED in 2026 2027 2028 2029; do
  echo "launching extC seed $SEED: $N_ITER iterations"
  julia --project=julia_v2 julia/calibrate_mcmc_ext.jl $N_ITER $SEED \
      --tag=extC --amp-mu=1.08 --amp-sigma=0.15 --overdisperse \
      > outputs/mcmc/log_extC_seed${SEED}.txt 2>&1 &
done
wait
echo "extC production complete: outputs/mcmc/chain_extC_seed{2026..2029}_n${N_ITER}.csv"
