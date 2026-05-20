#!/bin/bash
#SBATCH --job-name=brick_pulse_anova
#SBATCH --account=torch_pr_1041_general
#SBATCH --partition=cpu_short
#SBATCH --time=00:30:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --output=logs/brick_pulse_anova_%j.out
#SBATCH --error=logs/brick_pulse_anova_%j.err
#
# Step 2 of the pulse-SLR 4-way H-S:
#   1. Extract .npy files from the FaIR ANOVA pulse cube (NPZ.jl can't parse
#      numpy <U keys; same workaround as the baseline cube).
#   2. Run paired BRICK on the 13,500 ANOVA tuples against the pulse cube.
#
# No Wong weighting at this step — the marginal-decomp script inherits
# w_norm from the baseline weighted CSV (same tuples, same posterior).
#
# Inputs:
#   outputs/rff_anova_subset_pulse_stoch_to2300.npz   (from job 8832865)
#   outputs/anova_metadata.csv                        (existing)
#
# Output:
#   outputs/brick_anova_pulse_long_2300.csv           ~63 MB, 13,500 rows × 451 yr cols

set -euo pipefail
cd /scratch/ms17839/SLR-RFF-BRICK
mkdir -p logs outputs

set +u; source ~/.bashrc; set -u
conda activate envs/fair
export JULIA_DEPOT_PATH=$SCRATCH/.julia
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export PYTHONUNBUFFERED=1

CUBE_STEM=outputs/rff_anova_subset_pulse_stoch_to2300
POSTERIOR=data/MimiBRICK/parameters_subsample_brick.csv

echo "==============================================="
echo "ANOVA 2300 BRICK on PULSE cube   host=$(hostname)   start=$(date)"
echo "==============================================="

# Step 1: extract .npy files from the pulse cube (NPZ.jl workaround)
echo
echo "=== Step 1: extract .npy files from pulse cube ==="
python -u -c "
import numpy as np
nz = np.load('${CUBE_STEM}.npz')
print('npz keys:', list(nz.keys()))
print('gmst shape:', nz['gmst_traj_rff'].shape, 'dtype:', nz['gmst_traj_rff'].dtype)
stem = '${CUBE_STEM}'
np.save(f'{stem}_gmst.npy',  nz['gmst_traj_rff'].astype(np.float32))
np.save(f'{stem}_ohc.npy',   nz['ohc_traj_rff'].astype(np.float32))
np.save(f'{stem}_years.npy', nz['years'].astype(np.int64))
np.save(f'{stem}_rffs.npy',  nz['unique_rffs'].astype(np.int64))
print('Extracted .npy files for', stem)
"
ls -lh outputs/rff_anova_subset_pulse_stoch_to2300_*.npy

# Step 2: BRICK paired runs over the 13,500 tuples to 2300
echo
echo "=== Step 2: paired BRICK on 13,500 tuples × 1850-2300 against pulse cube ==="
cd julia
time julia --project=. run_mimibrick_paired_explicit.jl \
    --cube      /tmp/unused.npz \
    --npy-stem  ../${CUBE_STEM} \
    --metadata  ../outputs/anova_metadata.csv \
    --posterior ../${POSTERIOR} \
    --output    ../outputs/brick_anova_pulse_long_2300.csv \
    --seed      2026 \
    --start-year 1850 --end-year 2300 \
    --save-trajs true
cd ..

echo
echo "Done: $(date)"
ls -lh outputs/brick_anova_pulse_long_2300.csv 2>/dev/null || true
