# Note 2026-08-12 — Is AR(1) the right noise model, are the five streams independent, and where does the total actually bind?

Script `python/diag_noise_model_and_grip.py`; outputs
`outputs/diag_noise_model_{streams,crosscorr,grip}.csv`,
`outputs/diag_noise_model_summary.md`, `figures/diag_noise_model_and_grip.png`.
Questions pre-registered in the script header before any number was computed.

Three threads that turned out to be one: §6.1 of
`notes/note_2026-08-12_vivek_joint_calibration_artifacts.md` (Vivek's R matrix
drops `rho_gmsl` 0.960 → 0.883), the caveat flagged into
`python/prep_recalib_targets_ext.py` when the gate-3.1 σ ruling landed (an
anchor-shaped closure σ may double-count level correlation given ρ ≈ 0.97), and
item 4.3 (re-check TE against a modern OHC target).

**Residuals throughout are `model − target` at the extC posterior medians, cm.**

---

## 0. The machinery was tested before it was believed

Section C's headline is a rejection, so the test had to be shown capable of
*not* rejecting. Simulating from AR(1)+band with known parameters
(sd 0.30, ρ 0.5, band 0.05, n = 126): recovered ρ = 0.564, Ljung-Box on the
whitened residuals **p = 0.84**, BIC prefers the true AR(1) over a random walk
by 24.8. Two earlier versions of this self-test failed — once because the band
term swamped the process (sd 0.1 against band 0.2), once because at ρ = 0.97
the models are genuinely indistinguishable. Both failures were the test's
design, and finding them is why the test exists.

**Resolution probe** (stationary sd held fixed, ρ varied, 12 draws each) — how
often BIC picks the true AR(1) over a random walk:

| ρ | 0.5 | 0.8 | 0.9 | 0.95 | 0.97 | 0.99 | 0.995 |
|---|---|---|---|---|---|---|---|
| picks true AR(1) | 12/12 | 12/12 | 9/12 | 8/12 | 9/12 | 10/12 | 8/12 |

**Above ρ ≈ 0.8 this comparison stops working.** So a ΔBIC of ±6 between AR(1)
and a random walk on a series with ρ ≈ 0.99 — which is what gis and steric
return below — means "the data cannot tell", not "the residual is a random
walk". Read section C with that in hand.

---

## 1. The five streams are not independent — by construction, not by accident

`calibrate_mcmc_ext.jl` scores four component streams **and** a total stream,
where the modelled total *is* the sum of the modelled components plus observed
LWS. So

```
dang_resid = sum(component resids) + closure     (+ R19 glaciers + the gsic delta ramp)
```

where `closure = sum(component targets) + lws_obs − dang_target` is the +0.74 cm
quantity gate 3.1 already characterised. Measured over 1900–2023:

- the identity explains **55.9%** of the total residual's variance,
- `corr(dang_resid, sum(component resids)) = +0.81`,
- the unexplained remainder has sd **0.276 cm** — the R19 glacier scope term
  and the gsic δ ramp, both genuine model terms, not slop.

**Over half of the total stream's information is already in the component
streams.** The likelihood treats it as a fifth independent observation of the
same years. This is a structural double-count, and it is a stronger statement
than Vivek's: his R matrix models an *empirical* cross-stream correlation,
whereas ours is algebraic.

The correlation lives in the **levels** — dang–gis +0.73, dang–gsic +0.68 — and
largely disappears in the AR(1) **innovations**, where no pair exceeds |0.26|.
Leading PC of the standardised residuals: 50.3% of variance.

---

## 2. AR(1) is not the right specification — but neither is anything else in the family

BIC against the incumbent (negative = better), and Ljung-Box p on the
Cholesky-whitened residuals, which are iid N(0,1) iff the model is right:

| series | white | **AR(1)** | AR(2) | ARMA(1,1) | local level | trend+AR(1) | ML ρ |
|---|---|---|---|---|---|---|---|
| ais | −4.2 | 0.0 | −1.0 | +4.3 | −4.2 | +9.6 | 0.727 |
| gsic | +18.0 | 0.0 | **−6.6** | +3.4 | +14.7 | −0.5 | 0.998 |
| gis | +364.7 | 0.0 | **−20.3** | −2.0 | −6.4 | +8.7 | 0.992 |
| steric | +104.5 | 0.0 | +2.4 | +2.8 | −4.7 | +7.1 | 0.983 |
| dang | −4.8 | 0.0 | +4.8 | +4.8 | −4.8 | +9.7 | 0.000 |

**Ljung-Box p = 0.0000 for every series against every model** (best case
steric/AR(2), p = 0.0001), with Q running from 47 to 482 against a χ²₁₀
critical value of ~18. The self-test returns p = 0.84 on data it generated, so
this is a statement about the models, not the test.

**No member of this family — white noise, AR(1), AR(2), ARMA(1,1), a random
walk, or a linear trend plus AR(1) — whitens any of the five residual series.**

Two further readings:

- **A random walk is never excluded.** The 95% profile interval for ρ includes
  1 for all five streams (gis [0.980, 0.9998], gsic [0.984, 0.9999], steric
  [0.940, 0.9997]). The sampled ρ ≈ 0.985 is not identified against a unit root.
- **The re-referencing is not the cause.** Repeating the whole comparison with
  the 1995–2005 re-reference operator applied to every model (REML transform to
  an orthonormal basis of its range) changes no verdict by more than ~2 BIC. The
  hypothesis flagged when the closure σ landed — that pinning the residual at a
  mid-record anchor manufactures the apparent persistence — is **disconfirmed**.

The honest description: **the residuals are systematic model error, not noise**,
and an AR(1) with ρ → 1 is this family's only way of saying so.

---

## 3. Vivek's mechanism does NOT transfer to Ladrillo

§6.1's hypothesis was that a near-unity per-series ρ is cross-stream correlation
with nowhere else to go, so an R-sampling scheme would lower ρ_gis and restore
leverage on the mid-century Greenland offset. Projecting the leading common
factor out of the residual matrix and re-estimating:

| series | ρ as calibrated | ρ ML | ρ after PC1 removed |
|---|---|---|---|
| ais | 0.727 | 0.784 | 0.784 |
| gsic | 0.998 | 0.998 | 0.992 |
| gis | 0.992 | 0.992 | **0.994 (rises)** |
| steric | 0.983 | 0.981 | **0.986 (rises)** |

**The persistence is intrinsic within-series structure, not cross-stream
leakage.** Removing a factor carrying half the cross-stream variance moves ρ by
less than 0.01, and for gis and steric it moves the wrong way. This is a clean
negative result and it settles the §6.1 action: the step-5 pre-registration does
**not** need a second expected posterior under an R-sampling likelihood, and
there is now a second reason (on top of 32× wall clock) not to adopt one.

Consistent with §2: the cross-stream signal is in the levels, where §1's
identity already accounts for it, and the innovations are nearly uncorrelated.

---

## 4. The total target is the weakest constraint in every window

σ on a window-mean offset (cm; smaller = tighter), from the Fisher information
`s' Σ⁻¹ s` under each stream's own fitted AR(1)+band:

| window | ais | gsic | **gis** | steric | **dang** | dang, closure OFF |
|---|---|---|---|---|---|---|
| 1900–1930 | 0.058 | 0.235 | 0.156 | 0.211 | **0.554** | 0.414 |
| 1942–1982 | 0.021 | 0.121 | **0.085** | 0.127 | **0.300** | 0.252 |
| 1950–1980 | 0.023 | 0.124 | 0.084 | 0.119 | 0.336 | 0.284 |
| 1993–2018 | 0.014 | 0.069 | 0.056 | 0.084 | 0.195 | 0.145 |
| 2000–2024 | 0.014 | 0.072 | 0.055 | 0.070 | 0.185 | 0.114 |

**The total is the loosest stream in every window** — 3.5× looser than the gis
component over 1942–1982, and that holds **with the closure term switched off**
(0.252 vs 0.085). So the total was never what limits a mid-century Greenland
correction; the **gis component target** is. That independently supports gate
3.1's verdict, and it means a step-5 outcome-3 (Greenland improvement
suppressed) cannot be blamed on the total or on the closure σ.

