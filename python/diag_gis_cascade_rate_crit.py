"""THE LAST OPEN PIECE OF EVIDENCE ON THE SHIPPED CELL: does the 2-STAGE CASCADE pass
the 2250-2300 RATE criterion?

WHY THIS COULD NOT BE READ OFF THE EXISTING SCANS. The rate criterion is one of the
TWO independent sources that pinned the flux (the other is Greve at 3001), and every
run of it predates the cascade. `psi = 100*V/tau` is a FIRST-ORDER parameterisation
and does NOT carry over to n = 2: at the shipped cell it is not even defined, because
the delivered unit is the SECOND stage. So the flux has to be MEASURED off the
trajectory, and the cell re-scored against the band.

WHAT THIS DOES, and why it is a diagnostic rather than an edit to the scan.
`scope_gis_reservoir_rate_rank.py` RE-RANKS 1080 cells. The cell is no longer being
chosen -- it was chosen 2026-08-23 on the between-scenario criterion -- so the
question is not "which cell wins the rate test" but "does the SHIPPED one pass it".
This reuses that scan's band construction verbatim (import, not copy) and scores four
named cells, so the answer is comparable to everything already written.

  base                no reservoir
  A   V=1.0 tau  800 n=1   the 2026-08-22a offline optimum (psi 0.125)
  B   V=6.0 tau 2200 n=1   the cell the rate criterion selected at n=1 (psi 0.273)
  SHIPPED V=6.0 tau 800 n=2  the cascade, chosen on between-scenario separation

BOTH BAND BASES ARE REPORTED, AND SO IS LEAVE-ONE-GCM-OUT. The run-level band is the
narrower and hence stricter one; a "run" is one of several percentile variants of a
GCM x RCM pair, so it carries less structural spread than its n suggests. The
2026-08-22c finding that dropping ONE GCM (MPI-ESM1-2-HR) moved the r2300 p05 from
9.7 to 19.2 and voided all 7 survivors is the reason the leave-one-out is not
optional here.

AND THEN: IS THE ANSWER STRUCTURAL? `--scan` asks whether ANY cascade cell at the
chosen onset satisfies the rate criterion TOGETHER with the three gates the cell
already had to clear (2100 exactly inert, both ssp585 2150 bands, our own ssp585
2300 inside the matched band). Adding a gate that the shipped cell fails is only
half an answer; the other half is whether something nearby passes.

READ-ONLY. Writes one CSV.
  python3 python/diag_gis_cascade_rate_crit.py [--scan]
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
    DRIVER_BASE, GIS_V0_M, YEARS, gis_shape_table, regional_driver,
)
import scope_gis_reservoir_offline as R  # noqa: E402
import scope_gis_reservoir_rate_rank as RR  # noqa: E402

import gis_targets  # noqa: E402

SCAN = "--scan" in sys.argv
OUT = os.path.join(REPO,
                   "outputs/diag_gis_cascade_rate_crit"
                   + ("_scan" if SCAN else "") + ".csv")

# --- named constants; every label and verdict below derives from these -----------
TAG, HIND, ARMS = A.TAG, A.HIND, A.ARMS
SSP585_ARMS = A.SSP585_ARMS
CM_PER_M, V_MAX_M, K_FIXED = R.CM_PER_M, R.V_MAX_M, R.K_FIXED
RATE_WIN, RATE_Q = RR.RATE_WIN, RR.RATE_Q
RATE_BAND_BASIS = RR.RATE_BAND_BASIS      # {"run","gcm"}; the pass criterion uses this
RATE_ARM_FAM = RR.RATE_ARM_FAM            # the constant-forcing arm, the only reachable one
## THE SHIPPED CELL, and the cells the arc argued over. Carried by name so this table
## is comparable to the ones already written rather than a fresh ranking with no anchors.
SHIPPED = dict(V_m=6.0, onset_K=4.69, tau_yr=800.0, stages=2)
CELLS = [("base (no reservoir)",            0.0, 0.0,  1.0,    1),
         ("A   V=1.0 tau  800 n=1",         1.0, 4.69,  800.0, 1),
         ("B   V=6.0 tau 2200 n=1",         6.0, 4.69, 2200.0, 1),
         ("SHIPPED V=6.0 tau 800 n=2",      SHIPPED["V_m"], SHIPPED["onset_K"],
                                            SHIPPED["tau_yr"], SHIPPED["stages"])]
## THE SCAN GRID. The ONSET IS HELD at the shipped 4.69 K on purpose: it was settled
## 2026-08-23 on the between-scenario criterion, and re-opening it here would answer a
## different question than "does the shipped FAMILY have a cell that passes". V and tau
## are the wide-V grids the cascade was selected on; the stage count is extended to 3
## because the analytic bound says the delivery ratio rises steeply in n (2.82 / 7.86 /
## 21.71), so if any n fixes the late slope it is the one that back-loads harder.
SCAN_ONSET_K = SHIPPED["onset_K"]
SCAN_STAGES = [2, 3]
SCAN_V_M = [2.0, V_MAX_M, 3.0, 4.5, 6.0, GIS_V0_M]
SCAN_TAU = [400, 800, 1600, 2200, 2700, 3200]


def unit(gmt, onset, tau, stages):
    """stages = 1 dispatches to `reservoir_unit` itself, so an n=1 row here is the
    same object every earlier scan scored, not a re-derivation of it."""
    return (R.reservoir_unit(gmt, onset, tau) if stages == 1
            else R.reservoir_unit_n(gmt, onset, tau, stages=stages))


def main():
    post = pd.read_csv(A.POST)
    tbar = gis_tbar()
    r_s = np.exp(post["gis_slow_ell"].to_numpy())
    post["gis_alpha_s"] = post["gis_slow_w"].to_numpy() * r_s / tbar
    post["gis_beta_s"] = (1.0 - post["gis_slow_w"].to_numpy()) * r_s
    S_tab = gis_shape_table()
    idx = {y: int(np.where(YEARS == y)[0][0])
           for y in tuple(RATE_WIN) + tuple(HIND) + (2015, 2100, 2150, 2300)}
    ibd = (YEARS >= DRIVER_BASE[0]) & (YEARS <= DRIVER_BASE[1])

    def load(path, col):
        g = pd.read_csv(path).set_index("year")[col].reindex(YEARS).to_numpy()
        rb = g - g[ibd].mean()
        return rb, regional_driver(rb, post["gis_amp"].to_numpy(), S_tab)

    gmst, drivers = {}, {}
    for ssp, lab, fam, stem in ARMS:
        gmst[(ssp, fam)], drivers[(ssp, fam)] = load(f"outputs/{stem}.csv", "gmst_spliced")
    ours_gmst, ours_drv = {}, {}
    for ssp, lab in R.OURS:
        ours_gmst[lab], ours_drv[lab] = load(
            f"data/observations/fair_mean_gmst_{ssp}.csv", "gmst_C")

    # --- the hindcast bisection: identical to every other scan in this family -----
    tgt = pd.read_csv(A.TARGETS).set_index("year")["gis"]
    want = float(tgt.loc[HIND[1]] - tgt.loc[HIND[0]])
    Th = drivers[A.HIND_ARM]
    lo, hi = np.full(len(post), 1e-4), np.full(len(post), 1e3)
    for _ in range(80):
        mid = np.sqrt(lo * hi)
        L = basin2_series(Th, post, K_FIXED, mid)
        b = 100.0 * (L[:, idx[HIND[1]]] - L[:, idx[HIND[0]]]) < want
        lo, hi = np.where(b, mid, lo), np.where(b, hi, mid)
    s = np.sqrt(lo * hi)
    base_arm = {k: np.median(rebase_cm(basin2_series(v, post, K_FIXED, s)), axis=0)
                for k, v in drivers.items()}
    base_ours = {k: np.median(rebase_cm(basin2_series(v, post, K_FIXED, s)), axis=0)
                 for k, v in ours_drv.items()}

    # --- the rate band, BOTH bases, plus the per-run table for leave-one-out ------
    ann = pd.read_csv(A.ANN)
    rband, rband_gcm, rate_by_run = {}, {}, {}
    for ssp, lab, fam, _ in ARMS:
        sub = A.protect_band(ann, lab, fam)
        w = sub[sub.year.isin(RATE_WIN)].pivot_table(
            index=["group", "model", "exp"], columns="year", values="gis_cm")
        per_run = (w[RATE_WIN[1]] - w[RATE_WIN[0]]) / (RATE_WIN[1] - RATE_WIN[0]) * 100.0
        rband[(ssp, fam)] = (per_run.quantile(RATE_Q[0]), per_run.median(),
                             per_run.quantile(RATE_Q[1]), len(per_run))
        pr = per_run.rename("rate").reset_index()
        pr["gcm"] = pr.exp.str.split("_").str[0]
        rate_by_run[(ssp, fam)] = pr
        g = pr.groupby("gcm").rate.median()
        rband_gcm[(ssp, fam)] = (g.quantile(RATE_Q[0]), g.median(),
                                 g.quantile(RATE_Q[1]), len(g))

    print(f"=== THE {RATE_WIN[0]}-{RATE_WIN[1]} RATE CRITERION ON THE SHIPPED CASCADE "
          f"| tag {TAG} ===\n")
    print(f"  target band, cm/century ({RATE_BAND_BASIS.upper()}-level = the pass "
          f"criterion; GCM-clustered beside it)\n")
    print(f"  {'arm':22}{'p05':>8}{'p50':>8}{'p95':>8}{'n':>5}   | "
          f"{'GCM p05':>8}{'p50':>7}{'p95':>7}{'n':>4}")
    for ssp, lab, fam, _ in SSP585_ARMS:
        r, gq = rband[(ssp, fam)], rband_gcm[(ssp, fam)]
        print(f"  {lab + ' ' + fam:22}{r[0]:8.1f}{r[1]:8.1f}{r[2]:8.1f}{r[3]:5d}   | "
              f"{gq[0]:8.1f}{gq[1]:7.1f}{gq[2]:7.1f}{gq[3]:4d}")
    print()

    # --- score the named cells ---------------------------------------------------
    rows = []
    print(f"  {'cell':28}" + "".join(f"{lab[-3:] + ' ' + fam[:2]:>11}"
                                     for _, lab, fam, _ in SSP585_ARMS)
          + f"{'PASS ' + RATE_ARM_FAM:>12}{'psi_eff':>10}{'100V/tau':>10}"
            f"{'our 2300':>10}")
    for nm, V, on, tau, ns in CELLS:
        vals, pass_flag = [], None
        for ssp, lab, fam, _ in SSP585_ARMS:
            add = CM_PER_M * V * unit(gmst[(ssp, fam)], on, tau, ns) if V \
                else np.zeros(len(YEARS))
            L = base_arm[(ssp, fam)] + add
            r = RR.rate_of(L, idx[RATE_WIN[0]], idx[RATE_WIN[1]], *RATE_WIN)
            vals.append(r)
            if fam == RATE_ARM_FAM:
                bnd = rband[(ssp, fam)] if RATE_BAND_BASIS == "run" \
                    else rband_gcm[(ssp, fam)]
                pass_flag = bool(bnd[0] <= r <= bnd[2])
                rate_arm_key, rate_arm_val = (ssp, fam), r
        a5 = CM_PER_M * V * unit(ours_gmst["SSP5-8.5"], on, tau, ns) if V \
            else np.zeros(len(YEARS))
        L5 = base_ours["SSP5-8.5"] + a5
        ## psi_eff: the RESERVOIR'S OWN 2250-2300 rate on OUR ssp585 -- the only
        ## version of the flux that means the same thing at n=1 and n=2.
        psi_eff = RR.rate_of(a5, idx[RATE_WIN[0]], idx[RATE_WIN[1]], *RATE_WIN)
        cf = f"{100.0 * V / tau:10.3f}" if (ns == 1 and V) else f"{'-':>10}"
        print(f"  {nm:28}" + "".join(f"{v:11.1f}" for v in vals)
              + f"{('PASS' if pass_flag else 'FAIL'):>12}{psi_eff:10.3f}{cf}"
              + f"{L5[idx[2300]]:10.1f}"
              + ("  [V>inventory]" if V > V_MAX_M else ""))
        rows.append(dict(cell=nm, V_m=V, onset_K=on, tau_yr=tau, stages=ns,
                         rate_r2300=rate_arm_val, psi_eff=psi_eff,
                         psi_closed=(100.0 * V / tau if (ns == 1 and V) else np.nan),
                         our_ssp585_2300_cm=L5[idx[2300]],
                         passes_rate=pass_flag, band_basis=RATE_BAND_BASIS))

    # --- LEAVE-ONE-GCM-OUT on the band, for the shipped cell only ----------------
    ## The verdict is only as wide as the ensemble behind the band. 2026-08-22c: one
    ## GCM moved the r2300 p05 by 2x and voided every survivor, so a pass that dies on
    ## a leave-one-out is not a pass -- it is one model's opinion.
    print(f"\n  LEAVE-ONE-GCM-OUT on the {RATE_ARM_FAM} band ({RATE_BAND_BASIS}-level), "
          f"shipped cell rate = {rows[-1]['rate_r2300']:.1f} cm/century")
    pr = rate_by_run[rate_arm_key]
    lo1 = []
    for g in sorted(pr.gcm.unique()):
        keep = pr[pr.gcm != g].rate
        p05, p95 = keep.quantile(RATE_Q[0]), keep.quantile(RATE_Q[1])
        ok = bool(p05 <= rows[-1]["rate_r2300"] <= p95)
        lo1.append(ok)
        print(f"    drop {g:20} band [{p05:6.1f}, {p95:6.1f}]  n={len(keep):3d}   "
              f"{'PASS' if ok else 'FAIL'}")
    print(f"    ⇒ shipped cell passes {sum(lo1)}/{len(lo1)} leave-one-GCM-out bands")

    if not SCAN:
        pd.DataFrame(rows).to_csv(OUT, index=False)
        print(f"\nwrote {os.path.relpath(OUT, REPO)}")
        return

    # --- IS THE FAILURE STRUCTURAL? the joint feasibility scan -------------------
    ## The level bands, built exactly as the shipped scan builds them (same offset,
    ## same run-level quantiles), so "in band" means here what it means there.
    offs = float(np.median(rebase_cm(
        basin2_series(drivers[("ssp585", "r2300")], post, 1.0, 1.0))[:, idx[2015]]))
    band = {}
    for ssp, lab, fam, _ in ARMS:
        q = A.protect_band(ann, lab, fam).groupby("year").gis_cm
        band[(ssp, fam)] = {y: (q.quantile(.05)[y] + offs, q.median()[y] + offs,
                                q.quantile(.95)[y] + offs) for y in (2100, 2150, 2300)}
    m_lo, m_hi = (100 * gis_targets.MATCHED_2300_M["SSP5-8.5"][0],
                  100 * gis_targets.MATCHED_2300_M["SSP5-8.5"][1])
    r_bnd = rband[rate_arm_key] if RATE_BAND_BASIS == "run" else rband_gcm[rate_arm_key]

    print(f"\n=== IS THE FAILURE STRUCTURAL? joint scan, onset held at "
          f"{SCAN_ONSET_K} K ===\n")
    print(f"  gates: 2100 EXACTLY inert | ssp585 r2300 & x2300 2150 in band | "
          f"our ssp585 2300 in [{m_lo:.1f}, {m_hi:.1f}] cm\n"
          f"         | {RATE_WIN[0]}-{RATE_WIN[1]} r2300 rate in "
          f"[{r_bnd[0]:.1f}, {r_bnd[2]:.1f}] cm/century ({RATE_BAND_BASIS}-level)\n")
    srows = []
    for ns in SCAN_STAGES:
        for V in SCAN_V_M:
            for tau in SCAN_TAU:
                add = {k: CM_PER_M * V * unit(g, SCAN_ONSET_K, float(tau), ns)
                       for k, g in gmst.items()}
                a5 = CM_PER_M * V * unit(ours_gmst["SSP5-8.5"], SCAN_ONSET_K,
                                         float(tau), ns)
                L5 = base_ours["SSP5-8.5"] + a5
                rec = dict(stages=ns, V_m=V, tau_yr=tau, onset_K=SCAN_ONSET_K)
                rec["inert2100"] = bool(abs(a5[idx[2100]]) < 1e-9)
                for fam in ("r2300", "x2300"):
                    lvl = base_arm[("ssp585", fam)][idx[2150]] + add[("ssp585", fam)][idx[2150]]
                    rec[f"{fam}_2150"] = lvl
                    rec[f"{fam}_2150_in"] = bool(band[("ssp585", fam)][2150][0] <= lvl
                                                 <= band[("ssp585", fam)][2150][2])
                rec["our2300"] = L5[idx[2300]]
                rec["lvl2300_in"] = bool(m_lo <= L5[idx[2300]] <= m_hi)
                r = RR.rate_of(base_arm[rate_arm_key] + add[rate_arm_key],
                               idx[RATE_WIN[0]], idx[RATE_WIN[1]], *RATE_WIN)
                rec["rate_r2300"] = r
                rec["rate_in"] = bool(r_bnd[0] <= r <= r_bnd[2])
                rec["psi_eff"] = RR.rate_of(a5, idx[RATE_WIN[0]], idx[RATE_WIN[1]],
                                            *RATE_WIN)
                rec["all_pass"] = bool(rec["inert2100"] and rec["r2300_2150_in"]
                                       and rec["x2300_2150_in"] and rec["lvl2300_in"]
                                       and rec["rate_in"])
                srows.append(rec)
    sc = pd.DataFrame(srows)
    ## PRE-RATE is the set the shipped cell belongs to: everything it already cleared.
    pre = sc[sc.inert2100 & sc.r2300_2150_in & sc.x2300_2150_in & sc.lvl2300_in]
    print(f"  cells clearing the PRE-EXISTING gates (no rate term): {len(pre)}/{len(sc)}")
    print(f"  of those, also clearing the RATE band:                {int(pre.rate_in.sum())}"
          f"/{len(pre)}")
    print(f"  cells clearing EVERYTHING:                            "
          f"{int(sc.all_pass.sum())}/{len(sc)}\n")
    if len(pre):
        print(f"    rate range over the pre-rate set: "
              f"{pre.rate_r2300.min():.1f} - {pre.rate_r2300.max():.1f} cm/century "
              f"vs a band top of {r_bnd[2]:.1f}")
        show = pre.sort_values("rate_r2300").head(6)
        print(f"\n    {'n':>2}{'V_m':>7}{'tau':>7}{'2300':>8}{'rate':>8}"
              f"{'r2150':>8}{'x2150':>8}  rate_in")
        for _, b in show.iterrows():
            print(f"    {int(b.stages):2d}{b.V_m:7.2f}{int(b.tau_yr):7d}{b.our2300:8.1f}"
                  f"{b.rate_r2300:8.1f}{b.r2300_2150:8.1f}{b.x2300_2150:8.1f}"
                  f"  {'IN' if b.rate_in else 'out'}")
    # --- HOW MUCH DOES THE RATE GATE ACTUALLY COST? ------------------------------
    ## The grid has no point between V = 4.5 and V = 6.0, so read off it the tension
    ## looks like 12.2 cm at 2300. Solve for the LARGEST V at the shipped (n, tau,
    ## onset) that still clears the rate band, and the answer is much smaller. V
    ## scales the reservoir linearly, so this is a clean bisection with no ambiguity
    ## about what is being held fixed.
    ns, tau = SHIPPED["stages"], SHIPPED["tau_yr"]
    u_arm = unit(gmst[rate_arm_key], SCAN_ONSET_K, tau, ns)
    u_our = unit(ours_gmst["SSP5-8.5"], SCAN_ONSET_K, tau, ns)
    rate_at = lambda V: RR.rate_of(base_arm[rate_arm_key] + CM_PER_M * V * u_arm,
                                   idx[RATE_WIN[0]], idx[RATE_WIN[1]], *RATE_WIN)
    lvl_at = lambda V: (base_ours["SSP5-8.5"] + CM_PER_M * V * u_our)[idx[2300]]
    lo, hi = 0.0, GIS_V0_M
    if rate_at(hi) <= r_bnd[2]:
        V_max = hi
    else:
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if rate_at(mid) <= r_bnd[2] else (lo, mid)
        V_max = lo
    ## THE p50 IS THE **MATCHED** ONE, gis_targets.MATCHED_2300_P50_M, not the r2300
    ## arm's own band median. They are 98.5 vs 72.3 cm and quoting the wrong one would
    ## move this verdict by 1.36x. "Lands on the p50" is PREDICTOR-DEPENDENT -- memory
    ## `gis_matched_band_predictor` -- and the cell was chosen against the MATCHED one.
    p50 = 100 * gis_targets.MATCHED_2300_P50_M["SSP5-8.5"]
    print(f"\n  THE COST OF THE RATE GATE, at the shipped n={ns} / tau={tau:.0f} / "
          f"onset {SCAN_ONSET_K} K")
    print(f"    largest V clearing the rate band : {V_max:.2f} m "
          f"(rate {rate_at(V_max):.1f} vs band top {r_bnd[2]:.1f})")
    print(f"    it gives our ssp585 2300         : {lvl_at(V_max):.1f} cm  "
          f"= {lvl_at(V_max) / lvl_at(SHIPPED['V_m']):.3f}x the shipped "
          f"{lvl_at(SHIPPED['V_m']):.1f} cm")
    print(f"    matched p50 for reference        : {p50:.1f} cm  "
          f"⇒ the rate-clearing cell is {lvl_at(V_max) / p50:.3f}x it, "
          f"the shipped one {lvl_at(SHIPPED['V_m']) / p50:.3f}x")
    print(f"    the shipped cell overshoots the rate band top by "
          f"{rate_at(SHIPPED['V_m']) / r_bnd[2]:.3f}x "
          f"({rate_at(SHIPPED['V_m']) - r_bnd[2]:.1f} cm/century)")

    sc.to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
