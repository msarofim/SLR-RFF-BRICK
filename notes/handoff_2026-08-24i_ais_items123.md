# Handoff — the AIS module assessed, and its top three fixes run

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, commits **`b4e17b5`** (the
component fork), **`8f66819`** (Coulon), **`1c2bf3c`** (items 1+3 results), and the CHANGELOG
entry `2026-08-24p`. Written 2026-08-24, to be picked up cold. **Continues**
`handoff_2026-08-24h_deficits_unresolved.md`, whose §7 items 1–2 were closed there;
this note is a new arc opened by Marcus asking for an AIS-module evaluation.

**One chain read** (2000 draws x 4 seeds, ~40 min). Items 2 and 3 read no chains at all.

---

## 0. THE ONE-PARAGRAPH VERSION

Marcus asked for strengths/weaknesses/improvements on the AIS module, then for the top three
improvements to be run. The framing number is that **AIS is 94.7–100.9% of the total p05–p95
SPREAD at every scenario x horizon cell** while the calibration sees **1.404 cm** of
cumulative AIS signal over 1900–2025 — a **200x** extrapolation. Three fixes ran and all
three landed. **(1)** DAIS's binary fast-dynamics flux is worth **26–750x** of the
scenario separation and **84%** of the ssp245@2300 median. **(2)** The Coulon 2025
comparison was never like-for-like — their forcing is **1.83–2.59x** ours — and correcting it
**flips the sign** of the shipped reading. **(3)** Four RAM proposals disagree **347x** in
shape while every acceptance rate sits on 0.234.

---

## 1. THE FRAMING NUMBERS (recompute before quoting; both are one-liners)

From `outputs/ssps_components_2300_L14.csv`:

| cell | AIS share of MEDIAN | **AIS share of SPREAD** |
|---|---|---|
| SSP2-4.5 @2100 | 12.4% | **94.7%** |
| SSP5-8.5 @2100 | 39.2% | **100.9%** |
| SSP2-4.5 @2300 | 60.0% | **98.9%** |
| SSP5-8.5 @2300 | 60.1% | **99.6%** |

From `outputs/recalib_targets_ext.csv`: the AIS target spans **1.404 cm** 1900–2025, mean 1σ
band **0.141 cm**. The ssp585@2300 median is 281 cm ⇒ **200x** the calibrated range.
Re-running `python/diag_ais_region_lit_check.py` adds: the IMBIE **whole-sheet** loss rate is
only **0.95–1.44 σ from zero** across four windows; WAIS carries 89–100% of it; EAIS is
indistinguishable from zero (0.02–0.25 σ).

⇒ **AIS is not a component of the uncertainty, it is the uncertainty**, and every weakness
below is a weakness of the whole model's error bar.

---

## 2. WHAT WAS BUILT

* `julia/antarctic_icesheet_magdep_component.jl` — **verbatim fork** of MimiBRICK v2.0.0's
  DAIS (the `edplP` package dir the Manifest actually resolves to) with the fast-dynamics
  flux generalised to `-lambda * g * const`, `g = (excess/ref)^n`. Three added parameters,
  three added reporting variables, one rewritten block, all flagged `## MAGDEP`.
* `julia/scope_ais_fastdyn_shape.jl` — propagates n over the L14 posterior. ~40 min.
* `python/diag_ais_coulon_like_for_like.py` — 3 blocks, seconds, no chains.
* `python/diag_ais_proposal_scaling.py` — 4 blocks, seconds, no chains.

---

## 3. ITEM 1 — the binary form, priced

Stock DAIS (`antarctic_icesheet_component.jl:180-184`) disintegrates at a **constant flux**
the moment `T_ant` clears `T_crit` and forever after. Measured on this posterior:

| cell | median above-threshold excess | tipped |
|---|---|---|
| ssp245@2300 | **0.391 degC** | 59.6% |
| ssp585@2300 | **4.529 degC** | 100.0% |

**11.6x apart, charged the same flux.** Anchored so ssp585@2300 keeps its shipped median:

| cell | n=0 (shipped) | n=1 | n=2 |
|---|---|---|---|
| **ssp245@2300** | 131.3 | **28.4** | **23.5** |
| ssp585@2100 | 37.1 | 14.5 | 9.5 |
| ssp585@2150 | 94.3 | 60.5 | 44.0 |

**The anchor-free number** (a lambda rescale multiplies numerator and denominator alike), the
ssp585/ssp245 ratio of the fast-dynamics contribution @2300: **1.87 -> 47.9 (n=1) -> 1400
(n=2)** ⇒ the binary form compresses the scenario separation by **26x to 750x**.

At ssp245 the median draw contributes **zero** fast dynamics at 2100 and 2150 in every arm;
at 2300 the stock form gives **110 cm = 83.8% of the AIS median**, of which 97–99.9% vanishes.
The ssp245@2300 **band** is mostly the form too: **280.8 -> 48.8 -> 20.0 cm**.

**Gates.** `[FORK]` n=0 reproduces the SHIPPED projection at **0.0000 cm** on all six cells.
`[INERT]` 1850–2024 bit-identical at **0.000e+00** ⇒ likelihood-inert and prior-propagatable,
**measured**. `[AFFINE]` **APPROXIMATE** (2.2e-3 / 4.8e-3 of the band), so `[ANCHOR-EXACT]`
re-runs the headline anchor — agreement **<=3.4e-4 of the band**. `[GMAX]` max g 1.58 / 2.50;
`[FLOOR]` never bound.

---

## 4. ITEM 2 — Coulon was never like-for-like, and the sign flips

| Antarctic warming @2300, vs 1995–2014 | |
|---|---|
| **Coulon ssp585** | **+12.0 to +17.0 degC** |
| **ours** | **+5.46 to +7.72 degC** — the WHOLE `ais_gmst_amp` p05–p95 |

Our entire posterior sits below their coldest GCM; our p95 draw reaches **64%** of it. The gap
decomposes and compounds (**1.28 x 1.33 = 1.69x** at 2100): amplification **0.9447** vs a
34-GCM median **1.143** (Coulon's four: 1.205; **29 of 34** above our median, **19** above our
p95; we **de-amplify** where 27 of 34 GCMs amplify), times GMST 4.69 vs 6.23 degC.

Interpolated to our forcing Coulon gives **~131 cm** vs our **281 cm = 2.14x** — and because
the response is **convex** across the retreat threshold, 131 is an **upper** bound and 2.14x a
**LOWER** bound on the displacement.

⇒ **The shipped "inside Coulon's band, displaced high, 2.4x narrower" reverses: we are
displaced high by MORE than recorded.** Do not re-quote the old form.

---

## 5. ITEM 3 — the sampler

| | |
|---|---|
| acceptance, 4 seeds | **0.237 / 0.235 / 0.236 / 0.236** vs a 0.234 target |
| adapted-shape disagreement | **87x, 198x, 347x** |
| reproducible NARROW direction | `ais_ocean_temperature0`, `antarctic_alpha`, `anto_beta` at **0.08–0.10x** of seed2026, in all three comparison seeds |

Those three enter the grounding-line speed through the **same product**
(`antarctic_icesheet_component.jl:153`) — a real degeneracy, onto which RAM collapses the
proposal in three runs of four. **The global scale converged perfectly in every run and told
us nothing about the shape.**

**The lever:** `calibrate_mcmc_ext.jl:1613-1623` seeds every production proposal from a
**single** chain's adaptation (every candidate is `_seed2026`), and seed2026 is the **widest**
of the four, not a consensus. `--adcov=` already exists ⇒ **no code change needed**.

⚠ **Item 3 is a proposal for the next production run, not a result.** It changes the sampler,
so it needs a tune chain and a fresh certificate before anything is re-quoted.

---

## 6. NON-OBVIOUS STATE / TRAPS

* ⚠ **`ref_excess` is a DOMAIN requirement, not a normalisation.** Left at 1.0 degC, n=2
  applies g up to 51, exhausts the sheet, and **stock DAIS's own cone geometry inverts** —
  its `ais_radius^1.5` throws a DomainError on a negative radius. It is now the median
  above-threshold excess at a named anchor cell, computed from the draws + the deterministic
  GMST path with **no model run**.
