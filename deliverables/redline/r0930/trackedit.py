"""Tracked edits on word/document.xml by STRING operations (never ElementTree, which renames
namespace prefixes and corrupts the file). Every change is a <w:ins>/<w:del> by AUTHOR.

A phrase must sit inside ONE run's single <w:t> (merge_runs.py has been applied). Each call
asserts the phrase occurs exactly once in the document, so an edit can never land in the wrong
place silently.
"""
import re
from xml.sax.saxutils import escape

AUTHOR, DATE = "Claude", "2026-09-30T00:00:00Z"
RUN_RE = re.compile(r'<w:r(?: [^>]*)?>(?:(<w:rPr>(?:(?!</w:rPr>).)*</w:rPr>))?'
                    r'<w:t(?: xml:space="preserve")?>([^<]*)</w:t></w:r>', re.S)


class Doc:
    def __init__(self, path):
        self.path = path
        self.x = open(path, encoding="utf8").read()
        self.nid = max(int(i) for i in re.findall(r'w:id="(\d+)"', self.x)) + 5000
        self.log = []

    def _id(self):
        self.nid += 1
        return self.nid

    @staticmethod
    def _t(text):
        return f'<w:t xml:space="preserve">{text}</w:t>'

    def _run(self, rpr, text):
        return f'<w:r>{rpr or ""}{self._t(text)}</w:r>' if text else ""

    def _ins(self, rpr, text):
        return (f'<w:ins w:id="{self._id()}" w:author="{AUTHOR}" w:date="{DATE}">'
                f'<w:r>{rpr or ""}{self._t(text)}</w:r></w:ins>') if text else ""

    def _del(self, rpr, text):
        return (f'<w:del w:id="{self._id()}" w:author="{AUTHOR}" w:date="{DATE}">'
                f'<w:r>{rpr or ""}<w:delText xml:space="preserve">{text}</w:delText></w:r></w:del>'
                ) if text else ""

    def _locate(self, old_esc):
        hits = [m for m in RUN_RE.finditer(self.x) if old_esc in m.group(2)]
        total = self.x.count(old_esc)
        if len(hits) != 1 or total != 1:
            raise SystemExit(f"*** phrase must occur exactly once inside one run "
                             f"(runs {len(hits)}, raw {total}): {old_esc[:90]!r}")
        return hits[0]

    def replace(self, old, new, why=""):
        """Tracked replacement of `old` by `new` (either may be ''). Plain text in, escaped here."""
        o, n = escape(old), escape(new)
        m = self._locate(o)
        rpr, txt = m.group(1), m.group(2)
        i = txt.index(o)
        out = (self._run(rpr, txt[:i]) + self._del(rpr, o) + self._ins(rpr, n)
               + self._run(rpr, txt[i + len(o):]))
        self.x = self.x[:m.start()] + out + self.x[m.end():]
        self.log.append((old, new, why))

    def delete(self, old, why=""):
        self.replace(old, "", why)

    def insert_after(self, anchor, new, why=""):
        """Tracked insertion of `new` immediately after `anchor` (anchor text unchanged)."""
        a = escape(anchor)
        m = self._locate(a)
        rpr, txt = m.group(1), m.group(2)
        j = txt.index(a) + len(a)
        out = self._run(rpr, txt[:j]) + self._ins(rpr, escape(new)) + self._run(rpr, txt[j:])
        self.x = self.x[:m.start()] + out + self.x[m.end():]
        self.log.append((anchor + " [+]", new, why))

    def save(self):
        open(self.path, "w", encoding="utf8").write(self.x)


# ---- 2026-09-30 additions ---------------------------------------------------------------------
def _in_tracked(x, pos):
    """True if `pos` sits inside an open <w:ins>/<w:del> (so a plain-run search must skip it)."""
    pre = x[max(0, pos - 3000):pos]
    return pre.rfind("<w:ins ") > pre.rfind("</w:ins>") or pre.rfind("<w:del ") > pre.rfind("</w:del>")


def _para_bounds(x, pos):
    s = max(x.rfind("<w:p ", 0, pos), x.rfind("<w:p>", 0, pos))
    e = x.index("</w:p>", pos) + len("</w:p>")
    return s, e


