#!/bin/bash
## L32 BENCHMARK INPUTS (2026-09-23) — the WHOLE-MODEL comparison against the frozen L27 champion.
##
## ⭐⭐ WHY, AND THE ONE THING THAT MAKES THIS ARM DIFFERENT FROM EVERY PREVIOUS BENCH RUN:
## **L34 WAS FITTED ON THE FREDERIKSE TARGET AND IS SCORED HERE ON THE IMBIE ONE.** That is
## DELIBERATE and it is what makes the comparison fair: it puts L34 in EXACTLY L27's out-of-sample
## position, so L34-vs-L27 is a clean one-axis comparison (the noise floor) with the target held
## fixed on both sides of the ruler. Scoring L34 on its own training target instead would hand it
## the in-sample advantage that 09-23d spent a whole session stripping out of the L32 reading.
##
## ⚠ THEREFORE THE TARGET MUST BE THE **IMBIE** BUILD WHEN THIS RUNS — the opposite of run_L34.sh,
## which needs the Frederikse build live. run_L34.sh restores IMBIE through its EXIT trap; the
## precondition below asserts it rather than trusting that.
##
## THE DECISION THIS FEEDS. PRIMARY, pre-registered 09-24 before any number existed: the
## FULL-PERIOD AIS RMSE against the `L27*` column. **WIN <= 0.70 sigma, LOSS >= 0.80, 0.70-0.80
## AMBIGUOUS and said so.** L27* reads 0.70 and L32 0.88 in the L32 file.
##
## ⭐ WHAT MAKES IT LIKE-FOR-LIKE. `bench_ladrillo.py` reads the LIVE target file and re-scores the
## FROZEN champion snapshot `benchmark/reference/L27/` in the same run, emitting it as the `L27*`
## column. So the comparison inside `bench_ladrillo_L32.md` is on ONE ruler.
## ⚠ `outputs/bench_ladrillo_L27.md` is NOT that ruler — it was written 09-21 09:24, BEFORE the
## target was rebuilt onto IMBIE 2026 at 13:12, and its BRICK 2.0 AIS RMSE (1.5740) differs from
## every later file's (1.4766) with nothing about BRICK having changed. **Read the `L27*` column
## inside the L32 file, never the standalone L27 bench.**
##
## ⚠ THE BENCHMARK SCORES SSPs ONLY; the paper's figures are van Vuuren. A pass here is therefore
## necessary and NOT sufficient for promotion, and this script deliberately stops short of the van
## Vuuren campaign and the figures.
##
## ⚠ RUN SEQUENTIALLY, ON PURPOSE. The three fair-uncertainty arms are independent and would
## normally go in parallel, but this machine is shared and carried heavy contention
## at launch. Sequential adds ONE process rather than three. It is slower for us and kinder to the
## other job; that is the intended trade (eta_in_days_is_not_a_slow_run: read the meter, do not
## assume).
##
## champions.json is UNTOUCHED. Nothing here promotes anything.
##   bash run_L34_bench.sh        log = outputs/log_L34_bench.txt
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T=L34
LOG=outputs/log_L34_bench.txt; : > "$LOG"
J="julia --project=julia_v2"
say(){ echo "[$(date '+%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }
## ⛔ FAILURES ARE COUNTED, NOT JUST PRINTED. The repo's inherited step() printed "FAILED ... —
## continuing" and the driver then said ALLDONE regardless, so a run with two dead stages looked
## exactly like a clean one (flagged by another session, 09-23: "both FAILED at 16:08:07 and the
## driver still printed ALLDONE"). ALLDONE now means ALL DONE.
FAILED_STEPS=0
step(){ local nm="$1"; shift; say "START  $nm"
  if "$@" >> "$LOG" 2>&1; then say "OK     $nm"; else say "FAILED $nm (rc=$?)"; FAILED_STEPS=$((FAILED_STEPS+1)); fi; }

## preconditions, asserted rather than assumed
grep -qa "OK     L34 ssp components" outputs/log_L34.txt || { say "run_L34.sh did not complete; STOP"; exit 1; }
[[ "$(md5 -q outputs/recalib_targets_ext.csv)" == "eb768cd96463a3b84721e2bb9a20f009" ]] || { say "target is not the IMBIE build; STOP"; exit 2; }
[[ -d benchmark/reference/L27 ]] || { say "frozen L27 champion snapshot missing — the L27* column could not be produced; STOP"; exit 3; }
say "$T benchmark inputs | commit $(git rev-parse --short HEAD) | load $(uptime | sed 's/.*load averages*: //')"

for s in ssp126 ssp245 ssp585; do
  step "fair-uncertainty joint band $s" $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s --tap
done
## ⚠ REQUIRED BY ladrillo_model_comparison.py AND EASY TO MISS: it needs the UNTAPPED SSP
## deliverable (outputs/ssps_components_2300_<TAG>.csv). run_L28_stage2.sh has this step; the first
## version of this script omitted it and the model comparison died with rc=1.
step "ssp components (no-tap)" $J julia/project_ssps_components_ladrillo.jl 2000 --tag=$T --no-tap
source ~/climate-env/bin/activate
step "model comparison" python python/ladrillo_model_comparison.py --tag=$T
step "benchmark"        python python/bench_ladrillo.py --tag=$T
step "IMBIE 2026 vs targets/hindcast" python python/diag_imbie2026_vs_targets.py --tag=$T

## ⛔ THE PATTERNS ARE GLOBS, BECAUSE THE PRODUCTS CARRY A TAP SUFFIX.
## The first version of this check spelled the draws files WITHOUT `_tap4p69K_V5p64m_tau800`,
## taken from an error message rather than a product listing, so it reported MISSING for three
## files that existed — and would have done so forever, on every future run, regardless of success
## (flagged by another session, 09-23). A check that cannot pass is worse than no check: it trains
## the reader to ignore it. Verified by MUTATION below.
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

## ⭐ ALLDONE IS EARNED, NOT PRINTED. Exit non-zero so a caller (or a later reader of the log)
## cannot mistake a partial run for a complete one.
if (( FAILED_STEPS == 0 && MISSING_INPUTS == 0 )); then
  say "ALLDONE — $FAILED_STEPS failed step(s), $MISSING_INPUTS missing input(s)"
else
  say "INCOMPLETE — $FAILED_STEPS failed step(s), $MISSING_INPUTS missing input(s). DO NOT read the bench as final."
  exit 1
fi
