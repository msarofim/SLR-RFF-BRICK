#!/bin/bash
## L35 (2026-09-24) = L32 PLUS `--ais-fit-from=1979`. CONTROL = L32, ONE AXIS.
##
## ⭐⭐ WHAT IT IS: THE MISSING CELL OF THE (noise floor x fit span) 2x2 AT THE IMBIE TARGET.
##
##                      full fit 1900-        fitted 1979+ only
##   free sd_ais        L28                   L31   (ran 09-22)
##   floored sd_ais     L32  (the arm in      L35   <- THIS ARM, never run
##                            the Tony memo)
##
## ⭐ WHY L31 DOES NOT ALREADY ANSWER STEP 2. The 09-24c handoff proposed "L35 = the IMBIE target
## build + --ais-fit-from=1979", which taken literally IS L31 -- already run, already on disk, and
## scored 09-24f by python/diag_ais_heldout_pre1979.py: the held-out 1900-1978 SHAPE error is
## 0.3241 cm = 1.39x the Frederikse target's own published band over that window ==> FAIL (and a
## FAIL is AMBIGUOUS, by pre-registration, because the held-out data is the product under doubt).
##
## But L31 carries FREE sd_ais and the memo's arm does not, and that same scoring run measured the
## floor to be worth a LOT pre-1979 on this target: at the SAME target and the SAME full fit span,
## L28 -> L32 cuts the pre-1979 shape error 0.1501 -> 0.0501 cm, a factor 3.0. On the FREDERIKSE
## target the same floor moves it the other way (L27 0.0241 -> L34 0.0305). That is the SAME
## target-dependent interaction the L34 cell found on the dynamics channel
## ([[ais_noise_floor_is_target_dependent]]: -1.4 Gt/yr on Frederikse vs -61.9 on IMBIE) -- and it
## is the documented reason a 2x2 cell may NOT be inferred from its neighbours here. So reading
## L31's FAIL as L32's would be re-running exactly the error L34 was built to catch.
##
## ⛔⛔ L35's LOGPOST IS NOT COMPARABLE TO L32's, NOR TO L27's OR L28's. Dropping 79 years removes 79
## likelihood terms: L31 measured logpost(theta0) = -1220.7 on the full span vs -554.95 on 1979+.
## That ~666 is BOOKKEEPING, not fit. Compare on HINDCAST STATISTICS and the channels, never on
## log_post. (L35 adds a floor on top, which moves the sigma scale as well.)
##
## ⭐ SUCCESS CRITERIA, PRE-REGISTERED -- committed BEFORE the chains start, and the BOUND COMES FROM
## AN OBSERVATION, not from the code under test (`threshold_from_obs_or_law`):
##
##   PRIMARY  HELD-OUT 1900-1978 AIS SHAPE ERROR (the residual sd after removing the window mean).
##            ⚠ The SHAPE, not the RMSE, and that choice is pre-registered and reasoned: pre-1979
##            the two target builds are the SAME Frederikse data differing by EXACTLY a constant
##            -0.134074 cm, which is a 1995-2005 re-referencing artefact and not data. The shape
##            statistic is identical under both builds; an RMSE is not.
##              BOUND = the Frederikse target's OWN published 1-sigma band over 1900-1978,
##              sigma_1900_78 = 0.2337 cm (NOT the bench's whole-record sigma-bar 0.1674, which is
##              dragged down by the 0.01 cm post-2018 cliff years).
##              PASS  <= 0.2337 cm (1.00 sigma)  -- the floor rescues the held-out prediction.
##              FAIL  >= 0.3241 cm               -- no better than free-sd L31; the floor bought
##                                                  nothing here.
##              0.2337-0.3241 is PARTIAL and must be reported as PARTIAL, not rounded to either.
##
##   INTERACTION  A MEASUREMENT, NOT A PASS/FAIL. The floor's effect on the pre-1979 hindcast at the
##            full fit span is L28 -> L32 = -0.1000 cm. Report L31 -> L35 beside it. If the two
##            differ by more than the bench's own 2% dead band, the floor and the fit span INTERACT
##            and neither cell may be inferred from the other in any future write-up.
##
##   GUARD    the four non-Antarctic components within ~0.02 sigma of L32. If Greenland / glaciers /
##            thermal expansion move, the change did not stay Antarctic and the arm is not
##            interpretable as an Antarctic experiment.
##
##   COST     the IN-SAMPLE 1979-2025 AIS fit. L35 still fits those 47 years; if it degrades them to
##            buy the held-out window, that is the price and it is stated next to the result.
##
##   ⚠ NOT A CRITERION: sd_ais sitting on its bound (true BY CONSTRUCTION); log_post (see above).
##
## ⚠⚠ THE ASYMMETRY, STATED HERE AND NOT ONLY IN THE READ-OUT. This test is ONE-SIDED, in the
## OPPOSITE direction from the GRACE test (09-23h). A PASS is INFORMATIVE: the two products are
## reconcilable and the pre-1979 loss is not intrinsic to fitting IMBIE. A FAILURE is AMBIGUOUS: the
## held-out data IS the product under doubt, so it cannot separate "the model is wrong" from
## "Frederikse is wrong."
##
## ⚠ POWER. L31 vs L28 measured +115.9% -- far outside the 2% dead band -- so the held-out years DO
## do work on this target and the test is not structurally null. That was measured on the free-sd
## cell; the read-out repeats it for L35 vs L32.
##
## ⛔ NO TARGET SWAP AND NONE IS WANTED. L35 trains on the IMBIE-2026 build, which is ALREADY live
## (md5 eb768cd9...), so unlike run_L34.sh there is no swap, no exit trap, and no window in which
## another arm's gate would fail. The md5 is still GATED, not assumed: 09-24b's lesson is that a
## gate must point at a file the scoring actually reads, and this one does -- calibrate_mcmc_ext.jl
## reads outputs/recalib_targets_ext.csv directly.
##
## Everything else is L32's, unchanged: BASEFLAGS + --no-ledger (50 params), --sd-ais-floor=smb,
## seeds 2026-2029, L27's pooled proposal covariance, overdispersed_starts_L27r_sdfloor.csv.
## 4 chains in parallel on the Mac, ~3 h at L32's pace; launched at load 1.49 with no other chains
## running (checked, per `eta_in_days_is_not_a_slow_run`).
## TORCH CONSIDERED AND NOT WARRANTED: every arm L27-L34 ran here and the Julia/Mimi/MimiBRICK stack
## is not provisioned on Torch. Kill by PID (never pkill -f); log = outputs/log_L35.txt.
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
LOG=outputs/log_L35.txt; : > "$LOG"
say(){ echo "[$(date '+%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

[[ "$(md5 -q outputs/recalib_targets_ext.csv)" == "eb768cd96463a3b84721e2bb9a20f009" ]] \
  || { echo "target file is not the IMBIE-2026 build; refusing to start"; exit 2; }
say "target gate PASSED: $(md5 -q outputs/recalib_targets_ext.csv) (IMBIE-2026 build)"
say "provenance stamp: $(grep -E '^(ais_source|reproduces)' outputs/recalib_targets_ext_provenance.txt | tr '\n' ' ')"

J="julia --project=julia_v2"
NITER=2000000
BASEFLAGS="--gis-ordered --gis-basins2 --amp-mu=1.09 --amp-sigma=0.180 --paleo-priors --no-delta --no-d2-gsic --obs-corr-len=100 --toff-lo=-4 --precip-reparam --cut-fastdyn --fix-gamma"
ARMFLAG="--sd-ais-floor=smb --ais-fit-from=1979"
STARTS=outputs/mcmc/overdispersed_starts_L27r_sdfloor.csv

FAILED_STEPS=0
step(){ local nm="$1"; shift
  say "START  $nm"
  if "$@" >> "$LOG" 2>&1; then say "OK     $nm"; else say "FAILED $nm (rc=$?) — continuing"; FAILED_STEPS=$((FAILED_STEPS+1)); fi
}

run_chains(){ # TAG SEEDS STARTS ADCOV FLAGS
  local T="$1" SEEDS="$2" ST="$3" ADCOV="$4" FLAGS="$5"
  [[ -f "$ST" ]] || { say "MISSING $ST"; return 1; }
  [[ -f "outputs/mcmc/$ADCOV" ]] || { say "MISSING outputs/mcmc/$ADCOV"; return 1; }
  say "$T: 4 chains x $NITER (seeds $SEEDS) — $FLAGS ; adcov=$ADCOV starts=$ST ; commit $(git rev-parse --short HEAD) ; load $(uptime | sed 's/.*load averages*: //')"
  local PIDS=()
  for SEED in $SEEDS; do
    $J --threads=1 julia/calibrate_mcmc_ext.jl "$NITER" "$SEED" \
        --tag=$T --overdisperse --starts=$ST --adcov=$ADCOV $FLAGS \
        > "outputs/mcmc/log_${T}_seed${SEED}.txt" 2>&1 &
    PIDS+=($!)
  done
  say "  chain PIDs: ${PIDS[*]}"
  wait "${PIDS[@]}"
  say "$T chains done. ARM VERIFICATION:"
  ## ⚠ BOTH arm flags are read BACK OFF THE RUN, never inferred from the flag string. A dropped
  ## --sd-ais-floor gives a second L31; a dropped --ais-fit-from gives a second L32. Either would
  ## be a duplicate arm wearing a new label, which is the whole hazard this 2x2 exists to avoid.
  local NBAD=0
  for SEED in $SEEDS; do
    say "  seed$SEED: $(tr '\r' '\n' < outputs/mcmc/log_${T}_seed${SEED}.txt | grep -a -m1 'L26 structure flags') | $(tr '\r' '\n' < outputs/mcmc/log_${T}_seed${SEED}.txt | grep -a -m1 'seeding proposal' | cut -c1-90)"
    say "    floor:  $(tr '\r' '\n' < outputs/mcmc/log_${T}_seed${SEED}.txt | grep -a -m1 'sd_ais FLOOR' | cut -c1-120)"
    say "    window: $(tr '\r' '\n' < outputs/mcmc/log_${T}_seed${SEED}.txt | grep -a -m1 'Extended fit windows' | cut -c1-120)"
    say "    restr:  $(tr '\r' '\n' < outputs/mcmc/log_${T}_seed${SEED}.txt | grep -a -m1 'AIS LEVEL TERM RESTRICTED' | cut -c1-140)"
    tr '\r' '\n' < "outputs/mcmc/log_${T}_seed${SEED}.txt" | grep -aq 'FLOOR DERIVED FROM OBSERVATION' \
      || { say "    *** FLOOR GATE FAILED on seed $SEED: sd_ais is NOT floored from the observation ***"; NBAD=$((NBAD+1)); }
    tr '\r' '\n' < "outputs/mcmc/log_${T}_seed${SEED}.txt" | grep -aq 'ais 1979-' \
      || { say "    *** SPAN GATE FAILED on seed $SEED: the AIS term is NOT restricted to 1979+ ***"; NBAD=$((NBAD+1)); }
  done
  (( NBAD == 0 )) || { say "*** ARM VERIFICATION FAILED ($NBAD) — this is not L35; do not postprocess ***"; return 1; }
  say "  arm verification PASSED on all seeds: floored AND restricted to 1979+"
}

noise_gate(){ # TAG SEEDS
  source ~/climate-env/bin/activate
  python - "$1" $2 >> "$LOG" 2>&1 <<'PY'
import sys, pandas as pd
t = sys.argv[1]; bad = []
for s in sys.argv[2:]:
    d = pd.read_csv(f"outputs/mcmc/chain_{t}_seed{s}_n2000000.csv", usecols=["sd_gis", "sd_ais", "log_post"]); d = d.iloc[len(d)//2:]
    m = d.sd_gis.median(); print(f"  seed{s}: sd_gis median {m:.4f}  sd_ais {d.sd_ais.median():.4f}  log_post {d.log_post.median():.1f}  {'OK' if m < 0.10 else '*** NOISE MODE ***'}")
    if m >= 0.10: bad.append(s)
print(f"NOISE-MODE GATE {t}:", "PASS" if not bad else f"FAIL on seeds {bad}")
PY
  grep -q "NOISE-MODE GATE $1: PASS" "$LOG"
}

postprocess(){ # TAG
  local T="$1"
  step "$T slr convergence diag" $J julia/diag_slr_convergence_by_chain_ladrillo.jl --tag=$T
  step "$T postprocess (subsample; DO NOT KILL)" $J julia/postprocess_mcmc_ext.jl --tag=$T --accept-slr
  ## ⚠ the priors dump MUST precede posterior_predictive: the latter recovers the restricted AIS
  ## span from the priors file's provenance (posterior_predictive_ladrillo.jl:138, the L31 lesson).
  ## Out of order, L35's pre-1979 rows would be mislabelled IN-sample -- silently, and in exactly
  ## the window this arm exists to measure.
  step "$T priors dump" $J --threads=1 julia/calibrate_mcmc_ext.jl 1 2026 --tag=$T $BASEFLAGS --no-ledger $ARMFLAG --dump-priors
  step "$T posterior predictive" $J julia/posterior_predictive_ladrillo.jl --tag=$T
  step "$T ssp components (tap, fixed climate)" $J julia/project_ssps_components_ladrillo.jl --tag=$T
  step "$T DAIS flux split vs IMBIE" $J julia/diag_ais_flux_split_vs_imbie.jl --tag=$T 1000
  source ~/climate-env/bin/activate
  step "$T prior/posterior table" python python/ladrillo_prior_posterior_table.py --tag=$T
}

## ---- L35 ---------------------------------------------------------------------------------------
if run_chains L35 "2026 2027 2028 2029" "$STARTS" adapted_cov_L27_named.csv "$BASEFLAGS --no-ledger $ARMFLAG"; then
  if noise_gate L35 "2026 2027 2028 2029"; then postprocess L35
  else say "L35 noise-mode gate FAILED — not postprocessing (investigate, do not --force)"; FAILED_STEPS=$((FAILED_STEPS+1)); fi
else
  say "L35 chains/arm verification FAILED — not postprocessing"; FAILED_STEPS=$((FAILED_STEPS+1))
fi
## ⚠ the held-out read-out is NOT run here: it scores every arm and belongs in one place.
## After ALLDONE:  python python/diag_ais_heldout_pre1979.py
(( FAILED_STEPS == 0 )) && say "ALLDONE — 0 failed step(s)" \
  || { say "INCOMPLETE — $FAILED_STEPS failed step(s); do not read the outputs as final."; exit 1; }
