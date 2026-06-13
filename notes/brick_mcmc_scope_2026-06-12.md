# Scope — full Bayesian MCMC calibration of BRICK-Mengel

**Date:** 2026-06-12 · **For:** Marcus Sarofim (+ Tony Wong coordination)
**Predecessor:** the MAP point estimate (`SLR-RFF-BRICK/julia/calibrate_full_joint.jl`,
memory `project_brick_full_joint_calibration`) — this MCMC promotes it to a full posterior.
**Read with:** `notes/brick_recalibration_plan_2026-06-10.md`, memory `reference_mengel2016_glacier_model`.

---

## 0. Objective & deliverable
A Bayesian **posterior sample** over the BRICK-Mengel parameters, conditioned on the modernized
obs targets, replacing the central MAP with full uncertainty. Deliverable: a
`parameters_subsample_brick_mengel.csv` (same schema role as Tony's
`parameters_subsample_brick.csv`) that drops straight into the existing FaIR-forced
projection + importance-weighting pipeline (`project_ssps_2100_ensemble.jl`).

## 1. Reuse, don't rebuild — adapt MimiBRICK's `brick` calibration core
MimiBRICK ships the machinery (verified in `src/calibration/`):
- **Sampler:** `RAM_sample` (RobustAdaptiveMetropolisSampler; Vihola 2012), `opt_α=0.234`,
  single adaptive chain, adaptive proposal covariance.
- **Likelihood:** `hetero_logl_ar1(residuals, σ, ρ, ϵ)` — heteroscedastic **AR(1) per component**
  (also `hetero_logl_car1` for irregularly-sampled series). This is the key piece the MAP's
  point-subsampling only crudely approximated — it properly accounts for the autocorrelation in
  each component's residual series.
- **Log-posterior:** `construct_brick_log_posterior(run_brick!; ...)` — the BRICK-only config,
  **externally forced by temperature + ocean heat** = exactly our FaIR-driven setup.
- **Data:** `load_calibration_data(...)`; **diagnostics:** MCMCDiagnosticTools.

We adapt four things: forcing (FaIR), glacier component (Mengel), targets, priors.

