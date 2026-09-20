#!/bin/bash
## THE PAPER'S PROJECTION ARMS ON A NEW POSTERIOR TAG (handoff 2026-09-20 §1.3), then every figure the GMD
## draft carries, in memo AND --paper mode. Template: run_paper_arms_lws_central_20260918.sh (LWS_MODE=:central
## is the kernel default since 4617723; nothing here changes it).
##   Ladrillo (scope_slr_fair_uncertainty.jl, ~4 min each):  7 vv markers (FaIR climate, tapped)
##                                                          + ssp126/245/585 x {spliced, raw} MAGICC climate
##   The 3 SSP FaIR-climate joint bands are written by run_l27_postprocess.sh and are NOT re-run here.
##   BRICK 2.0 arms do not depend on the Ladrillo tag and are NOT re-run (the 09-18c files stand).
## No quarantine: a new tag writes NEW filenames; the L24 paper arms stay canonical for L24.
## ~1 h on the laptop. Torch verdict: not needed (single-core arms, no licence, ~1 h).
## Run from a FROZEN copy of the drivers: do not edit julia/*.jl or python/*.py while this runs.
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T="${TAG:-L27}"
LOG=outputs/log_paper_arms_${T}.txt
J="julia --project=julia_v2"
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }
step(){ local nm="$1"; shift; say "START  $nm"
  if "$@" >> "$LOG" 2>&1; then say "OK     $nm"; else say "FAILED $nm (rc=$?)"; fi; }
: > "$LOG"
say "paper arms for $T | commit $(git rev-parse --short HEAD)"
for f in data/MimiBRICK/parameters_subsample_brick_mengel_${T}.csv outputs/postpred_${T}_components_timeseries.csv; do
  [[ -f "$f" ]] || { say "MISSING $f — the postprocess has not produced the $T posterior; STOP"; exit 1; }
done
for m in vvVL vvL vvLN vvML vvM vvHL vvH; do
  step "ladrillo $m (FaIR climate, tapped)" $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$m --tap
done
for s in ssp126 ssp245 ssp585; do
  step "ladrillo $s MAGICC climate (spliced)" $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s --climate=magicc --tap
  step "ladrillo $s MAGICC climate (raw)"     $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s --climate=magicc --forcing=raw --tap
done
say "=== arms done; figures + benchmark ==="
source ~/climate-env/bin/activate
step "vv model comparison"       python python/vv_model_comparison.py --tag=$T
step "ladrillo model comparison" python python/ladrillo_model_comparison.py --tag=$T
step "memo figures"              python python/plot_ladrillo_memo_figures.py --tag=$T
step "hindcast (FIG 1)"          python python/plot_hindcast_components.py --tag=$T
step "vv comparison figures"     python python/plot_model_comparison_components.py --tag=$T --set=vv --year=all
step "vv trajectories"           python python/plot_future_components.py --tag=$T --set=vv
step "vv gsic ladrillo-only"     python python/plot_vv_gsic_wr_vs_ladrillo.py --tag=$T --ladrillo-only
step "climate swap"              python python/plot_vv_climate_swap.py --tag=$T --year=all
step "responsiveness"            python python/plot_vv_responsiveness.py --tag=$T
say "=== --paper renders -> figures/paper/ ==="
step "paper: hindcast"           python python/plot_hindcast_components.py --tag=$T --paper
step "paper: vv comparison"      python python/plot_model_comparison_components.py --tag=$T --set=vv --year=all --paper
step "paper: vv trajectories"    python python/plot_future_components.py --tag=$T --set=vv --paper
step "paper: vv gsic"            python python/plot_vv_gsic_wr_vs_ladrillo.py --tag=$T --ladrillo-only --paper
step "paper: responsiveness"     python python/plot_vv_responsiveness.py --tag=$T --paper
step "benchmark (refresh)"       python python/bench_ladrillo.py --tag=$T
say "=== DONE. figures/*${T}* and figures/paper/*${T}*; Table 4 = ladrillo_model_comparison_${T}.csv; next: IC arms (scripts/run_ic_arms.sh $T), Table A1/A2 on $T ==="
