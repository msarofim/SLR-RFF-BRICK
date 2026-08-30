# Ladrillo benchmark — `L21`

*benchmark v1.0, 2026-08-30, repo `e6f0e9f`. Champion arm: **L21** (the candidate IS the champion — no delta column).*

Arms: **candidate** (live `outputs/`), **champion\*** (frozen), **BRICK 2.0** (stock MimiBRICK v2.0.0, own posterior), **literature** (FACTS + MAGICC-SLR, frozen).

## Caveats that travel with every verdict

* HINDCAST RANKS IN ONE DIRECTION ONLY -- in-sample for every Ladrillo arm, out-of-sample for BRICK 2.0. It can REJECT an arm; a small fitted bias is not skill.
* BANDS ARE NOT ONE OBJECT -- Ladrillo-fixed and BRICK 2.0 are posterior-parameter spread; Ladrillo-JOINT, FACTS and MAGICC carry climate uncertainty. Only the JOINT band is scored against the literature.
* SOME WIDTH IS A PRIOR, NOT AN INFERENCE -- 78% of the ssp585 2300 AIS band is antarctic_lambda's paleo prior, so narrowness is never scored as a win at ais/ssp585.
* WHERE THE OBSERVED STATISTIC IS UNDER 2.0 SIGMA FROM ZERO the RATIO model/obs is suppressed as uninterpretable, but the DIFFERENCE is still graded on z -- being 3 sigma from a value that is itself 1 sigma from zero is still a miss.
* THE MODERN AIS RATE CANNOT REJECT ZERO -- IMBIE whole-sheet loss is 0.95-1.44 sigma from zero, so the 1993-2026 window separates no two AIS models however different they are.
* A p5-p95 SPREAD IS BLIND TO A MODE UNDER 5% OF THE MASS -- cells whose p05-p99/p05-p95 exceeds 2.0x the Gaussian 1.207 are marked N/A(bimodal) and NOT scored on width; quote the mean and the tipped fraction there.
* ssp245@2300 IS A THRESHOLD ARTIFACT -- 48.3% of draws tip, so its MEDIAN is bimodal-fragile. Quote the mean and the tipped fraction there, never the bare median.

## [V] Roll-up

| module | hindcast | rate/accel | projection | separation | vs champion |
|---|---|---|---|---|---|
| **AIS** | PASS | UNRESOLVED | FAIL | WARN | — |
| **glaciers** | WARN | UNRESOLVED | WARN | WARN | — |
| **Greenland** | PASS | UNRESOLVED | FAIL | WARN | — |
| **thermal exp.** | WARN | FAIL | WARN | FAIL | — |
| **land water** | — | — | WARN | PASS | — |
| **TOTAL** | PASS | UNRESOLVED | WARN | WARN | — |

## [H] Hindcast — the full observational period, scaled to each component's own target 1-sigma

| module | target 1σ (cm) | window | arm | RMSE (cm) | RMSE (σ) | note |
|---|---|---|---|---|---|---|
| AIS | 0.1674 | full | L21 | 0.0311 | 0.19 | bias -0.0024 cm = -0.01 sd; cov90 83%; n=106 |
| AIS | 0.1674 | full | BRICK 2.0 | 1.1758 | 7.02 | bias -0.8211 cm = -4.90 sd; cov90 31%; n=106 |
| AIS | 0.1674 | 1920-1949 | L21 | 0.0079 | 0.05 | bias -0.0075 cm = -0.04 sd; cov90 100%; n=30 |
| AIS | 0.1674 | 1920-1949 | BRICK 2.0 | 1.9843 | 11.85 | bias -1.9579 cm = -11.69 sd; cov90 0%; n=30 |
| AIS | 0.1674 | 1950-1992 | L21 | 0.0079 | 0.05 | bias +0.0030 cm = +0.02 sd; cov90 98%; n=43 |
| AIS | 0.1674 | 1950-1992 | BRICK 2.0 | 0.8082 | 4.83 | bias -0.7053 cm = -4.21 sd; cov90 2%; n=43 |
| AIS | 0.1674 | 1993-2026 | L21 | 0.0545 | 0.33 | bias -0.0048 cm = -0.03 sd; cov90 48%; n=33 |
| AIS | 0.1674 | 1993-2026 | BRICK 2.0 | 0.0992 | 0.59 | bias +0.0615 cm = +0.37 sd; cov90 97%; n=33 |
| glaciers | 0.4593 | full | L21 | 0.3366 | 0.73 | bias +0.1721 cm = +0.37 sd; cov90 52%; n=104 |
| glaciers | 0.4593 | full | BRICK 2.0 | 0.8941 | 1.95 | bias +0.5000 cm = +1.09 sd; cov90 47%; n=104 |
| glaciers | 0.4593 | 1920-1949 | L21 | 0.5990 | 1.30 | bias +0.5356 cm = +1.17 sd; cov90 20%; n=30 |
| glaciers | 0.4593 | 1920-1949 | BRICK 2.0 | 1.6382 | 3.57 | bias +1.5142 cm = +3.30 sd; cov90 0%; n=30 |
| glaciers | 0.4593 | 1950-1992 | L21 | 0.1351 | 0.29 | bias +0.0799 cm = +0.17 sd; cov90 56%; n=43 |
| glaciers | 0.4593 | 1950-1992 | BRICK 2.0 | 0.1311 | 0.29 | bias +0.0341 cm = +0.07 sd; cov90 95%; n=43 |
| glaciers | 0.4593 | 1993-2026 | L21 | 0.0871 | 0.19 | bias -0.0518 cm = -0.11 sd; cov90 77%; n=31 |
| glaciers | 0.4593 | 1993-2026 | BRICK 2.0 | 0.2460 | 0.54 | bias +0.1647 cm = +0.36 sd; cov90 26%; n=31 |
| Greenland | 0.1832 | full | L21 | 0.0587 | 0.32 | bias +0.0013 cm = +0.01 sd; cov90 56%; n=106 |
| Greenland | 0.1832 | full | BRICK 2.0 | 0.7230 | 3.95 | bias -0.5975 cm = -3.26 sd; cov90 22%; n=106 |
| Greenland | 0.1832 | 1920-1949 | L21 | 0.0798 | 0.44 | bias +0.0247 cm = +0.13 sd; cov90 57%; n=30 |
| Greenland | 0.1832 | 1920-1949 | BRICK 2.0 | 0.7876 | 4.30 | bias -0.7371 cm = -4.02 sd; cov90 27%; n=30 |
| Greenland | 0.1832 | 1950-1992 | L21 | 0.0493 | 0.27 | bias -0.0152 cm = -0.08 sd; cov90 63%; n=43 |
| Greenland | 0.1832 | 1950-1992 | BRICK 2.0 | 0.9132 | 4.99 | bias -0.8659 cm = -4.73 sd; cov90 0%; n=43 |
| Greenland | 0.1832 | 1993-2026 | L21 | 0.0457 | 0.25 | bias +0.0015 cm = +0.01 sd; cov90 45%; n=33 |
| Greenland | 0.1832 | 1993-2026 | BRICK 2.0 | 0.1686 | 0.92 | bias -0.1209 cm = -0.66 sd; cov90 45%; n=33 |
| thermal exp. | 0.3091 | full | L21 | 0.4006 | 1.30 | bias +0.1604 cm = +0.52 sd; cov90 39%; n=106 |
| thermal exp. | 0.3091 | full | BRICK 2.0 | 0.3243 | 1.05 | bias +0.1908 cm = +0.62 sd; cov90 96%; n=106 |
| thermal exp. | 0.3091 | 1920-1949 | L21 | 0.5450 | 1.76 | bias +0.4076 cm = +1.32 sd; cov90 33%; n=30 |
| thermal exp. | 0.3091 | 1920-1949 | BRICK 2.0 | 0.4741 | 1.53 | bias +0.3885 cm = +1.26 sd; cov90 100%; n=30 |
| thermal exp. | 0.3091 | 1950-1992 | L21 | 0.2157 | 0.70 | bias -0.1064 cm = -0.34 sd; cov90 60%; n=43 |
| thermal exp. | 0.3091 | 1950-1992 | BRICK 2.0 | 0.1897 | 0.61 | bias +0.0499 cm = +0.16 sd; cov90 100%; n=43 |
| thermal exp. | 0.3091 | 1993-2026 | L21 | 0.4300 | 1.39 | bias +0.2832 cm = +0.92 sd; cov90 15%; n=33 |
| thermal exp. | 0.3091 | 1993-2026 | BRICK 2.0 | 0.2941 | 0.95 | bias +0.1946 cm = +0.63 sd; cov90 88%; n=33 |
| TOTAL | 1.5380 | full | L21 | 0.6813 | 0.44 | bias +0.5414 cm = +0.35 sd; cov90 33%; n=105 |
| TOTAL | 1.5380 | full | BRICK 2.0 | 1.8198 | 1.18 | bias -1.3318 cm = -0.87 sd; cov90 25%; n=105 |
| TOTAL | 1.5380 | 1920-1949 | L21 | 1.0493 | 0.68 | bias +0.9907 cm = +0.64 sd; cov90 23%; n=30 |
| TOTAL | 1.5380 | 1920-1949 | BRICK 2.0 | 2.5470 | 1.66 | bias -2.4846 cm = -1.62 sd; cov90 0%; n=30 |
| TOTAL | 1.5380 | 1950-1992 | L21 | 0.5186 | 0.34 | bias +0.4823 cm = +0.31 sd; cov90 35%; n=43 |
| TOTAL | 1.5380 | 1950-1992 | BRICK 2.0 | 1.8672 | 1.21 | bias -1.5605 cm = -1.01 sd; cov90 12%; n=43 |
| TOTAL | 1.5380 | 1993-2026 | L21 | 0.3596 | 0.23 | bias +0.1996 cm = +0.13 sd; cov90 41%; n=32 |
| TOTAL | 1.5380 | 1993-2026 | BRICK 2.0 | 0.3164 | 0.21 | bias +0.0564 cm = +0.04 sd; cov90 66%; n=32 |

