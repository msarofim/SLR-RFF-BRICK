#!/usr/bin/env python3
"""
diag_gis_zone_driver_scope.py — before wiring the basin mock into ZONE space,
measure the one thing the wiring assumes: is the GMT -> zone-driver map
MONOTONE and SCENARIO-STABLE?

WHY THIS EXISTS (2026-08-18, handoff 2026-08-18c section 6 item 1)
  The basin mock places dormant-basin onsets in GMT space because per-zone
  regional drivers did not exist when it was written. Tier 2a/2b built them
  (t_gis_zones.csv now carries central/north; per-zone CMIP6 amp shapes exist).
  The stated expectation is that re-expressing onsets in zone-driver units maps
  the passing region over MONOTONICALLY. That expectation is a claim about the
  driver splice, and it is cheap to measure BEFORE any wiring is written:

    D_zone(y) = amp_zone * S_zone(dT30(y)) * GMST_rb(y) + (anchor - amp*shape_anchor)

  THE TEST THAT IS ACTUALLY AVAILABLE. A first draft of this script tested two
  things that cannot answer the question, and both are recorded here so the
  mistake is not repeated:
    (a) monotonicity of the driver TIME SERIES -- wrong: SSP1-2.6 peaks and
        declines, so its driver legitimately falls. The claim in section 6.1 is
        about the GMT -> driver MAP, not about t -> driver.
    (b) the SCENARIO SPREAD of the zone-driver value at a given onset -- vacuous
        BY CONSTRUCTION: the mock's falsifier F3 established that no passing
        onset sits below SSP2-4.5's 2300 GMT (3.15 K), so SSP5-8.5 is the only
        scenario that ever crosses one. There is no second scenario to spread
        against, and printing a NaN "instability" would be an artefact.
  What the wiring actually needs, and what this script measures instead:
    M1  is the GMT -> zone-driver map along the SSP5-8.5 path (the only path
        that reaches the onsets) strictly increasing over the onset range? If
        yes, each GMT-space onset has a unique zone-space image and the pass
        region maps over one-for-one.
    M2  does each translated onset still sit ABOVE the 2300 zone-driver value of
        SSP1-2.6 and SSP2-4.5 -- i.e. do the dormant basins stay inert on those
        scenarios, as they are in GMT space? Reported as a MARGIN, per zone.
    M3  what does the fixed 1 K GMT ramp width W become in zone units? The local
        slope dD_zone/dGMT rescales it, so the same structural knob is a
        different physical softness in each zone -- this is the quantitative
        input to the W choice in section 6 item 2.

WHAT IT DOES NOT DECIDE
  Nothing here picks the amp WINDOW, the MID-basin zone, or the ramp width W --
  those are Marcus's calls (handoff section 6 item 2). Both candidate windows
  (full, modern) and all three zones are reported so the choice is made on
  numbers rather than defaults.

READS   data/observations/t_gis_zones.csv, outputs/gis_amp_prior.csv,
        outputs/gis_amp_shape[_<zone>].csv (+ metas),
        data/observations/fair_mean_gmst_<ssp>.csv,
        outputs/scope_gis_basin_mock_vs_literature.csv (the 59 passing onsets)
WRITES  outputs/diag_gis_zone_driver_scope.csv

  source ~/climate-env/bin/activate
  python3 python/diag_gis_zone_driver_scope.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
from scope_gis_2300_relaxation import (  # noqa: E402
    ANCHOR_N, OBS, SHAPE_WIN, SSPS, YEARS, _running_mean, gmst_rebased,
)

# --- named constants; every label and filename below derives from these ------
ZONES = ["south", "central", "north"]          # driver columns in t_gis_zones.csv
AMP_WINDOWS = ["full", "modern"]               # the pending choice, both reported
MOCK_CSV = os.path.join(REPO, "outputs/scope_gis_basin_mock_vs_literature.csv")
OUT = os.path.join(REPO, "outputs/diag_gis_zone_driver_scope.csv")
REPORT_YEARS = (2100, 2200, 2300)
MONO_TOL = 1e-9                # strictness of the M1 map-monotonicity gate
SPLICE_START = 2025            # first year the splice (not obs) supplies D_zone
ONSET_GRID_STEP_K = 1.0        # the mock's GMT onset spacing
RAMP_W_GMT_K = 1.0             # the mock's fixed soft-ramp width, GMT K (M3)
MAP_SSP = "SSP5-8.5"           # the only scenario that reaches the onsets (F3)
MAP_GMT_LO, MAP_GMT_HI = 3.15, 7.81   # SSP2-4.5 and SSP5-8.5 2300 GMT: the bracket


def shape_fun(zone):
    """S_zone(dT) from the per-zone anchored shape table. South keeps the
    canonical unsuffixed path; other zones carry a _<zone> suffix."""
    sfx = "" if zone == "south" else f"_{zone}"
    tbl = pd.read_csv(os.path.join(REPO, f"outputs/gis_amp_shape{sfx}.csv"))
    meta_path = (os.path.join(REPO, "outputs/gis_amp_shape_meta.csv") if zone == "south"
                 else os.path.join(REPO, f"outputs/gis_amp_shape_meta_{zone}.csv"))
    meta = pd.read_csv(meta_path).iloc[0]
    x, y = tbl["dt"].to_numpy(), tbl["S"].to_numpy()
    S = lambda dt: np.interp(np.clip(dt, x[0], x[-1]), x, y)
    assert abs(S(float(meta.anchor_dt)) - 1.0) < 1e-9, f"S(anchor) != 1 for {zone}"
    return S


def amp_mean(zone, window):
    pri = pd.read_csv(os.path.join(REPO, "outputs/gis_amp_prior.csv"))
    r = pri[(pri.zone == zone) & (pri.window == window)]
    assert len(r) == 1, f"amp prior lookup {zone}/{window} -> {len(r)} rows"
    return float(r["mean"].iloc[0])


def zone_driver(gmst_rb, zone, amp, S):
    """The regional_driver of scope_gis_2300_relaxation, parameterised by ZONE
    instead of the module-level GIS_ZONE constant. Same anchor-preserving
    splice, same 30-yr shape window, same 11-yr anchor."""
    tgz = pd.read_csv(os.path.join(OBS, "t_gis_zones.csv"))
    gd = dict(zip(tgz["year"].astype(int), tgz[zone].astype(float)))
    last = int(tgz["year"].max())
    obs = np.array([gd.get(int(y), 0.0) for y in YEARS])
    mask = YEARS <= last
    ianch = np.isin(YEARS, np.arange(last - ANCHOR_N + 1, last + 1))
    anchor = obs[ianch].mean()
    shape = S(_running_mean(gmst_rb, SHAPE_WIN))
    shape_anchor = float((shape[ianch] * gmst_rb[ianch]).mean())
    spliced = amp * shape * gmst_rb + (anchor - amp * shape_anchor)
    return np.where(mask, obs, spliced), anchor


def map_along(gmst_rb, driver, lo, hi):
    """Restrict to the splice era and to GMST in [lo, hi], sorted by GMST: the
    GMT -> zone-driver map along this scenario's path."""
    era = (YEARS >= SPLICE_START) & (gmst_rb >= lo) & (gmst_rb <= hi)
    g, d = gmst_rb[era], driver[era]
    o = np.argsort(g)
    return g[o], d[o]


