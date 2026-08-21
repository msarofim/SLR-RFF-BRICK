# Handoff — the pre-flight is done, it killed k = 2-3, and the TARGET SET is now the first job

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`.
Written 2026-08-21 at Marcus's request, to be picked up cold.

**Supersedes** `handoff_2026-08-21c_next_calibration_setup.md` for its §4 (items 1-3 and 5
are now DONE) and for its §3 framing (the routes are still the routes, but the destination
they were arguing about is now known to break two pre-registered bands).

**Read with:** `handoff_2026-08-21b_protect_matched_forcing.md` (how the PROTECT evidence was
built), `handoff_2026-08-21_protect_greenland.md` §3 (where `LIT_2300_M`'s ssp585 band came
from — this is now load-bearing), `spec_2026-08-14_next_calibration.md` (D1-D5, settled, NOT
STARTED).

Commits this handoff closes over: `2cfd53a` `4a5c165`.

---

## 0. MARCUS'S DECISION, AND THE ONE-PARAGRAPH VERSION

**The decision (2026-08-21):** do **option 1 (RE-TARGET) FIRST**. Then **option 2
(state-dependent relaxation rate)** as the preferred structural solution. Options 3-8 below
are held **in reserve** — do not spend the session on them unless 1 or 2 forces it.

The pre-flight measurements the last handoff asked for are done and they killed the thing
they were testing. The PROTECT trajectories want the model at k = 2-3 on the `phi*Leq`
ridge; the cool scenarios' 2300 bands allow only **k <= 1.25**; and re-pricing the tap
along the ridge fails at k >= 1.5 for a reason that has nothing to do with the tap. Then,
tracing why the ssp585 target is so far away, the **ssp585 2300 band every scorecard scores
against turns out to be the PROTECT `x2300` family — forced to 13.64 K at 2300 against our
ssp585's 7.78 K.** The repo already derived the forcing-matched target for our own scenario
(~100 cm, 70-230) and never propagated it into the scorecards. So the "3.5-6.3x shortfall"
that has driven this entire arc is, in part, a **comparison at two different forcings** —
the exact trap `handoff_2026-08-21c` §8 warns about. Re-target first; then fix the shape.

---

## 1. WHAT WAS MEASURED (all of it new, all of it committed)

### 1.1 Pre-flight items 1-3 — `python/scope_gis_ridge_vs_ssp_bands.py` (`2cfd53a`)

L14, per draw, 2000 draws thinned exactly as the projection driver thins. Reproduction gate
vs the shipped untapped projection: **0.00 cm** on all three SSPs at 2100/2150/2300.

| k | tau_slow | ssp126@2300 | ssp245@2300 | ssp585@2300 | 585@2100 | G4 |
|---|---|---|---|---|---|---|
| **1.00** | 55 yr | **0.101** OK | **0.183** OK | 0.499 | 13.95 | 7.46 |
| 1.25 | 86 yr | 0.122 OK | 0.216 OK | 0.587 | 14.25 | 7.20 |
| 1.50 | 116 yr | 0.139 OK | **0.243 out** | 0.662 | 14.60 | 7.15 |
| **2.00** | 174 yr | **0.167 out** | 0.289 out | 0.795 | 15.18 | 7.17 |
| **3.00** | 290 yr | 0.203 out | 0.349 out | 0.990 | 15.87 | 7.27 |
| 12.0 | 1321 yr | 0.279 out | 0.489 out | **1.463 <- peak** | 17.08 | 7.56 |

* **Q1 (cool scenarios) KILLS k = 2-3.** Bands hold only at **k <= 1.25**. ssp245 leaves at
  k = 1.5, ssp126 at k = 2.0. At k = 3 they are 1.25x and 1.60x over band top.
* **Q2 (G4) does not kill it** — 0.96-1.01x of k = 1 over k = 1-16; breaks only at k >= 32.
* **Q3 (AR6 2100) does not kill it** — ssp585@2100 stays in ~9-18 cm at EVERY k on 1-50.
* **The ridge CEILING moved at L14**: peaks at **1.463 m (k = 12)** vs L12's 1.794 m
  (k = 14), so **no k reaches the ssp585 band at all** — 1.18x short of its FLOOR. This is
  exactly the absolute level `2026-08-21c` §6 said must be re-derived, not quoted.
* The handoff's premise that k = 2-3 "was never scored" was wrong: the L12 grid DID include
  2.0 and 3.0 and already failed there. What was missing was L14 per draw. The conclusion
  survived the re-derivation; the framing did not.

### 1.2 Pre-flight item 5 — the tap re-priced (`4a5c165`)

`python3 python/scope_gis_tap_l13.py --tag=L14 --k=1,1.25,1.5,2,3` (new `--k=` flag; V grid
refined 0.5 -> 0.25 m for the scan; 360 cells per k).

| k | base 585@2300 | ratio | high head | passing | V range | ratio range |
|---|---|---|---|---|---|---|
| 1.00 | 0.499 | 2.73x | 2.58 m | **43/280** | 1.50-2.50 | 2.73-**16.00x** |
| 1.25 | 0.587 | 2.72x | 2.57 m | **52/280** | 1.25-2.50 | 2.72-13.98x |
| 1.50 | 0.662 | 2.73x | 2.57 m | **0/280** | — | 2.73-12.73x |
| 2.00 | 0.795 | 2.75x | 2.56 m | **0/280** | — | 2.75-11.19x |
| 3.00 | 0.990 | 2.83x | 2.55 m | **0/280** | — | 2.83-9.78x |

* **Above k = 1.25 nothing passes, and NOT for a tap reason.** The failing criterion is the
  2300 LEVEL bands (0/280 at every k >= 1.5), failing on **ssp126/ssp245 — which the tap
  provably never touches** (G2b). The ratio band still has 41/28/17 passers. Same Q1 base
  failure through a second scorecard. **The tap and the ridge do not compose.**
* **Raising k makes the tap's job HARDER** — best achievable ratio falls **16.00x -> 9.78x**
  over k = 1->3, because the ridge lifts ssp245 (1.9x) nearly as fast as ssp585 (2.0x), so
  the same V buys less separation against a bigger denominator. §4 item 5's "much smaller
  tap, or none" is **backwards**; it holds only as a 1.2x effect at k = 1.25 (smallest
  passing V 1.50 -> 1.25 m).
* **The inventory is NOT binding** — head moves 2.58 -> 2.55 m against 2.73 m Mouginot. The
  obvious "a bigger commitment eats the tap's headroom" hypothesis is measured FALSE.

### 1.3 The headline metric is reproducible now

The RMS log-misfit that the whole k = 2-3 recommendation was reported on was computed ad hoc
and never written to the CSV. It is a column in `scope_gis_ridge_vs_protect.py` now and
**reproduces the 2026-08-21e table exactly** (k=1 0.497, k=2 0.294, k=3 0.293, 1.70x worse
at shipped). Two things the old grid hid: k=8 is 0.408, and **k=22.6 is 0.304** — a second,
nearly-as-good lobe past the V0 clip. The optimum is double-lobed, not simply interior.
Band membership saturates at 5/8 across most of the ridge and does NOT locate the optimum;
the script prints both and says which is which.

---

## 2. THE FINDING THAT REORDERS EVERYTHING — DO THIS FIRST (option 1)

**`LIT_2300_M["SSP5-8.5"] = (1.732, 3.127) m` IS THE PROTECT `x2300` FAMILY.**
`handoff_2026-08-21_protect_greenland.md` §3 records the independent validation: the
hand-transcribed band is sourced "SSP5-8.5-ext from IPSL-CM6A-LR and CESM2-WACCM", and our
own x2300 extraction reproduces it (p05 217.9 / p50 233.6 / p95 301.1 cm). That family's
GSAT is **13.64 K at 2300**. Ours is **7.78 K**. That is a factor of 1.75 in warming anomaly.

The repo already knows what the forcing-matched target is — `[[protect_matched_forcing]]`:
**~100 cm (70-230) for our own ssp585@2300**, interpolated between two measured matched
plateaus (r2300 5.61 K -> 72.3 cm, x2300 13.59 K -> 234.4 cm). Against THAT, the untapped
base at 50.0 cm is **2x low, not 3.5-6.3x low**, and the shipped tap at 230.3 is 2.3x high.

**None of the scorecards were ever updated.** `scope_gis_leq_ridge_vs_literature.py`,
`scope_gis_ridge_vs_ssp_bands.py`, `scope_gis_tap_l13.py`, `scope_gis_basin_mock_vs_literature.py`,
`scope_gis_rate_power_vs_literature.py` and the two plotters all import or copy `LIT_2300_M`
unchanged. Every "SHORT by 2.9x", every "0/3 @2300", every ratio band, inherits the mismatch.

### 2.1 The job, concretely

1. **Establish the forcing of every band in `LIT_2300_M`, not just ssp585.** The ssp585
   mismatch is VERIFIED. The two cool bands are labelled "stabilised" / "stabilised+ext"
   and their forcing level is **UNCHECKED** — that is the single highest-value unknown in
   the repo right now, because **Q1's kill depends entirely on those two bands**. Our own
   ssp126 plateaus at 1.74 K and ssp245 at 3.15 K by 2300 (measured, `fair_mean_gmst_*`).
   If the literature's stabilised arms sit near those levels, Q1 stands as written. If they
   sit higher, k <= 1.25 loosens.
2. **Build a forcing-matched target set** and put it in ONE place that every scorecard
   imports (they currently copy the dict — `plot_gis_basin_mock.py:47` and
   `plot_gis_rate_power_scan.py:46` carry their own literals). Name it so it cannot be
   confused with the raw literature bands; keep BOTH, and make every printout say which
   it is scoring against.
3. **Re-run the three scorecards on the new targets**: the ridge-vs-ssp-bands scan, the tap
   k-scan, and the ridge-vs-protect scan. Expect the verdicts to move. Report the DELTA
   against today's table above, not just the new numbers.
4. **Re-score the two single-law variants that were declared dead** under the new targets
   (Leq ridge 3.36x, rate-power 4.71x on the ratio) — they were killed by a ratio band built
   from the same mismatched pair, so the death certificate is suspect. This is option 4 in
   reserve, but the re-score is nearly free once step 2 exists.

**Falsifier, stated before running:** if the matched-forcing target for ssp585@2300 lands
inside 70-230 cm and the cool bands turn out to be near our plateaus, then the model needs
about a **2x** lift at 2300 with 2100 held — which is a shape problem, not a scale problem,
and option 2 is the right next move. If instead the cool bands are also mismatched and
loosen a lot, re-open k on the ridge before building new physics.

---

## 3. THEN: OPTION 2 — A STATE-DEPENDENT RELAXATION RATE

**Why this one.** The base model's error against matched forcing is a **rotation in time**,
not a gain:

| ours / PROTECT | 2100 | 2150 | 2300 |
|---|---|---|---|
| r2300 (5 GCMs, 5.58 K plateau) | 1.18 | 0.89 | **0.49** |
| x2300 (2 GCMs, 9.8-13.6 K) | 1.63 | 0.97 | **0.38** |

Too high early, right in the middle, too low late, with a **7.2x late-rate deficit under
CONSTANT forcing** (3.7 vs 26.7 cm/century over 2200-2300). `k` is a SCALE. A scale cannot
fix a rotation — which is precisely why the 2100 over-prediction is ridge-INVARIANT and why
every scan since 2026-08-14 has hit the same wall.

**The form.** `r = r0(T) * (1 + gamma * L / (k_b * V0))` (or an equivalent state feedback),
so the relaxation ACCELERATES as loss proceeds. Physically this is the elevation-SMB
feedback plus marine-terminus retreat. It is the only candidate on the list that produces
the diagnosed signature — convexity under CONSTANT forcing — rather than a bigger endpoint.

**Why it should be cheap.** Over 1900-2025, `L/V0 ~ 0.008`, so the feedback is nearly inert
on the likelihood. If that holds when measured, `gamma` can be **prior-propagated exactly
like `gis_amp` and the tap** — no chain, no refit, projection-side only. **MEASURE IT, do
not assume it**: compute `max |r_with - r_without|` over the calibration window before
claiming inertness, the same way G2 does for the tap.

**Build it offline first** (`[[offline_emulator]]`): the harness already exists. Add the
feedback to `basin2_series` in `scope_gis_ridge_vs_protect.py` behind a `gamma` argument
(default 0.0 => bit-identical, which is the G3-style nesting gate), then score gamma against
the PROTECT trajectories with the RMS log-misfit column that is now in the CSV. Do NOT touch
`greenland_3basin_component.jl` until a gamma clears offline.

**What to watch.** (a) 2100 must not move — the feedback is small early by construction, but
assert it. (b) The V0 clip interacts: a faster rate against a saturating target can still
flatten, so check the clip's role before concluding gamma is inert or ineffective. (c) The
hindcast: unlike k, gamma does NOT trivially preserve it, so re-solve or re-check.

---

## 4. IN RESERVE — do not start these without a reason

3. **A third, genuinely slow reservoir** (own commitment, centuries-to-millennium tau). The
   conservative fallback if gamma fails: it adds late rise without moving 2100, and it
   ESCAPES the ridge scan's objection (lengthening an existing channel's tau lowers 2300
   because the commitment is fixed; a new channel ADDS commitment). This is "the tap done
   properly" — a reservoir instead of a GMT-triggered volume step.
4. **Nonlinear / threshold `Leq(T)`.** Two single-law variants already priced and dead — but
   against the suspect ratio band; see §2.1 step 4.
5. **Drop the saturating clip.** MEASURED: removing one clip cuts the shape error 2.2x and
   the 2150 overshoot 2.3x, no new machinery. Cheapest structural change with a measured
   benefit. **But it sits inside an unresolved contradiction in our own evidence:** every
   physics-tracking shape form gives **~19 cm** on our ssp585 at 2300 against the
   plateau-interpolated bracket of **70-230 cm**, a 4-12x gap. Resolve that before adopting
   any shape form. (It may well dissolve under §2 — both numbers are targets-side.)
6. **Hysteresis / peak-warming commitment** — `Leq` on max T reached. Separates scenarios
   naturally. Untested here.
7. **Emulate an ISM directly** (PROTECT / ISMIP6 / emuGrIS, or the Mengel approach already
   used for glaciers in MimiBRICK-FM). High cost; coverage caveat severe past 2100 (ONE
   model, TWO GCMs).
8. **Re-scope the deliverable** — ship 2150 (base matches physics to 3-11% on both
   families) and give 2300 as a literature-anchored range with the structural caveat. The
   honest floor if nothing else converges.

**Companion, independent of the choice:** effective `amp*S` is pinned at **1.65** against the
forcing GCMs' **1.31-1.54**, so we feed Greenland 7-27% too much warming even at matched
GMST. It needs the amp law's **SUPPORT EXTENDED** — a new measurement.
**`gis_amp_shape_fullcurve` was run and is nearly inert; do NOT re-propose it.** This is the
only item that attacks the 2100 over-prediction, which nothing in §2-§4 touches.

---

## 5. STILL NOT DONE

* **§4 item 4 of the previous handoff** — whether a REFIT can reach the hindcast at a moved
  k without railing `gis_slow_ell`. Needs the calibrator, not an offline scan. Note it is
  now much less urgent: k > 1.25 is out on the cool bands anyway.
* **The D1-D5 change set** (`spec_2026-08-14_next_calibration.md`): D1 drop the total
  (`dang`) stream, D2 discrepancy on gsic+steric only, D3 moot given D1, D4 keep sampling
  `gis_amp`, D5 AIS grounding-line constraint OUT. 54 -> 52 params. **Rebuild starts and
  `adapted_cov` BY NAME** (`[[nameless_matrix_order]]`). Orthogonal to everything above and
  still applies whichever option wins.
* **No chain has been started.** No gate changed, no cell moved, the admissible set is still
  25 (140-cell basis) / 43 (360-cell basis, L14).
* The Greenland reparameterisation spec is still DRAFT and its own §1 shows the convergence
  case is weak. **The real unconverged mass is AIS** (`ais_iceflow0` 1.777, `antarctic_alpha`
  1.602, `ais_slope` 1.478). Do not spend a calibration on the Greenland block's convergence.

---

## 6. NON-OBVIOUS STATE — READ BEFORE TOUCHING THE SCANS

* **`scope_gis_ridge_vs_protect.py`'s body moved into `main()`** so its gated two-basin
  kernel (`basin2_series`, `rebase_cm`) can be IMPORTED rather than retyped. Output verified
  **byte-identical** to the committed CSV apart from the new `rms_log_misfit` column. Import
  from it; do not re-implement the kernel a fourth time.
* **`scope_gis_tap_l13.py` now takes `--k=`.** Without it the file behaves exactly as before
  and reproduces the published 25/140 (verified byte-identical apart from a `k_c` column).
  With it, `OUT` gains a `_kscan` suffix so a scan CANNOT overwrite the k = 1 artefact the
  shipped cell rests on. The filename is still `_l13` for historical reasons; `--tag=` is
  the authority.
* **The k = 1 ROW of any ridge scan is NOT the shipped model.** Every row re-bisects the
  rate onto the hindcast target and the shipped posterior does not sit exactly on it
  (s = 1.0167 at k = 1). The GATE block, at s = 1, is the shipped model. Both scan scripts
  now say so in their own output.
* **`HIND_DRIVER` is not exactly inert.** `t_gis_zones` ends in **2024**, so 2025 — one year
  of the 1900-2025 hindcast window — is already spliced and scenario-dependent (0.043 K).
  The L12 scan called it inert on the assumption history is fully observed. Measured
  consequence: re-solving under each scenario's history moves 2300 by **< 0.001 cm**, so it
  is inert IN CONSEQUENCE, which is the claim that was needed. The check is in the script
  and is scored in cm, not K.
* **`scope_gis_leq_ridge_vs_literature.py` is still L12, single-basin A+B, median
  parameters.** It is the ancestor, not a current scorecard. Its RATIO and
  relative-to-k=1 conclusions transfer; **its absolute levels do not** — the ridge ceiling
  moved 1.794 -> 1.463 m between L12 and L14. Import its BANDS and helpers, not its numbers.
* `scope_gis_2300_relaxation.py` has still not been audited against the three gate bugs
  (`gis_g` fixed 0, `gis_s_high` log10, driver rebase). Its `gmst_rebased` uses the correct
  `DRIVER_BASE`, and it has no basins, so bugs 1 and 3 do not apply — but it runs at median
  parameters and nothing else in it has been re-checked.

---

## 7. FILES

**New** — `python/scope_gis_ridge_vs_ssp_bands.py`; `outputs/scope_gis_ridge_vs_ssp_bands.csv`;
`outputs/scope_gis_tap_l14_kscan.csv`; logs `outputs/log_scope_gis_ridge_vs_ssp_bands.txt`,
`outputs/log_scope_gis_ridge_vs_protect.txt`, `outputs/log_scope_gis_tap_l14_kscan.txt`.

**Modified** — `python/scope_gis_ridge_vs_protect.py` (body into `main()`; `rms_log_misfit`
column; best-by-RMS printed alongside best-by-band-count),
`python/scope_gis_tap_l13.py` (`--k=`, `price_at()` extracted, `run_3basin(T, p, k_c, s_r)`,
`_kscan` output suffix), `CHANGELOG.md` (entries 2026-08-21f and 2026-08-21g).

**Memory updated** — `gis_ridge_broken_by_protect` (pre-flight verdict),
`gis_tap_priced_l13` (the re-pricing), `INDEX_slr.md` (both lines).

---

## 8. TRAPS

* **A comparison at two different forcings is not a comparison.** This has now bitten this
  dataset TWICE: the 2026-08-21a reading was inverted by it, and §2 shows the ssp585 2300
  target band has been carrying it the whole time. Before quoting any external number as a
  target, state the forcing it was produced at.
* **The k = 1 row is not the shipped model** (see §6). Do not read a scan row as a
  deliverable.
* **Band membership does not locate an optimum.** It saturates at 5/8 across most of the
  PROTECT ridge. Use `rms_log_misfit`.
* **`--untapped` before any ratio.** "3.5x too high" is uninterpretable until the base model
  and the tap are separated.
* **The admissible set is scored against a k = 1 base AND against the suspect target set.**
  Both reasons void it independently.
* **Sensitivity arms have to be RUN**, not reasoned about. `gis_amp_shape_fullcurve` was
  argued to be the amp fix and measured to be nearly inert.
* **Do not widen a gate to make a new vintage pass.** `G1_REF` in the tap pricer is keyed by
  vintage for exactly this reason; add a row transcribed from the Julia log instead.
