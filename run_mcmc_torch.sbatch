#!/bin/bash
## Production MCMC on NYU Torch — 4 RAM chains as a job array on the `cs` partition.
## Deploy first (see DEPLOY notes at bottom): rsync the repo + instantiate julia_v2.
##   sbatch run_mcmc_torch.sbatch
#SBATCH --job-name=brick_mengel_mcmc
#SBATCH --account=torch_pr_1041_general
#SBATCH --partition=cs
#SBATCH --array=0-3
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=03:00:00
#SBATCH --output=outputs/mcmc/torch_chain_%a.out

cd /scratch/ms17839/SLR-RFF-BRICK
mkdir -p outputs/mcmc
SEED=$((2026 + SLURM_ARRAY_TASK_ID))
N_ITER=200000
echo "chain seed=$SEED  n_iter=$N_ITER  on $(hostname)"
~/julia-1.12/bin/julia --project=julia_v2 julia/calibrate_mcmc.jl $N_ITER $SEED
## After all array tasks finish, on the login node:
##   julia --project=julia_v2 julia/postprocess_mcmc.jl 10000

## ============================== DEPLOY (one-time) ==============================
## 1. rsync the repo (code + data + the local julia_v2 Project/Manifest) to Torch:
##      rsync -av --exclude outputs/mcmc --exclude '*.png' \
##        ~/Documents/2026/CodeProjects/SLR-RFF-BRICK/ torch:/scratch/ms17839/SLR-RFF-BRICK/
## 2. On Torch, instantiate the v2.0.0 MimiBRICK env (GitHub-tag install; Julia ≥1.10):
##      cd /scratch/ms17839/SLR-RFF-BRICK
##      julia --project=julia_v2 -e 'using Pkg; Pkg.instantiate()'
##    (resolves MimiBRICK @ repo-rev v2.0.0 + Distributions + RobustAdaptiveMetropolisSampler)
## 3. Smoke-test one chain interactively before the array:
##      julia --project=julia_v2 julia/calibrate_mcmc.jl 2000 2026
## NOTE: the compute is small (~236 iter/s); 4×200k ≈ 15 min/chain. cs has no time
## cap, but cpu_short (6-hr) would also work. The model is single-threaded per chain.
