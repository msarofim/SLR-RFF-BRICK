# Handoff — the additional discharge response built, refitted (L30) and NOT TAKEN by the likelihood; the objective scores LEVELS, not rates (09-22 06:20 → 12:00)

**Start here.** Self-contained for the ramp arc; continues `handoff_2026-09-22_L29_rho_cap_landed.md` (the ρ-cap arm; its §5 traps
all still stand) and does not supersede it — L28/L29 remain the controls this arm is read against. Records: CHANGELOG **09-22b**
(the exponent algebra), **09-22c** (the onset sweep), **09-22d** (the build + launch) and **09-22e** (the result + the likelihood
profile); scoping note `notes/scoping_2026-09-21_dais_structure_vs_imbie2026.md` **§6, §7, the §6/§7 erratum, §8**. Commits
`1160ff2`, `333c9fb`, `664816c`, `41f488b`, `014d2c5`, `57e938e`, `d9b24a4`, `1ad6c2c` on `ladrillo-dev`, all pushed. Memory:
`dais_toc_exponent_is_inert`, `dais_onset_ramp_reaches_imbie`, `dais_additional_discharge_response`,
`objective_scores_levels_not_rates` (new); **`INDEX_ais.md` was SPLIT** at 18,591 B → `INDEX_ais_imbie.md` (15,954 / 4,236),
registered in `MEMORY.md`.

## 0. STATE AT HANDOFF (2026-09-22 ~12:00)
- **Champion and the paper's posterior are STILL L27**; draft r9 (`deliverables/GMD.Ladrillo.v1_review-2026-09-21c_L27.docx`);
  `champions.json` untouched; comment #12 (code availability) still open. L28, L29 and L30 have all landed; **none promoted**.
- **Nothing is running.** The L30 chains (8 GB) are in `outputs/mcmc/`, not in git. The four `run_dispersed_multistart.R`
  processes are the CCX session's.
- **The calibration target is unchanged**: IMBIE 2026, `outputs/recalib_targets_ext.csv` md5 `eb768cd9…`, asserted by every runner.
- Torch verdict was said out loud before launch: Mac (4 chains, 2 h 48 min wall under a load of ~3).

## 1. ⭐ NEXT — the open ruling is METHODOLOGICAL and it is Marcus's
The arc has answered the question it was built to answer and the next move is a CHOICE, not a debugging step:

1. **Put a RATE/window term in the likelihood?** §7's sweep showed a ramp reproduces IMBIE's four pre-pause window RATES; §5's
   profile showed the SHIPPED objective — which scores the LEVEL series under AR(1) (ρ ≈ 0.97) plus a 100-yr-correlated
   observational ε — pays almost nothing for that shape. The two scoring rules disagree, and the refit follows the objective.
   Making Ladrillo honour the reconciled record's ACCELERATION means changing **what the model is fitted to**. Scope before
   building: which windows, whose σ (IMBIE's own window bars), whether the term REPLACES or SUPPLEMENTS the level likelihood
   (double-counting the same data if it supplements), and what it does to the OTHER components' balance in the joint fit.
2. **L31 = L30 + `--rho-max=ais:0.90`?** ~4 h Mac, one axis vs L30, recipe identical to `run_L30.sh` + the flag. ⚠ **The profile
   already predicts the answer**: at ρ = 0.90 the best ramp cell gains ~1.2 log-units at s ≈ 1e-4 with an EARLY onset (0.45 K).
   So L31 would land a small, identified ramp — worth running only to put that on the record, not to change the picture.
3. **Which posterior the paper ships** — unchanged by L30: L27 (old target, consistent draft) vs L28 (new target, level not
   shape) vs post-structure. Do NOT swap the draft to L28/L29/L30 as is. If L28: the 14 vv MAGICC-climate arms (FIG 11 /
   regrowth attribution) are still unrun (~1 h) and the benchmark's L27* rows must be re-scored on the IMBIE target first.
4. The 09-16 list: venue (GMD), package extraction for Tony's team, `facts` remote, FACTS/MAGICC scope, pulse analysis.

## 2. WHAT WAS SCOPED FIRST, AND WHY IT SAVED A REFIT (09-22b, scoping §6)
The candidate the 09-22 handoff named — a free exponent n on DAIS's ocean-temperature ratio r, nesting DAIS at n = 2, prior
[1, 4] — is **inert on the historical range**, by algebra, in minutes. At the L29 posterior ANTO map `r = 0.931 + 0.1016·GMST`,
a **5.7 % span** across the window the record doubles over. On the record's own statistic (loss per K, secant; IMBIE 0.45 → 1.02 K
= 2.02×): n = 2 → 1.03×, n = 4 → 1.10×, n = 8 → 1.25×; the doubling needs **n ≈ 20** (≈ 6 only at ANTO's prior corner), which is
an exponential with e-folding 0.45 K and a 113× speed factor at 4 K. A [1, 4] prior would have produced a NO-POWER refit.
⚠ **§6's "the record has a kink at ~0.5 K" was wrong and is retracted in place** (the §6/§7 erratum): the early leg was
Frederikse NET loss and the late leg IMBIE DYNAMICS — two products, two quantities. On IMBIE 1979–2023 alone the dynamics
anomaly is LINEAR in GMST (−232 Gt/yr K⁻¹, residual sd 22, zero-crossing ~+0.15 K). **There is no kink in the record.**

## 3. THE FIXED-PARAMETER SWEEP (09-22c, scoping §7) — `julia/scope_ais_onset_sweep.jl`
295 L29 draws, 22 arms, hindcast + 3 SSPs, **90 s**. The magdep component's fast-dynamics term as a LINEAR RAMP (n_fd = 1,
ref 1 K), onset swept in GLOBAL warming and mapped per draw through its own amp. `stock` reproduces L29 (2011–17 0.0411 vs 0.0418).
- **on 0.75 K / s 6e-4** put all four pre-pause windows inside ±0.5σ at once (z +0.20 / +0.04 / −0.17 / −0.08; Σz² 0.1 vs stock's
  4.9) with the acceleration-window dynamics anomaly at −109 (IMBIE −106). on 0.60 / 3e-4 is nearly as good.
