"""10-01b: replies to the open comments, and one new note. Text is never changed here."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comments_lib import comment, reply

reply(0, "MimiBRICK has no Zenodo archive of the v2.0.0 code (checked 10-01). The JOSS software archive, "
         "10.5281/zenodo.7011156, is v1.1.0 and its concept record holds nothing later. 10.5281/zenodo.20592337 is "
         "v2.0.0 model OUTPUT (a dataset), not code. Software Heritage holds the v2.0.0 tag (commit 11b2dff). "
         "Cleanest fix: Tony mints a Zenodo release of v2.0.0; otherwise cite the Software Heritage ID. "
         "Mimi 1.6.0 (the version in the Manifest) also has no Zenodo record, so the all-versions DOI plus '1.6' "
         "stays. A user-manual pointer has been added to this section.")
reply(1, "Möller fixed (10-01b; in the Acknowledgements, now after the Appendix). Still open: the Wellcome grant "
         "number, if there is one.")
reply(2, "Relabelled to 2025 throughout (10-01b). Re-running Table 4 and all three Table 5 arms gives identical "
         "values. FIG 1 was re-rendered to end in 2025. The thermal-expansion ratios were NOT label-only: "
         "diag_te_rate_attribution compared model and FaIR rates through 2026 with observed rates that end in 2025 "
         "(IGCC 2024). On matched spans they are Ladrillo 1.22×, BRICK 2.0 1.16×, FaIR 1.21–1.27× (were "
         "1.23 / 1.17 / 1.24–1.29). The pre-fix outputs are in outputs/quarantine/20261001_te_rate_window_mismatch/.")
reply(3, "Receipt now committed: python/diag_facts_gis_extrap_receipt.py → "
         "outputs/diag_facts_gis_extrap_receipt_vvHL2300.csv. It gives 46.5 cm (default) and 111.6 cm (fit evaluated "
         "through 2300) at 2300, paired seed, identical through 2100.")
reply(4, "Receipt now committed: python/diag_gis_timescales.py → outputs/diag_gis_timescales_L27.csv, 109.3 yr "
         "(62–191) and 289.3 yr (142–663).")
comment("is used for the hindcast",
        "From the equation extraction (10-01b): in the CALIBRATION, land water enters only through DAIS's sea-level "
        "feedback, and it uses a stylised series (zero before 2018, then 0.3 mm/yr), not this observed series. The "
        "observed series is added to the hindcast totals (FIG 1, Table 4) and drives the projections. One clause "
        "here would make that explicit.")
