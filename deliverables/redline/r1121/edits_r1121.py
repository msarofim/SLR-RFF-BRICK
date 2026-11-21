"""Round r1121 (2026-11-21) on Marcus's save of the 11-20c clean copy: wording edits by "Claude" (r1121_data.py).
Marcus's pending tracked mark(s) are left exactly as they are. No comments. Run by build.sh on a fresh copy."""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
W = sys.argv[1]
sys.path.insert(0, HERE)
import edlib  # noqa: E402
from r1121_data import EDITS, INSERTS  # noqa: E402

N_MARCUS = 1   # his fast-dynamics insertion (11-21 save)
d = edlib.open_doc(W + "/word/document.xml")
marcus_before = re.findall(r'<w:(?:ins|del) [^>]*w:author="Marcus Sarofim".*?</w:(?:ins|del)>', d.x, re.S)
for ctx, old, new, why in EDITS:
    edlib.edit(ctx, old, new, why)
for ctx, prefix, new, why in INSERTS:
    edlib.ins(ctx, prefix, new, why)
n_wording = len(d.log)
marcus_after = re.findall(r'<w:(?:ins|del) [^>]*w:author="Marcus Sarofim".*?</w:(?:ins|del)>', d.x, re.S)
assert marcus_before == marcus_after and len(marcus_after) == N_MARCUS, "Marcus's tracked marks changed"
d.save()
open(os.path.join(W, "..", os.path.basename(W) + "_log.txt"), "w", encoding="utf8").write(
    "\n".join(f"{a} | {b} | {c}" for a, b, c in d.log) + "\n")
print(f"edits_r1121: {n_wording} edits; Marcus's {N_MARCUS} mark(s) unchanged")
