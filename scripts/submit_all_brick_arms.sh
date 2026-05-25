#!/bin/bash
# submit_all_brick_arms.sh — submit 18 BRICK arm jobs (9 LHS + 9 ANOVA).
#
# Each job runs julia/run_mimibrick_flatcube.jl on ONE cube .npz and writes
# the corresponding output CSV under /scratch/ms17839/SLR-RFF-BRICK/outputs/brick_v145/.
#
# Usage (from /scratch/ms17839/SLR-RFF-BRICK):
#   bash scripts/submit_all_brick_arms.sh           # full run
#   bash scripts/submit_all_brick_arms.sh smoke      # one tiny smoke test only

set -euo pipefail

ROOT=/scratch/ms17839/SLR-RFF-BRICK
CUBES=/scratch/ms17839/FaIRtoFrEDI/fair_outputs/cubes_v145
META=/scratch/ms17839/FaIRtoFrEDI/fair_outputs/metadata_v145
OUT=${ROOT}/outputs/brick_v145
POST=${ROOT}/data/MimiBRICK/parameters_subsample_brick.csv

mkdir -p ${OUT} ${ROOT}/logs

MODE=${1:-full}

# Cube → metadata pairing. LHS arms use lhs10k_metadata_v145.csv; ANOVA arms
# use anova18k_metadata_v145.csv. Same metadata file across baseline + pulse
# arms within a family — the pairing is per (rff,cfg,seed,post) tuple, not
# per-arm.
declare -A META_OF=(
  ["lhs10k"]="${META}/lhs10k_metadata_v145.csv"
  ["anova18k"]="${META}/anova18k_metadata_v145.csv"
)

ARMS=(
  cube_v145_lhs10k_baseline.npz
  cube_v145_lhs10k_pulse_co2_pos_1gt.npz
  cube_v145_lhs10k_pulse_co2_neg_1gt.npz
  cube_v145_lhs10k_pulse_co2_pos_001gt.npz
  cube_v145_lhs10k_pulse_co2_neg_001gt.npz
  cube_v145_lhs10k_pulse_ch4_pos_1tg.npz
  cube_v145_lhs10k_pulse_ch4_neg_1tg.npz
  cube_v145_lhs10k_pulse_ch4_pos_001tg.npz
  cube_v145_lhs10k_pulse_ch4_neg_001tg.npz
  cube_v145_anova18k_baseline.npz
  cube_v145_anova18k_pulse_co2_pos_1gt.npz
  cube_v145_anova18k_pulse_co2_neg_1gt.npz
  cube_v145_anova18k_pulse_co2_pos_001gt.npz
  cube_v145_anova18k_pulse_co2_neg_001gt.npz
  cube_v145_anova18k_pulse_ch4_pos_1tg.npz
  cube_v145_anova18k_pulse_ch4_neg_1tg.npz
  cube_v145_anova18k_pulse_ch4_pos_001tg.npz
  cube_v145_anova18k_pulse_ch4_neg_001tg.npz
)

submit_arm() {
  local cube_file=$1
  local base=${cube_file%.npz}
  # extract family: "lhs10k" or "anova18k"
  local family
  if [[ "${cube_file}" == *lhs10k* ]]; then family=lhs10k
  elif [[ "${cube_file}" == *anova18k* ]]; then family=anova18k
  else
    echo "ERROR: cannot infer family from ${cube_file}" >&2
    exit 1
  fi
  local meta_file="${META_OF[${family}]}"
  local out_file="${OUT}/brick_${base#cube_v145_}.csv"
  local job_name="brick_${base#cube_v145_}"

  echo "submit: ${job_name}"
  echo "        cube=${CUBES}/${cube_file}"
  echo "        meta=${meta_file}"
  echo "        out=${out_file}"

  sbatch \
    --job-name="${job_name}" \
    --export=ALL,CUBE="${CUBES}/${cube_file}",METADATA="${meta_file}",OUTPUT="${out_file}",POSTERIOR="${POST}",YR_START=1850,YR_END=2300,SAVE_TRAJS=true,SAVE_COMP=true \
    scripts/submit_brick_arm.sh
}

if [[ "${MODE}" == "smoke" ]]; then
  echo "SMOKE MODE — submitting one tiny job (baseline LHS, will use --max-rows via custom submit)"
  echo "Run this only to verify the Torch driver works end-to-end before full submission."
  # For smoke, override sbatch script to add --max-rows 5
  # (Easier: pass the limit via inline julia call.)
  sbatch \
    --job-name="brick_smoke" \
    --account=torch_pr_1041_general \
    --partition=cs \
    --time=20:00 --mem=4G \
    --output=${ROOT}/logs/brick_smoke_%j.out \
    --error=${ROOT}/logs/brick_smoke_%j.err \
    --wrap "cd ${ROOT} && julia --project=julia julia/run_mimibrick_flatcube.jl \
       --cube ${CUBES}/cube_v145_lhs10k_baseline.npz \
       --metadata ${META}/lhs10k_metadata_v145.csv \
       --posterior ${POST} \
       --output ${OUT}/brick_smoke_lhs10k_baseline.csv \
       --start-year 1850 --end-year 2300 \
       --max-rows 20 \
       --save-trajs true --save-component-trajs true"
  exit 0
fi

# Full submission
for cube_file in "${ARMS[@]}"; do
  submit_arm "${cube_file}"
done

echo
echo "=== Submitted 18 BRICK arm jobs ==="
squeue -u ms17839 -o "%i %j %T %M %l"
