#!/bin/bash
## OVERNIGHT 2026-09-20 -> 21: the two tests that separate the hypotheses for the L27 vs L26 Antarctic-geometry
## move (handoff_2026-09-20b §3), run SEQUENTIALLY on the Mac (4 chains each; ~4 h each under a quiet load).
##
##   L27r  SAME objective as L27; seed bank 3026-3029 (a different RNG stream per start row); starts = L27's OWN
##         2nd-half draws at the ais_iceflow0 quantiles (overdispersed_starts_L27r.csv); proposal seed = L27's
##         pooled covariance (adapted_cov_L27_named.csv). Measures the BETWEEN-REFIT precision of the AIS
##         geometry and of the AIS projection medians. If it lands on L27, the L26 -> L27 move was real and L26
##         was the drifted run; if it lands between, the ridge is slow (tau ~47k) and the paper states the spread.
##   L27b  L27 WITHOUT --no-ledger (the two 1850-1900 glacier set-asides sampled again; 52 params), canonical
##         seeds, L27's starts file (L26 draws, which carry the ledger columns), L26's covariance (superset by
##         name). If L27b lands on L26's geometry, option D couples to the AIS block; if on L27's, D is inert
##         and the move is drift.
## Each run: chains -> arm verification -> NOISE-MODE gate -> SLR convergence diag -> postprocess (--accept-slr)
## -> posterior predictive -> fixed-climate SSP components (tap). Then python/diag_refit_precision.py compares
## L26 / L27 / L27r / L27b on the AIS geometry (per chain), the hindcast RMSE and the AIS projection medians.
## Kill by PID (never pkill -f); log = outputs/log_overnight_L27r_L27b.txt.
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
LOG=outputs/log_overnight_L27r_L27b.txt; : > "$LOG"
J="julia --project=julia_v2"
NITER=2000000
BASEFLAGS="--gis-ordered --gis-basins2 --amp-mu=1.09 --amp-sigma=0.180 --paleo-priors --no-delta --no-d2-gsic --obs-corr-len=100 --toff-lo=-4 --precip-reparam --cut-fastdyn --fix-gamma"
say(){ echo "[$(date '+%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }
step(){ local nm="$1"; shift
  say "START  $nm"
  if "$@" >> "$LOG" 2>&1; then say "OK     $nm"; else say "FAILED $nm (rc=$?) — continuing"; fi
}

run_chains(){ # TAG SEEDS STARTS ADCOV FLAGS
  local T="$1" SEEDS="$2" STARTS="$3" ADCOV="$4" FLAGS="$5"
  [[ -f "$STARTS" ]] || { say "MISSING $STARTS"; return 1; }
  [[ -f "outputs/mcmc/$ADCOV" ]] || { say "MISSING outputs/mcmc/$ADCOV"; return 1; }
  say "$T: 4 chains x $NITER (seeds $SEEDS) — $FLAGS ; adcov=$ADCOV starts=$STARTS ; commit $(git rev-parse --short HEAD) ; load $(uptime | sed 's/.*load averages*: //')"
  local PIDS=()
  for SEED in $SEEDS; do
    $J --threads=1 julia/calibrate_mcmc_ext.jl "$NITER" "$SEED" \
        --tag=$T --overdisperse --starts=$STARTS --adcov=$ADCOV $FLAGS \
        > "outputs/mcmc/log_${T}_seed${SEED}.txt" 2>&1 &
    PIDS+=($!)
  done
  say "  chain PIDs: ${PIDS[*]}"
  wait "${PIDS[@]}"
  say "$T chains done. ARM VERIFICATION:"
  for SEED in $SEEDS; do
    say "  seed$SEED: $(tr '\r' '\n' < outputs/mcmc/log_${T}_seed${SEED}.txt | grep -a -m1 'L26 structure flags') | $(tr '\r' '\n' < outputs/mcmc/log_${T}_seed${SEED}.txt | grep -a -m1 'seeding proposal' | cut -c1-90)"
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
  step "$T posterior predictive" $J julia/posterior_predictive_ladrillo.jl --tag=$T
  step "$T ssp components (tap, fixed climate)" $J julia/project_ssps_components_ladrillo.jl --tag=$T
}

## ---- L27r ---------------------------------------------------------------------------------------------------
run_chains L27r "3026 3027 3028 3029" outputs/mcmc/overdispersed_starts_L27r.csv adapted_cov_L27_named.csv "$BASEFLAGS --no-ledger"
if noise_gate L27r "3026 3027 3028 3029"; then postprocess L27r; else say "L27r noise-mode gate FAILED — not postprocessing (investigate, do not --force)"; fi

## ---- L27b ---------------------------------------------------------------------------------------------------
run_chains L27b "2026 2027 2028 2029" outputs/mcmc/overdispersed_starts_L27.csv adapted_cov_L26_named.csv "$BASEFLAGS"
if noise_gate L27b "2026 2027 2028 2029"; then postprocess L27b; else say "L27b noise-mode gate FAILED — not postprocessing"; fi

## ---- the comparison -----------------------------------------------------------------------------------------
source ~/climate-env/bin/activate
step "refit precision comparison (L26 / L27 / L27r / L27b)" python python/diag_refit_precision.py --tags=L26,L27,L27r,L27b --ref=L26
say "ALLDONE"
