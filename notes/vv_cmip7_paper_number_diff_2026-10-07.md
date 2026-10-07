# GMD draft: van Vuuren numbers after the CMIP7-basis rerun (2026-10-07)

**For Marcus. The docx was NOT edited**: Tony holds the review copy. The text was read from
`deliverables/GMD.Ladrillo.v1_forTonyreview_TW1.docx` (Tony's return, 10-07 14:22) with pandoc and tracked changes
accepted.

- **Basis:** old = Smith-2024-history vv arms (`outputs/quarantine/20261007_vv_smith_history_arms/`); new = CMIP7 basis.
- **Model:** FaIR 2.2.4 (calib 1.6.0), Ladrillo L27, BRICK 2.0 post-PR#93; cm relative to 1995–2014; joint arm unless
  noted. FACTS is relative to 2005, n = 200.
- **Machine-readable:** `outputs/vv_cmip7_paper_number_diff_20261007.csv`, computed from `vv_model_comparison_L27.csv`,
  the `*_magiccclim` cells, `verify_magicc_regrowth_attribution_L27.csv`, `vv_model_comparison_L27_gmst.csv` and
  `vv_responsiveness_L27.csv`.
- **Commits:** SLR-RFF-BRICK at c35513a plus this rerun; FACTS 43bf0204.

## 1. Numbers quoted in the text: old → new (rounded as the text rounds)

| where | quantity | text | old | new | changes? |
|---|---|---|---|---|---|
| 4.3 High | Ladrillo total 2100, median | 71 | 71.0 | 72.7 | **71 → 73** |
| 4.3 High | BRICK 2.0 total 2100 | 82 | 82.4 | 84.6 | **82 → 85** |
| 4.3 High | MAGICC-SLR total 2100 | 62 | 62.3 | 62.3 | no |
| 4.3 High | Ladrillo total 2300 | 422 | 422.1 | 426.5 | **422 → 426** |
| 4.3 High | BRICK 2.0 total 2300 | 414 | 413.9 | 417.3 | **414 → 417** |
| 4.3 High | MAGICC-SLR total 2300 | 570 | 569.8 | 569.8 | no |
| 4.3 High | Ladrillo AIS 2300 | 244 | 243.6 | 246.5 | **244 → 246** |
| 4.3 High | BRICK 2.0 AIS 2300 | 248 | 248.0 | 250.6 | **248 → 251** |
| 4.3 High | MAGICC AIS 2300 | 382 | 381.6 | 381.6 | no |
| 4.3 High | Ladrillo on MAGICC climate, total 2300 | 407 | 406.8 | 410.1 | **407 → 410** |
| 4.3 High | BRICK 2.0 on MAGICC climate, total 2300 | 392 | 392.4 | 395.8 | **392 → 396** |
| 4.3 High | "decreases their totals by 15–22 cm" | 15–22 | 15.2 / 21.5 | 16.4 / 21.5 | **15–22 → 16–22** (Ladrillo 426.5 − 410.1; BRICK 417.3 − 395.8) |
| 4.3 High | AIS 5–95% width 2300, Ladrillo / BRICK 2.0 | 274 / 332 | 273.9 / 331.7 | 274.6 / 333.9 | **332 → 334** (274 unchanged) |
| 4.3 High | λ ensemble / posterior stats (0.0104, 0.0036) | — | — | — | no (posterior property) |
| 4.3 Low | Very Low total 2300: Ladrillo | 60 | 59.5 | 60.6 | **60 → 61** |
| 4.3 Low | Very Low total 2300: MAGICC-SLR | 46 | 45.7 | 45.7 | no |
| 4.3 Low | Very Low total 2300: BRICK 2.0 | 81 | 80.7 | 82.1 | **81 → 82** |
| 4.3 Low | VL total 2300 5–95% width: MAGICC | 67 | 67.3 | 67.3 | no |
| 4.3 Low | VL total 2300 5–95% width: Ladrillo | 137 | 137.1 | **160.7** | **137 → 161** ⚠ §3 |
| 4.3 Low | VL total 2300 5–95% width: BRICK 2.0 | 182 | 182.0 | **207.8** | **182 → 208** ⚠ §3 |
| 4.3 Peak-and-decline / Fig 5 | Ladrillo regrowth, Low-to-Neg | 0.11 | 0.112 | 0.102 | **0.11 → 0.10** |
| 4.3 Peak-and-decline / Fig 5 | Ladrillo regrowth, Medium-to-Low | 0.10 | 0.096 | 0.092 | **0.10 → 0.09** |
| 4.3 Peak-and-decline | Ladrillo on MAGICC climate regrowth, LN | 1.95 | 1.950 | 1.949 | no |
| 4.3 Peak-and-decline | MAGICC own regrowth, LN | 8.58 | 8.585 | 8.585 | no |
| 4.3 Peak-and-decline | gap decrease from the climate swap | 1.84 | 1.838 | 1.847 | **1.84 → 1.85** |
| 4.3 Peak-and-decline | structure / climate split | ¾ / ¼ | 0.783 | 0.782 | no |
| Fig 6 caption | FaIR High − Very Low GMST gap 2100 / 2150 / 2300 | 1.7 / 3.1 / 5.5 K | 1.677 / 3.125 / 5.461 | 1.677 / 3.124 / 5.459 | no |
| Fig 6 caption | MAGICC gap 2.0 / 3.6 / 5.9 K | — | — | — | no (own climate) |
| 4.2 FACTS | FittedISMIP High-to-Low Greenland 2300, default | 47 | 46.5 | 46.4 | **47 → 46** (a rounding flip; 0.1 cm move) |
| 4.2 FACTS | the same, fit evaluated through 2300 | 112 | — | — | **not recomputable**: no output file (already flagged in `gmd_prefinal_review_2026-09-30.md` item 6) |
| Conclusions | "reductions of up to 31 cm by 2300 (… SSP2-4.5 and High-to-Low)" | 31 | vv max 27.2 (vvHL) | vv max 27.4 (vvHL) | no: the 31 is the SSP2-4.5 cell, and the SSPs did not move |

The prose reading of each paragraph survives every change above: the orderings, the "fairly similar at 2100", the
"together … well below MAGICC" and the structure-over-climate attribution all hold.

## 2. Figures to swap (regenerated; paper PNGs in `figures/paper/`)

| figure | file | moved? |
|---|---|---|
| Fig 2 | `model_comparison_components_vv_L27_2100.png` (+ caption txt: provenance commit only) | yes |
| Fig 3 | `model_comparison_components_vv_L27_2300.png` (and `_2150`) | yes |
| Fig 4 | `future_components_vv_L27_joint.png` | yes |
| Fig 5 | `vv_gsic_ladrillo_L27_2300.png` (+ caption txt: driver commit 6cc34b6 → 31aa963) | yes |
| Fig 6 | `vv_responsiveness_L27.png` | yes |

## 3. ⚠ Two things to decide or know (not resolved here)

1. **The Very Low 2300 width moves +24 cm (Ladrillo) and +26 cm (BRICK 2.0) from a ~0.06 K warmer path.**
   - The cause is the DAIS fast-dynamics tail, not the bulk: Ladrillo's VL-2300 AIS median moves 11.7 → 12.2 cm while
     its p95 moves 114 → 140 cm, and draws above 100 cm go from 112 to 136 of 2,000.
   - VL sits near the fast-dynamics threshold, so its upper tail is steep in temperature. BRICK 2.0 (an independent
     posterior on the same DAIS) moves by the same amount.
   - The text's ordering (MAGICC 67 < Ladrillo 161 < BRICK 2.0 208) is unchanged.
   - It means a low-scenario 2300 width is sensitive to a few hundredths of a kelvin. Whether that deserves a sentence
     is your call.
2. **FACTS p95 for the DeConto 2021 / Bamber 2019 workflows is not a stable statistic at n = 200.**
   - Its moves (up to +616 cm on DeConto AIS at vvVL 2300) are a quantile falling into the gap of a bimodal
     distribution: 8 → 13 of 200 samples in the MICI branch.
   - The bootstrap 5–95% of that p95 spans both modes in both runs. Details are in
     `facts/quarantine/20261007_vv_smith_history/README.md` §4.
   - The text quotes no FACTS p95, but the Fig. 2 Total bracket's thin line is "the union of their 5–95%", so its upper
     end at 2100 is set by these workflows. At 2100 the moves are small (FACTS total p95 ≤ +13 cm across all markers).
