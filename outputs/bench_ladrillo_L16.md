# Ladrillo benchmark — `L16`

*benchmark v1.0, 2026-08-26, repo `085a725`. Champion arm: **L14**.*

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
| **AIS** | PASS | UNRESOLVED | FAIL | WARN | WORSE |
| **glaciers** | WARN | UNRESOLVED | WARN | WARN | WORSE |
| **Greenland** | PASS | UNRESOLVED | FAIL | WARN | SAME |
| **thermal exp.** | WARN | FAIL | WARN | WARN | SAME |
| **land water** | — | — | WARN | PASS | — |
| **TOTAL** | PASS | UNRESOLVED | WARN | WARN | BETTER |

## [H] Hindcast — the full observational period, scaled to each component's own target 1-sigma

| module | target 1σ (cm) | window | arm | RMSE (cm) | RMSE (σ) | note |
|---|---|---|---|---|---|---|
| AIS | 0.1674 | full | L16 | 0.0321 | 0.19 | bias -0.0068 cm = -0.04 sd; cov90 84%; n=106 |
| AIS | 0.1674 | full | L14* | 0.0308 | 0.18 | bias -0.0012 cm = -0.01 sd; cov90 83%; n=106 |
| AIS | 0.1674 | full | BRICK 2.0 | 1.1758 | 7.02 | bias -0.8211 cm = -4.90 sd; cov90 31%; n=106 |
| AIS | 0.1674 | 1920-1949 | L16 | 0.0097 | 0.06 | bias -0.0094 cm = -0.06 sd; cov90 100%; n=30 |
| AIS | 0.1674 | 1920-1949 | L14* | 0.0058 | 0.03 | bias -0.0045 cm = -0.03 sd; cov90 100%; n=30 |
| AIS | 0.1674 | 1920-1949 | BRICK 2.0 | 1.9843 | 11.85 | bias -1.9579 cm = -11.69 sd; cov90 0%; n=30 |
| AIS | 0.1674 | 1950-1992 | L16 | 0.0091 | 0.05 | bias -0.0037 cm = -0.02 sd; cov90 98%; n=43 |
| AIS | 0.1674 | 1950-1992 | L14* | 0.0067 | 0.04 | bias +0.0039 cm = +0.02 sd; cov90 98%; n=43 |
| AIS | 0.1674 | 1950-1992 | BRICK 2.0 | 0.8082 | 4.83 | bias -0.7053 cm = -4.21 sd; cov90 2%; n=43 |
| AIS | 0.1674 | 1993-2026 | L16 | 0.0558 | 0.33 | bias -0.0084 cm = -0.05 sd; cov90 52%; n=33 |
| AIS | 0.1674 | 1993-2026 | L14* | 0.0544 | 0.32 | bias -0.0047 cm = -0.03 sd; cov90 48%; n=33 |
| AIS | 0.1674 | 1993-2026 | BRICK 2.0 | 0.0992 | 0.59 | bias +0.0615 cm = +0.37 sd; cov90 97%; n=33 |
| glaciers | 0.4593 | full | L16 | 0.3288 | 0.72 | bias +0.1656 cm = +0.36 sd; cov90 53%; n=104 |
| glaciers | 0.4593 | full | L14* | 0.3308 | 0.72 | bias +0.1671 cm = +0.36 sd; cov90 54%; n=104 |
| glaciers | 0.4593 | full | BRICK 2.0 | 0.8941 | 1.95 | bias +0.5000 cm = +1.09 sd; cov90 47%; n=104 |
| glaciers | 0.4593 | 1920-1949 | L16 | 0.5834 | 1.27 | bias +0.5207 cm = +1.13 sd; cov90 23%; n=30 |
| glaciers | 0.4593 | 1920-1949 | L14* | 0.5888 | 1.28 | bias +0.5246 cm = +1.14 sd; cov90 23%; n=30 |
| glaciers | 0.4593 | 1920-1949 | BRICK 2.0 | 1.6382 | 3.57 | bias +1.5142 cm = +3.30 sd; cov90 0%; n=30 |
| glaciers | 0.4593 | 1950-1992 | L16 | 0.1346 | 0.29 | bias +0.0760 cm = +0.17 sd; cov90 56%; n=43 |
| glaciers | 0.4593 | 1950-1992 | L14* | 0.1326 | 0.29 | bias +0.0743 cm = +0.16 sd; cov90 56%; n=43 |
| glaciers | 0.4593 | 1950-1992 | BRICK 2.0 | 0.1311 | 0.29 | bias +0.0341 cm = +0.07 sd; cov90 95%; n=43 |
| glaciers | 0.4593 | 1993-2026 | L16 | 0.0898 | 0.20 | bias -0.0540 cm = -0.12 sd; cov90 77%; n=31 |
| glaciers | 0.4593 | 1993-2026 | L14* | 0.0848 | 0.18 | bias -0.0502 cm = -0.11 sd; cov90 81%; n=31 |
| glaciers | 0.4593 | 1993-2026 | BRICK 2.0 | 0.2460 | 0.54 | bias +0.1647 cm = +0.36 sd; cov90 26%; n=31 |
| Greenland | 0.1832 | full | L16 | 0.0588 | 0.32 | bias +0.0015 cm = +0.01 sd; cov90 53%; n=106 |
| Greenland | 0.1832 | full | L14* | 0.0590 | 0.32 | bias +0.0020 cm = +0.01 sd; cov90 57%; n=106 |
| Greenland | 0.1832 | full | BRICK 2.0 | 0.7230 | 3.95 | bias -0.5975 cm = -3.26 sd; cov90 22%; n=106 |
| Greenland | 0.1832 | 1920-1949 | L16 | 0.0803 | 0.44 | bias +0.0241 cm = +0.13 sd; cov90 53%; n=30 |
| Greenland | 0.1832 | 1920-1949 | L14* | 0.0805 | 0.44 | bias +0.0266 cm = +0.15 sd; cov90 60%; n=30 |
| Greenland | 0.1832 | 1920-1949 | BRICK 2.0 | 0.7876 | 4.30 | bias -0.7371 cm = -4.02 sd; cov90 27%; n=30 |
| Greenland | 0.1832 | 1950-1992 | L16 | 0.0491 | 0.27 | bias -0.0146 cm = -0.08 sd; cov90 58%; n=43 |
| Greenland | 0.1832 | 1950-1992 | L14* | 0.0494 | 0.27 | bias -0.0149 cm = -0.08 sd; cov90 60%; n=43 |
| Greenland | 0.1832 | 1950-1992 | BRICK 2.0 | 0.9132 | 4.99 | bias -0.8659 cm = -4.73 sd; cov90 0%; n=43 |
| Greenland | 0.1832 | 1993-2026 | L16 | 0.0456 | 0.25 | bias +0.0018 cm = +0.01 sd; cov90 45%; n=33 |
| Greenland | 0.1832 | 1993-2026 | L14* | 0.0458 | 0.25 | bias +0.0017 cm = +0.01 sd; cov90 48%; n=33 |
| Greenland | 0.1832 | 1993-2026 | BRICK 2.0 | 0.1686 | 0.92 | bias -0.1209 cm = -0.66 sd; cov90 45%; n=33 |
| thermal exp. | 0.3091 | full | L16 | 0.3195 | 1.03 | bias +0.1794 cm = +0.58 sd; cov90 27%; n=106 |
| thermal exp. | 0.3091 | full | L14* | 0.3202 | 1.04 | bias +0.1808 cm = +0.59 sd; cov90 28%; n=106 |
| thermal exp. | 0.3091 | full | BRICK 2.0 | 0.3243 | 1.05 | bias +0.1908 cm = +0.62 sd; cov90 96%; n=106 |
| thermal exp. | 0.3091 | 1920-1949 | L16 | 0.4444 | 1.44 | bias +0.3540 cm = +1.15 sd; cov90 30%; n=30 |
| thermal exp. | 0.3091 | 1920-1949 | L14* | 0.4475 | 1.45 | bias +0.3576 cm = +1.16 sd; cov90 30%; n=30 |
| thermal exp. | 0.3091 | 1920-1949 | BRICK 2.0 | 0.4741 | 1.53 | bias +0.3885 cm = +1.26 sd; cov90 100%; n=30 |
| thermal exp. | 0.3091 | 1950-1992 | L16 | 0.1842 | 0.60 | bias +0.0313 cm = +0.10 sd; cov90 37%; n=43 |
| thermal exp. | 0.3091 | 1950-1992 | L14* | 0.1847 | 0.60 | bias +0.0333 cm = +0.11 sd; cov90 37%; n=43 |
| thermal exp. | 0.3091 | 1950-1992 | BRICK 2.0 | 0.1897 | 0.61 | bias +0.0499 cm = +0.16 sd; cov90 100%; n=43 |
| thermal exp. | 0.3091 | 1993-2026 | L16 | 0.3228 | 1.04 | bias +0.2138 cm = +0.69 sd; cov90 12%; n=33 |
| thermal exp. | 0.3091 | 1993-2026 | L14* | 0.3207 | 1.04 | bias +0.2123 cm = +0.69 sd; cov90 15%; n=33 |
| thermal exp. | 0.3091 | 1993-2026 | BRICK 2.0 | 0.2941 | 0.95 | bias +0.1946 cm = +0.63 sd; cov90 88%; n=33 |
| TOTAL | 1.5380 | full | L16 | 0.6796 | 0.44 | bias +0.5488 cm = +0.36 sd; cov90 25%; n=105 |
| TOTAL | 1.5380 | full | L14* | 0.6923 | 0.45 | bias +0.5606 cm = +0.36 sd; cov90 26%; n=105 |
| TOTAL | 1.5380 | full | BRICK 2.0 | 1.8198 | 1.18 | bias -1.3318 cm = -0.87 sd; cov90 25%; n=105 |
| TOTAL | 1.5380 | 1920-1949 | L16 | 0.9619 | 0.63 | bias +0.9177 cm = +0.60 sd; cov90 37%; n=30 |
| TOTAL | 1.5380 | 1920-1949 | L14* | 0.9777 | 0.64 | bias +0.9346 cm = +0.61 sd; cov90 40%; n=30 |
| TOTAL | 1.5380 | 1920-1949 | BRICK 2.0 | 2.5470 | 1.66 | bias -2.4846 cm = -1.62 sd; cov90 0%; n=30 |
| TOTAL | 1.5380 | 1950-1992 | L16 | 0.6473 | 0.42 | bias +0.6043 cm = +0.39 sd; cov90 5%; n=43 |
| TOTAL | 1.5380 | 1950-1992 | L14* | 0.6590 | 0.43 | bias +0.6151 cm = +0.40 sd; cov90 5%; n=43 |
| TOTAL | 1.5380 | 1950-1992 | BRICK 2.0 | 1.8672 | 1.21 | bias -1.5605 cm = -1.01 sd; cov90 12%; n=43 |
| TOTAL | 1.5380 | 1993-2026 | L16 | 0.2918 | 0.19 | bias +0.1285 cm = +0.08 sd; cov90 41%; n=32 |
| TOTAL | 1.5380 | 1993-2026 | L14* | 0.3053 | 0.20 | bias +0.1368 cm = +0.09 sd; cov90 41%; n=32 |
| TOTAL | 1.5380 | 1993-2026 | BRICK 2.0 | 0.3164 | 0.21 | bias +0.0564 cm = +0.04 sd; cov90 66%; n=32 |

