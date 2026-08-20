# Handoff — the tap is PRICED, the offline A+B fit is LOCATED, and L13 fixed the partition but not the separation

**Start-here document.** Repo `SLR-RFF-BRICK`, branch **`ladrillo-dev`**.
Predecessor: `notes/handoff_2026-08-20_gis_zone_and_tap.md`.
Commits: `1b2c90a` (offline fit), `6c4f907` (tap pricing).

**Bottom line. (1) THE TAP CLEARS. 25 of 140 admissible cells pass every gate at ratio
9.77–16.41×, and the tap moves ssp126/ssp245 by EXACTLY zero. (2) BUT L13 ALONE DOES NOT.
Its own untapped ssp585/ssp245 2300 ratio is 2.71× against the literature's 7.9–31.9× —
inside the single-law ridge ceiling. The sector restructure fixed the PARTITION, not the
SEPARATION, exactly as predicted; the tap is still load-bearing. (3) Item 1 was blocked on
a prerequisite nobody had spotted: there was no L13 posterior subsample. (4) Item 2's
offline A+B fit EXISTS and needed no rebuilding — but it carried the SAME amp bug the
calibrator had fixed one commit earlier.**

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

## 6. NEXT ACTIONS, in order

1. **Decide the tap's cell.** The scoping delivers a 25-cell plateau, not a point. Picking
   (T_on, V, τ) is a methodological choice: it is a prior specification for a
   projection-side mechanism, and it should be stated as one rather than tuned. The plateau
   is wide (every τ 50–200, every V 1.5–2.5, onsets 5–7 K), so a defensible default is the
   centre of it rather than an extremum.
2. **Wire the tap into `greenland_3basin_component.jl`** on the projection side, and verify
   with the same nesting discipline: tap-on vs tap-off bit-identical to 2025, and diverging
   only at the onset year. G2/G2b/G3 here are the offline versions of exactly that check.
3. **Run the `all` arm of the offline A+B fit** (`--zone=all`), now unblocked and cheap.
   Adopting its centres into the calibrator remains Marcus's call.
4. **L13 promotion** — still open from 19d.
5. Only if a zone × amp factorial is bought: stand up Torch (predecessor §4 stands, and
   §2.2 here strengthens it — the tap needed no chain).

**Open decisions for Marcus:** the tap cell (item 1); L13 promotion; whether the D2G/D2S
arms get re-run; whether L13's mid-basin −1.09 z justifies a second rate-scale knob;
and whether to adopt `all`-driver prior centres.
