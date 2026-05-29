# Design — balanced-factorial ANOVA cross-check for SLR Hawkins-Sutton

**Date:** 2026-05-28
**Purpose:** A model-free cross-check of the Group-Sobol SLR H-S attribution
(which depends on a surrogate that ceilings at OOF R²≈0.71 and drops ~28%
"model-unresolved" variance). The ANOVA removes the "is the emissions
correction a surrogate artifact?" objection and fixes the cfg-sparsity of the
old ANOVA-18k (15 cfg).

---

## The cheap-FaIR structure (confirmed)

FaIR GMST/OHC output is indexed only by **(rff, cfg, seed)** — `post_idx` is
ignored by `lhs_climate_v145_meta.py`. BRICK fans over `post` on top of each
FaIR cell. So a crossed factorial costs:

- **FaIR runs = n_rff × n_cfg × n_seed**  (the expensive part)
- **BRICK runs = n_rff × n_cfg × n_seed × n_post**  (cheap: ~2 min / 10k on 1 core)

This is why a 30–60k *BRICK* ensemble is far cheaper than 30–60k FaIR runs.

### Measured unit costs
- FaIR, **ANOVA regime** (measured 2026-05-29, smoke 7200 cells = 40 rff × 60 cfg ×
  3 seed, 8 cores, ~115 s compute): **≈3,760 cells/min on 8 cores (~470 cells/min/core)**.
  This is ~18× the I/O-bound baseline rate (10k rff × 1 config ≈ 26 cells/min/core)
  because the ANOVA loads few RFFs and runs many configs/RFF vectorized.
  ⇒ FaIR is NOT the binding constraint: 2 hr ≈ 450k FaIR cells.
- BRICK: ≈5,000 cells/min/core (10k/2min); parallelizable into arms.
  BRICK cells = FaIR × post, so post drives BRICK runtime + output size.
- **Binding constraint is now BRICK runtime + CSV/decomp size, not FaIR.**
  Provisional 324k design: ~18 min FaIR + ~65 min BRICK ≈ 80 min total.

---

## Recommended design (confirm before submit)

Old ANOVA-18k: 100 rff × **15 cfg** × 3 seed × 3 post = 13.5k. Weak on cfg
(15) and post (3). Because `post` is free and FaIR only scales with
rff×cfg×seed, the "size" knob is really the FaIR budget — so spend a doubling
on rff (emissions headline) + cfg, and bump post generously regardless:

| design | rff | cfg | seed | post | BRICK cells | **FaIR cells** | FaIR wall @16c* |
|---|---|---|---|---|---|---|---|
| A — original | 100 | 30 | 3 | 3 | 27,000 | 9,000 | ~21 min |
| **B — doubled (RECOMMENDED)** | **150** | **40** | 3 | **6** | 108,000 | **18,000** | **~43 min** |
| C — post-rich, A-cost | 100 | 30 | 3 | 10 | 90,000 | 9,000 | ~21 min |

*assumes near-linear core scaling (driver is parallel over rff). Real wall
likely 45–90 min incl. queue + node variance; BRICK adds <15 min; well inside
cpu_short's 6-hr cap. +equal FaIR for the pulse cube if doing pulse-SLR ANOVA.

**Recommendation (updated 2026-05-29): Option B (doubled).** Doubling the FaIR
budget (9k→18k, ~+20 min wall) buys 150 emissions levels (vs 100) + 40 cfg (vs
the old 15), and post 3→6 is free — strong on every main effect. The 108k BRICK
CSV (~900 MB w/ trajectories) ⇒ run `anova_hs_decomp.py` ON TORCH, pull the
small per-axis CSV. Baseline cube only for the total-SLR validation (add the
pulse cube only if we want the pulse-SLR ANOVA too).
Build: `--n-rff 150 --n-cfg 40 --n-seed 3 --n-post 6 --tag 108k --stratify-rff`.

