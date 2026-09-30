"""09-30b: reply in the reference-audit thread (#17)."""
import sys
sys.path.insert(0, "/private/tmp/claude-501/-Users-MarcusMarcus-Documents-2026-CodeProjects-FaIRtoFrEDI/e88c7db1-5ed3-4ee0-bbf2-08bb6c77ecb6/scratchpad/v0930b")
from comments_lib import reply
reply(17, "09-30b, done as tracked changes. (1) Wong, Bakker and Keller (2017a) cited for the DAIS paleo file; "
          "BRICK v0.2 becomes 2017b in all three places (GMD rule: same first author and year, ordered by the next "
          "differing co-author, Keller before Ruckert). (2) The Table 3 dataset DOIs are now reference entries: "
          "GlaMBIE (2024), Wiese et al. (2024), Dangendorf (2024), Smith et al. (2026) for the IGCC release, Schuster "
          "et al. (2025) for the GlacierMIP3 data, WGMS (2023). (3) New references for LARMIP, DeConto, Bamber, AR5, "
          "emulandice (Edwards et al., 2021), FittedISMIP (Fox-Kemper et al., 2021), GlacierMIP2, ISMIP6 Antarctica, PISM, "
          "Mimi and FRISIA, MP25, ProFSea and SURFER, each at first mention; module citations follow Kopp et al. (2023) and "
          "emulator citations follow SLEIP. (4) HadCRUT5 row added to Table 3 (HadCRUT.5.0.2.0 analysis ensemble mean; no "
          "DOI is published). Judgment calls, easy to change: PISM is cited as Golledge et al. (2019), the PISM runs SLEIP "
          "uses, not a model paper. Mimi 1.6 has no DOI, so the all-versions Zenodo DOI is cited (creators from its last "
          "archived version, 1.5.1). GRACE year 2024 is the DOI record's; the provider lists a 2023 release. Author lists "
          "for the two IPCC chapters come from the FACTS and SLEIP reference lists (Crossref has none). Not added: Nauels et "
          "al. 2017b (would force a/b on Nauels 2017) and AR5 Chapter 4 for Table 2 footnote 8 (no verified author list).")
