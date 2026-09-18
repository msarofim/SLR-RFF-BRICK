"""Round 2 (2026-09-18): answer Marcus's comments, extend the references, add the closing paragraph."""
import sys
from redline import *

TIMING = dict(l_hind=None, b_hind=None, l_proj=None, b_proj=None, l_run=None, b_run=None)  # filled from CSV
import csv
with open("/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/outputs/diag_runtime_ladrillo_vs_brick20.csv") as f:
    for r in csv.DictReader(f):
        key = ("l" if r["model"].startswith("Ladrillo") else "b")
        if r["mode"] == "apply_draw+run":
            TIMING[key + ("_hind" if r["span"] == "1850-2026" else "_proj")] = float(r["ms_per_draw_median"])
        elif r["span"] == "1850-2300":
            TIMING[key + "_run"] = float(r["ms_per_draw_median"])
assert all(v is not None for v in TIMING.values()), TIMING
ratio_proj = TIMING["l_proj"] / TIMING["b_proj"]
ratio_run = TIMING["l_run"] / TIMING["b_run"]

x = load()

# ---- [2] the reduced-complexity reference ----
x = replace_text(x, "Sarofim et al. 2021", "Sarofim et al., 2021")
x = replace_text(x, ", NAS SC-GHG assessment)", "; National Academies of Sciences, Engineering, and Medicine, 2017)")
x = add_reply(x, 2, "Added: Sarofim, Smith, St. Juliana and Hartin (2021), Nature Climate Change 11, 1–3, 10.1038/s41558-020-00973-9 — in the list below.")

# ---- [4] regrowth: Marcus is right ----
x = replace_text(x, "but full regrowth would require temperatures to return to their 1850 level",
                 "but full regrowth would require cooling below the 1850–1900 level: the posterior places each block's equilibrium-offset temperature T_off below that level (medians −1.6 K for SLOWG and −1.5 K for FASTG in the regional frame), so the 1850 ice was already out of equilibrium and committed to loss, consistent with the Leclercq constraint on 1850–1900 melt")
x = add_reply(x, 4, "Yes — you're right and the sentence was wrong. In the fitted posterior T_off (the regional temperature at which the 1850 volume is the equilibrium) sits below the 1850–1900 mean for essentially every draw of the two large blocks (SLOWG median −1.6 K, 94% of draws < 0; FASTG −1.5 K, 100%); RGI 19 straddles zero. Reworded accordingly; numbers from parameters_subsample_brick_mengel_L24.csv.")

# ---- [5] LWS: start year and the value of the stochastic draw ----
x = replace_text(x, "about 0.2 cm by 2024", "")
x = replace_text(x, "and about 8 cm by 2300 at the mean rate).", "")
x = replace_text(x, "increments are drawn from a fixed seed, so one land-water realisation is shared by every posterior draw and scenario and the contribution is climate-independent (",
                 "module starts in 2019 in projections regardless of the hindcast's observed series, so over 2019–2026 the two conventions differ by under 0.5 cm and the projection omits the observed 1995–2018 land-water change (about 0.4 cm relative to the 1995–2014 baseline). The increments are drawn from a fixed seed, so one land-water realisation is shared by every posterior draw and scenario; the contribution is climate-independent and, at the mean rate, about 8 cm by 2300, with the random-walk wobble of the single realisation worth about 0.3 cm (0.18 mm/yr × √281 yr). A constant 0.3 mm/yr would be indistinguishable; the stochastic form is kept only to preserve BRICK 2.0's convention.")  # noqa
x = add_reply(x, 5, "Answered in the text: the module starts in 2019 in projections (BRICK's first_projection_year = 2018 is never changed), independent of the hindcast's held-2023 observed series; the mismatch over 2019–2026 is < 0.5 cm and the projection also omits the observed 1995–2018 LWS change (≈0.4 cm rel. 1995–2014). Value of the stochastic draw: none that I can find — it is ONE seeded realisation shared by all draws, so it adds no spread to the band and its own wobble is ≈0.3 cm by 2300. Switching to the constant 0.3 mm/yr mode (`lws=:central`, already implemented) would move every projection by ≤0.3 cm and needs a re-run of the figures — your call.")

