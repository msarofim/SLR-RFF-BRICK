#!/bin/bash
## Round 7 runner: base = the r6 review docx AS ON DISK (Marcus's copy if he has saved into it).
set -euo pipefail
cd "$(dirname "$0")"
SK="/Users/MarcusMarcus/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/bde964e6-4558-410f-b23a-3b83edafdcf0/a8b27aae-cf9d-41c6-8c2f-bc82579b92b8/skills/docx"
BASE=../GMD.Ladrillo.v1_review-2026-09-20b_L27.docx
OUT=../GMD.Ladrillo.v1_review-2026-09-21_L27.docx
source ~/climate-env/bin/activate
rm -rf unpacked && mkdir unpacked && unzip -q "$BASE" -d unpacked
python "$SK/scripts/merge_runs.py" unpacked/
python3 apply_edits_r7_precision.py
rm -f "$OUT"; (cd unpacked && zip -Xqr "../$OUT" .)
python "$SK/scripts/office/validate.py" "$OUT" --original "$BASE" --author Claude
echo "wrote $OUT"
