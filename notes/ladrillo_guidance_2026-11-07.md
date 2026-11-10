---
title: "Ladrillo GMD draft: guidance for the remaining issues"
subtitle: "Draft saved 2026-11-07 09:08 · notes from ladrillonotes.docx (08:40) · prepared 2026-11-07 · updated 2026-11-10"
---

# How to use these notes

Items run page by page, using the page numbers Word showed at your last save. Each item has one tag:

- **HAND**: a text change you can make now. Suggested wording is in the indented blocks.
- **DECIDE**: your call. Options are given and the recommended one comes first.
- **CLAUDE**: needs a run or a figure from me. Everything that can be done before that is listed with it.
- **CLOSE**: the text already handles the comment; resolve the bubble.

Simplification was the priority in every suggested rewrite. The rewrites keep your numbers and claims, shorten
sentences, and remove repetition. Rewrites marked "optional" are simplifications only.

## Answers to your notes

1. **Joint arm everywhere (option b).** Done or ready for every *result*. Fig. 5 is re-rendered on the joint arm.
   The Sect. 2.2.3 amplification numbers are recomputed on the joint arm (p. 7). I recommend keeping the fixed arm for
   two *diagnostics* only, the projection R̂ and the refit comparison in Sect. 3.2, because climate spread would hide
   differences between chains. A suggested sentence for Sect. 2.1 says so (p. 4).
2. **RGI 19 prior centre 0.72.** No derivation is recorded. It entered on 2026-08-09 (calibrator commit 02150d8) with
   the note "cross-dataset ranges". It is close to the midpoint of the range of the three products' fits (0.58–0.86),
   while the SLOWG and FASTG centres sit near HadCRUT5; that midpoint reading is my inference. Switching to
   0.68 (the three-product mean, the rule Greenland uses) changes glacier medians by at most 0.03 cm in any scenario
   or horizon. I priced it by reweighting the posterior by the ratio of the new prior to the old one, which is exact
   whenever only a prior changes (receipt `outputs/diag_r19_amp_prior_reweight_L27.csv`). Recommendation: keep
   0.72 and describe the priors as spanning the three products (p. 4). No recalibration is needed either way.
3. **log₁₀ versus ln.** ln works equally well. The base only rescales the prior (N(0, 0.5) in log₁₀ is N(0, 1.15) in
   ln), and halving and doubling are equally likely in either base. No reason for base 10 is recorded: s_high copied
   the glacier κ convention, while ℓ and u were already ln. **Updated 2026-11-10:** you chose to show the four log₁₀
   rows of Table A1 in ln. The code and the posterior file stay in log₁₀, so no number in the paper changes. Edits:
   Table A1 (new "Appendix A" item below) and the s_b sentence on p. 7.
4. **Level and tilt.** A sentence is on p. 6. The reason is recorded in the calibrator: in test chains, sampling
   (ℓ, w) instead of (α_s, β_s) cut the within-chain correlation between the two parameters from 0.58 to 0.14
   (`python/diag_gis_slow_reparam.py`).
5. **Symbol clashes.** A renaming table is at the end. The four that matter most: T_on (Greenland) → T_thr, Antarctic
   κ → κ_P, Greenland amplification a → A_G, and the CMIP6 decline function S → φ.
6. **Discrepancy term in simpler words.** On p. 11.

## Waiting on Claude (nothing else depends on these)

| item | status |
|---|---|
| New figure files with panel letters, Figs. 1–4 and 6 | **Ready.** Insert from `SLR-RFF-BRICK/figures/paper/`: `hindcast_components_L27.png`, `model_comparison_components_vv_L27_2100.png`, `model_comparison_components_vv_L27_2300.png`, `future_components_vv_L27_joint.png`, `vv_responsiveness_L27.png` |
| Fig. 5 on the joint arm | **Ready:** `figures/paper/vv_gsic_ladrillo_L27_2300_joint.png` (new caption on p. 17) |
| Runtime sentence (Conclusions) | Re-measure on the current BRICK 2.0 posterior; a few minutes |
| Table 2 note 7 (BRICK 2.0 inventory) | Only if you choose the second option on p. 3: a 10,000-draw rerun |
| Code availability | The text says the archive holds "the scripts that produce every figure and table". Ladrillo.jl currently ships only the Table 5 script; the figure scripts are in SLR-RFF-BRICK. Either I copy them into Ladrillo.jl before the release you tag, or the sentence changes. Repository still private; DOI comes from the Zenodo release |

---

# Page 1: title and abstract

**Title. DECIDE (optional).** GMD titles read "Model vX.Y: description". "A spinoff of BRICK" is informal.

> Ladrillo v1.3: a sea-level model derived from BRICK with improved twentieth-century hindcasts

**Abstract. HAND (simplification).** It is 287 words and its first two sentences repeat each other. Suggested
version (191 words), with your numbers unchanged:

> BRICK (Building blocks for Relevant Ice and Climate Knowledge) is a widely used simple, semi-empirical model of
> sea-level rise. It is calibrated to historical observations and reproduces twentieth-century sea level. Ladrillo
> keeps BRICK's structure and approach, but adds more detailed glacier and Greenland components, regional temperature
> amplification and longer observational records for each component. Where observations cannot constrain the model,
> Ladrillo uses results from model intercomparison projects. It is driven by the Finite-amplitude Impulse Response
> (FaIR) climate model instead of being coupled to the Simple Nonlinear Earth System model (SNEASY). This paper
> describes these changes, compares Ladrillo's hindcast with observations, and compares its projections with
> BRICK 2.0. Over 1900–2025, Ladrillo's hindcast has a root-mean-square error lower than BRICK 2.0's by 95% for
> Antarctica, 79% for glaciers, 72% for Greenland and 19% for thermal expansion. The Akaike and Bayesian information
> criteria both favour Ladrillo despite its 15 additional parameters. By 2300, Ladrillo projects 9–14 cm (27–56%) less
> glacier melt than BRICK 2.0, but a 47% larger difference between the High and Very Low scenarios. Among the seven
> emulators assessed by the Sea Level Emulator Intercomparison Project (SLEIP), Ladrillo occupies a distinct niche.

Notes:

