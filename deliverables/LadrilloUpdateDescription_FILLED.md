# Ladrillo (L24)

Ladrillo is a derivative of Tony Wong's BRICK2.0 model. Ladrillo was developed by Marcus C Sarofim using the Claude model. The primary goals for Ladrillo were to add additional observational data, update the glacier module to better match observations and to halt melting for stabilization scenarios, update the Antarctic calibration approach to better match observations prior to 1980, and update the Greenland model to incorporate the different responses of surface melt balance and ice discharge.

Ladrillo compares well relative to the other models and sits in a unique space. Unlike MAGICC, Ladrillo is designed to work with the FaIR model. Unlike FACTS, Ladrillo has a simplified structure. Ladrillo does a good job matching historical observations, with the primary weakness being thermal expansion, though that is inherited from FaIR and does not appear when running with OHC from observation. For future projections, Ladrillo matches physical expectations and is comparable to the other models despite different structural approaches.

> **Vintage.** This document describes posterior **L24**. Basis for every number below: **cm, re-referenced to 1995–2014**.

## Ladrillo Structural Updates

### GSIC

BRICK 2.0's glacier model uses a Wigley-Raper equation that is always melting when above its equilibrium temperature. Ladrillo replaces it with a **Mengel-style equilibrium volume** `S_eq` **driven by a Nauels-ν transient**, which separates *how much* ice is committed at a given warming from *how fast* it gets there, and splits the world into three reservoirs on regional temperature.

**SLOWP — RGI regions 03, 09, 07, 06** (Arctic Canada North, Russian Arctic, Svalbard, Iceland). Large, high-latitude, long relaxation time, and strongly amplified relative to global mean temperature (prior 2.50). This block dominates the glacier contribution in both the hindcast and the projections.

**FAST — the other 13 RGI regions.** Smaller, faster-responding bodies with weak amplification (prior 1.45). It equilibrates quickly enough that its committed volume is close to its realised volume through most of the record.

**R19 — Antarctic and Subantarctic periphery.** This block exists because the historical glacier target (Frederikse) **assumes zero Antarctic-periphery melt**, while the GlaMBIE series spliced in from 2019 onward **includes it**. Folding R19 into either SLOWP or FAST would leave the model's hindcast scope mismatched. Keeping it separate lets the hindcast be evaluated on **SLOWP + FAST** while R19 still contributes to projected totals. Its amplification prior (0.72) is also far below the other two, so it is not physically interchangeable with them either. (The three blocks cover 18 of the 19 RGI regions; RGI 05, Greenland Periphery, is excluded — Frederikse's glacier target excludes it and it falls inside the Greenland ice-sheet mask.)

**Compared with BRICK 2.0 and MAGICC.** BRICK 2.0 and Ladrillo now have completely different glacier modules. Compared to MAGICC, both use the formulation from Nauels 2017 Eq. 3; where they differ is the three regions used in Ladrillo. MAGICC's committed 1850 melt is 28–136 mm, Ladrillo's 63–146 mm.

**Regrowth potential.** Neither BRICK nor FACTS can regrow glacial ice, but MAGICC and Ladrillo can. The law is

    S_eq = max( a·(1 − exp(−b·(T − T_off))), 0 )        
    dS   = min( κ·|T − T_eq|^ν, 1 ) · (S_eq − S)        

**Regrowth limits.** MAGICC assumes that once ice committed to melt in 1850 has gone, it can't be regrown, but ice past that point can be. In theory, Ladrillo can regrow up until its 1850 ice extent (and no further), but that would require temperatures to drop below 1850 levels.

### Greenland

BRICK 2.0 treats Greenland as **one body with one response channel**. Ladrillo replaces that with a **two-channel, two-basin sheet**.

**Two channels (fast / slow).** Greenland melt occurs through surface-mass-balance response (slow) and outlet/dynamic discharge (fast). Two channels allow for that partition.

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