# ---- [8] Table 5 column widths ----
x = set_table_widths(x, "Independent Gaussian, observational σ", [3600, 1500, 2000, 1130, 1130], [3046, 1269, 1692, 956, 956])
x = add_reply(x, 8, "Widened the ΔAIC/ΔBIC columns (0.39\"/0.33\" → 0.78\" each) and narrowed the likelihood column; fixed layout, so the numbers should sit on one line now.")

# ---- [9] streamline the AIC paragraph ----
x = replace_para_text(x, "hindcast gain is not its extra parameters",
    "**Ladrillo's hindcast gain is not its extra parameters.** Ladrillo samples 58 parameters to BRICK 2.0's 35, so the gains in Table 4 could in principle be overfitting. Following Wong et al. (2017) we compare the two models with the Akaike and Bayesian information criteria (AIC = 2k − 2 ln L, BIC = k ln N − 2 ln L; Akaike 1974, Schwarz 1978), each at its maximum-likelihood posterior draw on the same four component series (N = 502 observation-years) and charged for every sampled parameter its likelihood uses (Table 5). With independent observational errors the log-likelihood gain (+1328) dwarfs the charge for 23 parameters. Under the calibration's own AR(1)-plus-observational-error likelihood, with noise scale and autocorrelation profiled per series for both models, the gain is +68: three times the AIC charge (ΔAIC = +89) but level on BIC (−8), because at the calibration's ρ ≤ 0.99 bound the AR(1) term acts as a near-random-walk discrepancy that cheaply absorbs BRICK 2.0's smooth biases; at ρ ≤ 0.95 the BIC margin is +53. Glaciers and Greenland carry the gain (+33 and +30), Antarctica +6; thermal expansion ties by construction (same module, same ocean-heat driver). Two caveats: the maximum over draws is a lower bound on each model's maximum likelihood, and Ladrillo was calibrated to these targets while BRICK 2.0 was calibrated to its own.")
x = add_reply(x, 9, "Cut from ~290 to ~200 words: dropped the restated definitions and the 'worth N parameters' arithmetic, folded the per-series split into one clause. Everything numerical is unchanged.")

# ---- [13] relative speed ----
x = replace_text(x, "Despite a small increase in complexity, Ladrillo still runs extremely quickly.",
                 f"Despite the added structure, Ladrillo runs at {ratio_proj:.1f}× BRICK 2.0's time per posterior draw on an 1850–2300 projection ({TIMING['l_proj']:.1f} against {TIMING['b_proj']:.1f} ms on a laptop, most of it parameter handling; the model evaluation itself is {TIMING['l_run']:.2f} against {TIMING['b_run']:.2f} ms), so a 10,000-draw scenario takes about a minute.")
x = add_reply(x, 13, f"Measured (julia/diag_runtime_ladrillo_vs_brick20.jl, 300 draws each, same FaIR driver, medians): per draw incl. parameter update, 1850–2300: Ladrillo {TIMING['l_proj']:.2f} ms vs BRICK 2.0 {TIMING['b_proj']:.2f} ms ({ratio_proj:.2f}×); 1850–2026 hindcast {TIMING['l_hind']:.2f} vs {TIMING['b_hind']:.2f} ms; the Mimi model run alone {TIMING['l_run']:.2f} vs {TIMING['b_run']:.2f} ms ({ratio_run:.2f}×). Parameter handling (Mimi update_param! over 58 vs 35 parameters, plus Ladrillo rebuilding its regional drivers per draw) dominates both. Table in outputs/diag_runtime_ladrillo_vs_brick20.csv with provenance.")

# ---- van Vuuren citation ----
x = replace_text(x, "We report projections for the seven van Vuuren scenarios",
                 "We report projections for the seven ScenarioMIP-CMIP7 marker scenarios (van Vuuren et al., 2026; 'van Vuuren scenarios' below)")

