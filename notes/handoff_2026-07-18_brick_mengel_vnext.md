# Handoff — BRICK-Mengel v-next recalibration (2026-07-18)

Self-contained: a fresh session should be able to pick up from this + `CLAUDE.md` +
memory `project_brick_mengel_vnext_recalib`.

---

## 1. What we were doing

Executing the **BRICK-Mengel v-next recalibration** that Marcus flagged as a blocker
("a key issue we should address before continuing with all this work"). The MAGICC-vs-FaIR
× 3-SLR-model comparison tables are complete but rest on the June-13 posterior; v-next
updates that posterior before the pulse paper builds on it.

**Marcus's decisions, already made:**
- IMBIE 1992–2017 AIS-rate point constraint → **drop**
- Phase 1 and Phase 2 → **do both together**
- Geometry prior → **Strategy B** (joint paleo-covariance prior)
- "Make sure the earlier calibrate has the updated Mengel and Antarctic equilibrium value" → **verified**

---

## 2. Decisions made this session, and why

### Pivot off the fork's calibrate script
`MimiBRICK.jl/calibration/calibrate_mcmc_mengel.jl` (PR-2 / brick-fm) **does not run**:
it calls unexported MimiBRICK internals unqualified (`get_model`, `set_external_forcing!`,
`_apply_mengel_defaults!` — working code uses `MimiBRICK.get_model`), and separately crashes
on `Float64.(Vector{Union{Missing,Float64}})` because the extended targets gained trailing
missing years after it was written. My inference: refactored for the PR, never re-run.
My edits to it were **reverted** (`git checkout`); it is back at PR state.

Pivoted to **`SLR-RFF-BRICK/julia/calibrate_mcmc_ext.jl`**, verified to already carry:
Mengel emulator (`build_brick_mengel`, 6 gic params free, `precip_log=true`), freed
`ais_ocean_temperature₀` (μ=0.72, σ=0.50, bounds 0.50–2.00), point terms already dropped,
NaN handling for extended targets.

### Strategy B implementation (28 → 35 params)
Freed the 7 DAIS geometry params (`ais_μ`, `bedheight₀`, `slope`, `iceflow₀`,
`precipitation₀`, `runoffline_snowheight₀`, `c`), previously fixed at the prior medoid.

- Prior built by `MimiBRICK.jl/calibration/compute_paleo_geo_prior.jl` from the
  DAISfastdyn paleo ensemble → `SLR-RFF-BRICK/outputs/paleo_geo_prior.csv`.
- Stored **standardized** — `MvNormal(0, C)` on `z=(θ−μ)/sd`. **Why:** scales span
  1e-4…1e3, so `cond(Σ)=5.2e13` vs `cond(C)=2.75`. Bounds = paleo min/max.

### Forcing switch → SSP2-4.5 harmonized
`fair_mean_{gmst,ohc}_ssp245harm.csv`, so calibration sits on the **same** forcing as the
pulse projections (`fairtable7_v145_pulse.py` uses `emissions_v145_ssp245_harmonized.csv`)
and matches this script's `build_brick_mengel(ssp="ssp245")`.
Both splices share the Smith historical → 1850/1900/1971 **bit-identical**; differ only
over ~2020–2026 of the fit window (mean |ΔGMST| 0.03 °C) and in the tail.
`build_fair_mean_v145.py` was parameterized (`--emissions-file/--tag/--scenario-label`) so
this does **not** overwrite the canonical RFF-SP `fair_mean_{gmst,ohc}.csv`.

---

## 3. Non-obvious traps (each cost real time)

1. **`precipitation₀` is LOG-space.** MimiBRICK v2.0.0's AIS component computes
   `exp(ais_precipitation₀)` (default `log(0.37)`); `setp!` applies `log()` only when
   `islog=true`. Geometry rows therefore use **`islog=false`** with log-space θ — `islog=true`
   would log twice.
2. **θ0 must start geometry at the MEDOID, not the paleo prior mean.** The naive prior-mean
   start put `logpost(θ0)` at −5636 vs the 28-param baseline's −771 and collapsed acceptance
   to 0.022. Cause: medoid `precip₀` 0.94 m/yr vs paleo mean 0.40 (**2.3×**), `iceflow₀` −1.4 sd.
   Isolated by running the original 28-param script at matched iterations/seed as a control
   (acceptance 0.192). With medoid start: −779, acceptance 0.196.
   **A geometry proposal-scale fix was tried first and REFUTED** — it moved acceptance only
   0.022 → 0.029. `GEO_PROP_SCALE` is retained as a sane default, not as the fix.
3. **`fair_mean_*_ssp245.csv` ≠ `*_ssp245harm.csv`.** The former is RCMIP-native
   (`run_fair_ssps.py`, `fill_from_rcmip`). They differ *in the historical period* = the fit
   window, so they are **not interchangeable for calibration**.
