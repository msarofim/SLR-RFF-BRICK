#!/usr/bin/env python3
"""refresh_draws_parquet.py -- re-derive every Parquet twin that is OLDER than its CSV (2026-09-21).

The 2026-09-01 migration wrote `outputs/scope_slr_fairunc_draws_*.parquet` (float32 value_cm) beside the
CSVs the Julia drivers emit, and `draws_io.draws_path` prefers the twin. A re-run of an arm rewrites the
CSV only, so the twin goes stale and shadows it (draws_io now detects that and reads the CSV, with a
warning). This script brings the twins back in line: same schema as the migration (value_cm float32,
everything else as read), one file per stale twin, and a per-file gate that the twin reproduces the CSV
to the float32 relative error the migration measured (6e-08). Prints what it did; --dry-run lists only.

  python3 python/refresh_draws_parquet.py [--dry-run] [--all]
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRY = "--dry-run" in sys.argv
ALL = "--all" in sys.argv
REL_TOL = 1.0e-7            # the migration measured 6.0e-08; float32 is 6e-08 at worst

done = 0
for pq in sorted(glob.glob(os.path.join(REPO, "outputs", "scope_slr_fairunc_draws_*.parquet"))):
    csv = pq[:-len(".parquet")] + ".csv"
    if not os.path.exists(csv):
        continue
    stale = os.path.getmtime(csv) > os.path.getmtime(pq) + 1.0
    if not (stale or ALL):
        continue
    print(("would refresh" if DRY else "refreshing"), os.path.basename(pq))
    if DRY:
        continue
    d = pd.read_csv(csv)
    d["value_cm"] = d["value_cm"].astype(np.float32)
    d.to_parquet(pq, index=False)
    back = pd.read_parquet(pq)
    orig = pd.read_csv(csv)
    assert len(back) == len(orig), "row count"
    rel = np.nanmax(np.abs(back.value_cm.values.astype(np.float64) - orig.value_cm.values) /
                    np.maximum(np.abs(orig.value_cm.values), 1e-9))
    assert rel < REL_TOL, f"{os.path.basename(pq)}: float32 twin off by {rel:.2e} > {REL_TOL}"
    done += 1
print(f"{done} twin(s) refreshed" if not DRY else "dry run")
