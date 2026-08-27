#!/bin/bash
## L18 OVERNIGHT POST-CHAIN DRIVER — waits for the chains, then runs -26b §6 end to end.
##
## Launch this any time; it BLOCKS until no `tag=L18` julia process remains, so it can be
## started while the chains are still running.  bash run_l20_postprocess.sh
##
## ⚠ ORDER: diag_slr_convergence FIRST, then postprocess --accept-slr. Handoff -26b §6 and
## -26c §1 both say so, and the CODE agrees: diag_slr_convergence_by_chain_ladrillo.jl reads
## the RAW CHAINS (chain_<TAG>_seed<sd>_n<N>.csv), not the subsample, so it does NOT need a
## postprocess pass first. The tail of julia/run_l14_production.sh prescribes the OTHER order
## ("postprocess, then diag, then postprocess --accept-slr") — that would burn an extra 2-3 h
## pass for nothing. Verified 2026-08-26 by reading the diag script's inputs.
##
## ⚠ postprocess_mcmc_ext.jl REFUSES to write when marginals fail unless
## outputs/mcmc/slr_convergence_L18.csv exists AND --accept-slr is passed. That gate is why
## the diag must precede it. It is a DOCUMENTED gate, not a failure.
##
## ⚠ BUDGET 2-3 h FOR postprocess ALONE and DO NOT KILL IT (-26b §5). It took 2h11m for L17
## vs <=51 min for L16 on identical data — the ess(arr; maxlag=200_000) loop over ~59 params
## holds ~1.9 GB, and on a swap-bound Mac that reads as compute-bound. The machine was rebooted
## before this run (swap 0), so expect the FAST end.
##
## ⚠ BLAS PINNED on every julia call (pin_blas_threads): 4.8x on this M4.
## ⚠ The python steps NEED the venv — bare python3 has no numpy (-26b §5).
## ⚠ The full-chain sweeps (ton_*) run only AFTER the chains are done, never alongside them
## (`eta_in_days_is_not_a_slow_run`): they read 2.2 GB x N files and starve the samplers.
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T=L20
LOG=outputs/log_l20_postprocess_driver.txt
J="julia --project=julia_v2"
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }
step(){ # step <name> <cmd...>
  local nm="$1"; shift
  say "START  $nm"
  if "$@" >> "$LOG" 2>&1; then say "OK     $nm"; else say "FAILED $nm (rc=$?) — continuing to the next independent step"; fi
}

: > "$LOG"
say "waiting for the L20 chains to finish..."
while pgrep -f "tag=$T" > /dev/null; do sleep 60; done
say "chains done."

# ---- VERIFY THE ARM BEFORE TRUSTING ANYTHING (-26c §2). stdout only flushes at exit, so
# ---- these two lines are readable now and were NOT while the chains ran.
say "=== ARM VERIFICATION ==="
for s in 2026 2027 2028 2029; do
  say "  seed$s: $(tr '\r' '\n' < outputs/mcmc/log_${T}_seed${s}.txt | grep -E 'A6 prior|logpost' | tr '\n' ' ')"
done
say "  EXPECT amp ~ N(1.090, 0.100) on [0.790, 1.390]; four DISTINCT starts ~ +221..+230;"
say "  EXPECT [MAP start = -643.92] — which equals L15's, so L20 IS option B (L15's prior)"
say "  re-run with GOOD starts. If it differs, STOP."
ls -la outputs/mcmc/chain_${T}_seed*.csv >> "$LOG" 2>&1

step "slr convergence diag (REQUIRED before postprocess)" \
     $J julia/diag_slr_convergence_by_chain_ladrillo.jl --tag=$T
step "postprocess (2-3 h — DO NOT KILL)" \
     $J julia/postprocess_mcmc_ext.jl --tag=$T --accept-slr
step "T_on band occupancy per chain" \
     bash scripts/ton_band_by_chain.sh $T
step "T_on excursion structure" \
     bash scripts/ton_transition_rates.sh $T
step "T_on band hindcast vs L14" \
     $J julia/scope_ais_ton_band_hindcast.jl 2000 --tags=L14,$T
step "posterior predictive" \
     $J julia/posterior_predictive_ladrillo.jl --tag=$T
step "ssp components (tap)" \
     $J julia/project_ssps_components_ladrillo.jl --tag=$T
step "ssp components (no-tap)" \
     $J julia/project_ssps_components_ladrillo.jl --tag=$T --no-tap
for s in ssp126 ssp245 ssp585; do
  step "fair-uncertainty joint band $s" \
       $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s
done

say "=== python steps (venv) ==="
source ~/climate-env/bin/activate
step "model comparison" python python/ladrillo_model_comparison.py --tag=$T
step "benchmark"        python python/bench_ladrillo.py --tag=$T

# ---- the sweep still OWED from -26c §3, now safe to run: no sampler to starve.
step "escape scale L15/L16/L17/L18 (the owed test; driftless-walk null = 2.0x)" \
     bash scripts/ton_escape_scale.sh L15 L16 L17 $T

say "=== DONE. READ IN THIS ORDER ==="
say "  1. the ARM VERIFICATION block above (MAP must be -644.51)"
say "  2. RESOLVE THE REGISTERED PREDICTION (run_mcmc_L18.sh header) BEFORE anything else:"
say "     AIS median_vs_lit ssp245 @2100/@2150/@2300 in outputs/scope_slr_fairunc_cells_ssp245_spliced_${T}.csv"
say "       band: does AIS ssp126@2100 p05-p95 come back near L14's 6.91 cm (vs L18's 47.81)?"
say "       median: if it tracks L18's, centre and sigma are SEPARABLE and choosable independently"
say "  3. outputs/bench_ladrillo_${T}.md  — and champions.json stays UNTOUCHED without Marcus"
say "  4. ⚠ sd(medians)/mean(within-chain sd) @2100, NOT just R-hat (-26b §1: L17 'passed' at"
say "     0.142, the worst of four arms). Never quote an arm as converged on R-hat alone."
