# GMD Ladrillo draft: remaining comments and other improvements, page by page (2026-11-05)

Draft read: `deliverables/GMD.Ladrillo.v1_review-2026-10-15_L27_TW2.docx`, saved 2026-11-05 12:35 (md5 `97e2e643…`), read
from a scratch copy. It is open in Word (lock file present), so it was not edited. Page numbers are Word's last saved
layout (`w:lastRenderedPageBreak`), with tracked changes shown as Word lays them out; they may shift by a page.

Comments in the file: 83 (Tony 78, Marcus 3, Claude 2), none marked resolved. About 20 of Tony's are already handled in
the text (marked RESOLVED below: delete or resolve the bubble). The rest are open.

Status codes: **RESOLVED** (text already does it), **FACT** (a factual answer, given here with receipts), **EASY** (a
mechanical fix), **YOURS** (framing or prose; options given, no prose drafted). Where a methods passage is missing, a
draft is given for you to edit (methods text is within Claude's remit; narrative is not).

Receipts: Ladrillo paths are relative to the Ladrillo.jl checkout (src at HEAD = tag v1.3.0); `cal@43d84aa:N` is line N
of `julia/calibrate_mcmc_ext.jl` at the commit L27 ran from. Other paths are relative to SLR-RFF-BRICK.

## Decisions only you can make (collected from below)

1. Fixed arm vs joint arm (Tony 49, 269, 654). Recommendation: keep the fixed arm only for calibration and diagnostics,
   say so once in Sect. 2.1, and move Fig. 5 to the joint arm. That also fixes a number clash (Fig. 5 caption 0.05 cm,
   fixed; Sect. 4.3 text 0.08 cm, joint).
2. The α sentence in Sects. 2.2.4 and 4.1 ("within 4 %"): on matched scope it is 1.18× (item 4, below).
3. Sect. 4.3: whether the Lin et al. (2026) comparison goes in, and where Poinelli et al. (2026) is cited (ruled 10-21:
   as a Thwaites analysis, no comparison).
4. Conclusions: "reductions of up to 18 cm" (one-sided; Ladrillo is higher in 7 of 10 scenarios) and "shown to be a
   result of the FaIR OHC output" (item 4 weakens it).
5. Sect. 4.3 "sit together" (427 vs 383 cm).
6. Tony 559: keep or cut the independent-errors sentence (+1528).
7. Tony 7: "emulator" vs "simple semi-empirical model" in the abstract.

## Claude can do on your OK (no docx edits)

- Fig. 5 on the joint arm: `python/plot_vv_gsic_wr_vs_ladrillo.py:69` `ARM = "fixed"` → `"joint"`, rewrite the
  hard-coded caption text at :345-346; joint paths exist for all 7 scenarios. Joint regrowth 0.0834 cm (fixed 0.0526).
- Panel letters (a), (b), … on Figs. 1–4 and 6 (Tony 440). Only Fig. 5 has them now.
- Re-measure the runtime sentence on the Zenodo BRICK 2.0 posterior (`julia/diag_runtime_ladrillo_vs_brick20.jl`;
  last receipt 09-21, May-22 posterior; inventory U09). A few minutes.
- Table 5 row labels "ρ ≤ 0.99/0.95/0.90" → "ρ < …" (the code is strict; item p14 below).
- Ladrillo repo before it goes public: `src/targets.jl:7` comment says the total is "Frederikse 2020 spliced to NOAA
  STAR"; it is built from Dangendorf 2024 (`python/prep_recalib_targets_ext.py:23-25,296-313`).

---

## Page 1 (title, abstract)

- **Tony 7, "emulator" — YOURS.** Tony: BRICK is broader than emulation, it is fitted to data more than to models.
  Option: call BRICK and Ladrillo "simple, semi-empirical models" in your own sentences and keep "emulator" where it is
  SLEIP's term (the project name, "the seven sea level emulators"). The abstract uses both in its first two sentences.
- **Title — YOURS.** GMD requires the model name and version in the title (present: "Ladrillo v1.3"). "a spinoff of
  BRICK" reads informally beside GMD's usual "Model vX.Y: description" form.
- **Abstract — other.** 263 words. It reports hindcast skill but no projection result; if one headline projection
  number belongs there, it is yours to choose. "fills a unique niche" is the kind of absolute you usually soften.

## Page 2 (Introduction)

- **Tony 30, Wong 2022 for parity — RESOLVED.** Style: "(…, Wong et al., 2022)" needs the comma.
- **Tony 32, "total GMSL" — RESOLVED.**
- **Other.** "Frederikse reconstruction", "Mouginot data" and "GlaMBIE" are named before their first dated citation
  (first cited p8, p6, p5). Add the citation at first mention.

## Page 3 (Introduction end, Table 1)

- **Claude 43, "equal sensitivity" — RESOLVED** by the 10-15 build ("similar … (about 1.1×)"; AIS 1.14, TE 1.07).
  Delete the bubble once you accept the wording.
- **Table 1 note 2 — EASY.** "Goelzer et al., 2020, Seroussi et al., 2020;" separates two citations with a comma inside
  a semicolon list; restructure (e.g. "ISMIP6: Goelzer et al., 2020, and Seroussi et al., 2020").
- **Table 1 caption — EASY.** "(2026; Tables 2 and 6, §3)" → "Sect. 3" (Copernicus).

## Page 4 (Table 2, Sect. 2.1)

- **Tony 49, is the ensemble mean a viable state of the world? — YOURS** (he suggested Slack). The per-year mean of 841
  trajectories is smoother than any one configuration and is not itself a FaIR run. It drives the calibration (where
  it is the natural choice for a fit to one observed history) and the fixed arm. Options: (a) one sentence in Sect. 2.1
  saying the fixed arm is a calibration and diagnostic device and every headline number is joint; (b) also move the
  remaining fixed-arm results to the joint arm: Fig. 5, the amplification sensitivity in Sect. 2.2.3 ("fixed arm"
  twice) and the projection R̂ in Sect. 3.2. (b) satisfies Tony 654 too.
- **Table 2 note 7 — no change.** Re-run on the Zenodo posterior 10-15f (CHANGELOG.md:272-278): v0 41.5 (32.0–51.8),
  remaining at 2000 37.4 (27.9–47.8), melt 4.05 cm. The printed values stand. (Inventory U01 predates the re-run.)

## Page 5 (Sect. 2.2.1 Glaciers)

- **Tony 55, 61, 85, give the equations first — RESOLVED** (you moved them up).
- **Tony 66, 94, parameter descriptions — FACT.** The placeholder "[give description and units]" is still there. Draft
  (from `src/components/glaciers.jl:8-15,69-76`, `model.jl:131-137,206`):

  > In Eqs. (1) and (2), S is a block's cumulative loss since 1850 (m SLE) and S_eq its equilibrium (committed) loss at
  > block temperature T (K relative to 1850–1900). a is the committed-loss scale (m SLE), b the sensitivity of committed
  > loss to temperature (K⁻¹) and T_off the temperature at which committed loss is zero (K). κ is the response-rate
  > constant (yr⁻¹ K⁻ν) and ν the rate exponent. T_eq is the temperature at which the current loss would be in
  > equilibrium, T_eq = T_off − ln(1 − S/a)/b. The model steps annually, driven by the previous year's block
  > temperature, and dS is the change in S over one year. a, b, T_off and log₁₀ κ are sampled for each block (Table A1);
  > ν is fixed for each block (1.54–1.62).

  Check that Table A3 lists the three ν values (`nu_anch_obsfit`); the agent found them in code but not in Table A1.
- **Equation layout — EASY.** Eqs. (1)–(2) are one run-on line ("…(1)dS = …"), as are (3)–(7), (8)–(11) and (12)–(14).
  Put each equation on its own line as a Word equation object with its number at the right.
- **Tony 70, define RGI outside captions — RESOLVED** (p5 #135). Missing reference: RGI Consortium (2017) is never cited
  although RGI appears ~15 times.
- **Tony 74, 75, what the 2.50 prior is; add an equation — FACT, with one gap.** Draft (`model.jl:7,175,234-235`;
  cal@43d84aa:178-190,203-213; `python/diag_amp_dataset_comparison.py`):

  > Each block b is driven by its own regional temperature T_b. Through 2024, T_b is the HadCRUT5 annual anomaly
  > averaged over the block's RGI regions, weighted by glacier area in 2000. After 2024,
  > T_b(t) = A_b·G(t) + c_b, where G is GMST relative to 1850–1900, A_b the block's amplification and c_b the constant
  > that matches the 2014–2024 observed mean. The prior on A_b is a truncated normal whose width and bounds come from the
  > through-origin regressions of the block's anomaly on global anomaly over 1901–2024 in HadCRUT5, Berkeley Earth and
  > GISTEMP: N(2.50, 0.45) on [1.80, 3.50] for SLOWG, N(1.45, 0.15) on [1.33, 1.82] for FASTG and N(0.72, 0.15) on
  > [0.58, 0.88] for RGI 19. In calibration the drivers are built once at the prior centres.

  ⚠ Gap: the code note says "center near HadCRUT5". SLOWG (2.50 vs HadCRUT5 2.48) and FASTG (1.45 vs 1.40) fit that;
  RGI 19's 0.72 does not (HadCRUT5 0.615, Berkeley 0.847, GISTEMP 0.580, mean 0.68), and no derivation of the σ values
  was found. State the rule only after you confirm where 0.72 came from.
  Also, A_b enters only after 2024, and in calibration the driver is fixed at the prior centre, so A_b is effectively
  prior-propagated (it also sets κ's prior centre). Sect. 2.2.2 says this for Greenland; say it for glaciers too.
- **Units — EASY.** "0.049 ± 0.116 mm/yr" → "mm yr⁻¹" (5 other places use the exponent form).

## Page 6 (Sect. 2.2.1 end, Sect. 2.2.2)

- **Tony 77 and your 78, is 32.4 used? — FACT.** No. The constraint is 29.0 ± 6.0 cm; 32.4 ± 8.4 is the full-RGI value
  for context and already appears in the Table 2 caption. Option: drop the sentence from 2.2.1.
- **Broken paragraph — EASY.** p6 #140/#142: "Ladrillo does have the potential to regrow glacier ice after cooling" and
  ", with a regrowth limit…" are separate paragraphs (the deleted equations sat between them). Rejoin.
- **Tony 118 and your 119, Mengel 2016 — RESOLVED.**
- **Tony 126, abbreviations — RESOLVED** (deleted). **Tony 132, Mouginot full reference — RESOLVED** (in the list).
- **Tony 145 and the "[Claude: describe exact approach here]" placeholder — FACT.** Draft (`python/build_t_gis.py`
  :26-45,87-88,104-114,241-273,322-329; `python/diag_gis_amp_cmip6.py`; `outputs/gis_amp_prior.csv`):

  > Both basins are driven by one regional series: the HadCRUT5 annual anomaly over southern Greenland (59–70° N; 11
  > grid cells, each weighted by its overlap with the RGI region 05 outline and its land fraction), relative to
  > 1850–1900. There is no further downscaling within the ice sheet; the basins differ only in their volume shares and
  > rate scales. The amplification is the through-origin regression of this series on the same product's global anomaly
  > over 1901–2024: 1.97 in HadCRUT5, 1.51 in Berkeley Earth and 2.29 in GISTEMP. Its prior is their mean and standard
  > deviation, N(1.92, 0.32), truncated to [1.51, 2.29]. Its decline with warming, S, is the median over 40 CMIP6 models
  > of the ratio of 30-year mean regional to global warming, binned by global warming and interpolated over 0.75–2.75 K
  > (S = 0.96 at 1.5 K and 0.86 above 2.75 K, relative to 1 at 0.94 K).

  This also lets you shorten p7 #153's description of the splice. The above-threshold channel reads global GMST.

## Page 7 (Sect. 2.2.2)

- **Tony 154, equations before values — EASY.** The first sentence of "Above-threshold discharge channel" gives "V = 564
  cm, τ = 800 yr, onset 4.69 K…, two stages"; the same values follow Eq. (11) (p8 #156, as "V = 5.64 m"). Delete them
  from the first sentence; that also removes the cm/m inconsistency.
- **Tony 167, citation for "5.7 implied by process-model runs" — FACT.** It is PROTECT-Greenland, Goelzer et al. (2025),
  The Cryosphere 19, 6887 (data doi:10.11582/2025.lf9m2wd0): NORCE-CISM r2300/x2300 runs, interpolated to the calib
  1.6.0 forcing, p50 86.92 / 15.27 cm = 5.69 (`python/build_gis_matched_targets.py:1-60`,
  `outputs/gis_matched_targets_2300.csv`). Caveat for the text: past 2100 every anchor is one ice-sheet model. It is a
  different model from the ISMIP6/SICOPOLIS constraints named two sentences earlier. Goelzer et al. (2025) is not in the
  reference list yet.
- **Tony 168, log₁₀ vs ln — FACT.** s_b is a positive scale spanning about a decade, so it is sampled in log space; the
  prior is N(0, 0.5) on [−2, 2] in log₁₀, centred at s = 1 so the Mouginot partition is not counted twice
  (cal@43d84aa:927-942). The base only rescales the prior. The glacier κ's are also log₁₀; ℓ is ln. Option: say "log₁₀"
  once with the reason, or switch ℓ to log₁₀ for consistency. No change needed otherwise.
- **Tony 169, 170, explain level and tilt — FACT (170 is YOURS).** From the definitions already printed: ℓ = ln r_s(T̄)
  is the log discharge rate at the 2015–2024 regional temperature, and w = α_s·T̄ / r_s(T̄) is the share of that rate
  that scales with temperature, which is also the elasticity d ln r_s / d ln T at T̄ (Table A1 already calls it
  "temperature-dependent fraction of the rate"). One sentence saying this answers 169 and 428. The reason for sampling
  (ℓ, w) instead of (α_s, β_s) is not in the receipts I have; state it from your notes. Tony 170 (framing Ladrillo as
  intermediate complexity, more process detail than BRICK) is a framing choice for the Introduction.
- **Symbol clashes — EASY, worth one pass.** T_on is the Greenland above-threshold onset (4.69 K GMST, Eq. 8) and the
  Antarctic runoff onset (p8 #161). κ is the glacier rate constant and the Antarctic precipitation sensitivity (p8 #160).
  T̄ is 1.963 K (Greenland) and −18.0 °C (Antarctica). α is the expansion coefficient and the Greenland rate slopes. w is
  the tilt and w_r the ramp width. c is Greenland's c₀, c₁ and the Antarctic runoff-line slope. S is glacier loss and the
  CMIP6 decline function. L is the error e-folding length and the likelihood terms L_i, L_m. A notation table in
  Appendix A would let a reader check these.

## Page 8 (Sect. 2.2.3 Antarctica)

- **Tony 190, (REF?) for the paleo prior — FACT.** Wong et al. (2017a), the source of
  `DAISfastdyn_calibratedParameters_gamma_29Jan2017.nc` (Table 3 already says so; CHANGELOG.md:1818).
- **Tony 195, grammar of the ln P₀ clause — RESOLVED** in substance. Rename κ here (see symbol clashes).
- **Tony 196, "modern" — RESOLVED.** **Tony 206, cite Frederikse — RESOLVED;** style "(Frederikse et al., 2020)".
- **Tony 230, (REF?) for "dearth of contemporary evidence" — FACT.** IPCC AR6 WG1 Ch. 9 (Fox-Kemper et al., 2021, in the
  list) assesses MICI with low confidence; Tony suggests mirroring that language. The paper's own measurement follows in
  the same paragraph (every draw firing by 2025 has weight below 10⁻²⁰).
- **Other.** "λ = 0" in any added Lin text means "DAIS fast dynamics off", not "no MICI" (MICI is outside the
  representable set; memory `ais_lambda_prior_envelope`).

## Page 9 (Sect. 2.2.3 end, 2.2.4)

- **"(REF Wong et al 2017)" for the 1.196 ratio — FACT.** MimiBRICK v2.0.0 sets ais_temperature_coefficient 0.8365 and
  intercept 15.42 (`src/MimiBRICK.jl:95-96` there); 1/0.8365 = 1.196. The code comment calls it a regression of global
  temperature on an Antarctic temperature reconstruction; the BRICK v0.2 paper cites "Morice et al., 2012; Shaffer,
  2014" and prints no coefficients. Cite Wong et al. (2017b) and Shaffer (2014). "Equilibrium" in the text is the
  research notes' word; the code says "regression". Choose one.
- **Tony 269, caveat on "mean" — YOURS** (same decision as Tony 49).
- **Tony 272, does the orthogonalization prevent compensating errors? — FACT.** Yes. The basis is orthogonal to a
  constant and to FaIR's ocean-heat series, so δ cannot mimic a change in α or an offset. Option: "so δ and α cannot
  trade off".
- **Item 4, "within 4 % of the value the 0–2000 m observations imply" — YOURS, numbers here.** α multiplies FaIR's OHC,
  which is Earth's total heat uptake. Ladrillo α ÷ observation-implied α, 1993–2020: 0.974 per 0–2000 m heat (the draft's
  basis), 1.079 per full-depth ocean, 1.183 per total Earth heat (matched). Matched obs-implied α = 0.141, below the
  posterior 5–95 % (0.148–0.186). No formal error bar. Receipt `python/diag_te_alpha_matched_scope.py`,
  `outputs/diag_te_alpha_matched_scope_L27.csv` (9baec70). The same sentence recurs in Sect. 4.1 (p17).
- **Amplification sensitivity "(fixed arm)" twice — YOURS** (decision 1).

## Page 10 (Sect. 2.2.5, 3.1, Table 3)

- **Sect. 2.2.5 vs Sect. 4.1 on BRICK 2.0's land water — check.** 2.2.5 says BRICK 2.0 "as published sets land water to
  zero before 2019"; 4.1 (p16 #282) says it "subtracts LWS prior to calibration". Both may be true, but they read as two
  different claims. State it once, in 2.2.5 (also Tony 505).
- **Tony 294, "spliced onto" — FACT.** (`python/prep_recalib_targets_ext.py:369-394,433-450`; cal@43d84aa:650-663,
  1150-1187,1592-1622). Both: GlaMBIE extends the target series, and it also enters as two separate constraints. Draft:

  > The glacier target is one series: Frederikse et al. (2020) through 2018, then GlaMBIE (global minus RGI 05) for
  > 2019–2023, shifted by a constant so that the two have the same mean over 2003–2018. GlaMBIE also enters the
  > likelihood twice more: as the FASTG share of the 2000–2024 mean loss rate of SLOWG plus FASTG, N(0.69, 0.05), and as
  > RGI 19's 2000–2024 mean rate, N(0.049, 0.116) mm yr⁻¹.

- **Tony 295, 308, "offset" / "offset-matched" — FACT.** A constant shift so that the two series have the same mean over
  the overlap (`prep_recalib_targets_ext.py:231-234`): NCEI 0–2000 m onto Frederikse over 2005–2018 (fills 2019–2025);
  NOAA STAR onto Dangendorf over 2003–2018 (fills 2022–2024). Option: define it once in the Table 3 caption.

## Page 11 (Table 3 end)

- **Tony 296, his edit "(a process-model constraint, not data used for calibration)" — FACT: the edit is inaccurate.**
  The GlacierMIP3 committed-loss fractions are likelihood terms (Sect. 3.2 lists them among the L_m, p14 #232). Option:
  "(a process-model constraint in the likelihood, not observations)".
- **Tony 299, what "observed" means in the CMIP6 row — FACT.** Greenland's amplification level and prior width come from
  the three observational products (p6 item above); CMIP6 supplies only the shape of its decline with warming. For
  Antarctica, CMIP6 gives the prior itself.
- **GTN-G and WGMS — EASY.** Both appear only in note 18 ("region polygons GTN-G Glacier Regions (WGMS, 2023)") and are
  not expanded there. Expand once: "the Global Terrestrial Network for Glaciers (GTN-G) region outlines (World Glacier
  Monitoring Service, WGMS, 2023)". The methods drafts in this note say "RGI regions" instead, because the GTN-G outlines
  are the RGI first-order regions, so the main text needs no new acronym (Marcus 11-05 asked).
- **Table 3 style — EASY.** The journal shorthand in the version column ("PNAS 116:9239", "Nat. Geosci. 12:168",
  "Science 388:979", …) duplicates the reference list; author–year is enough.

## Page 12 (Sect. 3.1 end)

- **Tony 321, 323 — RESOLVED** (both edits are accurate; the "four component series" have the point constraints beside
  them).
- **"with the addition of observed land-water storage" (p12 #221) — EASY.** Land water is an input, not a fitted series;
  the sentence reads as if it were fitted.
- **Tony 359, the calibrated model's results in a data section — YOURS.** Options: move the IMBIE 2026 paragraphs to
  Sect. 4.1, or keep them and start with "The calibrated model…".
- **Tony 360, σ here but cm later — EASY.** Give both: "by 0.38 cm (2.6σ)".
- **Item 7, the post-2002 Antarctic rate (disclosure) — YOURS, numbers here.** Per draw, OLS mm yr⁻¹, L27 p05/p50/p95:
  2002–2021 0.248/0.294/0.331 vs target 0.423 ± 0.029 and IMBIE 2026 0.524 ± 0.048; 2002–2023 0.255/0.302/0.339 vs
  0.393 ± 0.038 and 0.498 ± 0.062; 2002–2025 0.262/0.310/0.348 vs 0.372 ± 0.049. Every draw is below the target through
  2021 and 2023, 99.5 % through 2025; BRICK 2.0 82/75/68 %. Receipt `python/diag_ais_rate_2002_per_draw.py`,
  `outputs/diag_ais_rate_2002_per_draw_L27.csv` (4108e55). Natural home: this IMBIE paragraph.
- **Citation form — EASY.** "(Otosaka et al., 2026) (which starts…)" has back-to-back parentheses.

## Page 13 (Sect. 3.2)

- **Tony 365, 366 — RESOLVED** by reading on; optional rewording "a two-coefficient discrepancy term for thermal
  expansion".
- **Tony 374 — RESOLVED** (the sentence he flagged is deleted).
- **"Five Antarctic changes … the four described above" — EASY.** Sect. 2.2.3 does not number them, and a reader can
  count five or six (joint geometry prior with the u reparameterization, T_on, fast dynamics held at medians, the
  amplification prior, the 1900 target). List the four here.
- **Tony 376, 377, "harmonized per species" — FACT.** (`tools/forcing/build_emissions_v160_ssp245.py:1-20,246-264`
  in Ladrillo). Draft: "Each of the 51 emitted species (greenhouse gases, aerosol and ozone precursors) is scaled by a
  constant ratio, history over scenario at 2023.5, applied to every later year." So Tony's "greenhouse gases?" is no;
  "emitted species" is right.
- **Tony 388–392, the discrepancy term — FACT.** (cal@43d84aa:666-800,1043-1049,1546-1555;
  `data/posterior/ladrillo_L27_posterior.csv`). Draft replacement for the middle of p13 #229:

  > The two basis functions are the linear and quadratic terms in time over the 1900–2025 fit years (time scaled to
  > [−1, 1]), made orthogonal to a constant, to FaIR's ensemble-mean ocean heat content over those years and to each
  > other (unweighted inner product), then scaled to unit RMS, so each coefficient is an RMS discrepancy in cm. Both have
  > N(0, 0.5 cm) priors truncated to ±2.5 cm. The quadratic coefficient's posterior spans zero (median 0.07 cm, 5–95 %
  > −0.05 to 0.20); the linear one does not (0.21 cm, 0.01 to 0.40).

  Answers: 388 linear and quadratic; 389 the fit years, unweighted (a 1/ε² weighting was tried and rejected,
  cal@43d84aa:716-727); 390 the OHC level series, not its annual change; 391 "the driver" is OHC; 392 the ranges above.
- **References — EASY.** Mimi "(1.6; Rennels et al., 2022)": the list entry ends with the GitHub handle "Catawbasam" and
  uses the all-versions Zenodo DOI; cite the v1.6 release DOI. CMIP7 historical emissions, MESSAGE-GLOBIOM SSP2-4.5 and
  RCMIP v5.1.0 have no references.

## Page 14 (Sect. 3.2 end, 3.3)

- **Tony 400, does [0, 0.99) disallow 0.99? — FACT.** Yes; the code rejects ρ ≥ 0.99 (cal@43d84aa:1489), and the highest
  posterior ρ is 0.98999, at the bound. The Table 5 script is strict too (`python/ic_ladrillo_vs_brick20.py:187,212`),
  so its labels "ρ ≤ 0.99/0.95/0.90" should read "<".
- **Tony 410, R̂ < 1.1 is also used — FACT, and the sentence overstates.** (`outputs/log_l27_postprocess_driver.txt:73-82`.)
  The 8 failures are failures of the joint gate, mostly on ESS. Only 3 exceed R̂ 1.05: ais_runoff_Ton 1.313,
  ais_c 1.079, ais_slope 1.063. The other 5 have R̂ 1.013–1.047 (antarctic_alpha, anto_alpha, anto_beta, ais_iceflow0,
  ais_precip_u). All 8 have ESS below 400 (19.5–243.8). Only ais_runoff_Ton exceeds 1.1. Suggested facts for the
  sentence: "Three exceed R̂ = 1.05 (ais_runoff_Ton 1.31, ais_c 1.08, ais_slope 1.06) and all eight have effective
  sample sizes below 400 (20–244)."
  ⚠ Reviewer risk (my recollection, not checked here): Vehtari et al. (2021), whose R̂ the paper uses, recommend
  R̂ < 1.01. A reviewer may note that 1.05 is looser than the cited source's threshold. The projection R̂ (1.001, 1.002)
  meets 1.01.
- **Tony 415 — RESOLVED** (deleted).
- **Tony 426, machine and timing — FACT.** Apple M4, 10 cores, 16 GB (CHANGELOG.md:1442). Four chains of 2,000,000
  iterations in parallel on 2026-09-20, 14,379–14,678 s each (about 4 h), after a 500,000-iteration tuning chain
  (`outputs/mcmc/log_L27_seed202{6..9}.txt`). Projection: 6.26 ms per draw, 1850–2300 (median; 09-21 receipt, May-22
  BRICK posterior). The paper's joint arm uses 2,000 draws per scenario.
- **Tony 427, link to Code availability — EASY.**
- **Tony 428, remind the reader what level and tilt are — EASY** once p7's sentence exists: "(Sect. 2.2.2, Eq. 4)".

## Page 15 (Sect. 4.1, Fig. 1, Table 4)

- **Tony 440, panel labels — EASY (Claude, on your OK).** Figs. 1–4 and 6 title panels by component and have no
  letters. All six embedded images match the current renders (md5, `figures/paper/`, 10-15 21:06; Fig. 5 10-08).

## Page 16 (Sect. 4.1, Table 5)

- **Broken paragraph — EASY.** p16 #280/#281: "…We note that" / "the non-closure…". Rejoin.
- **Tony 505, the LWS sentence — YOURS (recommend delete here).** Sect. 2.2.5 already says it; keep only the
  target-vintage clause if you want it, and reconcile the two descriptions (p10 item above).
- **Tony 562, the ρ rows — EASY.** Name them in the text as sensitivity rows to the calibration's ρ bound.

## Page 17 (Sect. 4.1)

- **Tony 559, the independent-errors sentence (+1528) — YOURS.** Tony: not a model worth entertaining. It is the contrast
  the AR(1) result is measured against. Option: keep the Table 5 row and cut the sentence to a clause.
- **Item 4 again: "Despite Ladrillo's expansion coefficient being within 4 %…" — YOURS** (numbers on p9).
- **Tony 597, 603, 1.21–1.27 vs 1.24, and "1.10 + 1.10" — EASY, with one warning.** The text now multiplies:
  1.11 × 1.10 × 1.02 ≈ 1.24. Say that 1.24 is IGCC's 0–2000 m member of the 1.21–1.27 range, over 1993–2020, and write
  the product out. Do not use Tony's suggested sentence ("FaIR's full-depth uptake overestimating IGCC's full-depth
  value"): it restates the attribution retracted 10-01 (triage note §2).

## Page 18 (Sect. 4.2, Fig. 2)

- **Tony 606, joint-arm reminder — RESOLVED** (his insertion; accept).
- **Tony 609, bars into the caption — EASY.**
- **Tony 613, FACTS's 200 — FACT.** FACTS is driven by the same FaIR 2.2.4 (calib 1.6.0) ensemble: 200 of the 841
  configurations, evenly spaced. Also say the counts: BRICK 2.0 1,000 draws and Ladrillo 1,997 (SSPs) / 1,998 (van
  Vuuren), paired with the same configuration draw by draw (inventory U10).
- **Tony 619, 631, baselines — RESOLVED** (Fig. 2 caption; accurate).
- **Tony 620, tie the component paragraph to the projection differences — YOURS.** One option per component: the
  structural difference, then the difference it makes in Figs. 2–3.
- **Tony 621, "the Nauels et al. (2017) transient" — EASY:** "transient response formulation".

## Pages 19–21 (Figs. 3–6)

- **Tony 649, which scenarios are peak-and-decline — RESOLVED** (caption names the four).
- **Tony 654, Fig. 5 is the fixed arm — YOURS (recommend joint).** Cost and receipts under "Claude can do". The caption's
  "about 0.05 cm" (fixed) and Sect. 4.3's 0.08 cm (joint) disagree now; the joint figure removes that.
- **Tony 663, FittedISMIP — no change.** The next sentence of the text answers it (fitting through 2300 gives 112 cm
  while the climate cools). A reply to Tony is enough.

## Page 22 (Sect. 4.3)

- **Tony 676, FACTS in the High 2100 numbers — FACT.** Total medians, cm relative to 2005, `outputs/facts_components_shared_n200.csv`:
  wf1e 60.5, wf1f 56.3, wf2f 64.4, wf3f 66.1, wf4 76.0 (also wf2e 66.2, wf3e 65.0). A range "FACTS 56–76 cm across its
  workflows" fits beside Ladrillo 73, BRICK 2.0 79, MAGICC-SLR 62. Not at 2300 (no FACTS total is climate-driven).
- **"sit together (427 and 383 cm)" — YOURS (N10).** Ladrillo is 44 cm above BRICK 2.0; both are 140–185 cm below
  MAGICC-SLR's 567.
- **Tony 690, "climate" for GMST + OHC — EASY.** "not the climate modules" → "not the climate drivers"; define "climate
  driver (GMST and OHC)" once in Sect. 2.1.
- **Tony 696, "DAIS fast-dynamics rate" — EASY.** Drop "DAIS".
- **Tony 697, 698, is λ one constant? — RESOLVED** (the text now says "jointly with the threshold temperature");
  add "(Sect. 2.2.3)".
- **Lin et al. (2026) and Poinelli et al. (2026) — YOURS.** If Lin goes in, this paragraph is its home. Numbers
  (2015→2100, cm, median [5–95]), Lin's drift-corrected row as ruled 10-17:

  | | SSP2-4.5 | SSP5-8.5 |
  |---|---|---|
  | Lin, drift-corrected posterior | 5.2 [1.2–9.7] | 7.7 [1.9–16.2] |
  | Ladrillo L27 | 10.0 [3.8–57.2] | 36.3 [6.9–69.3] |
  | Ladrillo L27, λ = 0 | 5.4 [3.6–8.8] | 7.5 [4.6–12.9] |
  | BRICK 2.0 | 22.0 [0.8–66.6] | 37.6 [13.7–78.4] |

  Receipt `julia/diag_ais_2100_vs_lin2026.jl`, `outputs/diag_ais_2100_vs_lin2026_L27.csv` (ecc98c4; follow-up note
  2026-10-15h). Poinelli: cite as a Thwaites analysis with no number set against Ladrillo (ruled 10-21). Reference entry
  in that note. Neither paper is in the list yet.
- **Low scenarios, "Ladrillo sits at the low end" — EASY.** For Very Low it is between MAGICC-SLR (46) and BRICK 2.0 (80).
- **Tony 724, cite equation numbers — EASY:** "(Eqs. 1–2)".
- **Tony 744, move the 1.91 cm sentence — EASY.** It belongs with the ¾ / ¼ paragraph. Writing the arithmetic out helps:
  gap 8.55 − 0.08 = 8.47 cm; with MAGICC's climate Ladrillo regrows 1.91, closing 1.83 cm (22 %); the remaining 6.64 cm
  (78 %) is structure.
- **Tony 747 — EASY:** "MAGICC's glaciers".

## Page 23 (Conclusions)

- **Claude 767, "reductions of up to 18 cm" — YOURS (N09).** True only for 3 scenarios. Ladrillo's 2300 Antarctic median
  is higher than BRICK 2.0's in 7 of 10 (SSP5-8.5 +47 cm, High +31, Medium +7, Low +4, SSP1-2.6 +4, Very Low +3,
  Medium-to-Low +0.05). Receipt `outputs/brick20_swap_paper_number_diff_20261015.csv`. A factual frame is the signed
  range (−18 to +47 cm) by scenario.
- **"Remaining mismatches of historical thermal expansion are shown to be a result of the FaIR OHC output" — YOURS.** The
  timing argument (FaIR's back-loaded uptake) stands; the matched-scope α (1.18×) means "shown to be" claims more than
  the analysis does. Item 8 (the next-version direction: calibrate TE on an observed OHC driver and splice FaIR's future
  anomaly) would fit here.
- **Runtime sentence — EASY (Claude, on your OK).** Not re-measured since the Zenodo swap. "a 10,000-draw ensemble takes
  about a minute" is arithmetic from 6.3 ms per draw; the paper's own projections use 2,000 draws.

## Pages 35–46 (back matter, references)

- **Your 790, Code and data availability — YOURS.** DOI and "[repository URL]" are placeholders; msarofim/Ladrillo.jl is
  still private. GitHub–Zenodo integration mints the DOI at the release you tag for submission.
- **Acknowledgements — YOURS.** Frank Errickson is still missing (queued item 7). Consider S. Dangendorf (the corrected
  file, Table 3 note 21) and the PROTECT data providers.
- **Reference list — EASY** (agent check, `scratchpad/gmd1105/refcheck/`):
  - Morlighem et al. (2017) DOI reads `10.1022/2017GL074954`; it is `10.1002/2017GL074954`.
  - Sarofim et al. (2021) pages "11, 1–3" look like a placeholder; check against the DOI.
  - Mimi (Rennels et al., 2022): author "Catawbasam" and the concept DOI (p13 item).
  - Missing: Goelzer et al. (2025), RGI Consortium (2017), Church and White's 2015 update (p12 #221 names it), CMIP7
    emissions / RCMIP v5.1.0, NOAA STAR (no DOI; cite the product page), Lin et al. (2026) and Poinelli et al. (2026)
    if used.
  - Leclercq et al. (2011) is cited only in Table 3; the main text says "the Leclercq constraint" three times without
    a year.
  - Missing commas: "(…, Wong et al. 2022)", "(Frederikse et al. 2020)" twice, "Wong et al 2017". "Millan et al., 2022,
    have…" should be "Millan et al. (2022) have…".
- **Copy-edit.** Every "outside the brief" typo in the 10-15 inventory is now fixed in the text. Still present:
  "0 deg C" (p8 #161) → "0 °C"; "Gt/yr" ×4 and "mm/yr" ×1 → "Gt yr⁻¹", "mm yr⁻¹".
