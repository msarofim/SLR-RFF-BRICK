#!/bin/bash
#SBATCH --job-name=anova_2300
#SBATCH --account=torch_pr_1041_general
#SBATCH --partition=cpu_short
#SBATCH --time=00:30:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --output=logs/anova_2300_%j.out
#SBATCH --error=logs/anova_2300_%j.err
#
# Step 2-3 of the 4-way SLR H-S extension to 2300:
#   1. Run paired BRICK on the new ANOVA-subset 2300 cube (13,500 tuples).
#   2. Apply Wong importance weighting to the output.
#
# Inputs:
#   outputs/rff_anova_subset_stoch_to2300.npz         (1.2 GB, 4D cube, from 8822531)
#   outputs/anova_metadata.csv                        (existing)
#   outputs/brick_lB_per_post.csv                     (existing)
#
# Outputs:
#   outputs/brick_anova_long_2300.csv             -- unweighted, ~25 MB
#   outputs/brick_anova_long_2300_weighted.csv    -- with l_FB, l_B, log_w, w_norm

set -euo pipefail
cd /scratch/ms17839/SLR-RFF-BRICK
mkdir -p logs outputs

set +u; source ~/.bashrc; set -u
conda activate envs/fair
export JULIA_DEPOT_PATH=$SCRATCH/.julia
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export PYTHONUNBUFFERED=1

CUBE_STEM=outputs/rff_anova_subset_stoch_to2300   # .npy files alongside (NPZ.jl can't parse numpy <U keys)
POSTERIOR=data/MimiBRICK/parameters_subsample_brick.csv

echo "==============================================="
echo "ANOVA 2300 BRICK + Wong   host=$(hostname)   start=$(date)"
echo "==============================================="

# Step 1: BRICK paired runs over the 13,500 ANOVA tuples to 2300
echo
echo "=== Step 1: paired BRICK on 13,500 tuples × 1850-2300 ==="
cd julia
time julia --project=. run_mimibrick_paired_explicit.jl \
    --cube      /tmp/unused.npz \
    --npy-stem  ../${CUBE_STEM} \
    --metadata  ../outputs/anova_metadata.csv \
    --posterior ../${POSTERIOR} \
    --output    ../outputs/brick_anova_long_2300.csv \
    --seed      2026 \
    --start-year 1850 --end-year 2300 \
    --save-trajs true
cd ..

# Step 2: Wong importance weighting
echo
echo "=== Step 2: Wong importance weighting ==="
python python/apply_wong_weights.py \
    --input   outputs/brick_anova_long_2300.csv \
    --posterior ${POSTERIOR} \
    --lB      outputs/brick_lB_per_post.csv \
    --output  outputs/brick_anova_long_2300_weighted.csv

echo
echo "Done: $(date)"
ls -lh outputs/brick_anova_long_2300.csv outputs/brick_anova_long_2300_weighted.csv 2>/dev/null
