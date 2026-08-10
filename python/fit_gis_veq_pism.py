#!/usr/bin/env python3
"""
fit_gis_veq_pism.py — the Greenland equilibrium-volume curve V_eq(T) for
BRICK-F*, fitted directly to the PISM-dEBM equilibrium ladder.

DECISION 1 (Marcus, 2026-08-10): PISM-dEBM is the single implemented ladder.
No Yelmo sensitivity arm. Yelmo is carried here as an EVALUATION-ONLY overlay
so the threshold-location disagreement stays visible in the figure, exactly the
way ISMIP6 is evaluation-only for the transient.

WHY THIS EXISTS
    Stock SIMPLE uses V_eq = a*T + b, linear, which gives only 152 cm of
    committed loss at +5 C -- 21% of the ice sheet. The ladder says 98% is
    committed at +5 C. The linear form is a real defect of the 2300 and
    pulse-experiment results (scoping §10 option C). It is NOT what closes the
    2100 gap; the transient is (option B).

    This replaces the retracted Bochow-2026 cubic emulator entirely. That
    emulator was implemented from the preprint's Table 2, and the transcribed
    coefficients (a = -1.83, c = -2.14, both negative) make the cubic strictly
    monotonic -- no fold at all, contradicting the paper's own premise. The
    ladder is raw model output and needs no transcription, so we fit it directly.

FRAME -- deliberately GMT, not the regional driver
    The ladder's native axis is GMT = dT_summer/1.19 + 0.5 (the authors' own
    conversion; dT_summer is REGIONAL SUMMER warming, not global -- the trap
    noted in the handoff). GMT here is relative to preindustrial, so it lines
    up with BRICK's 1850-1900 frame.

    V_eq is fitted and stored as a function of GMT. The regional driver
    (data/observations/t_gis_zones.csv) drives the TRANSIENT; the equilibrium
    is a function of the large-scale state. Keeping V_eq in GMT means this file
    does not depend on the amplification prior, which is still an open choice.
    If the calibrator later wants V_eq in the regional frame, convert the rungs
    there -- do not refit here.

FORMS COMPARED
    linear      V0 - a*T - b            stock SIMPLE, the incumbent
    saturating  V0 - a*(1-exp(-b*(T-T_off)))   the glacier-reservoir form (§10)
    logistic2   two logistic steps      an intermediate state plus a collapse
    pchip       monotone interpolant through the rungs -- the non-parametric
                reference. Per the standing rule that real data beats a
                parametric approximation, pchip is the ACCEPTANCE TARGET: a
                parametric form earns its place only by coming close to it.
    pchip_shift pchip(T - dT), i.e. the ladder's exact shape with the threshold
                LOCATION as a single sampled parameter. This is what the
                calibrator should use. It keeps every rung exactly, has no
                low-warming bias, and makes the one genuinely uncertain
                quantity -- where the collapse sits -- the thing that is
                sampled. dT is reported here at 0 (the PISM fit); the prior
                width belongs in the calibrator, informed by how far Yelmo's
                threshold sits from PISM's.

WEIGHTING -- not a detail
    The ladder spans 0.05 to 7.4 m, two orders of magnitude. Unweighted least
    squares in metres is decided almost entirely by the top of the range, and
    the resulting logistic2 is 4x too high at GMT 0.5 and 2x too high at 0.92 --
    which is exactly where the HINDCAST operates (present GMT ~1.25). A V_eq
    that overstates committed loss at the historical operating point biases the
    transient fit, and the calibrator would absorb it by slowing the response:
    the very pathology this work exists to remove. Both weightings are therefore
    fitted and reported, and the relative one is the headline.

UNRESOLVED BY CONSTRUCTION
    The rungs are uniformly spaced at 0.4202 K in GMT. The collapse happens
    between two adjacent rungs (2.18 -> 2.60), so the sweep cannot resolve how
    sharp it is. Fitting w2 freely rails it at the lower bound. It is bounded
    below at the rung spacing here, and flagged: the sharpness is a prior, not
    a measurement.

  python3 python/fit_gis_veq_pism.py
Writes:
  outputs/gis_veq_pism_fit.csv        fitted coefficients + per-form RMSE
  outputs/gis_veq_pism_curve.csv      the fitted curves on a dense GMT grid
  figures/gis_veq_pism_fit.png
"""
import os
import subprocess

