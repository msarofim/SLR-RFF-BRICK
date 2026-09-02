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
