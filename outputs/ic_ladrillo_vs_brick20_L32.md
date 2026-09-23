# Information-criterion test: Ladrillo L32 vs BRICK 2.0 hindcast (tag L32)

Common data: the four fitted component series (ais, gsic, gis, steric), 1900-2026 where observed, N = 502 observation-years (ais 126, gsic 124, gis 126, steric 126); one target set, one forcing, one baseline. Parameter counts are EVERY sampled parameter of each posterior (file: {'ladrillo': 50, 'brick20': 35}); k below is what each arm charges.

AR(1) arm: rho bounded at 0.99.

| arm | model | k | ln L (max over draws) | ln L (posterior-median series) | AIC | AICc | BIC |
|---|---|---|---|---|---|---|---|
| obs_iid | Ladrillo L32 | 42 | 11.5 | -634.8 | 60.9 | 68.8 | 238.1 |
| obs_iid | BRICK 2.0 | 27 | -1200.4 | -4165.3 | 2454.7 | 2457.9 | 2568.6 |
| ar1_prof | Ladrillo L32 | 50 | 248.0 | 237.0 | -396.0 | -384.7 | -185.1 |
| ar1_prof | BRICK 2.0 | 35 | 193.7 | 148.7 | -317.3 | -311.9 | -169.7 |

## The test

- **obs_iid**: Δln L (Ladrillo − BRICK 2.0) = **1211.9** for Δk = 15. ΔAIC (BRICK − Ladrillo) = **2393.8**, ΔBIC = **2330.5**. The likelihood gain is worth 1212 parameters under AIC and 390 under BIC (ln N = 6.22); Ladrillo has 15 more.
- **ar1_prof**: Δln L (Ladrillo − BRICK 2.0) = **54.3** for Δk = 15. ΔAIC (BRICK − Ladrillo) = **78.7**, ΔBIC = **15.4**. The likelihood gain is worth 54 parameters under AIC and 17 under BIC (ln N = 6.22); Ladrillo has 15 more.

## Per-series ln L at each model's JOINT maximising draw (ar1_prof, rho ≤ 0.99) and the profiled noise there

| series | Ladrillo L32 ln L | sd | ρ | BRICK 2.0 ln L | sd | ρ | Δln L |
|---|---|---|---|---|---|---|---|
| ais | 130.4 | 0.010 | 0.956 | 127.2 | 0.015 | 0.921 | 3.2 |
| gsic | 3.9 | 0.028 | 0.988 | -24.8 | 0.107 | 0.990 | 28.8 |
| gis | 103.5 | 0.023 | 0.988 | 80.6 | 0.054 | 0.990 | 22.9 |
| steric | 10.1 | 0.072 | 0.990 | 10.7 | 0.070 | 0.990 | -0.6 |

## Per-window decomposition (obs_iid, at each model's own maximising draw)

| window | Ladrillo L32 | BRICK 2.0 | Δln L |
|---|---|---|---|
| 1900-2026 | 11.5 | -1200.4 | 1211.9 |
| 1900-1919 | -63.9 | -226.1 | 162.1 |
| 1920-1949 | -64.0 | -230.7 | 166.7 |
| 1950-1992 | 46.3 | -456.8 | 503.1 |
| 1993-2026 | 93.1 | -286.8 | 380.0 |

## The total (out-of-sample for BOTH — not in either likelihood; reference only)

| arm | Ladrillo L32 ln L (max) | at fit4 max-draw | BRICK 2.0 ln L (max) | at fit4 max-draw |
|---|---|---|---|---|
| obs_iid | -162.4 | -170.1 | -165.3 | -218.7 |
| ar1_prof | -162.4 | -164.4 | -165.3 | -177.0 |

## Reading, and what this does NOT show

- ln L (max over draws) is a LOWER bound on each model's true maximum for this likelihood: neither posterior was optimised for it. Both bounds are from the same draw count.
- DIC / p_V are in the CSV only: p_V = var(D)/2 is an effective parameter count only when the likelihood is the one the posterior was fitted under, which holds for neither arm here (and for BRICK 2.0 on no arm).
- In ar1_prof the profiled rho sits AT the 0.99 bound wherever the residual is a smooth bias (every BRICK 2.0 series; Ladrillo's steric and gsic): the AR(1) term then acts as a near-random-walk discrepancy that absorbs a smooth bias cheaply, so this arm's gain is a function of how much autocorrelation the noise model is allowed. See the --rho-max sensitivity files.
- Ladrillo's thermal-expansion module IS BRICK's (one alpha on the same OHC), so the steric row is a tie by construction: the two best draws produce the same residual to 3 decimals.
- Ladrillo was calibrated to these targets; BRICK 2.0 to Wong's. AIC/BIC correct for a fitted model's own optimism, not for a comparator fitted to different data. The structure test that removes that axis is a BRICK 2.0 arm recalibrated on the extended targets (note_2026-08-14_ladrillo_vs_brick20_scorecard.md).
- obs_iid treats residual years as independent and OVERSTATES the evidence; ar1_prof is the calibrator's own form and the headline.

Provenance: ic_ladrillo_vs_brick20.py | tag L32 | k_phys {'ladrillo': 42, 'brick20': 27} + 8 profiled noise in ar1_prof | N_fit 502 | inputs: ladrillo: ic_hindcast_residuals.jl | Ladrillo tag L32 | posterior parameters_subsample_brick_mengel_L32.csv NDRAW=2000 evenly thinned of 10000 | forcing ssp245harm | run 1850-2026 scored 1900-2026 reref 1995-2005 | gsic = gsic_hind + F_unch vs gsic_adj target, no delta ramp, no d2 | total = glaciers+ais+gis+te+OBSERVED lws vs dang | residual = model - obs, cm || brick20: ic_hindcast_residuals.jl | BRICK 2.0 stock MimiBRICK get_model(ssp245), Random.seed!(2026) immediately before get_model | posterior parameters_subsample_brick.csv NDRAW=10000 evenly thinned of 10000 | forcing ssp245harm | run 1850-2026 scored 1900-2026 reref 1995-2005 | gsic = gsic_sea_level vs gsic_adj target | total = ais+gsic+gis+te+OBSERVED lws vs dang | residual = model - obs, cm
