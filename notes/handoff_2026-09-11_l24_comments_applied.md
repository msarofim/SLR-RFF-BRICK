# Handoff — L24 deliverable: 9/11 comments applied; four tasks queued for the next session

**Start here.** Work done 2026-09-10 → 09-11 in one long session (the "LWS / forcing / captions"
arc). Supersedes nothing; `handoff_2026-09-09b_recalib_questions_closed.md` is still the record
for the recalibration rulings, which are unchanged. **Read this note plus `INDEX_slr.md` and
`INDEX_slr_obs.md` before touching the deliverable or the hindcast comparison.**

**STATUS: `SLR-RFF-BRICK` `ladrillo-dev`, clean, NOT PUSHED.** `FaIRtoFrEDI` clean.
> ⚠ Do not type a commit count ([[status_field_carries_the_query]]). Run
> `git -C ~/Documents/2026/CodeProjects/SLR-RFF-BRICK rev-list --count origin/ladrillo-dev..HEAD`.
> A concurrent SLEIP session commits to the same branch — check `git log` authorship before pushing.

**TORCH VERDICT (standing, say it out loud):** every task below is LOCAL — none is a chain.

---

## 1. ⭐ THE FOUR TASKS FOR THE NEXT SESSION (Marcus, 09-11)

All four come from Marcus's 9/11 comments file
(`deliverables/Ladrillocomments.9.11.23.docx`, items [1], [9], [12]) — the three of thirteen that
could not be closed by editing. Ten were applied (§4).

