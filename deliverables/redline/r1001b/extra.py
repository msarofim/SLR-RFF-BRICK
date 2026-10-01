"""Round 10-01b additions to trackedit.Doc: headings (tracked style + text), multi-run paragraphs
(equations, bold run-ins), a tracked table, and a tracked MOVE of a block of paragraphs (delete
in place + insert the accepted-view copy elsewhere). String operations only, never ElementTree."""
import difflib
import re
from xml.sax.saxutils import escape

import trackedit
from trackedit import Doc, RUN_RE, _in_tracked

A = lambda: trackedit.AUTHOR
D = lambda: trackedit.DATE
TXT = lambda s: "".join(re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", s))
P_RE = re.compile(r"<w:p(?: [^>]*)?/>|<w:p(?: [^>]*)?>.*?</w:p>", re.S)


def _body_paras(x):
    """Top-level paragraphs only (paragraphs inside tables are skipped)."""
    b = x.index("<w:body>")
    spans = [(m.start(), m.end()) for m in re.finditer(r"<w:tbl>.*?</w:tbl>", x, re.S)]
    return [m for m in P_RE.finditer(x, b) if not any(a <= m.start() < e for a, e in spans)]


def _para_exact(self, text):
    """The unique top-level paragraph whose accepted-view text (plain + inserted runs) == text."""
    hits = [m for m in _body_paras(self.x) if TXT(re.sub(r"<w:del .*?</w:del>", "", m.group(0), flags=re.S)) == text]
    assert len(hits) == 1, ("paragraph not unique", text, len(hits))
    return hits[0]


def heading(self, old, new, level, why=""):
    """Tracked: apply Heading<level> (pPrChange) and diff-edit the text of a one-run paragraph."""
    m = _para_exact(self, old)
    p = m.group(0)
    runs = [r for r in RUN_RE.finditer(p)]
    assert len(runs) == 1, ("heading must be one run", old, len(runs))
    r = runs[0]
    rpr, t = r.group(1) or "", r.group(2)
    out = ""
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, t, new, autojunk=False).get_opcodes():
        if op == "equal":
            out += self._run(rpr, t[i1:i2])
        else:
            out += self._del(rpr, t[i1:i2]) + self._ins(rpr, escape(new[j1:j2]))
    p2 = p[:r.start()] + out + p[r.end():]
    chg = f'<w:pPrChange w:id="{self._id()}" w:author="{A()}" w:date="{D()}">'
    pm = re.search(r"<w:pPr>(.*?)</w:pPr>", p2, re.S)
    if pm:
        inner = pm.group(1)
        old_ppr = re.sub(r"<w:rPr>.*?</w:rPr>", "", inner, flags=re.S)
        new_inner = re.sub(r"<w:pStyle [^>]*/>", "", inner)
        rpr_part = re.search(r"<w:rPr>.*?</w:rPr>", new_inner, re.S)
        rest = re.sub(r"<w:rPr>.*?</w:rPr>", "", new_inner, flags=re.S)
        new_ppr = (f'<w:pPr><w:pStyle w:val="Heading{level}"/>{rest}{rpr_part.group(0) if rpr_part else ""}'
                   f'{chg}<w:pPr>{old_ppr}</w:pPr></w:pPrChange></w:pPr>')
        p2 = p2[:pm.start()] + new_ppr + p2[pm.end():]
    else:
        j = p2.index(">") + 1
        p2 = p2[:j] + f'<w:pPr><w:pStyle w:val="Heading{level}"/>{chg}<w:pPr/></w:pPrChange></w:pPr>' + p2[j:]
    self.x = self.x[:m.start()] + p2 + self.x[m.end():]
    self.log.append((old + " [heading]", f"{new} (Heading{level})", why))


def _newp(self, style, runs):
    """A tracked-inserted paragraph. runs: list of (text, kind) with kind in {'', 'b', 'code', 'br'}."""
    mark = f'<w:rPr><w:ins w:id="{self._id()}" w:author="{A()}" w:date="{D()}"/></w:rPr>'
    st = ('<w:pStyle w:val="%s"/>' % style) if style else ""
    ppr = f'<w:pPr>{st}{mark}</w:pPr>'
    body = ""
    for text, kind in runs:
        if kind == "br":
            body += (f'<w:ins w:id="{self._id()}" w:author="{A()}" w:date="{D()}"><w:r><w:br/></w:r></w:ins>')
            continue
        rpr = {"": None, "b": "<w:rPr><w:b/></w:rPr>",
               "code": '<w:rPr><w:rStyle w:val="VerbatimChar"/></w:rPr>'}[kind]
        body += self._ins(rpr, escape(text))
    return f"<w:p>{ppr}{body}</w:p>"


