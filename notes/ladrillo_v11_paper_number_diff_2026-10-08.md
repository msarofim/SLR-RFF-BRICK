# GMD draft: the numbers after the Ladrillo v1.1 rerun (2026-10-08)

**For Marcus. The docx was NOT edited**: Tony holds `GMD.Ladrillo.v1_forTonyreview_TW1.docx`.

- **Basis:** v1.0 = the submitted projections (quarantined: `outputs/quarantine/20261008_ladrillo_v10_superseded/`).
  v1.1 = same posterior (L27), paleo single assignment, land water starting at 0.
- **Model:** FaIR 2.2.4 (calib 1.6.0), CMIP7 basis; cm relative to 1995–2014; joint arm unless noted.
- **Machine-readable:** `outputs/v11_paper_number_diff_20261008.csv` (`python/v11_paper_number_diff.py`).
- **Commits:** SLR-RFF-BRICK 39926cc, bcebbac + this note; Ladrillo.jl 78b03c6 (v1.1.0, re-certified bit-identical).
- ⚠ **"Printed" is Tony's copy, which still carries the PRE-CMIP7 van Vuuren numbers.** The 10-07 diff
  (`notes/vv_cmip7_paper_number_diff_2026-10-07.md`) was never applied to it. Column "v1.0 file" is the CMIP7-basis
  v1.0 output, so **printed → v1.0 file** is the 10-07 round and **v1.0 file → v1.1** is this one. Both are needed
  for one docx pass.

## 1. Numbers that change at the text's rounding

| where | quantity | printed | v1.0 file | **v1.1** | which round |
|---|---|---|---|---|---|
| Intro | glacier responsiveness, Ladrillo / BRICK 2.0 (High − Very Low, 2300) | 1.3× | 1.41 | **1.4×** | 10-07 (missed by the 10-07 diff); glaciers are bit-identical in v1.1 |
| 2.2.2 | Greenland tap's contribution to the SSP5-8.5 total, 2300 (difference of the total medians) | 36.5 | 36.46 | ~~34.7~~ | ⛔ superseded: RULED 10-08, quote the paired statistics, §3.3 |
| 2.2.2 | … at SSP2-4.5 | 0.3 | 0.265 | ~~0.0~~ | ⛔ superseded, §3.3 |
| 2.2.2 | **tap, paired (RULED 10-08):** share of draws in which it fires, SSP5-8.5 / SSP2-4.5 / SSP1-2.6, 2300 | — | 96.2 / 11.7 / 0.25 % | **96.2 / 11.7 / 0.25 %** (1,924 / 234 / 5 of 2,000) | new statistic; identical in v1.0 |
| 2.2.2 | **tap, paired:** mean contribution to the total, same three, 2300 | — | 35.0 / 1.5 / 0.00 | **35.0 / 1.5 / 0.00 cm** | new statistic; v1.0 → v1.1 moves ≤ 0.0003 cm |
| 2.2.3 | Antarctic amplification leverage, +1σ, SSP2-4.5 AIS 2300 (fixed arm) | 46 | 45.77 | **45** | v1.1 (17% unchanged; SSP5-8.5 20 cm / 4% unchanged) |
| 2.2.3 | reverting to 1.196: SSP2-4.5 total 2100 / 2300 | 15 / 32 | 15.13 / 31.76 | **14 / 34** | v1.1 |
| 2.2.3 | … SSP5-8.5 2100 / 2300 | 6 / 13 | 6.38 / 12.54 | **7 / 12** | v1.1 |
| 3.2 | refit precision: AIS medians, L27 vs L27r, max over 5 fixed-panel cells | 1.3 | 1.32 | **1.8** | v1.1 ⚠ §3.4 |
| 4.3 High | Ladrillo total 2100 | 71 | 72.75 | **73** | 10-07 |
| 4.3 High | BRICK 2.0 total 2100 | 82 | 84.63 | **85** | 10-07 |
| 4.3 High | Ladrillo total 2300 | 422 | 426.45 | **428** | both |
| 4.3 High | BRICK 2.0 total 2300 | 414 | 417.35 | **417** | 10-07 |
| 4.3 High | Ladrillo AIS 2300 | 244 | 246.45 | **250** | both |
| 4.3 High | BRICK 2.0 AIS 2300 | 248 | 250.55 | **251** | 10-07 |
| 4.3 High | Ladrillo / BRICK 2.0 on MAGICC climate, total 2300 | 407 / 392 | 410.10 / 395.83 | **410 / 396** | 10-07 |
| 4.3 High | "decreases their totals by 15–22 cm" | 15–22 | 16.36 / 21.52 | **17–22** | both |
| 4.3 High | AIS 5–95% widths 2300, Ladrillo / BRICK 2.0 | 274 / 332 | 274.61 / 333.86 | **268 / 334** | Ladrillo v1.1; BRICK 10-07 |
| 4.3 Low | Very Low total 2300, Ladrillo / BRICK 2.0 | 60 / 81 | 60.60 / 82.09 | **61 / 82** | 10-07 |
| 4.3 Low | Very Low total 2300 width, Ladrillo / BRICK 2.0 | 137 / 182 | 160.69 / 207.78 | **163 / 208** | both / 10-07 |
| Concl. | "reductions of up to 31 cm by 2300" (BRICK 2.0 − Ladrillo AIS, SSP2-4.5) | 31 | 30.93 | **30** | v1.1 |