### 1a. Extend the FACTS **SSP** runs to 2300
- **Why:** FIG 8 (the SSP comparison at 2300) has no FACTS bars. FACTS already runs to 2300 for
  the **van Vuuren** set — CHANGELOG **2026-09-02e**: *"eight configs in the FACTS repo set
  `pyear_end: 2300`… runs to 2300 with no change: 26 outputs per arm… built as SEPARATE `*2300`
  experiments so the twelve 2150 configs stay byte-identical."* The SSP set was simply never given
  the same treatment. Evidence it is missing: `outputs/ladrillo_model_comparison_L24.csv` carries
  FACTS at 2100 and 2150 only; `outputs/vv_model_comparison_L24.csv` carries 2100/2150/**2300**.
- **How:** follow the 09-02e recipe — separate `*2300` experiments, horizon carried in the climate
  file's own `PyearEnd` attribute (the config builder reads it, so a config cannot disagree with
  its climate). FACTS repo is `~/Documents/2026/CodeProjects/facts`. Then re-run
  `python/ladrillo_model_comparison.py --tag=L24` and `plot_model_comparison_components.py --tag=L24`
  (SSP set), and **change the FIG 8 caption back** — it currently says *"the FACTS SSP runs used
  here stop at 2150"*, which becomes false the moment this lands.
- ⚠ Keep the 2150 SSP configs byte-identical (the 09-02e discipline); do not extend in place.

### 1b. Run MAGICC pre-2000 (the history)
- **Why:** Marcus's comment [1] asks whether MAGICC's *historical* Greenland matches
  observations. **No MAGICC component series before 2000 exists in this repo.** The extractor
  `python/extract_magicc_components.py:47` hard-codes `YEARS_OUT = range(2000, 2301)`, and its
  own comment (lines 37–46) records that the SOURCE run spans **through 2305** — the 2000 cut is
  ours. Whether the source ALSO spans pre-2000 is the first thing to check.
- **Where the MAGICC side lives:** source file at
  `~/Documents/2026/CodeProjects/MAGICC/slr-refresh/data/processed/…` (`extract_magicc_components.py:33-34`);
  the run script is `slr-refresh/notebooks/302_run-magicc-scenarios-SSPs.py` (`endyear_run = 2300+5`);
  MAGICC GMST/OHC *history* was already scoped from
  `~/Documents/2026/CodeProjects/FaIRtoFrEDI/magicc_comparison/processed/vv_wide_20260831`
  (`python/scope_magicc_climate_history_gap.py:40`).
- **How:** first inspect the processed file for pre-2000 columns. If present, extend `YEARS_OUT`
  and re-extract (no MAGICC re-run needed — that was exactly the 08-25 lesson at lines 37–46). If
  absent, re-run `302_…` with an earlier start and re-extract. Then a MAGICC line can go on the
  Greenland hindcast panel, re-referenced to **1995–2005** like the others.
- ⚠ The `_with_slr` drawnset is `magicc-ar6-0fd0f62-f023edb-drawnset_with_slr.json` (41 SLR keys),
  outside the repo (`python/scope_magicc_glacier_drawnset.py:52-54`).

### 1c. Build the responsiveness figure (Marcus [9])
- **What:** for each component × model × horizon (2100/2150/2300), the **difference between the
  very-low and high van Vuuren markers** — "how responsive is each component in each model." Marcus
  notes it may inform the pulse analysis.
- **Data is already on disk:** `outputs/vv_model_comparison_L24.csv` — columns include
  `source, module, marker, component, year, med, p05, p95`; markers `vvVL` and `vvH`; sources
  Ladrillo / BRICK 2.0 / MAGICC-SLR (Nauels2025) / FACTS (per-module: larmip, deconto21, bamber19,
  ar5AIS, emuAIS, FittedISMIP, ar5glaciers, emuglaciers, tlm…). No new runs.
- **Design points to decide, not silently resolve** ([[methodological choices are explicit]]):
  (i) FACTS per module or collapsed — the deliverable's "148 / 259" only reproduce as a MEAN across
  four workflows, which `plot_model_comparison_components.py`'s header argues against; show per
  module. (ii) Difference of medians vs median of paired differences — only Ladrillo/BRICK have
  paired draws; use difference of medians for all four for like-for-like and say so.
  (iii) Baseline 1995–2014 (projection), units cm. Stamp provenance
  (`python/provenance.py`).
- **Model:** `plot_model_comparison_components.py` for style/constants; put the in-figure caption
  to description + provenance only (§3.4 below) and the argument in the document text.

### 1d. Get MAGICC's Greenland output from a MAGICC re-run
- **Why:** Marcus [1] second half — *what does the second basin buy relative to MAGICC's
  structure?* Needs MAGICC's Greenland at least as **SMB + SID** separately; the extractor already
  maps `gis = SLR_GIS_SMB + SLR_GIS_SID` (`extract_magicc_components.py:15,54`) but only the SUM
  is written. Emit the two parts separately (and any basin-level variable if the run exposes one).
- ⚠ **The deliverable's MAGICC Greenland sentence has NO REPO RECEIPT.** *"17 parameters
  between the two, of which 9 vary and each of those takes only 4 distinct values"* and the
  SICOPOLIS attribution appear ONLY in the deliverable and in
  `notes/handoff_2026-09-03b_docx_canonical_and_pulse_next.md:97-100` (which says "verified against
  source data" but names no file). The nearest trace is `handoff_2026-08-31g_magicc_climate_arm.md:143-144`
  ("15 discrete tunes (Greenland 4)"). **Verify against the drawnset JSON while you are in there,
  or soften the sentence.** [[confidence words need receipts]].

---

## 2. ⭐⭐ WHAT CHANGED IN THE COMPARISON — three confounds removed, all at SOURCE

Each moved the L24 hindcast numbers. Each is in the .docx already. In order found:

| # | confound | fix | where | what moved |
|---|---|---|---|---|
| 1 | BRICK saved from **1920**, ran from 1850; scorecard scores on the INTERSECTION ⇒ 1900–1919 silently dropped from every RMSE ratio and from "full" | save from 1900 (`FY0`, `posterior_predictive_oldbrick.jl`) | `_slr` ⇒ [[oldbrick_unseeded_lws_jitter]] (the span change is what exposed the next row) | a new 1900–1919 column; "full" only |
| 2 | BRICK's `get_model()` **unseeded** ⇒ ~0.05 cm run-to-run jitter on the total; NOT reproducible | `Random.seed!(2026)` immediately before `get_model`; both arms stamp a `provenance` column; **two runs byte-identical** | [[oldbrick_unseeded_lws_jitter]], [[mimibrick_getmodel_seed]], [[seed_recorded_in_the_artifact]] (now in `~/.claude/CLAUDE.md`) | ~0.03 cm |
| 3 | **LWS convention differed**: Ladrillo's total carried the OBSERVED LWS, BRICK's its OWN, which is **exactly 0 until 2019** by calibration design (Wong stripped LWS from the CW11 target) — measured by `julia/diag_brick_lws_extract.jl` | BRICK's total now takes the observed LWS too (Marcus's ruling; **not double-counting** — BRICK's components were fitted to an LWS-free target) | [[lws_convention_asymmetry]] | **TOTAL row verdict flips** (full 0.459 → 1.12) |
| 4 | **Forcing differed**: BRICK read `fair_mean_{gmst,ohc}.csv` = the **RFF-SP baseline cube**; Ladrillo `ssp245harm`. Re-referenced they agree post-1950 but differ **5.76e22 J at 1900** (~0.65 cm TE) | BRICK reads `…_ssp245harm.csv` (`const FORCING`) | commit `Match the BRICK forcing…` | **TE row flips**: 1.327 → 0.820 full |

⭐ **Shipped Table 2 now (matched forcing + shared LWS + seeded):**
`AIS 0.003/0.005/0.010/0.676/0.019 · Greenland 0.110/0.102/0.054/0.263/0.085 · Glaciers
0.431/0.371/1.061/0.408/0.419 · TE 0.703/0.723/1.107/1.519/0.820 · Total 4.138/1.369/0.519/0.892/1.172`
(windows 1900–19 / 1920–49 / 1950–92 / 1993–2026 / full). Cumulative 1900–04→2020–24: obs +21.00,
Ladrillo +19.84, BRICK +21.34. 2024 level: Ladrillo +0.36, BRICK +0.54.

⭐ **Why Ladrillo wins every component early and loses the total — COMPENSATING ERROR**, measured
(`python/diag_component_error_cancellation.py`): 1900–1919 BRICK's AIS −2.90 cancels its glaciers
+3.28 (92 % of 7.57 cm cancels); Ladrillo's +1.95 of 1.97 survives. The obs budget non-closure is
COMMON to both arms and small (−0.31 / +0.17), so it cannot be the cause. In the document.

⚠ **Two other headline corrections in the same arc**, both in the document:
- the **+0.74 cm** 2024 gap was **52 % ragged-window artefact** (5-yr model mean vs 3-yr obs mean
  on a rising series; `diag_epoch_window_asymmetry.py`); matched windows now, `n` printed;
- the **"axis ≈ 2.46 cm ≈ 3× the gap"** was trend×span and BACKWARDS — on the panel's own
  baseline the recon axis is 0.60× the gap and is a MID-CENTURY structure ⇒
  [[recon_axis_is_midcentury_not_recent]]; and there are **two different "+0.74 cm"** ⇒
  [[two_plus_074_cm_are_different_quantities]].

---

## 3. RULINGS AND CONVENTIONS THIS SESSION (Marcus)

1. **Recalibration (09-09c):** anchor → IGCC altimetry ensemble **at the next target rebuild**
   (recorded as a comment in `prep_recalib_targets_ext.py`, DELIBERATELY UNAPPLIED so script and
   `recalib_targets_ext.csv` stay consistent); `ALT_SIGMA_MM` stays 4.0; **PROVENANCE update, not
   RESULT** — no chain, no shipped number moved ⇒ [[recalib_rulings_20260909c]]. Unchanged today.
2. **Seeds are RECORDED IN THE ARTIFACT** (promoted to `~/.claude/CLAUDE.md`). Provenance stamping
   is scoped to **L24 and forward**: `python/provenance.py` is wired into five python producers and
   both julia postpred arms; ~400 existing L24 outputs are NOT retro-stamped (would re-roll numbers).
3. **The document is L24 vs observations, BRICK and other models — NOT a history of our work.**
   No "previously / earlier version / this version changed" language. A sweep is in every rebuild.
4. **Captions say what the figure DOES**, plus provenance; argument goes in the text. Applied to
   FIG 1 and FIGs 2–8 (`ladrillo_figs.py` shared notes trimmed; per-script notes trimmed; warning
   glyphs stripped from caption STRINGS, kept in `print()` console diagnostics). FIG 9
   (`plot_ladrillo_memo_figures.py`) was **not** touched.
5. **1995–2005 is a BASELINE, not "the calibration window"** — `reref()` only sets zero; the fit
   runs 1900→2023–25 per series. The repo uses the phrase both ways; the deliverable no longer does.
6. **FIG 6 is Ladrillo-only** (`--ladrillo-only` → `figures/vv_gsic_ladrillo_2300.png`); the 4-panel
   WR contrast keeps its original filename.

---

## 4. THE 9/11 COMMENTS — what was applied (10 of 13)
[3] CSIRO/CW11 named as BRICK's target · [4] LWS row simplified (2023 held through 2026; projections
use BRICK's LWS module) · [5] clause deleted · [6] provenance note rewritten — Rignot/Farinotti are
**published values** (the citation is the version); CMIP6/NOAA are **live products** where the download
date is the version, recovered from mtimes (CMIP6 2026-07-21..08-24, NOAA 2026-06-13) · [7] "driven by
the scenario rather than by the historical emissions inventory" (FaIR is emissions-driven) · [8] AIS/TE
lineage added: **Ladrillo and BRICK 2.0 SHARE DAIS and α·OHC** (`LADRILLO.md:45,448`), FACTS independent
on both · [10] glacier inventory: BRICK `glaciers_v0` median **0.417** (5–95 0.32–0.52, from the posterior
CSV) vs Ladrillo **0.290 ± 0.060** remaining-at-2000 on target scope (`calibrate_mcmc_ext.jl:1280`),
full-RGI 0.324 ± 0.084 · [11] FIG 6 Ladrillo-only · [12] FIG 8 caption (**revert when 1a lands**) ·
[2] **Table widths — a real bug**: pandoc's **gfm reader ignores pipe-table dash widths** (every table
came out equal-column); builds now use `markdown+pipe_tables-smart-implicit_figures` (verified zero
text differences, same 9 figures) and widths are **computed at build time** by
`deliverables/balance_table_widths.py` from column text load, because the docx→gfm sync resets
separators to equal dashes on every run. Table 1 = 17/53/30.

---

## 5. ⚠ NON-OBVIOUS STATE / TRAPS
- **The .docx is CANONICAL; Marcus edits it in Word.** ALWAYS `python3 deliverables/sync_filled_from_docx.py --verify`
  before editing `FILLED.md`, then rebuild with the build script's chain (now:
  `sed … | balance_table_widths.py | pandoc --from=markdown+pipe_tables-smart-implicit_figures`).
  Three times this session an edit anchor failed because Marcus had changed the wording meanwhile;
  one script printed "ok" for an edit and then ABORTED before writing — **verify in the rebuilt
  .docx with python-docx, never trust the edit script's own print.**
- **`diag_lws_convention_asymmetry.py` is a REGRESSION TEST, not a measurement** — the corrected
  BRICK arm is the only one on disk, so re-measuring would compare it to itself
  ([[gate_reads_its_own_output]]). The sizes are in the 09-10 commits and memory.
- **Quarantine:** `outputs/quarantine/20260910_oldbrick_span1920/` = the span-1920 unseeded file
  Table 2 was ORIGINALLY computed from, plus the same-span control that proved the jitter; README
  records it is superseded twice over.
- `julia/_frozen_postpred_oldbrick_fy1900.jl` and `_frozen_ctrl_oldbrick_fy1920.jl` are frozen run
  copies (repo convention; `@__DIR__` breaks if frozen outside the repo — learned the hard way).
- **Memory root index** was restructured (18,380 → 13,046 B; `INDEX_conv.md` split out, registered in
  `FaIRtoFrEDI/CLAUDE.md`); still 758 B over the 12,288 soft target. Next cut: the READ-FIRST block
  carries facts against its own "routing only" rule.
- `postpred_L21_*` was re-rendered as a side effect of the epoch-mean fix but has NO provenance column.

## 6. FILES (this arc)
**New:** `python/diag_recon_axis_level_vs_l24_gap.py`, `diag_epoch_window_asymmetry.py`,
`diag_glacier_response_times_L24.py`, `diag_ohc_product_disagreement.py`,
`diag_lws_convention_asymmetry.py`, `diag_component_error_cancellation.py`, `provenance.py`;
`julia/diag_brick_lws_extract.jl`; `deliverables/balance_table_widths.py`; `figures/vv_gsic_ladrillo_2300.png`.
**Changed:** `julia/posterior_predictive_oldbrick.jl` (span, seed, LWS, forcing, provenance),
`posterior_predictive_ladrillo.jl` (provenance), `python/plot_hindcast_components.py`,
`scope_ladrillo_vs_brick20_scorecard.py`, `ladrillo_figs.py`, `plot_model_comparison_components.py`,
`plot_future_components.py`, `plot_vv_gsic_wr_vs_ladrillo.py`, `build_l24_deliverable_doc.sh`,
`deliverables/sync_filled_from_docx.py`, the deliverable .docx/.md, `CHANGELOG.md`.
**Memory (new):** `seed_recorded_in_the_artifact`, `oldbrick_unseeded_lws_jitter`, `mimibrick_getmodel_seed`,
`lws_convention_asymmetry`, `recon_axis_is_midcentury_not_recent`, `two_plus_074_cm_are_different_quantities`,
`recalib_rulings_20260909c`, `INDEX_conv`.
