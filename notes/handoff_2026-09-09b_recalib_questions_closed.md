# Handoff — BOTH recalibration questions CLOSED; both diagnostics INVERTED their own premise

**Start here.** Work done 2026-09-09 (second session, "09-09b"). Supersedes nothing: the
predecessor `handoff_2026-09-09_igcc2026_and_recalib_scope.md` is **still live and was updated
in place** — its §3, §4 and §5 now carry the corrections below at the point of the claim, so
reading it will not mislead you. Read **that one for the IGCC adoption**; read **this one for
what was decided and measured afterwards.**

**STATUS: `SLR-RFF-BRICK` `ladrillo-dev`, clean, NOT PUSHED.**
> ⚠ **Do not type a commit count here** ([[status_field_carries_the_query]] — this note's own
> commit changes it). Run:
> `git -C ~/Documents/2026/CodeProjects/SLR-RFF-BRICK rev-list --count origin/ladrillo-dev..HEAD`

⚠ **A concurrent SLEIP session is committing to the same branch.** `cc0ff7f` and the
`CHANGELOG.md` / `notes/note_2026-09-09_sleip_comment_support.md` changes interleaved with mine
are **NOT this session's**. Mine, oldest first: `15ebdca`, `ca54c2c`, `7862308`, `6a45904`,
`ca51276`, `05d88f8`, `9d6b9cc` (+ this note's own commit).
`FaIRtoFrEDI` was **not touched** this session.

---

## 1. ⭐ THE THREE RULINGS — all Marcus, 2026-09-09b. These are RULINGS, not open items.

1. **Sequencing: DIAGNOSTIC PASS FIRST**, before any chains.
2. **Total term: KEEP DANGENDORF as the fitted target, and CARRY THE CW11 AXIS as an
   UNCERTAINTY.** ⇒ The total term does **not** become a reconstruction spread. The
   +0.21–0.23 mm/yr Dangendorf-vs-CW11 offset becomes an **uncertainty term**, not a change of
   central estimate. **§4 question 2 of the predecessor is CLOSED.**
3. **The stale root `.docx`: untrack + gitignore.** Done, `ca54c2c`.

⇒ **Both open questions of the predecessor handoff are now answered.** Nothing in §4 is
awaiting Marcus any more; what is awaiting him is the NEW choice in §5 below.

---

## 2. ⛔⛔ THE HEADLINE: BOTH DIAGNOSTICS CONTRADICTED THE SCOPING NOTE THAT ORDERED THEM

This is the thing to carry forward. The 09-09 scope gave two reasons to rebuild the targets.
**Measuring them weakened both.** The diagnostic-first sequencing existed exactly to find this
out before committing chains a month from submission, and it earned its keep.

| | the scope CLAIMED | the measurement SAYS |
|---|---|---|
| **Reason 2** — the recon spread is as big as our deficits | a spread on the total is the scientifically strongest change | the spread is **mostly artifact**, and what survives is **ONE AXIS** with Dangendorf alone on the low side ⇒ averaging over it is not sampling independent error |
| **Reason 1** — the typed `ALT_SIGMA_MM` is 1.4–11× the measured spread | our modern anchor carries an over-wide typed σ | the σ is **CONSERVATIVE** — replacing it **TIGHTENS** the target. The real defect is the **LEVEL** |

⇒ **On the evidence, this is looking like a PROVENANCE update, not a RESULT update.** That is
not yet a ruling — see §5.

---

## 3. ✅ DIAGNOSTIC 1 — `python/diag_recon_trend_spread.py` (`7862308`, `6a45904`)

The naive 0.35 mm/yr spread across Dangendorf **1.50** / Wang **1.60** / Mu **1.75** / IGCC
**1.85** decomposes:

| term | mm/yr | what it is |
|---|---|---|
| **estimator** | **~0.161** | ⛔⛔ **IGCC's 1.85 is Δ/n, NOT a slope.** Table 11 *defines* rate = Δ/n. Same series, same window: **Δ/n 1.851** (reproducing the published 1.85) vs **OLS 1.691**. **Never put 1.85 in a column beside the other three.** |
| **window** | ~0.135 | Dangendorf **alone**, 1.390 (1900–2007) → 1.524 (1900–2021). That is the record's **acceleration**, not disagreement. |
| **product** | ~0.105 | Dangendorf 1.526 vs IGCC 1.632 on a **derived** 1901–2021 overlap, matched estimator — **inside Dangendorf's own ±0.19** |

⭐ **THE ESTIMATOR QUESTION CLOSED ITSELF.** Mu never states its estimator, but it states its
benchmark: *"Our curve yields a rate of 1.60 mm yr⁻¹, very close to the rate of 1.62 mm yr⁻¹ by
C2011."* **Our OLS on CSIRO Recons over 1900–2007 = 1.620** — reproducing that 1.62 to the quoted
precision. ⇒ OLS is what these papers report, so **Mu is +0.210 above Dangendorf**, not the Δ/n
+0.132.

⭐⭐ **AND THE SURVIVOR IS ONE STRUCTURAL AXIS, NOT SCATTER.** Over 1900–2007, all OLS:
CW11-lineage **+0.230** and Mu **+0.210** against Dangendorf — same sign, same size — and **Wang
inherits CW11's gauge list and editing criteria verbatim** and sits high too (+0.10 over
1900–2019). **Dangendorf is alone on the low side.** All three also take **Frederikse 2020**.
⇒ **This is the evidence behind ruling 2.**

