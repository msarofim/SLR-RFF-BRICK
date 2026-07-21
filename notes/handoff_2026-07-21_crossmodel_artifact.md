# Handoff — Cross-model sea-level artifact + pulse means (2026-07-21)

> **DONE 2026-07-21 (evening session).** Pulse-mean column added and artifact republished (same
> URL). Full numbers: `outputs/crossmodel_pulse_means_subannual.csv` (BRICK, sub-annual) +
> FaIRtoFrEDI CHANGELOG (FACTS/MAGICC-native). Corrections vs this note: (1) §3c means were
> partial-N; full-N sub-annual means are higher (transient MAGICC @2100 15.9 not 13.7×10⁻³);
> (2) the equilibrium calibration's sub-annual MEDIAN rises 2–4× (not ~1%) — most equilib draws
> are tipped, so the tip channel reaches the median; (3) MAGICC-native `PULSE_co2..._n600` is a
> **0.01-GtCO₂** pulse, and the artifact's MAGICC-native medians trace to the 0.1-GtCO₂ sweep
> arm — μ uses the ±10-GtCO₂ arms; (4) wf2f, not wf3f/wf4, is the fat-pulse-tail FACTS workflow.
> equilib subsample CSV written (§1 first-action done). BRICK-FM write-up:
> `notes/writeup_2026-07-21_brick_fm_vs_wong_brick.md`. Open: sub-annual adoption (M2) + μ-arm
> choice for MAGICC-native — both awaiting Marcus.

Self-contained recipe to (re)generate the **"Cross-model sea-level rise · SSP2-4.5"** artifact,
INCLUDING the not-yet-added pulse-mean column. A fresh session should be able to finish the pulse-mean
update from this note + the linked scripts. Companion memory: [[project_analytic_pulse_mean_quantization_bias]],
[[project_brick_mengel_vnext_recalib]], [[project_facts_install_scoping]], [[project_magicc_comparison]].

**Repos:** `SLR-RFF-BRICK @ brick-mengel-vnext` (BRICK + all diag scripts) · `FaIRtoFrEDI @ heat-ed-morbidity`
(forcing + FACTS + MAGICC data + artifact HTML snapshot). Cross-repo: BRICK handoffs live here per CLAUDE.md,
but the artifact touches both repos — paths below are absolute or repo-tagged.

---

## 0. The artifact

- **Live:** https://claude.ai/code/artifact/7b5f05fe-9d59-49b3-9524-3c99ca605d51 (owned by Marcus; private).
- **HTML snapshot (source of truth):** `FaIRtoFrEDI/magicc_comparison/artifacts/crossmodel_slr_ssp245.html`
  — edit this, then publish via the Artifact tool with `url=<the URL above>` to keep the same link.
- **Structure:** 4 tables in a 2×2 grid — Level@2100, Level@2150, Pulse@2100, Pulse@2150. Columns = climate
  driver (MAGICC, FaIR); rows = 7 SLR-model rows. Below: 4 finding cards + footer notes. All data lives in one
  JS `D={}` object + `models[]` array; rendering is `levelCard()`/`pulseCard()`. Design tokens (teal=level,
  copper=pulse, purple=BRICK accent) are inline CSS; dual light/dark. Favicon 🌊.
- **Current state:** level cells pair **median + mean (μ)**; pulse cells are **median only**. The task is to
  ADD a pulse **mean** (μ) to the pulse cells, exactly mirroring the level cells.

### Conventions (apply everywhere)
- **Scenario:** SSP2-4.5. **Horizons:** 2100, 2150. **Levels** rel. **1995–2014** mean.
- **Pulse:** **10 GtCO₂ @2030**, paired base/pulse; marginals reported **per GtCO₂** (÷10).
- **OHC scaling:** all OHC forcing CSVs are in **ZJ**; BRICK wants 1e22 J → multiply by **0.1** (`OHCS=0.1`).
- **Ensemble sizes:** FACTS n=200, MAGICC-driven n=600, FaIR-driven BRICK n=841.
- **Level tail flag (copper μ):** per-model **driver-averaged** mean/median ratio **≥ 1.20** (flag both driver
  cells together — a hard per-cell cutoff splits skewed rows).

---

## 1. Models, drivers, and how each was run

**All model outputs are ALREADY GENERATED and cached** — the artifact regen does NOT need to re-run FaIR,
FACTS, or MAGICC. This section is provenance + where the cached outputs live.

