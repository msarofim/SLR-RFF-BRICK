#!/usr/bin/env python3
"""
test_ladrillo_data.py — python/ladrillo_data.py must reproduce the committed
calibrator inputs exactly, and its physics must satisfy the relations the
constants are supposed to encode.

  [1] REGRESSION. The three artifacts rebuilt in memory are identical, to the
      full precision they are written at, to the committed files the original
      exec-prefix chain produced. This is what licenses the refactor: the
      accepted Ladrillo posterior was calibrated against those exact files.
  [2] Reservoir partition: the three reservoirs cover every inventory region
      exactly once, and their inventories sum to the Farinotti total.
  [3] The anchored (kappa, nu) reproduce BOTH regional response times.
  [4] The fitted equilibrium curve reproduces the GlacierMIP3 committed ladder
      within the rung uncertainty it was fit to.
  [5] The region-19 seam adjustment is identity before the seam and, after it,
      removes exactly the observed GlaMBIE region-19 cumulative (lagged one
      year, matching the target's year convention).
  [6] Drivers: no gaps, zero mean over the 1850-1900 frame, and ordered by
      response class over the modern era (R19 coldest-responding, SLOWP the
      strongest amplifier).

  python3 python/test_ladrillo_data.py
"""
import os
import sys

import numpy as np
import pandas as pd

import ladrillo_data as bd

FAILURES = []


def check(name, ok, detail=""):
    print(f"  {name:<62s} {'PASS' if ok else 'FAIL'}{'  (' + detail + ')' if detail else ''}")
    if not ok:
        FAILURES.append(name)
    return ok


def roundtrip(df, fmt):
    """Write/read through the same float format the artifact is stored at, so
    the comparison is against what the calibrator actually reads."""
    import io
    buf = io.StringIO()
    df.to_csv(buf, index=False, float_format=fmt)
    buf.seek(0)
    return pd.read_csv(buf)


print("[1] regression vs the committed artifacts")
drivers, constants, gsic_adj = bd.build_artifacts(write=False)
for label, built, path, fmt in (
        ("t_glac_blocks.csv", drivers, bd.OUT_DRIVERS, "%.12f"),
        ("extc_block_constants.csv", constants, bd.OUT_CONSTANTS, "%.12g"),
        ("recalib_targets_ext_gsicadj.csv", gsic_adj, bd.OUT_GSIC_ADJ, "%.12g")):
    committed = pd.read_csv(path)
    rebuilt = roundtrip(built, fmt)
    if list(rebuilt.columns) != list(committed.columns):
        check(label, False, f"columns differ: {set(rebuilt.columns) ^ set(committed.columns)}")
        continue
    if len(rebuilt) != len(committed):
        check(label, False, f"{len(rebuilt)} rows vs {len(committed)}")
        continue
    worst, worst_col = 0.0, ""
    for c in committed.columns:
        if pd.api.types.is_numeric_dtype(committed[c]):
            d = float(np.nanmax(np.abs(rebuilt[c].to_numpy() - committed[c].to_numpy())))
        else:
            d = 0.0 if (rebuilt[c] == committed[c]).all() else np.inf
        if d > worst:
            worst, worst_col = d, c
    check(label, worst == 0.0, "identical" if worst == 0.0
          else f"max|diff| {worst:.3e} in {worst_col}")

print("\n[2] reservoir partition")
members = [r for m in bd.SPEC_3RES.values() for r in m]
# Region 05 (Greenland periphery) is absent by design: it belongs to the ice-sheet
# scope, which is why the uncharted-ice book value carries the R5_MELT_SHARE factor.
check("every inventory region covered exactly once",
      sorted(members) == sorted(bd.REGIONS.index) and len(members) == len(set(members)),
      f"{len(members)} regions, region 05 excluded (ice-sheet scope)")
inventory = constants.a0.sum() - constants.S2000_data.sum()
expected = bd.FARINOTTI_NONR19[0] + bd.FARINOTTI_R19[0]
check("reservoir inventories sum to the Farinotti total",
      abs(inventory - expected) < 1e-9, f"{inventory:.4f} vs {expected:.4f} m SLE")

