"""Round r1115: Claude's tracked edits on r1114 (2026-11-12). Run by build.sh on a fresh copy. Data: r1115_data.py."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
W = sys.argv[1]
sys.path.insert(0, HERE)
import edlib  # noqa: E402
from r1115_data import AVAIL_ANCHOR, AVAIL_NEW, TYPO_CTX, TYPO_OLD, TYPO_NEW, STALE_COMMENTS  # noqa: E402
from comments_done import mark_done  # noqa: E402

d = edlib.open_doc(W + "/word/document.xml")

if __name__ == "__main__":
    edlib.ins(AVAIL_ANCHOR, AVAIL_ANCHOR, AVAIL_NEW, "Code and data availability: the target builders and sources")
    edlib.edit(TYPO_CTX, TYPO_OLD, TYPO_NEW, "typo: space after '('")
    d.save()
    done = [mark_done(W, f) for f in STALE_COMMENTS]
    open(os.path.join(W, "..", os.path.basename(W) + "_log.txt"), "w", encoding="utf8").write(
        "\n".join(f"{a} | {b} | {c}" for a, b, c in d.log) + f"\ncomments marked resolved: {done}\n")
    print(f"edits_r1115: 2 tracked edits; comments {done} marked resolved")
