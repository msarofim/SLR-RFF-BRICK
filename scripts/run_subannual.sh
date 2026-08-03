#!/bin/bash
# run_subannual.sh — run a driver with the sub-annual DAIS patch applied, GUARANTEEING restore.
#
# The patch overwrites a file inside the SHARED MimiBRICK depot, so a patched depot left behind means
# every later BRICK job silently gets different physics (pulse statistics move 2-3x). A hand
# apply/restore is one crash away from that. This wrapper traps EXIT so the depot is restored on
# success, failure, or interrupt.
#
# Usage:  scripts/run_subannual.sh julia --project=julia_v2 julia/weight_and_project_brick_fair.jl ARGS...
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PATCH="$REPO/julia/patches/antarctic_icesheet_smoothed_trigger.jl.txt"

# Resolve the depot component of the MimiBRICK that julia_v2 ACTUALLY loads (several slugs exist).
DEPOT=$(julia --project="$REPO/julia_v2" -e '
using MimiBRICK
print(joinpath(dirname(dirname(pathof(MimiBRICK))),"src","components","antarctic_icesheet_component.jl"))')
[ -f "$DEPOT" ] || { echo "FATAL: depot component not found: $DEPOT" >&2; exit 1; }
[ -f "$PATCH" ] || { echo "FATAL: patch not found: $PATCH" >&2; exit 1; }

BACKUP="$(mktemp -t brick_ais_component)"
cp "$DEPOT" "$BACKUP"
restore() {
    local rc=$?
    chmod u+w "$DEPOT" 2>/dev/null || true
    cp "$BACKUP" "$DEPOT"
    chmod u-w "$DEPOT" 2>/dev/null || true
    if cmp -s "$DEPOT" "$BACKUP"; then
        echo "[run_subannual] depot RESTORED pristine (verified)"
    else
        echo "[run_subannual] *** DEPOT RESTORE FAILED — restore by hand from $BACKUP ***" >&2
        return 1
    fi
    rm -f "$BACKUP"
    return $rc
}
trap restore EXIT INT TERM

chmod u+w "$DEPOT"
cp "$PATCH" "$DEPOT"
grep -q frac "$DEPOT" || { echo "FATAL: patch did not take" >&2; exit 1; }
echo "[run_subannual] sub-annual patch ACTIVE on $DEPOT"
echo "[run_subannual] running: $*"
"$@"
