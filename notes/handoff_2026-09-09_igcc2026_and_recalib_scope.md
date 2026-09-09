# Handoff — IGCC 2026 adopted; the recalibration is SCOPED but NOT STARTED

**Start here.** Work done 2026-09-09. Written at Marcus's instruction **before** any
recalibration work begins, so the next session starts from a clean statement of what is decided
and what is not.

**STATUS: `SLR-RFF-BRICK` `ladrillo-dev`, clean, NOT PUSHED.** Two commits this session:
`ddfc565` (adopt IGCC 2025-indicators GMSL) and `048ce4e` (regenerate the L24 hindcast figure).
⚠ `b2b73bb` on top of them is **NOT mine** — a SLEIP note from a concurrent session.
`FaIRtoFrEDI` is on `heat-ed-morbidity`; only `CLAUDE.md` changed there this session.

> ⚠ **Do not type a commit count into this line.** A handoff's own commit changes it and four
> corrections in two notes proved the point ([[status_field_carries_the_query]]). Run
> `git -C ~/Documents/2026/CodeProjects/SLR-RFF-BRICK rev-list --count origin/ladrillo-dev..HEAD`.

---

## 1. WHAT WAS ASKED

Marcus attached Forster et al. 2026 (IGCC, 2025 indicators; ESSD 18, 3889–3933) and asked which
SLR indicators could join the Ladrillo historical-observation comparisons. He then ruled:

1. **update to the latest for all values used in the documentation comparisons**;
2. **add Wang 2024 and Mu 2025 to the reconstruction panel, and check whether they have
   components**;
3. and raised — **leaning yes** — whether to recalibrate a Ladrillo version on all the updated
   data, on the grounds that we are a month or more from submission and it should be as
   up-to-date as possible "with all the right uncertainty bands".

Items 1 and 2's *investigation* are done. Item 2's *data acquisition* is blocked (§4). Item 3 is
scoped here and **deliberately not started**.

---

## 2. ✅ THE IGCC UPDATE IS DONE — and it is not the update it looks like

`python/ingest_igcc2026_gmsl.py`, **11/11 gates**, `ddfc565`. Raw drop at
`data/observations/raw/igcc2026/` (GitHub tag **`v2026.06.02`**; ⚠ Zenodo `20499280` was
returning 504/000 all session — **GitHub serves the same release**). Ingested to
`data/observations/igcc2026_gmsl_annual.csv` + `igcc2026_gmsl_benchmarks.csv`.

⭐ **It re-derives the ENTIRE altimetry era from 1993**, not just appends 2025: three products
re-downloaded Feb–Mar 2026 (AVISO, NASA, **U. Colorado**), so one set of corrections spans the
record. ⚠ **NOAA was dropped for AVAILABILITY** — the other three "had been updated at the time
of writing" — **not on a quality judgement**, and the same paper is explicit about US
data-centre funding cuts. Do not write it up as a verdict on NOAA STAR.

| | change vs the 2024-indicators drop |
|---|---|
| pre-1993 | a **UNIFORM +0.70 mm** offset (residual 5e-08) — the tide-gauge record is untouched |
| 1993– | re-derived; max 4.94 mm at 2001 |
| **re-referenced** (what every figure plots) | **max 0.265 cm** |
| **1993– interval** | **±9.1 → ±4.4 mm** ⇐ the actual gain |
| 1901– interval | ±51.6 → ±51.0 mm — unchanged; TG structural spread dominates |

⇒ **the picture barely moves; the uncertainty does.** On the L24 total panel at 2024 IGCC reads
**8.33 cm** against Ladrillo **8.55** and the Dangendorf-built target **7.81** — so Ladrillo is
**+0.22 cm** against IGCC where it is +0.74 against the fitted target. Both consumers repointed
(`plot_hindcast_components.py`, the substack GMST/GMSL figure).

### ⛔⛔ The band we had been drawing for four months was wrong

