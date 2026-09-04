#!/usr/bin/env bash
# run_pulse_vv_magiccclim.sh -- Ladrillo L24 on MAGICC's OWN paired pulse climate, 7 markers, CO2.
#
# ⛔ NEVER EDIT THIS SCRIPT, OR THE JULIA IT CALLS, WHILE IT RUNS. bash and Julia both read
#    incrementally; an edit shifts byte offsets under the live process and it resumes mid-token,
#    then reports a line that is perfectly fine on disk (`never_edit_a_running_script`). The
#    driver is called through a FROZEN COPY for exactly that reason.
#
# Marcus's rulings, 2026-09-04e: L24 (not the level arm's L21 -- every pulse cell already in the
# cross-model table is L24, and mixing them is the like-for-like error), CO2 only for the first
# pass, and SPLICED primary with the RAW check MEASURED rather than assumed. The 08-31 level
# ruling was "spliced primary, raw as check"; whether the injection convention still costs
# -42.7 cm through AIS on a PAIRED pulse is unknown -- stage 5 found the splice cancels on a
# pair, the level arm found it decisive. So both are run and the difference is reported.
set -euo pipefail
cd "$(dirname "$0")/.."
DRIVER=julia/_frozen_scope_slr_pulse_vv_magiccclim.jl
NDRAW=2000                       # matches the shipped FaIR-climate arm, so the cells compare
MARKERS=(VL LN L ML M HL H)      # van Vuuren's own order
ts() { date +'[%H:%M:%S]'; }
echo "$(ts) Ladrillo L24 on MAGICC climate | CO2 1 Gt @2030 | ${#MARKERS[@]} markers x 2 conventions"
for FORCING in spliced raw; do
  for M in "${MARKERS[@]}"; do
    echo "$(ts) vv$M / $FORCING ..."
    julia --project=julia_v2 "$DRIVER" "$NDRAW" \
      --marker="$M" --specie=CO2 --pulse-size=1 --climate=magicc \
      --forcing="$FORCING" --tap --tag=L24 \
      > "outputs/log_pulse_magiccclim_vv${M}_${FORCING}.txt" 2>&1
  done
done
echo "$(ts) DONE ${#MARKERS[@]} markers x 2 conventions"
