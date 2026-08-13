# Gate 3.1 part 2 — likelihood grip per target series (extC)

Vintage: **extC (superseded 2026-08-13; stock-SIMPLE Greenland)**. Noise parameters: 10,000-member posterior subsample (parameters_subsample_brick_mengel_extC.csv), a uniform stride over the pooled post-burn draws of seeds [2026, 2027, 2028, 2029].

## Effective sample size

| series | years | n | rho | AR(1) tau (yr) | n_eff | stationary sd (cm) | mean band sigma (cm) |
|---|---|---|---|---|---|---|---|
| ais | 1900-2025 | 126 | 0.615 | 2.1 | **30.00** | 0.017 | 0.171 |
| gsic | 1900-2023 | 124 | 0.595 | 1.9 | **31.45** | 0.017 | 0.459 |
| gis | 1900-2025 | 126 | 0.985 | 67.9 | **0.93** | 0.319 | 0.188 |
| steric | 1900-2025 | 126 | 0.973 | 37.0 | **1.70** | 0.302 | 0.310 |
| dang | 1900-2024 | 125 | 0.451 | 1.3 | **47.32** | 0.068 | 2.021 |

## Cost of a 0.65 cm systematic residual over 1942-1982

Log-likelihood penalty (positive = worse fit) under three covariances.
n_eff above describes the AR(1) term alone and so understates the grip; the AR(1)-only column is that understatement made explicit.

| series | shape | AR(1)+band (as calibrated) | band only (iid) | AR(1) only | leverage the AR(1) removes |
|---|---|---|---|---|---|
| gis | step | 27.69 | 382.60 | 141.62 | 14x |
| gis | ramp | 7.53 | 122.77 | 8.91 | 16x |
| dang | step | 2.34 | 2.34 | 758.14 | 1x |
| dang | ramp | 0.82 | 0.83 | 261.69 | 1x |

## The realised correction (actual extC residuals, not a synthetic shape)

Mean over 1942-1982, cm; residual = model - obs.

| series | residual now | correction applied | residual after | delta logl |
|---|---|---|---|---|
| gis | -0.822 | +0.822 | +0.000 | **+16.47** |
| dang | -0.322 | +0.822 | +0.499 | **-2.11** |

Net over both channels: **+14.36 log-likelihood units** in favour of the Greenland correction.

Net log-likelihood available to the Greenland fix, as calibrated: **+27.69** gained on gis against **-2.34** paid on dang = **+25.36 net** (step), **+6.70 net** (smooth ramp).
