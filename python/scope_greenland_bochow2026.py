#!/usr/bin/env python3
"""
scope_greenland_bochow2026.py — run the published Bochow et al. 2026 Greenland
tipping emulator on our SSP paths, and compare it with BRICK's Greenland.

SOURCE (verified 2026-08-10, fetched)
  Bochow, N., Kroenke, J., Garbe, J., Wunderling, N. (2026) "Informing low-order
  models of climate tipping elements using outputs from higher-complexity Earth
  system models", EGUsphere preprint, doi 10.5194/egusphere-2026-614.
  PREPRINT, in open discussion — referees have raised concerns about uncertainty
  quantification, verification against transient ESM runs, and the
  justification for the functional form. Treat as provisional.

THE MODEL (their Eq. 1 and Eq. 3)
    dz/dt = (1/tau(p)) * (a z^3 + c z + e + p),      z = x - x0
    tau(p) = k * (kappa / |p - pc|)^alpha,           kappa = 1 K
  x is the standardised ice volume, p is GMT above pre-industrial in degC. The
  cubic gives a fold (saddle-node) bifurcation: two stable branches separated by
  an unstable one, hence a threshold AND hysteresis. tau diverges as the
  threshold is approached, which is the physically-motivated version of the
  "how fast does it get there" question.

  This single form does what our options C and D were separately reaching for —
  a nonlinear equilibrium with a threshold (C), multistability from the
  melt-elevation feedback (D) — and adds a principled transient timescale.

FITTED PARAMETERS, their Table 2 (p in degC GMT above pre-industrial):
  model                    a       c      x0     e     k[yr]  alpha  p1     p2
  GrIS Yelmo             -1.83  -2.14  -0.14   0.89   10500   0.27   1.80   0.70
  GrIS PISM              -1.17  -1.67  -0.13   1.72       *      *   2.27   1.63
  GrIS SICOPOLIS 1st     -1.10  -1.24  -0.13   0.62       *      *   1.00   0.23
  GrIS SICOPOLIS 2nd     -0.80  -0.58  -0.02   1.59       *      *   1.99   0.23
  (* = inherited from the Yelmo timescale fit; p1 = forward threshold,
   p2 = reverse/regrowth threshold, i.e. the hysteresis edges.)

NORMALISATION. Table 2 does not give the mean and standard deviation used to
standardise ice volume, so the state cannot be inverted to metres directly.
Instead the cubic's own stable branches are used: at each p the upper stable
root is the glaciated branch and the lower stable root the deglaciated one, and
the state is mapped linearly so that the upper branch at p = 0 is zero loss and
the lower branch is the full GRIS_SLE_M. This is self-consistent and needs no
constants the paper withholds; absolute metres are therefore indicative.

  python3 python/scope_greenland_bochow2026.py
Writes outputs/scope_greenland_bochow2026.csv
"""
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBS = os.path.join(REPO, "data/observations")
OUT = os.path.join(REPO, "outputs/scope_greenland_bochow2026.csv")

GRIS_SLE_M = 7.42                  # the scale Bochow et al. use for a full GrIS
KAPPA_K = 1.0
TAU_K, TAU_ALPHA = 10500.0, 0.27   # Yelmo transient fit, inherited by all GrIS arms
SSPS = ["ssp126", "ssp245", "ssp585"]
LABEL = {"ssp126": "SSP1-2.6", "ssp245": "SSP2-4.5", "ssp585": "SSP5-8.5"}
YEARS = np.arange(1850, 2301)
IREF = (YEARS >= 1995) & (YEARS <= 2014)
HORIZONS = (2100, 2150, 2300)
SUBSTEPS = 12                      # sub-annual integration; the cubic is stiff near pc

# (a, c, x0, e, p_forward)
ARMS = {
    "Yelmo":            (-1.83, -2.14, -0.14, 0.89, 1.80),
    "PISM":             (-1.17, -1.67, -0.13, 1.72, 2.27),
    "SICOPOLIS 1st":    (-1.10, -1.24, -0.13, 0.62, 1.00),
    "SICOPOLIS 2nd":    (-0.80, -0.58, -0.02, 1.59, 1.99),
}
# BRICK-F*'s own Greenland, for reference (outputs/ssps_components_2300_extC.csv)
BRICKF_GIS = {2100: {"ssp126": 6.6, "ssp245": 7.3, "ssp585": 8.8},
              2300: {"ssp126": 19.2, "ssp245": 25.7, "ssp585": 48.6}}


