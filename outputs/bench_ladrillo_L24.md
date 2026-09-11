# Ladrillo benchmark — `L24`

*benchmark v1.0, 2026-09-11, repo `b7ad086`. Champion arm: **L24** (the candidate IS the champion — no delta column).*

Arms: **candidate** (live `outputs/`), **champion\*** (frozen), **BRICK 2.0** (stock MimiBRICK v2.0.0, own posterior), **literature** (FACTS + MAGICC-SLR, frozen).

## Caveats that travel with every verdict

* HINDCAST RANKS IN ONE DIRECTION ONLY -- in-sample for every Ladrillo arm, out-of-sample for BRICK 2.0. It can REJECT an arm; a small fitted bias is not skill.
* BANDS ARE NOT ONE OBJECT -- Ladrillo-fixed is posterior-parameter spread; Ladrillo-JOINT, FACTS and MAGICC carry climate uncertainty. Only the JOINT band is scored against the literature. NOTE 2026-08-30: BRICK 2.0 NOW HAS A JOINT ARM TOO (scope_slr_fairunc_oldbrick.jl), but THIS BENCHMARK still takes BRICK 2.0 from the shipped FIXED panel (brick20_projection), so BRICK widths here remain fixed-driver. ladrillo_model_comparison.py DOES use the joint arm. Do not read a width comparison against BRICK 2.0 out of this table -- read it out of the comparison.
* SOME WIDTH IS A PRIOR, NOT AN INFERENCE -- 78% of the ssp585 2300 AIS band is antarctic_lambda's paleo prior, so narrowness is never scored as a win at ais/ssp585.
* WHERE THE OBSERVED STATISTIC IS UNDER 2.0 SIGMA FROM ZERO the RATIO model/obs is suppressed as uninterpretable, but the DIFFERENCE is still graded on z -- being 3 sigma from a value that is itself 1 sigma from zero is still a miss.
* THE MODERN AIS RATE CANNOT REJECT ZERO -- IMBIE whole-sheet loss is 0.95-1.44 sigma from zero, so the 1993-2026 window separates no two AIS models however different they are.
* A p5-p95 SPREAD IS BLIND TO A MODE UNDER 5% OF THE MASS -- cells whose p05-p99/p05-p95 exceeds 2.0x the Gaussian 1.207 are marked N/A(bimodal) and NOT scored on width; quote the mean and the tipped fraction there.
* ssp245@2300 IS A THRESHOLD ARTIFACT -- 48.3% of draws tip, so its MEDIAN is bimodal-fragile. Quote the mean and the tipped fraction there, never the bare median.

## [V] Roll-up

| module | hindcast | rate/accel | projection | separation | vs champion |
|---|---|---|---|---|---|
| **AIS** | PASS | UNRESOLVED | FAIL | PASS | — |
| **glaciers** | WARN | UNRESOLVED | WARN | PASS | — |
| **Greenland** | PASS | UNRESOLVED | FAIL | PASS | — |
| **thermal exp.** | WARN | FAIL | PASS | PASS | — |
| **land water** | — | — | WARN | PASS | — |
| **TOTAL** | PASS | UNRESOLVED | WARN | PASS | — |

## [H] Hindcast — the full observational period, scaled to each component's own target 1-sigma

| module | target 1σ (cm) | window | arm | RMSE (cm) | RMSE (σ) | note |
|---|---|---|---|---|---|---|
| AIS | 0.1674 | full | L24 | 0.0292 | 0.17 | bias -0.0042 cm = -0.02 sd; cov90 85%; n=126 |
| AIS | 0.1674 | full | BRICK 2.0 | 1.5740 | 9.40 | bias -1.1500 cm = -6.87 sd; cov90 25%; n=126 |
| AIS | 0.1674 | 1920-1949 | L24 | 0.0099 | 0.06 | bias -0.0096 cm = -0.06 sd; cov90 100%; n=30 |
| AIS | 0.1674 | 1920-1949 | BRICK 2.0 | 1.9565 | 11.68 | bias -1.9306 cm = -11.53 sd; cov90 0%; n=30 |
| AIS | 0.1674 | 1950-1992 | L24 | 0.0084 | 0.05 | bias +0.0027 cm = +0.02 sd; cov90 98%; n=43 |
| AIS | 0.1674 | 1950-1992 | BRICK 2.0 | 0.8044 | 4.80 | bias -0.7067 cm = -4.22 sd; cov90 0%; n=43 |
| AIS | 0.1674 | 1993-2026 | L24 | 0.0550 | 0.33 | bias -0.0057 cm = -0.03 sd; cov90 45%; n=33 |
| AIS | 0.1674 | 1993-2026 | BRICK 2.0 | 0.0814 | 0.49 | bias +0.0424 cm = +0.25 sd; cov90 97%; n=33 |
| glaciers | 0.4593 | full | L24 | 0.6484 | 1.41 | bias +0.3694 cm = +0.80 sd; cov90 44%; n=124 |
| glaciers | 0.4593 | full | BRICK 2.0 | 1.5475 | 3.37 | bias +0.9400 cm = +2.05 sd; cov90 42%; n=124 |
| glaciers | 0.4593 | 1920-1949 | L24 | 0.5909 | 1.29 | bias +0.5283 cm = +1.15 sd; cov90 20%; n=30 |
| glaciers | 0.4593 | 1920-1949 | BRICK 2.0 | 1.5932 | 3.47 | bias +1.4701 cm = +3.20 sd; cov90 0%; n=30 |
| glaciers | 0.4593 | 1950-1992 | L24 | 0.1347 | 0.29 | bias +0.0783 cm = +0.17 sd; cov90 56%; n=43 |
| glaciers | 0.4593 | 1950-1992 | BRICK 2.0 | 0.1269 | 0.28 | bias +0.0552 cm = +0.12 sd; cov90 95%; n=43 |
| glaciers | 0.4593 | 1993-2026 | L24 | 0.0874 | 0.19 | bias -0.0522 cm = -0.11 sd; cov90 81%; n=31 |
| glaciers | 0.4593 | 1993-2026 | BRICK 2.0 | 0.2143 | 0.47 | bias +0.1441 cm = +0.31 sd; cov90 35%; n=31 |
| Greenland | 0.1832 | full | L24 | 0.0598 | 0.33 | bias +0.0042 cm = +0.02 sd; cov90 60%; n=126 |
| Greenland | 0.1832 | full | BRICK 2.0 | 0.7030 | 3.84 | bias -0.5958 cm = -3.25 sd; cov90 19%; n=126 |
| Greenland | 0.1832 | 1920-1949 | L24 | 0.0808 | 0.44 | bias +0.0267 cm = +0.15 sd; cov90 53%; n=30 |
| Greenland | 0.1832 | 1920-1949 | BRICK 2.0 | 0.7952 | 4.34 | bias -0.7459 cm = -4.07 sd; cov90 27%; n=30 |
| Greenland | 0.1832 | 1950-1992 | L24 | 0.0494 | 0.27 | bias -0.0142 cm = -0.08 sd; cov90 58%; n=43 |
| Greenland | 0.1832 | 1950-1992 | BRICK 2.0 | 0.9104 | 4.97 | bias -0.8614 cm = -4.70 sd; cov90 0%; n=43 |
| Greenland | 0.1832 | 1993-2026 | L24 | 0.0459 | 0.25 | bias +0.0018 cm = +0.01 sd; cov90 45%; n=33 |
| Greenland | 0.1832 | 1993-2026 | BRICK 2.0 | 0.1745 | 0.95 | bias -0.1258 cm = -0.69 sd; cov90 45%; n=33 |
| thermal exp. | 0.3091 | full | L24 | 0.4396 | 1.42 | bias +0.2198 cm = +0.71 sd; cov90 33%; n=126 |
| thermal exp. | 0.3091 | full | BRICK 2.0 | 0.5357 | 1.73 | bias +0.3440 cm = +1.11 sd; cov90 91%; n=126 |
| thermal exp. | 0.3091 | 1920-1949 | L24 | 0.5452 | 1.76 | bias +0.4078 cm = +1.32 sd; cov90 33%; n=30 |
| thermal exp. | 0.3091 | 1920-1949 | BRICK 2.0 | 0.7538 | 2.44 | bias +0.6519 cm = +2.11 sd; cov90 90%; n=30 |
| thermal exp. | 0.3091 | 1950-1992 | L24 | 0.2156 | 0.70 | bias -0.1063 cm = -0.34 sd; cov90 56%; n=43 |
| thermal exp. | 0.3091 | 1950-1992 | BRICK 2.0 | 0.1948 | 0.63 | bias +0.0381 cm = +0.12 sd; cov90 100%; n=43 |
| thermal exp. | 0.3091 | 1993-2026 | L24 | 0.4299 | 1.39 | bias +0.2831 cm = +0.92 sd; cov90 12%; n=33 |
| thermal exp. | 0.3091 | 1993-2026 | BRICK 2.0 | 0.2830 | 0.92 | bias +0.1779 cm = +0.58 sd; cov90 85%; n=33 |
| TOTAL | 1.5380 | full | L24 | 0.8646 | 0.56 | bias +0.6898 cm = +0.45 sd; cov90 30%; n=125 |
| TOTAL | 1.5380 | full | BRICK 2.0 | 0.7377 | 0.48 | bias -0.3148 cm = -0.20 sd; cov90 47%; n=125 |
| TOTAL | 1.5380 | 1920-1949 | L24 | 1.0471 | 0.68 | bias +0.9894 cm = +0.64 sd; cov90 27%; n=30 |
| TOTAL | 1.5380 | 1920-1949 | BRICK 2.0 | 0.7651 | 0.50 | bias -0.4210 cm = -0.27 sd; cov90 63%; n=30 |
| TOTAL | 1.5380 | 1950-1992 | L24 | 0.5171 | 0.34 | bias +0.4809 cm = +0.31 sd; cov90 35%; n=43 |
| TOTAL | 1.5380 | 1950-1992 | BRICK 2.0 | 0.9966 | 0.65 | bias -0.9052 cm = -0.59 sd; cov90 9%; n=43 |
| TOTAL | 1.5380 | 1993-2026 | L24 | 0.3569 | 0.23 | bias +0.1973 cm = +0.13 sd; cov90 41%; n=32 |
| TOTAL | 1.5380 | 1993-2026 | BRICK 2.0 | 0.4002 | 0.26 | bias +0.2089 cm = +0.14 sd; cov90 50%; n=32 |

