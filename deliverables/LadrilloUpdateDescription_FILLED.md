# Ladrillo Sea Level Rise Emulator

Ladrillo is a derivative of Tony Wong's BRICK2.0 model. Ladrillo was developed by Marcus C Sarofim using the Claude model. The primary goals for Ladrillo were to add additional observational data, update the glacier module to better match observations and to halt melting for stabilization scenarios, update the Antarctic calibration approach to better match observations prior to 1980, and update the Greenland model to incorporate the different responses of surface melt balance and ice discharge.

Ladrillo is comparable in quality to other sea level emulators, and occupies its own niche. Unlike MAGICC, Ladrillo is designed to work with the FaIR model. Unlike FACTS, Ladrillo has a simplified structure. Ladrillo does a good job matching historical observations, with the primary weakness being thermal expansion, though that is inherited from FaIR and does not appear when running with OHC from observation. For future projections, Ladrillo matches physical expectations and is comparable to the other models despite different structural approaches. BRICK's design philosophy is to calibrate on historical data products rather than to emulate projections from process-based models, which is what makes it a line of evidence relatively independent of the large Earth system and ice sheet models. Ladrillo extends that philosophy where the data reach — the Antarctic likelihood now runs from 1900 rather than IMBIE's 1992–2017 window, and Dangendorf, GlaMBIE, GRACE and Mouginot are added — but departs from it for two key parameters not constrained by observations. The first is a Greenland tap that triggers above a threshold temperature and is informed by SICOPOLIS. The second is the use of local temperature amplification relative to global that is informed by CMIP6 in addition to historic observations, and is relevant for Antarctic melt.

> **Vintage.** This document describes posterior L24. Units are cm. Two baseline windows are used: 1995-2005 for the hindcast section (FIG 1, the RMSE table, and the 2024 levels); and 1995-2014 for the projection sections. Model version FaIR 2.2.4 (fair-calibrate 1.6.0). Observational vintages are given in the calibration-data table below. Both hindcast arms are reproducible: every random seed is fixed and is recorded inside the output file each figure reads, so any number here can be regenerated from the artifact alone.

## Ladrillo Structural Updates

### GSIC

BRICK 2.0's glacier model uses a Wigley-Raper equation that is always melting when above its equilibrium temperature. Ladrillo replaces it with a Mengel-style equilibrium volume `S_eq` driven by a Nauels-ν transient, which separates *how much* ice is committed at a given warming from *how fast* it gets there, and splits the world into three reservoirs on regional temperature.

**SLOWP — RGI regions 03, 09, 07, 06** (Arctic Canada North, Russian Arctic, Svalbard, Iceland). Large, high-latitude, long relaxation time, and strongly amplified relative to global mean temperature (prior 2.50). This block dominates the glacier contribution in both the hindcast and the projections.

**FAST — 13 other RGI regions.** Smaller, faster-responding bodies with weak amplification (prior 1.45). It equilibrates quickly enough that its committed volume is close to its realised volume through most of the record.

**R19 — Antarctic and Subantarctic periphery.** This block exists because the historical glacier target (Frederikse) assumes zero Antarctic-periphery melt, while the GlaMBIE series spliced in from 2019 onward includes it. Folding R19 into either SLOWP or FAST would leave the model's hindcast scope mismatched. Keeping it separate lets the hindcast be evaluated on SLOWP + FAST while R19 still contributes to projected totals. Its amplification prior (0.72) is also far below the other two, so it is not physically interchangeable with them either.

These three blocks cover 18 of the 19 RGI regions; RGI 05, Greenland Periphery, is excluded — Frederikse's glacier target excludes it and it falls inside the Greenland ice-sheet mask.

