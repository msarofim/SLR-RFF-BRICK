# The GMST→Antarctic temperature map in BRICK-FM: a CMIP6-based update

*Marcus Sarofim / 2026-07-22. Prepared as a discussion note. Scripts, reduced data, and
figures are committed on `SLR-RFF-BRICK @ brick-mengel-vnext`
(`python/reduce_cmip6_tas_pai*.py`, `python/diag_pai_cmip6_time.py`,
`python/diag_pai_mask_sensitivity.py`, `python/diag_pai_deck.py`; outputs
`outputs/diag_pai_cmip6_time.*`, `outputs/diag_pai_deck.*`).*

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
(1961–1990) T_a = −18 °C. So T_a is **continent-averaged (ice-sheet/land-only), not an
average over all grid cells south of 60°S** (which would fold in the Southern Ocean) —
and the "reduced to sea level" step is a fixed lapse-rate
offset, which cancels in anomalies and trends. For the amplification `a`, the
like-for-like CMIP6 quantity is therefore the **land-only** Antarctic surface air
temperature (we use `tas` over grid cells with land fraction ≥ 50% south of 60°S).

Two consistency checks from the CMIP6 archive:

- Land-only 1850–1900 absolute mean = −33.9 °C (34-model mean); with the ~16 K sea-level
  reduction (mean surface elevation ~2.2 km × ~7 K/km lapse) this reproduces Shaffer's
  −18 °C anchor.
- The average over all cells south of 60°S (land + ocean) happens to come out at −17.7 °C
  *at the surface* (the ocean warms the mean) — numerically near −18, but it is the wrong
  quantity; the match is coincidental.

The frame matters at the 0.15–0.2 level for amplification ratios, because the all-cells
average includes the delayed-warming Southern Ocean. Concretely: **Xie et al. 2022** (Sci
Rep 12:16548) report an annual AIS "PAI1" (trend ratio, 2015–2100) of 0.95 (SSP2-4.5) /
1.03 (SSP5-8.5); those values are reproduced almost exactly by the all-cells (land +
ocean) south-of-60°S average (6-model test: 0.92/0.98; the same average bounded at the
Antarctic Circle, 66.5°S, instead gives 1.03/1.12). **Converted to `a`'s land frame, the same
models give ≈ 1.09/1.16**, and the full 34-model land-frame trend ratio is 1.13/1.16.
All numbers below are reported directly in the land frame.

## 3. What CMIP6 says `a` is

We compute the quantity `a` actually is — the **secant (level) ratio**
R(t) = (T_AIS − T_AIS,PI) / (T_glob − T_glob,PI), each temperature a 30-yr running mean,
anomalies relative to 1850–1900, land-frame AIS, 34 models (historical + ssp245 + ssp585;
`python/diag_pai_cmip6_time.py`). This is the cumulative warming-since-preindustrial ratio
— a level ratio, *not* the trend-ratio PAI1 of §2. Years before 1950 are dropped: the
denominator is then too small and R is pure internal-variability noise (even 1950–~2000,
with ΔT_glob < 1 K, is loose).

**Result (Figure 1).** Once ΔT_glob passes ~1.5 K the secant settles to **≈1.05–1.11 and
stays nearly flat across 2–5 K** (multi-model median; ssp245 and ssp585 collapse onto one
curve). It sits **below the 1.196 equilibrium slope** — a century-scale ramp has not
equilibrated — but well above the 0.95 used in the phase-2 prior. Because R is already a
level ratio it reads off directly as `a`: at the crossing-relevant warming (ΔT_glob ≈
2.5–3.5 K, where the DAIS thresholds fall) the value is **≈1.06–1.10**.

| ΔT_glob (K) | secant, SSP2-4.5 | secant, SSP5-8.5 |
|---|---|---|
| 1.5 | 1.15 | 1.10 |
| 2.0 | 1.11 | 1.08 |
| 2.5 | 1.09 | 1.08 |
| 3.0 | 1.07 | 1.10 |
| 3.5 | 1.06 | 1.11 |

The two scenarios coincide at matched warming; §4 shows why a ramp cannot do otherwise
(level and forcing age co-vary along any ramp), and supplies the idealized-run test that
*does* separate them.

## 4. The time component: an idealized-run (DECK) test

Does amplification depend on warming level alone, or also on time-since-forcing? A
scenario ensemble cannot answer this — along every ramp, level and forcing age co-vary,
and cross-SSP contrasts add aerosol/ozone composition differences (a multi-SSP test we
ran was correspondingly inconclusive). The DECK pair separates the axes with GHG-only
forcing: **1pctCO2** sweeps warming level at a sustained rate, while **abrupt-4xCO2**
holds forcing fixed and sweeps time. 41 models, anomalies relative to each model's own
piControl mean, same land-frame AIS metric (`python/diag_pai_deck.py`).

**The time component is real.** The two runs pass through the same warming levels at
very different forcing ages: abrupt-4xCO2 reaches 2.5–4.5 K within ~6–22 years of the
quadrupling, while 1pctCO2 takes ~100–124 years to arrive there. At matched warming the
younger state is systematically **less** amplified — the paired difference
D = R_abrupt − R_1pct runs from **−0.13 [−0.20, −0.03] at 2.5 K to −0.08
[−0.13, −0.03] at 4.5 K**, bootstrap CIs over models excluding zero in every bin.
Complementary views agree:

- Within abrupt-4xCO2 — pure time at ~fixed forcing — the level ratio climbs from
  ~0.95 to ~1.2 over the first century and **asymptotes at 1.23 [IQR 1.11–1.45],
  i.e. at the DAIS equilibrium slope** (the two models with 300-yr runs continue to
  ~1.39, hinting the true equilibrium may sit somewhat higher).
- A Gregory-style decomposition gives a **fast-mode amplification of 1.08** (years
  1–20) and a **slow-mode amplification of 1.70** (years 21–150): the deep
  Southern-Ocean adjustment mode is strongly polar-amplified, which is *why* the
  ratio grows with forcing age. Nearly every model sits above the 1:1 line.

**Implications.**

- A **constant secant** (proposal 5A) is an effective closure for century-scale ramps:
  because level and forcing age co-vary along a ramp, one number captures the ramp's
  cumulative amplification — which is exactly why the scenario secant (§3) is flat, and
  why it is adequate for scenario-driven projections through ~2150.
- It will **understate amplification under stabilization**, where the secant keeps
  rising toward ~1.2 while ΔT stalls — relevant to post-2100 extensions and long-horizon
  pulse metrics.
- The GHG-only 1pctCO2 secant at 2.5–3.5 K (1.07–1.13) **agrees with the scenario secant
  of §3 (1.06–1.10)**: the aerosol/ozone suppression in realistic trajectories leaves
  little imprint on the *cumulative* (level) ratio — it depresses the transient marginal,
  not the secant. Both give `a` ≈ 1.08.
- The structurally honest generalization drives T_ant from **fast and slow thermal
  components** (≈1.08 and ≈1.70 respectively) rather than from warming level; a two-box
  energy-balance driver already carries those states (proposal 5B).

## 5. The two proposals

**A. Constant (cheap; a prior swap only): `a ~ N(1.08, 0.15)`.**
Center = the direct secant at crossing-relevant warming (1.06–1.10 over 2.5–3.5 K, §3),
corroborated by the DECK 1pctCO2 GHG-only secant (1.07–1.13, §4). Because the secant is
nearly flat across 2–5 K, a single constant is adequate for scenario-driven projections.
Width = inter-model spread plus method systematics; at σ = 0.15 the equilibrium 1.196
sits ~0.7σ above center (admitted, not the +2.45σ near-exclusion of the phase-2 0.95
prior). Since the observations don't identify `a`, the posterior tracks whatever prior is
chosen — treat it as a considered model input, not something the calibration will correct.

**B. Beyond ramps: a two-mode map (structural; needs recalibration).**
The DECK test shows the secant is not fixed — at constant forcing it climbs from ~0.95
toward the equilibrium ~1.2 over a century (§4). For applications that leave the ramp
regime — post-2100 stabilization, overshoot, paleo — drive T_ant from the fast and slow
thermal components rather than from ΔT_glob:

> **T_ant − T_ant,PI ≈ 1.08·ΔT_fast + 1.70·ΔT_slow**

with the Gregory fast/slow-mode slopes, where ΔT_fast and ΔT_slow are the two boxes a
standard energy-balance driver already carries (no new state in BRICK). It reduces to
proposal A along a ramp and converges to the equilibrium slope as the slow box fills — a
single warming-*level* function can do neither, since it would misextrapolate under
stabilization (amplification rises while ΔT stalls). Supersedes the earlier marginal-fit
amp(ΔT) equation, which parameterized by level and understated the secant by ~0.1.

## 6. Caveats

- The secant below ΔT_glob ~1.5 K is small-denominator noise; the reliable range is
  ΔT_glob > 1.5 K (post-~2000), which covers the crossing-relevant warming.
- One member per model; a few non-r1i1p1f1.
- sftlf treats ice shelves inconsistently across models, and "land south of 60°S" is a
  proxy for the ice sheet. The attribution of Xie et al.'s values to an all-cells
  (land + ocean) average is inference from numerical reproduction (their methods do not
  state the mask).
- The sea-level reduction in Shaffer's T_a is treated as a constant offset; CMIP6 surface
  `tas` trends over the ice sheet include any lapse-rate/inversion changes, which the
  reduced-to-sea-level quantity would partly remove.
- Proposal B's two-mode slopes are Gregory-window estimates (fast yrs 1–20, slow 21–150)
  from abrupt-4xCO2; a production version would refit them jointly. DECK anomalies are
  relative to each model's piControl mean without drift removal (second-order for
  multi-K ratios); the abrupt-4xCO2 asymptote beyond year 150 rests on two models.

## 7. Remaining questions

1. **Regression provenance:** which reconstruction pair (and anomaly convention) produced
   the 0.8365/−15.42 GMST→T_a relation in the BRICK coupling layer — and is its Antarctic
   variable the same sea-level-reduced, continent-averaged T_a as Shaffer (2014)? §2's
   frame determination assumes it is.
2. **Structure:** does anything downstream of the temperature map — the runoff-line
   parameterization in particular — assume linearity of T_ant in ΔT_glob in a way that the
   two-mode map (proposal 5B) would violate?
3. **Prior width:** does σ = 0.15 appropriately span the structural uncertainty for
   proposal 5A, given that the posterior will track the prior?
