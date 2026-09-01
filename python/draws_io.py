#!/usr/bin/env python3
"""
draws_io.py — format-agnostic access to the per-draw SLR ensembles.

WHY THIS EXISTS (2026-09-01)
  The 96 `outputs/scope_slr_fairunc_draws_*` ensembles were written to Parquet
  (0.80 GB -> 0.10 GB, float32; max relative error 6.0e-08 per column, MEASURED).
  Three populations of the same logical file now coexist and every reader has to
  accept all three:

    .parquet   the migrated bulk, float32
    .csv       what the Julia writers (`scope_slr_fair_uncertainty.jl`,
               `scope_slr_fairunc_oldbrick.jl`) still emit, so a FRESH run of any
               arm lands as CSV until it is converted
    .csv.gz    `bench_ladrillo.py`'s frozen benchmark references, which must keep
               scoring bit-for-bit as they were frozen

  A reader that hardcodes `pd.read_csv(<...>.csv)` silently MISSES an arm the
  moment its CSV is deleted -- the file simply "does not exist" and the arm drops
  out of a table with no error (`intersect_is_a_silent_default`). Resolve every
  draws path through `draws_path()` / `draws_exists()` and read it through
  `read_draws()`; never call `pd.read_csv` on a draws path directly.

  Modelled on `metric_horizon_table.pairs_path` / `pairs_read`, which did the same
  job for the `wong_cond_pulse_pairs_*` ensembles.
"""

import os

import pandas as pd

PARQUET_SUFFIX = ".parquet"
CSV_SUFFIX = ".csv"

# Escape hatch, and the mechanism the format-equivalence check uses: set
# SLR_DRAWS_PARQUET=0 to read the float64 CSVs even where a Parquet twin exists.
# Any driver run under it must be LABELLED as a CSV-basis run -- the two bases are
# equal to 6e-08 per column, not identical.
PREFER_PARQUET = os.environ.get("SLR_DRAWS_PARQUET", "1") not in ("0", "no", "false")


def draws_path(path):
    """Resolve a LOGICAL draws path to the file that actually exists.

    Prefers the Parquet twin of a `.csv` path. Anything else -- an explicit
    `.parquet`, a frozen `.csv.gz`, a missing file -- is returned unchanged, so
    the caller's own existence check still reports on the name it asked for.
    """
    if PREFER_PARQUET and path.endswith(CSV_SUFFIX):
        pq = path[: -len(CSV_SUFFIX)] + PARQUET_SUFFIX
        if os.path.exists(pq):
            return pq
    return path


def draws_exists(path):
    """True if EITHER format of this logical draws path is on disk."""
    return os.path.exists(draws_path(path))


def read_draws(path, columns=None, **kw):
    """Read a draws ensemble in whichever format is present.

    `columns` is honoured by both backends (Parquet reads only those column
    chunks; CSV parses only those fields), so a caller that needs three of six
    columns should say so.
    """
    p = draws_path(path)
    if p.endswith(PARQUET_SUFFIX):
        if kw:
            raise TypeError(f"read_draws: {sorted(kw)} not supported for Parquet ({p})")
        return pd.read_parquet(p, columns=columns)
    return pd.read_csv(p, usecols=columns, **kw)
