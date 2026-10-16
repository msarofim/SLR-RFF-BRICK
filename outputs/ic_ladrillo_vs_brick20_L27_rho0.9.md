# Information-criterion test: Ladrillo L27 vs BRICK 2.0 hindcast (tag L27)

Common data: the four fitted component series (ais, gsic, gis, steric), 1900-2025 where observed, N = 502 observation-years (ais 126, gsic 124, gis 126, steric 126); one target set, one forcing, one baseline. Parameter counts are EVERY sampled parameter of each posterior (file: {'ladrillo': 50, 'brick20': 35}); k below is what each arm charges.

AR(1) arm: rho bounded at 0.9.  Draws: 10000 Ladrillo, 10000 BRICK 2.0.

| arm | model | k | ln L (max over draws) | ln L (posterior-median series) | AIC | AICc | BIC |
|---|---|---|---|---|---|---|---|
| obs_iid | Ladrillo L27 | 42 | 23.2 | -588.2 | 37.5 | 45.4 | 214.7 |
| obs_iid | BRICK 2.0 | 27 | -1504.4 | -4488.1 | 3062.8 | 3066.0 | 3176.7 |
| ar1_prof | Ladrillo L27 | 50 | 227.0 | 209.7 | -354.0 | -342.7 | -143.1 |
| ar1_prof | BRICK 2.0 | 35 | 95.2 | -37.0 | -120.5 | -115.1 | 27.2 |

## The test

- **obs_iid**: Δln L (Ladrillo − BRICK 2.0) = **1527.6** for Δk = 15. ΔAIC (BRICK − Ladrillo) = **3025.2**, ΔBIC = **2962.0**. The likelihood gain is worth 1528 parameters under AIC and 491 under BIC (ln N = 6.22); Ladrillo has 15 more.
- **ar1_prof**: Δln L (Ladrillo − BRICK 2.0) = **131.8** for Δk = 15. ΔAIC (BRICK − Ladrillo) = **233.5**, ΔBIC = **170.2**. The likelihood gain is worth 132 parameters under AIC and 42 under BIC (ln N = 6.22); Ladrillo has 15 more.

## Per-series ln L at each model's JOINT maximising draw (ar1_prof, rho ≤ 0.9) and the profiled noise there

| series | Ladrillo L27 ln L | sd | ρ | BRICK 2.0 ln L | sd | ρ | Δln L |
|---|---|---|---|---|---|---|---|
| ais | 118.0 | 0.013 | 0.754 | 101.5 | 0.039 | 0.900 | 16.6 |
| gsic | 0.4 | 0.031 | 0.900 | -54.7 | 0.202 | 0.900 | 55.1 |
| gis | 110.1 | 0.018 | 0.874 | 47.7 | 0.108 | 0.900 | 62.4 |
| steric | -1.5 | 0.117 | 0.900 | 0.8 | 0.112 | 0.900 | -2.3 |

## Per-window decomposition (obs_iid, at each model's own maximising draw)

| window | Ladrillo L27 | BRICK 2.0 | Δln L |
|---|---|---|---|
| 1900-2025 | 23.2 | -1504.4 | 1527.6 |
| 1900-1919 | -78.1 | -233.3 | 155.3 |
| 1920-1949 | -74.7 | -351.9 | 277.2 |
| 1950-1992 | 50.7 | -824.2 | 874.9 |
| 1993-2025 | 125.3 | -94.9 | 220.2 |

## The total (out-of-sample for BOTH — not in either likelihood; reference only)

| arm | Ladrillo L27 ln L (max) | at fit4 max-draw | BRICK 2.0 ln L (max) | at fit4 max-draw |
|---|---|---|---|---|
| obs_iid | -162.0 | -173.4 | -166.0 | -199.4 |
| ar1_prof | -162.0 | -168.8 | -166.0 | -183.3 |

## Reading, and what this does NOT show

- ln L (max over draws) is a LOWER bound on each model's true maximum for this likelihood: neither posterior was optimised for it. Both bounds are over 10000 draws.
- DIC / p_V are in the CSV only: p_V = var(D)/2 is an effective parameter count only when the likelihood is the one the posterior was fitted under, which holds for neither arm here (and for BRICK 2.0 on no arm).
- In ar1_prof, at each model's joint maximising draw, the profiled rho sits at the 0.9 bound (to 3 decimals) for Ladrillo L27 gsic, Ladrillo L27 steric, BRICK 2.0 ais, BRICK 2.0 gsic, BRICK 2.0 gis, BRICK 2.0 steric. A rho at the bound means the AR(1) term acts as a near-random-walk discrepancy that absorbs a smooth bias cheaply, so this arm's gain depends on how much autocorrelation the noise model is allowed. See the --rho-max sensitivity files.
- Ladrillo's thermal-expansion component is BRICK's (one alpha on the same OHC), so the steric row compares the two posteriors' parameter values at the draws that maximise the four-series total, not two structures: Δln L (steric) = -2.3.
- Ladrillo was calibrated to these targets; BRICK 2.0 to Wong's. AIC/BIC correct for a fitted model's own optimism, not for a comparator fitted to different data. The structure test that removes that axis is a BRICK 2.0 arm recalibrated on the extended targets (note_2026-08-14_ladrillo_vs_brick20_scorecard.md).
- obs_iid treats residual years as independent and OVERSTATES the evidence; ar1_prof is the calibrator's own form and the headline.

Provenance: ic_ladrillo_vs_brick20.py | tag L27 | k_phys {'ladrillo': 42, 'brick20': 27} + 8 profiled noise in ar1_prof | N_fit 502 | inputs: ladrillo: ic_hindcast_residuals.jl | Ladrillo tag L27 | posterior parameters_subsample_brick_mengel_L27.csv NDRAW=10000 evenly thinned of 10000 | forcing ssp245harm | run 1850-2026 scored 1900-2026 reref 1995-2005 | gsic = gsic_hind + F_unch vs gsic_adj target, no delta ramp, no d2 | total = glaciers+ais+gis+te+OBSERVED lws vs dang | residual = model - obs, cm || brick20: ic_hindcast_residuals.jl | BRICK 2.0 stock MimiBRICK get_model(ssp245), Random.seed!(2026) immediately before get_model | posterior parameters_subsample_sneasybrick_zenodo20592337.csv NDRAW=10000 evenly thinned of 10000 | forcing ssp245harm | run 1850-2026 scored 1900-2026 reref 1995-2005 | gsic = gsic_sea_level vs gsic_adj target | total = ais+gsic+gis+te+OBSERVED lws vs dang | residual = model - obs, cm
