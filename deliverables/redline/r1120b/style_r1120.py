"""Round r1120 style pass, author STYLE_AUTHOR, so Word can show, hide or accept it apart from the wording edits.
Copernicus manuscript preparation guidelines (read 2026-11-20): "Footnotes to tables should be marked by lowercase
letters"; "Spaces must be included between number and unit" (example "1 %").

1. Table footnote markers. Tables 1-3 are numbered on across the three tables (1-6, 7-12, 13-16) with Unicode
   superscript digits. Each table restarts at "a": tracked deletion of the digit marker, tracked insertion of the
   letter as a real superscript (w:vertAlign), in the table cells and in each table's note paragraph(s). The two
   in-text pointers "Table 3, note 14" become "Table 3, note b".
2. "%": a tracked space between a digit and "%" everywhere before the References (40 places in the base).
Each step asserts the exact marker sequence or count it expects, so a changed base stops the build.
"""
import re
from xml.sax.saxutils import escape
import trackedit
from trackedit import RUN_RE, _in_tracked, _para_bounds

STYLE_AUTHOR, STYLE_DATE = "Claude (style)", "2026-11-20T12:30:00Z"
SUP = "⁰¹²³⁴⁵⁶⁷⁸⁹"
CELL_MARK = re.compile(r"(?<![⁻ᐟ⁰¹²³⁴⁵⁶⁷⁸⁹])([¹²³⁴⁵⁶⁷⁸⁹][⁰¹²³⁴⁵⁶⁷⁸⁹]?)(?![⁰¹²³⁴⁵⁶⁷⁸⁹])")
NOTE_MARK = re.compile(r"(?:^|(?<=\s))([¹²³⁴⁵⁶⁷⁸⁹][⁰¹²³⁴⁵⁶⁷⁸⁹]?)(?=\s)")
# per table: (first note number, cell-marker sequence in document order, first-note anchor, last-note anchor)
TABLES = [
    (1, [1, 1, 2, 3, 2, 3, 2, 2, 4, 5, 6, 5], "¹ Ice sheets", "⁶ A 2100 model"),
    (7, [7, 8, 9, 10, 11, 12], "⁷ Calibrated ini", "¹² AR5 (parametri"),
    (13, [13, 14, 15, 16], "¹³ The 2023 value", "¹⁶ The 16-paramet"),
]
N_PCT = 40
RPR_AFTER_VERTALIGN = ("rtl", "cs", "em", "lang", "eastAsianLayout", "specVanish", "oMath")


def supnum(s):
    return int("".join(str(SUP.index(c)) for c in s))


def sup_rpr(rpr):
    """The run's properties with w:vertAlign superscript, placed where CT_RPr's sequence puts it."""
    va = '<w:vertAlign w:val="superscript"/>'
    if not rpr:
        return f"<w:rPr>{va}</w:rPr>"
    rpr = re.sub(r'<w:vertAlign [^>]*/>', '', rpr)
    for tag in RPR_AFTER_VERTALIGN:
        k = rpr.find(f"<w:{tag}")
        if k >= 0 and not rpr.startswith(f"<w:{tag}", 0):
            return rpr[:k] + va + rpr[k:]
    return rpr[: rpr.rindex("</w:rPr>")] + va + "</w:rPr>"


def _replace_markers(d, a, b, pattern, first, kind):
    """Tracked marker -> letter in the plain runs of d.x[a:b]; returns the note numbers seen, in order."""
    jobs, seen = [], []
    for m in RUN_RE.finditer(d.x, a, b):
        if _in_tracked(d.x, m.start()):
            continue
        rpr, t = m.group(1), m.group(2)
        hits = list(pattern.finditer(t))
        if not hits:
            continue
        pieces, k = [], 0
        for h in hits:
            num = supnum(h.group(1))
            letter = "abcdefghijkl"[num - first]
            pieces += [d._run(rpr, t[k:h.start(1)]), d._del(rpr, h.group(1)), d._ins(sup_rpr(rpr), letter)]
            k = h.end(1)
            seen.append(num)
        pieces.append(d._run(rpr, t[k:]))
        jobs.append((m.start(), m.end(), "".join(pieces)))
    for s, e, new in reversed(jobs):
        d.x = d.x[:s] + new + d.x[e:]
    d.log += [(f"[{kind} footnote markers {first}..]", ",".join(map(str, seen)), "Copernicus: table footnotes as letters")]
    return seen


def _tables(x):
    return [(m.start(), m.end()) for m in re.finditer(r"<w:tbl>.*?</w:tbl>", x, re.S)]


def run(d):
    saved = trackedit.AUTHOR, trackedit.DATE
    trackedit.AUTHOR, trackedit.DATE = STYLE_AUTHOR, STYLE_DATE
    try:
        # 1. footnote markers; tables are re-located after each change (positions move)
        for ti, (first, cells, a1, a2) in enumerate(TABLES):
            a, b = _tables(d.x)[ti]
            seen = _replace_markers(d, a, b, CELL_MARK, first, f"Table {ti + 1} cell")
            assert seen == cells, (ti + 1, "cells", seen)
            e1, e2 = escape(a1), escape(a2)
            assert d.x.count(e1) == 1 and d.x.count(e2) == 1, (a1, a2)
            s, _ = _para_bounds(d.x, d.x.index(e1))
            _, e = _para_bounds(d.x, d.x.index(e2))
            seen = _replace_markers(d, s, e, NOTE_MARK, first, f"Table {ti + 1} note")
            assert seen == list(range(first, first + len(set(cells)))), (ti + 1, "notes", seen)
        # in-text pointers to Table 3's note 14 (body text and a Table A3 cell)
        ptr = "Table 3, note 14"
        hits = [m for m in RUN_RE.finditer(d.x) if ptr in m.group(2) and not _in_tracked(d.x, m.start())]
        assert len(hits) == 2 and d.x.count(ptr) == 2, len(hits)
        for m in reversed(hits):
            rpr, t = m.group(1), m.group(2)
            i = t.index(ptr) + len("Table 3, note ")
            new = d._run(rpr, t[:i]) + d._del(rpr, "14") + d._ins(rpr, "b") + d._run(rpr, t[i + 2:])
            d.x = d.x[:m.start()] + new + d.x[m.end():]
        d.log.append((ptr + " (2)", "Table 3, note b", "follows the letters"))
        # 2. "%" spacing, body only
        refs = d.x.index(">References<")
        jobs = []
        for m in RUN_RE.finditer(d.x, 0, refs):
            if _in_tracked(d.x, m.start()):
                continue
            rpr, t = m.group(1), m.group(2)
            cuts = [h.start() + 1 for h in re.finditer(r"\d%", t)]
            if not cuts:
                continue
            pieces, k = [], 0
            for c in cuts:
                pieces += [d._run(rpr, t[k:c]), d._ins(rpr, " ")]
                k = c
            pieces.append(d._run(rpr, t[k:]))
            jobs.append((m.start(), m.end(), "".join(pieces), len(cuts)))
        n = sum(j[3] for j in jobs)
        assert n == N_PCT, n
        for s, e, new, _ in reversed(jobs):
            d.x = d.x[:s] + new + d.x[e:]
        d.log.append(("[digit%]", f"{n} spaces inserted", "Copernicus: space between number and %"))
        return n
    finally:
        trackedit.AUTHOR, trackedit.DATE = saved
