#!/usr/bin/env python3
"""
diag_l10_vs_l11_projection.py — what the D1+D2 change set does to the PROJECTION
deliverable, and the one parameter move that explains most of it.

The hindcast side is already scored (python/scope_l10_vs_l11_scorecard.py ->
outputs/scope_l10_vs_l11_scorecard.csv, bias and coverage against the targets).
This is the other half: the change set was adopted on hindcast grounds, so the
question it does not answer is what it does to projected sea level, which is the
thing the posterior is actually licensed to produce (handoff 15b, MAY/MAY NOT).

PART 1 — the deliverable delta. Per-component medians at 2100/2150/2300 for the
three SSPs, L10 vs L11, from outputs/ssps_components_2300_{L10,L11}.csv (same
2000 draws, same FaIR-mean forcing, same 1995-2014 baseline, so the difference
is the posterior and nothing else).

PART 2 — thermal_alpha, MIXING-GATED. te_sea_level is exactly te_s0 + te_α·S(t)
with S set by the OHC forcing alone and te_s0 = 0 (MimiBRICK v2.0.0 default, not
sampled), so the projected steric series is EXACTLY proportional to thermal_alpha
— a shift in α is the whole story for the te panel, with no confounder. The gate
is the one 22635dd established: a between-arm shift is only reportable if it
exceeds the worst between-CHAIN disagreement within either arm by MIX_RATIO_MIN.
Without it, a parameter the chains never agreed on reads as a finding.

The D1-only arm is quoted from 22635dd rather than recomputed: those chains
(chain_D1_seed*.csv) were deleted after that analysis; only the adapted
covariances and logs survive. Re-running D1 would mean 4 x 250k fresh chains.

  source ~/climate-env/bin/activate && python3 python/diag_l10_vs_l11_projection.py
Writes outputs/diag_l10_vs_l11_projection.csv
"""
import glob
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs/diag_l10_vs_l11_projection.csv")

ARMS = ("L10", "L11")
SSPS = ("SSP1-2.6", "SSP2-4.5", "SSP5-8.5")
HORIZONS = (2100, 2150, 2300)
COMPONENTS = ("glaciers", "gis", "ais", "te", "total")

# The mixing gate from 22635dd. A shift must clear the between-chain spread by
# this factor before it is a finding rather than an artefact of non-mixing.
MIX_RATIO_MIN = 2.0
CHAIN_STRIDE = 100                       # 2.29 GB chains; one column, post-burn
PARAM = "thermal_alpha"
# THE OPTIMUM IS METRIC-DEPENDENT, AND THE TWO POINT IN OPPOSITE DIRECTIONS.
# Both are produced by python/diag_te_weighted_and_seam.py, CHECK 2.
#
#   PRECISION-WEIGHTED 0.13950 — weights each year by the calibrator's own band
#     sigma, eps = max((hi-lo)/(2*1.645), 0.05). This IS what the likelihood
#     optimises, so it is the one to headline. Modern years have tiny bands and
#     therefore dominate; they want a LOWER alpha.
#   ZERO-MEAN-BIAS 0.17711 — the alpha that zeroes the unweighted full-window
#     bias. The early century, where the bands are wide and the weight is small,
#     wants a HIGHER alpha.
#
# L10 0.1503 sits BETWEEN them. So "alpha moved toward/away from the optimum" is
# meaningless without naming the metric: L10 -> L11 moves AWAY from the
# precision-weighted optimum and TOWARD the zero-mean-bias one. Reporting either
# alone is a directional claim that reverses under the other. This script prints
# both, and the era-split below is what actually reconciles them.
ALPHA_PRECISION_WEIGHTED = 0.13950
ALPHA_ZERO_MEAN_BIAS = 0.17711
# D1-only arm, recorded in 22635dd from 4 x 250k --drop-total chains, both arms
# tightly mixed. Quoted, not recomputed — see the module docstring.
ALPHA_D1 = (0.15023, 0.15205)


