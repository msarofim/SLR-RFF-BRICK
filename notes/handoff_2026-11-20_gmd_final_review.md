# Handoff 2026-11-20: GMD Ladrillo paper, final review after round r1119

Written at the end of a long session (FaIRtoFrEDI launch cwd). A fresh session picks up from here.

## 1. What we were working on

The GMD Ladrillo paper (Sarofim and Wong). Marcus drafts the main text; Claude makes tracked redlines on frozen copies
and never edits the file Marcus is holding. Rules for this work: `INDEX_slr_post.md` (GMD draft basis, audits) and
memory `gmd_1111_decisions.md` (the 11-11 decisions, with the r1119 DONE paragraph appended).

Last request (11-19): "Do a final review of the paper. I scanned all the most recent changes. What additional parts
of it should I check by hand?" The answer is Sect. 4 below. Marcus has not yet replied to it, so nothing in it has
been applied.

## 2. Files

| File | md5 | What it is |
|---|---|---|
| `deliverables/GMD.Ladrillo.v1.2026-11-12b.clean_TW.docx` | 25dd4786… | Tony's 11-19 return (8 tracked marks, all his). Base of r1119. |
| `deliverables/GMD.Ladrillo.v1_review-2026-11-19_L27_r1119.docx` | 96b37ddc… | r1119 redline (authors "Claude" and "Claude (notation)") |
| `deliverables/GMD.Ladrillo.v1.2026-11-19.clean.docx` | 213fc5e9… | r1119 with all changes accepted; the copy the final review read |

Build directory: `deliverables/redline/r1119/` (committed 81d98e8, pushed). Key pieces:
- `build.sh` (md5 guard on BASE), `accept_tony.py` + `accept_lib.py` (string-only accept), `edits_r1119.py` driver,
  `r1119_data.py` (EDITS / INSERTS / TABLE2 / REF / COMMENTS), `notation_r1119.py` (equations to OMML and
  sub/superscripts in the text), `make_eq_omml.py` → `eq_omml.json` (pandoc 3.9.0.2), `clean_r1119.py`.
- `verify_r1119.py` gates G1–G5b read with pandoc (independent reader); `mutation_test_verify.py` (8 mutations, all
  caught). Results in `verify_result.txt`, `mutation_result_verify.txt`; edit log `edit_log_r1119.txt`.
- Word rendering check: copy to `~/Library/Containers/com.microsoft.Word/Data/` and open read-only via AppleScript
  (Word is sandboxed; LibreOffice is not installed). Both r1119 files: 42 pages, equations checked by eye.

Ladrillo code repo (`CodeProjects/Ladrillo`, `main`, pushed through dbe2f69): "sea level" open form in README,
generated sources table, package docstring, `data/comparison/README.md`, CITATION.cff title. Ladrillo CHANGELOG entry
"2026-11-19 — README: "sea level" in the open form".

## 3. Decisions made in r1119 (Marcus 11-19)

- Tony's four edits accepted. Open form "sea level" / "sea level rise" throughout (hyphen stays only in reference
  titles and FACTS's name); reply posted on Tony's comment.
- SLEIP sentence cut. "FACTS (v1.1.4; Kopp et al., 2023)".
- Eqs. (1)–(14) set in the Word equation editor (Copernicus requires equation-editor objects, not images), numbered on
  a right tab; underscore/caret symbols in the text set as real sub/superscripts (tracked under "Claude (notation)").
- MAGICC-SLR notes from the AGU poster analysis went in: Table 2 Antarctic cell "quadratic in GSAT"; a High-scenario
  paragraph insertion; a Very-Low sentence; Edwards et al. (2019) added to the references.

## 4. The final-review list (as given to Marcus; repeat this to him)

### Errors to fix
1. **Conclusions, "−18 to +47 cm":** +47 cm is SSP5-8.5 at 2300 (joint 280.9 vs 233.8 cm; fixed arm +49.4); −18 cm
   is High-to-Low. The body reports only the van Vuuren scenarios (−18.2 vvHL to +31.4 vvH, Sect. 4.2). Either
   "−18 to +31 cm across the van Vuuren scenarios", or give the SSP5-8.5 number in Sect. 4.2. Source:
   `Ladrillo/outputs/projections/joint_cells_<scen>.csv`.
