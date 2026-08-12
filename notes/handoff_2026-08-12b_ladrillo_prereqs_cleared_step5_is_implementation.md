# Handoff 2026-08-12b — Ladrillo: all four step-5 prerequisites cleared, and step 5 turns out to be an implementation job, not a launch

**Self-contained pickup:** this note + the `CHANGELOG.md` entries for 2026-08-12 (there are
three) + the two quarantine READMEs named in §2. The morning's handoff
`notes/handoff_2026-08-12_ladrillo_gates_cleared_step5_ready.md` is superseded on three
points — see §0 before reusing any number from it.

Repo `SLR-RFF-BRICK`, branch **`brick-mengel-vnext`**, tip `fb21d53`. Three commits:
`7e142ff` (4.7), `dfe1d1b` (gate 3.1 ruling), `fb21d53` (the fitter bug + 4.1/4.2).

**Run `./run_ladrillo_tests.sh` first.** Four suites, all pass.

---

## 0. WHAT THE MORNING HANDOFF GOT WRONG — read before reusing it

1. **"A+B's 6.30 cm 2100 spread is on the evaluation band floor (6.3–7.3). The joint
   calibration can only push it down."** (its §6) — **RETIRED.** That was a property of an
   **unconverged fit**. The converged A+B spread is **10.44 cm, ABOVE the band**. Pushing it
   down is now the desirable direction, not a worry.
2. **"4.2 — fixing β_f at a literature SMB response time costs nothing measurable"** (its §4)
   — **FALSIFIED.** It costs **2Δ = +133** and collapses the Mouginot surface share to 0.34
   against a 0.735 constraint. See §3.
3. **"β_f is unidentified — 100% of its local range within Δ < 2.3"** — the *claim* survives
   in a much weaker form, but the *evidence* cited for it was void: measured against a
   non-optimum, over a ×30 window pinned to a railed value (1e-6 to 3e-5), with optimiser
   scatter of ±6 nlp — larger than the Δ = 2.30 threshold applied to it.

Everything in its §2 and §3 (gates 3.1 and 3.2) stands unchanged.

---

## 1. Where the work stands

| item | state |
|---|---|
| Gate 3.1 target conflict | CLEARED 08-11; **σ treatment RULED by Marcus 08-12** — §4 |
| Gate 3.2 28 cm attribution | CLEARED 08-11, unchanged |
| **4.1 decide `g`** | **DONE — FIX AT 0**, §3 |
| **4.2 fix or justify β_f** | **DONE — stays FREE** (Marcus), §3 |
| **4.7 RNG call-order** | **DONE**, §5 |
| offline-cell fitter | **BUG FOUND AND FIXED**, §2 — this was not on anyone's list |
| **step 5** joint recalibration | **UNBLOCKED, but it is a BUILD not a launch** — §6 |

---

## 2. The thing nobody was looking for: the cell fits were never converged

`python/gis_offline_cell.py` reported optima that are not optima. **The evidence was sitting
in the committed outputs**: 214 of the 225 A+B `(f, beta_f)` ridge points — which *fix two
parameters* and re-optimise the rest with a *weaker* inner optimiser — scored **below** the
reported 8-parameter optimum of 42.52, by up to 24 units. A constrained fit cannot beat an
unconstrained one at the same objective. Re-evaluating the committed parameter vector under
the corrected code reproduces `nlp = 42.5228`, `spread = 6.301`, `RMSE = 0.0987`,
`share = 0.741` **exactly**, so this is one objective at two points, not two objectives.

Cause: starts drawn **uniformly** over rate bounds spanning five orders of magnitude
(`[1e-6, 0.2]`), so the slow decades were never sampled; and one Nelder-Mead call taken as
converged, when its simplex degenerates on flat log-scaled directions.

**Corrected table** (`outputs/gis_offline_cell_fits.csv`; pre-fix in quarantine):

| cell | npar | nlp was → is | RMSE was → is | spread was → is | G4 |
|---|---|---|---|---|---|
| stock | 5 | 234.92 → 234.92 | 0.325 → 0.325 | 7.25 → 7.25 | OK |
| A | 5 | 17.87 → 17.87 | 0.061 → 0.061 | 10.85 → 10.85 | — |
| B | 8 | 246.61 → **232.07** | 0.315 → 0.282 | 6.90 → 7.27 | OK |
| **A+B** | 8 | 42.52 → **17.856** | 0.099 → **0.062** | **6.30 → 10.44** | **OK → —** |
| A+B' | 7 | 62.78 → **19.15** | 0.068 → 0.077 | 6.27 → **0.00** | — |
| A+B+C | 7 | 2038.31 → **563.20** | 1.675 → 0.844 | 51.99 → 0.28 | — |
| A+B'+C | 6 | 724.26 → **118.15** | 1.009 → 0.350 | 13.08 → 6.24 | — |

