# Ladrillo benchmark — `L33`

*benchmark v1.0, 2026-09-24, repo `8184651`. Champion arm: **L27**.*

Arms: **candidate** (live `outputs/`), **champion\*** (frozen), **BRICK 2.0** (stock MimiBRICK v2.0.0, own posterior), **literature** (FACTS + MAGICC-SLR, frozen).

**Hindcast ruler:** obs from the **target**, `outputs/recalib_targets_ext.csv` (md5 `eb768cd96463`). Sigma denominators are from the frozen `_fixed` copy in every run, so sigma stays comparable across bench files.

> ⚠ **THE CANDIDATE WAS FITTED TO A DIFFERENT OBSERVATIONAL SERIES THAN IT IS SCORED ON HERE**, so it is OUT-OF-SAMPLE on these components and any arm fitted to the scoring target is IN-SAMPLE. This asymmetry is not corrected for; read it at the gate.
>
> | component | max \|cand−target\| (cm) | mean offset (cm) |
> |---|---|---|
> | glaciers | 0.0381 | -0.0007 |

## Caveats that travel with every verdict

* HINDCAST RANKS IN ONE DIRECTION ONLY -- in-sample for every Ladrillo arm, out-of-sample for BRICK 2.0. It can REJECT an arm; a small fitted bias is not skill.
* BANDS ARE NOT ONE OBJECT -- Ladrillo-fixed is posterior-parameter spread; Ladrillo-JOINT, FACTS and MAGICC carry climate uncertainty. Only the JOINT band is scored against the literature. BRICK 2.0 has a joint arm (scope_slr_fairunc_oldbrick.jl) but this benchmark takes it from the shipped FIXED panel (brick20_projection), so BRICK widths here are fixed-driver; read a BRICK 2.0 width comparison out of ladrillo_model_comparison.py, which does use the joint arm.
* SOME WIDTH IS A PRIOR, NOT AN INFERENCE -- 78% of the ssp585 2300 AIS band is antarctic_lambda's paleo prior, so narrowness is never scored as a win at ais/ssp585.
* WHERE THE OBSERVED STATISTIC IS UNDER 2.0 SIGMA FROM ZERO the RATIO model/obs is suppressed as uninterpretable, but the DIFFERENCE is still graded on z -- being 3 sigma from a value that is itself 1 sigma from zero is still a miss.
* THE MODERN AIS RATE CANNOT REJECT ZERO -- IMBIE whole-sheet loss is 0.95-1.44 sigma from zero, so the 1993-2026 window separates no two AIS models however different they are.
* A p5-p95 SPREAD IS BLIND TO A MODE UNDER 5% OF THE MASS -- cells whose p05-p99/p05-p95 exceeds 2.0x the Gaussian 1.207 are marked N/A(bimodal) and NOT scored on width; quote the mean and the tipped fraction there.
* ssp245@2300 IS A THRESHOLD ARTIFACT -- 48.3% of draws tip, so its MEDIAN is bimodal-fragile. Quote the mean and the tipped fraction there, never the bare median.

## [V] Roll-up

| module | hindcast | rate/accel | projection | separation | vs champion |
|---|---|---|---|---|---|
| **AIS** | WARN | WARN | FAIL | WARN | WORSE |
| **glaciers** | PASS | UNRESOLVED | WARN | PASS | BETTER |
| **Greenland** | WARN | UNRESOLVED | FAIL | WARN | SAME |
| **thermal exp.** | WARN | FAIL | WARN | PASS | SAME |
| **land water** | — | — | WARN | PASS | — |
| **TOTAL** | PASS | UNRESOLVED | WARN | WARN | SAME |

## [H] Hindcast — the full observational period, scaled to each component's own target 1-sigma