2. **The MAGICC sentence (Claude's r1119 insertion, High scenarios):** gives IMBIE as 0.43 ± 0.07 mm yr⁻¹, a mean
   annual rate over 2002–2023 with an end-point σ. Sect. 3.1 gives 0.52 ± 0.05, an OLS trend over 2002–2021 with AR(1)
   se (SLR CHANGELOG ~line 705). Mean rates for reference: 0.471 (2002–2021), 0.428 (2002–2023). Simplest fix: drop
   the number ("…when IMBIE 2026 shows a net loss"). The sources comment repeats 0.43 and needs the same change.
3. **Sect. 3.2, Claude's r1119 edit:** "(see Code availability)" → "(see Code and data availability)".
4. **Sect. 3.2, "11 remaining (…)":** the list has 10; α (thermal_alpha) is missing.
5. **Two broken section references in Sect. 2.2.1:** "see Sect. 4.3" for RGI 19's response time (Sect. 4.3 never
   discusses response time); "Partial regrowth … (see Sect. 4.2)" (regrowth is discussed only in Sect. 4.3, 5 mentions;
   Sect. 4.2 has none).
6. **Missing reference entries:** Berkeley Earth and GISTEMP (amplification priors), MESSAGE-GLOBIOM SSP2-4.5 (forcing).
7. **"(Smith, 2026)" for the CMIP7 historical emissions:** the only single-author Smith 2026 entry is the fair
   calibration data record. Check whether the emissions file is in that record; if not, it needs its own reference.
   **RESOLVED 11-20 (no change needed):** Zenodo 18828694 lists `historical_emissions_1750-2023_cmip7.csv`
   (98,297 B, md5 ae0fecc9…), byte-identical to `FaIRtoFrEDI/v160_cache/` (the file
   `scripts/build_emissions_v160_ssp245.py` reads). The citation is correct.
   Item 1 re-checked 11-20 from `Ladrillo/outputs/projections/{joint,brick20}_cells_<scen>.csv` (AIS, 2300, joint
   medians, Ladrillo − BRICK 2.0): vvHL −18.2, vvH +31.4, vvM +7.2, others within ±4; ssp245 −6.3, ssp585 +47.1.
8. **Copernicus conventions:** "Sect. 4.1 attributes…" at a sentence start → "Section 4.1"; "(Eqs. 1–2)" →
   "Eqs. (1)–(2)"; "resulting from 5 components" → "five"; author lines lack the middle-initial period
   ("Marcus C Sarofim", "Tony E Wong").

Items 2 and 3 were introduced by Claude in r1119.

### Before submission (GMD requirements)
- **Placeholders:** "DOI [to be assigned at submission]" and "[repository URL]". GMD: code access must be in place when
  the preprint is submitted.
- **Ladrillo on GitHub:** repo is PRIVATE. Remote tags are the OLD names: remote v1.0.0 → a2bb3b0 (= local v0.1.0),
  v1.1.0 → 78b03c6, v1.2.0 → c526331, v1.3.0 → 01462a8 (= local v0.4.0). Local holds both v0.1.0–v0.4.0 and the old
  v1.x tags. The rename push and a new v1.0.0 release tag on current code are Marcus's call; do not push tags,
  publish a release, make the repo public or create a Zenodo record without him.
- **GitHub-only code citations:** MimiBRICK v2.0.0, Mimi.jl and FaIR are cited by GitHub link; GMD wants persistent
  archives. Marcus decided 10-01 to cite MimiBRICK by its GitHub tag through review; an editor may push back here.
- **Ladrillo's MIT licence** is stated only in the Conclusions; the GMD template also puts it in the availability section.
- **Scope and limitations passage:** GMD expects one; none exists. Marcus writes it.
- **Style a copy editor may otherwise query:** ~40 "95%" → "95 %"; Tables 1–2 footnote markers are digits ¹–¹²
  (Copernicus wants letters); 6 em dashes; tables first cited out of order (Table 4 in Sect. 2.2.3 before Table 3 in
  Sect. 3.1; Table A3 before A2); Fig. 1 caption split-bolded; italic "PNAS" in Table 3; MimiBRICK URL has no
  last-access date.

