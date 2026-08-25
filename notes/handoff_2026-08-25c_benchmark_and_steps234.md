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

---

# ADDENDUM — 2026-08-25, after Marcus chose "fix the ssp126 form first"

Commit **`a29ea6c`**. **The choice was right and the first measurement retracted the defect it
was made about.** Nothing was recalibrated; `python/diag_ais_ssp126_tail_anatomy.py` reads the
draws that already existed.

## A. STEP 1'S NAMED RESIDUAL DEFECT IS WITHDRAWN

The claim was: *"at ssp126 the band has no tipping tail at all — the fast-dynamics term is
EXACTLY 0.000 cm in every arm and horizon."* **That is a FIXED-DRIVER statement**, quoted about
a model whose reported band has been the JOINT one since 2026-08-25. Under the joint band
(`outputs/diag_ais_tipping_under_forcing_L14.csv`, per-draw config):

| ssp126 | 2100 | 2150 | 2300 |
|---|---|---|---|
| tipped, per-draw config | **3.95%** | **3.75%** | **6.30%** |
| tipped, shipped MEAN driver | 0.05% | 0.00% | 0.00% |

**The tail exists.** And the benchmark score that seemed to corroborate the claim — ssp126 AIS
spread 0.24–0.33× the literature — **was the same error a second time**: a p05–p95 interval is
**arithmetically blind** to a mode carrying under 5% of the mass, because that mode sits entirely
above the p95 cut. Our p05–p99 / p05–p95 there is **8.45**; the Gaussian value is **1.207**.

## B. WIRED IN, AND IT DISCRIMINATES

`bench_ladrillo.py` now marks any cell whose p05–p99 / p05–p95 exceeds **2× the Gaussian
1.207** as `N/A(bimodal)` and does not score it on width; its median row carries the **mean**
beside it (ssp126@2150: median 0.31× lit, **mean 0.50×**). ⚠ **The guard is not a blanket
excuse** — Greenland's ratios are **1.35–1.45**, so its five spread FAILs are untouched and are
now **the largest genuine width problem in the model**.

## C. THE PROPOSED FIX WOULD NOT HAVE WORKED

`g = (excess/ref)^n` (`julia/antarctic_icesheet_magdep_component.jl`) is **zero below threshold
for every n**, and 96% of ssp126 draws never tip. It is the ssp245/ssp585 **separation** fix
(`ais_binary_form_priced`), not the ssp126 one. **Binary in MAGNITUDE and binary in ONSET are
two different features.** Had step 5 been preceded by "adopt the magnitude-dependent fork to fix
ssp126", it would have changed nothing at ssp126 and the failure would have been read as
evidence about n.

## D. WHAT THE COOL-SCENARIO PROBLEM ACTUALLY IS NOW

Not widths — **levels**, plus one real width problem in Greenland:

* **AIS**: ssp126/ssp245 **medians** 0.31–0.51× lit (mean 0.50–0.68×); ssp585@2150 **spread**
  0.397×, unimodal, so that one stands.
* **glaciers**: **level** 0.755–0.91×, every scenario, growing with horizon.
* **Greenland**: **spread** 0.14–0.46× at 5 of 6 cells — unimodal, real, and now top of the list.
* **the sum**: ssp126/245 medians 0.61–0.83× while ssp585 is 1.09–1.25×.

## E. THE OPEN QUESTION, RESTATED PRECISELY

Not *"why is our ssp126 band narrow"* but ***"is 3.95% the right tipped fraction at
ssp126@2100"*** — a **threshold** question, about the probability of marine ice-sheet
instability onset under low forcing, needing literature this repo does not have. It is a
different question with a different fix and different evidence from the one the fork answers.

**Suggested next, in order:** (1) the Greenland width — real, unimodal, 5 of 6 cells, and the
module is closed so this is a deliberate reopening decision; (2) the tipped-fraction literature
for ssp126; (3) the glacier level deficit; (4) step 5 with `--adcov=` + the `ais_gmst_amp` refit.

---

# ADDENDUM 2 — 2026-08-25, the Greenland width, priced

Commit **`bbee082`**, `python/diag_gis_width_anatomy.py`. **Nothing recalibrated.** Marcus:
*"Do the Greenland width next."* Priced before proposing a fix — and it shrank by 4×.

## A. WHAT THE DEFICIT ACTUALLY IS

