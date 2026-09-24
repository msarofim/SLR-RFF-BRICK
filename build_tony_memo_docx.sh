#!/bin/bash
## BUILD THE L27-vs-L32 TRADE-OFF MEMO (.docx) FOR TONY WONG.
##
## ⚠ .docx IS BUILT WITH PANDOC, NEVER BY HAND. Writing .docx XML directly (e.g. with
## ElementTree) renames namespace prefixes and Word then reports "unreadable content" — and a
## round-trip through the same library CANNOT see it. Verify with an INDEPENDENT reader; this
## script does that with `textutil` and fails if the text does not come back.
##
## ⚠⚠ MARCUS EDITS THE .docx DIRECTLY. If deliverables/L27_vs_L32_proscons_for_TonyWong.docx
## already exists and is NEWER than the .md, he may have edited it — a rebuild would destroy that
## silently. This script REFUSES to overwrite a newer .docx unless --force is passed. Pull his
## prose back into the .md first.
##
##   bash build_tony_memo_docx.sh [--force]
set -uo pipefail
cd "$(dirname "$0")"
SRC=deliverables/L27_vs_L32_proscons_for_TonyWong.md
OUT=deliverables/L27_vs_L32_proscons_for_TonyWong.docx
TMP=$(mktemp -t tonymemo).md
say(){ echo "[$(date '+%H:%M:%S')] $*"; }

[[ -f "$SRC" ]] || { say "missing $SRC; STOP"; exit 1; }
if [[ -f "$OUT" && "$OUT" -nt "$SRC" && "${1:-}" != "--force" ]]; then
  say "REFUSING: $OUT is NEWER than $SRC — Marcus may have edited the .docx."
  say "Sync his edits into the .md first, or pass --force to discard them."
  exit 2
fi

say "balancing table widths"
python3 deliverables/balance_table_widths.py "$SRC" > "$TMP" || { say "balance step failed; STOP"; exit 3; }
say "pandoc -> docx"
pandoc "$TMP" -o "$OUT" --resource-path=. \
  --from=markdown+pipe_tables-smart-implicit_figures --to=docx \
  || { say "pandoc failed; STOP"; exit 4; }

## ⭐ INDEPENDENT-READER GATE. pandoc wrote it; something that is NOT pandoc must be able to read
## it back. A word count near zero means a structurally broken file that still unzips fine.
say "verifying with an independent reader (textutil)"
WORDS=$(textutil -convert txt -stdout "$OUT" 2>/dev/null | wc -w | tr -d ' ')
if [[ "${WORDS:-0}" -lt 500 ]]; then
  say "*** INDEPENDENT READER GOT ${WORDS:-0} WORDS — the .docx is not readable. STOP ***"
  exit 5
fi
## and the content must actually be the memo, not an empty shell with the right size
textutil -convert txt -stdout "$OUT" 2>/dev/null | grep -q "trade-off summary" \
  || { say "*** the .docx does not contain the memo's title; STOP ***"; exit 6; }
rm -f "$TMP"
say "OK — $OUT ($WORDS words, independently read)"
