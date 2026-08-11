# Red team: BRICK-F\* before the joint recalibration

2026-08-11. Adversarial review of every change in BRICK-F\* — glaciers,
Antarctic, extended datasets — plus the Greenland A+B module now built but not
yet calibrated. Written to be attacked from, not to reassure.

Sources: `notes/memo_2026-08-10_brickf_sharing.md`, the extC posterior and its
diagnostics, `outputs/brickf_model_comparison{,_spread}.csv`,
`outputs/recalib_targets_ext.csv`, the component sources in `julia/`.
Everything asserted here is either computed in this note or referenced to a
file; where I am recalling rather than checking, I say so.

---

## 0. The one finding that should change what happens next

**The component targets and the total target disagree in exactly the window the
Greenland fix operates on, and they disagree in the direction that will fight
it.**

Computed here from `outputs/recalib_targets_ext.csv`, 1900–2023 overlap, summing
the five component targets (Frederikse-derived) against the independent total
target (Dangendorf 2024 spliced to NOAA STAR):

| window | Σ components | Dangendorf total | residual |
|---|---|---|---|
| 1900–1930 | −12.455 | −12.202 | **−0.253** cm |
| 1950–1980 | −3.878 | −4.616 | **+0.738** cm |
| 1993–2018 | +1.777 | +1.723 | +0.054 cm |

Residual over the whole overlap: mean +0.195, sd 0.477, range [−0.592, +1.540]
cm, with a +0.23 cm/century trend.

So in mid-century the component budget already sums **0.74 cm above** the
independent total. The Greenland component target, over that same era, sits
**0.5–0.7 cm above** the model (§7 of the memo, the 1942–1982 miss). The
likelihood is therefore being pulled two ways there: the Greenland series says
*melt more*, the total series says *melt less*, and stock BRICK-F\* has been
resolving that conflict by under-melting Greenland.

**Prediction for step 5, stated before it is run:** adding ~0.7 cm of
mid-century Greenland melt via A+B will degrade the *total* fit by close to the
same amount unless the calibrator takes that melt out of another component.
Glaciers and thermal expansion are the only candidates with mid-century
freedom. Three outcomes are possible and they are distinguishable:

1. Greenland improves, total degrades → the conflict is real and one of the two
   target series is wrong in mid-century. That is a data problem, not a model
   problem, and it should be resolved on the data side before the posterior is
   accepted.
2. Greenland improves, glaciers/TE absorb the difference → check whether the
   glacier module leaves its GlacierMIP3 rungs or its GlaMBIE modern rate. If
   it does, the Greenland fix has been paid for by breaking the glacier fit.
3. Greenland's improvement is suppressed and the posterior looks much like extC
   → the joint calibration is what limits Greenland, not the module, and the
   whole pass-1 exercise buys less than the offline cell suggests.

**Outcome 3 is not hypothetical.** The offline cell already showed that
refitting *stock* SIMPLE on Greenland alone, with no structural change, takes
the 2100 scenario spread from 2.29 to 7.25 cm — i.e. most of the spread deficit
is a joint-calibration outcome. The same competition that produced 2.29 cm will
still be there after the surgery. Diagnose which of the three happened before
reporting anything.

---

## 1. Glaciers (GSIC)

The most thoroughly worked module, and the one I would attack least on
substance. The attacks that remain are about degrees of freedom.

**1.1 ν is fixed, not sampled.** The response exponent is pinned per reservoir
at the value reproducing that region's volume response time at both +1.5 and
+3.0 K (`nu_anch_obsfit` in `outputs/extc_block_constants.csv`; all three land
at 1.55–1.62). The memo is explicit that this is deliberate. The consequence is
that **transient-shape uncertainty is not propagated** — the glacier band is a
parameter band conditional on one transient shape. A reviewer will ask why the
one structural quantity that governs how fast the commitment is realised is the
one held fixed. The defensible answer is that (κ, ν) are jointly degenerate and
ν is anchored to an external quantity; it should be said in those words, and
the sensitivity to ν should be reported at least once.

