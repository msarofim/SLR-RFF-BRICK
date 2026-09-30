# Reference metadata checks: Table 3 data sets, HadCRUT5, Wong 2017a/b (2026-09-30)

Sources: DataCite REST (api.datacite.org/dois/<doi>), Crossref REST, NASA CMR (GRACE), GMD submission page,
copernicus.bst v1.6 (Oct 2023) from Copernicus_LaTeX_Package.zip on the GMD site.

## 1. Data-set entries (all fields from the DataCite record unless noted)

1. GlaMBIE: https://doi.org/10.5904/wgms-glambie-2024-07
   DataCite: creator "GlaMBIE" (Organizational); title "Glacier Mass Balance Intercomparison Exercise (GlaMBIE)";
   publisher World Glacier Monitoring Service; year 2024; version field EMPTY.
   "Dataset 1.0.0" is from the archive's own GlaMBIE_DATASETS_INFO.md ("How to cite: GlaMBIE (2024): ... Dataset 1.0.0.
   World Glacier Monitoring Service (WGMS), Zurich"), not from DataCite.
   Entry: GlaMBIE: Glacier Mass Balance Intercomparison Exercise (GlaMBIE), Dataset 1.0.0, World Glacier Monitoring Service [data set], https://doi.org/10.5904/wgms-glambie-2024-07, 2024.
   In-text (GlaMBIE, 2024). No collision with "GlaMBIE Team, 2025" (different name string and year).
   VERIFIED (version from the provider's how-to-cite, not DataCite).

2. JPL mascons: https://doi.org/10.5067/TEMSC-3JC634
   DataCite creator is MANGLED: name "GRACE-FO, D. N. Wiese" (familyName "GRACE-FO", givenName "D. N. Wiese").
   DataCite year 2024 (registered 2024-09-10), version EMPTY, publisher NASA Physical Oceanography Distributed Active Archive Center.
   NASA CMR CollectionCitations: creators "D. N. Wiese, D.-N. Yuan, C. Boening, F. W. Landerer, M. M. Watkins", version RL06.3Mv04,
   publisher PO.DAAC, ReleaseDate 2023-01-25.
   Entry (CMR creators): Wiese, D. N., Yuan, D.-N., Boening, C., Landerer, F. W., and Watkins, M. M.: JPL GRACE and GRACE-FO Mascon Ocean, Ice, and Hydrology Equivalent Water Height CRI Filtered RL06.3Mv04, RL06.3Mv04, NASA Physical Oceanography Distributed Active Archive Center [data set], https://doi.org/10.5067/TEMSC-3JC634, 2024 (DataCite) / 2023 (CMR release date).
   In-text (Wiese et al., 2024) or 2023 -- YEAR NEEDS A DECISION. No collision.
   PARTIAL: DataCite creator unusable; creators from NASA CMR; registries disagree on year.

3. Dangendorf data: https://doi.org/10.5281/zenodo.10621070
   DataCite: name "Sönke, Dangendorf" (inverted string; familyName=Dangendorf, givenName=Sönke are correct) -> "Dangendorf, S.";
   title "Kalman Smoother Sea Level Reconstruction"; Zenodo; 2024 (issued 2024-02-05); version EMPTY; concept DOI 10.5281/zenodo.10621069.
   Entry: Dangendorf, S.: Kalman Smoother Sea Level Reconstruction, Zenodo [data set], https://doi.org/10.5281/zenodo.10621070, 2024.
   In-text (Dangendorf, 2024). No letter needed vs Dangendorf et al., 2024 (single-author vs team category). VERIFIED.

4. IGCC: https://doi.org/10.5281/zenodo.20499280
   DataCite: 16 creators, Smith first, Forster last; title "Indicators of Global Climate Change 2025"; version v2026.06.02;
   Zenodo; 2026; resourceTypeGeneral = SOFTWARE (GitHub release; IsSupplementTo github ClimateIndicator/data tree v2026.06.02).
   Entry: Smith, C., Walsh, T., Gillett, N., Hauser, M., Krummel, P., Lamb, W., Lamboll, R., Mühle, J., Palmer, M., Ribes, A., Schumacher, D., Seneviratne, S., Slangen, A., Trewin, B., von Schuckmann, K., and Forster, P.: Indicators of Global Climate Change 2025, v2026.06.02, Zenodo [data set], https://doi.org/10.5281/zenodo.20499280, 2026.
   (DataCite gives no middle initials; typed Software so Copernicus could label it [code].)
   In-text (Smith et al., 2026). No collision with Smith, 2026 / Smith et al., 2024 / Forster et al., 2026. VERIFIED.

5. GlacierMIP3 data: https://doi.org/10.5281/zenodo.15046588
   DataCite: 15 creators, Schuster first; title "Data from Glacier Model Intercomparison Project Phase 3 (GlacierMIP3)"; Zenodo; 2025
   (issued 2025-03-18); version EMPTY; IsSupplementTo 10.31223/X51T5W (preprint), concept 10.5281/zenodo.14045268.
   Entry: Schuster, L., Zekollari, H., Maussion, F., Hock, R., Marzeion, B., Rounce, D. R., Compagno, L., Fujita, K., Huss, M., James, M., Kraaijenbrink, P. D. A., Lipscomb, W. H., Minallah, S., Oberrauch, M., and Van Tricht, L.: Data from Glacier Model Intercomparison Project Phase 3 (GlacierMIP3), Zenodo [data set], https://doi.org/10.5281/zenodo.15046588, 2025.
   In-text (Schuster et al., 2025). No collision with Zekollari et al., 2025. VERIFIED.

6. GTN-G regions: https://doi.org/10.5904/gtng-glacreg-2023-07
   DataCite: creator "World Glacier Monitoring Service (WGMS)" (Organizational); title "GTN-G Glacier Regions (GlacReg)";
   publisher Global Terrestrial Network for Glaciers (GTN-G); 2023 (available 2023-07-07); version EMPTY.
   Entry: WGMS: GTN-G Glacier Regions (GlacReg), Global Terrestrial Network for Glaciers (GTN-G) [data set], https://doi.org/10.5904/gtng-glacreg-2023-07, 2023.
   In-text (WGMS, 2023) [or spelled out]. No collision. VERIFIED.

## 2. HadCRUT5
File data/observations/raw/HadCRUT.5.0.2.0.analysis.anomalies.ensemble_mean.nc (32.5 MB, untracked).
NetCDF attrs: version "HadCRUT.5.0.2.0"; source CRUTEM.5.0.2.0 + HadSST.4.0.1.0; history "Data set built at: 2025-04-30T17:33:58";
2102 monthly steps, 1850-01 to 2025-02. Analysis (statistically infilled), ensemble mean, monthly 5 deg.
URL (README_modern_extensions.md:57): https://www.metoffice.gov.uk/hadobs/hadcrut5/data/HadCRUT.5.0.2.0/analysis/HadCRUT.5.0.2.0.analysis.anomalies.ensemble_mean.nc
Access date not recorded explicitly; file mtime 2026-08-06 13:43, first used in commit 597b7e1 (2026-08-06).
Consumers: build_t_glac.py:46 (per-RGI-region glacier-area-weighted series -> t_glac_regions_hadcrut5.csv, global
gmst_hadcrut5_C for amp fits); build_t_gis.py:72 (headline zone south 59-70 N -> t_gis_zones.csv). Annual means need 12 months -> ends 2024.
DOI: none found in DataCite for any HadCRUT5 version from Met Office / CEDA (10.5285); only third-party Zenodo derivatives. Cite Morice et al. (2021) + URL.

## 3. Wong 2017a/b
GMD rule (submission.html): team papers "first chronologically ..., then alphabetically within each year according to the
second (third, etc.) author". copernicus.bst sort.format.names: sort key = names in order, year inserted after author 2
for 3+ authors; so compare 3rd author: Keller < Ruckert.
2017a = Wong, Bakker, Keller, Clim. Change 144, 347-364 (Crossref authors: Wong, Bakker, Keller).
2017b = Wong, Bakker, Ruckert, Applegate, Slangen, Keller, GMD 10, 2741-2760.
In-text occurrences (all are the GMD paper -> 2017b): line 112, line 220, line 288.
