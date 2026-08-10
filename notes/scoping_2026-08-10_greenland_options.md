# Scoping: Greenland improvements for BRICK-F\*

2026-08-10. Diagnostic: `python/scope_greenland_options.py` →
`outputs/scope_greenland_options.csv`. Nothing in the model was changed.

---

## 1. What the current module is

Stock SIMPLE (Bakker et al. 2016), unchanged from BRICK 2.0:

```
V_eq(T)  = a·T + b                          equilibrium volume, m SLE   (LINEAR in T)
1/tau(t) = (alpha·T + beta) · V(t)/V0       relaxation rate, 1/yr
V(t)     = V(t-1) + (V_eq - V)/tau
SLE(t)   = V0 - V(t)
```

driven by **global** mean temperature. Posterior medians: a = −0.158 m SLE/°C,
V₀ = 7.35 m, e-folding time 836–1218 yr depending on warming level.

## 2. The diagnosis

The equilibrium sensitivity is fine. **The transient is the bottleneck.**

| | SSP1-2.6 | SSP2-4.5 | SSP5-8.5 |
|---|---|---|---|
| GMST at 2100 | +1.84 °C | +2.74 °C | +4.69 °C |
| committed loss at that temperature | 101 cm | 116 cm | 146 cm |
| e-folding time | 1218 yr | 1062 yr | 836 yr |
| **fraction of the commitment realised by 2100** | **6.5%** | **6.3%** | **6.0%** |

The committed-loss *difference* between SSP1-2.6 and SSP5-8.5 is **44 cm** —
ample. Only ~6% of it is realised by 2100, because the relaxation time is
millennial. That 6% of 44 cm is the +2.2 cm scenario spread we see.

The calibration is not at fault: it is fitting the observed modern rate
(~0.7 mm/yr) correctly, but through the only mechanism SIMPLE offers — a slow
relaxation toward a distant equilibrium. One lumped timescale has to serve both
the fast surface-mass-balance response and the slow dynamic one, and the fit
resolves that by making everything slow.

## 3. Which knobs have leverage

One-at-a-time counterfactuals at the existing posterior, GIS at 2100 in cm
relative to 1995–2014. **These are un-refit**: they show the direction and
leverage of each change, not the number it would land on after recalibration
(the historical constraint would pull the levels back down). What matters here
is the **spread** column.

| variant | SSP1-2.6 | SSP2-4.5 | SSP5-8.5 | spread |
|---|---|---|---|---|
| stock SIMPLE | 6.6 | 7.3 | 8.8 | **+2.2** |
| no V/V₀ damping | 6.7 | 7.4 | 8.9 | +2.2 |
| steeper V_eq ×2 | 8.5 | 9.6 | 12.2 | +3.7 |
| faster response ×3 | 15.9 | 17.5 | 21.5 | +5.6 |
| **regional driver** | 10.8 | 12.5 | 16.7 | **+5.9** |
| faster response ×10 | 27.5 | 31.2 | 40.1 | +12.7 |
| **two channel (30% SMB, τ = 10 yr)** | 11.8 | 15.8 | 24.5 | **+12.7** |
| regional + two channel | 21.2 | 29.9 | 48.6 | +27.4 |

Target spread: **+6.3 cm** (FACTS FittedISMIP), **+7.1 cm** (MAGICC-SLR).

Two knobs are dead ends, and that is worth knowing:

- **The V/V₀ damping is irrelevant this century** (+2.2 → +2.2). Only ~1% of the
  ice sheet is gone by 2100, so V/V₀ ≈ 0.99. It matters for multi-millennial
  runs, not for 2100.
- **Raising the equilibrium sensitivity barely helps** (+2.2 → +3.7 at double
  a). The realised fraction stays ~6%, so doubling the commitment doubles
  almost nothing.

Two knobs have real leverage, and they are the two the glacier work identified
in the same order: **the temperature frame** and **the transient structure**.

## 4. The frame fix is independently supported by the hindcast

Greenland's twentieth century is not global: it warmed ~1.2 °C during the early
warm period (1920–45, against +0.22 °C globally) and then **cooled at
−1.8 °C/century from 1940 to 1990 while the globe warmed +0.4** — precisely the
1942–1982 window where BRICK-F\* misses the target.

Driving SIMPLE with Greenland-region temperature instead of GMST, without
refitting anything:

| driver | melt-rate correlation with the target, 1900–2018 |
|---|---|
| global (stock) | **+0.21** |
| Greenland regional | **+0.77** |

The correlation is the fair statistic here — it is level-invariant, whereas the
absolute bias is not comparable without refitting (feeding a driver twice as
large through parameters calibrated for GMST shifts the level by construction;
the 1942–1982 bias goes −0.82 → −1.13 cm and means nothing until refit).

So one change addresses **both** symptoms: the mid-century hindcast miss and the
weak scenario response. That is the same structure as the glacier case.