def stable_branches(a, c, e, p):
    """Real roots of a z^3 + c z + e + p = 0, sorted. With a, c < 0 the outer
    roots are stable and the middle one unstable."""
    r = np.roots([a, 0.0, c, e + p])
    r = np.sort(r[np.abs(r.imag) < 1e-9].real)
    return r


def branch_map(a, c, e):
    """Linear map from state z to metres of sea-level contribution, anchored on
    the cubic's own branches: upper branch at p=0 -> 0 m, deglaciated -> full."""
    z_hi = stable_branches(a, c, e, 0.0).max()
    z_lo = stable_branches(a, c, e, 6.0).min()      # deep in the deglaciated regime
    return lambda z: (z_hi - z) / (z_hi - z_lo) * GRIS_SLE_M, z_hi


def run_arm(name, gmst):
    a, c, x0, e, pc = ARMS[name]
    to_m, z0 = branch_map(a, c, e)
    z = z0
    dt = 1.0 / SUBSTEPS
    out = np.empty(len(gmst))
    for i, p in enumerate(gmst):
        for _ in range(SUBSTEPS):
            tau = TAU_K * (KAPPA_K / max(abs(p - pc), 1e-3)) ** TAU_ALPHA
            z += dt * (a * z ** 3 + c * z + e + p) / tau
        out[i] = to_m(z)
    return 100.0 * (out - out[IREF].mean())          # cm, rel 1995-2014


def main():
    gmst = {s: pd.read_csv(os.path.join(OBS, f"fair_mean_gmst_{s}.csv")
                           ).set_index("year")["gmst_C"].reindex(YEARS).to_numpy()
            for s in SSPS}
    peak = {s: float(np.nanmax(gmst[s])) for s in SSPS}

    print("Bochow et al. 2026 GrIS tipping emulator on our SSP paths "
          "(PREPRINT, provisional)\n")
    print("  forward thresholds: " + ", ".join(
        f"{k} {v[4]:.2f} C" for k, v in ARMS.items()))
    print("  our peak GMT:       " + ", ".join(
        f"{LABEL[s]} {peak[s]:.2f} C" for s in SSPS))
    print("\n  Which scenarios cross which threshold?")
    for name, (_, _, _, _, pc) in ARMS.items():
        crossed = [LABEL[s] for s in SSPS if peak[s] >= pc]
        print(f"    {name:16s} pc = {pc:.2f} C  ->  crossed by: "
              f"{', '.join(crossed) if crossed else 'none'}")

    rows = []
    print(f"\n  Greenland contribution, cm rel 1995-2014")
    print(f"  {'arm':16s} {'year':>6s} " + "".join(f"{LABEL[s]:>11s}" for s in SSPS))
    for name in ARMS:
        series = {s: run_arm(name, gmst[s]) for s in SSPS}
        for y in HORIZONS:
            i = int(np.where(YEARS == y)[0][0])
            vals = [series[s][i] for s in SSPS]
            print(f"  {name:16s} {y:6d} " + "".join(f"{v:11.1f}" for v in vals))
            rows.append(dict(arm=name, year=y,
                             **{LABEL[s]: series[s][i] for s in SSPS}))
    for y in (2100, 2300):
        print(f"  {'BRICK-F* (ours)':16s} {y:6d} " +
              "".join(f"{BRICKF_GIS[y][s]:11.1f}" for s in SSPS))
        rows.append(dict(arm="BRICK-F* (ours)", year=y,
                         **{LABEL[s]: BRICKF_GIS[y][s] for s in SSPS}))

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"""
  READING THIS
  The arms disagree about WHERE the threshold is, not about whether there is
  one. Our SSP1-2.6 peaks at {peak['ssp126']:.2f} C, which sits between the Yelmo (1.80)
  and PISM (2.27) thresholds and far above SICOPOLIS's first (1.00). So the
  choice of arm decides whether BRICK-F* would say SSP1-2.6 commits Greenland.
  Absolute metres are indicative: the state normalisation is reconstructed from
  the cubic's own branches because Table 2 withholds the standardisation
  constants.""")
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