def per_chain_medians(tag, param, stride=CHAIN_STRIDE):
    """Post-burn median of `param` in each chain SEPARATELY — the only way to
    tell a real posterior shift from a parameter the chains have not agreed on."""
    out = {}
    for f in sorted(glob.glob(os.path.join(REPO, f"outputs/mcmc/chain_{tag}_seed*.csv"))):
        d = pd.read_csv(f, usecols=[param])
        out[os.path.basename(f).split("seed")[1][:4]] = float(d[param].iloc[len(d) // 2::stride].median())
    return out


def part1_deliverable_delta():
    proj = {t: pd.read_csv(os.path.join(REPO, f"outputs/ssps_components_2300_{t}.csv"))
            for t in ARMS}
    rows = []
    for ssp in SSPS:
        for y in HORIZONS:
            for c in COMPONENTS:
                r = {t: proj[t][(proj[t].ssp == ssp) & (proj[t].year == y)
                                & (proj[t].component == c)].iloc[0] for t in ARMS}
                rows.append(dict(ssp=ssp, year=y, component=c,
                                 med_L10=r["L10"].med, med_L11=r["L11"].med,
                                 delta=r["L11"].med - r["L10"].med,
                                 p17_L11=r["L11"].p17, p83_L11=r["L11"].p83))
    d = pd.DataFrame(rows)

    print("=" * 78)
    print("PART 1 — projected SLR, cm rel. 1995-2014, median (2000 draws, FaIR mean forcing)")
    print("=" * 78)
    for y in HORIZONS:
        print(f"\n@{y}   {'component':10s}" + "".join(f"{s:>22s}" for s in SSPS))
        for c in COMPONENTS:
            cells = []
            for ssp in SSPS:
                r = d[(d.ssp == ssp) & (d.year == y) & (d.component == c)].iloc[0]
                cells.append(f"{r.med_L10:7.2f} ->{r.med_L11:7.2f} ({r.delta:+5.2f})")
            print(f"      {c:10s}" + "".join(f"{x:>22s}" for x in cells))
    tot = d[(d.component == "total") & (d.year == 2100)]
    print(f"\n  TOTAL at 2100 moves {', '.join(f'{v:+.2f}' for v in tot.delta)} cm — "
          "near-neutral, while glaciers fall and steric rises underneath it.")
    return d


def part2_thermal_alpha():
    print("\n" + "=" * 78)
    print(f"PART 2 — {PARAM}, mixing-gated (te_sea_level is EXACTLY proportional to it)")
    print("=" * 78)
    chains = {t: per_chain_medians(t, PARAM) for t in ARMS}
    for t in ARMS:
        print(f"  {t} per-chain post-burn medians: "
              + ", ".join(f"{k} {v:.5f}" for k, v in chains[t].items()))

    sd = pd.read_csv(os.path.join(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_L10.csv"),
                     usecols=[PARAM])[PARAM].std()
    m = {t: float(np.median(list(chains[t].values()))) for t in ARMS}
    shift = m["L11"] - m["L10"]
    spread = max(max(v.values()) - min(v.values()) for v in chains.values())
    ratio = abs(shift) / spread if spread > 0 else np.inf
    verdict = "REPORTABLE" if ratio > MIX_RATIO_MIN else "NOT RESOLVED at this chain length"

    print(f"\n  L10 {m['L10']:.5f}  ->  L11 {m['L11']:.5f}   "
          f"shift {shift:+.5f} = {shift / sd:+.2f} L10 sd")
    print(f"  worst between-chain spread in either arm {spread:.5f}  ->  "
          f"MIX RATIO {ratio:.1f} (needs > {MIX_RATIO_MIN})  ->  {verdict}")

    d1_shift = ALPHA_D1[1] - ALPHA_D1[0]
    print(f"\n  ATTRIBUTION. D1 alone moved it {ALPHA_D1[0]:.5f} -> {ALPHA_D1[1]:.5f} "
          f"({d1_shift / sd:+.2f} L10 sd, 22635dd), i.e. {d1_shift / shift * 100:.0f}% "
          "of the L10->L11 move. The remainder is D2.")
    print("\n  DIRECTION — state the metric or the claim reverses:")
    for lbl, opt in (("precision-weighted (what the likelihood optimises)", ALPHA_PRECISION_WEIGHTED),
                     ("zero-mean-bias (unweighted level)", ALPHA_ZERO_MEAN_BIAS)):
        d10, d11 = abs(m["L10"] - opt), abs(m["L11"] - opt)
        print(f"    vs {opt:.5f}  {lbl}")
        print(f"      L10 {d10:.4f} away -> L11 {d11:.4f} away = {d11 / d10:.2f}x "
              f"{'FURTHER' if d11 > d10 else 'CLOSER'}")
    print("  L10 sits BETWEEN the two optima, so the change set moves alpha AWAY from\n"
          "  the precision-weighted optimum and TOWARD the zero-mean-bias one. That is\n"
          "  an ERA TRADE, and the scorecard shows the same thing on the residuals:\n"
          "  steric 1900-1919 bias 0.418 -> 0.162 and 1920-49 0.555 -> 0.348 (wide\n"
          "  bands, low weight) bought at 1993-2026 0.133 -> 0.216 with coverage\n"
          "  21.2% -> 15.2% (tiny bands, high weight). The projection is anchored on\n"
          "  the modern era, which is the era that got worse.")
    print("\n  The D2 steric basis is orthogonal to S(t) ITSELF, not merely to the\n"
          "  constant -- corrected 2026-08-14 after L11tune2 measured\n"
          "  corr(d2_steric_1, thermal_alpha) = -0.724 -- so delta CANNOT mimic a\n"
          "  rescaling of alpha in the plain inner product. But the likelihood metric\n"
          "  is the AR(1)-correlated heteroskedastic precision, in which that\n"
          "  orthogonality does NOT hold, and the calibrator says so in as many words.\n"
          "  So this is documented residual coupling, NOT a failed gate. What is open\n"
          "  is the MAGNITUDE, and which of the two D2 streams carries it.")
    return dict(param=PARAM, med_L10=m["L10"], med_L11=m["L11"], shift=shift,
                shift_in_L10_sd=shift / sd, chain_spread=spread, mix_ratio=ratio,
                verdict=verdict, d1_share=d1_shift / shift,
                opt_precision_weighted=ALPHA_PRECISION_WEIGHTED,
                opt_zero_mean_bias=ALPHA_ZERO_MEAN_BIAS)


if __name__ == "__main__":
    d = part1_deliverable_delta()
    alpha = part2_thermal_alpha()
    d.to_csv(OUT, index=False)
    pd.DataFrame([alpha]).to_csv(OUT.replace(".csv", "_thermal_alpha.csv"), index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)} and "
          f"{os.path.relpath(OUT.replace('.csv', '_thermal_alpha.csv'), REPO)}")
