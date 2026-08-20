#!/bin/bash
# run_l14_postprocess_after_production.sh — wait for the four L14 production chains,
# then run the post-production pipeline IN THE ORDER THAT MATTERS.
#
# A SEPARATE FILE, deliberately. run_l14_chain_after_tune.sh is already running, and
# bash reads a script INCREMENTALLY as it executes — editing a running script can make
# it resume at a byte offset that is now the middle of a different line. Never edit the
# one in flight; add a sibling.
#
# THE ORDER IS LOAD-BEARING. postprocess --accept-slr reads
# outputs/mcmc/slr_convergence_L14.csv and refuses it if it is older than the newest
# chain. Running the two postprocess calls back-to-back without the convergence
# diagnostic between them produces NO SUBSAMPLE — that is what left L13 without one for
# a day (handoff 2026-08-20b §1).
#
# Every output is TAG-SCOPED (chain_L14_*, slr_convergence_L14.csv,
# parameters_subsample_brick_mengel_L14.csv), so nothing here can clobber L12 (canonical)
# or L13 (certified).
set -uo pipefail          # NOT -e: a failing step must still report, not kill the log
cd "$(dirname "$0")/.."

TAG=L14
NITER=2000000
SEEDS="2026 2027 2028 2029"
MAXWAIT=36000            # 10 h; production is ~5.5 h but it is sharing the box today
JL="julia --project=julia_v2"

say() { echo "[$(date '+%H:%M:%S')] $*"; }
allchains() { for s in $SEEDS; do echo "outputs/mcmc/chain_${TAG}_seed${s}_n${NITER}.csv"; done; }

say "waiting for the $(echo $SEEDS | wc -w | tr -d ' ') ${TAG} production chains (max ${MAXWAIT}s)"
waited=0; last=""; stable=0
while true; do
  have=1
  for f in $(allchains); do [[ -f "$f" ]] || have=0; done
  if [[ $have -eq 1 ]]; then
    now=$(for f in $(allchains); do wc -c < "$f"; done | tr '\n' ' ')
    if [[ "$now" == "$last" ]]; then
      stable=$((stable+1)); [[ $stable -ge 2 ]] && break
    else
      stable=0
    fi
    last="$now"
  fi
  sleep 60; waited=$((waited+60))
  [[ $waited -ge $MAXWAIT ]] && { say "TIMED OUT after ${MAXWAIT}s"; exit 1; }
done
say "all four chains complete"
for s in $SEEDS; do
  a=$(tr '\r' '\n' < "outputs/mcmc/log_${TAG}_seed${s}.txt" | grep -a "RAM run:" | tail -1 | sed 's/.*acceptance = //')
  say "  seed$s acceptance = ${a:-UNKNOWN}"
done

say "[1/4] postprocess (R-hat / ESS; writes nothing canonical if unconverged)"
$JL julia/postprocess_mcmc_ext.jl --tag=$TAG    > "outputs/mcmc/log_${TAG}_postprocess1.txt" 2>&1
say "      -> outputs/mcmc/log_${TAG}_postprocess1.txt (exit $?)"

say "[2/4] SLR convergence by chain — MUST precede --accept-slr"
$JL julia/diag_slr_convergence_by_chain_ladrillo.jl --tag=$TAG \
    > "outputs/mcmc/log_${TAG}_slrconv.txt" 2>&1
say "      -> outputs/mcmc/log_${TAG}_slrconv.txt (exit $?)"

say "[3/4] postprocess --accept-slr (writes the L14 subsample)"
$JL julia/postprocess_mcmc_ext.jl --tag=$TAG --accept-slr \
    > "outputs/mcmc/log_${TAG}_postprocess2.txt" 2>&1
say "      -> outputs/mcmc/log_${TAG}_postprocess2.txt (exit $?)"

say "[4/4] basin shares — the number the whole restructure exists for"
$JL julia/diag_l13_basin_shares.jl --tag=$TAG \
    > "outputs/mcmc/log_${TAG}_basinshares.txt" 2>&1
say "      -> outputs/mcmc/log_${TAG}_basinshares.txt (exit $?)"

say "DONE. Headlines:"
grep -aiE "worst \|z\||rate scales|DETECTED" "outputs/mcmc/log_${TAG}_basinshares.txt" 2>/dev/null | sed 's/^/    /'
grep -aiE "2100|2150|R-hat|Rhat|R̂" "outputs/mcmc/log_${TAG}_slrconv.txt" 2>/dev/null | tail -8 | sed 's/^/    /'
