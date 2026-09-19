**Table A1.** Prior distributions and posterior median (5–95%) of the 58 sampled Ladrillo parameters (10,000 thinned draws of the four chains). N(µ, σ) on [lo, hi] is a normal density restricted to the bounds; 'flat' is bounds only. Glacier-block temperatures are in the block's regional frame (K relative to 1850–1900). ᵃ κ's prior centre κ̂(amp) is a log-linear function of the block's sampled amplification (τ₅₀ anchored to GlacierMIP3); ᵇ the seven DAIS geometry parameters carry a joint normal prior with the correlation of the DAIS paleo ensemble — the marginal is shown. The Greenland channel ordering (SMB faster than discharge) is a hard constraint on top of these marginals. Antarctic temperatures on the DAIS scale; ais_runoff_Ton replaces h₀ (h₀ = −T_on·c).

| Parameter | Description | Units | Prior | Median | 5% | 95% |
|---|---|---|---|---|---|---|
| **Glacier reservoirs (three blocks; SLOWG = SLOWP and FASTG = FAST in the code)** | | | | | | |
| `gic_a_R19` | Committed-loss scale a, RGI 19 | m SLE | N(0.069, 0.018) on [0.01, 0.141] | 0.0677 | 0.0391 | 0.0966 |
| `gic_b_R19` | Equilibrium temperature sensitivity b, RGI 19 | K⁻¹ (glacier frame) | flat [0.05, 3] | 0.78 | 0.22 | 2.5 |
| `gic_T_off_R19` | Equilibrium temperature offset T_off, RGI 19 | K rel. 1850–1900, glacier frame | flat [−3, 1] | −0.05 | −2.33 | 0.71 |
| `gic_log10_kappa_R19` | log₁₀ of the response-rate constant κ, RGI 19 | log₁₀(yr⁻¹ K⁻ν) | N(κ̂(amp), 0.114) on [−3.91, −1.66]ᵃ | −2.78 | −3 | −2.56 |
| `gic_a_SLOWG` | Committed-loss scale a, SLOWG | m SLE | N(0.146, 0.0328) on [0.0333, 0.277] | 0.133 | 0.088 | 0.179 |
| `gic_b_SLOWG` | Equilibrium temperature sensitivity b, SLOWG | K⁻¹ (glacier frame) | flat [0.05, 3] | 0.2 | 0.128 | 0.347 |
| `gic_T_off_SLOWG` | Equilibrium temperature offset T_off, SLOWG | K rel. 1850–1900, glacier frame | flat [−3, 1] | −1.65 | −2.85 | 0.09 |
| `gic_log10_kappa_SLOWG` | log₁₀ of the response-rate constant κ, SLOWG | log₁₀(yr⁻¹ K⁻ν) | N(κ̂(amp), 0.114) on [−4.75, −2.17]ᵃ | −3.44 | −3.68 | −3.21 |
| `gic_a_FASTG` | Committed-loss scale a, FASTG | m SLE | N(0.14, 0.0242) on [0.0809, 0.237] | 0.146 | 0.112 | 0.18 |
| `gic_b_FASTG` | Equilibrium temperature sensitivity b, FASTG | K⁻¹ (glacier frame) | flat [0.05, 3] | 0.334 | 0.24 | 0.476 |
| `gic_T_off_FASTG` | Equilibrium temperature offset T_off, FASTG | K rel. 1850–1900, glacier frame | flat [−3, 1] | −1.53 | −2.44 | −0.8 |
| `gic_log10_kappa_FASTG` | log₁₀ of the response-rate constant κ, FASTG | log₁₀(yr⁻¹ K⁻ν) | N(κ̂(amp), 0.114) on [−3.77, −1.52]ᵃ | −2.56 | −2.75 | −2.37 |
| **Glacier regional temperature amplification** | | | | | | |
| `gic_amp_R19` | Regional/global warming ratio, RGI 19 | – | N(0.72, 0.15) on [0.58, 0.88] | 0.727 | 0.598 | 0.86 |
| `gic_amp_SLOWG` | Regional/global warming ratio, SLOWG | – | N(2.5, 0.45) on [1.8, 3.5] | 2.57 | 2.02 | 3.17 |
| `gic_amp_FASTG` | Regional/global warming ratio, FASTG | – | N(1.45, 0.15) on [1.33, 1.82] | 1.46 | 1.35 | 1.66 |
| **Glacier scope and ledger terms (hindcast-target constructs)** | | | | | | |
| `gic_u_unch` | Uncharted-ice content of the Frederikse glacier target | mm SLE | flat [14.5, 41.8] | 28 | 18.5 | 37.8 |
| `gic_delta` | Early-segment (1900–1960) rate bias of the glacier target | mm yr⁻¹ | N(0, 0.3) on [−1.2, 1.2] | 0.243 | 0.111 | 0.392 |
| `gic_u_pre` | Pre-1901 uncharted-ice set-aside (ledger) | mm SLE | flat [0, 25] | 7.5 | 0.7 | 20.3 |
| `gic_s_r5` | RGI 05 share of the 19th-century glacier datum (ledger) | mm SLE | N(2.5, 2) on [0, 8] | 2.58 | 0.37 | 5.59 |
| **Greenland ice sheet (two channels, two basins)** | | | | | | |
| `gis_c1` | Committed-loss sensitivity to regional temperature | m SLE K⁻¹ | N(0.0328, 0.05) on [0, 4] | 0.0463 | 0.0347 | 0.0688 |
| `gis_c0` | Committed loss at zero regional anomaly | m SLE | N(0.0404, 0.1) on [0, 4] | 0.061 | 0.045 | 0.105 |
| `gis_f` | Surface-mass-balance share of the committed loss | – | N(0.783, 0.3) on [0.02, 0.98] | 0.543 | 0.314 | 0.721 |
| `gis_alpha_f` | Fast (SMB) channel rate, temperature-dependent part | yr⁻¹ K⁻¹ | N(0.00285, 0.02) on [0, 0.5] | 0.0048 | 0.0016 | 0.0102 |
| `gis_beta_f` | Fast (SMB) channel rate, constant part | yr⁻¹ | N(0.00737, 0.05) on [0.000001, 0.5] | 0.0097 | 0.0043 | 0.0158 |
| `gis_slow_ell` | Slow (discharge) channel: log rate at the reference temperature | ln(yr⁻¹) | N(−4.21, 1) on [−8.21, −0.207] | −5.13 | −6.12 | −4.44 |
| `gis_slow_w` | Slow (discharge) channel: temperature-dependent fraction of the rate | – | flat [0, 1] | 0.525 | 0.076 | 0.949 |
| `gis_s_high` | log₁₀ rate scale of the high basin (NO+NE) relative to the active basin | log₁₀(–) | N(0, 0.5) on [−2, 2] | −0.645 | −0.863 | −0.432 |
| `gis_amp` | Southern-Greenland/global warming ratio | – | N(1.92, 0.318) on [1.51, 2.28] | 1.92 | 1.58 | 2.23 |
| **Antarctic ice sheet (DAIS) and Antarctic ocean** | | | | | | |
| `ais_gmst_amp` | Antarctic/global warming ratio | – | N(1.09, 0.18) on [0.55, 1.63] | 1.07 | 0.78 | 1.35 |
| `ais_ocean_temperature₀` | Initial high-latitude ocean subsurface temperature T_oc,0 | °C | N(0.72, 0.5) on [0.5, 2] | 0.87 | 0.54 | 1.52 |
| `antarctic_alpha` | Partition of ocean subsurface temperature into ice flux, α_DAIS | – | N(0.22, 0.195) on [0.00591, 0.862] | 0.266 | 0.099 | 0.418 |
| `antarctic_nu` | Runoff-decrease-with-height to precipitation constant ν | m⁻¹ᐟ² yr⁻¹ᐟ² | N(0.00923, 0.00321) on [0.0033, 0.0148] | 0.0097 | 0.006 | 0.0135 |
| `antarctic_temp_threshold` | Fast-dynamics temperature threshold | °C (DAIS scale) | N(−15.6, 0.435) on [−16.4, −14.5] | −15.6 | −16.2 | −14.9 |
| `anto_alpha` | Antarctic ocean temperature sensitivity a_ANTO | °C °C⁻¹ | N(0.194, 0.188) on [0.00362, 0.845] | 0.326 | 0.151 | 0.557 |
| `anto_beta` | Antarctic ocean temperature offset b_ANTO | °C | N(0.899, 0.543) on [0.0268, 1.95] | 1.07 | 0.27 | 1.76 |
| `antarctic_lambda` | Fast-dynamics disintegration rate λ | m yr⁻¹ | N(0.0104, 0.00364) on [0.00397, 0.0207] | 0.0104 | 0.0053 | 0.0163 |
| `antarctic_gamma` | Power of ice-flow speed on water depth γ | – | N(2.79, 0.929) on [0.747, 4.22] | 2.74 | 1.35 | 3.93 |
| `antarctic_kappa` | Exponential dependence of precipitation on Antarctic temperature κ_DAIS | °C⁻¹ | N(0.0656, 0.0135) on [0.0307, 0.0845] | 0.0579 | 0.0386 | 0.0772 |
| `ais_mu` | Profile parameter µ | m¹ᐟ² | paleo N(10.8, 1.81) on [7.05, 13.6]ᵇ | 10.5 | 8.3 | 12.9 |
| `ais_bedheight0` | Bed height at the continent centre b₀ | m | paleo N(780, 23) on [740, 820]ᵇ | 782 | 749 | 813 |
| `ais_slope` | Bed slope | – | paleo N(0.000628, 0.000062) on [0.00045, 0.00075]ᵇ | 0.00063 | 0.000596 | 0.00066 |
| `ais_iceflow0` | Ice-flow constant f₀ | m yr⁻¹ | paleo N(1.24, 0.341) on [0.6, 1.8]ᵇ | 0.97 | 0.72 | 1.25 |
| `ais_precip0_LOG` | ln of the precipitation constant P₀ | ln(m yr⁻¹) | paleo N(−0.919, 0.743) on [−3.65, 0.405]ᵇ | −0.638 | −0.993 | −0.279 |
| `ais_runoff_Ton` | Runoff onset temperature T_on = −h₀/c (sampled in place of h₀) | °C (DAIS scale) | paleo N(−15.6, 5.54) on [−43.3, −5.22]ᵇ | −17.8 | −18 | −17.5 |
| `ais_c` | Runoff-line slope c | m °C⁻¹ | paleo N(97.2, 26.6) on [47.5, 142]ᵇ | 86 | 55 | 121 |
| **Thermal expansion** | | | | | | |
| `thermal_alpha` | Thermal expansion coefficient α | kg m⁻³ °C⁻¹ | N(0.16, 0.0289) on [0.102, 0.24] | 0.172 | 0.155 | 0.185 |
| **Model-discrepancy coefficients** | | | | | | |
| `d2_gsic_1` | Glacier discrepancy, basis coefficient 1 | cm (RMS) | N(0, 0.5) on [−2.5, 2.5] | 0.036 | −0.076 | 0.14 |
| `d2_gsic_2` | Glacier discrepancy, basis coefficient 2 | cm (RMS) | N(0, 0.5) on [−2.5, 2.5] | 0.041 | −0.053 | 0.126 |
| `d2_steric_1` | Thermal-expansion discrepancy, basis coefficient 1 | cm (RMS) | N(0, 0.5) on [−2.5, 2.5] | 0.258 | 0.093 | 0.402 |
| `d2_steric_2` | Thermal-expansion discrepancy, basis coefficient 2 | cm (RMS) | N(0, 0.5) on [−2.5, 2.5] | 0.013 | −0.099 | 0.129 |
| **Observation-error model (AR(1) per target series)** | | | | | | |
| `sd_ais` | AR(1) innovation sd, Antarctica | cm | half-normal N⁺(0, 5) | 0.0135 | 0.0016 | 0.0284 |
| `rho_ais` | AR(1) autocorrelation, Antarctica | – | flat [0, 0.99] | 0.618 | 0.08 | 0.931 |
| `sd_gsic` | AR(1) innovation sd, glaciers | cm | half-normal N⁺(0, 5) | 0.0164 | 0.0016 | 0.0406 |
| `rho_gsic` | AR(1) autocorrelation, glaciers | – | flat [0, 0.99] | 0.72 | 0.083 | 0.976 |
| `sd_gis` | AR(1) innovation sd, Greenland | cm | half-normal N⁺(0, 5) | 0.016 | 0.003 | 0.0288 |
| `rho_gis` | AR(1) autocorrelation, Greenland | – | flat [0, 0.99] | 0.741 | 0.173 | 0.951 |
| `sd_steric` | AR(1) innovation sd, thermal expansion | cm | half-normal N⁺(0, 5) | 0.0707 | 0.0492 | 0.0969 |
| `rho_steric` | AR(1) autocorrelation, thermal expansion | – | flat [0, 0.99] | 0.968 | 0.921 | 0.988 |

<!-- ladrillo_prior_posterior_table.py | tag L24 | priors from calibrate_mcmc_ext.jl --dump-priors (tag L24) | posterior parameters_subsample_brick_mengel_L24.csv n=10000 | quantiles 5/50/95 over all draws | commit ea9121a | 2026-09-19 12:14 -->
