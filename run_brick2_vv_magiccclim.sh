#!/bin/bash
## BRICK 2.0 on MAGICC's OWN climate, the seven van Vuuren markers + the two SSPs not yet run
## (2026-09-11, Marcus's 9/11b comment [8]: "a single figure to highlight how the
## MAGICC/BRICK/Ladrillo comparison changes when they all use the MAGICC climate driver").
## Ladrillo already has every marker on MAGICC's climate (run_l24_vv_magiccclim.sh); BRICK 2.0
## had only ssp126/ssp534over (run_brick2_ssp_overshoot_magiccclim.sh). Same driver, same flags.
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
LOG=outputs/log_vv_magiccclim_brick2.txt; : > "$LOG"
J="julia --project=julia_v2"
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }
for s in vvVL vvLN vvL vvML vvM vvHL vvH ssp245 ssp585; do
  say "START brick2 $s"
  if $J julia/scope_slr_fairunc_oldbrick.jl --ssp=$s --climate=magicc >> "$LOG" 2>&1
  then say "OK    brick2 $s"; else say "FAILED brick2 $s (rc=$?)"; fi
done
say "DONE brick2"
