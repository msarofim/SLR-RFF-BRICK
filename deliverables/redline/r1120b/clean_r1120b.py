"""Clean copy of round r1120b: the redline with every tracked change accepted (comments kept, as in the 11-12b clean
copy). String edits only; never writes the input.

    python clean_r1120b.py <redline.docx> <workdir> <out.docx>
"""
import os, re, subprocess, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from accept_lib import accept, remaining  # noqa: E402

src, W, out = sys.argv[1:4]
assert not os.path.exists(W) and not os.path.exists(out)
zipfile.ZipFile(src).extractall(W)
p = W + "/word/document.xml"
x = open(p, encoding="utf8").read()
n = remaining(x)
x = accept(x)
assert remaining(x) == 0 and "<w:delText" not in x, "tracked marks left"
open(p, "w", encoding="utf8").write(x)
subprocess.run(["zip", "-q", "-X", "-r", "-D", os.path.abspath(out), "."], cwd=W, check=True)
print(f"clean_r1120b: {n} tracked marks accepted -> {out}")
