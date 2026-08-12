> **2026-08-12 — the model described here is now named `Ladrillo`** (was BRICK-F\*).
> This memo is frozen as written; see `CHANGELOG.md` (2026-08-12) for the path
> mapping. **Ladrillo 1.0** is defined as the version including the Greenland
> update as well as the GSIC and Antarctic updates, i.e. after pass-1 step 5 —
> which this memo predates.

# BRICK-F\*: an updated BRICK — three glacier reservoirs, recalibrated Antarctic dynamics, and an extended observational basis

Marcus C. Sarofim, NYU Marron Institute — 2026-08-10

Repository: `SLR-RFF-BRICK`, branch `brick-mengel-vnext`
Posterior: `data/MimiBRICK/parameters_subsample_brick_mengel_extC.csv`

> **Draft status.** Everything below the abstract is technical content, numbers,
> and methodology, generated from the committed code and outputs. The abstract
> is a first draft for Marcus to rewrite in his own voice.

---

## Abstract

BRICK-F\* is MimiBRICK v2.0.0 with three changes, calibrated together in one
joint fit: a **new glacier module**, a **recalibrated Antarctic ice sheet**, and
an **extended observational basis**.

**Glaciers.** The single-reservoir Wigley–Raper module is replaced by three
reservoirs split by volume response time — the Antarctic periphery (RGI region
19), a slow-responding block (Arctic Canada North, Russian Arctic, Svalbard,
Iceland), and the thirteen remaining regions. Each follows a Mengel-type
equilibrium curve S_eq(T) = a (1 − e^(−b(T − T_off))) with a Nauels-type
transient dS = min(κ·excess^ν, 1)(S_eq − S), driven by its **own**
glacier-area-weighted surface temperature rather than by global mean
temperature. The response exponent ν is fixed per reservoir at the value
reproducing that region's volume response time at both +1.5 K and +3.0 K; the
regional warming amplification is sampled under priors set by the spread across
three observational temperature products.

**Antarctic.** Six parameter groups that the stock model fixes or samples in
degenerate coordinates are freed and re-parameterised: the initial ocean
temperature; a sampled transient GMST-to-Antarctic-surface amplification
replacing the inverted paleo regression, with the T_ant(GMST=0) anchor
preserved; the fast-dynamics triplet under its paleo marginals; the seven DAIS
geometry parameters under a joint paleo prior; the runoff line sampled along its
identified direction rather than across a 0.9997-correlated ridge; and a surface
mass balance anchor against Rignot et al. (2019), area-corrected to the DAIS
disc, that breaks the mass-balance-minus-discharge degeneracy. The early-century
Antarctic overshoot that motivated this work is gone: hindcast bias is 0.00 cm
at 1900 and −0.004 cm on average over 1900–2026.

**Data.** Inventory from Farinotti et al. (2019); response times and the
committed-loss ladder from GlacierMIP3; modern glacier mass change and areas
from GlaMBIE (2025); the historical component budget from Frederikse et al.
(2020), extended with GRACE-FO ice-sheet mass and NOAA NCEI thermosteric sea
level; the total-sea-level target from Dangendorf et al. (2024) spliced to NOAA
STAR altimetry; regional temperatures from HadCRUT5. Three observationally
motivated set-asides are carried on the model side of the comparison rather than
by adjusting the data: uncharted ice absent from the inventory, a rate bias in
the pre-1960 reconstruction segment, and a pre-1901 accounting term in the
nineteenth-century melt datum.

**Results.** The posterior fits every calibration target with a mean bias below
0.5 cm over 1900–2026. Glacier projections at 2100 are 8.5 / 10.6 / 14.7 cm
under SSP1-2.6 / SSP2-4.5 / SSP5-8.5, inside the range spanned by MAGICC-SLR
(Nauels 2025) and the FACTS glacier modules at every scenario. Total sea level
at 2100 is 35.9 / 49.5 / 97.8 cm relative to 1995–2014. **Greenland is the one
module left untouched, and it shows**: it under-responds to scenario by a factor
of three relative to every other model considered here, and it is the intended
next piece of work.

---

## 1. What BRICK-F\* changes

