# CMIP6 Greenland amplification vs warming level (zone = central)

- commit `d59ce12`; 40 CMIP6 models; scenarios ['ssp126', 'ssp245', 'ssp585']
- window 30 yr, anomalies rel 1850-1900, windows dropped if centre < 1950 or mean dT_glob < 0.5 K
- bootstrap over models, 2000 resamples, seed 2026
- observed prior for comparison: south/full **2.359** (the value Ladrillo 1.0 uses), south/modern 2.240

## secant

| dT bin (K) | n models | median amp |
|---|---|---|
| 0.75 | 40 | 1.710 |
| 1.25 | 40 | 1.693 |
| 1.75 | 40 | 1.597 |
| 2.25 | 40 | 1.587 |
| 2.75 | 40 | 1.548 |
| 3.25 | 39 | 1.571 |
| 3.75 | 34 | 1.579 |
| 4.25 | 25 | 1.597 |
| 4.75 | 21 | 1.581 |
| 5.25 | 14 | 1.518 |
| 5.75 | 7 | 1.558 |

- linear slope over warming level: **-0.0307 per K** [95% -0.0631, -0.0010]
- **DECLINING/RISING (CI excludes zero)**

## slope

| dT bin (K) | n models | median amp |
|---|---|---|
| 0.75 | 40 | 1.658 |
| 1.25 | 40 | 1.682 |
| 1.75 | 40 | 1.598 |
| 2.25 | 40 | 1.586 |
| 2.75 | 40 | 1.547 |
| 3.25 | 39 | 1.575 |
| 3.75 | 34 | 1.587 |
| 4.25 | 25 | 1.594 |
| 4.75 | 21 | 1.574 |
| 5.25 | 14 | 1.518 |
| 5.75 | 7 | 1.557 |

- linear slope over warming level: **-0.0277 per K** [95% -0.0598, -0.0006]
- **DECLINING/RISING (CI excludes zero)**

## anchored shape (for ladrillo_gis_driver)

Shape factor S(dT) = R_secant(dT) / R_secant(dT_eff), anchored at the x^2-weighted effective warming level of the observed through-origin fit: **dT_eff = 0.940 K** (python/diag_gis_amp_anchor.py), R_secant(dT_eff) = 1.707.
PCHIP through the pooled binned medians over 0.75-2.75 K, HELD FLAT outside that range (the 3.25 K bump is scenario composition, not physics we trust).

| dT (K) | S(dT) | amp = S * obs_full |
|---|---|---|
| 0.50 | 1.002 | 2.363 |
| 1.00 | 0.999 | 2.356 |
| 0.94 | 1.000 | 2.359 |  <- anchor
| 1.50 | 0.963 | 2.272 |
| 2.00 | 0.932 | 2.200 |
| 2.50 | 0.921 | 2.173 |
| 3.00 | 0.907 | 2.139 |
| 4.00 | 0.907 | 2.139 |
| 5.00 | 0.907 | 2.139 |

- **flat-hold sensitivity arm** `gis_amp_shape_fullcurve`: same construction with the support run to the last populated bin (5.75 K) instead of 2.75 K. S at 3.0/4.0/5.0 K: 0.913/0.931/0.906 vs the held 0.907/0.907/0.907.

