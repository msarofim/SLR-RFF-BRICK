"""
diag_te_residual_onto_shape.py

THE TEST REGISTERED BY THE L22 RESULT (2026-08-29): is the TE modern residual
INVISIBLE TO THE D2 DISCREPANCY BASIS BY CONSTRUCTION?

WHY IT IS THE LIVE QUESTION. L22 capped the steric AR(1) marginal by 64% and the
2025 TE residual did not move (16.94 -> 17.79 sigma), while NOTHING else in the
fit moved either. So the misfit is not absorbable by the noise, is not fixed by
`thermal_alpha` (+0.20 of L21's own posterior sd), and is only partly reached by
D2 (+0.70 sd on d2_steric_1). The hypothesis that explains all of it at once:

    `D2_BASIS["steric"]` is Gram-Schmidt'd against [ones, S(t)], so ANY residual
    parallel to S(t) is orthogonal to every D2 column BY CONSTRUCTION. Only
    `thermal_alpha` scales S(t) -- and `thermal_alpha` is pinned by the early
    record, where eps is ~0.5 cm and the driver changed shape at the migration.

If that is right, the modern misfit is structurally unreachable: the one knob
shaped like it is held elsewhere, and the flexible term is blind to it.

⚠ THE BASIS USES A PLAIN INNER PRODUCT. `d2_basis` ACCEPTS a 1/eps^2 weight
vector and IGNORES it -- deliberately, and the source says so: weighting was
measured and made corr(d2_gsic_1, gic_delta) worse (0.161 -> 0.787). So the
orthogonality guarantee is in the PLAIN metric. The likelihood, however, scores
in a heteroskedastic AR(1) metric, so "what the basis cannot represent" and
"what the misfit costs" are different geometries. BOTH are reported; conflating
them is how one would talk oneself into the wrong conclusion here.

  source ~/climate-env/bin/activate && python python/diag_te_residual_onto_shape.py
"""
import os
import numpy as np
import pandas as pd

REPO      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS   = os.path.join(REPO, "outputs/recalib_targets_ext.csv")
OHC       = os.path.join(REPO, "data/observations/fair_mean_ohc_ssp245harm.csv")
OUT       = os.path.join(REPO, "outputs/diag_te_residual_onto_shape.csv")
ARMS      = ["L21", "L22"]
# posterior medians of the steric AR(1) pair, from each arm's own subsample
FITTED    = {"L21": (0.07093, 0.96781), "L22": (0.02992, 0.95298)}
D2_BASIS_N = 2          # calibrate_mcmc_ext.jl
EPS_FLOOR, EPS_Z = 0.05, 1.645
MODERN_Y0 = 1993


def d2_basis(years, protect):
    """Port of calibrate_mcmc_ext.jl's d2_basis: PLAIN inner product, x on
    [-1,1], protect set orthogonalised against itself first, then x^k
    Gram-Schmidt'd against it, each column scaled to unit RMS."""
    years = np.asarray(years, float)
    n = len(years)
    x = 2 * (years - years.min()) / (years.max() - years.min()) - 1
    base = []
    for u0 in protect:
        u = np.array(u0, float)
        for w in base:
            d = w @ w
            if d > 1e-12:
                u = u - (u @ w) / d * w
        if np.linalg.norm(u) > 1e-10:
            base.append(u)
    cols = []
    for k in range(1, D2_BASIS_N + len(protect) + 3):
        if len(cols) == D2_BASIS_N:
            break
        v = x ** k
        for u in base:
            d = u @ u
            if d > 1e-12:
                v = v - (v @ u) / d * u
        rms = np.sqrt((v ** 2).sum() / n)
        if rms < 1e-8:
            continue
        v = v / rms
        cols.append(v); base.append(v)
    assert len(cols) == D2_BASIS_N
    return np.column_stack(cols), base[:len(protect)]


def ar1_precision(eps, sigma, rho):
    """The likelihood's OWN metric: Sigma = sigma^2/(1-rho^2) * rho^|i-j| + diag(eps^2),
    exactly hetero_logl_ar1. A smooth persistent offset is CHEAP under this and
    expensive under diag(1/eps^2) -- which is why the diagonal is the wrong proxy."""
    n = len(eps)
    H = np.abs(np.subtract.outer(np.arange(n), np.arange(n)))
    Sig = (sigma ** 2 / (1 - rho ** 2)) * rho ** H + np.diag(eps ** 2)
    return np.linalg.inv(Sig)


def frac_in_full(r, cols, P):
    """Fraction of the residual's CHI-SQUARE removable by span(cols) under a full
    (non-diagonal) precision P."""
    A = cols if cols.ndim > 1 else cols[:, None]
    coef = np.linalg.solve(A.T @ P @ A, A.T @ P @ r)
    fit = A @ coef
    chi0 = r @ P @ r
    return float(chi0 - (r - fit) @ P @ (r - fit)) / float(chi0)


def frac_in(r, cols, W=None):
    """Fraction of ||r||^2 removable by the span of `cols`, in metric W (diag)."""
    if W is None:
        W = np.ones_like(r)
    A = cols * np.sqrt(W)[:, None]
    b = r * np.sqrt(W)
    coef, *_ = np.linalg.lstsq(A, b, rcond=None)
    fit = A @ coef
    return float(fit @ fit) / float(b @ b)


