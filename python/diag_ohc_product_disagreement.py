#!/usr/bin/env python3
"""
DIAGNOSTIC — how far apart are the two spliced observed-OHC products over 1950-1993?

Why this exists: the L24 deliverable ends its thermal-expansion paragraph with "Cheng and IGCC
disagree by ~50% on 1950-1993 ocean heat gain", and a 2026-09-10 audit found NO OUTPUT computing
it. The number turns out to be right for the window named. The ATTRIBUTION does not survive.

⛔⛔ THE NAMES ARE NOT THE PRODUCTS OVER MOST OF THAT WINDOW. Both files are Zanna 2019 spliced
to a modern product, but AT DIFFERENT PIVOTS: cheng from 1961, igcc only from 1981. So over
1950-1993 the comparison decomposes into three quite different things, and only the last is
actually Cheng-against-IGCC:

    1950-1960   both series ARE Zanna         -> identical by construction, 0%
    1961-1980   Cheng vs ZANNA                -> 62%, and it is NOT a Cheng/IGCC disagreement
    1981-1993   Cheng vs IGCC, genuinely      -> ratio 11.7x on a TINY Cheng base (0.40 vs 4.70)

⇒ the defensible sentence is about THE TWO SPLICED PRODUCTS AS BUILT, not about Cheng vs IGCC.
⚠ And the 11.7x is a ratio on a near-zero denominator: quote the BASE, never the ratio alone
  ([[ratio_needs_its_base]]).
⚠ The headline is also endpoint-sensitive: single-year endpoints give 51%, five-year mean
  endpoints give 35%. The project rule is multi-year endpoints, so BOTH are reported and the
  document should say which it means.

WRITES only outputs/. Reports only.
"""
import os
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from provenance import stamp

REPO   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBS    = os.path.join(REPO, "data", "observations")
OUT_CSV = os.path.join(REPO, "outputs", "diag_ohc_product_disagreement.csv")

FILES  = {"Zanna+Cheng": "ohc_spliced_zanna_cheng.csv",
          "Zanna+IGCC":  "ohc_spliced_zanna_igcc.csv"}
DOC_WINDOW = (1950, 1993)          # the window the deliverable names
DOC_CLAIM_PCT = 50.0               # "~50%"
HALF = 2                           # +/- HALF yr for the multi-year endpoint variant
SUBWINDOWS = [((1950, 1960), "both series ARE Zanna - identical by construction"),
              ((1961, 1980), "Cheng vs ZANNA - NOT a Cheng/IGCC disagreement"),
              ((1981, 1993), "Cheng vs IGCC - the only genuine head-to-head"),
              (DOC_WINDOW,   "the window the deliverable quotes")]


def load(fn):
    d = pd.read_csv(os.path.join(OBS, fn), comment="#", header=None,
                    names=["year", "ohc_1e22J", "source"])
    for c in ("year", "ohc_1e22J"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=["year", "ohc_1e22J"]).astype({"year": int}).set_index("year")
    assert d.index.is_unique, f"{fn}: duplicate years"
    return d


def gain(d, y0, y1, half=0):
    """Cumulative-OHC difference between window endpoints. half=0 -> single years."""
    if half == 0:
        return d.loc[y1, "ohc_1e22J"] - d.loc[y0, "ohc_1e22J"]
    return (d.loc[y1-half:y1+half, "ohc_1e22J"].mean()
            - d.loc[y0-half:y0+half, "ohc_1e22J"].mean())


