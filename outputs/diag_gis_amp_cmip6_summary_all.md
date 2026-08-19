# CMIP6 Greenland amplification vs warming level (zone = all)

- commit `3143dd9`; 40 CMIP6 models; scenarios ['ssp126', 'ssp245', 'ssp585']
- window 30 yr, anomalies rel 1850-1900, windows dropped if centre < 1950 or mean dT_glob < 0.5 K
- bootstrap over models, 2000 resamples, seed 2026
- observed prior for comparison: south/full **2.347** (the value Ladrillo 1.0 uses), south/modern 2.225

## secant

| dT bin (K) | n models | median amp |
|---|---|---|
| 0.75 | 40 | 1.659 |
| 1.25 | 40 | 1.680 |
| 1.75 | 40 | 1.623 |
| 2.25 | 40 | 1.581 |
| 2.75 | 40 | 1.525 |
| 3.25 | 39 | 1.572 |
| 3.75 | 34 | 1.589 |
| 4.25 | 25 | 1.582 |
| 4.75 | 21 | 1.531 |
| 5.25 | 14 | 1.486 |
| 5.75 | 7 | 1.477 |

- linear slope over warming level: **-0.0335 per K** [95% -0.0621, -0.0043]
- **DECLINING/RISING (CI excludes zero)**

## slope

| dT bin (K) | n models | median amp |
|---|---|---|
| 0.75 | 40 | 1.682 |
| 1.25 | 40 | 1.662 |
| 1.75 | 40 | 1.625 |
| 2.25 | 40 | 1.559 |
| 2.75 | 40 | 1.527 |
| 3.25 | 39 | 1.558 |
| 3.75 | 34 | 1.591 |
| 4.25 | 25 | 1.578 |
| 4.75 | 21 | 1.526 |
| 5.25 | 14 | 1.487 |
| 5.75 | 7 | 1.479 |

- linear slope over warming level: **-0.0345 per K** [95% -0.0582, -0.0044]
- **DECLINING/RISING (CI excludes zero)**

## anchored shape (for ladrillo_gis_driver)

Shape factor S(dT) = R_secant(dT) / R_secant(dT_eff), anchored at the x^2-weighted effective warming level of the observed through-origin fit: **dT_eff = 0.940 K** (python/diag_gis_amp_anchor.py), R_secant(dT_eff) = 1.674.
PCHIP through the pooled binned medians over 0.75-2.75 K, HELD FLAT outside that range (the 3.25 K bump is scenario composition, not physics we trust).

| dT (K) | S(dT) | amp = S * obs_full |
|---|---|---|
| 0.50 | 0.991 | 2.325 |
| 1.00 | 1.001 | 2.351 |
| 0.94 | 1.000 | 2.347 |  <- anchor
| 1.50 | 0.990 | 2.324 |
| 2.00 | 0.957 | 2.246 |
| 2.50 | 0.928 | 2.179 |
| 3.00 | 0.911 | 2.138 |
| 4.00 | 0.911 | 2.138 |
| 5.00 | 0.911 | 2.138 |

- **flat-hold sensitivity arm** `gis_amp_shape_fullcurve`: same construction with the support run to the last populated bin (5.75 K) instead of 2.75 K. S at 3.0/4.0/5.0 K: 0.923/0.948/0.898 vs the held 0.911/0.911/0.911.

