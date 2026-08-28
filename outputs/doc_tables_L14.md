# Comparison tables — Ladrillo L14

Basis: **cm, re-referenced to 1995-2014**. Commit `a2d9b41`.

> ⚠ **Ladrillo and BRICK 2.0 run on MEAN forcing -> bands are posterior-parameter spread only; MAGICC/FACTS bands also carry climate uncertainty. MEDIANS comparable, WIDTHS not.**

> **AR6 T9.9** = IPCC AR6 WG1 Ch9 Table 9.9 (Fox-Kemper 2021 p.1302), median and *likely* (17–83%) range, medium confidence — the **assessed IPCC number itself**, not a FACTS workflow standing in for one. **2150 is totals only; there is no AR6 2300 row.**

> **FACTS workflows, identified from the data** (not from the AR6 taxonomy): `wf1f` = ar5AIS + FittedISMIP; `wf2f` = larmip + FittedISMIP (**no MICI, no expert elicitation** — the pure process workflow); `wf3f` = deconto21/**MICI** + FittedISMIP; `wf4` = **bamber19 in both ice sheets = the structured-expert-judgement envelope**. `FACTS range` = min–max across the six model-class workflow medians.

> ⚠ **Coverage.** FACTS stops at **2150**. AR6 has no **2300**. MAGICC-SLR and BRICK 2.0 run to **2300**. Blanks are *absence of data*, not zero.

> ✅ **BRICK 2.0 now has proper 17–83% bands for every component.** Earlier versions showed it only for glaciers at 5–95%, because `ladrillo_model_comparison.py:62` reads the superseded glacier-only `ssps_gsic_2300.csv`. These tables read `outputs/ssps_components_2300_oldbrick.csv` (all six components to 2300, p17/p83), which `project_ssps_components_oldbrick.jl` was written to produce for exactly this reason. **No BRICK 2.0 re-run was needed.**

## Total GMSL

| scenario | horizon | Ladrillo | AR6 T9.9 | FACTS wf1f | FACTS wf2f | FACTS wf3f | FACTS wf4 | FACTS range | MAGICC-SLR | BRICK 2.0 |
|---|---|---|---|---|---|---|---|---|---|---|
| ssp126 | 2100 | 35.1 [33.7, 36.5] | 44.0 [32.0, 62.0] | 39.8 [31.1, 48.5] | 46.1 [37.0, 61.3] | 43.1 [37.0, 50.0] | 53.5 [35.5, 83.9] | 42.2 [39.8, 46.1] | 35.6 [27.4, 48.9] | 39.2 [35.7, 44.2] |
| ssp126 | 2150 | 45.8 [44.0, 47.6] | 68.0 [46.0, 99.0] | 60.2 [43.5, 77.6] | 72.0 [55.1, 97.5] | 74.9 [60.4, 96.6] | 83.1 [52.5, 144.2] | 72.0 [60.2, 74.9] | 45.9 [34.0, 66.9] | 55.2 [50.3, 62.1] |
| ssp126 | 2300 | 67.1 [64.3, 70.0] | — | — | — | — | — | — | 66.5 [47.0, 106.5] | 91.2 [82.3, 102.0] |
| ssp245 | 2100 | 44.9 [42.7, 59.0] | 56.0 [44.0, 76.0] | 48.7 [39.0, 58.1] | 56.9 [46.0, 75.2] | 55.1 [46.8, 81.2] | 67.9 [45.2, 120.2] | 54.3 [48.7, 57.1] | 53.2 [40.6, 70.4] | 70.9 [49.7, 92.9] |
| ssp245 | 2150 | 70.7 [64.7, 127.7] | 92.0 [66.0, 133.0] | 80.0 [61.9, 99.3] | 98.1 [79.9, 134.6] | 105.2 [83.1, 300.4] | 111.2 [71.9, 207.7] | 98.1 [80.0, 105.2] | 88.1 [64.6, 125.3] | 138.0 [107.6, 173.7] |
| ssp245 | 2300 | 219.1 [107.8, 323.0] | — | — | — | — | — | — | 186.8 [118.0, 305.9] | 317.5 [253.9, 405.5] |
| ssp585 | 2100 | 94.7 [81.5, 110.7] | 77.0 [63.0, 101.0] | 64.9 [54.4, 77.2] | 76.6 [63.6, 101.8] | 91.9 [70.6, 114.9] | 90.8 [60.7, 160.2] | 78.0 [64.9, 91.9] | 97.8 [74.8, 132.3] | 104.7 [88.1, 124.9] |
| ssp585 | 2150 | 201.1 [175.2, 231.1] | 132.0 [98.0, 188.0] | 117.1 [96.7, 141.5] | 151.7 [123.6, 208.4] | 310.7 [193.8, 476.6] | 162.3 [113.3, 306.4] | 151.7 [117.1, 310.7] | 262.9 [189.7, 387.8] | 202.8 [169.1, 243.0] |
| ssp585 | 2300 | 513.7 [443.3, 592.8] | — | — | — | — | — | — | 1016.0 [691.1, 1585.3] | 482.4 [386.8, 592.5] |

Brackets: **17–83%** for Ladrillo, AR6 T9.9, each FACTS workflow, MAGICC-SLR and BRICK 2.0. `FACTS range` bracket is **min–max across workflow medians** — a between-workflow spread, not a probabilistic band.

## Antarctica

| scenario | horizon | Ladrillo | AR6 T9.9 | FACTS wf1f | FACTS wf2f | FACTS wf3f | FACTS wf4 | FACTS range | MAGICC-SLR | BRICK 2.0 |
|---|---|---|---|---|---|---|---|---|---|---|
| ssp126 | 2100 | 4.4 [3.8, 5.0] | 11.0 [3.0, 27.0] | — | — | — | — | 9.2 [6.3, 11.9] | 3.7 [-0.2, 13.1] | 4.2 [2.2, 7.0] |
| ssp126 | 2150 | 6.8 [5.7, 7.8] | — | — | — | — | — | 22.7 [13.2, 26.3] | 5.3 [-0.3, 19.5] | 6.4 [3.2, 10.6] |
| ssp126 | 2300 | 13.5 [11.4, 15.5] | — | — | — | — | — | — | 8.7 [-1.2, 35.6] | 12.6 [6.5, 20.9] |
| ssp245 | 2100 | 5.6 [4.4, 20.1] | 11.0 [3.0, 29.0] | — | — | — | — | 9.7 [5.5, 12.7] | 11.2 [3.2, 23.9] | 29.2 [8.0, 50.8] |
| ssp245 | 2150 | 11.9 [8.0, 70.0] | — | — | — | — | — | 27.7 [10.9, 30.3] | 27.2 [9.4, 54.4] | 74.5 [44.6, 110.0] |
| ssp245 | 2300 | 131.3 [20.2, 233.9] | — | — | — | — | — | — | 83.5 [30.5, 172.9] | 207.9 [144.7, 295.2] |
| ssp585 | 2100 | 37.1 [24.1, 53.3] | 12.0 [3.0, 34.0] | — | — | — | — | 11.8 [4.0, 28.6] | 39.1 [22.1, 65.9] | 49.0 [34.2, 69.3] |
| ssp585 | 2150 | 94.4 [69.0, 124.3] | — | — | — | — | — | 37.4 [6.3, 198.8] | 153.6 [96.1, 241.3] | 104.1 [73.4, 142.9] |
| ssp585 | 2300 | 281.7 [212.0, 359.9] | — | — | — | — | — | — | 712.0 [470.0, 1005.1] | 290.2 [197.3, 400.8] |

Brackets: **17–83%** for Ladrillo, AR6 T9.9, each FACTS workflow, MAGICC-SLR and BRICK 2.0. `FACTS range` bracket is **min–max across workflow medians** — a between-workflow spread, not a probabilistic band.

## Greenland

| scenario | horizon | Ladrillo | AR6 T9.9 | FACTS wf1f | FACTS wf2f | FACTS wf3f | FACTS wf4 | FACTS range | MAGICC-SLR | BRICK 2.0 |
|---|---|---|---|---|---|---|---|---|---|---|
| ssp126 | 2100 | 6.5 [6.1, 6.9] | 6.0 [1.0, 10.0] | — | — | — | — | 6.6 [5.5, 7.7] | 6.4 [4.5, 8.7] | 6.6 [5.5, 8.1] |
| ssp126 | 2150 | 7.9 [7.3, 8.6] | — | — | — | — | — | 13.2 [13.2, 13.2] | 9.3 [6.5, 13.0] | 9.9 [8.2, 12.2] |
| ssp126 | 2300 | 10.1 [9.0, 11.4] | — | — | — | — | — | — | 15.0 [9.8, 20.8] | 18.8 [15.7, 23.1] |
| ssp245 | 2100 | 8.5 [7.8, 9.1] | 8.0 [4.0, 13.0] | — | — | — | — | 9.1 [8.0, 10.2] | 9.3 [7.1, 12.2] | 7.1 [5.7, 9.0] |
| ssp245 | 2150 | 12.4 [11.3, 13.7] | — | — | — | — | — | 18.2 [18.2, 18.2] | 16.5 [11.5, 20.7] | 11.4 [9.0, 14.9] |
| ssp245 | 2300 | 18.3 [16.2, 21.0] | — | — | — | — | — | — | 35.8 [21.1, 44.8] | 23.8 [18.2, 32.0] |
| ssp585 | 2100 | 13.9 [12.3, 15.5] | 13.0 [9.0, 18.0] | — | — | — | — | 13.4 [12.7, 14.0] | 13.5 [10.7, 17.2] | 8.2 [6.2, 11.1] |
| ssp585 | 2150 | 30.6 [27.0, 34.3] | — | — | — | — | — | 27.3 [27.3, 27.3] | 32.4 [23.9, 49.5] | 15.6 [10.8, 22.5] |
| ssp585 | 2300 | 95.7 [88.5, 104.3] | — | — | — | — | — | — | 113.0 [79.8, 369.7] | 40.4 [25.2, 62.9] |

Brackets: **17–83%** for Ladrillo, AR6 T9.9, each FACTS workflow, MAGICC-SLR and BRICK 2.0. `FACTS range` bracket is **min–max across workflow medians** — a between-workflow spread, not a probabilistic band.

## Glaciers

| scenario | horizon | Ladrillo | AR6 T9.9 | FACTS wf1f | FACTS wf2f | FACTS wf3f | FACTS wf4 | FACTS range | MAGICC-SLR | BRICK 2.0 |
|---|---|---|---|---|---|---|---|---|---|---|
| ssp126 | 2100 | 7.9 [6.9, 9.1] | 9.0 [7.0, 11.0] | — | — | — | — | 9.1 [8.9, 9.2] | 10.4 [8.4, 12.4] | 12.0 [11.1, 13.1] |
| ssp126 | 2150 | 9.7 [8.5, 11.1] | — | — | — | — | — | 12.0 [12.0, 12.0] | 12.3 [9.9, 14.8] | 17.2 [15.7, 18.8] |
| ssp126 | 2300 | 12.4 [10.8, 14.1] | — | — | — | — | — | — | 13.8 [11.1, 17.1] | 27.3 [23.7, 30.8] |
| ssp245 | 2100 | 10.0 [8.7, 11.3] | 12.0 [10.0, 15.0] | — | — | — | — | 11.8 [11.4, 12.2] | 12.5 [10.3, 14.4] | 13.5 [12.4, 14.7] |
| ssp245 | 2150 | 14.0 [12.3, 15.7] | — | — | — | — | — | 17.5 [17.5, 17.5] | 16.7 [14.0, 19.1] | 20.8 [18.6, 23.0] |
| ssp245 | 2300 | 19.1 [16.8, 21.3] | — | — | — | — | — | — | 21.5 [18.2, 24.4] | 32.4 [26.7, 37.7] |
| ssp585 | 2100 | 14.3 [12.6, 16.0] | 18.0 [15.0, 21.0] | — | — | — | — | 16.6 [15.5, 17.7] | 15.3 [13.0, 17.0] | 16.5 [15.1, 18.0] |
| ssp585 | 2150 | 22.0 [19.4, 24.3] | — | — | — | — | — | 28.4 [28.4, 28.4] | 22.0 [19.2, 24.0] | 27.1 [23.7, 30.6] |
| ssp585 | 2300 | 27.6 [24.5, 30.7] | — | — | — | — | — | — | 29.1 [26.0, 31.4] | 35.2 [27.5, 42.9] |

Brackets: **17–83%** for Ladrillo, AR6 T9.9, each FACTS workflow, MAGICC-SLR and BRICK 2.0. `FACTS range` bracket is **min–max across workflow medians** — a between-workflow spread, not a probabilistic band.

## Thermal expansion

| scenario | horizon | Ladrillo | AR6 T9.9 | FACTS wf1f | FACTS wf2f | FACTS wf3f | FACTS wf4 | FACTS range | MAGICC-SLR | BRICK 2.0 |
|---|---|---|---|---|---|---|---|---|---|---|
| ssp126 | 2100 | 13.7 [13.1, 14.2] | 14.0 [11.0, 18.0] | — | — | — | — | 14.1 [14.1, 14.1] | 11.1 [8.2, 14.9] | 13.8 [11.4, 16.0] |
| ssp126 | 2150 | 17.1 [16.4, 17.8] | — | — | — | — | — | 17.8 [17.8, 17.8] | 12.7 [9.0, 18.2] | 17.2 [14.3, 20.0] |
| ssp126 | 2300 | 22.7 [21.7, 23.6] | — | — | — | — | — | — | 16.7 [11.6, 25.6] | 22.8 [18.9, 26.5] |
| ssp245 | 2100 | 17.9 [17.1, 18.6] | 20.0 [16.0, 24.0] | — | — | — | — | 18.8 [18.8, 18.8] | 16.6 [12.9, 21.4] | 18.0 [15.0, 21.0] |
| ssp245 | 2150 | 26.6 [25.4, 27.6] | — | — | — | — | — | 28.6 [28.6, 28.6] | 23.2 [17.3, 31.6] | 26.7 [22.1, 31.0] |
| ssp245 | 2300 | 41.9 [40.0, 43.4] | — | — | — | — | — | — | 36.3 [26.0, 55.1] | 42.0 [34.9, 48.9] |
| ssp585 | 2100 | 26.9 [25.7, 27.9] | 30.0 [24.0, 36.0] | — | — | — | — | 28.8 [28.8, 28.8] | 27.9 [22.1, 35.7] | 27.0 [22.5, 31.4] |
| ssp585 | 2150 | 49.7 [47.5, 51.6] | — | — | — | — | — | 53.3 [53.3, 53.3] | 49.9 [38.3, 66.4] | 49.9 [41.5, 58.1] |
| ssp585 | 2300 | 99.7 [95.3, 103.5] | — | — | — | — | — | — | 103.5 [74.4, 142.9] | 100.2 [83.2, 116.5] |

Brackets: **17–83%** for Ladrillo, AR6 T9.9, each FACTS workflow, MAGICC-SLR and BRICK 2.0. `FACTS range` bracket is **min–max across workflow medians** — a between-workflow spread, not a probabilistic band.

## Land water storage

| scenario | horizon | Ladrillo | AR6 T9.9 | FACTS wf1f | FACTS wf2f | FACTS wf3f | FACTS wf4 | FACTS range | MAGICC-SLR | BRICK 2.0 |
|---|---|---|---|---|---|---|---|---|---|---|
| ssp126 | 2100 | 2.6 [2.6, 2.6] | 3.0 [1.0, 4.0] | — | — | — | — | 3.0 [3.0, 3.0] | 3.0 [1.7, 4.4] | 2.3 [2.3, 2.3] |
| ssp126 | 2150 | 4.2 [4.2, 4.2] | — | — | — | — | — | 4.6 [4.6, 4.6] | 5.0 [2.9, 7.2] | 4.0 [4.0, 4.0] |
| ssp126 | 2300 | 8.5 [8.5, 8.5] | — | — | — | — | — | — | 10.8 [6.5, 15.5] | 8.9 [8.9, 8.9] |
| ssp245 | 2100 | 2.6 [2.6, 2.6] | 3.0 [1.0, 4.0] | — | — | — | — | 3.1 [3.1, 3.1] | 3.0 [1.7, 4.4] | 2.3 [2.3, 2.3] |
| ssp245 | 2150 | 4.2 [4.2, 4.2] | — | — | — | — | — | 5.2 [5.2, 5.2] | 5.0 [2.9, 7.2] | 4.0 [4.0, 4.0] |
| ssp245 | 2300 | 8.5 [8.5, 8.5] | — | — | — | — | — | — | 10.8 [6.5, 15.5] | 8.9 [8.9, 8.9] |
| ssp585 | 2100 | 2.6 [2.6, 2.6] | 3.0 [1.0, 4.0] | — | — | — | — | 3.0 [3.0, 3.0] | 3.0 [1.7, 4.4] | 2.3 [2.3, 2.3] |
| ssp585 | 2150 | 4.2 [4.2, 4.2] | — | — | — | — | — | 4.7 [4.7, 4.7] | 5.0 [2.9, 7.2] | 4.0 [4.0, 4.0] |
| ssp585 | 2300 | 8.5 [8.5, 8.5] | — | — | — | — | — | — | 10.8 [6.5, 15.5] | 8.9 [8.9, 8.9] |

Brackets: **17–83%** for Ladrillo, AR6 T9.9, each FACTS workflow, MAGICC-SLR and BRICK 2.0. `FACTS range` bracket is **min–max across workflow medians** — a between-workflow spread, not a probabilistic band.
