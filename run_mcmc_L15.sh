#!/bin/bash
## L15 production: 4 RAM chains (seeds 2026-2029), the 2026-08-25 recalibration.
##
## WHAT CHANGED vs L14 -- all four are in commit 893bfaa:
##   1. A6 amp prior re-centred 0.95 -> 1.09 (sigma 0.10 unchanged); bounds mu+-3sigma.
##      THE ONLY CHANGE THAT MOVES A NUMBER.
##   2. LWS 2019-2023 = real GRACE/GRACE-FO instead of the hold-flat fiat.
##   3. dang_closure_sig trend-extended past the ensemble instead of held flat.
##   4. --adcov = the POOLED adapted covariance over the four L14 seeds.
##
## ⚠ BLAS IS PINNED. Julia defaults to 4 BLAS threads; four naked chains put 16 threads on
## 4 P-cores and roughly half of each process is OpenBLAS spin-wait. Measured 4.8x on this
## M4: ETA 11h naked vs 2h17m pinned for 4x2M (`pin_blas_threads`).
##
##   bash run_mcmc_L15.sh [n_iter]        # default 2000000, the L14 production length
set -e
cd "$(dirname "$0")"
NITER="${1:-2000000}"
TAG=L15
ADCOV=adapted_cov_L15pool_seed2026.csv
mkdir -p outputs/mcmc
echo "L15: 4 chains x $NITER iter (seeds 2026-2029), adcov=$ADCOV, BLAS pinned"
for SEED in 2026 2027 2028 2029; do
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
    julia --project=julia_v2 --threads=1 julia/calibrate_mcmc_ext.jl "$NITER" "$SEED" \
        --tag=$TAG --gis-ordered --gis-basins2 --adcov=$ADCOV \
        > "outputs/mcmc/log_${TAG}_seed${SEED}.txt" 2>&1 &
done
wait
echo "L15 chains done -> outputs/mcmc/chain_${TAG}_seed*.csv"
echo "NEXT: julia --project=julia_v2 julia/postprocess_mcmc_ext.jl --tag=$TAG --accept-slr"
