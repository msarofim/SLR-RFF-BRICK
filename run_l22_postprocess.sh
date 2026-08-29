#!/bin/bash
## L22 POST-CHAIN DRIVER — copy of run_l21_postprocess.sh retargeted to the steric-cap arm.
## Blocks until no `tag=L22` julia process remains, so launch it any time.
##
##   bash run_l22_postprocess.sh
##
## ⚠ WHAT IS DIFFERENT FROM THE L21 COPY, AND IT IS ONLY THE TARGETS:
##   * T=L22, its own driver log.
##   * every cross-arm comparison points at L21, not L14/L18 — L22 changes exactly one thing
##     about L21 (the steric AR(1) marginal cap) so L21 is the control.
##   * the arm verification expects the CAP LINE and the START-REPAIR LINES.
##
## ⚠ THE HEADER LINES ARE NOT MISSING FROM THE RUN LOGS. Julia's stdout only flushes at
## process exit, and ProgressMeter owns the terminal until then, so `log_L22_seed*.txt` looks
## like nothing but a progress bar WHILE THE CHAINS RUN. The header appears when they finish.
## Do not "fix" this and do not conclude the flags did not take — `ps` showed all four chains
## carrying --steric-marg-cap=modern at launch.
##
## EXPECTED IN THE ARM VERIFICATION (measured on the 4000-iter smoke, seed 2026):
##   * "MARGINAL σ/sqrt(1-ρ²) CAPPED at 0.1036 cm (1993-2025 mean ε)"
##   * TWO "steric start repaired" lines per chain: the default θ0 (marginal 1.155 -> 0.0518)
##     and the --overdisperse row (0.187-0.234 -> 0.0518). If they are ABSENT the cap did not
##     take and the whole arm is L21 re-run under a different name — STOP.
##   * [MAP start] = -675.78, DIFFERENT from L21's -650.59. Equal to L21's => the cap is inert.
##   * over-dispersed starts ~ +190 (L21: +217..+224); the ~29 log-unit drop IS the cap.
##
## ⚠ BUDGET 2-3 h FOR postprocess ALONE AND DO NOT KILL IT. ⚠ BLAS PINNED. ⚠ python steps
## need the venv. ⚠ The full-chain sweeps run only after the chains are done.
##
## ⚠ THIS PROMOTES NOTHING. L21 is champion; champions.json is untouched. L22 is a DIAGNOSTIC.
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T=L22
CTRL=L21                       # the control arm: L22 changes ONE thing about it
MAP_EXPECT=-675.78              # [MAP start] under the cap (smoke, seed 2026)
MAP_CTRL=-650.59                # the control's, which it must NOT equal
CAP_EXPECT="0.1036"             # the marginal bound, cm
LOG=outputs/log_l22_postprocess_driver.txt
J="julia --project=julia_v2"
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }
step(){ # step <name> <cmd...>
  local nm="$1"; shift
  say "START  $nm"
  if "$@" >> "$LOG" 2>&1; then say "OK     $nm"; else say "FAILED $nm (rc=$?) — continuing to the next independent step"; fi
}

: > "$LOG"
say "waiting for the $T chains to finish..."
while pgrep -f "tag=$T" > /dev/null; do sleep 60; done
say "chains done."

# ---- VERIFY THE ARM BEFORE TRUSTING ANYTHING (-26c §2). stdout only flushes at exit, so
# ---- these two lines are readable now and were NOT while the chains ran.
say "=== ARM VERIFICATION ==="
for s in 2026 2027 2028 2029; do
  say "  seed$s: $(tr '\r' '\n' < outputs/mcmc/log_${T}_seed${s}.txt | grep -E 'A6 prior|logpost|CAPPED|start repaired' | tr '\n' ' ')"
done
say "  EXPECT amp ~ N(0.950, 0.100); four DISTINCT over-dispersed starts ~ +190"
say "  EXPECT the cap line: MARGINAL ... CAPPED at $CAP_EXPECT cm, and TWO 'start repaired'"
say "         lines per chain (the default theta0 and the --overdisperse row)."
say "  EXPECT [MAP start = $MAP_EXPECT] — DIFFERENT from $CTRL's $MAP_CTRL, which is how we"
say "         know the cap took. If it EQUALS $MAP_CTRL the flag was inert: STOP."
ls -la outputs/mcmc/chain_${T}_seed*.csv >> "$LOG" 2>&1

step "slr convergence diag (REQUIRED before postprocess)" \
     $J julia/diag_slr_convergence_by_chain_ladrillo.jl --tag=$T
step "postprocess (2-3 h — DO NOT KILL)" \
     $J julia/postprocess_mcmc_ext.jl --tag=$T --accept-slr
step "T_on band occupancy per chain" \
     bash scripts/ton_band_by_chain.sh $T
step "T_on excursion structure" \
     bash scripts/ton_transition_rates.sh $T
step "T_on band hindcast vs $CTRL" \
     $J julia/scope_ais_ton_band_hindcast.jl 2000 --tags=$CTRL,$T
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
step "escape scale vs the control arm" \
     bash scripts/ton_escape_scale.sh $CTRL $T

step "$CTRL-vs-$T: where did the TE residual go" \
     python python/diag_l21_vs_l22_steric_cap.py

say "=== DONE. READ IN THIS ORDER ==="
say "  1. the ARM VERIFICATION block above — the cap line and BOTH start-repair lines must be"
say "     present and [MAP start] must be $MAP_EXPECT, not $CTRL's $MAP_CTRL. If not, inert."
say "  2. python/diag_l21_vs_l22_steric_cap.py output — it resolves the four predictions"
say "     registered in run_mcmc_L22.sh. The one that decides the next step:"
say "       COLLAPSE toward ~2 sigma => the 17 sigma was the NOISE MODEL, and the depth split"
say "                                   becomes a question about the PROJECTION, not the fit."
say "       STAYS LARGE            => something else holds TE up; the depth split is live."
say "     ⚠ CHECK d2_steric_1/_2 BEFORE CALLING IT: the D2 basis is 1/eps^2-weighted with"
say "       prior sd 0.5 cm, FIVE TIMES the cap, so the misfit can be bought off THERE instead."
say "  3. outputs/bench_ladrillo_${T}.md — expect SOME axis to look worse. That is the cap"
say "     working, not a regression. Report what moved."
say "  4. sd(medians)/mean(within-chain sd) @2100, not just R-hat."
say "  5. ⚠ champions.json STAYS UNTOUCHED. Promotion is Marcus's call and this is a"
say "     diagnostic arm, not a champion candidate."
