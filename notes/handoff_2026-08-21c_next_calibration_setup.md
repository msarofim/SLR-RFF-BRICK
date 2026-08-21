# Handoff — setting up the next calibration, now that the ridge is breakable

**Start here for the calibration.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`.
Written 2026-08-21 at Marcus's request, to be picked up cold.

**Read with:** `handoff_2026-08-21b_protect_matched_forcing.md` (how the PROTECT
evidence was built), `spec_2026-08-14_next_calibration.md` (the D1-D5 change set,
settled and NOT STARTED), `spec_2026-08-21_greenland_reparameterisation.md` (DRAFT;
its §1 already argues the convergence objective is not the one the data support).

Commits this handoff closes over: `2c1687b` `860742d` `07b0883` `c0ce0ee` `27f0061`
`02c6774` `be59e74` `9f24a12` `a93daed` `cd5d7d7` `b5484bf` `778631e`.

---

## 0. THE ONE-PARAGRAPH VERSION

L14 is canonical and the tap ships at (6.5 K, 2.0 m, 50 yr). New physics evidence
(PROTECT-Greenland, Goelzer 2025) run at **matched forcing** says three things:
the tap is too EARLY and the wrong SHAPE; the base model is **not convex enough in
time** on two independent forcing families; and — the actionable one — the
**`phi*Leq` degeneracy that has blocked this since 2026-08-14 is breakable**, by
scoring on 200 years of trajectory instead of a 2300 endpoint. The ridge has an
**interior optimum at k = 2-3** (`tau_slow` 175-290 yr against the shipped 55), and
the shipped k = 1 is **1.7x worse**. Nothing has been changed. The calibration
decision is whether, and how, to move the model onto that ridge point.

---

## 1. WHAT IS NEW SINCE THE LAST CALIBRATION SPEC

`spec_2026-08-14_next_calibration.md` was written when the commitment/rate ridge
was believed **unidentifiable from the data we had**. Its framing — "the
identifying constraint must be an external `Leq(T)` target" — is now out of date.

It is not out of date because an `Leq(T)` target appeared. Option C (the Bochow
ladder) is still dead ([[ladrillo_option_c]]). It is out of date because **the
identifying constraint turns out not to have to be an `Leq(T)` target at all**: a
time-resolved *trajectory* under a known forcing identifies the ridge coordinate
directly, because moving along the ridge changes `phi(t)` even though it leaves the
1900-2025 endpoint invariant.

That is the whole opening. Everything below follows from it.

---

## 2. THE MEASUREMENT (`python/scope_gis_ridge_vs_protect.py`)

Per-draw, ensemble-median, hindcast held by per-draw bisection at every k so it
never discriminates. Scored against the PROTECT medians at 2100/2150/2200/2300 on
**both** families.

| k | `tau_slow` | RMS log-misfit (8 horizons) |
|---|---|---|
| **1.0 shipped** | **55 yr** | **0.497** |
| 1.5 | 116 yr | 0.349 |
| 2.0 | 175 yr | 0.294 |
| **3.0** | **290 yr** | **0.293 — best** |
| 5.0 | 521 yr | 0.356 |
| 14.0 | 1553 yr | 0.392 |
| 50.0 | 5304 yr | 0.644 |

The optimum is **interior and two-sided**. Misfit rises again past k ~ 5 because
`Leq` clips at `V0 = 7.42 m` — the same non-monotonicity
[[ladrillo_leq_ridge_ceiling]] found from the endpoint side, now reproduced from
the trajectory side. That agreement between two independent scorings is the best
evidence the scan is measuring something real.

**The ridge-invariant residual.** 2100 is over-predicted **1.2-1.4x (r2300)** and
**1.6-1.9x (x2300)** at EVERY k. Moving along the ridge does not touch it. The
independently measured amp excess (ours 1.65 vs the forcing GCMs' 1.31-1.54)
covers part of the r2300 half and not the x2300 half. **This is a second, separate
defect and it should not be folded into the k decision.**

---

## 3. THE DECISION THE CALIBRATION HAS TO MAKE

The scan says where the physics wants the model. It does **not** say how to get it
there, and the three routes are genuinely different commitments:

**(A) Prior-propagate k, no refit.** Scale `(c1, c0)` by k and re-solve the rate to
hold the hindcast, as the scan does. Cheap, reversible, no new posterior. But the
rate re-solve is a point transformation of a *sampled* pair, so the resulting
ensemble is not a posterior of anything — it is a reweighted prior. Defensible only
if labelled that way in every deliverable, and it cannot claim the hindcast
uncertainty it inherits.

**(B) Refit with a PROTECT-derived projection term in the likelihood.** The honest
version of (A). But it puts **one ice sheet model (NORCE-CISM)** into the
likelihood of a calibrated emulator, and the coverage caveat is severe: past 2100
the whole PROTECT long-run sample is NORCE-CISM — x2300 is 2 GCMs across several
CISM configs, r2300 is 5 GCMs through ONE config. Neither is structural-uncertainty
sampling. **My recommendation is not to do this as a likelihood term.**

**(C) Refit with a widened / re-centred PRIOR on the commitment, PROTECT used only
to justify the prior.** Keeps the likelihood on observations, moves the thing the
observations genuinely cannot identify, and states the external evidence where it
belongs. **This is the route I would take**, and it composes cleanly with the
D1-D5 change set because it is a prior edit, not a likelihood edit.

Marcus's call. Nothing below depends on which is chosen except §4 item 4.

---

## 4. PRE-FLIGHT — MEASURE THESE BEFORE ANY CHAIN RUNS

None of these has been done. Each is cheap and each can kill k = 2-3.

1. **The cool scenarios at k = 2-3.** The 2026-08-18 endpoint scan found every k
   that repairs ssp585 breaks ssp126/ssp245. It tested k >= 12; **k = 2-3 was never
   scored against the ssp126/ssp245 2300 literature bands.** Reuse
   `scope_gis_leq_ridge_vs_literature.py`, which already has those bands — but
   **port the three gate fixes in §6 first**, it runs at median parameters and its
   `gis_s_high` handling must be checked against them.
2. **The 2100 G4 spread**, relative to k = 1, against the 15% degradation tolerance
   already coded in that script. k = 1.05x was the earlier finding at high k; at
   k = 2-3 it is unmeasured.
3. **AR6 2100.** Greenland@2100 must stay in 9-18 cm. At k = 3 the r2300 arm reads
   1.33x the physics at 2100 — check what that does to the ssp585 2100 deliverable.
4. **The hindcast, properly.** The scan holds 1900-2025 by construction via a rate
   re-solve. A real refit does not get that for free: confirm the likelihood can
   actually reach the hindcast at k = 2-3 without railing `gis_slow_ell`.
5. **The tap, re-priced.** A base model with k = 2-3 needs a much smaller tap, or
   none. `GIS_TAP_CELL` and the 25-cell admissible set are both scored against a
   k = 1 base and **every one of them becomes meaningless the moment k moves.**
   Do not carry the shipped cell across.

---

## 5. WHAT ELSE IS ALREADY ON THE TABLE FOR THIS CALIBRATION

One change set, because each item invalidates the posterior
(`spec_2026-08-14_next_calibration.md`'s own argument):

* **D1** drop the total (`dang`) stream; **D2** discrepancy on gsic+steric only;
  **D3** retained as a check, moot given D1; **D4** keep sampling `gis_amp`;
  **D5** AIS grounding-line constraint OUT. `sd_dang`/`rho_dang` leave the vector,
  54 -> 52 params. **Rebuild starts and `adapted_cov` BY NAME** ([[nameless_matrix_order]]).
* **The Greenland reparameterisation** (`spec_2026-08-21_...`) is DRAFT and its §1
  shows the convergence case is weak — the Greenland block is already at R-hat
  1.001-1.031. The real unconverged mass is AIS (`ais_iceflow0` 1.777,
  `antarctic_alpha` 1.602, `ais_slope` 1.478). **Do not spend this calibration on
  the Greenland block's convergence.**
* **`gis_amp`.** The PROTECT GCMs put Greenland/global amplification at 1.31-1.54
  where our effective `amp*S` is pinned at **1.65** by the S table's flat-hold. The
  `fullcurve` arm was run and is **nearly inert** (do not re-propose it — both
  tables flat-hold above 5.75 K and the comparison runs at 9.8-13.6 K). If the amp
  is to move, it needs the law's **SUPPORT extended**, which is a new measurement,
  not a table swap.

---

## 6. NON-OBVIOUS STATE — READ BEFORE TOUCHING THE OFFLINE SCANS

`python/scope_gis_ridge_vs_protect.py` failed its 0.5 cm reproduction gate **by
30 cm**. The tolerance was not widened. Three real bugs, every one one-signed and
growing with time:

1. **`gis_g` is FIXED AT 0** (`LADRILLO_GIS_G`) — both channels start at zero, not
   at `f*eq[0]`.
2. **`gis_s_high` is LOG10** in the posterior. The Julia does
   `10.0^row["gis_s_high"]`. The raw median is **-0.6451**, i.e. a NEGATIVE rate
   scale that clips to the 1e-9 floor and freezes the high basin; the linear value
   is **0.2264**. Memory's "s_high 0.2265" is the LINEAR number.
3. **The GMST driver rebases on `DRIVER_BASE = (1850, 1900)`**, not the 1995-2014
   SLR reporting baseline. Two windows, two different quantities.

Gate now passes at **0.16 cm** worst-case, both families, all four horizons.
Median-parameters vs ensemble-median was worth **under 2 cm** and was NOT the fix —
do not reach for that explanation when a residual is one-signed and growing.

**The other offline scans have not been audited against bugs 1-3.**
`scope_gis_leq_ridge_vs_literature.py` and `scope_gis_2300_relaxation.py` predate
this and run at median parameters. Their RATIO and relative-to-k=1 conclusions
should survive; **any absolute level from them should be re-derived, not quoted.**

---

## 7. FILES

**New and committed** — `python/`: `reduce_cmip6_gsat_ssp585ext.py`,
`build_protect_x2300_forcing.py`, `build_protect_r2300_forcing.py`,
`scope_gis_tap_shape.py`, `scope_gis_ridge_vs_protect.py`,
`plot_protect_forcing_matched.py`, `plot_protect_r2300_matched.py`;
`julia/diag_protect_forcing_matched.jl` (`--family=` `--set` `--untapped`
`--scan=` `--unsmoothed`); `scripts/fetch_cmip6_ssp585ext.sh`.

**Modified** — `python/extract_protect_greenland.py` (now also writes annual series
for long runs); `julia/project_ssps_components_ladrillo.jl` (**latent defect fixed**:
`LADRILLO_GIS_SHAPE` now reaches the output filename via `SHAPE_TAG`, so running a
shape arm can no longer overwrite the shipped deliverable under its own name).

**Data** — `data/cmip6_gsat_ext/*.nc` gitignored, re-fetch with
`bash scripts/fetch_cmip6_ssp585ext.sh` (md5-pinned). r2300 needs **no** post-2100
CMIP6: forcing held at 2100 means the Pangeo mirror suffices.

**Pending / not run** — every item in §4. No chain has been started.

---

## 8. TRAPS

* **The Pangeo CMIP6 zarr mirror has no post-2100 data** for any member of either
  x2300 GCM, while still advertising `experiment_id == "ssp585"`. Check `time[-1]`.
* **A comparison at two different forcings is not a comparison.** The 2026-08-21a
  reading of this same dataset was inverted by exactly that.
* **`--untapped` before any ratio.** "3.5x too high" is uninterpretable until the
  base model and the tap are separated.
* **The admissible set is scored against a k = 1 base.** Moving k voids all 25 cells.
* **Sensitivity arms have to be RUN.** A CHANGELOG draft here attributed the
  splice-vs-raw difference to smoothing before `--unsmoothed` had been run.
