#!/bin/bash
#SBATCH --job-name=fair_lhs
#SBATCH --account=torch_pr_1041_general
#SBATCH --partition=cpu_short
#SBATCH --time=03:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --array=0-19
#SBATCH --output=logs/fair_%A_%a.out
#SBATCH --error=logs/fair_%A_%a.err
#
# 20-job array running FaIR on 100 RFFs per chunk, --n-seeds 10
# Total: 2000 LHS RFFs * 10 stochastic seeds = 20,000 FaIR runs
# Expected wallclock: ~1 hr per job; full array ~1 hr if jobs run in parallel.
#
# Submit:    sbatch slurm/submit_lhs_fair.sh
# Status:    squeue -u $USER
# Cancel:    scancel <jobid>
# After all jobs finish, run: sbatch slurm/submit_concat.sh --dependency=afterok:<jobid>

set -euo pipefail
cd /scratch/ms17839/SLR-RFF-BRICK

# Make sure log dir exists (sbatch fails if missing)
mkdir -p logs outputs

# Conda + Julia env (.bashrc has eval and JULIA_DEPOT_PATH)
set +u; source ~/.bashrc; set -u
conda activate $SCRATCH/SLR-RFF-BRICK/envs/fair

# Pin BLAS thread count to allotted CPUs (avoid oversubscription)
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export PYTHONUNBUFFERED=1   # flush stdout/stderr live so logs are tailable

# Each task handles 100 RFFs out of 2000
TASK=${SLURM_ARRAY_TASK_ID}
START=$((TASK * 100 + 1))
END=$((START + 99))

echo "==============================================="
echo "Task $TASK: RFFs $START to $END"
echo "Host: $(hostname)"
echo "Started: $(date)"
echo "JULIA_DEPOT_PATH=$JULIA_DEPOT_PATH"
echo "Python: $(which python)"
echo "==============================================="

python python/lhs_climate_pilot.py \
    --rff-range ${START}:${END} \
    --stochastic --n-seeds 10 \
    --output-tag chunk_${TASK} \
    --batch-size 5

echo "==============================================="
echo "Finished: $(date)"
echo "==============================================="
