#!/usr/bin/env bash
# The IC comparison at the calibrator's rho bound (0.99) and two sensitivity bounds.
set -uo pipefail
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
PY=$HOME/climate-env/bin/python3
for r in 0.99 0.95 0.90; do
  echo "=== rho-max $r $(date)"
  $PY python/ic_ladrillo_vs_brick20.py --rho-max=$r > logs/ic_ladrillo_vs_brick20_rho$r.log 2>&1
  echo "exit $? $(date)"
done
echo DONE
