"""Non-content normalisation: drop <w:lastRenderedPageBreak/> (a layout cache) and merge adjacent
<w:t> pieces inside one run, so each text run has a single <w:t>. Asserts the text is unchanged."""
import re, sys
p = sys.argv[1] + "/word/document.xml"
x = open(p, encoding="utf8").read()
txt = lambda s: "".join(re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", s))
t0 = txt(x)
x = x.replace("<w:lastRenderedPageBreak/>", "")
n = 0
while True:
    y = re.sub(r'<w:t(?: xml:space="preserve")?>([^<]*)</w:t><w:t(?: xml:space="preserve")?>([^<]*)</w:t>',
               r'<w:t xml:space="preserve">\1\2</w:t>', x)
    if y == x: break
    n += 1; x = y
assert txt(x) == t0, "text changed"
open(p, "w", encoding="utf8").write(x)
print("normalised; merge passes", n)
