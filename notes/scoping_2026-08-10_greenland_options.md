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

---

# Decisions taken (Marcus, 2026-08-10)

1. **First pass = A + B together** (regional frame + SMB/dynamics split).
2. **Driver zone**: recommendation below, decided on the two axes Marcus named —
   confidence in each zone's temperature, and which zone drives melt rate.
3. **Options C and D scoped here, excluded from the first pass.**
4. **ISMIP6 is evaluation-only** for now — it does not enter the likelihood.
   (Note the asymmetry this creates against the glacier module, where the
   GlacierMIP3 rungs *are* in the likelihood. It means the Greenland scenario
   response will be judged against ISMIP6 rather than fitted to it, so the first
   pass may land outside it; that is the intended, more conservative choice.)

---

# 9. Driver zone: the evidence

`python/scope_greenland_zones.py` → `outputs/scope_greenland_zones.csv`. Four
land-masked Greenland zones plus the periphery weighting already on disk, built
identically from three independent gridded products, annual and summer.

### Axis 1 — confidence: warming amplification vs global, by product

Early era (1901–1960) / modern (1961–2024). The early era is what matters: it is
where the current module fails and where the products have least in common.

| zone | season | HadCRUT5 | Berkeley Earth | GISTEMP | early spread |
|---|---|---|---|---|---|
| **south** | annual | 3.08 / 1.56 | 2.60 / 1.50 | 3.10 / 1.56 | **1.19×** |
| all | annual | 3.46 / 1.90 | 2.52 / 1.61 | 3.98 / 2.13 | 1.58× |
| central | annual | 3.93 / 2.20 | 2.52 / 1.62 | 5.12 / 2.87 | 2.03× |
| north | annual | 3.94 / 2.46 | 2.38 / 1.80 | 6.62 / 3.78 | 2.78× |
| all | JJA | 2.23 / 1.64 | 1.03 / 1.04 | 1.15 / 1.01 | 2.16× |
| south | JJA | 2.01 / 1.45 | 0.72 / 0.94 | 1.01 / 0.80 | 2.79× |
| central | JJA | 2.58 / 2.05 | 1.19 / 1.08 | 1.34 / 1.31 | 2.16× |
| north | JJA | 2.44 / 1.72 | 1.36 / 1.18 | 1.64 / 1.57 | 1.80× |

Two clear results. **South Greenland is much the best-observed zone** — the
three products agree to 1.19× on its early-era amplification, against 2.0–2.8×
for central and north. And **summer temperature is worse-observed than annual,
not better**: every JJA row has a wider spread than its annual counterpart, with
HadCRUT5 a consistent high outlier (2.0–2.6 against 0.7–1.6 elsewhere).

### Axis 2 — relevance: correlation with the observed melt rate

11-year smoothed, 1900–2018, against the Frederikse GIS target differenced.

| zone | annual | JJA |
|---|---|---|
| south | **0.71** | 0.69 |
| periphery (r05) | **0.71** | — |
| all | 0.69 | 0.67 |
| central | 0.69 | 0.61 |
| north | 0.63 | 0.66 |
| *global mean, for reference* | *0.16* | — |

**This axis does not discriminate.** Every Greenland zone lands between 0.63 and
0.71 on ~11 effectively independent smoothed points; 0.71 versus 0.69 is not a
real difference. What the axis *does* establish, decisively, is that any
Greenland zone beats global mean temperature by a factor of four — which is the
case for option A, not a case for one zone over another.

So the zone choice rests almost entirely on the confidence axis.

### Recommendation

**Annual mean temperature over southern Greenland (59–70 °N), land-masked, with
a sampled amplification.**

- It is the only zone the three products agree on in the early era (1.19×),
  which means the amplification prior can be tight and defensible —
  approximately N(2.9, 0.2) spanning the 2.60–3.10 product range — rather than
  the very wide prior a 2.8× disagreement would force. For comparison, the
  glacier work ended up with N(2.50, 0.45) on [1.80, 3.50] for its worst-observed
  reservoir purely because the products disagreed that much.
- It is as good as anything else on melt-rate relevance, and it is where most
  Greenland ablation happens, so the choice is not merely statistical.
