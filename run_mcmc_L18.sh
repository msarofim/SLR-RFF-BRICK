#!/bin/bash
## L18 production: 4 RAM chains (seeds 2026-2029). THE SINGLE-CHANGE *START* ARM.
##
## WHAT CHANGED vs L16 — EXACTLY ONE THING:
##   the START. `--overdisperse` is added, so the four chains begin at four DISTINCT real
##   posterior draws (outputs/mcmc/overdispersed_starts.csv) instead of one common
##   MEDOID/MAP point. The amp prior is UNCHANGED at N(1.090, 0.180); the proposal is
##   UNCHANGED at adapted_cov_L15pool_seed2026.csv; targets, --gis-ordered, --gis-basins2,
##   and the 2M length are all L16's.
##
## WHY. Commit fa1a467 (2026-08-26) established that the champion-vs-challenger comparison
## has NEVER been like-for-like. Verified across all 16 chain logs via `logpost(θ0)`:
##   L14  FOUR DISTINCT real posterior draws:  224.32 / 228.36 / 225.60 / 223.78
##   L15  one common medoid/MAP point, -643.92, all four seeds
##   L16  one common medoid/MAP point, -644.51, all four seeds
##   L17  one common medoid/MAP point, -644.51, all four seeds
## L14 ran --overdisperse; L15/L16/L17 did not. Every challenger began ~866 log units BELOW
## the typical set and had to burn in from there. That uncontrolled difference sits alongside
## the amp prior in every arm run so far, so THE AMP QUESTION HAS NEVER BEEN TESTED ON EQUAL
## FOOTING (`like_for_like_forcing`). L18 is the arm that splits them:
##   L18 vs L16  = the START effect, prior held fixed.
##   L18 vs L14  = the AMP-PRIOR effect, start protocol matched.
##
## WHY IT MATTERS NOW. Commit 45b66cd measured what the T_on modes are worth downstream by
## CONDITIONING L16 on its MID band: 6.9% of the L16-vs-L14 gap, 0 of 9 verdicts changed. So
## the modes are real but small, and ~93% of the gap is amp-or-start. amp is unidentified
## (posterior sd / truncated-prior sd = 0.989, NO shrinkage) yet NOT downstream-inert — it
## moves AIS ssp245@2150 from 0.406x the literature median to 1.710x. Splitting amp from
## burn-in is therefore the load-bearing run, not a diagnostic nicety.
##
## ⚠ THE STARTS FILE IS L14's, REUSED AS-IS, BY DECISION. outputs/mcmc/overdispersed_starts.csv
## (Aug 20 11:21) is the file L14 itself ran on. Reusing it unrebuilt is what makes the amp
## comparison EXACTLY controlled: L18 and L14 then differ in the amp prior and the proposal
## seed and nothing else. Its four amp values are 1.0813 / 1.0945 / 0.8275 / 0.8829 — inside
## BOTH priors' bounds (L14's [0.700, 1.250] and this arm's [0.550, 1.630]), so no start is
## dragged to a bound by the prior change.
##
## ⚠⚠ WHAT THIS ARM CANNOT DO — `no_power_null`. build_overdispersed_starts.jl disperses along
## `ais_iceflow0` quantiles (0.02/0.35/0.65/0.98), the badly-mixing axis as understood
## 2026-07-20, BEFORE T_on multimodality was found (2026-08-26). All four starts sit in the MID
## T_on band (-17.837 / -17.673 / -17.952 / -17.810). So L18 is dispersed WITHIN the good mode
## and has power ONLY on the burn-in/start question. If it comes back 100% MID that is largely
## BY CONSTRUCTION and is NOT evidence that the LOW/HIGH modes are negligible. The arm that
## WOULD test that disperses along `ais_runoff_Ton` across LOW/MID/HIGH and is still not run
## (handoff -26b Priority 2).
##
## FALSIFIABLE PREDICTION, registered before the run:
##   L18's chains start in MID, so if the START was the confound the AIS `median_vs_lit`
##   cells should move most of the way to L14's (ssp245 @2100/@2150/@2300: L14 0.531 / 0.406
##   / 0.949 vs L16 0.865 / 1.710 / 1.974). If instead L18 reproduces the L16MID conditioned
##   column (0.815 / 1.601 / 1.908, i.e. only 15/8/6% of the gap closed), the start was NOT
##   doing the work and THE AMP PRIOR IS THE LEVER — which makes the remaining decision a
##   PROVENANCE call (Xie sliding-window trend ratio vs two corrected CMIP6 secant ensembles)
##   that the benchmark scores fit for and structurally cannot see.
##   Either resolution is informative. Record which branch fired BEFORE reading anything else.
##
## ⚠ FLAGGED, NOT FIXED (inherited from L16's header): the amp prior is 1.8x wider than the
## proposal block adapted under sigma=0.10. RAM adapts, so this is a burn-in cost not a bias —
## but it is now compounded, because the starts also predate the wider prior.
##
## ⚠ BLAS IS PINNED (`pin_blas_threads`): 4.8x on this M4. L14 took ~2h34m for 4x2M with
## --overdisperse; L16 ~3h20m and L17 ~3h55m from the MAP start. Expect 2.5-4 h. A slow run is
## not a hung one. Julia block-buffers redirected stdout — an EMPTY LOG IS NOT A FAILED RUN;
## `tr '\r' '\n'` before grepping, the logs are progress-bar CRs.
##
##   bash run_mcmc_L18.sh [n_iter]        # default 2000000, the L14/L15/L16/L17 length
set -e
cd "$(dirname "$0")"
NITER="${1:-2000000}"
TAG="${TAG:-L18}"
ADCOV=adapted_cov_L15pool_seed2026.csv
AMP_SIGMA=0.180
STARTS=outputs/mcmc/overdispersed_starts.csv
mkdir -p outputs/mcmc

