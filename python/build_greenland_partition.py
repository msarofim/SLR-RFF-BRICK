#!/usr/bin/env python3
"""
build_greenland_partition.py — the observed Greenland surface-mass-balance /
discharge partition, from Mouginot et al. 2019 into a tidy tracked CSV.

This is the constraint that makes a two-channel Greenland module identifiable:
the model's fast (surface) and slow (dynamic) channels have to reproduce not
just the total mass loss but how it divides between accumulation-minus-runoff
and marine-terminating discharge.

SOURCE
  Mouginot, J. et al. (2019) "Forty-six years of Greenland Ice Sheet mass
  balance from 1972 to 2018", PNAS 116:9239, doi 10.1073/pnas.1904242116.
  Supplementary Dataset S2 (pnas.1904242116.sd02.xlsx), sheet "(2) MB_GIS".
  260 glaciers; 85% of discharge constrained by measured ice thickness, 15%
  from velocity-scaled reference fluxes.

WHY THIS SOURCE AND NOT MANKOFF 2021
  Mankoff et al. 2021 (ESSD 13:5001) runs from 1840 and is tempting for the
  full historical window, but its pre-1986 discharge is reconstructed as a
  linear fit to runoff with a 6-year trailing average, and its pre-1986 SMB is
  a regression of in-situ temperature onto RACMO. Before 1986 its two channels
  are therefore not independent, and fitting a two-channel model to them would
  recover Mankoff's assumed relationship rather than an observed one. Mouginot
  is shorter but is a genuine measurement of the split. Mankoff remains useful
  as a TOTAL mass-balance series.

CONVENTIONS
  Gt/yr, sign convention as published: SMB positive = mass gain,
  D positive = mass lost by discharge, MB = SMB - D (checked below).
  SMB starts 1958, discharge and mass balance 1972; the file carries all of it
  and leaves SMB-only years with missing discharge.

  python3 python/build_greenland_partition.py
Writes data/observations/greenland_partition_mouginot2019.csv
"""
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.expanduser("~/Documents/2026/ClaudeDocs/Papers/Mouginot/"
                         "pnas.1904242116.sd02.xlsx")
SHEET = "(2) MB_GIS"
OUT = os.path.join(REPO, "data/observations/greenland_partition_mouginot2019.csv")

REGIONS = ["SW", "CW", "NW", "NO", "NE", "CE", "SE", "GIS"]
# Sheet layout: a labelled header row ("D", "SMB", "MB", "MB CUMUL", ...) is
# followed by eight region rows. Within each row the VALUES occupy the first run
# of year columns and the ERRORS a second run of the same years further right,
# so the year header appears twice.
BLOCKS_WANTED = ["D", "SMB", "MB"]
CLOSURE_TOL_GT = 0.51            # MB = SMB - D to the published rounding


def load_sheet():
    import openpyxl
    wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
    return [list(r) for r in wb[SHEET].iter_rows(values_only=True)]


def find_year_header(rows):
    """The 'start' row carries the decimal year of each data column, twice: once
    for the values and once for the errors. Returns (years, value_cols, err_cols)."""
    for r in rows:
        if len(r) > 1 and r[1] == "start":
            runs, run = [], []
            prev = None
            for j, v in enumerate(r):
                if isinstance(v, (int, float)) and 1900 < float(v) < 2100:
                    if prev is not None and j != prev + 1:
                        runs.append(run); run = []
                    run.append((j, int(round(float(v) + 0.5))))   # start 1971.5 -> 1972
                    prev = j
            if run:
                runs.append(run)
            if len(runs) != 2:
                raise RuntimeError(f"expected a value run and an error run, found {len(runs)}")
            years = [y for _, y in runs[0]]
            if [y for _, y in runs[1]] != years:
                raise RuntimeError("value and error year headers disagree")
            return years, [j for j, _ in runs[0]], [j for j, _ in runs[1]]
    raise RuntimeError("no 'start' year header row found in the sheet")


