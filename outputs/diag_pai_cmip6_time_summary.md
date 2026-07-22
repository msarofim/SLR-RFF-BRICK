# PAI-vs-time diagnostic (34 CMIP6 models)

Windowed PAI1 = 41-yr trend(T_AIS)/trend(T_glob); AIS = land (sftlf>=50%) south of 60S; anomalies rel (1850, 1900); global-trend floor 0.05 K/decade.

## Validation gate (Xie et al. 2022 Table 1)
- SSP2-4.5: MMEM-series PAI1 1.129 (mean-of-ratios 1.128, model range 0.68-1.69) vs Xie 0.95 -> FAIL (tol 0.1)
- SSP5-8.5: MMEM-series PAI1 1.160 (mean-of-ratios 1.160, model range 0.84-1.57) vs Xie 1.03 -> FAIL (tol 0.1)

## Within-scenario time dependence
- SSP2-4.5: median PAI1 1.06 (early windows) -> 1.19 (late windows); within-scenario slope +0.035/decade
- SSP5-8.5: median PAI1 1.13 (early windows) -> 1.19 (late windows); within-scenario slope +0.016/decade

Models: ACCESS-CM2, ACCESS-ESM1-5, AWI-CM-1-1-MR, BCC-CSM2-MR, CAMS-CSM1-0, CESM2, CESM2-WACCM, CMCC-CM2-SR5, CMCC-ESM2, CNRM-CM6-1, CNRM-CM6-1-HR, CNRM-ESM2-1, CanESM5, CanESM5-CanOE, EC-Earth3, EC-Earth3-Veg, EC-Earth3-Veg-LR, FGOALS-g3, GFDL-CM4, GFDL-ESM4, GISS-E2-1-G, GISS-E2-1-H, HadGEM3-GC31-LL, INM-CM4-8, INM-CM5-0, IPSL-CM6A-LR, MIROC-ES2L, MIROC6, MPI-ESM1-2-HR, MPI-ESM1-2-LR, MRI-ESM2-0, NorESM2-MM, TaiESM1, UKESM1-0-LL
