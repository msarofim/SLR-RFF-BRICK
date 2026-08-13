# Gate 3.1 part 2 — likelihood grip per target series (L10)

Vintage: **L10 (Ladrillo 1.0; Greenland A+B in the joint likelihood)**. Noise parameters: 10,000-member posterior subsample (parameters_subsample_brick_mengel_L10.csv), a uniform stride over the pooled post-burn draws of seeds [2026, 2027, 2028, 2029].

## Effective sample size

| series | years | n | rho | AR(1) tau (yr) | n_eff | stationary sd (cm) | mean band sigma (cm) |
|---|---|---|---|---|---|---|---|
| ais | 1900-2025 | 126 | 0.603 | 2.0 | **31.22** | 0.017 | 0.171 |
| gsic | 1900-2023 | 124 | 0.649 | 2.3 | **26.41** | 0.020 | 0.459 |
| gis | 1900-2025 | 126 | 0.789 | 4.2 | **14.85** | 0.025 | 0.188 |
| steric | 1900-2025 | 126 | 0.976 | 41.6 | **1.51** | 0.315 | 0.310 |
| dang | 1900-2024 | 125 | 0.452 | 1.3 | **47.16** | 0.101 | 2.021 |

## Cost of a 0.65 cm systematic residual over 1942-1982

Log-likelihood penalty (positive = worse fit) under three covariances.
n_eff above describes the AR(1) term alone and so understates the grip; the AR(1)-only column is that understatement made explicit.

| series | shape | AR(1)+band (as calibrated) | band only (iid) | AR(1) only | leverage the AR(1) removes |
|---|---|---|---|---|---|
| gis | step | 311.83 | 382.60 | 3056.09 | 1x |
| gis | ramp | 103.39 | 122.77 | 686.52 | 1x |
| dang | step | 2.33 | 2.34 | 344.18 | 1x |
| dang | ramp | 0.82 | 0.83 | 118.75 | 1x |

## The realised correction (actual L10 residuals, not a synthetic shape)

Mean over 1942-1982, cm; residual = model - obs.

| series | residual now | correction applied | residual after | delta logl |
|---|---|---|---|---|
| gis | +0.008 | -0.008 | +0.000 | **+13.44** |
| dang | +0.297 | -0.008 | +0.289 | **+0.08** |

Net over both channels: **+13.52 log-likelihood units** in favour of the Greenland correction.

Net log-likelihood available to the Greenland fix, as calibrated: **+311.83** gained on gis against **-2.33** paid on dang = **+309.51 net** (step), **+102.56 net** (smooth ramp).
