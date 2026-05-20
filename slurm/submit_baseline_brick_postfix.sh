#!/bin/bash
#SBATCH --job-name=brick_baseline_pf
#SBATCH --account=torch_pr_1041_general
#SBATCH --partition=cpu_short
#SBATCH --time=00:30:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --output=logs/brick_baseline_postfix_%j.out
#SBATCH --error=logs/brick_baseline_postfix_%j.err
#
# Rerun the Phase C RFF baseline paired BRICK with the POST-FIX driver
# (run_mimibrick_paired_explicit.jl with Random.seed!() before get_model)
# using the SAME metadata tuples and SAME seed (2027) as the newly-run
# CH4 pulse BRICK.  This gives a baseline that pairs cleanly with the CH4
# pulse output → clean marginal SLR.
#
# The existing brick_paired_rff_baseline_to2300_weighted.csv is pre-fix
# (May 13).  Pairing pre-fix baseline with post-fix CH4 pulse gave a
# spurious ~0.2 cm offset across all years (poster review May 18 audit).
#
# Output:
#   outputs/brick_paired_rff_baseline_postfix_to2300.csv
#   outputs/brick_paired_rff_baseline_postfix_to2300_weighted.csv

set -euo pipefail
cd /scratch/ms17839/SLR-RFF-BRICK
mkdir -p logs outputs

set +u; source ~/.bashrc; set -u
conda activate envs/fair
export JULIA_DEPOT_PATH=$SCRATCH/.julia
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export PYTHONUNBUFFERED=1

CUBE_NPZ=outputs/rff_baseline_stoch_to2300.npz
STEM=outputs/rff_baseline_stoch_to2300
POSTERIOR=data/MimiBRICK/parameters_subsample_brick.csv
CSIRO=/scratch/ms17839/.julia/packages/MimiBRICK/bpCAF/data/calibration_data/CSIRO_Recons_gmsl_yr_2015.csv
LB=outputs/brick_lB_per_post.csv
META=outputs/ch4pulse_paired_metadata.csv   # already built by ch4 job

echo "==============================================="
echo "Post-fix BASELINE BRICK (Phase C, paired explicit)"
echo "Host: $(hostname)  Started: $(date)"
echo "==============================================="

# Step 1: extract .npy files from the baseline cube if not already there
if [ ! -f "${STEM}_gmst.npy" ]; then
    echo
    echo "=== Step 1: extract .npy from baseline cube ==="
    python -u -c "
import numpy as np
nz = np.load('${CUBE_NPZ}')
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

# Step 2: paired BRICK using explicit-tuple driver with seed 2027 (matches
# the CH4 pulse run)
echo
echo "=== Step 2: paired BRICK on baseline cube (post-fix) ==="
cd julia
time julia --project=. run_mimibrick_paired_explicit.jl \
    --cube      /tmp/unused.npz \
    --npy-stem  ../${STEM} \
    --metadata  ../${META} \
    --posterior ../${POSTERIOR} \
    --output    ../outputs/brick_paired_rff_baseline_postfix_to2300.csv \
    --seed      2027 \
    --start-year 1850 --end-year 2300 \
    --save-trajs true
cd ..

# Step 3: Wong weighting
echo
echo "=== Step 3: Wong importance weighting on post-fix baseline ==="
python python/apply_wong_weights.py \
    --paired     outputs/brick_paired_rff_baseline_postfix_to2300.csv \
    --csiro      "$CSIRO" \
    --posterior  "$POSTERIOR" \
    --lB         "$LB" \
    --output     outputs/brick_paired_rff_baseline_postfix_to2300_weighted.csv \
    --c          auto \
    --ess-target 0.5

echo
echo "Done: $(date)"
ls -lh outputs/brick_paired_rff_baseline_postfix_to2300*.csv 2>/dev/null || true
