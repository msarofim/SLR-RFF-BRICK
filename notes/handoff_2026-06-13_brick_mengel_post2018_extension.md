# Handoff — BRICK-Mengel post-2018 multi-component extension + figure rework

**Date:** 2026-06-13 · **Repo:** `SLR-RFF-BRICK`, branch `brick-v2-precip-shim`
(notes live in `FaIRtoFrEDI/notes/`). **Env:** Julia `julia_v2/` (MimiBRICK v2.0.0,
juliaup 1.12); Python `~/climate-env`. **Self-contained resume:** read this +
`~/.claude/CLAUDE.md` + prior handoff `notes/handoff_2026-06-13_brick_mengel_postpred_projections.md`
+ memories `project_brick_mengel_post2018_extension`, `project_brick_mengel_postpred`,
`reference_mengel2016_glacier_model`, `project_fair_version_distinction`, `mimibrick-quirks` skill.

---

## 0. TL;DR
Resolved the open question from the prior handoff (extend AIS past 2020) AND, per Marcus's
expansion, extended **all** SLR components past Frederikse 2018, re-fit, checked, and reworked
the figures for Tony Wong. **Extending barely moves the physics** (ais_ocean_temperature₀ +0.013);
GMSL@2100 drops only 0.8–3.2 cm, ~all via AIS; the high-forcing overshoot vs AR6 persists. All
committed (8 commits, `180aa31`…`3241aa0`). The Greenland increase/pause/increase disconnect was
investigated (§4.1): **candidate 1 (re-tune within SIMPLE) was tested and FAILS structurally** — even
a GIS-only fit with bounds widened past the priors can't hold the mid-century pause or delay the
resumption to ~2000. The other three fixes lack Mengel-grade provenance → **recommend STOP** with the
substantial improvements already in hand (Marcus lean 2026-06-13).

## 0.5 The updated BRICK — what it is, vs stock BRICK 2.0
**"BRICK 2.0" (the comparison baseline)** = stock MimiBRICK **v2.0.0**: single-reservoir GSIC glacier
arm, stock LWS, run on the OLD joint posterior (`parameters_subsample_brick.csv`). FaIR-forced, its
AIS massively over-accelerates in the hindcast — the v2.0.0 pathology (see `project_brick_v2_obsdriven_interface`).

**The updated BRICK ("BRICK-Mengel")** = MimiBRICK v2.0.0 base with four upgrades:
1. **Mengel 2016 two-timescale glacier component** replaces single-reservoir GSIC — temp-dependent
   equilibrium S_eq(ΔT)=a·(1−exp(−b·ΔT)) with fast+slow relaxation (`glaciers_mengel`; fixes the
   commit-everything pathology). See `reference_mengel2016_glacier_model`.
2. **precip_log shim** — restores v1.0.1-bit-identical AIS precip reparam (exp(precip0)) on the v2.0.0
   base. See `project_brick_v2_obsdriven_interface`.
3. **Full MCMC recalibration** against FaIR-mean GMST forcing + Frederikse 2020 per-component obs
   (1900–2018), now EXTENDED post-2018 with multi-method products (GRACE-FO AIS/GIS, GlaMBIE GSIC,
   NOAA steric TE, NOAA STAR total) — 4×500k, **27/28 R̂<1.05**.
4. **Frederikse-LWS budget** (not stock LWS) for the total.

The **graphics comparing the updated BRICK against stock BRICK 2.0** are listed in §3 (chiefly the
`postpred_ext_components.png` hindcast, which overlays both); the §0.5→§3 cross-reference is the
"four upgrades" Tony-framed story.

## 1. What got done (all committed on `brick-v2-precip-shim`)
1. **Data acquisition (`180aa31`)** — all reconciled multi-method products, in `data/observations/raw/`
   (see `raw/README_modern_extensions.md`). GRACE-FO JPL mascon AIS+GIS (→2026, needs Earthdata
   `~/.netrc` — **Marcus set one up**, machine `urs.earthdata.nasa.gov`), GlaMBIE 2025 glaciers (→2023),
   NOAA NCEI 0-2000m thermosteric (→2025), NOAA STAR total (→2024), IMBIE 2023 AIS+GIS (cross-check only).
2. **Splice + extended targets (`180aa31`)** — `python/prep_recalib_targets_ext.py` → `outputs/recalib_targets_ext.csv`
   (+ `_sources.csv` provenance sidecar, + splice diagnostic PNG). Each modern product → cm SLE,
   offset-matched (level shift, no rescale) to Frederikse over an overlap window, then Frederikse
   1900-2018 + modern to each own end-year. IMBIE agrees with GRACE splices <0.07 cm. Post-2018
   increments (cm): AIS +0.07 (pause), GIS +0.38, GSIC +0.60, TE +1.16, total +1.59.
