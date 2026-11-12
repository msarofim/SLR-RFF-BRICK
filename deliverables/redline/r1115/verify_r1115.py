"""Gate for round r1115 (Code and data availability; the clean copy). Tracked file: Checks that do not use the edit code's own reading.

    python verify_r1112.py <base.docx> <out.docx>

1. No <w:ins> nests inside another <w:ins> (a deletion inside someone's insertion is valid; an insertion is not).
2. Strip this round's changes from out.docx by string handling (its new paragraphs and insertions removed, its
   deletions restored):
   (a) pandoc's accepted text (--track-changes=accept) equals the base's exactly, and (b) the sequence of image
   references equals the base's.
3. Every new value of the round is in pandoc's accepted text of out.docx and every replaced value is gone.
4. The images visible in the accepted view (references outside any deletion or move source) are exactly the base's.
Exit 0 = PASS. Mutation-tested: mutation_test_verify.py.
"""
import os, re, subprocess, sys, tempfile, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from trackedit import AUTHOR, DATE  # noqa: E402

OWN = f'w:author="{AUTHOR}" w:date="{DATE}"'
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))


def edits_data():
    import r1115_data as R
    g = dict(vars(R))
    g["NEW_VALUES"] = [R.AVAIL_ANCHOR + R.AVAIL_NEW, "all three blocks (committed-loss fractions at 1.2"]
    g["ABSENT"] = ["( committed"]
    return g


def read(docx, name):
    with zipfile.ZipFile(docx) as z:
        return z.read(name)


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
    # this round's new paragraphs (as trackedit.insert_para writes them): mark and text are both this round's
    x = re.sub(r'<w:p><w:pPr>(?:(?!</w:pPr>).)*<w:rPr><w:ins w:id="\d+" ' + re.escape(OWN) + r'/></w:rPr></w:pPr>'
               r'<w:ins w:id="\d+" ' + re.escape(OWN) + r'>(?:(?!</w:p>).)*</w:ins></w:p>', "", x, flags=re.S)
    x = re.sub(r'<w:ins w:id="\d+" ' + re.escape(OWN) + r'>.*?</w:ins>', "", x, flags=re.S)
    return re.sub(r'<w:del w:id="\d+" ' + re.escape(OWN) + r'>(.*?)</w:del>',
                  lambda m: m.group(1).replace("<w:delText", "<w:t").replace("</w:delText>", "</w:t>"), x, flags=re.S)


def embeds(x):
    return re.findall(r'r:embed="(rId\d+)"', x)


def visible_embeds(x):
    """Image references outside any open <w:del> or <w:moveFrom> (self-closing marks open nothing)."""
    out, open_ = [], 0
    for m in re.finditer(r'<(/?)w:(del|moveFrom)\b([^>]*?)(/?)>|r:embed="(rId\d+)"', x):
        if m.group(5):
            if open_ == 0:
                out.append(m.group(5))
        elif m.group(4) == "/":
            continue
        else:
            open_ += -1 if m.group(1) else 1
    return out


def target(docx, rid):
    rels = read(docx, "word/_rels/document.xml.rels").decode("utf8")
    return re.search(r'Id="%s"[^>]*Target="([^"]+)"' % rid, rels).group(1)


def main(base, out):
    g = edits_data()
    ok = True
    x, xb = read(out, "word/document.xml").decode("utf8"), read(base, "word/document.xml").decode("utf8")
    dep = max_ins_depth(x)
    print(f"[VERIFY] (1) max <w:ins> nesting depth {dep}", "PASS" if dep == 1 else "FAIL")
    ok &= dep == 1
    s = strip_own(x)
    with tempfile.TemporaryDirectory() as t:
        stripped = os.path.join(t, "stripped.docx")
        write_with(out, s, stripped)
        a, b = accepted_text(base), accepted_text(stripped)
    same_t, same_i = a == b, embeds(s) == embeds(xb)
    print(f"[VERIFY] (2) own changes stripped: accepted text {'==' if same_t else '!='} base ({len(a)} chars); image "
          f"references {'==' if same_i else '!='} base ({len(embeds(xb))})", "PASS" if same_t and same_i else "FAIL")
    if not same_t:
        import difflib
        for l in list(difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm="", n=0))[:12]:
            print("     ", l[:160])
    ok &= same_t and same_i
    acc = re.sub(r"\s+", " ", accepted_text(out))
    missing = [v for v in g["NEW_VALUES"] if v not in acc]
    left = [v for v in g["ABSENT"] if v in acc]
    print(f"[VERIFY] (3) {len(g['NEW_VALUES']) - len(missing)} of {len(g['NEW_VALUES'])} new values present, "
          f"{len(g['ABSENT']) - len(left)} of {len(g['ABSENT'])} replaced values gone",
          "PASS" if not missing and not left else f"FAIL: missing {missing}, left {left}")
    ok &= not missing and not left
    vb, vo = visible_embeds(xb), visible_embeds(x)
    same = vo == vb
    print(f"[VERIFY] (4) visible images: {len(vo)} (base {len(vb)})", "PASS" if same else "FAIL: they differ")
    ok &= same
    print("[VERIFY]", "PASS" if ok else "FAIL")
    return ok