The published σ is near-constant (38.4–49.4 mm), **not zero at 1901**, and non-monotone ⇒ it is a
**LEVEL** uncertainty dominated by a common-mode term, which **cancels** when a consumer
re-references the series (the hindcast figure re-bases to 1995–2005). The source settles it
against itself: propagating ±1.645σ across two years gives **±99 mm** on a difference against the
paper's own tightest published Δ interval of **±4.4 mm** — a factor of **23**.
⇒ column renamed **`sigma_level_mm`** so a plot cannot mistake it, legend now states what the
shading is, and the **Table 11 period differences ship beside it as the real gate**.
⚠ **IGCC publishes no ensemble members**, so the correct `sd(x_t − mean(window))` band **CANNOT**
be computed from this release. Full rule ⇒ [[published_sigma_may_be_level_not_anomaly]].

### Gate notes
- ⭐ `[TABLE-11]` is the **provenance** gate — it is also what proved our OLD file was exactly
  the Forster-et-al.-2025 column, which is how the two vintages were told apart.
- ⚠⚠ **The rate column is REPORTED, not gated.** Table 11 defines rate = Δ/n, so it is Δ/n on
  both sides and tests nothing the Δ gate has not. Gating it exposed only the paper's rendering:
  **2006–2025 prints 3.66 where its own Δ/n = 3.6684, which ROUNDS to 3.67** — the other three
  rows round, that one is truncated. A 0.005 bound FAILED on it.
- Mutations: `shiftlevel` fails `[TABLE-11]`, `dropyear` fails `[COVERAGE]`.

### ⚠ Two provenance regressions IN THE RELEASE
1. **No `metadata.yml` for sea level** (the 2025 drop shipped six; the new one ships none
   repo-wide) ⇒ the old drop is KEPT as the only machine-readable provenance. **Do not delete it.**
2. **`altimetry_indiv_estimates.csv` still heads its third column `NOAA`** while the paper says
   U. Colorado; that column moves **+7.1 mm at 2024** against AVISO's +0.7 and NASA's −1.3 — a
   product swap under an unchanged header, not a reprocessing. ⚠ **NOT PROVEN** (same class as
   [[dangendorf_mislabel]]). **Do not use that column until it is settled**; worth reporting
   upstream.

---

## 3. ✅ WANG AND MU — the components answer is NO, for both

| | Wang et al. 2024 | Mu et al. 2025 |
|---|---|---|
| cite | J. Climate 37, 6453–6474, `10.1175/JCLI-D-23-0410.1` | ESSD 17, 5507–5528, `10.5194/essd-17-5507-2025` |
| span | 1900–2019 | 1900–2022 |
| **components** | **NO** — it CONSUMES a budget, comparing its GMSL to "the sum of observation-based contributions" | **NO** — its own variable list is GMSL + per-gauge only |

⇒ **component targets are unchanged**: Frederikse 2020, GlaMBIE, GRACE, Mouginot. What these two
add is a **SPREAD ON THE TOTAL** — which is exactly the term the deficits arc turns on.

⭐⭐ ~~**WANG INDEPENDENTLY REPORTS OUR NON-CLOSURE.**~~ ⛔ **CORRECTED 2026-09-09b — this
heading INVERTED the abstract by quoting it from its second clause on.** The abstract opens the
sentence with **"Despite GMSL budget closure in terms of long-term trend since 1900,"** and only
then reports "discrepancies between the trends from available GMSL reconstructions and the sum of
independent observation-based contributions over different periods in the 20th century, e.g., the
discrepancy at the beginning of the 20th century, which could be related to possible bias in the
land ice component estimate."

⇒ Wang makes **two** claims, and only one of them is ours:
1. **CLOSURE** on the long-term 1900–2019 trend (1.6 ± 0.2 vs contributions 1.5 ± 0.2).
   **Wang is NOT an external witness to a whole-record deficit.**
2. **SUB-PERIOD non-closure**, worst at the century's start, suspect = **land ice** — *this* is
   what maps onto [[curvature_budget_no_closure]] / [[deficits_are_unresolved]], which are
   curvature/period-structure claims anyway. **Cite it for (2); never for (1).**
The **1.3–2.0 mm yr⁻¹ spread is across PRE-EXISTING reconstructions over 1900–2008** — a third
statement, on a different window again, and not about closure at all.
⚠ This bears on §4 Reason 2: the spread argument survives intact; the "outside witness to
non-closure" argument narrows to the early century.