| | BRICK 2.0 | BRICK-F\* |
|---|---|---|
| glacier module | one Wigley–Raper reservoir, no finite temperature-dependent equilibrium, driven by GMST | three reservoirs split by response time, temperature-dependent equilibrium volume, each on its own regional temperature |
| Antarctic dynamics | ocean temperature initial condition, fast-dynamics triplet and geometry fixed; runoff line sampled across a degenerate ridge; GMST→T_ant from the inverted paleo regression | all freed under paleo priors, geometry jointly; runoff line along its identified direction; sampled transient amplification with the anchor preserved; SMB anchored to Rignot 2019 |
| Greenland module | stock | **unchanged** |
| thermal expansion, land-water storage | stock | **unchanged** |
| glacier calibration data | historical budget only | + GlacierMIP3 committed ladder and response times, GlaMBIE modern rates and areas, Farinotti inventory, uncharted-ice accounting |
| ice-sheet calibration data | Frederikse 1900–2018 | + GRACE-FO 2002–2026, IMBIE 2023 as an independent cross-check |
| thermosteric | Frederikse 1900–2018 | + NOAA NCEI 2005–2025 |
| total sea level | Frederikse total | Dangendorf et al. 2024 spliced to NOAA STAR altimetry |
| error model | AR(1) per series | unchanged in form; σ and ρ sampled per series |

All of it is one joint calibration: there is no separate glacier fit and
Antarctic fit to reconcile. The 52-parameter posterior is sampled against all
five target series simultaneously.

## 2. Glacier module

### 2.1 What is replaced

BRICK-F\* is MimiBRICK v2.0.0 with the component in the
`:glaciers_small_icecaps` slot replaced. All wiring is preserved: the slot still
exposes `gsic_sea_level`, which `:global_sea_level` sums and the Antarctic
module consumes. Every other BRICK module — DAIS, the Antarctic ocean, the
Greenland ice sheet, thermal expansion, land-water storage — is unchanged.

### 2.2 Reservoirs

Glaciers are partitioned into three reservoirs by volume response time. The
partition covers all RGI regions except region 5, the Greenland periphery,
which belongs to the ice-sheet target scope.

| reservoir | RGI regions | inventory a (m SLE) | τ₅₀ at +1.5 K | τ₅₀ at +3.0 K | amplification (posterior) |
|---|---|---|---|---|---|
| `R19` | 19 (Antarctic periphery) | 0.069 ± 0.018 | 828 yr | 213 yr | 0.72 |
| `SLOWP` | 03, 06, 07, 09 | 0.146 ± 0.033 | 523 yr | 113 yr | 2.61 |
| `FAST` | 01, 02, 04, 08, 10–18 | 0.140 ± 0.024 | 130 yr | 37 yr | 1.44 |

The split is by response time because that is the property a single reservoir
cannot represent: a 130-year and an 828-year reservoir sharing one relaxation
constant force the fast regions to under-respond and the slow ones to
over-respond, in opposite directions, over the same historical window.

### 2.3 Equations

For each reservoir *b*, with driver T_b(t) in K relative to 1850–1900:

```
S_eq,b(T)  = a_b · (1 − exp(−b_b · (T − T_off,b)))          equilibrium loss
T_eq,b(S)  = T_off,b − ln(1 − S/a_b) / b_b                  temperature this stock is in equilibrium with
excess     = max(T_b(t−1) − T_eq,b(S_b), 0)
S_b(t)     = S_b(t−1) + min(κ_b · excess^ν_b, 1) · (S_eq,b − S_b(t−1))
```

with S_b(t₀) = 0 and the driver lagged one year. The slot output is the sum over
all three reservoirs; the component additionally exposes SLOWP + FAST, the scope
of the historical glacier target (see §5.1).

`ν_b` is the exponent on the temperature excess: it is what lets a reservoir
respond faster in a warmer climate. It is **fixed**, not sampled — the hindcast
cannot identify it (free fits drive it to zero), so it is set per reservoir to
the value that reproduces the region's GlacierMIP3 response time at **both**
+1.5 K and +3.0 K, solved jointly with κ_b. Fixed values are 1.545 / 1.622 /
1.567 for R19 / SLOWP / FAST.

### 2.4 The temperature frame

Each reservoir is driven by the **glacier-area-weighted surface temperature of
its own regions**, not global mean temperature. Historically this comes from
HadCRUT5 sampled on the GTN-G region masks, area-weighted by GlaMBIE glacier
area at 2000. Beyond the observations the driver is amp_b × GMST, spliced so
that the modelled driver matches the observed driver's mean over the last eleven
observed years.

Over 1995–2024 the three drivers warm by +0.60 K (R19), +1.42 K (FAST) and
+2.50 K (SLOWP) — a factor of four across reservoirs. A single global driver
with a single scaling cannot deliver that.