**Compared with BRICK 2.0 and MAGICC.** BRICK 2.0 and Ladrillo now have completely different glacier modules. MAGICC and Ladrillo both use the formulation from Nauels 2017 Eq. 3; where they differ is the three regions used in Ladrillo. MAGICC's committed 1850 melt is 2.8–13.6 cm, Ladrillo's 6.3–14.6 cm. The two models also start from different total glacier inventories. BRICK 2.0's calibrated initial volume centres on 42 cm SLE (5–95% 32–52), inherited from the Wigley and Raper (2005) assumed maximum of 41 cm; Ladrillo constrains the remaining stock at 2000 to 29.0 ± 6.0 cm SLE on its target scope (Farinotti 2019 excluding RGI regions 5 and 19, plus 6.9 cm for region 19), with Millan 2022 agreeing to 1% on the matched scope. The full-RGI Farinotti value is 32.4 ± 8.4 cm. The comparators' inventories are larger and differ in scope: FACTS's AR5 glacier module caps cumulative melt at 31.6 cm SLE (AR5 Table 4.2's 41.2 cm less 9.63 cm; its regional fingerprints include the Greenland periphery and no Antarctic periphery), which every SSP5-8.5 sample reaches by 2300; MAGICC's tabulated equilibrium curves reach 35.6–45.1 cm SLE across their 15 tunes. Ladrillo's glaciers exclude RGI 05 (about 3.4 cm SLE, carried inside its Greenland ice-sheet mask), so its glacier contribution is structurally smaller than the comparators' by that region's melt.

**Regrowth potential.** Neither BRICK nor FACTS can regrow glacial ice, but MAGICC and Ladrillo can. The equations governing melt are:

    S_eq = max( a·(1 − exp(−b·(T − T_off))), 0 )        
    dS   = min( κ·|T − T_eq|^ν, 1 ) · (S_eq − S)        

**Regrowth limits.** MAGICC assumes that once ice committed to melt in 1850 has gone, it can't be regrown, but ice lost past that point can be. In theory, Ladrillo can regrow up until its 1850 ice extent (though no further), but that would require temperatures to drop below 1850 levels.

### Greenland

BRICK 2.0 treats Greenland as one body with one response channel responsive to global temperatures. Ladrillo replaces that with a two-channel, two-basin sheet that responds to local temperatures.

**Two channels (fast / slow).** Greenland melt occurs through surface-mass-balance response (fast) and outlet/dynamic discharge (slow). Two channels allow for that partition. "Fast" names which physics the channel carries, not a short time constant — the surface-mass-balance channel drains a multi-millennial commitment, and at the optimum its response time is 86 years.

**Two basins.** The sheet is split into an active basin (SW+CW+CE+SE+NW) and a high basin (NO+NE), each carrying its own fast/slow channel pair, with sector shares scored against Mouginot.

**Amplification.** The ratio of Greenland warming to global warming is itself a function of temperature.

**High-basin volume tap.** A post-2100 commitment above a threshold: V = 564 cm, τ = 800 yr, onset 4.69 K, two stages, whole-sheet. The tap does not fire until temperatures exceed the onset. It cannot be calibrated on observations, so the parameters were informed by ISMIP6 at 2100 and SICOPOLIS at 2300 and 3001. It is included in every projection here, contributing 35.1 cm to the SSP5-8.5 total at 2300 on the joint arm this document reports throughout, and nothing at SSP1-2.6 (exactly zero) or SSP2-4.5 (+0.04 cm).

**Compared with BRICK 2.0 and MAGICC.** The observed Greenland contribution rises quickly from the 1930s to the 1960s, nearly stalls from the 1960s to 1990, then accelerates; BRICK 2.0's single-channel response to global temperature yields an almost uniform rate across the century (0.46–0.49 cm/decade in every 30-year period against an observed 0.67 then 0.23), so it runs about 1 cm low through the 1950s–60s and 0.2 cm low since 2010. Ladrillo reproduces the shape because its fast surface-mass-balance channel responds to Greenland's local warming of about 1.2 °C during 1920–45 (in contrast to 0.2 °C globally), then local cooling through 1990 while the globe warmed. Meanwhile, the slow discharge channel carries the long-term trend. MAGICC similarly splits Greenland into SMB and SID and parameterises against SICOPOLIS, but with 17 parameters between the two, of which 9 vary and each of those takes only 4 distinct values. MAGICC’s Greenland melt module starts in 1990, and underestimates melt relative to observations over the 1990-2026 period.

## Ladrillo Calibration Data Updates

**Table 1.** Observational inputs added or replaced relative to BRICK 2.0, with the version of each as used in the calibration.

