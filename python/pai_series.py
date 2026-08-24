"""Which files in `data/cmip6_pai/` are per-model AIS/global tas series — and which are not.

`data/cmip6_pai/` is a SHARED directory. Alongside the per-model series
`tas_series_<model>.csv` (columns year, member, tas_global, tas_ais, scenario) it holds
several sibling reductions written by other scripts, all matching the same
`tas_series_*.csv` glob and NONE of them carrying `tas_global` + `tas_ais`:

    tas_series_ext_<model>.csv        reduce_cmip6_tas_pai_ext.py     post-2100 extension
    tas_series_deck_<model>.csv       reduce_cmip6_tas_pai_deck.py    DECK 1pctCO2
    tas_series_hemis_<model>.csv      reduce_cmip6_hemis.py           tas_sh / tas_nh
    tas_series_ohc_deck_<model>.csv   reduce_cmip6_ohc_deck.py        ocean heat content

Each consumer used to carry its OWN inline tuple of prefixes to skip, and the three
copies had already drifted apart -- `diag_pai_cmip6_rate.py` skipped only `ext`, while
`diag_pai_cmip6_time.py` and `diag_pai_denominator.py` skipped `ext`/`deck`/`hemis`. When
the OHC reduction landed in the same directory it matched none of the three lists, and
`diag_pai_cmip6_time.py` began dying on a bare `KeyError: tas_global` -- a filename
blacklist cannot be kept in step with a directory that keeps gaining siblings.

So the list lives here ONCE, and the prefix filter is BACKED BY A SCHEMA GATE. A file
that survives the prefix filter but does not carry the required columns is a LOUD ERROR
naming the file, not a silent skip: silently dropping it is how a model quietly leaves
an ensemble, and every number in these diagnostics is a median or a spread over that
ensemble.
"""
import glob
import os

import pandas as pd

## Sibling reductions that share the `tas_series_*.csv` glob. Longest-first so that
## `ohc_deck` is tested before `deck` and the recorded kind is the specific one.
SIBLING_PREFIXES = ("ohc_deck", "hemis", "deck", "ext")
## The columns that make a file a per-model AIS/global series.
REQUIRED_COLS = ("year", "tas_global", "tas_ais", "scenario")


def sibling_kind(basename):
    """The sibling-reduction kind this filename declares, or None if it is a model series."""
    for p in SIBLING_PREFIXES:
        if basename.startswith(f"tas_series_{p}_"):
            return p
    return None


def model_series_files(in_dir):
    """`{model: path}` for every per-model AIS/global series in `in_dir`.

    Raises on a file that passes the prefix filter but lacks REQUIRED_COLS, because that
    means a new sibling reduction has appeared and SIBLING_PREFIXES has not been told
    about it -- the caller must decide, not this function.
    """
    out = {}
    for f in sorted(glob.glob(os.path.join(in_dir, "tas_series_*.csv"))):
        b = os.path.basename(f)
        if sibling_kind(b) is not None:
            continue
        cols = set(pd.read_csv(f, nrows=0).columns)
        missing = [c for c in REQUIRED_COLS if c not in cols]
        if missing:
            raise ValueError(
                f"{b} is not a per-model AIS/global series (missing {missing}; has "
                f"{sorted(cols)}) but does not match any prefix in SIBLING_PREFIXES="
                f"{SIBLING_PREFIXES}. A new sibling reduction has landed in {in_dir}: "
                f"add its prefix to python/pai_series.py, or move it out of this "
                f"directory. It is NOT skipped silently -- that would drop a model from "
                f"the ensemble without saying so.")
        out[b[len("tas_series_"):-len(".csv")]] = f
    return out


