# Handoff 2026-11-11c: Table 4 and Table A1 in Ladrillo.jl, seeds recorded, calibration port scoped

Session `76ba2d5f` (launched from FaIRtoFrEDI, worked in Ladrillo and SLR-RFF-BRICK), 2026-11-11 14:15 onward.
Previous: `notes/handoff_2026-11-11b_gmd_decisions_ladrillo_v1.md` (still current for the draft pass; this note adds to it).

## 1. What we were working on

The open items of the 11-11b handoff while the GMD draft waits for Marcus's hand edits. At 14:50 the draft on disk was
still the 10:19 save, with Word's lock file from 14:00 (he has it open). **The draft pass has not been run.**

## 2. Decisions (Marcus, 11-11, AskUserQuestion)

| question | answer |
|---|---|
| Table 4's scorecard script in Ladrillo.jl? | **port it now** (done, §3) |
| Calibration drivers and target builders, which the Code availability sentence also claims | **port before release** (scoped, §4; not started) |
| Seed provenance in the figure-input files | **yes** (done in Ladrillo.jl, §3; research repo left, see §3) |

Memory: `gmd_1111_decisions` (updated).

## 3. Done (Ladrillo.jl `main`, pushed; tags still held)

- **184c95d, Table 4.** `python/tables/ladrillo_vs_brick20_scorecard.py` ports `python/scope_ladrillo_vs_brick20_scorecard.py`:
  250/250 numbers bit-identical to `outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv`. Added to
  `check_tables_identity.py`, the test references and `test/runtests.jl`.
- **Same commit, Table A1 caught up with b8d7fdf.** The package's Table A1 builder still printed the four log₁₀ rows;
  the research builder shows them in ln since 11-10 (Marcus "Option 1"). The gate against the research repo was failing
  on five md lines and nobody had run it. Ported, with [LN-DISPLAY]. `mutation_test_tables.py`: 7 new mutants, 14/14.
- **3c83772, seeds.** Audit: every projection, hindcast and BRICK 2.0 file in the package already recorded its seeds
  (paleo 20260920, pairing 2026, `Random.seed!(2026)` before get_model, NOISE_SEED 2026). Gaps filled:
  `vv_model_comparison.csv` (Figs. 2, 3, 6) now copies every seed clause of the 14 draws files and stops if one is
  missing or differs (mutation-tested); `Ladrillo.fair_seed_note()` puts the FaIR stochastic status in every driver's
  provenance (SSP + ssp245harm: calib 1.6.0 per-config seeds, 841 distinct; van Vuuren: deterministic). Two runs of each
  figure-input producer byte-identical (11 files). The local hindcast and van Vuuren products were regenerated (53
  files, 0 non-provenance cells differ) and swapped in; the SSP products were not (no figure reads them).
- Gates: figures PASS (every PNG byte-identical to `figures/paper/`), tables PASS (5 outputs), tests 97/97 exact.
- **Not done, deliberately:** the research repo's figure inputs (`vv_model_comparison_L27.csv`,
  `scope_slr_fairunc_{draws,paths}_*`) still have no provenance column. Fixing them means re-running the research
  projections and changing column sets the package gates read. Memory `gmd_seed_claim_unsupported_by_figure_inputs`.

### Files touched

Ladrillo.jl (`~/Documents/2026/CodeProjects/Ladrillo`, `main`):
- 184c95d: new `python/tables/ladrillo_vs_brick20_scorecard.py`; `python/tables/{check_tables_identity,ladrillo_prior_posterior_table,mutation_test_tables}.py`,
  `python/tables/mutation_result.txt`; `test/runtests.jl`; `tools/build_test_reference.py`; `test/reference/` (new
  `research_postpred_brick20_components_timeseries.csv`, `research_scope_ladrillo_vs_brick20_scorecard_L27.csv`;
  Table A1 references re-copied; `SOURCES.csv`); README (Tables 4 and 5 section, tables gate); CHANGELOG 2026-11-11c.
- 3c83772: `src/forcing.jl` (`fair_seed_note`); provenance lines in `scripts/{project_joint,brick20_joint,project_fixed,posterior_predictive,posterior_predictive_brick20,ic_hindcast_residuals}.jl`;
  `python/figures/vv_model_comparison.py`; CHANGELOG 2026-11-11d.
- Untracked, regenerated: `outputs/hindcast/*`, `outputs/projections/*vv*`, `outputs/tables/*`, `outputs/figures/*`.

SLR-RFF-BRICK: this note only (no code or output changed). Its CHANGELOG has no 11-11c entry; the Ladrillo.jl
CHANGELOG carries the record.

Memory: `gmd_1111_decisions` (the three answers), `gmd_seed_claim_unsupported_by_figure_inputs` (audit result),
new `calibrator_gate_reference_is_all_rejections` (pointer in `INDEX_diag_bound`).

## 4. For the draft pass (add to the 11-11b list)

- Code availability: with Table 4 ported, the archive now holds the scripts for Figs. 1–6 and Tables 4, 5, A1, A2. The
  calibration drivers and target builders are not in it yet (§5).
- Seed sentence (Sect. 3.2): Marcus's wording. Facts: in Ladrillo.jl every file a figure reads records the seeds behind
  it; the research files do not. The 11-11 guidance's replacement sentence remains true either way.
- Table A1: the package now prints the same ln rows and footnote ᶜ as the guidance's Appendix A item.

