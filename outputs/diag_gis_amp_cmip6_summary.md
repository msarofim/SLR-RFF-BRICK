# CMIP6 Greenland amplification vs warming level (zone = south)

- commit `d59ce12`; 40 CMIP6 models; scenarios ['ssp126', 'ssp245', 'ssp585']
- window 30 yr, anomalies rel 1850-1900, windows dropped if centre < 1950 or mean dT_glob < 0.5 K
- bootstrap over models, 2000 resamples, seed 2026
- observed prior for comparison: south/full **1.922** (the value Ladrillo 1.0 uses), south/modern 1.792

## secant

| dT bin (K) | n models | median amp |
|---|---|---|
| 0.75 | 40 | 1.498 |
| 1.25 | 40 | 1.478 |
| 1.75 | 40 | 1.393 |
| 2.25 | 40 | 1.347 |
| 2.75 | 40 | 1.284 |
| 3.25 | 39 | 1.341 |
| 3.75 | 34 | 1.332 |
| 4.25 | 25 | 1.301 |
| 4.75 | 21 | 1.251 |
| 5.25 | 14 | 1.220 |
| 5.75 | 7 | 1.233 |

- linear slope over warming level: **-0.0503 per K** [95% -0.0792, -0.0120]
- **DECLINING/RISING (CI excludes zero)**

## slope

| dT bin (K) | n models | median amp |
|---|---|---|
| 0.75 | 40 | 1.483 |
| 1.25 | 40 | 1.466 |
| 1.75 | 40 | 1.383 |
| 2.25 | 40 | 1.343 |
| 2.75 | 40 | 1.283 |
| 3.25 | 39 | 1.341 |
| 3.75 | 34 | 1.329 |
| 4.25 | 25 | 1.296 |
| 4.75 | 21 | 1.250 |
| 5.25 | 14 | 1.219 |
| 5.75 | 7 | 1.236 |

- linear slope over warming level: **-0.0487 per K** [95% -0.0789, -0.0096]
- **DECLINING/RISING (CI excludes zero)**

## anchored shape (for ladrillo_gis_driver)

Shape factor S(dT) = R_secant(dT) / R_secant(dT_eff), anchored at the x^2-weighted effective warming level of the observed through-origin fit: **dT_eff = 0.940 K** (python/diag_gis_amp_anchor.py), R_secant(dT_eff) = 1.494.
PCHIP through the pooled binned medians over 0.75-2.75 K, HELD FLAT outside that range (the 3.25 K bump is scenario composition, not physics we trust).

| dT (K) | S(dT) | amp = S * obs_full |
|---|---|---|
| 0.50 | 1.002 | 1.927 |
| 1.00 | 0.998 | 1.919 |
| 0.94 | 1.000 | 1.922 |  <- anchor
| 1.50 | 0.963 | 1.851 |
| 2.00 | 0.916 | 1.762 |
| 2.50 | 0.882 | 1.696 |
| 3.00 | 0.860 | 1.652 |
| 4.00 | 0.860 | 1.652 |
| 5.00 | 0.860 | 1.652 |

- **flat-hold sensitivity arm** `gis_amp_shape_fullcurve`: same construction with the support run to the last populated bin (5.75 K) instead of 2.75 K. S at 3.0/4.0/5.0 K: 0.878/0.883/0.824 vs the held 0.860/0.860/0.860.

- **anchor cross-check:** estimator-matched denominator (CMIP6 median full-window through-origin) = 1.509 vs the dT_eff route's 1.494, a 1.0% difference; S(2.75) would be 0.851 instead of 0.860.

