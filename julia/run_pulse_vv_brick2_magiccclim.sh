#!/usr/bin/env bash
# run_pulse_vv_brick2_magiccclim.sh -- BRICK 2.0 on MAGICC's OWN paired pulse climate,
# 7 van Vuuren markers, CO2, spliced AND raw. The counterpart of run_pulse_vv_magiccclim.sh
# (Ladrillo), and §8 item 5 of FaIRtoFrEDI/notes/handoff_2026-09-04f_magiccclim_pulse_arm.md.
#
# ⛔ NEVER EDIT THIS SCRIPT, OR THE JULIA IT CALLS, WHILE IT RUNS. bash and Julia both read
#    incrementally; an edit shifts byte offsets under the live process and it resumes mid-token,
#    then reports a line that is perfectly fine on disk (`never_edit_a_running_script`). The
#    driver is called through a FROZEN COPY for exactly that reason -- and the frozen copy is
#    GITIGNORED, so a `git add` of it FAILS and, chained with &&, silently skips the commit
#    that follows (handoff_2026-09-04f §6.7; it happened once).
#
# SPEC (Marcus, 2026-09-05): match the shipped arms EXACTLY -- 1 GtCO2, pulse year 2030, seven
# markers, joint driver, SPLICED primary with the RAW control MEASURED rather than assumed.
# The Lemoine-Traeger pair is what the driver reports; never a median.
#
# ⚠ WHY RAW IS RUN HERE WHEN STAGE 3 NEVER RAN IT. `[SPLICE-DELTA]` (2026-09-04f) measured the
# injection convention on Ladrillo's MAGICC-climate arm and found it does NOT cancel for a
# threshold model: te 4e-16 cm and lws exactly 0, but ais 20 % median / 34 % max. Stage 5's
# "the splice cancels on a pair" was measured on FACTS, which has no threshold. BRICK 2.0 has
# one, so its splice cost is a measurement, not an inheritance.
#
# ⚠ `a_glob_is_not_a_model_key`: this run creates the FIRST `_raw_` B20 file on disk. The
# shipped stage-3 glob omits both `_raw_` and `_magiccclim`, so it was correct BY ACCIDENT
# exactly as the Ladrillo one was -- and it stops being correct the moment this finishes.
# Fix the consumer's globs BEFORE reading any table, and let [ROWCOUNT] prove it.
set -euo pipefail
cd "$(dirname "$0")/.."
DRIVER=julia/_frozen_scope_slr_pulse_vv_brick2_magiccclim.jl
NDRAW=2000                       # matches the shipped FaIR-climate arm, so the cells compare
MARKERS=(VL LN L ML M HL H)      # van Vuuren's own order
ts() { date +'[%H:%M:%S]'; }
echo "$(ts) BRICK 2.0 on MAGICC climate | CO2 1 Gt @2030 | ${#MARKERS[@]} markers x 2 conventions"
for FORCING in spliced raw; do
  for M in "${MARKERS[@]}"; do
    echo "$(ts) vv$M / $FORCING ..."
    julia --project=julia_v2 "$DRIVER" \
      --marker="$M" --specie=CO2 --pulse-size=1 --climate=magicc \
      --forcing="$FORCING" --ndraw="$NDRAW" --tag=B20 \
      > "outputs/log_pulse_brick2_magiccclim_vv${M}_${FORCING}.txt" 2>&1
  done
done
echo "$(ts) DONE ${#MARKERS[@]} markers x 2 conventions"
