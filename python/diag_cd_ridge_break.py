#!/usr/bin/env python3
"""
diag_cd_ridge_break.py — does option D's throughput cap do anything to the
phi*L_eq ridge, and if so WHICH of the two pre-registered things?

THE RIDGE (scoping thread 5, section 1 -- the load-bearing fact)
  The 1900-2025 hindcast constrains only the PRODUCT phi*L_eq. Scale the
  commitment by k, re-solve the rate scale that restores the hindcast, and every
  row fits equally well while 2300 moves 14.59 -> 58.29 cm. So the commitment is
  NOT identified, and the reported 2300 number rides on an unidentified k.

WHY A CAP COULD CHANGE THAT
  Under proportional relaxation the annual increment is (k*L_eq - L)*(s*r), which
  for L << k*L_eq is ~ k*s*L_eq*r -- invariant under k*s = const. That IS the
  ridge. A throughput cap q is NOT rescaled by k, so min((k*L_eq - L)*s*r, q)
  is not invariant. Two distinct outcomes follow, and they are distinguished by
  WHICH quantity collapses across k:

  (i)  ridge BROKEN  -- the hindcast starts to constrain k. Needs the cap to bind
       INSIDE the historical window. Tell: hindcast RMSE rises with k.
  (ii) ridge DEFUSED -- the hindcast still cannot constrain k, but because q is
       not rescaled, once the cap binds in projection the 2300 value stops
       depending on k. Tell: hindcast RMSE flat in k, 2300 spread collapses.

  Both were pre-registered (CHANGELOG 2026-08-16c, and its amendment written
  before any C+D cell had been fitted). (ii) is a SUCCESS for the deliverable --
  it removes the harm the ridge does -- but it must be reported as "k is
  unidentified and no longer load-bearing", NEVER as "k is identified".

A SHARPER TEST THAN SECTION 1'S
  Section 1 bisected the rate scale to match the hindcast ENDPOINT, so of course
  every row matched the endpoint -- that was true by construction. This script
  does the same bisection but then reports the FULL-WINDOW RMSE against the
  1900-2025 target as well. The endpoint is matched by construction; the SHAPE is
  not, so RMSE-versus-k is the honest identification test.

READS   outputs/gis_offline_cell_fits.csv   (fitted cell parameters)
WRITES  outputs/diag_cd_ridge_break.csv

  python3 python/diag_cd_ridge_break.py
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gis_offline_cell as G  # noqa: E402

REPO = G.REPO
FITS_CSV = G.OUT_FITS
OUT = os.path.join(REPO, "outputs/diag_cd_ridge_break.csv")

# --- named constants that the labels below derive from -----------------------
# The commitment scales from the thread-5 ridge table, plus the Bochow-matched
# k = 22.6 that forces tau into the 1300 yr range.
K_SCALES = (1.0, 2.0, 5.0, 10.0, 22.6)
RATE_PARAMS = ("alpha", "beta", "alpha_f", "beta_f", "alpha_s", "beta_s")
CAP_PARAMS = ("q_f", "q_s")
PROJ_SSP = "SSP5-8.5"          # the scenario the ridge table reports at 2300
PROJ_YEAR_2300 = 2300
BISECT_LO, BISECT_HI, BISECT_N = 1e-6, 1e4, 100
# A spread this small across the whole k range counts as "collapsed".
COLLAPSE_TOL_CM = 1.0
# An RMSE rise this large across the k range counts as "k is constrained".
IDENTIFY_TOL_CM = 0.05

CELLS_UNDER_TEST = ("A+B+C+D", "A+B'+C+D", "A+B'+C+D2")
# A ladder-scale range below this means option C is INERT: scaling the committed
# loss from 0.5x to 22.6x does not move 2300, so the ladder is not doing the job
# C was added for. This gates the "collapsed, not identified" verdict -- added
# 2026-08-16 after the D run exposed it as a hole in this script's own logic.
LADDER_INERT_TOL_CM = 2.0
LADDER_SCALES = (0.5, 1.0, 2.0, 5.0, 22.6)


def parse_params(s):
    return {kv.split("=")[0].strip(): float(kv.split("=")[1])
            for kv in str(s).split(";") if "=" in kv}


def build_context():
    drv = pd.read_csv(G.DRIVER_CSV).set_index("year")[G.DRIVER_ZONE]
    last_obs_year = int(drv.index.max())
    t_reg = G.extend(drv)
    gmst_hist = G.extend(G.load_gmst())
    ty, obs, sig = G.load_target()
    return dict(t_reg=np.asarray(t_reg, float),
                t_gmst=np.asarray(gmst_hist, float),
                ty=ty, obs=obs, sig=sig, ti=[G._yi[y] for y in ty],
                last_obs_year=last_obs_year)


def series(cell, p, ctx, k, s, capped, t_reg=None, t_gmst=None):
    """One trajectory with the ladder commitment scaled by k and every RELAXATION
    rate by s. The smbrate cell's k_smb is a melt FLUX, not a relaxation rate, so
    it is deliberately left alone -- the ridge is a commitment/relaxation-rate
    degeneracy and scaling a flux would confound the test."""
    spec = G.CELLS[cell]
    t_reg = ctx["t_reg"] if t_reg is None else t_reg
    t_gmst = ctx["t_gmst"] if t_gmst is None else t_gmst
    q = dict(p)
    for r in RATE_PARAMS:
        if r in q:
            q[r] = q[r] * s
    for c in CAP_PARAMS:
        q[c] = q.get(c, G.CAP_INERT_CM_YR) if capped else G.CAP_INERT_CM_YR
    leq = k * G.leq_ladder(t_gmst, q["dT"])
    L, _ = G.integrate(t_reg, leq, q, spec["two_channel"])
    return L


def hind_stats(L, ctx):
    """Endpoint change over the target window, and the full-window RMSE."""
    mdl = G.reref(L)[ctx["ti"]]
    endpoint = float(mdl[-1] - mdl[0])
    rmse = float(np.sqrt(np.mean((mdl - ctx["obs"]) ** 2)))
    return endpoint, rmse


def solve_rate_scale(cell, p, ctx, k, capped, want):
    """Bisect the rate scale so the hindcast ENDPOINT is reproduced."""
    lo, hi = BISECT_LO, BISECT_HI

    def f(s):
        return hind_stats(series(cell, p, ctx, k, s, capped), ctx)[0]

    if (f(lo) - want) * (f(hi) - want) > 0:
        return None                      # endpoint not reachable at any rate scale
    for _ in range(BISECT_N):
        mid = np.sqrt(lo * hi)
        if f(mid) < want:
            lo = mid
        else:
            hi = mid
    return float(np.sqrt(lo * hi))


def project_2300(cell, p, ctx, k, s, capped):
    g = G.extend(G.load_gmst(G.PROJ_SCENARIOS[PROJ_SSP]))
    tr = G.splice_regional(ctx["t_reg"], ctx["t_gmst"], g, ctx["last_obs_year"])
    L = series(cell, p, ctx, k, s, capped,
               t_reg=np.asarray(tr, float), t_gmst=np.asarray(g, float))
    return float(G.reref(L, G.PROJ_REF_WIN)[G._yi[PROJ_YEAR_2300]])


def main():
    if not os.path.exists(FITS_CSV):
        raise SystemExit(f"missing {FITS_CSV} -- run gis_offline_cell.py first")
    fits = pd.read_csv(FITS_CSV).set_index("cell")
    ctx = build_context()
    want = float(ctx["obs"][-1] - ctx["obs"][0])
    print(f"diag_cd_ridge_break | commit={G.COMMIT}")
    print(f"  hindcast target {G.FIT_WIN[0]}-{G.FIT_WIN[1]} endpoint change: "
          f"{want:.2f} cm")
    print(f"  projection {PROJ_SSP} at {PROJ_YEAR_2300}\n")

    rows, ladder_range = [], {}
    for cell in CELLS_UNDER_TEST:
        if cell not in fits.index:
            print(f"  {cell}: NOT in {os.path.basename(FITS_CSV)} -- skipped")
            continue
        p = parse_params(fits.loc[cell, "params"])
        caps = {c: p[c] for c in list(CAP_PARAMS) + ["q_dyn", "q_thalf", "q_marine"]
                if c in p}
        print(f"=== {cell} === fitted caps: " +
              (", ".join(f"{c}={v:.4g}" for c, v in caps.items()) or "state-dependent"))
        ladder_range[cell] = ladder_leverage(cell, p, ctx)
        for capped in (False, True):
            tag = "CAPPED (option D on)" if capped else "uncapped (C only)"
            print(f"\n  {tag}")
            print(f"    {'k':>6s} {'rate scale':>11s} {'hind cm':>9s} "
                  f"{'hind RMSE':>10s} {'2300 cm':>10s}")
            got = []
            for k in K_SCALES:
                s = solve_rate_scale(cell, p, ctx, k, capped, want)
                if s is None:
                    print(f"    {k:6.1f} {'UNREACHABLE':>11s} "
                          f"{'--':>9s} {'--':>10s} {'--':>10s}")
                    rows.append(dict(cell=cell, capped=capped, k=k,
                                     reachable=False))
                    continue
                L = series(cell, p, ctx, k, s, capped)
                ep, rmse = hind_stats(L, ctx)
                proj = project_2300(cell, p, ctx, k, s, capped)
                got.append((rmse, proj))
                print(f"    {k:6.1f} {s:11.4g} {ep:9.2f} {rmse:10.4f} "
                      f"{proj:10.2f}")
                rows.append(dict(cell=cell, capped=capped, k=k, reachable=True,
                                 rate_scale=s, hind_endpoint_cm=ep,
                                 hind_rmse_cm=rmse, proj_2300_cm=proj))
            if len(got) > 1:
                dr = max(r for r, _ in got) - min(r for r, _ in got)
                dp = max(p2 for _, p2 in got) - min(p2 for _, p2 in got)
                print(f"    -> across k: hindcast RMSE spread {dr:.4f} cm, "
                      f"2300 spread {dp:.2f} cm")
        print()

    if rows:
        pd.DataFrame(rows).to_csv(OUT, index=False)
        print(f"wrote {os.path.relpath(OUT, REPO)}")
        verdict(pd.DataFrame(rows), ladder_range)


def ladder_leverage(cell, p, ctx):
    """C's OWN leverage: how far 2300 moves when the committed loss is scaled
    with every other parameter held fixed. If this is ~0 the ladder is inert and
    option C is inoperative, whatever the ridge numbers say."""
    v = [project_2300(cell, p, ctx, k, 1.0, True) for k in LADDER_SCALES]
    return max(v) - min(v)


def verdict(df, ladder_range):
    """Name which pre-registered outcome the numbers support, per cell."""
    print("\n=== VERDICT (against the pre-registered (i)/(ii) split) ===")
    for cell in ladder_range:
        g = df[(df.cell == cell) & df.reachable] if "reachable" in df else df.iloc[0:0]
        cap, unc = g[g.capped], g[~g.capped]
        if cap.empty or unc.empty:
            # The rate-scale bisection cannot reach the endpoint on the smbrate
            # cells: their loss is dominated by the k_smb melt FLUX, which the
            # ridge scaling deliberately does not touch, so the relaxation rate
            # has no leverage. The ridge test is structurally uninformative here
            # -- but the ladder-leverage number is not, and is the one that
            # actually decides whether option C is doing anything.
            print(f"\n  {cell}")
            print("    ridge test UNINFORMATIVE (rate-scale bisection unreachable:")
            print("    an smbrate cell's loss is carried by the unscaled melt flux)")
            print(f"    LADDER range (C's own leverage): {ladder_range[cell]:8.2f} cm")
            if ladder_range[cell] < LADDER_INERT_TOL_CM:
                print("    -> COLLAPSED, NOT IDENTIFIED: the ladder is inert;")
                print("       option C is inoperative in this cell.")
            continue
        d_rmse = cap.hind_rmse_cm.max() - cap.hind_rmse_cm.min()
        d_2300 = cap.proj_2300_cm.max() - cap.proj_2300_cm.min()
        d_2300_u = unc.proj_2300_cm.max() - unc.proj_2300_cm.min()
        lad = ladder_range.get(cell, np.nan)
        print(f"\n  {cell}")
        print(f"    uncapped 2300 spread across k : {d_2300_u:8.2f} cm  "
              f"(the ridge's harm)")
        print(f"    CAPPED   2300 spread across k : {d_2300:8.2f} cm")
        print(f"    CAPPED   hindcast RMSE spread : {d_rmse:8.4f} cm")
        print(f"    LADDER range (C's own leverage): {lad:8.2f} cm")
        # THIRD VERDICT, added after the D run. A cap that binds everywhere makes
        # 2300 independent of k by making the model independent of everything,
        # which satisfies (i) and (ii) trivially and meaninglessly. Check whether
        # option C still has any leverage BEFORE crediting either outcome.
        if np.isfinite(lad) and lad < LADDER_INERT_TOL_CM:
            print("    -> COLLAPSED, NOT IDENTIFIED: scaling the committed loss")
            print(f"       0.5x-22.6x moves 2300 by only {lad:.2f} cm, so the ladder")
            print("       is inert and option C is not doing its job. Any ridge")
            print("       verdict here is VACUOUS -- do not report it as a win.")
        elif d_rmse > IDENTIFY_TOL_CM:
            print("    -> (i) RIDGE BROKEN: the hindcast shape now discriminates k.")
        elif d_2300 < COLLAPSE_TOL_CM < d_2300_u:
            print("    -> (ii) RIDGE DEFUSED: k is still unidentified, but 2300 no")
            print("       longer depends on it. Report as 'unidentified and no")
            print("       longer load-bearing', NEVER as 'identified'.")
        else:
            print("    -> NEITHER: the cap did not change the ridge. D is not")
            print("       doing the job it was added for.")


if __name__ == "__main__":
    main()
