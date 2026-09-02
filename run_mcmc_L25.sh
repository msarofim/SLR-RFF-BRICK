#!/bin/bash
## L25 — RECONSTRUCTED 2026-09-02. L23's configuration with L21/L22's PROPOSAL COVARIANCE — the run that exonerated the covariance and exposed the dropped --amp-mu. Ran 2026-09-01 18:52.
##
## ⚠⚠ THIS SCRIPT DID NOT EXIST WHEN L25 RAN, AND THAT IS WHY IT EXISTS NOW. Three flags were
## dropped on the L23 line because no run script pinned them: `--gis-ordered --gis-basins2`
## (quarantined 20260831_l23_missing_gis_flags), `--adcov` (369755c), and `--amp-mu`
## (663c74e — it was the whole "glacier law moved Antarctica by 66 cm" story). A flag that is
## absent does not error; it silently selects a default, and the default is not the
## predecessor's value.
##
## ⚠ EVERY AXIS BELOW IS PINNED EXPLICITLY, INCLUDING ONES THE ORIGINAL RUN OMITTED.
## The original passed only: --tag --gis-ordered --gis-basins2 --overdisperse --amp-sigma=0.10 --adcov=adapted_cov_L14tune_seed2026.csv
## The pinned values are what its defaults RESOLVED TO at the time, reconstructed from
## evidence, not assumed:
##   * --adcov  : from the run's own outputs/mcmc/seed_diag_L25_seed*.txt
##   * --amp-mu : default has been 1.09 since 893bfaa; L21/L22 are the only arms that
##                override it (--amp-mu=0.95), and their banners prove the difference
##   * --amp-sigma : verified from the DATA — ais_gmst_amp is prior-dominated, so its
##                posterior sd reveals the prior sigma (measured: implied 0.10)
## Pinning means this script reproduces L25 whenever it is run. The original command would
## NOT, because the defaults have since moved.
##
## ⚠⚠ THE LANDMINE THIS PREVENTS: **L23 AND L24 HAVE THE SAME ORIGINAL COMMAND LINE AND
## DIFFERENT PRIORS.** L23 ran 2026-08-31 22:39 when the default AMP_SIGMA was 0.10; L24 ran
## 2026-09-01 13:02, after 165a860 moved it to 0.180 at 10:12 that morning. Same invocation,
## different model. Measured implied prior sd: L23 0.102, L24 0.178.
##
## ⚠ THIS PROMOTES NOTHING. champions.json is untouched; promotion is Marcus's call.
## ⚠ BLAS PINNED. ⚠ CHECK uptime AND READ THE ETA AT ~5 MIN (eta_in_days_is_not_a_slow_run).
##
##   bash run_mcmc_L25.sh [n_iter]        # default 2000000
set -e
cd "$(dirname "$0")"
NITER="${1:-2000000}"
TAG="${TAG:-L25}"
ADCOV=adapted_cov_L14tune_seed2026.csv
STARTS=outputs/mcmc/overdispersed_starts.csv
mkdir -p outputs/mcmc
[[ -f "$STARTS" ]] || { echo "MISSING $STARTS"; exit 1; }
[[ -f "outputs/mcmc/$ADCOV" ]] || { echo "MISSING outputs/mcmc/$ADCOV"; exit 1; }
echo "$TAG: 4 chains x $NITER (seeds 2026 2027 2028 2029) — amp ~ N(1.09, 0.10), adcov=$ADCOV"
for SEED in 2026 2027 2028 2029; do
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
    julia --project=julia_v2 --threads=1 julia/calibrate_mcmc_ext.jl "$NITER" "$SEED" \
        --tag=$TAG --gis-ordered --gis-basins2 --overdisperse \
        --adcov=$ADCOV --amp-mu=1.09 --amp-sigma=0.10 \
        > "outputs/mcmc/log_${TAG}_seed${SEED}.txt" 2>&1 &
done
wait
echo "=== ARM VERIFICATION — do not trust the run until this matches ==="
for SEED in 2026 2027 2028 2029; do
  echo "  seed$SEED: $(tr '\r' '\n' < outputs/mcmc/log_${TAG}_seed${SEED}.txt | grep -m1 'A6 prior')"
done
echo "  EXPECT: amp ~ N(1.09, 0.10).  If it differs, a default moved under you — STOP."
