"""Gates for round r1119, read with an INDEPENDENT reader (pandoc), not with the code that built the files.

    python verify_r1119.py <Tony's file> <redline.docx> <clean.docx>

G1  the redline's tracked changes are by "Claude" and "Claude (notation)" only, and none by Tony is left;
G2  REJECT view of the redline == Tony's file with his edits accepted (pandoc on each), except the 14 equation lines,
    which pandoc cannot read inside a deleted code block / tracked math;
G2b the four deleted equation blocks hold exactly the draft's equation text (string check on the XML);
G3  ACCEPTED (clean) text == Tony's accepted text with exactly the planned wording edits applied (r1119_data.py),
    after normalising sub/superscript notation (pandoc writes T_(off), the draft T_off);
G4  the clean copy has 14 equation-editor equations, numbered (1)-(14) in order, each non-empty;
G5  no literal underscore is left in the clean body except in code and file names; no "sea-level" outside reference
    titles and FACTS's name.
Exit 1 on any failure.
"""
import os, re, subprocess, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from r1119_data import EDITS, INSERTS, TABLE2, REF_BEFORE, REF_NEW  # noqa: E402
import json  # noqa: E402

tony, red, clean = sys.argv[1:4]
fails = []


def gate(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f": {detail}"))
    if not ok:
        fails.append(name)


def pandoc(path, mode, fmt="plain"):
    return subprocess.run(["pandoc", f"--track-changes={mode}", "-t", fmt, "--wrap=none", path],
                          capture_output=True, text=True, check=True).stdout


EQ = re.compile(r"\((\d{1,2})\)\s*$")


def drop_eq_lines(s):
    out = []
    for ln in s.split("\n"):
        m = EQ.search(ln)
        if m and 1 <= int(m.group(1)) <= 14 and ("=" in ln or ln.strip() == m.group(0).strip()):
            continue
        if ln.strip():
            out.append(ln)
    return out


# G1
x = zipfile.ZipFile(red).read("word/document.xml").decode("utf8")
authors = set(re.findall(r'<w:(?:ins|del) [^>]*w:author="([^"]*)"', x))
gate("G1 authors", authors == {"Claude", "Claude (notation)"}, authors)

# G2
A = pandoc(tony, "accept")
## pandoc's math reader ignores tracking marks inside equations, so a rejected equation leaves its structure characters;
## read the reject view from a copy with the equation objects removed (nothing else changed)
import shutil, tempfile  # noqa: E402
with tempfile.TemporaryDirectory() as t:
    nm = os.path.join(t, "nomath.docx")
    with zipfile.ZipFile(red) as zi, zipfile.ZipFile(nm, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            b = zi.read(it.filename)
            if it.filename == "word/document.xml":
                b = re.sub(r"<m:oMath>.*?</m:oMath>", "", b.decode("utf8"), flags=re.S).encode("utf8")
            zo.writestr(it, b)
    R = pandoc(nm, "reject")
a2, r2 = drop_eq_lines(A), drop_eq_lines(R)
gate("G2 reject view == Tony accepted (equation lines aside)", a2 == r2,
     next(((i, p, q) for i, (p, q) in enumerate(zip(a2, r2)) if p != q), (len(a2), len(r2))))

# G2b
eqs = json.load(open(os.path.join(HERE, "eq_omml.json"), encoding="utf8"))["eqs"]
blocks = re.findall(r'<w:p [^>]*><w:pPr><w:pStyle w:val="SourceCode"/>.*?</w:p>', x, re.S)
deltext = ["".join(re.findall(r"<w:delText[^>]*>([^<]*)</w:delText>", b)) for b in blocks]
want = [(1, 2), (3, 7), (8, 11), (12, 14)]
exp = ["".join(eqs[n - 1]["plain"].replace("&", "&amp;") + f"({n})" for n in range(lo, hi + 1)) for lo, hi in want]
gate("G2b deleted blocks hold the draft equations", deltext == exp and all("<w:t>" not in b and "<w:t " not in b for b in blocks),
     [(d[:40], e[:40]) for d, e in zip(deltext, exp) if d != e] or len(blocks))

# G3
C = pandoc(clean, "accept")
norm = lambda s: re.sub(r"\^\(([^)]*)\)", r"^\1", re.sub(r"_\(([^)]*)\)", r"_\1", s))
words = lambda lines: [w for w in " ".join(lines).split() if not re.fullmatch(r"-+", w)]
exp_text = norm(" ".join(drop_eq_lines(A)))
exp_text = re.sub(r"\s+", " ", exp_text).replace("K⁻ν", "K^−ν")
for ctx, old, new, _ in EDITS:
    c = re.sub(r"\s+", " ", ctx)
    assert exp_text.count(c) == 1, ("G3 context", ctx[:50], exp_text.count(c))
    exp_text = exp_text.replace(c, c.replace(old, new, 1))
for ctx, prefix, new, _ in INSERTS:
    assert exp_text.count(ctx) == 1, ("G3 insert context", ctx[:50])
    exp_text = exp_text.replace(ctx, prefix + new + ctx[len(prefix):])
anchor = TABLE2[0]
i = exp_text.index(anchor)
j = exp_text.index(TABLE2[1], i)
exp_text = exp_text[:j] + TABLE2[2] + exp_text[j + len(TABLE2[1]):]
exp_text = exp_text.replace(REF_BEFORE, REF_NEW + " " + REF_BEFORE, 1)
got, want_w = words([norm(" ".join(drop_eq_lines(C)))]), words([exp_text])
first = next(((k, got[max(0, k - 6):k + 6], want_w[max(0, k - 6):k + 6]) for k, (p, q) in enumerate(zip(got, want_w)) if p != q),
             (len(got), len(want_w)))
gate("G3 accepted text == Tony accepted + planned edits", got == want_w, first)

# G4
md = pandoc(clean, "accept", "markdown")
nums = [int(m.group(2)) for m in re.finditer(r"^\$(.+)\$ \((\d+)\)$", md, re.M) if m.group(1).strip()]
gate("G4 14 equations numbered in order", nums == list(range(1, 15)), nums)

# G5
body = "\n".join(drop_eq_lines(C.split("\nReferences\n")[0]))
code = re.compile(r"[A-Za-zΑ-Ωα-ωℓ0-9.]*[A-Za-zΑ-Ωα-ωℓ0-9]{2}_[A-Za-z0-9_.₀-₉-]*")   # one letter before "_" = a symbol
fname = re.compile(r"\[?[\w/.-]*_[\w/.-]*\.(?:png|nc|csv|xlsx)\]?")    # figure paths, file names (code font)
stray = [w for w in re.findall(r"\S*_(?!\()\S*", body)
         if not code.fullmatch(w.strip(",.;:()\"'“”‘’")) and not fname.fullmatch(w.strip(",.;:()"))]
gate("G5a no stray underscores", not stray, stray[:10])
hy = [m.group(0) for m in re.finditer(r".{30}[Ss]ea-level.{10}", body) if "Changes To Sea-level" not in m.group(0)]
gate("G5b no 'sea-level' in the body", not hy, hy[:5])

print("ALL GATES PASS" if not fails else f"{len(fails)} GATE(S) FAILED: {fails}")
sys.exit(1 if fails else 0)