amp_b is **sampled**, under priors centred on the observational through-origin
fit and bounded by the spread across three temperature products (HadCRUT5,
Berkeley Earth, GISTEMP): N(0.72, 0.15) on [0.58, 0.88] for R19,
N(2.50, 0.45) on [1.80, 3.50] for SLOWP, N(1.45, 0.15) on [1.33, 1.82] for FAST.
The wide SLOWP prior reflects a genuine dataset disagreement — the three
products give 1.82, 2.48 and 3.46 for that block.

---

## 3. Antarctic ice sheet

The DAIS module itself is unchanged. What changes is which of its parameters are
free, the coordinates they are sampled in, and the priors and anchors they are
sampled under. Six groups:

**3.1 Ocean temperature initial condition.** `ais_ocean_temperature₀` sets the
sub-shelf melt forcing at the start of the run and therefore the pace of
nineteenth- and early-twentieth-century Antarctic loss. It is freed under
N(0.72, 0.50) on [0.50, 2.00]; posterior 0.86 [0.54, 1.54]. This is the
parameter that removes the early-century overshoot.

**3.2 GMST → Antarctic surface temperature.** The stock map, T_ant = (GMST −
15.42)/0.8365, is the *inverted paleo/equilibrium* regression — an amplification
of 1.196, appropriate to an equilibrated ice sheet, not to a transient one.
BRICK-F\* samples the amplification directly with the T_ant(GMST = 0) anchor
preserved: coefficient = 1/amp, intercept = −T_ant,0/amp, so only the anomaly
scaling moves and the threshold-crossing GMST stays interpretable as
(threshold − T_ant,0)/amp. Prior N(1.08, 0.15), the CMIP6 land-frame secant;
posterior 1.06 [0.82, 1.31].

**3.3 Fast dynamics.** λ, γ and κ — the marine ice-cliff / ice-shelf collapse
triplet — are freed under their existing paleo marginals rather than fixed at
the prior medoid. The medoid is biased in the pulse-amplifying direction
(λ 0.0137 against a paleo mean of 0.0104) and carried no reported uncertainty at
all, which matters because λ is the dominant lever on the century-scale pulse
response. The historical window does not identify them, so they largely sample
their prior; that is the intent — the uncertainty is propagated rather than
silently set to zero.

**3.4 Geometry, jointly.** The seven DAIS geometry parameters (`ais_mu`,
`ais_bedheight0`, `ais_slope`, `ais_iceflow0`, `ais_precip0`, and the runoff-line
pair) are freed under a **joint** paleo prior built from the DAISfastdyn
ensemble, so the paleo correlation structure survives. The prior is applied in
standardised form — a multivariate normal on z = (θ − μ)/sd with the correlation
matrix — because the raw covariance is ill-conditioned (condition number 5×10¹³;
the parameter scales span 10⁻⁴ to 10³) while the correlation matrix is not
(2.75). Bounds are the ensemble minima and maxima. `ais_precip0` is sampled in
log space, matching MimiBRICK v2.0.0's reparameterisation.

**3.5 Runoff line, in its identified direction.** The runoff-line height enters
the model only as h_R = h₀ + c·T_ant, so (h₀, c) ride a ridge with r = 0.9997
while the identified combination is the runoff onset temperature
T_on = −h₀/c. BRICK-F\* samples (T_on, c) and reconstructs h₀ = −T_on·c per
draw, with the joint paleo prior rebuilt in those coordinates: T_on marginal
−15.64 ± 5.54, i.e. runoff onset at about +2.3 °C GMST under the default map,
consistent with Shaffer's DAIS (+2.5 °C), and r(T_on, c) = +0.64 rather than
0.9997. Posterior T_on −17.75 [−17.92, −17.53].

**3.6 Surface mass balance anchor.** Antarctic mass balance is
accumulation minus discharge, and the sea-level target constrains only the
difference: the posterior pinned it to −145 ± 15 Gt/yr while the two fluxes
individually sat at ±505 and ±509 Gt/yr — a textbook input-output degeneracy,
and precisely where the worst-mixing parameter (`ais_iceflow0`) lives. One
Gaussian likelihood term on the model's own accumulation (1979–2008 mean)
anchors the absolute scale, against Rignot et al. (2019) grounded-Antarctic SMB
2098 ± 133 Gt/yr. **The area convention is handled explicitly**: Rignot's figure
is for the observed grounded area of 12.295×10⁶ km², whereas DAIS is an
idealised π R₀² = 10.92×10⁶ km² disc, so the target is scaled by 0.888 to
1863 ± 118 Gt/yr. Skipping that scaling would push a ±15% bias into
`ais_precip0` and into the pulse response.

