"""Round r1122 edits (2026-11-22) on the 11-21 clean copy (GMD.Ladrillo.v1.2026-11-21.clean.docx, md5 940c1c12;
Marcus 11-22: "build r1122 on the 11-21 clean"). It carries no pending tracked marks. All edits author "Claude".

Receipts:
- Zenodo version DOI 10.5281/zenodo.24445689, reserved by Marcus 2026-11-22 (draft saved; resolves once published).
  Ladrillo.jl f056a7d, tag v1.0.0; CITATION.cff carries the same DOI and date-released 2026-11-22.
- Repository URL: https://github.com/msarofim/Ladrillo.jl (public at submission, Marcus 11-21).
- Citation style follows the paper's MimiBRICK-posterior citation "(...; Wong et al., 2026, https://doi.org/...)" and
  its "Zenodo [data set]" reference entries; software is "[code]" (Copernicus). A single-author entry goes before the
  same first author's multi-author entries.
- "every figure and table" -> "every figure and the computed tables": Tables 1-3 are compiled from the literature,
  not produced by code (proposed 11-22; Marcus can reject the mark).
"""

DOI = "10.5281/zenodo.24445689"
URL = "https://github.com/msarofim/Ladrillo.jl"

EDITS = [   # (context, old, new, why)
    ("the scripts that produce every figure and table in this paper", "every figure and table",
     "every figure and the computed tables", "Tables 1-3 are compiled, not computed"),
    ("is archived at Zenodo under DOI [to be assigned at submission]", " under DOI [to be assigned at submission]",
     f" (Sarofim, 2026, https://doi.org/{DOI})", "Zenodo version DOI"),
    ("development continues at [repository URL].", "[repository URL]", URL, "repository URL"),
]

INSERTS = []

REFS = [   # (start of the reference entry the new one goes BEFORE, new entry, why)
    ("Sarofim, M. C., Smith, J. B.",
     "Sarofim, M. C.: Ladrillo.jl: a calibrated reduced-complexity emulator of global mean sea level rise, v1.0.0, "
     f"Zenodo [code], https://doi.org/{DOI}, 2026.", "software reference"),
]
