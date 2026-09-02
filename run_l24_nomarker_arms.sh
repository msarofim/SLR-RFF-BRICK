#!/bin/bash
## L24 MARKER-FREE ARMS — the SSPs driven WITHOUT any CMIP7 marker assumption.
##
## Land use is `calculated` from each scenario's own cumulative CO2 AFOLU; Irrigation is ONE
## shared trajectory; Volcanic and Solar were never marker-dependent. See
## notes/note_2026-09-02_marker_free_ssps.md.
##
## ⚠ THIS IS A SENSITIVITY SET, NOT A REPLACEMENT. The shipped drivers stay marker-based.
## The point is to turn the marker ambiguity from a CHOICE into a MEASURED quantity, and to
## test whether the overshoot penalty survives removing the assumption.
##
## ⚠ The posterior is used OFF-DESIGN (identical constrained parameters, different forcing
## treatment). Cost over the constraining period: 2-6 % of the ensemble's own p5-p95 spread,
## smaller than the marker ambiguity it removes. Do not quote an ABSOLUTE number from this set
## without stating the deviation.
##
## ⚠ ALL ARMS TAPPED, matching every other L24 arm.
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T=L24; LOG=outputs/log_l24_nomarker_arms.txt
J="julia --project=julia_v2"
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }
: > "$LOG"
for s in ssp126 ssp245 ssp534over ssp585; do
  say "START  ${s}_nomarker"
  if $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=${s}_nomarker --tap >> "$LOG" 2>&1
  then say "OK     ${s}_nomarker"; else say "FAILED ${s}_nomarker (rc=$?)"; fi
done
say "DONE"
