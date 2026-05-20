# Greene HPC runbook for SLR-RFF-BRICK pipeline

Author: prep notes for Marcus's Thursday session.

The aim: replicate the local FaIR → MimiBRICK → FrEDI pipeline on Greene at
N=2000 LHS draws, taking advantage of array-job parallelism.

## What we need on Greene

| Component | Reason | Approach |
|-----------|--------|----------|
| Python 3 + FaIR 2.2.4 | Climate runs | Singularity overlay or conda env |
| Julia 1.10+ + MimiBRICK | Sea-level model | juliaup install in $HOME (no admin needed) |
| R 4.4+ + FrEDI | Damages | Singularity image with R, then `install.packages` |
| ~3 GB working data | RFF-SP CSVs + MimiBRICK posterior + FaIR calibration | scp once, store in /scratch |

The pre-flight goal is to have all three runtimes installed and a single test
draw pass through end-to-end before scaling to N=2000.

---

## Step 0 — Log in and locate scratch

```bash
ssh netid@greene.hpc.nyu.edu     # or use OOD web at https://ood.hpc.nyu.edu
echo $SCRATCH                     # typically /scratch/<netid>
mkdir -p $SCRATCH/SLR-RFF-BRICK
cd       $SCRATCH/SLR-RFF-BRICK
```

Greene-specific paths to know:
- `/scratch/<netid>/` — your scratch (purged after 60 days inactivity, 50 TB quota)
- `/scratch/work/public/singularity/` — read-only public Singularity images
- `/scratch/work/public/overlay-fs-ext3/` — pre-built overlay files for conda

---

## Step 1 — Transfer code + data from laptop

From the **laptop** terminal:

```bash
# Code (small)
rsync -av ~/Documents/2026/CodeProjects/SLR-RFF-BRICK/{python,julia,R,docs} \
        netid@dtn.hpc.nyu.edu:/scratch/<netid>/SLR-RFF-BRICK/

# Data (~3 GB total)
rsync -av ~/Documents/2026/CodeProjects/SLR-RFF-BRICK/data/ \
        netid@dtn.hpc.nyu.edu:/scratch/<netid>/SLR-RFF-BRICK/data/

# FaIR calibration (cached in pooch, also re-fetchable from Zenodo)
rsync -av ~/Documents/2026/CodeProjects/FaIRtoFrEDI/volcanic_solar_hist.csv \
        netid@dtn.hpc.nyu.edu:/scratch/<netid>/SLR-RFF-BRICK/data/
```

Use `dtn.hpc.nyu.edu` (data-transfer node) instead of `greene.hpc.nyu.edu` for
large rsyncs.

---

## Step 2 — Python with FaIR (Singularity overlay + conda)

Greene's recommended pattern for self-installed Python is a Singularity
container backed by an ext3 overlay file. Standard recipe:

```bash
cd $SCRATCH/SLR-RFF-BRICK

# Copy a 5 GB overlay (read-write) and a base image (read-only)
cp /scratch/work/public/overlay-fs-ext3/overlay-5GB-200K.ext3.gz .
gunzip overlay-5GB-200K.ext3.gz
mv overlay-5GB-200K.ext3 fair-overlay.ext3

# Open the container in read-write mode and install Miniconda
singularity exec --overlay fair-overlay.ext3:rw \
  /scratch/work/public/singularity/cuda12.1.1-cudnn8.9.0-ubuntu-22.04.4.sif \
  /bin/bash <<'EOF'
  cd /ext3
  wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
  bash Miniconda3-latest-Linux-x86_64.sh -b -p /ext3/miniconda3
  /ext3/miniconda3/bin/conda init bash
EOF

# Now install FaIR + deps inside the overlay
singularity exec --overlay fair-overlay.ext3:rw \
  /scratch/work/public/singularity/cuda12.1.1-cudnn8.9.0-ubuntu-22.04.4.sif \
  /bin/bash -c "source /ext3/miniconda3/etc/profile.d/conda.sh && \
                conda create -y -n fair python=3.11 && \
                conda activate fair && \
                pip install fair pandas numpy pooch scipy"
```

**Wrapper script** `bin/run-py.sh` so SLURM jobs can just call `bin/run-py.sh
script.py args...`:

```bash
#!/bin/bash
SIF=/scratch/work/public/singularity/cuda12.1.1-cudnn8.9.0-ubuntu-22.04.4.sif
OVL=$SCRATCH/SLR-RFF-BRICK/fair-overlay.ext3
singularity exec --overlay "$OVL:ro" "$SIF" \
  /bin/bash -c "source /ext3/miniconda3/etc/profile.d/conda.sh && \
                conda activate fair && python $@"
```

