# BRICK-FM vs the original Tony Wong BRICK — what changed and why

*Technical/methods write-up, 2026-07-21. Companion to the cross-model SLR artifact
("Cross-model sea-level rise · SSP2-4.5") and to the acceptance README
`data/MimiBRICK/README_brick_mengel_ext_acceptance.md`. Sources are cited inline;
suitable as raw material for the MimiBRICK-FM repo docs and the CH4/CO2 pulse-paper
methods section.*

> **Status (updated 2026-07-24).** This is the 2026-07-21 snapshot. Since then the model was
> **renamed BRICK-FM → BRICK-AM** and the A6 amplification prior **revised N(0.95, 0.10) →
> N(1.08, 0.15)** (posterior ≈ 1.07); the artifact's two BRICK rows are now **BRICK-AM (a = 1.08)**
> and **BRICK 2.0** (not "transient"/"equilibrium"), and the sub-annual DAIS crossing (§6) is now
> used for the artifact's pulse column. The §5 projection numbers are the earlier **a ≈ 0.95**
> posterior (BRICK-AM's SSP2-4.5 @2100 median is ~48.7 cm, not 39.7). **Canonical current
> reference:** `notes/walkthrough_2026-07-24_brick20_to_brickam.{md,pdf}`.

---

## 1. Baseline and lineage

"Tony Wong BRICK" here means **MimiBRICK v2.0.0** (Wong et al., raddleverse) run with
Tony's own calibration setup: parameters calibrated **end-to-end inside the coupled
SNEASY/DOECLIM chain** against Church & White GMSL (an LWS-removed total) with
Gouretski-era OHC, and — since PR#91/#93 (2026-05) — a joint posterior whose Greenland
block is constrained by the Frederikse GIS component (fixing the v1.0.1 no-GIS-melt
pathology, 97.6% b>v₀ → 0%). Verified 2026-05-21 that our "Tony-mode" simulation
reproduces the AIS trajectory Tony reported by email (1850 −6, 1900 −4, 2000 0,
2020 +1 cm) — so the comparisons below start from a faithful reproduction of his setup
(`julia/test_sneasy_posterior.jl`, memory `project_brick_calibration_input_mismatch`).

**BRICK-FM** ("FM" = **F**aIR + **M**engel, the two structural changes — per the
MimiBRICK-FM README) is our fork of that model: same Mimi component architecture and
DAIS/SIMPLE/anto/TE physics, with one structural component replaced, the forcing
convention changed, and a full recalibration. It lives in the shareable
**MimiBRICK-FM** repo (canonical home of the model) with the calibration machinery on
`SLR-RFF-BRICK @ brick-mengel-vnext`.

The changes fall into four groups.

## 2. Structural change: Mengel-2016 glacier emulator replaces the Wigley–Raper GSIC

The single change to the model physics (`julia/glaciers_mengel_component.jl`, swapped
in via Mimi `replace!` so the `:glaciers_small_icecaps` slot and all wiring are
preserved).

- **Wong's GSIC** (Wigley–Raper single reservoir) commits **100% of glacier volume**
  to melt for any sustained warming above its equilibrium temperature — a
  commit-everything pathology under stabilization scenarios.
- **Mengel et al. 2016** (PNAS 113:2597, DOI 10.1073/pnas.1500515113) instead gives a
  **temperature-dependent equilibrium**: `S_eq(ΔT) = a·(1 − exp(−b·(ΔT − T_lia)))`,
  relaxed toward on two timescales (fast + slow reservoirs, mixing fraction `f`). A
  sustained 1.5 °C world retains a glacier remnant instead of full depletion
  (stabilization regression passes; memory `reference_mengel2016_glacier_model`).
- The **`T_lia` offset** (< 0) is our addition to Mengel's form: at the 1850–1900
  baseline `S_eq(0) > 0`, so the committed/disequilibrium melt of glaciers still
  retreating from their Little-Ice-Age extent is *simulated* rather than imposed via
  an external attribution budget (which would double-count natural forcing already in
  the GMST driver).
- All 6 glacier parameters (`a, b, T_lia, f, tau_fast, tau_slow`) are **free in the
  phase-2 calibration** (fit against Frederikse Glaciers + Dyurgerov + GlaMBIE), not
  fixed at the Mengel published coefficients.

## 3. Interface changes: external forcing, reproducibility

- **Obs-driven forcing convention.** Wong's calibration produces parameters tuned to
  SNEASY-internal GMST/OHC — SNEASY's 1850–2018 ΔOHC is ~40–50% larger than
  obs/FaIR-mean OHC, so feeding external forcing into Wong's posterior gives, e.g., a
  ~3× TE undershoot (te_α 0.057 vs physics ~0.154; memory
  `project_brick_calibration_input_mismatch`). BRICK-FM is built to be driven
  **directly by external GMST + OHC** (FaIR, MAGICC, or obs), and its posterior is
  calibrated **under that same convention** — the input the model is calibrated with
  is the input it is run with.
- **v2.0.0 precip reparameterization shim.** v2.0.0 stores AIS `precipitation₀` in
  log space (component computes `exp(·)`); the `precip_log` flag in
  `update_brick_params!` handles the transform. With the shim, the v2.0.0 port
  reproduces v1.0.1 **bit-identically** over all 1058 component-trajectory columns
  (max|Δ| = 0), so the FM changes are measured against a clean baseline (memory
  `project_brick_v2_obsdriven_interface`).
- **LWS locked.** `get_model()` draws land-water storage unseeded on every call
  (~0.4 cm total-SLR drift between re-runs). BRICK-FM locks it (MimiBRICK-FM: the
  deterministic 0.3 mm/yr `:central` mean; the calibration branch: a fixed-seed
  realization, seed 2026), making builds reproducible (memory
  `project_brick_canonical_versions_lws_lock`).

## 4. Recalibration: new forcing, new observations, new parameters

Two phases, both by adaptive (RAM) MCMC on the obs-driven model; production =
4 × 2,000,000 over-dispersed chains (seeds 2026–2029, first half burned), SSP2-4.5
harmonized FaIR-mean forcing.

**Phase 1** (2026-06/07): recalibrated Wong's free parameters + the Mengel glacier
block to **FaIR-mean forcing** and updated observations — Frederikse 2020 per-component
budgets, GRACE-FO, GlaMBIE glaciers, IGCC/Gouretski OHC — replacing the
SNEASY-internal forcing + Church & White total of the original.

**Phase 2** (2026-07-20, the accepted posterior; 39 sampled parameters = 29 model + 10
AR(1)/band likelihood): five substantive changes, labels per the acceptance README:

| item | change | vs Wong |
|---|---|---|
| A2 | DAIS fast-dynamics λ, ais_γ, ais_κ **freed** under paleo marginals | Wong samples these too — freed vs the project's phase-1 baseline (fixed at medoid) |
| A4 | runoff line reparameterized to its identified direction (T_on = −h0/c) | Wong samples h0, c raw too; the reparameterization is ours (kills the r ≈ 0.9997 ridge) |
| A5 | **SMB likelihood** on β_total vs area-scaled Rignot 2019 (1863 ± 118 Gt/yr); posterior 1860 Gt/yr (medoid was 2389) | no SMB constraint |
| A6 | GMST→AIS-temperature map freed with **CMIP6-transient prior N(0.95, 0.10)** (PAI1/Xie 2022); posterior amp ≈ 0.94 | hard-coded equilibrium 1.196 = 1/0.8365 |
| geom | 7 DAIS geometry params under a **joint paleo-covariance prior** (Strategy B, standardized MvNormal; cond(C) = 2.75 vs raw 5.2e13) | Wong samples these too — freed vs the phase-1 baseline (fixed at medoid), now under an explicit joint prior |
| obs | total-SLR term = **real Dangendorf 2024** (1900–2021) + **NOAA STAR** (2022–2024); component-band σ from the Frederikse **5000-member ensemble** | Church & White total |

**On the "vs Wong" column.** Verified against Wong's posterior `data/MimiBRICK/parameters_subsample_brick.csv`: BRICK 2.0 **samples the full DAIS geometry and λ/γ/κ block** (all 15 Antarctic parameters vary). So A2, A4, and geom are refinements to parameters Wong *already* frees — the "fixed at medoid" baseline is the project's own **phase-1 28-parameter calibration** (`julia/calibrate_mcmc.jl`), not Wong. The genuine changes **vs Wong** are A5 (SMB anchor), A6 (amplification), obs (total-SLR product), and — in phase 1 — freeing `ais_ocean_temperature₀`, which Wong hard-fixes at 0.72 °C (`SNEASY_BRICK.jl:91`).

The Dangendorf item fixed two stacked data bugs: the repo's "Dangendorf" CSV was
actually Frederikse's own GMSL (redistributed inside Dangendorf's Zenodo record), and
the record's Global nc mis-writes barystatic into the GMSL slot upstream (memory
`project_dangendorf_frederikse_mislabel`).

