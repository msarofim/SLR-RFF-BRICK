# Handoff — the cell is CHOSEN and PORT-TESTED, the wiring is in and off by default, and what remains is finalization

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, through `2b5e596`.
Written 2026-08-23, to be picked up cold. **This is the finalization handoff — the
science is settled, the remaining work is mechanical plus ONE test rewrite.**

**Supersedes** `handoff_2026-08-23c_form_refuted_cascade.md` for its §5 work queue.
Its §2–§4 (the 2150 veto, the refuted sample-size rescue, the analytic form bound) are
**unchanged and still load-bearing**. `handoff_2026-08-23b` §6's SC-GHG conflict is
**RESOLVED by the onset decision in §1 below** — read §1.3 before reopening it.

---

## 0. THE ONE-PARAGRAPH VERSION

The Greenland commitment reservoir is a **2-stage cascade**, cell **V = 6.0 m,
τ = 800 yr, onset 4.69 K, whole-sheet home**, chosen by Marcus 2026-08-23 on the
between-scenario criterion. It is **already wired** into `greenland_3basin` behind two
off-by-default parameters, the **existing test suite passes unchanged and
bit-identically**, and a **400-draw port test confirms the offline pricing transfers**
(ssp585@2300 wired 98.81 vs offline 98.2 cm; 2100 exactly inert; the capacity clamp never
binds). What remains: flip `GIS_TAP_CELL`, **rewrite one test assertion** ([G2]'s "2150
UNMOVED"), regenerate the deliverable projections, and update the memo numbers.

---

## 1. THE DECISION, AND THE REASONING THAT SETTLED IT

### 1.1 The cell

| | value |
|---|---|
| stages | **2** (cascade; `gis_tap_stages = 2.0`) |
| V | **6.0 m** |
| τ | **800 yr** (the TOTAL mean delay; each stage runs at stages/τ) |
| onset | **4.69 K** GMT rel 1850-1900 |
| home | **whole sheet** (`gis_tap_wholesheet = 1.0`) |
| ramp width | 1.0 K (unchanged) |

### 1.2 WHY A CASCADE AT ALL — the first-order form is refuted, not just out-scored
The joint constraint (≤ 8.1 cm added at 2150 on the ssp585 x2300 arm, 48.6 cm needed at
2300 to reach the matched p50) requires a **delivery ratio R = 6.03**. A reservoir's
response to its ramp is an n-fold repeated integral, so in the long-τ limit — the most
back-loaded any n can be — **n=1 gives 2.82, n=2 gives 7.86, n=3 gives 21.71**, and swept
over onsets 1.6–7.5 K n=1 peaks at **2.89**. No (V, τ, onset) of the first-order form can
do it. A cascade is **not completely monotone**, so the exact bound that refuted the
ladder / Prony / stretched-exponential / Mittag-Leffler / power-law families does not
reach it. Full argument: `handoff_2026-08-23c` §4, `python/diag_gis_2150_band_veto.py`.

### 1.3 WHY ONSET 4.69 AND NOT 2.35 — the criterion that decided it
**Marcus 2026-08-23: "we aren't trying to match between-model spread (we don't have the
precipitation level), just between-scenario spreads."** Scored that way at 2300:

| onset | ssp585/ssp245 | ssp585/ssp126 | ssp585@2300 | Greve@3001 | w(3:2:1) |
|---|---|---|---|---|---|
| untapped base | **2.73×** | 4.94× | 49.9 | 0.18× | 0.885 |
| 2.35 | **2.60×** ← *below the base* | 5.55× | 55.9 | 0.39× | 0.588 |
| 3.60 | 5.15× | 9.37× | 94.4 | 1.15× | 0.351 |
| 4.35 | 4.86× | 8.85× | 89.1 | 1.14× | **0.331** |
| **4.69 (CHOSEN)** | **5.38×** | **9.79×** | **98.6** | **1.05×** | 0.346 |

matched ssp585/ssp245 ratio band at 2300 = **2.00–13.68×**.

**A low onset fires the reservoir in SSP2-4.5 and SHRINKS the separation below the
untapped model** — the exact quantity the reservoir exists to buy. 4.69 K gives the
highest separation on the whole ladder, lands our ssp585@2300 on the matched p50 (98.6 vs
98.5) and is closest to Greve at 3001 (1.05×).

⚠ **The composite w-score mildly preferred 4.35 (0.331 vs 0.346) and it is the criterion
to DISCOUNT here**, because it scores level agreement against ISM medians — a
between-MODEL criterion in disguise. See memory `between_scenario_not_model`. **Report the
scenario RATIO alongside any level score from now on, and let the ratio break ties.**