* ⚠ **Stock DAIS has NO mass floor on disintegration.** The fork adds one and counts bindings.
* ⚠ **The anchor for item 1 is UNRESOLVED and is Marcus's.** Anchoring on ssp245@2300 needs a
  lambda rescale of 35x (n=1) / 1240x (n=2) and gives absurd ssp585 values ⇒ untenable, which
  is itself informative. The whole envelope is in
  `outputs/scope_ais_fastdyn_envelope_L14.csv`.
* ⚠ **Standardize before ANY eigendecomposition of these covariances.** Raw cond **1.9e16**;
  a first pass in raw units returned eigenvectors loading **1.000 on `ais_slope` at BOTH ends**
  of the spectrum and read like a finding.
* `Mimi.replace!` **keeps the slot name**, which is why `ladrillo_run_draw!` needed no change
  to drive the fork — the same property `brick_mengel.jl` relies on for the glacier slot.
* Julia **soft scope**: any `for` loop at top level that assigns to a global needs wrapping in
  a function. Cost two smoke iterations here and two in the `-24h` work.
* `NOTHING WAS RECALIBRATED.` `outputs/recalib_targets_ext.csv` is unchanged and still carries
  the LWS hold-flat fiat. The magdep component is **not** wired into any production path.

---

## 7. OPEN, IN PRIORITY ORDER

1. **Marcus's call on the item-1 anchor**, and on whether the magnitude-dependent arm ships as
   a flagged arm beside `UNRESOLVED_AMPLIFICATION` or stays a diagnostic. Everything needed to
   decide is in `outputs/scope_ais_fastdyn_{cells,envelope}_L14.csv`.
2. **`ais_gmst_amp` ~ 0.94 is a live defect** — a *de-amplification* where 27 of 34 CMIP6 GCMs
   amplify. It is a **sampled** parameter, so unlike the GMST half it is directly fixable, and
   the CMIP6 target (34-GCM median **1.143**) is already measured and on disk.
3. **The pooled-proposal tune run** (item 3's lever). Needs a tune chain + fresh certificate.
4. **The reconstruction mixing** (`-24h` item 1) — unchanged, Marcus's, and still demoted.
5. **The anchored net's counterintuitive sign** at ssp585@2300 (`-24e` §8 item 2).
6. **Wire the LWS GRACE extension** (`-24h` item 3) — still deferred by Marcus.
7. **WAIS/EAIS split** — ranked LOW deliberately. `diag_ais_region_lit_check.py` says closure
   is exact (4.5e-7) and WAIS carries the loss, but a **static shares term is not defensible**
   (EAIS drift **4.33 sigma**) and the whole-sheet rate is ~1 sigma from zero. High cost, and
   the data will not constrain the new degrees of freedom the way Greenland's did.
8. **The AIS observed driver**, **FrEDI linearity**, **Marcus's prose** — unchanged.

---

## 8. FILES AND COMMITS

**New:** `julia/antarctic_icesheet_magdep_component.jl`, `julia/scope_ais_fastdyn_shape.jl`,
`python/diag_ais_coulon_like_for_like.py`, `python/diag_ais_proposal_scaling.py`,
`outputs/scope_ais_fastdyn_{cells,envelope}_L14.csv`,
`outputs/diag_ais_{coulon_like_for_like,proposal_scaling_L14}.csv`,
`outputs/log_scope_ais_fastdyn_shape_L14.txt`.
**Modified:** `CHANGELOG.md` (`2026-08-24p`).
**Memories:** `ais_binary_form_priced`, `ais_coulon_not_like_for_like`,
`acceptance_rate_certifies_nothing` (all new); `INDEX_slr.md` Antarctica section +3 lines;
`MEMORY.md` SLR live-state and working-conventions extended.
**Commits:** `b4e17b5`, `8f66819`, `1c2bf3c`, the CHANGELOG commit, and this note.
