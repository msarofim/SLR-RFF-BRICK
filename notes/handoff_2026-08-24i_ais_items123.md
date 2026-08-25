# Handoff — the AIS module assessed, and its top three fixes run

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, commits **`b4e17b5`** (the
component fork), **`8f66819`** (Coulon), **`1c2bf3c`** (items 1+3 results), and the CHANGELOG
entry `2026-08-24p`. Written 2026-08-24, to be picked up cold. **Continues**
`handoff_2026-08-24h_deficits_unresolved.md`, whose §7 items 1–2 were closed there;
this note is a new arc opened by Marcus asking for an AIS-module evaluation.

**One chain read** (2000 draws x 4 seeds, ~40 min). Items 2 and 3 read no chains at all.

⚠ **Read §0.5 first.** Marcus challenged two things after the run and both stuck: one of them
is a defect in this session's own envelope script (now fixed), and the other reframes what the
next run should be. §3 and §4 are correct as written but §0.5 supersedes their *framing*.

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

## 0.5. START HERE — MARCUS'S TWO CHALLENGES, AND WHAT THEY CHANGE

Marcus, 2026-08-24, on reading §3 and §4:

> *"Absurd SSP5-85 values is a reason to reject, unless there's a second correction that would
> fix that. For Coulon, if our posterior is too low, can't we just run a new scenario through
> FaIR to create a higher projection?"*

**Both land. The first exposes a defect in my own script, not a property of the anchor. The
second has an inverted premise, but the instrument it points at is the right one.**

### (A) He is right, and the mechanism is worse than §3 said

§3 called the ssp245@2300 anchor "untenable, which is itself informative". That was a
rationalisation of a **bug**. The anchor envelope rebuilds a rescaled arm as
`base + s*(arm - base)`. That identity is licensed by `[AFFINE]` and checked by
`[ANCHOR-EXACT]` — **but only at the scales those gates actually ran at, s = 1.42 and 1.70.**
The envelope then applied it at **s = 35.4 and s = 1240**, and printed the results as numbers.

Checked against the component's own ceiling (it reports `57.0*(1 - V/V0)`, so 57 m = 5700 cm
is total deglaciation):

| | |
|---|---|
| envelope cells **above total deglaciation** | **2 of 48** — worst **153210 cm = 26.9x THE WHOLE ICE SHEET** |
| cells at an **unverified** lambda rescale (> 3.0) | **28 of 48** |
| cells actually inside the verified domain | **18 of 48** |

⇒ **"Report the whole anchor envelope" was resting on cells that were mostly not licensed.**
The two impossible cells are not physics and never were — they are a locally-verified
linearity extrapolated ~700x, with no knowledge of the mass floor or the cone geometry.

**FIXED THIS SESSION.** `scope_ais_fastdyn_shape.jl` now carries `DEGLACIATION_CM = 5700.0`
and `SCALE_VERIFIED_MAX = 3.0`, tags every envelope cell `ok` / `UNVERIFIED` / `IMPOSSIBLE`,
prints `>57m` instead of a number, and reports the counts. The **shipped**
`outputs/scope_ais_fastdyn_envelope_L14.csv` has been given the same `domain` column in place,
so the 153210 cm cell cannot be retrieved unmarked.

**Is there a second correction that rescues the ssp245@2300 anchor? No.** The obvious
candidate is a saturating cap (`gmax`), and it fails on arithmetic: to bound ssp585 you need
`gmax` below roughly 1/12, which makes ssp585's flux **lower than stock** — the opposite of
the physics the whole arm exists to represent. The blow-up is structural: anchoring on the
**coldest** cell forces lambda to compensate for a tiny `g` there, and any monotone
`g(excess)` then amplifies that compensation at ssp585. **Reject the anchor.**

⚠ **What does NOT change:** the anchor-free ratio (§3) and the ssp585@2300-anchored table are
untouched — they run at s = 1.42 / 1.70, inside the verified domain, and `[ANCHOR-EXACT]`
re-ran both. Item 1's finding stands; the untenable-anchor rows go.

### (A2) The same instinct kills the n = 2 arm — and points at a FRACTIONAL n

Pushing on "absurd" one step further pays off. Coulon's own scenario separation is a external
check on how much separation is *credible*, and it was sitting in the item-2 numbers unused:

| TOTAL AIS @2300, high/low scenario ratio | |
|---|---|
| ours, **n = 0** (shipped binary form) | **2.14** |
| **Coulon 2025** (ssp585 270.0 / ssp126 56.5 cm) | **4.78** |
| ours, **n = 1** | **10.04** |
| ours, **n = 2** | **12.06** |

**Coulon sits between our n = 0 and our n = 1** — and their pair is ssp126-vs-ssp585, *wider*
than our ssp245-vs-ssp585, so on our own pair their ratio would be **smaller** still, pushing
the implied exponent further down. Indicative reading: **n ~ 0.3-0.5.**

⇒ **The binary form is wrong AND n = 1 overshoots; n = 2 is outside anything the literature
separation supports.** Next session should re-run the arm set as **n ∈ {0, 0.25, 0.5, 1}** and
**drop n = 2** to a stated boundary case, the way the MICI branch is handled. ⚠ This is a
two-anchor, cross-scenario, cross-forcing bracket — an orienting number, **not** a calibration
of n. Do not quote 0.3-0.5 as fitted.

### (B) "Run a new scenario through FaIR" — the premise is inverted, the instrument is right

**The premise first.** "If our posterior is too low" — our Antarctic **warming** is too low
(§4). Our **sea level** is too **HIGH** for that warming: ≥2.14x a forcing-matched Coulon.
Those are consistent, and §3 is why — the binary form over-credits cold worlds. **So running a
hotter scenario would push an already-high-for-its-forcing answer higher.** The two findings
are not independent problems to be fixed separately; they are the same finding twice.

**Mechanically**, a hotter FaIR run addresses only the GMST third of the gap (1.33x), not the
amplification third (1.28x). At `ais_gmst_amp` = 0.9447 you would need **GMST 12.7-18.0 °C**
to reach Coulon's 12-17 °C Antarctic — far outside any ssp585 — i.e. using the scenario to
compensate for a wrong amplification, which simultaneously breaks precipitation, the runoff
line and ANTO, all of which read the same `T_ant`. That is `hist_compensating` exactly.

**The right instrument is `ais_gmst_amp`** — it is the parameter that is wrong, it is sampled,
and its target is already measured (34-GCM median **1.143**; Coulon's four **1.205**; we
sample **0.9447**). **But it is NOT likelihood-inert, and that was MEASURED this session, not
assumed:**

| moving the median to CMIP6's 1.143 (x1.2099), 12 draws, ssp245 | |
|---|---|
| max abs delta over **1850-2024** | **0.110 cm** — against lambda's `[INERT]` **0.000e+00** |
| as a share of the **entire** 1.404 cm AIS calibration signal | **~8%** |
| delta at 2024 | **-0.056 cm** = **0.4 sigma** of the target's own band |
| delta at 2300 | **+34.4 cm** |

⇒ **Unlike lambda, this needs a REFIT.** And note the sign: raising amp *lowers* the hindcast,
so the likelihood will actively push back and partly undo the prior change. Budget for a full
recalibration, not a prior propagation.

**What IS worth running, and it is the good version of Marcus's suggestion:** a **diagnostic
arm at Coulon's forcing** — scale the GMST driver so our Antarctic warming reaches 12 / 14.5 /
17 °C and read the AIS band. One arm, no refit, and it completes the like-for-like in the
direction we actually control ("at *their* forcing, what does *our* model give?"). It also
tests whether our band is narrow because the model is over-confident or merely because our
forcing range is narrow. **This is the first thing to run next session.**
⚠ Scaling GMST moves ANTO and every other component too, so read the AIS component only and
say so.

Also cheap and worth checking first: our driver is `fair_mean_gmst_ssp585.csv`, a **mean over
configs**. The FaIR ensemble's hot tail may already span CMIP6-like forcing with no new
scenario at all — check before building one.

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
* ⚠⚠ **THE ANCHOR ENVELOPE HAS A DOMAIN AND ONLY 18 OF 48 CELLS ARE IN IT** (§0.5A). The
  arithmetic rebuild is verified at lambda rescales 1.42 and 1.70 only; the envelope applied
  it at 35.4 and 1240 and printed **153210 cm = 26.9x the whole ice sheet** as a number.
  `scope_ais_fastdyn_shape.jl` now tags every cell `ok` / `UNVERIFIED` / `IMPOSSIBLE` and the
  shipped CSV carries the same `domain` column. **Filter on `domain == "ok"` before reading
  `outputs/scope_ais_fastdyn_envelope_L14.csv`.** The ssp245@2300 anchor is REJECTED, and no
  saturating cap rescues it — bounding ssp585 needs gmax < ~1/12, which puts ssp585's flux
  BELOW stock.
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