import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator
from scipy.optimize import least_squares

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LADDER_CSV = os.path.join(REPO, "data/observations/greenland_equilibrium_bochow2023.csv")
OUT_FIT = os.path.join(REPO, "outputs/gis_veq_pism_fit.csv")
OUT_CURVE = os.path.join(REPO, "outputs/gis_veq_pism_curve.csv")
OUT_FIG = os.path.join(REPO, "figures/gis_veq_pism_fit.png")

LADDER_MODEL = "PISM-dEBM"          # decision 1
EVAL_ONLY_MODEL = "Yelmo-REMBO"     # shown, never fitted
V0_M = 7.42                         # m SLE, total Greenland volume; both ladders agree
GMT_GRID = np.arange(0.0, 8.001, 0.01)
# Scenario peaks the fit has to be sensible across (handoff): SSP1-2.6 1.92,
# SSP2-4.5 3.19, SSP5-8.5 7.81 C.
SCENARIO_PEAKS = {"SSP1-2.6": 1.92, "SSP2-4.5": 3.19, "SSP5-8.5": 7.81}
# Reporting levels for the committed-loss table.
REPORT_LEVELS = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
FIT_SEED = 2026
N_MULTISTART = 200
# The ladder is uniformly spaced at this in GMT; nothing sharper is resolvable,
# so it is the lower bound on any step-width parameter (asserted at run time).
RUNG_SPACING_K = 0.4202
# Equilibrium at preindustrial is zero loss by definition. The lowest rung is
# GMT 0.50, so the interpolant needs this anchor or it extrapolates a straight
# line off the bottom of the ladder.
PI_ANCHOR = (0.0, 0.0)
# Residual weighting. "relative" divides by max(y, REL_FLOOR_M) so the
# low-warming rungs -- where the hindcast lives -- are not swamped.
REL_FLOOR_M = 0.05
WEIGHTING_HEADLINE = "relative"

COMMIT = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True).stdout.strip()
_rng = np.random.default_rng(FIT_SEED)


# =============================================================================
# forms -- all return COMMITTED LOSS in m SLE as a function of GMT
# =============================================================================
def f_linear(T, p):
    a, b = p
    return np.clip(a * T + b, 0.0, V0_M)


def f_saturating(T, p):
    a, b, T_off = p
    return np.clip(a * (1.0 - np.exp(-b * (T - T_off))), 0.0, V0_M)


def _logistic(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -700, 700)))


def f_logistic2(T, p):
    """Two steps: an intermediate state of size f1*V0 opening at T1, then the
    collapse to near-total loss at T2. Sharpness w1, w2 in C."""
    f1, T1, w1, T2, w2 = p
    return V0_M * (f1 * _logistic((T - T1) / w1) + (1.0 - f1) * _logistic((T - T2) / w2))


FORMS = {
    "linear": dict(fn=f_linear, p0=[1.5, -1.0],
                   lo=[0.0, -10.0], hi=[10.0, 10.0],
                   names=["a", "b"]),
    "saturating": dict(fn=f_saturating, p0=[7.4, 0.5, 0.3],
                       lo=[1.0, 0.01, -5.0], hi=[20.0, 10.0, 3.0],
                       names=["a", "b", "T_off"]),
    # w1/w2 bounded below at the rung spacing: nothing sharper is resolvable.
    "logistic2": dict(fn=f_logistic2, p0=[0.22, 1.6, 0.60, 2.4, 0.45],
                      lo=[0.02, 0.0, RUNG_SPACING_K, 0.5, RUNG_SPACING_K],
                      hi=[0.90, 4.0, 3.00, 7.0, 3.00],
                      names=["f1", "T1", "w1", "T2", "w2"]),
}


