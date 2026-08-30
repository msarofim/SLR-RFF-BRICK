# Handoff — van Vuuren GMST/OHC cubes exist; the "4 models" premise is half-false

**Start here.** Repos `SLR-RFF-BRICK` (branch `ladrillo-dev`) and `FaIRtoFrEDI`
worktree `.claude/worktrees/optimistic-swartz-112637` (branch `claude/calib160-migration`).
Written 2026-08-31 to be picked up cold. Supersedes nothing; extends
`handoff_2026-08-30_documentation_ready.md`, whose five `[MARCUS —]` placeholders are STILL the
document's blocker and are untouched here.

---

## 0. WHAT MARCUS ASKED, AND WHAT IS ACTUALLY POSSIBLE

Asked (2026-08-31): build the van Vuuren cubes; do NOT match the previous cube convention just for
comparability — go non-stochastic if that makes more sense; then **drive all 4 SLR models** with the
new cube for a fully consistent set, after which "the SSPs might become superfluous".

⚠ **ONLY TWO OF THE FOUR SOURCES CAN BE DRIVEN, AND THE SSPs DO NOT BECOME SUPERFLUOUS.**

| source | drivable on van Vuuren? |
|---|---|
| Ladrillo | ✅ ours |
| BRICK 2.0 | ✅ ours |
| MAGICC-SLR | ❌ `data/comparison/magicc_nauels_components.csv` is a ONE-TIME EXTRACT. `python/extract_magicc_components.py` states the run "lives in the members-only MAGICC working copy". A local tree exists at `~/Documents/2026/CodeProjects/MAGICC` (magiccv.7.5.3 + drawnset + slr-refresh), so a van Vuuren MAGICC run is *conceivable* as a separate track — but it would be driven by van Vuuren EMISSIONS through MAGICC's OWN climate, not by our cube. Driving it with our GMST would destroy the independence that makes it a comparator. |
| FACTS | ❌ `outputs/facts_components_n200.csv` is an ingested n=200 quantile table, 2964 rows, ssp126/245/585 only. No FACTS install, no builder script in the repo. |

`python/ladrillo_model_comparison.py:76` already says it: `SCENARIOS = ["ssp126","ssp245","ssp585"]
# the three all four sources share`. **The SSP set is an INTERSECTION with the published
literature, not a preference.** Dropping it deletes 6 of 8 columns from the model document's
validation table (AR6 T9.9 + FACTS wf1f/wf2f/wf3f/wf4 + MAGICC-SLR + BRICK 2.0) with nothing to
replace them. Whether anyone has published SLR under the CMIP7 markers was NOT checked; the set is
~3 months old so probably not, but that is an expectation, not a citation.

**Recommendation: keep SSPs as the COMPARISON basis, add van Vuuren as the PROCESS/COMMITMENT
basis.** Not a replacement — a second axis.

---

## 1. WHAT WAS BUILT

`FaIRtoFrEDI/scripts/build_fair_cube_vv_v160.py` (new, in the worktree beside its SSP counterpart
`build_fair_cube_v160.py`). 7 markers x {gmst,ohc} x {cube,mean} = **28 files** in
`SLR-RFF-BRICK/data/observations/`, scenario keys `vvH vvHL vvM vvML vvL vvLN vvVL`. **12 s per
marker.** Schema is byte-compatible with the SSP cubes (1850-2300, 6-dp, 1850-1900 rebase-then-
average, full-range means), so every consumer resolves them by scenario key with NO edit.

**THE UNEXPECTED WIN — the marker forcing stops being an approximation.**
`calibration_v160_prod/README.md`, on the SSP cubes: *"no CMIP7 marker **is** a CMIP6 SSP, so a
driver must name the marker it uses ... It does affect projections to 2300 and is an **open
question** for ssp126/ssp585."* 1.6.0 ships land-use + irrigation forcing for the seven CMIP7
markers; the SSPs borrow them through a lossy mapping (ssp126→L, ssp245→M, ssp585→H) measured at
0.022-0.094 K at 2100/2300. **On van Vuuren each marker uses its own `volcanic_solar_<MARKER>.csv`
and that ambiguity is identically zero.** This is the one thing van Vuuren gets for free that the
SSPs cannot.

