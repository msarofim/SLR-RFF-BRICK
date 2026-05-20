# `data/` — input data for the SLR-RFF-BRICK pipeline

## What's tracked in git

### `data/observations/`
Small (a few MB each) observed reference series, used by the model–obs
overlay figures and for the Wong (2026) importance weighting against
observed historical GMSL.

| File | What it is |
|---|---|
| `dangendorf_2024_gmsl.csv` | Dangendorf et al. 2024 tide-gauge reconstruction of global mean sea level, 1900–2018 (mm rel a centred 20th-century baseline; rebaselined to year 2000 in scripts). [Zenodo 10.5281/zenodo.10621070](https://doi.org/10.5281/zenodo.10621070) |
| `nasa_gmsl_annual.csv` | NOAA STAR satellite altimetry, 1993–2024 (mm rel 1993). Annual means; downloaded with `python/download_obs.py`. |
| `berkeley_earth_annual.csv` | Berkeley Earth annual surface temperature anomaly, native rel 1951–1980 baseline (converted to rel 1986–2005 in scripts). |
| `igcc2024_gmst_4dataset_mean.csv` | IGCC 2024 4-dataset consensus (HadCRUT5 + Berkeley Earth + GISTEMP + NOAAGlobalTemp). Trewin's raw mean. The canonical GMST anchor for the project (2015–2024 mean rel PI = +1.254 °C). |
| `igcc2024_gmst_with_uncertainty.csv` | Walsh-fitted IGCC GMST timeseries with p05 / total_p50 / p95. **Note:** we use this for the cross-dataset uncertainty *band width* only; the central line comes from `igcc2024_gmst_4dataset_mean.csv` because Walsh's `total_p50` is an attribution-method regression fit that smooths over the 2024 ENSO peak. |

`python/download_obs.py` can refresh NOAA STAR / Berkeley Earth from
canonical sources.

## What's external (not tracked, fetch separately)

### `data/RFF-SP-emissions/` and `data/RFF-SP-socioeconomics/`
The Resources for the Future Social Cost of CO2 (RFF-SP) probabilistic
ensemble — 10,000 internally-consistent socio-economic + emissions
trajectories. **Required for Tier 3 reproducibility only** (rerunning FaIR
from scratch).

- Citation: Rennert et al. 2022, *Nature*. doi:[10.1038/s41586-022-05224-9](https://doi.org/10.1038/s41586-022-05224-9)
- Download: [Zenodo 10.5281/zenodo.6016583](https://doi.org/10.5281/zenodo.6016583) (`rffsps_v5.7z`, ~1.36 GB)
- Extract to `data/RFF-SP-emissions/` and `data/RFF-SP-socioeconomics/`
  (or set RFF_SP_DIR env var to wherever you put it).

### `data/MimiBRICK/`
MimiBRICK release artifacts — calibrated posterior and projections.
**Required for Tier 2 reproducibility** (running BRICK with the project's
metadata).

- The 10,000-member posterior subsample (`parameters_subsample_brick.csv`)
  drives the Wong importance weighting and conditional BRICK sampling.
- Citation: Wong et al., MimiBRICK package. [github.com/raddleverse/MimiBRICK.jl](https://github.com/raddleverse/MimiBRICK.jl)
- Download: From the MimiBRICK release page, place
  `parameters_subsample_brick.csv` at `data/MimiBRICK/parameters_subsample_brick.csv`.

The first time you run the Julia BRICK driver
(`julia/run_mimibrick_paired_explicit.jl`), it will fetch the MimiBRICK
package via Julia's package manager (see `julia/Project.toml`).
