"""Mutation test for verify_r1120.py: break what each gate guards, on copies, and require that gate to FAIL.

    python mutation_test_verify.py <base.docx> <redline.docx> <clean.docx>
"""
import os, re, subprocess, sys, tempfile, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
base, red, clean = sys.argv[1:4]
SP = '<w:r><w:t xml:space="preserve"> </w:t></w:r>'


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


def drop_pct_space(x):
    """Remove the first accepted space run that sits right before a run starting with '%'."""
    m = re.search(re.escape(SP) + r'(?=<w:r>(?:<w:rPr>(?:(?!</w:rPr>).)*</w:rPr>)?<w:t[^>]*>%)', x, re.S)
    assert m, "no space-before-% run"
    return x[:m.start()] + x[m.end():]


def wrong_letter(x):
    m = re.search(r'(<w:vertAlign w:val="superscript"/></w:rPr><w:t xml:space="preserve">)a(</w:t>)', x)
    assert m
    return x[:m.start()] + m.group(1) + "b" + m.group(2) + x[m.end():]


DOC, COM = "word/document.xml", "word/comments.xml"
MUTATIONS = [   # (gate expected to fail, which file, part, mutation)
    ("G1", "red", DOC, lambda x: re.sub(r'(<w:ins w:id="\d+" w:author=")Claude(")', r"\1Tony Wong\2", x, count=1)),
    ("G1", "red", DOC, lambda x: x.replace('w:date="2026-11-20T12:30:00Z"', 'w:date="2026-11-19T18:00:00Z"', 1)),
    ("G2", "red", DOC, lambda x: once(x, "Ladrillo inherits BRICK", "Ladrillo inherit BRICK")),       # untracked edit
    ("G3", "clean", DOC, lambda x: once(x, "across the van Vuuren scenarios", "depending on the scenario")),  # lost edit
    ("G3", "clean", DOC, lambda x: once(x, "Ladrillo inherits BRICK", "Ladrillo inherit BRICK")),     # unplanned edit
    ("G3", "clean", DOC, wrong_letter),                                                              # wrong letter
    ("G4", "clean", DOC, drop_pct_space),
    ("G5", "clean", DOC, lambda x: once(x, "Rohde, R. A. and Hausfather", "Rhode, R. A. and Hausfather")),
    ("G6", "clean", COM, lambda x: once(x, "IMBIE shows a net loss over the same years", "IMBIE 0.43 ± 0.07 mm yr⁻¹.")),
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
        out = subprocess.run([sys.executable, os.path.join(HERE, "verify_r1120.py"), base, r2, c2],
                             capture_output=True, text=True).stdout
        caught = re.search(rf"^FAIL {re.escape(gate)} ", out, re.M) is not None
        print(f"{'caught ' if caught else 'MISSED '} mutation {k} ({which}) -> {gate}")
        ok &= caught
print("MUTATION TEST PASS: every gate failed on its mutation" if ok else "MUTATION TEST FAILED")
sys.exit(0 if ok else 1)
