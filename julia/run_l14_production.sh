#!/bin/bash
# L14 production: 4 x 2M over-dispersed chains — the TWO-BASIN Greenland.
# Decided by Marcus 2026-08-20; execution plan notes/handoff_2026-08-20c_two_basin_plan.md.
#
# L14 = L13's change set with --gis-basins REPLACED by --gis-basins2. Exactly ONE
# variable moves, so the result is attributable. Everything else is inherited by NOT
# passing a restore flag: --gis-ordered (the channel wedge), D1 (total dropped), the
# GlaMBIE R19 rate term, the tightened rung sigma, D2, the (ell, w) reparameterisation,
# and GIS_ZONE = south. The `all` zone is a SEPARATE run (L15) with its own prerequisite
# chain — do not fold it in here.
#
# WHAT --gis-basins2 IS. NOT a new component: greenland_3basin at k_mid = 0 IS a
# two-basin model, by construction (eq_b == k_b * eq_whole identically) and by
# measurement (test_greenland_3basin_nesting.jl gate [4], max|diff| 4.4e-16 against
# whole-sheet greenland_ab; gate [5] mutation-tests [4] and trips at 4.0e-02).
#
#   active = SW + CW + CE + SE + NW    k 0.628571   carried in the `south` SLOT
#   high   = NO + NE                   k 0.371429   ONE sampled rate scale, gis_s_high
#
# WHY TWO. Refitting every structure in the offline Greenland cell returns s_mid =
# 1.024; pinning it to 1 costs Delta nlp 0.0023 and the PROFILE IS WELL CURVED (+6.3 at
# s_mid 0.25, +7.3 at 3.98) — so s_mid is IDENTIFIED-and-equal-to-1, not merely
# unconstrained, and the prototype's 4.47x is excluded at Delta nlp > 7. Two basins also
# fit the Mouginot windows BETTER (worst |z| 0.69 vs 1.01) with one fewer parameter,
# because a single NW scale cannot span the two-window tension 0.207 -> 0.262.
# Evidence: 03df3d2, outputs/scope_gis_basin_structure{,_profile}.csv.
#
# STANDING CAVEAT, on the record: that evidence is the Greenland-ONLY offline cell — no
# BRICK coupling, no AR(1) noise, none of the other likelihood terms. It has NOT been
# shown to transfer. THIS RUN IS THE TRANSFER TEST.
#
# WHAT CHANGED IN THE LAYOUT, and why the covariance must be re-tuned. gis_s_mid is
# DROPPED from FREE: at k_mid = 0 it multiplies a zero-commitment basin and does
# nothing, and a dead sampled parameter is a random walk that inflates the proposal and
# hides defects. NK goes 59 -> 58, so no covariance on disk matches BY SIZE and every
# seed goes through embed_cov! BY NAME. That is the THIRD layout change in this arc and
# BOTH previous ones bit: the ADCOV size collision that gave acceptance exactly 0.0, and
# the L11_NAMES mis-order that voided L13's first line by handing ais_c the variance of
# ais_slope. The seed gate now covers gis_s_high as well as the AIS geometry block
# (GEO_SEED_FLOOR; floor 1e-3 against L13's tuned 0.0234).
#
# The shares term switches to the 2-way targets automatically — active = south + mid,
# so 0.799 / 0.201 and 0.816 / 0.183, sd 0.05 — and only ONE share per window is scored,
# because with two basins only one is independent.
#
# EXPECTED, from the offline 2-basin refit: s_high ~ 0.20-0.30 (L13's 3-basin posterior
# gave 0.268, the offline 3-basin refit 0.259, the offline 2-basin refit 0.229), worst
# |z| ~ 0.7, hindcast RMSE ~ 0.0617 cm. A calibrated s_high near 1 means the shares term
# is not biting; below ~0.1 means it is dominating.
#
# WHAT WILL NOT CHANGE, so nobody reads it as failure: NO basin structure buys the 2300
# scenario separation. One / two / three basins give ssp585@2300 ratios 2.69x / 2.73x /
# 2.72x, all inside the single-law ridge ceiling of 1.72-3.36x, against the literature's
# 7.9-31.9x. The restructure fixes the PARTITION; the TAP fixes the SEPARATION. A 2-basin
# run coming back at ratio ~2.7x untapped has behaved exactly as expected.
#
# L12 REMAINS CANONICAL (SLR@2100 45.53 cm) throughout. This run promotes nothing.
# L13 is intact and certified at 44.97 cm, subsample at
# data/MimiBRICK/parameters_subsample_brick_mengel_L13.csv.
#
# PRECONDITIONS (the script checks all of them):
#   1. adapted_cov_L14tune_seed2026.csv exists — tuned WITH --gis-basins2. An L13
#      covariance is 59x59 against NK=58 and carries a gis_s_mid row with no target.
#   2. overdispersed_starts.csv rebuilt from the L14tune chain. NOTE the trap: an
#      L13-vintage starts file PASSES the calibrator's by-name guard, because a
#      gis_s_mid column it does not need is simply ignored. The checks below catch it.
#   3. julia/test_greenland_3basin_nesting.jl (gates [4] and [5]) and
#      ./run_ladrillo_tests.sh pass, and --gis-check scores 0.0000 under --gis-basins2.
#
# Threads: ONE per chain — four chains x 4 BLAS threads spend about half their CPU in
# OpenBLAS spin-wait; pinning to 1 took L10 from an 11h ETA to 2h15m.
set -euo pipefail
cd "$(dirname "$0")/.."

