# Substack post — handoff for Claude chat editing session

**Date:** 2026-05-19
**Author:** Marcus Sarofim (NYU Marron / Johns Hopkins EPCP)
**Topic:** Uncertainty in projected global mean surface temperature (GMST) and
global mean sea level (GMSL), built on a coupled FaIR + BRICK ensemble
forced by RFF-SP socio-economic / emissions scenarios.

This note is a self-contained briefing for a Claude chat session that
will help refine the substack post draft. It assumes no prior familiarity
with the project, methods, or jargon. Every term in the figures and tables
is defined below.

---

## 1. What the project does in plain English

This is an "uncertainty plumbing" exercise: I run thousands of plausible
futures through a chain of three reduced-complexity climate models, then
quantify how much of the projection spread comes from each source of
uncertainty (which emissions trajectory we end up on, how sensitive the
climate is to those emissions, how much of an ocean-and-ice-sheet response
that warming triggers, and irreducible chaos).

The end product is a probabilistic picture of:

1. **How warm the world gets** (GMST) by 2050, 2100, 2150.
2. **How much sea level rises** (GMSL) over the same horizons.
3. **What a single tonne of CO₂ emitted in 2030 contributes** to those
   outcomes (the "marginal climate response" — relevant for the social
   cost of CO₂).
4. **Where the projection uncertainty comes from** — emissions, climate
   sensitivity, ice-sheet response, or internal climate variability.

---

## 2. The model chain

```
RFF-SP emissions  →  FaIR v2.2.4 climate model  →  MimiBRICK sea-level model
   (398 scenarios)     (841 parameter configs)        (per-tuple posterior)
```

### 2.1 RFF-SP emissions scenarios
- **What it is:** 10,000 internally-consistent socio-economic + emissions
  trajectories from Resources for the Future's Social Cost of Carbon
  Initiative (Rennert et al. 2022 Nature). Probabilistic, no policy
  scenarios — meant to span the full plausible range of unmitigated futures
  given current trends.
- **What we use:** A 398-RFF subset for tractability. Each is treated as
  one Monte Carlo draw.
- **Variable name in code:** `rff_idx`.

### 2.2 FaIR v2.2.4 climate model + v1.4.1 calibration
- **Important version distinction:** the *model* is **FaIR v2.2.4** (the
  Python package `from fair import FAIR` — the carbon-cycle + energy-
  balance solver). The *calibration* is **FaIR-calibrate v1.4.1** —
  Chris Smith et al.'s 841-member posterior over FaIR's free parameters.
  Captions that just say "FaIR v1.4.1" are referring to the calibration,
  not the model version; the model is v2.2.4 throughout this work.
- **What it is:** A reduced-complexity ("simple") climate model that
  converts emissions of CO₂, CH₄, N₂O, aerosols, etc. into a GMST anomaly
  time series. It is the "energy balance + carbon cycle" engine.
- **841 parameter configs:** Each is a different draw from the
  FaIR-calibrate v1.4.1 posterior over FaIR's free parameters (climate
  sensitivity, ocean heat uptake rate, aerosol forcing, carbon-cycle
  feedbacks). The calibration was fit to historical observations + AR6
  assessed ranges by Smith et al.
- **Variable name in code:** `fair_cfg_idx`.

### 2.3 MimiBRICK sea-level model
- **What it is:** A reduced-complexity sea-level model that converts a
  GMST trajectory into GMSL. Has separate components for thermal
  expansion, glaciers, Greenland and Antarctic ice sheets.
- **Posterior draws (`post_idx`):** BRICK has its own free parameters
  (ice-sheet sensitivities, tipping thresholds for the Antarctic ice
  sheet, etc.). We use a posterior over those parameters fit to historical
  observed GMSL.
- **Importance weighting (Wong 2026 AR(1) likelihood):** Not every BRICK
  posterior draw fits the *paired* observed GMSL trajectory equally well.
  We compute a Wong importance weight `w_norm` per draw that reweights the
  posterior toward draws that match observed GMSL well. These weights
  flow through all downstream uncertainty quantification.

