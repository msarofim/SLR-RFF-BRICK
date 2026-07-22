# The GMST→Antarctic temperature map in BRICK-FM: a CMIP6-based update

*Marcus Sarofim / 2026-07-22. Prepared as a discussion note. Scripts, reduced data, and
figures are committed on `SLR-RFF-BRICK @ brick-mengel-vnext`
(`python/reduce_cmip6_tas_pai.py`, `python/diag_pai_cmip6_time.py`,
`python/diag_pai_mask_sensitivity.py`; outputs `outputs/diag_pai_cmip6_time.*`).*

## 1. Background

DAIS drives its runoff line and fast-dynamics threshold with an Antarctic surface
temperature computed linearly from global temperature each timestep:

> T_ant = T_ant,PI + a · ΔT_glob,  with the classic a = 1/0.8365 ≈ **1.196** and
> T_ant,PI ≈ −18.4 °C (the −15.42/0.8365 regression in the DAIS lineage, Shaffer 2014).

In the BRICK-FM phase-2 recalibration we freed `a` under a CMIP6-*transient* prior
centered at 0.95, on the argument that 1.196 is an equilibrium/paleo number while a
21st-century simulation runs far from equilibrium. The observations do not constrain `a`,
so the posterior tracked the prior — and projected SSP2-4.5 GMSL @2100 moved from 76 to
40 cm (median). The lesson we take from that experiment is simply that **the projection
is highly sensitive to `a`**, which makes it worth pinning down (i) exactly what
temperature `a` references and (ii) what value — or functional form — the CMIP6 transient
archive supports. That is what this note does.

## 2. What `a` references

Shaffer (2014, GMD 7:1803, §2.1 and Table 1) defines the forcing as *"the mean annual air
temperature reduced to sea level and averaged over Antarctica"*, with present-day
(1961–1990) T_a = −18 °C. So T_a is **continent-averaged (ice-sheet/land-only), not a
polar-cap temperature** — and the "reduced to sea level" step is a fixed lapse-rate
offset, which cancels in anomalies and trends. For the amplification `a`, the
like-for-like CMIP6 quantity is therefore the **land-only** Antarctic surface air
temperature (we use `tas` over grid cells with land fraction ≥ 50% south of 60°S).

Two consistency checks from the CMIP6 archive:

- Land-only 1850–1900 absolute mean = −33.9 °C (34-model mean); with the ~16 K sea-level
  reduction (mean surface elevation ~2.2 km × ~7 K/km lapse) this reproduces Shaffer's
  −18 °C anchor.
- The all-points cap south of 60°S happens to average −17.7 °C *at the surface* (the
  ocean warms the mean) — numerically near −18, but it is the wrong quantity; the match
  is coincidental.

The frame matters at the 0.15–0.2 level for amplification ratios, because the cap
includes the delayed-warming Southern Ocean. Concretely: **Xie et al. 2022** (Sci Rep
12:16548) report an annual AIS "PAI1" (trend ratio, 2015–2100) of 0.95 (SSP2-4.5) / 1.03
(SSP5-8.5); those values are reproduced almost exactly by the *cap* mask (6-model test:
0.92/0.98) and are therefore cap-referenced. **Converted to `a`'s land frame, the same
models give ≈ 1.09/1.16**, and the full 34-model land-frame trend ratio is 1.13/1.16.
All numbers below are reported directly in the land frame.

## 3. The diagnostic

34 CMIP6 models (one member each, Amon `tas` streamed from the public Pangeo/GCS mirror),
historical + ssp245 + ssp585; anomalies rel. 1850–1900. We compute a *windowed*
amplification: the 41-yr OLS trend ratio trend(T_AIS)/trend(T_glob), sliding through
1850–2100 (windows with global trend < 0.05 K/decade masked — the ratio is unstable
there).

Findings (figure: `outputs/diag_pai_cmip6_time.png`):