def main():
    S = {k: load(v) for k, v in FILES.items()}
    a, b = list(S)

    print("=" * 78)
    print("DIAGNOSTIC: spliced observed-OHC product disagreement, cumulative 1e22 J")
    print("=" * 78)
    for k, d in S.items():
        print(f"    {k:12s} {int(d.index.min())}-{int(d.index.max())}  "
              f"sources: {sorted(d.source.unique())}")

    # GATE: the two must be IDENTICAL wherever both are still Zanna. If they are not,
    # they were not built from a common base and no comparison below means anything.
    both_zanna = [y for y in S[a].index
                  if y in S[b].index
                  and str(S[a].loc[y, "source"]).startswith("zanna")
                  and str(S[b].loc[y, "source"]).startswith("zanna")]
    dmax = max(abs(S[a].loc[y, "ohc_1e22J"] - S[b].loc[y, "ohc_1e22J"]) for y in both_zanna)
    print(f"\n[GATE COMMON BASE] {len(both_zanna)} yr where BOTH are still Zanna "
          f"({min(both_zanna)}-{max(both_zanna)}): max |diff| = {dmax:.3e}")
    if dmax > 1e-9:
        raise SystemExit("[GATE COMMON BASE] FAILED - the two files do not share the Zanna "
                         "base, so a 'product disagreement' is confounded with the base")
    print("    => PASS. They share a base; every difference below is the SPLICE, not the base.")

    rows = []
    print(f"\n[1] DECOMPOSITION - what is actually being compared, window by window")
    print(f"    {'window':12s} {a:>12s} {b:>12s} {'ratio':>8s} {'% of smaller':>13s}")
    for (y0, y1), note in SUBWINDOWS:
        ga, gb = gain(S[a], y0, y1), gain(S[b], y0, y1)
        lo = min(abs(ga), abs(gb))
        ratio = gb / ga if abs(ga) > 1e-12 else np.nan
        pct = abs(gb - ga) / lo * 100 if lo > 1e-12 else np.nan
        print(f"    {f'{y0}-{y1}':12s} {ga:12.3f} {gb:12.3f} {ratio:8.2f} {pct:12.0f}%")
        print(f"      {note}")
        rows.append(dict(window=f"{y0}-{y1}", endpoint="single-year",
                         gain_cheng=ga, gain_igcc=gb, ratio=ratio, pct_of_smaller=pct,
                         note=note))

    print(f"\n[2] ENDPOINT SENSITIVITY on the quoted window {DOC_WINDOW[0]}-{DOC_WINDOW[1]}")
    y0, y1 = DOC_WINDOW
    for half, lbl in ((0, "single-year"), (HALF, f"{2*HALF+1}-yr mean")):
        ga, gb = gain(S[a], y0, y1, half), gain(S[b], y0, y1, half)
        pct = abs(gb - ga) / min(abs(ga), abs(gb)) * 100
        print(f"    {lbl:12s} endpoints: {a} {ga:6.2f}, {b} {gb:6.2f}  => {pct:.0f}% of smaller")
        if half:
            rows.append(dict(window=f"{y0}-{y1}", endpoint=lbl, gain_cheng=ga, gain_igcc=gb,
                             ratio=gb/ga, pct_of_smaller=pct,
                             note="multi-year endpoints, the project's standing rule"))

    print(f"\n[3] VERDICT vs the deliverable's '~{DOC_CLAIM_PCT:.0f}%'")
    ga, gb = gain(S[a], y0, y1), gain(S[b], y0, y1)
    pct1 = abs(gb - ga) / min(abs(ga), abs(gb)) * 100
    print(f"    NUMBER: BACKED on single-year endpoints ({pct1:.0f}% of the smaller). "
          f"On {2*HALF+1}-yr endpoints it is "
          f"{abs(gain(S[b],y0,y1,HALF)-gain(S[a],y0,y1,HALF))/min(abs(gain(S[a],y0,y1,HALF)),abs(gain(S[b],y0,y1,HALF)))*100:.0f}%.")
    print(f"    ⛔ ATTRIBUTION: NOT BACKED. Over {SUBWINDOWS[0][0][0]}-{SUBWINDOWS[1][0][1]} the "
          f"'{b}' series is ZANNA, not IGCC,")
    print(f"       so most of the quoted disagreement is Cheng-vs-Zanna. Say 'the two spliced "
          f"OHC products',")
    print(f"       not 'Cheng and IGCC'.")

    stamp(pd.DataFrame(rows), __file__, inputs=FILES,
          extra='cumulative 1e22 J; gains are endpoint differences').to_csv(OUT_CSV, index=False)
    print(f"\n[wrote] {os.path.relpath(OUT_CSV, REPO)}")


if __name__ == "__main__":
    main()
