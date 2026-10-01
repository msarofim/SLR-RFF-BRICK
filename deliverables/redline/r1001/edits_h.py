"""10-01 edit set H: arm definitions + labels, scenario names, number fixes, disclosures, Table 3 rows.
Receipts: rev1001 facts agent (outputs/*L27*.csv provenance, prep_recalib_targets_ext.py at HEAD)."""
import sys
sys.path.insert(0, "/private/tmp/claude-501/-Users-MarcusMarcus-Documents-2026-CodeProjects-FaIRtoFrEDI/e88c7db1-5ed3-4ee0-bbf2-08bb6c77ecb6/scratchpad/v1001")
from trackedit import Doc
d = Doc(sys.argv[1] + "/word/document.xml")

# ---- arms: defined at first need (Overall structure), fixed-arm numbers labelled
d.insert_after("see below). ",
    "Projections are run in two ways. In the joint arm, each posterior draw is paired with one of the 841 FaIR "
    "configurations, so the spread combines parameter and climate uncertainty. In the fixed arm, every draw is driven by "
    "the FaIR ensemble-mean GMST and ocean heat content, so the spread is parameter uncertainty only. ",
    "Marcus 10-01: define joint/fixed arm")
d.replace("The parameter’s leverage is strongly scenario-dependent:", "The parameter’s leverage (fixed arm) is strongly scenario-dependent:",
          "diag_ais_amp_leverage_L27.csv: fixed-driver arm")
d.replace("(6 and 13 cm for SSP5-8.5)", "(6 and 13 cm for SSP5-8.5; fixed arm)", "diag_brick_philosophy_arms_L27.csv: FaIR-mean driver")
d.replace("1.002 at 2150 on SSP2-4.5,", "1.002 at 2150 on SSP2-4.5 in the fixed arm,", "diag_slr_convergence_by_chain_ladrillo.jl reads fair_mean_gmst")
d.replace("reproduces every Antarctic projection median to within 1.3 cm at 2300",
          "reproduces every Antarctic projection median (fixed arm) to within 1.3 cm at 2300", "diag_refit_precision block ssp_fixed")
d.replace("FaIR-mean forcing (fixed-climate arm).", "Fixed arm.", "now defined in the text")
d.replace("All Ladrillo bands are the joint (posterior × FaIR-forcing) arm.",
          "All Ladrillo bands and medians below are from the joint arm.", "definition moved to Overall structure")

# ---- van Vuuren scenario names (van Vuuren et al. 2026, Table 1); codes replaced by names
d.replace("(van Vuuren et al., 2026; 'van Vuuren scenarios' below)",
          "(van Vuuren et al., 2026; 'van Vuuren scenarios' below): High, High-to-Low, Medium, Medium-to-Low, Low, "
          "Low-to-Negative (Low-to-Neg in the figures) and Very Low", "Marcus 10-01: define the scenario terms")
d.replace("occurs on vvLN and vvML", "occurs on Low-to-Negative and Medium-to-Low", "scenario code -> name")
d.replace("For vvVL its 2300", "For Very Low its 2300", "scenario code -> name")
d.replace("0.11 cm at vvLN and 0.10 cm at vvML", "0.11 cm at Low-to-Negative and 0.10 cm at Medium-to-Low", "scenario code -> name")
d.replace("regrows 1.95 cm at vvLN", "regrows 1.95 cm at Low-to-Negative", "scenario code -> name")
d.replace("at vvLN, the scenario where", "at Low-to-Negative, the scenario where", "scenario code -> name")
# figure signposting so FIGs 2-6 are cited in order in the body
d.insert_after("whereas MAGICC-SLR relies on its own 600-member AR6 ensemble.",
    " FIG 2 and FIG 3 compare the four models by component at 2100 and 2300, FIG 4 shows the Ladrillo and BRICK 2.0 "
    "trajectories, FIG 5 Ladrillo's glacier response, and FIG 6 each model's responsiveness to scenario.",
    "FIGs 2, 3, 4 and 6 were cited only in their captions")

# ---- number fixes
d.replace("(5–95% widths of 314 and 405 cm at SSP5-8.5 in 2300)", "(5–95% widths of 274 and 332 cm at 2300)",
          "vv_model_comparison_L27.csv vvH: 273.9 / 331.7; 314/405 were SSP5-8.5")
