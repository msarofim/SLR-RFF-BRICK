#!/bin/bash
## BRICK 2.0 joint band (posterior x FaIR configs) on the three shared SSPs.
## ndraw=1000 MATCHES the shipped panel's thinning, which is what makes [CONTROL] mean something.
set -e
cd /Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
for s in ssp126 ssp245 ssp585; do
  echo "=== $s $(date +%H:%M:%S) ==="
  julia --project=julia_v2 julia/scope_slr_fairunc_oldbrick.jl --ssp=$s --ndraw=1000 \
      > outputs/log_fairunc_oldbrick_${s}.txt 2>&1
  grep -E "SPLICE-MATCH|cells compared" outputs/log_fairunc_oldbrick_${s}.txt
done
echo "ALL DONE $(date +%H:%M:%S)"
