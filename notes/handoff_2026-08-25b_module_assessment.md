# Handoff — the 5-step module assessment: STEP 1 DONE, steps 2–5 open

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, commit **`c6c7f50`** (step 1)
on top of **`95cae6a`** (the FaIR-uncertainty arc). Written 2026-08-25 to be picked up cold.
**Continues** `handoff_2026-08-25_fair_uncertainty.md` — read that one's **addendum** first,
because the joint band it establishes is what step 1 scores against.

**NOTHING WAS RECALIBRATED.** Step 1 read no chains; it is post-processing over outputs that
already existed plus one cheap scorecard re-run.

---

## 0. THE TASK

Marcus, 2026-08-25:

> *"Step 1: how good is our AIS module relative to old BRICK and to the literature,
> recognizing that there are irreducible uncertainties. Step 2: Do the same test for
> glaciers. Step 3: Do the same test for Greenland, but with more flexibility because it
> isn't as important for global sea level. Step 4: Do the same test for the sum of all the
> components. Step 5: If the model passes steps 1–4, then redo the calibration test with the
> new model. Use torch if necessary."*

Then: *"Do step 1 and then a handoff. BRICK2.0 should be considered 'old brick'."*

**`old BRICK` = BRICK 2.0** = stock MimiBRICK v2.0.0 with its **own published posterior**
(`parameters_subsample_brick.csv`). NOT `brick-v1.2-vehicle`.

**The five steps map onto Marcus's OWN acceptance criteria (2026-08-14)**, recorded in
`scope_ladrillo_vs_brick20_scorecard.py`'s header: (1) formulation at least as credible as
BRICK 2.0's, (2) hindcast at least as good, (3) projection spread at least as good
(FACTS/MAGICC match, or more physical), (4) the same under the joint calibration.
**Step 5 IS criterion (4).** Score every module on the same four.

---

## 1. STEP 1 — DONE. THE AIS VERDICT

`python/scope_ais_module_assessment.py` → `outputs/scope_ais_module_assessment_L14.csv`.

### (1) FORMULATION — **PASS BY IDENTITY**, and this reframes everything

**Ladrillo's AIS component IS BRICK 2.0's.** `replace!` is applied only to the GLACIER and
GREENLAND slots (`brick_mengel.jl:57,117,173,238,267`); **the AIS slot is never replaced**, so
the shipped model runs stock MimiBRICK v2.0.0 `antarctic_icesheet_component.jl` out of the
depot, unmodified. Ladrillo changes the **posterior** plus two per-draw reparameterisations in
`ladrillo_apply_draw!`:

    ais_runoffline_snowheight0  = -ais_runoff_Ton * ais_c        (sampled along T_on)
    ais_temperature_coefficient = 1/amp,  intercept = -TANT0/amp (anchor-preserving)

⇒ **the question is never "is our module better", only "is our CALIBRATION better".**
⚠ Check this for steps 2–3 before writing a word: glaciers and Greenland **are** replaced, so
they are genuinely different formulations and criterion (1) is a real question there.

### (2) HINDCAST — **NOT DECIDABLE**

RMSE ratio Ladrillo/BRICK 2.0: **0.03× full**, 0.01× 1950–1992, 0.55× 1993–2026. Ignore it:

* **in-sample for Ladrillo, out-of-sample for BRICK 2.0** — BRICK runs its published posterior
  and was never recalibrated on `recalib_targets_ext.csv`. The script's own header says so.
* **the data have no power.** IMBIE whole-sheet loss is **0.95–1.44 σ from zero** across four
  windows, EAIS is 0.02–0.25 σ, on a target spanning **1.404 cm**.
  **A hindcast that cannot reject zero cannot rank two models.**

### (3) PROJECTION — **over-separated, and under-dispersed at ssp126**

⚠ Scored on the **JOINT** band, because FACTS/MAGICC carry climate uncertainty and ours did
not until 2026-08-25. Using the fixed band here would be `like_for_like_forcing` again.

| AIS, vs the literature median | @2100 | @2150 |
|---|---|---|
| ssp126 median | 0.48× | 0.31× |
| ssp245 median | 0.51× | 0.42× |
| ssp585 median | **2.16×** | **2.49×** |
| **ssp585/ssp126 SEPARATION** | **8.17× vs lit 1.98×** | **14.12× vs lit 1.90×** |
| ssp126 spread | **0.33×** | **0.24×** |
| ssp245 / ssp585 spread | 1.09× / 1.12× | 0.66× / 0.40× |

