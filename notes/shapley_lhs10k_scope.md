# LHS-10k Shapley variance decomposition — scope

**Created:** 2026-05-26
**Owner:** Marcus
**Target deliverable:** v2 substack figure replacing the Hawkins-Sutton ANOVA
panels (Panels C/D of the AGU Chapman poster) with a Shapley-based
attribution at the physical-parameter level. No compute beyond local
machine + already-pulled CSVs.

## Why

Two limitations of the current ANOVA-18k nested decomposition surface in
the v1.4.5 results:

1. **Resolution limit.** With 15 cfgs × 3 seeds × 3 posts the bias-correction
   subtraction `V_emi_corrected = max(0, V_rff_obs − V_clim/15 −
   V_int/45)` clips V_emissions to zero for pulse-marginal GMST, even
   though the carbon-cycle (airborne fraction) and log-CO₂ forcing
   nonlinearities should generate a 5–15 % V_emi signal.

2. **Attribution opacity.** Nested ANOVA bundles the cfg-×-BRICK
   interaction (cfg-driven baseline temperature → baseline AIS state →
   BRICK-tipping-threshold interaction) entirely into V_brick, since
   BRICK posterior is the innermost axis. Apparent f_brick = 81 % at
   2100 in Panel D overstates the "pure" BRICK contribution; some of it
   is climate-cfg expressed through the tipping channel.

Shapley decomposition fixes both:

- It doesn't need a balanced factorial — works fine on the LHS-10k
  unstructured sample. The estimator uses a surrogate-model `Y ≈
  f(X₁,...,X_d)` to compute the conditional expectations
  `Var(E[Y|X_S])` for all 2^d subsets.
- Aggregates per-input contributions across all orderings of inclusion,
  so confounded effects are split fairly between inputs instead of
  pooled into the innermost axis.
- Naturally attributes to continuous physical drivers (ECS, te_α, ais_κ,
  ais_temperature_threshold, cumulative emissions, …) instead of to
  categorical axis indices (cfg_idx, post_idx, …). Much richer
  interpretation.

## Inputs (all local)

**Per-cell metadata to assemble (10,000 rows × ~50 continuous covariates):**

| Source axis | File | Per-axis covariates |
|---|---|---|
| `fair_cfg_idx` | `~/Documents/2026/CodeProjects/FaIRtoFrEDI/calibration_v145/calibrated_constrained_parameters_1.4.5.csv` (841 rows) | ECS, TCR, F2x (`forcing_4co2`), iirf_0[CO2], iirf_uptake[CO2], iirf_airborne[CO2], iirf_temperature[CO2], erfari_radiative_efficiency[*] (BC/OC/Sulfur/NOx/VOC/NH3/Equivalent_effective_stratospheric_chlorine), ocean_heat_capacity[0..2], ocean_heat_transfer[0..2], deep_ocean_efficacy, sigma_eta, sigma_xi, aerosol_cloud_(beta_total) (the v1.4.5 aci formulation), seed (already used; can map to forcing volcanic/solar scaling factors). ~30 continuous parameters per cfg. |
| `post_idx` | `data/MimiBRICK/parameters_subsample_brick.csv` (10,000 rows) | thermal_alpha (te_α), thermal_s0, glaciers_beta0, glaciers_v0, glaciers_s0, glaciers_n, greenland_a, greenland_b, greenland_alpha, greenland_beta, greenland_v0, antarctic_alpha, antarctic_gamma, antarctic_mu, antarctic_nu, antarctic_kappa, antarctic_precip0, antarctic_flow0, antarctic_runoff_height0, antarctic_bed_height0, antarctic_s0, antarctic_slope, antarctic_c, antarctic_lambda, antarctic_temp_threshold, anto_alpha, anto_beta. 27 continuous BRICK parameters per post. |
| `rff_idx` | `data/RFF-SP-emissions/csv/emissions_<rff_idx>.csv` (10,000 CSVs) | Per-draw summary statistics computed from the CO₂ trajectory: `cumulative_emissions_2030`, `cumulative_emissions_2100`, `peak_co2_emissions`, `peak_year`, `slope_2050_2100`, `fraction_negative_post_2050`, `cumulative_ch4_emissions_2100`. ~8 continuous summary features per RFF. |
| `seed_idx` | (no continuous covariate) | Leave as categorical / residual. |