| module | target 1σ (cm) | window | arm | RMSE (cm) | RMSE (σ) | note |
|---|---|---|---|---|---|---|
| AIS | 0.1674 | full | L33 | 0.1854 | 1.11 | bias -0.1494 cm = -0.89 sd; cov90 79%; n=126 |
| AIS | 0.1674 | full | L27* | 0.1178 | 0.70 | bias -0.0067 cm = -0.04 sd; cov90 64%; n=126 |
| AIS | 0.1674 | full | BRICK 2.0 | 1.4766 | 8.82 | bias -1.0797 cm = -6.45 sd; cov90 32%; n=126 |
| AIS | 0.1674 | 1920-1949 | L33 | 0.2391 | 1.43 | bias -0.2381 cm = -1.42 sd; cov90 100%; n=30 |
| AIS | 0.1674 | 1920-1949 | L27* | 0.0129 | 0.08 | bias +0.0120 cm = +0.07 sd; cov90 100%; n=30 |
| AIS | 0.1674 | 1920-1949 | BRICK 2.0 | 1.8243 | 10.90 | bias -1.7965 cm = -10.73 sd; cov90 0%; n=30 |
| AIS | 0.1674 | 1950-1992 | L33 | 0.1011 | 0.60 | bias -0.0698 cm = -0.42 sd; cov90 98%; n=43 |
| AIS | 0.1674 | 1950-1992 | L27* | 0.0622 | 0.37 | bias +0.0554 cm = +0.33 sd; cov90 70%; n=43 |
| AIS | 0.1674 | 1950-1992 | BRICK 2.0 | 0.6899 | 4.12 | bias -0.5807 cm = -3.47 sd; cov90 16%; n=43 |
| AIS | 0.1674 | 1993-2026 | L33 | 0.1606 | 0.96 | bias -0.1071 cm = -0.64 sd; cov90 21%; n=33 |
| AIS | 0.1674 | 1993-2026 | L27* | 0.2127 | 1.27 | bias -0.1459 cm = -0.87 sd; cov90 3%; n=33 |
| AIS | 0.1674 | 1993-2026 | BRICK 2.0 | 0.0958 | 0.57 | bias -0.0564 cm = -0.34 sd; cov90 100%; n=33 |
| glaciers | 0.4593 | full | L33 | 0.3111 | 0.68 | bias +0.0540 cm = +0.12 sd; cov90 70%; n=124 |
| glaciers | 0.4593 | full | L27* | 0.3176 | 0.69 | bias +0.0609 cm = +0.13 sd; cov90 69%; n=124 |
| glaciers | 0.4593 | full | BRICK 2.0 | 1.5473 | 3.37 | bias +0.9394 cm = +2.05 sd; cov90 42%; n=124 |
| glaciers | 0.4593 | 1920-1949 | L33 | 0.1791 | 0.39 | bias -0.0092 cm = -0.02 sd; cov90 100%; n=30 |
| glaciers | 0.4593 | 1920-1949 | L27* | 0.1817 | 0.40 | bias +0.0017 cm = +0.00 sd; cov90 100%; n=30 |
| glaciers | 0.4593 | 1920-1949 | BRICK 2.0 | 1.5932 | 3.47 | bias +1.4701 cm = +3.20 sd; cov90 0%; n=30 |
| glaciers | 0.4593 | 1950-1992 | L33 | 0.2324 | 0.51 | bias -0.1175 cm = -0.26 sd; cov90 56%; n=43 |
| glaciers | 0.4593 | 1950-1992 | L27* | 0.2289 | 0.50 | bias -0.1153 cm = -0.25 sd; cov90 56%; n=43 |
| glaciers | 0.4593 | 1950-1992 | BRICK 2.0 | 0.1269 | 0.28 | bias +0.0552 cm = +0.12 sd; cov90 95%; n=43 |
| glaciers | 0.4593 | 1993-2026 | L33 | 0.0491 | 0.11 | bias -0.0238 cm = -0.05 sd; cov90 42%; n=31 |
| glaciers | 0.4593 | 1993-2026 | L27* | 0.0483 | 0.11 | bias -0.0232 cm = -0.05 sd; cov90 39%; n=31 |
| glaciers | 0.4593 | 1993-2026 | BRICK 2.0 | 0.2088 | 0.45 | bias +0.1414 cm = +0.31 sd; cov90 35%; n=31 |
| Greenland | 0.1832 | full | L33 | 0.1960 | 1.07 | bias -0.1421 cm = -0.78 sd; cov90 35%; n=126 |
| Greenland | 0.1832 | full | L27* | 0.1959 | 1.07 | bias -0.1422 cm = -0.78 sd; cov90 35%; n=126 |
| Greenland | 0.1832 | full | BRICK 2.0 | 0.7030 | 3.84 | bias -0.5958 cm = -3.25 sd; cov90 19%; n=126 |
| Greenland | 0.1832 | 1920-1949 | L33 | 0.1982 | 1.08 | bias -0.1496 cm = -0.82 sd; cov90 60%; n=30 |
| Greenland | 0.1832 | 1920-1949 | L27* | 0.1994 | 1.09 | bias -0.1521 cm = -0.83 sd; cov90 60%; n=30 |
| Greenland | 0.1832 | 1920-1949 | BRICK 2.0 | 0.7952 | 4.34 | bias -0.7459 cm = -4.07 sd; cov90 27%; n=30 |
| Greenland | 0.1832 | 1950-1992 | L33 | 0.2676 | 1.46 | bias -0.2494 cm = -1.36 sd; cov90 0%; n=43 |
| Greenland | 0.1832 | 1950-1992 | L27* | 0.2671 | 1.46 | bias -0.2489 cm = -1.36 sd; cov90 0%; n=43 |
| Greenland | 0.1832 | 1950-1992 | BRICK 2.0 | 0.9104 | 4.97 | bias -0.8614 cm = -4.70 sd; cov90 0%; n=43 |
| Greenland | 0.1832 | 1993-2026 | L33 | 0.1256 | 0.69 | bias -0.0855 cm = -0.47 sd; cov90 18%; n=33 |
| Greenland | 0.1832 | 1993-2026 | L27* | 0.1244 | 0.68 | bias -0.0846 cm = -0.46 sd; cov90 18%; n=33 |
| Greenland | 0.1832 | 1993-2026 | BRICK 2.0 | 0.1745 | 0.95 | bias -0.1258 cm = -0.69 sd; cov90 45%; n=33 |
| thermal exp. | 0.3091 | full | L33 | 0.4650 | 1.50 | bias +0.2624 cm = +0.85 sd; cov90 41%; n=126 |
| thermal exp. | 0.3091 | full | L27* | 0.4666 | 1.51 | bias +0.2647 cm = +0.86 sd; cov90 41%; n=126 |
| thermal exp. | 0.3091 | full | BRICK 2.0 | 0.5357 | 1.73 | bias +0.3440 cm = +1.11 sd; cov90 91%; n=126 |
| thermal exp. | 0.3091 | 1920-1949 | L33 | 0.6138 | 1.99 | bias +0.4916 cm = +1.59 sd; cov90 37%; n=30 |
| thermal exp. | 0.3091 | 1920-1949 | L27* | 0.6176 | 2.00 | bias +0.4961 cm = +1.60 sd; cov90 37%; n=30 |
| thermal exp. | 0.3091 | 1920-1949 | BRICK 2.0 | 0.7538 | 2.44 | bias +0.6519 cm = +2.11 sd; cov90 90%; n=30 |
| thermal exp. | 0.3091 | 1950-1992 | L33 | 0.1960 | 0.63 | bias -0.0567 cm = -0.18 sd; cov90 72%; n=43 |
| thermal exp. | 0.3091 | 1950-1992 | L27* | 0.1953 | 0.63 | bias -0.0541 cm = -0.18 sd; cov90 72%; n=43 |
| thermal exp. | 0.3091 | 1950-1992 | BRICK 2.0 | 0.1948 | 0.63 | bias +0.0381 cm = +0.12 sd; cov90 100%; n=43 |
| thermal exp. | 0.3091 | 1993-2026 | L33 | 0.3788 | 1.23 | bias +0.2470 cm = +0.80 sd; cov90 18%; n=33 |
| thermal exp. | 0.3091 | 1993-2026 | L27* | 0.3761 | 1.22 | bias +0.2451 cm = +0.79 sd; cov90 18%; n=33 |
| thermal exp. | 0.3091 | 1993-2026 | BRICK 2.0 | 0.2830 | 0.92 | bias +0.1779 cm = +0.58 sd; cov90 85%; n=33 |
| TOTAL | 1.5380 | full | L33 | 0.3316 | 0.22 | bias +0.0338 cm = +0.02 sd; cov90 81%; n=125 |
| TOTAL | 1.5380 | full | L27* | 0.4026 | 0.26 | bias +0.1831 cm = +0.12 sd; cov90 82%; n=125 |
| TOTAL | 1.5380 | full | BRICK 2.0 | 0.7377 | 0.48 | bias -0.3148 cm = -0.20 sd; cov90 47%; n=125 |
| TOTAL | 1.5380 | 1920-1949 | L33 | 0.3650 | 0.24 | bias -0.0473 cm = -0.03 sd; cov90 97%; n=30 |
| TOTAL | 1.5380 | 1920-1949 | L27* | 0.4308 | 0.28 | bias +0.2106 cm = +0.14 sd; cov90 100%; n=30 |
| TOTAL | 1.5380 | 1920-1949 | BRICK 2.0 | 0.7651 | 0.50 | bias -0.4210 cm = -0.27 sd; cov90 63%; n=30 |
| TOTAL | 1.5380 | 1950-1992 | L33 | 0.2766 | 0.18 | bias -0.1176 cm = -0.08 sd; cov90 91%; n=43 |
| TOTAL | 1.5380 | 1950-1992 | L27* | 0.2141 | 0.14 | bias +0.0136 cm = +0.01 sd; cov90 88%; n=43 |
| TOTAL | 1.5380 | 1950-1992 | BRICK 2.0 | 0.9966 | 0.65 | bias -0.9052 cm = -0.59 sd; cov90 9%; n=43 |
| TOTAL | 1.5380 | 1993-2026 | L33 | 0.2971 | 0.19 | bias +0.1127 cm = +0.07 sd; cov90 41%; n=32 |
| TOTAL | 1.5380 | 1993-2026 | L27* | 0.2710 | 0.18 | bias +0.0754 cm = +0.05 sd; cov90 44%; n=32 |
| TOTAL | 1.5380 | 1993-2026 | BRICK 2.0 | 0.4002 | 0.26 | bias +0.2089 cm = +0.14 sd; cov90 50%; n=32 |

## [R] Rate (1993-2026) and acceleration (1900-2026), with an error bar on the observations

