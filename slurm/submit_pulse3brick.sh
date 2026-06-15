#!/bin/bash
#SBATCH --job-name=p3brick
#SBATCH --account=torch_pr_1041_general
#SBATCH --partition=cpu_short
#SBATCH --time=03:00:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=2
#SBATCH --array=0-8
#SBATCH --output=/scratch/ms17839/SLR-RFF-BRICK/slurm/logs/p3brick_%A_%a.out
#SBATCH --error=/scratch/ms17839/SLR-RFF-BRICK/slurm/logs/p3brick_%A_%a.err
# ============================================================================
# Step 4: CO2/CH4 pulse->SLR, 3 BRICK versions x 3 arms x 10k = 90k BRICK runs.
# 9-task array; idx = version*3 + arm.  versions: 0 pre93 / 1 brick2 / 2 mengel.
# arms: 0 baseline / 1 co2 (0.01 GtCO2, /0.01) / 2 ch4 (1 TgCH4, /1.0).
# Paired determinism: SAME --seed across baseline & pulse (default 2026).
# Marginals differenced downstream (extract_pulse_marginals). Baseline arm saves
# the GMSL history (--save-trajs) for per-version Wong weighting (Step 5).
# Cubes = realization r2 (paired, seed-provenance embedded).
# ============================================================================
set -euo pipefail
set +u; source ~/.bashrc; set -u
export PATH=$HOME/.juliaup/bin:$PATH
export JULIA_DEPOT_PATH=/scratch/ms17839/.julia
REPO=/scratch/ms17839/SLR-RFF-BRICK
CUBEDIR=/scratch/ms17839/FaIRtoFrEDI/fair_outputs/cubes_v145
cd $REPO
mkdir -p outputs/pulse3brick_v145

IDX=${SLURM_ARRAY_TASK_ID}
VER=$((IDX / 3)); ARM=$((IDX % 3))
case $VER in
  0) VNAME=pre93;  PROJ=julia_v121; POST=outputs/quarantine/20260522_pre_pr93_v10x/parameters_subsample_brick.csv ;;
  1) VNAME=brick2; PROJ=julia_v2;   POST=data/MimiBRICK/parameters_subsample_brick.csv ;;
  2) VNAME=mengel; PROJ=julia_v2;   POST=data/MimiBRICK/parameters_subsample_brick_mengel_ext.csv ;;
esac
case $ARM in
  0) ANAME=baseline; CUBE=$CUBEDIR/cube_v145_lhs10ks_baseline_flat2015_r2.npz;          SAVET=true  ;;
  1) ANAME=co2;      CUBE=$CUBEDIR/cube_v145_lhs10ks_pulse_co2_pos_001gt_flat2015_r2.npz; SAVET=false ;;
  2) ANAME=ch4;      CUBE=$CUBEDIR/cube_v145_lhs10ks_pulse_ch4_pos_1tg_flat2015_r2.npz;   SAVET=false ;;
esac
OUT=outputs/pulse3brick_v145/${VNAME}_${ANAME}.csv

echo "[$IDX] version=$VNAME arm=$ANAME proj=$PROJ host=$(hostname) start=$(date)"
echo "  cube=$CUBE"
echo "  post=$POST  out=$OUT  save-trajs=$SAVET"
julia --project=$PROJ julia/run_mimibrick_pulse_versioned.jl \
  --cube "$CUBE" --metadata outputs/lhs10ks_brick_metadata.csv \
  --posterior "$POST" --brick-version $VNAME \
  --seed 2026 --save-trajs $SAVET --output "$OUT"
echo "[$IDX] DONE $VNAME/$ANAME $(date)"
