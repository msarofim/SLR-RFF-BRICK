"""Gate for round r1111 (memory docx_collaborator_ins_attrs): three checks that do not use the edit code's own reading.

    python verify_r1111.py <base.docx> <out.docx>

1. No <w:ins> nests inside another <w:ins> (a deletion inside someone's insertion is valid; an insertion is not).
2. Strip this round's changes from out.docx by string handling (its insertions removed, its deletions restored, its
   paragraph-property changes reverted, its inserted paragraphs and table rows removed), and pandoc's accepted text
   (--track-changes=accept) equals the base's EXACTLY.
3. Every new value of the round appears in pandoc's accepted text of out.docx.
4. The structural edits (the optional simplifications, 20:34 save): each Sect. 3.3 break separates two paragraphs of
   the accepted text, the Sect. 2.2.2 paragraphs are one, and no moved Table 3 note text is left (absence checked in
   pandoc's text and in docx_review_extract's, which does not wrap table cells).
Check 2 rejoins a paragraph this round split (its mark is this round's insertion and it holds earlier text) with the
next one, and drops this round's deleted paragraph marks. Exit 0 = PASS. Mutation-tested: mutation_test_verify.py.
"""
import os, re, subprocess, sys, tempfile, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trackedit import AUTHOR, DATE

OWN = f'w:author="{AUTHOR}" w:date="{DATE}"'
EXTRACT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "python",
                                       "docx_review_extract.py"))


def read_xml(docx):
    with zipfile.ZipFile(docx) as z:
        return z.read("word/document.xml").decode("utf8")


def write_with(docx, xml, out):
    with zipfile.ZipFile(docx) as zi, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            zo.writestr(it, xml.encode("utf8") if it.filename == "word/document.xml" else zi.read(it.filename))


def accepted_text(docx):
    return subprocess.run(["pandoc", "--track-changes=accept", "-t", "plain", "--wrap=none", docx],
                          capture_output=True, text=True, check=True).stdout


def max_ins_depth(x):
    depth = best = 0
    for m in re.finditer(r"<w:ins [^>]*?(/?)>|</w:ins>", x):
        if m.group(0) == "</w:ins>":
            depth -= 1
        elif m.group(1) != "/":
            depth += 1
            best = max(best, depth)
    return best


def strip_own(x):
    # this round's paragraph marks. A deleted mark (a join) is restored. A paragraph whose mark is this round's insertion
    # is removed if it holds nothing older (a new paragraph), else rejoined with the next paragraph (a split), last first
    x = re.sub(r'<w:del w:id="\d+" ' + re.escape(OWN) + r'/>', "", x)
    own_ins = re.compile(r'<w:ins w:id="\d+" ' + re.escape(OWN) + r'>.*?</w:ins>', re.S)
    mark = re.compile(r'<w:ins w:id="\d+" ' + re.escape(OWN) + r'/>')
    para = re.compile(r'<w:p>((?:(?!</w:p>).)*)</w:p>', re.S)
    ppr_end = re.compile(r'<w:pPr>(?:(?!</w:pPr>)(?!<w:pPrChange).)*(?:<w:pPrChange [^>]*>(?:<w:pPr>(?:(?!</w:pPr>).)*'
                         r'</w:pPr>|<w:pPr/>)</w:pPrChange>)?</w:pPr>', re.S)
    while True:
        heads = [m for m in para.finditer(x) if (k := ppr_end.match(m.group(1))) and mark.search(k.group(0))]
        if not heads:
            break
        m = heads[-1]
        body = m.group(1)[ppr_end.match(m.group(1)).end():]
        if not re.search(r"<w:t[ >]|<w:delText|<w:tab/>|<w:drawing", own_ins.sub("", body)):
            x = x[:m.start()] + x[m.end():]
            continue
        nxt = re.compile(r"<w:p(?: [^>]*)?>").match(x, m.end())
        assert nxt, "a split paragraph is not followed by a paragraph"
        k = ppr_end.match(x, nxt.end())
        at = k.end() if k else nxt.end()
        x = x[:m.start()] + x[nxt.start():at] + body + x[at:]
    x = re.sub(r'<w:tr><w:trPr><w:ins w:id="\d+" ' + re.escape(OWN) + r'/></w:trPr>.*?</w:tr>', "", x, flags=re.S)
    # this round's insertions out, its deletions back in
    x = re.sub(r'<w:ins w:id="\d+" ' + re.escape(OWN) + r'>.*?</w:ins>', "", x, flags=re.S)
    x = re.sub(r'<w:del w:id="\d+" ' + re.escape(OWN) + r'>(.*?)</w:del>',
               lambda m: m.group(1).replace("<w:delText", "<w:t").replace("</w:delText>", "</w:t>"), x, flags=re.S)
    # paragraph-property changes: restore the recorded pPr. (Until 11-11 evening this pattern stopped at the pPrChange's
    # INNER </w:pPr>, so it never reverted anything; harmless for the text comparison, which ignores pPr.)
    def revert(m):
        pc = re.search(r'<w:pPrChange w:id="\d+" ' + re.escape(OWN) + r'><w:pPr>(.*?)</w:pPr></w:pPrChange>', m.group(0), re.S)
        if not pc:
            return m.group(0)
        rpr = re.search(r"<w:rPr>.*?</w:rPr>", m.group(0)[:pc.start()], re.S)
        return "<w:pPr>" + pc.group(1) + (rpr.group(0) if rpr else "") + "</w:pPr>"
    return re.sub(r"<w:pPr>(?:(?!</w:pPr>)(?!<w:pPrChange).)*<w:pPrChange [^>]*>(?:<w:pPr>(?:(?!</w:pPr>).)*</w:pPr>|<w:pPr/>)"
                  r"</w:pPrChange></w:pPr>", revert, x, flags=re.S)


