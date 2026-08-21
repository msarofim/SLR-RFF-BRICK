#!/usr/bin/env python3
"""
scope_gis_basin_zonespace_vs_literature.py — the basin mock, re-expressed on
PER-ZONE regional drivers instead of GMST. Handoff 2026-08-18c section 6 item 1.

WHY THIS EXISTS
  The GMT-space mock (scope_gis_basin_mock_vs_literature.py) is the first
  structure to clear the whole 2300 scorecard — 59/720 cells, ratio 10.1-17.6x
  against a literature demand of 7.9-31.9x. It placed dormant-basin onsets in
  GMST because per-zone drivers did not exist. They do now (tier 2a/2b). A
  dormant basin in NE/NO does not feel GMST; it feels its own zone's
  temperature. This script re-runs the identical scorecard with each dormant
  basin on its own driver, and asks whether the pass region SURVIVES.

  The pre-check (diag_gis_zone_driver_scope.py) established the two things this
  translation rests on: the GMT -> zone-driver map along SSP5-8.5 is strictly
  increasing over the whole (3.15, 7.81] K bracket (so onsets are 1:1), and
  every translated onset stays above SSP1-2.6/SSP2-4.5's 2300 zone drivers by
  at least 1.30 K (so the basins stay inert on the low scenarios). What did NOT
  translate is the ramp width — see W below.

THE FOUR METHODOLOGICAL CHOICES (Marcus, 2026-08-18; standing rule: these are
never resolved silently)
  1. MID basin -> the CENTRAL zone (70-77 N), HIGH basin -> NORTH (77-84 N).
     Stated caveat, carried from tier 1: central is ~CW/CE/NW latitudes, not NW
     specifically, so the mid driver is broader than the basin it stands for.
  2. AMP WINDOW = full, for both dormant zones — matching the shipped south
     choice (Ladrillo 1.0 uses south/full = 1.922). north full N(2.83, 0.92),
     central full N(2.36, 0.53).
  3. RAMP WIDTH W = GMT-EQUIVALENT per zone. The mock's fixed 1 K GMT ramp is
     1.6 K (south) / 2.1 K (central) / 2.7 K (north) in zone units, so holding
     W = 1 K in zone units would SHARPEN the onset by those factors. Setting
     W_zone = D_zone(T_on + 1 K) - D_zone(T_on) makes this run a pure
     re-parameterisation of the GMT-space mock: any change in the pass region
     is then attributable to the DRIVER, not to a smuggled change in W.
  4. The dormant basins are PROJECTION-SIDE ONLY. They are inert until 2087 at
     the earliest, so the hindcast carries no information about them and the
     calibrator is not touched. L12 stays canonical; no chain is run.

AMP PROVENANCE, STATED. The incumbent south basin keeps the POSTERIOR amp
(pa["gis_amp"]) and the shipped `regional_driver` — it is unchanged, and gated
as such. The dormant zones have no posterior, so they use the OBSERVED prior
MEAN amp for their zone/window from outputs/gis_amp_prior.csv. Those are two
different kinds of number and the script prints both rather than blending them.

THE QUESTIONS, FIXED BEFORE RUNNING
  Z1  does the pass region SURVIVE the move to zone space — how many of the 720
      cells clear the full scorecard, and how does the set compare to the 59?
  Z2  is the change attributable to the driver? Reported as the per-cell shift
      in ssp585 dormant loss vs the GMT-space run, since W is GMT-equivalent.
  Z3  does the move to zone space make any basin ACTIVE on a low scenario that
      was INERT in GMT space? A HARD PARITY gate, not an absolute one. The
      distinction matters and a first draft got it wrong: the 2.5 and 3.0 K mid
      onsets sit BELOW ssp245's 2300 GMT of 3.15 K, so they are already active
      on ssp245 in GMT space (unit response 0.541 and 0.114 at tau=100). Gating
      those against zero would have reported the mock's own grid as a
      zone-splice failure. What must hold is PARITY — inert in GMT space implies
      inert in zone space — plus, for the deliverable, dormant loss identically
      zero on ssp126/245 among the PASSING cells (as it is in GMT space, where
      the passer maximum is exactly 0.0).
  FALSIFIER: if the pass region collapses, or survives only by cells that were
  failing in GMT space, the zone splice — not the basin structure — is doing
  the work, and that is a finding to report, not to tune away.

READS   the GMT-space mock (grid, scorecard, unit-response form), the ridge
        harness (posterior, targets, bands), the per-zone drivers and amp
        tables, outputs/scope_gis_basin_mock_vs_literature.csv (the comparand)
WRITES  outputs/scope_gis_basin_zonespace_vs_literature.csv

  source ~/climate-env/bin/activate
  python3 python/scope_gis_basin_zonespace_vs_literature.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
import scope_gis_basin_mock_vs_literature as mock  # noqa: E402
import scope_gis_leq_ridge_vs_literature as ridge  # noqa: E402
from scope_gis_2300_relaxation import (  # noqa: E402
    GIS_V0_M, IREF, SSPS, YEARS, gis_shape_table, gmst_rebased, regional_driver,
)
from diag_gis_zone_driver_scope import (  # noqa: E402
    SPLICE_START, amp_mean, shape_fun, zone_driver,
)

# --- the four choices, as named constants; every label derives from these ----
ZONE_OF = {"mid": "central", "high": "north"}      # choice 1
AMP_WINDOW = "full"                                # choice 2
W_MODE = "gmt_equivalent"                          # choice 3
CALIBRATOR_SIDE = False                            # choice 4 — projection only
CHOICE_TAG = (f"mid={ZONE_OF['mid']}, high={ZONE_OF['high']}, amp={AMP_WINDOW}, "
              f"W={W_MODE}, calibrator={'yes' if CALIBRATOR_SIDE else 'NO'}")

# --- inherited, unchanged, from the GMT-space mock --------------------------
LADRILLO_TAG = mock.LADRILLO_TAG
POST, TARGETS = mock.POST, mock.TARGETS
HIND, HIND_DRIVER = mock.HIND, mock.HIND_DRIVER
## 2026-08-21g: the 2300 bands come from gis_targets, which carries BOTH the raw
## literature set and the forcing-matched one. Default MATCHED. This scorecard has
## NOT been re-run under the matched set (see the 2026-08-21g handoff §5) -- the
## banner below is what makes that visible the moment anyone does.
import gis_targets  # noqa: E402
LIT_2300_M, TARGET_SET = gis_targets.from_argv(sys.argv)
TARGET_WORD = gis_targets.SET_WORD[TARGET_SET]
RIDGE_CSV = mock.RIDGE_CSV
G4_DEGRADE_TOL, REPRO_TOL = mock.G4_DEGRADE_TOL, mock.REPRO_TOL
GMT_2300_EXPECT, GMT_2300_TOL = mock.GMT_2300_EXPECT, mock.GMT_2300_TOL
T_ON_MID, T_ON_HIGH = mock.T_ON_MID, mock.T_ON_HIGH
V_TOT, MID_SHARE, TAU = mock.V_TOT, mock.MID_SHARE, mock.TAU
RAMP_W_GMT_K = mock.RAMP_W

GMT_MOCK_CSV = mock.OUT
OUT = gis_targets.out_path(
    os.path.join(REPO, "outputs/scope_gis_basin_zonespace_vs_literature.csv"), TARGET_SET)
INERT_TOL = 0.0            # choice-3 gate Z3: dormant loss on ssp126/245 must be 0
MAP_SSP = "SSP5-8.5"       # the only scenario reaching the onsets (mock F3)


def translate(gmt_rb, drv, t_on_gmt):
    """Map a GMT-space onset onto a zone driver along the SSP5-8.5 path, and
    return the GMT-equivalent ramp width there. Returns (T_on_zone, W_zone)."""
    ok = (YEARS >= SPLICE_START) & (gmt_rb >= t_on_gmt)
    if not ok.any():
        return np.nan, np.nan
    t_zone = float(drv[np.where(ok)[0][0]])
    hi = (YEARS >= SPLICE_START) & (gmt_rb >= t_on_gmt + RAMP_W_GMT_K)
    if hi.any():
        w = float(drv[np.where(hi)[0][0]]) - t_zone
    else:                      # onset + W is past this scenario's 2300 warming
        j = np.where(ok)[0][0]
        w = float((drv[-1] - t_zone) / max(gmt_rb[-1] - t_on_gmt, 1e-9)
                  * RAMP_W_GMT_K) if gmt_rb[-1] > t_on_gmt else np.nan
        del j
    return t_zone, w


def dormant_unit_zone(D, t_on_zone, w_zone, tau):
    """Unit-volume dormant basin on a ZONE driver. Identical form to the
    GMT-space mock.dormant_unit, with (D, t_on_zone, w_zone) in place of
    (G, t_on, RAMP_W)."""
    seq = np.clip((D - t_on_zone) / w_zone, 0.0, 1.0)
    S = np.zeros_like(D)
    r = 1.0 / tau
    for i in range(1, len(D)):
        S[i] = S[i - 1] + (seq[i - 1] - S[i - 1]) * r
    return S


def main():
    post = pd.read_csv(POST)
    tbar = ridge.gis_tbar()
    pa = ridge.native_greenland(post.median(numeric_only=True), tbar)
    S_south = gis_shape_table()

    drivers, gmt, zdrv = {}, {}, {b: {} for b in ZONE_OF}
    zamp = {b: amp_mean(ZONE_OF[b], AMP_WINDOW) for b in ZONE_OF}
    zshape = {b: shape_fun(ZONE_OF[b]) for b in ZONE_OF}
    for ssp, label in SSPS:
        _, rb = gmst_rebased(ssp)
        gmt[label] = rb
        drivers[label] = regional_driver(rb, np.array([pa["gis_amp"]]), S_south)[0]
        for b in ZONE_OF:
            zdrv[b][label], _ = zone_driver(rb, ZONE_OF[b], zamp[b], zshape[b])

    i21 = int(np.where(YEARS == 2100)[0][0])
    i23 = int(np.where(YEARS == 2300)[0][0])
    ih0 = int(np.where(YEARS == HIND[0])[0][0])
    ih1 = int(np.where(YEARS == HIND[1])[0][0])
    for _, lab in SSPS:
        got = float(gmt[lab][i23])
        if abs(got - GMT_2300_EXPECT[lab]) > GMT_2300_TOL:
            raise SystemExit(f"GMT frame check failed: {lab} @2300 = {got:.3f} "
                             f"vs recorded {GMT_2300_EXPECT[lab]}")

    # ---- incumbent south basin: identical to the GMT mock, gated as such ----
    tgt = pd.read_csv(TARGETS).set_index("year")["gis"]
    want_cm = float(tgt.loc[HIND[1]] - tgt.loc[HIND[0]])
    Th = drivers[dict(SSPS)[HIND_DRIVER]]
    lo, hi = 1e-4, 1e3
    for _ in range(80):
        m = np.sqrt(lo * hi)
        L = ridge.ab_series(Th, pa, 1.0, m)[0]
        if 100.0 * (L[ih1] - L[ih0]) < want_cm:
            lo = m
        else:
            hi = m
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

    print(f"THE BASIN MOCK IN ZONE SPACE — Ladrillo {LADRILLO_TAG}, median "
          f"params, offline")
    print(f"  choices: {CHOICE_TAG}")
    print(f"  south basin = shipped A+B (k=1, s={s1:.4f}, POSTERIOR amp "
          f"{pa['gis_amp']:.4f}); ridge k=1 gate PASSED ({max(gate):.1e})")
    print("  dormant-zone amp = OBSERVED PRIOR MEAN (no posterior exists): "
          + ", ".join(f"{b}/{ZONE_OF[b]}/{AMP_WINDOW} {zamp[b]:.4f}" for b in ZONE_OF))
    print(f"  inventory headroom: {inv_head:.2f} m\n")

    # ---- translate every onset, per basin, and record W --------------------
    tr = {}
    print(f"=== onset translation (along {MAP_SSP}; W is GMT-equivalent) ===\n")
    print(f"  {'basin':5s} {'zone':8s} {'T_on GMT':>9s} {'T_on zone':>10s} "
          f"{'W zone':>7s} {'W ratio':>8s}")
    for b, grid in (("mid", T_ON_MID), ("high", T_ON_HIGH)):
        for t in grid:
            tz, wz = translate(gmt[MAP_SSP], zdrv[b][MAP_SSP], t)
            tr[(b, t)] = (tz, wz)
            print(f"  {b:5s} {ZONE_OF[b]:8s} {t:9.1f} {tz:10.2f} {wz:7.2f} "
                  f"{wz / RAMP_W_GMT_K:8.2f}")
    print()

    # ---- unit responses on the ZONE drivers --------------------------------
    unit = {}
    for b, grid in (("mid", T_ON_MID), ("high", T_ON_HIGH)):
        for t in grid:
            tz, wz = tr[(b, t)]
            for tau in TAU:
                for _, lab in SSPS:
                    unit[(b, t, tau, lab)] = dormant_unit_zone(
                        zdrv[b][lab], tz, wz, tau)

    # ---- Z3 HARD PARITY GATE vs the GMT-space run --------------------------
    print("=== Z3 parity gate — inert in GMT space must imply inert in zone "
          "space ===\n")
    viol, checked, already = [], 0, 0
    for b, grid in (("mid", T_ON_MID), ("high", T_ON_HIGH)):
        for t in grid:
            for tau in TAU:
                for _, lab in SSPS:
                    if lab == MAP_SSP:
                        continue
                    g_resp = float(np.abs(mock.dormant_unit(gmt[lab], t, tau)).max())
                    z_resp = float(np.abs(unit[(b, t, tau, lab)]).max())
                    if g_resp > INERT_TOL:
                        already += 1          # active in GMT space too — not ours
                        continue
                    checked += 1
                    if z_resp > INERT_TOL:
                        viol.append((b, t, tau, lab, z_resp))
    print(f"  {checked} (basin, onset, tau, scenario) combinations are inert in "
          f"GMT space and must stay inert")
    print(f"  {already} are ALREADY active in GMT space (mid onsets below "
          f"ssp245's 2300 GMT of {GMT_2300_EXPECT['SSP2-4.5']} K) — the mock's "
          f"own grid, not a zone-space effect")
    if viol:
        for v in viol[:10]:
            print(f"    VIOLATION {v[0]}/{v[1]} K, tau {v[2]}, {v[3]}: {v[4]:.3e}")
        raise SystemExit(
            f"Z3 PARITY GATE FAILED: {len(viol)} combinations activate on a low "
            "scenario only in zone space. That is a finding about the zone "
            "splice — report it, do not tune W.")
    print("  VERDICT Z3: PASS — no combination activates on a low scenario that "
          "was inert in GMT space\n")

    # ---- the scorecard, cell for cell identical to the GMT-space mock -------
    rows, seen = [], set()
    for t_mid in T_ON_MID:
        for t_high in T_ON_HIGH:
            if t_high <= t_mid:
                continue
            for vt in V_TOT:
                for sh in MID_SHARE:
                    for tau in TAU:
                        key = (t_mid if sh > 0 else None, t_high, vt, sh, tau)
                        if key in seen:
                            continue
                        seen.add(key)
                        v_mid, v_high = sh * vt, (1 - sh) * vt
                        r = dict(tag=LADRILLO_TAG, choices=CHOICE_TAG,
                                 t_on_mid=t_mid, t_on_high=t_high, v_tot=vt,
                                 mid_share=sh, tau=tau, v_mid=v_mid,
                                 v_high=v_high,
                                 t_on_mid_zone=tr[("mid", t_mid)][0],
                                 t_on_high_zone=tr[("high", t_high)][0],
                                 w_mid_zone=tr[("mid", t_mid)][1],
                                 w_high_zone=tr[("high", t_high)][1])
                        for _, lab in SSPS:
                            um = unit[("mid", t_mid, tau, lab)]
                            uh = unit[("high", t_high, tau, lab)]
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

    # ---- Z1/Z2: against the GMT-space run ----------------------------------
    key = ["t_on_mid", "t_on_high", "v_tot", "mid_share", "tau"]
    gmtdf = pd.read_csv(GMT_MOCK_CSV)
    j = df.merge(gmtdf, on=key, suffixes=("_zone", "_gmt"))
    assert len(j) == len(df), f"cell-for-cell join lost rows: {len(j)} vs {len(df)}"
    both = int((j.all_pass_zone & j.all_pass_gmt).sum())
    only_z = int((j.all_pass_zone & ~j.all_pass_gmt).sum())
    only_g = int((~j.all_pass_zone & j.all_pass_gmt).sum())
    d585 = j["dorm2300_SSP5-8.5_zone"] - j["dorm2300_SSP5-8.5_gmt"]

    # ---- Z3b: the deliverable gate, on the PASSING cells -------------------
    lowmax = {lab: float(winners[f"dorm2300_{lab}"].abs().max()) if len(winners)
              else 0.0 for _, lab in SSPS if lab != MAP_SSP}
    print(f"\n=== Z3b: dormant loss among PASSERS on the low scenarios ===\n")
    for lab, v in lowmax.items():
        print(f"  {lab:9s} max |dorm2300| over passers = {v:.3e} m SLE")
    if max(lowmax.values(), default=0.0) > INERT_TOL:
        raise SystemExit("Z3b FAILED: a passing cell moves ssp126/245 at 2300; "
                         "they would no longer be bit-identical to shipped")
    print("  VERDICT Z3b: PASS — ssp126/245 stay bit-identical to shipped\n")

    print(f"=== Z1: pass region vs the GMT-space mock ===\n")
    print(f"  zone-space passers {int(df.all_pass.sum())}   "
          f"GMT-space passers {int(gmtdf.all_pass.sum())}")
    print(f"  in BOTH {both}   zone-space ONLY {only_z}   GMT-space ONLY {only_g}")
    print(f"\n=== Z2: per-cell shift in ssp585 dormant loss (m SLE @2300) ===\n")
    print(f"  median {d585.median():+.4f}   mean {d585.mean():+.4f}   "
          f"range [{d585.min():+.4f}, {d585.max():+.4f}]")
    print(f"  as a fraction of the GMT-space dormant loss: median "
          f"{(d585 / j['dorm2300_SSP5-8.5_gmt'].replace(0, np.nan)).median():+.3%}")

    if len(winners):
        print("\n=== the passing REGION (values represented among passers) ===\n")
        act = winners[winners.mid_share > 0]
        for knob in key:
            vals = sorted(float(v) for v in winners[knob].unique())
            print(f"  {knob:10s} {vals}")
        print(f"  {'t_on_mid':10s} among passers with an ACTIVE mid basin: "
              f"{sorted(float(v) for v in act.t_on_mid.unique())} — the other "
              f"t_on_mid values above are mid_share=0 PLACEHOLDERS (the dedupe "
              f"keeps the first inert value); do not read them as onsets")
        print(f"  ratio span  {winners.ratio_585_over_245.min():.1f}x - "
              f"{winners.ratio_585_over_245.max():.1f}x  "
              f"(lit {lit_lo:.1f}-{lit_hi:.1f}x)")
        print(f"  G4 span     {winners.g4_rel_to_ref.min():.3f}x - "
              f"{winners.g4_rel_to_ref.max():.3f}x of shipped")
        print(f"  cells with an ACTIVE mid basin: "
              f"{int((winners.mid_share > 0).sum())}; single-dormant-basin: "
              f"{int((winners.mid_share == 0).sum())}")

        mid585 = 0.5 * sum(LIT_2300_M["SSP5-8.5"])
        w = winners.copy()
        w["margin"] = -(w["m2300_SSP5-8.5"] - mid585).abs()
        w = w.sort_values("margin", ascending=False)
        cols = key + ["t_on_high_zone", "w_high_zone", "m2300_SSP1-2.6",
                      "m2300_SSP2-4.5", "m2300_SSP5-8.5", "g4_rel_to_ref",
                      "ratio_585_over_245"]
        print("\n=== exemplars (widest 585 margin, median, narrowest) ===\n")
        print(w.iloc[[0, len(w) // 2, -1]][cols].to_string(
            index=False, float_format=lambda v: f"{v:.3f}"))
    else:
        print("\n=== NO cell clears the scorecard in zone space — see Z2 ===")

    df.to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
