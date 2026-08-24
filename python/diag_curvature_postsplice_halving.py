#!/usr/bin/env python3
"""
diag_curvature_postsplice_halving.py -- is the component sum's post-splice
curvature HALVING real, or is it the LWS hold-flat construction?

THE QUESTION (handoff 2026-08-24d sec 1, carried forward as 2026-08-24e open
item 1's second half). The observed component sum's quadratic acceleration
falls from 0.007189 cm/yr^2 over 1993-2018 to 0.003533 over the window that
includes the splice -- a factor of 2.03. At the same time
`prep_recalib_targets_ext.py:311` holds LWS EXACTLY CONSTANT at its 2018 value
for 2019+, by fiat, because Frederikse's TWS stream ends in 2018. A series held
flat for the last years of a fitted window pulls that window's quadratic term
down mechanically. So the halving has a candidate artifact explanation and had
never been priced against it. "Real post-2018 slowdown vs splice artifact: NOT
established" was the flag; this file establishes it.

WHY THE DECOMPOSITION IS EXACT, NOT AN APPROXIMATION. The estimator is
2 x the quadratic coefficient of an ORDINARY LEAST SQUARES fit on a fixed design
matrix (the window's years). OLS is linear in the response, and every component
shares the window, so accel(sum of components) = sum of accel(component) to
machine precision. Gate [LINEARITY] asserts it rather than assuming it. That is
what lets a single component be charged a share of the drop.

WHY THE INDEPENDENT TOTAL IS THE VERDICT AND THE COUNTERFACTUALS ARE ONLY A
BOUND. Dangendorf 2024 is a reconstruction of the TOTAL. It is not built from
our components, it carries no LWS hold-flat, and it is real data across the whole
of both windows. If it decelerates over the same window change, deceleration is
in the observations and not in our construction -- no extrapolation required to
say so. The LWS counterfactual arms below are EXTRAPOLATIONS, not data (no
post-2018 TWS product is on disk; Frederikse's ends 2018 and IGCC 2024 carries no
land-water-storage component), so they can bound the artifact's size but cannot
be quoted as a measurement.

THE ESTIMATOR IS COPIED, NOT REINVENTED. `accel_of` here is a transcription of
`julia/diag_curvature_deficit_2x2.jl:84`, so every number in this file is on the
same estimator as the 2x2 and as the 0.65x / 0.727x deficits. Gate [IDENT]
reproduces the two shipped numbers before anything else runs.

  python3 python/diag_curvature_postsplice_halving.py [--tag=L14]
Writes outputs/diag_curvature_postsplice_{decomp,arms,windows}_<tag>.csv
"""
import csv
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--tag=")), "L14")
SRC = os.path.join(REPO, "outputs", "recalib_targets_ext.csv")

# ---- every label in this file derives from these -------------------------
COMPONENTS = ["ais", "gsic", "gis", "steric", "lws"]
TOTAL_COL = "dang"                 # the INDEPENDENT total; not a sum of the above
TOTAL_NAME = "Dangendorf 2024 + NOAA STAR"
SPLICE_YEAR = 2018                 # last Frederikse year; LWS is fiat-flat after it
WIN_PRE = (1993, SPLICE_YEAR)      # no splice inside this window
WIN_POST = (1993, 2023)            # the sum's longest COMPLETE window -- see [WINDOW]
LWS_HOLD_FROM = SPLICE_YEAR + 1    # prep_recalib_targets_ext.py:311
# The two numbers the handoff shipped, reproduced by gate [IDENT].
SHIPPED_PRE, SHIPPED_POST = 0.007189, 0.003533
IDENT_TOL = 5e-7                   # the shipped numbers are quoted to 6 decimals
LIN_TOL = 1e-12                    # [LINEARITY] is an algebraic identity, not a fit
TREND_WIN = (1993, SPLICE_YEAR)    # window the LWS counterfactuals are fitted on
UNITS = "cm/yr^2"