**1.2 Three model-side set-asides is a lot.** `gic_u_unch` (26.5 mm posterior),
`gic_delta` (0.21 mm/yr), `gic_u_pre` (6.5 mm) and `gic_s_r5` (2.5 mm) all
adjust the model side of a comparison rather than the data. Each is individually
motivated and each cites a source. Collectively they are ~35 mm of adjustable
material against a target whose whole 20th-century signal is ~90 mm. The
strongest defence is that they are *sampled with priors and reported*, not
tuned; the strongest attack is that a structural error in the glacier module
would be absorbed by them invisibly. **Test that would settle it:** refit with
all four fixed at their prior centres and see whether the glacier series
residual acquires structure. If it does not, they are doing real work; if it
does, they were absorbing it.

**1.3 The +1.2 K aggregate rung is outside the GlacierMIP3 likely range.**
56.3% [41.1, 69.9] against 37.4% [11.8, 54.0]. The memo diagnoses this as an
aggregation effect and shows it is not a denominator artifact. Accepted, but it
means **the module commits more glacier ice at low warming than GlacierMIP3
does**, which is the regime SSP1-2.6 lives in. Worth a line in any low-scenario
result.

**1.4 Reservoir membership was chosen by an offline shootout.** Which regions
go in SLOWP versus FAST came from `python/d1b_slow_split.py` and the D1 series.
That is a researcher-degrees-of-freedom exposure: the split was selected partly
on fit. The mitigating fact is that `notes/note_2026-08-08_d1b_slow_split_verdict.md`
reports the century integral is *topology-invariant*, i.e. the answer did not
depend much on the split. Cite that when the question comes.

**1.5 A reproducibility landmine that is documented but still live.**
`python/brickf_data.py` preserves an RNG **call-order dependence** in
`four_rung_fit()` — the fitted (b, T_off) depend on how many fits ran before
them, and the module deliberately reproduces the development call sequence
including two discarded fits. This is honest and it is tested
(`python/test_brickf_data.py` byte-compares), but it means the calibrator's
inputs are reproducible only by re-running that exact sequence. Fix it at the
next recalibration, as the file's own header says.

---

## 2. Greenland (A+B, built but not calibrated)

**2.1 β_f is unidentified, and that is an argument against having it.** The
separability profile (`outputs/gis_offline_cell_ridge.csv`) shows the fast rate
spanning 100% of its local range within Δ<2.3 at corr −0.03. The physical
reading is benign — once the fast channel is fast relative to a century its
speed stops mattering. But a reviewer is entitled to ask why the model carries a
parameter the data cannot see. **Cheapest defensible fix:** fix β_f at a
literature SMB response time and sample only f. That removes a free parameter
and loses nothing measurable.

**2.2 `g` is a new, essentially unconstrained parameter.** The fraction of the
1850 commitment already realised at 1850 fits at 0.711 with no observational
anchor before 1900. It sets the initial disequilibrium and therefore the whole
early-century melt rate. Stock SIMPLE has g = 0 by construction. Introducing it
as free is a real expansion of the model's freedom, made in order to let the
ladder cells start sensibly — and **the ladder cells were then rejected**. It
should probably be fixed at 0 for A+B, matching stock, unless it earns its place
in a likelihood-ratio sense. This is a loose end I introduced and did not close.

**2.3 The channel split rests on one dataset, 47 years long.** f is pinned by
the Mouginot 2019 SMB/discharge partition (1972–2018, 73.5%/26.5% verified from
the file). A+B′ — the alternative fast-channel form — fits the *sea-level*
history slightly better (RMSE 0.068 vs 0.099 cm) and gets the partition badly
wrong (0.36). So the entire structural choice between two channel forms is made
by one 47-year record. Mankoff 2021 was excluded as a partition (its pre-1986
discharge is a lagged fit to runoff), correctly, but that leaves no independent
second opinion. **State this as the load-bearing assumption it is.**