- Carry **whole-ice-sheet annual** as the pre-registered sensitivity arm. Its
  amplification differs enough (3.46 vs 3.08 in HadCRUT5) that the arm is
  informative, and it is the more natural choice if a reviewer objects to a
  regional driver for a whole-ice-sheet module.

**Do not use JJA in the first pass.** It is worse on both axes in anomaly space.
The physical argument for summer temperature is real, but it only bites in a
formulation with absolute temperatures and a melting threshold — positive
degree days — not in an anomaly-driven relaxation model. If the module ever
moves to a PDD formulation, revisit this; as long as the driver is an anomaly,
annual is both better observed and no less relevant.

**Open design question for option B.** The two channels may want different
drivers: surface mass balance responds to melt-season temperature over the
ablation zone, whereas dynamic discharge responds to ocean forcing at marine
termini, which is not a surface air temperature at all. The first pass should
use one driver with a per-channel amplification and treat "does the dynamic
channel need an ocean driver" as the first thing the offline cell tests.

### Caveats

- Zones are land-masked latitude bands over the Greenland box, not an ice-sheet
  or ablation-zone mask. Building a proper mask is worth doing, but the zones
  differ from each other by far more than a mask refinement would move any one
  of them, so it does not change the recommendation.
- The amplifications above are large (2.5–3.9 annual) because they are
  through-origin fits over an era when Greenland warmed much faster than the
  globe and then cooled. They are not a steady Arctic-amplification factor, and
  the projection splice must be anchor-preserving, as the glacier drivers are.

---

# 10. Options C and D — scoped, not in the first pass

### Option C — nonlinear equilibrium volume

**Change.** Replace V_eq = a·T + b with a form that can express near-total loss
at high sustained warming. The obvious candidate is the same saturating form the
glacier reservoirs use, V_eq = V₀ − a(1 − e^(−b(T − T_off))), which is bounded
by the ice sheet's own volume; a threshold form capturing an irreversibility
temperature is the alternative.

**Why it is not in the first pass.** It buys almost nothing at 2100: doubling
the equilibrium sensitivity moves the scenario spread only +2.2 → +3.7 cm,
because the realised fraction of the commitment stays at ~6% whatever the
commitment is. Reshaping the same lever cannot do much better while the
transient is the bottleneck.

**Where it does matter.** The linear form gives only 152 cm of committed loss at
+5 °C — 21% of the ice sheet — which understates the multi-millennial
commitment at high warming. BRICK-F\* is run to 2300 and used for pulse
experiments, so this is a real defect of the long-horizon results, just not of
the 2100 ones.

**What it needs.** An equilibrium-versus-warming ladder for Greenland — the
GlacierMIP3 analogue. This is the piece most likely not to exist in usable form:
the glacier ladder gives committed loss at four warming levels with bands, and
I do not know that an equivalent multi-level GrIS ladder is published. Sources
to check: van Breedam et al. 2020, Bochow et al. 2023, Gregory et al. 2020.
**Not verified — I have not read any of these for this note.**

**Pre-register.** Does 2300 SSP5-8.5 GIS move materially, and does the +1.5 °C
commitment land inside the published range? If the answer to the first is no,
the change is not worth its complexity.

### Option D — elevation–surface-mass-balance feedback

**Change.** Make ablation increase as the ice surface lowers. In a lumped model
that means replacing the V/V₀ term — which currently *slows* the response as ice
is lost — with a term of the opposite sign, or carrying an explicit surface
elevation state.

**Why it is not in the first pass.** Measured, not assumed: dropping the V/V₀
damping entirely changes the 2100 scenario spread by 0.0 cm, because only ~1% of
the ice sheet is gone by 2100 so V/V₀ ≈ 0.99. The feedback cannot matter this
century in a lumped model.

**But flag it as a known defect now.** The V/V₀ term has the wrong sign
physically. It is harmless at 2100 and actively wrong at 2300, where BRICK-F\*
is used, and it will interact with option C: a saturating V_eq plus a damping
term that slows response as ice is lost would double-suppress the long-horizon
commitment.