- The glacier sentence is safe to trace to the glacier formulation. Giving BRICK 2.0 Ladrillo's glacier inventory
  closes only 8–16% of the 2100 gap and 10–20% of the 2300 gap in the low and middle scenarios, and it narrows BRICK's
  range instead of widening it (CHANGELOG 2026-11-05c). If you want the bootstrap interval on the 47%: 41–54%.
- This version drops "emulator ecosystem" (Tony's comment, now closed) and "not overfitting" (the criteria sentence
  makes the point).

# Pages 2–3: Introduction

**p. 2, paragraph "As a derivative of BRICK…". HAND (simplification).** One 230-word paragraph becomes two shorter
ones:

> Ladrillo derives from BRICK (Wong et al., 2017b, 2022). Below, "BRICK" refers to the model family and "BRICK 2.0" to
> its MimiBRICK v2.0.0 release, against which Ladrillo is compared. Ladrillo keeps BRICK's approach of physically based
> components calibrated to the historical record. It departs from that approach in two places that observations cannot
> inform: a Greenland discharge channel above a temperature threshold, informed by the Ice Sheet Model
> Intercomparison Project for CMIP6 (ISMIP6) and the SImulation COde for POLythermal Ice Sheets (SICOPOLIS), and the
> committed loss and response time of each glacier block at future warming levels, informed by the Glacier Model
> Intercomparison Project phase 3 (GlacierMIP3).
>
> The largest structural changes split glaciers into three regions, each with a separate response time and equilibrium
> curve, and split Greenland into two basins with separate surface mass balance and discharge. Ladrillo also extends
> BRICK 2.0's observational constraints: an Antarctic likelihood from 1900 instead of the 1992–2017 Ice Sheet Mass
> Balance Inter-comparison Exercise (IMBIE) record, and new data from the Glacier Mass Balance Intercomparison Exercise
> (GlaMBIE, 2024), the Gravity Recovery and Climate Experiment (GRACE) and Mouginot et al. (2019). It replaces
> BRICK 2.0's paleo-equilibrium Antarctic amplification with one based on the Coupled Model Intercomparison Project
> Phase 6 (CMIP6; Eyring et al., 2016), adds regional amplification for Greenland and the glacier regions, and is
> calibrated to FaIR 2.2.4 (fair-calibrate 1.6.0, 841-member ensemble; Leach et al., 2021; Smith et al., 2024; Smith,
> 2026) instead of being coupled to SNEASY.

**p. 3, "Overall, these changes…". HAND (optional).**

> These changes let Ladrillo match twentieth-century estimates of each component more closely. By 2300, Ladrillo's
> glacier and Greenland components respond more to the choice of scenario than BRICK 2.0's (1.5 and 3 times the
> difference between the High and Very Low scenarios). Antarctica and thermal expansion respond about equally (about
> 1.1 times), although Ladrillo's Antarctic component responds less than BRICK 2.0's at shorter horizons. Ladrillo is
> also one of the few emulators whose glaciers can regrow in overshoot scenarios (Table 2).

**Tony on "Ladrillo will be much more of an intermediate simplified model" (his reply on p. 7). DECIDE.** If you want
that framing, one sentence at the end of the paragraph above would carry it.

# Pages 3–4: Tables 1 and 2

**Table 1 note 2. HAND.** Remove the double space in "Goelzer et al., 2020,  and".

**Table 2 note 7, BRICK 2.0's glacier inventory. DECIDE.**

- (a, recommended for now) Leave 37.4 cm. It is BRICK 2.0's initial volume minus its melt since 1850.
- (b) Report the ice BRICK 2.0's own equations can still melt. Its glacier state starts at an offset (median
  1.9 cm), which its cap counts as melted, so the remaining ice is about 35.5 cm (1,000 joint draws). This needs a
  10,000-draw rerun from me for the table value. Note text would become:

> ⁷ Calibrated initial volume 42 cm (5–95% 32–52) at the 1850 start, less its initial offset and 4.0 cm of melt by 2000.

# Page 4: Sect. 2.1 and the start of Sect. 2.2.1

**Sect. 2.1, the joint/fixed paragraph (Tony 63, option b). HAND.** Replace from "Projections are run in two ways"
to the end of the paragraph:

> Projections are run in two ways. In the joint arm, used for every projection in this paper, each posterior draw is
> paired with one of the 841 FaIR configurations, so the spread combines parameter and climate uncertainty. In the
> fixed arm, every draw is driven by the FaIR ensemble mean: the per-year mean over the 841 configurations, taken
> separately for GMST and ocean heat content. The ensemble mean is smoother than any single configuration. It drives
> the calibration, which fits one observed history, and two checks of the calibration (Sect. 3.2), where climate
> spread would hide differences between chains or between fits.

This also answers Tony's comment on the TE forcing in Sect. 2.2.4 ("caveat about mean").

**Eqs. (1)–(2) and every other equation group. HAND.** Each group is typed as one run-on line ("…(1)dS = …"). Put
each equation on its own line as a Word equation with its number at the right: Eqs. (1)–(2), (3)–(7), (8)–(11),
(12)–(14).

**Parameter paragraph after Eqs. (1)–(2). CLOSE** (Tony 87). The descriptions are in.

**Block-temperature paragraph ("Each block b is driven…"). HAND.** Fixes the RGI 19 description, adds the
prior-propagation note, and is shorter:

> Each block is driven by its own regional temperature T_b. Through 2024, T_b is the HadCRUT5 annual anomaly averaged
> over the block's RGI regions, weighted by glacier area in 2000. After 2024, T_b(t) = A_b·G(t) + c_b, where G is GMST
> relative to 1850–1900, A_b is the block's amplification and c_b matches the 2014–2024 observed mean. The priors on
> A_b are truncated normals that span the regressions of each block's anomaly on the global anomaly over 1901–2024 in
> HadCRUT5, Berkeley Earth and GISTEMP: N(2.50, 0.45) on [1.80, 3.50] for SLOWG, N(1.45, 0.15) on [1.33, 1.82] for
> FASTG and N(0.72, 0.15) on [0.58, 0.88] for RGI 19. The glacier record ends before A_b affects the drivers, so the
> calibration builds the drivers once with the prior-centre values. A_b does enter the GlacierMIP3 constraints, which
> are given at global warming levels and converted to each block's temperature with A_b.

