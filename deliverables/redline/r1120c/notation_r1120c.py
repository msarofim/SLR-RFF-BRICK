"""Round r1120c notation pass, author NOTATION_AUTHOR (Marcus 11-20: fix the symbol clashes and the text-vs-table names).

1. Glacier block index b -> g, in the one Sect. 2.2.1 paragraph that uses it ("Each block b ...": T_b, A_b, c_b), so it
   no longer collides with the glacier sensitivity b of Eq. (1). Greenland's basin index b (Eqs. 3-11) is unchanged.
2. Table A1: kappa_DAIS -> kappa_P (the text's name for the same parameter, antarctic_kappa), twice; alpha_DAIS is a
   different parameter and is left alone. In the ais_precip_u row, T-bar -> T-bar_A, twice (the text's name).
3. Table A3: T-bar -> T_ref (the text's name for the Greenland discharge reference temperature, 1.963 K);
   "shape S" -> "shape phi" (the text's name); "w_r" -> "Delta T_r" (Eq. 8's name).
Every step asserts the count it expects.
"""
import re
import trackedit
from trackedit import RUN_RE, _in_tracked, _para_bounds

NOTATION_AUTHOR, NOTATION_DATE = "Claude (notation)", "2026-11-20T15:30:00Z"
SUBVA = '<w:vertAlign w:val="subscript"/>'
AFTER_VA = ("rtl", "cs", "em", "lang", "eastAsianLayout", "specVanish", "oMath")


def sub_rpr(rpr):
    if not rpr:
        return f"<w:rPr>{SUBVA}</w:rPr>"
    rpr = re.sub(r"<w:vertAlign [^>]*/>", "", rpr)
    for tag in AFTER_VA:
        k = rpr.find(f"<w:{tag}")
        if k > 0:
            return rpr[:k] + SUBVA + rpr[k:]
    return rpr[: rpr.rindex("</w:rPr>")] + SUBVA + "</w:rPr>"


def is_sub(rpr):
    return bool(rpr) and 'w:val="subscript"' in rpr


def plain_runs(d, a=0, b=None):
    b = len(d.x) if b is None else b
    return [m for m in RUN_RE.finditer(d.x, a, b) if not _in_tracked(d.x, m.start())]


def replace_run(d, m, new):
    d.x = d.x[:m.start()] + new + d.x[m.end():]


def run(d):
    saved = trackedit.AUTHOR, trackedit.DATE
    trackedit.AUTHOR, trackedit.DATE = NOTATION_AUTHOR, NOTATION_DATE
    try:
        # 1. block index, inside the one paragraph
        key = "Each block b is driven by its own regional temperature"
        assert d.x.count(key) == 1
        s, e = _para_bounds(d.x, d.x.index(key))
        jobs = []
        for m in plain_runs(d, s, e):
            rpr, t = m.group(1), m.group(2)
            if is_sub(rpr) and t == "b":
                jobs.append((m, d._del(rpr, "b") + d._ins(rpr, "g")))
            elif key in t:
                i = t.index("Each block b") + len("Each block ")
                jobs.append((m, d._run(rpr, t[:i]) + d._del(rpr, "b") + d._ins(rpr, "g") + d._run(rpr, t[i + 1:])))
        assert len(jobs) == 11, len(jobs)
        for m, new in reversed(jobs):
            replace_run(d, m, new)
        d.log.append(("[glacier block index]", "b -> g (10 subscripts + 'Each block g')", "clash with Eq. (1)'s b"))

        # 2a. kappa_DAIS -> kappa_P: a subscript run "DAIS" right after a run ending in kappa
        runs = plain_runs(d)
        jobs = [m for k, m in enumerate(runs) if is_sub(m.group(1)) and m.group(2) == "DAIS"
                and k > 0 and runs[k - 1].group(2).endswith("κ") and runs[k - 1].end() == m.start()]
        assert len(jobs) == 2, len(jobs)
        for m in reversed(jobs):
            replace_run(d, m, d._del(m.group(1), "DAIS") + d._ins(m.group(1), "P"))
        d.log.append(("[Table A1] κ_DAIS (2)", "κ_P", "the text's name"))

        # 2b. T-bar -> T-bar_A in the ais_precip_u row (one run, two occurrences)
        hits = [m for m in plain_runs(d) if "·T̄ (T̄ = −17.99" in m.group(2)]
        assert len(hits) == 1, len(hits)
        m = hits[0]; rpr, t = m.group(1), m.group(2)
        cuts = [i + 2 for i in (t.index("T̄"), t.index("T̄", t.index("T̄") + 2))]   # T + combining macron = 2 chars
        assert t.count("T̄") == 2
        out, k = "", 0
        for c in cuts:
            out += d._run(rpr, t[k:c]) + d._ins(sub_rpr(rpr), "A")
            k = c
        replace_run(d, m, out + d._run(rpr, t[k:]))
        d.log.append(("[Table A1] T̄ (2)", "T̄_A", "the text's name"))

        # 3a. Table A3: the cell "T̄" -> T_ref
        hits = [m for m in plain_runs(d) if m.group(2) == "T̄"]
        assert len(hits) == 1, len(hits)
        m = hits[0]; rpr = m.group(1)
        replace_run(d, m, d._del(rpr, "T̄") + d._ins(rpr, "T") + d._ins(sub_rpr(rpr), "ref"))
        d.log.append(("[Table A3] T̄", "T_ref", "the text's name"))

        # 3b. "shape S" -> "shape φ"
        hits = [m for m in plain_runs(d) if m.group(2).endswith("amplification shape S")]
        assert len(hits) == 1, len(hits)
        m = hits[0]; rpr, t = m.group(1), m.group(2)
        replace_run(d, m, d._run(rpr, t[:-1]) + d._del(rpr, "S") + d._ins(rpr, "φ"))
        d.log.append(("[Table A3] shape S", "shape φ", "the text's name"))

        # 3c. "τ, n, w" + subscript r -> "τ, n, ΔT" + subscript r
        runs = plain_runs(d)
        hits = [m for k, m in enumerate(runs) if m.group(2).endswith("τ, n, w") and k + 1 < len(runs)
                and is_sub(runs[k + 1].group(1)) and runs[k + 1].group(2) == "r"]
        assert len(hits) == 1, len(hits)
        m = hits[0]; rpr, t = m.group(1), m.group(2)
        replace_run(d, m, d._run(rpr, t[:-1]) + d._del(rpr, "w") + d._ins(rpr, "ΔT"))
        d.log.append(("[Table A3] w_r", "ΔT_r", "Eq. (8)'s name"))
    finally:
        trackedit.AUTHOR, trackedit.DATE = saved