### 2.4 Final SLR ensemble: 10,000-triplet LHS with conditional BRICK weighting

The SLR-side figures (everything downstream of BRICK) are built from a
final ensemble of 10,000 (RFF, FaIR-cfg, BRICK-posterior) triplets sampled
by Latin Hypercube. Coverage is excellent: every one of the 490 RFFs is
used 19–22 times, every one of the 841 FaIR configs 11–13 times, and each
of the 10,000 MimiBRICK posterior members is used exactly once. The
triplet pairings are randomized across axes so there is no spurious
structural correlation between RFF, FaIR cfg, and BRICK draw.

For each triplet we run a paired baseline + pulse simulation through
1850–2300, then compute a Wong (2026) importance weight per row:

```
log(w_i)  ∝  l_FB( gmsl_i | cfg_i, post_i )  −  l_B( post_i )
```

Here l_FB is the AR(1) Gaussian log-likelihood of the row's paired
FaIR-driven BRICK trajectory against observed historical GMSL (Dangendorf
et al. 2024), and l_B is the same likelihood evaluated with BRICK's
default-forcing trajectory for that posterior member. The ratio rewards
(cfg, post) pairings whose joint historical fit beats the
unconditional-on-cfg fit for the same BRICK member.

Because the numerator l_FB depends on each row's *specific* paired FaIR
cfg, the weights are **conditional on the cfg** by construction — they
approximate the joint posterior p(cfg, post | obs GMSL) rather than the
product of marginals. This addresses a methodological concern about the
earlier 500-cell paired ensemble: that pairing FaIR climate-sensitivity
draws with BRICK posterior members independently of the cfg could let
high-sensitivity FaIR runs stack on top of high-sensitivity ice-sheet
parameters, inflating the projection spread. The conditional weighting
prevents this — though as it turned out, the practical effect was small.

**Effective sample size after weighting: ESS = 7,037 / 10,000 (70.4%)** —
i.e., the weighted 10,000-row ensemble is statistically equivalent to
~7,000 equal-weight independent samples. In Bayesian importance sampling
ESS > 50% of N is considered excellent; this is well within that range.

**Comparison to the earlier 500-cell paired ensemble:** the LHS-10k
percentiles agree with the older design to within ~1–2 cm at every
horizon. The win from the redesign is statistical resolution — the 95th
percentile is determined by ~500 samples instead of ~25 — not bias
correction. Both designs are conditional via the same Wong-weight
mechanism.

---

## 3. Key methodological choices to mention in prose

### 3.1 Observational anchors

- **GMST:** IGCC 2024 4-dataset consensus (HadCRUT5 + Berkeley Earth +
  GISTEMP + NOAAGlobalTemp). 2015–2024 mean rel. 1850–1900 preindustrial
  baseline = **+1.254 °C**. This is the value FaIR is bias-corrected to
  (see 3.2). The IGCC dataset is what FaIR's own calibration team uses.
- **SLR:** Dangendorf et al. 2024 (tide-gauge reconstruction) for
  pre-1993 historical data + NOAA STAR satellite altimetry for the
  altimetry era (1993–2024). 2015–2024 anchor: +6.38 cm rel. year 2000.

### 3.2 AR6-style bias correction (applied everywhere we report "rel PI")

FaIR's ensemble-median modelled 2015–2024 warming is +1.04 °C rel.
preindustrial, versus the IGCC observation of +1.254 °C. So the FaIR
ensemble systematically under-predicts the observed present-day warming
by about 0.21 °C.

We apply the AR6 framing: each FaIR trajectory is rebaselined to its
*own* 2015–2024 mean, then shifted up to the IGCC observed anchor:

```
T_corrected(t) = T_FaIR(t) − T_FaIR(2015-2024 mean) + 1.254 °C
```

Result: every trajectory passes through the observed present-day value,
and the future spread is added on top of observed warming. This is
standard AR6 projection-framing and respects the historical observation
record rather than blindly trusting the model's absolute level.