**One-time gotcha**: read-only mounts (`:ro`) for parallel array jobs;
write-mode mount (`:rw`) only for environment setup, never inside SLURM jobs
(corrupts the overlay).

---

## Step 3 — Julia + MimiBRICK

Greene has Julia available via modules but the latest Mimi packages need a
recent Julia. Easiest path: install via juliaup in $HOME (works without
admin):

```bash
# On a Greene login node
curl -fsSL https://install.julialang.org | sh -s -- -y
# adds ~/.juliaup/bin to PATH; source ~/.bashrc

# Project env in scratch so package files are easy to manage
cd $SCRATCH/SLR-RFF-BRICK/julia
~/.juliaup/bin/julia --project=. -e '
  using Pkg
  Pkg.Registry.add("General")
  Pkg.Registry.add(RegistrySpec(url="https://github.com/mimiframework/MimiRegistry.git"))
  Pkg.add(["Mimi", "MimiBRICK", "ArgParse", "CSV", "DataFrames", "Distributions"])
'
```

This takes ~10–15 min for first precompile. Subsequent invocations are fast.

---

## Step 4 — R + FrEDI

Greene has R via `module load r/4.4.0` (or whatever the current default is).
FrEDI installs via CRAN:

```bash
module load r/4.4.0
mkdir -p $HOME/R_libs
echo 'R_LIBS_USER="$HOME/R_libs"' >> $HOME/.Renviron
R -e 'install.packages("FrEDI", lib=Sys.getenv("R_LIBS_USER"))'
# Check
R -e 'library(FrEDI); print(get_sectorInfo()[1:5])'
```

Alternative if FrEDI isn't on CRAN (it currently is, as of 2026-05): install
from EPA's GitHub:

```bash
R -e 'remotes::install_github("USEPA/FrEDI")'
```

---

## Step 5 — Sanity-check: one-draw end-to-end

Before submitting array jobs, run **one** draw through the entire pipeline
locally on a Greene login node to catch path / module / package issues:

```bash
# Activate Python overlay
. bin/run-py.sh python/run_fair_rff.py --draw 1 --output-dir /tmp

# Then BRICK side
~/.juliaup/bin/julia --project=julia julia/run_mimibrick.jl \
  --gmst-csv /tmp/rff_draw1_temp_all841.csv \
  --metadata <(echo "sample,draw_id,rff_idx,fair_cfg_idx
lhs,0,1,575") \
  --posterior data/MimiBRICK/parameters_subsample_brick.csv \
  --output /tmp/draw1_brick.csv \
  --start-year 1850 --end-year 2100 --rcp RCP45

# Then FrEDI
module load r/4.4.0
Rscript R/brick_fredi_from_fair.R /tmp/rff_draw1_temp_all841.csv test_draw1
```

If all three steps complete on a login node, the array job will work.

---

## Step 6 — SLURM array job for FaIR pilot

Template `slurm/fair_array.sbatch`:

```bash
#!/bin/bash
#SBATCH --job-name=fair-array
#SBATCH --output=logs/fair-%A_%a.out
#SBATCH --error=logs/fair-%A_%a.err
#SBATCH --array=0-19                # 20 chunks of 100 unique RFFs each
#SBATCH --time=01:30:00             # 90 min per chunk
#SBATCH --mem=8G
#SBATCH --cpus-per-task=2
#SBATCH --partition=cpu_short

cd $SCRATCH/SLR-RFF-BRICK

CHUNK_SIZE=100
START=$(( SLURM_ARRAY_TASK_ID * CHUNK_SIZE + 1 ))
END=$((   START + CHUNK_SIZE - 1 ))

bin/run-py.sh python/lhs_climate_pilot.py \
    --rff-range "${START}:${END}" \
    --output-tag "chunk_${SLURM_ARRAY_TASK_ID}" \
    --keep-start 1850 --keep-end 2300 \
    --stochastic --n-seeds 10
```

