# NEXT-SESSION HANDOFF — execute the CO2 & CH4 pulse→SLR experiment (3 BRICK versions)

> **████ STATUS 2026-06-15: STEP 4 DONE (90k runs complete + validated). RESUME AT STEP 5. ████**
> Outputs: `outputs/pulse3brick_v145/{pre93,brick2,mengel}_{baseline,co2,ch4}.csv` on Torch (9 × 10000 rows, paired).
> Launch bug caught+fixed: cube seed-provenance string fields broke NPZ.jl (`unsupported type U171`) → moved to
> sidecar `cube_*.provenance.json`, `cell_seeds` kept in npz (existing r2 cubes stripped on Torch; builder fixed
> FaIRtoFrEDI `c5a7b84`). Re-run job 10848541 all COMPLETED ~2 min/arm. Unweighted per-unit marginal medians:
> CO2 pre93/brick2/mengel = 1.15e-2 / 5.07e-3 / 4.69e-3 cm/GtCO2@2100 (pre-#93 ≈2.3–3× = GIS pathology, expected);
> CH4 = 7.27e-4 / 3.07e-4 / 2.80e-4 cm/Tg@2100, resolvable @2300 (1Tg fix worked).
> **NEXT — Steps 5–7:** (5) Wong weights pre93+brick2 via stock `compute_lB_per_post.jl` (l_FB from the baseline
> `--save-trajs` hist + `apply_wong_weights.py`); **mengel = EQUAL-weight (Marcus), NO Wong** (already Dangendorf-
> calibrated); (6) `extract_pulse_marginals.py` weighted/plain quantiles, co2 ÷0.01, ch4 ÷1.0, per-component+total
> @2100/2150/2300; (7) headline figure 3 versions × {CO2,CH4} × component decomposition.
> ───────────────────────────────────────────────────────────────────────────
> (historical: ALL PREREQS P1–P4 were done before launch; the run was held for Marcus's go, then launched.)
> - **P1 DONE+VALIDATED** — paired r2 triplet on Torch `/scratch/.../FaIRtoFrEDI/fair_outputs/cubes_v145/`:
>   `cube_v145_lhs10ks_{baseline,pulse_co2_pos_001gt,pulse_ch4_pos_1tg}_flat2015_r2.npz`. Validation: cells_meta==metadata,
>   cell_seeds present + cal-sha matches + identical across arms (paired), pre-2030 dGMST=0, **CH4-1Tg resolvable at
>   all years** (median 3.8e-5/7.4e-6/1.9e-6 °C/Tg @2050/2100/2300), CO2 marginal unchanged (3.58e-4 °C/GtCO2@2100).
>   ⚠ cubes' `builder_git_sha`=NA (Torch dir isn't a git repo); committed builder = FaIRtoFrEDI `eba66b7`.
> - **P2 DONE** — `julia_v2` (v2.0.0) + `julia_v121` (v1.2.1) instantiated+precompiled on Torch (`/scratch/.../.julia` depot).
> - **P3 DONE (mechanics)** — `julia/compute_lB_per_post_mengel.jl` (28-col mengel l_B vs Dangendorf, sd_dang/rho_dang).
>   ✅ **Step-5 weighting RESOLVED (Marcus 2026-06-15): PRIMARY mengel = EQUAL-WEIGHTED** (posterior already
>   Dangendorf-calibrated → Wong would double-count). Step 6: mengel marginals = PLAIN/uniform quantiles;
>   pre93 + brick2 = Wong-weighted via stock `compute_lB_per_post.jl`. The mengel l_B script is for an OPTIONAL
>   Wong-weighted sensitivity only, NOT the primary path.
> - **P4 DONE** — drivers + 3 posteriors + medoid + metadata synced to Torch; **9-task production array staged**:
>   `slurm/submit_pulse3brick.sh` (NOT submitted). Torch BRICK smoke (3 versions × 10 cells) all pass, closure 0.0,
>   totals bit-identical to local.
>
> **TO LAUNCH STEP 4 (on Marcus's go):**
> ```
> ssh torch 'cd /scratch/ms17839/SLR-RFF-BRICK && sbatch slurm/submit_pulse3brick.sh'
> ```
> Then Steps 5–7: per-version Wong (resolve mengel Q first) → marginals (extract_pulse_marginals; co2 ÷0.01, ch4 ÷1.0) → headline figure.

> **████ STATUS 2026-06-14 (later same day): Steps 0–3 DONE; gate OPEN. Resume at Step 4 (Torch). ████**
> Foundations built & sanity-gated on the local Mac (Marcus: foundations-only, stop pre-launch):
> - **Step 0 env DONE** — real MimiBRICK **v1.2.1** env `julia_v121/` (pins git `repo-rev v1.2.1`, sha `94ceca2`;
>   `julia_v121/build_v121_env.jl`). Smoke OK (build→run 1850–2300, closure 4.4e-16 m).
> - **Steps 1+2 DONE, UNIFIED** — built **ONE** driver `julia/run_mimibrick_pulse_versioned.jl` with
>   `--brick-version pre93|brick2|mengel` (one output schema for all three; supersedes the schema-limited
>   `run_mimibrick_flatcube_v121.jl`). pre93→`--project=julia_v121`; brick2/mengel→`--project=julia_v2`.
>   Added NPZ to `julia_v2`.
> - **Step 3 GATE = ALL PASS / OPEN** — `python/scripts/sanity_battery_pulse3brick.py` on a 25-cell lhs10k-proxy
>   smoke (`outputs/smoke25_lhs10k_metadata.csv`), report `outputs/sanity_battery_pulse3brick_smoke.txt`.
>   Zero-pulse determinism EXACT (cross-process), sign-flip ✓, ×magnitude linear ~1% (no AIS tip @0.01Gt),
>   first-principles ✓, closure ~1e-11. Reproduced pre-#93 GIS pathology (dGIS@2100 ≈8.1e-3 vs ~4–5e-4 cm/GtCO2).
> - **3 RUNBOOK CORRECTIONS** (see CHANGELOG 2026-06-14): (1) v1.2.1 already uses `get_model(ssprcp_scenario=)`,
>   NOT `rcp_scenario=`; linear precip0 → `precip_log=false`. (2) Mengel 28-col posterior ≠ `update_brick_params!`
>   input — apply medoid central row + 18 free params (per `project_ssps_2100_mengel.jl`). (3) `brick_mengel.jl`
>   include MUST be module-scope (world-age MethodError otherwise).
> - **RESUME = Step 4, AFTER 3 prerequisites** (from the 2026-06-14 pre-launch review below). Driver verified for all
>   3 versions; production = drive `run_mimibrick_pulse_versioned.jl` over `outputs/lhs10ks_brick_metadata.csv`
>   with the per-version posterior+env+cube; then Wong (Step 5) + marginals (Step 6) + figure (Step 7).
>   NB the production lhs10ks family has POSITIVE pulses only — the sign-flip/×magnitude tests used the lhs10k proxy.
>
> **████ PRE-LAUNCH REVIEW (2026-06-14) — 3 prerequisites before Step 4; choices verified sound ████**
> VERIFIED SOUND (no action): sample lhs10ks_flat2015 cells_meta == metadata incl seeds; pairing (pre-2030 dGMST=0,
> @2000=0 → 2000-rebaseline cancels); cross-process paired determinism EXACT; CO2 0.01Gt well-resolved (15–30× float32
> ULP, ×mag linear ~1%, tipping-safe); all 3 posteriors =10000 rows (post_idx max 9999, no off-by-one); closure ~1e-11.
> - **P1 CH4 pulse size — DECISION (Marcus 2026-06-14): REGENERATE lhs10ks CH4 at 1 Tg.** The 0.01 Tg CH4 cube is
>   float32-CORRUPTED: dGMST decays below the float32 ULP (~2.4e-7 °C) after ~2060 (72% cells nonzero @2075, 34% @2100,
>   8% @2300). SLR marginal ratio (0.01-cube/1-cube) = 0.97@2100, 1.20@2150, 0.51@2300, **TE@2300 → 0** (OHC float32
>   ULP is coarsest). 1 Tg CH4 is clean AND ~10× SMALLER dGMST than CO2-1Gt → well below AIS tipping (the 0.01 choice
>   generalized CO2's tipping concern to CH4 and missed float32). **ACTION:** build
>   `cube_v145_lhs10ks_pulse_ch4_pos_1tg_flat2015.npz` via the FaIR cube driver (paired seeds, same as the others; FaIR
>   builders on Torch `/scratch/.../FaIRtoFrEDI/compute_pulse_temps_v145.py` etc.), CH4 marginal = (pulse−base)/1.0 per Tg.
>   **Keep CO2 at 0.01 Gt.** [[project_rennels_ssp245_7panel]] (float32 destroys sub-1e-4 pulses).
> - **P2 Torch envs MISSING — build before launch.** Torch has ONLY `/scratch/ms17839/SLR-RFF-BRICK/julia` (v1.0.1).
>   `julia_v2` (brick2/mengel) AND `julia_v121` (pre93) do NOT exist there — `Pkg.instantiate()`+precompile both on
>   Torch (juliaup 1.12.6 present; Manifests pin git revs so they resolve identically; arm64 local depot won't transfer).
> - **P3 Mengel Wong-l_B path missing (Step 5, not Step-4-blocking).** `compute_lB_per_post{,_v121}.jl` assume the
>   35-col posterior; the mengel 28-col needs the medoid+18-free application. Build a `_mengel` l_B variant before Step 5.
> - **Production cube/env/posterior matrix:** pre93=julia_v121 + quarantine pre-#93 posterior; brick2=julia_v2 +
>   parameters_subsample_brick.csv; mengel=julia_v2 + parameters_subsample_brick_mengel_ext.csv. Arms: baseline +
>   co2_pos_001gt (÷0.01) + ch4_pos_**1tg** (÷1.0, after P1). Use `--save-trajs true` on baseline for Wong.

**Date written:** 2026-06-14 · **Repo:** `SLR-RFF-BRICK`, build on branch **`brick-mengel`** (already
checked out, pushed to origin). **This is the runbook.** Full design/rationale:
`notes/handoff_2026-06-14_co2ch4_pulse_3brick_plan.md` (same dir) — read it once, then work from THIS file.

**Read to start cold:** this file + `~/.claude/CLAUDE.md` + `FaIRtoFrEDI/CLAUDE.md` + skills
`climate-modeling` (sanity tests), `mimibrick-quirks`, `fair-quirks`, `nyu-torch-hpc` + memories
`project_co2ch4_pulse_3brick_plan`, `project_v145_cubes_complete`, `project_pulse_size_findings`,
`project_v145_slr_pulse_response_smaller`, `project_lhs10k_brick_coupling`,
`project_brick_post_pr93_posterior_installed`, `project_brick_mengel_post2018_extension`,
`feedback_git_dash_c_convention` (use `git -C <literal abspath>`, never `cd && git`; and tell any
git-touching subagent the same).

---

## 1. The experiment (locked decisions, Marcus 2026-06-14)
Compare the **CO2 and CH4 pulse→sea-level-rise marginal** across **3 BRICK versions**, on the full
FaIR(v1.4.5, 841-cfg) × RFF-SP LHS-10k uncertainty ensemble. **Pulse year 2030; small 0.01-unit pulses
(÷0.01 → per-unit, linear, avoids AIS-tipping); physical SLR marginal only** (cm per GtCO2 and per Tg CH4)
**at 2100/2150/2300, per-component (AIS/GSIC/GIS/TE/LWS) + total; report the MEDIAN; Wong-weighted**
(per-version importance weights vs Dangendorf). No $ / no FrEDI.

## 2. The three versions
| label | model | env | posterior (10k) | what it represents |
|---|---|---|---|---|
| **pre-#93** | MimiBRICK **v1.2.1** (`rcp_scenario`, `precip_log=false`) | a real **v1.2.1** env (set up — see Step 0) | `outputs/quarantine/20260522_pre_pr93_v10x/parameters_subsample_brick.csv` (35 col, pre-#93) | **EPA-2026-rescission-comparable** baseline |
| **BRICK 2.0** | MimiBRICK **v2.0.0** (`ssprcp_scenario`, `precip_log=true`) | `julia_v2/` | `data/MimiBRICK/parameters_subsample_brick.csv` (post-#93, 35 col) | current standard |
| **BRICK-Mengel** | v2.0.0 + Mengel glacier swap (`build_brick_mengel`) | `julia_v2/` | `data/MimiBRICK/parameters_subsample_brick_mengel_ext.csv` (28 col) | recalibrated |

**pre-#93 = v1.2.1 on purpose** (EPA's likely rescission version), NOT a repro of our past vehicle env.
pre→2.0 bundles the v1.2.1→2.0.0 jump WITH the #93 GIS fix — three real configs, not a clean factorial.

## 3. What ALREADY exists (do not rebuild — exact paths)
- **Cubes** `FaIRtoFrEDI/fair_outputs/cubes_v145/` (Torch `/scratch/ms17839/FaIRtoFrEDI/fair_outputs/cubes_v145/`):
  `cube_v145_baseline.npz`, `cube_v145_pulse_co2_pos_001gt.npz`, `cube_v145_pulse_ch4_pos_001tg.npz`.
  Paired seeds; FaIR/RFF × CO2/CH4 forcing DONE. (Flat-cube schema for the v1.x driver:
  `cells_meta(n,3)=(rff_idx,fair_cfg_idx,seed_idx)`, `gmst_traj/ohc_traj (n,n_year) float32`.)
- **LHS-10k metadata** `outputs/lhs10ks_brick_metadata.csv` (10k cells: `rff_idx,fair_cfg_idx,seed_idx,post_idx,axis`).
- **Drivers:** v1.x paired `julia/run_mimibrick_paired_explicit.jl`, `julia/run_mimibrick_flatcube.jl`;
  v1.2.1 `julia/run_mimibrick_flatcube_v121.jl` + `julia/compute_lB_per_post_v121.jl`; Mengel build helper
  `julia/brick_mengel.jl` (`build_brick_mengel` / `set_forcing!` / `update_brick_mengel!`); shared param
  updater `julia/brick_param_updates.jl` (flags `precip_log`, `skip_glaciers`); marginal extractor
  `python/scripts/extract_pulse_marginals.py`.
- **Component/forcing names (identical all 3 versions):** force via
  `update_param!(m,:model_global_surface_temperature,gmst)` + `update_param!(m,:thermal_expansion,:ocean_heat_interior,ohc)`;
  extract `m[:antarctic_icesheet,:ais_sea_level]`, `[:glaciers_small_icecaps,:gsic_sea_level]`,
  `[:greenland_icesheet,:greenland_sea_level]`, `[:thermal_expansion,:te_sea_level]`,
  `[:landwater_storage,:lws_sea_level]`, total `[:global_sea_level,:sea_level_rise]`.
- **Wong infra** `FaIRtoFrEDI/compute_vehicle_wong_weights.py` + `python/apply_wong_weights.py`
  (`hetero_logl_ar1`, `ess_fraction`, `weighted_quantile`, `load_dangendorf`); ref `outputs/brick_lB_per_post_dangendorf.csv`.

## 4. EXECUTION RUNBOOK (in order)

**Step 0 — prereqs (DO FIRST; these block everything):**
- [ ] **Stand up a real MimiBRICK v1.2.1 env** for the pre-#93 arm. ⚠ The `brick-v1.2-vehicle:julia/Manifest.toml`
  hard-pins **1.0.1** — do NOT assume 1.2.1. Create/verify a 1.2.1 depot (e.g. `julia_v121/` Project+Manifest
  pinning MimiBRICK 1.2.1), confirm `get_model(rcp_scenario=)` resolves to 1.2.1.
- [ ] Confirm all 3 posteriors present locally (the two `data/MimiBRICK/*` are gitignored): pre-#93 quarantine,
  post-#93 `parameters_subsample_brick.csv`, Mengel `parameters_subsample_brick_mengel_ext.csv` (regen if missing:
  `bash run_mcmc_ext_local.sh 500000` → `julia --project=julia_v2 julia/postprocess_mcmc_ext.jl 10000`).
- [ ] Confirm cubes on Torch `/scratch`.

**Step 1 — build the version-aware paired pulse driver for B + C** (`julia/run_mimibrick_pulse_versioned.jl`):
template from `git -C <repo> show main:julia/run_mimibrick_obs_driven.jl` (version-aware build) + the
cube/paired logic of `run_mimibrick_flatcube.jl`. Flag `--brick-version {brick2,mengel}`.
- brick2: `get_model(ssprcp_scenario="ssp245",…)`; apply 35-col posterior via `update_brick_params!(m,prow; precip_log=true)`.
- mengel: `build_brick_mengel(…)`; apply 28-col via `update_brick_mengel!(m,prow,gic; precip_log=true)`.
- Inject GMST+OHC from the cube cell; **`Random.seed!(seed)` IMMEDIATELY before `get_model()`**, SAME seed for the
  paired baseline+pulse cell (else BRICK internal noise ~1e-5 m swamps the 0.01 signal — [[mimibrick-quirks]]).
- Output per cell: per-component + total at 2100/2150/2300 AND the full GMSL hist trajectory (1900–2024) for Wong.
  Keep the 5-component closure check. Window y0=1850,y1=2300.

**Step 2 — pre-#93 arm** via `run_mimibrick_flatcube_v121.jl` in the **v1.2.1 env** (Step 0) with the pre-#93
quarantine posterior + the small-pulse cubes. Confirm `rcp_scenario` / `precip_log=false`. Tag outputs `pre93`.

**Step 3 — SANITY BATTERY (GATE — before any full run), 10–50-cell smoke per version**
([[feedback_apply_sanity_tests_for_pulses]], climate-modeling skill):
(1) zero-pulse → marginal bit-identical 0; (2) sign-flip (neg cubes) → flips sign, same |Δ|;
(3) ×magnitude (0.01 vs 1) → per-unit marginals agree in the quiescent/linear regime, diverge only where AIS tips;
(4) first-principles GIS/TE vs ΔGMST; (5) closure AIS+GSIC+GIS+TE+LWS≡total. Do NOT launch the full run until all pass.

**Step 4 — full run on Torch** ([[reference_nyu_hpc]], nyu-torch-hpc): 3 versions × 3 arms
{baseline, co2_pos_001, ch4_pos_001} × 10k cells = **90k BRICK runs**. Partition `cs` (no 6-hr cap). `sbatch`
per (version,arm) → 9 array jobs over the 10k metadata, `--batch-size ~500`, ~2.5 GB/batch. Outputs →
`/scratch/.../outputs/pulse3brick_v145/`, tagged by version+arm. Envs: pre93=v1.2.1, brick2+mengel=`julia_v2`.

**Step 5 — Wong weights per version** (each posterior has its OWN `l_B` — do NOT reuse pre-#93's for the others):
each version's baseline GMSL hist traj → `l_FB` per (cfg,post) vs Dangendorf (AR(1) het.); `l_B` per posterior
member; softmax with `c` auto-tuned to ESS/N≈0.5 (`apply_wong_weights.py`) → `wong_weights_{pre93,brick2,mengel}.csv`.

**Step 6 — marginals:** paired per cell (same rff/cfg/seed/post): `ΔSLR_c(t)=(SLR_pulse_c−SLR_base_c)/0.01`
→ cm/GtCO2 (co2 arm), cm/Tg CH4 (ch4 arm), per component c + total, at 2100/2150/2300. **Weighted MEDIAN**
(+ 5–95) using the per-version Wong weights. (Mean is tipping-contaminated — use median.)

**Step 7 — outputs & figures** (Marcus drafts narrative; figures/tables/numbers are mine):
per-version per-species marginal CSVs; **headline figure** = 3 versions × {CO2, CH4} marginal-SLR distributions
(median + 5–95) at 2100/2150/2300 with the per-component (esp. GIS, AIS) decomposition showing WHERE the version
differences live. Expectation: pre-#93 GIS posterior → LARGER CO2→SLR than post-#93
([[project_v145_slr_pulse_response_smaller]] 0.0175 vs 0.0074 cm/GtCO2@2150); Mengel moves GSIC+GIS.

## 5. Risks / watch
- **v1.2.1 env** is the #1 blocker — the branch Manifest lies (pins 1.0.1). Build a real 1.2.1 env. **THREE envs total.**
- **Gitignored posteriors** — verify present; Mengel-ext regen is ~45–60 min local.
- **Tipping even at 0.01** — small but check; report median.
- **CH4→SLR is novel here** — first-principles-check the CH4:CO2 SLR-marginal ratio against the GMST pulse ratio.
- **Per-version Wong `l_B`** — regenerate per posterior; never reuse across versions.
- **pre→2.0 not a clean factor** (version jump + #93 fix bundled) — state this in the writeup.

## 6. Session state & conventions (as of 2026-06-14)
- **Branches (all pushed to origin):** `main`=BRICK 2.0 (v2.0.0 port), `brick-mengel`=all calibration+Mengel
  (build HERE), `brick-v1.2-vehicle`=old BRICK / vehicle-memo state. FaIRtoFrEDI `main`=FrEDI5 (pushed).
- **git:** use `git -C /Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK <cmd>` (LITERAL path, not a
  `$var`); never `cd && git`; brief any git-touching subagent the same ([[feedback_git_dash_c_convention]]).
- **Nothing of the pulse experiment is built yet** — Steps 1–7 are all pending. The cubes + metadata + the
  v1.x/Mengel building blocks exist; the version-aware driver, the v1.2.1 env, and the Torch runs do not.
