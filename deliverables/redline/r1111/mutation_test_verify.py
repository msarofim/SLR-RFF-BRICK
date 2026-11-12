"""Mutation test of verify_r1111.py: each mutant breaks one property of a built output; the gate must FAIL.
    python mutation_test_verify.py <base.docx> <out.docx>
  V1 (check 2) an untracked text change: one plain-run word altered outside any tracked change
  V2 (check 1) an insertion nested inside another insertion
  V3 (check 3) one of the round's new values (the Lin et al. 2026 entry) removed with its insertion
  V4 (check 2) an untracked word change inside a Sect. 3.3 list item (text in a paragraph this round split)
  V5 (check 2) one Sect. 3.3 paragraph break made untracked (its inserted mark removed)
  V6 (check 4) the Sect. 2.2.2 join undone (its deleted paragraph mark removed)
  V7 (check 4) one moved Table 3 note left in place (its deletion unwrapped into plain text)
"""
import os, re, subprocess, sys, tempfile, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from verify_r1111 import read_xml, write_with
base, out = sys.argv[1:3]
x = read_xml(out)
def v1(x):
    i = x.index("Discrepancy terms.")
    assert x.rfind("<w:ins ", 0, i) <= x.rfind("</w:ins>", 0, i), "V1 target is inside an insertion"
    return x[:i] + x[i:].replace("Discrepancy terms.", "Discrepancy term.", 1)
def v2(x):
    m = re.search(r'(<w:ins w:id="\d+" w:author="Claude" w:date="2026-11-11T23:00:00Z">)(<w:r>.*?</w:r>)(</w:ins>)', x, re.S)
    return x[:m.start()] + m.group(1) + '<w:ins w:id="999999" w:author="Claude" w:date="2026-11-11T23:00:00Z">' + \
        m.group(2) + "</w:ins>" + m.group(3) + x[m.end():]
def v3(x):
    m = re.search(r'<w:ins w:id="\d+" w:author="Claude" w:date="2026-11-11T23:00:00Z"><w:r>(?:<w:rPr>.*?</w:rPr>)?'
                  r'<w:t xml:space="preserve">Lin, Y\., Zhang.*?</w:ins>', x, re.S)
    return x[:m.start()] + x[m.end():]
OWN = 'w:author="Claude" w:date="2026-11-11T23:00:00Z"'
def v4(x):
    return x.replace("(ii) the glacier component, as called", "(ii) the glacier components, as called", 1)
def v5(x):
    i = x.index("equal the committed input files;")
    k = x.rindex("<w:p>", 0, i)
    m = re.compile(r'<w:ins w:id="\d+" ' + OWN + '/>').search(x, k, i)
    return x[:m.start()] + x[m.end():]
def v6(x):
    i = x.index("Greenland melt occurs through")
    k = max(x.rfind("<w:p ", 0, i), x.rfind("<w:p>", 0, i))
    m = re.compile(r'<w:del w:id="\d+" ' + OWN + '/>').search(x, k, i)
    return x[:m.start()] + x[m.end():]
def v7(x):
    m = re.search(r'<w:del w:id="\d+" ' + OWN + r'>(<w:r>(?:(?!</w:del>).)*?<w:delText xml:space="preserve">[^<]*²² md5[^<]*</w:delText></w:r>)</w:del>', x, re.S)
    return x[:m.start()] + m.group(1).replace("<w:delText", "<w:t").replace("</w:delText>", "</w:t>") + x[m.end():]
res = []
for name, f in (("V1", v1), ("V2", v2), ("V3", v3), ("V4", v4), ("V5", v5), ("V6", v6), ("V7", v7)):
    y = f(x); assert y != x, name
    with tempfile.TemporaryDirectory() as t:
        p = os.path.join(t, "m.docx"); write_with(out, y, p)
        r = subprocess.run([sys.executable, os.path.join(HERE, "verify_r1111.py"), base, p], capture_output=True, text=True)
    fails = [l for l in r.stdout.splitlines() if "FAIL" in l and not l.startswith("[VERIFY] FAIL")]
    res.append(f"{name}: {'KILLED' if r.returncode else 'SURVIVED'}  {fails[0][:110] if fails else ''}")
    print(res[-1])
open(os.path.join(HERE, "mutation_result_verify.txt"), "w").write("\n".join(res) + "\n")
