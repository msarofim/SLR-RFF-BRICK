# Ladrillo (L24)

Ladrillo is a derivative of Tony Wong's BRICK2.0 model. Ladrillo was developed by Marcus C Sarofim using the Claude model. The primary goals for Ladrillo were to add additional observational data, update the glacier module to better match observations and to halt melting for stabilization scenarios, update the Antarctic calibration approach to better match observations prior to 1980, and update the Greenland model to incorporate the different responses of surface melt balance and ice discharge.

Ladrillo compares well relative to the other models and sits in a unique space. Unlike MAGICC, Ladrillo is designed to work with the FaIR model. Unlike FACTS, Ladrillo has a simplified structure. Ladrillo does a good job matching historical observations, with the primary weakness being thermal expansion, though that is inherited from FaIR and does not appear when running with OHC from observation. For future projections, Ladrillo matches physical expectations and is comparable to the other models despite different structural approaches.

> **Vintage.** This document describes posterior **L24**. Basis for every number below: **cm, re-referenced to 1995–2014**.

## Ladrillo Structural Updates

### GSIC

BRICK 2.0's glacier model uses a Wigley-Raper equation that is always melting when above its equilibrium temperature. Ladrillo replaces it with a **Mengel-style equilibrium volume** `S_eq` **driven by a Nauels-ν transient**, which separates *how much* ice is committed at a given warming from *how fast* it gets there, and splits the world into three reservoirs on regional temperature.

**SLOWP — RGI regions 03, 09, 07, 06** (Arctic Canada North, Russian Arctic, Svalbard, Iceland). Large, high-latitude, long relaxation time, and strongly amplified relative to global mean temperature (prior 2.50). This block dominates the glacier contribution in both the hindcast and the projections.

**FAST — 13 other RGI regions.** Smaller, faster-responding bodies with weak amplification (prior 1.45). It equilibrates quickly enough that its committed volume is close to its realised volume through most of the record.

**R19 — Antarctic and Subantarctic periphery.** This block exists because the historical glacier target (Frederikse) assumes zero Antarctic-periphery melt, while the GlaMBIE series spliced in from 2019 onward includes it. Folding R19 into either SLOWP or FAST would leave the model's hindcast scope mismatched. Keeping it separate lets the hindcast be evaluated on SLOWP + FAST while R19 still contributes to projected totals. Its amplification prior (0.72) is also far below the other two, so it is not physically interchangeable with them either. (The three blocks cover 18 of the 19 RGI regions; RGI 05, Greenland Periphery, is excluded — Frederikse's glacier target excludes it and it falls inside the Greenland ice-sheet mask.)

**Compared with BRICK 2.0 and MAGICC.** BRICK 2.0 and Ladrillo now have completely different glacier modules. MAGICC and Ladrillo both use the formulation from Nauels 2017 Eq. 3; where they differ is the three regions used in Ladrillo. MAGICC's committed 1850 melt is 28–136 mm, Ladrillo's 63–146 mm.

**Regrowth potential.** Neither BRICK nor FACTS can regrow glacial ice, but MAGICC and Ladrillo can. The law is

    S_eq = max( a·(1 − exp(−b·(T − T_off))), 0 )        
    dS   = min( κ·|T − T_eq|^ν, 1 ) · (S_eq − S)        

**Regrowth limits.** MAGICC assumes that once ice committed to melt in 1850 has gone, it can't be regrown, but ice lost past that point can be. In theory, Ladrillo can regrow up until its 1850 ice extent (though no further), but that would require temperatures to drop below 1850 levels.

### Greenland

BRICK 2.0 treats Greenland as **one body with one response channel**. Ladrillo replaces that with a **two-channel, two-basin sheet**.

**Two channels (fast / slow).** Greenland melt occurs through surface-mass-balance response (fast) and outlet/dynamic discharge (slow). Two channels allow for that partition. "Fast" names which physics the channel carries, not a short time constant — the surface-mass-balance channel drains a multi-millennial commitment, and at the optimum its response time is 86 years.

**Two basins.** The sheet is split into an **active** basin (SW+CW+CE+SE+NW) and a **high** basin (NO+NE), each carrying its own fast/slow channel pair, with sector shares scored against Mouginot.

