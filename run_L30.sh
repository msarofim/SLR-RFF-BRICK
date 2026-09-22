#!/bin/bash
## L30 (2026-09-22): L28's objective PLUS the ADDITIONAL DISCHARGE RESPONSE (--ais-ramp). CONTROL = L28, ONE axis:
## the ramp (two new sampled parameters, 52 in all). Everything else IDENTICAL to run_L28.sh / run_L29.sh — the
## IMBIE-2026 target (md5 asserted), BASEFLAGS + --no-ledger, seeds 2026-2029, starts = overdispersed_starts_L27r.csv,
## proposal = adapted_cov_L27_named.csv (the two ramp rows get a fresh diagonal; the ramp params start at the
## sweep's best cell on EVERY chain — they have no ancestor in any starts file).
## WHY: L28 (rho free) absorbed the reconciled record's acceleration as persistence and L29 (rho capped at 0.90)
## could neither absorb nor fit it — DAIS's linear discharge has no direction that produces it (scoping §4-5).
## A free exponent on the T_oc ratio is inert on the historical range (§6). The fixed-parameter sweep (§7,
## scope_ais_onset_sweep.jl) found that an ADDITIONAL discharge response linear in T_ant above ~0.6-0.75 K of global
## warming reproduces all four pre-pause IMBIE windows at once. This refit asks whether the likelihood takes it,
## whether the level is re-bought by the physics rather than by the noise, and what it costs the projections.
## The term COEXISTS with the paleo binary (Marcus 09-22); a REPLACE arm would be L30b.
## PRE-REGISTERED SUCCESS LINE (handoff 09-22, scoping §7): 2011-17 rate within 1 sigma of IMBIE's 0.0556 AND
## 1992-2002 within 1 sigma AND the 1979-2023 cumulative within 1 sigma AND rho_ais < 0.95 (the shape carried by
## the physics, not by persistence). Failing any one of those, the ramp did not do what the sweep said it would.
## Steps: chains -> arm verification (incl. the ramp banner and the ramp START line) -> NOISE-MODE gate (rho_ais
## REPORTED, not capped) -> SLR convergence diag -> postprocess (--accept-slr) -> posterior predictive -> ssp
## components (tap) -> stage 2 diagnostics (no paper arms: not the paper's posterior unless Marcus rules so).
## Kill by PID (never pkill -f); log = outputs/log_L30.txt.
set -uo pipefail
cd /Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T=L30
LOG=outputs/log_${T}.txt; : > "$LOG"
[[ "$(md5 -q outputs/recalib_targets_ext.csv)" == "eb768cd96463a3b84721e2bb9a20f009" ]] || { echo "target file is not the IMBIE-2026 build"; exit 2; }
J="julia --project=julia_v2"
NITER=2000000
BASEFLAGS="--gis-ordered --gis-basins2 --amp-mu=1.09 --amp-sigma=0.180 --paleo-priors --no-delta --no-d2-gsic --obs-corr-len=100 --toff-lo=-4 --precip-reparam --cut-fastdyn --fix-gamma"
ARMFLAGS="$BASEFLAGS --no-ledger --ais-ramp"
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
    say "  seed$SEED: $(tr '\r' '\n' < $L | grep -a -m1 'L26 structure flags') | $(tr '\r' '\n' < $L | grep -a -m1 'L30 flag' | cut -c1-120) | $(tr '\r' '\n' < $L | grep -a -m1 'ais-ramp: .* start at the declared' | cut -c1-110) | $(tr '\r' '\n' < $L | grep -a -m1 'seeding proposal' | cut -c1-90)"
  done
  # the ramp must be LIVE in every chain, not just intended: the banner, the fresh covariance rows, and two
  # ramp columns that actually MOVE in the second half (a frozen column would mean the arm never sampled them).
  for SEED in $SEEDS; do
    tr '\r' '\n' < outputs/mcmc/log_${T}_seed${SEED}.txt | grep -aq "L30 flag: ais-ramp=true" || say "  *** seed$SEED: ramp NOT announced in its log ***"
    tr '\r' '\n' < outputs/mcmc/log_${T}_seed${SEED}.txt | grep -aq "fresh diagonal for .*ais_ramp_gon" || say "  *** seed$SEED: ramp rows not fresh in the proposal ***"
  done
}

noise_gate(){ # TAG SEEDS
  source ~/climate-env/bin/activate
  python - "$1" $2 >> "$LOG" 2>&1 <<'PY'
import sys, pandas as pd
t = sys.argv[1]; bad = []
for s in sys.argv[2:]:
    d = pd.read_csv(f"outputs/mcmc/chain_{t}_seed{s}_n2000000.csv", usecols=["sd_gis", "sd_ais", "rho_ais", "ais_ramp_gon", "ais_ramp_log10s", "log_post"]); d = d.iloc[len(d)//2:]
    m = d.sd_gis.median(); nu_gon = d.ais_ramp_gon.nunique(); nu_s = d.ais_ramp_log10s.nunique()
    print(f"  seed{s}: sd_gis median {m:.4f}  sd_ais {d.sd_ais.median():.4f}  rho_ais median {d.rho_ais.median():.4f}  "
          f"G_on {d.ais_ramp_gon.median():.3f} [{d.ais_ramp_gon.quantile(.05):.3f}, {d.ais_ramp_gon.quantile(.95):.3f}]  "
          f"log10 s {d.ais_ramp_log10s.median():.3f} [{d.ais_ramp_log10s.quantile(.05):.3f}, {d.ais_ramp_log10s.quantile(.95):.3f}]  "
          f"log_post {d.log_post.median():.1f}  {'OK' if m < 0.10 else '*** NOISE MODE ***'}")
    if m >= 0.10: bad.append(s)
    if nu_gon < 100 or nu_s < 100: bad.append(f"{s}(ramp FROZEN: {nu_gon}/{nu_s} unique values in the 2nd half)")
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
  step "refit precision (L28 / L29 / L30)" python python/diag_refit_precision.py --tags=L28,L29,L30 --ref=L28
  step "AIS tipped share (L28 / L29 / L30)" $J julia/diag_ais_tipped_share.jl --tags=L28,L29,L30 --ssps=ssp126,ssp245 --gap=15
}

## ---- L30 ----------------------------------------------------------------------------------------------------
run_chains $T "2026 2027 2028 2029" outputs/mcmc/overdispersed_starts_L27r.csv adapted_cov_L27_named.csv "$ARMFLAGS"
if noise_gate $T "2026 2027 2028 2029"; then postprocess $T; stage2 $T; else say "$T noise-mode gate FAILED — not postprocessing (investigate, do not --force)"; fi
say "ALLDONE"