**Pipeline already Greene-ready as of 2026-05-07:**
- `--rff-range START:END` (chunked array job)
- `--stochastic --n-seeds 10` (10 stochastic FaIR seeds per (RFF, cfg) pair)
- Cube saves before metadata loop (so a metadata bug doesn't lose hours of compute)
- OHC trajectory saved alongside GMST trajectory; both passed to MimiBRICK
  (TE component now properly coupled to per-config emissions)
- gas_partitions full-array reset between f.run() calls (multi-scenario bug)

GMST cube shape becomes `(n_rffs, 841, n_seeds, n_years)` when `n_seeds > 1`.
OHC cube has the same shape, in 10^22 J cumulative since 1750.

Validated locally 2026-05-07:
- 5 RFFs x 10 seeds with `--stochastic`: year-to-year sigma_white = 0.095 degC
  matching Berkeley Earth detrended residuals
- Cube-wide OHC at 2020 = 529 ZJ matching Cheng et al. ~500 ZJ observed
- Per-seed median is FLAT across seeds (no state carry-over)
- TE component variance share grows from 0.1% (with default RCP4.5 OHC) to
  0.4-3.2% (with FaIR OHC); AIS still dominates; sigma_internal at 2100 = 2.5 cm
  matches AR6 / Frederikse 1-3 cm estimates

Submit:
```bash
sbatch slurm/fair_array.sbatch
squeue -u netid
```

After all chunks finish, concat:
```bash
bin/run-py.sh python/scripts/concat_chunks.py outputs/chunk_*.npz \
    --output outputs/fair_full_N2000.npz
```

---

## Step 7 — Run MimiBRICK and FrEDI on the full ensemble

These are *much* faster than FaIR per draw, so they don't need array
parallelism. Run as single SLURM jobs (`slurm/mimibrick.sbatch`,
`slurm/fredi.sbatch`).

Estimated wall times at N=2000:
- MimiBRICK on cross-product: ~80 min (160 draws/s × 2000 × 841 ≈ 850k runs)
- MimiBRICK on paired LHS draws only: ~13 sec
- FrEDI: ~17 hr without optimization, ~5 hr with data.table refactor

The FrEDI step is the bottleneck. If we want quick turnaround, parallelize
FrEDI with a SLURM array (per-chunk-of-50-draws).

---

## Step 8 — Code patches: status as of 2026-05-06

| Patch | Status | File |
|-------|--------|------|
| `--rff-range START:END` | DONE | `python/lhs_climate_pilot.py` |
| `--stochastic --n-seeds N` | DONE | `python/lhs_climate_pilot.py` |
| Chunk concatenator | DONE | `python/scripts/concat_chunks.py` |
| `concat_chunks.py` for 4D cube (n_seeds dim) | NEEDED | one-line tweak |
| `R/lhs_brick.R` parameterized I/O | NEEDED | mostly hardcoded |
| FrEDI per-chunk wrapper | NEEDED | new script |
| Variance decomposition with seed dim (4-way ANOVA) | NEEDED | python/figure4_*.py |

Remaining patch effort: ~1 hour of code work (mostly path-parameterization).

---

## Resource estimates (N=2000 plan)

| Step | Wall time | Cores | Memory | Storage |
|------|-----------|-------|--------|---------|
| FaIR (20-chunk array) | 1.5 hr × 20 in parallel | 2/job | 8 GB/job | 5 GB output |
| MimiBRICK paired | 30 sec | 1 | 2 GB | 50 MB |
| MimiBRICK cross-product | 80 min | 1 | 4 GB | 1 GB |
| FrEDI (40-chunk array) | 30 min × 40 in parallel | 1/job | 4 GB/job | 500 MB |

Total billable core-hours: ~80, well within typical Greene budgets.

---

## Verification checklist (before launching N=2000)

- [ ] One-draw end-to-end runs cleanly on a login node
- [ ] FaIR results from a 1-RFF chunk match local pilot to <0.001 °C at 2100
- [ ] MimiBRICK SLR for that draw matches local to <0.1 cm at 2100
- [ ] FrEDI damages match local to within $10M at 2100 (numerical noise OK)
- [ ] Array job logs show all chunks completing (no SIGKILL / OOM)
- [ ] Concat step produces expected cube shape (`(N_unique_rffs, 841, 251)`)

---

## Pre-flight checklist for Thursday

Things you can do *now* (laptop, no Greene access needed) to make Thursday
faster:

1. ☑ Verify your Greene access works (`ssh netid@greene.hpc.nyu.edu`)
2. ☑ Apply the four code patches in §8 above (chunking, concat, etc.)
3. ☑ Tar the data directory: `cd ~/Documents/2026/CodeProjects/SLR-RFF-BRICK
       && tar czf /tmp/slr-rff-data.tgz data/` so a single rsync moves it
4. ☑ Bookmark this runbook for reference during the session
