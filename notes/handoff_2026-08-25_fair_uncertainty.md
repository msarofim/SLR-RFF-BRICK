# Handoff — the Coulon pre-check, two retractions, and the climate uncertainty put back in

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, commits **`57549ad`** (Coulon
arm), **`3c14b88`** (item 2), **`3945995`** (FaIR uncertainty), plus CHANGELOG entries
`2026-08-24q`, `2026-08-25a`, `2026-08-25b`. Also `FaIRtoFrEDI` commits **`8b7bde5`** and the
cube-writing follow-up. Written 2026-08-25, to be picked up cold. **Continues**
`handoff_2026-08-24i_ais_items123.md`, whose open items 1 and 2 are closed here.

**Three chain reads + one FaIR run.** ~2h wall clock. **NOTHING WAS RECALIBRATED.**

⚠ **Two things the previous handoff asserted did not survive.** Both are in §1. Neither
touches the structural findings; both touch the *evidence* offered for them.

---

## 0. THE ONE-PARAGRAPH VERSION

The pre-check the last handoff asked for — *does our own FaIR hot tail already reach Coulon's
forcing?* — came back **YES**, so no scenario was invented and the arm uses **real configs**.
Driving the L14 posterior at Coulon's own Antarctic warming shows the **"2.4x narrower band"
was a forcing-range artifact** (at matched forcing our spread is **1.01x** theirs) and that
the displacement is **forcing-dependent** (>=2.14x at our forcing, **1.82x** at their
midpoint). Item 2's rationale — a fractional exponent from Coulon's 4.78 separation — is
**RETRACTED**: that ratio was **mid/mid of two models that disagree 37x**, and per model the
separation spans **2.43x-91x** and rejects every arm. Finally, on Marcus's instruction, the
**climate uncertainty is back in**: pairing 2000 draws with 841 FaIR configs widens the
**total** band **1.52-1.63x**, and the assessment's own framing number — *AIS is 94.7-100.9%
of the total spread* — turns out to be a **fixed-driver artifact**, falling to **73-79%**.

---

## 1. THE TWO RETRACTIONS — read before quoting anything from `-24i`

### (A) "Coulon's 4.78 separation implies a fractional n ~ 0.3-0.5" — RETRACTED

`-24i` §0.5A2 formed **one** high/low ratio from Coulon Table 1 as mid(267,273)/mid(3,110) =
**4.78**, placed it between our n=0 (2.14) and n=1 (10.04), and read off n ~ 0.3-0.5.
Verified against the paper (PMC12680641), the pairing is:

| ice-sheet model | ssp585 @2300 | ssp126 @2300 | **separation** |
|---|---|---|---|
| Kori-ULB | 2.67 m | 1.10 m | **2.43x** |
| PISM | 2.73 m | 0.03 m | **91.0x** |

The two models **disagree 37x at ssp126**, so averaging before dividing manufactured a
precision neither has — `endpoint_division_is_not_a_ratio_band`. Per model the span
**2.43x-91x contains all five arms and selects none**.

**And it was not like-for-like either.** Their pair is ssp126-vs-ssp585; the 2.14 was our
**ssp245**-vs-ssp585. On the matched pair our n=0 total ratio is **20.88x** — *above* the
4.78 it was placed *below*. **The direction of the inference reverses.**

⇒ **The structural case against the binary form is untouched** (an 11.6x range of
above-threshold excess charged one flux). **Only the evidence for a particular n is gone.
No exponent is currently selected by anything.**

### (B) "our entire posterior sits below Coulon's coldest GCM" — TRUE, but it is the DRIVER

`ladrillo_setup` builds **one** `gmst` vector; every draw sees it. The driver is the **MEAN**
over FaIR's 841 configs. The spread had never been written to disk:

| ssp585 GMST @2300, degC vs 1995-2014, 11-yr | p05 | p50 | **p95** | max | **shipped driver** |
|---|---|---|---|---|---|
| 841 configs | 3.49 | 6.56 | **11.25** | 21.39 | **6.95** |

**16 of 841 configs** clear T_ant = 12 degC at the posterior-median amp. So the gap is
substantially the **mean-driver choice**, not the model's reachable forcing.
⚠ This does **not** clear `ais_gmst_amp` = 0.9447 (still a de-amplification where 27 of 34
GCMs amplify) — open item 4 in `-24i` stands.

---

## 2. WHAT WAS BUILT

* `FaIRtoFrEDI/run_fair_ssp585_spread.py` — `run_fair_ssps.py`'s ssp585 branch with the
  `.mean(axis=1)` removed. Writes the percentile bands, the three arm drivers, and the full
  **841-config spliced GMST+OHC cube**. `[MEAN-MATCH]` reproduces the shipped driver at
  **8.9e-16 degC**; `[SPLICE-INERT]` is **exactly 0** pre-2014.
