# Handoff — Greenland is CLOSED as a module; the leverage is Antarctica

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, through `6cd0a02`
(pushed; `origin/ladrillo-dev` is in sync). Written 2026-08-24, to be picked up cold.

**Supersedes** `handoff_2026-08-23f_v564_and_amp_law.md` for its §5 open-work list —
items 1 (the amp law) and 5 (the cell-choice envelope) are **closed by measurement**,
not by fixing. Its §1 (the shipped cell) and §3 (the separation target) are unchanged.

---

## 0. THE ONE-PARAGRAPH VERSION

Greenland is now a finalized Ladrillo module on every axis GSIC was: gated in the
canonical suite (7 → 10 steps), certified at the canonical vintage, deliverables and
figures regenerated at L14, the tap shipped as the **default** arm, a module memo, and
an accurate `LADRILLO.md`. The two things that were open evidence are now both
**answered rather than fixed**: the cell-choice envelope is **38.0 cm = 1.41× the
sampled spread and is ONE-SIDED** (the shipped value is the admissible *maximum*), and
the 2100 fast bias is **characterised and reported** after three candidate corrections
were tested and all three refuted. Along the way the `data/cmip6_pai` reduction — which
underpins the PAI/A6 **Antarctic** amplification analysis — was found **corrupt for the
MPI pair**, and corrected series are now on disk. Greenland is 18.6% of the ssp585 2300
total with a spread of 26.9 cm; **Antarctica is 54.8% with 252.3 cm.** Go there.

---

## 1. WHAT IS DONE — DO NOT REDO IT

1. **`run_ladrillo_tests.sh` gates the Greenland that ships** — 10 steps. Steps 8–10
   (`test_greenland_3basin_nesting`, `test_gis_ordering_wedge`, `test_gis_tap_wiring`)
   were previously run by hand only, so a green suite described the A+B whole-sheet
   model L14 superseded. All 10 pass, exit 0 (`outputs/log_ladrillo_tests_10step.txt`).
2. **The Greenland block has a convergence certificate at L14** —
   `outputs/mcmc/gis_block_convergence_L14.csv`. **3 of 9 fail, worst R̂ 1.075**,
   against Ladrillo 1.0's 4 of 8 / 1.335. The slow-channel reparameterisation worked:
   `gis_slow_w` R̂ 1.005 / ESS 1598 where `gis_alpha_s` was 1.180 / ESS 34.
   **LADRILLO.md's old "spanning 2.8×" Greenland caveat overstated the shipping model**
   and is corrected. The projections-only rule stands — it is set by AIS, not Greenland.
