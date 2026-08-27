#!/bin/bash
## L19 production: 4 RAM chains (seeds 2026-2029). THE T_on-DISPERSED ARM.
## Handoff -26b PRIORITY 2, finally runnable. This is a DIAGNOSTIC arm, NOT a champion
## candidate — see "DO NOT PROMOTE" below.
##
## WHAT CHANGED vs L14 (the CHAMPION) — EXACTLY ONE THING: the DISPERSION AXIS of the starts.
##   L14  --overdisperse on outputs/mcmc/overdispersed_starts.csv     (ais_iceflow0 quantiles)
##   L19  --overdisperse on outputs/mcmc/overdispersed_starts_ton.csv (ais_runoff_Ton bands)
## Amp prior N(0.95, 0.10) = L14's. Proposal adapted_cov_L14tune_seed2026.csv = L14's.
## --gis-ordered --gis-basins2, 2M iters = L14's.
##
## WHY THIS ARM EXISTS. Every arm we trust is ~100% MID BY CONSTRUCTION. L14's starts and
## L18's are the SAME FILE, dispersed along `ais_iceflow0`, and ALL FOUR SIT IN MID
## (-17.837 / -17.673 / -17.952 / -17.810). `no_power_null`: an over-dispersed arm has power
## only along the AXIS IT WAS DISPERSED ON. So L14's 100% MID occupancy and its tight T_on
## (sd 0.09) do NOT show that chains FIND MID from elsewhere — only that they stay where they
## started. That has never been tested. This arm tests it.
##
## AND IT MATTERS MORE NOW THAN WHEN IT WAS QUEUED. scripts/ton_escape_scale.sh (2026-08-27)
## showed the T_on barrier is REAL: every chain of L15/L16/L17/L18 sits 3.5-28.5x above the
## driftless-diffusion null of 2.0x, uniformly, so a restoring force holds chains out of MID.
## A real barrier is EXACTLY the condition under which all-MID starts cannot settle the
## question — chains genuinely cannot cross on their own within 2M draws.
##
## THE STARTS. Built by build_overdispersed_starts.jl with --param=ais_runoff_Ton and
## --sources (the modes do NOT co-exist in one chain — each dominates a different one).
## In physical units, runoff onset GMST = (T_on + 18.435)/amp:
##
##   seed    T_on     amp    GMST onset    band    source          meaning
##   2026  -22.000  1.0643    -3.35 C      LOW     L17 seed2026    runoff always on, deep
##   2027  -19.500  1.1640    -0.92 C      LOW     L16 seed2028    runoff on since pre-industrial
##   2028  -12.000  1.0694    +6.02 C      HIGH    L17 seed2028    runoff essentially never starts
##   2029  -17.800  0.9814    +0.65 C      MID     L17 seed2029    THE CONTROL (= the posterior)
##
## T_on spread 10.00 vs L14/L18's 0.28 — 36x wider on the axis that matters.
##
## ⚠ ALL FOUR STARTS ARE FROM CURRENT-CODE CHAINS (L16/L17), NOT FROM L14. Deliberate:
## commit 893bfaa landed AFTER L14 ran and moved `lws` 0.123 and `dang_closure_sig` 0.151 in
## the likelihood, so L14's own draws score against a DIFFERENT objective. Seed 2029 is the
## MID CONTROL whose specific job is to separate "the modes are real and separated" from
## "MID is no longer favoured under the current targets".
##
## ⚠ AMP-BOUNDS FILTER, and it is load-bearing. The source draws come from arms that ran
## amp ~ N(1.09, 0.180) on [0.55, 1.63]. THIS arm runs L14's N(0.95, 0.10) on [0.70, 1.25],
## so any start with amp outside [0.70, 1.25] would give logposterior = -Inf, every MH ratio
## would be NaN, and the chain would freeze at theta0 reporting "accept 0.0". The builder was
## given --filter=ais_gmst_amp:0.70:1.25; 78-85% of post-burn draws pass. All four picked
## starts are inside. The calibrator's finite-logposterior assertion is the final gate.
##
## ⚠ --starts= IS NEW AND DEFAULT-OFF. It exists so this arm does NOT overwrite
## outputs/mcmc/overdispersed_starts.csv, which is L14's file and load-bearing (L14 AND L18
## both ran on it; reusing it unrebuilt is what makes their comparison exactly controlled).
## PROVEN INERT: regenerating L14's own starts through the extended builder with no new flags
## returned a BYTE-IDENTICAL file. (`mutation_test_gates`.)
##
## ⚠⚠ DO NOT PROMOTE L19, AND DO NOT TREAT ITS SUBSAMPLE AS A DELIVERABLE. If the barrier is
## real the four chains will NOT mix, and a non-mixing ensemble is not a posterior — pooling
## it would manufacture a multi-modal "uncertainty" that is really four separate answers.
## champions.json stays untouched regardless of what this arm returns.
##
## REGISTERED PREDICTION, before the run. The escape-scale result (barrier real, 3.5-28.5x)
## makes me EXPECT branch (B). Record which fired BEFORE reading anything else:
##   (A) ALL FOUR chains migrate to MID (T_on -> ~-17.8). Then MID is genuinely favoured, the
##       barrier is crossable after all, and L14's tight T_on is a real posterior. Champion
##       CONFIRMED and the caveat can be dropped.
##   (B) Chains STAY in their starting bands. Then L14's 100% MID is START-DETERMINED, its
##       T_on sd 0.09 is not a posterior width, and the champion's AIS projections inherit a
##       mode that was chosen by build_overdispersed_starts.jl in July 2026 — before T_on
##       multimodality was known. This is the outcome that forces a caveat.
##   (C) Chains migrate to a band OTHER than MID, or the MID CONTROL (seed 2029) LEAVES MID.
##       Then MID is not favoured under the current targets and the champion is wrong for
##       reasons unrelated to amp. The control is what makes (C) distinguishable from (B).
##
## ⚠ THE ARM IS INFORMATIVE EVEN UNDER (B) — this is the point of the design. If the chains
## never mix, each still equilibrates within its own band, so their MEAN LOG-POSTERIORS give
## a direct per-band comparison UNDER THE CURRENT TARGETS. That is the number nobody has:
## every previous band comparison was made on draws from a single contaminated chain, not on
## chains equilibrated in each band. Read the log-posterior gap, not just the occupancy.
##
## ⚠ BLAS PINNED (pin_blas_threads). L14 took ~2h34m for 4x2M on an idle machine.
## ⚠ CHECK THE MACHINE FIRST (eta_in_days_is_not_a_slow_run): `uptime`, `sysctl -n
## vm.swapusage`, and read the meter's ETA at ~5 min. ETA in DAYS => kill and requeue.
##
##   bash run_mcmc_L19.sh [n_iter]        # default 2000000
set -e
cd "$(dirname "$0")"
NITER="${1:-2000000}"
TAG="${TAG:-L19}"
ADCOV=adapted_cov_L14tune_seed2026.csv
STARTS=outputs/mcmc/overdispersed_starts_ton.csv
mkdir -p outputs/mcmc

