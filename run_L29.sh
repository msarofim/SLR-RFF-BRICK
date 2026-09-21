#!/bin/bash
## L29 (2026-09-21): L28's objective with the ANTARCTIC AR(1) rho CAPPED at 0.90 (--rho-max=ais:0.90). CONTROL = L28,
## ONE axis: the rho_ais bound (0.99 -> 0.90). Everything else IDENTICAL to run_L28.sh — the IMBIE-2026 target
## (md5 asserted), BASEFLAGS + --no-ledger (50 params), seeds 2026-2029, starts = overdispersed_starts_L27r.csv
## (row 4's rho_ais 0.916 is repaired to 0.855 by the calibrator, marginal held), proposal = adapted_cov_L27_named.csv.
## WHY: L28 took the reconciled record with rho_ais 0.89 -> 0.97 against the bound and the physics unmoved
## (scoping_2026-09-21_dais_structure_vs_imbie2026.md §4). With the noise model unable to absorb the acceleration, either
## the sensitivity parameters move up (the physics CAN carry the shape; early-century misfit grows) or the fit degrades
## everywhere (it cannot; a structural steepening is needed). Either way the binding term is named.
## Steps: chains -> arm verification (incl. the rho-cap banner) -> NOISE-MODE gate -> SLR convergence diag -> postprocess
## (--accept-slr) -> posterior predictive -> ssp components (tap) -> stage 2 diagnostics (no paper arms: not the
## paper's posterior unless Marcus rules so). Kill by PID (never pkill -f); log = outputs/log_L29.txt.
set -uo pipefail
cd /Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T=L29
LOG=outputs/log_${T}.txt; : > "$LOG"
[[ "$(md5 -q outputs/recalib_targets_ext.csv)" == "eb768cd96463a3b84721e2bb9a20f009" ]] || { echo "target file is not the IMBIE-2026 build"; exit 2; }
J="julia --project=julia_v2"
NITER=2000000
RHO_CAP="ais:0.90"
BASEFLAGS="--gis-ordered --gis-basins2 --amp-mu=1.09 --amp-sigma=0.180 --paleo-priors --no-delta --no-d2-gsic --obs-corr-len=100 --toff-lo=-4 --precip-reparam --cut-fastdyn --fix-gamma"
ARMFLAGS="$BASEFLAGS --no-ledger --rho-max=$RHO_CAP"
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
    local L=outputs/mcmc/log_${T}_seed${SEED}.txt
    say "  seed$SEED: $(tr '\r' '\n' < $L | grep -a -m1 'L26 structure flags') | $(tr '\r' '\n' < $L | grep -a -m1 'AR(1) rho bound') | $(tr '\r' '\n' < $L | grep -a -m1 'rho_ais start repaired' || echo 'no rho repair') | $(tr '\r' '\n' < $L | grep -a -m1 'seeding proposal' | cut -c1-90)"
  done
  # the cap must be LIVE in every chain, not just announced
  for SEED in $SEEDS; do
    tr '\r' '\n' < outputs/mcmc/log_${T}_seed${SEED}.txt | grep -aq "rho bound: CAPPED — rho_ais < 0.9" || say "  *** seed$SEED: rho cap NOT announced in its log ***"
  done
}

noise_gate(){ # TAG SEEDS
  source ~/climate-env/bin/activate
  python - "$1" $2 >> "$LOG" 2>&1 <<'PY'
import sys, pandas as pd
t = sys.argv[1]; bad = []
for s in sys.argv[2:]:
    d = pd.read_csv(f"outputs/mcmc/chain_{t}_seed{s}_n2000000.csv", usecols=["sd_gis", "sd_ais", "rho_ais", "log_post"]); d = d.iloc[len(d)//2:]
    m = d.sd_gis.median(); rmax = d.rho_ais.max()
    print(f"  seed{s}: sd_gis median {m:.4f}  sd_ais {d.sd_ais.median():.4f}  rho_ais median {d.rho_ais.median():.4f} max {rmax:.4f}  log_post {d.log_post.median():.1f}  {'OK' if m < 0.10 else '*** NOISE MODE ***'}")
    if m >= 0.10: bad.append(s)
    if rmax >= 0.90: bad.append(f"{s}(rho_ais {rmax:.4f} >= cap — the cap was NOT live)")
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

stage2(){ # TAG — run_L28_stage2.sh's diagnostics, minus the paper arms
  local T="$1"
  step "prior dump for the appendix" $J julia/calibrate_mcmc_ext.jl 100 2026 --tag=$T $ARMFLAGS --dump-priors
  step "ssp components (no-tap)" $J julia/project_ssps_components_ladrillo.jl --tag=$T --no-tap
  for s in ssp126 ssp245 ssp585; do
    step "fair-uncertainty joint band $s" $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s --tap
  done
  step "DAIS flux split vs IMBIE" $J --threads=1 julia/diag_ais_flux_split_vs_imbie.jl --tag=$T 1000
  source ~/climate-env/bin/activate
  step "IMBIE 2026 vs targets/hindcast" python python/diag_imbie2026_vs_targets.py --tag=$T
  step "model comparison" python python/ladrillo_model_comparison.py --tag=$T
  step "benchmark"        python python/bench_ladrillo.py --tag=$T
  step "prior/posterior table" python python/ladrillo_prior_posterior_table.py --tag=$T
  step "refit precision (L27 / L28 / L29)" python python/diag_refit_precision.py --tags=L27,L28,L29 --ref=L28
}

## ---- L29 ----------------------------------------------------------------------------------------------------
run_chains $T "2026 2027 2028 2029" outputs/mcmc/overdispersed_starts_L27r.csv adapted_cov_L27_named.csv "$ARMFLAGS"
if noise_gate $T "2026 2027 2028 2029"; then postprocess $T; stage2 $T; else say "$T noise-mode gate FAILED — not postprocessing (investigate, do not --force)"; fi
say "ALLDONE"
