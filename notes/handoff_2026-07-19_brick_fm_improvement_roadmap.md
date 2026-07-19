# Handoff — continuing to improve BRICK-FM (2026-07-19)

Self-contained roadmap. A fresh session should be able to pick up cold from this +
`CLAUDE.md` + the memory files linked inline. Companion to the 2026-07-18 v-next handoff
(`handoff_2026-07-18_brick_mengel_vnext.md`) — read that first for the recalibration mechanics.

**Repos / branches (all work below is on these):**
- `SLR-RFF-BRICK` @ **`brick-mengel-vnext`** — calibration + pulse drivers. HEAD `842a531`.
- `MimiBRICK.jl` @ **`brick-fm`** — the model + paleo-prior builder. HEAD `ec9680e`.
- `FaIRtoFrEDI` @ `heat-ed-morbidity` — forcing builder only (`build_fair_mean_v145.py`).

**Nothing is running.** All background jobs finished. All work is committed.

---

## 1. Where BRICK-FM stands right now

The v-next recalibration (Strategy B: 28→35 params, freeing the 7 DAIS geometry params under a
joint paleo prior; SSP2-4.5 harmonized forcing) is **run and accepted on the deliverable, not
on the parameter marginals.** This distinction is the central result of the last two days and
must not be lost:

- **Parameter marginals do NOT converge** and will not in feasible compute. Worst R̂ **1.458**
  (`ais_slope`), true ESS 18–40 for the ridge params (`ais_iceflow0` ESS ~24, τ≈167k). These
  are a narrow, curved, weakly-identified ridge among the AIS geometry + ocean-transfer params.
  Verified NOT a bug (see the 2026-07-18 adversarial audit): not multimodal in a way that
  matters, not bound-railing, correct rank-normalized split-R̂. Chain length does not fix it
  (2M was marginally *worse* than 1M). See memory [[project-brick-mengel-vnext-recalib]].
- **The deliverable IS converged**, and now under **over-dispersed starts** (the strong test):
  **SLR@2100 R̂ 1.003, SLR@2150 R̂ 1.004** (`julia/diag_slr_convergence_by_chain.jl`), with
  chains started from `ais_iceflow0` quantiles 0.02/0.35/0.65/0.98. The geometry sits on a
  **compensating ridge** — individually each param has up to 57 cm of leverage on SLR@2100, yet
  the chains agree on the projection to ~5 cm. Projected SLR: @2100 median 76.1 cm, @2150 159 cm.
- **Accepted posterior:** `data/MimiBRICK/parameters_subsample_brick_mengel_ext_NOTCONVERGED.csv`
  (10k draws). The `_NOTCONVERGED` suffix is honest about the *marginals*; it is accepted for
  SLR-level use. **Naming/acceptance is a Marcus decision — see §5.**

The pre-v-next canonical `parameters_subsample_brick_mengel.csv` (Jun-13, non-ext) is still what
the pulse/table drivers read; it is untouched.

---

## 2. Bugs found and fixed this session (all committed)

