#!/bin/bash
## gate_calibrator_identity.sh — does calibrate_mcmc_ext.jl still define the L24 objective?
##
## Runs the L24 configuration (run_mcmc_L24.sh's flags) for 300 iterations from seed 2026 and
## demands BYTE-IDENTITY of the chain and the adapted covariance against the frozen reference in
## benchmark/reference/calibrator_300iter/ (written 2026-09-16 from the pre-cleanup calibrator,
## kept verbatim as benchmark/reference/calibrator_300iter/calibrate_mcmc_ext_precleanup_2026-09-16.jl). Any edit to the objective, the
## priors, the proposal seed, the start row or the RNG stream changes the chain; a pure code
## cleanup does not. MUTATION-TESTED at creation: --amp-sigma=0.181 → chain differs (as it must).
##
##   bash scripts/gate_calibrator_identity.sh            # ~40 s; exit 0 = identical
##
## RE-FROZEN AGAIN 2026-09-21 (afternoon) on the IMBIE-2026 AIS target (logpost(θ0) 219.64 -> 148.36; the Frederikse-AIS
## reference is archived in benchmark/reference/calibrator_300iter_ais_frederikse_20260921/ and reproduces with the
## quarantined target swapped in). Earlier the same day:
## RE-FROZEN 2026-09-21 under LWS_MODE = :central (the 09-18 land-water ruling enters the objective through
## the Antarctic sea-level feedback, ~1e-4 log-units, enough to flip accept/reject inside 300 iterations); the
## 09-16 :seeded reference is archived beside it and is reproduced byte-for-byte by the current calibrator with
## LWS_MODE = :seeded (proof run 09-21). See benchmark/reference/calibrator_300iter/README.md. ⚠ The gate had
## been RED since 09-18 without anyone running it: run it after EVERY calibrator or brick_mengel.jl edit.
set -uo pipefail
cd "$(dirname "$0")/.."
REF=benchmark/reference/calibrator_300iter
TAG=gate300
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
julia --project=julia_v2 --threads=1 julia/calibrate_mcmc_ext.jl 300 2026 \
    --tag=$TAG --gis-ordered --gis-basins2 --overdisperse \
    --adcov=adapted_cov_L11tune3_seed2026_named.csv --amp-mu=1.09 --amp-sigma=0.180 \
    > outputs/mcmc/log_${TAG}.txt 2>&1 || { echo "[GATE] calibrator FAILED to run; see outputs/mcmc/log_${TAG}.txt"; exit 2; }
ok=0
cmp -s outputs/mcmc/chain_${TAG}_seed2026_n300.csv $REF/chain_L24_seed2026_n300.csv || { echo "[GATE] FAIL: 300-iteration chain differs from the L24 reference"; ok=1; }
cmp -s outputs/mcmc/adapted_cov_${TAG}_seed2026.csv $REF/adapted_cov_L24_seed2026.csv || { echo "[GATE] FAIL: adapted covariance differs from the L24 reference"; ok=1; }
[ $ok -eq 0 ] && echo "[GATE] PASS: calibrator reproduces the L24 objective byte-for-byte (300 iter, seed 2026)"
exit $ok
