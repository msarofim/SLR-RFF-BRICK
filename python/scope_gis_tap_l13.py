#!/usr/bin/env python3
"""
scope_gis_tap_l13.py — price the HIGH-BASIN VOLUME TAP offline, against the
CERTIFIED L13 POSTERIOR, with no further MCMC.

WHY THIS EXISTS (2026-08-20, handoff notes/handoff_2026-08-20_gis_zone_and_tap.md §6.1)
  The tap is LIKELIHOOD-INERT: its admissible onset bracket is (4.69, 7.81] K GMT
  and the calibration forcing tops out at 1.385 K in 2025, 3.31 K below the lowest
  onset. So it can never be informed by the 1900-2025 hindcast and belongs on the
  PROJECTION side, prior-propagated exactly as `gis_amp` already is. That makes
  this scoping the whole pricing exercise — there is no chain to buy.

WHAT IS NEW HERE, vs the mock (scope_gis_basin_mock_vs_literature.py) and the
prototype (scope_gis_3basin_partition.py) that preceded it:

  1. THE RATE SCALES ARE MEASURED, NOT BISECTED. Both predecessors solved s_b
     offline against an exactly-identified target. L13 FITTED them:
     s_mid 0.949 [0.53, 1.60], s_high 0.268 [0.139, 0.506]. The tap sits on top
     of s_high, so this is the first pricing that uses the posterior it will
     actually be propagated through.
  2. THE POSTERIOR IS PROPAGATED, NOT COLLAPSED TO ITS MEDIAN. The predecessors
     ran at median parameters. Ratios of medians are not medians of ratios (the
     same trap that once made the shipped model look like it failed G4), and the
     deliverable IS a ratio, so every headline number here is an ENSEMBLE
     quantile over draws.
  3. THE DRIVER IS L13's, NOT THE DESIGN'S. The 3-basin DESIGN specifies the
     `all` zone; L13 as calibrated still runs GIS_ZONE = "south" (the zone switch
     is gated on an offline A+B refit that has not happened). Scoring L13 on the
     `all` driver would price a model nobody has fitted. This uses south.
  4. THE PER-BASIN COMMITMENT CLAMP IS THE JULIA'S, NOT THE PROTOTYPE'S. The
     prototype clamped each basin to the WHOLE-SHEET v0; greenland_3basin_component.jl
     clamps to k_b*v0, so that eq_b == k_b*eq_whole identically. The two agree
     over the hindcast (the cap never binds there) and DIVERGE at 2300 under
     ssp585 — which is the only regime this script is about.

THE QUESTION, FIXED BEFORE RUNNING
  Q  Over the tap grid (T_on, V_tap, tau), what is the ssp585/ssp245 Greenland
     loss ratio at 2300, and does any cell reach the 7.9-31.9x literature band
     without breaking the three 2300 level bands, the 2100 scenario spread, or
     the Mouginot high-basin inventory?
  FALSIFIER  If no cell clears, the tap as specified cannot buy the separation
     on the L13 posterior and that is the finding — REPORT IT, do not tune the
     grid until something passes.

GATES (all hard; none skippable)
  G1  CROSS-LANGUAGE. This Python 3-basin re-implementation must reproduce
      julia/diag_l13_basin_shares.jl — the fitted rate scales AND both windows'
      sector shares — on the same chain, the same driver, the same medians.
  G2  INERTNESS. Every tap cell's ramp must be EXACTLY zero over the whole
      calibration window on every scenario. This is the check the memory demands
      be verified rather than assumed.
  G3  NESTING. At V = 0 the tapped series must be bit-identical to the base.

RE-PRICING ALONG THE RIDGE (--k=, 2026-08-21f, handoff 2026-08-21c §4 item 5)
  The 25-cell admissible set was scored against a k = 1 base, and every cell is
  void the moment the commitment scale moves — the tap's job is defined RELATIVE
  to what the base already delivers. `--k=1,1.5,3` scales (c1, c0) by each k and
  re-solves the rate by per-draw bisection onto the same 1900-2025 hindcast, then
  re-runs the whole grid at each point, on a 0.25 m V grid. Without --k the file
  behaves exactly as before and reproduces the published 25/140.

  NOTE what this scorecard IS: the 2300-ENDPOINT one (three level bands + the
  ssp585/ssp245 ratio + G4). It is NOT the PROTECT matched-forcing trajectory
  test, which separately found 0/25 cells fitting at 2150 and diagnosed the
  exponential's SHAPE. A cell passing here is not a cell that fits the physics.

READS   data/MimiBRICK/parameters_subsample_brick_mengel_L13.csv (certified posterior)
        outputs/mcmc/chain_L13_seed2026_n2000000.csv (G1 only)
        the ridge harness (drivers, literature bands), the Mouginot parse
WRITES  outputs/scope_gis_tap_l13.csv

  source ~/climate-env/bin/activate
  python3 python/scope_gis_tap_l13.py
  python3 python/scope_gis_tap_l13.py --tag=L14 --k=1,1.25,1.5,2,3
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
import scope_gis_leq_ridge_vs_literature as ridge  # noqa: E402
import diag_gis_basin_lit_check as lit  # noqa: E402
from scope_gis_2300_relaxation import (  # noqa: E402
    GIS_G, GIS_V0_M, GIS_ZONE, IREF, OBS, REF, SSPS, YEARS,
    gis_shape_table, gmst_rebased, regional_driver, thin,
)

# --- provenance, and every label below derives from it ----------------------
# --tag= REPRICES ON ANOTHER VINTAGE (Marcus 2026-08-21). The 25-cell admissible
# set was priced on L13, but L14 is canonical and differs in exactly the two
# places the tap rides on: it is TWO-basin (no gis_s_mid at all) and its
# s_high is 0.2265, not L13's 0.268. Shipping an L13-priced band on an
# L14 deliverable would be quoting an admissible set nobody re-scored.
#
# THE FILENAME IS HISTORICAL. This module is still scope_gis_tap_l13.py because
# notes and memory reference it by that name; the TAG is the authority, and the
# banner says so whenever they disagree. OUT is tag-derived, so an L14 run writes
# scope_gis_tap_l14.csv and CANNOT overwrite the L13 artefact that the 25-cell
# result rests on.
LADRILLO_TAG = next((a.split("=", 1)[1] for a in sys.argv[1:]
                     if a.startswith("--tag=")), "L13")
POST = os.path.join(REPO,
                    f"data/MimiBRICK/parameters_subsample_brick_mengel_{LADRILLO_TAG}.csv")
# G1_SEEDS mirrors HOW EACH REFERENCE WAS PRODUCED, and the two vintages differ:
# the L13 julia log is headed "chain_L13_seed2026_n2000000.csv" (ONE chain) while
# the L14 log is headed "L14, 4 chain(s) POOLED". Comparing a pooled reference
# against a single-chain python median is not a cross-language test, it is a
# pooling test -- it fails at 3.8e-03 on s_high purely from that, which looks
# exactly like a port bug. Set alongside G1_REF so the two cannot drift apart.
G1_SEEDS = {"L13": (2026,), "L14": (2026, 2027, 2028, 2029)}
GATE_CHAINS = [os.path.join(REPO, f"outputs/mcmc/chain_{LADRILLO_TAG}_seed{sd}_n2000000.csv")
               for sd in G1_SEEDS.get(LADRILLO_TAG, (2026,))]
GATE_CHAIN = GATE_CHAINS[0]     # for messages that name a single file
# --k=1,1.25,... RE-PRICES THE TAP ON A MOVED BASE (handoff 2026-08-21c §4 item 5).
# The 25-cell admissible set was scored against a k = 1 base; every cell in it is
# void the moment the commitment scale moves, because the tap's job is defined
# RELATIVE to what the base already delivers. Given, each k scales (c1, c0) and
# re-solves the rate by per-draw bisection so the 1900-2025 hindcast still holds --
# i.e. it moves ALONG the phi*Leq ridge, exactly as the ridge scans do.
# NOT given, this file behaves EXACTLY as before: no bisection, s_r = 1, and the
# 140-cell result the shipped cell rests on reproduces unchanged.
K_SCAN = [float(x) for a in sys.argv[1:] if a.startswith("--k=")
          for x in a.split("=", 1)[1].split(",")]
## TARGET SET (2026-08-21g). Default MATCHED: LIT's ssp585 2300 band is the PROTECT
## x2300 family at 13.8 K against our ssp585's 7.8 K, so both the LEVEL bands and
## the ssp585/ssp245 RATIO band derived from it score a hotter world than ours. The
## set is in the FILENAME as well as the printout -- a matched-set scan must not
## overwrite the artefact the published 25/140 rests on.
import gis_targets  # noqa: E402
_TARGET_BANDS, TARGET_SET = gis_targets.from_argv(sys.argv)
TARGET_WORD = gis_targets.SET_WORD[TARGET_SET]
OUT = os.path.join(REPO, f"outputs/scope_gis_tap_{LADRILLO_TAG.lower()}"
                   + ("_kscan" if K_SCAN else "")
                   + gis_targets.SET_SUFFIX[TARGET_SET] + ".csv")

# --- the 3-basin geometry, mirroring julia/greenland_3basin_component.jl -----
BASINS = ("south", "mid", "high")
SECTORS = {"south": ("SW", "CW", "CE", "SE"), "mid": lit.MID_SECTORS,
           "high": lit.HIGH_SECTORS}
GIS3_VOL_M = {b: sum(lit.MOUGINOT_SLE_CM[s] for s in SECTORS[b]) / 100.0
              for b in BASINS}
_V3 = {b: GIS3_VOL_M[b] / sum(GIS3_VOL_M.values()) for b in BASINS}
# TWO-BASIN detection is from the POSTERIOR ITSELF, not a flag: a two-basin
# vintage simply has no gis_s_mid column, so there is nothing to guess and no way
# for the mode and the file to disagree. Shares then mirror julia/
# greenland_3basin_component.jl GIS2_VSHARE exactly -- NW merges into the active
# basin, high untouched, k_mid = 0. A zero share contributes a zero series to
# every sum, which is why the component calls k_mid = 0 "a genuine two-basin
# model BY CONSTRUCTION rather than by test".
def _post_cols(path):
    with open(path) as fh:
        return fh.readline().rstrip("\n").split(",")


TWO_BASIN = os.path.exists(POST) and "gis_s_mid" not in _post_cols(POST)
GIS3_VSHARE = ({"south": _V3["south"] + _V3["mid"], "mid": 0.0,
                "high": _V3["high"]} if TWO_BASIN else _V3)
PINNED_BASIN = "south"          # its rate scale is s = 1 by construction
TAPPED = "high"                 # NO+NE; mid gets no tap (Aschwanden: deceleration)

# --- the tap, as the mock defines it ----------------------------------------
# S_t = first-order relaxation toward a soft GMT ramp of width TAP_RAMP_W_K;
# the tap adds V*S_t of extra loss to the tapped basin. Onsets are in GMT space
# (K rel 1850-1900), the space the Tier-1 literature bracket is quoted in.
TAP_ONSET_K = [4.0, 4.69, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 7.81]
TAP_V_M = [0.5, 1.0, 1.5, 2.0, 2.5]
TAP_TAU = [50, 100, 200, 400]
TAP_RAMP_W_K = 1.0
# The default V grid is 0.5 m coarse, which was enough to answer "does any cell
# clear". It is NOT enough to answer "how much smaller does the tap get", so the
# k-scan uses a 0.25 m grid. Kept separate so the default path's cell count -- and
# therefore the published 25/140 -- cannot move.
TAP_V_M_KSCAN = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5]
# Tier-1 admissible onset bracket: above ssp585's 2100 GMT (nothing may fire in
# the accepted 2100 deliverable) and at or below its 2300 GMT (it must fire).
ONSET_LO_K, ONSET_HI_K = lit.GMT2100_585_EXPECT, lit.GMT2300_585_EXPECT
V_TAP_MAX_M = lit.V_HIGH_MAX    # 2.73 m = the NO+NE Mouginot inventory

# --- the scorecard ----------------------------------------------------------
LIT_2300_M = _TARGET_BANDS
RATIO_LO, RATIO_HI = gis_targets.ratio_band(LIT_2300_M)
G4_DEGRADE_TOL = ridge.G4_DEGRADE_TOL
G4_PAIR = ("SSP5-8.5", "SSP1-2.6")      # the 2100 spread A+B was selected on
CALIB_WIN = ridge.HIND                  # (1900, 2025) — the inertness window
HORIZONS = (2100, 2300)
QLO, QHI = 0.05, 0.95

# --- G1 reference: julia/diag_l13_basin_shares.jl on GATE_CHAIN -------------
G1_WINS = ((2002, 2011), (2012, 2018))
# KEYED BY VINTAGE, not hardcoded to one. These are transcriptions of the JULIA
# diagnostic's own output on that vintage's chain -- L13 from
# julia/diag_l13_basin_shares.jl, L14 from outputs/mcmc/log_L14_basinshares.txt
# (the same tool, which detects the 2-basin structure from the chain columns).
# A single hardcoded set is the stale-fixture bug this file already carries once
# elsewhere: run --tag=L14 against L13's numbers and G1 fails on a REAL
# difference (L14's s_high is 0.2265, L13's 0.2644) while looking like a code
# fault. DO NOT WIDEN G1_TOL_* to make a new vintage pass -- add its row here,
# transcribed from the julia log, or the cross-language gate stops meaning
# anything.
G1_REF = {
    "L13": dict(
        scales={"mid": 0.9375, "high": 0.2644},
        shares=({"south": 0.583, "mid": 0.213, "high": 0.204},
                {"south": 0.558, "mid": 0.207, "high": 0.234})),
    # two-basin: `mid` is not sampled and k_mid = 0, so it is NOT SCORED.
    "L14": dict(
        scales={"high": 0.2265},
        shares=({"south": 0.818, "mid": 0.000, "high": 0.182},
                {"south": 0.788, "mid": 0.000, "high": 0.212})),
}
if LADRILLO_TAG not in G1_REF:
    raise SystemExit(
        f"G1 has no reference for tag {LADRILLO_TAG!r}. Add one to G1_REF, "
        f"transcribed from the julia basin-shares diagnostic run on that "
        f"vintage's chain. Do NOT relax G1_TOL_* instead.")
G1_SCALES = G1_REF[LADRILLO_TAG]["scales"]
G1_SHARES = G1_REF[LADRILLO_TAG]["shares"]
G1_TOL_SCALE, G1_TOL_SHARE = 5e-4, 1e-3
G1_TBAR = 1.9631                # the calibrator's printed anchor for this zone

IY = {y: int(np.where(YEARS == y)[0][0]) for y in HORIZONS}


# ---------------------------------------------------------------------------
# the model
# ---------------------------------------------------------------------------
def basin_scales(p):
    """The per-basin rate scales a posterior carries: south PINNED at 1, the
    other two as LOG10 scales, matching the calibrator's 10.0^theta."""
    n = len(p)
    return {"south": np.ones(n),
            # a two-basin posterior has no gis_s_mid; k_mid is 0 there, so the
            # value is arithmetically irrelevant and 1.0 keeps the rate finite.
            "mid": (np.ones(n) if TWO_BASIN
                    else 10.0 ** p["gis_s_mid"].to_numpy()),
            "high": 10.0 ** p["gis_s_high"].to_numpy()}


