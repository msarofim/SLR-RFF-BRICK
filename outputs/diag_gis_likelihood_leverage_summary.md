# Gate 3.1 part 2 — likelihood grip per target series

Noise parameters: pooled medians over seeds [2026, 2027, 2028, 2029], last 50% of each 2,000,000-step extC chain (4,000,000 draws).

## Effective sample size

| series | years | n | rho | AR(1) tau (yr) | n_eff | stationary sd (cm) | mean band sigma (cm) |
|---|---|---|---|---|---|---|---|
| ais | 1900-2025 | 126 | 0.616 | 2.1 | **29.95** | 0.017 | 0.171 |
| gsic | 1900-2023 | 124 | 0.594 | 1.9 | **31.61** | 0.017 | 0.459 |
| gis | 1900-2025 | 126 | 0.985 | 67.5 | **0.93** | 0.318 | 0.188 |
| steric | 1900-2025 | 126 | 0.973 | 37.1 | **1.70** | 0.302 | 0.310 |
| dang | 1900-2024 | 125 | 0.453 | 1.3 | **47.09** | 0.068 | 1.538 |

## Cost of a 0.65 cm systematic residual over 1942-1982

Log-likelihood penalty (positive = worse fit) under three covariances.
n_eff above describes the AR(1) term alone and so understates the grip; the AR(1)-only column is that understatement made explicit.

| series | shape | AR(1)+band (as calibrated) | band only (iid) | AR(1) only | leverage the AR(1) removes |
|---|---|---|---|---|---|
| gis | step | 27.71 | 382.60 | 141.70 | 14x |
| gis | ramp | 7.53 | 122.77 | 8.92 | 16x |
| dang | step | 3.46 | 3.48 | 748.62 | 1x |
| dang | ramp | 1.22 | 1.22 | 258.24 | 1x |

## The realised correction (actual extC residuals, not a synthetic shape)

Mean over 1942-1982, cm; residual = model - obs.

| series | residual now | correction applied | residual after | delta logl |
|---|---|---|---|---|
| gis | -0.822 | +0.822 | +0.000 | **+16.49** |
| dang | -0.322 | +0.822 | +0.499 | **-4.06** |

Net over both channels: **+12.43 log-likelihood units** in favour of the Greenland correction.

Net log-likelihood available to the Greenland fix, as calibrated: **+27.71** gained on gis against **-3.46** paid on dang = **+24.25 net** (step), **+6.32 net** (smooth ramp).
