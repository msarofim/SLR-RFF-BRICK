#!/bin/bash
## Joint band on the TAPPED Greenland arm, L21, all three SSPs.
## Closes the 6 cells ladrillo_model_comparison.py had to hold on the fixed band
## because scope_slr_fair_uncertainty.jl had no tap support (added 2026-08-30).
## Outputs carry _tap<cell> so they cannot overwrite the untapped files.
set -e
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T=${TAG:-L21}
for s in ssp126 ssp245 ssp585; do
  echo "=== $s $(date +%H:%M:%S) ==="
  julia --project=julia_v2 julia/scope_slr_fair_uncertainty.jl --tag=$T --ssp=$s --tap \
      > outputs/log_fairunc_tap_${T}_${s}.txt 2>&1
  echo "    done $(date +%H:%M:%S)"
done
echo "ALL DONE $(date +%H:%M:%S)"
