"""10-01e edit set N (Marcus 10-01): the land-water-in-calibration clause, and Marcus's abstract sentence.

1. Land water: the calibration's land water is MimiBRICK's stylized series (0 through 2018, then 0.30 mm/yr;
   MimiBRICK.jl:132-134, pinned by calibrate_mcmc_ext.jl lws=:central), and it reaches the fit only
   through DAIS's sea-level feedback (the scored components exclude land water). Substituting the observed
   series moves the Antarctic contribution by at most 0.014 cm (95th percentile of the per-draw maximum,
   1900-2025) and 0.012 cm to 2300, on all 2,000 L27 projection draws (scratchpad dais_slfb, 10-01).
2. Abstract: Marcus's sentence, with the numbers from scope_ladrillo_vs_brick20_scorecard_L27.csv (window
   "full", 1900-2025: RMSE ratios 0.059 / 0.205 / 0.279 / 0.871) and Table 5 (AR(1), rho <= 0.99:
   dAIC +89, dBIC +26; k 50 vs 35). Changes from his draft: comparator and window named, RMSE/AIC/BIC
   spelled out (GMD: define abbreviations in the abstract), the signs explained, "demonstrate ... not
   overfitting" softened to "indicating".
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edlib
from edlib import edit, ins

d = edlib.open_doc(sys.argv[1] + "/word/document.xml")

ins("; both take it from observations", "; both take it from observations",
    ", except in calibration, where a stylized series (zero through 2018, then 0.30 mm yr⁻¹) reaches the"
    " fit only through the DAIS sea-level feedback and changes the Antarctic contribution by less than"
    " 0.02 cm relative to the observed series",
    "land water in calibration (Marcus 10-01)")

ins(". The paper also places Ladrillo", ".",
    " These changes improve Ladrillo’s 1900–2025 hindcast relative to BRICK 2.0, with root-mean-square error"
    " (RMSE) reductions of 94% for Antarctica, 79% for glaciers, 72% for Greenland, and 13% for thermal"
    " expansion. The Akaike and Bayesian information criteria (AIC and BIC) both favour Ladrillo (by 89 and"
    " 26), indicating that it is not overfitting despite 15 more parameters.",
    "abstract numbers (Marcus 10-01 draft sentence)")

d.save()
for c, ch, w in d.log:
    print(f"- {c[:50]!r}: {ch[:100]}  [{w}]")
print(f"{len(d.log)} edits")
