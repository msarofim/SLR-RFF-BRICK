# Model/module references for the Ladrillo GMD manuscript (compiled 2026-09-30)

Sources checked: Crossref API (`api.crossref.org/works/<doi>`) for every journal DOI; DataCite + Zenodo API for software;
Kopp et al. (2023) full text (gmd-16-7461-2023.pdf) + its Crossref reference list; SLEIP preprint
(egusphere-2026-3874) text + reference list; MimiBRICK JOSS paper (joss.04556).
Status key: VERIFIED = every field matches Crossref/DataCite. PARTIAL = what is not machine-verified is named.
Already in accepted.txt, so NOT repeated: Kopp 2023, Nauels 2017 (GMD), 2025 (NCC), 2026 (SLEIP), Wong 2017 (BRICK v0.2), Wong 2022 (JOSS),
Goelzer 2020, Greve & Chambers 2022, Zekollari 2025, Mengel 2016.

---------------------------------------------------------------------------------------------------
## A. FACTS modules (citations as Kopp et al. 2023 uses them)

### LARMIP (larmip/AIS) — Kopp 2023 §2.3.2 and SLEIP §3.2 both cite Levermann et al. (2020)
Levermann, A., Winkelmann, R., Albrecht, T., Goelzer, H., Golledge, N. R., Greve, R., Huybrechts, P., Jordan, J., Leguy, G., Martin, D., Morlighem, M., Pattyn, F., Pollard, D., Quiquet, A., Rodehacke, C., Seroussi, H., Sutter, J., Zhang, T., Van Breedam, J., Calov, R., DeConto, R., Dumas, C., Garbe, J., Gudmundsson, G. H., Hoffman, M. J., Humbert, A., Kleiner, T., Lipscomb, W. H., Meinshausen, M., Ng, E., Nowicki, S. M. J., Perego, M., Price, S. F., Saito, F., Schlegel, N.-J., Sun, S., and van de Wal, R. S. W.: Projecting Antarctica's contribution to future sea level rise from basal ice shelf melt using linear response functions of 16 ice sheet models (LARMIP-2), Earth Syst. Dynam., 11, 35–76, https://doi.org/10.5194/esd-11-35-2020, 2020.
VERIFIED (37 authors).

