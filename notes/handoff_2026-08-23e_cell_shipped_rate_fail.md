# Handoff — the cascade cell IS SHIPPED, the finalization queue is CLOSED, and the rate criterion it had never been scored on comes back a 1.055× FAIL

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, through `939e631`.
Written 2026-08-23, to be picked up cold.

**Supersedes** `handoff_2026-08-23d_cell_chosen_finalization.md` — **all six items of
its §3 queue are DONE**. Its §1 (the decision and the reasoning), §2 (what was already
wired) and §5–§6 (non-obvious state, traps) are **unchanged and still load-bearing**.

---

## 0. THE ONE-PARAGRAPH VERSION

`GIS_TAP_CELL` is now the 2-stage cascade — **V = 6.0 m, τ = 800 yr, onset 4.69 K,
whole-sheet** — and everything downstream of that flip is done: the test rewrite, the
regenerated deliverables, the quarantine, the stale-label sweep. Greenland ssp585@2300
is **98.7 cm** and the 585/245 separation **5.39×**. The one item that was open
evidence rather than mechanics — the **2250–2300 rate criterion**, never run at n = 2 —
now has an answer, and it is a **FAIL at 1.055× the band top**, robust to how the band
is built but with a margin of 2.3 cm/century on a band 4.3× wide. **It is not
structural** (16/72 cascade cells clear all four gates) and **the price of fixing it is
2.6% of the 2300 level** (V 6.0 → 5.66 m). That trade is a methodological choice and
is left for Marcus.

---

## 1. THE OPEN DECISION — the only thing waiting on you

**Does the 2250–2300 rate band join the shipped cell's selection criteria?**

| | V = 6.0 m (SHIPPED) | V = 5.66 m |
|---|---|---|
| our ssp585 Greenland@2300 | **98.6 cm = 1.001× the matched p50** | 95.9 cm = 0.974× |
| r2300 2250–2300 rate | **43.8 = 1.055× the band top** | 41.5 = exactly at the top |
| 2100 | exactly inert | exactly inert |
| both ssp585 2150 bands | IN | IN |
| matched 2300 band [42.9, 145.0] | IN | IN |

Everything else is identical — same n, same τ, same onset, same home. It is a 5.7% cut
in V.

**The case for keeping V = 6.0.** The cell was chosen on the between-scenario criterion
and to land the matched p50, and it does both better than anything else in the scan.
The rate band is **4.3× wide** and rests on **5 GCM clusters**; 2.3 cm/century is inside
what that ensemble can resolve. And this repo has twice been burned by gates tighter
than the evidence behind them.

**The case for moving to ~5.66.** The rate criterion is **one of the two independent
sources that pinned the flux** (the other is Greve at 3001), it is the criterion that
selected cell A over cell B in the first place, and the fail survives every band
construction tried — GCM-clustered (1.19× over) and all five leave-one-GCM-out variants
(0/5). Buying it costs 2.6% of a number whose own band is 42.9–145.0 cm.

**My read, offered not assumed:** the price is small enough and the criterion
independent enough that V ≈ 5.66 is the better-defended cell — but it trades away the
"lands exactly on the p50" line, which several written outputs lean on, and that is a
presentation cost only you can price. **Nothing is changed pending your call.**

Reproduce either side with:

```
python3 python/diag_gis_cascade_rate_crit.py --scan
```

---

## 2. WHAT IS NOW DONE — DO NOT REDO IT

1. **`GIS_TAP_CELL` FLIPPED** (`1246f2f`) to
   `(onset_K = 4.69, V_m = 6.0, tau_yr = 800.0, ramp_w_K = 1.0, stages = 2.0,
   wholesheet = true)`. The **component's build-time defaults deliberately STAY** at
   first-order / high-basin (`GIS_TAP_STAGES_DEFAULT = 1.0`, `GIS_TAP_WHOLESHEET_OFF`),
   so building `greenland_3basin` without asking for the tap is bit-identical to
   everything predating 2026-08-23. `update_gis3_tap!` and `ladrillo_set_tap!` default
   their two capability keywords to **the cell's**, so switching the shipped tap on is
   one call with no keywords. That is the "safer form" §3.1 of the previous handoff
   asked for.
2. **`--tap-set` passes `stages=1, wholesheet=false` EXPLICITLY.** Its cells were priced
   first-order and the new setter defaults would otherwise have silently re-run an
   admissible set as cascades. Its membership check still errors on the new cell, and
   the message now says why: every set on disk was priced on a refuted form.
3. **The filename carries the cell in full**: `_tap4p69K_V6p0m_tau800_n2_ws`. Stage
   count and home are in there because a cascade and a first-order run at the same
   (onset, V, τ) would otherwise collide on one name.
