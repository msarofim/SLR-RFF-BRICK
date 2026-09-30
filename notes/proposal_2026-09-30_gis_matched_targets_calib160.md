# PROPOSAL (not applied) — re-derive the Greenland matched 2300 targets on calib 1.6.0

2026-09-30 · branch `ladrillo-dev` · **awaiting Marcus**. Changing the calibration
version of a target is a methodological choice, so nothing canonical has been touched.
Everything below was **measured**. Each consumer ran in three copy-on-write clones of
this repo:

- **A** = calib 1.4.5 forcing (`839a176^`) + calib 1.4.5 targets. This is the state that shipped.
- **B** = calib 1.6.0 forcing + calib 1.4.5 targets. This is what any re-run since 08-28 gives.
- **C** = calib 1.6.0 forcing + calib 1.6.0 targets. This is the proposal.

Re-run the measurement with `scripts/measure_gis_target_retarget.sh <empty-dir>` and
`scripts/compare_gis_target_retarget.py`.

## 1. The premise, verified

| file | rebuilt from | result |
|---|---|---|
| `outputs/scope_gis_cool_band_targets.csv`, `outputs/gis_matched_targets_2300.csv` (canonical) | 1.4.5 forcing | **byte-identical** |
| `outputs/*_calib160.csv` (12ba837) | today's 1.6.0 forcing | **byte-identical** |

So the canonical targets rest on calib 1.4.5. The forcing moved as follows:

| our GMST | T2300 (K, 11-yr), 1.4.5 → 1.6.0 | 2015-2300 integral (K·yr), 1.4.5 → 1.6.0 |
|---|---|---|
| ssp585 | 7.80 → 7.48 | 1626 → 1539 |
| ssp245 | 3.14 → 3.16 | 790 → 786 |
| ssp126 | 1.73 → 1.80 | 495 → 510 |

The PROTECT anchors themselves do not move; only our predictor does.

| band (cm, rel 2015) | calib 1.4.5 (canonical) | calib 1.6.0 |
|---|---|---|
| SSP1-2.6 | 6.2–15.9 (UNION rule) | 6.2–15.9 (UNION, unchanged) |
| SSP2-4.5 | 10.6–21.5, p50 15.4 | 10.5–21.2, p50 15.3 |
| SSP5-8.5 | 42.9–145.0, p50 98.5 | **37.2–129.7, p50 86.9** |
| 585/245 p50 ratio | 6.40 | **5.69** (5.68 from the 3-dp literals) |
| `ratio_band()` 585/245 | 2.00–13.7 | 1.75–12.4 |

## 2. The complication: the MODEL side has two vintages too

The target should carry the vintage of the forcing that the model it scores was run on.
The two model sides are **not** on the same vintage:

| model side | forcing (identified from the file's `gmst` column at 2300) |
|---|---|
| `ssps_components_2300_L27*.csv`: the paper posterior, Table/GMD numbers | **calib 1.6.0** (7.4984 K = 1.6.0 exactly) |
| `ssps_components_2300_L14*.csv`: the 08-21..23 Greenland design arc | **calib 1.4.5** (7.8148 K) |
| every shipped consumer output (all dated 08-21..08-23) | calib 1.4.5 model vs calib 1.4.5 target: **internally consistent** |

- **Shipped outputs are not wrong.** They are a consistent calib 1.4.5 record.
- **The live hazard is re-running.** Any consumer re-run today puts a 1.6.0 model
  (read from `fair_mean_gmst_*` at runtime) against 1.4.5 targets.
  - Most consumers do this **silently**.
  - Three refuse on their own gates:
    - `scope_gis_basin_mock_vs_literature` and `scope_gis_basin_zonespace_vs_literature`
      fail the "GMT frame check: SSP1-2.6 @2300 = 1.815 vs recorded 1.74".
    - `scope_gis_ridge_vs_ssp_bands` fails because the offline model differs from the
      shipped L14 projection by 2.35 cm.
- **The paper (L27, 1.6.0) needs the 1.6.0 target.** The GMD draft's 5.7 is therefore
  the like-for-like number, and the canonical 6.40 is not (§5).

## 3. Consumers

**Read `MATCHED_2300_M` / `MATCHED_2300_P50_M` directly (13):**
- `diag_gis_amp_above_275`
- `diag_gis_cascade_rate_crit`
- `diag_gis_committed_loss` (comment only)
- `diag_gis_k_vs_residual`
- `diag_gis_matched_band_score` (also reads the CSV)
- `diag_gis_npv_tau_sensitivity`
- `diag_gis_residual_band` and `diag_gis_scorecard_logo` (both also read
  `scope_gis_cool_band_targets.csv` and import `build_gis_matched_targets.interp_log`)
- `diag_gis_separation_target`
- `scope_gis_gamma_offline`
- `scope_gis_onset_rescan`
- `scope_gis_reservoir_offline`
- `scope_gis_reservoir_rate_rank`

**Via `from_argv` / `get()` (default set = matched), plus `ratio_band` / `banner` (9):**
- `scope_gis_leq_ridge_vs_literature`
- `scope_gis_basin_mock_vs_literature`
- `scope_gis_basin_zonespace_vs_literature`
- `scope_gis_rate_power_vs_literature`
- `scope_gis_ridge_vs_ssp_bands`
- `scope_gis_3basin_partition`
- `scope_gis_tap_l13`
- `plot_gis_basin_mock`
- `plot_gis_rate_power_scan`

**Hard-coded copies:** these would NOT follow a literal change.
- `python/diag_gis_2150_band_veto.py:93` has `P50_2300_CM = 98.5`, and on **:94 a 1.4.5 MODEL
  value** `BASE_OURS_2300_CM = 49.9`. The 1.6.0 base is 47.7.
- `julia/diag_gis_cell_vs_priority_ladder.jl:67` has `MATCHED_2300 = (lo = 42.9, p50 = 98.5, hi = 145.0)`.
- `python/diag_gis_stepback_rate_crit.py:110` has the label "matched p50 98.5".

**Prose quoting the 1.4.5 numbers:**
- `gis_targets.py`: the module docstring ("173-313 cm -> 43-145 cm, a factor 0.39") and
  the `LIT_2300_FORCING` "OURS 7.80 K (int 1626)" strings.
- `scope_gis_gamma_offline.py:23`
- `scope_gis_reservoir_offline.py:17`
- `diag_gis_matched_band_score.py:16`
- `diag_gis_committed_loss.py:113`
- `diag_gis_cascade_rate_crit.py:318`

**Builders:** `scope_gis_cool_band_forcing.py` → `build_gis_matched_targets.py`.
`build_protect_cool_forcing.py` and `diag_gis_gcm_tdecomp.py` import helpers only.

**NOT consumers:**
- `bench_ladrillo.py`: the [S] separation block scores against the FACTS/MAGICC bracket,
  not these targets.
- The calibrator: no Julia calibration file references them.
- The deliverable redline scripts `r0930/edits_c.py` and `comments_0930.py` quote the
  calib160 file.

**Tests:** there is no test suite covering these. The only guard is `gis_targets._verify()`.

## 4. What changes, measured

"A" is the shipped state; A reproduced 15 shipped consumer outputs, plus both target CSVs,
byte-for-byte, so it is faithful.

**Headline cells**

1. **`diag_gis_matched_band_score`, WINNER cell (ssp585, adopted integral arm).**
   - ours/p50: A **1.009×**, B 0.957×, C **1.085×**.
   - Percentile: A 51, B 43, C 58.
   - In band in all three. "Lands on the p50" survives, but moves from 51st to 58th percentile.
2. **Cell A (70 cm)**: percentile 12.8 (A), 11.3 (B), 15.9 (C).
3. **The no-reservoir base**: in band in all three (47.2 > 37.2). Percentile 5.6 (A), 5.3 (B), 6.8 (C).
4. **Julia ladder, shipped cell (L14 + V 5.64) at SSP5-8.5 2300, versus the matched p50.**
   These compare today's code in both sandboxes. The shipped CSV itself is not reproducible:
   kernel drift since 08-23 moves values up to 1.2 cm.
   - A: 95.9 / 98.5 = **0.973**
   - C: 89.2 / 86.9 = **1.026**
5. **Separation, shipped L14 cell.**
   - ssp585/ssp245 ratio: 5.25× on 1.4.5 = 0.82 of 6.40; 4.82× on 1.6.0 = **0.85 of 5.68**.
   - Original BRICK: 1.87× → 1.78×.
   - Untapped: 2.74× → 2.59×.
6. **L27, the paper posterior**, read directly from `ssps_components_2300_L27_tap…ws.csv`.
   Values are a difference of medians (2300 − 2015), an approximation.
   - SSP5-8.5 85.9 cm: **0.872×** p50 (1.4.5 target) vs **0.988×** (1.6.0 target).
     In band either way.
   - Separation: tapped 4.64 = 0.73 of 6.38, or **0.82 of 5.69**; untapped 2.41, as the draft says.
7. **`diag_gis_amp_above_275`, cell B.** The flux ratio psi_level/psi_rate for the shipped law:
   **A 0.97, B 1.07, C 0.83**.
   - A like-for-like re-score moves cell B from 3 % short to 17 % short.
   - The mismatched B run would have reported the opposite sign.
8. **`diag_gis_2150_band_veto`.** Required delivery ratio R: 6.03 (A).
   - C as run: 4.59, still on the 1.4.5 base.
   - C with the 1.6.0 base (derived; R is linear in the required addition): **4.86**.
   - "n = 2 is enough, n = 1 is not" (n = 1 reaches 2.66) **survives**.
9. **`scope_gis_gamma_offline`.** The p50 needs ×2.06 (A), ×1.82 (C); the ceiling is ×1.13.
   "NOT REACHABLE by any gamma" **survives**.
10. **`diag_gis_npv_tau_sensitivity`.** SSP2-4.5 headroom: OVER by 7.4×/17.7× (A) and
    8.0×/19.2× (C). The verdict is unchanged.

**Scan counts (in-band / pass), A → B → C**

| scan | quantity | A | B | C | which cells |
|---|---|---|---|---|---|
| `scope_gis_onset_rescan` | ssp585_in_band / 210 | 184 | 186 | 180 | 6 hot cells whose 2300 lands at 130–145 cm (onset ≤ 2.85 K with V ≥ 6 m, τ 1600; and 4.69 K / 4.5 m / 800). The shipped cell is not on this grid. |
| `scope_gis_reservoir_offline_tolspread` | ssp585 in_matched / 216 | 200 | 202 | 195 | 7 cells at 130–154 cm |
| same | all_pass / 216 | 178 | 179 | 178 | one cell (V 1.5, onset 6.5 K, τ 100) flips in under B and back out under C |
| `scope_gis_reservoir_rate_rank` | in_matched / 1080 | 1027 | 1034 | 1010 | its own repro gate refuses in all three, see §6 |
| `scope_gis_tap_l13` | all_pass | 105 | 112 | 104 | 8 legacy L13 first-order cells at 1.30–1.45 m |
| `scope_gis_leq_ridge_vs_literature` | in_band SSP5-8.5 / 13 | 8 | 8 | 7 | |
| `scope_gis_rate_power_vs_literature` | in_band SSP5-8.5 / 117 | 43 | 43 | 42 | |
| `diag_gis_residual_band` | ssp585 count / 132 | 102 | 102 | 92 | |

**Byte-identical between B and C:**
- `cascade_rate_crit`
- `committed_loss`
- `k_vs_residual`
- `3basin_partition`
- the `gamma_offline` and `npv_tau` CSVs
- the `2150_band_veto` CSV (console-only changes)

**Pattern.** Every flip is a hot-edge cell whose SSP5-8.5 at 2300 lies between 129.7 and
145 cm, the slice the new band ceiling cuts off. No pass/fail verdict on the shipped cell
changes. Two ratios do cross 1.0:
- the shipped cell's ratio to the p50 (item 4: 0.97 → 1.03, now slightly ABOVE the central
  estimate);
