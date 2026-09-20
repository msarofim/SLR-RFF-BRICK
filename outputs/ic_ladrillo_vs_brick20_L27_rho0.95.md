# Information-criterion test: Ladrillo L27 vs BRICK 2.0 hindcast (tag L27)

Common data: the four fitted component series (ais, gsic, gis, steric), 1900-2026 where observed, N = 502 observation-years (ais 126, gsic 124, gis 126, steric 126); one target set, one forcing, one baseline. Parameter counts are EVERY sampled parameter of each posterior (file: {'ladrillo': 50, 'brick20': 35}); k below is what each arm charges.

AR(1) arm: rho bounded at 0.95.

| arm | model | k | ln L (max over draws) | ln L (posterior-median series) | AIC | AICc | BIC |
|---|---|---|---|---|---|---|---|
| obs_iid | Ladrillo L27 | 42 | 23.2 | -588.9 | 37.5 | 45.4 | 214.7 |
| obs_iid | BRICK 2.0 | 27 | -1252.1 | -3957.3 | 2558.3 | 2561.5 | 2672.2 |
| ar1_prof | Ladrillo L27 | 50 | 233.8 | 223.7 | -367.7 | -356.4 | -156.7 |
| ar1_prof | BRICK 2.0 | 35 | 148.2 | 58.1 | -226.4 | -221.0 | -78.8 |

## The test

- **obs_iid**: Δln L (Ladrillo − BRICK 2.0) = **1275.4** for Δk = 15. ΔAIC (BRICK − Ladrillo) = **2520.8**, ΔBIC = **2457.5**. The likelihood gain is worth 1275 parameters under AIC and 410 under BIC (ln N = 6.22); Ladrillo has 15 more.
- **ar1_prof**: Δln L (Ladrillo − BRICK 2.0) = **85.6** for Δk = 15. ΔAIC (BRICK − Ladrillo) = **141.2**, ΔBIC = **78.0**. The likelihood gain is worth 86 parameters under AIC and 28 under BIC (ln N = 6.22); Ladrillo has 15 more.

## Per-series ln L at each model's JOINT maximising draw (ar1_prof, rho ≤ 0.95) and the profiled noise there

| series | Ladrillo L27 ln L | sd | ρ | BRICK 2.0 ln L | sd | ρ | Δln L |
|---|---|---|---|---|---|---|---|
| ais | 114.0 | 0.019 | 0.950 | 110.5 | 0.024 | 0.950 | 3.5 |
| gsic | 4.8 | 0.017 | 0.950 | -44.4 | 0.169 | 0.950 | 49.2 |
| gis | 108.0 | 0.018 | 0.950 | 75.1 | 0.065 | 0.950 | 33.0 |
| steric | 7.0 | 0.090 | 0.950 | 7.0 | 0.090 | 0.950 | 0.0 |

## Per-window decomposition (obs_iid, at each model's own maximising draw)

| window | Ladrillo L27 | BRICK 2.0 | Δln L |
|---|---|---|---|
| 1900-2026 | 23.2 | -1252.1 | 1275.4 |
| 1900-1919 | -78.1 | -228.0 | 150.0 |
| 1920-1949 | -74.7 | -241.3 | 166.5 |
| 1950-1992 | 50.7 | -479.7 | 530.4 |
| 1993-2026 | 125.3 | -303.1 | 428.4 |

## The total (out-of-sample for BOTH — not in either likelihood; reference only)

| arm | Ladrillo L27 ln L (max) | at fit4 max-draw | BRICK 2.0 ln L (max) | at fit4 max-draw |
|---|---|---|---|---|
| obs_iid | -162.0 | -173.4 | -165.3 | -218.7 |
| ar1_prof | -162.0 | -164.9 | -165.3 | -183.1 |

## Reading, and what this does NOT show

- ln L (max over draws) is a LOWER bound on each model's true maximum for this likelihood: neither posterior was optimised for it. Both bounds are from the same draw count.
- DIC / p_V are in the CSV only: p_V = var(D)/2 is an effective parameter count only when the likelihood is the one the posterior was fitted under, which holds for neither arm here (and for BRICK 2.0 on no arm).
- In ar1_prof the profiled rho sits AT the 0.95 bound wherever the residual is a smooth bias (every BRICK 2.0 series; Ladrillo's steric and gsic): the AR(1) term then acts as a near-random-walk discrepancy that absorbs a smooth bias cheaply, so this arm's gain is a function of how much autocorrelation the noise model is allowed. See the --rho-max sensitivity files.
- Ladrillo's thermal-expansion module IS BRICK's (one alpha on the same OHC), so the steric row is a tie by construction: the two best draws produce the same residual to 3 decimals.
- Ladrillo was calibrated to these targets; BRICK 2.0 to Wong's. AIC/BIC correct for a fitted model's own optimism, not for a comparator fitted to different data. The structure test that removes that axis is a BRICK 2.0 arm recalibrated on the extended targets (note_2026-08-14_ladrillo_vs_brick20_scorecard.md).
- obs_iid treats residual years as independent and OVERSTATES the evidence; ar1_prof is the calibrator's own form and the headline.

Provenance: ic_ladrillo_vs_brick20.py | tag L27 | k_phys {'ladrillo': 42, 'brick20': 27} + 8 profiled noise in ar1_prof | N_fit 502 | inputs: ladrillo: ic_hindcast_residuals.jl | Ladrillo tag L27 | posterior parameters_subsample_brick_mengel_L27.csv NDRAW=2000 evenly thinned of 10000 | forcing ssp245harm | run 1850-2026 scored 1900-2026 reref 1995-2005 | gsic = gsic_hind + F_unch vs gsic_adj target, no delta ramp, no d2 | total = glaciers+ais+gis+te+OBSERVED lws vs dang | residual = model - obs, cm || brick20: ic_hindcast_residuals.jl | BRICK 2.0 stock MimiBRICK get_model(ssp245), Random.seed!(2026) immediately before get_model | posterior parameters_subsample_brick.csv NDRAW=10000 evenly thinned of 10000 | forcing ssp245harm | run 1850-2026 scored 1900-2026 reref 1995-2005 | gsic = gsic_sea_level vs gsic_adj target | total = ais+gsic+gis+te+OBSERVED lws vs dang | residual = model - obs, cm
