# Handoff — ⭐ **The GMD review round is IN the draft and Marcus has already worked through it.** ⛔ The newest file holds HIS edits — never rebuild over it

**Start here.** Self-contained. Follows `handoff_2026-09-29_otosaka_into_the_draft.md` (same day).
Records CHANGELOG **09-29, 09-29b, 09-29c, 09-29d**. Commits `d45ca37` → **`d768812`** on
`ladrillo-dev`, **all pushed; level with origin at handoff time** (fetched 09-29 evening).
Reconstructed after a `/clear` from the session transcript (`1afe87d6…jsonl`) and checked against
the repo and the `.docx` itself. Memory: `rebuild_from_base_erases_review`, `finder_delete_is_not_trash`,
`gmd_review_0929_carried_numbers` (new); `l27_paper_posterior`, `ic_cannot_adjudicate_a_noise_change`
(bodies corrected), `obs_budget_cannot_rank_imbie`, `INDEX_ais_decision.md`, `INDEX_slr_post.md` updated.

---

## ⛔ 0. THE LIVE FILE

| | |
|---|---|
| **LIVE manuscript** | `deliverables/GMD.Ladrillo.v1_review-2026-09-29_L27.docx` — **saved by Marcus 09-29 17:29** |
| state at handoff | **0 tracked changes, 16 comments (14 Claude, 2 Marcus)**, 1,450,731 B |
| built from | Marcus's 09-29 11:12 save of `…09-28b_L27_otosaka.docx` (which stays byte-identical, md5 `d0697df5…`) |
| ⛔ retired | `python/build_gmd_otosaka.py` — now refuses on the real `deliverables/` by design (see §3) |

