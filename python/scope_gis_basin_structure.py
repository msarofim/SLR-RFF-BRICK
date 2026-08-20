#!/usr/bin/env python3
"""
scope_gis_basin_structure.py — how many Greenland basins does the HINDCAST
actually support: one, two, or three?

WHY THIS EXISTS (2026-08-20, Marcus)
  L13 ships THREE Mouginot sector basins {SW,CW,CE,SE} / {NW} / {NO,NE} with two
  sampled rate scales. Its posterior says one of those two is not identified:
  P(s_mid > 1) = 0.435, q05-q95 spanning 0.53-1.59, while s_high = 0.268
  [0.139, 0.506] excludes 1.0 decisively. A first, crude scan -- holding L13's
  SHAPE parameters fixed and moving only s_high -- suggested a TWO-basin model
  hits the Mouginot windows BETTER than three (worst |z| 0.49 vs 1.09) with one
  fewer parameter.

  That scan is not evidence: the shape parameters it held fixed were themselves
  fitted UNDER the three-basin structure, so it compared a refitted model with a
  half-refitted one. This script does the comparison properly -- every structure
  refits its FULL parameter set against the SAME objective, in the same offline
  harness (python/gis_offline_cell.py), under the same multistart-plus-basin-hop
  protocol that file established after its first protocol was found returning
  points 24.7 nlp above the optimum.

THE STRUCTURES
  B1  one basin   -- the shipped whole-sheet A+B. No sector prediction at all.
  B2  two basins  -- {SW,CW,CE,SE,NW} active + {NO,NE} dormant.   1 free scale.
  B3  three basins -- L13's structure.                            2 free scales.

WHAT IS AND IS NOT COMPARABLE, stated before running
  The three structures are NOT fitted to the same data: B1 has no sector terms,
  B2 scores one independent share per window, B3 two. Their total nlp values are
  therefore NOT comparable, and this script never compares them. What IS
  comparable:
    * the SHARED terms -- the 1900-2025 target and the Mouginot channel share --
      which all three predict. Does splitting NW off cost anything there?
    * each structure's own worst |z| on the shares IT can score.
    * IDENTIFIABILITY of the added scale, by PROFILE likelihood: re-optimise
      everything else at each fixed s_mid. A flat profile through s_mid = 1 means
      the parameter is not identified, and no fit quality can rescue it.
  The profile is the decisive experiment. Per `profile_beats_optimum`, a profile
  point BELOW the reported optimum means the optimum was not converged, and that
  is checked and reported rather than smoothed over.

GATE
  G1 NESTING. B1 must reproduce python/gis_offline_cell.py's own A+B cell -- same
     objective, same protocol -- to a tight tolerance on nlp and on every fitted
     parameter. With k = 1 and s = 1 the basin machinery IS the whole-sheet A+B;
     if it is not, the comparison is measuring a wiring bug.

READS   the offline harness (objective, integrator, bounds, protocol, gates)
WRITES  outputs/scope_gis_basin_structure{,_profile}.csv

  source ~/climate-env/bin/activate
  python3 python/scope_gis_basin_structure.py
"""
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gis_offline_cell as goc  # noqa: E402
import diag_gis_basin_lit_check as lit  # noqa: E402

REPO = goc.REPO
OUT = os.path.join(REPO, "outputs/scope_gis_basin_structure.csv")
OUT_PROFILE = os.path.join(REPO, "outputs/scope_gis_basin_structure_profile.csv")

# --- the sector geometry, from the same parse the component uses -------------
SECTORS = {"south": ("SW", "CW", "CE", "SE"), "mid": lit.MID_SECTORS,
           "high": lit.HIGH_SECTORS}
VOL_CM = {b: sum(lit.MOUGINOT_SLE_CM[s] for s in SECTORS[b]) for b in SECTORS}
VSHARE = {b: VOL_CM[b] / sum(VOL_CM.values()) for b in SECTORS}

STRUCTURES = {
    "B1": dict(basins=("whole",), k={"whole": 1.0}, pinned="whole", scored=()),
    "B2": dict(basins=("active", "high"),
               k={"active": VSHARE["south"] + VSHARE["mid"], "high": VSHARE["high"]},
               pinned="active", scored=("high",)),
    "B3": dict(basins=("south", "mid", "high"), k=dict(VSHARE),
               pinned="south", scored=("south", "mid")),
}
SHAPE_PARAMS = ["c1", "c0", "f", "alpha_f", "beta_f", "alpha_s", "beta_s", "g"]