Storage: assemble into a single `outputs/substack/lhs10k_per_cell_covariates.csv`
(10,000 × ~65 columns), keyed by `(rff_idx, fair_cfg_idx, seed_idx, post_idx)`.

**Per-cell target variable:**

`ΔSLR_pulse(2100)` = `slr_pulse_co2_pos_001gt(2100)` − `slr_baseline(2100)`,
read from `outputs/brick_v145/brick_lhs10k_{baseline,pulse_co2_pos_001gt}.csv`
(already local; 485 MB each, full per-component schema). Divide by 0.01
to get per-GtCO₂ marginal. Could also run on 2050 and 2150 for landmark
comparison — small extra cost since the surrogate refits per year.

## Model choice

`sklearn.ensemble.HistGradientBoostingRegressor` (fast, robust on
heterogeneous covariates, handles categorical features via `categorical_features`
argument). Default hyperparameters (max_iter=100, max_leaf_nodes=31)
typically work well on this scale.

Validation: 5-fold cross-validation, target R² > 0.85. Lower R² means
the surrogate isn't capturing the physics and Shapley values are
unreliable — would prompt a richer model (gradient boosting with
deeper trees, or LightGBM).

Alternative if HGB underfits: stacked surrogate (gradient boosting +
Gaussian process residual model), or move to LightGBM with
hyperparameter tuning. Not expected to be needed.

## Shapley computation

`shap.TreeExplainer` against the fitted HGB model, applied to the 10,000
LHS rows. Returns per-cell × per-feature SHAP values of shape
(10000, n_features).

**Global Shapley effects:**
- `shapley[i] = mean over cells of |SHAP[cell, i]|` — global magnitude
  attribution, sums approximately to the total prediction variance
  (formally Lundberg-Lee identity).
- Alternative formulation (Owen 2014 / Song et al. 2016): variance-based
  Shapley effects `Sh_i = E_{cell}[ E[(SHAP[i] − mean_SHAP[i])²] ]` —
  these sum exactly to V_total.

**Aggregation:**
- Per-physical-parameter: top-N table sorted by Shapley effect
- Per-source axis (for ANOVA comparison): sum SHAP magnitudes across
  features that belong to the same axis grouping. Mappings:
    - `V_emissions` ≈ sum of SHAP|_{rff-summary features}
    - `V_climate`   ≈ sum of SHAP|_{cfg parameters: ECS, TCR, F2x, ari, aci, ...}
    - `V_internal`  ≈ remaining unexplained variance + seed effect
    - `V_brick`     ≈ sum of SHAP|_{BRICK posterior parameters}

