# Handoff — BRICK-Mengel: convergence → posterior-predictive → SSP-2100 projections

**Date:** 2026-06-13 · **Repo:** `SLR-RFF-BRICK`, branch `brick-mengel` (formerly `brick-v2-precip-shim`)
(this note + the BRICK-Mengel lineage live in `SLR-RFF-BRICK/notes/`; not on main). **Env:** Julia `julia_v2/` (MimiBRICK v2.0.0,
depot `edplP`); Python `~/climate-env`. **Self-contained resume:** read this +
`~/.claude/CLAUDE.md` + the prior handoff
`notes/handoff_2026-06-12_brick_mengel_calibration.md` + memories
`project_brick_mengel_postpred`, `reference_mengel2016_glacier_model`,
`project_brick_ais_overshoot_anto_alpha`, `mimibrick-quirks` skill.

---

## 0. TL;DR
Completed the recalibration arc from the 2026-06-12 handoff: **MCMC convergence
verified, posterior-predictive + sanity passed, and the headline SSP-2100 projection
ensemble produced.** All committed on `brick-mengel`. The one substantive open
science question is whether to **extend the AIS calibration past 2020** (post-2020 GRACE-FO
"pause"); assessment + plan in §4.

## 1. What got done this session (all committed)
1. **Convergence (commit `431e361`)** — re-ran MCMC at **500k** (was 300k), cov-seeded from
   `outputs/mcmc/adapted_cov.csv`. **27/28 params R̂<1.05** (was 24/28). Sole straggler
   `rho_ais` R̂=1.105 (ESS 2216) is an **AR(1) noise nuisance** that lives only in the
   likelihood (`hetero_logl_ar1`), NOT the forward model → **Marcus accepted as non-blocking.**
   300k run archived to `outputs/mcmc/archive_run1_300k_20260612/` (README, not deleted).
2. **Posterior-predictive + sanity (commit `431e361`)** — `julia/posterior_predictive.jl`
   forward-runs all 10k draws 1900-2018. Posterior is Dangendorf-conditioned → bands are raw
   percentiles, **no importance weighting**. Outputs `outputs/postpred_*.csv`,
   `python/plot_postpred_components.py` → `outputs/postpred_components.png`.
   - **Sanity:** determinism PASS (bit-identical re-run); **glacier stabilization PASS across
     all 10k** (Mengel remnant S_eq(T*)<a; 0 commit-to-total-melt). The other 3 paired-pulse
     tests belong to the later SC-GHG pulse stage, not posterior-predictive.
   - **Component biases @2018 (median−obs cm):** AIS −0.04, GSIC +0.15, GIS −0.23, **TE +0.61**,
     total −0.41 (within Dangendorf). TE overshoot = freed `te_α` 0.164 (~3× old miscalibrated
     0.057) absorbed by persistent AR(1) (`rho_steric` 0.93). **Live calibration tension.**
3. **SSP-2100 projection ensemble (commits `90fb5d6`, `66e5bc4`, `96c7674`)** —
   `julia/project_ssps_2100_mengel.jl` projects the 10k posterior on `build_brick_mengel` +
   medoid fixed params + 18 free/draw, FaIR v1.4.5 per SSP, rel 1995-2014. **ONE calibration,
   UNWEIGHTED.** `python/plot_ssp_projections_mengel.py` → `outputs/ssp_projections_2100_mengel.png`
   (3-panel: dot-whisker vs **old BRICK + AR6**, trajectories+bands, 2100 component stack with
   in-block labels for SSP1-1.9/2-4.5/5-8.5, Mengel vs old BRICK).

## 2. Headline numbers — GMSL @2100 (cm, rel 1995-2014), 10k-draw posterior
| SSP | Mengel p50 [p05–p95] | old BRICK p50 | AR6 median |
|-----|----------------------|---------------|------------|
| SSP1-1.9 | 32.3 [30–35] | 35.8 | 38 |
| SSP1-2.6 | 35.8 [34–76] | 39.3 | 44 |
| SSP2-4.5 | 77.7 [41–108] | 70.7 | 56 |
| SSP4-6.0 | 89.3 [59–113] | 79.6 | — |
| SSP3-7.0 | 92.4 [71–114] | 83.3 | 68 |
| SSP5-8.5 | 116.5 [99–133] | 103.2 | 77 |

- **High-forcing runs HIGH vs AR6** via the per-draw **AIS-MICI threshold** (AIS median 43cm
  @SSP2-4.5; median draw crosses MICI ~2.7°C). `antarctic_temp_threshold` is free and
  **unconstrained by historical data** → the ensemble carries it; NOT a bug.
- **Glacier-swap headline:** Mengel GSIC@2100 ~6cm vs old single-reservoir ~11–16cm (old
  over-commits melt). Net: old BRICK higher at low forcing (glacier), Mengel higher at high
  forcing (AIS). LWS (~2.5cm) is the **uncalibrated MimiBRICK default** `landwater_storage`,
  identical old vs Mengel, climate-independent.

## 3. Two framing cautions for any writeup
1. **Parametric bands only.** The projection 5–95% bands carry PARAMETER uncertainty only —
   they EXCLUDE structural + AR(1) obs-noise, so they are much narrower than AR6's multi-method
   range (SSP1-1.9 is only ~4cm wide). Do NOT present them as AR6-comparable uncertainty.
