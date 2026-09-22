# Handoff — L29 (ρ-cap) landed: the cap bound, the physics did not move; DAIS has no direction that produces the acceleration (09-22 00:00 → 01:20)

**Start here.** Continues `handoff_2026-09-21c_L29_rho_cap_launched.md` and `handoff_2026-09-21b_imbie2026_L28.md` (their traps
stand). CHANGELOG **09-22a** is the record; scoping note **§5** the argument; memory `dais_structure_not_warranted_by_imbie2026`
revised in place (second time), `INDEX_ais` one-liner (now 16.7 KB — over soft, under hard).

**STATE AT HANDOFF (2026-09-22 ~01:20):**
- **Champion and the paper's posterior are STILL L27**; draft r9; champions.json untouched. L28 and L29 landed, neither promoted.
- **L29 = L28 + `--rho-max=ais:0.90`**: complete through stage 2 (no paper arms). Chains (8 GB) on disk, not in git. Nothing running.
- **Result in one line:** the cap BOUND (`rho_ais` 0.966 → 0.885, ~2–7 log-units) and every Antarctic parameter stayed within 0.1
  L28-sd; the fit shifted level slightly (2011–17 rate 0.039 → 0.042 vs IMBIE 0.056, via SMB) and the acceleration-window
  discharge anomaly stayed at −52 Gt/yr (IMBIE −106). Neither pre-registered branch; the binding term is DAIS's linear discharge
  response, now measured from both sides. L29 is a diagnostic arm, not a candidate posterior.
- ⚠ L29's SSP1-2.6 p95 (30 → 17 cm) is the tipped SHARE crossing 5 % (7.6 → 5.25 %), not sensitivity — `diag_ais_tipped_share.jl`.

## 1. ⭐ NEXT (Marcus's rulings, in order)
1. **The steepening build?** §4 candidate 1: a free exponent on DAIS's ocean-temperature ratio (nests DAIS at 2; one parameter; a
   curvature, not a claim) — vs a fast-dynamics onset inside the observed range (a scientific claim with large projection
   consequences). L29 says the current parameter space cannot produce the acceleration, so this is now the only route to the
   record's shape. Scope before building: which DAIS term, its prior, its identity-gate treatment (a default that nests exactly),
   and the pre-registered success line (2011–17 rate within 1σ of 0.056 WITHOUT the early century worsening past −1.9σ).
2. **Which posterior the paper ships** — unchanged by L29: L27 (old target, consistent draft) vs L28 (new target, level not shape)
   vs post-structure. Do not swap the draft to L28 or L29 as is.
3. The 09-16 list: venue (GMD), package extraction for Tony's team, `facts` remote, FACTS/MAGICC scope, pulse analysis.

## 2. Receipts (all in git unless noted)
`outputs/bench_ladrillo_L29.{md,csv}`, `diag_imbie2026_vs_targets{,_windows,_anchors}_L29.csv`, `diag_ais_flux_split_vs_imbie{,_draws}_L29.csv`,
`diag_refit_precision_L27_L28_L29.csv`, `diag_ais_tipped_share_L27_L28_L29.csv` (+ `_draws_`), `ladrillo_prior_posterior_L29.{csv,md}`,
`ladrillo_priors_L29.csv` (rho_ais row reads 0.90), `postpred_L29_*`, `ssps_components_2300_L29*.csv`, `mcmc/slr_convergence_L29.csv`,
`data/MimiBRICK/parameters_subsample_brick_mengel_L29.csv`. Logs: `outputs/log_L29.txt`, `outputs/mcmc/log_L29_seed*.txt`.

## 3. ⚠ TRAPS (adds to the earlier notes)
- `bench_ladrillo_L29.md`'s "L27*" rows are scored on the OLD target — compare L29 to L28's rows (`bench_ladrillo_L28.md`), never to L27*.
- `diag_imbie2026_vs_targets.py` reads the POSTERIOR PREDICTIVE (`postpred_<tag>_components_timeseries.csv`, AR(1) noise seed 2026);
  the model-only per-draw series is in the flux-split file (`ais_cm_p50`). They agreed on every window here, but read the
  flux split when the noise model is the thing being changed.
- On a bimodal tail a p95 is a step function of the tipped share; quote the share (`diag_ais_tipped_share.jl --tags=... --gap=15`).
- `outputs/ladrillo_priors_L24.csv`, `seed_diag_L24_seed2026.txt`, `vv_responsiveness_L24.csv` still show as modified from before
  this session; left alone.