**This closes `handoff_2026-08-23b` §6.** The moderate-scenario per-tonne SC-GHG term is
**exactly zero at this onset**, and that is now a decision made on evidence rather than an
unexamined inheritance: buying that term costs the scenario separation the model exists to
produce. If the CH₄-vs-CO₂ SLR paper needs a nonzero moderate-scenario commitment term, it
needs a **second, separately-justified arm**, not a change to this cell.

---

## 2. WHAT IS ALREADY DONE — DO NOT REDO IT

* **`greenland_3basin` carries both capabilities, OFF BY DEFAULT and bit-identical**:
  `gis_tap_stages` (1 = first-order, default) and `gis_tap_wholesheet` (0 = high-basin
  home, default). Plumbed through `brick_mengel.update_gis3_tap!` and
  `ladrillo_projection.ladrillo_set_tap!` with keyword args `stages=` and `wholesheet=`.
* **`julia/test_gis_tap_wiring.jl` PASSES UNCHANGED** after that change — every nesting
  and horizon check still 0.000e+00, [CAP] still never binds, [MUT] still fails when
  perturbed. `GIS_TAP_CELL` is **untouched**; nothing ships yet.
* **The port test passes** (`julia/diag_gis_cascade_port.jl`, 400 draws):

  | ssp | 2100 Δ | 2150 | 2300 wired | 2300 offline |
  |---|---|---|---|---|
  | SSP1-2.6 | +0.000e+00 | unchanged | 10.05 | 10.1 |
  | SSP2-4.5 | +0.000e+00 | unchanged | 18.28 | 18.3 |
  | SSP5-8.5 | +0.000e+00 | 28.45 → 31.03 | **98.81** | 98.2 |

  Level transfers to 0.05 / 0.02 / 0.61 cm; **2100 exactly inert on all three**; the
  **whole-sheet clamp NEVER binds** (max(wanted − applied) = 0.0000 m), so the wiring IS
  the uncapped additive reservoir the cell was priced on.
* **NO REFIT IS NEEDED.** G-INERT is exactly 0.0 over the calibration window on every cell
  scanned, so the hindcast, the bisection and the rate solution are unchanged. This is a
  prior-propagated projection-side change, like `gis_amp`. If anyone asks for a
  recalibration, that is a **separate and much larger decision**, not implied by this.

---

## 3. WHAT REMAINS — IN ORDER

1. **Flip `GIS_TAP_CELL`** in `julia/greenland_3basin_component.jl` to
   `(onset_K = 4.69, V_m = 6.0, tau_yr = 800.0, ramp_w_K = 1.0)` and make the defaults
   `GIS_TAP_STAGES_DEFAULT = 2.0` and whole-sheet ON **for the shipped cell**. Decide
   deliberately whether the module defaults move or only the projection driver's call
   does — the safer form is to leave the component defaults at 1.0 / OFF and have
   `ladrillo_set_tap!` pass the shipped cell's stages and home explicitly, so anything
   that builds the model without asking for the tap is still bit-identical.
2. **REWRITE [G2], DO NOT DELETE IT.** `test_gis_tap_wiring.jl` asserts
   `ssp585 total at 2150 is UNMOVED`. The new cell moves it by **+2.58 cm**. Replace the
   identity assertion with a **spread-scaled plausibility assertion** — the same move made
   on the 2100 tolerance on 2026-08-23g:
   > 2150 must move by less than `TOL_FRAC` × Greenland's own sampled p05–p95 width there.
   Numbers to use: sampled width at 2150 = **11.54 cm**, so at `TOL_FRAC = 0.5` the
   tolerance is **5.77 cm** and the cell's 2.58 cm passes with margin (22.3% of the width,
   9.1% of the median). **Keep the [MUT] mutation check** — repoint it at a cell that
   violates the NEW bound, or the rewritten gate is untested.
   *Justification to record in the test's own comment*: the test already stated its
   condition for revisiting 2150 — "do NOT narrow the admissible set on 2150 without a
   physics-based source at that horizon" — and **SICOPOLIS at 2150 is now such a source**
   (commit `166e1d2`), reading **0.61–0.89×**, i.e. we are LOW there, not high.
3. **Regenerate the deliverable projections**:
   `julia --project=julia_v2 julia/project_ssps_components_ladrillo.jl <n> --tap`.
   The filename already encodes the cell; **check that the TAG string picks up the new
   onset/V/τ** before trusting the output name, and consider adding the stage count and
   the home to it — a cascade run and a first-order run at the same (V, τ, onset) would
   otherwise collide.