- **The 10-07 rows not listed above** (regrowth 0.11/0.10 → 0.10/0.09, the 1.84 → 1.85 gap, FACTS 47 → 46) are
  glacier, climate or FACTS numbers. v1.1 does not touch them; take them from the 10-07 note.
- **Orderings survive:**
  - Conclusions: SSP2-4.5 is still the largest gap (30.1 cm), and High-to-Low is still second (28.6, was 27.4).
  - High: Ladrillo 428 vs BRICK 2.0 417 at 2300, and Ladrillo 73 below BRICK 2.0 85 at 2100.
  - The High AIS widths: Ladrillo is still narrower.
  - The Very Low width ordering (MAGICC 67 < Ladrillo 163 < BRICK 2.0 208).
  - Intro: "Antarctic ice and thermal expansion have equal sensitivity" holds. At 2300 the AIS responsiveness is
    237.7 cm for Ladrillo and 237.7 for BRICK 2.0 (was 234.2), against TE 69/66.
  - "Ladrillo less sensitive on shorter timescales" holds: 22.7 vs 32.8 cm at 2100.

## 2. Numbers checked and unchanged

- **Abstract and Table 4:** RMSE reductions 94/79/72/13%, and every Table 4 cell.
  - The scorecard moved only in its provenance text.
  - The posterior predictive moved only in its 2026 95th percentiles, by ≤ 0.001 cm.
- **AIC/BIC and all of Table 5.** Its residual inputs are byte-identical, and the rerun gates that.
- **Sect. 3.1 IMBIE:** −2.6σ and −0.38 cm.
- **Sect. 3.2 hindcast refit precision:** 0.005 cm.
- **Sect. 4.1 cumulative rise:** +20.41 (−0.6) and +7.88 (+0.07).
- **Sect. 2.2.5 land water:** 8.8 cm by 2300.
- **Greenland, glacier and TE numbers everywhere**, including Sect. 2.2.2's 0.7–7.6 cm shape sensitivity and the
  4.4 / 2.4 Greenland ratios. These components are bit-identical between v1.0 and v1.1.
- **The convergence R̂/ESS:** a chain statistic, not re-run by design.

## 3. Things to know or decide

1. **The moves are resampling noise, not a bias.**
   - Fix A replaces "one chain's 500 paleo rows, reused by all four chains" with 2,000 distinct assignments.
   - Across the 3 SSPs and 7 markers × 3 horizons, the Ladrillo joint medians moved in mixed directions:
     - Antarctica: 10 up, 20 down.
     - Total: 16 up, 14 down.
   - Median |Δ| is 0.26–0.31 bootstrap standard errors, max 1.64, and none above 2
     (`outputs/diag_v11_paleo_change_vs_noise.csv`).
   - The largest printed mover, High AIS 2300 (+3.5 cm), is 1.6 se.
   - Fix B's share is ≤ 0.05 cm everywhere. BRICK 2.0, which only has fix B, moves ≤ 0.03 cm in every row above.
2. **The paper's version label.** The title, the Conclusions' first sentence and Code availability say "Ladrillo
   v1.0". The package is now 1.1.0, with `v1.0.0` tagged. Your call.