N_ITER=2000000
TAG=L14
SEEDS="2026 2027 2028 2029"
BASINFLAG=--gis-basins2

ADCOV=outputs/mcmc/adapted_cov_L14tune_seed2026.csv
STARTS=outputs/mcmc/overdispersed_starts.csv
TUNECHAIN=outputs/mcmc/chain_L14tune_seed2026_n1000000.csv
# The L14tune run seeds from the L13 PRODUCTION covariance, name-mapped: 58 of its 59
# rows land, gis_s_mid is dropped for want of a target. That is the correct seed — it
# carries L13's tuned shape for every parameter the two runs share, including gis_s_high.
TUNESEED=adapted_cov_L13_seed2026.csv

[[ -f "$ADCOV" ]] || { echo "MISSING $ADCOV — run the L14tune tuning run first:"; \
  echo "  julia --project=julia_v2 julia/calibrate_mcmc_ext.jl 1000000 2026 --tag=L14tune --gis-ordered $BASINFLAG --adcov=$TUNESEED"; exit 1; }
[[ -f "$STARTS" ]] || { echo "MISSING $STARTS"; exit 1; }

# The starts must carry the L14 columns. The calibrator's by-name assertion is
# authoritative for what must be PRESENT; these are cheap early checks that name the fix.
for col in gis_slow_ell d2_gsic_1 gis_s_high; do
  head -1 "$STARTS" | tr ',' '\n' | grep -qx "$col" || {
    echo "$STARTS is missing '$col' — rebuild it from the L14tune chain:"
    echo "  cp $STARTS ${STARTS}.pre_l14_bak"
    echo "  julia --project=julia_v2 julia/build_overdispersed_starts.jl $TUNECHAIN"
    exit 1; }
done
# AND IT MUST NOT CARRY gis_s_mid. This is the check the calibrator CANNOT make for us:
# a column that is not in pn0 is silently ignored, so an L13-vintage starts file passes
# the by-name guard and puts all four chains at a 3-basin posterior draw.
if head -1 "$STARTS" | tr ',' '\n' | grep -qx "gis_s_mid"; then
  echo "$STARTS carries a 'gis_s_mid' column, so it came from a 3-BASIN (L13) chain."
  echo "The calibrator would accept it silently — the column is simply unused."
  echo "Rebuild it from the L14tune chain:"
  echo "  cp $STARTS ${STARTS}.pre_l14_bak"
  echo "  julia --project=julia_v2 julia/build_overdispersed_starts.jl $TUNECHAIN"
  exit 1
fi
# PROVENANCE: starts built from a pre-L14 chain would put chains in the rejected
# region, where every MH ratio is NaN and acceptance is exactly 0.0.
[[ -f "$TUNECHAIN" ]] || { echo "MISSING $TUNECHAIN"; exit 1; }
[[ "$STARTS" -nt "$TUNECHAIN" ]] || {
  echo "$STARTS is OLDER than $TUNECHAIN — it was built from a different chain."
  echo "Rebuild it, or the chains start outside the wedge:"
  echo "  cp $STARTS ${STARTS}.pre_l14_bak"
  echo "  julia --project=julia_v2 julia/build_overdispersed_starts.jl $TUNECHAIN"
  exit 1; }

echo "L14 production: 4 x $N_ITER, seeds $SEEDS, tag=$TAG  (--gis-ordered $BASINFLAG)"
echo "  proposal seed: $ADCOV"
echo "  starts:        $STARTS"
echo "  EXPECT s_high in roughly 0.20-0.30 and worst |z| ~ 0.7. EXPECT the 2300 ratio to"
echo "  stay near 2.7x — the tap, not the structure, is what buys the separation."
for SEED in $SEEDS; do
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
    julia --project=julia_v2 --threads=1 julia/calibrate_mcmc_ext.jl "$N_ITER" "$SEED" \
      --tag=$TAG --gis-ordered $BASINFLAG --overdisperse --adcov="$ADCOV" \
      > "outputs/mcmc/log_${TAG}_seed${SEED}.txt" 2>&1 &
done
wait
echo "L14 production complete: outputs/mcmc/chain_${TAG}_seed{2026..2029}_n${N_ITER}.csv"
echo "next, IN THIS ORDER (the other way round leaves you with no subsample):"
echo "  julia --project=julia_v2 julia/postprocess_mcmc_ext.jl --tag=$TAG"
echo "  julia --project=julia_v2 julia/diag_slr_convergence_by_chain_ladrillo.jl --tag=$TAG"
echo "  julia --project=julia_v2 julia/postprocess_mcmc_ext.jl --tag=$TAG --accept-slr"
echo "  julia --project=julia_v2 julia/diag_l13_basin_shares.jl --tag=$TAG   (2-basin adaptation)"
