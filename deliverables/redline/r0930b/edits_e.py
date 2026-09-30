"""09-30b edit set E: Table 3 DOIs -> reference entries, Table 3 style, HadCRUT5 row, Wong 2017a/b.
Metadata: DataCite/Crossref, checked 2026-09-30 (scratchpad v0930b/refs_datasets.md)."""
import sys
sys.path.insert(0, "/private/tmp/claude-501/-Users-MarcusMarcus-Documents-2026-CodeProjects-FaIRtoFrEDI/e88c7db1-5ed3-4ee0-bbf2-08bb6c77ecb6/scratchpad/v0930b")
from trackedit import Doc
d = Doc(sys.argv[1] + "/word/document.xml")

# ---- Table 3: inline DOIs -> citations; Copernicus citation style in the label column
d.replace("Dataset 1.0.0, DOI 10.5904/wgms-glambie-2024-07; paper 10.1038/s41586-024-08545-z¹³",
          "Dataset 1.0.0 (GlaMBIE, 2024); paper GlaMBIE Team (2025)¹³", "DOI -> reference list")
d.replace("Release RL06.3Mv04 CRI, DOI 10.5067/TEMSC-3JC634¹⁴", "Release RL06.3Mv04 CRI (Wiese et al., 2024)¹⁴", "DOI -> reference list")
d.replace("Mouginot 2019 Greenland sector shares", "Mouginot et al. (2019) Greenland sector shares", "style")
d.replace("Rignot 2019 Antarctic SMB", "Rignot et al. (2019) Antarctic SMB", "style")
d.replace("Farinotti 2019 glacier inventory", "Farinotti et al. (2019) glacier inventory", "style")
d.replace(" 12:168, reconciled per Hock 2023¹⁸", " 12:168, reconciled per Hock et al. (2023)¹⁸", "style")
d.replace("Leclercq et al. 2011 19th-century glacier change", "Leclercq et al. (2011) 19th-century glacier change", "style")
d.replace(" 32:519, DOI 10.1007/s10712-011-9121-7", " 32:519", "DOI is in the reference list")
d.replace("GlacierMIP3 equilibrium experiments (Zekollari et al. 2025)", "GlacierMIP3 equilibrium experiments (Zekollari et al., 2025)", "style")
d.replace(", DOI 10.1126/science.adu4675; data 10.5281/zenodo.15046588", " 388:979; data Schuster et al. (2025)",
          "paper DOI is in the reference list; data set -> reference list")
d.replace(", shipped with MimiBRICK²⁰", " (Wong et al., 2017a), shipped with MimiBRICK²⁰",
          "BRICK fastdy branch DAISfastdyn_calib_driver.R writes this filename; 4 x 200,000 = 800,000 members")
d.replace(" Dangendorf 2024 GMSL", " Dangendorf et al. (2024) GMSL", "style")
d.replace("Zenodo 10.5281/zenodo.10621070²¹", "Kalman-smoother reconstruction (Dangendorf, 2024)²¹", "DOI -> reference list")
d.replace("Tag v2026.06.02, data DOI 10.5281/zenodo.20499280; Forster et al. 2026, 10.5194/essd-18-3889-2026²²",
          "Tag v2026.06.02 (Smith et al., 2026); Forster et al. (2026)²²", "DOIs -> reference list")
# footnote 18: GTN-G regions DOI -> reference (the DOI is its own styled run)
d.replace("region polygons GTN-G Glacier Regions 2023, DOI ", "region polygons GTN-G Glacier Regions (WGMS, 2023)", "DOI -> reference list")
d.replace("10.5904/gtng-glacreg-2023-07", "", "DOI -> reference list")
# HadCRUT5 row (Marcus 09-30), after the GlacierMIP3 row, before the CMIP6 amplification row
d.insert_row("committed-loss fraction at 1.2–3.0 K",
             ["HadCRUT5 surface temperature (Morice et al., 2021)",
              "HadCRUT.5.0.2.0 analysis (infilled) ensemble mean, monthly on a 5° grid; no DOI is published",
              "The observed regional temperature drivers to 2024 (area-weighted over each glacier block; southern "
              "Greenland, 59–70° N) and each driver's regional/global amplification fit."],
             "build_t_glac.py:46, build_t_gis.py:72; data/observations/raw/HadCRUT.5.0.2.0.analysis.anomalies.ensemble_mean.nc")

