#!/bin/bash
# run_l14_chain_after_tune.sh — wait for the L14tune chain, rebuild the starts, then
# launch L14 production. Written to run UNATTENDED (Marcus away 2026-08-20, ~4 h).
#
# WAITS ON A FILE, NOT ON pgrep. `pgrep -f <pattern>` SELF-MATCHES the waiting shell,
# whose own command line contains the pattern, so `! pgrep` never becomes true and the
# loop spins to timeout. Two waiters hung that way in this arc. The calibrator writes
# the chain CSV LAST (adapted_cov first, then the chain), so the chain file appearing
# AND its size going quiet is the completion signal.
set -euo pipefail
cd "$(dirname "$0")/.."

TUNECHAIN=outputs/mcmc/chain_L14tune_seed2026_n1000000.csv
ADCOV=outputs/mcmc/adapted_cov_L14tune_seed2026.csv
STARTS=outputs/mcmc/overdispersed_starts.csv
TUNELOG=outputs/mcmc/log_L14tune_seed2026.txt
MAXWAIT=7200          # 2 h; the tune's own ETA is ~50 min from launch of this waiter

say() { echo "[$(date '+%H:%M:%S')] $*"; }

say "waiting for $TUNECHAIN (max ${MAXWAIT}s)"
waited=0; last=-1; stable=0
while true; do
  if [[ -f "$TUNECHAIN" ]]; then
    sz=$(wc -c < "$TUNECHAIN")
    if [[ "$sz" -eq "$last" && "$sz" -gt 0 ]]; then
      stable=$((stable+1)); [[ $stable -ge 2 ]] && break
    else
      stable=0
    fi
    last=$sz
  fi
  sleep 30; waited=$((waited+30))
  [[ $waited -ge $MAXWAIT ]] && { say "TIMED OUT after ${MAXWAIT}s — tune did not finish"; exit 1; }
done
say "tune chain complete ($(wc -c < "$TUNECHAIN") bytes)"
[[ -f "$ADCOV" ]] || { say "MISSING $ADCOV — the tune did not write its covariance"; exit 1; }

# LIVENESS GUARD, not a posterior review. A tune that froze (acceptance ~0.0, every MH
# ratio NaN) produces a perfectly well-formed chain file, and spending 5.5 h seeded from
# its covariance is the waste this catches. 0.05 is far below the ~0.24 this
# configuration runs at and far above a frozen chain's 0.000.
ACC=$(tr '\r' '\n' < "$TUNELOG" | grep -a "RAM run:" | tail -1 | sed 's/.*acceptance = //')
say "tune acceptance = ${ACC:-UNKNOWN}"
[[ -n "$ACC" ]] || { say "could not read acceptance from $TUNELOG — refusing to proceed"; exit 1; }
awk -v a="$ACC" 'BEGIN { exit !(a > 0.05) }' || {
  say "acceptance $ACC <= 0.05 — the tune chain is frozen, NOT launching production"; exit 1; }

say "backing up starts -> ${STARTS}.pre_l14_bak"
cp "$STARTS" "${STARTS}.pre_l14_bak"
say "rebuilding starts from the L14tune chain"
OPENBLAS_NUM_THREADS=1 julia --project=julia_v2 julia/build_overdispersed_starts.jl "$TUNECHAIN"

# The two column facts run_l14_production.sh will re-check. Checked here too so a bad
# rebuild is reported at the point it happened rather than as a launch refusal.
head -1 "$STARTS" | tr ',' '\n' | grep -qx gis_s_high || { say "rebuilt starts lack gis_s_high"; exit 1; }
head -1 "$STARTS" | tr ',' '\n' | grep -qx gis_s_mid  && { say "rebuilt starts still carry gis_s_mid"; exit 1; }
say "starts rebuilt: gis_s_high present, gis_s_mid absent"

say "launching L14 production (4 x 2M, ~5.5 h)"
./julia/run_l14_production.sh
say "L14 production returned $?"
