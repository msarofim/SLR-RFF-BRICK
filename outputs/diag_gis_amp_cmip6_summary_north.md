# CMIP6 Greenland amplification vs warming level (zone = north)

- commit `d59ce12`; 40 CMIP6 models; scenarios ['ssp126', 'ssp245', 'ssp585']
- window 30 yr, anomalies rel 1850-1900, windows dropped if centre < 1950 or mean dT_glob < 0.5 K
- bootstrap over models, 2000 resamples, seed 2026
- observed prior for comparison: south/full **2.828** (the value Ladrillo 1.0 uses), south/modern 2.711

## secant

| dT bin (K) | n models | median amp |
|---|---|---|
| 0.75 | 40 | 1.879 |
| 1.25 | 40 | 1.931 |
| 1.75 | 40 | 1.874 |
| 2.25 | 40 | 1.827 |
| 2.75 | 40 | 1.851 |
| 3.25 | 39 | 1.846 |
| 3.75 | 34 | 1.871 |
| 4.25 | 25 | 1.839 |
| 4.75 | 21 | 1.855 |
| 5.25 | 14 | 1.782 |
| 5.75 | 7 | 1.767 |

- linear slope over warming level: **-0.0195 per K** [95% -0.0390, +0.0069]
- **FLAT (CI includes zero)**

## slope

| dT bin (K) | n models | median amp |
|---|---|---|
| 0.75 | 40 | 1.906 |
| 1.25 | 40 | 1.884 |
| 1.75 | 40 | 1.878 |
| 2.25 | 40 | 1.827 |
| 2.75 | 40 | 1.845 |
| 3.25 | 39 | 1.846 |
| 3.75 | 34 | 1.867 |
| 4.25 | 25 | 1.841 |
| 4.75 | 21 | 1.858 |
| 5.25 | 14 | 1.784 |
| 5.75 | 7 | 1.769 |

- linear slope over warming level: **-0.0186 per K** [95% -0.0353, +0.0068]
- **FLAT (CI includes zero)**

## anchored shape (for ladrillo_gis_driver)

Shape factor S(dT) = R_secant(dT) / R_secant(dT_eff), anchored at the x^2-weighted effective warming level of the observed through-origin fit: **dT_eff = 0.940 K** (python/diag_gis_amp_anchor.py), R_secant(dT_eff) = 1.911.
PCHIP through the pooled binned medians over 0.75-2.75 K, HELD FLAT outside that range (the 3.25 K bump is scenario composition, not physics we trust).

| dT (K) | S(dT) | amp = S * obs_full |
|---|---|---|
| 0.50 | 0.983 | 2.780 |
| 1.00 | 1.004 | 2.838 |
| 0.94 | 1.000 | 2.828 |  <- anchor
| 1.50 | 0.999 | 2.824 |
| 2.00 | 0.965 | 2.729 |
| 2.50 | 0.959 | 2.711 |
| 3.00 | 0.969 | 2.740 |
| 4.00 | 0.969 | 2.740 |
| 5.00 | 0.969 | 2.740 |

- **flat-hold sensitivity arm** `gis_amp_shape_fullcurve`: same construction with the support run to the last populated bin (5.75 K) instead of 2.75 K. S at 3.0/4.0/5.0 K: 0.967/0.971/0.953 vs the held 0.969/0.969/0.969.

