#!/bin/bash
## L28 STAGE 2 (2026-09-21): after run_L28.sh's pipeline (chains -> postprocess -> postpred -> ssp components tap),
## the rest of what L27 had (run_l27_postprocess.sh lines 43-53) plus the IMBIE-2026 diagnostics, then the paper arms
## (TAG=L28 run_paper_arms_L27.sh). CONTROL = L27, ONE axis: the AIS calibration target (Frederikse+GRACE -> IMBIE 2026).
## champions.json UNTOUCHED — promotion and the draft swap are Marcus's call.
set -uo pipefail
cd /Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T=L28
LOG=outputs/log_L28_stage2.txt; : > "$LOG"
J="julia --project=julia_v2"
say(){ echo "[$(date '+%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }
step(){ local nm="$1"; shift; say "START  $nm"
  if "$@" >> "$LOG" 2>&1; then say "OK     $nm"; else say "FAILED $nm (rc=$?)"; fi; }
grep -q "OK     L28 ssp components" outputs/log_L28.txt || { say "run_L28.sh did not complete its pipeline; STOP"; exit 1; }
[[ "$(md5 -q outputs/recalib_targets_ext.csv)" == "eb768cd96463a3b84721e2bb9a20f009" ]] || { say "target is not the IMBIE build; STOP"; exit 2; }
say "L28 stage 2 | commit $(git rev-parse --short HEAD)"
step "prior dump for the appendix" $J julia/calibrate_mcmc_ext.jl 100 2026 --tag=$T --gis-ordered --gis-basins2 --amp-mu=1.09 --amp-sigma=0.180 --paleo-priors --no-delta --no-d2-gsic --obs-corr-len=100 --toff-lo=-4 --precip-reparam --cut-fastdyn --fix-gamma --no-ledger --dump-priors
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
step "refit precision (L27 / L27r / L28)" python python/diag_refit_precision.py --tags=L27,L27r,L28 --ref=L27
say "=== stage 2 done; paper arms ==="
TAG=$T bash run_paper_arms_L27.sh >> "$LOG" 2>&1 && say "OK     paper arms" || say "FAILED paper arms"
say "ALLDONE stage 2"