| module | statistic | arm | value | unit | z vs obs bar | note |
|---|---|---|---|---|---|---|
| AIS | rate | observations | 0.041932 | cm/yr | — | se: estimator 0.005832, band-correlated 0.0005689, band-independent 0.003061; CONSERVATIVE 0.005832 cm/yr; |obs|/se = 7.19 |
| AIS | rate | L33 | 0.032243 | cm/yr | -1.66 | 0.77x obs; z=-1.66 vs the obs error bar |
| AIS | rate | L27* | 0.027801 | cm/yr | -2.42 | 0.66x obs; z=-2.42 vs the obs error bar |
| AIS | rate | BRICK 2.0 | 0.03785 | cm/yr | -0.70 | 0.90x obs; z=-0.70 vs the obs error bar |
| glaciers | rate | observations | 0.068013 | cm/yr | — | se: estimator 0.0005236, band-correlated 0.0001274, band-independent 0.009223; CONSERVATIVE 0.009223 cm/yr; |obs|/se = 7.37 |
| glaciers | rate | L33 | 0.06667 | cm/yr | -0.15 | 0.98x obs; z=-0.15 vs the obs error bar |
| glaciers | rate | L27* | 0.066751 | cm/yr | -0.14 | 0.98x obs; z=-0.14 vs the obs error bar |
| glaciers | rate | BRICK 2.0 | 0.087211 | cm/yr | +2.08 | 1.28x obs; z=+2.08 vs the obs error bar |
| Greenland | rate | observations | 0.06596 | cm/yr | — | se: estimator 0.01044, band-correlated 0.0006502, band-independent 0.003349; CONSERVATIVE 0.01044 cm/yr; |obs|/se = 6.32 |
| Greenland | rate | L33 | 0.058611 | cm/yr | -0.70 | 0.89x obs; z=-0.70 vs the obs error bar |
| Greenland | rate | L27* | 0.058715 | cm/yr | -0.69 | 0.89x obs; z=-0.69 vs the obs error bar |
| Greenland | rate | BRICK 2.0 | 0.057934 | cm/yr | -0.77 | 0.88x obs; z=-0.77 vs the obs error bar |
| thermal exp. | rate | observations | 0.1234 | cm/yr | — | se: estimator 0.003756, band-correlated 0.002392, band-independent 0.005651; CONSERVATIVE 0.005651 cm/yr; |obs|/se = 21.84 |
| thermal exp. | rate | L33 | 0.15244 | cm/yr | +5.14 | 1.24x obs UNCORRECTED, 1.12x at the FULL depth-scope bound; z spans +2.91..+5.14. Model is FULL-DEPTH, target is 0-2000 m; factor <= 1.1022 from IGCC ocean_2000-6000m (PRESCRIBED 1.15 ZJ/yr, not data), and it OVERSTATES the correction because deep water expands less per joule. NOT applied to accel: a prescribed constant rate carries no curvature. |
| thermal exp. | rate | L27* | 0.15222 | cm/yr | +5.10 | 1.23x obs UNCORRECTED, 1.12x at the FULL depth-scope bound; z spans +2.87..+5.10. Model is FULL-DEPTH, target is 0-2000 m; factor <= 1.1022 from IGCC ocean_2000-6000m (PRESCRIBED 1.15 ZJ/yr, not data), and it OVERSTATES the correction because deep water expands less per joule. NOT applied to accel: a prescribed constant rate carries no curvature. |
| thermal exp. | rate | BRICK 2.0 | 0.14458 | cm/yr | +3.75 | 1.17x obs UNCORRECTED, 1.06x at the FULL depth-scope bound; z spans +1.52..+3.75. Model is FULL-DEPTH, target is 0-2000 m; factor <= 1.1022 from IGCC ocean_2000-6000m (PRESCRIBED 1.15 ZJ/yr, not data), and it OVERSTATES the correction because deep water expands less per joule. NOT applied to accel: a prescribed constant rate carries no curvature. |
| TOTAL | rate | observations | 0.32469 | cm/yr | — | se: estimator 0.02949, band-correlated 0.02545, band-independent 0.02945; CONSERVATIVE 0.02949 cm/yr; |obs|/se = 11.01 |
| TOTAL | rate | L33 | 0.34068 | cm/yr | +0.54 | 1.05x obs; z=+0.54 vs the obs error bar |
| TOTAL | rate | L27* | 0.3361 | cm/yr | +0.39 | 1.04x obs; z=+0.39 vs the obs error bar |
| TOTAL | rate | BRICK 2.0 | 0.35585 | cm/yr | +1.06 | 1.10x obs; z=+1.06 vs the obs error bar |
| AIS | accel | observations | 0.00031296 | cm/yr2 | — | se: estimator 0.0002581, band-correlated 3.924e-05, band-independent 2.522e-05; CONSERVATIVE 0.0002581 cm/yr2; |obs|/se = 1.21 |
| AIS | accel | L33 | 0.00024062 | cm/yr2 | -0.28 | ratio NOT INTERPRETABLE (obs is 1.21 se from zero); z=-0.28 vs the obs error bar |
| AIS | accel | L27* | 0.00021744 | cm/yr2 | -0.37 | ratio NOT INTERPRETABLE (obs is 1.21 se from zero); z=-0.37 vs the obs error bar |
| AIS | accel | BRICK 2.0 | -0.00012334 | cm/yr2 | -1.69 | ratio NOT INTERPRETABLE (obs is 1.21 se from zero); z=-1.69 vs the obs error bar |
| glaciers | accel | observations | -0.00054814 | cm/yr2 | — | se: estimator 0.000447, band-correlated 3.442e-05, band-independent 7.199e-05; CONSERVATIVE 0.000447 cm/yr2; |obs|/se = 1.23 |
| glaciers | accel | L33 | -0.00017215 | cm/yr2 | +0.84 | ratio NOT INTERPRETABLE (obs is 1.23 se from zero); z=+0.84 vs the obs error bar |
| glaciers | accel | L27* | -0.00016692 | cm/yr2 | +0.85 | ratio NOT INTERPRETABLE (obs is 1.23 se from zero); z=+0.85 vs the obs error bar |
| glaciers | accel | BRICK 2.0 | 0.00063496 | cm/yr2 | +2.65 | ratio NOT INTERPRETABLE (obs is 1.23 se from zero); z=+2.65 vs the obs error bar |
| Greenland | accel | observations | -0.00027825 | cm/yr2 | — | se: estimator 0.0005241, band-correlated 6.83e-05, band-independent 2.759e-05; CONSERVATIVE 0.0005241 cm/yr2; |obs|/se = 0.53 |
| Greenland | accel | L33 | -0.000129 | cm/yr2 | +0.28 | ratio NOT INTERPRETABLE (obs is 0.53 se from zero); z=+0.28 vs the obs error bar |
| Greenland | accel | L27* | -0.00012804 | cm/yr2 | +0.29 | ratio NOT INTERPRETABLE (obs is 0.53 se from zero); z=+0.29 vs the obs error bar |
| Greenland | accel | BRICK 2.0 | 0.00010691 | cm/yr2 | +0.73 | ratio NOT INTERPRETABLE (obs is 0.53 se from zero); z=+0.73 vs the obs error bar |
| thermal exp. | accel | observations | 0.0008428 | cm/yr2 | — | se: estimator 0.0002431, band-correlated 2.312e-05, band-independent 4.655e-05; CONSERVATIVE 0.0002431 cm/yr2; |obs|/se = 3.47 |
| thermal exp. | accel | L33 | 0.0012405 | cm/yr2 | +1.64 | 1.47x obs; z=+1.64 vs the obs error bar |
| thermal exp. | accel | L27* | 0.0012388 | cm/yr2 | +1.63 | 1.47x obs; z=+1.63 vs the obs error bar |
| thermal exp. | accel | BRICK 2.0 | 0.0011766 | cm/yr2 | +1.37 | 1.40x obs; z=+1.37 vs the obs error bar |
| TOTAL | accel | observations | 0.00089376 | cm/yr2 | — | se: estimator 0.001159, band-correlated 0.0001276, band-independent 0.0002363; CONSERVATIVE 0.001159 cm/yr2; |obs|/se = 0.77 |
| TOTAL | accel | L33 | 0.0013591 | cm/yr2 | +0.40 | ratio NOT INTERPRETABLE (obs is 0.77 se from zero); z=+0.40 vs the obs error bar |
| TOTAL | accel | L27* | 0.0013314 | cm/yr2 | +0.38 | ratio NOT INTERPRETABLE (obs is 0.77 se from zero); z=+0.38 vs the obs error bar |
| TOTAL | accel | BRICK 2.0 | 0.0019643 | cm/yr2 | +0.92 | ratio NOT INTERPRETABLE (obs is 0.77 se from zero); z=+0.92 vs the obs error bar |

