#!/usr/bin/env python3
"""
scope_gis_basin_mock_vs_literature.py — can a MULTI-BASIN Greenland (the GSIC
three-group move) clear the whole 2300 scorecard, offline, before pricing it?

WHY THIS EXISTS (2026-08-18, after both single-law fixes measured dead)
  The Leq(T) ridge caps the ssp585/ssp245 ratio at 3.36x; the convex fast-rate
  law peaks at 4.71x and falls back; literature demands 7.9-31.9x. Both die the
  same death: ONE LAW ties the scenarios together. The glacier precedent
  (glaciers_nu3: R19/SLOWP/FAST, per-block onsets and rates) fixed exactly this
  disease for GSIC — a single reservoir's railed fit compressed the scenario
  spread; three blocks with their own onsets restored it. This mock asks
  whether the same structural move works for Greenland: the shipped A+B stays
  as the hindcast-bearing SOUTH basin (it is RIGHT at ssp126/ssp245), and
  DORMANT northern basins with staggered onsets add commitment that ssp245
  never touches and ssp585 realises.

THE MOCK STRUCTURE (a feasibility scan, not a calibration)
    L_total = A+B(shipped, k=1, s re-bisected)  +  sum_b S_b
    S_eq,b(G) = V_b * clip((G - T_on_b) / W, 0, 1)      G = GMST rel 1850-1900
    S_b[i]    = S_b[i-1] + (S_eq,b(G[i-1]) - S_b[i-1]) / tau_b
  Two dormant basins: MID (~NW, moderate onset) and HIGH (~NE+N, high onset).
  mid_share = 0 collapses to a SINGLE dormant basin — a structural variant, not
  a degenerate cell. Onsets are in GMT SPACE because per-zone regional drivers
  do not exist yet (t_gis_zones.csv carries only south/all); a per-zone driver
  would RESCALE onsets, not change feasibility. Symmetric relaxation is fine
  here because no scenario declines through an onset (ssp126 peaks at 1.92 K,
  below every onset in the grid). W is fixed: the grid's job is the region,
  not the boundary's sharpness.

THE QUESTIONS, FIXED BEFORE RUNNING
  F1  does ANY cell clear the full scorecard (three 2300 bands + G4 within 15%
      of the shipped spread)?  [the ratio band is implied by the 585+245 bands]
  F2  is the passing region CONTIGUOUS and multi-knob (robust), or a knife-edge?
  F3  are its onsets physically placed — i.e. BETWEEN the scenarios' 2300 GMTs
      (3.15 and 7.81 K) — and its volumes within the remaining inventory
      (V_tot <= V0 - Leq_incumbent(T585@2300) = 7.42 - 0.54)?
  FALSIFIER: if passing cells need onsets BELOW ssp245's 2300 GMT, or only the
  fastest tau, the structure would be tuning, not physics.

READS   the ridge harness (posterior, drivers, targets, bands) +
        outputs/scope_gis_leq_ridge_vs_literature.csv (gate, k=1 row)
WRITES  outputs/scope_gis_basin_mock_vs_literature.csv

  source ~/climate-env/bin/activate
  python3 python/scope_gis_basin_mock_vs_literature.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
import scope_gis_leq_ridge_vs_literature as ridge  # noqa: E402
from scope_gis_2300_relaxation import (  # noqa: E402
    GIS_V0_M, IREF, YEARS, gis_shape_table, gmst_rebased, regional_driver,
)

# --- named constants; every label below derives from these -------------------
LADRILLO_TAG = ridge.LADRILLO_TAG
POST, TARGETS = ridge.POST, ridge.TARGETS
HIND, HIND_DRIVER, SSPS = ridge.HIND, ridge.HIND_DRIVER, ridge.SSPS
## 2026-08-21g: the 2300 bands come from gis_targets, which carries BOTH the raw
## literature set and the forcing-matched one. Default MATCHED. This scorecard has
## NOT been re-run under the matched set (see the 2026-08-21g handoff §5) -- the
## banner below is what makes that visible the moment anyone does.
import gis_targets  # noqa: E402
LIT_2300_M, TARGET_SET = gis_targets.from_argv(sys.argv)
TARGET_WORD = gis_targets.SET_WORD[TARGET_SET]
RIDGE_CSV = ridge.OUT
OUT = gis_targets.out_path(
    os.path.join(REPO, "outputs/scope_gis_basin_mock_vs_literature.csv"), TARGET_SET)

G4_DEGRADE_TOL = ridge.G4_DEGRADE_TOL        # >15% change in 2100 spread = broken
REPRO_TOL = 1e-9
GMT_2300_EXPECT = {"SSP1-2.6": 1.74, "SSP2-4.5": 3.15, "SSP5-8.5": 7.81}
GMT_2300_TOL = 0.05                          # frame check vs the recorded values

# the grid — structural knobs, NOT fitted parameters
T_ON_MID = [2.5, 3.0, 3.5, 4.0, 5.0]         # GMT K rel 1850-1900, ~NW basin
T_ON_HIGH = [5.0, 6.0, 7.0]                  # ~NE+N basin; must exceed the mid
V_TOT = [1.5, 2.5, 3.5, 4.5]                 # dormant committed volume, m SLE
MID_SHARE = [0.0, 0.3, 0.5, 0.7]             # 0.0 = single dormant basin
TAU = [50, 100, 200, 400]                    # e-folding once active, yr
RAMP_W = 1.0                                 # K; onset softness, fixed


def dormant_unit(G, t_on, tau):
    """Unit-volume dormant basin: S_eq = clip((G - t_on)/W, 0, 1), first-order
    relaxation at rate 1/tau with the same t-1 lag the other modules use.
    Loss is LINEAR in V, so V multiplies this afterwards."""
    seq = np.clip((G - t_on) / RAMP_W, 0.0, 1.0)
    S = np.zeros_like(G)
    r = 1.0 / tau
    for i in range(1, len(G)):
        S[i] = S[i - 1] + (seq[i - 1] - S[i - 1]) * r
    return S


def main():
    post = pd.read_csv(POST)
    tbar = ridge.gis_tbar()
    pa = ridge.native_greenland(post.median(numeric_only=True), tbar)
    S = gis_shape_table()

    drivers, gmt = {}, {}
    for ssp, label in SSPS:
        _, rb = gmst_rebased(ssp)
        gmt[label] = rb
        drivers[label] = regional_driver(rb, np.array([pa["gis_amp"]]), S)[0]

    i21 = int(np.where(YEARS == 2100)[0][0])
    i23 = int(np.where(YEARS == 2300)[0][0])
    ih0 = int(np.where(YEARS == HIND[0])[0][0])
    ih1 = int(np.where(YEARS == HIND[1])[0][0])
    for _, lab in SSPS:
        got = float(gmt[lab][i23])
        if abs(got - GMT_2300_EXPECT[lab]) > GMT_2300_TOL:
            raise SystemExit(f"GMT frame check failed: {lab} @2300 = {got:.3f} "
                             f"vs recorded {GMT_2300_EXPECT[lab]}")

    # ---- the incumbent south basin: k=1, s re-bisected, gated vs the ridge --
    tgt = pd.read_csv(TARGETS).set_index("year")["gis"]
    want_cm = float(tgt.loc[HIND[1]] - tgt.loc[HIND[0]])
    Th = drivers[dict(SSPS)[HIND_DRIVER]]
    lo, hi = 1e-4, 1e3
    for _ in range(80):
        mid = np.sqrt(lo * hi)
        L = ridge.ab_series(Th, pa, 1.0, mid)[0]
        if 100.0 * (L[ih1] - L[ih0]) < want_cm:
            lo = mid
        else:
            hi = mid
    s1 = float(np.sqrt(lo * hi))

    rec = pd.read_csv(RIDGE_CSV).set_index("k")
    inc2300, inc2100 = {}, {}
    for _, lab in SSPS:
        L, _ = ridge.ab_series(drivers[lab], pa, 1.0, s1)
        inc2300[lab] = float(L[i23] - L[IREF].mean())
        inc2100[lab] = float(L[i21] - L[IREF].mean())
    gate = [abs(s1 - float(rec.loc[1.0, "rate_scale"]))]
    gate += [abs(inc2300[lab] - float(rec.loc[1.0, f"m2300_{lab}"]))
             for _, lab in SSPS]
    if max(gate) > REPRO_TOL:
        raise SystemExit(f"REPRODUCTION GATE FAILED: max diff {max(gate):.2e} "
                         f"vs the ridge k=1 row — refusing to scan")
    g4_ref = float(rec.loc[1.0, "g4_2100_cm"])
    inv_head = GIS_V0_M - float(np.clip(pa["gis_c1"] * drivers["SSP5-8.5"][i23]
                                        + pa["gis_c0"], 0, GIS_V0_M))

    print(f"CAN A MULTI-BASIN GREENLAND CLEAR THE 2300 SCORECARD?  — Ladrillo "
          f"{LADRILLO_TAG}, median params, offline mock")
    print(f"  south basin = shipped A+B (k=1, s={s1:.4f}); reproduction gate "
          f"PASSED vs the ridge k=1 row ({max(gate):.1e})")
    print(f"  incumbent @2300: " + "  ".join(f"{lab} {inc2300[lab]:.3f}"
                                             for _, lab in SSPS)
          + f";  G4 ref {g4_ref:.2f} cm; dormant G4 headroom "
          f"{G4_DEGRADE_TOL * g4_ref:.2f} cm at 2100")
    print(f"  inventory headroom for dormant volume: {inv_head:.2f} m "
          f"(= V0 {GIS_V0_M} - incumbent Leq at ssp585/2300)")
    yrs585 = {t: (int(YEARS[np.argmax(gmt['SSP5-8.5'] >= t)])
                  if (gmt['SSP5-8.5'] >= t).any() else None)
              for t in sorted(set(T_ON_MID + T_ON_HIGH))}
    print("  ssp585 GMT crossing years: "
          + "  ".join(f"{t:g}K:{y}" for t, y in yrs585.items()) + "\n")

    # ---- unit responses: one integration per (onset, tau, scenario) ---------
    onsets = sorted(set(T_ON_MID + T_ON_HIGH))
    unit = {(t_on, tau, lab): dormant_unit(gmt[lab], t_on, tau)
            for t_on in onsets for tau in TAU for _, lab in SSPS}

    rows, seen = [], set()
    for t_mid in T_ON_MID:
        for t_high in T_ON_HIGH:
            if t_high <= t_mid:
                continue
            for vt in V_TOT:
                for sh in MID_SHARE:
                    for tau in TAU:
                        key = (t_mid if sh > 0 else None, t_high, vt, sh, tau)
                        if key in seen:      # mid onset is inert at share 0
                            continue
                        seen.add(key)
                        v_mid, v_high = sh * vt, (1 - sh) * vt
                        r = dict(tag=LADRILLO_TAG, t_on_mid=t_mid,
                                 t_on_high=t_high, v_tot=vt, mid_share=sh,
                                 tau=tau, v_mid=v_mid, v_high=v_high)
                        for _, lab in SSPS:
                            um = unit[(t_mid, tau, lab)]
                            uh = unit[(t_high, tau, lab)]
                            d23 = v_mid * um[i23] + v_high * uh[i23]
                            d21 = v_mid * um[i21] + v_high * uh[i21]
                            r[f"m2300_{lab}"] = inc2300[lab] + d23
                            r[f"dorm2300_{lab}"] = d23
                            r[f"dorm2100_{lab}"] = d21
                            r[f"in_band_{lab}"] = (
                                LIT_2300_M[lab][0] <= r[f"m2300_{lab}"]
                                <= LIT_2300_M[lab][1])
                        g4 = (100.0 * (inc2100["SSP5-8.5"] - inc2100["SSP1-2.6"])
                              + 100.0 * (r["dorm2100_SSP5-8.5"]
                                         - r["dorm2100_SSP1-2.6"]))
                        r["g4_2100_cm"] = g4
                        r["g4_rel_to_ref"] = g4 / g4_ref
                        r["keeps_2100"] = abs(g4 / g4_ref - 1.0) <= G4_DEGRADE_TOL
                        r["ratio_585_over_245"] = (r["m2300_SSP5-8.5"]
                                                   / r["m2300_SSP2-4.5"])
                        r["within_inventory"] = vt <= inv_head
                        r["all_pass"] = (all(r[f"in_band_{lab}"] for _, lab in SSPS)
                                         and r["keeps_2100"]
                                         and r["within_inventory"])
                        rows.append(r)

    df = pd.DataFrame(rows)
    winners = df[df.all_pass]

    # ---- census: which constraint kills the failing cells -------------------
    lit_lo, lit_hi = gis_targets.ratio_band(LIT_2300_M)
    print("  " + gis_targets.banner(TARGET_SET).replace("\n", "\n  "))
    print(f"=== CENSUS — {len(df)} cells ===\n")
    for crit, ok in [("SSP1-2.6 band @2300", df["in_band_SSP1-2.6"]),
                     ("SSP2-4.5 band @2300", df["in_band_SSP2-4.5"]),
                     ("SSP5-8.5 band @2300", df["in_band_SSP5-8.5"]),
                     (f"2100 kept (<= {100 * G4_DEGRADE_TOL:.0f}%)", df.keeps_2100),
                     ("within inventory", df.within_inventory),
                     ("ALL PASS", df.all_pass)]:
        print(f"  {crit:24s} {int(ok.sum()):4d} / {len(df)}")

    print(f"\n=== F1: {'YES — ' + str(len(winners)) + ' cells clear everything'
                       if len(winners) else 'NO cell clears everything'} ===")
    if len(winners):
        print("\n=== F2: the passing REGION (values represented among passers) ===\n")
        for knob in ["t_on_mid", "t_on_high", "v_tot", "mid_share", "tau"]:
            vals = sorted(winners[knob].unique())
            print(f"  {knob:10s} {vals}")
        print(f"  ratio span  {winners.ratio_585_over_245.min():.1f}x - "
              f"{winners.ratio_585_over_245.max():.1f}x  "
              f"(lit {lit_lo:.1f}-{lit_hi:.1f}x)")
        print(f"  G4 span     {winners.g4_rel_to_ref.min():.3f}x - "
              f"{winners.g4_rel_to_ref.max():.3f}x of shipped")

        print("\n=== exemplar passing cells (widest 585 margin, then median, "
              "then narrowest) ===\n")
        mid585 = 0.5 * sum(LIT_2300_M["SSP5-8.5"])
        w = winners.copy()
        w["margin"] = -(w["m2300_SSP5-8.5"] - mid585).abs()
        w = w.sort_values("margin", ascending=False)
        pick = w.iloc[[0, len(w) // 2, -1]]
        cols = ["t_on_mid", "t_on_high", "v_tot", "mid_share", "tau",
                "m2300_SSP1-2.6", "m2300_SSP2-4.5", "m2300_SSP5-8.5",
                "dorm2100_SSP5-8.5", "g4_rel_to_ref", "ratio_585_over_245"]
        print(pick[cols].to_string(index=False,
                                   float_format=lambda v: f"{v:.3f}"))

        print("\n=== F3: physical placement ===\n")
        bind = winners.t_on_high if (winners.mid_share == 0).all() else \
            winners[["t_on_mid", "t_on_high"]].min(axis=1)
        active_mid = winners[winners.mid_share > 0]
        print(f"  binding onsets among passers: min {bind.min():g} K, "
              f"max {winners.t_on_high.max():g} K "
              f"(scenarios' 2300 GMTs: 3.15 / 7.81 K)")
        print(f"  cells passing WITH an active mid basin: {len(active_mid)}; "
              f"single-dormant-basin passers: {int((winners.mid_share == 0).sum())}")
        below245 = winners[(winners.mid_share > 0)
                           & (winners.t_on_mid < GMT_2300_EXPECT['SSP2-4.5'])]
        print(f"  passers whose MID onset sits below ssp245's 2300 GMT: "
              f"{len(below245)} (falsifier watches this being the ONLY mode)")
    else:
        near = df.sort_values("all_pass", ascending=False)
        nb = df[df[[f"in_band_{lab}" for _, lab in SSPS]].sum(axis=1) == 3]
        print(f"  cells with all three 2300 bands but 2100 broken: {len(nb)}")

    df.to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