3. **The tap is the DEFAULT arm** (`--no-tap` gets the base model). Filenames kept
   their meanings deliberately: four consumers read the plain
   `ssps_components_2300_<TAG>.csv` as the *base* model, and one of them
   (`test_gis_tap_wiring`'s `SPREAD_SRC`) would have become self-referential.
4. **The reporting chain is at L14** — `postpred_L14_*`,
   `ladrillo_model_comparison_L14{,_spread}`, `ladrillo_L14_fig{1,2,3}`. The two python
   halves built paths by f-string and could only ever see the untapped file; they now
   resolve through `gis_targets.ssps_csv()`.
5. **`LADRILLO.md` rewritten** — it had described `greenland_ab` on posterior L10 since
   2026-08-13. Greenland detail is delegated to the module memo, not duplicated.
6. **Module memo**: `notes/memo_2026-08-23_greenland_module.md`. §1 and §9 are marked
   placeholders — **Marcus drafts the prose**.
7. **The r2300 "tap-free" guard was DEAD** and is fixed at the root:
   `gis_targets.tap_cell()` now parses `const GIS_TAP_CELL` out of the Julia component,
   so the cell is never retyped in python again.

---

## 2. THE TWO CLOSED QUESTIONS

### 2.1 The cell-choice envelope — 38.0 cm, and REPORT IT ONE-SIDED

`python/diag_gis_cascade_envelope.py`, `outputs/diag_gis_cascade_envelope.csv`.

| | value |
|---|---|
| admissible range, Greenland ssp585@2300 | **57.8 – 95.7 cm** |
| envelope | **38.0 cm = 1.41× the sampled p05–p95 (26.85 cm)** |
| admissible median | 66.8 cm |
| the shipped cell | **95.7 cm = the MAXIMUM, 100th pctile, 1.43× the median** |
| first-order predecessor | 118.0 cm = 4.4× — **3.1× worse; never quote it** |

⚠ **A symmetric ± band around 95.7 cm is wrong in both directions.** The cell was
chosen as the largest V clearing the melt-rate band, so it sits at the top of
admissibility by construction; the uncertainty runs **downward**.

⚠ **The scan grid does not contain the shipped cell** — its V axis jumps 4.5 → 6.0 and
V = 5.64 was solved by bisection. Reading the envelope off the grid alone gives an
admissible maximum of 86.5 cm and puts the shipped value *outside its own admissible
set*. The boundary cell is added explicitly.

⚠ Set values are the **offline** emulator's, the shipped value the **wired**
deliverable's. The port was 0.4% on the cell — far below the envelope, but not the
same code path.

### 2.2 The 2100 fast bias — characterised, three fixes REFUTED

It is the **driver, not the ice response** (0.99× on each GCM's own regional T vs 1.31×
through our law), and within the driver the **level, not the shape**: the law is
exactly `R_CMIP6(ΔT) × 1.2864`, one constant offset carried forward forever.

**Do not re-run these. Each is a result:**

| attempted | outcome | file |
|---|---|---|
| relax the offset with timescale τ | preferred τ **tracks the observational product** — ∞ (Berkeley Earth), 25 yr (3-product mean), 0 (GISTEMP). It calibrates the observational chain, not a decadal mode | `scope_gis_amp_relax_tau.py` |
| re-anchor to Berkeley Earth (sits on CMIP6, 1.011×) | BE is the **WORST** product against the observed melt record: shape err 0.233 vs HadCRUT5 0.102, needs a **1.71** rate scale, 59.5% of years in band vs 92.1%. It is also **the calibration driver** (`build_t_gis.py`: `hp = "HadCRUT5"`), so switching is a **recalibration** | `diag_gis_driver_product_skill.py` |
| find the same offset in GSIC and fix both | glacier blocks sit **below** CMIP6 at every frame (0.71–0.99) and barely move. **No common mechanism** | `diag_glac_amp_cmip6_offset.py` |

**And the premise is frame-dependent.** With obs *and* CMIP6 rebased to the same
window, obs/CMIP6 is **1.274× on the shipped 1850-1900 frame and BELOW 1 on all four
alternatives** (0.445–0.903). CMIP6's amplification is frame-robust (CV 0.014–0.054);
the observational estimate is not (CV 0.049–0.127) — in every Greenland zone and every
glacier block. `diag_gis_amp_baseline_sens.py`.

⚠ **Do NOT rebase to 1971-2000.** It is the worst modern window tested: obs amp 0.651
(Greenland warming *less* than global — not credible) and a product spread worse than
1961-1990. The Greenland cold anomaly sits inside it. **1995-2014 is best on both**
and is already the deliverables' frame.

**The one live thread**: a through-origin secant is not baseline-invariant, and once
the base sits mid-record the data straddle zero. An intercept-bearing estimator should
be tried before any frame is adopted. The ladder's non-monotonicity (1.513, 1.192,
1.111, 1.249, 1.068) is that showing through.

---

## 3. ⚠ `data/cmip6_pai` IS CORRUPT FOR THE MPI PAIR — and Antarctic work leans on it

Found by the new reducer's gate. `data/cmip6_pai` 1850-1900 **global** means:

| model | reference | ours (correct) |
|---|---|---|
| MPI-ESM1-2-LR | **279.31 K** | 286.68 K |
| MPI-ESM1-2-HR | **279.44 K** | 287.08 K |
| other 33 | 285.5 – 288 K | — |

279 K is 6 °C. **The error SURVIVES REBASING** — anomaly rms 0.13 K, and 2081-2100
global warming reads **2.62 K in the reference against 2.41 K here, i.e. 8.7% HIGH**.
So it is a spatial-sampling defect (the signature of a partial-grid intersection
between `tas` and `sftlf` coords), not a constant offset anomalies would cancel.

**Why it matters for the next phase:** `data/cmip6_pai` is the reduction behind the
PAI/A6 **Antarctic** amplification analysis — the one that produced the two-mode
fast/slow recommendation and the A6 prior re-centring. Any PAI computed as AIS/global
for those two models has an 8.7%-high denominator, biasing their PAI **low**.

**NOT re-run.** Corrected global + block series for all 45 models are on disk at
`data/cmip6_glac/` (they carry `tas_global`), so re-deriving PAI for the MPI pair is
cheap. Whether it moves the A6 conclusions is **unmeasured**.

---

## 4. WHERE THE LEVERAGE IS — the AIS numbers, ssp585, from the shipped deliverable

| horizon | component | median | share of total | p05–p95 |
|---|---|---|---|---|
| 2100 | Greenland | 13.90 cm | 14.7% | 4.78 |
| 2100 | **Antarctic** | 37.07 cm | 39.2% | **50.56** |
| 2300 | Greenland | 95.74 cm | 18.6% | 26.85 |
| 2300 | **Antarctic** | 281.69 cm | 54.8% | **252.33** |

**AIS spread is 10.6× Greenland's at 2100 and 9.4× at 2300.** At SSP2-4.5 the AIS 2300
band is **[15.4, 296.1] cm — a 19× range, wider than the whole total's spread.**

Known state, not re-verified this session:
* **AIS is the ONLY component still on stock MimiBRICK** — GSIC and Greenland were both
  replaced. That asymmetry is the obvious structural question.
