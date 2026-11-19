"""Round r1119, notation pass (Tony 11-19: "Does GMD require the equations to be typeset in equation mode with proper
subscripts and superscripts?"; Copernicus: "use the Microsoft equation editor and not the graphic mode").
Tracked under the author NOTATION_AUTHOR so Word can show, hide or accept this pass separately from the wording edits.

1. Eqs. (1)-(14): each Source Code block (one paragraph per block, lines split by line breaks) is replaced by one
   paragraph per equation: centred equation-editor object (OMML from eq_omml.json) and the number on a right tab.
   The new paragraphs are tracked insertions (paragraph mark, tabs, number and every math run; each math structure's
   control properties carry the insertion too, as Word writes them); the old block is a tracked deletion.
2. Symbols in the text written with an underscore or a caret (T_off, c_R, e^l) get real sub/superscripts: tracked
   deletion of the token, tracked insertion of the base and a subscript/superscript run with the same formatting.
   Underscores inside code and file names (ais_runoff_Ton, slr_sla_gbl_free_ref_90) are left: a token is a symbol
   only if its base letter starts a word. Every underscore in the body must be classified one way or the other.
"""
import json, os, re, sys
from xml.sax.saxutils import escape
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import trackedit  # noqa: E402
from trackedit import RUN_RE, _in_tracked, _para_bounds  # noqa: E402

NOTATION_AUTHOR, NOTATION_DATE = "Claude (notation)", "2026-11-19T18:30:00Z"
BLOCK_KEYS = ["S_eq = max( a·(1", "E_b(T)   = min(", "u(t)  = min( max(", "ln 𝓛_i   = ln N("]
BLOCK_NUMS = [(1, 2), (3, 7), (8, 11), (12, 14)]
STRUCTS = ["d", "sSub", "sSup", "sSubSup", "nary", "f", "func", "rad", "acc", "bar"]
MATH_RPR = '<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/></w:rPr>'


def _mark(d):
    return f'w:id="{d._id()}" w:author="{NOTATION_AUTHOR}" w:date="{NOTATION_DATE}"'


def tracked_omml(d, o):
    """Wrap every math run in an insertion and give every structure an inserted control-properties element."""
    o = re.sub(r'<m:t>', '<m:t xml:space="preserve">', o)
    o = re.sub(r'(<m:r>.*?</m:r>)', lambda m: f'<w:ins {_mark(d)}>{m.group(1)}</w:ins>', o, flags=re.S)
    for s in STRUCTS:
        ctrl = lambda: f'<m:ctrlPr><w:ins {_mark(d)}>{MATH_RPR}</w:ins></m:ctrlPr>'
        # existing <m:sPr>...</m:sPr>: append ctrlPr (it is the last child of every *Pr)
        o = re.sub(rf'</m:{s}Pr>', lambda m: ctrl() + m.group(0), o)
        o = re.sub(rf'<m:{s}Pr/>', lambda m: f'<m:{s}Pr>{ctrl()}</m:{s}Pr>', o)
        # structure without a Pr element: add one as its first child
        o = re.sub(rf'<m:{s}>(?!<m:{s}Pr)', lambda m: f'<m:{s}><m:{s}Pr>{ctrl()}</m:{s}Pr>', o)
    return o


def eq_paragraph(d, omml, n):
    assert omml.startswith("<m:oMath>") and omml.endswith("</m:oMath>") and omml.count("<m:oMath>") == 1, n
    omml = omml[len("<m:oMath>"):-len("</m:oMath>")]      # wrapped once below
    ppr = ('<w:pPr><w:pStyle w:val="BodyText"/><w:tabs><w:tab w:val="center" w:pos="4680"/>'
           '<w:tab w:val="right" w:pos="9360"/></w:tabs><w:spacing w:before="60" w:after="60"/>'
           f'<w:rPr><w:ins {_mark(d)}/></w:rPr></w:pPr>')
    return (f'<w:p>{ppr}<w:ins {_mark(d)}><w:r><w:tab/></w:r></w:ins><m:oMath>{tracked_omml(d, omml)}</m:oMath>'
            f'<w:ins {_mark(d)}><w:r><w:tab/><w:t>({n})</w:t></w:r></w:ins></w:p>')


