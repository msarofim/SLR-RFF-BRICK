#!/usr/bin/env python3
"""Build outputs/mcmc/overdispersed_starts.csv from an extC tuning chain.

Convention (2026-07-19 audit / extA108 workflow): starts are REAL posterior
draws, not jitter — 4 rows at the ais_iceflow0 quantiles 0.02/0.35/0.65/0.98
of the post-burn tuning chain (iceflow0 is the slowest-mixing direction; real
draws are feasible by construction AND dispersed along the direction that
actually fails to mix). Columns = the chain's parameter columns (all 52 for
extC sampled-amp), which is exactly the pn0 header the calibrator asserts.

Usage: python3 python/build_overdispersed_starts_extc.py [--chain=...] [--burn-frac=0.5]
Seeds 2026/2027/2028/2029 map to rows 1-4 (calibrator convention).
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")


def _argval(pfx, default=None):
    for a in sys.argv[1:]:
        if a.startswith(pfx):
            return a[len(pfx):]
    return default


CHAIN = _argval("--chain=")
if CHAIN is None:
    cands = sorted(glob.glob(os.path.join(REPO, "outputs/mcmc/chain_extC1_seed*_n*.csv")))
    assert cands, "no extC1 tuning chain found; pass --chain="
    CHAIN = cands[-1]
BURN = float(_argval("--burn-frac=", "0.5"))
OUT = os.path.join(REPO, "outputs/mcmc/overdispersed_starts.csv")
QUANTS = [0.02, 0.35, 0.65, 0.98]

ch = pd.read_csv(CHAIN)
ch = ch.iloc[int(len(ch) * BURN):]
par_cols = [c for c in ch.columns if c not in ("log_post", "accept_rate")]
rows = []
for q in QUANTS:
    target = ch["ais_iceflow0"].quantile(q)
    ix = (ch["ais_iceflow0"] - target).abs().idxmin()
    rows.append(ch.loc[ix, par_cols])
out = pd.DataFrame(rows).reset_index(drop=True)
if os.path.exists(OUT):
    os.replace(OUT, OUT + ".pre_extc_bak")   # the stale 2-tau 39-col file; keep a copy
out.to_csv(OUT, index=False, float_format="%.10g")
print(f"chain={os.path.basename(CHAIN)} (post-burn n={len(ch)}) -> {os.path.relpath(OUT, REPO)}")
print(f"  {len(par_cols)} param columns; ais_iceflow0 at quantiles {QUANTS}: "
      + "/".join(f"{r['ais_iceflow0']:.3f}" for _, r in out.iterrows()))
