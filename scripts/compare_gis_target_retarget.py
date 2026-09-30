#!/usr/bin/env python3
"""compare_gis_target_retarget.py — column-level diff of consumer outputs between two
sandboxes built by measure_gis_target_retarget.sh (or a sandbox and the real repo).

  python scripts/compare_gis_target_retarget.py <scratch-dir> <X|REAL> <Y|REAL> [outputs/f.csv ...]

Default files: every CSV the Y run wrote (newer than <scratch-dir>/_marker). Prints
BYTE-IDENTICAL, or each differing column with its max |diff|; boolean and string
columns (the verdicts) report how many rows change and the True count before -> after.
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S, X, Y = sys.argv[1], sys.argv[2], sys.argv[3]
root = lambda k: REPO if k == "REAL" else os.path.join(S, f"sbx{k}")
marker = os.path.join(S, "_marker")
files = sys.argv[4:] or sorted(
    os.path.relpath(p, root(Y)) for p in glob.glob(os.path.join(root(Y), "outputs/*.csv"))
    if os.path.getmtime(p) > os.path.getmtime(marker))

for f in files:
    a, b = os.path.join(root(X), f), os.path.join(root(Y), f)
    if not (os.path.exists(a) and os.path.exists(b)):
        print(f"{f}: missing in {X if not os.path.exists(a) else Y}")
        continue
    if open(a, "rb").read() == open(b, "rb").read():
        print(f"{f}: BYTE-IDENTICAL")
        continue
    da, db = pd.read_csv(a), pd.read_csv(b)
    if list(da.columns) != list(db.columns) or len(da) != len(db):
        print(f"{f}: SHAPE/COLUMNS differ {da.shape} vs {db.shape}")
        continue
    out = []
    for c in da.columns:
        va, vb = da[c], db[c]
        if va.equals(vb):
            continue
        if pd.api.types.is_numeric_dtype(va) and va.dtype != bool:
            d = (va - vb).abs()
            rel = (d / va.abs().replace(0, np.nan)).max()
            out.append(f"    {c}: max|d| {d.max():.4g} (max rel {rel:.3g})")
        else:
            n = int((va.astype(str) != vb.astype(str)).sum())
            extra = f"  True {int(va.sum())} -> {int(vb.sum())}" if va.dtype == bool else ""
            out.append(f"    {c}: {n}/{len(va)} rows change{extra}  [VERDICT]")
    print(f"{f}: {len(out)} columns differ")
    print("\n".join(out))
