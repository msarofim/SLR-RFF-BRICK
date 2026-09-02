# Scoping — the TE rate FAIL: how much is scope, how much is the driver, and what is left to do

**Written 2026-09-02.** Marcus's criterion (2026-09-02): *projection mismatches against other
models are low priority; conflict with physical understanding or observational matching is not.*
Under that filter, of L24's 309 benchmark cells only **30 are observational**, and on those
**L21, L23 and L24 are identical — 1 FAIL, 3 WARN each**. Every difference between the vintages
lives in the literature block. So there is exactly one observational conflict in the model, and
this document scopes it. **Scoping only; nothing changed.**

---

## 1. THE DEFECT AS REPORTED — AND WHAT IT ACTUALLY IS

    [R] te  rate/1993-2026   0.1565 cm/yr   1.27x obs   z = +5.87   FAIL

⚠ **The benchmark applies NO depth-scope correction, and the mismatch is stated in the target
file's own header.** `data/observations/ohc_spliced_zanna_igcc.csv` line 2 reads *"IGCC 2024
ocean_0-2000m"*; FaIR's `ohc_1e22J` is **full-depth**. `grep` finds no scope handling anywhere in
`bench_ladrillo.py`.

This is the SAME cell that in August read 1.19x / z=+4.19 and was scope-corrected to
**1.08-1.19x, "WARN at worst"** ([[scope_before_skill]], commit `d24cc67`). That correction was
measured — IGCC's own `ocean_2000-6000m` layer prices the deep contribution at **+10.2 % of the
trend**, i.e. **51 % of the overshoot was scope** — and it was never wired into the benchmark.
Re-applying it (the factor reproduces August's recorded outcome exactly: 1.19/1.102 = 1.080):

| | raw | scope-corrected |
|---|---|---|
| ratio | 1.27x | **1.152x** |
| z | +5.87 | **~3.3** |

## 2. WHAT REMAINS DECOMPOSES ALMOST ENTIRELY INTO THE DRIVER

`scope_before_skill` prescribes the decomposition, because the relation is linear:
`TE = alpha x OHC`, so `rate(TE)/rate(obs) = OHC_ratio x alpha_ratio` exactly.

**FaIR OHC rate vs the IGCC 0-2000 m target, OLS on the cumulative series, matched windows:**

    1993-2024   FaIR 1.3676   obs 1.1258   ratio 1.215   (n=32/32)
    1993-2020   FaIR 1.3245   obs 1.0714   ratio 1.236   (n=28/28)
    2005-2024   FaIR 1.4843   obs 1.2152   ratio 1.221   (n=20/20)

Stable at **1.215-1.236**; the window mismatch in the benchmark's own 1993-2026 cell is worth only
~2 %. Therefore:

| term | value |
|---|---|
| TE rate ratio (raw) | 1.270 |
| **OHC driver ratio** | **1.236** |
| implied alpha ratio | **1.028** |

⇒ **The driver carries 87 % of the overshoot. The expansion coefficient is neutral.** August
measured alpha at 0.93-0.97x on the L14-era arm; here it is 1.028 on L24. Different vintage and
estimator, same conclusion: **alpha is within ~7 % of 1 either way and cannot explain 27 %.**
"Tighten alpha" is not the fix, and in August it would have made the fit worse.

## 3. THE MISS IS SHARED — SO IT IS NOT A CALIBRATION PROBLEM

`rate/1993-2026`, all arms:

| arm | te | verdict | total | verdict |
|---|---|---|---|---|
| L24 | 1.27x, z=+5.87 | FAIL | 1.07x, z=+0.76 | pass |
| L23 | 1.27x, z=+5.84 | FAIL | 1.07x, z=+0.76 | pass |
| **BRICK 2.0** | **1.17x, z=+3.74** | FAIL | 1.04x, z=+0.46 | pass |

BRICK 2.0 is a **completely independent posterior on the same FaIR OHC driver** and it misses the
same cell. Per `scope_before_skill`: *a shared miss across two independent calibrations is a scope
or driver signal, not a calibration one.*

⭐ **AND BOTH MODELS MATCH THE OBSERVED TOTAL RATE** (1.07x / 1.04x, both well inside the bar).
So this is a component-attribution problem, not "the model gets sea level wrong". TE runs fast and
AIS/glaciers/GIS run slightly slow (0.97 / 0.92 / 1.00), and they compensate.

## 4. ALREADY RULED OUT — DO NOT REDO

* ⛔ **The OHC aging / vintaging module** (deep heat contributing less to SLR). **Empirically dead**
  2026-08-29 ([[rebased_share_trend_flips]]): on the baseline-free window partition FaIR and IGCC
  **AGREE** (1971-92 0.728 vs 0.734; 2005-24 0.709 vs 0.703; change -0.020 vs -0.031 +/- 0.130),
  **neither resolved at 2 sigma**. The 6.3 sigma mismatch that motivated it was a rebasing artifact.
  ⚠ The *physical* case for a two-coefficient depth split is untouched — it never rested on a
  mismatch — but it has **no observational support** and cannot be justified by the observed
  partition.
* ⛔ **The steric noise model.** L22 capped the AR(1) MARGINAL at the observational epsilon
  (0.277 -> 0.100, a 64 % cut). The TE residual did not collapse ([[l22_noise_cap_exonerates]]).
* ⛔ **thermal_alpha.** ~1.03 here, 0.93-0.97 in August. Near 1 either way (§2).
* ⚠ **The headline size is 4.5 sigma, not 17.8.** `posterior_predictive_ladrillo.jl` applies no
  `d2`; the fit does. The effective 2025 residual is +0.227 cm = 4.52 sigma
  ([[postpred_omits_discrepancy]]). Quote the effective number.

## 5. WHAT IS LEFT, IN COST ORDER

1. ⭐ **Fix the benchmark's scope — ~1 h, no runs.** `bench_ladrillo` scores a full-depth model
   against a 0-2000 m target with no correction, in defiance of a standing project lesson that was
   established in August on this exact cell. Either subtract the model's >2000 m contribution or
   add the deep layer to the target, and LABEL the cell with which was done.
   ⚠ **State the caveat at the cell:** IGCC's `ocean_2000-6000m` rises by exactly 1.15 ZJ/yr, sd
   0.000000 — a **PRESCRIBED rate, not data**. So the correction is a bounded adjustment, not a
   measurement, and the corrected cell must say so.
2. **Decide whether a ~12 % fast FaIR OHC rate is a real conflict — and it is a FaIR question.**
   The cheapest decisive test is product sensitivity: OHC products disagree by ~2x, Cheng is the
   low-side outlier and Gouretski the high-side ([[brick_gouretski_calib]]), so re-measure the
   §2 ratio against **both** products on the baseline-free estimator. If "fast" does not survive
   the product choice, there is no conflict to fix.
3. **Only then** consider model changes — and note the lever is in FaIR's ocean, not in Ladrillo.

⚠ **What would NOT be evidence:** a refit. TE's coefficient is neutral and the driver is external,
so a Ladrillo recalibration cannot move this cell except by buying the residual off in `d2`, which
it already partly does.

---

# ADDENDUM 2026-09-02 — THE ALPHA CONNECTION, TESTED

§2 above said the driver carries 87 % and alpha is neutral. Both true, and both miss the point:
**alpha's neutrality is itself the regression.** Tested and confirmed below.

## The cell degraded, and it is the coefficient

| | alpha (cm per 1e22 J) | vs obs-implied | TE rate ratio |
|---|---|---|---|
| L14 (August) | 0.10571 | 0.93-0.96x | 1.192x — WARN after scope |
| L21 / L24 | **0.11252** | 0.99-1.03x | **1.269x — FAIL even after scope** |

⚠ `run_mcmc_L21.sh` states L21 is L14's EXACT configuration with only the forcing driver changed
(`632f330`). So L14 -> L21 is already a controlled one-variable test, and the variable is the driver.
⚠ Both read the SAME FILENAME, `fair_mean_ohc_ssp245harm.csv` — its CONTENT was regenerated. The
pre-migration driver must be recovered from git (`632f330^`), not from `fair_mean_ohc.csv`, which
is a different 2026-05-25 file. I used the wrong one at first.

## TEST 1 — does the driver's OHC change predict the alpha change? YES

alpha is fit so that `alpha x OHC` tracks the steric target over the fit window (1900-2025), so it
must scale as the inverse of the driver's OHC gain:

    OHC change 1900-2025   PRE-migration 75.326   POST-migration 69.366   ratio 0.9209
    PREDICTED alpha ratio  1/0.9209 = 1.0859
    MEASURED  alpha ratio  0.11252/0.10571 = 1.0644      agreement 98 %

The 2 % shortfall is the rest of the parameter vector absorbing part of it; alpha is not the only
free term. **Mechanism confirmed.**

## TEST 2 — WHERE did the driver change? ENTIRELY THE PRE-1950 RAMP

    window      dOHC old   dOHC new   new/old
    1900-1950     14.500      9.092    0.627      <- the whole effect
    1950-1993     16.769     16.119    0.961
    1993-2025     44.057     44.156    1.0022     <- satellite era UNTOUCHED
    1900-2025     75.326     69.366    0.921

Matches [[brick_calib_input]] exactly: *endpoints EQUAL, the gap is the pre-1950 ramp.*

## TEST 3 — IS THE NEW EARLY RAMP BETTER? YES, DECISIVELY

    window      OLD drv   NEW drv   Z+IGCC   Z+Cheng   verdict
    1900-1950     14.50      9.09     7.34      7.34    NEW closer (|err| 7.16 -> 1.75)
    1900-1970     20.16     14.35    13.75     12.83    NEW closer (|err| 6.87 -> 1.06)
    1950-1993     16.77     16.12    17.66     11.72    NEW closer
    1993-2024     42.33     42.35    33.35     35.44    UNCHANGED (7.93 vs 7.96) — both ~22% fast

calib 1.6.0 **halved a real early-century bias**: the old driver put 2x the observed heat into
1900-1950. Consistent with the 44 % OHC RMSE improvement recorded for the migration.

## ⇒ THE CHAIN, AND WHAT IT MEANS

1. calib 1.6.0 **correctly** cut early-century OHC uptake (14.50 -> 9.09 against an observed 7.34).
2. The **modern-era OHC overshoot (~22 %) is untouched** — it predates the migration and survives it.
3. The fit has **ONE time-invariant alpha** and matches steric over 1900-2025, so the smaller early
   ramp forced alpha **up 6.4 %**.
4. That higher alpha, applied to a modern OHC that is still ~22 % fast, **stopped offsetting it** —
   TE rate 1.192x -> 1.269x, WARN -> FAIL.

**The alpha rise is CORRECT behaviour, not a defect.** The FAIL is the visible symptom of a
structural limit: **one expansion coefficient cannot simultaneously serve an early ramp that is now
right and a modern rate whose driver is 22 % fast.** The model was previously hiding the modern
driver bias inside a low alpha that was compensating for an early-century driver bias. Fixing the
early bias exposed the modern one.

⭐ **AND THIS HANDS THE DEPTH SPLIT A NEW MOTIVATION — a different one from the refuted case.**
The two-coefficient split was killed as an *observational-partition* claim ([[rebased_share_trend_flips]]:
FaIR and IGCC agree on the vertical partition, neither resolved at 2 sigma). This is not that
argument. It is an **internal over-determination** argument: a single alpha is now provably
required to satisfy two epochs the driver gets wrong by different amounts. ⚠ **NOT PROVEN that a
split would fix it** — that depends on whether FaIR's depth structure lines up with the epochs, and
it must be tested before being built. But the case no longer rests on the refuted partition claim.

**What this does NOT change:** the ~22 % modern OHC overshoot is still a FaIR question, still shared
with BRICK 2.0, and still unfixable inside either sea-level model.

---

# ADDENDUM 2 — THE DEPTH SPLIT, TESTED IN CLOSED FORM. IT IS REFUTED, AND THE REASON IS PHYSICAL.

Addendum 1 said the over-determination "hands the depth split a NEW motivation" and flagged it
UNTESTED. **Tested now, and it does not survive.** No refit was needed: TE is linear in OHC, so with
FaIR's own layer output the question closes analytically (`d2_prior_is_not_binding` — count the
parameter's places first).

Data: `FaIRtoFrEDI/fair_outputs/diag_fair_ohc_layers_full.csv` (H0/H1/H2, 1750-2301). Verified the
SAME vintage as the calibration driver — layer total minus driver = **0.000** at 1950/2000/2024.

## What each epoch wants, and how its heat is distributed

| epoch | alpha needed (cm per 1e22 J) | shallow share H0+H1 | deep share H2 |
|---|---|---|---|
| 1900-1950 | 0.0874 | 0.575 | 0.425 |
| **1950-1993** | **0.1277** | **0.379** | **0.622** |
| **1993-2025** | **0.0904** | **0.527** | 0.473 |
| 1900-2025 | 0.0987 | 0.522 | 0.478 |
| **fit chose** | **0.11252** | | |

⚠ **My first framing was wrong.** I set the conflict up as EARLY vs MODERN; those two agree to 3.4 %
(0.0874 vs 0.0904) and their partitions differ by only 4.8 points. **The outlier is MID-CENTURY**,
which wants **41 % more alpha** than the modern epoch and differs from it by **15 points** of
partition. That is the system that had to be solved, and I solved the wrong one first.

## The closed form, every epoch pair x every split

Physical requirement: `0 < alpha_deep < alpha_upper` — deep water is colder and expands LESS per
joule; the pressure effect only partly offsets it. Published efficiency ratios are ~0.4-0.7.

    epoch pair                split          cond    a_upper     a_deep      d/u   physical?
    1900-1950 vs 1950-1993    H0+H1 | H2      6.0   -0.00287   +0.19877  -69.374   NO negative
    1900-1950 vs 1950-1993    H0 | H1+H2     19.3   -0.23312   +0.12990   -0.557   NO negative
    1900-1950 vs 1993-2025    H0+H1 | H2     48.8   -0.00386   +0.20012  -51.821   NO negative
    1900-1950 vs 1993-2025    H0 | H1+H2    144.7   +0.43886   +0.02954   +0.067   yes, but 15x
    1950-1993 vs 1993-2025    H0+H1 | H2      9.9   -0.00239   +0.19848  -83.038   NO negative
    1950-1993 vs 1993-2025    H0 | H1+H2     16.9   -0.09653   +0.12704   -1.316   NO negative

**Five of six give a NEGATIVE coefficient.** The one that does not demands `a_deep/a_upper = 0.067`
— the deep ocean expanding **15x less per joule than the top 45 m** — against a 0.4-0.7 expectation.

## ⇒ WHY IT FAILS, AND IT IS A MECHANISM, NOT AN ABSENCE OF EVIDENCE

The epoch that wants **HIGH** alpha (1950-1993) is **DEEP-weighted**; the epoch that wants **LOW**
alpha (1993-2025) is **SHALLOW-weighted**. To satisfy both, the deep reservoir would have to expand
**MORE** per joule than the shallow one. **The partition structure runs the WRONG WAY**, so a depth
split moves the model AWAY from reconciling the epochs.

⚠ This is a **stronger** refutation than the 2026-08-29 one. That killed the split as an
*observational-partition* claim ([[rebased_share_trend_flips]]) and explicitly left the physical case
"untouched". This kills the physical case too, on FaIR's own layer structure: **there is no
physically-ordered pair of coefficients that reconciles the epochs.** ⇒ **DO NOT BUILD IT.**

## Caveats — what would overturn this

1. **The mid-century steric target is the load-bearing input**, and it is the least secure one. The
   target's own splice is internally inconsistent: Frederikse/NOAA slope ratio **0.937** on the
   2005-2018 overlap, so the target changes method at 2019 ([E] of `diag_te_rate_attribution.py`).
   If the 1950-1993 requirement of 0.1277 is wrong, the whole conflict changes shape.
2. **FaIR's boxes are not depth horizons.** Box 0 is **45 m** thick, nothing like 0-700 m or
   0-2000 m. A split on FaIR's boxes is not the split the literature discusses; a physically-posed
   version would need a re-mapping, and this test does not rule that out — only the box-wise form.
3. The test uses ensemble-mean layers, not per-draw. A per-draw version could differ, though not
   plausibly by enough to flip a negative coefficient.

⇒ **The lever is still the driver, not the coefficient.** ~22 % fast modern OHC, shared with
BRICK 2.0, unfixable in either sea-level model.
