# Scoping — the AIS refit wander, what causes it, and five ways to deal with it

> ⛔⛔ **CORRECTION, SAME DAY (2026-09-01, later).** This document's premise — "the glacier
> module, the only thing changed" — is **FALSE**, and two of its 2x2 cells do not survive.
> The measurements stand; the attribution does not. Read this box before §3's table.
>
> 1. **The glacier law is INERT in the calibration likelihood.** Old vs new differ by
>    **≤7.3e-05** log-units on L23-region draws, against **1.86** for a 1 % wiggle of one
>    glacier parameter and **11.4** for 1 % of amp — a null **WITH power**, 4–5 orders of
>    headroom (`julia/scope_amp_likelihood_tilt.jl`). D1 drops the total series, so glaciers
>    and AIS have separate likelihood terms with no shared channel. There is no mechanism.
> 2. **L23 was NOT one variable.** It carries no `--adcov` and fell through to
>    `adapted_cov_L11tune3` where L21/L22 passed `adapted_cov_L14tune`; the AIS-block proposal
>    is **2.7–5.3× tighter** in L23 (`python/diag_proposal_seed_by_vintage.py`, read from the
>    runs' own `seed_diag_*.txt`).
> 3. **Two cells are inside their own error bars.** Recomputed over all 4M post-burn draws with
>    a batch-means se (`python/diag_amp_by_vintage.py`): L21 **0.9438 ± 0.0018**, L22
>    **0.9465 ± 0.0021**, L23 **1.0824 ± 0.0037**, L23b **1.0896 ± 0.0029** — every published
>    cell agrees within 1.6 se, so the table below is the same estimate on a noisier ~10k
>    thinned pool. But its **L21→L22 delta of −0.0021 recomputes to +0.0026 ± 0.0027** and
>    flips sign: read that cell as **NO DIFFERENCE**, not as a signed number. And the
>    **4.93 cm** reproducibility figure is BLIND — L23b shares L23's covariance and varied
>    only RNG, so it measured noise *inside* the defect.
>
> ⇒ **RESOLVED, later the same day, by L25.** L25 (L23's config + L21/L22's covariance) reads
> **1.0791 ± 0.0030** — 0.7 se from L23, 39 se from L21 — so the covariance is exonerated too.
> Both standing hypotheses dead, the cause is a **THIRD DROPPED FLAG**: `run_mcmc_L21.sh` and
> `run_mcmc_L22.sh` pass `--amp-mu=0.95`, there is no `run_mcmc_L23.sh`, and L23 onward took the
> default **1.09**. The banners: L21/L22 `N(0.950, 0.100) on [0.650, 1.250]`, L25
> `N(1.090, 0.100) on [0.790, 1.390]`. **Prior-mean shift +0.1400 vs posterior span +0.1386,
> ratio 0.990**, on a parameter this very document measured as prior-dominated. At 386 cm/unit
> that is ~53 cm of the ~66-69 cm AIS move.
>
> ⚠ **AND IT DISSOLVES §2's PREMISE.** "Under the ratchet the likelihood pulled amp 1.45 σ below
> its prior" was an artifact of scoring L21 against the WRONG prior. Against the prior each run
> actually used, z_own is **−0.06 / −0.04 / −0.08 / −0.00 / −0.11** for L21/L22/L23/L23b/L25 —
> every vintage sits on its own prior mean, as a prior-dominated parameter must. There was no
> displaced centre to explain. `python/diag_amp_by_vintage.py`.

**Written 2026-09-01** after the L23 refit moved Antarctica by +66 cm at ssp245/2300 while the
glacier module — believed at the time to be the only thing changed, and a change that is
bit-identical on a monotonically warming path — moved 0.05 cm. Measurements from `julia/scope_ais_refit_wander.jl` →
`outputs/scope_ais_refit_wander_{L21,L23}.csv`. **Scoping only; nothing changed in the model.**

---

## 1. WHAT IS MEASURED

**The move is entirely Antarctica.** L23 − L21 medians at ssp245/2300, cm:
glaciers **0.05**, gis −0.09, te −0.05, lws 0.00, **ais +69.3**, total +69.1.
On the 10k-draw deliverable; +66.0 on the 300-draw/chain re-measurement below. So the
between-vintage difference carries no information about the change that was made.

**AIS is the only component with meaningful between-chain spread.** Four chains WITHIN one
refit, ssp245, range of the chain medians (cm):

| component | L21 @2300 | L23 @2300 |
|---|---|---|
| glaciers | 0.28 | 0.19 |
| gis | 1.36 | 0.51 |
| te | 0.33 | 0.16 |
| **ais** | **10.48** | **34.35** |
| total | 9.48 | 33.42 |

R-hat on AIS@2300 is **1.004** at L23 while the chain medians span **34 cm** — the
`rhat_denominator_forgives` shape exactly: a wide band divides the displacement away. **Quote the
range in cm, not R-hat.**

**One parameter dominates.** Standardised shift of each AIS parameter, L23 vs L21, in units of
L21's own posterior sd, paired with the measured sensitivity of AIS@2300:

| parameter | shift (sd) | slope cm/unit @2300 | shift x slope |
|---|---|---|---|
| **`ais_gmst_amp`** | **+1.45** | **386.1** | **54.2 cm** |
| `ais_runoff_Ton` | +0.97 | 175.1 | 14.0 |
| `ais_slope` | −0.60 | −524076 | 8.1 |
| `ais_iceflow0` | +0.49 | 55.7 | 5.4 |

(The univariate products double-count correlated variance, so they sum above the observed 66 cm;
the ranking is the point.) **`ais_gmst_amp` alone accounts for ~82 % of the move.**

**It is not mode-hopping.** `ais_runoff_Ton` is multimodal ([[ais_ton_multimodal]]), but **both**
vintages sit ~100 % in the MID band on all four chains. That hypothesis was tested and refuted.
`ais_runoff_Ton` explains only 14 of the 66 cm.

**⚠ THE SENSITIVITY GROWS WITH HORIZON AND THE CONSTRAINT DOES NOT.** `ais_gmst_amp` slope on
AIS: **78 cm/unit @2100 → 178 @2150 → 386 @2300.** Meanwhile the AIS contribution inside the
calibration window is sub-centimetre. A parameter with almost no leverage on the data and
monotonically growing leverage on the answer is, by construction, not identifiable from the fit.

**And the posterior confirms it.** Prior is **N(1.09, 0.10)** (`calibrate_mcmc_ext.jl:1172`).
L23 posterior: median **1.086**, sd **0.097** — indistinguishable from the prior. **The data add
essentially nothing.** L21 posterior: same width, median **0.946**, i.e. **−1.44 sigma** off the
prior centre.

---

## 2. RESOLVED 2026-09-01 — IT IS THE GLACIER LAW, NOT SAMPLER WANDER

**⚠ THIS SECTION REPLACES THE ORIGINAL §2, WHICH POSED THIS AS AN OPEN QUESTION AND LEANED
TOWARD THE WRONG ANSWER.** The original text guessed that L21 had simply not equilibrated and
that L23 was the better-sampled run. That guess was the flattering one, it was mine, and the
measurement refutes it.

A replicate refit (**L23b**: identical law, identical flags, identical START ROWS, seeds
3026-3029 so only the RNG stream differs) plus the already-on-disk **L22** completes a 2x2 that
separates the two changes which landed between L21's chains and L23's — the glacier law
(`a0155bf`) and the L22 steric AR(1) marginal cap (`abd308d`). ⚠ **I had missed the second one
entirely** when I first called this wander; L21 and L23 differed by TWO things, not one.

`ais_gmst_amp` pooled posterior median, prior N(1.09, 0.10). ⛔ **See the correction box at the
top: these are a ~10k thinned pool with se ≈ 0.002–0.004, the L21/L22 cell is inside its own bar
and flips sign on recompute, and the "new glacier law" column also changed proposal covariance:**

| | old glacier law | new glacier law |
|---|---|---|
| **pre** steric-cap | **L21 0.9455** (z −1.45) | — |
| **post** steric-cap | **L22 0.9434** (z −1.47) | **L23 1.0865** (z −0.04) · **L23b 1.0850** (z −0.05) |

* steric cap changed, law held → **Δ 0.0021**. Not the cause.
* law changed, cap held → **Δ 0.1431 = 1.43 prior sd**. The cause.
* nothing changed but the RNG → **Δ 0.0014**. Sampler noise is negligible.

At the SLR level the same separation: AIS@2300 pooled, L23 **201.85** vs L23b **196.92** —
**between-refit reproducibility 4.93 cm** — against the L21→L23 gap of **66.04 cm**, thirteen
times larger.

**⇒ THE GLACIER LAW IS NOT INERT ON ANTARCTICA.** It is worth ≤0.15 cm in the glacier component
and ~+66 cm in AIS at 2300, entirely through the CALIBRATION. Every earlier statement in this
session that the change is "provably inert on warming paths" was about the glacier OUTPUT at
FIXED parameters, and does not survive refitting.

**What it means, and what is still open.** Under the old law the likelihood pulled amplification
**1.45 sigma below its prior**; under the new law it does not, and the posterior sits on the
prior. So a glacier modelling convention was setting the Antarctic amplification. Which state is
right is NOT established here: either the ratchet was manufacturing a spurious constraint on AIS
(in which case removing it is correct and L21/L22's lower amplification was an artifact), or the
floor/regrowth introduces slack that lets an unconstrained parameter drift to its prior. **That
question is now the important one**, and it is a question about whether AIS amplification was
ever identified at all rather than about glaciers.

⚠ **A METHOD NOTE WORTH KEEPING.** Between-chain spread WITHIN one refit is a BAD proxy for
between-refit spread of the POOLED estimate: the within-L23 chain-median range at AIS@2300 is
34.35 cm, while two independent refits' pooled medians differ by 4.93 cm. Averaging over four
chains removes most of it. Do not size a reproducibility claim off the within-run range in
either direction.

## 2b. THE ORIGINAL OPEN QUESTION (superseded, kept for the record)

Why L21's amplification sat 1.44 sigma below the prior centre while L23's sits on it. Two
candidates, not separated:

* **(a) L21 was not equilibrated in that direction.** Its AIS R-hats are much worse than L23's
  (`ais_iceflow0` **2.323** vs 1.455; `ais_slope` 1.566 vs 1.182; `antarctic_alpha` 1.479 vs
  1.215). On this reading L23 is the better-sampled run and L21 was stuck low.
* **(b) The glacier law changed the joint likelihood's pull on amplification.** Glaciers and AIS
  both enter total SLR and the D2 discrepancy term on gsic+steric, so a glacier change is not
  formally inert on the AIS direction even where the glacier OUTPUT is unchanged.

⚠ **Do not assume (a).** It is the flattering reading and it is the one I reached first.
**The test that separates them:** refit ONCE more at the L23 law with different seeds
(3026-3029). If amplification again lands at the prior centre, (a) is supported and L21 was the
outlier. If it lands low again, the glacier law is implicated and (b) is live. ~3 h, and it is
the only measurement here that needs new chains.

---

## 3. FIVE WAYS TO DEAL WITH IT

Ordered by what they cost, not by preference. **None is chosen; this is a menu.**

### A. Constrain `ais_gmst_amp` from observations — CHEAPEST, BIGGEST EFFECT
The parameter is Antarctic polar amplification, a **measurable physical quantity**, currently held
only by a prior whose sd (0.10) was set from an inter-model spread that was then deliberately not
adopted (`calibrate_mcmc_ext.jl:1166-1171` — the corrected data gave 0.180 and the standing
constraint put between-model spread out of scope). An **observational** constraint — reanalysis or
station Antarctic surface-temperature trend regressed on GMST over the satellite era — would be an
observation rather than a model, which is the order `threshold_from_obs_or_law` asks for.
⚠ It would REPLACE a model-derived prior with an observed one, which is a methodological change
and Marcus's call, not a tuning knob. Cost: the regression is hours, not days; no refit needed to
scope the width it would imply.
**What it buys:** halving the amp sd roughly halves the 54 cm term.

### B. Add a likelihood term the parameter can actually see
Amplification has sub-cm leverage on the current calibration window, so no amount of sampling will
identify it. An **IMBIE-style AIS mass-balance rate over 1993-2020**, or an Antarctic surface
temperature target, would give it something to be constrained BY. ⚠ This is a new target and
therefore a new calibration, not a re-run — and `audit_every_target` applies: adding one target
changes what every other one is doing.
**What it buys:** the only option that makes the parameter identifiable rather than prior-bound.

### C. Report between-refit wander as a stated uncertainty component
Cheapest honest option: keep the model, measure the wander (needs §2's second refit), and quote
AIS with a "refit reproducibility" term beside the posterior band. ⚠ This DISCLOSES the problem
rather than fixing it, and the term is not small — 34 cm between-chain at L23 is a lower bound.
**What it buys:** stops a refit difference being read as a physics result. It does not narrow
anything.

### D. Reparameterise the AIS block onto its adapted covariance
Nine AIS parameters fail R-hat and they are correlated; the sampler is exploring a ridge in the
native basis. Rotating onto the principal axes of the adapted covariance (already written every
run as `adapted_cov_L23_seed*.csv`) would let the sampler move along the ridge instead of across
it. ⚠ [[nameless_matrix_order]] — a permuted matrix is still valid, so rows must be NAMED on write
and the diagonal gated on read, or a parameter silently gets its neighbour's scale.
**What it buys:** better mixing at the same cost. It does NOT make an unidentified parameter
identified — a flat direction stays flat in any basis.

### E. Longer chains
ESS on the AIS parameters is 15-83 at 2M iterations. Reaching ESS ~400 needs roughly 10-25x more,
i.e. **30-75 hours**. ⚠ Listed for completeness and **not recommended**: §1 shows the parameter is
prior-dominated, and sampling a prior more precisely does not add information. This is the option
that looks like diligence and buys the least.

---

## 4. RECOMMENDATION — REVISED 2026-09-01

The second refit is DONE and it changed the question. This is no longer "is the AIS posterior
reproducible" (it is, to 4.93 cm) but "was Antarctic amplification ever identified, or was it
being set by a glacier convention".

**Option E (longer chains) is now firmly out** — the parameter is prior-dominated under the new
law and sampling it harder cannot help. **Option D (reparameterise)** is likewise beside the
point: the direction is not badly mixed, it is unconstrained.

**A and B are the live ones, and B is now the more important.** Under the new law the data say
nothing about amplification, so its prior IS the answer, and the prior's width was set from an
inter-model spread that was deliberately not adopted. Either give the parameter an observational
constraint (**A**) or give the likelihood a term that can see it (**B**). **C** — disclosing the
between-refit term — is cheap and should be done regardless, but the term is 4.93 cm, an order
smaller than the 66 cm the law change moves, so it is no longer the headline.

⚠ **AND THE PROMOTION QUESTION HAS CHANGED SHAPE.** L23 is not "an unreproducible draw"; it is a
reproducible fit under a law we believe is more physical, whose Antarctic answer differs from the
champion by 66 cm for a reason we can now name but cannot yet adjudicate. Promoting it means
adopting the position that the ratchet was manufacturing the old AIS constraint. That is a
defensible position and it is Marcus's to take, not mine to assume.

---

# ADDENDUM 2026-09-01 — OPTION B WAS ATTEMPTED AND IS REFUTED BY ITS OWN POWER

Marcus asked for **B**: give the likelihood a term that can see `ais_gmst_amp`. Measuring the
power of that term BEFORE building it (`no_power_null`) says it cannot work. Reporting the
negative rather than shipping a term that would look like a constraint and act as none.

## What A actually is

`antarctic_icesheet_magdep_component.jl:165` with the calibrator's `1/θ` mapping gives

    T_antarctic = A * GMST + TANT0 ,   TANT0 = -18.435 C, FIXED

so **A is the regression slope of Antarctic mean surface temperature on GMST** — a directly
observable quantity, which is why B looked promising. The problem is the lever arm.

## Why no instrumental record can see it

**A only ever multiplies the ANOMALY.** Its footprint is proportional to GMST, which is ~0.5 C
where the observations are and 3-8 C where the answer is. For the L22->L23 shift dA = 0.1431:

| epoch | GMST | dT_antarctic | d precipitation |
|---|---|---|---|
| 1979-2008 (the existing SMB term's window) | 0.58 | **0.083 C** | 0.52 % |
| 1992-2017 (IMBIE) | 0.79 | 0.113 C | 0.70 % |
| 2100 / 2300 | 2.70 / 3.18 | 0.387 / 0.455 C | 2.4 / 2.9 % |

A shift that moves AIS@2300 by **66 cm** perturbs Antarctic temperature by **0.083 C** over the
window where we have mass-balance data, and precipitation by half a percent — far under Rignot's
uncertainty. **The identifiability problem is structural, not a missing dataset.**

## And a temperature target is worse, not better

Slope standard error `sigma_A = sigma_eff / sqrt(Sxx)` on the model's own GMST regressor, with an
AR(1) inflation at rho = 0.3, against the **prior sd of 0.10**:

| window | sigma_obs 0.4 | 0.6 | 0.8 |
|---|---|---|---|
| 1979-2024 satellite | 0.271 | **0.407** | 0.542 |
| 1957-2024 (longest real record) | 0.200 | 0.300 | 0.400 |
| 1850-2024 (longer than any record exists) | **0.119** | 0.179 | 0.239 |

Antarctic annual continental-mean temperature has an interannual sd of ~0.4-0.8 C. **Every cell
is worse than the prior**, including one that assumes 175 years of data that do not exist.

## The other candidates, and why they are already closed

* **IMBIE dAIS(92-17)** was in this likelihood and was **deliberately REMOVED** (calibrator
  header item 4, Marcus 2026-06-13) because the extended AIS time series constrains the modern
  rate directly and keeping both double-weights it. Re-adding it would reverse a decision, and
  the table above shows it would buy 0.113 C of signal.
* **An SMB term already exists** (A5: model beta_total 1979-2008 vs area-scaled Rignot 2019). It
  is in the likelihood NOW, and A is still prior-dominated. The observable is present and does
  not identify the parameter.
* **Paleo (LGM ice cores)** would constrain **EQUILIBRIUM** amplification (~1.5 from a -6 C
  global, -9 C Antarctic contrast). The model needs the **TRANSIENT** coefficient, which A6
  deliberately took from CMIP6 PAI1 (Xie et al. 2022). Wrong quantity — do not substitute it.

## ⇒ WHAT I RECOMMEND INSTEAD

**F. Widen the prior to the inter-model spread that was actually measured — 0.180, not 0.10.**
The calibrator records (`:1166-1171`) that the corrected data DID give an inter-model sd of
0.180 and that 0.10 was kept deliberately, because between-model spread was out of scope for
that recalibration. That reasoning predates knowing that **A is prior-dominated and carries
386 cm/unit at 2300**. When a parameter's posterior IS its prior, the prior's width IS the
projection uncertainty, and 0.10 understates the AIS band by ~1.8x on the dominant term.
⚠ This REVERSES a standing constraint and is Marcus's call. It WIDENS the band; it does not
improve the fit.

**G. Report A as an explicit structural axis, not a fitted parameter.** Project AIS at A = the
prior's p05 / p50 / p95 and quote the spread as declared structural uncertainty. A
prior-dominated, high-leverage parameter laundered through a posterior looks like a result; run
as an axis it looks like what it is.

**C. still stands** — disclose that the glacier law moves AIS@2300 by 66 cm, against 4.93 cm of
between-refit reproducibility.

**Not recommended: building B anyway.** A term with sigma_A of 0.27-0.54 against a 0.10 prior
would leave the posterior unchanged and add the *appearance* of an observational constraint.
That is the failure `no_power_null` exists to prevent.
