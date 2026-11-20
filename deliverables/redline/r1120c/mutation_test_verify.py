"""Mutation test for verify_r1120c.py: break what each gate guards, on copies, and require that gate to FAIL.

    python mutation_test_verify.py <base.docx> <redline.docx> <clean.docx>
"""
import os, re, subprocess, sys, tempfile, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
base, red, clean = sys.argv[1:4]
DOC = "word/document.xml"


def mutate(src, dst, part, fn):
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            b = zi.read(it.filename)
            if it.filename == part:
                y = fn(b.decode("utf8"))
                assert y != b.decode("utf8"), "mutation changed nothing"
                b = y.encode("utf8")
            zo.writestr(it, b)


def once(x, a, b):
    assert x.count(a) >= 1, a
    return x.replace(a, b, 1)


def sub_text(old, new):
    pat = re.compile(r'(w:val="subscript"/>(?:(?!</w:r>).)*?<w:t xml:space="preserve">)' + re.escape(old) + r'(</w:t>)', re.S)
    def f(x):
        assert pat.search(x), old
        return pat.sub(lambda m: m.group(1) + new + m.group(2), x, count=1)
    return f


MUTATIONS = [   # (gate expected to fail, which file, part, mutation)
    ("G1", "red", DOC, lambda x: re.sub(r'(<w:ins w:id="\d+" w:author=")Claude(")', r"\1Tony Wong\2", x, count=1)),
    ("G1", "red", DOC, lambda x: once(x, " (below)</w:delText>", " (above)</w:delText>")),   # Marcus's mark altered
    ("G2", "red", DOC, lambda x: once(x, "Ladrillo inherits BRICK", "Ladrillo inherit BRICK")),  # untracked edit
    ("G3", "clean", DOC, lambda x: once(x, '<w:t xml:space="preserve">3000</w:t>', '<w:t xml:space="preserve">3001</w:t>')),
    ("G3", "clean", DOC, lambda x: once(x, "Ladrillo inherits BRICK", "Ladrillo inherit BRICK")),  # unplanned edit
    ("G4", "clean", DOC, sub_text("g", "b")),          # one block index back to b
    ("G4", "clean", DOC, sub_text("P", "DAIS")),       # kappa_P back to kappa_DAIS
    ("G5", "clean", DOC, lambda x: once(x, "35.7 (24–49)", "35.5 (24–49)")),
]

ok = True
with tempfile.TemporaryDirectory() as t:
    for k, (gate, which, part, fn) in enumerate(MUTATIONS):
        r2, c2 = red, clean
        dst = os.path.join(t, f"m{k}.docx")
        mutate(red if which == "red" else clean, dst, part, fn)
        if which == "red":
            r2 = dst
        else:
            c2 = dst
        out = subprocess.run([sys.executable, os.path.join(HERE, "verify_r1120c.py"), base, r2, c2],
                             capture_output=True, text=True).stdout
        caught = re.search(rf"^FAIL {re.escape(gate)} ", out, re.M) is not None
        print(f"{'caught ' if caught else 'MISSED '} mutation {k} ({which}) -> {gate}")
        ok &= caught
print("MUTATION TEST PASS: every gate failed on its mutation" if ok else "MUTATION TEST FAILED")
sys.exit(0 if ok else 1)
