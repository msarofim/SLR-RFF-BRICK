#!/bin/bash
# Forward-project total SLR on the 4 continuous-joint posterior chains + split-R̂ the deliverable.
# Streams each 3.4 GB chain (CSV.Rows, low memory), thins post-burn, projects to 2300 with each
# draw's OWN reconstructed forcing. A few min (I/O dominated).
#SBATCH --job-name=jcont_proj
#SBATCH --account=torch_pr_1041_general
#SBATCH --partition=cpu_short
#SBATCH --time=00:45:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=2
#SBATCH --output=/scratch/ms17839/SLR-RFF-BRICK/logs/%x_%j.out
#SBATCH --error=/scratch/ms17839/SLR-RFF-BRICK/logs/%x_%j.err

set -euo pipefail
cd /scratch/ms17839/SLR-RFF-BRICK
mkdir -p logs
set +u; source ~/.bashrc; set -u
export JULIA_DEPOT_PATH=$SCRATCH/.julia
export JULIA_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-2}
julia --project=julia_v2 julia/project_slr_joint_cont.jl --amp-mu=1.08 --amp-sigma=0.15
