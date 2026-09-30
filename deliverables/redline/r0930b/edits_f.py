"""09-30b edit set F: FACTS modules, GlacierMIP2, ISMIP6-Antarctica, PISM, Mimi, SLEIP emulators.
Entries are taken VERBATIM from refs_models.md (Crossref/DataCite-verified 2026-09-30; the two IPCC
chapters' author lists are from Kopp 2023 / SLEIP, which agree; Crossref has none)."""
import sys
sys.path.insert(0, "/private/tmp/claude-501/-Users-MarcusMarcus-Documents-2026-CodeProjects-FaIRtoFrEDI/e88c7db1-5ed3-4ee0-bbf2-08bb6c77ecb6/scratchpad/v0930b")
from trackedit import Doc
NOTES = open("/private/tmp/claude-501/-Users-MarcusMarcus-Documents-2026-CodeProjects-FaIRtoFrEDI/e88c7db1-5ed3-4ee0-bbf2-08bb6c77ecb6/scratchpad/v0930b/refs_models.md", encoding="utf8").read().splitlines()
def entry(prefix, must):
    hits = [l.strip() for l in NOTES if l.startswith(prefix) and must in l]
    assert len(hits) == 1, (prefix, must, len(hits))
    e = hits[0]
    for tail in ("  VERIFIED.", " VERIFIED."):
        if tail in e: e = e[:e.index(tail)].rstrip()
    assert e.endswith("."), e[-40:]
    return e
d = Doc(sys.argv[1] + "/word/document.xml")

# ---- in-text citations at first mention
d.replace("Scope and calibration of the seven SLEIP emulators and Ladrillo.",
          "Scope and calibration of the seven SLEIP emulators and Ladrillo: BRICK 2.0 (Wong et al., 2017b, 2022), FACTS "
          "(Kopp et al., 2023), FRISIA (Ramme et al., 2025), MAGICC-SLR (Nauels et al., 2017, 2025), MP25 (Perrette and "
          "Mengel, 2025), ProFSea (Weeks et al., 2023) and SURFER (Couplet et al., 2025).",
          "the references SLEIP itself uses for each emulator")
d.replace("BRICK 2.0, SURFER, and MP25 (see Table 1)",
          "BRICK 2.0, SURFER (Couplet et al., 2025), and MP25 (Perrette and Mengel, 2025; see Table 1)", "first mention")
d.replace("(ISMIP6, LARMIP, DeConto, SICOPOLIS, PISM, GlacierMIP2)",
          "(ISMIP6, Goelzer et al., 2020, Seroussi et al., 2020; LARMIP, Levermann et al., 2020; DeConto, DeConto et al., "
          "2021; SICOPOLIS, Greve and Chambers, 2022; PISM, Golledge et al., 2019; GlacierMIP2, Marzeion et al., 2020)",
          "PISM as SLEIP cites it (MAGICC-SLR's calibration to Golledge et al. 2019)")
d.replace("AR5 (parametric), LARMIP (response functions), DeConto (sampled), Bamber (expert judgement)",
          "AR5 (parametric; Church et al., 2013), LARMIP (response functions; Levermann et al., 2020), DeConto (sampled; "
          "DeConto et al., 2021), Bamber (expert judgement; Bamber et al., 2019)", "the citations FACTS (Kopp et al., 2023) uses")
d.replace("(Gaussian-process emulators of ISMIP6 and GlacierMIP2 output)",
          "(Gaussian-process emulators of ISMIP6 and GlacierMIP2 output; Edwards et al., 2021)", "Kopp 2023 cites Edwards 2021 for emulandice")
d.replace("Its Greenland module (FittedISMIP) fits", "Its Greenland module (FittedISMIP; Fox-Kemper et al., 2021) fits",
          "Kopp 2023 p.7466: details in Fox-Kemper et al. (2021) supplementary material")
d.replace("within the Mimi framework (1.6)", "within the Mimi framework (1.6; Rennels et al., 2022)",
          "no DOI exists for Mimi 1.6; the all-versions Zenodo DOI is cited")

# ---- reference entries (alphabetical; GMD: single, two-author, then 3+ chronologically)
MIMI = entry("Rennels, L., Anthoff, D.", "zenodo.7370071").replace(
    "mimiframework/Mimi.jl: v1.5.1, Zenodo [code], https://doi.org/10.5281/zenodo.7370071, 2022.",
    "mimiframework/Mimi.jl, all versions, Zenodo [code], https://doi.org/10.5281/zenodo.4321855, 2022.")
assert "4321855" in MIMI
R = [
 ("Church, J. A. and White", True,  entry("Bamber, J. L.", "11195")),
 ("Church, J. A. and White", False, entry("Church, J. A., Clark", "CBO9781107415324.026")),
 ("Dangendorf, S.: Kalman Smoother", True, entry("Couplet, V.", "gmd-18-3081")),
 ("Eyring, V., Bony", True, entry("DeConto, R. M.", "s41586-021-03427-0")),
 ("Eyring, V., Bony", True, entry("Edwards, T. L., Nowicki", "s41586-021-03302-y")),
 ("Frederikse, T., Landerer", True, entry("Fox-Kemper, B.", "9781009157896.011")),
 ("Greve, R. and Chambers", True, entry("Golledge, N. R., Keller", "s41586-019-0889-9")),
 ("Mengel, M., Levermann", True, entry("Levermann, A., Winkelmann", "esd-11-35-2020")),
 ("Mengel, M., Levermann", True, entry("Marzeion, B., Hock", "2019EF001470")),
 ("Rignot, E., Mouginot, J., Scheuchl", True, entry("Perrette, M.", "ado4506")),
 ("Rignot, E., Mouginot, J., Scheuchl", True, entry("Ramme, L.", "gmd-18-10017")),
 ("Rignot, E., Mouginot, J., Scheuchl", True, MIMI),
 ("Shaffer, G.: Formulation", True, entry("Seroussi, H., Nowicki", "tc-14-3033-2020")),
 ("WGMS: GTN-G", True, entry("Weeks, J. H.", "acc020")),
]
for anchor, before, text in R:
    d.insert_para(anchor, text, before=before, why="reference added (verified 2026-09-30)")
d.save()
for o, n, w in d.log: print(f"- {o[:50]!r} -> {n[:60]!r}")
print(len(d.log), "edits")