Against **model-based** comparators (structured expert judgement excluded, §D):

| ours / theirs | ssp126 | ssp245 | ssp585 |
|---|---|---|---|
| @2100 | **0.49×** | 0.69× | **0.92×** |
| @2150 | 0.62× | 0.74× | **1.08×** |

**Scenario-graded, and it vanishes at ssp585.** The benchmark's flat "0.14–0.46× at 5 of 6
cells" was **two-thirds comparator selection**. At ssp126@2100 the four comparators are
FittedISMIP 7.06, Nauels2025 9.57, emuGrIS 17.14, **bamber19 55.71** — an 8× span. And at
2150 only two exist, so their "median" (49.03 cm) is the **mean of a process band and an
expert-elicitation envelope — a width no module produces**.

## B. IT IS NOT OUR CLIMATE ENSEMBLE — the TE control

Greenland is **80–91% forcing**, so a narrow FaIR ensemble would produce a narrow Greenland
band with nothing wrong in the ice sheet. **Thermal expansion is the control**: 94–96%
forcing at *every* scenario, same FaIR configs, its own comparators.

| | ssp126 | ssp245 | ssp585 |
|---|---|---|---|
| TE vs lit @2100 | 0.89× | 0.81× | 0.78× |
| GIS vs like-for-like @2100 | 0.49× | 0.69× | 0.92× |

TE is **flat**; GIS grades **1.9×**. A narrow ensemble would make both flat. **The missing
width is Greenland's own.** (Our GIS parametric σ is 0.435 cm at ssp126@2100 = 9% of the
joint variance.)

## C. THE OUT-OF-SCOPE TERM CLOSES ssp585 AND NOT ssp126

