#!/usr/bin/env python3
"""
scope_gis_2300_relaxation.py — WHY is Ladrillo 1.0's Greenland (A+B, regional
driver, amp law) FLATTER at 2300 than the stock SIMPLE module it replaced?

Thread 5, second step. The first step (python/scope_greenland_bochow2026.py,
commit 9665014) established the fact: L10 minus extC, Greenland median, cm rel
1995-2014, is -0.45 / +0.90 / +4.78 at 2100 but -11.37 / -11.13 / -9.52 at 2300
(SSP1-2.6 / SSP2-4.5 / SSP5-8.5). This script asks which term of the model does
it, WITHOUT running a chain or touching the calibrator.

THE DECOMPOSITION. Both modules are the same first-order relaxation written two
ways: a loss L(t) closing on a committed loss Leq(T(t)) at a rate r(T). So

    L(y) = phi(y) * Leq(y),      phi = the realised FRACTION of the commitment

and the 2300 gap between the two modules splits exactly (symmetric/Shapley form)
into a COMMITMENT term and a REALISATION term:

    dL = (phi_A - phi_S) * (Leq_A + Leq_S)/2   +   (Leq_A - Leq_S) * (phi_A + phi_S)/2
         [------- realisation -------]             [------- commitment -------]

Which term dominates decides what thread 5 is actually about. If it is
REALISATION, the relaxation form is the problem and the spec's item 9 framing
("what replaces proportional relaxation at high warming") is right. If it is
COMMITMENT, the relaxation form is a red herring and the question is the
equilibrium sensitivity c1 on the regional driver.

MEDIAN-LEVEL ALGEBRA, STATED. The decomposition is applied to per-scenario
MEDIANS of two DIFFERENT posteriors, which are not paired, so it cannot be done
per draw. Medians are not multiplicative, so the script CHECKS
med(phi)*med(Leq) against med(L) and prints the residual rather than assuming it
away -- the "56% redundant" retraction in handoff 2026-08-14 came from exactly
this trap.

REPRODUCTION GATE. Both modules are re-implemented here in numpy from
julia/greenland_ab_component.jl and MimiBRICK's greenland_icesheet_component.jl,
including the t-1 lag, the clamps, and the V/V0 rate damping that A+B drops. The
script re-derives the 2100/2150/2300 medians and REFUSES to print a diagnosis
unless they match the recorded projection CSVs. Nothing downstream is
trustworthy if that gate fails.

  source ~/climate-env/bin/activate
  python3 python/scope_gis_2300_relaxation.py
Writes outputs/scope_gis_2300_relaxation.csv
"""
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBS = os.path.join(REPO, "data/observations")
OUT = os.path.join(REPO, "outputs/scope_gis_2300_relaxation.csv")

