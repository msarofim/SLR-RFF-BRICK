# Handoff 2026-10-01b: GMD round 10-01b (Marcus's 10-01 instructions applied)

Follows `handoff_2026-10-01_gmd_prefinal.md`. CHANGELOG entries 10-01b and 10-01c. Everything is on `ladrillo-dev`.

## 0. ⛔ The live file

| | |
|---|---|
| **NEWEST** | `deliverables/GMD.Ladrillo.v1_review-2026-10-01b_L27.docx` |
| base | `…10-01_L27.docx`, md5 `9062e357`, still UNTOUCHED. Word had it open (lock file); no save was seen. |
| state | 47 pending 10-01 edits (`w:date` T00:00) + this round's 68 edits + the FIG 1 swap (T20:00) + 5 replies and 1 note |
| build | `deliverables/redline/r1001b/build.sh <workdir> <out.docx>`. It asserts the base md5, then runs edits_i, edits_j, edits_k and comments_j, then validate `--author Claude` (PASS). |

⚠ **If Marcus saved edits into the 10-01 file after this round**, `build.sh` refuses to run because the base md5
check fails. Rebase then means re-pointing BASE and re-running; the edit scripts anchor on text, so most edits
survive.

## 1. What Marcus asked (10-01) and what was done

- **Möller and 2025.** Done. The 2025 change was **not label-only for thermal expansion**: the diag mixed spans
  (bug, quarantined, fixed). New values: 1.22× / 1.16×, FaIR 1.21–1.27×. Table 4 and Table 5 were re-run and
  their values are identical (see CHANGELOG 10-01c). FIG 1 was re-rendered to 2025.
- **Refit to 0.884?** No. Recommendation and numbers are in CHANGELOG 10-01c (−9 Gt/yr, 0.075 sd). 12.295 is
  Bedmap2's grounded area. Footnote 17 has been rewritten.
- **BRICK naming.** Answered in chat. It was NOT applied: the decision is Marcus's. See §2.
- **Deleted:** "slightly high" and "ties by construction".
- **Profiled noise:** clarified, and the Table 5 caption fixed. **1,600 draws:** expanded. **"couples to":**
  Marcus's wording.
- **Headings:** numbered and sentence case. **Appendix:** the back matter was moved after it (Copernicus order).
- **Leftovers:** fixed.
- **New:** Greenland Eqs. (3)–(11), likelihood (12)–(14), §3.3 Verification, Table A3, a manual pointer.
- **Zenodo for MimiBRICK v2.0.0:** none exists (code). Details are in the reply on Marcus's Zenodo comment.

## 2. Open, for Marcus

1. Accept or reject the 10-01 and 10-01b rounds.
2. **BRICK naming decision.** Recommendation: keep "BRICK 2.0" for the comparison arm, since the 54 existing uses
   and the figure legends already do, and switch the ~13 bare "BRICK" uses that mean the arm. Use plain "BRICK" only
   for the model family, defined once. Not applied yet.
3. **Two equation-transcription findings:**
   - `gis_amp` is prior-only in calibration. This is now stated in the text.
   - In calibration, land water uses the stylised `:central` series, and only via DAIS's sea-level feedback. A
     comment proposes a clause; not stated in the text.
4. **Wellcome grant number.**
5. **MimiBRICK archive:** ask Tony to mint a Zenodo release of v2.0.0. Otherwise cite the Software Heritage ID for
   commit 11b2dff.
6. **Still open from the 09-30 review lists:** "presumably" (SLEIP), "FIG" vs "Fig.", undefined acronyms, US/UK
   spelling, abstract with no number.

## 3. Non-obvious state

- Repo changes this round:
  - `python/diag_te_rate_attribution.py` (fix);
  - window labels in `scope_ladrillo_vs_brick20_scorecard.py` and `ic_ladrillo_vs_brick20.py`;
  - `plot_hindcast_components.py` `X1 = 2025`;
  - new `python/diag_smb_area_reweight.py`;
  - the suite log `outputs/log_suite_20261001.txt` (10/10).
- Side experiment in the FACTS repo (untracked, like its siblings): `facts/experiments/global.shared.vvHL2300.n200.crate0`.
- ⚠ Run IC arms **sequentially**. In parallel, each starts a full worker pool (load average 70).
- ⚠ A `pgrep -f` wait loop self-matched again this session. Wait on literal PIDs.
- No LibreOffice on this machine, so there is no PDF render. pandoc drops tracked insertions inside SourceCode
  paragraphs (a viewer artifact); check the equations in the XML or in Word.
