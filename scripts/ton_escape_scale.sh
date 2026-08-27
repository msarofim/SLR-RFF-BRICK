#!/usr/bin/env bash
# ==============================================================================
# ton_escape_scale.sh — IS THE T_on BARRIER REAL, OR IS THE PROPOSAL JUST SLOW?
#
# WHY THIS EXISTS. ton_transition_rates.sh answered Priority 3 of handoff -26b, but the
# answer was that THE HAZARD FRAMING HAS NO POWER: out-of-MID time is ONE absorbing event
# per affected chain (L17/2028 = 98.2% of its out-time in a single excursion; L16/2026 =
# 93.2%), not many blocked returns. Excluding each chain's longest run, L16 and L17 have
# INDISTINGUISHABLE excursion lengths (~25-45 draws of boundary jitter). So "exit hazard"
# and "return hazard" are both N=1 estimates and cannot discriminate (`no_power_null`,
# `two_statistics_can_be_blind`).
#
# THIS TEST HAS POWER because it uses every post-burn draw (~1e6/chain), not 2 events.
#
# THE IDEA. If a chain sits at distance D outside the MID edge and its accepted T_on moves
# have per-move variance s^2 at move-rate p, then a DRIFTLESS random walk returns in about
#     T_diffusive = D^2 / (p * s^2)   draws.
# Compare that to the OBSERVED longest excursion:
#     observed >> diffusive  =>  a RESTORING FORCE holds the chain out — a REAL barrier /
#                                genuine second mode, not a sampler artifact.
#     observed ~  diffusive  =>  no barrier; the chain is simply diffusing slowly and the
#                                "modes" are a proposal-scale problem, fixable by tuning.
#
# ⚠ WHAT IT CANNOT DO. T_diffusive is a LOWER BOUND on the true return time: it assumes no
# drift and no restoring force, which is exactly the null it tests against. It also assumes
# the step distribution is roughly homogeneous across the excursion. And the chain files
# store ACCEPTED states only — rejected proposals are invisible, so `p` is the observed move
# rate for THIS parameter, not the sampler's global acceptance (0.234).
#
# ⚠ s is measured as RMS over MOVES ONLY (d != 0). The second moment is what enters a
# diffusion coefficient; mean|d| is printed beside it because RMS is outlier-sensitive and a
# large gap between the two means the step distribution is heavy-tailed and the diffusive
# estimate is optimistic.
#
# ⚠ Steps are measured OUT OF MID ONLY. In-MID steps are drawn from a different local
# geometry and would not describe the return journey.
#
# Burn-in = FIRST HALF. Bands = scope_ais_ton_band_hindcast.jl's KDE valley floors, kept in
# sync with ton_band_by_chain.sh / ton_transition_rates.sh.  `nameless_matrix_order`: the
# column is resolved BY NAME from each file's own header and the index is printed.
#
#   bash scripts/ton_escape_scale.sh [TAG ...]     (default: L16 L17)
# ==============================================================================
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EDGE_LOW=-18.5
EDGE_HIGH=-17.4
PARAM=ais_runoff_Ton
if [ "$#" -gt 0 ]; then TAGS=("$@"); else TAGS=(L16 L17); fi

printf '%s ESCAPE SCALE | LOW<=%s MID(%s,%s] HIGH>%s | every post-burn draw, OUT-OF-MID steps only\n' \
       "$PARAM" "$EDGE_LOW" "$EDGE_LOW" "$EDGE_HIGH" "$EDGE_HIGH"
printf '  T_diff = D^2/(p*s^2) is a LOWER BOUND on return time (no drift, no restoring force).\n'
printf '  observed_longest >> T_diff  =>  REAL BARRIER.   observed ~ T_diff  =>  just slow diffusion.\n\n'
for tag in "${TAGS[@]}"; do
  for f in "$REPO"/outputs/mcmc/chain_${tag}_seed*_n*.csv; do
    [ -e "$f" ] || continue
    base=$(basename "$f")
    idx=$(head -1 "$f" | tr ',' '\n' | grep -n "^${PARAM}\$" | cut -d: -f1)
    if [ -z "$idx" ]; then echo "  $base: NO COLUMN $PARAM — skipped"; continue; fi
    ndraw=$(printf '%s' "$base" | sed -E 's/.*_n([0-9]+)\.csv/\1/')
    if ! printf '%s' "$ndraw" | grep -qE '^[0-9]+$'; then echo "  $base: cannot parse _n<N> — skipped"; continue; fi
    cut -d, -f"$idx" "$f" | awk -v lo_e="$EDGE_LOW" -v hi_e="$EDGE_HIGH" \
        -v burn="$((ndraw/2))" -v nm="$base" -v col="$idx" '
      function abs(x){ return x<0 ? -x : x }
      NR == 1 { next }
      { i++ }
      i <= burn { prevv = $1+0; have = 1; prevout = 0; next }
      {
        v = $1 + 0
        if (!have) { prevv = v; have = 1; next }
        d = v - prevv
        isout = (v <= lo_e || v > hi_e)
        if (isout) {
          nout++
          dist = (v <= lo_e) ? (lo_e - v) : (v - hi_e)
          sdist += dist; if (dist > maxdist) maxdist = dist
          # ONLY steps with BOTH ends out of MID describe the return journey. The step that
          # CROSSES the edge is the exit jump, not a step of the walk back, and including it
          # inflated the RMS 17x on the synthetic (one 1.7-wide crossing among 104 moves of
          # 0.01). Caught by the mutation test — `mutation_test_gates`.
          if (prevout) {
            nstep++
            if (d != 0) { nmove++; s2 += d*d; sabs += abs(d) }
          }
          # track current excursion length to report the longest
          runlen++
          if (runlen > maxrun) maxrun = runlen
        } else { runlen = 0 }
        prevout = isout
        prevv = v
      }
      END {
        if (nout == 0) { printf "  %-42s col %d  NEVER OUT OF MID — no escape scale to measure\n", nm, col; exit }
        if (nstep == 0 || nmove == 0) {
          printf "  %-42s col %d  out-draws %d — NO within-excursion moves; escape scale UNDEFINED\n", nm, col, nout; exit
        }
        p    = nmove / nstep
        rms  = sqrt(s2 / nmove)
        mabs = sabs / nmove
        Dmean = sdist / nout
        tdif  = (p>0 && rms>0) ? (Dmean*Dmean)/(p*rms*rms) : -1
        printf "  %-42s col %d  out-draws %d\n", nm, col, nout
        printf "      move rate p %.4f   step RMS s %.3e   mean|d| %.3e   (RMS/mean %.2f)\n", p, rms, mabs, rms/mabs
        printf "      distance out of MID:  mean D %.4f   max %.4f\n", Dmean, maxdist
        if (tdif > 0)
          printf "      T_diffusive %12.0f draws   observed longest %d   ratio obs/diff %8.1fx\n",
                 tdif, maxrun, maxrun/tdif
        else
          printf "      T_diffusive UNDEFINED (no accepted moves out of MID — chain FROZEN there)\n"
      }'
  done
done
