# Changelog

All notable changes to this project. Older history reconstructed from the
commit log; recent entries are explicit.

## [unreleased] — 2026-07-22 (late) — switch scenario diagnostic to the SECANT ratio; a ≈ 1.08

- `diag_pai_cmip6_time.py` reworked from the 41-yr windowed MARGINAL trend ratio to the
  **secant (level) ratio** R = (T_AIS−T_AIS,PI)/(T_glob−T_glob,PI), 30-yr running means,
  pre-1950 dropped (Marcus's request — the secant is what BRICK `a` actually is, so no
  marginal→level integration needed).
- **RESULT: the direct secant is ≈1.06–1.10 at crossing-relevant warming (2.5–3.5 K) and
  nearly FLAT across 2–5 K** (ssp245/ssp585 collapse). This CORRECTS the earlier
  integrated-marginal estimate of 0.97–1.03, which was biased ~0.1 low by a too-low
  extrapolated ΔT→0 intercept. The corrected secant now AGREES with the DECK 1pctCO2
  GHG-only secant (1.07–1.13), so the previously-claimed ~0.08 "aerosol suppression gap"
  was an artifact and is retracted.
- **A6 note consequences:** proposal A center moved 1.00 → **1.08** (`a ~ N(1.08, 0.15)`,
  equilibrium 1.196 now at +0.7σ); the "Level vs marginal slope" section deleted (moot);
  proposal B's marginal amp(ΔT) exponential replaced by the DECK two-mode map
  T_ant−T_ant,PI ≈ 1.08·ΔT_fast + 1.70·ΔT_slow; Figure 1 + captions synced. PDF re-rendered.

## [unreleased] — 2026-07-22 (evening) — DECK 1pctCO2/abrupt-4xCO2: the time component IS real

- `python/reduce_cmip6_tas_pai_deck.py` + `python/diag_pai_deck.py`: 41 models, GHG-only
  (aerosols/ozone at piControl — the confound-free test), anomalies rel. piControl mean.
- **At matched warming (2.5–4.5 K), amplification depends on forcing AGE**: abrupt-4xCO2
  reaches those levels ~6–22 yr after forcing (level ratio 0.93–1.11); 1pctCO2 takes
  ~100–124 yr (1.07–1.13). Paired D = −0.13…−0.08, bootstrap CIs exclude zero. The
  scenario-based null was an estimator-power result, not absence: cross-SSP forcing-age
  contrasts are ~10× smaller than the DECK contrast.
- **abrupt R(t) climbs 0.95 → ~1.2 over ~100 yr and asymptotes at 1.23 [IQR 1.11–1.45]**
  ≈ the DAIS equilibrium 1.196 (n=2 runs to 300 yr hint slightly higher). Gregory
  fast/slow-mode slopes: 1.08 / 1.70 — the slow (deep Southern Ocean) mode is strongly
  polar-amplified and drags the ratio up with time.
- Interpretation: along century-scale ramps, level and forcing-age co-vary, so the
  scenario amp(ΔT) closure silently absorbs the time dependence (fine for ramp-like
  futures); it would misextrapolate under stabilization (amp keeps rising while ΔT
  stalls) — relevant to post-2100/2150 horizons. 1pct GHG-only level ratio at 2.5–3.5 K
  (~1.07–1.13) sits ~0.08 above the scenario-based secant (0.97–1.03), consistent with
  ozone/aerosol suppression baked into real-world trajectories.

## [unreleased] — 2026-07-22 (later) — 5-scenario level-vs-rate test: NO identifiable rate component

- Added ssp119/ssp126/ssp370 to the PAI reduction (`python/reduce_cmip6_tas_pai_ext.py`,
  same members as the base pull; `data/cmip6_pai/tas_series_ext_*.csv`) and a level+rate
  decomposition (`python/diag_pai_cmip6_rate.py`): matched-warming table + joint fit
  pai = 1.196 − (1.196−a0)exp(−dT/Ts) − c·rate on the 32-model common subset.
- **RESULT: the rate/time component is NOT identified** — c = −0.50 [−0.91, +0.11]
  per (K/decade), CI spans zero, sign driven entirely by ssp126's degenerate stabilized
  windows; with the three well-behaved scenarios (245/370/585, rates 0.25–0.5 K/dec) the
  residuals from the level-only fit are flat in rate. The ssp245>ssp585 crossover at
  2.5–3 K that motivated the test is NOT corroborated as a rate effect (ssp370, nearly as
  fast as 585, sits with 245).
- Two contaminations diagnosed and filtered (named constants): ozone-hole/aerosol-era
  windows (centres <2005; median Antarctic trend negative under non-GHG forcing) and
  stabilized windows (global trend <0.10 K/dec; trend-ratio estimator degenerates +
  ozone-recovery confound — visually obvious for ssp119/126 post-2040).
- Conclusion: the level-dependent amp(ΔT) form stands as the supported parsimonious
  model; a genuine time/rate test needs idealized runs (1pctCO2 vs abrupt-4xCO2) or a
  single-model large ensemble, which remove the composition confound.
- **SSP3-7.0 subsequently EXCLUDED from the analysis** (Marcus: it is the aerosol
  outlier; SH forcing-mix confound). Rerun on the 33-model {126,245,585} subset:
  conclusion unchanged — c = −0.64 [−1.06, +0.07], matched-warming flat at 2.0–2.5 K
  (245 1.13 vs 585 1.14 @2.5 K); the crossover survives only in the 3.0 K bin. The A6
  note gained §4 (multi-scenario test) + Figure 2 and was re-rendered to PDF.

## [unreleased] — 2026-07-22 — PAI-vs-time diagnostic (CMIP6): amp rises with warming; A6 prior reference-frame flag

- **New `python/reduce_cmip6_tas_pai.py`** (streams Amon tas for 35 models from the public
  Pangeo/GCS zarr archive; annual global + AIS-proxy means to `data/cmip6_pai/`, 780 KB total)
  and **`python/diag_pai_cmip6_time.py`** (windowed 41-yr trend-ratio PAI1, Xie-2022 gate,
  collapse test) + **`python/diag_pai_mask_sensitivity.py`**.
- **RESULT (34 models, land≥50% south of 60°S):** within-scenario PAI1 RISES in both SSP2-4.5
  (+0.035/decade; median 1.06→1.19) and SSP5-8.5 (+0.016/decade; 1.13→1.19), and the two
  scenarios roughly COLLAPSE onto one curve in global warming level: ~0.9 at ΔT≈0.7 K rising
  to ~1.15–1.2 by ΔT≈2 K, then flattening at ≈ the DAIS equilibrium value 1.196. Supports a
  warming-level-dependent GMST→AIS amplification interpolating transient→equilibrium.
- **MASK FINDING (A6 flag):** our land-only AIS metric gives full-window (2015–2100) PAI1
  1.13/1.16 (ssp245/585) — Xie et al. 2022's 0.95/1.03 is instead reproduced by the ALL-points
  polar-cap mask (6-model test: cap60 0.92/0.98). Xie's "AIS" metric is cap-like; DAIS's
  temperature lineage (ice-core/continent) argues for the land-referenced number, so the A6
  transient prior N(0.95, 0.10) may sit ~0.15 low in DAIS's reference frame — which would
  overstate the transient-vs-equilibrium contrast and part of the phase-2 76→40 cm drop.
  Flagged for the M5/A6 revisit; NOT resolved here.

## [unreleased] — 2026-07-21 — artifact pulse-MEAN column (sub-annual) + BRICK-FM write-up

- **New `julia/diag_subannual_pulse_means.jl`**: full-ensemble 10-GtCO₂ pulse means under the
  temporary sub-annual DAIS-crossing depot patch (applied for the run, restored after), both
  calibrations × both drivers → `outputs/crossmodel_pulse_means_subannual.csv`. Also writes the
  equilib posterior subsample `data/MimiBRICK/parameters_subsample_brick_mengel_extA6eq.csv`
  once (10k rows, loadpost-identical thinning of the 4 extA6eq chains; untracked like its
  siblings) so equilib runs are prefix-reproducible.
- **RESULTS** (×10⁻³ cm/GtCO₂, [MAGICC, FaIR]): transient mean @2100 [15.9, 12.1], @2150
  [29.1, 22.9]; equilib @2100 [22.8, 21.0], @2150 [34.7, 31.8]. Cross-checks: levels move <1%
  under the patch, transient medians +6–15% — but **equilibrium medians rise 2–4×** (@2100
  MAGICC 5.4→22.6): most equilib draws are already tipped, so the previously-quantized
  tip-advance channel reaches the median draw, not just the tail. Raises the stakes of the
  pending sub-annual-integrator adoption decision (M2).
- **`notes/writeup_2026-07-21_brick_fm_vs_wong_brick.md`**: BRICK-FM vs the original Tony Wong
  BRICK — structure (Mengel glacier), interface (external forcing, precip_log, LWS lock),
  calibration (phase-1/phase-2 A2/A4/A5/A6/geometry/obs), results deltas, pending integrator
  decision, provenance table.
- Cross-model artifact republished with the pulse-mean column (snapshot + details in
  FaIRtoFrEDI `magicc_comparison/artifacts/`).

## [unreleased] — 2026-07-20 (later) — phase-2 production run DONE + accepted; A6 sensitivity running

- **Two-stage launch executed.** Tuning chain (1M, acceptance 0.237) → built
  `overdispersed_starts.csv` + 39-param `adapted_cov_ext.csv` → **4×2M over-dispersed
  production run** (acceptance 0.234–0.237, ~3 h). All phase-2 terms confirmed working in the
  tuning posterior: SMB β_total→1860 Gt/yr (target 1863); amp 1.195→0.944; T_on sd 0.1;
  λ/γ/κ sampling paleo.
