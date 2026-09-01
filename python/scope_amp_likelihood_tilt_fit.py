#!/usr/bin/env python3
"""Fit slope + curvature of the conditional ll(amp) profile, per law arm.

Laplace: with ll ~= ll0 + s*(a-mu) + c/2*(a-mu)^2 against a N(mu,sigma) prior,
    sd_post/sd_prior = 1/sqrt(1 - c*sigma^2)
    mean_post - mu   = s*sigma^2 / (1 - c*sigma^2)
A TILT (c ~ 0, s != 0) shifts the centre and leaves the width alone -- the signature
the handoff reports and cannot explain.
"""
import glob, os, re, numpy as np, pandas as pd

OUT = "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/outputs"
MU, SIG_L23, SIG_L24 = 1.09, 0.10, 0.180
LAW = {"R1.0_F1": "NEW  (R=1, floored)      = L23/L24 champion",
       "RInf_F1": "ratchet, floored         (law 2x2 cell)",
       "R1.0_F0": "regrowth, unfloored      (law 2x2 cell)",
       "RInf_F0": "OLD  (R=Inf, unfloored)  = L21/L22 shipped law"}

def fit(g, mu):
    """Weighted quadratic about mu, restricted to the +-2sigma core where the
    Laplace expansion is the relevant one (the prior has negligible mass beyond)."""
    x = g.amp.to_numpy() - mu
    y = g.ll.to_numpy()
    m = np.abs(x) <= 2 * SIG_L23
    if m.sum() < 5:
        m = np.ones(len(x), bool)
    p = np.polyfit(x[m], y[m], 2)          # p[0]*x^2 + p[1]*x + p[2]
    return p[1], 2 * p[0]                  # slope s, curvature c

rows = []
for f in sorted(glob.glob(f"{OUT}/scope_amp_likelihood_tilt_*.csv")):
    arm = re.search(r"tilt_(.+)\.csv", f).group(1)
    d = pd.read_csv(f)
    d = d[np.isfinite(d.ll)]
    for di, g in d.groupby("draw"):
        if len(g) < 5:
            continue
        s, c = fit(g, MU)
        rows.append(dict(arm=arm, draw=di, s=s, c=c))
r = pd.DataFrame(rows)
if r.empty:
    raise SystemExit("no profiles found")

print("=" * 104)
print("CONDITIONAL ll(amp) PROFILE — slope and curvature by law arm")
print("⚠ conditional at fixed theta, NOT marginal: magnitudes are an UPPER bound on identification.")
print("=" * 104)
hdr = f"{'law arm':42s} {'n':>3s} {'slope s':>12s} {'se':>8s} {'curv c':>10s} {'se':>8s}"
print("\n" + hdr)
for arm, g in r.groupby("arm"):
    n = len(g)
    ses = g.s.std(ddof=1) / np.sqrt(n); sec = g.c.std(ddof=1) / np.sqrt(n)
    print(f"{LAW.get(arm,arm):42s} {n:3d} {g.s.mean():+12.2f} {ses:8.2f} "
          f"{g.c.mean():+10.2f} {sec:8.2f}")

print(f"\n{'law arm':42s} {'predicted shift':>16s} {'predicted sd ratio':>20s}")
print(f"{'':42s} {'(prior sd units)':>16s} {'sd_post/sd_prior':>20s}")
for arm, g in r.groupby("arm"):
    s, c = g.s.mean(), g.c.mean()
    for sig, lab in ((SIG_L23, "sigma=0.10"),):
        den = 1 - c * sig**2
        shift = s * sig**2 / den
        print(f"{LAW.get(arm,arm)[:38]+' '+lab:42s} {shift/sig:+16.2f} {1/np.sqrt(den):20.3f}")

print("\nMEASURED, for comparison (handoff §2/§3):")
print("  L21 (old law) amp median 0.9455 => shift  (0.9455-1.09)/0.10 = -1.45 prior sd")
print("  L23 (new law) amp median 1.0865 => shift  (1.0865-1.09)/0.10 = -0.04 prior sd")
print("  posterior sd / prior sd = 0.97 (L21) / 0.99 (L23) / 0.95 (L24, sigma=0.180)")