def weights_for(y, weighting):
    if weighting == "absolute":
        return np.ones_like(y)
    if weighting == "relative":
        return 1.0 / np.maximum(y, REL_FLOOR_M)
    raise ValueError(weighting)


def fit_form(name, T, y, weighting):
    """Multi-start bounded least squares. Seeded, so the fit is reproducible --
    the glacier module's RNG-order wart is not repeated here."""
    spec = FORMS[name]
    lo, hi = np.array(spec["lo"], float), np.array(spec["hi"], float)
    w = weights_for(y, weighting)
    best = None
    starts = [np.array(spec["p0"], float)]
    for _ in range(N_MULTISTART):
        starts.append(lo + _rng.random(len(lo)) * (hi - lo))
    for p0 in starts:
        try:
            r = least_squares(lambda p: (spec["fn"](T, p) - y) * w,
                              np.clip(p0, lo, hi), bounds=(lo, hi),
                              max_nfev=20000)
        except Exception:
            continue
        if best is None or r.cost < best.cost:
            best = r
    return best


def railed(name, p):
    """Parameters sitting on a bound -- the fit wanted to leave the feasible set."""
    lo, hi = np.array(FORMS[name]["lo"]), np.array(FORMS[name]["hi"])
    tol = 1e-6 * np.maximum(1.0, np.abs(hi - lo))
    return [n for n, v, l, h, t in zip(FORMS[name]["names"], p, lo, hi, tol)
            if abs(v - l) < t or abs(v - h) < t]


def rmse(pred, y, w=None):
    r = pred - y
    if w is not None:
        r = r * w
    return float(np.sqrt(np.mean(r ** 2)))


