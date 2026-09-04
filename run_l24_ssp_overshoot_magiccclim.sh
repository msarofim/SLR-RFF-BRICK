#!/bin/bash
## L24 + BRICK 2.0 on MAGICC's OWN climate, for the SSP OVERSHOOT PAIR.
##
## WHY. `diag_magicc_overshoot_depth.py` measured MAGICC's real ssp534-over minus ssp126
## overshoot at +0.659 K peak against FaIR's +0.308 K -- 2.1x on an IDENTICAL scenario pair --
## while our 2300 penalty (Ladrillo 2.21 cm paired median, BRICK 2.0 2.57) sits 2.5-5.8x below
## MAGICC-SLR's own 12.75 / 14.28, which is INSIDE SLEIP's published 8-29 cm band. DEPTH and
## MODULE are confounded. This arm holds the module axis and moves only the climate.
## ⚠ The reverse arm is IMPOSSIBLE (MAGICC-SLR consumes MAGICC's own climate module).
## Cubes: magicc_comparison/build_magicc_wide_ssp_overshoot.py ([GATE-REPRO] 4.4e-16 on ssp126).
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
LOG=outputs/log_ssp_overshoot_magiccclim.txt; : > "$LOG"
J="julia --project=julia_v2"
FORCING=spliced          ## the posterior was calibrated on the spliced path
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }
for s in ssp534over ssp126; do
  say "START ladrillo $s"
  if $J julia/scope_slr_fair_uncertainty.jl --tag=L24 --ssp=$s --tap \
       --climate=magicc --forcing=$FORCING >> "$LOG" 2>&1
  then say "OK    ladrillo $s"; else say "FAILED ladrillo $s (rc=$?)"; fi
done
say "DONE ladrillo"
