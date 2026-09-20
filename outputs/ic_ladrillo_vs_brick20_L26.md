# Information-criterion test: Ladrillo L26 vs BRICK 2.0 hindcast (tag L26)

Common data: the four fitted component series (ais, gsic, gis, steric), 1900-2026 where observed, N = 502 observation-years (ais 126, gsic 124, gis 126, steric 126); one target set, one forcing, one baseline. Parameter counts are EVERY sampled parameter of each posterior (file: {'ladrillo': 55, 'brick20': 35}); k below is what each arm charges.

AR(1) arm: rho bounded at 0.99.

| arm | model | k | ln L (max over draws) | ln L (posterior-median series) | AIC | AICc | BIC |
|---|---|---|---|---|---|---|---|
| obs_iid | Ladrillo L26 | 47 | -18.9 | -556.8 | 131.7 | 141.7 | 330.0 |
| obs_iid | BRICK 2.0 | 27 | -1252.1 | -3957.3 | 2558.3 | 2561.5 | 2672.2 |
| ar1_prof | Ladrillo L26 | 55 | 242.6 | 230.2 | -375.1 | -361.3 | -143.1 |
| ar1_prof | BRICK 2.0 | 35 | 180.9 | 137.6 | -291.9 | -286.5 | -144.2 |

## The test

- **obs_iid**: Δln L (Ladrillo − BRICK 2.0) = **1233.3** for Δk = 20. ΔAIC (BRICK − Ladrillo) = **2426.5**, ΔBIC = **2342.2**. The likelihood gain is worth 1233 parameters under AIC and 397 under BIC (ln N = 6.22); Ladrillo has 20 more.
- **ar1_prof**: Δln L (Ladrillo − BRICK 2.0) = **61.6** for Δk = 20. ΔAIC (BRICK − Ladrillo) = **83.3**, ΔBIC = **-1.1**. The likelihood gain is worth 62 parameters under AIC and 20 under BIC (ln N = 6.22); Ladrillo has 20 more.

## Per-series ln L at each model's JOINT maximising draw (ar1_prof, rho ≤ 0.99) and the profiled noise there

| series | Ladrillo L26 ln L | sd | ρ | BRICK 2.0 ln L | sd | ρ | Δln L |
|---|---|---|---|---|---|---|---|
| ais | 115.1 | 0.019 | 0.940 | 114.2 | 0.018 | 0.941 | 0.9 |
| gsic | 8.5 | 0.000 | 0.145 | -24.4 | 0.106 | 0.990 | 32.9 |
| gis | 109.4 | 0.015 | 0.937 | 80.4 | 0.054 | 0.990 | 29.0 |
| steric | 9.6 | 0.074 | 0.990 | 10.7 | 0.070 | 0.990 | -1.1 |

## Per-window decomposition (obs_iid, at each model's own maximising draw)

| window | Ladrillo L26 | BRICK 2.0 | Δln L |
|---|---|---|---|
| 1900-2026 | -18.9 | -1252.1 | 1233.3 |
| 1900-1919 | -93.6 | -228.0 | 134.4 |
| 1920-1949 | -85.4 | -241.3 | 155.8 |
| 1950-1992 | 30.1 | -479.7 | 509.8 |
| 1993-2026 | 130.1 | -303.1 | 433.2 |

## The total (out-of-sample for BOTH — not in either likelihood; reference only)

| arm | Ladrillo L26 ln L (max) | at fit4 max-draw | BRICK 2.0 ln L (max) | at fit4 max-draw |
|---|---|---|---|---|
| obs_iid | -162.2 | -176.4 | -165.3 | -218.7 |
| ar1_prof | -162.2 | -165.9 | -165.3 | -175.4 |

## Reading, and what this does NOT show

- ln L (max over draws) is a LOWER bound on each model's true maximum for this likelihood: neither posterior was optimised for it. Both bounds are from the same draw count.
- DIC / p_V are in the CSV only: p_V = var(D)/2 is an effective parameter count only when the likelihood is the one the posterior was fitted under, which holds for neither arm here (and for BRICK 2.0 on no arm).
- In ar1_prof the profiled rho sits AT the 0.99 bound wherever the residual is a smooth bias (every BRICK 2.0 series; Ladrillo's steric and gsic): the AR(1) term then acts as a near-random-walk discrepancy that absorbs a smooth bias cheaply, so this arm's gain is a function of how much autocorrelation the noise model is allowed. See the --rho-max sensitivity files.
- Ladrillo's thermal-expansion module IS BRICK's (one alpha on the same OHC), so the steric row is a tie by construction: the two best draws produce the same residual to 3 decimals.
- Ladrillo was calibrated to these targets; BRICK 2.0 to Wong's. AIC/BIC correct for a fitted model's own optimism, not for a comparator fitted to different data. The structure test that removes that axis is a BRICK 2.0 arm recalibrated on the extended targets (note_2026-08-14_ladrillo_vs_brick20_scorecard.md).
- obs_iid treats residual years as independent and OVERSTATES the evidence; ar1_prof is the calibrator's own form and the headline.

Provenance: ic_ladrillo_vs_brick20.py | tag L26 | k_phys {'ladrillo': 47, 'brick20': 27} + 8 profiled noise in ar1_prof | N_fit 502 | inputs: ladrillo: ic_hindcast_residuals.jl | Ladrillo tag L26 | posterior parameters_subsample_brick_mengel_L26.csv NDRAW=2000 evenly thinned of 10000 | forcing ssp245harm | run 1850-2026 scored 1900-2026 reref 1995-2005 | gsic = gsic_hind + F_unch vs gsic_adj target, no delta ramp, no d2 | total = glaciers+ais+gis+te+OBSERVED lws vs dang | residual = model - obs, cm || brick20: ic_hindcast_residuals.jl | BRICK 2.0 stock MimiBRICK get_model(ssp245), Random.seed!(2026) immediately before get_model | posterior parameters_subsample_brick.csv NDRAW=10000 evenly thinned of 10000 | forcing ssp245harm | run 1850-2026 scored 1900-2026 reref 1995-2005 | gsic = gsic_sea_level vs gsic_adj target | total = ais+gsic+gis+te+OBSERVED lws vs dang | residual = model - obs, cm
