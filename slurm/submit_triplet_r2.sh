#!/bin/bash
#SBATCH --job-name=cube_r2
#SBATCH --account=torch_pr_1041_general
#SBATCH --partition=cpu_short
#SBATCH --time=05:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --array=0-2
#SBATCH --output=/scratch/ms17839/SLR-RFF-BRICK/slurm/logs/cube_r2_%A_%a.out
#SBATCH --error=/scratch/ms17839/SLR-RFF-BRICK/slurm/logs/cube_r2_%A_%a.err
# Build the paired r2 triplet (one arm per array task, parallel) on Torch.
# realization r2: provenance-embedded cubes (cell_seeds etc). CO2 stays 0.01 Gt
# (float32-resolved); CH4 is 1 Tg (the 0.01 Tg cube was float32-corrupted).
set -euo pipefail
set +u; source ~/.bashrc; set -u
conda activate /scratch/ms17839/SLR-RFF-BRICK/envs/fair
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
cd /scratch/ms17839/FaIRtoFrEDI
META=fair_outputs/metadata_v145/lhs10ks_metadata_v145.csv
case ${SLURM_ARRAY_TASK_ID} in
  0) ARGS="--output-tag lhs10ks_baseline_flat2015_r2 --metadata-csv $META --pulse-year 2030" ;;
  1) ARGS="--output-tag lhs10ks_pulse_co2_pos_001gt_flat2015_r2 --metadata-csv $META --pulse-specie 'CO2 FFI' --pulse-size 0.01 --pulse-year 2030" ;;
  2) ARGS="--output-tag lhs10ks_pulse_ch4_pos_1tg_flat2015_r2 --metadata-csv $META --pulse-specie CH4 --pulse-size 1.0 --pulse-year 2030" ;;
  *) echo "bad array idx"; exit 1 ;;
esac
echo "task ${SLURM_ARRAY_TASK_ID}: $ARGS  host=$(hostname) start=$(date)"
eval python lhs_climate_v145_meta.py $ARGS
echo "TASK ${SLURM_ARRAY_TASK_ID} DONE: $(date)"