def insert_paras(self, anchor_para_text, paras, before=False, why=""):
    """Insert tracked paragraphs after (or before) the paragraph whose accepted text is anchor_para_text.
    paras: list of (style, runs)."""
    m = _para_exact(self, anchor_para_text)
    new = "".join(_newp(self, st, runs) for st, runs in paras)
    pos = m.start() if before else m.end()
    self.x = self.x[:pos] + new + self.x[pos:]
    self.log.append((anchor_para_text[:40] + (" [+paras before]" if before else " [+paras after]"),
                     " / ".join("".join(t for t, k in r if k != "br")[:80] for _, r in paras), why))


def insert_paras_after_prefix(self, prefix, paras, why=""):
    """As insert_paras, anchored on the unique paragraph whose accepted text STARTS with prefix."""
    hits = [m for m in _body_paras(self.x)
            if TXT(re.sub(r"<w:del .*?</w:del>", "", m.group(0), flags=re.S)).startswith(prefix)]
    assert len(hits) == 1, ("prefix paragraph not unique", prefix, len(hits))
    m = hits[0]
    new = "".join(_newp(self, st, runs) for st, runs in paras)
    self.x = self.x[:m.end()] + new + self.x[m.end():]
    self.log.append((prefix[:40] + " [+paras after]",
                     " / ".join("".join(t for t, k in r if k != "br")[:80] for _, r in paras), why))


def insert_table_after_prefix(self, prefix, rows, widths, why=""):
    """Tracked table (first row = header) inserted after the paragraph starting with prefix."""
    hits = [m for m in _body_paras(self.x)
            if TXT(re.sub(r"<w:del .*?</w:del>", "", m.group(0), flags=re.S)).startswith(prefix)]
    assert len(hits) == 1, ("prefix paragraph not unique", prefix, len(hits))
    m = hits[0]
    tblpr = ('<w:tblPr><w:tblStyle w:val="Table"/><w:tblW w:w="5000" w:type="pct"/><w:tblLayout w:type="fixed"/>'
             '<w:tblLook w:val="0020" w:firstRow="1" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" '
             'w:noHBand="0" w:noVBand="0"/></w:tblPr>')
    grid = "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths) + "</w:tblGrid>"
    trs = []
    for i, cells in enumerate(rows):
        assert len(cells) == len(widths), cells
        hdr = "<w:tblHeader/>" if i == 0 else ""
        tr = f'<w:tr><w:trPr>{hdr}<w:ins w:id="{self._id()}" w:author="{A()}" w:date="{D()}"/></w:trPr>'
        for w, c in zip(widths, cells):
            tr += (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/></w:tcPr>'
                   + _newp(self, "Compact", [(c, "")]) + "</w:tc>")
        trs.append(tr + "</w:tr>")
    tbl = "<w:tbl>" + tblpr + grid + "".join(trs) + "</w:tbl>"
    self.x = self.x[:m.end()] + tbl + self.x[m.end():]
    self.log.append((prefix[:40] + " [+table]", f"{len(rows) - 1} rows", why))


def _strip_comment_markers(s):
    s = re.sub(r'<w:commentRangeStart w:id="\d+"/>|<w:commentRangeEnd w:id="\d+"/>', "", s)
    return re.sub(r'<w:r>(?:<w:rPr>(?:(?!</w:rPr>).)*</w:rPr>)?<w:commentReference w:id="\d+"/></w:r>', "", s, flags=re.S)


