#!/bin/bash
## BUILD THE L24 MODEL-DESCRIPTION DELIVERABLE — figures, then the .docx.
##
## Run AFTER run_l24_deliverable_arms.sh finishes. It blocks until that script exits, so it
## can be launched at any time.
##
## ⚠ EVERY ARM IS TAPPED (see run_l24_deliverable_arms.sh). The figure drivers PREFER the
## tapped joint arm and silently fall back to untapped, so an untapped set would produce
## figures that look fine and are not comparable to L21/L23.
##
## ⚠ .docx IS BUILT WITH PANDOC, NEVER BY HAND. Writing .docx XML directly renames namespace
## prefixes and Word reports "unreadable content"; the round-trip cannot see it. Node and
## LibreOffice are absent on this machine, so docx-js and the soffice render-check are not
## options here. The verification below reads the ARCHIVE instead: embedded media, <w:tbl>
## count, and a heading round-trip.
set -uo pipefail
cd "$(dirname "$0")"
T=L24
LOG=outputs/log_l24_deliverable_doc.txt
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }
step(){ local nm="$1"; shift; say "START  $nm"
  if "$@" >> "$LOG" 2>&1; then say "OK     $nm"; else say "FAILED $nm (rc=$?)"; fi; }
: > "$LOG"
while pgrep -f "run_l24_deliverable_arms" >/dev/null; do sleep 60; done
say "arms finished; building figures"
source ~/climate-env/bin/activate
for d in plot_future_components plot_model_comparison_components plot_vv_gsic_wr_vs_ladrillo; do
  step "$d" python python/$d.py --tag=$T
done
step "vv model comparison"      python python/vv_model_comparison.py --tag=$T
step "ladrillo model comparison" python python/ladrillo_model_comparison.py --tag=$T
step "memo figures"             python python/plot_ladrillo_memo_figures.py --tag=$T
step "benchmark (refresh)"      python python/bench_ladrillo.py --tag=$T

say "=== figures now present for $T ==="
ls figures/ | grep "$T" | sed 's/^/  /' | tee -a "$LOG"

say "=== rebuilding the .docx ==="
step "docx" bash -c "sed 's|\.\./figures/|figures/|g' deliverables/LadrilloUpdateDescription_FILLED.md > /tmp/doc_build_${T}.md && \
  pandoc /tmp/doc_build_${T}.md -o deliverables/LadrilloUpdateDescription_${T}.docx --resource-path=. --from=gfm+pipe_tables --to=docx"

say "=== VERIFY THE ARCHIVE (no soffice available; do not trust the build silently) ==="
D=deliverables/LadrilloUpdateDescription_${T}.docx
{ echo "  media embedded: $(unzip -l $D | grep -c 'word/media')"
  echo "  w:tbl elements: $(unzip -p $D word/document.xml | grep -o '<w:tbl>' | wc -l | tr -d ' ')"
  echo "  headings:       $(pandoc $D -t markdown 2>/dev/null | grep -c '^#')"
  echo "  size:           $(du -h $D | cut -f1)"; } | tee -a "$LOG"
EXPECTED=$(grep -c "^!\[" deliverables/LadrilloUpdateDescription_FILLED.md)
GOT=$(unzip -l $D | grep -c "word/media")
if [ "$EXPECTED" -ne "$GOT" ]; then
  say "*** FIGURE COUNT MISMATCH: source markdown has $EXPECTED figures, the docx embeds $GOT."
  say "*** This is the check that caught the 2026-09-02 regression, where the projection figures"
  say "*** were added to a TEMPORARY build file and not to the canonical source, so a faithful"
  say "*** rebuild silently shipped 1 figure instead of 6. DO NOT SHIP until they match."
  exit 1
fi
say "DONE. $GOT figures embedded, matching the source."
