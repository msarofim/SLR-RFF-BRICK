"""Apply the 2026-09-17 review of GMD.Ladrillo.v1.docx as tracked changes + comments."""
from redline import *

x = load()

# ---------------- copyedits / accuracy (tracked) ----------------
x = replace_text(x, "premiere sea level rise emulators", "premier sea level rise emulators")
x = replace_text(x, "(SLEIP reference)", "(Nauels et al., 2026)")
x = replace_text(x, "Ladrillo largest structural changes", "Ladrillo's largest structural changes")
x = replace_text(x, "(though the last module is a constant for now)",
                 "(the last taken from observations in the hindcast and from BRICK 2.0's stochastic land-water module in projections; see below)")
x = replace_text(x, "but that would require temperatures to drop below 1850 levels",
                 "but full regrowth would require temperatures to return to their 1850 level; partial regrowth begins whenever a block's temperature falls below the level its current volume is in equilibrium with (FIG 5)")
x = replace_text(x, "the three described below", "the three described above")
x = replace_text(x, "ssp245harm forcing", "SSP2-4.5 forcing (see Forcing)")
x = replace_text(x, "Following the BRICK v0.2 description (Wong 2017)", "Following Wong et al. (2017)")
x = replace_text(x, "As in Wong 2017,", "As in Wong et al. (2017),")
x = replace_text(x, "We report comparisons to both the van Vuuren scenarios, with BRICK2.0, FACTS, and MAGICC used as cmoparisons.",
                 "We report projections on the seven van Vuuren scenarios, with BRICK 2.0, FACTS and MAGICC-SLR as comparators.")
x = replace_text(x, "At 2150 and 2300 (FIGs 3, 4 and 9) only", "At 2300 (FIG 3) only")
x = replace_text(x, "FIG 4.", "FIG 3.", para="The same comparison at 2300")
x = replace_text(x, "FIG 5.", "FIG 4.", para="Component trajectories across the van Vuuren scenarios")
x = replace_text(x, "FIG 6.", "FIG 5.", para="Ladrillo glacier contribution to 2300")
x = replace_text(x, "FIG 7.", "FIG 6.", para="the High-minus-Very-Low difference of medians")
x = replace_text(x, "(to 425 and 393; FIG 11)", "(to 425 and 393)")
x = replace_text(x, "Ladrillo continues to be codes in the [describe] [available, open-source, accessible, transparent languages].",
                 "Ladrillo is coded in Julia within the Mimi framework, as MimiBRICK is, and is released under an open-source (MIT) licence.")

# the internal calibration tag out of the paper
x = replace_text(x, "Ladrillo L24 (solid", "Ladrillo (solid")
x = replace_text(x, "RMSE of the Ladrillo L24 median", "RMSE of the Ladrillo median")
x = replace_text(x, "Information criteria for the Ladrillo L24 and BRICK 2.0", "Information criteria for the Ladrillo and BRICK 2.0")
x = replace_text(x, "Ladrillo L24 compared against BRICK 2.0", "Ladrillo compared against BRICK 2.0")
x = replace_text(x, "L24 is therefore accepted", "The posterior is therefore accepted")

