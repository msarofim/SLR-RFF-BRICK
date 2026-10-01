#!/bin/bash
# Round 10-01b build: base = Marcus's untouched 10-01 file (md5 9062e357, 47 pending Claude 10-01 edits).
#   ./build.sh <workdir> <out.docx>
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
PY="$HOME/climate-env/bin/python"
SK="/Users/MarcusMarcus/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/bde964e6-4558-410f-b23a-3b83edafdcf0/a8b27aae-cf9d-41c6-8c2f-bc82579b92b8/skills/docx"
BASE="$REPO/deliverables/GMD.Ladrillo.v1_review-2026-10-01_L27.docx"
WD="$1"; OUT="$2"
[ "$(md5 -q "$BASE")" = "9062e3571ecd0fc5a4c0efee274aa105" ] || { echo "base changed under us"; exit 1; }
rm -rf "$WD" && mkdir -p "$WD" && unzip -q "$BASE" -d "$WD" && find "$WD" -type l -delete
"$PY" "$SK/scripts/merge_runs.py" "$WD/"
"$PY" "$HERE/normalise.py" "$WD"
"$PY" "$HERE/edits_i.py" "$WD" | tail -1
"$PY" "$HERE/edits_j.py" "$WD" | tail -1
"$PY" "$HERE/edits_k.py" "$WD"
"$PY" "$HERE/comments_j.py" "$WD"
rm -f "$OUT"; (cd "$WD" && zip -q -X -r "$OUT" .)
"$PY" "$SK/scripts/office/validate.py" "$OUT" --original "$BASE" --author Claude
