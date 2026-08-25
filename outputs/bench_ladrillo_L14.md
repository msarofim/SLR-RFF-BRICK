# Ladrillo benchmark — `L14`

*benchmark v1.0, 2026-08-25, repo `12b3eeb`. Champion arm: **L14** (the candidate IS the champion — no delta column).*

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
| **AIS** | PASS | UNRESOLVED | WARN | WARN | — |
| **glaciers** | WARN | WARN | WARN | WARN | — |
| **Greenland** | PASS | UNRESOLVED | FAIL | WARN | — |
| **thermal exp.** | WARN | FAIL | WARN | WARN | — |
| **land water** | — | — | WARN | PASS | — |
| **TOTAL** | PASS | UNRESOLVED | FAIL | WARN | — |

## [H] Hindcast — the full observational period, scaled to each component's own target 1-sigma

| module | target 1σ (cm) | window | arm | RMSE (cm) | RMSE (σ) | note |
|---|---|---|---|---|---|---|
| AIS | 0.1674 | full | L14 | 0.0308 | 0.18 | bias -0.0012 cm = -0.01 sd; cov90 83%; n=106 |
| AIS | 0.1674 | full | BRICK 2.0 | 1.1758 | 7.02 | bias -0.8211 cm = -4.90 sd; cov90 31%; n=106 |
| AIS | 0.1674 | 1920-1949 | L14 | 0.0058 | 0.03 | bias -0.0045 cm = -0.03 sd; cov90 100%; n=30 |
| AIS | 0.1674 | 1920-1949 | BRICK 2.0 | 1.9843 | 11.85 | bias -1.9579 cm = -11.69 sd; cov90 0%; n=30 |
| AIS | 0.1674 | 1950-1992 | L14 | 0.0067 | 0.04 | bias +0.0039 cm = +0.02 sd; cov90 98%; n=43 |
| AIS | 0.1674 | 1950-1992 | BRICK 2.0 | 0.8082 | 4.83 | bias -0.7053 cm = -4.21 sd; cov90 2%; n=43 |
| AIS | 0.1674 | 1993-2026 | L14 | 0.0544 | 0.32 | bias -0.0047 cm = -0.03 sd; cov90 48%; n=33 |
| AIS | 0.1674 | 1993-2026 | BRICK 2.0 | 0.0992 | 0.59 | bias +0.0615 cm = +0.37 sd; cov90 97%; n=33 |
| glaciers | 0.4593 | full | L14 | 0.3308 | 0.72 | bias +0.1671 cm = +0.36 sd; cov90 54%; n=104 |
| glaciers | 0.4593 | full | BRICK 2.0 | 0.8941 | 1.95 | bias +0.5000 cm = +1.09 sd; cov90 47%; n=104 |
| glaciers | 0.4593 | 1920-1949 | L14 | 0.5888 | 1.28 | bias +0.5246 cm = +1.14 sd; cov90 23%; n=30 |
| glaciers | 0.4593 | 1920-1949 | BRICK 2.0 | 1.6382 | 3.57 | bias +1.5142 cm = +3.30 sd; cov90 0%; n=30 |
| glaciers | 0.4593 | 1950-1992 | L14 | 0.1326 | 0.29 | bias +0.0743 cm = +0.16 sd; cov90 56%; n=43 |
| glaciers | 0.4593 | 1950-1992 | BRICK 2.0 | 0.1311 | 0.29 | bias +0.0341 cm = +0.07 sd; cov90 95%; n=43 |
| glaciers | 0.4593 | 1993-2026 | L14 | 0.0848 | 0.18 | bias -0.0502 cm = -0.11 sd; cov90 81%; n=31 |
| glaciers | 0.4593 | 1993-2026 | BRICK 2.0 | 0.2460 | 0.54 | bias +0.1647 cm = +0.36 sd; cov90 26%; n=31 |
| Greenland | 0.1832 | full | L14 | 0.0590 | 0.32 | bias +0.0020 cm = +0.01 sd; cov90 57%; n=106 |
| Greenland | 0.1832 | full | BRICK 2.0 | 0.7230 | 3.95 | bias -0.5975 cm = -3.26 sd; cov90 22%; n=106 |
| Greenland | 0.1832 | 1920-1949 | L14 | 0.0805 | 0.44 | bias +0.0266 cm = +0.15 sd; cov90 60%; n=30 |
| Greenland | 0.1832 | 1920-1949 | BRICK 2.0 | 0.7876 | 4.30 | bias -0.7371 cm = -4.02 sd; cov90 27%; n=30 |
| Greenland | 0.1832 | 1950-1992 | L14 | 0.0494 | 0.27 | bias -0.0149 cm = -0.08 sd; cov90 60%; n=43 |
| Greenland | 0.1832 | 1950-1992 | BRICK 2.0 | 0.9132 | 4.99 | bias -0.8659 cm = -4.73 sd; cov90 0%; n=43 |
| Greenland | 0.1832 | 1993-2026 | L14 | 0.0458 | 0.25 | bias +0.0017 cm = +0.01 sd; cov90 48%; n=33 |
| Greenland | 0.1832 | 1993-2026 | BRICK 2.0 | 0.1686 | 0.92 | bias -0.1209 cm = -0.66 sd; cov90 45%; n=33 |
| thermal exp. | 0.3091 | full | L14 | 0.3202 | 1.04 | bias +0.1808 cm = +0.59 sd; cov90 28%; n=106 |
| thermal exp. | 0.3091 | full | BRICK 2.0 | 0.3243 | 1.05 | bias +0.1908 cm = +0.62 sd; cov90 96%; n=106 |
| thermal exp. | 0.3091 | 1920-1949 | L14 | 0.4475 | 1.45 | bias +0.3576 cm = +1.16 sd; cov90 30%; n=30 |
| thermal exp. | 0.3091 | 1920-1949 | BRICK 2.0 | 0.4741 | 1.53 | bias +0.3885 cm = +1.26 sd; cov90 100%; n=30 |
| thermal exp. | 0.3091 | 1950-1992 | L14 | 0.1847 | 0.60 | bias +0.0333 cm = +0.11 sd; cov90 37%; n=43 |
| thermal exp. | 0.3091 | 1950-1992 | BRICK 2.0 | 0.1897 | 0.61 | bias +0.0499 cm = +0.16 sd; cov90 100%; n=43 |
| thermal exp. | 0.3091 | 1993-2026 | L14 | 0.3207 | 1.04 | bias +0.2123 cm = +0.69 sd; cov90 15%; n=33 |
| thermal exp. | 0.3091 | 1993-2026 | BRICK 2.0 | 0.2941 | 0.95 | bias +0.1946 cm = +0.63 sd; cov90 88%; n=33 |
| TOTAL | 1.5380 | full | L14 | 0.6923 | 0.45 | bias +0.5606 cm = +0.36 sd; cov90 26%; n=105 |
| TOTAL | 1.5380 | full | BRICK 2.0 | 1.8198 | 1.18 | bias -1.3318 cm = -0.87 sd; cov90 25%; n=105 |
| TOTAL | 1.5380 | 1920-1949 | L14 | 0.9777 | 0.64 | bias +0.9346 cm = +0.61 sd; cov90 40%; n=30 |
| TOTAL | 1.5380 | 1920-1949 | BRICK 2.0 | 2.5470 | 1.66 | bias -2.4846 cm = -1.62 sd; cov90 0%; n=30 |
| TOTAL | 1.5380 | 1950-1992 | L14 | 0.6590 | 0.43 | bias +0.6151 cm = +0.40 sd; cov90 5%; n=43 |
| TOTAL | 1.5380 | 1950-1992 | BRICK 2.0 | 1.8672 | 1.21 | bias -1.5605 cm = -1.01 sd; cov90 12%; n=43 |
| TOTAL | 1.5380 | 1993-2026 | L14 | 0.3053 | 0.20 | bias +0.1368 cm = +0.09 sd; cov90 41%; n=32 |
| TOTAL | 1.5380 | 1993-2026 | BRICK 2.0 | 0.3164 | 0.21 | bias +0.0564 cm = +0.04 sd; cov90 66%; n=32 |

