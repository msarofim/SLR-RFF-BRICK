# The Ladrillo benchmark — a standing comparison you can re-run in one command

**Purpose (Marcus, 2026-08-25):** *"make these comparisons durable. E.g. BRICK2.0 versus the
full observational period and against MAGICC and FACTS and other constraints for future
projections. Then whenever we update a Ladrillo module we can quickly see how it matches that
comparison. And keep the best performing Ladrillo module in the comparison as well, so we can
quickly check if any changes improve against that best version."*

    source ~/climate-env/bin/activate
    python python/bench_ladrillo.py --tag=L15            # score a candidate
    python python/bench_ladrillo.py --tag=L15 --freeze   # snapshot it as a comparable arm
    python python/bench_ladrillo.py --tag=L15 --promote --why="ssp126 tail fixed"

Writes `outputs/bench_ladrillo_<TAG>.csv` (machine-readable, every metric) and
`outputs/bench_ladrillo_<TAG>.md` (the report, verdicts and deltas).

## The four arms every run scores

| arm | what it is | where it is frozen |
|---|---|---|
| **candidate** | the tag you are testing, read LIVE from `outputs/` | — |
| **champion** | the best-performing Ladrillo to date, per module | `benchmark/reference/<tag>/` |
| **BRICK 2.0** | stock MimiBRICK v2.0.0 on its own published posterior | `benchmark/reference/_fixed/` |
| **literature** | FACTS (13 modules/workflows), MAGICC-SLR (Nauels 2025) | `benchmark/reference/_fixed/` |

The champion and the fixed arms are **frozen copies**, not live paths. A benchmark whose
comparators move is not a benchmark: if `outputs/` is regenerated, the reference arms do not
change, and a score from today is comparable to a score from six months ago.

## What is scored — the five blocks

1. **[H] HINDCAST — the full observational period.** Per component × window
   (full / 1920-1949 / 1950-1992 / 1993-2026): bias, RMSE, max|err|, 90% coverage —
   each **also expressed in that component's own target 1-sigma**, because a raw RMSE
   ratio hides whether a miss is 0.2 sigma or 11.7 sigma (`handoff_2026-08-25b` §3).
2. **[R] OBSERVED RATE AND ACCELERATION.** The level can be right while the slope is
   wrong (`score_the_rate_not_the_level`). Both carry an **AR(1)-inflated OLS error bar**
   on the observations (`curvature_needs_an_error_bar`), so a "deficit" that is 0.3 sigma
   is reported as unresolved rather than as a finding.
3. **[P] PROJECTIONS vs the literature.** Per component × SSP × horizon, on the
   **JOINT** band (climate uncertainty in) wherever the draws exist, because FACTS and
   MAGICC carry forcing uncertainty and scoring our fixed-driver band against theirs is
   the `like_for_like_forcing` error. The fixed band is printed beside it, never scored.
4. **[S] SCENARIO SEPARATION.** ssp585/ssp126 median ratio against the full literature
   range. Marcus 2026-08-25: lying **between FACTS and MAGICC** is acceptable — so the
   verdict is bracket membership, not distance from a median.
5. **[V] VERDICTS AND DELTAS.** Per module: PASS / WARN / FAIL, and **BETTER / SAME /
   WORSE vs the champion** on every metric that has a direction.

### A median comparator is only a summary if the comparators agree

The spread test scores our width against the **median** comparator width. That is a summary
only when the set being summarised agrees. At ssp585@2150 the four model-based AIS
comparators span **8.4×** (ar5AIS 48.7 cm to deconto21 408.4) and split cleanly into a
no-MICI pair and a MICI/MAGICC pair, so the median lands in the **gap between the two
groups** and describes neither.

The test is exact and needs no threshold: score against **each comparator on its own** and
ask whether the median's verdict is one a **majority** of them share. Where it is not, the
verdict is **capped at WARN in both directions** — the median can no more earn a PASS than a
FAIL — and the note prints the per-comparator tally. As of L14 this caps four cells, all at
2150, all driven by deconto21: AIS and TOTAL at ssp245 *and* ssp585. **Two of the four are
cells where we look good** (ssp245@2150, 1.23× — capped from PASS), which is the check that
the rule is not a device for improving our own score. A FAIL a majority *does* support is
untouched (Greenland ssp126@2100 stays FAIL, 2 of 3 agree). `python bench_ladrillo.py
--selftest` mutation-tests it in every direction. (`diag_total_spread_ssp585_2150.py`.)

### "Measurably better than BRICK 2.0" — now checkable in every block

Marcus's standing stopping rule is *"if everything is measurably better than BRICK 2.0, and
everything passes the laugh test, at some point we can stop tweaking."* Until 2026-08-25 the
benchmark could only answer it for **[H]** and **[R]**: BRICK 2.0 appeared in **[P]** as an
unscored `median_fixed` row. Its projection **medians** are now scored against the same
literature, with a `median_vs_lit_delta` head-to-head row per cell.

⚠ **MEDIANS ONLY, DELIBERATELY.** Ours is the JOINT band and BRICK 2.0's is parameter-only;
a joint band moves a *median* by ≤5.4% but changes a *spread* by 1.5–1.6×, so scoring one
spread against the other is the `like_for_like_forcing` error. The spread is not compared.

Two rules keep the comparison honest:

* **A tie is a tie.** A difference in `|ratio − 1|` below `H2H_TIE` (0.02) reports SAME.
  Without it the table calls 1.455 vs 1.452 a loss.
* ⚠ **A projection win by an arm that fails the observations is not a win.** BRICK 2.0's
  glaciers sit closer to the literature median at three cells — while its glacier hindcast
  misses by 3.30 sd and its 1993–2026 rate by z = +2.39. That is a **compensating error**.
  Such cells report `WORSE(unearned)` and name the failing block.

And a total-level loss is uninterpretable without asking whether it was earned:
`component-error sum vs total error` reports, per cell, the sum of `|ratio − 1|` over the
five components beside the total's own error. Where an arm has **larger** component errors
and a **closer** total, the verdict is `CANCELLATION`, not skill.

## Reading a verdict honestly — three standing caveats the report re-prints every run

* **The hindcast is IN-SAMPLE for every Ladrillo arm** and out-of-sample for BRICK 2.0.
  It therefore **ranks in one direction only**: it can *reject* an arm that misses by
  many sigma, but a small fitted bias is not evidence of skill.
* **Bands are not all the same object.** Ladrillo-fixed and BRICK 2.0 are posterior-parameter
  spread only; Ladrillo-joint, FACTS and MAGICC carry climate uncertainty as well.
* **Some width is irreducible and must not be "improved".** 78% of our ssp585 2300 AIS band
  is the `antarctic_lambda` paleo prior; a narrower band there is a *worse* model, so the
  report never scores narrowness as a win at ssp585 AIS.

## Champion promotion is MANUAL and reasoned

`champions.json` records, per module, which tag is champion, when, and **why in one line**.
Promotion is a judgement — a tag that improves ssp126 spread while losing the hindcast is not
automatically better — so `--promote` requires `--why=`. Champions are per MODULE, not global:
a change that improves glaciers and leaves AIS alone promotes only glaciers.