**Result.** Antarctic hindcast bias is +0.00 cm at 1900, −0.006 at 1950, −0.13
at 2018 and +0.09 at 2025, with a mean of −0.004 cm over the 126 fit years and
99.2% predictive coverage. The fit tracks the GRACE-FO plateau (bias −0.08 cm at
2019, +0.01 at 2022, +0.05 at 2024).

**Cost.** Eight parameter marginals do not converge across chains, and all eight
are in this geometry block. They are unidentified by the historical window by
construction, so they sample their paleo prior; convergence is therefore judged
on the projected sea level (§6), not on these marginals. The practical
consequence is that the Antarctic **upper tail** in §8 is prior-propagated
rather than observationally constrained, and should be read that way.

## 4. Calibration data

| dataset | what it provides | reference |
|---|---|---|
| Farinotti et al. 2019 | glacier ice volume, the reservoir inventory prior a_b | *Nat. Geosci.* 12:168 |
| GlacierMIP3 (Zekollari et al. 2025) | committed loss at +1.2/1.5/2.0/3.0 K, regional volume response times, ISIMIP3 regional warming ratios | Zenodo 15046588 |
| GlaMBIE 2025 | regional glacier mass change 2000–2024, glacier areas, region-19 series for the target seam | DOI 10.5904/wgms-glambie-2024-07 |
| Frederikse et al. 2020 | historical component sea-level budget 1900–2018 and its 5000-member uncertainty ensemble | *Nature* 584:393 |
| Dangendorf et al. 2024 | total GMSL reconstruction 1900–2021 | — |
| NOAA STAR altimetry | total GMSL 2022–2024 | — |
| GRACE-FO JPL mascon RL06.3Mv4 | Antarctic and Greenland mass 2002–2026 | DOI 10.5067/TEMSC-3JC634 |
| NOAA NCEI | 0–2000 m thermosteric sea level 2005–2025 | — |
| HadCRUT5 (gridded) | regional and global surface temperature | — |
| Parkes & Marzeion 2018 | uncharted-ice content of the historical glacier budget | *Nature* 563:551 |
| Rignot et al. 2019 | Antarctic surface mass balance anchor | *PNAS* 116:1095 |
| IMBIE 2023 (Otosaka et al.) | independent cross-check on the GRACE splices (not fit) | — |
| FaIR 2.2.4 (calibration 1.4.5) | GMST and ocean heat content forcing | — |

Relative to the calibration BRICK 2.0 was fit against, the additions are the
whole glacier-constraint set (Farinotti, GlacierMIP3, GlaMBIE, Parkes &
Marzeion), the post-2018 extensions (GRACE-FO, NOAA NCEI, GlaMBIE), the Rignot
Antarctic mass-balance anchor, and the replacement of the Frederikse total by
the independent Dangendorf reconstruction spliced to NOAA STAR altimetry.

The glacier inputs are assembled by `python/brickf_data.py`, which names each input file
and emits the three artifacts the calibrator reads. `python/test_brickf_data.py`
checks it.

---

## 5. Target construction and set-asides

The historical glacier record and the model measure slightly different things.
Three differences are priced explicitly, as sampled parameters carried on the
**model side** of the comparison, so the observational data are never edited.

### 5.1 Region-19 scope (a target adjustment, not a parameter)

The Frederikse glacier segment assumes zero Antarctic-periphery melt; the
GlaMBIE splice that extends it from 2019 includes region 19. The observed
GlaMBIE region-19 cumulative is therefore removed from the target's 2019+
segment, so the whole series has one scope — SLOWP + FAST — and the model is
compared against it on that scope. Net removal is 0.38 mm by 2023. The
region-19 reservoir is still simulated and still contributes to total sea level;
it is only excluded from this one target.

### 5.2 Uncharted ice — `gic_u_unch`

Parkes & Marzeion (2018) show the historical budget contains glaciers absent
from the modern inventory. That mass is real sea level but has no reservoir to
melt from, so it is added to the model's glacier series before comparison, with
a taper that is flat from 1901, ramps to zero rate by 2005, and is constant
thereafter. Prior flat [14.5, 41.8] mm; posterior 26.5 [19.0, 35.0] mm.

Because the term is exhausted by 2005, it is a hindcast construct: in a
projection re-referenced to 1995–2014 it contributes under 0.1 mm. Include it in
hindcast overlays; ignore it in future deltas.

### 5.3 Early-segment rate bias — `gic_delta`

The pre-1960 part of the target rests on the Marzeion-2015 reconstruction, whose
early rate is contested. A linear rate correction is applied to the
**observations** over 1900–1959, scaled by a sampled parameter with prior
N(0, 0.30) mm/yr. Posterior 0.21 [0.10, 0.33] mm/yr — a real but sub-σ shift.

