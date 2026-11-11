def para_text(s, e):
    """Accepted text of the paragraph [s, e): w:t contents (Tony's insertions included), w:delText excluded."""
    return unescape("".join(re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", d.x[s:e])))


def candidates(old_esc):
    out = [m for m in RUN_RE.finditer(d.x) if old_esc in m.group(2) and not _in_tracked(d.x, m.start())]
    out += [m for m in edlib.INS_PAT.finditer(d.x) if old_esc in m.group(4)]
    return out


def place(e):
    """The single run (plain, or an earlier author's pending insertion) holding e['old'] in e's paragraph/cell."""
    o = escape(e["old"])
    hits = candidates(o)
    if len(hits) > 1 and e.get("anchor"):
        a = e["anchor"]
        hits = [m for m in hits if a in para_text(*_para_bounds(d.x, m.start()))]
    if len(hits) > 1 and e["category"] == "table":
        hits = [m for m in hits if cell_ok(m, e)]
    return hits


def cell_ok(m, e):
    """For a table entry: the hit sits in table `docx_table_index`, in the row whose first cell is `row_label`."""
    s = d.x.rfind("<w:tr", 0, m.start()); t = d.x.index("</w:tr>", m.start())
    row = d.x[s:t]
    first = unescape("".join(re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", row.split("</w:tc>")[0])))
    tbl_start = d.x.rfind("<w:tbl>", 0, m.start())
    idx = d.x.count("<w:tbl>", 0, tbl_start + 1) - 1
    if first.strip() != e.get("row_label", "").strip() or idx != e.get("docx_table_index", idx):
        return False
    if "column" not in e:
        return True
    col = row[:m.start() - s].count("</w:tc>")            # this hit's cell index in its row
    hdr = d.x[tbl_start:d.x.index("</w:tr>", tbl_start)].split("</w:tc>")
    names = [unescape("".join(re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", c))).strip() for c in hdr]
    return col < len(names) and names[col] == e["column"].strip()


def cell_bounds(e):
    """(start, end) of the cell of table `docx_table_index`, row `row_label`, column `column`."""
    tbls = [m.start() for m in re.finditer(r"<w:tbl>", d.x)]
    ts = tbls[e["docx_table_index"]]; te = d.x.index("</w:tbl>", ts)
    rows = [(m.start(), m.end()) for m in re.finditer(r"<w:tr[ >].*?</w:tr>", d.x[ts:te], re.S)]
    cellsof = lambda rs, re_: [(rs + c.start(), rs + c.end()) for c in re.finditer(r"<w:tc>.*?</w:tc>", d.x[rs:re_], re.S)]
    txt = lambda a, b: unescape("".join(re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", d.x[a:b]))).strip()
    hdr = [txt(*c) for c in cellsof(ts + rows[0][0], ts + rows[0][1])]
    out = []
    for r0, r1 in rows:
        cs = cellsof(ts + r0, ts + r1)
        if cs and txt(*cs[0]) == e["row_label"].strip() and e["column"].strip() in hdr:
            k = hdr.index(e["column"].strip())
            if k < len(cs):
                out.append(cs[k])
    return out


def bold_rpr(rpr, bold):
    rpr = rpr or "<w:rPr></w:rPr>"
    rpr = re.sub(r"<w:b/>|<w:bCs/>|<w:b w:val=\"[^\"]*\"/>", "", rpr)
    if bold:
        rpr = rpr.replace("<w:rPr>", "<w:rPr><w:b/><w:bCs/>", 1)
    return rpr if rpr != "<w:rPr></w:rPr>" else ""


def apply(e):
    if e.get("op") == "insert_paragraph_after":
        d.insert_para(e["anchor"], e["new"], why=e["id"])
        return "ok"
    hits = place(e)
    if len(hits) != 1:
        return f"SKIP ({len(hits)} runs hold the old span)"
    m = hits[0]; o, n = escape(e["old"]), escape(e["new"])
    plain = m.re is RUN_RE
    rpr, t = (m.group(1), m.group(2)) if plain else (m.group(3), m.group(4))
    if t.count(o) != 1:
        return f"SKIP (old occurs {t.count(o)}x in its run)"
    i = t.index(o)
    nrpr = rpr
    if e.get("table") == "Table 4":                       # Table 4 bolds a ratio below 1 (its caption)
        try:
            nrpr = bold_rpr(rpr, float(e["new"]) < 1)
        except ValueError:
            pass
    if plain:
        out = d._run(rpr, t[:i]) + d._del(rpr, o) + d._ins(nrpr, n) + d._run(rpr, t[i + len(o):])
    else:                                                 # inside an earlier author's insertion: split it, nest the deletion
        attrs = m.group(2)
        half = lambda s: f'<w:ins w:id="{d._id()}" {attrs}><w:r>{rpr}{d._t(s)}</w:r></w:ins>' if s else ""
        out = (half(t[:i]) + f'<w:ins w:id="{d._id()}" {attrs}>' + d._del(rpr, o) + "</w:ins>"
               + d._ins(nrpr, n) + half(t[i + len(o):]))
    d.x = d.x[:m.start()] + out + d.x[m.end():]
    d.log.append((e["id"], f"{e['old']!r} -> {e['new']!r}", e.get("source", "")[:60]))
    return "ok" + ("" if plain else " (inside Tony's insertion)")


P_RE = re.compile(r"<w:p[ >].*?</w:p>", re.S)


def enclosing_ins(pos):
    """attrs of the pending insertion (any author) that encloses `pos`, or None."""
    if not _in_tracked(d.x, pos):
        return None
    pre = d.x[max(0, pos - 3000):pos]
    k = max((m.start() for m in re.finditer(r"<w:ins (?:[^>/]|/(?!>))*>", pre)), default=-1)
    if k < 0 or pre.rfind("</w:ins>") > k:
        return None
    m = re.match(r'<w:ins w:id="\d+" ([^>]*)>', pre[k:])     # every attribute after the id (TW2: + w16du:dateUtc)
    assert m, pre[k:k + 120]
    return m.group(1)


def span_edit(e):
    """Tracked replacement of e['old'] when it straddles several runs of ONE paragraph (formatting, comment ranges,
    or one of Tony's pending insertions). Each overlapped run is split; its overlapped part is deleted (inside Tony's
    insertion the deletion nests in it, which Word reads as deleting inserted text); the new text is inserted once,
    after the last deleted part (splitting Tony's insertion around it if needed)."""
    if e["category"] == "table":
        cells = cell_bounds(e)
        if len(cells) != 1:
            return f"SKIP ({len(cells)} cells match)"
        ps, pe = cells[0]
    else:
        paras = [m for m in P_RE.finditer(d.x) if e["anchor"] in para_text(m.start(), m.end())]
        if len(paras) != 1:
            return f"SKIP (anchor in {len(paras)} paragraphs)"
        ps, pe = paras[0].start(), paras[0].end()
    runs, txt, offs = [], "", []
    for m in RUN_RE.finditer(d.x, ps, pe):
        if m.end() > pe:
            break
        runs.append(m); offs.append(len(txt)); txt += unescape(m.group(2))
    if txt.count(e["old"]) != 1:
        return f"SKIP (old occurs {txt.count(e['old'])}x in the paragraph's run text)"
    a0 = txt.index(e["old"]); a1 = a0 + len(e["old"])
    hit = [k for k, m in enumerate(runs) if offs[k] < a1 and offs[k] + len(unescape(m.group(2))) > a0]
    first_rpr = runs[hit[0]].group(1)
    for k in reversed(hit):
        m = runs[k]; rpr = m.group(1); t = unescape(m.group(2))
        i, j = max(0, a0 - offs[k]), min(len(t), a1 - offs[k])
        before, mid, after = escape(t[:i]), escape(t[i:j]), escape(t[j:])
        attrs = enclosing_ins(m.start())
        out = d._run(rpr, before) + d._del(rpr, mid)
        if k == hit[-1]:
            ins = d._ins(first_rpr, escape(e["new"]))
            out += (f"</w:ins>{ins}<w:ins w:id=\"{d._id()}\" {attrs}>" if attrs else ins)
        out += d._run(rpr, after)
        d.x = d.x[:m.start()] + out + d.x[m.end():]
    d.log.append((e["id"], f"{e['old']!r} -> {e['new']!r} [span over {len(hit)} runs]", e.get("source", "")[:60]))
    return f"ok (span over {len(hit)} runs" + (", touches Tony's insertion)" if any(enclosing_ins(runs[k].start()) for k in hit) else ")")


