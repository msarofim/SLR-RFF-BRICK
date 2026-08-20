# Where the unidentified directions are (block ridge diagnostic)

- commit `0319384`; tag `L14`; 4 chains, first 50% burned, thinned 1-in-200
- eigen-analysis on the CORRELATION matrix (z-scores), computed WITHIN each chain — the pooled posterior of a non-converged block is a mixture, not a ridge

## ais_geometry  (7 parameters)

Eigen-spectrum (mean over chains, % of standardised variance): 28%, 18%, 16%, 14%, 12%, 10%, 2%
Condition number of the correlation matrix: 13

**Loosest direction, chain-to-chain alignment |cos| = 0.583, 0.625, 0.857** — the chains do NOT agree on the loose direction; they are in different places, and a single reparameterisation may not serve all four.

| direction | % var | loadings (largest first) |
|---|---|---|
| loosest | 28% | ais_slope +0.65  ais_iceflow0 -0.43  ais_mu +0.32  ais_bedheight0 +0.31 |
| 2nd loosest | 18% | ais_runoff_Ton +0.54  ais_c -0.41  ais_mu +0.16  ais_iceflow0 -0.16 |
| STIFFEST | 2% | ais_slope -0.70  ais_bedheight0 +0.49  ais_iceflow0 -0.44  ais_mu +0.10 |

**Worst-mixing directions — where the four chains DISAGREE.** Within-chain covariance cannot see these (a chain with ESS 12 on an axis has not moved along it); this is the generalised eigenproblem `B v = lambda W v`, i.e. a directional R-hat.

| rank | between/within | loadings |
|---|---|---|
| 1 | 1.69 | ais_iceflow0 +0.97  ais_slope -0.19  ais_runoff_Ton +0.10  ais_bedheight0 +0.08 |
| 2 | 0.40 | ais_slope +0.72  ais_iceflow0 +0.65  ais_bedheight0 -0.21  ais_precip0_LOG -0.10 |
| 3 | 0.01 | ais_bedheight0 +0.87  ais_runoff_Ton +0.40  ais_iceflow0 -0.18  ais_c -0.15 |

The top direction carries 81% of all between-chain variance. It is CONCENTRATED, so one reparameterisation addresses most of the non-mixing.

Per-parameter share of that direction (|loading|, z-scored — what a new coordinate must be built from):

| param | |loading| on worst direction |
|---|---|
| ais_iceflow0 | 0.97 |
| ais_slope | 0.19 |
| ais_runoff_Ton | 0.10 |
| ais_bedheight0 | 0.08 |
| ais_precip0_LOG | 0.06 |
| ais_c | 0.04 |
| ais_mu | 0.02 |

Pairs with |r| >= 0.8 in at least one chain:

| pair | mean r | range | chains |
|---|---|---|---|
| ais_slope — ais_iceflow0 | -0.846 | [-0.846, -0.846] | 1/4 |

Posterior/prior width (mean over chains) — < 1 means the data constrain it, ~1 means the marginal is the prior:

| param | post sd / prior sd |
|---|---|
| ais_mu | 0.73 |
| ais_bedheight0 | 0.80 |
| ais_slope | 0.30 |
| ais_iceflow0 | 0.34 |
| ais_precip0_LOG | 0.29 |
| ais_runoff_Ton | 0.02 |
| ais_c | 0.70 |

## ais_other  (10 parameters)

Eigen-spectrum (mean over chains, % of standardised variance): 19%, 13%, 11%, 10%, 10%, 10%, 10%, 9%, 6%, 2%
Condition number of the correlation matrix: 8

**Loosest direction, chain-to-chain alignment |cos| = 0.404, 0.536, 0.213** — the chains do NOT agree on the loose direction; they are in different places, and a single reparameterisation may not serve all four.

| direction | % var | loadings (largest first) |
|---|---|---|
| loosest | 19% | ais_ocean_temperature₀ +0.32  antarctic_nu -0.09  antarctic_temp_threshold -0.04  antarctic_gamma +0.03 |
| 2nd loosest | 13% | anto_beta +0.55  ais_ocean_temperature₀ +0.50  antarctic_alpha +0.13  ais_gmst_amp +0.08 |
| STIFFEST | 2% | antarctic_nu -0.35  antarctic_alpha -0.22  antarctic_kappa +0.22  anto_alpha -0.21 |

**Worst-mixing directions — where the four chains DISAGREE.** Within-chain covariance cannot see these (a chain with ESS 12 on an axis has not moved along it); this is the generalised eigenproblem `B v = lambda W v`, i.e. a directional R-hat.

