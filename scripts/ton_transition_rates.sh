#!/usr/bin/env bash
# ==============================================================================
# ton_transition_rates.sh — EXIT vs RETURN structure of the T_on excursions.
#
# THE QUESTION (handoff 2026-08-26b §1, Priority 3). L17's mode-local proposal made
# `ais_runoff_Ton` mixing WORSE (R-hat 1.184 -> 2.264, out-of-MID 13.5% -> 36.9%), which
# inverts the arm's own premise that "a mode-local proposal makes staying EASIER by
# construction". The registered hypothesis for why: THE TIGHT PROPOSAL BLOCKS RETURNS,
# NOT EXITS. This script is the free discriminator on the existing chains.
#
# ⚠ EXITS AND RETURNS ARE NOT INDEPENDENT COUNTS. A chain alternates in/out, so
# |exits - returns| <= 1 ALWAYS. Comparing their COUNTS is vacuous. What separates the
# hypotheses is (a) HOW MANY distinct excursions there are and (b) HOW LONG each lasts:
#   blocked returns  => FEW excursions, each LONG   (the limit is absorption: 1 exit, 0 returns)
#   easy exits       => MANY excursions, each SHORT (a chain that crosses and comes back)
# So the reported statistic is the excursion COUNT and the MEAN/MAX SOJOURN, and the rates
# are printed with their DENOMINATORS attached (`no_power_null`: a rate on n=1 excursion is
# not a rate, and must be visible as such).
#
# ⚠ NO STRIDE. Transitions require CONSECUTIVE draws. ton_band_by_chain.sh strides by 500
# for occupancy, which is correct there and would destroy every transition here. The chains
# are stored unthinned (one row per iteration), so consecutive rows are genuine MH steps and
# a repeated row is a REJECTED proposal, not a duplicate record.
#
# Burn-in is the FIRST HALF, matching postprocess_mcmc_ext.jl and ton_band_by_chain.sh.
# `nameless_matrix_order`: the column index is looked up BY NAME in each file's own header
# and printed. Bands are scope_ais_ton_band_hindcast.jl's KDE valley floors — keep in sync
# with ton_band_by_chain.sh:  LOW <= -18.5 | MID (-18.5, -17.4] | HIGH > -17.4
#
#   bash scripts/ton_transition_rates.sh [TAG ...]     (default: L16 L17)
# ==============================================================================
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EDGE_LOW=-18.5
EDGE_HIGH=-17.4
PARAM=ais_runoff_Ton
if [ "$#" -gt 0 ]; then TAGS=("$@"); else TAGS=(L16 L17); fi

printf '%s MID-excursion structure | LOW<=%s MID(%s,%s] HIGH>%s | EVERY post-burn draw (no stride)\n' \
       "$PARAM" "$EDGE_LOW" "$EDGE_LOW" "$EDGE_HIGH" "$EDGE_HIGH"
printf '  exits=MID->out  returns=out->MID  (|exits-returns|<=1 BY CONSTRUCTION — read the SOJOURNS)\n\n'
for tag in "${TAGS[@]}"; do
  for f in "$REPO"/outputs/mcmc/chain_${tag}_seed*_n*.csv; do
    [ -e "$f" ] || continue
    base=$(basename "$f")
    idx=$(head -1 "$f" | tr ',' '\n' | grep -n "^${PARAM}\$" | cut -d: -f1)
    if [ -z "$idx" ]; then echo "  $base: NO COLUMN $PARAM — skipped"; continue; fi
    ndraw=$(printf '%s' "$base" | sed -E 's/.*_n([0-9]+)\.csv/\1/')
    if ! printf '%s' "$ndraw" | grep -qE '^[0-9]+$'; then echo "  $base: cannot parse _n<N> — skipped"; continue; fi
    # cut a single column first: awk -F, over 59 fields x 2M rows is ~10x this.
    cut -d, -f"$idx" "$f" | awk -v lo_e="$EDGE_LOW" -v hi_e="$EDGE_HIGH" \
        -v burn="$((ndraw/2))" -v nm="$base" -v col="$idx" '
      NR == 1 { next }                       # header
      { i++ }                                # draw index, 1-based
      i <= burn { next }
      {
        v = $1 + 0
        b = (v <= lo_e) ? "L" : (v <= hi_e ? "M" : "H")
        n++
        if (b == "M") { nmid++ } else { nout++; if (b=="L") nlow++; else nhigh++ }
        if (n == 1) { prev = b; runlen = 1; next }
        if (b == prev) { runlen++ }
        else {
          if (prev == "M" && b != "M") { exits++; if (runlen > maxmid) maxmid = runlen }
          if (prev != "M" && b == "M") { returns++; nexc++; if (runlen > maxexc) maxexc = runlen }
          runlen = 1
        }
        prev = b
      }
      END {
        if (n == 0) { printf "  %-42s NO POST-BURN ROWS\n", nm; exit }
        # a trailing out-of-MID run never returns: count it as an excursion that is still open
        openexc = (prev != "M") ? 1 : 0
        if (openexc && runlen > maxexc) maxexc = runlen
        if (!openexc && runlen > maxmid) maxmid = runlen   # trailing MID run is censored too
        totexc = nexc + openexc
        printf "  %-42s col %d  n=%d\n", nm, col, n
        printf "      occupancy   MID %5.1f%% (%d)   LOW %5.1f%% (%d)   HIGH %5.1f%% (%d)\n",
               100*nmid/n, nmid, 100*nlow/n, nlow, 100*nhigh/n, nhigh
        printf "      transitions exits %d   returns %d   excursions %d (%d still open at chain end)\n",
               exits+0, returns+0, totexc, openexc
        if (nmid > 0)   printf "      exit hazard   %8.2f per 1e6 MID-draws   (%d exits / %d MID-draws)\n",
                               1e6*exits/nmid, exits+0, nmid
        else            printf "      exit hazard   UNDEFINED — 0 MID-draws\n"
        if (nout > 0)   printf "      return hazard %8.2f per 1e6 out-draws   (%d returns / %d out-draws)\n",
                               1e6*returns/nout, returns+0, nout
        else            printf "      return hazard UNDEFINED — 0 out-of-MID draws\n"
        if (totexc > 0) printf "      mean excursion %10.0f draws   longest %d\n", nout/totexc, maxexc+0
        else            printf "      mean excursion  n/a — chain never left MID (exit hazard has NO POWER here)\n"
        if (exits+0 > 0) printf "      mean MID sojourn %8.0f draws   longest %d\n", nmid/(exits+0), maxmid+0
        else             printf "      mean MID sojourn n/a — chain never left MID\n"
      }'
  done
done
