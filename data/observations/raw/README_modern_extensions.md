# Modern SLR-component extension data (post-2018), acquired 2026-06-13

Reconciled multi-method products used to extend the Frederikse 2020 (1900-2018)
recalibration targets past 2018, for the BRICK-Mengel post-2020 AIS-extension
re-calibration (Marcus, 2026-06-13). Consumed by `python/prep_recalib_targets_ext.py`.

| File | Component | Source | Coverage | DOI / access |
|------|-----------|--------|----------|--------------|
| `grace_antarctica_mass.txt` | AIS | NASA JPL GRACE/GRACE-FO mascon RL06.3Mv4, Antarctic mass anomaly (Gt rel Apr 2002) | 2002.3–2026.3 | 10.5067/TEMSC-3JC634 (PO.DAAC, Earthdata login) |
| `grace_greenland_mass.txt` | GIS | same mascon solution, Greenland mass anomaly | 2002.3–2026.3 | 10.5067/TEMSC-3JC634 |
| `glambie_global_glacier_mass.csv` | GSIC | GlaMBIE 2025 (GlaMBIE Team, *Nature*) global glacier mass change, `calendar_years/0_global.csv` (annual Gt) | 2000–2023 | 10.5904/wgms-glambie-2024-07 (WGMS, open) |
| `glambie_data.zip` | — | full GlaMBIE 1.0.0 release (inputs + results) | — | as above |
| `noaa_thermosteric_w0-2000m_yearly.dat` | TE/steric | NOAA NCEI World-Ocean 0–2000 m thermosteric sea level anomaly (mm, yearly) | 2005–2025 | ncei.noaa.gov/access/global-ocean-heat-content (open) |
| `imbie_antarctica_2021_mm.csv` | AIS (xcheck) | IMBIE 2023 / Otosaka et al. *ESSD*, Antarctic cumulative mass balance (mm SLE) | 1992–2020 | 10.5285/77B64C55-… (BAS PDC, open) |
| `imbie_greenland_2021_mm.csv` | GIS (xcheck) | IMBIE 2023, Greenland cumulative mass balance (mm SLE) | 1992–2020 | 10.5285/77B64C55-… |
| `imbie_{east_antarctica,west_antarctica,antarctic_peninsula}_2021_{Gt,mm}.csv` | AIS regional | IMBIE 2023, per-region mass balance (EAIS / WAIS / APIS) | 1992–2020 | same DOI, RAMADDA entry `77b64c55-…`, OGL v3.0 |

### IMBIE Antarctic REGIONAL files (acquired 2026-08-19)

Fetched from the same DOI's RAMADDA entry
(`https://ramadda.data.bas.ac.uk/repository/entry/show?entryid=77b64c55-7166-4a06-9def-2e400398e452`),
byte-sizes verified against the catalogue listing. Full citation: Shepherd, A.,
Ivins, E., Rignot, E., Smith, B., van den Broeke, M., Velicogna, I., et al. (2021),
*Antarctic and Greenland Ice Sheet mass balance 1992-2020 for IPCC AR6* (v1.0),
UK Polar Data Centre / NERC / UKRI. Licence: Open Government Licence v3.0.

Acquired to answer whether an EAIS/WAIS split of DAIS is SCORABLE — the Antarctic
analogue of the Mouginot sector check that gated the Greenland 3-basin term.
Verdict in `python/diag_ais_region_lit_check.py`: the regions CLOSE against the
published whole sheet (1e-7), but the partition is NOT usable as shares (EAIS's
share is NEGATIVE in 3 of 4 windows and drifts 4.33x the sigma the Greenland term
uses), and as absolute rates only WAIS is distinguishable from zero (1.8-2.8 sigma
vs EAIS 0.02-0.25, APIS 0.3-0.8).

Total constraint extended with NOAA STAR altimetry GMSL (`../nasa_gmsl_annual.csv`, 1993–2024).

## Notes / conventions
- **Gt → cm SLE:** `prep_recalib_targets_ext.py` uses 362 Gt/mm (ocean-area based);
  the splice offset-matches over an overlap window, so only the post-2018 *increment*
  is affected by this factor (<1%). Mass loss (negative Gt anomaly) → positive SLE.
- **NOAA steric is 0–2000 m only** (Argo depth). Misses the deep-ocean (>2000 m,
  ~0.1 mm/yr) thermosteric term — a small post-2018 underestimate. Frederikse "Steric"
  is full-depth; the splice matches level, not the (small) deep slope.
- **GRACE/GRACE-FO gap** (~2017.5–2018.5) leaves 2017/2018 with <6 monthly samples →
  those annual means are dropped, but the fit uses Frederikse for years ≤2018 anyway.
- **IMBIE cross-check** (not fed to the fit): spliced to the same overlap, IMBIE and
  GRACE agree to <0.07 cm at 2015/2020 for both AIS and GIS.
- IMBIE 2023 ΔAIS(1992–2017) = 0.60 cm — cf. the legacy hardcoded point-term
  `IMBIE_MU = 0.72` cm in `calibrate_mcmc.jl` (point terms are dropped in the
  extended fit, see `calibrate_mcmc_ext.jl`).

## T_glac driver inputs (Option D glacier driver, acquired 2026-08-06)

