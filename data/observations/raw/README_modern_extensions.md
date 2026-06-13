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
