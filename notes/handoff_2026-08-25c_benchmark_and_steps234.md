# Handoff — the comparison is now a STANDING BENCHMARK; steps 2–4 done and all PASS

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, commits **`8acedd3`** (the
benchmark) and **`4b4ee93`** (steps 2–4), on top of `4086176`. Written 2026-08-25 to be
picked up cold. **Continues** `handoff_2026-08-25b_module_assessment.md` (step 1 = AIS).

**NOTHING WAS RECALIBRATED. NO CHAIN WAS READ.** Everything here is post-processing over
files that already existed, plus one cheap new Julia projection run (~30 s).

---

## 0. THE TASK

Marcus, 2026-08-25, two things at once:

> *"Read handoff at handoff_2026-08-25b_module_assessment.md and continue work. One
> additional task: make these comparisons durable. E.g. BRICK2.0 versus the full
> observational period and against MAGICC and FACTS and other constraints for future
> projections. Then whenever we update a Ladrillo module we can quickly see how it matches
> that comparison. And keep the best performing Ladrillo module in the comparison as well,
> so we can quickly check if any changes improve against that best version."*

Both are done: the benchmark (§1) and steps 2, 3, 4 (§2). **Step 5 is not started and is
Marcus's call** (§4).

---

## 1. THE BENCHMARK — `python/bench_ladrillo.py`

    source ~/climate-env/bin/activate
    python python/bench_ladrillo.py --tag=L15                      # score a candidate
    python python/bench_ladrillo.py --tag=L15 --freeze             # make it comparable later
    python python/bench_ladrillo.py --tag=L15 --promote --why="…"  # champion, per module
    python python/scope_module_assessment.py --all                 # steps 2–4 on top of it

Writes `outputs/bench_ladrillo_<TAG>.csv` (every metric) and `.md` (the report).
`benchmark/README.md` is the contract; read it before changing a metric.

### Four arms, and three of them are FROZEN

| arm | what | where |
|---|---|---|
| candidate | the tag under test, LIVE from `outputs/` | — |
| **champion\*** | best-performing Ladrillo to date, **per module** | `benchmark/reference/<tag>/` |
| BRICK 2.0 | stock MimiBRICK v2.0.0, own published posterior | `benchmark/reference/_fixed/` |
| literature | FACTS (13 modules/workflows) + MAGICC-SLR | `benchmark/reference/_fixed/` |

**Frozen copies, not live paths** — a benchmark whose comparators move with `outputs/` cannot
compare today's score with one from six months ago. Champion draws are stored **raw** (gzipped,
~1 MB/SSP) rather than as precomputed percentiles, so that if a metric definition ever changes
the champion's score is recomputable **under the new definition**.

`champions.json` is **per module** (a change that improves glaciers must not take credit for
AIS) and `--promote` **requires `--why=`**: promotion is a judgement, not a threshold.
Currently every module's champion is **L14**, frozen at `8acedd3`.

### Five blocks

**[H]** hindcast, per component × {full, 1920-49, 1950-92, 1993-2026}, always **scaled to that
component's own target 1-sigma**. **[R]** rate (1993–2026) **and** acceleration (1900–2026) with
an observational error bar. **[P]** projections **on the JOINT band** (fixed shown, never
scored). **[S]** separation vs the literature **bracket**. **[V]** roll-up + BETTER/SAME/WORSE
vs champion.

### ⚠ THE GAP THAT WAS FILLED: BRICK 2.0 had no projection arm beyond glaciers

`julia/project_ssps_components_oldbrick.jl` (**NEW**) — all six components, six SSPs, to 2300,
same forcing / re-reference window / output schema as Ladrillo, ~30 s.
`[GSIC-MATCH]` reproduces the standalone glacier driver to **0.0000 cm**, so the new file is
like-for-like with the one arm that already existed. Every AIS/GIS/TE/total cell of
`ladrillo_model_comparison_*.csv` had been blank, and `-25b` §3 had to warn against reading a
blank as a zero. That warning is now obsolete.

