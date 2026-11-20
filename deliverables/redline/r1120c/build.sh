#!/bin/bash
# Round r1120c build (2026-11-20): Marcus's 10:02 save of the 11-20b clean copy, with Claude's tracked wording edits and
# the notation pass (author "Claude (notation)"); his own three tracked marks are kept. Never writes the base.
#   ./build.sh <fresh workdir> <out.docx>
# The guard is the base's md5.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="$HOME/climate-env/bin/python"
SK="/Users/MarcusMarcus/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/bde964e6-4558-410f-b23a-3b83edafdcf0/a8b27aae-cf9d-41c6-8c2f-bc82579b92b8/skills/docx"
BASE="${BASE_DOCX:-$HERE/base_marcus_2026-11-20_1002.docx}"   # frozen copy of Marcus's 10:02 save
CONFIRMED_MD5="${BASE_MD5:-a93fb35c92fc52f73b2f022ed5c20765}"
WD="$1"; OUT="$2"
[ "$(md5 -q "$BASE")" = "$CONFIRMED_MD5" ] || { echo "base md5 is not $CONFIRMED_MD5 (a newer save?): look at it, then pass BASE_MD5"; exit 1; }
[ ! -e "$OUT" ] || { echo "refusing to overwrite $OUT"; exit 1; }
[ ! -e "$WD" ] || { echo "workdir $WD exists; pass a fresh one"; exit 1; }
echo "base md5 $CONFIRMED_MD5"
mkdir -p "$WD" && cp "$BASE" "$WD.base.docx"
"$PY" -c "import sys,zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" "$WD.base.docx" "$WD"
"$PY" "$SK/scripts/merge_runs.py" "$WD/"
"$PY" "$HERE/normalise.py" "$WD"
(cd "$WD" && zip -q -X -r -D "$WD.norm.docx" .)   # the base after non-content normalisation: the gates' reference
"$PY" "$HERE/edits_r1120c.py" "$WD"
(cd "$WD" && zip -q -X -r -D "$OUT" .)   # -D: no directory entries (they break cloud co-editing)
"$PY" "$SK/scripts/office/validate.py" "$OUT" --original "$WD.norm.docx"
