#!/usr/bin/env python3
"""
scope_greenland_bochow2026.py — the Bochow et al. 2026 Greenland tipping
emulator on our SSP paths, and the sampled-across-families ensemble design
(Marcus 2026-08-10: sample across all three model families, do not pick one).

RE-POINTED AT L10, 2026-08-14 (thread 5, first concrete step). This was written
against extC's stock-SIMPLE Greenland; the shipped model is now A+B on a regional
driver with the amp(GMST) law, which is far more scenario-responsive, so the
comparison is a different one and had to be redone rather than path-edited. The
Ladrillo column is now READ from outputs/ssps_components_2300_L10.csv (median
plus the posterior 5-95%) instead of being three hardcoded numbers.

SOURCE (verified 2026-08-10, fetched)
  Bochow, N., Kroenke, J., Garbe, J., Wunderling, N. (2026) "Informing low-order
  models of climate tipping elements using outputs from higher-complexity Earth
  system models", EGUsphere preprint, doi 10.5194/egusphere-2026-614.
  PREPRINT in open discussion — referees have raised concerns about uncertainty
  quantification, verification against transient runs, and the justification for
  the functional form; code availability is still a placeholder. Provisional.

THE MODEL (their Eq. 1 and Eq. 3)
    dz/dt = (1/tau(p)) * (a z^3 + c z + e + p),      z = x - x0
    tau(p) = k * (kappa / |p - pc|)^alpha,           kappa = 1 K
  x is standardised ice volume, p is GMT above pre-industrial in degC. The cubic
  gives a fold bifurcation: two stable branches, an unstable one between them,
  hence a threshold and hysteresis. tau diverges as the threshold is approached.
  This one form covers what options C and D were separately reaching for.

THREE MODEL FAMILIES, not four arms. Yelmo and PISM are each a single two-fold
system. SICOPOLIS is ONE model represented by TWO summed subsystems — per the
paper, "the sum of these two systems represents the ice volume of the whole
GrIS" — whose intermediate state is an ice-free southern Greenland with the
north still glaciated. Treating its two thresholds as independent arms (as an
earlier version of this script did) misrepresents that model.

ASSUMPTION, flagged. Table 2 gives no per-subsystem amplitude for SICOPOLIS, so
the split between its two subsystems is anchored on Hoening et al. 2024
(ERL 19:024038), which attributes ~1.8 m SLE to southern Greenland alone. The
first-threshold subsystem is therefore given 1.8 m of the 7.42 m total and the
second the remaining 5.62 m. Absolute metres for SICOPOLIS depend on that
choice; the threshold structure does not.

NORMALISATION. Table 2 withholds the mean and standard deviation used to
standardise ice volume, so the state cannot be inverted to metres directly.
Each cubic's own stable branches are used instead: the upper stable root at
p = 0 is mapped to zero loss and the deglaciated branch to that subsystem's
share of the ice sheet. Self-consistent, and needs no withheld constants.

  python3 python/scope_greenland_bochow2026.py [--nsample N]
Writes outputs/scope_greenland_bochow2026.csv (per-family) and
       outputs/scope_greenland_bochow2026_sampled.csv (the ensemble)
"""
import argparse
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBS = os.path.join(REPO, "data/observations")
OUT = os.path.join(REPO, "outputs/scope_greenland_bochow2026.csv")
OUT_SAMPLED = os.path.join(REPO, "outputs/scope_greenland_bochow2026_sampled.csv")

GRIS_SLE_M = 7.42                  # full-ice-sheet scale used by Bochow et al.
SOUTH_SLE_M = 1.80                 # Hoening 2024 southern-Greenland share
KAPPA_K = 1.0
TAU_K, TAU_ALPHA = 10500.0, 0.27   # Yelmo transient fit, inherited by all arms
SSPS = ["ssp126", "ssp245", "ssp585"]
LABEL = {"ssp126": "SSP1-2.6", "ssp245": "SSP2-4.5", "ssp585": "SSP5-8.5"}
YEARS = np.arange(1850, 2301)
IREF = (YEARS >= 1995) & (YEARS <= 2014)
HORIZONS = (2100, 2150, 2300)
SUBSTEPS = 12

