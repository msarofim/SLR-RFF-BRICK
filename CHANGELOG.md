# Changelog

All notable changes to this project. Older history reconstructed from the
commit log; recent entries are explicit.

## [unreleased] — 2026-06-14 — CO2/CH4 pulse→SLR: prerequisites P1+P2 executed

Executing the two Step-4 blockers from the pre-launch review (Marcus: go ahead with P1+P2).
- **P2 DONE** — `julia_v2` (v2.0.0) + `julia_v121` (v1.2.1) instantiated + precompiled on
  Torch via `slurm/precompile_julia_envs.sbatch` (compute node; login-node instantiate was
  stalling/precompiling — SIGKILL risk). Both verified: `get_model`+`run` OK (v2 SLR2100=102.1,
  v121 99.0 cm). Plots/GR/Qt precompile-fails are benign (headless, unused by the BRICK driver).
- **P1 IN PROGRESS** — paired r2 triplet (baseline + co2-0.01Gt + ch4-**1Tg**) built on Torch
  via `slurm/submit_triplet_r2.sh` (array job, one arm each). Moved to Torch after the local
  background build died untraced; Torch calibration sha256 matches local
  (`03b0368…`) so the realization equals the locally-validated smoke. Cubes land on `/scratch`
  with embedded seed provenance (`cell_seeds` etc.). Tag `_flat2015_r2`.
- The 0.01 Tg CH4 cube is float32-corrupted (see prior entry); CO2 stays 0.01 Gt.

## [unreleased] — 2026-06-14 — CO2/CH4 pulse→SLR, 3 BRICK versions: foundations (runbook Steps 0–3)

Built the prerequisites for the CO2 & CH4 pulse→SLR marginal study across three
BRICK calibration versions (pre-#93 v1.2.1 / BRICK 2.0 / BRICK-Mengel), on the
FaIR-v1.4.5 × RFF-SP LHS-10k ensemble. Stopped before the 90k-run Torch launch
(Marcus: foundations-only this pass). Runbook:
`notes/handoff_2026-06-14_co2ch4_pulse_3brick_NEXT-SESSION.md`.

### Added
- **`julia_v121/` — a real MimiBRICK v1.2.1 env** for the pre-#93 arm (the
  `brick-v1.2-vehicle` Manifest pins 1.0.1, so this is a build, not a checkout).
  Pins MimiBRICK git `repo-rev v1.2.1` (sha `94ceca2`) under Julia 1.12; smoke
  passes (build→run 1850–2300, closure 4.4e-16 m). `julia_v121/build_v121_env.jl`.
- **`julia/run_mimibrick_pulse_versioned.jl` — ONE version-aware flat-cube driver
  for all THREE versions** (`--brick-version pre93|brick2|mengel`), one output
  schema (per-component + total SLR at 2100/2150/2300, optional GMSL history for
  Wong). Supersedes the schema-limited `run_mimibrick_flatcube_v121.jl` (components
  at 2100 only) — unified to remove the cross-arm schema-drift risk. pre93 runs in
  `julia_v121` (precip_log=false); brick2/mengel in `julia_v2` (precip_log=true);
  mengel applies the 28-col posterior as 18 free params over the medoid central row
  (mirrors `project_ssps_2100_mengel.jl`). Added NPZ to `julia_v2`.
- **`python/scripts/sanity_battery_pulse3brick.py`** + smoke metadata
  `outputs/smoke25_lhs10k_metadata.csv`. 5-test gate (zero-pulse/cross-process
  determinism, sign-flip, ×magnitude, first-principles, closure) on a 25-cell
  lhs10k-proxy smoke per version → **ALL PASS, gate OPEN**
  (`outputs/sanity_battery_pulse3brick_smoke.txt`). Smoke reproduces the pre-#93
  GIS pathology (dGIS@2100 ≈ 8.1e-3 cm/GtCO2 vs ~4–5e-4 for brick2/mengel; pre93
  total ~3× larger @2300), ×magnitude linear to ~1% (no AIS tipping at 0.01 Gt),
  CH4:CO2 per-unit ratio ~0.055–0.063.