4. **[G2] REWRITTEN AS TWO GATES OF DIFFERENT KIND** — see §3.
5. **DELIVERABLES REGENERATED**, both the default arm and the
   `LADRILLO_GIS_SHAPE=gis_amp_shape_fullcurve` sensitivity arm, at 2000 draws.
6. **SUPERSEDED OUTPUTS QUARANTINED** at `outputs/quarantine/20260823_old_tap_cell/`
   with a README recording the refutation, the size of the change, and how to reproduce
   the old arm. Bulk CSVs stay on local disk untracked (matching every other quarantine
   dir); README and run logs are tracked.
7. **THE RATE CRITERION IS RUN** — §4.
8. **`.gitignore`** now covers the three gridded surface-temperature NetCDFs (0.5 GB)
   that made `git add -A` stall. That trap is gone.

**ALL GATES PASS**: `test_gis_tap_wiring.jl`, `test_greenland_3basin_nesting.jl`,
`test_ladrillo_basins2_variant.jl`, `test_gis_ordering_wedge.jl`.

---

## 3. THE TEST REWRITE, AND WHY IT IS TWO GATES

`[G2]` used to assert *"ssp585 total at 2100 AND 2150 is UNMOVED"* — one identity gate
covering two horizons that are **not the same kind of claim**.

* **2100 stays EXACT.** It is the horizon with independent validation (ISMIP6, 16
  models), and the shipped tap is inert there by construction: the onset is our own
  fair_mean ssp585's 2100 GMT. Measured `0.000e+00`.
* **2150 is now SPREAD-SCALED.** `|move| < TOL_FRAC × Greenland's own sampled p05–p95
  width there`, **read from `outputs/ssps_components_2300_L14.csv`** rather than
  hardcoded — 0.5 × 11.54 = **5.77 cm**. The shipped cell moves it **2.59 cm = 22.5%**.
* **`first divergence is AFTER 2150` became `AFTER 2100`.** The previous handoff named
  only the "2150 UNMOVED" assertion, but this second 2150-anchored check would have
  failed too: the cascade first diverges in **2102**.

**WHY IT WAS ALLOWED TO MOVE.** The old gate stated its own condition for revision —
*"do NOT narrow the admissible set on 2150 without a physics-based source at that
horizon"* — and `166e1d2` supplied one. **SICOPOLIS at 2150 reads 0.61–0.89×: we are
LOW there, not high.**

**`[MUT]` IS REPOINTED, NOT KEPT.** The old mutation (onset 4.0 K) was built to break an
*identity* gate and would pass a spread-scaled one trivially — a gate whose mutation
cannot fail is untested. τ is what the 2150 bound actually constrains, so **τ = 100 yr**
is the perturbation now (**107.59 cm** against the 5.77 cm bound). A second mutation
(onset 3.0 K, moves 2100 by 0.996 cm) keeps the identity half tested.

**`[VTILDE]` HAD A SILENT FAILURE MODE ON A CASCADE.** It read `gis_tap_s`, but at
n ≥ 2 the delivered unit is **`gis_tap_s2`** — s₁ is an internal state. Reading s₁ would
have overstated u₂₃₀₀ ~4×, picked a matching V 4× too small, and **still printed
"SURVIVES"**. Its alt cell is also now **faster, not slower**: matching Ṽ at a longer τ
needs V past the whole sheet, where the capacity clamp binds and the comparison is of
two different objects. The bite is measured and **voids** the gate if it binds.

---

## 4. THE RATE CRITERION AT n = 2 — the new evidence

`python/diag_gis_cascade_rate_crit.py` (new), `outputs/diag_gis_cascade_rate_crit*.csv`.

**Why it could not be read off any existing scan.** ψ = 100·V/τ is a **first-order
parameterisation**; at n = 2 it is not even defined, because the delivered unit is the
second stage. The flux has to be **measured off the trajectory**. The `psi_eff` column
is the reservoir's own 2250–2300 rate contribution in cm/century — form-agnostic, and
the only version of the quantity that means the same thing at n = 1 and n = 2. The
closed form is printed **beside** it, for n = 1 only, where it is defined; the gap
between the two columns is exactly what does not carry over.

| cell | r2300 rate | band [9.7, 41.5] | ψ_eff | 100V/τ | our 2300 |
|---|---|---|---|---|---|
| base | 2.9 | out (low) | 0.000 | — | 49.9 |
| A  V=1.0 τ 800 n=1 | 12.0 | IN | 10.202 | 0.125 | 70.9 |
| B  V=6.0 τ 2200 n=1 | 26.0 | IN | 25.330 | 0.273 | 99.1 |
| **SHIPPED V=6.0 τ 800 n=2** | **43.8** | **OUT (1.055×)** | **40.557** | — | **98.6** |

* **Robust to band construction**: 1.19× over the GCM-clustered band [11.6, 36.9], and
  **0/5** on leave-one-GCM-out. (2026-08-22c's finding that dropping MPI-ESM1-2-HR
  voided every survivor is why that check is not optional.)