# ---------------- the empty methodology sections (tracked insertions) ----------------
TE = [
    "Thermal expansion is BRICK 2.0's module, unchanged (Wong et al., 2017; 2022): each year's change in thermal-expansion sea level is proportional to that year's change in ocean heat content, ΔTE = α ΔOHC / (A C ρ²), with the ocean surface area A, specific heat C and density ρ fixed at BRICK's values and the expansion coefficient α (kg m⁻³ °C⁻¹) sampled under BRICK's prior, N(0.16, 0.029) truncated to [0.10, 0.24]. The driver is FaIR's full-depth ocean heat content — the mean over the 841 configurations, in 10²² J relative to 1850–1900 — in place of the SNEASY ocean heat BRICK 2.0 is coupled to. The posterior median of α is 0.172 (5–95% 0.155–0.185), within 3% of the value the 0–2000 m observations imply; the 1993–2026 overshoot discussed under Results is the driver, not the coefficient. The thermal-expansion series is scored through a two-coefficient discrepancy term (see Calibration) that is orthogonalised against the ocean-heat shape, so the discrepancy cannot substitute for α.",
]
LWS = [
    "Land-water storage is not modelled in the hindcast: neither BRICK 2.0 nor Ladrillo predicts it, and it is not a calibration target. Where the total is compared with observations (FIG 1, Table 4) the observed series is added to both models' four modelled components — Frederikse et al. (2020) through 2018, then GRACE/GRACE-FO JPL mascons for 2019–2023 (land mass with the ice sheets masked, less the GlaMBIE glacier mass), with the 2023 value held through the 2026 end of the fit window. In projections Ladrillo keeps BRICK 2.0's stochastic land-water module, which is zero before 2019 and thereafter accumulates annual increments drawn from N(0.30, 0.18) mm/yr; the increments are drawn from a fixed seed, so one land-water realisation is shared by every posterior draw and scenario and the contribution is climate-independent (about 0.2 cm by 2024 and about 8 cm by 2300 at the mean rate).",
]
CODE = [
    "Ladrillo is written in Julia (1.12) within the Mimi framework (1.6) as a set of components swapped into MimiBRICK v2.0.0 (Wong et al., 2022): the three-reservoir glacier component and the two-basin, two-channel Greenland component replace BRICK's glacier and Greenland components through Mimi's component-replacement interface, while the Antarctic (DAIS), Antarctic-ocean, thermal-expansion, land-water and global-sum components are BRICK 2.0's own, unchanged. The regional temperature drivers are built outside the components — observed regional series to 2024 (HadCRUT5, area-weighted over each glacier block; southern Greenland, 59–70° N, for the ice sheet), spliced to amplified GMST thereafter with an anchor over the last eleven observed years — so each component sees only the temperature it responds to, and a user can substitute a different climate driver, a different regional-temperature product or a different component without touching the others. The calibration driver samples the 58 parameters with the robust adaptive Metropolis sampler (RobustAdaptiveMetropolisSampler.jl); one model evaluation takes 1–2 ms and the four 2,000,000-iteration chains complete in about three hours on a laptop. Projections use a separate kernel that re-applies each posterior draw and rebuilds its temperature drivers per draw, and a suite of ten regression tests (including byte-identity of the calibrator's likelihood against a frozen reference and reproduction of the shipped hindcast series) is run before release.",
]
AVAIL = [
    "Ladrillo v1.0 — the component code, the calibration and projection drivers, the calibration targets with the scripts that build them from the sources in Table 3, the 10,000-member posterior, and the scripts that produce every figure and table in this paper — is archived at Zenodo under DOI [to be assigned at submission]; development continues at [repository URL]. MimiBRICK v2.0.0 is available at https://github.com/raddleverse/MimiBRICK.jl (Wong et al., 2022). The FaIR 2.2.4 climate ensemble uses the fair-calibrate 1.6.0 constrained parameter set [Smith et al., DOI]. The observational inputs and their versions are listed in Table 3; the derived FaIR forcing files and regional-temperature drivers are included in the archive.",
]
x = insert_after(x, "Thermal Expansion", TE)
x = insert_after(x, "Land water storage", LWS)
x = insert_after(x, "[language, modularity, model calibration]", CODE)
x = insert_after(x, "Code and data availability", AVAIL)