Optional extra sentence: "Centring the RGI 19 prior on the mean of the three regressions (0.68) changes the glacier
projections by less than 0.03 cm."

**Block descriptions (SLOWG, FASTG, RGI 19). HAND.**

- SLOWG: delete "(a prior of 2.50 for the ratio of local warming to global warming)", now given above, and change
  "the warming in these regions are strongly amplified" to "warming in these regions is strongly amplified".
- FASTG: delete "(a prior of 1.45)".
- RGI 19, shorter version:

> RGI region 19 (Antarctic and Subantarctic periphery). The ice volume in 2000 is 6.9 ± 1.8 cm SLE. This block is
> separate because the historical glacier target (Frederikse et al., 2020) assumes no Antarctic-periphery melt while
> the GlaMBIE series used from 2019 includes it, and because its amplification is much lower than that of the other
> two blocks. Its only direct observation is GlaMBIE's 2000–2024 mean rate for the region (0.049 ± 0.116 mm yr⁻¹),
> which constrains it weakly because Ladrillo treats GlaMBIE's annual errors as fully correlated. Its committed loss
> and response time rest on the GlacierMIP3 constraints shared by all three blocks (committed-loss fractions at 1.2,
> 1.5, 2.0 and 3.0 K and response-time anchors at 1.5 and 3.0 K; Zekollari et al., 2025). Its response time is the
> least constrained of the three (5–95% range 60–3200 yr at 1.5 K; Sect. 4.3).

# Page 5: rest of Sect. 2.2.1, start of Sect. 2.2.2

**Inventory sentence. HAND, and CLOSE Tony 107.** "(Millan et al., 2022, have similar glacier ice numbers)" →
"Millan et al. (2022) give similar volumes." as a separate sentence.

**Regrowth (broken paragraph). HAND.** The paragraph is split after "after cooling". Replace both pieces with:

> Ladrillo's glaciers can regrow after cooling, up to each block's 1850 extent. In the two larger blocks the 1850 ice
> was already out of equilibrium and committed to loss, consistent with the Leclercq et al. (2011) constraint on
> 1850–1900 melt, so full regrowth would require cooling below the 1850–1900 level. Partial regrowth begins whenever
> a block's temperature falls below the level its current volume is in equilibrium with (Sect. 4.3).

"In the two larger blocks" is needed: RGI 19's 1850 ice is committed in only about half the posterior draws.

**Basin abbreviations. CLOSE** (Tony 155). They were removed.

# Page 6: Sect. 2.2.2 Greenland

**Amplification paragraph and the next one ("The use of past local temperatures…"). HAND.** Merge them; the first
sentence becomes direct, the duplicate splice description goes, and S becomes φ (see the symbol table):

> Amplification. Ladrillo drives Greenland with regional temperature instead of GMST. Both basins use the HadCRUT5
> annual anomaly over southern Greenland (59–70° N; 11 grid cells weighted by their overlap with the RGI region 05
> outline and by land fraction), relative to 1850–1900. Regional temperature matters for the hindcast because
> Greenland warmed from about 1920 to 1930, stayed flat until about 1960 and then cooled to a low around 1990, a
> different shape from global temperature. The amplification is the regression through the origin of this series on
> the same product's global anomaly over 1901–2024: 1.97 in HadCRUT5, 1.51 in Berkeley Earth and 2.29 in GISTEMP. Its
> prior is their mean and standard deviation, N(1.92, 0.32), truncated to [1.51, 2.29]. Its decline with warming, φ,
> is the median over 40 CMIP6 models of the ratio of 30-year mean regional to global warming, binned by global warming
> and interpolated over 0.75–2.75 K (φ = 0.96 at 1.5 K and 0.86 above 2.75 K, relative to 1 at 0.94 K). Holding the
> amplification constant instead would add 0.7 cm (SSP1-2.6) to 7.6 cm (SSP5-8.5) of Greenland melt by 2300.

**Above-threshold channel. HAND.**

- Citation: "(Goelzer et al. (2025)." → "(Goelzer et al., 2025)."
- Simpler middle sentence: "It cannot be calibrated on observations alone, so we use as additional constraints
  ISMIP6 data at 2100 (Goelzer et al., 2020) and SICOPOLIS at 2300 and 3001 (Greve and Chambers, 2022)." →

> Observations cannot constrain it, so it is set to match ISMIP6 projections at 2100 (Goelzer et al., 2020) and
> SICOPOLIS projections at 2300 and 3001 (Greve and Chambers, 2022).

# Page 7: Greenland equations and Sect. 2.2.3 Antarctica

**Paragraph after Eqs. (3)–(7): s_b, level and tilt (Tony 208, 209, and your notes). HAND.** Replace from "The rate
scale s_b is 1…" to "…β_s = (1 − w)·e^ℓ;" with:

> The rate scale s_b is 1 for the active basin and is sampled as ln s_b for the high basin, so that halving and
> doubling the rate are equally likely a priori. The discharge rate is sampled as a level and a tilt at the
> reference temperature T_ref = 1.963 K (the 2015–2024 mean of the regional driver). The level, ℓ = ln r_s(T_ref), is
> the logarithm of the discharge rate at present-day temperature. The tilt, w = α_s·T_ref / r_s(T_ref), is the
> fraction of that rate that scales with temperature, so that α_s = w·e^ℓ / T_ref and β_s = (1 − w)·e^ℓ. In test
> chains, sampling (ℓ, w) instead of (α_s, β_s) reduced the correlation between the two parameters from 0.58 to 0.14.

Then simplify the end of the same paragraph (from "Through 2024 the regional temperature T is the observed series…"):

> Through 2024, T is the observed series. After 2024, it is A_G·φ(Ḡ₃₀(t))·G(t) plus the constant that matches the
> 2014–2024 observed mean, where A_G is the sampled amplification and Ḡ₃₀ the 30-year running mean of GMST. The
> calibration builds this series once with the prior-centre amplification (1.92).

**Eq. (8) and the line after it. HAND.** T_on → T_thr and w_r → ΔT_r, in the equation and in "with onset T_on =
4.69 K … ramp width w_r = 1 K".