**Acceptance criterion.** Ten parameter marginals never reach R̂ < 1.05 — the DAIS
geometry block sits on a compensating ridge (individually consequential, jointly
constrained; verified not-a-bug). The posterior is **accepted on the deliverable**:
SLR@2100 R̂ = 1.006, SLR@2150 R̂ = 1.008 across the over-dispersed chains
(Marcus's 2026-07-19 criterion; `postprocess_mcmc_ext.jl --accept-slr`).

**Two retained calibrations.** The A6 sensitivity run (`extA6eq`, amplification pinned
at Wong's 1.196, everything else recalibrated identically) is kept as a full posterior
alongside the transient one. In the artifact these are the two BRICK-FM rows:
*CMIP6-transient AIS T* (canonical) and *AR6-equilibrium AIS T*. Subsamples:
`data/MimiBRICK/parameters_subsample_brick_mengel_ext.csv` and
`..._extA6eq.csv` (both 10k draws).

## 5. What the changes do to projections (SSP2-4.5, rel. 1995–2014)

| quantity | pre-recalib (v-next posterior) | phase-2 transient | equilibrium (A6eq) |
|---|---|---|---|
| SLR@2100 median | 76.1 cm | **39.7 cm** [36.9, 75.0] | 63.6 cm |
| SLR@2150 median | 159.1 cm | **62.8 cm** [55.7, 153.5] | ~128 cm (artifact, MAGICC driver) |
| DAIS threshold crossing by 2100 | ~82% | **~29%** | — |

- **A6 (transient amplification) drives ~⅔ of the 76→40 cm drop** (~24 cm); A2/A4/A5 +
  the new observations supply the remaining ⅓ (~12 cm) (`diag_a6_attribution.jl`,
  `outputs/a6_attribution_summary.md`).
- This moves BRICK-FM from above-AR6 (the old BRICK-Mengel postpred sat at 77.7 cm
  @2100, above the AR6 likely 40–60 cm) to the **low edge of the AR6 likely range**;
  the equilibrium calibration lands with the AR6-era/FACTS process models.
- **Pulse marginals are much less calibration-sensitive than levels**: the pulse
  *median* is A6-robust to ~5% (4.56e-3 vs 4.35e-3 cm/GtCO₂ @2100 in the A/B test);
  the pulse *mean and fat tail* are A6-dominated, since A6 sets the fraction of draws
  near the disintegration threshold.

## 6. Validated-but-not-yet-adopted: the sub-annual DAIS crossing

The DAIS fast-dynamics trigger is evaluated on annual steps, which quantizes the tip
year and biases the finite-difference pulse **mean** low ~3× (the median is robust).
An analytic tip-time decomposition (approach 1) and a one-line sub-annual crossing
patch in the integrator (approach 2) agree to ~2% @2150; the patch collapses the
pulse-size dependence of the mean from 2.4–3.2× to 1.04–1.08. The artifact's BRICK
pulse-mean column is computed under the sub-annual patch. **Adopting the sub-annual
crossing permanently in BRICK-FM is validated but awaits Marcus's sign-off** — it
would shift all pulse (and slightly level) results (memory
`project_analytic_pulse_mean_quantization_bias`, handoff 2026-07-21 §4).

New evidence from the full-ensemble sub-annual runs (2026-07-21,
`outputs/crossmodel_pulse_means_subannual.csv`): the correction is **not just a
mean/tail effect for the equilibrium calibration** — its pulse *median* rises 2–4×
(e.g. MAGICC driver @2100: 5.4e-3 → 2.26e-2 cm/GtCO₂) because most equilibrium draws
are already tipped, so the previously-quantized tip-advance channel enters the median
draw, not just the tail. Transient medians move only +6%/+15% (@2100/@2150), since
only ~29% of transient draws tip. Levels move < 1%. This raises the stakes of the
adoption decision for any equilibrium-calibration pulse results.

## 7. Provenance quick-reference

| artifact | where |
|---|---|
| Mengel glacier component | `julia/glaciers_mengel_component.jl` (brick-mengel-vnext + MimiBRICK-FM) |
| build/update helpers | `julia/brick_mengel.jl`, `julia/brick_param_updates.jl` (`precip_log`) |
| phase-2 calibration driver | `julia/calibrate_mcmc_ext.jl` |
| production chains | `outputs/mcmc/chain_ext_seed{2026..2029}_n2000000.csv`, `chain_extA6eq_...` |
| accepted subsamples | `data/MimiBRICK/parameters_subsample_brick_mengel_ext.csv`, `..._extA6eq.csv` |
| acceptance record | `data/MimiBRICK/README_brick_mengel_ext_acceptance.md` |
| superseded posteriors | `outputs/quarantine/20260718_pre_vnext_28param_ext/`, `20260720_*` |
