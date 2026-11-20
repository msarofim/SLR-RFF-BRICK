"""Round r1120 edits (2026-11-20) on the r1119 clean copy (GMD.Ladrillo.v1.2026-11-19.clean.docx, md5 213fc5e9).
Marcus 11-20 (AskUserQuestion): the mechanical items of the 11-19 final-review list (2-5, 8, "%" spacing, table-footnote
letters) plus item 1 as "-18 to +31 cm across the van Vuuren scenarios" and entries for the missing references
(item 6). The list: SLR-RFF-BRICK/notes/handoff_2026-11-20_gmd_final_review.md, Sect. 4.

EDITS:   (context occurring once in one plain run, old text inside it, new text, why)       author "Claude"
INSERTS: (context, prefix of the context, text inserted after the prefix, why)               author "Claude"
REFS:    (anchor of the reference entry the new one goes BEFORE, new entry, why)            author "Claude"
STYLE (footnote letters, "%" spacing, "note 14" -> "note b") is in style_r1120.py, author "Claude (style)".
"""

EDITS = [
    # item 1: the body reports only the van Vuuren scenarios (Sect. 4.2: High-to-Low -18.2, High +31.4); +47 cm is
    # SSP5-8.5 (joint 280.9 vs 233.8 cm; Ladrillo/outputs/projections/{joint,brick20}_cells_ssp585.csv)
    ("by −18 to +47 cm, depending on the scenario", "+47 cm, depending on the scenario",
     "+31 cm across the van Vuuren scenarios", "item 1: range of the scenarios the body reports"),
    # item 2: 0.43 +- 0.07 is a mean rate over 2002-2023; Sect. 3.1's 0.52 +- 0.05 is an OLS trend over 2002-2021
    ("when IMBIE 2026 shows a loss of 0.43 ± 0.07 mm yr⁻¹ (Otosaka", "a loss of 0.43 ± 0.07 mm yr⁻¹", "a net loss",
     "item 2: a second IMBIE estimator would sit beside Sect. 3.1's"),
    # item 3: the section's title
    ("in the code archive (see Code availability)", "Code availability", "Code and data availability",
     "item 3: section title"),
    # item 5: no Results section discusses RGI 19's response time; regrowth is discussed in Sect. 4.3, not 4.2
    ("at 1.5 K; see Sect. 4.3)", "; see Sect. 4.3", "", "item 5: no section discusses it"),
    ("is in equilibrium with (see Sect. 4.2)", "4.2", "4.3", "item 5: regrowth is in Sect. 4.3"),
    # item 8: Copernicus conventions ("Sect." not at a sentence start; words for cardinal numbers below 10;
    # middle initials with a period)
    ("Sect. 4.1 attributes", "Sect.", "Section", "item 8: sentence start"),
    ("resulting from 5 components", "5", "five", "item 8: number below ten"),
    ("projections of 7 sea level emulators", "7", "seven", "item 8: number below ten"),
    ("constrains 3 combinations", "3", "three", "item 8: number below ten"),
]

INSERTS = [
    ("Marcus C Sarofim", "Marcus C", ".", "item 8: middle initial"),
    ("Tony E Wong", "Tony E", ".", "item 8: middle initial"),
    # item 4: Table A1 lists 11 'remaining' parameters: thermal_alpha, d2_steric_1/2, and 8 noise parameters
    ("11 remaining (a two-coefficient", "11 remaining (", "the thermal expansion coefficient α, ",
     "item 4: the list had 10 of the 11"),
    # item 6: in-text citations for the three uncited sources
    ("1901–2024 in HadCRUT5, Berkeley Earth and GISTEMP:", "1901–2024 in HadCRUT5, Berkeley Earth",
     " (Rohde and Hausfather, 2020)", "item 6: Berkeley Earth reference"),
    (" and GISTEMP: N(", " and GISTEMP", " (Lenssen et al., 2024; GISTEMP Team, 2026)", "item 6: GISTEMP reference"),
    ("spliced at 2023.5 to MESSAGE-GLOBIOM SSP2-4.5. Future", "spliced at 2023.5 to MESSAGE-GLOBIOM SSP2-4.5",
     " (Fricko et al., 2017; Gidden et al., 2019)", "item 6: SSP2-4.5 reference"),
    # r1120b (Marcus 11-20: "add Table 9.11 to the citation and resolve the comment"). Verified 11-20 in the built-in
    # browser: AR6 WG1 Ch. 9 Table 9.11, SSP5-8.5, Antarctica at 2300, "Assessed Ice-sheet Contribution" column
    ("(−0.28 to 3.13 m; Fox-Kemper et al., 2021)", "(−0.28 to 3.13 m; Fox-Kemper et al., 2021", ", Table 9.11",
     "AR6 range: name the table (verified 11-20)"),
]

