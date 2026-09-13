#!/usr/bin/env python3
"""Rewrite each pipe table's separator row so column widths are proportional to the text each
column carries, with every column at least wide enough for its longest unbreakable word.
Reads a markdown file, writes to stdout. Run in the docx build chain.

WHY THIS IS A BUILD STEP AND NOT A HAND EDIT (2026-09-11): pandoc's markdown reader takes
relative column widths from the dash counts of the separator row, but the docx->gfm sync that
regenerates FILLED.md writes every separator back as equal dashes, so a hand-set width is lost
on the very next sync. Deriving it from content at build time makes it structural. It also
balances line counts across columns by construction, which is what Marcus asked for.

WORD FLOORS (2026-09-13, Marcus): load-proportional widths alone gave the "attribute" column a
third of the nine-column Tables 1-2 while "SURFER", "(1850)", "partial", "parametric" and
"statistical" broke mid-word in the emulator columns. Each column now gets a FLOOR = the measured
width of its longest token (Word breaks at spaces and after hyphens) plus the cell margins, at the
font size the table is rendered in; the width left over is shared by text load, with the attribute
column's load down-weighted. Widths are measured with the document's body font (Aptos, the Word
theme's minor font) when its file is present, else estimated at 0.5 em per character.
"""
import math
import os
import re
import sys

TOTAL_DASHES = 100     # pandoc only needs the RATIO; 100 keeps 1 dash ~ 4.7 pt
TABLE_WIDTH_PT = 468.0 # pandoc writes tblW 100 %: Letter, 1 in margins (no pgMar in the sectPr)
CELL_MARGIN_PT = 2 * 5.4   # tblCellMar left+right, 108 twips each (pandoc's Table style)
FLOOR_SLACK_PT = 1.5
BODY_FONT_PT = 12.0        # docDefaults sz 24
WIDE_TABLE_NCOLS = 9
WIDE_TABLE_FONT_PT = 8.0   # mirrors shrink_attribute_tables.py PT (the post-pass sets it)
ATTRIBUTE_COL_WEIGHT = 0.5 # the attribute column's text load counts at this weight
FONT_FILE = "/Applications/Microsoft Word.app/Contents/Resources/DFonts/Aptos.ttf"
EM_FALLBACK = 0.5

_font_cache = {}


def text_width_pt(s, pt):
    """Width of s in points at size pt, measured on the body font when available."""
    if os.path.exists(FONT_FILE):
        try:
            from PIL import ImageFont
            if pt not in _font_cache:
                _font_cache[pt] = ImageFont.truetype(FONT_FILE, size=int(round(pt * 10)))
            return _font_cache[pt].getlength(s) / 10.0
        except Exception:
            pass
    return len(s) * EM_FALLBACK * pt


def tokens(cell):
    """Unbreakable pieces: Word wraps at spaces and after hyphens/en-dashes."""
    cell = re.sub(r"[*`]", "", cell)
    return [t for t in re.split(r"\s+|(?<=[-–])", cell) if t]


def widths_for(cells, ncol):
    wide = ncol >= WIDE_TABLE_NCOLS
    pt = WIDE_TABLE_FONT_PT if wide else BODY_FONT_PT
    ## Floors only for the wide tables: the 3- and 6-column tables carry DOIs and granule ids whose
    ## unbreakable length would otherwise swallow the prose column, and Marcus accepted their
    ## load-proportional layout on 09-11.
    floor = [max([text_width_pt(t, pt) for c in cells if len(c) > k for t in tokens(c[k])] or [0])
             + CELL_MARGIN_PT + FLOOR_SLACK_PT if wide else 0.0 for k in range(ncol)]
    load = [sum(text_width_pt(c[k], pt) for c in cells if len(c) > k) for k in range(ncol)]
    if wide:
        load[0] *= ATTRIBUTE_COL_WEIGHT
    spare = TABLE_WIDTH_PT - sum(floor)
    if spare <= 0:   # floors alone exceed the table: scale them, nothing else fits anyway
        return [f * TABLE_WIDTH_PT / sum(floor) for f in floor]
    tot = sum(load) or 1.0
    return [f + spare * l / tot for f, l in zip(floor, load)]


def to_dashes(widths):
    d = [max(1, int(math.floor(TOTAL_DASHES * w / TABLE_WIDTH_PT))) for w in widths]
    # hand the rounding remainder to the columns that lost the most to the floor
    rem = TOTAL_DASHES - sum(d)
    order = sorted(range(len(d)), key=lambda k: -(TOTAL_DASHES * widths[k] / TABLE_WIDTH_PT - d[k]))
    for k in order[:max(0, rem)]:
        d[k] += 1
    return d


def balance(md):
    out, i, lines = [], 0, md.split("\n")
    while i < len(lines):
        ln = lines[i]
        is_header = ln.startswith("|") and i + 1 < len(lines) and re.fullmatch(r"\|[-:| ]+\|", lines[i + 1].strip())
        if not is_header:
            out.append(ln); i += 1; continue
        j = i + 2
        while j < len(lines) and lines[j].startswith("|"):
            j += 1
        rows = [lines[i]] + lines[i + 2:j]
        cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
        ncol = len(cells[0])
        dashes = to_dashes(widths_for(cells, ncol))
        out.append(lines[i])
        out.append("|" + "|".join("-" * d for d in dashes) + "|")
        out.extend(lines[i + 2:j])
        i = j
    return "\n".join(out)


if __name__ == "__main__":
    sys.stdout.write(balance(open(sys.argv[1]).read()))
