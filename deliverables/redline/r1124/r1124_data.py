"""Round r1124 edit (2026-11-22) on the 11-22c clean copy (r1123 accepted, Fig. 5 at 300 dpi). Marcus 11-22: "yes,
extend the sentence", i.e. the r1123 comparison-outputs sentence now names what the re-cut archive adds. Author "Claude".

Receipt: Ladrillo.jl v1.0.0 at 46a93de ships comparison/ (FACTS run configurations, run scripts and extraction script;
the MAGICC-SLR extraction scripts; comparison/README.md and MANIFEST.csv), CHANGELOG 2026-11-22b.
"""

FACTS_URL = "https://github.com/radical-collaboration/facts"
CLAUSE = ", together with the FACTS run configurations and the scripts that extracted both models' outputs"

EDITS = [   # (context, old, new, why)
    ("outputs shown in Figs. 2, 3 and 6 are included in the archive as static files.",
     " as static files.", " as static files" + CLAUSE + ".",
     "the re-cut archive includes comparison/ (Ladrillo.jl 46a93de)"),
]

INSERTS = []
REFS = []
