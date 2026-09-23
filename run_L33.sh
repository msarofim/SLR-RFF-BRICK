#!/bin/bash
## L33 (2026-09-23) = L28 + `--sd-ais-floor=smb2021`. CONTROL = L32, ONE AXIS: the FLOOR'S VALUE.
##
## ⭐ THIS IS A FALSIFICATION TEST, NOT AN IMPROVEMENT ATTEMPT. L32 (floor 0.03259 cm, from the
## IMBIE 2026 SMB record) moved the 2018-23 dynamics anomaly to -133.1, off the identity trade-off
## line by 38.9 Gt/yr, and strictly dominated L27. The obvious way that result could be an artifact
## is the FLOOR'S OWN VALUE: IMBIE 2021 and IMBIE 2026 disagree about how much interannual
## variability the record contains, and L32 used the HIGHER vintage.
##
## The floor is re-derived against the earlier release: IMBIE 2021 has no SMB partition, so the only
## cross-vintage handle is the TOTAL, whose year-on-year sd over the shared 1992-2020 window is
## 36.0 Gt/yr against 2026's 54.8 — a ratio of 0.656. ⚠ APPLYING THAT RATIO TO THE SMB IS AN
## ASSUMPTION (that the vintage difference in the total transfers to its SMB component) and the
## calibrator PRINTS it as such at the gate. It gives 77.4 Gt/yr = **0.02139 cm**, a 34 % lower
## floor — which happens to equal L27's own fitted sd_ais (0.02162) to 1 % and is still 1.5x above
## L28's (0.01394). It is the most conservative defensible floor, so it is the right falsifier.
##
## ⭐ SUCCESS CRITERIA, PRE-REGISTERED. ⚠ THE FRAMING IS INVERTED FROM L31/L32: this arm is trying
## to BREAK a result, so the burden is on ROBUSTNESS, and "no change" is the GOOD outcome.
##   PRIMARY  2018-23 dynamics anomaly. **ROBUST** if it still clears -110 (L32 reached -133.1).
##            **VINTAGE-DEPENDENT** if it reverts above -90 (i.e. back toward L28's -74.6).
##            -90..-110 = PARTIAL, and must be reported as such, not rounded to either verdict.
##   REPORT   whether the floor BINDS at 0.02139. If sd_ais settles ABOVE it, the floor is not doing
##            the work in this arm and the L32-vs-L33 contrast is NOT a clean one-axis comparison —
##            say so rather than reading the dynamics number as if it were.
##   SAME     COST A (hindcast bias), COST B (p05-p95 vs L28) and the GUARD as L32, on one ruler.
##
## Everything else is L32's, including its starts file (all four sd_ais 0.033-0.035, comfortably
## above this lower floor, so nothing is rejected at the start). 4 chains, seeds 2026-2029.
## ⚠ LAUNCHED UNDER CONTENTION: load 47.5 with a large R job running. Expect well over L32's
## 2 h 45 m; read the meter early and requeue rather than wait if the ETA is absurd.
## Torch considered and NOT warranted (stack not provisioned). Kill by PID; log outputs/log_L33.txt.
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
LOG=outputs/log_L33.txt; : > "$LOG"
[[ "$(md5 -q outputs/recalib_targets_ext.csv)" == "eb768cd96463a3b84721e2bb9a20f009" ]] || { echo "target file is not the IMBIE-2026 build"; exit 2; }
J="julia --project=julia_v2"
NITER=2000000
BASEFLAGS="--gis-ordered --gis-basins2 --amp-mu=1.09 --amp-sigma=0.180 --paleo-priors --no-delta --no-d2-gsic --obs-corr-len=100 --toff-lo=-4 --precip-reparam --cut-fastdyn --fix-gamma"
ARMFLAG="--sd-ais-floor=smb2021"
STARTS=outputs/mcmc/overdispersed_starts_L27r_sdfloor.csv
say(){ echo "[$(date '+%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }
step(){ local nm="$1"; shift
  say "START  $nm"
  if "$@" >> "$LOG" 2>&1; then say "OK     $nm"; else say "FAILED $nm (rc=$?) — continuing"; fi
}
run_chains(){ local T="$1" SEEDS="$2" ST="$3" ADCOV="$4" FLAGS="$5"
  [[ -f "$ST" ]] || { say "MISSING $ST"; return 1; }
  say "$T: 4 chains x $NITER (seeds $SEEDS) — $FLAGS ; adcov=$ADCOV starts=$ST ; commit $(git rev-parse --short HEAD) ; load $(uptime | sed 's/.*load averages*: //')"
  local PIDS=()
  for SEED in $SEEDS; do
    $J --threads=1 julia/calibrate_mcmc_ext.jl "$NITER" "$SEED" \
        --tag=$T --overdisperse --starts=$ST --adcov=$ADCOV $FLAGS \
        > "outputs/mcmc/log_${T}_seed${SEED}.txt" 2>&1 &
    PIDS+=($!)
  done
  say "  chain PIDs: ${PIDS[*]}"
  wait "${PIDS[@]}"
  say "$T chains done. ARM VERIFICATION:"
  for SEED in $SEEDS; do
    ## ⚠ THE FLOOR'S VALUE IS READ BACK PER CHAIN, not assumed from the flag string: an arm whose
    ## flag silently fell back to the 2026 value would otherwise be indistinguishable from L32.
    say "    floor: $(tr '\r' '\n' < outputs/mcmc/log_${T}_seed${SEED}.txt | grep -a -m1 'FLOOR DERIVED' | cut -c1-140)"
    tr '\r' '\n' < "outputs/mcmc/log_${T}_seed${SEED}.txt" | grep -aq 'smb2021' \
      || say "    *** FLOOR GATE FAILED on seed $SEED: this is NOT the 2021-vintage floor ***"
  done
}
noise_gate(){ source ~/climate-env/bin/activate
  python - "$1" $2 >> "$LOG" 2>&1 <<'PY'
import sys, pandas as pd
t = sys.argv[1]; bad = []
for s in sys.argv[2:]:
    d = pd.read_csv(f"outputs/mcmc/chain_{t}_seed{s}_n2000000.csv", usecols=["sd_gis","sd_ais","log_post"]); d = d.iloc[len(d)//2:]
    m = d.sd_gis.median(); print(f"  seed{s}: sd_gis median {m:.4f}  sd_ais {d.sd_ais.median():.4f}  log_post {d.log_post.median():.1f}  {'OK' if m < 0.10 else '*** NOISE MODE ***'}")
    if m >= 0.10: bad.append(s)
print(f"NOISE-MODE GATE {t}:", "PASS" if not bad else f"FAIL on seeds {bad}")
PY
  grep -q "NOISE-MODE GATE $1: PASS" "$LOG"; }
postprocess(){ local T="$1"
  step "$T slr convergence diag" $J julia/diag_slr_convergence_by_chain_ladrillo.jl --tag=$T
  step "$T postprocess (subsample; DO NOT KILL)" $J julia/postprocess_mcmc_ext.jl --tag=$T --accept-slr
  step "$T priors dump" $J --threads=1 julia/calibrate_mcmc_ext.jl 1 2026 --tag=$T $BASEFLAGS --no-ledger $ARMFLAG --dump-priors
  step "$T posterior predictive" $J julia/posterior_predictive_ladrillo.jl --tag=$T
  step "$T ssp components (tap, fixed climate)" $J julia/project_ssps_components_ladrillo.jl --tag=$T
  step "$T DAIS flux split vs IMBIE" $J julia/diag_ais_flux_split_vs_imbie.jl --tag=$T 1000
  source ~/climate-env/bin/activate
  step "$T prior/posterior table" python python/ladrillo_prior_posterior_table.py --tag=$T; }
run_chains L33 "2026 2027 2028 2029" "$STARTS" adapted_cov_L27_named.csv "$BASEFLAGS --no-ledger $ARMFLAG"
if noise_gate L33 "2026 2027 2028 2029"; then postprocess L33; else say "L33 noise-mode gate FAILED — not postprocessing"; fi
say "ALLDONE"