**Decision 4 (A+B is the module) SURVIVES, on better evidence than before.** A+B is the best
cell; it ties A's hindcast (RMSE 0.062 vs 0.061, G1/G2/G3 all pass) *and* reproduces the
Mouginot partition to four figures (0.7351 against 0.735), which single-channel A cannot
represent at all. The regional driver is what does the work — stock/B ≈ 232–235 against
A/A+B ≈ 17.9. Option C still fails decisively.

**Three invariants now assert on every run**, and they are the reusable part:
- **no constrained ridge point may beat the optimum** (`convergence_check()`);
- **no container cell may score above the cell it nests** (`NEST_MAP`: stock→B, A→A+B);
- **repair pass** — a violating ridge point is re-used as a *start* before the assert fires,
  so the gate reports genuine failure rather than optimiser luck. **It fired on this run:**
  B 234.92 → **232.07** via a 232.18 witness.

The protocol needed all of: log-uniform draws on rate axes, 240 starts, restart-polish,
basin-hopping jitter, **and** nested warm starts. The first three alone still had B landing
at 234.92 on one run and 245.06 on the next — both above what stock, which B *nests*, had
already achieved.

**Quarantine:** `outputs/quarantine/20260812_gis_offline_cell_underconverged/` + README with
the full impact table. **Bug, not a vintage difference** — said so in the README.

**Flagged, not chased:** A+B' now returns a 2100 spread of **exactly 0.00 cm** (all three
scenarios give 1.31 cm) because its anti-overshoot clamp saturates at the converged optimum.
Suspicious uniformity and a real structural pathology of that cell. Not the module.

**NOT affected:** the Julia port (`validate_greenland_ab.jl` runs *both* sides at the same
parameter vector, so it is a structural identity check, indifferent to which vector), the
extC posterior (predates the module), and gates 3.1/3.2 (neither read this table).

---

## 3. 4.1 and 4.2, decided

Evidence: `python/diag_gis_g_betaf.py` → `outputs/gis_g_betaf_{variants,profiles}.csv`,
`figures/gis_g_betaf.png`. Criteria were **pre-registered in the script header** before any
fit ran.

### 4.1 `g` → **FIX AT 0. Do not sample it in step 5.**
Profiled over [0, 0.8] the objective moves **4e-4 nlp** and the 2100 projections do not move
at all (max |Δ| **0.000 cm**); LR accepts `g = 0` at 2Δ = +0.001 against χ²₁ = 3.841. It is
**confounded with `c0`**: two converged runs returned `(c0 61.99, g 0.917)` and
`(c0 5.21, g 0.183)` at the same `nlp = 17.856`, with 2100 projections agreeing to
**< 0.001 cm** in all three scenarios. A flat manifold, not a shifted estimate. `g = 0`
restores stock SIMPLE's own initial condition. Recorded in the component header.

### 4.2 `beta_f` → **stays FREE and sampled** (Marcus's ruling, 2026-08-12)
- A literature **decadal** SMB rate is **rejected at 2Δ = +133** and collapses the Mouginot
  share to 0.34. In the share form the SMB channel drains a *multi-millennial* commitment,
  so "fast" names which **physics** the channel carries, not a short time constant —
  **τ_f = 86 yr** at the optimum. **Do not re-fix it at a decadal value.**
- The data **bound** it (`beta_f < ~1e-2/yr`) but cannot resolve below that: flat to Δ < 2.3
  across five decades, 1e-6 → 9.8e-3.
- It is unidentified **and consequential**: `beta_f = 0` costs only 2Δ = +0.55 (LR accepts)
  yet moves 2100 SSP5-8.5 by **1.70 cm** and the spread by 1.28 cm.
- Marcus chose free-sampling over fixing, so the 1.7 cm stays visible as uncertainty rather
  than hiding in a point value, and the joint likelihood gets a chance to identify it.
  **Re-bounding the prior to the data support was offered and declined** — so `[1e-6, 0.5]`
  spans four decades the offline fit excludes. **Watch sampler efficiency there.**

---

## 4. Gate 3.1 σ ruling — implemented and live