# Cheap early guards that NAME the fix. The calibrator's by-name column assertion and its
# finite-logposterior assertion are authoritative; these two catch the failures it cannot see.
[[ -f "$STARTS" ]] || { echo "MISSING $STARTS — --overdisperse cannot run."; exit 1; }
# A column absent from pn0 is SILENTLY IGNORED, so an L13-vintage (3-basin) starts file passes
# the by-name guard and puts all four chains at a 3-basin posterior draw.
if head -1 "$STARTS" | tr ',' '\n' | grep -qx "gis_s_mid"; then
  echo "$STARTS carries 'gis_s_mid' — it came from a 3-BASIN (L13) chain and would be"
  echo "accepted SILENTLY. Rebuild it from an L14-vintage chain before running L18."; exit 1
fi
for col in gis_s_high ais_gmst_amp ais_runoff_Ton; do
  head -1 "$STARTS" | tr ',' '\n' | grep -qx "$col" || {
    echo "$STARTS is missing '$col' — it predates the current parameter set."; exit 1; }
done

echo "L18: 4 chains x $NITER iter (seeds 2026-2029), amp ~ N(1.09, $AMP_SIGMA), adcov=$ADCOV,"
echo "     OVERDISPERSED starts from $STARTS, BLAS pinned"
for SEED in 2026 2027 2028 2029; do
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
    julia --project=julia_v2 --threads=1 julia/calibrate_mcmc_ext.jl "$NITER" "$SEED" \
        --tag=$TAG --gis-ordered --gis-basins2 --overdisperse \
        --adcov=$ADCOV --amp-sigma=$AMP_SIGMA \
        > "outputs/mcmc/log_${TAG}_seed${SEED}.txt" 2>&1 &
done
wait
echo "L18 chains done -> outputs/mcmc/chain_${TAG}_seed*.csv"
echo "VERIFY THE ARM FIRST (both lines, every seed):"
echo "  tr '\\r' '\\n' < outputs/mcmc/log_${TAG}_seed2026.txt | grep -m1 'A6 prior'      # N(1.090, 0.180)"
echo "  tr '\\r' '\\n' < outputs/mcmc/log_${TAG}_seed2026.txt | grep -m1 'logpost'       # over-dispersed start, ~+224"
echo "NEXT: julia/diag_slr_convergence_by_chain_ladrillo.jl --tag=$TAG, then"
echo "      julia/postprocess_mcmc_ext.jl --tag=$TAG --accept-slr   (2-3 h, see handoff -26b §5)"