def done_flags(docx):
    e = read(docx, "word/commentsExtended.xml").decode("utf8")
    return dict(re.findall(r'w15:paraId="([0-9A-Fa-f]+)"[^>]*?w15:done="(\d)"', e))


def comments_check(base, out, label):
    """Only the STALE_COMMENTS change state, and they become resolved."""
    g = edits_data()
    fb, fo = done_flags(base), done_flags(out)
    changed = {k for k in fb if fo.get(k) != fb[k]} | (set(fo) - set(fb))
    c = read(out, "word/comments.xml").decode("utf8")
    want = set()
    for f in g["STALE_COMMENTS"]:
        m = [m for m in re.finditer(r'<w:comment w:id="\d+"[^>]*>(.*?)</w:comment>', c, re.S)
             if f in re.sub(r"<[^>]+>", "", m.group(1))]
        want.add(re.findall(r'w14:paraId="([0-9A-Fa-f]+)"', m[0].group(1))[-1] if len(m) == 1 else "missing:" + f)
    ok = changed == want and all(fo.get(k) == "1" for k in want)
    print(f"[VERIFY] ({label}) comments: {len(changed)} changed state, expected the {len(want)} stale ones, now resolved",
          "PASS" if ok else f"FAIL: changed {sorted(changed)} want {sorted(want)}")
    return ok


def clean_check(clean_base, clean_out, tracked_out):
    g = edits_data()
    ok = True
    xo = read(clean_out, "word/document.xml").decode("utf8")
    n = len(re.findall(r"<w:(ins|del|moveFrom|moveTo) ", xo))
    print(f"[VERIFY] (C1) clean copy has {n} tracked changes", "PASS" if n == 0 else "FAIL")
    ok &= n == 0
    a, b = accepted_text(clean_base), accepted_text(clean_out)
    a2 = a.replace(g["AVAIL_ANCHOR"], g["AVAIL_ANCHOR"] + g["AVAIL_NEW"], 1).replace("( committed", "(committed", 1)
    a2 = a2.replace("each block’s1850 ice extent", "each block’s 1850 ice extent", 1)
    same = a2 == b
    print(f"[VERIFY] (C2) clean text = its base with exactly this round's edits ({len(b)} chars)",
          "PASS" if same else "FAIL")
    if not same:
        import difflib
        for l in list(difflib.unified_diff(a2.splitlines(), b.splitlines(), lineterm="", n=0))[:10]:
            print("     ", l[:160])
    ok &= same
    imgs = lambda d: [read(d, "word/" + target(d, r)) for r in embeds(read(d, "word/document.xml").decode("utf8"))]
    si = imgs(clean_base) == imgs(clean_out)
    print("[VERIFY] (C3) clean images byte-identical to its base", "PASS" if si else "FAIL")
    ok &= si
    ok &= comments_check(clean_base, clean_out, "C4")
    ## cross-file: the clean copy against the tracked file's accepted text. Lines in code blocks (the equations, whose
    ## tracked insertions pandoc's reader drops) are left out; the regrowth paragraph is split in the tracked file only.
    t = accepted_text(tracked_out)
    keep = lambda s: [l for l in re.sub(r"\s+\n", "\n", s).splitlines() if l.strip() and not l.startswith("    ")]
    import difflib
    diff = [l for l in difflib.unified_diff(keep(t), keep(b), lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    print(f"[VERIFY] (C5) clean vs tracked accepted text: {len(diff)} differing lines (expected: the regrowth split only)")
    for l in diff[:8]:
        print("     ", l[:150])
    return ok


if __name__ == "__main__":
    base, out = sys.argv[1:3]
    ok = main(base, out)
    ok &= comments_check(base, out, "5")
    if len(sys.argv) > 4:
        ok &= clean_check(sys.argv[3], sys.argv[4], out)
    print("[VERIFY] ALL", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