### ⚠ A NEW ITEM, and it is a REASON TO LOOK, NOT A RESULT
0.230 mm/yr × 107 yr = **2.46 cm** cumulative, against the **+0.74 cm** by which Ladrillo sits
above the Dangendorf-built target on the L24 total panel ⇒ **the reconstruction axis is ~3× the
gap we currently report as a MODEL result**, so that gap **sits inside the reconstruction
disagreement**.
⛔ **This is a TREND-to-LEVEL comparison and the level depends on the reference window.**
**Sign and order of magnitude ONLY. Recompute on a stated baseline before anyone quotes it.**
Bears on [[deficits_are_unresolved]] **for the TOTAL term only.**

---

## 4. ✅ DIAGNOSTIC 2 — `python/diag_modern_splice_altimetry.py` (`05d88f8`)

### The σ case is DEAD
| in the spliced years **2022–24** | mm |
|---|---|
| typed `ALT_SIGMA_MM` | **4.00** |
| measured across-product sd, all 3 | **1.92–2.25** |
| same, suspect column dropped (n=2) | **2.72–3.18** |
| **Dangendorf's OWN SE at the join (2021)** | **2.68** |

⇒ the typed σ is **above** the measured spread **and** above the reconstruction's own SE at the
join. **Replacing it TIGHTENS the target.** ⚠ The scope's "**1.4–11×**" is not wrong, it is
**evaluated over the wrong window** — that is the **era-wide** published range (0.35–2.89 mm),
dominated by the early-1990s years the splice never uses. Over the splice window it is 1.3–2.1×.
**[[like_for_like_forcing]] applies to a σ's window as much as to a trend's.**

### The LEVEL case is live, and small in reach
Offset-matched to Dangendorf over 2003–2018, at **2024**: **STAR 82.25 mm vs IGCC ensemble
85.92 ⇒ +3.67 mm = 0.92× the σ it is assigned.** **Every** IGCC product is above STAR in **every**
spliced year, and STAR is **the one product IGCC dropped** — ⚠ **for AVAILABILITY, not quality.**
**Reach = 3 of 122 years** (2022–24) directly, though the choice **also sets the offset** via the
2003–2018 match, so it moves those years twice over. **IGCC altimetry runs to 2025**, one year
past STAR.

### ⭐ The suspected col-3 product swap TESTS AGAINST
§2 of the predecessor suspected `altimetry_indiv_estimates.csv` col 3 (headed `NOAA`, paper says
U. Colorado) of being a swapped product, on a **VINTAGE** observation (+7.1 mm at 2024 between
releases). Tested for **product IDENTITY** instead — all offset-matched, 1993–2024:

