"""Mutation test of verify_r1113.py: break what each check guards and require the gate to FAIL.

    python mutation_test_verify.py <base.docx> <out.docx>     (writes mutation_result_verify.txt)

V1 an untracked character in Table A3 text (check 2); V2 this round's insertion nested in another insertion (check 1);
V3 the γ insertion removed (check 3); V4 this round's deletion of 0.00991 unwrapped, so the old value shows (check 3);
V5 one visible image's relationship removed from the document (check 4); V6 the new data-set entry's text made untracked
inside its tracked paragraph (check 2).
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


def v3(x):   # drop the γ insertion
    return re.sub(r'<w:ins w:id="\d+" ' + re.escape(OWN) + r'><w:r>(?:(?!</w:ins>).)*?Calibration: 2\.04; projection: </w:t></w:r></w:ins>',
                  "", x, count=1, flags=re.S)


def v4(x):   # restore the deleted 0.00991 as plain text, leaving the insertion
    return re.sub(r'<w:del w:id="\d+" ' + re.escape(OWN) + r'>(<w:r>(?:(?!</w:del>).)*?)<w:delText([^>]*)>0\.00991</w:delText>(</w:r>)</w:del>',
                  r"\1<w:t\2>0.00991</w:t>\3", x, count=1, flags=re.S)


def v5(x):   # the first image vanishes (its run's embed is renamed to a missing relationship)
    return x.replace('r:embed="rId12"', 'r:embed="rId99999"', 1)


def v6(x):   # unwrap the insertion inside this round's new paragraph
    return re.sub(r'(<w:rPr><w:ins w:id="\d+" ' + re.escape(OWN) + r'/></w:rPr></w:pPr>)<w:ins w:id="\d+" ' + re.escape(OWN)
                  + r'>((?:(?!</w:p>).)*)</w:ins></w:p>', r"\1\2</w:p>", x, count=1, flags=re.S)


MUTANTS = [("V1", dict(doc=lambda x: once(x, "DAIS fast-dynamics rate and threshold", "DAIS fast-dynamicsZ rate and threshold"))),
           ("V2", dict(doc=v2)), ("V3", dict(doc=v3)), ("V4", dict(doc=v4)), ("V5", dict(doc=v5)),
           ("V6", dict(doc=v6))]

if __name__ == "__main__":
    base, out = sys.argv[1:3]
    lines = []
    with tempfile.TemporaryDirectory() as t:
        for name, kw in MUTANTS:
            dst = os.path.join(t, name + ".docx")
            mutate(out, dst, **kw)
            r = subprocess.run([sys.executable, os.path.join(HERE, "verify_r1113.py"), base, dst],
                               capture_output=True, text=True)
            fails = [l for l in r.stdout.splitlines() if "FAIL" in l and not l.startswith("[VERIFY] FAIL")]
            lines.append(f"{name}: {'KILLED' if r.returncode else 'SURVIVED'}  {fails[0][:110] if fails else ''}")
            print(lines[-1])
    open(os.path.join(HERE, "mutation_result_verify.txt"), "w").write(
        f"verify_r1113.py mutation test on {os.path.basename(out)}\n" + "\n".join(lines) + "\n")
    sys.exit(0 if all("KILLED" in l for l in lines) else 1)
