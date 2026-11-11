"""docx_review_extract.py -- READ-ONLY extraction of a reviewed .docx draft: accepted text per paragraph with Word's
last-rendered page number, every tracked change (author, date), and every comment (author, date, anchor, OPEN/DONE,
reply-to). Used to build the GMD guidance notes (2026-11-07, 2026-11-11).

  ~/climate-env/bin/python3 python/docx_review_extract.py <draft.docx> <outdir>
  ~/climate-env/bin/python3 python/docx_review_extract.py --author="Tony Wong" <draft.docx>

The first form writes <outdir>/paras.txt ("[p<page> #<para index><T if in a table>] text"), changes.txt and
comments.txt. The second prints that author's insertions that survive in the accepted text (>= 12 characters).
Run it on a COPY of the draft (Marcus may have the file open); it never writes to the docx. Page numbers come from
<w:lastRenderedPageBreak/>, so they match what Word showed at the last save. Word renumbers comment ids on every save:
refer to comments by page and first words, never by id.
"""
import os
import sys
import zipfile

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14 = "http://schemas.microsoft.com/office/word/2010/wordml"
W15 = "http://schemas.microsoft.com/office/word/2012/wordml"
q = lambda t: "{%s}%s" % (W, t)
local = lambda el: etree.QName(el).localname
in_del = lambda el: any(local(a) == "del" for a in el.iterancestors())


def accepted_text(el):
    """Text as it reads with every tracked change accepted (insertions kept, deletions dropped)."""
    s = []
    for t in el.iter():
        tag = local(t)
        if tag == "t" and not in_del(t):
            s.append(t.text or "")
        elif tag == "tab":
            s.append("\t")
    return "".join(s)


def walk(body):
    """Yield (page, index, paragraph) in document order, advancing the page at rendered page breaks."""
    page = 1
    for idx, p in enumerate(body.iter(q("p"))):
        for el in p.iter():
            tag = local(el)
            if tag == "lastRenderedPageBreak" or (tag == "br" and el.get(q("type")) == "page"):
                page += 1
                break
        yield page, idx, p


def surviving_insertions(src, author, min_len=12):
    body = etree.fromstring(zipfile.ZipFile(src).read("word/document.xml")).find(q("body"))
    for page, idx, p in walk(body):
        for ins in p.iter(q("ins")):
            if ins.get(q("author")) != author or in_del(ins):
                continue
            t = "".join(x.text or "" for x in ins.iter(q("t")) if not in_del(x)).strip()
            if len(t) >= min_len:
                print(f"p{page} #{idx}: {t}")


def extract(src, out):
    z = zipfile.ZipFile(src)
    body = etree.fromstring(z.read("word/document.xml")).find(q("body"))
    paras, changes, cpage = [], [], {}
    last_page = 1
    for page, idx, p in walk(body):
        last_page = page
        tbl = "T" if any(local(a) == "tbl" for a in p.iterancestors()) else ""
        for el in p.iter():
            tag = local(el)
            if tag in ("ins", "del"):
                t = "".join((x.text or "") for x in el.iter() if local(x) in ("t", "delText"))
                if t.strip():
                    changes.append((page, idx, tag, el.get(q("author")), (el.get(q("date")) or "")[:10], t))
            elif tag in ("commentRangeStart", "commentReference"):
                cpage.setdefault(el.get(q("id")), (page, idx))
        paras.append((page, idx, tbl, accepted_text(p)))
    # comment anchors: accepted text between each range start and end, in document order
    cur, anc = set(), {}
    for el in body.iter():
        tag = local(el)
        if tag == "commentRangeStart":
            cur.add(el.get(q("id")))
            anc.setdefault(el.get(q("id")), [])
        elif tag == "commentRangeEnd":
            cur.discard(el.get(q("id")))
        elif tag == "t" and cur and not in_del(el):
            for c in cur:
                anc[c].append(el.text or "")
    done, parent = {}, {}
    if "word/commentsExtended.xml" in z.namelist():
        for e in etree.fromstring(z.read("word/commentsExtended.xml")).iter("{%s}commentEx" % W15):
            pid = e.get("{%s}paraId" % W15)
            done[pid] = e.get("{%s}done" % W15) == "1"
            if e.get("{%s}paraIdParent" % W15):
                parent[pid] = e.get("{%s}paraIdParent" % W15)
    rows, pid2cid = [], {}
    if "word/comments.xml" in z.namelist():
        for c in etree.fromstring(z.read("word/comments.xml")).iter(q("comment")):
            cid, ps = c.get(q("id")), c.findall(q("p"))
            pids = [pp.get("{%s}paraId" % W14) for pp in ps]
            for pid in pids:
                pid2cid[pid] = cid
            rows.append((cid, c.get(q("author")), (c.get(q("date")) or "")[:10], pids[-1] if pids else None,
                         "\n  ".join(accepted_text(pp) for pp in ps)))
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "paras.txt"), "w") as f:
        for page, idx, tbl, txt in paras:
            if txt.strip():
                f.write(f"[p{page} #{idx}{tbl}] {txt}\n")
    with open(os.path.join(out, "changes.txt"), "w") as f:
        for page, idx, kind, a, d, t in changes:
            f.write(f"[p{page} #{idx}] {kind} {a} {d}: {t}\n")
    n_open = 0
    with open(os.path.join(out, "comments.txt"), "w") as f:
        for cid, a, d, pid, t in rows:
            page, idx = cpage.get(cid, ("?", "?"))
            is_done = done.get(pid, False)
            n_open += not is_done
            rep = f" | reply to #{pid2cid.get(parent[pid], '?')}" if pid in parent else ""
            f.write(f"=== #{cid} page {page} para {idx} | {a} {d} | {'DONE' if is_done else 'OPEN'}{rep}\n"
                    f"  ANCHOR: {''.join(anc.get(cid, []))[:200]}\n  {t}\n")
    print(f"{len(paras)} paras, {len(changes)} changes, {len(rows)} comments ({n_open} open); last page {last_page}")


if __name__ == "__main__":
    if sys.argv[1].startswith("--author="):
        surviving_insertions(sys.argv[2], sys.argv[1].split("=", 1)[1])
    else:
        extract(sys.argv[1], sys.argv[2])