### Climate drivers (the two columns)
- **MAGICC** v7.5.3, AR6 **n600** drawset. **FaIR** 2.2.4 **calib1.4.5**, **841** configs.
- **Wide forcing ensembles** (year × member), built by `FaIRtoFrEDI/magicc_comparison/build_curvature_figure.py`,
  in `FaIRtoFrEDI/magicc_comparison/processed/curv_wide/`:
  - MAGICC driver: `ssp245_gmst_base.csv`, `ssp245_ohc_base.csv`, `ssp245_gmst_pulse10gt.csv`,
    `ssp245_ohc_pulse10gt.csv` (600 members). (Also `..._pulse.csv` = **0.1 GtCO₂** pulse — used only for the
    pulse-size robustness tests, NOT the artifact.)
  - FaIR driver: `fair_gmst_base_wide.csv`, `fair_ohc_base_wide.csv`, `fair_gmst_pulse_wide.csv`,
    `fair_ohc_pulse_wide.csv` (841 members, **10 GtCO₂** pulse — the ΔGMST differs from MAGICC by climate response,
    not pulse size).

### FACTS (4 workflow rows)
- Docker/Colima on the M4 (see [[project_facts_install_scoping]]). Driven by **injected** climate (GSAT+OHC) via
  the `climate_data_file` seam; workflows wf1f=IPCC/process, wf2f=+LARMIP, wf3f=+DeConto MICI, wf4=Bamber SEJ.
- Experiments under `FaIRtoFrEDI/facts/experiments/`:
  `global.coupling.ssp245.pbase` (FaIR base), `.p10gt` (FaIR +10 Gt), `.magiccbase`, `.magiccp10gt`.
- Totals: `<exp>/output/<exp>.total.workflow.{wf1f,wf2f,wf3f,wf4}.global.nc`, var `sea_level_change`,
  dims **samples=200**, years 2020–2150. Values already ≈1995–2014-anchored → **just mm→cm (÷10), read the year**
  (no rebaseline; validated to reproduce the artifact medians <0.1 cm).

### MAGICC-native (Nauels module, 1 row, MAGICC driver only)
- Base: `MAGICC/slr-refresh/data/processed/SSPs_Nauels2025_withOCH_2026_06_16_100817.csv` (600 members;
  read the "Sea Level Rise" total, scenario ssp245). Pulse: `PULSE_co2_ssp245_Nauels2025_withOCH_n600_*.csv`.
- Rebaseline: subtract **each member's own 1995–2014 mean**, then mm→cm (validated: @2100 53.2, @2150 88.1).
- No FaIR-driven counterpart by construction (climate + SLR are one model) → cell = "—".

### BRICK-FM (2 rows — the two AIS-temperature calibrations)
- Built by `SLR-RFF-BRICK/julia/brick_mengel.jl` (`build_brick_mengel(ssp="ssp245", y0=1850, y1=2150)`,
  `precip_log=true`); run on the wide driver forcing above (pair posterior draw i ↔ forcing member i).
- **transient** ("CMIP6-transient AIS T"): posterior
  `data/MimiBRICK/parameters_subsample_brick_mengel_ext.csv` (10k draws, 39 params, amp ~0.94).
- **equilibrium** ("AR6-equilibrium AIS T"): posterior = subsample of
  `outputs/mcmc/chain_extA6eq_seed{2026,2027,2028,2029}_n2000000.csv` (amp pinned 1.196).
  **⚠ No subsample CSV written yet** — `diag_brick_crossmodel_numbers.jl` reads the 4 chains and thins on the
  fly (`loadpost(...)`). First action for reuse: write
  `data/MimiBRICK/parameters_subsample_brick_mengel_extA6eq.csv` once (thin post-burn, 10k rows).
- Parameter mapping (verbatim in every diag script): 27 FREE columns + 2 DERIVED —
  `ais_runoff_Ton`→`h0 = −T_on·ais_c`; `ais_gmst_amp`→`coef=1/amp, intercept=−(−15.42/0.8365)/amp`.

---

## 2. BRICK-FM updates relative to the original Tony Wong BRICK

(For the artifact's "two calibrations" note + methods. Full detail: acceptance README
`data/MimiBRICK/README_brick_mengel_ext_acceptance.md` + memory.)

1. **Mengel-2016 glacier emulator** replaces the Wong GSIC block (`julia/glaciers_mengel_component.jl`,
   included at build; 6 gic params free). This is the "FM" in BRICK-FM. [[reference_mengel2016_glacier_model]]
2. **MimiBRICK v2.0.0 obs-driven port** (the `precip_log` shim; bit-identical to v1.0.1 pre-2019). [[project_brick_v2_obsdriven_interface]]
3. **Phase-1 recalibration** to FaIR-mean forcing + updated obs (Frederikse components, GRACE-FO, GlaMBIE
   glaciers, IGCC/Gouretski OHC) — vs Wong's SNEASY-internal forcing + older obs.
