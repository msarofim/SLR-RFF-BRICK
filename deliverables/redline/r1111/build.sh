#!/bin/bash
# Round 11-11 build: Claude's next pass (notes/ladrillo_guidance_2026-11-11.md, "Claude's next pass", plus the additions
# in handoffs 11-11b/c/d) on Marcus's 15:07 save of the TW2 review file. Every change is a new tracked change by Claude
# dated this round; Tony's and Marcus's tracked changes and all comments are left as they are. Never writes the base.
#   ./build.sh <fresh workdir> <out.docx>
# Word's lock file was still present when Marcus confirmed the save ("the 15:07 save is done", 2026-11-11), so the guard
# is the base's md5: the build runs only on a save that has been looked at and refuses any other (a newer save needs a
# new look: diff its extract against the last one, then pass its md5 as BASE_MD5). He saved again at 17:00 (his HAND
# rewrite of the discrepancy paragraph); that save is the default.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
PY="$HOME/climate-env/bin/python"
SK="/Users/MarcusMarcus/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/bde964e6-4558-410f-b23a-3b83edafdcf0/a8b27aae-cf9d-41c6-8c2f-bc82579b92b8/skills/docx"
BASE="${BASE_DOCX:-$REPO/deliverables/GMD.Ladrillo.v1_review-2026-10-15_L27_TW2.docx}"   # BASE_DOCX: a frozen copy, for test builds
CONFIRMED_MD5="${BASE_MD5:-84c9f503636df9f9b515d9fb2c32dd88}"   # 17:00 save (15:07 was 872c3feff24c0c0e4182fdf2506ae1e0)
WD="$1"; OUT="$2"
[ "$(md5 -q "$BASE")" = "$CONFIRMED_MD5" ] || { echo "base md5 is not $CONFIRMED_MD5 (a newer save?): look at it, then pass BASE_MD5"; exit 1; }
[ ! -e "$OUT" ] || { echo "refusing to overwrite $OUT"; exit 1; }
[ ! -e "$WD" ] || { echo "workdir $WD exists; pass a fresh one"; exit 1; }
echo "base md5 $CONFIRMED_MD5"
mkdir -p "$WD" && cp "$BASE" "$WD.base.docx" && unzip -q "$WD.base.docx" -d "$WD" && find "$WD" -type l -delete
"$PY" "$SK/scripts/merge_runs.py" "$WD/"
"$PY" "$HERE/normalise.py" "$WD"
"$PY" "$HERE/edits_r1111.py" "$WD"
(cd "$WD" && zip -q -X -r -D "$OUT" .)   # -D: no directory entries (they break cloud co-editing)
"$PY" "$SK/scripts/office/validate.py" "$OUT" --original "$WD.base.docx" --author Claude
