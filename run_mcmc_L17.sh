#!/bin/bash
## L17 production: 4 RAM chains (seeds 2026-2029). THE SINGLE-CHANGE PROPOSAL ARM.
##
## WHAT CHANGED vs L16 — EXACTLY ONE THING:
##   the proposal seed. --adcov moves from adapted_cov_L15pool_seed2026.csv to
##   adapted_cov_L16MID.csv, the empirical covariance of L16's own post-burn-in draws
##   RESTRICTED TO THE MID T_on BAND. The amp prior is UNCHANGED at N(1.09, 0.180).
##
## WHY. L16 repaired L15's AIS hindcast, and the repair was NOT the amp median moving
## 1.090 -> 1.060 (commit dc77cdc). scope_ais_ton_band_hindcast.jl scored 2 arms x 3
## COMMON T_on bands and hindcast quality tracks the BAND, not the arm:
##   1950-1992 bias, target sd:  L15 LOW -0.323 | L16 LOW -0.328 | L16 MID -0.003
## L16's LOW-band draws carry amp 1.066, essentially its MID 1.054, and still score like
## L15. And L14 -- the champion -- sits at T_on -17.84 +- 0.09, 100% MID, the SAME mode
## as L16. L15 is the aberration (73.7% LOW, 25.0% HIGH, 1.3% MID).
##
## THE DEFECT L17 TARGETS. L16 leaves that mode for 13% of its draws, and those draws sit
## 5.5-6.2 log units below its MID band -- where they should carry ~0.4% weight, not 13%.
## That is SAMPLER WANDER, not honest uncertainty, and it is what drags L16's pooled
## hindcast off its MID band (1950-1992 rmse 0.0080 -> 0.0091 cm) and pushes its AIS
## projection cells out. postprocess_mcmc_ext.jl's own comment names the mechanism: a
## proposal pooled over a non-converged ensemble is inflated by the between-chain (here
## between-MODE) variance "in exactly the worst directions".
##
## ⚠ THE DEFLATION IS SURGICAL, AND THAT IS THE POINT. Diagonal sd, MID-local vs L16
## pooled: ais_runoff_Ton 0.526 -> 0.142 (ratio 0.271) and essentially NOTHING else moves
## (median ratio over all 58 params = 1.000; ais_gmst_amp 0.985, so amp exploration is
## NOT narrowed). Conditioning is 3.20e12 against the pooled L16's 3.10e12 and the
## L15pool file L16 actually ran on, 1.21e15 -- so this is the best-conditioned of the
## three, and it is positive definite.
##
## ⚠ NOT CHANGED, DELIBERATELY: the start point. theta0 is the MEDOID/MAP start
## (recalib_central_row.csv; T_on reconstructed as -h0/c at line 1564), identical to L14,
## L15 and L16. Moving it would be a second change. Note this is the MAP, NOT the prior
## centre -- an earlier draft of this header said prior centre and was wrong; the smoke
## run prints "start = MAP".
##
## ⚠ AND THE CALIBRATOR ITSELF WARNS: "start = MAP; common across seeds -> R-hat is
## ANTI-CONSERVATIVE". All four chains leave from ONE point. That is true of L14/L15/L16
## too, and it is load-bearing for the mode argument: four chains that start together and
## agree are weaker evidence of having covered the posterior than four dispersed ones.
## L14's T_on sd of 0.09 at R-hat 1.092 should be read with that in mind -- it is
## unverified coverage, not established identification. --overdisperse exists if this
## needs testing, but it is a SEPARATE arm.
##
## ⚠ WHAT THIS ARM CANNOT DO. A mode-local proposal makes it EASIER to stay in the mode.
## If L17 comes back tight in T_on, that is partly by construction, so it is NOT evidence
## that the other modes are negligible. The evidence for that is the log_post gap
## (5.5-6.2 units) measured on L16, which is independent of this proposal. Report both.
##
## FALSIFIABLE PREDICTION, registered before the run (notes/handoff_2026-08-26_L17.md):
##   the AIS hindcast should land on L16's MID band -- 1950-1992 bias ~ -0.00 target sd,
##   rmse ~ 0.008 cm against L14's 0.0067 -- and the AIS projection cells should move
##   partway back toward L14's. If instead it reproduces L16's POOLED numbers, the wander
##   is not proposal-driven and the mode structure is a deeper problem than a seed.
##
## ⚠ BLAS IS PINNED (pin_blas_threads). L16 took ~3h20m for 4x2M with this pinning.
##
##   bash run_mcmc_L17.sh [n_iter]        # default 2000000, the L14/L15/L16 length
set -e
cd "$(dirname "$0")"
NITER="${1:-2000000}"
TAG=L17
ADCOV=adapted_cov_L16MID.csv
AMP_SIGMA=0.180
mkdir -p outputs/mcmc
echo "L17: 4 chains x $NITER iter (seeds 2026-2029), amp ~ N(1.09, $AMP_SIGMA), adcov=$ADCOV, BLAS pinned"
for SEED in 2026 2027 2028 2029; do
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
    julia --project=julia_v2 --threads=1 julia/calibrate_mcmc_ext.jl "$NITER" "$SEED" \
        --tag=$TAG --gis-ordered --gis-basins2 --adcov=$ADCOV --amp-sigma=$AMP_SIGMA \
        > "outputs/mcmc/log_${TAG}_seed${SEED}.txt" 2>&1 &
done
wait
echo "L17 chains done -> outputs/mcmc/chain_${TAG}_seed*.csv"
echo "NEXT: julia/diag_slr_convergence_by_chain_ladrillo.jl --tag=L17, then"
echo "      julia/postprocess_mcmc_ext.jl --tag=L17 --accept-slr"
