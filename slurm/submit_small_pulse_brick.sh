#!/bin/bash
#SBATCH --job-name=brick_smallpulse
#SBATCH --account=torch_pr_1041_general
#SBATCH --partition=cpu_short
#SBATCH --time=01:30:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --output=logs/brick_smallpulse_%A_%a.out
#SBATCH --error=logs/brick_smallpulse_%A_%a.err
#SBATCH --array=0-3
#
# Pair each small-pulse FaIR cube through BRICK + apply Dangendorf-anchored
# Wong weights.  Depends on small-pulse FaIR job array completing.
#
# Array tasks (same scenario tags as submit_small_pulse_fair.sh):
#   0 = CO2 +0.1  GtC pulse  -> brick_paired_rff_pulse0p1gtc_to2300_weighted.csv
#   1 = CO2 +0.01 GtC pulse  -> brick_paired_rff_pulse0p01gtc_to2300_weighted.csv
#   2 = CH4 +0.1  Tg pulse   -> brick_paired_rff_ch4pulse0p1tg_to2300_weighted.csv
#   3 = CH4 +0.01 Tg pulse   -> brick_paired_rff_ch4pulse0p01tg_to2300_weighted.csv
#
# CO2 small pulses pair against the PRE-fix baseline (same lineage as the
# 1-GtC CO2 pulse, seed=2026, run_mimibrick_paired_seeded.jl default lineage).
# CH4 small pulses pair against the POST-fix baseline (same lineage as the
# 1-Tg CH4 pulse, seed=2027, explicit-tuple driver lineage; uses seed=2027).

set -euo pipefail
cd /scratch/ms17839/SLR-RFF-BRICK
mkdir -p logs outputs
set +u; source ~/.bashrc; set -u
conda activate $SCRATCH/SLR-RFF-BRICK/envs/fair
export JULIA_DEPOT_PATH=$SCRATCH/.julia
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export PYTHONUNBUFFERED=1

TASK=${SLURM_ARRAY_TASK_ID}

case $TASK in
  0) SCEN=pulse0p1gtc;     SEED=2026 ;;
  1) SCEN=pulse0p01gtc;    SEED=2026 ;;
  2) SCEN=ch4pulse0p1tg;   SEED=2027 ;;
  3) SCEN=ch4pulse0p01tg;  SEED=2027 ;;
  *) echo "unknown task $TASK"; exit 1 ;;
esac

STEM=outputs/rff_${SCEN}_stoch_to2300
META=${STEM}_metadata.csv
PAIRED=outputs/brick_paired_rff_${SCEN}_to2300.csv
WEIGHTED=outputs/brick_paired_rff_${SCEN}_to2300_weighted.csv

echo '==============================================='
echo "Small-pulse BRICK task=$TASK  SCEN=$SCEN  start=$(date)"
echo '==============================================='

# Expand .npz -> 4D .npy if not already done (paired driver needs the stem).
if [ ! -f ${STEM}_gmst.npy ]; then
    echo "Expanding ${STEM}.npz to 4D .npy ..."
    python python/scripts/expand_phaseC_to_4d.py ${STEM}.npz
fi

cd julia
julia --project=. run_mimibrick_paired_seeded.jl \
    --cube      ../${STEM}.npz \
    --npy-stem  ../${STEM} \
    --metadata  ../${META} \
    --posterior ../data/MimiBRICK/parameters_subsample_brick.csv \
    --output    ../${PAIRED} \
    --seed      $SEED \
    --start-year 1850 --end-year 2300 \
    --save-trajs true
cd ..

python python/apply_wong_weights.py \
    --paired    ${PAIRED} \
    --obs       dangendorf \
    --obs-path  data/observations/dangendorf_2024_gmsl.csv \
    --posterior data/MimiBRICK/parameters_subsample_brick.csv \
    --lB        outputs/brick_lB_per_post_dangendorf.csv \
    --output    ${WEIGHTED} \
    --c         auto --ess-target 0.5

echo "Done task $TASK: $(date)"
ls -lh ${PAIRED} ${WEIGHTED}
