# Addendum to `handoff_2026-08-22_greenland_flux_deliverable.md` — §4.2 discharged, stages 1a/1b run

Written 2026-08-22. Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`.
Commits: `3f920fb` (§4.2), `c087ba2` (stages 1a+1b), `730645d` (CHANGELOG),
`438990e` (code review — §2.3 and §2.4 below are its findings; no scan logic
changed, both CSVs byte-identical).

**§4.1 — the NPV/SC-GHG sensitivity to τ — was deliberately NOT run** (Marcus set it
aside for this session). It remains the one unrun item of the parent handoff's §4, and
it is still the cheapest thing on the list.

**This addendum SUPERSEDES the parent handoff's §1.2 ranking and its §5 stage-1a/1b
entries. §1.1, §1.3, §1.4, §2, §3 and §7 are UNCHANGED** — §1.1 and §1.3 are in fact
confirmed below, with their domains of validity now measured rather than asserted.

---

## 0. THE ONE-PARAGRAPH VERSION

The amplification question is **discharged and it does not bite**: across four laws
spanning a **1.48×** range in effective amplification at our own ssp585@2300, the
required flux moves **1.01×** (ψ = 0.279–0.282 cm/yr), and the law above 2.75 K is
**exactly hindcast-inert** so it stays revisable with no refit. **But stage 1b
overturns the parent handoff's cell ranking.** Applied as a *band* rather than as a
*point*, the rate criterion cuts 526 admissible cells to **7**, and the survivor is
**cell A (ψ = 0.125)** — the cell §1.2 demoted. Two structural reasons, and the second
is the one that matters for wiring: the PROTECT rate band spans **4.3× on 35 runs that
are only 5 GCM clusters**, so it holds cell A and cell B alike; and since **ψ = 100·V/τ**,
the 2.73 m NO+NE inventory caps ψ at **0.124 cm/yr at τ = 2200 yr** against the 0.273 cell B
needs — **cell B is a whole-sheet object, not a high-basin tap, and no scan setting changes
that.** Stage 1a is a **STOP**.

---

## 1. §4.2 — THE AMPLIFICATION LAW ABOVE 2.75 K (`python/diag_gis_amp_above_275.py`)

Gated: the local driver reproduces `regional_driver` under the shipped law to
**3.6e-15 K**, so the other three laws differ *only* in the amp field.

| law | amp @7.81 K | amp @13.63 K | base 2300 | **ψ_rate** | ψ_level | ratio |
|---|---|---|---|---|---|---|
| `held` S flat above 2.75 K **[SHIPPED]** | 1.652 | 1.652 | 49.9 | **0.279** | 0.269 | 0.97 |
| `full` CMIP6 binned to 5.75 K, then flat | 1.586 | 1.586 | 47.7 | **0.280** | 0.282 | 1.01 |
| `decl` full + the −0.0503/K decline *continued* | 1.453 | 1.077 | 43.8 | **0.280** | 0.304 | 1.08 |
| `summer` Bochow melt-relevant, `GMT = f_conv/1.19 + 0.5` inverted | 1.114 | 1.146 | 38.1 | **0.282** | 0.335 | 1.19 |

ψ in cm/yr at fixed τ = 2200 yr, solved in closed form (the reservoir ramp keys off
GMT, not the regional driver, so its contribution is exactly linear in ψ — no scan).

**Three findings.**

1. **ψ is invariant — 1.01× across a 1.48× amp spread.** The base's own 2250-2300 rate
   is 2.6–2.9 cm/century against a 26.5 target, so the reservoir supplies ~90 % of it
   under every law and the amp cannot move what is already nearly dead.
2. **The LEVEL requirement is not invariant, and that is the real caveat.** Base 2300
   moves 49.9 → 38.1 cm (1.31×), so the level/rate agreement cell B rests on degrades
   **0.97× → 1.19×**. One flux satisfies both requirements under `held` and `full`;
   under the two lower-amp laws it no longer quite does.
3. **Exactly hindcast-inert.** The bisected rate scale is identical to all printed
   digits across all four laws (1.015246, spread **1.000000×**) — the driver is observed
   south-Greenland T through 2024 and only spliced after. **Sub-choice 1 of
   `ladrillo_gis_amp` stays revisable at projection time with no refit.**

**§1.1 confirmed and now quantitative:** the φ=1 ceiling ratio on the warm arms stays
above 1 under every law, **1.93×–3.81×**. The parent handoff predicted 2.41 → ~3.4;
`decl` (3.81) and `summer` (3.23) bracket it. ⚠ **The summer law pushes ssp126 r2300 to
1.11×**, so "the cool arms are at or above their ceiling" is amp-law dependent in a way
the warm-arm reading is not.

**Where the evidence stops:** CMIP6 has ≥20 models only to **4.75 K** and any models
only to **5.75 K**. Our ssp585@2300 (7.81 K) is **1.4× beyond any data**; the x2300 arm
(13.63 K) is **2.4× beyond**.

---

## 2. STAGES 1a + 1b (`python/scope_gis_reservoir_rate_rank.py`)

1080 cells = the shipped 216 × a 5-point `RAMP_W_K` axis. Two gates: the
w-parameterised ramp is **bit-identical** to the shipped one at w=1, and the w=1 slice
reproduces the shipped **(135 all_pass, 86 also clearing both 2150 bands) exactly**.

### 2.1 Stage 1a — **STOP**, and the verdict had to be taken off the level score

| w (K) | pass_2150 | + r2300 rate | best rms_all | τ of best |
|---|---|---|---|---|
| 0.5 | 81 | 3 | 0.2992 | 400 |
| **1.0** | **86** | **4** | 0.3015 | 800 |
| 2.0 | 95 | **0** | 0.2911 | 800 |
| 4.0 | 117 | **0** | 0.2836 | 400 |
| 8.0 | 147 | **0** | 0.2807 | 400 |

Widening the ramp improves `rms_all` by **1.074×**, so an `rms_all`-only reading returns
GO. But `rms_all` is a **LEVEL** score and the criterion the model *fails* is the
**RATE**: passing cells go **4 → 0** for every w > 1, and every w>1 winner sits at
**τ ≤ 400 yr** against the equilibrium literature's 2–3 kyr. Since `RAMP_W_K` **is** a
common-τ ladder's `v(θ)` half (parent §2 identity), **a ladder cannot pay for its extra
parameters either. Do not build N>1.**

### 2.2 Stage 1b — the criterion is powerful, and it re-opens the selection the *other* way

| criterion | cells |
|---|---|
| 2100 + 2300 bands + shape + inventory | 740/1080 |
| … + both ssp585 2150 bands | 526 |
| … + the **r2300 rate band** | **7** |
| … + the **x2300 rate band** | **0** |

**0/1080 on x2300 confirms parent §3.1 over the full grid** rather than by argument.
The 7 survivors carry **ψ 0.094–0.125 cm/yr**, and the re-ranked winner is
**V=1 m / onset 4.69 K / τ=800 yr — cell A.**

**Why this differs from §1.2, and neither is wrong:**

* **POINT vs BAND.** Cell A's 12.0 cm/century is **2.2× below the PROTECT median 26.5**
  (§1.2's demotion) and **inside the run-level band 9.7–41.5** (this scan's winner).
  The band spans **4.3× on 35 runs that are only 5 GCM clusters**; the clustered band
  (11.6–36.9, 3.2×) still holds both cells. ⇒ **the rate criterion narrows the set hard
  but does not pin ψ to better than ~2×.** §1.3's "the rate criterion identifies the
  flux" holds against the **median**, not the band.
* **THE INVENTORY CEILING EXCLUDES CELL B, and this is the wiring statement.**
  `ψ = 100·V/τ`, so a hard cap on V is a τ-dependent cap on ψ:

  | τ (yr) | ψ_max at V_MAX = 2.73 m | × short of 0.273 |
  |---|---|---|
  | 800 | 0.341 | 0.80× |
  | 1600 | 0.171 | 1.60× |
  | **2200** | **0.124** | **2.20×** |
  | 3200 | 0.085 | 3.20× |

  **At the handoff's own τ the high basin cannot supply the handoff's own flux, short by
  2.2×.** Cell B is not merely outside this grid — it is outside the high basin. The flux
  and the literature τ *together* force a whole-sheet object.

### 2.3 ⚠ ONE CLIMATE MODEL IS LOAD-BEARING (added after code review)

Leave-one-GCM-out on the r2300 rate band. The parent handoff's §7 says *"35/35 runs is
not p = 2^-35; cluster by GCM"* — the same trap applies to a **band** built from those
runs, and it was not checked in the first pass.

| dropped GCM | band p05-p95 | survivors |
|---|---|---|
| — (all 5) | 9.7-41.5 | 7/7 |
| CESM2-Leo | 9.6-41.5 | 7/7 |
| CNRM-ESM2-1 | 9.7-41.5 | 7/7 |
| IPSL-CM6A-LR | 9.7-41.5 | 7/7 |
| **MPI-ESM1-2-HR** | **19.2-41.5** | **0/7** |
| UKESM1-0-LL-Robin | 9.6-36.7 | 7/7 |

**The band's p05 (9.7) is exactly the lowest per-GCM median.** Drop that one model and
the floor moves to 19.2, cell A's 12.0 falls outside, and **no high-basin cell clears
the rate band at all.** So §2.2's "the criterion admits cell A" is a one-model result —
and its failure mode **strengthens the whole-sheet reading**, because without MPI the
inventory-capped grid is simply empty.

**By contrast the x2300 verdict is band-independent** despite resting on only 2 GCMs:
the grid's best achievable rate is **81.3** against the single *slowest* run at
**122.2**, a 1.5× gap. No band width could admit a cell, so 0/1080 stands.

### 2.4 §1.3 confirmed, with its domain measured

Grouped by **(ψ, onset)** — grouping on ψ alone folds the onset spread into a claim
that is about how (V, τ) split at *fixed* onset, and inflates it. Corrected, `rms_all`
within one group varies by **≤2.297× over all τ**, **≤1.220× at τ≥800**, and
**≤1.011× (median 1.003×) at τ≥800 with w fixed** — exactly as the O((s/τ)²) curvature
argument requires, and **substantially tighter than the ψ-alone numbers first
reported** (1.150×/1.089×). **The degeneracy is a long-τ statement, not a property of
the grid.**

---

## 3. TWO CHOICES FLAGGED, NOT RESOLVED — both are Marcus's call

1. **Rate-band basis.** Built **run-level** to match how the shipped LEVEL bands are
   built, which makes it the *narrower* and therefore *stricter* of the two.
   `RATE_BAND_BASIS` switches it to GCM-clustered; both are printed. A run is one of 5
   percentile variants of a GCM × RCM pair, so the honest n is 5, not 35 — the same trap
   the parent handoff's §7 flags for "35/35 runs".
2. **Promotion.** Both new files write their own CSVs;
   `scope_gis_reservoir_offline.py` and `outputs/scope_gis_reservoir_offline.csv` are
   **untouched**, because folding the rate criterion in would overwrite the provenance
   for 86/216 and for the shipped cell's selection. **Promotion moves a cell.**

---

## 4. WHAT THIS CHANGES ABOUT THE DELIVERABLE

The parent handoff's quotable result was *"a sustained flux ψ ≈ 0.27 cm/yr opening
above ~4.7 K, with (V, τ) by prior."* After this session:

* **The ψ ≈ 0.28 number is robust to the amplification question** — that was the stated
  blocker and it is discharged.
* **But ψ ≈ 0.27 and "a high-basin tap" are not simultaneously available.** Either the
  flux is charged to the whole sheet (V ≈ 6 m at τ = 2200), or the high basin caps it at
  **ψ ≤ 0.124** and the model lands on cell A's ψ ≈ 0.125 with a 2250-2300 rate at the
  **bottom** of the PROTECT band rather than at its median.
* **The x2300 arm is untouched by any of this** — 0/1080 cells, exactly as §3.1 said,
  and band-independent (§2.3).
* **⚠ The high-basin case is one model wide.** Cell A survives only because
  MPI-ESM1-2-HR sets the band floor (§2.3). That is not a reason to prefer cell B, but
  it does mean the high-basin option should never be quoted as "the rate criterion
  selects it" without the leave-one-out attached.

## 4b. HIGH BASIN vs WHOLE SHEET — the fork, with the numbers

**Capacity, measured** (`K_SOUTH, K_HIGH = 0.6286, 0.3714`, `GIS_V0_M = 7.42 m`):

| | capacity | base L_eq @our ssp585 2300 | headroom | clip active |
|---|---|---|---|---|
| south | 4.664 m | 0.400 m (8.6 %) | 4.264 m | 0.0 % of draws |
| **high (NO+NE)** | **2.756 m** | 0.237 m (8.6 %) | **2.519 m** | 0.0 % |
| whole sheet | 7.420 m | 0.637 m | **6.783 m** | — |

**The model's high-basin capacity is the Mouginot NO+NE inventory to 1 %** (2.756 vs
2.73 m) — the physical bound is already structurally encoded, not bolted on. And the
base model's clip is **nowhere near binding** (0.0 % of draws, 8.6 % of capacity used,
still only 1.06 m at the x2300 arm's 13.63 K), so "re-opens the capacity clamp" is a
statement about the *reservoir*, not about the base colliding with it.

### High basin

**For.** The threshold is *defensible physics for this specific ice*: Mouginot 2019's
own conclusion is that NO+NE hold the largest potential SLE (273 cm), currently
discharge little (25.9 + 39.5 Gt/yr in 2018) because shelves still buttress them, and
are "of greatest relevance to future sea level rise" — a margin-retreat-into-deep-basin
threshold is exactly that process. The dormancy premise survived its own audit (NW is
the over-active region; NO+NE dormancy holds). It is **already wired**
(`greenland_3basin_component.jl`), the capacity bound is a citable inventory number, and
the tap is calibration-inert with 3.3 K of headroom.

**Against.** `ψ = 100·V/τ` with V ≤ 2.73 m caps **ψ ≤ 0.124 cm/yr at τ = 2200 yr** —
**2.2× short** of the flux that matches the PROTECT rate median. To reach ψ = 0.273
inside the basin you need **τ ≤ 1000 yr**, against the equilibrium literature's 2-3 kyr
(Van Breedam 2020 ~2 kyr; Greve & Chambers 2022 ⇒ τ ≈ 3300 yr). And the cells that do
survive sit at the **bottom** of the PROTECT band and only because **one GCM** puts the
floor there (§2.3).

### Whole sheet

**For.** Relieves the ψ cap: V = 6 m at τ = 2200 gives ψ = 0.273, matching the rate
median *and* (under the shipped and fullcurve amp laws) the level p50 simultaneously.
It **fits** — 6.0 m of 6.78 m headroom. And it is the object the equilibrium literature
actually reports: Van Breedam and Greve & Chambers describe **whole-sheet** response on
a 2-3 kyr clock, so a V ≈ V₀ / τ ≈ 2-3 kyr reservoir puts the prior on the right thing.
§1.1's φ=1 ceiling is itself a whole-sheet statement (it sums both basins).

**Against.** Three, and the first is the serious one.
1. **It takes the literature's τ and V but discards the literature's low-T commitment
   shape.** A whole-sheet object with *exactly zero* commitment below 4.69 K and 6 m
   above is the opposite of what the same equilibrium literature says: both Bochow-2023
   ladders are extremely sensitive at low T (PISM commits 85 % of the sheet by 2.6 K,
   Yelmo 66 % by 1.76 K). A high-basin threshold does not have this problem, because
   NO+NE activation genuinely *is* a high-T marginal process.
2. **It consumes 88 % of the remaining headroom** (6.0 of 6.78 m), so the `L_eq` clip
   goes from never-binding to near-binding — and §7 already flags the clip as
   non-smooth and invalidating gradients wherever it binds.
3. **No existing wiring.** The tap is on the high basin; a whole-sheet term is new
   structure, i.e. Stage 4's ~10 edit sites in `calibrate_mcmc_ext.jl`, three of which
   have each caused a silent result-voiding failure in this repo's history.

### Recommendation — it is a false binary, and §1.1 already said so

**Neither assignment fixes the actual defect.** §1.1 says the broken thing is the
**commitment law**; §3.1 (now 0/1080 and band-independent) says **no fixed-V reservoir
can ever match x2300**. A reservoir is a *proxy* for missing commitment, and choosing
which basin to charge the proxy to does not make it the right object.

**Proposed split, which is Stage 2 with a reason it is not optional:**
* **Keep the reservoir on the HIGH BASIN, inventory-capped** (ψ ≤ 0.124 at literature
  τ). It is already wired, calibration-inert, capacity-bounded by a citable number, and
  its threshold is defensible physics for that ice specifically.
* **Put the remaining shortfall on a convex slow-channel `L_eq`** — what §1.1 says is
  broken, what x2300 needs, and what avoids asserting 6 m of whole-sheet commitment
  behind a threshold the equilibrium literature contradicts at low T.
* **Keep whole-sheet as the fallback parameterisation if Stage 2 fails**, with the low-T
  contradiction documented rather than quietly carried.

## 4c. ⚠ THE WHOLE SCORECARD IS GCM-FRAGILE — this reverses §4b's "Stage 2 next"

Prompted by the MPI finding, the same leave-one-GCM-out was run on the **level** bands
that every criterion in this arc is scored against. Edge shift is the worst movement of
either band edge when one GCM is dropped, as a fraction of the band's own width.

| arm | horizon | band | width | worst edge shift | nGCM |
|---|---|---|---|---|---|
| SSP5-8.5 r2300 | 2150 | 14.1-47.7 | 33.6 | **31.9 %** | 5 |
| SSP5-8.5 r2300 | 2300 | 29.8-108.7 | 78.9 | **33.0 %** | 5 |
| SSP5-8.5 x2300 | 2150 | 43.8-52.5 | 8.6 | 14.1 % | 2 |
| SSP5-8.5 x2300 | 2300 | 217.9-301.1 | 83.2 | **94.1 %** | 2 |
| SSP1-2.6 r2300 | 2300 | 6.2-15.9 | 9.7 | **87.9 %** | 2 |
| SSP1-2.6 x2300 | 2300 | 9.5-10.4 | **0.9** | undefined | **1** |
| SSP2-4.5 r2300 | 2300 | 10.6-21.5 | 10.9 | **84.5 %** | 2 |

**Four of the five arms rest on ≤2 GCMs, and one on a single GCM.** The ssp126 x2300
"band" is 6 runs of one climate model at three ISM percentiles — a 0.9 cm width that is
parameter spread, not model spread. And **every x2300 arm is NORCE / CISM16x-MAR312 at
p25/p50/p75**: one ice-sheet model, three percentile variants, which are not independent.

This sharpens the parent handoff's §8 ("every anchor past 2100 is NORCE-CISM, so the
p05-p95 is CLIMATE-forcing spread, not structural spread") in the direction that matters:
**the climate-forcing spread is itself 1-2 GCMs on four of the five arms.**

**Consequence for sequencing.** Stage 2 introduces a **calibration-ACTIVE** change (a
convex `L_eq` acts in the hindcast ⇒ refit, not prior-propagation), i.e. Stage 3/4's
~3-5 days plus 6-8 h compute across ~10 edit sites, three of which have each caused a
silent result-voiding failure here. It would be **fitted to the x2300 arm (1 ISM × 2
GCMs)** and **judged by bands whose edges move 78-94 % of their own width on a single
GCM drop**. That is the expensive move first.

⇒ **§4b's "Stage 2 is the next real step" is WITHDRAWN.** The next step is to price the
targets, not to build against them. Revised order in §5.

## 4d. STEP 1 RUN — the commitment-law diagnosis is GCM-robust; the cell selection is not

`python/diag_gis_scorecard_logo.py`. Two gates: the baseline matched-band rebuild
reproduces the shipped `gis_targets` to **0.03 cm**, and **ACCESS1.3** — already
excluded by `protect_band` — drops as an **exact no-op** (null control), so the sweep
measures the drop and not the rebuild.

| dropped GCM | 135 | 86 | 2150 | +r2300 rate | best ψ | k*(585) | k*(cool) |
|---|---|---|---|---|---|---|---|
| **(none)** | 135 | 86 | 526 | 7 | 0.125 | 3 | 0.75 |
| ACCESS1.3 *(null control)* | 135 | 86 | 526 | 7 | 0.125 | 3 | 0.75 |
| **CESM2** | **0** | **0** | **0** | **0** | — | 3 | 0.75 |
| CESM2-Leo | 135 | 86 | 526 | 7 | 0.125 | 3 | 0.75 |
| CESM2-WACCM | 134 | 82 | 504 | 4 | 0.094 | 2 | 1.00 |
| CNRM-ESM2-1 | 138 | 86 | 526 | 7 | 0.125 | 3 | 0.75 |
| IPSL-CM6A-LR | 137 | 78 | 493 | 4 | 0.094 | 3 | 0.75 |
| **MPI-ESM1-2-HR** | **33** | **0** | **0** | **0** | — | 3 | 1.00 |
| UKESM1-0-LL-Robin | 129 | 86 | 526 | 7 | 0.125 | 2 | 0.75 |

**NOT ROBUST — every cell-selection verdict.** Two single models each void the whole
admissible set, by **different** mechanisms, and the mechanism matters more than the
count:

* **CESM2** — the **ssp245** matched band collapses **10.6-21.5 → 10.1-12.3** and the
  base model's 18.3 cm falls **outside** it. The reservoir is inert below its onset, so
  **no cell can repair a cool-band failure**: 1080 → 0. The ssp245 criterion is one GCM.
* **MPI-ESM1-2-HR** — the **ssp585** matched band's floor rises **42.9 → 77.6** and the
  base 49.9 falls out. Cells *can* add loss there, so 135 → 33, but 2150 kills the rest.
  This is the same model already load-bearing for the rate band (§2.3).

**ROBUST — the structural conclusion, which is what the step-back actually rests on.**

* **The k tension survives 8/8.** ssp585 wants k ∈ {2, 3} and cool wants k ∈
  {0.75, 1.0} under **every** drop. So *"one law is being asked to be steep at 6 K and
  flat at 2 K"* — the reading that identified the **linear `L_eq`** as the defect — is
  **not a one-model artefact.**
* The x2300 rate verdict is 0 under every drop (already band-independent, §2.3).
* ψ of the winning cell stays **0.094-0.125** whenever anything survives — never near
  the handoff's 0.273.

**⇒ The §1.1 commitment-law diagnosis stands. What does not stand is any cell chosen
against these bands** — including the shipped cell, cell A and cell B alike.

**Stated approximation.** Level, rate and matched-anchor *quantiles* are rebuilt exactly
from the reduced run set; the matched bands' PCHIP *predictor* (each anchor's 2015-2300
GSAT integral) is **held**, because per-GCM GSAT is not on disk. Within one arm every
GCM follows the same scenario, so the forcing-integral spread is far narrower than the
SLR-response spread — the smaller of the two errors.

## 4e. STEP (b) — the residual band, built and tested

`python/diag_gis_gcm_tdecomp.py`, `python/reduce_cmip6_tas_gis_extra.py`,
`python/diag_gis_residual_band.py`. Marcus's framing: the two things separating the
GCMs are the **rate of local temperature change** (correctable) and **precipitation**
(not). That makes the band-basis question "how much of the width is correctable", not
"run-level or GCM-clustered".

**Most of it is correctable.** On ssp585 r2300, now complete at **n=5** (UKESM1-0-LL
fetched — it was never missing data, `reduce_cmip6_tas_gis.py` caps at 40 models
alphabetically and stops at NorESM2-MM):

| route | R² | rank r | resid sd / ISM sd |
|---|---|---|---|
| **GMST (our production path)** | **0.95** | 0.90 | **0.23** |
| DIRECT, south-zone T | 0.80 | 0.90 | 0.45 |
| DIRECT, all-zone T | 0.80 | 0.90 | 0.44 |

Adding the arm's **largest** member (UKESM, 106.7 cm) *improved* the fit (0.92 → 0.95).
Guidance from the arms too small to fit: the single pairwise contrast puts **0.49×**
(ssp126) and **0.78×** (ssp245) of the gap on local temperature — both correctly
ordered, and the ssp245 number is on the exact arm where CESM2 was load-bearing.

⚠ **Driving with the GCM's own regional T makes predictions WORSE** (R² 0.80 vs 0.95).
`c1` was calibrated against the observed south driver and absorbs the amplification
level, so feeding a weaker driver without it under-predicts. The GMST route already
carries the correction.

### The band, and the result that reversed my expectation

| dropped GCM | RAW band | RESIDUAL band |
|---|---|---|
| **(none)** | 750 | 752 |
| CESM2 | **0** | *undefined* (ssp126 → 1 GCM) |
| CESM2-Leo | 750 | 759 |
| CNRM-ESM2-1 | 750 | 762 |
| IPSL-CM6A-LR | 750 | 763 |
| MPI-ESM1-2-HR | **126** | *undefined* |
| UKESM1-0-LL-Robin | 739 | 741 |

1. **On ssp585 the residual band is stable** — 741-763 against a 752 baseline, none
   zeroed, against the raw band's MPI drop taking 750 → 126. Banding on the residual
   fixes the **position**, which is what the fragility was.
2. **Width was never the problem.** The naive min/max residual band collapses ssp245 to
   1.5 cm and **excludes our own base** (top 17.4 vs base 18.3); the reservoir only
   adds, so nothing passes. Respect the sample size with a Student-t prediction
   interval and it inverts:

   | scenario | n | base | SHIPPED | minmax | t-PI | widths sh/mm/t |
   |---|---|---|---|---|---|---|
   | SSP1-2.6 | 2 | 10.1 | 6.2-15.9 | 7.7-12.6 | −35.7-56.8 | 10 / 5 / **93** |
   | SSP2-4.5 | 2 | 18.3 | 10.6-21.5 | 16.0-17.4 | 0.3-33.1 | 11 / 1 / **33** |
   | SSP5-8.5 | 5 | 49.9 | 42.9-145.0 | 47.6-110.5 | 18.5-150.9 | 102 / 63 / 132 |

   **The honest cool-arm bands are 3-9× WIDER than shipped.** So the raw bands were not
   too wide — they were arbitrarily **placed** and **spuriously precise** on the cool
   arms. ⚠ **The cool-arm 2300 criterion is far weaker evidence than it looks**, and it
   is what kills k ≥ 1.5.
3. **No leave-one-out is defined on a 2-GCM arm** — dropping one leaves a single model
   with no spread. My first pass took min==max, produced a zero-width band, and it read
   as "this GCM is load-bearing" when it means "this arm has 2 models". The raw band
   only *appears* to survive cool-arm drops because it quantiles run-level percentile
   variants rather than models.

**Flagged, not resolved:** `RESID_FORM` (additive vs multiplicative) and
`RESID_INTERVAL` (minmax vs t-PI); both computed and printed.
**Limitation:** built on **three** r2300 anchors, not the shipped five — an x2300 arm
cannot be T-normalised without post-2100 CMIP6. Our ssp585 forcing sits **above** that
3-anchor hull, so its band comes from the hull rule rather than interpolation.

**Provenance:** UKESM went into `data/cmip6_gis_extra/`, NOT the shipped panel, because
`diag_gis_amp_cmip6.py` globs `data/cmip6_gis/` and a 41st file would silently change
`gis_amp_shape.csv` on re-derivation.

## 5. NEXT

1. **§4.1, the NPV sensitivity to τ** — still unrun, still the cheapest item, and it may
   retire the τ question outright.
2. **Decide the two flagged choices in §3.** The band basis changes how many cells pass;
   the promotion decision moves a cell.
3. **NOT Stage 2 — see §4c.** Cheapest-first, and the first two re-price everything
   already concluded:
   * **(a) DONE — see §4d.** The commitment-law diagnosis (the k tension) is
     GCM-robust 8/8; every cell-selection verdict is not, and two single models void
     the admissible set outright.
   * **(b) DONE — see §4e.** Both options I had proposed were wrong: run-level and
     GCM-clustered both quantile the TOTAL. The residual basis is right and is stable
     on the one arm that can test it — but the cool arms cannot be tested at all, and
     their honest bands are 3-9x WIDER than shipped, not narrower.
   * **(c) Run §3.2's two-stage gate** — `corr(d(history)/dp, d(2300 rates)/dp)` at the
     optimum. The parent handoff names this as the precondition for "fit the ensemble
     first", which is exactly the strategy Stage 2/3 would use. Cheap and offline, and
     it determines *how* Stage 2 is run if it runs.
   * **(d) §4.1, the NPV sensitivity** — still the parent handoff's own stated gate
     before any model change; deprioritised by Marcus, so his call whether it stays so.
   * **THEN Stage 2**, with the target's structural width known.
4. **The §4b fork does not need deciding yet.** It is a physics/wiring call, and (a)
   may change which side the evidence falls on — cell A already survives on one GCM.