## [R] Rate (1993-2026) and acceleration (1900-2026), with an error bar on the observations

| module | statistic | arm | value | unit | z vs obs bar | note |
|---|---|---|---|---|---|---|
| AIS | rate | observations | 0.032608 | cm/yr | — | se: estimator 0.003405, band-correlated 0.0005689, band-independent 0.003061; CONSERVATIVE 0.003405 cm/yr; |obs|/se = 9.58 |
| AIS | rate | L21 | 0.031609 | cm/yr | -0.29 | 0.97x obs; z=-0.29 vs the obs error bar |
| AIS | rate | BRICK 2.0 | 0.039301 | cm/yr | +1.97 | 1.21x obs; z=+1.97 vs the obs error bar |
| glaciers | rate | observations | 0.068013 | cm/yr | — | se: estimator 0.0005236, band-correlated 0.0001274, band-independent 0.009223; CONSERVATIVE 0.009223 cm/yr; |obs|/se = 7.37 |
| glaciers | rate | L21 | 0.062863 | cm/yr | -0.56 | 0.92x obs; z=-0.56 vs the obs error bar |
| glaciers | rate | BRICK 2.0 | 0.090078 | cm/yr | +2.39 | 1.32x obs; z=+2.39 vs the obs error bar |
| Greenland | rate | observations | 0.06596 | cm/yr | — | se: estimator 0.01044, band-correlated 0.0006502, band-independent 0.003349; CONSERVATIVE 0.01044 cm/yr; |obs|/se = 6.32 |
| Greenland | rate | L21 | 0.065744 | cm/yr | -0.02 | 1.00x obs; z=-0.02 vs the obs error bar |
| Greenland | rate | BRICK 2.0 | 0.058529 | cm/yr | -0.71 | 0.89x obs; z=-0.71 vs the obs error bar |
| thermal exp. | rate | observations | 0.1234 | cm/yr | — | se: estimator 0.003756, band-correlated 0.002392, band-independent 0.005651; CONSERVATIVE 0.005651 cm/yr; |obs|/se = 21.84 |
| thermal exp. | rate | L21 | 0.15656 | cm/yr | +5.87 | 1.27x obs; z=+5.87 vs the obs error bar |
| thermal exp. | rate | BRICK 2.0 | 0.14454 | cm/yr | +3.74 | 1.17x obs; z=+3.74 vs the obs error bar |
| TOTAL | rate | observations | 0.32469 | cm/yr | — | se: estimator 0.02949, band-correlated 0.02545, band-independent 0.02945; CONSERVATIVE 0.02949 cm/yr; |obs|/se = 11.01 |
| TOTAL | rate | L21 | 0.34709 | cm/yr | +0.76 | 1.07x obs; z=+0.76 vs the obs error bar |
| TOTAL | rate | BRICK 2.0 | 0.33831 | cm/yr | +0.46 | 1.04x obs; z=+0.46 vs the obs error bar |
| AIS | accel | observations | 0.00020499 | cm/yr2 | — | se: estimator 0.0001336, band-correlated 3.924e-05, band-independent 2.522e-05; CONSERVATIVE 0.0001336 cm/yr2; |obs|/se = 1.53 |
| AIS | accel | L21 | 0.00020364 | cm/yr2 | -0.01 | ratio NOT INTERPRETABLE (obs is 1.53 se from zero); z=-0.01 vs the obs error bar |
| AIS | accel | BRICK 2.0 | -9.5414e-05 | cm/yr2 | -2.25 | ratio NOT INTERPRETABLE (obs is 1.53 se from zero); z=-2.25 vs the obs error bar |
| glaciers | accel | observations | -0.00054814 | cm/yr2 | — | se: estimator 0.000447, band-correlated 3.442e-05, band-independent 7.199e-05; CONSERVATIVE 0.000447 cm/yr2; |obs|/se = 1.23 |
| glaciers | accel | L21 | -0.00010531 | cm/yr2 | +0.99 | ratio NOT INTERPRETABLE (obs is 1.23 se from zero); z=+0.99 vs the obs error bar |
| glaciers | accel | BRICK 2.0 | 0.00082242 | cm/yr2 | +3.07 | ratio NOT INTERPRETABLE (obs is 1.23 se from zero); z=+3.07 vs the obs error bar |
| Greenland | accel | observations | -0.00027825 | cm/yr2 | — | se: estimator 0.0005241, band-correlated 6.83e-05, band-independent 2.759e-05; CONSERVATIVE 0.0005241 cm/yr2; |obs|/se = 0.53 |
| Greenland | accel | L21 | -0.00025054 | cm/yr2 | +0.05 | ratio NOT INTERPRETABLE (obs is 0.53 se from zero); z=+0.05 vs the obs error bar |
| Greenland | accel | BRICK 2.0 | 0.00014987 | cm/yr2 | +0.82 | ratio NOT INTERPRETABLE (obs is 0.53 se from zero); z=+0.82 vs the obs error bar |
| thermal exp. | accel | observations | 0.0008428 | cm/yr2 | — | se: estimator 0.0002431, band-correlated 2.312e-05, band-independent 4.655e-05; CONSERVATIVE 0.0002431 cm/yr2; |obs|/se = 3.47 |
| thermal exp. | accel | L21 | 0.001274 | cm/yr2 | +1.77 | 1.51x obs; z=+1.77 vs the obs error bar |
| thermal exp. | accel | BRICK 2.0 | 0.0013015 | cm/yr2 | +1.89 | 1.54x obs; z=+1.89 vs the obs error bar |
| TOTAL | accel | observations | 0.00089376 | cm/yr2 | — | se: estimator 0.001159, band-correlated 0.0001276, band-independent 0.0002363; CONSERVATIVE 0.001159 cm/yr2; |obs|/se = 0.77 |
| TOTAL | accel | L21 | 0.0013021 | cm/yr2 | +0.35 | ratio NOT INTERPRETABLE (obs is 0.77 se from zero); z=+0.35 vs the obs error bar |
| TOTAL | accel | BRICK 2.0 | 0.0022411 | cm/yr2 | +1.16 | ratio NOT INTERPRETABLE (obs is 0.77 se from zero); z=+1.16 vs the obs error bar |