## [R] Rate (1993-2026) and acceleration (1900-2026), with an error bar on the observations

| module | statistic | arm | value | unit | z vs obs bar | note |
|---|---|---|---|---|---|---|
| AIS | rate | observations | 0.032608 | cm/yr | — | se: estimator 0.003405, band-correlated 0.0005689, band-independent 0.003061; CONSERVATIVE 0.003405 cm/yr; |obs|/se = 9.58 |
| AIS | rate | L16 | 0.031499 | cm/yr | -0.33 | 0.97x obs; z=-0.33 vs the obs error bar |
| AIS | rate | L14* | 0.031707 | cm/yr | -0.26 | 0.97x obs; z=-0.26 vs the obs error bar |
| AIS | rate | BRICK 2.0 | 0.039301 | cm/yr | +1.97 | 1.21x obs; z=+1.97 vs the obs error bar |
| glaciers | rate | observations | 0.068013 | cm/yr | — | se: estimator 0.0005236, band-correlated 0.0001274, band-independent 0.009223; CONSERVATIVE 0.009223 cm/yr; |obs|/se = 7.37 |
| glaciers | rate | L16 | 0.062574 | cm/yr | -0.59 | 0.92x obs; z=-0.59 vs the obs error bar |
| glaciers | rate | L14* | 0.063042 | cm/yr | -0.54 | 0.93x obs; z=-0.54 vs the obs error bar |
| glaciers | rate | BRICK 2.0 | 0.090078 | cm/yr | +2.39 | 1.32x obs; z=+2.39 vs the obs error bar |
| Greenland | rate | observations | 0.06596 | cm/yr | — | se: estimator 0.01044, band-correlated 0.0006502, band-independent 0.003349; CONSERVATIVE 0.01044 cm/yr; |obs|/se = 6.32 |
| Greenland | rate | L16 | 0.065776 | cm/yr | -0.02 | 1.00x obs; z=-0.02 vs the obs error bar |
| Greenland | rate | L14* | 0.065777 | cm/yr | -0.02 | 1.00x obs; z=-0.02 vs the obs error bar |
| Greenland | rate | BRICK 2.0 | 0.058529 | cm/yr | -0.71 | 0.89x obs; z=-0.71 vs the obs error bar |
| thermal exp. | rate | observations | 0.1234 | cm/yr | — | se: estimator 0.003756, band-correlated 0.002392, band-independent 0.005651; CONSERVATIVE 0.005651 cm/yr; |obs|/se = 21.84 |
| thermal exp. | rate | L16 | 0.14725 | cm/yr | +4.22 | 1.19x obs; z=+4.22 vs the obs error bar |
| thermal exp. | rate | L14* | 0.14708 | cm/yr | +4.19 | 1.19x obs; z=+4.19 vs the obs error bar |
| thermal exp. | rate | BRICK 2.0 | 0.14454 | cm/yr | +3.74 | 1.17x obs; z=+3.74 vs the obs error bar |
| TOTAL | rate | observations | 0.32469 | cm/yr | — | se: estimator 0.02949, band-correlated 0.02545, band-independent 0.02945; CONSERVATIVE 0.02949 cm/yr; |obs|/se = 11.01 |
| TOTAL | rate | L16 | 0.33743 | cm/yr | +0.43 | 1.04x obs; z=+0.43 vs the obs error bar |
| TOTAL | rate | L14* | 0.3373 | cm/yr | +0.43 | 1.04x obs; z=+0.43 vs the obs error bar |
| TOTAL | rate | BRICK 2.0 | 0.33831 | cm/yr | +0.46 | 1.04x obs; z=+0.46 vs the obs error bar |
| AIS | accel | observations | 0.00020499 | cm/yr2 | — | se: estimator 0.0001336, band-correlated 3.924e-05, band-independent 2.522e-05; CONSERVATIVE 0.0001336 cm/yr2; |obs|/se = 1.53 |
| AIS | accel | L16 | 0.00021546 | cm/yr2 | +0.08 | ratio NOT INTERPRETABLE (obs is 1.53 se from zero); z=+0.08 vs the obs error bar |
| AIS | accel | L14* | 0.00020186 | cm/yr2 | -0.02 | ratio NOT INTERPRETABLE (obs is 1.53 se from zero); z=-0.02 vs the obs error bar |
| AIS | accel | BRICK 2.0 | -9.5414e-05 | cm/yr2 | -2.25 | ratio NOT INTERPRETABLE (obs is 1.53 se from zero); z=-2.25 vs the obs error bar |
| glaciers | accel | observations | -0.00054814 | cm/yr2 | — | se: estimator 0.000447, band-correlated 3.442e-05, band-independent 7.199e-05; CONSERVATIVE 0.000447 cm/yr2; |obs|/se = 1.23 |
| glaciers | accel | L16 | -0.00011027 | cm/yr2 | +0.98 | ratio NOT INTERPRETABLE (obs is 1.23 se from zero); z=+0.98 vs the obs error bar |
| glaciers | accel | L14* | -9.9967e-05 | cm/yr2 | +1.00 | ratio NOT INTERPRETABLE (obs is 1.23 se from zero); z=+1.00 vs the obs error bar |
| glaciers | accel | BRICK 2.0 | 0.00082242 | cm/yr2 | +3.07 | ratio NOT INTERPRETABLE (obs is 1.23 se from zero); z=+3.07 vs the obs error bar |
| Greenland | accel | observations | -0.00027825 | cm/yr2 | — | se: estimator 0.0005241, band-correlated 6.83e-05, band-independent 2.759e-05; CONSERVATIVE 0.0005241 cm/yr2; |obs|/se = 0.53 |
| Greenland | accel | L16 | -0.00025087 | cm/yr2 | +0.05 | ratio NOT INTERPRETABLE (obs is 0.53 se from zero); z=+0.05 vs the obs error bar |
| Greenland | accel | L14* | -0.00025027 | cm/yr2 | +0.05 | ratio NOT INTERPRETABLE (obs is 0.53 se from zero); z=+0.05 vs the obs error bar |
| Greenland | accel | BRICK 2.0 | 0.00014987 | cm/yr2 | +0.82 | ratio NOT INTERPRETABLE (obs is 0.53 se from zero); z=+0.82 vs the obs error bar |
| thermal exp. | accel | observations | 0.0008428 | cm/yr2 | — | se: estimator 0.0002431, band-correlated 2.312e-05, band-independent 4.655e-05; CONSERVATIVE 0.0002431 cm/yr2; |obs|/se = 3.47 |
| thermal exp. | accel | L16 | 0.001001 | cm/yr2 | +0.65 | 1.19x obs; z=+0.65 vs the obs error bar |
| thermal exp. | accel | L14* | 0.00099983 | cm/yr2 | +0.65 | 1.19x obs; z=+0.65 vs the obs error bar |
| thermal exp. | accel | BRICK 2.0 | 0.0013015 | cm/yr2 | +1.89 | 1.54x obs; z=+1.89 vs the obs error bar |
| TOTAL | accel | observations | 0.00089376 | cm/yr2 | — | se: estimator 0.001159, band-correlated 0.0001276, band-independent 0.0002363; CONSERVATIVE 0.001159 cm/yr2; |obs|/se = 0.77 |
| TOTAL | accel | L16 | 0.0010343 | cm/yr2 | +0.12 | ratio NOT INTERPRETABLE (obs is 0.77 se from zero); z=+0.12 vs the obs error bar |
| TOTAL | accel | L14* | 0.0010226 | cm/yr2 | +0.11 | ratio NOT INTERPRETABLE (obs is 0.77 se from zero); z=+0.11 vs the obs error bar |
| TOTAL | accel | BRICK 2.0 | 0.0022411 | cm/yr2 | +1.16 | ratio NOT INTERPRETABLE (obs is 0.77 se from zero); z=+1.16 vs the obs error bar |

