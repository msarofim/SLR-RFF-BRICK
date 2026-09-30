"""Replies to Marcus's comments and new Claude comments. String edits only; text is never changed."""
import re, subprocess, sys
from xml.sax.saxutils import escape

W = sys.argv[1]
SK = ("/Users/MarcusMarcus/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/"
      "bde964e6-4558-410f-b23a-3b83edafdcf0/a8b27aae-cf9d-41c6-8c2f-bc82579b92b8/skills/docx")
U, D = W, W + "/word/document.xml"
REF = '<w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="%s"/></w:r>'
RUN_RE = re.compile(r'<w:r(?: [^>]*)?>(?:(<w:rPr>(?:(?!</w:rPr>).)*</w:rPr>))?'
                    r'<w:t(?: xml:space="preserve")?>([^<]*)</w:t></w:r>', re.S)


def add(text, parent=None):
    cmd = ["python", SK + "/scripts/comment.py", U, text, "--author", "Claude", "--initials", "CL"]
    if parent is not None:
        cmd += ["--parent", str(parent)]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    return int(re.search(r"id=(\d+)", out).group(1))


def reply(parent, text):
    cid = add(text, parent)
    x = open(D, encoding="utf8").read()
    s, e = '<w:commentRangeStart w:id="%d"/>' % parent, '<w:commentRangeEnd w:id="%d"/>' % parent
    assert x.count(s) == 1 and x.count(e) == 1, parent
    x = x.replace(s, s + '<w:commentRangeStart w:id="%d"/>' % cid)
    x = x.replace(e, '<w:commentRangeEnd w:id="%d"/>' % cid + e)
    r = '<w:commentReference w:id="%d"/>' % parent
    i = x.index(r); j = x.index("</w:r>", i) + len("</w:r>")
    x = x[:j] + REF % cid + x[j:]
    open(D, "w", encoding="utf8").write(x)
    print("reply %d -> %d" % (cid, parent))


def comment(phrase, text):
    """Anchor a new comment on `phrase`, which must sit in exactly one plain (untracked) run."""
    x = open(D, encoding="utf8").read()
    p = escape(phrase)
    hits = [m for m in RUN_RE.finditer(x) if p in m.group(2)]
    assert len(hits) == 1 and x.count(p) == 1, (len(hits), x.count(p), phrase[:60])
    m = hits[0]
    pre = x[max(0, m.start() - 400):m.start()]
    assert pre.rfind("<w:ins ") <= pre.rfind("</w:ins>") and pre.rfind("<w:del ") <= pre.rfind("</w:del>"), \
        "phrase is inside a tracked change: " + phrase[:50]
    cid = add(text)
    rpr, t = m.group(1) or "", m.group(2)
    i = t.index(p)
    mk = lambda s: ('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr, s)) if s else ""
    new = (mk(t[:i]) + '<w:commentRangeStart w:id="%d"/>' % cid + mk(p)
           + '<w:commentRangeEnd w:id="%d"/>' % cid + REF % cid + mk(t[i + len(p):]))
    x = x[:m.start()] + new + x[m.end():]
    open(D, "w", encoding="utf8").write(x)
    print("comment %d on: %s" % (cid, phrase[:60]))


