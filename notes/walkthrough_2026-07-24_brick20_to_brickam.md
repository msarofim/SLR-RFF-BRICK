# BRICK 2.0 → BRICK-AM

<p class="subtitle">A walkthrough of the updates — data sources, justifications, and code changes for the Antarctic-Mengel recalibration</p>

**M. Sarofim · NYU Marron Institute** — compiled 2026-07-24 · repo `SLR-RFF-BRICK`, branch `brick-mengel-vnext` (HEAD `69a2bfb`)

---

## 0. Orientation

**BRICK-AM** ("**A**ntarctic-**M**engel") is our fully-updated MimiBRICK sea-level model. It differs from **BRICK 2.0** (Tony Wong's obs-driven MimiBRICK v2.0.0 port) in three substantive ways plus one numerical correction:

| # | Update | In BRICK 2.0? | In v2.1.0? | Category |
|---|---|---|---|---|
| 1 | **Mengel-2016 glacier emulator** (replaces the Wigley–Raper single-reservoir glacier) | No | **Yes** | model structure |
| 2 | **Observation updates** (Dangendorf/STAR total; GRACE-FO + GlaMBIE extensions; proper σ; dropped point terms) | No | No — v2.1.0 keeps Church–White | calibration data |
| 3 | **GMST→Antarctic amplification** `a`: equilibrium 1.196 → CMIP6 secant **1.08 ± 0.15** | No | No | calibration prior |
| — | **Sub-annual DAIS crossing correction** (a numerical fix, only affects the pulse marginal) | No | No | numerics |

The name emphasizes update 3: a decomposition (§7) attributes **~85 % of the level change** from BRICK 2.0 to the amplification, with the glacier and observation updates far smaller. Relative to Tony Wong's official **v2.1.0** (which already carries the Mengel glacier), the BRICK-AM changes are **updates 2 and 3** — see below.

### BRICK 2.1 and the baseline

Tony Wong's official MimiBRICK releases (confirmed by Tony) are: **v2.0.0 = Wigley–Raper glaciers + Church–White GMSL**; **v2.1.0 = Mengel glaciers + Church–White GMSL**. So the Mengel glacier (**update 1**) is **shared with the official v2.1.0**, and relative to v2.1.0 the BRICK-AM changes are **updates 2 and 3** (plus the numerical fix). A large part of update 2 is precisely the total-GMSL observation swap **Church–White → Dangendorf 2024 + NOAA STAR** (§3), alongside the GRACE-FO / GlaMBIE component extensions and the Frederikse-ensemble σ.

This document is written from the **BRICK 2.0** baseline (all three updates visible) because that is where our development actually happened and what the decomposition (§7) measures. Two implementation facts to keep straight:

- Our BRICK-AM is built on **stock MimiBRICK v2.0.0 + a *local* Mengel component** (`julia/glaciers_mengel_component.jl`) swapped in at runtime (§3a) — we did not build on the packaged v2.1.0. The Mengel *structure* matches v2.1.0; our *posterior* differs, because we calibrate the same emulator against different targets (the extended Dangendorf / GRACE-FO / GlaMBIE set, not Church–White).
- The `v2.1` git tag in `SLR-RFF-BRICK` is **our own repo release tag**, unrelated to the MimiBRICK package version. The Julia depot pins `1.0.1`, the `v1.2.1` tag, and the `v2.0.0` tag (slot `edplP`); the BRICK-AM calibration runs under the `julia_v2` environment (= v2.0.0). The Mengel model is also canonicalized in the separate **MimiBRICK-FM** repo.

### BRICK version map

| Repo / branch or env | MimiBRICK build | Role |
|---|---|---|
| `SLR-RFF-BRICK` branch `brick-v1.2-vehicle` | v1.2.1 (`RtLCv`) | pre-2.0, EPA-rescission-comparable arm |
| `SLR-RFF-BRICK` branch `main` | v2.0.0 (`edplP`) | **BRICK 2.0** = Wong obs-driven port |
| `SLR-RFF-BRICK` branch `brick-mengel` (archived, tag `archive/brick-mengel-2026-06-17`) | v2.0.0 | frozen prior Mengel/study-driver work |
| `SLR-RFF-BRICK` branch **`brick-mengel-vnext`** (env `julia_v2`) | v2.0.0 + local Mengel | **BRICK-AM** (this document) |

> **Reproducibility flag.** `brick-mengel-vnext` is **local-only** (not pushed to origin). Anyone reproducing this needs the working tree, not a clone of origin.

---

## 1. The three updates at a glance

Each update is developed below in its own section with four parts: **what changed**, **data sources** (with paths + provenance), **justification** (with the authoritative write-up), and **code** (with paths). File paths are repo-relative to `SLR-RFF-BRICK/` unless prefixed `FaIRtoFrEDI/`.

The **forcing** is common to all rungs: FaIR **2.2.4 (calib1.4.5)** ensemble-mean GMST + OHC on Smith-harmonized SSP2-4.5, files `data/observations/fair_mean_gmst_ssp245harm.csv` and `..._ohc_ssp245harm.csv`, built in the sibling repo:

```bash
# in FaIRtoFrEDI/
python build_fair_mean_v145.py \
    --emissions-file calibration_v145/emissions_v145_ssp245_harmonized.csv \
    --tag ssp245harm --scenario-label ssp245_harmonized
```

The harmonized splice (not the RCMIP-native `fair_mean_*_ssp245.csv`) is used deliberately so the calibration fit window and the pulse projections sit on identical forcing (`calibrate_mcmc_ext.jl:85-95`, `FORCING_TAG="ssp245harm"`).

---

## 2. Update 1 — The Mengel-2016 glacier emulator

**What changed.** BRICK 2.0's glacier & small-ice-cap (GSIC) component is the Wigley–Raper single-reservoir model. BRICK-AM replaces it with the **Mengel et al. 2016** (PNAS 113:2597) two-timescale emulator, driven by total GMST, with a Little-Ice-Age (LIA) disequilibrium baseline.

### Data sources

The Mengel emulator ingests **no external glacier time series** — it is forced by GMST and models the post-LIA committed melt internally (see below). The only glacier *observation* is the calibration **target** (§3, update 2): the `gsic` column of `outputs/recalib_targets_ext.csv`, a splice of **Frederikse 2020** (1900–2018) and **GlaMBIE 2025** (2000→2023; DOI 10.5904/wgms-glambie-2024-07, raw `data/observations/raw/glambie_global_glacier_mass.csv`).

### Justification

The Wigley–Raper glacier structurally undershoots the 20th-century record (the "GSIC H1/H2 structural undershoot"). Mengel's design fixes this by construction: with `gic_T_lia < 0` the equilibrium contribution `S_eq(T=0) > 0`, so glaciers are out of equilibrium at the 1850–1900 baseline and are *committed* to post-LIA melt — reproducing the early-20th-century melt directly, without an anthropogenic/natural forcing split or an external "natural" budget. A prototype validated the emulator against the Frederikse glacier total to RMSE ≈ 0.13 cm. The full rationale and prototype fits are in `notes/handoff_2026-06-12_brick_mengel_calibration.md` and `handoff_2026-06-13_brick_mengel_post2018_extension.md`.

### Code

| File | Role |
|---|---|
| `julia/glaciers_mengel_component.jl` | the `@defcomp glaciers_mengel` (equations below); output var `gsic_sea_level` matches the WRB component so wiring into `global_sea_level` is unchanged |
| `julia/brick_mengel.jl` | `build_brick_mengel(...)` builds a stock v2.0.0 model then `replace!(m, :glaciers_small_icecaps => glaciers_mengel)` (`:51-52`); `update_brick_mengel!` sets the 7 Mengel params + non-glacier params |
| `julia/brick_param_updates.jl` | `update_brick_params!(…; skip_glaciers=true)` skips the WRB glacier mapping when Mengel is in place (`:79-84`) |
| `python/calibrate_mengel_glacier.py`, `python/glacier_2tau_validate.py` | offline prototype least-squares fits (single-τ and 2-τ) that informed the prior *ranges* |

**Equations** (`glaciers_mengel_component.jl:56-59`), with `T` = total GMST anomaly rel. 1850–1900:

```
S_eq[t]   = gic_a · (1 − exp(−gic_b · (T[t−1] − gic_T_lia)))
S_fast[t] = S_fast[t−1] + (gic_f·S_eq[t]       − S_fast[t−1]) / gic_tau_fast
S_slow[t] = S_slow[t−1] + ((1−gic_f)·S_eq[t]   − S_slow[t−1]) / gic_tau_slow
gsic_sea_level[t] = S_fast[t] + S_slow[t]
```

Parameters (`:37-44`): `gic_a` (asymptotic max SLE from the LIA state, m), `gic_b` (T-sensitivity, 1/K), `gic_T_lia` (LIA equilibrium temp, °C < 0), `gic_f` (fast-mode fraction), `gic_tau_fast` / `gic_tau_slow` (yr), `gic_sl0` (init m).

> **Important:** the six Mengel parameters are **freed and sampled in the MCMC** (§6), not fixed. Their "central" values are the MCMC **prior means** (`calibrate_mcmc_ext.jl:146-151`: `gic_a` N(0.45,0.08); `gic_b` N(0.52,0.25); `gic_T_lia` N(−0.45,0.30); `gic_f` N(0.50,0.30); `gic_tau_fast` N(40,30); `gic_tau_slow` N(300,200)) and the medoid init `(a=0.45,b=0.52,T_lia=−0.45,f=0.5,τ_fast=40,τ_slow=250)`. The offline python fit `outputs/mengel_glacier_2tau_params.csv` was used only to set prior ranges — do not treat it as the deployed parameterization.

**Total ice and the parameter posterior.** There is **no external total-glacier-ice constraint** in the likelihood — the total ice available to melt, `gic_a`, is pinned only by its prior and the 1900–2023 gsic time series. The prior *range* is inventory-informed (lower bound 0.32 m SLE = Farinotti 2019 present-day glaciers; mean ~0.45 m ≈ Mengel 2016's published median across 19 glacier-model fits), but no inventory total enters as *data*. The committed-melt combination `S_eq(0)=a·(1−exp(b·T_lia))` is well constrained at **0.20 ± 0.02 m SLE**. **One prior bound *is* too tight:** `gic_T_lia` rails against its −1.0 °C floor (29 % of the posterior at/near the bound; 5th percentile *at* it) — the data prefers a colder LIA equilibrium than the prior allows. Candidate follow-up: widen the `gic_T_lia` lower bound (−1.5/−2.0) and re-check whether the posterior moves interior and the fit improves; the well-constrained `S_eq(0)` is unaffected regardless.

---

## 3. Update 2 — Observation updates

**What changed.** The calibration targets were rebuilt into a **reconciled, extended-to-present** product; the uncertainty band was put on a defensible footing (Frederikse 5000-member ensemble); and the legacy IMBIE/Dyurgerov Gaussian *point* terms were dropped in favor of the extended time series constraining the modern rate directly.

### Data sources — `outputs/recalib_targets_ext.csv` (+ `_sources.csv`)

Built by **`python/prep_recalib_targets_ext.py`**. Series are 1900–2026, cm rel. the **1995–2005** window, NaN where a component lacks data. Splices are **offset-match only** (a level shift over the overlap window, no rescale; `GT_PER_CM_SLE = 3620.0`).

| Component | Historical | Modern extension → end yr | Raw file / DOI |
|---|---|---|---|
| **AIS** | Frederikse 2020 (1900–2018) | GRACE-FO JPL mascon RL06.3Mv4 → 2026 | `raw/grace_antarctica_mass.txt` · DOI 10.5067/TEMSC-3JC634 |
| **GIS** | Frederikse 2020 | GRACE-FO JPL mascon → 2026 | `raw/grace_greenland_mass.txt` · same DOI |
| **GSIC** | Frederikse 2020 | GlaMBIE 2025 → 2023 | `raw/glambie_global_glacier_mass.csv` · DOI 10.5904/wgms-glambie-2024-07 |
| **Steric / TE** | Frederikse 2020 | NOAA NCEI 0–2000 m thermosteric → 2025 | `raw/noaa_thermosteric_w0-2000m_yearly.dat` |
| **Total** | **Dangendorf 2024** GMSL reconstruction (1900–2021) | NOAA STAR altimetry → 2024 | `data/observations/dangendorf2024_gmsl_annual.csv` + `nasa_gmsl_annual.csv` |

Two points worth stating explicitly:

- **The total is a genuinely independent Dangendorf 2024 reconstruction**, not the sum of the modeled components (`prep_recalib_targets_ext.py:156-166`).
- **IMBIE 2023 (Otosaka et al.) is an independent cross-check only**, never fed to the fit (`prep_recalib_targets_ext.py:18-19, :258-271`).

**For comparison — BRICK 2.0 calibration observations.** BRICK 2.0 fits the standalone-BRICK likelihood: total GMSL plus four component series (temperature and OHC are *forcing inputs*, not fitted). It uses the package-bundled obs, extended only to the mid-2010s:

| Component | BRICK 2.0 | BRICK-AM |
|---|---|---|
| Total GMSL | Church & White (CSIRO recon 2015) | Dangendorf 2024 + NOAA STAR → 2024 |
| AIS | IMBIE 1992–2017 | Frederikse + GRACE-FO → 2026 |
| GIS | Frederikse 2020 (post-#93) | Frederikse + GRACE-FO → 2026 |
| GSIC | glaciers / small-ice-caps 1961–2003 | Frederikse + GlaMBIE → 2023 |
| Steric / TE | IPCC trend windows (1971–2009, 1993–2009) | Frederikse + NOAA NCEI → 2025 |
| Temperature (forcing) | HadCRUT4 | FaIR-mean GMST |
| OHC (forcing) | Gouretski 3000 m | FaIR-mean OHC |

BRICK 2.0's obs files live in the MimiBRICK package (`edplP/src/calibration/`); the post-PR#93 Greenland term is Frederikse 2020, replacing the earlier IMBIE-based merge. The headline shift is total GMSL **Church–White → Dangendorf 2024 + NOAA STAR**, plus swapping each component's short/older series for the reconciled, extended-to-present product above.

**Uncertainty σ** — from the **Frederikse 2020 5000-member weighted component ensemble** `data/observations/raw/frederikse2020_GMSL_ensembles.nc` (redistributed in Dangendorf's Zenodo 10621070). `load_ensemble_sigma()` (`:94-113`) re-references each member to 1995–2005, takes the per-year weighted sd, and writes `value ∓ 1.645·σ` into `_lo`/`_hi` so the Julia likelihood recovers σ exactly via `ϵband=(hi−lo)/(2·1.645)` (`calibrate_mcmc_ext.jl:97`). The Dangendorf total borrows the ensemble **GMSL** sd because Dangendorf's own per-year SE is corrupted upstream.

**Rignot 2019 SMB anchor** — enters not as a target column but as a likelihood term: grounded-AIS SMB 2098 ± 133 Gt/yr, area-scaled ×(10.92/12.295) = 0.888 → **1863.4 ± 118.1 Gt/yr** (`calibrate_mcmc_ext.jl:230-245`).

### Antarctic parameters freed to fit the record

To track the extended Antarctic record, BRICK-AM opens Antarctic degrees of freedom and adds one Antarctic likelihood term. **BRICK 2.0 already samples the full DAIS geometry and fast-dynamics block** (verified: all 15 Antarctic parameters vary in `parameters_subsample_brick.csv`), so the genuinely *new* freedoms **relative to Wong** are two:

- **`ais_ocean_temperature₀`** — Wong hard-fixes this at 0.72 °C (`SNEASY_BRICK.jl:91`); BRICK-AM samples it, prior N(0.72, 0.50) on [0.50, 2.00] (`calibrate_mcmc_ext.jl:137`). It is a direct lever on the Antarctic sub-shelf ocean forcing, so freeing it lets the model bend toward the observed AIS mass loss instead of the fixed default.
- **The GMST→Antarctic amplification** (§4) — Wong hard-codes the equilibrium slope 1.196; BRICK-AM frees it (prior N(1.08, 0.15)).

BRICK-AM also changes *how* the already-sampled Antarctic parameters are constrained:

- The DAIS **geometry block** (`ais_μ`, `bedheight₀`, `slope`, `iceflow₀`, `precipitation₀`, the runoff-onset `T_on`, `c`) and the **fast-dynamics** parameters (`λ`, `ais_γ`, `ais_κ`) are sampled under an explicit **joint paleo-covariance prior** (`outputs/paleo_geo_prior_ton.csv`, built from the DAISfastdyn paleo ensemble; standardized, cond ≈ 2.75), which carries the paleo correlation structure and identifies the runoff onset via the coordinate `T_on = −h₀/c`.
- A **Rignot 2019 SMB likelihood anchor** (data sources above) pins the modern Antarctic surface mass balance and breaks the SMB-vs-discharge input–output degeneracy.

> The DAIS geometry block stays **weakly identified** even so: several geometry parameters do not reach R̂ < 1.05 individually (a compensating ridge), which is why acceptance is gated on the projected-SLR deliverable (§7), not on the nuisance marginals.

### Justification

Extending the AIS/GSIC series to the present lets the **time series** constrain the modern melt rate directly, which is both more informative and avoids double-weighting the same information via a separate Gaussian point term:

> "DROPS the IMBIE dAIS(92-17) + Dyurgerov dGSIC(61-03) Gaussian point terms: the extended AIS/GSIC time-series now constrain the modern rate directly … avoids double-weighting" — `calibrate_mcmc_ext.jl:22-24`

The target reconciliation and the likelihood are documented in `notes/handoff_2026-07-20_phase2_calibration_wired.md` and `prerun_summary_2026-07-20_phase2_calibration.md`.

### Code

| File | Role |
|---|---|
| `python/prep_recalib_targets_ext.py` | builds `recalib_targets_ext.csv` + `_sources.csv` from the raw obs; splices + ensemble σ |
| `julia/calibrate_mcmc_ext.jl` | the likelihood: **AR(1) heteroscedastic** `hetero_logl_ar1` (`:74-81`), per-series obs-end years (`:99-130`), Rignot anchor (`:290-292`), point terms **absent** from `logposterior` (`:264-303`) |

The likelihood covariance for each of the five series is `Σ = σ²/(1−ρ²)·ρ^|i−j| + diag(ϵ²)` — an AR(1) process with per-year heteroscedastic observation error ϵ (the ensemble σ). Each series has its own free `sd_s`, `rho_s` (10 AR(1) nuisance params).

---

## 4. Update 3 — The GMST→Antarctic amplification

**What changed.** The DAIS component drives Antarctic ice-sheet temperature from global GMST through a linear map with slope `a` (the "amplification"). BRICK 2.0 uses the Shaffer-2014 **equilibrium/paleo** slope, `a = 1/0.8365 = 1.19546`. BRICK-AM recalibrates it to the **CMIP6 transient secant**, prior `a ~ N(1.08, 0.15)`.

### The mapping (and what the constants mean)

The DAIS component computes Antarctic surface temperature as (`julia/patches/antarctic_icesheet_smoothed_trigger.jl.txt:108`):

```
antartic_surface_temperature[t] = (global_surface_temperature[t−1] − ais_temperature_intercept)
                                   / ais_temperature_coefficient
```

so `a ≡ dT_ant/dGMST = 1 / ais_temperature_coefficient`. The recalibration samples `amp` and maps it **with the pre-industrial anchor held fixed** (`calibrate_mcmc_ext.jl:274-276`):

```
ais_temperature_coefficient = 1.0 / amp
ais_temperature_intercept   = − AIS_TANT0 / amp        # AIS_TANT0 = −15.42 / 0.8365 = −18.435
```

Decoding the constants (`calibrate_mcmc_ext.jl:164-171, :182`):

- **0.8365** = the original DAIS `ais_temperature_coefficient` (Shaffer 2014 GMST→T_ant regression slope). Its inverse **1/0.8365 = 1.19546** is the old **equilibrium amplification** that BRICK 2.0 uses.
- **15.42** = the original `ais_temperature_intercept`.
- **AIS_TANT0 = −18.435 °C** = the pre-industrial Antarctic surface-temperature anomaly anchor (Shaffer's ≈ −18 °C PI), held constant as `amp` varies so that only the *slope*, not the PI baseline, moves.

### Justification

The 1.196 slope is an **equilibrium/paleo** relationship; the DAIS fast-dynamics threshold is crossed on a **transient** trajectory. Reading the Antarctic-amplification **secant** (Antarctic ÷ global cumulative warming since pre-industrial) from **34 CMIP6 models in the land frame** (AIS `tas`), it settles to **≈ 1.06–1.10** at the DAIS-crossing-relevant 2.5–3.5 K of global warming. BRICK-AM adopts **N(1.08, 0.15)**. The full argument — including why the phase-2 prior's 0.95 was too low (it came from Xie 2022's PAI1 trend-ratio computed in an all-cells rather than land frame) — is the authoritative write-up:

> **`notes/writeup_2026-07-22_a6_amplification_for_tony.{md,pdf}`** — the primary justification document (sent to Tony Wong).

Supporting CMIP6 diagnostics: `python/diag_pai_cmip6_time.py`, `diag_pai_deck.py` (idealized 1pctCO2 / abrupt-4×CO2), `diag_pai_ohc.py`, `diag_pai_denominator.py`, `diag_pai_mask_sensitivity.py`.

### Code

| Location | Role |
|---|---|
| `calibrate_mcmc_ext.jl:274-276` | the `amp → (coefficient, intercept)` mapping with PI anchor preserved |
| `calibrate_mcmc_ext.jl:176-184` | the A6 prior — **file default N(0.95, 0.10)** on [0.70, 1.25] |
| `calibrate_mcmc_ext.jl:59-69` | CLI: `--amp-mu=`, `--amp-sigma=`, `--tag=` (note the `=`-form), and `--amp-equilibrium` |

The **BRICK-AM value N(1.08, 0.15)** is applied via CLI override (`--amp-mu=1.08 --amp-sigma=0.15 --tag=extA108`), which also widens the sampling bounds to μ ± 3σ = **[0.63, 1.53]** (`:178-181`). The equilibrium sensitivity run pins `a = 1.19546` (σ = 0.002) via `--amp-equilibrium --tag=extA6eq`.

> **Flag:** the file's *default* prior is 0.95 (the superseded phase-2 value). BRICK-AM is defined by the CLI override to 1.08 — the tag `extA108` is what makes a posterior "BRICK-AM."

---

## 5. The sub-annual DAIS crossing correction (numerical)

This is **not a model update** — it is a numerical fix, and it matters **only for the pulse marginal**, not for levels or the calibration.

**The problem.** DAIS disintegration triggers when Antarctic temperature crosses `temperature_threshold`. The stock integrator flips this on **whole-year** boundaries, so a 10 GtCO₂ pulse that advances a draw's crossing by a *fraction* of a year is rounded to zero for most draws — biasing the finite-difference pulse **median** ~3–4× low (it collapses to the non-AIS floor) while the mean is only mildly affected.

**The fix.** Scale the crossing-year disintegration by the fraction of the year spent above threshold, using a backward-mean Antarctic temperature:

```
frac = clamp( (T_sm − threshold) / max(dT_sm, 1e-4), 0, 1 )
disintegration_rate[t] = −λ · 24.78e15 / 57.0 · frac
```

**Where it lives.** The canonical patched component is saved in-repo at **`julia/patches/antarctic_icesheet_smoothed_trigger.jl.txt`** (`:181-200`). It is applied by hand to the loaded depot file `~/.julia/packages/MimiBRICK/edplP/src/components/antarctic_icesheet_component.jl` (the `get_model` path does not read the local repo copy). Apply/restore is **manual** — `chmod u+w → paste the frac block → run → restore from backup → chmod u−w` — and every pulse diagnostic **guards and aborts if the patch is absent** (`diag_subannual_pulse_means.jl:13-14`, `diag_decomposition_pulse.jl:13-14`).

**It is not used during calibration.** The 1850–2026 fit window never crosses the DAIS threshold (ΔT_glob only reaches ~1.3 K vs the ~2.9 K crossing), so the patch changes calibration by nothing and levels by < 1 %. It is applied only for the pulse-marginal diagnostics. Recipe: `notes/handoff_2026-07-22_a108_recalibration.md:53-59`.

---

## 6. The calibration + deployment pipeline

Environment: `julia --project=julia_v2` (MimiBRICK v2.0.0). Sampler: `RobustAdaptiveMetropolisSampler.RAM_sample(…; opt_α = 0.234)`. Free parameters: **39** (29 physical + 10 AR(1) nuisance).

```bash
# 1. Build the reconciled/extended targets (-> recalib_targets_ext.csv + _sources.csv)
python python/prep_recalib_targets_ext.py
```
```bash
# 2. MCMC: 4 chains x 2,000,000 iters, seeds 2026-2029, over-dispersed starts, a ~ N(1.08, 0.15)
for SEED in 2026 2027 2028 2029; do
  julia --project=julia_v2 julia/calibrate_mcmc_ext.jl 2000000 $SEED \
      --overdisperse --amp-mu=1.08 --amp-sigma=0.15 --tag=extA108 &
done; wait
```
```bash
# 3. Convergence gate on the SLR deliverable (writes outputs/mcmc/slr_convergence_extA108.csv)
julia --project=julia_v2 julia/diag_slr_convergence_by_chain.jl --tag=extA108
```
```bash
# 4. Accept-on-SLR + write the deployable posterior subsample
julia --project=julia_v2 julia/postprocess_mcmc_ext.jl --tag=extA108 --accept-slr
#   -> data/MimiBRICK/parameters_subsample_brick_mengel_extA108.csv   (10,000 rows x 39 cols)
```
```bash
# 5. Sub-annual pulse projection (REQUIRES the depot patch of §5; aborts otherwise)
julia --project=julia_v2 julia/diag_subannual_pulse_means.jl
```

Production driver: `run_vnext_production.sh`. Equilibrium sensitivity: `run_A6eq_sensitivity.sh` (`--amp-equilibrium`, tag `extA6eq`). The MCMC reuses the phase-2 `outputs/mcmc/adapted_cov_ext.csv` proposal and `overdispersed_starts.csv`.

**Priors consumed by step 2**: `outputs/param_priors.csv` (22 independent-Gaussian physical priors), `outputs/paleo_geo_prior_ton.csv` (the joint 7-param DAIS-geometry prior + 7×7 correlation, in the identified runoff-onset coordinate), and `outputs/recalib_central_row.csv` (the medoid post-#93 member used as the model base and geometry start point).

---

## 7. Validation & results

**Convergence** — `outputs/mcmc/slr_convergence_extA108.csv` (the SLR deliverable, 4 chains):

| Horizon | R̂ | ESS |
|---|---|---|
| 2100 | **1.0035** | 1578 |
| 2150 | **1.0025** | 1588 |

Acceptance ≈ 0.238; several nuisance AIS-geometry marginals never reach R̂ < 1.05 (a compensating ridge), but the **projected SLR is converged** — acceptance is gated on the deliverable, not the nuisance marginals.

**Level decomposition** BRICK 2.0 → BRICK-AM (`outputs/decomposition_ssp245.csv`, GMSL cm, SSP2-4.5 median):

| horizon | BRICK 2.0 | + Mengel | + obs/recalib | + amplification | = BRICK-AM |
|---|---|---|---|---|---|
| 2100 | 70.3 | −1.1 | −3.1 | **−17.4** | 48.7 |
| 2150 | 136.2 | −4.4 | +0.5 | **−24.0** | 108.4 |

The amplification is ≈ 85 % of the level change; it moves BRICK-AM from above-AR6 to **mid the AR6 likely range** (0.40–0.60 m @2100).

**Pulse decomposition** (`outputs/decomposition_pulse.csv`, MAGICC ensemble + sub-annual patch, ×10⁻³ cm/GtCO₂ @2100): the amplification (−) and recalibration (+) terms partially cancel, so the per-tonne response barely moves (median 21.4 → 16.6, mean 21.4 → 18.4). The sub-annual patch (§5) is the single largest element of the pulse *median* (+15.8), negligible for the level and the mean. See the cross-model artifact's decomposition panel.

> **Projection-file caveat.** The regenerated `outputs/proj_ssps_mengel_ext_*` and `postpred_ext_*` files are the **pre-amplification** `ext` posterior (a ≈ equilibrium; SSP2-4.5 @2100 p50 = 75.4 cm). The BRICK-AM (a = 1.08) result lives in the decomposition CSVs and the cross-model artifact (@2100 median 48.7 cm), **not** in a regenerated SSP/postpred file. Regenerate `posterior_predictive_ext.jl` with `--tag=extA108` if a fresh BRICK-AM postpred is needed.

---

## Appendix A — File index

**Data / inputs**

| Path | Contents |
|---|---|
| `outputs/recalib_targets_ext.csv` (+ `_sources.csv`) | calibration targets (5 components + total), 1900–2026, cm rel. 1995–2005 |
| `data/observations/raw/` | GRACE-FO AIS/GIS, GlaMBIE glaciers, NOAA thermosteric, Frederikse 5000-member `.nc` |
| `data/observations/dangendorf2024_gmsl_annual.csv`, `nasa_gmsl_annual.csv` | total-GMSL obs (Dangendorf + NOAA STAR) |
| `data/observations/fair_mean_gmst_ssp245harm.csv`, `..._ohc_ssp245harm.csv` | FaIR forcing (calib1.4.5, harmonized SSP2-4.5) |
| `outputs/param_priors.csv`, `outputs/paleo_geo_prior_ton.csv`, `outputs/recalib_central_row.csv` | priors + medoid base |
| `data/MimiBRICK/parameters_subsample_brick_mengel_extA108.csv` | **the deployable BRICK-AM posterior** (10k × 39) |

**Code**

| Path | Role |
|---|---|
| `python/prep_recalib_targets_ext.py` | build targets + σ |
| `julia/glaciers_mengel_component.jl` | Mengel glacier component |
| `julia/brick_mengel.jl`, `julia/brick_param_updates.jl` | model assembly + param mapping |
| `julia/calibrate_mcmc_ext.jl` | likelihood, priors, amplification mapping, MCMC |
| `julia/postprocess_mcmc_ext.jl`, `julia/diag_slr_convergence_by_chain.jl` | accept-on-SLR + convergence |
| `julia/patches/antarctic_icesheet_smoothed_trigger.jl.txt` | canonical sub-annual DAIS patch |
| `julia/diag_decomposition.jl`, `julia/diag_decomposition_pulse.jl`, `julia/diag_subannual_pulse_means.jl` | decomposition + pulse diagnostics |
| `run_vnext_production.sh`, `run_A6eq_sensitivity.sh` | production drivers |
| `FaIRtoFrEDI/build_fair_mean_v145.py` | forcing build |

## Appendix B — Notes & write-ups (all in `SLR-RFF-BRICK/notes/`)

| File | Covers |
|---|---|
| `writeup_2026-07-22_a6_amplification_for_tony.{md,pdf}` | **the amplification justification** (primary) |
| `writeup_2026-07-21_brick_fm_vs_wong_brick.md` | BRICK-FM vs Wong BRICK comparison |
| `handoff_2026-07-22_a108_recalibration.md` | the a=1.08 cold-start recipe + patch procedure |
| `handoff_2026-07-20_phase2_calibration_wired.md`, `prerun_summary_2026-07-20_phase2_calibration.md` | phase-2 (A2/A4/A5/A6) wiring |
| `handoff_2026-07-19_brick_fm_improvement_roadmap.md`, `handoff_2026-07-18_brick_mengel_vnext.md` | roadmap + v-next kickoff |
| `handoff_2026-06-12_brick_mengel_calibration.md`, `handoff_2026-06-13_brick_mengel_post2018_extension.md`, `handoff_2026-06-13_brick_mengel_postpred_projections.md` | early Mengel provenance |

## Appendix C — Provenance commits (branch `brick-mengel-vnext`)

`7423ab3` port Mengel · `841e679` LIA offset · `047b27a` 2-τ + LWS lock · `180aa31` acquire extension data + splice · `636f849` ext-target calibration · `9dd7d95` free DAIS geometry · `a954701` phase-2 A2/A4/A5/A6 · `cda7ca2` M3 Dangendorf+STAR + ensemble σ · `2b43e35` `--amp-equilibrium` · `ee0685b` wire a=1.08 · `69a2bfb` pulse decomposition (HEAD).
