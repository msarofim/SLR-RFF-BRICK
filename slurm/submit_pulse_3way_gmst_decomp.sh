#!/bin/bash
#SBATCH --job-name=gmst3way
#SBATCH --account=torch_pr_1041_general
#SBATCH --partition=cpu_short
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=24G
#SBATCH --output=slurm/logs/gmst3way_%j.out
#SBATCH --error=slurm/logs/gmst3way_%j.err

set -euo pipefail

cd /scratch/ms17839/SLR-RFF-BRICK
mkdir -p slurm/logs

source /share/apps/anaconda3/2025.06/etc/profile.d/conda.sh
conda activate /scratch/ms17839/SLR-RFF-BRICK/envs/fair

echo "node=$(hostname)  start=$(date)"
python python/scripts/run_pulse_3way_gmst_decomp.py
echo "end=$(date)"
