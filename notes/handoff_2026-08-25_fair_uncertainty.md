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

---
---

# ADDENDUM — 2026-08-25, after Marcus promoted the band

Commits **`2ba0893`** (three-SSP joint band + ranking), **`c67c54d`** (FaIRtoFrEDI), and the
CHANGELOG entry `2026-08-25c`. Supersedes §7's priority list above.

## A. WHAT MARCUS DECIDED, AND THE CHECK HE ASKED FOR

> *"I remember that an earlier analysis suggested that the fixed driver was good enough to
> match to the uncertain past: can you confirm that? If so, then yes, the joint band should
> become the reported band, and the other SSPs should add FaIR re-runs. After that is done,
> do a new priority ranking."*

**CONFIRMED, from `outputs/mcmc/slr_coupling_test.csv` (2026-08-01), on this branch.** The
mean-forcing calibration drops the te_α↔OHC coupling; that loss is **−1.38 cm = −2.3%** of
total@2100 width and **−0.55 cm** of the median. The directly-coupled TE component tightens
**29%**, the total moves 2.3%. The 2026-08-02 production run closed it: *"coupling immaterial
… Independent pipeline stands everywhere."* And the 2026-08-01 Marcus directive already
prescribes this method: propagate forcing FORWARD, never re-calibrate it against SLR.

⚠ **CAVEAT: established on extA108, not L14.** extA108 total@2100 median **46.9 cm** vs L14's
**94.7 cm** — 2.0× apart, different lineage, restructured AIS, different baseline. It
transfers as strong evidence, **not proof**. Re-testing it on L14 needs the joint calibration
machinery, which is banner-marked REJECTED and should stay that way.

## B. THE FORCING CONVENTION IS SETTLED — SPLICED

The canonical pipeline paired on each config's **full** forcing; this work spliced at 2014.
Run head-to-head on ssp585, both at 2000 draws:

| | spliced | raw |
|---|---|---|
| every median and spread, 12 cells | — | **agree to <1%** |
| **[CALIB-MOVE]** ais | **0.66 σ** | **3.68 σ** |

⇒ **raw buys nothing in the band and costs 5.6× on hindcast consistency. Use SPLICED.**
Per component the splice leaves **glaciers / GIS / LWS at exactly 0.0000 cm**; all the
movement is TE (**1.76 cm** worst draw-year, **0.42 cm typical**), because 2015–2024 is inside
the fit window and TE integrates OHC. A 2014→2024 splice-year shift is bounded *below* the
raw-vs-spliced perturbation (<1%) a fortiori, so it was **not** re-run.

## C. ⚠ ssp245@2300's MEDIAN IS A THRESHOLD ARTIFACT

`julia/diag_ais_tipping_under_forcing.jl` — closed form, no model run, same pairing seed:

| tipped @2300 | mean driver | per-config | median draw |
|---|---|---|---|
| ssp126 | 0.0% | 6.3% | never tipped |
| **ssp245** | **59.6%** | **48.3%** | **tipped → NOT tipped** |
| ssp585 | 100.0% | 99.2% | tipped either way |

The only cell of nine that crosses 50%, and exactly the one whose median moved: total
**219.07 → 162.84**, AIS **131.35 → 79.23 cm**. ⚠ **48.3% is knife-edge ⇒ bimodal-fragile
median. At ssp245@2300 quote the MEAN plus the tipped fraction, never the bare median.**
`mean_cm` and a per-draw dump at every horizon are now written so any statistic is
recomputable without a re-run.

## D. THE NEW PRIORITY RANKING

**The metric is ADDRESSABLE cm = spread(joint) × (1 − pct_forcing)** — the part of a band
generated inside BRICK rather than inherited from FaIR. Not band growth, and not
share-of-width (a p05–p95 spread is not additive; the share exceeded 100% under the fixed
driver, and the covariance residual here is +18% to +34%).

