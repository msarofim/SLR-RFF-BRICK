# Handoff — the four 09-11 tasks are DONE; one two-part decision is Marcus's (benchmark re-freeze)

**Start here.** Continues `handoff_2026-09-11_l24_comments_applied.md` (its §1 listed four tasks
from Marcus's 9/11 comments; all four closed this session). Rulings in §3 of that note are
unchanged. Read `INDEX_cmp.md` (three new lines, 09-11) before touching FACTS, MAGICC or the
responsiveness figure.

**STATUS:** `SLR-RFF-BRICK` `ladrillo-dev` clean, **NOT PUSHED**; `facts` `slr-comparison-arm`
clean at 2f007423 (config.yml for the 3 new experiments committed; .nc outputs gitignored as
always). Run `git -C ~/Documents/2026/CodeProjects/SLR-RFF-BRICK rev-list --count
origin/ladrillo-dev..HEAD` for the count; check authorship before pushing (SLEIP session shares
the branch). **TORCH VERDICT:** every job today was seconds-to-a-minute, local.

---

## 1. What was done (commits df4fd6c, 977c609, 604fad4 here; 2f007423 in facts)

**1a. FACTS SSP controls to 2300 → FIG 8 has FACTS bars.** Three twin keys
`ssp1262300/ssp2452300/ssp5852300`, same recipe as the vv twins; no emulandice on twins. NEW
**[EXTEND] gate** in `extract_facts_shared_components.py`: a twin must equal its base run
bit-for-bit on the overlap (13 files, bound 0.0 identity; PASS 10/10; mutation-tested with a
1 mm perturbation) and only then are its years > 2150 merged under the base name — **the merge
used to be done by hand on the CSV** (a1341eb), so the CSV was not reproducible from its own
producer. 9,600 pre-existing rows byte-identical, 5,352 added. FIG 8 caption: "stop at 2150"
sentence gone; notes the ar5glaciers 31.57 cm ceiling. ⚠ FACTS at 2300 is far less
scenario-sensitive than the other three (ssp126 total 132–208 vs ssp585 228–896).

**1b + 1d. MAGICC history.** No re-run needed (source spans 1750–2305). ⭐ **MAGICC's Greenland
module starts 1990 (AIS 2002): identically zero before**, so a pre-1991 Greenland hindcast is
IMPOSSIBLE, not absent. From 1991 it runs low: 1993–2026 bias −0.26 cm / RMSE 0.35 vs BRICK
−0.13 / 0.17 and Ladrillo +0.00 / 0.05 (in-sample). FIG 1 now carries MAGICC on the Greenland
panel from 1991 with a start-year note; caption updated. **The deliverable's "17 parameters, 9
vary, 4 distinct values" sentence is VERIFIED** against the `_with_slr` drawnset
(`diag_magicc_gis_structure.py`; SMB and SID tunes independent → 16 combos; label GREVE =
SICOPOLIS). Structure for Marcus to draft from: SID is a prescribed rate (non-monotone in warming
at 2300: 21.0/20.1/17.8 cm for ssp126/245/585), SMB is NEGATIVE to 2050 in every SSP (below-
threshold branch, 2.5–2.9 K) and carries all the spread, capped at 7260 mm. New products:
`data/comparison/magicc_nauels_components_hist.csv` (1900–2026, rel 1995–2005, NaN before
start) and `magicc_nauels_gis_split.csv`; **the frozen projection file is byte-identical.**

**1c. Responsiveness figure** `figures/vv_responsiveness_L24.png` (+ stamped CSV): med(vvH) −
med(vvVL), FACTS per module, cm rel 1995–2014; MAGICC's own GMST gap (2.03/3.61/5.86 K) vs the
FaIR driver's (1.68/3.12/5.46 K) on the caption, cm/K in the console. **Not placed in the
deliverable — Marcus's call.** Headline: Ladrillo's Greenland ≈ MAGICC's ≈ 3× BRICK's; ar5AIS
responds NEGATIVELY; at 2300 the DAIS pair and MAGICC are 2–5× any FACTS workflow, all Antarctica.

**Also fixed:** the canonical .docx was STILL embedding the 4-panel Wigley-Raper figure as FIG 6
(the 9/11 "[11] applied" changed caption and script, not the image path or the sync script's
FIGS list; found by matching embedded media size 365,566 B). Build script now runs
`--ladrillo-only`; panel (a) labelled. CHANGELOG gained the missing 09-10 arc entry (from the
previous handoff) plus 09-11b/c/d.

## 2. ⚠ THE DECISION FOR MARCUS — benchmark re-freeze, two parts
`ladrillo_model_comparison_L24.csv` has +39 FACTS rows at 2300 (nothing else moved), so the plot's
[LIT] gate stamps **"LITERATURE ARM MOVED: 39 of 189 … the comparators drawn here are the LIVE
ones"** on FIGs 7 and 8 (it is in the shipped PNGs now) and `bench_ladrillo.py` scores on the
frozen copy. A `bench_ladrillo.py --tag=L24 --freeze-fixed` would:
  (a) add the 39 rows — additive, but 2300 cells go from ONE comparator to FIVE, so 2300 verdicts
      can change; and
  (b) **also re-freeze the BRICK 2.0 hindcast arm** (`postpred_oldbrick_components_timeseries.csv`,
      236 lines differ) — the 09-10 span/seed/LWS/forcing changes were made at source and the
      benchmark never caught up, so hindcast verdicts move too.
Measured by a trial re-freeze, then `git checkout -- benchmark/reference/_fixed` (it is tracked).
Options: literature-only additive re-freeze (needs a `--freeze-literature` flag, ~10 lines);
full re-freeze (benchmark catches up with Table 2 — then re-run bench and record which cells
flip); or leave frozen and accept the stamp. Nothing was resolved silently.

## 3. Non-obvious state / traps
- `.docx` canonical; `sync_filled_from_docx.py --verify` before any edit; verified round-trip
  126/126 paragraphs after the last rebuild. FIGS list there now says `vv_gsic_ladrillo_2300.png`.
- `build_l24_deliverable_doc.sh` regenerates the SSP-set comparison figures + memo figures, NOT
  FIG 1 (`plot_hindcast_components.py --tag=L24`) and NOT the vv-set figures; run those by hand.
- `outputs/bench_ladrillo_L24.md` differs from HEAD~4 only by its date/commit stamp.
- `diag_magicc_gis_structure.py` writes COUNTS/SHAPE only; drawnset values never go to a tracked
  file (members-only).
- Memory: `INDEX_cmp.md` is at 18,107 B of its 18,432 B hard ceiling — the next addition needs a
  split (candidate: move the MAGICC-module lines to a `INDEX_cmp_magicc.md`). Root `MEMORY.md`
  `wc -c` reads 19,925 B (the rules header is excluded from the budget; re-measure before acting).

## 4. Files
**facts:** `build_shared_climate_nc.py`, `build_shared_configs.py`, `extract_facts_shared_components.py`,
`run_ssp_facts_2300.sh`, 3 `config.yml`. **Here (new):** `python/diag_magicc_gis_structure.py`,
`diag_magicc_gis_hindcast.py`, `plot_vv_responsiveness.py`; `data/comparison/magicc_nauels_components_hist.csv`,
`magicc_nauels_gis_split.csv`; `outputs/{diag_magicc_gis_hindcast_L24,vv_responsiveness_L24}.csv`,
`log_diag_magicc_gis_structure.txt`; `figures/vv_responsiveness_L24.png`. **Changed:**
`extract_magicc_components.py`, `plot_hindcast_components.py`, `plot_vv_gsic_wr_vs_ladrillo.py`,
`build_l24_deliverable_doc.sh`, `deliverables/sync_filled_from_docx.py`, the deliverable .md/.docx,
`figures/{hindcast_components,model_comparison_components_{2100,2150,2300},vv_gsic_ladrillo_2300}_L24.png`,
`outputs/{facts_components_shared_n200,ladrillo_model_comparison_L24}.csv`, `CHANGELOG.md`.
**Memory (new):** `magicc_gis_starts_1991`, `facts_twin_extend_gate`, `vv_responsiveness_high_minus_verylow`.
