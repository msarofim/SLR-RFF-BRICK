"""Round 10-15: the edit pass on Tony's TW2 file (Marcus 2026-10-15: "Apply this all in the edit pass on Tony's TW2 file
... do all the updates that we have available, so that the next version of the paper reflects the latest versions of
everything").

The edits are the inventory `tw2_edit_inventory.json` (built read-only against TW2's accepted text, every `old` span
verified to occur once in its paragraph or table cell; human-readable `tw2_edit_inventory.md`), plus EXTRA below. They
carry: the BRICK 2.0 arm on the Zenodo v2.0.0 joint posterior (SLR CHANGELOG 2026-10-15d), the v1.1 / 10-07 / v1.2
numbers, the queued wording fixes of handoff_2026-10-01c §1c items 1, 2, 3, 5, 6, the version label v1.3 (tag v1.3.0),
the paired tap statistics, the record-conditioning sentence, Table 2 on the re-run glacier diagnostic, and the captions.
Every change is a tracked change by Claude dated this round; Tony's tracked changes and all comments are left alone.

    python edits_r1015.py <unpacked workdir>      (run by build.sh)

An entry whose `old` span cannot be placed in exactly one run (e.g. it straddles one of Tony's pending insertions) is
REPORTED and skipped, never guessed; MANUAL below handles those by hand.
"""
import json, os, re, sys
from xml.sax.saxutils import escape, unescape
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edlib
from trackedit import RUN_RE, _in_tracked, _para_bounds

HERE = os.path.dirname(os.path.abspath(__file__))
INV = json.load(open(os.path.join(HERE, "tw2_edit_inventory.json")))
d = edlib.open_doc(sys.argv[1] + "/word/document.xml")

## ---- additions to the inventory --------------------------------------------------------------------------------
EXTRA = [
    # Table 2, BRICK 2.0 glacier inventory at 2000: julia/diag_brick_gsic_melt_1850_2000.jl re-run on the Zenodo file
    # (10-15; SLR CHANGELOG 2026-10-15f): remaining_at_2000 p50 37.435, p05 27.9, p95 47.8 (was 37.67 / 28.0 /
    # 47.7); the melt 1850-2000 stays 4.0 cm (4.045), so note 7 is unchanged.
    dict(id="X01", section="Table 2", category="table", old="37.7 (28–48)", new="37.4 (28–48)",
         anchor="37.7 (28–48)", source="outputs/diag_brick_gsic_melt_1850_2000.csv remaining_at_2000_cm p50 37.435"),
    # Copyedits from the inventory's "outside the brief" list (Marcus 10-15: "do all the updates that we have available").
    # The last three sit in Tony's pending insertions; they are split around the change as for any other edit.
    dict(id="C01", section="4.1", category="wording", old="observations are largest", new="observations is largest",
         anchor="observations are largest", source="grammar: 'The improvement ... are largest'"),
    dict(id="C02", section="3.1", category="wording", old="as an type of", new="as a type of", anchor="as an type of",
         source="grammar"),
    dict(id="C03", section="3.2", category="wording", old="mean times series", new="mean time series",
         anchor="mean times series", source="typo"),
    dict(id="C04", section="2.2.3", category="wording", old="impacts on projections is", new="impacts on projections are",
         anchor="impacts on projections is", source="grammar"),
    dict(id="C05", section="4.2", category="wording", old="climate uncer.", new="climate uncertainty.",
         anchor="ensemble to represent climate uncer.", source="truncated word in Tony's insertion"),
    dict(id="C06", section="5", category="wording", old="10,000-draw ensembles", new="10,000-draw ensemble",
         anchor="10,000-draw ensembles", source="grammar in Tony's insertion"),
    dict(id="C07", section="4.2", category="wording", old="relative to 1995-2014 mean", new="relative to the 1995–2014 mean",
         anchor="relative to 1995-2014 mean", source="article + en dash in Tony's insertion"),
]
## Comments for Marcus (a flagged reading, not a number): anchored on untracked text next to the edited span.
COMMENTS = [
    ("its updated calibration also substantially improves observational matches",
     "Claude 10-15: on the Zenodo BRICK 2.0 posterior, BRICK 2.0 minus Ladrillo Antarctic sea level at 2300 is 18 cm "
     "at most (High-to-Low) and 6 cm for SSP2-4.5, and Ladrillo's median is HIGHER than BRICK 2.0's in 7 of the 10 "
     "scenarios (by up to 47 cm, SSP5-8.5). So 'reductions of up to 18 cm' is true only for 3 scenarios. I changed the "
     "number; the reading is yours. Receipt: outputs/brick20_swap_paper_number_diff_20261015.csv."),
    ("whereas Antarctic ice and thermal expansion",
     "Claude 10-15: 'equal' no longer holds: the Ladrillo/BRICK 2.0 responsiveness ratio (High minus Very Low, 2300) "
     "is 1.14 for Antarctica and 1.07 for thermal expansion. I wrote 'similar (about 1.1x)'; the wording is yours."),
]


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


