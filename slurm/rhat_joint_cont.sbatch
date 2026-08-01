#!/bin/bash
# Split-R-hat convergence diagnostic for the 4 continuous-joint production chains.
# Chunked+thinned read of the 3.4 GB chains (low memory); a few min, but run off the login node.
#SBATCH --job-name=jcont_rhat
#SBATCH --account=torch_pr_1041_general
#SBATCH --partition=cpu_short
#SBATCH --time=00:30:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=2
#SBATCH --output=/scratch/ms17839/SLR-RFF-BRICK/logs/%x_%j.out
#SBATCH --error=/scratch/ms17839/SLR-RFF-BRICK/logs/%x_%j.err

set -euo pipefail
cd /scratch/ms17839/SLR-RFF-BRICK
mkdir -p logs
set +u; source ~/.bashrc; set -u
conda activate /scratch/ms17839/SLR-RFF-BRICK/envs/fair
export PYTHONUNBUFFERED=1
python python/rhat_joint_cont.py 4000000
