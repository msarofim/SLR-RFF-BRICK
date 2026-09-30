# FaIR forcing in this directory: which calibration

**Standard (Marcus 2026-09-30): every paper calculation and every future calculation uses
FaIR 2.2.4 (calib 1.6.0).** The migration was made 2026-08-28, commits `839a176` and
`632f330`, then extended by `9ceaa82`, `6cc34b6`, `9b03ab9`, `26f9f33` and `296f9e6`.

## Calib 1.6.0: use these

- `fair_mean_{gmst,ohc}_ssp{126,245,585}.csv`
- `fair_mean_{gmst,ohc}_ssp245harm.csv`: the calibration and hindcast driver
- `*_nomarker.csv`, `*_ssp534over*.csv`, `fair_mean_*_vv*.csv`
- `fair_cube_*_raw.csv` / `*_spliced.csv`, `fair_pctile_gmst_*.csv`
- `fair_coulon_*_v160*.csv`

## Pre-migration: renamed so nothing reads them by accident

| file | what it is |
|---|---|
| `fair_mean_{gmst,ohc}_pre160.csv` | Formerly `fair_mean_{gmst,ohc}.csv` (2026-05-25). It matches none of the 1.4.5 SSP files (2100 = 3.00 K), so its exact vintage is unknown, but it is pre-1.6.0. |
| `fair_mean_{gmst,ohc}_ssp{119,370,460}_pre160.csv` | Formerly `…_ssp{119,370,460}.csv` (2026-06-13); pre-1.6.0. **No calib 1.6.0 version exists yet.** |
| `fair_mean_{gmst,ohc}_v145.csv` | Already labelled; unchanged. |

The rename was made 2026-09-30. Scripts that still ask for the old names now fail with a
missing-file error. That is deliberate: a missing file cannot be silently mistaken for
1.6.0 forcing.

None of these files is on the paper pipeline (audited 2026-09-30). To use SSP1-1.9,
SSP3-7.0 or SSP4-6.0, generate them on 1.6.0 with the ported v160 generators
(FaIRtoFrEDI `main`, commit `802905f`) rather than pointing a script at a `_pre160` file.

Still-reading scripts found by the 09-30 audit, all off the paper pipeline:
- **julia:**
  - `posterior_predictive.jl`, `posterior_predictive_ext.jl`
  - `calibrate_mcmc.jl`, `calibrate_full_joint.jl`, `recalibrate_central.jl`
  - `fit_greenland_only.jl`, `diag_brick_lws_extract.jl`
  - `project_ssps_2100{,_ensemble,_mengel}.jl`, `project_ssps_gsic_2300{,_mengel}.jl`
  - `project_ssps_components_oldbrick.jl`
- **python:**
  - `plot_recalib_components.py`, `plot_ssps_gsic_wr_vs_mengel.py`
  - `calibrate_mengel_glacier.py`, `glacier_2tau_validate.py`
  - `gsic_stabilization_demo.py`, `gis_offline_cell.py` (`load_gmst(tag=None)`)
  - `diag_te_rate_bars_and_seam.py`
  - `scripts/substack/gouretski_vs_cheng_ohc.py`
