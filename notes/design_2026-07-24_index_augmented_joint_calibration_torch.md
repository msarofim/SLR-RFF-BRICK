# Design — index-augmented joint FaIR/BRICK calibration (Torch)

*M. Sarofim · NYU Marron Institute · 2026-07-24. Design for a one-way joint calibration that
couples the BRICK SLR parameters to the pre-run FaIR ensemble, run on NYU Torch (not the Mac).*

---

## 1. Why, in one paragraph

BRICK-AM is currently calibrated on the **FaIR *mean*** forcing; the FaIR uncertainty is added
downstream by pairing BRICK draws with FaIR members **independently**. That factorizes the joint
posterior `p(θ_BRICK, z | obs) ≈ p(θ_BRICK | obs, FaIR_mean) · p(z | clim obs)` and throws away the
`θ_BRICK ↔ z` coupling. The coupling is real: the FaIR ensemble spreads **19 % (sd) in historical OHC**
(50–93 ×10²² J across the 5–95 % at 2018), and `TE ∝ te_α · OHC`, so `te_α` should anti-correlate with
the FaIR OHC member. The current approach fixes `te_α` to the mean-OHC value and pairs randomly, so
off-mean members mis-fit the historical record and the level-projection bands are mis-estimated. The
fix is to sample `(θ_BRICK, z)` **jointly**, where `z` indexes the pre-run FaIR ensemble. This is exactly
the coupling SNEASY-BRICK gets for free (DOECLIM in the loop); we recover it while keeping the
AR6-constrained FaIR climate. Because FaIR is **pre-run** (not in the MCMC loop), the joint costs only
~**2× BRICK**, not FaIR-in-the-loop — but it's still 4–16 chains × 2M iters, which belongs on Torch.

Quantify the payoff first with the **reweighting diagnostic** (`diag_coupling_reweight.jl`, "step 1");
build this only if that shows the coupling materially tightens the TE/total bands.

## 2. The joint target

- **`z ∈ {1 … M}`** indexes the pre-run FaIR ensemble (M = 841 AR6-constrained members). Each member
  carries `GMST_z(t), OHC_z(t)` for 1850–2300 — already on disk as
  `curv_wide/fair_gmst_base_wide.csv` + `fair_ohc_base_wide.csv` (841 columns). **This is the "run FaIR
  first" step — done.**