## [P] Projections vs the literature — scored on the JOINT band

| module | ssp | horizon | metric | value | verdict | note |
|---|---|---|---|---|---|---|
| AIS | ssp126 | 2100 | median_vs_lit | 0.631 x lit median | **PASS** | ours 5.70 cm vs lit 3.66-11.93 (median 9.04), n_lit=5 [1 SEJ comparator(s) excluded from the score; full range 3.66-11.93] |
| AIS | ssp126 | 2100 | median_vs_lit | 0.478 x lit median | **PASS** | BRICK 2.0 4.32 cm vs the same lit median 9.04; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp126 | 2100 | spread_vs_lit | 2.233 x lit spread | **FAIL** | ours 47.78 cm vs model-based lit 20.72-40.49 (median 21.40, n=5); ALL comparators 20.72-105.01 |
| AIS | ssp126 | 2150 | median_vs_lit | 0.601 x lit median | **PASS** | ours 8.82 cm vs lit 5.34-24.01 (median 14.67), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| AIS | ssp126 | 2150 | median_vs_lit | 0.445 x lit median | **PASS** | BRICK 2.0 6.52 cm vs the same lit median 14.67; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp126 | 2150 | spread_vs_lit | 1.673 x lit spread | **PASS** | ours 87.16 cm vs model-based lit 33.17-71.04 (median 52.10, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| AIS | ssp126 | 2300 | median_vs_lit | 1.993 x lit median | **WARN** | ours 17.35 cm vs lit 8.71-8.71 (median 8.71), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| AIS | ssp126 | 2300 | median_vs_lit | 1.495 x lit median | **WARN** | BRICK 2.0 13.01 cm vs the same lit median 8.71; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp126 | 2300 | spread_vs_lit | 3.058 x lit spread | **WARN** | ours 212.85 cm vs model-based lit 69.60-69.60 (median 69.60, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |
| AIS | ssp245 | 2100 | median_vs_lit | 1.003 x lit median | **PASS** | ours 10.52 cm vs lit 5.22-12.17 (median 10.49), n_lit=5 [1 SEJ comparator(s) excluded from the score; full range 5.22-12.17] |
| AIS | ssp245 | 2100 | median_vs_lit | 2.613 x lit median | **FAIL** | BRICK 2.0 27.41 cm vs the same lit median 10.49; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp245 | 2100 | spread_vs_lit | 1.546 x lit spread | **PASS** | ours 55.38 cm vs model-based lit 20.77-42.39 (median 35.81, n=5); ALL comparators 20.77-113.21 |
| AIS | ssp245 | 2150 | median_vs_lit | 1.708 x lit median | **WARN** | ours 46.64 cm vs lit 27.21-27.41 (median 27.31), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| AIS | ssp245 | 2150 | median_vs_lit | 2.658 x lit median | **WARN** | BRICK 2.0 72.60 cm vs the same lit median 27.31; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp245 | 2150 | spread_vs_lit | 1.352 x lit spread | **PASS** | ours 115.43 cm vs model-based lit 80.10-90.72 (median 85.41, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| AIS | ssp245 | 2300 | median_vs_lit | 1.867 x lit median | **WARN** | ours 155.85 cm vs lit 83.46-83.46 (median 83.46), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| AIS | ssp245 | 2300 | median_vs_lit | 2.468 x lit median | **WARN** | BRICK 2.0 205.94 cm vs the same lit median 83.46; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp245 | 2300 | spread_vs_lit | 1.150 x lit spread | **PASS** | ours 312.38 cm vs model-based lit 271.56-271.56 (median 271.56, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| AIS | ssp585 | 2100 | median_vs_lit | 2.852 x lit median | **PASS** | ours 37.63 cm vs lit 4.30-39.10 (median 13.20), n_lit=5 [1 SEJ comparator(s) excluded from the score; full range 4.30-39.10] |
| AIS | ssp585 | 2100 | median_vs_lit | 3.345 x lit median | **FAIL** | BRICK 2.0 44.14 cm vs the same lit median 13.20; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp585 | 2100 | spread_vs_lit | 1.255 x lit spread | **PASS** | ours 64.52 cm vs model-based lit 20.71-79.00 (median 51.40, n=5); ALL comparators 20.71-126.10; width here is the antarctic_lambda PRIOR -- do NOT narrow |
| AIS | ssp585 | 2150 | median_vs_lit | 0.992 x lit median | **PASS** | ours 93.18 cm vs lit 34.31-153.62 (median 93.97), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| AIS | ssp585 | 2150 | median_vs_lit | 1.042 x lit median | **PASS** | BRICK 2.0 97.88 cm vs the same lit median 93.97; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp585 | 2150 | spread_vs_lit | 0.532 x lit spread | **PASS** | ours 106.77 cm vs model-based lit 125.28-276.23 (median 200.75, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; width here is the antarctic_lambda PRIOR -- do NOT narrow |
| AIS | ssp585 | 2300 | median_vs_lit | 1.034 x lit median | **PASS** | ours 282.24 cm vs lit 267.00-712.02 (median 273.00), n_lit=3 |
| AIS | ssp585 | 2300 | median_vs_lit | 1.014 x lit median | **PASS** | BRICK 2.0 276.83 cm vs the same lit median 273.00; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp585 | 2300 | spread_vs_lit | 0.325 x lit spread | **WARN** | ours 306.99 cm vs model-based lit 944.94-944.94 (median 944.94, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; width here is the antarctic_lambda PRIOR -- do NOT narrow |
| glaciers | ssp126 | 2100 | median_vs_lit | 0.785 x lit median | **WARN** | ours 8.13 cm vs lit 9.72-10.45 (median 10.36), n_lit=3 |
| glaciers | ssp126 | 2100 | median_vs_lit | 1.167 x lit median | **WARN** | BRICK 2.0 12.09 cm vs the same lit median 10.36; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp126 | 2100 | spread_vs_lit | 0.643 x lit spread | **PASS** | ours 4.97 cm vs model-based lit 7.12-10.06 (median 7.74, n=3) |
| glaciers | ssp126 | 2150 | median_vs_lit | 0.773 x lit median | **WARN** | ours 10.00 cm vs lit 12.28-13.60 (median 12.94), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp126 | 2150 | median_vs_lit | 1.348 x lit median | **WARN** | BRICK 2.0 17.44 cm vs the same lit median 12.94; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp126 | 2150 | spread_vs_lit | 0.562 x lit spread | **PASS** | ours 6.74 cm vs model-based lit 8.52-15.46 (median 11.99, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| glaciers | ssp126 | 2300 | median_vs_lit | 0.685 x lit median | **WARN** | ours 12.55 cm vs lit 13.80-22.85 (median 18.33), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp126 | 2300 | median_vs_lit | 1.512 x lit median | **WARN** | BRICK 2.0 27.72 cm vs the same lit median 18.33; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp126 | 2300 | spread_vs_lit | 0.598 x lit spread | **PASS** | ours 9.72 cm vs model-based lit 11.23-21.30 (median 16.26, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| glaciers | ssp245 | 2100 | median_vs_lit | 0.776 x lit median | **WARN** | ours 9.73 cm vs lit 11.22-12.90 (median 12.54), n_lit=3 |
| glaciers | ssp245 | 2100 | median_vs_lit | 1.064 x lit median | **WARN** | BRICK 2.0 13.34 cm vs the same lit median 12.54; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp245 | 2100 | spread_vs_lit | 0.688 x lit spread | **PASS** | ours 5.76 cm vs model-based lit 7.42-11.15 (median 8.38, n=3) |
| glaciers | ssp245 | 2150 | median_vs_lit | 0.775 x lit median | **WARN** | ours 13.38 cm vs lit 16.71-17.82 (median 17.27), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp245 | 2150 | median_vs_lit | 1.198 x lit median | **WARN** | BRICK 2.0 20.69 cm vs the same lit median 17.27; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp245 | 2150 | spread_vs_lit | 0.600 x lit spread | **PASS** | ours 8.68 cm vs model-based lit 9.16-19.79 (median 14.47, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| glaciers | ssp245 | 2300 | median_vs_lit | 0.680 x lit median | **WARN** | ours 18.04 cm vs lit 21.47-31.57 (median 26.52), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp245 | 2300 | median_vs_lit | 1.226 x lit median | **WARN** | BRICK 2.0 32.50 cm vs the same lit median 26.52; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp245 | 2300 | spread_vs_lit | 0.968 x lit spread | **PASS** | ours 12.23 cm vs model-based lit 10.95-14.32 (median 12.63, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| glaciers | ssp585 | 2100 | median_vs_lit | 0.840 x lit median | **WARN** | ours 12.85 cm vs lit 13.93-17.13 (median 15.30), n_lit=3 |
| glaciers | ssp585 | 2100 | median_vs_lit | 1.020 x lit median | **PASS** | BRICK 2.0 15.61 cm vs the same lit median 15.30; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp585 | 2100 | spread_vs_lit | 0.798 x lit spread | **PASS** | ours 7.26 cm vs model-based lit 8.51-14.02 (median 9.10, n=3) |
| glaciers | ssp585 | 2150 | median_vs_lit | 0.834 x lit median | **WARN** | ours 20.13 cm vs lit 22.03-26.22 (median 24.13), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp585 | 2150 | median_vs_lit | 1.088 x lit median | **WARN** | BRICK 2.0 26.25 cm vs the same lit median 24.13; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp585 | 2150 | spread_vs_lit | 0.768 x lit spread | **PASS** | ours 10.42 cm vs model-based lit 10.09-17.06 (median 13.58, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| glaciers | ssp585 | 2300 | median_vs_lit | 0.866 x lit median | **WARN** | ours 26.28 cm vs lit 29.10-31.57 (median 30.34), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp585 | 2300 | median_vs_lit | 1.166 x lit median | **WARN** | BRICK 2.0 35.36 cm vs the same lit median 30.34; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp585 | 2300 | spread_vs_lit | 2.262 x lit spread | **WARN** | ours 11.27 cm vs model-based lit 0.13-9.83 (median 4.98, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |
| Greenland | ssp126 | 2100 | median_vs_lit | 0.976 x lit median | **WARN** | ours 6.25 cm vs lit 6.36-8.31 (median 6.40), n_lit=3 [1 SEJ comparator(s) excluded from the score; full range 6.36-13.80] |
| Greenland | ssp126 | 2100 | median_vs_lit | 1.034 x lit median | **PASS** | BRICK 2.0 6.62 cm vs the same lit median 6.40; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp126 | 2100 | spread_vs_lit | 0.392 x lit spread | **FAIL** | ours 3.75 cm vs model-based lit 8.22-17.86 (median 9.57, n=3); ALL comparators 8.22-68.88 |
| Greenland | ssp126 | 2150 | median_vs_lit | 0.894 x lit median | **WARN** | ours 8.32 cm vs lit 9.31-9.31 (median 9.31), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp126 | 2150 | median_vs_lit | 1.074 x lit median | **WARN** | BRICK 2.0 10.01 cm vs the same lit median 9.31; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp126 | 2150 | spread_vs_lit | 0.399 x lit spread | **WARN** | ours 6.26 cm vs model-based lit 15.69-15.69 (median 15.69, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |
| Greenland | ssp126 | 2300 | median_vs_lit | 0.785 x lit median | **WARN** | ours 11.76 cm vs lit 14.98-14.98 (median 14.98), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp126 | 2300 | median_vs_lit | 1.271 x lit median | **WARN** | BRICK 2.0 19.04 cm vs the same lit median 14.98; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp126 | 2300 | spread_vs_lit | 0.405 x lit spread | **WARN** | ours 11.91 cm vs model-based lit 29.41-29.41 (median 29.41, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |
| Greenland | ssp245 | 2100 | median_vs_lit | 0.788 x lit median | **WARN** | ours 7.31 cm vs lit 8.12-9.59 (median 9.28), n_lit=3 [1 SEJ comparator(s) excluded from the score; full range 8.12-14.49] |
| Greenland | ssp245 | 2100 | median_vs_lit | 0.757 x lit median | **WARN** | BRICK 2.0 7.03 cm vs the same lit median 9.28; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp245 | 2100 | spread_vs_lit | 0.565 x lit spread | **PASS** | ours 4.72 cm vs model-based lit 7.77-17.73 (median 8.35, n=3); ALL comparators 7.77-77.52 |
| Greenland | ssp245 | 2150 | median_vs_lit | 0.676 x lit median | **WARN** | ours 11.17 cm vs lit 16.53-16.53 (median 16.53), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp245 | 2150 | median_vs_lit | 0.686 x lit median | **WARN** | BRICK 2.0 11.35 cm vs the same lit median 16.53; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp245 | 2150 | spread_vs_lit | 0.683 x lit spread | **PASS** | ours 10.17 cm vs model-based lit 14.88-14.88 (median 14.88, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| Greenland | ssp245 | 2300 | median_vs_lit | 0.505 x lit median | **WARN** | ours 18.09 cm vs lit 35.79-35.79 (median 35.79), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp245 | 2300 | median_vs_lit | 0.662 x lit median | **WARN** | BRICK 2.0 23.71 cm vs the same lit median 35.79; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp245 | 2300 | spread_vs_lit | 0.700 x lit spread | **PASS** | ours 28.64 cm vs model-based lit 40.91-40.91 (median 40.91, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| Greenland | ssp585 | 2100 | median_vs_lit | 0.799 x lit median | **WARN** | ours 9.77 cm vs lit 11.67-13.49 (median 12.23), n_lit=3 [1 SEJ comparator(s) excluded from the score; full range 11.67-17.18] |
| Greenland | ssp585 | 2100 | median_vs_lit | 0.644 x lit median | **WARN** | BRICK 2.0 7.88 cm vs the same lit median 12.23; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp585 | 2100 | spread_vs_lit | 0.666 x lit spread | **PASS** | ours 8.10 cm vs model-based lit 8.46-18.27 (median 12.15, n=3); ALL comparators 8.46-81.93 |
| Greenland | ssp585 | 2150 | median_vs_lit | 0.659 x lit median | **WARN** | ours 21.35 cm vs lit 32.40-32.40 (median 32.40), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp585 | 2150 | median_vs_lit | 0.456 x lit median | **WARN** | BRICK 2.0 14.77 cm vs the same lit median 32.40; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp585 | 2150 | spread_vs_lit | 0.303 x lit spread | **WARN** | ours 27.55 cm vs model-based lit 90.97-90.97 (median 90.97, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |
| Greenland | ssp585 | 2300 | median_vs_lit | 0.709 x lit median | **WARN** | ours 80.08 cm vs lit 113.01-113.01 (median 113.01), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp585 | 2300 | median_vs_lit | 0.342 x lit median | **WARN** | BRICK 2.0 38.60 cm vs the same lit median 113.01; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp585 | 2300 | spread_vs_lit | 0.159 x lit spread | **WARN** | ours 108.42 cm vs model-based lit 680.24-680.24 (median 680.24, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |
| thermal exp. | ssp126 | 2100 | median_vs_lit | 1.130 x lit median | **PASS** | ours 15.75 cm vs lit 11.09-16.79 (median 13.94), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp126 | 2100 | median_vs_lit | 1.100 x lit median | **PASS** | BRICK 2.0 15.34 cm vs the same lit median 13.94; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp126 | 2100 | spread_vs_lit | 0.935 x lit spread | **PASS** | ours 12.21 cm vs model-based lit 11.97-14.17 (median 13.07, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp126 | 2150 | median_vs_lit | 1.168 x lit median | **PASS** | ours 19.65 cm vs lit 12.68-20.97 (median 16.83), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp126 | 2150 | median_vs_lit | 1.140 x lit median | **PASS** | BRICK 2.0 19.18 cm vs the same lit median 16.83; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp126 | 2150 | spread_vs_lit | 0.976 x lit spread | **PASS** | ours 17.53 cm vs model-based lit 16.06-19.84 (median 17.95, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp126 | 2300 | median_vs_lit | 1.148 x lit median | **PASS** | ours 25.00 cm vs lit 16.74-26.81 (median 21.77), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp126 | 2300 | median_vs_lit | 1.152 x lit median | **PASS** | BRICK 2.0 25.08 cm vs the same lit median 21.77; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp126 | 2300 | spread_vs_lit | 1.021 x lit spread | **PASS** | ours 29.10 cm vs model-based lit 25.47-31.53 (median 28.50, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp245 | 2100 | median_vs_lit | 1.058 x lit median | **PASS** | ours 20.00 cm vs lit 16.62-21.18 (median 18.90), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp245 | 2100 | median_vs_lit | 1.025 x lit median | **PASS** | BRICK 2.0 19.37 cm vs the same lit median 18.90; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp245 | 2100 | spread_vs_lit | 0.888 x lit spread | **PASS** | ours 14.11 cm vs model-based lit 15.26-16.52 (median 15.89, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp245 | 2150 | median_vs_lit | 1.081 x lit median | **PASS** | ours 29.22 cm vs lit 23.23-30.82 (median 27.03), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp245 | 2150 | median_vs_lit | 1.056 x lit median | **PASS** | BRICK 2.0 28.53 cm vs the same lit median 27.03; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp245 | 2150 | spread_vs_lit | 0.883 x lit spread | **PASS** | ours 23.96 cm vs model-based lit 25.87-28.40 (median 27.13, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp245 | 2300 | median_vs_lit | 1.073 x lit median | **PASS** | ours 44.82 cm vs lit 36.30-47.22 (median 41.76), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp245 | 2300 | median_vs_lit | 1.069 x lit median | **PASS** | BRICK 2.0 44.66 cm vs the same lit median 41.76; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp245 | 2300 | spread_vs_lit | 0.880 x lit spread | **PASS** | ours 47.37 cm vs model-based lit 53.37-54.25 (median 53.81, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp585 | 2100 | median_vs_lit | 0.979 x lit median | **PASS** | ours 27.98 cm vs lit 27.88-29.29 (median 28.59), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp585 | 2100 | median_vs_lit | 0.947 x lit median | **WARN** | BRICK 2.0 27.07 cm vs the same lit median 28.59; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp585 | 2100 | spread_vs_lit | 0.827 x lit spread | **PASS** | ours 18.82 cm vs model-based lit 22.64-22.88 (median 22.76, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp585 | 2150 | median_vs_lit | 0.992 x lit median | **PASS** | ours 51.59 cm vs lit 49.94-54.12 (median 52.03), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp585 | 2150 | median_vs_lit | 0.968 x lit median | **PASS** | BRICK 2.0 50.34 cm vs the same lit median 52.03; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp585 | 2150 | spread_vs_lit | 0.825 x lit spread | **PASS** | ours 39.00 cm vs model-based lit 46.46-48.08 (median 47.27, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp585 | 2300 | median_vs_lit | 0.965 x lit median | **WARN** | ours 102.67 cm vs lit 103.49-109.39 (median 106.44), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| thermal exp. | ssp585 | 2300 | median_vs_lit | 0.957 x lit median | **WARN** | BRICK 2.0 101.88 cm vs the same lit median 106.44; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp585 | 2300 | spread_vs_lit | 0.826 x lit spread | **PASS** | ours 99.09 cm vs model-based lit 118.64-121.40 (median 120.02, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| land water | ssp126 | 2100 | median_vs_lit | 0.938 x lit median | **WARN** | ours 2.81 cm vs lit 2.99-3.01 (median 3.00), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp126 | 2100 | median_vs_lit | 0.781 x lit median | **WARN** | BRICK 2.0 2.34 cm vs the same lit median 3.00; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp126 | 2100 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 3.64-4.06 (median 3.85, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp126 | 2150 | median_vs_lit | 0.904 x lit median | **WARN** | ours 4.31 cm vs lit 4.58-4.96 (median 4.77), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp126 | 2150 | median_vs_lit | 0.847 x lit median | **WARN** | BRICK 2.0 4.04 cm vs the same lit median 4.77; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp126 | 2150 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 5.64-5.78 (median 5.71, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp126 | 2300 | median_vs_lit | 0.978 x lit median | **PASS** | ours 8.81 cm vs lit 7.25-10.78 (median 9.01), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| land water | ssp126 | 2300 | median_vs_lit | 0.987 x lit median | **PASS** | BRICK 2.0 8.90 cm vs the same lit median 9.01; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp126 | 2300 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 8.70-12.12 (median 10.41, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp245 | 2100 | median_vs_lit | 0.919 x lit median | **WARN** | ours 2.81 cm vs lit 3.01-3.11 (median 3.06), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp245 | 2100 | median_vs_lit | 0.765 x lit median | **WARN** | BRICK 2.0 2.34 cm vs the same lit median 3.06; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp245 | 2100 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 3.64-4.48 (median 4.06, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp245 | 2150 | median_vs_lit | 0.849 x lit median | **WARN** | ours 4.31 cm vs lit 4.96-5.20 (median 5.08), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp245 | 2150 | median_vs_lit | 0.796 x lit median | **WARN** | BRICK 2.0 4.04 cm vs the same lit median 5.08; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp245 | 2150 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 5.78-6.87 (median 6.33, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp245 | 2300 | median_vs_lit | 0.804 x lit median | **WARN** | ours 8.81 cm vs lit 10.78-11.14 (median 10.96), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp245 | 2300 | median_vs_lit | 0.812 x lit median | **WARN** | BRICK 2.0 8.90 cm vs the same lit median 10.96; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp245 | 2300 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 12.12-13.82 (median 12.97, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp585 | 2100 | median_vs_lit | 0.944 x lit median | **WARN** | ours 2.81 cm vs lit 2.96-3.01 (median 2.98), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp585 | 2100 | median_vs_lit | 0.786 x lit median | **WARN** | BRICK 2.0 2.34 cm vs the same lit median 2.98; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp585 | 2100 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 3.64-4.12 (median 3.88, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp585 | 2150 | median_vs_lit | 0.892 x lit median | **WARN** | ours 4.31 cm vs lit 4.70-4.96 (median 4.83), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp585 | 2150 | median_vs_lit | 0.836 x lit median | **WARN** | BRICK 2.0 4.04 cm vs the same lit median 4.83; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp585 | 2150 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 5.78-5.80 (median 5.79, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp585 | 2300 | median_vs_lit | 0.963 x lit median | **PASS** | ours 8.81 cm vs lit 7.53-10.78 (median 9.16), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| land water | ssp585 | 2300 | median_vs_lit | 0.972 x lit median | **PASS** | BRICK 2.0 8.90 cm vs the same lit median 9.16; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp585 | 2300 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 9.04-12.12 (median 10.58, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| TOTAL | ssp126 | 2100 | median_vs_lit | 0.854 x lit median | **PASS** | ours 39.01 cm vs lit 35.59-50.06 (median 45.68), n_lit=7 [1 SEJ comparator(s) excluded from the score; full range 35.59-55.88] |
| TOTAL | ssp126 | 2100 | median_vs_lit | 0.901 x lit median | **PASS** | BRICK 2.0 41.16 cm vs the same lit median 45.68; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp126 | 2100 | spread_vs_lit | 1.325 x lit spread | **PASS** | ours 61.39 cm vs model-based lit 32.73-55.62 (median 46.34, n=7); ALL comparators 32.73-125.52 |
| TOTAL | ssp126 | 2150 | median_vs_lit | 1.125 x lit median | **WARN** | ours 51.68 cm vs lit 45.94-45.94 (median 45.94), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| TOTAL | ssp126 | 2150 | median_vs_lit | 1.260 x lit median | **WARN** | BRICK 2.0 57.89 cm vs the same lit median 45.94; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp126 | 2150 | spread_vs_lit | 1.856 x lit spread | **PASS** | ours 109.47 cm vs model-based lit 58.97-58.97 (median 58.97, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| TOTAL | ssp126 | 2300 | median_vs_lit | 1.157 x lit median | **WARN** | ours 76.94 cm vs lit 66.49-66.49 (median 66.49), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| TOTAL | ssp126 | 2300 | median_vs_lit | 1.425 x lit median | **WARN** | BRICK 2.0 94.76 cm vs the same lit median 66.49; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp126 | 2300 | spread_vs_lit | 2.120 x lit spread | **WARN** | ours 247.17 cm vs model-based lit 116.60-116.60 (median 116.60, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |
| TOTAL | ssp245 | 2100 | median_vs_lit | 0.955 x lit median | **PASS** | ours 52.75 cm vs lit 49.78-58.27 (median 55.25), n_lit=7 [1 SEJ comparator(s) excluded from the score; full range 49.78-67.77] |
| TOTAL | ssp245 | 2100 | median_vs_lit | 1.270 x lit median | **WARN** | BRICK 2.0 70.19 cm vs the same lit median 55.25; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp245 | 2100 | spread_vs_lit | 1.302 x lit spread | **PASS** | ours 69.47 cm vs model-based lit 35.22-64.58 (median 53.36, n=7); ALL comparators 35.22-151.34 |
| TOTAL | ssp245 | 2150 | median_vs_lit | 1.191 x lit median | **WARN** | ours 104.92 cm vs lit 88.11-88.11 (median 88.11), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| TOTAL | ssp245 | 2150 | median_vs_lit | 1.566 x lit median | **WARN** | BRICK 2.0 137.98 cm vs the same lit median 88.11; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp245 | 2150 | spread_vs_lit | 1.280 x lit spread | **PASS** | ours 138.71 cm vs model-based lit 108.33-108.33 (median 108.33, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| TOTAL | ssp245 | 2300 | median_vs_lit | 1.352 x lit median | **WARN** | ours 252.50 cm vs lit 186.77-186.77 (median 186.77), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| TOTAL | ssp245 | 2300 | median_vs_lit | 1.702 x lit median | **WARN** | BRICK 2.0 317.82 cm vs the same lit median 186.77; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp245 | 2300 | spread_vs_lit | 1.068 x lit spread | **PASS** | ours 362.90 cm vs model-based lit 339.75-339.75 (median 339.75, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| TOTAL | ssp585 | 2100 | median_vs_lit | 1.216 x lit median | **PASS** | ours 91.62 cm vs lit 62.39-97.85 (median 75.33), n_lit=7 [1 SEJ comparator(s) excluded from the score; full range 62.39-97.85] |
| TOTAL | ssp585 | 2100 | median_vs_lit | 1.301 x lit median | **WARN** | BRICK 2.0 98.00 cm vs the same lit median 75.33; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp585 | 2100 | spread_vs_lit | 1.149 x lit spread | **PASS** | ours 79.14 cm vs model-based lit 40.46-106.79 (median 68.88, n=7); ALL comparators 40.46-181.04 |
| TOTAL | ssp585 | 2150 | median_vs_lit | 0.735 x lit median | **WARN** | ours 193.29 cm vs lit 262.93-262.93 (median 262.93), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| TOTAL | ssp585 | 2150 | median_vs_lit | 0.742 x lit median | **WARN** | BRICK 2.0 195.15 cm vs the same lit median 262.93; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp585 | 2150 | spread_vs_lit | 0.371 x lit spread | **WARN** | ours 149.72 cm vs model-based lit 403.38-403.38 (median 403.38, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |
| TOTAL | ssp585 | 2300 | median_vs_lit | 0.497 x lit median | **WARN** | ours 504.60 cm vs lit 1015.98-1015.98 (median 1015.98), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| TOTAL | ssp585 | 2300 | median_vs_lit | 0.461 x lit median | **WARN** | BRICK 2.0 467.87 cm vs the same lit median 1015.98; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp585 | 2300 | spread_vs_lit | 0.310 x lit spread | **WARN** | ours 427.75 cm vs model-based lit 1379.10-1379.10 (median 1379.10, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |

## [P] Levels — every arm side by side (cm)

| module | ssp | horizon | candidate (joint) | champion (joint) | BRICK 2.0 (fixed) |
|---|---|---|---|---|---|
| AIS | ssp126 | 2100 | 5.70 | 4.92 | 4.32 |
| AIS | ssp126 | 2150 | 8.82 | 7.68 | 6.52 |
| AIS | ssp126 | 2300 | 17.35 | 15.23 | 13.01 |
| AIS | ssp245 | 2100 | 10.52 | 10.55 | 27.41 |
| AIS | ssp245 | 2150 | 46.64 | 46.18 | 72.60 |
| AIS | ssp245 | 2300 | 155.85 | 156.34 | 205.94 |
| AIS | ssp585 | 2100 | 37.63 | 36.66 | 44.14 |
| AIS | ssp585 | 2150 | 93.18 | 92.56 | 97.88 |
| AIS | ssp585 | 2300 | 282.24 | 277.71 | 276.83 |
| glaciers | ssp126 | 2100 | 8.13 | 8.11 | 12.09 |
| glaciers | ssp126 | 2150 | 10.00 | 9.93 | 17.44 |
| glaciers | ssp126 | 2300 | 12.55 | 12.48 | 27.72 |
| glaciers | ssp245 | 2100 | 9.73 | 9.72 | 13.34 |
| glaciers | ssp245 | 2150 | 13.38 | 13.41 | 20.69 |
| glaciers | ssp245 | 2300 | 18.04 | 18.06 | 32.50 |
| glaciers | ssp585 | 2100 | 12.85 | 12.91 | 15.61 |
| glaciers | ssp585 | 2150 | 20.13 | 20.17 | 26.25 |
| glaciers | ssp585 | 2300 | 26.28 | 26.14 | 35.36 |
| Greenland | ssp126 | 2100 | 6.25 | 6.23 | 6.62 |
| Greenland | ssp126 | 2150 | 8.32 | 8.30 | 10.01 |
| Greenland | ssp126 | 2300 | 11.76 | 11.72 | 19.04 |
| Greenland | ssp245 | 2100 | 7.31 | 7.31 | 7.03 |
| Greenland | ssp245 | 2150 | 11.17 | 11.18 | 11.35 |
| Greenland | ssp245 | 2300 | 18.09 | 17.89 | 23.71 |
| Greenland | ssp585 | 2100 | 9.77 | 9.84 | 7.88 |
| Greenland | ssp585 | 2150 | 21.35 | 21.49 | 14.77 |
| Greenland | ssp585 | 2300 | 80.08 | 79.49 | 38.60 |
| thermal exp. | ssp126 | 2100 | 15.75 | 15.73 | 15.34 |
| thermal exp. | ssp126 | 2150 | 19.65 | 19.40 | 19.18 |
| thermal exp. | ssp126 | 2300 | 25.00 | 25.07 | 25.08 |
| thermal exp. | ssp245 | 2100 | 20.00 | 19.88 | 19.37 |
| thermal exp. | ssp245 | 2150 | 29.22 | 28.99 | 28.53 |
| thermal exp. | ssp245 | 2300 | 44.82 | 44.66 | 44.66 |
| thermal exp. | ssp585 | 2100 | 27.98 | 27.81 | 27.07 |
| thermal exp. | ssp585 | 2150 | 51.59 | 51.39 | 50.34 |
| thermal exp. | ssp585 | 2300 | 102.67 | 102.60 | 101.88 |
| land water | ssp126 | 2100 | 2.81 | 2.46 | 2.34 |
| land water | ssp126 | 2150 | 4.31 | 3.96 | 4.04 |
| land water | ssp126 | 2300 | 8.81 | 8.46 | 8.90 |
| land water | ssp245 | 2100 | 2.81 | 2.46 | 2.34 |
| land water | ssp245 | 2150 | 4.31 | 3.96 | 4.04 |
| land water | ssp245 | 2300 | 8.81 | 8.46 | 8.90 |
| land water | ssp585 | 2100 | 2.81 | 2.46 | 2.34 |
| land water | ssp585 | 2150 | 4.31 | 3.96 | 4.04 |
| land water | ssp585 | 2300 | 8.81 | 8.46 | 8.90 |
| TOTAL | ssp126 | 2100 | 39.01 | 38.00 | 41.16 |
| TOTAL | ssp126 | 2150 | 51.68 | 50.28 | 57.89 |
| TOTAL | ssp126 | 2300 | 76.94 | 74.81 | 94.76 |
| TOTAL | ssp245 | 2100 | 52.75 | 52.65 | 70.19 |
| TOTAL | ssp245 | 2150 | 104.92 | 104.85 | 137.98 |
| TOTAL | ssp245 | 2300 | 252.50 | 247.73 | 317.82 |
| TOTAL | ssp585 | 2100 | 91.62 | 90.67 | 98.00 |
| TOTAL | ssp585 | 2150 | 193.29 | 191.21 | 195.15 |
| TOTAL | ssp585 | 2300 | 504.60 | 497.87 | 467.87 |

## [S] Scenario separation — ssp585/ssp126 median ratio

| module | horizon | ours | verdict | literature |
|---|---|---|---|---|
| AIS | 2100 | 6.60x | **PASS** | FACTS 0.73-2.10 (n=5); MAGICC-SLR 10.69-10.69 (n=1) |
| AIS | 2150 | 10.57x | **PASS** | FACTS 1.43-1.43 (n=1); MAGICC-SLR 28.79-28.79 (n=1) |
| AIS | 2300 | 16.26x | **WARN** | MAGICC-SLR 81.77-81.77 (n=1)  [NO UPPER COMPARATOR AT THIS HORIZON] |
| glaciers | 2100 | 1.58x | **PASS** | FACTS 1.43-1.65 (n=2); MAGICC-SLR 1.46-1.46 (n=1) |
| glaciers | 2150 | 2.01x | **CHECK(wide)** | FACTS 1.93-1.93 (n=1); MAGICC-SLR 1.79-1.79 (n=1); 0.08 outside the bracket = 64% of its own range |
| glaciers | 2300 | 2.09x | **PASS** | FACTS 1.38-1.38 (n=1); MAGICC-SLR 2.11-2.11 (n=1) |
| Greenland | 2100 | 1.56x | **PASS** | FACTS 1.24-1.84 (n=3); MAGICC-SLR 2.11-2.11 (n=1) |
| Greenland | 2150 | 2.57x | **WARN** | MAGICC-SLR 3.48-3.48 (n=1)  [NO UPPER COMPARATOR AT THIS HORIZON] |
| Greenland | 2300 | 6.81x | **WARN** | MAGICC-SLR 7.54-7.54 (n=1)  [NO UPPER COMPARATOR AT THIS HORIZON] |
| thermal exp. | 2100 | 1.78x | **PASS** | FACTS 1.74-1.74 (n=1); MAGICC-SLR 2.51-2.51 (n=1) |
| thermal exp. | 2150 | 2.63x | **PASS** | FACTS 2.58-2.58 (n=1); MAGICC-SLR 3.94-3.94 (n=1) |
| thermal exp. | 2300 | 4.11x | **PASS** | FACTS 4.08-4.08 (n=1); MAGICC-SLR 6.18-6.18 (n=1) |
| land water | 2100 | 1.00x | **PASS** | FACTS 0.99-0.99 (n=1); MAGICC-SLR 1.00-1.00 (n=1) |
| land water | 2150 | 1.00x | **PASS** | FACTS 1.03-1.03 (n=1); MAGICC-SLR 1.00-1.00 (n=1) |
| land water | 2300 | 1.00x | **PASS** | FACTS 1.04-1.04 (n=1); MAGICC-SLR 1.00-1.00 (n=1) |
| TOTAL | 2100 | 2.35x | **PASS** | FACTS 1.44-1.82 (n=7); MAGICC-SLR 2.75-2.75 (n=1) |
| TOTAL | 2150 | 3.74x | **WARN** | MAGICC-SLR 5.72-5.72 (n=1)  [NO UPPER COMPARATOR AT THIS HORIZON] |
| TOTAL | 2300 | 6.56x | **WARN** | MAGICC-SLR 15.28-15.28 (n=1)  [NO UPPER COMPARATOR AT THIS HORIZON] |

---

*Machine-readable: `outputs/bench_ladrillo_L33.csv`. Regenerate: `python python/bench_ladrillo.py --tag=L33`.*
