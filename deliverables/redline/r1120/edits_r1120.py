"""Round r1120 (2026-11-20) on the r1119 clean copy: wording edits by "Claude" (r1120_data.py), then the style pass
(style_r1120.py, author "Claude (style)"), then two new comments and the fix to Claude's 11-19 sources comment.
Run by build.sh on a fresh copy."""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
W = sys.argv[1]
sys.path.insert(0, HERE)
import edlib  # noqa: E402
import style_r1120  # noqa: E402
from r1120_data import EDITS, INSERTS, REFS, COMMENT_FIX, COMMENTS  # noqa: E402
from xml.sax.saxutils import escape  # noqa: E402

d = edlib.open_doc(W + "/word/document.xml")
for ctx, old, new, why in EDITS:
    edlib.edit(ctx, old, new, why)
for ctx, prefix, new, why in INSERTS:
    edlib.ins(ctx, prefix, new, why)
for before, text, why in REFS:
    d.insert_para(before, text, before=True, why=why)
n_wording = len(d.log)
n_pct = style_r1120.run(d)
d.save()

import comments_lib  # noqa: E402  (reads/writes the saved document.xml)
for phrase, text in COMMENTS:
    comments_lib.comment(phrase, text)
cp = W + "/word/comments.xml"
c = open(cp, encoding="utf8").read()
old, new = escape(COMMENT_FIX[0]), escape(COMMENT_FIX[1])
assert c.count(old) == 1, c.count(old)
open(cp, "w", encoding="utf8").write(c.replace(old, new))

open(os.path.join(W, "..", os.path.basename(W) + "_log.txt"), "w", encoding="utf8").write(
    "\n".join(f"{a} | {b} | {c}" for a, b, c in d.log) + "\n")
print(f"edits_r1120: {n_wording} wording edits (incl. {len(REFS)} references); style: footnote letters in Tables 1-3, "
      f"2 note pointers, {n_pct} % spaces; {len(COMMENTS)} comments + 1 comment text fixed")
