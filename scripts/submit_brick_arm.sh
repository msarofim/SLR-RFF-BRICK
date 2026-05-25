#!/bin/bash
#SBATCH --job-name=brick_arm
#SBATCH --account=torch_pr_1041_general
#SBATCH --partition=cs
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=8:00:00
#SBATCH --output=/scratch/ms17839/SLR-RFF-BRICK/logs/brick_%x_%j.out
#SBATCH --error=/scratch/ms17839/SLR-RFF-BRICK/logs/brick_%x_%j.err
#
# submit_brick_arm.sh -- single-arm BRICK driver run on Torch.
#
# Each job consumes one FaIR cube .npz and writes one BRICK CSV. Run 18
# in parallel (9 LHS-10k arms + 9 ANOVA-18k arms) by submitting this 18
# times via submit_all_brick_arms.sh.
#
# Required env vars (passed by submit_all_brick_arms.sh):
#   CUBE         absolute path to cube .npz
#   METADATA     absolute path to metadata CSV
#   OUTPUT       absolute path to output CSV
#   POSTERIOR    absolute path to BRICK posterior CSV
#   YR_START     first year (1850)
#   YR_END       last year (2300 for LHS, 2100 OK for ANOVA — keep 2300 for consistency)
#   SAVE_TRAJS   "true" to write per-year total SLR columns (slr_<y>)
#   SAVE_COMP    "true" to write per-year per-component columns (te_<y>, ais_<y>, ...)
#
# Usage:
#   sbatch --job-name=lhs10k_baseline \
#     --export=ALL,CUBE=/scratch/.../cube_v145_lhs10k_baseline.npz,... \
#     scripts/submit_brick_arm.sh
#
# Notes:
# - Memory: ~2-3 GB peak for LHS-10k, ~5-6 GB for ANOVA-18k. 8G is a safe cap.
# - Wall: LHS-10k ~1 hr, ANOVA-18k ~5 hr. 8 hr cap is conservative.
# - Partition cs vs cpu_short: cs has 513 GB/node available, no per-job cap.

set -euo pipefail

cd /scratch/ms17839/SLR-RFF-BRICK

mkdir -p "$(dirname "${OUTPUT}")"
mkdir -p logs

echo "=== brick arm job ==="
echo "  JOB:        ${SLURM_JOB_NAME:-?} (${SLURM_JOB_ID:-?})"
echo "  NODE:       $(hostname)"
echo "  CUBE:       ${CUBE}"
echo "  METADATA:   ${METADATA}"
echo "  OUTPUT:     ${OUTPUT}"
echo "  POSTERIOR:  ${POSTERIOR}"
echo "  YR window:  ${YR_START}-${YR_END}"
echo "  SAVE_TRAJS: ${SAVE_TRAJS}"
echo "  SAVE_COMP:  ${SAVE_COMP}"
echo "  START:      $(date)"

julia --project=julia julia/run_mimibrick_flatcube.jl \
  --cube       "${CUBE}" \
  --metadata   "${METADATA}" \
  --posterior  "${POSTERIOR}" \
  --output     "${OUTPUT}" \
  --start-year "${YR_START}" \
  --end-year   "${YR_END}" \
  --save-trajs           "${SAVE_TRAJS}" \
  --save-component-trajs "${SAVE_COMP}"

echo "  END:        $(date)"