## [R] Rate (1993-2026) and acceleration (1900-2026), with an error bar on the observations

| module | statistic | arm | value | unit | z vs obs bar | note |
|---|---|---|---|---|---|---|
| AIS | rate | observations | 0.032608 | cm/yr | — | se: estimator 0.003405, band-correlated 0.0005689, band-independent 0.003061; CONSERVATIVE 0.003405 cm/yr; |obs|/se = 9.58 |
| AIS | rate | L14 | 0.031707 | cm/yr | -0.26 | 0.97x obs; z=-0.26 vs the obs error bar |
| AIS | rate | BRICK 2.0 | 0.039301 | cm/yr | +1.97 | 1.21x obs; z=+1.97 vs the obs error bar |
| glaciers | rate | observations | 0.068013 | cm/yr | — | se: estimator 0.0005236, band-correlated 0.0001274, band-independent 0.009223; CONSERVATIVE 0.009223 cm/yr; |obs|/se = 7.37 |
| glaciers | rate | L14 | 0.063042 | cm/yr | -0.54 | 0.93x obs; z=-0.54 vs the obs error bar |
| glaciers | rate | BRICK 2.0 | 0.090078 | cm/yr | +2.39 | 1.32x obs; z=+2.39 vs the obs error bar |
| Greenland | rate | observations | 0.06596 | cm/yr | — | se: estimator 0.01044, band-correlated 0.0006502, band-independent 0.003349; CONSERVATIVE 0.01044 cm/yr; |obs|/se = 6.32 |
| Greenland | rate | L14 | 0.065777 | cm/yr | -0.02 | 1.00x obs; z=-0.02 vs the obs error bar |
| Greenland | rate | BRICK 2.0 | 0.058529 | cm/yr | -0.71 | 0.89x obs; z=-0.71 vs the obs error bar |
| thermal exp. | rate | observations | 0.1234 | cm/yr | — | se: estimator 0.003756, band-correlated 0.002392, band-independent 0.005651; CONSERVATIVE 0.005651 cm/yr; |obs|/se = 21.84 |
| thermal exp. | rate | L14 | 0.14708 | cm/yr | +4.19 | 1.19x obs; z=+4.19 vs the obs error bar |
| thermal exp. | rate | BRICK 2.0 | 0.14454 | cm/yr | +3.74 | 1.17x obs; z=+3.74 vs the obs error bar |
| TOTAL | rate | observations | 0.32469 | cm/yr | — | se: estimator 0.02949, band-correlated 0.02545, band-independent 0.02945; CONSERVATIVE 0.02949 cm/yr; |obs|/se = 11.01 |
| TOTAL | rate | L14 | 0.3373 | cm/yr | +0.43 | 1.04x obs; z=+0.43 vs the obs error bar |
| TOTAL | rate | BRICK 2.0 | 0.33831 | cm/yr | +0.46 | 1.04x obs; z=+0.46 vs the obs error bar |
| AIS | accel | observations | 0.00020499 | cm/yr2 | — | se: estimator 0.0001336, band-correlated 3.924e-05, band-independent 2.522e-05; CONSERVATIVE 0.0001336 cm/yr2; |obs|/se = 1.53 |
| AIS | accel | L14 | 0.00020186 | cm/yr2 | -0.02 | ratio NOT INTERPRETABLE (obs is 1.53 se from zero); z=-0.02 vs the obs error bar |
| AIS | accel | BRICK 2.0 | -9.5414e-05 | cm/yr2 | -2.25 | ratio NOT INTERPRETABLE (obs is 1.53 se from zero); z=-2.25 vs the obs error bar |
| glaciers | accel | observations | -0.00054814 | cm/yr2 | — | se: estimator 0.000447, band-correlated 3.442e-05, band-independent 7.199e-05; CONSERVATIVE 0.000447 cm/yr2; |obs|/se = 1.23 |
| glaciers | accel | L14 | -9.9967e-05 | cm/yr2 | +1.00 | ratio NOT INTERPRETABLE (obs is 1.23 se from zero); z=+1.00 vs the obs error bar |
| glaciers | accel | BRICK 2.0 | 0.00082242 | cm/yr2 | +3.07 | ratio NOT INTERPRETABLE (obs is 1.23 se from zero); z=+3.07 vs the obs error bar |
| Greenland | accel | observations | -0.00027825 | cm/yr2 | — | se: estimator 0.0005241, band-correlated 6.83e-05, band-independent 2.759e-05; CONSERVATIVE 0.0005241 cm/yr2; |obs|/se = 0.53 |
| Greenland | accel | L14 | -0.00025027 | cm/yr2 | +0.05 | ratio NOT INTERPRETABLE (obs is 0.53 se from zero); z=+0.05 vs the obs error bar |
| Greenland | accel | BRICK 2.0 | 0.00014987 | cm/yr2 | +0.82 | ratio NOT INTERPRETABLE (obs is 0.53 se from zero); z=+0.82 vs the obs error bar |
| thermal exp. | accel | observations | 0.0008428 | cm/yr2 | — | se: estimator 0.0002431, band-correlated 2.312e-05, band-independent 4.655e-05; CONSERVATIVE 0.0002431 cm/yr2; |obs|/se = 3.47 |
| thermal exp. | accel | L14 | 0.00099983 | cm/yr2 | +0.65 | 1.19x obs; z=+0.65 vs the obs error bar |
| thermal exp. | accel | BRICK 2.0 | 0.0013015 | cm/yr2 | +1.89 | 1.54x obs; z=+1.89 vs the obs error bar |
| TOTAL | accel | observations | 0.00089376 | cm/yr2 | — | se: estimator 0.001159, band-correlated 0.0001276, band-independent 0.0002363; CONSERVATIVE 0.001159 cm/yr2; |obs|/se = 0.77 |
| TOTAL | accel | L14 | 0.0010226 | cm/yr2 | +0.11 | ratio NOT INTERPRETABLE (obs is 0.77 se from zero); z=+0.11 vs the obs error bar |
| TOTAL | accel | BRICK 2.0 | 0.0022411 | cm/yr2 | +1.16 | ratio NOT INTERPRETABLE (obs is 0.77 se from zero); z=+1.16 vs the obs error bar |