3. **Re-fit (`636f849`, scripts; results `2a2652b`)** — `julia/calibrate_mcmc_ext.jl`,
   `run_mcmc_ext_local.sh`, `postprocess_mcmc_ext.jl`. **Decisions (Marcus): NOAA STAR extends the
   total; BOTH point terms (IMBIE ΔAIS, Dyurgerov ΔGSIC) DROPPED** (extended series now constrain the
   modern rate). Per-series AR(1) windows; Y1 1850→2026 (same forcing — fair_mean_*.csv already runs
   to 2301). **4×500k → 27/28 R̂<1.05** (straggler antarctic_alpha 1.052/ESS2124, accepted). Baseline
   `calibrate_mcmc.jl` LEFT INTACT for the A/B.
4. **Obs/historical check (`2a2652b`)** — `julia/posterior_predictive_ext.jl` + figure (see §3).
5. **High-T glacier melt check (`81d607f`, `2a2652b`)** — `python/verify_mengel_hightemp_melt.py [TAG]`.
   Marcus asked to confirm Mengel still melts MOST glaciers at high T. **PASS** both posteriors:
   committed S_eq/a = 88%@1.3°C, 99%@4°C, ~100%@7°C; gic_a 0.34-0.36 m in Farinotti range. Realized
   melt lags (gic_tau_slow ~589 yr): 62%@2100, 77%@2300 under SSP5-8.5 — correct slow large-glacier response.
6. **Projections + figures (`2a2652b`, `b2d0bbb`, `1c85275`, `1614c14`, `3241aa0`)** — see §3.

## 2. Headline result — extending barely moves the physics
| param | baseline | extended | Δ |
|---|---|---|---|
| ais_ocean_temperature₀ | 0.981 | 0.994 | **+0.013** |
| anto_alpha | 0.405 | 0.354 | −0.051 |
| te_α | 0.164 | 0.159 | −0.005 |
| gic_a | 0.342 | 0.364 | +0.021 |

GMSL@2100 LOWER by 0.8 cm (SSP1-1.9) → 3.2 cm (SSP5-8.5), **~entirely via AIS** (ΔAIS −1.0 to −2.6 cm).
High-forcing overshoot vs AR6 PERSISTS (SSP5-8.5 116.5→113.4 vs AR6 77) — MICI-threshold-driven,
unconstrainable by ~7 yr. **Obs check:** total fits NOAA STAR to −0.01 cm@2024; **TE overshoot NOT
resolved** by NOAA steric (+0.51 cm@2025); **AIS pause not reproduced** (warming-driven model rises
through the plateau, +0.11@2025); GSIC tracks GlaMBIE accel. 120 yr of history dominate the ~7 yr of new data.

## 3. Key files (this session)
- **Prep/data:** `python/prep_recalib_targets_ext.py`; `data/observations/raw/README_modern_extensions.md`
  + the raw products; `outputs/recalib_targets_ext.csv`, `_ext_sources.csv`, `_ext_splice_diagnostic.png`.
