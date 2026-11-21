"""Gates for round r1121, read with an INDEPENDENT reader (pandoc, HTML writer, inline tags dropped, block tags to
spaces; sub/superscripts written _(x) / ^(x)), not with the code that built the files.

    python verify_r1121.py <base.docx> <redline.docx> <clean.docx>

The base carries Marcus's pending tracked insertion, so G2/G3 compare the REJECT-ALL and ACCEPT-ALL views.
G1  new tracked marks are by "Claude" with this round's date; Marcus's mark is still there (type, author, date, text);
G2  REJECT-ALL view of the redline == REJECT-ALL view of the base;
G3  ACCEPT-ALL (clean) == ACCEPT-ALL of the base + the planned edits (r1121_data.py);
G4  facts: no "40 layers"/"40-layer"; "50 layers" (Table 2) and "50-layer" (text); "rate quadratic in GSAT"; no
    "Sanke", one "Sönke"; the FACTS version caveat once; "pre-2100 ocean forcing".
Exit 1 on any failure.
"""

import html, os, re, subprocess, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from r1121_data import EDITS, INSERTS  # noqa: E402

base, red, clean = sys.argv[1:4]
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
fails = []
DATES = {"2026-11-21T12:00:00Z"}
N_MARCUS = 1


def gate(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f": {detail}"))
    if not ok:
        fails.append(name)


def text(path, mode):
    h = subprocess.run(["pandoc", f"--track-changes={mode}", "-t", "html", "--wrap=none", path],
                       capture_output=True, text=True, check=True).stdout
    h = re.sub(r"<sup>([^<]*)</sup>", r"^(\1)", h)
    h = re.sub(r"<sub>([^<]*)</sub>", r"_(\1)", h)
    ## inline tags carry no whitespace: Marcus's Word save splits runs (spell-check marks between two code-font runs
    ## give two <code> elements), which the build's run merge joins; only block tags separate words
    h = re.sub(r"</?(?:code|span|em|strong|a|u|s|mark|small)(?: [^>]*)?>", "", h)
    h = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(h)).strip()


def marks(path, who=None):
    x = zipfile.ZipFile(path).read("word/document.xml").decode("utf8")
    out = []
    for m in re.finditer(r'<w:(ins|del) [^>]*w:author="([^"]*)" w:date="([^"]*)"[^>]*?(/>|>(.*?)</w:\1>)', x, re.S):
        if who is None or m.group(2) == who:
            body = m.group(5) or ""
            out.append((m.group(1), m.group(2), m.group(3),
                        "".join(re.findall(r"<(?:w:t|w:delText|m:t)[^>]*>([^<]*)<", body))))
    return out


def first_diff(a, b):
    return next(((k, a[max(0, k - 6):k + 6], b[max(0, k - 6):k + 6]) for k, (p, q) in enumerate(zip(a, b)) if p != q),
                (len(a), len(b)))


# G1
allm = marks(red)
mine = [m for m in allm if m[1] != "Marcus Sarofim"]
his_red, his_base = marks(red, "Marcus Sarofim"), marks(base, "Marcus Sarofim")
gate("G1 authors, dates, Marcus's marks kept",
     bool(mine) and {m[1] for m in mine} == {"Claude"} and {m[2] for m in mine} <= DATES
     and his_red == his_base and len(his_base) == N_MARCUS,
     (sorted({(m[1], m[2]) for m in mine}), his_base, his_red))

# G2
bw, rw = text(base, "reject").split(), text(red, "reject").split()
gate("G2 reject-all view == base reject-all", bw == rw, first_diff(bw, rw))

# G3
exp = text(base, "accept")
for ctx, old, new, _ in EDITS:
    assert exp.count(ctx) == 1, ("G3 context", ctx, exp.count(ctx))
    exp = exp.replace(ctx, ctx.replace(old, new, 1))
for ctx, prefix, new, _ in INSERTS:
    assert exp.count(ctx) == 1, ("G3 insert context", ctx, exp.count(ctx))
    exp = exp.replace(ctx, prefix + new + ctx[len(prefix):])
C = text(clean, "accept")
ew, cw = exp.split(), C.split()
gate("G3 accept-all == base accept-all + planned edits", ew == cw, first_diff(ew, cw))

# G4
caveat = "These descriptions apply to FACTS v1.1.4 at its default settings."
checks = {"no 40 layers": "40 layers" not in C and "40-layer" not in C, "50 layers": "50 layers" in C,
          "50-layer": "MAGICC-SLR uses a 50-layer approach" in C, "rate": "rate quadratic in GSAT" in C,
          "Sanke gone": "Sanke" not in C, "Sönke once": C.count("Sönke") == 1, "caveat once": C.count(caveat) == 1,
          "ocean forcing": "pre-2100 ocean forcing by 2300" in C}
gate("G4 facts", all(checks.values()), [k for k, v in checks.items() if not v])

print("ALL GATES PASS" if not fails else f"{len(fails)} GATE(S) FAILED: {fails}")
sys.exit(1 if fails else 0)
