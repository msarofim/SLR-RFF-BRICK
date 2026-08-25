#!/bin/bash
## L16 production: 4 RAM chains (seeds 2026-2029). THE SINGLE-CHANGE amp-sigma ARM.
##
## WHAT CHANGED vs L15 — EXACTLY ONE THING, by decision (Marcus 2026-08-25):
##   A6 amp prior sigma 0.10 -> 0.180. The CENTRE STAYS AT 1.09. Bounds follow the
##   file's own mu+-3sigma rule, [0.79, 1.39] -> [0.55, 1.63].
##
## WHY. L15 re-centred amp on two CMIP6 secant ensembles and the AIS hindcast broke.
## The proposed repair -- freeing the pinned DAIS anchor -- was REFUTED before it was
## built (commit 410f8fe, notes/handoff_2026-08-25e_anchor_refuted.md): amp is a SLOPE
## on GMST and the anchor is a LEVEL, so a translation cannot cancel the 0.208 K tilt
## the re-centring imposes across the calibration window, and the likelihood's own
## preferred anchor shift is -0.001 K rather than the predicted -0.077.
##
## What that work DID establish is that the historical record HAS an opinion about amp:
## moving L14's draws to amp 1.09 costs -4.81 log units (median, ~3.1 sigma on one
## parameter). sigma = 0.10 is what stops the posterior from expressing it. handoff -25d
## section 2 records that 0.10 was held deliberately so L15's delta stayed attributable;
## that reason has expired now that the delta IS attributed. 0.180 is the MEASURED
## between-model sd of the same two ensembles the 1.09 centre came from (34-model SSP
## secant sd 0.180; 41-model DECK 1pctCO2 range 1.087-1.153).
##
## ⚠ EVERYTHING ELSE IS L15's, DELIBERATELY. Same targets (LWS GRACE extension,
## trend-extended dang_closure_sig) and the SAME pooled proposal, adapted_cov_L15pool_
## seed2026.csv -- NOT re-pooled from the L15 chains, which would be a second change.
## L15's lesson (its section 3e) is that a bundled arm cannot be attributed.
##
## ⚠ FLAGGED, NOT FIXED: the amp prior widens 1.8x while its proposal block does not.
## The RAM sampler adapts, so this is a burn-in cost rather than a bias, but if the amp
## acceptance or its adapted scale looks pathological, re-pool BEFORE reading the result.
##
## ⚠ BLAS IS PINNED (pin_blas_threads): 4.8x on this M4, ETA 11h naked vs ~2h17m pinned
## for 4x2M. L15 took 4h20m with the same pinning and the cause was never established --
## expect somewhere in that range, and do not read a slow run as a hung one.
##
##   bash run_mcmc_L16.sh [n_iter]        # default 2000000, the L14/L15 production length
set -e
cd "$(dirname "$0")"
NITER="${1:-2000000}"
TAG=L16
ADCOV=adapted_cov_L15pool_seed2026.csv
AMP_SIGMA=0.180
mkdir -p outputs/mcmc
echo "L16: 4 chains x $NITER iter (seeds 2026-2029), amp ~ N(1.09, $AMP_SIGMA), adcov=$ADCOV, BLAS pinned"
for SEED in 2026 2027 2028 2029; do
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
    julia --project=julia_v2 --threads=1 julia/calibrate_mcmc_ext.jl "$NITER" "$SEED" \
        --tag=$TAG --gis-ordered --gis-basins2 --adcov=$ADCOV --amp-sigma=$AMP_SIGMA \
        > "outputs/mcmc/log_${TAG}_seed${SEED}.txt" 2>&1 &
done
wait
echo "L16 chains done -> outputs/mcmc/chain_${TAG}_seed*.csv"
echo "NEXT: julia --project=julia_v2 julia/postprocess_mcmc_ext.jl --tag=$TAG --accept-slr"
