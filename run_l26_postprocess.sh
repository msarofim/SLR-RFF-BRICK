#!/bin/bash
## L26 POSTPROCESS (2026-09-19): waits for the four L26 chains, then the L24 postprocess chain of steps.
## CONTROL = L24. ⚠ NOT a one-axis comparison: L26 changes priors (paleo), structure (no delta, no glacier d2,
## correlated bands L=100, precip reparam) and a bound (T_off -4) at once. The single-chain arms L26a/b/c/d
## isolate the error-model axis; nothing isolates the prior axis yet. Read bench_ladrillo_L26 vs _L24 with that
## in mind. champions.json STAYS UNTOUCHED — promotion is Marcus's call.
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T=L26
CTRL=L24
LOG=outputs/log_l26_postprocess_driver.txt
J="julia --project=julia_v2"
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }
step(){ local nm="$1"; shift
  say "START  $nm"
  if "$@" >> "$LOG" 2>&1; then say "OK     $nm"; else say "FAILED $nm (rc=$?) — continuing to the next independent step"; fi
}
: > "$LOG"
say "waiting for the $T chains (pgrep on the interpreter+tag, never the bare script name)..."
while pgrep -f "calibrate_mcmc_ext.jl [0-9]* [0-9]* --tag=$T " > /dev/null; do sleep 60; done
say "chains done."
say "=== ARM VERIFICATION (each chain's own banner) ==="
for SEED in 2026 2027 2028 2029; do
  say "  seed$SEED: $(tr '\r' '\n' < outputs/mcmc/log_${T}_seed${SEED}.txt | grep -a -m1 'L26 structure flags') | $(tr '\r' '\n' < outputs/mcmc/log_${T}_seed${SEED}.txt | grep -a -m1 'MCMC:' | cut -c1-60)"
done
say "  EXPECT paleo-priors=true no-delta=true no-d2-gsic=true obs-corr-len=100.0 precip-reparam=true; 55 free params. If not — STOP."
ls -la outputs/mcmc/chain_${T}_seed*.csv >> "$LOG" 2>&1
step "slr convergence diag (REQUIRED before postprocess)" $J julia/diag_slr_convergence_by_chain_ladrillo.jl --tag=$T
step "postprocess (writes the subsample; ~50 min — DO NOT KILL)" $J julia/postprocess_mcmc_ext.jl --tag=$T --accept-slr
step "prior dump for the appendix" $J julia/calibrate_mcmc_ext.jl 100 2026 --tag=$T --gis-ordered --gis-basins2 --amp-mu=1.09 --amp-sigma=0.180 --paleo-priors --no-delta --no-d2-gsic --obs-corr-len=100 --toff-lo=-4 --precip-reparam --dump-priors
step "posterior predictive" $J julia/posterior_predictive_ladrillo.jl --tag=$T
step "ssp components (tap)" $J julia/project_ssps_components_ladrillo.jl --tag=$T
for s in ssp126 ssp245 ssp585; do
  step "fair-uncertainty joint band $s" $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s --tap
done
source ~/climate-env/bin/activate
step "model comparison" python python/ladrillo_model_comparison.py --tag=$T
step "benchmark"        python python/bench_ladrillo.py --tag=$T
say "=== DONE. bench_ladrillo_${T}.md vs _${CTRL}.md; the AIS block's R̂ in the postprocess log; Table A1 needs the prior/posterior table rebuilt with --tag=$T (ladrillo_prior_posterior_table.py needs its BLOCKS/DESC updated for ais_precip_u and the three dropped parameters). ==="
