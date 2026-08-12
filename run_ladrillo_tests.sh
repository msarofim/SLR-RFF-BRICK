#!/usr/bin/env bash
# run_ladrillo_tests.sh — every Ladrillo model test, in dependency order.
#
#   1. python/test_ladrillo_data.py       the data-assembly module reproduces the
#                                       committed calibrator inputs byte-for-byte,
#                                       and the constants satisfy the relations
#                                       they encode (inventory, response times,
#                                       committed ladder, target seam, drivers)
#   2. julia/validate_glaciers_nu3.jl   the CALIBRATOR's code path reproduces the
#                                       python offline reference, both amp bases
#   3. julia/test_ladrillo_projection.jl  the PROJECTION kernel reproduces the same
#                                       reference, applies the posterior
#                                       deterministically, and is physically
#                                       monotone across scenarios
#   4. julia/validate_greenland_ab.jl   the Greenland A+B COMPONENT reproduces
#                                       python/gis_offline_cell.py at 1e-9, keeps
#                                       the slot contract, and starts at BRICK's
#                                       initial condition rather than in
#                                       equilibrium (Greenland pass 1)
#   6. julia/validate_gis_projection_ab.jl the PROJECTION kernel can consume a
#                                       Ladrillo 1.0 posterior and builds
#                                       Greenland the same way the calibrator
#                                       does (constant parity + end-to-end)
#   5. calibrate_mcmc_ext.jl --gis-check the CALIBRATOR wires that component up
#                                       correctly. 4 validates the component in
#                                       isolation; the driver, the fixed g and v0,
#                                       the re-reference frame and the Mouginot
#                                       windows all live in the calibrator, and
#                                       none of them is covered by 4.
#
# 2 and 3 test the same physics through the two independent code paths that use
# it, so passing both is what says the calibration and the projections are the
# same model.
#
# Not run here: python/eval_chain_gates_extc.py, which evaluates acceptance
# gates for a specific MCMC chain and therefore needs chain files on disk.
#
#   ./run_ladrillo_tests.sh [n_draws]      # n_draws for the projection test, default 100
set -euo pipefail
cd "$(dirname "$0")"

NDRAW="${1:-100}"
: "${PYTHON:=$HOME/climate-env/bin/python3}"
JULIA="julia --project=julia_v2"

echo "=============================================================="
echo "[1/6] python/test_ladrillo_data.py"
echo "=============================================================="
(cd python && "$PYTHON" test_ladrillo_data.py)

echo
echo "=============================================================="
echo "[2/6] julia/validate_glaciers_nu3.jl (both amp bases)"
echo "=============================================================="
for basis in regchar obsfit; do
    echo "--- amp basis: $basis ---"
    $JULIA julia/validate_glaciers_nu3.jl 2000 2026 --amp-basis=$basis | grep -E "^\[|VALIDATION"
done

echo
echo "=============================================================="
echo "[3/6] julia/test_ladrillo_projection.jl ($NDRAW draws)"
echo "=============================================================="
$JULIA julia/test_ladrillo_projection.jl "$NDRAW"

echo
echo "=============================================================="
echo "[4/6] julia/validate_greenland_ab.jl"
echo "=============================================================="
"$PYTHON" python/emit_gis_port_reference.py
$JULIA julia/validate_greenland_ab.jl

echo
echo "=============================================================="
echo "[5/6] julia/calibrate_mcmc_ext.jl --gis-check (calibrator wiring)"
echo "=============================================================="
$JULIA julia/calibrate_mcmc_ext.jl 1 2026 --tag=gischeck --gis-check \
    | sed -n '/--gis-check/,$p'

echo
echo "=============================================================="
echo "[6/6] julia/validate_gis_projection_ab.jl (projection kernel)"
echo "=============================================================="
$JULIA julia/validate_gis_projection_ab.jl

echo
echo "ALL Ladrillo MODEL TESTS PASS"