⚠ **NOT `calibration_v160/`** — it deviates from stock 1.6.0 (Land use forced `calculated`,
Irrigation as one shared 7-marker mean) for the VV-vs-RFF percentile comparison; the land-use
deviation alone is 0.025 K of historical fit. The pre-existing
`fair_outputs/vanvuuren_ext_harmonized_erf_cube_v160.npz` was built against THAT dir and the single
generic `volcanic_solar.csv`, so **it is not the ERF counterpart of these cubes.**

GMST (K rel 1850-1900), median of 841:

| marker | 2050 | 2100 | 2300 | | SSP | 2050 | 2100 | 2300 |
|---|---|---|---|---|---|---|---|---|
| Very Low (SSP1) | 1.69 | 1.55 | 1.09 | | ssp126 | 1.79 | 1.83 | 1.67 |
| Low-to-Negative | 1.78 | 1.65 | 0.25 | | ssp245 | 1.88 | 2.60 | 2.95 |
| Low (SSP2) | 1.72 | 1.74 | 1.16 | | ssp585 | 2.10 | 4.18 | 7.11 |
| Medium-to-Low | 1.82 | 2.26 | 0.49 | | | | | |
| Medium (SSP2) | 1.85 | 2.78 | 4.00 | | | | | |
| High-to-Low (SSP5) | 1.98 | 2.74 | 1.28 | | | | | |
| High (SSP3) | 1.94 | 3.22 | 6.27 | | | | | |

All seven return **mean GMST 2024 = +1.2725 K identically** — the shared-CMIP7-history identity
holding, and a free correctness check.

---

## 2. STOCHASTIC IS **OFF**, AND THE MEASUREMENT REFUTED MY OWN REASONING

1.6.0 sets `stochastic_run=True` with 841 distinct seeds, so the SSP cubes carry internal
variability. `scripts/diag_vv_stochastic_ab.py` (2 markers x both settings) decides it, and is kept
runnable so the decision can be re-checked instead of remembered.

⚠ **Three of the four a priori arguments for determinism were FALSE.**

| claim | measured |
|---|---|
| "it inflates the joint band" | p17-p83 ratios **0.989-1.028**. Worth 0-3%. FALSE |
| "TE integrates it, so it accumulates" | OHC band ratio at 2300 = **0.999**. Does not happen. FALSE |
| "it manufactures spurious scenario differences" | exactly **0** over 1850-2023 where forcing is identical; **0.028 K** later = **0.54%** of the 5.18 K H-VL signal. FALSE |
| "noise is not forced-response uncertainty" | survives — an argument about MEANING, not magnitude |

**POWER CHECKED FIRST** (else every null above is vacuous): noise sd **0.1103 K**, lag-1 autocorr
0.339 — realistic annual variability. The gate errors if sd < 0.02 K.

The one residual effect: an arbitrary seed-dependent ensemble-mean offset of **±0.005 K**, against
its own first-principles prediction `sd/sqrt(841) = 0.0038 K` (observed 1.2-1.4x). Pure artifact,
removable at no measurable cost — so removed.

⚠ **Corollary worth carrying into the document: the EXISTING SSP joint bands are NOT materially
contaminated by internal variability.** That retires a concern nobody had measured.

---

## 3. TWO DRIVER FIXES (both in `SLR-RFF-BRICK/julia/`)

