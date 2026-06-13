> **SUPERSEDED / GARBAGE (2026-06-10).** Pre-fix v2.0.0 run: AIS@1900 ≈ +100 cm is the
> precip-reparameterization blocker (v1.0.1-era LINEAR posterior fed into v2.0.0's exp()).
> Canonical replacement: `ais_oceantemp_sweep_v2_precipfix_summary.md` (reproduces v1.0.1
> bit-for-bit). See memory `mimibrick-v2-0-0-is-not-a-drop-in...`.

# AIS `ais_ocean_temperature₀` confirming sweep

Driver: `julia/sweep_ais_oceantemp.jl` (reuses `run_mimibrick_obs_driven.jl` machinery, MimiBRICK v1.0.1).
Forcing: FaIR-mean GMST (`fair_mean_gmst.csv`) + FaIR-mean OHC (`fair_mean_ohc.csv`), the `fair_fair` combo.
Posterior: `parameters_subsample_brick.csv`, first **2000** of 10000 members. Window 1850-2024, rcp=RCP45. All AIS values cm rel 2000.

Targets: Frederikse 2020 AIS@1900 = **-0.64 ± 0.39** cm; IMBIE ΔAIS(1992-2017) = **0.72 ± 0.156** cm. Pass = within ±2σ. `ais_ocean_temperature₀` default = 0.72 °C.

| ocean_temp₀ (°C) | n | median AIS@1900 (cm) | median ΔAIS 1992-2017 (cm) | hist pass | modern pass | joint pass |
|---:|---:|---:|---:|---:|---:|---:|
| 0.72 | 2000 | 100.350 | -25.742 | 0.000 | 0.000 | 0.000 |
| 1.00 | 2000 | 104.145 | -26.716 | 0.000 | 0.000 | 0.000 |
| 1.25 | 2000 | 106.022 | -27.212 | 0.000 | 0.000 | 0.000 |
| 1.50 | 2000 | 107.761 | -27.599 | 0.000 | 0.000 | 0.000 |
| 1.75 | 2000 | 108.849 | -27.931 | 0.000 | 0.000 | 0.000 |
| 2.00 | 2000 | 109.568 | -28.173 | 0.000 | 0.000 | 0.000 |
| 2.50 | 2000 | 111.081 | -28.557 | 0.000 | 0.000 | 0.000 |

Frederikse AIS@1900 central target = -0.64 cm (horizontal reference in the PNG).