| rank | between/within | loadings |
|---|---|---|
| 1 | 1.44 | antarctic_alpha +0.94  anto_alpha +0.27  antarctic_nu +0.14  anto_beta -0.11 |
| 2 | 0.26 | anto_beta -0.78  ais_ocean_temperature₀ +0.57  antarctic_alpha +0.22  antarctic_nu +0.11 |
| 3 | 0.03 | antarctic_nu -0.76  anto_alpha -0.52  ais_ocean_temperature₀ +0.31  antarctic_temp_threshold -0.14 |

The top direction carries 83% of all between-chain variance. It is CONCENTRATED, so one reparameterisation addresses most of the non-mixing.

Per-parameter share of that direction (|loading|, z-scored — what a new coordinate must be built from):

| param | |loading| on worst direction |
|---|---|
| antarctic_alpha | 0.94 |
| anto_alpha | 0.27 |
| antarctic_nu | 0.14 |
| anto_beta | 0.11 |
| antarctic_kappa | 0.07 |
| ais_ocean_temperature₀ | 0.05 |
| antarctic_temp_threshold | 0.02 |
| ais_gmst_amp | 0.02 |
| antarctic_gamma | 0.01 |
| antarctic_lambda | 0.00 |

Pairs with |r| >= 0.8 in at least one chain:

| pair | mean r | range | chains |
|---|---|---|---|
| antarctic_alpha — anto_alpha | -0.823 | [-0.823, -0.823] | 1/4 |

## greenland  (8 parameters)

Eigen-spectrum (mean over chains, % of standardised variance): 40%, 23%, 14%, 12%, 7%, 2%, 1%, 1%
Condition number of the correlation matrix: 67

**Loosest direction, chain-to-chain alignment |cos| = 0.959, 0.988, 0.976** — all four chains see the SAME loose direction, so a reparameterisation along it is well posed.

| direction | % var | loadings (largest first) |
|---|---|---|
| loosest | 40% | gis_slow_ell -0.49  gis_f -0.47  gis_c1 +0.46  gis_c0 +0.44 |
| 2nd loosest | 23% | gis_alpha_f -0.59  gis_slow_w -0.46  gis_beta_f +0.39  gis_c0 -0.33 |
| STIFFEST | 1% | gis_alpha_f +0.55  gis_c1 +0.51  gis_beta_f +0.45  gis_f +0.41 |

**Worst-mixing directions — where the four chains DISAGREE.** Within-chain covariance cannot see these (a chain with ESS 12 on an axis has not moved along it); this is the generalised eigenproblem `B v = lambda W v`, i.e. a directional R-hat.

| rank | between/within | loadings |
|---|---|---|
| 1 | 0.06 | gis_c0 -0.79  gis_c1 -0.49  gis_slow_ell -0.22  gis_alpha_f -0.20 |
| 2 | 0.01 | gis_beta_f -0.65  gis_alpha_f -0.61  gis_c0 +0.38  gis_slow_ell -0.16 |
| 3 | 0.00 | gis_c0 -0.54  gis_f -0.54  gis_slow_ell -0.39  gis_c1 -0.34 |

The top direction carries 84% of all between-chain variance. It is CONCENTRATED, so one reparameterisation addresses most of the non-mixing.

Per-parameter share of that direction (|loading|, z-scored — what a new coordinate must be built from):

| param | |loading| on worst direction |
|---|---|
| gis_c0 | 0.79 |
| gis_c1 | 0.49 |
| gis_slow_ell | 0.22 |
| gis_alpha_f | 0.20 |
| gis_f | 0.19 |
| gis_s_high | 0.13 |
| gis_beta_f | 0.03 |
| gis_slow_w | 0.01 |

Pairs with |r| >= 0.8 in at least one chain:

| pair | mean r | range | chains |
|---|---|---|---|
| gis_c0 — gis_slow_ell | -0.808 | [-0.815, -0.802] | 2/4 |

Posterior/prior width (mean over chains) — < 1 means the data constrain it, ~1 means the marginal is the prior:

| param | post sd / prior sd |
|---|---|
| gis_c1 | 0.20 |
| gis_c0 | 0.19 |
| gis_f | 0.40 |
| gis_alpha_f | 0.13 |
| gis_beta_f | 0.07 |
| gis_slow_ell | 0.50 |
| gis_slow_w | 0.95 |
| gis_s_high | 0.26 |

