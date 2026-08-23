# Handoff — τ is retired, the onset's premise is spent but its VALUE survives, the 2100 target passed a gate it had never been given, and the answer is to move the CELL, not the onset

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, through `01e89bb`.
Written 2026-08-23, to be picked up cold.

**Supersedes** `handoff_2026-08-23_commitment_evidence.md` for its **§4 work queue**
(items 1, 2 and 3 are all now done or answered) and for the expectation in its §4 item 2
that "2100 will move and that is a feature". Its §1, §2, §3, §6, §7, §8 and §9 are
**unchanged and still load-bearing** — especially the §9 trap list.

**Decision layer** is still `notes/scoping_2026-08-23_leq_options.md`, but its §5
RECOMMENDED ORDER is now spent: step 1 (onset re-scan) and step 2 (pin V) are done, and
they came out the other way round from what it expected.

---

## 0. THE ONE-PARAGRAPH VERSION

Three things ran, in the order the prior handoff asked for. **(1) §4.1, open since
2026-08-22, is done and it RETIRES τ** — at fixed ψ, τ 800→2700 yr moves a discounted
2030–2300 NPV by **0.01–0.39 %** at ssp585 and by **exactly zero** at ssp245/ssp126,
across a 4×2 block of discount rates and damage elasticities. **ψ is 20–60× more
valuable and the onset more still.** **(2) The onset re-scan found the shipped 4.69 K
onset does not do the job it was chosen for** — it was "the don't-move-2100 constraint"
evaluated on *our* driver, which crosses 4.69 K at 2100 by construction, while the four
GCM cells carrying the 2100 evidence cross at **2069/2078/2082/2087**. **(3) But when
Marcus set the horizon weights (2100 > 2300 > 3001) the onset STAYED at 4.69 K under
every weight set, and the CELL moved instead** — from V=1 m/τ=800 (ψ 0.125) to
**V=7.42 m / τ=2700 / ψ=0.275**, 1.42× better, and exactly the ψ that Greve@3001 and the
2250–2300 rate criterion had already pinned from two horizons 900 years apart. **Nothing
was wired, no gate moved, no cell moved, nothing refit.**

---

## 1. THE ANSWER, IF YOU READ NOTHING ELSE

**Wire this cell.** It is a prior-propagated change: G-INERT exactly 0.0, no refit, no
recalibration, same class of move as `gis_amp`.

| | V | τ | onset | ψ = 100·V/τ | w-score (3:2:1) | 2100 ratio | ssp585@2300 |
|---|---|---|---|---|---|---|---|
| shipped cell A | 1.00 m | 800 yr | 4.69 K | 0.125 | 0.584 | 1.43× | 70.4 cm |
| **WINNER** | **7.42 m** | **2700 yr** | **4.69 K** | **0.275** | **0.412** | 1.47× | **99.4 cm** |
| baseline (no reservoir) | — | — | — | — | 0.885 | 1.32× | 49.5 cm |

**Three independent determinations of ψ agree:** Greve@3001 requires 0.179–0.341 (median
0.242); the 2250–2300 rate criterion gives 0.273–0.282; this scan selects 0.275. **V =
7.42 m is the whole sheet, which the CLIMBER-X volume check already cleared (7.30–7.68).**
So handoff §4 item 3 — "pin V to the ladder and let τ follow from ψ" — is answered as a
by-product and is **self-consistent**.

⚠ `ssp585@2300 = 99.4 cm` sits almost exactly on the **~100 cm (70–230)** physics bracket
in memory `protect_matched_forcing`. That is encouraging and **it has NOT been scored
against that bracket** — do it before quoting the agreement as a result.

---

## 2. §4.1 — τ IS RETIRED, AND ONLY FOR DISCOUNTED USE

`python/diag_gis_npv_tau_sensitivity.py`. NPV 2030–2300 on **total** GMSL (L14 canonical,
untapped base, median). **No damage function is asserted**: the integrand is
`SLR(t)^ALPHA · exp(-RHO_NET·(t−2030))` scanned over `ALPHA ∈ {1,2}` × `RHO_NET ∈
{0.5,1,2,3}%`, where `RHO_NET` = consumption discount rate **minus** the growth rate of
exposed value. A verdict holding across the whole block is about **discounting**, not
about a damage-function choice.

**Ranking, max |ΔNPV/NPV|, SSP5-8.5:** τ **0.01–0.39 %** · ψ **1.04–8.51 %** · onset
**2.53–17.30 %**. At ssp245 and ssp126 both τ and ψ are **exactly zero** — neither
crosses the 4.69 K onset.

