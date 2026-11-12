"""Mark a comment resolved (w15:done="1") by a text fragment of its body. String edits only."""
import re


def mark_done(W, fragment):
    c = open(W + "/word/comments.xml", encoding="utf8").read()
    ms = [m for m in re.finditer(r'<w:comment w:id="(\d+)"[^>]*>(.*?)</w:comment>', c, re.S)
          if fragment in re.sub(r"<[^>]+>", "", m.group(2))]
    assert len(ms) == 1, (fragment, len(ms))
    pid = re.findall(r'w14:paraId="([0-9A-Fa-f]+)"', ms[0].group(2))[-1]
    p = W + "/word/commentsExtended.xml"
    e = open(p, encoding="utf8").read()
    i = e.index(f'<w15:commentEx w15:paraId="{pid}"')
    j = e.index("/>", i) + 2
    tag = e[i:j]
    new = re.sub(r'w15:done="\d"', 'w15:done="1"', tag) if "w15:done" in tag else tag[:-2] + ' w15:done="1"/>'
    open(p, "w", encoding="utf8").write(e[:i] + new + e[j:])
    return ms[0].group(1)