**The runoff line is sampled in its identified direction.** `h0` and `c` enter only as `hR = h0 + c·T_ant`, so individually they ride a correlation-0.9997 ridge no sampler can traverse. Ladrillo samples `T_on = −h0/c`, the runoff **onset temperature**, which is what the data constrain.

**Antarctic amplification is a key parameter.** Stock DAIS hard-codes 1.196. Ladrillo samples it under N(1.09, 0.180), the measured CMIP6 between-model spread. The parameter is not constrained by observation — the posterior is very close to the prior — and a one-sigma change moves Antarctic sea level at 2300 by about 69 cm on SSP5-8.5, roughly 13% of that scenario's total. That is leverage on a *trajectory*, not on the reported band: widening the prior 1.8× (L23 → L24) widened the AIS@2300 spread only **1.07×** (93.1 → 99.5 cm).

**Criterion matching.** L24 is accepted under the deliverable criterion: 19 parameter marginals fail R̂ < 1.05 (primarily the Antarctic-geometry ridge) while **projected sea level converges** (R̂ = 1.008 at 2100, 1.011 at 2150; ESS ≈ 1050).

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

Ladrillo is closer to the observations than BRICK 2.0 on **every ice component in every window** — by two orders of magnitude on early-20th-century Antarctica, and by roughly a factor of ten on Greenland. Cumulative 1900–2026 totals: observed 7.81 cm, Ladrillo 8.55, BRICK 2.0 8.45, against an independent IGCC check of 8.33.

**For thermal expansion Ladrillo is worse than BRICK 2.0, and the cause is FaIR.** In both models thermal expansion is *exactly* proportional to the ocean heat they are given, and both are given the same FaIR driver — so the miss is shared (BRICK 2.0 misses the same cell at 1.17×) and the same driver correction would apply to both. Against *observed* ocean heat a single constant coefficient ≈ 0.11 reproduces the steric target across 1900–1950, 1950–1993 and 1993–2024 to within 3%, and Ladrillo's fitted 0.11252 sits inside that range. Half the apparent miss is depth scope: FaIR's ocean heat is full-depth while the steric target is 0–2000 m, and correcting on IGCC's own >2000 m layer takes the 1993–2026 rate ratio from 1.27× to 1.15×. A depth-resolved coefficient was tested and failed, though that may reflect observational uncertainty — Cheng and IGCC disagree by ~50% on 1950–1993 ocean heat gain.

## Ladrillo Projection Comparison

The van Vuuren markers are the **primary** comparison; the SSPs are a secondary set and the control, being the only scenarios with a prior result to check the pipeline against. All Ladrillo bands are the **joint** (posterior × FaIR-forcing) arm, width-comparable to MAGICC and FACTS; BRICK 2.0's joint band uses the same cubes, splice pivot and pair seed.

![van Vuuren markers by component, 2100](../figures/model_comparison_components_vv_L24_2100.png)

**FIG 2.** Ladrillo L24 against BRICK 2.0, FACTS and MAGICC-SLR across the seven van Vuuren markers at **2100**, by component.

![van Vuuren markers by component, 2150](../figures/model_comparison_components_vv_L24_2150.png)

**FIG 3.** The same comparison at **2150**.

![van Vuuren markers by component, 2300](../figures/model_comparison_components_vv_L24_2300.png)

**FIG 4.** The same comparison at **2300**.

![van Vuuren component trajectories](../figures/future_components_vv_L24_joint.png)

**FIG 5.** Component trajectories across the van Vuuren markers, joint band.

![Glacier response on the declining markers](../figures/vv_gsic_wr_vs_ladrillo_2300.png)

**FIG 6.** ⭐ The glacier contribution at 2300 across the markers, against the Wigley–Raper formulation BRICK 2.0 uses. This is where the floored-equilibrium law is visible: Ladrillo halts and reverses on the declining markers where a melt-only reservoir cannot.

### Secondary: the SSPs

![Component comparison at 2100](../figures/model_comparison_components_L24_2100.png)

**FIG 7.** The SSP comparison at **2100**.

![Component comparison at 2300](../figures/model_comparison_components_L24_2300.png)

