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
#
# ⚠ SPECIE IS AN ARGUMENT, AND ITS SIZE COMES WITH IT (added 2026-09-05). `./run_... CH4` runs
#   the 0.01 GtCH4 spec. The two move together or not at all -- the size tag is both the MAGICC
#   cube filename this opens and the per-tonne divisor the driver reports (Marcus's 09-04
#   ruling 3). ⚠ The CO2 log names are UNCHANGED for backward compatibility only where they
#   already exist; new runs carry the specie in the name.
set -euo pipefail
cd "$(dirname "$0")/.."
DRIVER=julia/_frozen_scope_slr_pulse_vv_magiccclim.jl
NDRAW=2000                       # matches the shipped FaIR-climate arm, so the cells compare
MARKERS=(VL LN L ML M HL H)      # van Vuuren's own order
SPECIE="${1:-CO2}"
case "$SPECIE" in
  CO2) PULSE_SIZE=1 ;;
  CH4) PULSE_SIZE=0.01 ;;
  *)   echo "specie must be CO2 or CH4; got '$SPECIE'" >&2; exit 2 ;;
esac
ts() { date +'[%H:%M:%S]'; }
echo "$(ts) Ladrillo L24 on MAGICC climate | $SPECIE $PULSE_SIZE Gt @2030 | ${#MARKERS[@]} markers x 2 conventions"
for FORCING in spliced raw; do
  for M in "${MARKERS[@]}"; do
    echo "$(ts) vv$M / $SPECIE / $FORCING ..."
    julia --project=julia_v2 "$DRIVER" "$NDRAW" \
      --marker="$M" --specie="$SPECIE" --pulse-size="$PULSE_SIZE" --climate=magicc \
      --forcing="$FORCING" --tap --tag=L24 \
      > "outputs/log_pulse_magiccclim_vv${M}_${SPECIE}_${FORCING}.txt" 2>&1
  done
done
echo "$(ts) DONE $SPECIE: ${#MARKERS[@]} markers x 2 conventions"
