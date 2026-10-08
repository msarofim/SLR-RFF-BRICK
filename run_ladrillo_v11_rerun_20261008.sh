#!/bin/bash
## LADRILLO v1.1 RE-RUN (Marcus 2026-10-08, handoff notes/handoff_2026-10-07c_ladrillo_v11.md §2: "the paper moves to
## v1.1 now; the research drivers produce it"). SAME POSTERIOR (L27), two projection-side fixes, no recalibration:
##   A  paleo (lambda, T_crit): ONE assignment over the 10,000-draw subsample (LADRILLO_PALEO_ASSIGNMENT = :single), so
##      the joint arm no longer reuses one chain's 500 paleo rows four times and every driver's draw keeps its row.
##      The joint arm now reads the 10k subsample (--source=subsample), proven to give the raw-chain draws exactly.
##   B  land water: the observed series starts at 0 (LWS_OBS_ANCHOR = :zero_at_first_year), not at its 1995-2005-frame
##      value in 1900 (the v1.0 "frame step"), which DAIS's sea-level feedback saw.
## Both v1.0 settings stay reachable by environment (LADRILLO_LWS_OBS_ANCHOR=v1_step, LADRILLO_PALEO_ASSIGNMENT=v1), and
## a run under them writes "_paleov1_lwsv1_step"-suffixed names, so it cannot overwrite the canonical outputs.
##
## THREE PHASES:
##   ./run_ladrillo_v11_rerun_20261008.sh regress     the EDITED code with the v1.0 settings must reproduce the SHIPPED
##                                                    v1.0 products exactly (panel, SSP + vv FaIR, vv MAGICC, BRICK 2.0)
##                                                    -- run BEFORE anything canonical is touched; writes to $R only
##   ./run_ladrillo_v11_rerun_20261008.sh arms        snapshot -> panels FIRST (the joint arms' [CONTROL-EXACT] reads
##                                                    them) -> three parallel streams -> hindcast-side products
##   ./run_ladrillo_v11_rerun_20261008.sh downstream  tables, figures, benchmark; prune the snapshot to what moved
## WHAT RE-RUNS (inventory 2026-10-08, CHANGELOG): every Ladrillo projection arm (fixes A+B), every BRICK 2.0 arm
## (fix B only: its DAIS sees the land-water series; its posterior carries lambda/T_crit), the fixed-climate panels and
## the paper's fixed-arm sensitivities (1.196 reversion, amplification leverage, refit precision L27r/L27b), and the
## posterior predictive (fix A reaches 2021-2026 through 4 low-T_crit draws). Table 5's residuals already assign over
## all 10,000 draws and use :central land water, so they must come back BYTE-IDENTICAL (a gate, not a refresh).
## NOT re-run: the pulse drivers (L24, a separate paper), the convergence R-hat (per-chain paleo rows are the right
## design for a between-chain statistic), FACTS / MAGICC-SLR (no Ladrillo or land-water input).
##
## QUARANTINE (~/.claude/CLAUDE.md): the v1.0 products are SUPERSEDED, not bugged -- they are the submitted version.
## Snapshot-then-prune as in run_vv_cmip7_rerun_20261007.sh: $Q ends holding exactly the v1.0 bytes of what moved.
## Torch verdict: not needed -- single-core arms, ~1.5 h with three streams; load was ~3 of 10 cores at launch.
## Run from a FROZEN state: do not edit julia/*.jl or python/*.py while this runs.
set -uo pipefail
PHASE="${1:?usage: $0 regress|arms|downstream}"
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T=L27
TAP=_tap4p69K_V5p64m_tau800
SSPS="ssp126 ssp245 ssp585"
MARKERS="vvVL vvL vvLN vvML vvM vvHL vvH"
Q=outputs/quarantine/20261008_ladrillo_v10_superseded
R=outputs/v11_regression_20261008
LOG=outputs/log_ladrillo_v11_rerun_20261008.txt
MARK="$Q/.run_start"
J="julia --project=julia_v2"
V10="env LADRILLO_LWS_OBS_ANCHOR=v1_step LADRILLO_PALEO_ASSIGNMENT=v1"
V10SFX=_paleov1_lwsv1_step
say(){ echo "[$(date '+%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }
step(){ local nm="$1" lg="$2"; shift 2; say "START  $nm"
  if "$@" >> "$lg" 2>&1; then say "OK     $nm"; else say "FAILED $nm (rc=$?)"; echo x >> "$LOG.fails"; fi; }
nfails(){ [[ -f "$LOG.fails" ]] && wc -l < "$LOG.fails" | tr -d ' ' || echo 0; }
[[ "$PHASE" == regress || "$PHASE" == arms || "$PHASE" == downstream ]] || { echo "phase must be regress|arms|downstream"; exit 1; }
[[ -n "${LADRILLO_LWS_OBS_ANCHOR:-}${LADRILLO_PALEO_ASSIGNMENT:-}${LADRILLO_GIS_SHAPE:-}" ]] &&
  { echo "the v1.1 settings must come from the code defaults: unset LADRILLO_LWS_OBS_ANCHOR / LADRILLO_PALEO_ASSIGNMENT / LADRILLO_GIS_SHAPE"; exit 1; }
source ~/climate-env/bin/activate
rm -f "$LOG.fails"

## ======================================== PHASE: regress =============================================
if [[ "$PHASE" == regress ]]; then
: > "$LOG"
say "v1.1 re-run, phase REGRESS | commit $(git rev-parse --short HEAD) | load $(uptime | sed 's/.*load averages*: //')"
mkdir -p "$R"; lg="$R/log_regress.txt"; : > "$lg"
step "v1.0 settings: panel (tap)"            "$lg" $V10 $J julia/project_ssps_components_ladrillo.jl --tag=$T
step "v1.0 settings: ladrillo ssp585 FaIR"   "$lg" $V10 $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=ssp585 --tap
step "v1.0 settings: ladrillo vvH FaIR"      "$lg" $V10 $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=vvH --tap
step "v1.0 settings: ladrillo vvH MAGICC"    "$lg" $V10 $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=vvH --climate=magicc --tap
step "v1.0 settings: BRICK 2.0 vvH FaIR"     "$lg" env LADRILLO_LWS_OBS_ANCHOR=v1_step $J julia/scope_slr_fairunc_oldbrick.jl --ssp=vvH
## move the reproductions out of outputs/ (they are evidence, not products), then compare against the shipped files
pairs=()
add(){ local new="$1" old="$2"; mv "outputs/$new" "$R/$new" && pairs+=("$R/$new" "outputs/$old"); }
add "ssps_components_2300_${T}${TAP}_n2_ws${V10SFX}.csv" "ssps_components_2300_${T}${TAP}_n2_ws.csv"
for s in ssp585 vvH; do for k in cells draws paths gates; do
  add "scope_slr_fairunc_${k}_${s}_spliced_${T}${TAP}${V10SFX}.csv" "scope_slr_fairunc_${k}_${s}_spliced_${T}${TAP}.csv"
done; done
for k in cells draws paths gates; do
  add "scope_slr_fairunc_${k}_vvH_spliced_magiccclim_${T}${TAP}${V10SFX}.csv" "scope_slr_fairunc_${k}_vvH_spliced_magiccclim_${T}${TAP}.csv"
done
for k in cells draws paths; do
  add "scope_slr_fairunc_${k}_vvH_spliced_oldbrick_lwsv1_step.csv" "scope_slr_fairunc_${k}_vvH_spliced_oldbrick.csv"
done
step "[V1-REGRESSION] reproduced v1.0 vs shipped" "$LOG" python python/gate_v11_regression.py "${pairs[@]}"
say "=== REGRESS DONE, $(nfails) failed step(s). Only on 0: '$0 arms' ==="
exit "$(nfails)"
fi

## ======================================== PHASE: arms ================================================
if [[ "$PHASE" == arms ]]; then
grep -q "\[V1-REGRESSION\] PASS" "$LOG" 2>/dev/null || { echo "phase regress has not passed (no [V1-REGRESSION] PASS in $LOG). STOP"; exit 1; }
say "v1.1 re-run, phase ARMS | commit $(git rev-parse --short HEAD) | load $(uptime | sed 's/.*load averages*: //')"
[[ -e "$Q" ]] && { say "$Q already exists -- refusing to overwrite a quarantine. STOP"; exit 1; }
mkdir -p "$Q"; touch "$MARK"
find outputs -maxdepth 1 -type f \( -name "*${T}*" -o -name "*vv*" -o -name "*oldbrick*" \) \
     -newer outputs/mcmc/chain_${T}_seed2026_n2000000.csv > "$Q/.snapshot_list"
find figures benchmark -type f >> "$Q/.snapshot_list"
ls outputs/ic_hindcast_residuals_brick20.csv outputs/ic_hindcast_obs_sigma.csv >> "$Q/.snapshot_list"   # Table 5's other inputs
sort -u -o "$Q/.snapshot_list" "$Q/.snapshot_list"
rsync -a --files-from="$Q/.snapshot_list" ./ "$Q/"
say "snapshot: $(wc -l < "$Q/.snapshot_list" | tr -d ' ') files -> $Q"

## --- panels FIRST: every SSP joint arm's [CONTROL-EXACT] compares against them -------------------------------
lg=outputs/log_v11_panels.txt; : > "$lg"
step "panel L27 (tap)"                 "$lg" $J julia/project_ssps_components_ladrillo.jl --tag=$T
step "panel L27 (no tap)"              "$lg" $J julia/project_ssps_components_ladrillo.jl --tag=$T --no-tap
step "panel L27 (const Greenland amp)" "$lg" env LADRILLO_GIS_SHAPE=gis_amp_shape_const $J julia/project_ssps_components_ladrillo.jl --tag=$T
step "panel L27aisamp1p196 (the 1.196 reversion)" "$lg" $J julia/project_ssps_components_ladrillo.jl --tag=${T}aisamp1p196
step "panel L27r (refit precision)"    "$lg" $J julia/project_ssps_components_ladrillo.jl --tag=${T}r
step "panel L27b (refit precision)"    "$lg" $J julia/project_ssps_components_ladrillo.jl --tag=${T}b
[[ "$(nfails)" == 0 ]] || { say "a panel FAILED -- the joint arms would compare against a stale panel. STOP"; exit 1; }

stream_fair(){ local lg=outputs/log_v11_fair.txt; : > "$lg"
  for s in $SSPS $MARKERS; do step "ladrillo $s FaIR (tapped)" "$lg" $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s --tap; done
  for s in $SSPS; do step "ladrillo $s FaIR (no tap)" "$lg" $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s; done
  for s in $SSPS; do step "ladrillo $s FaIR (tapped, const Greenland amp)" "$lg" \
      env LADRILLO_GIS_SHAPE=gis_amp_shape_const $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s --tap; done
}
stream_magicc(){ local lg=outputs/log_v11_magicc.txt; : > "$lg"
  for s in $SSPS $MARKERS; do
    step "ladrillo $s MAGICC climate (spliced)" "$lg" $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s --climate=magicc --tap
    step "ladrillo $s MAGICC climate (raw)"     "$lg" $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s --climate=magicc --forcing=raw --tap
  done
}
stream_brick(){ local lg=outputs/log_v11_brick.txt; : > "$lg"
  for s in $SSPS $MARKERS; do
    step "BRICK 2.0 $s FaIR"           "$lg" $J julia/scope_slr_fairunc_oldbrick.jl --ssp=$s
    step "BRICK 2.0 $s MAGICC climate" "$lg" $J julia/scope_slr_fairunc_oldbrick.jl --ssp=$s --climate=magicc
  done
  ## hindcast side, after BRICK (short): fix A reaches 2021-2026; Table 5's residuals must not move at all
  step "posterior predictive L27"         "$lg" $J julia/posterior_predictive_ladrillo.jl --tag=$T
  step "IC hindcast residuals L27 (must be byte-identical)" "$lg" $J julia/ic_hindcast_residuals.jl --tag=$T
  step "amplification leverage L27 (fixed arm)" "$lg" $J julia/diag_ais_amp_leverage.jl --tag=$T
}
stream_fair & P1=$!; stream_magicc & P2=$!; stream_brick & P3=$!
say "streams: fair $P1, magicc $P2, brick+hindcast $P3"
wait $P1 $P2 $P3
## [TABLE5-INPUT] byte identity of the IC residuals against the v1.0 snapshot
for f in ic_hindcast_residuals_ladrillo_${T}.csv ic_hindcast_residuals_brick20.csv ic_hindcast_obs_sigma.csv; do
  if [[ -f "$Q/outputs/$f" ]]; then
    cmp -s "outputs/$f" "$Q/outputs/$f" && say "[TABLE5-INPUT] $f byte-identical: PASS" || { say "[TABLE5-INPUT] $f MOVED: FAIL"; echo x >> "$LOG.fails"; }
  else say "[TABLE5-INPUT] $f not in the snapshot (written before the chains?) -- compare by hand"; fi
done
say "=== ARMS DONE, $(nfails) failed step(s). Next: '$0 downstream' ==="
exit "$(nfails)"
fi

## ======================================== PHASE: downstream ==========================================
say "v1.1 re-run, phase DOWNSTREAM | commit $(git rev-parse --short HEAD)"
[[ -f "$Q/.snapshot_list" ]] || { say "no snapshot at $Q -- run the arms phase first. STOP"; exit 1; }
lg=outputs/log_v11_downstream.txt; : > "$lg"
## the union of run_paper_arms_L27.sh, run_lws_observed_rerun.sh and run_vv_cmip7_rerun_20261007.sh, SSP steps included
step "vv model comparison"         "$lg" python python/vv_model_comparison.py --tag=$T
step "ladrillo model comparison"   "$lg" python python/ladrillo_model_comparison.py --tag=$T
step "memo figures"                "$lg" python python/plot_ladrillo_memo_figures.py --tag=$T
step "hindcast (FIG 1)"            "$lg" python python/plot_hindcast_components.py --tag=$T
step "vv comparison figures"       "$lg" python python/plot_model_comparison_components.py --tag=$T --set=vv --year=all
step "vv trajectories"             "$lg" python python/plot_future_components.py --tag=$T --set=vv
step "vv gsic ladrillo-only"       "$lg" python python/plot_vv_gsic_wr_vs_ladrillo.py --tag=$T --ladrillo-only
step "climate swap"                "$lg" python python/plot_vv_climate_swap.py --tag=$T --year=all
step "responsiveness"              "$lg" python python/plot_vv_responsiveness.py --tag=$T
step "paper: hindcast"             "$lg" python python/plot_hindcast_components.py --tag=$T --paper
step "paper: vv comparison"        "$lg" python python/plot_model_comparison_components.py --tag=$T --set=vv --year=all --paper
step "paper: vv trajectories"      "$lg" python python/plot_future_components.py --tag=$T --set=vv --paper
step "paper: vv gsic"              "$lg" python python/plot_vv_gsic_wr_vs_ladrillo.py --tag=$T --ladrillo-only --paper
step "paper: responsiveness"       "$lg" python python/plot_vv_responsiveness.py --tag=$T --paper
step "regrowth attribution"        "$lg" python python/verify_magicc_regrowth_attribution.py --tag=$T
step "philosophy arms"             "$lg" python python/diag_brick_philosophy_arms.py --tag=$T
step "Table 4: hindcast scorecard" "$lg" python python/scope_ladrillo_vs_brick20_scorecard.py --tag=$T
step "compensating-error diag"     "$lg" python python/diag_component_error_cancellation.py --tag=$T
step "TE rate attribution"         "$lg" python python/diag_te_rate_attribution.py --tag=$T
step "glacier response times"      "$lg" python python/diag_glacier_response_times.py --tag=$T
step "Table A2 (10k subsample)"    "$lg" python python/ladrillo_table_a2.py --tag=$T --source=subsample
## added 2026-10-08 after the paper-number map (CHANGELOG 10-08b): producers of quoted numbers the first list missed
step "posterior predictive L27r (refit precision)" "$lg" $J julia/posterior_predictive_ladrillo.jl --tag=${T}r
step "posterior predictive L27b (refit precision)" "$lg" $J julia/posterior_predictive_ladrillo.jl --tag=${T}b
step "IMBIE 2026 vs targets (Sect. 3.1)"           "$lg" python python/diag_imbie2026_vs_targets.py --tag=$T
step "refit precision (Sect. 3.2; reads raw chains)" "$lg" python python/diag_refit_precision.py --tags=L26,${T},${T}r,${T}b --ref=L26
## the benchmark is REFRESHED against its frozen v1.0 champion (benchmark/reference/L27), not re-frozen: re-freezing
## the champion on v1.1 is Marcus's call (handoff 10-08)
step "benchmark (refresh vs the frozen v1.0 champion)" "$lg" python python/bench_ladrillo.py --tag=$T

step "paper-number diff v1.0 -> v1.1" "$lg" python python/v11_paper_number_diff.py

## --- prune the snapshot to what moved ----------------------------------------------------------------
moved=0; same=0
while IFS= read -r f; do
  if [[ -f "$f" ]] && cmp -s "$f" "$Q/$f"; then rm -f "$Q/$f"; same=$((same+1)); else moved=$((moved+1)); fi
done < "$Q/.snapshot_list"
find "$Q" -type d -empty -delete
grep -vxF -f "$Q/.snapshot_list" <(find outputs figures benchmark -maxdepth 2 -type f -newer "$MARK" -not -path "$Q/*" -not -path "$R/*" | sort) \
  > "$Q/.touched_not_snapshotted" || true
say "quarantine: $moved v1.0 files kept in $Q, $same unchanged copies pruned"
say "touched but NOT snapshotted (v1.0 bytes only in git, if tracked): $(wc -l < "$Q/.touched_not_snapshotted" | tr -d ' ')"
say "=== DONE, $(nfails) failed step(s). Next: the v1.0 -> v1.1 paper-number diff ==="
exit "$(nfails)"
