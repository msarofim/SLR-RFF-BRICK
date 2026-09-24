#!/bin/bash
## L34 (2026-09-24) = L27 PLUS `--sd-ais-floor=smb`. CONTROL = L27, ONE AXIS.
##
## ⭐⭐ WHAT IT IS: THE MISSING CELL OF A 2x2 (Marcus, 09-23: "what about fixing the noise
## specification on L27?").
##
##                     free sd_ais          floored sd_ais
##   Frederikse target  L27 (CHAMPION)      L34  <- this arm, never run
##   IMBIE-2026 target  L28                 L32 / L33
##
## L32 changed TWO things at once — the AIS target AND the noise model — and won on the dynamics
## while LOSING the full-period AIS to L27 (0.88 vs 0.70 sigma). L34 separates them: the noise fix
## ALONE, on the champion's own target.
##
## ⭐ WHY IT IS NOT MERE TIDINESS. 09-23b measured that the misspecified noise term does not only
## under-disperse the posterior — it BIASES THE MEAN, because the mean is made to do the noise's
## job (L32's AIS hindcast bias at 1900 went -0.524 -> -0.154 when the floor went on; I had
## predicted the opposite). L27 carries the SAME misspecification: its fitted sd_ais is 0.02162 cm
## against the SMB-derived floor of 0.03259 — a factor 1.51 BELOW it. So the champion's mean may be
## biased too, and the floor may improve the very statistic L27 currently wins on.
##
## ⚠ THE FLOOR IS IDENTICAL TO L32's, and that is checked, not assumed: `--sd-ais-floor=smb` derives
## it from data/observations/raw/imbie2026/imbie3_antarctica_Gt_partitioned.csv at run time, which is
## INDEPENDENT of which level target is live. The per-chain FLOOR GATE below reads the value back.
##
## ⚠⚠ THIS ARM IS NOT "PURE FREDERIKSE" AND MUST NOT BE DESCRIBED AS ONE. The floor is an
## IMBIE-derived statistic. It is a VARIABILITY channel, not a LEVEL one — a different piece of
## information from the level series L28/L32 fit — but IMBIE information enters L34, and any write-up
## says so. (Same import as L32; only the level target differs.)
##
## ⭐ SUCCESS CRITERIA, PRE-REGISTERED (Marcus, 09-23, chosen BEFORE the numbers land):
##   PRIMARY  FULL-PERIOD AIS RMSE in the whole-model benchmark, scored on the LIVE IMBIE target in
##            ONE run against the frozen `L27*` column — the only valid ruler (09-23d).
##            WIN <= 0.70 sigma (matches or beats the champion on the statistic that currently
##            decides the question).  LOSS >= 0.80 sigma.  0.70-0.80 is AMBIGUOUS and must be said so.
##   MECHANISM 2018-23 dynamics anomaly vs L27's -119.1 (IMBIE -167.2). Confirms the floor actually
##            fired; it does NOT decide promotion.
##   COST A   AIS hindcast bias at 1900/1950/2018/2025 vs L27 — report either way. ⚠ I predicted this
##            wrong for L32; the prediction is not a criterion.
##   COST B   SSP AIS p05-p95 at 2100/2300 vs L27. A win that is only a wider posterior is NO win.
##   GUARD    the four non-Antarctic components within ~0.02 sigma of L27. If Greenland / glaciers /
##            thermal expansion move, the change did not stay local and the arm is not interpretable.
##   ⚠ NOT A CRITERION: sd_ais sitting on its bound. True BY CONSTRUCTION.
##
## ⛔⛔ THE OPERATIONAL HAZARD IS THE SHARED TARGET FILE, AND IT IS GATED, NOT COMMENTED.
## This arm needs L27's FREDERIKSE target live, while NINE other drivers gate on the IMBIE md5.
## `outputs/recalib_targets_ext.csv` is a SHARED INPUT — the exact class that produced retraction 2
## on 09-23g, where two individually valid files were mutually invalid. So:
##   - the Frederikse target is REBUILT here and gated on md5 070f74ab... (proven 09-23i to be
##     byte-identical to outputs/quarantine/20260921_ais_target_frederikse/);
##   - the IMBIE target is RESTORED BY AN EXIT TRAP, so it comes back even if this script is killed;
##   - the restore is VERIFIED by md5 and screams if it fails.
## ⚠ While this runs, any IMBIE-arm driver will FAIL ITS GATE. That is the SAFE direction (loud, not
## silent) but it means: do not launch an IMBIE arm against this window.
##
## ⚠⚠ WHAT THE TRAP DOES **NOT** COVER, MEASURED 09-24 RATHER THAN ASSUMED. `trap ... EXIT INT TERM`
## fires on a clean exit, on `exit N` (mutation-tested: a wrong expected md5 exits 2 AND restores),
## and on SIGTERM — but bash DEFERS a signal trap until the running FOREGROUND command returns. In
## the mutation test a TERM sent at 06:06:26 did not restore until the stand-in `sleep` ended at
## 06:07:14. So `kill -TERM` on THIS SCRIPT during the ~3 h `wait` will not restore until the chains
## finish, and SIGKILL never restores at all.
##   ⇒ KILL THE CHAINS BY PID (they are listed in the log): `wait` then returns and the trap runs.
##   ⇒ If the target IS left swapped, nothing reads it silently — all nine IMBIE drivers gate on
##     md5 eb768cd9... and refuse to start. Recover with: python python/prep_recalib_targets_ext.py
##
## ⛔ L34's LOGPOST IS NOT COMPARABLE to L27's (a bound + a different sigma scale) NOR to L32's
## (a different target). Compare on hindcast statistics and the channels only.
##
## Everything else is L27's: BASEFLAGS + --no-ledger (50 params), seeds 2026-2029, L27's pooled
## proposal covariance, and `overdispersed_starts_L27r_sdfloor.csv` (L27's own starts with sd_ais at
## floor*1.05, every other column byte-identical — built for L32, correct here unchanged).
## 4 chains in parallel on the Mac, ~2 h 45 m at L31's pace; launched at load 3.19.
## TORCH CONSIDERED AND NOT WARRANTED: every arm L27-L33 ran here and the Julia/Mimi/MimiBRICK stack
## is not provisioned on Torch. Kill by PID (never pkill -f); log = outputs/log_L34.txt.
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
LOG=outputs/log_L34.txt; : > "$LOG"
say(){ echo "[$(date '+%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

MD5_IMBIE=eb768cd96463a3b84721e2bb9a20f009
MD5_FRED=070f74abe11080da7b77a80b67c54033
PREP="python python/prep_recalib_targets_ext.py"

restore_target(){
  say "RESTORING the shared target to the IMBIE build ..."
  ( source ~/climate-env/bin/activate && $PREP ) >> "$LOG" 2>&1
  local m; m=$(md5 -q outputs/recalib_targets_ext.csv)
  if [[ "$m" == "$MD5_IMBIE" ]]; then say "  restored OK ($m)"
  else say "*** RESTORE FAILED: live target is $m, expected $MD5_IMBIE."
       say "*** DO NOT RUN ANY OTHER ARM until this is fixed: python python/prep_recalib_targets_ext.py"; fi
}
trap restore_target EXIT INT TERM

## ---- swap in L27's target, and GATE on it ------------------------------------------------------
[[ "$(md5 -q outputs/recalib_targets_ext.csv)" == "$MD5_IMBIE" ]] \
  || { say "PRE-CONDITION FAILED: the live target is not the IMBIE build; refusing to start"; exit 2; }
say "building L27's Frederikse target (--ais-frederikse) ..."
( source ~/climate-env/bin/activate && $PREP --ais-frederikse ) >> "$LOG" 2>&1
MD5_NOW=$(md5 -q outputs/recalib_targets_ext.csv)
[[ "$MD5_NOW" == "$MD5_FRED" ]] \
  || { say "TARGET GATE FAILED: got $MD5_NOW, expected the L27 Frederikse build $MD5_FRED"; exit 2; }
say "target gate PASSED: $MD5_NOW (= L27's calibration target, byte-identical)"
say "provenance stamp: $(grep -E '^(ais_source|reproduces)' outputs/recalib_targets_ext_provenance.txt | tr '\n' ' ')"

J="julia --project=julia_v2"
NITER=2000000
BASEFLAGS="--gis-ordered --gis-basins2 --amp-mu=1.09 --amp-sigma=0.180 --paleo-priors --no-delta --no-d2-gsic --obs-corr-len=100 --toff-lo=-4 --precip-reparam --cut-fastdyn --fix-gamma"
ARMFLAG="--sd-ais-floor=smb"
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
  for SEED in $SEEDS; do
    say "  seed$SEED: $(tr '\r' '\n' < outputs/mcmc/log_${T}_seed${SEED}.txt | grep -a -m1 'L26 structure flags') | $(tr '\r' '\n' < outputs/mcmc/log_${T}_seed${SEED}.txt | grep -a -m1 'seeding proposal' | cut -c1-90)"
    ## ⚠ THE FLOOR'S VALUE IS READ BACK PER CHAIN, not assumed from the flag string. A dropped or
    ## misspelled flag would otherwise produce an UNFLOORED arm labelled L34 — i.e. a second L27.
    say "    floor: $(tr '\r' '\n' < outputs/mcmc/log_${T}_seed${SEED}.txt | grep -a -m1 'sd_ais FLOOR' | cut -c1-120)"
    tr '\r' '\n' < "outputs/mcmc/log_${T}_seed${SEED}.txt" | grep -aq 'FLOOR DERIVED FROM OBSERVATION' \
      || say "    *** FLOOR GATE FAILED on seed $SEED: sd_ais is NOT floored from the observation ***"
  done
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
  step "$T priors dump" $J --threads=1 julia/calibrate_mcmc_ext.jl 1 2026 --tag=$T $BASEFLAGS --no-ledger $ARMFLAG --dump-priors
  step "$T posterior predictive" $J julia/posterior_predictive_ladrillo.jl --tag=$T
  step "$T ssp components (tap, fixed climate)" $J julia/project_ssps_components_ladrillo.jl --tag=$T
  step "$T DAIS flux split vs IMBIE" $J julia/diag_ais_flux_split_vs_imbie.jl --tag=$T 1000
  source ~/climate-env/bin/activate
  step "$T prior/posterior table" python python/ladrillo_prior_posterior_table.py --tag=$T
}

## ---- L34 ---------------------------------------------------------------------------------------
## ⚠ postprocess runs while the FREDERIKSE target is still live, deliberately: L34's own hindcast
## diagnostics belong against its own training target, exactly as L27's were produced. The bench
## (IMBIE target, L27* ruler) is a SEPARATE run afterwards — run_L34_bench.sh.
run_chains L34 "2026 2027 2028 2029" "$STARTS" adapted_cov_L27_named.csv "$BASEFLAGS --no-ledger $ARMFLAG"
if noise_gate L34 "2026 2027 2028 2029"; then postprocess L34; else say "L34 noise-mode gate FAILED — not postprocessing (investigate, do not --force)"; fi
(( FAILED_STEPS == 0 )) && say "ALLDONE — 0 failed step(s)" \
  || { say "INCOMPLETE — $FAILED_STEPS failed step(s); do not read the outputs as final."; exit 1; }
