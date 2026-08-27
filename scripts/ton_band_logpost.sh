#!/usr/bin/env bash
# ==============================================================================
# ton_band_logpost.sh — WHICH T_on BAND DOES THE CURRENT OBJECTIVE PREFER?
#
# WHY THIS EXISTS. Every previous band comparison was made on draws taken from a SINGLE
# contaminated chain, so "the LOW draws score worse" conflated the band with the fact that
# the chain was passing through on an excursion. L19 starts one chain in each band, so each
# chain equilibrates in its OWN band and the comparison is between EQUILIBRATED chains.
#
# It also survives the outcome we EXPECT. If the barrier is real (ton_escape_scale.sh says
# it is: 3.5-28.5x the driftless null) the chains will NOT mix, R-hat will be meaningless,
# and the ensemble is not a posterior — but each chain is still a valid sample of ITS band,
# so the per-band log-posterior comparison is exactly what a non-mixing run CAN deliver.
#
# ⚠⚠ WHAT THIS DOES *NOT* MEASURE: POSTERIOR MASS. Mean log-posterior is a comparison of
# TYPICAL DENSITY, not of the probability mass in each mode. A narrow, tall mode can have a
# higher mean log-density and far less mass than a broad, low one; mass needs the volume too
# (thermodynamic integration / stepping-stone), which this does not attempt. So a band that
# wins here is "where the density is highest", NOT "where the posterior probability is".
# Quote it that way or not at all.
#
# ⚠ The comparison is only as good as the equilibration. A chain still burning in reports a
# rising log_post; the split-half drift column below is the check — if the two halves of the
# post-burn segment disagree by more than a few log units, that chain has NOT settled and its
# number is not usable.
#
# Burn-in = FIRST HALF, matching postprocess_mcmc_ext.jl. Columns resolved BY NAME
# (`nameless_matrix_order`). Bands = scope_ais_ton_band_hindcast.jl's KDE valley floors.
#
#   bash scripts/ton_band_logpost.sh [TAG ...]      (default: L19)
# ==============================================================================
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EDGE_LOW=-18.5
EDGE_HIGH=-17.4
TANT0=-18.434554692169755      # = -15.42/0.8365, the preserved T_ant(GMST=0) anchor
if [ "$#" -gt 0 ]; then TAGS=("$@"); else TAGS=(L19); fi

printf 'per-chain EQUILIBRATED log-posterior by T_on band | LOW<=%s MID(%s,%s] HIGH>%s\n' \
       "$EDGE_LOW" "$EDGE_LOW" "$EDGE_HIGH" "$EDGE_HIGH"
printf '⚠ mean log-density, NOT posterior mass. GMST onset = (T_on - %.3f)/amp.\n\n' "$TANT0"
printf '  %-34s %6s %8s %10s %10s %10s %9s\n' chain band %occ "mean lp" "sd lp" "drift(2nd-1st)" "GMSTonset"
for tag in "${TAGS[@]}"; do
  for f in "$REPO"/outputs/mcmc/chain_${tag}_seed*_n*.csv; do
    [ -e "$f" ] || continue
    base=$(basename "$f")
    hdr=$(head -1 "$f")
    it=$(printf '%s' "$hdr" | tr ',' '\n' | grep -n "^ais_runoff_Ton$" | cut -d: -f1)
    ia=$(printf '%s' "$hdr" | tr ',' '\n' | grep -n "^ais_gmst_amp$"   | cut -d: -f1)
    il=$(printf '%s' "$hdr" | tr ',' '\n' | grep -n "^log_post$"       | cut -d: -f1)
    if [ -z "$it" ] || [ -z "$ia" ] || [ -z "$il" ]; then
      echo "  $base: missing one of ais_runoff_Ton/ais_gmst_amp/log_post — skipped"; continue; fi
    ndraw=$(printf '%s' "$base" | sed -E 's/.*_n([0-9]+)\.csv/\1/')
    cut -d, -f"${it},${ia},${il}" "$f" | awk -F, -v lo_e="$EDGE_LOW" -v hi_e="$EDGE_HIGH" \
        -v burn="$((ndraw/2))" -v nm="$base" -v tant0="$TANT0" '
      NR==1{next} {i++} i<=burn{next}
      {
        t=$1+0; a=$2+0; lp=$3+0
        b = (t<=lo_e) ? "LOW" : (t<=hi_e ? "MID" : "HIGH")
        n[b]++; s[b]+=lp; ss[b]+=lp*lp; g[b]+=(t-tant0)/a
        tot++
        # split-half drift on the WHOLE post-burn segment: is this chain equilibrated?
        if (!half) half = int((ndraw-burn)/2)
        if (tot<=half) {h1+=lp; n1++} else {h2+=lp; n2++}
      }
      END{
        drift = (n1>0 && n2>0) ? h2/n2 - h1/n1 : 0
        first=1
        for (b in n) {
          m=s[b]/n[b]; v=ss[b]/n[b]-m*m; sd=(v>0)?sqrt(v):0
          printf "  %-34s %6s %7.1f%% %10.2f %10.2f %10.2f %9.2f\n",
                 (first?nm:""), b, 100*n[b]/tot, m, sd, (first?drift:0), g[b]/n[b]
          first=0
        }
      }' ndraw="$ndraw"
  done
done
echo
echo "READ IT LIKE THIS:"
echo "  chains STAY in their start bands  -> the barrier is real; L14's 100% MID is START-DETERMINED"
echo "  chains all MIGRATE to MID          -> MID genuinely favoured; champion CONFIRMED"
echo "  the MID CONTROL (seed 2029) LEAVES -> MID not favoured under the CURRENT targets"
echo "  |drift| more than a few log units  -> that chain has NOT equilibrated; its mean is not usable"
