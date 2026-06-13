# Mengel GIC high-temperature melt check — 2018-baseline posterior (10000 draws)

**Verdict: PASS** — committed melt fraction at ΔT=4°C (SSP5-8.5 @2100) = 99.0% (threshold 80% for 'most glaciers').

`gic_b` median = 0.937 [0.728, 0.995] (saturation rate; high → fast saturation → near-complete high-T melt).

## 1. Committed (equilibrium) melt fraction S_eq/a = 1-exp(-b(ΔT - T_lia))

| ΔT (°C) | committed melt % (median [5-95%]) |
|--|--|
| 1.3 | 88.0 [81, 90] |
| 2 | 93.8 [88, 95] |
| 3 | 97.6 [94, 98] |
| 4 | 99.0 [97, 99] |
| 5 | 99.6 [99, 100] |
| 7 | 99.9 [100, 100] |
| 8 | 100.0 [100, 100] |

## 2. Under SSP5-8.5 (GMST 2100=4.7°C, 2200=7.3°C, 2300=7.8°C)

| year | realized S (m) | realized S/a (%) | committed S_eq/a (%) | remaining a-S (m) |
|--|--|--|--|--|
| 2050 | 0.181 [0.162, 0.205] | 52 [42, 61] | 95.3 [91, 96] | 0.162 [0.127, 0.236] |
| 2100 | 0.213 [0.195, 0.237] | 62 [51, 71] | 99.5 [98, 100] | 0.130 [0.096, 0.200] |
| 2200 | 0.248 [0.231, 0.270] | 72 [61, 80] | 100.0 [100, 100] | 0.096 [0.066, 0.159] |
| 2300 | 0.267 [0.249, 0.289] | 77 [67, 85] | 100.0 [100, 100] | 0.078 [0.051, 0.133] |

## 3. Max melt `a` vs physical glacier inventory

`gic_a` = 0.342 m SLE [0.322, 0.410] vs Farinotti 2019 0.324 m [0.24, 0.408] — physically consistent.

**Caveat:** `S_eq`/`a` is relative to the Little-Ice-Age glacier state; the long `gic_tau_slow` means full realization of committed melt lags centuries past 2100 (physically expected for large/cold glaciers). At equilibrium / on multi-century timescales, near-all glacier volume melts at high T.
