"""Round r1123 edits (2026-11-22) on the 11-22 clean copy (GMD.Ladrillo.v1.2026-11-22.clean.docx = r1122 accepted).
Marcus 11-22: "yes, build r1123 and the submission PDF", after the GMD checklist review found two gaps in the Code and
data availability section. All edits author "Claude".

Receipts:
- GMD code and data policy (geoscientific-model-development.net/policies/code_and_data_policy.html, read 11-22): the
  section gives the archive citation, the means to access other versions, and the licence; the archive covers
  "preprocessing, run control and postprocessing scripts covering every data processing action".
- Licence: Ladrillo.jl LICENSE is MIT and CITATION.cff says `license: MIT`; no file in the repository declares CC BY 4.0
  for non-code content, so the Conclusions' "and CC-BY-4.0 (non-code content)" has no backing (Marcus may reject).
- Comparison outputs: Ladrillo.jl v1.0.0 ships data/comparison/{facts_components_shared_n200, magicc_nauels_components_vv,
  magicc_gmst_vv}.csv as static files (data/comparison/README.md). FACTS origin
  https://github.com/radical-collaboration/facts, model code at tag v1.1.4. MAGICC-SLR access through the probabilistic
  MAGICC repository (Acknowledgements; MAGICC team approval, memory magicc_cmp). MAGICC output may be published (Marcus
  2026-06-18, memory magicc_cmp).
"""

FACTS_URL = "https://github.com/radical-collaboration/facts"

EDITS = [   # (context, old, new, why)
    ("and is released under the MIT licence (code) and CC-BY-4.0 (non-code content).",
     " (code) and CC-BY-4.0 (non-code content).", ".",
     "the repository declares MIT only (LICENSE, CITATION.cff)"),
]

INSERTS = [   # (context, prefix, new, why)
    ("development continues at https://github.com/msarofim/Ladrillo.jl. MimiBRICK v2.0.0",
     "development continues at https://github.com/msarofim/Ladrillo.jl.",
     " Ladrillo is released under the MIT licence.",
     "GMD policy: the section states the licence"),
    ("The README in the archive covers installation, running the calibration and projections, and the input and output "
     "files.",
     "The README in the archive covers installation, running the calibration and projections, and the input and output "
     "files.",
     " The FACTS and MAGICC-SLR outputs shown in Figs. 2, 3 and 6 are included in the archive as static files. FACTS "
     f"v1.1.4 is available at {FACTS_URL}, and the probabilistic MAGICC repository used to run MAGICC-SLR is available "
     "on request from the MAGICC team.",
     "GMD policy: every result's data path; the comparator outputs"),
]

REFS = []
