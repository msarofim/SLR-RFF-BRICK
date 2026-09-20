#!/bin/bash
## IC test (AIC/BIC vs BRICK 2.0) for one posterior tag, three rho bounds. Usage: scripts/run_ic_arms.sh L26
## Prerequisite: julia --project=julia_v2 julia/ic_hindcast_residuals.jl --tag=<TAG>  (90 s, gated)
set -uo pipefail
cd "$(dirname "$0")/.."
T="${1:-L24}"
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
PY=$HOME/climate-env/bin/python3
mkdir -p logs
for r in 0.99 0.95 0.90; do
  echo "=== $T rho-max $r $(date '+%H:%M:%S')"
  $PY python/ic_ladrillo_vs_brick20.py --tag=$T --rho-max=$r > logs/ic_ladrillo_vs_brick20_${T}_rho$r.log 2>&1
  echo "exit $? $(date '+%H:%M:%S')"
done
echo DONE
