# Quarantine 2026-10-08: Ladrillo v1.0 products, SUPERSEDED by v1.1

## 1. Why these files are here

They are **superseded, not bugged.** These are the v1.0 products: the projections of the GMD paper as submitted
(posterior L27). On 2026-10-08 Marcus ruled that the paper moves to Ladrillo v1.1. The posterior is the same, and two
projection-side fixes become the defaults (CHANGELOG 2026-10-08):

- **A. Paleo assignment.**
  - The Antarctic fast-dynamics pair (lambda, T_crit) is now assigned once over all 10,000 posterior draws.
  - v1.0 assigned it after selecting draws. The joint-climate arm did it chain by chain, so all four chains reused the
    same 500 paleo rows; the fixed-climate panel did it once over its own 2,000.
  - Fix A moves Ladrillo's Antarctica and total only. The moves look like resampling noise: across 30 Antarctic and
    30 total median cells, the signs are mixed, median |z| is 0.26–0.31 bootstrap standard errors, and none exceeds 2
    (`outputs/diag_v11_paleo_change_vs_noise.csv`).
- **B. Land-water frame step.**
  - The observed land-water series now starts at 0. v1.0 started it at its 1995–2005-frame value in 1900 (+1.565 cm),
    and DAIS's sea-level feedback saw that step.
  - Fix B moves Antarctica by about −1e-4 of itself (≤ 0.049 cm at 2300, SSP5-8.5) in both Ladrillo and BRICK 2.0.
    Glaciers, Greenland and thermal expansion are bit-identical.

## 2. What is here

These are the v1.0 bytes of every file the v1.1 rerun changed: 250 files in total, 233 in `outputs/` and 17 in
`figures/`.
- **Method:** snapshot-then-prune. Everything the run could touch was copied first, and copies whose canonical file
  came back byte-identical were deleted (343 of them).
- **Ladrillo arms:** `scope_slr_fairunc_{cells,draws,paths,gates}_*_L27*`.
  - SSPs and the 7 van Vuuren markers, on FaIR and MAGICC climate.
  - Spliced and raw, tapped and untapped, plus the constant-Greenland-shape arms.
- **BRICK 2.0 arms:** `*_oldbrick*`.
- **Fixed-climate panels:** `ssps_components_2300_*` for L27, L27 no-tap, L27 shape-const, L27aisamp1p196, L27r and
  L27b.
- **Posterior predictives:** `postpred_L27{,r,b}_components_timeseries.csv`.
  - L27 moved only in the 2026 95th percentiles, by ≤ 0.001 cm, through the 4 draws whose fast dynamics fires in
    2021–2026.
- **Diagnostics and tables:**
  - `diag_ais_amp_leverage*`, `diag_brick_philosophy_arms` (the 1.196 reversion), `diag_refit_precision_*`,
    `diag_imbie2026_vs_targets*`;
  - the comparison tables `vv_model_comparison_*`, `ladrillo_model_comparison_*`, `vv_climate_swap`,
    `vv_responsiveness`;
  - the benchmark `bench_ladrillo_L27.*` (one verdict changed: SSP1-2.6 2300 total spread WARN → PASS).
- **Provenance-only moves:** `diag_component_error_cancellation`, `diag_glacier_response_times` and the Table 4
  scorecard changed ONLY in their provenance text (date and commit). Their numbers are identical.
- **Figures:** the 17 regenerated figures, including the paper's Figs 2–4 and 6 (`figures/paper/`).
- **Note on the vv MAGICC-raw arms:** the 7 `*_vv*_raw_magiccclim_*` files carried FIXED-arm rows still on the
  Smith-basis FaIR mean, because the 10-07 CMIP7 rerun skipped them. Their joint rows were on MAGICC's own climate.
  The v1.1 rerun fixes both.
- **Not snapshotted:** 7 files, all new (the run's logs and `v11_paper_number_diff_20261008.csv`).
  `.touched_not_snapshotted` lists them.

## 3. Canonical replacements

The same file names at `outputs/` and `figures/`, produced by `run_ladrillo_v11_rerun_20261008.sh` (phases regress,
arms, downstream; SLR-RFF-BRICK commits 39926cc and bcebbac).
- `outputs/log_ladrillo_v11_rerun_20261008.txt`: 0 failed steps.
- Gates passed:
  - **[V1-REGRESSION]:** the edited code under the v1.0 settings reproduced 16 shipped files exactly, before anything
    was overwritten. The evidence is in `outputs/v11_regression_20261008/`.
  - **[CONTROL-EXACT]:** 15 SSP arms equal their panels exactly.
  - **[TABLE5-INPUT]:** the IC residuals are byte-identical, so Table 5 is unchanged.
  - The Ladrillo.jl package was re-certified bit-identical, at commit 78b03c6.

To regenerate any file here (v1.0), run the same driver with `LADRILLO_LWS_OBS_ANCHOR=v1_step
LADRILLO_PALEO_ASSIGNMENT=v1`. Its outputs then carry `_paleov1_lwsv1_step`. Alternatively, use the Ladrillo package
at tag `v1.0.0`, or its `--v1.0` option.

The paper-number consequences are in `notes/ladrillo_v11_paper_number_diff_2026-10-08.md`.