# ---- Wong et al. 2017a (Wong, Bakker, Keller) / 2017b (BRICK v0.2): GMD rule, 3rd author Keller < Ruckert
d.revise_own_ins("(Wong et al., 2017, 2022)", "2017,", "2017b,", "BRICK v0.2 is 2017b")
d.replace("Following Wong et al. (2017) we compare", "Following Wong et al. (2017b) we compare", "BRICK v0.2 (AIC/BIC section)")
d.replace("in the layout of Wong et al. (2017), Appendix A", "in the layout of Wong et al. (2017b), Appendix A", "BRICK v0.2 Appendix A")
d.replace("https://doi.org/10.5194/gmd-10-2741-2017, 2017.", "https://doi.org/10.5194/gmd-10-2741-2017, 2017b.", "a/b")

REFS = [  # (anchor paragraph, before?, entry)
 ("Wong, T. E., Bakker, A. M. R., Ruckert", True,
  "Wong, T. E., Bakker, A. M. R., and Keller, K.: Impacts of Antarctic fast dynamics on sea-level projections and coastal flood defense, Clim. Change, 144, 347–364, https://doi.org/10.1007/s10584-017-2039-4, 2017a."),
 ("GlaMBIE Team: Community estimate", True,
  "GlaMBIE: Glacier Mass Balance Intercomparison Exercise (GlaMBIE), Dataset 1.0.0, World Glacier Monitoring Service [data set], https://doi.org/10.5904/wgms-glambie-2024-07, 2024."),
 ("Wigley, T. M. L. and Raper", True,
  "Wiese, D. N., Yuan, D.-N., Boening, C., Landerer, F. W., and Watkins, M. M.: JPL GRACE and GRACE-FO Mascon Ocean, Ice, and Hydrology Equivalent Water Height CRI Filtered RL06.3Mv04, NASA Physical Oceanography Distributed Active Archive Center [data set], https://doi.org/10.5067/TEMSC-3JC634, 2024."),
 ("Dangendorf, S., Sun, Q., Wahl", True,
  "Dangendorf, S.: Kalman Smoother Sea Level Reconstruction, Zenodo [data set], https://doi.org/10.5281/zenodo.10621070, 2024."),
 ("Smith, C., Cummins, D. P., Fredriksen", False,
  "Smith, C., Walsh, T., Gillett, N., Hauser, M., Krummel, P., Lamb, W., Lamboll, R., Mühle, J., Palmer, M., Ribes, A., Schumacher, D., Seneviratne, S., Slangen, A., Trewin, B., von Schuckmann, K., and Forster, P.: Indicators of Global Climate Change 2025, v2026.06.02, Zenodo [data set], https://doi.org/10.5281/zenodo.20499280, 2026."),
 ("Schwarz, G.: Estimating the dimension", True,
  "Schuster, L., Zekollari, H., Maussion, F., Hock, R., Marzeion, B., Rounce, D. R., Compagno, L., Fujita, K., Huss, M., James, M., Kraaijenbrink, P. D. A., Lipscomb, W. H., Minallah, S., Oberrauch, M., and Van Tricht, L.: Data from Glacier Model Intercomparison Project Phase 3 (GlacierMIP3), Zenodo [data set], https://doi.org/10.5281/zenodo.15046588, 2025."),
]
for anchor, before, text in REFS:
    d.insert_para(anchor, text, before=before, why="reference added; DataCite/Crossref-verified 2026-09-30")
# WGMS sorts after Vihola and before Wiese ('wg' < 'wi'): insert before the Wiese entry just added is not
# possible (tracked run); anchor on Vihola instead.
d.insert_para("Vihola, M.: Robust adaptive Metropolis", 
  "WGMS: GTN-G Glacier Regions (GlacReg), Global Terrestrial Network for Glaciers (GTN-G) [data set], https://doi.org/10.5904/gtng-glacreg-2023-07, 2023.",
  before=False, why="reference added; DataCite-verified 2026-09-30")
d.save()
for o, n, w in d.log: print(f"- {o[:55]!r} -> {n[:55]!r}")
print(len(d.log), "edits")
