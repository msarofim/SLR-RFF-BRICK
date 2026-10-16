# TW2 edit inventory (GMD Ladrillo draft, next version)

- **Draft read:** `deliverables/GMD.Ladrillo.v1_forTonyreview_TW2.docx` (10-15 16:33), read only: pandoc `--track-changes=accept|all` and an lxml read of `word/document.xml`. Never written.
- **Basis of every new number:** canonical `outputs/` after the 2026-10-15 BRICK 2.0 swap (Zenodo 10.5281/zenodo.20592337 joint SNEASY-BRICK posterior), Ladrillo L27 as released in Ladrillo.jl **v1.3.0** (v1.2 model + record-conditioned joint arm + published-emissions vv forcing), FaIR 2.2.4 (calib 1.6.0) CMIP7 basis; cm relative to 1995–2014 (projections) or 1995–2005 (hindcast); joint arm unless stated.
- **Old values confirmed** against `outputs/quarantine/20261015_brick20_may22_posterior/outputs/` (every printed BRICK 2.0 number reproduces from the May-22 files with the same accessor).
- **Verification:** every `anchor` is ≥ 40 characters and occurs in exactly one accepted paragraph; every `old` occurs exactly once in that paragraph (table cells: exactly once in the named cell). 91 / 91 pass. `verify.tony_insertion_overlap` says whether the old span sits inside Tony's tracked insertions. E001's anchor contains the superscript 'th', which pandoc plain renders as `20^(th)`; it matches the docx text.
- Machine-readable: `tw2_edit_inventory.json` (same ids). Built by `build_inventory.py`; numbers by `compute_numbers.py` (output `numbers_out.txt`).

**Counts:** caption 2, citation 2, label 3, number 36, table 39, wording 9; total 91.

## Edits

### Title

- **E001** [label] anchor: “Ladrillo v1.0, a spinoff of BRICK with improved 20th century hindcasts”
  - old: “Ladrillo v1.0”
  - new: “Ladrillo v1.3”
  - source: Ladrillo.jl git tag v1.3.0 (README 'Versions' v1.3; CITATION.cff version 1.3.0, 2026-10-15)
  - note: GMD convention puts the model version in the title; v1.3 = v1.2's model and numbers + BRICK 2.0 arm on the Zenodo posterior.

### Abstract

- **E002** [number] anchor: “root-mean-square error (RMSE) reductions of 94% for Antarctica”
  - old: “94% for Antarctica”
  - new: “95% for Antarctica”
  - source: outputs/brick20_swap_paper_number_diff_20261015.csv row 'AIS RMSE reduction vs BRICK 2.0, full window (%)': 100*(1-0.053785) = 94.62 -> 95; outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv window=full component=AIS rmse Ladrillo 0.09307 / BRICK 2.0 1.73033
  - docx: comments anchored in this paragraph: 5, 16
- **E003** [number] anchor: “72% for Greenland, and 13% for thermal expansion”
  - old: “13% for thermal expansion”
  - new: “19% for thermal expansion”
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv window=full component='thermal exp.': rmse Ladrillo 0.46658 / BRICK 2.0 0.57689 = 0.80878; 100*(1-0.80878) = 19.12 -> 19 (was 1-0.87098 = 12.90 -> 13 on the May-22 file)
  - note: Glaciers 79% (79.41) and Greenland 72% (71.99) are unchanged at integer rounding.
  - docx: comments anchored in this paragraph: 5, 16
- **E004** [number] anchor: “both favour Ladrillo (by 89 and 26), indicating that it is not overfitting”
  - old: “(by 89 and 26)”
  - new: “(by 95 and 32)”
  - source: outputs/ic_ladrillo_vs_brick20_L27.csv (rho<=0.99, ar1_prof): dAIC = 95.486, dBIC = 32.207 (fit4 ll_max Ladrillo 240.404, BRICK 2.0 177.661; k 50/35; N 502)
  - note: Round from full precision: the .md prints 95.5, which must NOT be re-rounded to 96.
  - docx: comments anchored in this paragraph: 5, 16

### 1 Introduction

- **E005** [number] anchor: “Ladrillo is more sensitive to differences between scenarios by 2300 for the glacier”
  - old: “1.3×”
  - new: “1.5×”
  - source: outputs/brick20_swap_paper_number_diff_20261015.csv row 'glacier responsiveness ratio Ladrillo/BRICK 2.0 (vvH-vvVL, 2300)' = 1.469; cells joint vvH-vvVL glaciers 2300: Ladrillo 14.23 / BRICK 2.0 9.68 cm
  - note: Greenland '(3×)' holds: 44.44 / 16.08 = 2.76 -> 3 at the text's integer precision.
- **E006** [wording] anchor: “whereas Antarctic ice and thermal expansion have equal sensitivity to scenarios on those timescales”
  - old: “have equal sensitivity to scenarios”
  - new: “have similar sensitivity to scenarios (about 1.1×)”
  - source: cells joint vvH-vvVL at 2300 (scope_slr_fairunc_cells_{vvH,vvVL}_spliced_L27_tap4p69K_V5p64m_tau800.csv vs ..._oldbrick.csv): AIS 237.1 vs 208.3 cm = 1.14; TE 68.6 vs 64.2 cm = 1.07 (May-22: AIS 237.1 vs 238.0 = 1.00, TE 1.04). Also outputs/brick20_swap_paper_number_diff_20261015.csv rows 'AIS responsiveness ...'
  - note: READING CHANGE driven by the swap: 'equal' no longer holds for Antarctica (Ladrillo now 14% more responsive at 2300). The parenthetical on shorter timescales still holds (2100: 22.7 vs 29.2 cm). Marcus may prefer other wording.

### 2.1 Overall structure