Marcus chose **(c) widen across the whole span**, with the shape taken from data rather than
a fitted decay: the per-year weighted sd of Frederikse's **own** budget closure
(Σ components − their GMSL) across the 5000 members, each re-referenced to 1995–2005 exactly
as the targets are.

| year | 1900 | 1950 | 1980 | 2000 | 2018 |
|---|---|---|---|---|---|
| closure sd (cm) | 2.375 | 1.389 | 0.776 | 0.460 | 0.775 |
| inflation on total σ | 1.37× | 1.25× | — | 1.11× | 1.90× |

The modern rise is the **anchor**, not an artifact: the spread is pinned at 1995–2005 and
grows away from it in both directions, which is correct for a level anomaly scored in that
frame, while Dangendorf's own σ collapses to 0.44 cm under altimetry. Two monotone variants
(flatten after the anchor; pre-1993 only) were offered and **declined** — each needs a
discretionary choice.

- `python/prep_recalib_targets_ext.py` → `load_closure_sigma()`, new column
  `dang_closure_sig`. Ensemble ends 2018, target runs to 2024 → **held flat past 2018**, the
  same FLAGGED convention already used for LWS. **Every pre-existing column is
  bit-identical** (max|diff| 0.0 across all 18).
- `julia/calibrate_mcmc_ext.jl` adds it in quadrature in the `isdang` branch of
  `make_series`, prints the inflation in the run log, and **`--no-closure-sigma` reverts**.
- Verified live: `logpost(θ0)` = **−831.74** with the flag vs **−849.24** with the term on.
  The toggle is not inert.

**CAVEAT ON RECORD, flagged not corrected:** the total channel also carries a sampled AR(1)
with ρ_steric ≈ 0.97, so an anchor-shaped σ may partly **double-count level correlation**.

---

## 5. 4.7 done — `ladrillo_data.py` is order-independent

Each `four_rung_fit` now seeds its own stream from the block's identity
(name, inventory basis, `amp_b`) instead of sharing one module-level RNG; the two discarded
"RNG parity" fits are gone from `build_artifacts()`.

**Measured before changing anything:** six different global seeds moved `(a, b, T_off)` by
**1e-10 to 3e-8** for every block on both bases. Every seed finds the same optimum, so this
was a reproducibility fix, not a correctness one. Only `outputs/extc_block_constants.csv`
moved (**1.69e-8** in `T_off_fit_regchar`); drivers and the seam-adjusted target are
bit-identical. Far below MCMC noise → **the accepted extC posterior stands and was not
re-run**; the fix landed *before* step 5 so Ladrillo 1.0 gets clean inputs.

`python/test_ladrillo_data.py` [1] used to assert exact identity against the dev-chain
artifacts. It now asserts **three** things: exact identity against the canonical files;
agreement with the quarantined dev-chain copy within a documented 1e-6; and
**order-independence** under a permuted build — the property the fix adds, and one that
fails on the pre-fix code. Quarantine:
`outputs/quarantine/20260812_ladrillo_data_rng_order/` (README + the pre-fix CSV, both
force-added since `outputs/quarantine/` is gitignored).

---

## 6. Step 5 is a BUILD, not a launch — this is the main correction to the plan

`grep` for `greenland_ab|gis_beta_f|gis_alpha_f` in `julia/calibrate_mcmc_ext.jl` returns
**0**. The Greenland module exists and is validated as a Mimi component, but **it is not
wired into the calibrator at all**. Step 5 therefore requires, before any chain runs:

1. Swap the stock SIMPLE GIS component for `greenland_ab` in the calibrator's model build.
2. Feed it the **regional** driver, built inside the model as `amp × GMST + offset` with the
   anchor-preserving splice (`ladrillo_driver` in `julia/ladrillo_projection.jl`). **Do not
   break the GMST+OHC-only external interface** — that drop-in property is what distinguishes
   Ladrillo from MAGICC-SLR.
3. Add priors/bounds for **7** sampled Greenland parameters — `gis_c1, gis_c0, gis_f,
   gis_alpha_f, gis_beta_f, gis_alpha_s, gis_beta_s` — with **`gis_g` fixed at 0** (§3) and
   `gis_v0` structural. The offline optimum is a reasonable prior centre:
   `c1 = 3.278, c0 = 61.99, f = 0.7827, alpha_f = 2.843e-3, beta_f = 7.371e-3,
   alpha_s = 7.079e-3, beta_s = 1e-6` (cm units — the component works in **m SLE**;
   `python/emit_gis_port_reference.py` does the conversion, do not redo it by hand).
   NB `beta_s` rails at its floor; `c0` is only identified jointly with `g`, so with `g = 0`
   fixed it becomes identified and the prior should not be centred on a manifold value.