REFS = [
    "References",
    "Akaike, H.: A new look at the statistical model identification, IEEE Trans. Autom. Control, 19, 716–723, https://doi.org/10.1109/TAC.1974.1100705, 1974.",
    "Farinotti, D., Huss, M., Fürst, J. J., Landmann, J., Machguth, H., Maussion, F., and Pandit, A.: A consensus estimate for the ice thickness distribution of all glaciers on Earth, Nat. Geosci., 12, 168–173, https://doi.org/10.1038/s41561-019-0300-3, 2019.",
    "Frederikse, T., Landerer, F., Caron, L., Adhikari, S., Parkes, D., Humphrey, V. W., Dangendorf, S., Hogarth, P., Zanna, L., Cheng, L., and Wu, Y.-H.: The causes of sea-level rise since 1900, Nature, 584, 393–397, https://doi.org/10.1038/s41586-020-2591-3, 2020.",
    "Mengel, M., Levermann, A., Frieler, K., Robinson, A., Marzeion, B., and Winkelmann, R.: Future sea level rise constrained by observations and long-term commitment, P. Natl. Acad. Sci. USA, 113, 2597–2602, https://doi.org/10.1073/pnas.1500515113, 2016.",
    "Nauels, A., Meinshausen, M., Mengel, M., Lorbacher, K., and Wigley, T. M. L.: Synthesizing long-term sea level rise projections – the MAGICC sea level model v2.0, Geosci. Model Dev., 10, 2495–2524, https://doi.org/10.5194/gmd-10-2495-2017, 2017.",
    "Nauels, A., Möller, T., Couplet, V., Kopp, R. E., Kumar, P., Mengel, M., Munday, G., Nicholls, Z. R. J., Ramme, L., Slangen, A. B. A., Smith, C., Weeks, J. H., and Wong, T. E.: Sea Level Emulator Intercomparison Project (SLEIP) Phase 1: Assessing emulated multi-century global mean sea level projections, EGUsphere [preprint], https://doi.org/10.5194/egusphere-2026-3874, 2026.",
    "National Academies of Sciences, Engineering, and Medicine: Valuing Climate Damages: Updating Estimation of the Social Cost of Carbon Dioxide, The National Academies Press, Washington, DC, https://doi.org/10.17226/24651, 2017.",
    "Schwarz, G.: Estimating the dimension of a model, Ann. Stat., 6, 461–464, https://doi.org/10.1214/aos/1176344136, 1978.",
    "Vehtari, A., Gelman, A., Simpson, D., Carpenter, B., and Bürkner, P.-C.: Rank-normalization, folding, and localization: an improved R̂ for assessing convergence of MCMC (with discussion), Bayesian Anal., 16, 667–718, https://doi.org/10.1214/20-BA1221, 2021.",
    "Vihola, M.: Robust adaptive Metropolis algorithm with coerced acceptance rate, Stat. Comput., 22, 997–1008, https://doi.org/10.1007/s11222-011-9269-5, 2012.",
    "Wigley, T. M. L. and Raper, S. C. B.: Extended scenarios for glacier melt due to anthropogenic forcing, Geophys. Res. Lett., 32, L05704, https://doi.org/10.1029/2004GL021238, 2005.",
    "Wong, T. E., Bakker, A. M. R., Ruckert, K., Applegate, P., Slangen, A. B. A., and Keller, K.: BRICK v0.2, a simple, accessible, and transparent model framework for climate and regional sea-level projections, Geosci. Model Dev., 10, 2741–2760, https://doi.org/10.5194/gmd-10-2741-2017, 2017.",
    "Wong, T. E., Rennels, L., Errickson, F., Srikrishnan, V., Bakker, A., Keller, K., and Anthoff, D.: MimiBRICK.jl: A Julia package for the BRICK model for sea-level change in the Mimi integrated modeling framework, J. Open Source Softw., 7, 4556, https://doi.org/10.21105/joss.04556, 2022.",
    "Zekollari, H., et al.: Glacier preservation doubled by limiting warming to 1.5 °C versus 2.7 °C, Science, https://doi.org/10.1126/science.adu4675, 2025. [confirm title/authors]",
    "[Still to add, cited in the text: Dangendorf 2024 (GMSL, Zenodo 10.5281/zenodo.10621070); Forster et al. 2026 (IGCC, ESSD 18, 3889, 10.5194/essd-18-3889-2026); GlaMBIE 2025 (Nature, 10.1038/s41586-024-08545-z); Leclercq et al. 2011; Mouginot et al. 2019; Rignot et al. 2019; Millan et al. 2022; Hock 2023; van Vuuren et al. 2025 (the scenarios; Zenodo 10.5281/zenodo.20713982); the FaIR 2.2.4 and fair-calibrate 1.6.0 papers; ISMIP6 / SICOPOLIS / GlacierMIP3 sources; the Sarofim reduced-complexity-model paper.]",
]
x = insert_after(x, "Acknowledgments.", REFS)

