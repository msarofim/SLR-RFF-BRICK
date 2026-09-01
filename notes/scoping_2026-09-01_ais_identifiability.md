# Scoping — the AIS refit wander, what causes it, and five ways to deal with it

**Written 2026-09-01** after the L23 refit moved Antarctica by +66 cm at ssp245/2300 while the
glacier module — the only thing changed, and a change that is bit-identical on a monotonically
warming path — moved 0.05 cm. Measurements from `julia/scope_ais_refit_wander.jl` →
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

## 2. THE ONE THING NOT RESOLVED

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

## 4. RECOMMENDATION

**Do §2's second refit first** — it is the only thing here that changes what the other options
mean. If amplification lands at the prior centre again, then L23 is the better-sampled vintage,
the glacier law is exonerated, and **A + C** is the sensible pair: constrain the parameter from an
observation, and disclose the residual wander. If it lands low again, the glacier law is
implicated and the diagnosis in §1 has to be redone against that.

⚠ **And do not promote L23 until this is settled.** Promotion would move headline ssp245 SLR@2300
by +69 cm on a difference that is currently attributable to a prior-bound parameter rather than to
any modelling decision.
