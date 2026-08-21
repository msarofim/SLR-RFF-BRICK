#!/bin/bash
# L11 production: 4 x 2M over-dispersed chains (Marcus green-light 2026-08-15).
#
# L11 = the 2026-08-14 change set, all five parts default-ON, so NO flags select
# them: D1 (total dropped), the GlaMBIE R19 rate term, the rung sigma tightened
# by d2(8)=2.847, D2 (delta(t) on gsic+steric), and the Greenland (ell, w)
# reparameterisation. The five restore flags (--keep-total --no-r19-rate
# --rung-sig-legacy --no-d2 --gis-native) are deliberately NOT passed.
#
# No --amp-mu/--amp-sigma: L10 was launched without them and the file defaults
# (0.95 / 0.10) are the canonical Ladrillo prior. The extC-era 1.08/0.15
# override belongs to the A6 study, not here — passing it would silently change
# the AIS amp prior relative to L10 and break the like-for-like comparison.
#
# PRECONDITIONS (two-stage launch; the script checks all three):
#   1. adapted_cov_L11tune3_seed2026.csv exists — the tuning covariance on the
#      SHIPPED D2 basis (construction 2). L11tune/L11tune2 were tuned on
#      superseded bases and are only fallbacks.
#   2. overdispersed_starts.csv has been rebuilt BY NAME from the L11tune3
#      posterior (julia/build_overdispersed_starts.jl), so it carries the four
#      d2_* and two gis_slow_* columns. The calibrator asserts by-name coverage
#      and will refuse a stale file — that assertion is the real gate.
#   3. ./run_ladrillo_tests.sh passes.
#
# Threads: ONE per chain. The M4 has 4 performance cores; four chains x 4 BLAS
# threads spent about half their CPU in OpenBLAS spin-wait. Pinning to 1 took
# L10 from an 11h ETA to 2h15m. The RAM sampler's per-iteration work is a 57x57
# Cholesky update, far below where threading pays.
set -euo pipefail
cd "$(dirname "$0")/.."

N_ITER=2000000
TAG=L11
SEEDS="2026 2027 2028 2029"

ADCOV=outputs/mcmc/adapted_cov_L11tune3_seed2026.csv
STARTS=outputs/mcmc/overdispersed_starts.csv

[[ -f "$ADCOV" ]] || { echo "MISSING $ADCOV — run the L11tune3 tuning run first"; exit 1; }
[[ -f "$STARTS" ]] || { echo "MISSING $STARTS"; exit 1; }
# The starts file must post-date the L11 parameter set. Cheap header check here;
# the calibrator's by-name assertion is the authoritative one.
head -1 "$STARTS" | tr ',' '\n' | grep -qx "d2_gsic_1" || {
  echo "$STARTS predates L11 (no d2_gsic_1 column) — rebuild it from the L11tune3 chain:"
  echo "  julia --project=julia_v2 julia/build_overdispersed_starts.jl outputs/mcmc/chain_L11tune3_seed2026_n1000000.csv"
  exit 1; }
head -1 "$STARTS" | tr ',' '\n' | grep -qx "gis_slow_ell" || {
  echo "$STARTS predates the Greenland (ell, w) reparam — rebuild it from the L11tune3 chain"; exit 1; }

# --adcov IS PASSED. Before 2026-08-21 it was not: the script defined $ADCOV,
# hard-failed if it was missing, and echoed it as "proposal seed", but the
# invocation omitted the flag, so the calibrator fell through to its PREFERENCE
# LIST instead. That was harmless HERE only by coincidence -- with GIS_AB on the
# list's first candidate IS adapted_cov_L11tune3_seed2026.csv, the same file the
# banner names -- so this change is behaviour-preserving and the archived chains
# still reproduce. What it removes is the TEMPLATE TRAP: copy this script for a
# new vintage, point $ADCOV at the new tune file, and without the flag the
# preference list silently hands the run an L11-layout covariance while the
# banner claims the new one. That is the exact failure --adcov was added for
# (the L13 reseed), and run_l13/run_l14_production.sh already pass it.
echo "L11 production: 4 x $N_ITER, seeds $SEEDS, tag=$TAG"
echo "  proposal seed: $ADCOV"
echo "  starts:        $STARTS"
for SEED in $SEEDS; do
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
    julia --project=julia_v2 --threads=1 julia/calibrate_mcmc_ext.jl "$N_ITER" "$SEED" \
      --tag=$TAG --overdisperse --adcov="$ADCOV" \
      > "outputs/mcmc/log_${TAG}_seed${SEED}.txt" 2>&1 &
done
wait
echo "L11 production complete: outputs/mcmc/chain_${TAG}_seed{2026..2029}_n${N_ITER}.csv"
echo "next: julia --project=julia_v2 julia/postprocess_mcmc_ext.jl --tag=$TAG --accept-slr"