OUT_DECOMP = os.path.join(REPO, "outputs", f"diag_curvature_postsplice_decomp_{TAG}.csv")
OUT_ARMS = os.path.join(REPO, "outputs", f"diag_curvature_postsplice_arms_{TAG}.csv")
OUT_WINDOWS = os.path.join(REPO, "outputs", f"diag_curvature_postsplice_windows_{TAG}.csv")
OUT_RECON = os.path.join(REPO, "outputs", f"diag_curvature_postsplice_recon_{TAG}.csv")
OUT_SWEEP = os.path.join(REPO, "outputs", f"diag_curvature_postsplice_sweep_{TAG}.csv")
OUT_SE = os.path.join(REPO, "outputs", f"diag_curvature_postsplice_se_{TAG}.csv")
# Frederikse's OWN total -- the reconstruction our five components come from, and the
# only like-for-like partner for their sum. mm, and it stops at the splice year.
FRED_TOTAL = os.path.join(REPO, "data/observations", "frederikse2020_gmsl_total.csv")
FRED_NAME = "Frederikse 2020 total"
MM_TO_CM = 0.1
# Sweep starts for [6]. Every window ends at the splice year, so both reconstructions
# carry real data throughout and no LWS fiat is inside any of them. Started at 1950
# because Frederikse's own budget non-closure peaks mid-century (prep_recalib_targets_ext.py
# CLOSURE block) and a window opening before that scores a different object.
SWEEP_STARTS = list(range(1950, 1999, 4))
SWEEP_REF = 1993          # the window the shipped 1.83x was measured in
SE_MC_SEED = 2026         # [SE-MC] is a gate, so its draw is fixed
SE_MC_N = 20000


def accel_of(v, yrs, w):
    """Quadratic-fit acceleration of a cumulative series, in cm/yr^2.

    Transcribed from julia/diag_curvature_deficit_2x2.jl:84. Returns NaN on any
    NaN inside the window -- deliberately, so a component that has run out of
    data cannot be silently dropped from a sum and change its meaning."""
    i0 = np.where(yrs == w[0])[0]
    i1 = np.where(yrs == w[1])[0]
    if len(i0) == 0 or len(i1) == 0:
        return np.nan
    sl = slice(i0[0], i1[0] + 1)
    x = (yrs[sl] - w[0]).astype(float)
    y = np.asarray(v[sl], dtype=float)
    if np.isnan(y).any():
        return np.nan
    A = np.vstack([np.ones_like(x), x, x ** 2]).T
    return 2.0 * np.linalg.lstsq(A, y, rcond=None)[0][2]


d = pd.read_csv(SRC)
YRS = d["year"].values
SER = {c: d[c].values for c in COMPONENTS + [TOTAL_COL]}
SER["sum5"] = d[COMPONENTS].sum(axis=1, min_count=len(COMPONENTS)).values
SER["sum4"] = d[[c for c in COMPONENTS if c != "lws"]].sum(
    axis=1, min_count=len(COMPONENTS) - 1).values

wpre = f"{WIN_PRE[0]}-{WIN_PRE[1]}"
wpost = f"{WIN_POST[0]}-{WIN_POST[1]}"
print(f"POST-SPLICE CURVATURE HALVING | tag {TAG} | units {UNITS}")
print(f"  estimator: 2 x OLS quadratic coefficient (diag_curvature_deficit_2x2.jl:84)")
print(f"  windows: pre-splice {wpre} | post-splice {wpost}")
print(f"  LWS held flat at its {SPLICE_YEAR} value from {LWS_HOLD_FROM} "
      f"(prep_recalib_targets_ext.py:311)")

# ===========================================================================
# GATES
# ===========================================================================
print("\n" + "=" * 78 + "\nGATES\n" + "=" * 78)

a_pre = accel_of(SER["sum5"], YRS, WIN_PRE)
a_post = accel_of(SER["sum5"], YRS, WIN_POST)
ok_ident = (abs(a_pre - SHIPPED_PRE) < IDENT_TOL) and (abs(a_post - SHIPPED_POST) < IDENT_TOL)
print(f"[IDENT]     sum5 {wpre} = {a_pre:.6f} vs shipped {SHIPPED_PRE:.6f} | "
      f"{wpost} = {a_post:.6f} vs shipped {SHIPPED_POST:.6f}  -> "
      f"{'PASS' if ok_ident else 'FAIL'}")
assert ok_ident, "estimator does not reproduce the shipped numbers -- stop"

# [WINDOW] the handoff labelled the second number 1993-2024. It is not: gsic ends
# 2023, so the five-component sum has no 2024 value at all and accel_of returns
# NaN there. Left as a printed gate rather than a silent correction, because the
# label travelled into two handoffs and a CHANGELOG entry.
a_2024 = accel_of(SER["sum5"], YRS, (WIN_POST[0], 2024))
gsic_last = int(d.loc[d["gsic"].notna(), "year"].max())
print(f"[WINDOW]    sum5 {WIN_POST[0]}-2024 = {a_2024} (gsic ends {gsic_last}) -> "
      f"the shipped 0.003533 is {wpost}, NOT {WIN_POST[0]}-2024. Label corrected.")