### 5.4 Nineteenth-century ledger — `gic_u_pre`, `gic_s_r5`

The nineteenth-century melt datum, S(1900) − S(1850) = 20 ± 9 mm, covers a
scope wider than the model's reservoirs: it includes pre-1901 uncharted ice and
a region-5 share. Both are carried as sampled set-asides added to the model's
S(1900) before the datum is evaluated, priors flat [0, 25] mm and
N(2.5, 2) mm. Posteriors 6.5 [0.6, 18.8] mm and 2.5 [0.4, 5.5] mm. The ledger —
the model's own S(1900) − S(1850) of 15.9 mm plus these two set-asides — sums to
26.2 mm against the 20 ± 9 mm datum, z +0.68.

### 5.5 Likelihood terms

Beyond the five time-series terms (Antarctic, glacier, Greenland, thermosteric,
total — each with a heteroscedastic AR(1) error model whose σ and ρ are
sampled), the glacier block adds:

- **inventory**: Σa_b − S_all(2000) ~ N(0.290, 0.060) m SLE;
- **committed ladder**, per reservoir: the four GlacierMIP3 rungs, with the
  band-derived σ and a 0.6 cross-rung correlation (the rungs share models);
- **modern rate**, per reservoir: mean 2000–2024 GlaMBIE rate, error inflated
  ×1.5; region 19 excluded, matching the target scope;
- **nineteenth-century ledger** as in §3.4;
- **Antarctic surface-mass-balance anchor** against Rignot et al. (2019).

---

## 6. Calibration and posterior

Sampling is adaptive-Metropolis over **52 parameters** (42 physical + 10 AR(1)
noise), four chains of 2×10⁶ iterations from overdispersed starts, seeds
2026–2029, acceptance 0.236–0.237.

Convergence is judged **on the deliverable**: projected sea level at 2100 and
2150, pushed through the model per chain. R̂ = 1.000 at 2100 and 1.002 at 2150.
Eight nuisance marginals do not converge; all eight are in the Antarctic
fast-dynamics geometry block, which the historical window does not identify —
those parameters sample their paleo prior by design.

The full parameter table (median, 5–95%, prior, prior source) is
`outputs/brickf_posterior_summary.csv`; the glacier block is:

| parameter | median | 5–95% | prior |
|---|---|---|---|
| `gic_a_R19` | 0.0669 | 0.0395 – 0.0943 | N(0.069, 0.018) m SLE |
| `gic_b_R19` | 0.878 | 0.205 – 2.71 | flat [0.05, 3.0] |
| `gic_T_off_R19` | −1.24 | −2.81 – 0.58 | flat [−3.0, 1.0] |
| `gic_log10_kappa_R19` | −2.78 | −3.00 – −2.56 | N(−2.686, 0.114) |
| `gic_a_SLOWP` | 0.131 | 0.0854 – 0.178 | N(0.146, 0.033) m SLE |
| `gic_b_SLOWP` | 0.196 | 0.113 – 0.426 | flat [0.05, 3.0] |
| `gic_T_off_SLOWP` | −1.85 | −2.90 – −0.24 | flat [−3.0, 1.0] |
| `gic_log10_kappa_SLOWP` | −3.46 | −3.68 – −3.24 | N(−3.402, 0.114) |
| `gic_a_FAST` | 0.154 | 0.124 – 0.186 | N(0.140, 0.024) m SLE |
| `gic_b_FAST` | 0.350 | 0.260 – 0.496 | flat [0.05, 3.0] |
| `gic_T_off_FAST` | −1.53 | −2.14 – −0.89 | flat [−3.0, 1.0] |
| `gic_log10_kappa_FAST` | −2.53 | −2.70 – −2.36 | N(−2.559, 0.114) |
| `gic_amp_R19` | 0.724 | 0.598 – 0.858 | N(0.72, 0.15) |
| `gic_amp_SLOWP` | 2.61 | 2.03 – 3.17 | N(2.50, 0.45) |
| `gic_amp_FAST` | 1.44 | 1.34 – 1.62 | N(1.45, 0.15) |

The Antarctic block:

| parameter | median | 5–95% | prior |
|---|---|---|---|
| `ais_ocean_temperature₀` | 0.863 | 0.537 – 1.541 | N(0.72, 0.50) on [0.50, 2.00] |
| `ais_gmst_amp` | 1.061 | 0.818 – 1.305 | N(1.08, 0.15) |
| `antarctic_alpha` | 0.240 | 0.113 – 0.357 | paleo marginal |
| `antarctic_nu` | 0.0106 | 0.0069 – 0.0139 | paleo marginal |
| `antarctic_temp_threshold` | −15.58 | −16.21 – −14.90 | paleo marginal |
| `antarctic_lambda` | 0.0106 | 0.0054 – 0.0164 | paleo marginal |
| `antarctic_gamma` | 2.76 | 1.38 – 3.96 | paleo marginal |
| `antarctic_kappa` | 0.0578 | 0.0387 – 0.0772 | paleo marginal |
| `anto_alpha` | 0.359 | 0.183 – 0.566 | paleo marginal |
| `anto_beta` | 1.03 | 0.311 – 1.75 | paleo marginal |
| `ais_mu` | 10.4 | 8.08 – 12.74 | joint paleo geometry prior |
| `ais_bedheight0` | 780.5 | 748.9 – 811.2 | joint paleo geometry prior |
| `ais_slope` | 6.19e−4 | 5.89e−4 – 6.57e−4 | joint paleo geometry prior |
| `ais_iceflow0` | 1.069 | 0.779 – 1.364 | joint paleo geometry prior |
| `ais_precip0_LOG` | −0.637 | −0.992 – −0.289 | joint paleo geometry prior |
| `ais_runoff_Ton` | −17.75 | −17.92 – −17.53 | joint paleo prior in (T_on, c) |
| `ais_c` | 89.8 | 59.3 – 121.8 | joint paleo prior in (T_on, c) |

`b` and `T_off` are given flat bounds rather than Gaussian priors: they are
constrained by the committed-ladder likelihood, and a prior centred on the same
GlacierMIP3 information would count it twice. κ carries a Gaussian prior whose
centre is the response-time-anchored solve, with σ = 0.114 (±30%).

Posterior inventory: Σa_b = 0.352 m SLE.

---

## 7. Observation comparison

`figures/brickf_fig1_hindcast.png`; numbers in
`outputs/postpred_extC_{bias,coverage}.csv`.

The posterior is pushed over 1900–2026 on the calibration forcing and compared
to the targets on the calibration re-reference window, 1995–2005. Two bands are
reported: the posterior-parameter band, and the predictive band that adds a draw
from the calibrated error model (AR(1) plus per-year observational σ) — the
latter is the correct one for asking whether the model fits.

| component | mean bias (cm) | 90% coverage, parameter band | 90% coverage, predictive band |
|---|---|---|---|
| Antarctic ice sheet | −0.00 | 84.9% | 99.2% |
| glaciers | −0.00 | 62.9% | 100% |
| Greenland ice sheet | −0.40 | 31.0% | 68.3% |
| thermal expansion | +0.24 | 27.8% | 100% |
| total | +0.03 | 40.8% | 100% |

Two things to note honestly:

- **Greenland** is the one component whose observations fall outside the
  predictive band a third of the time. The failures are a single contiguous
  window, **1942–1982**, over which the model sits 0.5–0.7 cm below the
  Frederikse target. This is BRICK's stock Greenland module, unchanged by this
  work.
- Coverage above 90% elsewhere means the calibrated AR(1) error model is
  conservative: the residuals are strongly autocorrelated, which inflates the
  marginal predictive variance.

The Antarctic fit tracks the GRACE-FO plateau: bias −0.08 cm at 2019, +0.01 at
2022, +0.05 at 2024.

### Committed loss against GlacierMIP3

`outputs/brickf_committed_ladder.csv`. Per reservoir, on the observed 2020 stock
— the denominator the likelihood uses — every rung sits within 1.2σ of the
GlacierMIP3 central value:

| reservoir | +1.2 K | +1.5 K | +2.0 K | +3.0 K |
|---|---|---|---|---|
| R19 | 74.6% (z +1.17) | 79.3% (z +0.97) | 85.1% (z +0.75) | 92.4% (z +0.80) |
| SLOWP | 52.5% (z +0.50) | 59.3% (z +0.42) | 68.5% (z +0.17) | 81.2% (z −0.10) |
| FAST | 50.7% (z +0.68) | 57.7% (z +0.65) | 67.3% (z +0.31) | 80.4% (z +0.14) |

In **aggregate** the +1.2 K rung sits about two points above the GlacierMIP3
likely upper bound — 56.3% [41.1, 69.9] against 37.4% [11.8, 54.0]; the other
three rungs are inside. This is an aggregation effect, not a denominator
artifact: it is unchanged (56.6%) if the model's own simulated 2020 stock
(74.8 mm) is used instead of the observed one (76.7 mm). Three reservoirs each
sitting modestly high, combined against a tighter aggregate band, put the
aggregate just outside at the lowest rung.

