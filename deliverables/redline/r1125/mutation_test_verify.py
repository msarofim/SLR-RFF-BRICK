"""Mutation test for verify_r1125.py: break what each gate guards, on copies, and require that gate to FAIL.

    python mutation_test_verify.py <base.docx> <redline.docx> <clean.docx>
"""
import os, re, subprocess, sys, tempfile, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from trackedit import DATE  # noqa: E402
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


MUTATIONS = [   # (gate expected to fail, which file, part, mutation)
    ("G1", "red", DOC, lambda x: re.sub(r'(<w:ins w:id="\d+" w:author=")Claude(")', r"\1Tony Wong\2", x, count=1)),
    ("G1", "red", DOC, lambda x: x.replace(f'w:date="{DATE}"', 'w:date="2026-11-22T21:00:00Z"', 1)),
    ("G2", "red", DOC, lambda x: once(x, "Ladrillo inherits BRICK", "Ladrillo inherit BRICK")),  # untracked edit
    ("G3", "clean", DOC, lambda x: once(x, "Ladrillo inherits BRICK", "Ladrillo inherit BRICK")),  # unplanned edit
    ("G3", "clean", DOC, lambda x: once(x, "Software Heritage [code]", "Software Heritage [software]")),
    ## one hex digit of the SWHID inside the resolver URL only: G4's whole-entry check must catch it
    ("G4", "clean", DOC, lambda x: once(x, "softwareheritage.org/swh:1:rel:0410476503074d",
                                        "softwareheritage.org/swh:1:rel:0410476503074e")),
    ## the old GitHub URL left in the text somewhere else
    ("G4", "clean", DOC, lambda x: once(x, "within the Mimi framework (1.6; Rennels et al., 2026)",
                                        "within the Mimi framework (1.6; Rennels et al., 2026; "
                                        "https://github.com/mimiframework/Mimi.jl/releases/tag/v1.6.0)")),
    ## the in-text citation dropped
    ("G4", "clean", DOC, lambda x: once(x, " (1.6; Rennels et al., 2026)", " (1.6)")),
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
        out = subprocess.run([sys.executable, os.path.join(HERE, "verify_r1125.py"), base, r2, c2],
                             capture_output=True, text=True).stdout
        caught = re.search(rf"^FAIL {re.escape(gate)} ", out, re.M) is not None
        print(f"{'caught ' if caught else 'MISSED '} mutation {k} ({which}) -> {gate}")
        ok &= caught
print("MUTATION TEST PASS: every gate failed on its mutation" if ok else "MUTATION TEST FAILED")
sys.exit(0 if ok else 1)
