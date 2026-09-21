#!/bin/bash
## L28 (2026-09-21): the L27 objective REFIT ON THE IMBIE-2026 AIS TARGET (CHANGELOG 09-21g). Everything else as
## L27: BASEFLAGS + --no-ledger (50 params), canonical seeds 2026-2029, starts = L27's own 2nd-half draws at the
## ais_iceflow0 quantiles (overdispersed_starts_L27r.csv), proposal seed = L27's pooled covariance
## (adapted_cov_L27_named.csv). 4 chains in parallel on the Mac (~4 h under a quiet load).
## Target: outputs/recalib_targets_ext.csv md5 eb768cd96463a3b84721e2bb9a20f009 (asserted below); the superseded
## Frederikse-AIS target is in outputs/quarantine/20260921_ais_target_frederikse/.
## Steps: chains -> arm verification -> NOISE-MODE gate -> SLR convergence diag -> postprocess (--accept-slr)
## -> posterior predictive -> fixed-climate SSP components (tap). Kill by PID (never pkill -f);
## log = outputs/log_L28.txt.
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
LOG=outputs/log_L28.txt; : > "$LOG"
[[ "$(md5 -q outputs/recalib_targets_ext.csv)" == "eb768cd96463a3b84721e2bb9a20f009" ]] || { echo "target file is not the IMBIE-2026 build"; exit 2; }
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

## ---- L28 ----------------------------------------------------------------------------------------------------
run_chains L28 "2026 2027 2028 2029" outputs/mcmc/overdispersed_starts_L27r.csv adapted_cov_L27_named.csv "$BASEFLAGS --no-ledger"
if noise_gate L28 "2026 2027 2028 2029"; then postprocess L28; else say "L28 noise-mode gate FAILED — not postprocessing (investigate, do not --force)"; fi
say "ALLDONE"