def move_block(self, first_text, stop_text, dest_text, retitle=None, restyle=None, why=""):
    """Tracked MOVE: paragraphs from the one whose accepted text == first_text up to (not including) the
    one == stop_text are deleted in place, and an accepted-view copy of them is inserted before the
    paragraph == dest_text. Comment markers travel with the copy. retitle/restyle map a paragraph's
    accepted text to its new text / style in the copy (it is a fresh insertion, so no pPrChange)."""
    retitle, restyle = retitle or {}, restyle or {}
    s = _para_exact(self, first_text).start()
    e = _para_exact(self, stop_text).start()
    block = self.x[s:e]
    assert "<w:tbl" not in block and "<w:sectPr" not in block
    deleted, copies = "", ""
    for pm in P_RE.finditer(block):
        p = pm.group(0)
        acc = TXT(re.sub(r"<w:del .*?</w:del>", "", p, flags=re.S))
        # --- deleted version (in place)
        dmark = f'<w:del w:id="{self._id()}" w:author="{A()}" w:date="{D()}"/>'
        if p.endswith("/>"):
            dp = p[:-2] + f"><w:pPr><w:rPr>{dmark}</w:rPr></w:pPr></w:p>"
        else:
            dp = _strip_comment_markers(p)
            dp = re.sub(r"(<w:del [^>]*>.*?</w:del>)|" + RUN_RE.pattern,
                        lambda mm: mm.group(0) if mm.group(1) else self._del(mm.group(2), mm.group(3)), dp, flags=re.S)
            pp = re.search(r"<w:pPr>(.*?)</w:pPr>", dp, re.S)
            if pp:
                inner = pp.group(1)
                if "<w:rPr>" in inner:
                    if re.search(r"<w:rPr><w:ins [^>]*/>", inner):
                        inner = re.sub(r"(<w:rPr><w:ins [^>]*/>)", r"\1" + dmark, inner, count=1)
                    else:
                        inner = inner.replace("<w:rPr>", "<w:rPr>" + dmark, 1)
                else:
                    inner = inner + f"<w:rPr>{dmark}</w:rPr>"
                dp = dp[:pp.start()] + f"<w:pPr>{inner}</w:pPr>" + dp[pp.end():]
            else:
                j = dp.index(">") + 1
                dp = dp[:j] + f"<w:pPr><w:rPr>{dmark}</w:rPr></w:pPr>" + dp[j:]
        deleted += dp
        # --- inserted copy (accepted view), skipped for empty spacer paragraphs
        if not acc.strip():
            continue
        style = restyle.get(acc)
        if style is None:
            sm = re.search(r'<w:pStyle w:val="([^"]+)"/>', p)
            style = sm.group(1) if sm else None
        if acc in retitle:
            runs_xml = self._ins(None, escape(retitle[acc]))
        else:
            src = re.sub(r"<w:del .*?</w:del>", "", p, flags=re.S)
            runs_xml = ""
            for item in re.finditer(r'<w:commentRangeStart w:id="\d+"/>|<w:commentRangeEnd w:id="\d+"/>|'
                                    r'<w:r>(?:<w:rPr>(?:(?!</w:rPr>).)*</w:rPr>)?<w:commentReference w:id="\d+"/></w:r>|'
                                    + RUN_RE.pattern, src, re.S):
                if item.group(0).startswith("<w:comment") or "commentReference" in item.group(0):
                    runs_xml += item.group(0)
                else:
                    rpr = item.group(1)
                    rpr = re.sub(r"<w:ins [^>]*/>|<w:del [^>]*/>", "", rpr) if rpr else rpr
                    runs_xml += self._ins(rpr if rpr and rpr != "<w:rPr></w:rPr>" else None, item.group(2))
        mark = f'<w:rPr><w:ins w:id="{self._id()}" w:author="{A()}" w:date="{D()}"/></w:rPr>'
        st = ('<w:pStyle w:val="%s"/>' % style) if style else ""
        copies += f"<w:p><w:pPr>{st}{mark}</w:pPr>{runs_xml}</w:p>"
    self.x = self.x[:s] + deleted + self.x[e:]
    d = _para_exact(self, dest_text).start()
    self.x = self.x[:d] + copies + self.x[d:]
    self.log.append((f"[move] {first_text[:30]} .. {stop_text[:20]}", f"before {dest_text[:30]}", why))


Doc.heading = heading
Doc.insert_paras = insert_paras
Doc.insert_paras_after_prefix = insert_paras_after_prefix
Doc.insert_table_after_prefix = insert_table_after_prefix
Doc.move_block = move_block