---

## 8. Projections, and comparison with FACTS, MAGICC-SLR and BRICK 2.0

`figures/brickf_fig2_ssp_total.png`, `figures/brickf_fig3_glaciers.png`;
`outputs/ssps_components_2300_extC.csv`,
`outputs/brickf_model_comparison{,_spread}.csv`.

Projections use FaIR mean GMST and ocean heat per SSP, so the reported BRICK
bands are **posterior-parameter spread only**. MAGICC and FACTS bands also carry
climate uncertainty. Medians are comparable; band widths are not. All values
are cm relative to 1995–2014 (FACTS relative to baseyear 2005).

### 8.1 BRICK-F\* by component

| | SSP1-2.6 | SSP2-4.5 | SSP5-8.5 |
|---|---|---|---|
| **2100** glaciers / GIS / AIS / TE / LWS | 8.5 / 6.6 / 4.9 / 13.2 / 2.6 | 10.6 / 7.3 / 11.7 / 17.3 / 2.6 | 14.7 / 8.8 / 45.8 / 25.9 / 2.6 |
| **2100** total | 35.9 [34.0, 38.8] | 49.5 [41.5, 97.1] | 97.8 [73.8, 132.3] |
| **2150** total | 48.9 | 112.1 | 200.5 |
| **2300** total | 77.9 | 288.5 | 501.7 |

Bands are 5–95%. Beyond 2100 the SSP2-4.5 and SSP5-8.5 distributions are
strongly right-skewed by Antarctic fast dynamics.

### 8.2 Glaciers at 2100

| source | module | SSP1-2.6 | SSP2-4.5 | SSP5-8.5 | spread 1-2.6→5-8.5 |
|---|---|---|---|---|---|
| **BRICK-F\*** | extC | **8.5** | **10.6** | **14.7** | **+6.1** |
| MAGICC-SLR | Nauels 2025 | 10.4 | 12.5 | 15.3 | +4.8 |
| FACTS | ar5glaciers | 8.9 | 11.4 | 15.5 | +6.6 |
| FACTS | emuglaciers | 9.2 | 12.2 | 17.7 | +8.5 |
| BRICK 2.0 | Wigley–Raper | 12.0 | 13.5 | 16.5 | +4.5 |

BRICK-F\* sits inside the multi-model range at every scenario. The comparison
with BRICK 2.0 is where the structural change shows: Wigley–Raper has no finite
temperature-dependent equilibrium, so it projects 12.0 cm under SSP1-2.6 — more
than any of the other three models — and its scenario spread is the smallest of
the five. Extended to 2300 (figure 3c) BRICK-F\* approaches a scenario-dependent
equilibrium (27 cm under SSP5-8.5, 76% of the 35.5 cm inventory), while
Wigley–Raper continues melting past the inventory limit.

### 8.3 Totals and other components at 2100

| component | BRICK-F\* | MAGICC-SLR | FACTS range across modules |
|---|---|---|---|
| glaciers | 10.6 | 12.5 | 11.4 – 12.2 |
| Greenland | 7.3 | 9.3 | 8.0 – 14.4 |
| Antarctic | 11.7 [5.5, 41.0] | 11.2 [3.2, 23.9] | 5.5 – 13.7 |
| thermal expansion | 17.3 | 16.6 | 18.8 |
| total | 49.5 | 53.2 | 48.7 – 67.9 |

(SSP2-4.5; BRICK/MAGICC bands 17–83%.) Under SSP5-8.5 the two totals coincide
at 97.8 cm; FACTS workflows give 64.9–91.9 cm.

Two BRICK-F\* characteristics worth stating plainly:

- **Antarctic**: the median agrees with MAGICC, but the upper tail is heavier
  (17–83% reaching 41 cm at SSP2-4.5). That is the DAIS fast-dynamics
  parameterisation, whose geometry parameters the historical window does not
  identify and which therefore sample their paleo prior.
- **Greenland**: BRICK-F\* under-responds to scenario — +2.2 cm from SSP1-2.6 to
  SSP5-8.5 at 2100, against +6.3 to +7.3 cm in MAGICC and every FACTS module.
  This is the stock BRICK Greenland module. It is the obvious next target for
  the same treatment the glaciers received here.

---

## 9. Implementing this in BRICK

Everything needed is in the repository; the pieces to port are small.