**What it needs.** Multi-century process-model behaviour to calibrate the
feedback strength; ISMIP6 does not run long enough. Same unverified source list
as C.

**Recommendation.** C and D are the same physics approached from two sides —
both govern the long-horizon commitment — and doing either alone would be
incoherent. Scope them as **one later pass targeted at the 2300 horizon and the
pulse response**, after the first pass has fixed the century-scale behaviour.

---

# 11. Revised first-pass plan

1. **Build the driver**: land-masked southern-Greenland annual series from all
   three products, plus the whole-ice-sheet sensitivity arm, with the
   anchor-preserving splice. Reuses the glacier driver machinery directly.
2. **Acquire the SMB/discharge partition** — the constraint that makes the
   two-channel split identifiable, and the one thing the first pass cannot
   proceed without. Candidate sources in §6, none verified.
3. **Offline cell**: fit stock, A, B and A+B against the historical target with
   pre-registered gates (modern rate, mid-century shape, 1942–1982 window), and
   report the ISMIP6 comparison as an evaluation-only diagnostic.
4. **Surgery + port validation** at 1e-9 against the offline reference.
5. **Joint recalibration** of the whole model, then re-run the existing
   projection, comparison and memo pipeline.

---

# 12. VERIFIED: the SMB / discharge partition

Checked against the primary sources on 2026-08-10 (fetched, not recalled).

### Mankoff et al. 2021, ESSD 13:5001 — 1840 to present

Data: GEUS Dataverse `doi:10.22008/FK2/OHI23Z`, two NetCDF (Zwally sectors,
Mouginot-Rignot regions) and two CSV (daily and annual, ice-sheet-summed).
Annual 1840–1985, daily 1986–present.

**It does not provide an independent partition before 1986, and this matters.**
Per the paper: SMB for 1840–1985 is a semi-empirical regression of in-situ air
temperature onto RACMO2.1 output, calibrated 1960–2012; **discharge for
1840–1985 is "a linear fit between unsmoothed annual discharge spanning 2000 to
2012 and runoff data … using a 6-year trailing average."** Discharge is
observation-based only from 1986, when satellite velocity begins.

So over 1840–1985 the "discharge" channel is by construction a smoothed, lagged
function of the runoff channel. Fitting a two-channel model to that partition
would recover their assumed relationship, not an observed one — and the
temperature-driven SMB reconstruction makes the SMB side close to circular for a
temperature-driven SMB channel too. **Use Mankoff pre-1986 as a total only.**

### Mouginot et al. 2019, PNAS 116:9239 — 1972 to 2018

Reconstructs thickness, elevation, velocity and SMB for 260 glaciers; **85% of
discharge is constrained by measured thickness**, 15% by velocity-scaled
reference fluxes. Cumulative SMB, discharge and mass anomalies are given for
seven regions and the whole ice sheet. This is a genuine observational
partition. (Data location — PNAS supplementary datasets — still to confirm; the
PNAS site blocks automated fetching.)

### Verdict

The partition **exists and is usable, but only from 1972**, not over the
historical window. That is ~50 years against the 126-year fit window, and it is
a period in which both channels accelerated together, which limits how well the
split separates. Consequences for the design:

1. The two-channel split is identified by the modern era alone. Over 1900–1971
   the model is constrained by total mass only, exactly as now.
2. Do not put the Mankoff pre-1986 partition in the likelihood. Its
   discharge is a function of its runoff.
3. Pre-register the separability question: fit the two-channel model to
   1972–2018 partitioned data and check whether the fast fraction and the fast
   timescale are jointly identified, or whether they trade off along a ridge.
   If they ride a ridge, sample the identified combination — the same treatment
   the Antarctic runoff line got with (T_on, c).

---

# 13. Options C and D — upgraded to active, with verified anchors

Marcus asked for these to be pursued because the 2300 response matters. There
is now a verified equilibrium ladder to anchor them.

### Verified anchors

- **Box et al. 2022**, *Nat. Clim. Change* 12:808 — Greenland's imbalance with
  the 2000–2019 climate commits **at least 274 ± 68 mm** of sea-level rise
  (3.3 ± 0.9% of volume) regardless of twenty-first-century pathway. A
  disequilibrium **lower bound** at ~+1.2 °C, not an equilibrium.
