"""Gates for round r1122, read with an INDEPENDENT reader (pandoc, HTML writer, inline tags dropped, block tags to
spaces; sub/superscripts written _(x) / ^(x)), not with the code that built the files.

    python verify_r1122.py <base.docx> <redline.docx> <clean.docx>

The base (the 11-21 clean copy) carries no tracked marks.
G1  every tracked mark is by "Claude" with this round's date; the base has none;
G2  REJECT-ALL view of the redline == the base;
G3  ACCEPT-ALL (clean) == the base + the planned edits and reference (r1122_data.py);
G4  facts: no placeholder left; the DOI twice (availability text, reference entry); the URL once; "(Sarofim, 2026,"
    once; the software entry sits between Rohde and Hausfather (2020) and Sarofim, Smith et al.
Exit 1 on any failure.
"""

import html, os, re, subprocess, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from r1122_data import EDITS, INSERTS, REFS, DOI, URL  # noqa: E402

base, red, clean = sys.argv[1:4]
fails = []
DATES = {"2026-11-22T12:00:00Z"}


def gate(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f": {detail}"))
    if not ok:
        fails.append(name)


def text(path, mode):
    h = subprocess.run(["pandoc", f"--track-changes={mode}", "-t", "html", "--wrap=none", path],
                       capture_output=True, text=True, check=True).stdout
    h = re.sub(r"<sup>([^<]*)</sup>", r"^(\1)", h)
    h = re.sub(r"<sub>([^<]*)</sub>", r"_(\1)", h)
    h = re.sub(r"</?(?:code|span|em|strong|a|u|s|mark|small)(?: [^>]*)?>", "", h)
    h = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(h)).strip()


def marks(path):
    x = zipfile.ZipFile(path).read("word/document.xml").decode("utf8")
    return [(m.group(1), m.group(2), m.group(3)) for m in
            re.finditer(r'<w:(ins|del) [^>]*w:author="([^"]*)" w:date="([^"]*)"', x)]


def first_diff(a, b):
    return next(((k, a[max(0, k - 6):k + 6], b[max(0, k - 6):k + 6]) for k, (p, q) in enumerate(zip(a, b)) if p != q),
                (len(a), len(b)))


# G1
mine, theirs = marks(red), marks(base)
gate("G1 authors and dates", bool(mine) and {m[1] for m in mine} == {"Claude"} and {m[2] for m in mine} <= DATES
     and theirs == [], (sorted({(m[1], m[2]) for m in mine}), len(theirs)))

# G2
B = text(base, "accept")
bw, rw = B.split(), text(red, "reject").split()
gate("G2 reject-all view == base", bw == rw, first_diff(bw, rw))

# G3
exp = B
for ctx, old, new, _ in EDITS:
    assert exp.count(ctx) == 1, ("G3 context", ctx, exp.count(ctx))
    exp = exp.replace(ctx, ctx.replace(old, new, 1))
for ctx, prefix, new, _ in INSERTS:
    assert exp.count(ctx) == 1, ("G3 insert context", ctx, exp.count(ctx))
    exp = exp.replace(ctx, prefix + new + ctx[len(prefix):])
for before, entry, _ in REFS:
    j = exp.index(" References ")
    k = exp.index(before, j)
    exp = exp[:k] + entry + " " + exp[k:]
C = text(clean, "accept")
ew, cw = exp.split(), C.split()
gate("G3 accept-all == base + planned edits", ew == cw, first_diff(ew, cw))

# G4
refs = C[C.index(" References "):]
entry = REFS[0][1]
i_r, i_s, i_n = refs.find("Rohde, R. A. and Hausfather"), refs.find(entry), refs.find("Sarofim, M. C., Smith, J. B.")
checks = {"no DOI placeholder": "[to be assigned" not in C, "no URL placeholder": "[repository URL]" not in C,
          "DOI twice": C.count(f"https://doi.org/{DOI}") == 2, "URL once": C.count(URL) == 1,
          "text citation once": C.count("(Sarofim, 2026, ") == 1,
          "entry in order": -1 < i_r < i_s < i_n,
          "tables wording": C.count("every figure and the computed tables in this paper") == 1}
gate("G4 facts", all(checks.values()), [k for k, v in checks.items() if not v])

print("ALL GATES PASS" if not fails else f"{len(fails)} GATE(S) FAILED: {fails}")
sys.exit(1 if fails else 0)
