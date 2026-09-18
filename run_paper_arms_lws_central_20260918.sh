#!/bin/bash
## RE-RUN EVERY PROJECTION ARM BEHIND THE GMD PAPER'S FIGURES ON LWS_MODE = :central (Marcus 2026-09-18),
## then the figures and the benchmark. Hindcast arms (FIG 1, Tables 4-5) do NOT depend on the LWS mode
## (the hindcast total uses the OBSERVED series) and are not re-run.
##
##   Ladrillo (scope_slr_fair_uncertainty.jl, ~4 min each):  7 vv markers + 3 SSPs (FaIR climate, tapped)
##                                                          + ssp126/245/585 x {spliced, raw} MAGICC climate
##   BRICK 2.0 (scope_slr_fairunc_oldbrick.jl, ~30 s each):  7 vv + 3 SSPs (FaIR) + 7 vv + ssp245/585 (MAGICC)
##   then build_l24_deliverable_doc.sh's figure + benchmark steps (NOT its docx step — the paper is
##   Marcus's docx; the documentation memo's docx is rebuilt only on request).
## ~1.5 h on the laptop. Torch verdict: not needed (single-core arms, no licence, 1.5 h).
## Run from a FROZEN copy of the drivers: do not edit julia/*.jl while this runs.
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T=L24
LOG=outputs/log_paper_arms_lws_central_20260918.txt
J="julia --project=julia_v2"
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }
step(){ local nm="$1"; shift; say "START  $nm"
  if "$@" >> "$LOG" 2>&1; then say "OK     $nm"; else say "FAILED $nm (rc=$?)"; fi; }
: > "$LOG"
say "paper arms on LWS_MODE=:central | commit $(git rev-parse --short HEAD)"
for m in vvVL vvL vvLN vvML vvM vvHL vvH ssp126 ssp245 ssp585; do
  step "ladrillo $m (FaIR climate, tapped)" $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$m --tap
done
for s in ssp126 ssp245 ssp585; do
  step "ladrillo $s MAGICC climate (spliced)" $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s --climate=magicc --tap
  step "ladrillo $s MAGICC climate (raw)"     $J julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s --climate=magicc --forcing=raw --tap
done
for m in vvVL vvL vvLN vvML vvM vvHL vvH; do
  step "brick2 $m (FaIR climate)" $J julia/scope_slr_fairunc_oldbrick.jl --ssp=$m
done
for s in ssp126 ssp245 ssp585; do
  step "brick2 $s (FaIR climate, ndraw 1000)" $J julia/scope_slr_fairunc_oldbrick.jl --ssp=$s --ndraw=1000
done
for s in vvVL vvLN vvL vvML vvM vvHL vvH ssp245 ssp585; do
  step "brick2 $s MAGICC climate" $J julia/scope_slr_fairunc_oldbrick.jl --ssp=$s --climate=magicc
done
say "=== arms done; figures + benchmark next (build_l24_deliverable_doc.sh figure steps) ==="
