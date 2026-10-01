"""edit()/ins() helpers from r1001d/edits_m.py (plain run OR Claude's earlier pending insertion)."""
import os, re, sys
from xml.sax.saxutils import escape
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trackedit import Doc, DATE

d = None   # set by open_doc()
INS_PAT = re.compile(r'<w:ins (w:id="\d+") (w:author="Claude" w:date="[^"]*")>'
                     r'<w:r>((?:<w:rPr>(?:(?!</w:rPr>).)*</w:rPr>)?)<w:t(?: xml:space="preserve")?>([^<]*)</w:t></w:r></w:ins>', re.S)


def _plain_hits(c):
    from trackedit import RUN_RE, _in_tracked
    return [m for m in RUN_RE.finditer(d.x) if c in m.group(2) and not _in_tracked(d.x, m.start())]


def _earlier_ins(c):
    hits = [m for m in INS_PAT.finditer(d.x) if c in m.group(4)]
    for m in hits:
        assert DATE not in m.group(2), "that insertion is this round's own"
    return hits


def edit(context, old, new, why=""):
    """Tracked replacement of `old` by `new` at the first occurrence of `old` inside `context`.
    `context` must occur once: in an untracked run, or else in one of Claude's EARLIER pending insertions
    (which is split around the change rather than nested)."""
    c = escape(context)
    ph, eh = _plain_hits(c), _earlier_ins(c)
    if len(ph) + len(eh) != 1:   # (raw counts would include deleted text, which is not a second target)
        raise SystemExit(f"*** context must occur exactly once (plain {len(ph)}, earlier-ins {len(eh)}): {context[:80]!r}")
    o, n = escape(old), escape(new)
    if ph:
        m = ph[0]; rpr, t = m.group(1), m.group(2)
        i = t.index(c) + c.index(o)
        out = d._run(rpr, t[:i]) + d._del(rpr, o) + d._ins(rpr, n) + d._run(rpr, t[i + len(o):])
    else:
        m = eh[0]; attrs, rpr, t = m.group(2), m.group(3), m.group(4)
        i = t.index(c) + c.index(o)
        half = lambda s: f'<w:ins w:id="{d._id()}" {attrs}><w:r>{rpr}{d._t(s)}</w:r></w:ins>' if s else ""
        nested = (f'<w:ins w:id="{d._id()}" {attrs}>' + d._del(rpr, o) + '</w:ins>') if o else ""
        out = half(t[:i]) + nested + d._ins(rpr, n) + half(t[i + len(o):])
    d.x = d.x[:m.start()] + out + d.x[m.end():]
    d.log.append((context, f"{old!r} -> {new!r}", why))


def ins(context, prefix, new, why=""):
    """Tracked insertion of `new` right after `prefix` (a leading part of `context`)."""
    assert context.startswith(prefix)
    c = escape(context)
    ph, eh = _plain_hits(c), _earlier_ins(c)
    if len(ph) + len(eh) != 1:
        raise SystemExit(f"*** context must occur exactly once (plain {len(ph)}, earlier-ins {len(eh)}): {context[:80]!r}")
    n = escape(new)
    if ph:
        m = ph[0]; rpr, t = m.group(1), m.group(2)
        j = t.index(c) + len(escape(prefix))
        out = d._run(rpr, t[:j]) + d._ins(rpr, n) + d._run(rpr, t[j:])
    else:
        m = eh[0]; attrs, rpr, t = m.group(2), m.group(3), m.group(4)
        j = t.index(c) + len(escape(prefix))
        half = lambda s: f'<w:ins w:id="{d._id()}" {attrs}><w:r>{rpr}{d._t(s)}</w:r></w:ins>' if s else ""
        out = half(t[:j]) + d._ins(rpr, n) + half(t[j:])
    d.x = d.x[:m.start()] + out + d.x[m.end():]
    d.log.append((context, f"+ {new!r}", why))



def open_doc(path):
    global d
    d = Doc(path)
    return d
