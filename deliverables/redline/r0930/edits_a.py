"""09-30 edit set A: Table 5 (equal draws), session-verified fixes, citation style, figure swaps."""
import sys, shutil, re
sys.path.insert(0, "/private/tmp/claude-501/-Users-MarcusMarcus-Documents-2026-CodeProjects-FaIRtoFrEDI/e88c7db1-5ed3-4ee0-bbf2-08bb6c77ecb6/scratchpad/v0930")
from trackedit import Doc
W = sys.argv[1]
d = Doc(W + "/word/document.xml")

# ---- Table 5 (Marcus 09-30: equal draws). outputs/ic_ladrillo_vs_brick20_L27{,_rho0.95,_rho0.9}.md @ 63e4a88
# rows done bottom-up so each anchor is still a plain run when used
d.replace_after("225.9 / 106.9", "+208", "+210", "rho<=0.90 dAIC 210.2")
d.replace_after("225.9 / 106.9", "+145", "+147", "rho<=0.90 dBIC 146.9")
d.replace("225.9 / 106.9", "227.0 / 106.9", "rho<=0.90 Ladrillo lnL max, 10k draws")
d.replace_after("233.8 / 148.2", "+141", "+145", "rho<=0.95 dAIC 145.2")
d.replace_after("233.8 / 148.2", "+78", "+82", "rho<=0.95 dBIC 81.9")
d.replace("233.8 / 148.2", "235.8 / 148.2", "rho<=0.95 Ladrillo lnL max, 10k draws")
d.replace_after("238.0 / 180.9", "+84", "+89", "rho<=0.99 dAIC 88.9")
d.replace_after("238.0 / 180.9", "+21", "+26", "rho<=0.99 dBIC 25.7")
d.replace("238.0 / 180.9", "240.4 / 180.9", "rho<=0.99 Ladrillo lnL max, 10k draws")
d.replace("ln L is the maximum over posterior draws.",
          "ln L is the maximum over 10,000 posterior draws of each model.",
          "equal draw counts (was 2,000 Ladrillo vs 10,000 BRICK 2.0)")
# ¶80 text
d.replace("the gain is +57: nearly four times the AIC charge (ΔAIC = +84) and positive on BIC (+21)",
          "the gain is +60: nearly four times the AIC charge (ΔAIC = +89) and positive on BIC (+26)",
          "dlnL 59.5, dAIC 88.9, dBIC 25.7")
d.replace("at ρ ≤ 0.95 the BIC margin is +78", "at ρ ≤ 0.95 the BIC margin is +82", "81.9")
d.replace("Glaciers and Greenland are the primary source of the gain (+30 and +24)",
          "Glaciers and Greenland are the primary source of the gain (+26 and +30)",
          "per-series dlnL at the joint max draw: gsic 26.0, gis 29.7, ais 3.8")

# ---- session-verified fixes (notes/gmd_nextpass_prep_2026-09-29.md, table A)
d.replace("each by about two of IMBIE’s standard deviations",
          "by 2.9 and 1.8 of IMBIE’s standard deviations, respectively",
          "diag_imbie2026_vs_targets_windows_L27.csv: AIS -2.92, GIS +1.84 on IMBIE sigma alone (same basis as the 2.6 sigma)")
d.replace("to within 8 % in every window", "to within about 8 % in every window", "2003–10 is −8.1 %")
d.replace("1.22–1.29×", "1.24–1.29×", "diag_te_rate_attribution_L27.csv: 1.236 / 1.285 on 1993–2026; 1.215 was 1993–2024")
d.replace("an open-source (MIT) licence", "the MIT licence (code) and CC-BY-4.0 (non-code content)",
          "LICENSE (MIT) + LICENSE-CONTENT (CC-BY-4.0)")
d.replace("reflect differences in reservoir count, driver, and posterior",
          "reflect differences in equilibrium curve, reservoir count, driver, and posterior",
          "glaciers_nu3_component.jl:92 analytic S_eq vs MAGICC's tabulated S_eq(T)")