4. **`postprocess_mcmc_ext.jl` globs `chain_ext_seed*`** and `TAG` stayed `"ext"` → any
   pre-v-next 28-column chain left in `outputs/mcmc/` gets silently mixed with 35-column ones.
5. **Pre-v-next adapted covariances are 28×28** → embedded into the 35×35 proposal on the
   non-geometry indices (geometry rows were appended, so relative order is preserved) rather
   than crashing. Asserts posdef.

---

## 4. Current state

**Branch `brick-mengel-vnext`** (new, off the archived/frozen `brick-mengel`).
Commits: `9dd7d95` (calibration), `8b43d18` + `bb4ab92` (CHANGELOG).
Also: `MimiBRICK.jl@brick-fm ec9680e` (prior builder), `FaIRtoFrEDI@heat-ed-morbidity f6fed87`
(forcing builder).

### Run 1 (4 × 500k) — NOT CONVERGED, and NOT a bug
Acceptance 0.224–0.241; **12 params fail R̂<1.05** — the 7 geometry params (R̂ 1.44–1.98)
plus the AIS block they correlate with. ESS ≈ 2000 → good within-chain, bad between-chain.

Three tests ruled out the plausible bug explanations:
- **Not multimodal** — per-chain median `log_post` 126.7 / 128.5 / 129.7 / 126.8.
- **Not bound-railing** — 5% of `ais_c`, 10% of `ais_runoff_h0` within 2% of a bound.
  (This **corrected** an earlier over-read that `ais_c` was railing, from one 50k tuning chain.)
- **Weakly identified** — posterior sd / prior sd = 0.46–0.76; `ais_bedheight0` 0.76 ≈ unidentified.

Broad correlated ridge = exactly why the original calibration fixed these.
`ais_ocean_temperature₀`: R̂ 1.09, pooled **0.772 ± 0.255** (2018-baseline median 0.981).

### Run 2 (4 × 1M) — RUNNING at time of writing
Launched under `caffeinate -i` via `julia/run_vnext_production.sh`, reseeded from the
**empirical 35×35 posterior covariance** (run 1 started from an embed+diagonal that knew
nothing about the ridge). ~70 min. Check: `pgrep -f calibrate_mcmc_ext`.

### Quarantined (nothing deleted)
| Path | What |
|---|---|
| `outputs/quarantine/20260718_pre_vnext_28param_ext/` | June-13 28-param chains + README (**superseded, not bugged**) |
| `outputs/quarantine/20260718_vnext_run1_notconverged/` | run-1 chains + logs |
| `outputs/quarantine/20260718_vnext_NOTCONVERGED_subsample/` | the non-converged subsample postprocess wrote to the canonical path |

**Note:** postprocess overwrote the June-13 `data/MimiBRICK/parameters_subsample_brick_mengel_ext.csv`
(untracked → not in git, but regenerable from the quarantined June-13 chains by moving them
back into `outputs/mcmc/` and re-running postprocess). The four MAGICC-vs-FaIR tables are
**unaffected** — `project_pulse_hybrid_mengel_lvl2150.jl` reads the non-`_ext`
`parameters_subsample_brick_mengel.csv`, untouched.

---

## 5. Next step / open questions

**Immediate:** when run 2 finishes, `julia --project=julia_v2 julia/postprocess_mcmc_ext.jl`
and check R̂ on the geometry block.

**If run 2 still misses R̂<1.05 — DO NOT resolve silently (methodological choice):**
1. **Longer chains** (4 × 5M, ~6 h overnight). No methodological change. Note 5M chains are
   ~3.5 GB each — thin or watch disk.
2. **Reduce the freed set** — re-fix `ais_bedheight0` (the one genuinely unidentified param),
   keep the identifiable ones free. Changes what "v-next" means.
3. **Accept geometry as a prior-dominated nuisance block.** Report marginals for the params
   of interest; cannot claim R̂ convergence. *This may be a publishable result rather than a
   failure:* "modern sea-level obs do not identify DAIS geometry."

**Also awaiting Marcus:**
- **Branch home.** Is `brick-mengel-vnext` right, or should the calibration drivers move into
  the **MimiBRICK-FM** repo (now the canonical home of the Mengel model)? I branched rather
  than commit onto the archived `brick-mengel`, but did not choose the long-term home.
- **Fix the broken fork `calibrate_mcmc_mengel.jl`** as separate cleanup / flag to Tony Wong?
  (Raised earlier, still unanswered.)
- Deferred MCS notes: **JOSS paper for BRICK-FM?**; switch table horizons to **100/150 yr from
  the emission point** rather than calendar 2100/2150.

**Downstream once the posterior is accepted:** regenerate the BRICK cells in the four
MAGICC-vs-FaIR tables.
