# Handoff — the tap is PRICED and narrowed to six cells, the hindcast supports TWO basins,
# and L13 fixed the partition but not the separation

**Start-here document.** Repo `SLR-RFF-BRICK`, branch **`ladrillo-dev`**.
Predecessor: `notes/handoff_2026-08-20_gis_zone_and_tap.md`.
Commits: `1b2c90a` (offline fit), `6c4f907` (tap pricing), `03df3d2` (basin structure).

**Bottom line. (1) THE TAP CLEARS. 25 of 140 admissible cells pass every gate at ratio
9.77–16.41×, and the tap moves ssp126/ssp245 by EXACTLY zero. (2) BUT L13 ALONE DOES NOT.
Its own untapped ssp585/ssp245 2300 ratio is 2.71× against the literature's 7.9–31.9× —
inside the single-law ridge ceiling. The sector restructure fixed the PARTITION, not the
SEPARATION, exactly as predicted; the tap is still load-bearing. (3) THE 2300 SCORECARD
IDENTIFIES ONLY ONE COMBINATION of (T_on, V, τ), and the free direction is expensive at
2150 — resolved by a DESIGN PRINCIPLE, not a fit: onset ≥ 6.5 K leaves 2100 AND 2150
bit-identical. (4) THE HINDCAST SUPPORTS TWO BASINS, NOT THREE: refit, s_mid = 1.024, and
pinning it to 1 costs Δnlp 0.002. (5) Item 1 was blocked on a prerequisite nobody had
spotted: there was no L13 posterior subsample. (6) Item 2's offline A+B fit EXISTS and
needed no rebuilding — but it carried the SAME amp bug the calibrator had fixed one
commit earlier.**

---

## 1. THE PREREQUISITE NOBODY HAD SPOTTED

Next-action 1 says "scope the tap offline against the **certified L13 posterior**".
There was no certified L13 posterior on disk.

`postprocess_mcmc_ext.jl` ran at **01:50**; `diag_slr_convergence_by_chain_ladrillo.jl`
wrote `slr_convergence_L13.csv` at **01:53**. Three minutes. So `--accept-slr` found no
file, the parameter-level gate failed (14 marginals), and it refused the canonical write —
which the 08-20 CHANGELOG entry then recorded as *"deliberately not run"* on promotion
grounds. Two different reasons for the same absence, and the second one hid the first.

**Re-run here, and it is NOT a promotion.** Verified rather than assumed:

* `LADRILLO_POSTERIOR_CSV` (`ladrillo_projection.jl:109`) is a **hardcoded L12 path**.
* The `ADCOV` preference list (`calibrate_mcmc_ext.jl:1541`) is an explicit list of named
  files; `adapted_cov_L13.csv` is not in it.
* Both writes are tag-suffixed.

