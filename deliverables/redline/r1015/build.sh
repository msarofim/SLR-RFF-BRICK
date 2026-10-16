#!/bin/bash
# Round 10-15 build: the edit pass on TONY'S RETURNED TW2 file (Marcus 2026-10-15: "Apply this all in the edit pass on
# Tony's TW2 file"), never an older build (memory rebuild_from_base_erases_review). Tony's 119 tracked edits and all
# comments are left as they are; every change here is a new tracked change by Claude, dated this round.
#   ./build.sh <fresh workdir> <out.docx>
# Refuses while Word has the base open (its ~$ lock file exists).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
PY="$HOME/climate-env/bin/python"
SK="/Users/MarcusMarcus/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/bde964e6-4558-410f-b23a-3b83edafdcf0/a8b27aae-cf9d-41c6-8c2f-bc82579b92b8/skills/docx"
BASE="$REPO/deliverables/GMD.Ladrillo.v1_forTonyreview_TW2.docx"
LOCK="$REPO/deliverables/~\$D.Ladrillo.v1_forTonyreview_TW2.docx"
WD="$1"; OUT="$2"
[ ! -e "$LOCK" ] || { echo "Word still has TW2 open (lock file); save and close it first"; exit 1; }
[ ! -e "$OUT" ] || { echo "refusing to overwrite $OUT"; exit 1; }
[ ! -e "$WD" ] || { echo "workdir $WD exists; pass a fresh one"; exit 1; }
echo "base md5 $(md5 -q "$BASE") (record it in the CHANGELOG)"
mkdir -p "$WD" && unzip -q "$BASE" -d "$WD" && find "$WD" -type l -delete
"$PY" "$SK/scripts/merge_runs.py" "$WD/"
"$PY" "$HERE/normalise.py" "$WD"
"$PY" "$HERE/edits_r1015.py" "$WD" | tail -3
(cd "$WD" && zip -q -X -r "$OUT" .)
"$PY" "$SK/scripts/office/validate.py" "$OUT" --original "$BASE" --author Claude
