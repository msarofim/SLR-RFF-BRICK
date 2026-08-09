# Handoff 2026-08-09 (evening) — extC surgery COMPLETE + validated; launch gated on amp-basis call (cross-dataset check running); then tuning → production → comparisons → sharing memo

**Self-contained pickup:** this note + memory `project_brick_mengel_vnext_recalib` (top
block) + memory `feedback_brickf_sharing_memo_spec`. Branch `brick-mengel-vnext`.
Commits today (in order): 6abb477 (T1 memo), e8e8666 (T2 memo), 0646571 (D1e spec+cell),
1a55663 (D1e results), bc99223 (d1f script), 9f09a03 (d1f results), 6771ed5 (extC
surgery), + CHANGELOG commits. Session task list: #3 tuning+production, #4 projections/
comparisons, #5 sharing memo (all pending; #1 d1f and #2 surgery completed).

## 1. What happened today (one paragraph each)

- **T1/T2 memos** (`memo_2026-08-09_t1_s1900_box_scope.md`,
  `memo_2026-08-09_t2_structural_assessment.md`): S(1900) box provenance + honest
  structural assessment. Record corrections that MUST be used going forward: the
  like-for-like adjusted modern-rate comparator is **0.766 mm/yr** (not 0.81); headline
  C_both SSP levels are **9.06/11.23/15.78** cm (the arc handoff's 7.7/9.8/14.1 was the
  A_4rung ablation row); D1d gate status was 3/4 not 4/4.