# Each family is a list of (a, c, x0, e, pc, share_of_ice_sheet) subsystems.
FAMILIES = {
    "Yelmo":     [(-1.83, -2.14, -0.14, 0.89, 1.80, GRIS_SLE_M)],
    "PISM":      [(-1.17, -1.67, -0.13, 1.72, 2.27, GRIS_SLE_M)],
    "SICOPOLIS": [(-1.10, -1.24, -0.13, 0.62, 1.00, SOUTH_SLE_M),
                  (-0.80, -0.58, -0.02, 1.59, 1.99, GRIS_SLE_M - SOUTH_SLE_M)],
}
# Within-family threshold uncertainty. Bochow et al. 2023 quote 1.7-2.3 degC for
# PISM, i.e. a real within-model range, so a point value understates it.
PC_JITTER_K = 0.25
# Kypke et al. 2026 (ESD 17:769): post-threshold collapse timing is chaotic over
# 10^4-10^5 yr, so the single inherited k cannot be treated as known.
K_LOG10_JITTER = 0.5
SEED = 2026

# Ladrillo's own Greenland. READ, not hardcoded, and no longer the extC vintage:
# this compared against stock SIMPLE when it was written (2026-08-10), and the
# shipped model is now A+B with the amp(GMST) law. Re-pointed extC -> L10
# (2026-08-14) and L10 -> L11 (2026-08-17, when L11 became canonical); each time
# the live comparison is whatever vintage is accepted on the deliverable, which
# is why the extC quarantine README lists this script as "re-running against the
# current vintage is work, not a path edit". LADRILLO_TAG must move with the
# path — it labels every figure and table this script emits.
LADRILLO_SSP_CSV = os.path.join(REPO, "outputs/ssps_components_2300_L11.csv")
LADRILLO_TAG = "Ladrillo (L11, A+B + amp law)"
LADRILLO_COMPONENT = "gis"
SSP_LABEL_TO_KEY = {"SSP1-2.6": "ssp126", "SSP2-4.5": "ssp245", "SSP5-8.5": "ssp585"}


def ladrillo_gis(horizons):
    """{year: {ssp: (med, p05, p95)}} for Greenland, from the shipped posterior."""
    d = pd.read_csv(LADRILLO_SSP_CSV)
    d = d[d["component"] == LADRILLO_COMPONENT]
    out = {}
    for y in horizons:
        sub = d[d["year"] == y]
        if sub.empty:
            continue
        out[y] = {SSP_LABEL_TO_KEY[r.ssp]: (r.med, r.p05, r.p95)
                  for r in sub.itertuples() if r.ssp in SSP_LABEL_TO_KEY}
    if not out:
        raise SystemExit(f"no {LADRILLO_COMPONENT} rows at {horizons} in "
                         f"{os.path.basename(LADRILLO_SSP_CSV)}")
    return out


def stable_branches(a, c, e, p):
    r = np.roots([a, 0.0, c, e + p])
    return np.sort(r[np.abs(r.imag) < 1e-9].real)


def subsystem_map(a, c, e, share):
    """State -> metres for one subsystem, anchored on its own stable branches."""
    z_hi = stable_branches(a, c, e, 0.0).max()
    z_lo = stable_branches(a, c, e, 6.0).min()
    return (lambda z: (z_hi - z) / (z_hi - z_lo) * share), z_hi


def run_family(subsystems, gmst, pc_shift=0.0, k=TAU_K):
    """Total Greenland contribution, cm rel 1995-2014, summing all subsystems."""
    total = np.zeros(len(gmst))
    dt = 1.0 / SUBSTEPS
    for a, c, x0, e, pc, share in subsystems:
        to_m, z = subsystem_map(a, c, e, share)
        pc = pc + pc_shift
        series = np.empty(len(gmst))
        for i, p in enumerate(gmst):
            for _ in range(SUBSTEPS):
                tau = k * (KAPPA_K / max(abs(p - pc), 1e-3)) ** TAU_ALPHA
                z += dt * (a * z ** 3 + c * z + e + p) / tau
            series[i] = to_m(z)
        total += series
    return 100.0 * (total - total[IREF].mean())