**DAIS geometry paragraph (Tony 238, 249). HAND.**

> The seven DAIS geometry parameters (ais_mu, ais_bedheight0, ais_slope, ais_iceflow0, ais_precip_u, ais_runoff_Ton,
> ais_c) share a joint prior constrained by paleo sea-level evidence (Wong et al., 2017a). One change from BRICK:
> precipitation is sampled through u = ln P₀ + κ_P·T̄_A, with T̄_A = −18.0 °C on the DAIS scale, because the record
> constrains this combination; ln P₀ is then derived from u. Ladrillo's pre-1990 Antarctic hindcast is much closer to
> observational estimates than BRICK 2.0's (Fig. 1, Table 4). A key reason is the observational constraint: BRICK 2.0's
> Antarctic likelihood uses IMBIE data for 1992–2017 (IMBIE Team, 2018), while Ladrillo fits a series that starts in
> 1900 (Frederikse et al., 2020).

Then CLOSE Tony 238 and 249.

**Runoff line. HAND.** Fixes "0 deg C" and the c clash:

> The runoff line is sampled in the direction the data identify. Its height, h_R = h₀ + c_R·T_ant, depends on its
> height at 0 °C (h₀) and its temperature sensitivity (c_R). Sampling both directly leaves a correlation ridge, so
> Ladrillo samples the runoff onset temperature, T_on = −h₀/c_R, which is what the data constrain.

# Page 8: Sect. 2.2.3 (continued), 2.2.4, 2.2.5

**Fast-dynamics paragraph (Tony 273). HAND.** Shorter, with the "low confidence" wording Tony suggested. Check the
exact AR6 wording before keeping the second sentence.

> The fast-dynamics parameters are propagated, not sampled. There is little observational evidence that fast
> dynamical processes have driven past Antarctic ice loss, and AR6 assigns low confidence to projections that include
> marine ice-cliff instability (Fox-Kemper et al., 2021). The disintegration rate λ, its temperature threshold T_crit
> and the ice-flow exponent γ are flat in the likelihood over 1900–2025: when sampled, their posterior width equals
> their prior width. Ladrillo therefore holds them at their DAIS paleo-ensemble medians during calibration
> (λ = 0.0099 m yr⁻¹, T_crit = −15.7 °C, γ = 2.83). In projection, each posterior draw gets a joint draw of
> (λ, T_crit) from that ensemble. The joint draw keeps the ensemble's correlation between the two (r = +0.45);
> independent draws would put four times as many draws in the corner of high λ and low threshold, where the sheet
> collapses under modest warming. Under the calibration likelihood, every draw whose fast dynamics start by 2025 has
> a weight below 10⁻²⁰, so the joint arm drops those draws: 3 of 2,000 in the SSP scenarios and 2 of 2,000 in the van
> Vuuren scenarios.

**Antarctic amplification (joint-arm numbers). HAND.** New numbers from `outputs/diag_ais_amp_joint_L27.csv`
(identity gates pass; the old values were fixed-arm):