# [LINEARITY] the decomposition below charges each component a share of the drop.
# That is only meaningful if the accel of a sum IS the sum of the accels.
for w, lbl in ((WIN_PRE, wpre), (WIN_POST, wpost)):
    s = sum(accel_of(SER[c], YRS, w) for c in COMPONENTS)
    t = accel_of(SER["sum5"], YRS, w)
    print(f"[LINEARITY] {lbl}: sum of component accels {s:+.9f} vs accel of sum "
          f"{t:+.9f} | diff {abs(s - t):.2e} -> {'PASS' if abs(s - t) < LIN_TOL else 'FAIL'}")
    assert abs(s - t) < LIN_TOL

# ===========================================================================
# [1] DECOMPOSITION -- who is charged with the drop
# ===========================================================================
print("\n" + "=" * 78 + f"\n[1] DECOMPOSITION OF THE DROP ({UNITS})\n" + "=" * 78)
drop = a_post - a_pre
print(f"  sum5 {a_pre:+.6f} -> {a_post:+.6f} | drop {drop:+.6f} | "
      f"ratio {a_post / a_pre:.3f} (= 1/{a_pre / a_post:.2f})")
print(f"\n  {'component':10s} {wpre:>12s} {wpost:>12s} {'delta':>12s} {'share of drop':>14s}")
rows = []
for c in COMPONENTS:
    p, q = accel_of(SER[c], YRS, WIN_PRE), accel_of(SER[c], YRS, WIN_POST)
    share = (q - p) / drop
    print(f"  {c:10s} {p:+12.6f} {q:+12.6f} {q - p:+12.6f} {share:+13.1%}")
    rows.append([c, p, q, q - p, share])
with open(OUT_DECOMP, "w", newline="") as fh:
    w_ = csv.writer(fh)
    w_.writerow(["component", f"accel_{wpre}", f"accel_{wpost}", "delta", "share_of_drop"])
    for r in rows:
        w_.writerow([r[0]] + [f"{x:.9f}" for x in r[1:]])

# ===========================================================================
# [2] THE INDEPENDENT TOTAL -- the verdict leg
# ===========================================================================
print("\n" + "=" * 78 + "\n[2] THE INDEPENDENT TOTAL (no LWS construction in it)\n" + "=" * 78)
t_pre, t_post = accel_of(SER[TOTAL_COL], YRS, WIN_PRE), accel_of(SER[TOTAL_COL], YRS, WIN_POST)
s4_pre, s4_post = accel_of(SER["sum4"], YRS, WIN_PRE), accel_of(SER["sum4"], YRS, WIN_POST)
print(f"  {TOTAL_COL} ({TOTAL_NAME})")
print(f"    {t_pre:+.6f} -> {t_post:+.6f} | ratio {t_post / t_pre:.3f}")
print(f"  sum4 (component sum with LWS REMOVED from both windows)")
print(f"    {s4_pre:+.6f} -> {s4_post:+.6f} | ratio {s4_post / s4_pre:.3f}")
print(f"  sum5 (as shipped)                     ratio {a_post / a_pre:.3f}")
# What the sum WOULD be if it decelerated only as much as the independent total.
implied = a_pre * (t_post / t_pre)
print(f"\n  If sum5 decelerated at the total's own ratio it would read {implied:+.6f}; "
      f"it reads {a_post:+.6f},")
print(f"  an excess drop of {a_post - implied:+.6f} vs LWS's own delta "
      f"{accel_of(SER['lws'], YRS, WIN_POST) - accel_of(SER['lws'], YRS, WIN_PRE):+.6f}.")

# ===========================================================================
# [3] LWS COUNTERFACTUAL ARMS -- a bound, NOT a measurement
# ===========================================================================
print("\n" + "=" * 78 + "\n[3] LWS COUNTERFACTUAL ARMS (EXTRAPOLATIONS -- not data)\n" + "=" * 78)
lws = SER["lws"].copy()
i0 = np.where(YRS == TREND_WIN[0])[0][0]
i1 = np.where(YRS == TREND_WIN[1])[0][0]
xf = (YRS[i0:i1 + 1] - TREND_WIN[0]).astype(float)
yf = lws[i0:i1 + 1].astype(float)
lin = np.polyfit(xf, yf, 1)
qua = np.polyfit(xf, yf, 2)
post_mask = YRS >= LWS_HOLD_FROM
xp = (YRS[post_mask] - TREND_WIN[0]).astype(float)

