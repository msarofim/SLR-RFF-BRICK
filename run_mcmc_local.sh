#!/bin/bash
## Local production MCMC: 4 RAM chains (different seeds) in parallel + postprocess.
## ~236 iter/s; 4 × 100k iter parallel ≈ 8 min + postprocess. The compute is small
## enough to run locally; the Torch SLURM (run_mcmc_torch.sbatch) is the alternative.
##   bash run_mcmc_local.sh [n_iter]
set -e
cd "$(dirname "$0")"
NITER="${1:-100000}"
mkdir -p outputs/mcmc
echo "Launching 4 chains × $NITER iter (seeds 2026-2029)..."
for SEED in 2026 2027 2028 2029; do
    julia --project=julia_v2 julia/calibrate_mcmc.jl "$NITER" "$SEED" \
        > "outputs/mcmc/log_seed${SEED}.txt" 2>&1 &
done
wait
echo "Chains done. Postprocessing (R̂/ESS, subsample)..."
julia --project=julia_v2 julia/postprocess_mcmc.jl 10000 2>&1 | tee outputs/mcmc/postprocess.txt
echo "MCMC DONE -> data/MimiBRICK/parameters_subsample_brick_mengel.csv"
