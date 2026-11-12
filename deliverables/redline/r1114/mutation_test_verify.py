"""Mutation test of verify_r1114.py: break what each check guards and require the gate to FAIL.

    python mutation_test_verify.py <base.docx> <out.docx>     (writes mutation_result_verify.txt)

V1 an untracked character in Table 1 note 5 (check 2); V2 this round's insertion nested in another insertion (check 1);
V3 the Table 1 note insertion removed (check 3); V4 this round's deletion of "land-water storage" in the Fig. 3 caption
unwrapped (check 3); V5 the new Fig. 6 relationship pointed back at the old image (check 4); V6 the deletion around the
old Fig. 3 image unwrapped, so both show (check 4).
"""
import os, re, subprocess, sys, tempfile, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from trackedit import AUTHOR, DATE  # noqa: E402
OWN = f'w:author="{AUTHOR}" w:date="{DATE}"'


def mutate(out, dst, doc=None, rels=None):
    with zipfile.ZipFile(out) as zi, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            b = zi.read(it.filename)
            if it.filename == "word/document.xml" and doc:
                b = doc(b.decode("utf8")).encode("utf8")
            if it.filename == "word/_rels/document.xml.rels" and rels:
                b = rels(b.decode("utf8")).encode("utf8")
            zo.writestr(it, b)


def once(s, old, new):
    assert s.count(old) >= 1, old[:60]
    return s.replace(old, new, 1)


def v2(x):   # wrap this round's first insertion in a second, outer insertion
    m = re.search(r'<w:ins w:id="\d+" ' + re.escape(OWN) + r'>.*?</w:ins>', x, re.S)
    return x[:m.start()] + f'<w:ins w:id="999991" {OWN}>' + m.group(0) + "</w:ins>" + x[m.end():]


def v3(x):   # drop the Table 1 note insertion
    return re.sub(r'<w:ins w:id="\d+" ' + re.escape(OWN) + r'><w:r>(?:(?!</w:ins>).)*?In FACTS, Greenland(?:(?!</w:ins>).)*</w:ins>',
                  "", x, count=1, flags=re.S)


def v4(x):   # restore the deleted caption words as plain text
    return re.sub(r'<w:del w:id="\d+" ' + re.escape(OWN) + r'>(<w:r>(?:(?!</w:del>).)*?)<w:delText([^>]*)>(glaciers, thermal expansion and land-water storage)</w:delText>(</w:r>)</w:del>',
                  r"\1<w:t\2>\3</w:t>\4", x, count=1, flags=re.S)


def v5(r):   # the new Fig. 6 relationship points at the old image
    old = re.search(r'Target="(media/image\d+\.png)"', r).group(1)
    return re.sub(r'(Target=")media/fig1114_vv_responsiveness_L27\.png(")', rf"\g<1>{old}\2", r)


def v6(x):   # unwrap this round's deletion around the old Fig. 3 image
    ms = list(re.finditer(r'<w:del w:id="\d+" ' + re.escape(OWN) + r'>(<w:r>(?:(?!</w:del>).)*?<w:drawing>.*?)</w:del>', x, re.S))
    m0 = ms[0]
    return x[:m0.start()] + m0.group(1) + x[m0.end():]


MUTANTS = [("V1", dict(doc=lambda x: once(x, "ProFSea's Greenland uses the FACTS implementation", "ProFSea's GreenlandZ uses the FACTS implementation"))),
           ("V2", dict(doc=v2)), ("V3", dict(doc=v3)), ("V4", dict(doc=v4)), ("V5", dict(rels=v5)),
           ("V6", dict(doc=v6))]

if __name__ == "__main__":
    base, out = sys.argv[1:3]
    lines = []
    with tempfile.TemporaryDirectory() as t:
        for name, kw in MUTANTS:
            dst = os.path.join(t, name + ".docx")
            mutate(out, dst, **kw)
            r = subprocess.run([sys.executable, os.path.join(HERE, "verify_r1114.py"), base, dst],
                               capture_output=True, text=True)
            fails = [l for l in r.stdout.splitlines() if "FAIL" in l and not l.startswith("[VERIFY] FAIL")]
            lines.append(f"{name}: {'KILLED' if r.returncode else 'SURVIVED'}  {fails[0][:110] if fails else ''}")
            print(lines[-1])
    open(os.path.join(HERE, "mutation_result_verify.txt"), "w").write(
        f"verify_r1114.py mutation test on {os.path.basename(out)}\n" + "\n".join(lines) + "\n")
    sys.exit(0 if all("KILLED" in l for l in lines) else 1)