Caveat on the driver used: it is the **glacier-area-weighted temperature over
RGI region 5, the Greenland periphery** — the only Greenland-region series
already on disk. It is a margin-weighted proxy, which is arguably the right
frame for ablation, but a proper implementation should build an ice-sheet-mask
weighted series and compare. The amplification (2.04) is also a single-product
HadCRUT5 estimate; the glacier work found the analogous number varied by nearly
2× across temperature products, so it needs the same cross-dataset check.

## 5. Candidate structural changes, ranked

**A. Regional temperature frame** — smallest change, well supported.
Replace the GMST driver with an ice-sheet-region driver plus a sampled
amplification, exactly as the glacier reservoirs do. Requires: an ice-sheet-mask
weighted HadCRUT5 series, a cross-dataset amplification prior, and the
anchor-preserving splice for projections. Buys +2.2 → +5.9 cm of spread and
triples the hindcast rate correlation.

**B. Two channels: surface mass balance and dynamics** — the structural fix.
Split the response into a fast SMB channel (years to a decade) and the existing
slow dynamic relaxation. This is the direct analogue of splitting one glacier
reservoir into three by response time, and it is what lets one model fit both
the modern rate and a century-scale scenario response. Buys the most spread of
any single change (+12.7 cm at a 30% / 10 yr split, i.e. it will need to be
*calibrated down*, not up). Requires an observational constraint on the split —
see §6.

**C. Nonlinear V_eq** — needed for the long horizon, not for 2100.
The linear V_eq gives only 152 cm of committed loss at +5 °C (21% of the ice
sheet), which understates the multi-millennial commitment at high warming.
Since BRICK-F\* is run to 2300 and used for pulse experiments, this is worth
fixing, but it is not what closes the 2100 gap.

**D. Elevation–SMB feedback** — the mechanism behind C, and the reason the
V/V₀ damping has the wrong sign physically (as the ice sheet thins, ablation
should accelerate, not decelerate). Larger job; I would not put it in the first
pass.

My recommendation is **A + B together, calibrated jointly**, with C folded in if
it is cheap. They trade off against each other during the fit — a faster channel
and a larger driver both raise the modern rate — so fitting them separately
would be misleading.

## 6. Data that would be needed, and what is already here

Already on disk: GRACE-FO Greenland mass (2002–2026), IMBIE 2021 Greenland,
Frederikse GIS 1900–2018, GlaMBIE region-5 periphery, HadCRUT5 gridded.

Not on disk, and needed for the analogue of the glacier constraint set:

| need | role | candidate source |
|---|---|---|
| SMB vs discharge partition, multi-decadal | identifies the two-channel split — the single most important new constraint | Mouginot et al. 2019 (PNAS) 1972–2018 partition; Mankoff discharge series |
| process-model intercomparison at 2100 by scenario | the GlacierMIP3 analogue: what the scenario response *should* be | ISMIP6 GrIS (Goelzer et al. 2020; Payne et al. 2021) |
| committed / equilibrium loss at warming levels | anchors V_eq, the analogue of the committed-loss ladder | Box et al. 2022 for present-day disequilibrium commitment; van Breedam et al. 2020 for multi-millennial equilibrium |
| ice-sheet-mask regional temperature | the driver for option A | build from the HadCRUT5 grid already on disk |
| cross-dataset amplification | the prior for A's amplification | Berkeley Earth and GISTEMP grids, already on disk |

**Citation confidence:** I have not re-read Mouginot, Goelzer, Payne, Box or van
Breedam for this note — they are named as the right *kind* of source from
recollection, and the specific values and usability of each need checking before
any of them is used as an anchor. The ISMIP6 and committed-loss items in
particular need someone to confirm a usable ladder exists in the form the
calibrator would want.

## 7. Proposed program

Mirroring the glacier arc, which worked:

1. **Offline cell** — reimplement SIMPLE and the candidate variants outside Mimi
   (already done, `scope_greenland_options.py`), extend it to fit each variant
   against the historical target, and check which variants can satisfy the
   modern rate, the mid-century shape, and an ISMIP6-consistent 2100 response
   *simultaneously*. Pre-register the gates before fitting.
2. **Data acquisition** — the table in §6, with the SMB/discharge partition
   first since it is what makes option B identifiable.
3. **Surgery** — new Mimi component, port-validated against the offline
   reference at 1e-9, exactly as `validate_glaciers_nu3.jl` does.
4. **Joint recalibration** — the whole model again, not Greenland alone.
5. **Re-run** the projections, comparisons and memo through the existing
   pipeline, which is now generic.

## 8. Decisions I need from you before starting

1. **Scope of the first pass**: A alone (cheap, defensible, ~half the needed
   spread), or A + B (the real fix, needs the SMB/discharge data)?
2. **Driver definition**: ice-sheet-mask weighted, margin/ablation-zone
   weighted, or the periphery-glacier weighting already built? These give
   materially different amplifications.
3. **Whether to fix V_eq's functional form** (option C) in the same pass, given
   the 2300 horizon and the pulse experiments.
4. **Whether an ISMIP6-style 2100 constraint enters the likelihood** (as the
   GlacierMIP3 rungs do for glaciers) or stays an evaluation-only gate. For
   glaciers the rungs are in the likelihood; the equivalent choice here decides
   how much the projection target is allowed to shape the fit.
