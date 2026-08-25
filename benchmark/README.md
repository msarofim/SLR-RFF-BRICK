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
