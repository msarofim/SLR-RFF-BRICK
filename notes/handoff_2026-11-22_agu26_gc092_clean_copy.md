# Handoff 2026-11-22: AGU26 GC092 poster, clean copy for coauthor review

Session: "AGU26 GC092 poster" (child of Ladrillo.9.2.26). Predecessor: `handoff_2026-11-17_agu26_pulse_poster_status.md`.
Poster: "Slow Seas, Fast Gas: Coastal Damages from CO2 and CH4", AGU26 **GC33I-0525** (session GC092), Wednesday
9 December 2026, 14:15–17:45 PST, Poster Hall ABC. Working folder:
`FaIRtoFrEDI/magicc_comparison/poster_agu26/` on branch `heat-ed-morbidity`, **pushed at 513d153**.

## 1. Where things stand

The clean copy (`layout/gc092_layout_44in.pdf`, 44 x 44 in, vector, 3.2 MB) is ready for Marcus to send to his
coauthors. No red suggestion or open note is left. The only placeholder is the QR slot in the header.

## 2. Decisions on 11-22 (Marcus) and why

- **MAGICC `vv-slr-runs` stays local** (never pushed to the developers' GitLab).
- **Print:** CCI **Standard, Fri 4 Dec 17:00 PST** ($128; pickup at Moscone). Early Bird (23 Nov) was dropped.
  **Stay RGB.** CCI accepts RGB; we lack CCI's printer profile; the file uses transparency. A round trip through Apple's
  Generic CMYK keeps colour-blind separation above target (worst: SLR models, protan 12.5 -> 9.3, target 8).
- **Edge:** content at least 1 in from the edge (AGU26's own poster page and CCI). `MARGIN = EDGE_CLEAR + STROKE_ALLOW`.
- **Header:** final abstract number from the AGU26 program; "The Saraph Report: thesaraphreport.substack.com"; no
  logos; one square QR slot for the **AGU26 iPoster** (AGU asks for iPosters published by 2 December).
- **Affiliation:** "George Washington University, Milken Institute School of Public Health" after NYU. Now the
  **global rule** in `~/.claude/CLAUDE.md`: two affiliations where allowed, NYU first. Older work is not re-labelled
  (the Ladrillo.jl v1.0.0 tag and Zenodo zip stay NYU only). Whether the GMD manuscript counts as older work was left
  to the gmd-final-review session to ask Marcus.
- **Text:** every red suggestion approved, including six corrections from an independent final check (e.g. 1.3 not
  1.4; MAGICC-SLR's CO2 and CH4 contrasts hold for the MEAN only). His note on the Ladrillo reference deleted.
- **FACTS labels:** wf1f prints as **FACTS-AR5**, wf2f as **FACTS-LARMIP** (named for their Antarctic module, the only
  module in which they differ). Data and provenance keep the wf ids.
- **emulandice tested** (Marcus: "and test emulandice"): causal and deterministic, but at n=200 only emuGrIS resolves
  the pulse; wf1e/wf2e totals z <= 6.6 vs 38-61 for wf1f/wf2f. Methods says the two are "the FACTS workflows whose
  pulse response 200 members resolve". Memory `facts_emulandice_pulse_unresolved`; CHANGELOG 2026-11-22 (g).
- **Share the PDF, not the PNG** (vector; zoomable; the file that goes to CCI). The PNG is a 60 dpi preview.

## 3. Files touched (all committed and pushed in FaIRtoFrEDI unless noted)

- `poster_agu26/make_layout_agu26.py`: edge, header (`HEAD_Y`, `HEADER_H` 5.02, `ABSTRACT_NO`, `SARAPH_URL`, one QR
  slot), markup `{{his=>>approved=>suggested}}`, `--reject-red`, gates [EDGE] and [CLEAN], `DRAFT_MARKS = False`,
  section sizes (Methods 23, Conclusions 27, References 18, Acknowledgments 20).
- `poster_agu26/make_panels_agu26.py`: stamps print the poster letter; panel A Oxford comma and "AR5 and LARMIP" box;
  panel D dots explained; [SEG-LABEL] in panel E; FACTS display names; [TITLE-FIT] now checks drawn tick labels;
  printed F and H left margins widened.
- `poster_agu26/text/gc092_poster_text.md`, `claims_and_layout.md`, `layout/*`, `panels/*`, `panel_numbers_agu26.csv`
  (numbers unchanged from 11-19 apart from the two FACTS display names; checked).
- `magicc_comparison/diag_facts_emulandice_pulse.py`, `processed/facts_emulandice_pulse_test.csv`; comment fix in
  `extract_pulse_vv_facts.py`.
- `FaIRtoFrEDI/CHANGELOG.md` 2026-11-22 (a)-(g).
- **Not committed:** in the `facts` clone, `build_emu_pulse_configs.py`, `build_emu_pulse_scaled.py`,
  `run_emu_pulse_test.sh`, `emu_pulse_test.log`, `experiments/global.emupulse.*` (that repo is not one we commit to).
- Memory: `agu26_pulse_poster_rulings` (11-22 items), `facts_emulandice_pulse_unresolved` (new, indexed in
  `INDEX_cmp_pulse.md`); global `~/.claude/CLAUDE.md` affiliation rule.

## 4. Next steps

1. Marcus sends the PDF to Tony Wong, Vivek Srikrishnan, Frank Errickson and Lisa Rennels; fold in their edits.
   His prose changes go in as `{{his=>>new}}` (black); Claude's suggestions as red with `DRAFT_MARKS = True`.
2. **QR code:** Marcus creates the iPoster in AGU's iPosterSessions editor (publish by 2 Dec) and supplies its URL.
   Then generate a vector QR, place it in the header slot (`HEADER_SLOTS`), and add a check that it decodes to that URL.
3. Marcus places the CCI Standard order by **Fri 4 Dec 17:00 PST** with the final PDF (Claude does not place orders).
4. Optional, unresolved: the panel script's palette comment claims "CVD dE 13.0", but the repo's
   `validate_palette.py` gives a tritan separation of 4.9 for Ladrillo vs FACTS (covered by direct labels). Reconcile
   the two validators or correct the comment.
5. From earlier, still Marcus's call: the short note on MAGICC's Antarctic module in the Ladrillo paper
   (`answers/answers_2026-11-19.md` §12.5).

## 5. Non-obvious state

- **Render order:** commit text and scripts first; panels with `~/miniforge3/envs/slr-refresh-2025/bin/python`
  (matplotlib 3.8.4), commit; then the layout with `~/climate-env/bin/python`, commit. [PROV] rejects panels rendered
  from an uncommitted script. Render twice and `cmp` (byte-identical every time today).
- **Fit is tight in column 1:** Methods 12.49 of 12.51 in, Motivation 14.64 of 14.67. Any text added there needs a
  cut or a size change; run `--reject-red` as well when red suggestions exist.
- **Gates:** 14 layout mutations (`--mutate ...`, incl. `edge`, `clean`) all trip; the `unmark` mutation falls back to
  an approved edit when no red is left. Panel script: [TITLE-FIT] (titles, subtitles, drawn ticks), [SEG-LABEL],
  [A-FIT], `AGU26_MUTATE=...`.
- **Colima is stopped** (the emulandice agent stopped it, as it was off when the agent started).
- MAGICC/slr-refresh branch `vv-slr-runs` (6 commits) is local only, by Marcus's ruling.
