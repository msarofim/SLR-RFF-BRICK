# Handoff — the ρ-cap test (L29) built, run and answered: the cap bound, the physics did not move; DAIS has no direction that produces the acceleration (09-21 19:30 → 09-22 01:30)

**Start here.** Self-contained for the ρ-cap arc; continues `handoff_2026-09-21b_imbie2026_L28.md` (the IMBIE target, L28, the
§4 structural verdict — its §3 traps stand) and supersedes `handoff_2026-09-21c_L29_rho_cap_launched.md`. Records: CHANGELOG
**09-21i** (the flag, the gate, the launch) and **09-22a** (the result); scoping note
`notes/scoping_2026-09-21_dais_structure_vs_imbie2026.md` **§5** (the argument). Commits `fcbe828`, `a539557`, `6f2e650` on
`ladrillo-dev`, all pushed. Memory: `mutation_test_gates` (+ the 09-21 no-power instance), `INDEX_diag` (one-liner),
`dais_structure_not_warranted_by_imbie2026` (revised in place, second time), `INDEX_ais` (one-liner; now 16.7 KB — over soft 14, under hard 18).

## 0. STATE AT HANDOFF (2026-09-22 ~01:30)
- **Champion and the paper's posterior are STILL L27**; draft r9 (`deliverables/GMD.Ladrillo.v1_review-2026-09-21c_L27.docx`);
  champions.json untouched; comment #12 (code availability) still open. L28 and L29 both landed, neither promoted.
- **The calibration target is IMBIE 2026** (`outputs/recalib_targets_ext.csv`, md5 eb768cd9…); the old Frederikse+GRACE file is
  quarantined; the identity gate is frozen on the IMBIE objective and was GREEN after this session's calibrator edit.
- **L29 = L28 + `--rho-max=ais:0.90`, complete through stage 2** (chains 19:57–00:07, pipeline ALLDONE 01:05; no paper arms,
  no vv MAGICC-climate arms). Chains (8 GB) on disk in `outputs/mcmc/`, not in git. **Nothing is running.** The four
  `calibration/run_dispersed_multistart.R` processes at 100 % are the CCX session's, not this arc's.
- Torch verdict was said out loud before launch: Mac (4 chains, ~4 h; ran 4 h 10 min under the CCX contention).

## 1. ⭐ NEXT (Marcus's rulings, in order)
1. **The steepening build?** L29 says DAIS's current parameter space cannot produce the reconciled record's acceleration, so
   §4's candidate 1 is now the only route to the record's shape: a **free exponent on DAIS's ocean-temperature ratio**
   (discharge speed (1−α) + α·rⁿ; nests DAIS at n = 2; one parameter; a curvature, not a claim) — vs a fast-dynamics onset inside
   the observed range (reads as "instability under way"; large projection consequences; a scientific claim). Scope before
   building: which term, its prior (n on [1, 4]? log-uniform?), the identity gate (a default that nests EXACTLY so the gate stays
   green), the start repair (none needed if the default is n = 2), and the **pre-registered success line**: 2011–17 rate within
   1σ of IMBIE's 0.056 WITHOUT the early century worsening past its current −1.8σ, and the 1979–2023 cumulative held. ~4 h Mac
   per refit, same recipe as `run_L29.sh` (frozen copy, one axis vs L28).
2. **Which posterior the paper ships** — unchanged by L29: L27 (old target, consistent draft) vs L28 (new target, level not
   shape, ρ on the bound) vs post-structure. Do NOT swap the draft to L28 or L29 as is. If L28: the 14 vv MAGICC-climate arms
   (FIG 11 / regrowth attribution) are still unrun (~1 h) and the benchmark's L27* rows must be re-scored on the IMBIE target
   before any "vs champion" claim.
3. The 09-16 list: venue (GMD), package extraction for Tony's team, `facts` remote, FACTS/MAGICC scope, pulse analysis.

## 2. WHAT LANDED — the flag (09-21i)
- `--rho-max=<series>:<val>[,<series>:<val>]` in `julia/calibrate_mcmc_ext.jl`: `RHO_MAX` is a vector over `SERIES`
  (`[:ais,:gsic,:gis,:steric]`), default 0.99 each, read by the hard rejection (the old literal at `:1490`) and the
  `--dump-priors` table. **Per-series on purpose**: a single cap would also move `rho_gis` (0.96–0.99) and `rho_steric`
  (0.90–0.99) and the arm would stop being one axis. `repair_rho_start!` moves a start ρ above the cap to 0.95×cap with σ
  scaled so the marginal σ/√(1−ρ²) is held (mirrors the steric repair). Bad series / value outside (0, 0.99] error at load.
