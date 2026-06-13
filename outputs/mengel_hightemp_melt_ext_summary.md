# Mengel GIC high-temperature melt check — ext posterior (10000 draws)

**Verdict: PASS** — committed melt fraction at ΔT=4°C (SSP5-8.5 @2100) = 98.7% (threshold 80% for 'most glaciers').

`gic_b` median = 0.880 [0.651, 0.989] (saturation rate; high → fast saturation → near-complete high-T melt).

## 1. Committed (equilibrium) melt fraction S_eq/a = 1-exp(-b(ΔT - T_lia))

| ΔT (°C) | committed melt % (median [5-95%]) |
|--|--|
| 1.3 | 86.0 [77, 89] |
| 2 | 92.5 [85, 95] |
| 3 | 96.9 [92, 98] |
| 4 | 98.7 [96, 99] |
| 5 | 99.5 [98, 100] |
| 7 | 99.9 [99, 100] |
| 8 | 100.0 [100, 100] |

## 2. Under SSP5-8.5 (GMST 2100=4.7°C, 2200=7.3°C, 2300=7.8°C)

| year | realized S (m) | realized S/a (%) | committed S_eq/a (%) | remaining a-S (m) |
|--|--|--|--|--|
| 2050 | 0.185 [0.166, 0.211] | 51 [38, 62] | 94.2 [88, 96] | 0.177 [0.127, 0.283] |
| 2100 | 0.223 [0.203, 0.249] | 61 [47, 73] | 99.3 [97, 100] | 0.140 [0.091, 0.242] |
| 2200 | 0.266 [0.245, 0.295] | 73 [59, 84] | 99.9 [100, 100] | 0.098 [0.053, 0.188] |
| 2300 | 0.288 [0.266, 0.324] | 79 [66, 89] | 100.0 [100, 100] | 0.076 [0.036, 0.154] |

## 3. Max melt `a` vs physical glacier inventory

`gic_a` = 0.364 m SLE [0.324, 0.461] vs Farinotti 2019 0.324 m [0.24, 0.408] — physically consistent.

**Caveat:** `S_eq`/`a` is relative to the Little-Ice-Age glacier state; the long `gic_tau_slow` means full realization of committed melt lags centuries past 2100 (physically expected for large/cold glaciers). At equilibrium / on multi-century timescales, near-all glacier volume melts at high T.
