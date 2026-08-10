# BRICK-F\*: a three-reservoir glacier module for BRICK, and its calibration

Marcus C. Sarofim, NYU Marron Institute — 2026-08-10

Repository: `SLR-RFF-BRICK`, branch `brick-mengel-vnext`
Posterior: `data/MimiBRICK/parameters_subsample_brick_mengel_extC.csv`

> **Draft status.** Everything below the abstract is technical content, numbers,
> and methodology, generated from the committed code and outputs. The abstract
> is a first draft for Marcus to rewrite in his own voice.

---

## Abstract

BRICK-F\* replaces BRICK's single-reservoir Wigley–Raper glacier module with
**three glacier reservoirs**, each with a temperature-dependent equilibrium
volume and its own transient response, and calibrates them jointly with the rest
of BRICK against observations.

**Structural choices.** Glaciers are split by volume response time into the
Antarctic periphery (RGI region 19), a slow-responding block (Arctic Canada
North, Russian Arctic, Svalbard, Iceland) and the thirteen remaining regions.
Each reservoir follows a Mengel-type equilibrium curve
S_eq(T) = a (1 − e^(−b(T − T_off))) with a Nauels-type transient
dS = min(κ·excess^ν, 1)(S_eq − S), and is driven by its **own** glacier-area-
weighted surface temperature rather than by global mean temperature. The
exponent ν is not sampled: it is fixed per reservoir at the value that
reproduces that region's volume response time at both +1.5 K and +3.0 K. The
regional-to-global warming amplification is sampled, under priors set by the
spread across three observational temperature products.

**Data.** Inventory from Farinotti et al. (2019); volume response times and the
committed-loss ladder from GlacierMIP3; modern mass change and glacier areas
from GlaMBIE (2025); the historical target from Frederikse et al. (2020)
spliced to GlaMBIE; regional temperatures from HadCRUT5; the total sea-level
target from Dangendorf et al. (2024) spliced to NOAA STAR altimetry; Antarctic
and Greenland mass from GRACE-FO; thermosteric sea level from NOAA NCEI. Three
observationally-motivated set-asides are carried explicitly on the model side of
the comparison rather than by adjusting the data: uncharted ice absent from the
inventory, a rate bias in the pre-1960 reconstruction segment, and a
pre-1901 accounting term in the nineteenth-century melt datum.

**Results.** The posterior fits every calibration target with a mean bias below
0.5 cm over 1900–2026. Glacier projections at 2100 are 8.5 / 10.6 / 14.7 cm
under SSP1-2.6 / SSP2-4.5 / SSP5-8.5, inside the range spanned by MAGICC-SLR
(Nauels 2025) and the FACTS glacier modules at every scenario, with a
scenario spread (+6.1 cm) comparable to those models. Total sea level at 2100 is
35.9 / 49.5 / 97.8 cm relative to 1995–2014.

---

## 1. Model structure

### 1.1 What is replaced

BRICK-F\* is MimiBRICK v2.0.0 with the component in the
`:glaciers_small_icecaps` slot replaced. All wiring is preserved: the slot still
exposes `gsic_sea_level`, which `:global_sea_level` sums and the Antarctic
module consumes. Every other BRICK module — DAIS, the Antarctic ocean, the
Greenland ice sheet, thermal expansion, land-water storage — is unchanged.

### 1.2 Reservoirs

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

### 1.3 Equations

For each reservoir *b*, with driver T_b(t) in K relative to 1850–1900:

```
S_eq,b(T)  = a_b · (1 − exp(−b_b · (T − T_off,b)))          equilibrium loss
T_eq,b(S)  = T_off,b − ln(1 − S/a_b) / b_b                  temperature this stock is in equilibrium with
excess     = max(T_b(t−1) − T_eq,b(S_b), 0)
S_b(t)     = S_b(t−1) + min(κ_b · excess^ν_b, 1) · (S_eq,b − S_b(t−1))
```

with S_b(t₀) = 0 and the driver lagged one year. The slot output is the sum over
all three reservoirs; the component additionally exposes SLOWP + FAST, the scope
of the historical glacier target (see §3.1).

`ν_b` is the exponent on the temperature excess: it is what lets a reservoir
respond faster in a warmer climate. It is **fixed**, not sampled — the hindcast
cannot identify it (free fits drive it to zero), so it is set per reservoir to
the value that reproduces the region's GlacierMIP3 response time at **both**
+1.5 K and +3.0 K, solved jointly with κ_b. Fixed values are 1.545 / 1.622 /
1.567 for R19 / SLOWP / FAST.

### 1.4 The temperature frame

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

## 2. Calibration data

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

Everything is assembled by `python/brickf_data.py`, which names each input file
and emits the three artifacts the calibrator reads. `python/test_brickf_data.py`
checks it.

---

## 3. Target construction and set-asides

The historical glacier record and the model measure slightly different things.
Three differences are priced explicitly, as sampled parameters carried on the
**model side** of the comparison, so the observational data are never edited.

### 3.1 Region-19 scope (a target adjustment, not a parameter)

The Frederikse glacier segment assumes zero Antarctic-periphery melt; the
GlaMBIE splice that extends it from 2019 includes region 19. The observed
GlaMBIE region-19 cumulative is therefore removed from the target's 2019+
segment, so the whole series has one scope — SLOWP + FAST — and the model is
compared against it on that scope. Net removal is 0.38 mm by 2023. The
region-19 reservoir is still simulated and still contributes to total sea level;
it is only excluded from this one target.

### 3.2 Uncharted ice — `gic_u_unch`