## [P] Projections vs the literature — scored on the JOINT band

| module | ssp | horizon | metric | value | verdict | note |
|---|---|---|---|---|---|---|
| AIS | ssp126 | 2100 | median_vs_lit | 0.498 x lit median | **PASS** | ours 4.46 cm vs lit 3.66-11.90 (median 8.94), n_lit=5 [1 SEJ comparator(s) excluded from the score; full range 3.66-11.90]; ⚠ BIMODAL cell -- our MEAN is 6.64 cm = 0.74x the literature median, and the median sits entirely inside the near mode |
| AIS | ssp126 | 2100 | median_vs_lit | 0.482 x lit median | **PASS** | BRICK 2.0 4.32 cm vs the same lit median 8.94; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp126 | 2100 | spread_vs_lit | 0.760 x lit spread | **N/A(bimodal)** | ours 16.05 cm vs model-based lit 9.86-39.27 (median 21.11, n=5); ALL comparators 9.86-91.07; ⚠ p05-p99/p05-p95 = 3.21 vs Gaussian 1.207 => BIMODAL, and p95 is blind to the far mode (p05-p99 = 51.46 cm). The p5-p95 ratio is a property of the QUANTILE here, not of the model |
| AIS | ssp126 | 2150 | median_vs_lit | 0.381 x lit median | **PASS** | ours 6.83 cm vs lit 5.34-26.34 (median 17.92), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 5.34-26.34]; ⚠ BIMODAL cell -- our MEAN is 11.59 cm = 0.65x the literature median, and the median sits entirely inside the near mode |
| AIS | ssp126 | 2150 | median_vs_lit | 0.364 x lit median | **PASS** | BRICK 2.0 6.52 cm vs the same lit median 17.92; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp126 | 2150 | spread_vs_lit | 0.867 x lit spread | **N/A(bimodal)** | ours 40.03 cm vs model-based lit 33.17-72.55 (median 46.14, n=4); ALL comparators 33.17-156.27; ⚠ p05-p99/p05-p95 = 2.59 vs Gaussian 1.207 => BIMODAL, and p95 is blind to the far mode (p05-p99 = 103.51 cm). The p5-p95 ratio is a property of the QUANTILE here, not of the model |
| AIS | ssp126 | 2300 | median_vs_lit | 1.548 x lit median | **WARN** | ours 13.48 cm vs lit 8.71-8.71 (median 8.71), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| AIS | ssp126 | 2300 | median_vs_lit | 1.495 x lit median | **WARN** | BRICK 2.0 13.01 cm vs the same lit median 8.71; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp126 | 2300 | spread_vs_lit | 2.026 x lit spread | **WARN** | ours 140.98 cm vs model-based lit 69.60-69.60 (median 69.60, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |
| AIS | ssp245 | 2100 | median_vs_lit | 0.525 x lit median | **WARN** | ours 5.45 cm vs lit 5.54-12.73 (median 10.38), n_lit=5 [1 SEJ comparator(s) excluded from the score; full range 5.54-13.71] |
| AIS | ssp245 | 2100 | median_vs_lit | 2.641 x lit median | **FAIL** | BRICK 2.0 27.41 cm vs the same lit median 10.38; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp245 | 2100 | spread_vs_lit | 1.212 x lit spread | **PASS** | ours 43.42 cm vs model-based lit 20.88-44.94 (median 35.81, n=5); ALL comparators 20.88-109.87 |
| AIS | ssp245 | 2150 | median_vs_lit | 0.397 x lit median | **FAIL** | ours 10.89 cm vs lit 10.91-30.28 (median 27.45), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 10.91-30.28] |
| AIS | ssp245 | 2150 | median_vs_lit | 2.645 x lit median | **FAIL** | BRICK 2.0 72.60 cm vs the same lit median 27.45; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp245 | 2150 | spread_vs_lit | 1.216 x lit spread | **WARN** | ours 102.22 cm vs model-based lit 44.92-369.45 (median 84.10, n=4); ALL comparators 44.92-369.45; ⚠ THE COMPARATORS DO NOT AGREE -- scored one at a time they give 1xhigh/2xin/1xlow and the median's 'in' is not a majority, so the median is not a summary here; verdict CAPPED at WARN |
| AIS | ssp245 | 2300 | median_vs_lit | 0.790 x lit median | **WARN** | ours 65.92 cm vs lit 83.46-83.46 (median 83.46), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| AIS | ssp245 | 2300 | median_vs_lit | 2.468 x lit median | **WARN** | BRICK 2.0 205.94 cm vs the same lit median 83.46; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp245 | 2300 | spread_vs_lit | 1.074 x lit spread | **PASS** | ours 291.76 cm vs model-based lit 271.56-271.56 (median 271.56, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| AIS | ssp585 | 2100 | median_vs_lit | 2.045 x lit median | **PASS** | ours 29.49 cm vs lit 3.98-39.10 (median 14.43), n_lit=5 [1 SEJ comparator(s) excluded from the score; full range 3.98-39.10] |
| AIS | ssp585 | 2100 | median_vs_lit | 3.060 x lit median | **FAIL** | BRICK 2.0 44.14 cm vs the same lit median 14.43; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp585 | 2100 | spread_vs_lit | 1.014 x lit spread | **PASS** | ours 57.25 cm vs model-based lit 20.51-79.00 (median 56.48, n=5); ALL comparators 20.51-151.54; width here is the antarctic_lambda PRIOR -- do NOT narrow |
| AIS | ssp585 | 2150 | median_vs_lit | 0.882 x lit median | **PASS** | ours 84.25 cm vs lit 6.26-198.76 (median 95.53), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 6.26-198.76] |
| AIS | ssp585 | 2150 | median_vs_lit | 1.025 x lit median | **PASS** | BRICK 2.0 97.88 cm vs the same lit median 95.53; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp585 | 2150 | spread_vs_lit | 0.504 x lit spread | **WARN** | ours 103.40 cm vs model-based lit 48.68-408.37 (median 205.25, n=4); ALL comparators 48.68-570.98; ⚠ THE COMPARATORS DO NOT AGREE -- scored one at a time they give 1xhigh/1xin/2xlow and the median's 'in' is not a majority, so the median is not a summary here; verdict CAPPED at WARN; width here is the antarctic_lambda PRIOR -- do NOT narrow |
| AIS | ssp585 | 2300 | median_vs_lit | 0.980 x lit median | **PASS** | ours 267.49 cm vs lit 267.00-712.02 (median 273.00), n_lit=3 |
| AIS | ssp585 | 2300 | median_vs_lit | 1.014 x lit median | **PASS** | BRICK 2.0 276.83 cm vs the same lit median 273.00; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp585 | 2300 | spread_vs_lit | 0.297 x lit spread | **WARN** | ours 280.97 cm vs model-based lit 944.94-944.94 (median 944.94, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; width here is the antarctic_lambda PRIOR -- do NOT narrow |
| glaciers | ssp126 | 2100 | median_vs_lit | 0.864 x lit median | **WARN** | ours 7.99 cm vs lit 8.95-10.45 (median 9.25), n_lit=3 |
| glaciers | ssp126 | 2100 | median_vs_lit | 1.307 x lit median | **WARN** | BRICK 2.0 12.09 cm vs the same lit median 9.25; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp126 | 2100 | spread_vs_lit | 0.815 x lit spread | **PASS** | ours 6.00 cm vs model-based lit 7.12-7.85 (median 7.36, n=3) |
| glaciers | ssp126 | 2150 | median_vs_lit | 0.812 x lit median | **WARN** | ours 9.86 cm vs lit 12.00-12.28 (median 12.14), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp126 | 2150 | median_vs_lit | 1.437 x lit median | **WARN** | BRICK 2.0 17.44 cm vs the same lit median 12.14; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp126 | 2150 | spread_vs_lit | 0.787 x lit spread | **PASS** | ours 8.04 cm vs model-based lit 8.52-11.89 (median 10.21, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| glaciers | ssp126 | 2300 | median_vs_lit | 0.899 x lit median | **WARN** | ours 12.40 cm vs lit 13.80-13.80 (median 13.80), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp126 | 2300 | median_vs_lit | 2.008 x lit median | **WARN** | BRICK 2.0 27.72 cm vs the same lit median 13.80; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp126 | 2300 | spread_vs_lit | 0.979 x lit spread | **PASS** | ours 11.00 cm vs model-based lit 11.23-11.23 (median 11.23, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| glaciers | ssp245 | 2100 | median_vs_lit | 0.789 x lit median | **WARN** | ours 9.64 cm vs lit 11.38-12.54 (median 12.21), n_lit=3 |
| glaciers | ssp245 | 2100 | median_vs_lit | 1.093 x lit median | **WARN** | BRICK 2.0 13.34 cm vs the same lit median 12.21; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp245 | 2100 | spread_vs_lit | 0.907 x lit spread | **PASS** | ours 6.97 cm vs model-based lit 7.42-9.60 (median 7.68, n=3) |
| glaciers | ssp245 | 2150 | median_vs_lit | 0.780 x lit median | **WARN** | ours 13.35 cm vs lit 16.71-17.53 (median 17.12), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp245 | 2150 | median_vs_lit | 1.208 x lit median | **WARN** | BRICK 2.0 20.69 cm vs the same lit median 17.12; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp245 | 2150 | spread_vs_lit | 0.786 x lit spread | **PASS** | ours 10.14 cm vs model-based lit 9.16-16.65 (median 12.91, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| glaciers | ssp245 | 2300 | median_vs_lit | 0.854 x lit median | **WARN** | ours 18.33 cm vs lit 21.47-21.47 (median 21.47), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp245 | 2300 | median_vs_lit | 1.514 x lit median | **WARN** | BRICK 2.0 32.50 cm vs the same lit median 21.47; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp245 | 2300 | spread_vs_lit | 1.200 x lit spread | **PASS** | ours 13.14 cm vs model-based lit 10.95-10.95 (median 10.95, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| glaciers | ssp585 | 2100 | median_vs_lit | 0.833 x lit median | **WARN** | ours 12.88 cm vs lit 15.30-17.73 (median 15.46), n_lit=3 |
| glaciers | ssp585 | 2100 | median_vs_lit | 1.009 x lit median | **PASS** | BRICK 2.0 15.61 cm vs the same lit median 15.46; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp585 | 2100 | spread_vs_lit | 0.914 x lit spread | **PASS** | ours 8.60 cm vs model-based lit 8.51-13.85 (median 9.41, n=3) |
| glaciers | ssp585 | 2150 | median_vs_lit | 0.809 x lit median | **WARN** | ours 20.40 cm vs lit 22.03-28.40 (median 25.22), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp585 | 2150 | median_vs_lit | 1.041 x lit median | **PASS** | BRICK 2.0 26.25 cm vs the same lit median 25.22; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp585 | 2150 | spread_vs_lit | 0.912 x lit spread | **PASS** | ours 11.68 cm vs model-based lit 10.09-15.53 (median 12.81, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| glaciers | ssp585 | 2300 | median_vs_lit | 0.916 x lit median | **WARN** | ours 26.65 cm vs lit 29.10-29.10 (median 29.10), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp585 | 2300 | median_vs_lit | 1.215 x lit median | **WARN** | BRICK 2.0 35.36 cm vs the same lit median 29.10; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp585 | 2300 | spread_vs_lit | 1.237 x lit spread | **PASS** | ours 12.16 cm vs model-based lit 9.83-9.83 (median 9.83, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| Greenland | ssp126 | 2100 | median_vs_lit | 1.019 x lit median | **PASS** | ours 6.52 cm vs lit 5.46-7.67 (median 6.40), n_lit=3 [1 SEJ comparator(s) excluded from the score; full range 5.46-13.05] |
| Greenland | ssp126 | 2100 | median_vs_lit | 1.034 x lit median | **PASS** | BRICK 2.0 6.62 cm vs the same lit median 6.40; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp126 | 2100 | spread_vs_lit | 0.463 x lit spread | **FAIL** | ours 4.43 cm vs model-based lit 7.06-17.14 (median 9.57, n=3); ALL comparators 7.06-55.71 |
| Greenland | ssp126 | 2150 | median_vs_lit | 0.709 x lit median | **WARN** | ours 7.97 cm vs lit 9.31-13.18 (median 11.25), n_lit=2 [1 SEJ comparator(s) excluded from the score; full range 9.31-22.20] ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp126 | 2150 | median_vs_lit | 0.890 x lit median | **PASS** | BRICK 2.0 10.01 cm vs the same lit median 11.25; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp126 | 2150 | spread_vs_lit | 0.489 x lit spread | **WARN** | ours 6.55 cm vs model-based lit 11.12-15.69 (median 13.40, n=2); ALL comparators 11.12-86.94; ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |
| Greenland | ssp126 | 2300 | median_vs_lit | 0.671 x lit median | **WARN** | ours 10.04 cm vs lit 14.98-14.98 (median 14.98), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp126 | 2300 | median_vs_lit | 1.271 x lit median | **WARN** | BRICK 2.0 19.04 cm vs the same lit median 14.98; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp126 | 2300 | spread_vs_lit | 0.396 x lit spread | **WARN** | ours 11.66 cm vs model-based lit 29.41-29.41 (median 29.41, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |
| Greenland | ssp245 | 2100 | median_vs_lit | 0.879 x lit median | **PASS** | ours 8.16 cm vs lit 7.97-10.21 (median 9.28), n_lit=3 [1 SEJ comparator(s) excluded from the score; full range 7.97-14.39] |
| Greenland | ssp245 | 2100 | median_vs_lit | 0.757 x lit median | **WARN** | BRICK 2.0 7.03 cm vs the same lit median 9.28; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp245 | 2100 | spread_vs_lit | 0.690 x lit spread | **PASS** | ours 5.76 cm vs model-based lit 7.85-16.85 (median 8.35, n=3); ALL comparators 7.85-72.68 |
| Greenland | ssp245 | 2150 | median_vs_lit | 0.684 x lit median | **WARN** | ours 11.87 cm vs lit 16.53-18.19 (median 17.36), n_lit=2 [1 SEJ comparator(s) excluded from the score; full range 16.53-25.62] ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp245 | 2150 | median_vs_lit | 0.654 x lit median | **WARN** | BRICK 2.0 11.35 cm vs the same lit median 17.36; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp245 | 2150 | spread_vs_lit | 0.755 x lit spread | **PASS** | ours 11.26 cm vs model-based lit 14.88-14.93 (median 14.91, n=2); ALL comparators 14.88-88.90; ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| Greenland | ssp245 | 2300 | median_vs_lit | 0.480 x lit median | **WARN** | ours 17.16 cm vs lit 35.79-35.79 (median 35.79), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp245 | 2300 | median_vs_lit | 0.662 x lit median | **WARN** | BRICK 2.0 23.71 cm vs the same lit median 35.79; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp245 | 2300 | spread_vs_lit | 0.733 x lit spread | **PASS** | ours 30.00 cm vs model-based lit 40.91-40.91 (median 40.91, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| Greenland | ssp585 | 2100 | median_vs_lit | 0.893 x lit median | **WARN** | ours 12.04 cm vs lit 12.72-14.02 (median 13.49), n_lit=3 [1 SEJ comparator(s) excluded from the score; full range 12.72-20.28] |
| Greenland | ssp585 | 2100 | median_vs_lit | 0.584 x lit median | **WARN** | BRICK 2.0 7.88 cm vs the same lit median 13.49; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp585 | 2100 | spread_vs_lit | 0.827 x lit spread | **PASS** | ours 10.05 cm vs model-based lit 11.46-17.10 (median 12.15, n=3); ALL comparators 11.46-93.18 |
| Greenland | ssp585 | 2150 | median_vs_lit | 0.856 x lit median | **WARN** | ours 25.56 cm vs lit 27.33-32.40 (median 29.87), n_lit=2 [1 SEJ comparator(s) excluded from the score; full range 27.33-38.13] ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp585 | 2150 | median_vs_lit | 0.495 x lit median | **WARN** | BRICK 2.0 14.77 cm vs the same lit median 29.87; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp585 | 2150 | spread_vs_lit | 0.525 x lit spread | **PASS** | ours 30.42 cm vs model-based lit 24.97-90.97 (median 57.97, n=2); ALL comparators 24.97-121.86; ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| Greenland | ssp585 | 2300 | median_vs_lit | 0.734 x lit median | **WARN** | ours 82.92 cm vs lit 113.01-113.01 (median 113.01), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp585 | 2300 | median_vs_lit | 0.342 x lit median | **WARN** | BRICK 2.0 38.60 cm vs the same lit median 113.01; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp585 | 2300 | spread_vs_lit | 0.159 x lit spread | **WARN** | ours 108.01 cm vs model-based lit 680.24-680.24 (median 680.24, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |
| thermal exp. | ssp126 | 2100 | median_vs_lit | 1.277 x lit median | **WARN** | ours 16.05 cm vs lit 11.09-14.05 (median 12.57), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| thermal exp. | ssp126 | 2100 | median_vs_lit | 1.220 x lit median | **WARN** | BRICK 2.0 15.34 cm vs the same lit median 12.57; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp126 | 2100 | spread_vs_lit | 1.032 x lit spread | **PASS** | ours 11.98 cm vs model-based lit 11.26-11.97 (median 11.61, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp126 | 2150 | median_vs_lit | 1.313 x lit median | **WARN** | ours 20.05 cm vs lit 12.68-17.85 (median 15.26), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| thermal exp. | ssp126 | 2150 | median_vs_lit | 1.257 x lit median | **WARN** | BRICK 2.0 19.18 cm vs the same lit median 15.26; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp126 | 2150 | spread_vs_lit | 1.054 x lit spread | **PASS** | ours 17.41 cm vs model-based lit 16.06-16.96 (median 16.51, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp126 | 2300 | median_vs_lit | 1.537 x lit median | **WARN** | ours 25.72 cm vs lit 16.74-16.74 (median 16.74), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| thermal exp. | ssp126 | 2300 | median_vs_lit | 1.499 x lit median | **WARN** | BRICK 2.0 25.08 cm vs the same lit median 16.74; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp126 | 2300 | spread_vs_lit | 1.153 x lit spread | **PASS** | ours 29.36 cm vs model-based lit 25.47-25.47 (median 25.47, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp245 | 2100 | median_vs_lit | 1.145 x lit median | **WARN** | ours 20.31 cm vs lit 16.62-18.84 (median 17.73), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| thermal exp. | ssp245 | 2100 | median_vs_lit | 1.092 x lit median | **WARN** | BRICK 2.0 19.37 cm vs the same lit median 17.73; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp245 | 2100 | spread_vs_lit | 0.972 x lit spread | **PASS** | ours 14.09 cm vs model-based lit 13.73-15.26 (median 14.49, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp245 | 2150 | median_vs_lit | 1.147 x lit median | **WARN** | ours 29.74 cm vs lit 23.23-28.64 (median 25.94), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| thermal exp. | ssp245 | 2150 | median_vs_lit | 1.100 x lit median | **PASS** | BRICK 2.0 28.53 cm vs the same lit median 25.94; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp245 | 2150 | spread_vs_lit | 0.956 x lit spread | **PASS** | ours 23.79 cm vs model-based lit 23.92-25.87 (median 24.90, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp245 | 2300 | median_vs_lit | 1.267 x lit median | **WARN** | ours 45.98 cm vs lit 36.30-36.30 (median 36.30), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| thermal exp. | ssp245 | 2300 | median_vs_lit | 1.230 x lit median | **WARN** | BRICK 2.0 44.66 cm vs the same lit median 36.30; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp245 | 2300 | spread_vs_lit | 0.889 x lit spread | **PASS** | ours 48.25 cm vs model-based lit 54.25-54.25 (median 54.25, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp585 | 2100 | median_vs_lit | 0.998 x lit median | **PASS** | ours 28.30 cm vs lit 27.88-28.82 (median 28.35), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp585 | 2100 | median_vs_lit | 0.955 x lit median | **WARN** | BRICK 2.0 27.07 cm vs the same lit median 28.35; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp585 | 2100 | spread_vs_lit | 0.849 x lit spread | **PASS** | ours 18.68 cm vs model-based lit 21.13-22.88 (median 22.00, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp585 | 2150 | median_vs_lit | 1.019 x lit median | **PASS** | ours 52.62 cm vs lit 49.94-53.35 (median 51.64), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp585 | 2150 | median_vs_lit | 0.975 x lit median | **PASS** | BRICK 2.0 50.34 cm vs the same lit median 51.64; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp585 | 2150 | spread_vs_lit | 0.862 x lit spread | **PASS** | ours 38.79 cm vs model-based lit 41.87-48.08 (median 44.98, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp585 | 2300 | median_vs_lit | 1.017 x lit median | **WARN** | ours 105.22 cm vs lit 103.49-103.49 (median 103.49), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| thermal exp. | ssp585 | 2300 | median_vs_lit | 0.984 x lit median | **WARN** | BRICK 2.0 101.88 cm vs the same lit median 103.49; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp585 | 2300 | spread_vs_lit | 0.819 x lit spread | **PASS** | ours 99.44 cm vs model-based lit 121.40-121.40 (median 121.40, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| land water | ssp126 | 2100 | median_vs_lit | 0.865 x lit median | **WARN** | ours 2.60 cm vs lit 2.99-3.01 (median 3.00), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp126 | 2100 | median_vs_lit | 0.781 x lit median | **WARN** | BRICK 2.0 2.34 cm vs the same lit median 3.00; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp126 | 2100 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 3.64-4.06 (median 3.85, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp126 | 2150 | median_vs_lit | 0.887 x lit median | **WARN** | ours 4.23 cm vs lit 4.58-4.96 (median 4.77), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp126 | 2150 | median_vs_lit | 0.847 x lit median | **WARN** | BRICK 2.0 4.04 cm vs the same lit median 4.77; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp126 | 2150 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 5.64-5.78 (median 5.71, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp126 | 2300 | median_vs_lit | 0.787 x lit median | **WARN** | ours 8.48 cm vs lit 10.78-10.78 (median 10.78), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp126 | 2300 | median_vs_lit | 0.825 x lit median | **WARN** | BRICK 2.0 8.90 cm vs the same lit median 10.78; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp126 | 2300 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 12.12-12.12 (median 12.12, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp245 | 2100 | median_vs_lit | 0.848 x lit median | **WARN** | ours 2.60 cm vs lit 3.01-3.11 (median 3.06), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp245 | 2100 | median_vs_lit | 0.765 x lit median | **WARN** | BRICK 2.0 2.34 cm vs the same lit median 3.06; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp245 | 2100 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 3.64-4.48 (median 4.06, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp245 | 2150 | median_vs_lit | 0.833 x lit median | **WARN** | ours 4.23 cm vs lit 4.96-5.20 (median 5.08), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp245 | 2150 | median_vs_lit | 0.796 x lit median | **WARN** | BRICK 2.0 4.04 cm vs the same lit median 5.08; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp245 | 2150 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 5.78-6.87 (median 6.33, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp245 | 2300 | median_vs_lit | 0.787 x lit median | **WARN** | ours 8.48 cm vs lit 10.78-10.78 (median 10.78), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp245 | 2300 | median_vs_lit | 0.825 x lit median | **WARN** | BRICK 2.0 8.90 cm vs the same lit median 10.78; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp245 | 2300 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 12.12-12.12 (median 12.12, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp585 | 2100 | median_vs_lit | 0.871 x lit median | **WARN** | ours 2.60 cm vs lit 2.96-3.01 (median 2.98), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp585 | 2100 | median_vs_lit | 0.786 x lit median | **WARN** | BRICK 2.0 2.34 cm vs the same lit median 2.98; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp585 | 2100 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 3.64-4.12 (median 3.88, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp585 | 2150 | median_vs_lit | 0.875 x lit median | **WARN** | ours 4.23 cm vs lit 4.70-4.96 (median 4.83), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp585 | 2150 | median_vs_lit | 0.836 x lit median | **WARN** | BRICK 2.0 4.04 cm vs the same lit median 4.83; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp585 | 2150 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 5.78-5.80 (median 5.79, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp585 | 2300 | median_vs_lit | 0.787 x lit median | **WARN** | ours 8.48 cm vs lit 10.78-10.78 (median 10.78), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp585 | 2300 | median_vs_lit | 0.825 x lit median | **WARN** | BRICK 2.0 8.90 cm vs the same lit median 10.78; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp585 | 2300 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 12.12-12.12 (median 12.12, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| TOTAL | ssp126 | 2100 | median_vs_lit | 0.916 x lit median | **PASS** | ours 37.80 cm vs lit 35.59-46.11 (median 41.25), n_lit=7 [1 SEJ comparator(s) excluded from the score; full range 35.59-53.47] |
| TOTAL | ssp126 | 2100 | median_vs_lit | 0.998 x lit median | **PASS** | BRICK 2.0 41.16 cm vs the same lit median 41.25; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp126 | 2100 | spread_vs_lit | 0.958 x lit spread | **PASS** | ours 32.14 cm vs model-based lit 25.25-49.52 (median 33.55, n=7); ALL comparators 25.25-107.65 |
| TOTAL | ssp126 | 2150 | median_vs_lit | 0.745 x lit median | **PASS** | ours 49.25 cm vs lit 45.94-74.90 (median 66.11), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 45.94-83.12] |
| TOTAL | ssp126 | 2150 | median_vs_lit | 0.876 x lit median | **PASS** | BRICK 2.0 57.89 cm vs the same lit median 66.11; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp126 | 2150 | spread_vs_lit | 1.072 x lit spread | **PASS** | ours 62.48 cm vs model-based lit 53.31-79.31 (median 58.29, n=4); ALL comparators 53.31-200.59 |
| TOTAL | ssp126 | 2300 | median_vs_lit | 1.066 x lit median | **WARN** | ours 70.85 cm vs lit 66.49-66.49 (median 66.49), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| TOTAL | ssp126 | 2300 | median_vs_lit | 1.425 x lit median | **WARN** | BRICK 2.0 94.76 cm vs the same lit median 66.49; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp126 | 2300 | spread_vs_lit | 1.556 x lit spread | **PASS** | ours 181.37 cm vs model-based lit 116.60-116.60 (median 116.60, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| TOTAL | ssp245 | 2100 | median_vs_lit | 0.885 x lit median | **WARN** | ours 47.34 cm vs lit 48.68-57.10 (median 53.51), n_lit=7 [1 SEJ comparator(s) excluded from the score; full range 48.68-67.90] |
| TOTAL | ssp245 | 2100 | median_vs_lit | 1.312 x lit median | **WARN** | BRICK 2.0 70.19 cm vs the same lit median 53.51; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp245 | 2100 | spread_vs_lit | 1.130 x lit spread | **PASS** | ours 59.48 cm vs model-based lit 32.00-60.35 (median 52.65, n=7); ALL comparators 32.00-146.33 |
| TOTAL | ssp245 | 2150 | median_vs_lit | 0.803 x lit median | **WARN** | ours 74.79 cm vs lit 80.04-105.22 (median 93.13), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 80.04-111.19] |
| TOTAL | ssp245 | 2150 | median_vs_lit | 1.482 x lit median | **WARN** | BRICK 2.0 137.98 cm vs the same lit median 93.13; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp245 | 2150 | spread_vs_lit | 1.233 x lit spread | **WARN** | ours 129.09 cm vs model-based lit 59.41-382.80 (median 104.68, n=4); ALL comparators 59.41-382.80; ⚠ THE COMPARATORS DO NOT AGREE -- scored one at a time they give 1xhigh/2xin/1xlow and the median's 'in' is not a majority, so the median is not a summary here; verdict CAPPED at WARN |
| TOTAL | ssp245 | 2300 | median_vs_lit | 0.851 x lit median | **WARN** | ours 158.93 cm vs lit 186.77-186.77 (median 186.77), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| TOTAL | ssp245 | 2300 | median_vs_lit | 1.702 x lit median | **WARN** | BRICK 2.0 317.82 cm vs the same lit median 186.77; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp245 | 2300 | spread_vs_lit | 1.030 x lit spread | **PASS** | ours 349.87 cm vs model-based lit 339.75-339.75 (median 339.75, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| TOTAL | ssp585 | 2100 | median_vs_lit | 1.087 x lit median | **PASS** | ours 86.30 cm vs lit 64.93-97.85 (median 79.41), n_lit=7 [1 SEJ comparator(s) excluded from the score; full range 64.93-97.85] |
| TOTAL | ssp585 | 2100 | median_vs_lit | 1.234 x lit median | **WARN** | BRICK 2.0 98.00 cm vs the same lit median 79.41; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp585 | 2100 | spread_vs_lit | 1.111 x lit spread | **PASS** | ours 78.12 cm vs model-based lit 41.09-106.79 (median 70.33, n=7); ALL comparators 41.09-197.47 |
| TOTAL | ssp585 | 2150 | median_vs_lit | 0.919 x lit median | **PASS** | ours 190.57 cm vs lit 117.08-310.66 (median 207.31), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 117.08-310.66] |
| TOTAL | ssp585 | 2150 | median_vs_lit | 0.941 x lit median | **PASS** | BRICK 2.0 195.15 cm vs the same lit median 207.31; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp585 | 2150 | spread_vs_lit | 0.526 x lit spread | **WARN** | ours 145.78 cm vs model-based lit 77.93-414.71 (median 277.00, n=4); ALL comparators 77.93-631.59; ⚠ THE COMPARATORS DO NOT AGREE -- scored one at a time they give 2xin/2xlow and the median's 'in' is not a majority, so the median is not a summary here; verdict CAPPED at WARN |
| TOTAL | ssp585 | 2300 | median_vs_lit | 0.488 x lit median | **WARN** | ours 495.34 cm vs lit 1015.98-1015.98 (median 1015.98), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| TOTAL | ssp585 | 2300 | median_vs_lit | 0.461 x lit median | **WARN** | BRICK 2.0 467.87 cm vs the same lit median 1015.98; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp585 | 2300 | spread_vs_lit | 0.287 x lit spread | **WARN** | ours 396.03 cm vs model-based lit 1379.10-1379.10 (median 1379.10, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |

## [P] Levels — every arm side by side (cm)

| module | ssp | horizon | candidate (joint) | champion (joint) | BRICK 2.0 (fixed) |
|---|---|---|---|---|---|
| AIS | ssp126 | 2100 | 4.46 | (is champion) | 4.32 |
| AIS | ssp126 | 2150 | 6.83 | (is champion) | 6.52 |
| AIS | ssp126 | 2300 | 13.48 | (is champion) | 13.01 |
| AIS | ssp245 | 2100 | 5.45 | (is champion) | 27.41 |
| AIS | ssp245 | 2150 | 10.89 | (is champion) | 72.60 |
| AIS | ssp245 | 2300 | 65.92 | (is champion) | 205.94 |
| AIS | ssp585 | 2100 | 29.49 | (is champion) | 44.14 |
| AIS | ssp585 | 2150 | 84.25 | (is champion) | 97.88 |
| AIS | ssp585 | 2300 | 267.49 | (is champion) | 276.83 |
| glaciers | ssp126 | 2100 | 7.99 | (is champion) | 12.09 |
| glaciers | ssp126 | 2150 | 9.86 | (is champion) | 17.44 |
| glaciers | ssp126 | 2300 | 12.40 | (is champion) | 27.72 |
| glaciers | ssp245 | 2100 | 9.64 | (is champion) | 13.34 |
| glaciers | ssp245 | 2150 | 13.35 | (is champion) | 20.69 |
| glaciers | ssp245 | 2300 | 18.33 | (is champion) | 32.50 |
| glaciers | ssp585 | 2100 | 12.88 | (is champion) | 15.61 |
| glaciers | ssp585 | 2150 | 20.40 | (is champion) | 26.25 |
| glaciers | ssp585 | 2300 | 26.65 | (is champion) | 35.36 |
| Greenland | ssp126 | 2100 | 6.52 | (is champion) | 6.62 |
| Greenland | ssp126 | 2150 | 7.97 | (is champion) | 10.01 |
| Greenland | ssp126 | 2300 | 10.04 | (is champion) | 19.04 |
| Greenland | ssp245 | 2100 | 8.16 | (is champion) | 7.03 |
| Greenland | ssp245 | 2150 | 11.87 | (is champion) | 11.35 |
| Greenland | ssp245 | 2300 | 17.16 | (is champion) | 23.71 |
| Greenland | ssp585 | 2100 | 12.04 | (is champion) | 7.88 |
| Greenland | ssp585 | 2150 | 25.56 | (is champion) | 14.77 |
| Greenland | ssp585 | 2300 | 82.92 | (is champion) | 38.60 |
| thermal exp. | ssp126 | 2100 | 16.05 | (is champion) | 15.34 |
| thermal exp. | ssp126 | 2150 | 20.05 | (is champion) | 19.18 |
| thermal exp. | ssp126 | 2300 | 25.72 | (is champion) | 25.08 |
| thermal exp. | ssp245 | 2100 | 20.31 | (is champion) | 19.37 |
| thermal exp. | ssp245 | 2150 | 29.74 | (is champion) | 28.53 |
| thermal exp. | ssp245 | 2300 | 45.98 | (is champion) | 44.66 |
| thermal exp. | ssp585 | 2100 | 28.30 | (is champion) | 27.07 |
| thermal exp. | ssp585 | 2150 | 52.62 | (is champion) | 50.34 |
| thermal exp. | ssp585 | 2300 | 105.22 | (is champion) | 101.88 |
| land water | ssp126 | 2100 | 2.60 | (is champion) | 2.34 |
| land water | ssp126 | 2150 | 4.23 | (is champion) | 4.04 |
| land water | ssp126 | 2300 | 8.48 | (is champion) | 8.90 |
| land water | ssp245 | 2100 | 2.60 | (is champion) | 2.34 |
| land water | ssp245 | 2150 | 4.23 | (is champion) | 4.04 |
| land water | ssp245 | 2300 | 8.48 | (is champion) | 8.90 |
| land water | ssp585 | 2100 | 2.60 | (is champion) | 2.34 |
| land water | ssp585 | 2150 | 4.23 | (is champion) | 4.04 |
| land water | ssp585 | 2300 | 8.48 | (is champion) | 8.90 |
| TOTAL | ssp126 | 2100 | 37.80 | (is champion) | 41.16 |
| TOTAL | ssp126 | 2150 | 49.25 | (is champion) | 57.89 |
| TOTAL | ssp126 | 2300 | 70.85 | (is champion) | 94.76 |
| TOTAL | ssp245 | 2100 | 47.34 | (is champion) | 70.19 |
| TOTAL | ssp245 | 2150 | 74.79 | (is champion) | 137.98 |
| TOTAL | ssp245 | 2300 | 158.93 | (is champion) | 317.82 |
| TOTAL | ssp585 | 2100 | 86.30 | (is champion) | 98.00 |
| TOTAL | ssp585 | 2150 | 190.57 | (is champion) | 195.15 |
| TOTAL | ssp585 | 2300 | 495.34 | (is champion) | 467.87 |

## [S] Scenario separation — ssp585/ssp126 median ratio

| module | horizon | ours | verdict | literature |
|---|---|---|---|---|
| AIS | 2100 | 6.62x | **PASS** | FACTS 0.63-3.20 (n=5); MAGICC-SLR 10.69-10.69 (n=1) |
| AIS | 2150 | 12.33x | **PASS** | FACTS 0.48-7.55 (n=4); MAGICC-SLR 28.79-28.79 (n=1) |
| AIS | 2300 | 19.84x | **WARN** | MAGICC-SLR 81.77-81.77 (n=1)  [NO UPPER COMPARATOR AT THIS HORIZON] |
| glaciers | 2100 | 1.61x | **PASS** | FACTS 1.73-1.92 (n=2); MAGICC-SLR 1.46-1.46 (n=1) |
| glaciers | 2150 | 2.07x | **PASS** | FACTS 2.37-2.37 (n=1); MAGICC-SLR 1.79-1.79 (n=1) |
| glaciers | 2300 | 2.15x | **WARN** | MAGICC-SLR 2.11-2.11 (n=1)  [NO UPPER COMPARATOR AT THIS HORIZON] |
| Greenland | 2100 | 1.85x | **PASS** | FACTS 1.55-2.33 (n=3); MAGICC-SLR 2.11-2.11 (n=1) |
| Greenland | 2150 | 3.21x | **PASS** | FACTS 1.72-2.07 (n=2); MAGICC-SLR 3.48-3.48 (n=1) |
| Greenland | 2300 | 8.26x | **WARN** | MAGICC-SLR 7.54-7.54 (n=1)  [NO UPPER COMPARATOR AT THIS HORIZON] |
| thermal exp. | 2100 | 1.76x | **FAIL** | FACTS 2.05-2.05 (n=1); MAGICC-SLR 2.51-2.51 (n=1); 0.29 outside the bracket = 62% of its own range |
| thermal exp. | 2150 | 2.62x | **FAIL** | FACTS 2.99-2.99 (n=1); MAGICC-SLR 3.94-3.94 (n=1); 0.36 outside the bracket = 38% of its own range |
| thermal exp. | 2300 | 4.09x | **WARN** | MAGICC-SLR 6.18-6.18 (n=1)  [NO UPPER COMPARATOR AT THIS HORIZON] |
| land water | 2100 | 1.00x | **PASS** | FACTS 0.99-0.99 (n=1); MAGICC-SLR 1.00-1.00 (n=1) |
| land water | 2150 | 1.00x | **PASS** | FACTS 1.03-1.03 (n=1); MAGICC-SLR 1.00-1.00 (n=1) |
| land water | 2300 | 1.00x | **PASS** | MAGICC-SLR 1.00-1.00 (n=1)  [NO UPPER COMPARATOR AT THIS HORIZON] |
| TOTAL | 2100 | 2.28x | **PASS** | FACTS 1.63-2.23 (n=7); MAGICC-SLR 2.75-2.75 (n=1) |
| TOTAL | 2150 | 3.87x | **PASS** | FACTS 1.94-4.15 (n=4); MAGICC-SLR 5.72-5.72 (n=1) |
| TOTAL | 2300 | 6.99x | **WARN** | MAGICC-SLR 15.28-15.28 (n=1)  [NO UPPER COMPARATOR AT THIS HORIZON] |

---

*Machine-readable: `outputs/bench_ladrillo_L21.csv`. Regenerate: `python python/bench_ladrillo.py --tag=L21`.*