4. **Phase-2 (v-next, 2026-07):**
   - **A2** freed the DAIS fast-dynamics params λ, ais_γ, ais_κ under paleo marginals (were fixed).
   - **A4** reparameterized the runoff line to the identified direction (T_on = −h0/c).
   - **A5** added an SMB likelihood term on β_total vs area-scaled Rignot 2019 (1863±118 Gt/yr).
   - **A6** replaced the fixed GMST→Antarctic amplification (**1.196 = 1/0.8365**, the BRICK/DAIS default,
     hard-set in `MimiBRICK.jl:110` etc.) with a **CMIP6-transient prior ~0.95** — this is the transient
     vs equilibrium distinction. A6 drives ~⅔ of the 76→40 cm SLR drop.
   - Freed the **7 DAIS geometry params** under a joint paleo-covariance prior (Strategy B).
   - **Dangendorf 2024 + NOAA STAR** total term (fixed the mislabeled-Frederikse bug); component-band σ from the
     Frederikse 5000-member ensemble. [[project_dangendorf_frederikse_mislabel]]
   - LWS locked. Accepted on **SLR-level deliverable** convergence (SLR@2100/2150 R̂ 1.006/1.008), NOT on the
     parameter marginals (a compensating AIS-geometry ridge; verified not-a-bug).

---

## 3. THE DATA (all numbers for the artifact)

### 3a. Level — median + mean (cm rel 1995–2014), [MAGICC, FaIR] — ALL COMPUTED, already in the artifact
| row | med 2100 | mean 2100 | med 2150 | mean 2150 |
|---|---|---|---|---|
| FACTS · IPCC-process (wf1f) | [47.1, 50.0] | [46.9, 49.8] | [77.7, 81.2] | [76.9, 81.1] |
| FACTS · +LARMIP (wf2f)      | [56.0, 59.3] | [60.2, 62.1] | [97.9, 101.2] | [105.1, 107.8] |
| FACTS · +DeConto MICI (wf3f)| [54.7, 55.4] | [61.3, 62.4] | [111.0, 106.6] | [181.7, 169.6] |
| FACTS · Bamber SEJ (wf4)    | [64.4, 68.0] | [84.2, 82.9] | [107.1, 108.6] | [156.2, 151.6] |
| BRICK-FM · transient        | [37.6, 40.5] | [47.5, 48.8] | [60.2, 65.0] | [87.9, 88.6] |
| BRICK-FM · equilibrium      | [65.1, 62.7] | [65.5, 65.1] | [128.0, 124.1] | [122.0, 121.6] |
| MAGICC-native               | [53.2, —]    | [56.0, —]    | [88.1, —]    | [95.6, —] |

### 3b. Pulse — MEDIAN (×10⁻³ cm/GtCO₂), [MAGICC, FaIR] — ALL COMPUTED, already in the artifact
| row | med 2100 | med 2150 |
|---|---|---|
| wf1f | [6.03, 5.66] | [8.21, 7.94] |
| wf2f | [8.26, 7.73] | [14.2, 12.8] |
| wf3f | [6.79, 6.26] | [9.59, 8.94] |
| wf4  | [5.05, 4.82] | [6.71, 6.64] |
| BRICK-FM · transient   | [4.93, 4.69] | [7.38, 6.92] |
| BRICK-FM · equilibrium | [5.44, 5.12] | [8.48, 8.02] |
| MAGICC-native | [15.4, —] | [26.4, —] |

### 3c. Pulse — MEAN (×10⁻³ cm/GtCO₂) — THE NEW QUANTITY. Partially computed:
BRICK-FM analytic means (approach 1, `diag_analytic_pulse_mean.jl`), **MAGICC driver only so far:**
| row | mean 2100 (MAGICC) | mean 2150 (MAGICC) | mean/median @2100 |
|---|---|---|---|
| BRICK-FM · transient   | **13.7** (sub-annual 11.3) | **23.0** (sub-annual 22.5) | ~2.8× |
| BRICK-FM · equilibrium | **20.9** | **26.1** | ~3.8× |

**STILL TO COMPUTE for the pulse-mean column:**
- BRICK-FM pulse means for the **FaIR** driver (both calibrations) — swap `diag_analytic_pulse_mean.jl`
  forcing from `ssp245_*` (MAGICC) to `fair_*_wide` (FaIR).
