#!/bin/bash
## Local EXTENDED-target MCMC: 4 RAM chains (seeds 2026-2029) + ext postprocess.
## Mirrors run_mcmc_local.sh but for calibrate_mcmc_ext.jl (post-2018-extended fit).
## Writes chain_ext_seed*.csv and (via postprocess_mcmc_ext.jl) a SEPARATE subsample
## parameters_subsample_brick_mengel_ext.csv -- the 2018-baseline outputs are untouched.
##   bash run_mcmc_ext_local.sh [n_iter]
set -e
cd "$(dirname "$0")"
NITER="${1:-100000}"
mkdir -p outputs/mcmc
rm -f outputs/mcmc/chain_ext_seed*.csv
echo "Launching 4 EXTENDED chains × $NITER iter (seeds 2026-2029)..."
for SEED in 2026 2027 2028 2029; do
    julia --project=julia_v2 julia/calibrate_mcmc_ext.jl "$NITER" "$SEED" \
        > "outputs/mcmc/log_ext_seed${SEED}.txt" 2>&1 &
done
wait
echo "Chains done. Postprocessing (R̂/ESS, subsample, A/B vs baseline)..."
julia --project=julia_v2 julia/postprocess_mcmc_ext.jl 10000 2>&1 | tee outputs/mcmc/postprocess_ext.txt
echo "EXT MCMC DONE -> data/MimiBRICK/parameters_subsample_brick_mengel_ext.csv"