### DeConto (deconto21/AIS) — Kopp 2023 and SLEIP cite DeConto et al. (2021)
DeConto, R. M., Pollard, D., Alley, R. B., Velicogna, I., Gasson, E., Gomez, N., Sadai, S., Condron, A., Gilford, D. M., Ashe, E. L., Kopp, R. E., Li, D., and Dutton, A.: The Paris Climate Agreement and future sea-level rise from Antarctica, Nature, 593, 83–89, https://doi.org/10.1038/s41586-021-03427-0, 2021.
VERIFIED. (Kopp 2023's own list misspells several authors and gives 83–88; Crossref is used here.)

### Bamber (bamber19/icesheets) — Kopp 2023 and SLEIP cite Bamber et al. (2019)
Bamber, J. L., Oppenheimer, M., Kopp, R. E., Aspinall, W. P., and Cooke, R. M.: Ice sheet contributions to future sea-level rise from structured expert judgment, P. Natl. Acad. Sci. USA, 116, 11195–11200, https://doi.org/10.1073/pnas.1817205116, 2019.
VERIFIED. (Crossref title spells "judgment".)

### AR5 (ipccar5/icesheets, ipccar5/glaciers) — Church et al. (2013)
Church, J. A., Clark, P. U., Cazenave, A., Gregory, J. M., Jevrejeva, S., Levermann, A., Merrifield, M. A., Milne, G. A., Nerem, R. S., Nunn, P. D., Payne, A. J., Pfeffer, W. T., Stammer, D., and Unnikrishnan, A. S.: Sea Level Change, in: Climate Change 2013: The Physical Science Basis. Contribution of Working Group I to the Fifth Assessment Report of the Intergovernmental Panel on Climate Change, edited by: Stocker, T. F., Qin, D., Plattner, G.-K., Tignor, M., Allen, S. K., Boschung, J., Nauels, A., Xia, Y., Bex, V., and Midgley, P. M., Cambridge University Press, Cambridge, UK and New York, NY, USA, 1137–1216, https://doi.org/10.1017/CBO9781107415324.026, 2013.
PARTIAL: DOI, title and pages 1137–1216 are VERIFIED by Crossref. Crossref's chapter record has no authors or editors. The author and editor lists are taken from the reference lists of Kopp 2023 and SLEIP, which agree with each other. Crossref's issued date is 2014-03-24 (the CUP online date); the report year is 2013.
Note: Kopp 2023 cites the AR5 ice-sheet and glacier METHODS to "Church et al., 2013b", the Chapter 13 Supplementary Material. That has no DOI; Kopp gives a URL: https://www.ipcc.ch/site/assets/uploads/2018/07/WGI_AR5.Chap_.13_SM.1.16.14.pdf. If you want to cite the method exactly as FACTS does, add it as a second entry:
Church, J. A., [same 14 authors]: Sea Level Change Supplementary Material, in: Climate Change 2013: The Physical Science Basis. [same book/editors], https://www.ipcc.ch/site/assets/uploads/2018/07/WGI_AR5.Chap_.13_SM.1.16.14.pdf, 2013.  (NOT machine-verifiable; no DOI.)

⚠ Table 2 footnote ⁸ ("Cumulative-melt cap from AR5 Table 4.2") refers to AR5 WG1 **Chapter 4** (Observations: Cryosphere; Vaughan et al.), not Chapter 13. Crossref confirms https://doi.org/10.1017/CBO9781107415324.012, pp. 317–382. The authors are not in Crossref, so NO entry is given here. Get the author list from the chapter PDF.

### emulandice (emulandice/GrIS, /AIS, /glaciers) — Kopp 2023 cites Edwards et al. (2021)
Edwards, T. L., Nowicki, S., Marzeion, B., Hock, R., Goelzer, H., Seroussi, H., Jourdain, N. C., Slater, D. A., Turner, F. E., Smith, C. J., McKenna, C. M., Simon, E., Abe-Ouchi, A., Gregory, J. M., Larour, E., Lipscomb, W. H., Payne, A. J., Shepherd, A., Agosta, C., Alexander, P., Albrecht, T., Anderson, B., Asay-Davis, X., Aschwanden, A., Barthel, A., Bliss, A., Calov, R., Chambers, C., Champollion, N., Choi, Y., Cullather, R., Cuzzone, J., Dumas, C., Felikson, D., Fettweis, X., Fujita, K., Galton-Fenzi, B. K., Gladstone, R., Golledge, N. R., Greve, R., Hattermann, T., Hoffman, M. J., Humbert, A., Huss, M., Huybrechts, P., Immerzeel, W., Kleiner, T., Kraaijenbrink, P., Le clec'h, S., Lee, V., Leguy, G. R., Little, C. M., Lowry, D. P., Malles, J.-H., Martin, D. F., Maussion, F., Morlighem, M., O'Neill, J. F., Nias, I., Pattyn, F., Pelle, T., Price, S. F., Quiquet, A., Radić, V., Reese, R., Rounce, D. R., Rückamp, M., Sakai, A., Shafer, C., Schlegel, N.-J., Shannon, S., Smith, R. S., Straneo, F., Sun, S., Tarasov, L., Trusel, L. D., Van Breedam, J., van de Wal, R., van den Broeke, M., Winkelmann, R., Zekollari, H., Zhao, C., Zhang, T., and Zwinger, T.: Projected land ice contributions to twenty-first-century sea level rise, Nature, 593, 74–82, https://doi.org/10.1038/s41586-021-03302-y, 2021.
VERIFIED (84 authors). Note that SLEIP does NOT cite Edwards 2021 anywhere; the citation comes from Kopp 2023.

### FittedISMIP (FittedISMIP/GrIS) — Kopp 2023 (p. 7466): "Details are provided by Fox-Kemper et al. (2021b)", i.e. the AR6 WG1 Ch. 9 SUPPLEMENTARY MATERIAL
Fox-Kemper, B., Hewitt, H. T., Xiao, C., Aðalgeirsdóttir, G., Drijfhout, S. S., Edwards, T. L., Golledge, N. R., Hemer, M., Kopp, R. E., Krinner, G., Mix, A., Notz, D., Nowicki, S., Nurhati, I. S., Ruiz, L., Sallée, J.-B., Slangen, A. B. A., and Yu, Y.: Ocean, Cryosphere and Sea Level Change, in: Climate Change 2021: The Physical Science Basis. Contribution of Working Group I to the Sixth Assessment Report of the Intergovernmental Panel on Climate Change, edited by: Masson-Delmotte, V., Zhai, P., Pirani, A., Connors, S. L., Péan, C., Berger, S., Caud, N., Chen, Y., Goldfarb, L., Gomis, M. I., Huang, M., Leitzell, K., Lonnoy, E., Matthews, J. B. R., Maycock, T. K., Waterfield, T., Yelekçi, O., Yu, R., and Zhou, B., Cambridge University Press, Cambridge, UK and New York, NY, USA, 1211–1362, https://doi.org/10.1017/9781009157896.011, 2021.
PARTIAL: DOI, title and pages 1211–1362 are VERIFIED by Crossref. Crossref has no authors or editors; those lists are from the Kopp 2023 reference list. Crossref's issued date is 2023-07-06 (the CUP print date); the report year is 2021.
Kopp's "2021b" is the Supplementary Material, cited with the SAME chapter DOI: "Ocean, Cryosphere, and Sea Level Change Supplementary Material, in: [same book]". Citing the chapter (above) is the defensible choice because it has a DOI.
⚠ SLEIP's entry for this chapter has a corrupted DOI ("…896.011.1212"). Do not copy it.

---------------------------------------------------------------------------------------------------
## B. GlacierMIP2 and ISMIP6-Antarctica

### GlacierMIP2 — Kopp 2023, SLEIP (ProFSea §3.6) and FACTS all cite Marzeion et al. (2020)
Marzeion, B., Hock, R., Anderson, B., Bliss, A., Champollion, N., Fujita, K., Huss, M., Immerzeel, W. W., Kraaijenbrink, P., Malles, J.-H., Maussion, F., Radić, V., Rounce, D. R., Sakai, A., Shannon, S., van de Wal, R., and Zekollari, H.: Partitioning the uncertainty of ensemble projections of global glacier mass change, Earth's Future, 8, e2019EF001470, https://doi.org/10.1029/2019EF001470, 2020.
VERIFIED. Crossref gives "Malles, J."; Kopp and SLEIP both give "Malles, J.-H.", which is used here.
Optional, the GlacierMIP protocol that Kopp cites next to it:
Hock, R., Bliss, A., Marzeion, B., Giesen, R. H., Hirabayashi, Y., Huss, M., Radić, V., and Slangen, A. B. A.: GlacierMIP – A model intercomparison of global-scale glacier mass-balance models and projections, J. Glaciol., 65, 453–467, https://doi.org/10.1017/jog.2019.22, 2019.  VERIFIED.

### ISMIP6 Antarctica — Seroussi et al. (2020)
Seroussi, H., Nowicki, S., Payne, A. J., Goelzer, H., Lipscomb, W. H., Abe-Ouchi, A., Agosta, C., Albrecht, T., Asay-Davis, X., Barthel, A., Calov, R., Cullather, R., Dumas, C., Galton-Fenzi, B. K., Gladstone, R., Golledge, N. R., Gregory, J. M., Greve, R., Hattermann, T., Hoffman, M. J., Humbert, A., Huybrechts, P., Jourdain, N. C., Kleiner, T., Larour, E., Leguy, G. R., Lowry, D. P., Little, C. M., Morlighem, M., Pattyn, F., Pelle, T., Price, S. F., Quiquet, A., Reese, R., Schlegel, N.-J., Shepherd, A., Simon, E., Smith, R. S., Straneo, F., Sun, S., Trusel, L. D., Van Breedam, J., van de Wal, R. S. W., Winkelmann, R., Zhao, C., Zhang, T., and Zwinger, T.: ISMIP6 Antarctica: a multi-model ensemble of the Antarctic ice sheet evolution over the 21st century, The Cryosphere, 14, 3033–3070, https://doi.org/10.5194/tc-14-3033-2020, 2020.
VERIFIED (47 authors).
ProFSea's Antarctic module (SLEIP §3.6) is calibrated to the ISMIP6 **23rd-century** ensemble, so if Table 1 footnote ²'s "ISMIP6" is also meant to cover ProFSea, add:
Seroussi, H., Pelle, T., Lipscomb, W. H., Abe-Ouchi, A., Albrecht, T., Alvarez-Solas, J., Asay-Davis, X., Barre, J., Berends, C. J., Bernales, J., Blasco, J., Caillet, J., Chandler, D. M., Coulon, V., Cullather, R., Dumas, C., Galton-Fenzi, B. K., Garbe, J., Gillet-Chaulet, F., Gladstone, R., Goelzer, H., Golledge, N., Greve, R., Gudmundsson, G. H., Han, H. K., Hillebrand, T. R., Hoffman, M. J., Huybrechts, P., Jourdain, N. C., Klose, A. K., Langebroek, P. M., Leguy, G. R., Lowry, D. P., Mathiot, P., Montoya, M., Morlighem, M., Nowicki, S., Pattyn, F., Payne, A. J., Quiquet, A., Reese, R., Robinson, A., Saraste, L., Simon, E. G., Sun, S., Twarog, J. P., Trusel, L. D., Urruty, B., Van Breedam, J., van de Wal, R. S. W., Wang, Y., Zhao, C., and Zwinger, T.: Evolution of the Antarctic Ice Sheet over the next three centuries from an ISMIP6 model ensemble, Earth's Future, 12, e2024EF004561, https://doi.org/10.1029/2024EF004561, 2024.
VERIFIED (53 authors).
Optional, the ISMIP6 protocol that Kopp cites for emulandice: Nowicki et al. (2016), GMD 9, 4521–4545, doi:10.5194/gmd-9-4521-2016, and Nowicki et al. (2020), TC 14, 2331–2368, doi:10.5194/tc-14-2331-2020. Both DOIs resolve in Crossref; full entries are not written out here.

---------------------------------------------------------------------------------------------------
## C. PISM

**SLEIP cites no PISM model paper.** PISM appears in it once (§3.4, MAGICC-SLR): the Antarctic SMB component "has been calibrated against Golledge et al. (2019) based on the PISM ice-sheet model". Kopp 2023 does not mention PISM at all. So the citation SLEIP uses for the PISM runs in Table 1 footnote ² is:
Golledge, N. R., Keller, E. D., Gomez, N., Naughten, K. A., Bernales, J., Trusel, L. D., and Edwards, T. L.: Global environmental consequences of twenty-first-century ice-sheet melt, Nature, 566, 65–72, https://doi.org/10.1038/s41586-019-0889-9, 2019.
VERIFIED.
If you also want the model itself cited (neither SLEIP nor FACTS does this):
Bueler, E. and Brown, J.: Shallow shelf approximation as a "sliding law" in a thermomechanically coupled ice sheet model, J. Geophys. Res., 114, F03008, https://doi.org/10.1029/2008JF001179, 2009.
PARTIAL: Crossref and OpenAlex confirm volume 114 and issue F3, but neither gives the article number. F03008 is my recollection and is NOT verified; check the AGU page.
Winkelmann, R., Martin, M. A., Haseloff, M., Albrecht, T., Bueler, E., Khroulev, C., and Levermann, A.: The Potsdam Parallel Ice Sheet Model (PISM-PIK) – Part 1: Model description, The Cryosphere, 5, 715–726, https://doi.org/10.5194/tc-5-715-2011, 2011.  VERIFIED.
Related: MAGICC-SLR's Antarctic SID is calibrated to Edwards et al. (2019), Nature 566, 58–64, doi:10.1038/s41586-019-0901-4 (VERIFIED). The "DeConto" in footnote ² may therefore also stand for MAGICC's DeConto & Pollard (2016)/Edwards (2019) calibration, not only FACTS's deconto21.

---------------------------------------------------------------------------------------------------
## D. Mimi

- The MimiBRICK JOSS paper cites Mimi ONLY by URL (https://www.mimiframework.org/). It has no reference-list entry for Mimi.
- SLEIP cites it as "Anthoff, D. and others: Mimi: An Integrated Assessment Modeling Framework, 2025." That entry has no DOI or URL and is not usable in GMD.
- mimiframework.org and the Mimi.jl README give no "how to cite" guidance, and there is no Mimi paper in Crossref.
- Zenodo concept DOI (all versions): 10.5281/zenodo.4321855. The last archived version is **v1.5.1 (2022-11-28, doi:10.5281/zenodo.7370071)**; Zenodo has 15 versions, v1.1.1 to v1.5.1.
- **There is NO DOI for v1.6.** GitHub releases show v1.6.0 on 2026-04-03 and v1.7.0/v1.7.1 on 2026-09-18/19. The local depot has Mimi 1.6.0 (~/.julia/packages/Mimi/ynT7j).
Best available software entry (VERIFIED against DataCite; 18 creators exactly as DataCite lists them):
Rennels, L., Anthoff, D., Kingdon, C., Plevin, R., Balaji, G., Werwath, S., Rising, J., Gautam, A., Wingenroth, J., Celles, S., Procida, D., Saba, E., De La Guardia, F. H., Ekre, F., Delgado, M., Piibeleht, M., Monticone, P., and Catawbasam: mimiframework/Mimi.jl: v1.5.1, Zenodo [code], https://doi.org/10.5281/zenodo.7370071, 2022.
(DataCite stores "Girish Balaji" and "Arnav Gautam" as unsplit strings; I rendered them as "Balaji, G." and "Gautam, A.". "Catawbasam" is a GitHub handle, as listed.)
CHOICE FOR MARCUS: (a) cite v1.5.1 with its DOI and keep "Mimi (1.6)" in the text; this is a version mismatch. (b) Cite the concept DOI 10.5281/zenodo.4321855 as "Mimi.jl, all versions". (c) Cite the v1.6.0 GitHub release URL (no DOI), and let the Ladrillo Zenodo archive (Manifest.toml) pin the exact version. Option (c) plus (b) is probably the most honest.

---------------------------------------------------------------------------------------------------
## E. SLEIP emulators (SLEIP §3 and its reference list)

### FRISIA — SLEIP §3.3: "(Ramme et al., 2025)"; FRISIA version 1.0.1 run
Ramme, L., Blanz, B., Wells, C., Wong, T. E., Schoenberg, W., Smith, C., and Li, C.: Feedback-based sea level rise impact modelling for integrated assessment models with FRISIAv1.0, Geosci. Model Dev., 18, 10017–10052, https://doi.org/10.5194/gmd-18-10017-2025, 2025.  VERIFIED.

### MP25 — SLEIP §3.5: "MP25 (Perrette and Mengel, 2025)"
Perrette, M. and Mengel, M.: Relative sea level projections constrained by historical trends at tide gauge sites, Sci. Adv., 11, eado4506, https://doi.org/10.1126/sciadv.ado4506, 2025.  VERIFIED.

### ProFSea — SLEIP §3.6: "ProFSea tool v3.0 (Weeks et al., 2023)"
Weeks, J. H., Fung, F., Harrison, B. J., and Palmer, M. D.: The evolution of UK sea-level projections, Environ. Res. Commun., 5, 032001, https://doi.org/10.1088/2515-7620/acc020, 2023.  VERIFIED.
(Its glacier method also cites Palmer et al., 2020, Earth's Future 8, e2019EF001413, doi:10.1029/2019EF001413 — VERIFIED; optional.)

### SURFER — SLEIP §3.7: "SURFER v3.0 (Couplet et al., 2025)", extending v2.0 (Martínez Montero et al., 2022)
Couplet, V., Martínez Montero, M., and Crucifix, M.: SURFER v3.0: a fast model with ice sheet tipping points and carbon cycle feedbacks for short- and long-term climate scenarios, Geosci. Model Dev., 18, 3081–3129, https://doi.org/10.5194/gmd-18-3081-2025, 2025.  VERIFIED.
Optional: Martínez Montero, M., Crucifix, M., Couplet, V., Brede, N., and Botta, N.: SURFER v2.0: a flexible and simple model linking anthropogenic CO2 emissions and solar radiation modification to ocean acidification and sea level rise, Geosci. Model Dev., 15, 8059–8084, https://doi.org/10.5194/gmd-15-8059-2022, 2022.  VERIFIED (CO₂ subscript in the title).

### BRICK (SLEIP §3.1): "(Wong et al., 2017a)" for the model; "(Wong et al., 2026, 2022a)" for the current Mimi version; Mimi as "(Anthoff and others, 2025)"
- Wong et al. 2017a (BRICK v0.2, GMD) and 2022a (JOSS): both ALREADY in accepted.txt.
- "Wong et al., 2026" is a Zenodo dataset, VERIFIED on DataCite (title "Model output supporting MimiBRICK v2.0.0", 2026, resource type Dataset, version v4):
Wong, T., Rennels, L., Errickson, F., Srikrishnan, V., Bakker, A., Keller, K., and Anthoff, D.: Model output supporting MimiBRICK v2.0.0, Zenodo [data set], https://doi.org/10.5281/zenodo.20592337, 2026.
- SLEIP also lists "Wong, T.: Modeling the Sea-Level Change from U.S. Vehicle Emissions, 2026" with no DOI (not citable as given).
- Other BRICK components SLEIP cites: Wong et al. 2017b (fast dynamics, Clim. Change 144, 347–364, doi:10.1007/s10584-017-2039-4); Wong et al. 2022b (Earth's Future 10, e2022EF003061). Not re-verified here.

### MAGICC-SLR (SLEIP §3.4): "MAGICC-SLR (Nauels et al., 2017a, b, and 2025)", within MAGICC (Meinshausen et al., 2011a, b, and 2020)
- Nauels 2017a (GMD) and 2025 (NCC): ALREADY in accepted.txt.
- Nauels 2017b is NOT in the manuscript:
Nauels, A., Rogelj, J., Schleussner, C.-F., Meinshausen, M., and Mengel, M.: Linking sea level rise and socioeconomic indicators under the Shared Socioeconomic Pathways, Environ. Res. Lett., 12, 114002, https://doi.org/10.1088/1748-9326/aa92b6, 2017.  VERIFIED.
- MAGICC itself:
Meinshausen, M., Raper, S. C. B., and Wigley, T. M. L.: Emulating coupled atmosphere-ocean and carbon cycle models with a simpler model, MAGICC6 – Part 1: Model description and calibration, Atmos. Chem. Phys., 11, 1417–1456, https://doi.org/10.5194/acp-11-1417-2011, 2011.  VERIFIED.
Meinshausen, M., Wigley, T. M. L., and Raper, S. C. B.: Emulating atmosphere-ocean and carbon cycle models with a simpler model, MAGICC6 – Part 2: Applications, Atmos. Chem. Phys., 11, 1457–1471, https://doi.org/10.5194/acp-11-1457-2011, 2011.  VERIFIED.
Meinshausen, M., Nicholls, Z. R. J., Lewis, J., Gidden, M. J., Vogel, E., Freund, M., Beyerle, U., Gessner, C., Nauels, A., Bauer, N., Canadell, J. G., Daniel, J. S., John, A., Krummel, P. B., Luderer, G., Meinshausen, N., Montzka, S. A., Rayner, P. J., Reimann, S., Smith, S. J., van den Berg, M., Velders, G. J. M., Vollmer, M. K., and Wang, R. H. J.: The shared socio-economic pathway (SSP) greenhouse gas concentrations and their extensions to 2500, Geosci. Model Dev., 13, 3571–3605, https://doi.org/10.5194/gmd-13-3571-2020, 2020.  VERIFIED.

### FACTS in SLEIP: "FACTS v1.1 (Reedy and Kopp, 2023, Kopp et al., 2023)". Reedy & Kopp 2023 ("Temperature-Dependent Projections in FACTS v1.1.1") has no DOI in SLEIP.
Kopp 2023 cites the code as Zenodo 10.5281/zenodo.10152885 (FACTS v1.1.1). That DOI is not DataCite-checked here, so check it before use if the FACTS version is cited.

---------------------------------------------------------------------------------------------------
## Where each name appears in accepted.txt (line numbers from the plain-text file)

- LARMIP — first: Table 1 fn ² (l.35) "Calibrated to process-model projections (ISMIP6, LARMIP, DeConto, SICOPOLIS, PISM, GlacierMIP2)". Also Table 2 fn ¹² (l.53) "AR5 (parametric), LARMIP (response functions), DeConto (sampled), Bamber (expert judgement)"; l.232 "FACTS (LARMIP, DeConto, Bamber, AR5 and emulated ice-sheet modules)"; l.254 "LARMIP's response functions are 200 years long and zero beyond"; l.256 "and LARMIP Antarctica".
- DeConto — Table 1 fn ²; Table 2 fn ¹² "DeConto (sampled)"; l.232; l.254 "The Bamber and DeConto modules select their projections from the temperature integrated over 2000–2099".
- Bamber — first: Table 2 fn ¹² "Bamber (expert judgement)"; l.232; l.254; FIG 6 caption (l.252) "open triangles: structured expert judgement"; Table 1 fn ² "or structured expert judgement".
- AR5 — first: Table 2 fn ⁸ "Cumulative-melt cap from AR5 Table 4.2" (= AR5 Ch. 4, see ⚠ above); fn ¹² "AR5 (parametric)"; l.232; l.254 "with the AR5 Antarctic dynamics term as a prescribed function of time".
- emulandice — ONLY at l.230: "FACTS's three emulandice workflows (Gaussian-process emulators of ISMIP6 and GlacierMIP2 output) end in 2100".
- FittedISMIP — ONLY at l.254: "Its Greenland module (FittedISMIP) fits the melt rate to 2015–2100 ISMIP6 runs".
- GlacierMIP2 — first: Table 1 fn ²; then l.230.
- ISMIP6 — first: Introduction l.15 "a Greenland commitment above a threshold, informed by ISMIP6 and SICOPOLIS" (Greenland = Goelzer, already cited at l.96). Antarctic ISMIP6 is named ONLY implicitly: in Table 1 fn ² (which covers FACTS emulandice/AIS and ProFSea's AIS) and at l.230 (emulandice). So Seroussi 2020 belongs at l.230 (and optionally fn ²), and Seroussi 2024 in fn ² if ProFSea is meant.
- PISM — ONLY Table 1 fn ². Cite Golledge et al. 2019.
- Mimi — first: Model description l.158 "written in Julia (1.12) within the Mimi framework (1.6) as a set of components swapped into MimiBRICK v2.0.0"; again at l.274 (Discussion) "Ladrillo is coded in Julia within the Mimi framework, as MimiBRICK is". The Code availability paragraph (l.280) does NOT mention Mimi; the software citation may also belong there.
- SURFER, MP25 — first: Introduction l.13 "only three carry a hindcast of every component starting in 1900 or earlier: BRICK 2.0, SURFER, and MP25 (see Table 1)".
- FRISIA — first appears only as a Table 1 column header (l.22), then Table 2. Never named in running text.
- ProFSea — Table 1 header; Table 1 fn ⁵ "ProFSea's Greenland uses the FACTS implementation"; Table 2. Never named in running text.
- Suggestion: cite all four SLEIP emulators (plus BRICK 2.0 / MAGICC-SLR / FACTS) in the Table 1 caption, which already says "SLEIP entries from Nauels et al. (2026 …)".
- MAGICC-SLR — first: Table 1 header; running text l.228 already cites "(v7.5.3, sea-level parameters from Nauels et al., 2025)".