## [R] Rate (1993-2026) and acceleration (1900-2026), with an error bar on the observations

| module | statistic | arm | value | unit | z vs obs bar | note |
|---|---|---|---|---|---|---|
| AIS | rate | observations | 0.032608 | cm/yr | — | se: estimator 0.003405, band-correlated 0.0005689, band-independent 0.003061; CONSERVATIVE 0.003405 cm/yr; |obs|/se = 9.58 |
| AIS | rate | L24 | 0.031598 | cm/yr | -0.30 | 0.97x obs; z=-0.30 vs the obs error bar |
| AIS | rate | BRICK 2.0 | 0.03785 | cm/yr | +1.54 | 1.16x obs; z=+1.54 vs the obs error bar |
| glaciers | rate | observations | 0.068013 | cm/yr | — | se: estimator 0.0005236, band-correlated 0.0001274, band-independent 0.009223; CONSERVATIVE 0.009223 cm/yr; |obs|/se = 7.37 |
| glaciers | rate | L24 | 0.06276 | cm/yr | -0.57 | 0.92x obs; z=-0.57 vs the obs error bar |
| glaciers | rate | BRICK 2.0 | 0.087211 | cm/yr | +2.08 | 1.28x obs; z=+2.08 vs the obs error bar |
| Greenland | rate | observations | 0.06596 | cm/yr | — | se: estimator 0.01044, band-correlated 0.0006502, band-independent 0.003349; CONSERVATIVE 0.01044 cm/yr; |obs|/se = 6.32 |
| Greenland | rate | L24 | 0.065783 | cm/yr | -0.02 | 1.00x obs; z=-0.02 vs the obs error bar |
| Greenland | rate | BRICK 2.0 | 0.057934 | cm/yr | -0.77 | 0.88x obs; z=-0.77 vs the obs error bar |
| thermal exp. | rate | observations | 0.1234 | cm/yr | — | se: estimator 0.003756, band-correlated 0.002392, band-independent 0.005651; CONSERVATIVE 0.005651 cm/yr; |obs|/se = 21.84 |
| thermal exp. | rate | L24 | 0.15655 | cm/yr | +5.87 | 1.27x obs UNCORRECTED, 1.15x at the FULL depth-scope bound; z spans +3.64..+5.87. Model is FULL-DEPTH, target is 0-2000 m; factor <= 1.1022 from IGCC ocean_2000-6000m (PRESCRIBED 1.15 ZJ/yr, not data), and it OVERSTATES the correction because deep water expands less per joule. NOT applied to accel: a prescribed constant rate carries no curvature. |
| thermal exp. | rate | BRICK 2.0 | 0.14458 | cm/yr | +3.75 | 1.17x obs UNCORRECTED, 1.06x at the FULL depth-scope bound; z spans +1.52..+3.75. Model is FULL-DEPTH, target is 0-2000 m; factor <= 1.1022 from IGCC ocean_2000-6000m (PRESCRIBED 1.15 ZJ/yr, not data), and it OVERSTATES the correction because deep water expands less per joule. NOT applied to accel: a prescribed constant rate carries no curvature. |
| TOTAL | rate | observations | 0.32469 | cm/yr | — | se: estimator 0.02949, band-correlated 0.02545, band-independent 0.02945; CONSERVATIVE 0.02949 cm/yr; |obs|/se = 11.01 |
| TOTAL | rate | L24 | 0.34702 | cm/yr | +0.76 | 1.07x obs; z=+0.76 vs the obs error bar |
| TOTAL | rate | BRICK 2.0 | 0.35585 | cm/yr | +1.06 | 1.10x obs; z=+1.06 vs the obs error bar |
| AIS | accel | observations | 0.00020499 | cm/yr2 | — | se: estimator 0.0001336, band-correlated 3.924e-05, band-independent 2.522e-05; CONSERVATIVE 0.0001336 cm/yr2; |obs|/se = 1.53 |
| AIS | accel | L24 | 0.00020415 | cm/yr2 | -0.01 | ratio NOT INTERPRETABLE (obs is 1.53 se from zero); z=-0.01 vs the obs error bar |
| AIS | accel | BRICK 2.0 | -0.00012334 | cm/yr2 | -2.46 | ratio NOT INTERPRETABLE (obs is 1.53 se from zero); z=-2.46 vs the obs error bar |
| glaciers | accel | observations | -0.00054814 | cm/yr2 | — | se: estimator 0.000447, band-correlated 3.442e-05, band-independent 7.199e-05; CONSERVATIVE 0.000447 cm/yr2; |obs|/se = 1.23 |
| glaciers | accel | L24 | -0.00010791 | cm/yr2 | +0.98 | ratio NOT INTERPRETABLE (obs is 1.23 se from zero); z=+0.98 vs the obs error bar |
| glaciers | accel | BRICK 2.0 | 0.00063496 | cm/yr2 | +2.65 | ratio NOT INTERPRETABLE (obs is 1.23 se from zero); z=+2.65 vs the obs error bar |
| Greenland | accel | observations | -0.00027825 | cm/yr2 | — | se: estimator 0.0005241, band-correlated 6.83e-05, band-independent 2.759e-05; CONSERVATIVE 0.0005241 cm/yr2; |obs|/se = 0.53 |
| Greenland | accel | L24 | -0.00025266 | cm/yr2 | +0.05 | ratio NOT INTERPRETABLE (obs is 0.53 se from zero); z=+0.05 vs the obs error bar |
| Greenland | accel | BRICK 2.0 | 0.00010691 | cm/yr2 | +0.73 | ratio NOT INTERPRETABLE (obs is 0.53 se from zero); z=+0.73 vs the obs error bar |
| thermal exp. | accel | observations | 0.0008428 | cm/yr2 | — | se: estimator 0.0002431, band-correlated 2.312e-05, band-independent 4.655e-05; CONSERVATIVE 0.0002431 cm/yr2; |obs|/se = 3.47 |
| thermal exp. | accel | L24 | 0.001274 | cm/yr2 | +1.77 | 1.51x obs; z=+1.77 vs the obs error bar |
| thermal exp. | accel | BRICK 2.0 | 0.0011766 | cm/yr2 | +1.37 | 1.40x obs; z=+1.37 vs the obs error bar |
| TOTAL | accel | observations | 0.00089376 | cm/yr2 | — | se: estimator 0.001159, band-correlated 0.0001276, band-independent 0.0002363; CONSERVATIVE 0.001159 cm/yr2; |obs|/se = 0.77 |
| TOTAL | accel | L24 | 0.0012964 | cm/yr2 | +0.35 | ratio NOT INTERPRETABLE (obs is 0.77 se from zero); z=+0.35 vs the obs error bar |
| TOTAL | accel | BRICK 2.0 | 0.0019643 | cm/yr2 | +0.92 | ratio NOT INTERPRETABLE (obs is 0.77 se from zero); z=+0.92 vs the obs error bar |