| data source | vintage / version as used | what it constrains |
|----|----|----|
| Dangendorf 2024 GMSL | Zenodo `10.5281/zenodo.10621070`; GMSL derived from `Fields.nc`, not the record's `Global.nc` (mis-written upstream), and validated against a corrected `_v2.nc` supplied by S. Dangendorf, pers. comm. 2026-08-07 | The total, replacing the CSIRO (Church & White 2011 lineage, 2015 update) reconstruction BRICK 2.0 was calibrated to. |
| GlaMBIE glacier series (2019 onward) | Dataset 1.0.0, DOI `10.5904/wgms-glambie-2024-07`; acquired 2026-06-13; paper `10.1038/s41586-024-08545-z` | The modern glacier rate, spliced onto Frederikse. It includes Antarctic-periphery melt (R19) which is excluded by Frederikse. |
| JPL GRACE / GRACE-FO mascons | Release RL06.3Mv04 CRI, DOI `10.5067/TEMSC-3JC634`, granule `200204_202606` | Land-water storage. GRACE data run 2019–2023; the 2023 value is then held constant through 2026, the end of the calibration window. In projections LWS follows BRICK's stochastic land-water module from 2019. |
| Mouginot Greenland sector shares | `10.1073/pnas.1904242116`, Supplementary Dataset S2 (`pnas.1904242116.sd02.xlsx`, sheet "(2) MB_GIS"). No dataset version is published | The basin split, as a shares term rather than a level. |
| Rignot 2019 Antarctic SMB, area-corrected ×0.888 | *PNAS* 116:1095; 2098 ± 133 Gt/yr over the 1979–2008 climatology, entered as published values | The absolute Antarctic flux scale. SMB minus discharge is well constrained at −145 ± 15 Gt/yr but each flux individually has high uncertainty (±505/±509), so Rignot anchors the pair. |
| Glacier inventory likelihood + a 19th-century flow constraint, `S(1900) − S(1850) ~ N(2.0, 0.9)` cm SLE | Inventory: Farinotti 2019 (*Nat. Geosci.* 12:168) reconciled per Hock 2023, at the RGI ~2000 outline epoch, entered as published values; region polygons GTN-G Glacier Regions 2023, DOI `10.5904/gtng-glacreg-2023-07`, on the RGI6 scheme. 19th-c flow: Leclercq/Oerlemans/Cogley 2011, DOI `10.1007/s10712-011-9121-7` | The absolute inventory and the pre-observational flow. |
| CMIP6 regional amplification (34–41 models) | Pangeo/Google-Cloud CMIP6 zarr catalogue, fetched 2026-07-21 to 2026-08-24 (Greenland panel 2026-08-18, glacier panel 2026-08-23); member ID recorded per model and the panel pinned to the fetched files, so a later catalogue change cannot swap the ensemble | Priors on the per-block glacier amplification and on Antarctic amplification. |
| Paleo constraints on DAIS geometry, in a standardised correlation form | `DAISfastdyn_calibratedParameters_gamma_29Jan2017.nc` (sha256\[:16\] `0b53b45e2422563b`), the 16-parameter / 800,000-member ensemble shipped with MimiBRICK; extracted 2026-08-24 | The seven freed geometry parameters (below). |
| *(not a calibration target)* IGCC 2025-indicators GMSL | Tag `v2026.06.02`, data DOI `10.5281/zenodo.20499280`, md5 `8ae5ac0041e26351b9f497f969bd0dab`; paper Forster et al. 2026, `10.5194/essd-18-3889-2026` | Shown on FIG 1 as an independent consensus check on the total. |

**Deliberately removed: IMBIE.** Dropped from the Antarctic likelihood to avoid double-weighting the same mass-balance information already entering through other terms.

**Forcing.** FaIR 2.2.4 (fair-calibrate 1.6.0), driven by CMIP7 historical emissions 1750–2023 spliced at 2023.5 to MESSAGE-GLOBIOM SSP2-4.5 and harmonized per species. The calibration's fit window runs to 2026, so its last three years are driven by the scenario rather than by the historical emissions inventory — a difference bounded at about 0.002 W/m².

**Sampler.** Over-dispersed chain starts.

## Ladrillo Calibration Approach Updates

