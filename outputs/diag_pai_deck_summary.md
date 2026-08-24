# DECK level-vs-time test (41 models)

Level ratio = 11-yr-smoothed dT_AIS/dT_glob (dT >= 1.0 K), anomalies rel. piControl mean (no drift removal). D = R_abrupt - R_1pct at matched dT, paired by model, bootstrap CI over models.

|    dT |      n |   r_1pct |   yr_1pct |   r_abrupt |   yr_abrupt |      D |   D_lo |   D_hi |
|------:|-------:|---------:|----------:|-----------:|------------:|-------:|-------:|-------:|
| 2.500 | 15.000 |    1.109 |    98.000 |      0.930 |       6.000 | -0.130 | -0.175 | -0.057 |
| 3.000 | 37.000 |    1.097 |    97.000 |      0.955 |       6.000 | -0.124 | -0.186 | -0.100 |
| 3.500 | 39.000 |    1.089 |   108.000 |      1.021 |       9.000 | -0.092 | -0.174 | -0.055 |
| 4.000 | 37.000 |    1.087 |   119.000 |      1.075 |      13.000 | -0.082 | -0.104 | -0.022 |
| 4.500 | 31.000 |    1.153 |   124.000 |      1.106 |      22.000 | -0.078 | -0.130 | -0.029 |

Gregory (abrupt): fast yrs (1, 20), slow (21, 150), late (151, 300); asymptote R means over (100, 150)/(250, 300).

|       |   fast |   slow |   late |   asy150 |   asy300 |
|:------|-------:|-------:|-------:|---------:|---------:|
| 50%   |  1.079 |  1.720 |  1.482 |    1.243 |    1.392 |
| 25%   |  0.937 |  1.318 |  1.264 |    1.130 |    1.290 |
| 75%   |  1.330 |  2.094 |  1.823 |    1.454 |    1.494 |
| count | 41.000 | 41.000 |  3.000 |   41.000 |    2.000 |

Models: ACCESS-CM2, ACCESS-ESM1-5, AWI-CM-1-1-MR, BCC-CSM2-MR, BCC-ESM1, CAMS-CSM1-0, CESM2, CESM2-FV2, CESM2-WACCM, CESM2-WACCM-FV2, CMCC-CM2-SR5, CMCC-ESM2, CNRM-CM6-1, CNRM-CM6-1-HR, CNRM-ESM2-1, CanESM5, E3SM-1-0, EC-Earth3, EC-Earth3-AerChem, EC-Earth3-Veg, FGOALS-g3, GFDL-CM4, GFDL-ESM4, GISS-E2-1-G, GISS-E2-1-H, HadGEM3-GC31-LL, HadGEM3-GC31-MM, INM-CM4-8, INM-CM5-0, IPSL-CM6A-LR, MIROC-ES2L, MIROC6, MPI-ESM-1-2-HAM, MPI-ESM1-2-HR, MPI-ESM1-2-LR, MRI-ESM2-0, NorCPM1, NorESM2-MM, SAM0-UNICON, TaiESM1, UKESM1-0-LL