⚠⚠ **THE THREE TRENDS ARE NOT A CLEAN SPREAD AND MUST NOT BE QUOTED AS ONE** — IGCC **1.85** is
1901–2025, Wang **1.6** is 1900–2019, Dangendorf **~1.5** is 1900–2021, and the later windows
carry more acceleration. **Match the windows first** ([[like_for_like_forcing]]).

### ⛔ BLOCKED — neither dataset is on disk
Neither is in the IGCC release (it ships only the AR6-era `CW2011/HA2015/DA2017/DA2019/FR2020`).
- **Mu**: Zenodo `10.5281/zenodo.15385035`, file `SLRv2.nc`. **Zenodo still DOWN on 09-09b** —
  `504 Gateway Time-out` in ~30 s on `/api/records`, `/records` and via `doi.org`, while DNS
  resolved, TCP 443 connected and GitHub + doi.org answered normally. **Their gateway, not our
  network**, two days running. Pure retry; still the easy one.
- **Wang**: ⚠ **data location STILL UNRESOLVED after a second pass (09-09b).**
  ⛔⛔ **A DECOY EXISTS AND SEARCH OFFERS IT CONFIDENTLY: `10.5281/zenodo.15288816` IS NOT WANG
  2024.** It is **Shengdao** Wang et al. **2025**, *ESSD* 17, 7055 — different group, different
  reconstruction, **1950–2022**. Ours is **Jin-Ping** Wang / Church / Zhang / Chen, 1900–2019.
  Same surname, nothing else. **Do not ingest it.**
  ⚠ **AMS is a CloudFront IP-LEVEL BLOCK on the whole domain, not a paywall** — scripted fetch
  and a real browser both get 403. The paper is **hybrid OA CC-BY** and OpenAlex lists **NO
  repository copy**, so the only host is the blocked one. The abstract *is* reachable (Semantic
  Scholar, `DOI:10.1175/JCLI-D-23-0410.1`) — the data statement is not.
  ⇒ **Don't retry AMS.** Route is a PDF in `ClaudeDocs/Papers/`, or ask Church.
  ⛔⛔ **RESOLVED 09-09b — THERE IS NOTHING TO DOWNLOAD.** Marcus supplied the statement:
  **every URL in it is an INPUT** (PSMSL, CSIRO altimetry, NASA/GSFC, ESGF CMIP6, NGL GNSS,
  ORA20C/SODA/GECCO3, Frederikse 2020, Malles & Marzeion, Peltier + Caron GIA). **Wang
  archives NO OUTPUT SERIES** ⇒ not an outage, not fixable by retrying; only the authors
  have it. ⭐ It also settles three things: Wang **uses CMIP6**; Wang **takes Frederikse
  2020**, so **all three** reconstructions share that input; and Wang uses **"the same tide
  gauge list and data editing criteria as in CW11"** — inherited, not re-screened.

---

## 4. ⭐⭐ ITEM 3 — THE RECALIBRATION, SCOPED AND NOT STARTED

**The IGCC update does NOT force a recalibration.** IGCC GMSL is an independent check,
explicitly *not in the fit*. The calibration's total term is Dangendorf 1900–2021 spliced from
2022 with NOAA STAR. **But tracing that turned up two real reasons, and they are the reasons to
do it — not the IGCC headline.**

### Reason 1 — the modern splice is a single-product anchor with a TYPED σ
`python/prep_recalib_targets_ext.py:316` reads `nasa_gmsl_annual.csv` (NOAA STAR, ends **2024**,
**sigma column EMPTY**) and assigns a hardcoded **`ALT_SIGMA_MM = 4.0`**. IGCC now publishes an
altimetry-only three-product ensemble **1993–2025** with a **MEASURED** across-product σ of
**0.35–2.89 mm**, and the two differ by up to **6.32 mm at 2024** re-referenced to 1993–2012.
⇒ our modern anchor is the one product IGCC dropped, carrying a typed uncertainty **1.4–11× the
measured spread**, where a measured multi-product alternative now exists.

### Reason 2 — the total term could be a reconstruction SPREAD, not one reconstruction
Wang's 1.3–2.0 mm yr⁻¹ spread across reconstructions is **the same size as the "deficits" we
currently report as model-vs-obs mismatch**. This is the scientifically strongest change and it
bears directly on [[deficits_are_unresolved]] and [[curvature_budget_no_closure]].

