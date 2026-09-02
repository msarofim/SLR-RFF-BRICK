#!/bin/bash
## L24 POST-CHAIN DRIVER — the SHIPPED-PRIOR arm. Adapted from run_l22_postprocess.sh.
##
##   bash run_l24_postprocess.sh
##
## WHY L24 MATTERS (2026-09-01). HEAD's production prior is N(1.09, 0.180) (`165a860`).
## NO SCORED VINTAGE USES IT: L21/L22 are N(0.95, 0.10) — a superseded centre AND width —
## and L23/L23b/L25 are N(1.09, 0.10). L24 is the ONLY vintage on the shipped prior and it
## has never been postprocessed or benchmarked. Until it is, nobody knows what the production
## configuration actually scores.
##
## ⚠ L24 HAS NO RUN LOG, so the banner cannot be read (the same gap that lost --amp-mu on the
## L23 line). The arm is therefore verified FROM THE DATA below: `ais_gmst_amp` is
## prior-dominated (posterior sd / prior sd = 0.95-0.99), so its POSTERIOR sd reveals the
## prior sigma. Measured 2026-09-01: L24 implies 0.178 where L21/L22/L23/L23b/L25 imply ~0.10.
##
## ⚠ ITS PROPOSAL COVARIANCE WAS INHERITED, NOT CHOSEN (adapted_cov_L11tune3, no --adcov).
## That is acceptable HERE and the justification is measured, not assumed: L23-vs-L25 changes
## ONLY the covariance and lands INSIDE the RNG-only noise floor (L23-vs-L23b) — median shift
## 0.029 sd vs 0.046 sd, max 0.84 vs 0.79 sd. The covariance does not move this posterior.
##
## ⚠ THIS PROMOTES NOTHING. champions.json is untouched; promotion is Marcus's call.
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T=L24
CTRL=L23                        # L24 changes ONE thing about it: amp sigma 0.10 -> 0.180
SIGMA_EXPECT=0.180              # verified from the posterior sd, not from a banner
LOG=outputs/log_l24_postprocess_driver.txt
J="julia --project=julia_v2"
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }
step(){ local nm="$1"; shift
  say "START  $nm"
  if "$@" >> "$LOG" 2>&1; then say "OK     $nm"; else say "FAILED $nm (rc=$?) — continuing to the next independent step"; fi
}

: > "$LOG"
say "waiting for any $T chains to finish..."
while pgrep -f "tag=$T" > /dev/null; do sleep 60; done
say "chains done."

say "=== ARM VERIFICATION (from data — there is no run log) ==="
source ~/climate-env/bin/activate
python - "$T" "$SIGMA_EXPECT" >> "$LOG" 2>&1 <<'PY'
import sys, glob, numpy as np
t, want = sys.argv[1], float(sys.argv[2])
fs = sorted(glob.glob(f"outputs/mcmc/ampcol_{t}_seed*.npy"))
if not fs:
    print(f"  no ampcol cache for {t}; run python/diag_amp_by_vintage.py {t} first"); sys.exit(0)
v = np.concatenate([np.load(f) for f in fs]); implied = v.std()/0.97
ok = abs(implied-want)/want < 0.10
print(f"  amp posterior sd {v.std():.4f} -> implied prior sd {implied:.4f} (expect {want}) "
      f"{'OK' if ok else '*** MISMATCH — STOP, this is not the sigma-0.180 arm ***'}")
print(f"  amp pooled median {np.median(v):.4f}  n={len(v):,}")
PY
tail -3 "$LOG"
ls -la outputs/mcmc/chain_${T}_seed*.csv >> "$LOG" 2>&1

step "slr convergence diag (REQUIRED before postprocess)" \
     $J julia/diag_slr_convergence_by_chain_ladrillo.jl --tag=$T
step "postprocess (writes the subsample; ~50 min — DO NOT KILL)" \
     $J julia/postprocess_mcmc_ext.jl --tag=$T --accept-slr
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
step "model comparison" python python/ladrillo_model_comparison.py --tag=$T
step "benchmark"        python python/bench_ladrillo.py --tag=$T
step "amp table incl $T" python python/diag_amp_by_vintage.py L21 L22 L23 L23b $T L25

say "=== DONE. READ IN THIS ORDER ==="
say "  1. the ARM VERIFICATION above — implied prior sd must be ~$SIGMA_EXPECT. If it reads"
say "     ~0.10 this is NOT the shipped-prior arm and everything below is mislabelled."
say "  2. outputs/bench_ladrillo_${T}.md vs bench_ladrillo_${CTRL}.md and _L21.md."
say "     ⚠ THE ONLY LIKE-FOR-LIKE PAIR IS ${CTRL} vs ${T} (one axis: amp sigma). L21 differs"
say "     in BOTH the amp centre and the glacier law and is NOT a controlled comparison."
say "  3. The AIS spread_vs_lit cells specifically: a 1.8x wider prior bought only 1.07x band"
say "     at L23->L24, so if AIS spread degrades further the cause is NOT the prior width."
say "  4. champions.json STAYS UNTOUCHED."