- **`θ_BRICK`** = the current 39 parameters (29 physical + 10 AR(1)).
- **Posterior**

  ```
  p(θ_BRICK, z | y) ∝ L_SLR(y_SLR | θ_BRICK, forcing_z)      # existing AR(1) SLR likelihood, on forcing_z
                     · L_clim(y_GMST,OHC | z)                # per-member climate-obs weight (precomputed, length-M)
                     · π(θ_BRICK) · π(z)
  ```

  - `L_SLR` — **unchanged** from `calibrate_mcmc_ext.jl`, but evaluated with `forcing_z` in place of `fair_mean`.
  - `L_clim(z)` — a length-M vector precomputed **once**: each member's GMST + OHC likelihood vs obs
    (IGCC GMST, Gouretski/IGCC OHC). Since the ensemble is already AR6+historical constrained this is
    near-flat, but include it so `z` is properly weighted (and it's free — a constant lookup).
  - `π(θ_BRICK)` — existing priors (`param_priors.csv` + `paleo_geo_prior_ton.csv` + the A6 amp prior).
  - `π(z)` — uniform over the M equal-weight members (fold any FaIR importance weights into `L_clim`).

## 3. Sampler — Metropolis-within-Gibbs (2 BRICK runs / iter)

Keep the current **RAM** sampler for the continuous block; add a discrete **MH step** for `z`:

1. **`θ_BRICK | z`** — the *existing* RAM update, with BRICK driven by `forcing_z`. `run(model)` once.
2. **`z | θ_BRICK`** — propose `z′ ~ q(·|z)`, `run(model)` on `forcing_z′`, accept with
   `min(1, [L_SLR(z′,θ)·L_clim(z′)] / [L_SLR(z,θ)·L_clim(z)])`. `run(model)` once.

**`z`-proposal (the one design risk — mixing over 841 discrete states).** Order the members by their
dominant forcing summary (historical **OHC@2018**, or forcing-PC1) so `L_SLR` is a *smooth* function of
the ordered index; then a **local** proposal mixes well:
- 80 % local: `z′ =` a uniform neighbor within ±k of `z` in the OHC-sorted order (k ≈ 20–40).
- 20 % independence: `z′ ∝ L_clim(z′)` (global moves, escapes local traps).

Take **several `z`-steps per `θ`-step** (e.g. 3) if the `z`-autocorrelation is high — `z`-steps are cheap.

**Clustering fallback (only if `z` still mixes poorly):** k-means the M members into **K ≈ 50–100**
representative forcing trajectories (on standardized GMST+OHC curves, or on `(ECS, aerosol)`), sample
`z` over K. Fewer states → easier mixing; K≈75 keeps ~all of the forcing spread. This is the "clustering"
option — a mixing aid, not a necessity. (A continuous variant — replace `z` with 2–3 forcing PCs + an
emulator, all-continuous RAM — is a possible v2 but adds emulator error; start with the exact ensemble.)

## 4. Cost & why Torch

- BRICK run ≈ 1–2 ms; 2 runs/iter × 2M iters ≈ 1.7 h/chain of pure BRICK, ~**4–8 h/chain** with
  likelihood + RAM + `z` overhead — **~2× the current** per-chain wall.
- **Embarrassingly parallel across chains** → a SLURM array (1 chain/task) runs 8–16 chains in the wall
  time of one, frees the Mac, and gives better R̂ + a real `z`-mixing read. Memory is tiny (<4 GB/chain:
  BRICK + the `M×T×2` forcing matrix ≈ 6 MB), so `cpu_short` fits.
- If a chain needs > 4 h (the `cpu_short` cap), either use **`cs`** (no wall cap, lower priority) or
  **checkpoint** the (RAM state, `z`, chain buffer) every ~200k iters and resubmit in 4-h `cpu_short`
  chunks. Recommend building checkpointing in regardless — it makes the run robust.

## 5. Torch execution

Layout on `/scratch/ms17839/SLR-RFF-BRICK/` (Julia depot `$SCRATCH/.julia`, already has MimiBRICK).

**Push (one bundle — few files, rsync is fine):**
```bash
cd ~/Documents/2026/CodeProjects/SLR-RFF-BRICK
rsync -avz --relative \
  julia/calibrate_mcmc_joint.jl julia/brick_mengel.jl julia/brick_param_updates.jl \
  julia/glaciers_mengel_component.jl julia/patches/ julia_v2/ \
  data/observations/fair_mean_gmst_ssp245harm.csv data/observations/fair_mean_ohc_ssp245harm.csv \
  data/observations/igcc2024_gmst_with_uncertainty.csv \
  outputs/recalib_targets_ext.csv outputs/recalib_central_row.csv \
  outputs/param_priors.csv outputs/paleo_geo_prior_ton.csv outputs/Lclim_z.csv \
  outputs/mcmc/adapted_cov_ext.csv outputs/mcmc/overdispersed_starts.csv \
  slurm/joint_calib.sbatch \
  torch:/scratch/ms17839/SLR-RFF-BRICK/
# the FaIR ensemble forcing (2 files, ~18 MB) — from FaIRtoFrEDI:
rsync -avz ~/Documents/2026/CodeProjects/FaIRtoFrEDI/magicc_comparison/processed/curv_wide/fair_{gmst,ohc}_base_wide.csv \
  torch:/scratch/ms17839/SLR-RFF-BRICK/data/fair_ensemble/
```

**`slurm/joint_calib.sbatch`:**
```bash
#!/bin/bash
#SBATCH --job-name=joint_calib
#SBATCH --account=torch_pr_1041_general
#SBATCH --partition=cs                    # no wall cap; use cpu_short+checkpoint if fairshare is low
#SBATCH --time=12:00:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=2
#SBATCH --array=0-7                        # 8 chains, seeds 2026..2033
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err

set -euo pipefail
cd /scratch/ms17839/SLR-RFF-BRICK
mkdir -p logs outputs/mcmc
set +u; source ~/.bashrc; set -u          # NYU /etc/bashrc unbound-var sandwich
export JULIA_DEPOT_PATH=$SCRATCH/.julia
export JULIA_NUM_THREADS=1                 # BRICK is serial; parallelism is across array tasks
SEED=$((2026 + SLURM_ARRAY_TASK_ID))
julia --project=julia_v2 julia/calibrate_mcmc_joint.jl 2000000 $SEED \
      --tag=jointA108 --amp-mu=1.08 --amp-sigma=0.15 --overdisperse \
      --fair-ensemble=data/fair_ensemble --zsteps=3 --zwindow=30
```

**Mandatory smoke gate BEFORE production** (per the HPC protocol — never scale unproven):
```bash
# 3 chains, short (50k iters via a SMOKE env or a small first arg), spread across the array
sbatch --array=0,3,7 --time=00:30:00 slurm/joint_calib_smoke.sbatch
sacct -j <jobid> -X --format=JobID,State,ExitCode        # want State=COMPLETED, ExitCode 0:0
# confirm: chain files exist for all 3; the z-index actually MOVES (>1 distinct member); logs show progress
grep -c "z accept" logs/joint_calib_smoke_*_*.out
```
Only after all three pass → submit the full `--array=0-7`, 2M-iter array.

**Pull back + postprocess** (rsync FROM the laptop side — never from within an ssh session):
```bash
cd ~/Documents/2026/CodeProjects/SLR-RFF-BRICK
rsync -avz torch:/scratch/ms17839/SLR-RFF-BRICK/outputs/mcmc/chain_jointA108_seed*.csv outputs/mcmc/
julia --project=julia_v2 julia/diag_slr_convergence_by_chain.jl --tag=jointA108
julia --project=julia_v2 julia/postprocess_mcmc_joint.jl --tag=jointA108 --accept-slr
#   -> data/MimiBRICK/parameters_subsample_brick_mengel_jointA108.csv  (+ the sampled z per draw)
```

## 6. Code changes (from `calibrate_mcmc_ext.jl`)

Minimal delta — the SLR likelihood and priors are untouched:
1. **Load the ensemble** `GMST_z, OHC_z` (M×T matrices) + the sort order by OHC@2018 + `Lclim_z.csv`.
   Precompute `Lclim_z` once with a tiny `python/precompute_Lclim.py` (member GMST+OHC vs IGCC/Gouretski).
2. **State**: append `z` (Int) to the chain record; init each chain's `z` at a diverse member (over-disperse).
3. **`logposterior(θ, z)`**: set the forcing to `(GMST_z, OHC_z)` before the BRICK run; add `+ log Lclim[z]`.
   Everything else (the AR(1) SLR terms, the Rignot A5 anchor, the geometry/amp mapping) is identical.
4. **After each RAM θ-step**, run `--zsteps` MH updates of `z` (local ±`--zwindow` in OHC-sort order,
   20 % independence-from-`Lclim`). Log the `z`-acceptance and the current member.
5. **Checkpoint** (state, `z`, RAM covariance, rng, chain buffer) every 200k iters to
   `outputs/mcmc/ckpt_jointA108_seed<seed>.jld2`; resume if present.

## 7. Validation

1. **Recovery**: run with the ensemble replaced by a single column = `fair_mean` (M=1, `z` frozen).
   Must reproduce the current `extA108` posterior — confirms the joint code reduces to the current on
   one forcing.
2. **Convergence**: R̂ on SLR@2100/2150 (the accept-on-deliverable criterion, as now) **plus** `z`-mixing —
   distinct members visited per chain, `z`-autocorrelation, and the marginal `p(z)` (does it refine the
   FaIR climate-obs weights?).
3. **Coupling signature**: in the joint posterior, `te_α` should be **anti-correlated** with the sampled
   member's OHC@2018 (the physical mechanism). Report `corr(te_α, OHC_z)`.
4. **Bands**: compare joint vs (a) current independent-pairing and (b) the step-1 reweight. Expect the
   joint to sit **between** — tighter than the current, but retaining more spread than the (over-tightening)
   reweight, because it *generates* the compensating low-`te_α` draws the reweight cannot.

## 8. Deliverables & timeline

- `julia/calibrate_mcmc_joint.jl`, `python/precompute_Lclim.py`, `julia/postprocess_mcmc_joint.jl`,
  `slurm/joint_calib{,_smoke}.sbatch`.
- `data/MimiBRICK/parameters_subsample_brick_mengel_jointA108.csv` (θ_BRICK + sampled `z`).
- A short note: joint vs current vs reweight bands + the `te_α`–OHC coupling.
- **~1–2 weeks**: implement + recovery test (Mac, 1–2 d) → smoke on Torch (0.5 d) → production (0.5 d
  wall) → postprocess + compare (2–3 d). The `z`-mixing is the only real risk; the clustering fallback
  de-risks it.