58 parameters are sampled: 17 Antarctic, 9 Greenland, 19 glacier, 13 remaining (thermal expansion, two discrepancy bases, and four AR(1) noise pairs). Four Antarctic changes distinguish Ladrillo's calibration from BRICK 2.0's — the three described below, plus an SMB likelihood term anchoring the Antarctic flux scale to Rignot 2019. The Antarctic changes have not been tested individually, so the AIS changes cannot be formally attributed by parameter.

**The seven DAIS geometry parameters.** The seven parameters (`ais_mu`, `ais_bedheight0`, `ais_slope`, `ais_iceflow0`, `ais_precip0_LOG`, `ais_runoff_Ton`, `ais_c`) are freed under a joint paleo prior. Ladrillo's pre-1990 Antarctic hindcast is far closer to the record than BRICK 2.0's — 1920–1949 bias −0.01 cm against −1.93 cm, and 1950–1992 +0.003 cm against −0.71 cm. BRICK 2.0 also samples its DAIS geometry; a key difference is the constraint, since its Antarctic likelihood is IMBIE 1992–2017 while Ladrillo fits an Antarctic series from 1900.

**The runoff line is sampled in its identified direction.** `h0` and `c` enter only as `hR = h0 + c·T_ant` with a correlation ridge. Ladrillo samples `T_on = −h0/c`, the runoff onset temperature, which is what the data constrain.

