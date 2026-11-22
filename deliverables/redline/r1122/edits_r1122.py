"""Round r1122 (2026-11-22) on the 11-21 clean copy: the Zenodo DOI, the repository URL and the software reference,
by "Claude" (r1122_data.py). The base has no pending tracked marks. No comments. Run by build.sh on a fresh copy."""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
W = sys.argv[1]
sys.path.insert(0, HERE)
import edlib  # noqa: E402
from r1122_data import EDITS, INSERTS, REFS  # noqa: E402

d = edlib.open_doc(W + "/word/document.xml")
assert not re.search(r"<w:(?:ins|del) ", d.x), "the base was expected to carry no tracked marks"
for ctx, old, new, why in EDITS:
    edlib.edit(ctx, old, new, why)
for ctx, prefix, new, why in INSERTS:
    edlib.ins(ctx, prefix, new, why)
for before, text, why in REFS:
    d.insert_para(before, text, before=True, why=why)
d.save()
open(os.path.join(W, "..", os.path.basename(W) + "_log.txt"), "w", encoding="utf8").write(
    "\n".join(f"{a} | {b} | {c}" for a, b, c in d.log) + "\n")
print(f"edits_r1122: {len(d.log)} edits ({len(REFS)} reference)")
