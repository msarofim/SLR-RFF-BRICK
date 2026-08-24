# Antarctic amplification, SECANT (level) ratio (34 CMIP6 models)

R = [smooth30(T_AIS) - T_AIS,PI] / [smooth30(T_glob) - T_glob,PI]; PI = (1850, 1900); centered 30-yr mean; plotted post-1950; land-frame AIS. This is a LEVEL ratio (= BRICK `a`), NOT Xie's trend ratio.

## Within-scenario rise
- SSP2-4.5: median secant 1.54 (1950-75) -> 1.07 (2065-90)
- SSP5-8.5: median secant 1.54 (1950-75) -> 1.11 (2065-90)

## Matched-warming secant ratio (median over models)
|    dT |   ssp245 |   ssp585 |
|------:|---------:|---------:|
| 1.500 |    1.161 |    1.129 |
| 2.000 |    1.124 |    1.115 |
| 2.500 |    1.097 |    1.086 |
| 3.000 |    1.073 |    1.101 |
| 3.500 |    1.064 |    1.106 |
| 4.000 |  nan     |    1.093 |

Models: ACCESS-CM2, ACCESS-ESM1-5, AWI-CM-1-1-MR, BCC-CSM2-MR, CAMS-CSM1-0, CESM2, CESM2-WACCM, CMCC-CM2-SR5, CMCC-ESM2, CNRM-CM6-1, CNRM-CM6-1-HR, CNRM-ESM2-1, CanESM5, CanESM5-CanOE, EC-Earth3, EC-Earth3-Veg, EC-Earth3-Veg-LR, FGOALS-g3, GFDL-CM4, GFDL-ESM4, GISS-E2-1-G, GISS-E2-1-H, HadGEM3-GC31-LL, INM-CM4-8, INM-CM5-0, IPSL-CM6A-LR, MIROC-ES2L, MIROC6, MPI-ESM1-2-HR, MPI-ESM1-2-LR, MRI-ESM2-0, NorESM2-MM, TaiESM1, UKESM1-0-LL
