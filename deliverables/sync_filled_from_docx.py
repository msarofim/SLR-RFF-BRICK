#!/usr/bin/env python3
"""sync_filled_from_docx.py — regenerate LadrilloUpdateDescription_FILLED.md FROM the .docx.

⚠⚠ THE .docx IS CANONICAL FOR THIS DELIVERABLE (Marcus, 2026-09-03). Marcus edits the .docx
directly in Word. FILLED.md is a GENERATED ARTIFACT, not a hand-maintained source — it exists
only because pandoc needs a markdown intermediate to rebuild the .docx (figures + gfm tables).

THE RULE THIS ENFORCES: before ANY edit to the deliverable's text, run this script first. It
reads the CURRENT .docx and overwrites FILLED.md to match it exactly (verified below by a
round-trip: rebuilding a .docx from the fresh FILLED.md and diffing its text against the
source .docx must show ZERO differences). Only AFTER that sync should FILLED.md be edited —
and it must be rebuilt into the .docx (build_l24_deliverable_doc.sh's docx step, or the
equivalent pandoc call) before the session ends, so the .docx never falls behind FILLED.md.

Skipping this — editing FILLED.md from memory of what it "should" say and rebuilding — is
exactly what caused the 2026-09-03 incident: Marcus's condensed edits were silently reverted
because the rebuild started from a stale FILLED.md instead of his current .docx.

WHAT IT DOES
  1. pandoc .docx -> gfm (pipe tables, so pandoc's forward build --from=gfm+pipe_tables reads
     them back identically)
  2. remaps <img src="media/imageN..."> back to ![alt](../figures/<canonical-name>.png) in
     FIGURE-APPEARANCE ORDER, using the FIGS list below — the inverse of what
     build_l24_deliverable_doc.sh's `sed 's|../figures/|figures/|g'` step does forward.
     ⚠ FIGS must list every figure in the SAME ORDER they appear in the document. If a figure
     is added, removed or reordered, update FIGS to match — the script hard-errors on a count
     mismatch rather than mis-mapping.
  3. unescapes pandoc's literal backslash-escapes (\\', \\-, \\<, \\>, \\|) and collapses
     blank-line runs.

Usage:  python3 deliverables/sync_filled_from_docx.py [--verify]
  --verify   after syncing, round-trip FILLED.md back through the SAME pandoc invocation
             build_l24_deliverable_doc.sh uses and diff its text against the source .docx.
             Requires pandoc. Exits nonzero on any difference.
"""
import re
import subprocess
import sys
import zipfile
import html
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCX = HERE / "LadrilloUpdateDescription_L24.docx"
FILLED = HERE / "LadrilloUpdateDescription_FILLED.md"

# Figure filenames in the ORDER they appear in the document. Keep in sync with the document —
# see the docstring warning above.
FIGS = [
    "hindcast_components_L24.png",
    "model_comparison_components_vv_L24_2100.png",
    "model_comparison_components_vv_L24_2150.png",
    "model_comparison_components_vv_L24_2300.png",
    "future_components_vv_L24_joint.png",
    "vv_gsic_wr_vs_ladrillo_2300.png",
    "model_comparison_components_L24_2100.png",
    "model_comparison_components_L24_2300.png",
    "ladrillo_L24_fig2_ssp_total.png",
]


def docx_text(path):
    """Plain paragraph text of a .docx, for the round-trip diff — independent of pandoc."""
    xml = zipfile.ZipFile(path).read("word/document.xml").decode("utf8")
    t = html.unescape(re.sub(r"<[^>]+>", "", re.sub(r"</w:p>", "\n", xml)))
    return [re.sub(r"\s+", " ", line).strip() for line in t.split("\n") if line.strip()]


def sync():
    if not DOCX.exists():
        sys.exit(f"ERROR: {DOCX} not found")
    gfm = subprocess.run(
        ["pandoc", str(DOCX), "-t", "gfm", "--wrap=none"],
        capture_output=True, text=True, check=True,
    ).stdout

    n = [0]

    def repl(m):
        alt_m = re.search(r'alt="([^"]*)"', m.group(0))
        alt = alt_m.group(1) if alt_m else ""
        if n[0] >= len(FIGS):
            sys.exit(f"ERROR: docx has more figures than FIGS ({len(FIGS)}) lists — "
                      f"update FIGS in {__file__}")
        f = FIGS[n[0]]
        n[0] += 1
        return f"![{alt}](../figures/{f})"

    gfm = re.sub(r'<img src="(?:media/)?image\d+\.\w+"[^>]*/>', repl, gfm)
    if n[0] != len(FIGS):
        sys.exit(f"ERROR: docx has {n[0]} figures, FIGS lists {len(FIGS)} — "
                 f"update FIGS in {__file__} to match the CURRENT document before syncing")

    gfm = (gfm.replace("\\'", "'").replace("\\-", "-")
              .replace("\\<", "<").replace("\\>", ">").replace("\\|", "|"))
    ## ADJACENT CODE SPANS. Word run boundaries inside a formula (e.g. Marcus formatting
    ## "hR = h0 + " and "c" as separate Code-Font runs with nothing between them) make pandoc
    ## emit two BACK-TO-BACK code spans -- "`hR = h0 + `" + "`c\u00b7T_ant`" -- which
    ## concatenate to "`hR = h0 + ``c\u00b7T_ant`". CommonMark parses the doubled backtick as
    ## a DIFFERENT delimiter run, not a span boundary, so the forward pandoc build (gfm ->
    ## docx) mis-renders it -- caught by --verify 2026-09-03. Merge any run of adjacent
    ## same-line spans separated by nothing into one span, repeatedly (3+ runs chain).
    prev = None
    while prev != gfm:
        prev = gfm
        gfm = re.sub(r"`([^`\n]*)``([^`\n]*)`", r"`\1\2`", gfm)
    gfm = re.sub(r"\n{3,}", "\n\n", gfm).strip() + "\n"
    FILLED.write_text(gfm)
    print(f"synced {FILLED.name} <- {DOCX.name}: {len(gfm.split())} words, {n[0]} figures")
    return gfm


def verify():
    build_md = HERE / f"/tmp/sync_verify_{DOCX.stem}.md"
    text = FILLED.read_text().replace("../figures/", "figures/")
    build_md.write_text(text)
    out_docx = Path(f"/tmp/sync_verify_{DOCX.stem}.docx")
    subprocess.run(
        ["pandoc", str(build_md), "-o", str(out_docx),
         "--resource-path=" + str(HERE), "--from=gfm+pipe_tables", "--to=docx"],
        check=True,
    )
    src = docx_text(DOCX)
    rt = docx_text(out_docx)
    diff = [l for l in src if l not in rt] + [l for l in rt if l not in src]
    if diff:
        print(f"*** VERIFY FAILED: {len(diff)} differing lines (order-insensitive check)")
        for l in diff[:10]:
            print("   ", l[:150])
        sys.exit(1)
    print(f"[VERIFY] round-trip matches the source .docx exactly "
          f"({len(src)} paragraphs, {len(rt)} after rebuild)")


if __name__ == "__main__":
    sync()
    if "--verify" in sys.argv[1:]:
        verify()
