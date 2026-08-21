#!/bin/bash
# D2 STREAM ATTRIBUTION — which D2 discrepancy stream moves thermal_alpha?
#
# THE QUESTION (2026-08-16). L10 -> L11 moved thermal_alpha +1.31 L10 sd at a mix
# ratio of 19.7, and D1 alone accounts for only 19% of that (22635dd), so the
# other 81% is D2. But D2 has TWO streams and no chain in the repo separates
# them: D2chk, D2chk2 and D2chk3 all carry both d2_gsic_* and d2_steric_*.
#
#   H-A  the steric basis couples to alpha despite being orthogonalised against
#        S(t) itself -- orthogonality holds in the PLAIN inner product but the
#        likelihood metric is the AR(1)-correlated heteroskedastic precision,
#        where it does not, and d2_basis documents exactly that.
#   H-B  the gsic term moves alpha indirectly. NOTE this hypothesis is WEAKER
#        than the 2026-08-16 handoff first claimed: D1 removed the total from the
#        likelihood, so there is no term rewarding the component sum and hence no
#        obvious pathway by which a weakened glacier response pressures alpha.
#        The near-cancellation in the projected total (glaciers -1.2, steric +1.1
#        at 2100) may simply be two independent effects of similar size.
#
# DESIGN. Two arms, each the full L11 configuration with ONE D2 stream:
#   D2S  --d2-streams=steric   (55 params: 57 minus the two gsic coefficients)
#   D2G  --d2-streams=gsic     (55 params: 57 minus the two steric coefficients)
# 4 seeds each, matching 22635dd's D1 design, so the same mixing gate applies.
# Read alpha with python/diag_l10_vs_l11_projection.py's per_chain_medians.
#
# CHAIN LENGTH. 250k, as 22635dd used. Acceptance starts near ZERO and climbs as
# RAM adapts -- 0.000 at 3k, 0.004 at 5k, 0.217 by 30k on the D2Sprobe run. Do
# NOT read a short-run acceptance as a broken proposal; it is the adaptation
# warming up from a name-mapped covariance. No separate tuning run is needed.
#
# COVARIANCE, and this is load-bearing. These arms are 55-param, so they CANNOT
# use adapted_cov_L11tune3 positionally. L10_NAMES and the L11 layout are BOTH 57
# long, so the old size-based dispatch silently read the L11 covariance under
# L10's names and produced a chain that accepted EXACTLY 0 of 2000 proposals.
# Fixed 2026-08-16 by dispatching on the file's VINTAGE (L11_VINTAGE_ADCOV).
# Verify the launch banner says "as L11 layout" and names the dropped pair.
#
# Threads: ONE per chain (see run_l11_production.sh). 8 chains on 10 cores.
set -euo pipefail
cd "$(dirname "$0")/.."

N_ITER=250000
SEEDS="2026 2027 2028 2029"
ADCOV=outputs/mcmc/adapted_cov_L11tune3_seed2026.csv
STARTS=outputs/mcmc/overdispersed_starts.csv

[[ -f "$ADCOV" ]] || { echo "MISSING $ADCOV"; exit 1; }
[[ -f "$STARTS" ]] || { echo "MISSING $STARTS"; exit 1; }

export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export JULIA_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1

for ARM in steric gsic; do
  case $ARM in steric) TAG=D2S;; gsic) TAG=D2G;; esac
  for S in $SEEDS; do
    echo "launching $TAG seed $S (--d2-streams=$ARM, $N_ITER iter)"
    julia --project=julia_v2 julia/calibrate_mcmc_ext.jl "$N_ITER" "$S" \
      --overdisperse --d2-streams="$ARM" --tag="$TAG" --adcov="$ADCOV" \
      > "outputs/mcmc/log_${TAG}_seed${S}.txt" 2>&1 &
  done
done

wait
echo
echo "=== acceptance (must be ~0.2, not ~0 -- a ~0 here means the covariance dispatch regressed) ==="
grep -H "acceptance =" outputs/mcmc/log_D2{S,G}_seed*.txt
echo
echo "=== covariance layout actually used ==="
grep -H "seeding proposal" outputs/mcmc/log_D2{S,G}_seed*.txt
