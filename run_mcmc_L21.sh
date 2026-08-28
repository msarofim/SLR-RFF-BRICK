#!/bin/bash
## L21 — L14's EXACT CONFIGURATION, RE-RUN ON THE calib 1.6.0 + CMIP7 DRIVERS.
##
## ⚠ THIS IS NOT ANOTHER AMP ARM. L15-L20 were amp-prior experiments and the amp question is
## CLOSED (decided 2026-08-27: keep N(0.95, 0.10) on fit; see CHANGELOG [DECIDED] 2026-08-27d).
## L21 changes NOTHING about the model or its priors. The ONLY thing that changed is the
## FORCING DRIVER underneath it, so L21 is the migrated champion candidate, not a new arm.
##
## WHAT CHANGED — EXACTLY ONE THING, AND IT IS NOT IN THIS SCRIPT:
##   data/observations/fair_mean_{gmst,ohc}_ssp245harm.csv were regenerated on
##   FaIR 2.2.4 (calib 1.6.0) + CMIP7 historical 1750-2023 spliced to chrisroadmap
##   MESSAGE-GLOBIOM SSP2-4.5 harmonized at 2023.5, CMIP7 volcanic + solar, PRESCRIBED
##   per-marker land use and irrigation (CMIP7 marker M). SLR-RFF-BRICK commit 632f330,
##   by the migration-owner session. Verified independently here: that commit touched
##   EXACTLY those two files, and the RCMIP-native fair_mean_gmst_ssp245.csv was NOT touched
##   (last written by f2b0a8d) — the harmonized-vs-RCMIP-native trap did not fire.
##
## EVERY FLAG BELOW IS L14's, UNCHANGED: --overdisperse on the canonical
## outputs/mcmc/overdispersed_starts.csv, --adcov=adapted_cov_L14tune_seed2026.csv,
## --gis-ordered --gis-basins2, amp ~ N(0.95, 0.10), 4 x 2M, seeds 2026-2029.
## ⚠ --amp-mu=0.95 MUST be passed explicitly: the code default moved to 1.09 at commit 893bfaa,
## so omitting it would silently run L16's centre and confound the migration with the amp arm.
##
## WHAT THE NEW DRIVER DOES (measured by the migration owner, spot-checked here):
##   GMST v160 - v145:  1900 +0.029 | 2020 -0.030 | 2050 -0.087 | 2100 -0.015 | 2300 +0.085 K
##   COOLER NEAR TERM, WARMER FAR TERM — 1.6.0's ocean is more sluggish
##   (ocean_heat_capacity[1] 15.27 -> 18.83, ocean_heat_transfer[2] 0.909 -> 1.089).
##   GMST RMSE vs IGCC 1850-2023: 0.107 -> 0.122 K   (a THIRD of the ensemble's own
##                                                    per-config p5-p95 RMSE spread of ~0.05 K)
##   OHC RMSE vs Zanna/IGCC 1870-2023: 6.80 -> 3.83 (1e22 J) — a 44% IMPROVEMENT.
##
## ⚠⚠ SO THE NEW OBJECTIVE IS NOT SIMPLY "WORSE". calibrate_mcmc_ext.jl fits BOTH gmst AND ohc.
## This is a small GMST degradation against a large OHC improvement. Per mimibrick-quirks item 10
## (TE scales with the OHC input alone, GIS with GMST alone) EXPECT THE TE SIDE TO MOVE MORE THAN
## THE GIS SIDE, and plausibly to move in a direction that helps. Watch it in the refit; do not
## assume it.
##
## FALSIFIABLE PREDICTIONS, registered before the run:
##   (i)   [MAP start] MUST DIFFER from L14's -642.84. If it does not, the driver did not
##         actually change under this run and the migration is a no-op — STOP.
##   (ii)  TE posterior moves MORE than GIS, on the OHC improvement. If GIS moves more, the
##         mimibrick-quirks item-10 separation does not hold here and that needs explaining.
##   (iii) The hindcast should NOT degrade materially: the champion is refit against SLR
##         observations, so a cooler driver is absorbed by higher sensitivities.
##   (iv)  ⚠ THE MARGINAL IS THE RISK, NOT THE LEVEL. A refit fixes the level; the migration
##         owner's paired pulse shows the marginal changes SHAPE (+16.7% dERF by 2300 but
##         -4.3% dT at 2050; the dT integral flips sign with discount rate). Marginal
##         SLR-per-GtCO2 must be checked before/after — see the coverage caveat in the handoff.
##
## ⚠ L14 IS STILL CHAMPION AND champions.json IS NOT TOUCHED BY THIS RUN. Promotion is Marcus's.
## L14's pre-migration outputs are COPIED (not moved) to
## outputs/quarantine/20260828_calib160_migration/L14_pre_migration/ — L14's own outputs were
## generated against drivers that NO LONGER EXIST in the working tree, so re-running any L14
## postprocessing step now would silently produce different numbers under the L14 name.
##
## ⚠ BLAS PINNED. ⚠ CHECK uptime/swap AND READ THE ETA AT ~5 MIN (eta_in_days_is_not_a_slow_run).
##
##   bash run_mcmc_L21.sh [n_iter]        # default 2000000
set -e
cd "$(dirname "$0")"
NITER="${1:-2000000}"
TAG="${TAG:-L21}"
ADCOV=adapted_cov_L14tune_seed2026.csv
STARTS=outputs/mcmc/overdispersed_starts.csv
mkdir -p outputs/mcmc
[[ -f "$STARTS" ]] || { echo "MISSING $STARTS"; exit 1; }
# guard: the drivers must actually be the migrated ones, or this run is a silent no-op
if ! git -C . log --oneline -1 -- data/observations/fair_mean_gmst_ssp245harm.csv | grep -q 632f330; then
  echo "⚠ fair_mean_gmst_ssp245harm.csv is NOT at migration commit 632f330 — refusing to run."
  echo "  Last touched by: $(git -C . log --oneline -1 -- data/observations/fair_mean_gmst_ssp245harm.csv)"
  exit 1
fi
echo "L21: 4 chains x $NITER (seeds 2026-2029) — L14 config on calib 1.6.0 + CMIP7 drivers"
echo "     amp ~ N(0.95, 0.10) [L14's], adcov=$ADCOV [L14's], overdispersed starts, BLAS pinned"
for SEED in 2026 2027 2028 2029; do
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
    julia --project=julia_v2 --threads=1 julia/calibrate_mcmc_ext.jl "$NITER" "$SEED" \
        --tag=$TAG --gis-ordered --gis-basins2 --overdisperse \
        --adcov=$ADCOV --amp-mu=0.95 --amp-sigma=0.10 \
        > "outputs/mcmc/log_${TAG}_seed${SEED}.txt" 2>&1 &
done
wait
echo "L21 chains done. VERIFY FIRST: 'A6 prior' = N(0.950, 0.100); [MAP start] MUST DIFFER from"
echo "L14's -642.84 (same prior, new driver) — if it equals it, the driver did not change."
