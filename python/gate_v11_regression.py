#!/usr/bin/env python3
"""
gate_v11_regression.py -- the edited (v1.1) code, run with the v1.0 settings, must reproduce the SHIPPED v1.0 outputs.

    python python/gate_v11_regression.py <reproduced.csv> <shipped.csv> [<reproduced.csv> <shipped.csv> ...]

Run by run_ladrillo_v11_rerun_20261008.sh (phase `regress`) BEFORE any canonical output is overwritten. The reproduced
files carry the v1.0 suffix (LADRILLO_V11_SFX = "_paleov1_lwsv1_step", or "_lwsv1_step" for BRICK 2.0); the shipped
files are the canonical v1.0 products. Every column except `provenance` (whose text names the new settings) must be
equal, value for value: floats parsed exactly (pandas float_precision="round_trip"; its default parser is not exact,
Ladrillo CHANGELOG 2026-10-07e), NaN == NaN. Exit 1 on any difference.

Power: before comparing, each pair is checked once with ONE value of the reproduced file moved by one ulp; the gate
must report exactly one difference, or it is refused as blind.
"""
import sys, os
import numpy as np, pandas as pd

def load(p):
    d = pd.read_csv(p, float_precision="round_trip")
    return d.drop(columns=[c for c in d.columns if c == "provenance"])

def ndiff(a, b):
    if list(a.columns) != list(b.columns) or a.shape != b.shape:
        return None
    n = 0
    for c in a.columns:
        x, y = a[c].to_numpy(), b[c].to_numpy()
        if x.dtype.kind == "f" or y.dtype.kind == "f":
            x, y = x.astype(float), y.astype(float)
            n += int((~((x == y) | (np.isnan(x) & np.isnan(y)))).sum())
        else:
            n += int((x != y).sum())
    return n

pairs = sys.argv[1:]
if not pairs or len(pairs) % 2:
    raise SystemExit(__doc__)
bad = 0
for new_p, old_p in zip(pairs[0::2], pairs[1::2]):
    a, b = load(new_p), load(old_p)
    ## power check: one ulp on the first float cell of the reproduced copy
    fc = next((c for c in a.columns if a[c].dtype.kind == "f"), None)
    if fc is None:
        raise SystemExit(f"{new_p}: no float column to mutation-test")
    m = a.copy(); i = int(np.flatnonzero(np.isfinite(m[fc].to_numpy()))[0])
    m.loc[i, fc] = np.nextafter(m.loc[i, fc], np.inf)
    if ndiff(m, a) != 1:
        raise SystemExit(f"[V1-REGRESSION] BLIND on {os.path.basename(new_p)}: a 1-ulp mutant was not caught exactly once")
    n = ndiff(a, b)
    verdict = "IDENTICAL" if n == 0 else ("SHAPE/COLUMNS DIFFER" if n is None else f"{n} values differ")
    print(f"  {os.path.basename(new_p):78s} vs shipped: {a.shape[0]:7d} rows  {verdict}")
    bad += 0 if n == 0 else 1
print(f"[V1-REGRESSION] {'PASS' if bad == 0 else 'FAIL'} ({len(pairs)//2} pair(s); 1-ulp power check passed on each)")
sys.exit(0 if bad == 0 else 1)
