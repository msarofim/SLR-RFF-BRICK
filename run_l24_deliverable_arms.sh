#!/bin/bash
## L24 DELIVERABLE ARMS — the van Vuuren markers and the MAGICC-climate comparison.
##
## WHY: L24 was promoted champion 2026-09-02, but its postprocess only built the three SSP
## joint bands. The model-description deliverable asks for the van Vuuren markers as the
## PRIMARY projection comparison and for a separate Ladrillo-vs-MAGICC arm on MAGICC's own
## climate. Those exist for L21 and L23 and NOT for L24, so every figure in that document
## would otherwise be drawn on a superseded vintage.
##
## ⚠ The magiccclim arm is the LIKE-FOR-LIKE one: it drives Ladrillo with MAGICC's climate so
## the comparison is not confounded by the forcing (`like_for_like_forcing`). Both the raw and
## spliced forcing conventions are built, matching what L21/L23 have.
##
##   bash run_l24_deliverable_arms.sh
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T=L24
LOG=outputs/log_l24_deliverable_arms.txt
J="julia --project=julia_v2"
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }
step(){ local nm="$1"; shift
  say "START  $nm"
  if "$@" >> "$LOG" 2>&1; then say "OK     $nm"; else say "FAILED $nm (rc=$?)"; fi
}
: > "$LOG"
say "L24 deliverable arms: 7 van Vuuren markers + the MAGICC-climate arm"
for m in vvVL vvL vvLN vvML vvM vvHL vvH; do
  step "van Vuuren $m (FaIR climate)" $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$m
done
for s in ssp126 ssp245 ssp585; do
  step "MAGICC-climate $s (spliced)" $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s --climate=magicc
  step "MAGICC-climate $s (raw)"     $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s --climate=magicc --forcing=raw
done
say "=== DONE. Rebuild the comparisons and figures on L24 next. ==="