* **NOT structural**: 63/72 cascade cells at the shipped onset clear the pre-existing
  gates; **16 of those also clear the rate band**. The shipped cell is simply not one
  of them — it is the cell in the whole scan closest to the matched p50, and **that is
  exactly what makes it steep at 2300**. Back-loading hard enough to clear the 2150 cap
  is the same property that gives it a fast late slope.
* **The price is 2.6%, not 12%.** Off the grid the tension reads as 12.2 cm at 2300
  only because there is no grid point between V = 4.5 and V = 6.0.

⚠ **TWO TRAPS, both live for anyone re-deriving this.**
1. **The p50 is `gis_targets.MATCHED_2300_P50_M` = 98.5 cm, NOT the r2300 arm's own
   band median = 72.3 cm.** Quoting the wrong one moves the verdict 1.36×. "Lands on
   the p50" is predictor-dependent (memory `gis_matched_band_predictor`).
2. **The x2300 arm is unreachable and always was**: the shipped cell gives 61.0 against
   a 122.8–189.0 band. That is a separate, band-independent finding (0/1080 in the
   earlier scan), not something this cell broke.

---

## 5. FILES

**New:** `python/diag_gis_cascade_rate_crit.py`,
`outputs/diag_gis_cascade_rate_crit.csv`, `outputs/diag_gis_cascade_rate_crit_scan.csv`,
`outputs/quarantine/20260823_old_tap_cell/README.md`,
`outputs/ssps_components_2300_L14_tap4p69K_V6p0m_tau800_n2_ws{,_shapefullcurve}.csv`.
**Modified:** `julia/greenland_3basin_component.jl`, `julia/brick_mengel.jl`,
`julia/ladrillo_projection.jl`, `julia/project_ssps_components_ladrillo.jl`,
`julia/test_gis_tap_wiring.jl`, `python/scope_gis_tap_shape.py`,
`python/diag_gis_stepback_rate_crit.py` (gains `--cells=legacy|shipped`, default arm
verified byte-identical), `.gitignore`, `CHANGELOG.md`.
**Quarantined:** the four `tap6p5K` / `tapset` outputs.

Commits `1246f2f` → `939e631`.

---

## 6. WHAT IS STILL OPEN

1. **§1's decision.** V = 6.0 vs V ≈ 5.66.
2. **THE CELL-CHOICE ENVELOPE HAS NO CASCADE VERSION.** The `--tap-set` arm's 25 cells
   were priced first-order. That band was **1.180 m at Greenland 2300 — 4.4× the
   sampled p05–p95 of 0.268 m, and the LARGER of the two uncertainties**. It is
   currently **unquantified** for the cascade. Do not quote the quarantined envelope
   against the shipped cell. Producing a cascade-priced admissible set is real work and
   nobody has done it.
3. **The 2100 fast bias (1.32× ISMIP6, and 1.37× under the shipped cell) is a SEPARATE
   defect that no onset and no cell fixes**, and it is now the binding one. ISMIP6
   passes the observational gate (median 1.15× obs, obs inside the spread), so the bias
   is ours. Our hindcast rates are 0.95–1.07× but our **acceleration is 0.65×** over
   1993–2024 — we match level and rate, under-run curvature, and arrive high at 2100.
4. **`build_protect_r2300_forcing.py` still carries `ONSET_K = 6.5` labelled
   "GIS_TAP_CELL.onset_K"** with an assertion built around it. It is a data-prep script
   for the r2300 forcing and its output is unchanged, but the comment is now wrong.
   Low priority, flagged rather than churned.

---

## 7. NON-OBVIOUS STATE

* **τ is the TOTAL mean delay at every stage count** (each stage runs at `stages/τ`).
  That is what makes `stages = 1` the old recursion term for term, in both
  `reservoir_unit_n` and `gis_tap_s` / `gis_tap_s2`. Do **not** "simplify" it to
  per-stage τ.
* **The capacity clamp never binds at the shipped cell** — `max(wanted − applied) =
  0.0000 m` over the wiring gate and over 400 draws in the port test — so the wiring IS
  the offline mock's uncapped additive reservoir and the pricing transfers exactly.
* **`git add -A` no longer stalls**, but stage explicit paths anyway; `outputs/` carries
  a lot of untracked scratch.
* **`--tol=legacy` still reproduces the pre-2026-08-23g artefact byte-identically**, and
  `diag_gis_stepback_rate_crit.py --cells=legacy` does the same for the 2026-08-22c
  rate verdict. Both were checked this session.
* Every trap in `handoff_2026-08-23_commitment_evidence.md` §9,
  `handoff_2026-08-23b` §9 and `handoff_2026-08-23d` §5–§6 still applies unchanged.