Marcus's standing constraint (2026-08-23): *"we aren't trying to match between-model spread
(we don't have the precipitation level), just between-scenario spreads."* ISMIP6 measures
that term **at fixed forcing** — one GCM through 9–14 ice-sheet models — so it can be
subtracted rather than assumed. Composed **in variance** (never by adding p05–p95 ranges),
and required to hold at the **larger, range-based** σ, the one that favours "it is structural":

| | ours | +ISM(IQR) | +ISM(range) | like-for-like target | |
|---|---|---|---|---|---|
| ssp585@2100 | 11.21 | 11.85 | **13.70** | 11.81 | **CLOSED** |
| ssp126@2100 | 4.69 | 4.99 | **6.02** | 8.32 | **2.30 cm missing** |

⚠ IQR- and range-based σ disagree up to 2.2× because the ISM **min** is an outlier (at
CNRM-CM6-1 ssp126 the min sits 2.4 cm below p25 while the IQR spans 0.70 cm). Both reported.

## D. PRICED ON THE DELIVERABLE — and it does not justify reopening the module

| | GIS gap | total now | total, independent | total, correlated |
|---|---|---|---|---|
| ssp126@2100 | 3.63 cm | 24.33 | **25.28 (+3.9%)** | 31.20 (+28.2%) |
| ssp126@2150 | 4.21 cm | 36.51 | **37.54 (+2.8%)** | 45.22 (+23.9%) |
| ssp585@2100 | 0.60 cm | 81.94 | 82.03 (+0.1%) | 85.66 (+4.5%) |

The **independent** column is the estimate — the missing width would come from Greenland's
**own** parameters, which the sampler makes independent of the other components. Correlated
is an upper bound that would apply only if the widening rode a shared forcing channel.

⇒ **One surviving FAIL cell in the whole module (ssp126@2100, 0.489×), worth ~4% of one
scenario's band.** Greenland is a CLOSED module; +4% of the ssp126 total does not justify
reopening it. **The glacier level deficit now outranks it** — every scenario, growing with
horizon (0.755–0.91×), and glaciers are **40.1% of addressable at ssp126@2100**.

## E. WHAT WAS MADE DURABLE, AND THE SELF-AUDIT IT NEEDED

* `benchmark/comparator_classes.csv` — one line, editable, argued in its own header.
  Only **bamber19** is separated (Bamber et al. 2019 PNAS 116:11195, structured expert
  judgement). ⚠ **Finer lines were considered and NOT drawn**: emuGrIS is an emulator *over*
  ISMIP6, so its width is largely between-model — but that is an inference from the numbers,
  not a fact about the module, and **classifying a comparator to make your own score better
  needs a receipt**.
* Cells with **fewer than 3 comparators** have their verdict **capped at WARN**: a median of
  one or two is not a summary.
* ⚠⚠ **A CLASSIFICATION AUDIT now prints every run.** The exclusion improves scores by up to
  **4.41×** and **five verdicts depend on it** — AIS ssp585@2150 (0.803 PASS vs 0.397 FAIL)
  and four Greenland cells. A classification that flips verdicts must never be silent.

## F. NEXT

1. **Glaciers — the level deficit.** Now the top genuine defect: 0.755–0.91× at every
   scenario and horizon, growing with horizon, in the component that is 40.1% of addressable
   uncertainty at ssp126@2100. Needs the global-cm GloGEM/OGGM target (§ main note).
2. **The ssp126 AIS tipped fraction** (3.95% — right or wrong? a threshold question).
3. **Step 5** with `--adcov=` + the `ais_gmst_amp` refit.
4. **Greenland width** — parked at ~4%, with the measurement on record so it can be picked
   up cheaply if ssp126 becomes a headline reported scenario.

---

# ADDENDUM 3 — 2026-08-25: TE, glaciers, and MAGICC to 2300

Commits **`6c6acd4`** (MAGICC), **`d24cc67`** (TE), **`1e69237`** (glaciers).
**Nothing recalibrated. No MAGICC re-run was needed.**

Marcus: *"Before step 5, I would like to do a quick pass on the TE question and then
glaciers. Also, continue to use MAGICC for sanity tests (though we can't rule out that
MAGICC has serious flaws): can we run MAGICC to 2150 and 2300 ourselves?"*

## A. MAGICC — WE DO NOT NEED TO RUN IT. IT ALWAYS DID.

`slr-refresh/notebooks/302_run-magicc-scenarios-SSPs.py` sets `endyear_run = 2300 + 5`, its
own summary table filters to `year=[2100, 2300]`, and the source CSV carries annual columns
through **2305-01-01**. Only `extract_magicc_components.py` was wrong — `YEARS_OUT =
range(2000, 2101)` with a comment asserting the run ended at 2100. Re-extracted;
`[YEARS-PRESENT]` now **asserts the columns exist** instead of trusting a comment.

That retires every *"NO UPPER COMPARATOR AT THIS HORIZON"* warning at 2150, and step 1's
caveat that the separation ruling *"is a 2100 statement"*.

⚠ **AND MARCUS'S CAVEAT IMMEDIATELY EARNED ITS KEEP.** At 2300 MAGICC-SLR puts ssp585 AIS at
**712 cm** and the total at **1016 cm (10.2 m)**. Scored against that alone we are 0.39× and
look badly low. **Coulon et al. 2025** (Table 1, PMC12680641; two Bayesian-calibrated
ice-sheet models, no MICI) publish 2300 ssp585 AIS medians of **267 and 273 cm**. **Ours is
277.34** — 1.02× the comparator median with all three in, and MAGICC sits above Coulon's own
5–95% upper bound of 595 cm.
* `benchmark/literature_extra.csv` — new extension slot, every row with its citation.
* ⚠ Coulon entered at **ssp585 only**: their two models agree there (267/273) so attribution
  does not matter, but at ssp126 they publish **3 cm and 110 cm** — a 37× disagreement where
  the pairing *does* matter and which this repo records as a nameless tuple. Entering those
  would let the separation block pair models across scenarios on an unverified attribution.
* Bug fixed in the same change: the thin-comparator cap was evaluated on the **median** count
  for both metrics; Coulon supplies a median with no band, which silently un-capped a spread
  comparison still resting on n=1. Now per metric.

## B. TE — THE DRIVER, HALF OF IT DEPTH SCOPE, AND NOT A SEA-LEVEL DEFECT

TE is linear in OHC, so the miss factors exactly:
`rate(TE)/rate(target) = [rate(OHC_FaIR)/rate(OHC_obs)] × [α_model/α_obs]`.

* **NOT the coefficient.** α_model = 0.10574 cm per 10²² J against an obs-implied
  0.1096–0.1140 ⇒ **0.93–0.97×**. It is slightly LOW and **partially offsets** the driver;
  tightening it would make the level fit *worse*.
* **The driver, and 51% of that is depth scope.** FaIR's OHC is **full-depth**; both obs OHC
  products here and the post-2019 steric target are **0–2000 m** (NOAA NCEI). IGCC publishes
  the layer that prices it: over 1993–2024 its **>2000 m layer adds 10.2%** to the trend, and
  FaIR is **1.222× IGCC 0–2000 m but only 1.108× IGCC's own full-depth series**.
* ⚠ **The residual 1.11× is a FaIR question, not a BRICK one** — which is exactly why BRICK
  2.0 misses by the same amount. Nothing in either sea-level model can fix it.
* ⚠ **The correction is an upper bound**: the deep ocean is colder and expands less per
  joule, so the true model/target ratio is between **1.08× and 1.19×** ⇒ **the FAIL survives
  as a WARN at worst.**
* ⚠ **NEW, previously asserted rather than tested.** `prep_recalib_targets_ext.py:30`
  offset-matches Frederikse to NOAA as *"a pure level shift … both measure the same physical
  SLE"*. On their 2005–2018 overlap their **slopes differ by 6.3%** (0.1133 vs 0.1209 cm/yr).
  A level-matched splice does not equalise slopes, so the target changes method/scope at 2019.

## C. GLACIERS — "GROWING WITH HORIZON" WITHDRAWN; MOST OF THE OFFSET IS SCOPE

* **Not growing.** With MAGICC at 2300 the mean ratio runs **0.847 → 0.805 → 0.877** across
  2100/2150/2300. The apparent growth was FACTS-at-2150 vs MAGICC-at-2300 — a comparator
  change between horizons. It is a roughly **constant** level offset.
* **Regional scope, measured.** Ours owns RGI **1–18 minus r5 plus r19** (Marcus 2026-08-06:
  r5 sits in the GIS target). FACTS's AR5 module distributes into a list that **has glac5 and
  has no glac18/glac19**. Over GlaMBIE 2000–2023, **r5 = 13.00%** and **r19 = 6.54%** of
  global loss ⇒ our scope 0.870, AR5 scope 0.935, **scope alone predicts 0.931** against an
  observed 0.843.
* ⇒ **Residual model deficit ~9%, not ~16%.**
* ⚠ **A hypothesis of mine was refuted en route.** If r5 had merely moved from our glaciers to
  our GIS, glaciers+GIS should match the comparators. It does not — the combined ratio is
  **0.52–0.95, worse than glaciers alone** — because GIS carries its own large deficit at
  2150/2300. Scope is a **partial** explanation, not a complete one.
* ⚠ Three named assumptions that would move the number: the AR5 scope comes from a
  **spatial-fingerprint** file its own code comment calls defective (no region 4, region 7
  twice); emuglaciers' and MAGICC `SLR_GL`'s scope are **not established at all**; and the
  shares are observed-era while **r19 depletes last**, so the correction is an
  **under-estimate** at 2150/2300.
* **The cheap decisive test:** get FACTS/MAGICC's glacier region set directly, or re-run our
  own projection **with r5 and without r19** and compare like for like.

## D. WHERE THAT LEAVES THE OPEN LIST

The benchmark's candidate FAIL list is now **TE rate** (→ WARN once scope is credited; a FaIR
question), **Greenland ssp126@2100 spread** (0.489×, worth +3.9% of one band), and
**TOTAL ssp585@2150 spread** (0.365×) — which is new, has 3+ comparators, and has NOT been
looked at. Everything else is PASS or WARN.

