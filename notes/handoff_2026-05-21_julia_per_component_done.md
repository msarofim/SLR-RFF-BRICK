# Handoff — 2026-05-21 — Julia BRICK per-component output: Phase B shipped, Phase A scaffolded

Spinoff from `handoff_2026-05-20_brick_julia_per_component.md` (the Julia
work) and ultimately the parent
`FaIRtoFrEDI/notes/handoff_2026-05-20_tony_wong_followup.md`. A fresh
Claude session should be able to pick up cold by reading this note plus
the project `CLAUDE.md` and the auto-memory at
`~/.claude/projects/-Users-MarcusMarcus-Documents-2026-CodeProjects-FaIRtoFrEDI/memory/`.

## 1. What got done this session

### 1.1 Phase B (obs-driven BRICK) — fully shipped

New driver at `julia/run_mimibrick_obs_driven.jl`. Consumes a BRICK
posterior CSV plus year+value CSVs for GMST and OHC. Loops over the
posterior (10 k members) and writes year-by-year per-component SLR with
the schema

```
post_idx,
slr_2050_cm, slr_2100_cm, ais_2100_cm, gsic_2100_cm, gis_2100_cm,
te_2100_cm, lws_2100_cm,
slr_<y>, te_<y>, ais_<y>, gis_<y>, gsic_<y>, lws_<y>   for every y in window
```

All four (GMST source, OHC source) combinations have been **run on
Torch and pulled to local**:

| label     | GMST                                          | OHC                                  | output (local)                                       |
|-----------|-----------------------------------------------|--------------------------------------|------------------------------------------------------|
| obs_obs   | igcc2024_gmst_4dataset_mean (time / GMST)     | ohc_spliced_zanna_cheng              | outputs/brick_obsdriven_obs_obs_to2024.csv           |
| obs_fair  | igcc2024_gmst_4dataset_mean                   | fair_mean_ohc (cube ensemble mean)   | outputs/brick_obsdriven_obs_fair_to2024.csv          |
| fair_obs  | fair_mean_gmst                                | ohc_spliced_zanna_cheng              | outputs/brick_obsdriven_fair_obs_to2024.csv          |
| fair_fair | fair_mean_gmst                                | fair_mean_ohc                        | outputs/brick_obsdriven_fair_fair_to2024.csv         |

Each file is ~180 MB, 10 000 rows × 1058 cols, 1850–2024.

### 1.2 Phase A (FaIR-cube per-component) — scaffolded but **not re-run**

`julia/run_mimibrick_paired_explicit.jl` gained a `--save-component-trajs`
flag (independent of, and composable with, the existing `--save-trajs`
flag). When on, the output CSV picks up an extra
`{te,ais,gis,gsic,lws}_<year>` block. First-iteration sanity check
asserts `Σ components ≡ total SLR` to 1e-10 m and aborts the run on
failure (it caught the missing-LWS bug during development).

The flag is wired up and the modified driver is on Torch
(`/scratch/ms17839/SLR-RFF-BRICK/julia/run_mimibrick_paired_explicit.jl`).
The LHS-10k pipeline has **not** yet been re-submitted with the flag on,
so there are no per-component CSVs for the existing
`brick_lhs10k_{baseline,pulse,pulse0p01gtc}_to2300_*` family yet. See
§ 3 for the resubmit command.

### 1.3 Helper + SLURM script — both shipped

- `python/build_fair_mean_trajectories.py` — computes FaIR ensemble-mean
  GMST and OHC from `outputs/rff_baseline_stoch_to2300.npz` and writes
  `data/observations/fair_mean_{gmst,ohc}.csv` with the canonical
  `year,gmst_C` / `year,ohc_1e22J` schema. Already run locally; CSVs
  exist locally and on Torch.
