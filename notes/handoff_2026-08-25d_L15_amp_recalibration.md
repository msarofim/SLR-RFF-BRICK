# Handoff — L15: the amp correction is RIGHT IN DIRECTION AND TOO LARGE. Next step: FREE THE DAIS ANCHOR

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, head **`efc0056`**. Written
2026-08-25 to be picked up cold. **Continues** `handoff_2026-08-25c_benchmark_and_steps234.md`
(read its **ADDENDUM 8** first — it contains a retraction that this note depends on).

**L14 REMAINS CHAMPION. L15 IS COMMITTED AS AN ARM AND WAS NOT PROMOTED.** Nothing downstream
has moved. `champions.json` is untouched.

---

## 0. THE TASK, AND HOW IT CHANGED UNDER US

Marcus, 2026-08-25: *"Do the amp(ΔT) improvement. After that, do all the free fixes that will
go with the new calibration."*

**⚠ amp(ΔT) WAS NOT BUILT, AND MUST NOT BE.** The measurement that motivated it was refuted
before implementation — see §1. What was built instead, on Marcus's redirect, was a
**re-centring of the constant** plus the free fixes. It ran, and it made the benchmark
**worse**. §3 is the result; §4 is the next step Marcus has chosen.

---

## 1. ⚠⚠ THE RETRACTION THAT STARTED THIS — read before trusting any amp number

`handoff -25c` **ADDENDUM 7** asserted, citing memory `pai_cmip6_time`, that Antarctic
amplification **RISES** with warming level (~0.85 at 0.6–0.8 K → ~1.15–1.20 at 2–4 K) and that
the fix was therefore a state-dependent `amp(ΔT)`.

**That memory describes a SUPERSEDED diagnostic.** Two commits on 2026-08-24 replaced it:

* `a79d532` — *"Switch scenario diagnostic to SECANT ratio; correct a to ~1.08"*
* `9de38bf` — *"data/cmip6_pai was corrupt for SEVEN files, not two — and the numerator was
  wrong too"* (xarray `.weighted()` inner-join on float-noise latitudes cut MPI-ESM1-2-LR to
  56 of 96 latitudes; the AIS numerator inherited it)

BRICK's `amp` multiplies a **LEVEL** anomaly, so the BRICK-relevant statistic is the **SECANT**
ratio, not Xie's sliding-window **TREND** ratio (PAI1). `diag_pai_cmip6_time.py`'s own header
states the supersession. **The two behave oppositely with warming.**

**Measured on the corrected data** (`python/scope_ais_amp_law_form.py`, 34 models, land-frame,
ΔT ≥ 1.0 K):

| | slope of secant on ΔT | z | worth over 1–4 K |
|---|---|---|---|
| ssp245 | −0.0065 /K | −0.59 | −0.019 |
| ssp585 | +0.0091 /K | +1.43 | +0.027 |

**Neither resolves, they disagree in SIGN, and each is worth 6–9× less than the between-model
sd of 0.180.** ⇒ a constant is the right FORM. Addendum 7's `amp(ΔT)` would have encoded a
trend of the **wrong sign**. Do not rebuild it without re-running that test.

---

## 2. WHAT L15 IS — four changes, bundled by decision

Marcus chose: re-centre the constant, **keep σ = 0.10**, bundle the target-builder fixes and
`--adcov=`. **Attribution was named as the cost of bundling going in, and §3 is where that
bill comes due.**

1. **A6 amp prior 0.95 → 1.09** (`calibrate_mcmc_ext.jl`). The only change with a large
   predicted effect. Two independent ensembles: 34-model SSP secant **1.095** (sd 0.180),
   41-model **DECK 1pctCO2** secant **1.097** (1.087–1.153). Bounds → μ±3σ = **[0.79, 1.39]**
   (the old [0.70, 1.25] was built around μ=0.95 and would clip the new prior at +1.6σ);
   `θ0` starts at the prior centre instead of the old fixed map 1.196.
