# Note — the matched-dT overshoot pair, and what it says about Ladrillo vs the other models

**2026-09-02.** Answering Marcus: *"do the matched dT scenario pair so I better understand the
difference between Ladrillo and the other models with the 3.4-OS scenario."*
Builder `scripts/build_fair_cube_matched_dt.py` (FaIRtoFrEDI, `claude/calib160-migration` worktree);
analysis `python/diag_matched_dt_penalty.py` (reproduces with no args).

## 1. THE HEADLINE — THREE FINDINGS, AND THE THIRD IS THE ONE THAT MATTERS

**(a) The native pair really was the problem.** Total penalty at 2300 (paired median):

| | native pair | matched pair |
|---|---|---|
| dT (overshoot − reference) @2150 / @2300 | **−0.102 / −0.133 K** | **+0.042 / +0.020 K** |
| **Ladrillo L24** | −1.23 ±0.048 cm | **+2.21 ±0.029 cm** |
| **BRICK 2.0** | −0.52 ±0.085 cm | **+2.57 ±0.184 cm** |

The dT inversion was worth **~3.4 cm** to Ladrillo and **~3.1 cm** to BRICK 2.0 at 2300. Both
penalties change SIGN. And the matched pair's **p05 is +1.23 / +0.87 cm** — strictly positive,
where natively it was −24 / −29 — so essentially every draw now shows a real penalty.

**(b) ⭐ LADRILLO IS NOT AN OUTLIER.** On an identical climate, identical splice, identical
reference and identical pairing, Ladrillo and BRICK 2.0 agree closely on the matched pair:
**2.21 vs 2.57 cm @2300**, **3.32 vs 3.35 @2150**, **4.05 vs 3.63 @2100**. BRICK 2.0 is the right
comparator precisely because it is INDEPENDENT where MAGICC is not — `ladrillo_glacier_is_nauels`
records that Ladrillo's glacier transient IS MAGICC's law. Whatever separates us from SLEIP, it is
**not something specific to Ladrillo's modules.**

**(c) ⭐⭐ AND THE GAP TO SLEIP MAY NOT BE A GAP AT ALL — IT IS A STATISTIC.** The penalty
distribution is heavily RIGHT-SKEWED (skew ≈ +3), so the median hides the tail:

| total @2300 | median | mean | p05 | p95 | skew |
|---|---|---|---|---|---|
| Ladrillo, matched | 2.21 | **8.94** | 1.23 | 43.31 | +3.29 |
| BRICK 2.0, matched | 2.57 | **11.54** | 0.87 | 51.32 | +2.80 |

**SLEIP reports 0.1-0.3 m.** Against our MEDIAN that is a factor of 4-14. Against our **MEAN
(8.9 / 11.5 cm) it is a near-match**, and their range sits between our mean and our p95.
⚠ **WHICH STATISTIC THEY REPORT IS THE OPEN QUESTION AND IS NOW THE HIGHEST-VALUE THING TO CHECK.**
This is `spread_blind_to_its_own_tail` again: I nearly reported a factor-of-10 model disagreement
that may be a mean-vs-median artifact.

## 2. ANTARCTICA COMES BACK — the artifact was hiding a real signal

AIS penalty at 2300 goes **+0.003 → +0.630 cm** (Ladrillo) and **+0.174 → +0.793 cm** (BRICK 2.0).

⇒ **Our Antarctica DOES carry overshoot hysteresis.** It read as zero only because the native
reference arm was warmer after 2127 and caught up. This does not reinstate "the DAIS relaxes back"
— [[ais_never_regrows]] stands, the AIS still never regrows on any pathway — but it does retire the
conclusion that the 2300 AIS row carries no hysteresis information. On a matched pair it carries
the LARGEST non-TE share of the penalty in both models.

Matched-pair components at 2300 (cm): Ladrillo glaciers 0.42 / gis 0.28 / **ais 0.63** / te 0.73;
BRICK 2.0 glaciers 0.50 / gis 0.32 / **ais 0.79** / te 0.67.

## 3. HOW THE PAIR WAS BUILT — AND WHY IN FORCING SPACE

    ERF_matched(t, config) = ERF_126 + max(ERF_534 − ERF_126, 0)