**⚠ THE TRAP: thermal expansion.** It takes **36–48% of everything the restored forcing adds**
and its band grows **6.2×** — and it is **84% forcing**. Ranking on growth puts TE **first at
five of six cells**; on addressable it is **last or near-last everywhere**.

| addressable share | 1st | 2nd | 3rd | 4th |
|---|---|---|---|---|
| ssp585@2300 | ais **82.7%** | gis 8.8% | te 5.0% | glaciers 3.5% |
| ssp245@2300 | ais **92.6%** | gis 2.7% | glaciers 2.6% | te 2.1% |
| ssp126@2300 | ais 33.2% | glaciers 28.4% | gis 20.9% | te 17.6% |
| **ssp126@2100** | **glaciers 40.1%** | te 22.6% | ais 21.9% | gis 15.4% |

### THE RE-RANKED WORK QUEUE

1. **AIS remains first at ssp245/ssp585 — on a corrected justification.** Not "94.7–100.9% of
   the spread" (a fixed-driver artifact) but **77–93% of the addressable** spread, and only
   **7–21% of its band is forcing**, so model work genuinely moves it. Within AIS the open
   items are unchanged: **`ais_gmst_amp` ≈ 0.94** (a de-amplification where 27 of 34 GCMs
   amplify; NOT likelihood-inert; needs a **refit**), then the **pooled-proposal tune run**
   (`--adcov=`), naturally combined since both want a recalibration.
2. **⚠ NEW — glaciers, at ssp126.** 40.1% of addressable at 2100 and 28.4% at 2300, and only
   33–49% forcing. The glacier module has had **no** attention in this arc. If ssp126 is a
   reported scenario, this is the second thing to do and it is currently unranked anywhere.
3. **GIS is a consistent, modest #2 at ssp585** (8.8% @2300, 26.9 cm addressable) — but 56–61%
   forcing, so the achievable gain is about half its band. Greenland is CLOSED as a module;
   do not reopen it for this.
4. **DE-PRIORITISE thermal expansion.** Biggest band growth, smallest addressable share.
   Its width is inherited from FaIR's OHC spread, not generated by BRICK. `te_α` work would
   move ~16% of a 94.8 cm band.
5. **Extend the joint band to the remaining SSPs** (ssp119/ssp370/ssp460) if they are to be
   reported — one `run_fair_ssp_spread.py <ssp>` each (~3 min) plus one Ladrillo run (~45 min).
6. **Everything else** — the anchored net's sign, reconstruction mixing, LWS GRACE extension,
   WAIS/EAIS split, the AIS observed driver, FrEDI linearity, Marcus's prose — unchanged.

## E. NON-OBVIOUS STATE ADDED HERE

* **Cubes are RAW now**; the splice lives in Julia behind `--forcing=`, gated by
  `[SPLICE-MATCH]` (1.14e-06 °C against a **2e-06 tolerance derived** from the 6-decimal write
  precision, not picked). The python-spliced ssp585 cubes were removed as derivable.
* `julia/scope_slr_fair_uncertainty.jl` takes `--ssp=` and `--forcing=`; outputs are keyed
  `_<ssp>_<forcing>_<tag>`. It reads **all five** components plus the total, and **[SUM]**
  checks the decomposition closes per draw (~2e-13 cm).
* **LWS is exactly 0.00 cm of spread everywhere** — a seeded constant with no forcing
  dependence. Not a bug; do not go looking for its uncertainty.
* ⚠ `run_fair_ssp_spread.py`'s ssp585-only Coulon-arm block **used to `sys.exit(0)` before the
  cube block**, so ssp245/ssp126 cubes were silently not written. Fixed by moving the cube
  block above the guard. Check output files exist, not just that a script exited 0.
* ⚠ `git add -A outputs/` sweeps in **227 deliberately-untracked** mcmc artifacts. Stage the
  intended files by name.
* ⚠ A `pgrep -f "<script>.jl"` wait-loop **matches its own shell** and never exits. Match on
  PID, or on a pattern the waiter itself does not contain.
