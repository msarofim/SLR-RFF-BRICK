"""09-30 edit set D: Greenland amplification sentence on the JOINT arm (Marcus reply to #2)."""
import sys
sys.path.insert(0, "/private/tmp/claude-501/-Users-MarcusMarcus-Documents-2026-CodeProjects-FaIRtoFrEDI/e88c7db1-5ed3-4ee0-bbf2-08bb6c77ecb6/scratchpad/v0930")
from trackedit import Doc
d = Doc(sys.argv[1] + "/word/document.xml")
d.replace("an additional 1 cm (SSP1-2.6, 2300) to 8 cm (SSP5-8.5, 2300) (using a fixed-driver)",
          "an additional 0.7 cm (SSP1-2.6, 2300) to 7.6 cm (SSP5-8.5, 2300)",
          "joint arm, paired per-draw median of the Greenland component, shape-constant minus shipped "
          "(outputs/scope_slr_fairunc_draws_ssp{126,585}_spliced_L27_tap4p69K_V5p64m_tau800_gis_amp_shape_const.csv)")
d.save()
for o, n, w in d.log: print(f"- {o[:70]!r} -> {n[:70]!r}")
