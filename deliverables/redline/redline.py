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
