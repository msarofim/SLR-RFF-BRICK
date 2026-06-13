# AIS `ais_ocean_temperature₀` confirming sweep

Driver: `julia/sweep_ais_oceantemp.jl` (reuses `run_mimibrick_obs_driven.jl` machinery, MimiBRICK v2.0.0 (precip_log=true)).
Forcing: FaIR-mean GMST (`fair_mean_gmst.csv`) + FaIR-mean OHC (`fair_mean_ohc.csv`), the `fair_fair` combo.
Posterior: `parameters_subsample_brick.csv`, first **2000** of 10000 members. Window 1850-2024, ssprcp=ssp245. All AIS values cm rel 2000.

Targets: Frederikse 2020 AIS@1900 = **-0.64 ± 0.39** cm; IMBIE ΔAIS(1992-2017) = **0.72 ± 0.156** cm. Pass = within ±2σ. `ais_ocean_temperature₀` default = 0.72 °C.

| ocean_temp₀ (°C) | n | median AIS@1900 (cm) | median ΔAIS 1992-2017 (cm) | hist pass | modern pass | joint pass |
|---:|---:|---:|---:|---:|---:|---:|
| 0.72 | 2000 | -3.940 | 0.902 | 0.008 | 0.807 | 0.007 |
| 1.00 | 2000 | -2.121 | 0.441 | 0.143 | 0.501 | 0.021 |
| 1.25 | 2000 | -0.990 | 0.150 | 0.164 | 0.360 | 0.015 |
| 1.50 | 2000 | -0.172 | -0.081 | 0.142 | 0.285 | 0.009 |
| 1.75 | 2000 | 0.548 | -0.272 | 0.129 | 0.243 | 0.009 |
| 2.00 | 2000 | 1.103 | -0.423 | 0.125 | 0.211 | 0.009 |
| 2.50 | 2000 | 1.961 | -0.649 | 0.117 | 0.173 | 0.004 |

Frederikse AIS@1900 central target = -0.64 cm (horizontal reference in the PNG).
