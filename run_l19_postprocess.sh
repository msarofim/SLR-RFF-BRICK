#!/bin/bash
## L19 POST-CHAIN DRIVER — DIAGNOSTIC ONLY. Blocks until the chains finish, then runs the
## analyses that answer the registered prediction. Launch any time.
##
## ⚠⚠ THIS IS DELIBERATELY *NOT* THE L18 PIPELINE. No postprocess_mcmc_ext.jl, no subsample,
## no projections, no benchmark. If the barrier is real the four chains will NOT mix, and a
## non-mixing ensemble is NOT a posterior: pooling it into a subsample would manufacture a
## multi-modal "uncertainty" that is really four separate answers, and every downstream
## number would inherit it. champions.json is not touched under ANY outcome.
##
## Run the full pipeline ONLY if branch (A) fires (all four chains migrate to MID) — then the
## ensemble IS a single posterior and `bash run_l18_postprocess.sh`-style processing applies.
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T=L19
LOG=outputs/log_l19_postprocess_driver.txt
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }
step(){ local nm="$1"; shift; say "START  $nm"
  if "$@" >> "$LOG" 2>&1; then say "OK     $nm"; else say "FAILED $nm (rc=$?) — continuing"; fi; }

: > "$LOG"
say "waiting for the L19 chains..."
while pgrep -f "tag=$T" > /dev/null; do sleep 60; done
say "chains done."

say "=== ARM VERIFICATION (stdout only flushes at exit) ==="
for s in 2026 2027 2028 2029; do
  say "  seed$s: $(tr '\r' '\n' < outputs/mcmc/log_${T}_seed${s}.txt | grep -E 'A6 prior|starts file|logpost' | tr '\n' ' ')"
done
say "  EXPECT amp ~ N(0.950, 0.100); starts file ..._ton.csv; FOUR DIFFERENT logpost values."
say "  ⚠ [MAP start] will NOT match L14's -642.84 — commit 893bfaa moved lws and"
say "  dang_closure_sig AFTER L14 ran. That is WHY seed 2029 is an in-arm MID control."

step "band occupancy per chain — DID CHAINS MOVE?" bash scripts/ton_band_by_chain.sh $T
step "per-band EQUILIBRATED log-posterior (the key measurement)" bash scripts/ton_band_logpost.sh $T
step "excursion structure" bash scripts/ton_transition_rates.sh $T
step "escape scale vs the driftless null (2.0x)" bash scripts/ton_escape_scale.sh $T
step "SLR convergence across chains (R-hat expected BAD if they did not mix)" \
     julia --project=julia_v2 julia/diag_slr_convergence_by_chain_ladrillo.jl --tag=$T

say "=== RESOLVE THE REGISTERED PREDICTION (run_mcmc_L19.sh header) ==="
say "  (A) all four migrate to MID          -> champion CONFIRMED, caveat can be dropped"
say "  (B) chains STAY in their start bands -> L14's 100% MID is START-DETERMINED (expected)"
say "  (C) MID control (seed 2029) LEAVES   -> MID not favoured under the CURRENT targets"
say "  ⚠ the log-posterior table is mean log-DENSITY, not posterior MASS. A narrow tall mode"
say "  can beat a broad one on density and lose on mass. Do not call a band 'more probable'."
say "  ⚠ check the drift column first — a chain that has not equilibrated has no usable mean."