> Antarctic amplification is a key parameter. BRICK 2.0 maps global to Antarctic surface temperature with a fixed
> ratio of 1.196, based on an equilibrium relationship (Shaffer, 2014; Wong et al., 2017b). Ladrillo instead samples a
> transient ratio from N(1.09, 0.18), based on the CMIP6 mean and between-model spread. Its effect depends strongly on
> the scenario. Raising the ratio by one standard deviation raises Antarctic sea level at 2300 by 39 cm on average
> under SSP2-4.5 (15% of that scenario's median total), but by 25 cm under SSP5-8.5 (5%), because SSP5-8.5 is already
> past the thresholds where amplification matters. Using BRICK 2.0's ratio of 1.196 instead would raise the SSP2-4.5
> median total by 11 cm at 2100 and 32 cm at 2300 (6 and 13 cm under SSP5-8.5).

**Thermal expansion, the α sentence. HAND (needed: "within 4%" holds only against 0–2000 m heat).** FaIR's ocean
heat is Earth's total heat uptake. Against IGCC's total, the observations imply a smaller α. Replace "The posterior
median of α is 0.167 … differences between FaIR ocean heat content and observations." with:

> The posterior median of α is 0.167 (5–95% 0.148–0.186). FaIR's ocean heat content is Earth's total heat uptake, so
> the matching observational value divides the observed thermosteric rate by IGCC's total heat uptake. Over 1993–2020
> that value is 0.141, below the posterior range. Sect. 4.1 attributes the resulting overshoot to the timing of FaIR's
> heat uptake.

Also change "(the mean over the 841 configurations, in 10²² J relative to 1850–1900)" to "(in 10²² J relative to
1850–1900; the ensemble mean in calibration, each draw's paired configuration in projection)". Then CLOSE Tony 321.

**Sect. 2.2.5 land water. HAND (simplification; it also fixes an unmatched parenthesis).**

> Neither Ladrillo nor BRICK 2.0 models land-water storage (LWS); both take it from observations. Ladrillo's hindcast
> uses Frederikse et al. (2020) through 2018, then Jet Propulsion Laboratory (JPL) GRACE/GRACE Follow-On mascons for
> 2019–2023 (land mass with the ice sheets masked, minus GlaMBIE glacier mass), held constant through 2025. From 2024,
> both models continue LWS at 0.30 mm yr⁻¹, the mean of the N(0.30, 0.18) mm yr⁻¹ rate that BRICK 2.0 draws, so LWS
> adds 8.8 cm by 2300 relative to 1995–2014 in every scenario and in both models. BRICK 2.0 as published sets LWS to
> zero before 2019, so the observed series is added to its total for comparison. In calibration, LWS enters only
> through the DAIS sea-level feedback; a stylized series (zero through 2018, then 0.30 mm yr⁻¹) changes the Antarctic
> contribution by less than 0.02 cm.

# Pages 8–11: Sect. 3.1 and Table 3

**Table 3 caption (Tony 351, 372: "offset"). HAND.** Add one sentence; then CLOSE both:

> Offset-matched: shifted by a constant so that the two series have the same mean over the stated overlap years.

**GlaMBIE row, "what it constrains" (Tony 349). HAND**, matching your reply; then CLOSE:

> Glaciers 2019–2023, offset-matched to Frederikse over 2003–2018; also two point constraints (Sect. 3.2).

**Table 3, version column. HAND (optional).** Journal shorthand repeats the reference list ("PNAS 116:9239",
"PNAS 116:1095", "Nat. Geosci. 12:168", "Surv. Geophys. 32:519", "Science 388:979"). The citation is enough.

**Note 18. HAND.** Remove the stray spaces in "( World Glacier  Monitoring Service;".

**GlacierMIP3 row (Tony 354), CMIP6 row (Tony 361). CLOSE.**

**"Datasets removed" paragraph. HAND.** The last two sentences read as if land water were fitted:

> Ladrillo is therefore fitted only to the four component series (Greenland, Antarctica, glaciers and thermal
> expansion) and the point constraints above; observed land-water storage is an input. The total sea-level hindcast in
> Fig. 1 and Table 4 is compared with observations as an out-of-sample check (Dangendorf et al., 2024, extended with
> NOAA STAR altimetry over 2022–2024).

**IMBIE 2026 paragraph. HAND, and CLOSE Tony 431.** Add the post-2002 rate disclosure after the Antarctic sentence
(receipt `outputs/diag_ais_rate_2002_per_draw_L27.csv`):

> From 2002, Ladrillo's Antarctic rate is lower than its target: 0.29 mm yr⁻¹ (5–95% 0.25–0.33) over 2002–2021, below
> 0.42 ± 0.03 mm yr⁻¹ for the Frederikse–GRACE target in every posterior draw, and 0.52 ± 0.05 mm yr⁻¹ for IMBIE 2026.
> The gap narrows as later years are included (2002–2025: 0.31 against 0.37 ± 0.05 mm yr⁻¹).

Citation form: "(Otosaka et al., 2026) (which starts…)" → "(Otosaka et al., 2026), which starts…".

# Pages 11–13: Sect. 3.2

**Parameter-count paragraph. HAND.**

- "one discrepancy basis of two coefficients" → "a two-coefficient discrepancy term for thermal expansion".
- "Five Antarctic changes distinguish Ladrillo's calibration from BRICK 2.0's — the four described above, plus…"
  counts changes that Sect. 2.2.3 never numbers (a reader can find five or six there). Simpler and safe:

> Several Antarctic changes distinguish Ladrillo's calibration from BRICK 2.0's: those in Sect. 2.2.3, and an SMB
> likelihood term that anchors the Antarctic flux scale to Rignot et al. (2019). Without that term the net balance is
> well constrained, but surface mass balance and discharge are not separately identified (about ±505 Gt yr⁻¹ each in a
> calibration without it), which allows compensating errors.

**Forcing. HAND.** "future emissions of each of the 51 included species is scaled by the ratio of history to scenario
at 2023.5" →

> Future emissions of each of the 51 species are scaled by the ratio of historical to scenario emissions at 2023.5.

**Discrepancy terms (Tony 474–478 and your note). HAND.** Simpler version:

> Thermal-expansion discrepancy. A discrepancy term δ(t) is added to the modelled thermal expansion before it is
> scored. δ(t) is the sum of a linear and a quadratic trend over 1900–2025, each with its own coefficient. Before
> fitting, both trends are made uncorrelated with a constant and with FaIR's ocean heat content over 1900–2025, so δ
> cannot reproduce the effect of a change in α or in the baseline. Each coefficient is the root-mean-square size of its
> trend in cm and has a N(0, 0.5 cm) prior. In the posterior the quadratic coefficient spans zero (0.07 cm, 5–95%
> −0.05 to 0.20), while the linear one does not (0.21 cm, 5–95% 0.01 to 0.40). The linear term represents the part of
> FaIR's ocean-heat timing error (Sect. 4.1) that rescaling cannot fix. Figure 1 and Table 4 show the module without
> δ(t), for a cleaner comparison with BRICK 2.0, which has no such term.

Then CLOSE Tony 474–478.

**ρ bound (Tony 486, your "yes"). HAND.** Use "<" everywhere: Table 5 rows "ρ ≤ 0.95" and "ρ ≤ 0.90" (if they still
read ≤), and in Sect. 4.1 "at the calibration's ρ ≤ 0.99 bound" and "at ρ ≤ 0.95". Then CLOSE.

**Sampler. HAND.** "the ice-flow constant f₀" → "the ice-flow constant (ais_iceflow0)" (f is already Greenland's SMB
share).

**Convergence paragraph (Tony 497, 502). HAND.** The current sentence says 8 parameters fail R̂ < 1.05, but only 3
do; all 8 fail the ESS > 400 part (`outputs/log_l27_postprocess_driver.txt`). Shorter version that also explains the
fixed arm:

> Convergence. We assess convergence with the rank-normalized split-R̂ of Vehtari et al. (2021), a form of the
> Gelman–Rubin statistic (Gelman and Rubin, 1992) that compares the spread across chains with the spread within them;
> it approaches 1 when the four chains sample the same distribution. Our gate is R̂ < 1.05 with an effective sample
> size (ESS) above 400, and 42 of the 50 parameters pass. The 8 that fail are all Antarctic, including the geometry
> parameters, which share a joint prior and compensate for each other, and the ocean-temperature parameters. Three exceed
> R̂ = 1.05 (ais_runoff_Ton 1.31, ais_c 1.08, ais_slope 1.06); all eight have ESS below 400 (20–244). The chains show
> these parameters moving along weakly identified, compensating directions (Table A2 gives the combinations the record
> does identify). Projected sea level converges: R̂ = 1.001 at 2100 and 1.002 at 2150 under SSP2-4.5, with ESS of
> about 1,240 and 1,250, from 400 draws per chain (every 2,500th retained iteration). This check and the refit
> comparison below use the fixed arm, so that climate spread does not hide differences between chains or fits. An
> independent refit (different seeds, starting points and proposal covariance) reproduces every Antarctic projection
> median to within 1.8 cm at 2300 and the hindcast to 0.005 cm. The weakly identified geometry directions differ by up
> to 0.8 posterior standard deviations between the two fits without changing the projections.

Then CLOSE Tony 502 (its sentence is gone). For Tony 497 ("PSRF < 1.1 is also used"): only ais_runoff_Ton exceeds
1.1. If you mention 1.1, cite a source for it; Gelman et al. (2013) is my recollection, so check it. A reviewer may
also note that Vehtari et al. (2021) recommend R̂ < 1.01 (also my recollection). The projection R̂ meets 1.01.

**Reproducibility and computing. HAND.**

> All results are reproducible: every random seed is fixed and recorded in the output file that each figure reads.
> The calibration ran on an Apple M4 laptop (10 cores, 16 GB RAM); the four chains of 2 million iterations ran in
> parallel in about 4 h, after a 500,000-iteration tuning chain.

# Page 13: Sect. 3.3 Verification

**Tony 522. HAND.** "The level-and-tilt form of the discharge rates is checked against the native form, to 10⁻¹²…" →

> The level-and-tilt form of the discharge rate (Sect. 2.2.2) is checked against Eq. (4) to 10⁻¹², each time the
> calibrator starts.

Also "linked to in the Code Availability section" → "listed under Code and data availability".

# Pages 14–16: Sect. 4.1

**Fig. 1 (Tony 534). HAND:** insert the new file. CLOSE after the swap.

**Broken paragraph after "We note that". HAND.** Join it with "the non-closure…".

**Information-criteria paragraph (Tony 661, 664). DECIDE + HAND.**

- Tony 661 (independent errors): recommended, keep the Table 5 row and reduce the sentence to one clause at the
  end of the paragraph (below).
- Tony 664 (ρ tests): name the last two Table 5 rows as tests of tighter bounds on ρ.

> Improvements in Ladrillo's hindcast are not due to extra parameters. Ladrillo samples 50 parameters against
> BRICK 2.0's 35, so the gains in Table 4 could reflect overfitting. Following Wong et al. (2017b), we compare the
> models with the Akaike and Bayesian information criteria (AIC = 2k − 2 ln L, BIC = k ln N − 2 ln L; Akaike, 1974;
> Schwarz, 1978), using each model's best posterior draw on the same four component series (N = 502
> observation-years; Table 5). Under the calibration's AR(1)-plus-observational-error likelihood, with σ and ρ
> refitted to each draw's residuals for each series, Ladrillo's log-likelihood is higher by 63. That is more than
> four times the AIC penalty (ΔAIC = +95) and positive on BIC (+32), even at the calibration's bound of ρ < 0.99,
> where the AR(1) term behaves like a random walk and absorbs BRICK 2.0's smooth biases. The last two rows of Table 5
> test tighter bounds; at ρ < 0.95 the BIC margin is +93. Glaciers and Greenland account for most of the gain (+26 and
> +31), thermal expansion +7 and Antarctica −1. With independent observational errors only, the gain is +1528. Two
> caveats: the maximum over draws underestimates each model's maximum likelihood, and Ladrillo was calibrated to these
> targets while BRICK 2.0 was calibrated to its own.