- **Identity gate PASS with the flag absent** (byte-identical chain + covariance). **Mutation**: `ais:0.90` on the gate config
  returned an IDENTICAL chain — no power (the L24 start row is at ρ 0.61 and 300 iterations never propose above 0.66). The
  mutation with power: cap 0.60 (below the start) → repair fires, chain differs, max ρ 0.59998928 without crossing. Lesson in
  `mutation_test_gates`: for a truncation, mutate to a value the reference trajectory actually crosses.
- `run_L29.sh` = `run_L28.sh` + the flag, otherwise identical (IMBIE md5 asserted; `BASEFLAGS --no-ledger`; seeds 2026–2029;
  starts `overdispersed_starts_L27r.csv`; proposal `adapted_cov_L27_named.csv`). Arm verification greps the cap banner + the
  repair per chain; the noise gate also FAILS if any chain's second-half `rho_ais` reaches the cap. Stage 2 (prior dump, no-tap,
  joint bands ×3, flux split, IMBIE diagnostics, model comparison, benchmark, prior/posterior table, refit precision vs L28)
  folded in. `L29` declared in both figure TAG_DESC guards (`ladrillo_figs.py`, `plot_ladrillo_memo_figures.py`).
- New `julia/diag_ais_tipped_share.jl --tags=L27,L28,L29 --ssps=ssp126,ssp245 --gap=15`: per-draw AIS at 2100/2300 and the share
  of draws above a gap (the tipped mode), written because a p95 on a bimodal tail is a step function of that share.

