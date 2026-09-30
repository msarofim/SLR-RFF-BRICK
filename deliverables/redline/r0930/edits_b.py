"""09-30 edit set B: reference list (additions verified against Crossref 09-30, order per GMD guidelines)."""
import sys
sys.path.insert(0, "/private/tmp/claude-501/-Users-MarcusMarcus-Documents-2026-CodeProjects-FaIRtoFrEDI/e88c7db1-5ed3-4ee0-bbf2-08bb6c77ecb6/scratchpad/v0930")
from trackedit import Doc
W = sys.argv[1]
d = Doc(W + "/word/document.xml")

d.replace("continues to use the same DAIS structure as was used in BRICK",
          "continues to use the same DAIS structure (Shaffer, 2014) as was used in BRICK", "DAIS named without a reference")
d.replace("(HadCRUT5, area-weighted over each glacier block;", "(HadCRUT5, Morice et al., 2021, area-weighted over each glacier block;",
          "HadCRUT5 used as an input with no citation")

NEW = {
 "Gelman": ("GlaMBIE Team: Community estimate", True,
   "Gelman, A. and Rubin, D. B.: Inference from iterative simulation using multiple sequences, Stat. Sci., 7, 457–472, https://doi.org/10.1214/ss/1177011136, 1992."),
 "Morice": ("Mouginot, J., Rignot, E., Bjørk", True,
   "Morice, C. P., Kennedy, J. J., Rayner, N. A., Winn, J. P., Hogan, E., Killick, R. E., Dunn, R. J. H., Osborn, T. J., Jones, P. D., and Simpson, I. R.: An updated assessment of near-surface temperature change from 1850: The HadCRUT5 data set, J. Geophys. Res.-Atmos., 126, e2019JD032361, https://doi.org/10.1029/2019JD032361, 2021."),
 "Parkes": ("Rignot, E., Mouginot, J., Scheuchl", True,
   "Parkes, D. and Marzeion, B.: Twentieth-century contribution to sea-level rise from uncharted glaciers, Nature, 563, 551–554, https://doi.org/10.1038/s41586-018-0687-9, 2018."),
 "Shaffer": ("Schwarz, G.: Estimating the dimension", False,
   "Shaffer, G.: Formulation, calibration and validation of the DAIS model (version 1), a simple Antarctic ice sheet model sensitive to variations of sea level and ocean subsurface temperature, Geosci. Model Dev., 7, 1803–1818, https://doi.org/10.5194/gmd-7-1803-2014, 2014."),
}
for k, (anchor, before, text) in NEW.items():
    d.insert_para(anchor, text, before=before, why=f"reference added ({k}); Crossref-verified 2026-09-30")

# order (GMD guidelines: alphabetical by first author; single-author before multi-author for the same name)
NAS = ("National Academies of Sciences, Engineering, and Medicine: Valuing Climate Damages: Updating Estimation of the "
       "Social Cost of Carbon Dioxide, The National Academies Press, Washington, DC, https://doi.org/10.17226/24651, 2017.")
d.delete_para("National Academies of Sciences, Engineering, and Medicine: Valuing", why="moved before Nauels")
d.insert_para("Nauels, A., Meinshausen, M., Mengel, M.", NAS, before=True, why="'Nat' sorts before 'Nau'")
SM = "Smith, C.: fair calibration data, v1.6.0 (fastmip v1 calibration of fair v2.2.4), Zenodo [data set], https://doi.org/10.5281/zenodo.18828694, 2026."
d.delete_para("Smith, C.: fair calibration data", why="moved: single-author before multi-author")
d.insert_para("Smith, C., Cummins, D. P., Fredriksen", SM, before=True, why="GMD: single-author papers first")
VV = open("/private/tmp/claude-501/-Users-MarcusMarcus-Documents-2026-CodeProjects-FaIRtoFrEDI/e88c7db1-5ed3-4ee0-bbf2-08bb6c77ecb6/scratchpad/v0930/vv_ref.txt", encoding="utf8").read().strip()
d.delete_para("van Vuuren, D. P., O'Neill, B. C.", why="moved: 'van Vuuren' sorts before 'Vehtari'")
d.insert_para("Vehtari, A., Gelman, A., Simpson", VV, before=True, why="copernicus.bst sorts on 'van Vuuren'")
d.delete_para("Reference list complete for everything the text cites", why="working note, and no longer true")
d.save()
for o, n, w in d.log: print(f"- {o[:60]!r} -> {n[:60]!r}")
print(len(d.log), "edits")
