# The GMST→Antarctic temperature map in BRICK-FM: a CMIP6-based update

*Marcus Sarofim / 2026-07-22. Prepared as a discussion note. Scripts, reduced data, and
figures are committed on `SLR-RFF-BRICK @ brick-mengel-vnext`
(`python/diag_pai_cmip6_time.py`, `diag_pai_deck.py`, `diag_pai_ohc.py`,
`diag_pai_denominator.py`, `diag_pai_mask_sensitivity.py`; outputs
`outputs/diag_pai_*.{png,csv,_summary.md}`).*

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
(1961–1990) T_a = −18 °C. So T_a is **continent-averaged (ice-sheet / land-only), not an
average over all grid cells south of 60°S** — and the "reduced to sea level" step is a
fixed lapse-rate offset that cancels in anomalies. The like-for-like CMIP6 quantity is
therefore the **land-only** Antarctic surface air temperature (`tas` over cells with land
fraction ≥ 50% south of 60°S); its 1850–1900 mean of −33.9 °C reproduces Shaffer's −18 °C
anchor once the ~16 K sea-level reduction (mean surface elevation ~2.2 km × ~7 K/km lapse)
is applied. All numbers below are reported in this land frame.[^frame]

[^frame]: The frame matters at the 0.15–0.2 level, because an all-cells (land + ocean)
average south of 60°S folds in the delayed-warming Southern Ocean. That all-cells average
also happens to sit at −17.7 °C at the surface — near −18 by coincidence, not because it
is the right quantity. It is, however, what Xie et al. 2022 (Sci Rep 12:16548) appear to
use: their reported trend-ratio "PAI1" of 0.95 (SSP2-4.5) / 1.03 (SSP5-8.5) is reproduced
by the all-cells south-of-60°S average (0.92/0.98 on a 6-model test; bounded at the
Antarctic Circle, 66.5°S, it gives 1.03/1.12), and converts to ≈1.09/1.16 in the land
frame (full 34-model land-frame trend ratio 1.13/1.16).

## 3. What CMIP6 says `a` is

We compute the quantity `a` is: the **Antarctic amplification ratio** — Antarctic warming
divided by global warming since pre-industrial, R = ΔT_ant / ΔT_glob, with each ΔT a 30-yr
running mean (anomalies rel. 1850–1900, land-frame AIS, 34 models, historical + ssp245 +
ssp585; `python/diag_pai_cmip6_time.py`). This is a cumulative ratio — the "secant" slope
that `a` represents — *not* the trend-ratio PAI1 of §2. Years before 1950 are dropped: the
denominator is then too small and R is internal-variability noise, and even 1950–~2000
is loose.[^denom]

**Result (Figure 1).** Once ΔT_glob passes ~1.5 K the ratio settles to **≈1.05–1.11 and
stays nearly flat across 2–5 K** (multi-model median; ssp245 and ssp585 collapse onto one
curve). It sits **below the 1.196 equilibrium slope** — a century-scale ramp has not
equilibrated — but well above the 0.95 used in the phase-2 prior. Because it is a
cumulative ratio it reads off directly as `a`: at the crossing-relevant warming (ΔT_glob ≈
2.5–3.5 K, where the DAIS thresholds fall) the value is **≈1.06–1.10**.

| ΔT_glob (K) | ratio, SSP2-4.5 | ratio, SSP5-8.5 |
|---|---|---|
| 1.5 | 1.15 | 1.10 |
| 2.0 | 1.11 | 1.08 |
| 2.5 | 1.09 | 1.08 |
| 3.0 | 1.07 | 1.10 |
| 3.5 | 1.06 | 1.11 |

[^denom]: The pre-2000 excursion is a small-denominator artifact with a clear aerosol
signature (`python/diag_pai_denominator.py`). Mid-century NH sulfate aerosols suppressed
the *global* mean — at 1980 the global-mean warming (0.31 K) sits below the
Southern-Hemisphere mean (0.35 K) — inflating the global-referenced ratio to a ~1.7 peak
around 1980 that then relaxes as aerosols are cleaned up. Referencing Antarctic warming to
the SH mean instead halves the inter-model spread (IQR 0.97 → 0.46 at 1980) and removes the
peak, confirming the noise is in the denominator; it does not touch the post-2000 value
used for `a`. (The SH-referenced ratio is not itself usable for `a`, which BRICK defines
against the global mean; it settles higher, ~1.39, because the SH warms less than the
globe.)

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

- Within abrupt-4xCO2 — pure time at ~fixed forcing — the amplification ratio climbs from
  ~0.95 to ~1.2 over the first century and **asymptotes at 1.23 [IQR 1.11–1.45],
  i.e. at the DAIS equilibrium slope** (the two models with 300-yr runs continue to
  ~1.39, hinting the true equilibrium may sit somewhat higher).
- A Gregory-style decomposition gives a **fast-mode amplification of 1.08** (years
  1–20) and a **slow-mode amplification of 1.70** (years 21–150): the deep
  Southern-Ocean adjustment mode is strongly polar-amplified, which is *why* the
  ratio grows with forcing age. Nearly every model sits above the 1:1 line.