**Thermal-expansion paragraphs (Tony 699, 705; the α sentence). HAND.** Replaces both paragraphs. It removes
"within 4%", makes 1.24 the IGCC member of the 1.21–1.27 range, and writes the product out. It does not use Tony's
suggested sentence, which restates the attribution retracted on 2026-10-01.

> Ladrillo's thermal-expansion overshoot comes from the timing of FaIR's ocean heat uptake. In both models, thermal
> expansion is proportional to ocean heat. Both overestimate the 1993–2025 thermal-expansion rate, Ladrillo by a
> factor of 1.22 and BRICK 2.0 by 1.13. A constant scale difference between FaIR and the observations would be
> absorbed by α. The overshoot comes from timing instead: FaIR's heat uptake is back-loaded, with a 1900–1949 rate
> 0.13 of its 1993–2024 rate, against 0.24 for the steric target and 0.21 for observed 0–2000 m ocean heat, so no
> single α fits both periods.
>
> FaIR's ocean heat uptake is also larger than the 0–2000 m observations that the steric target is built from, by a
> factor of 1.21–1.27 depending on the product. For IGCC over 1993–2020 the factor is 1.24, the product of three
> terms: 1.11 because FaIR's ocean is full-depth (IGCC estimates warming below 2000 m at about 11% of the 0–2000 m
> uptake), 1.10 because FaIR counts as ocean heat the roughly 9% of Earth's heat uptake that goes to land, ice and the
> atmosphere, and 1.02, the remaining difference between FaIR and IGCC's total heat uptake (1.11 × 1.10 × 1.02 ≈
> 1.24).

# Pages 17–20: Sect. 4.2 and Figs. 2–6

**Component paragraph ("On glaciers, Ladrillo and MAGICC-SLR share…", Tony 731). HAND.** Tony asks to tie each
component to the projection differences. A sentence you could add for glaciers, from the new ablation:

> Ladrillo's glacier contribution is lower than BRICK 2.0's in every scenario, by 9–14 cm at 2300. Giving BRICK 2.0
> Ladrillo's glacier inventory closes only 10–20% of that gap in the low and middle scenarios, so most of it comes from
> the glacier formulation.

Similar one-line ties for the other components, from Fig. 3 at 2300: Greenland, Ladrillo lower in six scenarios
(by 3–9 cm) and higher in High (+20 cm, the above-threshold channel); Antarctica, within 7 cm except High-to-Low
(−18 cm) and High (+31 cm); thermal expansion, Ladrillo 1–6 cm higher in every scenario (same module, different α).

**Figs. 2–4 and 6. HAND:** insert the lettered files. Captions need no change; you can now cite "(c)" for the
Antarctic panel.

**Fig. 5 (Tony 766, 761). HAND:** insert `vv_gsic_ladrillo_L27_2300_joint.png` and replace the caption:

> Figure 5. Ladrillo glacier contribution to 2300 across the seven van Vuuren scenarios: GMST forcing, the FaIR
> ensemble mean (a), cumulative glacier melt (b), and the melt rate on the four peak-and-decline pathways, Very Low,
> Low-to-Negative, Medium-to-Low and High-to-Low (c). Joint arm; the shaded band is the 5–95% range for Very Low.
> Regrowth of about 0.08 cm occurs on Low-to-Negative as temperatures drop below reservoir equilibrium levels.