**L12 remains canonical at 45.53 cm** (Marcus 2026-08-20: *"leave L12 as the canonical
version for now, even though L13 is the preferred configuration"*).

**LATENT TRAP CREATED, flagged not fixed.** `adapted_cov_L13.csv` is a **nameless** 59×59
written as `DataFrame(cov(M), :auto)`, at a canonical name, appearing in **no** vintage
name list. That is the `nameless_matrix_order` shape that voided L13's first line. Nothing
reads it today. Anything that later points `--adcov=` at it must gate the diagonal first.

---

## 2. THE RESULT: the tap clears, and L13 alone does not

`python/scope_gis_tap_l13.py` → `outputs/scope_gis_tap_l13.csv`. 2000 draws, no MCMC.

### 2.1 The base — the number that reframes the arc

| scenario | 2100 cm | 2300 m | lit band | |
|---|---|---|---|---|
| SSP1-2.6 | 6.43 [5.73, 7.15] | 0.097 [0.080, 0.117] | 0.058–0.163 | **IN** |
| SSP2-4.5 | 8.41 [7.38, 9.54] | 0.177 [0.142, 0.218] | 0.098–0.218 | **IN** |
| SSP5-8.5 | 13.86 [11.58, 16.41] | **0.480** [0.369, 0.613] | 1.732–3.127 | **out** |

**ssp585/ssp245 @2300 = 2.71× [2.56, 2.85]** against the literature's **7.9–31.9×**.

That sits squarely inside the single-law ridge ceiling of 1.72–3.36×. **The sector
restructure fixed the PARTITION and not the SEPARATION** — which is what
`ladrillo_leq_ridge_ceiling` §6 said it would do, but this is the first time the ratio has
been measured on a *fitted* 3-basin posterior instead of an offline reduction. **The tap
is still the load-bearing mechanism.** Do not let L13's partition success be misread as
having addressed the ssp585 deficit.

### 2.2 The tap — 25/140, a plateau

Admissible = onset ∈ (4.69, 7.81] K and V ≤ 2.73 m: **140 of 180** grid cells.

| gate | cleared |
|---|---|
| 2300 level bands (all three) | **25** / 140 |
| ratio band 7.9–31.9× | 37 / 140 |
| 2100 spread kept | **140** / 140 |
| **everything** | **25 / 140** |

Passers span onsets **5.0–7.0 K**, V **1.5–2.5 m**, τ **50–200 yr**, ratio
**9.77–16.41×**. Consistent with the mock's 59/720 at 10.1–17.6× and the prototype's 10/64.
**The binding constraint is the 2300 LEVEL band, not the ratio band** — worth knowing,
because it means the answer is sensitive to the TC 19:6887 level band and comparatively
insensitive to how the ratio band is constructed from its endpoints.

**The tap acts ONLY on the defective column — measured, not argued.** Across all 25
passers, ssp126 and ssp245 deviate from the untapped base at 2300 by **exactly
0.000e+00 m**, and ssp585's 2100 contribution is **exactly zero**, so **G4 = 1.0000×** on
every passer. The high basin holds **2.58 m [2.54, 2.62]** at 2300 under ssp585 against a
2.73 m Mouginot inventory, so the inventory cap binds in **≤0.05%** of draws — V is not
being clipped, the passing cells are genuinely feasible.

### 2.3 Four things this got right that its predecessors did not

1. **Rate scales MEASURED, not bisected.** The mock and the prototype solved `s_b` offline
   against an exactly-identified target; L13 fitted them, and the tap sits on `s_high`.
2. **The posterior is PROPAGATED, not collapsed to its median.** The deliverable IS a
   ratio, and ratios of medians are not medians of ratios — the trap that once made the
   shipped model look like it failed G4.
3. **The driver is L13's `south`, not the design's `all`.** L13 as calibrated still runs
   `GIS_ZONE = "south"`; scoring it on `all` would price a model nobody has fitted.
4. **The per-basin clamp is the Julia's `k_b·v0`, not the prototype's whole-sheet `v0`.**
   The two agree over the hindcast (the cap never binds there) and **diverge at 2300 under
   ssp585** — the only regime this exercise is about.

---

## 2.4 THE TAP HAS ONE IDENTIFIED NUMBER, NOT THREE — and the free direction costs 2150

The tap enters additively, so ssp585 at 2300 is `base + V·u₂₃₀₀(T_on, τ)`. The level band
therefore constrains a **single combination**, Ṽ ≡ V·u₂₃₀₀ ∈ **[1.252, 2.647] m**. Tested,
not asserted: *"Ṽ in that window"* reproduces `all_pass` **exactly, 25 of 25**. There is a
1-D identified quantity and a **2-D degenerate surface** — the same shape as the `φ·L_eq`
commitment ridge this whole arc has been fighting.

**The degenerate direction is free at 2300 and expensive at 2150.** Holding Ṽ fixed and
moving along it, 2150 still ranges by up to **0.82 m** (e.g. Ṽ = 1.889 ± 0.06: 2300 spans
2.369–2.427 while 2150 spans 0.350–1.169). At 2100 the spread is exactly 0.000 m. **So the
choice is invisible where the model is validated and loud where it is reported.** Worse,
the degeneracy is worst on the one axis with **no independent published gate** — τ.

### The resolution is a DESIGN PRINCIPLE, not a fit

`gis_offline_cell.py` states the rule: fitting to the FACTS/MAGICC intercomparison "would
make Ladrillo's Greenland a second-hand FACTS FittedISMIP and destroy the comparison's
independence" — which is why G4 is *reported*, never in the objective. Selecting the tap
cell on FittedISMIP's 2150 would breach exactly that rule.

**It is not needed.** The same answer follows from: *the tap must not move any horizon at
which the model has independent validation.* That is precisely how the Tier-1 bracket's
4.69 K floor arose — it IS ssp585's 2100 GMT. Extending the identical logic to 2150 gives
**onset ≥ 6.5 K**, because 6.5 K first fires in **2155** and 7.0 K in **2180**.

Six cells clear 2300 while leaving 2100 **and** 2150 bit-identical to the untapped model:

| onset K | V m | τ yr | ratio | 2300 m |
|---|---|---|---|---|
| 6.5 | 1.5 | 50 | 10.32× | 1.832 |
| **6.5** | **2.0** | **100** | **10.48×** | **1.860** |
| 7.0 | 2.5 | 50 | 11.29× | 2.004 |
| 6.5 | 2.5 | 100 | 12.42× | 2.205 |
| 6.5 | 2.0 | 50 | 12.87× | 2.283 |
| 6.5 | 2.5 | 50 | 15.41× | 2.734 |

**Recommended: onset 6.5 K, V 2.0 m, τ 100 yr** (bold row) — low in the band, tap = 73% of
the NO+NE inventory — with the other five as the sensitivity set. The FittedISMIP agreement
then stays what it must be: an EVALUATION you report, not a target you fit.

*The independent 2150 comparison, for reporting:* FittedISMIP 0.273 [0.180, 0.429],
bamber19 0.381 [0.039, 1.257], Ladrillo L11 0.271 — against L13's untapped base of
**0.279 m**, already on FittedISMIP's median.

**CAVEAT.** The exact 1-D collapse is a property of the MOCK's ADDITIVE tap. Wired inside
`greenland_3basin_component.jl` the tap interacts with the basin's own relaxation and its
`k_b·v0` clamp. **Re-test the collapse after wiring; do not assume it survives.**

---

## 2.5 THE HINDCAST SUPPORTS TWO BASINS, NOT THREE (commit `03df3d2`)

`python/scope_gis_basin_structure.py`. Every structure refits its **full** parameter set
against the same objective, in `gis_offline_cell.py`'s own integrator, bounds and
multistart-plus-basin-hop protocol. **G1 PASS**: B1 reproduces the harness's own A+B cell
to 1.6e-05 on every parameter and 2.4e-10 on nlp, so what follows is structure, not wiring.

| | npar | shared terms | worst \|z\| | s_mid | s_high |
|---|---|---|---|---|---|
| B1 one basin | 8 | 17.8559 | — | — | — |
| **B2 two basins** | **9** | **18.2241** | **0.69** | — | **0.229** |
| B3 three basins | 10 | 18.2238 | 1.01 | **1.024** | 0.259 |

All pass every pre-registered gate at identical RMSE (0.0617 cm). **Adding the NW split
costs a parameter and buys nothing** — shared terms agree to 4 decimals and the share fit
gets WORSE, because one NW rate scale still cannot span the two-window tension
(0.207 vs 0.262). L13's −1.09 only moves to 1.01 under a clean refit.

**THE PROFILE IS DECISIVE.** Refit properly, B3 puts `s_mid` at **1.024**, not L13's
posterior median 0.949:

```
s_mid 0.501 +1.76 | 0.794 +0.25 | 1.000 +0.0023 | 1.259 +0.18 | 1.995 +2.12
```

The profile is **well-curved, not flat** (+6.3 at 0.25, +7.3 at 3.98). So `s_mid` is
genuinely **IDENTIFIED** — this is not "we cannot tell", it is **"we can tell, and it is
1"**, which is the stronger claim. *(This corrects my own earlier over-claim that `s_mid`
was unidentified: L13's posterior sd of 0.147 in log10 is 3.4× NARROWER than the
calibrator's N(0, 0.5) prior, so the likelihood was informing it all along.)*

* 1σ interval (Δnlp ≤ 0.5, 1 dof): **[0.794, 1.259]**
* **cost of pinning `s_mid` = 1: Δnlp = +0.0023** — free
* the offline prototype's **4.47× is excluded at Δnlp > 7**. "Do not chase 4.47" is now a
  measurement, not an instruction.
* no profile point falls below the B3 optimum ⇒ the fit converged.

**The other three criteria agree.** *Process models:* Aschwanden has NW going
land-terminating with discharge "greatly reduced" by 2300 — a DECELERATION; the accelerating
mechanism (margin retreat into below-sea-level interior) is NO+NE. *Fundamentals:* SMB melt
vs marine dynamic discharge is the first-order partition, and a third channel with the same
functional form on a shared driver "is not dynamically distinct". *Simplicity:* one sampled
scale instead of two, and only one share is independently identified anyway.

**WHAT DOES NOT CHANGE: the separation.** B1/B2/B3 give ssp585 2300 = 46.2 / 55.1 / 54.1 cm,
ratios **2.69× / 2.73× / 2.72×** — all inside the ridge ceiling. **No basin structure buys
the separation.** The tap stays load-bearing whichever is chosen.

**CAVEATS.** This is the Greenland-only offline cell — no BRICK coupling, no AR(1) noise,
none of the other likelihood terms. B2 and B3 are scored on DIFFERENT data by construction
(one independent share per window vs two), which is why the comparison is on shared terms
and each structure's own worst |z|, **never on total nlp**. And Mouginot sectors are
*drainage basins* while `t_gis_zones` are *latitude bands* (central 70–77 N, north 77–84 N)
— NW straddles both, so per-zone drivers can never cleanly carry sector geometry. That is an
argument for keeping geometry in the LIKELIHOOD, i.e. the single-amp design.

---

## 3. THE GATES, and the one that mutation-tests itself

* **G1 CROSS-LANGUAGE.** The Python 3-basin reproduces `julia/diag_l13_basin_shares.jl` on
  the same chain, same post-burn half, same medians: rate scales to 3.0e-06 / 3.2e-05,
  both windows' sector shares to <1e-3. **Worst deviation 0.48 of its tolerance.**
* **G2 INERTNESS.** Max |tap ramp| over 1900–2025, across all 108 (scenario, onset, τ)
  combinations: **exactly 0.0**. The likelihood-inertness claim from the predecessor
  handoff is now verified, which is what `gis_tap_likelihood_inert` asked for.
* **G2b FIRST-FIRE YEAR.** Added because "inert over the calibration window" is necessary
  but not sufficient. Inside the bracket the tap fires on **ssp585 only**, never before
  2100: 5.0 K → 2108, 6.0 K → 2136, 7.0 K → 2180, 7.81 K → 2300. On ssp126/ssp245 it fires
  **never**, at every admissible onset.
* **G3 NESTING.** V = 0 reproduces the base bit-identically on every scenario at both ends
  of the onset and τ grids.

**G2b CARRIES ITS OWN MUTATION TEST.** The out-of-bracket **4.00 K** onset fires in
**2088** and **4.69 K** in **2101** — so the detector provably has something to detect
(`mutation_test_gates`), and, unplanned, **the Tier-1 bracket's 4.69 K lower bound turns
out to be exactly the "do not move 2100" constraint.** Two independent derivations of the
same number: the TC 19:6887 stabilised-vs-continued arms, and ssp585's own 2100 GMT.

---

## 4. ITEM 2 — the offline A+B fit exists, and carried the same amp bug

The handoff said "locate or rebuild", and correctly ruled out `julia/fit_greenland_only.jl`.

| link | file |
|---|---|
| the cell fit | `python/gis_offline_cell.py` (`DRIVER_ZONE`, `FIT_WIN` 1900–2025) |
| the g = 0 re-fit | `python/diag_gis_g_betaf.py` — imports goc's model/objective/gates wholesale |
| the artefact | `outputs/gis_g_betaf_variants.csv`, row **`g=0`** |
| the consumer | `GIS_OFFLINE_G0` + the five `gis_*` prior centres, `calibrate_mcmc_ext.jl:1983` |

The `g=0` row is those constants bit-for-bit (cm ÷ 100), and
`julia/validate_gis_projection_ab.jl:45` already named the chain in a comment.

**THE TRAP FOR WHOEVER RE-DERIVES ON `all`: the centres are the g = 0 arm.** The headline
`A+B` row of `gis_offline_cell_fits.csv` has `c0 = 61.99 cm` at `g = 0.917`; the calibrator
uses `c0 = 4.04 cm` at `g = 0`. **Four of the five centres agree to 4 significant figures
either way, so `c0` alone looks like a 15× error if you check against the wrong file.**

**THE BUG — Class B again.** `AMP_MEAN` was `1.92`, a rounded south/full literal with no
reference to `DRIVER_ZONE`, while `AMP_PRIOR_CSV` was **defined and never read**. Identical
shape to the `gis_amp` prior fixed in `09eec0a` *one commit earlier*, and sitting in the one
tool the zone switch depends on. Now derived from `gis_amp_prior.csv` keyed on
`(DRIVER_ZONE, AMP_WINDOW)`: south **1.9221976**, all **2.3470378**.

**Blast radius, measured not assumed.** `AMP_MEAN` enters `splice_regional` ONLY, past
`last_obs_year`. `FIT_WIN` is 1900–2025 on the **observed** driver, so no fitted parameter
— and **none of the prior centres this script exists to supply** — can move. What it
corrupts is `proj_SSP*` and `spread_2100_cm`, the **G4 EVALUATION column**, which would
then have read as a result of the zone switch.

**Provenance cost:** south moves 1.92 → 1.9221976, so a re-run from HEAD is no longer
bit-identical to the artefacts `GIS_OFFLINE_G0` traces to. Same +0.0022 story as `GIS_AMP`.

**`--zone=<south|all|central|north>` is now a flag**, parsed in `gis_offline_cell` so it
reaches `diag_gis_g_betaf` through the import — one flag, both entry points. Outputs are
zone-tagged via `zoned()` for anything but south, because the south artefacts **are** the
provenance of the shipped calibration. Both gates mutation-tested.

**⇒ The item-2 prerequisite is much smaller than estimated.** The zone enters the whole
offline chain through one named constant. Re-deriving on `all` is a flag plus two script
runs, not a rebuild.

---

## 5. AN OBSERVATION, NOT A CLAIM

Base **G4 = 7.42 cm [5.63, 9.48]** sits **0.12 cm above** the 6.3–7.3 cm range
`gis_offline_cell.py` records from the four comparison models (MAGICC-SLR 7.09, emuGrIS
7.26, bamber19 7.23, FACTS FittedISMIP 6.34). It is an **ensemble median**, so the
comparison is legitimate — unlike the median-parameter version that once wrongly indicted
the shipped model. Being just above the top of a range of four models is not a failure.
Worth a look when L13 promotion is decided; **nothing in this handoff turns on it.**

---

## 5.5 DECISIONS TAKEN (Marcus, 2026-08-20)

**TAP CELL: onset 6.5 K / V 2.0 m / τ 50 yr** — candidate #5 of the six in §2.4.
Chosen over #2 (τ 100) on ROBUSTNESS, not fit: #2 sits at band position **0.09**, hard
against the bottom of the 1.732–3.127 m band, and the 2-basin restructure MOVES THE BASE
(the offline harness alone shifts ssp585@2300 by ~1 cm; a recalibration can move it more).
A band-edge cell can fall out under a base shift it had nothing to do with. #5 sits at
**0.40**, keeps V at **73%** of the NO+NE inventory rather than #4/#6's near-railing 92%,
and takes the onset at the design principle's minimum. τ 50 vs 100 is unconstrained either
way — no published gate. **This is a PRIOR SPECIFICATION, not a fit; say so in any methods text.**

| # | onset K | V m | τ yr | fires | 2200 m | 2300 m | ratio | band pos | V/inv |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 6.5 | 1.5 | 50 | 2155 | 0.834 | 1.832 | 10.32× | 0.07 | 55% |
| 2 | 6.5 | 2.0 | 100 | 2155 | 0.729 | 1.860 | 10.48× | 0.09 | 73% |
| 3 | 7.0 | 2.5 | 50 | 2180 | 0.521 | 2.004 | 11.29× | 0.19 | 92% |
| 4 | 6.5 | 2.5 | 100 | 2155 | 0.815 | 2.205 | 12.42× | 0.34 | 92% |
| **5 ✓** | **6.5** | **2.0** | **50** | **2155** | **0.984** | **2.283** | **12.87×** | **0.40** | **73%** |
| 6 | 6.5 | 2.5 | 50 | 2155 | 1.134 | 2.734 | 15.41× | 0.72 | 92% |

**BASIN STRUCTURE: TWO basins**, `active` = {SW,CW,CE,SE,**NW**} + `high` = {NO,NE},
`k = (0.628571, 0.371429)`, ONE sampled rate scale. **Three basins RETAINED as the
documented fallback** with named revert conditions — see memory `gis_two_basin_decision`.

### NO NEW MIMI COMPONENT IS NEEDED — verified bit-identical

`greenland_3basin` with **`k_mid = 0`** reproduces a genuine two-basin model EXACTLY:
`max |gis_sl_mid| = 0.0`, and active / high / total all differ by **0.000e+00 m**
(`array_equal` True). The two-basin model is a `k`-CONFIGURATION of the component that
already exists, so the nesting is exact by construction rather than by test.

**Three things the wiring must get right, none optional:**

1. **DROP `gis_s_mid` from `FREE`.** At `k_mid = 0` it multiplies a zero-commitment basin
   and does nothing. A dead sampled parameter is a random walk that inflates the proposal
   and hides defects.
2. **NK goes 59 → 58**, so no existing covariance matches by size ⇒ `embed_cov!` **BY
   NAME**. This is the third layout change in this arc and both previous ones bit
   (`ladrillo_adcov_size`, `nameless_matrix_order`).
3. **`GISB_TERM` switches to the 2-way targets**: active **0.799 / 0.816**, high
   **0.201 / 0.183**, σ 0.05. Only ONE share is independent now.

**Not yet done: the recalibration.** The offline evidence is the Greenland-ONLY cell — no
BRICK coupling, no AR(1) noise, none of the other likelihood terms. Whether it transfers to
the full calibrator is exactly what the recalibration tests, and it has not been run.

---

## 6. NEXT ACTIONS, in order

1. **Wire the 2-basin mode into `calibrate_mcmc_ext.jl`** per §5.5 — `k_mid = 0`, drop
   `gis_s_mid` from `FREE`, 2-way `GISB_TERM`, `embed_cov!` by name. Mechanical, but all
   three items are load-bearing. Then re-tune + production: **~7 h**, and the sequencing
   question is whether to run it on the current `south` zone (runnable NOW) or wait to
   combine it with `--gis-zone=all` (still blocked on item 4). **Ask before burning the run.**
2. **Wire the tap** at the decided cell (§5.5) on the projection side. Verify with the same nesting discipline — tap-on vs tap-off
   bit-identical to 2025, diverging only at the onset year; G2/G2b/G3 here are the offline
   versions of exactly that check. **AND re-test the Ṽ collapse of §2.4**, which is a
   property of the additive mock and may not survive the wiring.
4. **Run the `all` arm of the offline A+B fit** (`--zone=all`), now unblocked and cheap
   (§4). Adopting its centres into the calibrator remains a methodological choice.
5. **L13 promotion** — still open from 19d. L12 canonical meanwhile.
6. Only if a zone × amp factorial is bought: stand up Torch. The predecessor §4 verdict
   stands and §2 here strengthens it — the tap needed no chain at all.

**Open decisions for Marcus:** the tap cell; the basin structure; L13 promotion; whether
the D2G/D2S arms get re-run; whether to adopt `all`-driver prior centres.

**Housekeeping trap for the next session.** Two background waiters in this session hung on
a `pgrep -f <pattern>` **self-match** — the waiting shell's own command line contains the
pattern, so `! pgrep` is never true and the loop spins to timeout. Use `pgrep -f` with a
pattern that cannot match the waiter, or poll on an output file instead.