ARMS = {
    "held_flat (SHIPPED)": lws,
    f"linear cont. of {TREND_WIN[0]}-{TREND_WIN[1]}": None,
    f"quadratic cont. of {TREND_WIN[0]}-{TREND_WIN[1]}": None,
}
alt_lin = lws.copy(); alt_lin[post_mask] = np.polyval(lin, xp)
alt_qua = lws.copy(); alt_qua[post_mask] = np.polyval(qua, xp)
ARMS[f"linear cont. of {TREND_WIN[0]}-{TREND_WIN[1]}"] = alt_lin
ARMS[f"quadratic cont. of {TREND_WIN[0]}-{TREND_WIN[1]}"] = alt_qua

sum4_arr = SER["sum4"]
arm_rows = []
print(f"  {'LWS arm':36s} {'lws@2023':>9s} {'sum5 ' + wpost:>16s} {'ratio to pre':>13s}")
for name, arr in ARMS.items():
    s5 = sum4_arr + arr
    v = accel_of(s5, YRS, WIN_POST)
    l23 = arr[np.where(YRS == WIN_POST[1])[0][0]]
    print(f"  {name:36s} {l23:9.3f} {v:+16.6f} {v / a_pre:13.3f}")
    arm_rows.append([name, l23, v, v / a_pre])
env = max(r[2] for r in arm_rows) - min(r[2] for r in arm_rows)
print(f"\n  ARM ENVELOPE {env:.6f} {UNITS} = {env / abs(drop):.1%} of the {abs(drop):.6f} drop.")
lws_sd = float(np.nanstd(np.diff(lws[(YRS >= TREND_WIN[0]) & (YRS <= TREND_WIN[1])])))
print(f"  For scale: LWS year-to-year change over {TREND_WIN[0]}-{TREND_WIN[1]} has sd "
      f"{lws_sd:.3f} cm, so the flat hold also removes real INTERANNUAL variance,")
print(f"  not only a trend. Every arm here is an extrapolation; none is an observation.")
with open(OUT_ARMS, "w", newline="") as fh:
    w_ = csv.writer(fh)
    w_.writerow(["lws_arm", "lws_2023_cm", f"sum5_accel_{wpost}", "ratio_to_pre",
                 "is_extrapolation"])
    for r in arm_rows:
        w_.writerow([r[0], f"{r[1]:.6f}", f"{r[2]:.9f}", f"{r[3]:.6f}",
                     "no" if r[0].startswith("held_flat") else "yes"])

# ===========================================================================
# [4] WINDOW-LENGTH CONTROL -- is the drop the record, or the window?
# ===========================================================================
print("\n" + "=" * 78 + "\n[4] WINDOW-LENGTH CONTROL\n" + "=" * 78)
print("  A longer window sees more of the curve, so a quadratic accel can fall")
print("  without the record decelerating. Matched-LENGTH windows separate the two.")
span = WIN_PRE[1] - WIN_PRE[0]
controls = [WIN_PRE, (WIN_POST[1] - span, WIN_POST[1]), WIN_POST]
print(f"\n  {'window':>12s} {'yrs':>4s} {'sum5':>11s} {'sum4':>11s} {'dang':>11s} "
      f"{'dang/sum5':>10s} {'dang-sum5':>11s}")
win_rows = []
for w in controls:
    r = [f"{w[0]}-{w[1]}", w[1] - w[0],
         accel_of(SER["sum5"], YRS, w), accel_of(SER["sum4"], YRS, w),
         accel_of(SER[TOTAL_COL], YRS, w)]
    r.append(r[4] / r[2])
    r.append(r[4] - r[2])
    print(f"  {r[0]:>12s} {r[1]:4d} {r[2]:+11.6f} {r[3]:+11.6f} {r[4]:+11.6f} {r[5]:10.2f}"
          f" {r[6]:+11.6f}")
    win_rows.append(r)