def committed_loss(subsystems, p, pc_shift=0.0):
    """Equilibrium loss in m SLE at a sustained temperature p — the diagnostic
    the threshold actually governs, as opposed to realised 2300 sea level."""
    out = 0.0
    for a, c, x0, e, pc, share in subsystems:
        to_m, _ = subsystem_map(a, c, e, share)
        roots = stable_branches(a, c, e, p)
        # on a warming path the system tracks the UPPER branch until it vanishes
        out += to_m(roots.max())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nsample", type=int, default=600)
    args = ap.parse_args()

    gmst = {s: pd.read_csv(os.path.join(OBS, f"fair_mean_gmst_{s}.csv")
                           ).set_index("year")["gmst_C"].reindex(YEARS).to_numpy()
            for s in SSPS}
    peak = {s: float(np.nanmax(gmst[s])) for s in SSPS}

    print("Bochow et al. 2026 GrIS tipping emulator (PREPRINT, provisional)\n")
    print("  our peak GMT: " + ", ".join(f"{LABEL[s]} {peak[s]:.2f} C" for s in SSPS))
    print("\n  thresholds and which scenarios cross them")
    for fam, subs in FAMILIES.items():
        for (_, _, _, _, pc, share) in subs:
            crossed = [LABEL[s] for s in SSPS if peak[s] >= pc]
            print(f"    {fam:10s} pc {pc:.2f} C (share {share:.2f} m) -> "
                  f"{', '.join(crossed) if crossed else 'none'}")

    rows = []
    print(f"\n  PER FAMILY — Greenland, cm rel 1995-2014")
    print(f"  {'family':12s} {'year':>6s} " + "".join(f"{LABEL[s]:>11s}" for s in SSPS))
    for fam, subs in FAMILIES.items():
        series = {s: run_family(subs, gmst[s]) for s in SSPS}
        for y in HORIZONS:
            i = int(np.where(YEARS == y)[0][0])
            print(f"  {fam:12s} {y:6d} " + "".join(f"{series[s][i]:11.1f}" for s in SSPS))
            rows.append(dict(family=fam, year=y, **{LABEL[s]: series[s][i] for s in SSPS}))
    lad = ladrillo_gis(HORIZONS)
    print(f"\n  {LADRILLO_TAG} — median, and 5-95% of the posterior beneath it")
    for y in sorted(lad):
        print(f"  {'Ladrillo':12s} {y:6d} " +
              "".join(f"{lad[y][s][0]:11.1f}" for s in SSPS))
        print(f"  {'  5-95%':12s} {'':6s} " +
              "".join(f"{lad[y][s][1]:5.1f}-{lad[y][s][2]:<5.1f}" for s in SSPS))
        rows.append(dict(family=LADRILLO_TAG, year=y,
                         **{LABEL[s]: lad[y][s][0] for s in SSPS}))
    pd.DataFrame(rows).to_csv(OUT, index=False)

    # ---- the sampled ensemble: family + threshold + timescale ---------------
    print(f"\n  SAMPLED ACROSS FAMILIES ({args.nsample} draws): family drawn uniformly, "
          f"threshold jittered +/-{PC_JITTER_K} C,\n  timescale k jittered "
          f"{K_LOG10_JITTER} in log10 (Kypke et al. 2026: post-threshold timing is chaotic)")
    rng = np.random.default_rng(SEED)
    fams = list(FAMILIES)
    draws = []
    for _ in range(args.nsample):
        fam = fams[rng.integers(len(fams))]
        draws.append((fam, float(rng.normal(0.0, PC_JITTER_K)),
                      TAU_K * 10.0 ** float(rng.normal(0.0, K_LOG10_JITTER))))
    samp_rows = []
    print(f"\n  {'year':>6s} {'scenario':10s} {'median':>9s} {'5-95%':>18s}")
    for y in HORIZONS:
        i = int(np.where(YEARS == y)[0][0])
        for s in SSPS:
            vals = np.array([run_family(FAMILIES[f], gmst[s], d, k)[i]
                             for f, d, k in draws])
            q = np.percentile(vals, [5, 50, 95])
            print(f"  {y:6d} {LABEL[s]:10s} {q[1]:9.1f}  [{q[0]:7.1f},{q[2]:7.1f}]")
            samp_rows.append(dict(year=y, scenario=LABEL[s], med=q[1], p05=q[0], p95=q[2],
                                  n=len(vals)))
    pd.DataFrame(samp_rows).to_csv(OUT_SAMPLED, index=False)

    # ---- committed loss: where the threshold actually bites -----------------
    print("\n  COMMITTED LOSS at sustained warming (m SLE) — the diagnostic the")
    print("  threshold governs, unlike realised 2300 sea level")
    print(f"  {'GMT':>5s} " + "".join(f"{f:>12s}" for f in FAMILIES) + f"{'sampled p05-p95':>22s}")
    for p in (1.5, 1.92, 2.5, 3.19, 5.0):
        per = [committed_loss(FAMILIES[f], p) for f in FAMILIES]
        samp = np.array([committed_loss(FAMILIES[f], p, d) for f, d, _ in draws])
        q = np.percentile(samp, [5, 95])
        print(f"  {p:5.2f} " + "".join(f"{v:12.2f}" for v in per) +
              f"      [{q[0]:6.2f},{q[1]:6.2f}]")

    print(f"\nwrote {os.path.relpath(OUT, REPO)} and {os.path.relpath(OUT_SAMPLED, REPO)}")


if __name__ == "__main__":
    main()