Then CLOSE Tony 761 and 766.

**FACTS paragraphs after Fig. 6 (Tony 775). HAND (simplification).** The two paragraphs become one. Reply to Tony
that the cutoff is FACTS's default and that removing it is worse, as the text shows; then CLOSE.

> Past 2100, Figs. 3 and 6 show only the FACTS modules that respond to the FaIR climate: glaciers, thermal expansion
> and land-water storage, plus LARMIP Antarctica at 2150. FACTS's Greenland module (FittedISMIP; Fox-Kemper et al.,
> 2021) fits the melt rate to 2015–2100 ISMIP6 runs as a cubic in temperature plus a quadratic in time, and by
> default continues each sample at its 2080–2100 mean rate after 2100 (46 cm at 2300 for High-to-Low). Evaluating the
> fit through 2300 instead gives 112 cm even though the climate cools, because the time terms keep growing beyond the
> fitting period. The Bamber and DeConto modules select projections from temperature integrated over 2000–2099, the
> AR5 Antarctic dynamics term is a prescribed function of time, and LARMIP's 200-year response functions give no weight
> to pre-2100 forcing by 2300. Workflow totals that include these modules are omitted past 2100. SLEIP's 2300 FACTS
> values are these extrapolations (Nauels et al., 2026).

# Page 21: Sect. 4.3

**High scenarios (Tony 788, 802, "sit together"). HAND.** Adds FACTS at 2100, replaces "sit together" (427 and
383 cm are 44 cm apart), drops "actually" and uses "climate drivers":

> High scenarios. At 2100 the models are fairly similar for the High scenario: Ladrillo 73 cm, BRICK 2.0 79 cm,
> MAGICC-SLR 62 cm and FACTS 56–76 cm across its workflows (relative to 2005). By 2300, Ladrillo (427 cm) and BRICK 2.0
> (383 cm) are both well below MAGICC-SLR (567 cm), mostly because of Antarctica (249 and 218 cm against 380 cm).
> Driving Ladrillo and BRICK 2.0 with MAGICC's climate lowers their totals by 17–20 cm (to 410 and 363 cm), mainly
> through thermal expansion, so the gap comes from the ice-sheet modules and not from the climate drivers.

Then CLOSE Tony 788 and 802.

**Antarctic spread paragraph (Tony 810, 811). HAND**, then CLOSE:

> Ladrillo's 2300 Antarctic spread comes mostly from the fast-dynamics rate λ. Ladrillo attaches λ to each draw jointly
> with its threshold (Sect. 2.2.3), from the same DAIS ensemble that BRICK 2.0 samples (mean 0.0104 and sd 0.0036 in the
> ensemble; 0.0104 and 0.0035 in BRICK 2.0's posterior), so the two Antarctic spreads are similar (5–95% widths of 268
> and 307 cm at 2300).

**Lin et al. (2026) and Poinelli et al. (2026). DECIDE.** Recommended: one short paragraph here. Numbers are from
`outputs/diag_ais_2100_vs_lin2026_L27.csv` (change from 2015 to 2100; Lin's drift-corrected row, as you ruled on
10-17). Neither paper is in the reference list yet.

> Lin et al. (2026) emulate the ISMIP6-2300 ensemble, calibrated to the observed 2002–2021 Antarctic rate. Their
> projections of the Antarctic contribution from 2015 to 2100 are 5.2 cm (5–95% 1.2–9.7) for SSP2-4.5 and 7.7 cm
> (1.9–16.2) for SSP5-8.5. Ladrillo's are higher, 10.0 cm (3.8–57.2) and 36.3 cm (6.9–69.3). Without DAIS fast
> dynamics (λ = 0), Ladrillo gives 5.4 cm (3.6–8.8) and 7.5 cm (4.6–12.9), within Lin et al.'s ranges, so most of the
> difference at 2100 comes from the fast-dynamics term. Poinelli et al. (2026) find that Thwaites Glacier alone could
> contribute 1.9–3.0 cm by 2100 under constant climate when grounding-zone melt is resolved, up to about twice the
> ISMIP6 mean for that glacier. Results for single glaciers are difficult to compare with a model that represents Antarctica
> as one sheet.

**Low scenarios. HAND** ("at the low end" is not right; it is between the other two):

> Low scenarios. For Very Low, Ladrillo's 2300 median total (61 cm) lies between MAGICC-SLR (46 cm) and BRICK 2.0
> (80 cm). Ladrillo's spread is narrower than BRICK 2.0's on every component and narrower than the FACTS glacier and
> thermal-expansion modules. MAGICC-SLR is narrowest for Antarctica, thermal expansion and the total (2300 total 5–95%
> width 68 cm, against 166 cm for Ladrillo and 221 cm for BRICK 2.0).

**Peak-and-decline (Tony 837, 857). HAND.** One paragraph instead of two, with the arithmetic in the order Tony
asked:

> Peak-and-decline scenarios. Ladrillo's glaciers can regrow (Eqs. 1–2), but on its FaIR climate the regrowth is
> small: from each scenario's peak to 2300 it reaches 0.08 cm in Low-to-Negative and is negligible elsewhere.
> MAGICC-SLR's glaciers regrow 8.55 cm in Low-to-Negative. About ¾ of this difference comes from model structure and
> ¼ from climate: driven by MAGICC's colder climate, Ladrillo's glaciers regrow 1.91 cm, closing 1.83 cm of the
> 8.47 cm gap.

Then CLOSE Tony 837 and 857.

# Page 22: Conclusions

**First paragraph (my comment on "up to 18 cm"). HAND**, then CLOSE the bubble. "Reductions of up to 18 cm" holds in
3 of 10 scenarios; Ladrillo is higher in the other 7.

> While Antarctica still uses the DAIS model, its updated calibration substantially improves the match to
> observations. It changes the 2300 Antarctic median relative to BRICK 2.0 by −18 to +47 cm, depending on the
> scenario. Remaining mismatches in historical thermal expansion come mainly from the timing of FaIR's ocean heat
> uptake. A future version could calibrate thermal expansion against observed ocean heat and use FaIR only for future
> changes.