def find_blocks(rows):
    """Each wanted block is a header row whose label is the block name, followed
    by eight region rows."""
    blocks = {}
    for i, r in enumerate(rows):
        lab = r[1] if len(r) > 1 else None
        if lab in BLOCKS_WANTED and lab not in blocks:
            run = [rr for rr in rows[i + 1:i + 40]
                   if len(rr) > 1 and rr[1] in REGIONS][:len(REGIONS)]
            if [rr[1] for rr in run] != REGIONS:
                raise RuntimeError(f"block {lab}: region rows are {[rr[1] for rr in run]}")
            blocks[lab] = run
    missing = set(BLOCKS_WANTED) - set(blocks)
    if missing:
        raise RuntimeError(f"blocks not found: {sorted(missing)}")
    return blocks


def series(block, region, years, cols):
    row = block[REGIONS.index(region)]
    vals = [float(row[c]) if c < len(row) and isinstance(row[c], (int, float)) else np.nan
            for c in cols]
    return pd.Series(vals, index=years)


def main():
    rows = load_sheet()
    years, vcols, ecols = find_year_header(rows)
    blocks = find_blocks(rows)

    out = pd.DataFrame({"year": years}).set_index("year")
    for name, key, cols in (("smb_gt", "SMB", vcols), ("discharge_gt", "D", vcols),
                            ("mb_gt", "MB", vcols), ("smb_err_gt", "SMB", ecols),
                            ("discharge_err_gt", "D", ecols), ("mb_err_gt", "MB", ecols)):
        out[name] = series(blocks[key], "GIS", years, cols)
    out = out.dropna(how="all")

    # closure: the published MB must be SMB - D
    both = out.dropna(subset=["smb_gt", "discharge_gt", "mb_gt"])
    resid = both.smb_gt - both.discharge_gt - both.mb_gt
    worst = float(np.max(np.abs(resid)))
    assert worst < CLOSURE_TOL_GT, \
        f"MB != SMB - D: max residual {worst:.3f} Gt/yr over {len(both)} years"

    out.reset_index().to_csv(OUT, index=False)

    print(f"Mouginot 2019 Greenland partition | {os.path.basename(SRC)} :: {SHEET}")
    print(f"  SMB       {int(out.smb_gt.first_valid_index())}-{int(out.smb_gt.last_valid_index())}"
          f"  ({out.smb_gt.notna().sum()} yr)")
    print(f"  discharge {int(out.discharge_gt.first_valid_index())}-"
          f"{int(out.discharge_gt.last_valid_index())}  ({out.discharge_gt.notna().sum()} yr)")
    print(f"  closure MB = SMB - D: max residual {worst:.3f} Gt/yr  PASS")

    print("\n  decade means, Gt/yr (SMB positive = gain, D positive = loss, MB = SMB - D)")
    print(f"  {'decade':8s} {'SMB':>9s} {'D':>9s} {'MB':>9s}")
    for d0 in range(1970, 2020, 10):
        w = out.loc[d0:d0 + 9].dropna(subset=["discharge_gt"])
        if w.empty:
            continue
        print(f"  {d0}s{'':3s} {w.smb_gt.mean():9.1f} {w.discharge_gt.mean():9.1f} "
              f"{w.mb_gt.mean():9.1f}")

    # the number the two-channel split actually has to reproduce
    early = out.loc[1972:1990].dropna(subset=["discharge_gt"])
    late = out.loc[2000:2018].dropna(subset=["discharge_gt"])
    print(f"\n  1972-1990 mean: SMB {early.smb_gt.mean():6.1f}  D {early.discharge_gt.mean():6.1f}"
          f"  MB {early.mb_gt.mean():+6.1f} Gt/yr  (near balance)")
    print(f"  2000-2018 mean: SMB {late.smb_gt.mean():6.1f}  D {late.discharge_gt.mean():6.1f}"
          f"  MB {late.mb_gt.mean():+6.1f} Gt/yr")
    dsmb = late.smb_gt.mean() - early.smb_gt.mean()
    dd = late.discharge_gt.mean() - early.discharge_gt.mean()
    print(f"  CHANGE:         SMB {dsmb:+6.1f}  D {dd:+6.1f} Gt/yr  ->  "
          f"{100 * (-dsmb) / (-dsmb + dd):.0f}% of the extra loss is surface, "
          f"{100 * dd / (-dsmb + dd):.0f}% dynamic")
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
