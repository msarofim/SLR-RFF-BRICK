"""Round r1115 on Marcus's clean copy (no tracked changes): the same Code and data availability passage and typo fix as
plain text, the two clean-only fixes, and the two stale comments marked resolved. Never writes the base.

    python clean_r1115.py <clean base.docx> <workdir> <out.docx>
"""
import os, re, shutil, subprocess, sys, zipfile
from xml.sax.saxutils import escape
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from r1115_data import AVAIL_ANCHOR, AVAIL_NEW, TYPO_CTX, TYPO_OLD, TYPO_NEW, STALE_COMMENTS, CLEAN_ONLY  # noqa: E402
from comments_done import mark_done  # noqa: E402

base, W, out = sys.argv[1:4]
assert not os.path.exists(W) and not os.path.exists(out)
os.makedirs(W)
with zipfile.ZipFile(base) as z:
    z.extractall(W)
p = W + "/word/document.xml"
x = open(p, encoding="utf8").read()
assert "<w:ins " not in x and "<w:del " not in x, "the clean base has tracked changes"


def once(x, old, new):
    o, n = escape(old), escape(new)
    assert x.count(o) == 1, (old[:50], x.count(o))
    return x.replace(o, n)


x = once(x, AVAIL_ANCHOR, AVAIL_ANCHOR + AVAIL_NEW)
x = once(x, TYPO_CTX, TYPO_CTX.replace(TYPO_OLD, TYPO_NEW, 1))
## regrowth: the two pieces are adjacent runs, "...each block’s</w:t></w:r><w:r ...><w:t>1850 ice extent..."
a, b = CLEAN_ONLY[0]
m = re.search(re.escape(escape(a)) + r'(</w:t></w:r><w:r(?: [^>]*)?><w:t(?: xml:space="preserve")?>)' + re.escape(escape(b)), x)
assert m and len(re.findall(re.escape(escape(a)), x)) == 1, "regrowth runs not adjacent"
x = x[:m.start()] + escape(a) + m.group(1).replace("<w:t>", '<w:t xml:space="preserve">') + " " + escape(b) + x[m.end():]
x = once(x, *CLEAN_ONLY[1])
open(p, "w", encoding="utf8").write(x)
done = [mark_done(W, f) for f in STALE_COMMENTS]
subprocess.run(["zip", "-q", "-X", "-r", "-D", os.path.abspath(out), "."], cwd=W, check=True)
print(f"clean_r1115: 4 plain-text edits; comments {done} marked resolved -> {out}")
