"""Accept tracked changes by STRING operations (never ElementTree, which renames namespace prefixes).

accept(x, author=None) accepts every change by `author` (all authors if None) in a document.xml string:
  - <w:ins ...>...</w:ins> unwrapped (also inside m:oMath and m:ctrlPr);
  - <w:del ...>...</w:del> removed;
  - a self-closing inserted paragraph/row mark (<w:ins .../> in an rPr or trPr) dropped;
  - a paragraph whose mark is deleted (<w:del .../> in its pPr's rPr) is removed, which is what accepting does
    when every run in it is deleted too (asserted; a partly kept paragraph would need a merge, not handled);
  - <w:rPrChange>/<w:pPrChange> by `author` dropped (formatting accepted).
"""
import re


def _by(author):
    return r'w:author="%s"' % re.escape(author) if author else r'w:author="[^"]*"'


def accept(x, author=None):
    a = _by(author)
    # 1. paragraphs whose mark is deleted: must be fully deleted, then removed whole
    pm = re.compile(r'<w:p(?: [^>]*)?>(?:(?!</w:p>).)*?<w:pPr>(?:(?!</w:pPr>).)*?<w:rPr>(?:(?!</w:rPr>).)*?'
                    r'<w:del [^>]*' + a + r'[^>]*/>(?:(?!</w:p>).)*</w:p>', re.S)
    for m in list(pm.finditer(x))[::-1]:
        p = m.group(0)
        body = re.sub(r'<w:del [^>]*/>', '', p)
        body = re.sub(r'<w:del (?:[^>/]|/(?!>))*>.*?</w:del>', '', body, flags=re.S)
        kept = "".join(u + v for u, v in re.findall(r'<w:t(?: [^>]*)?>([^<]*)</w:t>|<m:t(?: [^>]*)?>([^<]*)</m:t>', body))
        assert not kept.strip(), ("deleted paragraph mark on a paragraph with kept text", kept[:60])
        x = x[:m.start()] + x[m.end():]
    # 2. deletions (non-self-closing) removed
    x = re.sub(r'<w:del (?:[^>/]|/(?!>))*' + a + r'(?:[^>/]|/(?!>))*>.*?</w:del>', '', x, flags=re.S)
    # 3. insertions unwrapped (repeat for any nesting)
    pat = re.compile(r'<w:ins (?:[^>/]|/(?!>))*' + a + r'(?:[^>/]|/(?!>))*>((?:(?!<w:ins ).)*?)</w:ins>', re.S)   # innermost first
    while True:
        y = pat.sub(lambda m: m.group(1), x)
        if y == x:
            break
        x = y
    # 4. self-closing marks: inserted paragraph/row marks dropped
    x = re.sub(r'<w:ins [^>]*' + a + r'[^>]*/>', '', x)
    # 5. formatting changes accepted
    x = re.sub(r'<w:rPrChange [^>]*' + a + r'[^>]*>.*?</w:rPrChange>|<w:rPrChange [^>]*' + a + r'[^>]*/>', '', x, flags=re.S)
    x = re.sub(r'<w:pPrChange [^>]*' + a + r'[^>]*>.*?</w:pPrChange>', '', x, flags=re.S)
    x = x.replace('<w:rPr></w:rPr>', '')
    return x


def remaining(x, author=None):
    a = _by(author)
    return len(re.findall(r'<w:(?:ins|del|rPrChange|pPrChange) [^>]*' + a, x))