## [P] Projections vs the literature — scored on the JOINT band

| module | ssp | horizon | metric | value | verdict | note |
|---|---|---|---|---|---|---|
| AIS | ssp126 | 2100 | median_vs_lit | 0.480 x lit median | **PASS** | ours 4.29 cm vs lit 3.66-11.90 (median 8.94), n_lit=5 [1 SEJ comparator(s) excluded from the score; full range 3.66-11.90]; ⚠ BIMODAL cell -- our MEAN is 6.16 cm = 0.69x the literature median, and the median sits entirely inside the near mode |
| AIS | ssp126 | 2100 | spread_vs_lit | 0.327 x lit spread | **N/A(bimodal)** | ours 6.91 cm vs model-based lit 9.86-39.27 (median 21.11, n=5); ALL comparators 9.86-91.07; ⚠ p05-p99/p05-p95 = 8.45 vs Gaussian 1.207 => BIMODAL, and p95 is blind to the far mode (p05-p99 = 58.39 cm). The p5-p95 ratio is a property of the QUANTILE here, not of the model |
| AIS | ssp126 | 2150 | median_vs_lit | 0.364 x lit median | **PASS** | ours 6.53 cm vs lit 5.34-26.34 (median 17.92), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 5.34-26.34]; ⚠ BIMODAL cell -- our MEAN is 10.40 cm = 0.58x the literature median, and the median sits entirely inside the near mode |
| AIS | ssp126 | 2150 | spread_vs_lit | 0.320 x lit spread | **N/A(bimodal)** | ours 14.78 cm vs model-based lit 33.17-72.55 (median 46.14, n=4); ALL comparators 33.17-156.27; ⚠ p05-p99/p05-p95 = 7.44 vs Gaussian 1.207 => BIMODAL, and p95 is blind to the far mode (p05-p99 = 109.98 cm). The p5-p95 ratio is a property of the QUANTILE here, not of the model |
| AIS | ssp126 | 2300 | median_vs_lit | 1.455 x lit median | **WARN** | ours 12.67 cm vs lit 8.71-8.71 (median 8.71), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN; ⚠ BIMODAL cell -- our MEAN is 23.99 cm = 2.75x the literature median, and the median sits entirely inside the near mode |
| AIS | ssp126 | 2300 | spread_vs_lit | 1.108 x lit spread | **N/A(bimodal)** | ours 77.09 cm vs model-based lit 69.60-69.60 (median 69.60, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; ⚠ p05-p99/p05-p95 = 3.55 vs Gaussian 1.207 => BIMODAL, and p95 is blind to the far mode (p05-p99 = 273.50 cm). The p5-p95 ratio is a property of the QUANTILE here, not of the model |
| AIS | ssp245 | 2100 | median_vs_lit | 0.531 x lit median | **WARN** | ours 5.51 cm vs lit 5.54-12.73 (median 10.38), n_lit=5 [1 SEJ comparator(s) excluded from the score; full range 5.54-13.71] |
| AIS | ssp245 | 2100 | spread_vs_lit | 1.208 x lit spread | **PASS** | ours 43.26 cm vs model-based lit 20.88-44.94 (median 35.81, n=5); ALL comparators 20.88-109.87 |
| AIS | ssp245 | 2150 | median_vs_lit | 0.406 x lit median | **PASS** | ours 11.16 cm vs lit 10.91-30.28 (median 27.45), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 10.91-30.28] |
| AIS | ssp245 | 2150 | spread_vs_lit | 1.234 x lit spread | **PASS** | ours 103.80 cm vs model-based lit 44.92-369.45 (median 84.10, n=4); ALL comparators 44.92-369.45 |
| AIS | ssp245 | 2300 | median_vs_lit | 0.949 x lit median | **WARN** | ours 79.23 cm vs lit 83.46-83.46 (median 83.46), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| AIS | ssp245 | 2300 | spread_vs_lit | 1.111 x lit spread | **PASS** | ours 301.74 cm vs model-based lit 271.56-271.56 (median 271.56, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| AIS | ssp585 | 2100 | median_vs_lit | 2.430 x lit median | **PASS** | ours 35.05 cm vs lit 3.98-39.10 (median 14.43), n_lit=5 [1 SEJ comparator(s) excluded from the score; full range 3.98-39.10] |
| AIS | ssp585 | 2100 | spread_vs_lit | 1.130 x lit spread | **PASS** | ours 63.80 cm vs model-based lit 20.51-79.00 (median 56.48, n=5); ALL comparators 20.51-151.54; width here is the antarctic_lambda PRIOR -- do NOT narrow |
| AIS | ssp585 | 2150 | median_vs_lit | 0.964 x lit median | **PASS** | ours 92.13 cm vs lit 6.26-198.76 (median 95.53), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 6.26-198.76] |
| AIS | ssp585 | 2150 | spread_vs_lit | 0.525 x lit spread | **PASS** | ours 107.81 cm vs model-based lit 48.68-408.37 (median 205.25, n=4); ALL comparators 48.68-570.98; width here is the antarctic_lambda PRIOR -- do NOT narrow |
| AIS | ssp585 | 2300 | median_vs_lit | 1.016 x lit median | **PASS** | ours 277.34 cm vs lit 267.00-712.02 (median 273.00), n_lit=3 |
| AIS | ssp585 | 2300 | spread_vs_lit | 0.321 x lit spread | **WARN** | ours 303.07 cm vs model-based lit 944.94-944.94 (median 944.94, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; width here is the antarctic_lambda PRIOR -- do NOT narrow |
| glaciers | ssp126 | 2100 | median_vs_lit | 0.836 x lit median | **WARN** | ours 7.73 cm vs lit 8.95-10.45 (median 9.25), n_lit=3 |
| glaciers | ssp126 | 2100 | spread_vs_lit | 0.816 x lit spread | **PASS** | ours 6.00 cm vs model-based lit 7.12-7.85 (median 7.36, n=3) |
| glaciers | ssp126 | 2150 | median_vs_lit | 0.776 x lit median | **WARN** | ours 9.42 cm vs lit 12.00-12.28 (median 12.14), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp126 | 2150 | spread_vs_lit | 0.779 x lit spread | **PASS** | ours 7.95 cm vs model-based lit 8.52-11.89 (median 10.21, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| glaciers | ssp126 | 2300 | median_vs_lit | 0.855 x lit median | **WARN** | ours 11.80 cm vs lit 13.80-13.80 (median 13.80), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp126 | 2300 | spread_vs_lit | 0.980 x lit spread | **PASS** | ours 11.01 cm vs model-based lit 11.23-11.23 (median 11.23, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| glaciers | ssp245 | 2100 | median_vs_lit | 0.800 x lit median | **WARN** | ours 9.77 cm vs lit 11.38-12.54 (median 12.21), n_lit=3 |
| glaciers | ssp245 | 2100 | spread_vs_lit | 0.872 x lit spread | **PASS** | ours 6.70 cm vs model-based lit 7.42-9.60 (median 7.68, n=3) |
| glaciers | ssp245 | 2150 | median_vs_lit | 0.788 x lit median | **WARN** | ours 13.49 cm vs lit 16.71-17.53 (median 17.12), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp245 | 2150 | spread_vs_lit | 0.747 x lit spread | **PASS** | ours 9.65 cm vs model-based lit 9.16-16.65 (median 12.91, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| glaciers | ssp245 | 2300 | median_vs_lit | 0.847 x lit median | **WARN** | ours 18.19 cm vs lit 21.47-21.47 (median 21.47), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp245 | 2300 | spread_vs_lit | 1.175 x lit spread | **PASS** | ours 12.86 cm vs model-based lit 10.95-10.95 (median 10.95, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| glaciers | ssp585 | 2100 | median_vs_lit | 0.906 x lit median | **WARN** | ours 14.00 cm vs lit 15.30-17.73 (median 15.46), n_lit=3 |
| glaciers | ssp585 | 2100 | spread_vs_lit | 0.942 x lit spread | **PASS** | ours 8.87 cm vs model-based lit 8.51-13.85 (median 9.41, n=3) |
| glaciers | ssp585 | 2150 | median_vs_lit | 0.851 x lit median | **WARN** | ours 21.45 cm vs lit 22.03-28.40 (median 25.22), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp585 | 2150 | spread_vs_lit | 0.897 x lit spread | **PASS** | ours 11.49 cm vs model-based lit 10.09-15.53 (median 12.81, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| glaciers | ssp585 | 2300 | median_vs_lit | 0.928 x lit median | **WARN** | ours 27.01 cm vs lit 29.10-29.10 (median 29.10), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp585 | 2300 | spread_vs_lit | 1.215 x lit spread | **PASS** | ours 11.95 cm vs model-based lit 9.83-9.83 (median 9.83, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| Greenland | ssp126 | 2100 | median_vs_lit | 0.976 x lit median | **PASS** | ours 6.25 cm vs lit 5.46-7.67 (median 6.40), n_lit=3 [1 SEJ comparator(s) excluded from the score; full range 5.46-13.05] |
| Greenland | ssp126 | 2100 | spread_vs_lit | 0.489 x lit spread | **FAIL** | ours 4.69 cm vs model-based lit 7.06-17.14 (median 9.57, n=3); ALL comparators 7.06-55.71 |
| Greenland | ssp126 | 2150 | median_vs_lit | 0.674 x lit median | **WARN** | ours 7.58 cm vs lit 9.31-13.18 (median 11.25), n_lit=2 [1 SEJ comparator(s) excluded from the score; full range 9.31-22.20] ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp126 | 2150 | spread_vs_lit | 0.515 x lit spread | **PASS** | ours 6.90 cm vs model-based lit 11.12-15.69 (median 13.40, n=2); ALL comparators 11.12-86.94; ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| Greenland | ssp126 | 2300 | median_vs_lit | 0.632 x lit median | **WARN** | ours 9.47 cm vs lit 14.98-14.98 (median 14.98), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp126 | 2300 | spread_vs_lit | 0.399 x lit spread | **WARN** | ours 11.74 cm vs model-based lit 29.41-29.41 (median 29.41, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |
| Greenland | ssp245 | 2100 | median_vs_lit | 0.882 x lit median | **PASS** | ours 8.19 cm vs lit 7.97-10.21 (median 9.28), n_lit=3 [1 SEJ comparator(s) excluded from the score; full range 7.97-14.39] |
| Greenland | ssp245 | 2100 | spread_vs_lit | 0.687 x lit spread | **PASS** | ours 5.73 cm vs model-based lit 7.85-16.85 (median 8.35, n=3); ALL comparators 7.85-72.68 |
| Greenland | ssp245 | 2150 | median_vs_lit | 0.689 x lit median | **WARN** | ours 11.96 cm vs lit 16.53-18.19 (median 17.36), n_lit=2 [1 SEJ comparator(s) excluded from the score; full range 16.53-25.62] ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp245 | 2150 | spread_vs_lit | 0.743 x lit spread | **PASS** | ours 11.08 cm vs model-based lit 14.88-14.93 (median 14.91, n=2); ALL comparators 14.88-88.90; ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| Greenland | ssp245 | 2300 | median_vs_lit | 0.478 x lit median | **WARN** | ours 17.12 cm vs lit 35.79-35.79 (median 35.79), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp245 | 2300 | spread_vs_lit | 0.512 x lit spread | **PASS** | ours 20.95 cm vs model-based lit 40.91-40.91 (median 40.91, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| Greenland | ssp585 | 2100 | median_vs_lit | 0.989 x lit median | **PASS** | ours 13.35 cm vs lit 12.72-14.02 (median 13.49), n_lit=3 [1 SEJ comparator(s) excluded from the score; full range 12.72-20.28] |
| Greenland | ssp585 | 2100 | spread_vs_lit | 0.922 x lit spread | **PASS** | ours 11.21 cm vs model-based lit 11.46-17.10 (median 12.15, n=3); ALL comparators 11.46-93.18 |
| Greenland | ssp585 | 2150 | median_vs_lit | 0.904 x lit median | **WARN** | ours 26.99 cm vs lit 27.33-32.40 (median 29.87), n_lit=2 [1 SEJ comparator(s) excluded from the score; full range 27.33-38.13] ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp585 | 2150 | spread_vs_lit | 0.464 x lit spread | **WARN** | ours 26.88 cm vs model-based lit 24.97-90.97 (median 57.97, n=2); ALL comparators 24.97-121.86; ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |
| Greenland | ssp585 | 2300 | median_vs_lit | 0.420 x lit median | **WARN** | ours 47.48 cm vs lit 113.01-113.01 (median 113.01), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp585 | 2300 | spread_vs_lit | 0.089 x lit spread | **WARN** | ours 60.73 cm vs model-based lit 680.24-680.24 (median 680.24, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |
| thermal exp. | ssp126 | 2100 | median_vs_lit | 1.075 x lit median | **PASS** | ours 13.51 cm vs lit 11.09-14.05 (median 12.57), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp126 | 2100 | spread_vs_lit | 0.886 x lit spread | **PASS** | ours 10.29 cm vs model-based lit 11.26-11.97 (median 11.61, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp126 | 2150 | median_vs_lit | 1.106 x lit median | **PASS** | ours 16.88 cm vs lit 12.68-17.85 (median 15.26), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp126 | 2150 | spread_vs_lit | 0.898 x lit spread | **PASS** | ours 14.83 cm vs model-based lit 16.06-16.96 (median 16.51, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp126 | 2300 | median_vs_lit | 1.319 x lit median | **WARN** | ours 22.08 cm vs lit 16.74-16.74 (median 16.74), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| thermal exp. | ssp126 | 2300 | spread_vs_lit | 1.066 x lit spread | **PASS** | ours 27.16 cm vs model-based lit 25.47-25.47 (median 25.47, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp245 | 2100 | median_vs_lit | 1.000 x lit median | **PASS** | ours 17.73 cm vs lit 16.62-18.84 (median 17.73), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp245 | 2100 | spread_vs_lit | 0.814 x lit spread | **PASS** | ours 11.80 cm vs model-based lit 13.73-15.26 (median 14.49, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp245 | 2150 | median_vs_lit | 1.012 x lit median | **PASS** | ours 26.26 cm vs lit 23.23-28.64 (median 25.94), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp245 | 2150 | spread_vs_lit | 0.816 x lit spread | **PASS** | ours 20.32 cm vs model-based lit 23.92-25.87 (median 24.90, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp245 | 2300 | median_vs_lit | 1.121 x lit median | **WARN** | ours 40.67 cm vs lit 36.30-36.30 (median 36.30), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| thermal exp. | ssp245 | 2300 | spread_vs_lit | 0.793 x lit spread | **PASS** | ours 43.01 cm vs model-based lit 54.25-54.25 (median 54.25, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp585 | 2100 | median_vs_lit | 0.938 x lit median | **WARN** | ours 26.60 cm vs lit 27.88-28.82 (median 28.35), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| thermal exp. | ssp585 | 2100 | spread_vs_lit | 0.785 x lit spread | **PASS** | ours 17.27 cm vs model-based lit 21.13-22.88 (median 22.00, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp585 | 2150 | median_vs_lit | 0.950 x lit median | **WARN** | ours 49.06 cm vs lit 49.94-53.35 (median 51.64), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| thermal exp. | ssp585 | 2150 | spread_vs_lit | 0.804 x lit spread | **PASS** | ours 36.16 cm vs model-based lit 41.87-48.08 (median 44.98, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp585 | 2300 | median_vs_lit | 0.952 x lit median | **WARN** | ours 98.47 cm vs lit 103.49-103.49 (median 103.49), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| thermal exp. | ssp585 | 2300 | spread_vs_lit | 0.781 x lit spread | **PASS** | ours 94.80 cm vs model-based lit 121.40-121.40 (median 121.40, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| land water | ssp126 | 2100 | median_vs_lit | 0.865 x lit median | **WARN** | ours 2.60 cm vs lit 2.99-3.01 (median 3.00), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp126 | 2100 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 3.64-4.06 (median 3.85, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp126 | 2150 | median_vs_lit | 0.887 x lit median | **WARN** | ours 4.23 cm vs lit 4.58-4.96 (median 4.77), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp126 | 2150 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 5.64-5.78 (median 5.71, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp126 | 2300 | median_vs_lit | 0.787 x lit median | **WARN** | ours 8.48 cm vs lit 10.78-10.78 (median 10.78), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp126 | 2300 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 12.12-12.12 (median 12.12, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp245 | 2100 | median_vs_lit | 0.848 x lit median | **WARN** | ours 2.60 cm vs lit 3.01-3.11 (median 3.06), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp245 | 2100 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 3.64-4.48 (median 4.06, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp245 | 2150 | median_vs_lit | 0.833 x lit median | **WARN** | ours 4.23 cm vs lit 4.96-5.20 (median 5.08), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp245 | 2150 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 5.78-6.87 (median 6.33, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp245 | 2300 | median_vs_lit | 0.787 x lit median | **WARN** | ours 8.48 cm vs lit 10.78-10.78 (median 10.78), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp245 | 2300 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 12.12-12.12 (median 12.12, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp585 | 2100 | median_vs_lit | 0.871 x lit median | **WARN** | ours 2.60 cm vs lit 2.96-3.01 (median 2.98), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp585 | 2100 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 3.64-4.12 (median 3.88, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp585 | 2150 | median_vs_lit | 0.875 x lit median | **WARN** | ours 4.23 cm vs lit 4.70-4.96 (median 4.83), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp585 | 2150 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 5.78-5.80 (median 5.79, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp585 | 2300 | median_vs_lit | 0.787 x lit median | **WARN** | ours 8.48 cm vs lit 10.78-10.78 (median 10.78), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp585 | 2300 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 12.12-12.12 (median 12.12, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| TOTAL | ssp126 | 2100 | median_vs_lit | 0.814 x lit median | **WARN** | ours 34.33 cm vs lit 35.59-53.47 (median 42.18), n_lit=8; ⚠ BIMODAL cell -- our MEAN is 36.92 cm = 0.88x the literature median, and the median sits entirely inside the near mode |
| TOTAL | ssp126 | 2100 | spread_vs_lit | 0.681 x lit spread | **N/A(bimodal)** | ours 24.33 cm vs model-based lit 25.25-107.65 (median 35.74, n=8); ⚠ p05-p99/p05-p95 = 3.04 vs Gaussian 1.207 => BIMODAL, and p95 is blind to the far mode (p05-p99 = 73.87 cm). The p5-p95 ratio is a property of the QUANTILE here, not of the model |
| TOTAL | ssp126 | 2150 | median_vs_lit | 0.620 x lit median | **WARN** | ours 44.64 cm vs lit 45.94-83.12 (median 72.02), n_lit=5; ⚠ BIMODAL cell -- our MEAN is 49.52 cm = 0.69x the literature median, and the median sits entirely inside the near mode |
| TOTAL | ssp126 | 2150 | spread_vs_lit | 0.619 x lit spread | **N/A(bimodal)** | ours 36.51 cm vs model-based lit 53.31-200.59 (median 58.97, n=5); ⚠ p05-p99/p05-p95 = 3.76 vs Gaussian 1.207 => BIMODAL, and p95 is blind to the far mode (p05-p99 = 137.35 cm). The p5-p95 ratio is a property of the QUANTILE here, not of the model |
| TOTAL | ssp126 | 2300 | median_vs_lit | 0.969 x lit median | **WARN** | ours 64.44 cm vs lit 66.49-66.49 (median 66.49), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN; ⚠ BIMODAL cell -- our MEAN is 77.68 cm = 1.17x the literature median, and the median sits entirely inside the near mode |
| TOTAL | ssp126 | 2300 | spread_vs_lit | 1.026 x lit spread | **N/A(bimodal)** | ours 119.61 cm vs model-based lit 116.60-116.60 (median 116.60, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; ⚠ p05-p99/p05-p95 = 2.59 vs Gaussian 1.207 => BIMODAL, and p95 is blind to the far mode (p05-p99 = 309.32 cm). The p5-p95 ratio is a property of the QUANTILE here, not of the model |
| TOTAL | ssp245 | 2100 | median_vs_lit | 0.827 x lit median | **WARN** | ours 44.92 cm vs lit 48.68-67.90 (median 54.29), n_lit=8 |
| TOTAL | ssp245 | 2100 | spread_vs_lit | 1.090 x lit spread | **PASS** | ours 59.55 cm vs model-based lit 32.00-146.33 (median 54.65, n=8) |
| TOTAL | ssp245 | 2150 | median_vs_lit | 0.729 x lit median | **WARN** | ours 71.57 cm vs lit 80.04-111.19 (median 98.15), n_lit=5 |
| TOTAL | ssp245 | 2150 | spread_vs_lit | 1.191 x lit spread | **PASS** | ours 128.99 cm vs model-based lit 59.41-382.80 (median 108.33, n=5) |
| TOTAL | ssp245 | 2300 | median_vs_lit | 0.872 x lit median | **WARN** | ours 162.84 cm vs lit 186.77-186.77 (median 186.77), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| TOTAL | ssp245 | 2300 | spread_vs_lit | 1.022 x lit spread | **PASS** | ours 347.18 cm vs model-based lit 339.75-339.75 (median 339.75, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| TOTAL | ssp585 | 2100 | median_vs_lit | 1.086 x lit median | **PASS** | ours 92.45 cm vs lit 64.93-97.85 (median 85.09), n_lit=8 |
| TOTAL | ssp585 | 2100 | spread_vs_lit | 1.159 x lit spread | **PASS** | ours 81.94 cm vs model-based lit 41.09-197.47 (median 70.69, n=8) |
| TOTAL | ssp585 | 2150 | median_vs_lit | 1.205 x lit median | **PASS** | ours 195.59 cm vs lit 117.08-310.66 (median 162.34), n_lit=5 |
| TOTAL | ssp585 | 2150 | spread_vs_lit | 0.365 x lit spread | **FAIL** | ours 147.38 cm vs model-based lit 77.93-631.59 (median 403.38, n=5) |
| TOTAL | ssp585 | 2300 | median_vs_lit | 0.454 x lit median | **WARN** | ours 461.72 cm vs lit 1015.98-1015.98 (median 1015.98), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| TOTAL | ssp585 | 2300 | spread_vs_lit | 0.279 x lit spread | **WARN** | ours 385.07 cm vs model-based lit 1379.10-1379.10 (median 1379.10, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |

## [P] Levels — every arm side by side (cm)

| module | ssp | horizon | candidate (joint) | champion (joint) | BRICK 2.0 (fixed) |
|---|---|---|---|---|---|
| AIS | ssp126 | 2100 | 4.29 | (is champion) | 4.21 |
| AIS | ssp126 | 2150 | 6.53 | (is champion) | 6.37 |
| AIS | ssp126 | 2300 | 12.67 | (is champion) | 12.64 |
| AIS | ssp245 | 2100 | 5.51 | (is champion) | 29.21 |
| AIS | ssp245 | 2150 | 11.16 | (is champion) | 74.53 |
| AIS | ssp245 | 2300 | 79.23 | (is champion) | 207.88 |
| AIS | ssp585 | 2100 | 35.05 | (is champion) | 48.98 |
| AIS | ssp585 | 2150 | 92.13 | (is champion) | 104.07 |
| AIS | ssp585 | 2300 | 277.34 | (is champion) | 290.17 |
| glaciers | ssp126 | 2100 | 7.73 | (is champion) | 12.00 |
| glaciers | ssp126 | 2150 | 9.42 | (is champion) | 17.18 |
| glaciers | ssp126 | 2300 | 11.80 | (is champion) | 27.26 |
| glaciers | ssp245 | 2100 | 9.77 | (is champion) | 13.48 |
| glaciers | ssp245 | 2150 | 13.49 | (is champion) | 20.82 |
| glaciers | ssp245 | 2300 | 18.19 | (is champion) | 32.41 |
| glaciers | ssp585 | 2100 | 14.00 | (is champion) | 16.47 |
| glaciers | ssp585 | 2150 | 21.45 | (is champion) | 27.14 |
| glaciers | ssp585 | 2300 | 27.01 | (is champion) | 35.20 |
| Greenland | ssp126 | 2100 | 6.25 | (is champion) | 6.60 |
| Greenland | ssp126 | 2150 | 7.58 | (is champion) | 9.92 |
| Greenland | ssp126 | 2300 | 9.47 | (is champion) | 18.79 |
| Greenland | ssp245 | 2100 | 8.19 | (is champion) | 7.09 |
| Greenland | ssp245 | 2150 | 11.96 | (is champion) | 11.43 |
| Greenland | ssp245 | 2300 | 17.12 | (is champion) | 23.76 |
| Greenland | ssp585 | 2100 | 13.35 | (is champion) | 8.24 |
| Greenland | ssp585 | 2150 | 26.99 | (is champion) | 15.57 |
| Greenland | ssp585 | 2300 | 47.48 | (is champion) | 40.35 |
| thermal exp. | ssp126 | 2100 | 13.51 | (is champion) | 13.76 |
| thermal exp. | ssp126 | 2150 | 16.88 | (is champion) | 17.22 |
| thermal exp. | ssp126 | 2300 | 22.08 | (is champion) | 22.80 |
| thermal exp. | ssp245 | 2100 | 17.73 | (is champion) | 18.03 |
| thermal exp. | ssp245 | 2150 | 26.26 | (is champion) | 26.68 |
| thermal exp. | ssp245 | 2300 | 40.67 | (is champion) | 42.05 |
| thermal exp. | ssp585 | 2100 | 26.60 | (is champion) | 27.05 |
| thermal exp. | ssp585 | 2150 | 49.06 | (is champion) | 49.95 |
| thermal exp. | ssp585 | 2300 | 98.47 | (is champion) | 100.22 |
| land water | ssp126 | 2100 | 2.60 | (is champion) | 2.34 |
| land water | ssp126 | 2150 | 4.23 | (is champion) | 4.04 |
| land water | ssp126 | 2300 | 8.48 | (is champion) | 8.90 |
| land water | ssp245 | 2100 | 2.60 | (is champion) | 2.34 |
| land water | ssp245 | 2150 | 4.23 | (is champion) | 4.04 |
| land water | ssp245 | 2300 | 8.48 | (is champion) | 8.90 |
| land water | ssp585 | 2100 | 2.60 | (is champion) | 2.34 |
| land water | ssp585 | 2150 | 4.23 | (is champion) | 4.04 |
| land water | ssp585 | 2300 | 8.48 | (is champion) | 8.90 |
| TOTAL | ssp126 | 2100 | 34.33 | (is champion) | 39.24 |
| TOTAL | ssp126 | 2150 | 44.64 | (is champion) | 55.17 |
| TOTAL | ssp126 | 2300 | 64.44 | (is champion) | 91.18 |
| TOTAL | ssp245 | 2100 | 44.92 | (is champion) | 70.87 |
| TOTAL | ssp245 | 2150 | 71.57 | (is champion) | 137.98 |
| TOTAL | ssp245 | 2300 | 162.84 | (is champion) | 317.51 |
| TOTAL | ssp585 | 2100 | 92.45 | (is champion) | 104.68 |
| TOTAL | ssp585 | 2150 | 195.59 | (is champion) | 202.83 |
| TOTAL | ssp585 | 2300 | 461.72 | (is champion) | 482.40 |

## [S] Scenario separation — ssp585/ssp126 median ratio

| module | horizon | ours | verdict | literature |
|---|---|---|---|---|
| AIS | 2100 | 8.17x | **PASS** | FACTS 0.63-3.20 (n=5); MAGICC-SLR 10.69-10.69 (n=1) |
| AIS | 2150 | 14.12x | **PASS** | FACTS 0.48-7.55 (n=4); MAGICC-SLR 28.79-28.79 (n=1) |
| AIS | 2300 | 21.89x | **WARN** | MAGICC-SLR 81.77-81.77 (n=1)  [NO UPPER COMPARATOR AT THIS HORIZON] |
| glaciers | 2100 | 1.81x | **PASS** | FACTS 1.73-1.92 (n=2); MAGICC-SLR 1.46-1.46 (n=1) |
| glaciers | 2150 | 2.28x | **PASS** | FACTS 2.37-2.37 (n=1); MAGICC-SLR 1.79-1.79 (n=1) |
| glaciers | 2300 | 2.29x | **WARN** | MAGICC-SLR 2.11-2.11 (n=1)  [NO UPPER COMPARATOR AT THIS HORIZON] |
| Greenland | 2100 | 2.14x | **PASS** | FACTS 1.55-2.33 (n=3); MAGICC-SLR 2.11-2.11 (n=1) |
| Greenland | 2150 | 3.56x | **PASS(edge)** | FACTS 1.72-2.07 (n=2); MAGICC-SLR 3.48-3.48 (n=1); 0.08 outside the bracket = 5% of its own range |
| Greenland | 2300 | 5.02x | **WARN** | MAGICC-SLR 7.54-7.54 (n=1)  [NO UPPER COMPARATOR AT THIS HORIZON] |
| thermal exp. | 2100 | 1.97x | **PASS(edge)** | FACTS 2.05-2.05 (n=1); MAGICC-SLR 2.51-2.51 (n=1); 0.08 outside the bracket = 18% of its own range |
| thermal exp. | 2150 | 2.91x | **PASS(edge)** | FACTS 2.99-2.99 (n=1); MAGICC-SLR 3.94-3.94 (n=1); 0.08 outside the bracket = 9% of its own range |
| thermal exp. | 2300 | 4.46x | **WARN** | MAGICC-SLR 6.18-6.18 (n=1)  [NO UPPER COMPARATOR AT THIS HORIZON] |
| land water | 2100 | 1.00x | **PASS** | FACTS 0.99-0.99 (n=1); MAGICC-SLR 1.00-1.00 (n=1) |
| land water | 2150 | 1.00x | **PASS** | FACTS 1.03-1.03 (n=1); MAGICC-SLR 1.00-1.00 (n=1) |
| land water | 2300 | 1.00x | **PASS** | MAGICC-SLR 1.00-1.00 (n=1)  [NO UPPER COMPARATOR AT THIS HORIZON] |
| TOTAL | 2100 | 2.69x | **PASS** | FACTS 1.63-2.23 (n=7); MAGICC-SLR 2.75-2.75 (n=1) |
| TOTAL | 2150 | 4.38x | **PASS** | FACTS 1.94-4.15 (n=4); MAGICC-SLR 5.72-5.72 (n=1) |
| TOTAL | 2300 | 7.17x | **WARN** | MAGICC-SLR 15.28-15.28 (n=1)  [NO UPPER COMPARATOR AT THIS HORIZON] |

---

*Machine-readable: `outputs/bench_ladrillo_L14.csv`. Regenerate: `python python/bench_ladrillo.py --tag=L14`.*
