# Handoff 2026-11-24: AGU26 GC092 poster, Tony Wong's review applied

Predecessor: `handoff_2026-11-22_agu26_gc092_clean_copy.md` (this folder). Poster: "Slow Seas, Fast Gas: Coastal
Damages from CO2 and CH4", AGU26 **GC33I-0525** (session GC092), Wed 9 Dec 2026, 14:15–17:45 PST. Working folder:
`FaIRtoFrEDI/magicc_comparison/poster_agu26/`, branch `heat-ed-morbidity`, **pushed at 7657abf**. Current review copy:
`layout/gc092_layout_44in.pdf` (44 x 44 in, vector), with three red suggestions.

## 1. What was done (11-22 evening to 11-24)

- **Palette comment** (11-22, CHANGELOG (i), (j)): the panel script's "CVD dE 13.0" (dataviz skill validator, Machado
  2009, gates protan/deutan) and SLR-RFF-BRICK `python/validate_palette.py` (Viénot 1999, also gates tritan) measure
  different things. The 11-22 handoff's "tritan 4.9 Ladrillo vs FACTS" was wrong: 4.9 is BRICK 2.0 vs MAGICC.
  Panel E's red/orange (thermal expansion vs Greenland, normal-vision dE 7.1) kept "as is for this print" (Marcus).