def main():
    lad = pd.read_csv(LADDER_CSV)
    pism = lad[lad.model == LADDER_MODEL].sort_values("gmt_K").reset_index(drop=True)
    yelmo = lad[lad.model == EVAL_ONLY_MODEL].sort_values("gmt_K").reset_index(drop=True)
    T, y = pism["gmt_K"].to_numpy(), pism["loss_m_sle"].to_numpy()

    # Guard the ladder before fitting anything to it (handoff: validate first).
    assert len(T) == 16, f"expected 16 PISM rungs, got {len(T)}"
    assert np.all(np.diff(T) > 0), "PISM rungs not sorted in GMT"
    assert abs(y[-1] / pism["loss_frac_of_volume"].iloc[-1] - V0_M) < 0.01, \
        "V0 implied by the ladder disagrees with V0_M"
    assert pism["drift_over_window_m"].abs().max() < 0.20, "a PISM rung has not converged"
    assert abs(float(np.diff(T).mean()) - RUNG_SPACING_K) < 1e-3 and \
        np.allclose(np.diff(T), np.diff(T)[0]), \
        "rung spacing is not the uniform RUNG_SPACING_K the width bounds assume"

    # Anchored at preindustrial: zero warming, zero committed loss.
    Ta = np.concatenate(([PI_ANCHOR[0]], T))
    ya = np.concatenate(([PI_ANCHOR[1]], y))
    pch = PchipInterpolator(Ta, ya, extrapolate=True)

    def pchip_on(grid, dT=0.0):
        return np.clip(pch(np.asarray(grid, float) - dT), 0.0, V0_M)

    rows, curves = [], {"gmt_K": GMT_GRID}
    curves["pchip"] = pchip_on(GMT_GRID)
    wrel = weights_for(y, "relative")
    for weighting in ("absolute", "relative"):
        w = weights_for(y, weighting)
        rows.append(dict(weighting=weighting, form="pchip", n_par=len(Ta),
                         rmse_m=rmse(pchip_on(T), y),
                         rmse_rel=rmse(pchip_on(T), y, wrel),
                         railed="", params=f"anchored at {PI_ANCHOR}"))
        for name in FORMS:
            r = fit_form(name, T, y, weighting)
            pred = FORMS[name]["fn"](T, r.x)
            if weighting == WEIGHTING_HEADLINE:
                curves[name] = FORMS[name]["fn"](GMT_GRID, r.x)
            rows.append(dict(
                weighting=weighting, form=name, n_par=len(r.x),
                rmse_m=rmse(pred, y), rmse_rel=rmse(pred, y, wrel),
                railed="|".join(railed(name, r.x)),
                params="; ".join(f"{n}={v:.6g}"
                                 for n, v in zip(FORMS[name]["names"], r.x))))
    fit = pd.DataFrame(rows)
    fit.to_csv(OUT_FIT, index=False)
    pd.DataFrame(curves).to_csv(OUT_CURVE, index=False, float_format="%.9g")

    shown = ["pchip"] + list(FORMS)

    # ---- report -----------------------------------------------------------
    print(f"FIT to the {LADDER_MODEL} ladder, {len(T)} rungs, "
          f"GMT {T.min():.2f}-{T.max():.2f} C at {RUNG_SPACING_K} K spacing, "
          f"V0 = {V0_M} m SLE")
    print(f"pchip anchored at {PI_ANCHOR}; headline weighting = "
          f"'{WEIGHTING_HEADLINE}'\n")
    for weighting in ("absolute", "relative"):
        print(f"  --- weighting: {weighting} "
              f"{'(headline)' if weighting == WEIGHTING_HEADLINE else ''}")
        print(f"  {'form':12s} {'n_par':>5s} {'RMSE m':>8s} {'RMSE rel':>9s} "
              f"{'railed':>8s}   parameters")
        for _, r in fit[fit.weighting == weighting].iterrows():
            print(f"  {r.form:12s} {r.n_par:5d} {r.rmse_m:8.3f} {r.rmse_rel:9.3f} "
                  f"{r.railed or '-':>8s}   {r.params}")
        print()

    print(f"COMMITTED LOSS, m SLE ({WEIGHTING_HEADLINE}-weighted fits)")
    print(f"  {'GMT':>5s} {'ladder':>8s} " + "".join(f"{f:>12s}" for f in shown))
    for lev in REPORT_LEVELS:
        print(f"  {lev:5.1f} {np.interp(lev, Ta, ya):8.2f} " +
              "".join(f"{np.interp(lev, GMT_GRID, curves[f]):12.2f}" for f in shown))

    print(f"\nLOW-WARMING REGIME -- where the hindcast operates (present GMT ~1.25)")
    print(f"  {'GMT':>5s} {'ladder':>8s} " + "".join(f"{f:>12s}" for f in shown))
    for lev in T[:5]:
        print(f"  {lev:5.2f} {np.interp(lev, Ta, ya):8.3f} " +
              "".join(f"{np.interp(lev, GMT_GRID, curves[f]):12.3f}" for f in shown))

    print(f"\nAT THE SCENARIO PEAKS")
    print(f"  {'scenario':10s} {'GMT':>5s} {'ladder':>8s} " +
          "".join(f"{f:>12s}" for f in shown) + f"{'Yelmo(eval)':>13s}")
    for sc, lev in SCENARIO_PEAKS.items():
        ye = np.interp(lev, yelmo["gmt_K"], yelmo["loss_m_sle"])
        print(f"  {sc:10s} {lev:5.2f} {np.interp(lev, Ta, ya):8.2f} " +
              "".join(f"{np.interp(lev, GMT_GRID, curves[f]):12.2f}" for f in shown) +
              f"{ye:13.2f}")

    print(f"\nTHRESHOLD-SHIFT SENSITIVITY -- pchip(T - dT), committed loss m SLE")
    print(f"  the one parameter the calibrator should sample. Yelmo's collapse sits "
          f"~0.7 K below PISM's,\n  which is the scale the dT prior has to cover.")
    print(f"  {'dT':>6s} " + "".join(f"{sc:>12s}" for sc in SCENARIO_PEAKS))
    for dT in (-0.8, -0.4, 0.0, 0.4, 0.8):
        print(f"  {dT:+6.1f} " +
              "".join(f"{pchip_on([lev], dT)[0]:12.2f}"
                      for lev in SCENARIO_PEAKS.values()))

    make_figure(pism, yelmo, curves, pchip_on)
    for p in (OUT_FIT, OUT_CURVE, OUT_FIG):
        print(f"wrote {os.path.relpath(p, REPO)}")