## 5. Calibration port: scope (subagent map 11-11, key claims re-checked)

Production (`run_mcmc_L27.sh`, commit 43d84aa, 2026-09-20 13:34, 4 chains in parallel, ~4 h wall, ~2 GB each):
```
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
julia --project=julia_v2 --threads=1 julia/calibrate_mcmc_ext.jl 2000000 $SEED \
  --tag=L27 --overdisperse --starts=outputs/mcmc/overdispersed_starts_L27.csv --adcov=adapted_cov_L26_named.csv \
  --gis-ordered --gis-basins2 --amp-mu=1.09 --amp-sigma=0.180 --paleo-priors --no-delta --no-d2-gsic \
  --obs-corr-len=100 --toff-lo=-4 --precip-reparam --cut-fastdyn --fix-gamma --no-ledger
```
seeds 2026–2029. Post-processing `run_l27_postprocess.sh`: noise-mode check, `diag_slr_convergence_by_chain_ladrillo.jl`,
`postprocess_mcmc_ext.jl --tag=L27 --accept-slr` (burn first half, pool in readdir order, step 400 → 10,000 draws; no
RNG), then `--dump-priors` (the package's `data/constants/ladrillo_priors_L27.csv` is a ready second gate).

- **Calibrator:** `calibrate_mcmc_ext.jl` 2536 lines; on L27's path only `brick_mengel.jl` → `build_brick_nu3_gis3`
  (nu3 glaciers, 3-basin Greenland). Droppable: mengel/nu/ab components, magdep (`--ais-ramp`), the ledger branch, a list
  of unused flags (`--gis-ordered`/`--gis-basins2` are hard-wired true). Ladrillo's `src/` already has the forward
  kernel; missing is the whole `logposterior` (:1664–1880), the priors (paleo MvNormal, `k10c`), parameter table, start
  repair, sampler call and chain writing. Same package versions in Ladrillo's Manifest; its Project.toml lacks the direct
  deps (Distributions, RobustAdaptiveMetropolisSampler, MCMCDiagnosticTools, ...).
- **Frozen inputs to ship:** the overdispersed starts and the L26 adapted covariance (derived from L26, not rebuildable),
  `param_priors.csv`, `gis_amp_prior.csv`, `calib_full_joint_params.csv`.
- **Targets:** `python/prep_recalib_targets_ext.py` (612 lines; Frederikse default, `--ais-imbie2026` opt-in; hard-coded
  path :88) and `python/ladrillo_data.py` (573; gsic-adjusted target, `t_glac_blocks.csv`, `extc_block_constants.csv`),
  plus `build_t_glac.py`, `build_t_gis.py`, `build_lws_grace_extension.py`, `download_obs.py`. Package targets already
  match by md5 (070f74ab, 3e751f78). **Non-public:** `dangendorf2024_KalmanSmootherHR_Global_v2.nc` (personal
  communication; feeds only the `dang*` columns, i.e. the unscored total that Table 4 and Fig. 1 use); GRACE needs an
  Earthdata login. Ship frozen copies with sha256, as `tools/forcing/inputs.sha256` does.
- **The research gate is weak (re-checked):** `benchmark/reference/calibrator_300iter_L27/chain_L27prod_seed2026_first300.csv`
  is 300 copies of one row (log_post 792.9208399273703); production's first acceptance is reportedly at row 460. Memory
  `calibrator_gate_reference_is_all_rejections`. The port's gate: logpost(θ₀) = 792.9208399273703 exactly on the package
  kernel, then the first 2k–20k rows of the seed-2026 production chain reproduced on this machine, and a mutant that
  leaves θ₀ alone.
- **Rename traps:** SLOWP→SLOWG, FAST→FASTG in the parameter table, `BLOCKS`, `AMP_PRIOR`, `GLAMBIE_FAST_SHARE`, Mimi
  variables, `t_glac_blocks` columns, `extc_block_constants`, the starts/covariance headers. Handoff
  `notes/handoff_2026-10-07_clean_l27_repo.md` §B/§F has the earlier port plan.
- Size: ~1,000–1,300 Julia + ~1,100 Python lines, ~8 data files, the gate; 2–4 sessions. Bit-identity of a full rerun
  holds only on this machine/BLAS/Julia; elsewhere statistical agreement (L27r/L27b agreed to ≤ 1.3 cm at 2300).
- Suggested split: (1) calibrator + logpost(θ₀) + chain-prefix gate; (2) post-processing + dump-priors gate; (3) target
  builders with frozen inputs; (4) README/Code-availability text, CHANGELOG, mutation tests.

## 6. Next steps

1. Marcus to choose where the calibration port runs (new session recommended; this note is its brief).
2. When Marcus saves his hand edits: the draft pass per 11-11b §4 plus §4 above, on a NEW output file.
3. At release: tags per 11-11b §4.3.

## 7. Non-obvious state

- Ladrillo.jl `outputs/hindcast/` and `outputs/projections/*vv*` were regenerated 11-11 (provenance only changed);
  SSP projection products still carry 10-08 provenance ("Ladrillo 1.2.0-DEV").
- `python/tables/mutation_test_tables.py` now needs `outputs/hindcast/postpred_*` to exist (copies them).
- The `INPUTS.manifest.json` change in SLR-RFF-BRICK's working tree (RFF-SP Zenodo DOI, 10-30/31) is another session's;
  not touched here.
- Scratchpad is gone with this session.