**Implications.**

- A **constant ratio** (proposal 5A) is an effective closure for century-scale ramps:
  because level and forcing age co-vary along a ramp, one number captures the ramp's
  cumulative amplification — which is exactly why the scenario ratio (§3) is flat, and
  why it is adequate for scenario-driven projections through ~2150.
- It will **understate amplification under stabilization**, where the ratio keeps
  rising toward ~1.2 while ΔT stalls — relevant to post-2100 extensions and long-horizon
  pulse metrics.
- The GHG-only 1pctCO2 ratio at 2.5–3.5 K (1.07–1.13) **agrees with the scenario ratio
  of §3 (1.06–1.10)**: the aerosol/ozone suppression in realistic trajectories leaves
  little imprint on the *cumulative* (level) ratio — it depresses the transient trend
  ratio, not the cumulative one. Both give `a` ≈ 1.08.
- The structurally honest generalization drives T_ant from a **fast (GMST) and a slow
  (ocean heat content)** component rather than from warming level alone — the slow mode is
  the strongly-amplified Southern-Ocean adjustment, and OHC tracks it (proposal 5B).

## 5. The two proposals

**A. Constant (cheap; a prior swap only): `a ~ N(1.08, 0.15)`.**
Center = the direct amplification ratio at crossing-relevant warming (1.06–1.10 over
2.5–3.5 K, §3), corroborated by the DECK 1pctCO2 GHG-only ratio (1.07–1.13, §4). Because
the ratio is nearly flat across 2–5 K, a single constant is adequate for scenario-driven
projections.
Width = inter-model spread plus method systematics; at σ = 0.15 the equilibrium 1.196
sits ~0.7σ above center, so it stays admissible. Since the observations don't identify `a`,
the posterior tracks whatever prior is chosen — treat it as a considered model input, not
something the calibration will correct.

**B. Beyond ramps: add ocean heat content (structural; needs recalibration).**
The DECK test shows the ratio is not fixed — at constant forcing it climbs from ~0.95
toward the equilibrium ~1.2 over a century (§4). For applications that leave the ramp
regime (post-2100 stabilization, overshoot, paleo), the map needs that time information,
and **ocean heat content carries it**: OHC is the time-integral of forcing, is already a
BRICK input (for thermal expansion), and — tested across the DECK runs (Figure 3,
`python/diag_pai_ohc.py`; proxy = thermosteric SLR `zostoga`) — explains the Antarctic
warming that GMST leaves behind (positive partial correlation in all 17 models, median
0.46; a GMST + OHC map transfers between forcing pathways with ~**40% less error** than
GMST alone, 0.98 → 0.61 K). So

> **T_ant − T_ant,PI ≈ α·ΔGMST + β·ΔOHC**

reduces to proposal A along a ramp and rises toward the equilibrium slope as OHC
accumulates — which a warming-*level* function cannot do. The effect is second-order to
GMST (within-scenario skill barely moves), so it earns its keep for long-horizon use, not
ramp projections.

## 6. Caveats

- The amplification ratio below ΔT_glob ~1.5 K is small-denominator noise (§3 footnote);
  the reliable range is ΔT_glob > 1.5 K (post-~2000), which covers the crossing-relevant
  warming.
- One member per model; a few non-r1i1p1f1.
- sftlf treats ice shelves inconsistently across models, and "land south of 60°S" is a
  proxy for the ice sheet. The attribution of Xie et al.'s values to an all-cells
  (land + ocean) average is inference from numerical reproduction (their methods do not
  state the mask).
- The sea-level reduction in Shaffer's T_a is treated as a constant offset; CMIP6 surface
  `tas` trends over the ice sheet include any lapse-rate/inversion changes, which the
  reduced-to-sea-level quantity would partly remove.
- Proposal 5B's (α, β) are illustrative: the OHC test uses `zostoga` as the proxy,
  rebaselined to each model's piControl mean without drift removal, over the 17 models that
  report it; a production version would refit jointly. DECK anomalies are likewise
  piControl-relative (second-order for multi-K ratios); the abrupt-4xCO2 asymptote beyond
  year 150 rests on two models.
- The DECK matched-warming result (Fig. 2 centre) is robust over **2.5–4.5 K** — the range
  the quoted D values cover. The curves cross beyond ~5 K, but that is the sparse tail where
  only the highest-sensitivity models reach those levels and the two runs no longer sample
  the same models (n falls from ~40 to ~15); it is not a clean physical reversal.

## 7. Remaining questions

1. **Regression provenance:** which reconstruction pair (and anomaly convention) produced
   the 0.8365/−15.42 GMST→T_a relation in the BRICK coupling layer — and is its Antarctic
   variable the same sea-level-reduced, continent-averaged T_a as Shaffer (2014)? §2's
   frame determination assumes it is.
2. **Structure:** does anything downstream of the temperature map — the runoff-line
   parameterization in particular — assume linearity of T_ant in ΔT_glob in a way that the
   GMST + OHC map (proposal 5B) would violate?
3. **Prior width:** does σ = 0.15 appropriately span the structural uncertainty for
   proposal 5A, given that the posterior will track the prior?
