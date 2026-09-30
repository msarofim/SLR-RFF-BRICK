#!/bin/bash
## gate_calibrator_identity.sh — does calibrate_mcmc_ext.jl still define the L27 objective?
##
## Runs run_mcmc_L27.sh's configuration (flags, starts, proposal seed) for 300 iterations from seed
## 2026 and demands that every field of the chain equals the first 300 rows of the PRODUCTION L27
## chain, except `accept_rate` (a whole-run stamp that depends on run length). The reference comes
## from the run behind the shipped posterior, not from the code under test, so a pass CERTIFIES the
## objective rather than re-baselining it. The 300-iteration covariance is also compared byte-for-byte
## (regression only). See benchmark/reference/calibrator_300iter_L27/README.md.
## Needs the L27 AIS target at outputs/recalib_targets_ext.csv (md5 070f74ab; the prep default).
## MUTATION-TESTED at creation (2026-09-30): --amp-sigma=0.181 -> chain FAIL.
##
##   bash scripts/gate_calibrator_identity.sh            # ~2.5 min; exit 0 = identical
##   GATE_MUTATE='s/--amp-sigma=0.180/--amp-sigma=0.181/' bash scripts/gate_calibrator_identity.sh   # must FAIL
## ⚠ The mutation EDITS the flag string. Appending a second --amp-sigma does nothing: the calibrator
## reads the FIRST occurrence, so an appended mutation "passes" -- that is how the first mutation
## test of this gate came back green (2026-09-30), with the prior still at 0.180 in the log.
set -uo pipefail
cd "$(dirname "$0")/.."
REF=benchmark/reference/calibrator_300iter_L27
TAG=gate27
FLAGS="$(sed -n 's/^FLAGS="\(.*\)"$/\1/p' run_mcmc_L27.sh)"
[ -n "$FLAGS" ] || { echo "[GATE] cannot read FLAGS from run_mcmc_L27.sh"; exit 2; }
if [ -n "${GATE_MUTATE:-}" ]; then
    MUT="$(printf '%s' "$FLAGS" | sed "$GATE_MUTATE")"
    [ "$MUT" != "$FLAGS" ] || { echo "[GATE] GATE_MUTATE changed nothing -- not a mutation"; exit 2; }
    FLAGS="$MUT"; echo "[GATE] MUTATED flags: $FLAGS"
fi
TGT_MD5=$(md5 -q outputs/recalib_targets_ext.csv 2>/dev/null || md5sum outputs/recalib_targets_ext.csv | cut -d' ' -f1)
[ "$TGT_MD5" = "070f74abe11080da7b77a80b67c54033" ] || { echo "[GATE] outputs/recalib_targets_ext.csv is not the L27 target (md5 $TGT_MD5)"; exit 2; }
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
julia --project=julia_v2 --threads=1 julia/calibrate_mcmc_ext.jl 300 2026 \
    --tag=$TAG --overdisperse --starts=outputs/mcmc/overdispersed_starts_L27.csv \
    --adcov=adapted_cov_L26_named.csv $FLAGS \
    > outputs/mcmc/log_${TAG}.txt 2>&1 || { echo "[GATE] calibrator FAILED to run; see outputs/mcmc/log_${TAG}.txt"; exit 2; }
ok=0
## exact field-by-field comparison of every column but accept_rate (found by name, not position)
awk -F, 'NR==FNR { a[FNR]=$0; next }
         FNR==1 { if ($0 != a[1]) { print "[GATE] header differs"; bad=1; exit }
                  for (i=1;i<=NF;i++) if ($i=="accept_rate") skip=i; next }
         { split(a[FNR], r, ",")
           for (i=1;i<=NF;i++) if (i!=skip && $i!=r[i]) { printf "[GATE] row %d col %d differs\n", FNR-1, i; bad=1; exit } }
         END { if (!bad && FNR!=301) { print "[GATE] row count " FNR " != 301"; bad=1 }; exit bad }' \
    $REF/chain_L27prod_seed2026_first300.csv outputs/mcmc/chain_${TAG}_seed2026_n300.csv \
    || { echo "[GATE] FAIL: 300-iteration chain differs from the PRODUCTION L27 chain"; ok=1; }
cmp -s outputs/mcmc/adapted_cov_${TAG}_seed2026.csv $REF/adapted_cov_L27_seed2026_n300.csv \
    || { echo "[GATE] FAIL: 300-iteration adapted covariance differs from the 2026-09-30 reference"; ok=1; }
[ $ok -eq 0 ] && echo "[GATE] PASS: calibrator reproduces the production L27 chain (all fields but accept_rate) and the reference covariance"
exit $ok
