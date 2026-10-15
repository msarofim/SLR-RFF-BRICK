# Tony's TW2 pass and his BRICK-posterior answer: triage (2026-10-15)

Source: `deliverables/GMD.Ladrillo.v1_forTonyreview_TW2.docx` (10-15 16:33). Read only; the docx was not edited.
- TW2 = TW1's 54 comments, all still present, plus **24 new comments** (10-14 / 10-15) and **119 new tracked edits**
  (82 insertions, 37 deletions), carrying his pass through Results and Discussion.
- Extraction scripts (read-only, lxml): session scratchpad `extract_comments.py`, `comment_paras.py`.
- This triage supplies receipts and flags. Replies to Tony and all prose are Marcus's.

## 1. The BRICK 2.0 posterior (Tony's email, 10-15)

Tony: the May-22 file was a work in progress; the Zenodo v2.0.0 set is "probably the best stable version to use and can
cite" and "shouldn't be TOO far off". Likely differences: fixed seeds, explicit normalization periods, and perhaps
Wang et al. (2024) GMSL in place of Church & White.

**Our 10-08 measurement disagrees with "not too far off" for thermal expansion** (SLR CHANGELOG 2026-10-08h).
- On our FaIR forcing (1,000 draws each), SSP2-4.5 TE is 6.6 / 15.2 cm at 2100 / 2300 with the Zenodo file, against
  19.4 / 44.7 cm with ours. The TE hindcast RMSE is 1.97 vs 0.52 cm.
- Glaciers and Greenland agree within ~15 % on RMSE; AIS within ~7 % at 2100 / 2300.

**The ratio has a specific signature.**
- `thermal_alpha` median 0.054 (Zenodo) vs 0.158 (ours): ratio 0.34.
- TE projection ratio: 0.34 at 2100 and 0.34 at 2300.
- MimiBRICK's TE is linear in ocean heat (α × ΔOHC), so the Zenodo α is what fits observed TE when the ocean-heat
  driver's changes are about 2.9× larger than FaIR's.
- MimiBRICK v2.0.0's calibration is the coupled SNEASY/DOECLIM-BRICK fit (tag `v2.0.0`,
  `src/calibration/create_log_posteriors/create_log_posterior_sneasybrick.jl`). Its TE is driven by DOECLIM's modelled
  ocean heat, constrained to Gouretski 0–3000 m (`calibration_helper_functions.jl:95`). Our arm drives the same TE
  module with FaIR's OHC.
- Hypothesis: α is calibrated in DOECLIM's ocean-heat units, and that is about 2.9× off FaIR's ΔOHC. If so, the Zenodo
  posterior cannot be transferred to an external OHC driver without a scale step.
- A normalization-period difference shifts a baseline and cannot produce a proportional 3× gap at both 2100 and 2300.
  Seeds cannot either.
- Not tested. Two tests would separate it:
  1. Run the Zenodo draws in their own coupled SNEASY-BRICK hindcast and check TE against observations. A good fit
     there plus a bad fit on FaIR means a driver-scale mismatch.
  2. Compare DOECLIM's 1900–2020 ΔOHC under those draws with FaIR's. The driver-scale hypothesis predicts a ratio near
     2.9.
- Ask Tony directly what ocean-heat driver and units the v2.0.0 TE was calibrated against.

**Wang et al. (2024).** The `v2.0.0` tag calibrates GMSL to Church & White (`CSIRO_Recons_gmsl_yr_2015.csv`,
normalized 1961–1990) and contains no Wang file. If the Zenodo posterior used Wang 2024, it came from code after the
tag, and the code and posterior would need to be cited as a matched pair.