## 3. WHAT LANDED — the result (09-22a; scoping §5)
- **The cap bound**: `rho_ais` 0.966 (L28) → **0.885** (p05–p95 0.838–0.899; max < 0.90 in every chain); cost ~2–7 log-units on the
  second-half log-post median (L28 819.6–821.7 → L29 812.6–819.6; the Gaussian estimate from L28's ρ sd 0.025 × Δρ 0.08 is ~5).
  Acceptance 0.238 (L28 0.239); noise gate PASS; SLR R̂ 1.003, `--accept-slr`.
- **Nothing physical moved**: every Antarctic parameter within 0.1 L28-sd (anto_α 0.287 → 0.286, ice-flow₀ 1.064 → 1.063,
  antarctic_α 0.302 → 0.307, T_oc,0 1.026 → 1.026, amp 1.041 → 1.027) except `ais_c` 80.2 → 74.6 (−0.3 sd); `sd_ais` 0.0139 →
  0.0138; `diag_refit_precision_L27_L28_L29`: every per-chain move inside ±0.5 L28-sd. The SMB parameters' SPREAD widened
  (precip_u sd ×1.8, runoff_Ton ×2.2) without their centres moving.
- **The fit did the level again, by a little** (model-only p50): 1979–2023 cumulative 1.226 → 1.300 cm (IMBIE 1.328; z −0.76 →
  −0.21); 2011–17 rate 0.0391 → **0.0418 cm/yr** (IMBIE 0.0556; z −2.10 → −1.79 — ON the §3 line of 0.042); 1992–2020 z −1.84 →
  −1.34; 2018–23 overshoot +0.88 → +1.12σ; early century unchanged (1900–78 net −50.6 → −46.9 Gt/yr vs target −20; bench 1920–49
  bias −1.86 → −1.82 sd); bench AIS hindcast RMSE 1.53 → 1.45σ. **The acceleration-window discharge anomaly (1992–2002 → 2011–17)
  is −52.0 Gt/yr — L28's −51.6, IMBIE −106.** The extra modern rate came from SMB (anomaly −23 → −33; IMBIE −14).
- **Projections**: medians ≈ L28 (fixed-climate AIS SSP2-4.5 2100 8.1 → 8.5 cm, 2300 166 → 168; SSP5-8.5 36.1 → 36.6, 272 → 278;
  SSP1-2.6 5.2 → 5.7). ⚠ **SSP1-2.6 p95 30.3 → 17.0 (2100), 50.4 → 30.5 (2300) is the tipped SHARE crossing 5 %** — L27 8.85 → L28
  7.60 → **L29 5.25 %** of draws with AIS@2100 > 15 cm; p83/p90 unchanged (6.5/7.2 → 6.9/7.5); SSP2-4.5 41.6 → 40.4 %. A 2.3-point
  move on 2000 draws is ~4 binomial se: real, small, a step function on the p95, not a sensitivity change.
- **Verdict**: neither pre-registered branch — the sensitivity parameters did not rise (a), the fit did not degrade (b). With ρ
  unable to price the acceleration, DAIS shifted LEVEL (SMB, `ais_c`) and left the SHAPE exactly where L28 had it, because no
  direction in its parameter space produces the acceleration. The binding term is the linear discharge response, measured from
  both sides (ρ free absorbs it; ρ capped can neither absorb nor fit it). **L29 is a diagnostic arm, not a candidate posterior**
  (a truncated noise prior is not a shippable modelling choice, and it moves nothing the paper reports).

## 4. Receipts (in git unless noted)
`outputs/bench_ladrillo_L29.{md,csv}`, `diag_imbie2026_vs_targets{,_windows,_anchors}_L29.csv` (+ `figures/…_L29.png`),
`diag_ais_flux_split_vs_imbie{,_draws}_L29.csv`, `diag_refit_precision_L27_L28_L29.csv`, `diag_ais_tipped_share_L27_L28_L29.csv`
(+ `_draws_`), `ladrillo_prior_posterior_L29.{csv,md}`, `ladrillo_priors_L29.csv` (the rho_ais row reads 0.90),
`ladrillo_model_comparison_L29{,_spread}.csv`, `postpred_L29_{components_timeseries,bias,coverage}.csv`,
`ssps_components_2300_L29*.csv`, `mcmc/slr_convergence_L29.csv`, `data/MimiBRICK/parameters_subsample_brick_mengel_L29.csv`.
NOT in git: the four chains, `adapted_cov_L29*.csv`, the logs (`outputs/log_L29.txt`, `outputs/mcmc/log_L29_seed*.txt`,
`outputs/log_diag_ais_tipped_share.txt`).

## 5. ⚠ NON-OBVIOUS STATE / TRAPS
- **`bench_ladrillo_L29.md`'s "L27*" rows are scored on the OLD target** — compare L29 to `bench_ladrillo_L28.md`'s rows, never to
  L27*. (Same for any future tag until the champion is re-frozen on the IMBIE target.)
- **`diag_imbie2026_vs_targets.py` reads the POSTERIOR PREDICTIVE** (`postpred_<tag>_components_timeseries.csv`, AR(1) noise seed
  2026), not the model-only series; the model-only per-draw p50 is `ais_cm_p50` in the flux-split file. They agreed on every
  window here — but read the flux split whenever the NOISE MODEL is the thing being changed.
- **Julia's stdout is BUFFERED to the per-chain logs**: the cap banner / repair line / logpost(θ₀) appear only when a chain EXITS.
  Verify a launched arm's configuration with a short smoke run of the same flags, not by grepping a live chain's log.
- **`pgrep -fl "julia.*calibrate_mcmc_ext"` from inside a Claude Bash call lists the CALLING shell too** (its command line contains
  the pattern) — count the julia PIDs. `pgrep -f "calibrate_mcmc_ext.jl 2000000"` matches nothing (juliaup's path precedes the
  script). Best: wait on the runner PID.
- **A bound mutation the chain never visits returns byte-identity** — see §2. Size a truncation mutation off the reference
  trajectory's actual range.
- On a bimodal projection tail, quote the tipped share (`diag_ais_tipped_share.jl`), never the bare p95; the benchmark already
  marks such cells N/A(bimodal) but the components CSV does not.
- Smoke/mutation artefacts (`*smokeL29*`, `*gate300mut*`, `*smk_*`, `*gatebad*`) were deleted from `outputs/mcmc/`; the gate's
  own `*gate300*` files are the standing ones.
- `outputs/ladrillo_priors_L24.csv`, `outputs/mcmc/seed_diag_L24_seed2026.txt`, `outputs/vv_responsiveness_L24.csv` show as
  MODIFIED in the tree from before this session (the identity gate does not write them); left alone, not mine to resolve.
- The deliverables `.docx` reviews and `deliverables/redline/unpacked/` are untracked by convention; unchanged this session.
