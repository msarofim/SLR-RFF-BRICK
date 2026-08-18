"""Is the channel-ordering constraint already satisfied by the SHIPPED L11 posterior?

Handoff 2026-08-16 thread-5 §5 priced the channel inversion on the OFFLINE A+B
optimum: imposing `alpha_s <= alpha_f` AND `beta_s <= beta_f` costs 0.067 nlp
there.  §7 then asks whether to buy a re-tune + 4x2M + re-acceptance (~5 h) to
carry that constraint into the deliverable.

That question is premature until we know what the constraint would DO.  The
offline test is a single MAP point; the deliverable is a 55-column posterior
SAMPLE.  Three outcomes, with very different prices:

  (a) most draws already ordered   -> the re-tune buys a cosmetic tail trim;
                                      a REJECTION FILTER on the existing
                                      posterior is the cheap equivalent.
  (b) ~half ordered                -> the constraint is a real prior, and the
                                      filter is defensible but lossy.
  (c) ~none ordered                -> a filter would destroy the sample, and
                                      only a re-tune can impose it.

L11 carries the slow channel in the REPARAMETERISED (ell, w) coordinates, so
the native pair must be reconstructed with the projection stack's own inverse
map (`ladrillo_native_greenland!`, ladrillo_projection.jl):

    r_s = exp(ell);  alpha_s = w * r_s / TBAR;  beta_s = (1 - w) * r_s

TBAR is recomputed here from the same driver/window the Julia side uses, so the
two cannot drift apart silently -- the same discipline ladrillo_projection.jl
applies to its own copy.

Reports, additionally, the ordering as a WEDGE in (ell, w): the constraint is
NOT a box in the sampled coordinates, which is why it cannot be imposed by
moving `lo`/`hi` and would need a -Inf region in the log-prior.
"""
import os
import sys
import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Vintage under test. Defaults to L11 (the vintage this diagnostic was written
# against); pass a tag to re-check a later one -- e.g. L12, where the ordering
# share is a WIRING check that must read exactly 100 %.
TAG = next((a.split("=", 1)[1] for a in sys.argv[1:]
            if a.startswith("--tag=")), "L11")
POSTERIOR_CSV = os.path.join(
    REPO, f"data/MimiBRICK/parameters_subsample_brick_mengel_{TAG}.csv")
GIS_DRIVER_CSV = os.path.join(REPO, "data/observations/t_gis_zones.csv")
GIS_ZONE = "south"            # == ladrillo_projection.jl's LADRILLO_GIS_ZONE
TBAR_WIN = (2015, 2024)
TBAR_ASSERTED = 1.963          # the calibrator's own assertion
TBAR_TOL = 5e-3
# Output paths carry the TAG, so re-running on a later vintage cannot silently
# overwrite the L11 measurement the L12 decision was based on.
_SUF = "" if TAG == "L11" else f"_{TAG}"
OUT_CSV = os.path.join(
    REPO, f"outputs/diag_gis_ordering_in_l11_posterior{_SUF}.csv")
OUT_TSWEEP_CSV = os.path.join(
    REPO, f"outputs/diag_gis_ordering_in_l11_posterior{_SUF}_tsweep.csv")
# Regional (south-zone) temperature range the projections visit. The zone runs
# ~GIS_AMP x GMST, GIS_AMP ~ 1.92, and L11's SSP peak GMSTs are 1.92 / 3.19 /
# 7.81 K (handoff 2026-08-16 thread-5 section 2) -> ~3.7 / 6.1 / 15 K regional.
# TBAR = 1.963 K is the MODERN value and anchors the low end.
T_SWEEP_K = [0.0, 1.0, 1.963, 3.0, 5.0, 8.0, 12.0, 15.0]


def load_tbar():
    """The regional-driver mean over TBAR_WIN, recomputed rather than hardcoded."""
    t = pd.read_csv(GIS_DRIVER_CSV)
    if GIS_ZONE not in t.columns:
        raise SystemExit(f"zone column '{GIS_ZONE}' not in {list(t.columns)}")
    col = GIS_ZONE
    w = t[(t["year"] >= TBAR_WIN[0]) & (t["year"] <= TBAR_WIN[1])]
    tbar = float(w[col].mean())
    if abs(tbar - TBAR_ASSERTED) >= TBAR_TOL:
        raise SystemExit(
            f"TBAR = {tbar:.4f} from {TBAR_WIN} on column '{col}' disagrees with "
            f"the calibrator's asserted {TBAR_ASSERTED} -- the (ell,w) inverse map "
            f"below would be wrong by exactly that ratio.")
    return tbar, col


def native_slow(df, tbar):
    r_s = np.exp(df["gis_slow_ell"].to_numpy(float))
    w_s = df["gis_slow_w"].to_numpy(float)
    return w_s * r_s / tbar, (1.0 - w_s) * r_s


def main():
    tbar, col = load_tbar()
    df = pd.read_csv(POSTERIOR_CSV)
    n = len(df)
    print(f"posterior : {os.path.basename(POSTERIOR_CSV)}  ({n} draws)")
    print(f"TBAR      : {tbar:.4f} K  ({TBAR_WIN[0]}-{TBAR_WIN[1]} mean of "
          f"'{col}', matches the calibrator's {TBAR_ASSERTED})")

    a_s, b_s = native_slow(df, tbar)
    a_f = df["gis_alpha_f"].to_numpy(float)
    b_f = df["gis_beta_f"].to_numpy(float)

    ok_a = a_s <= a_f
    ok_b = b_s <= b_f
    ok_both = ok_a & ok_b

    print("\n--- ordering shares in the SHIPPED posterior ---")
    for label, m in (("alpha_s <= alpha_f", ok_a),
                     ("beta_s  <= beta_f ", ok_b),
                     ("BOTH (the constraint)", ok_both)):
        print(f"  {label:24s} {m.sum():7d} / {n}   = {100*m.mean():6.2f} %")

    print("\n--- native slow/fast marginals (median [p5, p95]) ---")
    for label, v in (("alpha_f", a_f), ("alpha_s", a_s),
                     ("beta_f", b_f), ("beta_s", b_s)):
        q = np.percentile(v, [5, 50, 95])
        print(f"  {label:8s} {q[1]:12.6g}  [{q[0]:.6g}, {q[2]:.6g}]")

    # The timescale defect the ordering was meant to repair: tau = 1/(alpha*T+beta).
    # Evaluated at the modern regional TBAR, which is where the hindcast lives.
    tau_f = 1.0 / (a_f * tbar + b_f)
    tau_s = 1.0 / (a_s * tbar + b_s)
    print(f"\n--- tau at T_regional = TBAR = {tbar:.3f} K (yr) ---")
    for label, v in (("tau_fast", tau_f), ("tau_slow", tau_s)):
        q = np.percentile(v, [5, 50, 95])
        print(f"  {label:9s} {q[1]:12.6g}  [{q[0]:.6g}, {q[2]:.6g}]")
    print(f"  tau_slow > tau_fast in {100*np.mean(tau_s > tau_f):.2f} % of draws")

    # WHY THE TWO NUMBERS DIFFER, and which one the deliverable actually needs.
    #
    # The pairwise constraint (alpha_s<=alpha_f AND beta_s<=beta_f) is SUFFICIENT
    # for tau_slow >= tau_fast at every T >= 0, but it is not NECESSARY at any
    # particular T: a draw with alpha_s > alpha_f can still be correctly ordered
    # below its crossover.  So the pairwise share is a LOWER BOUND on the share
    # that is physically well-ordered wherever the projections live.  Sweeping T
    # separates "the deliverable has an inversion problem" from "the offline MAP
    # had one" -- and locates the crossover if there is one.
    print("\n--- tau ordering vs regional T (the projection range) ---")
    print("  T_south (K)   tau_slow > tau_fast     median tau_fast   median tau_slow")
    rows_T = []
    for T in T_SWEEP_K:
        tf = 1.0 / (a_f * T + b_f)
        ts = 1.0 / (a_s * T + b_s)
        share = float(np.mean(ts > tf))
        print(f"  {T:9.2f}     {100*share:8.2f} %          "
              f"{np.median(tf):10.1f}       {np.median(ts):10.1f}")
        rows_T.append(dict(T_south_K=T, frac_tau_ordered=share,
                           median_tau_fast_yr=float(np.median(tf)),
                           median_tau_slow_yr=float(np.median(ts))))
    pd.DataFrame(rows_T).to_csv(OUT_TSWEEP_CSV, index=False)

    # The defect the ordering was meant to repair (handoff 2026-08-16 §5):
    # "nothing exceeds ~221 yr".  Check it against the posterior rather than the
    # MAP -- a long-timescale reservoir present in the sample needs no repair.
    tau_max = np.maximum(tau_f, tau_s)
    print(f"\n--- the '~221 yr' reservoir defect, checked on the SAMPLE ---")
    for thr in (221.0, 500.0, 1000.0):
        print(f"  draws with max(tau_fast, tau_slow) > {thr:6.0f} yr : "
              f"{100*np.mean(tau_max > thr):6.2f} %")
    print(f"  max(tau) p50/p95/p99 = {np.percentile(tau_max,50):.1f} / "
          f"{np.percentile(tau_max,95):.1f} / {np.percentile(tau_max,99):.1f} yr")

    # The wedge: the constraint in the SAMPLED coordinates. Both bounds are
    # joint in (ell, w) -- neither is a per-parameter box, which is the reason a
    # bound change cannot express it.
    ell = df["gis_slow_ell"].to_numpy(float)
    w = df["gis_slow_w"].to_numpy(float)
    print("\n--- the constraint as a WEDGE in the sampled (ell, w) ---")
    print("  alpha_s <= alpha_f  <=>  w * exp(ell)     <= alpha_f * TBAR")
    print("  beta_s  <= beta_f   <=>  (1-w) * exp(ell) <= beta_f")
    print("  => joint in (ell, w) AND coupled to alpha_f/beta_f: NOT a box,")
    print("     so it needs a -Inf region in the log-prior, not new lo/hi.")
    print(f"  ell : median {np.median(ell):.4f}  [{np.percentile(ell,5):.4f}, "
          f"{np.percentile(ell,95):.4f}]")
    print(f"  w   : median {np.median(w):.4f}  [{np.percentile(w,5):.4f}, "
          f"{np.percentile(w,95):.4f}]")

    frac = float(ok_both.mean())
    # A CONSTRAINED vintage must read exactly 100 %: the wedge rejects inside
    # logposterior, so no draw can violate it at any convergence state. This
    # case is a WIRING check, not a diagnosis, and must not be reported with
    # the "a filter would do instead" message written for unconstrained L11.
    if frac == 1.0:
        verdict = ("CONSTRAINED VINTAGE -- every draw satisfies the ordering, as\n"
                   "  the --gis-ordered wedge requires. This confirms the constraint\n"
                   "  is LIVE in the production path; it is not evidence about\n"
                   "  whether the constraint was needed.")
    elif frac > 0.80:
        verdict = ("(a) MOSTLY ORDERED -- a rejection filter on the existing "
                   "posterior is the cheap equivalent of the re-tune")
    elif frac > 0.20:
        verdict = ("(b) PARTIALLY ORDERED -- the constraint is a real prior; a "
                   "filter is defensible but discards a large minority")
    else:
        verdict = ("(c) ESSENTIALLY UNORDERED -- a filter would destroy the "
                   "sample; only a re-tune can impose the ordering")
    print(f"\nVERDICT: {frac*100:.2f} % of draws satisfy the ordering.\n  {verdict}")

    pd.DataFrame([
        dict(quantity="n_draws", value=n),
        dict(quantity="tbar_K", value=tbar),
        dict(quantity="frac_alpha_ordered", value=float(ok_a.mean())),
        dict(quantity="frac_beta_ordered", value=float(ok_b.mean())),
        dict(quantity="frac_both_ordered", value=frac),
        dict(quantity="frac_tau_ordered", value=float(np.mean(tau_s > tau_f))),
        dict(quantity="median_alpha_f", value=float(np.median(a_f))),
        dict(quantity="median_alpha_s", value=float(np.median(a_s))),
        dict(quantity="median_beta_f", value=float(np.median(b_f))),
        dict(quantity="median_beta_s", value=float(np.median(b_s))),
        dict(quantity="median_tau_fast_yr", value=float(np.median(tau_f))),
        dict(quantity="median_tau_slow_yr", value=float(np.median(tau_s))),
    ]).to_csv(OUT_CSV, index=False)
    print(f"\nwrote {os.path.relpath(OUT_CSV, REPO)}")


if __name__ == "__main__":
    main()