**Six ratios, one defect: the scenario separation is 4.1×–7.4× too wide.** And at ssp126 the
band has **no tipping tail at all** — the fast-dynamics term is *exactly* 0.000 cm in every
arm and horizon — while every literature module keeps one.

**This RECONCILES with `ais_binary_form_priced`, it does not contradict it.** A step function
**compresses** separation between two scenarios that both tip (fast-dyn ssp585/ssp245 = 1.87
at n=0 vs 47.9 at n=1) and **exaggerates** it across the threshold (ssp126→ssp585 8.17× vs
1.98×). Same defect, both signs.

⚠⚠ **CAVEAT ON THE COMPARATOR — this does NOT by itself convict us.** MAGICC-SLR, the other
**emulator**, separates *more* than we do (**10.69×** @2100). The weak-separation cluster is
the process-model/FACTS side: ar5AIS **0.63×** (sign INVERTED — an AR5 SMB-gain artefact),
emuAIS 0.98×, larmip 1.21×, bamber19 1.98×, deconto21 3.20×. **"Emulators separate more than
process models" is a live alternative reading.** Quote the comparator, never just the median.

### (4) IRREDUCIBLE

**78%** of the ssp585 2300 band is `antarctic_lambda`, whose posterior sits **0.027 prior sd**
from its paleo prior and which is identified by the **LIG alone** (three of Ruckert's four
constraints are exactly inert). ⇒ **the ssp585 WIDTH must NOT be narrowed — a tighter band
would be a worse model.** **The ssp126 width is the real defect, and it is MODEL-FORM, not data.**

### STEP-1 BOTTOM LINE

As credible as BRICK 2.0 **by construction**; better calibrated on a hindcast that **cannot
arbitrate**; and against the literature **over-separated across scenarios and under-dispersed
at ssp126**, both tracing to the binary fast-dynamics threshold. **It does not cleanly "pass"
criterion (3)** — which matters, because step 5 is conditional on steps 1–4 passing.

---

## 2. STEPS 2–5 — WHAT TO DO, AND WHAT ALREADY EXISTS

### Reusable instruments (all present, all cheap)

| what | file | state |
|---|---|---|
| hindcast vs BRICK 2.0, per module | `python/scope_ladrillo_vs_brick20_scorecard.py --tag=L14` | **run at L14**, `outputs/scope_ladrillo_vs_brick20_scorecard_L14.csv` |
| projection vs FACTS/MAGICC | `outputs/ladrillo_model_comparison_L14{,_spread}.csv` | exists; `source` ∈ {Ladrillo, BRICK 2.0, FACTS, MAGICC-SLR} |
| joint-band per-draw values | `outputs/scope_slr_fairunc_draws_<ssp>_spliced_L14.csv` | all 3 SSPs, horizons 2100/2150/2300 |
| the step-1 template | `python/scope_ais_module_assessment.py` | **copy this for steps 2–4** |

### STEP 2 — glaciers
* ⚠ **Criterion (1) is a REAL question here**: the glacier slot IS replaced
  (`glaciers_nu3`), so we are NOT running BRICK 2.0's WR-GSIC. Formulation must be argued.
* Hindcast is already computed: RMSE **0.37× full**, but **1.01× (WORSE) over 1950–1992** —
  the only window where BRICK 2.0 beats us on any module. **Explain that before anything else.**
* Between-scenario spread @2100: ours **6.37** vs BRICK 2.0 **4.47**, MAGICC 4.85,
  FACTS ar5glaciers 6.52 / emuglaciers 8.48 ⇒ we sit **inside** the FACTS range.
* ⚠ **The literature targets do NOT exist in this repo.** GlacierMIP / Rounce 2023 /
  Marzeion have never been assembled. **This is the real work of step 2.**
* Priority context: glaciers are **40.1% of ADDRESSABLE uncertainty at ssp126@2100**, the
  top contributor there ([[addressable_not_band_growth]]) — so step 2 is not a formality.

### STEP 3 — Greenland ("with more flexibility")
* **Greenland is CLOSED as a module** (2026-08-24) and has by far the most literature work
  already done: ISMIP6 (16 ISMs), PROTECT, Greve/SICOPOLIS, CLIMBER-X, `python/gis_targets.py`
  (`--targets=lit|matched`), `diag_gis_obs_scorecard.py`. **Assemble, do not re-derive.**
