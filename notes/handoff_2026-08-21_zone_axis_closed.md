# Handoff — THE ZONE AXIS IS CLOSED. L14 stands. The next chain is a choice, not a queue.

**Start-here document.** Repo `SLR-RFF-BRICK`, branch **`ladrillo-dev`**.
Predecessor: `handoff_2026-08-20e_tap_wired.md`. Companion:
`spec_2026-08-21_greenland_reparameterisation.md` (read before building it).

---

## 0. THE STATE, in eight lines

* **L14 remains CANONICAL.** Nothing this session changed a shipped number.
  SLR@2100 45.01 cm / @2150 70.58 cm.
* **L15 was NOT run and should probably not be.** The `--gis-zone=all` prereqs
  were measured; the evidence turned against adopting it. See §1.
* **Per-basin drivers TESTED and REJECTED** — central/north costs hindcast
  fidelity and buys exactly no separation. See §2.
* **Four defects fixed** (figure KeyError, stale audit fixture, unpassed
  `$ADCOV` x2, nameless covariances quarantined). See §5.
* **The TAP ADMISSIBLE-SET ARM is BUILT** and repriced on L14. The cell choice is
  4.4x the reported posterior spread at 2300, and **2150 is not protected**. See §3.
* **The Greenland reparameterisation is DRAFTED, not built** — and its stated
  objective was wrong. See §5.
* **20 unconverged marginals are an AIS problem, measured.** Greenland's worst
  is R-hat 1.031. See §4.
* Nothing is running. Working tree clean at the commit this note lands in.

---

## 1. THE `all` DRIVER — measured, and the case turned AGAINST it

Handoff 20c §4 steps 1-2 ran. Both scripts zone-tag via `goc.zoned()`, so the
south provenance is untouched (md5 verified identical before/after).

Two independent confirmations the flag reaches the right inputs: `AMP_MEAN`
2.3470378 and `Tbar(2015-24)` 2.6543 K, both exactly as 20c predicts (south
1.9631; ratio **1.352x hotter**).

**The `g=0` centres** (the arm that feeds the calibrator, NOT the headline row —
the south `g=0` row reproduces the shipped `GIS_OFFLINE_G0` to every digit, which
confirms this file is its provenance):

| key | south (shipped) | all | ratio |
|---|---|---|---|
| gis_c1 | 0.032766 | 0.017221 | 0.53x |
| gis_c0 | 0.0404293 | 0.0518977 | 1.28x |
| gis_f | 0.782569 | 0.529989 | 0.68x |
| gis_alpha_f | 0.00284865 | 0.0135564 | 4.76x |
| gis_beta_f | 0.00736838 | 0.000433212 | 0.06x |
| gis_alpha_s | 0.00707271 | 7.43e-15 | **RAILED** |
| gis_beta_s | 1e-06 (railed) | 0.0145195 | 14520x |

**THE SLOW CHANNEL INVERTS, and this is the reason to refuse `all`.** The slow rate
is `1/tau_s = alpha_s*T + beta_s`. South rails `beta_s` and carries the rate on
`alpha_s` — temperature-dependent. `all` rails `alpha_s` and carries it on
`beta_s` — **constant, temperature-INDEPENDENT**. Under `all` the slow (dynamic
discharge) channel contributes the same at ssp585 as at ssp126. That is
structurally adverse to the ssp585/ssp245 2300 separation the tap exists to fix
(2.73x untapped vs a literature demand of 7.9-31.9x). `GIS_NATIVE_MU` is exactly
that pair, so adopting `all` changes WHICH TERM IS ACTIVE, not just its value.

Marcus 2026-08-21 discounted G4 as a criterion, so it is recorded but not argued
from: A+B's 2100 spread is 10.44 cm on south (fails the 6.3-7.3 window) and
7.03 cm on `all` (passes).

**(ell, w) MUST be rederived if `all` is adopted** (Marcus, 2026-08-21), and 20c's
quoted `(-3.9234, 0.94943)` are VOID — they are only what you get by KEEPING
south's `GIS_NATIVE_MU` and re-anchoring `Tbar`, which contradicts 20c's own
instruction to re-derive it. Naive rederivation puts `w` on its bound
(`ell -4.2323, w 1.36e-12`). **The convention-consistent answer**: south lifts its
railed term to carry 6.72% of the total rate, so the same fractional lift on the
now-railed `alpha_s` gives **`alpha_s = 3.94e-4` -> `ell = -4.1627, w = 0.06718`**
— the exact mirror of south's 0.9328, which is the sign the convention transferred.
NOT adopted; awaiting the zone decision.

