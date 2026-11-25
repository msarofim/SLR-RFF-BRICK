"""Submission copy of the GMD manuscript: the accepted clean text (r1125: the 11-22d text + the Mimi.jl SWHID) with continuous line numbers and a centred page number in
the footer (GMD: "All pages must be numbered consecutively and line numbers must be included"). String edits only
(never ElementTree); never writes the input. Marcus 11-22: "yes, build r1123 and the submission PDF".

    python make_submission.py <clean.docx> <workdir> <out.docx>

Gates
  [LNNUM]     the section carries exactly one continuous, count-by-1 line numbering element, placed after pgMar.
  [FOOTER]    one footer part, typed in [Content_Types].xml, related from document.xml.rels, referenced first in the
              sectPr, holding a PAGE field.
  [LIGATURES] the document defaults no longer request contextual ligatures (see the note at that step).
  [TEXT-SAME] the body text read by pandoc (an independent reader) is identical in the input and the output.
The PDF itself is rendered by Word (word_render.applescript) and checked by check_submission_pdf.py.
"""
import html, os, re, subprocess, sys, zipfile

src, W, out = sys.argv[1:4]
assert not os.path.exists(W) and not os.path.exists(out)
zipfile.ZipFile(src).extractall(W)
fails = []


def gate(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f": {detail}"))
    if not ok:
        fails.append(name)


RID = "rIdSubmissionFooter1"
LNNUM = '<w:lnNumType w:countBy="1" w:restart="continuous"/>'
FOOTER = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
          '<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
          '<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
          '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
          '<w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
          '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
          '<w:r><w:t>1</w:t></w:r>'
          '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:ftr>')
CT = ('<Override PartName="/word/footer1.xml" '
      'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>')
REL = (f'<Relationship Id="{RID}" '
       'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>')

p_doc, p_rel, p_ct = (os.path.join(W, *p.split("/")) for p in
                      ("word/document.xml", "word/_rels/document.xml.rels", "[Content_Types].xml"))
assert not os.path.exists(os.path.join(W, "word", "footer1.xml")), "input already has a footer1.xml"
x = open(p_doc, encoding="utf8").read()
assert x.count("<w:sectPr") == 1 and "lnNumType" not in x and "footerReference" not in x, "unexpected section setup"
x = re.sub(r"(<w:sectPr[^>]*>)", r'\1<w:footerReference w:type="default" r:id="%s"/>' % RID, x, count=1)
x = re.sub(r"(<w:pgMar [^>]*/>)", r"\1" + LNNUM, x, count=1)
open(p_doc, "w", encoding="utf8").write(x)
## Ligatures off in the document defaults: with "standardContextual", Word for Mac's PDF export writes Calibri's "ti"
## ligature with a wrong text mapping ("calibraMon" in pdftotext, 2026-11-22), which garbles copied and indexed text.
p_sty = os.path.join(W, "word", "styles.xml")
s = open(p_sty, encoding="utf8").read()
dd = re.search(r"<w:docDefaults>.*?</w:docDefaults>", s, re.S)
assert dd and dd.group(0).count('w14:ligatures w14:val="standardContextual"') == 1, "docDefaults ligature setting changed"
s = s[:dd.start()] + dd.group(0).replace('w14:ligatures w14:val="standardContextual"', 'w14:ligatures w14:val="none"') \
    + s[dd.end():]
open(p_sty, "w", encoding="utf8").write(s)
open(os.path.join(W, "word", "footer1.xml"), "w", encoding="utf8").write(FOOTER)
r = open(p_rel, encoding="utf8").read()
assert RID not in r
open(p_rel, "w", encoding="utf8").write(r.replace("</Relationships>", REL + "</Relationships>", 1))
c = open(p_ct, encoding="utf8").read()
open(p_ct, "w", encoding="utf8").write(c.replace("</Types>", CT + "</Types>", 1))
subprocess.run(["zip", "-q", "-X", "-r", "-D", os.path.abspath(out), "."], cwd=W, check=True)

# gates, read back from the written file
z = zipfile.ZipFile(out)
d = z.read("word/document.xml").decode("utf8")
sect = re.search(r"<w:sectPr[^>]*>(.*?)</w:sectPr>", d, re.S).group(1)
gate("LNNUM", d.count("<w:lnNumType") == 1 and re.search(r"<w:pgMar [^>]*/>" + re.escape(LNNUM), sect) is not None,
     sect)
gate("FOOTER", "word/footer1.xml" in z.namelist() and " PAGE " in z.read("word/footer1.xml").decode("utf8")
     and z.read("[Content_Types].xml").decode("utf8").count("/word/footer1.xml") == 1
     and z.read("word/_rels/document.xml.rels").decode("utf8").count(RID) == 1
     and sect.startswith(f'<w:footerReference w:type="default" r:id="{RID}"/>'), sect[:120])


sty = z.read("word/styles.xml").decode("utf8")
gate("LIGATURES", "standardContextual" not in re.search(r"<w:docDefaults>.*?</w:docDefaults>", sty, re.S).group(0),
     "docDefaults still request contextual ligatures")


def text(path):
    h = subprocess.run(["pandoc", "-t", "html", "--wrap=none", path], capture_output=True, text=True, check=True).stdout
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


gate("TEXT-SAME", text(src) == text(out), "body text differs")
print("ALL GATES PASS" if not fails else f"FAILED: {fails}")
sys.exit(1 if fails else 0)