def _add_methods():
    def replace_after(self, anchor, old, new, why=""):
        """Tracked replace of the FIRST plain-run occurrence of `old` after the unique `anchor`
        (for values that repeat, e.g. table cells)."""
        a, o, n = escape(anchor), escape(old), escape(new)
        assert self.x.count(a) == 1, ("anchor not unique", anchor[:60], self.x.count(a))
        start = self.x.index(a)
        for m in RUN_RE.finditer(self.x, start):
            if o in m.group(2) and not _in_tracked(self.x, m.start()):
                rpr, txt = m.group(1), m.group(2)
                i = txt.index(o)
                out = (self._run(rpr, txt[:i]) + self._del(rpr, o) + self._ins(rpr, n)
                       + self._run(rpr, txt[i + len(o):]))
                self.x = self.x[:m.start()] + out + self.x[m.end():]
                self.log.append((f"{old} [after {anchor[:25]}]", new, why))
                return
        raise SystemExit(f"*** not found after anchor: {old!r} / {anchor[:40]!r}")

    def delete_para(self, anchor, why=""):
        """Tracked deletion of the whole paragraph containing the unique `anchor`: every text run in
        <w:del> and the paragraph mark deleted. Comment markers are left in place."""
        a = escape(anchor)
        assert self.x.count(a) == 1, ("anchor not unique", anchor[:60])
        s, e = _para_bounds(self.x, self.x.index(a))
        p = self.x[s:e]
        body = RUN_RE.sub(lambda m: self._del(m.group(1), m.group(2)), p)
        mark = f'<w:rPr><w:del w:id="{self._id()}" w:author="{AUTHOR}" w:date="{DATE}"/></w:rPr>'
        if "<w:pPr>" in body:
            if "<w:rPr>" in body.split("</w:pPr>")[0]:
                body = body.replace("<w:rPr>", "<w:rPr>" + mark[7:-8], 1)
            else:
                body = body.replace("</w:pPr>", mark + "</w:pPr>", 1)
        else:
            j = body.index(">") + 1
            body = body[:j] + "<w:pPr>" + mark + "</w:pPr>" + body[j:]
        self.x = self.x[:s] + body + self.x[e:]
        self.log.append((anchor[:60] + " [para deleted]", "", why))

    def insert_para(self, anchor, text, before=False, why=""):
        """Tracked insertion of a new plain paragraph after (or before) the one containing `anchor`,
        copying that paragraph's pPr."""
        a = escape(anchor)
        assert self.x.count(a) == 1, ("anchor not unique", anchor[:60])
        s, e = _para_bounds(self.x, self.x.index(a))
        p = self.x[s:e]
        m = re.search(r"<w:pPr>(.*?)</w:pPr>", p, re.S)
        ppr_inner = re.sub(r"<w:rPr>.*?</w:rPr>", "", m.group(1), flags=re.S) if m else ""
        mark = f'<w:rPr><w:ins w:id="{self._id()}" w:author="{AUTHOR}" w:date="{DATE}"/></w:rPr>'
        newp = f'<w:p><w:pPr>{ppr_inner}{mark}</w:pPr>{self._ins(None, escape(text))}</w:p>'
        self.x = (self.x[:s] + newp + self.x[s:]) if before else (self.x[:e] + newp + self.x[e:])
        self.log.append((anchor[:40] + (" [+para before]" if before else " [+para after]"), text, why))

    def swap_image(self, rid, new_rid, new_cy, new_descr, why=""):
        """Tracked figure swap: the run holding r:embed=rid goes into <w:del>; a copy pointing at
        new_rid (height new_cy EMU, width unchanged) goes into <w:ins> right after it."""
        key = f'r:embed="{rid}"'
        assert self.x.count(key) == 1, rid
        i = self.x.index(key)
        s = max(self.x.rfind("<w:r>", 0, i), self.x.rfind("<w:r ", 0, i))
        e = self.x.index("</w:r>", i) + len("</w:r>")
        run = self.x[s:e]
        new = run.replace("<w:lastRenderedPageBreak/>", "").replace(key, f'r:embed="{new_rid}"')
        new = re.sub(r' wp14:anchorId="[^"]*"| wp14:editId="[^"]*"', "", new)
        new = re.sub(r'(<wp:extent cx="\d+" cy=")\d+(")', rf"\g<1>{new_cy}\2", new)
        new = re.sub(r'(<a:ext cx="\d+" cy=")\d+(")', rf"\g<1>{new_cy}\2", new)
        dpr = max(int(v) for v in re.findall(r'<wp:docPr id="(\d+)"', self.x)) + 1
        new = re.sub(r'<wp:docPr id="\d+"', f'<wp:docPr id="{dpr}"', new)
        new = re.sub(r'(<pic:cNvPr id="\d+" name="Picture" descr=")[^"]*(")', rf"\g<1>{new_descr}\2", new)
        out = (f'<w:del w:id="{self._id()}" w:author="{AUTHOR}" w:date="{DATE}">{run}</w:del>'
               f'<w:ins w:id="{self._id()}" w:author="{AUTHOR}" w:date="{DATE}">{new}</w:ins>')
        self.x = self.x[:s] + out + self.x[e:]
        self.log.append((f"[image {rid}]", f"[image {new_rid}: {new_descr}]", why))

    Doc.replace_after = replace_after
    Doc.delete_para = delete_para
    Doc.insert_para = insert_para
    Doc.swap_image = swap_image


_add_methods()