### Corrected (vs the runbook's assumptions)
- **MimiBRICK v1.2.1 already uses `get_model(ssprcp_scenario=…)`**, NOT
  `rcp_scenario=` as the runbook claimed; it ships both RCP- and ssp-named SNEASY
  forcing files (no date suffix) and uses LINEAR precip0 (`precip_log=false`). The
  real v1.2.1→v2.0.0 differences are the date-suffixed forcing files + the
  precip_log reparam. (Forcing is overridden by the cube's GMST/OHC anyway.)
- **The Mengel 28-col posterior cannot be applied via `update_brick_params!`** (it
  lacks the full AIS/glacier/thermal_s0 columns). Canonical path = medoid central
  row for fixed params, then the 18 free params per draw, per `project_ssps_2100_mengel.jl`.
- **`brick_mengel.jl` must be include()d at module scope**, not lazily in a
  function — Mimi's `run(m)` otherwise hits a world-age MethodError on
  `run_timestep_glaciers_mengel`. Loading it is harmless for pre93/brick2 (the
  Mengel component is defined but only instantiated for `--brick-version mengel`).

### Pre-launch review (2026-06-14) — 3 prerequisites before Step 4
Verified sound: lhs10ks cell layout == metadata (incl. seeds); pairing (pre-2030
dGMST=0, @2000=0 → rebaseline cancels); cross-process paired determinism exact;
CO2 0.01 Gt well-resolved (15–30× float32 ULP, ×magnitude ~1%); posteriors all
10000 rows (no off-by-one); closure ~1e-11.
- **P1 — CH4 0.01 Tg cube is float32-corrupted → regenerate at 1 Tg** (Marcus
  2026-06-14). CH4 dGMST decays below the float32 ULP (~2.4e-7 °C) after ~2060
  (nonzero cells: 72%@2075, 34%@2100, 8%@2300); CH4 SLR marginal ratio
  (0.01-cube/1-cube) = 0.97@2100, 1.20@2150, 0.51@2300, **TE@2300 → 0**. 1 Tg CH4
  is ~10× smaller dGMST than CO2-1Gt → well below AIS tipping. Build
  `cube_v145_lhs10ks_pulse_ch4_pos_1tg_flat2015.npz` (FaIR driver, paired seeds),
  marginal ÷1.0; CO2 stays 0.01 Gt ÷0.01.
- **P2 — Torch envs missing.** Only the v1.0.1 `julia` env is on Torch; build
  `julia_v2` (brick2/mengel) + `julia_v121` (pre93) there (instantiate + precompile).
- **P3 — Mengel Wong-`l_B` path missing** for Step 5 (`compute_lB_per_post*` assume
  the 35-col posterior; mengel 28-col needs medoid + 18-free).

### Pending (next session — Step 4 after P1/P2)
- Torch: 3 versions × 3 arms {baseline, co2_pos_001gt ÷0.01, ch4_pos_**1tg** ÷1.0}
  × 10k = 90k runs, partition `cs`. Then per-version Wong weights (own `l_B`) +
  paired marginals + headline figure.

## [unreleased] — 2026-06-13 — BRICK-Mengel post-2018 multi-component extension

### Added
- **Extended ALL calibration targets past Frederikse 2020's 2018 end** with
  reconciled modern products and re-fit, to test the post-2020 Antarctic pause +
  (Marcus's expansion) Greenland / thermal-expansion / glaciers.
  - Data: GRACE-FO JPL mascon AIS+GIS (→2026), GlaMBIE 2025 glaciers (→2023),
    NOAA NCEI thermosteric (→2025), NOAA STAR total (→2024); IMBIE 2023 AIS+GIS
    cross-check (agrees with GRACE splices <0.07cm). `raw/README_modern_extensions.md`.
  - `python/prep_recalib_targets_ext.py` → `outputs/recalib_targets_ext.csv`
    (offset-match splice onto Frederikse over GRACE/obs overlap; per-component end yrs).
  - `julia/calibrate_mcmc_ext.jl` + `run_mcmc_ext_local.sh` + `postprocess_mcmc_ext.jl`:
    per-series AR(1) windows; **dropped IMBIE+Dyurgerov point terms**; total extended
    w/ NOAA STAR (Marcus decisions). 4×500k → 27/28 R̂<1.05.
  - Obs check `julia/posterior_predictive_ext.jl` + `python/plot_postpred_components_ext.py`.
  - High-T glacier melt verification `python/verify_mengel_hightemp_melt.py` (Marcus:
    confirm Mengel melts MOST glaciers at high T) — PASS (99% committed @4°C).
  - Projection A/B `python/plot_ssp_projections_ext_compare.py`; `project_ssps_2100_mengel.jl`
    gained an optional TAG arg (baseline default byte-identical).

### Result
- Extending barely moves the physics (ais_ocean_temperature₀ +0.013); GMSL@2100
  LOWER by 0.8–3.2cm, ~entirely via AIS; high-forcing overshoot vs AR6 persists
  (MICI-threshold-driven, unconstrainable by ~7yr). TE overshoot NOT resolved by
  NOAA steric (+0.51cm@2025). AIS pause not reproduced (warming-driven model).

### Tried / noted
- 4×**100k** with the baseline proposal covariance did NOT converge (25/26 R̂>1.05;
  per-chain logpost spread 6–138 = slow burn-in from a mismatched proposal, NOT a
  bug). Fixed by seeding the 500k from the ext-tuned `adapted_cov_ext.csv`.
- `.gitignore`: exclude the 276MB×4 MCMC chain files (regenerable).

## [unreleased] — 2026-05-30 — Rennels 7-panel SSP2-4.5 SLR + pulse figure

### Added
- **7-panel SLR figure for Lisa Rennels** confirming emission-pulse + BRICK
  results under SSP2-4.5. Left: total GMSLR rel 2005 (median + 75%/90% bands,
  unweighted spread over 841 v1.4.5 configs × 8 BRICK post-PR#93 posteriors).
  Right 2×3: SLR impulse response to a 2020 CO₂ pulse, decomposed into
  TE/GSIC/GIS/AIS/LWS/Total, with BOTH a +0.01 GtC and a +1e-4 GtC arm overlaid.
  - Driver: `python/scripts/rennels/rennels_build_ssp245_cubes.py` — FaIR v2.2.4
    (v1.4.5 cal) SSP2-4.5 baseline + 4 pulse arms (±0.01, +0.02, +1e-4 GtC at
    2020.5, CO₂ FFI), emits **GMST + OHC flat-cubes** (float64 — float32 destroys
    the 1e-4 GtC signal, ~1e-7 °C on ~2.5 °C). Pulse in GtC→GtCO₂ ×44/12.
  - Figure: `python/scripts/rennels/rennels_7panel_figure.py`.
  - Outputs: `outputs/rennels/slr_7panel_ssp245.{png,pdf}`,
    `rennels_pulse_response_summary.csv`, 5 cubes + metadata, BRICK CSVs.
- **Result:** 1e-4 GtC pulse IS resolvable through BRICK in float64; the two arms
  agree to <0.2% at 2150 (linear). Per-GtCO₂ total marginal @2150 = 0.0073
  cm/GtCO₂ (matches memory ~0.0074). TE dominates; LWS ≈ 0 (pre-2019 calib).
- **Sanity:** all 5 paired-pulse tests pass at FaIR level (zero/sign-flip 0.02% /
  doubling 2.0002 / linearity 0.02% / first-principles 0.415 m°C/GtCO₂) AND BRICK
  level (repro bit-identical / sign-flip anti-sym / doubling 2.0000 / linearity
  0.29% / closure Σcomp=total to 1.4e-13 m).
- **Caveat flagged on-figure:** unweighted SSP2-4.5 median runs above AR6
  (69 vs ~50 cm @2100; 132 vs ~68 cm @2150) — consistent with this project's
  hot BRICK posterior (RFF-SP gives ~93 cm @2100), not a bug; per user's
  explicit "unweighted climate+BRICK spread" choice (no Wong importance weights).
- **Absolute-units variant** `slr_7panel_ssp245_abs1em4.{png,pdf}`: right panels
  in metres of SLR per literal +1e-4 GtC pulse (TE ~2e-8 m @2300; direct-1e-4 vs
  0.01÷100 agree <0.2%). For comparison with Rennels' own per-1e-4-GtC numbers.

### Fixed / corrected
- **AIS get_model seed-bug note in CLAUDE.md was overstated** ("uniformly
  non-negative once seeded"). Measured: matched-seed AIS median is slightly
  NEGATIVE at 2050 and 34–56% of draws are negative at all horizons — the true
  small-pulse AIS signal straddles zero. A negative *median* alone is not proof
  of the bug. Demonstrated the actual bug signature: seed-mismatch zero-pert
  (2026 vs 1234) injects a systematic AIS offset (median −5e-4 cm, 100% negative)
  ~100× the true ~5e-6 cm signal. Diagnostic tests added to the note.

## [v2.1] — 2026-05-29 — finalized substack + poster (Group-Sobol H-S)

### Changed
- **Group-Sobol is now the canonical SLR Hawkins-Sutton method** (replaces the
  earlier TreeSHAP/Shapley attribution, which under-counted the emissions axis
  ~3× — 8.6% vs ~27-29% at 2150 — because collinear cumulative-emissions
  features dilute per-feature Shapley credit). Sobol decomposes *grouped* variance
  directly, immune to within-group collinearity, and is importance-weighted.
  Module: `python/scripts/substack/group_sobol_hs.py`; renderers
  `render_hybrid_tipping_split.py`, `paired_figures_hs.py`,
  `poster/hawkins_sutton_panels.py`.
- **Independent model-free cross-check:** a 324,000-run balanced-factorial ANOVA
  (`anova_hs_decomp.py`) reproduces the Sobol emissions/climate/internal shares
  to within ~2 pp at 2150 (emissions 27.0% ANOVA vs 28.9% Sobol), confirming the
  attribution is not a surrogate artifact. Overlay figure `anova_vs_sobol_overlay.py`
  → `outputs/substack/anova_vs_sobol_total_slr.{png,pdf}`.
- **Terminology:** reader-facing figures/captions now say "importance weighted"
  rather than "Wong-weighted" (provenance comments keep "Wong").
- **Pulse SLR figure:** removed the ensemble-mean line from the pulse-SLR panel
  (tipping-corrupted, not pulse-size-invariant); median + 5-95% band retained.
  Pulse GMST keeps its mean (no tipping pathology).
- **Exceedance table caption** corrected to "FaIR v2.2.4 (v1.4.5 calibration)"
  — distinguishes the model version from the calibration posterior.

### Notes
- Superseded TreeSHAP-era H-S outputs quarantined under
  `outputs/quarantine/20260528_treeshap_slr_underattribution/`.
- Decided to keep Sobol canonical and ANOVA as validator; no pulse ANOVA (the
  cross-check's motivation was the emissions axis, which is ~1% / uncontroversial
  for the pulse). See `notes/handoff_2026-05-28b_group_sobol_hs.md`.

## [Unreleased] — v145 end-to-end pipeline

### Added
- **Hybrid total_slr H-S decomposition with augmentation-based V_BRICK + V_seed** (2026-05-27).
  Pure-Shapley failed for SLR: even high-capacity surrogate + p99 outlier clip left
  OOF V_residual at 25-32%, factor 6-47× the pure-seed gold standard. Diagnosed as
  cfg×post interactions + AIS tipping nonlinearity that HistGradientBoosting can't
  capture. Replaced V_BRICK and V_seed in the SLR figure with model-free estimates:
  - V_BRICK: within-cell variance across 10 BRICK posts per cell (90,000 augmentation
    runs: 10,000 v5 cells × 9 extra post_idx via LHS-stratified sampling).
  - V_seed: within-cell variance across 10 seeds per (rff, cfg, post) group (200
    parent cells × 9 extra seeds = 1800 new FaIR runs + paired BRICK).
  Result: V_internal_SLR now declines from 4.6% (2025) to 0.5% (2150), matching
  physical expectation. BRICK is the dominant axis (~42-59%) across all years. A
  residual wedge (20-37%) is labeled as "cfg×post interactions + tipping" since
  those interactions can't be uniquely attributed.
  Files: `python/scripts/substack/hybrid_hs_total_slr.py`,
  `outputs/substack/shapley_hs_total_slr_hybrid.{png,pdf}`,
  `outputs/substack/v5_hybrid_decomp_diagnostic.csv`.

- **v5 noise-isolated H-S figures landed** (2026-05-27).
  Re-ran `shapley_hawkins_sutton.py` against the new LHS-10k_s cubes
  (`cube_v145_lhs10ks_{baseline,pulse_co2_pos_001gt}_flat2015.npz`) and
  the post-PR#93 BRICK posterior. Headline:
  - total_gmst V_internal at 2021 = **97.5%** (canonical H-S near-term
    recovered; v4 had ~0% because LHS-10k was single-seeded).
  - total_slr at 2050: emi 2% / climate 38% / brick 40% / internal 20%
    (first time all 4 axes nonzero — v4 internal was misallocated to
    surrogate fit gap).
  - pulse_gmst: ~100% climate response (matched-seed cancels internal).
  - pulse_slr: BRICK 35-50% of variance across 2050-2150.
  Companion BRICK metadata `outputs/lhs10ks_brick_metadata.csv` LHS-samples
  `post_idx ∈ {0..9999}` (one unique BRICK posterior member per cell);
  the previous `lhs10k_metadata_v145.csv` only used 3 unique post_idx
  across all 10,000 cells, which had been silently under-sampling BRICK
  uncertainty across the entire v4 family of plots.
  Caveat carried forward: TreeSHAP under-attributes BRICK; Owen-Shapley
  re-render (~40 hr Torch) still pending.

### Fixed
- **Hawkins-Sutton nested-ANOVA finite-replication bias** (2026-05-26).
  The variance-decomposition functions in `python/hawkins_sutton.py`
  (`decompose_slr_4way`, `decompose_gmst`) and the substack-side
  reimplementation in `updated_hawkins_sutton.py` were using `ddof=0`
  population variance at every level and were not subtracting the
  propagated within-cell sampling-noise term from each outer-level
  variance. With only 3 seeds × 3 posts per (rff, cfg) cell, the
  ddof=0 estimator was biased down by (n−1)/n = 2/3 at the inner
  level, and the cfg-means carried σ²_seed/n_seed sampling noise that
  was being absorbed into V_climate. Result: total-GMST early-year
  f_internal showed as 65% (canonical Hawkins-Sutton expectation:
  ~100%) and the substack/poster Panel C / D fractions were
  systematically tilted away from V_internal and toward V_climate.
  Fix: unbiased ddof=1 variances at every level via the
  `n_eff/(n_eff − 1)` Bessel correction (handles weighted variance via
  the effective sample size), plus subtract the propagated noise from
  each outer level (V_internal/n_seed off V_climate; V_climate/n_cfg
  plus V_internal/(n_cfg × n_seed) off V_emissions; analogous 4-way
  formulae with V_brick at the bottom). Clipped to ≥0 since
  finite-sample bias-corrected estimates can go slightly negative when
  the true variance is below the noise floor. Affected outputs: every
  Hawkins-Sutton figure in the substack and poster. Substantive
  changes: total-GMST f_internal at 2030 went 62% → 80%; Panel C
  fractions at 2100 went f_clim/f_emi/f_brick/f_int = 80/3/13/3% →
  54/23/23/0%; Panel D at 2100 went 17/3/45/35% → 1/1/81/16%. The
  Panel C/D PDFs in the IEc handoff are regenerated, and the
  discussion paragraph in poster_text.txt has been updated to reflect
  the new fractions.

### Tried and abandoned
- **Lemoine-Traeger tipping-decomposition framing for pulse-marginal SLR
  figures** (2026-05-26). Three active sites used L-T classifiers with
  inconsistent methodology: `gaussian_vs_empirical_slr.py` used a
  pulse-outcome classifier (per-year marginal > 0.3 cm; pulse-size
  sensitive); `extract_lhs10k_smallpulse_summary.py` used a baseline-state
  classifier (`ais_2100_cm > 20 cm`) but it was silently dead because the
  slim CSV didn't carry `ais_2100_cm`; `lemoine_traeger_decomposition.py`
  used baseline-state but had no callers. We initially standardized on
  baseline-state at 20 cm; that revealed that v1.4.5 + post-PR#93 BRICK +
  Wong weighting leaves 88% of cells classified as tipping-prone, so the
  "L-T linear baseline" was a 12%-subset mean (small slice; the L-T
  premium framing was more informative under v1.4.1 where tipping was the
  minority state). Decision: empirical importance-weighted p5/p50/p95
  quantiles satisfy "accurately reflect likely impact + uncertainty"
  while being both threshold-invariant AND pulse-size-invariant.
  `gaussian_vs_empirical_slr.py` + outputs retired to
  `outputs/quarantine/20260526_lt_to_empirical/`. Tipping-conditional
  columns dropped from `extract_lhs10k_smallpulse_summary.py` output.
  `lemoine_traeger_decomposition.py` library kept as a diagnostic
  utility (marked as such in its docstring) for any future revisit of
  the decomposition framework.

### Added
- **v1.4.5 FaIR pipeline end-to-end**: 18 v1.4.5 cubes (9 LHS-10k + 9 ANOVA-18k;
  baseline + 8 pulse arms each) on Torch; new BRICK driver
  `julia/run_mimibrick_flatcube.jl` adapted to the flat
  `(n_cells, n_year)` cube schema. 270× compute reduction vs. the rectangular
  layout that was used in the v1.4.1 era.
- **`run_mimibrick_flatcube.jl`** flat-cube driver with paired closure check
  (Σ components ≡ total SLR to 1e-10 m on the first row).
- **`python/scripts/run_wong_pipeline_v145.py`** end-to-end Wong-weighting
  pipeline matched to the new schema: l_FB from per-arm BRICK CSVs,
  l_B from post-PR#93 posterior, per-arm baseline-weighted CSVs + envelope
  summaries + paired marginal envelopes.
- **`python/scripts/emit_slim_legacy_csvs_v145.py`** writes slim,
  legacy-schema CSVs (bare-year SLR columns + keys + w_norm) so downstream
  plot scripts (`gaussian_vs_empirical_slr`, `slr_band`, `run_4way_slr_decomp`,
  `run_pulse_4way_slr_decomp`) work unchanged on the v145 outputs.
- **Tony component overlay**: added an LWS panel (BRICK ≡ 0 by design
  through the hindcast — Wong et al. 2017 calibration target had LWS
  removed — plus Frederikse 2020 Terrestrial Water Storage overlay).
  Added Frederikse 2020 overlays to the AIS and GSIC panels so the
  20th-century component biases that cancel into matching GMSL are
  visible: BRICK AIS overshoots Frederikse by ~3.3 cm at 1900 (1900-2000
  rise of +3.95 cm vs Frederikse +0.6 cm), GSIC undershoots by ~4 cm at
  1900, GMSL net agreement is within ~0.2 cm — diagnosed bias cancellation.
- **`fair_vs_obs_gmst_ohc.py`** new substack diagnostic figure: v1.4.5
  ensemble-mean GMST vs IGCC 2024 (4-dataset mean), and FaIR v1.4.5
  ensemble-mean OHC vs spliced Zanna 2019 + IGCC 2024.

### Changed
- **BRICK posterior**: swapped pre-PR#93 (`b > v0` in 97.6% of draws) for
  post-PR#93 (`b > v0` in 0%). The new posterior matches Frederikse 2020
  GIS back to 1900. Old posterior moved to
  `data/MimiBRICK/quarantine/20260524_pre_pr93/` with a README.
- **CITATION / .zenodo.json**: updated calibration source from FaIR v1.4.1
  to v1.4.5 and BRICK posterior provenance from v1.0.1 to post-PR#93 joint.

### Quarantined (pre-fix outputs, kept for postmortem)
- `outputs/quarantine/20260524_pre_v145_e2e/` — v1.4.1-era weighted CSVs
  superseded by v1.4.5 outputs:
  - `brick_lhs10k_baseline_to2300_weighted.csv` (LHS-10k baseline, v1.4.1 era)
  - `brick_lhs10k_pulse0p01gtc_to2300_weighted.csv`
  - `brick_lhs10k_pulse_to2300_weighted.csv` (1-GtC pulse)
  - `brick_anova_long_2300_weighted.csv` (13,500-row ANOVA, v1.4.1 era)
  - `brick_anova_long_2300.csv`, `brick_anova_pulse_long_2300.csv`,
    `brick_anova_marginal_long_2300_weighted.csv`
- `data/MimiBRICK/quarantine/20260524_pre_pr93/parameters_subsample_brick.csv`
  — pre-PR#93 posterior (97.6% b > v0).

### Diagnosed but not fixed (deliberate documentation)
- BRICK 20th-century **AIS overshoots Frederikse 2020 by ~3.3 cm at 1900**;
  cancels against GSIC undershoot. PR#93 only added Frederikse GIS to
  calibration; TE / AIS / GSIC still calibrated to Wong et al. 2017 targets
  (pre-ARGO Gouretski 2007 OHC and a less complete antarctic obs basis).
  Fix would require a future PR adding Frederikse AIS/GSIC to the
  calibration target set. Documented in memory
  `project_brick_component_biases_vs_frederikse`.

## [v1.0-poster-agu-chapman] — 2026-05-06
- Initial v1.4.1-era pipeline + AGU Chapman SLR conference poster artifacts.
- LHS-10k conditional-BRICK ensemble (ESS = 7,037).
- Hawkins-Sutton 4-way decomposition of total SLR and pulse-marginal SLR.
- Zenodo DOI: 10.5281/zenodo.20312325.
