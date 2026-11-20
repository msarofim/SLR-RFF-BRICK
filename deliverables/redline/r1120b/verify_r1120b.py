"""Gates for round r1120b (= r1120 + G7), read with an INDEPENDENT reader (pandoc, HTML writer, tags stripped to text), not with the
code that built the files. HTML rather than plain text: the plain writer re-wraps table cells when a column's width
changes, which reorders words; HTML keeps cell order linear.

    python verify_r1120b.py <base.docx> <redline.docx> <clean.docx>

G1  every tracked mark in the redline is by "Claude" or "Claude (style)", dated this round;
G2  REJECT view of the redline == the base (word for word);
G3  ACCEPTED (clean) == base + planned edits (r1120b_data.py) + "%" spacing + "note 14" -> "note b", where the ONLY
    other differences are table-footnote markers, each digit marker n replaced by the letter its table assigns
    (Table 1: 1-6, Table 2: 7-12, Table 3: 13-16, each restarting at "a"), and there are exactly 38 of them;
G4  no digit directly followed by "%" in the clean body; 40 more "<digit> %" than the base;
G5  the five new sources are cited in the body, have an entry in the references, and each entry sits between
    alphabetical neighbours;
G6  comments: Claude's 11-19 sources comment no longer gives the rate as IMBIE's; the two r1120 comments exist.
Exit 1 on any failure.
"""
import html, os, re, subprocess, sys, unicodedata, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from r1120b_data import EDITS, INSERTS, REFS, COMMENT_FIX, COMMENTS  # noqa: E402

base, red, clean = sys.argv[1:4]
fails = []
DATES = {"2026-11-20T12:00:00Z", "2026-11-20T12:30:00Z"}
SUP = "⁰¹²³⁴⁵⁶⁷⁸⁹"
N_MARKERS, N_PCT = 38, 40


def gate(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f": {detail}"))
    if not ok:
        fails.append(name)


def text(path, mode):
    h = subprocess.run(["pandoc", f"--track-changes={mode}", "-t", "html", "--wrap=none", path],
                       capture_output=True, text=True, check=True).stdout
    h = re.sub(r"<sup>([^<]*)</sup>", r"^(\1)", h)
    h = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(h)).strip()


def split_refs(t):
    i = t.rindex(" References ")
    return t[:i], t[i:]


# G1
x = zipfile.ZipFile(red).read("word/document.xml").decode("utf8")
marks = re.findall(r'<w:(?:ins|del) [^>]*w:author="([^"]*)" w:date="([^"]*)"', x)
gate("G1 authors and dates", bool(marks) and {a for a, _ in marks} == {"Claude", "Claude (style)"}
     and {dt for _, dt in marks} <= DATES, sorted({m for m in marks}))

# G2
B = text(base, "accept")
R = text(red, "reject")
bw, rw = B.split(), R.split()
gate("G2 reject view == base", bw == rw,
     next(((k, bw[max(0, k - 5):k + 5], rw[max(0, k - 5):k + 5]) for k, (p, q) in enumerate(zip(bw, rw)) if p != q),
          (len(bw), len(rw))))

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
assert exp.count("Table 3, note 14") == 2
exp = exp.replace("Table 3, note 14", "Table 3, note b")
body, refs = split_refs(exp)
exp = re.sub(r"(\d)%", r"\1 %", body) + refs
C = text(clean, "accept")
ew, cw = exp.split(), C.split()
mk = re.compile(r"^(.*?)([¹²³⁴⁵⁶⁷⁸⁹][⁰¹²³⁴⁵⁶⁷⁸⁹]?)([^⁰-⁹¹²³]*)$")
n_mark, bad = 0, None
if len(ew) != len(cw):
    bad = ("word counts", len(ew), len(cw),
           next(((k, ew[max(0, k - 5):k + 5], cw[max(0, k - 5):k + 5]) for k, (p, q) in enumerate(zip(ew, cw)) if p != q), None))