def main(base, out, new_values, struct=None):
    ok = True
    x = read_xml(out)
    d = max_ins_depth(x)
    print(f"[VERIFY] (1) max <w:ins> nesting depth {d}", "PASS" if d == 1 else "FAIL")
    ok &= d == 1
    with tempfile.TemporaryDirectory() as t:
        stripped = os.path.join(t, "stripped.docx")
        write_with(out, strip_own(x), stripped)
        a, b = accepted_text(base), accepted_text(stripped)
    same = a == b
    print(f"[VERIFY] (2) own changes stripped: accepted text {'==' if same else '!='} base ({len(a)} chars)",
          "PASS" if same else "FAIL")
    if not same:
        import difflib
        for l in list(difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm="", n=0))[:20]:
            print("     ", l[:160])
    ok &= same
    acc = accepted_text(out)
    acc_n = re.sub(r"\s+", " ", acc)
    missing = [v for v in new_values if re.sub(r"\s+", " ", v) not in acc_n]
    second = []
    if missing:   # pandoc drops tracked insertions inside code-styled (SourceCode) paragraphs: the equations.
        # Second reader for those values only: python/docx_review_extract.py (accepted view, its own XML walk).
        with tempfile.TemporaryDirectory() as t:
            subprocess.run([sys.executable, EXTRACT, out, t], capture_output=True, check=True)
            ext = re.sub(r"\s+", " ", open(os.path.join(t, "paras.txt"), encoding="utf8").read())
        second = [v for v in missing if re.sub(r"\s+", " ", v) in ext]
        missing = [v for v in missing if v not in second]
    print(f"[VERIFY] (3) {len(new_values) - len(missing)} of {len(new_values)} new values in the accepted text"
          + (f" ({len(second)} found only by docx_review_extract: {second})" if second else ""),
          "PASS" if not missing else f"FAIL: {missing[:8]}")
    ok &= not missing
    if struct:
        paras = [re.sub(r"\s+", " ", b).strip() for b in re.split(r"\n\s*\n", acc) if b.strip()]
        bad = [f"break {b[-20:]!r} | {a[:20]!r}" for b, a, _ in struct["splits"]
               if not any(p.endswith(b) and q.startswith(a) for p, q in zip(paras, paras[1:]))]
        if not any(struct["joined"] in p for p in paras):
            bad.append(f"not joined: {struct['joined'][:40]!r}")
        with tempfile.TemporaryDirectory() as t:
            subprocess.run([sys.executable, EXTRACT, out, t], capture_output=True, check=True)
            ext = open(os.path.join(t, "paras.txt"), encoding="utf8").read()
        bad += [f"still present: {v!r}" for v in struct["absent"] if v in acc_n or v in ext]
        n_checks = len(struct["splits"]) + 1 + len(struct["absent"])
        print(f"[VERIFY] (4) structure: {n_checks - len(bad)} of {n_checks} checks",
              "PASS" if not bad else f"FAIL: {bad[:6]}")
        ok &= not bad
    print("[VERIFY]", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    base, out = sys.argv[1], sys.argv[2]
    sys.argv = [sys.argv[0], "/nonexistent"]          # edits_r1111 reads sys.argv[1] at import; its lists are all we need
    import importlib.util
    spec = importlib.util.spec_from_file_location("e", os.path.join(os.path.dirname(os.path.abspath(__file__)), "edits_r1111.py"))
    src = open(spec.origin, encoding="utf8").read()
    head = src[:src.index("d = edlib.open_doc")] + src[src.index("E = lambda"):src.index("def cell_text")]
    ns = {"__file__": spec.origin}
    exec(head, ns)
    vals = [e["new"] for e in ns["ENTRIES"] if e["new"].strip()] + [n for _, _, _, n in ns["MINIMAL"]] + \
           [c[3].strip("; ").strip() for c in ns["CITES"]] + [r[1][:60] for r in ns["NEW_REFS"]] + \
           [v for cols in ns["A1"].values() for v in cols.values()] + [ns["A1_FOOTNOTE"].strip()[:60]] + ns["SIMP_NEW"]
    struct = dict(splits=ns["SPLITS_33"], joined=ns["SIMP_JOINED"], absent=ns["SIMP_ABSENT"])
    sys.exit(0 if main(base, out, vals, struct) else 1)
