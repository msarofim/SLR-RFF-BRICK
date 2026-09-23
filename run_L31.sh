#!/bin/bash
## L31 (2026-09-22) = L28 PLUS `--ais-fit-from=1979`. CONTROL = L28, ONE AXIS.
##
## WHAT IT TESTS (Marcus, 09-22: "try option 5"). IMBIE 2026's net == smb + dyn is an IDENTITY and this
## module's SMB cannot produce the +141 Gt/yr 2018-23 snowfall excursion, so fitting the Antarctic LEVEL
## and matching IMBIE's DYNAMICS partition are mutually exclusive: every Gt/yr gained on the net transfers
## one-for-one into the dynamics error. L28/L29/L30 all bought the level and paid in dynamics; the rho-cap
## (L29) and the additional-discharge ramp (L30) were each tested and bought nothing.
##
## Option 5 is the one remaining route with a MEASURED chance of changing the answer. Attributing the AIS
## level term's objection per year (julia/diag_ais_isocumulative_channels.jl, BOTH the antarctic_alpha and
## the anto_alpha/beta axes, n=100, CHANGELOG 09-22l): forcing the model onto IMBIE's dynamics anomaly at
## fixed cumulative costs 12.3-16.2 log-units on the full 1900-2025 span, but only 2.7-3.8 on 1979+ --
## the barrier falls 3.2-4.5x. At alpha x1.3 (dynamics anomaly -150.4 vs IMBIE's -167.2) the level cost
## goes -4.12 -> -1.28. Those are FIXED-PARAMETER numbers, i.e. an UPPER BOUND on a refit's cost, which is
## why a refit is worth running: it has freedom the diagnostic did not.
##
## ⚠ THE 1979 BOUNDARY IS A PROPERTY OF THE TARGET, NOT A TUNING KNOB. prep_recalib_targets_ext.py splices
## Frederikse 2020 (1900-1978) onto IMBIE over IMBIE_JOIN_WIN (1979-1988); from 1979 the `ais` column IS
## the IMBIE reconciled record. So this arm fits the Antarctic to ONE dataset instead of two spliced ones.
## That is the argument for it and it is the honest way to describe it. It is NOT a window-rate term --
## that would double-count, because the level target equals IMBIE to machine precision from 1992 on.
##
## ⛔⛔ L31's LOGPOST IS NOT COMPARABLE TO L28's OR L27's. Dropping 79 years removes 79 likelihood terms:
## at the shared MAP start, logpost(theta0) = -1220.7 on the full span and -554.95 on 1979+. That ~666 is
## BOOKKEEPING, not fit. Compare arms on HINDCAST STATISTICS and on the channels, never on log_post.
## (Same trap as flat priors making L30 look -15.6 worse than L28 on an unchanged likelihood.)
##
## ⚠ THE FLAG WAS MUTATION-TESTED BEFORE THIS RUN (a gate that passes is not a gate that works):
##   no flag              -> "ais 1900-2025", logpost(theta0) -1220.7
##   --ais-fit-from=1900  -> "ais 1900-2025", logpost(theta0) -1220.7   (byte-identical: the null case)
##   --ais-fit-from=1979  -> "ais 1979-2025", 47 yr, logpost(theta0) -554.95
##
## ⭐ SUCCESS CRITERIA, PRE-REGISTERED so the answer cannot be moved after the numbers land. The POINT of
## this arm is the DISCHARGE, not the level:
##   PRIMARY  2018-23 dynamics anomaly moves from L28's -74.6 Gt/yr toward IMBIE's -167.2.
##            Call it a WIN at <= -110 (i.e. past L30's -102 and at least halfway to L27's -119.1);
##            call it NO EFFECT above -90; -90..-110 is ambiguous and must be reported as such.
##   SECOND   rho_ais comes off 0.966 (the value at which the level channel loses shape discrimination).
##   COST     the 1900-1978 hindcast, which is now OUT-OF-SAMPLE, not absent. ⚠ REPORT IT EITHER WAY.
##            L28's 1900-78 Antarctic loss already runs 2x its target; if L31 is worse than L28 there,
##            that is the price and it must be stated next to the win.
##   GUARD    the four non-Antarctic components must stay within ~0.02 sigma of L28, as L28/L29/L30 all
##            did. If Greenland / glaciers / thermal expansion move, the change did not stay local and
##            the arm is not interpretable as an Antarctic experiment.
##
## Everything else is L28's: BASEFLAGS + --no-ledger (50 params), seeds 2026-2029, starts = L27's own
## 2nd-half draws at the ais_iceflow0 quantiles, proposal seed = L27's pooled covariance. 4 chains in
## parallel on the Mac (~4 h under a quiet load). Torch was considered and is NOT warranted: every arm
## L27-L30 ran here, and the Julia/Mimi/MimiBRICK stack is not provisioned there.
## Kill by PID (never pkill -f); log = outputs/log_L31.txt.
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
LOG=outputs/log_L31.txt; : > "$LOG"
[[ "$(md5 -q outputs/recalib_targets_ext.csv)" == "eb768cd96463a3b84721e2bb9a20f009" ]] || { echo "target file is not the IMBIE-2026 build"; exit 2; }
J="julia --project=julia_v2"
NITER=2000000
BASEFLAGS="--gis-ordered --gis-basins2 --amp-mu=1.09 --amp-sigma=0.180 --paleo-priors --no-delta --no-d2-gsic --obs-corr-len=100 --toff-lo=-4 --precip-reparam --cut-fastdyn --fix-gamma"
AISFLAG="--ais-fit-from=1979"
say(){ echo "[$(date '+%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }
## ⚠ GATE ADDED 2026-09-23, AFTER THIS ARM HAD ALREADY RUN — it did NOT affect the run it records.
## The inherited step() printed "FAILED ... — continuing" and the driver then said ALLDONE
## regardless, so a run with dead stages was indistinguishable from a clean one (flagged by another
## session on run_L32_bench.sh). Failures are now counted and ALLDONE is earned.
FAILED_STEPS=0
step(){ local nm="$1"; shift
  say "START  $nm"
  if "$@" >> "$LOG" 2>&1; then say "OK     $nm"; else say "FAILED $nm (rc=$?) — continuing"; FAILED_STEPS=$((FAILED_STEPS+1)); fi
}

run_chains(){ # TAG SEEDS STARTS ADCOV FLAGS
  local T="$1" SEEDS="$2" STARTS="$3" ADCOV="$4" FLAGS="$5"
  [[ -f "$STARTS" ]] || { say "MISSING $STARTS"; return 1; }
  [[ -f "outputs/mcmc/$ADCOV" ]] || { say "MISSING outputs/mcmc/$ADCOV"; return 1; }
  say "$T: 4 chains x $NITER (seeds $SEEDS) — $FLAGS ; adcov=$ADCOV starts=$STARTS ; commit $(git rev-parse --short HEAD) ; load $(uptime | sed 's/.*load averages*: //')"
  local PIDS=()
  for SEED in $SEEDS; do
    $J --threads=1 julia/calibrate_mcmc_ext.jl "$NITER" "$SEED" \
        --tag=$T --overdisperse --starts=$STARTS --adcov=$ADCOV $FLAGS \
        > "outputs/mcmc/log_${T}_seed${SEED}.txt" 2>&1 &
    PIDS+=($!)
  done
  say "  chain PIDs: ${PIDS[*]}"
  wait "${PIDS[@]}"
  say "$T chains done. ARM VERIFICATION:"
  for SEED in $SEEDS; do
    say "  seed$SEED: $(tr '\r' '\n' < outputs/mcmc/log_${T}_seed${SEED}.txt | grep -a -m1 'L26 structure flags') | $(tr '\r' '\n' < outputs/mcmc/log_${T}_seed${SEED}.txt | grep -a -m1 'seeding proposal' | cut -c1-90)"
    ## ⚠ THE SPAN IS VERIFIED PER CHAIN, not assumed from the flag string. A flag that is silently
    ## dropped (wrong spelling, wrong position) would otherwise produce a full-span arm labelled L31.
    say "    span: $(tr '\r' '\n' < outputs/mcmc/log_${T}_seed${SEED}.txt | grep -a -m1 'Extended fit windows' | cut -c1-70)"
    tr '\r' '\n' < "outputs/mcmc/log_${T}_seed${SEED}.txt" | grep -aq 'ais 1979-' \
      || say "    *** SPAN GATE FAILED on seed $SEED: the AIS term is NOT restricted ***"
  done
}

noise_gate(){ # TAG SEEDS
  source ~/climate-env/bin/activate
  python - "$1" $2 >> "$LOG" 2>&1 <<'PY'
import sys, pandas as pd
t = sys.argv[1]; bad = []
for s in sys.argv[2:]:
    d = pd.read_csv(f"outputs/mcmc/chain_{t}_seed{s}_n2000000.csv", usecols=["sd_gis", "sd_ais", "log_post"]); d = d.iloc[len(d)//2:]
    m = d.sd_gis.median(); print(f"  seed{s}: sd_gis median {m:.4f}  sd_ais {d.sd_ais.median():.4f}  log_post {d.log_post.median():.1f}  {'OK' if m < 0.10 else '*** NOISE MODE ***'}")
    if m >= 0.10: bad.append(s)
print(f"NOISE-MODE GATE {t}:", "PASS" if not bad else f"FAIL on seeds {bad}")
PY
  grep -q "NOISE-MODE GATE $1: PASS" "$LOG"
}

postprocess(){ # TAG
  local T="$1"
  step "$T slr convergence diag" $J julia/diag_slr_convergence_by_chain_ladrillo.jl --tag=$T
  step "$T postprocess (subsample; DO NOT KILL)" $J julia/postprocess_mcmc_ext.jl --tag=$T --accept-slr
  step "$T posterior predictive" $J julia/posterior_predictive_ladrillo.jl --tag=$T
  step "$T ssp components (tap, fixed climate)" $J julia/project_ssps_components_ladrillo.jl --tag=$T
  ## the PRIMARY criterion: the discharge split against IMBIE
  step "$T DAIS flux split vs IMBIE" $J julia/diag_ais_flux_split_vs_imbie.jl --tag=$T 1000
}

## ---- L31 ----------------------------------------------------------------------------------------------------
run_chains L31 "2026 2027 2028 2029" outputs/mcmc/overdispersed_starts_L27r.csv adapted_cov_L27_named.csv "$BASEFLAGS --no-ledger $AISFLAG"
if noise_gate L31 "2026 2027 2028 2029"; then postprocess L31; else say "L31 noise-mode gate FAILED — not postprocessing (investigate, do not --force)"; fi
(( FAILED_STEPS == 0 )) && say "ALLDONE — 0 failed step(s)" \
  || { say "INCOMPLETE — $FAILED_STEPS failed step(s); do not read the outputs as final."; exit 1; }