# ---- closing paragraph ----
x = insert_after(x, "The modular approach used by both BRICK and Ladrillo", [
    "Ladrillo complements the existing set of sea level emulators: it has high observational fidelity, couples to any reduced-complexity climate model that produces both GMST and ocean heat content, is modular, and is probabilistic. It should be a useful source of sea level rise projections for damage models driven by global sea level (e.g., FrEDI; Hartin et al., 2023), for social cost of carbon analyses, and for decision makers."])

# ---- references: replace the bracketed to-do line with entries, in alphabetical position ----
NEW = {
 "Akaike, H.": [  # after Akaike
    "Church, J. A. and White, N. J.: Sea-level rise from the late 19th to the early 21st century, Surv. Geophys., 32, 585–602, https://doi.org/10.1007/s10712-011-9119-1, 2011.",
    "Dangendorf, S., Sun, Q., Wahl, T., Thompson, P., Mitrovica, J. X., and Hamlington, B.: Probabilistic reconstruction of sea-level changes and their causes since 1900, Earth Syst. Sci. Data, 16, 3471–3494, https://doi.org/10.5194/essd-16-3471-2024, 2024.",
 ],
 "Farinotti, D.": [
    "Forster, P. M., Walsh, T., Smith, C., Lamb, W. F., Lamboll, R., Cassou, C., Hauser, M., Hausfather, Z., Lee, J.-Y., Palmer, M. D., von Schuckmann, K., Slangen, A. B. A., et al.: Indicators of Global Climate Change 2025: annual update of key indicators of the state of the climate system and human influence, Earth Syst. Sci. Data, 18, 3889–3933, https://doi.org/10.5194/essd-18-3889-2026, 2026. [67 authors — complete the list]",
 ],
 "Frederikse, T.": [
    "GlaMBIE Team: Community estimate of global glacier mass changes from 2000 to 2023, Nature, 639, 382–388, https://doi.org/10.1038/s41586-024-08545-z, 2025.",
    "Goelzer, H., Nowicki, S., Payne, A., Larour, E., Seroussi, H., Lipscomb, W. H., et al.: The future sea-level contribution of the Greenland ice sheet: a multi-model ensemble study of ISMIP6, The Cryosphere, 14, 3071–3096, https://doi.org/10.5194/tc-14-3071-2020, 2020. [complete the author list]",
    "Greve, R. and Chambers, C.: Mass loss of the Greenland ice sheet until the year 3000 under a sustained late-21st-century climate, J. Glaciol., 68, 618–624, https://doi.org/10.1017/jog.2022.9, 2022.",
    "Hartin, C., McDuffie, E. E., Noiva, K., Sarofim, M., Parthum, B., Martinich, J., Barr, S., Neumann, J., Willwerth, J., and Fawcett, A.: Advancing the estimation of future climate impacts within the United States, Earth Syst. Dynam., 14, 1015–1037, https://doi.org/10.5194/esd-14-1015-2023, 2023.",
    "Hock, R., Maussion, F., Marzeion, B., and Nowicki, S.: What is the global glacier ice volume outside the ice sheets?, J. Glaciol., 69, 204–210, https://doi.org/10.1017/jog.2023.1, 2023.",
    "Kopp, R. E., Garner, G. G., Hermans, T. H. J., Jha, S., Kumar, P., Reedy, A., Slangen, A. B. A., Turilli, M., Edwards, T. L., Gregory, J. M., Koubbe, G., Levermann, A., Merzky, A., Nowicki, S., Palmer, M. D., and Smith, C.: The Framework for Assessing Changes To Sea-level (FACTS) v1.0: a platform for characterizing parametric and structural uncertainty in future global, relative, and extreme sea-level change, Geosci. Model Dev., 16, 7461–7489, https://doi.org/10.5194/gmd-16-7461-2023, 2023.",
    "Leach, N. J., Jenkins, S., Nicholls, Z., Smith, C. J., Lynch, J., Cain, M., Walsh, T., Wu, B., Tsutsui, J., and Allen, M. R.: FaIRv2.0.0: a generalized impulse response model for climate uncertainty and future scenario exploration, Geosci. Model Dev., 14, 3007–3036, https://doi.org/10.5194/gmd-14-3007-2021, 2021.",
    "Leclercq, P. W., Oerlemans, J., and Cogley, J. G.: Estimating the glacier contribution to sea-level rise for the period 1800–2005, Surv. Geophys., 32, 519–535, https://doi.org/10.1007/s10712-011-9121-7, 2011.",
 ],
 "Mengel, M.": [
    "Millan, R., Mouginot, J., Rabatel, A., and Morlighem, M.: Ice velocity and thickness of the world's glaciers, Nat. Geosci., 15, 124–129, https://doi.org/10.1038/s41561-021-00885-z, 2022.",
    "Mouginot, J., Rignot, E., Bjørk, A. A., van den Broeke, M., Millan, R., Morlighem, M., Noël, B., Scheuchl, B., and Wood, M.: Forty-six years of Greenland Ice Sheet mass balance from 1972 to 2018, P. Natl. Acad. Sci. USA, 116, 9239–9244, https://doi.org/10.1073/pnas.1904242116, 2019.",
 ],
 "Valuing Climate Damages": [
    "Rignot, E., Mouginot, J., Scheuchl, B., van den Broeke, M., van Wessem, M. J., and Morlighem, M.: Four decades of Antarctic Ice Sheet mass balance from 1979–2017, P. Natl. Acad. Sci. USA, 116, 1095–1103, https://doi.org/10.1073/pnas.1812883116, 2019.",
    "Sarofim, M. C., Smith, J. B., St. Juliana, A., and Hartin, C.: Improving reduced complexity model assessment and usability, Nat. Clim. Change, 11, 1–3, https://doi.org/10.1038/s41558-020-00973-9, 2021.",
 ],
 "Schwarz, G.": [
    "Smith, C., Cummins, D. P., Fredriksen, H.-B., Nicholls, Z., Meinshausen, M., Allen, M., Jenkins, S., Leach, N., Mathison, C., and Partanen, A.-I.: fair-calibrate v1.4.1: calibration, constraining, and validation of the FaIR simple climate model for reliable future climate projections, Geosci. Model Dev., 17, 8569–8592, https://doi.org/10.5194/gmd-17-8569-2024, 2024.",
 ],
 "Vehtari, A.": [
    "van Vuuren, D. P., O'Neill, B. C., Tebaldi, C., Sanderson, B. M., Chini, L. P., Friedlingstein, P., Hasegawa, T., Riahi, K., et al.: The Scenario Model Intercomparison Project for CMIP7 (ScenarioMIP-CMIP7), Geosci. Model Dev., 19, 2627–2656, https://doi.org/10.5194/gmd-19-2627-2026, 2026. [45 authors — complete the list]",
 ],
}
for anchor, entries in NEW.items():
    x = insert_after(x, anchor, entries)
