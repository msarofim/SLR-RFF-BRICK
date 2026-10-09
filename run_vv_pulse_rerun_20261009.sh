#!/bin/bash
## THE VAN VUUREN PULSE ARC, RE-RUN DOWNSTREAM OF THE 10-08 PULSE CUBES (Marcus 2026-10-09: "start the pulse arc
## downstream rerun"; rulings: posterior L27 = Ladrillo v1.2, record conditioning own-config drop, the MAGICC-climate
## Ladrillo arm on 2,000 draws paired with the FaIR arm).
## WHY. Every live pulse product (09-04..09-07) was built on the Smith-2024-history + harmonized-tail vv cubes, two
## generations stale: the 10-02 CMIP7 rebuild and the 10-08 published-emissions rebuild both re-made the 112 pulse cubes
## and re-ran nothing downstream (run_vv_cmip7_rerun_20261007.sh claimed every fair_*_vv* reader and missed the arc).
## MAGICC's pulse scenarios were built from the 08-31 harmonized slr_vv_and_ssps.csv; FACTS's pulse climate from the
## Smith cubes. Spec unchanged: 1 GtCO2 / 0.01 GtCH4 at 2030, seven markers, joint driver, tapped Greenland.
## PHASES:
##   quarantine  move every stale pulse product, in all four repos, to <repo quarantine>/20261009_vv_pulse_smith_harmonized
##   magicc      stage 4: pulse scenarios from the live (zenodo) slr_vv_and_ssps.csv -> 14 MAGICC runs (n=600) ->
##               extract (cells/gates/paths) -> vv_pulse_wide_20261009 (feeds the /magiccclim arms)
##   facts       stage 5: pulse climate from the live cubes -> configs -> 21 Docker experiments -> extract
##   brick       stage 3: BRICK 2.0 on the live FaIR pulse cubes (B20; not conditioned, per the 10-08 ruling)
##   (ladrillo, magiccclim, downstream: added after the L27 port of scope_slr_pulse_vv.jl)
## Torch verdict: not needed and not possible -- MAGICC is a licensed local binary, FACTS needs the local Docker; the
## Julia arms are minutes. MAGICC runs with 6 workers (not .env's 8): FACTS, BRICK 2.0 and the Ladrillo port run alongside.
## Run from FROZEN copies: the Julia drivers and 302d are copied to _frozen_*_20261009 before the runs start.
set -uo pipefail
PHASE="${1:?usage: $0 quarantine|magicc|facts|brick}"
cd "$(dirname "$0")"
SLR=$PWD
FTF=$(cd ../FaIRtoFrEDI && pwd)
MAG=$(cd ../MAGICC/slr-refresh && pwd)
FACTS=$(cd ../facts && pwd)
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
TAGQ=20261009_vv_pulse_smith_harmonized
SQ=$SLR/outputs/quarantine/$TAGQ
FQ=$FTF/magicc_comparison/processed/quarantine/$TAGQ
GQ=$MAG/data/quarantine/$TAGQ
XQ=$FACTS/quarantine/$TAGQ
MCODES="VL L LN ML M HL H"
PY=~/miniforge3/envs/slr-refresh-2025/bin/python      # FTF magicc_comparison + MAGICC
J="julia --project=julia_v2"
MAGICC_WORKERS=6
LOG=$SLR/outputs/log_vv_pulse_rerun_20261009.txt
say(){ echo "[$(date '+%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }
step(){ local nm="$1" lg="$2"; shift 2; say "START  $nm"
  if "$@" >> "$lg" 2>&1; then say "OK     $nm"; else say "FAILED $nm (rc=$?)"; echo "$nm" >> "$LOG.fails.$PHASE"; fi; }
psize(){ [[ "$1" == CO2 ]] && echo 1 || echo 0.01; }
[[ "$PHASE" =~ ^(quarantine|magicc|facts|brick)$ ]] || { echo "phase must be quarantine|magicc|facts|brick"; exit 1; }
rm -f "$LOG.fails.$PHASE"

## ======================================== PHASE: quarantine ==========================================
if [[ "$PHASE" == quarantine ]]; then
  for q in "$SQ" "$FQ" "$GQ" "$XQ"; do [[ -e "$q" ]] && { say "$q exists -- refusing to overwrite a quarantine. STOP"; exit 1; }; done
  mkdir -p "$SQ/outputs" "$SQ/logs" "$SQ/deliverables" "$FQ/figures" "$GQ/processed/emissions" "$GQ/notebooks" "$XQ/experiments"
  ## SLR (quarantined data untracked, README + SHA256SUMS tracked -- this repo's convention)
  mv outputs/pulse_ladrillo_*_vv* outputs/pulse_brick2_*_vv* outputs/log_pulse_*magiccclim* "$SQ/outputs/"
  mv logs/lad_*.log logs/b2_*.log "$SQ/logs/"
  mv deliverables/pulse_model_differences_tables.md deliverables/pulse_model_differences_L24_section.md "$SQ/deliverables/"
  ## FaIRtoFrEDI (quarantined data TRACKED -- that repo's convention): git mv when tracked, mv otherwise
  fmv(){ local src="$1" dst="$2"
    if git -C "$FTF" ls-files --error-unmatch "$src" >/dev/null 2>&1; then git -C "$FTF" mv "$src" "$dst"; else mv "$FTF/$src" "$FTF/$dst"; fi; }
  P=magicc_comparison/processed
  for f in $(cd "$FTF" && ls $P/pulse_magicc_{cells,gates,paths}_vv*_n600.csv $P/pulse_manifest_vv*_{co2,ch4}_headline.csv \
               $P/pulse_facts_{cells,gates}_vv_2030_n200.csv $P/pulse_crossmodel_cells_vv_2030{,_gates}.csv \
               $P/pulse_duration_{cells,gates}_vv_2030.csv $P/diag_igmst_ordering{,_gates}_vv_2030.csv \
               $P/diag_te_ohc_mechanism{,_gates}_vv_2030.csv $P/magiccclim_module_vs_climate*.csv \
               $P/scenario_dependence_2300{,_gates}.csv); do fmv "$f" "$P/quarantine/$TAGQ/"; done
  fmv $P/vv_pulse_wide_20260904 $P/quarantine/$TAGQ/vv_pulse_wide_20260904
  for f in $(cd "$FTF" && ls magicc_comparison/figures/pulse_duration_*); do fmv "$f" "$P/quarantine/$TAGQ/figures/"; done
  ## MAGICC (data/ is untracked)
  mv "$MAG"/data/processed/PULSEVV_vv*_co2_headline_n600_*.csv "$MAG"/data/processed/PULSEVV_vv*_ch4_headline_n600_*.csv "$GQ/processed/"
  mv "$MAG"/data/processed/emissions/slr_vv*_co2headline2030.csv "$MAG"/data/processed/emissions/slr_vv*_ch4headline2030.csv "$GQ/processed/emissions/"
  mv "$MAG"/notebooks/302d_run-magicc-pulse-vv*_headline.log "$GQ/notebooks/" 2>/dev/null
  ## FACTS: input/ + output/ of the 21 pulse experiments (as the 10-08 level rerun did)
  for e in $(cd "$FACTS/experiments" && ls -d global.shared.vv*.p*.2300.n200); do
    mkdir -p "$XQ/experiments/$e"; mv "$FACTS/experiments/$e/input" "$FACTS/experiments/$e/output" "$XQ/experiments/$e/"; done
  for q in "$SQ" "$FQ" "$GQ" "$XQ"; do (cd "$q" && find . -type f ! -name SHA256SUMS ! -name README.md -print0 | sort -z |
    xargs -0 shasum -a 256 > SHA256SUMS); say "quarantined $(($(wc -l < "$q/SHA256SUMS"))) files -> $q"; done
  exit 0
fi

## ======================================== PHASE: magicc (stage 4) ====================================
if [[ "$PHASE" == magicc ]]; then
  lg=$SLR/outputs/log_vvp_magicc.txt; : > "$lg"
  cp "$MAG/notebooks/302d_run-magicc-pulse-vv.py" "$MAG/notebooks/_frozen_302d_20261009.py"
  for M in $MCODES; do for gas in co2 ch4; do
    step "scenario vv$M $gas" "$lg" bash -c "cd '$FTF' && $PY magicc_comparison/build_pulse_scenarios_vv.py --marker=$M --gas=$gas --set=headline --snap"
    step "MAGICC vv$M $gas (n600)" "$lg" bash -c "cd '$MAG/notebooks' && MAGICC_WORKER_NUMBER=$MAGICC_WORKERS MAGICC_VV_MARKER=$M \
      MAGICC_PULSE_GAS=$gas MAGICC_VV_SET=headline MAGICC_PULSE_NCFGS=600 $PY _frozen_302d_20261009.py"
    run=$(ls -t "$MAG"/data/processed/PULSEVV_vv${M}_${gas}_headline_n600_*.csv 2>/dev/null | head -1)
    [[ -n "$run" ]] || { say "no PULSEVV output for vv$M $gas -- STOP"; exit 1; }
    step "extract vv$M $gas" "$lg" bash -c "cd '$FTF' && $PY magicc_comparison/extract_pulse_vv_magicc.py --input '$run' \
      --manifest magicc_comparison/processed/pulse_manifest_vv${M}_${gas}_headline.csv --paths"
  done; done
  for S in CO2 CH4; do step "MAGICC pulse wide $S" "$lg" bash -c "cd '$FTF' && $PY magicc_comparison/build_magicc_pulse_wide_vv.py --specie $S"; done
  say "magicc phase done, $(cat "$LOG.fails.magicc" 2>/dev/null | wc -l | tr -d ' ') failures"; exit 0
fi

## ======================================== PHASE: facts (stage 5) =====================================
if [[ "$PHASE" == facts ]]; then
  lg=$SLR/outputs/log_vvp_facts.txt; : > "$lg"
  source ~/climate-env/bin/activate
  step "FACTS pulse climate (21 arms, n200)" "$lg" bash -c "cd '$FACTS' && python build_pulse_climate_vv.py --all --nsamp=200"
  step "FACTS configs"                     "$lg" bash -c "cd '$FACTS' && python build_shared_configs.py"
  step "FACTS 21 experiments (Docker)"     "$lg" bash -c "cd '$FACTS' && ./run_vv_pulse_facts.sh"
  step "FACTS extract"                     "$lg" bash -c "cd '$FTF' && python magicc_comparison/extract_pulse_vv_facts.py"
  say "facts phase done, $(cat "$LOG.fails.facts" 2>/dev/null | wc -l | tr -d ' ') failures"; exit 0
fi

## ======================================== PHASE: brick (stage 3) =====================================
if [[ "$PHASE" == brick ]]; then
  lg=$SLR/outputs/log_vvp_brick.txt; : > "$lg"
  cp julia/scope_slr_pulse_vv_brick2.jl julia/_frozen_scope_slr_pulse_vv_brick2_20261009.jl
  for M in $MCODES; do for S in CO2 CH4; do
    step "BRICK 2.0 vv$M $S (FaIR)" "$lg" bash -c "$J julia/_frozen_scope_slr_pulse_vv_brick2_20261009.jl --marker=$M --specie=$S \
      --pulse-size=$(psize $S) --ndraw=2000 --tag=B20 > logs/b2_${M}_${S}.log 2>&1"
  done; done
  say "brick phase done, $(cat "$LOG.fails.brick" 2>/dev/null | wc -l | tr -d ' ') failures"; exit 0
fi
