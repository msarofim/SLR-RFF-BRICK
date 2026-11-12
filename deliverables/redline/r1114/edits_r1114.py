"""Round r1114: Claude's tracked edits on r1113 (2026-11-12). Run by build.sh on a fresh copy.

Marcus 11-12: "Put in item 2 and the Table 1 note as tracked edits. Drop FACTS land water post 2100 because it isn't
climate driven." Source: the FACTS module audit (memory facts_post2100_module_audit; SLR CHANGELOG 2026-11-12d).
  1. Sect. 4.2: the AR5 time-prescribed dynamics term belongs to ipccar5/icesheets, not to the Bamber and DeConto
     modules, which draw one trajectory per sample.
  2. Table 1 note 5: what each FACTS ice-sheet module does after 2100.
  3. Land water dropped past 2100: Sect. 4.2's list and the Fig. 3 caption lose it, and Figs. 3 and 6 are the
     re-renders (figures/paper, SLR 70df729).
"""
import hashlib, os, re, shutil, sys
from xml.sax.saxutils import escape
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
W = sys.argv[1]
sys.path.insert(0, HERE)
import edlib  # noqa: E402
from trackedit import AUTHOR, DATE, RUN_RE  # noqa: E402

d = edlib.open_doc(W + "/word/document.xml")
OWN = f'w:author="{AUTHOR}" w:date="{DATE}"'

## ---- data (verify_r1114.py execs this block) ----------------------------------------------------------------
## (context, old, new): plain runs or earlier pending insertions; contexts unique.
EDITS = [
    # Sect. 4.2, AR5 term (the later edit in the run first, so the earlier one finds its context in the first part)
    ("Antarctic dynamics term as a prescribed function", "Antarctic dynamics term as", "Antarctic module's dynamics term is"),
    ("2000–2099 with the AR5", " with", ","),
    # Table 1 note 5
    ("⁵ Ice-sheet modules extrapolate the 2080–2100 rate or sample 21st-century projections;",
     "Ice-sheet modules extrapolate the 2080–2100 rate or sample 21st-century projections",
     "In FACTS, Greenland (FittedISMIP) continues its 2080–2100 rate, the Bamber and DeConto modules follow "
     "trajectories selected by 2000–2099 warming, the AR5 Antarctic dynamics term is a function of time, and LARMIP "
     "drops forcing more than 200 years old"),
    # land water, Sect. 4.2 (Marcus's two 11-11 insertions) and the Fig. 3 caption (Claude 10-15 insertion)
    (": glaciers, thermal expan", ",", " and"),
    ("sion, and land-water storage, plus LARMIP Antarctica at 2150", ", and land-water storage", ""),
    ("(glaciers, thermal expansion and land-water storage; Sect. 4.2)", "glaciers, thermal expansion and land-water storage",
     "glaciers and thermal expansion"),
]
## Sect. 4.2: "select projections from" -> "select a projection for each sample from". The run "projections from "
## occurs twice in the document, so it is found as the first plain run after this anchor.
PROJ = dict(anchor="The Bamber and DeConto modules select ", run="projections from ", old="projections",
            new="a projection for each sample")
NEW_VALUES = [
    "The Bamber and DeConto modules select a projection for each sample from temperature integrated over 2000–2099, "
    "the AR5 Antarctic module's dynamics term is a prescribed function of time, and",
    "⁵ In FACTS, Greenland (FittedISMIP) continues its 2080–2100 rate, the Bamber and DeConto modules follow "
    "trajectories selected by 2000–2099 warming, the AR5 Antarctic dynamics term is a function of time, and LARMIP "
    "drops forcing more than 200 years old; ProFSea's Greenland uses the FACTS implementation.",
    "respond to the FaIR climate: glaciers and thermal expansion, plus LARMIP Antarctica at 2150.",
    "climate-driven at 2300 (glaciers and thermal expansion; Sect. 4.2)",
]
ABSENT = ["with the AR5 Antarctic dynamics term as", "sample 21st-century projections",
          "thermal expansion, and land-water storage, plus", "thermal expansion and land-water storage; Sect. 4.2"]
## Figure swaps: (paper figure, file in figures/paper). The image now shown is identified by the md5 of the render it
## replaces (SLR 3dd62ba era = the pre-11-12 renders, kept in the scratchpad control copy and in git at c22bb9a).
FIGSWAP = [("Fig. 3", "model_comparison_components_vv_L27_2300.png"), ("Fig. 6", "vv_responsiveness_L27.png")]
OLD_REV = "c22bb9a"                                           # SLR commit whose figures/paper renders are in r1113
## ---- end data ------------------------------------------------------------------------------------------------


def git_bytes(rev, path):
    import subprocess
    return subprocess.run(["git", "-C", REPO, "show", f"{rev}:{path}"], capture_output=True, check=True).stdout