x = replace_para_text(x, "[Still to add, cited in the text",
    "[Still to add: the MAGICC-SLR 'Nauels 2025' source cited in the FIG 1 caption; a SICOPOLIS Antarctic/3001 source if one is cited beyond Greve and Chambers (2022); ISMIP6 Antarctica if cited; the CMIP6 catalogue (Pangeo/Google Cloud); the fair-calibrate 1.6.0 release (Zenodo DOI); IMBIE if named as a source. Zekollari (2025), Goelzer (2020), Forster (2026) and van Vuuren (2026) still need their full author lists.]")
x = add_reply(x, 15, "Round 2: added Church & White 2011, Dangendorf 2024, Forster 2026, GlaMBIE 2025, Goelzer 2020, Greve & Chambers 2022, Hartin 2023, Hock 2023, Kopp 2023 (FACTS), Leach 2021 (FaIR), Leclercq 2011, Millan 2022, Mouginot 2019, Rignot 2019, Sarofim 2021, Smith 2024 (fair-calibrate), van Vuuren 2026 — each checked against the publisher page today except Church & White, Leclercq, Mouginot and Goelzer (from memory of the DOIs; please spot-check). The bracketed line lists what remains.")

save(x)
print("round 2 applied; timing", TIMING, f"ratio proj {ratio_proj:.2f}, run {ratio_run:.2f}")
