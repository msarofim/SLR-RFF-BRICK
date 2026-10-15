#!/bin/bash
## THE BRICK 2.0 ARM MOVES TO THE PUBLISHED MimiBRICK v2.0.0 JOINT POSTERIOR (Marcus 2026-10-15: "move the BRICK 2.0 arm
## to the Zenodo joint file"). Zenodo 10.5281/zenodo.20592337, parameters_subsample_sneasybrick.csv (sha256 d74577f6...),
## at data/MimiBRICK/parameters_subsample_sneasybrick_zenodo20592337.csv. The arm reads its 35 BRICK columns;
## antarctic_precip0 is in log space, so the precip_log shim is off (brick_param_updates.jl). CHANGELOG 2026-10-15c/d.
## Every BRICK 2.0 product re-runs; no Ladrillo product moves (Table 5's Ladrillo residuals are a byte-identity gate).
##
## TWO PHASES:
##   ./run_brick20_zenodo_swap_20261015.sh arms        snapshot -> [SWAP-REGRESSION] (the EDITED code on the OLD file must
##                                                     reproduce the shipped vvH level arm and vvM CO2 pulse arm, provenance
##                                                     aside) -> the BRICK glacier + components panels -> three parallel
##                                                     streams: level arms (FaIR + MAGICC climate), hindcast side (posterior
##                                                     predictive, Table 5 residuals + Table 5, the Sect. 3.3 reversion
##                                                     test), pulse arms (FaIR + MAGICC climate, spliced + raw)
##   ./run_brick20_zenodo_swap_20261015.sh downstream  GMD tables/figures/benchmark, the pulse chain in FaIRtoFrEDI, the
##                                                     May-22 -> Zenodo paper-number diff; prune the snapshot to what moved
## NOT re-run (each is an older vintage the 10-08 v1.1 rerun also left alone, and still carries the May-22 file):
##   the overshoot / matched-dT arms (ssp126_nomarker, ssp534over_nomarker, ssp534overMATCH, ssp534over MAGICC climate;
##   09-02..09-04), diag_gcrit_brick2_vs_ladrillo (L24 only, 09-04), and the runtime timing (contaminated under load).
## QUARANTINE (~/.claude/CLAUDE.md): the May-22 products are SUPERSEDED, not bugged. Snapshot-then-prune as in
## run_ladrillo_v11_rerun_20261008.sh: $Q / $FQ end holding exactly the May-22 bytes of what moved. The *oldbrick*.parquet
## twins are MOVED (no driver rewrites them; a stale twin shadowed re-run arms once, memory
## stale_parquet_twin_shadowed_the_csv).
## Torch verdict: not needed -- single-core Julia arms of ~1-2 min, ~45 min with five processes; load ~2 of 10 at launch.
## Run from a FROZEN state: do not edit julia/*.jl or python/*.py while this runs (the pulse driver runs from a copy).
set -uo pipefail
PHASE="${1:?usage: $0 arms|downstream}"
cd "$(dirname "$0")"
SLR=$PWD
FTF=$(cd ../FaIRtoFrEDI && pwd)
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T=L27
SSPS="ssp126 ssp245 ssp585"
MARKERS="vvVL vvL vvLN vvML vvM vvHL vvH"
MCODES="VL L LN ML M HL H"
POSTERIOR=data/MimiBRICK/parameters_subsample_sneasybrick_zenodo20592337.csv
POSTERIOR_SHA=d74577f603602b222c829a152cb4dbcb60753af34ce4d1fba4cd0dfea52c203c
OLD_POSTERIOR=data/MimiBRICK/parameters_subsample_brick.csv
TAGQ=20261015_brick20_may22_posterior
Q=outputs/quarantine/$TAGQ
FQ=magicc_comparison/processed/quarantine/$TAGQ          # relative to $FTF
MARK="$Q/.run_start"
LOG=outputs/log_brick20_zenodo_swap_20261015.txt
J="julia --project=julia_v2"
PY=~/miniforge3/envs/slr-refresh-2025/bin/python          # FaIRtoFrEDI magicc_comparison
BRK=julia/_frozen_scope_slr_pulse_vv_brick2_20261015.jl
WIDE=$FTF/magicc_comparison/processed/vv_pulse_wide_20261009
NPAR=3                                                   # concurrent pulse runs
say(){ echo "[$(date '+%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }
step(){ local nm="$1" lg="$2"; shift 2; say "START  $nm"
  if "$@" >> "$lg" 2>&1; then say "OK     $nm"; else say "FAILED $nm (rc=$?)"; echo "$nm" >> "$LOG.fails"; fi; }
nfails(){ [[ -f "$LOG.fails" ]] && wc -l < "$LOG.fails" | tr -d ' ' || echo 0; }
psize(){ [[ "$1" == CO2 ]] && echo 1 || echo 0.01; }
[[ "$PHASE" == arms || "$PHASE" == downstream ]] || { echo "phase must be arms|downstream"; exit 1; }
[[ -n "${BRICK20_POSTERIOR:-}${BRICK20_PRECIP_LOG:-}${LADRILLO_LWS_OBS_ANCHOR:-}${LADRILLO_PALEO_ASSIGNMENT:-}${LADRILLO_GIS_SHAPE:-}" ]] &&
  { echo "settings must come from the code defaults: unset BRICK20_* and LADRILLO_* overrides"; exit 1; }
echo "$POSTERIOR_SHA  $POSTERIOR" | shasum -a 256 -c - >/dev/null || { echo "$POSTERIOR missing or not sha256 $POSTERIOR_SHA"; exit 1; }
source ~/climate-env/bin/activate
rm -f "$LOG.fails"
export SLR J BRK LOG
export -f say step psize

## ======================================== PHASE: arms ================================================
if [[ "$PHASE" == arms ]]; then
## RESUME: once the snapshot exists and [SWAP-REGRESSION] has passed, a re-launch skips both (a second snapshot would
## capture the regression runs' bytes, not the shipped ones) and starts at the panels. Added 10-15 after the first launch
## stopped at the panels (their ssp119/370/460 inputs no longer exist).
if [[ -f "$Q/.snapshot_list" ]] && grep -q "OK     \[SWAP-REGRESSION\]" "$LOG" 2>/dev/null; then RESUME=1; else RESUME=0; fi
[[ $RESUME == 1 ]] || : > "$LOG"
say "BRICK 2.0 posterior swap, phase ARMS$([[ $RESUME == 1 ]] && echo ' (RESUMED after the regression gate)') | SLR $(git rev-parse --short HEAD) | load $(uptime | sed 's/.*load averages*: //')"
for S in CO2 CH4; do [[ -f "$WIDE/gates_$S.csv" ]] || { say "missing $WIDE/gates_$S.csv (MAGICC pulse climate). STOP"; exit 1; }; done
cp julia/scope_slr_pulse_vv_brick2.jl "$BRK"
if [[ $RESUME == 0 ]]; then
[[ -e "$Q" || -e "$FTF/$FQ" ]] && { say "$Q or $FTF/$FQ already exists -- refusing to overwrite a quarantine. STOP"; exit 1; }
mkdir -p "$Q" "$FTF/$FQ"; touch "$MARK"

## --- snapshot: every file a BRICK 2.0 change can reach -----------------------------------------------------
find outputs -maxdepth 1 -type f \( -name "*oldbrick*" -o -name "*brick2*" -o -name "*brick20*" -o -name "*_B20*" \
     -o -name "ssps_gsic_2300*" -o -name "vv_gsic_2300*" -o -name "ic_*" -o -name "*scorecard*" -o -name "diag_*" \
     -o -name "vv_model_comparison*" -o -name "ladrillo_model_comparison*" -o -name "*paper_number_diff*" \
     -o -name "bench*" \) > "$Q/.snapshot_list"
find figures benchmark -type f >> "$Q/.snapshot_list"
ls deliverables/pulse_model_differences_tables.md deliverables/pulse_model_differences_L27_section.md >> "$Q/.snapshot_list"
sort -u -o "$Q/.snapshot_list" "$Q/.snapshot_list"
rsync -a --files-from="$Q/.snapshot_list" ./ "$Q/"
(cd "$FTF" && { find magicc_comparison/processed -maxdepth 1 -type f \( -name "pulse_crossmodel_cells_vv_2030*" \
     -o -name "scenario_dependence_2300*" -o -name "magiccclim_module_vs_climate*" -o -name "pulse_duration_*_vv_2030*" \
     -o -name "diag_igmst_ordering*" -o -name "diag_te_ohc_mechanism*" -o -name "diag_exchange_rate_paired_se*" \);
   find magicc_comparison/figures -maxdepth 1 -type f -name "pulse_duration_*"; } | sort -u > "$FQ/.snapshot_list"
   rsync -a --files-from="$FQ/.snapshot_list" ./ "$FQ/")
mkdir -p "$Q/outputs"; mv outputs/*oldbrick*.parquet "$Q/outputs/" 2>/dev/null
say "snapshot: $(wc -l < "$Q/.snapshot_list" | tr -d ' ') SLR files -> $Q; $(wc -l < "$FTF/$FQ/.snapshot_list" | tr -d ' ') FaIRtoFrEDI files -> $FTF/$FQ; parquet twins moved"

## --- [SWAP-REGRESSION]: the edited code with the OLD file must reproduce the shipped products -------------------
lg=outputs/log_brick20_swap_regress.txt; : > "$lg"
RG="env BRICK20_POSTERIOR=$OLD_POSTERIOR BRICK20_PRECIP_LOG=true"
step "regress: BRICK 2.0 vvH FaIR, old file" "$lg" $RG $J julia/scope_slr_fairunc_oldbrick.jl --ssp=vvH
step "regress: BRICK 2.0 pulse vvM CO2 FaIR, old file" "$lg" bash -c "$RG $J $BRK --marker=M --specie=CO2 --pulse-size=1 --ndraw=2000 --tag=B20 > logs/b2_regress_M_CO2.log 2>&1"
pairs=()
for k in cells draws paths; do pairs+=("outputs/scope_slr_fairunc_${k}_vvH_spliced_oldbrick.csv" "$Q/outputs/scope_slr_fairunc_${k}_vvH_spliced_oldbrick.csv"); done
for k in cells draws paths gates; do pairs+=("outputs/pulse_brick2_${k}_vvM_CO2_1Gt_2030_spliced_B20.csv" "$Q/outputs/pulse_brick2_${k}_vvM_CO2_1Gt_2030_spliced_B20.csv"); done
step "[SWAP-REGRESSION] edited code + May-22 file vs shipped" "$LOG" python python/gate_v11_regression.py "${pairs[@]}"
[[ "$(nfails)" == 0 ]] || { say "regression FAILED -- the edit changed more than the posterior. STOP (canonical vvH / vvM CO2 now hold regress output; the snapshot holds the shipped bytes)"; exit 1; }
fi

## --- panels FIRST: the SSP level arms' [CONTROL] reads the components panel, whose [GSIC-MATCH] reads the glacier panel
lg=outputs/log_brick20_swap_panels.txt; : > "$lg"
step "BRICK glacier panel (ssp)" "$lg" $J julia/project_ssps_gsic_2300.jl --set=ssp
step "BRICK glacier panel (vv)"  "$lg" $J julia/project_ssps_gsic_2300.jl --set=vv
step "BRICK 2.0 components panel" "$lg" $J julia/project_ssps_components_oldbrick.jl
[[ "$(nfails)" == 0 ]] || { say "a panel FAILED -- the level arms would compare against a stale panel. STOP"; exit 1; }

stream_level(){ local lg=outputs/log_brick20_swap_level.txt; : > "$lg"
  for s in $SSPS $MARKERS; do
    step "BRICK 2.0 $s FaIR"           "$lg" $J julia/scope_slr_fairunc_oldbrick.jl --ssp=$s
    step "BRICK 2.0 $s MAGICC climate" "$lg" $J julia/scope_slr_fairunc_oldbrick.jl --ssp=$s --climate=magicc
  done; }
stream_hind(){ local lg=outputs/log_brick20_swap_hind.txt; : > "$lg"
  step "BRICK 2.0 posterior predictive" "$lg" $J julia/posterior_predictive_oldbrick.jl
  step "IC hindcast residuals $T"       "$lg" $J julia/ic_hindcast_residuals.jl --tag=$T
  for f in ic_hindcast_residuals_ladrillo_${T}.csv ic_hindcast_obs_sigma.csv; do      # Ladrillo's half must not move
    if cmp -s "outputs/$f" "$Q/outputs/$f"; then say "[TABLE5-INPUT] $f byte-identical: PASS"
    else say "[TABLE5-INPUT] $f MOVED: FAIL"; echo "$f" >> "$LOG.fails"; fi; done
  step "Table 5 (rho 0.99 / 0.95 / 0.90)" "$lg" bash scripts/run_ic_arms.sh $T
  step "Sect. 3.3: reverted Ladrillo == BRICK 2.0" "$lg" $J julia/test_ladrillo_reverts_to_brick20.jl; }
stream_pulse(){
  one(){ local M=$1 S=$2 C=$3 F=$4
    if [[ "$C" == fair ]]; then
      step "BRICK 2.0 pulse vv$M $S FaIR" /dev/null bash -c "$J $BRK --marker=$M --specie=$S --pulse-size=$(psize $S) \
        --ndraw=2000 --tag=B20 > logs/b2_${M}_${S}.log 2>&1"
    else
      step "BRICK 2.0 pulse vv$M $S MAGICC climate ($F)" /dev/null bash -c "$J $BRK --marker=$M --specie=$S --pulse-size=$(psize $S) \
        --climate=magicc --forcing=$F --ndraw=2000 --tag=B20 > outputs/log_pulse_brick2_magiccclim_vv${M}_${S}_${F}.txt 2>&1"
    fi; }
  export -f one
  { for M in $MCODES; do for S in CO2 CH4; do echo "$M $S fair -"; done; done
    for F in spliced raw; do for M in $MCODES; do for S in CO2 CH4; do echo "$M $S magicc $F"; done; done; done; } |
    xargs -P $NPAR -L 1 bash -c 'one $0 $1 $2 $3'; }
stream_level & P1=$!; stream_hind & P2=$!; stream_pulse & P3=$!
say "streams: level $P1, hindcast $P2, pulse $P3"
wait $P1 $P2 $P3
say "=== ARMS DONE, $(nfails) failed step(s). Only on 0: '$0 downstream' ==="
exit "$(nfails)"
fi

## ======================================== PHASE: downstream ==========================================
say "BRICK 2.0 posterior swap, phase DOWNSTREAM | SLR $(git rev-parse --short HEAD)"
[[ -f "$Q/.snapshot_list" ]] || { say "no snapshot at $Q -- run the arms phase first. STOP"; exit 1; }
grep -q "=== ARMS DONE, 0 failed" "$LOG" || { say "the arms phase did not finish clean. STOP"; exit 1; }
lg=outputs/log_brick20_swap_downstream.txt; : > "$lg"
## GMD: the BRICK-reading steps of run_ladrillo_v11_rerun_20261008.sh's downstream (Ladrillo-only steps omitted)
step "vv model comparison"         "$lg" python python/vv_model_comparison.py --tag=$T
step "ladrillo model comparison"   "$lg" python python/ladrillo_model_comparison.py --tag=$T
step "memo figures"                "$lg" python python/plot_ladrillo_memo_figures.py --tag=$T
step "hindcast (FIG 1)"            "$lg" python python/plot_hindcast_components.py --tag=$T
step "vv comparison figures"       "$lg" python python/plot_model_comparison_components.py --tag=$T --set=vv --year=all
step "vv trajectories"             "$lg" python python/plot_future_components.py --tag=$T --set=vv
step "climate swap"                "$lg" python python/plot_vv_climate_swap.py --tag=$T --year=all
step "responsiveness"              "$lg" python python/plot_vv_responsiveness.py --tag=$T
step "paper: hindcast"             "$lg" python python/plot_hindcast_components.py --tag=$T --paper
step "paper: vv comparison"        "$lg" python python/plot_model_comparison_components.py --tag=$T --set=vv --year=all --paper
step "paper: vv trajectories"      "$lg" python python/plot_future_components.py --tag=$T --set=vv --paper
step "paper: responsiveness"       "$lg" python python/plot_vv_responsiveness.py --tag=$T --paper
step "regrowth attribution"        "$lg" python python/verify_magicc_regrowth_attribution.py --tag=$T
step "philosophy arms"             "$lg" python python/diag_brick_philosophy_arms.py --tag=$T
step "Table 4: hindcast scorecard" "$lg" python python/scope_ladrillo_vs_brick20_scorecard.py --tag=$T
step "compensating-error diag"     "$lg" python python/diag_component_error_cancellation.py --tag=$T
step "TE rate attribution"         "$lg" python python/diag_te_rate_attribution.py --tag=$T
step "IMBIE 2026 vs targets"       "$lg" python python/diag_imbie2026_vs_targets.py --tag=$T
step "benchmark (refresh vs the frozen champion)" "$lg" python python/bench_ladrillo.py --tag=$T
## pulse paper: the FaIRtoFrEDI chain (run_vv_pulse_rerun_20261009_ladrillo.sh downstream) + the paired-se exchange rate
d(){ local nm="$1"; shift; step "$nm" "$lg" bash -c "cd '$FTF' && $PY $*"; }
d "cross-model table"            magicc_comparison/build_stage4_crossmodel_table.py
d "scenario dependence 2300"     magicc_comparison/diag_scenario_dependence_2300.py
for m in ladrillo brick2; do for S in CO2 CH4; do
  d "module vs climate $m $S"    magicc_comparison/diag_magiccclim_module_vs_climate.py --module $m --specie $S; done; done
d "pulse duration"               magicc_comparison/pulse_duration_vv.py
d "pulse duration figures"       magicc_comparison/fig_pulse_duration_vv.py
d "iGMST ordering"               magicc_comparison/diag_igmst_ordering_vv.py
d "TE/OHC mechanism"             magicc_comparison/diag_te_ohc_mechanism_vv.py
d "doc tables"                   magicc_comparison/build_pulse_doc_tables.py
d "exchange rate, paired se"     magicc_comparison/diag_exchange_rate_paired_se.py
## the paper-number diff, May-22 -> Zenodo (the v1.1 quantity map, pointed at this quarantine)
step "paper-number diff May-22 -> Zenodo" "$lg" python python/v11_paper_number_diff.py --old-dir=$Q/outputs \
  --out=outputs/brick20_swap_paper_number_diff_20261015.csv --old-label=May-22 --new-label=Zenodo

## --- prune both snapshots to what moved -------------------------------------------------------------------
prune(){ local root="$1" q="$2" moved=0 same=0
  while IFS= read -r f; do
    if [[ -f "$root/$f" ]] && cmp -s "$root/$f" "$q/$f"; then rm -f "$q/$f"; same=$((same+1)); else moved=$((moved+1)); fi
  done < "$q/.snapshot_list"
  find "$q" -type d -empty -delete
  say "quarantine $q: $moved May-22 files kept, $same unchanged copies pruned"; }
prune "$SLR" "$SLR/$Q"
prune "$FTF" "$FTF/$FQ"
grep -vxF -f "$Q/.snapshot_list" <(find outputs figures benchmark deliverables -maxdepth 2 -type f -newer "$MARK" -not -path "$Q/*" | sort) \
  > "$Q/.touched_not_snapshotted" || true
say "touched but NOT snapshotted (May-22 bytes only in git, if tracked): $(wc -l < "$Q/.touched_not_snapshotted" | tr -d ' ')"
for q in "$SLR/$Q" "$FTF/$FQ"; do (cd "$q" && find . -type f ! -name SHA256SUMS ! -name README.md ! -name '.snapshot_list' \
  ! -name '.touched_not_snapshotted' ! -name '.run_start' -print0 | sort -z | xargs -0 shasum -a 256 > SHA256SUMS); done
say "=== DOWNSTREAM DONE, $(nfails) failed step(s) ==="
exit "$(nfails)"
