#!/bin/bash
# Continuous joint FaIR/BRICK calibration (calibrate_mcmc_joint_cont.jl) — SLURM array.
# One chain per array task; SEED = 2026 + array index (matches the 4 overdispersed_starts rows,
# indices 0..3 -> seeds 2026..2029). Outputs are keyed by SEED (chain_<TAG>_seed<SEED>_n<N>.csv,
# adapted_cov_<TAG>_seed<SEED>.csv) so concurrent tasks NEVER collide; all inputs are read-only.
# NITER + TAG are env-overridable so a smoke batch (small NITER, TAG=jcontsmoke) cannot overwrite
# production filenames. Run the exact same script for smoke and production (test what you run).
#
#   Smoke:      NITER=2000 TAG=jcontsmoke sbatch --array=0 slurm/joint_calib_cont.sbatch   # warm depot
#               NITER=2000 TAG=jcontsmoke sbatch --array=1-3 slurm/joint_calib_cont.sbatch # concurrent
#   Production: NITER=<N>  sbatch --array=0-3 slurm/joint_calib_cont.sbatch
#SBATCH --job-name=jcont
#SBATCH --account=torch_pr_1041_general
#SBATCH --partition=cpu_short
#SBATCH --time=04:00:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=2
#SBATCH --output=/scratch/ms17839/SLR-RFF-BRICK/logs/%x_%A_%a.out
#SBATCH --error=/scratch/ms17839/SLR-RFF-BRICK/logs/%x_%A_%a.err

set -euo pipefail
cd /scratch/ms17839/SLR-RFF-BRICK
mkdir -p logs outputs/mcmc
set +u; source ~/.bashrc; set -u          # NYU /etc/bashrc has an unbound var; sandwich required
export JULIA_DEPOT_PATH=$SCRATCH/.julia
export JULIA_NUM_THREADS=1                 # serial MCMC chain
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-2}   # BLAS threads for the AR(1) MvNormal factorization

SEED=$(( 2026 + ${SLURM_ARRAY_TASK_ID:-0} ))
NITER=${NITER:-2000}
TAG=${TAG:-jcont}
AMP_MU=${AMP_MU:-1.08}
AMP_SIGMA=${AMP_SIGMA:-0.15}

echo "host=$(hostname) task=${SLURM_ARRAY_TASK_ID:-NA} seed=$SEED niter=$NITER tag=$TAG amp=N($AMP_MU,$AMP_SIGMA)"
echo "depot=$JULIA_DEPOT_PATH blas_threads=$OPENBLAS_NUM_THREADS start=$(date +%H:%M:%S)"

julia --project=julia_v2 julia/calibrate_mcmc_joint_cont.jl "$NITER" "$SEED" \
    --overdisperse --amp-mu="$AMP_MU" --amp-sigma="$AMP_SIGMA" --tag="$TAG"

echo "done=$(date +%H:%M:%S) exit=$?"
