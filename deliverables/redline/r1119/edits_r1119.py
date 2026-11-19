"""Round r1119 (2026-11-19) on Tony's 11-19 file, his edits accepted: wording edits by Claude (r1119_data.py), then the
notation pass (notation_r1119.py, author 'Claude (notation)'), then comments. Run by build.sh on a fresh copy."""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
W = sys.argv[1]
sys.path.insert(0, HERE)
import edlib  # noqa: E402
import notation_r1119  # noqa: E402
from r1119_data import EDITS, INSERTS, TABLE2, REF_BEFORE, REF_NEW, COMMENTS, TONY_REPLY  # noqa: E402

d = edlib.open_doc(W + "/word/document.xml")
for ctx, old, new, why in EDITS:
    edlib.edit(ctx, old, new, why)
for ctx, prefix, new, why in INSERTS:
    edlib.ins(ctx, prefix, new, why)
d.replace_after(*TABLE2, why="Table 2: MAGICC-SLR's Antarctic law")
d.insert_para(REF_BEFORE, REF_NEW, before=True, why="reference for the MAGICC note")
n_wording = len(d.log)
n_tok, n_sup = notation_r1119.run(d)
d.save()

import comments_lib  # noqa: E402  (reads/writes the saved document.xml)
for phrase, text in COMMENTS:
    comments_lib.comment(phrase, text)
c = open(W + "/word/comments.xml", encoding="utf8").read()
ids = [m.group(1) for m in re.finditer(r'<w:comment w:id="(\d+)"[^>]*w:date="%s"' % re.escape(TONY_REPLY[0]), c)]
assert len(ids) == 1, ids
comments_lib.reply(int(ids[0]), TONY_REPLY[1])

open(os.path.join(W, "..", os.path.basename(W) + "_log.txt"), "w", encoding="utf8").write(
    "\n".join(f"{a} | {b} | {c}" for a, b, c in d.log) + "\n")
print(f"edits_r1119: {n_wording} wording edits; notation: 14 equations, {n_tok} subscripts, {n_sup} superscripts; "
      f"{len(COMMENTS)} comments + 1 reply")