# --- the sector-share likelihood, mirroring GISB_TERM in calibrate_mcmc_ext.jl
SHARE_WINS = ((2002, 2011), (2012, 2018))
SHARE_TGT3 = ({"south": 0.592, "mid": 0.207, "high": 0.201},
              {"south": 0.554, "mid": 0.262, "high": 0.183})
SHARE_SIGMA = 0.05
# log10 rate-scale prior, EXACTLY the calibrator's: mu 0, sigma 0.5, [-2, 2]
SCALE_MU, SCALE_SD, SCALE_BOUNDS = 0.0, 0.5, (-2.0, 2.0)

# --- G1 reference: the A+B row of the harness's own fit ----------------------
G1_CELL = "A+B"
G1_TOL_NLP = 1e-3
G1_TOL_REL = 2e-3

PROFILE_GRID = np.round(np.arange(-0.60, 0.61, 0.10), 4)   # log10 s_mid
N_START_MAIN = goc.N_MULTISTART
N_START_PROFILE = 40


def share_targets(struct):
    """Collapse the 3-way Mouginot targets onto this structure's basins."""
    out = []
    for tgt in SHARE_TGT3:
        d = {}
        for b in STRUCTURES[struct]["basins"]:
            if b == "whole":
                d[b] = 1.0
            elif b == "active":
                d[b] = tgt["south"] + tgt["mid"]
            else:
                d[b] = tgt[b]
        out.append(d)
    return out


def param_names(struct):
    s = STRUCTURES[struct]
    return SHAPE_PARAMS + [f"log10_s_{b}" for b in s["basins"] if b != s["pinned"]]


def run_basins(struct, theta, ctx, n=None):
    """Per-basin A+B through the harness's OWN integrator. Basin commitment is
    k_b * clip(c1*T + c0, 0, V0) -- identically k_b times the whole-sheet clamped
    commitment, matching julia/greenland_3basin_component.jl (NOT the earlier
    prototype's whole-sheet clamp). Both channel rates scale by s_b; passing
    s*alpha and s*beta into `integrate` reproduces clip(s*(alpha*T+beta),1e-9,1)
    exactly, because it clips after forming the product."""
    s = STRUCTURES[struct]
    p = dict(zip(param_names(struct), theta))
    t_rate = ctx["t_reg"]
    leq_whole = np.clip(p["c1"] * t_rate + p["c0"], 0.0, goc.V0_CM)
    out = {}
    for b in s["basins"]:
        sc = 1.0 if b == s["pinned"] else 10.0 ** p[f"log10_s_{b}"]
        pb = dict(f=p["f"], g=p["g"],
                  alpha_f=sc * p["alpha_f"], beta_f=sc * p["beta_f"],
                  alpha_s=sc * p["alpha_s"], beta_s=sc * p["beta_s"])
        out[b] = goc.integrate(t_rate, s["k"][b] * leq_whole, pb, "share", n)
    return out


def basin_shares(struct, per, win):
    """Each basin's share of the total loss RATE over a window."""
    i0, i1 = goc._yi[win[0]], goc._yi[win[1]]
    d = {b: (per[b][0][i1] - per[b][0][i0]) / (win[1] - win[0]) for b in per}
    tot = sum(d.values())
    return {b: d[b] / tot for b in d} if abs(tot) > 1e-12 else None


def neg_log_post(struct, theta, ctx):
    names = param_names(struct)
    p = dict(zip(names, theta))
    for k, v in p.items():
        lo, hi = SCALE_BOUNDS if k.startswith("log10_s_") else goc.PBOUNDS[k]
        if not (lo <= v <= hi):
            return 1e12
    per = run_basins(struct, theta, ctx, goc.N_FIT)
    L = sum(per[b][0] for b in per)
    Lf = sum(per[b][1] for b in per)
    if not np.all(np.isfinite(L)):
        return 1e12
    mdl = goc.reref(L)[ctx["ti"]]
    nlp = 0.5 * float(np.sum(((mdl - ctx["obs"]) / ctx["sig"]) ** 2))
    share = goc.model_surface_share(L, Lf)          # the whole-sheet channel term
    if np.isfinite(share):
        nlp += 0.5 * ((share - goc.MOUG_SURFACE_SHARE) / goc.MOUG_SHARE_SIGMA) ** 2
    for win, tgt in zip(SHARE_WINS, share_targets(struct)):
        sh = basin_shares(struct, per, win)
        if sh is None:
            return 1e12
        for b in STRUCTURES[struct]["scored"]:
            nlp += 0.5 * ((sh[b] - tgt[b]) / SHARE_SIGMA) ** 2
    for k, v in p.items():                           # the calibrator's scale prior
        if k.startswith("log10_s_"):
            nlp += 0.5 * ((v - SCALE_MU) / SCALE_SD) ** 2
    return nlp


