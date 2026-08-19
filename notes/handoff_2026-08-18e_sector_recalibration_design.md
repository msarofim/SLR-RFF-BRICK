# Handoff — the dormancy premise broke, and the 3-basin sector recalibration is now the plan

**Start-here document for the next session.** Repo `SLR-RFF-BRICK`, branch
**`ladrillo-dev`**, HEAD `8f20808`, **pushed and in sync with origin**.
Predecessor: `notes/handoff_2026-08-18d_zonespace_and_amp.md` (same day —
read this one first; it supersedes d's forward plan, not its results).

**Bottom line: the zone-space wiring landed and the amp sensitivity emptied the
robust core (handoff d). Then Marcus reframed the amp question around the
basins' different informational roles, and following that reframing broke the
mock's own premise: scored against Mouginot Dataset S2, the mid basin (NW) is
the single MOST over-active region in Greenland — 17% of the volume, 32% of the
1972–2018 loss — while the mock holds it dormant. The high basin's dormancy
premise survives. The projection-side-only decision does not. The plan is now a
3-basin recalibration on Mouginot SECTORS with a per-sector mass-loss likelihood
term, which is the calibrator restructure §6 item 3 was going to price — now
motivated by the historical partition being wrong rather than by the ssp585
shortfall. Design is decided and recorded below; nothing is blocking.**

---

## 0. WHAT CHANGED IN ONE TABLE

| | before | after |
|---|---|---|
| the mock's dormancy premise | assumed for both dormant basins | **HOLDS for high (0.54), FAILS for mid (1.83)** |
| basins the mock holds dormant | contribute 0% historically | **contributed 52% of 1972–2018 loss** |
| choice 4 (projection-side only) | decided this morning | **does not survive** — recalibration required |
| co-calibrating amp | recommended AGAINST (likelihood-flat) | **recommendation REVERSED** — basins get historical channels |
| basin geometry | latitude bands | **Mouginot SECTORS** (Marcus) |
| per-basin drivers | central/north built + guard-proved | **single Greenland amp** (Marcus) ⇒ tier-2 becomes provenance |
| mid basin structure | dormant, with a tap | **active channel, NO tap** |
| Aschwanden NW finding | "land-terminating by 2300", sign unexamined | **a DECELERATION at the horizon's edge** — argues against a tap |

Commits since handoff d: `765bf2a` (amp is prior-driven + the ANCHOR arm),
`adafb71` (the partition scoring), `8f20808` (Aschwanden fetched and quoted).
All pushed. CHANGELOG entries l / m.

---

## 1. THE FINDING THAT CHANGED THE PLAN

`python/diag_gis_basin_lit_check.py` block 1b, against the Dataset S2 parse the
script already owned and parse-gates:

| basin | %SLE | %loss 1972–2018 | loss/SLE | verdict |
|---|---|---|---|---|
| south (the shipped A+B) | 45.6% | 48.1% | 1.06 | proportional |
| **mid = NW** | 17.3% | **31.7%** | **1.83** | **OVER-ACTIVE — premise FAILS** |
| high = NO+NE | 37.1% | 20.2% | 0.54 | dormant premise HOLDS |

**The mock treats the most over-active region in Greenland as dormant**, and the
two basins it holds dormant contributed **52%** of the 1972–2018 loss. **41 of
the 59 passers have an active mid basin**, so it is not a corner case.

The consequence for the shipped model is the real problem: **A+B is calibrated
to TOTAL Greenland loss while driven by SOUTH-zone temperature alone**, so its
fitted parameters are compensating for mass loss that physically came from other
basins on other drivers. A structure whose historical partition is wrong cannot
be bolted onto a calibration fitted under the wrong partition.

---

## 2. WHY THE AMP RECOMMENDATION REVERSED (both halves are on the record)

**First position (CHANGELOG l, still correct as stated):** the hindcast is
nearly blind to amp — MEASURED. `regional_driver` returns the OBSERVED zone
series for every year observations cover (to 2024) and only splices
`amp·S(dT)·GMST` on afterwards; the calibration window is 1900–2025. So amp
changes the south driver in **exactly one year of 126** (first differing year
**2025**), and the dormant basins are inert until 2087 so their amps have
**exactly zero** effect anywhere in the hindcast. Corroboration: `gis_amp`
posterior **1.9169** vs prior mean **1.9222** — 0.3% movement. Co-calibrating a
likelihood-flat parameter returns the prior.

**What reversed it:** that argument rests entirely on the dormant basins being
invisible to the likelihood. Once they carry historical channels — which §1
forces — their zones become visible and co-calibration is genuinely informative.
**Marcus's original instinct was right, contingent on exactly this.**

---

## 3. THE DESIGN, AS DECIDED

**Geometry — Mouginot SECTORS** (Marcus): south {SW, CW, CE, SE} · mid {NW} ·
high {NO, NE}. Rationale in his words: sectors are the geometry the *data* has.

**Driver — a SINGLE Greenland amplification** (Marcus): "if we had to use a
single Greenland amplification number, that would probably be acceptable, and
the different temperatures for the different basins would probably be
internalized in the calibration process."

> **This is the big simplification: the sector geometry then lives ENTIRELY in
> the likelihood, not in the drivers.** No sector-masked temperature build, no
> sector CMIP6 re-reduction. The tier-2a/2b per-zone work becomes provenance.
>
> **Stated cost, on the record.** A single amp assumes the basin temperature
> *ratios* stay fixed. They do not — north amp **2.83** vs south **1.92**, so by
> 2300 under SSP5-8.5 the north zone is **21.2 K** against south's **12.6 K**.
> Calibration can internalise a constant offset into rate constants, not a
> diverging one, and it diverges most for the basin carrying the tap. **Cheap to
> revisit**: the per-zone drivers exist and are guard-proved, so the high
> basin's tap can read the north driver later without rebuilding anything.

**Driver column = `all`** (whole-sheet), not `south`. The shipped calibration
uses `south`; the model now spans every sector, so the whole-sheet series is the
consistent choice. Recommended and taken.

**Basin structure:**

| basin | structure | why |
|---|---|---|
| south | keeps A+B fast/slow | unchanged form; re-fitted to its own sector loss |
| **mid (NW)** | **active channel, NO tap** | over-active today; Aschwanden's NW transition is a *deceleration* |
| high (NO+NE) | small active channel **+ volume tap** | loss/SLE 0.54 = under-proportional, **not zero** |

**Likelihood:** existing total-GMSL term **+ per-sector cumulative mass loss**
from Dataset S2. This is the real new machinery, and it is the ONLY reason the
mid basin must stay separate (see §4).

---

## 4. THE TWO SUB-QUESTIONS MARCUS ASKED, ANSWERED

**"Is active-channel-no-tap sufficiently different from folding NW into the
south basin?"** — Honest structural answer: with a **single shared driver** and
the same functional form, **no**, not dynamically. A+B is already a fast+slow
two-exponential response; a third linear channel on the same driver merely
re-parameterises a multi-exponential.

**It is worth keeping separate for exactly one reason: the likelihood.** The
point of the recalibration is to reproduce the observed 48/32/20 partition, and
a per-sector constraint can only be scored against per-sector state. A lumped
basin has nothing to score. That settles it alone.

**The volume-cap argument does NOT hold and was dropped rather than padded**:
NW holds 127 cm and is drawn down at 1.83× its volume share, but at 2010–2018
rates it exhausts in **~6,800 yr** (NO 11,800; NE 29,200). The cap cannot bind
by 2300 unless rates rise ~20×.

**"How long before 2300 is the Aschwanden transition, and is it worth extra
parameters?"** — Fetched **PMC6584365** rather than answering from the one-line
summary. The paper: *"By the year 2300 (RCP 8.5) or 2500 (RCP 4.5), almost all
outlet glaciers in northwest Greenland have become land terminating, and ice
discharge there is greatly reduced."*

- **Timing: 2300 under RCP8.5 — the very edge of our horizon; 2500 under RCP4.5,
  beyond it entirely.**
- **The SIGN is the point: it is a DECELERATION, not an activation.** A tap
  accelerates. So the finding argues **against** a mid-basin tap.
- The mechanism that *does* accelerate under RCP8.5 is the one the HIGH basin
  already represents: the margin "retreat[ing] into interior areas below sea
  level, resulting in large calving fronts and increased ice discharge."
  **NW shuts down while the deep interior basins open** — precisely the
  mid-active / high-tapped partition.
- **Recommendation taken: do NOT parameterise the shut-off.** It arrives at the
  horizon's edge under the highest scenario only and nothing we have resolves
  it. Carry it as a stated caveat that NW is biased slightly HIGH at 2300.

Net parameter count is **lower** than the current mock — dropping the mid tap
removes three knobs (onset, V-share, τ).

---

## 5. WHAT'S NEXT — prove the partition offline BEFORE touching the calibrator

Same discipline that governed the whole arc: the mock proved the structure
*could* make the 2300 separation before anyone priced a refit. The new question
is strictly harder and **could fail**, so it gets the same treatment.

**STATUS: step 1 is DONE — results in §5a below. Step 2 (the calibrator) is next.**

1. **`scope_gis_3basin_partition.py` — BUILT AND RUN (commit below).** Three basins on ONE
   `all` driver, each fitted to its OWN Mouginot sector loss, then scored on:
   (F-a) can three basins on a shared driver reproduce the observed **48/32/20**
   partition *and* the total at once? They differ only in rate constants, so
   this is not guaranteed; (F-b) **how much does the south basin's calibration
   change** once it stops absorbing NW+NO+NE's loss — this is the number that
   decides whether the restructure moves the headline; (F-c) does the 2300
   scorecard still clear with the high tap on top?
2. **Only then** touch `calibrate_mcmc_ext.jl` and the per-sector likelihood.
   **This is now the live next step.**
3. **Expect SLR@2100 = 45.53 cm to MOVE.** That is the headline number and it is
   downstream of the south basin's parameters. Say so before it surprises anyone.
4. Ship-with-caveat remains legitimate throughout; the 2100 deliverable stands
   on the current model until this lands.

## 5a. RESULTS OF STEP 1 (`scope_gis_3basin_partition.py`)

- **P1 — the two-window tension is PRE-EXISTING.** 3-basin fitted 1972–2018
  predicts −23.1% on 1900–2025; the **single basin with no partition misses by
  −25.1%** on the identical test. The partition slightly REDUCES it. **⇒ the
  per-sector term (1972–2018) and the total term (1900–2025) pull against each
  other by ~25%, and the calibrator must weight them deliberately.** This is the
  single most important thing to carry into step 2.
- **P2 — the headline moves less than feared.** Whole-sheet 2300: single basin
  24.09 / 62.71 cm vs 3-basin sum 21.66 / 58.56 (SSP2-4.5 / SSP5-8.5) —
  0.899× / 0.934×.
- **P3 — the scorecard clears with the mid tap REMOVED**: 10/64 tap cells pass,
  three fewer parameters than the mock. The active-channel-no-tap call holds.
- Data facts measured: target/Mouginot disagree on the 1972–2018 total by
  **1.227×** (peripheral glaciers the obvious but UNVERIFIED candidate — shares
  from Mouginot, total from the target); **64% of the calibration signal
  predates 1972**.
- Built `outputs/gis_amp_shape_all.csv` en route (CMIP6 1.674 vs observed 2.347).

**A partition assumption that needs stating in the write-up:** Mouginot's window
is **1972–2018**; the calibration window is **1900–2025**. Applying the 48/32/20
split to the full hindcast assumes the partition is stationary. It probably is
not (NW's acceleration is a recent-decades phenomenon). The 2010–2018 rates in
the table give a second, more recent split to test against.

---

## 6. THINGS THAT DID NOT SURVIVE / correction ledger

1. **The mock's mid-basin dormancy premise** — dead, §1. The high basin's
   survives.
2. **Choice 4 (projection-side only)**, taken this morning — dead, §1.
3. **The "do not co-calibrate amp" recommendation** — reversed, §2. Both
   positions and the reason for the switch are recorded; the first is still
   correct *as stated*, under a premise that no longer holds.
4. Carried from d: **the same apples-to-oranges gate error bit twice** (gating
   dormant response against zero in absolute terms charges zone space for the
   2.5/3.0 K mid onsets, which are already active on ssp245 in GMT space). Gates
   must be **parity**, plus a separate check on PASSING cells.
5. Predecessor §7 items still parked: L11-vintage memo figures at L12, and the
   `d2_basis` one-liner (five vintages deferred).

---

## 7. NON-OBVIOUS STATE

- **L12 remains canonical and untouched.** No chain run, no posterior moved.
  Everything since handoff c is offline post-processing.
- **Still two inherited modified files, now characterised** (fifth handoff):
  `outputs/mcmc/overdispersed_starts.csv` (all 4 start rows replaced, Aug 17;
  backups at `.pre_extc_bak`/`.pre_l12_bak`) — **committing it changes what a
  future chain starts from, so it is Marcus's call**; and
  `figures/diag_gis_regional_driver.png` (regeneration, Aug 10).
- **Stray zero-value file in the WRONG repo**:
  `FaIRtoFrEDI/outputs/log_scope_gis_basin_mock.txt` (288 bytes) is just a
  "can't open file" error from a mis-`cd`'d run. Left in place, flagged.
- `~/Documents/2026/ClaudeDocs/Papers/Mouginot/` has paper + SI + sd01 + sd02.
  **Aschwanden 2019 is still NOT local** — this session read it via
  **PMC6584365** (science.org 403s). TC 19:6887 also not local.
- macOS has no `timeout`; pin `OPENBLAS_NUM_THREADS=1` for anything parallel.
- Untracked by convention: `outputs/log_*.txt`.

---

## 8. FILES

**Created this session (both handoffs' worth):**
`python/diag_gis_zone_driver_scope.py`,
`python/scope_gis_basin_zonespace_vs_literature.py`,
`python/scope_gis_basin_zonespace_amp_sens.py`, handoffs d and e.

**Modified:** `python/diag_gis_basin_lit_check.py` (partition block 1b +
the Aschwanden NW quote), `CHANGELOG.md` (entries i–m).

**Key outputs:** `outputs/diag_gis_zone_driver_scope.csv`,
`outputs/scope_gis_basin_zonespace_vs_literature.csv`,
`outputs/scope_gis_basin_zonespace_amp_sens.csv` (+ `_robust_core.csv`),
`outputs/diag_gis_basin_lit_check.csv`.

**Memory:** `ladrillo_leq_ridge_ceiling` (§5 + gotchas; description rewritten
around the empty core), `INDEX_slr.md`. **Both need a further update for §1–§4
of this handoff** — flagged, not yet done.