| file | what it is |
|---|---|
| `julia/glaciers_nu3_component.jl` | the Mimi component: 3 reservoirs, 15 parameters, 3 drivers. 82 lines. |
| `julia/brick_mengel.jl` | `build_brick_nu3` / `update_brick_nu3!` / `set_glacier_forcing3!` — builds a v2.0.0 model with the component swapped into the glacier slot and land-water storage seeded reproducibly. |
| `julia/brickf_projection.jl` | the projection kernel: posterior loading, the per-block driver splice, the 52-parameter apply, rebaselining. Use this rather than re-deriving the parameter map. |
| `python/brickf_data.py` | assembles every data source and emits the three calibrator inputs. |
| `julia/calibrate_mcmc_ext.jl` | the calibrator, including all likelihood terms in §5.5. |
| `data/MimiBRICK/parameters_subsample_brick_mengel_extC.csv` | 10 000-draw posterior subsample. |
| `outputs/extc_block_constants.csv` | the per-reservoir structural constants: inventory priors, response times, GlaMBIE rates, amplifications, ladder rungs, anchored (κ, ν). |
| `data/observations/t_glac_blocks.csv` | the three historical temperature drivers. |
| `outputs/paleo_geo_prior_ton.csv` | the joint DAIS geometry prior in (T_on, c) coordinates (§3.4–3.5). |

The Antarctic changes are **not** a new component — DAIS itself is stock. They
live entirely in the calibrator: which parameters are pushed onto the free list,
the joint geometry prior, the (T_on, c) reparameterisation reconstructed as
h₀ = −T_on·c per draw, the anchor-preserving amplification map, and the Rignot
SMB likelihood term. Adopting them means porting those blocks of
`calibrate_mcmc_ext.jl`, not swapping a module.

**Minimum port.** To run the glacier module inside an existing BRICK: take
`glaciers_nu3_component.jl`, `extc_block_constants.csv` and
`t_glac_blocks.csv`; set ν_b from `nu_anch_obsfit`; draw the remaining glacier
parameters from the posterior subsample; build each driver as the observed
series through 2024, spliced to amp_b × GMST with the eleven-year
anchor-preserving offset.

**Tests.** `./run_brickf_tests.sh` runs all three suites: the data module
reproduces the committed calibrator inputs byte-for-byte and satisfies the
physical relations the constants encode; the calibrator's code path reproduces
an independent Python reference at 5×10⁻¹³ on both amplification bases; and the
projection kernel reproduces the same reference, applies the posterior
deterministically, and is monotone across scenarios in every component.

**Reproducing the results in this memo.**

```bash
julia --project=julia_v2 julia/project_ssps_components_brickf.jl 2000
julia --project=julia_v2 julia/posterior_predictive_brickf.jl 2000
python3 python/extract_magicc_components.py
python3 python/brickf_model_comparison.py
python3 python/brickf_committed_ladder.py
python3 python/brickf_posterior_summary.py
python3 python/plot_brickf_memo_figures.py
```

---

## Known limitations, and what comes next

**Greenland is the next module.** It is the only ice component BRICK-F\* leaves
at stock, and it is now the weakest part of the model on two independent
measures: its scenario response is a third of everyone else's (+2.2 cm from
SSP1-2.6 to SSP5-8.5 at 2100, against +6.3 to +7.3 cm in MAGICC-SLR and in every
FACTS module, §8.3), and its hindcast misses a contiguous 1942–1982 window by
0.5–0.7 cm, the only such failure in the fit (§7). The glacier work here is a
usable template: identify the structural limitation, bring in the process-model
intercomparison and inventory data that constrain the missing behaviour, and
fold the new module into the same joint calibration rather than fitting it
separately.

Remaining limitations:

1. **Antarctic upper tail** is driven by geometry parameters the historical
   record does not identify; the reported spread is a prior-propagated tail, not
   an observationally constrained one.
3. **Aggregate committed loss at +1.2 K** sits ~2 points above the GlacierMIP3
   likely range while each reservoir is individually within 1.2σ (§7).
4. **Projection bands are parameter-only** — they carry no climate uncertainty
   and no structural uncertainty, and are therefore narrower than AR6's
   assessed ranges by construction.
5. **ν is fixed, not sampled.** The hindcast cannot identify it; the values are
   set by the GlacierMIP3 response times. Its uncertainty is not propagated.
6. **Land-water storage** is the MimiBRICK default, climate-independent and
   uncalibrated, ~2.6 cm at 2100.
7. **Thermal expansion** is stock BRICK on prescribed ocean heat content. It
   fits well (mean bias +0.24 cm) and was not revisited.