### Cost — chains are NOT the constraint
`notes/note_2026-08-12_vivek_joint_calibration_artifacts.md` records **4 parallel chains at
~1.06 h** for the non-joint sampler against **33.8 h** joint. ⚠ That was a different
configuration from L24's — treat it as an order of magnitude, and **measure L24's own** before
promising a number. **TORCH VERDICT (standing, say it out loud): LOCAL** for the non-joint
sampler; **Torch** if we go joint.

⛔⛔ **THE REAL COST IS DOWNSTREAM.** A new posterior moves **every shipped L24 number**: all five
pulse stages, both `/magiccclim` arms, the duration and ordering results, the CH₄:CO₂e exchange
rate, and the documentation section written 09-07
(`deliverables/pulse_model_differences_L24_section.md`). Marcus should weigh that, not the chain
hours.

### ⭐ THE RECOMMENDED SEQUENCE (my advice, awaiting his go-ahead)
1. Rebuild the targets with reasons 1 and 2 and run a **DIAGNOSTIC pass only** — measure how far
   the likelihood and the target trends actually move, on **window-matched** trends.
2. **Only then** commit chains. If the modern splice moves the fit by less than the posterior
   spread, this is a *provenance* update, not a *result* update — and that is worth knowing
   before redoing the pulse arc a month from submission.

### ⛔ TWO OPEN QUESTIONS MARCUS HAS NOT ANSWERED
1. **Go ahead on that sequencing** (diagnostic first), or straight to chains?
2. **Does the total term become a three-reconstruction spread, or stay Dangendorf** with Wang and
   Mu as comparison lines only? *(This is the one that changes the science.)*

⚠ Both are live. **Do not start §4 work without an answer** — [[handoff_open_item_is_not_a_ruling]].

### ✅ 09-09b UPDATE — Q1 ANSWERED, Q2 STILL OPEN, and the EVIDENCE ON Q2 MOVED
- **Q1 (sequencing): Marcus ruled DIAGNOSTIC FIRST.** The trend half has RUN —
  `python/diag_recon_trend_spread.py`, commits `7862308` + `6a45904`.
- **Q2 (spread vs Dangendorf) is STILL OPEN**, but the case for the spread is now
  **substantially WEAKER** and should be re-put to Marcus with this evidence:
  1. The naive 0.35 mm/yr spread is **mostly artifact** — ~0.16 **estimator** (IGCC's 1.85 is
     **Δ/n, not a slope**) + ~0.14 **window**; matched product term ~0.105, **inside
     Dangendorf's own ±0.19**.
  2. What survives is **ONE STRUCTURAL AXIS**, not scatter: CW11-lineage **+0.230** and Mu
     **+0.210** against Dangendorf over 1900–2007, and Wang **inherits CW11's gauge list**
     and sits high too. **Dangendorf is alone on the low side.**
  3. **All three share Frederikse 2020.** A spread across them is not independent error.
  4. **Wang's data cannot be obtained at all** (no archived output), so a
     three-reconstruction target is not constructible as specified regardless.
  ⇒ **My advice is now: KEEP Dangendorf as the fitted target, and carry the CW11 axis as an
  UNCERTAINTY rather than swapping the central estimate.** ⚠ Still Marcus's call.
- ⚠ **A NEW ITEM FOR HIM:** the axis is ~**2.46 cm** cumulative against the **+0.74 cm** by
  which Ladrillo sits above the target ⇒ **the gap we report as a model result sits INSIDE
  the reconstruction disagreement.** Trend-to-level, sign and magnitude only — **recompute on
  a stated baseline before quoting**. This is a reason to look, not a result.
- ✅ **Q2 RULED 09-09b: KEEP DANGENDORF as the fitted target, CARRY THE CW11 AXIS as an
  uncertainty.** Both open questions are now closed.