**Amplification.** The ratio of Greenland warming to global warming is itself a function of temperature.

**High-basin volume tap.** A post-2100 commitment above a threshold: V = 5.64 m, τ = 800 yr, onset 4.69 K, two stages, whole-sheet. The tap does not fire until temperatures exceed the onset. It cannot be calibrated on observations, so the parameters were informed by ISMIP6 at 2100 and SICOPOLIS at 2300 and 3001. It is included in every projection here, contributing exactly zero at SSP1-2.6 and SSP2-4.5 and 41.8 cm to the SSP5-8.5 total at 2300.

**Compared with BRICK 2.0 and MAGICC.** Greenland is the component where the hindcast gain over BRICK 2.0 is largest. MAGICC similarly splits Greenland into SMB and SID and parameterises against SICOPOLIS, but with 17 parameters between the two, of which 9 vary and each of those takes only 4 distinct values.

## Ladrillo Calibration Data Updates

Additional or replaced observational inputs, relative to BRICK 2.0:

| data source | what it constrains |
|----|----|
| **Dangendorf 2024** GMSL | The total, replacing the previous GMSL reconstruction. |
| **GlaMBIE** glacier series (2019 onward) | The modern glacier rate, spliced onto Frederikse. It **includes** Antarctic-periphery melt where Frederikse excludes it, which is why R19 is a separate block. |
| **JPL GRACE / GRACE-FO mascons** | Land-water storage 2019–2026, which had been held flat; the closure σ is trend-extended over the same period. |
| **Mouginot** Greenland sector shares | The basin split, as a shares term rather than a level. |
| **Rignot 2019** Antarctic SMB, area-corrected ×0.888 | The absolute Antarctic flux scale. SMB minus discharge is well constrained at −145 ± 15 Gt/yr but each flux individually has high uncertainty (±505/±509), so Rignot anchors the pair. |
| **Glacier inventory** likelihood + a 19th-century flow constraint, `S(1900) − S(1850) ~ N(0.020, 0.009)` m SLE | The absolute inventory and the pre-observational flow, neither of which the 20th-century transient identifies on its own. |
| **CMIP6 regional amplification** (34–41 models) | Priors on the per-block glacier amplification and on Antarctic amplification. |
| **Paleo constraints** on DAIS geometry, in a standardised correlation form | The seven freed geometry parameters (below). |

**Deliberately removed: IMBIE**, dropped from the Antarctic likelihood to avoid double-weighting the same mass-balance information already entering through other terms.

**Forcing.** **FaIR 2.2.4 (fair-calibrate 1.6.0, CMIP7 history to 2023)**.

**Sampler.** Over-dispersed chain starts.

## Ladrillo Calibration Approach Updates

**58 parameters are sampled**: 17 Antarctic, 9 Greenland, 19 glacier, 13 remaining (thermal expansion, two discrepancy bases, and four AR(1) noise pairs). Three Antarctic changes carry the improvement.

**The seven DAIS geometry parameters** (`ais_mu`, `ais_bedheight0`, `ais_slope`, `ais_iceflow0`, `ais_precip0_LOG`, `ais_runoff_Ton`, `ais_c`) are freed under a joint paleo prior. This change fixed the pre-1990 Antarctic melt: with the geometry fixed at the prior medoid, BRICK 2.0 draws far more early-20th-century Antarctic mass loss than the record supports, while Ladrillo tracks the observations to within a hundredth of a centimetre.

**The runoff line is sampled in its identified direction.** `h0` and `c` enter only as `hR = h0 + c·T_ant` with a correlation ridge. Ladrillo samples `T_on = −h0/c`, the runoff onset temperature, which is what the data constrain.