| vs actual NOAA STAR | rms mm | mean mm |
|---|---|---|
| **the `NOAA`-headed column** | **2.17** | **−0.24** |
| IGCC NASA | 2.44 | −0.70 |
| IGCC AVISO | 5.13 | −1.26 |
| *AVISO vs NASA (within-IGCC)* | *3.18* | *−0.56* |

It is the **closest** of the three to STAR, near-zero mean bias, and **closer than AVISO and NASA
are to each other**. A swap predicts the **opposite** ordering.
⇒ ⭐ **A vintage change and a product swap are DIFFERENT CLAIMS** — the +7.1 mm is equally
consistent with the **re-download** the paper describes (three products re-fetched Feb–Mar 2026).
⚠ **NOT settled** — these products share missions and are highly correlated. **The standing "do
not use that column until settled" is LEFT IN FORCE**, and **every number above is reported with
and without it**: 2-product mean at 2024 **85.90** vs 3-product **85.92**.

---

## 5. ⛔ WHAT IS OPEN — one NEW choice, and it is the only thing blocking `prep_recalib_targets_ext.py`

**Nothing from the predecessor is open any more.** This is new, and follows from §4:

1. **Does the modern anchor become the IGCC altimetry ensemble instead of NOAA STAR?**
   (It also picks up **2025**.) The case for: STAR is a single product, the one IGCC dropped, and
   it sits ~1σ low against all three. The case against: reach is 3 years.
2. **Does `ALT_SIGMA_MM` stay at its conservative 4.0, or move to the measured per-year spread?**
   ⚠ **Moving it TIGHTENS the target** — that is a real consequence, not a tidy-up, and it is
   the opposite of what the scoping note implied.
3. **Is this a PROVENANCE update or a RESULT update?** §2 says provenance on the evidence so far.
   ⚠ **Nobody has ruled.** ⛔ **The downstream cost has not changed and is still the real cost:**
   a new posterior moves all five pulse stages, both `/magiccclim` arms, duration and ordering,
   the CH₄:CO₂e exchange rate, and `deliverables/pulse_model_differences_L24_section.md`.

⚠ **Do not rebuild targets on any of these without an answer** — [[handoff_open_item_is_not_a_ruling]].
**TORCH VERDICT (standing, say it out loud): LOCAL** for the non-joint sampler; **Torch** if joint.

---

## 6. ⛔ WANG IS UNOBTAINABLE — this is CLOSED, do not spend another session on it

Marcus supplied the data-availability statement. **Every URL in it is an INPUT** (PSMSL, CSIRO
altimetry, NASA/GSFC, ESGF **CMIP6**, NGL GNSS, ORA20C/SODA/GECCO3, **Frederikse 2020**, Malles &
Marzeion, Peltier + **Caron 2018** GIA). **Wang archives NO OUTPUT SERIES.**
⇒ **Not an outage, not fixable by retrying, no repository copy exists.** Only the authors have it.
⚠ **AMS is a CloudFront IP-level block on the whole domain, not a paywall** — scripted fetch and a
real browser both 403; the paper is hybrid-OA CC-BY. **Don't retry AMS.**
⛔⛔ **`10.5281/zenodo.15288816` IS A DECOY** and search offers it confidently — it is **Shengdao**
Wang 2025 (ESSD 17, 7055; 1950–2022), not **Jin-Ping** Wang 2024. Caught before ingestion.
✅ The statement also settled three things: Wang **uses CMIP6**; Wang **takes Frederikse 2020**
(so **all three** reconstructions share it); and Wang uses **"the same tide gauge list and data
editing criteria as in CW11"** — inherited, not re-screened.

**Mu is a pure retry.** Zenodo returned **504 from its own gateway** in ~30 s on every route on
both 09-08 and 09-09, while DNS resolved, TCP 443 connected and GitHub + doi.org answered.
**Their outage.** ⚠ **Nothing above needed it** — Mu's published numbers carried the argument.

