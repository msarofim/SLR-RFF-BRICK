# Handoff — ⭐⭐ **The L27-vs-L32 arc is CLOSED by ruling; the Otosaka/IMBIE-2026 material is IN the live draft.** ⛔ Two of my builds went onto the WRONG BASE — read §2 before touching any manuscript file

**Start here.** Self-contained. Follows `handoff_2026-09-24d_step2_heldout_and_L35.md`. Records
CHANGELOG **09-24f/g/h, 09-26, 09-27, 09-28, 09-28b**. Commits `b1eeec1` → **`97c6135`** on
`ladrillo-dev`, **all pushed, 0 unpushed.**
Memory: `l27_ships_imbie_is_out_of_sample`, `l27_draft_carried_l24_methods`,
`gis_imbie2026_early_bias`, `obs_budget_cannot_rank_imbie`, `ais_heldout_pre1979_fails_ambiguously`
(new); `ais_noise_floor_is_target_dependent`, `mutation_test_gates` (extended);
`INDEX_ais_decision.md` (NEW SPLIT), `INDEX_ais_imbie.md`, `INDEX_ais.md`, `MEMORY.md` updated.
⚠ **Another session is also committing to this branch** (`c73c88c`, the RFF-SP pin) — `git pull` first.

---

## ⛔ 0. THE LIVE FILE, AND THE TWO DEAD ONES

| | |
|---|---|
| **LIVE manuscript** | `deliverables/GMD.Ladrillo.v1_review-2026-09-28b_L27_otosaka.docx` |
| built by | `python/build_gmd_otosaka.py` from `…v1_review-2026-09-21c_L27.docx` |
| ⛔ **DEAD — do not build on** | `GMD.Ladrillo.v1.docx` (the original, ~3,900 words behind) |
| ⛔ **DELETED** | `GMD.Ladrillo.v2_L27.docx` + `python/build_gmd_v2_L27.py` (Marcus) |

**The review line is the manuscript.** All the `.docx` files are **untracked**, deliberately — Marcus
edits them directly, and a tracked copy invites the rebuild that destroys his prose. **The edit list
is the artifact.**

## ⛔⛔ 1. RULING — the L27-vs-L32 arc is CLOSED

**Marcus, 09-24: *"let's stick with L27 as the model for the paper."*** `champions.json` never
changed and needs no change. **Do NOT re-open it** with a new arm, ruler or test. Three tests ran and
all three *relocated* the question rather than settling it ⇒ [[l27_ships_imbie_is_out_of_sample]].

**Scoping, also his:** the paper carries IMBIE-2026 as an **out-of-sample check** plus the **`sd_ais`
noise-floor finding**, and **deliberately OMITS** the L27-vs-L32 trade, the σ-sensitivity and the
held-out tests. Available in `INDEX_ais_decision.md` if a reviewer asks; **not volunteered**.

Step 2's result, for the record: **L31 FAIL (1.39 σ), L35 PARTIAL (1.18 σ)**, both **AMBIGUOUS by
pre-registration**, and an additive guess from the neighbouring cells would have called L35 a **PASS**
— crossing a band boundary ⇒ [[ais_heldout_pre1979_fails_ambiguously]].

## ⛔⛔ 2. THE MISTAKE TO NOT REPEAT: I BUILT TWICE ON A STALE BASE

I built `v2` from `GMD.Ladrillo.v1.docx`. **It is not the live draft.** The review line was ~3,900
words longer, carried Marcus's comments and live tracked changes, and **already contained every L27
correction v2 applied** (50 parameters, 42 of 50 converged, `ais_precip_u`, 314 cm). Its
`antarctic_lambda` sentence was **better written than mine**.

⚠⚠ **Worse: the figures were already being fixed there AS TRACKED CHANGES** — the L24 renders sit
inside `<w:del>`, replacements in place. **v2's script rewrites the media wholesale and would have
destroyed a review Marcus was in the middle of.**

⇒ **BEFORE EDITING ANY MANUSCRIPT FILE: `ls -t deliverables/GMD*.docx | head -1`, and check
`w:ins`/`w:del`/`comments.xml` before assuming a base is inert.** `build_gmd_otosaka.py` now gates on
all of it and **refuses to run on its own output.**

## 3. WHAT IS IN THE DRAFT NOW

