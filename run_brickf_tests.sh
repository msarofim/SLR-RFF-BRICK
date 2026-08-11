#!/usr/bin/env bash
# run_brickf_tests.sh — every BRICK-F* model test, in dependency order.
#
#   1. python/test_brickf_data.py       the data-assembly module reproduces the
#                                       committed calibrator inputs byte-for-byte,
#                                       and the constants satisfy the relations
#                                       they encode (inventory, response times,
#                                       committed ladder, target seam, drivers)
#   2. julia/validate_glaciers_nu3.jl   the CALIBRATOR's code path reproduces the
#                                       python offline reference, both amp bases
#   3. julia/test_brickf_projection.jl  the PROJECTION kernel reproduces the same
#                                       reference, applies the posterior
#                                       deterministically, and is physically
#                                       monotone across scenarios
#   4. julia/validate_greenland_ab.jl   the Greenland A+B component reproduces
#                                       python/gis_offline_cell.py at 1e-9, keeps
#                                       the slot contract, and starts at BRICK's
#                                       initial condition rather than in
#                                       equilibrium (Greenland pass 1)
#
# 2 and 3 test the same physics through the two independent code paths that use
# it, so passing both is what says the calibration and the projections are the
# same model.
#
# Not run here: python/eval_chain_gates_extc.py, which evaluates acceptance
# gates for a specific MCMC chain and therefore needs chain files on disk.
#
#   ./run_brickf_tests.sh [n_draws]      # n_draws for the projection test, default 100
set -euo pipefail
cd "$(dirname "$0")"

NDRAW="${1:-100}"
: "${PYTHON:=$HOME/climate-env/bin/python3}"
JULIA="julia --project=julia_v2"

echo "=============================================================="
echo "[1/4] python/test_brickf_data.py"
echo "=============================================================="
(cd python && "$PYTHON" test_brickf_data.py)

echo
echo "=============================================================="
echo "[2/4] julia/validate_glaciers_nu3.jl (both amp bases)"
echo "=============================================================="
for basis in regchar obsfit; do
    echo "--- amp basis: $basis ---"
    $JULIA julia/validate_glaciers_nu3.jl 2000 2026 --amp-basis=$basis | grep -E "^\[|VALIDATION"
done

echo
echo "=============================================================="
echo "[3/4] julia/test_brickf_projection.jl ($NDRAW draws)"
echo "=============================================================="
$JULIA julia/test_brickf_projection.jl "$NDRAW"

echo
echo "=============================================================="
echo "[4/4] julia/validate_greenland_ab.jl"
echo "=============================================================="
"$PYTHON" python/emit_gis_port_reference.py
$JULIA julia/validate_greenland_ab.jl

echo
echo "ALL BRICK-F* MODEL TESTS PASS"