## ---- figures: all six TW2 images predate the current renders (tw2_edit_inventory.md, "Figures to replace") ---------
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
FIGS = [("rId10", "hindcast_components_L27.png", "FIG 1: BRICK 2.0 hindcast on the Zenodo posterior"),
        ("rId11", "model_comparison_components_vv_L27_2100.png", "FIG 2: 10-07 / 10-08k vv forcing, conditioning, BRICK 2.0 swap"),
        ("rId12", "model_comparison_components_vv_L27_2300.png", "FIG 3: same"),
        ("rId13", "future_components_vv_L27_joint.png", "FIG 4: same"),
        ("rId14", "vv_gsic_ladrillo_L27_2300.png", "FIG 5: 10-07 / 10-08k vv forcing (glaciers; no BRICK)"),
        ("rId15", "vv_responsiveness_L27.png", "FIG 6: all of the above")]


def swap_figures(W):
    import shutil
    from PIL import Image
    rels_p = W + "/word/_rels/document.xml.rels"
    rels = open(rels_p, encoding="utf8").read()
    nid = max(int(i) for i in re.findall(r'Id="rId(\d+)"', rels)) + 1
    for rid, png, why in FIGS:
        src = os.path.join(REPO, "figures", "paper", png)
        tgt = f"media/fig1015_{png}"
        shutil.copyfile(src, os.path.join(W, "word", tgt))
        new = f"rId{nid}"; nid += 1
        rels = rels.replace("</Relationships>", f'<Relationship Id="{new}" Type="http://schemas.openxmlformats.org/'
                            f'officeDocument/2006/relationships/image" Target="{tgt}"/></Relationships>')
        cx = int(re.findall(r'<wp:extent cx="(\d+)"', d.x[:d.x.index(f'r:embed="{rid}"')])[-1])   # this image's width
        w_px, h_px = Image.open(src).size
        d.swap_image(rid, new, round(cx * h_px / w_px), "figures/paper/" + png, why)
    open(rels_p, "w", encoding="utf8").write(rels)
    ct = W + "/[Content_Types].xml"; c = open(ct, encoding="utf8").read()
    assert 'Extension="png"' in c, "png content type missing"
    return len(FIGS)


report = {}
for e in INV + EXTRA:
    r = apply(e)
    if r.startswith("SKIP (0 runs") and e.get("anchor"):
        r = span_edit(e)
    report[e["id"]] = r
nfig = swap_figures(sys.argv[1])
d.save()
print(f"figures swapped: {nfig}")
skipped = {k: v for k, v in report.items() if not v.startswith("ok")}
print(f"applied {sum(v.startswith('ok') for v in report.values())} of {len(report)}; "
      f"{sum('Tony' in v for v in report.values())} touch Tony's insertions; "
      f"{sum('span' in v for v in report.values())} span several runs")
for k, v in skipped.items():
    print(f"  {k}: {v}")

import comments_lib as cl                                 # works on the saved unpacked file (sys.argv[1])
for phrase, text in COMMENTS:
    cl.comment(phrase, text)
print(f"edits_r1015: {len(report) - len(skipped)} applied, {len(skipped)} skipped, {len(COMMENTS)} comments")
