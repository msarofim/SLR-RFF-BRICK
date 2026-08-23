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
#   7. julia/test_ladrillo_basins2_variant.jl the projector can tell a 2-basin
#                                       posterior from a 3-basin one and projects
#                                       it under the right k. 6 checks the kernel
#                                       against ONE variant's constants; this
#                                       checks that the variant is CHOSEN right,
#                                       which is where the -1.7 cm silent-wrong-
#                                       model error lived.
#   5. calibrate_mcmc_ext.jl --gis-check the CALIBRATOR wires that component up
#                                       correctly. 4 validates the component in
#                                       isolation; the driver, the fixed g and v0,
#                                       the re-reference frame and the Mouginot
#                                       windows all live in the calibrator, and
#                                       none of them is covered by 4.
#   8. julia/test_greenland_3basin_nesting.jl  the 3-basin component COLLAPSES to
#                                       greenland_ab at k=(1,0,0), the partition is
#                                       exact under the per-basin clamp, and the
#                                       published 2-basin k is the one derived from
#                                       the Mouginot inventory
#   9. julia/test_gis_ordering_wedge.jl the channel-ordering wedge in the log-prior,
#                                       mutation-tested
#  10. julia/test_gis_tap_wiring.jl     the SHIPPED tap cell: 2100 exactly unmoved,
#                                       2150 moved by less than a spread-scaled
#                                       bound, the cell actually fires, both
#                                       mutations caught
#
# WHY 8-10 ARE HERE AS OF 2026-08-23. They gate the Greenland that SHIPS -- two
# basins, the reparameterised slow channel, the tap cell -- and until now they were
# run by hand and named only in the L12/L13/L14 production runbooks and in handoffs.
# Steps 1-7 gate the glacier module and the A+B Greenland that L14 superseded, so a
# green suite was certifying a model the deliverables are not produced with.
#
# 2 and 3 test the same physics through the two independent code paths that use
# it, so passing both is what says the calibration and the projections are the
# same model.
#
# Not run here: python/eval_chain_gates_extc.py, which evaluates acceptance
# gates for a specific MCMC chain and therefore needs chain files on disk.
#
# ONE DEPENDENCY ON outputs/, and it is deliberate: step 10 reads Greenland's own
# sampled p05-p95 at 2150 out of outputs/ssps_components_2300_<TAG>.csv to scale its
# tolerance, rather than hardcoding a centimetre bound that would silently stop
# tracking the model. It errors with the command to regenerate that file if absent.
# TAG defaults to the canonical vintage inside each test; pass --tag= to override.
#
#   ./run_ladrillo_tests.sh [n_draws]      # n_draws for the projection test, default 100
set -euo pipefail
cd "$(dirname "$0")"

NDRAW="${1:-100}"
: "${PYTHON:=$HOME/climate-env/bin/python3}"
JULIA="julia --project=julia_v2"

echo "=============================================================="
echo "[1/10] python/test_ladrillo_data.py"
echo "=============================================================="
(cd python && "$PYTHON" test_ladrillo_data.py)

echo
echo "=============================================================="
echo "[2/10] julia/validate_glaciers_nu3.jl (both amp bases)"
echo "=============================================================="
for basis in regchar obsfit; do
    echo "--- amp basis: $basis ---"
    $JULIA julia/validate_glaciers_nu3.jl 2000 2026 --amp-basis=$basis | grep -E "^\[|VALIDATION"
done

echo
echo "=============================================================="
echo "[3/10] julia/test_ladrillo_projection.jl ($NDRAW draws)"
echo "=============================================================="
$JULIA julia/test_ladrillo_projection.jl "$NDRAW"

echo
echo "=============================================================="
echo "[4/10] julia/validate_greenland_ab.jl"
echo "=============================================================="
"$PYTHON" python/emit_gis_port_reference.py
$JULIA julia/validate_greenland_ab.jl

echo
echo "=============================================================="
echo "[5/10] julia/calibrate_mcmc_ext.jl --gis-check (calibrator wiring)"
echo "=============================================================="
$JULIA julia/calibrate_mcmc_ext.jl 1 2026 --tag=gischeck --gis-check \
    | sed -n '/--gis-check/,$p'

echo
echo "=============================================================="
echo "[6/10] julia/validate_gis_projection_ab.jl (projection kernel)"
echo "=============================================================="
$JULIA julia/validate_gis_projection_ab.jl

echo
echo "=============================================================="
echo "[7/10] julia/test_ladrillo_basins2_variant.jl (2-basin variant)"
echo "=============================================================="
$JULIA julia/test_ladrillo_basins2_variant.jl

echo
echo "=============================================================="
echo "[8/10] julia/test_greenland_3basin_nesting.jl (partition + 2-basin k)"
echo "=============================================================="
$JULIA julia/test_greenland_3basin_nesting.jl

echo
echo "=============================================================="
echo "[9/10] julia/test_gis_ordering_wedge.jl (channel-ordering prior)"
echo "=============================================================="
$JULIA julia/test_gis_ordering_wedge.jl

echo
echo "=============================================================="
echo "[10/10] julia/test_gis_tap_wiring.jl (the SHIPPED tap cell)"
echo "=============================================================="
$JULIA julia/test_gis_tap_wiring.jl

echo
echo "ALL Ladrillo MODEL TESTS PASS"