3. **The tap contribution (2.2.2). ✅ RULED 10-08 (decision 4): quote the PAIRED statistics** — the share of draws
   in which the tap fires and its paired mean contribution (tapped − untapped, same draws and FaIR configs, joint arm).
   - Producer: `python/diag_tap_paired_contribution.py` → `outputs/diag_tap_paired_contribution_L27.csv` (both
     versions, 2100/2150/2300, Greenland and total, bootstrap se, seed in the provenance). The three rows above are in
     the machine-readable diff as `tap [RULED 10-08] …`.
   - **2300, total:** SSP5-8.5 fires in 96.2% (1,924 of 2,000), paired mean +35.0 cm (se 0.4), +36.4 cm in the draws
     where it fires. SSP2-4.5 fires in 11.7% (234), paired mean +1.5 cm (se 0.14), +12.6 cm where it fires. SSP1-2.6
     fires in 0.25% (5), paired mean 0.00 cm.
   - **Why this statistic, measured:** v1.0 → v1.1 the paired means move by at most 0.0003 cm (Greenland's by exactly 0). The difference of the total
     medians moved 36.46 → 34.69 (bootstrap se 1.4–1.5) and 0.26 → 0.00 (se 0.15–0.31), with the tap unchanged.
     Greenland is bit-identical between the versions; the paired TOTAL differs only through the Antarctic sea-level
     feedback.
   - "Fires" is exact, not a tolerance: the tap's ramp is clamped at zero below onset, so a draw that never passes it
     gets exactly zero. The script asserts that no draw moves its total with Greenland unmoved.
   - The prose is yours; these are the numbers for it.
4. **Refit precision 1.3 → 1.8 cm** (L27 vs L27r, fixed panels, the max over 5 cells).
   - Both panels now use the same paleo rows by position, as they did in v1.0. So this is the refit difference plus
     sampling noise of a 2,000-draw median, now drawn over different paleo pairings.
   - The v1.0 pair was also on mixed land-water bases (L27r ran before the 09-21 switch to the observed series), which
     v1.1 removes.
   - "within 1.3 cm" becomes "within 1.8 cm".
5. **λ / T_crit are not inert in the hindcast** (wording in 2.2.3, "likelihood-flat over the 1900–2025 record").
   - That holds for the calibration, which uses the paleo medians and never crosses the threshold.
   - It does not hold for every propagated draw: 4 of the 10,000 (T_crit −16.4 to −16.9 °C) start fast dynamics in
     2021–2026, adding up to 1.6 cm of Antarctic sea level by 2026.
   - Every quoted hindcast number is unchanged.
   - ✅ **RULED 10-08 (decision 2): no change to the paper's method or numbers.** Any short qualifier in 2.2.3 is your
     prose. Conditioning is offered to package users as an opt-in option in Ladrillo.jl **v1.2**
     (`posterior(; drop_record_crossings=true)`), not in v1.1.
   - ⚠ **PREMISE CORRECTED after the ruling (CHANGELOG 10-08e).** "None of the 4 is among the 2,000 projection rows" is
     true on the MEAN climate only. In the JOINT arm, the reported band, each draw runs on its own FaIR config.
     - There, **3 of the 2,000 SSP draws fire by 2025** (in 2021–2023) and 7–8 by 2026; **2 of the van Vuuren draws**
       fire by 2025 and 5 by 2026.
     - Conditioning on the record end (2025) would move **medians by ≤ 0.23 cm** and **p95 by ≤ 3.8 cm** (Very Low AIS
       2300). Every move is ≤ 0.38 bootstrap se.
     - **One quoted number changes at the text's rounding:** the Very Low total 2300 width, 163.1 → 162.3.
     - Conditioning on 2026 instead moves it 163 → 159 (max 0.73 se).
     - Producer: `python/diag_record_crossing_effect.py` → `outputs/diag_record_crossing_effect_L27.csv`.
     - ⛔ **A qualifier must NOT say "none in the reported projections":** that is false for the joint arm.
6. **Wording that describes v1.0 mechanics:**
   - **Sect. 2.2.5 / Table A3, land water:** the series now starts at 0. The draft never mentioned the step; its
     "< 0.02 cm" is the calibration-side swap and still stands.
   - **Table A3, λ/T_crit row:** "projection: joint draws" is now exactly true; v1.0 reused 500 rows per chain.
7. **Table A2 → the 10k subsample.** Two cells change (PC14 slope loading −0.54 → −0.53, PC12 R̂ 1.018 → 1.017);
   the file is `outputs/ladrillo_table_a2_L27_sub10k.md`.
8. **The benchmark's frozen champion** (`benchmark/reference/L27`) is still v1.0.
   - The refresh scored the live v1.1 arms: one verdict changed, the SSP1-2.6 2300 total spread versus the
     literature, WARN → PASS.
   - Re-freezing the champion on v1.1 is your call.

## 4. Figures to swap (regenerated; paper PNGs in `figures/paper/`)

| figure | file | moved? |
|---|---|---|
| Fig 1 | hindcast | no (the paper PNG is byte-identical) |
| Fig 2 | `model_comparison_components_vv_L27_2100.png` | yes |
| Fig 3 | `model_comparison_components_vv_L27_2300.png` (and `_2150`) | yes |
| Fig 4 | `future_components_vv_L27_joint.png` | yes |
| Fig 5 | `vv_gsic_ladrillo_L27_2300.png` | no (glaciers only); the 10-07 swap still applies |
| Fig 6 | `vv_responsiveness_L27.png` | yes |