---

## 7. ⚠ NON-OBVIOUS STATE, AND TWO TRAPS FIXED IN PASSING

- **`CSIRO_Recons_gmsl_yr_2015.csv` needs a custom loader.** Its `#` header lines sit **inside a
  quoted field**, so pandas' `comment=` does **not** strip them; and its stamps are **mid-year**
  (1880.5), where `round()` is **half-to-even** and mapped 1880.5→1880 but 1881.5→**1882**,
  silently duplicating and skipping years. **Use `floor()` and assert year-uniqueness.**
- **Derive a common window, never type one.** A hardcoded `(1900, 2019)` silently reported
  "NOT COVERED" for IGCC, which starts 1901.
- ⚠ **The `*_ens.csv` files in the IGCC drop are `mean`+`std`, NOT members** — the names mislead.
  So [[published_sigma_may_be_level_not_anomaly]]'s "no members ⇒ band not computable" **stands**
  for the 1901–2025 GMSL. **But `altimetry_indiv_estimates.csv` DOES give three members for the
  altimetry era**, which is where the splice lives — that is what made §4 measurable at all.
- **The `.docx` untracking is deliberately narrow.** Only `LadrilloUpdateDescription_L24.docx`
  (root, 09-02, stale) was untracked. **`LadrilloUpdateDescription.docx` (no `_L24`, 15 KB) is a
  DIFFERENT document with no counterpart anywhere in the tree** — untracking it would have left it
  with zero tracked copies. It stays tracked, and the `.gitignore` entry is a **literal path, not
  a wildcard**, so a later edit cannot swallow it. Both files are still on disk; neither was
  deleted ([[l24_deliverable_docx_canonical]]).

## 8. THE WANG CITATION WAS INVERTED — corrected everywhere in one pass (`15ebdca`)
The 09-09 note and the memory both starred the abstract's **second** clause and dropped its
**first**. It opens: *"**Despite GMSL budget closure in terms of long-term trend since 1900,**"*
and only then reports sub-period discrepancies. ⇒ Wang reports **CLOSURE** on the long-term
1900–2019 trend (1.6 ± 0.2 vs contributions 1.5 ± 0.2) **and SUB-PERIOD non-closure** (early
century worst, **land ice** named). **Cite it for the second; NEVER for the first — Wang is not an
external witness to a whole-record deficit.** Separately, the **1.3–2.0 mm/yr spread is across
PRE-EXISTING reconstructions over 1900–2008** — a third statement, different window, not about
closure at all. Fixed at every quoting site in the same edit
([[retraction_in_place_does_not_propagate]]).

---

## 9. FILES

**New**: `python/diag_recon_trend_spread.py`, `python/diag_modern_splice_altimetry.py`,
`outputs/diag_recon_trend_spread.csv`, `outputs/diag_modern_splice_altimetry.csv`, this note.
**Changed**: `notes/handoff_2026-09-09_igcc2026_and_recalib_scope.md` (corrections in place),
`.gitignore`, `CHANGELOG.md`.
**Untracked (file kept on disk)**: `LadrilloUpdateDescription_L24.docx`.
⛔ **UNTOUCHED DELIBERATELY**: `python/prep_recalib_targets_ext.py`,
`outputs/recalib_targets_ext.csv` and **everything downstream**. No target was rebuilt, no chain
was run, and no shipped L24 number moved.

## 10. MEMORY

**NEW (3)**: `gmsl_recon_methods_compared`, `recon_spread_is_mostly_estimator_and_window`,
`modern_splice_defect_is_level_not_sigma`.
**UPDATED**: `gmsl_reconstructions_are_total_only` (Wang unobtainable + the decoy + the inverted
citation), `INDEX_slr_obs` (three new pointer lines).
Budgets measured on CONTENT ([[memory_budget_is_content_not_file]]) — `INDEX_slr_obs` is well
under its 14 KB soft target; no split needed.
