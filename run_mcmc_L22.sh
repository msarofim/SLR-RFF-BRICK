#!/bin/bash
## L22 — L21's EXACT CONFIGURATION WITH ONE CHANGE: THE STERIC AR(1) NOISE IS CAPPED.
##
## THE QUESTION. L21's thermal expansion is +0.847 cm at 2025 = +16.9σ against the steric
## target's own per-year σ (0.050 cm, the ϵband floor), while sitting at -0.19σ in 1900 where
## the data are weakest — near-perfect where nothing constrains it, 17σ off where everything
## does. Reproduced here from outputs/postpred_L21_bias.csv: 1900 -0.19 | 1950 +0.25 |
## 2000 +2.11 | 2018 +4.45 | 2025 +16.94 σ.
##
## WHY THE NOISE MODEL IS THE FIRST SUSPECT AND NOT THE FUNCTIONAL FORM. A plain WLS of the
## CURRENT one-coefficient TE form lands at 2.15σ over 1993-2025 (offline, handoff §2b) — so
## the structure CAN fit the modern data and was never the binding constraint. What the fit
## has instead is a free AR(1) noise term sitting ON TOP of the observational variance:
## hetero_logl_ar1 builds Σ = σ²/(1-ρ²)·ρ^|i-j| + diag(ε²) with BOTH σ and ρ free. L21 fits
## σ_steric = 0.0716, ρ_steric = 0.9634 (verified 2026-08-29 from chain_L21_seed2026, post-burn
## 1M draws) => a MARGINAL sd of 0.267 cm, against a modern observational ε of ~0.10 cm. A
## persistent modern offset therefore costs the likelihood almost nothing.
##
## ⚠⚠ THE CAP IS ON THE MARGINAL, NOT ON σ. σ = 0.0716 *looks* comparable to ε ~ 0.10, and
## capping σ at the observational sigma WOULD NOT BIND AT ALL, because ρ inflates it by
## 1/sqrt(1-ρ²) = 3.72x. A σ-cap arm would come back looking like a null result having tested
## nothing (no_power_null). --steric-marg-cap= bounds σ/sqrt(1-ρ²).
##
## THE VALUE COMES FROM AN OBSERVATION (threshold_from_obs_or_law). =modern is the MEAN
## per-year σ of the steric target over 1993-2025, the altimetry era = 0.1036 cm, computed
## in-script from S.steric.ϵ — the ε the likelihood itself sees, floor included, so bound and
## bounded are on identical footing. It binds 2.6x tighter than L21's 0.267. Chosen by Marcus
## 2026-08-29 over the two alternatives: the 0.050 cm single-tightest-year floor (5.3x, forces
## the legitimately larger early-record discrepancy — ε is 0.51 cm in 1900-1950 — into the D2
## basis and the physical parameters), and a full-record mean of 0.310 cm, WHICH DOES NOT BIND
## AT ALL since L21 already sits below it.
##
## FALSIFIABLE PREDICTIONS, REGISTERED BEFORE THE RUN (handoff §1 TASK 1):
##   (i)   If the modern TE residual COLLAPSES toward ~2σ, the 17σ was the NOISE MODEL, not
##         the functional form, and the fix is a likelihood constraint — TASK 2 (the depth
##         split) then becomes a question about the PROJECTION, not about the fit.
##   (ii)  If it STAYS LARGE, something else holds TE up and the depth split is the live
##         candidate.
##   (iii) ⚠ EXPECT SOME OTHER AXIS TO LOOK WORSE. That is the cap working, not a regression.
##         Report what moved.
##   (iv)  ⚠ THE RESIDUAL MAY MOVE INTO d2_steric RATHER THAN INTO thermal_alpha. The D2
##         discrepancy basis is weighted by 1/ε², i.e. it is a modern-era-weighted term with
##         prior sd 0.5 cm — five times the cap. If the misfit is bought off there instead,
##         "the residual collapsed" is TRUE and "the noise model was the cause" is only HALF
##         true. Check d2_steric_1/_2 against L21 explicitly; d2_steric_1 already more than
##         doubled at the migration (0.1168 -> 0.2549).
##
## EVERYTHING ELSE IS L21's, UNCHANGED: amp ~ N(0.95, 0.10) passed EXPLICITLY (the code
## default moved to 1.09 at 893bfaa), --adcov=adapted_cov_L14tune_seed2026.csv, --overdisperse
## on the canonical outputs/mcmc/overdispersed_starts.csv, --gis-ordered --gis-basins2,
## 4 x 2M, seeds 2026-2029, BLAS pinned. The drivers are the migrated ones and the same
## 632f330 guard runs below.
##
## ⚠ THE STARTS ALL VIOLATE THE CAP AND ARE REPAIRED IN-SCRIPT. Every row of
## overdispersed_starts.csv is at marginal 0.187-0.234 and the default θ0 at 1.155; the
## repair scales σ (holding ρ) to half the cap and PRINTS what it did. The starts file itself
## is NOT touched — it is load-bearing for the L14/L18/L21 comparison.
##
## ⚠ L21 IS CHAMPION AND champions.json IS NOT TOUCHED BY THIS RUN. This is a DIAGNOSTIC arm.
## ⚠ CHECK uptime/swap AND READ THE ETA AT ~5 MIN (eta_in_days_is_not_a_slow_run).
##
##   bash run_mcmc_L22.sh [n_iter]        # default 2000000
set -e
cd "$(dirname "$0")"
NITER="${1:-2000000}"
TAG="${TAG:-L22}"
ADCOV=adapted_cov_L14tune_seed2026.csv
STARTS=outputs/mcmc/overdispersed_starts.csv
CAP="${CAP:-modern}"
mkdir -p outputs/mcmc
[[ -f "$STARTS" ]] || { echo "MISSING $STARTS"; exit 1; }
# guard: the drivers must actually be the migrated ones, or this run is a silent no-op
if ! git -C . log --oneline -1 -- data/observations/fair_mean_gmst_ssp245harm.csv | grep -q 632f330; then
  echo "⚠ fair_mean_gmst_ssp245harm.csv is NOT at migration commit 632f330 — refusing to run."
  echo "  Last touched by: $(git -C . log --oneline -1 -- data/observations/fair_mean_gmst_ssp245harm.csv)"
  exit 1
fi
echo "L22: 4 chains x $NITER (seeds 2026-2029) — L21 config + steric AR(1) MARGINAL cap ($CAP)"
echo "     amp ~ N(0.95, 0.10) [L21's], adcov=$ADCOV [L21's], overdispersed starts, BLAS pinned"
for SEED in 2026 2027 2028 2029; do
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
    julia --project=julia_v2 --threads=1 julia/calibrate_mcmc_ext.jl "$NITER" "$SEED" \
        --tag=$TAG --gis-ordered --gis-basins2 --overdisperse \
        --adcov=$ADCOV --amp-mu=0.95 --amp-sigma=0.10 \
        --steric-marg-cap=$CAP \
        > "outputs/mcmc/log_${TAG}_seed${SEED}.txt" 2>&1 &
done
wait
echo "L22 chains done. VERIFY FIRST: the header must say 'MARGINAL σ/sqrt(1-ρ²) CAPPED at"
echo "0.1036 cm', the steric start-repair line must have PRINTED, and no post-burn draw may"
echo "exceed the cap (python/check_steric_cap.py). Then: TAG=L22 bash run_l21_postprocess.sh"
