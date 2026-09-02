#!/bin/bash
## MATCHED-dT OVERSHOOT PAIR — Ladrillo L24 + BRICK 2.0 on an identical climate.
## ssp534overMATCH = ssp126 forcing + max(ERF_534-ERF_126,0); GSAT relaxes back FROM ABOVE
## (+0.042 K @2150, +0.020 @2300) instead of the native pair's -0.102/-0.133 K inversion.
## ⚠ IDEALISED arm — never quote it as SSP5-3.4-OS.
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
LOG=outputs/log_matched_dt_arms.txt; : > "$LOG"
J="julia --project=julia_v2"
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }
## Ladrillo on the matched arm (the reference ssp126_nomarker arm already exists).
say "START ladrillo ssp534overMATCH"
if $J julia/scope_slr_fair_uncertainty.jl --tag=L24 --ssp=ssp534overMATCH --tap >> "$LOG" 2>&1
then say "OK    ladrillo ssp534overMATCH"; else say "FAILED ladrillo (rc=$?)"; fi
## BRICK 2.0 — the INDEPENDENT comparator (MAGICC shares Ladrillo's glacier law).
for s in ssp126_nomarker ssp534over_nomarker ssp534overMATCH; do
  say "START brick2.0 $s"
  if $J julia/scope_slr_fairunc_oldbrick.jl --ssp=$s >> "$LOG" 2>&1
  then say "OK    brick2.0 $s"; else say "FAILED brick2.0 $s (rc=$?)"; fi
done
say "DONE"