[[ -f "$STARTS" ]] || { echo "MISSING $STARTS — rebuild it:"; echo "  julia --project=julia_v2 julia/build_overdispersed_starts.jl \\"; \
  echo "    outputs/mcmc/chain_L17_seed2026_n2000000.csv --param=ais_runoff_Ton \\"; \
  echo "    --sources=<4 chains> --targets=-22.0,-19.5,-12.0,-17.8 \\"; \
  echo "    --filter=ais_gmst_amp:0.70:1.25 --out=$STARTS"; exit 1; }
# The whole point of this arm is the dispersion. If the file is not actually dispersed on
# T_on, the run has NO POWER and must not be launched — this is the failure L14 had silently.
python3 - "$STARTS" <<'PY' || exit 1
import csv,sys
r=list(csv.DictReader(open(sys.argv[1])))
t=[float(x['ais_runoff_Ton']) for x in r]
a=[float(x['ais_gmst_amp']) for x in r]
ok=True
if len(r)!=4: print(f"  FAIL: {len(r)} rows, need 4"); ok=False
if max(t)-min(t) < 3.0:
    print(f"  FAIL: T_on spread {max(t)-min(t):.2f} — NOT dispersed; this arm would have no power."); ok=False
bands={("LOW" if x<=-18.5 else "MID" if x<=-17.4 else "HIGH") for x in t}
if len(bands)<3: print(f"  FAIL: starts cover only {bands}; need LOW, MID and HIGH."); ok=False
if not all(0.70<=x<=1.25 for x in a):
    print(f"  FAIL: amp outside L14 prior bounds [0.70,1.25]: {a} -> logpost would be -Inf"); ok=False
print(f"  starts OK: T_on {min(t):.2f}..{max(t):.2f} (spread {max(t)-min(t):.2f}), bands {sorted(bands)}, amp {min(a):.3f}..{max(a):.3f}")
sys.exit(0 if ok else 1)
PY

echo "L19: 4 chains x $NITER iter (seeds 2026-2029), amp ~ N(0.95, 0.10) [L14's],"
echo "     adcov=$ADCOV [L14's], T_on-DISPERSED starts from $STARTS, BLAS pinned"
for SEED in 2026 2027 2028 2029; do
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
    julia --project=julia_v2 --threads=1 julia/calibrate_mcmc_ext.jl "$NITER" "$SEED" \
        --tag=$TAG --gis-ordered --gis-basins2 --overdisperse --starts=$STARTS \
        --adcov=$ADCOV --amp-mu=0.95 --amp-sigma=0.10 \
        > "outputs/mcmc/log_${TAG}_seed${SEED}.txt" 2>&1 &
done
wait
echo "L19 chains done -> outputs/mcmc/chain_${TAG}_seed*.csv"
echo "VERIFY THE ARM (all four seeds):"
echo "  tr '\\r' '\\n' < outputs/mcmc/log_${TAG}_seed2026.txt | grep -m1 'A6 prior'   # N(0.950, 0.100)"
echo "  tr '\\r' '\\n' < outputs/mcmc/log_${TAG}_seed2026.txt | grep -m1 'starts file' # ..._ton.csv"
echo "  tr '\\r' '\\n' < outputs/mcmc/log_${TAG}_seed2026.txt | grep -m1 'logpost'     # FOUR DIFFERENT values"
echo "THEN, BEFORE ANYTHING ELSE — resolve the registered prediction:"
echo "  bash scripts/ton_band_by_chain.sh $TAG      # did chains MOVE from their start bands?"
echo "  and compare per-chain MEAN LOG-POSTERIOR by band (informative even if they never mix)"