**Runtime sentence. CLAUDE** (re-measure). Text simplification you can make now: "so making scenario projections for
a 10,000-draw ensemble takes about a minute" → "so projecting 10,000 draws for one scenario takes about a minute".

# Appendix A: Table A1

**Four rows in ln (your 2026-11-10 choice). HAND.** In the rows for the three glacier κ and `gis_s_high`, replace the
description, units, prior and posterior entries with the values below. Keep the parameter names in the first column,
because they match the columns of the posterior file. Values are from `outputs/ladrillo_prior_posterior_L27.md`
(rebuilt at commit b8d7fdf; same precision rule as the rest of the table).

| Parameter | Description | Units | Prior | Median | 5% | 95% |
|---|---|---|---|---|---|---|
| `gic_log10_kappa_R19` | ln of the response-rate constant κ, RGI 19 | ln(yr⁻¹ K⁻ν)ᶜ | N(κ̂(amp), 0.262) on [−9, −3.81]ᵃ | −6.4 | −6.9 | −5.9 |
| `gic_log10_kappa_SLOWG` | ln of the response-rate constant κ, SLOWG | ln(yr⁻¹ K⁻ν)ᶜ | N(κ̂(amp), 0.262) on [−10.9, −4.99]ᵃ | −8.01 | −8.5 | −7.5 |
| `gic_log10_kappa_FASTG` | ln of the response-rate constant κ, FASTG | ln(yr⁻¹ K⁻ν)ᶜ | N(κ̂(amp), 0.262) on [−8.69, −3.5]ᵃ | −6.01 | −6.36 | −5.65 |
| `gis_s_high` | ln rate scale of the high basin (NO+NE) relative to the active basin | ln(–)ᶜ | N(0, 1.15) on [−4.61, 4.61] | −1.29 | −1.81 | −0.83 |

Add footnote ᶜ to the end of the caption:

> ᶜ sampled as log₁₀ in the code and the posterior file; shown here as ln = ln 10 × log₁₀ (ln 10 = 2.303).

---

# Pages 35–37: back matter

**Code and data availability (your placeholder comment). DECIDE + CLAUDE.** See the "Waiting on Claude" table. The DOI
and repository URL stay as placeholders until the repository is public and the Zenodo release exists.

**Acknowledgements. HAND.** Frank Errickson is still missing. Consider S. Dangendorf (the corrected file in Table 3
note 21).

**References. HAND.**

- Morlighem et al. (2017): DOI `10.1022/…` → `10.1002/2017GL074954`.
- Sarofim et al. (2021): pages "11, 1–3" look like a placeholder; check against the DOI.
- Rennels et al. (2022, Mimi): the author list ends with the GitHub handle "Catawbasam"; cite the v1.6 release DOI.
- To add: Lin et al. (2026) and Poinelli et al. (2026) if used; RCMIP v5.1.0 and the CMIP7 historical emissions
  (Sect. 3.2 Forcing); NOAA STAR (product page); Church and White's 2015 update (named in Sect. 3.1).
- Citation commas: "(Frederikse et al. 2020)" in Sect. 2.2.5; "(Fox-Kemper et al. 2021)" if you keep that form;
  "(Wong et al., 2017b and Shaffer 2014)" → "(Shaffer, 2014; Wong et al., 2017b)".
- Units: "Gt/yr" → "Gt yr⁻¹" (Table 3, note 17, Sect. 3.2).

---

# Symbol renaming

Renaming only the first four removes the clashes a reader is most likely to hit. If you rename symbols that appear in
Table A3 ("Greenland symbols as in Eqs. (3)–(11)"), update that table to match.

| current | meaning | where | suggested |
|---|---|---|---|
| T_on (Greenland) | onset of the above-threshold channel, 4.69 K GMST | Eq. (8) and the line after | **T_thr** |
| T_on (Antarctica) | runoff onset temperature | Sect. 2.2.3, Table A1 | keep |
| κ (Antarctica) | precipitation sensitivity in u = ln P₀ + κ·T̄ | Sect. 2.2.3 | **κ_P** |
| κ (glaciers) | response-rate constant | Eq. (2), Table A1 | keep |
| a (Greenland) | regional amplification | Sect. 2.2.2 (after Eq. 7) | **A_G** |
| a (glaciers) | committed-loss scale | Eq. (1) | keep |
| S (function) | CMIP6 decline of the Greenland amplification | Sect. 2.2.2 | **φ** |
| S (glaciers) | cumulative loss since 1850 | Eqs. (1)–(2) | keep |
| T̄ (Greenland) | 1.963 K reference temperature | Sect. 2.2.2 | T_ref |
| T̄ (Antarctica) | −18.0 °C on the DAIS scale | Sect. 2.2.3 | T̄_A |
| α | thermal-expansion coefficient | Sects. 2.2.4, 4.1 | α_TE (optional) |
| w_r | ramp width of the above-threshold channel | Eq. (8) | ΔT_r |
| L_i, L_m | likelihood terms | Eqs. (12), (14) and text | 𝓛_i, 𝓛_m (keep L for the e-folding length) |
| c (Antarctica) | runoff-line temperature sensitivity | Sect. 2.2.3, Table A1 note | c_R |
| f₀ | ice-flow constant (text only) | Sect. 3.2, Sampler | write "ais_iceflow0" |
| P(t) and P₀ | Greenland channel; Antarctic precipitation | Eqs. (7), (11); Sect. 2.2.3 | optional; low risk |

# Other places to simplify (optional)

- **Sect. 3.3 Verification** is one 330-word paragraph. A numbered list, (i) to (iv) plus the MCMC and BRICK 2.0
  checks, would read faster with no change in content.
- **Table 3 notes 17, 19, 20 and 21** carry provenance detail (SHA-256 prefix, fetch dates, file names). Moving them
  to Code and data availability would shorten the table.
- **Sect. 2.2.2 "Two channels" and "Two basins"** could be one paragraph.
- **The Introduction's first paragraph** ends with a long sentence on structural uncertainty. It could become two
  sentences.

# Comments you can resolve now

These are already handled in the text: Tony 87, 107 (with your reply), 155, 249, 354 and 361 (with your replies),
431, 486 (with your reply), 502. Tony 273 can close once you choose the fast-dynamics wording. The rest close with the
edits above, each marked CLOSE.