## [P] Projections vs the literature — scored on the JOINT band

| module | ssp | horizon | metric | value | verdict | note |
|---|---|---|---|---|---|---|
| AIS | ssp126 | 2100 | median_vs_lit | 0.527 x lit median | **PASS** | ours 4.76 cm vs lit 3.66-11.93 (median 9.04), n_lit=5 [1 SEJ comparator(s) excluded from the score; full range 3.66-11.93] |
| AIS | ssp126 | 2100 | median_vs_lit | 0.478 x lit median | **PASS** | BRICK 2.0 4.32 cm vs the same lit median 9.04; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp126 | 2100 | spread_vs_lit | 2.553 x lit spread | **FAIL** | ours 54.64 cm vs model-based lit 20.72-40.49 (median 21.40, n=5); ALL comparators 20.72-105.01 |
| AIS | ssp126 | 2150 | median_vs_lit | 0.401 x lit median | **PASS** | ours 7.33 cm vs lit 5.34-27.64 (median 18.27), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 5.34-27.64] |
| AIS | ssp126 | 2150 | median_vs_lit | 0.357 x lit median | **PASS** | BRICK 2.0 6.52 cm vs the same lit median 18.27; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp126 | 2150 | spread_vs_lit | 1.814 x lit spread | **WARN** | ours 104.38 cm vs model-based lit 33.17-242.51 (median 57.53, n=4); ALL comparators 33.17-242.51; ⚠ THE COMPARATORS DO NOT AGREE -- scored one at a time they give 2xhigh/1xin/1xlow and the median's 'in' is not a majority, so the median is not a summary here; verdict CAPPED at WARN |
| AIS | ssp126 | 2300 | median_vs_lit | 0.330 x lit median | **PASS** | ours 14.48 cm vs lit 8.71-126.56 (median 43.88), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 8.71-126.56] |
| AIS | ssp126 | 2300 | median_vs_lit | 0.297 x lit median | **PASS** | BRICK 2.0 13.01 cm vs the same lit median 43.88; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp126 | 2300 | spread_vs_lit | 1.694 x lit spread | **WARN** | ours 245.86 cm vs model-based lit 69.60-916.01 (median 145.14, n=4); ALL comparators 69.60-916.01; ⚠ THE COMPARATORS DO NOT AGREE -- scored one at a time they give 1xhigh/2xin/1xlow and the median's 'in' is not a majority, so the median is not a summary here; verdict CAPPED at WARN |
| AIS | ssp245 | 2100 | median_vs_lit | 0.736 x lit median | **PASS** | ours 7.72 cm vs lit 5.22-12.17 (median 10.49), n_lit=5 [1 SEJ comparator(s) excluded from the score; full range 5.22-12.17] |
| AIS | ssp245 | 2100 | median_vs_lit | 2.613 x lit median | **FAIL** | BRICK 2.0 27.41 cm vs the same lit median 10.49; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp245 | 2100 | spread_vs_lit | 1.739 x lit spread | **PASS** | ours 62.28 cm vs model-based lit 20.77-42.39 (median 35.81, n=5); ALL comparators 20.77-113.21 |
| AIS | ssp245 | 2150 | median_vs_lit | 1.459 x lit median | **WARN** | ours 39.85 cm vs lit 10.52-30.38 (median 27.31), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 10.52-30.38] |
| AIS | ssp245 | 2150 | median_vs_lit | 2.658 x lit median | **FAIL** | BRICK 2.0 72.60 cm vs the same lit median 27.31; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp245 | 2150 | spread_vs_lit | 1.513 x lit spread | **WARN** | ours 129.18 cm vs model-based lit 45.12-305.79 (median 85.41, n=4); ALL comparators 45.12-305.79; ⚠ THE COMPARATORS DO NOT AGREE -- scored one at a time they give 1xhigh/2xin/1xlow and the median's 'in' is not a majority, so the median is not a summary here; verdict CAPPED at WARN |
| AIS | ssp245 | 2300 | median_vs_lit | 2.075 x lit median | **FAIL** | ours 154.29 cm vs lit 40.85-136.38 (median 74.34), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 40.85-136.38] |
| AIS | ssp245 | 2300 | median_vs_lit | 2.770 x lit median | **FAIL** | BRICK 2.0 205.94 cm vs the same lit median 74.34; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp245 | 2300 | spread_vs_lit | 1.418 x lit spread | **PASS** | ours 332.11 cm vs model-based lit 168.75-1284.94 (median 234.17, n=4); ALL comparators 168.75-1284.94 |
| AIS | ssp585 | 2100 | median_vs_lit | 2.838 x lit median | **PASS** | ours 37.45 cm vs lit 4.30-39.10 (median 13.20), n_lit=5 [1 SEJ comparator(s) excluded from the score; full range 4.30-39.10] |
| AIS | ssp585 | 2100 | median_vs_lit | 3.345 x lit median | **FAIL** | BRICK 2.0 44.14 cm vs the same lit median 13.20; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp585 | 2100 | spread_vs_lit | 1.406 x lit spread | **PASS** | ours 72.24 cm vs model-based lit 20.71-79.00 (median 51.40, n=5); ALL comparators 20.71-126.10; width here is the antarctic_lambda PRIOR -- do NOT narrow |
| AIS | ssp585 | 2150 | median_vs_lit | 1.178 x lit median | **PASS** | ours 95.70 cm vs lit 6.93-153.62 (median 81.21), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 6.93-153.62] |
| AIS | ssp585 | 2150 | median_vs_lit | 1.205 x lit median | **PASS** | BRICK 2.0 97.88 cm vs the same lit median 81.21; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp585 | 2150 | spread_vs_lit | 0.588 x lit spread | **WARN** | ours 118.10 cm vs model-based lit 48.47-385.93 (median 200.75, n=4); ALL comparators 48.47-505.64; ⚠ THE COMPARATORS DO NOT AGREE -- scored one at a time they give 1xhigh/1xin/2xlow and the median's 'in' is not a majority, so the median is not a summary here; verdict CAPPED at WARN; width here is the antarctic_lambda PRIOR -- do NOT narrow |
| AIS | ssp585 | 2300 | median_vs_lit | 1.083 x lit median | **PASS** | ours 292.53 cm vs lit 22.49-712.02 (median 270.00), n_lit=6 [1 SEJ comparator(s) excluded from the score; full range 22.49-712.02] |
| AIS | ssp585 | 2300 | median_vs_lit | 1.025 x lit median | **PASS** | BRICK 2.0 276.83 cm vs the same lit median 270.00; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| AIS | ssp585 | 2300 | spread_vs_lit | 0.483 x lit spread | **WARN** | ours 329.46 cm vs model-based lit 185.62-1403.35 (median 682.37, n=4); ALL comparators 185.62-1403.35; ⚠ THE COMPARATORS DO NOT AGREE -- scored one at a time they give 2xin/2xlow and the median's 'low' is not a majority, so the median is not a summary here; verdict CAPPED at WARN; width here is the antarctic_lambda PRIOR -- do NOT narrow |
| glaciers | ssp126 | 2100 | median_vs_lit | 0.765 x lit median | **WARN** | ours 7.92 cm vs lit 9.72-10.45 (median 10.36), n_lit=3 |
| glaciers | ssp126 | 2100 | median_vs_lit | 1.167 x lit median | **WARN** | BRICK 2.0 12.09 cm vs the same lit median 10.36; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp126 | 2100 | spread_vs_lit | 0.770 x lit spread | **PASS** | ours 5.95 cm vs model-based lit 7.12-10.06 (median 7.74, n=3) |
| glaciers | ssp126 | 2150 | median_vs_lit | 0.757 x lit median | **WARN** | ours 9.79 cm vs lit 12.28-13.60 (median 12.94), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp126 | 2150 | median_vs_lit | 1.348 x lit median | **WARN** | BRICK 2.0 17.44 cm vs the same lit median 12.94; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp126 | 2150 | spread_vs_lit | 0.650 x lit spread | **PASS** | ours 7.80 cm vs model-based lit 8.52-15.46 (median 11.99, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| glaciers | ssp126 | 2300 | median_vs_lit | 0.676 x lit median | **WARN** | ours 12.38 cm vs lit 13.80-22.85 (median 18.33), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp126 | 2300 | median_vs_lit | 1.512 x lit median | **WARN** | BRICK 2.0 27.72 cm vs the same lit median 18.33; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp126 | 2300 | spread_vs_lit | 0.664 x lit spread | **PASS** | ours 10.80 cm vs model-based lit 11.23-21.30 (median 16.26, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| glaciers | ssp245 | 2100 | median_vs_lit | 0.763 x lit median | **WARN** | ours 9.56 cm vs lit 11.22-12.90 (median 12.54), n_lit=3 |
| glaciers | ssp245 | 2100 | median_vs_lit | 1.064 x lit median | **WARN** | BRICK 2.0 13.34 cm vs the same lit median 12.54; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp245 | 2100 | spread_vs_lit | 0.805 x lit spread | **PASS** | ours 6.74 cm vs model-based lit 7.42-11.15 (median 8.38, n=3) |
| glaciers | ssp245 | 2150 | median_vs_lit | 0.770 x lit median | **WARN** | ours 13.30 cm vs lit 16.71-17.82 (median 17.27), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp245 | 2150 | median_vs_lit | 1.198 x lit median | **WARN** | BRICK 2.0 20.69 cm vs the same lit median 17.27; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp245 | 2150 | spread_vs_lit | 0.682 x lit spread | **PASS** | ours 9.87 cm vs model-based lit 9.16-19.79 (median 14.47, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| glaciers | ssp245 | 2300 | median_vs_lit | 0.687 x lit median | **WARN** | ours 18.21 cm vs lit 21.47-31.57 (median 26.52), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp245 | 2300 | median_vs_lit | 1.226 x lit median | **WARN** | BRICK 2.0 32.50 cm vs the same lit median 26.52; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp245 | 2300 | spread_vs_lit | 1.048 x lit spread | **PASS** | ours 13.24 cm vs model-based lit 10.95-14.32 (median 12.63, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| glaciers | ssp585 | 2100 | median_vs_lit | 0.838 x lit median | **WARN** | ours 12.81 cm vs lit 13.93-17.13 (median 15.30), n_lit=3 |
| glaciers | ssp585 | 2100 | median_vs_lit | 1.020 x lit median | **PASS** | BRICK 2.0 15.61 cm vs the same lit median 15.30; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp585 | 2100 | spread_vs_lit | 0.918 x lit spread | **PASS** | ours 8.36 cm vs model-based lit 8.51-14.02 (median 9.10, n=3) |
| glaciers | ssp585 | 2150 | median_vs_lit | 0.841 x lit median | **WARN** | ours 20.30 cm vs lit 22.03-26.22 (median 24.13), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp585 | 2150 | median_vs_lit | 1.088 x lit median | **WARN** | BRICK 2.0 26.25 cm vs the same lit median 24.13; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp585 | 2150 | spread_vs_lit | 0.838 x lit spread | **PASS** | ours 11.38 cm vs model-based lit 10.09-17.06 (median 13.58, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| glaciers | ssp585 | 2300 | median_vs_lit | 0.875 x lit median | **WARN** | ours 26.53 cm vs lit 29.10-31.57 (median 30.34), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| glaciers | ssp585 | 2300 | median_vs_lit | 1.166 x lit median | **WARN** | BRICK 2.0 35.36 cm vs the same lit median 30.34; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| glaciers | ssp585 | 2300 | spread_vs_lit | 2.417 x lit spread | **WARN** | ours 12.04 cm vs model-based lit 0.13-9.83 (median 4.98, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |
| Greenland | ssp126 | 2100 | median_vs_lit | 1.029 x lit median | **PASS** | ours 6.58 cm vs lit 6.36-8.31 (median 6.40), n_lit=3 [1 SEJ comparator(s) excluded from the score; full range 6.36-13.80] |
| Greenland | ssp126 | 2100 | median_vs_lit | 1.034 x lit median | **PASS** | BRICK 2.0 6.62 cm vs the same lit median 6.40; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp126 | 2100 | spread_vs_lit | 0.472 x lit spread | **FAIL** | ours 4.52 cm vs model-based lit 8.22-17.86 (median 9.57, n=3); ALL comparators 8.22-68.88 |
| Greenland | ssp126 | 2150 | median_vs_lit | 0.682 x lit median | **WARN** | ours 8.09 cm vs lit 9.31-14.39 (median 11.85), n_lit=2 [1 SEJ comparator(s) excluded from the score; full range 9.31-24.45] ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp126 | 2150 | median_vs_lit | 0.844 x lit median | **PASS** | BRICK 2.0 10.01 cm vs the same lit median 11.85; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp126 | 2150 | spread_vs_lit | 0.436 x lit spread | **WARN** | ours 6.75 cm vs model-based lit 15.32-15.69 (median 15.51, n=2); ALL comparators 15.32-93.49; ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |
| Greenland | ssp126 | 2300 | median_vs_lit | 0.430 x lit median | **WARN** | ours 10.19 cm vs lit 14.98-32.45 (median 23.71), n_lit=2 [1 SEJ comparator(s) excluded from the score; full range 14.98-61.49] ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp126 | 2300 | median_vs_lit | 0.803 x lit median | **PASS** | BRICK 2.0 19.04 cm vs the same lit median 23.71; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp126 | 2300 | spread_vs_lit | 0.357 x lit spread | **WARN** | ours 11.79 cm vs model-based lit 29.41-36.69 (median 33.05, n=2); ALL comparators 29.41-275.26; ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |
| Greenland | ssp245 | 2100 | median_vs_lit | 0.887 x lit median | **PASS** | ours 8.23 cm vs lit 8.12-9.59 (median 9.28), n_lit=3 [1 SEJ comparator(s) excluded from the score; full range 8.12-14.49] |
| Greenland | ssp245 | 2100 | median_vs_lit | 0.757 x lit median | **WARN** | BRICK 2.0 7.03 cm vs the same lit median 9.28; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp245 | 2100 | spread_vs_lit | 0.701 x lit spread | **PASS** | ours 5.86 cm vs model-based lit 7.77-17.73 (median 8.35, n=3); ALL comparators 7.77-77.52 |
| Greenland | ssp245 | 2150 | median_vs_lit | 0.694 x lit median | **WARN** | ours 11.97 cm vs lit 16.53-17.98 (median 17.26), n_lit=2 [1 SEJ comparator(s) excluded from the score; full range 16.53-25.78] ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp245 | 2150 | median_vs_lit | 0.657 x lit median | **WARN** | BRICK 2.0 11.35 cm vs the same lit median 17.26; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp245 | 2150 | spread_vs_lit | 0.765 x lit spread | **PASS** | ours 11.55 cm vs model-based lit 14.88-15.32 (median 15.10, n=2); ALL comparators 14.88-104.03; ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| Greenland | ssp245 | 2300 | median_vs_lit | 0.446 x lit median | **WARN** | ours 17.52 cm vs lit 35.79-42.74 (median 39.27), n_lit=2 [1 SEJ comparator(s) excluded from the score; full range 35.79-68.69] ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| Greenland | ssp245 | 2300 | median_vs_lit | 0.604 x lit median | **WARN** | BRICK 2.0 23.71 cm vs the same lit median 39.27; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp245 | 2300 | spread_vs_lit | 0.778 x lit spread | **PASS** | ours 31.05 cm vs model-based lit 38.95-40.91 (median 39.93, n=2); ALL comparators 38.95-296.05; ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| Greenland | ssp585 | 2100 | median_vs_lit | 0.989 x lit median | **PASS** | ours 12.10 cm vs lit 11.67-13.49 (median 12.23), n_lit=3 [1 SEJ comparator(s) excluded from the score; full range 11.67-17.18] |
| Greenland | ssp585 | 2100 | median_vs_lit | 0.644 x lit median | **WARN** | BRICK 2.0 7.88 cm vs the same lit median 12.23; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp585 | 2100 | spread_vs_lit | 0.831 x lit spread | **PASS** | ours 10.10 cm vs model-based lit 8.46-18.27 (median 12.15, n=3); ALL comparators 8.46-81.93 |
| Greenland | ssp585 | 2150 | median_vs_lit | 0.910 x lit median | **PASS** | ours 25.72 cm vs lit 24.11-32.40 (median 28.26), n_lit=2 [1 SEJ comparator(s) excluded from the score; full range 24.11-32.51] ⚠ n_lit=2 < 3: a median of so few is not a summary |
| Greenland | ssp585 | 2150 | median_vs_lit | 0.523 x lit median | **WARN** | BRICK 2.0 14.77 cm vs the same lit median 28.26; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp585 | 2150 | spread_vs_lit | 0.563 x lit spread | **PASS** | ours 30.80 cm vs model-based lit 18.48-90.97 (median 54.73, n=2); ALL comparators 18.48-113.11; ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| Greenland | ssp585 | 2300 | median_vs_lit | 0.969 x lit median | **PASS** | ours 83.67 cm vs lit 59.76-113.01 (median 86.38), n_lit=2 [1 SEJ comparator(s) excluded from the score; full range 59.76-113.01] ⚠ n_lit=2 < 3: a median of so few is not a summary |
| Greenland | ssp585 | 2300 | median_vs_lit | 0.447 x lit median | **WARN** | BRICK 2.0 38.60 cm vs the same lit median 86.38; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| Greenland | ssp585 | 2300 | spread_vs_lit | 0.298 x lit spread | **WARN** | ours 108.39 cm vs model-based lit 46.66-680.24 (median 363.45, n=2); ALL comparators 46.66-680.24; ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN |
| thermal exp. | ssp126 | 2100 | median_vs_lit | 1.154 x lit median | **PASS** | ours 16.09 cm vs lit 11.09-16.79 (median 13.94), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp126 | 2100 | median_vs_lit | 1.100 x lit median | **PASS** | BRICK 2.0 15.34 cm vs the same lit median 13.94; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp126 | 2100 | spread_vs_lit | 0.926 x lit spread | **PASS** | ours 12.10 cm vs model-based lit 11.97-14.17 (median 13.07, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp126 | 2150 | median_vs_lit | 1.186 x lit median | **PASS** | ours 19.96 cm vs lit 12.68-20.97 (median 16.83), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp126 | 2150 | median_vs_lit | 1.140 x lit median | **PASS** | BRICK 2.0 19.18 cm vs the same lit median 16.83; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp126 | 2150 | spread_vs_lit | 0.956 x lit spread | **PASS** | ours 17.16 cm vs model-based lit 16.06-19.84 (median 17.95, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp126 | 2300 | median_vs_lit | 1.180 x lit median | **PASS** | ours 25.68 cm vs lit 16.74-26.81 (median 21.77), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp126 | 2300 | median_vs_lit | 1.152 x lit median | **PASS** | BRICK 2.0 25.08 cm vs the same lit median 21.77; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp126 | 2300 | spread_vs_lit | 1.023 x lit spread | **PASS** | ours 29.15 cm vs model-based lit 25.47-31.53 (median 28.50, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp245 | 2100 | median_vs_lit | 1.073 x lit median | **PASS** | ours 20.28 cm vs lit 16.62-21.18 (median 18.90), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp245 | 2100 | median_vs_lit | 1.025 x lit median | **PASS** | BRICK 2.0 19.37 cm vs the same lit median 18.90; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp245 | 2100 | spread_vs_lit | 0.890 x lit spread | **PASS** | ours 14.14 cm vs model-based lit 15.26-16.52 (median 15.89, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp245 | 2150 | median_vs_lit | 1.097 x lit median | **PASS** | ours 29.64 cm vs lit 23.23-30.82 (median 27.03), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp245 | 2150 | median_vs_lit | 1.056 x lit median | **PASS** | BRICK 2.0 28.53 cm vs the same lit median 27.03; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp245 | 2150 | spread_vs_lit | 0.873 x lit spread | **PASS** | ours 23.68 cm vs model-based lit 25.87-28.40 (median 27.13, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp245 | 2300 | median_vs_lit | 1.097 x lit median | **PASS** | ours 45.81 cm vs lit 36.30-47.22 (median 41.76), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp245 | 2300 | median_vs_lit | 1.069 x lit median | **PASS** | BRICK 2.0 44.66 cm vs the same lit median 41.76; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp245 | 2300 | spread_vs_lit | 0.888 x lit spread | **PASS** | ours 47.78 cm vs model-based lit 53.37-54.25 (median 53.81, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp585 | 2100 | median_vs_lit | 0.993 x lit median | **PASS** | ours 28.38 cm vs lit 27.88-29.29 (median 28.59), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp585 | 2100 | median_vs_lit | 0.947 x lit median | **WARN** | BRICK 2.0 27.07 cm vs the same lit median 28.59; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp585 | 2100 | spread_vs_lit | 0.806 x lit spread | **PASS** | ours 18.35 cm vs model-based lit 22.64-22.88 (median 22.76, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp585 | 2150 | median_vs_lit | 1.010 x lit median | **PASS** | ours 52.53 cm vs lit 49.94-54.12 (median 52.03), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp585 | 2150 | median_vs_lit | 0.968 x lit median | **PASS** | BRICK 2.0 50.34 cm vs the same lit median 52.03; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp585 | 2150 | spread_vs_lit | 0.802 x lit spread | **PASS** | ours 37.92 cm vs model-based lit 46.46-48.08 (median 47.27, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| thermal exp. | ssp585 | 2300 | median_vs_lit | 0.986 x lit median | **PASS** | ours 104.98 cm vs lit 103.49-109.39 (median 106.44), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| thermal exp. | ssp585 | 2300 | median_vs_lit | 0.957 x lit median | **WARN** | BRICK 2.0 101.88 cm vs the same lit median 106.44; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| thermal exp. | ssp585 | 2300 | spread_vs_lit | 0.823 x lit spread | **PASS** | ours 98.73 cm vs model-based lit 118.64-121.40 (median 120.02, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary |
| land water | ssp126 | 2100 | median_vs_lit | 0.865 x lit median | **WARN** | ours 2.60 cm vs lit 2.99-3.01 (median 3.00), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp126 | 2100 | median_vs_lit | 0.781 x lit median | **WARN** | BRICK 2.0 2.34 cm vs the same lit median 3.00; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp126 | 2100 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 3.64-4.06 (median 3.85, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp126 | 2150 | median_vs_lit | 0.887 x lit median | **WARN** | ours 4.23 cm vs lit 4.58-4.96 (median 4.77), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp126 | 2150 | median_vs_lit | 0.847 x lit median | **WARN** | BRICK 2.0 4.04 cm vs the same lit median 4.77; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp126 | 2150 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 5.64-5.78 (median 5.71, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp126 | 2300 | median_vs_lit | 0.941 x lit median | **PASS** | ours 8.48 cm vs lit 7.25-10.78 (median 9.01), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| land water | ssp126 | 2300 | median_vs_lit | 0.987 x lit median | **PASS** | BRICK 2.0 8.90 cm vs the same lit median 9.01; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp126 | 2300 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 8.70-12.12 (median 10.41, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp245 | 2100 | median_vs_lit | 0.848 x lit median | **WARN** | ours 2.60 cm vs lit 3.01-3.11 (median 3.06), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp245 | 2100 | median_vs_lit | 0.765 x lit median | **WARN** | BRICK 2.0 2.34 cm vs the same lit median 3.06; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp245 | 2100 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 3.64-4.48 (median 4.06, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp245 | 2150 | median_vs_lit | 0.833 x lit median | **WARN** | ours 4.23 cm vs lit 4.96-5.20 (median 5.08), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp245 | 2150 | median_vs_lit | 0.796 x lit median | **WARN** | BRICK 2.0 4.04 cm vs the same lit median 5.08; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp245 | 2150 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 5.78-6.87 (median 6.33, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp245 | 2300 | median_vs_lit | 0.774 x lit median | **WARN** | ours 8.48 cm vs lit 10.78-11.14 (median 10.96), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp245 | 2300 | median_vs_lit | 0.812 x lit median | **WARN** | BRICK 2.0 8.90 cm vs the same lit median 10.96; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp245 | 2300 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 12.12-13.82 (median 12.97, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp585 | 2100 | median_vs_lit | 0.871 x lit median | **WARN** | ours 2.60 cm vs lit 2.96-3.01 (median 2.98), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp585 | 2100 | median_vs_lit | 0.786 x lit median | **WARN** | BRICK 2.0 2.34 cm vs the same lit median 2.98; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp585 | 2100 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 3.64-4.12 (median 3.88, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp585 | 2150 | median_vs_lit | 0.875 x lit median | **WARN** | ours 4.23 cm vs lit 4.70-4.96 (median 4.83), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary; verdict CAPPED at WARN |
| land water | ssp585 | 2150 | median_vs_lit | 0.836 x lit median | **WARN** | BRICK 2.0 4.04 cm vs the same lit median 4.83; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp585 | 2150 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 5.78-5.80 (median 5.79, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| land water | ssp585 | 2300 | median_vs_lit | 0.927 x lit median | **PASS** | ours 8.48 cm vs lit 7.53-10.78 (median 9.16), n_lit=2 ⚠ n_lit=2 < 3: a median of so few is not a summary |
| land water | ssp585 | 2300 | median_vs_lit | 0.972 x lit median | **PASS** | BRICK 2.0 8.90 cm vs the same lit median 9.16; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| land water | ssp585 | 2300 | spread_vs_lit | 0.000 x lit spread | **N/A(by construction)** | ours 0.00 cm vs model-based lit 9.04-12.12 (median 10.58, n=2); ⚠ n=2 < 3 comparators WITH A BAND, so this median is not a summary; verdict CAPPED at WARN; LWS is a seeded constant -- zero spread is the DESIGN, not a defect |
| TOTAL | ssp126 | 2100 | median_vs_lit | 0.841 x lit median | **PASS** | ours 38.40 cm vs lit 35.59-50.06 (median 45.68), n_lit=7 [1 SEJ comparator(s) excluded from the score; full range 35.59-55.88] |
| TOTAL | ssp126 | 2100 | median_vs_lit | 0.901 x lit median | **PASS** | BRICK 2.0 41.16 cm vs the same lit median 45.68; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp126 | 2100 | spread_vs_lit | 1.481 x lit spread | **PASS** | ours 68.62 cm vs model-based lit 32.73-55.62 (median 46.34, n=7); ALL comparators 32.73-125.52 |
| TOTAL | ssp126 | 2150 | median_vs_lit | 0.703 x lit median | **PASS** | ours 50.24 cm vs lit 45.94-83.52 (median 71.52), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 45.94-92.42] |
| TOTAL | ssp126 | 2150 | median_vs_lit | 0.809 x lit median | **PASS** | BRICK 2.0 57.89 cm vs the same lit median 71.52; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp126 | 2150 | spread_vs_lit | 1.658 x lit spread | **WARN** | ours 124.28 cm vs model-based lit 58.97-253.21 (median 74.95, n=4); ALL comparators 58.97-253.21; ⚠ THE COMPARATORS DO NOT AGREE -- scored one at a time they give 2xhigh/1xin/1xlow and the median's 'in' is not a majority, so the median is not a summary here; verdict CAPPED at WARN |
| TOTAL | ssp126 | 2300 | median_vs_lit | 0.538 x lit median | **PASS** | ours 72.58 cm vs lit 66.49-208.27 (median 134.81), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 66.49-208.27] |
| TOTAL | ssp126 | 2300 | median_vs_lit | 0.703 x lit median | **PASS** | BRICK 2.0 94.76 cm vs the same lit median 134.81; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp126 | 2300 | spread_vs_lit | 1.639 x lit spread | **WARN** | ours 282.19 cm vs model-based lit 116.60-949.74 (median 172.16, n=4); ALL comparators 116.60-949.74; ⚠ THE COMPARATORS DO NOT AGREE -- scored one at a time they give 1xhigh/2xin/1xlow and the median's 'in' is not a majority, so the median is not a summary here; verdict CAPPED at WARN |
| TOTAL | ssp245 | 2100 | median_vs_lit | 0.944 x lit median | **PASS** | ours 52.14 cm vs lit 49.78-58.27 (median 55.25), n_lit=7 [1 SEJ comparator(s) excluded from the score; full range 49.78-67.77] |
| TOTAL | ssp245 | 2100 | median_vs_lit | 1.270 x lit median | **WARN** | BRICK 2.0 70.19 cm vs the same lit median 55.25; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp245 | 2100 | spread_vs_lit | 1.462 x lit spread | **PASS** | ours 77.99 cm vs model-based lit 35.22-64.58 (median 53.36, n=7); ALL comparators 35.22-151.34 |
| TOTAL | ssp245 | 2150 | median_vs_lit | 1.067 x lit median | **PASS** | ours 100.53 cm vs lit 80.52-106.90 (median 94.25), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 80.52-111.40] |
| TOTAL | ssp245 | 2150 | median_vs_lit | 1.464 x lit median | **WARN** | BRICK 2.0 137.98 cm vs the same lit median 94.25; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp245 | 2150 | spread_vs_lit | 1.400 x lit spread | **WARN** | ours 153.45 cm vs model-based lit 66.28-338.40 (median 109.59, n=4); ALL comparators 66.28-338.40; ⚠ THE COMPARATORS DO NOT AGREE -- scored one at a time they give 1xhigh/2xin/1xlow and the median's 'in' is not a majority, so the median is not a summary here; verdict CAPPED at WARN |
| TOTAL | ssp245 | 2300 | median_vs_lit | 1.302 x lit median | **PASS** | ours 249.25 cm vs lit 170.82-269.43 (median 191.36), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 170.82-269.43] |
| TOTAL | ssp245 | 2300 | median_vs_lit | 1.661 x lit median | **WARN** | BRICK 2.0 317.82 cm vs the same lit median 191.36; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp245 | 2300 | spread_vs_lit | 1.306 x lit spread | **WARN** | ours 381.57 cm vs model-based lit 188.93-1328.01 (median 292.22, n=4); ALL comparators 188.93-1328.01; ⚠ THE COMPARATORS DO NOT AGREE -- scored one at a time they give 1xhigh/2xin/1xlow and the median's 'in' is not a majority, so the median is not a summary here; verdict CAPPED at WARN |
| TOTAL | ssp585 | 2100 | median_vs_lit | 1.251 x lit median | **PASS** | ours 94.21 cm vs lit 62.39-97.85 (median 75.33), n_lit=7 [1 SEJ comparator(s) excluded from the score; full range 62.39-97.85] |
| TOTAL | ssp585 | 2100 | median_vs_lit | 1.301 x lit median | **WARN** | BRICK 2.0 98.00 cm vs the same lit median 75.33; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp585 | 2100 | spread_vs_lit | 1.271 x lit spread | **PASS** | ours 87.52 cm vs model-based lit 40.46-106.79 (median 68.88, n=7); ALL comparators 40.46-181.04 |
| TOTAL | ssp585 | 2150 | median_vs_lit | 1.008 x lit median | **PASS** | ours 200.26 cm vs lit 114.05-262.93 (median 198.69), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 114.05-262.93] |
| TOTAL | ssp585 | 2150 | median_vs_lit | 0.982 x lit median | **PASS** | BRICK 2.0 195.15 cm vs the same lit median 198.69; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp585 | 2150 | spread_vs_lit | 0.558 x lit spread | **WARN** | ours 156.89 cm vs model-based lit 79.09-424.71 (median 281.29, n=4); ALL comparators 79.09-558.81; ⚠ THE COMPARATORS DO NOT AGREE -- scored one at a time they give 2xin/2xlow and the median's 'in' is not a majority, so the median is not a summary here; verdict CAPPED at WARN |
| TOTAL | ssp585 | 2300 | median_vs_lit | 0.835 x lit median | **PASS** | ours 516.71 cm vs lit 228.50-1015.98 (median 618.54), n_lit=4 [1 SEJ comparator(s) excluded from the score; full range 228.50-1015.98] |
| TOTAL | ssp585 | 2300 | median_vs_lit | 0.756 x lit median | **PASS** | BRICK 2.0 467.87 cm vs the same lit median 618.54; ⚠ FIXED-driver median, scored on medians only -- its parameter-only SPREAD is not comparable with our joint band |
| TOTAL | ssp585 | 2300 | spread_vs_lit | 0.480 x lit spread | **WARN** | ours 443.05 cm vs model-based lit 221.36-1441.45 (median 922.79, n=4); ALL comparators 221.36-1441.45; ⚠ THE COMPARATORS DO NOT AGREE -- scored one at a time they give 1xhigh/1xin/2xlow and the median's 'low' is not a majority, so the median is not a summary here; verdict CAPPED at WARN |

## [P] Levels — every arm side by side (cm)

| module | ssp | horizon | candidate (joint) | champion (joint) | BRICK 2.0 (fixed) |
|---|---|---|---|---|---|
| AIS | ssp126 | 2100 | 4.76 | (is champion) | 4.32 |
| AIS | ssp126 | 2150 | 7.33 | (is champion) | 6.52 |
| AIS | ssp126 | 2300 | 14.48 | (is champion) | 13.01 |
| AIS | ssp245 | 2100 | 7.72 | (is champion) | 27.41 |
| AIS | ssp245 | 2150 | 39.85 | (is champion) | 72.60 |
| AIS | ssp245 | 2300 | 154.29 | (is champion) | 205.94 |
| AIS | ssp585 | 2100 | 37.45 | (is champion) | 44.14 |
| AIS | ssp585 | 2150 | 95.70 | (is champion) | 97.88 |
| AIS | ssp585 | 2300 | 292.53 | (is champion) | 276.83 |
| glaciers | ssp126 | 2100 | 7.92 | (is champion) | 12.09 |
| glaciers | ssp126 | 2150 | 9.79 | (is champion) | 17.44 |
| glaciers | ssp126 | 2300 | 12.38 | (is champion) | 27.72 |
| glaciers | ssp245 | 2100 | 9.56 | (is champion) | 13.34 |
| glaciers | ssp245 | 2150 | 13.30 | (is champion) | 20.69 |
| glaciers | ssp245 | 2300 | 18.21 | (is champion) | 32.50 |
| glaciers | ssp585 | 2100 | 12.81 | (is champion) | 15.61 |
| glaciers | ssp585 | 2150 | 20.30 | (is champion) | 26.25 |
| glaciers | ssp585 | 2300 | 26.53 | (is champion) | 35.36 |
| Greenland | ssp126 | 2100 | 6.58 | (is champion) | 6.62 |
| Greenland | ssp126 | 2150 | 8.09 | (is champion) | 10.01 |
| Greenland | ssp126 | 2300 | 10.19 | (is champion) | 19.04 |
| Greenland | ssp245 | 2100 | 8.23 | (is champion) | 7.03 |
| Greenland | ssp245 | 2150 | 11.97 | (is champion) | 11.35 |
| Greenland | ssp245 | 2300 | 17.52 | (is champion) | 23.71 |
| Greenland | ssp585 | 2100 | 12.10 | (is champion) | 7.88 |
| Greenland | ssp585 | 2150 | 25.72 | (is champion) | 14.77 |
| Greenland | ssp585 | 2300 | 83.67 | (is champion) | 38.60 |
| thermal exp. | ssp126 | 2100 | 16.09 | (is champion) | 15.34 |
| thermal exp. | ssp126 | 2150 | 19.96 | (is champion) | 19.18 |
| thermal exp. | ssp126 | 2300 | 25.68 | (is champion) | 25.08 |
| thermal exp. | ssp245 | 2100 | 20.28 | (is champion) | 19.37 |
| thermal exp. | ssp245 | 2150 | 29.64 | (is champion) | 28.53 |
| thermal exp. | ssp245 | 2300 | 45.81 | (is champion) | 44.66 |
| thermal exp. | ssp585 | 2100 | 28.38 | (is champion) | 27.07 |
| thermal exp. | ssp585 | 2150 | 52.53 | (is champion) | 50.34 |
| thermal exp. | ssp585 | 2300 | 104.98 | (is champion) | 101.88 |
| land water | ssp126 | 2100 | 2.60 | (is champion) | 2.34 |
| land water | ssp126 | 2150 | 4.23 | (is champion) | 4.04 |
| land water | ssp126 | 2300 | 8.48 | (is champion) | 8.90 |
| land water | ssp245 | 2100 | 2.60 | (is champion) | 2.34 |
| land water | ssp245 | 2150 | 4.23 | (is champion) | 4.04 |
| land water | ssp245 | 2300 | 8.48 | (is champion) | 8.90 |
| land water | ssp585 | 2100 | 2.60 | (is champion) | 2.34 |
| land water | ssp585 | 2150 | 4.23 | (is champion) | 4.04 |
| land water | ssp585 | 2300 | 8.48 | (is champion) | 8.90 |
| TOTAL | ssp126 | 2100 | 38.40 | (is champion) | 41.16 |
| TOTAL | ssp126 | 2150 | 50.24 | (is champion) | 57.89 |
| TOTAL | ssp126 | 2300 | 72.58 | (is champion) | 94.76 |
| TOTAL | ssp245 | 2100 | 52.14 | (is champion) | 70.19 |
| TOTAL | ssp245 | 2150 | 100.53 | (is champion) | 137.98 |
| TOTAL | ssp245 | 2300 | 249.25 | (is champion) | 317.82 |
| TOTAL | ssp585 | 2100 | 94.21 | (is champion) | 98.00 |
| TOTAL | ssp585 | 2150 | 200.26 | (is champion) | 195.15 |
| TOTAL | ssp585 | 2300 | 516.71 | (is champion) | 467.87 |

## [S] Scenario separation — ssp585/ssp126 median ratio

| module | horizon | ours | verdict | literature |
|---|---|---|---|---|
| AIS | 2100 | 7.86x | **PASS** | FACTS 0.73-2.10 (n=5); MAGICC-SLR 10.69-10.69 (n=1) |
| AIS | 2150 | 13.06x | **PASS** | FACTS 0.55-4.64 (n=4); MAGICC-SLR 28.79-28.79 (n=1) |
| AIS | 2300 | 20.21x | **PASS** | FACTS 0.47-5.38 (n=4); MAGICC-SLR 81.77-81.77 (n=1) |
| glaciers | 2100 | 1.62x | **PASS** | FACTS 1.43-1.65 (n=2); MAGICC-SLR 1.46-1.46 (n=1) |
| glaciers | 2150 | 2.07x | **CHECK(wide)** | FACTS 1.93-1.93 (n=1); MAGICC-SLR 1.79-1.79 (n=1); 0.14 outside the bracket = 109% of its own range |
| glaciers | 2300 | 2.14x | **PASS(edge)** | FACTS 1.38-1.38 (n=1); MAGICC-SLR 2.11-2.11 (n=1); 0.03 outside the bracket = 5% of its own range |
| Greenland | 2100 | 1.84x | **PASS** | FACTS 1.24-1.84 (n=3); MAGICC-SLR 2.11-2.11 (n=1) |
| Greenland | 2150 | 3.18x | **PASS** | FACTS 1.33-1.68 (n=2); MAGICC-SLR 3.48-3.48 (n=1) |
| Greenland | 2300 | 8.21x | **PASS(edge)** | FACTS 1.27-1.84 (n=2); MAGICC-SLR 7.54-7.54 (n=1); 0.67 outside the bracket = 11% of its own range |
| thermal exp. | 2100 | 1.76x | **PASS** | FACTS 1.74-1.74 (n=1); MAGICC-SLR 2.51-2.51 (n=1) |
| thermal exp. | 2150 | 2.63x | **PASS** | FACTS 2.58-2.58 (n=1); MAGICC-SLR 3.94-3.94 (n=1) |
| thermal exp. | 2300 | 4.09x | **PASS** | FACTS 4.08-4.08 (n=1); MAGICC-SLR 6.18-6.18 (n=1) |
| land water | 2100 | 1.00x | **PASS** | FACTS 0.99-0.99 (n=1); MAGICC-SLR 1.00-1.00 (n=1) |
| land water | 2150 | 1.00x | **PASS** | FACTS 1.03-1.03 (n=1); MAGICC-SLR 1.00-1.00 (n=1) |
| land water | 2300 | 1.00x | **PASS** | FACTS 1.04-1.04 (n=1); MAGICC-SLR 1.00-1.00 (n=1) |
| TOTAL | 2100 | 2.45x | **PASS** | FACTS 1.44-1.82 (n=7); MAGICC-SLR 2.75-2.75 (n=1) |
| TOTAL | 2150 | 3.99x | **PASS** | FACTS 1.65-3.00 (n=4); MAGICC-SLR 5.72-5.72 (n=1) |
| TOTAL | 2300 | 7.12x | **PASS** | FACTS 1.66-4.30 (n=4); MAGICC-SLR 15.28-15.28 (n=1) |

---

*Machine-readable: `outputs/bench_ladrillo_L24.csv`. Regenerate: `python python/bench_ladrillo.py --tag=L24`.*
