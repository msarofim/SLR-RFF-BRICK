"""Round r1112: Claude's tracked edits on Marcus's 07:59 save of r1111b (2026-11-12). Run by build.sh on a fresh copy.

Marcus 11-12: "Yes, add the c_R edits and cut panel (a)'s title." He had moved Figs. 5 and 6 into Sect. 4.3 himself
(Word recorded the images as his deletion at the old place and his insertion at the new one) and changed the NOAA
acknowledgment to "provided by".
  1. Table A1: the runoff-line slope is c_R in the T_on row and the caption, as in the ais_c row and Sect. 2.2.3.
  2. Fig. 5 at its new place: the image Marcus inserted is deleted (a Claude deletion inside his insertion) and the
     re-render with the short panel (a) title "(a)  GMST forcing" is inserted beside it. The copy at the old place is
     already his deletion and is left alone.
  3. A reply on the r1111 Fig. 5 comment.
"""
import os, re, shutil, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
W = sys.argv[1]
sys.path.insert(0, HERE)
import edlib  # noqa: E402
from trackedit import AUTHOR, DATE  # noqa: E402

d = edlib.open_doc(W + "/word/document.xml")
OWN = f'w:author="{AUTHOR}" w:date="{DATE}"'

## (context, prefix, inserted text, why). verify_r1112.py reads CR, NEW_VALUES and ABSENT.
CR = [("T_on = −h₀/c (sampled", "T_on = −h₀/c", "_R", "Table A1 T_on row: c_R, as in the ais_c row"),
      ("(h₀ = −T_on·c).", "(h₀ = −T_on·c", "_R", "Table A1 caption: c_R, as in the ais_c row")]
NEW_VALUES = ["T_on = −h₀/c_R (sampled in place of h₀)", "(h₀ = −T_on·c_R)."]
ABSENT = ["−h₀/c (", "−T_on·c)"]

## Fig. 5: the image Marcus inserted at the figure's new place (07:58) is the second reference to FIG5_RID.
FIG5_RID, FIG5_MOVER = "rId24", "Marcus Sarofim"
FIG5_PNG = "vv_gsic_ladrillo_L27_2300_joint.png"            # figures/paper/, rendered 11-12 with the short (a) title
FIG5_MEDIA = "media/fig1112_" + FIG5_PNG

REPLY_TO = "joint-arm image is in"                           # the r1111 Fig. 5 comment (moved with the caption)
REPLY = ("Claude 11-12 (r1112): panel (a) is now titled '(a) GMST forcing', your call 11-12; only that title line "
         "changed. The image swap is at the figure's new place. The move is done (yours, 07:58), so this comment can "
         "be closed.")


def swap_fig5():
    key = f'r:embed="{FIG5_RID}"'
    hits = [m.start() for m in re.finditer(re.escape(key), d.x)]
    assert len(hits) == 2, f"{FIG5_RID}: {len(hits)} references, expected 2 (old place deleted, new place inserted)"
    ## the old place: inside a deletion by the mover; left as it is
    pre0 = d.x[:hits[0]]
    o0 = pre0.rfind("<w:del ")
    assert o0 > pre0.rfind("</w:del>") and f'w:author="{FIG5_MOVER}"' in d.x[o0:o0 + 200], "old place is not deleted"
    ## the new place: one run, alone in an insertion by the mover
    i = hits[1]
    s = max(d.x.rfind("<w:r>", 0, i), d.x.rfind("<w:r ", 0, i))
    e = d.x.index("</w:r>", i) + len("</w:r>")
    o = d.x.rfind("<w:ins ", 0, s)
    assert o > d.x.rfind("</w:ins>", 0, s) and f'w:author="{FIG5_MOVER}"' in d.x[o:o + 200], "new place not inserted"
    oe = d.x.index(">", o) + 1
    assert d.x[oe:s] == "" and d.x[e:e + len("</w:ins>")] == "</w:ins>", "the insertion holds more than the image"
    run = d.x[s:e]
    ## the new image: relationship, media file, and the same width
    rels_p = W + "/word/_rels/document.xml.rels"
    rels = open(rels_p, encoding="utf8").read()
    new_rid = "rId%d" % (max(int(k) for k in re.findall(r'Id="rId(\d+)"', rels)) + 1)
    src = os.path.join(REPO, "figures", "paper", FIG5_PNG)
    shutil.copyfile(src, os.path.join(W, "word", FIG5_MEDIA))
    rels = rels.replace("</Relationships>", f'<Relationship Id="{new_rid}" Type="http://schemas.openxmlformats.org/'
                        f'officeDocument/2006/relationships/image" Target="{FIG5_MEDIA}"/></Relationships>')
    open(rels_p, "w", encoding="utf8").write(rels)
    cx = int(re.search(r'<wp:extent cx="(\d+)"', run).group(1))
    w_px, h_px = Image.open(src).size
    cy = round(cx * h_px / w_px)
    new = run.replace(key, f'r:embed="{new_rid}"')
    new = re.sub(r'(<wp:extent cx="\d+" cy=")\d+(")', rf"\g<1>{cy}\2", new)
    new = re.sub(r'(<a:ext cx="\d+" cy=")\d+(")', rf"\g<1>{cy}\2", new)
    dpr = max(int(v) for v in re.findall(r'<wp:docPr id="(\d+)"', d.x)) + 1
    new = re.sub(r'<wp:docPr id="\d+"', f'<wp:docPr id="{dpr}"', new)
    new = re.sub(r'( descr=")[^"]*(")', rf"\g<1>figures/paper/{FIG5_PNG}\2", new)
    out = (f'<w:del w:id="{d._id()}" {OWN}>{run}</w:del></w:ins>'
           f'<w:ins w:id="{d._id()}" {OWN}>{new}</w:ins>')
    d.x = d.x[:s] + out + d.x[e + len("</w:ins>"):]
    d.log.append((f"[image {FIG5_RID}, new place]", f"[image {new_rid}: figures/paper/{FIG5_PNG}]",
                  "Fig. 5 re-rendered with the short panel (a) title"))
    return new_rid


if __name__ == "__main__":
    for ctx, prefix, new, why in CR:
        edlib.ins(ctx, prefix, new, why)
    rid = swap_fig5()
    d.save()
    import comments_lib as cl
    c = open(W + "/word/comments.xml", encoding="utf8").read()
    pid = [m.group(1) for m in re.finditer(r'<w:comment w:id="(\d+)"[^>]*>((?:(?!</w:comment>).)*)</w:comment>', c, re.S)
           if REPLY_TO in re.sub(r"<[^>]+>", "", m.group(2))]
    assert len(pid) == 1, pid
    cl.reply(int(pid[0]), REPLY)
    open(os.path.join(W, "..", os.path.basename(W) + "_log.txt"), "w", encoding="utf8").write(
        "\n".join(f"{a} | {b} | {c}" for a, b, c in d.log) + "\n")
    print(f"edits_r1112: {len(CR)} c_R insertions, Fig. 5 swapped to {rid}, 1 reply")
