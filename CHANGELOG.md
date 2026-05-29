# Changelog

All notable changes to this project. Older history reconstructed from the
commit log; recent entries are explicit.

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
