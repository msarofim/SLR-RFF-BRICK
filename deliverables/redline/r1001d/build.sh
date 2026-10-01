#!/bin/bash
# Round 10-01d build: applied INCREMENTALLY to the 10-01c output (md5 e0be5ca7), which Marcus had not
# touched (mtime = build time; core.xml unchanged). Never rebuild from an older base
# (memory rebuild_from_base_erases_review).
#   ./build.sh <workdir> <out.docx>
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
PY="$HOME/climate-env/bin/python"
SK="/Users/MarcusMarcus/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/bde964e6-4558-410f-b23a-3b83edafdcf0/a8b27aae-cf9d-41c6-8c2f-bc82579b92b8/skills/docx"
BASE="$REPO/deliverables/GMD.Ladrillo.v1_review-2026-10-01c_L27.docx"
WD="$1"; OUT="$2"
[ "$(md5 -q "$BASE")" = "e0be5ca728ca840af760d8ca95dbd8e8" ] || { echo "base changed under us"; exit 1; }
# Guards: no newer manuscript beside the base, and never overwrite an existing output.
NEWER=$(find "$REPO/deliverables" -maxdepth 1 -name 'GMD.Ladrillo*.docx' -newer "$BASE" ! -path "$OUT")
[ -z "$NEWER" ] || { echo "newer manuscript exists: $NEWER"; exit 1; }
[ ! -e "$OUT" ] || { echo "refusing to overwrite $OUT"; exit 1; }
[ ! -e "$WD" ] || { echo "workdir $WD exists; pass a fresh one"; exit 1; }
mkdir -p "$WD" && unzip -q "$BASE" -d "$WD" && find "$WD" -type l -delete
"$PY" "$HERE/edits_m.py" "$WD" | tail -1
(cd "$WD" && zip -q -X -r "$OUT" .)
"$PY" "$SK/scripts/office/validate.py" "$OUT" --original "$BASE" --author Claude
