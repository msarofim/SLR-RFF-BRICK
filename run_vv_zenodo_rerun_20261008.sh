#!/bin/bash
## VAN VUUREN ON THE PUBLISHED EMISSIONS + RECORD CONDITIONING (Marcus 2026-10-08: "go with b and any pending fixes that
## can be done simultaneously"; rulings: conditioning "own-config, drop", MAGICC-SLR re-run, FaIR pulse cubes only).
##   1  vv emissions: the published Zenodo v1.1.1 scenario 2024-2300 on the CMIP7 1.6.0 history (variant b,
##      FaIRtoFrEDI 202eb74). The `harmonized` files put the published post-2100 extension on the IIASA PRERELEASE 2100
##      level; for Medium-to-Low that was 10.5 GtCO2/yr too low for 200 years (-2,098 GtCO2, 0.73 K too cold at 2300;
##      CHANGELOG 2026-10-08j). EVERY vv arm moves: Ladrillo, BRICK 2.0, FACTS, MAGICC-SLR (its own run, separately),
##      and the MAGICC-climate arms through MEAN_G.
##   2  record conditioning (10-08g: "the joint arms take the record-conditioned draws"): Ladrillo's FaIR-climate joint
##      arms drop every draw whose Antarctic fast dynamics fire by the record end on its OWN config (scope_slr_fair_
##      uncertainty.jl, RECORD CONDITIONING). EVERY Ladrillo FaIR joint arm moves, SSP ones included.
## PHASES:
##   regress     the EDITED driver with --no-record-conditioning must reproduce the shipped ssp585 arm EXACTLY
##   cubes       quarantine the vv cubes (base 28 + pulse 112), rebuild them on the new emissions, gate them
##   arms        snapshot -> three streams -> gsic; then [CONDITIONED-PREDICTED]. ⚠ MAGICC-SLR's vv run and the
##               rebuilt vv_wide_20260831/ files must exist FIRST (the MAGICC-climate arms read them).
##   downstream  tables, figures, benchmark; prune the snapshot to what moved
## NOT re-run (unchanged inputs): the panels (fixed climate, SSP), the SSP MAGICC-climate and BRICK 2.0 arms, the
## posterior predictive and Table 5 inputs. NOT re-run (ruling): the pulse arc downstream of the FaIR pulse cubes.
## FACTS runs from facts/run_vv_zenodo_rerun_20261008.sh, after `cubes`.
## Torch verdict: not needed -- FACTS needs the local Docker; the arms are single-core streams (~1.5 h).
## Run from a FROZEN state: do not edit julia/*.jl or python/*.py while this runs.
set -uo pipefail
PHASE="${1:?usage: $0 regress|cubes|arms|downstream}"
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T=L27
TAP=_tap4p69K_V5p64m_tau800
SSPS="ssp126 ssp245 ssp585"
MARKERS="vvVL vvL vvLN vvML vvM vvHL vvH"
MCODES="VL L LN ML M HL H"
FTF=../FaIRtoFrEDI
QC=outputs/quarantine/20261008_vv_harmonized_tail_cubes
Q=outputs/quarantine/20261008_vv_zenodo_conditioning_arms
R=outputs/vvz_regression_20261008
LOG=outputs/log_vv_zenodo_rerun_20261008.txt
MARK="$Q/.run_start"
J="julia --project=julia_v2"
say(){ echo "[$(date '+%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }
step(){ local nm="$1" lg="$2"; shift 2; say "START  $nm"
  if "$@" >> "$lg" 2>&1; then say "OK     $nm"; else say "FAILED $nm (rc=$?)"; echo x >> "$LOG.fails"; fi; }
nfails(){ [[ -f "$LOG.fails" ]] && wc -l < "$LOG.fails" | tr -d ' ' || echo 0; }
[[ "$PHASE" =~ ^(regress|cubes|arms|downstream)$ ]] || { echo "phase must be regress|cubes|arms|downstream"; exit 1; }
[[ -n "${LADRILLO_LWS_OBS_ANCHOR:-}${LADRILLO_PALEO_ASSIGNMENT:-}${LADRILLO_GIS_SHAPE:-}" ]] &&
  { echo "the v1.1 settings must come from the code defaults: unset LADRILLO_* overrides"; exit 1; }
source ~/climate-env/bin/activate
rm -f "$LOG.fails"

## ======================================== PHASE: regress =============================================
if [[ "$PHASE" == regress ]]; then
say "vv-zenodo re-run, phase REGRESS | commit $(git rev-parse --short HEAD) | load $(uptime | sed 's/.*load averages*: //')"
mkdir -p "$R"; lg="$R/log_regress.txt"; : > "$lg"
step "edited driver, conditioning OFF: ladrillo ssp585 FaIR" "$lg" $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=ssp585 --tap --no-record-conditioning
pairs=()
for k in cells draws paths; do
  mv "outputs/scope_slr_fairunc_${k}_ssp585_spliced_${T}${TAP}_uncond.csv" "$R/" &&
    pairs+=("$R/scope_slr_fairunc_${k}_ssp585_spliced_${T}${TAP}_uncond.csv" "outputs/scope_slr_fairunc_${k}_ssp585_spliced_${T}${TAP}.csv")
done
mv "outputs/scope_slr_fairunc_gates_ssp585_spliced_${T}${TAP}_uncond.csv" "$R/" 2>/dev/null
step "[REGRESSION] conditioning-off reproduction vs shipped v1.1" "$LOG" python python/gate_v11_regression.py "${pairs[@]}"
say "=== REGRESS DONE, $(nfails) failed step(s). Only on 0: '$0 cubes' ==="
exit "$(nfails)"
fi

## ======================================== PHASE: cubes ===============================================
if [[ "$PHASE" == cubes ]]; then
grep -q "OK     \[REGRESSION\]" "$LOG" 2>/dev/null || { echo "phase regress has not passed. STOP"; exit 1; }
say "vv-zenodo re-run, phase CUBES | commit $(git rev-parse --short HEAD) | FaIRtoFrEDI $(git -C $FTF rev-parse --short HEAD)"
[[ -e "$QC" ]] && { say "$QC already exists -- refusing to overwrite a quarantine. STOP"; exit 1; }
for m in $MCODES; do [[ "$(cat $FTF/calibration_v160_prod/emissions_v160_cmip7harm_vv$m.variant 2>/dev/null)" == zenodo ]] ||
  { say "emissions for vv$m are not the zenodo variant. STOP"; exit 1; }; done
mkdir -p "$QC/data_observations"
for s in $MARKERS; do for f in gmst ohc; do
  git mv "data/observations/fair_cube_${f}_${s}_raw.csv" "$QC/data_observations/"
  git mv "data/observations/fair_mean_${f}_${s}.csv" "$QC/data_observations/"
done; done
mv data/observations/fair_cube_*_vv*_pulse*_raw.csv "$QC/data_observations/"
say "quarantined $(ls "$QC/data_observations" | wc -l | tr -d ' ') cube files -> $QC"
lg="$R/log_cubes.txt"; : > "$lg"
for m in $MCODES; do
  step "FaIR cube vv$m"           "$lg" bash -c "cd $FTF && OPENBLAS_NUM_THREADS=4 python scripts/build_fair_cube_vv_v160.py --marker $m"
  step "FaIR pulse vv$m CO2 10Gt" "$lg" bash -c "cd $FTF && OPENBLAS_NUM_THREADS=4 python scripts/build_fair_pulse_vv_v160.py --marker $m --specie CO2"
  step "FaIR pulse vv$m CO2 1Gt"  "$lg" bash -c "cd $FTF && OPENBLAS_NUM_THREADS=4 python scripts/build_fair_pulse_vv_v160.py --marker $m --specie CO2 --pulse-size 1"
  step "FaIR pulse vv$m CH4 1Gt"  "$lg" bash -c "cd $FTF && OPENBLAS_NUM_THREADS=4 python scripts/build_fair_pulse_vv_v160.py --marker $m --specie CH4"
  step "FaIR pulse vv$m CH4 0.01Gt" "$lg" bash -c "cd $FTF && OPENBLAS_NUM_THREADS=4 python scripts/build_fair_pulse_vv_v160.py --marker $m --specie CH4 --pulse-size 0.01"
done
say "pulse cubes rebuilt: $(ls data/observations/fair_cube_*_vv*_pulse*_raw.csv | wc -l | tr -d ' ') (quarantined $(ls "$QC"/data_observations/*pulse* | wc -l | tr -d ' '))"
step "[VV-ZENODO-BASIS] pre-2024 identity, post-2023 move, arm-b identity" "$LOG" python python/gate_vv_zenodo_basis.py "$QC/data_observations" "$R/arm_b_cubes"
step "[VV-BASIS] CMIP7 history (blind to this change; must still pass)" "$LOG" python python/gate_vv_cmip7_basis.py
say "=== CUBES DONE, $(nfails) failed step(s). Next: FACTS (facts/run_vv_zenodo_rerun_20261008.sh), MAGICC-SLR vv, then '$0 arms' ==="
exit "$(nfails)"
fi

## ======================================== PHASE: arms ================================================
if [[ "$PHASE" == arms ]]; then
grep -q "OK     \[VV-ZENODO-BASIS\]" "$LOG" 2>/dev/null || { echo "phase cubes has not passed. STOP"; exit 1; }
[[ -f "$R/.magicc_vv_done" ]] || { echo "MAGICC-SLR vv re-run and vv_wide rebuild not marked done ($R/.magicc_vv_done). STOP"; exit 1; }
say "vv-zenodo re-run, phase ARMS | commit $(git rev-parse --short HEAD) | load $(uptime | sed 's/.*load averages*: //')"
[[ -e "$Q" ]] && { say "$Q already exists -- refusing to overwrite a quarantine. STOP"; exit 1; }
mkdir -p "$Q"; touch "$MARK"
find outputs -maxdepth 1 -type f \( -name "*${T}*" -o -name "*vv*" -o -name "*oldbrick*" \) \
     -newer outputs/mcmc/chain_${T}_seed2026_n2000000.csv > "$Q/.snapshot_list"
find figures benchmark -type f >> "$Q/.snapshot_list"
ls data/comparison/magicc_*vv*.csv >> "$Q/.snapshot_list" 2>/dev/null
sort -u -o "$Q/.snapshot_list" "$Q/.snapshot_list"
rsync -a --files-from="$Q/.snapshot_list" ./ "$Q/"
say "snapshot: $(wc -l < "$Q/.snapshot_list" | tr -d ' ') files -> $Q"

stream_fair(){ local lg=outputs/log_vvz_fair.txt; : > "$lg"
  for s in $SSPS $MARKERS; do step "ladrillo $s FaIR (tapped)" "$lg" $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s --tap; done
  for s in $SSPS; do step "ladrillo $s FaIR (no tap)" "$lg" $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s; done
  for s in $SSPS; do step "ladrillo $s FaIR (tapped, const Greenland amp)" "$lg" \
      env LADRILLO_GIS_SHAPE=gis_amp_shape_const $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s --tap; done
}
stream_magicc(){ local lg=outputs/log_vvz_magicc.txt; : > "$lg"
  for s in $MARKERS; do
    step "ladrillo $s MAGICC climate (spliced)" "$lg" $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s --climate=magicc --tap
    step "ladrillo $s MAGICC climate (raw)"     "$lg" $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s --climate=magicc --forcing=raw --tap
  done
}
stream_brick(){ local lg=outputs/log_vvz_brick.txt; : > "$lg"
  for s in $MARKERS; do
    step "BRICK 2.0 $s FaIR"           "$lg" $J julia/scope_slr_fairunc_oldbrick.jl --ssp=$s
    step "BRICK 2.0 $s MAGICC climate" "$lg" $J julia/scope_slr_fairunc_oldbrick.jl --ssp=$s --climate=magicc
  done
  step "vv glaciers to 2300" "$lg" $J julia/project_ssps_gsic_2300.jl --set=vv
}
stream_fair & P1=$!; stream_magicc & P2=$!; stream_brick & P3=$!
say "streams: fair $P1, magicc $P2, brick $P3"
wait $P1 $P2 $P3
step "[CONDITIONED-PREDICTED] SSP joint cells vs the 10-08e prediction" "$LOG" python python/gate_conditioned_predicted.py
say "=== ARMS DONE, $(nfails) failed step(s). Next: '$0 downstream' ==="
exit "$(nfails)"
fi

## ======================================== PHASE: downstream ==========================================
say "vv-zenodo re-run, phase DOWNSTREAM | commit $(git rev-parse --short HEAD)"
[[ -f "$Q/.snapshot_list" ]] || { say "no snapshot at $Q -- run the arms phase first. STOP"; exit 1; }
lg=outputs/log_vvz_downstream.txt; : > "$lg"
step "vv model comparison"         "$lg" python python/vv_model_comparison.py --tag=$T
step "ladrillo model comparison"   "$lg" python python/ladrillo_model_comparison.py --tag=$T
step "memo figures"                "$lg" python python/plot_ladrillo_memo_figures.py --tag=$T
step "vv comparison figures"       "$lg" python python/plot_model_comparison_components.py --tag=$T --set=vv --year=all
step "vv trajectories"             "$lg" python python/plot_future_components.py --tag=$T --set=vv
step "vv gsic ladrillo-only"       "$lg" python python/plot_vv_gsic_wr_vs_ladrillo.py --tag=$T --ladrillo-only
step "climate swap"                "$lg" python python/plot_vv_climate_swap.py --tag=$T --year=all
step "responsiveness"              "$lg" python python/plot_vv_responsiveness.py --tag=$T
step "paper: vv comparison"        "$lg" python python/plot_model_comparison_components.py --tag=$T --set=vv --year=all --paper
step "paper: vv trajectories"      "$lg" python python/plot_future_components.py --tag=$T --set=vv --paper
step "paper: vv gsic"              "$lg" python python/plot_vv_gsic_wr_vs_ladrillo.py --tag=$T --ladrillo-only --paper
step "paper: responsiveness"       "$lg" python python/plot_vv_responsiveness.py --tag=$T --paper
step "regrowth attribution"        "$lg" python python/verify_magicc_regrowth_attribution.py --tag=$T
step "philosophy arms"             "$lg" python python/diag_brick_philosophy_arms.py --tag=$T
step "paired tap statistics (Sect. 2.2.2)" "$lg" python python/diag_tap_paired_contribution.py
step "benchmark (refresh)"         "$lg" python python/bench_ladrillo.py --tag=$T

## --- prune the snapshot to what moved ----------------------------------------------------------------
moved=0; same=0
while IFS= read -r f; do
  if [[ -f "$f" ]] && cmp -s "$f" "$Q/$f"; then rm -f "$Q/$f"; same=$((same+1)); else moved=$((moved+1)); fi
done < "$Q/.snapshot_list"
find "$Q" -type d -empty -delete
grep -vxF -f "$Q/.snapshot_list" <(find outputs figures benchmark data/comparison -maxdepth 2 -type f -newer "$MARK" -not -path "$Q/*" -not -path "$R/*" -not -path "$QC/*" | sort) \
  > "$Q/.touched_not_snapshotted" || true
say "quarantine: $moved pre-fix files kept in $Q, $same unchanged copies pruned"
say "touched but NOT snapshotted: $(wc -l < "$Q/.touched_not_snapshotted" | tr -d ' ')"
say "=== DONE, $(nfails) failed step(s). Next: the paper-number diff ==="
exit "$(nfails)"