- ✅ **Reason 1 HAS NOW RUN** — `python/diag_modern_splice_altimetry.py`, commit `05d88f8`.
  ⛔ **It inverts this section's own framing.** The typed `ALT_SIGMA_MM = 4.0` is
  **CONSERVATIVE**, not loose: the measured across-product sd **in the spliced years** is
  1.9–2.3 mm (2.7–3.2 dropping the suspect column) and Dangendorf's own SE at the join is
  2.68 mm. Replacing it **TIGHTENS** the target. The "**1.4–11×**" claim above is the
  **era-wide** σ range and is **evaluated over the wrong window** — the early-1990s years
  the splice never touches dominate it.
  ⭐⭐ **The real defect is the LEVEL:** STAR **82.25** vs IGCC ensemble **85.92** mm at 2024
  ⇒ **+3.67 mm = 0.92σ**, with **every** IGCC product above STAR in every spliced year.
  Reach is **3 years** (2022–24), though the choice also sets the offset.
  ⭐ And §2's suspected col-3 product swap **tests AGAINST**: the `NOAA`-headed column is the
  **closest** of the three to actual STAR (rms 2.17, mean −0.24) vs NASA 2.44 and AVISO 5.13,
  and closer than AVISO-vs-NASA (3.18). A swap predicts the opposite ordering. **Vintage
  change ≠ product swap.** Not settled — the standing "do not use" stays in force, and
  neither conclusion depends on that column.

---

## 5. ⚠ A LOOSE END THAT GOT WORSE, NOT BETTER

`handoff_2026-09-05b_duration.md` §6.5 flagged two untracked `.docx` at the `SLR-RFF-BRICK` root
as **STALE Sep-2 duplicates** of the canonical `deliverables/` copy, and said committing a stale
copy at a second path is the silent-stale-retrieval trap. **They have since been COMMITTED** — in
`6ca2ec5`, a SLEIP commit that has nothing to do with them, so almost certainly an accidental
`git add -A`. They are still stale:

| path | md5 | mtime |
|---|---|---|
| `LadrilloUpdateDescription_L24.docx` (root) | `783194618c79…` | **2026-09-02** |
| `deliverables/LadrilloUpdateDescription_L24.docx` | `9f9cff351bfd…` | **2026-09-05** ⇐ canonical |

**Not mine to delete** — the `.docx` is a Marcus-edited source ([[l24_deliverable_docx_canonical]]).
**Recommended and awaiting his call:** `git rm --cached` the two root copies and gitignore that
path, leaving `deliverables/` canonical.

---

## 6. FILES

**New**: `python/ingest_igcc2026_gmsl.py`; `data/observations/igcc2026_gmsl_annual.csv`,
`igcc2026_gmsl_benchmarks.csv`; `data/observations/raw/igcc2026/` (drop + zip).
**Changed**: `python/plot_hindcast_components.py` (repointed, load path, legend, docstring),
`python/scripts/substack/fair_brick_vs_obs_gmst_gmsl.py` (repointed),
`figures/hindcast_components_L24.png` (regenerated), `FaIRtoFrEDI/CLAUDE.md` (index registration).
**Untouched deliberately**: `outputs/recalib_targets_ext.csv` and everything downstream of it —
that is §4 and it has not started.

## 7. MEMORY

**NEW (3)**: `igcc2026_gmsl_adopted`, `published_sigma_may_be_level_not_anomaly`,
`gmsl_reconstructions_are_total_only`.

⭐ **`INDEX_slr.md` was SPLIT, not trimmed** — it stood at **17495 B** against an 18432 B hard
ceiling with the IGCC adoption still to land ([[memory_index_split_beats_trim]]). New
**`INDEX_slr_obs.md`** takes the OBSERVATIONS (which product, which vintage, target construction
and splices, the curvature/budget arc, whether the budget closes); `INDEX_slr` keeps the MODEL
(structure and laws, posteriors and vintages, the standing benchmark, BRICK lineage).
**The split line and its straddling case — the DEFICITS ARC — are stated at the top of BOTH files
and in the project `CLAUDE.md`.** Result: **16737 + 5674**.

✅ Orphan sweep clean; **0 dangling** beyond the 3 known R-code false positives. One further
false positive of my OWN making was fixed rather than tolerated: `INDEX_cmp_pulse_dur.md`
described a template placeholder as `[[TABLE Tn]]`, which the sweep read as a wiki-link.
⚠ Root `MEMORY.md` is **16741 B content** against the 12288 soft target — over soft, well under
the 18432 hard ceiling, and **most of the growth since 09-07 is other sessions'. Do NOT trim
theirs.**