**Suggested next:** (1) the TOTAL ssp585@2150 spread, the one unexamined FAIL; (2) the
glacier region-set confirmation, which is a question to FACTS/MAGICC rather than an analysis;
(3) step 5 with `--adcov=` + the `ais_gmst_amp` refit.

---

# ADDENDUM 4 — 2026-08-25: the last unexamined FAIL, and it was the AIS spread in disguise

Commit **`ba99de0`**, `python/diag_total_spread_ssp585_2150.py`. **Nothing recalibrated. No
chain read. No model run.** Addendum 3 §D's item (1) — *"the TOTAL ssp585@2150 spread, the one
unexamined FAIL"*.

## A. THE SUSPICION WAS STATED BEFORE MEASURING, AND IT HELD

A total cannot be **0.365×** the literature while every component of it is **0.46–0.90×**
unless the two are scored against **different comparator sets**. The same cell's AIS scored
0.525 PASS.

Decomposed against each comparator, the share of its total-spread gap from ours that is its
**AIS**-spread gap:

| comparator | their AIS | their TOTAL | ours/theirs | AIS share of the gap |
|---|---|---|---|---|
| wf1f | 48.7 | 77.9 | **1.891** | 85% |
| **wf2f** | 134.3 | 150.6 | **0.979** | — (3.2 cm) |
| wf3f | 408.4 | 414.7 | 0.355 | 112% |
| MAGICC | 276.2 | 403.4 | 0.365 | 66% |