d.replace("MAGICC-SLR is the narrow outlier throughout", "MAGICC-SLR is the narrow outlier on Antarctica, thermal expansion and the total",
          "vvVL: MAGICC wider on Greenland, glaciers and land water at 2100 and 2300")
d.replace("That excess has two parts of similar size.",
          "Over 1993–2024, when FaIR's uptake is 1.22× IGCC's 0–2000 m estimate, that excess has two parts of similar size.",
          "diag_te_rate_attribution_L27.csv row D: 1.1022 x 1.1022 = 1.215 (1993-2024)")
d.replace("yields changes of up to 31 cm by 2300", "yields reductions of up to 31 cm by 2300",
          "Ladrillo-BRICK AIS medians: -30.9 (SSP2-4.5), -27.2 (High-to-Low)")

# ---- SSP forcing (facts: FaIRtoFrEDI scripts/build_emissions_v160_ssp_rcmip.py; commit 839a176)
d.insert_after("rather than by the historical emissions inventory.",
    " The SSP1-2.6, SSP2-4.5 and SSP5-8.5 projections used for sensitivity tests run the same FaIR ensemble on CMIP7 "
    "historical emissions joined at 2023.5 to the RCMIP (v5.1.0) SSP emissions, harmonized per species.",
    "SSP runs were quoted but never described")

# ---- disclosures: STAR extends the total after 2021; GRACE also extends AIS/GIS; NOAA thermosteric
d.replace("The total is compared against Dangendorf et al. (2024), which is not a calibration target.",
          "The total is compared against Dangendorf et al. (2024), extended with NOAA STAR altimetry over 2022–2024, which is "
          "not a calibration target.", "Dangendorf ends 2021 (recalib_targets_ext_sources.csv)")
d.replace("(Dangendorf et al., 2024) is an out-of-sample check",
          "(Dangendorf et al., 2024, extended with NOAA STAR altimetry over 2022–2024) is an out-of-sample check", "same")
d.replace("The total in FIG 1 and Table 4.", "The total in FIG 1 and Table 4, through 2021.", "STAR row added below")
d.replace("Land-water storage, 2019–2023", "Antarctic and Greenland mass 2019–2025, and land-water storage 2019–2023",
          "prep_recalib_targets_ext.py:361-366 (grace_antarctica/greenland_mass)")
d.insert_row("Kalman-smoother reconstruction (Dangendorf, 2024)",
    ["(not a calibration target) NOAA STAR altimetry GMSL",
     "NOAA Laboratory for Satellite Altimetry, slr_sla_gbl_free_ref_90 (66° S–66° N, inverted barometer applied, annual "
     "signal removed, no GIA correction), acquired May 2026; no version or DOI is published",
     "The total in FIG 1 and Table 4 over 2022–2024, offset-matched to Dangendorf et al. (2024) over 2003–2018."],
    "prep_recalib_targets_ext.py:23; download_obs.py:211")
d.insert_row("Release RL06.3Mv04 CRI (Wiese et al., 2024)",
    ["NOAA NCEI 0–2000 m thermosteric sea level",
     "World-ocean yearly 0–2000 m thermosteric anomaly, NCEI Accession 0164586 (Levitus et al., 2017), 2005–2025",
     "Thermal expansion 2019–2025, offset-matched to Frederikse over 2005–2018."],
    "prep_recalib_targets_ext.py OVERLAP steric (2005, 2018), SPLICE_FROM 2019")
d.insert_after("Kelly McCusker for help with the FACTS model.",
    " Altimetry data are provided by NOAA Laboratory for Satellite Altimetry.", "acknowledgement required by the STAR file header")
d.insert_para("Levermann, A., Winkelmann",
    "Levitus, S., Antonov, J. I., Boyer, T. P., Baranova, O. K., García, H. E., Locarnini, R. A., Mishonov, A. V., Reagan, "
    "J. R., Seidov, D., Yarosh, E., and Zweng, M. M.: NCEI ocean heat content, temperature anomalies, salinity anomalies, "
    "thermosteric sea level anomalies, halosteric sea level anomalies, and total steric sea level anomalies from 1955 to "
    "present calculated from in situ oceanographic subsurface profile data (NCEI Accession 0164586), NOAA National Centers "
    "for Environmental Information [data set], https://doi.org/10.7289/V53F4MVP, 2017.",
    before=False, why="DataCite-verified 2026-10-01")
d.save()
for o, n, w in d.log: print(f"- {o[:50]!r} -> {n[:55]!r}")
print(len(d.log), "edits")
