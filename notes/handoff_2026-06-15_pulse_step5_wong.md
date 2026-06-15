# HANDOFF — CO2/CH4 pulse→SLR (3 BRICK versions): execute STEPS 5–7 (Wong → marginals → figure)

**Date:** 2026-06-15 · **Repo:** `SLR-RFF-BRICK`, branch **`brick-mengel`** · **Steps 0–4 are DONE.**
This handoff covers the remaining Steps 5 (Wong weights), 6 (weighted marginals), 7 (headline figure).

**Read to start cold:** this file + `~/.claude/CLAUDE.md` + `FaIRtoFrEDI/CLAUDE.md` + skills
`mimibrick-quirks`, `nyu-torch-hpc`, `obs-model-comparisons` + memories `project_co2ch4_pulse_3brick_plan`,
`project_lhs10k_brick_coupling`, `feedback_ensemble_sampling_adequacy`, `project_obs_data_sources`,
`feedback_git_dash_c_convention`. The design/runbook is `notes/handoff_2026-06-14_co2ch4_pulse_3brick_NEXT-SESSION.md`
(its top status block is current); this file is the Step-5+ detail.

---

## 0. State as of 2026-06-15 (what's DONE)
- **Step 4 COMPLETE + validated.** 90k BRICK runs (3 versions × 3 arms × 10k). Outputs on Torch:
  `/scratch/ms17839/SLR-RFF-BRICK/outputs/pulse3brick_v145/{pre93,brick2,mengel}_{baseline,co2,ch4}.csv`
  — 9 files × 10000 rows, fully paired (same rff/cfg/seed/post per cell across arms; `--seed 2026`).
  Columns: `axis,rff_idx,fair_cfg_idx,seed_idx,post_idx, slr_{2100,2150,2300}_cm,
  {ais,gsic,gis,te,lws}_{2100,2150,2300}_cm` (all cm, re-referenced to year 2000). The **baseline** arms
  additionally have `slr_<year>` for 1850–2300 (from `--save-trajs true`) — that GMSL history is the l_FB input.
- **Cubes (realization r2)** on Torch `/scratch/.../FaIRtoFrEDI/fair_outputs/cubes_v145/`:
  `cube_v145_lhs10ks_{baseline,pulse_co2_pos_001gt,pulse_ch4_pos_1tg}_flat2015_r2.npz` (+ `.provenance.json`
  sidecars; `cell_seeds` in the npz). CO2 pulse = 0.01 GtCO2 (÷0.01), CH4 = 1 TgCH4 (÷1.0).
