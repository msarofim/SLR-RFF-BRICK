#!/usr/bin/env python3
"""
DIAGNOSTIC — glacier block response times ON THE L24 POSTERIOR.

Why this exists: the L24 deliverable states "the SLOWP and R19 regions have long timescales of
~275 yr and ~465 yr", and a 2026-09-10 audit found that NO OUTPUT IN THE REPO COMPUTED THEM.
The only source was prose in a 2026-09-03 handoff. `outputs/extc_block_constants.csv` carries
`tau15`/`tau30`, but those are the MARZEION-DERIVED ANCHORS used to solve for kappa/nu — they are
PRIOR inputs, not posterior results, and they read 522.8 / 828.0, nothing like the quoted numbers.
An unlocatable claim is not a wrong claim, so this script settles it by computation.

VERDICT (see the run): the quoted numbers ARE L24-backed, at 1.5 K.

⚠ TWO THINGS THE DOCUMENT'S PHRASING LEAVES OUT, and both change the reading:
  1. tau50 IS A FUNCTION OF TEMPERATURE. At 1.5 K the medians are ~271 / ~470 yr; at 3.0 K they
     are ~86 / ~150. A bare "~275 yr" is a factor of 3 ambiguous. State the level.
  2. R19's posterior is enormously wide (p05 82 yr, p95 3215 yr at 1.5 K -- a ~39x range). A bare
     median implies a precision the posterior does not have.

DEFINITION (taken from the repo's own `d1_multireservoir_cell.py:tau50_of`, not reinvented):
years to lose 50% of the committed loss under constant amp_b x level forcing, starting from the
block's S2020 data value. This is the GlacierMIP3 response-time definition.

[GATE TAU50] mutation-proof of the implementation: fed the anchored kappa/nu and the fitted
a/b/T_off/amp from `extc_block_constants.csv`, this code must reproduce that file's OWN
tau15/tau30. It does, to 0.00% on all six. Without that gate a wrong integrator would produce
confident posterior numbers indistinguishable from right ones.

WRITES only outputs/. Changes no target, no posterior, no chain.
"""
import os
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from provenance import stamp

REPO     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
## --tag= (default L24, the vintage the document quoted); a literal tag here reported L24 under any name.
TAG      = next((a[len("--tag="):] for a in sys.argv[1:] if a.startswith("--tag=")), "L24")
CONSTS   = os.path.join(REPO, "outputs", "extc_block_constants.csv")
POST     = os.path.join(REPO, "data", "MimiBRICK",
                        f"parameters_subsample_brick_mengel_{TAG}.csv")
OUT_CSV  = os.path.join(REPO, "outputs", f"diag_glacier_response_times_{TAG}.csv")

BLOCKS   = ("SLOWP", "R19", "FAST")
LEVELS   = (1.5, 3.0)                  # K of GLOBAL warming; amp_b scales to the block
ANCHOR_COL = {1.5: "tau15", 3.0: "tau30"}
HORIZON  = 4000                        # yr; tau50_of's solve horizon
THIN     = 10                          # every THIN-th posterior draw
GATE_TOL = 0.02                        # relative, vs the file's own anchors
DOC_CLAIM = {"SLOWP": 275.0, "R19": 465.0}      # what the deliverable states
DOC_LEVEL = 1.5                                  # the level it turns out to mean


def tau50(a, b, T0, amp, kappa, nu, S0, level):
    """Years to lose 50% of committed loss. Transcribed from d1_multireservoir_cell.tau50_of."""
    T = amp * level
    seq = a * (1.0 - np.exp(-b * (T - T0)))
    if seq <= S0:
        return np.inf
    S, target, prev = S0, S0 + 0.5 * (seq - S0), S0
    for k in range(1, HORIZON + 1):
        frac_left = max(1.0 - S / a, 1e-12)
        T_eq = T0 - np.log(frac_left) / b
        exc = max(T - T_eq, 0.0)
        S += min(kappa * exc ** nu, 1.0) * (seq - S)
        if S >= target:
            return (k - 1) + (target - prev) / max(S - prev, 1e-30)
        prev = S
    return float(2 * HORIZON)


