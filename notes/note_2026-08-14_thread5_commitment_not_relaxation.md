# Thread 5, step 2 — the 2300 flatness is a COMMITMENT defect, not a relaxation one

`python/scope_gis_2300_relaxation.py` → `outputs/scope_gis_2300_relaxation.csv`.
Offline, no chains, no calibrator edits.

**Headline.** Spec `notes/spec_2026-08-14_next_calibration.md` §9 frames thread 5
as "what replaces proportional relaxation at high warming". **That framing is
wrong.** A+B's relaxation is not too slow — it is *faster* than the stock SIMPLE
it replaced, and A+B is 99% equilibrated by 2300. The entire 2300 shortfall is
that its committed loss is 19-24× below what an ice-sheet model gives. And the
commitment cannot simply be raised, because the 1900-2025 hindcast only
constrains the **product** of commitment and rate: over a ridge that fits the
hindcast identically, the 2300 projection runs **14.6 → 58.3 cm**.

**Reproduction gate.** Both modules are re-implemented in numpy from
`julia/greenland_ab_component.jl` and MimiBRICK's
`greenland_icesheet_component.jl` (t−1 lag, clamps, the V/V0 rate damping A+B
drops). All 18 medians (3 SSPs × 3 horizons × 2 arms) land within **0.05 cm** of
`outputs/ssps_components_2300_L10.csv` and the quarantined
`ssps_components_2300_extC.csv`. The script refuses to print a diagnosis
otherwise.

---

## 1. A+B has already finished; stock is still going

Write both modules the same way — a loss `L(t)` closing on a committed loss
`Leq(T(t))` at rate `r(T)` — and read off the realised fraction `phi = L/Leq`:

| scenario | year | arm | Leq m | L m | **phi** | still to come m | rate cm/yr |
|---|---|---|---|---|---|---|---|
| SSP1-2.6 | 2300 | A+B | 0.137 | 0.135 | **0.987** | 0.002 | 0.002 |
| SSP1-2.6 | 2300 | stock | 1.002 | 0.257 | 0.259 | 0.740 | 0.058 |
| SSP2-4.5 | 2300 | A+B | 0.205 | 0.203 | **0.991** | 0.002 | 0.002 |
| SSP2-4.5 | 2300 | stock | 1.221 | 0.322 | 0.267 | 0.900 | 0.084 |
| SSP5-8.5 | 2300 | A+B | 0.454 | 0.448 | **0.989** | 0.005 | 0.019 |
| SSP5-8.5 | 2300 | stock | 1.957 | 0.552 | 0.295 | 1.383 | 0.196 |

Under SSP1-2.6 the shipped Greenland has **stopped**: 0.002 cm/yr at 2300, 2 mm
of commitment left. That is the flatness, and it is equilibration, not sluggishness.

The 2300 gap splits (symmetric/Shapley form) into a realisation term and a
commitment term. The realisation term runs the **wrong way** — A+B's faster
relaxation *adds* 0.41-0.84 m — and is more than cancelled by a commitment term
of −0.54 to −0.97 m:

| scenario | dL m | realisation | commitment | phi | Leq m |
|---|---|---|---|---|---|
| SSP1-2.6 | −0.122 | **+0.414** | **−0.538** | 0.259 → 0.987 | 1.00 → 0.14 |
| SSP2-4.5 | −0.120 | **+0.516** | **−0.639** | 0.267 → 0.991 | 1.22 → 0.20 |
| SSP5-8.5 | −0.105 | **+0.836** | **−0.965** | 0.295 → 0.989 | 1.96 → 0.45 |

That decomposition is a linearisation on medians of two *unpaired* posteriors, so
the script checks `med(phi)·med(Leq)` against `med(L)` rather than assuming it
(max residual 0.026 m, at SSP5-8.5/2300/stock) — the "56% redundant" retraction
came from exactly this trap.

## 2. The 2×2 cross-test, which does not rely on that linearisation

Each arm's `Leq(t)` is a plain time series in m SLE, so it can be fed to the
other arm's relaxation with no driver mapping. At median parameters, 2300, cm rel
1995-2014 (diagonal reproduces the arms: 7.67/14.57/39.51 vs 7.79/14.57/39.10,
and 18.88/25.46/49.90 vs 19.16/25.69/48.62):

| commitment ↓ / relaxation → | A+B | stock |
|---|---|---|
| **A+B** (SSP2-4.5) | 14.57 | **4.33** |
| **stock** (SSP2-4.5) | **65.72** | 25.46 |
| **A+B** (SSP5-8.5) | 39.51 | **11.63** |
| **stock** (SSP5-8.5) | **137.31** | 49.90 |

Holding commitment fixed, A+B's relaxation always yields *more* loss by 2300.
Holding relaxation fixed, stock's commitment yields 3.5-4.5× more. The
relaxation form is not the lever.

## 3. Neither channel is slow, and the two are labelled backwards

A+B splits the commitment into a "fast (surface mass balance)" share `f` and a
"slow (dynamic discharge)" remainder. At posterior medians:

    fast (SMB)      alpha 0.003536   beta 0.004979
    slow (dynamic)  alpha 0.005193   beta 0.007310

Both `alpha` and `beta` are LARGER on the slow channel, so `r_slow > r_fast` for
every `T > −1.41 K` — i.e. everywhere. **76.6% of draws** have slow faster than
fast at `T_south = 2 K`.

