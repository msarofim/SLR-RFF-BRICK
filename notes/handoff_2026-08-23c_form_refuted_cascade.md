# Handoff — the cell the last session said to wire CANNOT be wired, the first-order reservoir FORM is refuted at every onset, and a 2-stage CASCADE clears 2150 + the 2300 p50 + Greve@3001 at once

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, through `9cd8085`.
Written 2026-08-23, to be picked up cold.

**Supersedes** `handoff_2026-08-23b_weighted_verdict.md` for its **§1 ("wire this cell")**
and its **§7 items 1 and 2**. Its §2 (τ retired for discounted use), §3 (the onset's spent
premise, the 1.588 K measured floor), §4 (ISMIP6 passes the obs gate; the 2100 acceleration
deficit), §5 (the weighted scoring), §6 (the SC-GHG conflict) and §9 (non-obvious state) are
**unchanged and still load-bearing**.

---

## 0. THE ONE-PARAGRAPH VERSION

Item 1 of the queue is done: the winner's ssp585@2300 = 99.4 cm **is** 1.009× the matched
p50 — but only on the predictor the band adopted; on the 2300-**level** arm the same
derivation kept, it is 0.827× the p50 (percentile 17). Item 2 — wire the cell — came back
**NO**. The cell had never been scored on the 2150 criterion **because it was outside the
V and τ grid the scorecard ever ran**, and it misses the ssp585 x2300 2150 band by 1.19×.
The obvious rescue (that band counts members as models) was tested and **REFUTED**: its two
GCM clusters agree at 2150 to 0.6 cm. An analytic pre-check then closed the whole family —
the joint 2150/2300 constraint needs a delivery ratio **6.03**, and a first-order reservoir
tops out at **2.89** over every onset in 1.6–7.5 K. **A 2-stage cascade gives 7.86, and the
cell V = 6.0 m / τ = 800 yr / onset 4.69 K clears both 2150 bands, lands on the 2300 p50
(98.2 vs 98.5) and hits Greve@3001 to 1.046×, with 2100 held at exactly 0.0000 cm.**
Offline only: no gate changed, no cell moved, Julia untouched, both default scan arms
byte-identical.

---

## 1. THE ANSWER, IF YOU READ NOTHING ELSE

|  | 2100 ratio | ssp585@2300 | 3001 ratio | x2300@2150 | w-score (3:2:1) |
|---|---|---|---|---|---|
| cell A (n=1, V=1, τ=800) | 1.434× | 70.4 cm | 0.36× | 53.1 (edge) | 0.584 |
| 08-23b winner (n=1, V=7.42, τ=2700) | 1.470× | 99.4 cm | 0.61× | **63.1 OUT** | 0.412 |
| **n=2, V=6.0 m, τ=800 yr, onset 4.69 K** | **1.369×** | **98.2 cm** | **1.046×** | **52.5 in** | **0.346** |

**29 of the 30 cells common to both scorecards pass — it is a REGION, not a point.**
G-INERT exactly 0.0, so it is still a prior-propagated change, not a refit.

⚠ **This is priced, not wired, and three things are open — see §5. Do not wire it either
until §5 item 1 is settled: the Julia tap clamps its volume to the HIGH basin.**

---

## 2. WHY THE 08-23b CELL FAILED — AND WHY NOBODY SAW IT

`scope_gis_reservoir_offline.py` scanned **V ≤ 2.0 m against a 2.73 m ceiling** (the NO+NE
**high-basin** Mouginot inventory, inherited from when the reservoir was a high-basin TAP)
and τ ∈ {100…3200} with no 2200 or 2700. The onset re-scan used a **whole-sheet** 7.42 m
ceiling and a different τ ladder. **The two scorecards had disjoint admissible regions and
nobody had run the winner through the first one.** `--wide-v` fixes that: 11 × 6 × 8 = 528
cells, whole-sheet ceiling. **Moving that ceiling is a CLAIM** — V ≤ 7.42 m is admissible
only if the reservoir is a whole-sheet object, which is also what §5 item 1 is about.

