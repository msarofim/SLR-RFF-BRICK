"""Minimal tracked-change + comment editor for word/document.xml (runs already merged).

All edits are <w:ins>/<w:del> under AUTHOR so Marcus can accept/reject each one in Word.
Text matching is on the XML-escaped text inside a single <w:t>, after merge_runs.py.
"""
import re, html, subprocess, sys
from pathlib import Path

AUTHOR = "Claude"
DATE = "2026-09-17T00:00:00Z"
HERE = Path(__file__).parent
DOC = HERE / "unpacked/word/document.xml"
SK = Path("/Users/MarcusMarcus/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/"
          "bde964e6-4558-410f-b23a-3b83edafdcf0/a8b27aae-cf9d-41c6-8c2f-bc82579b92b8/skills/docx")

_id = [9000]
def nid():
    _id[0] += 1
    return _id[0]

def esc(s):
    return html.escape(s, quote=False)

def load():
    return DOC.read_text()

def save(x):
    DOC.write_text(x)

# ---------- paragraph / run helpers ----------
P_RE = re.compile(r"<w:p[ >].*?</w:p>|<w:p/>", re.S)
R_RE = re.compile(r"<w:r>.*?</w:r>|<w:r [^>]*>.*?</w:r>", re.S)

def find_para(x, needle, nth=0):
    """Return (start, end) of the nth paragraph whose text contains needle (escaped form)."""
    n = esc(needle)
    hits = [m for m in P_RE.finditer(x) if n in m.group(0)]
    if len(hits) <= nth:
        raise KeyError(f"paragraph not found: {needle!r} (hits={len(hits)})")
    m = hits[nth]
    return m.start(), m.end()

def run_parts(run):
    """Split a run into (rPr xml or '', text) — assumes a single <w:t>."""
    rpr = re.search(r"<w:rPr>.*?</w:rPr>", run, re.S)
    rpr = rpr.group(0) if rpr else ""
    ts = re.findall(r"<w:t(?: [^>]*)?>(.*?)</w:t>", run, re.S)
    return rpr, "".join(ts)

def mk_run(text, rpr=""):
    return f'<w:r>{rpr}<w:t xml:space="preserve">{text}</w:t></w:r>'

def mk_ins(text, rpr=""):
    return (f'<w:ins w:id="{nid()}" w:author="{AUTHOR}" w:date="{DATE}">'
            f'{mk_run(text, rpr)}</w:ins>')

def mk_del(text, rpr=""):
    return (f'<w:del w:id="{nid()}" w:author="{AUTHOR}" w:date="{DATE}">'
            f'<w:r>{rpr}<w:delText xml:space="preserve">{text}</w:delText></w:r></w:del>')

# ---------- edits ----------
def replace_text(x, old, new, nth=0, para=None):
    """Tracked replacement of `old` by `new` inside one run. `para` narrows to a paragraph."""
    o = esc(old)
    if para is not None:
        ps, pe = find_para(x, para)
        region = x[ps:pe]
    else:
        ps, pe = 0, len(x)
        region = x
    runs = [m for m in R_RE.finditer(region) if o in m.group(0)]
    if len(runs) <= nth:
        raise KeyError(f"run containing {old!r} not found (hits={len(runs)})")
    m = runs[nth]
    run = m.group(0)
    rpr, text = run_parts(run)
    i = text.index(o)
    before, after = text[:i], text[i + len(o):]
    out = ""
    if before:
        out += mk_run(before, rpr)
    out += mk_del(o, rpr)
    if new:
        out += mk_ins(esc(new), rpr)
    if after:
        out += mk_run(after, rpr)
    region = region[:m.start()] + out + region[m.end():]
    return x[:ps] + region + x[pe:]

def _para_ppr(para_xml):
    m = re.search(r"<w:pPr>.*?</w:pPr>", para_xml, re.S)
    return m.group(0) if m else ""

