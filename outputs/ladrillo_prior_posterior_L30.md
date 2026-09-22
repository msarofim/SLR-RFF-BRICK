**Table A1.** Prior distributions and posterior median (5–95%) of the 52 sampled Ladrillo parameters (10,000 thinned draws of the four chains). N(µ, σ) on [lo, hi] is a normal density restricted to the bounds; 'flat' is bounds only. Glacier-block temperatures are in the block's regional frame (K relative to 1850–1900). ᵃ κ's prior centre κ̂(amp) is a log-linear function of the block's sampled amplification (τ₅₀ anchored to GlacierMIP3); ᵇ the seven DAIS geometry parameters carry a joint normal prior with the correlation of the DAIS paleo ensemble — the marginal is shown. The Greenland channel ordering (SMB faster than discharge) is a hard constraint on top of these marginals. Antarctic temperatures on the DAIS scale; ais_runoff_Ton replaces h₀ (h₀ = −T_on·c).

| Parameter | Description | Units | Prior | Median | 5% | 95% |
|---|---|---|---|---|---|---|
| **Glacier reservoirs (three blocks; SLOWG = SLOWP and FASTG = FAST in the code)** | | | | | | |
| `gic_a_R19` | Committed-loss scale a, RGI 19 | m SLE | N(0.069, 0.018) on [0.01, 0.141] | 0.0673 | 0.0389 | 0.0957 |
| `gic_b_R19` | Equilibrium temperature sensitivity b, RGI 19 | K⁻¹ (glacier frame) | flat [0.05, 3] | 0.72 | 0.19 | 2.46 |
| `gic_T_off_R19` | Equilibrium temperature offset T_off, RGI 19 | K rel. 1850–1900, glacier frame | flat [−4, 1] | −0.16 | −3.24 | 0.7 |
| `gic_log10_kappa_R19` | log₁₀ of the response-rate constant κ, RGI 19 | log₁₀(yr⁻¹ K⁻ν) | N(κ̂(amp), 0.114) on [−3.91, −1.66]ᵃ | −2.78 | −3 | −2.57 |
| `gic_a_SLOWG` | Committed-loss scale a, SLOWG | m SLE | N(0.146, 0.0328) on [0.0333, 0.277] | 0.132 | 0.092 | 0.177 |
| `gic_b_SLOWG` | Equilibrium temperature sensitivity b, SLOWG | K⁻¹ (glacier frame) | flat [0.05, 3] | 0.171 | 0.114 | 0.287 |
| `gic_T_off_SLOWG` | Equilibrium temperature offset T_off, SLOWG | K rel. 1850–1900, glacier frame | flat [−4, 1] | −2.74 | −3.87 | −0.98 |
| `gic_log10_kappa_SLOWG` | log₁₀ of the response-rate constant κ, SLOWG | log₁₀(yr⁻¹ K⁻ν) | N(κ̂(amp), 0.114) on [−4.75, −2.17]ᵃ | −3.49 | −3.7 | −3.26 |
| `gic_a_FASTG` | Committed-loss scale a, FASTG | m SLE | N(0.14, 0.0242) on [0.0809, 0.237] | 0.151 | 0.12 | 0.184 |
| `gic_b_FASTG` | Equilibrium temperature sensitivity b, FASTG | K⁻¹ (glacier frame) | flat [0.05, 3] | 0.336 | 0.252 | 0.465 |
| `gic_T_off_FASTG` | Equilibrium temperature offset T_off, FASTG | K rel. 1850–1900, glacier frame | flat [−4, 1] | −1.51 | −2.18 | −0.9 |
| `gic_log10_kappa_FASTG` | log₁₀ of the response-rate constant κ, FASTG | log₁₀(yr⁻¹ K⁻ν) | N(κ̂(amp), 0.114) on [−3.77, −1.52]ᵃ | −2.61 | −2.76 | −2.45 |
| **Glacier regional temperature amplification** | | | | | | |
| `gic_amp_R19` | Regional/global warming ratio, RGI 19 | – | N(0.72, 0.15) on [0.58, 0.88] | 0.73 | 0.599 | 0.86 |
| `gic_amp_SLOWG` | Regional/global warming ratio, SLOWG | – | N(2.5, 0.45) on [1.8, 3.5] | 2.64 | 2.07 | 3.19 |
| `gic_amp_FASTG` | Regional/global warming ratio, FASTG | – | N(1.45, 0.15) on [1.33, 1.82] | 1.46 | 1.35 | 1.65 |
| **Glacier scope and ledger terms (hindcast-target constructs)** | | | | | | |
| `gic_u_unch` | Uncharted-ice content of the Frederikse glacier target | mm SLE | flat [14.5, 41.8] | 33.2 | 20.8 | 40.9 |
| **Greenland ice sheet (two channels, two basins)** | | | | | | |
| `gis_c1` | Committed-loss sensitivity to regional temperature | m SLE K⁻¹ | N(0.0328, 0.05) on [0, 4] | 0.0464 | 0.0189 | 0.0834 |
| `gis_c0` | Committed loss at zero regional anomaly | m SLE | N(0.0404, 0.1) on [0, 4] | 0.111 | 0.069 | 0.179 |
| `gis_f` | Surface-mass-balance share of the committed loss | – | N(0.783, 0.3) on [0.02, 0.98] | 0.582 | 0.359 | 0.745 |
| `gis_alpha_f` | Fast (SMB) channel rate, temperature-dependent part | yr⁻¹ K⁻¹ | N(0.00285, 0.02) on [0, 0.5] | 0.00196 | 0.00057 | 0.00468 |
| `gis_beta_f` | Fast (SMB) channel rate, constant part | yr⁻¹ | N(0.00737, 0.05) on [0.000001, 0.5] | 0.0048 | 0.0017 | 0.0102 |
| `gis_slow_ell` | Slow (discharge) channel: log rate at the reference temperature | ln(yr⁻¹) | N(−4.21, 1) on [−8.21, −0.207] | −5.68 | −6.5 | −4.98 |
| `gis_slow_w` | Slow (discharge) channel: temperature-dependent fraction of the rate | – | flat [0, 1] | 0.442 | 0.05 | 0.926 |
| `gis_s_high` | log₁₀ rate scale of the high basin (NO+NE) relative to the active basin | log₁₀(–) | N(0, 0.5) on [−2, 2] | −0.557 | −0.776 | −0.361 |
| `gis_amp` | Southern-Greenland/global warming ratio | – | N(1.92, 0.318) on [1.51, 2.28] | 1.91 | 1.58 | 2.23 |
| **Antarctic ice sheet (DAIS) and Antarctic ocean** | | | | | | |
| `ais_gmst_amp` | Antarctic/global warming ratio | – | N(1.09, 0.18) on [0.55, 1.63] | 1.03 | 0.74 | 1.32 |
| `ais_ocean_temperature₀` | Initial high-latitude ocean subsurface temperature T_oc,0 | °C | N(0.72, 0.5) on [0.5, 2] | 1 | 0.56 | 1.65 |
| `antarctic_alpha` | Partition of ocean subsurface temperature into ice flux, α_DAIS | – | N(0.296, 0.23) on [0.00001, 1] | 0.288 | 0.06 | 0.633 |
| `antarctic_nu` | Runoff-decrease-with-height to precipitation constant ν | m⁻¹ᐟ² yr⁻¹ᐟ² | N(0.00877, 0.00344) on [0.003, 0.015] | 0.0092 | 0.0046 | 0.0136 |
| `anto_alpha` | Antarctic ocean temperature sensitivity a_ANTO | °C °C⁻¹ | N(0.362, 0.261) on [0.000001, 1] | 0.319 | 0.077 | 0.665 |
| `anto_beta` | Antarctic ocean temperature offset b_ANTO | °C | N(0.976, 0.578) on [0.000003, 2] | 0.94 | 0.17 | 1.76 |
| `antarctic_kappa` | Exponential dependence of precipitation on Antarctic temperature κ_DAIS | °C⁻¹ | N(0.0588, 0.0166) on [0.025, 0.085] | 0.0548 | 0.0326 | 0.0771 |
| `ais_mu` | Profile parameter µ | m¹ᐟ² | paleo N(10.8, 1.81) on [7.05, 13.6]ᵇ | 10.9 | 8.4 | 13.1 |
| `ais_bedheight0` | Bed height at the continent centre b₀ | m | paleo N(780, 23) on [740, 820]ᵇ | 779 | 748 | 811 |
| `ais_slope` | Bed slope | – | paleo N(0.000628, 0.000062) on [0.00045, 0.00075]ᵇ | 0.000625 | 0.000578 | 0.000678 |
| `ais_iceflow0` | Ice-flow constant f₀ | m yr⁻¹ | paleo N(1.24, 0.341) on [0.6, 1.8]ᵇ | 1.08 | 0.72 | 1.56 |
| `ais_precip_u` | u = ln P₀ + κ_DAIS·T̄ (T̄ = −17.99 °C, DAIS scale); ln P₀ is derived | ln(m yr⁻¹) | paleo N(−1.98, 0.743) on [−1000000000, 1000000000]ᵇ | −1.67 | −1.78 | −1.5 |
| `ais_runoff_Ton` | Runoff onset temperature T_on = −h₀/c (sampled in place of h₀) | °C (DAIS scale) | paleo N(−15.6, 5.54) on [−43.3, −5.22]ᵇ | −17.8 | −23 | −9.6 |
| `ais_c` | Runoff-line slope c | m °C⁻¹ | paleo N(97.2, 26.6) on [47.5, 142]ᵇ | 84 | 54 | 125 |
| `ais_ramp_gon` | Onset of the additional discharge response, in global warming | °C | flat [0.3, 1.2] | 0.81 | 0.32 | 1.18 |
| `ais_ramp_log10s` | log10 slope of the additional discharge response, per °C of Antarctic excess | log10(m SLE yr⁻¹ °C⁻¹) | flat [−4.3, −2.7] | −4.02 | −4.27 | −3.51 |
| **Thermal expansion** | | | | | | |
| `thermal_alpha` | Thermal expansion coefficient α | kg m⁻³ °C⁻¹ | flat [0.05, 0.3] | 0.167 | 0.149 | 0.186 |
| **Model-discrepancy coefficients** | | | | | | |
| `d2_steric_1` | Thermal-expansion discrepancy, basis coefficient 1 | cm (RMS) | N(0, 0.5) on [−2.5, 2.5] | 0.211 | 0.001 | 0.396 |
| `d2_steric_2` | Thermal-expansion discrepancy, basis coefficient 2 | cm (RMS) | N(0, 0.5) on [−2.5, 2.5] | 0.071 | −0.051 | 0.199 |
| **Observation-error model (AR(1) per target series)** | | | | | | |
| `sd_ais` | AR(1) innovation sd, Antarctica | cm | half-normal N⁺(0, 5) | 0.0142 | 0.0115 | 0.0173 |
| `rho_ais` | AR(1) autocorrelation, Antarctica | – | flat [0, 0.99] | 0.967 | 0.911 | 0.988 |
| `sd_gsic` | AR(1) innovation sd, glaciers | cm | half-normal N⁺(0, 5) | 0.0167 | 0.0121 | 0.0221 |
| `rho_gsic` | AR(1) autocorrelation, glaciers | – | flat [0, 0.99] | 0.598 | 0.156 | 0.942 |
| `sd_gis` | AR(1) innovation sd, Greenland | cm | half-normal N⁺(0, 5) | 0.0255 | 0.022 | 0.0297 |
| `rho_gis` | AR(1) autocorrelation, Greenland | – | flat [0, 0.99] | 0.959 | 0.839 | 0.988 |
| `sd_steric` | AR(1) innovation sd, thermal expansion | cm | half-normal N⁺(0, 5) | 0.101 | 0.089 | 0.114 |
| `rho_steric` | AR(1) autocorrelation, thermal expansion | – | flat [0, 0.99] | 0.94 | 0.857 | 0.983 |

<!-- ladrillo_prior_posterior_table.py | tag L30 | priors from calibrate_mcmc_ext.jl --dump-priors (tag L30) | posterior parameters_subsample_brick_mengel_L30.csv n=10000 | quantiles 5/50/95 over all draws | commit d9b24a4 | 2026-09-22 11:39 -->