* `julia/scope_ais_coulon_forcing.jl` — AIS at Coulon's forcing, 4 arms. ~25 min.
* `julia/scope_slr_fair_uncertainty.jl` — the joint FaIR x BRICK band. ~45 min.
* `julia/scope_ais_fastdyn_shape.jl` — **modified**: `EXPONENTS = {0, 0.25, 0.5, 1, 2}` with
  n=2 demoted to a flagged BOUNDARY arm; `SSPS` gains **ssp126**; the separation block is
  generalised over named pairs and reports the external check **per model**.

---

## 3. AIS AT COULON'S FORCING (`scope_ais_coulon_cells_L14.csv`)

Arms are **real FaIR configs** at ensemble percentiles **98.0 / 99.4 / 99.8**, spliced at
2014. A pctile-99.8 config is a rare draw and is labelled as one in every cell.

| arm | T_ant @2300 | AIS@2300 med | x Coulon's 270 | spread | **x their width** |
|---|---|---|---|---|---|
| control | 6.57 | 281.2 | 1.04x | 252.4 | 0.48x |
| tant12 | 12.00 | 394.9 | 1.46x | 370.3 | 0.71x |
| **tant14** | 14.06 | **491.7** | **1.82x** | 527.7 | **1.01x** |
| tant17 | 16.64 | 581.4 | 2.15x | 709.0 | 1.36x |

**Gates:** `[CONTROL]` **+0.0000 cm** on all three horizons; `[CALIB-MOVE]` **0.09-0.48 sigma**
of the AIS target's own sigma; `[BASEYEAR]` the 2015-vs-1995-2014 offset is **0.337 cm**.

**(1) The "2.4x narrower band" was a forcing-range artifact** — at matched forcing our spread
is **1.01x** theirs, and that is our *parametric* spread alone against their parametric
**plus** GCM spread.

**(2) ⚠ THE DISPLACEMENT IS FORCING-DEPENDENT AND THE TWO NUMBERS ARE DIFFERENT QUANTITIES.**
`>=2.14x` moved **Coulon down to us**; `1.82x` moves **us up to them**. The gap **shrinks as
forcing rises** — which is what the binary form predicts, since it over-credits **cold**
worlds. **Never quote one as the other; state the forcing with every ratio.**

**Unchanged:** the sign. We are displaced high at every forcing tested.

⚠ **AIS component ONLY.** A hotter GMST moves ANTO, the runoff line, precipitation, glaciers,
Greenland and TE too.

---

## 4. ITEM 2 RE-RUN (`scope_ais_fastdyn_separation_L14.csv`)

All **nine** `[FORK]` cells at **+0.0000 cm** (ssp126 included); `[INERT]` **0.000e+00** on
all three scenarios. Anchor-free ssp585/ssp245 fast-dynamics ratio @2300:

| n = 0 | 0.25 | 0.5 | 1 | 2 *(boundary)* |
|---|---|---|---|---|
| **1.87** | 3.89 | 9.07 | 47.92 | 1400 |

ssp245@2300 fast dynamics: **110.0 -> 47.6 -> 18.8 -> 3.09 -> 0.088 cm**. The fractional arms
fill in smoothly; nothing pathological between n=0 and n=1.

**The matched-pair reading, and it needs no ratio.** At **ssp126 the fast-dynamics term is
EXACTLY 0.000 cm at every horizon in every arm** — no draw tips at all. Our ssp126 AIS@2300
is **13.5 cm** against Kori-ULB's **110 cm**: **~8x low at the low scenario while sitting at
1.04x at ssp585.** That asymmetry is the scenario-separation problem stated in **levels**,
and it is far better evidence than a ratio whose external comparator spans 2.43x-91x.

---

## 5. THE CLIMATE UNCERTAINTY, PUT BACK IN (`scope_slr_fairunc_cells_L14.csv`)

**Marcus, 2026-08-25:** *"use the FaIR uncertainty if we are comparing to analyses that
include climate uncertainty."* **Treat as standing.**

Each of 2000 draws paired with one of 841 configs by a seeded permutation.
**Gates:** `[PAIRING]` 841/841 used 2-3x each, assigned dGMST@2300 matching the whole cube
(p05 3.42/3.45, p50 6.58/6.58, p95 11.33/11.32); `[CONTROL]` **+0.0000 cm on all six cells**;
`[CALIB-MOVE]` ais **0.66 sigma**.

| spread, cm rel 1995-2014 | fixed | joint | **widening** |
|---|---|---|---|
| ais @2300 | 252.36 | 303.07 | 1.20x |
| **total @2100** | 50.13 | 81.94 | **1.63x** |
| **total @2150** | 94.92 | 147.38 | **1.55x** |
| **total @2300** | 253.44 | 385.07 | **1.52x** |

**THE REFRAMING.** `-24i` opened on *"AIS is 94.7-100.9% of the total p05-p95 SPREAD at every
cell"* and that framed the whole assessment. **It was measured under a fixed driver:**

| AIS share of total spread | 2100 | 2150 | 2300 |
|---|---|---|---|
| fixed | 100.9% | 99.9% | 99.6% |
| **joint** | **77.9%** | **73.1%** | **78.7%** |