- **Marcus ruled Option D** (model-side ledger; datum untouched), under his two-issue
  frame: (a) scope-matched historical target with set-asides, (b) model design for
  remaining history + present + scenario responsiveness. **D1e executed**
  (`note_2026-08-09_d1e_dside_ledger_verdict.md`): ledger = S_inv + S_r5 N(2.5,2) +
  U_pre flat[0,25] vs N(20,9); ANCH/MID now 4/4 gates, deficits unchanged, U_pre fits
  interior ~9–10 mm. P3 falsified informatively: FREE's high early melt is
  FLOW-driven (U_pre rails to 0), not Leclercq-pull — softens the "pure scope" story.
  P&M 2018 PDF now in `~/Documents/2026/ClaudeDocs/Papers/`, read in full; 7 receipts
  in `memo_2026-08-09_d_ledger_target_spec.md` §1 (incl. 1901 uncharted stock
  18.8–50.4 mm derivable; Frederikse's 13%-r5 regionalization is their own invention
  vs P&M's 43.1% r5 small-glacier area share).
- **Marcus green-lit extC + the obs-amp arm. D1f** (`d1f_obsamp_arm.py`): obs
  through-origin amps R19 0.61 / SLOWP 2.48 / FAST 1.40 vs regchar 1.03/1.70/1.23.
  MATERIAL per pre-registered rule, but the nuance is: **MID (the extC design) is
  deficit-invariant to the basis** (6.79 either way); ANCH's modern-rate bias flips
  sign (+26% ↔ −11%); projections differ ~1.5 cm (obs-fit closer to AR6). So the amp
  choice is a projection-side call, not a fit-side one.
- **extC surgery COMPLETE** (commit 6771ed5, details §2). Port-validated at ~5e-13 on
  both amp bases; smoke 50-iter accept 0.34.

## 2. The extC calibrator as it now stands (commit 6771ed5)

`julia/calibrate_mcmc_ext.jl`: **39 physical + 10 AR(1) = 49 params.** Glacier side:

- 3 reservoirs × (a_b, b_b, T_off_b, log10κ_b). a: Farinotti priors (R19 0.069±0.018;
  SLOWP/FAST = Gt-share split of 0.221±0.057). b/T_off: bounds-only (σ=10 ≈ flat; the
  per-block RUNG likelihood — data-basis committed %, band σ, cross-rung corr 0.6 —
  constrains them; a Gaussian prior would double-count). T_off bounds widened to
  (−3.0, +1.0) — fitted R19/SLOWP sit at +0.27/+0.23. log10κ: τ50-as-prior, center =
  anchored solve **per amp basis**, σ = 0.114 (±30%). **ν_b FIXED at the anchored
  value** (MID design; hindcast cannot identify ν).
- Likelihood-only params (comp=:likelihood_only, never setp!'d, gic_*-named so θ0
  starts at prior mean): `gic_u_unch` (F_unch U, flat[14.5,41.8] mm, taper profile;
  enters the gsic FLOW channel and the dang TOTAL channel on the model side; **never
  in the Mimi graph** — AIS feedback sees only real melt), `gic_delta` (N(0,0.30)
  mm/yr, obs-side ramp 1900–1959), `gic_u_pre` (flat[0,25]) + `gic_s_r5` (N(2.5,2),
  [0,8]) — the Option-D ledger on N(20,9), replacing the pre-D A2b.
- A2 inventory: sum(a_b) − S_all(2000) vs N(0.290,0.060). Per-block GlaMBIE rate
  terms (SLOWP 0.189±0.017, FAST 0.417±0.045; 2000–2024 mean; R19 excluded).
- gsic target = **obs_adj** (r19-seam; `outputs/recalib_targets_ext_gsicadj.csv`,
  asserted against the raw column). `--gsic-early-sigma-x2` still exists as the
  no-δ alternative — do NOT enable together with the default δ setup.
- `--amp-basis=regchar|obsfit` selects amp_b + matching κ anchors + matching offline
  (b,T_off) starts from `outputs/extc_block_constants.csv`.
- Component: `julia/glaciers_nu3_component.jl` (per-block lagged drivers named
  `glacier_surface_temperature_<BLK>` — the frame contract; slot Variable
  `gsic_sea_level` = R19+SLOWP+FAST so :global_sea_level/AIS wiring is preserved;
  `gsic_hind` = SLOWP+FAST is the seam scope). `build_brick_nu3` /
  `update_brick_nu3!` / `set_glacier_forcing3!` in `julia/brick_mengel.jl`.
- Machine-generated inputs (`python/build_extc_inputs.py` — rerun after ANY offline
  structure change, then re-validate): `data/observations/t_glac_blocks.csv`,
  `outputs/extc_block_constants.csv`, `outputs/recalib_targets_ext_gsicadj.csv`.
  ALL artifacts full precision (%.12f/%.12g) — 6-decimal CSVs broke the 1e-9 port
  validation twice (multi-region driver averages; amp truncation leaking through the
  splice tail).
- Validation: `julia/validate_glaciers_nu3.jl` **includes the calibrator itself**
  (PROGRAM_FILE guard skips sampling) → validates the real code paths. Run both:
  `julia --project=julia_v2 julia/validate_glaciers_nu3.jl 2000 2026` and
  `... 2000 2026 --amp-basis=obsfit`. Both PASS at ~5e-13 today.

## 3. THE GATE: amp-basis decision (Marcus, pending the dataset check)

Marcus leans obs-based amplification but asked how HadCRUT5's Arctic infill compares
to other products (HadCRUT4-era sparse-Arctic concern; SLOWP 2.48 is the sensitive
number; R19 0.61 is the least-observed). A background agent is running
`python/diag_amp_dataset_comparison.py` (it writes
`outputs/diag_amp_dataset_comparison.csv`): per-block through-origin amps from
**Berkeley Earth gridded** and **GISTEMP 1200km** with the same GTN-G regions,
GlaMBIE area weights, and windows (1901–2024, 1970–2024), self-tested against the
HadCRUT5 reference (R19 0.615 / SLOWP 2.484 / FAST 1.404 / aggregate 1.595).
**RESULTS ARRIVED (commit c52bd42, same evening):** self-test exact; block ordering
R19 < FAST < SLOWP robust in every dataset; **HadCRUT5 sits MID-RANGE on SLOWP**
(BE 1.82 / Had 2.48 / GISTEMP 3.46) and the spread is dataset CONTENT (5-deg
footprint arm < 0.02), with GISTEMP a uniform NH-high outlier and BE-vs-Had
divergence concentrated recently (BE's Arctic warms less post-2010). R19 is weakly
constrained everywhere (0.58–0.88; < half the cells observed early in ALL products;
BE = air-above-sea-ice variant, verified). regchar's SLOWP 1.70 sits BELOW the
lowest obs estimate. Dataset-informed sampled-amp priors: SLOWP [1.8, 3.5] center
~2.5 ([1.8, 2.6] if GISTEMP dropped), R19 [0.58, 0.88], FAST [1.33, 1.82].
**MARCUS RULED (same night): SAMPLED amp_b** — implemented (commit 02150d8) and
**extC1 TUNING LAUNCHED** (500k, seed 2026, --tag=extC1, sampled default; log
`outputs/mcmc/caliblog_extC1_seed2026_n500000.log`). Implementation facts: 3
`gic_amp_*` params, priors R19 N(0.72,0.15)[0.58,0.88] / SLOWP N(2.5,0.45)[1.8,3.5]
/ FAST N(1.45,0.15)[1.33,1.82]; sampled amp enters the likelihood ONLY via the rung
frame-conversion and the κ-prior center k10c(amp) (log-linear interpolation between
the regchar/obsfit τ50 anchor solves; κ excluded from the generic prior loop in
sampled mode); drivers built once at the prior centers — the amp-dependent splice
tail (2025–26) is read by no likelihood term (verified reasoning in the code
comment). **52 params total** (42 physical + 10 AR(1)). Fixed bases retained as A/B
arms (--amp-basis=regchar|obsfit); the port validator requires a fixed basis and
guards against sampled mode. Smoke: accept 0.24. NEXT after tuning: postprocess
--tag=extC1 → eval_chain_gates rewrite (§4 step 2) → rebuild
overdispersed_starts.csv (52-col header) → production per §4 step 4 (add
--tag=extC --amp-basis default sampled).

## 4. Launch procedure (after the amp call)

**Two-stage is MANDATORY** — `outputs/mcmc/overdispersed_starts.csv` is 39-col
2-τ-era and the calibrator hard-errors on `--overdisperse` until it is rebuilt.

1. **Tuning** (common start, ~40 min for 52 params):
   `cd ~/Documents/2026/CodeProjects/SLR-RFF-BRICK && julia --project=julia_v2 julia/calibrate_mcmc_ext.jl 500000 2026 --tag=extC1 --amp-mu=1.08 --amp-sigma=0.15`
   **`--amp-mu=1.08 --amp-sigma=0.15` is MANDATORY on every extC run** — the file
   default is the stale pre-A6-revision N(0.95, 0.10); the canonical BRICK-AM A6
   prior (CMIP6 land-frame secant, Marcus 2026-07-24) is only applied via the
   flags, exactly as extA108 did. A first extC1 tuning was run WITHOUT them
   (2026-08-09 night, my slip — posterior ais_gmst_amp 0.922±0.095 = the stale
   prior), deleted, and relaunched correctly.
   Acceptance expectation ~0.23–0.24 (opt_α 0.234).
2. **Evaluate tuning**: postprocess (`julia --project=julia_v2 julia/postprocess_mcmc_ext.jl --tag=extC1`
   — column-generic, works as-is) + gates. **`python/eval_chain_gates.py` is
   HARD-BROKEN for extC** (5-param single-reservoir assumptions; see the surgery-map
   items in the 2026-08-09 recon): rewrite it to exec the d1e prefix
   (forward_all/ledger machinery) and read the per-block θ columns; self-test against
   the `d1e_dside_ledger.csv` C_both/ANCH/unc_t5d row. Check: rung |z|, ledger z,
   inventory z, spread, ladder, per-block GlaMBIE rates, U/δ/U_pre posteriors vs
   priors (interior-not-railed), T_off vs bounds.
3. **Rebuild starts + cov from the tuning chain** (the extB2/extB3 two-stage pattern:
   postprocess writes `adapted_cov_extC1...`; build 4 overdispersed start rows into
   `outputs/mcmc/overdispersed_starts.csv` with the CURRENT 49-name header from real
   posterior draws at spread quantiles — see the calibrate header + the 2026-07-19
   audit lessons in memory).
4. **Production**: `julia/run_vnext_production.sh` pattern — 4 seeds × 2M,
   `--overdisperse --tag=extC --amp-basis=<CHOSEN>`, ~3.1 h wall, ~7.9 GB chains.
   Acceptance on the DELIVERABLE (SLR@2100/2150 R̂), not nuisance marginals.
   **`julia/diag_slr_convergence_by_chain.jl` must be repointed to
   build_brick_nu3/update_brick_nu3! first** (it still hard-codes 2-τ names and
   blocks `--accept-slr`).
5. Delete any stray smoke chains matching `chain_extC*` before postprocess (the
   chain-length-mismatch guard hard-errors).

**STATE AS OF 2026-08-09 ~17:30 — steps 1–3 DONE, step 4 RUNNING:**
- Tuning extC1 complete (correct A6 prior; accept 0.240; log
  `outputs/mcmc/caliblog_extC1_seed2026_n500000.log`). Posterior sane:
  ais_gmst_amp 1.01±0.15; glacier block stable across both tuning runs; amp
  posteriors R19 0.70 / SLOWP 2.58 / FAST 1.44 (SLOWP pulled up from 2.50).
- Gate eval (`eval_chain_gates_extc.py`, self-test PASS; commit c5f8af8):
  inv 88% / lec 98% / spread 98% pass; medians inv_z +0.09, ledger
  15.5+2.4+6.5=25.6 (z +0.62 — the JOINT fit finds more early melt than the
  offline ANCH, echoing the FREE-arm finding; legacy 10–30 box in for 84%),
  spread 6.25, ds 8.5/10.6/14.8, rate 0.807 vs 0.766, δ 0.7σ.
  **ACCEPTANCE-REVIEW ITEM — ladder gate 39%:** all failures HIGH side, led by
  +1.2K crossing its top edge ~2 pts (com1p2 med 56.1 vs 54.0) on the MODEL
  basis: the posterior melts S2020_all ≈ 74 mm (vs offline ANCH 46.5 — i.e. it
  FITS the century better), shrinking the remaining-stock denominator. The rung
  LIKELIHOOD is data-basis (fixed S2020_data) and satisfied by construction.
  Resolution for the review: emit data-basis com in the evaluator (cheap: same
  formula with S2020_D constants) and report BOTH bases; the memo's ladder
  section must use the data basis + explain the model-basis shift as the
  century-integral improvement in the denominator. NOT the extB3 pathology
  (spread healthy; com1p2 56 not 63–100).
- Starts rebuilt (52-col, iceflow0 quantiles 1.023/1.127/1.184/1.277; old
  39-col file kept as `.pre_extc_bak`).
- **PRODUCTION LAUNCHED** via `julia/run_extc_production.sh`: 4 × 2M, seeds
  2026–2029, `--tag=extC --amp-mu=1.08 --amp-sigma=0.15 --overdisperse`, logs
  `outputs/mcmc/log_extC_seed*.txt`, ~3.1 h, ~7.9 GB.
- **REMAINING BEFORE --accept-slr: repoint `julia/diag_slr_convergence_by_chain.jl`**
  (still 2-τ: hard-coded gic_a/gic_T_lia/... symbol list + update_brick_mengel!).
  Spec: build_brick_nu3 to the projection horizon; per-block θ from chain columns
  (gic_a_R19 … gic_log10_kappa_FAST as 10^θ; ν from extc_block_constants
  nu_anch_obsfit; per-draw amp from gic_amp_*); per-block drivers = t_glac_blocks
  obs + amp_b × ssp245harm GMST splice EXTENDED to the horizon (replicate the
  calibrator's tg3 construction with the longer year grid); non-glacier params
  via update_brick_params! as now. Then postprocess `--tag=extC --accept-slr`
  → canonical subsample `parameters_subsample_brick_mengel_extC.csv`.

## 5. After acceptance (tasks #4, #5)

- **Projection drivers**: everything still calls the 2-τ `build_brick_mengel` (43
  sites; key list in the 2026-08-09 surgery-map: `project_ssps_gsic_2300_mengel.jl`,
  `project_ssps_2100_mengel.jl`, `project_ssps_components_2300.jl`,
  `weight_and_project_brick_fair.jl`, `posterior_predictive_ext.jl`, pulse drivers).
  Each needs: build_brick_nu3 + per-block SSP drivers (per-block obs T_glac + amp_b ×
  scenario GMST splice — NO Julia analogue exists yet; replicate the calibrator's tg3
  construction with scenario GMST files `fair_mean_gmst_{ssp126,ssp245,ssp585}.csv`)
  + per-block θ from the posterior subsample. NB **F_unch is a hindcast-target
  construct** — exhausted by 2005, flat thereafter; in projections re-referenced to
  1995–2014 it contributes only a ~1-mm baseline-tail sliver; include it in any
  hindcast-overlay figure, ignore it in future-only deltas (state the choice).
- **Comparisons**: pre-Mengel BRICK 2.0 (`outputs/ssps_gsic_2300.csv` Wong WR-GSIC
  exists), FACTS (`outputs/facts_components_n200.csv`, b2 machinery; parameter-only
  vs climate-spread caveat), MAGICC (magicc-comparison machinery from the June work).
- **Sharing memo — Marcus's spec is BINDING** (memory `feedback_brickf_sharing_memo_spec`):
  (1) short abstract up front summarizing ALL key data sources + model structure
  choices; (2) observation comparison; (3) SSP comparison vs FACTS AND MAGICC;
  (4) methodology section enabling Tony/others to implement (component equations,
  parameter table with priors/sources, calibration-data inventory, target
  construction incl. set-asides). **Style: declarative — state the choices and why.
  NO litigation of considered-and-discarded alternatives; the ONLY legacy comparison
  is pre-Mengel BRICK 2.0.** The T2 memo's conventions table (§3c) and the D-ledger
  spec memo are the raw material for the methodology section.

## 6. Traps / non-obvious state

- **Exec-prefix chain**: d1f → d1e → d1d → d0. Each splits the parent at
  `# ---...--- run\n` (64 dashes) with a uniqueness assert; output paths rebound
  AFTER the exec. `build_extc_inputs.py` and `emit_extc_port_reference.py` exec the
  d1f prefix. Any offline change ⇒ rerun builder ⇒ re-validate ⇒ recommit artifacts.
- **Calibrator CLI**: positional `N_ITER SEED` MUST precede flags
  (`parse(Int, ARGS[1])`).
- **paths**: run everything from the repo root; the shell cwd resets between tool
  calls — `git -C`, absolute paths, or leading `cd`.
- extB3/b/c chains in `outputs/mcmc/` are falsification evidence — keep. extA108 is
  still the canonical production posterior until extC is accepted. Pulse arms parked;
  Marcus flagged returning to CO2/CH4 pulse analysis after this program — the
  posterior-choice question (extA108 now vs extC later) is open.
- The A2b comment block in the calibrator documents the D-ledger implementation and
  the receipts-family provenance of N(20,9) — keep it with the term.
- d1e/d1f record corrections (0.766 comparator; per-row SSP quotes; 3/4 gates) must
  not regress into new prose — the notes carrying the stale numbers are
  `note_2026-08-09_d1d_fourrung_seam_verdict.md` and the arc handoff.
- HadCRUT5 ensemble-mean nc is UNTRACKED on disk (`data/observations/raw/`); the
  dataset-comparison agent may add BE/GISTEMP downloads there (also untracked).
- Julia env: `--project=julia_v2`. OPENBLAS/OMP threads 2 for 4-way production.
