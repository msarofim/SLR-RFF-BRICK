"""Split the L11 posterior into its channel-ORDERED and channel-INVERTED halves.

Feeds the measurement that prices handoff-2026-08-16 section 7's open decision
(re-tune to impose the Greenland channel ordering, or ship L11 documented).
`diag_gis_ordering_in_l11_posterior.py` establishes that 37.5% of L11 draws
satisfy `alpha_s <= alpha_f AND beta_s <= beta_f`.  What that costs the
DELIVERABLE is not readable off a parameter share -- it has to be projected.

Design, and why it is a comparison rather than a single run:

  ORD  = the 37.5% that satisfy the ordering  -- what a re-tune would approximate
  INV  = the 62.5% that do not                -- what the constraint would remove

Comparing ORD to INV is the contrast the decision needs.  Running only ORD
against full L11 would confound the constraint with the fact that L11 is a
MIXTURE containing ORD, which damps any difference by construction.

Both halves are written at EXACTLY N_OUT rows so that
`project_ssps_components_ladrillo.jl` (which thins to NTHIN=2000) applies stride
1 to each and the two runs differ ONLY in which draws they contain -- not in
sample size or thinning stride.  Drawn without replacement under a fixed seed.

CONSISTENCY CHECK this buys for free: L11 is the mixture of the two halves, so
its already-published projection must lie BETWEEN ORD and INV at every horizon.
If it does not, the split or the projection wiring is wrong, not the physics.

  python python/split_l11_by_gis_ordering.py
  julia --project=julia_v2 julia/project_ssps_components_ladrillo.jl --tag=L11ord
  julia --project=julia_v2 julia/project_ssps_components_ladrillo.jl --tag=L11inv
"""
import os
import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTERIOR_CSV = os.path.join(
    REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_L11.csv")
OUT_ORD = os.path.join(
    REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_L11ord.csv")
OUT_INV = os.path.join(
    REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_L11inv.csv")
GIS_DRIVER_CSV = os.path.join(REPO, "data/observations/t_gis_zones.csv")
GIS_ZONE = "south"             # == ladrillo_projection.jl's LADRILLO_GIS_ZONE
TBAR_WIN = (2015, 2024)
TBAR_ASSERTED = 1.963
TBAR_TOL = 5e-3
N_OUT = 2000                   # == the driver's NTHIN, so its stride is 1
SEED = 2026


def load_tbar():
    t = pd.read_csv(GIS_DRIVER_CSV)
    if GIS_ZONE not in t.columns:
        raise SystemExit(f"zone column '{GIS_ZONE}' not in {list(t.columns)}")
    w = t[(t["year"] >= TBAR_WIN[0]) & (t["year"] <= TBAR_WIN[1])]
    tbar = float(w[GIS_ZONE].mean())
    if abs(tbar - TBAR_ASSERTED) >= TBAR_TOL:
        raise SystemExit(f"TBAR = {tbar:.4f} disagrees with the calibrator's "
                         f"asserted {TBAR_ASSERTED}")
    return tbar


def main():
    tbar = load_tbar()
    df = pd.read_csv(POSTERIOR_CSV)

    # the projection stack's own inverse map (ladrillo_native_greenland!)
    r_s = np.exp(df["gis_slow_ell"].to_numpy(float))
    w_s = df["gis_slow_w"].to_numpy(float)
    a_s, b_s = w_s * r_s / tbar, (1.0 - w_s) * r_s
    ordered = (a_s <= df["gis_alpha_f"].to_numpy(float)) & \
              (b_s <= df["gis_beta_f"].to_numpy(float))

    n_ord, n_inv = int(ordered.sum()), int((~ordered).sum())
    print(f"L11: {len(df)} draws -> ORD {n_ord} ({100*n_ord/len(df):.2f} %), "
          f"INV {n_inv} ({100*n_inv/len(df):.2f} %)")
    for label, n in (("ORD", n_ord), ("INV", n_inv)):
        if n < N_OUT:
            raise SystemExit(f"{label} has {n} draws < N_OUT={N_OUT}; the two "
                             f"halves could not be size-matched.")

    rng = np.random.default_rng(SEED)
    for label, mask, path in (("ORD", ordered, OUT_ORD),
                              ("INV", ~ordered, OUT_INV)):
        idx = np.flatnonzero(mask)
        pick = rng.choice(idx, size=N_OUT, replace=False)
        pick.sort()                       # keep the file in chain order
        df.iloc[pick].to_csv(path, index=False)
        print(f"  {label}: wrote {N_OUT} of {len(idx)} -> "
              f"{os.path.relpath(path, REPO)}")

    # Report the split's Greenland contrast, so the projection difference can be
    # read against the parameter difference that produced it.
    print("\n--- Greenland medians by half (native pair) ---")
    print(f"  {'':10s} {'alpha_f':>11s} {'alpha_s':>11s} {'beta_f':>11s} "
          f"{'beta_s':>11s} {'tau_f':>8s} {'tau_s':>8s}")
    for label, mask in (("ORD", ordered), ("INV", ~ordered)):
        af = df["gis_alpha_f"].to_numpy(float)[mask]
        bf = df["gis_beta_f"].to_numpy(float)[mask]
        aa, bb = a_s[mask], b_s[mask]
        tf, ts = 1.0/(af*tbar + bf), 1.0/(aa*tbar + bb)
        print(f"  {label:10s} {np.median(af):11.6g} {np.median(aa):11.6g} "
              f"{np.median(bf):11.6g} {np.median(bb):11.6g} "
              f"{np.median(tf):8.1f} {np.median(ts):8.1f}")


if __name__ == "__main__":
    main()
