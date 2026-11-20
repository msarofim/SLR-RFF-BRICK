"""Gates for round r1120c, read with an INDEPENDENT reader (pandoc, HTML writer, tags stripped to text; sub/superscripts
written _(x) / ^(x)), not with the code that built the files.

    python verify_r1120c.py <base.docx> <redline.docx> <clean.docx>

The base carries three pending tracked marks by Marcus, so G2/G3 compare the REJECT-ALL and ACCEPT-ALL views.
G1  new tracked marks are by "Claude" / "Claude (notation)" with this round's dates; Marcus's three marks are still there
    with the same type, author, date and text;
G2  REJECT-ALL view of the redline == REJECT-ALL view of the base;
G3  ACCEPT-ALL (clean) == ACCEPT-ALL of the base + the planned edits (r1120c_data.py), with the notation renames applied
    as string edits on the text;
G4  symbols: no kappa_DAIS, three kappa_P (text + Table A1 twice), no w_r, no "shape S", the block paragraph has ten
    _(g) and no _(b), Greenland's basin index _(b) is still used elsewhere;
G5  Table 2's BRICK 2.0 cell and note a equal the diagnostic CSV (outputs/diag_brick_gsic_melt_1850_2000.csv) rounded.
Exit 1 on any failure.
"""
import csv, html, os, re, subprocess, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from r1120c_data import EDITS, INSERTS, TEXT_NOTATION, BLOCK_PARA, N_BLOCK_SUB  # noqa: E402

base, red, clean = sys.argv[1:4]
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
fails = []
DATES = {"2026-11-20T15:00:00Z", "2026-11-20T15:30:00Z"}


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
     bool(mine) and {m[1] for m in mine} == {"Claude", "Claude (notation)"} and {m[2] for m in mine} <= DATES
     and his_red == his_base and len(his_base) == 3,
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
for ctx, old, new, n in TEXT_NOTATION:
    assert exp.count(ctx) == n, ("G3 notation context", ctx, exp.count(ctx))
    exp = exp.replace(ctx, ctx.replace(old, new))
i, j = exp.index(BLOCK_PARA[0]), exp.index(BLOCK_PARA[1])
seg = exp[i:j]
assert seg.count("_(b)") == N_BLOCK_SUB, seg.count("_(b)")
exp = exp[:i] + seg.replace("_(b)", "_(g)").replace("Each block b ", "Each block g ", 1) + exp[j:]
C = text(clean, "accept")
ew, cw = exp.split(), C.split()
gate("G3 accept-all == base accept-all + planned edits", ew == cw, first_diff(ew, cw))

# G4
i, j = C.index(BLOCK_PARA[0].replace("block b", "block g")), C.index(BLOCK_PARA[1])
blk = C[i:j]
checks = {"kappa_DAIS": C.count("κ_(DAIS)") == 0, "kappa_P x3": C.count("κ_(P)") == 3, "w_r": C.count("w_(r)") == 0,
          "shape S": "shape S " not in C, "block _(g) x10": blk.count("_(g)") == N_BLOCK_SUB,
          "block _(b) none": blk.count("_(b)") == 0, "basin _(b) kept": C.count("_(b)") >= 5,
          "alpha_DAIS kept": C.count("α_(DAIS)") == 2, "T_(ref) in Table A3": "T_(ref) Reference temperature" in C}
gate("G4 symbols", all(checks.values()), [k for k, v in checks.items() if not v])

# G5
rows = {r["quantity"]: r for r in csv.DictReader(open(os.path.join(REPO, "outputs", "diag_brick_gsic_melt_1850_2000.csv")))}
f1 = lambda q, k: f"{float(rows[q][k]):.1f}".replace("-", "−")
f0 = lambda q, k: f"{float(rows[q][k]):.0f}"
cell = f"{f1('remaining_at_2000_s0incl_cm', 'p50')} ({f0('remaining_at_2000_s0incl_cm', 'p05')}–" \
       f"{f0('remaining_at_2000_s0incl_cm', 'p95')})"
note = (f"Calibrated volume {f1('glaciers_v0_cm', 'p50')} cm (5–95 % {f1('glaciers_v0_cm', 'p05')}–"
        f"{f1('glaciers_v0_cm', 'p95')}), less the 1850 starting value of BRICK 2.0’s glacier term (median "
        f"{f1('glaciers_s0_cm', 'p50')} cm, 5–95 % {f1('glaciers_s0_cm', 'p05')} to {f1('glaciers_s0_cm', 'p95')}), "
        f"which its melt equation counts against that volume, and {f1('gsic_melt_1850_to_2000_cm', 'p50')} cm")
gate("G5 Table 2 BRICK 2.0 inventory = diagnostic CSV", f"{cell}^(a)" in C and note in C, (cell, note[:80]))

print("ALL GATES PASS" if not fails else f"{len(fails)} GATE(S) FAILED: {fails}")
sys.exit(1 if fails else 0)