The smooth components respond to forcing far more directly than AIS, whose spread is already
the lambda prior. ⇒ **"AIS is not a component of the uncertainty, it IS the uncertainty" is a
statement about the fixed-driver band, not about the model.** Still the largest single
contributor; no longer effectively the only one.

**Medians move only -1.3% to -5.4% ⇒ a WIDTH result, not a level one.**

---

## 6. NON-OBVIOUS STATE / TRAPS

* ⚠ **SPLICED, NOT RAW, and the reason is the posterior.** L14 was calibrated on the shipped
  historical driver; a config's own hindcast makes the posterior inconsistent with the
  forcing it is conditioned on. Splice at 2014; `[CALIB-MOVE]` measures the residue.
* ⚠ **PRIOR PROPAGATION, NOT A REFIT.** Right for COMPARISON against ensembles carrying
  climate uncertainty; **not** a recalibration. The shipped panel is unchanged.
* ⚠ **A percentile PATH is not a trajectory.** Build arms from real configs.
* ⚠ **The cube CSVs are 3.4 + 4.0 MB** in `data/observations/`. Regenerate rather than copy.
* ⚠ **OHC reaches `thermal_expansion` ONLY** (`brick_mengel.jl:92-95`); AIS and ANTO read
  `model_global_surface_temperature`. An AIS-only arm is a pure GMST override.
* `ladrillo_setup` costs **0.54 s warm**, so per-config setup is affordable (841 = ~7.6 min);
  `_yearmap` is the file loader if you need the shipped driver by hand.
* The `ssp245@2300` anchor remains **REJECTED** and only **18 of 48** envelope cells are in
  the verified domain — filter `domain == "ok"` (unchanged from `-24i`).
* ⚠ **A `git checkout` on a dirty file destroyed 17 uncommitted lines of
  `FaIRtoFrEDI/CLAUDE.md` this session.** Restored verbatim from context and verified at
  `17 insertions(+)`. It is unstaged, as it was. **Do not run `git checkout <file>` on a
  modified file.**

---

## 7. OPEN, IN PRIORITY ORDER

1. **Marcus's call: does the joint-uncertainty band become the reported band?** §5 changes the
   headline SLR error bar by 1.5-1.6x and re-ranks what dominates it. It is a comparison
   instrument today; making it the deliverable is a methodological choice, not mine.
2. **Re-do the AIS-module assessment's priorities under the joint band.** Every ranking in
   `-24i` was computed at AIS = ~100% of the spread. At 73-79%, thermal expansion, glaciers
   and Greenland are no longer negligible contributors to the error bar.
3. **`ais_gmst_amp` ~ 0.94 is still a live defect** — a de-amplification where 27 of 34 CMIP6
   GCMs amplify, target median 1.143. **NOT likelihood-inert** (0.110 cm = ~8% of the whole
   calibration signal), so **budget a full refit**. §1B does NOT close this.
4. **The pooled-proposal tune run** (`-24i` item 3's lever, `--adcov=`). Naturally combined
   with 3 — both want a recalibration.
5. **Extend the joint band to the other SSPs.** Only ssp585 has a cube; ssp126/245 need one
   `run_fair_ssp585_spread.py` run each with `SSP` changed.
6. **Whether the magnitude-dependent arm ships** as a flagged arm — Marcus's, unchanged, and
   now with no exponent selected (§1A).
7. **The reconstruction mixing**, **the anchored net's sign at ssp585@2300**, **the LWS GRACE
   extension**, **WAIS/EAIS split**, **the AIS observed driver**, **FrEDI linearity**,
   **Marcus's prose** — all unchanged from `-24i` §7.

---

## 8. FILES AND COMMITS

**New:** `julia/scope_ais_coulon_forcing.jl`, `julia/scope_slr_fair_uncertainty.jl`,
`FaIRtoFrEDI/run_fair_ssp585_spread.py`,
`data/observations/fair_{pctile_gmst,coulon_arm,cube_gmst,cube_ohc}_ssp585*.csv`,
`outputs/diag_fair_ssp585_hot_tail.csv`,
`outputs/scope_ais_coulon_{cells,paths,gates}_L14.csv`,
`outputs/scope_slr_fairunc_{cells,paths,gates}_L14.csv`,
`outputs/scope_ais_fastdyn_separation_L14.csv`, and the three logs.
**Modified:** `julia/scope_ais_fastdyn_shape.jl`, `CHANGELOG.md`.
**Memories:** `ensemble_mean_driver_hides_the_tail`, `coulon_narrow_band_was_forcing_range`,
`ais_share_was_a_fixed_driver_artifact` (new); `ais_binary_form_priced` and
`ais_coulon_not_like_for_like` **corrected**; `INDEX_slr.md` +3 lines and 2 edits;
`MEMORY.md` live-state extended.
**Commits:** `57549ad`, `3c14b88`, `3945995`, the three CHANGELOG commits, and this note.
