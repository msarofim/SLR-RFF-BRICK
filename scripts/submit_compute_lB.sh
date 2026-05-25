#!/bin/bash
#SBATCH --job-name=brick_lB_postpr93
#SBATCH --account=torch_pr_1041_general
#SBATCH --partition=cs
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=2:00:00
#SBATCH --output=/scratch/ms17839/SLR-RFF-BRICK/logs/brick_lB_postpr93_%j.out
#SBATCH --error=/scratch/ms17839/SLR-RFF-BRICK/logs/brick_lB_postpr93_%j.err
#
# Recompute baseline log-likelihood l_B(theta_i) for every BRICK posterior
# member under the post-PR#93 (raddleverse/MimiBRICK.jl#93) joint posterior
# installed 2026-05-22. The previous brick_lB_per_post_dangendorf.csv was
# computed against the pre-PR#93 posterior; using it with the new
# parameters_subsample_brick.csv would silently produce nonsense weights.

set -euo pipefail

cd /scratch/ms17839/SLR-RFF-BRICK

mkdir -p outputs logs

echo "JOB: ${SLURM_JOB_NAME} (${SLURM_JOB_ID})"
echo "NODE: $(hostname)"
echo "START: $(date)"

julia --project=julia julia/compute_lB_per_post.jl \
  --posterior data/MimiBRICK/parameters_subsample_brick.csv \
  --obs dangendorf \
  --obs-path data/observations/dangendorf_2024_gmsl.csv \
  --output outputs/brick_lB_per_post_dangendorf_postpr93.csv \
  --start-year 1850 --end-year 2100 \
  --rcp RCP45

echo "END: $(date)"