- **Bochow et al. 2023**, *Nature* 622:528 — two ice-sheet models run to
  equilibrium. Critical GMT threshold for abrupt loss **1.7–2.3 °C**
  (PISM-dEBM) and ~1.7 °C (Yelmo-REMBO). Stable states: present-day, an
  intermediate at **~75% of present volume**, and ice-free. Below 1.5 °C
  convergence, **< 1 m** long-term contribution; at 2.2 °C convergence,
  **> 20% of present volume** lost. Multistability comes from the
  **melt-elevation feedback** interacting with bedrock uplift. Model output
  open on **Zenodo 10.5281/zenodo.8155423**.
- **Levermann et al. 2013**, *PNAS* 110:13745 — 2000-year commitment ~2.3 m/°C
  total, thermal expansion 0.4 and Antarctica 1.2 m/°C, with glaciers
  saturating and being "overcompensated by the nonlinear response of the
  Greenland Ice Sheet". Per-level Greenland numbers are in the figures; **not
  extracted**.

### How BRICK's linear V_eq scores against them

`python/scope_greenland_commitment.py` → `outputs/scope_greenland_commitment.csv`

| GMT | BRICK committed loss | % of ice sheet | anchor | verdict |
|---|---|---|---|---|
| +1.2 °C | 0.91 m [0.63, 1.32] | 12.3% | Box ≥ 0.274 m | consistent (clears the floor) |
| +1.5 °C | 0.96 m | 13.0% | Bochow < 1 m | consistent |
| +2.2 °C | 1.07 m | 14.5% | Bochow > 1.47 m | **1.4× too low vs a lower bound** |
| +3.0 °C | 1.20 m | 16.3% | Bochow intermediate 1.84 m / ice-free 7.35 m | **1.5× to 6× too low** |
| +5.0 °C | 1.52 m | 20.6% | — | — |

The linear form is **fine where the ice sheet is near-stable and fails
progressively above the published threshold**. It cannot represent a threshold
at all — no curvature means no warming level produces qualitatively different
behaviour.

### What this changes about the design

- **C and D are one job, and the anchor says so.** Bochow's multistability is
  *produced by* the melt-elevation feedback. A single-valued saturating V_eq
  (C alone) can carry the magnitude of the high-warming commitment but cannot
  produce a threshold or hysteresis; that needs the feedback (D) as an explicit
  state-dependence. Doing C alone would fit the anchor's numbers while missing
  the behaviour that generates them.
- **The V/V₀ term must go when D lands.** It damps the response as ice is lost;
  the feedback runs the other way. Keeping both would cancel the mechanism.
- **Two models is not ten.** GlacierMIP3 gives a multi-model band per rung;
  Bochow gives two models that disagree on whether an intermediate state exists
  at all. Any Greenland ladder prior must be correspondingly wide, and the
  PISM-vs-Yelmo disagreement about the intermediate state should be carried as
  a structural arm, not averaged away.

---

# 14. Does the GlacierMIP3 logic transfer to ISMIP6?

Marcus asked whether the reasoning that justified putting GlacierMIP3 in the
likelihood — that it supplies physics we cannot otherwise incorporate — applies
to ISMIP6. **My answer: no for ISMIP6, but yes for the equilibrium ladder, and
that distinction is the useful one.**

**What makes GlacierMIP3 admissible.** It supplies *equilibrium* committed loss
at sustained warming levels. Our own pipeline makes this explicit: the cached
input is `outputs/d1_gmip3_steady_cache.nc` — steady-state runs. No observation
can supply it, because no glacier system has been observed to equilibrate, and
a reduced-form emulator cannot generate it from its own structure. It is
genuinely new information, so it earns a place in the likelihood.

**Why ISMIP6 is different in kind.** ISMIP6 is an intercomparison of *transient
twenty-first-century projections under prescribed forcing* — the same quantity
our model predicts, produced by other models. Putting it in the likelihood
would not add unobtainable physics; it would tune our emulator to other
emulators' transients. FACTS's `FittedISMIP` module already is an ISMIP6
emulator. If we fit to ISMIP6, BRICK-F\*'s Greenland becomes a second-hand
FittedISMIP, and the FACTS and MAGICC comparisons stop being independent checks
— we would be comparing a model to its own training data. **Recommend
evaluation-only permanently, not just for now.**

