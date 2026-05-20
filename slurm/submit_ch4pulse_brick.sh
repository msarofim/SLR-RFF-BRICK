#!/bin/bash
#SBATCH --job-name=brick_ch4pulse
#SBATCH --account=torch_pr_1041_general
#SBATCH --partition=cpu_short
#SBATCH --time=00:30:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --output=logs/brick_ch4pulse_%j.out
#SBATCH --error=logs/brick_ch4pulse_%j.err
#
# Paired BRICK on the Phase C CH4 pulse cube against the Phase C baseline,
# using the EXPLICIT-tuple driver so we run the SAME (rff, cfg, seed, post)
# combinations that the existing Phase C baseline run used.  This makes the
# CH4 marginal SLR comparable apples-to-apples with the existing CO2 pulse
# results.
#
# Output:
#   outputs/brick_paired_rff_ch4pulse_to2300.csv
#   outputs/brick_paired_rff_ch4pulse_to2300_weighted.csv

set -euo pipefail
cd /scratch/ms17839/SLR-RFF-BRICK
mkdir -p logs outputs

set +u; source ~/.bashrc; set -u
conda activate envs/fair
export JULIA_DEPOT_PATH=$SCRATCH/.julia
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export PYTHONUNBUFFERED=1

CUBE=outputs/rff_ch4pulse_stoch_to2300.npz
STEM=outputs/rff_ch4pulse_stoch_to2300
POSTERIOR=data/MimiBRICK/parameters_subsample_brick.csv
CSIRO=/scratch/ms17839/.julia/packages/MimiBRICK/bpCAF/data/calibration_data/CSIRO_Recons_gmsl_yr_2015.csv
LB=outputs/brick_lB_per_post.csv
META=outputs/ch4pulse_paired_metadata.csv

echo "==============================================="
echo "Paired BRICK on CH4 pulse Phase C cube"
echo "Host: $(hostname)  Started: $(date)"
echo "==============================================="

# Step 1: extract .npy files from the CH4 cube (NPZ.jl <U key workaround).
if [ ! -f "${STEM}_gmst.npy" ]; then
    echo
    echo "=== Step 1: extract .npy from CH4 pulse cube ==="
    python -u -c "
import numpy as np
nz = np.load('${CUBE}')
print('npz keys:', list(nz.keys()))
print('gmst shape:', nz['gmst_traj_rff'].shape)
np.save(f'${STEM}_gmst.npy',  nz['gmst_traj_rff'].astype(np.float32))
np.save(f'${STEM}_ohc.npy',   nz['ohc_traj_rff'].astype(np.float32))
np.save(f'${STEM}_years.npy', nz['years'].astype(np.int64))
np.save(f'${STEM}_rffs.npy',  nz['unique_rffs'].astype(np.int64))
print('Extracted .npy files for ${STEM}')
"
else
    echo "  Reusing existing ${STEM}_gmst.npy"
fi

# Step 2: build the metadata CSV by extracting (rff_idx, fair_cfg_idx,
# seed_idx, post_idx) tuples from the existing Phase C baseline BRICK CSV.
# This guarantees the CH4 pulse runs on identical draws → clean pairing.
echo
echo "=== Step 2: build metadata from baseline BRICK CSV ==="
python -u -c "
import pandas as pd
b = pd.read_csv('outputs/brick_paired_rff_baseline_to2300.csv',
                usecols=['rff_idx','fair_cfg_idx','seed_idx','post_idx'])
b.insert(0, 'axis', 'phaseC')
b.to_csv('${META}', index=False)
print(f'wrote ${META}  ({len(b)} rows)')
print(b.head(3).to_string(index=False))
"

# Step 3: paired BRICK using the explicit-tuple driver.
echo
echo "=== Step 3: paired BRICK on CH4 pulse cube (explicit tuples) ==="
cd julia
time julia --project=. run_mimibrick_paired_explicit.jl \
    --cube      /tmp/unused.npz \
    --npy-stem  ../${STEM} \
    --metadata  ../${META} \
    --posterior ../${POSTERIOR} \
    --output    ../outputs/brick_paired_rff_ch4pulse_to2300.csv \
    --seed      2027 \
    --start-year 1850 --end-year 2300 \
    --save-trajs true
cd ..

# Step 4: Apply Wong importance weighting.
echo
echo "=== Step 4: Wong importance weighting on CH4 pulse BRICK ==="
python python/apply_wong_weights.py \
    --paired     outputs/brick_paired_rff_ch4pulse_to2300.csv \
    --csiro      "$CSIRO" \
    --posterior  "$POSTERIOR" \
    --lB         "$LB" \
    --output     outputs/brick_paired_rff_ch4pulse_to2300_weighted.csv \
    --c          auto \
    --ess-target 0.5

echo
echo "Done: $(date)"
ls -lh outputs/brick_paired_rff_ch4pulse_to2300*.csv 2>/dev/null || true