**Not in temperature space.** Clipping GMST would leave OHC inconsistent, and OHC drives thermal
expansion — the component carrying the largest negative penalty (−1.089 cm). Clipping OHC too would
have destroyed REAL ocean-heat hysteresis: our ΔOHC stays POSITIVE until **2171**, 44 years past the
temperature crossing. Intervening on forcing lets FaIR produce a consistent GMST **and** OHC with
**no fitted parameter**.

**Gates.**
* **[GATE-R]** the copied model setup reproduces the COMMITTED nomarker cubes at **5.000e-07** —
  exactly the cubes' 6-dp rounding half-ulp. This is what verified the marker-free recipe rather
  than assuming it.
* **[GATE-Z]** a ZERO delta reproduces the base arm at **0.000e+00**: the injection is a no-op at zero.
* **[GATE-F]** the injected channel carries the delta at **1.110e-16**.

**⭐ TWO GATES FAILED FIRST, AND THE FAILURE WAS THE PHYSICS.** I asserted the realised total forcing
would equal `ERF_126 + delta`. It does not — by **5.2e-2 W/m2, 5.0 % of the delta**. Diagnosed per
species rather than loosened: the residual sits in **CO2 (6.5e-2), Ozone (2.5e-2), N2O (1.1e-4)** —
FaIR's temperature-feedback channels. A warmer overshoot weakens the carbon sinks, so CO2 stays
higher. **Part of the forcing is ENDOGENOUS**, so no pure forcing addition can produce an exactly
matched dT — and the small residual warming it leaves (+0.020 K at 2300) is itself correct overshoot
physics: an overshoot leaves extra airborne CO2 behind. The exact gate moved onto the MECHANISM
(the injected channel), and the feedback is REPORTED rather than tolerated away.

## 4. ⚠ CAVEATS THAT BOUND EVERY NUMBER ABOVE

* **`ssp534overMATCH` IS IDEALISED AND IS NOT SSP5-3.4-OS.** It carries ssp126's forcing plus the
  non-negative part of the 3.4-OS forcing excess. It answers "what does an overshoot that RETURNS
  cost" — SLEIP's question — but it is not their scenario. Never quote it as SSP5-3.4-OS.
* **⭐ OUR OVERSHOOT IS SHALLOW.** Peak excess over the reference is **+0.311 K (at 2060)**; our
  ssp534over peaks 2.195 K and our ssp126 peaks 1.929 K. My RECOLLECTION is that the literature's
  SSP5-3.4-OS vs SSP1-2.6 peak excess is more like 0.5-0.6 K — **that is recollection, not a
  citation, and it is the second thing to check.** If our overshoot is half as deep as theirs, a
  large part of the residual gap is scenario depth, not model physics.
* **Marker-free ⇒ the posterior is used OFF-DESIGN** (2-6 % of the ensemble's own p5-p95 over the
  constraining period). State it with any absolute number.
* **PRIOR PROPAGATION, not a refit**, for both models.
* BRICK 2.0 and Ladrillo have different posteriors and draw counts (1000 vs 2000), so the per-draw
  pairing is valid WITHIN a model; the cross-model comparison is on the penalty statistic.
* **The two penalty statistics separate much more for BRICK 2.0** (matched: paired median +2.58 vs
  difference-of-medians +5.66) than for Ladrillo (+2.21 vs +3.43). Quote which one you mean.

## 5. WHAT TO DO NEXT, IN ORDER

1. ⭐ **Read SLEIP's 0.1-0.3 m off their own paper and find out WHICH STATISTIC it is** (median
   across datasets? mean? a p-box edge?). This single fact decides whether we have a model
   disagreement at all. Everything else is secondary to it.
2. ⭐ **Check the real SSP5-3.4-OS vs SSP1-2.6 peak temperature excess** against our +0.311 K.
3. Only then, if a real gap survives both: the AIS structural question (MICI is outside our
   representable set) becomes the candidate — and now on evidence, since AIS carries the largest
   non-TE share of the matched penalty in BOTH models.

## PROVENANCE

FaIR 2.2.4 (calib 1.6.0) + CMIP7, marker-free, 841 configs → Ladrillo L24 (shipped posterior, no
refit, tapped, 2000 draws) and BRICK 2.0 (`oldbrick`, 1000 draws); `joint` arm, `spliced` forcing,
cm, end year 2300. Cubes `fair_cube_{gmst,ohc}_ssp534overMATCH_raw.csv`. Six FaIR runs + four SLR
arms, all local, ~9 min total.

