# Handoff — THE DAIS-ANCHOR REPAIR IS REFUTED. §4e is the surviving reading.

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`. Written 2026-08-25 to be picked
up cold. **Continues** `handoff_2026-08-25d_L15_amp_recalibration.md`, whose §4 named the
next step this note closes. Read `-25d` §3e and §4b before §2 below.

**L14 REMAINS CHAMPION. L15 REMAINS AN UNPROMOTED ARM. `champions.json` untouched.**
Nothing downstream moved. **No chain was run** — total compute for this session is ~15 minutes.

---

## 1. WHAT WAS ASKED, AND WHAT CAME BACK

`-25d` §4: *free the DAIS anchor*, as a single-change arm, after answering §4c's degeneracy
question. **The arm was not built, because it was refuted first, on its own terms.** Two cheap
measurements did it. Both are committed and both carry a passing control.

⚠ **This is the same shape of mistake as L15 itself** (`-25d` §3e: a separate concern was let
go along with the one that was refuted). §4b flagged itself as first-order and was run anyway.
It is not first-order — it is the **wrong order of the expansion**. See §3.

---

## 2. THE TWO TESTS

### 2a. `julia/scope_ais_anchor_offline.jl` — does the shift repair the hindcast? **NO**

L15's posterior HELD FIXED, only the anchor moved, 2000 draws, scored with
**`bench_ladrillo.py`'s own block [H] metric**. ⚠ Reproduction check first: this
re-implementation returns L14 **+0.023 sd / 98%** and L15 **−0.340 sd / 7%** on 1950–1992 —
the committed benchmark's numbers to three decimals. The metric is the benchmark's.

| anchor shift | bias/sd [full] | rmse [full] | **band [full]** | cov90 | bias/sd [50–92] | **band [50–92]** | cov90 |
|---|---|---|---|---|---|---|---|
| L14 champion | −0.015 | 0.029 | 0.105 | 86% | +0.023 | 0.081 | 98% |
| L15 pinned | −0.139 | 0.070 | 0.139 | 49% | −0.340 | 0.082 | 7% |
| **L15 −0.077** (§4b) | **−0.262** | 0.072 | 0.223 | 69% | **−0.418** | 0.151 | 53% |
| L15 −0.160 | −0.402 | 0.086 | 0.364 | 90% | −0.507 | 0.251 | 100% |
| L15 −0.300 | −0.605 | 0.119 | 0.626 | 97% | −0.658 | 0.426 | 100% |

**Bias and RMSE degrade MONOTONICALLY at every shift.** Coverage rises 7% → 100% and that is
**band inflation, not fit**: the band widens **5.2×** (0.082 → 0.426 cm) over the same sweep
while the median walks away from the observations. ⚠ `rhat_denominator_forgives`, in the
hindcast block this time — which is why the script now prints the band beside every coverage.

Projection retention at −0.077: **0.89–0.90** at ssp245@2150/2300 and **0.64** at ssp245@2100.
§4b's ~83% was about right for the far horizons. The trade it priced was real; there is
nothing to trade it for.

### 2b. `julia/scope_ais_anchor_identification.jl` — would a refit choose −0.077? **NO, it wants 0**

Conditional log-likelihood profile in the anchor, per draw, reconstructed from
`calibrate_mcmc_ext.jl`: the AIS AR(1) term + the A5 SMB anchor, which are the **only two**
anchor-dependent terms under D1. ⚠ The script ASSERTS D1 rather than assuming it — a posterior
carrying `sd_dang` is refused, because then a third anchor-dependent term exists. 200 draws.

| arm | amp med | peak p05 | **peak p50** | peak p95 | se p50 | Δll at −0.08 |
|---|---|---|---|---|---|---|
| **L14 (CONTROL)** | 0.957 | −0.061 | **+0.001** | +0.053 | 0.016 | −4.77 |
| L15 | 1.085 | −0.157 | **−0.001** | +0.123 | 0.052 | −0.88 |

The control PASSES (`no_power_null`): L14, whose hindcast already fits, peaks at zero. L15
peaks at zero too. **A freed anchor would sit where it already is.**

⚠ **ONE HYPOTHESIS WITHDRAWN.** Mid-session I expected an SMB-vs-sea-level tug-of-war holding
the anchor at zero. Decomposed, there isn't one: the AIS **sea-level series alone** peaks at
−0.003, and the SMB term is so flat that only **50 of 200** draws have an interior peak in it.

---

## 3. ⇒ THE ONE-LINE DIAGNOSIS: A TRANSLATION CANNOT CANCEL A TILT

`amp` multiplies GMST(t); `T_ant0` adds a constant. Over 1900–2025 GMST runs +0.043 → +1.385 K,
so Δamp = 0.145 imposes a **tilt of 0.208 K across the calibration window**, mean **+0.057 K**
(§4b's +0.060 — its arithmetic on the MEAN is correct). The best possible constant anchor shift
removes only that mean, leaving a **residual ramp −0.064 → +0.144 K, rms 0.055 K**.

And the mean was **already absorbed by the refit** — that is what `amp`'s r = 0.608 with
`ais_runoff_Ton` is. So shifting the anchor now REMOVES a compensation that is already in
place. That is precisely the monotone degradation of §2a, and it is why the sign came out
opposite to §4b's prediction.

---

## 4. §4e, MEASURED — and it is the surviving reading

Same profiler, `--axis=amp` (the A6 pair moved TOGETHER, anchor preserved — moving the
coefficient alone would profile neither axis). Conditionally **every draw's own amp is locally
optimal**: L14 +0.002, L15 −0.004. That is the signature of an exactly-compensated direction
and it is the mechanism behind "the amp marginal is a prior sample" (`scope_ais_amp_price`).

The information is in the **ASYMMETRY**:

* L14 draws → L15's amp: **−4.81** log units (median), ≈ 3.1σ on one parameter.
  **The historical record RESISTS 1.09.**
* L15 draws → L14's amp: **−0.73** log units. Re-tuned around 1.09, it is nearly indifferent
  to going back.

⇒ `-25d` §4e is the reading that survives: **the CMIP6 secant and DAIS's paleo pair are not
the same object**, and the fit pays ~5 log units to be told they are. THIRD frame problem on
this one parameter (polar-cap-vs-land mask; trend-vs-secant; paleo-pair-vs-CMIP6-transient).

⚠ **AND KEEP THE BASE UNDER THE RATIOS** (`ratio_needs_its_base`). The AIS target's sigma is
**0.167 cm**. L15's "sharp" degradation is RMSE 0.029 → 0.070 cm on a bias of 0.023 cm. The
ratios (1.5–9.2×; 98% → 7%) are real and they sit on a base of hundredths of a centimetre.

---

## 5. THE DECISION — MADE, AND L16 IS IN FLIGHT

**Marcus chose option 2 (2026-08-25): widen amp σ 0.10 → 0.180, centre held at 1.09.**
`run_mcmc_L16.sh` (commit `d9aaff6`) was written and **LAUNCHED** — 4 chains × 2M, seeds
2026–2029, BLAS pinned, ~4-7h. Acceptance at launch 0.225–0.237 on all four, against the RAM
target 0.234.

**It needs no source change.** `--amp-sigma=` already exists and its bounds branch is μ±3σ, so
[0.79, 1.39] → **[0.55, 1.63]** follows the file's own rule. Verified by smoke run:
`A6 prior: amp ~ N(1.090, 0.180) on [0.550, 1.630]`. ⚠ Also verified that the widened bounds
touch **only** the `ais_gmst_amp` row — the κ bounds a few lines away read `AMP_PRIOR[b]`, the
GLACIER amp, not `AMP_LO`/`AMP_HI`.

**Everything else is L15's, deliberately** — same targets, and the **SAME** pooled proposal
(`adapted_cov_L15pool_seed2026.csv`), NOT one re-pooled from the L15 chains, which would be a
second change. `-25d` §3e's lesson stands.

⚠ **FLAGGED, NOT FIXED:** the prior widens 1.8× while its proposal block does not. The RAM
sampler adapts, so this is a burn-in cost rather than a bias — but **check the amp acceptance
and its adapted scale before reading the result**, and re-pool if either looks pathological.

⚠ The chain logs' setup prints (`A6 prior: …`) appear LATE in the file, not at the head — Julia
block-buffers a redirected stdout while ProgressMeter writes to stderr. L15's log does the same.
Not a fault; `tr '\r' '\n' < log | grep "A6 prior"` once it has flushed.

**WHAT TO DO WHEN IT LANDS**
1. `julia --project=julia_v2 julia/postprocess_mcmc_ext.jl --tag=L16 --accept-slr`
2. `posterior_predictive_ladrillo.jl --tag=L16`, then `project_ssps_components_ladrillo.jl
   --tag=L16` **TWICE** — default AND `--no-tap` (`-25d` §5: the `--no-tap` file is a REQUIRED
   INPUT to `scope_slr_fair_uncertainty.jl`'s `[CONTROL]` gate), then the 3 SSP fairunc runs,
   then `bench_ladrillo.py --tag=L16`. ~15 min total.
3. **THE FALSIFIABLE PREDICTION, pre-registered here.** If the ~4.8-log-unit preference is
   real and σ was the only thing suppressing it, the amp posterior median must land
   **BELOW 1.09** and its sd must exceed the 0.10 the old prior imposed. If it instead sits at
   1.09 ± 0.18 — a prior sample again — then the historical record does NOT identify amp at
   all, the −4.81 is an artifact of holding L14's other parameters fixed, and §4e's frame
   reading is the only one left. **Either outcome is informative; write down which one.**
4. Re-run `scope_ais_anchor_offline.jl --tag=L16` for the hindcast row on the same metric.

### The options as they stood, kept for the record

1. **REVERT amp to L14's prior and treat the CMIP6 secant as out-of-frame.** Cleanest reading
   of §4. Cost: the CMIP6 measurement, which is real and reproducible on two ensembles, is set
   aside on a frame argument that has now been wrong twice in the other direction.
2. **KEEP the 1.09 centre but WIDEN σ from 0.10 to the measured between-model 0.180** and let
   the likelihood express its ~5-log-unit preference. `-25d` §2 records that σ was deliberately
   held at 0.10 so the delta stayed attributable — that reason has expired now that the delta
   is attributed. This is the only option that lets the DATA choose, and it is a single-change
   arm.
3. **Resolve the frame properly**: measure the CMIP6 secant in DAIS's own reference frame
   (ice-core/continental surface, not a land-mean of GCM `tas`) before using it as a prior at
   all. Most expensive, and the only one that would stop the frame problem recurring.

⚠ Do not bundle. `-25d` §3e's lesson stands.

---

## 6. FILES

**New:** `julia/scope_ais_anchor_offline.jl`, `julia/scope_ais_anchor_identification.jl`,
`run_mcmc_L16.sh`.
**Modified:** `CHANGELOG.md` (entry `2026-08-25j`).
**Outputs:** `outputs/scope_ais_anchor_offline_L15.csv`,
`outputs/scope_ais_anchor_identification_L15{,_peaks,_amp,_amp_peaks}.csv`,
`outputs/log_scope_ais_anchor_{offline,identification}.txt`.

**Non-obvious state**

* ⚠ Neither script touches `ladrillo_projection.jl`. The anchor override is applied
  **after** `ladrillo_apply_draw!`, per draw, so no shared module carries a mode that a later
  run could inherit silently. An env-var hook was considered and rejected for that reason.
* ⚠ The AIS target column is **bit-identical** pre/post the L15 target rebuild (`ais`,
  `ais_lo`, `ais_hi` all max|diff| = 0; only `lws` 0.123 and `dang_closure_sig` 0.151 moved),
  so scoring L14 and L15 against the CURRENT `recalib_targets_ext.csv` is exactly
  like-for-like. This was checked, not assumed — `-25d` §5 warns the file moved.
* The offline sweep runs UNTAPPED: the Greenland volume tap is a Greenland-component object
  and does not enter `:ais`.
* `--axis=amp` profiles the A6 PAIR. Do not profile `ais_temperature_coefficient` alone.
* Runtime: sweep ~7 min (8 cells × 2000 draws), profile ~90 s (2 arms × 200 × 41).