with open(OUT_WINDOWS, "w", newline="") as fh:
    w_ = csv.writer(fh)
    w_.writerow(["window", "n_years", "sum5_accel", "sum4_accel", f"{TOTAL_COL}_accel",
                 f"{TOTAL_COL}_over_sum5", f"{TOTAL_COL}_minus_sum5"])
    for r in win_rows:
        w_.writerow([r[0], r[1]] + [f"{x:.9f}" for x in r[2:]])

# !! The dang/sum5 RATIO explodes on the matched-length recent window only because its
# DENOMINATOR collapses toward zero. Quoting it bare would report a 19x reconstruction gap
# where the gap in the units the score is taken in barely moved (memory
# `ratio_needs_its_base`). The DIFFERENCE column is the honest one and is printed beside it.
gaps = [r[6] for r in win_rows]
print(f"\n  !! The dang-sum5 DIFFERENCE moves {min(gaps):+.6f} -> {max(gaps):+.6f} "
      f"({max(gaps) / min(gaps):.2f}x) while the RATIO moves "
      f"{min(r[5] for r in win_rows):.2f} -> {max(r[5] for r in win_rows):.2f}x. "
      f"The gap did not grow;\n     the base collapsed. Quote the difference.")

# The matched-length window is the one that isolates the record from the window, so the
# per-component read is taken there too -- otherwise a component's share of the drop and
# its recent behaviour are being read off two different window lengths.
print(f"\n  per component, matched-length {controls[0][0]}-{controls[0][1]} vs "
      f"{controls[1][0]}-{controls[1][1]}:")
print(f"  {'component':10s} {'early':>11s} {'late':>11s} {'ratio':>8s}")
for c in COMPONENTS:
    e, l = accel_of(SER[c], YRS, controls[0]), accel_of(SER[c], YRS, controls[1])
    rr = l / e if e != 0 else float("nan")
    print(f"  {c:10s} {e:+11.6f} {l:+11.6f} {rr:8.2f}"
          + ("   <- LWS is fiat-flat for 5 of these 25 years" if c == "lws" else ""))

# ===========================================================================
# [5] THE RECONSTRUCTION GAP IS NOT A CONSTANT
# ===========================================================================
print("\n" + "=" * 78 + "\n[5] THE RECONSTRUCTION GAP, BY WINDOW\n" + "=" * 78)
print("  Our five components are Frederikse 2020; the total target is Dangendorf 2024.")
print(f"  '{TOTAL_NAME}' is 1.83x Frederikse -- but that ratio was measured in ONE window.")
ft = pd.read_csv(FRED_TOTAL)
fy, fv = ft["year"].values, ft["value"].values * MM_TO_CM
recon_rows = []
print(f"\n  {'window':>12s} {'sum5':>11s} {FRED_NAME:>22s} {TOTAL_COL:>11s} "
      f"{'dang/fred':>10s} {'sum5/fred':>10s}")
for w in controls:
    f_ = accel_of(fv, fy, w)
    s5 = accel_of(SER["sum5"], YRS, w)
    dg = accel_of(SER[TOTAL_COL], YRS, w)
    df_ = dg / f_ if np.isfinite(f_) else float("nan")
    sf_ = s5 / f_ if np.isfinite(f_) else float("nan")
    print(f"  {w[0]}-{w[1]:<7d} {s5:+11.6f} {f_:+22.6f} {dg:+11.6f} {df_:10.2f} {sf_:10.3f}")
    recon_rows.append([f"{w[0]}-{w[1]}", s5, f_, dg, df_, sf_])
print(f"\n  {FRED_NAME} ENDS AT {int(fy.max())}, so only the first row is like-for-like.")
print("  In that row our component sum reproduces its own reconstruction's total"
      f" ({recon_rows[0][5]:.3f}x)")
print(f"  while the scored target runs {recon_rows[0][4]:.2f}x above it. The other rows"
      " have NO Frederikse")
print("  partner at all -- which is the mixing problem, stated as a measurement.")
with open(OUT_RECON, "w", newline="") as fh:
    w_ = csv.writer(fh)
    w_.writerow(["window", "sum5_accel", "frederikse_total_accel", f"{TOTAL_COL}_accel",
                 "dang_over_frederikse", "sum5_over_frederikse"])
    for r in recon_rows:
        w_.writerow([r[0]] + [f"{x:.9f}" for x in r[1:]])

# ===========================================================================
# [6] IS THE GAP MULTIPLICATIVE OR ADDITIVE? -- a window sweep
# ===========================================================================
print("\n" + "=" * 78 + "\n[6] GAP SWEEP -- 1.83x is a RATIO; is the gap actually additive?\n"
      + "=" * 78)