else:
    for k, (e, g) in enumerate(zip(ew, cw)):
        if e == g:
            continue
        m = mk.match(e)
        if m:
            n = int("".join(str(SUP.index(c)) for c in m.group(2)))
            first = 1 if n <= 6 else 7 if n <= 12 else 13
            if n <= 16 and g == f"{m.group(1)}^({'abcdef'[n - first]}){m.group(3)}":
                n_mark += 1
                continue
        bad = (k, ew[max(0, k - 5):k + 5], cw[max(0, k - 5):k + 5])
        break
gate("G3 accepted == base + planned edits, footnote markers mapped", bad is None and n_mark == N_MARKERS,
     bad or f"{n_mark} marker substitutions, expected {N_MARKERS}")

# G4
cb, _ = split_refs(C)
bb, _ = split_refs(B)
left = re.findall(r"\S{0,12}\d%", cb)
added = len(re.findall(r"\d %", cb)) - len(re.findall(r"\d %", bb))
gate("G4 no digit% in the body; 40 spaces added", not left and added == N_PCT, (left[:5], added))

# G5
cbody, crefs = split_refs(C)
NEW = [("Rohde and Hausfather, 2020", "Rohde, R. A. and Hausfather, Z.:"), ("Lenssen et al., 2024", "Lenssen, N.,"),
       ("GISTEMP Team, 2026", "GISTEMP Team:"), ("Fricko et al., 2017", "Fricko, O.,"), ("Gidden et al., 2019", "Gidden, M. J.,")]
para = [p for p in re.split(r"\n\s*\n", subprocess.run(["pandoc", "--track-changes=accept", "-t", "plain", "--wrap=none",
                                                            clean], capture_output=True, text=True, check=True).stdout)]
ri = next(i for i, p in enumerate(para) if p.strip() == "References")
entries = [p.strip() for p in para[ri + 1:] if p.strip()]
key = lambda s: unicodedata.normalize("NFKD", re.split(r"[,:]", s, maxsplit=1)[0]).encode("ascii", "ignore").decode().lower()
probs = []
for cite, lead in NEW:
    if cite not in cbody:
        probs.append(("not cited", cite))
    hit = [i for i, e in enumerate(entries) if e.startswith(lead)]
    if len(hit) != 1:
        probs.append(("entries", lead, len(hit)))
        continue
    i = hit[0]
    if not (key(entries[i - 1]) <= key(entries[i]) <= key(entries[i + 1])):
        probs.append(("order", entries[i - 1][:25], entries[i][:25], entries[i + 1][:25]))
gate("G5 new sources cited, listed, in order", not probs, probs)

# G6
probs = []
for path in (red, clean):
    c = zipfile.ZipFile(path).read("word/comments.xml").decode("utf8")
    if COMMENT_FIX[0] in c or html.escape(COMMENT_FIX[1], quote=False) not in c:
        probs.append(("sources comment", os.path.basename(path)))
    for _, t in COMMENTS:
        if c.count(html.escape(t[:60], quote=False)) != 1:
            probs.append(("new comment", t[:30], os.path.basename(path)))
gate("G6 comments", not probs, probs)

# G7 (r1120b): the sources thread carries the verification reply, and every comment in it is marked resolved
probs = []
for path in (red, clean):
    z = zipfile.ZipFile(path)
    c, ce = z.read("word/comments.xml").decode("utf8"), z.read("word/commentsExtended.xml").decode("utf8")
    t = lambda s: "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", s))
    thread = [m.group(0) for m in re.finditer(r"<w:comment [^>]*>.*?</w:comment>", c, re.S)
              if t(m.group(0)).startswith(("Claude 11-19, sources.", "Claude 11-20: checked."))]
    if len(thread) != 2:
        probs.append(("thread size", len(thread), os.path.basename(path)))
        continue
    for cm in thread:
        for pid in re.findall(r'w14:paraId="([0-9A-F]+)"', cm):
            if not re.search(r'<w15:commentEx w15:paraId="%s"[^>]*w15:done="1"' % pid, ce):
                probs.append(("not resolved", pid, os.path.basename(path)))
gate("G7 sources comment answered and resolved", not probs, probs)

print("ALL GATES PASS" if not fails else f"{len(fails)} GATE(S) FAILED: {fails}")
sys.exit(1 if fails else 0)