- **FACTS** pulse means (4 workflows × 2 drivers): ensemble mean of (pulse−base)/10 from the `*.total.workflow.*`
  nc at `p10gt`/`magiccp10gt` vs `pbase`/`magiccbase`. (Check for a fat pulse tail on wf3f/wf4 — their LEVEL mean
  is heavy-tailed, so the pulse mean may exceed the median substantially.)
- **MAGICC-native** pulse mean (MAGICC only): from `PULSE_co2_ssp245_Nauels2025...` vs base, per-member mean.

---

## 4. Pulse mean — method, validation, and which number to use

**Problem:** the raw per-tonne pulse MEAN is NOT pulse-size-robust for BRICK-FM (inflates 2.6–4.6× over
0.1→10 GtCO₂). The MEDIAN is robust (~1%). Root cause: the **annual-step DAIS disintegration trigger**
(`antarctic_icesheet_component.jl:180`) quantizes the tip YEAR, so a small pulse can't resolve sub-annual
tip-time shifts and the mean's hazard vanishes.

**Approach 1 — analytic tip-time decomposition** (`julia/diag_analytic_pulse_mean.jl`): per draw,
`marginal = smooth(non-AIS finite diff) + tip_channel`, where
`tip_channel = disint_rate(@horizon) × [pulse warming @ CONTINUOUS crossing / tonne] / [warming rate @ crossing]`.
Uses the sub-annual interpolated crossing → the derivative limit → **pulse-size-invariant by construction**
(verified: analytic mean via the 0.1 vs 10 GtCO₂ T-pulse agree to ratio **1.000**).

**Validation — approach 2, sub-annual crossing** (`julia/diag_subannual_validate.jl`): patch the LOADED depot
component (NOT the local `MimiBRICK.jl` repo — `get_model` uses the depot at
`~/.julia/packages/MimiBRICK/edplP/src/components/antarctic_icesheet_component.jl`) to scale the crossing-year
disintegration by `frac = (T[t]−thr)/(T[t]−T[t−1])`. **Exact patch** (make file writable with `chmod u+w`,
apply, run, then restore from backup + `chmod u-w`):
```julia
# replace the `if v.antartic_surface_temperature[t] > p.temperature_threshold ... end` block with:
if v.antartic_surface_temperature[t] > p.temperature_threshold
    frac = 1.0
    if v.antartic_surface_temperature[t-1] <= p.temperature_threshold   # NB: no `t>1` — t is a Mimi Timestep
        frac = (v.antartic_surface_temperature[t] - p.temperature_threshold) /
               (v.antartic_surface_temperature[t] - v.antartic_surface_temperature[t-1])
    end
    v.disintegration_rate[t] = -p.λ * 24.78e15 / 57.0 * frac
else
    v.disintegration_rate[t] = 0.0
end
```
**Result:** pulse-mean pulse-size ratio 0.1→10 collapses **2.4–3.2 (annual) → 1.04–1.08 (sub-annual)**; the
sub-annual small-pulse mean **matches the analytic** — @2150 2.25e-2 vs 2.30e-2 (~2%), @2100 1.13e-2 vs 1.37e-2
(~18%; analytic runs slightly high at 2100 where disintegration is still ramping). **Approach 1 validated;
approach 2 is the clean fix.** The true mean-pulse is **~2.5–3× the median**.

**Which number for the artifact:** use the **sub-annual model** mean (most accurate) if adopting the patch;
else the **analytic** mean (post-process on standard runs, ~18% high at 2100). Recommend sub-annual for the
final artifact and footnote the ~18% analytic/sub-annual @2100 spread. FACTS/MAGICC-native have no annual-step
quantization (pulse verified ~linear) so their plain 10-GtCO₂ ensemble mean IS the robust mean — no
decomposition needed. **Document the method split** (BRICK = derivative/sub-annual; others = ensemble mean).

**Open model decision (bigger than the artifact):** the sub-annual crossing is a *validated improvement* to
BRICK-FM. Adopting it (approach 2, in the depot or a forked component) would fix the pulse quantization
permanently and shift ALL pulse (and slightly level) results. Flag to Marcus before adopting.

---

## 5. Status of outputs — what exists vs what's needed