**Decision for Marcus.**
- (a) Ask Tony to publish the May-22 file (it has a sha256 and the paper's numbers rest on it).
- (b) Move the BRICK 2.0 arm to the Zenodo file. Every BRICK 2.0 number in the GMD paper and the pulse paper moves;
  TE moves about 3×. The deferred conditioning rerun could ride with it.
- (c) Hold until test 1 or 2 above, or Tony's answer on the driver, says whether the Zenodo α is usable with FaIR
  OHC at all.
- (c) costs the least and protects against adopting a posterior that does not fit our driver.

## 2. New comments: questions with a factual answer (receipts)

| # | Tony asks | Answer | Receipt |
|---|---|---|---|
| 362, 363 | "1.21" vs "1.10 + 1.10" is confusing; suggests "the remaining high bias is due to FaIR's full-depth uptake overestimating IGCC's full-depth value" | ⛔ His suggested sentence restates the attribution RETRACTED on 10-01. The queued correction replaces the paragraph: the remaining ~1.10× is heat FaIR books as ocean that goes to land, ice and air (~9 % of Earth's uptake); against IGCC's total, FaIR is within 2 % over 1993–2020; window 1993–2020; 1.107 × 1.097 × 1.018. | `handoff_2026-10-01c_gmd_round.md` §1c item 1; `outputs/diag_fair_ohc_vs_earth_heat.csv` |
| 371 | Are the FACTS runs forced with FaIR; are the 200 a subset of the 841? | Yes and yes: FACTS is driven by the same FaIR 2.2.4 (calib 1.6.0) ensemble, 200 of the 841 configs, evenly spaced. | memory `facts_shared_climate_arm`; `facts/build_pulse_climate_vv.py` [SUBSAMPLE] |
| 374, 384 | Were MAGICC, Ladrillo and BRICK relative to 1995–2014? His inserted "(2005 for FACTS)": accurate? | Yes. MAGICC-SLR, Ladrillo and BRICK 2.0 are relative to the 1995–2014 mean; FACTS to baseyear 2005, and its output starts 2020, so it cannot be re-referenced. His insertion is accurate. | memory `facts_shared_climate_arm` (baseline caveat) |
| 393 | FittedISMIP's 2100 cutoff "should be easy to fix" | The paper's next sentence answers it: evaluating the fit through 2300 gives 112 cm on High-to-Low while the climate cools, because the time terms grow outside their 2015–2100 fit period. Turning off the cutoff makes it worse. | memory `facts_workflows_differ_only_in_ais` (09-12c) |
| 400 | Should FACTS be among the High-scenario numbers? | At 2100, yes if wanted (all FACTS modules are climate-driven there; quote wf1f and wf2f separately). At 2300, no: under 09-12c no FACTS total is climate-driven past 2100. | `ladrillo_figs.FACTS_CLIMATE_DRIVEN` |
| 412, 413 | Is λ one constant for all samples, or sampled jointly but separately from the other AIS parameters? | His second reading. Calibration holds λ and T_crit at the paleo medians (0.00991 / −15.667) outside the likelihood. In projection each posterior draw is given one JOINT (λ, T_crit) draw from the paleo posterior (corr +0.45; seed 20260920). His suggested rationale (no evidence the process has contributed to observed SLR) has a measured backing: the record rejects every fast-dynamics onset through 2025. This links to the queued one-sentence conditioning qualifier. | memory `l27_paper_posterior`, `paleo_tcrit_crosses_in_hindcast`; SLR CHANGELOG 10-08f; `notes/ladrillo_v11_paper_number_diff_2026-10-08.md` §3.5 |
| 348 | Does not recall the autocorrelation tests (ρ re-fitted, profiled; ρ ≤ 0.99 vs ≤ 0.95) | These are the 09-29/09-30 Table 5 IC runs: AR(1)+observational-error likelihood, σ and ρ profiled per draw and per series, identical for both models. | memory `ic_profile_optimiser_bimodal`, `gmd_review_0929_carried_numbers` |
| 389 | Are the "peak-and-decline pathways" a subset of the seven scenarios? | Yes. The caption should name which markers panel (c) shows. Not checked here which ones the figure plots. | Fig 5 builder |

## 3. Decisions for Marcus (framing, not facts)

- **390: one ensemble throughout.** Tony prefers the joint arm everywhere. Fig 5 is labelled "Fixed arm". Options: re-plot
  Fig 5 on the joint arm, or keep it and say why (glacier regrowth is easier to read on the ensemble-mean climate).
- **347: drop the independent-errors line?** Tony says it is not the model worth entertaining because AR(1) residuals
  matter. Its +1275 is the contrast that the profiled AR(1) result (+60) is measured against.
- **326:** the LWS sentence: leave out, or move to Methods.
- **367:** move "Bars are 17–83 % (thick) and 5–95 % (thin)" to the caption.
- **364:** remind the reader what the joint arm samples (he inserted the reminder as a tracked edit).

## 4. Presentation and wording comments (Marcus's prose)

313 panel labels on the figure; 375 tie the component discussion more directly to the projection differences;
376 "Nauels et al. (2017) transient …" needs a noun; 407 "climate" as shorthand for GMST + OHC (a review risk he
flags, not a request); 411 drop "DAIS" where the fast-dynamics term is meant (fast dynamics was added separately from
DAIS); 428 cite equation numbers; 438 move the 1.95 cm MAGICC-climate regrowth figure to the paragraph whose ¾ / ¼
attribution rests on it; 439 "MAGICC regrows" → "MAGICC's glaciers".

## 5. Tracked edits that change technical content

Most of the 119 new edits are wording. Two carry content:
- **Inserted baseline clause** "and relative to 1995-2014 mean (2005 for FACTS)": accurate (see 374 / 384).
- **⛔ Rewritten 2300 figure caption.** He replaced "The same comparison at 2300." with the 2100 caption's text,
  including "the Total panel shows its seven workflow totals as one bracket". At 2300 that is wrong twice: there are no
  emulandice ("e") workflows past 2100, and under 09-12c the Total panel shows no FACTS total past 2100. The 2300 caption
  needs its own wording.

## 6. Still queued for the same docx pass (unchanged)

- `handoff_2026-10-01c_gmd_round.md` §1c, items 1–8 (item 1 now also answers 362 / 363).
- `handoff_2026-10-08b_ladrillo_github.md` §3 item 3: v1.1 / v1.2 numbers, the "Ladrillo v1.1" label, Table A2 on the
  subsample, Intro 1.3× → 1.4×, the paired tap statistics, the conditioning qualifier.
- If the BRICK 2.0 arm moves to a different posterior (§1), every BRICK 2.0 number in the draft changes, so that
  decision should come before the docx pass.