**But the logic does transfer — to Bochow/Levermann.** Equilibrium states at
sustained warming levels, unobservable, structural, and not derivable from the
model itself: that is the same category as GlacierMIP3, and it is the honest
Greenland analogue. It belongs in the likelihood on exactly the argument that
put the glacier rungs there.

**Consequence, and a decision for you.** The constraint that makes Greenland's
likelihood analogous to the glaciers' is an equilibrium ladder — and an
equilibrium ladder constrains V_eq, which *is* option C. So C is not only "the
2300 fix": it is the carrier of the GlacierMIP3-equivalent information. That is
an argument for pulling C into the first pass rather than a later one, with D
following as the mechanism that makes C's threshold real. **This reverses my
earlier recommendation to defer C, on the strength of the verification.**
Your call whether pass 1 becomes A + B + C, with D as pass 2.

---

# 15. Mouginot data received and ingested (2026-08-10)

Marcus supplied four files in `~/Documents/2026/ClaudeDocs/Papers/Mouginot/`. The
one that matters is **`pnas.1904242116.sd02.xlsx`, sheet `(2) MB_GIS`** — yearly
SMB, discharge and mass balance with errors, by region and for the ice sheet.
`python/build_greenland_partition.py` reads it into
`data/observations/greenland_partition_mouginot2019.csv`.

Sheet layout, for whoever touches it next: a labelled header row (`D`, `SMB`,
`MB`, `MB CUMUL`, …) is followed by eight rows (seven regions + `GIS`); within
each row the values occupy year columns 2–61 and the **errors repeat the same
years** in columns 69–128. Reading it positionally gets errors mixed into
values — the builder keys off the labels and the duplicated year header, and
asserts the published closure MB = SMB − D, which holds to **0.000 Gt/yr**.

Coverage: SMB 1959–2018 (60 yr), discharge and mass balance 1972–2018 (47 yr).

**The number the two-channel split has to reproduce:**

| period | SMB | discharge | mass balance |
|---|---|---|---|
| 1972–1990 | 446.0 | 458.7 | **−12.7** Gt/yr (near balance) |
| 2000–2018 | 283.8 | 517.1 | **−233.3** Gt/yr |
| change | **−162.2** | **+58.4** | −220.6 |

**74% of the additional loss is surface, 26% dynamic.** A two-channel model must
land that split, not just the total — and it is a strong constraint, because the
stock single-channel model has no way to express it.

The 1970s row is also worth noting: SMB 504.8, discharge 458.0, mass balance
**+46.9 Gt/yr** — the ice sheet was *gaining* mass. A model whose only mechanism
is monotone relaxation toward a distant equilibrium cannot produce a gaining
decade, which is the same defect as the 1942–1982 hindcast miss.

---

# 16. The PISM-vs-Yelmo disagreement, and what it means for us

### What the disagreement is

Both models in Bochow et al. 2023 were run to equilibrium at fixed warming
levels. They agree closely on **where** the threshold is — 1.7–2.3 °C
(PISM-dEBM) and ~1.7 °C GMT (Yelmo-REMBO) — and disagree on **what happens past
it**:

- **PISM-dEBM** finds *intermediate stable states* at roughly 50–90% of
  present-day volume. Crossing the threshold does not necessarily lose the ice
  sheet; it can settle part-way.
- **Yelmo-REMBO** finds only two stable states, present-day and near-ice-free.
  Crossing the threshold commits the ice sheet to almost complete loss.

### Why they differ

Per the authors, it is **not** the solid-earth treatment: both use the
Lingle-Clark model with identical parameters, and they note explicitly that the
oscillatory intermediate behaviour is absent from Yelmo despite the same Earth
deformation model.

