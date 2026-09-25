#!/bin/bash
## Regenerate the L27-vs-IMBIE-2026 comparison figure for the GMD draft (2026-09-24).
## Marcus's ruling: L27 is the paper's posterior; IMBIE-2026 enters as an OUT-OF-SAMPLE comparison.
##
## ⚠⚠ WHY A RUNNER AND NOT A BARE python CALL. `diag_imbie2026_vs_targets.py:86` reads the SHARED
## file outputs/recalib_targets_ext.csv, and its provenance string HARDCODES the label
## "Frederikse 2020 <= 2018, GRACE-FO after". The live target is currently the IMBIE build, so a bare
## run would silently stamp a FREDERIKSE label onto an IMBIE-built target -- the label-vs-behaviour
## drift ~/.claude/CLAUDE.md warns about, inside the provenance line that is supposed to prevent it.
## L27's figure must be built on L27's OWN training target (the Frederikse build).
##
## ⛔ WHY IT IS REGENERATED AT ALL. Every DATA input predates the existing figure (09-21 12:58) --
## postpred_L27 09-20 18:04, postpred_oldbrick 09-10, the IMBIE raw file 09-21 12:54 -- so the
## NUMBERS are current and this is NOT a stale-number fix. The one input that moved after it is
## `python/ladrillo_figs.py` (09-22 17:10), the shared house-style module. This run buys STYLE
## consistency with the rest of the paper's figure set, and a re-verified provenance stamp.
##
## The IMBIE target is restored BY AN EXIT TRAP so it comes back even if this is killed, and the
## restore is VERIFIED by md5 and screams if it fails (the run_L34.sh pattern).
## ⚠ While this runs, any IMBIE-arm driver would FAIL ITS GATE. That is the safe direction. It is
## seconds, not hours, but do not launch an IMBIE arm against this window.
set -uo pipefail
cd "$(dirname "$0")"
LOG=outputs/log_regen_imbie_fig_L27.txt; : > "$LOG"
say(){ echo "[$(date '+%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

MD5_IMBIE=eb768cd96463a3b84721e2bb9a20f009
MD5_FRED=070f74abe11080da7b77a80b67c54033
PREP="python python/prep_recalib_targets_ext.py"

restore_target(){
  say "RESTORING the shared target to the IMBIE build ..."
  ( source ~/climate-env/bin/activate && $PREP ) >> "$LOG" 2>&1
  local m; m=$(md5 -q outputs/recalib_targets_ext.csv)
  if [[ "$m" == "$MD5_IMBIE" ]]; then say "  restored OK ($m)"
  else say "*** RESTORE FAILED: live target is $m, expected $MD5_IMBIE"
       say "*** DO NOT RUN ANY OTHER ARM until fixed: python python/prep_recalib_targets_ext.py"; fi
}
trap restore_target EXIT INT TERM

[[ "$(md5 -q outputs/recalib_targets_ext.csv)" == "$MD5_IMBIE" ]] \
  || { say "PRE-CONDITION FAILED: live target is not the IMBIE build; refusing to start"; exit 2; }
say "building L27's Frederikse target ..."
( source ~/climate-env/bin/activate && $PREP --ais-frederikse ) >> "$LOG" 2>&1
NOW=$(md5 -q outputs/recalib_targets_ext.csv)
[[ "$NOW" == "$MD5_FRED" ]] || { say "TARGET GATE FAILED: got $NOW, expected $MD5_FRED"; exit 2; }
say "target gate PASSED: $NOW (= L27's own training target, byte-identical)"

source ~/climate-env/bin/activate
say "regenerating the L27 vs IMBIE-2026 comparison ..."
python python/diag_imbie2026_vs_targets.py --tag=L27 >> "$LOG" 2>&1 \
  || { say "*** the diagnostic FAILED; see $LOG"; exit 1; }

## ⚠ THE POST-2018 z VALUES CARRY A KNOWN RULER CLIFF AND MUST NOT BE PRESENTED.
## The Frederikse build's AIS sigma collapses 0.1023 cm (2018) -> exactly 0.0100 (2019) at the
## GRACE-FO splice (IMBIE_SIG_FLOOR, prep_recalib_targets_ext.py:149,267) -- a 10.2x step on
## unchanged data, which is the tell that the step is the RULER. Any |z| above this bar in a window
## ending after 2018 is that artefact, not a discrepancy. Flagged here so it cannot reach a caption.
## ⚠ THE CHECK MUST NOT MISLABEL A REAL MISFIT AS THE CLIFF. First cut flagged GIS rows whose large
## z belongs to BRICK 2.0 in windows ENDING BEFORE 2018 -- genuine comparator misfits, which the cliff
## cannot explain. So the cliff verdict is restricted to its actual precondition (AIS, window ends
## after CLIFF_YEAR) and everything else is reported as "large, inspect", never as an artefact.
say "z screen (CLIFF_YEAR=2019, BAR=5): a cliff claim needs AIS *and* a window ending after the cliff"
python - >> "$LOG" 2>&1 <<'PY'
import pandas as pd
CLIFF_YEAR, BAR, CLIFF_COMP = 2019, 5.0, "AIS"
W = pd.read_csv("outputs/diag_imbie2026_vs_targets_windows_L27.csv")
c = [x for x in W.columns if x.startswith("z_")]
big = W[(W[c].abs() > BAR).any(axis=1)]
cliff = big[(big.component == CLIFF_COMP) & (big.y1 >= CLIFF_YEAR)]
other = big.drop(cliff.index)
print(f"  {CLIFF_COMP} max |z| = {W[W.component==CLIFF_COMP][c].abs().max().max():.2f}")
print(f"  SUPPRESS as the sigma cliff ({CLIFF_COMP}, window ends >= {CLIFF_YEAR}, |z|>{BAR}): "
      + ("NONE" if not len(cliff) else "\n" + cliff[["component","y0","y1"]+c].round(2).to_string(index=False)))
print(f"  LARGE but NOT the cliff -- inspect, do not dismiss: "
      + ("none" if not len(other) else "\n" + other[["component","y0","y1"]+c].round(2).to_string(index=False)))
PY
tail -12 "$LOG" | sed 's/^/    /'
say "wrote figures/diag_imbie2026_vs_targets_L27.png"
say "provenance: $(python3 -c "import csv;print(next(csv.DictReader(open('outputs/diag_imbie2026_vs_targets_L27.csv')))['provenance'][:150])")"
say "DONE"