1. **Within-scenario rise.** Median windowed ratio climbs 1.06 → 1.19 through the century
   in SSP2-4.5 (+0.035/decade) and 1.13 → 1.19 in SSP5-8.5.
2. **Collapse on warming level.** Plotted against window-mean ΔT_glob, the two scenarios
   lie on ~one curve: ≈0.9 at 0.7 K, ≈1.1 at 1.5–2 K, flattening at ≈1.15–1.2 by 2–4 K.
   SSP5-8.5 at a given warming level (reached decades earlier) matches SSP2-4.5 at the
   same level — amplification behaves as a function of warming level, not elapsed time or
   forcing mix.
3. **It saturates at the equilibrium value.** Fitting a saturating curve with a free
   asymptote returns ≈1.14; *fixing* the asymptote at 1.196 fits essentially as well
   (RMSE 0.054 vs 0.050). CMIP6's transient Antarctic amplification relaxes toward the
   paleo-equilibrium slope — an independent consistency check of the classic number.

## 4. Testing for a time component: matched warming across scenarios

In the two-scenario collapse test, SSP2-4.5 sat slightly above SSP5-8.5 near 2.5–3 K —
at matched warming, the scenario arriving *later* showed higher amplification, hinting
that the Southern-Ocean deficit might scale with warming **rate** (a genuine time
component) rather than warming level alone. To test this we added ssp119 and ssp126,
spanning warming rates ~0.1–0.5 K/decade. **SSP3-7.0 is excluded as the aerosol
outlier** — its weak-air-quality-policy trajectory changes the Southern-Hemisphere
forcing mix and would confound a rate comparison.

Two probes on the 33-model common subset (`python/diag_pai_cmip6_rate.py`, figure
`outputs/diag_pai_cmip6_rate.png`):

- **Matched-warming medians.** At 2.0 K and 2.5 K the scenarios are flat within ±0.02
  (e.g. 2.5 K: SSP2-4.5 = 1.13 reached ~2059 vs SSP5-8.5 = 1.14 reached ~2051, despite
  rates of 0.27 vs 0.46 K/decade). The original crossover survives only in the single
  3.0 K bin (1.19 vs 1.10) — within window noise.
- **Joint fit** pai = 1.196 − (1.196 − a0)·exp(−ΔT/Ts) − c·rate: **c = −0.64
  [−1.06, +0.07] per (K/decade)** (bootstrap over models) — the CI spans zero, and the
  negative point estimate is an artifact of stabilized-scenario windows, not evidence
  that faster warming *raises* amplification.

The honest limitation: the windowed trend-ratio estimator **degenerates exactly where a
time effect would show most clearly**. As ssp119/ssp126 stabilize, the global trend
falls below ~0.1 K/decade (the ratio explodes) and ozone recovery confounds what
remains; the pre-2005 historical windows are likewise contaminated by the ozone
hole/aerosol era (median Antarctic trends are *negative* under non-GHG forcing). Both
regimes are excluded by explicit filters, which leaves rate leverage only over
0.15–0.5 K/decade — and there, no coherent rate dependence appears.

Conclusion: the level-dependent form (§6) stands as the supported parsimonious model. A
decisive level-vs-time separation needs identical-composition experiments — 1pctCO2 vs
abrupt-4xCO2 (pure rate contrast vs pure time-at-forcing), or a single-model large
ensemble to crush the window noise.

## 5. Level vs marginal slope

The windowed trend ratio is a **marginal** slope, dT_ant/dT_glob, which rises with
warming. But a constant `a` is a **secant (level)** slope anchored at pre-industrial:
T_ant − T_ant,PI = a·ΔT_glob. For what the map actually controls — when T_ant reaches the
runoff/disintegration thresholds — the constant that reproduces the nonlinear truth is
the *level* ratio at the crossing-relevant warming, i.e. the warming-average of the
marginal, which sits well below the late-century marginal.

