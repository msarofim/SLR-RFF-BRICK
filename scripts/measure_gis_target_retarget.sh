#!/bin/bash
# measure_gis_target_retarget.sh — what re-deriving the Greenland matched 2300 targets on
# calib 1.6.0 forcing does to every consumer, MEASURED rather than assumed (2026-09-30).
#
# Builds three APFS copy-on-write clones of this repo (cp -c: no disk cost, and nothing
# the consumers write can reach the real outputs/) and runs every consumer of
# gis_targets.MATCHED_* in dependency order in each:
#   A  calib 1.4.5 forcing (fair_mean_gmst/ohc + cube raw restored from 839a176^)
#      + calib 1.4.5 targets                    = what was shipped 08-21..08-23
#   B  calib 1.6.0 forcing + calib 1.4.5 targets = what any re-run since 08-28 gives
#   C  calib 1.6.0 forcing + calib 1.6.0 targets = the proposal
# ⚠ HISTORICAL (applied 2026-09-30): this measures the state at commit dded135, BEFORE the
# targets became calibration-keyed. Its C-sandbox patch expects the old single-set
# literals, so run it from `git worktree add <dir> dded135`, not from a later checkout.
# A must reproduce the shipped outputs byte-for-byte or the comparison means nothing;
# compare_gis_target_retarget.py REAL A checks that.
#
#   scripts/measure_gis_target_retarget.sh <empty-scratch-dir>
# then
#   python scripts/compare_gis_target_retarget.py <scratch-dir> B C
set -euo pipefail
REPO=$(cd "$(dirname "$0")/.." && pwd)
S=${1:?usage: $0 <scratch-dir>}
mkdir -p "$S"
[ -z "$(ls -A "$S")" ] || { echo "$S is not empty"; exit 1; }
MIGRATION=839a176   # "Regenerate the SSP cube line on calib 1.6.0 + CMIP7"

clone() { mkdir "$S/sbx$1"; for e in $(ls -A "$REPO" | grep -v -E '^\.claude$'); do cp -c -R "$REPO/$e" "$S/sbx$1/"; done; }
clone A; clone B; clone C

# A: the pre-migration forcing, every data file the migration commit touched
for f in $(git -C "$REPO" show --name-only --format= $MIGRATION -- data/observations/); do
  rm -f "$S/sbxA/$f"; git -C "$REPO" show "$MIGRATION^:$f" > "$S/sbxA/$f"
done

# C: the calib 1.6.0 targets at the canonical paths, and the literals that match them
cp -c "$REPO/outputs/gis_matched_targets_2300_calib160.csv" "$S/sbxC/outputs/gis_matched_targets_2300.csv.new"
mv "$S/sbxC/outputs/gis_matched_targets_2300.csv.new" "$S/sbxC/outputs/gis_matched_targets_2300.csv"
cp -c "$REPO/outputs/scope_gis_cool_band_targets_calib160.csv" "$S/sbxC/outputs/scope_gis_cool_band_targets.csv.new"
mv "$S/sbxC/outputs/scope_gis_cool_band_targets.csv.new" "$S/sbxC/outputs/scope_gis_cool_band_targets.csv"
python3 - "$S/sbxC" <<'EOF'
import sys
C = sys.argv[1]
def sub(p, old, new):
    s = open(p).read()
    assert s.count(old) == 1, (p, old)
    open(p, "w").write(s.replace(old, new))
sub(f"{C}/python/gis_targets.py",
    '"SSP2-4.5": (0.106, 0.215),\n                  "SSP5-8.5": (0.429, 1.450)}',
    '"SSP2-4.5": (0.105, 0.212),\n                  "SSP5-8.5": (0.372, 1.297)}')
sub(f"{C}/python/gis_targets.py",
    '"SSP2-4.5": 0.154, "SSP5-8.5": 0.985}', '"SSP2-4.5": 0.153, "SSP5-8.5": 0.869}')
sub(f"{C}/python/diag_gis_2150_band_veto.py", "P50_2300_CM = 98.5 ", "P50_2300_CM = 86.9 ")
sub(f"{C}/julia/diag_gis_cell_vs_priority_ladder.jl",
    "const MATCHED_2300 = (lo = 42.9, p50 = 98.5, hi = 145.0)",
    "const MATCHED_2300 = (lo = 37.2, p50 = 86.9, hi = 129.7)")
EOF

ORDER="scope_gis_leq_ridge_vs_literature scope_gis_basin_mock_vs_literature
scope_gis_basin_zonespace_vs_literature scope_gis_rate_power_vs_literature
scope_gis_ridge_vs_ssp_bands scope_gis_3basin_partition scope_gis_tap_l13
scope_gis_reservoir_offline scope_gis_reservoir_rate_rank scope_gis_gamma_offline
scope_gis_onset_rescan diag_gis_matched_band_score diag_gis_amp_above_275
diag_gis_cascade_rate_crit diag_gis_committed_loss diag_gis_k_vs_residual
diag_gis_npv_tau_sensitivity diag_gis_residual_band diag_gis_scorecard_logo
diag_gis_separation_target diag_gis_2150_band_veto plot_gis_basin_mock
plot_gis_rate_power_scan"
source ~/climate-env/bin/activate
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
       JULIA_NUM_THREADS=1 MPLBACKEND=Agg
touch "$S/_marker"          # outputs newer than this were written by these runs
run() {  # one sandbox; a consumer that refuses (its own gate) is a RESULT, so no set -e
  local X=$1 L="$S/runs/$1"; mkdir -p "$L"; : > "$L/_status.txt"
  cd "$S/sbx$X"
  julia --project=julia_v2 julia/diag_gis_cell_vs_priority_ladder.jl > "$L/julia_ladder.log" 2>&1 \
    && echo "julia_ladder rc=0" >> "$L/_status.txt" || echo "julia_ladder rc=$?" >> "$L/_status.txt"
  for f in $ORDER; do
    local t0=$(date +%s) rc=0
    perl -e 'alarm shift; exec @ARGV' 1800 python python/$f.py > "$L/$f.log" 2>&1 || rc=$?
    echo "$f rc=$rc $(( $(date +%s) - t0 ))s" >> "$L/_status.txt"
  done
  echo DONE >> "$L/_status.txt"
}
set +e
run A & pa=$!; run B & pb=$!; run C & pc=$!
wait $pa $pb $pc      # wait on PIDs, never a pgrep loop (it matches itself)
paste "$S/runs/A/_status.txt" "$S/runs/B/_status.txt" "$S/runs/C/_status.txt"