> ⚠ **DO NOT LET THE RETIREMENT LEAK.** τ still governs the **undiscounted 2300-level and
> commitment statements**, which is where the Greve/CLIMBER-X evidence lives. τ ≈ 2700 is
> still the right number; it just is not worth *identifying more precisely* for NPV.

**The marginal was computed, not assumed** — a threshold object can be spikier per-tonne
than in level. Finite-differenced against the FaIR 2.2.4 (calib 1.4.5) ssp245 CO₂-pulse
GMT response (a verified **near-step**) at three perturbation sizes; cell-to-cell **ratios**
are magnitude-free so the unknown per-tonne scaling and the un-modelled AIS/TE/glacier
marginals cancel. **ψ ratio = 2.184 exactly = 0.273/0.125** (strictly proportional);
**τ ratio 1.02–1.18**. Level verdict carries over.

**The finding nobody was looking for:** the per-tonne commitment term is **largest in the
MODERATE scenario**, which the shipped onset zeroes. At onset 2.0 K the ssp245 marginal is
**0.00956 cm/mK** vs ssp585's **0.00229 (4.2×)** — ssp245 sits *inside* the ramp, ssp585 is
past it and a pulse there only shifts the crossing year. At the shipped 4.69 K onset ssp245
is **exactly 0.00000**. An RFF-SP-weighted SC-GHG lives in that scenario space. Ordering
survives the never-scanned `RAMP_W_K` (2.4–6.5× over 0.5–4.0); only the ratio's size
depends on it. **This is now the strongest surviving argument for a lower onset, and §4's
weighting decision overrode it — see §6.**

---

## 3. THE ONSET RE-SCAN — TWO GATES CAUGHT TWO THINGS

`python/scope_gis_onset_rescan.py`. Scored on history (hard exactly-zero G-INERT) + 2100
(ISMIP6 16-model median) + 2300 (SICOPOLIS + the ssp585 matched band) + 3001 (SICOPOLIS),
5 CMIP6 cells, extended 1850–3001 axis. **The ssp245 2300 band was DROPPED as a gate**
(Marcus 2026-08-23) and is reported as a diagnostic in every table.

### 3.1 The G-INERT floor is 1.588 K, not 1.398 K — and it is now MEASURED
The first run scanned from a hardcoded 1.5 K and **the gate fired at 1.204e-04**. The floor
is **not** our own drivers' 1.398 K but **CNRM-CM6-1's own hot recent history, 1.588 K by
2023** — a driver that entered the scoring set only when the Greve/ISMIP6 GCM cells did.
Below 1.60 K the reservoir fires during the hindcast and prior-propagation becomes a
**REFIT**. Yelmo-REMBO's 1.68–1.76 K clears the floor by **0.092 K**; anything lower is
unreachable without refitting.

> ⚠ **The "calibration tops out at 1.385 K" figure in memory is OUR-DRIVER-ONLY.** It is
> the wrong floor for any scoring set containing GCM cells. The floor is now derived in
> `onset_floor()`, not typed.

### 3.2 The shipped onset's premise is spent
4.69 K exists because `gis_tap_priced_l13` records it as *"exactly the 'don't move 2100'
constraint"* — evaluated on **our** fair_mean ssp585 driver, which crosses 4.69 K at exactly
2100 **by construction**. Crossing years for every scored driver:

| driver | crosses 4.69 K |
|---|---|
| UKESM1-0-LL ssp585 | 2069 |
| CESM2 ssp585 | 2078 |
| CNRM-CM6-1 ssp585 | 2082 |
| CNRM-ESM2-1 ssp585 | 2087 |
| **our SSP5-8.5** | **2100** ← the driver it was tuned against |
| our SSP2-4.5, SSP1-2.6, CNRM-CM6-1 ssp126 | never |

On the actual shipped cell the 2100 median ratio **already moves 1.32× → 1.43×**. The onset
holds 2100 fixed on exactly one driver.

### 3.3 The trade, and a correction to the prior handoff
The prior handoff expected 2100 "to move, and treat that as a feature." **It moves, but
only upward** — the reservoir is additive and 2100 is already 1.32× the ISMIP6 median, so
**no onset can improve 2100.** Best 2300+3001 score by onset: **0.266 at 2.10 K vs 0.416 at
4.69 K (1.56×)** while the 2100 ratio goes **1.52× → 2.17×**. The late-horizon optimum at
2.10 K sits **inside** the ladder's 1.7–2.6 K range — independent corroboration, since
nothing in the scoring set knows about the ladders.

---

## 4. THE 2100 TARGET PASSED A GATE IT HAD NEVER BEEN GIVEN

`python/diag_gis_obs_scorecard.py`. The repo's own rule (prior handoff §2.2): gate a model
on the observed record before using its transient horizons. Greve **passed** and was used;
CLIMBER-X **failed** and was dropped. **ISMIP6 — which supplies the entire 2100 finding —
had never been gated.**