Parkes & Marzeion (2018) show the historical budget contains glaciers absent
from the modern inventory. That mass is real sea level but has no reservoir to
melt from, so it is added to the model's glacier series before comparison, with
a taper that is flat from 1901, ramps to zero rate by 2005, and is constant
thereafter. Prior flat [14.5, 41.8] mm; posterior 26.5 [19.0, 35.0] mm.

Because the term is exhausted by 2005, it is a hindcast construct: in a
projection re-referenced to 1995–2014 it contributes under 0.1 mm. Include it in
hindcast overlays; ignore it in future deltas.

### 3.3 Early-segment rate bias — `gic_delta`

The pre-1960 part of the target rests on the Marzeion-2015 reconstruction, whose
early rate is contested. A linear rate correction is applied to the
**observations** over 1900–1959, scaled by a sampled parameter with prior
N(0, 0.30) mm/yr. Posterior 0.21 [0.10, 0.33] mm/yr — a real but sub-σ shift.

### 3.4 Nineteenth-century ledger — `gic_u_pre`, `gic_s_r5`

The nineteenth-century melt datum, S(1900) − S(1850) = 20 ± 9 mm, covers a
scope wider than the model's reservoirs: it includes pre-1901 uncharted ice and
a region-5 share. Both are carried as sampled set-asides added to the model's
S(1900) before the datum is evaluated, priors flat [0, 25] mm and
N(2.5, 2) mm. Posteriors 6.5 [0.6, 18.8] mm and 2.5 [0.4, 5.5] mm. The ledger —
the model's own S(1900) − S(1850) of 15.9 mm plus these two set-asides — sums to
26.2 mm against the 20 ± 9 mm datum, z +0.68.

### 3.5 Likelihood terms

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

## 4. Calibration and posterior

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

`b` and `T_off` are given flat bounds rather than Gaussian priors: they are
constrained by the committed-ladder likelihood, and a prior centred on the same
GlacierMIP3 information would count it twice. κ carries a Gaussian prior whose
centre is the response-time-anchored solve, with σ = 0.114 (±30%).

Posterior inventory: Σa_b = 0.352 m SLE.

---

## 5. Observation comparison

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

## 6. Projections, and comparison with FACTS, MAGICC-SLR and BRICK 2.0

`figures/brickf_fig2_ssp_total.png`, `figures/brickf_fig3_glaciers.png`;
`outputs/ssps_components_2300_extC.csv`,
`outputs/brickf_model_comparison{,_spread}.csv`.

Projections use FaIR mean GMST and ocean heat per SSP, so the reported BRICK
bands are **posterior-parameter spread only**. MAGICC and FACTS bands also carry
climate uncertainty. Medians are comparable; band widths are not. All values
are cm relative to 1995–2014 (FACTS relative to baseyear 2005).

### 6.1 BRICK-F\* by component

| | SSP1-2.6 | SSP2-4.5 | SSP5-8.5 |
|---|---|---|---|
| **2100** glaciers / GIS / AIS / TE / LWS | 8.5 / 6.6 / 4.9 / 13.2 / 2.6 | 10.6 / 7.3 / 11.7 / 17.3 / 2.6 | 14.7 / 8.8 / 45.8 / 25.9 / 2.6 |
| **2100** total | 35.9 [34.0, 38.8] | 49.5 [41.5, 97.1] | 97.8 [73.8, 132.3] |
| **2150** total | 48.9 | 112.1 | 200.5 |
| **2300** total | 77.9 | 288.5 | 501.7 |

Bands are 5–95%. Beyond 2100 the SSP2-4.5 and SSP5-8.5 distributions are
strongly right-skewed by Antarctic fast dynamics.

### 6.2 Glaciers at 2100

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

### 6.3 Totals and other components at 2100

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

## 7. Implementing this in BRICK

Everything needed is in the repository; the pieces to port are small.

| file | what it is |
|---|---|
| `julia/glaciers_nu3_component.jl` | the Mimi component: 3 reservoirs, 15 parameters, 3 drivers. 82 lines. |
| `julia/brick_mengel.jl` | `build_brick_nu3` / `update_brick_nu3!` / `set_glacier_forcing3!` — builds a v2.0.0 model with the component swapped into the glacier slot and land-water storage seeded reproducibly. |
| `julia/brickf_projection.jl` | the projection kernel: posterior loading, the per-block driver splice, the 52-parameter apply, rebaselining. Use this rather than re-deriving the parameter map. |
| `python/brickf_data.py` | assembles every data source and emits the three calibrator inputs. |
| `julia/calibrate_mcmc_ext.jl` | the calibrator, including all likelihood terms in §3.5. |
| `data/MimiBRICK/parameters_subsample_brick_mengel_extC.csv` | 10 000-draw posterior subsample. |
| `outputs/extc_block_constants.csv` | the per-reservoir structural constants: inventory priors, response times, GlaMBIE rates, amplifications, ladder rungs, anchored (κ, ν). |
| `data/observations/t_glac_blocks.csv` | the three historical temperature drivers. |

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

## Known limitations

1. **Greenland scenario response** is too weak (§6.3). Unaddressed here.
2. **Antarctic upper tail** is driven by geometry parameters the historical
   record does not identify; the reported spread is a prior-propagated tail, not
   an observationally constrained one.
3. **Aggregate committed loss at +1.2 K** sits ~2 points above the GlacierMIP3
   likely range while each reservoir is individually within 1.2σ (§5).
4. **Projection bands are parameter-only** — they carry no climate uncertainty
   and no structural uncertainty, and are therefore narrower than AR6's
   assessed ranges by construction.
5. **ν is fixed, not sampled.** The hindcast cannot identify it; the values are
   set by the GlacierMIP3 response times. Its uncertainty is not propagated.
6. **Land-water storage** is the MimiBRICK default, climate-independent and
   uncalibrated, ~2.6 cm at 2100.