### Check by hand (Marcus's judgement)
- **Numbers only in the abstract or introduction:** abstract "9–14 cm (27–56 %)" (9.2–14.1 cm, 27.0–56.3 %) and
  "47 % larger difference" (glacier High − Very Low range, 14.3 vs 9.7 cm; max−min definition gives +19 %) are
  correct (SLR CHANGELOG 2026-11-05b) but not stated in the body. The introduction's "1.5×", "3×", "1.1×" are also
  not in the body; check against Fig. 6.
- **2,000 vs 10,000 draws:** projections use 2,000 of the 10,000 posterior draws; Sect. 3.2 says "10,000-member
  posterior used for projection".
- **Framing a reviewer could pick at:** IMBIE described both as "dropped to avoid double-weighting" and as
  "out-of-sample"; fast-dynamics parameters "flat in the likelihood" while the same paragraph gives some draws weight
  < 10⁻²⁰; RGI 19 "with no target of its own" yet given a GlaMBIE point constraint, and Sect. 3.2 says "two GlaMBIE
  constraints" (also GlaMBIE 2000–2024 vs 2000–2023).
- **Symbols:** b = glacier sensitivity and block index; Table A3 uses S and w_r where the text uses φ and ΔT_r;
  κ_P (text) vs κ_DAIS (Table A1); u and T̄ each have two meanings; δ used before it is defined; Table A2 loadings on
  ln P₀ while u is sampled; Table A3 calibration values unsourced.
- **Smaller checks:** Table 2 note 7, 42 − 4.0 ≠ 37.4 (flagged 11-05, Marcus's call; SLR CHANGELOG notes 37.8 vs
  37.4); ±6.0 cm glacier uncertainty derivation not stated; T_ref 2015–2024 vs continuation constant 2014–2024;
  Table 4 caption omits the NOAA STAR extension; Table 1 defines n.d. but does not use it; Table 1 FACTS past-2100
  cell omits LARMIP at 2150 (known from the 11-12 audit); Table 3 DAIS row "(below)"; SICOPOLIS "3001" vs the
  reference title's "until the year 3000"; "+8.14 (+0.34)" vs 7.81 differs by 0.33; Wong 2017b AIC/BIC usage.
- **External facts in Tables 1–2:** FRISIA, BRICK 2.0 "yes (1850)", FACTS 31.6 cm.
- **Abstract framing (optional, Claude's 11-19 comment):** Fig. 1 and Sect. 4 run BRICK 2.0 on the same FaIR forcing,
  so the FaIR driver is not one of the changes behind the hindcast improvement.
- **AR6 no-MICI range** (−0.28 to 3.13 m, 17–83 %) in the MAGICC insertion: never checked against AR6 Ch. 9 (web
  agents could not open it, nor the Nauels 2025 SI). Confirm before keeping the Fox-Kemper citation.
- **Figures by eye:** compare captions with figures. All 6 embedded images are byte-identical to
  `figures/paper/*.png`. All references are cited and every citation has a reference (apart from item 6).
- **Open comment threads (13).** No reply yet: Tony 10-06 level/tilt (ℓ, w) sampling (with his own follow-up);
  Tony 10-07 on the IMBIE paragraph placement; Tony 10-15 "can these be tied more directly to interpreting the
  differences…" (on "On glaciers…"); Tony 10-15 "climate" meaning only GMST + OHC (a BRICK GMD reviewer objected to
  this before). Also open: Marcus's availability placeholder note, Claude's 11-12 note, Claude's two 11-19 comments.

## 4b. DONE 11-20 — round r1120 (SLR 4d09682, pushed)