| File | Purpose | Source | Coverage | DOI / access |
|------|---------|--------|----------|--------------|
| `HadCRUT.5.0.2.0.analysis.anomalies.ensemble_mean.nc` (32 MB, UNTRACKED — re-fetch from URL) | gridded T for glacier-area-weighted T_glac | Met Office HadOBS, HadCRUT5 analysis (infilled) ensemble mean, monthly 5 deg (Morice et al. 2021, doi:10.1029/2019JD032361) | 1850–2025 | https://www.metoffice.gov.uk/hadobs/hadcrut5/data/HadCRUT.5.0.2.0/analysis/HadCRUT.5.0.2.0.analysis.anomalies.ensemble_mean.nc |
| `GlacReg_2023.zip` + `GlacReg_2023/` | RGI first-order glacier-region polygons for the T_glac masks | GTN-G Glacier Regions 2023 | — | 10.5904/gtng-glacreg-2023-07 |

Consumed by `python/build_t_glac.py` → `../t_glac_hadcrut5.csv` (see its provenance sidecar).

## Dangendorf 2024 corrected Global.nc (received 2026-08-07)

| File | Purpose | Source | Coverage |
|------|---------|--------|----------|
| `dangendorf2024_KalmanSmootherHR_Global_v2.nc` | corrected global GMSL + components + SEs | S. Dangendorf, personal communication 2026-08-07 (email to Marcus, fixing the Zenodo 10621070 slot-shift) | 1900–2021 |

The ORIGINAL `dangendorf2024_KalmanSmootherHR_Global.nc` (Zenodo fetch) is
mis-written upstream: its `GMSLHR`/`GMSLHRSE` slots hold the BARYSTATIC
series/SE (verified: old GMSLHR ≡ v2 GBSLHR value-for-value) and `GBSLHR*`
are all fill values. Kept in place only because
`diag_dangendorf_vs_frederikse.py` documents the corruption; NEVER read GMSL
from it. The v2 file fixes the slots; units are METERS, incl. the SE
("the error for the reconstruction is 3 mm in 2021, not 0.3 mm. The error
given in the file is in m." — Dangendorf, 2026-08-07): GMSLHRSE(2021) =
0.00268 m = 2.68 mm.

Validation (2026-08-07): v2 `GMSLHR` matches our Fields.nc-derived
`../dangendorf2024_gmsl_annual.csv` to 0.0000 mm demeaned (constant baseline
offset 53.45 mm; corr 1.000000) — the extraction that fed
`recalib_targets_ext.csv` `dang` values is confirmed exact. NOTE the v2 SE
falsifies the "Frederikse-ensemble sd is conservative" rationale in
`prep_recalib_targets_ext.py` for 1900–2010 (true Dangendorf SE is 1.3–2×
LARGER there; SMALLER after ~2015). RESOLVED same day (Marcus 2026-08-07):
`dang_sig` = native v2 SE; `prep_recalib_targets_ext.py` updated (units
assert) and targets rebuilt — the standing likelihood regardless of the
T1–T4 structural decision.

## GlacierMIP3 (Zekollari 2025) — fetched 2026-08-07 for the T2 anchor scope correction

| File | Purpose | Source | Coverage |
|------|---------|--------|----------|
| `gmip3/lowess_fit_rel_2020_101yr_avg_steady_state_Feb12_2024.csv` (+`_per_glac_model`, `_only_global_models`, `_rel_regional_glacier_temp_ch`, 21yr after100/500yr variants) | published LOWESS quantile fits: steady-state remaining mass (% of 2020) vs warming, per RGI region + 'All' | GlacierMIP3 Zenodo archive v2, DOI 10.5281/zenodo.15046588 (concept 10.5281/zenodo.14045268); Zekollari, Schuster et al. 2025 Science, DOI 10.1126/science.adu4675 | ΔT −0.1…6.85 K |
| `gmip3/table_S1a.csv`, `table_S1b.csv`, `table_S3.csv` | published per-region committed % [likely], mm SLE variants, 2020 masses | same | +1.2…4.0 K |
| `gmip3/3_shift_summary_region_characteristicsFeb12_2024.csv` | per-region 2020 volumes (Farinotti+Hugonnet `_via_5yravg`), warming ratios, response times | same | — |
| `gmip3/climate_input_data/temp_ch_ipcc_ar6_isimip3b*.csv` | per-experiment warming levels (5 GCM × 16 period-scenarios, AR6 defn) | same | — |
| `gmip3/resp_time_shifted_for_deltaT_rgi_reg_roll_volume_21yravg.csv` | per-region/model response timescales (τ_s prior receipts) | same | — |
| `gmip3/README_data.pdf`, `gmip3/gmip3_data_example_use_cases.ipynb` | dataset documentation | same | — |
| `gmip3/GMIP3_reg_glacier_model_data/all_shifted_...repeat_last_101yrs_via_5yravg.nc` (1.47 GB, UNTRACKED — re-fetch below) | per-experiment shifted volume series, the input the paper's LOWESS fits used; needed to replicate the 'All' composite on the excl-r5 scope | same | sim yr 0–5000 |

Re-fetch recipe for the big netCDF (selective extraction from the 984 MB zip
via HTTP range requests; or download the whole zip and unzip):
`python remote_zip_extract.py "https://zenodo.org/records/15046588/files/gmip3_data_zenodo.zip" --extract "data/GMIP3_reg_glacier_model_data/all_shifted_*" <outdir>`
(script pattern: list/extract members of a remote zip with a lazy
HTTP-range file object; any equivalent works.)

Consumed by `python/t2_gmip3_scope_anchor.py` → `outputs/t2_gmip3_scope_anchor.csv`.
The paper's fit machinery is `moepy` (pip-installed into ~/climate-env
2026-08-07); the paper's own scripts are at github.com/GlacierMIP/GlacierMIP3.
