# Information-criterion test: Ladrillo L27 vs BRICK 2.0 hindcast (tag L27)

Common data: the four fitted component series (ais, gsic, gis, steric), 1900-2026 where observed, N = 502 observation-years (ais 126, gsic 124, gis 126, steric 126); one target set, one forcing, one baseline. Parameter counts are EVERY sampled parameter of each posterior (file: {'ladrillo': 50, 'brick20': 35}); k below is what each arm charges.

AR(1) arm: rho bounded at 0.99.

| arm | model | k | ln L (max over draws) | ln L (posterior-median series) | AIC | AICc | BIC |
|---|---|---|---|---|---|---|---|
| obs_iid | Ladrillo L27 | 42 | -66.1 | -667.8 | 216.2 | 224.0 | 393.3 |
| obs_iid | BRICK 2.0 | 27 | -1200.4 | -4165.3 | 2454.7 | 2457.9 | 2568.6 |
| ar1_prof | Ladrillo L27 | 50 | 244.9 | 235.9 | -389.7 | -378.4 | -178.8 |
| ar1_prof | BRICK 2.0 | 35 | 193.7 | 148.7 | -317.3 | -311.9 | -169.7 |

## The test

- **obs_iid**: Δln L (Ladrillo − BRICK 2.0) = **1134.3** for Δk = 15. ΔAIC (BRICK − Ladrillo) = **2238.6**, ΔBIC = **2175.3**. The likelihood gain is worth 1134 parameters under AIC and 365 under BIC (ln N = 6.22); Ladrillo has 15 more.
- **ar1_prof**: Δln L (Ladrillo − BRICK 2.0) = **51.2** for Δk = 15. ΔAIC (BRICK − Ladrillo) = **72.4**, ΔBIC = **9.1**. The likelihood gain is worth 51 parameters under AIC and 16 under BIC (ln N = 6.22); Ladrillo has 15 more.

## Per-series ln L at each model's JOINT maximising draw (ar1_prof, rho ≤ 0.99) and the profiled noise there

| series | Ladrillo L27 ln L | sd | ρ | BRICK 2.0 ln L | sd | ρ | Δln L |
|---|---|---|---|---|---|---|---|
| ais | 121.8 | 0.024 | 0.985 | 127.2 | 0.015 | 0.921 | -5.4 |
| gsic | 8.3 | 0.000 | 0.101 | -24.8 | 0.107 | 0.990 | 33.1 |
| gis | 104.4 | 0.023 | 0.982 | 80.6 | 0.054 | 0.990 | 23.8 |
| steric | 10.4 | 0.072 | 0.990 | 10.7 | 0.070 | 0.990 | -0.4 |

## Per-window decomposition (obs_iid, at each model's own maximising draw)

| window | Ladrillo L27 | BRICK 2.0 | Δln L |
|---|---|---|---|
| 1900-2026 | -66.1 | -1200.4 | 1134.3 |
| 1900-1919 | -81.8 | -226.1 | 144.3 |
| 1920-1949 | -70.8 | -230.7 | 159.9 |
| 1950-1992 | 47.3 | -456.8 | 504.1 |
| 1993-2026 | 39.3 | -286.8 | 326.1 |

## The total (out-of-sample for BOTH — not in either likelihood; reference only)

| arm | Ladrillo L27 ln L (max) | at fit4 max-draw | BRICK 2.0 ln L (max) | at fit4 max-draw |
|---|---|---|---|---|
| obs_iid | -162.0 | -171.0 | -165.3 | -218.7 |
| ar1_prof | -162.0 | -163.4 | -165.3 | -177.0 |

## Reading, and what this does NOT show

- ln L (max over draws) is a LOWER bound on each model's true maximum for this likelihood: neither posterior was optimised for it. Both bounds are from the same draw count.
- DIC / p_V are in the CSV only: p_V = var(D)/2 is an effective parameter count only when the likelihood is the one the posterior was fitted under, which holds for neither arm here (and for BRICK 2.0 on no arm).
- In ar1_prof the profiled rho sits AT the 0.99 bound wherever the residual is a smooth bias (every BRICK 2.0 series; Ladrillo's steric and gsic): the AR(1) term then acts as a near-random-walk discrepancy that absorbs a smooth bias cheaply, so this arm's gain is a function of how much autocorrelation the noise model is allowed. See the --rho-max sensitivity files.
- Ladrillo's thermal-expansion module IS BRICK's (one alpha on the same OHC), so the steric row is a tie by construction: the two best draws produce the same residual to 3 decimals.
- Ladrillo was calibrated to these targets; BRICK 2.0 to Wong's. AIC/BIC correct for a fitted model's own optimism, not for a comparator fitted to different data. The structure test that removes that axis is a BRICK 2.0 arm recalibrated on the extended targets (note_2026-08-14_ladrillo_vs_brick20_scorecard.md).
- obs_iid treats residual years as independent and OVERSTATES the evidence; ar1_prof is the calibrator's own form and the headline.

Provenance: ic_ladrillo_vs_brick20.py | tag L27 | k_phys {'ladrillo': 42, 'brick20': 27} + 8 profiled noise in ar1_prof | N_fit 502 | inputs: ladrillo: ic_hindcast_residuals.jl | Ladrillo tag L27 | posterior parameters_subsample_brick_mengel_L27.csv NDRAW=2000 evenly thinned of 10000 | forcing ssp245harm | run 1850-2026 scored 1900-2026 reref 1995-2005 | gsic = gsic_hind + F_unch vs gsic_adj target, no delta ramp, no d2 | total = glaciers+ais+gis+te+OBSERVED lws vs dang | residual = model - obs, cm || brick20: ic_hindcast_residuals.jl | BRICK 2.0 stock MimiBRICK get_model(ssp245), Random.seed!(2026) immediately before get_model | posterior parameters_subsample_brick.csv NDRAW=10000 evenly thinned of 10000 | forcing ssp245harm | run 1850-2026 scored 1900-2026 reref 1995-2005 | gsic = gsic_sea_level vs gsic_adj target | total = ais+gsic+gis+te+OBSERVED lws vs dang | residual = model - obs, cm
