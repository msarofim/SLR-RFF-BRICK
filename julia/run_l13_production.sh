#!/bin/bash
# L13 production: 4 x 2M over-dispersed chains, matching the L12 configuration
# exactly (Marcus 2026-08-19).
#
# L13 = L12's change set PLUS the 3-basin Mouginot SECTOR Greenland and the
# per-sector SHARES likelihood term. The only flag that differs from
# run_l12_production.sh is --gis-basins. Everything else is inherited by NOT
# passing a restore flag: --gis-ordered (the channel wedge), D1 (total dropped),
# the GlaMBIE R19 rate term, the tightened rung sigma, D2, and the (ell, w)
# reparameterisation.
#
# WHAT CHANGED IN THE LAYOUT, and why the covariance must be re-tuned. L13 adds
# TWO sampled parameters (gis_s_mid, gis_s_high; south is PINNED at 1 because the
# common mode of the three rate scales is exactly degenerate with the shared shape
# rates — measured 0.0 over c in [0.25, 10]). NK goes 57 -> 59, so no existing
# covariance matches by size and the L12 rows are name-mapped with a fresh
# diagonal for the new pair. That start is poor, and it is why a SHORT run
# understates acceptance badly: a 3000-iteration smoke gave 0.017 while the same
# configuration reaches 0.319 by 40000. Do not judge the layout on a short run.
#
# THE FIRST L13 LINE (2026-08-19) WAS VOID — read this before re-running. The tuning
# run was seeded through `L11_NAMES`, a hardcoded row-order list for the nameless
# adapted-cov CSVs that had the four d2_* rows in the WRONG POSITION (appended after
# the AIS block instead of at rows 35-38, where FREE puts them). The name set matched,
# so the seeder logged "name-mapped 57 of 57 rows, dropped <nothing>" and handed live
# ais_c the variance of ais_slope: 8.005e-07 against a posterior that spans ~95. RAM's
# rank-one multiplicative update can never re-inflate a coordinate whose row of L is
# ~0, so ais_c was frozen for all 4x2M iterations while global acceptance sat at a
# healthy 0.245. Quarantined: outputs/quarantine/20260819_adcov_l11names_misorder/.
# SEED FROM THE L12 PRODUCTION COVARIANCE and let the geometry gate confirm it:
# the run refuses to start unless sqrt(diag(cov0))[ais_c] >= 0.05 (L12's is 1.282).
#
# WHY THE STARTS NEED NO EXTRA GATE: build_overdispersed_starts.jl picks REAL
# draws from the tuning chain's 2nd half. That chain is itself run with
# --gis-ordered --gis-basins, so every draw already satisfies the wedge AND
# carries the gis_s_* columns the calibrator asserts on by name.
#
# PRECONDITIONS (the script checks all of them):
#   1. adapted_cov_L13tune_seed2026.csv exists — tuned WITH the basins. An L12
#      covariance is the wrong SHAPE and is missing the new pair entirely.
#   2. overdispersed_starts.csv rebuilt from the L13tune chain (it CANNOT be
#      rebuilt earlier: no pre-L13 chain contains gis_s_mid / gis_s_high).
#   3. julia/test_greenland_3basin_nesting.jl and ./run_ladrillo_tests.sh pass.
#
# Threads: ONE per chain — four chains x 4 BLAS threads spend about half their
# CPU in OpenBLAS spin-wait; pinning to 1 took L10 from an 11h ETA to 2h15m.
set -euo pipefail
cd "$(dirname "$0")/.."

N_ITER=2000000
TAG=L13
SEEDS="2026 2027 2028 2029"

ADCOV=outputs/mcmc/adapted_cov_L13tune_seed2026.csv
STARTS=outputs/mcmc/overdispersed_starts.csv
TUNECHAIN=outputs/mcmc/chain_L13tune_seed2026_n1000000.csv

[[ -f "$ADCOV" ]] || { echo "MISSING $ADCOV — run the L13tune tuning run first:"; \
  echo "  julia --project=julia_v2 julia/calibrate_mcmc_ext.jl 1000000 2026 --tag=L13tune --gis-ordered --gis-basins --adcov=adapted_cov_L12_seed2026.csv"; exit 1; }
[[ -f "$STARTS" ]] || { echo "MISSING $STARTS"; exit 1; }

# The starts must carry the L13 columns. The calibrator's by-name assertion is
# authoritative; these are cheap early checks that name the actual fix.
for col in gis_slow_ell d2_gsic_1 gis_s_mid gis_s_high; do
  head -1 "$STARTS" | tr ',' '\n' | grep -qx "$col" || {
    echo "$STARTS is missing '$col' — rebuild it from the L13tune chain:"
    echo "  cp $STARTS ${STARTS}.pre_l13_bak"
    echo "  julia --project=julia_v2 julia/build_overdispersed_starts.jl $TUNECHAIN"
    exit 1; }
done
# PROVENANCE: starts built from a pre-L13 chain would put chains in the rejected
# region, where every MH ratio is NaN and acceptance is exactly 0.0.
[[ -f "$TUNECHAIN" ]] || { echo "MISSING $TUNECHAIN"; exit 1; }
[[ "$STARTS" -nt "$TUNECHAIN" ]] || {
  echo "$STARTS is OLDER than $TUNECHAIN — it was built from a different chain."
  echo "Rebuild it, or the chains start outside the wedge:"
  echo "  cp $STARTS ${STARTS}.pre_l13_bak"
  echo "  julia --project=julia_v2 julia/build_overdispersed_starts.jl $TUNECHAIN"
  exit 1; }

echo "L13 production: 4 x $N_ITER, seeds $SEEDS, tag=$TAG  (--gis-ordered --gis-basins)"
echo "  proposal seed: $ADCOV"
echo "  starts:        $STARTS"
echo "  EXPECT SLR@2100 = 45.53 cm TO MOVE — that is the point of the restructure."
for SEED in $SEEDS; do
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
    julia --project=julia_v2 --threads=1 julia/calibrate_mcmc_ext.jl "$N_ITER" "$SEED" \
      --tag=$TAG --gis-ordered --gis-basins --overdisperse \
      > "outputs/mcmc/log_${TAG}_seed${SEED}.txt" 2>&1 &
done
wait
echo "L13 production complete: outputs/mcmc/chain_${TAG}_seed{2026..2029}_n${N_ITER}.csv"
echo "next: julia --project=julia_v2 julia/postprocess_mcmc_ext.jl --tag=$TAG --accept-slr"