**2.4 The 2100 spread lands exactly on the band floor.** 6.30 cm against an
evaluation band of 6.3–7.3. That is not "inside the band" in any meaningful
sense; it is at the edge, and the joint calibration can only push it down (§0).

**2.5 The amplification is one scalar and the products disagree by 1.51×.**
Southern-Greenland 1901–2024 through-origin: HadCRUT5 1.97, Berkeley 1.51,
GISTEMP 2.28 (`outputs/gis_driver_constants.csv`). Sampling it under
N(1.92, 0.32) is the right treatment, but note that the *historical* driver is
HadCRUT5 alone — the product spread enters the projection splice and not the
hindcast. A reviewer who prefers Berkeley gets a systematically cooler Greenland
and a smaller response, and nothing in the calibration would flag it.

**2.6 Option C's failure is a finding, not just a null.** A proportional
relaxation cannot serve both a 6 cm historical loss against a 71 cm commitment
and a 742 cm post-threshold commitment; past the threshold, loss is limited by
ice throughput, not by the size of the disequilibrium. **This same criticism
applies to the accepted A+B module at high warming**, just less visibly: A+B's
linear L_eq reaches only a few hundred cm, so it never exposes the pathology,
but it is the same equation. Any 2300 or high-warming Greenland number from A+B
inherits that weakness. Say so wherever 2300 Greenland is reported.

---

## 3. Antarctic

This is where I would concentrate an attack, because it dominates the totals and
the tail.

**3.1 Eight nuisance marginals do not converge, and they are all in the block
that sets the tail.** The memo states this plainly: the fast-dynamics geometry
parameters are not identified by the historical window and sample their paleo
prior by design. The consequence is that **the AIS upper tail is prior-driven,
not data-driven**. At SSP2-4.5 2100 the median is 11.7 cm but the 17–83 range
reaches 41.0 cm (`outputs/brickf_model_comparison.csv`). That p83 is doing more
work in any risk-weighted application than the median is, and it comes from a
paleo prior, not from observations.

**3.2 Convergence is judged on the deliverable, which is the right choice and
also a partial answer.** R̂ = 1.000 at 2100 and 1.002 at 2150 on projected sea
level. That justifies using the projections. It does *not* justify quoting the
AIS parameter marginals, and it does not tell you the tail is right — a
prior-dominated quantity can be perfectly converged and still be an assumption.

**3.3 The tail interacts badly with pulse experiments.** From
`mimibrick-quirks` #11: ~5% of LHS-10k draws sit near the AIS tipping threshold
at baseline, and a 1 GtCO₂ pulse pushes them over, so the marginal-SLR *mean* is
dominated by tipped draws and the median is the reportable statistic. That is a
known, handled issue — but it is a property of this AIS parameterisation, and
the recalibration did not remove it. Any SC-GHG use inherits it.

