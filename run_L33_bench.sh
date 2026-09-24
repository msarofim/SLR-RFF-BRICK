#!/bin/bash
## L33 BENCHMARK INPUTS (2026-09-24) — closing the one untested cell of the option arc.
##
## WHY. L33 = L32's target and mechanism with the floor re-derived against the IMBIE 2021 vintage
## (`--sd-ais-floor=smb2021`, 0.02139 cm, a 34 % cut from L32's 0.03259). It has a BETTER
## cumulative level than L32 (z -1.21 vs -1.45) for a slightly smaller dynamics gain (-126.2 vs
## -133.1), and it has NEVER been benchmarked — it is the only arm in the L28-L34 option ladder
## with no whole-model score. If the IMBIE-side arm is adopted, L33 may be the better
## representative of it, and the L27-vs-L32 memo currently names an untested cell.
##
## ⚠⚠ THIS IS NOT THE L34 SITUATION AND THE HEADER MUST NOT BE COPIED FROM IT.
## L34 was FREDERIKSE-fitted and scored on IMBIE, which put it out-of-sample and was the whole
## point of that run. **L33 is IMBIE-FITTED and is scored on IMBIE**, so it is IN-SAMPLE here,
## exactly as L28/L29/L30/L32 are. That is the like-for-like comparison against those arms, and it
## is NOT like-for-like against L27, which is Frederikse-fitted. bench_ladrillo.py prints a
## divergence banner naming this asymmetry; read it at the gate.
##
## ⭐ THE RULER. Since 2026-09-24 bench_ladrillo.py takes the hindcast observations from the TARGET
## FILE, not from the candidate's own postpred, and stamps the file and its md5 into the report.
## Before that fix the arm under test supplied its own ruler, so L27's bench was silently scored on
## Frederikse while L28-L33's were on IMBIE. The `L27*` column re-scores the FROZEN
## benchmark/reference/L27/ snapshot in this same run, on this same ruler — that column is the only
## valid champion reference; never outputs/bench_ladrillo_L27.md as a standalone.
## For scale on the current ruler: L27* 0.70, L34 0.73, L32 0.88, L29 1.45, L28 1.53, L30 1.53.
##
## ⚠ NO PRE-REGISTERED THRESHOLD APPLIES TO L33. The 0.70/0.80 WIN/LOSS band was registered for
## L34, a different question (does the noise fix alone improve the champion?). L33 asks which of
## two IMBIE-side arms better represents that family. Report the numbers; do not import L34's gate.
##
## ⚠ THE BENCHMARK SCORES SSPs ONLY; the paper's figures are van Vuuren. A pass here is necessary
## and NOT sufficient for promotion, and this script stops short of the van Vuuren campaign.
##
## ⚠ RUN SEQUENTIALLY, ON PURPOSE — shared machine (eta_in_days_is_not_a_slow_run).
##
## champions.json is UNTOUCHED. Nothing here promotes anything.
##   bash run_L33_bench.sh        log = outputs/log_L33_bench.txt
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T=L33
LOG=outputs/log_L33_bench.txt; : > "$LOG"
J="julia --project=julia_v2"
say(){ echo "[$(date '+%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }
## ⛔ FAILURES ARE COUNTED, NOT JUST PRINTED (the 09-23 "ALLDONE after two FAILEDs" incident).
FAILED_STEPS=0
step(){ local nm="$1"; shift; say "START  $nm"
  if "$@" >> "$LOG" 2>&1; then say "OK     $nm"; else say "FAILED $nm (rc=$?)"; FAILED_STEPS=$((FAILED_STEPS+1)); fi; }

## preconditions, asserted rather than assumed
grep -qa "OK     $T ssp components" outputs/log_$T.txt || { say "run_$T.sh did not complete; STOP"; exit 1; }
[[ "$(md5 -q outputs/recalib_targets_ext.csv)" == "eb768cd96463a3b84721e2bb9a20f009" ]] || { say "target is not the IMBIE build; STOP"; exit 2; }
[[ -d benchmark/reference/L27 ]] || { say "frozen L27 champion snapshot missing — the L27* column could not be produced; STOP"; exit 3; }
grep -qa -- "--sd-ais-floor=smb2021" outputs/log_$T.txt || { say "$T is not the 2021-vintage-floor arm; STOP"; exit 4; }
say "$T benchmark inputs | commit $(git rev-parse --short HEAD) | load $(uptime | sed 's/.*load averages*: //')"

for s in ssp126 ssp245 ssp585; do
  step "fair-uncertainty joint band $s" $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s --tap
done
## ⚠ REQUIRED BY ladrillo_model_comparison.py AND EASY TO MISS: the UNTAPPED SSP deliverable.
step "ssp components (no-tap)" $J julia/project_ssps_components_ladrillo.jl 2000 --tag=$T --no-tap
source ~/climate-env/bin/activate
step "model comparison" python python/ladrillo_model_comparison.py --tag=$T
step "benchmark"        python python/bench_ladrillo.py --tag=$T
step "IMBIE 2026 vs targets/hindcast" python python/diag_imbie2026_vs_targets.py --tag=$T

## ⛔ PATTERNS ARE GLOBS — the products carry a tap suffix. A check that cannot pass is worse than
## no check; these were mutation-tested when run_L34_bench.sh was written.
say "INPUT CHECK:"
MISSING_INPUTS=0
check(){ local pat="$1"; local hit
  hit=$(ls -1 $pat 2>/dev/null | head -1)
  if [[ -n "$hit" && -s "$hit" ]]; then say "  OK      $hit"
  else say "  MISSING $pat"; MISSING_INPUTS=$((MISSING_INPUTS+1)); fi; }
check "outputs/ladrillo_model_comparison_$T.csv"
for s in ssp126 ssp245 ssp585; do
  check "outputs/scope_slr_fairunc_draws_${s}_spliced_${T}*.csv"
done
check "outputs/bench_ladrillo_$T.md"

## ⭐ ALLDONE IS EARNED, NOT PRINTED.
if (( FAILED_STEPS == 0 && MISSING_INPUTS == 0 )); then
  say "ALLDONE — $FAILED_STEPS failed step(s), $MISSING_INPUTS missing input(s)"
else
  say "INCOMPLETE — $FAILED_STEPS failed step(s), $MISSING_INPUTS missing input(s). DO NOT read the bench as final."
  exit 1
fi