**(a) `scope_slr_fair_uncertainty.jl` could not run any non-SSP scenario.** It passed the projection
scenario into `MimiBRICK.get_model`, which loads a bundled `sneasy_temperature_<ssp>_*.csv`; `vvH`
died after 3 min with "No file exists". But `set_forcing!` overwrites BOTH bundled inputs
(`model_global_surface_temperature`, `thermal_expansion.ocean_heat_interior`) on the next line, and
`scope_slr_fairunc_oldbrick.jl:113` ALREADY hardcodes `ssprcp_scenario="ssp245"` for exactly this
reason — which is why the BRICK 2.0 joint arm ran on van Vuuren unmodified and this one did not.
Now a named `BUILD_SSP = "ssp245"`, overridable via `--build-ssp=`.

⚠ **VERIFIED, NOT ASSERTED.** `--ssp=ssp585 --build-ssp=ssp585` (the old behaviour) and
`--build-ssp=ssp245` (the new) produce **bit-identical** CONTROL rows — `ais @2300 -0.5180`,
`total @2300 -0.2279` to the digit. The build scenario provably cannot leak. The `--build-ssp=`
flag exists SO THAT this stays testable.

**(b) Both `[CONTROL]` gates keyed off a Dict with no `vv` entry** (KeyError). They now print
`[CONTROL] SKIPPED -- <ssp> has no shipped panel row` and say the fixed-arm code path is verified by
the SSP runs, not by this one. While there, closed a **latent vacuous pass** in the Ladrillo one:
its `if nrow(r) == 1` would have silently compared ZERO cells had a label existed. It now counts
cells and errors on zero, matching what oldbrick already did.

⚠ **I REINTRODUCED THE `gsic_match_gate_was_vacuous` DEFECT WHILE FIXING IT** — `ncontrol += 1`
inside a top-level `for` binds a NEW Julia local. It errored on an undefined variable rather than
silently counting zero, which is the only reason it was cheap. Fixed with a `let`. **The lesson has
to be re-applied to each NEW gate, not remembered about the old one.**

---

## 4. ⚠ PRE-EXISTING, NOT CAUSED HERE: `ais @2300` is over CONTROL tolerance

`[CONTROL] ais @2300 fixed 268.219 vs shipped 268.737, diff -0.5180 cm -> CHECK` against
`CONTROL_TOL_CM = 0.5`. **Not mine** — identical under both build scenarios. The two runs agree
bit-for-bit with each other, so the driver is deterministic; the difference is between
`scope_slr_fair_uncertainty.jl`'s fixed arm and the panel shipped by
`project_ssps_components_ladrillo.jl` on 2026-08-30. 0.19% of 268 cm, and `ais @2150` sits at
-0.4666, just INSIDE the same tolerance. **AIS@2300 is a headline number in the model document —
worth knowing before publishing it, and worth deciding whether the tolerance or the cross-driver
gap is the thing to fix.** Untouched here.

---

## 5. RESULTS SO FAR

**BRICK 2.0 joint arm, all 7 markers** (26 s each), total GMSL cm rel 1995-2014, med [p05,p95]:

| marker | 2100 | 2150 | 2300 |
|---|---|---|---|
| Very Low | 37.8 [29.3, 99.7] | 52.0 [40.0, 154.9] | 80.7 [62.5, 244.5] |
| Low-to-Negative | 39.5 [30.5, 102.8] | 52.8 [41.0, 146.5] | 65.2 [53.1, 159.9] |
| Low | 39.7 [30.8, 103.4] | 55.3 [42.8, 166.5] | 83.9 [65.0, 260.8] |
| Medium-to-Low | 52.0 [34.1, 115.9] | 74.2 [48.0, 196.6] | 92.6 [63.9, 252.5] |
| Medium | 71.1 [39.0, 120.3] | 145.2 [68.0, 222.8] | 346.6 [203.2, 529.9] |
| High-to-Low | 84.5 [41.4, 130.5] | 133.2 [57.0, 220.3] | 162.5 [78.4, 346.4] |
| High | 81.9 [45.4, 128.5] | 165.0 [106.2, 244.7] | 414.0 [272.5, 652.1] |

