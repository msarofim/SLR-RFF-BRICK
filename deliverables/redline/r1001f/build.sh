#!/bin/bash
# Round 10-01f build, applied INCREMENTALLY to MARCUS'S OWN SAVE of 10-01e (he accepted changes in it), never
# to an older build output (memory rebuild_from_base_erases_review).
#   ./build.sh <fresh workdir> <out.docx>
# Refuses while Word has the base open (its ~$ lock file exists): edits made after this build would be lost.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
PY="$HOME/climate-env/bin/python"
SK="/Users/MarcusMarcus/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/bde964e6-4558-410f-b23a-3b83edafdcf0/a8b27aae-cf9d-41c6-8c2f-bc82579b92b8/skills/docx"
BASE="$REPO/deliverables/GMD.Ladrillo.v1_review-2026-10-01e_L27.docx"
LOCK="$REPO/deliverables/~\$D.Ladrillo.v1_review-2026-10-01e_L27.docx"
WD="$1"; OUT="$2"
[ ! -e "$LOCK" ] || { echo "Word still has 10-01e open (lock file); save and close it first"; exit 1; }
NEWER=$(find "$REPO/deliverables" -maxdepth 1 -name 'GMD.Ladrillo*.docx' -newer "$BASE" ! -path "$OUT")
[ -z "$NEWER" ] || { echo "newer manuscript exists: $NEWER"; exit 1; }
[ ! -e "$OUT" ] || { echo "refusing to overwrite $OUT"; exit 1; }
[ ! -e "$WD" ] || { echo "workdir $WD exists; pass a fresh one"; exit 1; }
echo "base md5 $(md5 -q "$BASE") (record it in the CHANGELOG)"
mkdir -p "$WD" && unzip -q "$BASE" -d "$WD" && find "$WD" -type l -delete
"$PY" "$SK/scripts/merge_runs.py" "$WD/"
"$PY" "$HERE/normalise.py" "$WD"
"$PY" "$HERE/edits_o.py" "$WD" | tail -1
(cd "$WD" && zip -q -X -r "$OUT" .)
"$PY" "$SK/scripts/office/validate.py" "$OUT" --original "$BASE" --author Claude