2. **LWS 2019–2023 = real GRACE/GRACE-FO** (`prep_recalib_targets_ext.py` now reads
   `build_lws_grace_extension.py`'s output). Max change 0.123 cm. ⚠ Its **band width** is
   still the 2018 half-width — a real centre with a held bar. Smaller fiat, still flagged.
3. **`dang_closure_sig` trend-extended** past the ensemble instead of held flat. The hold was
   measurably anti-conservative (+0.0216 cm/yr over 2009–2018, **z = +6.08**). 0.775 → 0.926
   cm by 2026. Gated: the realised residual stays at **0.69×** the held value, so this is
   insurance, not a repair.
4. **Pooled proposal** (`python/build_pooled_adapted_cov.py`, NEW → `--adcov=`). ⚠ The
   marginal view would have said pooling was unnecessary (per-parameter sds disagree only
   **2.4×**); the real disagreement is the generalized-eigenvalue spread between seed pairs,
   **44–427× raw and 532–3398× standardized**. Standardizing makes it LARGER, which
   **qualifies** `acceptance_rate_certifies_nothing`'s "standardize first" — that is advice
   about misreading the leading eigenvector, not a claim the raw spread is inflated.

**Run:** `bash run_mcmc_L15.sh 2000000` — 4 chains × 2M, seeds 2026–2029, BLAS pinned.
**~4h20m wall**, which is **1.9× the 2h17m `pin_blas_threads` records**; cause not
established, flagged rather than explained away. Accept 0.237 on all four.

---

## 3. THE RESULT — the prediction PASSED and the benchmark got WORSE

### 3a. The falsifiable prediction passed, cleanly

Predicted ssp245@2100 tipped fraction 33.1% → ~60% at amp 1.13; at the adopted 1.09 the
pure-threshold interpolation is ~53.2%. **Realised 53.8%** — within 0.6 pp. ⇒ the threshold
channel accounts for essentially the whole move and the **smooth channel absorbed nothing**.

Projections move exactly where the mechanism says (fixed-driver medians, L15/L14):

| | AIS @2100 | @2150 | @2300 | TOTAL @2300 |
|---|---|---|---|---|
| ssp126 | 1.27× | 1.29× | 1.29× | 1.06× |
| **ssp245** | **3.28×** | **5.54×** | **1.62×** | **1.37×** |
| ssp585 | 1.35× | 1.25× | 1.24× | 1.13× |

### 3b. Convergence: better where it was worst, at a price

**Marginals 20 failing → 18** (like-for-like, same script, 4×2M, 1M post-burn):
`ais_iceflow0` **2.244 → 1.665**, `antarctic_alpha` 1.777 → 1.438, `ais_slope` 1.750 → 1.313,
`rho_ais` 1.257 → 1.022. Cost: `ais_runoff_Ton` 1.092 → **1.908**.

**Deliverable gate PASSES** — SLR R-hat **1.002** at 2100 and 2150 (L14: 1.017 / 1.015).
⚠ **But R-hat is a ratio and a wider band forgives** (`rhat_denominator_forgives`):

| | chain medians apart (cm) | within-chain sd (cm) | scale-free ratio |
|---|---|---|---|
| @2100 | 0.603 → **1.576** | 11.80 → 18.37 | 0.051 → **0.086** |
| @2150 | 3.053 → **1.025** | 32.35 → 38.49 | 0.094 → **0.027** |

**At 2100 the R-hat gain is DENOMINATOR-DRIVEN** — the chains are 2.6× further apart in cm and
the scale-free measure is WORSE. At 2150 it is real on both counts. Do not quote "converges
better than L14" without this split.

### 3c. ⚠ THE BENCHMARK SAYS L15 IS WORSE: 4 improved, 10 degraded, 164 unchanged

**Improved — the known cool-scenario level deficit:**
TOTAL ssp126@2150 median WARN → **PASS**; TOTAL ssp245@2100 median WARN → **PASS**;
glaciers accel WARN → UNRESOLVED.

**Broke — AIS overshoots, and it passed THROUGH the target on the way:**

| cell | L14 | L15 | |
|---|---|---|---|
| ais ssp245@2150 median | 0.406× | **2.048×** | PASS → **FAIL** |
| ais ssp245@2300 median | **0.949×** | 2.239× | L14 was near-perfect |
| ais ssp585@2100 median | 2.430× | **3.343×** | PASS → **FAIL** |
| ais ssp126@2100 spread | N/A(bimodal) | **2.381×** | now too **WIDE** |
| [V] AIS projection | WARN | **FAIL** | |
| [V] AIS vs champion (hindcast) | — | **WORSE** | mean RMSE ratio **4.884** |

**And the AIS hindcast degraded sharply:** RMSE **1.5–9.2× worse** by window; 90% coverage over
1950–1992 collapses **98% → 7%**; bias +0.02 sd → **−0.34 sd**. It still reads "PASS" only
because the AIS target's own sigma is generous — **the roll-up hides this; read the coverage.**

### 3d. ⚠ A RED HERRING, RULED OUT — do not re-chase it

`ais_runoff_Ton` goes **bimodal** (sd 0.092 → 2.655, **29×**; 23% of the subsample in a second
mode at ≈ −13.9 against a main mode at ≈ −19.5). **It is NOT the cause.** It is a
**reparameterized, NON-IDENTIFIED coordinate** (`calibrate_mcmc_ext.jl:1364`, *"reconstruct h0
from the identified direction"*), and the **identified** combination `h0 = −T_on·c` is well
behaved in BOTH modes (**1797 m** and **1416 m**, both inside L14's own p05–p95 of
1054–2170 m). The sampler is exploring a degenerate direction — which is what the pooled
proposal was *for*. Judge this parameter on `h0`, never on `ais_runoff_Ton`.

### 3e. ⇒ THE DIAGNOSIS

**The measurement and the model's historical fit are in tension.** Two independent CMIP6
ensembles put the secant at ~1.09. The model fitted 0.945 and its historical AIS matched
observations well. Forcing 1.09 breaks the hindcast and overshoots every AIS projection.

⚠ **This was foreseen and then dropped.** Addendum 7 said re-centring *"buys the ssp245
projection by mis-fitting the history that the same parameter is pinned by."* When the
**state-dependence** was refuted, that **separate** concern about the **historical fit** was
let go with it. It was the operative one. Cost: one 4-hour chain.

⚠ **ATTRIBUTION IS NOT CLEAN.** Four things changed at once, by decision. The amp delta is
attributable (it is the only change with a large predicted effect, and §3a confirms its
mechanism quantitatively). A **convergence** or **hindcast** change could come from amp, from
the pooled proposal, or from the widened closure sigma loosening the total constraint. **No
single-change arm was run.**

---

## 4. THE NEXT STEP — FREE THE DAIS ANCHOR (Marcus, 2026-08-25)

### 4a. What is currently pinned, and why that is the suspect

DAIS computes (`antarctic_icesheet_component.jl:165`):

    T_ant[t] = (GMST[t-1] − ais_temperature_intercept) / ais_temperature_coefficient

Stock: `coef 0.8365, intercept 15.42` — the inverted paleo **equilibrium regression**, which
fitted the **pair jointly**. The A6 reparameterization samples `amp` with
`coef = 1/amp`, `intercept = −T_ant0/amp`, holding **T_ant0 = −18.434 °C PINNED**. So we have
been moving the **slope** of a jointly-fitted pair while nailing its **intercept**.

### 4b. ⇒ THE ARITHMETIC THAT MAKES THIS THE RIGHT NEXT MOVE

`T_ant = amp·GMST + T_ant0`, so raising amp shifts T_ant by `ΔGMST × Δamp` — and the
calibration and the projections sit at very different GMST:

| | GMST | T_ant(0.945) | T_ant(1.090) | shift |
|---|---|---|---|---|
| calibration 1900–2024 | 0.41 K | −18.044 | −17.985 | **+0.060** |
| SMB anchor 1979–2008 | 0.65 K | −17.823 | −17.729 | **+0.094** |
| ssp245 @2100 | 2.75 K | −15.835 | −15.436 | +0.399 |
| ssp245 @2150 | 3.00 K | −15.599 | −15.164 | +0.435 |
| ssp585 @2100 | 4.70 K | −13.993 | −13.311 | +0.682 |

**A T_ant0 shift of −0.077 K restores the HISTORICAL T_ant almost exactly while leaving the
projection shift at +0.19 to +0.61 K — keeping ~83% of the projection effect and removing
~all of the hindcast damage.** On the tipping channel, crossing GMST goes
**3.005 K** (L14) → **2.605 K** (L15, pinned) → **2.675 K** (anchor freed by −0.077).

⚠ **FIRST-ORDER ONLY.** T_ant enters precipitation as `exp(κ·T_ant)` and the runoff line as
`h0 + c·T_ant`, so equal T_ant does not guarantee equal mass balance once the other parameters
re-fit. **It is the leading term, not a proof** — which is exactly why it is worth a run.

### 4c. ⚠ THE DESIGN PROBLEM TO SOLVE BEFORE CODING IT

**T_ant0 is PARTIALLY DEGENERATE with `antarctic_temp_threshold`, which is already free.**
T_ant enters three channels:

| channel | form | does T_ant0 identify? |
|---|---|---|
| fast dynamics | `T_ant > temperature_threshold` | **NO** — only the DIFFERENCE matters |
| precipitation | `exp(ais_precipitation₀) · exp(κ·T_ant)` | **YES** — absolute level |
| runoff line | `h0 + ais_c · T_ant` | **YES** — absolute level |

So freeing T_ant0 is coherent — the smooth channels identify it — but it creates a flat
direction against `antarctic_temp_threshold` in the tipping channel. **Decide the handling
before running**, and flag it: pin the difference, use a joint prior, or sample the
(coef, intercept) pair in its original regression coordinates.
⚠ And note `antarctic_temp_threshold` is itself observationally unidentified over the
historical window (0.00% of draws cross it in 1850–2024, `ais_lambda_rests_on_lig`), so this
degeneracy is between one prior-driven parameter and one weakly-identified one.

### 4d. RUN IT AS A SINGLE-CHANGE ARM

**Do not bundle again.** L15's lesson is in §3e. The anchor arm should move **only** the
anchor, on top of L15's targets and proposal, so its delta is attributable. Everything else in
L15 stays put.

### 4e. THE HONEST ALTERNATIVE, KEPT ON THE TABLE

Freeing the anchor may not be the answer. The other reading is that the **CMIP6 secant and
DAIS's `a` are still not the same object** — which would be the **THIRD** frame problem on
this one parameter (Xie's polar-cap-vs-land mask; trend-vs-secant; now
paleo-equilibrium-pair-vs-CMIP6-transient). If the anchor arm also breaks the hindcast, that
is the conclusion, and the action is to **stop overwriting DAIS's paleo pair with a CMIP6
number** rather than to keep looking for a coordinate that makes it fit.

---

## 5. FILES, AND NON-OBVIOUS STATE

**New this session:** `python/scope_ais_amp_price.py`, `python/scope_ais_amp_law_form.py`,
`python/build_pooled_adapted_cov.py`, `python/scope_gsic_region_matched.py`,
`python/scope_gis_ssp126_acceptability.py`, `python/diag_te_rate_bars_and_seam.py`,
`python/diag_total_spread_ssp585_2150.py`, `julia/diag_gsic_scope_matched.jl`,
`run_mcmc_L15.sh`.
**Modified:** `python/prep_recalib_targets_ext.py`, `julia/calibrate_mcmc_ext.jl`,
`python/bench_ladrillo.py`, `python/diag_gis_width_anatomy.py`,
`benchmark/{README.md,comparator_classes.csv}`.
**L15 artifacts:** `data/MimiBRICK/parameters_subsample_brick_mengel_L15.csv`,
`outputs/mcmc/chain_L15_seed*.csv` (9.3 GB, gitignored),
`outputs/{bench_ladrillo_L15,ladrillo_model_comparison_L15,ssps_components_2300_L15*}.csv`,
`outputs/scope_slr_fairunc_draws_*_spliced_L15.csv`, `outputs/postpred_L15_*.csv`.

⚠ **`ssps_components_2300_<TAG>.csv` (the `--no-tap` BASE arm) is a REQUIRED INPUT, not an
optional deliverable.** `scope_slr_fair_uncertainty.jl`'s `[CONTROL]` gate reads it and all
three SSPs died on its absence. Run the projection driver **twice** — default and `--no-tap`.
⚠ **The joint draws are on the UNTAPPED arm** (the `[CONTROL]` gate compares against the base
file), which is what L14 used too — so the benchmark comparison is like-for-like.
⚠ **`recalib_targets_ext.csv` MOVED.** Every diagnostic reading it is stale; re-run rather than
trusting a committed output. The pre-change copy is NOT preserved in the repo — `git show
893bfaa^:outputs/recalib_targets_ext.csv` recovers it.
⚠ **The benchmark's frozen comparators are unaffected** — nothing about BRICK 2.0, FACTS or
MAGICC changed. Do NOT re-freeze.
⚠ **`git add -A outputs/` sweeps in ~227 deliberately-untracked mcmc artifacts.** Stage by name.
⚠ **Check `sshare` before any submitted run** — fairshare was 0.28 on 2026-08-01.

---

## 6. WHAT ELSE THIS SESSION SETTLED (all pre-L15, all still standing)

* **TOTAL ssp585@2150 spread FAIL → WARN.** It was the AIS spread scored against a comparator
  set the AIS cell itself excludes half of. `wf4` identified from the data as **bamber19 in
  both ice sheets** → joins the `sej` class. New **majority rule**: a median comparator is a
  summary only if the comparators agree.
* **TE rate: two claims withdrawn.** The 2019 seam warning is retracted (Frederikse/NOAA
  0.945 ± 0.120, z = −0.46) and the splice is moot by a second route (segments differ at
  z = −0.92). The defect dissolves **in OHC space only** (FaIR/IGCC full-depth 1.108,
  z = +1.48 UNRESOLVED); on the sea-level metric "survives as a WARN at worst" is an **EDGE
  case** (WARN only at c ≥ 1.1004 against a ceiling of 1.1022).
* **Greenland ssp126@2100 spread: ACCEPTED**, criteria fixed in source before the numbers
  (51% upper vs a 60% bar; +0.8% on the reported total p95 vs a 5% bar). The earlier park
  decision had been taken on the wrong number (0.563× vs the benchmark's 0.489×); the anatomy
  now reads the shared classification file.
* **Glaciers: scope does NOT explain the level deficit.** The scope-free test (glaciers + GIS,
  r19 removed, r5 present exactly once on both sides) gives **0.87 at 2100** — ~13%
  unexplained. And addendum 3's r19 flag had its **consequence backwards**.
* **The stopping rule is measurable.** BRICK 2.0's projection medians are now scored:
  **30 BETTER / 11 SAME / 6 WORSE(unearned) / 7 WORSE**, and **every** total-level loss is
  **CANCELLATION** (L14's summed component error is smaller at all nine cells).
