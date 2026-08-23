# The Ladrillo Greenland module

Companion to `notes/memo_2026-08-10_brickf_sharing.md`, whose closing line is
"Greenland is the next module." This is that module.

**Status 2026-08-23.** Shipped and gated. Posterior **L14** (canonical since
2026-08-20). Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, through `44e18bf`.

> **DRAFT — MARCUS DRAFTS THE PROSE.** Sections marked ✎ are placeholders: the
> framing, the argument, and the sharing/《what this is for》narrative are yours.
> Everything else — structure, parameters, numbers, tables, provenance, caveats —
> is populated and each number is quoted from the file named beside it.

---

## ✎ 1. What this is and why it exists

*[Placeholder — Marcus. The GSIC memo's §1 is the model for length and register.]*

---

## 2. What the module is

**`greenland_3basin`, run in its two-basin configuration** (`julia/greenland_3basin_component.jl`),
replacing MimiBRICK v2.0.0's stock SIMPLE Greenland.

### 2.1 Structure

Two-channel relaxation ("A+B") toward a shared equilibrium commitment, carried on
**Mouginot 2019 sector groups**:

| basin | sectors | volume share `k` |
|---|---|---|
| active (carried in the `south` slot) | SW + CW + CE + SE + **NW** | **0.628571** |
| high | NO + NE | **0.371429** |

`k` is **fixed geometry, never sampled**, derived once from the Mouginot Dataset S2
sector volumes (south 3.35 / mid 1.27 / high 2.73 m SLE) so a revision of the
inventory propagates to the calibrator and the component together.

Each basin's commitment is `k_b` × the whole-sheet commitment
`L_eq = clamp(c1·T + c0, 0, v0)`, split by `gis_f` into a fast (surface-mass-balance)
and a slow (dynamic) channel, each relaxing at its own rate. Its one free knob is a
rate scale `s_b` multiplying both channel rates.

Two properties are gated rather than asserted (`julia/test_greenland_3basin_nesting.jl`):

* **Nesting** — at `k = (1,0,0)`, `s = 1` the component reproduces `greenland_ab`
  to `4.4e-16` m.
* **Exact partition** — the clamp is applied per basin over `[0, k_b·v0]`, so
  `eq_b ≡ k_b · eq_whole` identically, saturated or not, and the basins sum to the
  whole sheet always. Clamping each basin to the *whole-sheet* `v0` instead (the
  prototype's form) agrees over the hindcast and breaks additivity beyond it.

### 2.2 Drivers, and the external interface

All basins read the **same** southern-Greenland regional temperature. Geometry lives
entirely in the likelihood, not in the drivers — Marcus 2026-08-18. Stated cost, on
the record: a single amplification assumes the basin temperature *ratios* stay fixed,
and they do not (north amp 2.83 vs south 1.92).

The regional driver is **observed** southern-Greenland T for every year of the
observational record, and only after it splices `amp_draw × S(ΔT) × GMST`. The
external interface stays **GMST + OHC only** — Ladrillo remains a drop-in.

**Consequence that matters throughout this memo: the amplification law is exactly
hindcast-inert.** Nothing about it is constrained by, or can perturb, the calibration.

### 2.3 Sampled parameters — L14 posterior, 10 000 draws

Median [p05, p95] on the **applied** scale
(`data/MimiBRICK/parameters_subsample_brick_mengel_L14.csv`):

| parameter | median | [p05, p95] | units |
|---|---|---|---|
| `gis_c1` equilibrium sensitivity | 0.0460 | [0.0345, 0.0686] | m SLE / K |
| `gis_c0` commitment at zero anomaly | 0.0608 | [0.0454, 0.1070] | m SLE |
| `gis_f` fast share | 0.5505 | [0.3209, 0.7275] | – |
| `gis_alpha_f` fast rate | 0.0048 | [0.0016, 0.0100] | 1/yr/K |
| `gis_beta_f` fast rate at zero | 0.0096 | [0.0042, 0.0154] | 1/yr |
| `gis_alpha_s` slow rate *(derived)* | 0.00143 | [0.00020, 0.00429] | 1/yr/K |
| `gis_beta_s` slow rate at zero *(derived)* | 0.00262 | [0.00020, 0.00717] | 1/yr |
| `gis_amp` regional amplification | 1.9081 | [1.5688, 2.2315] | – |
| `gis_s_high` high-basin rate scale | 0.2264 | [0.1362, 0.3697] | – |

The slow channel is **sampled as `(gis_slow_ell, gis_slow_w)`** — `r_s = exp(ell)`,
`alpha_s = w·r_s/T̄`, `beta_s = (1−w)·r_s`, `T̄ = 1.9631 K` — not in native
coordinates. `gis_s_high` is sampled as **log₁₀**. Both facts matter for anything
that summarises the block; see §4.

**Fixed, not sampled:** the basin shares `k`, `gis_v0 = 7.42 m` SLE,
`gis_g` (realised fraction of the 1850 commitment), and the channel-ordering wedge
in the log-prior (`julia/test_gis_ordering_wedge.jl`, 11 mutation checks).

---

## 3. What is calibrated and what is a prior

This distinction is load-bearing and should survive into any methods text.

| | how it is set |
|---|---|
| the nine parameters above | **calibrated**, 4 × 2M MCMC, seeds 2026–2029 |
| `k`, `v0`, `g`, the ordering wedge | **fixed structure** |
| the amplification law `S(ΔT)` | **prior, projection-side.** Exactly hindcast-inert |
| **the volume tap** (§6) | **prior specification, NOT a fit.** Exactly likelihood-inert: the onset is 4.69 K against a calibration topping out at 1.385 K |

**Neither prior-side object required a chain re-run, and neither can be "fitted"
after the fact without a recalibration** — a separate and much larger decision than
either implies.

---

## 4. Convergence — `outputs/mcmc/gis_block_convergence_L14.csv`

4 × 1M post-burn, R̂ threshold 1.05. Produced **2026-08-23**; before that the only
Greenland certificate on disk was L10, i.e. the whole-sheet `greenland_ab` model
that L14 superseded.

| parameter | scale | R̂ | ESS | median spread |
|---|---|---|---|---|
| `gis_c1` | linear | 1.032 | 99 | 1.078× |
| `gis_c0` | linear | **1.058** | 67 | 1.132× |
| `gis_f` | linear | **1.075** | 52 | 1.137× |
| `gis_alpha_f` | linear | 1.007 | 897 | 1.087× |
| `gis_beta_f` | linear | 1.011 | 672 | 1.078× |
| `gis_slow_ell` | log | **1.055** | 67 | 1.296× |
| `gis_slow_w` | linear | 1.005 | 1598 | 1.066× |
| `gis_amp` | linear | 1.003 | 3010 | 1.014× |
| `gis_s_high` | log₁₀ | **1.001** | **5796** | 1.027× |

**3 of 9 fail, all marginally.** Against Ladrillo 1.0's Greenland: 4 of 8 failed,
worst R̂ **1.335**, and the slow-channel chain medians spanned **2.8×**. The
reparameterisation fixed it — `gis_slow_w` mixes at ESS 1598 where `gis_alpha_s`
managed 34 — and the sampled basin knob the restructure added is the
**best-mixed parameter in the block**.

> ⚠ **The median-spread column is on each parameter's NATIVE scale.** `max/min` of
> the sampled values is not a spread statistic for `gis_slow_ell` or `gis_s_high`:
> both are log-sampled and negative throughout their support, where the ratio is < 1
> and *shrinks* as the spread grows. Read the `scale` column with the number.

> ⚠ **This does NOT lift the projections-only rule.** That rule is set by the
> **AIS geometry** marginals (`ais_iceflow0` R̂ 2.449), not by Greenland, and it is
> unchanged: L14 may be used for projected SLR and anything derived from it, and
> **not** for parameter-level inference.

---

## 5. Performance

### 5.1 Against observations — `julia/diag_gis_cell_vs_priority_ladder.jl`, 295 draws/arm

Four arms through one pipeline — same setup, forcing, baseline and obs file; only the
Greenland module differs. `:stock` SIMPLE on the extC posterior **is** original BRICK,
calibrated in our own pipeline.

| quantity | original BRICK | **Ladrillo L14** | target |
|---|---|---|---|
| calibration-window total | 0.989× | 0.992× | *fitted — not evidence* |
| rate 1900–1950 | 0.732× | **0.995×** | 0.554 mm/yr |
| rate 1950–1990 | 1.492× | **0.950×** | 0.294 mm/yr |
| rate 1993–2010 | 1.050× | **0.997×** | 0.497 mm/yr |
| rate 2010–2024 | 0.876× | **1.020×** | 0.680 mm/yr |
| rate 1995–2024 | **0.946×** | 1.060× | 0.593 mm/yr |
| years inside the obs band | 39/126 | **105/126** | 126 |
| worst miss | 0.161 cm | **0.077 cm** | 0 |
| acceleration 1993–2024 | 0.320× | **0.633×** | 0.0146 mm/yr² |
| volume `v0` | 0.981× | 0.991× | 7.49 m |

**Ladrillo wins historical shape, level, and acceleration; BRICK wins the single
1995–2024 rate** (0.946× vs 1.060×, marginal). The tap changes **none** of these —
every hindcast row is identical across the tapped and untapped arms, `0.000e+00`.

> ⚠ The obs band's half-width collapses **65×** across the record (1.068 → 0.016 cm),
> so "years in band" is dominated by the satellite era. The absolute worst miss is
> printed beside it for that reason.

**The recent-end defect is CURVATURE, not level or rate.** We match the level
(fitted), match the rate over four free windows (0.95–1.06×), and under-run the
acceleration at 0.63×.

### 5.2 Hindcast coverage — `outputs/postpred_L14_*`, 2000 draws

| component | years | parameter-only | predictive | mean bias |
|---|---|---|---|---|
| gis | 126 | 63.5% | 99.2% | +0.00 cm |
| glaciers | 124 | 79.8% | 100.0% | +0.01 cm |
| ais | 126 | 85.7% | 98.4% | −0.00 cm |
| te | 126 | 30.2% | 96.8% | +0.18 cm |
| total | 125 | 30.4% | — | +0.65 cm |

The total is **out-of-sample**: D1 dropped the Dangendorf total from the likelihood,
so it has no fitted error model and no predictive band. Arm-independent throughout.

### 5.3 Projections — `outputs/ssps_components_2300_L14_tap4p69K_V5p64m_tau800_n2_ws.csv`

Greenland median, cm rel. 1995–2014, 2000 draws, FaIR-mean forcing:

| | SSP1-2.6 | SSP2-4.5 | SSP5-8.5 |
|---|---|---|---|
| 2100 | 6.48 | 8.46 | 13.90 |
| 2150 | 7.92 | 12.43 | 30.60 |
| 2300 | 10.08 | 18.32 | **95.74** |

Anything quoting Greenland from the **priority ladder** instead (§5.1) will differ in
the second decimal — that runs 295 draws, this file 2000. Say which.

Bands elsewhere in the deliverable are **posterior-parameter spread on mean forcing
only** — no climate spread. Say so wherever they meet FACTS workflows, which include it.

### 5.4 Between-scenario separation at 2300

The quantity the tap exists to buy, against the **forcing-matched p50 ratio** — *not*
the endpoint-division "band" this repo quoted for months, which was an artefact:

| arm | 585/245 | 585/126 |
|---|---|---|
| original BRICK | 1.90× (0.30) | 2.56× (0.29) |
| Ladrillo, untapped | 2.72× (0.42) | 4.95× (0.56) |
| **Ladrillo, shipped** | **5.22× (0.82)** | **9.49× (1.07)** |
| *target* | *6.40×* | *8.87×* |

Per scenario, ssp585 lands at 0.97× the matched p50 while ssp126 is 0.90× and
ssp245 1.19× — **the cool arms carry the residual, and the tap is inert there by
construction.**

---

## 6. The volume tap

**`GIS_TAP_CELL = (onset 4.69 K, V 5.64 m, τ 800 yr, ramp 1.0 K, stages 2, whole-sheet)`.**
A discharge reservoir opening above a **global** temperature onset: a two-stage unit
cascade relaxes toward a soft ramp in GMT, releasing `V·S₂` of extra loss.

**On by default since 2026-08-23** — it is part of the module; `--no-tap` produces
the base arm.

### 6.1 Why the form is a cascade

The joint constraint is ≤ 8.1 cm added at 2150 on the ssp585 x2300 arm and 48.6 cm
needed at 2300 — a delivery ratio **R = 6.03**. A reservoir's response to its ramp is
an n-fold repeated integral, so in the long-τ limit n=1 gives **2.82**, n=2 **7.86**,
n=3 **21.71**; swept over onsets 1.6–7.5 K, n=1 peaks at 2.89. **No first-order cell
can do it**, and the same exact bound refutes every completely monotone family
(ladder, Prony, stretched-exponential, Mittag-Leffler, power-law). A cascade is not
completely monotone, so the bound does not reach it.

### 6.2 Why V = 5.64

Two criteria **700 years apart** agree to within 1%: it is the largest V clearing the
2250–2300 melt-rate band solved in the wired component (5.66 offline, 5.64 wired), and
it puts Greve/SICOPOLIS at year 3001 at **0.990×**. It is also the minimum of the
weighted score under 2100 > 2300 > 3001, and within 0.1% of the minimum under every
other weight set.

### 6.3 What switching it on does and does not move

Measured on the shipped files, tapped minus untapped:

| | SSP1-2.6 | SSP2-4.5 | SSP5-8.5 |
|---|---|---|---|
| every year ≤ 2100 | 0.000 | 0.000 | **0.000** |
| 2150 | 0.000 | 0.000 | +2.420 |
| 2300 | 0.000 | 0.000 | **+45.779** |

`max |tapped − untapped|` over **all** rows at year ≤ 2100 is `0.000e+00`; likewise
for both cool scenarios at **all** years. The whole calibration record is unmoved by
construction. Gated at `julia/test_gis_tap_wiring.jl`, including three mutations that
must break the gates and do.

**So the tap improves agreement with multi-century ice-sheet-model commitment
evidence and with scenario separation. It improves nothing scored against
observations, and it cannot: it is inert everywhere observations exist.**

---

## 7. Caveats — carry these into any report

1. **Projections only, not parameter-level inference** (§4). Set by AIS, not Greenland.
2. **The cell-choice envelope is UNQUANTIFIED for the cascade.** Its first-order
   predecessor was **1.180 m at Greenland 2300 — 4.4× the sampled p05–p95** and the
   larger of the two uncertainties. Never quote the superseded envelope against the
   shipped cell. This is the largest single gap in the module.
3. **The shipped cell sits ON the melt-rate ceiling, not inside it** — V was solved
   *as* the clearing value, so the verdict turns on the third significant figure
   (41.4 offline vs 41.5 wired against a 41.5 top). The two artifacts on disk
   therefore label it differently — `diag_gis_cascade_rate_crit.csv` says it passes,
   the priority ladder prints "OUT (too FAST)" — and the ladder says why immediately
   below. **Report it as ON the boundary; quote neither verdict alone.** There is no
   interior solution: untapped is 4.5× too slow, shipped is at the ceiling.
4. **2100 runs 1.37× fast, and the defect is the DRIVER, not the ice.** Driven by each
   GCM's own Greenland temperature the response lands on the ISMIP6 median (**0.99×**,
   n = 5, spread 0.65–1.33); through our amplification law it overshoots **1.31×**.
   Effective amp 1.58–1.63 against those models' own south-zone 1.08–1.39. Because the
   law is hindcast-inert, a correction is prior-propagatable rather than a refit.
   **This is the highest-value open item in the module.** No onset and no cell fixes it.
5. **The cool arms carry the residual separation error** (§5.4), and the reservoir
   cannot reach them.
6. **`gis_beta_f` is unidentified and consequential** — the data bound it only to
   < ~1e-2/yr. Part of the Greenland band width is prior width.
7. **The 2150 evidence is genuinely contradictory**: NORCE-CISM on hot x2300 forcing
   says adding mass by 2150 pushes us out the top; SICOPOLIS on ssp585 GCM forcing
   reads 0.61–0.89×, i.e. we are low. Both like-for-like in forcing. The cell sits
   inside both bands, which is why it does not block.
8. **The x2300 arm is unreachable and always was** — 58.3 cm against a 122.8–189.0
   band, band-independent. Reported, not a blocker.
9. **The moderate-scenario per-tonne SC-GHG commitment term is exactly ZERO** at this
   onset. A nonzero term needs a second, separately justified arm — not a change to
   this cell.
10. **Every 2300+ target rests on few models**, and most on one: every matched anchor
    past 2100 is NORCE-CISM. Stringency scales with model count — these are guidance,
    not fit objectives.

---

## 8. Files and reproduction

| role | file |
|---|---|
| component | `julia/greenland_3basin_component.jl` |
| projection kernel | `julia/ladrillo_projection.jl` |
| calibrator | `julia/calibrate_mcmc_ext.jl --gis-ordered --gis-basins2` |
| posterior | `data/MimiBRICK/parameters_subsample_brick_mengel_L14.csv` |
| convergence certificate | `outputs/mcmc/gis_block_convergence_L14.csv` |
| SSP deliverable (tapped) | `outputs/ssps_components_2300_L14_tap4p69K_V5p64m_tau800_n2_ws.csv` |
| SSP deliverable (base arm) | `outputs/ssps_components_2300_L14.csv` |
| hindcast | `outputs/postpred_L14_{components_timeseries,bias,coverage}.csv` |
| comparison vs FACTS/MAGICC/BRICK | `outputs/ladrillo_model_comparison_L14{,_spread}.csv` |
| figures | `figures/ladrillo_L14_fig{1,2,3}_*.png` |
| priority-ladder scorecard | `julia/diag_gis_cell_vs_priority_ladder.jl` |
| 2100 bias decomposition | `python/diag_gis_2100_bias_decomp.py` |
| the tap cell, in python | `gis_targets.tap_cell()` — parses the Julia constant |

```bash
./run_ladrillo_tests.sh                 # 10 steps; 8-10 gate this module
```

```bash
TAG=L14
julia --project=julia_v2 julia/project_ssps_components_ladrillo.jl 2000 --tag=$TAG
julia --project=julia_v2 julia/project_ssps_components_ladrillo.jl 2000 --tag=$TAG --no-tap
julia --project=julia_v2 julia/posterior_predictive_ladrillo.jl 2000 --tag=$TAG
python3 python/ladrillo_model_comparison.py --tag=$TAG
python3 python/plot_ladrillo_memo_figures.py --tag=$TAG
```

**The arm is in every filename.** A tapped and an untapped 2300 projection differ by
~46 cm on ssp585 and are otherwise identical in shape, units and header; the one thing
that must never be ambiguous is which arm a file on disk is.

---

## ✎ 9. What this is for / what we would ask a reader to check

*[Placeholder — Marcus.]*

---

## 10. Open, in priority order

1. **The amplification law** (caveat 4). Highest value, diagnosed rather than
   suspected, and hindcast-inert so a correction is prior-propagatable.
2. **Quantify the cascade cell-choice envelope** (caveat 2) — currently the largest
   unreported uncertainty on tapped Greenland@2300.
3. **The cool arms' separation residual** (caveat 5).
4. **`LADRILLO.md` still defines the module as `greenland_ab` on posterior L10** and
   lists closed threads as open. It is the last stale description of this module.

**Not Greenland:** at 2300 on ssp585, Greenland is **18.6%** of the total with a
p05–p95 of **26.9 cm**, while **Antarctica is 54.8% with a p05–p95 of 252.3 cm** (and at SSP2-4.5 a
[15.4, 296.1] cm range — a 19× spread, wider than the whole total's). Greenland is now
the smallest-uncertainty ice component in the model. **The leverage is AIS.**