---

# ADDENDUM — FACTS on the matched pair (2026-09-02, Marcus's request)

**⚠ HORIZON FIRST: FACTS is configured to `pyear_end` 2150 and does NOT reach 2300.** It cannot
address SLEIP's 2300 headline. Everything below is 2100/2150, read against Ladrillo/BRICK **at
those years**. Run: facts repo `slr-comparison-arm` `8eccc5e3`;
`python3 diag_matched_pair_facts_penalty.py`.

## Ladrillo is MID-PACK among four process-based methods

Paired median penalty at 2150, matched pair, cm — sorted:

| | median | mean | p95 |
|---|---|---|---|
| wf4 Bamber SEJ | 2.40 | 6.80 | 38.4 |
| wf1f IPCC AR5 | 3.21 | 3.39 | **5.2** |
| **Ladrillo L24** | **3.32** | 9.06 | 39.3 |
| **BRICK 2.0** | **3.35** | 11.34 | 46.4 |
| wf3f DeConto/Kopp | 4.07 | **27.37** | **230.6** |
| wf2f LARMIP-2 | 5.48 | 6.01 | 10.8 |

FACTS is the comparator independent of the BRICK line on **both** glaciers and ice sheets, so this
turns the Ladrillo/BRICK agreement from possible common-mode into corroboration.

## ⭐ The medians agree and the tails do not — and that is the finding

Medians span **2.3×** (2.40-5.48). p95 spans **44×** (5.2-230.6). Ladrillo's tail (39.3) sits close
to Bamber SEJ (38.4) and BRICK (46.4), far wider than IPCC-AR5 (5.2), and **~6× narrower than
DeConto/Kopp (230.6)** — the one workflow that can express marine ice cliff instability.

⇒ The MICI concern is **real and now quantified**, and it lives **entirely in the tail**, not in the
central estimate. ⇒ An overshoot penalty compared on medians alone will show agreement that the
tails do not support — and vice versa.

## Method notes

* **The pairing is EXACT.** FACTS is deterministic on the non-emu workflows (`default_rng(1234)`;
  two identical runs bit-identical) and both arms draw the SAME 200 configs in the same order, so
  sample i shares its climate config AND its module RNG draws: structural ice-sheet noise cancels
  exactly in the difference, not approximately.
* **Both arms `lws_ssp=ssp1`, deliberately.** `landwaterstorage` selects a POPULATION pathway, not
  climate; giving the overshoot arm ssp5 would put a reservoir/groundwater difference INTO the
  penalty. Held fixed, LWS cancels — as it does in Ladrillo and BRICK (LWS penalty 0.000 cm).
* **Identical workflow set on both arms** (wf1f/wf2f/wf3f/wf4; no emulandice, which is per-SSP
  trained and 2100-capped), so module differences are module differences, not config differences.
* ⚠ FACTS is rel. baseyear 2005 where the others are rel. 1995-2014 — the standing approximation.
* ⛔ **EnTK forbids underscores in an experiment key.** `ssp126_nomarker` failed one second in with
  a message about `pipeline.0000`; `ssp534overMATCH` ran fine. Our cube convention is underscored by
  construction, so every marker-free scenario hits it. The key is now decoupled from the cube
  filename and a guard refuses a bad key at BUILD time.

## ⭐ A framing correction (Marcus, 2026-09-02)

My previous answer called the Ladrillo/BRICK agreement "common-mode, not independent confirmation".
**That was too strong, and Marcus is right.** The two share a lineage but differ substantially —
different glacier models (nu3 Mengel+Nauels vs Wigley-Raper), different Greenland, and independent
posteriors. Likewise Ladrillo and MAGICC share the glacier **transient equation** (Nauels 2017
Eq. 3), but **Ladrillo's 3-basin separation (R19/SLOWP/FAST) is its own** and MAGICC has no
counterpart. The right phrasing is "shares the transient law with MAGICC" and "shares a lineage with
BRICK" — not "is not independent". FACTS then places Ladrillo mid-pack among four genuinely
independent methods regardless.
