"""Gate for round r1112. Checks that do not use the edit code's own reading.

    python verify_r1112.py <base.docx> <out.docx>

1. No <w:ins> nests inside another <w:ins> (a deletion inside someone's insertion is valid; an insertion is not).
2. Strip this round's changes from out.docx by string handling (its insertions removed, its deletions restored):
   (a) pandoc's accepted text (--track-changes=accept) equals the base's exactly, and (b) the sequence of image
   references equals the base's.
3. Every new value of the round is in pandoc's accepted text of out.docx and every replaced value is gone.
4. The images visible in the accepted view (references outside any deletion or move source) are the base's, with the
   Fig. 5 reference replaced by one whose media file has the md5 of figures/paper/<FIG5_PNG>.
Exit 0 = PASS. Mutation-tested: mutation_test_verify.py.
"""
import hashlib, os, re, subprocess, sys, tempfile, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from trackedit import AUTHOR, DATE  # noqa: E402

OWN = f'w:author="{AUTHOR}" w:date="{DATE}"'
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))


def edits_data():
    """CR, NEW_VALUES, ABSENT, FIG5_* from edits_r1112.py, without running its edits."""
    src = open(os.path.join(HERE, "edits_r1112.py"), encoding="utf8").read()
    block = src[src.index("## (context, prefix"):src.index("REPLY_TO")]
    g = {}
    exec(block, g)
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
    rid = g["FIG5_RID"]
    bad = []
    if vb.count(rid) != 1:
        bad.append(f"base shows {rid} {vb.count(rid)} times")
    else:
        k = vb.index(rid)
        if len(vo) != len(vb) or vo[:k] != vb[:k] or vo[k + 1:] != vb[k + 1:]:
            bad.append("visible images other than Fig. 5 changed")
        elif vo[k] == rid:
            bad.append("Fig. 5 still shows the old image")
        else:
            want = hashlib.md5(open(os.path.join(REPO, "figures", "paper", g["FIG5_PNG"]), "rb").read()).hexdigest()
            got = hashlib.md5(read(out, "word/" + target(out, vo[k]))).hexdigest()
            if got != want:
                bad.append(f"Fig. 5 media md5 {got[:8]} != figures/paper {want[:8]}")
    print(f"[VERIFY] (4) visible images: {len(vo)} (base {len(vb)}), Fig. 5 is the new render",
          "PASS" if not bad else f"FAIL: {bad}")
    ok &= not bad
    print("[VERIFY]", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main(*sys.argv[1:3]) else 1)