print(f"  Windows ENDING {SPLICE_YEAR}, so both reconstructions have real data throughout")
print("  and NO LWS fiat is inside any of them. Pure reconstruction vs reconstruction.")
print(f"\n  {'window':>12s} {FRED_NAME:>22s} {TOTAL_COL:>11s} {'ratio':>8s} {'difference':>11s}")
sweep = []
for y0 in SWEEP_STARTS:
    w = (y0, SPLICE_YEAR)
    f_ = accel_of(fv, fy, w)
    dg = accel_of(SER[TOTAL_COL], YRS, w)
    if not (np.isfinite(f_) and np.isfinite(dg)):
        continue
    print(f"  {y0}-{SPLICE_YEAR:<7d} {f_:+22.6f} {dg:+11.6f} {dg / f_:8.2f} {dg - f_:+11.6f}")
    sweep.append([f"{y0}-{SPLICE_YEAR}", f_, dg, dg / f_, dg - f_])
rs = [r[3] for r in sweep]
ds = [r[4] for r in sweep]
n_below = sum(1 for r in rs if r < 1.0)
print(f"\n  ratio spans {min(rs):.2f}-{max(rs):.2f}; difference spans {min(ds):+.6f} to "
      f"{max(ds):+.6f} -- BOTH change sign.")
print(f"  Dangendorf's acceleration is LOWER than Frederikse's in {n_below} of "
      f"{len(rs)} windows.")
print(f"  {FRED_NAME} accel spans {min(r[1] for r in sweep):+.6f} to "
      f"{max(r[1] for r in sweep):+.6f} ({max(r[1] for r in sweep) / min(r[1] for r in sweep):.1f}x)")
print(f"  {TOTAL_COL} accel spans          {min(r[2] for r in sweep):+.6f} to "
      f"{max(r[2] for r in sweep):+.6f} ({max(r[2] for r in sweep) / min(r[2] for r in sweep):.1f}x)")
print("\n  => NEITHER framing survives. The gap is not a constant factor AND not a constant")
print(f"     offset. The {SWEEP_REF}-{SPLICE_YEAR} value of 1.83x sits on a spike in the")
print("     DENOMINATOR, and test [7] shows why that denominator is unstable.")

with open(OUT_SWEEP, "w", newline="") as fh:
    w_ = csv.writer(fh)
    w_.writerow(["window", "frederikse_total_accel", f"{TOTAL_COL}_accel",
                 "ratio", "difference"])
    for r in sweep:
        w_.writerow([r[0]] + [f"{x:.9f}" for x in r[1:]])

# ===========================================================================
# [7] ERROR BARS ON THE ESTIMATOR -- which of these differences are real?
# ===========================================================================
print("\n" + "=" * 78 + "\n[7] ERROR BARS (nothing in this arc has carried one)\n" + "=" * 78)
print("  se is the OLS standard error of 2*b2, inflated by sqrt((1+rho)/(1-rho)) on the")
print("  fit residuals' lag-1 autocorrelation. It is a LOWER BOUND: it counts only the")
print("  scatter about the quadratic and NOT the reconstructions' own published band,")
print("  so every 'not significant' verdict below is conservative.")


def accel_se(v, yrs, w):
    """(accel, ols se, AR(1)-inflated se) of the same estimator as accel_of."""
    i0, i1 = np.where(yrs == w[0])[0], np.where(yrs == w[1])[0]
    if len(i0) == 0 or len(i1) == 0:
        return (np.nan,) * 3
    sl = slice(i0[0], i1[0] + 1)
    x = (yrs[sl] - w[0]).astype(float)
    y = np.asarray(v[sl], dtype=float)
    if np.isnan(y).any():
        return (np.nan,) * 3
    A = np.vstack([np.ones_like(x), x, x ** 2]).T
    b = np.linalg.lstsq(A, y, rcond=None)[0]
    r = y - A @ b
    s2 = r @ r / (len(x) - 3)
    se = 2.0 * np.sqrt(s2 * np.linalg.inv(A.T @ A)[2, 2])
    rho = np.corrcoef(r[:-1], r[1:])[0, 1]
    return 2.0 * b[2], se, se * np.sqrt(max((1 + rho) / (1 - rho), 1.0))