# ---------------- comments ----------------
x = add_comment(x, "Ladrillo v1.0, a spinoff of BRICK",
    "GMD model-description checklist (from Wong et al. 2017 and the GMD author guide): numbered sections; the version number in the title (done); a 'Code and data availability' section pointing at a DOI-archived frozen version at submission (Zenodo, after Tony's team review — text drafted below with placeholders); 'Author contributions'; and, as in Wong 2017 Appendix A, a table of priors and posterior median / 5–95% for all 58 parameters. outputs/ladrillo_posterior_summary.csv is an Aug-10 vintage (52 parameters, not L24) — I can rebuild it for L24 if you want the appendix.")
x = add_comment(x, "Ladrillo is much more sensitive to differences between scenarios",
    "Receipts (High − Very Low, difference of medians at 2300, FIG 6): Greenland Ladrillo +49.5 cm vs BRICK 2.0 +15.0 (≈3×, and ≈ MAGICC-SLR's +55.3); glaciers +14.9 vs +10.6 (≈1.4×). 'Much more' holds for Greenland; for glaciers 'somewhat more' — consider giving the two numbers.")
x = add_comment(x, "Sarofim reduced complexity model paper",
    "Which paper? Please give the citation; the NAS reference is in the list below (NASEM 2017, 10.17226/24651).")
x = add_comment(x, "deliverable-level criterion",
    "'L24' is the internal calibration tag for the shipped Ladrillo v1.0 posterior; I removed it from the captions and this sentence so the paper carries only the version number.")
x = add_comment(x, "so the difference is the ice-sheet modules, not the climate",
    "The climate-swap figure (FIG 11 in the documentation memo) is not in the paper. Either add it here as a figure or keep the numbers without a figure reference (as edited).")
x = add_comment(x, "5–95% widths of 329 and 405 cm at SSP5-8.5 in 2300",
    "SSP5-8.5 numbers inside a van-Vuuren-only results section (the SSP figures were dropped from the paper). The vvH equivalents are one line away in the joint-band outputs if you want a single scenario set.")
x = add_comment(x, "with modest implications for future projections",
    "This reads against the Antarctic-amplification paragraph: a one-sigma change in the amplification moves 2300 Antarctic sea level by ~58 cm on SSP2-4.5, and reverting to DAIS's 1.196 adds 42 cm at 2300. 'Modest' may be right for the high scenarios (24 cm, <5%), not for the middle ones — consider qualifying by scenario.")
x = add_comment(x, "[language, modularity, model calibration]",
    "Filled the language/modularity part below. The '58 parameters', 'Forcing', 'Discrepancy terms', 'Sampler' and 'Convergence' paragraphs are calibration, not code structure — suggest a 'Model calibration' heading above '58 parameters are sampled' (the documentation memo's 'Calibration Approach').")
x = add_comment(x, "Code and data availability",
    "Drafted with placeholders. GMD requires the DOI of the frozen version at submission; per the 09-16 plan that is Zenodo after Tony's team review of the extracted package. The FACTS comparison arm (branch slr-comparison-arm) still has no remote — the 54 experiment outputs behind FIGs 2–6 need a home before this section can be completed.")
x = add_comment(x, "Acknowledgments.",
    "References (inserted below): compiled from what the text cites, GMD (Copernicus) style. DOIs given are ones I could verify from the PDFs in ClaudeDocs/Papers or from Table 3; the bracketed line lists what is still missing. Dangendorf 2024 and van Vuuren 2025 need their journal citations from you.")

save(x)
print("edits applied")
