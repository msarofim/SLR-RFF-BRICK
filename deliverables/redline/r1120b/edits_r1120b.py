"""Round r1120b (2026-11-20; r1120 + Table 9.11 + resolved sources comment) on the r1119 clean copy: wording edits by "Claude" (r1120b_data.py), then the style pass
(style_r1120.py, author "Claude (style)"), then two new comments and the fix to Claude's 11-19 sources comment.
Run by build.sh on a fresh copy."""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
W = sys.argv[1]
sys.path.insert(0, HERE)
import edlib  # noqa: E402
import style_r1120  # noqa: E402
from r1120b_data import EDITS, INSERTS, REFS, COMMENT_FIX, COMMENTS, RESOLVE  # noqa: E402
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

# r1120b: reply to the sources comment, then resolve the thread (Word's "Resolve": w15:done="1" on every comment in it)
c = open(cp, encoding="utf8").read()
txt = lambda s: "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", s))
hits = [m for m in re.finditer(r'<w:comment w:id="(\d+)"[^>]*>.*?</w:comment>', c, re.S)
        if txt(m.group(0)).startswith(escape(RESOLVE[0]))]
assert len(hits) == 1, len(hits)
parent = int(hits[0].group(1))
parent_pids = re.findall(r'w14:paraId="([0-9A-F]+)"', hits[0].group(0))
comments_lib.reply(parent, RESOLVE[1])
c = open(cp, encoding="utf8").read()
rep = [m for m in re.finditer(r'<w:comment w:id="(\d+)"[^>]*>.*?</w:comment>', c, re.S)
       if txt(m.group(0)).startswith("Claude 11-20: checked.")]
assert len(rep) == 1, len(rep)
pids = parent_pids + re.findall(r'w14:paraId="([0-9A-F]+)"', rep[0].group(0))
xp = W + "/word/commentsExtended.xml"
ce = open(xp, encoding="utf8").read()
for pid in pids:
    pat = re.compile(r'(<w15:commentEx w15:paraId="%s"[^>]*w15:done=")0(")' % pid)
    assert len(pat.findall(ce)) == 1, ("commentEx", pid)
    ce = pat.sub(r"\g<1>1\2", ce)
open(xp, "w", encoding="utf8").write(ce)
print(f"resolved comment {parent} and its reply ({len(pids)} commentEx flags)")

open(os.path.join(W, "..", os.path.basename(W) + "_log.txt"), "w", encoding="utf8").write(
    "\n".join(f"{a} | {b} | {c}" for a, b, c in d.log) + "\n")
print(f"edits_r1120b: {n_wording} wording edits (incl. {len(REFS)} references); style: footnote letters in Tables 1-3, "
      f"2 note pointers, {n_pct} % spaces; {len(COMMENTS)} comments + 1 comment text fixed")
