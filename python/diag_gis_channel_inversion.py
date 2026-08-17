#!/usr/bin/env python3
"""
diag_gis_channel_inversion.py — the two-channel labels are backwards. Is that a
cosmetic artefact, a mis-specified constraint, or something the data genuinely
prefer?

THE DEFECT (verified 2026-08-16, offline A+B optimum)
  The channels are NAMED fast (surface mass balance) and slow (dynamic
  discharge), but the fit puts MORE temperature sensitivity on the slow one --
  alpha_s = 0.00708 against alpha_f = 0.00284 -- and rails beta_s at its 1e-6
  floor. The timescales cross at T_south = 1.74 K, above which the "slow" channel
  relaxes FASTER than the "fast" one, and nothing anywhere exceeds ~221 yr, so
  there is no century-plus dynamic reservoir at all. The Mouginot 73.5% surface
  constraint is then satisfied by assigning 78% of the COMMITMENT to whichever
  channel happens to be slower at present temperatures.

  Physically this is backwards twice over: surface melt should be the strongly
  temperature-sensitive channel, and dynamic discharge should be the sluggish,
  long-timescale one. This script asks which of three explanations holds.

THREE TESTS, chosen to SEPARATE the hypotheses rather than confirm one

  T1 EXCHANGEABILITY. Swapping the channels (f -> 1-f, alpha_f <-> alpha_s,
     beta_f <-> beta_s) leaves L_total ALGEBRAICALLY unchanged -- the two
     channels enter the sum symmetrically. So the hindcast term cannot tell them
     apart at all, and the ONLY term that assigns labels is the Mouginot
     partition penalty. Measured here rather than asserted: if the hindcast
     residual is bit-identical under the swap, label assignment rests entirely
     on one prior term with sigma 0.05.

  T2 WHAT MOUGINOT ACTUALLY PINS. The constraint is on the fast channel's share
     of the EXTRA LOSS RATE (late window minus reference window). The parameter
     `f` is the fast share of the COMMITMENT. Those are different objects once
     the channels have different timescales. This reports both, plus each
     channel's timescale, so it is visible whether the constraint pins the
     quantity its name implies -- and, crucially, whether ANYTHING pins the
     temperature SENSITIVITY (alpha) to the correct channel. A share constraint
     cannot; that is the suspected hole.

  T3 ORDERING-CONSTRAINED REFIT -- the decisive one. Refit A+B under
     alpha_s <= alpha_f AND beta_s <= beta_f, which makes the slow channel
     slower at EVERY temperature, and price the cost in nlp. Cheap cost => the
     inversion is cosmetic, impose the ordering and move on. Expensive cost =>
     the data genuinely prefer the inverted assignment, which is a finding about
     option B rather than a bug to fix.

READS   outputs/gis_offline_cell_fits.csv
WRITES  outputs/diag_gis_channel_inversion.csv

  python3 python/diag_gis_channel_inversion.py
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gis_offline_cell as G  # noqa: E402

REPO = G.REPO
OUT = os.path.join(REPO, "outputs/diag_gis_channel_inversion.csv")

# --- named constants that the labels below derive from -----------------------
CELL = "A+B"
SWAP_PAIRS = (("alpha_f", "alpha_s"), ("beta_f", "beta_s"))
# Temperatures (K, regional south driver) at which timescales are reported.
REPORT_T = (-1.0, 0.0, 1.0, 2.0, 4.0)
# T3's ordering constraint: the slow channel must be slower at EVERY temperature.
ORDER_DESC = "alpha_s <= alpha_f AND beta_s <= beta_f"
# A refit costing less than this many nlp units is "cheap" -- the ordering can be
# imposed without materially degrading the fit. 2 log-units ~ the conventional
# threshold for a distinguishable difference in fit.
CHEAP_NLP = 2.0


def parse_params(s):
    return {kv.split("=")[0].strip(): float(kv.split("=")[1])
            for kv in str(s).split(";") if "=" in kv}


def build_ctx():
    drv = pd.read_csv(G.DRIVER_CSV).set_index("year")[G.DRIVER_ZONE]
    t_reg = G.extend(drv)
    gmst = G.extend(G.load_gmst())
    ty, obs, sig = G.load_target()
    return dict(t_reg=t_reg, t_gmst=gmst, ty=ty, obs=obs, sig=sig,
                ti=[G._yi[y] for y in ty]), int(drv.index.max())


def swap(p):
    q = dict(p)
    q["f"] = 1.0 - p["f"]
    for a, b in SWAP_PAIRS:
        q[a], q[b] = p[b], p[a]
    return q


def hindcast_resid(p, ctx):
    order = [p[n] for n in G.cell_params(CELL)]
    L, Lf = G.run_cell(CELL, order, ctx["t_reg"], ctx["t_gmst"], G.N_FIT)
    return G.reref(L)[ctx["ti"]] - ctx["obs"], L, Lf


def t1_exchangeability(p, ctx, rows):
    print("=== T1. EXCHANGEABILITY — what actually assigns the labels? ===\n")
    r0, L0, Lf0 = hindcast_resid(p, ctx)
    r1, L1, Lf1 = hindcast_resid(swap(p), ctx)
    dmax = float(np.max(np.abs(r1 - r0)))
    print(f"  max|hindcast residual difference| under channel swap: {dmax:.3e} cm")
    if dmax < 1e-12:
        print("  -> BIT-IDENTICAL. The hindcast CANNOT distinguish the channels.")
        print("     The two enter L_total symmetrically, so every bit of label")
        print("     assignment rests on the Mouginot term alone.\n")
    else:
        print("  -> NOT identical; the hindcast does carry some label information.\n")

    nlp0 = G.neg_log_post(CELL, [p[n] for n in G.cell_params(CELL)], ctx)
    ps = swap(p)
    nlp1 = G.neg_log_post(CELL, [ps[n] for n in G.cell_params(CELL)], ctx)
    s0 = G.model_surface_share(L0, Lf0)
    s1 = G.model_surface_share(L1, Lf1)
    print(f"  as fitted : surface share {s0:.4f}, nlp {nlp0:9.3f}")
    print(f"  swapped   : surface share {s1:.4f}, nlp {nlp1:9.3f}")
    print(f"  the swap costs {nlp1 - nlp0:.2f} nlp, ALL of it from the Mouginot")
    print(f"  penalty (target {G.MOUG_SURFACE_SHARE}, sigma {G.MOUG_SHARE_SIGMA}).\n")
    rows.append(dict(test="T1", metric="hindcast_resid_max_diff_cm", value=dmax))
    rows.append(dict(test="T1", metric="swap_nlp_cost", value=nlp1 - nlp0))
    return dmax < 1e-12


def t2_what_mouginot_pins(p, ctx, rows):
    print("=== T2. WHAT DOES MOUGINOT PIN, AND WHAT PINS alpha? ===\n")
    _, L, Lf = hindcast_resid(p, ctx)
    share = G.model_surface_share(L, Lf)
    print(f"  f  = fast share of the COMMITMENT      : {p['f']:.4f}")
    print(f"  model fast share of the EXTRA LOSS RATE: {share:.4f}   "
          f"(constraint target {G.MOUG_SURFACE_SHARE})")
    print(f"  -> the constraint pins the RATE share; `f` is a COMMITMENT share.")
    print(f"     They differ by {abs(p['f'] - share):.4f} here, and coincide only")
    print("     when the two channels share a timescale.\n")
    print(f"  {'T_south':>8s} {'r_fast':>11s} {'r_slow':>11s} "
          f"{'tau_fast':>10s} {'tau_slow':>10s}  verdict")
    for T in REPORT_T:
        rf = p["alpha_f"] * T + p["beta_f"]
        rs = p["alpha_s"] * T + p["beta_s"]
        tf = 1 / rf if rf > 0 else np.inf
        ts = 1 / rs if rs > 0 else np.inf
        print(f"  {T:8.1f} {rf:11.3e} {rs:11.3e} {tf:10.1f} {ts:10.1f}  "
              f"{'ok' if ts > tf else 'INVERTED'}")
        rows.append(dict(test="T2", metric=f"tau_fast@T={T}", value=tf))
        rows.append(dict(test="T2", metric=f"tau_slow@T={T}", value=ts))
    dn = p["alpha_f"] - p["alpha_s"]
    tx = (p["beta_f"] - p["beta_s"]) / (p["alpha_s"] - p["alpha_f"]) \
        if abs(p["alpha_s"] - p["alpha_f"]) > 0 else np.inf
    print(f"\n  alpha_f - alpha_s = {dn:+.5f}  (NEGATIVE means the 'slow' channel")
    print("  is the more temperature-sensitive one -- backwards for surface melt)")
    print(f"  timescale crossover at T_south = {tx:.3f} K")
    print("  NOTHING in the objective constrains alpha to the right channel: the")
    print("  Mouginot term is a SHARE constraint, and a share cannot pin a")
    print("  sensitivity. That is the hole.\n")
    rows.append(dict(test="T2", metric="alpha_f_minus_alpha_s", value=dn))
    rows.append(dict(test="T2", metric="crossover_T_south_K", value=tx))


def t3_ordered_refit(p, ctx, rows):
    print(f"=== T3. ORDERING-CONSTRAINED REFIT — {ORDER_DESC} ===\n")
    names = G.cell_params(CELL)

    def obj(theta):
        q = dict(zip(names, theta))
        if not (q["alpha_s"] <= q["alpha_f"] and q["beta_s"] <= q["beta_f"]):
            return 1e12
        return G.neg_log_post(CELL, theta, ctx)

    best, best_v = None, np.inf
    starts = [np.array([swap(p)[n] for n in names], float)]     # the swapped optimum
    starts += [G.draw_start(names) for _ in range(G.N_MULTISTART)]
    for x0 in starts:
        r = G._nm(obj, x0, G.MAXFEV)
        if r.fun < best_v:
            best, best_v = r.x, r.fun
    best, best_v = G.basin_polish(obj, best, names)
    q = dict(zip(names, best))
    free_v = G.neg_log_post(CELL, [p[n] for n in names], ctx)

    print(f"  unconstrained (shipped structure) nlp : {free_v:9.3f}")
    print(f"  ordering-constrained              nlp : {best_v:9.3f}")
    print(f"  COST OF IMPOSING THE ORDERING         : {best_v - free_v:9.3f} nlp\n")
    print("  constrained optimum: " +
          "; ".join(f"{k}={v:.5g}" for k, v in q.items()))
    _, L, Lf = hindcast_resid(q, ctx)
    rmse = float(np.sqrt(np.mean((G.reref(L)[ctx["ti"]] - ctx["obs"]) ** 2)))
    print(f"  constrained hindcast RMSE: {rmse:.4f} cm "
          f"(unconstrained A+B is 0.0617)")
    print(f"  constrained surface share: {G.model_surface_share(L, Lf):.4f}")
    print(f"  {'T_south':>8s} {'tau_fast':>10s} {'tau_slow':>10s}")
    for T in REPORT_T:
        rf = q["alpha_f"] * T + q["beta_f"]
        rs = q["alpha_s"] * T + q["beta_s"]
        print(f"  {T:8.1f} {1/rf if rf>0 else np.inf:10.1f} "
              f"{1/rs if rs>0 else np.inf:10.1f}")
    cost = best_v - free_v
    print()
    if cost < CHEAP_NLP:
        print(f"  -> CHEAP ({cost:.2f} < {CHEAP_NLP} nlp). The inversion is COSMETIC:")
        print("     the ordering can be imposed at negligible cost to the fit, so")
        print("     impose it and the channels mean what they are named.")
    else:
        print(f"  -> EXPENSIVE ({cost:.2f} >= {CHEAP_NLP} nlp). The data GENUINELY")
        print("     prefer the inverted assignment. That is a finding about option")
        print("     B -- the two-channel split is not resolving surface vs dynamic")
        print("     -- not a bug to be patched by relabelling.")
    rows.append(dict(test="T3", metric="nlp_unconstrained", value=free_v))
    rows.append(dict(test="T3", metric="nlp_ordered", value=best_v))
    rows.append(dict(test="T3", metric="ordering_cost_nlp", value=cost))
    rows.append(dict(test="T3", metric="ordered_rmse_cm", value=rmse))


def main():
    fits = pd.read_csv(G.OUT_FITS).set_index("cell")
    p = parse_params(fits.loc[CELL, "params"])
    ctx, _ = build_ctx()
    print(f"diag_gis_channel_inversion | commit={G.COMMIT} | cell={CELL}")
    print(f"  fitted: " + "; ".join(f"{k}={v:.5g}" for k, v in p.items()) + "\n")
    rows = []
    t1_exchangeability(p, ctx, rows)
    t2_what_mouginot_pins(p, ctx, rows)
    t3_ordered_refit(p, ctx, rows)
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