4. **Quarantine the superseded tapped outputs** per the standing rule:
   `outputs/ssps_components_2300_L14_tap6p5K_V2p0m_tau50*.csv` are the OLD cell. Move to
   `outputs/quarantine/20260823_old_tap_cell/` with a README naming the replacement.
5. **Update the numbers that are quoted downstream** — the sharing memo's SSP section and
   any figure whose caption carries a Greenland@2300. **Sync captions and filenames to the
   new cell** (the standing labels-derive-from-constants rule).
6. **Re-run the 2250–2300 RATE criterion on the cascade.** Still not done. ψ = 100·V/τ is a
   first-order parameterisation and does NOT carry over to a cascade; the rate criterion is
   one of the two independent sources that pinned the flux, and it has never been
   re-evaluated for n = 2. This is the last open piece of evidence.

---

## 4. FILES

**New this session:** `python/diag_gis_matched_band_score.py`,
`python/diag_gis_2150_band_veto.py`, `python/diag_gis_2150_structural_spread.py`,
`julia/diag_gis_cascade_port.jl`.
**Extended, every default arm gated BYTE-IDENTICAL by diff:**
`python/scope_gis_reservoir_offline.py` (`--wide-v`, `--stages=N`, `--onsets=`,
`--tol=spread|legacy`), `python/scope_gis_onset_rescan.py` (`--stages=N`,
`--onset-max=`).
**Modified (all defaults bit-identical):** `julia/greenland_3basin_component.jl`,
`julia/brick_mengel.jl`, `julia/ladrillo_projection.jl`.
**Untouched:** `GIS_TAP_CELL`, every gate, every shipped output.

Commits `60423ad` → `2b5e596`. Memories: `gis_first_order_form_refuted`,
`gis_matched_band_predictor`, `tolerance_scaled_to_spread`,
`between_scenario_not_model`; `gis_weighted_verdict_cell` marked ACTION-SUPERSEDED.

---

## 5. NON-OBVIOUS STATE

* **`git add -A` STALLS in this repo.** There are multi-GB untracked NetCDFs under
  `data/observations/raw/` that are not gitignored (`HadCRUT.5.0.2.0...nc`,
  `Land_and_Ocean_LatLong1.nc`, `gistemp1200_GHCNv4_ERSSTv5.nc{,.gz}`). **Stage explicit
  paths**, and consider adding a `.gitignore` rule as a first task.
* **`--tol=legacy` reproduces the pre-2026-08-23g artefact byte-identically**, so the
  86/216 verdict and everything resting on it stays checkable. The tolerance rule, the
  arm, the stage count and the onset ladder are ALL in the output filename.
* **τ is the TOTAL mean delay at every stage count** (each stage runs at stages/τ). That
  is what makes `stages = 1` the old recursion term for term, in both the Python
  (`reservoir_unit_n`) and the Julia (`gis_tap_s` / `gis_tap_s2`) implementations. Do not
  "simplify" it to per-stage τ.
* **The 2150 evidence is genuinely contradictory and that is a REPORTED result, not an
  unresolved bug**: NORCE-CISM on the hot x2300 forcing says adding mass by 2150 pushes us
  out the top; SICOPOLIS on ssp585 GCM forcing says we are 0.61–0.89× LOW there. Both are
  like-for-like in forcing. The chosen cell sits inside **every** version of the 2150 band,
  which is why the contradiction does not block it.
* Every trap in `handoff_2026-08-23_commitment_evidence.md` §9 and `handoff_2026-08-23b`
  §9 still applies unchanged.

---

## 6. TRAPS ADDED THIS SESSION

* **A level-agreement score against a multi-model median is a between-MODEL criterion in
  disguise.** When the deliverable is between-scenario spread, it can rank cells the wrong
  way round — it did here. Report the scenario RATIO alongside any level score.
* **Scale plausibility gates to the sampled spread; keep identity gates exact.** A bare
  0.10 cm 2100 tolerance was 2.0% of the model's own spread there and was silently
  choosing τ, and through τ the millennial commitment.
* **Relaxing one gate can INVERT an earlier "does not bind" finding.** Under the tight 2100
  gate, dropping the ssp245 band changed nothing; under the scaled gate it changes a lot.
* **Two scorecards with different admissible ceilings will silently disagree about which
  cells exist** — one had a 2.73 m high-basin ceiling, the other 7.42 m whole-sheet.
* **Bound the FORM before scanning cells of it.** One n-fold-integral calculation killed
  every first-order (V, τ, onset) after two scans had explored the space cell-by-cell.
* **A band built from many runs of ONE model carries no structural spread** even when its
  width survives a sample-size test. Check what varies across the runs, not how many.
