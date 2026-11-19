"""Accept Tony Wong's tracked changes in his 11-19 file (Marcus 11-19: "go ahead"). String edits only."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from accept_lib import accept, remaining  # noqa: E402

p = sys.argv[1] + "/word/document.xml"
x = open(p, encoding="utf8").read()
authors = set(re.findall(r'<w:(?:ins|del|rPrChange|pPrChange) [^>]*w:author="([^"]*)"', x))
assert authors == {"Tony Wong"}, authors
n = remaining(x, "Tony Wong")
x = accept(x, "Tony Wong")
assert remaining(x) == 0, remaining(x)
open(p, "w", encoding="utf8").write(x)
print(f"accept_tony: {n} tracked marks by Tony Wong accepted")
