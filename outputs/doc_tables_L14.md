# Comparison tables — Ladrillo L14

Basis: **cm, re-referenced to 1995-2014**. Commit `bfc65ae`. Frozen inputs hashed in `benchmark/reference/_fixed/manifest.json`.

> ⚠ **Ladrillo and BRICK 2.0 run on MEAN forcing -> bands are posterior-parameter spread only; MAGICC/FACTS bands also carry climate uncertainty. MEDIANS comparable, WIDTHS not.**

> ⚠ **Coverage is not uniform, and blanks mean *no data*, not zero.** FACTS stops at **2150**. MAGICC-SLR runs to **2300** (the comparison script's docstring saying it ends at 2100 is stale — verified against the file). **BRICK 2.0 appears only for glaciers**: in this comparison it is the legacy glacier-only arm, so it is absent from every other component by scope, not by omission.

> ⚠ **FACTS is seven AR6 workflows, not one number.** The FACTS column is the **median of its 6 model-class workflows**, with the **min–max across them** in brackets — a between-workflow spread, NOT a probabilistic band. `wf4` is structured expert judgement (bamber19 in both ice sheets) and is reported on its own row, per `benchmark/comparator_classes.csv` and the house rule that SEJ envelopes are not scored against a calibrated model.

## Total GMSL

| scenario | horizon | Ladrillo | FACTS | FACTS-SEJ | MAGICC-SLR | BRICK 2.0 |
|---|---|---|---|---|---|---|
| ssp126 | 2100 | 35.1 [33.7, 36.5] | 42.2 [39.8, 46.1] | 53.5 [35.5, 83.9] | 35.6 [27.4, 48.9] | — |
| ssp126 | 2150 | 45.8 [44.0, 47.6] | 72.0 [60.2, 74.9] | 83.1 [52.5, 144.2] | 45.9 [34.0, 66.9] | — |
| ssp126 | 2300 | 67.1 [64.3, 70.0] | — | — | 66.5 [47.0, 106.5] | — |
| ssp245 | 2100 | 44.9 [42.7, 59.0] | 54.3 [48.7, 57.1] | 67.9 [45.2, 120.2] | 53.2 [40.6, 70.4] | — |
| ssp245 | 2150 | 70.7 [64.7, 127.7] | 98.1 [80.0, 105.2] | 111.2 [71.9, 207.7] | 88.1 [64.6, 125.3] | — |
| ssp245 | 2300 | 219.1 [107.8, 323.0] | — | — | 186.8 [118.0, 305.9] | — |
| ssp585 | 2100 | 94.7 [81.5, 110.7] | 78.0 [64.9, 91.9] | 90.8 [60.7, 160.2] | 97.8 [74.8, 132.3] | — |
| ssp585 | 2150 | 201.1 [175.2, 231.1] | 151.7 [117.1, 310.7] | 162.3 [113.3, 306.4] | 262.9 [189.7, 387.8] | — |
| ssp585 | 2300 | 513.7 [443.3, 592.8] | — | — | 1016.0 [691.1, 1585.3] | — |

Brackets: Ladrillo / MAGICC-SLR = **17–83%**; FACTS = **min–max across its 6 model-class workflows** (a between-workflow spread, not a probabilistic band); FACTS-SEJ = wf4, median of its 17–83%; **BRICK 2.0 = 5–95%**, because this comparison file carries no p17/p83 for it — a WIDER interval than the others, so do not read its bracket as comparable.

## Antarctica

| scenario | horizon | Ladrillo | FACTS | FACTS-SEJ | MAGICC-SLR | BRICK 2.0 |
|---|---|---|---|---|---|---|
| ssp126 | 2100 | 4.4 [3.8, 5.0] | 9.2 [6.3, 11.9] | 9.1 [-0.1, 35.3] | 3.7 [-0.2, 13.1] | — |
| ssp126 | 2150 | 6.8 [5.7, 7.8] | 22.7 [13.2, 26.3] | 19.2 [-1.1, 61.2] | 5.3 [-0.3, 19.5] | — |
| ssp126 | 2300 | 13.5 [11.4, 15.5] | — | — | 8.7 [-1.2, 35.6] | — |
| ssp245 | 2100 | 5.6 [4.4, 20.1] | 9.7 [5.5, 12.7] | 13.7 [-0.2, 49.9] | 11.2 [3.2, 23.9] | — |
| ssp245 | 2150 | 11.9 [8.0, 70.0] | 27.7 [10.9, 30.3] | 25.2 [2.3, 84.8] | 27.2 [9.4, 54.4] | — |
| ssp245 | 2300 | 131.3 [20.2, 233.9] | — | — | 83.5 [30.5, 172.9] | — |
| ssp585 | 2100 | 37.1 [24.1, 53.3] | 11.8 [4.0, 28.6] | 18.0 [-0.2, 60.3] | 39.1 [22.1, 65.9] | — |
| ssp585 | 2150 | 94.4 [69.0, 124.3] | 37.4 [6.3, 198.8] | 36.5 [-1.1, 139.7] | 153.6 [96.1, 241.3] | — |
| ssp585 | 2300 | 281.7 [212.0, 359.9] | — | — | 712.0 [470.0, 1005.1] | — |

Brackets: Ladrillo / MAGICC-SLR = **17–83%**; FACTS = **min–max across its 6 model-class workflows** (a between-workflow spread, not a probabilistic band); FACTS-SEJ = wf4, median of its 17–83%; **BRICK 2.0 = 5–95%**, because this comparison file carries no p17/p83 for it — a WIDER interval than the others, so do not read its bracket as comparable.

## Greenland

| scenario | horizon | Ladrillo | FACTS | FACTS-SEJ | MAGICC-SLR | BRICK 2.0 |
|---|---|---|---|---|---|---|
| ssp126 | 2100 | 6.5 [6.1, 6.9] | 6.6 [5.5, 7.7] | 13.0 [7.1, 25.8] | 6.4 [4.5, 8.7] | — |
| ssp126 | 2150 | 7.9 [7.3, 8.6] | 13.2 [13.2, 13.2] | 22.2 [12.2, 62.9] | 9.3 [6.5, 13.0] | — |
| ssp126 | 2300 | 10.1 [9.0, 11.4] | — | — | 15.0 [9.8, 20.8] | — |
| ssp245 | 2100 | 8.5 [7.8, 9.1] | 9.1 [8.0, 10.2] | 14.4 [6.8, 38.8] | 9.3 [7.1, 12.2] | — |
| ssp245 | 2150 | 12.4 [11.3, 13.7] | 18.2 [18.2, 18.2] | 25.6 [12.6, 67.1] | 16.5 [11.5, 20.7] | — |
| ssp245 | 2300 | 18.3 [16.2, 21.0] | — | — | 35.8 [21.1, 44.8] | — |
| ssp585 | 2100 | 13.9 [12.3, 15.5] | 13.4 [12.7, 14.0] | 20.3 [8.3, 49.8] | 13.5 [10.7, 17.2] | — |
| ssp585 | 2150 | 30.6 [27.0, 34.3] | 27.3 [27.3, 27.3] | 38.1 [15.1, 78.8] | 32.4 [23.9, 49.5] | — |
| ssp585 | 2300 | 95.7 [88.5, 104.3] | — | — | 113.0 [79.8, 369.7] | — |

Brackets: Ladrillo / MAGICC-SLR = **17–83%**; FACTS = **min–max across its 6 model-class workflows** (a between-workflow spread, not a probabilistic band); FACTS-SEJ = wf4, median of its 17–83%; **BRICK 2.0 = 5–95%**, because this comparison file carries no p17/p83 for it — a WIDER interval than the others, so do not read its bracket as comparable.

## Glaciers

| scenario | horizon | Ladrillo | FACTS | FACTS-SEJ | MAGICC-SLR | BRICK 2.0 |
|---|---|---|---|---|---|---|
| ssp126 | 2100 | 7.9 [6.9, 9.1] | 9.1 [8.9, 9.2] | — | 10.4 [8.4, 12.4] | 12.0 [10.5, 14.0] |
| ssp126 | 2150 | 9.7 [8.5, 11.1] | 12.0 [12.0, 12.0] | — | 12.3 [9.9, 14.8] | 17.2 [14.6, 20.1] |
| ssp126 | 2300 | 12.4 [10.8, 14.1] | — | — | 13.8 [11.1, 17.1] | 27.3 [21.0, 33.1] |
| ssp245 | 2100 | 10.0 [8.7, 11.3] | 11.8 [11.4, 12.2] | — | 12.5 [10.3, 14.4] | 13.5 [11.7, 15.7] |
| ssp245 | 2150 | 14.0 [12.3, 15.7] | 17.5 [17.5, 17.5] | — | 16.7 [14.0, 19.1] | 20.8 [17.1, 24.5] |
| ssp245 | 2300 | 19.1 [16.8, 21.3] | — | — | 21.5 [18.2, 24.4] | 32.4 [23.0, 40.9] |
| ssp585 | 2100 | 14.3 [12.6, 16.0] | 16.6 [15.5, 17.7] | — | 15.3 [13.0, 17.0] | 16.5 [14.0, 19.3] |
| ssp585 | 2150 | 22.0 [19.4, 24.3] | 28.4 [28.4, 28.4] | — | 22.0 [19.2, 24.0] | 27.1 [20.9, 32.9] |
| ssp585 | 2300 | 27.6 [24.5, 30.7] | — | — | 29.1 [26.0, 31.4] | 35.2 [23.4, 47.1] |

Brackets: Ladrillo / MAGICC-SLR = **17–83%**; FACTS = **min–max across its 6 model-class workflows** (a between-workflow spread, not a probabilistic band); FACTS-SEJ = wf4, median of its 17–83%; **BRICK 2.0 = 5–95%**, because this comparison file carries no p17/p83 for it — a WIDER interval than the others, so do not read its bracket as comparable.

## Thermal expansion

| scenario | horizon | Ladrillo | FACTS | FACTS-SEJ | MAGICC-SLR | BRICK 2.0 |
|---|---|---|---|---|---|---|
| ssp126 | 2100 | 13.7 [13.1, 14.2] | 14.1 [14.1, 14.1] | — | 11.1 [8.2, 14.9] | — |
| ssp126 | 2150 | 17.1 [16.4, 17.8] | 17.8 [17.8, 17.8] | — | 12.7 [9.0, 18.2] | — |
| ssp126 | 2300 | 22.7 [21.7, 23.6] | — | — | 16.7 [11.6, 25.6] | — |
| ssp245 | 2100 | 17.9 [17.1, 18.6] | 18.8 [18.8, 18.8] | — | 16.6 [12.9, 21.4] | — |
| ssp245 | 2150 | 26.6 [25.4, 27.6] | 28.6 [28.6, 28.6] | — | 23.2 [17.3, 31.6] | — |
| ssp245 | 2300 | 41.9 [40.0, 43.4] | — | — | 36.3 [26.0, 55.1] | — |
| ssp585 | 2100 | 26.9 [25.7, 27.9] | 28.8 [28.8, 28.8] | — | 27.9 [22.1, 35.7] | — |
| ssp585 | 2150 | 49.7 [47.5, 51.6] | 53.3 [53.3, 53.3] | — | 49.9 [38.3, 66.4] | — |
| ssp585 | 2300 | 99.7 [95.3, 103.5] | — | — | 103.5 [74.4, 142.9] | — |

Brackets: Ladrillo / MAGICC-SLR = **17–83%**; FACTS = **min–max across its 6 model-class workflows** (a between-workflow spread, not a probabilistic band); FACTS-SEJ = wf4, median of its 17–83%; **BRICK 2.0 = 5–95%**, because this comparison file carries no p17/p83 for it — a WIDER interval than the others, so do not read its bracket as comparable.
