# Changelog

All notable changes to this project. Older history reconstructed from the
commit log; recent entries are explicit.

## [Unreleased] — v145 end-to-end pipeline

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