- **Calibration:** `julia/calibrate_mcmc_ext.jl`, `julia/postprocess_mcmc_ext.jl`, `run_mcmc_ext_local.sh`.
  Posterior `data/MimiBRICK/parameters_subsample_brick_mengel_ext.csv` (untracked per data/MimiBRICK/*
  policy — regenerable). `outputs/mcmc/adapted_cov_ext.csv` (proposal seed). 286 MB×4 chains gitignored.
- **Comparison-to-BRICK-2.0 graphics:** `julia/posterior_predictive_ext.jl` + `python/plot_postpred_components_ext.py` →
  `outputs/postpred_ext_components.png` — the **headline updated-BRICK-vs-stock-BRICK-2.0 hindcast figure**
  (per-component + total, obs provenance shown, stock BRICK 2.0 overlaid per §0.5, 1920 start,
  re-ref 1970-2020, Tony framing); the stock-2.0 overlay curves come from
  `julia/posterior_predictive_oldbrick.jl` → `postpred_oldbrick_components_timeseries.csv`
  (stock single-reservoir glacier on the OLD posterior, FaIR-forced).
  `python/verify_mengel_hightemp_melt.py` → `mengel_hightemp_melt{,_ext}.png`;
  `julia/project_ssps_2100_mengel.jl` (+optional TAG arg) → `outputs/proj_ssps_mengel_ext_*` +
  `python/plot_ssp_projections_mengel.py [TAG]` → `ssp_projections_2100_mengel_ext.png`;
  `python/plot_ssp_projections_ext_compare.py` → `ssp_projections_ext_compare.png` (A/B).

## 4. NEXT STEPS (prioritized)

### 4.1 Greenland-module disconnect — candidate 1 TESTED → STRUCTURAL; recommend STOP (Marcus 2026-06-13)

**RESULT (2026-06-13): candidate 1 fails — the SIMPLE/Bakker structure cannot reproduce the
increase/pause/increase shape, confirming Marcus's prior.** Ran a GIS-ONLY fit
(`julia/fit_greenland_only.jl`): freed just the 5 Greenland params, **widened their bounds well past
the production priors** (a∈[−3,−0.001], b∈[3,9], α,β∈[1e-6,1e-2], v₀∈[5,12]), fit GIS in isolation
(no competition from AIS/GSIC/TE/total) to the extended target, same FaIR-mean GMST forcing. Even with
that maximal freedom the best fit (`outputs/greenland_only_fit_ext.{csv,png}`, params in `_params.csv`):
- **misses the mid-century pause** — model melt rate 0.29 cm/decade @1975 vs obs **0.09** (it melts
  straight through the plateau);
- **shows no delayed resumption** — model rate climbs monotonically with cumulative warming (0.26→0.29→
  0.42→0.64 cm/dec at 1965/75/95/2010), already accelerating by 1995 while obs is still 0.16; it resumes
  with the ~1970 warming, **~30 yr too early**;
- had to **rail a, b, v₀ OUTSIDE the physical priors** (a=−1.01, b=8.99=cap, v₀=9.98 vs prior 7.56) and
  STILL only reaches RMSE 0.69 cm. The melt rate just tracks GMST (see `_ext.png` bottom panel).
This is the predicted structural failure: a one-pole relaxation toward a linear-in-T equilibrium is a
low-pass filter of T — its melt rate is monotonic in cumulative warming, so it **cannot** hold a
mid-century pause and then resume ~30 yr after warming resumes. No tuning within SIMPLE escapes it.

**RECOMMENDATION → (c) leave the Greenland module as-is; STOP here (Marcus lean 2026-06-13).** The three
structural fixes that *could* capture the shape — (2) two-timescale relaxation, (3) nonlinear/threshold
equilibrium, (4) lagged-T driver — **lack the provenance the Mengel correction had**: Mengel 2016 was a
published, physically-derived, separately-calibrated glacier emulator we could port wholesale
(`reference_mengel2016_glacier_model`); there is no equivalent off-the-shelf Greenland parameterization,
so 2/3/4 would each be a **bespoke, self-derived component** needing its own physical justification and
calibration (and the ~30-yr lag still wants a cited mechanism — response-time vs threshold — before
committing). Given the recalibration already delivered substantial improvements and GIS only undershoots
by −0.23 cm@2025, this is a good place to stop. **Files this session:** `julia/fit_greenland_only.jl`,
`python/plot_greenland_only_fit.py`, `outputs/greenland_only_fit_ext.{csv,png}`, `..._params.csv`,
`outputs/greenland_only_fit.log`. (If revisited, the test harness + the candidate menu below are the
starting point.)

---

**Observation to capture:** GIS mass balance shows **increase → pause → increase** — early-20th-c melt
(~1920s-40s), a mid-century pause/near-balance, then a strong resumption that **begins ~2000 and
accelerates**. This roughly parallels GMST (warm to ~1940, mid-century hiatus, resumed warming ~1970)
**BUT the melt resumption (~2000) lags the warming resumption (~1970) by ~30 yr.** That ~30-yr lag is
the key feature — and a hint about the physics (ice-sheet thermal/dynamic response time? a threshold/
albedo-meltwater feedback that only engages ~2000? cumulative-warming trigger?).

**Current module** (`MimiBRICK .../src/components/greenland_icesheet_component.jl`, SIMPLE / Bakker 2016):
- `eq_volume(t) = greenland_a · T(t) + greenland_b`  (equilibrium volume LINEAR in T)
- `τ_inv(t) = (greenland_α · T(t) + greenland_β) · (V/V₀)`  (T-dependent relaxation rate)
- `dV/dt = −(V − V_eq)·τ_inv`  — **single-timescale relaxation toward a linear-in-T equilibrium.**
- 5 free params: greenland_a/b/α/β/v₀. In the ext posterior GIS UNDERSHOOTS obs (−0.23 cm@2025); the
  warming-driven model resumes melt with the 1970 warming (too early) rather than ~2000.

**Scoping question:** can a parameterization capture the increase/pause/increase shape WITH the ~30-yr
resumption lag? Candidates to weigh (pros/cons memo, like the Mengel glacier scoping in
`reference_mengel2016_glacier_model`):
1. Can the **existing 5 params** already do it (e.g. a slow τ giving a ~30-yr lag), or does a single
   linear-equilibrium + single-τ structurally forbid the pause-then-late-resumption shape? **→ TESTED
   2026-06-13, structurally forbidden — see the RESULT block at the top of §4.1.**
2. **Two-timescale** relaxation (fast + slow), directly analogous to the Mengel 2-τ glacier fix — a slow
   reservoir could carry the lagged resumption.
3. **Nonlinear / exponential equilibrium** (like Mengel's `a(1−exp(−bΔT))`) or a **threshold** term so
   melt accelerates only past a warming/temperature trigger (~the level reached ~2000) — physically a
   surface-meltwater/albedo or marine-margin feedback.
4. A **lagged temperature** driver (GIS responds to T smoothed/lagged by ~decades).
**Deliverable:** scoping memo + a quick GIS-only fit prototype; recommend whether to (a) re-tune within
SIMPLE, (b) port a 2-τ / nonlinear-equilibrium Greenland (new component, like glaciers_mengel), or (c)
leave as-is. Watch: don't break the AIS/total joint fit; keep the `update_brick_params!`/precip_log wiring.
Note the parallel asymmetry (warming resumes 1970, melt ~2000) needs a citation for the physical mechanism
before committing to a threshold vs lag interpretation.

### 4.2 Other open items (lower priority)
- **Post-2020 down-weighting sensitivity** — Marcus deferred to "after the equal-weight result." Equal-weight
  effect is only ~1–3 cm, so down-weighting would shrink an already-small effect → **lean SKIP** unless wanted for a writeup.
- **TE overshoot** (+0.51 cm@2025) — unchanged by the extension; separate calibration thread (freed te_α
  over-correcting, absorbed by high-ρ AR(1) noise). Not addressed here.
- **FaIR-label sweep** — audience-facing FIGURE text is fixed (FaIR v2.2.4, v1.4.5 = Smith calibration);
  the "FaIR v1.4.5-forced" shorthand still appears in code comments/docstrings inherited from the original
  drivers. Sweep if source consistency wanted. See `project_fair_version_distinction`.
- **Share branch with Tony Wong** — figures are now Tony-framed (BRICK v2.0.0 → current, four upgrades even).
- Optionally re-fit keeping IMBIE point term (the "drop only IMBIE / keep Dyurgerov" option) if AIS
  identifiability is ever a concern (it converged fine here, so not pressing).

## 5. Non-obvious state / gotchas
- **FaIR version:** model is **FaIR v2.2.4**; "v1.4.5" is the Smith CALIBRATION dataset, not the model.
  Audience-facing labels fixed this session; don't reintroduce "FaIR v1.4.5" as the model version.
- **100k did NOT converge; 500k did.** The first ext run (4×100k, baseline-cov proposal) gave 25/26
  R̂>1.05 with per-chain logpost spread 6–138 — that was slow burn-in from a MISMATCHED proposal, NOT a
  bug. Fixed by seeding 500k from the ext-tuned `adapted_cov_ext.csv`. calibrate_mcmc_ext.jl now prefers
  that file. For any further ext re-fit: run once, let postprocess write adapted_cov_ext.csv, then re-run long.
- **Display baseline ≠ calibration baseline.** Calibration uses 1995-2005; the hindcast FIGURE re-references
  all curves to 1970-2020 for display only (centers the trended components better, per Marcus). The
  posterior_predictive_ext.jl OUTPUT csv is rel 1995-2005; the re-ref is done in the plot.
- **Stock BRICK 2.0 overlay** (= "old-BRICK", §0.5) = stock single-reservoir glacier on the OLD posterior
  (`parameters_subsample_brick.csv`), FaIR-forced; its total uses the stock LWS, not the Frederikse-LWS budget
  the Mengel total uses (~mm difference, noted). Its AIS massively over-accelerates in the hindcast — that's
  the v2.0.0 pathology, expected.
- **Posterior files untracked** (data/MimiBRICK/* gitignored). Regenerate ext posterior via
  `bash run_mcmc_ext_local.sh 500000` (4 chains, ~45-60 min local, ~236 iter/s baseline).
- **project_ssps_2100_mengel.jl** and **plot_ssp_projections_mengel.py** and **verify_mengel_hightemp_melt.py**
  all take an optional TAG arg ("" = baseline, "ext" = extended), backward-compatible.
