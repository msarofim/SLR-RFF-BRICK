#!/bin/bash
## POSTPROCESS for any tag (generalised 2026-09-21 from run_l27_postprocess.sh; TAG=<T> CTRL=<control> SEEDS="2026 2027 2028 2029" FLAGS="..."): waits for the tag's chains, then the postprocess chain of steps. CONTROL = L26 (one axis: the A/C/D reduction).
## CONTROL = L24. ⚠ NOT a one-axis comparison: L26 changes priors (paleo), structure (no delta, no glacier d2,
## correlated bands L=100, precip reparam) and a bound (T_off -4) at once. The single-chain arms L26a/b/c/d
## isolate the error-model axis; nothing isolates the prior axis yet. Read bench_ladrillo_L26 vs _L24 with that
## in mind. champions.json STAYS UNTOUCHED — promotion is Marcus's call.
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T="${TAG:-L27}"
CTRL="${CTRL:-L26}"
SEEDS="${SEEDS:-2026 2027 2028 2029}"
## the production flags of the tag (the prior dump must be run with the SAME flags as its chains)
FLAGS="${FLAGS:---gis-ordered --gis-basins2 --amp-mu=1.09 --amp-sigma=0.180 --paleo-priors --no-delta --no-d2-gsic --obs-corr-len=100 --toff-lo=-4 --precip-reparam --cut-fastdyn --fix-gamma --no-ledger}"
LOG=outputs/log_$(echo "$T" | tr "[:upper:]" "[:lower:]")_postprocess_driver.txt
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
for SEED in $SEEDS; do
  say "  seed$SEED: $(tr '\r' '\n' < outputs/mcmc/log_${T}_seed${SEED}.txt | grep -a -m1 'L26 structure flags') | $(tr '\r' '\n' < outputs/mcmc/log_${T}_seed${SEED}.txt | grep -a -m1 'MCMC:' | cut -c1-60)"
done
say "  EXPECT the banner to match FLAGS=$FLAGS. If not — STOP."
ls -la outputs/mcmc/chain_${T}_seed*.csv >> "$LOG" 2>&1
say "=== NOISE-MODE GATE: 2nd-half median sd_gis must be < 0.10 cm in every chain (the L27tune chain from the MAP start sat at 0.6-1.0) ==="
source ~/climate-env/bin/activate
python - "$T" $SEEDS >> "$LOG" 2>&1 <<'PY'
import sys, pandas as pd
t = sys.argv[1]; bad = []
for s in sys.argv[2:]:
    d = pd.read_csv(f"outputs/mcmc/chain_{t}_seed{s}_n2000000.csv", usecols=["sd_gis", "sd_ais", "log_post"]); d = d.iloc[len(d)//2:]
    m = d.sd_gis.median(); print(f"  seed{s}: sd_gis median {m:.4f}  sd_ais {d.sd_ais.median():.4f}  log_post {d.log_post.median():.1f}  {'OK' if m < 0.10 else '*** NOISE MODE — STOP ***'}")
    if m >= 0.10: bad.append(s)
print("NOISE-MODE GATE:", "PASS" if not bad else f"FAIL on seeds {bad}")
PY
grep -q "NOISE-MODE GATE: PASS" "$LOG" || { say "noise-mode gate FAILED — not postprocessing"; exit 1; }
step "slr convergence diag (REQUIRED before postprocess)" $J julia/diag_slr_convergence_by_chain_ladrillo.jl --tag=$T
step "postprocess (writes the subsample; ~50 min — DO NOT KILL)" $J julia/postprocess_mcmc_ext.jl --tag=$T --accept-slr
step "prior dump for the appendix" $J julia/calibrate_mcmc_ext.jl 100 2026 --tag=$T $FLAGS --dump-priors
step "posterior predictive" $J julia/posterior_predictive_ladrillo.jl --tag=$T
step "ssp components (tap)" $J julia/project_ssps_components_ladrillo.jl --tag=$T
step "ssp components (no-tap)" $J julia/project_ssps_components_ladrillo.jl --tag=$T --no-tap
for s in ssp126 ssp245 ssp585; do
  step "fair-uncertainty joint band $s" $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s --tap
done
source ~/climate-env/bin/activate
step "model comparison" python python/ladrillo_model_comparison.py --tag=$T
step "benchmark"        python python/bench_ladrillo.py --tag=$T
step "prior/posterior table" python python/ladrillo_prior_posterior_table.py --tag=$T
say "=== DONE. bench_ladrillo_${T}.md vs _${CTRL}.md; the AIS block's R̂ in the postprocess log; Table A1 needs the prior/posterior table rebuilt with --tag=$T (ladrillo_prior_posterior_table.py needs its BLOCKS/DESC updated for ais_precip_u and the three dropped parameters). ==="
