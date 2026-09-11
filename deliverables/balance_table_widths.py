#!/usr/bin/env python3
"""Rewrite each pipe table's separator row so column widths are proportional to the text each
column carries. Reads a markdown file, writes to stdout. Run in the docx build chain.

WHY THIS IS A BUILD STEP AND NOT A HAND EDIT (2026-09-11): pandoc's markdown reader takes
relative column widths from the dash counts of the separator row, but the docx->gfm sync that
regenerates FILLED.md writes every separator back as equal dashes, so a hand-set width is lost
on the very next sync. Deriving it from content at build time makes it structural. It also
balances line counts across columns by construction, which is what Marcus asked for.
"""
import re
import sys

TOTAL_DASHES = 60      # pandoc only needs the RATIO; this keeps the row readable
MIN_DASHES = 4


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
        load = [sum(len(c[k]) for c in cells if len(c) > k) for k in range(ncol)]
        tot = sum(load) or 1
        dashes = [max(MIN_DASHES, round(TOTAL_DASHES * l / tot)) for l in load]
        out.append(lines[i])
        out.append("|" + "|".join("-" * d for d in dashes) + "|")
        out.extend(lines[i + 2:j])
        i = j
    return "\n".join(out)


if __name__ == "__main__":
    sys.stdout.write(balance(open(sys.argv[1]).read()))
