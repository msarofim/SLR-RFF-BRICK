# Handoff/Plan — CO2 & CH4 pulse→SLR across 3 BRICK versions on FaIR/RFF uncertainty

**Date:** 2026-06-14 · **Repo:** `SLR-RFF-BRICK` (build on branch `brick-mengel`; pre-#93 arm uses a
**MimiBRICK v1.2.1** env). FaIR/cube side in `FaIRtoFrEDI`. **Status:** SCOPED, not yet built.
**Self-contained resume:** read this + `~/.claude/CLAUDE.md` + skills `climate-modeling`,
`mimibrick-quirks`, `fair-quirks`, `nyu-torch-hpc` + memories `project_v145_cubes_complete`,
`project_pulse_size_findings`, `project_v145_slr_pulse_response_smaller`, `project_lhs10k_brick_coupling`,
`project_brick_post_pr93_posterior_installed`, `project_brick_mengel_post2018_extension`,
`project_v145_multidecade_uncertainty_results`.

---

## 0. Goal
Compare the **CO2 and CH4 pulse→sea-level-rise marginal** across three BRICK calibration versions,
propagated through the full FaIR(v1.4.5, 841-config) × RFF-SP uncertainty ensemble. Isolates how the
#93 GIS-posterior fix and the Mengel glacier recalibration each move the SC-SLR-relevant pulse response.