**Re-ranked by §0.5.** Items 1 and 2 below are new and come straight out of Marcus's two
challenges; the old item 1 (the anchor) is resolved — **reject the ssp245@2300 anchor**.

1. **RUN: the diagnostic arm at Coulon's forcing** (§0.5B). Scale the GMST driver so our
   Antarctic warming reaches 12 / 14.5 / 17 °C, read the **AIS component only**, and answer
   "at their forcing, what does our model give?". One arm, no refit. Check the FaIR
   ensemble's own hot tail first — it may already span CMIP6 with no new scenario.
2. **RUN: re-do the arm set as n ∈ {0, 0.25, 0.5, 1}, dropping n = 2** to a stated boundary
   case (§0.5A2). Coulon's own scenario separation (4.78) sits between our n = 0 (2.14) and
   n = 1 (10.04), so the credible exponent is **fractional**. The current n = 1 / n = 2 arms
   bracket it but neither is the candidate.
3. **Marcus's call** on whether the magnitude-dependent arm ships as a flagged arm beside
   `UNRESOLVED_AMPLIFICATION` or stays a diagnostic. Only the **18 of 48** `domain == ok`
   envelope cells are admissible input to that decision.
4. **`ais_gmst_amp` ~ 0.94 is a live defect** — a *de-amplification* where 27 of 34 CMIP6 GCMs
   amplify, target median **1.143**. ⚠ **NOT likelihood-inert** (measured §0.5B: 0.110 cm over
   1850-2024 = ~8% of the entire calibration signal, 0.4 sigma at 2024), and raising it
   *lowers* the hindcast so the likelihood pushes back. **Budget a full refit, not a prior
   propagation.**
5. **The pooled-proposal tune run** (item 3's lever). Needs a tune chain + fresh certificate.
   Naturally combined with item 4 — both want a recalibration.
6. **The reconstruction mixing** (`-24h` item 1) — unchanged, Marcus's, and still demoted.
7. **The anchored net's counterintuitive sign** at ssp585@2300 (`-24e` §8 item 2).
8. **Wire the LWS GRACE extension** (`-24h` item 3) — still deferred by Marcus.
9. **WAIS/EAIS split** — ranked LOW deliberately. `diag_ais_region_lit_check.py` says closure
   is exact (4.5e-7) and WAIS carries the loss, but a **static shares term is not defensible**
   (EAIS drift **4.33 sigma**) and the whole-sheet rate is ~1 sigma from zero. High cost, and
   the data will not constrain the new degrees of freedom the way Greenland's did.
10. **The AIS observed driver**, **FrEDI linearity**, **Marcus's prose** — unchanged.

---

## 8. FILES AND COMMITS

**New:** `julia/antarctic_icesheet_magdep_component.jl`, `julia/scope_ais_fastdyn_shape.jl`,
`python/diag_ais_coulon_like_for_like.py`, `python/diag_ais_proposal_scaling.py`,
`outputs/scope_ais_fastdyn_{cells,envelope}_L14.csv`,
`outputs/diag_ais_{coulon_like_for_like,proposal_scaling_L14}.csv`,
`outputs/log_scope_ais_fastdyn_shape_L14.txt`.
**Modified:** `CHANGELOG.md` (`2026-08-24p`); `julia/scope_ais_fastdyn_shape.jl` (the §0.5A
domain guard); `outputs/scope_ais_fastdyn_envelope_L14.csv` (`domain` column added in place).
**Memories:** `ais_binary_form_priced`, `ais_coulon_not_like_for_like`,
`acceptance_rate_certifies_nothing` (all new); `INDEX_slr.md` Antarctica section +3 lines;
`MEMORY.md` SLR live-state and working-conventions extended.
**Commits:** `b4e17b5`, `8f66819`, `1c2bf3c`, the CHANGELOG commit, and this note.