- Costs at fixed parameters: cumulative +1.4–1.7σ (level, unrefit) and the 2018–23 pause +2.2–2.7σ (a monotone ramp cannot pause).
- Projections: the ramp's own share is moderate (+6 / +30 cm SSP2-4.5 2100 / 2300); the big high-forcing move in the sweep was
  the REMOVAL of the paleo binary (the component holds one term), which is why Marcus ruled COEXIST.
⚠ **This is the arm that misled me.** It scores window RATES. See §5.

## 4. WHAT WAS BUILT (09-22d) — and it is all still in place
- **Component** (`julia/antarctic_icesheet_magdep_component.jl`): `ramp = ais_ramp_slope · max(T_ant − ais_ramp_threshold, 0) ·
  24.78e15/57`, ADDED to the fast-dynamics rate and floored JOINTLY with it; `slope == 0.0` is a LITERAL skip. New variable
  `ramp_rate`. The paleo binary keeps its stock meaning (fastdyn n = 0) — the two terms COEXIST.
- **Calibrator `--ais-ramp`**: samples `ais_ramp_gon` (onset in GLOBAL warming, flat [0.30, 1.20] K — the top is above the
  driver's 2011–17 mean of 1.03 K so "no onset in range" is reachable) and `ais_ramp_log10s` (flat, s 0.5–20·10⁻⁴ m SLE yr⁻¹ K⁻¹),
  and DERIVES `T_ramp = AIS_TANT0 + amp·G_on` per draw. The ramp pair is the ONE exemption from the starts-file
  cover-the-parameter-set guard, and its start is **over-dispersed by start row** — (0.45, 1.5e-4), (0.60, 3e-4), (0.75, 6e-4),
  (0.95, 12e-4) — so R̂ on the new dimensions measures mixing, not the start.
- **Projection kernel**: `ladrillo_ramp_posterior(path)` reads the flag off the posterior's own columns; `ladrillo_setup(…;
  ais_ramp=)` builds the slot; `ladrillo_apply_draw!` derives the same map and checks BOTH ways.
- **Gates**: `scripts/gate_calibrator_identity.sh` PASS with the flag absent (re-run after the start edit); new
  `scripts/gate_ais_ramp_inert.jl` — bit-identical to stock at slope 0 on 25 draws (19 of which tip the binary), MUTATION at
  6e-4 moves AIS 48.3 cm; `julia/test_ladrillo_projection.jl` ALL PASS.
- **Runners**: `run_L30.sh` (chains + everything) and `run_L30_stage2.sh` (postprocess + diagnostics only, chains on disk).
  L30 is declared in both figure `TAG_DESC` guards.

## 5. ⭐⭐ THE RESULT (09-22e) — the likelihood did not take the term, and the profile says why
**Refit**: chains 07:14 → 10:02, acceptance 0.247, noise gate PASS, SLR R̂ fine. **The pre-registered success line FAILS** on
two of its four clauses:

| | L28 | L29 | **L30** | IMBIE |
|---|---|---|---|---|
| 2011–17 rate (z) | 0.0387 (−2.10) | 0.0416 (−1.79) | **0.0382 (−2.14)** | 0.0556 |
| 1992–2002 (z) | 0.0209 (−0.19) | 0.0221 (+0.01) | 0.0207 (−0.22) | 0.0220 |
| cumulative 1979–2023 (z) | 1.226 (−0.76) | 1.300 (−0.21) | 1.220 (−0.77) | 1.328 |
| dyn anomaly, accel window | −52.4 | −49.8 | **−53.6** | −106 |
| `rho_ais` p50 | 0.966 | 0.885 | **0.966** | — |
| AIS 2300 SSP2-4.5 / 5-8.5 | 165.7 / 271.1 | 167.6 / 277.3 | **165.8 / 276.0** | — |

`ais_ramp_log10s` p50 −3.92…−4.08 (s ≈ 0.8–1.2·10⁻⁴) with p05 ON the prior floor; `ais_ramp_gon` spans essentially its whole
prior in all four chains (medians 0.50 / 0.74 / 0.74 / 1.04 — still their over-dispersed starts). Every Antarctic parameter
within **0.20 L28-sd** (`diag_refit_precision_L28_L29_L30`); tipped share (AIS@2100 > 15 cm) SSP1-2.6 7.60 → **6.20 %**,
SSP2-4.5 41.6 → 40.75 %.

**The profile** (`julia/diag_ais_ramp_likelihood_profile.jl`, NEW; 20 L30 draws, ramp overridden on a grid, the calibrator's own
`hetero_logl_ar1(model − obs, sd_ais, ρ, ε, L=100)` on the IMBIE target 1900–2026). AIS log-likelihood GAIN over no ramp, at
G_on 0.45 (the best onset at every ρ; later onsets are worse):

| ρ | 0.5e-4 | 1e-4 | 2e-4 | 3e-4 | 6e-4 |
|---|---|---|---|---|---|
| **0.966** (L30's own) | +0.12 | −0.30 | −2.73 | −7.29 | −33.8 |
| 0.90 (the L29 cap) | +0.92 | **+1.17** | −0.38 | −4.62 | −33.6 |
| 0.80 | +1.85 | **+2.91** | +2.63 | −0.84 | −30.4 |
| 0.60 | +2.70 | +4.50 | **+5.43** | +2.79 | −26.6 |

⭐ **At the posterior's own ρ every ramp setting LOSES.** Lowering ρ makes a ramp worth taking (the L28 persistence mechanism,
confirmed from a third side) but only ≤ 5.4 log-units even at ρ = 0.60, and the preferred cell is **1–2·10⁻⁴ at the earliest
onset**, not the sweep's 3–6·10⁻⁴ at 0.60–0.75 K. **L30's chains did exactly what the objective asks.** The objective scores the
LEVEL series, where AR(1) at ρ ≈ 0.97 plus a 100-yr-correlated ε makes a smooth drift nearly free and a level OVERSHOOT
expensive (at 0.75 K / 6e-4 the cumulative runs 1.16 → 1.44 against IMBIE's 1.33). ⇒ memory `objective_scores_levels_not_rates`.

## 6. THE EVIDENCE REVIEW BEHIND THE RULING (scoping §8)
- **Acceleration: strong. Instability: not supported by our data.** IMBIE's dynamics anomaly is WAIS-only, 84 % of the loss, and
  linear in GMST with no lag — a forced-response signature. External lines (Mouginot 2014, Rignot 2019/2014, Joughin 2014 — a
  MODEL statement; against: Jenkins 2018 / Holland 2019 on decadal wind-driven Amundsen forcing) are RECALLED, NOT VERIFIED here.
  **Cite from the papers, never from this note.**
- **The 2020–23 "stabilisation" is SMB**: net loss −200 → −104 Gt/yr while the dynamics anomaly went −179 → −249; the difference
  is +144 Gt/yr of record EAIS snowfall (~3σ on an interannual sd of 123). The NBC coverage of Otosaka et al. (Sci Data 13:1301)
  quotes the authors to the same effect and says the acceleration resumed after 2023.
- **Coexist, not replace** (Marcus): replace discards the LIG constraint above 1.2 K and moves the paper's tail by removing a
  prior. A replace arm stays available as L30b (needs no new code — drop the paleo binary from the L30 configuration).
- **The term is named "the additional discharge response"** in code, outputs and prose, deliberately. A fit cannot make a
  mechanism claim.

## 7. Receipts (in git unless noted)
`outputs/scope_ais_onset_sweep_{hindcast,hindcast_draws,proj}_L29.csv`; `outputs/diag_ais_ramp_likelihood_profile_L30.csv`;
`bench_ladrillo_L30.{md,csv}`, `diag_imbie2026_vs_targets{,_windows,_anchors}_L30.csv`,
`diag_ais_flux_split_vs_imbie{,_draws}_L30.csv`, `diag_refit_precision_L28_L29_L30.csv`,
`diag_ais_tipped_share_L28_L29_L30.csv` (+ `_draws_`), `ladrillo_prior_posterior_L30.{csv,md}`, `ladrillo_priors_L30.csv`
(the two ramp rows read flat [0.3, 1.2] and [−4.3, −2.7]), `ladrillo_model_comparison_L30{,_spread}.csv`,
`postpred_L30_{components_timeseries,bias,coverage}.csv`, `ssps_components_2300_L30*.csv`,
`scope_slr_fairunc_*_L30_*.csv`, `mcmc/slr_convergence_L30.csv`,
`data/MimiBRICK/parameters_subsample_brick_mengel_L30.csv`.
NOT in git: the four chains, `adapted_cov_L30*.csv`, the logs (`outputs/log_L30.txt`, `outputs/log_L30_stage2.txt`,
`outputs/mcmc/log_L30_seed*.txt`, `outputs/log_scope_ais_onset_sweep_L29.txt`).

## 8. ⚠ NON-OBVIOUS STATE / TRAPS (the 09-22 handoff's §5 still applies IN FULL)
- ⛔ **A WINDOW-RATE improvement is NOT evidence the objective will take a term.** Profile the objective's own likelihood first —
  minutes against a 4-h refit, and it would have predicted L30 exactly. This is the session's main lesson.
- ⚠ **A refit that adds FLAT priors is NOT logpost-comparable to its parent**: each σ = 1e3 prior subtracts log(10³√2π) ≈ 7.8, so
  L30's 801–805 against L28's 820–822 is −15.6 of bookkeeping on an unchanged likelihood. Compare on the LIKELIHOOD.
- ⚠ **`tr … | grep -q` under `set -o pipefail` reports FAILURE ON A MATCH** — grep exits early, `tr` takes SIGPIPE, pipefail
  takes the nonzero. It printed false "ramp NOT announced" alarms for seeds 2027/2029 whose banners were both present. Count
  matches (`grep -ac … ) -gt 0`) instead; fixed in `run_L30.sh`, and the same form may lurk in older runners.
- ⚠ **A new component parameter must be threaded through EVERY pipeline consumer**, not just the obvious four. The first stage-2
  run died at its FIRST step because `diag_slr_convergence_by_chain_ladrillo.jl` built a stock AIS slot and the apply-draw guard
  refused the draw (the guard working as designed); postprocess then declined to write a subsample and EVERY later step failed on
  the missing posterior. Fixed there and in `scope_slr_fair_uncertainty.jl`; **other `ladrillo_setup` callers (≈ 45 scripts) will
  error loudly, not silently, if pointed at an L30 posterior** — that is the guard, not a bug, but budget for it.
- ⚠ `ladrillo_prior_posterior_table.py`'s BLOCKS gate now DROPS names a tag's prior file lacks (so the ramp pair is inert for
  pre-L30 tags) but still fails on a parameter present-and-undescribed. Do not relax the second direction.
- ⚠ In `diag_ais_ramp_likelihood_profile.jl` the per-cell override MUTATES the loaded posterior frame in memory (DataFrameRow
  assignment writes through to the parent). Harmless there — every cell is overwritten — but do not copy that idiom into a
  script that later reads the untouched draw.
- ⚠ `for gon in G_ON, s in SLOPE` is ONE loop in Julia: a `break` inside leaves BOTH. The first profile run wrote a single row
  that way and printed empty tables rather than failing.
- ⚠ The likelihood in the profile script is a 12-line RE-IMPLEMENTATION of `hetero_logl_ar1` (the calibrator runs a chain on
  load, so it cannot be imported). Differences BETWEEN ramp settings are exact; the LEVEL is not the logpost, and the other
  components/priors are absent by design. If the calibrator's noise model changes, that copy must follow.
- `outputs/ladrillo_priors_L24.csv`, `outputs/mcmc/seed_diag_L24_seed2026.txt`, `outputs/vv_responsiveness_L24.csv` still show as
  MODIFIED in the tree from an earlier session; left alone, not mine to resolve.
- Memory: **`INDEX_ais.md` was split** — the IMBIE-2026 / DAIS-structure arc is now `INDEX_ais_imbie.md`. Straddlers are named in
  its header (the amp threshold, the λ prior's worth vs the cost of replacing it, `ais_lambda_rests_on_lig`).