## 2. Parameters (~38–40)
**Physical (from the MAP, 27):** 22 AIS/anto/GIS/TE + freed `ais_ocean_temperature₀` + the 4 Mengel
glacier params — see `outputs/calib_full_joint_params.csv` for MAP values (= chain start).
**Glacier additions to close the GSIC gap (Marcus-requested):**
- **2-timescale glacier** (a single τ can't be fast-early + slow-modern). Split the equilibrium
  into a fast (committed) and slow (modern) mode:
  `S = S_fast + S_slow`, `dS_fast/dt = (f·S_eq − S_fast)/τ_fast`,
  `dS_slow/dt = ((1−f)·S_eq − S_slow)/τ_slow`, `S_eq(T)=a(1−exp(−b(T−T_lia)))`.
  New params: `f` (fast fraction), `τ_fast`, `τ_slow` (replaces single `τ`). +2 params.
- **Widen `T_lia` prior** to allow regional/seasonal LIA amplification (glaciers see amplified
  signals): e.g. μ=−0.4, σ=0.3, bound [−1.0, −0.1] (vs the MAP's [−0.8,−0.1]).
**AR(1) noise (calibrated, ~10):** per component (AIS, GSIC, GIS, Steric, total GMSL) a
`(σ_c, ρ_c)` pair — BRICK calibrates these jointly with the physical params.

## 3. Likelihood & targets
Per-component **AR(1)** log-likelihood, summed over components, on the FaIR-forced BRICK-Mengel run
(1850–2018), re-ref 1995-2005:
- Frederikse 2020 **AIS / Glaciers / GIS / Steric** trajectories (1900–2018) — per-year obs σ from
  the bands (use `hetero_logl_ar1`).
- **Dangendorf 2024** total GMSL (1900–2018), with the **Frederikse-TWS LWS budget** added to the
  modeled total (LWS stays an external budget; OHC is a forcing input).
- Modern-rate constraints folded in as short series / point terms: **IMBIE ΔAIS(1992–2017)**,
  **Dyurgerov ΔGSIC(1961–2003)**.

## 4. Priors
Match the MAP: post-#93 posterior **mean±std** for the 22 AIS/anto/GIS/TE params (informative —
this is what keeps the ~40-D problem identifiable and the DAIS shape params from wandering);
physical priors for the glacier (`a`≈glacier volume 0.32–0.55, `b`≈Mengel 0.25–1.0, `T_lia`
widened, `f`∈[0,1], τ_fast∈[5,80], τ_slow∈[80,800]); weak prior on `ais_ocean_temperature₀`;
BRICK's standard weak/uniform priors on the AR(1) `(σ,ρ)`. Keep BRICK's **joint AIS prior**
(`joint_antarctic_prior=true`) to reject unphysical DAIS parameter combinations.

## 5. Sampling, convergence, compute
- **≥4 independent chains**, seeded at the MAP + dispersed perturbations; initial proposal
  covariance from the MAP curvature (finite-difference Hessian) for fast adaptation.
- Length ~3–5×10⁵ iter/chain; burn-in ~30–50%; thin to a ~10k-member subsample.
- **Convergence:** Gelman–Rubin R̂ < 1.05 every param, ESS > ~400/param, trace + acceptance (~0.234)
  checks (MCMCDiagnosticTools).
- **Compute (Torch `cs`, no time cap):** BRICK ~175 runs/s single-core → ~10 min per 10⁵ iter;
  4 chains × 4×10⁵ on 4 cores ≈ **~4–6 h wall**. Comfortable on `cs`.

## 6. Validation (before any headline posterior)
- **Posterior-predictive** component bands vs Frederikse + Dangendorf (must envelope obs).
- The full **5-test climate-modeling sanity battery** + the glacier **stabilization regression**
  on posterior draws (remnant survives; no commit-everything).
- Cross-checks: vs the MAP, vs Tony's `parameters_subsample_brick` (AIS/GIS/TE should be consistent
  where unchanged), and the importance-weighting **ESS** on each sampled axis.

## 7. Ordered build steps
1. `load_calibration_data` → our targets (Frederikse 4 components + Dangendorf + IMBIE + Dyurgerov),
   per-component obs σ; FaIR GMST+OHC forcing loader.
2. `run_brick_mengel!` (FaIR-forced, Mengel-2τ glacier) + `construct_brick_mengel_log_posterior`
   (per-component AR(1) + priors + joint-AIS prior).
3. Parameter vector + bounds/priors + MAP-seeded initial covariance.
4. RAM multi-chain driver + Torch SLURM (`cs`); R̂/ESS diagnostics.
5. Posterior-predictive + sanity validation; subsample → `parameters_subsample_brick_mengel.csv`.
6. Re-run the SSP projection ensemble + importance weighting on the new posterior.

## 8. Decisions to confirm before building
- **2-timescale glacier** (adds `f, τ_fast, τ_slow`; the lever to close the GSIC undershoot) — in?
- **`T_lia` prior width** (how much regional LIA amplification to allow).
- **AIS param set:** calibrate all DAIS params (prior-regularized) vs fix the weakly-constrained
  ones at Tony's posterior to cut dimensionality (~40 → ~25).
- **Coordinate with Tony:** the AR(1) likelihood + RAM harness is his; align so the result is
  mergeable with his BRICK posterior workflow and the MimiBRICK v2.0.0 publication.

## 9. Risks / effort
- **Risk:** ~40-D convergence (mitigate: informative priors + MAP-seeded covariance + multi-chain),
  2-timescale glacier identifiability (the fast/slow split may trade off with `T_lia`/`a` — the
  modern Dyurgerov + early Frederikse anchors should separate them), AR(1) likelihood correctness
  (reuse Tony's tested `hetero_logl_ar1`).
- **Effort:** ~2–4 days to build + validate the harness; ~4–6 h compute on `cs`. Paper-track, not
  regulatory (keep Tony's published posterior for EPA/vehicle comparison).
