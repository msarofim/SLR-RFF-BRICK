"""Mutation test for verify_r1119.py: break what each gate guards, on copies, and require that gate to FAIL.

    python mutation_test_verify.py <Tony's file> <redline.docx> <clean.docx>
"""
import os, re, subprocess, sys, tempfile, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
tony, red, clean = sys.argv[1:4]


def mutate(src, dst, fn):
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            b = zi.read(it.filename)
            if it.filename == "word/document.xml":
                y = fn(b.decode("utf8"))
                assert y != b.decode("utf8"), "mutation changed nothing"
                b = y.encode("utf8")
            zo.writestr(it, b)


def once(x, a, b):
    assert x.count(a) >= 1, a
    return x.replace(a, b, 1)


MUTATIONS = [   # (gate expected to fail, which file, mutation)
    ("G1", "red", lambda x: re.sub(r'(<w:ins w:id="\d+" w:author=")Claude(")', r"\1Tony Wong\2", x, count=1)),
    ("G2", "red", lambda x: once(x, "Ladrillo inherits BRICK", "Ladrillo inherit BRICK")),          # untracked edit
    ("G2b", "red", lambda x: once(x, "<w:delText xml:space=\"preserve\">S_eq = max(", "<w:delText xml:space=\"preserve\">S_eq = min(")),
    ("G3", "clean", lambda x: once(x, "In a departure", "A departure")),                            # a planned edit lost
    ("G3", "clean", lambda x: once(x, "Ladrillo inherits BRICK", "Ladrillo inherit BRICK")),        # an unplanned edit
    ("G4", "clean", lambda x: re.sub(r"<m:oMath>.*?</m:oMath>", "", x, count=1, flags=re.S)),
    ("G5a", "clean", lambda x: once(x, "Ladrillo inherits BRICK", "Ladrillo inherits T_x BRICK")),
    ("G5b", "clean", lambda x: once(x, '<w:t xml:space="preserve">sea level</w:t>', '<w:t xml:space="preserve">sea-level</w:t>')),
]

ok = True
with tempfile.TemporaryDirectory() as t:
    for k, (gate, which, fn) in enumerate(MUTATIONS):
        r2, c2 = red, clean
        dst = os.path.join(t, f"m{k}.docx")
        mutate(red if which == "red" else clean, dst, fn)
        if which == "red":
            r2 = dst
        else:
            c2 = dst
        out = subprocess.run([sys.executable, os.path.join(HERE, "verify_r1119.py"), tony, r2, c2],
                             capture_output=True, text=True).stdout
        caught = re.search(rf"^FAIL {re.escape(gate)} ", out, re.M) is not None
        print(f"{'caught ' if caught else 'MISSED '} mutation {k} ({which}) -> {gate}")
        ok &= caught
print("MUTATION TEST PASS: every gate failed on its mutation" if ok else "MUTATION TEST FAILED")
sys.exit(0 if ok else 1)
