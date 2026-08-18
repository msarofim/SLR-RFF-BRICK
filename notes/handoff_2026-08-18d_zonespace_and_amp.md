# Handoff — the zone-space wiring landed, and the amp test emptied the core

**Start-here document for the next session.** Repo `SLR-RFF-BRICK`, branch
**`ladrillo-dev`**, HEAD `8e37f16`, **pushed and in sync with origin**.
Predecessor: `notes/handoff_2026-08-18c_basin_arc.md`.

**Bottom line: §6's wiring is done and all four of Marcus's methodological
choices are wired as named constants. The zone-space mock reproduces the
GMT-space result cell-for-cell (the same 59 of 720) — but that is close to a
tautology and is labelled as such in the code, the CHANGELOG and memory. The
real result is the test the wiring existed to make askable: with onsets pinned
in zone units and per-zone amplification varied over its measured envelope, the
pass region is non-empty in 18/18 amp arms but NO PARAMETER CELL IS ROBUST
ACROSS THEM — the low-amp and high-amp passing sets are disjoint. The
deliverable is safe (no passing cell moves ssp126/245 at any arm). Nothing is
blocking. What is now decidable, with a measurement instead of a preference, is
the §6 item 3 pricing question.**

---

## 0. WHAT CHANGED IN ONE TABLE

| | before | after |
|---|---|---|
| §6 item 2 choices | open, awaiting Marcus | **all four answered and wired** as named constants |
| onset ↔ zone-driver map | assumed monotone | **measured** strictly increasing, every zone × window |
| ramp width W in zone space | assumed to translate | **it does NOT** — 1 K GMT = 1.58 / 2.07 / 2.66 K |
| zone-space pass region | unknown | **the same 59 cells**; ssp585 dormant loss −0.16% |
| amp uncertainty | never exercised | **18/18 arms non-empty, robust core EMPTY** |
| which zone's amp matters | expected north (wider prior) | **central dominates ~9×; north ~2×** |

Commits this session: `49c2c44` (zone-space pre-check), `92da79d` (zone-space
mock), `80b84a1` (amp sensitivity), `8e37f16` (tier-2b provenance byproduct).
All pushed. CHANGELOG entries 18i / 18j / 18k.

---

## 1. THE FOUR CHOICES, AS DECIDED

Asked and answered 2026-08-18, per the standing "methodological choices are
explicit" rule. All four are `# choice N` named constants at the top of
`scope_gis_basin_zonespace_vs_literature.py`, so a reader sees them before any
result:

1. **MID basin → the CENTRAL zone (70–77 N); HIGH → NORTH (77–84 N).** Carried
   caveat, unchanged from tier 1: central is ~CW/CE/NW latitudes, not NW
   specifically, so the mid driver is broader than the basin it stands for.
2. **Amp window = full**, both dormant zones — matching the shipped south
   choice (Ladrillo 1.0 uses south/full = 1.922). central 2.359, north 2.828.
3. **Ramp width W = GMT-equivalent per zone.** This makes the zone-space run a
   pure re-parameterisation, so any change in the pass region is attributable
   to the driver rather than to a smuggled change in W.
4. **Projection-side only.** The dormant basins are inert until 2087 at the
   earliest, so the hindcast carries no information about them. No chain run,
   no posterior moved, **L12 canonical and untouched**.

---

## 2. THE PRE-CHECK — what translated, and what did not

`python/diag_gis_zone_driver_scope.py` → `outputs/diag_gis_zone_driver_scope.csv`.

- **M1 PASS.** The GMT → zone-driver map along ssp585 is **strictly increasing**
  across the whole (3.15, 7.81] K bracket, every zone × amp window (min annual
  step 2.4e-4 K). Each GMT-space onset therefore has a unique zone-space image.
- **M2 PASS.** All 24 translated onsets stay above ssp126/245's 2300 zone
  drivers; **min margin 1.30 K** (south/modern, 4 K onset).
- **M3 — the one that did not translate.** The mock's fixed 1 K GMT ramp is
  **1.58 K (south) / 2.07 K (central) / 2.66 K (north)** in zone units. Holding
  W = 1 K in zone units would sharpen the onset by those factors. This is what
  made W a choice rather than a unit conversion.