### ⚠ THREE METRIC RULES ADDED WHILE RUNNING IT — each changed a verdict

1. **The observational error bar takes the CONSERVATIVE of THREE accounts**: estimator scatter
   about the fit, the published `_lo`/`_hi` band refitted under **perfect correlation**, and the
   same band propagated under **independence**. The first two are both far too tight for a
   *rate* — a cumulative series is smooth, and a near-parallel envelope cancels its own level
   uncertainty. **Without the third, a 7% glacier rate difference was being flagged at 9.5
   sigma.** ⚠ All three omit shared-method error across reconstructions ⇒ every bar is a lower
   bound.
2. **Ratio-interpretability and gradeability are different questions.** Where the observed
   statistic is under 2 se from zero the **ratio** model/obs is suppressed as uninterpretable,
   but the **difference** is still graded on z. **Four of five acceleration targets are in that
   state.** My first patch suppressed the verdict too, which erased BRICK 2.0's real 3.07-sigma
   glacier-acceleration miss; the second separates them.
3. **The separation bracket's edge tolerance is 25% of the comparators' OWN range**, not a
   picked number (`tolerance_scaled_to_spread`). TE at 1.97× against a 2.05–2.51 bracket is
   PASS(edge), not FAIL.

---

## 2. STEPS 2, 3, 4 — `python/scope_module_assessment.py`

One parameterised script, not three copies of the step-1 template: every criterion-(2)/(3)
number now comes from the benchmark CSV, so step 2 and a re-run six months from now use the
**same** metric. What is genuinely per-module is criterion (1), the **formulation dossier**,
which is facts with `file:line` provenance and is the only hand-written part.

### STEP 2 — GLACIERS: **PASS**

* **(1) FORMULATION — a real gain, argued.** The glacier slot IS `replace!`d, so unlike AIS
  this is not BRICK 2.0's component. BRICK 2.0 = Wigley–Raper GSIC: **one** reservoir,
  dV/dt ∝ (T − teq), and **no finite equilibrium** — any sustained T > teq commits every glacier
  to **total** loss, and `gsic_teq` is not even sampled in its posterior. Ladrillo =
  `glaciers_nu3`: **three** reservoirs (R19 / SLOWP / FAST), each with a finite
  temperature-dependent equilibrium and a Nauels-ν transient, each on its own glacier-area
  driver. Externally provenanced by GlacierMIP3 committed-loss rungs. ⚠ **Cost: 15 sampled
  parameters against 4**, and one global cumulative series cannot identify three reservoirs —
  the rungs are what identify it, so the formulation is exactly as credible as they are.
* **(2) HINDCAST — BETTER in 3 of 4 windows** (0.34–0.37× RMSE); worst window **1.28 sd**
  against BRICK 2.0's **3.57 sd**.
  **⚠ `-25b`'s standing question is ANSWERED.** The "1.01× WORSE over 1950–1992" is a **tie
  below the observations' resolution**: both arms sit at **0.29 sigma** of the glacier target
  in that window. Not a regression.
* **(2b) RATE** 1993–2026: ours z = **−0.54 UNRESOLVED**; BRICK 2.0 z = **+2.39 FAIL**.
* **(3) PROJECTION — the defect.** Medians **0.80–0.91×** the literature at 2100 and
  **0.755–0.785×** at 2150: systematic across every scenario, and **growing with horizon**.
  Spreads PASS everywhere (0.58–0.94×). Separation 1.81× sits inside FACTS 1.73–1.92 /
  MAGICC 1.46.
* ⚠ **Glaciers are 40.1% of ADDRESSABLE uncertainty at ssp126@2100** — the top contributor
  there — so a 16% level deficit at that cell is not cosmetic.

### STEP 3 — GREENLAND: **PASS**, with the flexibility Marcus allowed