The seed axis has no continuous covariate; the residual variance after
the surrogate fit is the natural V_internal estimate (similar in
spirit to Hawkins-Sutton's polynomial-smoothing approach).

## Outputs

```
outputs/substack/lhs10k_per_cell_covariates.csv      (metadata)
outputs/substack/shapley_lhs10k_pulse_slr_2100.csv   (per-feature Shapley)
outputs/substack/shapley_lhs10k_pulse_slr_2100.png   (bar chart, top 20)
outputs/substack/shapley_lhs10k_pulse_slr_2100.pdf
outputs/substack/shapley_lhs10k_axis_aggregated.csv  (4-axis sums for ANOVA comparison)
```

For the v2 substack figure, the headline visualization is the top-N
bar chart at year 2100. A multi-year version (2050, 2100, 2150 stacked
bars) reads naturally if compute is cheap (it is).

## Implementation steps

1. **Build per-RFF summary** (2-3 hr): script that iterates over the
   10,000 RFF-SP per-draw CSVs and computes the 8 summary statistics.
   One-time cost; cache to `outputs/rff_summary_features.csv`.
2. **Assemble metadata table** (1 hr): join per-cfg parameters,
   per-post parameters, and per-rff summaries onto the LHS-10k slim
   CSV's keys. Output `lhs10k_per_cell_covariates.csv`.
3. **Compute per-cell target** (30 min): read the two full per-component
   CSVs, subtract paired (pulse − baseline) at year 2100, divide by
   0.01 GtCO₂. Result: per-cell ΔSLR in cm/GtCO₂. Optionally same
   for 2050 and 2150.
4. **Fit surrogate + validate** (1 hr): HGB fit, 5-fold CV, report
   train/test R². Inspect a residual scatter plot.
5. **Compute SHAP** (30 min): TreeExplainer, persist per-cell SHAP.
6. **Aggregate + visualize** (1-2 hr): bar chart, per-axis table, save
   outputs.
7. **Sanity vs ANOVA** (30 min): check that the per-axis aggregated
   Shapley values are within a factor of 2 of the ANOVA-18k fractions
   for V_brick and V_climate. Material disagreement would be a flag
   to investigate (not necessarily a bug — Shapley redistributes
   confounded interactions differently).

Total: ~1 day of focused work. No new compute on Torch.

## Decisions for Marcus (before implementation)

1. **Years**: 2100 only, or 2050 + 2100 + 2150 in a multi-panel?
2. **Pulse arm**: 0.01-GtCO₂ small-pulse (cleanest linear-regime; same
   arm we standardized empirical p5/p50/p95 on) or 1-GtCO₂ large-pulse
   (more signal but AIS-tipping-state-dependence on top)? Recommend
   small-pulse for consistency.
3. **Seed handling**: aggregate to (rff, cfg, post) by averaging over
   seed (loses no information for the linear-regime small-pulse) or
   keep all 4 axes? Recommend aggregate-over-seed since seed has no
   physical covariate and contributes residual variance only.
4. **Aggregation tier in the figure**: per-physical-parameter (rich,
   ~50 bars) or per-source-axis (4 bars, comparable to ANOVA)?
   Recommend both — the rich version is the headline; the aggregated
   version is the methods-comparison.
5. **CH₄ pulse Shapley too**? The same machinery extends trivially to
   the LHS-10k 0.01-Tg CH₄ small-pulse arm; gives a per-parameter
   attribution of SC-CH₄-SLR uncertainty. Would add ~3 hr of work.

## Risks

- **R² too low**: if the HGB surrogate can't explain > 70% of the
  variance, the SHAP attributions are unreliable. Mitigation: try
  LightGBM / XGBoost with tuned hyperparameters; or add interaction
  features manually (cfg_ECS × rff_cumulative_emissions; etc.).
  Empirically, gradient-boosting on this kind of mechanistic-model
  output achieves R² > 0.9 routinely.
- **SHAP magnitude vs Shapley effects**: the two definitions sum to
  different totals (E[|SHAP|] is a magnitude attribution; Shapley
  effects are a variance attribution). For methods rigor we should
  report both and verify they tell the same qualitative story.
- **High-dimensional inputs (~65 features)**: SHAP TreeExplainer scales
  O(n × n_features × n_trees), well within budget at 10k × 65 × 100.

## Reference

- Owen, A. B. (2014). Sobol' indices and Shapley value. *SIAM/ASA Journal on Uncertainty Quantification*, 2(1), 245-251.
- Song, E., Nelson, B. L., & Staum, J. (2016). Shapley effects for global sensitivity analysis: Theory and computation. *SIAM/ASA Journal on Uncertainty Quantification*, 4(1), 1060-1083.
- Lundberg, S. M., & Lee, S. I. (2017). A unified approach to interpreting model predictions. *NeurIPS*.
- Iooss, B., & Prieur, C. (2019). Shapley effects for sensitivity analysis with correlated inputs. *International Journal for Uncertainty Quantification*, 9(5).
- Darnell et al. (2025) used a related framework (variance decomposition with confounded inputs handled via Shapley-equivalent attribution) — see their Methods §2.3.

## Status

Scoped 2026-05-26. Not implemented. Targeted for v2 of the
substack post / followup paper, after the AGU Chapman poster
delivers (~2026-06-01). For the poster itself, the ANOVA-18k decomp
+ a methodological footnote about the cfg-×-BRICK interaction is the
safe path.
