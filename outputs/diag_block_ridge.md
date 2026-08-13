# Where the unidentified directions are (block ridge diagnostic)

- commit `76bbc0a`; tag `L10`; 4 chains, first 50% burned, thinned 1-in-200
- eigen-analysis on the CORRELATION matrix (z-scores), computed WITHIN each chain — the pooled posterior of a non-converged block is a mixture, not a ridge

## ais_geometry  (7 parameters)

Eigen-spectrum (mean over chains, % of standardised variance): 26%, 17%, 15%, 14%, 13%, 11%, 3%
Condition number of the correlation matrix: 8

**Loosest direction, chain-to-chain alignment |cos| = 0.983, 0.965, 0.991** — all four chains see the SAME loose direction, so a reparameterisation along it is well posed.

| direction | % var | loadings (largest first) |
|---|---|---|
| loosest | 26% | ais_slope +0.70  ais_bedheight0 +0.51  ais_iceflow0 -0.39  ais_mu +0.29 |
| 2nd loosest | 17% | ais_runoff_Ton +0.36  ais_mu +0.25  ais_c -0.22  ais_bedheight0 -0.12 |
| STIFFEST | 3% | ais_slope -0.71  ais_bedheight0 +0.55  ais_iceflow0 -0.36  ais_mu +0.19 |

**Worst-mixing directions — where the four chains DISAGREE.** Within-chain covariance cannot see these (a chain with ESS 12 on an axis has not moved along it); this is the generalised eigenproblem `B v = lambda W v`, i.e. a directional R-hat.

| rank | between/within | loadings |
|---|---|---|
| 1 | 2.90 | ais_iceflow0 +1.00  ais_slope +0.06  ais_precip0_LOG -0.05  ais_runoff_Ton -0.04 |
| 2 | 0.06 | ais_slope +0.76  ais_iceflow0 +0.44  ais_bedheight0 -0.41  ais_runoff_Ton -0.20 |
| 3 | 0.00 | ais_runoff_Ton +0.63  ais_slope +0.57  ais_iceflow0 +0.43  ais_precip0_LOG +0.21 |

The top direction carries 98% of all between-chain variance. It is CONCENTRATED, so one reparameterisation addresses most of the non-mixing.

Per-parameter share of that direction (|loading|, z-scored — what a new coordinate must be built from):

| param | |loading| on worst direction |
|---|---|
| ais_iceflow0 | 1.00 |
| ais_slope | 0.06 |
| ais_precip0_LOG | 0.05 |
| ais_runoff_Ton | 0.04 |
| ais_bedheight0 | 0.03 |
| ais_mu | 0.02 |
| ais_c | 0.00 |

No pair reaches |r| >= 0.8 in any chain — the loose direction is not a two-parameter ridge.

Posterior/prior width (mean over chains) — < 1 means the data constrain it, ~1 means the marginal is the prior:

| param | post sd / prior sd |
|---|---|
| ais_mu | 0.73 |
| ais_bedheight0 | 0.82 |
| ais_slope | 0.27 |
| ais_iceflow0 | 0.32 |
| ais_precip0_LOG | 0.28 |
| ais_runoff_Ton | 0.02 |
| ais_c | 0.70 |

## ais_other  (10 parameters)

Eigen-spectrum (mean over chains, % of standardised variance): 18%, 15%, 11%, 10%, 10%, 10%, 10%, 8%, 5%, 2%
Condition number of the correlation matrix: 8

**Loosest direction, chain-to-chain alignment |cos| = 0.655, 0.874, 0.508** — the chains do NOT agree on the loose direction; they are in different places, and a single reparameterisation may not serve all four.

| direction | % var | loadings (largest first) |
|---|---|---|
| loosest | 18% | antarctic_alpha +0.62  anto_alpha -0.43  ais_ocean_temperature₀ +0.31  anto_beta +0.25 |
| 2nd loosest | 15% | ais_ocean_temperature₀ +0.54  anto_alpha +0.43  anto_beta +0.32  antarctic_kappa +0.28 |
| STIFFEST | 2% | ais_ocean_temperature₀ +0.38  anto_alpha -0.34  antarctic_alpha -0.30  anto_beta -0.24 |

**Worst-mixing directions — where the four chains DISAGREE.** Within-chain covariance cannot see these (a chain with ESS 12 on an axis has not moved along it); this is the generalised eigenproblem `B v = lambda W v`, i.e. a directional R-hat.

