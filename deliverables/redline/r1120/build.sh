#!/bin/bash
# Round r1120 build (2026-11-20): the r1119 clean copy (all r1119 changes accepted) with Claude's tracked wording edits
# and the style pass (author "Claude (style)"). Never writes the base.
#   ./build.sh <fresh workdir> <out.docx>
# The guard is the base's md5.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
PY="$HOME/climate-env/bin/python"
SK="/Users/MarcusMarcus/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/bde964e6-4558-410f-b23a-3b83edafdcf0/a8b27aae-cf9d-41c6-8c2f-bc82579b92b8/skills/docx"
BASE="${BASE_DOCX:-$REPO/deliverables/GMD.Ladrillo.v1.2026-11-19.clean.docx}"   # BASE_DOCX: a frozen copy
CONFIRMED_MD5="${BASE_MD5:-213fc5e97d24b630a6e0af89ea70d4dc}"   # r1119 clean copy, 11-19 18:58; Marcus 11-20: current
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
"$PY" "$HERE/edits_r1120.py" "$WD"
(cd "$WD" && zip -q -X -r -D "$OUT" .)   # -D: no directory entries (they break cloud co-editing)
"$PY" "$SK/scripts/office/validate.py" "$OUT" --original "$WD.norm.docx"