## 1. The three versions (Marcus 2026-06-14)
| label | model | env | posterior (10k draws) | isolates |
|---|---|---|---|---|
| **pre-#93** | MimiBRICK **v1.2.1** (`rcp_scenario`, `precip_log=false`) — the version EPA most likely used in the 2026 rescission | **v1.2.1 env** + `*_v121.jl` drivers (see ENV note) | `outputs/quarantine/20260522_pre_pr93_v10x/parameters_subsample_brick.csv` (35 col, pre-#93 GIS-pathology) | the **EPA-2026-rescission-comparable** BRICK = comparison baseline |
| **BRICK 2.0** | MimiBRICK **v2.0.0** (`ssprcp_scenario`, `precip_log=true`) | `julia_v2/` | `data/MimiBRICK/parameters_subsample_brick.csv` (post-#93, 35 col) | current standard vs EPA-era (pre→2.0 bundles the v1.2.1→2.0.0 jump **+** #93 fix — see note) |
| **BRICK-Mengel** | v2.0.0 + Mengel glacier swap | `julia_v2/` | `data/MimiBRICK/parameters_subsample_brick_mengel_ext.csv` (28 col, `gic_*`+`ais_ocean_temperature₀`) | the **Mengel recalibration** (2.0→Mengel) |

**pre-#93 = the EPA-2026-rescission-comparable BRICK (Marcus 2026-06-14).** = MimiBRICK **v1.2.1** + the
**pre-#93** GIS-pathology posterior. Chosen deliberately as the baseline because **v1.2.1 is the version EPA
most likely used in the 2026 rescission** — the appropriate comparison — **regardless of which version our own
past vehicle memo happened to run.** BRICK 2.0 and Mengel are then "how the pulse→SLR response changes vs the
EPA-era BRICK." (This resolves the earlier 1.0.1-vs-1.2.1 question: pin **1.2.1** on purpose, not by repro.)

> **ENV SETUP (build prereq).** The pre-#93 arm needs a **MimiBRICK v1.2.1** environment + the `*_v121.jl`
> drivers (`run_mimibrick_flatcube_v121.jl`, `compute_lB_per_post_v121.jl`). v1.2.1 uses
> `get_model(rcp_scenario=)` (rcp API, like 1.0.x) with `precip_log=false`. **NB the committed
> `brick-v1.2-vehicle:julia/Manifest.toml` currently hard-pins `version = "1.0.1"`** — do NOT assume it's 1.2.1;
> set up/verify a true 1.2.1 env first. Sanity-check the pre-#93 35-col posterior runs cleanly through v1.2.1.

> **NOTE — pre→2.0 is NOT a clean single factor.** pre-#93 (v1.2.1 + pre-#93 posterior) → BRICK 2.0 (v2.0.0 +
> post-#93) bundles the model-version jump (1.2.1→2.0.0) WITH the #93 GIS-posterior fix. The three arms are three
> real-world BRICK *configs* (EPA-era / current-standard / recalibrated), not a clean factorial. If a #93-only
> isolation is ever wanted, add a v2.0.0+pre-#93 arm.

> **RELATED VEHICLE-MEMO DECISION (Marcus 2026-06-14):** going forward the **vehicle memo** should also use the
> **pre-#93 posterior** (and v1.2.1) for best comparability with EPA — a change to the vehicle pipeline, tracked
> separately from this pulse study (the current canonical vehicle results may have used post-#93; verify when revisiting).

`data/MimiBRICK/*` are gitignored (regenerable). Verify all three posteriors are present before launch;
Mengel-ext regen = `bash run_mcmc_ext_local.sh 500000` → `julia --project=julia_v2 julia/postprocess_mcmc_ext.jl 10000`.

## 2. Locked methodological decisions (Marcus 2026-06-14)
1. **Pulse year = 2030 only** — use existing cubes; no new FaIR compute.
2. **Pulse size = small 0.01-unit, linear** — 0.01 GtCO2 / 0.01 Tg CH4; ÷0.01 to per-unit. Avoids the
   AIS-tipping contamination that 1-GtCO2 pulses cause in some draws ([[project_pulse_size_findings]]).
   STILL sanity-check tipping even at 0.01 (a few draws may sit near threshold).
3. **Metric = physical SLR marginal** — ΔSLR per GtCO2 and per Tg CH4 at **2100 / 2150 / 2300**,
   **per component (AIS/GSIC/GIS/TE/LWS) + total**, distribution across the ensemble, per version. No $/FrEDI.
4. **Weighting = Wong-weighted only** — per-version importance weights (each posterior's own historical
   fit to Dangendorf 2024). [[feedback_ensemble_sampling_adequacy]].

## 3. What ALREADY exists (do not rebuild)
- **Cubes** (`FaIRtoFrEDI/fair_outputs/cubes_v145/`, Torch `/scratch/ms17839/FaIRtoFrEDI/fair_outputs/cubes_v145/`):
  `cube_v145_baseline.npz`, `cube_v145_pulse_co2_pos_001gt.npz`, `cube_v145_pulse_ch4_pos_001tg.npz`
  (+ ±1 and neg variants we won't use). Schema: `gmst_traj/ohc_traj (n_rff,841,n_seed,n_keep) float32`,
  paired seeds. **FaIR/RFF × CO2/CH4 forcing is DONE.**
- **LHS-10k metadata** `outputs/lhs10ks_brick_metadata.csv` (10k cells: `rff_idx,fair_cfg_idx,seed_idx,post_idx,axis`).
  Canonical joint sample ([[project_lhs10k_brick_coupling]], [[feedback_ensemble_sampling_adequacy]]).
- **v1.x paired pulse driver** `julia/run_mimibrick_paired_explicit.jl` + `julia/run_mimibrick_flatcube.jl`
  (faster, flat-cube schema), and `python/scripts/extract_pulse_marginals.py`. These run **pre-#93 (A) as-is**.
- **Wong-weight infra** `FaIRtoFrEDI/compute_vehicle_wong_weights.py` + `python/apply_wong_weights.py`
  (`hetero_logl_ar1`, `weighted_quantile`, `load_dangendorf`); reference `outputs/brick_lB_per_post_dangendorf.csv`.

## 4. What to BUILD
### 4a. Version-aware paired pulse driver for B + C (v2.0.0 env)
New `julia/run_mimibrick_pulse_versioned.jl` (start from `git show main:julia/run_mimibrick_obs_driven.jl`
version-aware build + the cube/paired logic of `run_mimibrick_flatcube.jl`). Flag `--brick-version {brick2,mengel}`.
- **Build:** `brick2` → `MimiBRICK.get_model(ssprcp_scenario="ssp245",...)`; `mengel` → `build_brick_mengel(...)`
  (`include("julia/brick_mengel.jl")`; swaps glacier slot).
- **Posterior apply:** `brick2` → `update_brick_params!(m,prow; precip_log=true)` (35-col);
  `mengel` → `update_brick_mengel!(m,prow,gic; precip_log=true)` reading the 28-col `gic_*`+`ais_ocean_temperature₀`.
- **Forcing (identical all versions):** `update_param!(m,:model_global_surface_temperature,gmst)` +
  `update_param!(m,:thermal_expansion,:ocean_heat_interior,ohc)` from the cube cell.
- **CRITICAL paired determinism** ([[mimibrick-quirks]]): `Random.seed!(seed)` IMMEDIATELY before `get_model()`,
  SAME seed for the paired baseline and pulse cell, else BRICK internal noise (~1e-5 m AIS) swamps the 0.01 signal.
- **Extract (names identical all versions):** `m[:antarctic_icesheet,:ais_sea_level]`,
  `[:glaciers_small_icecaps,:gsic_sea_level]`, `[:greenland_icesheet,:greenland_sea_level]`,
  `[:thermal_expansion,:te_sea_level]`, `[:landwater_storage,:lws_sea_level]`, `[:global_sea_level,:sea_level_rise]`.
  Output per cell: per-component + total at 2100/2150/2300 **and** the full GMSL hist trajectory (1900–2024)
  needed for the Wong baseline fit. Keep the 5-component closure check.
- **Window:** y0=1850, y1=2300 (cubes/forcing reach 2301; thru-2300 metric).

### 4b. pre-#93 (A) via the v1.2.1 `*_v121.jl` path
Run `run_mimibrick_flatcube_v121.jl` in a **MimiBRICK v1.2.1 env** with the **pre-#93 quarantine**
posterior + the small-pulse cubes. Mostly wiring, but FIRST set up/verify the 1.2.1 env (the
`brick-v1.2-vehicle` Manifest pins 1.0.1 — see ENV note in §1). Confirm `rcp_scenario`/`precip_log=false`.
**THREE Julia envs in one study** (v1.2.1 pre93 / v2.0.0 brick2 / v2.0.0 Mengel) — tag A outputs `pre93`.

## 5. Run matrix & marginal
- **3 versions × 3 arms {baseline, co2_pos_001, ch4_pos_001} × 10k LHS cells = 90k BRICK runs.** Torch.
- Marginal per cell, paired (same rff/cfg/seed/post): `ΔSLR_c(t) = (SLR_pulse_c(t) − SLR_base_c(t))/0.01`
  → cm per GtCO2 (co2 arm) / cm per Tg CH4 (ch4 arm), per component c + total, at 2100/2150/2300.
- **Report MEDIAN, not mean** ([[project_pulse_size_findings]] — CO2 marginal mean contaminated by AIS tipping).

## 6. Wong weighting (per version)
Each version's baseline GMSL hist trajectory (from §4 baseline arm) → `l_FB` per (cfg,post) via AR(1)
het. likelihood vs Dangendorf; `l_B` per posterior member; softmax with `c` auto-tuned to ESS/N≈0.5
(`apply_wong_weights.py`). Produce `wong_weights_{pre93,brick2,mengel}.csv`. Then weighted quantiles of
the marginals. NB pre-#93 vs post-#93 vs Mengel each need their OWN `l_B`-per-post (different posteriors).

## 7. Sanity battery BEFORE headline numbers ([[feedback_apply_sanity_tests_for_pulses]], climate-modeling skill)
Run on a 10–50 cell smoke per version: (1) **zero-pulse** → marginal bit-identical 0 (paired seeds);
(2) **sign-flip** (use the neg cubes) → marginal flips sign, same magnitude; (3) **×magnitude** (0.01 vs 1)
→ per-unit marginals agree in the linear/quiescent regime, diverge only where AIS tips; (4) **first-principles**
GIS/TE magnitude vs ΔGMST; (5) **closure** AIS+GSIC+GIS+TE+LWS≡total. Gate the full run on these.

## 8. Torch launch ([[reference_nyu_hpc]], nyu-torch-hpc skill)
Partition `cs` (no 6-hr cap; 90k runs). `sbatch` per (version,arm) → 9 array jobs over the 10k metadata,
`--batch-size ~500`, ~2.5GB/batch. Depot/env: Mengel+brick2 use `julia_v2` (juliaup 1.12, MimiBRICK v2.0.0);
pre93 uses a **MimiBRICK v1.2.1** env (set up/verify — not the 1.0.1-pinned brick-v1.2-vehicle Manifest).
Cubes already on `/scratch`. Outputs → `/scratch/.../outputs/pulse3brick_v145/`.

## 9. Outputs & figures (Marcus drafts narrative; I do figures/tables/numbers)
- Per-version per-species marginal CSVs (per-component + total, 2100/2150/2300, weighted quantiles).
- **Headline figure:** 3 BRICK versions × {CO2, CH4}, marginal-SLR distributions (median + 5–95) at 2100/2150/2300,
  with the per-component (esp. GIS, AIS) decomposition showing WHERE the version differences live.
  Expectation from memory: pre-#93 GIS posterior gives a LARGER CO2→SLR pulse than post-#93
  ([[project_v145_slr_pulse_response_smaller]]: 0.0175 vs 0.0074 cm/GtCO2@2150); Mengel changes GSIC+GIS.

## 10. Risks / watch
- **THREE Julia envs** (MimiBRICK v1.2.1 for pre93, v2.0.0 for brick2/mengel) — don't cross-contaminate; tag outputs.
  Setting up a real v1.2.1 env is a build prereq (the brick-v1.2-vehicle Manifest pins 1.0.1, not 1.2.1).
- **Gitignored posteriors** — verify all 3 present before launch (esp. Mengel-ext regen cost).
- **Tipping at 0.01** — small but check; report median.
- **CH4→SLR is novel here** — no prior benchmark; first-principles-check the CH4:CO2 SLR ratio against the
  GMST pulse ratio (CH4 should track its shorter-lived forcing).
- **Per-version Wong `l_B`** — must regenerate per posterior; don't reuse the pre-#93 `l_B` for brick2/mengel.