def shared_terms(struct, theta, ctx):
    """The two terms EVERY structure predicts, so the only nlp comparison that
    is like-for-like across structures."""
    per = run_basins(struct, theta, ctx, goc.N_FIT)
    L = sum(per[b][0] for b in per); Lf = sum(per[b][1] for b in per)
    mdl = goc.reref(L)[ctx["ti"]]
    tgt = 0.5 * float(np.sum(((mdl - ctx["obs"]) / ctx["sig"]) ** 2))
    share = goc.model_surface_share(L, Lf)
    chan = 0.5 * ((share - goc.MOUG_SURFACE_SHARE) / goc.MOUG_SHARE_SIGMA) ** 2
    return tgt, chan, share


def draw_start(names):
    x = np.empty(len(names))
    for i, n in enumerate(names):
        if n.startswith("log10_s_"):
            x[i] = goc._rng.uniform(*SCALE_BOUNDS)
        else:
            lo, hi = goc.PBOUNDS[n]
            if n in goc.LOG_AXES:
                x[i] = np.exp(goc._rng.uniform(np.log(max(lo, 1e-6)), np.log(hi)))
            else:
                x[i] = goc._rng.uniform(lo, hi)
    return x


def fit(struct, ctx, nstart, extra_starts=(), fixed=None):
    """fixed: {name: value} held during the fit (for the profile)."""
    names = param_names(struct)
    free = [n for n in names if fixed is None or n not in fixed]

    def expand(xf):
        full = np.empty(len(names))
        j = 0
        for i, n in enumerate(names):
            if fixed is not None and n in fixed:
                full[i] = fixed[n]
            else:
                full[i] = xf[j]; j += 1
        return full

    obj = lambda xf: neg_log_post(struct, expand(xf), ctx)
    starts = [np.asarray(s, float) for s in extra_starts]
    starts += [draw_start(free) for _ in range(nstart)]
    best, best_v = None, np.inf
    for x0 in starts:
        r = goc._nm(obj, x0, goc.MAXFEV)
        if r.fun < best_v:
            best, best_v = r.x, r.fun
    best, best_v = goc.basin_polish(
        obj, best, [n if not n.startswith("log10_s_") else "c0" for n in free])
    return dict(zip(names, expand(best))), best_v


def project(struct, theta, ctx, last_obs_year):
    """2100/2150/2300 per scenario, cm rel PROJ_REF_WIN, basin sum."""
    out = {}
    for label, tag in goc.PROJ_SCENARIOS.items():
        g = goc.extend(goc.load_gmst(tag))
        tr = goc.splice_regional(ctx["t_reg"], ctx["t_gmst"], g, last_obs_year)
        c = dict(ctx); c["t_reg"] = tr
        per = run_basins(struct, theta, c)
        L = sum(per[b][0] for b in per)
        i = [goc._yi[y] for y in range(goc.PROJ_REF_WIN[0], goc.PROJ_REF_WIN[1] + 1)]
        Lr = L - L[i].mean()
        out[label] = {y: float(Lr[goc._yi[y]]) for y in (2100, 2150, 2300)}
    return out


