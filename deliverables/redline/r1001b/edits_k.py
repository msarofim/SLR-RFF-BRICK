"""10-01b edit set K: FIG 1 re-rendered to end in 2025 (plot_hindcast_components.py X1 = 2025), tracked swap."""
import os, re, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image
from trackedit import Doc
W = sys.argv[1]
R = os.path.join(HERE, "..", "..", "..", "figures", "paper") + "/"
d = Doc(W + "/word/document.xml")
rels_p = W + "/word/_rels/document.xml.rels"
rels = open(rels_p, encoding="utf8").read()
nid = max(int(i) for i in re.findall(r'Id="rId(\d+)"', rels)) + 1
png, new, tgt = "hindcast_components_L27.png", f"rId{nid}", "media/fig1001b_hindcast_components_L27.png"
shutil.copy(R + png, W + "/word/" + tgt)
rels = rels.replace("</Relationships>",
    f'<Relationship Id="{new}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="{tgt}"/></Relationships>')
w_px, h_px = Image.open(R + png).size
d.swap_image("rId4", new, round(5334000 * h_px / w_px), "figures/paper/" + png, "FIG 1 to 2025 (Marcus 10-01)")
open(rels_p, "w", encoding="utf8").write(rels)
d.save()
for o, n, w in d.log: print(f"- {o[:60]!r} -> {n[:60]!r}")
