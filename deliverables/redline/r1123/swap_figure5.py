"""Swap the 300-dpi Fig. 5 render into a GMD manuscript copy (2026-11-22). String edits only (never ElementTree); never
writes the input. Marcus 11-22: "If we are rebuilding the zip, should we fix Figure 5 at the same time?" (yes).

    python swap_figure5.py <in.docx> <workdir> <out.docx> <new Fig. 5 png>

Finds the image whose drawing names figures/paper/vv_gsic_ladrillo_L27_2300_joint.png, replaces its media part with the
new render, and keeps the placed width (cx) while setting the height (cy, in both wp:extent and a:ext) to the new
image's aspect ratio. An image swap is not a tracked change; apply it to whatever copy is current.

Gates
  [OLD]     the replaced part is the 150-dpi render the paper carried (md5 81e64dae...), so a second run cannot swap the
            wrong file or swap twice silently.
  [NEW]     the part now has the new render's bytes, at >= 300 dpi over the placed width.
  [OTHERS]  every other part of the package is byte-identical to the input's.
  [TEXT]    the body text read by pandoc is identical (an image swap must not touch text).
"""
import hashlib, html, os, re, struct, subprocess, sys, zipfile

src, W, out, png = sys.argv[1:5]
assert not os.path.exists(W) and not os.path.exists(out)
DESCR = "figures/paper/vv_gsic_ladrillo_L27_2300_joint.png"
OLD_MD5 = "81e64daeeb9abeb8c3a3d31d1a2d6c5c"
EMU_PER_IN, MIN_DPI = 914400, 300
fails = []


def gate(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f": {detail}"))
    if not ok:
        fails.append(name)


zipfile.ZipFile(src).extractall(W)
doc_p = os.path.join(W, "word", "document.xml")
x = open(doc_p, encoding="utf8").read()
blocks = [m for m in re.finditer(r"<w:drawing>.*?</w:drawing>", x, re.S) if f'descr="{DESCR}"' in m.group(0)]
assert len(blocks) == 1, f"expected one drawing for {DESCR}, found {len(blocks)}"
blk = blocks[0].group(0)
rid = re.search(r'r:embed="([^"]+)"', blk).group(1)
rels = open(os.path.join(W, "word", "_rels", "document.xml.rels"), encoding="utf8").read()
target = re.search(r'<Relationship Id="%s"[^>]*Target="([^"]+)"' % re.escape(rid), rels).group(1)
part = os.path.join(W, "word", *target.split("/"))
old = open(part, "rb").read()
gate("OLD", hashlib.md5(old).hexdigest() == OLD_MD5, hashlib.md5(old).hexdigest())

new = open(png, "rb").read()
w, h = struct.unpack(">II", new[16:24])                          # PNG IHDR width, height
cx = int(re.search(r'<wp:extent cx="(\d+)"', blk).group(1))
cy = round(cx * h / w)
blk2 = re.sub(r'(<wp:extent cx="\d+" cy=")\d+(")', r"\g<1>%d\2" % cy, blk, count=1)
blk2 = re.sub(r'(<a:ext cx="\d+" cy=")\d+(")', r"\g<1>%d\2" % cy, blk2, count=1)
assert blk2.count(f'cy="{cy}"') == 2, "did not find both extents"
x = x[:blocks[0].start()] + blk2 + x[blocks[0].end():]
open(doc_p, "w", encoding="utf8").write(x)
open(part, "wb").write(new)
subprocess.run(["zip", "-q", "-X", "-r", "-D", os.path.abspath(out), "."], cwd=W, check=True)

zi, zo = zipfile.ZipFile(src), zipfile.ZipFile(out)
pname = "word/" + target
dpi = w / (cx / EMU_PER_IN)
gate("NEW", zo.read(pname) == new and dpi >= MIN_DPI, f"{w} px over {cx / EMU_PER_IN:.2f} in = {dpi:.0f} dpi")
diff = [n for n in zi.namelist() if n not in (pname, "word/document.xml") and zi.read(n) != zo.read(n)]
gate("OTHERS", not diff and sorted(zi.namelist()) == sorted(zo.namelist()), diff)


def text(path):
    hh = subprocess.run(["pandoc", "-t", "html", "--wrap=none", path], capture_output=True, text=True, check=True).stdout
    hh = re.sub(r"<img [^>]*>", " ", hh)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", hh))).strip()


gate("TEXT", text(src) == text(out), "body text differs")
print(f"Fig. 5: {w} x {h} px, placed {cx / EMU_PER_IN:.2f} in wide ({dpi:.0f} dpi), height cy {cy}")
print("ALL GATES PASS" if not fails else f"FAILED: {fails}")
sys.exit(1 if fails else 0)