⚠ **THE RESULT THAT JUSTIFIES THE WHOLE EXERCISE.** High-to-Low at 2100 (84.5) EXCEEDS High (81.9).
I first called that an inversion; it is not. **HL is warmer than H from ~2040-2090, peaking +0.18 K
at 2073**, then crosses below (2100: -0.46 K). The deterministic FIXED arm shows the same +3.02 cm,
so it is not sampling noise. Componentwise: **AIS +3.63 cm** (responds to the EARLY warming) against
**TE -0.70 cm** (tracks the cooler endpoint). **That is a path-dependence signal, with the components
splitting in opposite directions, that the SSP set structurally cannot produce** — the SSPs differ in
LEVEL, HL-vs-H differs in TIMING. For a commitment-focused SLR paper this is the payoff.

Four genuine peak-and-decline pathways (VL, LN, ML, HL) vs the SSPs' one (ssp119).

**Ladrillo joint arm: ALL 7 DONE** (commit `f37a6d4`), each with `[CONTROL] SKIPPED`, no errors.
Both models on the SAME cube, so widths are like-for-like. Ladrillo/BRICK 2.0 p05-p95 width ratio,
total @2300: Very Low 0.28 | Low 0.26 | Low-to-Negative 0.30 | Medium-to-Low 0.67 | High-to-Low 0.77
| Medium 1.17 | High 0.95.

⚠ **THIS REPLICATES THE COOL-SCENARIO UNDER-DISPERSION on a different scenario family** (the 08-30
SSP result: 2.8x at ssp126/2100, 4.4x at ssp126/2300, ~13% at ssp585). Seven points trace a monotone
gradient where three could not.

⚠ **AND IT SEPARATES PEAK FROM ENDPOINT WARMING.** VL, L, LN and HL all END between 0.29 and 1.38 K
while their PEAKS span 1.76-2.96 K; the ratio tracks the PEAK (0.26-0.30 cool-peaking, 0.77 for HL),
Spearman **+0.93 peak vs +0.64 endpoint**. **n = 7 -- a direction to check, NOT a test**; the CI on
rho at n=7 is very wide. Recorded as a hypothesis for C7-adjacent work. The SSP set cannot pose the
question at all, since its peak and endpoint are near-monotonically related.

Medians: Ladrillo below BRICK 2.0 everywhere except High @2300 (413.8 vs 414.0 cm).

(superseded note) Ladrillo was still running at first writing: (7 markers x ~8 min). Logs at
`<scratch>/lad_vv<MARKER>.log`; outputs `outputs/scope_slr_fairunc_{cells,paths,gates}_vv<M>_spliced_L21_tap4p69K_V5p64m_tau800.csv`.
**Check each for `ladrillo vv<M> OK` and a `[CONTROL] SKIPPED` line before using them.**

---

## 6. NEXT

* **Finish/verify the 7 Ladrillo runs**, then build the 2-model VV comparison. NOTE
  `ladrillo_model_comparison.py` hardcodes the 3 SSPs at line 76 and loads FACTS + MAGICC; a VV
  table is a DIFFERENT object (2 columns, 7 markers) and should be a sibling script, not a flag on
  that one — do not let a VV run silently produce empty FACTS/MAGICC columns.
* **The glacier commitment figure** (`plot_ssps_gsic_wr_vs_mengel.py`) is the best candidate to move
  to van Vuuren: it needs no external comparator, and VV's four decline pathways test
  Wigley-Raper-commitment vs Mengel-stabilization far better than ssp119 alone. It would ALSO
  dissolve that figure's mixed-vintage caveat (see the 08-30 CHANGELOG entry), since all 7 markers
  come from one build on one calibration.
* **Committed:** `SLR-RFF-BRICK` 0c11029 (Mengel arms), 6cc34b6 (cubes + driver fixes + BRICK 2.0), f37a6d4 (Ladrillo x7); `FaIRtoFrEDI` worktree `claude/calib160-migration` 7fde943 (builder + stochastic A/B).
* The five `[MARCUS —]` placeholders remain the model document's only blocker.
