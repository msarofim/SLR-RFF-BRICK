# Handoff 2026-10-01c: GMD round 10-01c (BRICK naming, MimiBRICK citation)

Follows `handoff_2026-10-01b_gmd_round.md`. CHANGELOG entry 10-01d. Branch `ladrillo-dev`.

## 0. ⛔ The live file

| | |
|---|---|
| **NEWEST** | `deliverables/GMD.Ladrillo.v1_review-2026-10-01e_L27.docx` (md5 `9df3dc41`; 10-01e = land-water clause + Marcus's abstract sentence, T23:30, `r1001e/build.sh`) |
| before that | `deliverables/GMD.Ladrillo.v1_review-2026-10-01d_L27.docx` (md5 `12470007`; round 10-01d = Fig. calls, acronyms, Oxford spelling, 69 edits at T23:00, build `r1001d/build.sh`) |
| previous | `…10-01c_L27.docx` (md5 `e0be5ca7`), untouched |
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

## 1b. 10-01f BUILT (newest)

`deliverables/GMD.Ladrillo.v1_review-2026-10-01f_L27.docx` (md5 `1aa8491a`) = Marcus's 13:05 save of 10-01e (md5
`b93c8039`) + Sect. 3.3's reverted-model result (T23:45). Build: `redline/r1001f/build.sh`. Suite is 12/12
(`outputs/log_suite_20261001c.txt`). ⚠ Future rounds: copy `r1001f/trackedit.py`, which has the fixed `_in_tracked`.

## 2. Open, for Marcus

1. Accept or reject the 10-01, 10-01b and 10-01c rounds.
2. Land water in CALIBRATION: DONE in 10-01e (measured ≤0.014 cm). ⚠ The v1.0 projection code keeps a 1.565 cm
   land-water frame step in 1900; `lws_frame_guard` forces the fix (LWS_OBS_ANCHOR = :zero_at_first_year) at the
   next model update (CHANGELOG 10-01f, suite step 11).
3. Wellcome grant number.
4. From the 09-30 review lists: "presumably" (SLEIP) and "can't" in the abstract (style, not a GMD rule; awaiting
   Marcus). Abstract numbers DONE in 10-01e; FIG, acronyms and spelling DONE in 10-01d.
5. Ladrillo's own Zenodo DOI and repository URL (placeholders), at submission.
