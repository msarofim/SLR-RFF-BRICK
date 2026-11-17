#!/bin/bash
## Claim-10 pulse test, FaIR stage (Marcus 2026-11-17): 2030 and 2080 pulses, run to 2500, six van Vuuren markers
## (vvLN is outside the poster set), CO2 1 GtCO2 and CH4 0.01 GtCH4. New tags *_<YEAR>_to2500: nothing shipped moves.
## Inputs: FaIRtoFrEDI/calibration_v160_prod/to2500/ (zenodo2500 emissions, CMIP7 forcing to 2501).
## Torch verdict: laptop (19 s per run).
set -uo pipefail
cd "$(dirname "$0")"
FTF=$(cd ../FaIRtoFrEDI && pwd)
LOG=$PWD/outputs/log_vv_pulse2500_20261117.txt
say(){ echo "[$(date '+%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }
step(){ local nm="$1" lg="$2"; shift 2; say "START  $nm"
  if "$@" >> "$lg" 2>&1; then say "OK     $nm"; else say "FAILED $nm (rc=$?)"; echo "$nm" >> "$LOG.fails.fair"; fi; }
rm -f "$LOG.fails.fair"
lg=$PWD/outputs/log_vv_pulse2500_fair.txt; : > "$lg"
cp "$FTF/scripts/build_fair_pulse_vv_v160.py" "$FTF/scripts/_frozen_build_fair_pulse_vv_v160_20261117.py"
for Y in 2030 2080; do for M in VL L ML M HL H; do
  step "FaIR pulse vv$M CO2 1Gt $Y to2500" "$lg" bash -c "cd $FTF && OPENBLAS_NUM_THREADS=4 ~/climate-env/bin/python scripts/_frozen_build_fair_pulse_vv_v160_20261117.py --marker $M --specie CO2 --pulse-size 1 --pulse-year $Y --end-year 2500"
  step "FaIR pulse vv$M CH4 0.01Gt $Y to2500" "$lg" bash -c "cd $FTF && OPENBLAS_NUM_THREADS=4 ~/climate-env/bin/python scripts/_frozen_build_fair_pulse_vv_v160_20261117.py --marker $M --specie CH4 --pulse-size 0.01 --pulse-year $Y --end-year 2500"
done; done
say "fair phase done, $(cat "$LOG.fails.fair" 2>/dev/null | wc -l | tr -d ' ') failures"