**Zone-driver levels at 2300** (full-window amp, K in each zone's own frame):

| zone | SSP1-2.6 | SSP2-4.5 | SSP5-8.5 |
|---|---|---|---|
| south | 2.84 | 4.93 | 12.61 |
| central | 3.82 | 6.73 | 16.68 |
| north | 4.65 | 8.47 | 21.21 |

**Translated onsets** (ssp585 crossing years 2087 / 2107 / 2135 / 2179):
mid → central 5.39 / 6.46 / 7.50 / 8.59 / 10.69 K; high → north 13.55 / 16.29 /
19.00 K.

> **Anchor-window trap, now pinned in the script.** The predecessor handoff's
> per-zone anchors (south 1.9631, central 2.7667, north 3.2714) are **10-yr
> 2015–2024 means**. `regional_driver`'s splice uses **`ANCHOR_N` = 11**
> (2014–2024): south **1.9904**, central **2.7758**, north **3.2384**. Both
> right, different windows; only the 11-yr one enters the splice.

---

## 3. THE ZONE-SPACE MOCK — a consistency result, labelled as one

`python/scope_gis_basin_zonespace_vs_literature.py` →
`outputs/scope_gis_basin_zonespace_vs_literature.csv`.

- **Z1: 59/720 pass — the SAME 59 cells** (in both 59, zone-only 0, GMT-only 0).
  Ratio 10.1–17.6× vs literature 7.9–31.9×; G4 1.000–1.133× of shipped; 41
  active-mid passers, 18 single-basin.
- **Z2:** per-cell ssp585 dormant loss at 2300 moves by median **−0.0024 m
  (−0.16%)**, range [−0.0067, −0.0002] — uniformly negative, from the map's
  curvature inside the ramp. Not zero, which is what separates a real
  re-parameterisation from a no-op.
- **Z3 / Z3b PASS:** nothing activates on a low scenario that was inert in GMT
  space, and dormant loss among passers is identically 0.0 on ssp126/245.

**Do not quote Z1 as evidence FOR the basin structure.** With W GMT-equivalent
and the map monotone, the translation is close to a pure re-parameterisation
along the median-parameter ssp585 path — 59/59 is what that construction has to
produce. The warning is written into the script docstring and the CHANGELOG so
it cannot be quoted loose.

---

## 4. THE AMP SENSITIVITY — the actual result

`python/scope_gis_basin_zonespace_amp_sens.py` →
`outputs/scope_gis_basin_zonespace_amp_sens.csv` (+ `_robust_core.csv`).

**The framing is the whole test.** The onset is a property of the BASIN — the
marginal ice taps when the LOCAL temperature reaches some value — so the
zone-space onsets and widths are **PINNED** at their translated values and amp
is varied around them. Re-translating per amp would map straight back to GMT
space and, by construction, find nothing.

- **A2a PASS — the deliverable is safe.** In all 18 amp cells across both arm
  families, **no PASSING cell moves ssp126 or ssp245 at 2300**.
- **A1 — the structure survives everywhere, the parameters do not.** Pass region
  non-empty in **18/18** amp cells, size swinging **2 → 172** of 720.
- **A3 — central amp dominates, and it is the NARROWER prior.** Mean passers by
  central arm 15.3 (hi) → 49.3 (mean) → 133.7 (lo), ~9×; by north arm 40.0 →
  78.3 → 74.3, ~2×. North carries the wider spread (2.2× product range,
  N(2.83, 0.92)) but matters less: its inertness margin is large, and the
  binding constraint is 2100-keeping, which the central basin reaches first.
- **A4 — THE ROBUST CORE IS EMPTY.** Full factorial core 0 (union 284). The
  physically defensible **DIAGONAL** core — both zones moved together, since the
  two amps come from the same gridded products over adjacent latitude bands, so
  anti-correlated corners are a factorial artefact — is **also 0** (union 161,
  arm sizes 90 / 59 / 24). Evidenced pairwise rather than inferred:
  **lo&mean = 3, mean&hi = 9, lo&hi = 0.** The two ends are DISJOINT, so a
  three-way core cannot exist. **None of the 59 base passers is in any core.**

---

## 5. WHAT'S NEXT — the pricing decision, now with a measurement under it

The structure clears the 2300 scorecard at **every** amplification arm, but with
a **different** (onset, V, share, τ) cell each time. So onsets and volumes
**cannot be pinned offline independently of amp** — which was exactly the plan
the glacier precedent suggested and tier 1 was built to support. Three live
readings; **none is chosen, and this goes to Marcus**:

- **(a) Co-calibrate amp with the basin parameters.** This is now the argument
  FOR the calibrator restructure, and it is a measurement rather than a
  preference. Cost is the restructure plus a full chain; note the hindcast still
  cannot see the dormant basins, so what the chain would actually buy is the
  amp–onset covariance, not the onsets themselves.
- **(b) The onset is really a GMT-space property.** Then zone space buys nothing
  structural, one re-translates per amp, and the GMT-space mock stands as-is.
  Cheapest, and consistent with Z1 — but it means the basins do not respond to
  their own zone's temperature, which was the physical motivation.
- **(c) Ship ssp585/2300 with the 3.8–6.9× shortfall as a stated caveat.**
  §6 item 3 keeps this legitimate at every stage; the 2100 deliverable is
  unaffected throughout.

Worth noting for whichever is chosen: **A3 says the central zone is where the
information is**, which inverts the tier-2b intuition (north was the interesting
zone because its amp law came out FLAT). If any effort goes into tightening an
amp prior, it should go into central, not north.

---

## 6. THINGS THAT DID NOT SURVIVE / correction ledger

1. **The zone-driver pre-check's first draft ran two wrong tests.** It gated on
   monotonicity of the driver **time series** (SSP1-2.6 peaks and declines, so
   its driver legitimately falls — the claim is about the GMT → driver MAP), and
   it measured the **scenario spread** of the zone-driver value at each onset,
   which is **vacuous by construction**: the mock's own falsifier F3 established
   that no passing onset sits below ssp245's 2300 GMT, so ssp585 is the only
   scenario that ever crosses one. Replaced by M1 and M2's inertness margin.
2. **The same apples-to-oranges error bit TWICE**, and both times it looked like
   a zone-splice finding. Gating dormant response against **zero in absolute
   terms** charges the move to zone space for the **2.5 and 3.0 K mid onsets,
   which sit below ssp245's 2300 GMT of 3.15 K and are already active at every
   amp, in GMT space too** (unit response 0.541 and 0.114 at τ = 100, verified
   directly against `mock.dormant_unit`). First occurrence: the zone-space Z3
   gate, which reported "SSP2-4.5 not inert, 6.1e-1". Second: the amp test's A2,
   which reported 288 leaks in the mean/mean cell — i.e. the base itself. The
   gate must be **parity** (inert in GMT space ⇒ inert in zone space), plus a
   separate check on the PASSING cells. Both are recorded in the scripts.
3. Predecessor §7 items still parked: the L11-vintage memo figures at L12 (needs
   a Julia run; only if fig1/2/3 are to be shown) and the `d2_basis` one-liner
   (now four vintages deferred).

---

## 7. NON-OBVIOUS STATE

- **L12 remains canonical and untouched.** Everything this session is offline
  post-processing; no chain was run, no posterior moved,
  `LADRILLO_POSTERIOR_CSV` unchanged.
- **The two inherited modified files are down to two, and are now characterised
  rather than merely carried** (fourth handoff):
  - `outputs/mcmc/overdispersed_starts.csv` — **all 4 start rows replaced**,
    working-tree version dated **Aug 17**; backups exist at
    `.pre_extc_bak` / `.pre_l12_bak`. Committing this changes what a future
    chain starts from, so it is **Marcus's call**, not a byproduct.
  - `figures/diag_gis_regional_driver.png` — a regeneration dated Aug 10.
  The three tier-2b amp files that were also dirty (`diag_gis_amp_cmip6.png`,
  `diag_gis_amp_cmip6_summary.md`, `gis_amp_shape_fullcurve_meta.csv`) **were
  committed** in `8e37f16` — they differ only in the provenance commit field
  (`f340962` → `d59ce12`), which the predecessor handoff had already recorded.
- **A stray zero-value file sits in the WRONG repo**:
  `FaIRtoFrEDI/outputs/log_scope_gis_basin_mock.txt` (288 bytes) is just the
  "can't open file" error from a mis-`cd`'d invocation; the real log is at
  `SLR-RFF-BRICK/outputs/log_scope_gis_basin_mock.txt`. Left in place rather
  than deleted — flagged for a deliberate call.
- Untracked by convention: `outputs/log_*.txt` (this session added
  `log_diag_gis_zone_driver_scope`, `log_scope_gis_basin_zonespace`,
  `log_scope_gis_zonespace_amp_sens`), plus the raw obs `.nc` files (still
  guard-load-bearing — a re-download that changed the products would FIRE the
  driver guard and the rebuild must then be a deliberate act).
- macOS has no `timeout`; pin `OPENBLAS_NUM_THREADS=1` for anything parallel.
- `~/Documents/2026/ClaudeDocs/Papers/Mouginot/` has the paper + SI + sd01 +
  sd02; **Aschwanden 2019 and TC 19:6887 are still NOT local.**

---

## 8. FILES

**Created:** `python/diag_gis_zone_driver_scope.py`,
`python/scope_gis_basin_zonespace_vs_literature.py`,
`python/scope_gis_basin_zonespace_amp_sens.py`, this handoff.

**Modified:** `CHANGELOG.md` (entries i / j / k).

**Key outputs:** `outputs/diag_gis_zone_driver_scope.csv`,
`outputs/scope_gis_basin_zonespace_vs_literature.csv`,
`outputs/scope_gis_basin_zonespace_amp_sens.csv` (+ `_robust_core.csv`, empty
by construction — the emptiness IS the result).

**Memory touched:** `ladrillo_leq_ridge_ceiling` (new §5 + the parity-gate and
anchor-window gotchas; description rewritten around the empty core),
`INDEX_slr.md` (arc line updated).
