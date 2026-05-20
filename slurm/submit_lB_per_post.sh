#!/bin/bash
#SBATCH --job-name=brick_lB
#SBATCH --account=torch_pr_1041_general
#SBATCH --partition=cpu_short
#SBATCH --time=02:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --output=logs/brick_lB_%j.out
#SBATCH --error=logs/brick_lB_%j.err
#
# Compute BRICK baseline log-likelihood l_B for each of the 10,000 posterior
# members. Runs BRICK with default RCP4.5 forcing (no FaIR override) for each
# member, computes GMSL-only AR(1) log-likelihood vs CSIRO Recons observations,
# writes a one-row-per-member CSV.
#
# This is independent of the paired BRICK runs — can run in parallel with them.
# Expected wallclock: ~30-60 min for 10k members.
#
# Submit:   sbatch slurm/submit_lB_per_post.sh
# Watch:    tail -f logs/brick_lB_<jobid>.out

set -euo pipefail
cd /scratch/ms17839/SLR-RFF-BRICK
mkdir -p logs outputs

set +u; source ~/.bashrc; set -u
conda activate $SCRATCH/SLR-RFF-BRICK/envs/fair
export JULIA_DEPOT_PATH=$SCRATCH/.julia
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}

echo "==============================================="
echo "BRICK baseline l_B per posterior member"
echo "Host: $(hostname)  Started: $(date)"
echo "==============================================="

cd julia
julia --project=. compute_lB_per_post.jl \
    --posterior ../data/MimiBRICK/parameters_subsample_brick.csv \
    --csiro     /scratch/ms17839/.julia/packages/MimiBRICK/bpCAF/data/calibration_data/CSIRO_Recons_gmsl_yr_2015.csv \
    --output    ../outputs/brick_lB_per_post.csv \
    --start-year 1850 --end-year 2100 --rcp RCP45

echo "==============================================="
echo "Done: $(date)"
ls -lh ../outputs/brick_lB_per_post.csv