## [P] Projections vs the literature — scored on the JOINT band

| module | ssp | horizon | metric | value | verdict | note |
|---|---|---|---|---|---|---|
| AIS | ssp126 | 2100 | median_vs_lit | 0.535 x lit median | **PASS** | ours 4.79 cm vs lit 3.66-11.90 (median 8.94), n_lit=5 [1 SEJ comparator(s) excluded from the score; full range 3.66-11.90] |
| AIS | ssp126 | 2100 | median_vs_lit | 0.471 x lit median | **PASS** | BRICK 2.0 4.21 cm vs the same lit median 8.94; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp126 | 2100 | spread_vs_lit | 2.392 x lit spread | **FAIL** | ours 50.49 cm vs model-based lit 9.86-39.27 (median 21.11, n=5); ALL comparators 9.86-91.07 |
| AIS | ssp126 | 2150 | median_vs_lit | 0.409 x lit median | **PASS** | ours 7.33 cm vs lit 5.34-26.34 (median 17.92), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 5.34-26.34] |
| AIS | ssp126 | 2150 | median_vs_lit | 0.355 x lit median | **PASS** | BRICK 2.0 6.37 cm vs the same lit median 17.92; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp126 | 2150 | spread_vs_lit | 2.056 x lit spread | **WARN** | ours 94.86 cm vs model-based lit 33.17-72.55 (median 46.14, n=4); ALL comparators 33.17-156.27; ⚠ THE COMPARATORS DO NOT AGREE -- scored one at a time they give 2xhigh/2xin and the median's 'high' is not a majority, so the median is not a summary here; verdict CAPPED at WARN |
| AIS | ssp126 | 2300 | median_vs_lit | 1.637 x lit median | **WARN** | ours 14.26 cm vs lit 8.71-8.71 (median 8.71), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| AIS | ssp126 | 2300 | median_vs_lit | 1.452 x lit median | **WARN** | BRICK 2.0 12.64 cm vs the same lit median 8.71; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp126 | 2300 | spread_vs_lit | 3.231 x lit spread | **WARN** | ours 224.86 cm vs model-based lit 69.60-69.60 (median 69.60, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |
| AIS | ssp245 | 2100 | median_vs_lit | 0.865 x lit median | **PASS** | ours 8.98 cm vs lit 5.54-12.73 (median 10.38), n_lit=5 [1 SEJ comparator(s) excluded from the score; full range 5.54-13.71] |
| AIS | ssp245 | 2100 | median_vs_lit | 2.814 x lit median | **FAIL** | BRICK 2.0 29.21 cm vs the same lit median 10.38; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp245 | 2100 | spread_vs_lit | 1.721 x lit spread | **PASS** | ours 61.62 cm vs model-based lit 20.88-44.94 (median 35.81, n=5); ALL comparators 20.88-109.87 |
| AIS | ssp245 | 2150 | median_vs_lit | 1.710 x lit median | **WARN** | ours 46.94 cm vs lit 10.91-30.28 (median 27.45), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 10.91-30.28] |
| AIS | ssp245 | 2150 | median_vs_lit | 2.715 x lit median | **FAIL** | BRICK 2.0 74.53 cm vs the same lit median 27.45; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp245 | 2150 | spread_vs_lit | 1.531 x lit spread | **WARN** | ours 128.75 cm vs model-based lit 44.92-369.45 (median 84.10, n=4); ALL comparators 44.92-369.45; ⚠ THE COMPARATORS DO NOT AGREE -- scored one at a time they give 1xhigh/2xin/1xlow and the median's 'in' is not a majority, so the median is not a summary here; verdict CAPPED at WARN |
| AIS | ssp245 | 2300 | median_vs_lit | 1.974 x lit median | **WARN** | ours 164.73 cm vs lit 83.46-83.46 (median 83.46), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| AIS | ssp245 | 2300 | median_vs_lit | 2.491 x lit median | **WARN** | BRICK 2.0 207.88 cm vs the same lit median 83.46; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp245 | 2300 | spread_vs_lit | 1.255 x lit spread | **PASS** | ours 340.72 cm vs model-based lit 271.56-271.56 (median 271.56, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| AIS | ssp585 | 2100 | median_vs_lit | 3.009 x lit median | **FAIL** | ours 43.40 cm vs lit 3.98-39.10 (median 14.43), n_lit=5 [1 SEJ comparator(s) excluded from the score; full range 3.98-39.10] |
| AIS | ssp585 | 2100 | median_vs_lit | 3.395 x lit median | **FAIL** | BRICK 2.0 48.98 cm vs the same lit median 14.43; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp585 | 2100 | spread_vs_lit | 1.309 x lit spread | **PASS** | ours 73.94 cm vs model-based lit 20.51-79.00 (median 56.48, n=5); ALL comparators 20.51-151.54; width here is the antarctic_lambda PRIOR -- do NOT narrow |
| AIS | ssp585 | 2150 | median_vs_lit | 1.084 x lit median | **PASS** | ours 103.56 cm vs lit 6.26-198.76 (median 95.53), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 6.26-198.76] |
| AIS | ssp585 | 2150 | median_vs_lit | 1.089 x lit median | **PASS** | BRICK 2.0 104.07 cm vs the same lit median 95.53; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp585 | 2150 | spread_vs_lit | 0.602 x lit spread | **WARN** | ours 123.51 cm vs model-based lit 48.68-408.37 (median 205.25, n=4); ALL comparators 48.68-570.98; ⚠ THE COMPARATORS DO NOT AGREE -- scored one at a time they give 1xhigh/1xin/2xlow and the median's 'in' is not a majority, so the median is not a summary here; verdict CAPPED at WARN; width here is the antarctic_lambda PRIOR -- do NOT narrow |
| AIS | ssp585 | 2300 | median_vs_lit | 1.126 x lit median | **PASS** | ours 307.51 cm vs lit 267.00-712.02 (median 273.00), n_lit=3 |
| AIS | ssp585 | 2300 | median_vs_lit | 1.063 x lit median | **PASS** | BRICK 2.0 290.17 cm vs the same lit median 273.00; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp585 | 2300 | spread_vs_lit | 0.393 x lit spread | **WARN** | ours 371.22 cm vs model-based lit 944.94-944.94 (median 944.94, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; width here is the antarctic_lambda PRIOR -- do NOT narrow |
| glaciers | ssp126 | 2100 | median_vs_lit | 0.828 x lit median | **WARN** | ours 7.66 cm vs lit 8.95-10.45 (median 9.25), n_lit=3 |
| glaciers | ssp126 | 2100 | median_vs_lit | 1.297 x lit median | **WARN** | BRICK 2.0 12.00 cm vs the same lit median 9.25; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp126 | 2100 | spread_vs_lit | 0.791 x lit spread | **PASS** | ours 5.82 cm vs model-based lit 7.12-7.85 (median 7.36, n=3) |
| glaciers | ssp126 | 2150 | median_vs_lit | 0.772 x lit median | **WARN** | ours 9.37 cm vs lit 12.00-12.28 (median 12.14), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp126 | 2150 | median_vs_lit | 1.415 x lit median | **WARN** | BRICK 2.0 17.18 cm vs the same lit median 12.14; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp126 | 2150 | spread_vs_lit | 0.748 x lit spread | **PASS** | ours 7.64 cm vs model-based lit 8.52-11.89 (median 10.21, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| glaciers | ssp126 | 2300 | median_vs_lit | 0.852 x lit median | **WARN** | ours 11.75 cm vs lit 13.80-13.80 (median 13.80), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp126 | 2300 | median_vs_lit | 1.975 x lit median | **WARN** | BRICK 2.0 27.26 cm vs the same lit median 13.80; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp126 | 2300 | spread_vs_lit | 0.954 x lit spread | **PASS** | ours 10.71 cm vs model-based lit 11.23-11.23 (median 11.23, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| glaciers | ssp245 | 2100 | median_vs_lit | 0.791 x lit median | **WARN** | ours 9.66 cm vs lit 11.38-12.54 (median 12.21), n_lit=3 |
| glaciers | ssp245 | 2100 | median_vs_lit | 1.104 x lit median | **WARN** | BRICK 2.0 13.48 cm vs the same lit median 12.21; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp245 | 2100 | spread_vs_lit | 0.855 x lit spread | **PASS** | ours 6.56 cm vs model-based lit 7.42-9.60 (median 7.68, n=3) |
| glaciers | ssp245 | 2150 | median_vs_lit | 0.787 x lit median | **WARN** | ours 13.47 cm vs lit 16.71-17.53 (median 17.12), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp245 | 2150 | median_vs_lit | 1.216 x lit median | **WARN** | BRICK 2.0 20.82 cm vs the same lit median 17.12; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp245 | 2150 | spread_vs_lit | 0.732 x lit spread | **PASS** | ours 9.45 cm vs model-based lit 9.16-16.65 (median 12.91, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| glaciers | ssp245 | 2300 | median_vs_lit | 0.853 x lit median | **WARN** | ours 18.30 cm vs lit 21.47-21.47 (median 21.47), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp245 | 2300 | median_vs_lit | 1.510 x lit median | **WARN** | BRICK 2.0 32.41 cm vs the same lit median 21.47; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp245 | 2300 | spread_vs_lit | 1.153 x lit spread | **PASS** | ours 12.62 cm vs model-based lit 10.95-10.95 (median 10.95, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| glaciers | ssp585 | 2100 | median_vs_lit | 0.898 x lit median | **WARN** | ours 13.88 cm vs lit 15.30-17.73 (median 15.46), n_lit=3 |
| glaciers | ssp585 | 2100 | median_vs_lit | 1.065 x lit median | **PASS** | BRICK 2.0 16.47 cm vs the same lit median 15.46; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp585 | 2100 | spread_vs_lit | 0.918 x lit spread | **PASS** | ours 8.64 cm vs model-based lit 8.51-13.85 (median 9.41, n=3) |
| glaciers | ssp585 | 2150 | median_vs_lit | 0.850 x lit median | **WARN** | ours 21.45 cm vs lit 22.03-28.40 (median 25.22), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp585 | 2150 | median_vs_lit | 1.076 x lit median | **PASS** | BRICK 2.0 27.14 cm vs the same lit median 25.22; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp585 | 2150 | spread_vs_lit | 0.898 x lit spread | **PASS** | ours 11.50 cm vs model-based lit 10.09-15.53 (median 12.81, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| glaciers | ssp585 | 2300 | median_vs_lit | 0.929 x lit median | **WARN** | ours 27.04 cm vs lit 29.10-29.10 (median 29.10), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp585 | 2300 | median_vs_lit | 1.210 x lit median | **WARN** | BRICK 2.0 35.20 cm vs the same lit median 29.10; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp585 | 2300 | spread_vs_lit | 1.230 x lit spread | **PASS** | ours 12.10 cm vs model-based lit 9.83-9.83 (median 9.83, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| Greenland | ssp126 | 2100 | median_vs_lit | 0.977 x lit median | **PASS** | ours 6.25 cm vs lit 5.46-7.67 (median 6.40), n_lit=3 [1 SEJ comparator(s) excluded from the score; full range 5.46-13.05] |
| Greenland | ssp126 | 2100 | median_vs_lit | 1.030 x lit median | **PASS** | BRICK 2.0 6.60 cm vs the same lit median 6.40; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp126 | 2100 | spread_vs_lit | 0.494 x lit spread | **FAIL** | ours 4.73 cm vs model-based lit 7.06-17.14 (median 9.57, n=3); ALL comparators 7.06-55.71 |
| Greenland | ssp126 | 2150 | median_vs_lit | 0.668 x lit median | **WARN** | ours 7.51 cm vs lit 9.31-13.18 (median 11.25), n_lit=2 [1 SEJ comparator(s) excluded from the score; full range 9.31-22.20] ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp126 | 2150 | median_vs_lit | 0.882 x lit median | **PASS** | BRICK 2.0 9.92 cm vs the same lit median 11.25; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp126 | 2150 | spread_vs_lit | 0.511 x lit spread | **PASS** | ours 6.85 cm vs model-based lit 11.12-15.69 (median 13.40, n=2); ALL comparators 11.12-86.94; ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| Greenland | ssp126 | 2300 | median_vs_lit | 0.620 x lit median | **WARN** | ours 9.29 cm vs lit 14.98-14.98 (median 14.98), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp126 | 2300 | median_vs_lit | 1.255 x lit median | **WARN** | BRICK 2.0 18.79 cm vs the same lit median 14.98; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp126 | 2300 | spread_vs_lit | 0.383 x lit spread | **WARN** | ours 11.27 cm vs model-based lit 29.41-29.41 (median 29.41, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |
| Greenland | ssp245 | 2100 | median_vs_lit | 0.886 x lit median | **PASS** | ours 8.23 cm vs lit 7.97-10.21 (median 9.28), n_lit=3 [1 SEJ comparator(s) excluded from the score; full range 7.97-14.39] |
| Greenland | ssp245 | 2100 | median_vs_lit | 0.763 x lit median | **WARN** | BRICK 2.0 7.09 cm vs the same lit median 9.28; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp245 | 2100 | spread_vs_lit | 0.694 x lit spread | **PASS** | ours 5.79 cm vs model-based lit 7.85-16.85 (median 8.35, n=3); ALL comparators 7.85-72.68 |
| Greenland | ssp245 | 2150 | median_vs_lit | 0.686 x lit median | **WARN** | ours 11.91 cm vs lit 16.53-18.19 (median 17.36), n_lit=2 [1 SEJ comparator(s) excluded from the score; full range 16.53-25.62] ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp245 | 2150 | median_vs_lit | 0.658 x lit median | **WARN** | BRICK 2.0 11.43 cm vs the same lit median 17.36; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp245 | 2150 | spread_vs_lit | 0.745 x lit spread | **PASS** | ours 11.11 cm vs model-based lit 14.88-14.93 (median 14.91, n=2); ALL comparators 14.88-88.90; ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| Greenland | ssp245 | 2300 | median_vs_lit | 0.474 x lit median | **WARN** | ours 16.96 cm vs lit 35.79-35.79 (median 35.79), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp245 | 2300 | median_vs_lit | 0.664 x lit median | **WARN** | BRICK 2.0 23.76 cm vs the same lit median 35.79; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp245 | 2300 | spread_vs_lit | 0.492 x lit spread | **WARN** | ours 20.12 cm vs model-based lit 40.91-40.91 (median 40.91, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |
| Greenland | ssp585 | 2100 | median_vs_lit | 0.993 x lit median | **PASS** | ours 13.40 cm vs lit 12.72-14.02 (median 13.49), n_lit=3 [1 SEJ comparator(s) excluded from the score; full range 12.72-20.28] |
| Greenland | ssp585 | 2100 | median_vs_lit | 0.611 x lit median | **WARN** | BRICK 2.0 8.24 cm vs the same lit median 13.49; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp585 | 2100 | spread_vs_lit | 0.936 x lit spread | **PASS** | ours 11.38 cm vs model-based lit 11.46-17.10 (median 12.15, n=3); ALL comparators 11.46-93.18 |
| Greenland | ssp585 | 2150 | median_vs_lit | 0.907 x lit median | **WARN** | ours 27.09 cm vs lit 27.33-32.40 (median 29.87), n_lit=2 [1 SEJ comparator(s) excluded from the score; full range 27.33-38.13] ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp585 | 2150 | median_vs_lit | 0.521 x lit median | **WARN** | BRICK 2.0 15.57 cm vs the same lit median 29.87; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp585 | 2150 | spread_vs_lit | 0.464 x lit spread | **WARN** | ours 26.91 cm vs model-based lit 24.97-90.97 (median 57.97, n=2); ALL comparators 24.97-121.86; ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |
| Greenland | ssp585 | 2300 | median_vs_lit | 0.419 x lit median | **WARN** | ours 47.32 cm vs lit 113.01-113.01 (median 113.01), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp585 | 2300 | median_vs_lit | 0.357 x lit median | **WARN** | BRICK 2.0 40.35 cm vs the same lit median 113.01; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp585 | 2300 | spread_vs_lit | 0.085 x lit spread | **WARN** | ours 57.62 cm vs model-based lit 680.24-680.24 (median 680.24, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |
| thermal exp. | ssp126 | 2100 | median_vs_lit | 1.074 x lit median | **PASS** | ours 13.50 cm vs lit 11.09-14.05 (median 12.57), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp126 | 2100 | median_vs_lit | 1.095 x lit median | **PASS** | BRICK 2.0 13.76 cm vs the same lit median 12.57; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp126 | 2100 | spread_vs_lit | 0.874 x lit spread | **PASS** | ours 10.15 cm vs model-based lit 11.26-11.97 (median 11.61, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp126 | 2150 | median_vs_lit | 1.105 x lit median | **PASS** | ours 16.87 cm vs lit 12.68-17.85 (median 15.26), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp126 | 2150 | median_vs_lit | 1.128 x lit median | **PASS** | BRICK 2.0 17.22 cm vs the same lit median 15.26; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp126 | 2150 | spread_vs_lit | 0.916 x lit spread | **PASS** | ours 15.12 cm vs model-based lit 16.06-16.96 (median 16.51, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp126 | 2300 | median_vs_lit | 1.324 x lit median | **WARN** | ours 22.15 cm vs lit 16.74-16.74 (median 16.74), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| thermal exp. | ssp126 | 2300 | median_vs_lit | 1.362 x lit median | **WARN** | BRICK 2.0 22.80 cm vs the same lit median 16.74; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp126 | 2300 | spread_vs_lit | 1.068 x lit spread | **PASS** | ours 27.20 cm vs model-based lit 25.47-25.47 (median 25.47, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp245 | 2100 | median_vs_lit | 1.003 x lit median | **PASS** | ours 17.78 cm vs lit 16.62-18.84 (median 17.73), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp245 | 2100 | median_vs_lit | 1.017 x lit median | **PASS** | BRICK 2.0 18.03 cm vs the same lit median 17.73; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp245 | 2100 | spread_vs_lit | 0.813 x lit spread | **PASS** | ours 11.78 cm vs model-based lit 13.73-15.26 (median 14.49, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp245 | 2150 | median_vs_lit | 1.011 x lit median | **PASS** | ours 26.23 cm vs lit 23.23-28.64 (median 25.94), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp245 | 2150 | median_vs_lit | 1.029 x lit median | **PASS** | BRICK 2.0 26.68 cm vs the same lit median 25.94; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp245 | 2150 | spread_vs_lit | 0.816 x lit spread | **PASS** | ours 20.32 cm vs model-based lit 23.92-25.87 (median 24.90, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp245 | 2300 | median_vs_lit | 1.134 x lit median | **WARN** | ours 41.15 cm vs lit 36.30-36.30 (median 36.30), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| thermal exp. | ssp245 | 2300 | median_vs_lit | 1.159 x lit median | **WARN** | BRICK 2.0 42.05 cm vs the same lit median 36.30; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp245 | 2300 | spread_vs_lit | 0.796 x lit spread | **PASS** | ours 43.17 cm vs model-based lit 54.25-54.25 (median 54.25, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp585 | 2100 | median_vs_lit | 0.943 x lit median | **WARN** | ours 26.73 cm vs lit 27.88-28.82 (median 28.35), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| thermal exp. | ssp585 | 2100 | median_vs_lit | 0.954 x lit median | **WARN** | BRICK 2.0 27.05 cm vs the same lit median 28.35; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp585 | 2100 | spread_vs_lit | 0.775 x lit spread | **PASS** | ours 17.05 cm vs model-based lit 21.13-22.88 (median 22.00, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp585 | 2150 | median_vs_lit | 0.952 x lit median | **WARN** | ours 49.14 cm vs lit 49.94-53.35 (median 51.64), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| thermal exp. | ssp585 | 2150 | median_vs_lit | 0.967 x lit median | **PASS** | BRICK 2.0 49.95 cm vs the same lit median 51.64; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp585 | 2150 | spread_vs_lit | 0.819 x lit spread | **PASS** | ours 36.85 cm vs model-based lit 41.87-48.08 (median 44.98, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp585 | 2300 | median_vs_lit | 0.957 x lit median | **WARN** | ours 99.02 cm vs lit 103.49-103.49 (median 103.49), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| thermal exp. | ssp585 | 2300 | median_vs_lit | 0.968 x lit median | **WARN** | BRICK 2.0 100.22 cm vs the same lit median 103.49; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp585 | 2300 | spread_vs_lit | 0.792 x lit spread | **PASS** | ours 96.11 cm vs model-based lit 121.40-121.40 (median 121.40, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
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
| TOTAL | ssp126 | 2100 | median_vs_lit | 0.850 x lit median | **WARN** | ours 35.06 cm vs lit 35.59-46.11 (median 41.25), n_lit=7 [1 SEJ comparator(s) excluded from the score; full range 35.59-53.47] |
| TOTAL | ssp126 | 2100 | median_vs_lit | 0.951 x lit median | **PASS** | BRICK 2.0 39.24 cm vs the same lit median 41.25; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp126 | 2100 | spread_vs_lit | 1.941 x lit spread | **PASS** | ours 65.12 cm vs model-based lit 25.25-49.52 (median 33.55, n=7); ALL comparators 25.25-107.65 |
| TOTAL | ssp126 | 2150 | median_vs_lit | 0.691 x lit median | **WARN** | ours 45.68 cm vs lit 45.94-74.90 (median 66.11), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 45.94-83.12] |
| TOTAL | ssp126 | 2150 | median_vs_lit | 0.834 x lit median | **PASS** | BRICK 2.0 55.17 cm vs the same lit median 66.11; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp126 | 2150 | spread_vs_lit | 1.963 x lit spread | **PASS** | ours 114.42 cm vs model-based lit 53.31-79.31 (median 58.29, n=4); ALL comparators 53.31-200.59 |
| TOTAL | ssp126 | 2300 | median_vs_lit | 0.990 x lit median | **WARN** | ours 65.81 cm vs lit 66.49-66.49 (median 66.49), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| TOTAL | ssp126 | 2300 | median_vs_lit | 1.371 x lit median | **WARN** | BRICK 2.0 91.18 cm vs the same lit median 66.49; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp126 | 2300 | spread_vs_lit | 2.255 x lit spread | **WARN** | ours 262.92 cm vs model-based lit 116.60-116.60 (median 116.60, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |
| TOTAL | ssp245 | 2100 | median_vs_lit | 0.938 x lit median | **PASS** | ours 50.21 cm vs lit 48.68-57.10 (median 53.51), n_lit=7 [1 SEJ comparator(s) excluded from the score; full range 48.68-67.90] |
| TOTAL | ssp245 | 2100 | median_vs_lit | 1.325 x lit median | **WARN** | BRICK 2.0 70.87 cm vs the same lit median 53.51; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp245 | 2100 | spread_vs_lit | 1.431 x lit spread | **PASS** | ours 75.32 cm vs model-based lit 32.00-60.35 (median 52.65, n=7); ALL comparators 32.00-146.33 |
| TOTAL | ssp245 | 2150 | median_vs_lit | 1.130 x lit median | **WARN** | ours 105.22 cm vs lit 80.04-105.22 (median 93.13), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 80.04-111.19] |
| TOTAL | ssp245 | 2150 | median_vs_lit | 1.482 x lit median | **WARN** | BRICK 2.0 137.98 cm vs the same lit median 93.13; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp245 | 2150 | spread_vs_lit | 1.428 x lit spread | **WARN** | ours 149.52 cm vs model-based lit 59.41-382.80 (median 104.68, n=4); ALL comparators 59.41-382.80; ⚠ THE COMPARATORS DO NOT AGREE -- scored one at a time they give 1xhigh/2xin/1xlow and the median's 'in' is not a majority, so the median is not a summary here; verdict CAPPED at WARN |
| TOTAL | ssp245 | 2300 | median_vs_lit | 1.371 x lit median | **WARN** | ours 256.01 cm vs lit 186.77-186.77 (median 186.77), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| TOTAL | ssp245 | 2300 | median_vs_lit | 1.700 x lit median | **WARN** | BRICK 2.0 317.51 cm vs the same lit median 186.77; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp245 | 2300 | spread_vs_lit | 1.112 x lit spread | **PASS** | ours 377.79 cm vs model-based lit 339.75-339.75 (median 339.75, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary |
| TOTAL | ssp585 | 2100 | median_vs_lit | 1.269 x lit median | **WARN** | ours 100.81 cm vs lit 64.93-97.85 (median 79.41), n_lit=7 [1 SEJ comparator(s) excluded from the score; full range 64.93-97.85] |
| TOTAL | ssp585 | 2100 | median_vs_lit | 1.318 x lit median | **WARN** | BRICK 2.0 104.68 cm vs the same lit median 79.41; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp585 | 2100 | spread_vs_lit | 1.251 x lit spread | **PASS** | ours 87.97 cm vs model-based lit 41.09-106.79 (median 70.33, n=7); ALL comparators 41.09-197.47 |
| TOTAL | ssp585 | 2150 | median_vs_lit | 1.000 x lit median | **PASS** | ours 207.31 cm vs lit 117.08-310.66 (median 207.31), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 117.08-310.66] |
| TOTAL | ssp585 | 2150 | median_vs_lit | 0.978 x lit median | **PASS** | BRICK 2.0 202.83 cm vs the same lit median 207.31; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp585 | 2150 | spread_vs_lit | 0.572 x lit spread | **WARN** | ours 158.44 cm vs model-based lit 77.93-414.71 (median 277.00, n=4); ALL comparators 77.93-631.59; ⚠ THE COMPARATORS DO NOT AGREE -- scored one at a time they give 1xhigh/1xin/2xlow and the median's 'in' is not a majority, so the median is not a summary here; verdict CAPPED at WARN |
| TOTAL | ssp585 | 2300 | median_vs_lit | 0.484 x lit median | **WARN** | ours 491.83 cm vs lit 1015.98-1015.98 (median 1015.98), n_lit=1 ⚠ n_lit=1 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| TOTAL | ssp585 | 2300 | median_vs_lit | 0.475 x lit median | **WARN** | BRICK 2.0 482.40 cm vs the same lit median 1015.98; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp585 | 2300 | spread_vs_lit | 0.325 x lit spread | **WARN** | ours 447.86 cm vs model-based lit 1379.10-1379.10 (median 1379.10, n=1); ⚠ n=1 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |

## [P] Levels — every arm side by side (cm)

| module | ssp | horizon | candidate (joint) | champion (joint) | BRICK 2.0 (fixed) |
|---|---|---|---|---|---|
| AIS | ssp126 | 2100 | 4.79 | 4.29 | 4.21 |
| AIS | ssp126 | 2150 | 7.33 | 6.53 | 6.37 |
| AIS | ssp126 | 2300 | 14.26 | 12.67 | 12.64 |
| AIS | ssp245 | 2100 | 8.98 | 5.51 | 29.21 |
| AIS | ssp245 | 2150 | 46.94 | 11.16 | 74.53 |
| AIS | ssp245 | 2300 | 164.73 | 79.23 | 207.88 |
| AIS | ssp585 | 2100 | 43.40 | 35.05 | 48.98 |
| AIS | ssp585 | 2150 | 103.56 | 92.13 | 104.07 |
| AIS | ssp585 | 2300 | 307.51 | 277.34 | 290.17 |
| glaciers | ssp126 | 2100 | 7.66 | 7.73 | 12.00 |
| glaciers | ssp126 | 2150 | 9.37 | 9.42 | 17.18 |
| glaciers | ssp126 | 2300 | 11.75 | 11.80 | 27.26 |
| glaciers | ssp245 | 2100 | 9.66 | 9.77 | 13.48 |
| glaciers | ssp245 | 2150 | 13.47 | 13.49 | 20.82 |
| glaciers | ssp245 | 2300 | 18.30 | 18.19 | 32.41 |
| glaciers | ssp585 | 2100 | 13.88 | 14.00 | 16.47 |
| glaciers | ssp585 | 2150 | 21.45 | 21.45 | 27.14 |
| glaciers | ssp585 | 2300 | 27.04 | 27.01 | 35.20 |
| Greenland | ssp126 | 2100 | 6.25 | 6.25 | 6.60 |
| Greenland | ssp126 | 2150 | 7.51 | 7.58 | 9.92 |
| Greenland | ssp126 | 2300 | 9.29 | 9.47 | 18.79 |
| Greenland | ssp245 | 2100 | 8.23 | 8.19 | 7.09 |
| Greenland | ssp245 | 2150 | 11.91 | 11.96 | 11.43 |
| Greenland | ssp245 | 2300 | 16.96 | 17.12 | 23.76 |
| Greenland | ssp585 | 2100 | 13.40 | 13.35 | 8.24 |
| Greenland | ssp585 | 2150 | 27.09 | 26.99 | 15.57 |
| Greenland | ssp585 | 2300 | 47.32 | 47.48 | 40.35 |
| thermal exp. | ssp126 | 2100 | 13.50 | 13.51 | 13.76 |
| thermal exp. | ssp126 | 2150 | 16.87 | 16.88 | 17.22 |
| thermal exp. | ssp126 | 2300 | 22.15 | 22.08 | 22.80 |
| thermal exp. | ssp245 | 2100 | 17.78 | 17.73 | 18.03 |
| thermal exp. | ssp245 | 2150 | 26.23 | 26.26 | 26.68 |
| thermal exp. | ssp245 | 2300 | 41.15 | 40.67 | 42.05 |
| thermal exp. | ssp585 | 2100 | 26.73 | 26.60 | 27.05 |
| thermal exp. | ssp585 | 2150 | 49.14 | 49.06 | 49.95 |
| thermal exp. | ssp585 | 2300 | 99.02 | 98.47 | 100.22 |
| land water | ssp126 | 2100 | 2.60 | 2.60 | 2.34 |
| land water | ssp126 | 2150 | 4.23 | 4.23 | 4.04 |
| land water | ssp126 | 2300 | 8.48 | 8.48 | 8.90 |
| land water | ssp245 | 2100 | 2.60 | 2.60 | 2.34 |
| land water | ssp245 | 2150 | 4.23 | 4.23 | 4.04 |
| land water | ssp245 | 2300 | 8.48 | 8.48 | 8.90 |
| land water | ssp585 | 2100 | 2.60 | 2.60 | 2.34 |
| land water | ssp585 | 2150 | 4.23 | 4.23 | 4.04 |
| land water | ssp585 | 2300 | 8.48 | 8.48 | 8.90 |
| TOTAL | ssp126 | 2100 | 35.06 | 34.33 | 39.24 |
| TOTAL | ssp126 | 2150 | 45.68 | 44.64 | 55.17 |
| TOTAL | ssp126 | 2300 | 65.81 | 64.44 | 91.18 |
| TOTAL | ssp245 | 2100 | 50.21 | 44.92 | 70.87 |
| TOTAL | ssp245 | 2150 | 105.22 | 71.57 | 137.98 |
| TOTAL | ssp245 | 2300 | 256.01 | 162.84 | 317.51 |
| TOTAL | ssp585 | 2100 | 100.81 | 92.45 | 104.68 |
| TOTAL | ssp585 | 2150 | 207.31 | 195.59 | 202.83 |
| TOTAL | ssp585 | 2300 | 491.83 | 461.72 | 482.40 |

## [S] Scenario separation — ssp585/ssp126 median ratio

| module | horizon | ours | verdict | literature |
|---|---|---|---|---|
| AIS | 2100 | 9.07x | **PASS** | FACTS 0.63-3.20 (n=5); MAGICC-SLR 10.69-10.69 (n=1) |
| AIS | 2150 | 14.14x | **PASS** | FACTS 0.48-7.55 (n=4); MAGICC-SLR 28.79-28.79 (n=1) |
| AIS | 2300 | 21.57x | **WARN** | MAGICC-SLR 81.77-81.77 (n=1)  [NO UPPER COMPARATOR AT THIS HORIZON] |
| glaciers | 2100 | 1.81x | **PASS** | FACTS 1.73-1.92 (n=2); MAGICC-SLR 1.46-1.46 (n=1) |
| glaciers | 2150 | 2.29x | **PASS** | FACTS 2.37-2.37 (n=1); MAGICC-SLR 1.79-1.79 (n=1) |
| glaciers | 2300 | 2.30x | **WARN** | MAGICC-SLR 2.11-2.11 (n=1)  [NO UPPER COMPARATOR AT THIS HORIZON] |
| Greenland | 2100 | 2.14x | **PASS** | FACTS 1.55-2.33 (n=3); MAGICC-SLR 2.11-2.11 (n=1) |
| Greenland | 2150 | 3.60x | **PASS(edge)** | FACTS 1.72-2.07 (n=2); MAGICC-SLR 3.48-3.48 (n=1); 0.13 outside the bracket = 7% of its own range |
| Greenland | 2300 | 5.10x | **WARN** | MAGICC-SLR 7.54-7.54 (n=1)  [NO UPPER COMPARATOR AT THIS HORIZON] |
| thermal exp. | 2100 | 1.98x | **PASS(edge)** | FACTS 2.05-2.05 (n=1); MAGICC-SLR 2.51-2.51 (n=1); 0.07 outside the bracket = 15% of its own range |
| thermal exp. | 2150 | 2.91x | **PASS(edge)** | FACTS 2.99-2.99 (n=1); MAGICC-SLR 3.94-3.94 (n=1); 0.08 outside the bracket = 8% of its own range |
| thermal exp. | 2300 | 4.47x | **WARN** | MAGICC-SLR 6.18-6.18 (n=1)  [NO UPPER COMPARATOR AT THIS HORIZON] |
| land water | 2100 | 1.00x | **PASS** | FACTS 0.99-0.99 (n=1); MAGICC-SLR 1.00-1.00 (n=1) |
| land water | 2150 | 1.00x | **PASS** | FACTS 1.03-1.03 (n=1); MAGICC-SLR 1.00-1.00 (n=1) |
| land water | 2300 | 1.00x | **PASS** | MAGICC-SLR 1.00-1.00 (n=1)  [NO UPPER COMPARATOR AT THIS HORIZON] |
| TOTAL | 2100 | 2.88x | **PASS(edge)** | FACTS 1.63-2.23 (n=7); MAGICC-SLR 2.75-2.75 (n=1); 0.13 outside the bracket = 11% of its own range |
| TOTAL | 2150 | 4.54x | **PASS** | FACTS 1.94-4.15 (n=4); MAGICC-SLR 5.72-5.72 (n=1) |
| TOTAL | 2300 | 7.47x | **WARN** | MAGICC-SLR 15.28-15.28 (n=1)  [NO UPPER COMPARATOR AT THIS HORIZON] |

---

*Machine-readable: `outputs/bench_ladrillo_L16.csv`. Regenerate: `python python/bench_ladrillo.py --tag=L16`.*
