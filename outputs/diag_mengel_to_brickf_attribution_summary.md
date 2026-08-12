# Gate 3.2 — BRICK-Mengel to BRICK-F*, attributed by component

Medians at 2100, cm, both on FaIR **mean** forcing (parameter spread only) and the 1995-2014 baseline.

## SSP1-2.6

| component | BRICK-Mengel | BRICK-F* | shift |
|---|---|---|---|
| Antarctic | 6.31 | 4.88 | **-1.43** |
| Thermal expansion | 14.08 | 13.18 | **-0.90** |
| Greenland | 6.79 | 6.63 | **-0.16** |
| Land water storage | 2.60 | 2.60 | **+0.00** |
| Glaciers | 5.92 | 8.54 | **+2.62** |
| **TOTAL** | **35.92** | **35.91** | **-0.01** |

## SSP2-4.5

| component | BRICK-Mengel | BRICK-F* | shift |
|---|---|---|---|
| Antarctic | 43.05 | 11.74 | **-31.32** |
| Thermal expansion | 18.45 | 17.27 | **-1.18** |
| Greenland | 7.42 | 7.27 | **-0.15** |
| Land water storage | 2.60 | 2.60 | **+0.00** |
| Glaciers | 6.27 | 10.56 | **+4.29** |
| **TOTAL** | **78.02** | **49.48** | **-28.54** |

## SSP5-8.5

| component | BRICK-Mengel | BRICK-F* | shift |
|---|---|---|---|
| Antarctic | 70.77 | 45.78 | **-24.99** |
| Thermal expansion | 27.68 | 25.91 | **-1.77** |
| Greenland | 8.91 | 8.80 | **-0.11** |
| Land water storage | 2.60 | 2.60 | **+0.00** |
| Glaciers | 6.63 | 14.69 | **+8.06** |
| **TOTAL** | **116.85** | **97.75** | **-19.09** |

## Closure of the decomposition

| ssp | sum of component shifts | total shift | median non-additivity | Antarctic share of total |
|---|---|---|---|---|
| SSP1-2.6 | +0.13 | -0.01 | +0.14 | 17362% |
| SSP2-4.5 | -28.36 | -28.54 | +0.18 | 110% |
| SSP5-8.5 | -18.81 | -19.09 | +0.28 | 131% |

Medians are not additive in general; the non-additivity column is the size of that effect and is small here.

## Robustness to which BRICK-Mengel vintage is meant

| vintage | ssp | Mengel total | BRICK-F\* total | total shift | Antarctic shift | Antarctic share |
|---|---|---|---|---|---|---|
| BRICK-Mengel (base) | SSP1-2.6 | 35.92 | 35.91 | -0.01 | -1.43 | 17362% |
| BRICK-Mengel (base) | SSP2-4.5 | 78.02 | 49.48 | -28.54 | -31.32 | 110% |
| BRICK-Mengel (base) | SSP5-8.5 | 116.85 | 97.75 | -19.09 | -24.99 | 131% |
| BRICK-Mengel (post-2018 ext) | SSP1-2.6 | 34.26 | 35.91 | +1.65 | -0.28 | -17% |
| BRICK-Mengel (post-2018 ext) | SSP2-4.5 | 75.36 | 49.48 | -25.88 | -29.19 | 113% |
| BRICK-Mengel (post-2018 ext) | SSP5-8.5 | 113.35 | 97.75 | -15.60 | -22.36 | 143% |

## Is it a level shift or a median crossing? (Antarctic, by quantile)

| ssp | quantile | BRICK-Mengel | BRICK-F* | shift |
|---|---|---|---|---|
| SSP1-2.6 | p05 | 5.81 | 3.94 | **-1.87** |
| SSP1-2.6 | p50 | 6.31 | 4.88 | **-1.43** |
| SSP1-2.6 | p95 | 46.29 | 6.12 | **-40.16** |
| SSP2-4.5 | p05 | 7.36 | 4.76 | **-2.59** |
| SSP2-4.5 | p50 | 43.05 | 11.74 | **-31.32** |
| SSP2-4.5 | p95 | 73.21 | 59.06 | **-14.15** |
| SSP5-8.5 | p05 | 54.14 | 21.98 | **-32.16** |
| SSP5-8.5 | p50 | 70.77 | 45.78 | **-24.99** |
| SSP5-8.5 | p95 | 86.20 | 80.15 | **-6.05** |

At SSP2-4.5 the median moves -31.3 cm while the tails move -2.6 cm (p05) and -14.1 cm (p95). The Antarctic distribution is bimodal — tipped vs not tipped by 2100 — so the headline shift is mostly the 50th percentile crossing the sparse gap between the two branches, not a uniform reduction in Antarctic mass loss.
