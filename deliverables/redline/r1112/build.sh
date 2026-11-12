#!/bin/bash
# Round r1112 build: Claude's tracked edits (edits_r1112.py) on Marcus's 07:59 save of r1111b, 2026-11-12. Every change
# is a new tracked change by Claude dated this round; all earlier tracked changes and comments are left as they are.
# Never writes the base.
#   ./build.sh <fresh workdir> <out.docx>
# The guard is the base's md5: the build runs only on the save that was looked at (its extract diffed against the
# delivered r1111b: Figs. 5 and 6 moved into Sect. 4.3, "provided by" in the Acknowledgements, nothing else).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
PY="$HOME/climate-env/bin/python"
SK="/Users/MarcusMarcus/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/bde964e6-4558-410f-b23a-3b83edafdcf0/a8b27aae-cf9d-41c6-8c2f-bc82579b92b8/skills/docx"
BASE="${BASE_DOCX:-$REPO/deliverables/GMD.Ladrillo.v1_review-2026-11-12_L27_r1111b.docx}"   # BASE_DOCX: a frozen copy
CONFIRMED_MD5="${BASE_MD5:-90a85ff2288c19f5e182c844d879aeae}"   # Marcus's 07:59 save of r1111b
WD="$1"; OUT="$2"
[ "$(md5 -q "$BASE")" = "$CONFIRMED_MD5" ] || { echo "base md5 is not $CONFIRMED_MD5 (a newer save?): look at it, then pass BASE_MD5"; exit 1; }
[ ! -e "$OUT" ] || { echo "refusing to overwrite $OUT"; exit 1; }
[ ! -e "$WD" ] || { echo "workdir $WD exists; pass a fresh one"; exit 1; }
echo "base md5 $CONFIRMED_MD5"
mkdir -p "$WD" && cp "$BASE" "$WD.base.docx" && unzip -q "$WD.base.docx" -d "$WD" && find "$WD" -type l -delete
"$PY" "$SK/scripts/merge_runs.py" "$WD/"
"$PY" "$HERE/normalise.py" "$WD"
"$PY" "$HERE/edits_r1112.py" "$WD"
(cd "$WD" && zip -q -X -r -D "$OUT" .)   # -D: no directory entries (they break cloud co-editing)
"$PY" "$SK/scripts/office/validate.py" "$OUT" --original "$WD.base.docx" --author Claude
