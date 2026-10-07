# Handoff 2026-10-07: build the clean, submission-ready Ladrillo L27 repository

Follows `handoff_2026-10-01c_gmd_round.md` (the GMD draft state; Tony has `…forTonyreview.docx`, his partial pass is
`deliverables/GMD.Ladrillo.v1_forTonyreview_TW1.docx`). Source branch: `SLR-RFF-BRICK` `ladrillo-dev` at `92cb634`.

## 1. What and why (Marcus 10-07)

Tony asked for a reviewer-style "obtain Ladrillo from GitHub and run an example" path, and to rerun the full workflow.
Marcus: *"the code should run FaIR & Ladrillo, but not FACTS or MAGICC. And for Ladrillo, only L27, no history. The
calibration code can be included if someone wants to rerun that, but the meat is the already-calibrated sea level rise
emulator itself. ... a clean L27 repo with the right names for SLOWG and FASTG, and whatever else needs to be done to
make it submission worthy."*

**Decisions made (Marcus 10-07, AskUserQuestion):**
1. **A proper Julia package**, `Ladrillo.jl` (src/, Project.toml with its own name/UUID, `using Ladrillo`), plus
   `scripts/` for FaIR forcing, calibration, figures. Registry later (Tony mentioned it).
2. **BRICK 2.0 is rerun by the repo; FACTS and MAGICC-SLR outputs ship as static data** (with a note on how made), so
   every paper figure regenerates.
3. **Keep the land-water frame step in v1.0** (`LWS_OBS_ANCHOR = :v1_step`); document as a known issue; fix at v1.1.
4. **Claude creates a PRIVATE GitHub repo** with `gh` once the local build passes; Marcus makes it public / adds Tony.