Softening on the alarm I first raised: `gis_slow_w` is **flat on [0,1]** (sigma 1e3),
so its centre is a start value and a label, not a constraint, and `ell` moves 0.31
inside sigma 1.0. The rail matters for what the model DOES (above), not for whether
the prior is degenerate.

**20c steps 3-6 are NOT done** and should not be until the zone is decided.

---

## 2. PER-BASIN DRIVERS — tested, REJECTED, and the mechanism generalises

The component header books the cost of one driver for all basins ("a single amp
assumes the basin temperature RATIOS stay fixed, and they do not... Cheap to
revisit"). Measured: the ratio does not drift, it **REVERSES**. Regressing north on
south through the origin: **0.795** (1900-1959), **0.807** (1960-1999), **1.292**
(2000-2024). North used to be COOLER than south and is now HOTTER, so no single
(driver, amp) can serve both halves of the calibration window. The defect is real.

`scope_gis_3basin_partition.py` gained `--basins2` and
`--basin-zones=<basin>:<zone>,...`, outputs `CONFIG_TAG`-scoped. **Regression gate:
an unflagged run reproduces the committed CSV BIT-IDENTICALLY** (md5 d20efdfa...).

| | ARM A (single `all`) | ARM B (central/north) |
|---|---|---|
| s_south | 0.8107 | 0.7010 |
| s_high | 0.2165 | 0.1904 |
| **P1 total 1900-2025 miss** | **-23.3%** | **-27.1%** |
| ssp245 @2300 | 22.17 cm | 24.56 cm |
| ssp585 @2300 | 59.20 cm | 65.63 cm |
| **separation 585/245** | **2.670x** | **2.672x** |
| tap cells clearing 2300 | 0/64 | 0/64 |

**It costs and buys nothing.** The out-of-sample total degrades to -27.1%, worse
than the no-partition control (-25.1%). Mechanism: central 2.77 K / north 3.27 K
are hotter than `all` 2.65 K, so matching the same 1972-2018 Mouginot loss needs
SMALLER rate scales, which under-produce the colder early century where 64% of the
calibration signal lives.

**WHY IT CANNOT WORK, and this generalises: a rate scale CANCELS in a scenario
ratio.** `s` moved 13.5% while the ratio moved 0.07%. The separation is set by the
commitment/relaxation structure, not by the driver level, so NO choice of zone can
buy it. This extends memory `gis_two_basins_suffice` ("no structure buys the
separation") onto the driver axis, with a mechanism rather than an observation.

**Stated limitation, do not overclaim:** the harness pins the shape parameters
(c1, c0, f, alphas) and frees only `s_b`, so it is near-blind to a separation change
from drivers by construction. A full per-driver recalibration could differ, but costs
a chain. The P1 degradation is not subject to that caveat and is sufficient to stop.

---

## 3. THE TAP ADMISSIBLE-SET ARM — built, and 2150 is NOT protected

The tap is a PRIOR SPECIFICATION, not a fit, and **25 grid cells clear every
pre-registered 2300 gate**. Shipping one as a point estimate omitted the LARGER
of the two uncertainties.

**Repriced on L14 first.** `scope_gis_tap_l13.py` gains `--tag=`; two-basin
structure is detected FROM THE POSTERIOR (L14 has no `gis_s_mid`), shares then
mirroring julia `GIS2_VSHARE` exactly. **L13 default reproduces BIT-IDENTICALLY.**
The set is stable across the vintage — same 25 cells, identical membership, band
width identical at 1.180 m, everything shifted +0.020 m. Cross-check: the pricing
script puts the shipped cell at 2.303 m, exactly the tapped projection's
Greenland@2300 median of 230.27 cm, two codebases agreeing.

**The arm.** `project_ssps_components_ladrillo.jl --tap-set` runs the set and
writes per-cell series + an ENVELOPE. Cell band and posterior p05-p95 are reported
**SEPARATELY and never summed** — one is posterior spread, the other a choice among
admissible priors. It ERRORS if `GIS_TAP_CELL` is not a member (if the shipped cell
stops clearing the gates that is a finding, not a band to recentre). Non-set runs
keep the original schema.

| ssp585 (cm) | shipped | cell band | width | posterior p05-p95 |
|---|---|---|---|---|
| 2100 gis | 13.9 | [13.9, 13.9] | **0.0** | 4.8 |
| 2150 gis | 28.2 | [28.2, **139.5**] | **111.3** | 11.5 |
| 2300 gis | 230.3 | [175.3, 293.3] | **118.0** | 26.9 |
| 2300 total | 649.7 | [594.3, 713.9] | 119.6 | 253.8 |

**1. The 2100 deliverable is safe across the WHOLE set** — band exactly 0.0 at 2100
on every scenario, and exactly 0.0 at every horizon on ssp126/ssp245. The wiring
gates showed that for one cell; it holds for all 25.

**2. The 2150 horizon is NOT protected, and this qualifies the design principle.**
The cell was chosen so as not to move a horizon with independent validation, and
the shipped cell does not move 2150 (28.2 cm = untapped). That property belongs to
the ONSET, not to admissibility:

| onset | 2150 gis (cm) |
|---|---|
| 6.5, 7.0 | 28.2 (untapped) |
| 6.0 | 31.8 - 41.9 |
| 5.5 | 45.3 - 87.7 |
| 5.0 | 62.7 - 139.5 |

**15 of 25 admissible cells move 2150, by up to 5x**, and the shipped cell is TIED
AT THE MINIMUM (rank 6 of 25). So the published 2150 tapped number is the most
CONSERVATIVE admissible choice, not a central one. The 2300 gates that admitted the
other 24 never required the 2150 property.

**PRICED, so the decision is informed** — restricting the set to onset >= 6.5:

| | all 25 | onset >= 6.5 (6 cells) |
|---|---|---|
| 2150 gis band | 111.3 cm | **0.0 cm** |
| 2300 gis band | 118.0 cm | 90.2 cm (**-24%**) |
| separation ratio | 9.57 - 16.01x | 10.12 - 15.04x |

Full 2150 protection costs only 24% of the 2300 band and keeps the ratio well
inside the literature's 7.9-31.9x. **RECOMMENDED: adopt it** — the design principle
that chose the central cell should govern the SET, or the band admits cells that
principle would have rejected. Marcus's call; not applied.


## 4. DEFECTS CLOSED THIS SESSION

1. **`gis_offline_cell.py` `make_figure` KeyError 'A+B+C+D'** — the style table
   listed 8 cells while `CELLS` has had 11 since option D landed 2026-08-16, so
   EVERY run since died at the figure, discarding ~1 h of fitting. Fixed
   structurally: the table is now module-level `CELL_STYLE` beside `CELLS`, **gated
   at import**, so a missing entry fails in ~1 s naming the cell. Mutation-tested.
   `figures/gis_offline_cell_all.png` recovered from the saved series without refitting.
2. **`REPORTED_NLP = 42.522760`** in `diag_gis_g_betaf.py` — a stale literal from a
   pre-2026-08-12 vintage, making the convergence audit report a spurious "+8.9
   improvement" in BOTH zones. Now derived from `goc.OUT_FITS` (already zone-tagged).
   Verified: south -> 17.855910, all -> 33.628825.
3. **`--adcov` now passed** by `run_l11_production.sh` and
   `run_d2_stream_attribution.sh`. **Behaviour-preserving** — with `GIS_AB` on the
   preference list's first candidate already IS the file both banners name, so the
   archived chains still reproduce. It removes the TEMPLATE TRAP: Run A step 1 says
   to mirror an existing production script, and a copy with a repointed `$ADCOV`
   but no flag gets an L11-layout covariance while the banner claims otherwise.
4. **Nameless covariances quarantined** to
   `outputs/quarantine/20260821_nameless_adcov/` (README there). `adapted_cov_L13.csv`
   (59) and `adapted_cov_L14.csv` (58) carried `x1..xN` headers at canonical paths
   where the size collides with a live layout — L14's 58 IS canonical NK. The
   `size==NK` branch takes such a file AS-IS with row order assumed. Nothing read
   them. Named per-seed replacements exist and embed BY NAME.
   **STILL OPEN:** that branch still accepts any unrecognised nameless file. A general
   gate touches the hot path of every calibration and needs a run-test.

---

## 5. THE GREENLAND REPARAMETERISATION — drafted, and its premise was WRONG

Full spec: `spec_2026-08-21_greenland_reparameterisation.md`.

**20e §4 called it "the cheapest real win on convergence." The data say otherwise.**
Measured on the four L14 chains (60 sampled columns, post-warm-up half):

* R-hat > 1.01: **21** (= the "20 marginals" + `accept_rate`)
* R-hat > 1.05: **9** — and **NONE of them is Greenland**
* Worst: `ais_iceflow0` **1.777**, `antarctic_alpha` **1.602**, `ais_slope` **1.478**
* Greenland's worst is `gis_c0` at **1.031**, ranking 10th overall

**A Greenland reparameterisation will NOT lift the "projections only" caveat.** That
is gated by the AIS, which 20e §3 closed (needs an observational grounding-line
discharge constraint, not a better sampler; out of scope as decision D5).

What it WOULD buy is **sampling efficiency** — block condition number 67 with a 40%
loose direction. Real, but a different prize. Build it for that or not at all.

**A trap the spec kills.** The obvious fix on a `c1*T + c0` pair is to centre the
predictor. **Wrong here**: measured `r(c1, c0) = +0.42` only, and positive. The hub is
`gis_slow_ell`, at |r| 0.71-0.75 against ALL of c0, c1, f. The direction means a
larger commitment released more slowly through a smaller fast fraction — the
commitment-vs-rate degeneracy, the same object as `ladrillo_gis_commitment`.

Recommended transform: a **fixed orthogonal rotation** of the z-scored
{c1, c0, f, slow_ell} block along the frozen L14 loading vector. The sharpest edge is
that **bounds are not rotation-invariant** — a box does not map to a box — so gate 3
in the spec (prior-equivalence) is the one to get right.

---

## 6. NEXT — recommended order

1. **DECIDE THE 2150 GATE (§3).** Cheapest decision with the largest effect on what
   gets published, and it is already priced: adopting "must not move 2150" collapses
   the set to 6 cells, takes the 2150 band from 111.3 cm to **exactly 0.0**, costs
   only **24%** of the 2300 band, and leaves the separation ratio at 10.12-15.04x,
   well inside the literature's 7.9-31.9x. My recommendation is to adopt it: the
   design principle that selected the central cell should govern the SET too.
   Mechanically it is one filter on `outputs/gis_tap_admissible_L14.csv` plus a
   re-run of `--tap-set` (~18 min), no recalibration.
2. **THEN propagate tapped numbers to the other deliverables** (20e §4 item 4 —
   only `project_ssps_components_ladrillo.jl` has a tap arm). Do this AFTER 1, so
   what propagates is the settled band rather than a point estimate that will move.
3. **The general nameless-covariance gate** (§4 item 4), landed with a run-test.
4. **The Greenland reparameterisation (§5) — LOW priority.** It buys ESS on a block
   whose worst R-hat is 1.031, costs ~7 h of runs, and moves no shipped number.
5. **Re-price the tap if its cell moves.** Unchanged from 20e.

**NOT on this list, deliberately:** the zone axis (§1, §2). It has now cost two
investigations and returned nothing that improves the model. Marcus decided
2026-08-21 to stay on `south`; L15 is dropped.

## 7. STILL OPEN, unchanged from 20e

* D2G / D2S arms — whether re-run; bounded at ~2% of the steric effect.
* `diag_l13_projection_variant.jl` still hard-requires `:basins`.
* The eight `python/*.py` at `LADRILLO_TAG` L12/L13 — re-run individually only if a
  specific number is wanted at L14. Blanket-repointing relabels old measurements.
* Base G4 = 7.42 cm sits 0.12 cm above the four comparison models' 6.3-7.3 range.

## 8. TRAPS ADDED TODAY

* **A pipeline's exit code is its LAST command's.** `python3 ... | tee log | tail`
  reported exit 0 while Python died with a traceback; I reported a clean run that was
  not one. Check the real status, or drop the pipe.
* **`tee` without `-u` blinds you for the whole run.** An hour with no progress line
  because stdout was block-buffered. Use `python3 -u ... > log 2>&1`.
* **A cosmetic step at the END of a long run is not cosmetic** — it discards the run.
  Gate its inputs at import, where it costs a second.
* **The shell cwd resets between calls.** Relative paths silently pointed at
  `FaIRtoFrEDI/`; I briefly believed an output file had vanished. Use absolute paths.
* **A gate keyed to ONE vintage fails loudly on the next, and the failure looks
  like a code fault.** G1's reference was hardcoded to L13 (`s_high` 0.2644 vs
  L14's 0.2265), and then its POOLING differed too (L13's julia log is one chain,
  L14's is "4 chain(s) POOLED"). Both were real differences; neither was fixed by
  widening a tolerance. Key the reference by vintage, and record HOW it was
  produced, not just its value.
* **Check the ACTUAL numbers before repeating a handoff's characterisation.** "The
  cheapest win on convergence" and "20e's (ell,w) values" were both wrong, and both
  took one measurement to falsify.