print("\n[3] anchored transient reproduces both response times")
res3 = {n: bd.build_reservoir(n, m, farinotti_basis=True) for n, m in bd.SPEC_3RES.items()}
for name, row in constants.set_index("block").iterrows():
    block = dict(res3[name], a=row.a0, b=row.b_fit_obsfit, T_off=row.T_off_fit_obsfit,
                 amp_b=row.amp_obsfit)
    t15 = bd.tau50_of(block, row.kappa_anch_obsfit, row.nu_anch_obsfit, 1.5)
    t30 = bd.tau50_of(block, row.kappa_anch_obsfit, row.nu_anch_obsfit, 3.0)
    ok = (abs(t15 / row.tau15 - 1) < bd.TAU_MATCH_TOL
          and abs(t30 / row.tau30 - 1) < bd.TAU_MATCH_TOL)
    check(f"{name}: tau50 matches tau15 and tau30", ok,
          f"{t15:.0f}/{row.tau15:.0f} yr, {t30:.0f}/{row.tau30:.0f} yr")

print("\n[4] fitted equilibrium curve reproduces the committed ladder")
for name, row in constants.set_index("block").iterrows():
    worst_z = 0.0
    for L in bd.GMIP3_LEVELS:
        key = str(L).replace(".", "p")
        s_eq = row.a0 * (1 - np.exp(-row.b_fit_regchar
                                    * (row.amp_regchar * L - row.T_off_fit_regchar)))
        modelled = 100 * (s_eq - row.S2020_data) / (row.a0 - row.S2020_data)
        worst_z = max(worst_z, abs(modelled - row[f"com{key}"]) / row[f"sig{key}"])
    check(f"{name}: every rung within 2 sigma of the fit", worst_z < 2.0,
          f"worst |z| {worst_z:.2f}")

print("\n[5] region-19 seam adjustment")
raw = bd.TARGET_GSIC
adj = gsic_adj.gsic_adj.to_numpy()
pre = bd.TARGET_YEARS < bd.SEAM_START_YEAR
check("identity before the seam", np.array_equal(adj[pre], raw[pre]),
      f"{pre.sum()} years unchanged")
removed = raw[~pre] - adj[~pre]
# GlaMBIE region 19 gains mass in some years, so the running removal is NOT
# monotone; what must hold is that it equals the observed cumulative exactly.
g19 = bd.GLAMBIE["19"]
annual_cm = pd.Series((-g19.combined_gt.to_numpy()) / bd.GT_PER_MM_SLE / 10.0,
                      index=g19.start_dates.astype(int).to_numpy())
expected = np.cumsum([annual_cm.get(y - 1, 0.0) for y in bd.TARGET_YEARS[~pre]])
check("removal equals the observed GlaMBIE region-19 cumulative",
      np.allclose(removed, expected, atol=1e-15),
      f"max|diff| {np.max(np.abs(removed - expected)):.2e}")
check("net removal is positive at the series end", removed[-1] > 0,
      f"net {10 * removed[-1]:.3f} mm by {bd.TARGET_YEARS[-1]}")

print("\n[6] per-reservoir drivers")
check("no gaps", not drivers.isna().any().any(),
      f"{int(drivers.year.min())}-{int(drivers.year.max())}")
base = drivers[(drivers.year >= bd.DRIVER_BASE[0]) & (drivers.year <= bd.DRIVER_BASE[1])]
check("zero mean over the 1850-1900 frame",
      max(abs(base[b].mean()) for b in bd.SPEC_3RES) < 1e-12)
modern = drivers[drivers.year >= 1995]
warming = {b: modern[b].mean() for b in bd.SPEC_3RES}
check("SLOWP warms most, R19 least (the reason for the split)",
      warming["R19"] < warming["FAST"] < warming["SLOWP"],
      "  ".join(f"{b} {v:+.2f} K" for b, v in warming.items()))

print("\n" + "=" * 74)
if FAILURES:
    sys.exit(f"ladrillo_data: {len(FAILURES)} FAILED — " + "; ".join(FAILURES))
print("ladrillo_data: ALL TESTS PASS")
