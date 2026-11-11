# Handoff 2026-11-11d: calibrator ported into Ladrillo.jl; the L27 chain held gamma at 2.038

Session `ce77075c` (launched from FaIRtoFrEDI, worked in Ladrillo and SLR-RFF-BRICK), 2026-11-11 15:00 onward.
Previous: `notes/handoff_2026-11-11c_table4_seeds_calibration_scope.md` (its §5 scoped this work; §4 still lists the
draft-pass items). The GMD draft was still the 10:19 save at 15:05 (Word lock file from 14:00): the draft pass has not run.

## 1. What we were working on

Piece (1) of the calibration port (11-11c §5): the calibrator, logpost(θ₀) and a chain-prefix gate.

## 2. Done (Ladrillo.jl `main`)

- `src/calibration.jl` (module `Ladrillo.Calibration`): L27 log-posterior, parameter table, start rows, proposal seed,
  `run_chain`. Port of `julia/calibrate_mcmc_ext.jl` with `run_mcmc_L27.sh`'s flags, on the package's `LadrilloModel`
  (1850-2026, lws `:central`, tap off). Drivers built once at the amp prior centres, as in the research code.
- `scripts/calibrate.jl <n_iter> <seed>`: chain CSV, adapted covariance, provenance txt (seed and where applied).
- `data/calibration/`: starts, `adapted_cov_L26_named.csv`, `gis_amp_prior.csv` (via `tools/import_l27_data.py --only`,
  MANIFEST rows at source 88323e0).
- Deps Distributions / LinearAlgebra / RobustAdaptiveMetropolisSampler. ⚠ `Pkg.add` silently upgraded Distributions
  0.25.126 → 0.25.134 despite `preserve=PRESERVE_ALL`; reverted and re-added with explicit versions. Manifest now equals
  `julia_v2` on every shared package.
- Gate `test/calibration/gate_chain_prefix.jl` (~2 min): logpost at the four starts == production; first 20,000 rows of
  seed 2026 == production (log_post every row; all 50 params at 44 rows; 4,603 moves). PASS. References from the four
  production chains via `tools/build_test_reference.py` (new `chain_*` kinds; sha256 of each 2 GB chain in SOURCES.csv).
- `test/runtests.jl`: start-row check + parameter table == research `--dump-priors` (`ladrillo_priors_L27.csv`), all
  50 rows exact.
- Mutation test `test/calibration/mutation_test.sh`: RESULT_PENDING
- README (*Reproducing the calibration*, *Known issues* gamma item, layout), CHANGELOG 2026-11-11e.

## 3. Finding: L27 was sampled with gamma = 2.038 (central row), products use 2.834

`calibrate_mcmc_ext.jl` sets the paleo medians at :1605-1607, then `update_brick_nu3!(m, medoid, …)` (:1627) loads the
central row over λ, T_crit and γ. Port with paleo medians missed the four production starts by −0.015…+0.034; with the
central row it matches exactly. λ/T_crit are inert in the hindcast (bitwise); γ is not. Every product attaches
γ = 2.834 (`attach_paleo!`, research `ladrillo_attach_propagated!`).
Paired 500 draws, 2.834 vs 2.038: hindcast AIS ≤ 0.015 cm; projections ≤ 0.13 cm to 2100; 2300 AIS median −1.4 (ssp245),
−3.2 (ssp585), −2.6 cm (vvH); ssp585 2300 total median −4.1 cm.
Importance reweighting of the 10k posterior to γ = 2.834 (estimates a recalibration): w = exp(lp₂.₈₃₄ − lp₂.₀₃₈), dlp
−0.27…+0.42, ESS 99.7 %, max weight 1.5× uniform; reweighted quantiles (AIS, total; 2100/2300; ssp245/585) move ≤ 0.54 cm.
So the shipped products equal what a calibration at 2.834 would give, to ~0.5 cm.
Memory: `l27_held_gamma_is_central_row` (new), `l27_paper_posterior` corrected, pointers in `INDEX_slr_post`.

## 4. Open decision (Marcus)

Which γ the release uses: keep the products and state the as-run values; re-run the products at 2.038; or recalibrate
at 2.834 with the package calibrator. DECISION_PENDING

## 5. Next steps

1. Marcus's γ decision (§4).
2. Calibration port pieces (2)-(4) per 11-11c §5: post-processing (`postprocess_mcmc_ext.jl --accept-slr`; dump-priors
   gate is already covered by `parameter_table`), target builders with frozen inputs, Code availability text.
3. Draft pass when Marcus saves (11-11b §4 + 11-11c §4), plus the γ wording from §4 here.

## 6. Non-obvious state

- Diagnostics from this session (scratchpad, gone with it): research/package state dumps, `gamma_effect.jl`,
  `gamma_reweight.jl`. The method is in the memory file.
- The research calibrator still says "held at paleo medians" in its comments; not edited (it is production code and
  reproduces L27 as is).