Hypothesis tested: if ISMIP6 under-runs observations, part of our 1.32× is the target's own
slow bias. **REFUTED by its own numbers.** ssp585/standard, 48 runs / 14 ice-sheet models,
2016–2050: **median 0.682 mm/yr = 1.15× the observed 0.593**, obs **inside** the spread,
**11/14 models at or above observations**.

> ⚠ **DIRECTION.** The ISMIP6 median is **FASTER** than the observed record, not slower.
> No correction is available and none should be applied: **our 1.32× is ours.**

⚠ **Caveat on the CONVENTION, not this run** — it attaches equally to the Greve and
CLIMBER-X verdicts already on record: the gate compares a **2016–2050 PROJECTED** rate to a
**1995–2024 OBSERVED** one. The projection window is later and warmer, so a well-behaved
model *should* exceed the observed rate. **It is a floor, not a calibration** — and read
that way the notable number is that **3/14 models fail to reach a PAST observed rate in a
FUTURE window**.

### 4.1 Our model vs observations — the hindcast is NOT the problem
The calibration-window total is **fitted** by the bisection (1.0000×) and is **not
evidence**. What is free:

| window | observed mm/yr | ours | ours/obs |
|---|---|---|---|
| 1900–1950 | 0.554 | 0.556 | 1.00× |
| 1950–1990 | 0.294 | 0.281 | 0.95× |
| 1993–2010 | 0.497 | 0.502 | 1.01× |
| 2010–2024 | 0.680 | 0.701 | 1.03× |
| **1995–2024** (the priority-1 rate) | **0.593** | **0.634** | **1.07×** |

1.07× is **better than the ISMIP6 median's 1.15×** on the same yardstick.

**The recent-end defect is ACCELERATION: 0.65× observed over 1993–2024** (quadratic coeff
+0.0094 vs +0.0146 mm/yr²). **We match the LEVEL and the RATE, under-run the CURVATURE, and
then arrive 1.32× high at 2100.** That combination is a *different* defect from the
commitment-law one and is now the binding item.

---

## 5. THE WEIGHTED VERDICT

Marcus set the weights: **2100 > 2300 > 3001**, "unless there is a good reason not to."
§4 tested the one candidate reason and it failed, so the weighting is **evidence-supported**,
not merely decision-relevant. Four sets scored — equal, 3:2:1, 4:2:1, 6:3:1.

**The onset does NOT move: 4.69 K wins every weight set, including equal.** §1 has the cell
that does move. The reservoir is worth having under every weighting (best **0.404** vs
baseline **0.752** at 6:3:1, **1.86×**).

> The onset's premise being bad did not make its VALUE wrong. §3.2 and §5 are both correct
> and they are not in conflict — do not "fix" one against the other.

---

## 6. THE ONE THING THE WEIGHTING OVERRODE, AND IT IS NOT CLOSED

§2's SC-GHG finding — that at the shipped onset the per-tonne commitment term in ssp245 is
**exactly zero**, while at onset 2.0 K it is 4.2× the ssp585 term — is **not addressed** by
the weighted verdict. The weighting scores **2100/2300/3001 LEVELS on ssp585-family GCM
cells**; it contains no per-tonne term and no moderate-scenario term at all.

**So the position is: onset 4.69 K is right for the 2300-level deliverable and leaves the
commitment term at exactly zero per tonne for an RFF-SP-weighted SC-GHG.** If the SLR
SC-GHG work (the CH₄-vs-CO₂ paper) is downstream of this model, that is a live conflict, not
a settled question. It needs a decision from Marcus, and the honest options are: accept it,
carry two onsets for two deliverables, or add a moderate-scenario term to the scoring set.
**Do not resolve it silently by picking whichever onset the current script defaults to.**

---

## 7. WHAT TO DO NEXT — AND THE ORDER MATTERS

1. **Score `ssp585@2300 = 99.4 cm` against the `protect_matched_forcing` physics bracket
   (~100 cm, 70–230)** before quoting the agreement. Cheapest item, and it either
   corroborates §1's cell or complicates it.
2. **Wire the §1 cell** (V=7.42 / τ=2700 / onset 4.69). Prior-propagated, G-INERT exactly
   0.0, no refit. This is the shippable result and it is what the last three sessions were
   for.
3. **The 2100 ACCELERATION deficit is now the binding defect.** It degrades under every cell
   (1.32→1.47×), no onset and no ψ fixes it, and §4.1 localises it: 0.65× observed
   curvature over 1993–2024 with the level and rate both right. That is a **fast-channel
   shape** question, not a commitment question — a genuinely new thread.
