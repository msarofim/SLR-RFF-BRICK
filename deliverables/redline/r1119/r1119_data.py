"""Round r1119 wording edits (author Claude), on Tony Wong's 11-19 file with his four edits accepted.
Each entry: (context that occurs once in one run, old text inside it, new text, why). Marcus 11-19: "go ahead, cut the
SLEIP sentence, equations too", and "Consider whether any of [the MAGICC notes] should make it into the paper"."""

EDITS = [
    # Tony's abstract insertion: the paper's name for the release is "BRICK 2.0" (Sect. 1); "A departure ..., Ladrillo"
    # made Ladrillo the departure.
    ("A departure from its predecessor, BRICK v2.0, Ladrillo", "A departure", "In a departure", "Tony's abstract sentence: grammar"),
    (" from its predecessor, BRICK v2.0, Ladrillo", "BRICK v2.0", "BRICK 2.0", "Tony's abstract sentence: the paper's name"),
    # Tony's reproducibility pointer: the Code availability section names the archive as the permanent copy
    ("regenerated following instructions in the Ladrillo GitHub repository",
     "following instructions in the Ladrillo GitHub repository",
     "following the instructions in the code archive (see Code availability)", "point to the archive, as Code availability does"),
    # the README in the archive now covers what the "user manual" sentence promised
    ("A user manual (installation, running the calibration and projections, input formats) is in preparation and will be included in the archive.",
     "A user manual (installation, running the calibration and projections, input formats) is in preparation and will be included in the archive.",
     "The README in the archive covers installation, running the calibration and projections, and the input and output files.",
     "the manual exists: Ladrillo.jl README"),
    # deferred 11-12 item 1: unsupported (FACTS module audit); no SLEIP answer yet, so cut (Marcus 11-19)
    ("are omitted past 2100. SLEIP’s 2300 FACTS values are these extrapolations (Nauels et al., 2026).",
     " SLEIP’s 2300 FACTS values are these extrapolations (Nauels et al., 2026).", "", "SLEIP sentence cut (Marcus 11-19)"),
    # sea level: open form throughout (Marcus 11-19; Tony's comment on the abstract)
    (" century sea-level rise. Ladrillo inherits", "sea-level", "sea level", "sea level, open form"),
    ("MAGICC-SLR (sea-level module of the Model", "sea-level", "sea level", "sea level, open form"),
    ("cm sea-level equivalent (SLE)", "sea-level", "sea level", "sea level, open form"),
    ("20th century sea-level rise contribution", "sea-level", "sea level", "sea level, open form"),
    ("DAIS sea-level feedback", "sea-level", "sea level", "sea level, open form"),
    ("The total sea-level series", "sea-level", "sea level", "sea level, open form"),
    ("(v7.5.3, sea-level parameters from Nauels", "sea-level", "sea level", "sea level, open form"),
    ("global sea-level change that is derived", "sea-level", "sea level", "sea level, open form"),
]

INSERTS = [
    # deferred 11-12 item 2: the FACTS version the comparison ran (note 5 and Sect. 4.2 describe v1.1.4 at its defaults)
    ("comparing to BRICK 2.0, FACTS (Kopp et al., 2023)", "comparing to BRICK 2.0, FACTS (", "v1.1.4; ", "FACTS version"),
    # MAGICC comparator notes (AGU poster analysis 11-19, answers_2026-11-19 §12.4-12.5)
    ("so the difference comes from the ice-sheet modules.", "so the difference comes from the ice-sheet modules.",
     " MAGICC-SLR’s Antarctic term is quadratic in global surface air temperature, with each member assigned one of five"
     " curves fitted to the 5th, 17th, 50th, 83rd and 95th percentiles of an emulator of one ice-sheet model without"
     " marine ice-cliff instability (Edwards et al., 2019; Nauels et al., 2025). Its SSP5-8.5 median at 2300, 7.1 m"
     " (Nauels et al., 2025), is above the AR6 17–83% range without marine ice-cliff instability (−0.28 to 3.13 m;"
     " Fox-Kemper et al., 2021), and about half of its members gain Antarctic mass over 2002–2023, when IMBIE 2026 shows"
     " a loss of 0.43 ± 0.07 mm yr⁻¹ (Otosaka et al., 2026).",
     "MAGICC comparator note, High scenarios"),
    ("against 166 cm for Ladrillo and 221 cm for BRICK 2.0).", "against 166 cm for Ladrillo and 221 cm for BRICK 2.0).",
     " MAGICC-SLR’s Antarctic spread comes from its five fitted curves and its climate ensemble.",
     "MAGICC comparator note, Very Low"),
]

# Table 2, Antarctic row: MAGICC-SLR's cell is the first "parametric" after FACTS's "by workflow" cell
TABLE2 = ("by workflow", "parametric", "quadratic in GSAT")

REF_BEFORE = "Edwards, T. L., Nowicki, S."
REF_NEW = ("Edwards, T. L., Brandon, M. A., Durand, G., Edwards, N. R., Golledge, N. R., Holden, P. B., Nias, I. J., "
           "Payne, A. J., Ritz, C., and Wernecke, A.: Revisiting Antarctic ice loss due to marine ice-cliff instability, "
           "Nature, 566, 58–64, https://doi.org/10.1038/s41586-019-0901-4, 2019.")   # Crossref, checked 11-19

COMMENTS = [
    ("These changes improve",
     "Claude 11-19, optional: Fig. 1 and Sect. 4 run BRICK 2.0 on the same FaIR forcing, so the FaIR driver is not one "
     "of the changes behind this hindcast improvement. 'These changes' could become 'The structural and calibration changes'."),
    ("MAGICC-SLR’s Antarctic term is quadratic",
     "Claude 11-19, sources. Module form and the five fits: Nauels et al. (2025), Supplement Sect. 3.2.2 and Table 12 "
     "(the AGU poster session read the Supplement and matched Table 12 to our MAGICC parameter set to ten digits). "
     "7.1 m: their Supplementary Table 4, labelled low confidence there; our runs give 712 cm. The AR6 range "
     "(−0.28 to 3.13 m, 17–83%) is as the poster session quoted it alongside that table; I could not open AR6 Ch. 9 to "
     "confirm where AR6 tabulates it, so please check it before keeping the Fox-Kemper citation. Hindcast: "
     "FaIRtoFrEDI magicc_comparison/diag_magicc_ais_hindcast_imbie.py; 51% of the 600 members gain mass over "
     "2002–2023; IMBIE 0.43 ± 0.07 mm yr⁻¹. Ladrillo is also low against IMBIE (Sect. 3.1), so the contrast is "
     "between a low rate and no net loss."),
]
TONY_REPLY = ("2026-11-19T13:46:00Z",
              "Claude 11-19: changed to the open form throughout (“sea level”, “sea level rise”, as in IPCC AR5 and AR6 "
              "and SLEIP), in 8 places. The hyphen stays only in reference titles and in FACTS’s name.")