def make_figure(pism, yelmo, curves, pchip_on):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(17, 5.2))
    for ax, (x0, x1) in zip(axes[:2], [(0.0, 7.0), (0.5, 3.5)]):
        ax.plot(yelmo["gmt_K"], yelmo["loss_m_sle"], "s--", color="0.6", ms=5,
                lw=1.0, label=f"{EVAL_ONLY_MODEL} (evaluation only)")
        for f, c in zip(["pchip"] + list(FORMS), ["C2", "C3", "C1", "C0"]):
            ax.plot(curves["gmt_K"], curves[f], lw=2.0 if f == "pchip" else 1.6,
                    ls="-" if f in ("pchip", "logistic2") else "--", color=c, label=f)
        ax.plot(pism["gmt_K"], pism["loss_m_sle"], "ko", ms=6, zorder=5,
                label=f"{LADDER_MODEL} rungs (fitted)")
        for sc, lev in SCENARIO_PEAKS.items():
            if x0 <= lev <= x1:
                ax.axvline(lev, color="0.8", lw=1.0, zorder=0)
                ax.text(lev, V0_M * 0.02, f" {sc}", rotation=90, fontsize=7,
                        color="0.4", va="bottom")
        ax.axhline(V0_M, color="k", lw=0.6, ls=":")
        ax.set_xlim(x0, x1)
        ax.set_xlabel("GMT above preindustrial, C")
        ax.set_ylabel("committed loss, m SLE")
        ax.grid(alpha=0.3)
    axes[0].set_ylim(-0.2, V0_M + 0.4)
    axes[1].set_ylim(-0.1, 7.2)
    axes[0].set_title(f"Greenland equilibrium ladder, V0 = {V0_M} m SLE\n"
                      f"fitted to {LADDER_MODEL} ({WEIGHTING_HEADLINE} weighting)")
    axes[1].set_title("the threshold window, zoomed")
    axes[0].legend(fontsize=8, loc="lower right")

    ax = axes[2]
    for dT, c in zip((-0.8, -0.4, 0.0, 0.4, 0.8), ["C3", "C1", "k", "C0", "C4"]):
        ax.plot(curves["gmt_K"], pchip_on(curves["gmt_K"], dT),
                lw=2.2 if dT == 0 else 1.4, color=c,
                label=f"dT = {dT:+.1f}" + ("  (PISM)" if dT == 0 else ""))
    ax.plot(yelmo["gmt_K"], yelmo["loss_m_sle"], "s--", color="0.6", ms=4, lw=1.0,
            label=f"{EVAL_ONLY_MODEL} (evaluation only)")
    for sc, lev in SCENARIO_PEAKS.items():
        if lev <= 4.0:
            ax.axvline(lev, color="0.85", lw=1.0, zorder=0)
            ax.text(lev, 0.15, f" {sc}", rotation=90, fontsize=7, color="0.4")
    ax.set_xlim(0.0, 4.0)
    ax.set_ylim(-0.1, V0_M + 0.4)
    ax.set_xlabel("GMT above preindustrial, C")
    ax.set_ylabel("committed loss, m SLE")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="lower right")
    ax.set_title("pchip_shift: the threshold location as the\nsampled parameter "
                 "(the form the calibrator should use)")
    fig.tight_layout()
    fig.savefig(OUT_FIG, dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    main()