- **Production converged on the deliverable + accepted:** SLR@2100 R̂ **1.006**, SLR@2150 R̂
  **1.008** (10 param marginals still fail — the ridge). `postprocess_mcmc_ext.jl --accept-slr`
  wrote the canonical phase-2 `parameters_subsample_brick_mengel_ext.csv` (10k of 4M draws).
- **HEADLINE (SSP2-4.5, rel 1995–2014):** SLR@2100 median **39.7 cm** [36.9–75.0]
  (v-next 76.1), @2150 **62.8 cm** [55.7–153.5] (159.1). Threshold crossing ~82%→~29%.
  Production medians match the tuning preview (39.9/63.0) — robust. Moves BRICK-Mengel from
  above-AR6 to ~AR6-central for SSP2-4.5. Key params cooled: ais_ocean_temperature₀ 0.862
  (base 0.981), anto_alpha 0.296 (0.405).
- **A6-equilibrium sensitivity RUNNING** (`run_A6eq_sensitivity.sh`, amp pinned 1.196, infix
  `extA6eq`, ~3.7 h) to isolate A6's share of the headline drop (Marcus-approved attribution).
- **M2 downstream REFRAMED — NOT a mechanical repoint.** 12 drivers read the June-13
  `parameters_subsample_brick_mengel.csv` (incl. the pulse/MAGICC-vs-FaIR pipeline). Repointing
  to phase-2 halves the SLR-based pulse results, mostly via A6 (judgment-call σ). Gated on the
  A6 attribution + Marcus's decision on which posterior the pulse paper adopts. Held.

## [unreleased] — 2026-07-20 — phase-2 begun: M1 accept, Dangendorf/Frederikse untangle, A2/A4/A5/A6 wired

Phase-2 kickoff (Marcus decisions 2026-07-19/20). Nothing launched yet — the phase-2
recalibration awaits Marcus sign-off on the pinned numbers (see the pre-run summary /
handoff §5). What landed this session:

### M1 — accept the v-next posterior on the deliverable (DONE)
- Added `--accept-slr` to `postprocess_mcmc_ext.jl`: writes the canonical (no-suffix)
  subsample + proposal seed iff `outputs/mcmc/slr_convergence_ext.csv` (now emitted by
  `diag_slr_convergence_by_chain.jl`) shows SLR R̂<1.05 at all horizons AND is fresher than
  every chain file. Regenerated `parameters_subsample_brick_mengel_ext.csv` (canonical) +
  `README_brick_mengel_ext_acceptance.md`. Downstream drivers deliberately NOT repointed yet
  (done once, at the phase-2 posterior, with the M2 pulse rerun).
- Fixed a stray-chain trap: a 2-iteration smoke chain (`chain_ext_seed2026_n2.csv`) matched
  the `chain_ext_seed*` glob and had (1) collapsed the marginal diagnostic to 1 draw/chain,
  (2) leaked one smoke draw into row 1 of the prior subsample. Quarantined
  (`outputs/quarantine/20260720_smoke_chain_n2/`); postprocess now errors loudly on a
  chain-length mismatch (shortest < ½ longest). **This means the handoff's marginal numbers
  (worst R̂ 1.458) always came from the four full chains — the 18:22 "certification" was the
  degenerate 1-draw read, now confirmed.**

### Dangendorf / Frederikse — two-layer data bug untangled (A3 + M3 pre-check)
- `data/observations/dangendorf_2024_gmsl.csv` was **Frederikse 2020's own observed GMSL**
  (bit-identical). Renamed → `frederikse2020_gmsl_total.csv`; relabeled the active pipeline
  (`prep_recalib_targets_ext.py`, `apply_wong_weights.py`, `hawkins_sutton.py`,
  `julia/compute_lB_per_post.jl` — the "Dangendorf importance weights" were FREDERIKSE
  weights; `dangendorf` kept as a deprecated alias that warns).
- Fetched the **real Dangendorf 2024** (Zenodo 10621070). Its `KalmanSmootherHR_Global.nc`
  is mis-written upstream (the "GMSLHR" slot holds the BARYSTATIC mean — proved: cos-weighted
  mean of the Fields-nc `Bary` reproduces it to 0.000 mm). True GMSL = cos-lat-weighted mean
  of the `HR` field (`Fields.nc`), per the record's own `Master_Final.m`; validated vs the
  paper (1900–2021 1.52 vs 1.5±0.19; 1993–2021 3.17 vs 3.4±0.42 mm/yr). Extracted →
  `dangendorf2024_gmsl_annual.csv`. **SE unattributable (same slot-shift) — resolve before
  any likelihood use.**
- **Bonus:** the record also redistributes the full 5000-member weighted **Frederikse
  component ensemble** (`GMSL_ensembles_F20.nc`) — the exact object the 2026-07-19 σ-fix said
  was missing; enables the correct re-referenced per-component band σ (M3 implement).
- Tension diag (`python/diag_dangendorf_vs_frederikse.py`, ref 1995–2005): Dangendorf sits
  INSIDE Frederikse's 5–95% at every trend window; mid-century 1930–1970 D 1.44 vs F 1.85
  (6.8th pctl) is the real but bounded tension; 1993–2018 D 3.03 agrees with altimetry 2.86
  better than F 3.36 does. 11/119 yr outside the F band. Figure + summary in `outputs/`.

### A2/A4/A5/A6 — phase-2 calibration changes WIRED (not yet run), 35→39 params
- **A2:** freed `λ`, `ais_γ`, `ais_κ` under their existing paleo marginals (param_priors.csv).
  Observationally unidentified over the historical window → they sample the prior; the point
  is to propagate fast-dynamics uncertainty and de-bias the hot medoid (λ 0.0137→prior 0.0104).
- **A4:** runoff line reparameterized to its identified direction (`T_on = −h0/c`, `c`) under a
  rebuilt joint paleo prior (`compute_paleo_geo_prior_ton.jl` → `paleo_geo_prior_ton.csv`;
  paleo T_on −15.64±5.54, r(T_on,c)=+0.64 vs the posterior r(h0,c)=0.9997 it replaces).
  `h0 = −T_on·c` reconstructed per draw.