* Known standing results: hindcast beats BRICK 2.0 on shape/level/acceleration but **not** the
  1995–2024 rate (0.95× vs our 1.06×) and **not** the melt-rate band; 2100 runs **1.31–1.32×
  fast** and that bias is the **amp law**, hindcast-inert ⇒ prior-propagatable.
* Marcus's "more flexibility" = Greenland is **6.0% of the ssp585@2300 joint band** and
  **8.8% of addressable**. Do not spend step-3 effort proportional to step-1's.

### STEP 4 — the sum
* `total` rows already exist in every instrument. Hindcast RMSE **0.38× full**, **0.96×**
  1993–2026. Between-scenario spread @2100: ours **59.62** vs MAGICC **62.26** and FACTS
  workflows **25.15–50.69** ⇒ we are above every FACTS workflow, close to MAGICC.
* ⚠ **The total is NOT the sum of four independent verdicts** — `[SUM]` shows the components
  sum to the total per draw, but the covariance residual is **+18% to +34%**, so a total-level
  pass can hide compensating component errors and vice versa. Score it on its own.

### STEP 5 — the calibration test (conditional)
* = Marcus's criterion (4). **Only if 1–4 pass**, and **step 1 does not cleanly pass (3)**, so
  raise that before burning a Torch allocation.
* ⚠ **Do NOT resurrect the joint FaIR/BRICK calibration.** It is banner-marked REJECTED
  (`notes/negresult_2026-08-01_joint_forcing_calibration.md`); Marcus's 2026-08-01 directive
  is *propagate forcing forward, never re-calibrate it against SLR*.
* The canonical calibrator is `julia/calibrate_mcmc_ext.jl` (★ CANONICAL, mean forcing).
  Torch: `nyu_hpc` memory, `torch_pr_1041_general`, partition `cpu_short`, `slurm/` has
  templates. ⚠ **fairshare was 0.28 on 2026-08-01** — check `sshare` before submitting.
* ⚠ **`ais_iceflow0` R-hat 2.244 and 9 of 17 AIS params fail** at L14; the PROJECTION
  converges (11/12 cells) but parameter-level inference does not. A recalibration must
  carry a fresh certificate, and the **pooled-proposal lever (`--adcov=`) should go in first**
  — 4 RAM proposals disagree 347× in shape while every acceptance rate sits on 0.234.

---

## 3. NON-OBVIOUS STATE / TRAPS

* ⚠ **The hindcast comparison is in-sample for Ladrillo everywhere, not just AIS.** Every
  RMSE ratio in the scorecard carries it. Say so in every module's write-up.
* ⚠ **Score projections on the JOINT band, never the fixed one** — FACTS/MAGICC carry climate
  uncertainty. The fixed band understates our ssp126 AIS spread by **3.4×**.
* ⚠ **`ladrillo_model_comparison_L14.csv` has no BRICK 2.0 rows for AIS/GIS/TE** — only
  glaciers. BRICK 2.0's projection arm is incomplete; do not report a blank as a zero.
* ⚠ FACTS `ar5AIS` has **inverted** scenario sign (ssp585 < ssp126) from AR5's SMB gain. It is
  a legitimate member but it drags the median; report the range, not just the median.
* ⚠ A `pgrep -f "<script>.jl"` wait-loop **matches its own shell**. Match on PID.
* ⚠ `git add -A outputs/` sweeps in **227 deliberately-untracked** mcmc artifacts. Stage by name.
* ⚠ **Never `git checkout <file>` on a dirty file** — it destroyed 17 uncommitted lines of
  `FaIRtoFrEDI/CLAUDE.md` this session (restored from context, verified at `17 insertions(+)`).

---

## 4. FILES AND COMMITS

**New:** `python/scope_ais_module_assessment.py`,
`outputs/scope_ais_module_assessment_L14.csv`,
`outputs/scope_ladrillo_vs_brick20_scorecard_L14.csv`, this note.
**Memories:** `ais_is_brick20_overseparated` (new); `INDEX_slr.md` +1 line.
**Commits:** `c6c7f50`, plus the earlier `2ba0893` / `a00ed46` / `95cae6a` arc.