Nested-ANOVA convention (from `build_ofat_anova_metadata.py`): **the same post
set is used across all seeds within each (rff,cfg) cell**, so V_internal (seed)
is not contaminated by post-sampling. Keep this.

---

## OPEN CHOICES — need Marcus's call before the real submit

1. **Weighting.** A balanced factorial is *unweighted*; the Sobol/H-S figures
   are *Wong-importance-weighted*. Options: (a) unweighted ANOVA (cleanest
   classical decomposition; expect some divergence from Sobol purely from
   weighting); (b) sample the factor *levels* via importance weights so the
   balanced grid represents the weighted distribution; (c) apply Wong weights in
   the ANOVA sums (breaks balance). **Recommend (a)** for a clean model-free
   reference, and report the weighting difference explicitly. ← confirm.
2. **Level allocation** (Option A / B / C above). ← confirm.
3. **Seed handling.** Cross 3 seeds (rigorous V_internal as an ANOVA term, as
   ANOVA-18k) vs. seed=1 + separate seed-augmentation (cheaper FaIR). Recommend
   **3 crossed seeds**. ← confirm.
4. **Baseline-only vs +pulse.** Total-SLR ANOVA (validates the 8.6%→~29%
   emissions headline) needs **baseline only**. Adding the pulse-SLR ANOVA
   doubles the FaIR cube. Recommend **baseline-only first**. ← confirm.
5. **rff level selection.** Stratify the n_rff RFFs across the cumulative-CO₂
   distribution (so emissions levels span the range) vs. random. Recommend
   **stratified by cum_co2_2100**. ← confirm.

---

## Scaffolded scripts (drafted this session)

- `python/scripts/build_anova_factorial_metadata.py` — parameterized
  (`--n-rff --n-cfg --n-seed --n-post --tag --stratify-rff`). Writes a FaIR
  metadata CSV (unique rff×cfg×seed) and a BRICK metadata CSV (crossed with
  post, nested-post convention). Mirrors the index conventions of
  `build_lhs10k_metadata.py` (rff 1-indexed value, cfg 0-indexed, seed
  0-indexed, post 1-indexed).
- `slurm/anova_factorial_fair.sh` — clone of `lhs10k_pulse_co2_pos_1gt.sh`;
  runs `lhs_climate_v145_meta.py` on the FaIR metadata → baseline cube
  `cube_v145_anova<TAG>_baseline_flat2015.npz`. (Pulse variant flagged.)
- BRICK: reuse `scripts/submit_brick_arm.sh` with the BRICK metadata + the new
  cube → `brick_anova<TAG>_baseline.csv`.
- `python/scripts/substack/anova_hs_decomp.py` — **model-free** factorial
  variance decomposition per year → emissions/climate/brick/internal main
  effects + 2-way interactions, written in the same per-axis fraction schema as
  the Sobol figures so it drops into the existing renderers for a side-by-side.

## Workflow once design is confirmed
```
# 1. build metadata (local)
python python/scripts/build_anova_factorial_metadata.py --n-rff 100 --n-cfg 30 \
    --n-seed 3 --n-post 3 --tag 27k --stratify-rff
# 2. rsync metadata to Torch, submit FaIR cube
rsync -P outputs/anova27k_fair_metadata.csv torch:/scratch/ms17839/FaIRtoFrEDI/fair_outputs/metadata_v145/
sbatch slurm/anova_factorial_fair.sh        # ~25-40 min
# 3. submit BRICK arm on the new cube (cs partition)
sbatch --export=ALL,CUBE=...anova27k_baseline_flat2015.npz,METADATA=...anova27k_brick_metadata.csv,... scripts/submit_brick_arm.sh
# 4. pull BRICK csv, decompose
python python/scripts/substack/anova_hs_decomp.py --tag 27k
# 5. compare to Sobol: overlay anova vs sobol emissions/climate/brick shares
```