The winner passes three 2300 matched bands, holds 2100 at exactly 0.0000 cm and improves the
five-arm shape. It misses **ssp585 x2300 @2150: 63.1 cm vs a 44.6–53.2 band**. Cell A clears
that band by **0.12 cm = 1.4% of its width** — cell A was *selected* by this criterion and
has no margin in it.

Read as ψ the criteria are **disjoint**: 2150 caps ψ ≤ **0.125** cm/yr at onset 4.69 (the cap
rises to 0.141 / 0.188 / 0.281 at 5.5 / 6.5 / 7.5 K, but only reaches Greve's range where the
onset is past our own scenario's reach), against Greve@3001's 0.179–0.341 and the 2250–2300
rate criterion's 0.273–0.282.

---

## 3. THE RESCUE HYPOTHESIS, TESTED AND REFUTED — DO NOT RE-PROPOSE IT

`python/diag_gis_2150_band_veto.py`. The 2150 bands are run-level quantiles, and this repo
has twice found PROTECT run counts are not sample sizes, so the same band was rebuilt at the
GCM-cluster level. The x2300 arm has **2 GCM clusters and ONE ice-sheet model** — its three
`model` values are **MAR SMB percentile variants** (p25/p50/p75) of NORCE-CISM, not
independent ISMs — **but the two clusters agree at 2150 to 0.6 cm** (medians 45.0, 45.7). A
t-PI on n=2 widens the band only **1.6×**, top 53.2 → 53.0, and the winner is out under every
construction. **The narrowness is real at this horizon.**

---

## 4. THE PRE-CHECK THAT CLOSES THE FORM, NOT JUST THE CELL

≤ **8.1 cm** allowed at 2150 on x2300 (band top 53.2 − base 45.2); **48.6 cm** needed at 2300
on our ssp585 to reach the matched p50 (98.5 − base 49.9) ⇒ **required delivery ratio
R = 6.03**. A reservoir's response to its ramp is an **n-fold repeated integral**; in the
long-τ limit — the most back-loaded any n can be —

| n stages | achievable ratio | vs R = 6.03 |
|---|---|---|
| 1 (the form scanned exclusively so far) | 2.82 | short |
| 2 | 7.86 | clears |
| 3 | 21.71 | clears |

and swept over onsets 1.6–7.5 K, **n = 1 peaks at 2.89**. The escape "then move the onset" is
closed. This is the defect `protect_matched_forcing` named from the physics side on
2026-08-21b — *"physics wants ~nothing until 2147 then a term still accelerating at 2300; the
exponential is front-loaded and saturating"* — arriving independently from a band the
reservoir arc had never scored. **A cascade is NOT completely monotone**, so the exact bound
that refuted the ladder, Prony, stretched-exponential, Mittag-Leffler and power-law families
does not reach it.

---

## 5. WHAT TO DO NEXT, AND THE ORDER MATTERS

1. **WIRING IS A RE-HOMING, NOT A CONSTANT EDIT — settle this before touching Julia.**
   `julia/greenland_3basin_component.jl` applies `gis_tap_v` to the **high basin** behind a
   **high-basin capacity clamp** (`head = k_high*v0 − (fast_high+slow_high)`, `applied =
   min(wanted, head)`) and adds it into `gis_sl_high`. A whole-sheet V of 6.0 m against a
   k_high·v0 ≈ 2.76 m ledger is the wrong home even where the clamp does not bind. The
   component exports `gis_tap_wanted` and `gis_tap_applied` separately precisely so this can
   be measured — measure it before deciding.
2. **THE ONSET REOPENS UNDER THE CASCADE.** At equal / 3:2:1 / 4:2:1 weights the best is
   **2.10 K** (V = 3, τ = 800); 4.69 K wins only at 6:3:1. Those low onsets have **never been
   run through the offline 2150 scorecard** (its onset list starts at 3.2 K) — extend it.
   And 2.10 K is exactly the onset that **revives** the moderate-scenario per-tonne SC-GHG
   term that 08-23b §6 flagged the shipped onset as deleting, so item 2 and 08-23b §6 are the
   same decision wearing two hats. **Take it to Marcus together.**
3. **SCORE THE 2250–2300 RATE ON THE CASCADE.** ψ = 100·V/τ is a first-order
   parameterisation and does not carry over; the rate criterion is one of the two independent
   sources that pinned the flux, and it has not been re-evaluated for n = 2.
4. **The 2100 acceleration deficit is untouched and still the binding defect** (08-23b §4.1:
   0.65× observed curvature over 1993–2024 with level and rate both right). The cascade
   *improves* 2100 relative to both first-order cells (1.369× vs 1.434× / 1.470×) but the
   1.32× base bias is unchanged.
5. **Do NOT re-propose**: the sample-size widening of the 2150 band (§3, refuted), any
   first-order (V, τ, onset) that tries to reach the 2300 p50 (§4, bounded), or anything on
   08-23b §7 item 5's dead list.

---

## 6. FILES

**New:** `python/diag_gis_matched_band_score.py`, `python/diag_gis_2150_band_veto.py`.
**Extended, both default arms gated BYTE-IDENTICAL by diff:**
`python/scope_gis_reservoir_offline.py` (`--wide-v`, `--stages=N`) and
`python/scope_gis_onset_rescan.py` (`--stages=N`). Each writes an arm-suffixed CSV
(`_wideV`, `_n2`) so no arm can overwrite another's artefact.
**Unchanged:** everything in `julia/`, every gate, every cell. `86/216` still reproduces.
The D1–D5 change set (`spec_2026-08-14_next_calibration.md`) is still **NOT STARTED**.

Commits `60423ad` → `9cd8085`. Memories written: `gis_first_order_form_refuted`,
`gis_matched_band_predictor`; `gis_weighted_verdict_cell` marked ACTION-SUPERSEDED;
`MEMORY.md` and `INDEX_slr.md` updated.

---

## 7. NON-OBVIOUS STATE

* `scope_gis_reservoir_offline.reservoir_unit_n(gmt, onset, tau, stages)` keeps **τ as the
  TOTAL mean delay** (each stage runs at `stages/tau`), which is why `stages=1` is the old
  `reservoir_unit` term for term and the default CSV is byte-identical. The `stages` column
  is written **only** when stages > 1, so the default schema is untouched too.
* `diag_gis_matched_band_score.py`'s GATE 1 reconstructs the no-reservoir base from **all
  210 rows** of the onset-rescan CSV by subtracting `CM_PER_M*V*reservoir_unit(onset,τ)`
  rebuilt from the driver. Spread **7e-15 cm**. That is stronger than reading the base off a
  log line and it proves the CSV's 2300 column contains nothing but base + reservoir.
* The matched-target derivation CSV carries **five quantiles on two predictor arms**
  (`matched_p05..p95` = GSAT integral, adopted; `matched_Tarm_*` = 2300 level). Column names
  are **zero-padded** (`matched_p05_cm`, not `p5`).
* `diag_gis_2150_band_veto.py` imports `WINNER_CELL` and `CELL_A` from
  `scope_gis_reservoir_offline`, so the two files cannot drift on which cell is which.
* Every trap in `handoff_2026-08-23_commitment_evidence.md` §9 and `handoff_2026-08-23b` §9
  still applies unchanged (ISMIP6 positional indexing, the `os.chdir` at import, the
  identical pre-2015 hindcast, the out-of-repo pulse IRF path).

---

## 8. TRAPS ADDED THIS SESSION

* **Two scorecards with different admissible ceilings will silently disagree about which
  cells exist.** One inherited a 2.73 m high-basin ceiling, the other a 7.42 m whole-sheet
  one; the winner of the second had never been evaluated by the first. When a scan selects a
  cell, check it is **inside the grid of every other scorecard that is still live**.
* **A criterion that selects a cell by 1.4% of a band width has not validated it.** Cell A's
  2150 clearance was 0.12 cm. Report the margin, not the pass/fail.
* **When a test built to rescue a result refutes it, say so first.** The sample-size widening
  was expected to dissolve the 2150 veto (it has dissolved narrower bands in this repo
  before) and it did not: 1.6×, not 3–9×, because the two GCMs genuinely agree there.
* **Bound the FORM before scanning cells of it.** The n-fold-integral ratio killed every
  first-order (V, τ, onset) in one calculation, after two scans had explored the space
  cell-by-cell without noticing it was closed.