- **Coauthor email** reviewed (Marcus sends; prints Thu 3 Dec, a day before CCI's Fri 4 Dec 17:00 PST deadline).
- **Tony Wong's review** (CHANGELOG 2026-11-24 (aw)) and a **second round** (CHANGELOG (ax)), per the rulings below.
- **Ocean heat answer for Tony** (his panel B question): `diag_pulse_ohc_agu26.py` ->
  `answers/tony_2026-11-24/ohc_response_per_gtco2e.{png,pdf,csv}` (+ `_gates.csv`, 359 gates). Built by a subagent,
  re-run at a committed script (values identical). Then drawn as insets in panel B.

## 2. Decisions (Marcus, 11-24) and why

- **Panel C: median-draw lines dropped.** C's band is the range of the six scenario MEANS; the median draws of Ladrillo
  and BRICK 2.0 sat below it in all six scenarios (mean/median at 2300: 1.6–3.1 Ladrillo, 2.8–7.3 BRICK 2.0), which
  Tony read as an error. Cause: the Antarctic mean comes from the few draws whose DAIS threshold crossing the pulse moves
  earlier; median-draw Antarctic response is near zero (memory `pulse_threshold_is_variance_not_bias`). The median draw
  stays in D and F. Check scripts kept in `answers/tony_2026-11-24/c_check*.py`.
- **No versions or stamps in the results panels.** Standalone panels keep their stamps; the layout places stamp-free
  copies from `panels/poster/`. Methods, panel A and the footer carry provenance.
- **Superscript citations**, numbered by first use in reading order; References numbered to match. Render-time only:
  the text file keeps author-year, so [AS-WRITTEN] is untouched.
- **Model names in B and C in their line colours**, darker shades for contrast (his choice over the dataviz skill's
  ink-only rule).
- **Panel A**: Climate row "GMST and ocean heat"; FACTS box "1f AR5, 2f LARMIP"; footnote on the other five workflows
  (3e, 3f, 4: DeConto or Bamber, fixed projections; 1e, 2e: emulandice, noisier than the pulse response at 200 draws;
  verified against `facts/experiments/coupling.ssp585/config.yml`).
- **Methods**: "climate" defined (FaIR "supplies global mean surface temperature and ocean heat content ("climate")
  to"); FACTS sentence shortened to point at panel A. Both approved 11-24.
- **Heat-uptake insets in panel B, plotted as is and labelled**: FaIR = total Earth heat (integrated TOA imbalance),
  MAGICC = ocean only (Marcus declined scaling FaIR by ~0.91 or rerunning MAGICC). For CO2 the FaIR–MAGICC gap
  (MAGICC/FaIR 0.88–0.91) is about the observed ocean share, so mostly definition; for CH4 it is not (0.35 vs 0.63 ZJ
  per GtCO2e at 2100).
- **Side margins**: every panel text at least 0.2 in from the left and right edges (his "check F, G, and H for too
  tight text wrapping"; titles, tick labels and value labels had been at 0.10 in).
- **Ladrillo "submitted to GMD"** (his wording request): red in Next Steps and References, and the Methods citation
  follows so rejecting all red stays consistent.

## 3. Files (all in `FaIRtoFrEDI/`, committed and pushed)

- `magicc_comparison/poster_agu26/make_panels_agu26.py`: C medians removed; `LABEL_TEXT` colours + [LABEL-CONTRAST];
  panel A edits; poster copies + [CROP]; B insets (`b_insets`, `b_inset_clear`) + [B-INSET], [B-INSET-ID];
  `SIDE_MARGIN_IN` in [TITLE-FIT] (covers inset child axes); `TIME_ADJ` left 0.11 / right 0.985; F–I margins; D's
  ratio-axis label centred on its ticks; H's x-label shortened. Mutations: `a_counts a_prov a_pulse a_panels a_fit
  title_long label_contrast crop b_inset`, all trip.
- `make_layout_agu26.py`: reads `panels/poster/`; citation transform + [CITE] (`--mutate cite|uncited`); `CITE_ITEM`
  year tokens include "in review", "in prep.", "submitted"; [CLEAN] counts red edits in every section (it had counted
  only Marcus's paragraphs); `clean` mutation now makes a clean print; edits list includes Claude sections with red;
  `DRAFT_MARKS = True`. All 16 layout mutations trip.
- `text/gc092_poster_text.md`, `layout/*`, `panels/*`, `panels/poster/*`, `panel_numbers_agu26.csv` (1,593 rows: 24 C
  median rows removed, 56 inset rows added, nothing else changed), `panel_manifest_agu26.csv`, `claims_and_layout.md`.
- `diag_pulse_ohc_agu26.py`, `answers/tony_2026-11-24/`. `CHANGELOG.md` 2026-11-22 (i), (j); 2026-11-24 (aw), (ax).
- Memory: `agu26_pulse_poster_rulings` (11-22 panel E, 11-24 both rounds), `palette_check_unreproduced` (Machado
  addendum: a third implementation, still no tie-break).

## 4. Open (Marcus's calls unless noted)

1. **Approve or reject the three red Ladrillo edits.** Then `DRAFT_MARKS = False` for the clean print.
2. **Parametric uncertainty.** Marcus thought C and D show it. No panel shows the draw-to-draw spread: bands and dots =
   scenario spread; D/F/G intervals = bootstrap of the mean; D and F show the median draw. Options offered: (1) one
   Methods sentence (recommended; Methods has 1.9 in free), (2) the same note in each results subtitle, (3) a 5–95 %
   draw range in F (as retired panel J had).
3. **Bullets in "Do CH4 Emissions Lead to Permanent Increases in Sea Level?"** Options offered: A by model (4
   bullets, CO2 stays prose), B by gas and model (3 bullets), C answer-first (his lead line, then mean / median draw /
   MAGICC-SLR / CO2). Needs a hanging-indent rule for "•" in `HANG` (layout). Box has 1.6 in spare.
4. Offered, not asked for: thin D's crowded ratio-axis ticks (0 … 2.5) to 0, 1, 2.
5. Other coauthors' comments (Vivek Srikrishnan, Frank Errickson, Lisa Rennels) not yet received in-session.
6. Marcus's reply to Tony: facts are in this note (panel C) and CHANGELOG (aw) (heat numbers, ZJ per GtCO2e,
   scenario median: FaIR CO2 0.31 / 0.61 at 2100 / 2300, CH4 0.63 / 0.30; MAGICC CO2 0.27 / 0.56, CH4 0.35 / 0.23).
7. From before: QR code once the iPoster URL exists (publish by 2 Dec; `HEADER_SLOTS`, add a decode check); CCI order
   (Marcus); the MAGICC Antarctic note for the Ladrillo paper (`answers/answers_2026-11-19.md` §12.5).

## 5. Non-obvious state

- **Render order**: commit scripts and text; panels with `~/miniforge3/envs/slr-refresh-2025/bin/python
  make_panels_agu26.py` (from the poster folder), commit; layout with `~/climate-env/bin/python
  magicc_comparison/poster_agu26/make_layout_agu26.py` (repo root), commit. Render twice and compare (byte-identical
  every time on 11-24). [PROV] rejects panels from an uncommitted script; the layout footer names the layout script's
  commit, so commit it before the final render. Also run `--reject-red` for fit.
- **Fit** (typeset / box, in): Motivation 13.72 / 15.58; Methods 10.03 / 11.90; results box 12.96 / 14.59; Damage
  Caveats 4.28 / 6.27; Conclusions 14.60 / 15.05; Next Steps 5.20 / 5.52; References 9.19 / 9.51; Acknowledgments
  3.99 / 4.09. Column 4 is now the tight one.
- The panel script prints "gates passed: 0 (pulse_duration_vv)"; already noted in CHANGELOG as known, not new.
- `heat-ed-morbidity` is shared with other sessions (SY047 poster, oil and gas methane). Check
  `git log origin/heat-ed-morbidity..HEAD` before pushing; on 11-24 only this session's commits were ahead.
- `layout/gc092.slr.notes2.docx` and `layout/gc092slowseas.notes.docx` are untracked by design (Marcus's 11-19
  sources, read by the layout, never written).
- Not pushed anywhere else: MAGICC `vv-slr-runs` stays local (11-22 ruling).
