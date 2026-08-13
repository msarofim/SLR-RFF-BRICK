# Is the 3.25 K bump scenario composition? (balanced panels WITHIN scenario)

- commit `b2f698a`; estimator `secant`; 40 models; bins need >= 5 models
- panel = models present in EVERY bin up to the cap, within ONE scenario
- verdict scenario `ssp585` (the only one with coverage above ~3 K)

## ssp126

| cap | n models | curve (dT: median) | monotone | bump at first bin > 2.75 | slope above 2.75 K |
|---|---|---|---|---|---|
| 2.75 | 9 | 0.75: 1.348  1.25: 1.464  1.75: 1.581  2.25: 1.491  2.75: 1.596 | **no** | — | — |
| 3.25 | 9 | 0.75: 1.348  1.25: 1.464  1.75: 1.581  2.25: 1.491  2.75: 1.596 | **no** | — | — |
| 3.75 | 9 | 0.75: 1.348  1.25: 1.464  1.75: 1.581  2.25: 1.491  2.75: 1.596 | **no** | — | — |
| 4.25 | 9 | 0.75: 1.348  1.25: 1.464  1.75: 1.581  2.25: 1.491  2.75: 1.596 | **no** | — | — |
| 4.75 | 9 | 0.75: 1.348  1.25: 1.464  1.75: 1.581  2.25: 1.491  2.75: 1.596 | **no** | — | — |

## ssp245

| cap | n models | curve (dT: median) | monotone | bump at first bin > 2.75 | slope above 2.75 K |
|---|---|---|---|---|---|
| 2.75 | 27 | 0.75: 1.533  1.25: 1.589  1.75: 1.474  2.25: 1.340  2.75: 1.327 | **no** | — | — |
| 3.25 | 18 | 0.75: 1.478  1.25: 1.601  1.75: 1.462  2.25: 1.339  2.75: 1.357  3.25: 1.380 | **no** | +0.024 [-0.072, +0.095] | — |
| 3.75 | 10 | 0.75: 1.201  1.25: 1.399  1.75: 1.462  2.25: 1.452  2.75: 1.418  3.25: 1.417  3.75: 1.466 | **no** | -0.001 [-0.081, +0.038] | +0.0387/K [-0.1080, +0.1234] |

## ssp585

| cap | n models | curve (dT: median) | monotone | bump at first bin > 2.75 | slope above 2.75 K |
|---|---|---|---|---|---|
| 2.75 | 40 | 0.75: 1.489  1.25: 1.464  1.75: 1.361  2.25: 1.340  2.75: 1.303 | yes | — | — |
| 3.25 | 39 | 0.75: 1.539  1.25: 1.426  1.75: 1.360  2.25: 1.346  2.75: 1.310  3.25: 1.311 | **no** | +0.001 [-0.037, +0.036] | — |
| 3.75 | 34 | 0.75: 1.578  1.25: 1.510  1.75: 1.374  2.25: 1.351  2.75: 1.315  3.25: 1.339  3.75: 1.315 | **no** | +0.024 [-0.031, +0.036] | -0.0047/K [-0.0493, +0.0272] |
| 4.25 | 25 | 0.75: 1.597  1.25: 1.542  1.75: 1.412  2.25: 1.372  2.75: 1.317  3.25: 1.340  3.75: 1.319  4.25: 1.301 | **no** | +0.023 [-0.052, +0.042] | -0.0169/K [-0.0600, +0.0509] |
| 4.75 | 21 | 0.75: 1.597  1.25: 1.426  1.75: 1.385  2.25: 1.356  2.75: 1.296  3.25: 1.311  3.75: 1.300  4.25: 1.255  4.75: 1.251 | **no** | +0.015 [-0.031, +0.043] | -0.0164/K [-0.0425, +0.0459] |

## VERDICT

**The shipped support (0.75-2.75 K) is composition-free.** Within `ssp585` alone, on a balanced panel of all 40 models, the curve falls monotonically 1.489 -> 1.303 — the pooled curve the shape was built from falls 1.498 -> 1.284 over the same range. The part of the law actually in use does not depend on scenario mixing.

**Above 2.75 K the composition-controlled curve is INDISTINGUISHABLE FROM FLAT**, so the flat-hold is the right call and is neither conservative nor aggressive — it is what the data support.

- the pooled bump does NOT reproduce within `ssp585`: +0.015 [-0.031, +0.043] at the first bin above 2.75 K (balanced panel of 21 models to 4.75 K) against +0.057 pooled — so scenario composition IS most of the pooled bump, as hypothesised;
- but the slope above 2.75 K is -0.0164/K [-0.0425, +0.0459], spanning zero, so the region is flat-within-noise rather than declining. Reading the pooled curve's values there as 'above the held value' was reading composition, not physics.

**RETRACTS** the claim that the flat-hold 'assumes more decline than CMIP6 shows and is therefore not conservative'. That was computed on the pooled curve, which is exactly the object this test disqualifies above 2.75 K. The 0.41 cm G4 difference between the flat-hold and full-curve arms stands as a sensitivity, but the full-curve arm is now the LESS defensible of the two.

`ssp126` and `ssp245` cannot arbitrate: their balanced panels shrink to 9 and 10-27 models and are non-monotone even below 2.75 K, which is the small-panel noise this test is designed to expose, not a contradiction.

