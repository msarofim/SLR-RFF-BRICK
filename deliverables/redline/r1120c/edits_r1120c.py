"""Round r1120c (2026-11-20) on Marcus's 10:02 save: wording edits by "Claude" (r1120c_data.py), then the notation pass
(notation_r1120c.py, author "Claude (notation)"). Marcus's three pending tracked marks are left exactly as they are.
No comments (he deleted them all). Run by build.sh on a fresh copy."""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
W = sys.argv[1]
sys.path.insert(0, HERE)
import edlib  # noqa: E402
import notation_r1120c  # noqa: E402
from r1120c_data import EDITS, INSERTS  # noqa: E402

d = edlib.open_doc(W + "/word/document.xml")
marcus_before = re.findall(r'<w:(?:ins|del) [^>]*w:author="Marcus Sarofim".*?</w:(?:ins|del)>', d.x, re.S)
for ctx, old, new, why in EDITS:
    edlib.edit(ctx, old, new, why)
for ctx, prefix, new, why in INSERTS:
    edlib.ins(ctx, prefix, new, why)
n_wording = len(d.log)
notation_r1120c.run(d)
marcus_after = re.findall(r'<w:(?:ins|del) [^>]*w:author="Marcus Sarofim".*?</w:(?:ins|del)>', d.x, re.S)
assert marcus_before == marcus_after and len(marcus_after) == 3, "Marcus's tracked marks changed"
d.save()
open(os.path.join(W, "..", os.path.basename(W) + "_log.txt"), "w", encoding="utf8").write(
    "\n".join(f"{a} | {b} | {c}" for a, b, c in d.log) + "\n")
print(f"edits_r1120c: {n_wording} wording edits; notation: {len(d.log) - n_wording} steps; Marcus's 3 marks unchanged")