# [SE-MC] the inflation factor is a rule of thumb, so it is checked against a matched
# Monte Carlo rather than trusted: AR(1) noise at the fitted rho and residual sd, on the
# SAME design matrix, refitted MC_N times. The analytic se must not UNDER-state the
# empirical spread, or every "UNRESOLVED" verdict below would be optimistic.
def _se_mc(v, yrs, w, seed=SE_MC_SEED, n=SE_MC_N):
    i0, i1 = np.where(yrs == w[0])[0][0], np.where(yrs == w[1])[0][0]
    x = (yrs[i0:i1 + 1] - w[0]).astype(float)
    y = np.asarray(v[i0:i1 + 1], dtype=float)
    A = np.vstack([np.ones_like(x), x, x ** 2]).T
    r = y - A @ np.linalg.lstsq(A, y, rcond=None)[0]
    rho, sd, m = np.corrcoef(r[:-1], r[1:])[0, 1], r.std(ddof=3), len(x)
    rng = np.random.default_rng(seed)
    e = np.empty((n, m))
    e[:, 0] = rng.standard_normal(n) * sd
    sh = rng.standard_normal((n, m)) * sd * np.sqrt(max(1 - rho ** 2, 0.0))
    for t in range(1, m):
        e[:, t] = rho * e[:, t - 1] + sh[:, t]
    P = np.linalg.pinv(A)[2]
    return float((2.0 * (e @ P)).std())


SE_SERIES = [("sum5", SER["sum5"], YRS), (FRED_NAME, fv, fy),
             (TOTAL_COL, SER[TOTAL_COL], YRS)]
for nm, v, yy in SE_SERIES:
    _, _, sea = accel_se(v, yy, WIN_PRE)
    mc = _se_mc(v, yy, WIN_PRE)
    print(f"  [SE-MC] {nm:22s} analytic {sea:.6f} vs MC {mc:.6f} = {sea / mc:.2f}x -> "
          f"{'PASS (conservative)' if sea >= mc else 'FAIL (understates)'}")
    assert sea >= mc, f"analytic se understates the MC spread for {nm}"

print(f"\n  {'series':24s} {'window':>11s} {'accel':>11s} {'se':>10s} {'accel/se':>9s}")
se_rows = []
for w in (WIN_PRE, (WIN_POST[1] - span, WIN_POST[1]), WIN_POST):
    for nm, v, yy in SE_SERIES:
        a, se, sea = accel_se(v, yy, w)
        if not np.isfinite(a):
            print(f"  {nm:24s} {w[0]}-{w[1]}   (no data in window)")
            continue
        print(f"  {nm:24s} {w[0]}-{w[1]} {a:+11.6f} {sea:10.6f} {a / sea:9.2f}")
        se_rows.append([nm, f"{w[0]}-{w[1]}", a, se, sea, a / sea])
    print()


def contrast(n1, n2, w):
    """Difference of two series' accel over one window, with the ses added in
    quadrature. The two products are different reconstructions, so treating them as
    independent is the intended reading; a shared-method correlation would only
    SHRINK the error bar, and is flagged rather than modelled."""
    (a1, _, s1) = accel_se(dict(SE_SERIES_V)[n1][0], dict(SE_SERIES_V)[n1][1], w)
    (a2, _, s2) = accel_se(dict(SE_SERIES_V)[n2][0], dict(SE_SERIES_V)[n2][1], w)
    dd = a1 - a2
    ss = np.hypot(s1, s2)
    return dd, ss, dd / ss


SE_SERIES_V = [(nm, (v, yy)) for nm, v, yy in SE_SERIES]
print("  The three claims this arc rests on, re-read with the error bar. A difference at")
print("  <2 sigma is UNRESOLVED -- for a claimed AGREEMENT that means the agreement is")
print("  uninformative, not that it is confirmed; the error bar as a fraction of the")
print("  quantity being compared is printed so the two readings cannot be confused.")
CLAIMS = [
    (f"sum5 closes on {FRED_NAME} to 1.3%", "sum5", FRED_NAME, WIN_PRE),
    (f"{TOTAL_COL} is 1.83x {FRED_NAME}", TOTAL_COL, FRED_NAME, WIN_PRE),
    (f"sum5 falls short of {TOTAL_COL}", "sum5", TOTAL_COL, WIN_PRE),
]
for lbl, n1, n2, w in CLAIMS:
    dd, ss, z = contrast(n1, n2, w)
    base = abs(accel_se(dict(SE_SERIES_V)[n1][0], dict(SE_SERIES_V)[n1][1], w)[0])
    print(f"    {lbl:44s}\n      {w[0]}-{w[1]}: {dd:+.6f} +/- {ss:.6f} = {abs(z):.2f} sigma"
          f" | error bar = {ss / base:.0%} of the base -> "
          f"{'RESOLVED' if abs(z) >= 2 else 'UNRESOLVED'}")
