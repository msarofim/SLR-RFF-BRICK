# CMIP6 Greenland amplification vs warming level (zone = south)

- commit `304f99e`; 40 CMIP6 models; scenarios ['ssp126', 'ssp245', 'ssp585']
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

Shape factor S(dT) = R_secant(dT) / R_secant(1.25 K), R_secant(1.25) = 1.478

| dT (K) | S(dT) | amp = S * obs_full |
|---|---|---|
| 1.0 | 1.009 | 1.940 |
| 1.5 | 0.974 | 1.871 |
| 2.0 | 0.926 | 1.781 |
| 2.5 | 0.886 | 1.702 |
| 3.0 | 0.888 | 1.707 |
| 4.0 | 0.893 | 1.716 |
| 5.0 | 0.833 | 1.600 |