def _inline_runs(text, ins=True):
    """'**bold** rest' → runs; only leading/inline **...** bold is supported."""
    parts = re.split(r"(\*\*.*?\*\*)", text)
    out = ""
    for p in parts:
        if not p:
            continue
        if p.startswith("**") and p.endswith("**"):
            out += mk_ins(esc(p[2:-2]), "<w:rPr><w:b/></w:rPr>") if ins else mk_run(esc(p[2:-2]), "<w:rPr><w:b/></w:rPr>")
        else:
            out += mk_ins(esc(p)) if ins else mk_run(esc(p))
    return out

def new_para(text, ppr=""):
    """A tracked-inserted paragraph (its paragraph mark is inserted too)."""
    mark = f'<w:ins w:id="{nid()}" w:author="{AUTHOR}" w:date="{DATE}"/>'
    if ppr:
        if "<w:rPr>" in ppr:
            ppr2 = ppr.replace("<w:rPr>", f"<w:rPr>{mark}", 1)
        else:
            ppr2 = ppr.replace("</w:pPr>", f"<w:rPr>{mark}</w:rPr></w:pPr>")
    else:
        ppr2 = f"<w:pPr><w:rPr>{mark}</w:rPr></w:pPr>"
    return f"<w:p>{ppr2}{_inline_runs(text)}</w:p>"

def insert_after(x, anchor, texts, nth=0, ppr=None):
    """Insert tracked paragraphs after the paragraph containing `anchor`."""
    ps, pe = find_para(x, anchor, nth)
    if ppr is None:
        ppr = _para_ppr(x[ps:pe])
        ppr = re.sub(r"<w:rPr>.*?</w:rPr>", "", ppr, flags=re.S)  # drop para-mark rPr
    new = "".join(new_para(t, ppr) for t in texts)
    return x[:pe] + new + x[pe:]

def fill_empty_after(x, heading, texts):
    """Ladrillo draft has 'Heading' paragraph followed by an empty <w:p .../>; insert after heading."""
    return insert_after(x, heading, texts)

# ---------- comments ----------
def add_comment(x, anchor, text, nth=0, para=None):
    """Create a comment via the skill helper and anchor it on the run containing `anchor`."""
    save(x)
    r = subprocess.run([sys.executable, str(SK / "scripts/comment.py"), str(HERE / "unpacked"), text],
                       capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr + r.stdout)
    m = re.search(r'w:id="(\d+)"', r.stdout)
    cid = m.group(1)
    x = load()
    a = esc(anchor)
    if para is not None:
        ps, pe = find_para(x, para)
    else:
        ps, pe = 0, len(x)
    region = x[ps:pe]
    runs = [m for m in R_RE.finditer(region) if a in m.group(0)]
    if len(runs) <= nth:
        raise KeyError(f"comment anchor {anchor!r} not found (hits={len(runs)})")
    m = runs[nth]
    ref = (f'<w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr>'
           f'<w:commentReference w:id="{cid}"/></w:r>')
    region = (region[:m.start()] + f'<w:commentRangeStart w:id="{cid}"/>' + m.group(0)
              + f'<w:commentRangeEnd w:id="{cid}"/>' + ref + region[m.end():])
    return x[:ps] + region + x[pe:]


# ---------- round-2 additions ----------
def add_reply(x, parent_cid, text):
    """Reply to comment `parent_cid`; markers nested inside the parent's range."""
    save(x)
    r = subprocess.run([sys.executable, str(SK / "scripts/comment.py"), str(HERE / "unpacked"), text,
                        "--parent", str(parent_cid)], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr + r.stdout)
    cid = re.search(r"id=(\d+)", r.stdout).group(1)
    x = load()
    ps = f'<w:commentRangeStart w:id="{parent_cid}"/>'
    pe = f'<w:commentRangeEnd w:id="{parent_cid}"/>'
    refm = f'<w:commentReference w:id="{parent_cid}"/>'
    assert x.count(ps) == 1 and x.count(pe) == 1 and x.count(refm) == 1, f"parent {parent_cid} markers"
    ri = x.find(refm); rs = x.rfind("<w:r>", 0, ri); re_ = x.find("</w:r>", ri) + len("</w:r>")
    pref = x[rs:re_]
    x = x.replace(ps, ps + f'<w:commentRangeStart w:id="{cid}"/>')
    x = x.replace(pe, f'<w:commentRangeEnd w:id="{cid}"/>' + pe)
    x = x.replace(pref, pref + f'<w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr>'
                              f'<w:commentReference w:id="{cid}"/></w:r>')
    return x

