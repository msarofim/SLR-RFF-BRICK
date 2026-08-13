# Confound tests on the CMIP6 Greenland amp(dT) curve

commit `304f99e`; zone = south; 40 models

## Test A -- balanced panel (composition)

Median secant amplification using ONLY models present in every bin up to the cap.

| cap (K) | n models | curve (dT: amp) | monotone decreasing? |
|---|---|---|---|
| 2.75 | 40 | 0.75: 1.498  1.25: 1.478  1.75: 1.393  2.25: 1.347  2.75: 1.284 | **YES** |
| 3.25 | 39 | 0.75: 1.507  1.25: 1.477  1.75: 1.397  2.25: 1.348  2.75: 1.296  3.25: 1.341 | **NO** |
| 3.75 | 34 | 0.75: 1.553  1.25: 1.486  1.75: 1.439  2.25: 1.374  2.75: 1.324  3.25: 1.362  3.75: 1.332 | **NO** |
| 4.25 | 25 | 0.75: 1.543  1.25: 1.575  1.75: 1.442  2.25: 1.382  2.75: 1.363  3.25: 1.389  3.75: 1.339  4.25: 1.301 | **NO** |

## Test B -- the observed prior's own windows, computed on CMIP6

`build_t_gis.amp_through_origin` on historical + ssp245, anomalies rel 1850-1900.

| window | years | CMIP6 median [p05, p95] | observed | observed sd |
|---|---|---|---|---|
| early | 1901-1960 | **1.380** [0.247, 3.853] | 3.604 | 0.689 |
| full | 1901-2024 | **1.509** [0.974, 2.787] | 1.922 | 0.318 |
| modern | 1961-2024 | **1.513** [1.024, 2.808] | 1.792 | 0.303 |

Observed vs the CMIP6 ensemble, in ensemble-sd units:

- **early**: observed 3.604 vs CMIP6 mean 1.719 (sd 1.280) -> **+1.47 sd**; 10% of models exceed the observation
- **full**: observed 1.922 vs CMIP6 mean 1.604 (sd 0.608) -> **+0.52 sd**; 15% of models exceed the observation
- **modern**: observed 1.792 vs CMIP6 mean 1.595 (sd 0.592) -> **+0.33 sd**; 25% of models exceed the observation

### Does CMIP6 reproduce the observed early >> full > modern ordering?

- CMIP6 medians: early 1.380, full 1.509, modern 1.513 -> ordering holds: **False**
- observed: early 3.604, full 1.922, modern 1.792 -> ordering holds: **True**
- CMIP6 early/modern ratio 0.91 vs observed 2.01

