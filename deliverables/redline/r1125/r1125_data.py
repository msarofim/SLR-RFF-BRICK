"""Round r1125 edit (2026-11-25) on the 11-22d clean copy, which is the text submitted to GMD on 11-24. GMD's technical
check flagged reference 56 (Mimi.jl v1.6.0) as "No DOI/URL". Marcus 11-25: "use the Software Heritage ID". Author
"Claude".

Receipts (checked 2026-11-25):
  - No DOI exists for Mimi.jl v1.6.0. Zenodo's GitHub archiving of Mimi.jl stops at v1.5.1 (2022-11-28; concept record
    10.5281/zenodo.4321855, 15 versions, newest v1.5.1, read from the Zenodo API and DataCite).
  - Ladrillo.jl v1.0.0's Manifest.toml pins Mimi 1.6.0, git-tree-sha1 0148d5851962182866c53d5d59962c4b6f90ae69.
  - Software Heritage release swh:1:rel:0410476503074d090a8e9aa2221ff23922601af8 is named v1.6.0, dated 2026-04-03; its
    id equals GitHub's v1.6.0 annotated-tag object (gh api .../git/ref/tags/v1.6.0), its target revision is b01ae953,
    and that revision's directory is 0148d585..., the tree the Manifest pins. The resolver URL returns HTTP 200.
"""

SWHID = "swh:1:rel:0410476503074d090a8e9aa2221ff23922601af8"
SWH_URL = "https://archive.softwareheritage.org/" + SWHID
OLD_URL = "https://github.com/mimiframework/Mimi.jl/releases/tag/v1.6.0"
OLD_LOC = "GitHub [code], " + OLD_URL
NEW_LOC = f"Software Heritage [code], {SWHID}, {SWH_URL}"
ENTRY_CTX = "and catawbasam: mimiframework/Mimi.jl, v1.6.0, " + OLD_LOC + ", 2026."
NEW_ENTRY_TAIL = "and catawbasam: mimiframework/Mimi.jl, v1.6.0, " + NEW_LOC + ", 2026."
IN_TEXT = "within the Mimi framework (1.6; Rennels et al., 2026)"

EDITS = [   # (context, old, new, why)
    (ENTRY_CTX, OLD_LOC, NEW_LOC,
     "GMD technical check 11-25: no DOI exists for v1.6.0; Software Heritage archives that exact release (Marcus 11-25)"),
]

INSERTS = []
REFS = []
