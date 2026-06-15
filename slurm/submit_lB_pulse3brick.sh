#!/bin/bash
#SBATCH --job-name=lB_p3brick
#SBATCH --account=torch_pr_1041_general
#SBATCH --partition=cpu_short
#SBATCH --time=04:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --array=0-1
#SBATCH --output=logs/lB_p3brick_%A_%a.out
#SBATCH --error=logs/lB_p3brick_%A_%a.err
#
# Step 5 (CO2/CH4 pulse->SLR, 3 BRICK versions): per-posterior-member Wong
# baseline log-likelihood l_B vs Dangendorf, for the TWO Wong-weighted arms.
#   array idx 0 -> pre93  : MimiBRICK v1.2.1 (julia_v121), pre-#93 35-col posterior,
#                           precip_log=false, compute_lB_per_post_v121.jl
#   array idx 1 -> brick2 : MimiBRICK v2.0.0 (julia_v2),  post-#93 35-col posterior,
#                           precip_log=true,  compute_lB_per_post_brick2.jl
# (mengel is EQUAL-WEIGHTED — NO Wong — so it is NOT computed here; see
#  notes/handoff_2026-06-15_pulse_step5_wong.md §1.)
#
# --obs dangendorf MUST match apply_wong_weights.py, or (l_FB - l_B) is meaningless.
#
# Submit:  sbatch slurm/submit_lB_pulse3brick.sh
# Watch:   tail -f logs/lB_p3brick_<jobid>_<idx>.out

set -euo pipefail
cd /scratch/ms17839/SLR-RFF-BRICK
mkdir -p logs outputs

set +u; source ~/.bashrc; set -u
conda activate $SCRATCH/SLR-RFF-BRICK/envs/fair
export JULIA_DEPOT_PATH=$SCRATCH/.julia
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}

case "${SLURM_ARRAY_TASK_ID:-0}" in
  0) VNAME=pre93;  PROJ=julia_v121; SCRIPT=julia/compute_lB_per_post_v121.jl
     POST=outputs/quarantine/20260522_pre_pr93_v10x/parameters_subsample_brick.csv
     EXTRA="" ;;
  1) VNAME=brick2; PROJ=julia_v2;   SCRIPT=julia/compute_lB_per_post_brick2.jl
     POST=data/MimiBRICK/parameters_subsample_brick.csv
     EXTRA="--precip-log true" ;;
  *) echo "bad array idx"; exit 1 ;;
esac
OUT=outputs/brick_lB_per_post_${VNAME}.csv

echo "==============================================="
echo "Step-5 l_B  version=$VNAME  proj=$PROJ"
echo "  posterior=$POST"
echo "  output=$OUT"
echo "Host: $(hostname)  Started: $(date)"
echo "==============================================="

julia --project=$PROJ $SCRIPT \
    --posterior "$POST" \
    --obs dangendorf \
    --obs-path data/observations/dangendorf_2024_gmsl.csv \
    --output "$OUT" \
    --start-year 1850 --end-year 2100 $EXTRA

echo "==============================================="
echo "Done: $(date)"
ls -lh "$OUT"
