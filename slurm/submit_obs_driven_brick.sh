#!/bin/bash
#SBATCH --job-name=obs_brick
#SBATCH --account=torch_pr_1041_general
#SBATCH --partition=cpu_short
#SBATCH --time=03:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=12G
#SBATCH --array=1-4
#SBATCH --output=slurm/logs/obs_brick_%A_%a.out
#SBATCH --error=slurm/logs/obs_brick_%A_%a.err

# Obs-driven BRICK runs for component-by-component comparison vs observed
# SLR. Submitted as a 4-task SLURM array so the four (GMST, OHC) combos
# run in parallel and the wall clock fits comfortably under the 4 h
# cpu_short cap (each task ~1-1.5 h for 10k posterior draws):
#
#   task 1: (obs GMST,  obs OHC)   -- headline
#   task 2: (obs GMST,  FaIR OHC)  -- isolate surface-T contribution
#   task 3: (FaIR GMST, obs OHC)   -- isolate OHC contribution
#   task 4: (FaIR GMST, FaIR OHC)  -- reference; should track the cube driver
#
# Required pre-staged inputs on Torch:
#   data/MimiBRICK/parameters_subsample_brick.csv          (BRICK posterior)
#   data/observations/igcc2024_gmst_4dataset_mean.csv      (obs GMST)
#   data/observations/ohc_spliced_zanna_cheng.csv          (obs OHC, spliced)
#   data/observations/fair_mean_gmst.csv                   (FaIR-mean GMST)
#   data/observations/fair_mean_ohc.csv                    (FaIR-mean OHC)
#
# The two fair_mean_*.csv files are produced by
# python/build_fair_mean_trajectories.py from the LHS-10k baseline cube.

set -euo pipefail
cd /scratch/ms17839/SLR-RFF-BRICK
mkdir -p slurm/logs outputs

set +u; source ~/.bashrc; set -u
conda activate envs/fair
export JULIA_DEPOT_PATH=$SCRATCH/.julia
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export PYTHONUNBUFFERED=1

POSTERIOR=data/MimiBRICK/parameters_subsample_brick.csv
OBS_GMST=data/observations/igcc2024_gmst_4dataset_mean.csv
OBS_OHC=data/observations/ohc_spliced_zanna_cheng.csv
FAIR_GMST=data/observations/fair_mean_gmst.csv
FAIR_OHC=data/observations/fair_mean_ohc.csv

START=1850
END=2024   # historical-period only for now; extend post-2024 once headline
           # plots are agreed on (per the handoff "open questions" section).

# Map SLURM_ARRAY_TASK_ID -> (label, gmst_csv, gmst_time_col, gmst_value_col,
#                             ohc_csv, output_csv).
case "${SLURM_ARRAY_TASK_ID}" in
    1)  LABEL=obs_obs    ;  GMST_CSV=${OBS_GMST}   ; GMST_TC=time ; GMST_VC=GMST   ; OHC_CSV=${OBS_OHC}   ;;
    2)  LABEL=obs_fair   ;  GMST_CSV=${OBS_GMST}   ; GMST_TC=time ; GMST_VC=GMST   ; OHC_CSV=${FAIR_OHC}  ;;
    3)  LABEL=fair_obs   ;  GMST_CSV=${FAIR_GMST}  ; GMST_TC=year ; GMST_VC=gmst_C ; OHC_CSV=${OBS_OHC}   ;;
    4)  LABEL=fair_fair  ;  GMST_CSV=${FAIR_GMST}  ; GMST_TC=year ; GMST_VC=gmst_C ; OHC_CSV=${FAIR_OHC}  ;;
    *)  echo "ERROR: SLURM_ARRAY_TASK_ID=${SLURM_ARRAY_TASK_ID:-unset} not in 1..4"; exit 2 ;;
esac

OUT_CSV=outputs/brick_obsdriven_${LABEL}_to${END}.csv

echo "==============================================="
echo "Task ${SLURM_ARRAY_TASK_ID} [${LABEL}]"
echo "host=$(hostname)  start=$(date)"
echo "  gmst=${GMST_CSV}"
echo "  ohc =${OHC_CSV}"
echo "  out =${OUT_CSV}"
echo "==============================================="

cd julia
time julia --project=. run_mimibrick_obs_driven.jl \
    --posterior         ../${POSTERIOR} \
    --gmst-csv          ../${GMST_CSV} \
    --gmst-time-col     ${GMST_TC} \
    --gmst-value-col    ${GMST_VC} \
    --ohc-csv           ../${OHC_CSV} \
    --output            ../${OUT_CSV} \
    --start-year        ${START} \
    --end-year          ${END} \
    --save-total-trajs     true \
    --save-component-trajs true
cd ..

ls -lh ${OUT_CSV}

echo
echo "==============================================="
echo "Task ${SLURM_ARRAY_TASK_ID} [${LABEL}] DONE  end=$(date)"
echo "==============================================="