The difference is in the **surface mass balance scheme and its atmospheric
coupling**. PISM-dEBM uses dEBM-simple, which captures the surface-albedo
feedback but has no dynamic atmosphere. Yelmo-REMBO couples a regional
atmosphere that **increases precipitation as the ice margin retreats** — a
negative feedback that partly offsets the melt-elevation feedback. Differences
in the ice-dynamics formulations contribute as well. The authors' own verdict is
that this is "model-dependent behaviour that is a result of applying different
ice dynamics, climatic forcing and interactions within the system", and they
call for a coordinated intercomparison to constrain it.

The intermediate states in PISM also *oscillate on decamillennial timescales* —
tens of thousands of years — before settling.

### What it means for our model

**It changes how option D should be scoped.** I previously described D as "add
the melt-elevation feedback". That is half the physics. The published
disagreement is precisely about whether that positive feedback is compensated by
a negative precipitation feedback, and the two models bracket the answer. So D
should be implemented as a **net state-dependence with a sampled strength that
can take either sign**, with the two models bracketing the prior — not as a
positive feedback of assumed strength.

**Do not put the intermediate state into the structure.** It is model-dependent,
it oscillates on 10⁴-year timescales, and BRICK-F\* runs to 2300. Representing
a feature that takes tens of millennia to express, in a model that stops after
280 years, buys nothing.

**Quantified: how much does the arm actually matter?**
`python/scope_greenland_commitment.py` runs illustrative PISM-like (graded) and
Yelmo-like (step) equilibrium curves — consistent with the published anchors,
not proposed calibration forms — through the current transient and a ten-times
faster one. Greenland at 2300, cm relative to 1995–2014:

| equilibrium curve | transient | SSP1-2.6 | SSP2-4.5 | SSP5-8.5 |
|---|---|---|---|---|
| linear (current) | current | 18.9 | 25.5 | 50.2 |
| PISM-like graded | current | 28.2 | 58.1 | 167.5 |
| Yelmo-like step | current | 85.7 | 144.3 | 192.9 |
| linear (current) | 10× faster | 47.6 | 67.8 | 134.7 |
| PISM-like graded | 10× faster | 77.5 | 194.6 | 487.6 |
| Yelmo-like step | 10× faster | 309.8 | 476.1 | 526.5 |

Three conclusions, and the first one corrects an expectation I had going in:

1. **At 2300 the equilibrium curve matters on its own, even at the current slow
   transient** — SSP5-8.5 goes 50 → 167–193 cm from the shape of V_eq alone.
   280 years at τ ≈ 800 yr is about a third of an e-folding, enough for a
   multi-metre equilibrium gap to deliver metres. This is the *opposite* of the
   2100 result, where the transient was the whole story. **Option C is not
   contingent on option B at the 2300 horizon**, which is the direct answer to
   why C is worth doing for the reason Marcus gave.
2. **The two models differ from each other far less than either differs from the
   current linear form** — 1.15× apart at SSP5-8.5, against 3.3–3.8× for
   linear-versus-either. Getting off the linear form is first-order; the
   PISM-versus-Yelmo choice is second-order. Do not let the disagreement delay
   the change.
3. **The exception is low warming, and it is the one that matters for policy.**
   At SSP1-2.6 the arm is decisive — 28 cm (PISM-like) versus 86 cm
   (Yelmo-like), a factor of three — because SSP1-2.6 peaks at +1.84 °C, right
   on the 1.7 °C threshold. A step curve crosses it; a graded curve does not.
   So the structural arm must be carried through to the reported results
   specifically at low warming, and the memo should show both. Averaging the
   two arms would hide exactly the question a reader cares about: whether
   BRICK-F\* thinks SSP1-2.6 commits Greenland.

### Consequences for the plan

- Carry PISM-like and Yelmo-like as a **reported structural arm**, not a prior to
  average over, and report both at low warming.
- Sample the **threshold location** under a prior spanning 1.7–2.3 °C — the one
  thing the two models agree on and the parameter the results are most sensitive
  to at low warming.
- Implement D as a **signed** net state-dependence, bracketed by the two models.
- Retire the V/V₀ damping when D lands; it runs opposite to the mechanism.
- Pre-register: does the reported 2300 SSP1-2.6 result change qualitatively
  between arms? If it does — and on these numbers it will — that is a headline
  result of the Greenland work, not a caveat to bury.