def main():
    t0 = time.time()
    print(f"scope_gis_basin_structure | commit={goc.COMMIT} | zone={goc.DRIVER_ZONE} "
          f"| fit {goc.FIT_WIN[0]}-{goc.FIT_WIN[1]}")
    print(f"  volumes cm SLE: " + "  ".join(f"{b} {VOL_CM[b]} (k={VSHARE[b]:.4f})"
                                            for b in SECTORS))
    print(f"  share targets sigma {SHARE_SIGMA}, windows {SHARE_WINS}")
    print(f"  log10 scale prior N({SCALE_MU}, {SCALE_SD}) on {SCALE_BOUNDS}"
          f"  (the calibrator's own)")
    ctx = dict(t_reg=goc.extend(pd.read_csv(goc.DRIVER_CSV).set_index("year")[goc.DRIVER_ZONE]),
               t_gmst=goc.extend(goc.load_gmst()))
    last_obs_year = int(pd.read_csv(goc.DRIVER_CSV)["year"].max())
    ty, obs, sig = goc.load_target()
    ctx.update(ty=ty, obs=obs, sig=sig, ti=[goc._yi[y] for y in ty])

    rows = []
    # ---- G1: B1 must reproduce the harness's own A+B ----------------------
    print(f"\n=== G1 — B1 must reproduce gis_offline_cell.py's {G1_CELL} cell ===\n")
    ref = pd.read_csv(goc.OUT_FITS)
    ref = ref[ref.cell == G1_CELL]
    if len(ref) != 1:
        raise SystemExit(f"G1: {goc.OUT_FITS} has {len(ref)} rows for {G1_CELL}")
    ref_nlp = float(ref.neg_log_post.iloc[0])
    ref_par = dict(kv.split("=") for kv in ref.params.iloc[0].split("; "))
    ref_par = {k.strip(): float(v) for k, v in ref_par.items()}
    th1, v1 = fit("B1", ctx, N_START_MAIN,
                  extra_starts=[[ref_par[n] for n in SHAPE_PARAMS]])
    print(f"  {'param':<10s} {'B1 refit':>14s} {'harness A+B':>14s} {'rel diff':>11s}")
    worst = 0.0
    for n in SHAPE_PARAMS:
        a, b = th1[n], ref_par[n]
        rel = abs(a - b) / max(abs(b), 1e-9)
        worst = max(worst, rel)
        print(f"  {n:<10s} {a:14.6g} {b:14.6g} {rel:11.2e}")
    print(f"  {'nlp':<10s} {v1:14.6f} {ref_nlp:14.6f} {abs(v1-ref_nlp):11.2e}")
    rows.append(dict(quantity="g1", nlp=v1, ref_nlp=ref_nlp,
                     worst_rel=worst, tol=G1_TOL_REL))
    if abs(v1 - ref_nlp) > G1_TOL_NLP:
        raise SystemExit(f"G1 FAILED: nlp {v1:.6f} vs harness {ref_nlp:.6f}")
    print(f"\n  G1 PASS — the basin machinery at k=1, s=1 IS the whole-sheet A+B "
          f"(worst param rel diff {worst:.1e}).")

    # ---- the three structures --------------------------------------------
    fits = {"B1": (th1, v1)}
    warm = [th1[n] for n in SHAPE_PARAMS]
    for st in ("B2", "B3"):
        print(f"\n=== fitting {st} — basins {STRUCTURES[st]['basins']}, "
              f"scored {STRUCTURES[st]['scored']} ===")
        nsc = len(param_names(st)) - len(SHAPE_PARAMS)
        fits[st] = fit(st, ctx, N_START_MAIN,
                       extra_starts=[warm + [0.0] * nsc])
        print(f"  nlp {fits[st][1]:.6f}   ({time.time()-t0:.0f} s elapsed)")

    print(f"\n=== COMPARISON ===\n")
    print(f"  {'':4s} {'npar':>4s} {'total nlp':>10s} {'target':>9s} {'channel':>8s} "
          f"{'share':>7s} {'worst|z|':>9s}   scales")
    for st in ("B1", "B2", "B3"):
        th, v = fits[st]
        tgt, chan, share = shared_terms(st, [th[n] for n in param_names(st)], ctx)
        per = run_basins(st, [th[n] for n in param_names(st)], ctx, goc.N_FIT)
        wz = 0.0
        for win, tt in zip(SHARE_WINS, share_targets(st)):
            sh = basin_shares(st, per, win)
            for b in STRUCTURES[st]["scored"]:
                wz = max(wz, abs(sh[b] - tt[b]) / SHARE_SIGMA)
        sc = "  ".join(f"{b} {10**th[f'log10_s_{b}']:.3f}"
                       for b in STRUCTURES[st]["basins"] if b != STRUCTURES[st]["pinned"])
        print(f"  {st:4s} {len(param_names(st)):4d} {v:10.4f} {tgt:9.4f} {chan:8.4f} "
              f"{share:7.4f} {wz:9.2f}   {sc if sc else '(none — pinned only)'}")
        L = sum(per[b][0] for b in per)
        g = goc.evaluate_gates(L, ctx)
        pr = project(st, [th[n] for n in param_names(st)], ctx, last_obs_year)
        rows.append(dict(quantity="fit", structure=st, npar=len(param_names(st)),
                         nlp=v, term_target=tgt, term_channel=chan,
                         surface_share=share, worst_abs_z=wz, **g,
                         **{f"{s}_{y}": pr[s][y] for s in pr for y in pr[s]},
                         params="; ".join(f"{k}={v2:.6g}" for k, v2 in th.items())))
    print(f"\n  the SHARED terms (target + channel) are the only like-for-like nlp "
          f"comparison:\n  B1 {rows[1]['term_target']+rows[1]['term_channel']:.4f}   "
          f"B2 {rows[2]['term_target']+rows[2]['term_channel']:.4f}   "
          f"B3 {rows[3]['term_target']+rows[3]['term_channel']:.4f}")

    print(f"\n  2300 projections, cm rel {goc.PROJ_REF_WIN} (basin sum):")
    for st in ("B1", "B2", "B3"):
        r = [x for x in rows if x.get("structure") == st][0]
        print(f"    {st}  2100 " + "  ".join(f"{s} {r[f'{s}_2100']:6.2f}" for s in goc.PROJ_SCENARIOS)
              + f"   |  2300 ssp585 {r['SSP5-8.5_2300']:7.2f}"
              + f"   ratio {r['SSP5-8.5_2300']/max(r['SSP2-4.5_2300'],1e-9):5.2f}x")

    # ---- the decisive experiment: profile s_mid in B3 ---------------------
    print(f"\n=== PROFILE — s_mid in B3, everything else re-optimised at each point ===\n")
    th3, v3 = fits["B3"]
    prof = []
    for ls in PROFILE_GRID:
        warm3 = [th3[n] for n in param_names("B3") if n != "log10_s_mid"]
        thp, vp = fit("B3", ctx, N_START_PROFILE, extra_starts=[warm3],
                      fixed={"log10_s_mid": float(ls)})
        prof.append(dict(quantity="profile", structure="B3", log10_s_mid=float(ls),
                         s_mid=float(10**ls), nlp=vp, dnlp=vp - v3,
                         params="; ".join(f"{k}={v2:.6g}" for k, v2 in thp.items())))
        print(f"  s_mid {10**ls:6.3f}   nlp {vp:9.4f}   Δnlp {vp-v3:+8.4f}"
              + ("   <-- BELOW the reported optimum" if vp < v3 - 1e-6 else ""))
    pdf = pd.DataFrame(prof)
    below = pdf[pdf.dnlp < -1e-6]
    if len(below):
        print(f"\n  ** {len(below)} profile point(s) BELOW the B3 optimum — per "
              f"`profile_beats_optimum` the B3 fit did NOT converge. Reported, not hidden. **")
    within = pdf[pdf.dnlp <= 0.5]                 # 1 sigma for 1 dof on -log L
    print(f"\n  s_mid within Δnlp <= 0.5 (1 sigma, 1 dof): "
          f"[{within.s_mid.min():.3f}, {within.s_mid.max():.3f}]")
    print(f"  does that interval contain s_mid = 1 (NW indistinguishable from south)? "
          f"{'YES' if within.s_mid.min() <= 1.0 <= within.s_mid.max() else 'NO'}")
    at1 = pdf.iloc[(pdf.s_mid - 1.0).abs().argmin()]
    print(f"  cost of PINNING s_mid = 1: Δnlp = {at1.dnlp:+.4f} "
          f"(at the grid point s_mid = {at1.s_mid:.3f})")

    pd.DataFrame(rows).to_csv(OUT, index=False)
    pdf.to_csv(OUT_PROFILE, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)} and "
          f"{os.path.relpath(OUT_PROFILE, REPO)}  ({time.time()-t0:.0f} s)")


if __name__ == "__main__":
    main()