## ---------------------------------------------------------------------------
## The sftlf/tas coordinate-alignment repair
## ---------------------------------------------------------------------------
## Three reducers in this directory -- reduce_cmip6_tas_pai.py, _deck.py and _ext.py --
## build their cos-lat global weight `wg` and their AIS mask `wa` ONCE from **sftlf**'s
## coordinates, then apply them to each experiment's `tas` through xarray's
## `.weighted()`. `.weighted()` ALIGNS on coordinate VALUES with an inner join. When a
## model's `sftlf.lat` differs from its `tas.lat` in the last float digit, the reduction
## silently collapses to the INTERSECTION of the two grids -- no warning, no shape error,
## and a number that is wrong by several K while still looking like a temperature.
##
## Measured on the MPI family (`outputs/diag_pai_mpi_repair.md`), where `lat` differs by
## 1.4e-14 / 2.8e-14 deg and `lon` matches exactly:
##     MPI-ESM1-2-LR   56/96 latitudes kept (58.3%)   1850-1900 global 279.31 vs 286.68 K
##     MPI-ESM1-2-HR  120/192 latitudes kept (62.5%)  1850-1900 global 279.44 vs 287.08 K
## It bit `data/cmip6_pai`'s model series, the `deck` series (which also caught
## MPI-ESM-1-2-HAM) and the `ext` series. `reduce_cmip6_hemis.py` escaped only because it
## builds its weights from a **tas** dataset rather than from sftlf.
##
## Both halves below are needed and neither substitutes for the other: `align_sftlf_to`
## removes the cause, and `assert_global_plausible` is the gate that would have caught it
## in 2026-06 -- a 279 K global mean is not a global mean, whatever produced it.
COORD_TOL_DEG = 1e-3
## SIZED AGAINST THE REALISED SPREAD, not guessed. The gate sees a PER-EXPERIMENT series
## mean, and across all 45 model x 9 experiment series on disk those run
## **285.69 K** (CNRM-CM6-1-HR piControl) to **297.82 K** (CanESM5 ssp585) -- an ssp585 or
## abrupt-4xCO2 series mean legitimately sits well above any preindustrial value, and a
## first cut of this constant at (283, 293) would have rejected FOUR real series
## (CanESM5, ACCESS-CM2 and GISS-E2-1-H on ssp585, CESM2 on abrupt-4xCO2). That is the
## failure mode memory `tolerance_scaled_to_spread` records: a PLAUSIBILITY rail held to
## an identity gate's tightness starts choosing the data.
##
## The defect this rail exists to catch produced per-file means of 279.3-281.9 K. So:
##   bottom 283.0 -- 2.7 K below the coldest real series, 1.1 K above the mildest defect;
##   top    302.0 -- 4.2 K above the hottest real series, a loose sanity rail only.
## The observed defect is a COLD bias (the dropped cells were low-latitude), but the grid
## intersection could in principle go the other way, so the top rail is kept.
GLOBAL_PLAUSIBLE_K = (283.0, 302.0)


def align_sftlf_to(sftlf, ds, label=""):
    """`sftlf` carrying `ds`'s own lat/lon values, so `.weighted()`'s inner join is a no-op.

    Gated, because a reindex is only the right repair when the difference really is float
    noise:
      [SHAPE] same grid shape -- a genuine regrid is not a rounding repair and must not
              happen silently here;
      [DRIFT] the coordinate difference must be < COORD_TOL_DEG -- a real offset means
              these are different grids and reindexing would MOVE the AIS mask.
    Call this ONCE PER EXPERIMENT DATASET. Reusing one experiment's weights against
    another is the same bug in its cross-experiment form.
    """
    import numpy as np

    for c in ("lat", "lon"):
        a, b = np.asarray(ds[c].values), np.asarray(sftlf[c].values)
        if a.shape != b.shape:
            raise ValueError(f"{label}: {c} sftlf has {b.size} points, tas has {a.size} "
                             f"-- different grids, not a float-noise repair")
        d = float(np.max(np.abs(a - b)))
        if not (d < COORD_TOL_DEG):
            raise ValueError(f"{label}: {c} differs by {d:.3e} deg > {COORD_TOL_DEG} "
                             f"-- a real offset, so reindexing would move the AIS mask")
    return sftlf.assign_coords(lat=ds.lat.values, lon=ds.lon.values)


def assert_global_plausible(values, label=""):
    """A computed global-mean tas must be a temperature. Raises if it is not.

    Deliberately a PLAUSIBILITY gate on our own number rather than a comparison against
    another reduction: the defect this exists to catch produced a self-consistent set of
    files across three scripts, so there was nothing to disagree with.
    """
    import numpy as np

    m = float(np.nanmean(np.asarray(values, dtype=float)))
    lo, hi = GLOBAL_PLAUSIBLE_K
    if not (lo <= m <= hi):
        raise ValueError(f"{label}: global mean {m:.2f} K outside {GLOBAL_PLAUSIBLE_K} "
                         f"-- this is not a global mean. The usual cause is the "
                         f"sftlf/tas coordinate mismatch: see align_sftlf_to().")
    return m