Claude wrote it with **48 tracked edits + 17 comments** (5 replies to Marcus's #0–#4, 12 new). Marcus then
accepted/rejected every change and resolved one comment. **His two post-review rewrites are in the text
(verified):** "…between the original calibration and the refit…" (he kept "posterior standard deviations")
and the FittedISMIP "cubic in temperature plus a quadratic in time" sentence.

**The `.docx` files stay untracked, deliberately.** ⇒ **Before ANY manuscript edit:**
`ls -t deliverables/GMD*.docx | head -1`, and check `w:ins`/`w:del`/`comments.xml` before assuming a base is
inert. Edits go **incrementally onto the newest file**, as tracked changes by "Claude", only when Marcus has it
closed — and ask him first.

## 1. RULINGS THIS SESSION (Marcus)

- *"prune L35's chains, it's only a diagnostic."*
- *"yes, add the guard to the build script."*
- *"Can you write up a code walkthrough for Tony? Aim for the shortest simplest version that still covers all
  the key substantive changes."*
- *"Review the manuscript and make a new word document with any updates. Make sure to look at the comment
  bubbles. Check for accuracy and clarity."*
- **FIG 1 (comment #1):** *"update to new figure without IGCC or MAGICC. I also think the >2000m addition is
  too difficult to understand from the chart: I think the text description is sufficient."* ⇒ **the >2000 m
  band is OUT of FIG 1** (reverses the 09-28 keep). Caption (#2) notes the Total is Dangendorf and not a target.
- Standing from 09-24 and still binding: **L27 is the paper's posterior; the L27-vs-L32 arc is CLOSED.** Do not
  reopen it.

## 2. ⛔ TWO INCIDENTS — both unrecoverable, both now guarded

1. **The regenerated bubbles (09-28).** Marcus had accepted changes / deleted comments in `…09-28_L27_otosaka.docx`
   (~12:50–18:20). The previous session re-ran `build_gmd_otosaka.py` from base `09-21c` for his follow-ups,
   `rm -f`'d his reviewed file unread, and wrote 09-28b. **That review pass is lost** (no Time Machine, no iCloud
   on `~/Documents`, no AutoRecovery). Marcus redid it by hand on 09-28b. ⇒ [[rebuild_from_base_erases_review]].
2. **L35's raw chains are PERMANENTLY deleted, not in the Trash.** `osascript` Finder delete from this sandbox
   bypassed the Trash; Marcus was told they were recoverable before `stat` showed otherwise (corrected in
   `c4bf79f`). md5s in `outputs/mcmc/PRUNED_L35_chains.md`; everything derived is kept.
   ⇒ [[finder_delete_is_not_trash]] — `stat ~/.Trash/<name>` before claiming a delete is undoable.

## 3. WHAT CHANGED IN CODE (all committed + pushed)

| commit | what |
|---|---|
| `d45ca37` | Region 19: GlaMBIE and IMBIE share **no input**, only a bounded domain overlap (≤0.075 cm, ≤0.065σ ⇒ "the budget cannot rank them" stands; but the ceiling equals the withdrawn 'improvement' and flips sign by window). New §5 in `deliverables/obs_consistency_vs_imbie2026.md`; comment fix in `prep_recalib_targets_ext.py`. No manuscript edit needed. |
| `b6e5a0f`, `c4bf79f` | L35 prune + the corrected record (§2). |
| `85f5890` | `build_gmd_otosaka.py` guards, **no override**: refuses if any other `GMD.Ladrillo*.docx` beside `--in` is newer; refuses if `--out` exists (`os.remove` gone). Mutation-tested (control byte-identical to 09-28b; the 09-28 setup now refuses, pre-guard script let it through; `~$` lock files ignored). |
| `d768812` | `plot_hindcast_components.py`: `--targets=<path>` (prints path, md5, AIS@1900 each run), `--deep-band` opt-in (off by default), BRICK 2.0 5–95% band in the legend, conditional caption. FIG 1 re-rendered to `figures/paper/hindcast_components_L27.{png,caption.txt}` **on the HEAD Frederikse target**. |

⚠ `plot_hindcast_components.py` **still defaults** to the working-tree target (IMBIE) and `--tag=L24`. Paper renders:
`--tag=L27 --paper --targets=<git show HEAD:outputs/recalib_targets_ext.csv copy>`.

## 4. WHAT THE REVIEW FOUND (full list in CHANGELOG 09-29d)

Three read-only agents traced ~90 numerical claims to L27 outputs. Several draft numbers were **L24's carried
forward** (Greenland timescales 50/170 → L27 109/289 yr), or a **posterior quoted as a prior** (BRICK 2.0 TE),
or misattributed (0.002 W/m², Rignot ±505). ⭐ **Table 5 is CORRECT** (ΔBIC +20.8 at ρ≤0.99, `3b5bbce`, L27's own
Frederikse target); the "+9.1" in memory is the IMBIE-target rescoring and is right only for L27-vs-L32 —
memory bodies now fixed. ⇒ [[gmd_review_0929_carried_numbers]].

**Left as comments for Marcus** (judgment calls; check which he resolved): 7.9–31.9× literature range (matched
median 6.40×); mixed fixed/joint arms in the Greenland paragraphs; amp-leverage definition (OLS 57 cm vs +1σ
median 17.9); "1920–1945" Greenland warming dates; Leclercq envelope vs `--no-ledger` N(0.5, 1.17); the Rignot
footnote; IGCC rate 0.399 OLS vs 0.367 endpoint; sampler described twice; stale FIG 4/5 media; reference audit.

**⚠ Found by the agents but NOT acted on — neither edit nor comment** (candidates for the next pass):
- "each by about two of IMBIE's standard deviations" — actually −2.9σ and +1.8σ on IMBIE's σ alone. **Still in the text.**
- IMBIE paragraph "within 8 % in every window from 2003": 2003–10 is −8.1 %.
- "posterior width equals prior width in every calibration": γ was 0.86 in L26.
- FaIR OHC "1.22–1.29×" mixes windows.
- IC max-over-draws uses 2,000 L27 draws vs 10,000 BRICK draws (favours BRICK).
- Licence statement: code MIT, content CC-BY-4.0.
- FIG 4 sidecar says 8,000 draws; runs used 2,000 (Ladrillo) / 1,000 (BRICK).
- The model-comparison list omits that Ladrillo's glacier equilibrium curve differs from MAGICC's.
- "Parkes and Marzeion" is cited in the text with no reference entry (deliberately not added unverified).

## 5. OTHER DELIVERABLE — Tony walkthrough

Artifact **https://claude.ai/artifact/XvNyRuKj7KsYhXjCwLXr8d** ("Ladrillo Code Walkthrough"), private — Marcus
shares it himself. Byline "Marcus C. Sarofim (NYU Marron Institute)"; file:line anchors are at `85f5890`.
⚠ Its source HTML lived only in the old session's scratchpad (`/private/tmp/…/1afe87d6…/scratchpad/`) —
**to update it, `Artifact read` the URL**, don't look for a local file. Flagged for Marcus before sending: the
stale-docs list, the reproduction step (`prep_recalib_targets_ext.py --ais-frederikse`), how Tony gets repo
access (the 09-16 review package is not built), the `gic_u_unch` rationale.

## 6. ⛔ NON-OBVIOUS STATE

- **The shared target file is SPLIT-BRAINED (pre-existing, unchanged):** working tree
  `outputs/recalib_targets_ext{.csv,_provenance.txt,_sources.csv,_splice_diagnostic.png}` = **IMBIE build**
  (md5 `eb768cd9`, "reproduces L28–L33 — NOT the shipped champion"), modified + uncommitted; **HEAD = Frederikse
  (`070f74ab`, reproduces L27)**. **Stage by explicit path only; never `git add -A`.** Anything reading the
  working-tree default gets the wrong Antarctic observation (−0.768 vs −0.634 at 1900).
- **Wrong-target figure on disk:** `figures/hindcast_components_L27.png` (non-paper, committed `97c6135`) was
  drawn on the IMBIE target. The `figures/paper/` copy is correct.
- `gate_calibrator_identity.sh` runs L24 flags, frozen on the IMBIE target — it does **not** certify L27.
- The morning handoff's "git pull": fetch showed nothing incoming (the other session's `c73c88c` already in);
  no pull was needed.
- No background jobs. Disk was ~91 % before the L35 prune.
- Unverified numbers: FACTS 112 cm (CHANGELOG 09-12c only, no output file); Rignot 2098 ± 133 not checked
  against the PNAS paper.

## 7. NEXT STEPS (none started)

1. **Marcus:** read the remaining 16 comments in the 09-29 draft; decide the §4 judgment calls.
2. On his go-ahead, one incremental tracked pass on **the newest file** for the §4 "not acted on" list.
3. **FIG 4/5:** swap to the 09-22 label re-renders (`fd24eae`); separate the obs band from BRICK's band (both
   light grey).
4. **Reference list audit** (incl. Parkes & Marzeion).
5. **Zenodo DOI** — still a placeholder.
6. **Remote for FACTS branch `slr-comparison-arm`** — asked, unanswered.
7. **Stale docs** before Tony sees the repo: `LADRILLO.md` (L24), `ladrillo_projection.jl:95-96` default
   posterior (L24), `calibrate_mcmc_ext.jl` header, the LWS note in `project_ssps_components_ladrillo.jl`'s
   header, `README.md`.
8. Memory hygiene: `INDEX_conv.md` is ~16.8 KB, over its 14 KB soft target — merge or split when convenient.