**Against wf2f — the process workflow with no MICI and no expert elicitation — our total
spread is 0.979×.** The total cell carries no information the AIS cell does not.

## B. THE FACTS WORKFLOWS NOW HAVE RECEIPTS

They were opaque module strings with no documented composition anywhere in the repo, and **a
benchmark cannot classify a comparator it cannot name**. Each is now identified by fitting its
total against every (AIS × GIS) combination in the same file, on **three** statistics (sum of
medians; quadrature sum of p05–p95; quadrature sum of **upper** half-widths), voted **per
slot** and only by the statistics that **discriminate** that slot:

`wf1f` = ar5AIS+FittedISMIP · `wf2f` = larmip+FittedISMIP · `wf3f` = **deconto21 (MICI)**
+FittedISMIP · **`wf4` = bamber19 in BOTH ice sheets** (3/3 votes for the first three,
margins 3.1–18.2×).

⚠ **THE FIRST VERSION USED TWO STATISTICS, REJECTED wf4, AND WAS RIGHT TO FIRE.** bamber19's
AIS median (36.5 cm) and larmip's (37.4) differ by **2%** at that cell, so the median test is
**blind** to the slot — not a dissenting vote, *no information*. The **upper half-width**
discriminates 4.9× (517.9 vs 105.0, against wf4's own total upper of 553.6, unreachable by any
larmip composition — wf2f, which *is* larmip, has 105.5).

## C. TWO FIXES, BOTH GENERIC

1. **`wf4` joins `bamber19` as `sej`.** This is the **existing** line applied consistently, not
   a new one: component rows have excluded bamber19 since `bbee082`; total rows never did.
   Worth **1.46×** here, **≤7%** at every other total cell, **one** verdict moves.
   ⚠ **`wf3f` = MICI deliberately STAYS in `model`**, because deconto21 stays in `model` at
   the AIS level. Our gap to it is the already-priced `ais_binary_form_priced` decision.
2. **A median comparator is a summary only if the comparators agree.** Exact, threshold-free:
   score against each comparator alone, cap at **WARN in both directions** where the median's
   verdict is not a majority position. Caps **four** cells, all 2150, all deconto21-driven —
   AIS and TOTAL at ssp245 *and* ssp585. ⚠ **Two are cells where we look good** (ssp245@2150,
   1.23×, PASS → WARN); a supported FAIL survives (Greenland ssp126@2100, 2 of 3 agree).
   `bench_ladrillo.py --selftest` mutation-tests all four directions.
   *Abandoned: a `max/min > 4×` dispersion proxy — same four cells, but 4× was a picked number.*

## D. NET, AND THE OPEN LIST

**`TOTAL ssp585@2150 spread`: FAIL 0.365 → WARN 0.532 — NOT PASS.** TOTAL projection roll-up
FAIL → WARN. ⚠ The classification audit correspondingly **stops** listing AIS and TOTAL
ssp585@2150 as verdict-dependent on the SEJ exclusion: they are WARN either way now.

The candidate FAIL list is down to **TE rate** (a FaIR/OHC-driver question, → WARN once depth
scope is credited) and **Greenland ssp126@2100 spread** (0.489×, worth +3.9% of one band,
parked). **Everything the benchmark flags has now been priced.**

**Suggested next:** (1) the glacier region-set confirmation — a question to FACTS/MAGICC rather
than an analysis, and the cheap decisive alternative is re-running our own projection **with r5
and without r19**; (2) the ssp126 AIS **tipped fraction** (3.95% — right or wrong? a threshold
question needing literature this repo lacks); (3) **step 5** with `--adcov=` + the
`ais_gmst_amp` refit. ⚠ Step-5 cautions in §4 of the main note still stand (`sshare`; do NOT
resurrect the joint FaIR/BRICK calibration).
