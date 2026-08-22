"""LEAVE-ONE-GCM-OUT PROPAGATED THROUGH THE WHOLE GREENLAND SCORECARD.

WHY. Handoff 2026-08-22 section 7 says "35/35 runs is not p = 2^-35; cluster by GCM".
The 2026-08-22c review found the same trap one level up: the r2300 RATE band's p05 IS
the lowest per-GCM median, so dropping MPI-ESM1-2-HR killed all 7 surviving cells. A
follow-up showed the LEVEL bands are no better -- worst edge shift on one GCM drop is
32-33 % of band width on ssp585 r2300, 94 % on ssp585 x2300, 85-88 % on the two cool
r2300 arms, and ssp126 x2300 is a SINGLE GCM whose 0.9 cm "band" is ISM percentile
spread. Every verdict in this arc is scored against those bands. This re-prices them
all against the same drop.

WHAT IS RE-PRICED, per dropped GCM
  * the shipped counts 135 / 86 at w = 1
  * the 1080-cell ladder: pass_2150 -> + r2300 rate -> + x2300 rate
  * WHICH CELL WINS, and its psi
  * the k = 2-3 (ssp585 shape) vs k <= 1.0 (cool levels) TENSION -- the argmin of the
    k grid on each arm group, which is the disagreement the whole commitment-law
    step-back rests on

WHAT MOVES AND WHAT IS HELD -- the one stated approximation
  The PROTECT LEVEL bands, the RATE bands and the MATCHED-2300 anchor QUANTILES are
  all rebuilt from the reduced run set: those are pure SLR quantiles and the drop is
  exact. The MATCHED bands' PCHIP PREDICTOR -- each anchor's 2015-2300 GSAT integral
  -- is HELD at its full-ensemble value, because per-GCM GSAT is not on disk (the
  protect_*_forcing_gmst.csv files are already n-weighted composites; rebuilding them
  means re-running scope_gis_cool_band_forcing.py against raw CMIP6). This is the
  SMALLER error of the two -- within one arm every GCM follows the same scenario, so
  the forcing-integral spread is far narrower than the SLR-response spread -- but it
  is an approximation and it is stated, not hidden.

  ssp126 x2300 has exactly ONE GCM (CESM2-WACCM). Dropping it EMPTIES that arm; the
  arm is then excluded from the aggregates and the exclusion is printed, not silently
  averaged over.

WRITES outputs/diag_gis_scorecard_logo.csv
  python3 python/diag_gis_scorecard_logo.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
os.chdir(REPO)

import scope_gis_shape_all_scenarios as A  # noqa: E402
from scope_gis_ridge_vs_protect import basin2_series, rebase_cm  # noqa: E402
from scope_gis_leq_ridge_vs_literature import gis_tbar  # noqa: E402
from scope_gis_2300_relaxation import (  # noqa: E402
    DRIVER_BASE, YEARS, gis_shape_table, regional_driver,
)
from build_gis_matched_targets import interp_log, QCOLS, BAND_LO, BAND_HI  # noqa: E402
import gis_targets  # noqa: E402
import scope_gis_reservoir_offline as R  # noqa: E402
import scope_gis_reservoir_rate_rank as RR  # noqa: E402

OUT = os.path.join(REPO, "outputs/diag_gis_scorecard_logo.csv")

# --- named constants ---------------------------------------------------------
TAG, HIND, HORIZONS, ARMS = A.TAG, A.HIND, A.HORIZONS, A.ARMS
SSP585_ARMS, COOL_ARMS = A.SSP585_ARMS, A.COOL_ARMS
K_GRID, OURS = A.K_GRID, R.OURS
RES_TAU, RES_ONSET_K, RES_V_M = R.RES_TAU, R.RES_ONSET_K, R.RES_V_M
RAMP_W_GRID, RAMP_W_SHIPPED = RR.RAMP_W_GRID, RR.RAMP_W_SHIPPED
CM_PER_M, V_MAX_M, Y2100_TOL_CM = R.CM_PER_M, R.V_MAX_M, R.Y2100_TOL_CM
RATE_WIN, RATE_Q, RATE_ARMS = RR.RATE_WIN, RR.RATE_Q, RR.RATE_ARMS
SHIPPED_ALL_PASS, SHIPPED_2150 = RR.SHIPPED_ALL_PASS, RR.SHIPPED_2150
ANCHOR_SRC = os.path.join(REPO, "outputs/scope_gis_cool_band_targets.csv")
PRED, PRED_OURS = "gmst_int_theirs_Kyr", "gmst_int_ours_Kyr"
BASELINE = "(none) FULL ENSEMBLE"
## ACCESS1.3 is ALREADY excluded by A.protect_band (A.DROP_GCM), so dropping it must
## be an exact no-op. It is kept in the sweep as a NULL CONTROL on the drop machinery.
NULL_CONTROL = A.DROP_GCM
MATCHED_REPRO_TOL_CM = 0.05      # the baseline rebuild vs the shipped gis_targets
K_FIXED = 1.0


def bands_from(ann_v):
    """Every band the scorecard uses, rebuilt from one run set. Returns
    (level bands, rate bands, matched 2300 bands, list of arms that emptied)."""
    lvl, rate, empty = {}, {}, []
    for ssp, lab, fam, _ in ARMS:
        sub = ann_v[(ann_v.ssp == lab) & ann_v.exp.str.contains(fam)
                    & ~ann_v.exp.str.startswith(A.DROP_GCM)]
        if sub.empty:
            empty.append(f"{lab} {fam}")
            continue
        q = sub.groupby("year").gis_cm
        lvl[(ssp, fam)] = {y: (q.quantile(.05)[y], q.median()[y], q.quantile(.95)[y])
                           for y in HORIZONS}
        w = sub[sub.year.isin(RATE_WIN)].pivot_table(
            index=["group", "model", "exp"], columns="year", values="gis_cm")
        pr = ((w[RATE_WIN[1]] - w[RATE_WIN[0]])
              / (RATE_WIN[1] - RATE_WIN[0]) * 100.0).dropna()
        rate[(ssp, fam)] = (pr.quantile(RATE_Q[0]), pr.median(), pr.quantile(RATE_Q[1]))

    ## MATCHED 2300: anchor QUANTILES rebuilt from ann_v, PCHIP PREDICTOR held (see
    ## the module docstring -- the one stated approximation).
    t = pd.read_csv(ANCHOR_SRC).copy()
    keep = []
    for i, r in t.iterrows():
        sub = ann_v[(ann_v.ssp == r.label) & ann_v.exp.str.contains(r.family)
                    & ~ann_v.exp.str.startswith(A.DROP_GCM) & (ann_v.year == 2300)]
        if sub.empty:
            continue
        for c, qq in zip(QCOLS, (.05, .17, .50, .83, .95)):
            t.at[i, c] = float(sub.gis_cm.quantile(qq))
        keep.append(i)
    t = t.loc[keep]
    matched = {}
    for ssp, lab in OURS:
        oi = float(t.loc[t.label == lab, PRED_OURS].iloc[0])
        lo_a, hi_a = t[PRED].min(), t[PRED].max()
        v_lo, ex = interp_log(t[PRED], t[BAND_LO], oi)
        v_hi, _ = interp_log(t[PRED], t[BAND_HI], oi)
        if ex:      # outside the hull -> the builder's UNION rule
            if oi < lo_a:
                near = t[t[PRED] <= t[t[PRED] > lo_a][PRED].min()]
            else:
                near = t[t[PRED] >= t[t[PRED] < hi_a][PRED].max()]
            v_lo, v_hi = float(near[BAND_LO].min()), float(near[BAND_HI].max())
        matched[lab] = (v_lo, v_hi)
    return lvl, rate, matched, empty


def main():
    post = pd.read_csv(A.POST)
    tbar = gis_tbar()
    r_s = np.exp(post["gis_slow_ell"].to_numpy())
    post["gis_alpha_s"] = post["gis_slow_w"].to_numpy() * r_s / tbar
    post["gis_beta_s"] = (1.0 - post["gis_slow_w"].to_numpy()) * r_s
    S_tab = gis_shape_table()
    ibd = (YEARS >= DRIVER_BASE[0]) & (YEARS <= DRIVER_BASE[1])
    idx = {y: int(np.where(YEARS == y)[0][0])
           for y in tuple(HORIZONS) + tuple(HIND) + (2015,) + RATE_WIN}

    def load(path, col):
        g = pd.read_csv(path).set_index("year")[col].reindex(YEARS).to_numpy()
        rb = g - g[ibd].mean()
        return rb, regional_driver(rb, post["gis_amp"].to_numpy(), S_tab)

    gmst, drivers = {}, {}
    for ssp, lab, fam, stem in ARMS:
        gmst[(ssp, fam)], drivers[(ssp, fam)] = load(
            f"outputs/{stem}.csv", f"gmst_{A.ARM}")
    ours_gmst, ours_drv = {}, {}
    for ssp, lab in OURS:
        ours_gmst[lab], ours_drv[lab] = load(
            f"data/observations/fair_mean_gmst_{ssp}.csv", "gmst_C")

    tgt = pd.read_csv(A.TARGETS).set_index("year")["gis"]
    want_cm = float(tgt.loc[HIND[1]] - tgt.loc[HIND[0]])

    def model_at(k):
        """The MODEL is band-independent, so it is solved ONCE per k and re-scored
        against every band variant. That is what makes this diagnostic cheap."""
        Th = drivers[A.HIND_ARM]
        lo, hi = np.full(len(post), 1e-4), np.full(len(post), 1e3)
        for _ in range(80):
            mid = np.sqrt(lo * hi)
            L = basin2_series(Th, post, k, mid)
            below = 100.0 * (L[:, idx[HIND[1]]] - L[:, idx[HIND[0]]]) < want_cm
            lo, hi = np.where(below, mid, lo), np.where(below, hi, mid)
        s = np.sqrt(lo * hi)
        ba = {kk: np.median(rebase_cm(basin2_series(v, post, k, s)), axis=0)
              for kk, v in drivers.items()}
        bo = {kk: np.median(rebase_cm(basin2_series(v, post, k, s)), axis=0)
              for kk, v in ours_drv.items()}
        return ba, bo

    print(f"diag_gis_scorecard_logo — leave-one-GCM-out across the whole scorecard, "
          f"{TAG}, {len(post)} draws\n")
    print(f"solving the model on the {len(K_GRID)}-point k grid (band-independent, "
          f"done once) ...", flush=True)
    models = {k: model_at(k) for k in K_GRID}
    base_arm, base_ours = models[K_FIXED]

    ## the reservoir adds, cached: also band-independent
    cache = {}
    for on in RES_ONSET_K:
        for tau in RES_TAU:
            for w in RAMP_W_GRID:
                for kk, g in list(gmst.items()) + [(("OURS", lab), ours_gmst[lab])
                                                   for _, lab in OURS]:
                    cache[(on, tau, w, kk)] = RR.reservoir_unit_w(g, on, tau, w)

    ann = pd.read_csv(A.ANN)
    ann["gcm"] = ann.exp.str.split("_").str[0]
    gcms = sorted(set(ann.gcm))
    offs = float(np.median(rebase_cm(
        basin2_series(drivers[("ssp585", "r2300")], post, 1.0, 1.0))[:, idx[2015]]))

    def score_variant(lvl, rate, matched, empty):
        live = [a for a in ARMS if f"{a[1]} {a[3 - 2]}" not in empty
                and (a[0], a[2]) in lvl]
        b = {kk: {y: (v[y][0] + offs, v[y][1] + offs, v[y][2] + offs)
                  for y in HORIZONS} for kk, v in lvl.items()}

        def rms(ba, arms):
            per = []
            for ssp, lab, fam, _ in arms:
                if (ssp, fam) not in b:
                    continue
                L = ba[(ssp, fam)]
                per.append(np.mean([np.log(max(L[idx[y]], 1e-6) / b[(ssp, fam)][y][1]) ** 2
                                    for y in HORIZONS]))
            return float(np.sqrt(np.mean(per))) if per else np.nan

        def rms_add(ba, add, arms):
            per = []
            for ssp, lab, fam, _ in arms:
                if (ssp, fam) not in b:
                    continue
                L = ba[(ssp, fam)] + add[(ssp, fam)]
                per.append(np.mean([np.log(max(L[idx[y]], 1e-6) / b[(ssp, fam)][y][1]) ** 2
                                    for y in HORIZONS]))
            return float(np.sqrt(np.mean(per))) if per else np.nan

        rall_0 = rms(base_arm, live)
        rows = []
        for V in RES_V_M:
            for on in RES_ONSET_K:
                for tau in RES_TAU:
                    for w in RAMP_W_GRID:
                        aa = {(a[0], a[2]): CM_PER_M * V * cache[(on, tau, w, (a[0], a[2]))]
                              for a in ARMS}
                        rall = rms_add(base_arm, aa, live)
                        ok2300 = ok2100 = True
                        for _, lab in OURS:
                            v23 = base_ours[lab][idx[2300]] + \
                                CM_PER_M * V * cache[(on, tau, w, ("OURS", lab))][idx[2300]]
                            ok2300 &= matched[lab][0] <= v23 <= matched[lab][1]
                            ok2100 &= abs(CM_PER_M * V *
                                          cache[(on, tau, w, ("OURS", lab))][idx[2100]]) \
                                < Y2100_TOL_CM
                        ok2150 = all(
                            b[(a[0], a[2])][2150][0]
                            <= base_arm[(a[0], a[2])][idx[2150]] + aa[(a[0], a[2])][idx[2150]]
                            <= b[(a[0], a[2])][2150][2]
                            for a in SSP585_ARMS if (a[0], a[2]) in b)
                        shipped = bool(ok2300 and ok2100 and V <= V_MAX_M and rall < rall_0)
                        rr = {}
                        for a in RATE_ARMS:
                            kk = (a[0], a[2])
                            if kk not in rate:
                                continue
                            L = base_arm[kk] + aa[kk]
                            v = (L[idx[RATE_WIN[1]]] - L[idx[RATE_WIN[0]]]) / \
                                (RATE_WIN[1] - RATE_WIN[0]) * 100.0
                            rr[kk] = rate[kk][0] <= v <= rate[kk][2]
                        rows.append(dict(
                            V_m=V, onset_K=on, tau_yr=tau, ramp_w_K=w,
                            psi=CM_PER_M * V / tau, rms_all=rall,
                            pass_shipped=shipped, pass_2150=bool(shipped and ok2150),
                            pass_rate_r=bool(shipped and ok2150
                                             and rr.get(("ssp585", "r2300"), False)),
                            pass_rate_all=bool(shipped and ok2150 and all(rr.values()))))
        g = pd.DataFrame(rows)
        kk_arg = {}
        for nm, arms in (("ssp585", SSP585_ARMS), ("cool", COOL_ARMS)):
            sc = {k: rms(models[k][0], [a for a in arms if (a[0], a[2]) in b])
                  for k in K_GRID}
            sc = {k: v for k, v in sc.items() if not np.isnan(v)}
            kk_arg[nm] = min(sc, key=sc.get) if sc else np.nan
        return g, kk_arg, live

    ## GATE 1 — the baseline rebuild must reproduce the SHIPPED matched bands. Without
    ## this the whole sweep could be measuring a broken rebuild rather than the drop.
    _, _, m0, _ = bands_from(ann)
    worst = max(max(abs(m0[lab][0] - 100 * gis_targets.MATCHED_2300_M[lab][0]),
                    abs(m0[lab][1] - 100 * gis_targets.MATCHED_2300_M[lab][1]))
                for _, lab in OURS)
    print(f"GATE — baseline matched-band rebuild vs the shipped gis_targets: "
          f"max |diff| {worst:.4f} cm")
    if worst > MATCHED_REPRO_TOL_CM:
        sys.exit(f"GATE FAILED ({worst:.3f} cm): the rebuild is not the shipped "
                 f"construction, so every drop below measures the rebuild, not the drop.")
    print(f"  reproduces to < {MATCHED_REPRO_TOL_CM:g} cm => the drops are the only "
          f"thing moving.\n")

    recs = []
    print(f"\n{'dropped GCM':22}{'135':>6}{'86':>6}{'2150':>7}{'+rate_r':>9}"
          f"{'+rate_x':>9}{'best psi':>10}{'k*585':>7}{'k*cool':>8}   arms lost")
    for g in [None] + gcms:
        ann_v = ann if g is None else ann[ann.gcm != g]
        lvl, rate, matched, empty = bands_from(ann_v)
        gg, karg, live = score_variant(lvl, rate, matched, empty)
        ship = gg[gg.ramp_w_K == RAMP_W_SHIPPED]
        surv = gg[gg.pass_rate_r]
        bpsi = (surv.loc[surv.rms_all.idxmin()].psi if len(surv) else np.nan)
        nm = BASELINE if g is None else g
        ## WHY a drop zeroes the set, not just that it does. The reservoir is inert
        ## below its onset, so if a COOL matched band stops containing the base model
        ## no cell can repair it; if the ssp585 band moves, cells still can.
        why = []
        for _, lab in OURS:
            v = base_ours[lab][idx[2300]]
            if not (matched[lab][0] <= v <= matched[lab][1]):
                why.append(f"{lab} base {v:.1f} outside {matched[lab][0]:.1f}-"
                           f"{matched[lab][1]:.1f}"
                           + (" (UNREPAIRABLE: reservoir inert here)"
                              if lab != "SSP5-8.5" else " (reservoir can add)"))
        recs.append(dict(dropped=nm, why="; ".join(why) or "-",
                         n135=int(ship.pass_shipped.sum()),
                         n86=int(ship.pass_2150.sum()),
                         n2150=int(gg.pass_2150.sum()),
                         n_rate_r=int(gg.pass_rate_r.sum()),
                         n_rate_all=int(gg.pass_rate_all.sum()),
                         best_psi=bpsi, k_ssp585=karg["ssp585"], k_cool=karg["cool"],
                         arms_lost=";".join(empty) or "-"))
        print(f"{nm:22}{recs[-1]['n135']:6d}{recs[-1]['n86']:6d}{recs[-1]['n2150']:7d}"
              f"{recs[-1]['n_rate_r']:9d}{recs[-1]['n_rate_all']:9d}"
              f"{(f'{bpsi:.3f}' if bpsi == bpsi else '--'):>10}"
              f"{karg['ssp585']:7g}{karg['cool']:8g}   {recs[-1]['arms_lost']}"
              + ("   [NULL CONTROL]" if g == NULL_CONTROL else ""))

    out = pd.DataFrame(recs)
    out.to_csv(OUT, index=False)
    b0 = out.iloc[0]
    print(f"\n=== WHAT SURVIVES A SINGLE CLIMATE MODEL ===\n")
    print(f"  baseline (full ensemble): 135/86 = {b0.n135}/{b0.n86}, "
          f"2150 {b0.n2150}, +r2300 rate {b0.n_rate_r}, +x2300 rate {b0.n_rate_all}, "
          f"k*(585)={b0.k_ssp585:g} vs k*(cool)={b0.k_cool:g}")
    d = out.iloc[1:]
    print(f"\n  {'verdict':44}{'range over the 7 drops':>26}   robust?")
    checks = [
        ("the 86/216 admissible set", d.n86.min(), d.n86.max(), b0.n86),
        ("the 1080-cell 2150 set", d.n2150.min(), d.n2150.max(), b0.n2150),
        ("cells clearing the r2300 RATE band", d.n_rate_r.min(), d.n_rate_r.max(),
         b0.n_rate_r),
        ("cells clearing the x2300 RATE band", d.n_rate_all.min(), d.n_rate_all.max(),
         b0.n_rate_all),
    ]
    for nm, lo, hi, base in checks:
        rel = "n/a" if base == 0 else f"{lo / base:.2f}-{hi / base:.2f}x"
        rob = "YES" if (base == 0 and hi == 0) or (base and lo > 0 and hi / max(lo, 1) < 2) \
            else "NO"
        print(f"  {nm:44}{f'{lo}-{hi} (base {base})':>26}   {rob}  {rel}")
    print(f"\n  the k TENSION (ssp585 wants k*, cool wants k*):")
    print(f"    k*(ssp585) over the drops: {sorted(set(d.k_ssp585))}   "
          f"baseline {b0.k_ssp585:g}")
    print(f"    k*(cool)   over the drops: {sorted(set(d.k_cool))}   "
          f"baseline {b0.k_cool:g}")
    still = int((d.k_ssp585 > d.k_cool).sum())
    print(f"    ssp585 still wants a LARGER k than cool in {still}/{len(d)} drops "
          f"=> the tension is {'ROBUST' if still == len(d) else 'NOT robust'}.")
    nc = out[out.dropped == NULL_CONTROL]
    if len(nc):
        same = bool((nc.iloc[0][["n135", "n86", "n2150", "n_rate_r"]].values
                     == b0[["n135", "n86", "n2150", "n_rate_r"]].values).all())
        print(f"\n  NULL CONTROL — {NULL_CONTROL} is already excluded by "
              f"A.protect_band, so its drop must be an\n  exact no-op: "
              f"{'IDENTICAL to baseline, the drop machinery is exact' if same else '*** NOT IDENTICAL — the drop machinery is WRONG ***'}")
    print(f"\n  WHY each drop bites (the reservoir is inert below its onset, so a COOL "
          f"band that\n  stops containing the base model cannot be repaired by any cell):")
    for _, r in out.iterrows():
        if r.why != "-":
            print(f"    {r.dropped:22} {r.why}")

    print(f"\n  psi of the winning cell: baseline "
          f"{(f'{b0.best_psi:.3f}' if b0.best_psi == b0.best_psi else '--')}, "
          f"over the drops {sorted(set(np.round(d.best_psi.dropna(), 3)))}")
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