* **(1)** Also `replace!`d. The justification is a hindcast feature the old form **structurally
  cannot fit**: Greenland cooled at −1.8 °C/century 1940–1990 while the globe warmed, so a
  GMST-driven Greenland misses the 1942–1982 window by construction. Two channels, split
  **pinned by Mouginot 2019** (73.5% surface) rather than by the sea-level history.
* **(2) THE HARDEST REJECTION OF BRICK 2.0 OF ANY MODULE**: 0.05–0.27× its RMSE, BETTER in
  **all four** windows; worst window **0.44 sd** against **4.99 sd**.
* **(2b)** Rate and acceleration are UNRESOLVED for **both** arms — Greenland's modern rate does
  not separate them on this estimator and window.
* **(3) THE DEFECT IS THE SPREAD, NOT THE LEVEL.** Medians PASS at 2100 (0.84–0.97×) and
  degrade at 2150 (0.43–0.82×); the **spread FAILS at 5 of 6 cells, 0.14–0.46×** the literature.
* ⚠ **Carried forward, not re-litigated:** the 2100 projection is 1.31–1.32× fast against
  ISMIP6, that bias is the **amp law**, and it is **hindcast-inert** — criterion (2) cannot see
  it. Do not read the criterion-(2) PASS as its absence.
* Marcus's "more flexibility" has a number: Greenland is **6.0%** of the ssp585@2300 joint band
  and **8.8%** of addressable, against AIS's 82.7%.

### STEP 4 — THE SUM: **PASS**

* **(1)** ⚠ **NOT the conjunction of steps 1–3, in either direction.** The covariance residual
  is **+18% to +34%**, so a total-level PASS can hide compensating component errors. Scored on
  its own. It is also the only level with a direct observational target of its own (Dangendorf),
  whose 1-sigma is **3–9× wider** than any component's — so a total that matches Dangendorf is a
  much weaker statement than four components matching theirs.
* **(2)** BETTER in **all four** windows (0.35–0.96×); worst 0.64 sd against 1.66 sd.
* **(2b)** The 1993–2026 rate is **1.04× obs at z = +0.43** — the total rate matches.
* **(3)** **ssp585 PASSES level AND spread at both horizons** (1.09–1.25× / 0.52–1.16×);
  **ssp126 and ssp245 medians run 0.61–0.83×.** Separation 2.69× @2100 sits inside FACTS
  1.63–2.23 / MAGICC 2.75.

### ⇒ THE FOUR DEFECTS ARE ONE DEFECT

| step | module | defect |
|---|---|---|
| 1 | AIS | ssp126 **spread** 0.24–0.33× (fast-dyn is *exactly* 0.000 cm there) |
| 2 | glaciers | **level** 0.755–0.91×, every scenario, growing with horizon |
| 3 | Greenland | **spread** 0.14–0.46× at 5 of 6 cells |
| 4 | the sum | ssp126/245 medians **0.61–0.83×**, ssp585 **1.09–1.25×** |

**ssp585 passes level and spread at both horizons; the cool scenarios do not.** Three of the
four are **MODEL-FORM** — the binary AIS threshold, the glacier level law, the Greenland width —
so **a recalibration on the same likelihood will not fix them.**

---

## 3. ⚠ NEW AND UNEXPLAINED — the TE rate, and it is NOT ours

Over 1993–2026 thermal expansion runs **1.19× the steric target at z = +4.19**, and **BRICK 2.0
misses it almost identically: 1.17×, z = +3.74.** Two independent calibrations of the **same**
MimiBRICK component under the **same** FaIR mean OHC ⇒ this is the **OHC driver or the steric
target**, not the Ladrillo calibration. ⚠ **The direction is NOT settled** — OHC products
disagree by ~2× and Cheng is the low-side outlier (`igcc_ohc_finding`), so do not write "FaIR
OHC runs hot" without naming the product. Two tests that would separate it: re-score TE against
a second steric product; and check whether the same 1.19× appears in the OHC space directly
rather than through `te_α`.

