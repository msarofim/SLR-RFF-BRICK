# Handoff — L26 promoted, L27 (50-parameter reduction) running, the GMD draft at review round 5 (09-16 → 09-20)

**Start here.** Continues `handoff_2026-09-16b_test6_ic_and_venue.md` (its §4 GMD-vs-JOSS case stands; venue
still Marcus's call) and, behind it, `handoff_2026-09-16_paper_start.md` (the paper's map: package extraction
for Tony's team, the `facts` remote, the FACTS/MAGICC-scope question — all still open). CHANGELOG
**09-16f → 09-20c** is the primary record (33 commits, `7ea8ae7..098304c` on `ladrillo-dev`, all pushed).
Read `INDEX_slr.md` and `INDEX_cmp.md` before touching a deliverable; memory files written this arc:
`ic_ladrillo_vs_brick20` (updated), `lws_central_default`, `l26_candidate_posterior`.

**STATE AT HANDOFF (2026-09-20 ~14:45):**
- **L26 is CHAMPION** in all six benchmark modules since 09-20 (`benchmark/champions.json`, frozen arm under
  `benchmark/reference/L26/`). L24 is the previous champion and STILL the posterior every number in the
  paper draft and the shipped memo rests on — nothing downstream of the promotion has been re-run yet.
- **L27 production is RUNNING**: 4 × 2M chains, launched 13:34, ETA ~19:00 (load 20–45 from another
  session's R jobs). `run_l27_postprocess.sh` is queued behind it (pid-wait on the interpreter+tag pattern)
  and will run: noise-mode gate → SLR-convergence diag → postprocess `--accept-slr` → prior dump → posterior
  predictive → SSP components (tap AND no-tap) → three joint bands → comparison → benchmark (control L26) →
  Table A1. Its log: `outputs/log_l27_postprocess_driver.txt`. ⚠ If the noise-mode gate FAILS it exits
  without postprocessing — see §5.
- Test suite `run_ladrillo_tests.sh` **10/10 PASS** on the current kernel (09-20, after the L27 loader changes).
- Draft: `deliverables/GMD.Ladrillo.v1_review-2026-09-20.docx` (Marcus's latest edits were in the 09-19b
  base; every change of mine is a tracked change under author "Claude"; his four comments are replied to).
  Still on L24 numbers throughout.

---

## 1. ⭐ NEXT (in order)

1. **Read the L27 result** when the postprocess lands (~20:30 with postprocess):
   `outputs/log_l27_postprocess_driver.txt` — (a) the noise-mode gate line, (b) projected-SLR R̂, (c) the
   R̂ table (expect the geometry ridge f₀/slope/T_on/precip_u still failing; λ/T_crit/γ absent), (d)
   `outputs/bench_ladrillo_L27.md` vs `_L26.md` — the ONE-AXIS test: with three likelihood-flat parameters
   removed and the ledger marginalised, the hindcast must be UNCHANGED within noise (posterior-predictive
   RMSE per window: compare `outputs/postpred_L27_components_timeseries.csv` to `_L26_`; L26 values are in
   CHANGELOG 09-20). If it is: L27 is the paper's posterior (50 parameters). If Greenland or glaciers moved
   by more than ~0.05 cm full-window, the ledger marginalisation (option D) is the suspect — rerun with
   `--no-ledger` dropped (L27b) before concluding anything.
2. **Re-run the IC test on the chosen posterior** (`julia/ic_hindcast_residuals.jl --tag=L27` 90 s →
   `scripts/run_ic_arms.sh L27` ~35 min): Δk vs BRICK becomes 15; expect ΔBIC at ρ ≤ 0.99 to turn positive
   (~+30) at the same ln L.
3. **Re-run the paper's projection arms on the chosen posterior**: `run_paper_arms_lws_central_20260918.sh`
   is the template (T=L24 inside — change `T=`; it quarantines what it replaces; ~1.5 h; then the figure +
   benchmark steps it contains; add `--paper` renders to `figures/paper/`). Then the hindcast figure, Table
   4 and Table 5 (IC), Table A1 (`python/ladrillo_prior_posterior_table.py --tag=`), Table A2
   (`python/ladrillo_table_a2.py --tag=`) all move to the new tag, and the paper's Antarctic text changes
   from "onset 1998" to a wide posterior. ⚠ The docx currently mixes nothing — keep it that way: swap
   every table and figure in ONE round.
4. Then the 09-16 list, unchanged: venue (GMD recommended), package extraction for Tony's team, the `facts`
   remote (Marcus's action), the FACTS/MAGICC-scope call, the "must STATE" items, the pulse analysis.

## 2. WHAT HAPPENED 09-16 → 09-20 (receipts: CHANGELOG entries named)

- **09-16f** Table 5 + the AIC paragraph into the L24 documentation docx (sync-first rule followed).
- **09-17** GMD draft reviewed as a REDLINE (`deliverables/redline/` tooling: `redline.py` +
  `apply_edits_r*.py`; tracked changes + comments, reject-all reproduces the original). Empty methodology
  sections filled (TE, LWS, code structure, availability), figure numbering, "L24" out of captions,
  references compiled.
- **09-18** Round 2: regrowth sentence CORRECTED (T_off < 0 for SLOWG/FASTG: full regrowth needs cooling
  BELOW 1850–1900), LWS start-year text, Table 5 widths, AIC paragraph streamlined, **runtime measured**
  (`julia/diag_runtime_ladrillo_vs_brick20.jl`: 1.25× BRICK per draw, model evaluation < 1 ms), +17
  references verified, closing paragraph. **LWS switched to constant 0.3 mm/yr on BOTH arms**
  (`LWS_MODE=:central`, memory `lws_central_default`); all 35 paper arms re-run; pre-switch outputs in
  `outputs/quarantine/20260918_lws_seeded/`; 4 LWS-driven benchmark flips at the 0.03–0.3 cm level.
  `plot_ladrillo_memo_figures.py` had a missing import since 01f25ef — fixed.
- **09-19** Table A1 built from the calibrator's own prior dump (`calibrate_mcmc_ext.jl --dump-priors`,
  `python/ladrillo_prior_posterior_table.py`; priors never transcribed). Shift evaluation
  (`notes/note_2026-09-19_prior_posterior_shifts.md`). Calibration review
  (`notes/note_2026-09-19_calibration_review.md`): **the nine "BRICK" priors were BRICK 2.0's POSTERIOR
  mean/sd truncated at ±2 sd** (`outputs/param_priors.csv`); the T_on over-precision explained by `--profile`
  (a switch scored against a smooth reconstruction at 0.06–0.35 cm/yr); SLOWG bound test (`L24TOFF4`: 23 %
  of mass below −3) and δ test (`L24DELTA0`: early glacier RMSE 1.44 → 0.45 cm at the cost of `u_unch` at
  its bound). Arms `L26a/b/c/d` (README in `outputs/mcmc/`): dropping δ fixes the early glaciers; the band
  correlation length L railed at 100 when sampled → fixed at 100. **L26 production** (09-19d/09-20).
- **09-20** L26 shipped (18/55 marginals fail R̂, projected SLR R̂ 1.002 → `--accept-slr`), IC test on
  L26 (ΔAIC +83 / ΔBIC −1 at ρ ≤ 0.99, Δk 20; Antarctica's share of the gain +6 → +1), **Table A2**
  (identified Antarctic combinations via PCA in prior-sd units; `python/diag_ais_block_pca.py`,
  `python/ladrillo_table_a2.py`; on the L24 basis in the draft), reduction analysis + pros/cons
  (`notes/note_2026-09-20_ais_reduction_and_L26_vs_L24.md`), **L26 PROMOTED**, **L27 launched**.

## 3. DECISIONS MADE (and why) — all Marcus's, in order

- LWS constant 0.3 mm/yr on both arms (09-18): the seeded draw added no spread and the two arms' realisations
  differed by 0.4 cm.
- δ: "follow the recommendation" = not sampled; the correlated band error is the structural replacement;
  `u_unch` (33–37 mm) is the physical device that carries the early century — the paper must say so.
- Nine DAIS priors → DAISfastdyn paleo marginals (MimiBRICK's own construction); thermal_alpha
  Uniform(0.05, 0.3). For λ/γ/ν/T_crit BRICK's posterior WAS the paleo prior; the switch bites through the
  ±2 sd truncation and on anto_α / antarctic_α / κ.
- L = 100 yr fixed (the sampled L railed at 100; a cumulative-reconstruction band is level-like); 20/50 are
  the reported sensitivities. The runoff-onset LOCATION follows L (1991/2027/2049/2063) — must be stated.
- T_off bound −4; κ–P₀ reparameterised (u = log P₀ + κ·T̄, T̄ = −17.992 = `LADRILLO_TBAR_ANT`).
- Priorities for L26/L27: justifiable fit > justifiable structure/priors > fewer parameters.
- L26 promoted 09-20 ("Do it" / "Do the recommendations"); L27 = A (cut λ, T_crit: likelihood exactly
  flat; joint paleo draws attached in projections), C (γ fixed at paleo median), D (ledger set-asides
  integrated out: N(2.0 − 1.5 cm, √(0.9² + 0.72² + 0.2²) cm) on the 1850–1900 melt). Option B (cut amp)
  NOT taken; F (fix f₀) rejected.

## 4. FILES (new or changed this arc; the CHANGELOG has the per-entry lists)

Calibrator `julia/calibrate_mcmc_ext.jl` — flags, ALL default-off, L24 prior dump byte-identical after
every change: `--dump-priors`, `--profile=`, `--toff-lo=`, `--delta-sigma=`, `--paleo-priors`, `--no-delta`,
`--no-d2-gsic`, `--obs-corr-len=<L|sample>`, `--precip-reparam`, `--cut-fastdyn`, `--fix-gamma`, `--no-ledger`.
Kernel `julia/ladrillo_projection.jl`: `LADRILLO_TBAR_ANT` + log P₀ derivation (gated,
`julia/test_ladrillo_precip_reparam.jl`), `ladrillo_used_cols(variant, header)` (header-aware column
selection — chain readers MUST use it), `ladrillo_attach_propagated!` (λ/T_crit joint paleo draws from
`outputs/paleo_fastdyn_draws.csv`, seed 20260920; γ at paleo median). Chain readers updated:
`scope_slr_fair_uncertainty.jl`, `diag_slr_convergence_by_chain_ladrillo.jl`; `posterior_predictive_ladrillo.jl`
(absent δ = 0). Run scripts: `run_mcmc_L26.sh`, `run_mcmc_L27.sh`, `run_l26_postprocess.sh`,
`run_l27_postprocess.sh`, `run_paper_arms_lws_central_20260918.sh`, `scripts/run_ic_arms.sh <TAG>`.
Diagnostics: `julia/diag_runtime_ladrillo_vs_brick20.jl`, `julia/diag_ais_leverage.jl`,
`python/diag_ais_block_pca.py`, `python/ladrillo_table_a2.py`, `python/ladrillo_prior_posterior_table.py`.
Figures: `--paper` mode in the six figure drivers → `figures/paper/` (no title/footer, "Ladrillo" not the
tag; footer text in a sidecar .txt). Data: `outputs/paleo_dais_marginals.csv`, `outputs/paleo_fastdyn_draws.csv`,
`outputs/ladrillo_priors_{L24,L26,L27t}.csv`, `outputs/ladrillo_prior_posterior_{L24,L26}.{csv,md}`,
`outputs/ladrillo_table_a2_{L24,L26}.md`, `outputs/ic_ladrillo_vs_brick20_L26*`, `outputs/l26_arms_hindcast_rmse.csv`,
`outputs/mcmc/{overdispersed_starts_L26,overdispersed_starts_L27,adapted_cov_L26_named}.csv`,
`data/MimiBRICK/parameters_subsample_brick_mengel_L26.csv` (force-added; the dir is gitignored).
Docx: `deliverables/GMD.Ladrillo.v1_review-2026-09-{17,18,18b,19,19b,20}.docx` (untracked, Marcus's
lineage; each is the previous plus one tracked round), `deliverables/GMD_TableA1_priors_posterior_L24.docx`.

## 5. ⚠ NON-OBVIOUS STATE / TRAPS

- **Never mix L24 / L26 / L27 outputs** in one figure or table. Every cells CSV now carries a `provenance`
  column; the figure stamps declare the tag (`ladrillo_figs.TAG_DESC`, L26 declared, L27 NOT yet — add it
  before any figure driver runs with `--tag=L27`, or the driver refuses).
- **The L27 start point matters.** The MAP start's noise init is sd = 1.0 cm; `L27tune` (500k from the MAP)
  was still burning sd_gis down (0.66 at the end, log-post 479 vs 784) — NOT a mode, a start. Production
  starts from L26 draws; the postprocess driver's NOISE-MODE GATE (sd_gis < 0.10 in every chain) guards it.
  If it fails, do not `--force`; investigate (`--profile` on the noise params; or restart from the L26
  starts with L26's adcov — that IS the current configuration, so a fail would mean something real).
- **Chain readers select columns by name from a 2.2 GB file and CSV.jl drops missing names silently.**
  Use `ladrillo_used_cols(variant, header)`. Scripts still on the one-argument form (the scope_*/diag_*
  family in `julia/`) work on L24-era chains only.
- **The IC script now reads k from the posterior headers** (asserts L24 = 50 + 8, BRICK = 27 + 8).
- **`bench_ladrillo.py --promote`** was used for L26; `--freeze` first. Champion registry has the 09-20
  reasoning verbatim.
- **Projection outputs on disk are a MIX of vintages**: the L24 paper arms (09-18, LWS central), L26's three
  SSP joint bands (09-20), nothing for L27 yet. The paper figures in the docx are the 09-18 L24 renders.
- **`outputs/param_priors.csv` is BRICK 2.0's posterior moments** — still read by the default (L24) path,
  by `diag_ais_mwp1a_lambda.py` and the old `ladrillo_posterior_summary.py` (Aug 10, 52 params — do NOT cite).
- **Runtimes under contention**: the other session's R multistart jobs put the load at 10–100; Ladrillo
  chains then run 1.5–2×. Torch was reserved for FrEDI through 09-19; if that reservation lifts, a 4-chain
  run there is ~3 h. Kill by PID, never `pkill -f` (the resolved interpreter path does not match).
- `gic_T_off_SLOWP` bound −4 is now in L26/L27 (the −3 bound clipped 23 %); `u_unch` sits in the upper half
  of its Parkes & Marzeion range in every δ-free arm — say so in the paper.
- `hetero_logl_ar1` takes an optional L; `--obs-corr-len=sample` adds `obs_corr_log10L` (56 params) — used
  for L26d only.

## 6. OPEN QUESTIONS FOR MARCUS

- Splice the observed LWS series into projections (comment [3] reply): +0.4–0.6 cm on every projection
  total, both arms, one figure re-run. Not done.
- `gis_slow_w` (unidentified, projection-relevant): fix at the offline 0.93 or give it a prior — decision,
  not evidence.
- Option B (cut amp from the MCMC): would make "propagated" literal for the dominant projection lever at
  the cost of a ≤ 1.5 log-unit constraint.
- The T_on precision tests specific to the AIS series (σ ×3 pre-1992; fit-to-1992 / predict) were held
  because the correlated error already widened T_on 4×; still worth one chain if a reviewer asks.
- Venue (GMD vs JOSS), and everything in the 09-16 handoff §1.
