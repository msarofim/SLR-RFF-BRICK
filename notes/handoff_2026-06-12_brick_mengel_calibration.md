# Handoff — BRICK-Mengel recalibration: v2.0.0 port → Mengel glacier → MAP → MCMC

**Date:** 2026-06-12 · **Repo:** `SLR-RFF-BRICK` (branch `brick-v2-precip-shim`), some notes in
`FaIRtoFrEDI` (branch `fredi5-migration`). **Env:** Julia `julia_v2/` (MimiBRICK v2.0.0, depot
`edplP`); Python `~/climate-env`. **Self-contained resume:** read this + `~/.claude/CLAUDE.md` +
memories `project_brick_full_joint_calibration`, `reference_mengel2016_glacier_model`,
`project_brick_recalib_central_prototype`, `project_brick_ssp_projection_2100`.

---

## 0. TL;DR
Built a FaIR-forced, modern-obs recalibration of BRICK v2.0.0 with a new temperature-dependent
glacier model, culminating in a **full Bayesian MCMC**. Arc: fixed the v2.0.0 obs-driven port
(precip log-reparam) → diagnosed GSIC structural undershoot → central recalibration + SSP
projections (incl. 10k-ensemble + Dangendorf importance weighting) → ported the **Mengel 2016
glacier** (temperature-dependent equilibrium, fixes commit-everything) with an **LIA-disequilibrium
offset** (simulates committed melt; no forcing split) and a **2-timescale** fast/slow split (closes
the GSIC gap) → **MAP** joint calibration (29 params) → **MCMC** (RAM + AR(1), 28 params).

## 1. The arc (in order, all committed)
1. **v2.0.0 obs-driven port fix** — the +100cm AIS@1900 was the AIS precip LOG-reparam, not OHC;
   `precip_log` shim in `brick_param_updates.jl` reproduces v1.0.1 bit-identical.
2. **GSIC H1/H2 diagnostic** (`python/gsic_recalibration_diagnostic.py`) — glacier UNDERshoots
   historical loss +4σ; structural (melt ∝ T-level, not warming-rate).
3. **Central recalibration** (`julia/recalibrate_central.jl`) — 10-knob MAP-ish; AIS see-saw fixed
   by freeing oceanT0 JOINTLY with anto_α + an IMBIE modern-rate term.
4. **SSP projections to 2100** — central (`project_ssps_2100.jl`) + **10k-ensemble**
   (`project_ssps_2100_ensemble.jl`, FaIR-forced) + **Dangendorf importance weighting** (ESS 598).
   Key: v2.0.0 median runs HIGH vs AR6 for SSP2-4.5+ (median draw crosses DAIS-MICI ~2.7°C).
5. **Mengel glacier** (`julia/glaciers_mengel_component.jl`, swapped via Mimi `replace!` in
   `julia/brick_mengel.jl`) — `S_eq(T)=a(1−exp(−b(T−T_lia)))`, relax `dS/dt=(S_eq−S)/τ`. Fixes the
   commit-to-total-melt pathology (stabilization regression passes). **Disentanglement correction:**
   driven by TOTAL temperature (no anthro/natural split); the early-melt gap is COMMITTED/
   disequilibrium melt, captured by the **LIA offset `T_lia`** (glacier equilibrium ≈ colder LIA),
   NOT a Marzeion "natural budget" (that was retired). **2-timescale** (`f, τ_fast, τ_slow`) closes
   most of the residual: GSIC RMSE 1.31(single-res)→1.04(1τ)→0.60(2τ).
