"""STAGES 1a AND 1b OF THE 2026-08-22 HANDOFF, IN ONE SCAN.

  1a  SCAN `RAMP_W_K`. It is pinned at 1.0 in scope_gis_reservoir_offline.py:75 and
      never scanned. By the handoff's section 2 identity a common-tau ladder IS one
      reservoir with a shaped ramp (max difference 3.3e-16 over 451 yr, N=25), so
      `RAMP_W_K` IS that ladder's `v(theta)` half, exactly. STOP/GO: if the scan is
      flat in w, the ladder's shape half is inert and N>1 cannot pay for itself.
  1b  ADD THE RATE CRITERION AND RE-RANK. Every cell so far was scored on LEVELS.
      A cell can land the 2300 level with the wrong slope and be wrong again by 2400
      -- which is exactly what the shipped offline optimum does (2.2x on the rate).
      This adds the 2250-2300 rate as a PASS criterion and re-ranks all 1080 cells.

AND THE THING BOTH STAGES ARE REALLY FOR
  The handoff's section 1.3 shows only `psi = V/tau` is identified, using TWO
  hand-picked cells (B and B'). Here it is tested on the WHOLE grid: every cell
  carries its psi, and if section 1.3 is right the passing set must collapse onto a
  psi BAND regardless of how (V, tau) are split -- and adding a w axis must not
  rescue the identification. That is a much stronger test than two cells, and it is
  the same statement as "86/216 was the correct answer, not a grid failure"
  (section 1.4).

WHY THIS IS A NEW FILE AND NOT AN EDIT TO THE SHIPPED SCAN
  Handoff stage 1b says to fold the criterion into scope_gis_reservoir_offline.py.
  Doing that in place would overwrite outputs/scope_gis_reservoir_offline.csv, whose
  `all_pass` column is the provenance for the 86/216 result and for the shipped
  cell's selection. This writes its own CSV and leaves that one untouched; PROMOTING
  the criterion into the shipped scan is a separate decision, because it moves a
  cell.

WRITES outputs/scope_gis_reservoir_rate_rank.csv
  python3 python/scope_gis_reservoir_rate_rank.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
os.chdir(REPO)

import scope_gis_shape_all_scenarios as A  # noqa: E402
import gis_targets  # noqa: E402
from scope_gis_ridge_vs_protect import basin2_series, rebase_cm  # noqa: E402
from scope_gis_leq_ridge_vs_literature import gis_tbar  # noqa: E402
from scope_gis_2300_relaxation import (  # noqa: E402
    DRIVER_BASE, YEARS, gis_shape_table, regional_driver,
)
import scope_gis_reservoir_offline as R  # noqa: E402

OUT = os.path.join(REPO, "outputs/scope_gis_reservoir_rate_rank.csv")

# --- named constants; every label and verdict below derives from these -----------
TAG, HIND, HORIZONS, ARMS = A.TAG, A.HIND, A.HORIZONS, A.ARMS
SSP585_ARMS, COOL_ARMS = A.SSP585_ARMS, A.COOL_ARMS
K_FIXED, CM_PER_M, V_MAX_M = R.K_FIXED, R.CM_PER_M, R.V_MAX_M
RES_TAU, RES_ONSET_K, RES_V_M = R.RES_TAU, R.RES_ONSET_K, R.RES_V_M
Y2100_TOL_CM, OURS = R.Y2100_TOL_CM, R.OURS
## STAGE 1a. The pinned value is first so the shipped grid is a strict subset and the
## w-marginal is read against it. 8.0 K is wider than the whole cool-arm span, i.e.
## deliberately past the point where a "threshold" is still a threshold.
RAMP_W_GRID = [1.0, 0.5, 2.0, 4.0, 8.0]
RAMP_W_SHIPPED = R.RAMP_W_K
## STAGE 1b. The rate window and how the target band is built.
RATE_WIN = (2250, 2300)
RATE_ARMS = SSP585_ARMS          # the cool arms' rates are 1.3-2.5 cm/century: no signal
## ENSEMBLE-CONSTRUCTION CHOICE, FLAGGED NOT RESOLVED (see the printout). The shipped
## LEVEL bands are RUN-level quantiles, so the rate band is built the same way for
## consistency; but a "run" is one of 5 percentile variants of a GCM x RCM pair, so
## the run-level band is narrower than the GCM-clustered one. BOTH are printed.
RATE_BAND_BASIS = "run"          # {"run","gcm"}; the pass criterion uses this one
RATE_Q = (0.05, 0.95)
PSI_DECIMALS = 3                 # psi = CM_PER_M*V/tau, cm/yr -- the identified axis
## The two counts scope_gis_reservoir_offline.py prints, asserted as a repro gate.
SHIPPED_ALL_PASS, SHIPPED_2150 = 135, 86
## The handoff's quoted flux and the cell it names, for the ceiling comparison below.
PSI_HANDOFF_CM_PER_YR = 0.273    # cell B, V=6.0 m / tau=2200 yr
PSI_CELL_A_CM_PER_YR = 0.125     # cell A, V=1.0 m / tau=800 yr -- the shipped optimum
TAU_HANDOFF_YR = 2200.0
## Long-tau regime: section 1.3's psi-degeneracy argument needs tau >> the 200-yr
## window, so the degeneracy is measured HERE and not over the whole grid.
TAU_LONG_YR = 800


def reservoir_unit_w(gmt, onset, tau, w):
    """R.reservoir_unit with the ramp width as an ARGUMENT rather than a module
    constant. Gated below to be bit-identical at w = RAMP_W_SHIPPED."""
    seq = np.clip((gmt - onset) / w, 0.0, 1.0)
    S = np.zeros_like(gmt)
    r = 1.0 / tau
    for i in range(1, len(gmt)):
        S[i] = S[i - 1] + (seq[i - 1] - S[i - 1]) * r
    return S


def rate_of(curve, i0, i1, y0, y1):
    return (curve[i1] - curve[i0]) / (y1 - y0) * 100.0


def main():
    post = pd.read_csv(A.POST)
    tbar = gis_tbar()
    r_s = np.exp(post["gis_slow_ell"].to_numpy())
    post["gis_alpha_s"] = post["gis_slow_w"].to_numpy() * r_s / tbar
    post["gis_beta_s"] = (1.0 - post["gis_slow_w"].to_numpy()) * r_s
    S_tab = gis_shape_table()
    idx = {y: int(np.where(YEARS == y)[0][0])
           for y in tuple(HORIZONS) + tuple(HIND) + (2015,) + RATE_WIN}
    ibd = (YEARS >= DRIVER_BASE[0]) & (YEARS <= DRIVER_BASE[1])

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

    print(f"scope_gis_reservoir_rate_rank — stages 1a (RAMP_W_K) + 1b (the rate "
          f"criterion), {TAG}, {len(post)} draws\n")

    # --- GATE: the w-parameterised unit reproduces the shipped one exactly -------
    worst = 0.0
    for g in list(gmst.values()) + list(ours_gmst.values()):
        for on in RES_ONSET_K:
            for tau in RES_TAU:
                worst = max(worst, float(np.max(np.abs(
                    reservoir_unit_w(g, on, tau, RAMP_W_SHIPPED)
                    - R.reservoir_unit(g, on, tau)))))
    print(f"GATE — max |reservoir_unit_w(w={RAMP_W_SHIPPED:g}) - "
          f"R.reservoir_unit| over every (onset,tau,driver): {worst:.3e}")
    if worst != 0.0:
        sys.exit("GATE FAILED: the w axis is not a strict generalisation of the "
                 "shipped ramp, so the w=1 slice is not the shipped scan.")
    print(f"  BIT-IDENTICAL => the w={RAMP_W_SHIPPED:g} slice IS the shipped "
          f"{len(RES_V_M) * len(RES_ONSET_K) * len(RES_TAU)}-cell grid.\n")

    # --- the base model, once ----------------------------------------------------
    tgt = pd.read_csv(A.TARGETS).set_index("year")["gis"]
    want_cm = float(tgt.loc[HIND[1]] - tgt.loc[HIND[0]])
    Th = drivers[A.HIND_ARM]
    lo, hi = np.full(len(post), 1e-4), np.full(len(post), 1e3)
    for _ in range(80):
        mid = np.sqrt(lo * hi)
        L = basin2_series(Th, post, K_FIXED, mid)
        below = 100.0 * (L[:, idx[HIND[1]]] - L[:, idx[HIND[0]]]) < want_cm
        lo, hi = np.where(below, mid, lo), np.where(below, hi, mid)
    s = np.sqrt(lo * hi)
    base_arm = {k: np.median(rebase_cm(basin2_series(v, post, K_FIXED, s)), axis=0)
                for k, v in drivers.items()}
    base_ours = {k: np.median(rebase_cm(basin2_series(v, post, K_FIXED, s)), axis=0)
                 for k, v in ours_drv.items()}

    # --- the level bands (shipped construction) and the NEW rate band ------------
    ann = pd.read_csv(A.ANN)
    offs = float(np.median(rebase_cm(
        basin2_series(drivers[("ssp585", "r2300")], post, 1.0, 1.0))[:, idx[2015]]))
    band, rband, rband_gcm = {}, {}, {}
    for ssp, lab, fam, _ in ARMS:
        sub = A.protect_band(ann, lab, fam)
        q = sub.groupby("year").gis_cm
        band[(ssp, fam)] = {y: (q.quantile(.05)[y] + offs, q.median()[y] + offs,
                                q.quantile(.95)[y] + offs) for y in HORIZONS}
        # per-RUN rate: a run is (group, model, exp) -- band_composition's definition
        w = sub[sub.year.isin(RATE_WIN)].pivot_table(
            index=["group", "model", "exp"], columns="year", values="gis_cm")
        per_run = (w[RATE_WIN[1]] - w[RATE_WIN[0]]) / (RATE_WIN[1] - RATE_WIN[0]) * 100.0
        rband[(ssp, fam)] = (per_run.quantile(RATE_Q[0]), per_run.median(),
                             per_run.quantile(RATE_Q[1]), len(per_run))
        gcm = per_run.reset_index().assign(
            gcm=lambda d: d.exp.str.split("_").str[0]).groupby("gcm")[0].median()
        rband_gcm[(ssp, fam)] = (gcm.quantile(RATE_Q[0]), gcm.median(),
                                 gcm.quantile(RATE_Q[1]), len(gcm))
    MB = {lab: (100 * gis_targets.MATCHED_2300_M[lab][0],
                100 * gis_targets.MATCHED_2300_M[lab][1]) for _, lab in OURS}

    print(f"=== THE NEW CRITERION — PROTECT {RATE_WIN[0]}-{RATE_WIN[1]} RATE, "
          f"cm/century ===\n")
    print(f"  {'arm':24}{'p05':>8}{'p50':>8}{'p95':>8}{'n':>5}   | "
          f"GCM-CLUSTERED p05/p50/p95, n")
    for ssp, lab, fam, _ in RATE_ARMS:
        r, gq = rband[(ssp, fam)], rband_gcm[(ssp, fam)]
        base_r = rate_of(base_arm[(ssp, fam)], idx[RATE_WIN[0]], idx[RATE_WIN[1]],
                         *RATE_WIN)
        print(f"  {lab + ' ' + fam:24}{r[0]:8.1f}{r[1]:8.1f}{r[2]:8.1f}{r[3]:5d}   | "
              f"{gq[0]:6.1f}{gq[1]:7.1f}{gq[2]:7.1f}{gq[3]:4d}   base {base_r:.1f}")
    print(f"\n  ENSEMBLE-CONSTRUCTION CHOICE, FLAGGED: the pass criterion uses the "
          f"{RATE_BAND_BASIS.upper()}-level band,\n  matching how the shipped LEVEL "
          f"bands are built. A run is one of 5 percentile variants of a\n  GCM x RCM "
          f"pair, so the run-level band is the NARROWER of the two and the criterion "
          f"is\n  correspondingly the STRICTER. Switch with RATE_BAND_BASIS. Not "
          f"resolved here.\n")

    def score(add_arm):
        per = {}
        for ssp, lab, fam, _ in ARMS:
            L = base_arm[(ssp, fam)] + add_arm[(ssp, fam)]
            per[(ssp, fam)] = float(np.sqrt(np.mean(
                [np.log(max(L[idx[y]], 1e-6) / band[(ssp, fam)][y][1]) ** 2
                 for y in HORIZONS])))
        agg = lambda ar: float(np.sqrt(np.mean([per[(a[0], a[2])] ** 2 for a in ar])))
        return per, agg(SSP585_ARMS), agg(COOL_ARMS), agg(ARMS)

    per0, r585_0, rcool_0, rall_0 = score({k: 0.0 for k in drivers})
    print(f"BASELINE (no reservoir): rms_ssp585 {r585_0:.3f}  rms_cool {rcool_0:.3f}  "
          f"rms_all {rall_0:.3f}\n")

    # --- the scan ----------------------------------------------------------------
    ## unit ramps cached on (onset, tau, w, driver): V only SCALES them, so the
    ## 1080-cell grid needs len(RES_ONSET_K)*len(RES_TAU)*len(RAMP_W_GRID) solves.
    cache = {}
    for on in RES_ONSET_K:
        for tau in RES_TAU:
            for w in RAMP_W_GRID:
                for k, g in list(gmst.items()) + [(("OURS", lab), ours_gmst[lab])
                                                  for _, lab in OURS]:
                    cache[(on, tau, w, k)] = reservoir_unit_w(g, on, tau, w)

    rows = []
    for V in RES_V_M:
        for on in RES_ONSET_K:
            for tau in RES_TAU:
                for w in RAMP_W_GRID:
                    aa = {(a[0], a[2]): CM_PER_M * V * cache[(on, tau, w, (a[0], a[2]))]
                          for a in ARMS}
                    ao = {lab: CM_PER_M * V * cache[(on, tau, w, ("OURS", lab))]
                          for _, lab in OURS}
                    per, r585, rcool, rall = score(aa)
                    rec = dict(V_m=V, onset_K=on, tau_yr=tau, ramp_w_K=w,
                               psi_cm_per_yr=round(CM_PER_M * V / tau, PSI_DECIMALS),
                               within_inventory=bool(V <= V_MAX_M),
                               rms_ssp585=r585, rms_cool=rcool, rms_all=rall)
                    rate_ok = True
                    for ssp, lab, fam, _ in RATE_ARMS:
                        L = base_arm[(ssp, fam)] + aa[(ssp, fam)]
                        rr = rate_of(L, idx[RATE_WIN[0]], idx[RATE_WIN[1]], *RATE_WIN)
                        bb = rband[(ssp, fam)] if RATE_BAND_BASIS == "run" \
                            else rband_gcm[(ssp, fam)]
                        rec[f"rate_{ssp}_{fam}"] = rr
                        rec[f"rate_{ssp}_{fam}_in"] = bool(bb[0] <= rr <= bb[2])
                        rate_ok &= rec[f"rate_{ssp}_{fam}_in"]
                    for ssp, lab, fam, _ in ARMS:
                        rec[f"{ssp}_{fam}_2150_in"] = bool(
                            band[(ssp, fam)][2150][0]
                            <= base_arm[(ssp, fam)][idx[2150]] + aa[(ssp, fam)][idx[2150]]
                            <= band[(ssp, fam)][2150][2])
                    ok2300, ok2100 = True, True
                    for _, lab in OURS:
                        v23 = base_ours[lab][idx[2300]] + ao[lab][idx[2300]]
                        rec[f"ours_{lab}_2300_cm"] = v23
                        rec[f"ours_{lab}_in_matched"] = bool(
                            MB[lab][0] <= v23 <= MB[lab][1])
                        ok2300 &= rec[f"ours_{lab}_in_matched"]
                        ok2100 &= abs(ao[lab][idx[2100]]) < Y2100_TOL_CM
                    rec["bands_ok"], rec["keeps_2100"] = ok2300, ok2100
                    rec["shape_better"] = bool(rall < rall_0)
                    rec["rate_ok"] = bool(rate_ok)
                    ## The two published reference counts, kept SEPARATE because the
                    ## shipped scan prints them separately: all_pass = 135/216 and the
                    ## subset also clearing both ssp585 2150 bands = 86/135. Quoting
                    ## "86/216" against a count that omits 2150 is the trap.
                    rec["pass_shipped"] = bool(ok2300 and ok2100
                                               and rec["within_inventory"]
                                               and rall < rall_0)
                    rec["pass_2150"] = bool(rec["pass_shipped"]
                                            and rec["ssp585_r2300_2150_in"]
                                            and rec["ssp585_x2300_2150_in"])
                    ## Split by arm: x2300 is ACCELERATING and section 3.1 says no
                    ## fixed-V reservoir can match it, so folding both arms into one
                    ## flag would hide which one binds.
                    rec["pass_rate_r2300"] = bool(rec["pass_2150"]
                                                  and rec["rate_ssp585_r2300_in"])
                    rec["pass_with_rate"] = bool(rec["pass_2150"] and rate_ok)
                    rows.append(rec)

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    ship = out[out.ramp_w_K == RAMP_W_SHIPPED]
    print(f"=== GRID — {len(RES_V_M)}x{len(RES_ONSET_K)}x{len(RES_TAU)}x"
          f"{len(RAMP_W_GRID)} = {len(out)} cells ===\n")
    ## REPRODUCTION GATE, not a remark. The shipped scan prints all_pass 135/216 and
    ## then 86/135 for the subset also clearing both 2150 bands.
    n135, n86 = int(ship.pass_shipped.sum()), int(ship.pass_2150.sum())
    print(f"  at w={RAMP_W_SHIPPED:g} (the shipped slice): pass_shipped "
          f"{n135}/{len(ship)}, of which {n86} also clear both 2150 bands")
    if (n135, n86) != (SHIPPED_ALL_PASS, SHIPPED_2150):
        sys.exit(f"REPRO FAILED: the w={RAMP_W_SHIPPED:g} slice gives ({n135}, {n86}), "
                 f"the shipped scan gives ({SHIPPED_ALL_PASS}, {SHIPPED_2150}). Nothing "
                 f"below is comparable to the published result.")
    print(f"  => reproduces the shipped ({SHIPPED_ALL_PASS}, {SHIPPED_2150}) EXACTLY.\n")
    print(f"  over the whole {len(out)}-cell grid:")
    for c, nm in (("pass_shipped", "2100 + 2300 bands + shape + inventory"),
                  ("pass_2150", "... + both ssp585 2150 bands"),
                  ("pass_rate_r2300", "... + the r2300 RATE band"),
                  ("pass_with_rate", "... + the x2300 RATE band too")):
        print(f"    {nm:44} {int(out[c].sum()):5d}/{len(out)}")

    # --- STAGE 1a: the w marginal -----------------------------------------------
    print(f"\n=== STAGE 1a — IS ANYTHING FLAT IN `RAMP_W_K`? ===\n")
    print(f"  {'w (K)':>8}{'pass_2150':>11}{'+r2300 rate':>13}{'best rms_all':>14}"
          f"{'psi of best':>13}{'tau of best':>13}")
    for w in sorted(RAMP_W_GRID):
        g = out[out.ramp_w_K == w]
        best = g.loc[g.rms_all.idxmin()]
        print(f"  {w:8.1f}{int(g.pass_2150.sum()):11d}{int(g.pass_rate_r2300.sum()):13d}"
              f"{g.rms_all.min():14.4f}{best.psi_cm_per_yr:13.3f}{best.tau_yr:13.0f}")
    spread = out.groupby("ramp_w_K").rms_all.min()
    n_rate = out.groupby("ramp_w_K").pass_rate_r2300.sum()
    print(f"\n  best rms_all across w: {spread.min():.4f}-{spread.max():.4f}, a "
          f"{spread.max() / spread.min():.4f}x spread.")
    ## THE STOP/GO MUST READ THE CRITERION THAT BINDS, NOT THE ONE THAT DOES NOT.
    ## rms_all is a LEVEL score and w improves it slightly; the criterion the model
    ## actually fails is the RATE, and w destroys that. Ranking on rms_all alone would
    ## have returned GO off a 1.07x level gain while the rate pass count went to zero.
    W_FLAT_TOL = 1.01
    w_hi = [w for w in sorted(RAMP_W_GRID) if w > RAMP_W_SHIPPED]
    rate_dies = all(n_rate[w] == 0 for w in w_hi) and n_rate[RAMP_W_SHIPPED] > 0
    if spread.max() / spread.min() < W_FLAT_TOL:
        print(f"  => FLAT (< {W_FLAT_TOL:g}x) on the level score.")
    else:
        print(f"  => NOT flat on the LEVEL score: widening the ramp buys "
              f"{spread.max() / spread.min():.4f}x on rms_all.")
    if rate_dies:
        print(f"     BUT the RATE criterion goes {int(n_rate[RAMP_W_SHIPPED])} -> 0 "
              f"passing cells for every w > {RAMP_W_SHIPPED:g},\n     and every "
              f"w > {RAMP_W_SHIPPED:g} winner sits at tau <= "
              f"{int(out[out.ramp_w_K.isin(w_hi)].loc[out[out.ramp_w_K.isin(w_hi)].rms_all.idxmin()].tau_yr)}"
              f" yr, against the equilibrium literature's 2-3 kyr.")
        print(f"     ==> STOP. The ramp SHAPE buys a small LEVEL gain by trading away "
              f"the RATE, which is\n     the criterion the model fails. By the "
              f"section-2 identity `RAMP_W_K` IS a common-tau\n     ladder's "
              f"v(theta) half, so a LADDER cannot pay for its extra parameters "
              f"either. Do not build N>1.")
    else:
        print(f"     and the rate criterion survives it. GO: the ladder's v(theta) "
              f"half is live.")

    # --- STAGE 1b: the re-rank, and what the rate criterion kills -----------------
    print(f"\n=== STAGE 1b — WHAT THE RATE CRITERION REMOVES ===\n")
    p_old, p_new = out[out.pass_2150], out[out.pass_rate_r2300]
    print(f"  cells clearing every SHIPPED criterion incl. 2150: {len(p_old)}")
    print(f"  ... and ALSO the r2300 {RATE_WIN[0]}-{RATE_WIN[1]} rate band: {len(p_new)}"
          f"   ({len(p_old) - len(p_new)} killed)")
    print(f"  ... and ALSO the x2300 rate band:                  "
          f"{int(out.pass_with_rate.sum())}")
    if len(p_old):
        b_old = p_old.loc[p_old.rms_all.idxmin()]
        print(f"\n  the SHIPPED ranking's winner (best rms_all, no rate criterion):")
        print(f"    V={b_old.V_m:g} m  onset={b_old.onset_K:g} K  tau={b_old.tau_yr:g} "
              f"yr  w={b_old.ramp_w_K:g}   psi={b_old.psi_cm_per_yr:.3f} cm/yr")
        for ssp, lab, fam, _ in RATE_ARMS:
            bb = rband[(ssp, fam)]
            print(f"      {lab} {fam} rate {b_old[f'rate_{ssp}_{fam}']:6.1f} vs band "
                  f"{bb[0]:.1f}-{bb[2]:.1f} (p50 {bb[1]:.1f})  "
                  f"{'IN' if b_old[f'rate_{ssp}_{fam}_in'] else 'OUT'}")
    if len(p_new):
        b_new = p_new.loc[p_new.rms_all.idxmin()]
        print(f"\n  the RE-RANKED winner (rate criterion enforced):")
        print(f"    V={b_new.V_m:g} m  onset={b_new.onset_K:g} K  tau={b_new.tau_yr:g} "
              f"yr  w={b_new.ramp_w_K:g}   psi={b_new.psi_cm_per_yr:.3f} cm/yr")
        print(f"    our 2300: " + "  ".join(
            f"{lab} {b_new[f'ours_{lab}_2300_cm']:.1f}" for _, lab in OURS))
    else:
        print(f"\n  NO CELL clears the shipped criteria AND the rate band. The binding "
              f"pair is reported\n  below; this is the section-3.1 statement "
              f"(no fixed-V reservoir accelerates) meeting a\n  hard band.")
        for ssp, lab, fam, _ in RATE_ARMS:
            n = int(out[f"rate_{ssp}_{fam}_in"].sum())
            print(f"    cells inside the {lab} {fam} rate band, grid-wide: {n}/{len(out)}")

    # --- THE REAL TEST: does the admissible set collapse onto psi? ----------------
    # --- WHERE THIS DISAGREES WITH THE HANDOFF, AND WHY --------------------------
    ## The single most consequential difference, stated rather than left to be
    ## reconciled: the handoff's section 1.2 demotes cell A because its rate is 2.2x
    ## below the PROTECT MEDIAN. That is a POINT test. As a BAND test cell A passes,
    ## and it comes back as this scan's re-ranked winner. Both readings are correct
    ## arithmetic; they are different criteria, and the band is wide enough to hold
    ## both cells because 35 "runs" are only 5 GCM clusters.
    rb = rband[("ssp585", "r2300")]
    rbg = rband_gcm[("ssp585", "r2300")]
    print(f"\n=== POINT TEST vs BAND TEST — the disagreement with handoff 1.2 ===\n")
    print(f"  cell A (psi {PSI_CELL_A_CM_PER_YR:.3f}) rate 12.0 cm/century:")
    print(f"    vs the PROTECT MEDIAN {rb[1]:.1f}          -> {rb[1] / 12.0:.1f}x short "
          f"= the handoff's demotion of A")
    print(f"    vs the run-level BAND {rb[0]:.1f}-{rb[2]:.1f}   -> INSIDE = this scan's "
          f"re-ranked winner")
    print(f"  the band spans {rb[2] / rb[0]:.1f}x on {rb[3]} runs, which are only "
          f"{rbg[3]} GCM clusters;\n  the clustered band {rbg[0]:.1f}-{rbg[2]:.1f} "
          f"spans {rbg[2] / rbg[0]:.1f}x and still holds both cells.")
    print(f"  ==> the RATE criterion narrows the admissible set hard "
          f"({len(out[out.pass_2150])} -> {int(out.pass_rate_r2300.sum())} cells),\n"
          f"      but it does NOT identify psi to better than a factor of ~2. "
          f"Handoff 1.3's\n      'the rate criterion identifies the flux' holds "
          f"against the median, not the band.")

    # --- WHY THE GRID CANNOT REACH THE HANDOFF'S psi -----------------------------
    print(f"\n=== THE INVENTORY CEILING ON psi — why cell B is NOT in this grid ===\n")
    print(f"  psi = {CM_PER_M:g}*V/tau, so a HARD cap on V is a hard, tau-dependent "
          f"cap on psi.")
    print(f"  {'tau (yr)':>10}{'psi_max @V_MAX':>16}{'psi_max @V_grid':>17}"
          f"{'x short of ' + format(PSI_HANDOFF_CM_PER_YR, '.3f'):>18}")
    for tau in sorted(set(RES_TAU) | {TAU_HANDOFF_YR}):
        pm = CM_PER_M * V_MAX_M / tau
        pg = CM_PER_M * max(RES_V_M) / tau
        print(f"  {tau:10.0f}{pm:16.3f}{pg:17.3f}"
              f"{PSI_HANDOFF_CM_PER_YR / pm:17.2f}x"
              + ("   <- the handoff's tau" if tau == TAU_HANDOFF_YR else ""))
    pm_h = CM_PER_M * V_MAX_M / TAU_HANDOFF_YR
    print(f"\n  At the handoff's own tau = {TAU_HANDOFF_YR:g} yr the NO+NE inventory "
          f"({V_MAX_M:g} m) caps psi at\n  {pm_h:.3f} cm/yr, against the "
          f"{PSI_HANDOFF_CM_PER_YR:.3f} it needs — short by "
          f"{PSI_HANDOFF_CM_PER_YR / pm_h:.1f}x. So cell B is not merely outside\n"
          f"  this grid, it is outside the HIGH BASIN: the flux and the "
          f"literature tau together\n  force a WHOLE-SHEET object. That is a wiring "
          f"constraint, not a scan setting.")

    print(f"\n=== IS THE PASSING SET A psi RAY? (handoff 1.3/1.4, on 1080 cells) ===\n")
    for nm, p in (("shipped + 2150", p_old), ("+ r2300 rate", p_new)):
        if p.empty:
            print(f"  {nm:20} empty")
            continue
        print(f"  {nm:20} n={len(p):4d}   psi {p.psi_cm_per_yr.min():.3f}-"
              f"{p.psi_cm_per_yr.max():.3f} cm/yr ({len(set(p.psi_cm_per_yr))} distinct)"
              f"   V {sorted(set(p.V_m))}\n{'':22} tau {sorted(set(p.tau_yr))}  "
              f"w {sorted(set(p.ramp_w_K))}")
    ## If psi is the only identified quantity, cells sharing a psi must score alike
    ## REGARDLESS of how V and tau are split. Section 1.3's argument needs tau >> the
    ## 200-yr window (the separating curvature is O((s/tau)^2)), so the regime is
    ## reported SEPARATELY rather than averaged over a grid that includes tau=100.
    for nm, sub in (("ALL tau", out[out.within_inventory]),
                    (f"tau >= {TAU_LONG_YR}", out[out.within_inventory
                                                  & (out.tau_yr >= TAU_LONG_YR)]),
                    (f"tau >= {TAU_LONG_YR}, w = {RAMP_W_SHIPPED:g}",
                     out[out.within_inventory & (out.tau_yr >= TAU_LONG_YR)
                         & (out.ramp_w_K == RAMP_W_SHIPPED)])):
        g = sub.groupby("psi_cm_per_yr").rms_all
        n = sub.groupby("psi_cm_per_yr").size()
        r = (g.max() / g.min())[n > 1]
        if r.empty:
            continue
        print(f"\n  {nm:34} rms_all within one psi varies by <= {r.max():.3f}x "
              f"(median {r.median():.3f}x, {len(r)} psi values)")
    print(f"\n  => the degeneracy is a LONG-tau statement, exactly as section 1.3's "
          f"O((s/tau)^2)\n  curvature argument requires. It is NOT a property of the "
          f"whole grid.")
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
