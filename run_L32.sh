#!/bin/bash
## L32 (2026-09-23) = L28 PLUS `--sd-ais-floor=smb`. CONTROL = L28, ONE AXIS. Option 6.
##
## WHAT IT TESTS (Marcus, 09-22: option 6, "do we have evidence of interannual variability beyond
## 2020-23? It is worth trying."). THE EVIDENCE WAS MEASURED FIRST AND IT IS ABUNDANT:
##   IMBIE 2026 Antarctic SMB anomaly, EXCLUDING 2020-23 entirely: sd 92.8, year-on-year sd
##   116.5 Gt/yr (118.0 with the n-1 denominator the code uses). Every decade independently shows
##   sd 79-112 and yoy 107-132. Eight years exceed |z| 1.5 against the 1979-2019 distribution,
##   spread across 1981, 1987, 1994, 2005, 2007, 2016, 2022, 2023. All three regions show it
##   (East 105, West 64, Peninsula 51 yoy, ex-2020s). ⇒ the excursion is NOT the variability;
##   it is one large draw from a distribution that has been there for four decades.
##
## ⚠ ONLY A STOCHASTIC VERSION IS IMPLEMENTABLE. GMST explains R^2 = 4.3 % of the observed SMB
## anomaly (corr 0.21; its annual change corr 0.01), so the variability is WEATHER, not forcing:
## nothing in this model's state can predict it, and a FORCED SMB term is therefore not available.
##
## ⇒ THE IMPLEMENTABLE FORM IS A FLOOR ON THE ANTARCTIC NOISE TERM, DERIVED FROM THE OBSERVATION.
## At 3620 Gt per cm GMSL, 118.0 Gt/yr of irreducible SMB weather is 0.03259 cm/yr of level
## innovation that NOTHING in the model can produce (its own SMB yoy sd is 3-6 Gt/yr, 20-38x too
## quiet). Yet the likelihood puts sd_ais at 0.0139 cm (L28) / 0.0214 (L27) — 1.5-2.3x BELOW that,
## with 0.03259 about 2x outside L28's posterior p95 of 0.0171. The smooth trajectory is being
## credited with explaining interannual variability it cannot explain. **That is a misspecified
## noise model, not a fit**, and the floor is the observation refusing it.
##
## ⚠ MEASURED IN A 30k PRE-FLIGHT, NOT ASSUMED: acceptance 0.246 (L31's was 0.237, so the hard
## boundary does NOT cripple the sampler), and the floor BINDS — p05 0.03261, 76.6 % of draws
## within 2 % of it. sd_ais will therefore be a BOUND parameter in this arm, like L29's rho.
##
## ⚠⚠ THE MECHANISM IS NOT SELECTIVE, AND THIS IS THE ARM'S MAIN WEAKNESS. sd_ais 0.0139 -> 0.0326
## makes the sigma-p term (0.0326/0.0139)^2 = 5.5x larger, so the level penalty on ANY discrepancy
## shrinks ~5.5x — a bigger barrier cut than option 5's 3.2-4.5x, but it loosens the Antarctic
## constraint on EVERYTHING, not preferentially on a steeper discharge. A win on the dynamics MUST
## therefore be reported together with the widened posterior, or it is not a win.
##
## ⛔ L32's LOGPOST IS NOT COMPARABLE TO L28's. Different feasible region (a bound) and a different
## noise scale: the pre-flight sat at log_post ~793 against L28's ~620s. That is the sigma change,
## not fit. Compare on hindcast statistics and the channels only.
##
## ⚠ STARTS: L27's overdispersed starts all have sd_ais 0.019-0.021, BELOW the floor, so all four
## would be rejected and the chain would refuse to start (pre-flighted — it dies loudly, it does
## not run silently wrong). `overdispersed_starts_L27r_sdfloor.csv` is those same starts with
## sd_ais shifted to floor*1.05 keeping the original spread (0.002132) and EVERY OTHER COLUMN
## BYTE-IDENTICAL.
##
## ⭐ SUCCESS CRITERIA, PRE-REGISTERED so the answer cannot be moved after the numbers land.
##   PRIMARY  2018-23 dynamics anomaly moves from L28's -74.6 Gt/yr toward IMBIE's -167.2.
##            WIN at <= -110; NO EFFECT above -90; -90..-110 is ambiguous and must be said so.
##            (Identical threshold to L31's, so the two options are judged on one ruler.)
##   COST A   the Antarctic hindcast. A 5.5x looser constraint should fit WORSE in the mean —
##            report the AIS bias at 1900/1950/2018/2025 against L28 either way.
##   COST B   the posterior WIDTH. Report the SSP AIS p05-p95 at 2100 and 2300 vs L28. If the
##            dynamics improves only because everything got wider, say that plainly.
##   GUARD    the four non-Antarctic components within ~0.02 sigma of L28, as every arm L28-L31
##            managed. If Greenland / glaciers / thermal expansion move, the change did not stay
##            local and the arm is not interpretable as an Antarctic experiment.
##   ⚠ NOT A CRITERION: sd_ais sitting on its bound. That is true BY CONSTRUCTION (pre-flight
##            76.6 %) and is not evidence of anything.
##
## Everything else is L28's: BASEFLAGS + --no-ledger (50 params), seeds 2026-2029, L27's pooled
## proposal covariance. 4 chains in parallel on the Mac (~2 h 45 m at L31's pace). Torch was
## considered and is NOT warranted: every arm L27-L31 ran here and the Julia/Mimi/MimiBRICK stack
## is not provisioned there. Kill by PID (never pkill -f); log = outputs/log_L32.txt.
set -uo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
LOG=outputs/log_L32.txt; : > "$LOG"
[[ "$(md5 -q outputs/recalib_targets_ext.csv)" == "eb768cd96463a3b84721e2bb9a20f009" ]] || { echo "target file is not the IMBIE-2026 build"; exit 2; }
J="julia --project=julia_v2"
NITER=2000000
BASEFLAGS="--gis-ordered --gis-basins2 --amp-mu=1.09 --amp-sigma=0.180 --paleo-priors --no-delta --no-d2-gsic --obs-corr-len=100 --toff-lo=-4 --precip-reparam --cut-fastdyn --fix-gamma"
ARMFLAG="--sd-ais-floor=smb"
STARTS=outputs/mcmc/overdispersed_starts_L27r_sdfloor.csv
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
  local T="$1" SEEDS="$2" ST="$3" ADCOV="$4" FLAGS="$5"
  [[ -f "$ST" ]] || { say "MISSING $ST"; return 1; }
  [[ -f "outputs/mcmc/$ADCOV" ]] || { say "MISSING outputs/mcmc/$ADCOV"; return 1; }
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
    say "  seed$SEED: $(tr '\r' '\n' < outputs/mcmc/log_${T}_seed${SEED}.txt | grep -a -m1 'L26 structure flags') | $(tr '\r' '\n' < outputs/mcmc/log_${T}_seed${SEED}.txt | grep -a -m1 'seeding proposal' | cut -c1-90)"
    ## ⚠ THE FLOOR IS VERIFIED PER CHAIN AND ITS VALUE READ BACK, not assumed from the flag string.
    ## A dropped or misspelled flag would otherwise produce an unfloored arm labelled L32.
    say "    floor: $(tr '\r' '\n' < outputs/mcmc/log_${T}_seed${SEED}.txt | grep -a -m1 'sd_ais FLOOR' | cut -c1-120)"
    tr '\r' '\n' < "outputs/mcmc/log_${T}_seed${SEED}.txt" | grep -aq 'FLOOR DERIVED FROM OBSERVATION' \
      || say "    *** FLOOR GATE FAILED on seed $SEED: sd_ais is NOT floored from the observation ***"
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
  ## the priors dump must precede the prior/posterior table AND posterior_predictive, which now
  ## recovers a restricted AIS span from the priors file's provenance (L31 lesson).
  step "$T priors dump" $J --threads=1 julia/calibrate_mcmc_ext.jl 1 2026 --tag=$T $BASEFLAGS --no-ledger $ARMFLAG --dump-priors
  step "$T posterior predictive" $J julia/posterior_predictive_ladrillo.jl --tag=$T
  step "$T ssp components (tap, fixed climate)" $J julia/project_ssps_components_ladrillo.jl --tag=$T
  step "$T DAIS flux split vs IMBIE" $J julia/diag_ais_flux_split_vs_imbie.jl --tag=$T 1000
  source ~/climate-env/bin/activate
  step "$T prior/posterior table" python python/ladrillo_prior_posterior_table.py --tag=$T
}

## ---- L32 ----------------------------------------------------------------------------------------------------
run_chains L32 "2026 2027 2028 2029" "$STARTS" adapted_cov_L27_named.csv "$BASEFLAGS --no-ledger $ARMFLAG"
if noise_gate L32 "2026 2027 2028 2029"; then postprocess L32; else say "L32 noise-mode gate FAILED — not postprocessing (investigate, do not --force)"; fi
(( FAILED_STEPS == 0 )) && say "ALLDONE — 0 failed step(s)" \
  || { say "INCOMPLETE — $FAILED_STEPS failed step(s); do not read the outputs as final."; exit 1; }