Integrating the fitted marginal (§6) gives level ratios of ~0.85 at 1 K, **0.95 at 2 K,
1.02 at 3 K** (land frame). For the thresholds the posterior actually holds (T_ant must
rise ~2.3–3.3 K, i.e. crossings at ΔT_glob ≈ 2.5–3.5 K on SSP2-4.5), the
crossing-relevant level ratio is ~**0.97–1.03**.

## 6. The two proposals

**A. Constant (cheap; a prior swap only): `a ~ N(1.00, 0.15)`.**
Center = the land-referenced level ratio at crossing-relevant warming (0.97–1.03 over
2.5–3.5 K). Width = inter-model spread (per-model projection-era ratios: sd 0.20–0.27,
inflated by single-member internal variability) plus the mask/level systematics (~±0.05
each). Since the observations don't identify `a`, the posterior will track whatever prior
is chosen here — the choice should be treated as a considered model input, not something
the calibration will correct.

**B. Simple equation (structural; needs recalibration).** Fit to the pooled 34-model
median collapse curve (ΔT ≥ 0.6 K), asymptote fixed at the equilibrium slope:

> marginal form:  **amp(ΔT) = 1.196 − 0.54·exp(−ΔT/1.05)**
> (0.86 at 0.5 K, 0.99 at 1 K, 1.12 at 2 K, 1.17 at 3 K)

and the map DAIS would implement is its integral — still algebraic, per-timestep, no new
state variable:

> **T_ant = T_ant,PI + 1.196·ΔT_glob − 0.57·(1 − exp(−ΔT_glob/1.05))**

Properties: exactly the equilibrium slope in the high-warming/paleo limit (so the paleo
constraints that produced 0.8365/−15.42 are honored where they apply); transient
suppression at low warming emerges automatically; and it removes the need to choose
between "transient" and "equilibrium" constants at all. Against the CMIP6 median curve it
beats any constant by construction (constant-fit RMSE 0.065 vs 0.054).

| ΔT_glob (K) | marginal amp(ΔT) | level ratio T_ant′/ΔT |
|---|---|---|
| 0.5 | 0.86 | 0.77 |
| 1.0 | 0.99 | 0.85 |
| 2.0 | 1.12 | 0.95 |
| 3.0 | 1.17 | 1.02 |
| 4.0 | 1.18 | 1.06 |

## 7. Caveats

- The ΔT→0 intercept (0.655) is extrapolation: trend ratios are unstable below ~0.6 K of
  global warming, so the first ~0.6 K of the integral leans on the fitted form (shifting
  the intercept to 0.85 moves the 2 K level ratio only ~+0.02).
- One member per model; a few non-r1i1p1f1. Trend ratios pre-~1990 are internal-variability
  noise (masked in the fit).
- sftlf treats ice shelves inconsistently across models, and "land south of 60°S" is a
  proxy for the ice sheet. The attribution of Xie et al.'s values to a cap mask is
  inference from numerical reproduction (their methods do not state the mask).
- The sea-level reduction in Shaffer's T_a is treated as a constant offset; CMIP6 surface
  `tas` trends over the ice sheet include any lapse-rate/inversion changes, which the
  reduced-to-sea-level quantity would partly remove.
- The equation form assumes the marginal depends on warming *level*, not rate — supported
  by the multi-scenario test within its power (§4), but stabilized and overshoot
  trajectories are untestable with this estimator, and paleo trajectories are untested.

## 8. Remaining questions

1. **Regression provenance:** which reconstruction pair (and anomaly convention) produced
   the 0.8365/−15.42 GMST→T_a relation in the BRICK coupling layer — and is its Antarctic
   variable the same sea-level-reduced, continent-averaged T_a as Shaffer (2014)? §2's
   frame determination assumes it is.
2. **Structure:** does anything downstream of the temperature map — the runoff-line
   parameterization in particular — assume linearity of T_ant in ΔT_glob in a way that a
   warming-dependent map (proposal B) would violate?
3. **Prior width:** does σ = 0.15 appropriately span the structural uncertainty for
   proposal A, given that the posterior will track the prior?
