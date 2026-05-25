"""
column_helpers.py
=================

Shared CSV-column helpers used across the SLR-RFF-BRICK plot/decomp pipeline.
Two column-naming conventions coexist in this codebase:

  * **Legacy bare-year** (v1.4.1 era and slim-emitter output): column names
    are bare year strings — "1850", "1851", ..., "2300" — and a single
    set of these per CSV means "total SLR".
  * **Prefixed per-component** (v1.4.5 flat-cube driver output): columns
    are prefixed with the component name — "slr_1850", "ais_2100",
    "te_<y>", "gis_<y>", "gsic_<y>", "lws_<y>".

Downstream scripts need to detect year columns in both, and historically did
so with three different one-line patterns scattered across files. This
module centralizes the detection so a future schema change is a one-file fix.
"""
from __future__ import annotations

import pandas as pd


KEY_COLS = ("rff_idx", "fair_cfg_idx", "seed_idx", "post_idx")


def detect_year_columns(df: pd.DataFrame, prefix: str = "") -> list[int]:
    """Return sorted list of `int` years parsed from year-encoding column names.

    With `prefix=""` (default), matches bare-year columns like "1850". This
    is the legacy convention used by `apply_wong_weights.py`,
    `hawkins_sutton.py`, and the slim-CSV outputs.

    With `prefix="slr_"` (or `"ais_"`, `"te_"`, ...), matches the v1.4.5
    flat-cube driver's per-component columns like "slr_2100".

    Returns an empty list if no matching columns exist.
    """
    yrs: list[int] = []
    for c in df.columns:
        # `c.isdigit()` covers the bare-year path; the prefixed path strips
        # the prefix then re-checks.
        if prefix:
            if c.startswith(prefix) and c[len(prefix):].isdigit():
                yrs.append(int(c[len(prefix):]))
        else:
            if isinstance(c, str) and c.isdigit():
                yrs.append(int(c))
    return sorted(yrs)
