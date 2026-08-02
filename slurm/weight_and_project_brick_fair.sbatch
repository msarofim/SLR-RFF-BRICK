#!/bin/bash
# Conditional-Wong forward propagation + coupled SLR bands (single job), optional paired pulse arm.
#   Smoke:        DRAWS=200 CONFIGS=5   sbatch slurm/weight_and_project_brick_fair.sbatch
#   Full (bands): DRAWS=2000 CONFIGS=all sbatch slurm/weight_and_project_brick_fair.sbatch
#   Full (bands + pulse marginals in ONE pass, 2 runs/pair):
#                 DRAWS=2000 CONFIGS=all PULSE=on sbatch --time=06:00:00 slurm/weight_and_project_brick_fair.sbatch
#   Pulse on the deterministic basis (driver-comparable medians):
#                 DRAWS=2000 CONFIGS=all PULSE=on BASIS=_nonoise_flatsolar sbatch --time=06:00:00 slurm/...
# Runs to 2300: bands-only ≈1.68M (~5 ms/run Torch ≈ 2.3 h); PULSE=on doubles it (≈4.7 h -> request 6 h,
# cpu_short MaxWall 6 h; if headroom is a concern split by CONFIGS or use partition cs).
# ZERO-PULSE wiring test (cheap, run once after any driver change): DRAWS=20 CONFIGS=3 PULSE=zero
#SBATCH --job-name=wpf_brick
#SBATCH --account=torch_pr_1041_general
#SBATCH --partition=cpu_short
#SBATCH --time=04:00:00
#SBATCH --mem=16G
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
PULSE=${PULSE:-off}
BASIS=${BASIS:-}
OUTTAG=${OUTTAG:-}
echo "host=$(hostname) draws=$DRAWS configs=$CONFIGS pulse=$PULSE basis='$BASIS' outtag='$OUTTAG' start=$(date +%H:%M:%S)"
julia --project=julia_v2 julia/weight_and_project_brick_fair.jl 2000 2026 \
    --amp-mu=1.08 --amp-sigma=0.15 --draws="$DRAWS" --configs="$CONFIGS" --ess-target=0.6 \
    --pulse="$PULSE" --basis="$BASIS" --out-tag="$OUTTAG"
echo "done=$(date +%H:%M:%S)"