2. **TE +0.6cm overshoot** is a live tension (freed te_α over-corrected, absorbed by high-ρ noise).

## 4. NEXT STEPS (prioritized)
1. **Post-2020 AIS extension (the open science question Marcus raised 2026-06-13).**
   NASA GRACE-FO shows Antarctic mass ~flat since ~2020 (NASA page reports a continuous
   ~135 Gt/yr 2002–2025 average and does NOT itself quantify a pause; the "pause" is the
   shape of the GRACE-FO time series). **Repo has NO post-2020 AIS product** — AIS target is
   Frederikse 2020 (ends 2018) + hardcoded IMBIE point term (ΔAIS 1992–2017, μ=0.72±0.156 cm).
   - **Data to acquire:** IMBIE / **Otosaka et al. 2023 (ESSD)** AIS mass balance through 2020,
     or a **GRACE-FO JPL mascon** Antarctic series through ~2024. Convert Gt→cm SLE (≈360 Gt/mm).
   - **Predicted outcome (FALSIFIABLE — run the sensitivity test, don't argue it):** a ~4-yr
     pause is a cumulative AIS deficit of only ~0.15–0.20 cm. Expect it to pull
     `ais_ocean_temperature₀`/`anto_α` DOWN modestly (lower central + low-forcing AIS) but to
     **NOT** resolve the high-forcing overshoot (that is MICI-threshold-driven, which 4 yr of
     historical data cannot constrain). Test: add a post-2020 AIS rate term to
     `calibrate_mcmc.jl`, re-fit, compare `ais_ocean_temperature₀` posterior + SSP projections.
   - **Caution (Marcus's call):** the 2021–23 flattening may be a TRANSIENT East-Antarctic
     precipitation/snowfall anomaly (recollection — needs a citation), not a dynamical slowdown.
     Weighting 4 yr of it heavily risks biasing projections low. Methodological choice — flag,
     don't silently resolve.
2. **Untracked-files cleanup.** Working tree has many untracked `outputs/` files: the 170MB×4
   archived 300k chains + new 500k chains (→ `.gitignore`), AND small INPUT CSVs the scripts
   depend on (`recalib_targets.csv`, `param_priors.csv`, `recalib_central_row.csv`,
   `calib_full_joint_params.csv`) + the FaIR SSP forcing CSVs (`data/observations/fair_mean_*_ssp*.csv`)
   that should be COMMITTED for reproducibility. Decide + do.
3. **Optional Torch longer MCMC** if a fully-converged `rho_ais` is wanted (`run_mcmc_torch.sbatch`);
   compute is small, not needed for the deliverable.
4. **Share branch with Tony Wong** — FaIR-vs-SNEASY + Mengel + freed AIS equilibrium T.

## 5. Non-obvious state / gotchas
- **Smoke vs full:** the first-50-rows smoke gave GIS@2100 ~4cm; full 10k GIS median ~7cm
  (≈AR6). ALWAYS full-run before reading component medians.
- **MAP vs posterior is apples-to-oranges:** `outputs/calib_full_joint_params.csv` has 29 free
  params (full-joint freed the 11 DAIS-shape params: antarctic_s0/gamma/mu/kappa/precip0/flow0/
  runoff_height0/c/bed_height0/slope/lambda); the MCMC/posterior FIXES those at the medoid
  (`recalib_central_row.csv`). A "MAP forward run" that only sets the 18 MCMC-free params + medoid
  for the rest will NOT reproduce the MAP fit (esp. AIS) — don't read that gap as a bug.
- **Posterior file:** `data/MimiBRICK/parameters_subsample_brick_mengel.csv` (10k × 28: 18 physical
  + 10 AR(1) noise), column order = `calibrate_mcmc.jl` `pn`. The 18-physical (comp,sym) mapping is
  hardcoded as `PHYS`/`PHYS_NAMES` in both `posterior_predictive.jl` and `project_ssps_2100_mengel.jl`.
- **Forcing override:** `set_forcing!(m,gmst,ohc)` sets `:model_global_surface_temperature` +
  `:thermal_expansion,:ocean_heat_interior`; the swapped Mengel glacier reads the shared
  temperature (wiring preserved by `replace!`). Build with `ssp="ssp245"` then override forcing
  per-SSP — scenario-agnostic after override.
- **Old superseded drivers kept:** `project_ssps_2100_ensemble.jl` (old posterior + stock BRICK)
  is the comparison source for "old BRICK" (v2.0.0 unweighted rows of
  `outputs/proj_ssps_ensemble_summary.csv`).

## 6. Key files (this session)
- `julia/posterior_predictive.jl`, `python/plot_postpred_components.py`
- `julia/project_ssps_2100_mengel.jl`, `python/plot_ssp_projections_mengel.py`
- Outputs: `outputs/postpred_{components_timeseries,coverage}.csv`,
  `outputs/postpred_components.png`, `outputs/proj_ssps_mengel_{summary,timeseries}.csv`,
  `outputs/ssp_projections_2100_mengel.png`, `outputs/mcmc/{postprocess.txt,adapted_cov.csv}`.