- **E007** [wording] anchor: “In the fixed arm, every draw is driven by the FaIR ensemble-mean GMST and ocean heat content, so the spread is parameter uncertainty only.”
  - old: “so the spread is parameter uncertainty only.”
  - new: “so the spread is parameter uncertainty only. The ensemble mean is the per-year mean over the 841 configurations, taken separately for GMST and ocean heat content, and it also drives the calibration. In the joint arm, each draw follows the ensemble mean through 2014 and, after 2014, its configuration's own simulation (as an anomaly from that configuration's 1995–2014 mean). The BRICK 2.0 comparison is run in the same way, with the BRICK parameters of the joint SNEASY–BRICK posterior subsample published with MimiBRICK v2.0.0 (10,000 draws; Wong et al., 2026).”
  - source: handoff_2026-10-01c_gmd_round.md §1c item 6 (Tony's ensemble-mean question, comments 35/157); julia/scope_slr_fair_uncertainty.jl convention() L363-372: SPLICE_YEAR=2014, mean path = fair_mean_{gmst,ohc}_<scen>.csv through 2014, then mref + (raw - cref) with LADRILLO_REF=(1995,2014) (julia/ladrillo_projection.jl:214); BRICK posterior: CHANGELOG 2026-10-15d, Ladrillo README 'BRICK 2.0 posterior', Zenodo 10.5281/zenodo.20592337 parameters_subsample_sneasybrick.csv (sha256 d74577f6…)
  - note: Two pieces: (a) queued item 6 (ensemble-mean caveat); (b) the brief's item 6 Methods sentence naming the BRICK 2.0 posterior (new reference E092). Paragraph carries Tony comment 35.
  - docx: comments anchored in this paragraph: 35

### 2.2.2 Greenland ice sheet

- **E008** [wording] anchor: “holding it constant instead would increase Greenland melt by an additional 0.7 cm”
  - old: “to 7.6 cm (SSP5-8.5, 2300).”
  - new: “to 7.6 cm (SSP5-8.5, 2300; joint arm).”
  - source: handoff_2026-10-01c §1c item 5; numbers re-verified on the CONDITIONED joint arm: paired median (shape-constant minus shipped) Greenland 2300 = 0.664 (SSP1-2.6) / 7.565 (SSP5-8.5) cm, 1,997 paired draws (scope_slr_fairunc_draws_<ssp>_spliced_L27_tap4p69K_V5p64m_tau800[_gis_amp_shape_const].csv); original receipt outputs/diag_gis_amp_shape_joint_L27.csv (2,000 draws, 09-30)
- **E009** [number] anchor: “This discharge channel contributes 36.5 cm to the SSP5-8.5 total at 2300”
  - old: “This discharge channel contributes 36.5 cm to the SSP5-8.5 total at 2300, nothing at SSP1-2.6, and 0.3 cm at SSP2-4.5, yielding”
  - new: “In the joint arm at 2300, this discharge channel fires in 96.2% of draws under SSP5-8.5, adding 35.0 cm to the total on average, in 11.6% under SSP2-4.5 (1.5 cm on average) and in 0.25% under SSP1-2.6 (less than 0.01 cm), yielding”
  - source: RULED 10-08 (decision 4): paired statistics. outputs/diag_tap_paired_contribution_L27.csv version=v1.1 (conditioned, n=1,997), horizon 2300, component total, arm joint: fires_share 0.961943 / 0.115674 / 0.002504 (1,921 / 231 / 5 of 1,997); paired_mean_cm 34.953 / 1.4535 / 0.000117. Also outputs/brick20_swap_paper_number_diff_20261015.csv rows 'tap [RULED 10-08] …'. Ratios kept: Greenland median 2300 joint tapped 79.42/17.85 = 4.45 -> 4.4; untapped 41.94/17.82 = 2.35 -> 2.4 (cells files)
  - note: handoff_2026-10-01c §1c item 5 ('(joint arm)' label) is satisfied by 'In the joint arm'. The 10-08 note's 11.7% / 1,924 of 2,000 were pre-conditioning; current is 11.6% of 1,997. 'This discharge channel ' is TONY's tracked insertion (2026-10-06).
  - docx: old span overlaps Tony's tracked insertion (partial (18% of old span): ['This discharge channel ']); comments anchored in this paragraph: 63, 73

### 2.2.3 Antarctic ice sheet

- **E010** [wording] anchor: “holds a quarter as many draws under the joint prior as under independent ones.”
  - old: “holds a quarter as many draws under the joint prior as under independent ones.”
  - new: “holds a quarter as many draws under the joint prior as under independent ones. Scored under the calibration likelihood, every draw whose fast dynamics begin by 2025 has a weight below 10⁻²⁰, so the joint arm drops every draw whose attached threshold is crossed by 2025 on its paired FaIR configuration: 3 of the 2,000 draws in the SSP scenarios and 2 of the 2,000 in the van Vuuren scenarios.”
  - source: Brief item 4: conditioning DONE since 10-08k (SLR CHANGELOG 2026-10-08k 'Dropped draws: SSP 229, 610, 1260; vv 187, 610'; Ladrillo README Versions v1.2); weights: CHANGELOG 2026-10-08f / outputs/record_likelihood_weights.csv (Δ log L −46 to −802 on the calibration climate and −609 to −1703 for the joint-arm pairs, so w ≤ e^−46 ≈ 1e-20; every 2026 onset w = 1; joint-arm pairs stay rejected under every more lenient noise model, w ≤ 2e-14)
  - note: One methods sentence, describing the conditioning as done. Answers Tony 412/413 in part. BRICK 2.0 is NOT conditioned (CHANGELOG 10-08m); say so only if Marcus wants it. No effect sizes quoted (see UNCERTAIN U07).
  - docx: comments anchored in this paragraph: 128
- **E011** [number] anchor: “a one-sigma change moves Antarctic sea level at 2300 by a mean change of 46 cm”
  - old: “46 cm for SSP2-4.5”
  - new: “45 cm for SSP2-4.5”
  - source: outputs/brick20_swap_paper_number_diff_20261015.csv row 'amp leverage, +1 prior sd, mean, SSP2-4.5 AIS 2300 (fixed)' = 45.17 (outputs/diag_ais_amp_leverage_L27.csv)
  - note: 17% / 20 cm / 4% unchanged.
- **E012** [number] anchor: “Reverting to DAIS's 1.196 would add 15 cm to the SSP2-4.5 total”
  - old: “add 15 cm to the SSP2-4.5 total at 2100 and 32 cm at 2300 (6 and 13 cm”
  - new: “add 14 cm to the SSP2-4.5 total at 2100 and 34 cm at 2300 (7 and 12 cm”
  - source: outputs/brick20_swap_paper_number_diff_20261015.csv rows '1.196 reversion …' = 14.15 / 33.66 / 6.84 / 11.73 (ssps_components_2300_L27aisamp1p196 minus L27 panel, fixed)

### 2.2.4 Thermal expansion

- **E013** [wording] anchor: “is the annual change in FaIR's full-depth ocean heat content (the mean over the 841 configurations”
  - old: “FaIR's full-depth ocean heat content”
  - new: “FaIR's ocean heat content, which FaIR computes as its time-integrated top-of-atmosphere energy imbalance and so is Earth's total heat uptake (about 91% of it in the ocean)”
  - source: handoff_2026-10-01c §1c item 2; FaIR 2.2.4 fair/fair.py:1596-1609 (ocean_heat_content_change = cumsum(toa_imbalance) x 4πR²); outputs/diag_fair_ohc_vs_earth_heat.csv nonocean_share 0.088 (1993-2020), 0.086-0.092 across windows -> ocean ~91%
  - note: Tony comment 157 ('caveat about mean') sits on this paragraph; E007 supplies that caveat in Sect. 2.1.
  - docx: comments anchored in this paragraph: 157, 160

### 3.2 Model code and calibration

- **E014** [number] anchor: “reproduces every Antarctic projection median (fixed arm) to within 1.3 cm at 2300”
  - old: “within 1.3 cm at 2300”
  - new: “within 1.8 cm at 2300”
  - source: outputs/brick20_swap_paper_number_diff_20261015.csv row 'refit precision: max |AIS med L27r - L27| over 5 fixed-panel cells' = 1.789 (v1.1; notes/ladrillo_v11_paper_number_diff_2026-10-08.md §3.4)
  - note: Hindcast 0.005 cm unchanged.
  - docx: comments anchored in this paragraph: 292, 296

### 4.1 Table 4

- **E015** [table] Table 4, row *Antarctica*, column *1900–1919*: `0.026` → `0.024`
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv rmse Ladrillo / rmse BRICK 2.0 = 0.024109 (old values reproduce from outputs/quarantine/20261015_brick20_may22_posterior/outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv)
- **E016** [table] Table 4, row *Antarctica*, column *1920–1949*: `0.062` → `0.056`
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv rmse Ladrillo / rmse BRICK 2.0 = 0.056208 (old values reproduce from outputs/quarantine/20261015_brick20_may22_posterior/outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv)
- **E017** [table] Table 4, row *Antarctica*, column *1950–1992*: `0.099` → `0.085`
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv rmse Ladrillo / rmse BRICK 2.0 = 0.084602 (old values reproduce from outputs/quarantine/20261015_brick20_may22_posterior/outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv)
- **E018** [table] Table 4, row *Antarctica*, column *1993–2025*: `1.077` → `1.441`
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv rmse Ladrillo / rmse BRICK 2.0 = 1.441240 (old values reproduce from outputs/quarantine/20261015_brick20_may22_posterior/outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv)
- **E019** [table] Table 4, row *Antarctica*, column *full*: `0.059` → `0.054`
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv rmse Ladrillo / rmse BRICK 2.0 = 0.053785 (old values reproduce from outputs/quarantine/20261015_brick20_may22_posterior/outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv)
- **E020** [table] Table 4, row *Greenland*, column *1900–1919*: `0.100` → `0.102`
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv rmse Ladrillo / rmse BRICK 2.0 = 0.101534 (old values reproduce from outputs/quarantine/20261015_brick20_may22_posterior/outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv)
- **E021** [table] Table 4, row *Greenland*, column *1920–1949*: `0.251` → `0.252`
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv rmse Ladrillo / rmse BRICK 2.0 = 0.252348 (old values reproduce from outputs/quarantine/20261015_brick20_may22_posterior/outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv)
- **E022** [table] Table 4, row *Greenland*, column *1950–1992*: `0.293` → `0.294`
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv rmse Ladrillo / rmse BRICK 2.0 = 0.293992 (old values reproduce from outputs/quarantine/20261015_brick20_may22_posterior/outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv)
- **E023** [table] Table 4, row *Greenland*, column *1993–2025*: `0.713` → `0.715`
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv rmse Ladrillo / rmse BRICK 2.0 = 0.714904 (old values reproduce from outputs/quarantine/20261015_brick20_may22_posterior/outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv)
- **E024** [table] Table 4, row *Greenland*, column *full*: `0.279` → `0.280`
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv rmse Ladrillo / rmse BRICK 2.0 = 0.280152 (old values reproduce from outputs/quarantine/20261015_brick20_may22_posterior/outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv)
- **E025** [table] Table 4, row *Glaciers*, column *1900–1919*: `0.205` → `0.206`
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv rmse Ladrillo / rmse BRICK 2.0 = 0.205643 (old values reproduce from outputs/quarantine/20261015_brick20_may22_posterior/outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv)
- **E026** [table] Table 4, row *Glaciers*, column *1920–1949*: `0.114` → `0.115`
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv rmse Ladrillo / rmse BRICK 2.0 = 0.114693 (old values reproduce from outputs/quarantine/20261015_brick20_may22_posterior/outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv)
- **E027** [table] Table 4, row *Glaciers*, column *1950–1992*: `1.804` → `1.845`
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv rmse Ladrillo / rmse BRICK 2.0 = 1.844796 (old values reproduce from outputs/quarantine/20261015_brick20_may22_posterior/outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv)
- **E028** [table] Table 4, row *Glaciers*, column *1993–2025*: `0.212` → `0.209`
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv rmse Ladrillo / rmse BRICK 2.0 = 0.209110 (old values reproduce from outputs/quarantine/20261015_brick20_may22_posterior/outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv)
- **E029** [table] Table 4, row *Glaciers*, column *full*: `0.205` → `0.206`
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv rmse Ladrillo / rmse BRICK 2.0 = 0.205918 (old values reproduce from outputs/quarantine/20261015_brick20_may22_posterior/outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv)
- **E030** [table] Table 4, row *Thermal expansion*, column *1900–1919*: `0.808` → `0.737`
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv rmse Ladrillo / rmse BRICK 2.0 = 0.737205 (old values reproduce from outputs/quarantine/20261015_brick20_may22_posterior/outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv)
- **E031** [table] Table 4, row *Thermal expansion*, column *1920–1949*: `0.819` → `0.750`
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv rmse Ladrillo / rmse BRICK 2.0 = 0.750496 (old values reproduce from outputs/quarantine/20261015_brick20_may22_posterior/outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv)
- **E032** [table] Table 4, row *Thermal expansion*, column *1950–1992*: `1.003` → `0.925`
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv rmse Ladrillo / rmse BRICK 2.0 = 0.924893 (old values reproduce from outputs/quarantine/20261015_brick20_may22_posterior/outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv)
  - note: FORMAT: now below 1, so the cell must become BOLD (caption: 'below 1 … marked in bold'); it is not bold in TW2.
- **E033** [table] Table 4, row *Thermal expansion*, column *1993–2025*: `1.329` → `1.572`
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv rmse Ladrillo / rmse BRICK 2.0 = 1.572257 (old values reproduce from outputs/quarantine/20261015_brick20_may22_posterior/outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv)
- **E034** [table] Table 4, row *Thermal expansion*, column *full*: `0.871` → `0.809`
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv rmse Ladrillo / rmse BRICK 2.0 = 0.808782 (old values reproduce from outputs/quarantine/20261015_brick20_may22_posterior/outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv)
- **E035** [table] Table 4, row *Total*, column *1900–1919*: `1.986` → `2.650`
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv rmse Ladrillo / rmse BRICK 2.0 = 2.650458 (old values reproduce from outputs/quarantine/20261015_brick20_may22_posterior/outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv)
- **E036** [table] Table 4, row *Total*, column *1920–1949*: `0.563` → `0.511`
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv rmse Ladrillo / rmse BRICK 2.0 = 0.510757 (old values reproduce from outputs/quarantine/20261015_brick20_may22_posterior/outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv)
- **E037** [table] Table 4, row *Total*, column *1950–1992*: `0.215` → `0.198`
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv rmse Ladrillo / rmse BRICK 2.0 = 0.198433 (old values reproduce from outputs/quarantine/20261015_brick20_may22_posterior/outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv)
- **E038** [table] Table 4, row *Total*, column *1993–2025*: `0.677` → `0.770`
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv rmse Ladrillo / rmse BRICK 2.0 = 0.770361 (old values reproduce from outputs/quarantine/20261015_brick20_may22_posterior/outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv)
- **E039** [table] Table 4, row *Total*, column *full*: `0.546` → `0.513`
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv rmse Ladrillo / rmse BRICK 2.0 = 0.513442 (old values reproduce from outputs/quarantine/20261015_brick20_may22_posterior/outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv)

### 4.1 Comparisons to observations

- **E040** [number] anchor: “Over 1900–1919 BRICK 2.0's Antarctic undershoot (−2.90 cm)”
  - old: “Antarctic undershoot (−2.90 cm) and glacier overshoot (+3.28 cm)”
  - new: “Antarctic undershoot (−3.13 cm) and glacier overshoot (+3.27 cm)”
  - source: outputs/scope_ladrillo_vs_brick20_scorecard_L27.csv window 1900-1919 arm 'BRICK 2.0' mean_bias: AIS −3.1285, glaciers +3.2705 (May-22: −2.8999, +3.2810 reproduce the printed values)
  - note: 'nearly equal' still holds.
- **E041** [number] anchor: “so its four component biases sum to +0.62 cm out of 7.57 cm of absolute error”
  - old: “+0.62 cm out of 7.57 cm”
  - new: “+0.48 cm out of 7.86 cm”
  - source: same file, BRICK 2.0 1900-1919 mean_bias over AIS/Greenland/glaciers/thermal exp.: sum +0.4785, sum|.| 7.8640 (−3.1285, −0.5642, +3.2705, +0.9008)
  - note: Ladrillo's +1.23 / 1.37 and the 1920-1949 +0.22 / 0.77 are Ladrillo-only and unchanged.
- **E042** [number] anchor: “where BRICK 2.0 is closer (RMSE of 0.13 cm for BRICK 2.0 and 0.23 cm for Ladrillo)”
  - old: “0.13 cm for BRICK 2.0”
  - new: “0.12 cm for BRICK 2.0”
  - source: scorecard glaciers 1950-1992 rmse BRICK 2.0 0.1241 (May-22 0.1269); Ladrillo 0.2289 unchanged
  - note: AIS 1993-2025: BRICK 2.0 0.061, Ladrillo 0.088 cm, both still within 0.1 cm.
- **E043** [number] anchor: “and BRICK 2.0’s rise is +21.34 (+0.3). Over the shorter”
  - old: “+21.34 (+0.3)”
  - new: “+21.29 (+0.3)”
  - source: deliverables/redline/apply_edits_r6_l27.py L100-124 arithmetic on outputs/postpred_oldbrick_components_timeseries.csv total_p50: mean 2020-24 − mean 1900-04 = 21.293; obs (recalib_targets_ext dang) 21.003 -> +0.29 (May-22 file reproduces 21.342)
  - note: Uses a curly apostrophe in 'BRICK 2.0’s' in the docx.
- **E044** [number] anchor: “observed +7.81 cm, Ladrillo +7.88 (+0.07) and BRICK 2.0 +8.34 (+0.54)”
  - old: “BRICK 2.0 +8.34 (+0.54)”
  - new: “BRICK 2.0 +8.14 (+0.34)”
  - source: same arithmetic: BRICK 2.0 total_p50 mean 2022-24 = 8.141; obs 7.805 -> +0.336 (May-22 file reproduces 8.343)
  - note: Ladrillo +7.88 (+0.07), IGCC +8.21 unchanged.
- **E057** [number] anchor: “With independent observational errors the log-likelihood gain (+1275) dwarfs the charge”
  - old: “(+1275)”
  - new: “(+1528)”
  - source: outputs/ic_ladrillo_vs_brick20_L27.csv obs_iid dlnL = 23.234 − (−1504.384) = 1527.6
  - note: Tony comment 347 (drop this line?) is Marcus's call (NOT APPLIED); the number edit applies either way.
  - docx: comments anchored in this paragraph: 347, 348
- **E058** [number] anchor: “the gain is +60: nearly four times the AIC charge (ΔAIC = +89) and positive on BIC (+26)”
  - old: “the gain is +60: nearly four times the AIC charge (ΔAIC = +89) and positive on BIC (+26)”
  - new: “the gain is +63: more than four times the AIC charge (ΔAIC = +95) and positive on BIC (+32)”
  - source: outputs/ic_ladrillo_vs_brick20_L27.csv ar1_prof dlnL = 62.743 (62.743 / 15 = 4.18, so 'nearly four' becomes 'more than four'); dAIC 95.486; dBIC 32.207
  - docx: comments anchored in this paragraph: 347, 348
- **E059** [number] anchor: “at ρ ≤ 0.95 the BIC margin is +82. Glaciers and Greenland”
  - old: “the BIC margin is +82”
  - new: “the BIC margin is +93”
  - source: outputs/ic_ladrillo_vs_brick20_L27_rho0.95.csv ar1_prof dBIC = 92.833
  - docx: comments anchored in this paragraph: 347, 348
- **E060** [number] anchor: “Glaciers and Greenland are the primary source of the gain (+26 and +30), Antarctica +4.”
  - old: “(+26 and +30), Antarctica +4.”
  - new: “(+26 and +31), thermal expansion +7 and Antarctica −1.”
  - source: outputs/ic_ladrillo_vs_brick20_L27.csv ar1_prof per-series ll_at_fit4_maxdraw, Ladrillo − BRICK 2.0: gsic 1.646 − (−24.376) = 26.02; gis 110.065 − 79.518 = 30.55; steric 10.655 − 3.420 = 7.23; ais 118.039 − 119.099 = −1.06 (sum 62.74). May-22: 26.0 / 29.7 / −0.1 / 3.8
  - note: READING CHANGE: Antarctica now slightly favours BRICK 2.0 at the joint maximising draw, and thermal expansion contributes +7 (it was a tie, −0.1).
  - docx: comments anchored in this paragraph: 347, 348
- **E061** [wording] anchor: “Ladrillo thermal expansion overshoot is attributable to FaIR’s ocean heat.”
  - old: “Ladrillo thermal expansion overshoot is attributable to FaIR’s ocean heat.”
  - new: “Ladrillo's thermal-expansion overshoot comes from the timing of FaIR's ocean heat uptake.”
  - source: handoff_2026-10-01c §1c item 3 (CHANGELOG 2026-10-05b): outputs/diag_te_driver_timing.csv
  - note: Old span includes TONY's insertions 'Ladrillo ', ' is', 'attributable to'.
  - docx: old span overlaps Tony's tracked insertion (partial (36% of old span): ['Ladrillo ', ' is', 'attributable to'])
- **E062** [number] anchor: “(Ladrillo by a factor of 1.22 and BRICK 2.0 by a factor of 1.16)”
  - old: “BRICK 2.0 by a factor of 1.16”
  - new: “BRICK 2.0 by a factor of 1.13”
  - source: outputs/diag_te_rate_attribution_L27.csv block A note 'BRICK 2.0 1.132x; 1993-2025' (regenerated 10-15; the quarantined May-22 copy reads 1.162x); Ladrillo 1.223 unchanged
  - docx: old span overlaps Tony's tracked insertion (partial (52% of old span): ['by a factor of '])
- **E063** [wording] anchor: “This is because FaIR's ocean heat uptake over that period is 1.21–1.27× the observed 0–2000 m products”
  - old: “This is because FaIR's ocean heat uptake over that period is 1.21–1.27× the observed 0–2000 m products the target is built from (IGCC's record ends in 2024).”
  - new: “Over that period FaIR's ocean heat uptake is 1.21–1.27× the observed 0–2000 m products the target is built from (IGCC's record ends in 2024), but a constant scale difference would be absorbed by α. The overshoot comes from timing: FaIR's heat uptake is back-loaded, with a 1900–1949 rate 0.13 of its 1993–2024 rate against 0.24 for the steric target and 0.21 for observed 0–2000 m ocean heat, so one α cannot fit both eras.”
  - source: handoff_2026-10-01c §1c item 3; outputs/diag_te_driver_timing.csv A_era_shape 1900-1949: fair_total_heat 0.1266, target_steric 0.2377, observed_0_2000m_zanna_igcc 0.2067; 1.21–1.27 = outputs/diag_te_rate_attribution_L27.csv block B 1.2148 (IGCC, 1993-2024) / 1.2742 (Cheng, 1993-2025); constant-rescaling no-op: CHANGELOG 2026-10-05b
  - note: Do NOT quote the offline WLS 1.05 as Ladrillo's (handoff warning). The 'within 4%' α clause earlier in this paragraph is item 4 = NOT APPLIED.
- **E064** [wording] anchor: “Over 1993–2024, when FaIR's uptake is 1.21× IGCC's 0–2000 m estimate, that excess has two parts of similar size.”
  - old: “Over 1993–2024, when FaIR's uptake is 1.21× IGCC's 0–2000 m estimate, that excess has two parts of similar size.”
  - new: “Over 1993–2020, when FaIR's uptake is 1.24× IGCC's 0–2000 m estimate, that excess has three parts.”
  - source: handoff_2026-10-01c §1c item 1; outputs/diag_fair_ohc_vs_earth_heat.csv window 1993-2020: fair_over_0_2000 1.2363 = f_deep 1.1073 × f_nonocean 1.0967 × f_residual 1.0180 (IGCC's non-ocean terms end in 2020)
  - note: Answers Tony 362/363 without his suggested sentence (that sentence restates the attribution retracted 10-05).
  - docx: comments anchored in this paragraph: 362, 363
- **E065** [number] anchor: “IGCC's accounting estimates that warming below 2000 m has been about 10% as large”
  - old: “about 10% as large as the 0–2000 m heat uptake, so a full-depth model is expected to run about 1.10×”
  - new: “about 11% as large as the 0–2000 m heat uptake, so a full-depth model is expected to run about 1.11×”
  - source: outputs/diag_fair_ohc_vs_earth_heat.csv 1993-2020 f_deep = igcc_ocean_full-depth 1.18636 / igcc_ocean_0-2000m 1.07136 = 1.107
  - note: Window moves with E064 (1993-2024 gave 1.102).
  - docx: comments anchored in this paragraph: 362, 363
- **E066** [wording] anchor: “The remaining 1.10× is FaIR's full-depth heat uptake exceeding IGCC's full-depth estimate.”
  - old: “The remaining 1.10× is FaIR's full-depth heat uptake exceeding IGCC's full-depth estimate.”
  - new: “A further 1.10× is heat that FaIR books as ocean heat but that goes to land, ice and the atmosphere, about 9% of Earth's heat uptake in IGCC's accounting. Against IGCC's total heat uptake, FaIR is within 2% (1.02×).”
  - source: handoff_2026-10-01c §1c item 1 (RETRACTED attribution, CHANGELOG 2026-10-05); outputs/diag_fair_ohc_vs_earth_heat.csv 1993-2020: f_nonocean 1.0967, nonocean_share 0.0881, f_residual (FaIR / IGCC total) 1.0180
  - docx: comments anchored in this paragraph: 362, 363

### 4.1 Table 5

- **E045** [table] Table 5, row *Independent Gaussian, observational σ*, column *ln L (Ladrillo / BRICK 2.0)*: `−1252.1` → `−1504.4`
  - source: outputs/ic_ladrillo_vs_brick20_L27.csv obs_iid: fit4 ll_max Ladrillo 23.234 / BRICK 2.0 −1504.384; dAIC 3025.24; dBIC 2961.96 (k 42/27 iid, 50/35 AR(1); N 502; AIC = 2k − 2 ln L; BIC = k ln N − 2 ln L)
  - note: Only the BRICK 2.0 half of the ln L cell changes; the Ladrillo half is byte-identical ([TABLE5-INPUT] gate, CHANGELOG 10-15d).
- **E046** [table] Table 5, row *Independent Gaussian, observational σ*, column *ΔAIC*: `+2521` → `+3025`
  - source: outputs/ic_ladrillo_vs_brick20_L27.csv obs_iid: fit4 ll_max Ladrillo 23.234 / BRICK 2.0 −1504.384; dAIC 3025.24; dBIC 2961.96 (k 42/27 iid, 50/35 AR(1); N 502; AIC = 2k − 2 ln L; BIC = k ln N − 2 ln L)
- **E047** [table] Table 5, row *Independent Gaussian, observational σ*, column *ΔBIC*: `+2458` → `+2962`
  - source: outputs/ic_ladrillo_vs_brick20_L27.csv obs_iid: fit4 ll_max Ladrillo 23.234 / BRICK 2.0 −1504.384; dAIC 3025.24; dBIC 2961.96 (k 42/27 iid, 50/35 AR(1); N 502; AIC = 2k − 2 ln L; BIC = k ln N − 2 ln L)
- **E048** [table] Table 5, row *AR(1) + observational σ, ρ ≤ 0.99 (the calibration's bound)*, column *ln L (Ladrillo / BRICK 2.0)*: `180.9` → `177.7`
  - source: outputs/ic_ladrillo_vs_brick20_L27.csv ar1_prof: 240.404 / 177.661; dAIC 95.486; dBIC 32.207 (k 42/27 iid, 50/35 AR(1); N 502; AIC = 2k − 2 ln L; BIC = k ln N − 2 ln L)
  - note: Only the BRICK 2.0 half of the ln L cell changes; the Ladrillo half is byte-identical ([TABLE5-INPUT] gate, CHANGELOG 10-15d).
- **E049** [table] Table 5, row *AR(1) + observational σ, ρ ≤ 0.99 (the calibration's bound)*, column *ΔAIC*: `+89` → `+95`
  - source: outputs/ic_ladrillo_vs_brick20_L27.csv ar1_prof: 240.404 / 177.661; dAIC 95.486; dBIC 32.207 (k 42/27 iid, 50/35 AR(1); N 502; AIC = 2k − 2 ln L; BIC = k ln N − 2 ln L)
- **E050** [table] Table 5, row *AR(1) + observational σ, ρ ≤ 0.99 (the calibration's bound)*, column *ΔBIC*: `+26` → `+32`
  - source: outputs/ic_ladrillo_vs_brick20_L27.csv ar1_prof: 240.404 / 177.661; dAIC 95.486; dBIC 32.207 (k 42/27 iid, 50/35 AR(1); N 502; AIC = 2k − 2 ln L; BIC = k ln N − 2 ln L)
- **E051** [table] Table 5, row *AR(1) + observational σ, ρ ≤ 0.95*, column *ln L (Ladrillo / BRICK 2.0)*: `148.2` → `142.8`
  - source: outputs/ic_ladrillo_vs_brick20_L27_rho0.95.csv ar1_prof: 235.820 / 142.764; dAIC 156.112; dBIC 92.833 (k 42/27 iid, 50/35 AR(1); N 502; AIC = 2k − 2 ln L; BIC = k ln N − 2 ln L)
  - note: Only the BRICK 2.0 half of the ln L cell changes; the Ladrillo half is byte-identical ([TABLE5-INPUT] gate, CHANGELOG 10-15d).
- **E052** [table] Table 5, row *AR(1) + observational σ, ρ ≤ 0.95*, column *ΔAIC*: `+145` → `+156`
  - source: outputs/ic_ladrillo_vs_brick20_L27_rho0.95.csv ar1_prof: 235.820 / 142.764; dAIC 156.112; dBIC 92.833 (k 42/27 iid, 50/35 AR(1); N 502; AIC = 2k − 2 ln L; BIC = k ln N − 2 ln L)
- **E053** [table] Table 5, row *AR(1) + observational σ, ρ ≤ 0.95*, column *ΔBIC*: `+82` → `+93`
  - source: outputs/ic_ladrillo_vs_brick20_L27_rho0.95.csv ar1_prof: 235.820 / 142.764; dAIC 156.112; dBIC 92.833 (k 42/27 iid, 50/35 AR(1); N 502; AIC = 2k − 2 ln L; BIC = k ln N − 2 ln L)
- **E054** [table] Table 5, row *AR(1) + observational σ, ρ ≤ 0.90*, column *ln L (Ladrillo / BRICK 2.0)*: `106.9` → `95.2`
  - source: outputs/ic_ladrillo_vs_brick20_L27_rho0.9.csv ar1_prof: 227.003 / 95.241; dAIC 233.523; dBIC 170.244 (k 42/27 iid, 50/35 AR(1); N 502; AIC = 2k − 2 ln L; BIC = k ln N − 2 ln L)
  - note: Only the BRICK 2.0 half of the ln L cell changes; the Ladrillo half is byte-identical ([TABLE5-INPUT] gate, CHANGELOG 10-15d).
- **E055** [table] Table 5, row *AR(1) + observational σ, ρ ≤ 0.90*, column *ΔAIC*: `+210` → `+234`
  - source: outputs/ic_ladrillo_vs_brick20_L27_rho0.9.csv ar1_prof: 227.003 / 95.241; dAIC 233.523; dBIC 170.244 (k 42/27 iid, 50/35 AR(1); N 502; AIC = 2k − 2 ln L; BIC = k ln N − 2 ln L)
- **E056** [table] Table 5, row *AR(1) + observational σ, ρ ≤ 0.90*, column *ΔBIC*: `+147` → `+170`
  - source: outputs/ic_ladrillo_vs_brick20_L27_rho0.9.csv ar1_prof: 227.003 / 95.241; dAIC 233.523; dBIC 170.244 (k 42/27 iid, 50/35 AR(1); N 502; AIC = 2k − 2 ln L; BIC = k ln N − 2 ln L)

### 4.2 Fig. 3 caption

- **E067** [caption] anchor: “Figure 3. Ladrillo compared against BRICK 2.0, FACTS and MAGICC-SLR across the seven van Vuuren scenarios at 2300”
  - old: “by component. Each of FACTS's unique modules is shown; the Total panel shows its seven workflow totals as one bracket spanning their medians (thin line: the union of their 5–95%). FACTS's modules that are not climate-driven are omitted.”
  - new: “by component, relative to the 1995–2014 mean (2005 for FACTS). FACTS is shown only for its modules that are climate-driven at 2300 (glaciers, thermal expansion and land-water storage; Sect. 4.2). Its Greenland and Antarctic modules and its workflow totals are omitted, so the Total panel has no FACTS bracket.”
  - source: notes/tony_tw2_triage_2026-10-15.md §5; python/ladrillo_figs.py FACTS_CLIMATE_DRIVEN[2300] = {ar5glaciers, tlm, ssp-lws} (workflow totals wf* excluded by facts_module_ok); figures/paper/model_comparison_components_vv_L27_2300.caption.txt; emulandice workflows end in 2100 (Sect. 4.2)
  - note: TONY's tracked insertion (2026-10-15T11:40) replaced the original 'The same comparison at 2300.' with the 2100 caption's text, which is wrong at 2300 twice (no emulandice workflows past 2100; no FACTS total past 2100 under 09-12c). The last sentence ('FACTS's modules that are not climate-driven are omitted.') is original text; the new wording states it concretely. The baseline clause mirrors his accurate Fig. 2 insertion.
  - docx: old span overlaps Tony's tracked insertion (partial (76% of old span): ["by component. Each of FACTS's unique modules is shown; the Total panel shows its seven workflow totals as one bracket spanning their medians (thin line: the union of their 5–95%)."])

### 4.2 Fig. 5 caption

- **E068** [caption] anchor: “cumulative glacier melt (b), and the melt rate on the peak-and-decline pathways (c)”
  - old: “the melt rate on the peak-and-decline pathways (c)”
  - new: “the melt rate on the four peak-and-decline pathways, Very Low, Low-to-Negative, Medium-to-Low and High-to-Low (c)”
  - source: Tony comment 389; python/plot_vv_gsic_wr_vs_ladrillo.py panel (c) plots DECLINE = markers with decline flag in python/ladrillo_figs.py VV_SET: vvVL, vvLN, vvML, vvHL
  - docx: comments anchored in this paragraph: 389, 390
- **E069** [number] anchor: “Regrowth of about 0.1 cm occurs on Low-to-Negative and Medium-to-Low as temperatures drop”
  - old: “Regrowth of about 0.1 cm occurs on Low-to-Negative and Medium-to-Low as”
  - new: “Regrowth of about 0.05 cm occurs on Low-to-Negative as”
  - source: Computed here (no committed receipt): fixed-arm glacier median path, outputs/scope_slr_fairunc_paths_<m>_spliced_L27_tap4p69K_V5p64m_tau800.csv (component glaciers, arm fixed = the Fig. 5 data, ARM='fixed' in plot_vv_gsic_wr_vs_ladrillo.py): max(2015-2300) − value(2300) = 0.053 cm vvLN (peak 2230), 0.000 vvML and every other marker
  - note: The 10-08k published-emissions vv forcing removed Medium-to-Low regrowth (fixed and joint). Tony comment 390 ('Fixed arm.') is Marcus's call.
  - docx: comments anchored in this paragraph: 389, 390

### 4.2 Fig. 6 caption

- **E070** [number] anchor: “(High − Very Low GMST gap 1.7/3.1/5.5 K at the three horizons)”
  - old: “1.7/3.1/5.5 K”
  - new: “1.6/3.1/5.4 K”
  - source: outputs/vv_responsiveness_L27.csv dT_K (cls model, FaIR rows): 1.6488 / 3.0948 / 5.4326 K (figures/paper/vv_responsiveness_L27.caption.txt prints 1.65/3.09/5.43)
  - note: Moved with the 10-08k published-emissions vv forcing, not the BRICK swap.
- **E071** [number] anchor: “MAGICC-SLR responds to its own climate (2.0/3.6/5.9 K)”
  - old: “(2.0/3.6/5.9 K)”
  - new: “(2.0/3.6/5.8 K)”
  - source: outputs/vv_responsiveness_L27.csv dT_K MAGICC-SLR rows: 1.9977 / 3.5788 / 5.8273 K

### 4.2 Future projections

- **E072** [number] anchor: “which gives a High-to-Low Greenland median of 47 cm at 2300”
  - old: “median of 47 cm at 2300”
  - new: “median of 46 cm at 2300”
  - source: outputs/vvz_paper_number_diff_20261008.csv row 'FACTS FittedISMIP Greenland vvHL 2300, default extrapolation (cm rel 2005)' = 46 (10-07 diff 46.4; FACTS not re-run since)
  - note: 112 cm holds (same file).
  - docx: comments anchored in this paragraph: 393

### 4.3 High scenarios

- **E073** [number] anchor: “the three models are fairly similar at 2100 (Ladrillo 71 cm, BRICK 2.0 82 cm, MAGICC-SLR 62 cm)”
  - old: “(Ladrillo 71 cm, BRICK 2.0 82 cm,”
  - new: “(Ladrillo 73 cm, BRICK 2.0 79 cm,”
  - source: outputs/brick20_swap_paper_number_diff_20261015.csv rows 'Ladrillo total 2100' 73.05, 'BRICK 2.0 total 2100' 78.66 (vvH joint); MAGICC-SLR 62.23 (outputs/vv_model_comparison_L27.csv) unchanged at rounding
  - docx: old span overlaps Tony's tracked insertion (partial (9% of old span): [' cm']); comments anchored in this paragraph: 400, 407
- **E074** [number] anchor: “By 2300, Ladrillo and BRICK 2.0 sit together (422 and 414 cm, median) well below MAGICC-SLR (570 cm)”
  - old: “(422 and 414 cm, median) well below MAGICC-SLR (570 cm)”
  - new: “(427 and 383 cm, median) well below MAGICC-SLR (567 cm)”
  - source: outputs/brick20_swap_paper_number_diff_20261015.csv rows 'Ladrillo total 2300' 426.91, 'BRICK 2.0 total 2300' 382.72; MAGICC-SLR vvH total 2300 567.44 (outputs/vv_model_comparison_L27.csv; MAGICC re-run on the published emissions 10-08k, was 569.8)
  - note: READING: 'sit together' with a 44 cm gap (Ladrillo now above BRICK 2.0) is Marcus's call; see NOT APPLIED N10.
  - docx: comments anchored in this paragraph: 400, 407
- **E075** [number] anchor: “and the gap is due to Antarctica: 244 and 248 cm against MAGICC's 382”
  - old: “244 and 248 cm against MAGICC's 382”
  - new: “249 and 218 cm against MAGICC's 380”
  - source: outputs/brick20_swap_paper_number_diff_20261015.csv rows 'Ladrillo AIS 2300' 249.47, 'BRICK 2.0 AIS 2300' 218.10; MAGICC-SLR vvH AIS 2300 379.65 (vv_model_comparison_L27.csv)
  - note: 'gap is due to Antarctica' holds: MAGICC − Ladrillo total 140 cm of which AIS 130; MAGICC − BRICK 2.0 total 185 of which AIS 162.
  - docx: comments anchored in this paragraph: 400, 407
- **E076** [number] anchor: “actually decreases their totals by 15–22 cm (to 407 and 392)”
  - old: “by 15–22 cm (to 407 and 392)”
  - new: “by 17–20 cm (to 410 and 363)”
  - source: outputs/brick20_swap_paper_number_diff_20261015.csv rows 'Ladrillo on MAGICC climate' 409.71, 'BRICK 2.0 on MAGICC climate' 362.74, decreases 17.20 / 19.98
  - note: 'mainly due to thermal expansion' holds: TE climate term −18.4 (Ladrillo) / −18.1 cm (BRICK 2.0), outputs/vv_climate_swap_L27.csv vvH 2300. The common-draw swap gives Ladrillo 409.81, also 410.
  - docx: comments anchored in this paragraph: 400, 407
- **E077** [number] anchor: “0.0104, 0.0036 in BRICK 2.0's posterior), which is why the two Antarctic spreads are alike”
  - old: “0.0104, 0.0036 in BRICK 2.0's posterior”
  - new: “0.0104, 0.0035 in BRICK 2.0's posterior”
  - source: data/MimiBRICK/parameters_subsample_sneasybrick_zenodo20592337.csv antarctic_lambda over all 10,000 rows: mean 0.01036, sd 0.00354 (the May-22 file gives 0.0104 / 0.00364, reproducing the printed values with the same all-rows convention)
  - note: Ensemble values (0.0104, 0.0036) unchanged.
  - docx: comments anchored in this paragraph: 411, 412, 413
- **E078** [number] anchor: “(5–95% widths of 274 and 332 cm at 2300)”
  - old: “274 and 332 cm”
  - new: “268 and 307 cm”
  - source: outputs/brick20_swap_paper_number_diff_20261015.csv rows 'AIS 5-95% width 2300, Ladrillo' 268.42, 'BRICK 2.0' 307.23 (vvH joint)
  - note: 'alike' still reasonable (Ladrillo narrower).
  - docx: comments anchored in this paragraph: 411, 412, 413

### 4.3 Low scenarios

- **E079** [number] anchor: “For Very Low its 2300 total median is 60 cm, above only MAGICC-SLR's 46 cm and below BRICK 2.0's 81.”
  - old: “median is 60 cm, above only MAGICC-SLR's 46 cm and below BRICK 2.0's 81.”
  - new: “median is 61 cm, above only MAGICC-SLR's 46 cm and below BRICK 2.0's 80.”
  - source: outputs/brick20_swap_paper_number_diff_20261015.csv rows 'Very Low total 2300' Ladrillo 61.34, BRICK 2.0 79.55; MAGICC-SLR 46.40 (vv_model_comparison_L27.csv)
- **E080** [number] anchor: “(2300 total 5–95% width 67 cm against Ladrillo's 137 cm and BRICK 2.0's 182 cm)”
  - old: “width 67 cm against Ladrillo's 137 cm and BRICK 2.0's 182 cm”
  - new: “width 68 cm against Ladrillo's 166 cm and BRICK 2.0's 221 cm”
  - source: outputs/brick20_swap_paper_number_diff_20261015.csv rows 'Very Low total 2300 width' Ladrillo 166.499, BRICK 2.0 220.879; MAGICC-SLR p95−p05 = 68.45 (vv_model_comparison_L27.csv; was 67.3 before the 10-08k MAGICC re-run)
  - note: Ladrillo 166.499 sits 0.001 cm below a rounding boundary (U05). Orderings in the paragraph hold: Ladrillo narrower than BRICK 2.0 on every component (vvVL 2300 widths glaciers 8.7/15.5, GIS 9.8/13.7, AIS 139/196, TE 23.9/24.9) and than FACTS ar5glaciers 23.6 / tlm 26.0; MAGICC narrowest on AIS 43, TE 16.6, total 68.
  - docx: old span overlaps Tony's tracked insertion (partial (10% of old span): ['cm ', ' cm'])

### 4.3 Peak-and-decline scenarios

- **E081** [number] anchor: “it reaches only 0.11 cm in the Low-to-Negative scenario and 0.10 cm in Medium-to-Low”
  - old: “it reaches only 0.11 cm in the Low-to-Negative scenario and 0.10 cm in Medium-to-Low, and is essentially nil in the other scenarios.”
  - new: “it reaches only 0.08 cm in the Low-to-Negative scenario and is nil in the other scenarios.”
  - source: outputs/verify_magicc_regrowth_attribution_L27.csv (joint-arm median path, committed e567ea7 = 10-08k): ladrillo_fair_regrowth_cm vvLN 0.0834, every other marker 0.0 (was 0.112 / 0.096 in TW1; 0.102 / 0.092 after 10-07)
  - note: Medium-to-Low regrowth disappeared with the 10-08k published-emissions vv forcing (its tail is warmer). Old span includes TONY's insertions 'in the ', 'scenario ', 'in'.
  - docx: old span overlaps Tony's tracked insertion (partial (15% of old span): ['in the ', 'scenario ', 'in', 'in']); comments anchored in this paragraph: 428, 438
- **E082** [number] anchor: “Driven instead by MAGICC's colder climate, the same module regrows 1.95 cm at Low-to-Negative.”
  - old: “regrows 1.95 cm”
  - new: “regrows 1.91 cm”
  - source: outputs/verify_magicc_regrowth_attribution_L27.csv vvLN ladrillo_magiccclim_regrowth_cm 1.9097
  - note: Tony 438 (move this figure to the next paragraph) is wording, Marcus's.
  - docx: comments anchored in this paragraph: 428, 438
- **E083** [number] anchor: “MAGICC regrows 8.58 cm as compared to Ladrillo's 0.11 cm”
  - old: “MAGICC regrows 8.58 cm as compared to Ladrillo's 0.11 cm”
  - new: “MAGICC regrows 8.55 cm as compared to Ladrillo's 0.08 cm”
  - source: outputs/verify_magicc_regrowth_attribution_L27.csv vvLN magicc_own_regrowth_cm 8.5467 (MAGICC re-run 10-08k), ladrillo_fair_regrowth_cm 0.0834
  - note: 'as compared to ' is TONY's insertion. Tony 439 ('MAGICC's glaciers') is Marcus's wording call.
  - docx: old span overlaps Tony's tracked insertion (partial (27% of old span): ['as compared to ']); comments anchored in this paragraph: 439
- **E084** [number] anchor: “driving Ladrillo's module with MAGICC's climate decreases the gap by only 1.84 cm”
  - old: “by only 1.84 cm”
  - new: “by only 1.83 cm”
  - source: outputs/verify_magicc_regrowth_attribution_L27.csv vvLN climate_part_cm 1.8263; structure_share 0.784 so '¾ … ¼' holds
  - docx: comments anchored in this paragraph: 439

### 5 Conclusions

- **E085** [label] anchor: “We present Ladrillo v1.0, a modelling framework for global sea-level change”
  - old: “Ladrillo v1.0”
  - new: “Ladrillo v1.3”
  - source: Ladrillo.jl tag v1.3.0 (CITATION.cff, README 'Versions' v1.3)
- **E086** [number] anchor: “yields reductions of up to 31 cm by 2300 (the changes are largest for SSP2-4.5 and the High-to-Low peak-and-decline scenario)”
  - old: “up to 31 cm by 2300 (the changes are largest for SSP2-4.5 and the High-to-Low peak-and-decline scenario)”
  - new: “up to 18 cm by 2300 (the change is largest for the High-to-Low peak-and-decline scenario)”
  - source: outputs/brick20_swap_paper_number_diff_20261015.csv rows 'Concl.': BRICK 2.0 − Ladrillo AIS 2300 joint, SSP2-4.5 6.30, High-to-Low 18.17, max over 3 SSPs + 7 markers 18.17 (all 10: ssp126 −3.8, ssp245 6.3, ssp585 −47.1, VL −2.5, LN 1.1, L −3.7, ML −0.1, M −7.2, HL 18.2, H −31.4)
  - note: ⛔ READING CHANGE (Marcus's call, N09): with the Zenodo posterior Ladrillo's 2300 Antarctic median is now HIGHER than BRICK 2.0's in seven of ten scenarios, by up to 47 cm (SSP5-8.5) and 31 cm (High). 'reductions of up to 18 cm' is numerically right but one-sided.

### Appendix A Table A2

- **E087** [table] Table A2, row *14*, column *identified combination (loadings)*: `0.73 ln P₀ − 0.54 slope` → `0.73 ln P₀ − 0.53 slope`
  - source: outputs/ladrillo_table_a2_L27_sub10k.md (from diag_ais_block_pca_L27_sub10k.csv; CHANGELOG 2026-10-07d); handoff_2026-10-08b §3 item 3
  - note: Minimal span inside the cell: '0.54' -> '0.53' (unique in the cell).
- **E088** [table] Table A2, row *12*, column *R̂*: `1.018` → `1.017`
  - source: outputs/ladrillo_table_a2_L27_sub10k.md
  - note: The md's caption says '1900–2026 record'; the draft's '1900–2025' was left (U08).

### Code and data availability

- **E089** [label] anchor: “is archived at Zenodo under DOI [to be assigned at submission]; development continues at [repository URL]”
  - old: “Ladrillo v1.0 —”
  - new: “Ladrillo v1.3 (Ladrillo.jl, git tag v1.3.0) —”
  - source: Ladrillo.jl tags v1.0.0…v1.3.0 (git -C ~/Documents/2026/CodeProjects/Ladrillo tag -l); CITATION.cff 'The version the GMD paper reports is the git tag v1.3.0'
  - note: Repository URL left as the placeholder: msarofim/Ladrillo.jl is PRIVATE until Marcus makes it public (N12).
- **E090** [citation] anchor: “MimiBRICK v2.0.0 is available at https://github.com/raddleverse/MimiBRICK.jl (tag v2.0.0, commit 11b2dff; Wong et al., 2022).”
  - old: “(tag v2.0.0, commit 11b2dff; Wong et al., 2022).”
  - new: “(tag v2.0.0, commit 11b2dff; Wong et al., 2022). The BRICK 2.0 comparison uses the BRICK parameters of the joint SNEASY–BRICK posterior subsample published with MimiBRICK v2.0.0 (parameters_subsample_sneasybrick.csv, 10,000 draws; Wong et al., 2026, https://doi.org/10.5281/zenodo.20592337).”
  - source: Zenodo record 10.5281/zenodo.20592337 ('Model output supporting MimiBRICK v2.0.0', 2026-06-08, CC-BY-4.0; metadata read from the Zenodo API 2026-10-15); Ladrillo README 'BRICK 2.0 posterior'; CHANGELOG 2026-10-15d
  - note: Brief item 6. No 'post-PR#93', 'personal communication' or unpublished-subsample wording exists in TW2's accepted text, so nothing needs removing.

### References

- **E091** [citation] anchor: “Wong, T. E., Rennels, L., Errickson, F., Srikrishnan, V., Bakker, A., Keller, K., and Anthoff, D.: MimiBRICK.jl: A Julia package”
  - INSERT NEW PARAGRAPH after the anchor paragraph: “Wong, T. E., Rennels, L., Errickson, F., Srikrishnan, V., Bakker, A., Keller, K., and Anthoff, D.: Model output supporting MimiBRICK v2.0.0, Zenodo [data set], https://doi.org/10.5281/zenodo.20592337, 2026.”
  - source: Zenodo API https://zenodo.org/api/records/20592337: title 'Model output supporting MimiBRICK v2.0.0'; creators Wong, Tony; Rennels, Lisa; Errickson, Frank; Srikrishnan, Vivek; Bakker, Alexander; Keller, Klaus; Anthoff, David; published 2026-06-08; Dataset; CC-BY-4.0
  - note: INSERT a NEW reference paragraph immediately after the anchor paragraph (Wong et al., 2022), copying its paragraph style. Cited by E007 and E090. 'T. E.' follows the draft's style for Tony Wong (Zenodo lists 'Wong, Tony').

## Figures to replace (not text edits)

All six images in TW2 differ (md5) from the current paper renders in `SLR-RFF-BRICK/figures/paper/`:

| figure | current file | rendered | why it moved |
|---|---|---|---|
| Fig. 1 | `hindcast_components_L27.png` | 10-15 | BRICK 2.0 hindcast on the Zenodo posterior |
| Fig. 2 | `model_comparison_components_vv_L27_2100.png` | 10-15 | CMIP7 vv (10-07), published-emissions vv + conditioning (10-08k), BRICK 2.0 swap |
| Fig. 3 | `model_comparison_components_vv_L27_2300.png` | 10-15 | same |
| Fig. 4 | `future_components_vv_L27_joint.png` | 10-15 | same |
| Fig. 5 | `vv_gsic_ladrillo_L27_2300.png` | 10-08 18:24 | 10-07 and 10-08k vv forcing (glaciers only; no BRICK) |
| Fig. 6 | `vv_responsiveness_L27.png` | 10-15 | all of the above |

## Checked, no edit needed

- Abstract: glaciers 79% (79.41), Greenland 72% (71.99); '15 more parameters'.
- Intro: Greenland '(3×)' (44.44/16.08 = 2.76); Antarctic 'less sensitive … on shorter timescales' (2100: 22.7 vs 29.2 cm); definition of BRICK 2.0 as the MimiBRICK v2.0.0 release (accurate).
- 2.2.2: 0.7 / 7.6 cm (conditioned joint arm 0.664 / 7.565); ratios 4.4 / 2.4 (joint 4.45 / 2.35); 5.7.
- 2.2.3: 17%, 20 cm, 4%; λ ensemble mean/sd 0.0104 / 0.0036; Table A3 'projection: joint draws'.
- 2.2.5: land water 8.8 cm by 2300 (8.814 in both models, every scenario).
- 3.1: IMBIE −2.6σ, −0.38 cm, +0.44 cm, 0.50 / 0.13 cm (Ladrillo-only).
- 3.2: hindcast refit 0.005 cm; R̂ / ESS (chain statistics).
- 3.3: 'reproduces BRICK 2.0 bit-for-bit' (gate re-passed on the Zenodo posterior, CHANGELOG 10-15d).
- 4.1: obs +21.00 / +7.81, Ladrillo +20.41 (−0.6) / +7.88 (+0.07), IGCC +8.21; Ladrillo biases +1.23/1.37 and +0.22/0.77; non-closure −0.31/+0.17; Ladrillo TE ×1.22; 1.21–1.27×; the 'every ice component … except' sentence (glaciers 1950–1992 and Antarctica 1993–2025 are still the only exceptions); 'both within 0.1 cm' (0.061 / 0.088).
- 4.1 P279 'BRICK 2.0 runs on its own published posterior': now literally true (no edit; Tony 326 on this paragraph is Marcus's).
- Table 5 caption (k 42/27, 50/35; 10,000 draws per model); the Ladrillo half of every ln L cell.
- 4.2: FACTS 112 cm; '200 of the same configurations'.
- 4.3: MAGICC-SLR 62 cm (62.23) and 46 cm (46.40); '¾ … ¼' (structure share 0.784); 'mainly due to thermal expansion' (TE climate terms −18.4 / −18.1 cm); Very Low ordering and 'narrower on every component' claims.
- Author contributions 'whose published posterior … are used here': now accurate.
- No 'post-PR#93', 'Tony Wong subsample', 'personal communication' or 'unpublished' wording about the BRICK 2.0 posterior exists in TW2's accepted text (the only 'pers. comm.' is Dangendorf's, Table 3 note 21).

## NOT APPLIED (Marcus's calls)

- **N01 — handoff 10-01c §1c item 4, the α comparison.** Sect. 2.2.4 (“The posterior median of α is 0.167 (5–95% 0.148–0.186), within 4% of the value the 0–2000 m observations imply”) and Sect. 4.1 (“Despite Ladrillo's expansion coefficient being within 4% of the value implied by the observations”). α multiplies FaIR's total Earth heat uptake while the obs-implied α is on a 0–2000 m basis; re-derive on matched scopes before keeping. (Current `diag_te_rate_attribution_L27.csv` block C: model/obs-implied 0.960 Cheng, 1.006 IGCC.)
- **N02 — item 7.** Lin et al. 2026 (Nat. Geosci., ISMIP6 emulator) 2100 Antarctic comparison and fast-dynamics attribution (Sect. 4.3 High / 2.2.3); disclose the 2002–2021 Antarctic rate deficit (Sect. 3.1 'IMBIE 2026 as an out-of-sample check'; compute per-draw rates first); thank Frank Errickson (Acknowledgements, 'The authors would like to thank Alexander Nauels, …').
- **N03 — item 8.** State the next-version direction (calibrate TE on an observed OHC driver, splice FaIR's future anomaly): Sect. 4.1 TE paragraphs or Conclusions ('Remaining mismatches of historical thermal expansion are shown to be a result of the FaIR OHC output, not Ladrillo.').
- **N04 — Tony 390** (Fig. 5 caption 'Fixed arm.'; one ensemble throughout). E068/E069 keep the fixed arm and use the fixed-arm number.
- **N05 — Tony 347** (drop the independent-errors sentence in Sect. 4.1, 'With independent observational errors the log-likelihood gain … dwarfs the charge for 15 parameters'). E057 updates its number (+1275 → +1528) either way.
- **N06 — Tony 326** (Sect. 4.1 'Ladrillo uses the observed LWS time series directly, …': leave out or move to Methods).
- **N07 — Tony 367** (Sect. 4.2 'Bars are 17–83% (thick) and 5–95% (thin).' into the captions).
- **N08 — Tony 364** (joint-arm reminder; his tracked insertion ', which jointly samples uncertainty in both climate from FaIR and sea level from Ladrillo' in Sect. 4.2).
- **N09 — Conclusions reading.** E086 makes the number right (up to 18 cm, largest for High-to-Low; SSP2-4.5 is now 6 cm), but the sentence is one-sided: Ladrillo's 2300 Antarctic median is now HIGHER than BRICK 2.0's in seven of ten scenarios (SSP5-8.5 +47 cm, High +31, Medium +7, Low +4, SSP1-2.6 +4, Very Low +3, Medium-to-Low +0.05). Alternative for Marcus: 'and changes the 2300 Antarctic median relative to BRICK 2.0 by −18 cm (High-to-Low) to +47 cm (SSP5-8.5)'.
- **N10 — Sect. 4.3 High 'Ladrillo and BRICK 2.0 sit together'** (427 vs 383 cm now, Ladrillo above; both still 140–185 cm below MAGICC-SLR's 567).
- **N11 — Intro 'equal sensitivity'.** E006 applies the minimal factual fix ('similar … (about 1.1×)'; AIS 1.14, TE 1.07); the phrasing is Marcus's.
- **N12 — Code availability placeholders:** Ladrillo's Zenodo DOI and '[repository URL]' (msarofim/Ladrillo.jl is private until Marcus makes it public).
- **N13 — Tony's other prose comments** (triage §4): 16 (abstract numbers), 375, 376, 407, 411, 428, 438, 439; and 400 (FACTS among the High-scenario numbers at 2100: yes if wanted, wf1f/wf2f separately; not at 2300).

## UNCERTAIN (not sourced; no number guessed)

- **U01 — Table 2, BRICK 2.0 glacier inventory '37.7 (28–48)' and note 7 '…reduced by 4.0 cm of melt by 2000'.** These rest on `outputs/diag_brick_gsic_melt_1850_2000.csv` (09-12, May-22 posterior), which the 10-15 swap did NOT re-run. The v0 half holds on the Zenodo file (glaciers_v0 median 41.5 cm, 5–95% 32.0–51.8, so 'initial volume 42 cm (5–95% 32–52)' stands). The 1850→2000 melt and the remaining-at-2000 quantiles need `julia/diag_brick_gsic_melt_1850_2000.jl` re-run on `parameters_subsample_sneasybrick_zenodo20592337.csv` (precip_log=false). Not computable from `postpred_oldbrick` (starts in 1900).
- **U02 — Fig. 5 caption regrowth (E069, 0.05 cm).** Computed here from the fixed-arm glacier median path in the canonical paths files (max over 2015–2300 minus the 2300 value); there is no committed receipt for the fixed-arm figure. The joint-arm receipt (`verify_magicc_regrowth_attribution_L27.csv`) gives 0.08 cm.
- **U03 — Descriptions of BRICK 2.0's calibration data** (Sect. 2.2.3 'BRICK 2.0's Antarctic likelihood is based on IMBIE data spanning 1992–2017'; Sect. 3.1 'BRICK 2.0's CSIRO reconstruction, the 2015 update of Church and White, 2011'). They describe the v2.0.0-tagged calibration code. Whether the Zenodo posterior was produced by that code is unconfirmed (Tony mentioned Wang et al. 2024 GMSL; the tag has no Wang file; triage §1). Ask Tony before submission.
- **U04 — ΔAIC at ρ ≤ 0.99 is 95.486**: '+95' (E004, E050, E058). The .md prints 95.5; re-rounding that would wrongly give 96.
- **U05 — Very Low 2300 width, Ladrillo 166.499 cm** rounds to 166 but sits 0.001 cm below the rounding boundary (E080).
- **U06 — Reference E091 author style:** Zenodo lists 'Wong, Tony'; the draft's style 'Wong, T. E.' is used. Title, creators, date and DOI were read from the Zenodo API on 2026-10-15.
- **U07 — Conditioning sentence (E010) quotes no effect size.** The 10-08e estimate (medians ≤ 0.23 cm, p95 ≤ 3.8 cm) was measured before the 10-08k vv forcing change; it holds for the SSP cells (reproduced bit-for-bit, [CONDITIONED-PREDICTED]) but was not re-measured for the vv markers. BRICK 2.0 is not conditioned (CHANGELOG 10-08m).
- **U08 — Table A2 caption:** `ladrillo_table_a2_L27_sub10k.md` says 'the 1900–2026 record'; the draft says '1900–2025', consistent with the rest of the paper. Left unchanged.
- **U09 — Runtime sentence** (Conclusions, '6.3 against 5.1 ms'): not re-measured on the Zenodo posterior (CHANGELOG 10-15d lists it as not re-run). Per-draw time should not depend on parameter values, but this is unmeasured.
- **U10 — Sect. 4.2 'the same pairing of posterior draws to configurations'.** The BRICK 2.0 joint arm has 1,000 draws and Ladrillo's 1,998 (2,000 minus the 2 conditioned); the pairing gate is keyed by draw, so pairing holds draw by draw, but the counts differ.

## Outside the brief: things in TW2 that look wrong

- Sect. 4.2: 'to represent climate uncer.' is truncated (inside Tony's insertion ' to represent climate uncer').
- Sect. 2.2.1: equation placeholder 'In Equations 1 and 2, the parameters are: a, [give description and units]; b, [give description and units]; etc…' (Tony's insertion).
- Sect. 2.2.3: '(REF?)' twice and '(REF Wong et al 2017)' (Tony's insertions).
- Sect. 4.1: a paragraph break mid-sentence ('… We note that ' / 'the non-closure in the observational budget is small …').
- Sect. 4.1: 'The improvement in model fidelity with respect to the observations are largest' (are → is).
- Sect. 3.1: 'compared to data as an type of “out-of-sample” validation' (an → a).
- Conclusions: 'for a 10,000-draw ensembles' (Tony's insertion 'ensembles ').
- Sect. 2.2.3: 'The parameter’s impacts on projections is strongly scenario-dependent'.
- Sect. 3.2: 'using the mean times series' (times → time).
- Fig. 2 caption (Tony's insertion): 'relative to 1995-2014 mean' (hyphen and missing 'the').
- Repo, not paper: `outputs/ic_ladrillo_vs_brick20_L27*.md` still says the steric row is 'a tie by construction'; on the Zenodo posterior it is +7.2 (ρ ≤ 0.99).