4. Re-run `./run_ladrillo_tests.sh`, then a short smoke chain, then the production run.

**Pre-registration for reading the posterior** (updated from the morning handoff §2):
- Outcome 1 expected: Greenland improves, total degrades — but "degrades" means the total's
  mid-century residual flipping −0.32 → +0.50 cm, **0.32σ of its own σ**, and the σ is now
  wider mid-century (§4), so this should be easier to absorb than pre-registered.
- Outcome 3 (suppression) is **less likely than the red team feared**. If the posterior comes
  back ≈ extC, the cause is **not** the target conflict — look at **sd_gis / rho_gis
  inflation** next.
- Outcome 2: if glaciers/TE absorb it, check the GlacierMIP3 rungs and the GlaMBIE modern
  rate did not break.
- **New:** watch the 2100 GIS scenario spread coming DOWN from 10.44 cm toward the 6.3–7.3
  band. That is now the expected direction, and a posterior that leaves it above 10 cm is as
  much of a flag as one that crushes it to extC's 2.16.

---

## 7. Owed work, unchanged and not blocking

- **Quarantine sweep** for deliverables built on the 78.02 / 77.7 cm vintage. Needs a list of
  affected deliverables first. **Vintage difference, not a bug** — say so in the README.
- `data/MimiBRICK/parameters_subsample_brick_mengel_extC.csv` still says "brick_mengel"
  although extC has no Mengel glaciers. Wrong *before* the rename; kept separate.
- **4.3** re-check TE against a modern OHC target — note ρ_steric = 0.973 makes TE the other
  near-random-walk channel, so this and gate 3.1's finding are plausibly the same story and
  are worth doing together. §4's caveat is a third thread of it.
- **4.4** ν sensitivity once. **4.5** refit with the four glacier set-asides at prior centres.
  **4.6** structural-uncertainty caveat wherever bands are compared to FACTS.
- **Etymology / rationale sentence** for the sharing memo — **Marcus drafts prose**.
- Branch is still `brick-mengel-vnext`; renaming deferred.

---

## 8. Non-obvious state

- **Tony shared** `MimiBRICK.jl@zempdata/data/calibration_data/global_basin_timeseries.xlsx`.
  **We already have it, byte-identical** — git blob SHA `5bcf38cf1ed0892083b1f0c0e2984a9ba146d7b9`,
  271,196 B, = `data/observations/raw/frederikse2020_global_basin_timeseries.xlsx`. We hold
  strictly more: the 5000-member ensemble netCDF, which the spreadsheet does not contain and
  which §4's σ is built from. The one thing the xlsx has that we do **not** ingest is its six
  **basin** sheets (we read only `Global`). The branch name suggests **Zemp** glacier data —
  worth asking Tony what else is on it; the Frederikse file itself is a duplicate.
- **Two tracked files are dirty and incidental**, unchanged by this session and dirty before
  it: `figures/diag_gis_regional_driver.png`, `outputs/mcmc/overdispersed_starts.csv`. Leave
  them or commit them deliberately — don't sweep them into an unrelated commit.
- `outputs/gis_port_reference{,_theta}.csv` **changed** this session — they are re-emitted
  from the offline A+B fit, which moved. Expected; the port test passes at 1e-9 either way.
- Python env `source ~/climate-env/bin/activate`; Julia `--project=julia_v2`.
- `gis_offline_cell.py` takes **~35–40 min** end to end now (basin hopping + polished ridges).
  `diag_gis_g_betaf.py` takes ~25 min.
- The Bochow-2026 emulator retraction still stands; `outputs/scope_greenland_bochow2026*.csv`
  must not be used, and still contains the string `BRICK-F*` as a retracted artefact.
- Greenland option C failed and is out of pass 1; the same criticism (proportional relaxation
  cannot serve both a small historical loss and a huge post-threshold commitment) applies to
  A+B at high warming, where it is invisible rather than absent. **Flag it wherever 2300 or
  high-warming Greenland is reported.**
- Naming: **Ladrillo**, `ladrillo_`/`LADRILLO_`/`Ladrillo`. Never `sed s/brickf/ladrillo/g` —
  `brickf` ⊂ `brickfm`, and **BRICK-FM is a different model** with ~130 references here.
  Dated `notes/` are frozen; `CHANGELOG.md` 2026-08-12 has the path mapping table.