def proj_edit():
    a = d.x.index(escape(PROJ["anchor"]))
    assert d.x.count(escape(PROJ["anchor"])) == 1
    m = RUN_RE.search(d.x, a + len(PROJ["anchor"]))
    while m and m.group(2) != PROJ["run"]:
        m = RUN_RE.search(d.x, m.end())
    assert m and m.start() - a < 3000, "run not found after the anchor"
    rpr, t = m.group(1), m.group(2)
    i = t.index(PROJ["old"])
    out = d._run(rpr, t[:i]) + d._del(rpr, PROJ["old"]) + d._ins(rpr, escape(PROJ["new"])) + d._run(rpr, t[i + len(PROJ["old"]):])
    d.x = d.x[:m.start()] + out + d.x[m.end():]
    d.log.append((PROJ["anchor"] + PROJ["run"], f"{PROJ['old']!r} -> {PROJ['new']!r}", "Sect. 4.2 (FACTS audit)"))


def visible_refs(x):
    out, open_ = [], 0
    for m in re.finditer(r'<(/?)w:(del|moveFrom)\b([^>]*?)(/?)>|r:embed="(rId\d+)"', x):
        if m.group(5):
            if open_ == 0:
                out.append((m.group(5), m.start()))
        elif m.group(4) != "/":
            open_ += -1 if m.group(1) else 1
    return out


def swap(fig, png, rels):
    old_md5 = hashlib.md5(git_bytes(OLD_REV, "figures/paper/" + png)).hexdigest()
    target = {rid: t for rid, t in re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels)}
    md5 = lambda t: hashlib.md5(open(os.path.join(W, "word", t), "rb").read()).hexdigest()
    hits = [(rid, pos) for rid, pos in visible_refs(d.x) if rid in target and md5(target[rid]) == old_md5]
    assert len(hits) == 1, f"{fig}: {len(hits)} visible images match the old render"
    rid, i = hits[0]
    s = max(d.x.rfind("<w:r>", 0, i), d.x.rfind("<w:r ", 0, i))
    e = d.x.index("</w:r>", i) + len("</w:r>")
    o = d.x.rfind("<w:ins ", 0, s)
    assert o > d.x.rfind("</w:ins>", 0, s), f"{fig}: the image is not in a pending insertion"
    oe = d.x.index(">", o) + 1
    assert d.x[oe:s] == "" and d.x[e:e + len("</w:ins>")] == "</w:ins>", f"{fig}: its insertion holds more than it"
    run = d.x[s:e]
    new_rid = "rId%d" % (max(int(k) for k in re.findall(r'Id="rId(\d+)"', rels)) + 1)
    tgt = "media/fig1114_" + png
    src = os.path.join(REPO, "figures", "paper", png)
    shutil.copyfile(src, os.path.join(W, "word", tgt))
    rels = rels.replace("</Relationships>", f'<Relationship Id="{new_rid}" Type="http://schemas.openxmlformats.org/'
                        f'officeDocument/2006/relationships/image" Target="{tgt}"/></Relationships>')
    cx = int(re.search(r'<wp:extent cx="(\d+)"', run).group(1))
    w_px, h_px = Image.open(src).size
    cy = round(cx * h_px / w_px)
    new = run.replace(f'r:embed="{rid}"', f'r:embed="{new_rid}"')
    new = re.sub(r'(<wp:extent cx="\d+" cy=")\d+(")', rf"\g<1>{cy}\2", new)
    new = re.sub(r'(<a:ext cx="\d+" cy=")\d+(")', rf"\g<1>{cy}\2", new)
    dpr = max(int(v) for v in re.findall(r'<wp:docPr id="(\d+)"', d.x)) + 1
    new = re.sub(r'<wp:docPr id="\d+"', f'<wp:docPr id="{dpr}"', new)
    new = re.sub(r'( descr=")[^"]*(")', rf"\g<1>figures/paper/{png}\2", new)
    d.x = (d.x[:s] + f'<w:del w:id="{d._id()}" {OWN}>{run}</w:del></w:ins>'
           + f'<w:ins w:id="{d._id()}" {OWN}>{new}</w:ins>' + d.x[e + len("</w:ins>"):])
    d.log.append((f"[{fig} image {rid}]", f"[image {new_rid}: figures/paper/{png}]", "FACTS land water dropped past 2100"))
    return rels


if __name__ == "__main__":
    for ctx, old, new in EDITS:
        edlib.edit(ctx, old, new, "FACTS audit / land water dropped past 2100")
    proj_edit()
    rels_p = W + "/word/_rels/document.xml.rels"
    rels = open(rels_p, encoding="utf8").read()
    for fig, png in FIGSWAP:
        rels = swap(fig, png, rels)
    open(rels_p, "w", encoding="utf8").write(rels)
    d.save()
    open(os.path.join(W, "..", os.path.basename(W) + "_log.txt"), "w", encoding="utf8").write(
        "\n".join(f"{a} | {b} | {c}" for a, b, c in d.log) + "\n")
    print(f"edits_r1114: {len(EDITS) + 1} text edits, {len(FIGSWAP)} figures")