| item | status | file / how |
|---|---|---|
| Level median+mean, all 7 rows × 2 drivers | ✅ DONE, in artifact | FACTS/MAGICC via subagent reduction; BRICK via `diag_brick_crossmodel_numbers.jl` |
| Pulse median, all rows | ✅ DONE, in artifact | FACTS/MAGICC unchanged from prior; BRICK from `diag_brick_crossmodel_numbers.jl` |
| Pulse mean — BRICK transient/equilib, **MAGICC** | ✅ computed (analytic; transient also sub-annual) | `diag_analytic_pulse_mean.jl`, `diag_subannual_validate.jl` |
| Pulse mean — BRICK **FaIR** (both calib) | ❌ TODO | swap forcing to `fair_*_wide` in `diag_analytic_pulse_mean.jl` |
| Pulse mean — FACTS (4×2), MAGICC-native | ❌ TODO | ensemble mean of (pulse−base)/10 from the nc / Nauels CSVs (subagent can do this) |
| equilib posterior subsample CSV | ❌ not written | write `parameters_subsample_brick_mengel_extA6eq.csv` once for reuse |
| Artifact HTML snapshot | ✅ current (median+mean level, median pulse) | `FaIRtoFrEDI/magicc_comparison/artifacts/crossmodel_slr_ssp245.html` |

**Scripts (all committed on `brick-mengel-vnext`, `SLR-RFF-BRICK/julia/`):**
`brick_mengel.jl`, `diag_brick_crossmodel_numbers.jl` (level+pulse median run harness — the template to extend),
`diag_analytic_pulse_mean.jl` (approach 1), `diag_subannual_validate.jl` (approach 2 + patch), `diag_lt_robust_pulse_mean.jl`,
`diag_a6_attribution.jl`. All MAGICC-driver forcing is hardcoded — parameterize the forcing paths to add FaIR.

---

## 6. To regenerate the artifact WITH pulse means — checklist

1. Write the equilib subsample CSV (see §1) so BRICK runs are reproducible.
2. Extend `diag_analytic_pulse_mean.jl` (or a sub-annual variant) to output BRICK-FM pulse **mean** for
   **both drivers × both calibrations** @2100/2150. Decide analytic vs sub-annual (recommend sub-annual).
3. Compute FACTS (4×2) + MAGICC-native pulse **means** (ensemble mean of per-member marginals; subagent-friendly).
   Check wf3f/wf4 for a fat pulse tail.
4. In the HTML `D.pulse`, change each `2100:[[...]]` to `{med:[...], mean:[...]}` mirroring `D.level`, and copy
   the level cell's median+μ rendering into `pulseCard()` (μ copper where driver-averaged mean/median ≥ some
   threshold — pick to match the tail story; BRICK will be ~2.5–3× so it'll flag).
5. Update the footer: pulse now shows median+mean; note the method split (BRICK sub-annual/derivative vs others
   ensemble mean) and that the BRICK pulse mean is ~2.5–3× the median because of the (now-corrected) annual-step
   quantization.
6. Publish: Artifact tool, `file_path=<snapshot>`, `url=https://claude.ai/code/artifact/7b5f05fe-...`, favicon 🌊.
   Then copy the snapshot into the repo and commit.

---

## 7. Non-obvious traps (each cost real time this session)

- **`get_model` uses the DEPOT MimiBRICK, not the local `MimiBRICK.jl` repo.** Editing the repo component does
  nothing; patch `~/.julia/packages/MimiBRICK/edplP/...` (writable via `chmod u+w`, restore after). A fresh
  julia recompiles on the changed mtime.
- **Mimi `t` is a Timestep, not an Int** — `t > 1` throws; use `is_first(t)` or index arithmetic (`t-1`).
- **Model outputs are `Union{Missing,Float64}`** — coalesce (`x===missing ? NaN : Float64(x)`) before comparisons.
- **The Global `dangendorf_2024_gmsl.csv` in the SLR repo is Frederikse** (upstream Zenodo mislabel) — irrelevant
  to the artifact but don't confuse it. The artifact's MAGICC column = AR6 n600; FaIR = 841.
- **The non-10gt `ssp245_*_pulse.csv` is 0.1 GtCO₂**, `..._pulse10gt.csv` is 10 GtCO₂. Artifact uses 10gt.
- **Median is pulse-size-robust; MEAN is not (for BRICK)** — never quote a raw 10-GtCO₂ BRICK pulse mean without
  the sub-annual/analytic correction; it's inflated ~2.5–3×… but that IS the true derivative mean (the median
  under-states it). This is the subtle bit: the median under-reports, the raw-large-pulse mean over-reports for
  the wrong reason, and the corrected mean sits at ~2.5–3× the median for the right reason.

## 8. Also open (unrelated to the artifact)
- **M2** (still pending Marcus): does the pulse/SC-SLR paper adopt the phase-2 transient posterior? Median pulse
  is A6-robust (~5%); the mean/tail is A6-dominated. See [[project_brick_mengel_vnext_recalib]].
