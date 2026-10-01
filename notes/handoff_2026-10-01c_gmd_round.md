# Handoff 2026-10-01c: GMD round 10-01c (BRICK naming, MimiBRICK citation)

Follows `handoff_2026-10-01b_gmd_round.md`. CHANGELOG entry 10-01d. Branch `ladrillo-dev`.

## 0. ⛔ The live file

| | |
|---|---|
| **NEWEST** | `deliverables/GMD.Ladrillo.v1_review-2026-10-01c_L27.docx` (md5 `e0be5ca7`) |
| base | `…10-01b_L27.docx` (md5 `286a6181`), untouched by Marcus when this round was built |
| state | 47 pending 10-01 edits (T00:00) + 10-01b's 68 + FIG 1 (T20:00) + this round's 20 ins / 1 del (T22:00) + 12 comments |
| build | `deliverables/redline/r1001c/build.sh <fresh workdir> <out.docx>`: edits_l, comments_l, validate (PASS) |

⚠ If Marcus edits 10-01c, apply the next round TO HIS FILE. Never rebuild from 10-01b
(`rebuild_from_base_erases_review`). The 10-01c build refuses to run once any newer manuscript exists.

## 1. Done this round (Marcus 10-01)

- **"BRICK" means the family; "BRICK 2.0" means the specific model.** 18 arm uses were switched. The family is
  defined once, at "As a derivative of BRICK". Two claims were verified only on v2.0.0 code (1.196 and
  OHC-proportional TE), so they name BRICK 2.0. The CHANGELOG has the full list.
- **MimiBRICK goes through review as a GitHub citation.** It is pinned to tag v2.0.0, commit 11b2dff, and there is no
  ask to Tony. A reply on Marcus's Zenodo comment records the decision. The fallback is the Software Heritage ID.

## 2. Open, for Marcus

1. Accept or reject the 10-01, 10-01b and 10-01c rounds.
2. Land water in CALIBRATION: there is a comment proposing a clause, and the text does not state it yet.
3. Wellcome grant number.
4. From the 09-30 review lists: "presumably" (SLEIP); "FIG" vs "Fig."; undefined acronyms (BRICK is now cited at
   its definition but not expanded); US/UK spelling; the abstract has no number.
5. Ladrillo's own Zenodo DOI and repository URL (placeholders), at submission.