- `slurm/submit_obs_driven_brick.sh` — 4-task SLURM array
  (`--array=1-4`, `cpu_short`, 3.5 h, 12 GB). Each task selects one
  combo by `SLURM_ARRAY_TASK_ID`. Submission `9278115` finished cleanly:
  4 × ~1m 45s elapsed on cs615/cs623, exit 0, 236 BRICK runs/s sustained
  on warm Julia depot. Logs at
  `/scratch/ms17839/SLR-RFF-BRICK/slurm/logs/obs_brick_9278115_{1..4}.{out,err}`.

## 2. Key finding: BRICK has FIVE SLR contributors, not four

The original handoff named four: AIS, GIS, GSIC, TE. BRICK's
`:global_sea_level :sea_level_rise` actually sums **five** Mimi
sub-components — the four above plus `:landwater_storage
:lws_sea_level`. Omitting LWS leaves a ~3 mm residual at 2024
(BRICK's posterior parameterises it as a stochastic small contribution).
The closure-check assert caught this during development. Both Julia
drivers in this session extract all 5. See memory
`project_brick_five_components.md`.

Note also: the BRICK `:global_sea_level` namespace has misspelled
parameter names (`slr_greeland_icesheet` / `slr_antartic_icesheet`). Do
not "fix" these in our drivers — they are the upstream Mimi names and
must be matched literally.

## 3. Implicit cross-combo sanity check (use as a regression test)

Year-2024 medians across the four obs-driven CSVs show clean component
decoupling — a free physical-correctness test that any future
modification to the obs-driven driver must keep passing:

```
     combo |   slr_2024      ais_2024     gsic_2024      gis_2024       te_2024      lws_2024
------------------------------------------------------------------------------------------
   obs_obs |     +6.171        +0.754        +2.197        +1.904        +1.000        +0.289
  obs_fair |     +6.238        +0.755        +2.197        +1.904        +1.063        +0.289
  fair_obs |     +5.369        +0.780        +1.952        +1.322        +1.000        +0.289
 fair_fair |     +5.435        +0.781        +1.952        +1.322        +1.063        +0.289
```

Properties this confirms:
- TE depends **only** on OHC (te_2024 identical between obs_obs/fair_obs
  and between obs_fair/fair_fair).
- AIS/GSIC/GIS depend **only** on GMST.
- LWS depends on **neither** (identical across all four — purely
  posterior-driven).
- Tony's headline diagnostic at 2024: the 0.8 cm obs-vs-FaIR total-SLR
  gap is ~0.80 cm GMST-driven and ~0.07 cm OHC-driven. Obs gives more
  SLR than FaIR-mean because IGCC 2024 sits above the FaIR ensemble
  mean.

## 4. Files touched / created

New:
- `julia/run_mimibrick_obs_driven.jl`
- `python/build_fair_mean_trajectories.py`
- `slurm/submit_obs_driven_brick.sh`
- `data/observations/fair_mean_gmst.csv`
- `data/observations/fair_mean_ohc.csv`
- `outputs/brick_obsdriven_{obs_obs,obs_fair,fair_obs,fair_fair}_to2024.csv` (local + Torch)

Modified:
- `julia/run_mimibrick_paired_explicit.jl` (added `--save-component-trajs`
  flag, LWS column block, closure-check assert)

**Nothing is committed.** All of the above are loose on Mac and on
Torch under `/scratch`. No commit, PR, or tag yet.

## 5. Pending work — next session can resume from here

### 5.1 Phase A re-run on the existing LHS-10k cube (this is the unblocker)

The component-output flag is wired into the paired driver but the
LHS-10k pipeline has not been re-submitted. Add
`--save-component-trajs true` to both `julia` invocations inside
`slurm/submit_lhs10k_brick_pipeline.sh` (steps 1 and 2), or run as a
one-shot:

```
ssh torch 'cd /scratch/ms17839/SLR-RFF-BRICK && sbatch slurm/submit_lhs10k_brick_pipeline.sh'
```

(assuming the script is patched with the flag — it is not yet). The
existing total-only output continues to work; the wider CSV adds
~5 × 451 = 2255 columns. Downstream `apply_wong_weights.py` and the
pulse-CSV merge step join on the metadata keys, not on trajectory
columns, so they are unaffected.

### 5.2 Tony Wong component-comparison plotting

Outputs are local at
`~/Documents/2026/CodeProjects/SLR-RFF-BRICK/outputs/brick_obsdriven_*_to2024.csv`.
Build the overlay plot — per-component bands (median + 5/95 %) for each
of AIS, GSIC, GIS, TE against observed component series (Frederikse 2020
for AIS/GIS/GSIC; Dangendorf 2024 / NOAA STAR for total). Existing
overlay code at `python/scripts/substack/obs_overlay_slr.py` is the
right shape to extend; do not modify it without first reading its
expected schema.

The new wide schema is the headline contract:
`slr_<y>`, `te_<y>`, `ais_<y>`, `gis_<y>`, `gsic_<y>`, `lws_<y>` for
y in 1850..2024. All values in cm, re-referenced to year 2000.

### 5.3 Phase C (sign-flip symmetry per component) — still blocked

Requires the negative-pulse cube on the Python side, which still does
not exist. Defer to the new-ensemble work (handoff
`FaIRtoFrEDI/notes/handoff_2026-05-20_tony_wong_followup.md`).

### 5.4 Substack post correction + AGU Chapman per-component panel

Both wait on §5.2 plots. Memory `project_agu_chapman_poster.md` has
the ~2026-06-01 print-ready-PDF deadline.

### 5.5 Window: 1850–2024 vs longer horizon

Obs-driven runs are historical only. Extending past 2024 needs a forcing
continuation choice (RFF? SSP? obs-continued?) — flagged in the original
handoff as an open question and still unresolved.

## 6. Non-obvious state to be aware of

- **Pre-staged obs CSVs were not actually pre-staged on Torch.** Both
  `data/observations/igcc2024_gmst_4dataset_mean.csv` and
  `data/observations/ohc_spliced_zanna_cheng.csv` were missing at the
  start of this session despite the prior handoff listing them as
  pre-staged. Synced in-session. Do not trust similar
  "pre-staged on Torch" claims without `ssh torch 'ls -la <path>'`
  verification first.
- **Cube on Torch is still `rff_baseline_stoch_to2300.npz`** (3D / .npz
  form). The paired driver auto-detects and prefers `--npy-stem` if
  available; obs-driven driver does not touch the cube at all (uses
  `fair_mean_*.csv` for cube-mean trajectories).
- **Julia depot on Torch lives at `/scratch/ms17839/.julia`** — set via
  `export JULIA_DEPOT_PATH=$SCRATCH/.julia` in the SLURM script's
  bashrc-sandwich block. Already populated, ~3 GB, MimiBRICK precompiled.
  This is why Torch hit 236 runs/s on a cold submit while my Mac smoke
  test ran at 2.6 runs/s.
- **One Julia stderr warning is expected and harmless:** "MCMCDiagnostics.jl
  has been deprecated in favor of MCMCDiagnosticTools.jl" — comes from a
  MimiBRICK dependency, not our drivers.

## 7. Memory entries added this session

- `project_brick_five_components.md` — BRICK 5-component finding + LWS gotcha.
- `feedback_commands_in_code_blocks.md` — always put runnable commands in
  fenced blocks for UI copy-text affordance.

## 8. Pointers (unchanged from prior handoff)

- `julia/run_mimibrick_paired_explicit.jl` — modified driver
- `julia/run_mimibrick_obs_driven.jl` — new driver
- `julia/compute_lB_per_post.jl` — adjacent utility (unchanged)
- `python/scripts/substack/obs_overlay_slr.py` — Python overlay code that
  consumes the wide CSV schema for plotting
- `python/apply_wong_weights.py` — Wong-weighting machinery, unchanged
  for this work
- `BRICK_notes.md`, `METHODS.md` — repo-level docs that need updates
  after § 5.2 plotting lands