### 3.3 Hawkins-Sutton variance decomposition

The Hawkins-Sutton (2009) framework is the standard tool for asking
"where does the spread in a climate projection come from?" It decomposes
the total variance of a projection at year *t* into additive components:

- **Emissions uncertainty:** variance across RFF-SP scenarios, holding
  climate response and other factors fixed.
- **Climate-response uncertainty:** variance across FaIR parameter
  configs, for a given emissions trajectory.
- **Internal variability:** chaotic year-to-year fluctuations (only
  present when FaIR is run with stochastic seeds).
- **BRICK posterior uncertainty:** *for SLR only* — variance across
  BRICK ice-sheet / glacier / thermal-expansion parameter posteriors.

Each component is expressed as a fraction of total variance, varying
with year. The figure shows a stacked time series.

### 3.4 RFF-FaIR vs scenario-based projections like RCP/SSP

RFF-SP is a probabilistic 21st-century emissions set, *not* a small
number of policy scenarios. Where an IPCC report quotes "median SSP5-8.5
gives +4.4 °C by 2100," that's one specific aggressive-emissions
trajectory's median over CMIP model variants. The RFF-SP equivalent
would be: "across the full unmitigated socioeconomic range, the median
trajectory gives +2.8 °C by 2100, and the 95th-percentile RFF gives
+4.2 °C." RFF-SP has built-in probability weights; SSPs do not.

### 3.5 Pulse-marginal calculations (SC-GHG framing)

For social-cost-of-CO₂-style analysis: we run paired baseline + pulse
FaIR / BRICK runs. The "marginal climate response" to a 1 GtCO₂ emission
at 2030 is the year-by-year difference (pulse − baseline), shown as a
median + 5–95% band. These are the per-tonne sensitivities relevant for
discounting and welfare-economics math.

- **GMST marginal:** Linear in pulse size; computed at the +1 GtC
  production pulse (and verified pulse-size invariant). Per-GtCO₂ units
  obtained by dividing by the C-to-CO₂ molecular-mass ratio (3.667).
- **SLR marginal:** Has a nonlinearity from Antarctic ice-sheet (AIS)
  tipping at large pulses, so for the headline SC-SLR number we use the
  +0.01 GtC small-pulse companion run (linear regime). The 4-way variance
  decomposition (§3.3) is necessarily done at +1 GtC production-pulse
  scale, where the tipping-state-dependent variance is actually present.

### 3.6 The AIS tipping issue (Lemoine-style decomposition)