6. **MAP joint calibration** (`julia/calibrate_full_joint.jl`) — 29 free params, prior-regularized
   (priors = post-#93 posterior mean±std + physical glacier); J 135→19.6; AIS/GIS/Steric within obs,
   GSIC RMSE 0.76, MICI held at prior (historical can't constrain it). = the MCMC seed.
7. **MCMC** (`julia/calibrate_mcmc.jl`) — RAM_sample + reproduced `hetero_logl_ar1` (AR(1)); 28
   params (18 physical + 10 AR(1) noise); FaIR-forced; weak DAIS shape FIXED at posterior median,
   `ais_ocean_temperature₀` kept free, `T_lia` to −1.0, LWS-budget uncertainty in the total σ.

## 2. Current state — MCMC RAN + (mostly) CONVERGED
`run_mcmc_local.sh 300000` → 4 chains × 300k iter (acceptance 0.234–0.241 ✓), cov-seeded →
**24/28 params converged** (R̂<1.05, ESS 1200–1800). The 4 stragglers are AR(1) NOISE nuisance
params (rho_ais, sd_gsic, rho_gsic) + antarctic_alpha (R̂ 1.059, borderline) — the PHYSICAL /
projection-relevant posterior IS converged. Posterior `data/MimiBRICK/parameters_subsample_brick_mengel.csv`
(10k), median[5-95]: ais_ocean_temperature₀ 0.96[0.56,1.52] (was frozen 0.72), anto_α 0.42, MICI
−15.6 (prior-held), glacier gic_f 0.55 / τ_fast 56 / τ_slow 605 yr, gic_T_lia −0.98 (rails at −1.0).
**Gotchas fixed (all committed):** RAM_sample needs output_log_probability_x=true (else lp=nothing);
accept_rate via fill(); postprocess readdir not Glob; cov-seeding (empirical posterior cov in
`outputs/mcmc/adapted_cov.csv`) is the key mixing accelerator. Added deps: Distributions,
RobustAdaptiveMetropolisSampler, LinearAlgebra, MCMCDiagnosticTools.

## 3. NEXT STEPS (prioritized)
1. **Verify convergence** (R̂<1.05, ESS>400 per param in `outputs/mcmc/postprocess.txt`). If any
   param not converged → longer chains (`run_mcmc_local.sh 300000`) or more seeds.
2. **Posterior-predictive + sanity**: component bands vs Frederikse/Dangendorf; the 5 climate-modeling
   sanity tests + glacier stabilization on posterior draws.
3. **Re-run the SSP 2100 projection + importance-weighting ensemble** on
   `parameters_subsample_brick_mengel.csv` (adapt `project_ssps_2100_ensemble.jl` to build via
   `build_brick_mengel` + the new posterior) — the headline deliverable: recalibrated SLR projections.
4. **Optional Torch** production (`run_mcmc_torch.sbatch`, cs job array + deploy notes) if a longer/
   bigger run is wanted; compute is small (~236 iter/s) so local is fine.
5. **Share code with Tony** — major FaIR-vs-SNEASY branch from his v2.0.0 paper; he adapts Mengel,
   Dangendorf, and the freed AIS equilibrium T to his own work. No blocking coordination.

## 4. Key files
- Glacier: `julia/glaciers_mengel_component.jl` (2-τ + LIA offset), `julia/brick_mengel.jl` (build+set),
  `python/{calibrate_mengel_glacier.py, glacier_2tau_validate.py}` (standalone fits/validation).
- Calibration: `julia/calibrate_full_joint.jl` (MAP, 29 params), `julia/calibrate_mcmc.jl` (RAM+AR1),
  `julia/postprocess_mcmc.jl` (R̂/ESS/subsample), `outputs/calib_full_joint_params.csv` (MAP = seed),
  `outputs/param_priors.csv` (posterior priors), `python/prep_recalib_targets.py` (targets incl. GIS).
- Projections: `julia/project_ssps_2100{,_ensemble}.jl`, `python/plot_ssp_projections{,_ensemble}.py`.
- Scope: `FaIRtoFrEDI/notes/brick_mcmc_scope_2026-06-12.md`.

## 5. Non-obvious state
- `julia_v2` Project gained 4 deps (above) — committed.
- MAP seed (`calib_full_joint_params.csv`) is the 2-τ, T_lia−1.0, LWS-unc version (re-run after the
  glacier changes). `recalib_central_row.csv` (medoid post_idx 5808) = the base for fixed params.
- The MCMC `FREE` set: oceanT0, ais_α, ais_ν, MICI, anto_α/β, GIS(5), te_α, glacier(a,b,T_lia,f,τf,τs)
  + AR(1) (σ,ρ)×{ais,gsic,gis,steric,dang}. Weak DAIS shape params NOT free (held at medoid).
- AIS still runs high vs AR6 at high forcing via the MICI threshold (a posterior param, unconstrained
  by historical data) — the ensemble carries that uncertainty; not a bug.
- `data/observations/fair_mean_{gmst,ohc}_<ssp>.csv` = FaIR v1.4.5 SSP forcing (`run_fair_ssps.py`).
