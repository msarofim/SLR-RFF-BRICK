#!/bin/bash
## L24 van Vuuren arms on MAGICC's OWN climate — 7 markers x 2 forcing conventions.
##
## WHY. Ladrillo-vs-MAGICC on the vv markers is a TWO-variable comparison: MAGICC computes its
## own climate from emissions and runs 0.38-0.93 K COLDER at 2300 on the declining markers. This
## arm holds the MODULE axis and moves only the climate, so a residual difference is structural.
## ⚠ L21 and L23 have this set; L24 did not, so any matched-climate statement about the SHIPPED
## vintage was unsupported until now.
## Replicates L23's arm set exactly (raw AND spliced) so the vintages stay comparable.
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
LOG=outputs/log_l24_vv_magiccclim.txt; : > "$LOG"
J="julia --project=julia_v2"
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }
for s in vvVL vvL vvLN vvML vvM vvHL vvH; do
  for fc in spliced raw; do
    say "START $s $fc"
    if $J julia/scope_slr_fair_uncertainty.jl --tag=L24 --ssp=$s --tap \
         --climate=magicc --forcing=$fc >> "$LOG" 2>&1
    then say "OK    $s $fc"; else say "FAILED $s $fc (rc=$?)"; fi
  done
done
say "DONE"