---

## 4. WHAT TO DO NEXT — step 5 is unblocked but is a JUDGEMENT

Steps 1–4 all PASS, which is the condition Marcus set for step 5 (= his criterion 4, the joint
calibration). **It was deliberately not started.** The case against starting it immediately:

* three of the four residual defects are **model-form** and would survive a recalibration
  unchanged;
* ⚠ `ais_iceflow0` R-hat **2.244**, 9 of 17 AIS params fail at L14, and the **pooled-proposal
  lever (`--adcov=`) should go in first** — 4 RAM proposals disagree **347×** in shape while
  every acceptance rate sits on 0.234 (`acceptance_rate_certifies_nothing`);
* the `ais_gmst_amp ≈ 0.94` de-amplification needs a **refit** and naturally combines with it;
* ⚠ **do NOT resurrect the joint FaIR/BRICK calibration** — banner-marked REJECTED in
  `notes/negresult_2026-08-01_joint_forcing_calibration.md`; the directive is propagate forcing
  forward, never re-calibrate it against SLR;
* ⚠ **check `sshare` before submitting** — fairshare was 0.28 on 2026-08-01.

**The question for Marcus:** does step 5 run as-is (recalibration + `--adcov=` + the amp refit),
or does the cool-scenario model-form question get settled first? The binary AIS fast-dynamics
term is the single largest of the four and is the only one that would change what the
recalibration is calibrating.

**Second open item, smaller:** a transient **global-cm** glacier literature target does not
exist in this repo. GlacierMIP3 is present but as a committed-loss ladder that is **already in
the likelihood** (so not an independent check), and the GloGEM/OGGM archives are scoped in
`python/scope_glacier_model_constraints.py` as **per-block mass-loss percentages, not global
cm**. Step 2 rests on three comparators until that is built; the fetch recipe is in that
script's header.

---

## 5. NON-OBVIOUS STATE / TRAPS

* ⚠ **Re-run `--freeze-fixed` if BRICK 2.0 or the FACTS/MAGICC files are ever regenerated**, or
  the frozen comparator silently diverges from the live one. The manifest carries a sha256
  prefix for exactly this check.
* ⚠ **LWS spread is 0.00 cm by construction** (seeded constant) and is marked
  `N/A(by construction)`, not FAIL. Do not "fix" it.
* ⚠ **The ssp585 AIS width must NOT be narrowed** — 78% of it is the `antarctic_lambda` paleo
  prior. The benchmark exempts that cell from the too-wide half of the spread test only; it is
  still FAILing there at 2150 for being too **narrow** (0.397×), which is a different problem.
* ⚠ **ssp245@2300's median is a threshold artifact** (48.3% of draws tip). Quote the mean and
  the tipped fraction. The benchmark writes `mean` into the note of every `median_joint` row.
* ⚠ `git add -A outputs/` sweeps in **227 deliberately-untracked** mcmc artifacts. Stage by name.
* ⚠ `benchmark/reference/` is committed with `git add -f` because `outputs/`-shaped paths are
  gitignored in places; check `git status` after freezing a new champion.

---

## 6. FILES AND COMMITS

**New:** `python/bench_ladrillo.py`, `python/scope_module_assessment.py`,
`julia/project_ssps_components_oldbrick.jl`, `benchmark/{README.md,champions.json,reference/}`,
`outputs/bench_ladrillo_L14.{csv,md}`, `outputs/scope_module_assessment_{glaciers,gis,total}_L14.csv`,
`outputs/ssps_components_2300_oldbrick.csv`, this note.
**Memories:** `bench_ladrillo_standing`, `cool_scenario_underdispersion`; `INDEX_slr.md` +2 lines;
`MEMORY.md` live-state updated.
**CHANGELOG:** `2026-08-25e`.
**Commits:** `8acedd3`, `4b4ee93`.
