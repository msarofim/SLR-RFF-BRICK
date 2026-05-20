#!/bin/bash
#SBATCH --job-name=lhs10k_brick
#SBATCH --account=torch_pr_1041_general
#SBATCH --partition=cpu_short
#SBATCH --time=01:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --output=slurm/logs/lhs10k_brick_%j.out
#SBATCH --error=slurm/logs/lhs10k_brick_%j.err

# Final conditional-BRICK ensemble for the poster (10,000 LHS triplets).
#
#   1. BRICK on baseline cube  → brick_lhs10k_baseline_to2300.csv
#   2. BRICK on pulse cube     → brick_lhs10k_pulse_to2300.csv     (paired)
#   3. apply_wong_weights.py   → brick_lhs10k_baseline_to2300_weighted.csv
#   4. Inject baseline w_norm into pulse CSV → brick_lhs10k_pulse_to2300_weighted.csv
#
# Conditional sampling comes from the per-row Wong importance weight: the
# l_FB term in the weight depends on each row's PAIRED FaIR cfg and BRICK
# post. So the weighted ensemble approximates p(cfg, post | obs GMSL),
# not p(cfg) × p(post). With LHS coverage of all 841 cfgs and all 10,000
# posts, the effective sample size should be substantially larger than the
# 500-cell ANOVA design.
#
# Required pre-staged inputs (all on Torch):
#   outputs/rff_baseline_stoch_to2300_{gmst,ohc,years,rffs}.npy
#   outputs/rff_pulse_stoch_to2300_{gmst,ohc,years,rffs}.npy
#   outputs/brick_lB_per_post_dangendorf.csv
#   outputs/lhs10k_metadata.csv               (pushed alongside this script)
#   data/MimiBRICK/parameters_subsample_brick.csv
#   data/observations/dangendorf_2024_gmsl.csv

set -euo pipefail
cd /scratch/ms17839/SLR-RFF-BRICK
mkdir -p slurm/logs outputs

set +u; source ~/.bashrc; set -u
conda activate envs/fair
export JULIA_DEPOT_PATH=$SCRATCH/.julia
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export PYTHONUNBUFFERED=1

POSTERIOR=data/MimiBRICK/parameters_subsample_brick.csv
METADATA=outputs/lhs10k_metadata.csv
LB_CSV=outputs/brick_lB_per_post_dangendorf.csv
OBS_CSV=data/observations/dangendorf_2024_gmsl.csv

BASELINE_STEM=outputs/rff_baseline_stoch_to2300
PULSE_STEM=outputs/rff_pulse_stoch_to2300

BASELINE_CSV=outputs/brick_lhs10k_baseline_to2300.csv
PULSE_CSV=outputs/brick_lhs10k_pulse_to2300.csv
BASELINE_WEIGHTED=outputs/brick_lhs10k_baseline_to2300_weighted.csv
PULSE_WEIGHTED=outputs/brick_lhs10k_pulse_to2300_weighted.csv

echo "==============================================="
echo "LHS-10k conditional BRICK ensemble"
echo "host=$(hostname)  start=$(date)"
echo "metadata=$METADATA  $(wc -l <$METADATA) rows"
echo "==============================================="

# ---- Step 1: BRICK on baseline cube ---------------------------------------
echo
echo "=== Step 1/4: BRICK paired runs on baseline cube ==="
cd julia
time julia --project=. run_mimibrick_paired_explicit.jl \
    --cube      /tmp/unused.npz \
    --npy-stem  ../${BASELINE_STEM} \
    --metadata  ../${METADATA} \
    --posterior ../${POSTERIOR} \
    --output    ../${BASELINE_CSV} \
    --seed      2026 \
    --start-year 1850 --end-year 2300 \
    --save-trajs true
cd ..
ls -lh ${BASELINE_CSV}

# ---- Step 2: BRICK on pulse cube (same metadata, paired) -------------------
echo
echo "=== Step 2/4: BRICK paired runs on pulse cube ==="
cd julia
time julia --project=. run_mimibrick_paired_explicit.jl \
    --cube      /tmp/unused.npz \
    --npy-stem  ../${PULSE_STEM} \
    --metadata  ../${METADATA} \
    --posterior ../${POSTERIOR} \
    --output    ../${PULSE_CSV} \
    --seed      2026 \
    --start-year 1850 --end-year 2300 \
    --save-trajs true
cd ..
ls -lh ${PULSE_CSV}

# ---- Step 3: Apply Wong importance weights to baseline arm ----------------
echo
echo "=== Step 3/4: Wong importance weights on baseline ==="
time python -u python/apply_wong_weights.py \
    --paired    ${BASELINE_CSV} \
    --obs       dangendorf \
    --obs-path  ${OBS_CSV} \
    --posterior ${POSTERIOR} \
    --lB        ${LB_CSV} \
    --output    ${BASELINE_WEIGHTED} \
    --c         auto \
    --ess-target 0.5
ls -lh ${BASELINE_WEIGHTED}

# ---- Step 4: Propagate baseline weights into pulse CSV --------------------
# Same (rff_idx, fair_cfg_idx, seed_idx, post_idx) rows in both — just merge w_norm.
echo
echo "=== Step 4/4: Propagate w_norm into pulse CSV ==="
python -u -c "
import pandas as pd
keys = ['rff_idx','fair_cfg_idx','seed_idx','post_idx']
w = pd.read_csv('${BASELINE_WEIGHTED}', usecols=keys + ['w_norm', 'log_w', 'l_FB', 'l_B'])
p = pd.read_csv('${PULSE_CSV}')
m = p.merge(w, on=keys, how='left', validate='one_to_one')
assert m['w_norm'].notna().all(), 'pulse rows without matched baseline weight'
m.to_csv('${PULSE_WEIGHTED}', index=False)
print('wrote ${PULSE_WEIGHTED}  shape', m.shape)
"
ls -lh ${PULSE_WEIGHTED}

echo
echo "==============================================="
echo "DONE  end=$(date)"
echo "==============================================="
echo "Outputs:"
echo "  ${BASELINE_WEIGHTED}"
echo "  ${PULSE_WEIGHTED}"
