#!/bin/bash
## RE-RUN EVERY VAN VUUREN PROJECTION ARM ON THE CMIP7 FORCING BASIS (Marcus 2026-10-07, decision §2.1 of
## notes/handoff_2026-10-07_clean_l27_repo.md: "Rerun all on CMIP7", FACTS included -- FACTS is run separately
## by facts/run_vv_cmip7_rerun_20261007.sh because it needs Colima).
##
## WHY. The paper's vv arms (09-21) ran fair-calibrate 1.6.0 on SMITH 2024 history; the cubes were regenerated
## on the CMIP7 basis 2026-10-02 (commit 31aa963) but the arms were never re-run. Before 2014 every spliced arm
## runs on the marker's own mean GMST, which on the Smith basis sat up to 0.074 K off the ssp245harm calibration
## driver; after 2014 the spliced path moves +0.055 K @2100, +0.067 K @2300 (median, marker-independent).
## Template: run_lws_observed_rerun.sh (09-21), vv rows only.
##
## WHAT RE-RUNS (everything that reads fair_{mean,cube}_*_vv*):
##   Ladrillo L27  vv x {FaIR spliced tapped, MAGICC-climate spliced tapped}   (~5 min each; MAGICC RAW arms do
##                 not read the FaIR files and are NOT re-run)
##   BRICK 2.0     vv x {FaIR, MAGICC climate}                                 (~1 min each; both read MEAN_G)
##   vv_gsic_2300.csv (project_ssps_gsic_2300.jl --set=vv, reads fair_mean_gmst_vv*)
##   then every downstream table/figure the 09-21 rerun refreshed.
##
## QUARANTINE (~/.claude/CLAUDE.md): SNAPSHOT-THEN-PRUNE. Every candidate (outputs/ top-level files named *L27*,
## *vv*, *oldbrick* written since the L27 chains; figures/; benchmark/) is COPIED to $Q before anything runs;
## after the run, copies whose canonical file is byte-identical are deleted, so $Q ends holding exactly the
## pre-fix bytes of what moved. Files the run touched that were NOT snapshotted are LISTED at the end.
##
## Torch verdict: not needed -- single-core arms, ~1.5 h serial; the CCX multistart holds 8 of 10 cores, so
## this runs one arm at a time with BLAS pinned to 1 thread.
## TWO PHASES, because FACTS feeds the downstream tables and must land in between:
##   ./run_vv_cmip7_rerun_20261007.sh arms         gate + snapshot + every Julia arm
##   (facts/run_vv_cmip7_rerun_20261007.sh, then re-extract facts_components_shared_n200.csv)
##   ./run_vv_cmip7_rerun_20261007.sh downstream   tables/figures + prune the snapshot
## Run from a FROZEN state: do not edit julia/*.jl or python/*.py while this runs.
set -uo pipefail
PHASE="${1:?usage: $0 arms|downstream}"
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T=L27
MARKERS="vvVL vvL vvLN vvML vvM vvHL vvH"
Q=outputs/quarantine/20261007_vv_smith_history_arms
LOG=outputs/log_vv_cmip7_rerun_20261007.txt
MARK="$Q/.run_start"
J="julia --project=julia_v2"
say(){ echo "[$(date '+%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }
step(){ local nm="$1"; shift; say "START  $nm"
  if "$@" >> "$LOG" 2>&1; then say "OK     $nm"; else say "FAILED $nm (rc=$?)"; FAILS=$((FAILS+1)); fi; }
FAILS=0
[[ "$PHASE" == arms || "$PHASE" == downstream ]] || { echo "phase must be arms or downstream"; exit 1; }
[[ "$PHASE" == arms ]] && : > "$LOG"
source ~/climate-env/bin/activate
if [[ "$PHASE" == arms ]]; then
say "vv CMIP7-basis rerun for $T | commit $(git rev-parse --short HEAD) | load $(uptime | sed 's/.*load averages*: //')"

## [VV-BASIS] refuse to run on Smith-basis drivers (mutation-tested 10-07: fails 7/7 on the quarantine copy)
python python/gate_vv_cmip7_basis.py >> "$LOG" 2>&1 || { say "[VV-BASIS] FAILED -- STOP"; exit 1; }
say "[VV-BASIS] PASS"

## --- snapshot -----------------------------------------------------------------------------------------
[[ -e "$Q" ]] && { say "$Q already exists -- refusing to overwrite a quarantine. STOP"; exit 1; }
mkdir -p "$Q"
touch "$MARK"
find outputs -maxdepth 1 -type f \( -name "*${T}*" -o -name "*vv*" -o -name "*oldbrick*" \) \
     -newer outputs/mcmc/chain_${T}_seed2026_n2000000.csv > "$Q/.snapshot_list"
find figures benchmark -type f >> "$Q/.snapshot_list"
rsync -a --files-from="$Q/.snapshot_list" ./ "$Q/"
say "snapshot: $(wc -l < "$Q/.snapshot_list" | tr -d ' ') files -> $Q"

## --- arms ---------------------------------------------------------------------------------------------
for m in $MARKERS; do
  step "ladrillo $m FaIR (tapped)"              $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$m --tap
  step "ladrillo $m MAGICC climate (spliced)"   $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$m --climate=magicc --tap
  step "BRICK 2.0 $m FaIR"                      $J julia/scope_slr_fairunc_oldbrick.jl --ssp=$m
  step "BRICK 2.0 $m MAGICC climate"            $J julia/scope_slr_fairunc_oldbrick.jl --ssp=$m --climate=magicc
done
step "BRICK 2.0 WR glaciers on vv (vv_gsic_2300)" $J julia/project_ssps_gsic_2300.jl --set=vv
say "=== ARMS DONE, $FAILS failed step(s). Next: FACTS, then '$0 downstream' ==="
exit $FAILS
fi

## ======================================== PHASE: downstream ============================================
say "downstream phase | commit $(git rev-parse --short HEAD)"
[[ -f "$Q/.snapshot_list" ]] || { say "no snapshot at $Q -- run the arms phase first. STOP"; exit 1; }

## --- downstream (the 09-21 list, minus SSP-only steps) --------------------------------------------------
step "vv model comparison"        python python/vv_model_comparison.py --tag=$T
step "ladrillo model comparison"  python python/ladrillo_model_comparison.py --tag=$T
step "memo figures"               python python/plot_ladrillo_memo_figures.py --tag=$T
step "vv comparison figures"      python python/plot_model_comparison_components.py --tag=$T --set=vv --year=all
step "vv trajectories"            python python/plot_future_components.py --tag=$T --set=vv
step "vv gsic ladrillo-only"      python python/plot_vv_gsic_wr_vs_ladrillo.py --tag=$T --ladrillo-only
step "climate swap"               python python/plot_vv_climate_swap.py --tag=$T --year=all
step "responsiveness"             python python/plot_vv_responsiveness.py --tag=$T
step "paper: vv comparison"       python python/plot_model_comparison_components.py --tag=$T --set=vv --year=all --paper
step "paper: vv trajectories"     python python/plot_future_components.py --tag=$T --set=vv --paper
step "paper: vv gsic"             python python/plot_vv_gsic_wr_vs_ladrillo.py --tag=$T --ladrillo-only --paper
step "paper: responsiveness"      python python/plot_vv_responsiveness.py --tag=$T --paper
step "regrowth attribution"       python python/verify_magicc_regrowth_attribution.py --tag=$T
step "philosophy arms"            python python/diag_brick_philosophy_arms.py --tag=$T
step "benchmark (refresh)"        python python/bench_ladrillo.py --tag=$T
step "Table 4: hindcast scorecard" python python/scope_ladrillo_vs_brick20_scorecard.py --tag=$T

## --- prune the snapshot to what moved ------------------------------------------------------------------
moved=0; same=0
while IFS= read -r f; do
  if [[ -f "$f" ]] && cmp -s "$f" "$Q/$f"; then rm -f "$Q/$f"; same=$((same+1)); else moved=$((moved+1)); fi
done < "$Q/.snapshot_list"
find "$Q" -type d -empty -delete
grep -vxF -f "$Q/.snapshot_list" <(find outputs figures benchmark -maxdepth 2 -type f -newer "$MARK" -not -path "$Q/*" | sort) \
  > "$Q/.touched_not_snapshotted" || true
say "quarantine: $moved pre-fix files kept in $Q, $same unchanged copies pruned"
say "touched but NOT snapshotted (pre-fix bytes only in git, if tracked): $(wc -l < "$Q/.touched_not_snapshotted" | tr -d ' ')"
say "=== DONE, $FAILS failed step(s). Next: FACTS (facts/run_vv_cmip7_rerun_20261007.sh), then the paper-number diff ==="