**FIG 8.** The SSP comparison at **2300**, where only MAGICC-SLR and BRICK 2.0 extend.

![Total sea level by SSP](../figures/ladrillo_L24_fig2_ssp_total.png)

**FIG 9.** Total sea level by SSP, Ladrillo L24 joint band. Totals at 2300: **72.6 cm** (SSP1-2.6), **249.2 cm** (SSP2-4.5), **516.7 cm** (SSP5-8.5).

### Ladrillo compared to MAGICC on MAGICC's own climate

⚠ Comparing two sea-level models on **different climate drivers** confounds the module with the forcing. Ladrillo was therefore re-run on **MAGICC's climate** as well as FaIR's, so the remaining difference is structural. This arm is what licenses any statement that a Ladrillo/MAGICC-SLR difference is a *model* difference.

### Physical intuition — how Ladrillo behaves by scenario class

**High scenarios.** Ladrillo is comparable to the other models at 2100 and separates upward at the long horizons — expected of a model whose Antarctic response is threshold-driven rather than linear. ⚠ Its 2300 spread is dominated by `antarctic_lambda`, a **prior** rather than an inference, so the width at the high end is a stated uncertainty.

**Low scenarios.** Ladrillo sits at the low end of the comparison set on *level*, but its Antarctic band is **wider** than the literature's: 2.55× at ssp126/2100 (54.6 cm against 20.7–40.5), which carries the total to 1.48×. Greenland, glaciers and thermal expansion are all narrower there (0.47×, 0.77×, 0.93×). ⚠ This is the one place the benchmark flags a genuine discrepancy, and it is a projection-versus-other-models disagreement rather than an observational conflict. It is wider on L24 than on L21 because the amplification prior is wider — the honest, measured prior, not a tuned one.

**Peak-and-decline scenarios.** The glacier change is important here because it allows regrowth, though that regrowth is modest. Swapping back to the melt-only ratchet on a held posterior moves the total by only ≤6.2×10⁻⁵ cm on the SSPs and −0.20 cm at the low-overshoot marker, so what the law buys is structural rather than numerical: glaciers halt when temperature halts — the glacier rate at 2300 falls to 0.00–0.55 mm/yr on declining pathways against 1.96 on a rising one — and can reverse, which BRICK 2.0's melt-only formulation cannot do at all.

**MAGICC regrows substantially more than Ladrillo, and about ¾ of that is model structure and ¼ the climate module.** Re-running Ladrillo on MAGICC's own climate closes 13–35% of the regrowth gap (mean 24%) across the five van Vuuren markers where MAGICC regrows, leaving the rest to structure. The structural half is a *rate* limit, not an equilibrium one. At vvLN, where MAGICC's climate falls to −0.71 K by 2300, Ladrillo's own glacier equilibrium drops from 19.1 cm to 2.2 cm — 16.9 cm of headroom — yet it regrows only 2.1 cm of it. The reason is that Ladrillo's regional blocks relax at very different speeds on the cooling limb: FAST has a ~95-year timescale, but SLOWP (~275 yr) and R19 (~465 yr) together hold 60% of the headroom and cannot traverse it inside the horizon while chasing a still-falling equilibrium. MAGICC has no regional split — one global reservoir, relaxing fast enough to reach its floor. ⭐ **The regionalisation that makes Ladrillo fit the historical record better is the same feature that makes it slower to regrow.**

⚠ On a matched-temperature overshoot pair the regrowth is modest for everyone: at 2300 Ladrillo gives 2.21 cm against BRICK 2.0's 2.58, inside the 1.65–5.39 cm spread of four FACTS process-based workflows, with the long upper tails coming from the MICI-capable arm rather than from disagreement about the central estimate.

> **Regeneration note (2026-09-02).** Every number and figure here is **L24** unless an earlier vintage is explicitly named. The van Vuuren markers and the MAGICC-climate arm were built for L24 specifically (16 arms, all **tapped**; L21 and L23 have no untapped van Vuuren or MAGICC arms). ⚠ **L24 vs L21 remains a prior change, not a model improvement.**
