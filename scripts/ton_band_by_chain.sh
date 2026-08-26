#!/usr/bin/env bash
# ==============================================================================
# ton_band_by_chain.sh — PER-CHAIN T_on band occupancy, straight off the raw chains.
#
# WHY THIS EXISTS. scope_ais_ton_band_hindcast.jl scores the POOLED subsample, so a
# pooled "24% LOW" is ambiguous between (a) all four chains wandering 24% of the time
# and (b) one chain of four absorbed in LOW and never returning. Those have opposite
# implications for whether the proposal or the geometry is at fault. This splits it.
#
# It is deliberately INDEPENDENT of the Julia path (raw CSV + awk, no Mimi, no
# subsample file), so agreement between the two is a real cross-check rather than a
# restatement. Pooled fractions reconstruct as the mean over chains.
#
# `nameless_matrix_order` discipline: the T_on column index is looked up BY NAME in
# each file's own header, never hardcoded, and the resolved index is printed.
#
# Burn-in is the FIRST HALF, matching postprocess_mcmc_ext.jl. The draw count comes
# from the `_n<N>` filename field, so no second full pass over a 2.3 GB file.
#
# Bands are scope_ais_ton_band_hindcast.jl's KDE valley floors — keep in sync:
#   LOW <= -18.5 | MID (-18.5, -17.4] | HIGH > -17.4
#
#   bash scripts/ton_band_by_chain.sh [TAG ...]     (default: L16 L17)
# ==============================================================================
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EDGE_LOW=-18.5
EDGE_HIGH=-17.4
STRIDE=500          # every Nth post-burn draw
PARAM=ais_runoff_Ton
if [ "$#" -gt 0 ]; then TAGS=("$@"); else TAGS=(L16 L17); fi

printf '%s band occupancy per chain | bands LOW<=%s MID(%s,%s] HIGH>%s | every %dth post-burn draw\n' \
       "$PARAM" "$EDGE_LOW" "$EDGE_LOW" "$EDGE_HIGH" "$EDGE_HIGH" "$STRIDE"
for tag in "${TAGS[@]}"; do
  for f in "$REPO"/outputs/mcmc/chain_${tag}_seed*_n*.csv; do
    [ -e "$f" ] || continue
    base=$(basename "$f")
    idx=$(head -1 "$f" | tr ',' '\n' | grep -n "^${PARAM}\$" | cut -d: -f1)
    if [ -z "$idx" ]; then echo "  $base: NO COLUMN $PARAM — skipped"; continue; fi
    ndraw=$(printf '%s' "$base" | sed -E 's/.*_n([0-9]+)\.csv/\1/')
    if ! printf '%s' "$ndraw" | grep -qE '^[0-9]+$'; then echo "  $base: cannot parse _n<N> — skipped"; continue; fi
    awk -F, -v c="$idx" -v lo_e="$EDGE_LOW" -v hi_e="$EDGE_HIGH" -v st="$STRIDE" \
        -v burn="$((ndraw/2))" -v nm="$base" '
      NR > burn+1 && (NR-1-burn) % st == 0 {
        v=$c+0; n++
        if (v<=lo_e) lo++; else if (v<=hi_e) mid++; else hi++
        s+=v; if (n==1||v<mn) mn=v; if (n==1||v>mx) mx=v
      }
      END {
        if (n==0) { printf "  %-42s NO POST-BURN ROWS\n", nm; exit }
        printf "  %-42s n=%5d  LOW %5.1f%%  MID %5.1f%%  HIGH %5.1f%%   mean %7.2f  min %7.2f  max %7.2f  (col %d)\n",
               nm, n, 100*lo/n, 100*mid/n, 100*hi/n, s/n, mn, mx, c
      }' "$f"
  done
done