def main():
    tg = pd.read_csv(TARGETS).dropna(subset=["steric"])
    yrs = tg.year.astype(int).values
    eps = np.maximum((tg.steric_hi - tg.steric_lo).values / (2 * EPS_Z), EPS_FLOOR)
    ohc = pd.read_csv(OHC).set_index("year")["ohc_1e22J"]
    S = ohc.reindex(yrs).values                      # S(t) = TE_SHAPE
    ones = np.ones(len(yrs))
    D2, protect = d2_basis(yrs, [ones, S])
    Sperp = protect[1]                               # S(t) with the constant removed

    print(f"\n{'='*80}\nIS THE TE RESIDUAL INVISIBLE TO D2 BY CONSTRUCTION?")
    print(f"  steric window {yrs[0]}-{yrs[-1]}, n={len(yrs)}; D2 = {D2_BASIS_N} cols ⊥ [1, S(t)]"
          f"\n{'='*80}\n")
    # the construction check, mirroring the script's own load-time assertion
    for k in range(D2_BASIS_N):
        c = abs(D2[:, k] @ S) / (np.linalg.norm(D2[:, k]) * np.linalg.norm(S))
        print(f"  [CONSTRUCTION] |cos(D2 col {k+1}, S(t))| = {c:.2e}  "
              f"{'-> ORTHOGONAL' if c < 1e-8 else '⚠ NOT orthogonal'}")

    rows = []
    for arm in ARMS:
        p = os.path.join(REPO, f"outputs/postpred_{arm}_components_timeseries.csv")
        if not os.path.exists(p):
            print(f"\n  {arm}: missing {p}"); continue
        d = pd.read_csv(p).set_index("year")
        r = (d["te_p50"] - d["te_obs"]).reindex(yrs).values
        m = yrs >= MODERN_Y0
        print(f"\n  ── {arm} ──  residual RMS: full {np.sqrt((r**2).mean()):.4f} cm | "
              f"{MODERN_Y0}+ {np.sqrt((r[m]**2).mean()):.4f} cm")
        for lab, sel in (("full window", np.ones(len(yrs), bool)), (f"{MODERN_Y0}-{yrs[-1]}", m)):
            rr, SS, DD, ww = r[sel], Sperp[sel], D2[sel], 1.0 / eps[sel] ** 2
            fS_p = frac_in(rr, SS[:, None]); fD_p = frac_in(rr, DD)
            fS_w = frac_in(rr, SS[:, None], ww); fD_w = frac_in(rr, DD, ww)
            print(f"     {lab:>14}  along S(t): {100*fS_p:5.1f}% plain / {100*fS_w:5.1f}% ε-weighted"
                  f"   |  removable by D2: {100*fD_p:5.1f}% / {100*fD_w:5.1f}%")
            rows.append(dict(arm=arm, window=lab, frac_along_S_plain=fS_p,
                             frac_along_S_epsw=fS_w, frac_in_D2_plain=fD_p,
                             frac_in_D2_epsw=fD_w))
        # the metric the likelihood ACTUALLY uses, on the full window (the AR(1)
        # process is defined across the whole series; a sub-window slice of it is
        # not the same object, so this is reported full-window only)
        sg, rh = FITTED[arm]
        P = ar1_precision(eps, sg, rh)
        fS = frac_in_full(r, Sperp, P); fD = frac_in_full(r, D2, P)
        print(f"     {'AR(1) metric':>14}  along S(t): {100*fS:5.1f}%"
              f"   |  removable by D2: {100*fD:5.1f}%   (sigma={sg:.4f}, rho={rh:.4f})")
        rows.append(dict(arm=arm, window="full (AR1 metric)", frac_along_S_plain=np.nan,
                         frac_along_S_epsw=fS, frac_in_D2_plain=np.nan, frac_in_D2_epsw=fD))
    r = pd.DataFrame(rows)
    r.to_csv(OUT, index=False)
    print(f"\n  RESULT (2026-08-29): THE HYPOTHESIS IS REFUTED. D2 is orthogonal to S(t) over")
    print(f"  the FULL window (5e-17), but that does NOT make it orthogonal on a SUB-window:")
    print(f"  over 1993-2025 it can represent 95-98% of the residual. D2 is not blind to the")
    print(f"  modern misfit.")
    print(f"  BUT THE METRIC DECIDES. In the likelihood's OWN AR(1) precision the removable")
    print(f"  share is only 19.4% (L21) — a high rho makes a smooth persistent offset CHEAP to")
    print(f"  carry, so there is little gradient to remove it and the fit is not leaving free")
    print(f"  lunch on the table. Capping the noise raises it to 48.2% (L22), which is why")
    print(f"  d2_steric_1 moved +0.70 sd there. ⚠ Never read this decomposition in the")
    print(f"  eps-weighted diagonal: it says 98% where the real metric says 19%.")
    print(f"\n  OPEN: why L22 still declines the 48%.\n\n  wrote {OUT}\n")


if __name__ == "__main__":
    main()