**What the closure σ actually cost**, in these units: +19% mid-century
(0.252 → 0.300) but **+62% in the modern era** (0.114 → 0.185). The untuned
ruling loosens the well-observed present about three times more, in relative
terms, than the poorly-observed mid-century — the ratio Marcus was shown as
1.11× vs 1.90×, now in interpretable units. It remains defensible (the shape is
Frederikse's, not ours) and the affected constraint was already the weakest one,
but it is the opposite of the efficiency-motivated shape.

---

## 5. Item 4.3 — CLOSED. TE's expansion efficiency is right, and the "3× below physics" concern was about a calibration we no longer use

`te_sea_level[t] = te_sea_level[t−1] + ΔOHC[J] · te_α / (te_A · te_C · te_ρ²)`,
so the interpretable quantity is cm of thermosteric rise per 10²² J.

| | te_α (kg m⁻³ °C⁻¹) | efficiency (cm per 10²² J) |
|---|---|---|
| **extC posterior** p05 / p50 / p95 | 0.1422 / **0.1540** / 0.1648 | 0.0933 / **0.1010** / 0.1081 |
| physics (α_v 1.5–2.0e−4 /°C × ρ) | 0.154 – 0.205 | 0.1011 – 0.1348 |
| **observed**, NOAA 0–2000 m steric on Zanna+IGCC OHC, 2005–2024 | — | **0.1043** |
| **observed**, same on Zanna+Cheng OHC | — | **0.1133** |

extC sits **3% below the IGCC-based observed efficiency and 11% below the
Cheng-based one**, at the bottom edge of the physics range. Like-for-like: both
sides of the observed regression are 0–2000 m over 2005–2024.

The `mimibrick-quirks` concern that te_α is "~3× below the physics value"
refers to **Wong's v1.2 calibration (te_α ≈ 0.057)**, which is 2.7× below
extC's 0.154. **extC already fixed it**; item 4.3's premise does not apply to
the current model. What remains is a **level** offset, not an efficiency one:
the steric residual averages **+0.242 cm** (model above target, sd 0.279), the
same-signed overshoot recorded for BRICK-Mengel. That is an initial-condition /
`thermal_s0` question, and it is not what 4.3 was aimed at.

---

## 6. What this changes

**Do:**
1. **Close §6.1 as a negative result.** No dual pre-registration is needed.
   Record that the mechanism was tested and does not transfer.
2. **Close item 4.3.** Re-point the residual concern at `thermal_s0` / the TE
   level offset, which is a different question.
3. **State in the step-5 pre-registration** that the leverage figure (+14.38
   logl) is conditional on a noise model that fails goodness-of-fit on all five
   streams. Its *sign* is safe — the gis stream is 3.5× tighter than the total —
   but do not quote it to two decimals as though it were calibrated.

**Do not:**
4. Do not adopt an R-sampling likelihood for step 5 — §3 removes the physical
   motivation, on top of the 32× wall-clock argument.
5. Do not change the noise model before step 5. The misspecification is real but
   it is not new, extC was calibrated under it, and changing it now would make
   Ladrillo 1.0 incomparable to extC on top of every other change in flight.

**After 1.0 — the queue this opens, in priority order:**
6. **The total stream is 56% redundant with the components and is the loosest
   constraint in every window.** Two independent reasons to stop scoring it as a
   fifth independent observation. Options: drop it and score components only;
   score the total *instead of* one component; or model the joint covariance
   properly. This is the single largest structural issue the diagnostic found.
7. **The residuals are systematic model error, not noise.** No stationary or
   unit-root linear process at annual resolution whitens them. That argues for
   an explicit discrepancy term rather than a wider noise model.
8. `rho_dang` is barely identified — the total's residual (sd 0.415 cm) is now
   far inside its own σ (mean 2.02 cm), and the ML fit returns ρ = 0 while the
   posterior median is 0.453.