* **It is the block that fails to converge.** `ais_iceflow0` R̂ has run **2.2–2.4 across
  recent vintages** (2.359 at L10, 2.449 at L11); **the L14 value has NOT been
  re-measured** — do not quote one without measuring it. This is what sets the
  projections-only rule.
* The 2100 distribution is **bimodal** (tipped / not tipped): quote a distribution,
  never a median difference. Vintage changes move the *tipping probability*.
* The red team recorded the AIS tail as **prior- rather than data-driven**.
* Prior sampler work was judged **not warranted**: no ridge to rotate, and the
  worst-mixing axis explains R² < 0.001 of the projection. It is a reporting caveat.

Entry points: `julia/diag_ais_spread_decomposition.jl`,
`julia/diag_ais_param_sensitivity.jl`, `julia/sweep_ais_oceantemp.jl`,
`outputs/diag_ais_spread_decomposition.csv`, memory `pai_cmip6_time`.

---

## 5. NON-OBVIOUS STATE

* **`python/reduce_cmip6_tas_glac.py` imports `build_t_glac.py`, which is a SCRIPT —
  importing it RE-RUNS it.** Deliberate (it is the only place the RGI polygons and
  GlaMBIE weights are built), but it re-stamps `t_glac_hadcrut5_provenance.md` with the
  current commit and re-renders a figure. The data CSVs are unchanged. **Check
  `git status` after running and revert the cosmetic pair.**
* **That reducer's gate is PLAUSIBILITY-FIRST by design** (our own 1850-1900 global mean
  must be 284–290 K), with the cross-check against `data/cmip6_pai` advisory and
  skipped on a member mismatch. It was originally a hard cross-check and **it pointed at
  the right discrepancy while I read the arrow backwards twice** — first blaming my own
  masks, then shipping a "fix" whose byte-identical output should have disconfirmed it
  immediately. Identical numbers after a change mean the change did nothing.
* **45 of 46 models reduced.** Excluded: `MCM-UA-1-0` (non-regular grid, no `lat`).
  `CNRM-CM6-1` is present but stops in 2020, so a 1901-2024 fit drops it.
* **`gis_targets.py` now parses the Julia constant** — `tap_cell()`, `tap_cell_label()`,
  `tap_tag()`, `ssps_csv()`. Use these rather than retyping the cell or building
  deliverable paths by f-string.
* **`plot_protect_forcing_matched.py` deliberately draws a SUPERSEDED cell** (the
  2026-08-21 one) because its input CSVs were produced at it. Constants are named
  `CELL_DATE`, and it prints the gap against the shipped cell at import. Do not
  "fix" the labels without regenerating the inputs.
* Every trap in `handoff_2026-08-23f` §5 and `handoff_2026-08-23e` §7 still applies.

---

## 6. FILES

**New:** `python/diag_gis_cascade_envelope.py`, `python/scope_gis_amp_relax_tau.py`,
`python/diag_gis_amp_variability.py`, `python/diag_gis_driver_product_skill.py`,
`python/diag_gis_amp_baseline_sens.py`, `python/reduce_cmip6_tas_glac.py`,
`python/diag_glac_amp_cmip6_offset.py`, `notes/memo_2026-08-23_greenland_module.md`,
`data/cmip6_glac/` (45 models, 1.4 MB), `outputs/mcmc/gis_block_convergence_L14.csv`,
`outputs/postpred_L14_*`, `outputs/ladrillo_model_comparison_L14*`,
`figures/ladrillo_L14_fig{1,2,3}_*`.
**Modified:** `run_ladrillo_tests.sh`, `LADRILLO.md`,
`julia/project_ssps_components_ladrillo.jl` (tap default), `julia/test_gis_tap_wiring.jl`,
`julia/diag_gis_block_convergence.jl`, `julia/greenland_3basin_component.jl`,
`julia/diag_protect_forcing_matched.jl`, `python/gis_targets.py`,
`python/build_protect_r2300_forcing.py`, `python/plot_protect_forcing_matched.py`,
`python/ladrillo_model_comparison.py`, `python/plot_ladrillo_memo_figures.py`,
`CHANGELOG.md`.

Commits `ae1ed11` → `6cd0a02` (12). Memories: `gis_l14_block_certified`,
`ratio_needs_native_scale`, and this session's amp findings — see `INDEX_slr.md`.

---

## 7. OPEN, IN PRIORITY ORDER

1. **ANTARCTICA** (§4). 55% of the 2300 total, 9–10× Greenland's spread, the only
   component still on stock MimiBRICK, and the block that fails to converge.
2. **Re-measure `ais_iceflow0` R̂ at L14** before quoting any AIS convergence number.
3. **Re-derive PAI for the MPI pair** with the corrected globals (§3) and check whether
   the A6 conclusions move.
4. **The cool arms' separation residual** — ssp126 0.90×, ssp245 1.19×; the reservoir
   is inert there by construction.
5. **The amp-law estimator** (§2.2) — the one live thread on a closed question.
6. **Marcus's prose** for module-memo §1 and §9, and a decision on whether the current
   state earns a `2.0` tag (no tag has been cut).
