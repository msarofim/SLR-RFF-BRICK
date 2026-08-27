#!/bin/bash
## L20 production: 4 RAM chains (seeds 2026-2029). THE SIGMA ARM — option B.
##
## WHAT CHANGED vs L18 — EXACTLY ONE THING: --amp-sigma 0.180 -> 0.10.
## Centre stays 1.09. Proposal stays adapted_cov_L15pool_seed2026.csv. Starts stay L14/L18's
## outputs/mcmc/overdispersed_starts.csv (canonical, unrebuilt). Targets, --gis-ordered,
## --gis-basins2, 2M iters all unchanged. Bounds follow the file's mu+-3sigma rule:
## [0.55, 1.63] -> [0.79, 1.39].
##
## SO THE THREE-WAY COMPARISON IS FULLY CONTROLLED, EACH PAIR DIFFERING IN ONE THING:
##   L14 N(0.95, 0.10)  vs L20 N(1.09, 0.10)   -> the CENTRE, sigma and starts held
##   L18 N(1.09, 0.180) vs L20 N(1.09, 0.10)   -> the SIGMA, centre and starts held
## L14, L18 and L20 all run --overdisperse on the SAME four start points.
##
## WHY 0.10 AND NOT 0.180 (revisited 2026-08-27, Marcus asked for the sigma to be re-derived
## rather than inherited). Three grounds:
##
##  1. IT BRACKETS WHAT HAS ACTUALLY BEEN MEASURED, AND 0.180 DOES NOT DISCRIMINATE. Every
##     measured central estimate of amp, across all frames and warming levels, spans
##     0.875 .. 1.196:
##        0.875 STATE curve @0.6-0.8K | 0.920/0.980 Xie polar-cap cap60 ssp245/585
##        1.095 CMIP6 secant 34-model | 1.097 DECK 1pctCO2 41-model | 1.100 STATE @1.5-2K
##        1.130/1.160 LAND-only PAI1 34-model ssp245/585 (DAIS's OWN frame)
##        1.175 STATE @2-4K | 1.196 paleo equilibrium (stock DAIS)
##     N(1.09, 0.10) bounds [0.79, 1.39] = 1.9x that span. N(1.09, 0.180) bounds [0.55, 1.63]
##     = 3.4x it, so roughly half the prior mass sits where NOTHING has ever been measured.
##
##  2. SIGMA IS THE PROJECTION BAND, BECAUSE amp IS UNIDENTIFIED. Posterior sd / truncated
##     prior sd = 0.992 (L14), 1.015 (L15), 1.002 (L16), 1.002 (L18) — NO shrinkage in ANY
##     arm, so the posterior IS the prior and sigma passes straight through. Measured cost of
##     0.180: AIS p05-p95 at ssp126@2100 goes 6.91 -> 47.81 cm (6.9x), @2150 5.7x, and
##     spread_vs_lit at ssp126@2100 = 2.265 FAIL against L14's 0.327.
##
##  3. 0.180 IS THE SPREAD OF A DIFFERENT OBJECT. It is the between-model sd of the CMIP6
##     SECANT ensemble, and there are THREE documented frame mismatches between that and
##     DAIS's amp (polar-cap-vs-land; trend-vs-secant; paleo-pair-vs-CMIP6-transient,
##     CHANGELOG "TEST 3"). Importing its dispersion wholesale imports the wrong dispersion.
##
## ⚠⚠ WHAT THIS ARM DOES NOT FIX, AND MUST NOT BE READ AS FIXING.
##  [FRAME] DAIS's temperature lineage is ice-core/CONTINENTAL. Xie's 0.95 reproduces only
##     under a polar-cap mask INCLUDING the Southern Ocean (cap60 0.92/0.98). The land-only
##     34-model PAI1 is 1.13 (ssp245) / 1.16 (ssp585). So the frame-correct CENTRE may be
##     ~1.13-1.16, NOT 1.09 — L20 does not test that, and choosing 1.09 here is a compromise,
##     not a frame correction. A separate centre arm would be needed.
##  [STATE] amp is WARMING-LEVEL CONTROLLED, not constant: ~0.875 at 0.6-0.8 K, ~1.10 at
##     1.5-2 K, ~1.175 at 2-4 K. A constant amp is wrong in SHAPE, not just level. This is
##     almost certainly WHY the historical record prefers ~0.95 (the calibration window is
##     the LOW-warming end of that curve) while projections run at the HIGH end. L20 does not
##     resolve it; a state-dependent amp law would. `scope_ais_amp_law_form` measured that a
##     state-dependent law encodes a trend the data do not have — re-read it before trying.
##
## FALSIFIABLE PREDICTION, registered before the run:
##   amp is unidentified, so EXPECT posterior sd ~ 0.097 (0.10 x the 0.9707 truncation factor)
##   and posterior mean ~1.07-1.09. The informative parts are:
##   (i)  DOES THE ssp126 BAND COME BACK? Expect AIS p05-p95 @2100 near L14's 6.91 cm rather
##        than L18's 47.81, and spread_vs_lit back under the FAIL line.
##   (ii) DOES THE MEDIAN STAY PUT? If L20's median_vs_lit tracks L18's, the centre alone
##        drives the median and sigma only drives the band — the two are separable and can be
##        chosen independently. If the median ALSO moves toward L14, they are not.
##   (iii) DOES IT STAY IN MID? L19 showed bands are start-determined and these starts are
##        all-MID, so 100% MID is expected BY CONSTRUCTION and is NOT evidence (no_power_null).
##   (iv) sd(medians)/mean(sd_wc) @2100 vs L14's 0.051 and L18's 0.134 — same starts, so this
##        is the like-for-like convergence comparison.
##
## ⚠ BLAS PINNED. ⚠ CHECK uptime/swap AND READ THE ETA AT ~5 MIN (eta_in_days_is_not_a_slow_run).
##
##   bash run_mcmc_L20.sh [n_iter]        # default 2000000
set -e
cd "$(dirname "$0")"
NITER="${1:-2000000}"
TAG="${TAG:-L20}"
ADCOV=adapted_cov_L15pool_seed2026.csv
AMP_SIGMA=0.10
STARTS=outputs/mcmc/overdispersed_starts.csv
mkdir -p outputs/mcmc
[[ -f "$STARTS" ]] || { echo "MISSING $STARTS"; exit 1; }
# The bounds TIGHTEN from [0.55,1.63] to [0.79,1.39] when sigma drops. A start outside the new
# bounds gives logposterior = -Inf and a frozen chain. L18's starts carry amp 0.8275..1.0945,
# the lowest only 0.037 above the new floor — close enough to be worth an explicit gate.
python3 - "$STARTS" <<'PY' || exit 1
import csv,sys
a=[float(r['ais_gmst_amp']) for r in csv.DictReader(open(sys.argv[1]))]
lo,hi=1.09-3*0.10, 1.09+3*0.10
bad=[x for x in a if not (lo<=x<=hi)]
print(f"  starts amp {min(a):.4f}..{max(a):.4f} vs L20 bounds [{lo:.2f},{hi:.2f}] -> "
      + ("OK" if not bad else f"FAIL, outside: {bad} (logpost would be -Inf)"))
sys.exit(1 if bad else 0)
PY
echo "L20: 4 chains x $NITER iter (seeds 2026-2029), amp ~ N(1.09, $AMP_SIGMA), adcov=$ADCOV,"
echo "     OVERDISPERSED starts from $STARTS (L14/L18's, unrebuilt), BLAS pinned"
for SEED in 2026 2027 2028 2029; do
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
    julia --project=julia_v2 --threads=1 julia/calibrate_mcmc_ext.jl "$NITER" "$SEED" \
        --tag=$TAG --gis-ordered --gis-basins2 --overdisperse \
        --adcov=$ADCOV --amp-sigma=$AMP_SIGMA \
        > "outputs/mcmc/log_${TAG}_seed${SEED}.txt" 2>&1 &
done
wait
echo "L20 chains done. VERIFY: 'A6 prior' must read N(1.090, 0.100) on [0.790, 1.390]"
echo "  and [MAP start] must equal L18's -644.51 ONLY IF sigma did not change the prior density"
echo "  at the MAP — it DID, so expect a small offset. The four starts must be DISTINCT."