_dd, _ss, _ = contrast("sum5", FRED_NAME, WIN_PRE)
print(f"\n  !! '1.3%' is precision theatre: the two differ by {_dd:+.6f} with a {_ss:.6f}")
print(f"     error bar -- {_ss / abs(a_pre):.0%} of the value being closed. The closure is")
print("     consistent with agreement AND with a 78% disagreement, equally.")
with open(OUT_SE, "w", newline="") as fh:
    w_ = csv.writer(fh)
    w_.writerow(["series", "window", "accel", "se_ols", "se_ar1", "accel_over_se"])
    for r in se_rows:
        w_.writerow([r[0], r[1]] + [f"{x:.9f}" for x in r[2:]])

# ===========================================================================
# [8] IS THE HALVING ITSELF SIGNIFICANT?
# ===========================================================================
print("\n" + "=" * 78 + "\n[8] SIGNIFICANCE OF THE HALVING\n" + "=" * 78)
print("  The two windows are NESTED, so their estimates are strongly correlated and the")
print("  [7] error bars cannot be differenced. NULL: ONE quadratic describes the whole")
print(f"  {WIN_POST[0]}-{WIN_POST[1]} span, plus AR(1) noise at the series' own fitted rho and")
print("  residual sd. Under it, accel(pre) - accel(post) has mean zero by construction;")
print("  the question is only whether the observed drop is in its tail.")


def halving_p(v, yrs, seed=SE_MC_SEED, n=SE_MC_N):
    i0 = np.where(yrs == WIN_POST[0])[0][0]
    i1 = np.where(yrs == WIN_POST[1])[0][0]
    x = (yrs[i0:i1 + 1] - WIN_POST[0]).astype(float)
    y = np.asarray(v[i0:i1 + 1], dtype=float)
    A = np.vstack([np.ones_like(x), x, x ** 2]).T
    r = y - A @ np.linalg.lstsq(A, y, rcond=None)[0]
    rho, sd, m = np.corrcoef(r[:-1], r[1:])[0, 1], r.std(ddof=3), len(x)
    k = WIN_PRE[1] - WIN_POST[0] + 1          # rows of the PRE sub-window
    Ppre = np.linalg.pinv(A[:k])[2]
    Ppost = np.linalg.pinv(A)[2]
    rng = np.random.default_rng(seed)
    e = np.empty((n, m))
    e[:, 0] = rng.standard_normal(n) * sd
    sh = rng.standard_normal((n, m)) * sd * np.sqrt(max(1 - rho ** 2, 0.0))
    for t in range(1, m):
        e[:, t] = rho * e[:, t - 1] + sh[:, t]
    null = 2.0 * (e[:, :k] @ Ppre - e @ Ppost)
    obs = accel_of(v, yrs, WIN_PRE) - accel_of(v, yrs, WIN_POST)
    return obs, float(null.std()), float((np.abs(null) >= abs(obs)).mean())


print(f"\n  {'series':34s} {'observed drop':>14s} {'null sd':>10s} {'sigma':>7s} {'p':>8s}")
for nm, v in (("sum5 (as shipped, LWS fiat-flat)", SER["sum5"]),
              ("sum4 (LWS removed entirely)", SER["sum4"]),
              (f"{TOTAL_COL} (independent, real data)", SER[TOTAL_COL])):
    ob, nsd, pv = halving_p(v, YRS)
    print(f"  {nm:34s} {ob:+14.6f} {nsd:10.6f} {ob / nsd:7.2f} {pv:8.4f}"
          f"  {'REAL' if pv < 0.05 else 'not resolved'}")
print("\n  Read with [1]: whatever share of the drop survives here is shared between the")
print("  fiat and the record, and only the LWS-free rows can speak to the record alone.")

for p in (OUT_DECOMP, OUT_ARMS, OUT_WINDOWS, OUT_RECON, OUT_SWEEP, OUT_SE):
    print(f"\nwrote {os.path.relpath(p, REPO)}")
