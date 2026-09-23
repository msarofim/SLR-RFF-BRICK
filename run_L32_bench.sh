#!/bin/bash
## L32 BENCHMARK INPUTS (2026-09-23) — the WHOLE-MODEL comparison against the frozen L27 champion.
##
## WHY. L32 beats L27 on both ANTARCTIC channels (level z −1.45 vs −2.63; 2018–23 dynamics anomaly
## −133.1 vs −119.1) and reproduces its projections, but the Antarctic is ONE of FIVE components and
## `bench_ladrillo.py` is the only like-for-like scorer across all of them. It refused to run for
## L32 for want of four inputs — `ladrillo_model_comparison_L32.csv` and the three
## `scope_slr_fairunc_draws_ssp{126,245,585}_spliced_L32.csv`. This generates exactly those, then
## benchmarks. ⛔ Everything so far about L32's non-Antarctic components is TRANSITIVE INFERENCE
## (L32 within 0.008 cm of L28 on the guard; L28 within 0.02σ of L27 in its own bench) — this
## replaces that inference with a measurement, which is the point.
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
## normally go in parallel, but this machine is shared and carried load ~51 with a 12-process R job
## at launch. Sequential adds ONE process rather than three. It is slower for us and kinder to the
## other job; that is the intended trade (eta_in_days_is_not_a_slow_run: read the meter, do not
## assume).
##
## champions.json is UNTOUCHED. Nothing here promotes anything.
##   bash run_L32_bench.sh        log = outputs/log_L32_bench.txt
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T=L32
LOG=outputs/log_L32_bench.txt; : > "$LOG"
J="julia --project=julia_v2"
say(){ echo "[$(date '+%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }
step(){ local nm="$1"; shift; say "START  $nm"
  if "$@" >> "$LOG" 2>&1; then say "OK     $nm"; else say "FAILED $nm (rc=$?)"; fi; }

## preconditions, asserted rather than assumed
grep -qa "OK     L32 ssp components" outputs/log_L32.txt || { say "run_L32.sh did not complete; STOP"; exit 1; }
[[ "$(md5 -q outputs/recalib_targets_ext.csv)" == "eb768cd96463a3b84721e2bb9a20f009" ]] || { say "target is not the IMBIE build; STOP"; exit 2; }
[[ -d benchmark/reference/L27 ]] || { say "frozen L27 champion snapshot missing — the L27* column could not be produced; STOP"; exit 3; }
say "$T benchmark inputs | commit $(git rev-parse --short HEAD) | load $(uptime | sed 's/.*load averages*: //')"

for s in ssp126 ssp245 ssp585; do
  step "fair-uncertainty joint band $s" $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s --tap
done
source ~/climate-env/bin/activate
step "model comparison" python python/ladrillo_model_comparison.py --tag=$T
step "benchmark"        python python/bench_ladrillo.py --tag=$T
step "IMBIE 2026 vs targets/hindcast" python python/diag_imbie2026_vs_targets.py --tag=$T

## the four inputs bench_ladrillo.py named, verified to EXIST rather than inferred from exit codes
say "INPUT CHECK:"
for f in outputs/ladrillo_model_comparison_$T.csv \
         outputs/scope_slr_fairunc_draws_ssp126_spliced_$T.csv \
         outputs/scope_slr_fairunc_draws_ssp245_spliced_$T.csv \
         outputs/scope_slr_fairunc_draws_ssp585_spliced_$T.csv \
         outputs/bench_ladrillo_$T.md; do
  [[ -s "$f" ]] && say "  OK      $f" || say "  MISSING $f"
done
say "ALLDONE"
