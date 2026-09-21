#!/bin/bash
## LWS :observed RE-RUN (2026-09-21, Marcus: "If we have LWS observations we should use them"): every
## projection arm the paper and its comparison draw on, regenerated under brick_mengel.jl LWS_MODE = :observed
## (the Frederikse + GRACE-FO land-water series through 2023, 0.30 mm/yr after), on BOTH models.
## Gate for the change (run first, 09-21 08:40, fixed-climate SSP components L27): glaciers / GIS / TE move
## EXACTLY 0; lws and total move by the observed-minus-constant offset (+0.35 cm from 2024 on, rel. 1995-2014;
## -0.33 at 2000); AIS moves <= 0.0125 cm through the sea-level feedback (stated, not hidden).
## Three streams in parallel (10 cores; ~3.5 min per Ladrillo arm, ~1 min per BRICK arm): Ladrillo FaIR-climate
## arms, Ladrillo MAGICC-climate arms, BRICK 2.0 arms. Then the comparison tables, figures and the benchmark.
## Hindcast products are NOT touched (their drivers pin lws=:central; the postpred total adds the observed LWS itself).
## Log: outputs/log_lws_observed_rerun.txt. Kill by PID, never pkill -f.
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T="${TAG:-L27}"
LOG=outputs/log_lws_observed_rerun.txt; : > "$LOG"
J="julia --project=julia_v2"
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }
step(){ local nm="$1" lg="$2"; shift 2; say "START  $nm"
  if "$@" >> "$lg" 2>&1; then say "OK     $nm"; else say "FAILED $nm (rc=$?)"; fi; }
say "LWS :observed re-run for $T | commit $(git rev-parse --short HEAD) | load $(uptime | sed 's/.*load averages*: //')"

stream_fair(){ local lg=outputs/log_lws_rerun_fair.txt; : > "$lg"
  for s in ssp126 ssp245 ssp585 vvVL vvL vvLN vvML vvM vvHL vvH; do
    step "ladrillo $s FaIR (tapped)" "$lg" $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s --tap
  done
  for s in ssp126 ssp245 ssp585; do   # the no-tap joint arms (the tap-contribution numbers in the draft)
    step "ladrillo $s FaIR (no tap)" "$lg" $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s
  done
  step "ssp components (tap)"    "$lg" $J julia/project_ssps_components_ladrillo.jl --tag=$T
  step "ssp components (no-tap)" "$lg" $J julia/project_ssps_components_ladrillo.jl --tag=$T --no-tap
  ## the two projection-side sensitivity arms (their DIFFERENCES cancel LWS, but their base is regenerated above)
  step "ssp components (const Greenland amp)" "$lg" env LADRILLO_GIS_SHAPE=gis_amp_shape_const $J julia/project_ssps_components_ladrillo.jl --tag=$T
  step "ssp components (AIS amp 1.196)"       "$lg" $J julia/project_ssps_components_ladrillo.jl --tag=${T}aisamp1p196
}
stream_magicc(){ local lg=outputs/log_lws_rerun_magicc.txt; : > "$lg"
  for s in ssp126 ssp245 ssp585 vvVL vvL vvLN vvML vvM vvHL vvH; do
    step "ladrillo $s MAGICC climate (spliced)" "$lg" $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s --climate=magicc --tap
    step "ladrillo $s MAGICC climate (raw)"     "$lg" $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s --climate=magicc --forcing=raw --tap
  done
}
stream_brick(){ local lg=outputs/log_lws_rerun_brick.txt; : > "$lg"
  for s in ssp126 ssp245 ssp585 vvVL vvL vvLN vvML vvM vvHL vvH; do
    step "BRICK 2.0 $s FaIR"           "$lg" $J julia/scope_slr_fairunc_oldbrick.jl --ssp=$s
    step "BRICK 2.0 $s MAGICC climate" "$lg" $J julia/scope_slr_fairunc_oldbrick.jl --ssp=$s --climate=magicc
  done
}
stream_fair & P1=$!; stream_magicc & P2=$!; stream_brick & P3=$!
say "streams: fair $P1, magicc $P2, brick $P3"
wait $P1 $P2 $P3
say "=== arms done; tables, figures, benchmark ==="
source ~/climate-env/bin/activate
lg=outputs/log_lws_rerun_post.txt; : > "$lg"
step "vv model comparison"        "$lg" python python/vv_model_comparison.py --tag=$T
step "ladrillo model comparison"  "$lg" python python/ladrillo_model_comparison.py --tag=$T
step "memo figures"               "$lg" python python/plot_ladrillo_memo_figures.py --tag=$T
step "hindcast (FIG 1)"           "$lg" python python/plot_hindcast_components.py --tag=$T
step "vv comparison figures"      "$lg" python python/plot_model_comparison_components.py --tag=$T --set=vv --year=all
step "vv trajectories"            "$lg" python python/plot_future_components.py --tag=$T --set=vv
step "vv gsic ladrillo-only"      "$lg" python python/plot_vv_gsic_wr_vs_ladrillo.py --tag=$T --ladrillo-only
step "climate swap"               "$lg" python python/plot_vv_climate_swap.py --tag=$T --year=all
step "responsiveness"             "$lg" python python/plot_vv_responsiveness.py --tag=$T
step "paper: hindcast"            "$lg" python python/plot_hindcast_components.py --tag=$T --paper
step "paper: vv comparison"       "$lg" python python/plot_model_comparison_components.py --tag=$T --set=vv --year=all --paper
step "paper: vv trajectories"     "$lg" python python/plot_future_components.py --tag=$T --set=vv --paper
step "paper: vv gsic"             "$lg" python python/plot_vv_gsic_wr_vs_ladrillo.py --tag=$T --ladrillo-only --paper
step "paper: responsiveness"      "$lg" python python/plot_vv_responsiveness.py --tag=$T --paper
step "regrowth attribution"       "$lg" python python/verify_magicc_regrowth_attribution.py --tag=$T
step "philosophy arms (diff arms; LWS cancels)" "$lg" python python/diag_brick_philosophy_arms.py --tag=$T
step "benchmark (refresh)"        "$lg" python python/bench_ladrillo.py --tag=$T
say "ALLDONE"