**Antarctic amplification is a key parameter.** Stock DAIS hard-codes 1.196. Ladrillo samples it under N(1.09, 0.180), the measured CMIP6 between-model spread. The parameter is not constrained by observation — the posterior is very close to the prior — and its leverage is strongly scenario-dependent: across the posterior draws, a one-sigma change moves Antarctic sea level at 2300 by about 58 cm on SSP2-4.5 (roughly 23% of that scenario's total) but only about 24 cm on SSP5-8.5 (under 5%), because by SSP5-8.5 the Antarctic response is already past the thresholds that amplification would otherwise buy. These are regression slopes measured across the posterior draws, not one-at-a-time perturbations, so they carry the posterior's own parameter correlations.

**Criterion matching.** L24 is accepted under the deliverable criterion: 39 parameters pass. While 19 parameter marginals fail R̂ < 1.05, these primarily involve the Antarctic-geometry ridge and compensate for each other. Projected sea level converges (R̂ = 1.008 at 2100, 1.011 at 2150; with 1050 statistically independent draws in the final sample).

## Ladrillo Observational Comparison

![Hindcast: Ladrillo L24 vs BRICK 2.0 vs observations](../figures/hindcast_components_L24.png)

**FIG 1.** Component hindcasts, 1900–2026, against the calibration targets.

RMSE ratio against BRICK 2.0 — **below 1 means Ladrillo is closer to the observations**:

| component         | 1920–1949 | 1950–1992 | 1993–2026 | full      |
|-------------------|-----------|-----------|-----------|-----------|
| Antarctica        | **0.005** | **0.010** | 0.555     | **0.027** |
| Greenland         | **0.103** | **0.054** | 0.272     | **0.082** |
| Glaciers          | **0.361** | 1.027     | **0.355** | **0.372** |
| Thermal expansion | 1.150     | 1.137     | 1.462     | 1.236     |
| **Total**         | **0.411** | **0.277** | 1.128     | **0.373** |

*Thermal expansion in both models is driven by FaIR's full-depth ocean heat against a 0–2000 m target, so this row measures Ladrillo's fit relative to BRICK 2.0, not absolute accuracy — see the depth-scope discussion below.*

Ladrillo is closer to the observations than BRICK 2.0 on every ice component particularly in early eras. Cumulative total sea level rise, 1920–2024: observed +19.45 cm, Ladrillo +18.83, BRICK 2.0 +22.09 — Ladrillo undershoots by 0.6 cm, BRICK overshoots by 2.6. Over the shorter, more recent window — the level at 2024 relative to the 1995–2005 calibration baseline — both models run slightly high instead: observed +7.81 cm, Ladrillo +8.55 (+0.74), BRICK 2.0 +8.45 (+0.64), with IGCC's independent GMSL estimate at +8.33 cm in between.

**For thermal expansion Ladrillo overshoots, and the cause is FaIR.** In both Ladrillo and BRICK thermal expansion is *exactly* proportional to the ocean heat they are given. When given the FaIR driver, both models overestimate recent thermal expansion (BRICK 2.0 misses the 1993-2026 thermal expansion rate by 1.17× compared to Ladrillo's 1.27×). However, when using observed OHC Ladrillo reproduces steric changes within 4% at every era. Roughly half the apparent miss is depth scope: FaIR's ocean heat is full-depth while the steric target is 0–2000 m, and correcting on IGCC's own >2000 m layer narrows the 1993–2026 rate ratio from 1.27× to as little as 1.15× — an upper bound on the correction, not a point estimate, since deep water expands less per joule than the heat ratio implies, and the cell is still a FAIL even at that bound. A depth-resolved coefficient was tested and failed, though that may reflect observational uncertainty — Cheng and IGCC disagree by ~50% on 1950–1993 ocean heat gain.

## Ladrillo Projection Comparison

The van Vuuren markers are the **primary** comparison; the SSPs are a secondary set and the control, being the only scenarios with a prior result to check the pipeline against. All Ladrillo bands are the **joint** (posterior × FaIR-forcing) arm, width-comparable to MAGICC and FACTS; BRICK 2.0's joint band uses the same cubes, splice pivot and pair seed.

![van Vuuren markers by component, 2100](../figures/model_comparison_components_vv_L24_2100.png)

**FIG 2.** Ladrillo L24 compared against BRICK 2.0, FACTS and MAGICC-SLR across the seven van Vuuren markers at **2100**, by component.

![van Vuuren markers by component, 2150](../figures/model_comparison_components_vv_L24_2150.png)

**FIG 3.** The same comparison at **2150**.

![van Vuuren markers by component, 2300](../figures/model_comparison_components_vv_L24_2300.png)

**FIG 4.** The same comparison at **2300**.

![van Vuuren component trajectories](../figures/future_components_vv_L24_joint.png)

**FIG 5.** Component trajectories across the van Vuuren markers, joint band.

![Glacier response on the declining markers](../figures/vv_gsic_wr_vs_ladrillo_2300.png)

**FIG 6.** Glacier contribution over time, comparing Ladrillo to BRICK2.0. This is where glacier regrowth is visible in Ladrillo for overshoot scenarios, whereas the Wigley-Raper formulation continues melting.

### Secondary: the SSPs

![Component comparison at 2100](../figures/model_comparison_components_L24_2100.png)

**FIG 7.** The SSP comparison at **2100**.

![Component comparison at 2300](../figures/model_comparison_components_L24_2300.png)

**FIG 8.** The SSP comparison at **2300**, where only MAGICC-SLR and BRICK 2.0 extend.

![Total sea level by SSP](../figures/ladrillo_L24_fig2_ssp_total.png)

**FIG 9.** Total sea level by SSP, Ladrillo L24 joint band. Totals at 2300: **72.6 cm** (SSP1-2.6), **249.2 cm** (SSP2-4.5), **516.7 cm** (SSP5-8.5).

### Ladrillo compared to MAGICC on MAGICC's own climate

Comparing two sea-level models on different climate drivers confounds the module with the forcing. Ladrillo was therefore re-run on MAGICC's climate to test which differences were due to sea level module versus climate module.

### Physical intuition — how Ladrillo behaves by scenario class

**High scenarios.** Ladrillo is comparable to the other models at 2100. By 2300 it separates upward from BRICK 2.0 (due largely to Antarctic threshold behavior) but stays below MAGICC-SLR's steeper rise (439 cm vs. 570 cm, median). Its 2300 spread is dominated by the prior for `antarctic_lambda`.

**Low scenarios.** Ladrillo sits at the low end of the comparison set on level — at vvVL its 2300 total median is 58 cm, above only MAGICC-SLR's 46 cm and below BRICK 2.0's 81 and FACTS's 148. On spread it is narrower than both BRICK 2.0 and FACTS on every component; MAGICC-SLR is the narrow outlier throughout (2300 total 5–95% width 67 cm against Ladrillo's 163, BRICK 2.0's 182 and FACTS's 259), and it is only against MAGICC-SLR that Ladrillo's Antarctic and thermal-expansion bands are the wider ones.

**Peak-and-decline scenarios.** The glacier change is evident here because it allows regrowth, though on Ladrillo's own FaIR climate that regrowth is very small: measured from each marker's peak to 2300, it reaches only 0.18 cm at vvLN and 0.13 cm at vvML, and is essentially nil on the other markers. The capacity is larger than the realised amount — driven instead by MAGICC's colder climate, the same module regrows 2.2 cm at vvLN — so what limits regrowth here is how far the scenario cools, not the module's willingness to regrow.

**MAGICC regrows substantially more than Ladrillo, and about ¾ of that is model structure and ¼ the climate module.** Measured on realised regrowth (peak-to-2300) at vvLN, the marker where regrowth is largest: MAGICC regrows 8.59 cm against Ladrillo's 0.18 cm, and driving Ladrillo's unchanged module with MAGICC's own climate recovers 2.20 cm of that gap — leaving 76% to structure and 24% to the climate driver. Pooled across the five markers with a real gap the structure share is higher still, 87%. Comparing instead the two models’ equilibrium laws directly — both evaluated at MAGICC’s own temperature, so climate differences are removed — Ladrillo’s committed equilibrium regrowth is somewhat *less* than MAGICC’s on every marker where the comparison is possible (ratio 0.06–0.86 across three markers). At the two coldest markers no comparison can be made at all: MAGICC’s own tabulated equilibrium curve is undefined below the pre-industrial state, and both markers cool past that floor by 2300. So the gap to MAGICC is not purely a rate effect; the SLOWP and R19 regions’ long timescales (~275 yr, ~465 yr) compound a somewhat smaller equilibrium target, not offset it.