# ---- the two arms being compared -------------------------------------------
AB_TAG = "L10 (A+B, regional driver, amp law)"
AB_POST = os.path.join(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_L10.csv")
AB_RECORDED = os.path.join(REPO, "outputs/ssps_components_2300_L10.csv")
STOCK_TAG = "extC (stock SIMPLE, GMST driver)"
STOCK_POST = os.path.join(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_extC.csv")
STOCK_RECORDED = os.path.join(
    REPO, "outputs/quarantine/20260813_extc_vintage/ssps_components_2300_extC.csv")

# ---- must match julia/ladrillo_projection.jl and calibrate_mcmc_ext.jl ------
Y0, Y1 = 1850, 2300
REF = (1995, 2014)                 # AR6 reporting baseline
DRIVER_BASE = (1850, 1900)         # GMST rebase window (the frame contract)
GIS_ZONE = "south"
GIS_V0_M = 7.42
GIS_G = 0.0
SHAPE_WIN = 30                     # amp-law warming-level averaging window, yr
ANCHOR_N = 11                      # anchor-preserving splice window, yr
NTHIN = 2000                       # same thinning the projection driver applies
SSPS = [("ssp126", "SSP1-2.6"), ("ssp245", "SSP2-4.5"), ("ssp585", "SSP5-8.5")]
HORIZONS = (2100, 2150, 2300)
GATE_TOL_CM = 0.05                 # reproduction gate on the recorded medians

YEARS = np.arange(Y0, Y1 + 1)
IREF = (YEARS >= REF[0]) & (YEARS <= REF[1])


# ---------------------------------------------------------------------------
# drivers
# ---------------------------------------------------------------------------
def _running_mean(v, w):
    """Centred running mean, shrinking at the ends — matches _running_mean in
    julia/ladrillo_projection.jl exactly (lo = (w-1)//2, hi = w//2)."""
    if w <= 1:
        return np.asarray(v, float)
    n, lo, hi = len(v), (w - 1) // 2, w // 2
    return np.array([v[max(0, i - lo):min(n, i + hi + 1)].mean() for i in range(n)])


def gmst_rebased(ssp):
    g = (pd.read_csv(os.path.join(OBS, f"fair_mean_gmst_{ssp}.csv"))
         .set_index("year")["gmst_C"].reindex(YEARS).to_numpy())
    if not np.isfinite(g).all():
        raise SystemExit(f"fair_mean_gmst_{ssp}.csv does not cover {Y0}-{Y1}")
    ib = (YEARS >= DRIVER_BASE[0]) & (YEARS <= DRIVER_BASE[1])
    return g, g - g[ib].mean()


def gis_shape_table():
    tbl = pd.read_csv(os.path.join(REPO, "outputs/gis_amp_shape.csv"))
    meta = pd.read_csv(os.path.join(REPO, "outputs/gis_amp_shape_meta.csv")).iloc[0]
    x, y = tbl["dt"].to_numpy(), tbl["S"].to_numpy()
    S = lambda dt: np.interp(np.clip(dt, x[0], x[-1]), x, y)
    # the identity the whole construction rests on, asserted in the Julia too
    assert abs(S(float(meta.anchor_dt)) - 1.0) < 1e-9, "S(anchor) != 1"
    return S


def regional_driver(gmst_rb, amp, S):
    """A+B's driver: observed southern-Greenland T where it exists, then
    amp*S(warming level)*GMST spliced on with the offset that preserves the
    observed mean over the 11-yr anchor window. Vectorised over `amp` (draws)."""
    tgz = pd.read_csv(os.path.join(OBS, "t_gis_zones.csv"))
    gd = dict(zip(tgz["year"].astype(int), tgz[GIS_ZONE].astype(float)))
    last = int(tgz["year"].max())
    obs = np.array([gd.get(int(y), 0.0) for y in YEARS])
    mask = YEARS <= last
    ianch = np.isin(YEARS, np.arange(last - ANCHOR_N + 1, last + 1))
    anchor = obs[ianch].mean()
    shape = S(_running_mean(gmst_rb, SHAPE_WIN))
    shape_anchor = float((shape[ianch] * gmst_rb[ianch]).mean())
    amp = np.atleast_1d(np.asarray(amp, float))[:, None]           # (ndraw, 1)
    spliced = amp * shape[None, :] * gmst_rb[None, :] + (anchor - amp * shape_anchor)
    return np.where(mask[None, :], obs[None, :], spliced)


# ---------------------------------------------------------------------------
# the two modules, vectorised over draws
# ---------------------------------------------------------------------------
def run_ab(T, p):
    """julia/greenland_ab_component.jl. T is (ndraw, nyear); p a DataFrame.
    Returns (loss, eq) in m SLE, both (ndraw, nyear)."""
    c1 = p["gis_c1"].to_numpy()[:, None]
    c0 = p["gis_c0"].to_numpy()[:, None]
    f = p["gis_f"].to_numpy()
    af, bf = p["gis_alpha_f"].to_numpy(), p["gis_beta_f"].to_numpy()
    a_s, bs = p["gis_alpha_s"].to_numpy(), p["gis_beta_s"].to_numpy()
    eq = np.clip(c1 * T + c0, 0.0, GIS_V0_M)
    n, ny = T.shape
    fast, slow = np.empty((n, ny)), np.empty((n, ny))
    fast[:, 0] = GIS_G * f * eq[:, 0]
    slow[:, 0] = GIS_G * (1.0 - f) * eq[:, 0]
    for i in range(1, ny):
        Tm = T[:, i - 1]
        rf = np.clip(af * Tm + bf, 1e-9, 1.0)
        rs = np.clip(a_s * Tm + bs, 1e-9, 1.0)
        fast[:, i] = fast[:, i - 1] + (f * eq[:, i - 1] - fast[:, i - 1]) * rf
        slow[:, i] = slow[:, i - 1] + ((1.0 - f) * eq[:, i - 1] - slow[:, i - 1]) * rs
    return fast + slow, eq, fast, slow


def run_stock(T, p):
    """MimiBRICK greenland_icesheet_component.jl, including the V/V0 damping of
    the rate that A+B drops. T is (1, nyear) GMST (NOT rebased — the stock module
    is driven by the raw forcing series, as set_forcing! does)."""
    a = p["greenland_a"].to_numpy()[:, None]
    b = p["greenland_b"].to_numpy()[:, None]
    al, be = p["greenland_alpha"].to_numpy(), p["greenland_beta"].to_numpy()
    v0 = p["greenland_v0"].to_numpy()
    eqv = a * T + b                       # equilibrium VOLUME, m SLE
    n, ny = eqv.shape
    V, tau = np.empty((n, ny)), np.empty((n, ny))
    V[:, 0] = v0
    tau[:, 0] = al * T[:, 0] + be
    for i in range(1, ny):
        V[:, i] = V[:, i - 1] + tau[:, i - 1] * (eqv[:, i - 1] - V[:, i - 1])
        tau[:, i] = (al * T[:, i] + be) * (V[:, i] / v0)
    sle = np.where(V > 0.0, v0[:, None] - V, v0[:, None])
    return sle, v0[:, None] - eqv, tau     # loss, committed loss, rate


def thin(path):
    d = pd.read_csv(path)
    if len(d) > NTHIN:
        step = -(-len(d) // NTHIN)         # cld, as ladrillo_posterior does
        d = d.iloc[::step].iloc[:NTHIN]
    return d.reset_index(drop=True)


def cm_rel_ref(loss_m):
    return 100.0 * (loss_m - loss_m[:, IREF].mean(axis=1, keepdims=True))


def recorded(path):
    d = pd.read_csv(path)
    d = d[d["component"] == "gis"]
    return {(int(r.year), r.ssp): float(r.med) for r in d.itertuples()}


# ---------------------------------------------------------------------------
def main():
    S = gis_shape_table()
    post_ab, post_st = thin(AB_POST), thin(STOCK_POST)
    rec_ab, rec_st = recorded(AB_RECORDED), recorded(STOCK_RECORDED)
    iy = {y: int(np.where(YEARS == y)[0][0]) for y in HORIZONS}

    print(f"Greenland 2300 flatness — where the gap comes from")
    print(f"  A+B    : {AB_TAG}, {len(post_ab)} draws")
    print(f"  stock  : {STOCK_TAG}, {len(post_st)} draws")
    print(f"  base   : {REF[0]}-{REF[1]}; horizons {HORIZONS}\n")

    rows, gate_fail = [], []
    for ssp, label in SSPS:
        gmst_raw, gmst_rb = gmst_rebased(ssp)
        T_ab = regional_driver(gmst_rb, post_ab["gis_amp"].to_numpy(), S)
        L_ab, Eq_ab, F_ab, Sl_ab = run_ab(T_ab, post_ab)
        T_st = np.repeat(gmst_raw[None, :], len(post_st), axis=0)
        L_st, Eq_st, tau_st = run_stock(T_st, post_st)
        cm_ab, cm_st = cm_rel_ref(L_ab), cm_rel_ref(L_st)

        for y in HORIZONS:
            i = iy[y]
            for tag, cm, rec in (("A+B", cm_ab, rec_ab), ("stock", cm_st, rec_st)):
                got, want = float(np.median(cm[:, i])), rec.get((y, label))
                if want is None:
                    continue
                if abs(got - want) > GATE_TOL_CM:
                    gate_fail.append((tag, label, y, got, want))

        for y in HORIZONS:
            i = iy[y]
            # medians of the three quantities, each taken over draws
            m = lambda v: float(np.median(v))
            for tag, L, Eq, cm, extra in (
                ("A+B", L_ab, Eq_ab, cm_ab,
                 dict(driver_K=m(T_ab[:, i]),
                      eq_fast_m=m(post_ab["gis_f"].to_numpy() * Eq_ab[:, i]),
                      loss_fast_m=m(F_ab[:, i]), loss_slow_m=m(Sl_ab[:, i]),
                      phi_fast=m(F_ab[:, i] / (post_ab["gis_f"].to_numpy() * Eq_ab[:, i])),
                      phi_slow=m(Sl_ab[:, i] /
                                 ((1 - post_ab["gis_f"].to_numpy()) * Eq_ab[:, i])))),
                ("stock", L_st, Eq_st, cm_st,
                 dict(driver_K=float(np.median(T_st[:, i])), tau_yr=m(1.0 / tau_st[:, i]))),
            ):
                phi = L[:, i] / Eq[:, i]
                rate = 100.0 * (L[:, i] - L[:, i - 10]) / 10.0     # cm/yr, last decade
                rows.append(dict(
                    ssp=label, year=y, arm=tag,
                    cm_rel_ref=m(cm[:, i]), loss_m=m(L[:, i]), eq_m=m(Eq[:, i]),
                    phi=m(phi), remaining_m=m(Eq[:, i] - L[:, i]),
                    rate_cm_per_yr=m(rate),
                    med_prod_resid_m=m(phi) * m(Eq[:, i]) - m(L[:, i]), **extra))

    if gate_fail:
        print("REPRODUCTION GATE FAILED — refusing to diagnose. "
              f"tolerance {GATE_TOL_CM} cm:")
        for tag, label, y, got, want in gate_fail:
            print(f"    {tag:6s} {label} {y}: offline {got:8.3f}  recorded {want:8.3f}"
                  f"  diff {got - want:+.3f} cm")
        raise SystemExit(1)
    print(f"REPRODUCTION GATE PASSED — all {len(SSPS) * len(HORIZONS) * 2} "
          f"medians within {GATE_TOL_CM} cm of the recorded projections.\n")

    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)

    print("  LEVELS — committed loss Leq, realised loss L, realised fraction phi")
    print(f"  {'scenario':10s} {'year':>5s} {'arm':6s} {'driver K':>9s} {'Leq m':>8s} "
          f"{'L m':>8s} {'phi':>7s} {'left m':>8s} {'cm/yr':>7s} {'cm ref':>8s}")
    for _, r in df.iterrows():
        print(f"  {r.ssp:10s} {int(r.year):5d} {r.arm:6s} {r.driver_K:9.2f} "
              f"{r.eq_m:8.3f} {r.loss_m:8.3f} {r.phi:7.3f} {r.remaining_m:8.3f} "
              f"{r.rate_cm_per_yr:7.3f} {r.cm_rel_ref:8.2f}")

    print("\n  THE DECOMPOSITION at 2300 — A+B minus stock, m SLE of cumulative loss")
    print(f"  {'scenario':10s} {'dL':>8s} {'realisation':>13s} {'commitment':>12s} "
          f"{'med-resid':>10s}")
    for _, label in SSPS:
        a = df[(df.ssp == label) & (df.year == 2300) & (df.arm == "A+B")].iloc[0]
        s = df[(df.ssp == label) & (df.year == 2300) & (df.arm == "stock")].iloc[0]
        d_real = (a.phi - s.phi) * (a.eq_m + s.eq_m) / 2.0
        d_comm = (a.eq_m - s.eq_m) * (a.phi + s.phi) / 2.0
        resid = (a.loss_m - s.loss_m) - (d_real + d_comm)
        print(f"  {label:10s} {a.loss_m - s.loss_m:8.3f} {d_real:13.3f} "
              f"{d_comm:12.3f} {resid:10.2e}")
        print(f"  {'':10s} {'':8s} {'(phi ' + f'{s.phi:.3f}->{a.phi:.3f})':>13s} "
              f"{'(Leq ' + f'{s.eq_m:.2f}->{a.eq_m:.2f})':>12s}")

    print("\n  MEDIAN NON-ADDITIVITY CHECK — med(phi)*med(Leq) - med(L), m SLE")
    print("  (large values mean the decomposition above is a median-level "
          "statement only)")
    bad = df.loc[df.med_prod_resid_m.abs().idxmax()]
    print(f"  max |resid| = {bad.med_prod_resid_m:+.4f} m at "
          f"{bad.ssp} {int(bad.year)} {bad.arm}")

    cross(S, post_ab, post_st)
    channels(S, post_ab)
    literature(df)
    stress(S, post_ab)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


# ---------------------------------------------------------------------------
# The 2x2 cross-test. The decomposition above is a LINEARISATION at 2300; this
# swaps the two factors inside the actual dynamics, which is the version that
# cannot be argued with. Each arm's committed-loss series Leq(t) is a plain time
# series in m SLE, so it can be fed to the other arm's relaxation unchanged --
# no driver mapping is needed or assumed.
# ---------------------------------------------------------------------------
def relax(eq, rate_fn):
    """Explicit-Euler relaxation with the t-1 lag both modules use. `rate_fn`
    takes (index, current loss) so the stock module's V/V0 rate damping — which
    depends on the state, not just the driver — is carried faithfully."""
    L = np.zeros_like(eq)
    for i in range(1, len(eq)):
        L[i] = L[i - 1] + (eq[i - 1] - L[i - 1]) * rate_fn(i - 1, L[i - 1])
    return L


def cross(S, post_ab, post_st):
    """The 2x2. Run at POSTERIOR MEDIAN PARAMETERS for each arm — a single
    trajectory per cell — because the two posteriors are different objects and
    pairing their draws would invent a correlation. That makes this a structural
    statement, not an uncertainty one; the diagonal is printed against the
    median TRAJECTORY so the median-parameter substitution is visible rather
    than assumed."""
    print("\n  2x2 CROSS-TEST — swap commitment and relaxation inside the dynamics")
    print("  (median parameters; A+B's two channels collapsed to their")
    print("   f-weighted mean rate, so its diagonal is approximate by that much)")
    pa = post_ab.median(numeric_only=True)
    ps = post_st.median(numeric_only=True)
    i2300 = int(np.where(YEARS == 2300)[0][0])
    print(f"  {'scenario':10s} {'commitment':>11s} {'relaxation':>11s} "
          f"{'L2300 m':>9s} {'cm rel ref':>11s}")
    for ssp, label in SSPS:
        gmst_raw, gmst_rb = gmst_rebased(ssp)
        T_ab = regional_driver(gmst_rb, np.array([pa["gis_amp"]]), S)[0]
        T_st = gmst_raw
        eq_ab = np.clip(pa["gis_c1"] * T_ab + pa["gis_c0"], 0.0, GIS_V0_M)
        eq_st = ps["greenland_v0"] - (ps["greenland_a"] * T_st + ps["greenland_b"])
        f = pa["gis_f"]
        r_ab = (f * np.clip(pa["gis_alpha_f"] * T_ab + pa["gis_beta_f"], 1e-9, 1.0)
                + (1 - f) * np.clip(pa["gis_alpha_s"] * T_ab + pa["gis_beta_s"],
                                    1e-9, 1.0))
        v0s = ps["greenland_v0"]
        base = np.clip(ps["greenland_alpha"] * T_st + ps["greenland_beta"], 1e-9, 1.0)

        def rate_ab(i, _L):
            return r_ab[i]

        def rate_st(i, L):
            return base[i] * (v0s - L) / v0s      # the V/V0 damping A+B drops

        for cn, eq in (("A+B", eq_ab), ("stock", eq_st)):
            for rn, rf in (("A+B", rate_ab), ("stock", rate_st)):
                L = relax(eq, rf)
                print(f"  {label:10s} {cn:>11s} {rn:>11s} {L[i2300]:9.3f} "
                      f"{100.0 * (L[i2300] - L[IREF].mean()):11.2f}")


# ---------------------------------------------------------------------------
# The commitment/timescale stress test. If the 2300 shortfall is a COMMITMENT
# shortfall, the obvious question is why the calibration does not simply find a
# bigger commitment. This answers it: the hindcast constrains the PRODUCT
# phi*Leq, so scaling c1 up forces the relaxation rate down by very nearly the
# same factor to keep the observed 1900-2025 loss. The test scales c1/c0 by k,
# re-solves the rate scale s that restores the hindcast, and reports what the
# 2300 projection then becomes.
# ---------------------------------------------------------------------------
TARGETS = os.path.join(REPO, "outputs/recalib_targets_ext.csv")
HIND = (1900, 2025)                   # the gis target window that has data
C1_SCALES = (1.0, 2.0, 5.0, 10.0, 22.6)   # 22.6 = the Bochow-matched commitment
STRESS_SSP = "ssp245"


def _ab_series(T, pa, k_c, s_r):
    """A+B at median params with the commitment scaled by k_c and both channel
    rates by s_r. Same equations as run_ab, one draw."""
    eq = np.clip(k_c * (pa["gis_c1"] * T + pa["gis_c0"]), 0.0, GIS_V0_M)
    f = pa["gis_f"]
    rf = np.clip(s_r * (pa["gis_alpha_f"] * T + pa["gis_beta_f"]), 1e-9, 1.0)
    rs = np.clip(s_r * (pa["gis_alpha_s"] * T + pa["gis_beta_s"]), 1e-9, 1.0)
    fast = np.zeros_like(T)
    slow = np.zeros_like(T)
    for i in range(1, len(T)):
        fast[i] = fast[i - 1] + (f * eq[i - 1] - fast[i - 1]) * rf[i - 1]
        slow[i] = slow[i - 1] + ((1 - f) * eq[i - 1] - slow[i - 1]) * rs[i - 1]
    return fast + slow, eq, rs


def stress(S, post_ab):
    tgt = pd.read_csv(TARGETS).set_index("year")["gis"]
    want_cm = float(tgt.loc[HIND[1]] - tgt.loc[HIND[0]])
    pa = post_ab.median(numeric_only=True)
    _, gmst_rb = gmst_rebased(STRESS_SSP)
    T = regional_driver(gmst_rb, np.array([pa["gis_amp"]]), S)[0]
    ih0, ih1 = int(np.where(YEARS == HIND[0])[0][0]), int(np.where(YEARS == HIND[1])[0][0])
    i23 = int(np.where(YEARS == 2300)[0][0])

    def hind_cm(k, s):
        L, _, _ = _ab_series(T, pa, k, s)
        return 100.0 * (L[ih1] - L[ih0])

    print(f"\n  COMMITMENT/TIMESCALE STRESS TEST — driver {STRESS_SSP}, median params")
    print(f"  the {HIND[0]}-{HIND[1]} Greenland target is {want_cm:.2f} cm "
          f"(recalib_targets_ext.csv); for each commitment scale k the rate scale")
    print(f"  s is re-solved to reproduce it, and the 2300 projection re-read")
    print(f"  {'k (c1,c0)':>10s} {'Leq2300 m':>10s} {'rate s':>9s} "
          f"{'tau_slow yr':>12s} {'hind cm':>9s} {'2300 cm ref':>12s}")
    for k in C1_SCALES:
        lo, hi = 1e-4, 1e3                      # bisect in the rate scale
        for _ in range(80):
            mid = np.sqrt(lo * hi)
            if hind_cm(k, mid) < want_cm:
                lo = mid
            else:
                hi = mid
        s = np.sqrt(lo * hi)
        L, eq, rs = _ab_series(T, pa, k, s)
        cm = 100.0 * (L[i23] - L[IREF].mean())
        print(f"  {k:10.1f} {eq[i23]:10.3f} {s:9.4f} {1.0 / rs[i23]:12.0f} "
              f"{hind_cm(k, s):9.2f} {cm:12.2f}")
    print("  (tau_slow is the slow channel's e-folding time at the 2300 driver)")


# ---------------------------------------------------------------------------
# The two channels' actual e-folding times. A+B's channels are NAMED fast
# (surface mass balance) and slow (dynamic discharge) and the Mouginot partition
# pins f, the fast share of the COMMITMENT, on that reading -- so whether the
# posterior actually puts the slow channel on a longer timescale is worth
# checking rather than assuming from the names.
# ---------------------------------------------------------------------------
CHANNEL_YEARS = (2025, 2100, 2300)
CHANNEL_TEST_K = 2.0          # regional anomaly at which the draw share is counted


def channels(S, post_ab):
    pa = post_ab.median(numeric_only=True)
    af, bf = pa["gis_alpha_f"], pa["gis_beta_f"]
    a_s, bs = pa["gis_alpha_s"], pa["gis_beta_s"]
    share = float(np.mean(post_ab["gis_alpha_s"] * CHANNEL_TEST_K + post_ab["gis_beta_s"]
                          > post_ab["gis_alpha_f"] * CHANNEL_TEST_K + post_ab["gis_beta_f"]))
    print("\n  CHANNEL TIMESCALES at posterior medians")
    print(f"    fast (SMB)      alpha {af:.6f}  beta {bf:.6f}")
    print(f"    slow (dynamic)  alpha {a_s:.6f}  beta {bs:.6f}")
    print(f"    the SLOW channel relaxes FASTER than the fast one above "
          f"T_south = {(bf - bs) / (a_s - af):+.2f} K, i.e. over the whole "
          f"projection;\n    {share:.1%} of draws have slow > fast at "
          f"T_south = {CHANNEL_TEST_K:.1f} K")
    print(f"  {'scenario':10s} {'year':>5s} {'T_south K':>10s} {'tau_fast yr':>12s} "
          f"{'tau_slow yr':>12s}")
    for ssp, label in SSPS:
        _, gmst_rb = gmst_rebased(ssp)
        T = regional_driver(gmst_rb, np.array([pa["gis_amp"]]), S)[0]
        for y in CHANNEL_YEARS:
            i = int(np.where(YEARS == y)[0][0])
            tf = 1.0 / np.clip(af * T[i] + bf, 1e-9, 1.0)
            ts = 1.0 / np.clip(a_s * T[i] + bs, 1e-9, 1.0)
            print(f"  {label:10s} {y:5d} {T[i]:10.2f} {tf:12.1f} {ts:12.1f}")
    print("  NB neither channel exceeds ~80 yr anywhere. Greenland's dynamic")
    print("  response is millennial, so the module has no slow reservoir at all.")


# ---------------------------------------------------------------------------
# The literature anchor. "Lower than stock SIMPLE" is not by itself a defect --
# stock's own commitment is dominated by a temperature-INDEPENDENT intercept
# (its greenland_b), which is its own problem. The question that decides whether
# A+B's commitment is wrong rather than merely different is what an ice-sheet
# model says the commitment is at the same sustained GMST.
# ---------------------------------------------------------------------------
def literature(df):
    from scope_greenland_bochow2026 import FAMILIES, committed_loss
    print("\n  COMMITTED LOSS vs Bochow et al. 2026 (PREPRINT, provisional) at each")
    print("  scenario's own 2300 GMST — m SLE")
    print(f"  {'scenario':10s} {'GMST K':>7s} {'A+B':>7s} {'stock':>7s} "
          + "".join(f"{f:>11s}" for f in FAMILIES) + f"{'A+B / min lit':>14s}")
    for ssp, label in SSPS:
        gmst_raw, _ = gmst_rebased(ssp)
        p = float(gmst_raw[int(np.where(YEARS == 2300)[0][0])])
        a = df[(df.ssp == label) & (df.year == 2300) & (df.arm == "A+B")].eq_m.iloc[0]
        st = df[(df.ssp == label) & (df.year == 2300) & (df.arm == "stock")].eq_m.iloc[0]
        lit = [committed_loss(FAMILIES[f], p) for f in FAMILIES]
        print(f"  {label:10s} {p:7.2f} {a:7.3f} {st:7.3f} "
              + "".join(f"{v:11.2f}" for v in lit)
              + f"{min(lit) / a:13.0f}x low")
    print("  CAVEAT: above ~6 K the Bochow branch map extrapolates past its own")
    print("  deglaciated branch, so the 7.81 K column can exceed the 7.42 m ice")
    print("  sheet. The 1.74 K and 3.15 K columns are the ones to lean on.")


if __name__ == "__main__":
    main()