**Acceptance criterion (Claude's, not yet confirmed by Marcus):** the new package reproduces the shipped L27 outputs
**bit for bit** (projection components and totals at every year, per draw, both arms) from the old repo, and the
renamed posterior differs from the old one ONLY in column names. A mutation test proves the identity gate can fail.

## 2. ⛔ OPEN DECISIONS — ask Marcus before building

1. **The van Vuuren forcing basis.** The paper's vv arms (L27 and BRICK 2.0, run 09-21) used FaIR 1.6.0 parameters on
   SMITH 2024 history; corrected to the CMIP7 basis 10-02 (commit `31aa963`, memory `vv_arm_was_smith_history`; the
   old cubes are in `outputs/quarantine/20261002_vv_smith_history_basis/`, ignored). SSP arms and the calibration
   driver were already CMIP7-basis — unaffected. Options:
   (a) ship the Smith-basis cubes as data and keep the paper's numbers (repo then ships a known input mismatch);
   (b) rerun L27 + BRICK 2.0 vv arms on the CMIP7 cubes and update Sect. 4.2–4.3 / Figs 2–6 numbers — but the FACTS
       comparison ran on the same (Smith-basis?) configs, so the comparison becomes MIXED-BASIS unless FACTS is rerun
       too (`like_for_like_forcing`). Verify FACTS's basis before recommending.
2. **Raw chains.** `scope_slr_fair_uncertainty.jl:184` (the joint-arm projections) and `python/diag_ais_block_pca.py:30`
   (Table A2) read the 4 × ~2 GB raw chains `outputs/mcmc/chain_L27_seed{2026..2029}_n2000000.csv`, NOT the 10k
   subsample. Ship the chains on Zenodo (~8 GB), or switch both to the subsample (numbers move slightly; quantify).
3. **Redistribution:** Dangendorf v2 (`raw/dangendorf2024_KalmanSmootherHR_Global_v2.nc`) came by personal
   communication — rights? FaIR `calibration_v160_prod/` inputs are untracked with no licence — download them from
   Zenodo 10.5281/zenodo.18828694 in a script rather than redistribute.
4. Minor: `regen_imbie_fig_L27.sh` is stale (expects the IMBIE target build); drop or fix.

## 3. The manifest (Explore survey, 10-07) — act on this

### A. Projection path
Include chain `ladrillo_projection.jl:81-82` → `brick_mengel.jl` (+ glaciers_mengel, glaciers_nu, glaciers_nu3,
greenland_ab, greenland_3basin, brick_param_updates) + `antarctic_icesheet_magdep_component.jl`.
Drivers: `scope_slr_fair_uncertainty.jl:72`, `project_ssps_components_ladrillo.jl:46` (writes
`ssps_components_2300_L27.csv` with `--no-tap`, `…_L27_tap4p69K_V5p64m_tau800_n2_ws.csv` default),
`posterior_predictive_ladrillo.jl`, `diag_slr_convergence_by_chain_ladrillo.jl`, `ic_hindcast_residuals.jl`.
**Reached for `:basins2`:** `ladrillo_posterior` → `lws_frame_guard`, `ladrillo_gis_variant`, `ladrillo_used_cols`,
`ladrillo_gis_needs_native`, `ladrillo_precip_reparam`, `ladrillo_native_greenland!` → `ladrillo_attach_propagated!`;
`ladrillo_setup` → `_yearmap`, `_running_mean`, `ladrillo_gis_shape`, `build_brick_nu3_gis3` → `build_brick_nu3` →
`set_lws!(:observed)` → `lws_observed_increments`; `update_brick_nu3!` → `update_brick_params!(skip_greenland=true)`,
`set_forcing!`, `set_gis_forcing!`, `update_gis3_shares!(GIS2_VSHARE)`, `ladrillo_basin_k`, `_funch_unit`;
per draw `ladrillo_set_tap!` → `update_gis3_tap!`; `ladrillo_run_draw!` → `ladrillo_apply_draw!` (precip_u branch
:833) → `ladrillo_gis_driver`, `ladrillo_driver`; `ladrillo_series` → `ladrillo_rebase`.
**Dead for L27:** glaciers_mengel (+build/update_brick_mengel!), glaciers_nu (+build/update_brick_nu!,
set_glacier_forcing!; only `GIC_REGROW_R` used by nu3), magdep AIS + all ramp paths; Greenland `:ab`
(build_brick_nu3_gis, update_gis_ab!, greenland_ab) and `:basins`/3-basin (tests 4/6/8 only), `:stock` (test 12 only);
`gis_ab=`, LWS `:seeded/:zero/:random`, `--tap-set`, `--ton-band`, `--chain-tag`, `--build-ssp`, `--maxrows`,
non-default `LADRILLO_GIS_SHAPE` tables; non-L27 posterior constants `ladrillo_projection.jl:106-125`.
**Runtime reads (all tracked):** L27 subsample (9.8 MB), `t_glac_blocks.csv`, `t_gis_zones.csv`,
`fair_mean_{gmst,ohc}_{ssp126,245,585,ssp245harm,vv*}.csv`, `fair_cube_{gmst,ohc}_{ssp*,vv*}_raw.csv` (~3.5 MB each),
`fair_cube_*_ssp585_spliced.csv` ([SPLICE-MATCH]), `outputs/extc_block_constants.csv`, `gis_amp_shape.csv`+`_meta`,
`recalib_central_row.csv`, `paleo_fastdyn_draws.csv` (5.8 MB), `paleo_dais_marginals.csv`, `recalib_targets_ext.csv`
(LWS_OBS_CSV), `ssps_components_2300_<SHIPPED_TAG>.csv` ([CONTROL]).

### B. Calibration path
`run_mcmc_L27.sh` inputs: `outputs/mcmc/overdispersed_starts_L27.csv`, `adapted_cov_L26_named.csv` (tracked).
Calibrator reads (tracked): `fair_mean_*_ssp245harm`, `recalib_targets_ext.csv`, `recalib_targets_ext_gsicadj.csv`,
`extc_block_constants`, `t_glac_blocks`, `t_gis_zones`, `gis_amp_prior.csv`, `param_priors.csv`,
`paleo_dais_marginals`, `paleo_geo_prior_ton.csv`, `recalib_central_row`, `calib_full_joint_params.csv`.
`ADCOV_DEFAULT` (:2044) = L11tune3 file, used by tests 2 and 5 — repoint to the L26/L27 named file.
`run_l27_postprocess.sh`: `diag_slr_convergence_by_chain_ladrillo.jl` → `postprocess_mcmc_ext.jl --accept-slr` (block
:145 vs `parameters_subsample_brick_mengel.csv` is dead) → `--dump-priors` (Table A1 input) →
`posterior_predictive_ladrillo.jl` → `project_ssps_components_ladrillo.jl` ×2 → `scope_slr_fair_uncertainty.jl` ×3 →
`ladrillo_model_comparison.py`, `bench_ladrillo.py`, `ladrillo_prior_posterior_table.py`. Keep
`scripts/gate_calibrator_identity.sh` + `benchmark/reference/calibrator_300iter_L27/`.
Flags needed: `--amp-mu/-sigma --paleo-priors --no-delta --no-d2-gsic --obs-corr-len=100 --toff-lo --precip-reparam
--cut-fastdyn --fix-gamma --no-ledger --tag --overdisperse --starts --adcov --dump-priors --gis-check --amp-basis`.
Dead under L27: no-ops `--gis-ordered/--gis-basins2` (hard true :341, :1143); `--ais-fit-from` :132,
`--steric-marg-cap` :142, `--gis-zone` :293, `--obs-corr-len=sample`, `--delta-sigma` :1081, `--ais-ramp` :878,
`--sd-ais-floor` (~:1500; only reader of raw/imbie2026), `--rho-max` :1559, `--profile` :2467; branches
build_brick_nu3_gis / build_brick_nu3 at :1602-1603, GISB_SHARE3, δ ramp, D2-gsic, sampled ledger, non-paleo DAIS priors.
`prep_recalib_targets_ext.py` (default = L27 target) raw inputs in `data/observations/raw/` (tracked):
frederikse2020 nc + xlsx, dangendorf2024 v2 nc (redistribution? §2.3), grace_{ais,gis}_mass.txt,
glambie_global_glacier_mass.csv, glambie_r5_greenland_periphery.csv, noaa_thermosteric_w0-2000m_yearly.dat,
imbie_{ais,gis}_2021_mm.csv; plus `dangendorf2024_gmsl_annual.csv`, `nasa_gmsl_annual.csv`,
`outputs/lws_grace_extension_L14.csv` (built by `build_lws_grace_extension.py` from GRCTellus nc, untracked 46 MB,
needs pyshp). Sources/licences: `raw/README_modern_extensions.md`. Hard path at :88.

### C. FaIR forcing (FaIRtoFrEDI, PRIVATE)
`scripts/build_fair_mean_v160.py` (recipe in `FTF/calibration_v160/README.md`: `--calib-dir calibration_v160_prod
--emissions-file calibration_v160/emissions_v160_cmip7_ssp245_harmonized.csv --tag ssp245harm --scenario-label
ssp245_harmonized --marker M`); `build_fair_cube_v160.py --ssp {ssp126,ssp245,ssp585}` (markers L/M/H, emissions
`calibration_v160_prod/emissions_v160_cmip7harm_<ssp>.csv`); `build_fair_cube_spliced_v160.py`;
`build_fair_cube_vv_v160.py --marker X` (§2.1). Upstream: `setup_calibration_v160_production.py` (Zenodo
10.5281/zenodo.18828694 + `v160_cache/*_forcing_timebounds_cmip7.csv`), `build_emissions_v160_ssp_rcmip.py`,
`build_emissions_v160_ssp245.py`, `build_emissions_v160_cmip7harm_vv.py` (Zenodo 20713982 v1.1.1); helpers
`fair_basis.py`, `fair_units.py`. `calibration_v160_prod/` untracked, no LICENCE. All builders hard-code OUT_DIR.
Env: fair 2.2.4, Python 3.14.3, numpy 2.4.2, **pandas 2.3.3**, xarray 2026.2.0, scipy 1.17.1, matplotlib 3.10.8,
openpyxl 3.1.5, netCDF4 1.7.4. ⚠ `environment.yml`/`requirements.txt` pin pandas>=3.0 (wrong) and omit xarray,
openpyxl, netCDF4, pyshp.

### D. Tests (fresh-clone run 10-07: steps 1–5 PASS, step 6 aborts on untracked extC)
1 `test_ladrillo_data.py` OK. 2 `validate_glaciers_nu3` OK after repointing adcov. 3 `test_ladrillo_projection` OK.
4 `validate_greenland_ab` OK (rewrites tracked `outputs/gis_port_reference*.csv`). 5 `--gis-check` OK.
6 `validate_gis_projection_ab` needs extC (:stock header) + L12 (:ab header) → synthesize headers from L27.
7 `test_ladrillo_basins2_variant` needs `chain_L13` (2.4 GB) for a `gis_s_mid` header + 8 draws → L27 row +
synthetic `gis_s_mid=0`. 8, 9, 11 OK. 10 `test_gis_tap_wiring` defaults TAG=L14 → L27. 12 needs BRICK 2.0's
`parameters_subsample_brick.csv` (6.6 MB; gitignored by `data/MimiBRICK/*`) — ship it (MimiBRICK release data).

### E. Figures / tables
`run_paper_arms_L27.sh --paper`: `plot_hindcast_components.py`, `plot_model_comparison_components.py --set=vv`,
`plot_future_components.py --set=vv`, `plot_vv_gsic_wr_vs_ladrillo.py --ladrillo-only` (reads
`outputs/vv_gsic_2300.csv`), `plot_vv_responsiveness.py`. Table 4 `scope_ladrillo_vs_brick20_scorecard.py`;
Table 5 `ic_hindcast_residuals.jl` → `scripts/run_ic_arms.sh` → `ic_ladrillo_vs_brick20.py`; A1
`ladrillo_prior_posterior_table.py`; A2 `ladrillo_table_a2.py` ← `diag_ais_block_pca.py` (chains, §2.2); A3 by hand.
Shared: `ladrillo_figs.py` (prune VINTAGES L14–L30), `draws_io.py`, `gis_targets.py`, `provenance.py`.
Comparators (static): FACTS `outputs/facts_components_shared_n200.csv`; MAGICC
`data/comparison/magicc_nauels_components{,_hist,_vv}.csv`, `magicc_gmst_vv.csv`; BRICK 2.0 producers
`scope_slr_fairunc_oldbrick.jl`, `posterior_predictive_oldbrick.jl`, `project_ssps_components_oldbrick.jl`.
`ic_hindcast_residuals_brick20.csv` untracked (130 MB). MAGICC-climate arms read FTF/magicc_comparison (not in any paper PNG).

### F. Rename SLOWP→SLOWG, FAST→FASTG (keep R19)
Code: 148 `SLOWP`; `gic_{a,b,T_off,log10_kappa,amp,nu,kappa}_{SLOWP,FAST,R19}`, `glacier_surface_temperature_*`, Mimi
vars `gsic_slowp/gsic_fast/gsic_r19`, keys `ladrillo_projection.jl:896-899`, `NU3_BLOCKS/LADRILLO_BLOCKS/BLOCKS/
AMP_PRIOR/GLAMBIE_FAST_SHARE` (calibrator :225-231, :1224), `ladrillo_data.py:98-107`, `test_ladrillo_data.py:189-190`,
`diag_glacier_response_times.py:46,52`, labels `ladrillo_figs.py:189,292`. Data: L27 subsample cols 16-30, chains,
`adapted_cov_L26_named.csv`, `overdispersed_starts_L27.csv`, `t_glac_blocks.csv` cols, `extc_port_reference.csv`
(`drv_reg_SLOWP`…), `extc_block_constants.csv` `block` values, `extc_port_reference_theta.csv`,
`ladrillo_priors_L27.csv`, `ladrillo_prior_posterior_L27.csv`, `benchmark/reference/calibrator_300iter_L27`.
⛔ Blind-rename traps: `ladrillo_prior_posterior_table.py:216` already maps `_FAST→_FASTG` (→ `_FASTGG`);
`diag_gsic_blocks_vs_emulandice.py:53` already SLOWG/FASTG; leave `CUT_FASTDYN/--cut-fastdyn/DAISfastdyn`,
`FASTER/FASTEST/FASTX`, `SPEC_2BLK "FAST"`, Greenland `gis_fast*`, `fast_b`, `gis_alpha_f`, `gic_tau_fast`. R19 also in
`NON_R19`, `FARINOTTI_R19`, `diag_r19_*.jl`.

### G. Reviewer hazards
Hard paths: `prep_recalib_targets_ext.py:88`, `build_extc_inputs.py:37`, `scope_slr_fair_uncertainty.jl:136`,
`scope_slr_fairunc_oldbrick.jl:63`, all FTF builders. `~/climate-env` hard-coded in `run_l27_postprocess.sh:30,50`,
`run_paper_arms_L27.sh:35`, `run_ladrillo_tests.sh:81`, `scripts/run_ic_arms.sh:8`. MimiBRICK resolves from
github raddleverse/MimiBRICK.jl repo-rev v2.0.0 (Julia 1.12.6, Mimi 1.6.0, RAM sampler 1.1.0). LICENSE (MIT),
LICENSE-CONTENT (CC-BY) exist; CITATION.cff describes the OLD RFF-SP pipeline — rewrite. `ladrillo_figs.py` and
`bench_ladrillo.py` call `git` for provenance. Projection vs hindcast LWS modes differ by design (`:observed` +
`:v1_step` vs `:central`) — document.

## 4. Suggested build order (fresh session)
1. Settle §2 with Marcus. 2. New dir `~/Documents/2026/CodeProjects/Ladrillo/` (fresh `git init`), package skeleton.
3. Port the projection path (A) with dead code removed and the rename (F) applied; data with renamed columns.
4. **Identity gate first**: new package vs old repo, same draws, every component/year, `==` (rename-only diff on the
   posterior); mutation-test it. 5. Port calibration (B) + identity gate `gate_calibrator_identity` on renamed headers.
6. FaIR builders (C) with relative paths + Zenodo download. 7. Tests (D) on L27 only. 8. Figures/tables (E).
9. README quickstart (Tony's ask), CITATION.cff, environment files, docs. 10. Private GitHub repo (`gh`), push; Marcus
makes it public / adds Tony. Torch is not needed except for a full recalibration (4 × ~4 h on the M4).

## 5. Non-obvious state
- Fresh-clone test of `ladrillo-dev`: `scratchpad/freshclone/` (session scratch; disposable).
- Queued paper wording fixes for Tony's returned draft: `handoff_2026-10-01c_gmd_round.md` §1c (8 items).
- Tony's 10-07 review findings (4 edits that change meaning; answers to his R̂/ρ/discrepancy/compute questions):
  CHANGELOG 2026-10-07.