def run_3basin(T, p, k_c=1.0, s_r=1.0):
    """julia/greenland_3basin_component.jl, vectorised over draws.
    T is (ndraw, nyear) REGIONAL driver; returns {basin: loss (ndraw, nyear)}.

    The commitment clamp is PER BASIN, [0, k_b*v0] — identically k_b times the
    whole-sheet clamped commitment — NOT the prototype's whole-sheet clamp.

    k_c scales the COMMITMENT and s_r scales BOTH channel rates, per draw. The
    V0 clamp does NOT scale with k_c: V0 is the physical ice inventory, so a
    larger commitment saturates against the SAME ceiling — which is the whole
    reason the ridge is non-monotone in k. At (1.0, 1.0) every operation below
    is arithmetically identical to the un-scaled original."""
    c1 = p["gis_c1"].to_numpy()[:, None]
    c0 = p["gis_c0"].to_numpy()[:, None]
    f = p["gis_f"].to_numpy()
    af, bf = p["gis_alpha_f"].to_numpy(), p["gis_beta_f"].to_numpy()
    a_s, bs = p["gis_alpha_s"].to_numpy(), p["gis_beta_s"].to_numpy()
    s = basin_scales(p)
    s_r = np.atleast_1d(np.asarray(s_r, float))
    eq_w = np.clip(k_c * (c1 * T + c0), 0.0, GIS_V0_M)  # whole-sheet, m SLE
    n, ny = T.shape
    out = {}
    for b in BASINS:
        k = GIS3_VSHARE[b]
        eq = k * eq_w
        fast, slow = np.empty((n, ny)), np.empty((n, ny))
        fast[:, 0] = GIS_G * f * eq[:, 0]
        slow[:, 0] = GIS_G * (1.0 - f) * eq[:, 0]
        for i in range(1, ny):
            Tm = T[:, i - 1]
            rf = np.clip(s[b] * s_r * (af * Tm + bf), 1e-9, 1.0)
            rs = np.clip(s[b] * s_r * (a_s * Tm + bs), 1e-9, 1.0)
            fast[:, i] = fast[:, i - 1] + (f * eq[:, i - 1] - fast[:, i - 1]) * rf
            slow[:, i] = slow[:, i - 1] + ((1.0 - f) * eq[:, i - 1] - slow[:, i - 1]) * rs
        out[b] = fast + slow
    return out