def delete_block(d, p):
    """Tracked deletion of a whole paragraph whose runs may hold tabs and line breaks."""
    def drun(m):
        r = m.group(0).replace("<w:t>", '<w:delText xml:space="preserve">').replace(
            '<w:t xml:space="preserve">', '<w:delText xml:space="preserve">').replace("</w:t>", "</w:delText>")
        return f'<w:del {_mark(d)}>{r}</w:del>'
    body = re.sub(r'<w:r(?: [^>]*)?>.*?</w:r>', drun, p, flags=re.S)
    mark = f'<w:rPr><w:del {_mark(d)}/></w:rPr>'
    assert "<w:rPr>" not in body.split("</w:pPr>")[0], "block pPr already has an rPr"
    return body.replace("</w:pPr>", mark + "</w:pPr>", 1)


def equations(d, eqs):
    by_n = {e["n"]: e for e in eqs}
    for key, (lo, hi) in zip(BLOCK_KEYS, BLOCK_NUMS):
        k = escape(key)
        assert d.x.count(k) == 1, ("block key not unique", key)
        s, e = _para_bounds(d.x, d.x.index(k))
        p = d.x[s:e]
        assert '<w:pStyle w:val="SourceCode"/>' in p and not _in_tracked(d.x, s), key
        lines = [ln for ln in re.split(r"<w:br/>", p)]
        nums = re.findall(r"<w:t>\((\d+)\)</w:t>", p)
        assert [int(v) for v in nums] == list(range(lo, hi + 1)), (key, nums)
        assert len(lines) == hi - lo + 1, (key, len(lines))
        for ln, n in zip(lines, range(lo, hi + 1)):     # the block's text must be what eq_omml.json transcribed
            txt = "".join(re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", ln)).replace(f"({n})", "")
            assert txt == escape(by_n[n]["plain"]), (n, txt, by_n[n]["plain"])
        new = "".join(eq_paragraph(d, by_n[n]["omml"], n) for n in range(lo, hi + 1))
        d.x = d.x[:s] + new + delete_block(d, p) + d.x[e:]
        d.log.append((key, f"Eqs. ({lo})-({hi}) -> equation editor", "notation"))


# ---- symbols in the text --------------------------------------------------------------------------------
LETTER = r"A-Za-zΑ-Ωα-ωℓ𝓛"
TOKEN = re.compile(rf"(?<![{LETTER}0-9_])(Δ?[{LETTER}]̄?)_([A-Za-z0-9]+(?:,[0-9]|−1)?)")   # T_off, T_oc,0, T_t−1
SUPERS = [(re.compile(r"(?<![A-Za-z])(e)\^(ℓ)"), lambda h: h.group(2)),          # w·e^ℓ
          (re.compile(r"(?<=yr⁻¹ )(K)⁻(ν)"), lambda h: "−" + h.group(2))]       # yr⁻¹ K⁻ν (text and Table A1): ν not raised
CODE_WORD = re.compile(rf"[{LETTER}0-9.]*[{LETTER}0-9]_[A-Za-z0-9_.₀-₉-]*")   # code, parameter and file names


AFTER_VERTALIGN = ("<w:rtl", "<w:cs", "<w:em", "<w:lang", "<w:eastAsianLayout", "<w:specVanish", "<w:oMath")


def _rpr_with(rpr, tag):
    """rPr plus `tag` (a vertAlign), placed where the schema's element order puts it."""
    rpr = re.sub(r'<w:rPrChange [^>]*>.*?</w:rPrChange>', '', rpr or "", flags=re.S)
    if not rpr or rpr == "<w:rPr></w:rPr>":
        return f"<w:rPr>{tag}</w:rPr>"
    assert "<w:vertAlign" not in rpr, rpr
    cut = [rpr.index(a) for a in AFTER_VERTALIGN if a in rpr]
    i = min(cut) if cut else rpr.rindex("</w:rPr>")
    return rpr[:i] + tag + rpr[i:]


def symbols(d, body_end):
    """Convert underscore/caret symbols in untracked runs before `body_end` (the References heading)."""
    n_tok, n_sup, out_x, pos = 0, 0, [], 0
    for m in RUN_RE.finditer(d.x, 0, body_end):
        rpr, t = m.group(1) or "", m.group(2)
        rpr_del = rpr                                        # the deletion keeps the run's own formatting
        if ("_" not in t and "^" not in t and "K⁻ν" not in t) or _in_tracked(d.x, m.start()):
            continue
        if '<w:rStyle w:val="VerbatimChar"/>' in rpr:
            if not TOKEN.fullmatch(t):                       # code font: file and code names, left as they are
                continue
            rpr = rpr.replace('<w:rStyle w:val="VerbatimChar"/>', "")   # a symbol set in code font (S_eq): text font
            rpr = "" if rpr == "<w:rPr></w:rPr>" else rpr
        hits = sorted([(h.start(), h.end(), h.group(1), h.group(2), "subscript") for h in TOKEN.finditer(t)] +
                      [(h.start(), h.end(), h.group(1), f(h), "superscript") for rx, f in SUPERS for h in rx.finditer(t)])
        # every other underscore must sit inside a code or file name
        rest = t
        for a, b, *_ in hits[::-1]:
            rest = rest[:a] + " " * (b - a) + rest[b:]
        stray = [c.group(0) for c in re.finditer(r"\S*_\S*", rest) if not CODE_WORD.fullmatch(c.group(0).strip(",.;:()\"'“”‘’"))]
        assert not stray and "^" not in rest, ("unclassified underscore/caret", stray, rest[:80])
        if not hits:
            continue
        seg, cur = [], 0
        for a, b, base, sub, kind in hits:
            seg.append(d._run(rpr, t[cur:a]))
            va = '<w:vertAlign w:val="%s"/>' % kind
            mk = f'w:id="{d._id()}" w:author="{NOTATION_AUTHOR}" w:date="{NOTATION_DATE}"'
            seg.append(f'<w:del {mk}><w:r>{d._fresh(rpr_del)}<w:delText xml:space="preserve">{t[a:b]}</w:delText></w:r></w:del>')
            r0 = re.sub(r'<w:rPrChange [^>]*>.*?</w:rPrChange>', '', rpr, flags=re.S)
            r0 = "" if r0 == "<w:rPr></w:rPr>" else r0
            seg.append(f'<w:ins w:id="{d._id()}" w:author="{NOTATION_AUTHOR}" w:date="{NOTATION_DATE}">'
                       f'<w:r>{r0}<w:t xml:space="preserve">{base}</w:t></w:r>'
                       f'<w:r>{_rpr_with(rpr, va)}<w:t xml:space="preserve">{sub}</w:t></w:r></w:ins>')
            n_tok += kind == "subscript"
            n_sup += kind == "superscript"
            d.log.append((t[a:b], f"{base} + {kind} {sub}", "notation"))
            cur = b
        seg.append(d._run(rpr, t[cur:]))
        out_x.append(d.x[pos:m.start()] + "".join(seg))
        pos = m.end()
    d.x = "".join(out_x) + d.x[pos:]
    return n_tok, n_sup


def run(d):
    trackedit.AUTHOR, trackedit.DATE = NOTATION_AUTHOR, NOTATION_DATE
    eqs = json.load(open(os.path.join(HERE, "eq_omml.json"), encoding="utf8"))["eqs"]
    equations(d, eqs)
    refs = [m.start() for m in re.finditer(r"<w:t(?: [^>]*)?>References</w:t>", d.x)]
    assert len(refs) == 1, ("References heading", len(refs))
    return symbols(d, refs[0])