# ---- citation style (Copernicus) and missing citations for listed references
d.replace("sampled on the Parkes and Marzeion range", "sampled on the Parkes and Marzeion (2018) range", "reference added")
d.replace("(Wong et al., 2017; 2022)", "(Wong et al., 2017, 2022)", "style")
d.replace("(Vihola 2012)", "(Vihola, 2012)", "style")
d.replace("split-R̂ of Vehtari et al. 2021)", "split-R̂ of Vehtari et al., 2021)", "style")
d.replace("Akaike 1974, Schwarz 1978", "Akaike, 1974; Schwarz, 1978", "style")
d.replace("response-time anchors at 1.5 and 3.0 K; Zekollari et al. 2025)",
          "response-time anchors at 1.5 and 3.0 K; Zekollari et al., 2025)", "style")
d.replace("based on Farinotti et al. 2019 excluding RGI region 5 (Millan 2022 has similar",
          "based on Farinotti et al. (2019) excluding RGI region 5 (Millan et al., 2022, have similar", "style")
d.replace("share the Nauels 2017 transient", "share the Nauels et al. (2017) transient", "style")
d.replace("anchoring the Antarctic flux scale to Rignot 2019", "anchoring the Antarctic flux scale to Rignot et al. (2019)", "style")
d.replace("(Dangendorf 2024) is an out-of-sample check", "(Dangendorf et al., 2024) is an out-of-sample check", "style")
d.replace("the total against Dangendorf 2024", "the total against Dangendorf et al. (2024)", "style")
d.replace("Farinotti 2019 gives 32.4", "Farinotti et al. (2019) give 32.4", "style")
d.replace("Based on Farinotti 2019 minus", "Based on Farinotti et al. (2019) minus", "style")
d.replace("SLEIP entries from the SLEIP preprint (Tables 2 and 6, §3)",
          "SLEIP entries from Nauels et al. (2026; Tables 2 and 6, §3)", "cite the preprint")
d.replace("to a CMIP6 based one", "to a CMIP6 based one (Eyring et al., 2016)", "Eyring 2016 was listed, never cited")
d.replace("(fair-calibrate 1.6.0, 841-member climate ensemble)",
          "(fair-calibrate 1.6.0, 841-member climate ensemble; Leach et al., 2021; Smith et al., 2024)",
          "Leach 2021 listed, never cited; Smith 2024 cited only in data availability")
d.replace("BRICK’s Antarctic likelihood is IMBIE 1992–2017", "BRICK’s Antarctic likelihood is IMBIE 1992–2017 (IMBIE Team, 2018)",
          "IMBIE Team 2018 referred to only by name")
d.replace("the GlaMBIE series spliced in from 2019 onward", "the GlaMBIE series (GlaMBIE Team, 2025) spliced in from 2019 onward",
          "GlaMBIE Team 2025 referred to only by name")
d.replace("with a Mengel-style equilibrium volume ", "with a Mengel-style (Mengel et al., 2016) equilibrium volume ",
          "Mengel 2016 referred to only by name")
d.replace(" driven by a Nauels-ν transient,", " driven by a Nauels-ν transient (Nauels et al., 2017),",
          "Nauels 2017 referred to only by name")
d.replace("informed by ISMIP6 at 2100 and SICOPOLIS at 2300 and 3001",
          "informed by ISMIP6 at 2100 (Goelzer et al., 2020) and SICOPOLIS at 2300 and 3001 (Greve and Chambers, 2022)",
          "Goelzer 2020 / Greve and Chambers 2022 listed, never cited")
d.replace("Gelman–Rubin potential scale reduction factor", "Gelman–Rubin potential scale reduction factor (Gelman and Rubin, 1992)",
          "cited, not listed -> reference added")
d.save()
for o, n, w in d.log: print(f"- {o[:70]!r} -> {n[:70]!r}")
print(len(d.log), "edits")