def driver_at_gmst(gmst_rb, driver, level):
    """Zone-driver value where GMST_rb first reaches `level` in the splice era."""
    idx = np.where((YEARS >= SPLICE_START) & (gmst_rb >= level))[0]
    if idx.size == 0:
        return np.nan, np.nan
    i = idx[0]
    return float(YEARS[i]), float(driver[i])


def main():
    mock = pd.read_csv(MOCK_CSV)
    passers = mock[mock["all_pass"]]
    onsets = sorted(set(passers["t_on_high"]).union(
        {v for v, s in zip(passers["t_on_mid"], passers["mid_share"]) if s > 0}))
    print(f"[onsets] {len(passers)} passing cells -> ACTIVE onset levels "
          f"{onsets} K GMT (inactive mid placeholders excluded)")
    print(f"[frame]  only {MAP_SSP} crosses these (F3); SSP1-2.6/SSP2-4.5 peak "
          f"below {MAP_GMT_LO} K, so the map is measured along {MAP_SSP} and the "
          f"other two enter as INERTNESS MARGINS.\n")

    gm = {}
    for ssp, lab in SSPS:
        _, rb = gmst_rebased(ssp)
        gm[lab] = rb

    rows = []
    for zone in ZONES:
        S = shape_fun(zone)
        for window in AMP_WINDOWS:
            amp = amp_mean(zone, window)
            drv, anchor = {}, None
            for lab, rb in gm.items():
                d, anchor = zone_driver(rb, zone, amp, S)
                drv[lab] = d
                for y in REPORT_YEARS:
                    rows.append(dict(zone=zone, amp_window=window, amp=amp,
                                     anchor_splice=anchor, scenario=lab,
                                     kind="level", onset_K_GMT=np.nan, year=y,
                                     value=float(d[YEARS == y][0])))

            # --- M1: is the GMT -> driver map increasing over the bracket? ----
            g, d = map_along(gm[MAP_SSP], drv[MAP_SSP], MAP_GMT_LO, MAP_GMT_HI)
            dmin = float(np.diff(d).min())
            rows.append(dict(zone=zone, amp_window=window, amp=amp,
                             anchor_splice=anchor, scenario=MAP_SSP,
                             kind="M1_map_min_step", onset_K_GMT=np.nan,
                             year=np.nan, value=dmin))

            # --- M2/M3 per translated onset ----------------------------------
            for lev in onsets:
                yr, v = driver_at_gmst(gm[MAP_SSP], drv[MAP_SSP], lev)
                inert = {lab: float(np.nanmax(drv[lab])) for lab in drv if lab != MAP_SSP}
                margin = v - max(inert.values())
                _, v_hi = driver_at_gmst(gm[MAP_SSP], drv[MAP_SSP], lev + RAMP_W_GMT_K)
                w_zone = v_hi - v
                rows.append(dict(zone=zone, amp_window=window, amp=amp,
                                 anchor_splice=anchor, scenario=MAP_SSP,
                                 kind="onset_translated", onset_K_GMT=lev,
                                 year=yr, value=v))
                rows.append(dict(zone=zone, amp_window=window, amp=amp,
                                 anchor_splice=anchor, scenario="ALL",
                                 kind="M2_inert_margin", onset_K_GMT=lev,
                                 year=np.nan, value=margin))
                rows.append(dict(zone=zone, amp_window=window, amp=amp,
                                 anchor_splice=anchor, scenario=MAP_SSP,
                                 kind="M3_ramp_W_zone", onset_K_GMT=lev,
                                 year=np.nan, value=w_zone))

    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)

    print("=== zone-driver levels (K, each zone's own anomaly frame) ===")
    lv = df[df.kind == "level"]
    print(lv.pivot_table(index=["zone", "amp_window", "scenario"], columns="year",
                         values="value").round(2).to_string())
    print(f"\nsplice anchors (the ANCHOR_N={ANCHOR_N} window the splice actually "
          "uses, i.e. 2014-2024): " + ", ".join(
              f"{z} {df[df.zone == z]['anchor_splice'].iloc[0]:.4f}" for z in ZONES))
    print("  NOTE the handoff's per-zone anchors (south 1.9631, central 2.7667, "
          "north 3.2714) are the 10-yr 2015-2024 means -- the same quantity on a "
          "DIFFERENT window. Both are right; only the ANCHOR_N one enters the "
          "splice. Do not wire the 10-yr number.")

    print(f"\n=== M1: GMT -> zone-driver map along {MAP_SSP}, "
          f"GMST in [{MAP_GMT_LO}, {MAP_GMT_HI}] K ===")
    m1 = df[df.kind == "M1_map_min_step"]
    print(m1.pivot_table(index="zone", columns="amp_window", values="value").to_string())
    ok1 = bool((m1["value"] > MONO_TOL).all())
    print("VERDICT M1:", "PASS - strictly increasing, every zone x window"
          if ok1 else "FAIL - the map turns over; onsets are not 1:1")

    print("\n=== onsets translated into zone-driver units (and crossing year) ===")
    tr = df[df.kind == "onset_translated"]
    print(tr.pivot_table(index=["zone", "amp_window"], columns="onset_K_GMT",
                         values="value").round(2).to_string())
    print("\ncrossing years (identical across zones by construction):")
    print(tr[(tr.zone == "north") & (tr.amp_window == "full")]
          [["onset_K_GMT", "year"]].to_string(index=False))

    print("\n=== M2: inertness margin = translated onset - max(SSP1-2.6, SSP2-4.5) "
          "zone driver, K ===")
    m2 = df[df.kind == "M2_inert_margin"]
    print(m2.pivot_table(index=["zone", "amp_window"], columns="onset_K_GMT",
                         values="value").round(2).to_string())
    ok2 = bool((m2["value"] > 0).all())
    print("VERDICT M2:", f"PASS - all {len(m2)} translated onsets stay inert on "
          "SSP1-2.6/SSP2-4.5 (min margin "
          f"{m2['value'].min():.2f} K)" if ok2 else "FAIL - a basin activates "
          "on a low scenario; ssp126/245 would no longer be bit-identical")

    print(f"\n=== M3: the fixed {RAMP_W_GMT_K:g} K GMT ramp in zone units ===")
    m3 = df[df.kind == "M3_ramp_W_zone"]
    print(m3.pivot_table(index=["zone", "amp_window"], columns="onset_K_GMT",
                         values="value").round(2).to_string())
    print(f"(the {max(onsets):g} K onset has no column: onset + W = "
          f"{max(onsets) + RAMP_W_GMT_K:g} K exceeds {MAP_SSP}'s 2300 GMT of "
          f"{MAP_GMT_HI} K, so its ramp does not complete this century-set)")
    print("i.e. holding W = 1 K in ZONE units would make the ramp "
          f"{m3.groupby('zone')['value'].mean().round(2).to_dict()}x SHARPER "
          "than the GMT-space mock, per zone - a CHOICE, not a translation.")

    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