Built on the r1119 clean copy (Marcus: current). Redline `deliverables/GMD.Ladrillo.v1_review-2026-11-20_L27_r1120.docx`
(md5 22556f89…), clean `deliverables/GMD.Ladrillo.v1.2026-11-20.clean.docx` (md5 5d7c2808…). Applied: items 1–5, 8
(plus "seven sea level emulators", "three combinations"), item 6 (5 entries: Rohde & Hausfather 2020, Lenssen et al.
2024, GISTEMP Team 2026, Fricko et al. 2017, Gidden et al. 2019), "%" spacing (40), footnote letters in Tables 1–3
(+ "Table 3, note b" twice). Style marks under author "Claude (style)". Not changed: "(Eqs. 1–2)" (Copernicus rule
silent on parentheses). AR6 no-MICI range VERIFIED (built-in browser): AR6 Ch. 9 Table 9.11, SSP5-8.5,
Antarctica at 2300, "Assessed Ice-sheet Contribution" column, −0.28 to +3.13 m, 17–83 %, rel. 1995–2014 (MICI is a
separate column, 6.87–13.54 m). Text correct as written. **r1120b (Marcus: add Table 9.11, resolve the comment)
SUPERSEDES r1120:** `deliverables/GMD.Ladrillo.v1_review-2026-11-20_L27_r1120b.docx` + `GMD.Ladrillo.v1.2026-11-20b.clean.docx`
(md5 d295cecf…); build `redline/r1120b/`. Still open: every "Before submission" and "Check by hand" item above. The next
round starts from Marcus's review of r1120b. The next round starts from Marcus's review of r1120.

## 4c. DONE 11-20 — round r1120c (SLR 48c092a) SUPERSEDES r1120b

Base: Marcus's 10:02 save of the 11-20b clean copy (md5 a93fb35c; comments deleted; 3 tracked marks of his own, kept).
Redline `deliverables/GMD.Ladrillo.v1_review-2026-11-20_L27_r1120c.docx` (md5 8551ee10…), clean
`deliverables/GMD.Ladrillo.v1.2026-11-20c.clean.docx` (md5 0d367cfd…). Applied: his 11-20 list (draw count, block index
g, Table A1/A3 symbols, Table 2 BRICK 2.0 inventory 35.7 s0-inclusive, Table 4 caption, Table 1 n.d., SICOPOLIS 3000,
RGI 19 "constrained only by a weak GlaMBIE rate"). Kept by his ruling: "+0.34", IMBIE framing, ±6.0, LARMIP. Open:
Word render of r1120c (stalled on a likely macOS prompt), the fast-dynamics sentence (explained to him; wording his),
external facts in Tables 1–2, figure captions by eye, Tony's open threads (Marcus deleted all comments in his copy),
and the "Before submission" items. CHANGELOG 2026-11-20c has the detail.

## 5. Next step (as of the r1119 handoff; superseded by 4b, 4c)

Wait for Marcus's reply to the list. Offered: a tracked round **r1120** with errors 2–5, item 8, the % spacing and the
table-footnote letters (mechanical only; the rest is wording or his judgement). Before building:
1. Ask which file is his current one. If he has edited the r1119 clean copy, r1120's BASE is his file (new md5 guard),
   never the file he holds; copy it frozen into the build dir.
2. Copy the r1119 tooling to `redline/r1120/`, new AUTHOR date, new EDITS. Carry the gates (G1 authors, G2 reject
   view == base, G3 accepted == base + planned edits) and re-run the mutation test.
3. Render in Word via AppleScript before delivering. Commit the build dir; add an SLR CHANGELOG entry.

## 6. Non-obvious state

- Tracked equations: pandoc's math reader ignores w:ins inside oMath, so G2 reads the reject view from a copy with
  oMath stripped. Any r1120 gate must do the same.
- The r1119 clean copy has Claude's two comments and the reply to Tony still attached.
- Side sessions linked to the OLD session (not this one): `agu26-pulse-poster` and `agu26-fredi-damages`, both idle
  at handoff. The FrEDI session's final GC092 numbers were pending (28 CH4 MAGICC-climate runs, then downstream).
  Those are poster work, separate from the paper.
- Never `git add -A` in FaIRtoFrEDI (many untracked files); stage by name. Use `git -C <abspath>`.