A small fraction (~5%) of BRICK posterior draws have ice-sheet states
pre-positioned near a tipping threshold (Antarctic SLR contribution at
year 2100 > 20 cm at baseline). For these draws, a 1 GtCO₂ pulse can
push the system over the tipping point, producing very large marginal
SLR. The figure caption uses "Lemoine decomposition" to refer to the
framework (after Derek Lemoine's work) where the expected marginal
damage is split into:

1. A **linear sensitivity** term — what the response would be in the
   absence of tipping (computed from the non-tipping-prone subset, or
   equivalently from the small-pulse limit).
2. A **tipping insurance premium** — the additional expected response
   from the probability of crossing a tipping threshold.

Currently the *split* is implemented (the
`AIS_TIPPING_THRESHOLD_CM = 20.0` classifier), but a fully Lemoine-style
decomposition figure is sketched, not built. We display medians (which
are pulse-size invariant — they exclude the AIS-tipping nonlinearity)
rather than means (which are dominated by the tipping tail).

---

## 4. Headline numbers (all post-bias-correction, IGCC-anchored, rel PI)

### 4.1 Median GMST crossing years (when does the median trajectory first exceed a threshold?)

| Threshold | Median crossing year |
|---|---|
| 1.5 °C | 2030 |
| 2.0 °C | 2050 |
| 2.5 °C | 2080 |
| 3.0 °C | 2131 |

The 5th / 50th / 95th-percentile crossing years span:

| Threshold | p5 | p50 | p95 |
|---|---|---|---|
| 1.5 °C | 2027 | 2030 | 2036 |
| 2.0 °C | 2040 | 2050 | (>5% never cross) |
| 3.0 °C | 2065 | 2131 | (>5% never cross) |

### 4.2 P(GMST > T) at 2100

| Threshold | Probability |
|---|---|
| > 1.5 °C | 99% |
| > 2.0 °C | 88% |
| > 2.5 °C | 65% |
| > 3.0 °C | 38% |
| > 3.5 °C | 18% |
| > 4.0 °C | 7% |

### 4.3 RFF-FaIR 2100 and 2150 distributions

- **2100**: median +2.77 °C, 5–95% range +1.76 to +4.17 °C
- **2150**: median +3.11 °C, 5–95% range +1.67 to +5.32 °C
- **Comparison with RCP8.5**: About 15% of RFF-FaIR trajectories in 2150
  exceed the AR6 SSP5-8.5 best-estimate median of +4.4 °C at 2100.

### 4.4 Hawkins-Sutton variance attribution — GMST

| Year (years from 2026) | Emissions | Climate response | Internal variability |
|---|---|---|---|
| 2026 (0) | 0% | 9% | 91% |
| 2040 (14) | 2% | 48% | 49% ← internal-variability crossover |
| 2046 (20) | 7% | 56% | 37% |
| 2100 (74) | 39% | 48% | 13% |
| 2123 (97) | 46% | 46% | 8% ← emissions-overtakes-climate crossover |
| 2150 (124) | 52% | 43% | 5% |

Phrasing for the post:
> "Internal variability accounts for more than half of the variability
> over the next ~15 years; emissions uncertainty overtakes climate-
> parameter uncertainty as the primary contributor about 100 years into
> the future."

### 4.5 Hawkins-Sutton variance attribution — SLR

The BRICK posterior contribution peaks early and declines monotonically:

| Year | Emissions | Climate response | Internal | BRICK posterior |
|---|---|---|---|---|
| 2040 | 6% | 62% | 4% | **28%** |
| 2046 | — | — | — | **29% ← peak** |
| 2100 | 30% | 52% | 1% | **17%** |
| 2150 | 39% | 47% | 0% | **14%** |

Interpretation: BRICK posterior matters most when the climate signal is
small (and ice-sheet response is mostly noise). Once warming gets large,
emissions and climate-sensitivity uncertainty dominate. The BRICK
posterior is *tightly constrained* (small) overall because the Wong
importance weighting against observed historical GMSL strongly disfavors
draws whose threshold values are unrealistic. What spread survives is
mostly *threshold value* uncertainty; the *gating* of whether tipping
happens at all is dominated by emissions + climate variance.

### 4.6 Marginal climate response per 1 GtCO₂ pulse at 2030

| Year | Median ΔGMST (°C / GtCO₂) | Median ΔSLR (cm / GtCO₂) |
|---|---|---|
| 2050 | +0.00037 | +0.0029 |
| 2100 | +0.00033 | +0.0104 |
| 2150 | +0.00034 | +0.0172 |

(ΔGMST from 1 GtC production pulse, paired baseline; ΔSLR from 0.01 GtC
small-pulse companion to avoid the AIS-tipping fat tail. Both
computed across the LHS-10k conditional-BRICK ensemble.)

ΔGMST is roughly flat after 2050 (CO₂ pulse has decayed); ΔSLR grows
monotonically because SLR has long inertia (commitment).

### 4.7 Pulse-marginal Hawkins-Sutton attribution

**ΔGMST per GtCO₂:**

| Year | Emissions | Climate response |
|---|---|---|
| 2050 | 1% | 99% |
| 2100 | 4% | 96% |
| 2150 | 7% | 93% |

Climate-sensitivity uncertainty dominates because the marginal response
is essentially linear in climate sensitivity.

**ΔSLR per GtCO₂:**

| Year | Emissions | Climate | AIS tipping-state | BRICK posterior |
|---|---|---|---|---|
| 2050 | 1% | 13% | 24% | **62%** |
| 2100 | 2% | 14% | 24% | **59%** |
| 2150 | 3% | 15% | 25% | **57%** |

Ice-sheet posterior parameters dominate the marginal SLR variance.
About a quarter is the AIS tipping-state dependence: whether a small
pulse pushes a near-tipping baseline state over the threshold depends
on the FaIR stochastic climate state at 2030.

---

## 5. Methodological caveats worth flagging in prose

### 5.0 LHS-10k ensemble supersedes the earlier 500-cell paired design

The SLR-side figures (obs overlay, Hawkins-Sutton SLR envelope, pulse-
marginal SLR panel, pulse-marginal H-S) use the LHS-10k conditional-BRICK
ensemble described in §2.4. The GMST-side figures (obs overlay, exceedance
table, crossing year, GMST H-S, pulse-marginal GMST) are unchanged — GMST
is upstream of BRICK, so the BRICK redesign doesn't affect them. The
total-SLR Hawkins-Sutton variance decomposition figure
(`updated_hawkins_sutton_slr.png`) still uses the earlier 13,500-row
ANOVA factorial design, because classical variance decomposition requires
the factorial replication structure that LHS doesn't provide — a Sobol-
style decomposition on the LHS-10k would give a different (and probably
similar) answer, but rebuilding that pathway is out of scope for the post.

### 5.1 FaIR's cool anomaly bias is not fully canceled by bias correction

Even after AR6 bias correction (which shifts all trajectories to match
IGCC at 2015–2024), FaIR's cumulative warming trajectory from 1850–1900
to present is about 0.21 °C cooler than IGCC observed. The bias
correction places the trajectories at the right *level* today, but the
*path* of warming from PI to today is gentler in FaIR than observed.

### 5.2 BRICK underestimates historical SLR

- Observed (Dangendorf 2024) GMSL rise 1900 → 2018: **+20.9 cm**
- BRICK p50 modelled rise 1900 → 2018: **+12.0 cm**
- Shortfall: **~8.9 cm**

About 2–3 cm of this shortfall is plausibly attributable to FaIR's cool
anomaly bias (via FaIR delivering less heat to BRICK than reality);
the remainder (~6–7 cm) is BRICK-side. Candidate causes: under-
parameterized glacier melt, conservative ice-sheet rate constants,
or a Wong AR(1) likelihood weighting that under-fits early-20th-century
discrepancies.

### 5.3 BRICK underestimates the modern SLR rate

Over 2010–2024:
- NASA STAR observed slope: **3.99 mm/yr**
- BRICK p50 slope: **2.60 mm/yr** (65% of obs)
- BRICK p95 slope: **3.14 mm/yr** (still below obs median)

Observed slope sits *outside* BRICK's 5–95% band — the BRICK ensemble
does not encompass the observed acceleration. Same proportional miss
holds over 1993–2024.

### 5.4 RFF-SP vs SSP probabilistic interpretation

RFF-SP is a single internally consistent probabilistic set, so quoting
percentiles is well-defined. SSPs are policy scenarios without intrinsic
probability weights, so comparing "RFF p50" to "SSP5-8.5 median" mixes
incommensurable concepts. Be careful with phrasing.

### 5.5 Median is pulse-size invariant; mean is not

The headline SC-CO₂-SLR sensitivity should always cite the **median**
small-pulse value. The mean response to a +1 GtC pulse is contaminated
by AIS tipping in a small subset of posterior draws, which makes it
sensitive to pulse size. We verified pulse-size invariance of the median
across 0.01, 0.1, and 1.0 GtC pulses.

---

## 6. Figure inventory (under `outputs/substack/`)

| Filename | What it shows |
|---|---|
| `obs_overlay.png` (2-panel) | FaIR band vs IGCC + BE GMST observations |
| `obs_overlay_recent.png` | Modern decade close-up, secondary axis rel PI |
| `obs_overlay_slr.png` | FaIR × BRICK band vs Dangendorf + NOAA STAR |
| `updated_hawkins_sutton.png` | GMST envelope (top) + 3-way H-S stack (bottom) |
| `updated_hawkins_sutton_slr.png` | GMSL envelope + 4-way H-S stack |
| `pulse_responses_clean.png` | 2×2: CO₂/CH₄ × ΔGMST/ΔSLR marginal responses |
| `pulse_convergence.png` | Multi-pulse-size convergence diagnostic |
| `pulse_hawkins_sutton.png` | 2×2: CO₂ × ΔGMST/ΔSLR envelopes + H-S decomp |
| `exceedance_table.png` | P(GMST > T) at 2050/2100/2150 |
| `exceedance_crossing_year.png` | p5 / median / p95 crossing year per threshold |
| `median_crossing_year.png` | Median crossing year only |

---

## 7. Jargon glossary (in case it's useful)

- **GMST:** Global mean surface temperature — usually expressed as an
  anomaly relative to some baseline period.
- **GMSL:** Global mean sea level — usually expressed in cm relative to
  a baseline year (we use year 2000 for satellite-era comparisons).
- **PI:** Preindustrial baseline, 1850–1900 average. The IPCC's
  standard reference period.
- **AIS:** Antarctic ice sheet.
- **GIS:** Greenland ice sheet.
- **TE:** Thermal expansion of the ocean.
- **AR6:** IPCC's 6th Assessment Report (2021).
- **CMIP6:** The 6th Coupled Model Intercomparison Project — the
  multi-model ensemble of full general circulation models.
- **SSP:** Shared Socioeconomic Pathway. The successor to RCP.
- **RCP:** Representative Concentration Pathway. CMIP5-era policy
  scenarios.
- **SC-GHG, SC-CO₂:** Social cost of greenhouse gas / carbon dioxide.
  The present discounted value of damages from one extra tonne.
- **Hawkins-Sutton decomposition:** A variance-of-variances analysis
  that partitions projection uncertainty into source components.
- **Internal variability:** Chaotic, unforced fluctuations of the
  climate system (e.g., ENSO, volcanoes treated as random).
- **Bias correction (AR6 style):** Shifting model trajectories to match
  observed present-day values, while preserving the modelled future
  *spread*.
- **Wong importance weighting:** Reweighting an MCMC posterior by how
  well each draw's predicted trajectory fits an observed time series
  under an AR(1) likelihood (after Wong et al.).
- **Pulse-marginal:** The difference between a baseline run and a run
  with a small extra emissions pulse — the per-tonne sensitivity.
- **Tipping insurance premium:** In a probabilistic damage framework,
  the extra expected damage attributable to the probability of crossing
  a nonlinear threshold (Lemoine-style framing).

---

## 8. What I am asking Claude chat for

- Help drafting clear plain-English explanations of the methods (§2, §3)
  for a general-audience post.
- Sanity-checking my interpretation of the headline numbers (§4) — am
  I phrasing the variance attribution correctly, etc.
- Helping me write good figure captions that explain what each panel
  shows without resorting to jargon.
- Flagging anywhere I'm conflating concepts (e.g., median-vs-mean of a
  skewed distribution, RFF-vs-SSP probabilistic interpretation,
  absolute-vs-anomaly bias framing).
- I draft the main narrative myself — Claude chat's job is figure
  captions, methods boxes, sanity checks on numbers, and clearer prose
  where I struggle.

---

## 9. What Claude chat should NOT do

- Don't invent numbers. Every quoted statistic should come from this
  handoff or a CSV in `outputs/substack/`.
- Don't claim there is a "consensus" or "best" projection — RFF-FaIR
  gives a distribution, and the post's value is showing that
  distribution, not collapsing it to a single number.
- Don't conflate "median RFF-FaIR" with "RCP8.5" or "SSP5-8.5" — these
  are different probabilistic objects.
- Don't say "2 °C is the federal discount rate" — for SC-GHG framing,
  3% is the current-EPA-relevant Ramsey rate; 2% is for academic
  comparability only and was reverted away from under recent EPA.

---

End of handoff.