**Antarctic amplification is a key parameter.** Stock DAIS hard-codes 1.196. Ladrillo samples it under N(1.09, 0.180), the measured CMIP6 between-model spread. The parameter is not strongly constrained by observation and its leverage is strongly scenario-dependent: across the posterior draws, a one-sigma change moves Antarctic sea level at 2300 by about 58 cm on SSP2-4.5 (roughly 23% of that scenario's total) but only about 24 cm on SSP5-8.5 (under 5%), because by SSP5-8.5 the Antarctic response is already past the thresholds where amplification matters.

**Criterion matching.** L24 is accepted under the deliverable criterion: 39 parameters pass. While 19 parameter marginals fail R̂ < 1.05, these primarily involve the Antarctic-geometry ridge and compensate for each other. Projected sea level converges (R̂ = 1.008 at 2100, 1.011 at 2150; with 1050 statistically independent draws in the final sample).

## Ladrillo Observational Comparison

![Hindcast: Ladrillo L24 vs BRICK 2.0 vs observations](../figures/hindcast_components_L24.png)

**FIG 1.** Component hindcasts against the observations, 1900–2026, in cm relative to a 1995–2005 baseline. Ladrillo L24 (solid, with its 5–95% band) and BRICK 2.0 (dashed) are both run starting in 1850, plotted from 1900, and driven by the same ssp245harm forcing. The Greenland panel also shows MAGICC-SLR (v7.5.3 + Nauels 2025, dotted, with its 5–95% band) from 1991, the first year its Greenland module is active; it runs on its own emissions-driven climate. The total panel also shows IGCC 2025-indicators GMSL, which is not a calibration target. On the thermal-expansion panel the hatched band above the observation is the most the ocean below 2000 m could add to a 0–2000 m observation (IGCC deep-ocean heat times the observed upper-ocean expansion coefficient; an upper bound). Land-water storage is observational — neither model predicts it, so panel (e) shows the observed series alone and both totals carry it.

**Table 2.** RMSE of the Ladrillo L24 median against the observations, divided by BRICK 2.0's, by component and window; below 1 means Ladrillo is closer. Components are scored against their own targets and the total against Dangendorf 2024, all in cm relative to a 1995–2005 baseline.

| component         | 1900–1919 | 1920–1949 | 1950–1992 | 1993–2026 | full      |
|-------------------|-----------|-----------|-----------|-----------|-----------|
| Antarctica        | **0.003** | **0.005** | **0.010** | **0.676** | **0.019** |
| Greenland         | **0.110** | **0.102** | **0.054** | **0.263** | **0.085** |
| Glaciers          | **0.431** | **0.371** | 1.061     | **0.408** | **0.419** |
| Thermal expansion | **0.703** | **0.723** | 1.107     | 1.519     | **0.820** |
| **Total**         | 4.138     | 1.369     | **0.519** | **0.892** | 1.172     |

Ladrillo is closer than BRICK 2.0 on every component in the two earliest windows yet further from the total there, and the reason is compensating error. Over 1900–1919 BRICK's Antarctic undershoot (−2.90 cm) and glacier overshoot (+3.28 cm) are opposite in sign and nearly equal, so its four component biases sum to +0.62 cm out of 7.57 cm of absolute error. Ladrillo's biases are small but almost all positive, summing to +1.95 cm out of 1.97 cm. The same pattern holds over 1920–1949. The observational budget's own non-closure is common to both arms and small in these windows (−0.31 and +0.17 cm), so it cannot account for the difference. The component rows are therefore the skill statement; the total row additionally reflects whether a model's errors cancel after calibration. Ladrillo uses the observed LWS time series directly, whereas native BRICK subtracts LWS prior to calibration, so its components represent sea level excluding LWS; the observed series is added to both totals to put them on the same basis as the LWS-inclusive observational total. Separately, BRICK 2.0 runs on its own published posterior against our extended targets, so part of its bias is target vintage.

Ladrillo is closer to the observations than BRICK 2.0 on every ice component in every window except glaciers over 1950–1992, and the gains are largest in the early eras. Cumulative total sea level rise, comparing the 1900–1904 mean with the 2020–2024 mean: observed +21.00 cm, Ladrillo +19.84, BRICK 2.0 +21.34 — Ladrillo undershoots by 1.2 cm, BRICK overshoots by 0.3. Over the shorter, more recent window — the mean over 2022-2024 relative to the 1995–2005 baseline — both models still run high, but only slightly: observed +7.81 cm, Ladrillo +8.16 (+0.36) and BRICK 2.0 +8.34 (+0.54), with IGCC's independent GMSL estimate between them at +8.21. On the 2006–2025 rate of total sea level, the metric the SLEIP intercomparison reports, Ladrillo gives 0.374 cm/yr and BRICK 2.0 0.389 against 0.392 for the observational target and 0.399 for IGCC (same linear fit, same window).

**For thermal expansion Ladrillo overshoots, and the cause is the ocean heat it is given.** In both Ladrillo and BRICK thermal expansion is exactly proportional to ocean heat, and the expansion coefficient is not the problem: Ladrillo's is within 3% of the value the observations themselves imply. On the FaIR driver both models overestimate the 1993–2026 thermal-expansion rate (Ladrillo 1.27×, BRICK 2.0 1.17×), because FaIR's ocean heat uptake over that period is 1.22–1.29× the observed 0–2000 m products the target is built from. That excess has two parts of similar size. FaIR's ocean heat is full-depth while the steric target is 0–2000 m, and IGCC's own accounting puts the ocean below 2000 m at 10% of the heat uptake, so a full-depth model is expected to run about 1.10× a 0–2000 m target; the hatched band on FIG 1 shows the most this could add to the observation (0.3 cm by 2024, against Ladrillo's 0.8 cm excess). The remaining 1.10× is FaIR's full-depth heat uptake exceeding IGCC's full-depth estimate — a climate-model question, not a sea-level one, which is why BRICK 2.0 misses by nearly the same amount. Driving Ladrillo with observed 0–2000 m ocean heat — the target's own scope — removes both parts and reproduces the steric record within 4% in every era.

## Ladrillo Projection Comparison

The van Vuuren markers are the primary comparison; the SSPs are a secondary set and the control, being the only scenarios with a prior result to check the pipeline against. All Ladrillo bands are the joint (posterior × FaIR-forcing) arm, width-comparable to MAGICC and FACTS; BRICK 2.0's joint band uses the same cubes, splice pivot and pair seed. Bars are 17–83% (thick) and 5–95% (thin). All four sources carry climate uncertainty — Ladrillo from 841 FaIR configs, MAGICC-SLR from its 600-member AR6 drawnset, FACTS from its own internal ensembles — so the widths are the same kind of object and are comparable; they are not the same ensemble, and both joint arms are prior propagations rather than refits, since each posterior was calibrated under fixed forcing. FACTS is reported relative to baseyear 2005, treated as comparable to the 1995–2014 mean, which is the standing convention for this comparison. In the trajectory figure the two arms share cubes, splice pivot, re-reference and pairing seed, so their widths are directly comparable, but Ladrillo is thinned to 8000 draws against BRICK 2.0's 1000.

On glaciers, Ladrillo and MAGICC-SLR share the Nauels 2017 transient, so differences between Ladrillo and MAGICC reflect differences in reservoir count, driver and posterior; BRICK 2.0 and FACTS are independent there. At Greenland all four formulations differ. For Antarctica and thermal expansion Ladrillo and BRICK 2.0 share a formulation — DAIS for the ice sheet, and expansion proportional to ocean heat — and differ in calibration, while FACTS (LARMIP, DeConto, Bamber, AR5 and emulated ice-sheet modules; a two-layer expansion model) and MAGICC-SLR are separate on both.

![van Vuuren markers by component, 2100](../figures/model_comparison_components_vv_L24_2100.png)

**FIG 2.** Ladrillo L24 compared against BRICK 2.0, FACTS and MAGICC-SLR across the seven van Vuuren markers at 2100, by component. FACTS is drawn per module; its four workflows differ only in the Antarctic module, so the Total panel shows them as one bracket spanning the workflow medians (thin line: the union of their 5–95%). At 2150 and 2300 (FIGs 3, 4 and 9) only FACTS's climate-driven modules are drawn.

![van Vuuren markers by component, 2150](../figures/model_comparison_components_vv_L24_2150.png)

**FIG 3.** The same comparison at 2150.

![van Vuuren markers by component, 2300](../figures/model_comparison_components_vv_L24_2300.png)

**FIG 4.** The same comparison at 2300.

![van Vuuren component trajectories](../figures/future_components_vv_L24_joint.png)

**FIG 5.** Component trajectories across the van Vuuren markers, joint band, Ladrillo relative to BRICK2.0.

![Glacier response on the declining markers](../figures/vv_gsic_ladrillo_2300.png)

**FIG 6.** Ladrillo glacier contribution to 2300 across the seven van Vuuren markers: GMST forcing (a), cumulative glacier melt (b), and the melt rate on the peak-and-decline pathways (c). Regrowth appears when temperature declines below the reservoir equilibrium.

![Scenario responsiveness by component](../figures/vv_responsiveness_L24.png)

**FIG 7.** Scenario responsiveness by component: the High-minus-Very-Low difference of medians at 2100, 2150 and 2300 for each model, FACTS per module (open triangles: structured expert judgement). Ladrillo, BRICK 2.0 and FACTS share the FaIR driver (High − Very Low GMST gap 1.7/3.1/5.5 K at the three horizons); MAGICC-SLR responds to its own climate (2.0/3.6/5.9 K).

FACTS is drawn in full at 2100, but past 2100 only the modules that respond to the climate are shown. Its Greenland module (FittedISMIP) is an emulator fitted to 2015–2100 ISMIP6 runs whose rate carries an explicit quadratic term in time; FACTS extrapolates it linearly after 2100, and letting it run on the temperature path instead sends High-to-Low Greenland from 47 to 112 cm at 2300 while the climate cools — the time term, not the temperature. The Bamber and DeConto modules select their projections from the temperature integrated over 2000–2099, the AR5 Antarctic dynamics term is a prescribed function of time, and LARMIP's response functions are 200 years long and zero beyond, so at 2300 it has forgotten every pre-2100 forcing year (its response at lag 200 is still at full strength). Modules whose components are not climate-driven at a horizon, and every workflow total (each carries FittedISMIP), are therefore dropped from that horizon: at 2150 FACTS is drawn for glaciers, thermal expansion, land-water storage and LARMIP Antarctica; at 2300 for glaciers, thermal expansion and land-water storage only. The same rule applies to the benchmark. One further feature of the comparison is worth highlighting. MAGICC-SLR's Greenland band for the Low-to-Negative scenario reaches 144 cm at 2300 (95th percentile) compared to 25 cm for the Low scenario, although the medians are 13 and 14 cm: for MAGICC's own climate the Low-to-Negative scenario cools below preindustrial by 2300, and MAGICC's Greenland surface-mass-balance parameterisation, fitted for warming, turns positive there — the members with the strongest cooling (−1.5 to −2 K) give the largest Greenland melt (up to +343 cm from surface mass balance alone).

### Secondary: the SSPs

![Component comparison at 2100](../figures/model_comparison_components_L24_2100.png)

**FIG 8.** The SSP comparison at 2100.

![Component comparison at 2300](../figures/model_comparison_components_L24_2300.png)

**FIG 9.** The SSP comparison at 2300. The FACTS AR5 glacier module is completely melted (31.6 cm SLE) under SSP5-8.5.

![Total sea level by SSP](../figures/ladrillo_L24_fig2_ssp_total.png)

**FIG 10.** Total sea level by SSP, Ladrillo L24 joint band. Totals at 2300: 72.6 cm (SSP1-2.6), 249.2 cm (SSP2-4.5), 516.7 cm (SSP5-8.5).

### Ladrillo compared to MAGICC on MAGICC's own climate

Comparing two sea-level models on different climate drivers confounds the module with the forcing. Ladrillo and BRICK 2.0 were therefore re-run on MAGICC's climate to test which differences were due to sea level module versus climate module.

![Ladrillo and BRICK 2.0 on the FaIR driver and on MAGICC&#39;s climate, vs MAGICC-SLR](../figures/vv_climate_swap_L24_2300.png)

**FIG 11.** Ladrillo L24 and BRICK 2.0 at 2300 on the seven van Vuuren markers, each drawn twice — on the shared FaIR driver (filled) and on MAGICC's own 600-member climate (open), with the connector showing the swap — against MAGICC-SLR. Same posterior, tap and draws on both climates; FACTS has no MAGICC-climate arm and is not drawn.

### Physical intuition — how Ladrillo behaves by scenario class

**High scenarios.** At the High marker the three models agree at 2100 (Ladrillo 72 cm, BRICK 2.0 82, MAGICC-SLR 62). By 2300 Ladrillo and BRICK 2.0 sit together (439 and 414 cm, median) well below MAGICC-SLR (570 cm), and the gap is Antarctica: 255 and 248 cm against MAGICC's 382. Driving both on MAGICC's own climate moves their totals by only 15–20 cm (to 425 and 393; FIG 11), so the difference is the ice-sheet modules, not the climate. Ladrillo's 2300 Antarctic spread is dominated by the prior for `antarctic_lambda`, the DAIS fast-dynamics rate; BRICK 2.0 samples the same parameter from the same fast-dynamics ensemble (mean 0.0104, sd 0.0036 in both), which is why the two Antarctic spreads are alike (5–95% widths of 329 and 405 cm at SSP5-8.5 in 2300).

**Low scenarios.** Ladrillo sits at the low end of the comparison set on level — at vvVL its 2300 total median is 58 cm, above only MAGICC-SLR's 46 cm and below BRICK 2.0's 81. On spread it is narrower than BRICK 2.0 on every component and narrower than the FACTS glacier and thermal-expansion modules (the only FACTS modules drawn at 2300); MAGICC-SLR is the narrow outlier throughout (2300 total 5–95% width 67 cm against Ladrillo's 163 and BRICK 2.0's 182).

**Peak-and-decline scenarios.** The glacier change is evident here because it allows regrowth, though on Ladrillo's own FaIR climate that regrowth is very small: measured from each marker's peak to 2300, it reaches only 0.18 cm at vvLN and 0.13 cm at vvML, and is essentially nil on the other markers. The capacity is larger than the realised amount — driven instead by MAGICC's colder climate, the same module regrows 2.2 cm at vvLN — so what limits regrowth here is how far the scenario cools, not the module's willingness to regrow.

**MAGICC regrows substantially more than Ladrillo.** About ¾ of the regrowth difference is model structure and ¼ the climate module. Measured on realised regrowth (peak-to-2300) at vvLN, the scenario where regrowth is largest: MAGICC regrows 8.59 cm against Ladrillo's 0.18 cm, and driving Ladrillo's module with MAGICC's own climate decreases the gap by 2.02 cm. When driving the two models with MAGICC’s own temperature, Ladrillo’s committed equilibrium regrowth is also somewhat less than MAGICC’s, but MAGICC reaches its regrowth limits in the two coldest van Vuuren scenarios. So while the gap with MAGICC is mainly a rate effect (at 1.5 K the SLOWP and R19 regions have median response times of ~270 yr and ~470 yr, the latter very poorly constrained at 80–3200 yr across the posterior; all three blocks respond about three times faster at 3 K) this rate effect is compounded by an equilibrium effect.
