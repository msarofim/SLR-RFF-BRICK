# Which L24 parameters moved furthest from their priors, and whether the moves are justified (2026-09-19)

Source: `outputs/ladrillo_prior_posterior_L24.csv` (priors from `calibrate_mcmc_ext.jl --dump-priors`, posterior
`parameters_subsample_brick_mengel_L24.csv`, 10,000 draws). Shift z = (posterior median − prior µ)/prior σ for the
priors with information (σ < 10 in the code); width ratio = posterior 5–95 % ÷ prior 5–95 %; pile-up = share of
draws within 10 % of the posterior width of a bound. Per-chain checks from the four 2M-iteration chains
(post-burn, thinned 1:50). Modern SMB share computed with `scratchpad/smb_share.jl` (500 draws, the calibrator's
Mouginot windows 1972–1990 vs 2000–2018).

| rank | parameter | prior | posterior | z | width ratio | verdict |
|---|---|---|---|---|---|---|
| 1 | `gis_s_high` (log₁₀ rate scale, NO+NE basin) | N(0, 0.5) | −0.645 (−0.87, −0.43) ⇒ ×0.23 | −1.29 | 0.26 | **justified** — lands on the offline 3-basin prototype's exactly-identified value (0.2165, handoff 08-21) from a prior deliberately centred on the s = 1 null; identical in all four chains; physically the cold NO/NE basin responds slower. Say in the text that the prior centre was the null, not the prototype. |
| 2 | `gis_slow_ell` (log slow-channel rate) | N(−4.21, 1) | −5.13 ⇒ τ ≈ 169 yr (prior centre τ ≈ 67 yr) | −0.92 | 0.51 | **justified** — σ = 1 in log is weak by design; the hindcast shape plus the channel-ordering constraint push discharge slower than the offline A+B fit; this IS the "≈170-year" number the paper quotes. Prior centre came from an offline fit to the same target (on record). |
| 3 | `gic_delta` (early-segment rate bias of the glacier TARGET, mm/yr) | N(0, 0.30) | +0.243 (0.11, 0.39) | +0.81 (2.7σ from 0) | 0.28 | **justifiable but must be stated** — implies the 1900–1960 Frederikse/Marzeion-2015 glacier series is corrected by +δ·(1960−y)/10 cm, i.e. +1.5 cm at 1900 (less early-century melt than the raw target). It is a target-side device, trades against the uncharted-ice scope term (r = −0.49 with `gic_u_unch`), and the posterior excludes zero. Table 4 and FIG 1 score the BARE target (no ramp), so the hindcast-skill claim does not lean on it; the calibration does. Test that would settle it: refit with δ pinned at 0 and read the 1900–1949 glacier RMSE and (b, T_off). ~3 h. |
| 4 | `gis_f` (SMB share of the commitment) | N(0.78, 0.30) | 0.54 (0.31, 0.72) | −0.80 | 0.41 | **justified** — the prior centre was an offline fit of a different configuration; the quantity the data constrain is the MODERN SMB share, and the posterior gives 0.745 (0.66–0.82) against Mouginot's 0.735 ± 0.05. f trades with `gis_slow_ell` (+0.71) and `gis_c0/c1` (−0.6), as a commitment share should. |
| 5 | `ais_iceflow0` (f₀) | paleo N(1.24, 0.34) | 0.97 (0.72, 1.25) | −0.77 | 0.47 | **direction justified, precision NOT** — the 1900-onward Antarctic series moves the paleo prior; but per-chain medians are 0.92 / 0.98 / 1.01 / 1.02 (R̂ 1.26), so the pooled 5–95 % is a lower bound on the true width. |
| 6 | `ais_runoff_Ton` (runoff onset, DAIS scale) | paleo N(−15.6, 5.5) | −17.8 (−18.0, −17.5) | −0.39 | **0.023** | **direction justified, precision suspect** — 0.25 °C wide against a 5.5 °C prior. NOT a mixing artefact (all four chains −17.77…−17.80 with the same width), so it is the likelihood: the runoff line is the lever the smooth 1900–1992 AIS reconstruction pulls on (r = +0.78 with `ais_gmst_amp` — the identified quantity is the onset in GMST space). The reconstruction's serial and cross-series error is not modelled, so this width overstates what the data know; the paper's "must state" item. |
| 7 | `anto_alpha` | N(0.19, 0.19) | 0.33 (0.15, 0.56) | +0.70 | 0.66 | fine — inside BRICK v0.2's own posterior (Wong 2017 Table A4: 0.19, 0.04–0.51). |
| 8 | `antarctic_kappa` | N(0.066, 0.014) | 0.058 | −0.57 | 0.87 | fine. |
| 9 | `d2_steric_1` | N(0, 0.5) | 0.26 (0.09, 0.40) | +0.52 | 0.19 | documented — absorbs the part of the FaIR ocean-heat discrepancy a rescaling cannot. |
| 10 | `thermal_alpha` | N(0.16, 0.029) | 0.172 (0.155, 0.185) | +0.40 | 0.31 | documented — the 1.6.0 driver's early-century OHC. |

**Bound-active priors** (the prior is doing work through its bounds): `gic_T_off_SLOWP` flat [−3, 1] — p05 = −2.85,
10 % of draws within a tenth of the posterior width of −3: the SLOWG offset wants to go colder and the bound stops it.
This bears on the regrowth statement (T_off < 0); a refit with the bound at −4 is the test. `rho_gsic` (26 % near the
0.99 cap) and `rho_steric` (16 %): the known AR(1)-near-random-walk misspecification (memory `ladrillo_noise_model`),
already priced. `ais_ocean_temperature₀` 12 % near its lower bound 0.5.

**Not moved / effectively prior-propagated** (width ratio > 0.8): the three glacier amplifications, `gis_amp`,
`antarctic_lambda` (0.0104 vs 0.0104), `gic_a_*`, `anto_beta` — as the calibration notes say (likelihood-inert
splice tails, or the paleo marginal).

**Recommended sentences for the paper** (methods/appendix, Marcus's voice): (i) name the three deliberate
target-side/scope terms (`gic_delta`, `gic_u_unch`, `gic_u_pre`/`gic_s_r5`) and give δ's posterior; (ii) state that the
AIS geometry posteriors' precision is conditional on the unmodelled error structure of the 1900–1992 reconstruction;
(iii) note the two prior centres taken from offline fits to the same target (`gis_f`, `gis_slow_ell`) with the
"effectively uninformative sigma" caveat that is already in the calibrator comment.