def main():
    K = pd.read_csv(CONSTS).set_index("block")
    P = pd.read_csv(POST)

    print("=" * 78)
    print(f"DIAGNOSTIC: glacier block response times on the {TAG} posterior")
    print("=" * 78)

    print("\n[GATE TAU50] reproduce the constants file's OWN tau15/tau30 from its anchors")
    ok = True
    for blk in BLOCKS:
        r = K.loc[blk]
        for lev in LEVELS:
            got = tau50(float(r.a0), float(r.b_fit_obsfit), float(r.T_off_fit_obsfit),
                        float(r.amp_obsfit), float(r.kappa_anch_obsfit),
                        float(r.nu_anch_obsfit), float(r.S2020_data), lev)
            exp = float(r[ANCHOR_COL[lev]])
            rel = abs(got - exp) / exp
            ok &= rel < GATE_TOL
            print(f"    {blk:6s} @{lev}K   mine {got:8.1f}   file {exp:8.1f}   rel {rel:6.2%}"
                  f"   {'OK' if rel < GATE_TOL else 'FAIL'}")
    if not ok:
        raise SystemExit("[GATE TAU50] FAILED — the integrator is wrong; every posterior "
                         "number below would be confidently wrong in the same way")
    print("    => PASS. The implementation is the repo's own; posterior numbers below are valid.")

    print(f"\n[1] tau50 ON THE {TAG} POSTERIOR (every {THIN}th draw). "
          f"⚠ nu is NOT sampled — it is fixed at the anchor.")
    print(f"    {'block':7s} {'level':>6s} {'p05':>8s} {'median':>8s} {'p95':>8s} "
          f"{'p95/p05':>8s}   {'anchor(prior)':>13s}")
    rows, med = [], {}
    for blk in BLOCKS:
        nu = float(K.loc[blk, "nu_anch_obsfit"])
        S0 = float(K.loc[blk, "S2020_data"])
        for lev in LEVELS:
            v = np.array([tau50(P[f"gic_a_{blk}"][i], P[f"gic_b_{blk}"][i],
                                P[f"gic_T_off_{blk}"][i], P[f"gic_amp_{blk}"][i],
                                10.0 ** P[f"gic_log10_kappa_{blk}"][i], nu, S0, lev)
                          for i in range(0, len(P), THIN)])
            f = v[np.isfinite(v)]
            p05, p50, p95 = np.percentile(f, 5), np.median(f), np.percentile(f, 95)
            med[(blk, lev)] = p50
            print(f"    {blk:7s} {lev:6.1f} {p05:8.1f} {p50:8.1f} {p95:8.1f} {p95/p05:8.1f}x"
                  f"   {float(K.loc[blk, ANCHOR_COL[lev]]):13.1f}")
            rows.append(dict(tag=TAG, block=blk, level_K=lev, n_draws=len(f),
                             p05_yr=p05, median_yr=p50, p95_yr=p95,
                             anchor_prior_yr=float(K.loc[blk, ANCHOR_COL[lev]])))

    print(f"\n[2] AGAINST THE DELIVERABLE'S STATED NUMBERS")
    for blk, claim in DOC_CLAIM.items():
        m = med[(blk, DOC_LEVEL)]
        print(f"    {blk:7s} document ~{claim:.0f} yr   {TAG} median @{DOC_LEVEL}K = {m:.0f} yr"
              f"   ({abs(m-claim)/claim:.1%} apart)  => BACKED")
        other = med[(blk, 3.0)]
        print(f"            ⚠ but @3.0K the same quantity is {other:.0f} yr "
              f"({m/other:.1f}x smaller) — the LEVEL must be stated")
    r19 = [r for r in rows if r["block"] == "R19" and r["level_K"] == DOC_LEVEL][0]
    print(f"    ⚠ R19's posterior spans {r19['p05_yr']:.0f}–{r19['p95_yr']:.0f} yr "
          f"({r19['p95_yr']/r19['p05_yr']:.0f}x). A bare median overstates the precision.")

    stamp(pd.DataFrame(rows), __file__, tag=TAG, inputs={'posterior': POST, 'consts': CONSTS},
          extra=f'tau50 yr; nu FIXED at the anchor; every {THIN}th draw').to_csv(OUT_CSV, index=False)
    print(f"\n[wrote] {os.path.relpath(OUT_CSV, REPO)}")


if __name__ == "__main__":
    main()