1. **σ-construction bug** (`92b8ce4`, `python/prep_recalib_targets_ext.py`). The Frederikse
   uncertainty band was re-referenced to 1995–2005 with each of mean/lower/upper getting its
   OWN offset. A band width is invariant to a common shift, so three different offsets shrank
   `(hi−lo)` by a constant every year → **18–20 years per series inverted (lo>hi); AIS 47/126,
   GIS 35, steric 38 pinned to the 0.05 cm floor** — the entire modern record. Fixed: one offset
   (the mean's) for the whole band. Median σ was understated 1.3–1.8×. **Known approximation
   remaining:** the raw band width no longer shrinks toward the reference window; the correct
   quantity is `sd(x_t − mean(x_window))` over the Frederikse **ensemble**, which is not in
   `data/observations/raw` (only mean/lower/upper are). Current fix over-states σ near the
   window (safe direction). Getting the ensemble is a real improvement — see §4.
2. **Two postprocess convergence-gate bugs** (`26563ee`, `julia/postprocess_mcmc_ext.jl`), both
   found because the re-baseline was **falsely certified "all converged"**:
   - `ess(arr; maxlag=size(arr,1))` returns **NaN** on ≥1e6-draw chains (internal "draws after
     splitting is 0"), and `NaN < 400` is `false`, so NaN-ESS params silently PASS. Fixed:
     `maxlag = min(nmin−4, 200000)` + require `isfinite(r) && isfinite(e)`.
   - The full 37-col × 2e6-row × 4-chain read (~5.7 GB) returns **corrupted** data on the
     swap-bound Mac (NaN R̂/ESS for every param). Fixed: read only diagnosed columns.
   - Also present since 2026-07-18: `maxlag=250` default **floors ESS at ntotal/500** — every
     ESS reported for runs 1–3 was that floor, overstated up to 270×. See memory
     [[feedback-mcmc-ess-maxlag-trap]]. The gate now refuses to write canonical outputs from
     non-converged chains (`--force` writes a `_NOTCONVERGED` suffix off the canonical path).

**Not yet fixed — flagged for the record:**
- **`dangendorf_2024_gmsl.csv` IS Frederikse 2020** (bit-identical to `Observed GMSL`, max diff
  1.4e-14 mm over all 119 yr; `download_obs.py:353` pulls Frederikse's `global_basin_timeseries.xlsx`).
  So the "total" likelihood term is Frederikse's own total, and the project's "Dangendorf
  importance weights" (`apply_wong_weights.py`, `hawkins_sutton.py`) are Frederikse weights.
  The **label fix is minutes**; what to do with the term is a choice (§5, M3). Highest
  review-risk item in the repo.

---

## 3. The improvement roadmap (evidence-backed, prioritized)

Three adversarial workflows this session surveyed constraint improvements. Full findings in the
task outputs under `.../tasks/` (workflow IDs `w0auuifni` general, `wf_e0ffe212-1f7` future-only,
`wf_60207247-917` pulse-ladder). Consolidated and de-duplicated here. **Separate the three goals
— they are different:** (A) fix physical bias, (B) improve defensibility in review, (C) the
sampling ridge (largely unfixable by data; it's identifiability).

### TIER 1 — do first, high value, hours–days

- **A1. Recompute the pulse headline at ≤1 GtCO₂.** The pulse-size robustness ladder
  (`julia/diag_pulse_size_robustness.jl`, verified twice) shows the per-ton **median is robust
  to 0.7–2.2% over 0.03–1 GtCO₂**, but there is **genuine large-pulse nonlinearity** (+9–20% at
  10 GtCO₂, +42–101% at 30). **The canonical pulse tables were run at 10 GtCO₂ and overstate the
  per-ton median by ~9–20%.** Rerun at ≤1 GtCO₂ (0.3 or 1). Never quote the per-ton MEAN
  (90–111% ladder spread, non-monotone). Note the median UNDER-states fast dynamics (tip
  fraction never hits 50%, mean/median 11–18×) — for a fat-tail-inclusive number use the
  Lemoine-Traeger `P(tip)·ΔSLR_tip` decomposition (mimibrick-quirks #11), not the mean. Memory
  [[project-dais-fastdynamics-quantization]].
- **A2. Free λ, `ais_γ`, `ais_κ` under their EXISTING paleo marginals.** These are FIXED at the
  **medoid** (biased hot for λ, κ in the pulse-amplifying direction) while their paleo marginals
  already sit in `outputs/param_priors.csv`: `antarctic_lambda` 0.0104±0.0036, `antarctic_gamma`
  2.794±0.929, `antarctic_kappa` 0.0656±0.0135. They are just not in the `FREE` block of
  `calibrate_mcmc_ext.jl`. **λ dominates the 150-yr pulse number and currently carries ZERO
  reported uncertainty** — this is the single biggest unstated assumption in the work. Freeing
  them propagates real uncertainty and de-biases the medoid (λ 0.0137→0.0104). Caveat: they are
  observationally unidentified (historical T never triggers the threshold), so freeing them
  moves/widens the headline and the marginals will mix trivially (they just sample the prior) —
  which is fine. `temperature_threshold` is ALREADY free and paleo-tight (N(−15.61, 0.435)).
- **A3. Fix the Dangendorf label** (§2) and audit the two downstream weight scripts.

### TIER 2 — real value, days

- **A4. Reparameterize the DAIS runoff line to (T_on, `ais_c`).** `h0` and `c` enter ONLY as
  `hR = h0 + c·T_ant`, so `T_on = −h0/c` is the identified direction (posterior r(h0,c)=**0.9997**).
  The fitted posterior switches Antarctic surface runoff on at GMST **+0.62 °C** (~year 2000) vs
  +2.5 °C (Shaffer DAIS) / ~+7.5 °C (Kittel 2021) — i.e. the calibration buys the modern AIS loss
  GRACE-FO demands through a mechanism that is observationally ~zero (real loss is Amundsen-Sea
  dynamic), and it **flips the sign of the modelled 2026→2100 AIS trend** across the ridge.
  Fixes a physical bias AND removes a degeneracy.
- **A5. One SMB likelihood term** on the model's own `β_total` (1979–2008 mean) vs Rignot 2019.
  Posterior SMB=1772±505 and discharge=1916±509 Gt/yr while their **difference** is pinned to
  −145±15 (34:1) — the textbook input–output degeneracy, exactly where `ais_iceflow0` lives.
  **Marcus chose Rignot** (2098±133 Gt/yr) as the central value. Two things to handle explicitly:
  (i) **AREA CONVENTION** — Rignot is grounded Antarctica (12.295e6 km²), DAIS is an idealised
  π·R₀²=10.92e6 km² disc → ×0.888 → 1863±118; wrong convention injects ±15% into `ais_precip0`
  and the pulse. (ii) Rignot's ±133 is model spread, not measurement error — consider Mottram
  2021's multi-model SMB spread for the σ. Land A4 before A5 or the SMB target absorbs the
  spurious runoff.
- **A6. Replace the fixed GMST→Antarctic temperature map** (`ais_temperature_coefficient/intercept`,
  hard-coded 0.8365/15.42, zero uncertainty) with CMIP6 transient polar amplification (~0.95 vs
  the current equilibrium-implied 1.196 → the current map is ~26% high, which fires the
  threshold crossing early and inflates the pulse). Either propagate the regression s.e. (safe)
  or reparameterize `amp = 1/coef ~ N(1.0, 0.2)` (the sd 0.2 is a judgement call). **Highest
  single leverage on the 100/150-yr pulse** per the future-only survey. Methodological choice — §5.

### TIER 3 — structural / larger

- **B1. Diagnose the glacier pulse-marginal deficit.** BRICK GSIC marginal is **5.5× below
  GlacierMIP2 @2100, 8.7× @2150, and DECREASING** while everything else rises; the glacier block
  is railed on 3 bounds at once (`gic_a` floor, `gic_b` ceiling, `gic_T_lia` at −1.00). Bug-first
  per project discipline: paired sanity battery on the glacier component in isolation before
  invoking saturation physics. If a bug, it raises the total CO₂ marginal ~29% @2100 and shifts
  the CH₄-vs-CO₂ crossover (glaciers respond fast → weight CH₄). **Do NOT retune τ to match
  GlacierMIP2** — that imports another model and destroys the FACTS independence.
- **B2. Fix the DAIS annual-step integrator** (root cause of the pulse quantization). The
  disintegration trigger `antarctic_icesheet_component.jl:180` is a hard annual step. The
  ≤1-GtCO₂ recompute (A1) is the workaround; sub-annual crossing detection is the fix. Only worth
  it if the median-at-≤1-GtCO₂ workaround proves insufficient.
- **B3. Empirical-marginals + copula geometry prior** (replaces the truncated-MvNormal). Four of
  the 7 geometry marginals are indistinguishable from uniform; the truncated Gaussian is
  misspecified there. Defensibility, not mixing — expect R̂ to look WORSE. Precompute CDF splines
  (it sits in a 2e6-iteration inner loop).
- **B4. Geometry-as-mixture** (the structural fix for the ridge if A4/A5 don't lift ESS): draw K
  geometry vectors from the DAISfastdyn ensemble, run the 28-param chain conditional on each
  (that configuration mixed), combine with bridge-sampling weights. Embarrassingly parallel;
  K=64 ≪ 38M iter/chain. Report effective-K.

### REJECTED (with reasons — do not revisit without new argument)

- **Re-adding IMBIE/Dyurgerov rate constraints** — the posterior already pins net AIS balance to
  ±15 Gt/yr, tighter than IMBIE's own ±26; Marcus's 2026-06-13 drop is confirmed more strongly.
- **AR6/FACTS/ISMIP6/LARMIP as a *likelihood* or *output* constraint** — circular (same obs) and
  destroys the FACTS cross-check. Process priors on **unidentified parameters** (λ, γ, κ via
  Schoof/CMIP6/paleo) are fine; constraining the **output** (2100 AIS, the pulse) is not. This is
  the bright line for the methods section (see §6).
- **DP16/DP21 for λ, Bamber19 SEJ, Garbe hysteresis, ISMIP6 melt for `ais_α`, `te_α` revision,
  budget-closure term, GRACE regional mascons, Kopp Common Era, linear reparameterization** —
  each rejected in the surveys; see the future-only + general workflow outputs for the specific
  reason if any is revisited.

---

## 4. The independence rule (for the methods section, verbatim-usable)

A process-derived prior is admissible on a parameter **only where its source is a governing
equation, a physical scaling law, or an observational stream disjoint from the calibration
likelihood** (Frederikse/GRACE-FO/GlaMBIE). It is **inadmissible where the source is a sea-level
projection from the same ice-sheet-model family that constitutes the independent cross-check**
(ISMIP6, LARMIP, DeConto, FACTS emulators). Unidentifiability does NOT buy cross-check
independence: because BRICK's 100–150-yr AIS response is ≈ λ·(t−t_cross), drawing λ's prior from
DeConto/FACTS would make a later FACTS agreement partly tautological *even though the data cannot
identify λ*. Hold the fast-dynamics terms on **paleo** priors; use process projections only as a
displayed sensitivity bracket. The clean process-prior candidates: **Schoof 2007 → `ais_γ`**
(analytic grounding-line exponent, γ≈3.75–4.0), **CMIP6/Clausius-Clapeyron → `ais_κ`** (~5.5%/K),
**CMIP6 polar amplification → the temperature map**, **Bassis & Walker 2012 → λ upper truncation**
(fracture-mechanics cliff ceiling). All three that overlap the paleo marginals AGREE with them —
that three-way agreement is itself a reportable robustness result.

---

## 5. Decisions pending for Marcus (do NOT resolve silently)

- **M1. Acceptance/naming.** Is SLR-level R̂ (1.003/1.004, over-dispersed) the accepted
  convergence criterion? If yes, rename `parameters_subsample_brick_mengel_ext_NOTCONVERGED.csv`
  to a canonical "accepted-on-deliverable" path and point downstream drivers at it. If no (hold
  for parameter-level), the fix is B4 (mixture), not more iterations.
- **M2. Recompute the pulse headline at ≤1 GtCO₂** (A1) — the 10-GtCO₂ tables are ~9–20% high.
- **M3. The "total" likelihood term** now that it's known to be Frederikse, not Dangendorf: drop
  it pre-2018 and keep only 2019–2024 NOAA STAR / relabel as budget-closure / fetch the real
  Dangendorf 2024 ESSD (which imports a different 1930–1970 trend — not a silent bug fix).
- **M4. Free λ/γ/κ** (A2) — more honest but moves and widens the headline.
- **M5. Temperature-map amplification** (A6) — paleo-equilibrium 1.196 vs CMIP6-transient ~0.95;
  the sd is a judgement call. Could move "82% crossed by 2100" to a minority.
- **M6. Branch home** (carried from 2026-07-18): `brick-mengel-vnext` vs moving the calibration
  drivers into the MimiBRICK-FM repo (now canonical for the Mengel model).
- **M7. Fix or flag the broken fork `calibrate_mcmc_mengel.jl`** to Tony (carried over).
- **Deferred MCS notes:** JOSS paper for BRICK-FM alongside the pulse paper?; switch table
  horizons to 100/150-yr-from-emission rather than calendar 2100/2150 (the pulse-ladder driver
  already computes horizon-after-pulse = 2130/2180; the older tables do not).

---

## 6. Non-obvious state / traps (each cost real time this session)

- **`temperature_threshold` is already free + paleo-tight** (N(−15.61, 0.435)), NOT N(−15, 5).
  (I stated the wrong prior mid-session; corrected.)
- **`ais_precipitation₀` is LOG-space** in MimiBRICK v2.0.0 (component computes
  `exp(ais_precipitation₀)`); geometry rows use `islog=false` with a log-space θ. `islog=true`
  double-logs. Paleo prior stores precip in log space to match.
- **`fair_mean_*_ssp245.csv` ≠ `*_ssp245harm.csv`** — the former is RCMIP-native, the latter the
  harmonized Smith-historical splice that matches the pulse driver's emissions. Not
  interchangeable for calibration (they differ in the fit window). Build the harmonized one with
  `build_fair_mean_v145.py --emissions-file … --tag ssp245harm`.
- **Effective λ ≠ nominal λ.** Disintegration is normalized by a hard-coded 24.78e15 m³, not the
  model's own V₀ (~2.86e16), so effective SLE rate ≈ 0.92·λ — and since v-next frees the
  geometry, V₀ (hence effective λ) now varies per draw even while λ is nominally fixed. "λ is
  fixed" is not true in SLE units.
- **`postprocess_mcmc_ext.jl` globs `chain_ext_seed*` with `TAG="ext"`** — any stray non-current
  chain in `outputs/mcmc/` gets silently mixed. Quarantine old chains before a new run.
- **Over-dispersed starts** (`--overdisperse`) read `outputs/mcmc/overdispersed_starts.csv` (4
  rows at `ais_iceflow0` quantiles). Random jitter FAILED (200/200 non-finite logposterior) —
  the starts must be real posterior draws.
- **The machine is swap-bound** (18 GB swap, load ~12). Full 4×2M chain reads corrupt; always
  read chains column-selectively. Runs take ~4.5 h for 4×2M under `caffeinate -i`.

## 7. Quarantine ledger (nothing deleted — provenance preserved)

| dir under `outputs/quarantine/` | what |
|---|---|
| `20260718_pre_vnext_28param_ext/` | Jun-13 28-param `ext` posterior (superseded, not bugged) |
| `20260718_vnext_run1_notconverged/` | run 1 (4×500k) |
| `20260718_vnext_run2_notconverged/` | run 2 (4×1M) |
| `20260718_vnext_NOTCONVERGED_subsample/` | non-converged subsamples written to canonical path |
| `20260719_sigma_reref_bug/` | pre-σ-fix targets + run-3 chains built on them |
| `20260719_rebaseline_falsely_certified/` | the subsample the buggy gate wrongly blessed |

## 8. Key files

| file | role |
|---|---|
| `julia/calibrate_mcmc_ext.jl` | v-next calibration (35 params, `--overdisperse`) |
| `julia/postprocess_mcmc_ext.jl` | R̂/ESS + convergence-gated subsample write (bugs fixed) |
| `julia/diag_slr_convergence_by_chain.jl` | SLR-level convergence (the acceptance criterion) |
| `julia/diag_pulse_size_robustness.jl` | pulse-size ladder (A1 evidence) |
| `julia/brick_mengel.jl` | model build (`build_brick_mengel`, `precip_log=true`) |
| `python/prep_recalib_targets_ext.py` | targets (σ bug fixed) |
| `MimiBRICK.jl/calibration/compute_paleo_geo_prior.jl` | geometry joint paleo prior |
| `outputs/param_priors.csv` | all priors incl the unused paleo λ/γ/κ marginals (A2) |
| `MimiBRICK.jl/.../DAISfastdyn_calibratedParameters_gamma_29Jan2017.nc` | 16-param paleo ensemble (7 used, λ/Tcrit/γ/κ available) |

**Suggested first action next session:** M1 + M2 are the cheapest high-value moves (accept/name
the posterior, recompute the pulse headline at ≤1 GtCO₂). Then A2 (free λ/γ/κ under paleo) as the
first physics improvement, since it's the largest unstated assumption and the priors already
exist. Confirm the pending decisions with Marcus before running the next 4.5-h calibration.