- **A5:** SMB likelihood term on model `β_total` (1979–2008 mean) vs area-scaled Rignot 2019
  (2098×0.888 = **1863 ± 118 Gt/yr**; σ from Rignot's spread, Mottram-2021 alternative flagged).
  At the medoid β_total = 2389 Gt/yr (z=4.45) — target is interior to the paleo-prior-vs-SLR-fit
  tension, so it anchors precip0 to a physical intermediate and breaks the 34:1 input–output
  degeneracy. **σ is a Marcus sign-off item.**
- **A6:** GMST→Antarctic-temperature map sampled as transient amplification `amp` (anchor
  T_ant(GMST=0) preserved); prior **N(0.95, 0.10)** on CMIP6 PAI1 (Xie et al. 2022, Sci Rep
  12:16548: 0.88/0.95/0.97/1.03 for SSP1-2.6/2-4.5/3-7.0/5-8.5; no published inter-model sd —
  0.10 spans the scenario range without re-admitting the equilibrium 1.196). Replaces the
  hard-coded 0.8365/15.42 (amp 1.196, ~26% high). **σ is a Marcus sign-off item;** biggest
  headline-mover (could shift "82% crossed by 2100" to a minority).
- Smoke-tested (200 iter): 39 params, θ0 logpost −799 (vs baseline −779), amp anchor identity
  exact, all new params tracked. Launch is TWO-STAGE (common-start tuning run → build
  over-dispersed starts + adapted cov → 4×2M production); `--overdisperse` now errors clearly
  when the starts file predates the current parameter set.

---

## [unreleased] — 2026-07-19 — σ-fix re-baseline: accept-on-deliverable, + pulse-size robustness

### σ-fix re-baseline (4 × 2M, over-dispersed starts, corrected Frederikse band)

- **Parameter marginals NOT converged** — worst R̂ **1.458** (`ais_slope`), the same
  identifiability ridge. **This is slightly WORSE than run 3 (1.320), not better.**
  **Correction to an earlier claim:** I said the σ fix "plausibly fixes the sampling
  problem." It does not — widening the observational σ *flattens* the likelihood, which
  makes the weakly-identified ridge *less* identified, so param-level mixing got marginally
  worse. The σ fix remains correct (the uncertainty really was wrong), but its effect on
  sampling is neutral-to-negative, not positive.
- **Deliverable IS converged, now under OVER-DISPERSED starts:** SLR@2100 R̂ **1.003**,
  SLR@2150 R̂ **1.004** (`diag_slr_convergence_by_chain.jl`, chains started from
  `ais_iceflow0` quantiles 0.02/0.35/0.65/0.98). This closes the anti-conservative-R̂ hole:
  chains that start far apart on the failing direction still agree on projected SLR to ~5 cm
  against a ~23–35 cm within-chain sd. Projected SLR @2100 median 76.1 cm, @2150 159 cm.
- **Accept-on-the-deliverable is now vindicated:** the posterior gives a converged,
  over-dispersed-robust SLR projection despite the nuisance marginals. Subsample written to
  `data/MimiBRICK/parameters_subsample_brick_mengel_ext_NOTCONVERGED.csv` (the suffix is
  honest about the *marginals*; it is accepted for SLR-level use — see the naming decision below).

### Two postprocess convergence-gate bugs (both found because the re-baseline was FALSELY certified "all converged")

1. `ess(arr; maxlag = size(arr,1))` trips an internal "draws after splitting is 0" path on
   ≥1e6-draw chains → returns **NaN**, and `NaN < ESS_MIN` is `false`, so NaN-ESS params
   silently PASS. Fixed: `maxlag = min(nmin−4, 200000)` and require `isfinite(r) && isfinite(e)`.
2. The full 37-col × 2e6-row × 4-chain read (~5.7 GB) returns **corrupted** data (NaN R̂/ESS
   for every param) on the swap-bound machine. Fixed: read only diagnosed columns.
   Verified against a low-memory selective read: true worst R̂ 1.458, not "all converged".

### Pulse-size robustness ladder (Marcus's test) — answered and verified

`julia/diag_pulse_size_robustness.jl`: BRICK-Mengel paired at 7 sizes 0.03–30 GtCO₂, climate
by IRF scaling (validated vs real FaIR 20gt/0.01gt, <0.06% median error; P=10 rung reproduces
the production driver bit-identically). Two independent verifiers confirmed paired discipline,
units, linearity, horizons.

- **Per-ton MEDIAN robust to 0.7–2.2% over 0.03–1 GtCO₂** — quantization does NOT move the
  median (the median member never tips). ✔ we are OK at SCC pulse sizes.
- **Genuine large-pulse NONLINEARITY** (not quantization): median +9–20% at 10 GtCO₂,
  +42–101% at 30 GtCO₂, monotonic (compounding disintegration). **ACTIONABLE: the canonical
  BRICK-Mengel pulse tables were run at 10 GtCO₂ → they overstate per-ton median by ~9–20%.
  Recompute the headline at ≤1 GtCO₂.**
- **MEAN unusable** (90–111% ladder spread, non-monotone).
- **The median under-states fast dynamics** in the opposite direction from the mean: the tip
  fraction never reaches 50% at any rung, so the median is always the smooth-channel
  background (mean/median 11–18×). Median = *central* marginal, not the expectation. For a
  fat-tail-inclusive number use the Lemoine-Traeger P(tip)·ΔSLR_tip decomposition, not the mean.

### DECISION PENDING (Marcus)
- **Naming/acceptance:** is the SLR-level R̂ (1.003/1.004) the accepted convergence criterion,
  so the `_NOTCONVERGED` subsample should be renamed to a canonical "accepted-on-deliverable"
  path? Or hold for the parameter-level ridge (which needs a mixture/re-fix, not more iterations)?
- **Recompute the pulse headline at ≤1 GtCO₂** (the 10-GtCO₂ tables are ~9–20% high).

## [unreleased] — 2026-07-18 — BRICK-Mengel **v-next recalibration** (Strategy B: 28 → 35 params)

Branch **`brick-mengel-vnext`** (new). `brick-mengel` is archived/frozen per CLAUDE.md,
so this work branches off it rather than committing onto it. **Flagged for Marcus:**
confirm this is the intended home — the alternative is moving the calibration drivers
into the MimiBRICK-FM repo, which is now the canonical home of the Mengel model.

### Changed
- **`julia/calibrate_mcmc_ext.jl`** — the 7 DAIS geometry params (`ais_μ`,
  `bedheight₀`, `slope`, `iceflow₀`, `precipitation₀`, `runoffline_snowheight₀`, `c`),
  previously **fixed at the prior medoid**, are now **free** under a joint MvNormal
  paleo-covariance prior. 28 → 35 free params (25 physical + 10 AR(1) noise).
- **Forcing** switched from the RFF-SP-central splice to the **SSP2-4.5 harmonized**
  splice (`fair_mean_{gmst,ohc}_ssp245harm.csv`), so the calibration and the pulse
  projections sit on the same forcing. Both share the Smith historical → 1850–2020
  unchanged (1850/1900/1971 bit-identical); differs only over ~2020–2026 of the fit
  window (mean |ΔGMST| 0.03 °C) and in the tail.
- **`FaIRtoFrEDI/build_fair_mean_v145.py`** parameterized (`--emissions-file`, `--tag`,
  `--scenario-label`) so alternate forcings can be built **without overwriting** the
  canonical `fair_mean_{gmst,ohc}.csv`. Defaults unchanged.

### Added
- **`MimiBRICK.jl/calibration/compute_paleo_geo_prior.jl`** → `outputs/paleo_geo_prior.csv`.

### Quarantined
- June-13 28-param `ext` posterior → `outputs/quarantine/20260718_pre_vnext_28param_ext/`
  (**superseded, NOT bugged**). Necessary because `postprocess_mcmc_ext.jl` globs
  `chain_ext_seed*` and would otherwise silently mix 28- and 35-column chains.

### Tried and abandoned / rejected
- **Raw paleo covariance as the prior — rejected.** The 7 params span scales 1e-4…1e3,
  giving `cond(Σ) = 5.2e13`. Used the **standardized** form instead — `MvNormal(0, C)`
  on `z=(θ−μ)/sd`, `cond(C) = 2.75` — which keeps the paleo correlation structure
  without the ill-conditioning.
- **Continuing on the fork's `calibration/calibrate_mcmc_mengel.jl` — abandoned.**
  It does not run: it calls MimiBRICK internals (`get_model`, `set_external_forcing!`,
  `_apply_mengel_defaults!`) unqualified, as if lifted out of the module with the import
  dropped, and separately crashes on missing values because the extended targets gained
  trailing empty years after it was written. Evidence it was refactored for the PR and
  never re-run. My edits to it were **reverted**; pivoted to `calibrate_mcmc_ext.jl`,
  which runs and already had the Mengel emulator, the freed `ais_ocean_temperature₀`,
  the dropped point terms, and NaN handling. *Open: whether to also fix the fork script
  as separate cleanup / flag to Tony.*
- **`islog=true` for `precipitation₀` — rejected.** `setp!` applies `log()` when
  `islog=true`, and MimiBRICK v2.0.0 already computes `exp(ais_precipitation₀)`
  (default `log(0.37)`), so that would log twice. Sampled in log space with `islog=false`.
- **Geometry-specific proposal scale as the fix for low acceptance — rejected by test.**
  Plausible (paleo sd for `ais_μ` is 1.8 vs a chain spread of ~0.004) but **wrong**:
  it moved acceptance only 0.022 → 0.029. `GEO_PROP_SCALE` is retained as a sane default,
  not as the fix. The actual cause was the **θ0 start point** — geometry fell back to the
  paleo prior *mean* rather than the *medoid* the rest of the MAP was conditioned on
  (medoid `precip₀` 0.94 m/yr vs paleo mean 0.40, a 2.3× difference; `iceflow₀` −1.4 sd).
  That put `logpost(θ0)` at −5636 vs the 28-param baseline's −771. Isolated by running the
  original 28-param script at the same iteration count/seed (acceptance 0.192) as a control.
  With the medoid start: `logpost(θ0)` = −779, acceptance 0.196 → 0.222 after adaptation.

### Run 1 (4 × 500k) — NOT CONVERGED; diagnosed, not a bug

Acceptance healthy (0.224–0.241), but **12 params fail R̂<1.05**, and the failures are
exactly the 7 geometry params (R̂ 1.44–1.98) plus the AIS block they correlate with
(`ais_ocean_temperature₀` 1.09, `antarctic_alpha` 1.49, `anto_alpha` 1.25, `anto_beta` 1.51).
ESS ≈ 2000 with bad R̂ = good *within*-chain mixing, bad *between*-chain agreement.

Diagnosed with three tests rather than assumed:
- **Not multimodal.** Per-chain median `log_post` = 126.7 / 128.5 / 129.7 / 126.8 — all four
  chains sit on the same plateau. No chain found a better mode.
- **Not bound-railing.** Only 5% of pooled `ais_c` draws and 10% of `ais_runoff_h0` fall
  within 2% of a paleo bound. **This corrects the "watch `ais_c` railing" flag raised from
  the 50k tuning chain — it was an over-read of one short chain.**
- **The geometry block is weakly identified.** Posterior sd / prior sd = 0.46–0.76
  (`ais_bedheight0` 0.76 ≈ unidentified; the rest roughly halve the prior sd). Per-chain
  medians differ by 1.5–4.5 within-chain sd while posterior density is equal.

So the target is a broad, correlated, weakly-identified ridge — which is *why* the original
calibration fixed these at the medoid. Not a defect in the implementation.

### Run 2 (4 × 1M) — in progress
Reseeded from the **empirical 35×35 posterior covariance** written by postprocess. Run 1
started from the 28×28 embed + diagonal, which encoded nothing about the geometry ridge;
the empirical covariance captures its correlation, so this tests better mixing rather than
brute-forcing iterations. Run-1 chains quarantined to
`outputs/quarantine/20260718_vnext_run1_notconverged/` to keep the `chain_ext_seed*` glob clean.

**A non-converged subsample was written to the canonical
`data/MimiBRICK/parameters_subsample_brick_mengel_ext.csv` and has been moved out** to
`outputs/quarantine/20260718_vnext_NOTCONVERGED_subsample/`. The June-13 `_ext` subsample at
that path was overwritten in the process — it is untracked, but regenerable from the
quarantined June-13 chains. The four MAGICC-vs-FaIR tables are unaffected: their driver
reads the non-`_ext` `parameters_subsample_brick_mengel.csv`, which is untouched.

### 2026-07-19 — ADVERSARIAL AUDIT: several of the above diagnoses were WRONG

A 4-lens adversarial audit of the convergence diagnosis (workflow `wf_e17a59f6-443`)
found real defects. Retractions, with what replaced them:

- **RETRACTED: every ESS number reported for runs 1–3.** `postprocess_mcmc_ext.jl:37`
  called `ess(arr)` with MCMCDiagnosticTools' default `maxlag=250`, which truncates the
  Geyer sum at τ≤500 and therefore **floors ESS at ntotal/500**. Reported values were
  exactly that floor (run1 ~2000, run2 ~4000, run3 ~8000). The "ESS doubled → mixing
  improved" reading — which I used twice as evidence — was the floor doubling with
  `ntotal`. **True run-3 ESS: `ais_iceflow0` 10.6 (τ=376,230), `antarctic_alpha` 19.6,
  `ais_precip0_LOG` 41.9, `ais_slope` 47.7.** Fixed; ESS now reported with τ.
- **RETRACTED: "longer chains, no methodological change."** Reaching ESS 400 for
  `ais_iceflow0` needs ~38M iterations *per chain* (~80 h/chain). Run 3 (2 M) confirmed
  it empirically: R̂ did **not** improve over run 2 and the worst param got *worse*
  (1.245 → 1.320). Chain length is not the lever.
- **RETRACTED: the identifiability causal story — it was backwards.** The parameters that
  fail R̂ are the **constrained, correlated** ones; the weakly-identified ones mix
  *trivially* (`ais_bedheight0` ESS 7218, `ais_c` 5356) because the sampler just draws the
  prior. Correspondingly, "re-fix `ais_bedheight0`" was exactly backwards — it is the
  best-converged parameter in the set (R̂ 1.000).
- **RETRACTED: run-1 provenance.** Run 1 did **not** use a 28×28 embed; its log shows the
  full-35×35 branch fired. Both runs were seeded 35×35 (run 1 from the 50k pilot). The
  earlier commit message and handoff describing a diagonal-vs-tuned contrast are wrong.
- **RETRACTED: "not multimodal."** Per-chain median `log_post` cannot distinguish a flat
  ridge from equal-height modes. Run 1 never reached the typical set (plateau ~126 vs the
  stationary ~135, ≈3000× in density), and run-2 seed2029 sat at ~126 for 600k iterations
  then jumped to ~135 — a metastable neck, escape time O(3–6 × 10⁵).
- **CORRECTED: bound-railing.** Holds for run 2 (max 0.0075 within 2% of a bound) but was
  **false for run 1**, where chains spent ~50% of draws against the `ais_runoff_h0`
  ceiling. The 2%-of-range band was too thin to see it.
- **UPHELD:** R̂ *is* rank-normalized split-R̂ (Vehtari 2021), verified by independent
  reimplementation. Reseeding the proposal is legitimate adaptive MCMC (fixed before the
  run, diminishing adaptation satisfied) — the R̂ validity problem is the shared start, not
  the reseed. `ais_runoff_h0`↔`ais_c` posterior correlation +0.954 (prior +0.228) is a
  genuine structural degeneracy. Rotating onto the *prior's* principal axes would be a
  no-op, since RAM already adapts a full covariance.

### THE RESULT THAT MATTERS: the deliverable IS converged

`julia/diag_slr_convergence_by_chain.jl` (new) runs 400 thinned draws per chain forward
on SSP2-4.5 and diagnoses **projected SLR** rather than the nuisance marginals:

| quantity | R̂ | ESS | between-chain median spread |
|---|---|---|---|
| SLR@2100 | **1.001** | 1564 | 4.5 cm vs 22 cm within-chain sd |
| SLR@2150 | **1.002** | 1420 | 5.1 cm vs 34 cm within-chain sd |

Verified **not** an artifact of parameters silently failing to set: a one-at-a-time
sensitivity probe gives each badly-mixed param large individual leverage on SLR
(`ais_iceflow0` up to 57 cm @2100, `ais_precip0_LOG` 49 cm), and the chains genuinely
disagree on those marginals. So the AIS geometry sits on a **compensating ridge** —
individually consequential, jointly constrained. Pooled median SLR@2100 = 76.8 cm
corroborates the earlier 77.7 cm posterior-predictive value.

### Run 4 (4 × 2M, OVER-DISPERSED starts) — in progress
The one remaining validity hole: all runs to date started all 4 chains at an identical
θ0, making R̂ anti-conservative (it cannot see mass no chain reached) — including the SLR
R̂ above. `--overdisperse` now starts each chain from a real posterior draw at
`ais_iceflow0` quantiles 0.02/0.35/0.65/0.98. Random jitter was tried first and failed
(200/200 non-finite logposterior). Expect R̂ to look worse; that is the diagnostic working.

### DECISION PENDING (Marcus) — superseded framing below

*(The original three options were written before the audit. Options 1 and 2 are now dead:
chain length cannot work, and `ais_bedheight0` was the wrong parameter to re-fix.)*

The live decision is **what to gate acceptance on**:

- **RECOMMENDED — gate on the deliverable.** Accept the posterior on SLR@2100/@2150 R̂
  (1.001/1.002) plus the AIS projection knobs, and report the 7 geometry marginals as a
  weakly-identified nuisance block on a compensating ridge. Requires disclosure in methods
  (see below). Conditional on run 4 confirming under over-dispersed starts.
- **Alternative — re-fix the hard-mixing params** (`ais_iceflow0` / `ais_slope` /
  `ais_precip0_LOG`, *not* `ais_bedheight0`). Cheap, but `ais_precip0_LOG` is the most
  projection-coupled geometry param (r = −0.282 with `antarctic_alpha`, +0.364 with
  `anto_beta`), so fixing it is not free.
- **Alternative — change sampler.** The ridge is curved; a linear reparameterization is a
  no-op under RAM. Would need HMC/NUTS on a transformed target or tempering.

**Must be disclosed in the paper's methods** regardless of choice: R̂ is rank-normalized
split-R̂; several AIS marginals do not reach R̂<1.05 at 4 × 2M and are reported as a
weakly-identified nuisance block; convergence is asserted on posterior-predictive SLR, not
on those marginals; the `ais_runoff_h0`↔`ais_c` degeneracy (posterior r = +0.954).

## [unreleased] — 2026-07-09 — CH4/CO2 pulse → SLR **research plan** (adversarially reviewed)

- **`notes/research_plan_2026-07-09_ch4co2_slr_paper.md`** — full research plan
  expanding the same-day handoff into a submission-oriented document: paper thesis
  + 4 contributions, literature positioning/novelty (Sterner-Johansson-Azar 2014 and
  Zickfeld 2017 as ancestors; Nauels 2025 / SURFER v3.0 / Wong's own arXiv preprint as
  threats), the **RFF-SP-vs-SSP backbone decision** (recommend RFF-SP primary for the
  gas headline + uncertainty band; SSP2-4.5 as the shared cross-model-panel backbone
  and AR6-anchor/curvature layer), pulse-experiment design + discipline, MAGICC Phase 2
  and FACTS comparison plans, figure/table set, 11 open methodological decisions, an
  11-row risk register, dependency-ordered sequencing, journal strategy, and a compiled
  reference list with DOIs.
- **Built from a 7-agent context sweep** over the BRICK-FM fork docs, MAGICC Phase 1/2
  handoffs, the completed 3-BRICK pulse study, FACTS scoping, the backbone evidence, and
  a verified literature search; then **adversarially reviewed by 3 independent critics**
  (numeric consistency — all headline numbers recompute and match source; novelty/strategy;
  methods/execution risk). Fixes folded in: reframed "level-vs-marginal inversion" as a
  mechanism decomposition (pre-empts the "expected threshold-model behavior" objection);
  added a **required CH4-specific scenario-sensitivity test** (the ~8% scenario-insensitivity
  is a CO2 cross-check, not CH4 — and RFF under-projects CH4 growth, obs ≥ p95); elevated
  Wong coordination and the reference-arm reuse-vs-re-run question to explicit gates; split
  the fossil-CH4 doc-vs-lock contradiction by arm; flagged the RFF CO2-unit (1000×) and
  MAGICC float32-floor pulse-size risks; and made GWP-basis dependence of the crossover a
  first-class result.

## [unreleased] — 2026-07-09 — CH4/CO2 pulse → SLR paper plan (BRICK-FM coming-out paper)

- **`notes/handoff_2026-07-09_ch4co2_slr_paper_plan.md`** — plan for the paper
  combining CH4-vs-CO2 pulse SLR impacts with the BRICK-FM introduction. Covers:
  BRICK-FM v-next recalibration scope (Smith 2024 emissions splice, freed AIS
  geometry params, IMBIE/Dyurgerov point-term reconciliation, TE overshoot,
  FaIR-config-aware calibration options), MAGICC Phase 2 + FACTS2.0 comparison
  plan, paper skeleton, open methodological decisions, and sequencing.
- **Discrepancy flagged (must resolve before recalibration):** the fork's
  `calibrate_mcmc_mengel.jl` includes the IMBIE + Dyurgerov Gaussian point terms
  unconditionally, but the ext refit that produced the shipped posterior dropped
  both — re-running the fork script as-is will not reproduce the shipped posterior.

## [unreleased] — 2026-06-24 — Phase 2 RFF-SP 2k subsample + extractor --subset flag

- **`outputs/rff_subset_2k.csv`** — canonical 2000-draw RFF-SP subsample for the
  Phase 2 MAGICC-vs-BRICK-Mengel comparison. Stride-5 selection (rff_idx 1,6,11,…,
  9996); deterministic and evenly-spaced across the RFF-SP inventory. Decision
  confirmed by Marcus 2026-06-24 (2k subsample + 1:1 LHS MAGICC member pairing).
- **`extract_pulse_marginals_3brick.py`** — added `--subset <csv>` flag.  Optional
  path to a CSV with `rff_idx` column; filters the 10k per-draw arm files to the
  specified subset before computing weighted marginals. Default (no flag) = full 10k
  (existing behavior unchanged). Subset output named
  `marginals_summary_<stem>.csv` to avoid overwriting the canonical 10k result.
  Validated on 2k: Mengel CO2 medians agree with full-10k to 0.3% (@2100) / 0.6%
  (@2300) — within sampling noise.
- **`extract_fossil_ch4_marginals_3brick.py`** — same `--subset` flag added.
  Output named `marginals_fossil_ch4_summary_<stem>.csv`.

## [unreleased] — 2026-06-17 — LWS seed lock + brick-mengel archived

- **Root cause** of the ~0.4 cm total-SLR drift between Mengel SSP-projection re-runs: MimiBRICK's
  `get_model` draws `lws_random_sample ~ Normal(0.0003, 0.00018)` UNSEEDED on every call. (Diagnosis:
  GSIC/GIS/TE bit-identical, AIS float-noise, LWS the entire delta with mixed signs across SSPs.)
- **Fix:** `build_brick_mengel` now takes `lws=:seeded` (default; fixed-seed LOCAL RNG, `LWS_SEED=2026`,
  reproducible realization), `:central` (0.3 mm/yr mean = MimiBRICK-FM), `:zero`, or `:random` (legacy
  unseeded). Local RNG keeps the global stream (FaIR-member pairing seeds) untouched. Verified bit-identical
  across re-runs; LWS now a single locked value (2.596 cm) across all SSPs (correct — LWS is climate-independent).
  Regenerated SSP / matched / hybrid Mengel outputs (shifts immaterial, sub-0.5 cm).
- **All canonical BRICK versions now have locked LWS:** `main` (BRICK2.0) and `brick-v1.2-vehicle`
  (preBRICK2.0) already seed `Random.seed!` immediately before `get_model` in their canonical drivers
  (obs-driven, flatcube); MimiBRICK-FM uses the `:central` mean; brick-mengel uses `:seeded`.
- **`brick-mengel` ARCHIVED** (annotated tag `archive/brick-mengel-2026-06-17`, branch kept). Frozen final
  state of the calibration/working branch; the Mengel model is canonical in MimiBRICK-FM, and this tag
  preserves the study drivers (MAGICC comparison, CO2/CH4 pulse 3-BRICK, recalibration diagnostics) that
  were never extracted there. Canonical going forward: brick-v1.2-vehicle, main, MimiBRICK-FM.

## [unreleased] — 2026-06-15 — CO2/CH4 pulse→SLR: headline reframed to CH4-as-CO2eq (Marcus)

Marcus: drop the fossil-CH4 variant from the HEADLINE (the co-emitted oxidation CO2 is an instantaneous
pulse, an inexact stand-in — a real fossil pulse spreads the oxidation CO2 over the methane oxidation
lifetime) and express the headline CH4 marginal in **CO2-equivalent (AR6 non-fossil GWP-100 = 27.0)** so
both gases are on cm/GtCO2(eq).
- `marginals_summary_co2eq.csv` — CH4 rows ×(1000/27.0)=×37.037 (exact linear rescale of every quantile/
  mean/component); CO2 unchanged. The physical `marginals_summary.csv` (cm/TgCH4) stays as source of truth.
- `plot_pulse3brick_marginals.py` regenerated → `pulse3brick_marginals.png` now plots CO2 (top row) vs
  CH4-as-CO2eq (bottom row) with the **y-axis SHARED per horizon column**, so the short-lived-forcer
  crossover is visible: CH4-eq Total towers over CO2 at 2100 (~2.2–2.7e-2 vs ~0.5–1.2e-2 cm/GtCO2eq) and
  falls below it by 2300. GWP from a named constant; fossil exclusion noted in the caption.
- `headline_table_co2eq.md` is the headline table (CO2 vs CH4-CO2eq + ratio + per-component); the fossil
  sensitivity stays in `headline_table_fossil_ch4.md` (NOT headline). CH4-CO2eq ÷ CO2 ratio ~2.2–2.3× @2100,
  ~1.4× @2150, ~0.6–0.7× @2300, all 3 versions.

## [unreleased] — 2026-06-15 — CO2/CH4 pulse→SLR: STEPS 5–7 DONE — STUDY COMPLETE

Steps 5 (per-version Wong weights), 6 (paired weighted marginals), and 7 (headline figure) all
complete. The CO2/CH4 pulse→SLR / 3-BRICK-version study is finished through the figure; narrative
is Marcus's to draft.

- **Step 5a/b — per-post baseline l_B (Dangendorf):** `slurm/submit_lB_pulse3brick.sh` (2-task array,
  4 cpu, ~1–2 min each). pre93 via `julia/compute_lB_per_post_v121.jl` (julia_v121, pre-#93 35-col
  posterior, precip_log=false); brick2 via NEW `julia/compute_lB_per_post_brick2.jl` (julia_v2,
  post-#93 posterior, **precip_log=true**, v2.0.0 get_model — a copy of the v121 script with the
  precip log-shim + brick2 defaults). mengel SKIPPED (equal-weighted; no Wong — locked 2026-06-15).
  Outputs Torch `outputs/brick_lB_per_post_{pre93,brick2}.csv` (10000 rows, all finite).
  - **Tried + abandoned:** running `compute_lB_per_post_v121.jl` as-was in julia_v121 — FAILED
    (`ArgumentError: Package Distributions not found`; the pinned v1.2.1 env has no Distributions).
    Fix: replaced the `MvNormal` logpdf with a Cholesky logpdf using only `LinearAlgebra` (stdlib),
    numerically identical. Did NOT mutate the pinned env (no Pkg.add). brick2 unaffected (julia_v2
    has Distributions; left as-is — each version's Wong weight uses only its own (l_FB − l_B), so
    cross-version logl-implementation differences are irrelevant).
  - **Uniformity check (per "suspicious uniformity = bug" discipline):** pre93 l_B is very tight
    (std 1.9, range 364–385) vs brick2 (std 79). NOT a degenerate code path — **9959/10000 unique**
    l_B values; the tightness is real, driven by the pre-#93 posterior's near-constant AR(1) nuisance
    params (rho_gmsl CV 0.4 %, sd_gmsl CV 0.19 vs brick2 0.41) under a *fixed* default-ssp245 backbone
    (the logl scale is set by sd/rho, which barely vary).
- **Step 5d — Wong weights:** NEW `python/apply_wong_weights_pulse3brick.py` (split-CSV adaptation of
  `apply_wong_weights.py`; reuses its Kalman logl / ESS / loaders verbatim). Reads l_FB from
  `{version}_baseline.csv`'s `slr_<year>` 1850–2300 trajectory (cm, re-ref to 2000; verified slr_2000==0),
  merges l_B. **post_idx convention bug caught:** Step-4 cells store post_idx **0-based** (driver does
  `post_idx_1b = post_i + 1`), but `load_posterior`/Julia l_B are **1-based** → fixed with a +1 map for
  the sd/rho lookup and l_B merge, keeping the 0-based cell key in the output. Replaced the coarse grid
  c-tuner with a **bisection** root-solve (ESS_fraction is monotone in c, and the grid over/undershot
  the steep ESS curve). Both arms hit **ESS = 50.0 %** exactly: pre93 c=0.262, brick2 c=0.00857.
  Wong shifts are modest (pre93 total SLR@2100 83.7→83.5 cm; brick2 73.8→77.9). Outputs Torch
  `outputs/wong_weights_{pre93,brick2}.csv` (per-cell w_norm + l_FB/l_B/log_w + keys).
  `--obs dangendorf` (1900–2018, 119 yrs) kept in sync between Julia l_B and the Python l_FB.
- **Step 6 — paired weighted marginals:** NEW `python/scripts/extract_pulse_marginals_3brick.py`.
  Pairs pulse↔baseline on the 4 keys (validate one-to-one; 10000/version/species), differences each
  of {total, ais, gsic, gis, te, lws} × {2100,2150,2300}, ÷ pulse size (CO2 0.01 GtCO2, CH4 1.0 Tg),
  weighted quantiles (pre93/brick2 Wong; mengel uniform) + unweighted for the §0 sanity check.
  Output `outputs/pulse3brick_v145/marginals_summary.csv` (108 rows; committed).
  - **Sanity PASSED:** unweighted total-q50 matches handoff §0 to **0.1–0.3 %** (ratios 0.999–1.003).
    Component means sum to total to machine precision (~1e-14). LWS marginal = 0 everywhere (the
    deterministic landwater add-on cancels in the pulse−baseline difference — correct).
  - **Physics (weighted q50, cm/unit):** pre93 CO2 is **GIS-dominated** (GIS 9.1e-3 of 1.15e-2 total
    @2100; 2.8e-2 of 3.1e-2 @2300 — the pre-#93 GIS pathology). brick2 GIS is tamed (5e-4) and the
    marginal is TE/GSIC-led. mengel has the largest **AIS** (8.99e-4@2100 → 3.78e-3@2300) with a fat
    tipping tail (CO2 mean 4.3e-2 ≫ median 4.7e-3). pre93 AIS marginal is slightly negative (~−1e-4).
- **Step 7 — headline figure:** NEW `python/plot_pulse3brick_marginals.py` → `outputs/pulse3brick_marginals.png`
  (2 rows species × 3 cols horizon; x = {Total, AIS, GSIC, GIS, TE}, grouped bars per version at the
  WEIGHTED median, Total bars carry weighted 5–95 % whiskers). **Grouped median bars (not a stacked
  mean)** deliberately, because the marginals are heavily right-skewed (mean ≫ median in the AIS-tipping
  tail) so a mean-stack misrepresents the central estimate; LWS omitted (marginal≡0). The figure makes
  the version story legible: pre-#93's Total is **GIS-driven** (towering red GIS bar), BRICK-Mengel
  leads on **AIS**, BRICK 2.0/Mengel TE comparable. Labels all from named constants; the caption text
  box is a placeholder for Marcus's narrative. Companion `outputs/pulse3brick_v145/headline_table.md`
  (Total median [5–95] + per-component attribution) committed for the writeup.
- **Canonical outputs (Torch unless noted):** l_B `outputs/brick_lB_per_post_{pre93,brick2}.csv`;
  weights `outputs/wong_weights_{pre93,brick2}.csv`; marginals `outputs/pulse3brick_v145/marginals_summary.csv`
  (committed); figure `outputs/pulse3brick_marginals.png` + `headline_table.md` (committed).

## [unreleased] — 2026-06-15 — CO2/CH4 pulse→SLR: STEP 4 DONE (90k BRICK runs)

Launched + completed the production run (Marcus go). Outputs: `outputs/pulse3brick_v145/{pre93,brick2,mengel}_{baseline,co2,ch4}.csv`.
- **Bug caught at launch + fixed:** the first submit (job 10846724) failed all 9 tasks in 48 s —
  `NPZ.jl: unsupported type U171`. The 2026-06-14 cube seed-provenance addition embedded numpy
  **string/0-d arrays** in the `.npz`, which the Julia reader can't parse. Fix: strip string/scalar
  provenance to a sidecar `cube_*.provenance.json`, keep only `cell_seeds` (int64) in the npz —
  applied to the existing r2 cubes on Torch (data arrays untouched) and to the builder
  (`lhs_climate_v145_meta.py`, FaIRtoFrEDI `c5a7b84`). Re-ran (job 10848541): all 9 COMPLETED, ~2 min/arm.
- **Validated:** 9 CSVs × 10000 rows, fully paired. Unweighted per-unit marginal medians (cm):
  | version | CO2/GtCO2 @2100 | @2300 | CH4/Tg @2100 | @2300 |
  |---|---|---|---|---|
  | pre93  | 1.15e-2 | 3.11e-2 | 7.27e-4 | 5.94e-4 |
  | brick2 | 5.07e-3 | 1.00e-2 | 3.07e-4 | 1.74e-4 |
  | mengel | 4.69e-3 | 1.15e-2 | 2.80e-4 | 2.12e-4 |
  pre-#93 CO2→SLR ≈ 2.3–3× post-#93 (GIS pathology, as expected); CH4@2300 resolvable (1Tg fix worked).
- **Weighting (Marcus 2026-06-15):** primary BRICK-Mengel = EQUAL-weighted; pre93+brick2 = Wong-weighted.
- **Next:** Step 5 Wong (pre93/brick2) → Step 6 weighted marginals (co2 ÷0.01, ch4 ÷1.0; mengel plain) → Step 7 figure.

## [unreleased] — 2026-06-14 — CO2/CH4 pulse→SLR: Step-4 prep (P4) + Mengel l_B (P3)

Launch-readiness work while P1's cubes build (Marcus: P4 first, P3 second). Stops short of submitting.
- **P4 DONE** — synced BRICK drivers (`run_mimibrick_pulse_versioned.jl` + the 3 includes),
  the 3 posteriors + medoid central row, and the BRICK metadata to Torch `/scratch`. Wrote the
  9-task production array `slurm/submit_pulse3brick.sh` (idx = version*3 + arm; pre93→julia_v121,
  brick2/mengel→julia_v2; baseline arm `--save-trajs` for Wong; CO2 0.01Gt ÷0.01, CH4 1Tg ÷1.0;
  same `--seed 2026` for pairing) — STAGED, NOT submitted. Torch BRICK smoke (10 cells × 3 versions)
  all pass: closure resid 0.0, and totals **bit-identical to the local smokes** (pre93 5.3789, brick2
  3.2256, mengel 4.4536 m @2300) — cross-platform determinism confirmed.
- **P3 DONE (mechanics)** — `julia/compute_lB_per_post_mengel.jl`: per-member l_B vs Dangendorf for
  the 28-col mengel posterior (build_brick_mengel + medoid + 18 free params; uses `sd_dang`/`rho_dang`
  since the posterior has no `sd_gmsl`). Validated (5 members, finite l_B). ⚠ **OPEN Step-5 decision**
  flagged in the script: the Mengel posterior is already Dangendorf-calibrated, so whether to Wong-weight
  the mengel arm at all (vs equal-weight) is unresolved — await Marcus.

## [unreleased] — 2026-06-14 — CO2/CH4 pulse→SLR: prerequisites P1+P2 executed

Executing the two Step-4 blockers from the pre-launch review (Marcus: go ahead with P1+P2).
- **P2 DONE** — `julia_v2` (v2.0.0) + `julia_v121` (v1.2.1) instantiated + precompiled on
  Torch via `slurm/precompile_julia_envs.sbatch` (compute node; login-node instantiate was
  stalling/precompiling — SIGKILL risk). Both verified: `get_model`+`run` OK (v2 SLR2100=102.1,
  v121 99.0 cm). Plots/GR/Qt precompile-fails are benign (headless, unused by the BRICK driver).
- **P1 IN PROGRESS** — paired r2 triplet (baseline + co2-0.01Gt + ch4-**1Tg**) built on Torch
  via `slurm/submit_triplet_r2.sh` (array job, one arm each). Moved to Torch after the local
  background build died untraced; Torch calibration sha256 matches local
  (`03b0368…`) so the realization equals the locally-validated smoke. Cubes land on `/scratch`
  with embedded seed provenance (`cell_seeds` etc.). Tag `_flat2015_r2`.
- The 0.01 Tg CH4 cube is float32-corrupted (see prior entry); CO2 stays 0.01 Gt.

## [unreleased] — 2026-06-14 — CO2/CH4 pulse→SLR, 3 BRICK versions: foundations (runbook Steps 0–3)

Built the prerequisites for the CO2 & CH4 pulse→SLR marginal study across three
BRICK calibration versions (pre-#93 v1.2.1 / BRICK 2.0 / BRICK-Mengel), on the
FaIR-v1.4.5 × RFF-SP LHS-10k ensemble. Stopped before the 90k-run Torch launch
(Marcus: foundations-only this pass). Runbook:
`notes/handoff_2026-06-14_co2ch4_pulse_3brick_NEXT-SESSION.md`.

### Added
- **`julia_v121/` — a real MimiBRICK v1.2.1 env** for the pre-#93 arm (the
  `brick-v1.2-vehicle` Manifest pins 1.0.1, so this is a build, not a checkout).
  Pins MimiBRICK git `repo-rev v1.2.1` (sha `94ceca2`) under Julia 1.12; smoke
  passes (build→run 1850–2300, closure 4.4e-16 m). `julia_v121/build_v121_env.jl`.
- **`julia/run_mimibrick_pulse_versioned.jl` — ONE version-aware flat-cube driver
  for all THREE versions** (`--brick-version pre93|brick2|mengel`), one output
  schema (per-component + total SLR at 2100/2150/2300, optional GMSL history for
  Wong). Supersedes the schema-limited `run_mimibrick_flatcube_v121.jl` (components
  at 2100 only) — unified to remove the cross-arm schema-drift risk. pre93 runs in
  `julia_v121` (precip_log=false); brick2/mengel in `julia_v2` (precip_log=true);
  mengel applies the 28-col posterior as 18 free params over the medoid central row
  (mirrors `project_ssps_2100_mengel.jl`). Added NPZ to `julia_v2`.
- **`python/scripts/sanity_battery_pulse3brick.py`** + smoke metadata
  `outputs/smoke25_lhs10k_metadata.csv`. 5-test gate (zero-pulse/cross-process
  determinism, sign-flip, ×magnitude, first-principles, closure) on a 25-cell
  lhs10k-proxy smoke per version → **ALL PASS, gate OPEN**
  (`outputs/sanity_battery_pulse3brick_smoke.txt`). Smoke reproduces the pre-#93
  GIS pathology (dGIS@2100 ≈ 8.1e-3 cm/GtCO2 vs ~4–5e-4 for brick2/mengel; pre93
  total ~3× larger @2300), ×magnitude linear to ~1% (no AIS tipping at 0.01 Gt),
  CH4:CO2 per-unit ratio ~0.055–0.063.

### Corrected (vs the runbook's assumptions)
- **MimiBRICK v1.2.1 already uses `get_model(ssprcp_scenario=…)`**, NOT
  `rcp_scenario=` as the runbook claimed; it ships both RCP- and ssp-named SNEASY
  forcing files (no date suffix) and uses LINEAR precip0 (`precip_log=false`). The
  real v1.2.1→v2.0.0 differences are the date-suffixed forcing files + the
  precip_log reparam. (Forcing is overridden by the cube's GMST/OHC anyway.)
- **The Mengel 28-col posterior cannot be applied via `update_brick_params!`** (it
  lacks the full AIS/glacier/thermal_s0 columns). Canonical path = medoid central
  row for fixed params, then the 18 free params per draw, per `project_ssps_2100_mengel.jl`.
- **`brick_mengel.jl` must be include()d at module scope**, not lazily in a
  function — Mimi's `run(m)` otherwise hits a world-age MethodError on
  `run_timestep_glaciers_mengel`. Loading it is harmless for pre93/brick2 (the
  Mengel component is defined but only instantiated for `--brick-version mengel`).

### Pre-launch review (2026-06-14) — 3 prerequisites before Step 4
Verified sound: lhs10ks cell layout == metadata (incl. seeds); pairing (pre-2030
dGMST=0, @2000=0 → rebaseline cancels); cross-process paired determinism exact;
CO2 0.01 Gt well-resolved (15–30× float32 ULP, ×magnitude ~1%); posteriors all
10000 rows (no off-by-one); closure ~1e-11.
- **P1 — CH4 0.01 Tg cube is float32-corrupted → regenerate at 1 Tg** (Marcus
  2026-06-14). CH4 dGMST decays below the float32 ULP (~2.4e-7 °C) after ~2060
  (nonzero cells: 72%@2075, 34%@2100, 8%@2300); CH4 SLR marginal ratio
  (0.01-cube/1-cube) = 0.97@2100, 1.20@2150, 0.51@2300, **TE@2300 → 0**. 1 Tg CH4
  is ~10× smaller dGMST than CO2-1Gt → well below AIS tipping. Build
  `cube_v145_lhs10ks_pulse_ch4_pos_1tg_flat2015.npz` (FaIR driver, paired seeds),
  marginal ÷1.0; CO2 stays 0.01 Gt ÷0.01.
- **P2 — Torch envs missing.** Only the v1.0.1 `julia` env is on Torch; build
  `julia_v2` (brick2/mengel) + `julia_v121` (pre93) there (instantiate + precompile).
- **P3 — Mengel Wong-`l_B` path missing** for Step 5 (`compute_lB_per_post*` assume
  the 35-col posterior; mengel 28-col needs medoid + 18-free).

### Pending (next session — Step 4 after P1/P2)
- Torch: 3 versions × 3 arms {baseline, co2_pos_001gt ÷0.01, ch4_pos_**1tg** ÷1.0}
  × 10k = 90k runs, partition `cs`. Then per-version Wong weights (own `l_B`) +
  paired marginals + headline figure.

## [unreleased] — 2026-06-13 — BRICK-Mengel post-2018 multi-component extension

### Added
- **Extended ALL calibration targets past Frederikse 2020's 2018 end** with
  reconciled modern products and re-fit, to test the post-2020 Antarctic pause +
  (Marcus's expansion) Greenland / thermal-expansion / glaciers.
  - Data: GRACE-FO JPL mascon AIS+GIS (→2026), GlaMBIE 2025 glaciers (→2023),
    NOAA NCEI thermosteric (→2025), NOAA STAR total (→2024); IMBIE 2023 AIS+GIS
    cross-check (agrees with GRACE splices <0.07cm). `raw/README_modern_extensions.md`.
  - `python/prep_recalib_targets_ext.py` → `outputs/recalib_targets_ext.csv`
    (offset-match splice onto Frederikse over GRACE/obs overlap; per-component end yrs).
  - `julia/calibrate_mcmc_ext.jl` + `run_mcmc_ext_local.sh` + `postprocess_mcmc_ext.jl`:
    per-series AR(1) windows; **dropped IMBIE+Dyurgerov point terms**; total extended
    w/ NOAA STAR (Marcus decisions). 4×500k → 27/28 R̂<1.05.
  - Obs check `julia/posterior_predictive_ext.jl` + `python/plot_postpred_components_ext.py`.
  - High-T glacier melt verification `python/verify_mengel_hightemp_melt.py` (Marcus:
    confirm Mengel melts MOST glaciers at high T) — PASS (99% committed @4°C).
  - Projection A/B `python/plot_ssp_projections_ext_compare.py`; `project_ssps_2100_mengel.jl`
    gained an optional TAG arg (baseline default byte-identical).

### Result
- Extending barely moves the physics (ais_ocean_temperature₀ +0.013); GMSL@2100
  LOWER by 0.8–3.2cm, ~entirely via AIS; high-forcing overshoot vs AR6 persists
  (MICI-threshold-driven, unconstrainable by ~7yr). TE overshoot NOT resolved by
  NOAA steric (+0.51cm@2025). AIS pause not reproduced (warming-driven model).

### Tried / noted
- 4×**100k** with the baseline proposal covariance did NOT converge (25/26 R̂>1.05;
  per-chain logpost spread 6–138 = slow burn-in from a mismatched proposal, NOT a
  bug). Fixed by seeding the 500k from the ext-tuned `adapted_cov_ext.csv`.
- `.gitignore`: exclude the 276MB×4 MCMC chain files (regenerable).

## [unreleased] — 2026-05-30 — Rennels 7-panel SSP2-4.5 SLR + pulse figure

### Added
- **7-panel SLR figure for Lisa Rennels** confirming emission-pulse + BRICK
  results under SSP2-4.5. Left: total GMSLR rel 2005 (median + 75%/90% bands,
  unweighted spread over 841 v1.4.5 configs × 8 BRICK post-PR#93 posteriors).
  Right 2×3: SLR impulse response to a 2020 CO₂ pulse, decomposed into
  TE/GSIC/GIS/AIS/LWS/Total, with BOTH a +0.01 GtC and a +1e-4 GtC arm overlaid.
  - Driver: `python/scripts/rennels/rennels_build_ssp245_cubes.py` — FaIR v2.2.4
    (v1.4.5 cal) SSP2-4.5 baseline + 4 pulse arms (±0.01, +0.02, +1e-4 GtC at
    2020.5, CO₂ FFI), emits **GMST + OHC flat-cubes** (float64 — float32 destroys
    the 1e-4 GtC signal, ~1e-7 °C on ~2.5 °C). Pulse in GtC→GtCO₂ ×44/12.
  - Figure: `python/scripts/rennels/rennels_7panel_figure.py`.
  - Outputs: `outputs/rennels/slr_7panel_ssp245.{png,pdf}`,
    `rennels_pulse_response_summary.csv`, 5 cubes + metadata, BRICK CSVs.
- **Result:** 1e-4 GtC pulse IS resolvable through BRICK in float64; the two arms
  agree to <0.2% at 2150 (linear). Per-GtCO₂ total marginal @2150 = 0.0073
  cm/GtCO₂ (matches memory ~0.0074). TE dominates; LWS ≈ 0 (pre-2019 calib).
- **Sanity:** all 5 paired-pulse tests pass at FaIR level (zero/sign-flip 0.02% /
  doubling 2.0002 / linearity 0.02% / first-principles 0.415 m°C/GtCO₂) AND BRICK
  level (repro bit-identical / sign-flip anti-sym / doubling 2.0000 / linearity
  0.29% / closure Σcomp=total to 1.4e-13 m).
- **Caveat flagged on-figure:** unweighted SSP2-4.5 median runs above AR6
  (69 vs ~50 cm @2100; 132 vs ~68 cm @2150) — consistent with this project's
  hot BRICK posterior (RFF-SP gives ~93 cm @2100), not a bug; per user's
  explicit "unweighted climate+BRICK spread" choice (no Wong importance weights).
- **Absolute-units variant** `slr_7panel_ssp245_abs1em4.{png,pdf}`: right panels
  in metres of SLR per literal +1e-4 GtC pulse (TE ~2e-8 m @2300; direct-1e-4 vs
  0.01÷100 agree <0.2%). For comparison with Rennels' own per-1e-4-GtC numbers.

### Fixed / corrected
- **AIS get_model seed-bug note in CLAUDE.md was overstated** ("uniformly
  non-negative once seeded"). Measured: matched-seed AIS median is slightly
  NEGATIVE at 2050 and 34–56% of draws are negative at all horizons — the true
  small-pulse AIS signal straddles zero. A negative *median* alone is not proof
  of the bug. Demonstrated the actual bug signature: seed-mismatch zero-pert
  (2026 vs 1234) injects a systematic AIS offset (median −5e-4 cm, 100% negative)
  ~100× the true ~5e-6 cm signal. Diagnostic tests added to the note.

## [v2.1] — 2026-05-29 — finalized substack + poster (Group-Sobol H-S)

### Changed
- **Group-Sobol is now the canonical SLR Hawkins-Sutton method** (replaces the
  earlier TreeSHAP/Shapley attribution, which under-counted the emissions axis
  ~3× — 8.6% vs ~27-29% at 2150 — because collinear cumulative-emissions
  features dilute per-feature Shapley credit). Sobol decomposes *grouped* variance
  directly, immune to within-group collinearity, and is importance-weighted.
  Module: `python/scripts/substack/group_sobol_hs.py`; renderers
  `render_hybrid_tipping_split.py`, `paired_figures_hs.py`,
  `poster/hawkins_sutton_panels.py`.
- **Independent model-free cross-check:** a 324,000-run balanced-factorial ANOVA
  (`anova_hs_decomp.py`) reproduces the Sobol emissions/climate/internal shares
  to within ~2 pp at 2150 (emissions 27.0% ANOVA vs 28.9% Sobol), confirming the
  attribution is not a surrogate artifact. Overlay figure `anova_vs_sobol_overlay.py`
  → `outputs/substack/anova_vs_sobol_total_slr.{png,pdf}`.
- **Terminology:** reader-facing figures/captions now say "importance weighted"
  rather than "Wong-weighted" (provenance comments keep "Wong").
- **Pulse SLR figure:** removed the ensemble-mean line from the pulse-SLR panel
  (tipping-corrupted, not pulse-size-invariant); median + 5-95% band retained.
  Pulse GMST keeps its mean (no tipping pathology).
- **Exceedance table caption** corrected to "FaIR v2.2.4 (v1.4.5 calibration)"
  — distinguishes the model version from the calibration posterior.

### Notes
- Superseded TreeSHAP-era H-S outputs quarantined under
  `outputs/quarantine/20260528_treeshap_slr_underattribution/`.
- Decided to keep Sobol canonical and ANOVA as validator; no pulse ANOVA (the
  cross-check's motivation was the emissions axis, which is ~1% / uncontroversial
  for the pulse). See `notes/handoff_2026-05-28b_group_sobol_hs.md`.

## [Unreleased] — v145 end-to-end pipeline

### Added
- **Hybrid total_slr H-S decomposition with augmentation-based V_BRICK + V_seed** (2026-05-27).
  Pure-Shapley failed for SLR: even high-capacity surrogate + p99 outlier clip left
  OOF V_residual at 25-32%, factor 6-47× the pure-seed gold standard. Diagnosed as
  cfg×post interactions + AIS tipping nonlinearity that HistGradientBoosting can't
  capture. Replaced V_BRICK and V_seed in the SLR figure with model-free estimates:
  - V_BRICK: within-cell variance across 10 BRICK posts per cell (90,000 augmentation
    runs: 10,000 v5 cells × 9 extra post_idx via LHS-stratified sampling).
  - V_seed: within-cell variance across 10 seeds per (rff, cfg, post) group (200
    parent cells × 9 extra seeds = 1800 new FaIR runs + paired BRICK).
  Result: V_internal_SLR now declines from 4.6% (2025) to 0.5% (2150), matching
  physical expectation. BRICK is the dominant axis (~42-59%) across all years. A
  residual wedge (20-37%) is labeled as "cfg×post interactions + tipping" since
  those interactions can't be uniquely attributed.
  Files: `python/scripts/substack/hybrid_hs_total_slr.py`,
  `outputs/substack/shapley_hs_total_slr_hybrid.{png,pdf}`,
  `outputs/substack/v5_hybrid_decomp_diagnostic.csv`.

- **v5 noise-isolated H-S figures landed** (2026-05-27).
  Re-ran `shapley_hawkins_sutton.py` against the new LHS-10k_s cubes
  (`cube_v145_lhs10ks_{baseline,pulse_co2_pos_001gt}_flat2015.npz`) and
  the post-PR#93 BRICK posterior. Headline:
  - total_gmst V_internal at 2021 = **97.5%** (canonical H-S near-term
    recovered; v4 had ~0% because LHS-10k was single-seeded).
  - total_slr at 2050: emi 2% / climate 38% / brick 40% / internal 20%
    (first time all 4 axes nonzero — v4 internal was misallocated to
    surrogate fit gap).
  - pulse_gmst: ~100% climate response (matched-seed cancels internal).
  - pulse_slr: BRICK 35-50% of variance across 2050-2150.
  Companion BRICK metadata `outputs/lhs10ks_brick_metadata.csv` LHS-samples
  `post_idx ∈ {0..9999}` (one unique BRICK posterior member per cell);
  the previous `lhs10k_metadata_v145.csv` only used 3 unique post_idx
  across all 10,000 cells, which had been silently under-sampling BRICK
  uncertainty across the entire v4 family of plots.
  Caveat carried forward: TreeSHAP under-attributes BRICK; Owen-Shapley
  re-render (~40 hr Torch) still pending.

### Fixed
- **Hawkins-Sutton nested-ANOVA finite-replication bias** (2026-05-26).
  The variance-decomposition functions in `python/hawkins_sutton.py`
  (`decompose_slr_4way`, `decompose_gmst`) and the substack-side
  reimplementation in `updated_hawkins_sutton.py` were using `ddof=0`
  population variance at every level and were not subtracting the
  propagated within-cell sampling-noise term from each outer-level
  variance. With only 3 seeds × 3 posts per (rff, cfg) cell, the
  ddof=0 estimator was biased down by (n−1)/n = 2/3 at the inner
  level, and the cfg-means carried σ²_seed/n_seed sampling noise that
  was being absorbed into V_climate. Result: total-GMST early-year
  f_internal showed as 65% (canonical Hawkins-Sutton expectation:
  ~100%) and the substack/poster Panel C / D fractions were
  systematically tilted away from V_internal and toward V_climate.
  Fix: unbiased ddof=1 variances at every level via the
  `n_eff/(n_eff − 1)` Bessel correction (handles weighted variance via
  the effective sample size), plus subtract the propagated noise from
  each outer level (V_internal/n_seed off V_climate; V_climate/n_cfg
  plus V_internal/(n_cfg × n_seed) off V_emissions; analogous 4-way
  formulae with V_brick at the bottom). Clipped to ≥0 since
  finite-sample bias-corrected estimates can go slightly negative when
  the true variance is below the noise floor. Affected outputs: every
  Hawkins-Sutton figure in the substack and poster. Substantive
  changes: total-GMST f_internal at 2030 went 62% → 80%; Panel C
  fractions at 2100 went f_clim/f_emi/f_brick/f_int = 80/3/13/3% →
  54/23/23/0%; Panel D at 2100 went 17/3/45/35% → 1/1/81/16%. The
  Panel C/D PDFs in the IEc handoff are regenerated, and the
  discussion paragraph in poster_text.txt has been updated to reflect
  the new fractions.

### Tried and abandoned
- **Lemoine-Traeger tipping-decomposition framing for pulse-marginal SLR
  figures** (2026-05-26). Three active sites used L-T classifiers with
  inconsistent methodology: `gaussian_vs_empirical_slr.py` used a
  pulse-outcome classifier (per-year marginal > 0.3 cm; pulse-size
  sensitive); `extract_lhs10k_smallpulse_summary.py` used a baseline-state
  classifier (`ais_2100_cm > 20 cm`) but it was silently dead because the
  slim CSV didn't carry `ais_2100_cm`; `lemoine_traeger_decomposition.py`
  used baseline-state but had no callers. We initially standardized on
  baseline-state at 20 cm; that revealed that v1.4.5 + post-PR#93 BRICK +
  Wong weighting leaves 88% of cells classified as tipping-prone, so the
  "L-T linear baseline" was a 12%-subset mean (small slice; the L-T
  premium framing was more informative under v1.4.1 where tipping was the
  minority state). Decision: empirical importance-weighted p5/p50/p95
  quantiles satisfy "accurately reflect likely impact + uncertainty"
  while being both threshold-invariant AND pulse-size-invariant.
  `gaussian_vs_empirical_slr.py` + outputs retired to
  `outputs/quarantine/20260526_lt_to_empirical/`. Tipping-conditional
  columns dropped from `extract_lhs10k_smallpulse_summary.py` output.
  `lemoine_traeger_decomposition.py` library kept as a diagnostic
  utility (marked as such in its docstring) for any future revisit of
  the decomposition framework.

### Added
- **v1.4.5 FaIR pipeline end-to-end**: 18 v1.4.5 cubes (9 LHS-10k + 9 ANOVA-18k;
  baseline + 8 pulse arms each) on Torch; new BRICK driver
  `julia/run_mimibrick_flatcube.jl` adapted to the flat
  `(n_cells, n_year)` cube schema. 270× compute reduction vs. the rectangular
  layout that was used in the v1.4.1 era.
- **`run_mimibrick_flatcube.jl`** flat-cube driver with paired closure check
  (Σ components ≡ total SLR to 1e-10 m on the first row).
- **`python/scripts/run_wong_pipeline_v145.py`** end-to-end Wong-weighting
  pipeline matched to the new schema: l_FB from per-arm BRICK CSVs,
  l_B from post-PR#93 posterior, per-arm baseline-weighted CSVs + envelope
  summaries + paired marginal envelopes.
- **`python/scripts/emit_slim_legacy_csvs_v145.py`** writes slim,
  legacy-schema CSVs (bare-year SLR columns + keys + w_norm) so downstream
  plot scripts (`gaussian_vs_empirical_slr`, `slr_band`, `run_4way_slr_decomp`,
  `run_pulse_4way_slr_decomp`) work unchanged on the v145 outputs.
- **Tony component overlay**: added an LWS panel (BRICK ≡ 0 by design
  through the hindcast — Wong et al. 2017 calibration target had LWS
  removed — plus Frederikse 2020 Terrestrial Water Storage overlay).
  Added Frederikse 2020 overlays to the AIS and GSIC panels so the
  20th-century component biases that cancel into matching GMSL are
  visible: BRICK AIS overshoots Frederikse by ~3.3 cm at 1900 (1900-2000
  rise of +3.95 cm vs Frederikse +0.6 cm), GSIC undershoots by ~4 cm at
  1900, GMSL net agreement is within ~0.2 cm — diagnosed bias cancellation.
- **`fair_vs_obs_gmst_ohc.py`** new substack diagnostic figure: v1.4.5
  ensemble-mean GMST vs IGCC 2024 (4-dataset mean), and FaIR v1.4.5
  ensemble-mean OHC vs spliced Zanna 2019 + IGCC 2024.

### Changed
- **BRICK posterior**: swapped pre-PR#93 (`b > v0` in 97.6% of draws) for
  post-PR#93 (`b > v0` in 0%). The new posterior matches Frederikse 2020
  GIS back to 1900. Old posterior moved to
  `data/MimiBRICK/quarantine/20260524_pre_pr93/` with a README.
- **CITATION / .zenodo.json**: updated calibration source from FaIR v1.4.1
  to v1.4.5 and BRICK posterior provenance from v1.0.1 to post-PR#93 joint.

### Quarantined (pre-fix outputs, kept for postmortem)
- `outputs/quarantine/20260524_pre_v145_e2e/` — v1.4.1-era weighted CSVs
  superseded by v1.4.5 outputs:
  - `brick_lhs10k_baseline_to2300_weighted.csv` (LHS-10k baseline, v1.4.1 era)
  - `brick_lhs10k_pulse0p01gtc_to2300_weighted.csv`
  - `brick_lhs10k_pulse_to2300_weighted.csv` (1-GtC pulse)
  - `brick_anova_long_2300_weighted.csv` (13,500-row ANOVA, v1.4.1 era)
  - `brick_anova_long_2300.csv`, `brick_anova_pulse_long_2300.csv`,
    `brick_anova_marginal_long_2300_weighted.csv`
- `data/MimiBRICK/quarantine/20260524_pre_pr93/parameters_subsample_brick.csv`
  — pre-PR#93 posterior (97.6% b > v0).

### Diagnosed but not fixed (deliberate documentation)
- BRICK 20th-century **AIS overshoots Frederikse 2020 by ~3.3 cm at 1900**;
  cancels against GSIC undershoot. PR#93 only added Frederikse GIS to
  calibration; TE / AIS / GSIC still calibrated to Wong et al. 2017 targets
  (pre-ARGO Gouretski 2007 OHC and a less complete antarctic obs basis).
  Fix would require a future PR adding Frederikse AIS/GSIC to the
  calibration target set. Documented in memory
  `project_brick_component_biases_vs_frederikse`.

## [v1.0-poster-agu-chapman] — 2026-05-06
- Initial v1.4.1-era pipeline + AGU Chapman SLR conference poster artifacts.
- LHS-10k conditional-BRICK ensemble (ESS = 7,037).
- Hawkins-Sutton 4-way decomposition of total SLR and pulse-marginal SLR.
- Zenodo DOI: 10.5281/zenodo.20312325.