- **Unweighted per-unit marginal medians (sanity target for Step 6):**
  CO2 cm/GtCO2 @2100 / @2300 — pre93 1.15e-2 / 3.11e-2 ; brick2 5.07e-3 / 1.00e-2 ; mengel 4.69e-3 / 1.15e-2.
  CH4 cm/Tg @2100 / @2300 — pre93 7.27e-4 / 5.94e-4 ; brick2 3.07e-4 / 1.74e-4 ; mengel 2.80e-4 / 2.12e-4.
  (pre-#93 CO2→SLR ≈ 2.3–3× post-#93 = the GIS pathology, expected.)
- **Envs:** pre93 → `julia --project=julia_v121` (MimiBRICK v1.2.1); brick2/mengel → `--project=julia_v2` (v2.0.0).
  Both built+precompiled on Torch (`JULIA_DEPOT_PATH=/scratch/ms17839/.julia`). FaIR conda env (numpy/pandas):
  `conda activate /scratch/ms17839/SLR-RFF-BRICK/envs/fair`.

## 1. WEIGHTING DECISION (Marcus 2026-06-15) — LOCKED
- **pre93, brick2: Wong-weighted** (each its OWN l_B; their posteriors are not directly Dangendorf-conditioned).
- **mengel (PRIMARY): EQUAL-WEIGHTED — NO Wong.** Its posterior was MCMC-calibrated directly to Dangendorf, so
  Wong would double-count. Step 6 reports mengel marginals as PLAIN/uniform quantiles. `compute_lB_per_post_mengel.jl`
  exists ONLY for an OPTIONAL Wong-weighted mengel sensitivity — not the primary path.
- Obs series = **Dangendorf 2024** (`data/observations/dangendorf_2024_gmsl.csv`). `--obs dangendorf` MUST match
  between the l_B Julia script and `apply_wong_weights.py`, or (l_FB − l_B) is meaningless.

## 2. STEP 5 — per-version Wong weights
Wong weight ∝ softmax(c·(l_FB − l_B)); `c` auto-tuned so ESS/N ≈ 0.5. l_FB = FaIR-forced fit to Dangendorf
(per cfg,post; from the baseline arm's saved GMSL history). l_B = "BRICK as calibrated" default-backbone fit
(per post). Build per version:

**(a) pre93 l_B — script EXISTS:**
```
julia --project=julia_v121 julia/compute_lB_per_post_v121.jl \
  --posterior outputs/quarantine/20260522_pre_pr93_v10x/parameters_subsample_brick.csv \
  --obs dangendorf --output outputs/brick_lB_per_post_pre93.csv
```
(v1.2.1: ssprcp_scenario="ssp245", precip_log=false — correct as-is.)

**(b) brick2 l_B — BUILD ITEM (no v2.0.0 variant yet).** The stock `compute_lB_per_post.jl` is v1.0.1
(`rcp_scenario`, precip_log=false) and will NOT run in v2.0.0. Make a v2.0.0 variant = the `_v121.jl` script but
with **precip_log=true** in the `update_brick_params!` call, run in `julia_v2`:
```
# after adding precip_log=true (e.g. a --precip-log flag, default false):
julia --project=julia_v2 julia/compute_lB_per_post_brick2.jl \
  --posterior data/MimiBRICK/parameters_subsample_brick.csv \
  --obs dangendorf --output outputs/brick_lB_per_post_brick2.csv
```
Verify l_B is finite & sane (median ~hundreds, like the mengel smoke 109–200).

**(c) mengel: SKIP** (equal-weight primary).

**(d) l_FB + weights** via `python/apply_wong_weights.py` (`hetero_logl_ar1`, `ess_fraction`, `weighted_quantile`,
`load_dangendorf`). ⚠ It was written for the OLD single "paired CSV" (pulse+baseline+trajectory in one file). Our
Step-4 outputs SPLIT the arms, so it likely needs a small adaptation to read l_FB from `{version}_baseline.csv`
(the `slr_<year>` 1850–2300 cols) + the matching `outputs/brick_lB_per_post_{pre93,brick2}.csv`. Use the SAME
2000-baseline normalisation as the Julia l_B (it already does). `--ess-target 0.5 --obs dangendorf`. Output:
`outputs/wong_weights_{pre93,brick2}.csv` (per-cell w_norm). Report each version's ESS fraction + the tuned `c`.

## 3. STEP 6 — paired marginals (weighted)
Per cell, paired on (rff_idx,fair_cfg_idx,seed_idx,post_idx): `ΔSLR_c(t) = (pulse_c − baseline_c)/size`,
size = 0.01 for co2 (→ cm/GtCO2), 1.0 for ch4 (→ cm/Tg), per component c ∈ {ais,gsic,gis,te,lws} + total, at
2100/2150/2300. `python/scripts/extract_pulse_marginals.py` does the differencing (check/point it at the split CSVs).
Then **weighted quantiles** (median + 5–95):
- pre93, brick2 → use `wong_weights_{version}.csv` (`weighted_quantile`).
- mengel → UNIFORM weights (plain quantiles).
Sanity-check medians against §0's unweighted numbers (Wong shifts them modestly; don't expect order-of-magnitude moves).
Output per-version per-species marginal CSVs (per-component + total, 2100/2150/2300, weighted q05/q50/q95).

## 4. STEP 7 — headline figure (Marcus drafts narrative; figures/tables/numbers are mine)
3 BRICK versions × {CO2, CH4}: marginal-SLR distributions (median + 5–95) at 2100/2150/2300, WITH the
per-component (esp. GIS, AIS) decomposition showing WHERE the version differences live. Expectation: pre-#93 GIS
gives the largest CO2→SLR; Mengel moves GSIC+GIS. Labels/titles from named constants (per CLAUDE.md). Leave text
boxes as placeholders for Marcus.

## 5. Gotchas / watch
- **Pairing is by KEY, not row order** — always merge on (rff,cfg,seed,post); the driver is robust to row order but
  always verify 10000 paired rows per (version, species).
- **CH4 ÷1.0, CO2 ÷0.01** — different pulse sizes per species (CH4 went to 1 Tg because 0.01 Tg was float32-corrupted;
  see CHANGELOG 2026-06-14/15). Don't divide CH4 by 0.01.
- **NPZ/string-provenance trap** (if you ever rebuild cubes): keep only numeric arrays in the .npz; string provenance
  goes to the sidecar JSON. NPZ.jl errors `unsupported type U171` on string arrays (the 2026-06-15 launch bug).
- **mengel = equal-weight** — do NOT apply Wong to the primary mengel result.
- **git:** `git -C /Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK <cmd>` (literal path; never `cd && git`).
  FaIRtoFrEDI has an unrelated in-progress MAGICC change (`magicc_comparison/`, CHANGELOG) — NOT part of this work; leave it.
- **Torch SSH is flaky** (ProxyJump broken-pipe) — retry; verify sbatch landed via `squeue`/`sacct` before assuming.

## 6. Done-state pointers
- Step-4 outputs: Torch `outputs/pulse3brick_v145/*.csv`. Cubes: Torch `.../cubes_v145/*_r2.npz` (+ sidecars).
- Drivers on Torch `julia/`: `run_mimibrick_pulse_versioned.jl` + includes; sbatch `slurm/submit_pulse3brick.sh`.
- l_B scripts: `compute_lB_per_post_v121.jl` (pre93 ✓), `compute_lB_per_post.jl` (v1.0.1 stock),
  `compute_lB_per_post_mengel.jl` (sensitivity only). brick2 variant = TO BUILD.
- All Step 0–4 work committed on `brick-mengel` (pushed); CHANGELOG up to date through Step 4.
