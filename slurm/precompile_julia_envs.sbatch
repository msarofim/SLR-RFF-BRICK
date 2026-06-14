#!/bin/bash
#SBATCH --job-name=jl_envs
#SBATCH --account=torch_pr_1041_general
#SBATCH --partition=cpu_short
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=05:00:00
#SBATCH --output=/scratch/ms17839/SLR-RFF-BRICK/slurm/logs/jl_envs_%j.out
# Instantiate + precompile the two new BRICK envs on a COMPUTE node (login nodes
# SIGKILL long CPU jobs). instantiate is idempotent: instant if already cached,
# self-heals missing downloads if the compute node has internet.
set -e
export PATH=$HOME/.juliaup/bin:$PATH
export JULIA_DEPOT_PATH=/scratch/ms17839/.julia
cd /scratch/ms17839/SLR-RFF-BRICK
echo "=== instantiate+precompile julia_v2 (v2.0.0: brick2/mengel) ==="
julia --project=julia_v2   -e 'using Pkg; Pkg.instantiate(); Pkg.precompile(); import MimiBRICK; println("v2 MimiBRICK pkgversion ", pkgversion(MimiBRICK))'
echo "=== instantiate+precompile julia_v121 (v1.2.1: pre93) ==="
julia --project=julia_v121 -e 'using Pkg; Pkg.instantiate(); Pkg.precompile(); import MimiBRICK; println("v121 MimiBRICK pkgversion ", pkgversion(MimiBRICK))'
echo "=== verify get_model build+run (both) ==="
julia --project=julia_v2   -e 'using MimiBRICK,Mimi; m=MimiBRICK.get_model(ssprcp_scenario="ssp245",start_year=1850,end_year=2100); run(m); println("v2   get_model+run OK  SLR2100=", round(100*(m[:global_sea_level,:sea_level_rise][end]),digits=1))'
julia --project=julia_v121 -e 'using MimiBRICK,Mimi; m=MimiBRICK.get_model(ssprcp_scenario="ssp245",start_year=1850,end_year=2100); run(m); println("v121 get_model+run OK  SLR2100=", round(100*(m[:global_sea_level,:sea_level_rise][end]),digits=1))'
echo "PRECOMPILE_DONE"