| scenario | year | T_south K | tau_fast yr | tau_slow yr |
|---|---|---|---|---|
| SSP1-2.6 | 2025 | 2.31 | 76.0 | 51.8 |
| SSP2-4.5 | 2300 | 4.92 | 44.7 | 30.4 |
| SSP5-8.5 | 2300 | 12.59 | 20.2 | 13.8 |

Nothing in the module exceeds ~80 yr. Greenland's dynamic response is millennial,
so **there is no slow reservoir at all**, and the Mouginot partition — which pins
`f` as the *surface* share of the commitment — is pinning it onto whichever
channel the sampler made slower, which is the one named "fast".

(Note the posterior medians are NOT the offline A+B optimum the spec quotes,
`alpha_s = 0.00708, beta_s = 1e-6`. The optimum rails `beta_s`; the posterior
median does not. Both statements in spec §4 stand — the rail is `beta_s`, and
0.00-0.01% of draws sit on it — but any reasoning from the offline optimum's
channel timescales does not carry to the shipped posterior.)

## 4. The commitment is 19-24× below an ice-sheet model

"Lower than stock" is not by itself a defect: stock's own commitment is dominated
by a temperature-INDEPENDENT intercept (~0.73 m at zero anomaly, 73% of its
SSP1-2.6/2300 commitment), which is its own problem, so stock is not a benchmark.
Against Bochow et al. 2026 (EGUsphere preprint, provisional — referee concerns on
UQ, verification and functional form all still binding), committed loss at each
scenario's own 2300 GMST, m SLE:

| scenario | GMST K | A+B | stock | Yelmo | PISM | SICOPOLIS | A+B vs min |
|---|---|---|---|---|---|---|---|
| SSP1-2.6 | 1.74 | **0.137** | 1.002 | 3.37 | 3.11 | 3.23 | **23× low** |
| SSP2-4.5 | 3.15 | **0.205** | 1.221 | 5.06 | 4.84 | 4.93 | **24× low** |
| SSP5-8.5 | 7.81 | **0.454** | 1.957 | 8.56 | 8.71 | 8.67 | 19× low |

(Above ~6 K the Bochow branch map extrapolates past its own deglaciated branch —
hence >7.42 m — so lean on the 1.74 K and 3.15 K rows.) A+B commits 6% of the ice
sheet at ~6.5 K of global warming.

## 5. Why the calibration cannot just find a bigger commitment

Because the hindcast sees only `phi·Leq`. Scale `(c1, c0)` by `k`, re-solve the
rate scale `s` that restores the 1900-2025 target of **5.78 cm**
(`recalib_targets_ext.csv`), and re-read 2300 (SSP2-4.5, median params):

| k | Leq(2300) m | rate scale s | tau_slow @2300 | hindcast cm | **2300 cm** |
|---|---|---|---|---|---|
| 1.0 (as calibrated) | 0.204 | 1.0034 | 30 yr | 5.78 | **14.59** |
| 2.0 | 0.408 | 0.3254 | 93 yr | 5.78 | 29.82 |
| 5.0 | 1.020 | 0.1117 | 272 yr | 5.78 | 46.30 |
| 10.0 | 2.040 | 0.0535 | 569 yr | 5.78 | 53.68 |
| 22.6 (Bochow-matched) | 4.610 | 0.0231 | 1316 yr | 5.78 | **58.29** |

Every row fits the hindcast **exactly as well**. The 2300 projection moves by
**4×** across the ridge, saturating near ~60 cm. The `s = 1.0034` at `k = 1` is a
free check that the calibrated parameters sit on this curve.

So: `gis_c1` reading "strongly constrained" in spec §8.4 (posterior sd / prior sd
= 0.12) is the *conditional* width at the timescales the module can express. It is
not evidence that the commitment is identified — the module simply cannot hold a
large commitment unrealised, because its longest timescale is 80 years.

---

## 6. What this changes

1. **Spec §9's framing of thread 5 is retracted.** It is not "what replaces
   proportional relaxation at high warming". It is: *the module has no
   millennial reservoir, so the hindcast forces a commitment 20× too small, and
   the 2300 deliverable is set by an unidentified ridge.*
2. **Raising `c1` alone would be wrong**, and lengthening the timescale alone
   makes 2300 *lower* (4.33 cm at SSP2-4.5). They move together or not at all.
3. **The identifying constraint cannot come from the sea-level hindcast.** It has
   to be an external `Leq(T)` target — which is what Option C (the PISM
   equilibrium ladder) was reaching for and where it FAILED (CHANGELOG
   2026-08-10). Re-opening the commitment question means re-opening that, not
   re-tuning A+B.
4. **The 2100 deliverable is untouched.** At 2100 `phi` is 0.68-0.84, the ridge
   has not yet collapsed, and L10 was accepted on the 2100 spread. Nothing here
   argues against the shipped 2100 numbers; it argues against quoting the 2300
   column without this caveat.
5. **Channel labelling** (§3) is a separate, smaller defect and is worth fixing
   whatever is decided about the commitment.

## 7. What was NOT done

No calibrator edit, no chain, no change to any shipped output — per the
sequencing call (Marcus, 2026-08-14: scope thread 5 before committing to the
thread-4 calibration). The thread-4 change set remains NOT STARTED.

**Open for Marcus.** Whether an external `Leq(T)` constraint goes into the *same*
change set as D1/D2/1.2 (it invalidates the posterior the same way, so bundling
is the same argument), or whether Ladrillo 1.0 ships its 2300 column with the
§5 ridge stated as a caveat and the commitment question is deferred.
