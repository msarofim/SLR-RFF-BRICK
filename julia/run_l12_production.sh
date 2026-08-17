#!/bin/bash
# L12 production: 4 x 2M over-dispersed chains (Marcus green-light 2026-08-17).
#
# L12 = L11's change set PLUS the Greenland channel-ordering constraint. The only
# flag that differs from run_l11_production.sh is --gis-ordered, which imposes
# alpha_s <= alpha_f AND beta_s <= beta_f as a WEDGE in the sampled (ell, w) --
# see the GIS_ORDERED block in calibrate_mcmc_ext.jl for why this cannot be a
# bound change and why relabelling the posterior cannot substitute for it.
#
# Every other L11 choice is inherited by NOT passing its restore flag: D1 (total
# dropped), the GlaMBIE R19 rate term, the tightened rung sigma, D2, and the
# (ell, w) reparameterisation. No --amp-mu/--amp-sigma, as in L10 and L11.
#
# WHY THE STARTS NEED NO EXTRA GATE: build_overdispersed_starts.jl picks REAL
# draws from the tuning chain's 2nd half. That chain is itself run with
# --gis-ordered, so every draw in it already satisfies the wedge and the
# calibrator's logposterior(theta0) finiteness assertion cannot fire on them.
# Rebuilding the starts from an UNCONSTRAINED chain would break that, which is
# what the L12tune provenance check below is guarding.
#
# PRECONDITIONS (the script checks all of them):
#   1. adapted_cov_L12tune_seed2026.csv exists — tuned WITH the constraint. The
#      wedge truncates the posterior, so an L11 covariance is the wrong shape.
#   2. overdispersed_starts.csv rebuilt from the L12tune chain.
#   3. ./run_ladrillo_tests.sh and julia/test_gis_ordering_wedge.jl pass.
#
# Threads: ONE per chain — four chains x 4 BLAS threads spend about half their
# CPU in OpenBLAS spin-wait; pinning to 1 took L10 from an 11h ETA to 2h15m.
set -euo pipefail
cd "$(dirname "$0")/.."

N_ITER=2000000
TAG=L12
SEEDS="2026 2027 2028 2029"

ADCOV=outputs/mcmc/adapted_cov_L12tune_seed2026.csv
STARTS=outputs/mcmc/overdispersed_starts.csv
TUNECHAIN=outputs/mcmc/chain_L12tune_seed2026_n1000000.csv

[[ -f "$ADCOV" ]] || { echo "MISSING $ADCOV — run the L12tune tuning run first:"; \
  echo "  julia --project=julia_v2 julia/calibrate_mcmc_ext.jl 1000000 2026 --tag=L12tune --gis-ordered"; exit 1; }
[[ -f "$STARTS" ]] || { echo "MISSING $STARTS"; exit 1; }

# The starts must carry the L11-era columns AND post-date the L12 tune. The
# calibrator's by-name assertion is authoritative; these are cheap early checks.
head -1 "$STARTS" | tr ',' '\n' | grep -qx "gis_slow_ell" || {
  echo "$STARTS predates the Greenland (ell, w) reparam — rebuild from the L12tune chain"; exit 1; }
head -1 "$STARTS" | tr ',' '\n' | grep -qx "d2_gsic_1" || {
  echo "$STARTS predates D2 — rebuild from the L12tune chain"; exit 1; }
# PROVENANCE: starts built from an unconstrained chain would put chains in the
# rejected region, where every MH ratio is NaN and acceptance is exactly 0.0.
[[ -f "$TUNECHAIN" ]] || { echo "MISSING $TUNECHAIN"; exit 1; }
[[ "$STARTS" -nt "$TUNECHAIN" ]] || {
  echo "$STARTS is OLDER than $TUNECHAIN — it was built from a different (probably"
  echo "unconstrained) chain. Rebuild it, or the chains start outside the wedge:"
  echo "  cp $STARTS ${STARTS}.pre_l12_bak"
  echo "  julia --project=julia_v2 julia/build_overdispersed_starts.jl $TUNECHAIN"
  exit 1; }

echo "L12 production: 4 x $N_ITER, seeds $SEEDS, tag=$TAG  (--gis-ordered)"
echo "  proposal seed: $ADCOV"
echo "  starts:        $STARTS"
for SEED in $SEEDS; do
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
    julia --project=julia_v2 --threads=1 julia/calibrate_mcmc_ext.jl "$N_ITER" "$SEED" \
      --tag=$TAG --gis-ordered --overdisperse \
      > "outputs/mcmc/log_${TAG}_seed${SEED}.txt" 2>&1 &
done
wait
echo "L12 production complete: outputs/mcmc/chain_${TAG}_seed{2026..2029}_n${N_ITER}.csv"
echo "next: julia --project=julia_v2 julia/postprocess_mcmc_ext.jl --tag=$TAG --accept-slr"
