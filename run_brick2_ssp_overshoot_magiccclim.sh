#!/bin/bash
## BRICK 2.0 on MAGICC's OWN climate, SSP overshoot pair — the companion to
## run_l24_ssp_overshoot_magiccclim.sh. See that script's header for the design.
## ⚠ BRICK 2.0's level driver gained --climate=magicc for this run; Ladrillo's had it
## since 2026-08-31c. Only the JOINT arm moves: FIXED stays on FaIR's mean path, which is
## why [CONTROL] remains a live gate here and its passing shows the swap was contained.
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
LOG=outputs/log_ssp_overshoot_magiccclim_brick2.txt; : > "$LOG"
J="julia --project=julia_v2"
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }
for s in ssp534over ssp126; do
  say "START brick2 $s"
  if $J julia/scope_slr_fairunc_oldbrick.jl --ssp=$s --climate=magicc >> "$LOG" 2>&1
  then say "OK    brick2 $s"; else say "FAILED brick2 $s (rc=$?)"; fi
done
say "DONE brick2"
