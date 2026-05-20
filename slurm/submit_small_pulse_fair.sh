#!/bin/bash
#SBATCH --job-name=fair_smallpulse
#SBATCH --account=torch_pr_1041_general
#SBATCH --partition=cpu_short
#SBATCH --time=02:00:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --output=logs/fair_smallpulse_%A_%a.out
#SBATCH --error=logs/fair_smallpulse_%A_%a.err
#SBATCH --array=0-3
#
# Small-pulse FaIR runs to enable Lemoine-framework SC-GHG decomposition.
# Each task produces a stochastic FaIR cube paired to the same (rff, cfg, seed)
# layout as the baseline / 1-GtC / 1-Tg-CH4 production runs.  The marginal
# of (pulse - baseline) / pulse_size should converge to the linear sensitivity
# in the limit of small pulse size.
#
# Array tasks:
#   0 = CO2 +0.1  GtC at 2030  (~0.367 GtCO2)
#   1 = CO2 +0.01 GtC at 2030  (~0.0367 GtCO2)
#   2 = CH4 +0.1  Tg at 2030
#   3 = CH4 +0.01 Tg at 2030
#
# Outputs (npz + split npy stems):
#   outputs/rff_pulse0p1gtc_stoch_to2300.{npz, _gmst.npy, _ohc.npy, ...}
#   outputs/rff_pulse0p01gtc_stoch_to2300.{...}
#   outputs/rff_ch4pulse0p1tg_stoch_to2300.{...}
#   outputs/rff_ch4pulse0p01tg_stoch_to2300.{...}

set -euo pipefail
cd /scratch/ms17839/SLR-RFF-BRICK
mkdir -p logs outputs
set +u; source ~/.bashrc; set -u
conda activate $SCRATCH/SLR-RFF-BRICK/envs/fair
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export PYTHONUNBUFFERED=1

TASK=${SLURM_ARRAY_TASK_ID}

SEED_BASE=2027
N_DRAWS=250    # 2N -> 500 paired draws after LHS + random
END_YEAR=2300
COMMON="--baseline-mode rff --stochastic --n-seeds 1 --n-draws $N_DRAWS \
        --seed-base $SEED_BASE --batch-size 1 --keep-end $END_YEAR"

case $TASK in
  0)
    echo "CO2 +0.1 GtC pulse at 2030"
    python python/lhs_climate_pilot_ext.py $COMMON \
        --scenario-tag pulse0p1gtc \
        --pulse-gtc 0.1 --pulse-year 2030
    ;;
  1)
    echo "CO2 +0.01 GtC pulse at 2030"
    python python/lhs_climate_pilot_ext.py $COMMON \
        --scenario-tag pulse0p01gtc \
        --pulse-gtc 0.01 --pulse-year 2030
    ;;
  2)
    echo "CH4 +0.1 Tg pulse at 2030"
    python python/lhs_climate_pilot_ext.py $COMMON \
        --scenario-tag ch4pulse0p1tg \
        --pulse-tg-ch4 0.1 --pulse-year 2030
    ;;
  3)
    echo "CH4 +0.01 Tg pulse at 2030"
    python python/lhs_climate_pilot_ext.py $COMMON \
        --scenario-tag ch4pulse0p01tg \
        --pulse-tg-ch4 0.01 --pulse-year 2030
    ;;
  *) echo "unknown task $TASK"; exit 1 ;;
esac

echo "task $TASK done: $(date)"