4. **Take §6 to Marcus** as an explicit choice. It is the only place the weighted verdict
   and the SC-GHG evidence point different ways.
5. **Do NOT** re-propose: options C, D, γ, any completely-monotone family, `RAMP_W_K`, the
   single-constant T-space form (all dead, prior handoff §6), **or** τ identification at
   fixed ψ for a discounted deliverable (dead, §2 here).

---

## 8. FILES

**New this session**, all read-only, each with its own CSV + log in `outputs/`:
`python/diag_gis_npv_tau_sensitivity.py`, `python/scope_gis_onset_rescan.py`,
`python/diag_gis_obs_scorecard.py`.
**Modified:** `python/diag_gis_greve_year3000.py` — the §4 print block's "CLIMBER-X is the
only threshold source" sentence, flagged in the prior handoff §3 item 1, is **corrected**.
**Unchanged:** nothing in `julia/`, no gate changed, no cell moved, no chain started, and
`scope_gis_reservoir_offline.py` + its CSV untouched so **86/216 still reproduces**. The
D1–D5 change set (`spec_2026-08-14_next_calibration.md`) is still **NOT STARTED**.

Commits `6351f90` → `01e89bb`. Memories written: `npv_retires_tau`,
`onset_premise_spent`, `gis_obs_accel_deficit`, `gis_weighted_verdict_cell`; `MEMORY.md`
and `INDEX_slr.md` both updated.

---

## 9. NON-OBVIOUS STATE

* **`scope_gis_onset_rescan.py` derives its onset floor** via `onset_floor()` and builds
  `ONSET_SCAN_K` from it at runtime. There is no `ONSET_MIN_K`. If you add a driver to the
  scoring set the floor moves — that is the point.
* **It imports the extended-axis machinery from `diag_gis_greve_year3000`** (`ext_driver`,
  `gcm_gmst_ext`, `gate`, `YEARS_EXT`) and `reservoir_unit` from
  `scope_gis_reservoir_offline`, so neither object can drift. `build_base()` is gated
  against `diag_gis_greve_year3000_cmp.csv` at **0.0000 %** — keep that gate.
* **`diag_gis_greve_year3000` does `os.chdir(REPO)` at import**, so anything importing it
  inherits that cwd.
* **The pre-2015 hindcast is IDENTICAL across all 8 drivers** (max spread 0.0e+00 cm),
  because `ext_driver` splices the observed south-Greenland T through the obs record.
  `diag_gis_obs_scorecard.py` verifies this rather than assuming it — without it, "our
  hindcast" would not be well defined.
* **`diag_gis_npv_tau_sensitivity.py` reaches OUT OF THE REPO** for the pulse IRF:
  `../FaIRtoFrEDI/fair_outputs/fair_*_gmst_v145_ssp245_pulse001_2030.csv`. It degrades
  gracefully (prints SKIPPED) if absent. The pulse MAGNITUDE is normalised away — only the
  near-step SHAPE is used.
* **ISMIP6 TIME-AXIS TRAP still applies** (prior handoff §8): index **positionally**, gated
  on `n == 86` and `sle[0] == 0`. `diag_gis_obs_scorecard.py` re-reads the files itself to
  get annual series — `read_ismip6()` returns only `cm_2100`.
* Extracted data on disk, **gitignored**, re-fetchable from the DOIs in each
  `PROVENANCE.txt`: `data/gis_post2100/{climberx_10kyr,greve_chambers_2022,ismip6_scalars}/`.

---

## 10. TRAPS ADDED THIS SESSION

* **A constraint tuned on ONE driver is not a constraint on a scoring set containing
  others.** Re-measure every tuned threshold when the scoring set gains a member (§3.2).
* **Never carry an inertness floor across a change in the driver set** (§3.1).
* **Gate EVERY target on observations, including the one in longest use.** "We already use
  it" is not evidence it passes (§4).
* **When a test built to support a hypothesis refutes it, report the refutation as
  prominently** as a confirmation would have been (§4). I got the *direction* wrong in prose
  once here — the numbers were on screen and said the opposite — which is exactly the
  directional-claim failure mode `~/.claude/CLAUDE.md` warns about.
* **When an aggregate score TIES, the tie is being decided by the weighting, not the data.**
  Get the weighting decided explicitly before reading a winner off the table, and report the
  winner under several weight sets (§5).
* **Price a knob against the discounted deliverable BEFORE identifying it**, and report the
  RANKING of knobs rather than one knob's sensitivity — a single-knob number cannot produce
  a decision (§2).
* **For a threshold object, compute the MARGINAL as well as the level.** They need not
  agree: here the onset dominates the level and ψ dominates the per-tonne (§2).