**3.4 A 28 cm shift that needs an explanation on the record.** Memory
`project_brick_mengel_postpred` records BRICK-Mengel at SSP2-4.5 2100 = 77.7 cm;
BRICK-F\* gives 49.5 cm. That is the largest single quantitative movement in the
programme, and the memo does not attribute it. My expectation is that it is
mostly the Antarctic recalibration removing the early-century overshoot, but
**I have not tested that** and should not assert it. It needs a one-line
attribution (rebuild BRICK-Mengel's AIS block inside extC, or vice versa)
before anyone asks. Related: any deliverable built on the 77.7 cm vintage is
affected and should be checked against the quarantine rule.

---

## 4. The components nobody looked at

**4.1 Thermal expansion is stock, and its parameter may be non-physical.**
From `mimibrick-quirks` #8: the TE α posterior is ~3× below the physics value
because Wong's calibration ran against SNEASY OHC anchored to Gouretski 2007,
which over 1953–1996 runs ~2× Cheng IAPv4.2. TE was not revisited in BRICK-F\*.
The fit is fine (bias +0.24 cm) — a biased α against a biased OHC target can
still reproduce the series. The exposure is **extrapolation**: TE is 17.3 cm of
the 49.5 cm SSP2-4.5 2100 total and 25.9 cm at SSP5-8.5, and it is being driven
by modern-obs or FaIR OHC, not by the Gouretski-scaled OHC it was fitted
against. I would want this re-checked before any 2300 total is defended.

**4.2 Land-water storage is a fixed climate-independent rate.** Locked at
0.3 mm/yr (`LWS_MEAN` in `julia/brick_mengel.jl`), contributing a flat 2.6 cm at
2100 in every scenario. It is zero before ~2019 by calibration design. For
2100 that is defensible. For 2300 a constant groundwater-depletion rate three
centuries out is an assumption nobody has defended, and it is 100% of the
scenario-invariant part of the total.

**4.3 Two of five components will now be regional-driver-based.** After
Greenland, glaciers and Greenland both run on regional temperature; AIS runs on
a sampled GMST→T_ant amplification; TE runs on OHC. **The good news, and it was
a deliberate design choice worth stating: the external interface is still
GMST + OHC only** — every regional driver is constructed inside the model as
`amp × GMST + offset` with an anchor-preserving splice
(`brickf_driver` in `julia/brickf_projection.jl`). So the drop-in property
survives. The cost is that a growing share of the model's behaviour is
controlled by a handful of scalar amplifications, each fitted to a
product-dependent observational regression.

---

## 5. Is it still BRICK?

**Architecturally yes; component-wise, decreasingly.**

| component | origin | status in BRICK-F\* (post-Greenland) |
|---|---|---|
| Glaciers | Wigley–Raper–Bakker | **replaced** (3-reservoir Mengel/Nauels) |
| Greenland | SIMPLE (Bakker 2016) | **replaced** (regional driver + 2 channels) |
| Antarctic | DAIS (Shaffer 2014) | same structure, re-parameterised, 6 groups freed |
| Thermal expansion | Wong 2017 2-parameter | unchanged |
| Land-water storage | Wong 2017 | unchanged, locked |

What is unambiguously still BRICK: the **architecture** — lumped semi-empirical
components, additive to a global total, driven by temperature (plus OHC),
implemented in Mimi, calibrated by adaptive-Metropolis against a historical
budget. And DAIS, which is load-bearing: it sets the totals and the whole upper
tail.

What has actually changed most is not any component but the **calibration
philosophy**. Original BRICK fit a global mean sea-level total (Church & White),
with LWS removed from the target for that reason. BRICK-F\* fits a *component
budget* plus *process-model equilibrium ladders* (GlacierMIP3) plus *modern
per-region rates* (GlaMBIE) plus an *SMB anchor* (Rignot). That is a different
epistemic object: it is no longer "a simple model tuned to reproduce observed
GMSL", it is "a reduced-form emulator constrained by the same evidence base the
process models are assessed against". That shift is a bigger departure from
Wong et al. 2017 than any of the three component swaps, and it is the thing to
say first when someone asks whether it is still BRICK.

**Naming recommendation:** keep BRICK in the name — the architecture, the
calibration machinery, and DAIS are all inherited — but do not describe it as
"BRICK with an updated glacier module". Describe it as a BRICK-architecture
model with two replaced components and a re-derived calibration basis. The
honest one-liner is: *the skeleton and the Antarctic are BRICK; the glaciers,
Greenland and the evidence base are new.*

---

## 6. What BRICK-F\* is for, against FACTS and MAGICC-SLR

### The differentiators that survive scrutiny

**6.1 Forcing-agnostic, and that is the real one.** BRICK-F\* takes GMST and
OHC as external vectors (`set_forcing!`) and needs nothing else. It can be
driven by FaIR, by MAGICC output, by observations, by an RFF-SP ensemble, or by
a single perturbed trajectory. MAGICC-SLR is integrated *inside* MAGICC, so it
cannot be driven by FaIR or by any other temperature model — which for our own
work is disqualifying, because the whole FaIR→BRICK pipeline and every paired
pulse experiment depends on exactly that coupling. This is the clearest
capability BRICK-F\* has that MAGICC-SLR does not, and it is a structural
property, not a quality claim.

**6.2 Cheap enough for millions of paired runs.** ~1–2 ms per integration on
the fast path (`mimibrick-quirks` #14). That is what makes per-draw pulse
experiments, SC-GHG marginals, and Hawkins–Sutton decompositions feasible at
all. FACTS is a workflow system over module ensembles; it is not something you
call a million times in a marginal-damage loop.

**6.3 One joint posterior across components.** BRICK-F\*'s components are fitted
*together* against a historical budget, so their errors are correlated the way
the observations say they are. FACTS composes modules that were calibrated
independently; its workflows sample them jointly but do not *constrain* them
jointly against history. For a total-SLR uncertainty distribution that has to be
internally consistent, that is a real methodological difference in BRICK-F\*'s
favour.

**6.4 Independent of AR6 as a target.** MAGICC-SLR (Nauels 2025) is calibrated
to reproduce AR6 assessed ranges. BRICK-F\* is calibrated to observations and
process-model ladders. Agreement between them is therefore *informative*;
agreement between MAGICC-SLR and AR6 is not. Our SSP2-4.5 2100 total of 49.5
against MAGICC's 53.2 is a genuine independent corroboration in a way it would
not be if we had also fitted AR6.

**6.5 Runs to 2300 cheaply, with a scenario-dependent glacier equilibrium.**
Relevant to SC-GHG work, where the post-2100 integral carries real weight.

### Where the competition is straightforwardly better

**6.6 FACTS gives local sea level; BRICK-F\* does not.** Fingerprints, GIA,
vertical land motion, regional ocean dynamics. For coastal damage work that is
not a detail, it is the whole thing. Any comparison should concede this first,
because it is the main reason someone would choose FACTS.

**6.7 FACTS spans structural uncertainty deliberately; BRICK-F\* is one
structure.** FACTS carries several modules per component precisely so the
spread across structures is visible — the AIS spread from `ar5AIS` to
`deconto21` in `outputs/brickf_model_comparison.csv` is enormous and that is the
point. BRICK-F\* reports parameter uncertainty within one structure and
therefore *systematically understates* total uncertainty. Our bands are not
comparable to FACTS bands, and §8 of the memo already says so for the climate
half of it; it should say so for the structural half too.

**6.8 Neither BRICK-F\* projection band carries climate uncertainty at all.**
Projections use FaIR *mean* GMST per SSP. The memo states this. It bears
repeating in every figure caption, because a reader comparing band widths to
MAGICC or FACTS will be comparing different things.

### The honest positioning sentence

BRICK-F\* is the fast, forcing-agnostic, jointly-calibrated global emulator you
use when you need to run sea level a million times inside someone else's
temperature model — which is precisely what FACTS is too slow for and what
MAGICC-SLR is architecturally unable to do. It is not the tool for local sea
level, and it does not span structural uncertainty.

---

## 7. Ranked: what to do before accepting a recalibrated posterior

1. **Resolve the mid-century target conflict (§0).** It is the one issue that
   can make the Greenland work look like a failure for reasons that have nothing
   to do with the Greenland module. Diagnose which of the three outcomes
   occurred *before* interpreting the posterior.
2. **Decide `g` (§2.2).** Fix at 0 to match stock unless it earns its place.
   Free-and-unanchored is the weakest thing in the new module.
3. **Fix or justify β_f (§2.1).** Fixing it costs nothing measurable.
4. **Attribute the 28 cm BRICK-Mengel → BRICK-F\* shift (§3.4).** One
   experiment, and it will be asked about.
5. **Re-check thermal expansion against a modern OHC target (§4.1).** It is
   35% of the SSP2-4.5 2100 total and its parameter is suspected non-physical.
6. **Report a ν sensitivity once (§1.1)** and a set-asides-fixed refit (§1.2).
7. **State the structural-uncertainty caveat (§6.7) alongside the existing
   climate-uncertainty caveat** wherever bands are compared.

Items 1–3 are prerequisites for step 5. Items 4–7 are before external release.