def tap_unit(gmt, t_on, tau):
    """Unit tap: first-order relaxation toward a soft ramp in GMT. Deterministic
    given the scenario — it carries no posterior dependence, which is exactly
    why the tap is prior-propagated rather than sampled."""
    seq = np.clip((gmt - t_on) / TAP_RAMP_W_K, 0.0, 1.0)
    S = np.zeros_like(gmt)
    r = 1.0 / tau
    for i in range(1, len(gmt)):
        S[i] = S[i - 1] + (seq[i - 1] - S[i - 1]) * r
    return S


def q(v):
    return (float(np.median(v)), float(np.quantile(v, QLO)), float(np.quantile(v, QHI)))


# ---------------------------------------------------------------------------
# G1 — the cross-language gate
# ---------------------------------------------------------------------------
def gate_crosslanguage(rows):
    """Reproduce julia/diag_l13_basin_shares.jl in this Python. Same chain, same
    post-burn half, same medians, same OBSERVED driver (every year of both
    windows predates the amp splice, so no forcing file enters)."""
    cols = ["gis_c1", "gis_c0", "gis_f", "gis_alpha_f", "gis_beta_f",
            "gis_slow_ell", "gis_slow_w", "gis_s_high"]
    if not TWO_BASIN:
        cols.append("gis_s_mid")
    for gc in GATE_CHAINS:
        if not os.path.exists(gc):
            raise SystemExit(f"G1: {os.path.relpath(gc, REPO)} not found")
    # post-burn half of EACH chain, then concatenate -- pooling the halves, not
    # halving the pool. For a single-seed vintage this is the previous behaviour
    # exactly.
    h = pd.concat([pd.read_csv(gc, usecols=cols).iloc[lambda d: slice(len(d) // 2, None)]
                   for gc in GATE_CHAINS], ignore_index=True)
    pa = h.median(numeric_only=True)

    tbar = ridge.gis_tbar()
    if abs(tbar - G1_TBAR) > 1e-4:
        raise SystemExit(f"G1: TBAR {tbar:.4f} != the calibrator's {G1_TBAR}")
    pa = ridge.native_greenland(pa, tbar)
    p = pd.DataFrame([pa])

    tgz = pd.read_csv(os.path.join(OBS, "t_gis_zones.csv"))
    yrs = np.arange(1850, int(tgz["year"].max()) + 1)
    gd = dict(zip(tgz["year"].astype(int), tgz[GIS_ZONE].astype(float)))
    missing = [int(y) for y in yrs if int(y) not in gd]
    if missing:
        raise SystemExit(f"G1: t_gis_zones.csv missing {len(missing)} years from 1850")
    T = np.array([[gd[int(y)] for y in yrs]])
    bsl = run_3basin(T, p)

    s = basin_scales(p)
    print(f"\n=== G1 — cross-language reproduction of diag_l13_basin_shares.jl "
          f"on {len(GATE_CHAINS)} chain(s), seeds "
          f"{', '.join(str(x) for x in G1_SEEDS.get(LADRILLO_TAG, (2026,)))} ===\n")
    print(f"  {'rate scale':<14s} {'python':>10s} {'julia':>10s} {'|diff|':>10s}")
    worst = 0.0
    for b in ("mid", "high"):
        if b not in G1_SCALES:      # e.g. `mid` on a two-basin vintage
            continue
        d = abs(float(s[b][0]) - G1_SCALES[b])
        worst = max(worst, d / G1_TOL_SCALE)
        print(f"  {b:<14s} {float(s[b][0]):10.4f} {G1_SCALES[b]:10.4f} {d:10.2e}")
        rows.append(dict(quantity="g1_scale", basin=b, python=float(s[b][0]),
                         julia=G1_SCALES[b], absdiff=d, tol=G1_TOL_SCALE))
        if d > G1_TOL_SCALE:
            raise SystemExit(f"G1 FAILED: {b} rate scale differs by {d:.2e} "
                             f"(tol {G1_TOL_SCALE})")
    for w, want in zip(G1_WINS, G1_SHARES):
        i0 = int(np.where(yrs == w[0])[0][0])
        i1 = int(np.where(yrs == w[1])[0][0])
        d_b = {b: (bsl[b][0, i1] - bsl[b][0, i0]) / (w[1] - w[0]) for b in BASINS}
        tot = sum(d_b.values())
        line = []
        for b in BASINS:
            sh = d_b[b] / tot
            d = abs(sh - want[b])
            worst = max(worst, d / G1_TOL_SHARE)
            line.append(f"{b} {sh:.3f} (julia {want[b]:.3f})")
            rows.append(dict(quantity="g1_share", basin=b, window=f"{w[0]}-{w[1]}",
                             python=sh, julia=want[b], absdiff=d, tol=G1_TOL_SHARE))
            if d > G1_TOL_SHARE:
                raise SystemExit(f"G1 FAILED: {w} {b} share {sh:.4f} vs julia "
                                 f"{want[b]:.4f} (tol {G1_TOL_SHARE})")
        print(f"  {w[0]}-{w[1]}: " + "  ".join(line))
    print(f"\n  G1 PASS — worst deviation {worst:.2f} of its tolerance.")
    return worst


# ---------------------------------------------------------------------------
def price_at(k_c, s_r, post, drivers, gmt, rows, v_grid):
    """Base + the full tap grid at ONE ridge point. k_c scales the commitment and
    s_r the rates; (1.0, 1.0) is the certified model and reproduces the original
    pricing exactly. Every row appended carries k_c, so one CSV holds the whole
    scan and no k can be confused for another."""
    ktag = "" if k_c == 1.0 and np.isscalar(s_r) and s_r == 1.0 else f", k = {k_c:g}"
    # ---- base: L13 with no tap -------------------------------------------
    base, base_high_head = {}, {}
    print(f"\n=== BASE — {LADRILLO_TAG}{ktag}, NO tap "
          f"(m SLE rel {REF[0]}-{REF[1]}) ===\n")
    print(f"  {'scenario':10s} {'2100 cm':>18s} {'2300 m':>22s}   "
          f"{'2300 lit band':>16s}")
    for _, lab in SSPS:
        bsl = run_3basin(drivers[lab], post, k_c, s_r)
        tot = sum(bsl.values())
        ref = tot[:, IREF].mean(axis=1, keepdims=True)
        base[lab] = {y: (tot[:, IY[y]] - ref[:, 0]) for y in HORIZONS}
        # the tapped basin's remaining ice at 2300: its capacity less its own loss
        cap = GIS3_VSHARE[TAPPED] * GIS_V0_M
        base_high_head[lab] = np.clip(cap - bsl[TAPPED][:, IY[2300]], 0.0, None)
        m21, l21, h21 = q(100.0 * base[lab][2100])
        m23, l23, h23 = q(base[lab][2300])
        lo, hi = LIT_2300_M[lab]
        print(f"  {lab:10s} {m21:7.2f} [{l21:6.2f},{h21:6.2f}] "
              f"{m23:7.3f} [{l23:6.3f},{h23:6.3f}]   {lo:.3f}-{hi:.3f} "
              f"{'IN' if lo <= m23 <= hi else 'out'}")
        rows.append(dict(quantity="base", k_c=k_c, ssp=lab, cm2100_med=m21, cm2100_q05=l21,
                         cm2100_q95=h21, m2300_med=m23, m2300_q05=l23,
                         m2300_q95=h23, lit_lo=lo, lit_hi=hi,
                         in_band=bool(lo <= m23 <= hi)))
    base_ratio = base["SSP5-8.5"][2300] / base["SSP2-4.5"][2300]
    br, brl, brh = q(base_ratio)
    base_g4 = 100.0 * (base[G4_PAIR[0]][2100] - base[G4_PAIR[1]][2100])
    g4m, g4l, g4h = q(base_g4)
    verdict = ("IN" if RATIO_LO <= br <= RATIO_HI else
               f"SHORT by {RATIO_LO / br:.1f}x" if br < RATIO_LO else
               f"OVER by {br / RATIO_HI:.1f}x")
    print(f"\n  ssp585/ssp245 @2300 ratio   {br:6.2f}x [{brl:.2f}, {brh:.2f}]"
          f"   {TARGET_WORD} {RATIO_LO:.1f}-{RATIO_HI:.1f}x   {verdict}")
    print(f"  G4 = {G4_PAIR[0]} - {G4_PAIR[1]} @2100  {g4m:6.2f} cm "
          f"[{g4l:.2f}, {g4h:.2f}]  (the reference the tap must not degrade)")
    print(f"  {TAPPED}-basin ice remaining at 2300, ssp585: "
          f"{np.median(base_high_head['SSP5-8.5']):.2f} m "
          f"[{np.quantile(base_high_head['SSP5-8.5'], QLO):.2f}, "
          f"{np.quantile(base_high_head['SSP5-8.5'], QHI):.2f}]  "
          f"(capacity {GIS3_VSHARE[TAPPED] * GIS_V0_M:.2f} m; Mouginot inventory "
          f"{V_TAP_MAX_M:.2f} m)")
    rows.append(dict(quantity="base_ratio", k_c=k_c, ratio_med=br, ratio_q05=brl,
                     ratio_q95=brh, lit_lo=RATIO_LO, lit_hi=RATIO_HI,
                     g4_cm_med=g4m))

    # ---- G3 + the grid ----------------------------------------------------
    print(f"\n=== TAP GRID{ktag} — {len(TAP_ONSET_K)}x{len(v_grid)}x{len(TAP_TAU)} = "
          f"{len(TAP_ONSET_K) * len(v_grid) * len(TAP_TAU)} cells, ensemble-propagated "
          f"over {len(post)} draws ===\n")
    # G3 — NESTING. A zero tap must reproduce the base bit-identically, on every
    # scenario and at every onset/tau. This is the same gate that caught the
    # :basins mis-projection: a wiring bug that looks like physics.
    for _, lab in SSPS:
        for t_on in (min(TAP_ONSET_K), max(TAP_ONSET_K)):
            for tau in (min(TAP_TAU), max(TAP_TAU)):
                z = base[lab][2300] + np.minimum(0.0, base_high_head[lab]) \
                    * tap_unit(gmt[lab], t_on, tau)[IY[2300]]
                if not np.array_equal(z, base[lab][2300]):
                    raise SystemExit(f"G3 FAILED: V=0 moves {lab} at "
                                     f"(onset {t_on}, tau {tau})")
    rows.append(dict(quantity="g3_nesting", k_c=k_c, python=0.0, tol=0.0))
    print(f"  G3 PASS — a zero tap reproduces the base bit-identically on every "
          f"scenario, at both ends of the onset and tau grids.")

    npass, nbracket = 0, 0
    for t_on in TAP_ONSET_K:
        for V in v_grid:
            for tau in TAP_TAU:
                r = dict(quantity="tap_cell", k_c=k_c, basin=TAPPED, tap_onset_K=t_on,
                         tap_V_m=V, tap_tau=tau,
                         in_lit_bracket=bool(ONSET_LO_K < t_on <= ONSET_HI_K),
                         within_inventory=bool(V <= V_TAP_MAX_M))
                y23, y21 = {}, {}
                bind = 0.0
                for _, lab in SSPS:
                    u = tap_unit(gmt[lab], t_on, tau)
                    # a basin cannot lose more ice than it has left
                    Veff = np.minimum(V, base_high_head[lab])
                    bind = max(bind, float((Veff < V - 1e-12).mean()))
                    y23[lab] = base[lab][2300] + Veff * u[IY[2300]]
                    y21[lab] = base[lab][2100] + Veff * u[IY[2100]]
                    r[f"m2300_{lab}_med"] = float(np.median(y23[lab]))
                    r[f"tap2100_{lab}_m"] = float(np.median(Veff * u[IY[2100]]))
                ratio = y23["SSP5-8.5"] / y23["SSP2-4.5"]
                r["ratio_med"], r["ratio_q05"], r["ratio_q95"] = q(ratio)
                g4 = 100.0 * (y21[G4_PAIR[0]] - y21[G4_PAIR[1]])
                r["g4_cm_med"] = float(np.median(g4))
                r["g4_rel_to_base"] = r["g4_cm_med"] / g4m
                r["headroom_bind_frac"] = bind
                r["bands_ok"] = bool(all(
                    LIT_2300_M[l][0] <= r[f"m2300_{l}_med"] <= LIT_2300_M[l][1]
                    for _, l in SSPS))
                r["ratio_ok"] = bool(RATIO_LO <= r["ratio_med"] <= RATIO_HI)
                r["g4_ok"] = bool(abs(r["g4_rel_to_base"] - 1.0) <= G4_DEGRADE_TOL)
                r["all_pass"] = bool(r["bands_ok"] and r["ratio_ok"] and r["g4_ok"]
                                     and r["within_inventory"] and r["in_lit_bracket"])
                npass += int(r["all_pass"])
                nbracket += int(r["in_lit_bracket"] and r["within_inventory"])
                rows.append(r)

    cells = pd.DataFrame([r for r in rows if r["quantity"] == "tap_cell"
                          and r["k_c"] == k_c])
    adm = cells[cells["in_lit_bracket"] & cells["within_inventory"]]
    print(f"\n  admissible cells (onset in ({ONSET_LO_K}, {ONSET_HI_K}] K, "
          f"V <= {V_TAP_MAX_M:.2f} m): {nbracket}/{len(cells)}")
    print(f"  ratio over the admissible cells: {adm['ratio_med'].min():.2f}x - "
          f"{adm['ratio_med'].max():.2f}x   ({TARGET_WORD} {RATIO_LO:.1f}-{RATIO_HI:.1f}x)")
    for nm, col in (("2300 level bands", "bands_ok"), ("ratio band", "ratio_ok"),
                    ("2100 spread kept", "g4_ok")):
        print(f"    clearing {nm:20s} {int(adm[col].sum()):3d}/{len(adm)}")
    print(f"  cells clearing EVERYTHING: {npass}/{nbracket}")
    print(f"  VERDICT: {'PASS' if npass else 'NO admissible cell clears — REPORT, do not tune'}")
    if npass:
        w = adm[adm["all_pass"]].sort_values("ratio_med")
        print(f"\n  passing cells (onset K / V m / tau yr -> ratio, ssp585 2300 m):")
        for _, x in w.iterrows():
            print(f"    {x.tap_onset_K:5.2f} {x.tap_V_m:5.2f} {int(x.tap_tau):4d}"
                  f"  ->  {x.ratio_med:6.2f}x [{x.ratio_q05:.2f}, {x.ratio_q95:.2f}]"
                  f"   {x['m2300_SSP5-8.5_med']:.3f} m   G4 {x.g4_rel_to_base:.4f}x")

    return dict(k_c=k_c, rate_scale=float(np.median(np.atleast_1d(s_r))),
                base_ratio=br, base_g4_cm=g4m,
                base_m2300_585=float(np.median(base["SSP5-8.5"][2300])),
                n_cells=len(cells), n_admissible=nbracket, n_pass=npass,
                ratio_lo=float(adm["ratio_med"].min()),
                ratio_hi=float(adm["ratio_med"].max()),
                v_pass_lo=(float(adm[adm.all_pass].tap_V_m.min()) if npass else float("nan")),
                v_pass_hi=(float(adm[adm.all_pass].tap_V_m.max()) if npass else float("nan")),
                head_med=float(np.median(base_high_head["SSP5-8.5"])))


def main():
    rows = []
    if not os.path.exists(POST):
        raise SystemExit(
            f"{os.path.relpath(POST, REPO)} not found. The certified {LADRILLO_TAG} "
            f"posterior subsample is written by\n  julia --project=julia_v2 "
            f"julia/postprocess_mcmc_ext.jl --tag={LADRILLO_TAG} --accept-slr")
    print(f"scope_gis_tap — pricing the {TAPPED}-basin volume tap on the "
          f"certified {LADRILLO_TAG} posterior "
          f"({'TWO' if TWO_BASIN else 'THREE'}-basin)")
    if LADRILLO_TAG != "L13":
        print(f"  NOTE the module is still named scope_gis_tap_l13.py (notes and "
              f"memory reference it\n       by that name); the TAG above is the "
              f"authority and OUT is derived from it.")
    print(f"  posterior  {os.path.relpath(POST, REPO)}")
    print(f"  driver     GIS_ZONE = {GIS_ZONE!r} (L13 as CALIBRATED; the 3-basin "
          f"DESIGN's `all` zone is still gated)")
    print(f"  basins     " + "  ".join(
        f"{b} k={GIS3_VSHARE[b]:.4f} ({GIS3_VOL_M[b]:.2f} m)" for b in BASINS))
    print("  " + gis_targets.banner(TARGET_SET).replace("\n", "\n  "))
    print(f"  implied ssp585/ssp245 RATIO band {RATIO_LO:.2f}-{RATIO_HI:.2f}x "
          f"(this is a DERIVED quantity -- it inherits the set's forcing basis)")

    gate_crosslanguage(rows)

    # ---- drivers ----------------------------------------------------------
    post = thin(POST)
    tbar = ridge.gis_tbar()
    # ridge.native_greenland maps ONE draw (a Series); the same transform, applied
    # per draw. L11+ carries the slow channel ONLY as (ell, w), so this is required.
    if "gis_alpha_s" not in post.columns:
        r_s = np.exp(post["gis_slow_ell"].to_numpy())
        w_s = post["gis_slow_w"].to_numpy()
        post["gis_alpha_s"] = w_s * r_s / tbar
        post["gis_beta_s"] = (1.0 - w_s) * r_s
    S = gis_shape_table()
    amp = post["gis_amp"].to_numpy()
    drivers, gmt = {}, {}
    for ssp, lab in SSPS:
        g_raw, g_rb = gmst_rebased(ssp)
        drivers[lab] = regional_driver(g_rb, amp, S)
        gmt[lab] = g_rb
    print(f"\n  {len(post)} draws; gis_amp {np.median(amp):.4f} "
          f"[{np.quantile(amp, QLO):.4f}, {np.quantile(amp, QHI):.4f}] "
          f"(PRIOR-propagated: likelihood-inert past the splice)")

    # ---- G2: the tap is inert over the calibration window -----------------
    icw = (YEARS >= CALIB_WIN[0]) & (YEARS <= CALIB_WIN[1])
    print(f"\n=== G2 — tap inertness over the calibration window "
          f"{CALIB_WIN[0]}-{CALIB_WIN[1]} ===\n")
    for _, lab in SSPS:
        print(f"  {lab:9s} GMT {gmt[lab][icw].min():+.3f} -> "
              f"{gmt[lab][icw].max():+.3f} K   headroom below the lowest onset "
              f"{min(TAP_ONSET_K) - gmt[lab][icw].max():.3f} K")
    worst_u = 0.0
    for lab in [l for _, l in SSPS]:
        for t_on in TAP_ONSET_K:
            for tau in TAP_TAU:
                worst_u = max(worst_u, float(np.abs(tap_unit(gmt[lab], t_on, tau)[icw]).max()))
    rows.append(dict(quantity="g2_inertness", python=worst_u, tol=0.0))
    if worst_u != 0.0:
        raise SystemExit(f"G2 FAILED: max |tap| over {CALIB_WIN} is {worst_u:.3e}, "
                         f"not exactly zero — the tap is NOT likelihood-inert")
    print(f"\n  max |tap ramp| over {CALIB_WIN[0]}-{CALIB_WIN[1]}, over all "
          f"{len(SSPS) * len(TAP_ONSET_K) * len(TAP_TAU)} (scenario, onset, tau) "
          f"combinations: {worst_u:.1e}")
    print(f"  G2 PASS — EXACTLY zero. The tap cannot have been informed by the "
          f"hindcast, as claimed.")

    # ---- G2b: WHEN does it fire? ------------------------------------------
    # "Inert over the calibration window" is necessary but not sufficient. The
    # memory (gis_tap_likelihood_inert) asks that tap-on and tap-off diverge ONLY
    # after the onset year, and the deliverable claim is stronger still: an
    # admissible onset must not move the ACCEPTED 2100 numbers on any scenario,
    # and must never fire at all on the cooler two. Both are asserted, not assumed.
    print(f"\n=== G2b — first year the tap is non-zero, by scenario and onset ===\n")
    print(f"  {'onset K':>8s} " + "".join(f"{l:>12s}" for _, l in SSPS))
    for t_on in TAP_ONSET_K:
        adm = ONSET_LO_K < t_on <= ONSET_HI_K
        cells = []
        for _, lab in SSPS:
            u = tap_unit(gmt[lab], t_on, max(TAP_TAU))   # slowest tau fires latest
            nz = np.nonzero(u != 0.0)[0]
            y = int(YEARS[nz[0]]) if len(nz) else None
            cells.append("never" if y is None else str(y))
            rows.append(dict(quantity="g2b_first_fire", ssp=lab, tap_onset_K=t_on,
                             in_lit_bracket=bool(adm),
                             first_fire_year=(-1 if y is None else y)))
            if adm and y is not None and y <= 2100:
                raise SystemExit(
                    f"G2b FAILED: an ADMISSIBLE onset ({t_on} K) fires on {lab} in "
                    f"{y} <= 2100 — it would move the accepted 2100 deliverable")
        print(f"  {t_on:8.2f} " + "".join(f"{c:>12s}" for c in cells)
              + ("" if adm else "   (outside the Tier-1 bracket)"))
    cool = [r for r in rows if r.get("quantity") == "g2b_first_fire"
            and r["in_lit_bracket"] and r["ssp"] != "SSP5-8.5"
            and r["first_fire_year"] != -1]
    if cool:
        raise SystemExit(f"G2b FAILED: {len(cool)} admissible (onset, cool scenario) "
                         f"pairs fire at all; the tap must act ONLY on ssp585")
    print(f"\n  G2b PASS — inside the Tier-1 bracket the tap fires on SSP5-8.5 ONLY, "
          f"and never before 2100.")
    print(f"  So ssp126/ssp245 are untouched by construction, and the accepted 2100 "
          f"deliverable cannot move: the tap acts only on the defective column.")

    # ---- price, at k = 1 or along the ridge -------------------------------
    if not K_SCAN:
        price_at(1.0, 1.0, post, drivers, gmt, rows, TAP_V_M)
    else:
        ## MOVING THE BASE ALONG THE RIDGE. The hindcast pins only the product
        ## phi*Leq, so each k re-solves the rate by PER-DRAW bisection to the same
        ## 1900-2025 increment -- the same construction the ridge scans use, so the
        ## k axis here is the same k axis there. History is the OBSERVED driver, so
        ## the bisection is run on 1850-{CAL} only: the model is causal and the
        ## window is all that constrains it, which makes the solve ~2.5x cheaper.
        tgt = pd.read_csv(os.path.join(REPO, "outputs/recalib_targets_ext.csv")
                          ).set_index("year")["gis"]
        want_cm = float(tgt.loc[CALIB_WIN[1]] - tgt.loc[CALIB_WIN[0]])
        ih = {y: int(np.where(YEARS == y)[0][0]) for y in CALIB_WIN}
        Th = drivers["SSP2-4.5"][:, :ih[CALIB_WIN[1]] + 1]

        def solve_rate(k):
            lo = np.full(len(post), 1e-4)
            hi = np.full(len(post), 1e3)
            for _ in range(80):
                mid = np.sqrt(lo * hi)
                tot = sum(run_3basin(Th, post, k, mid).values())
                below = 100.0 * (tot[:, ih[CALIB_WIN[1]]]
                                 - tot[:, ih[CALIB_WIN[0]]]) < want_cm
                lo = np.where(below, mid, lo)
                hi = np.where(below, hi, mid)
            return np.sqrt(lo * hi)

        print(f"\n=== RE-PRICING ALONG THE RIDGE — k = "
              f"{', '.join(f'{k:g}' for k in K_SCAN)} ===\n")
        print(f"  handoff 2026-08-21c §4 item 5: the 25-cell admissible set was "
              f"scored against a k = 1 base,\n  and every cell in it is void the "
              f"moment k moves. V grid refined to "
              f"{TAP_V_M_KSCAN[1] - TAP_V_M_KSCAN[0]:.2f} m for this scan.")
        print(f"  hindcast {CALIB_WIN[0]}-{CALIB_WIN[1]} = {want_cm:.2f} cm, held by "
              f"per-draw bisection at every k")
        summ = [price_at(k, solve_rate(k), post, drivers, gmt, rows, TAP_V_M_KSCAN)
                for k in K_SCAN]

        print(f"\n=== THE RE-PRICED TAP ===\n")
        print(f"  {'k':>6} {'rate s':>8} {'base 585':>9} {'base ratio':>11} "
              f"{'head m':>7} | {'pass':>9} {'V range m':>12} {'ratio range':>14}")
        for r in summ:
            vr = ("--" if r["n_pass"] == 0
                  else f"{r['v_pass_lo']:.2f}-{r['v_pass_hi']:.2f}")
            print(f"  {r['k_c']:6.2f} {r['rate_scale']:8.4f} "
                  f"{r['base_m2300_585']:9.3f} {r['base_ratio']:11.2f}x "
                  f"{r['head_med']:7.2f} | {r['n_pass']:4d}/{r['n_admissible']:<4d} "
                  f"{vr:>12} "
                  f"{r['ratio_lo']:6.2f}-{r['ratio_hi']:<7.2f}")
        print(f"\n  (head = {TAPPED}-basin ice left at 2300/ssp585 BEFORE the tap; "
              f"it is what caps V)")
        base1 = next((r for r in summ if r["k_c"] == 1.0), None)
        if base1 is not None:
            for r in summ:
                if r["k_c"] == 1.0 or r["n_pass"] == 0 or base1["n_pass"] == 0:
                    continue
                print(f"  k = {r['k_c']:g}: the tap that clears is "
                      f"{base1['v_pass_hi'] / r['v_pass_hi']:.2f}x SMALLER at the top "
                      f"of its V range than at k = 1, and the base already delivers "
                      f"{r['base_m2300_585'] / base1['base_m2300_585']:.2f}x as much "
                      f"ssp585@2300")

    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")

if __name__ == "__main__":
    main()