| rank | between/within | loadings |
|---|---|---|
| 1 | 1.32 | ais_ocean_temperature₀ -0.57  anto_beta +0.54  antarctic_alpha +0.41  antarctic_nu -0.38 |
| 2 | 0.08 | anto_alpha -0.63  antarctic_alpha -0.50  antarctic_nu -0.42  ais_ocean_temperature₀ +0.34 |
| 3 | 0.02 | antarctic_alpha +0.76  anto_beta -0.53  ais_ocean_temperature₀ +0.37  antarctic_nu +0.06 |

The top direction carries 93% of all between-chain variance. It is CONCENTRATED, so one reparameterisation addresses most of the non-mixing.

Per-parameter share of that direction (|loading|, z-scored — what a new coordinate must be built from):

| param | |loading| on worst direction |
|---|---|
| ais_ocean_temperature₀ | 0.57 |
| anto_beta | 0.54 |
| antarctic_alpha | 0.41 |
| antarctic_nu | 0.38 |
| anto_alpha | 0.24 |
| antarctic_kappa | 0.14 |
| ais_gmst_amp | 0.03 |
| antarctic_gamma | 0.01 |
| antarctic_temp_threshold | 0.01 |
| antarctic_lambda | 0.01 |

No pair reaches |r| >= 0.8 in any chain — the loose direction is not a two-parameter ridge.

## greenland  (7 parameters)

Eigen-spectrum (mean over chains, % of standardised variance): 46%, 24%, 16%, 10%, 3%, 2%, 1%
Condition number of the correlation matrix: 90

**Loosest direction, chain-to-chain alignment |cos| = 0.976, 0.993, 0.979** — all four chains see the SAME loose direction, so a reparameterisation along it is well posed.

| direction | % var | loadings (largest first) |
|---|---|---|
| loosest | 46% | gis_alpha_f -0.49  gis_beta_f +0.48  gis_c1 +0.47  gis_c0 -0.32 |
| 2nd loosest | 24% | gis_alpha_s -0.56  gis_beta_s +0.43  gis_c1 +0.31  gis_c0 +0.20 |
| STIFFEST | 1% | gis_alpha_f +0.70  gis_c1 +0.49  gis_beta_f +0.35  gis_c0 +0.25 |

**Worst-mixing directions — where the four chains DISAGREE.** Within-chain covariance cannot see these (a chain with ESS 12 on an axis has not moved along it); this is the generalised eigenproblem `B v = lambda W v`, i.e. a directional R-hat.

| rank | between/within | loadings |
|---|---|---|
| 1 | 1.19 | gis_alpha_s +0.70  gis_beta_s +0.65  gis_c0 +0.16  gis_alpha_f +0.16 |
| 2 | 0.09 | gis_alpha_f -0.59  gis_beta_f -0.43  gis_c0 -0.38  gis_c1 -0.36 |
| 3 | 0.01 | gis_c1 +0.68  gis_c0 +0.46  gis_alpha_f +0.41  gis_beta_s -0.35 |

The top direction carries 93% of all between-chain variance. It is CONCENTRATED, so one reparameterisation addresses most of the non-mixing.

Per-parameter share of that direction (|loading|, z-scored — what a new coordinate must be built from):

| param | |loading| on worst direction |
|---|---|
| gis_alpha_s | 0.70 |
| gis_beta_s | 0.65 |
| gis_c0 | 0.16 |
| gis_alpha_f | 0.16 |
| gis_c1 | 0.13 |
| gis_beta_f | 0.10 |
| gis_f | 0.08 |

Pairs with |r| >= 0.8 in at least one chain:

| pair | mean r | range | chains |
|---|---|---|---|
| gis_c1 — gis_alpha_f | -0.863 | [-0.895, -0.816] | 3/4 |

Posterior/prior width (mean over chains) — < 1 means the data constrain it, ~1 means the marginal is the prior:

| param | post sd / prior sd |
|---|---|
| gis_c1 | 0.12 |
| gis_c0 | 0.07 |
| gis_f | 0.25 |
| gis_alpha_f | 0.10 |
| gis_beta_f | 0.05 |
| gis_alpha_s | 0.17 |
| gis_beta_s | 0.28 |

