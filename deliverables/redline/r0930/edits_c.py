"""09-30 edit set C: Marcus's comment replies, caption additions, figure swaps."""
import sys, shutil, re
sys.path.insert(0, "/private/tmp/claude-501/-Users-MarcusMarcus-Documents-2026-CodeProjects-FaIRtoFrEDI/e88c7db1-5ed3-4ee0-bbf2-08bb6c77ecb6/scratchpad/v0930")
from trackedit import Doc
W = sys.argv[1]
R = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/figures/paper/"
d = Doc(W + "/word/document.xml")

# #0/#1 Greenland dates, on the series used (data/observations/t_gis_zones.csv 'south'; 11-yr and 5-yr centred means)
d.replace("warming from 1915-", "warming from about 1920 to 1930, a plateau to about 1960, then cooling to a low around 1990",
          "5-yr min 1920 / 11-yr flat 1915-18; peak 1930-31; plateau to ~1960-63; minimum 1988 (11-yr) / 1991 (5-yr)")
d.replace("1931, then a plateau or a cooling through 1998", "", "replaced above; by 1998 the 11-yr mean is back at plateau level (1.27 K)")
# #5/#6 amp leverage: all per-draw MEANS (diag_ais_amp_leverage_draws_L27.csv; denominators = median total @2300, same arm)
d.replace("(roughly 21% of that scenario", "(roughly 17% of that scenario", "45.8 / 270.4 cm; 21% was the regression figure's share")
d.replace("but only about 23 cm for SSP5-8.5 (under 5%)", "but only about 20 cm for SSP5-8.5 (4%)",
          "per-draw mean 19.9 cm / 509.9; 23.1 was regression slope x sigma")
# #7/#8 pre-observational melt, simplest statement of what L27 scores (calibrate_mcmc_ext.jl:1458-9, 1761-4, 866-8)
d.replace("The pre-observational melt, S(1900) − S(1850) ~ N(2.0, 0.9) cm SLE.",
          "Glacier melt over 1850–1900. The published estimates, N(2.0, 0.9) cm SLE, include about 1.5 cm from ice the "
          "model does not track (uncharted glaciers and the Greenland periphery), so the model's own melt is scored "
          "against N(0.5, 1.2) cm.", "--no-ledger branch: N(0.020-0.015, sqrt(0.009^2+0.0072^2+0.0020^2)) m")
# #9/#10 Rignot footnote (calibrate_mcmc_ext.jl:1400-1409)
d.replace("¹⁷ Published values are a",
          "¹⁷ Scaled by 0.888, the ratio of the DAIS model's idealised ice-sheet area to the grounded area of the "
          "published estimate, giving 1863 ± 118 Gt/yr.", "SMB_TARGET_GT = 2098 x 10.92/12.295")
d.replace("rea-corrected by ×0.888.", "", "folded into the sentence above")
# #11/#12 the SLEIP-rate sentence: models 2006-2025, obs target 2006-2024, OLS not SLEIP's estimator -> delete (Marcus)
d.replace(". On the 2006–2025 rate of total sea level, the metric the SLEIP intercomparison reports, Ladrillo yields "
          "0.363 cm/yr and BRICK 2.0 0.389 relative to 0.392 for the observational target and 0.399 for IGCC.", ".",
          "apply_edits_r6_l27.py:124 windows differ (n=20 vs 19)")
# #4 the Greenland separation target, re-derived on calib 1.6.0 forcing (scratch rerun of
# scope_gis_cool_band_forcing.py + build_gis_matched_targets.py): matched p50 86.9 / 15.3 cm = 5.7 (6.40 on calib 1.4.5)
d.replace("considerably smaller than the ratio of 7.9–31.9 across the process-model literature",
          "well below the 5.7 implied by process-model runs at matched forcing",
          "7.9-31.9 divides band endpoints; matched p50 ratio on calib 1.6.0 forcing = 5.69")

# captions
d.insert_after("Land-water storage is based on observed series and both totals include it.",
               " Observations are the black line, with their ±1.645σ range hatched.", "FIG 1 re-render a62e555")
d.insert_after("joint band, Ladrillo relative to BRICK 2.0.",
               " Ladrillo solid, BRICK 2.0 dashed; the shading is Ladrillo's 5–95% range, shown for the Very Low and "
               "High scenarios only.", "plot_future_components.py BAND_SCENS = first and last scenario")

# figure swaps (current figures/paper renders; re-render byte-identity verified 09-30)
rels_p = W + "/word/_rels/document.xml.rels"
rels = open(rels_p, encoding="utf8").read()
nid = max(int(i) for i in re.findall(r'Id="rId(\d+)"', rels))
SW = [("rId8", "hindcast_components_L27.png", "FIG 1: obs band hatched (a62e555)"),
      ("rId11", "future_components_vv_L27_joint.png", "FIG 4: direct labels (fd24eae)"),
      ("rId12", "vv_gsic_ladrillo_L27_2300.png", "FIG 5: direct labels (fd24eae)")]
from PIL import Image
for rid, png, why in SW:
    nid += 1; new = f"rId{nid}"; tgt = f"media/fig0930_{png}"
    shutil.copy(R + png, W + "/word/" + tgt)
    rels = rels.replace("</Relationships>",
        f'<Relationship Id="{new}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="{tgt}"/></Relationships>')
    w_px, h_px = Image.open(R + png).size
    cy = round(5334000 * h_px / w_px)
    d.swap_image(rid, new, cy, "figures/paper/" + png, why)
open(rels_p, "w", encoding="utf8").write(rels)
d.save()
for o, n, w in d.log: print(f"- {o[:60]!r} -> {n[:60]!r}")
print(len(d.log), "edits")