- `amp_above_275`'s cell-B ratio (item 7), and cell B is not the shipped cell.

## 5. The GMD draft

`deliverables/GMD.Ladrillo.v1_review-2026-09-30_L27.docx` (edit `r0930/edits_c.py`, reply
#4) reads "well below the 5.7 implied by process-model runs at matched forcing". That
number comes from `gis_matched_targets_2300_calib160.csv`.

- It is **correct like-for-like**: L27's projections are on 1.6.0.
- Until a decision is made, the draft and the repo's canonical target **disagree**
  (canonical 6.40). Every gate and scorecard still reads 6.40.
- The draft's 2.4 (untapped) and 36.5 cm come from L27, so they are also 1.6.0.

## 6. Found on the way: not caused by the migration

These fail identically in the A sandbox.

1. **`scope_gis_reservoir_rate_rank` repro gate is stale.** It hard-codes (135, 86); the
   shipped tolspread scan gives (178, 114) on the original forcing. The shipped
   `scope_gis_reservoir_rate_rank.csv` is not reproducible.
2. **`plot_gis_basin_mock.py` and `plot_gis_rate_power_scan.py` crash** with
   `NameError: name 'lf' is not defined` (last touched 09-26).
3. **`diag_gis_residual_band.csv` and `diag_gis_scorecard_logo.csv` do not reproduce on 1.4.5.**
4. **`diag_gis_cell_vs_priority_ladder.csv` does not reproduce from today's code.**
   91 of 96 rows differ by ≤ 1.2 cm, from kernel changes since 08-23.
5. **`_verify()` checks band endpoints only.**
   - `MATCHED_2300_P50_M` is never checked: by inspection, `_verify()` reads only
     `band_lo_cm` / `band_hi_cm`.
   - The SSP1-2.6 P50 literal (0.111) is the **r2300 anchor median**, while the CSV's
     `matched_p50_cm` (13.8, 12.7 on 1.6.0) is what `diag_gis_matched_band_score` reports.
     Two definitions under one name.
6. **The target CSVs carry no forcing-vintage provenance.** The builders write the
   canonical path unconditionally. `_verify()` does catch a silent re-build: canonical
   literals against the calib160 CSV are **REFUSED** (mutation-tested today). But it
   cannot tell a calib label.

## 7. Proposal (for decision)

**Recommended: make the calibration vintage an explicit axis instead of overwriting one set with the other.**

1. `gis_targets.py` carries both sets, `MATCHED_2300_M_BY_CALIB = {"1.4.5": …, "1.6.0": …}`
   (same for P50).
   - The default is **1.6.0**, the paper standard.
   - `_verify()` checks each set against its own CSV, P50 included.
2. Files:
   - The canonical path becomes the 1.6.0 table.
   - The 1.4.5 table moves to `outputs/quarantine/20260930_gis_matched_targets_calib145/`
     with a README naming this note. `gis_targets` reads it from there, per the rule that a
     gate reads the quarantine copy.
   - The `_calib160` duplicates are removed once the canonical path equals them byte-for-byte.
3. Add a `provenance` column to both target CSVs recording calib, forcing file and md5,
   commit, and predictor.
4. Add a gate in the consumers: the md5 of the `fair_mean_gmst_*` a consumer reads must
   match the md5 recorded in the target it scores. A 1.6.0 model can then never be
   scored against a 1.4.5 target, and the B cell above becomes impossible rather than silent.
5. Route the hard-coded copies (`2150_band_veto:93-94`, Julia ladder `:67`, stepback `:110`)
   through `gis_targets`. The Julia script reads the CSV.
6. **Re-run on 1.6.0:** the consumers that pass their own gates on 1.6.0 (the C column).
   - Quarantine their 1.4.5 outputs to the same directory first.
   - Consumers whose gates refuse on 1.6.0 (basin_mock, zonespace, ridge_vs_ssp_bands)
     need their recorded GMT frames and the L14 Julia projections re-run on 1.6.0.
     That is a separate decision: the L14 design arc is closed, so the alternative is to
     leave them explicitly labelled calib 1.4.5.
7. Memory `gis_matched_band_predictor` (1.009×, pctile 51, 42.9–145.0) gets a
   "calib 1.4.5, L14" label, and the 1.6.0 values from §4.

**Alternative:** overwrite the canonical path with 1.6.0, change the literals, and
quarantine the 1.4.5 CSVs. This is simpler, but every consumer that is not re-run then
scores a stale 1.4.5 output against nothing, and the vintage axis stays implicit.

**Decisions needed:**
- (a) recommended vs alternative;
- (b) re-run L14 on 1.6.0 for the three gated consumers, or label them 1.4.5;
- (c) whether the SSP1-2.6 P50 should be the anchor median (11.1) or the extrapolated
  matched p50 (12.7).