# r1120b: reply to Claude's 11-19 sources comment (identified by its opening words), then mark the thread resolved
# (w15:done="1" on the comment and the reply in commentsExtended.xml)
RESOLVE = ("Claude 11-19, sources.",
           "Claude 11-20: checked. AR6 WG1 Ch. 9, Table 9.11, SSP5-8.5, Antarctic contribution at 2300 relative to "
           "1995–2014, \"Assessed Ice-sheet Contribution\" column: −0.28 to +3.13 m, 17th–83rd percentiles. MICI is a "
           "separate column there (6.87–13.54 m), so the text's \"without marine ice-cliff instability\" is right. The "
           "citation now names Table 9.11.")

# Crossref metadata checked 11-20 (DOIs below). Dataset entry in the style of the draft's NOAA STAR entry; the access
# date is the GISTEMP download date in Ladrillo/tools/targets/README.md (gistemp1200_GHCNv4_ERSSTv5.nc, 2026-08-09).
REFS = [
    ("Gelman, A. and Rubin, D. B.",
     "Fricko, O., Havlík, P., Rogelj, J., Klimont, Z., Gusti, M., Johnson, N., Kolp, P., Strubegger, M., Valin, H., "
     "Amann, M., Ermolieva, T., Forsell, N., Herrero, M., Heyes, C., Kindermann, G., Krey, V., McCollum, D. L., "
     "Obersteiner, M., Pachauri, S., Rao, S., Schmid, E., Schoepp, W., and Riahi, K.: The marker quantification of the "
     "Shared Socioeconomic Pathway 2: A middle-of-the-road scenario for the 21st century, Global Environ. Change, 42, "
     "251–267, https://doi.org/10.1016/j.gloenvcha.2016.06.004, 2017.", "item 6"),
    ("GlaMBIE: Glacier Mass Balance Intercomparison",
     "Gidden, M. J., Riahi, K., Smith, S. J., Fujimori, S., Luderer, G., Kriegler, E., van Vuuren, D. P., van den Berg, "
     "M., Feng, L., Klein, D., Calvin, K., Doelman, J. C., Frank, S., Fricko, O., Harmsen, M., Hasegawa, T., Havlík, P., "
     "Hilaire, J., Hoesly, R., Horing, J., Popp, A., Stehfest, E., and Takahashi, K.: Global emissions pathways under "
     "different socioeconomic scenarios for use in CMIP6: a dataset of harmonized emissions trajectories through the "
     "end of the century, Geosci. Model Dev., 12, 1443–1475, https://doi.org/10.5194/gmd-12-1443-2019, 2019.", "item 6"),
    ("GlaMBIE: Glacier Mass Balance Intercomparison",
     "GISTEMP Team: GISS Surface Temperature Analysis (GISTEMP), version 4, NASA Goddard Institute for Space Studies "
     "[data set], https://data.giss.nasa.gov/gistemp/, last access: 9 August 2026, 2026.", "item 6"),
    ("Levermann, A., Winkelmann, R.",
     "Lenssen, N., Schmidt, G. A., Hendrickson, M., Jacobs, P., Menne, M. J., and Ruedy, R.: A NASA GISTEMPv4 "
     "observational uncertainty ensemble, J. Geophys. Res.-Atmos., 129, e2023JD040179, "
     "https://doi.org/10.1029/2023JD040179, 2024.", "item 6"),
    ("Sarofim, M. C., Smith, J. B.",
     "Rohde, R. A. and Hausfather, Z.: The Berkeley Earth Land/Ocean Temperature Record, Earth Syst. Sci. Data, 12, "
     "3469–3479, https://doi.org/10.5194/essd-12-3469-2020, 2020.", "item 6"),
]

# Claude's 11-19 sources comment on the MAGICC sentence repeats the dropped rate (item 2): string edit in comments.xml
COMMENT_FIX = ("IMBIE 0.43 ± 0.07 mm yr⁻¹.",
               "IMBIE shows a net loss over the same years (r1120: the rate is no longer quoted in the text; its mean "
               "rate over 2002–2023 is 0.43 ± 0.07 mm yr⁻¹, while Sect. 3.1's 0.52 ± 0.05 is an OLS trend over "
               "2002–2021, a different estimator).")

COMMENTS = [
    ("Its response time is the least constrained",
     "Claude 11-20: removed \"see Sect. 4.3\" here; no Results section discusses RGI 19's response time. Restore it "
     "with a target if you add that discussion."),
    ("spliced at 2023.5 to MESSAGE-GLOBIOM SSP2-4.5",
     "Claude 11-20: Fricko et al. (2017) is the MESSAGE-GLOBIOM SSP2 marker. Gidden et al. (2019) is the CMIP6 "
     "harmonization of the series the forcing file holds (RCMIP format, MESSAGE-GLOBIOM___SSP2-45, from the "
     "fair-calibrate repository). Drop Gidden if you prefer to cite the marker only."),
]
