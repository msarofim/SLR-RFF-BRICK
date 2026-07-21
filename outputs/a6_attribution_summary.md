# A6 attribution — phase-2 vs equilibrium-recalibrated (2026-07-20/21)

Fully-recalibrated isolation of A6 (GMST→AIS amplification: CMIP6-transient N(0.95,0.10)
vs old equilibrium 1.196). Both posteriors 4×2M over-dispersed; the `extA6eq` chains differ
from phase-2 ONLY in the pinned amp. Scripts: `julia/diag_a6_attribution.jl` (level+pulse,
recalibrated) and `julia/diag_a6_pulse_ab.jl` (within-draw amp flip). SSP2-4.5; pulse 0.1 GtCO2.

## Total SLR@2100 median (deterministic harmonized mean forcing)
| posterior | SLR@2100 | SLR@2150 | threshold crossed |
|---|---|---|---|
| v-next (old, equilibrium) | 76.1 | 159.1 | — |
| A6-equilibrium recalib (A2/A4/A5+Dangendorf, amp 1.196) | 63.6 [38.5,98.3] | 126.4 | 81% |
| phase-2 (transient amp) | 39.8 [37.0,77.8] | 63.2 | 28% |

Attribution of the 76→40 cm drop: **A6 ≈ 24 cm (~⅔); A2/A4/A5 + obs/σ ≈ 12 cm (~⅓).**

## Pulse marginal (cm/GtCO2, 0.1 GtCO2 ensemble)
| | equilibrium recalib | phase-2 transient | A6 |
|---|---|---|---|
| median @2100 | 4.56e-3 | 4.35e-3 | −5% (ROBUST) |
| mean   @2100 | 3.86e-2 | 4.61e-3 | −88% (≈8×; the fat tip tail) |
| median @2150 | 6.66e-3 | 6.28e-3 | −6% |
| mean   @2150 | 4.05e-2 | 6.77e-3 | −83% |

**Median pulse is A6-robust (~5%); the mean/fat-tail is A6-dominated (~8×)** because A6 sets
the tipping fraction (81%→28%). Validation: equilibrium median 4.56e-3 ≈ June-13 3-BRICK
4.69e-3; equilibrium mean/median ≈ 8.5× matches the roadmap's "median under-states fast
dynamics 11–18×". Within-draw amp flip (holding phase-2 params fixed) gives −4% on the median
pulse — consistent, i.e. the recalibration adds little beyond the direct amp mechanism for the
median.

**Decision hook (M2):** the pulse HEADLINE is A6-robust iff the SC-SLR uses the MEDIAN (roadmap
already says never quote the per-ton mean). A fat-tail-inclusive number (Lemoine-Traeger
P(tip)·ΔSLR_tip) is highly A6-sensitive. The A6 controversy lives in the projection + the tail.
