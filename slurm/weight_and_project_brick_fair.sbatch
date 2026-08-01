#!/bin/bash
# Conditional-Wong forward propagation + coupled SLR bands (single job).
#   Smoke:  DRAWS=200 CONFIGS=5   sbatch slurm/weight_and_project_brick_fair.sbatch
#   Full:   DRAWS=2000 CONFIGS=all sbatch slurm/weight_and_project_brick_fair.sbatch
# ~1.68M BRICK runs to 2300 for the full case (~1–2.5 h single-core); fits cpu_short's 4h cap.
#SBATCH --job-name=wpf_brick
#SBATCH --account=torch_pr_1041_general
#SBATCH --partition=cpu_short
#SBATCH --time=04:00:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=2
#SBATCH --output=/scratch/ms17839/SLR-RFF-BRICK/logs/%x_%j.out
#SBATCH --error=/scratch/ms17839/SLR-RFF-BRICK/logs/%x_%j.err

set -euo pipefail
cd /scratch/ms17839/SLR-RFF-BRICK
mkdir -p logs outputs/mcmc
set +u; source ~/.bashrc; set -u
export JULIA_DEPOT_PATH=$SCRATCH/.julia
export JULIA_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-2}

DRAWS=${DRAWS:-2000}
CONFIGS=${CONFIGS:-all}
echo "host=$(hostname) draws=$DRAWS configs=$CONFIGS start=$(date +%H:%M:%S)"
julia --project=julia_v2 julia/weight_and_project_brick_fair.jl 2000 2026 \
    --amp-mu=1.08 --amp-sigma=0.15 --draws="$DRAWS" --configs="$CONFIGS" --ess-target=0.6
echo "done=$(date +%H:%M:%S)"
