#!/bin/bash
#SBATCH --job-name=lhs10k_brick_sp
#SBATCH --account=torch_pr_1041_general
#SBATCH --partition=cpu_short
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --output=slurm/logs/lhs10k_brick_sp_%j.out
#SBATCH --error=slurm/logs/lhs10k_brick_sp_%j.err

# Small-pulse (0.01 GtC) companion to the LHS-10k baseline ensemble.
# Produces the linear-regime SLR marginal for the poster's Panel D inset.
# Reuses baseline w_norm by tuple-merge (same draws).

set -euo pipefail
cd /scratch/ms17839/SLR-RFF-BRICK
mkdir -p slurm/logs outputs

set +u; source ~/.bashrc; set -u
conda activate envs/fair
export JULIA_DEPOT_PATH=$SCRATCH/.julia
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export PYTHONUNBUFFERED=1

POSTERIOR=data/MimiBRICK/parameters_subsample_brick.csv
METADATA=outputs/lhs10k_metadata.csv
BASELINE_WEIGHTED=outputs/brick_lhs10k_baseline_to2300_weighted.csv

PULSE_STEM=outputs/rff_pulse0p01gtc_stoch_to2300
PULSE_CSV=outputs/brick_lhs10k_pulse0p01gtc_to2300.csv
PULSE_WEIGHTED=outputs/brick_lhs10k_pulse0p01gtc_to2300_weighted.csv

echo "==============================================="
echo "LHS-10k BRICK on 0.01 GtC small-pulse cube"
echo "host=$(hostname)  start=$(date)"
echo "==============================================="

cd julia
time julia --project=. run_mimibrick_paired_explicit.jl \
    --cube      /tmp/unused.npz \
    --npy-stem  ../${PULSE_STEM} \
    --metadata  ../${METADATA} \
    --posterior ../${POSTERIOR} \
    --output    ../${PULSE_CSV} \
    --seed      2026 \
    --start-year 1850 --end-year 2300 \
    --save-trajs true
cd ..
ls -lh ${PULSE_CSV}

echo
echo "=== Propagate baseline w_norm into small-pulse CSV ==="
python -u -c "
import pandas as pd
keys = ['rff_idx','fair_cfg_idx','seed_idx','post_idx']
w = pd.read_csv('${BASELINE_WEIGHTED}', usecols=keys + ['w_norm','log_w','l_FB','l_B'])
p = pd.read_csv('${PULSE_CSV}')
m = p.merge(w, on=keys, how='left', validate='one_to_one')
assert m['w_norm'].notna().all()
m.to_csv('${PULSE_WEIGHTED}', index=False)
print('wrote ${PULSE_WEIGHTED} shape', m.shape)
"
ls -lh ${PULSE_WEIGHTED}
echo "DONE  end=$(date)"
