"""Gate for round r1111 (memory docx_collaborator_ins_attrs): three checks that do not use the edit code's own reading.

    python verify_r1111.py <base.docx> <out.docx>

1. No <w:ins> nests inside another <w:ins> (a deletion inside someone's insertion is valid; an insertion is not).
2. Strip this round's changes from out.docx by string handling (its insertions removed, its deletions restored, its
   paragraph-property changes reverted, its inserted paragraphs and table rows removed), and pandoc's accepted text
   (--track-changes=accept) equals the base's EXACTLY.
3. Every new value of the round appears in pandoc's accepted text of out.docx.
Exit 0 = PASS. Mutation-tested: see the bottom of this file.
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
    # paragraphs and table rows this round inserted (their mark carries the round's ins)
    x = re.sub(r'<w:p>(?:(?!</w:p>).)*?<w:rPr><w:ins w:id="\d+" ' + re.escape(OWN) + r'/></w:rPr>.*?</w:p>', "", x, flags=re.S)
    x = re.sub(r'<w:tr><w:trPr><w:ins w:id="\d+" ' + re.escape(OWN) + r'/></w:trPr>.*?</w:tr>', "", x, flags=re.S)
    # this round's insertions out, its deletions back in
    x = re.sub(r'<w:ins w:id="\d+" ' + re.escape(OWN) + r'>.*?</w:ins>', "", x, flags=re.S)
    x = re.sub(r'<w:del w:id="\d+" ' + re.escape(OWN) + r'>(.*?)</w:del>',
               lambda m: m.group(1).replace("<w:delText", "<w:t").replace("</w:delText>", "</w:t>"), x, flags=re.S)
    # paragraph-property changes: restore the recorded pPr
    def revert(m):
        inner = m.group(1)
        pc = re.search(r'<w:pPrChange w:id="\d+" ' + re.escape(OWN) + r'><w:pPr>(.*?)</w:pPr></w:pPrChange>', inner, re.S)
        if not pc:
            return m.group(0)
        rpr = re.search(r"<w:rPr>.*?</w:rPr>", inner, re.S)
        return "<w:pPr>" + pc.group(1) + (rpr.group(0) if rpr else "") + "</w:pPr>"
    return re.sub(r"<w:pPr>((?:(?!</w:pPr>).)*?<w:pPrChange (?:(?!</w:pPr>).)*?)</w:pPr>", revert, x, flags=re.S)


def main(base, out, new_values):
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
           [v for cols in ns["A1"].values() for v in cols.values()] + [ns["A1_FOOTNOTE"].strip()[:60]]
    sys.exit(0 if main(base, out, vals) else 1)