def replace_para_text(x, anchor, new_text):
    """Tracked: delete every text run of the paragraph containing `anchor`, insert `new_text`
    (with **bold** support) at the end. Comment markers and reference runs are kept."""
    ps, pe = find_para(x, anchor)
    para = x[ps:pe]
    def delrun(m):
        run = m.group(0)
        if "<w:t" not in run or "commentReference" in run:
            return run
        run = re.sub(r"<w:t(?: [^>]*)?>", "<w:delText xml:space=\"preserve\">", run).replace("</w:t>", "</w:delText>")
        return f'<w:del w:id="{nid()}" w:author="{AUTHOR}" w:date="{DATE}">{run}</w:del>'
    para2 = R_RE.sub(delrun, para)
    # insert the new runs before the closing </w:p> (and before a trailing commentRangeEnd if any)
    tail = re.search(r'((?:<w:commentRangeEnd [^>]*/>|<w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference [^>]*/></w:r>)*)</w:p>$', para2, re.S)
    ins = _inline_runs(new_text)
    para2 = para2[:tail.start(1)] + ins + para2[tail.start(1):]
    return x[:ps] + para2 + x[pe:]

def set_table_widths(x, anchor_text, grid, tcw):
    """Formatting only (not tracked): set gridCol and per-cell tcW of the table containing anchor_text."""
    i = x.find(esc(anchor_text)); ts = x.rfind("<w:tbl>", 0, i); te = x.find("</w:tbl>", i) + len("</w:tbl>")
    t = x[ts:te]
    t = re.sub(r"<w:tblGrid>.*?</w:tblGrid>", "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{g}"/>' for g in grid) + "</w:tblGrid>", t, flags=re.S)
    k = [0]
    def tc(m):
        v = tcw[k[0] % len(tcw)]; k[0] += 1
        return f'<w:tcW w:w="{v}" w:type="dxa"/>'
    t = re.sub(r'<w:tcW [^>]*/>', tc, t)
    return x[:ts] + t + x[te:]


# ---------- round-6 additions (2026-09-20, the L24 -> L27 swap) ----------
## Revision ids: every earlier round restarted the counter at 9000 and Word renumbered on save;
## the base for r6 carries ids up to 9041, so r6 starts above them. Duplicate ids are tolerated
## by Word but not by a reader that keys on them.
def start_ids_above(x):
    ids = [int(v) for v in re.findall(r'<w:(?:ins|del) w:id="(\d+)"', x)]
    _id[0] = max([9000] + ids) + 50

MONO_RPR = '<w:rPr><w:rStyle w:val="VerbatimChar"/></w:rPr>'   # the draft's monospace (pandoc's)

def _inline_runs(text, ins=True):
    """'**bold** `mono` rest' -> runs. Overrides the round-1 version: adds `code` -> VerbatimChar,
    the style the draft uses for parameter names, so a whole-paragraph replacement keeps them."""
    parts = re.split(r"(\*\*.*?\*\*|`[^`]*`)", text)
    out = ""
    for p in parts:
        if not p:
            continue
        if p.startswith("**") and p.endswith("**"):
            rpr, s = "<w:rPr><w:b/></w:rPr>", p[2:-2]
        elif p.startswith("`") and p.endswith("`"):
            rpr, s = MONO_RPR, p[1:-1]
        else:
            rpr, s = "", p
        out += mk_ins(esc(s), rpr) if ins else mk_run(esc(s), rpr)
    return out

def revert_pending(x, anchor, nth=0):
    """REJECT Claude's own pending changes inside the paragraph containing `anchor`: drop the
    <w:ins> runs, unwrap the <w:del> runs back to live text. Used before a whole-paragraph
    replacement of a paragraph an earlier round already edited, so the reject-all view stays the
    original text and Marcus sees ONE replacement rather than a deletion of an insertion."""
    ps, pe = find_para(x, anchor, nth)
    p = x[ps:pe]
    p = re.sub(r"<w:ins w:id=\"\d+\" w:author=\"%s\"[^>]*>.*?</w:ins>" % AUTHOR, "", p, flags=re.S)
    def undel(m):
        inner = m.group(1)
        inner = re.sub(r"<w:delText( [^>]*)?>", lambda mm: "<w:t%s>" % (mm.group(1) or ""), inner)
        return inner.replace("</w:delText>", "</w:t>")
    p = re.sub(r"<w:del w:id=\"\d+\" w:author=\"%s\"[^>]*>(.*?)</w:del>" % AUTHOR, undel, p, flags=re.S)
    # a paragraph-mark insertion (an inserted paragraph): the caller removes such paragraphs whole
    return x[:ps] + p + x[pe:]

def remove_pending_para(x, anchor, nth=0):
    """Remove a paragraph that is entirely Claude's pending insertion (paragraph mark included)."""
    ps, pe = find_para(x, anchor, nth)
    p = x[ps:pe]
    assert re.search(r"<w:pPr>.*?<w:rPr>.*?<w:ins ", p, re.S), "not an inserted paragraph: %r" % anchor
    return x[:ps] + x[pe:]

# ---- tables ----
TR_RE = re.compile(r"<w:tr\b.*?</w:tr>", re.S)
TC_RE = re.compile(r"<w:tc>.*?</w:tc>|<w:tc [^>]*>.*?</w:tc>", re.S)

def find_table(x, anchor, nth=0):
    """(start, end) of the nth <w:tbl> whose XML contains `anchor`."""
    a = esc(anchor); hits = []
    for m in re.finditer(r"<w:tbl>.*?</w:tbl>", x, re.S):
        if a in m.group(0):
            hits.append((m.start(), m.end()))
    if len(hits) <= nth:
        raise KeyError(f"table containing {anchor!r} not found (hits={len(hits)})")
    return hits[nth]

def cell_text(tc):
    return "".join(html.unescape(t) for t in re.findall(r"<w:t(?: [^>]*)?>(.*?)</w:t>", tc, re.S))

def _replace_cell_xml(tc, new):
    """Tracked: every text run of the cell deleted, `new` inserted (first run's rPr kept)."""
    runs = [m for m in R_RE.finditer(tc) if "<w:t" in m.group(0)]
    if not runs:
        # empty cell: insert before the last </w:p>
        j = tc.rfind("</w:p>")
        return tc[:j] + mk_ins(esc(new)) + tc[j:]
    rpr = run_parts(runs[0].group(0))[0]
    out = tc[:runs[0].start()]
    for m in runs:
        r = m.group(0)
        r = re.sub(r"<w:t(?: [^>]*)?>", '<w:delText xml:space="preserve">', r).replace("</w:t>", "</w:delText>")
        out += f'<w:del w:id="{nid()}" w:author="{AUTHOR}" w:date="{DATE}">{r}</w:del>'
    if new != "":
        out += mk_ins(esc(new), rpr)
    out += tc[runs[-1].end():]
    return out

def edit_table(x, anchor, edits, delete_rows=(), nth=0):
    """Tracked cell edits + tracked row deletions on the table containing `anchor`.
    edits: {(row, col): new_text}; delete_rows: row indices (0 = header). Cells whose text
    already equals new_text are left untouched, so calling twice is idempotent."""
    ts, te = find_table(x, anchor, nth)
    t = x[ts:te]
    rows = [m for m in TR_RE.finditer(t)]
    out = t[:rows[0].start()]
    for ri, rm in enumerate(rows):
        r = rm.group(0)
        if ri in delete_rows:
            mark = f'<w:del w:id="{nid()}" w:author="{AUTHOR}" w:date="{DATE}"/>'
            if "<w:trPr>" in r:
                r = r.replace("</w:trPr>", mark + "</w:trPr>", 1)
            else:
                r = re.sub(r"^(<w:tr\b[^>]*>)", lambda m: m.group(1) + f"<w:trPr>{mark}</w:trPr>", r, count=1)
            r = TC_RE.sub(lambda m: _replace_cell_xml(m.group(0), "") if "<w:t" in m.group(0) else m.group(0), r)
        else:
            cells = [m for m in TC_RE.finditer(r)]
            rr = r[:cells[0].start()] if cells else r
            for ci, cm in enumerate(cells):
                tc = cm.group(0)
                if (ri, ci) in edits and cell_text(tc) != edits[(ri, ci)]:
                    tc = _replace_cell_xml(tc, edits[(ri, ci)])
                rr += tc
            if cells:
                rr += r[cells[-1].end():]
            r = rr
        out += r
    out += t[rows[-1].end():]
    return x[:ts] + out + x[te:]

def table_texts(x, anchor, nth=0):
    """[[cell text, ...], ...] of the table containing `anchor` (accepted view)."""
    ts, te = find_table(x, anchor, nth)
    rows = []
    for rm in TR_RE.finditer(x[ts:te]):
        r = re.sub(r"<w:del\b.*?</w:del>", "", rm.group(0), flags=re.S)
        rows.append([cell_text(c.group(0)) for c in TC_RE.finditer(r)])
    return rows

# ---- images ----
def replace_image(x, unpacked, old_descr_png, new_png, new_alt, new_pic_descr):
    """Tracked figure swap. The run holding the drawing whose pic:cNvPr descr == old_descr_png is
    wrapped in <w:del>; a copy pointing at `new_png` (added to word/media + document.xml.rels) is
    inserted after it in <w:ins>. The extent keeps cx and rescales cy to the new image's aspect,
    so a different aspect ratio does not distort. Reject-all restores the old picture."""
    from PIL import Image
    import shutil
    unpacked = Path(unpacked)
    rels_p = unpacked / "word/_rels/document.xml.rels"
    rels = rels_p.read_text()
    media = unpacked / "word/media"
    n = 1 + max([0] + [int(m) for m in re.findall(r"image(\d+)\.png", rels)])
    target = f"media/image{n}.png"
    shutil.copy(new_png, media / f"image{n}.png")
    rid = 1 + max(int(v) for v in re.findall(r'Id="rId(\d+)"', rels))
    rels = rels.replace("</Relationships>",
        f'<Relationship Id="rId{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
        f'relationships/image" Target="{target}"/></Relationships>')
    rels_p.write_text(rels)
    runs = [m for m in re.finditer(r"<w:r>(?:(?!</w:r>).)*<w:drawing>.*?</w:drawing></w:r>", x, re.S)
            if f'descr="{esc(old_descr_png)}"' in m.group(0)]
    assert len(runs) == 1, f"drawing {old_descr_png!r}: {len(runs)} hits"
    m = runs[0]; old = m.group(0)
    w, h = Image.open(new_png).size
    cx = int(re.search(r'<wp:extent cx="(\d+)"', old).group(1))
    cy = int(round(cx * h / w))
    new = old
    new = re.sub(r'<wp:extent cx="(\d+)" cy="\d+"/>', lambda mm: f'<wp:extent cx="{mm.group(1)}" cy="{cy}"/>', new)
    new = re.sub(r'<a:ext cx="(\d+)" cy="\d+"/>', lambda mm: f'<a:ext cx="{mm.group(1)}" cy="{cy}"/>', new)
    new = re.sub(r'r:embed="rId\d+"', f'r:embed="rId{rid}"', new)
    ids = [int(v) for v in re.findall(r'<wp:docPr id="(\d+)"', x)]
    new = re.sub(r'<wp:docPr id="\d+" name="[^"]*" descr="[^"]*"',
                 f'<wp:docPr id="{max(ids) + 100 + n}" name="Picture" descr="{esc(new_alt)}"', new)
    new = re.sub(r'(<pic:cNvPr id="\d+" name="[^"]*") descr="[^"]*"', lambda mm: f'{mm.group(1)} descr="{esc(new_pic_descr)}"', new)
    new = re.sub(r' wp14:anchorId="[0-9A-F]+" wp14:editId="[0-9A-F]+"', "", new)
    out = (f'<w:del w:id="{nid()}" w:author="{AUTHOR}" w:date="{DATE}">{old}</w:del>'
           f'<w:ins w:id="{nid()}" w:author="{AUTHOR}" w:date="{DATE}">{new}</w:ins>')
    return x[:m.start()] + out + x[m.end():]


# ---------- round-8 addition: edit inside one of Claude's own PENDING insertions ----------
def edit_ins_text(x, old, new):
    """Replace `old` by `new` where `old` sits inside a PENDING <w:ins> run (an earlier round's insertion
    Marcus has not acted on). The outer insertion is SPLIT around the edit -- before / deleted-old / new /
    after -- with the before/after pieces keeping the original author+date (fresh ids) so validate.py
    still recognises them, the deletion NESTED inside a piece of the original insertion (what Word
    writes when you delete your own pending text), and `new` as a fresh insertion under today's DATE.
    (Generalised from apply_edits_r2b.py, which reused the original id for every piece.)"""
    o = esc(old)
    hits = [m for m in re.finditer(r"<w:ins [^>/]*>(?:(?!</w:ins>).)*</w:ins>", x, re.S) if o in m.group(0)]
    if len(hits) != 1:
        raise KeyError(f"edit_ins_text: {old[:50]!r} found in {len(hits)} pending insertions (need exactly 1)")
    m = hits[0]; ins = m.group(0)
    head0 = re.match(r"<w:ins [^>/]*>", ins).group(0)
    def head():
        return re.sub(r'w:id="\d+"', f'w:id="{nid()}"', head0, count=1)
    runs = [r for r in R_RE.finditer(ins) if o in r.group(0)]
    if len(runs) != 1:
        raise KeyError(f"edit_ins_text: {old[:50]!r} spans runs inside the insertion")
    run = runs[0].group(0)
    rpr, text = run_parts(run)
    i = text.index(o); before, after = text[:i], text[i + len(o):]
    pre, post = ins[:runs[0].start()], ins[runs[0].end():]        # other runs of the same insertion, if any
    out = ""
    if pre != head0:
        out += pre + "</w:ins>"
    if before:
        out += head() + mk_run(before, rpr) + "</w:ins>"
    out += head() + mk_del(o, rpr) + "</w:ins>"
    if new:
        out += mk_ins(esc(new), rpr)
    if after:
        out += head() + mk_run(after, rpr) + "</w:ins>"
    if post != "</w:ins>":
        out += head() + post
    return x[:m.start()] + out + x[m.end():]

def in_pending_ins(x, old):
    """True if the run containing `old` sits inside a <w:ins> element."""
    o = esc(old); i = x.find(o)
    if i < 0:
        raise KeyError(old[:50])
    last_open = x.rfind("<w:ins ", 0, i); last_close = x.rfind("</w:ins>", 0, i)
    return last_open > last_close

def smart_replace(x, old, new):
    """replace_text for live text, edit_ins_text for text inside a pending insertion."""
    return edit_ins_text(x, old, new) if in_pending_ins(x, old) else replace_text(x, old, new)