**Two tracked-inserted paragraphs** after *"Deliberately removed: IMBIE, and the total."* (halved from
four at Marcus's request, ~470 → ~280 words) + the **Otosaka et al. (2026)** reference, alphabetical.
All attributed to **"Claude"**, validated with `--author` so no untracked edit slipped in.

**Table 3**: 11 of 12 Consolas runs → body font, **untracked** as asked. ⭐ The paper decided this
itself — its **36 reference entries set DOIs as plain text** and Table 3 was the only exception;
~30 other `N(μ, σ)` are plain text too. ⛔ **The `.nc` filename KEEPS monospace**, as do Table 6's
**50 parameter names** — a literal a reader must type exactly is the one job monospace is for.

**FIG 1** (`figures/hindcast_components_L27.png`): **MAGICC-SLR and the IGCC GMSL line removed**
(opt-ins `--magicc` / `--igcc-gmsl`, not deletions); title and caption now **derive** from the toggle.
⭐ **The >2000 m hatched band STAYS** — it is the visual evidence for the thermal-expansion-overshoot
paragraph, and removing it orphans a standing argument. **IMBIE is OFF** on this figure (`--imbie`):
on those axes the record covers ~35–40 % of the x-axis and the discrepancy is 5–9 % of panel height.

## ⭐⭐ 4. THE SUBSTANTIVE FINDINGS (all receipted)

- **Greenland is the CLEANER out-of-sample test** — no GIS target vintage ever contained IMBIE, while
  the Antarctic comparison is out-of-sample only because L27 predates the IMBIE target build. Modern
  rates within **8 %**; **1972–91 loses 0.50 cm against the record's 0.13 (+3.67 σ)** = 83 % of the
  full-period gap, ~¾ of it the model missing **its own target** ⇒ [[gis_imbie2026_early_bias]].
- ⛔ **The two ice sheets CANCEL**: Greenland **+0.441**, Antarctica **−0.376**, net **+0.065 cm**.
  **A total-sea-level check sees neither.**
- ⛔ **The observational budget CANNOT rank Frederikse vs IMBIE** — residuals 0.1–0.5 σ and the
  "improvement" **flips sign by window** at 1/10 of its own bar ⇒ [[obs_budget_cannot_rank_imbie]].
  ⚠ I first reported it as favouring IMBIE from **one window with no error bar**. Withdrawn.
- ⭐ **`antarctic_lambda` is receipted on L27**: ssp585@2300 **R² 0.708, contrast 0.897**. ⚠⚠ **I
  nearly had Marcus delete that sentence** — I read `--cut-fastdyn` and concluded the channel was
  gone. It is not: lambda is **PROPAGATED at projection time**. **Absent from the posterior ≠ absent
  from the model** ⇒ [[l27_draft_carried_l24_methods]].

## 5. ⚠ NON-OBVIOUS STATE

- ⛔ **The shared target file is SPLIT-BRAINED and that is the pre-existing state**: working tree =
  **IMBIE** build (`eb768cd9`), committed = **Frederikse** (`070f74ab`). **Never `git add -A`** —
  it swept this in once, and Marcus's untracked drafts another time. **Stage by explicit path.**
- **L35's chains are 7.5 GB** in `outputs/mcmc/`. Keep or prune deliberately; L35 is a diagnostic,
  not a candidate.
- `plot_hindcast_components.py` has **three opt-in flags** now: `--imbie`, `--magicc`, `--igcc-gmsl`.
  All default OFF. The legend is conditional on each, after I twice shipped a drawn-but-unlabelled
  series (IMBIE, then **BRICK 2.0** — the second by hanging `if SHOW_MAGICC` on the whole else-branch).
- **Table A1 is rebuilt at L27** (`build_tableA1_docx.sh`, 50 rows). The L24 `.docx` is kept as
  provenance. ⚠ It is a **separate appendix file**, not embedded in the draft.
- `diag_ais_block_propagation.jl` now derives its parameter set from the chain **and** from the
  post-propagation draws — two sets that must not be conflated, or the dominant parameter is omitted
  and its absence read as a zero effect.

## 6. NEXT — nothing is blocking, and the arc is closed

1. **Marcus reviews the 09-28b draft.** The additions are markup; accept/reject in Word.
2. ⚠ **Owed from the draft's own comments, not from me:** the **Zenodo DOI** is a placeholder pending
   the frozen version, and the **FACTS comparison arm (`slr-comparison-arm`) still has no remote** —
   the 54 experiment outputs behind FIGs 2–6 need a home before that section can be completed.
3. **Open, untested** (flagged in `obs_consistency_vs_imbie2026.md`): whether **GlaMBIE** and IMBIE
   share input through Antarctic-periphery **region 19**, which the glacier target deliberately keeps.
   If they do, the components are less independent than the budget assumes — weakening that test
   further, never rescuing it.
