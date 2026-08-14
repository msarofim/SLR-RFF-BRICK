#!/usr/bin/env python3
"""
diag_gis_slow_reparam.py — WHICH reference anomaly T-bar should the Greenland
slow-channel reparameterisation be written around, and does the reparameterisation
actually buy anything?

THE DECISION THIS SERVES (Marcus 2026-08-14, spec_2026-08-14_next_calibration.md
section 4). Item 1.2 of the thread-4 spec replaces the sampled pair
(gis_alpha_s, gis_beta_s) with (log r_s(T-bar), tilt), where

    rate_s(T) = alpha_s * T + beta_s        (the slow channel's relaxation rate)
    r_s(T-bar) = the rate AT the reference anomaly = the LEVEL of the slow rate

T-bar has to be chosen explicitly because it sets what "the level" means and
therefore what the prior on log r_s(T-bar) asserts. Two candidates were on the
table: the hindcast-mean regional anomaly, and the 2015-2024 anchor that the amp
law and the driver splice already use. Marcus asked for both to be compared
offline before the sampler sees either.

THE REPARAMETERISATION, and why the tilt is dimensionless
    level  ell = log r_s(T-bar)
    tilt   w   = alpha_s * T-bar / r_s(T-bar)     the share of the LEVEL that
                                                  temperature carries
    inverse:   alpha_s = w * exp(ell) / T-bar ,   beta_s = (1 - w) * exp(ell)
For alpha_s >= 0 and beta_s >= 0, w lands in [0, 1] automatically, so the inverse
map cannot produce a negative rate. A plain tilt = alpha_s does NOT have that
property: it lets beta_s = r - alpha_s*T-bar go negative, which just moves the
rail rather than removing it. Both are reported; w is the one recommended.

WHAT THE REPARAMETERISATION CAN AND CANNOT DO, stated before any number
    ell is UNBOUNDED (r_s > 0 always), so the level -- the direction the chains
    do not mix along -- gets a coordinate with no boundary. But BOTH original
    rails map into w: alpha_s = 0 is w = 0 and beta_s = 0 is w = 1. So the
    reparameterisation does not delete the boundary, it moves the whole boundary
    into the tilt and frees the level. That is the claim being tested, and it is
    weaker than "moves the rail out to infinity".

THREE TRAPS THIS AVOIDS
    1. WITHIN-CHAIN, NEVER POOLED. The pooled posterior of a non-converged block
       is a mixture of four chains that never merged; its correlation describes
       the mixture. Every correlation here is computed per chain and the pooled
       value is reported separately and labelled. (Thread 3, 2026-08-13.)
    2. THE RAIL CLAIM IS CHECKED, NOT INHERITED. The handoff describes "a hard
       rail at alpha_s = 0". The offline A+B optimum on record rails BETA_s, not
       alpha_s, and the posterior rail occupancies are measured here rather than
       assumed.
    3. SAME FEASIBLE SET. The refit optimises over the native (alpha_s, beta_s)
       bounds in both parameterisations -- a transformed objective that quietly
       enlarges the feasible set would "win" for free.

  python3 python/diag_gis_slow_reparam.py [--thin N]
Writes:
  outputs/diag_gis_slow_reparam.csv     per-chain conditioning under each T-bar
  outputs/diag_gis_slow_reparam.md      the readable verdict
  figures/diag_gis_slow_reparam.png
"""
import argparse
import os
import subprocess
import sys

import numpy as np
import pandas as pd
from scipy.optimize import minimize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gis_offline_cell as CELL          # noqa: E402  (path set above)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAIN = os.path.join(REPO, "outputs/mcmc/chain_{tag}_seed{seed}_n{n}.csv")
TAG, NITER = "L10", 2000000
SEEDS = [2026, 2027, 2028, 2029]
BURN_FRAC = 0.5
THIN = 50

FITS_CSV = os.path.join(REPO, "outputs/gis_offline_cell_fits.csv")
FIT_CELL = "A+B"

# T-bar candidates. Both are means of the SAME driver the calibrator uses
# (t_gis_zones.csv, zone `south`, anomalies vs 1850-1900), so they differ only
# in the window. Labels derive from these constants.
HINDCAST_WIN = CELL.FIT_WIN            # (1900, 2025) -- where the slow channel is fitted
ANCHOR_WIN = (2015, 2024)              # the amp-law / driver-splice anchor

# native bounds, from gis_offline_cell.PBOUNDS -- the feasible set both
# parameterisations must optimise over
A_LO, A_HI = CELL.PBOUNDS["alpha_s"]
B_LO, B_HI = CELL.PBOUNDS["beta_s"]
RAIL_TOL_A = 1e-4                      # "at" the alpha_s = 0 rail
RAIL_TOL_B = 1.1e-6                    # "at" the beta_s = 1e-6 rail
FEAS_TOL = 1e-9                        # bound slack for the log/exp round trip (see make_obj)

# priors on record, calibrate_mcmc_ext.jl lines 384-387
PRIOR = {"alpha_s": (0.0070727, 0.020), "beta_s": (0.0010000, 0.020)}
PRIOR_N = 200000
TBAR_SCAN = np.linspace(0.2, 4.0, 77)

OUT_CSV = os.path.join(REPO, "outputs/diag_gis_slow_reparam.csv")
OUT_MD = os.path.join(REPO, "outputs/diag_gis_slow_reparam.md")
OUT_PNG = os.path.join(REPO, "figures/diag_gis_slow_reparam.png")

COMMIT = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True).stdout.strip()


# =============================================================================
# the map
# =============================================================================
def to_reparam(alpha_s, beta_s, tbar, tilt="w"):
    r = alpha_s * tbar + beta_s
    ell = np.log(np.maximum(r, 1e-300))
    return (ell, alpha_s * tbar / np.maximum(r, 1e-300)) if tilt == "w" \
        else (ell, alpha_s)


def from_reparam(ell, w, tbar, tilt="w"):
    r = np.exp(ell)
    if tilt == "w":
        return w * r / tbar, (1.0 - w) * r
    return w, r - w * tbar          # tilt = alpha_s; beta_s can go NEGATIVE


def selftest_roundtrip():
    """MUTATION-STYLE SELF-TEST. The verdicts below are statements about the
    posterior only if the map is its own inverse; a broken map would produce
    equally printable correlations."""
    rng = np.random.default_rng(11)
    a = rng.uniform(A_LO, A_HI, 5000)
    b = rng.uniform(B_LO, B_HI, 5000)
    for tbar in (0.5, 1.1692, 1.9631, 3.0):
        for tilt in ("w", "alpha"):
            a2, b2 = from_reparam(*to_reparam(a, b, tbar, tilt), tbar, tilt)
            err = max(np.max(np.abs(a2 - a)), np.max(np.abs(b2 - b)))
            assert err < 1e-10, f"round-trip failed, tbar={tbar} tilt={tilt}: {err:.2e}"
    # and the advertised property: w in [0,1] whenever both natives are >= 0
    _, w = to_reparam(a, b, 1.1692, "w")
    assert w.min() >= 0.0 and w.max() <= 1.0, "w escaped [0,1] on non-negative inputs"
    print("  [self-test] (ell, tilt) round-trips both ways, and w stays in [0,1]  OK")


# =============================================================================
# inputs
# =============================================================================
def tbar_candidates():
    drv = pd.read_csv(CELL.DRIVER_CSV).set_index("year")[CELL.DRIVER_ZONE]
    drv = drv - drv.loc[CELL.BASE_WIN[0]:CELL.BASE_WIN[1]].mean()
    return {
        f"hindcast_mean_{HINDCAST_WIN[0]}_{HINDCAST_WIN[1]}":
            float(drv.loc[HINDCAST_WIN[0]:HINDCAST_WIN[1]].mean()),
        f"anchor_{ANCHOR_WIN[0]}_{ANCHOR_WIN[1]}":
            float(drv.loc[ANCHOR_WIN[0]:ANCHOR_WIN[1]].mean()),
    }, drv


def load_chains(thin):
    cols = ["gis_alpha_s", "gis_beta_s"]
    out = {}
    for s in SEEDS:
        f = CHAIN.format(tag=TAG, seed=s, n=NITER)
        if not os.path.exists(f):
            sys.exit(f"missing chain {f}")
        d = pd.read_csv(f, usecols=cols)
        out[s] = d.iloc[int(len(d) * BURN_FRAC)::thin].reset_index(drop=True)
        print(f"  seed{s}: {len(out[s]):,} thinned post-burn draws", flush=True)
    return out


def offline_ctx_and_theta():
    """The A+B optimum on record, and the context needed to re-evaluate it."""
    drv = pd.read_csv(CELL.DRIVER_CSV).set_index("year")[CELL.DRIVER_ZONE]
    ctx = dict(t_reg=CELL.extend(drv), t_gmst=CELL.extend(CELL.load_gmst()))
    ty, obs, sig = CELL.load_target()
    ctx.update(ty=ty, obs=obs, sig=sig, ti=[CELL._yi[y] for y in ty])
    row = pd.read_csv(FITS_CSV).set_index("cell").loc[FIT_CELL]
    p = dict(kv.split("=") for kv in str(row["params"]).split("; "))
    names = CELL.cell_params(FIT_CELL)
    return ctx, np.array([float(p[k]) for k in names]), names, float(row["neg_log_post"])


# =============================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--thin", type=int, default=THIN)
    args = ap.parse_args()

    print(f"diag_gis_slow_reparam | commit={COMMIT} | driver={CELL.DRIVER_ZONE} | "
          f"posterior={TAG}")
    selftest_roundtrip()
    TBARS, drv = tbar_candidates()
    print("\n  T-bar candidates (zone %s, anomalies vs %d-%d):" %
          (CELL.DRIVER_ZONE, *CELL.BASE_WIN))
    for k, v in TBARS.items():
        print(f"    {k:28s} {v:.4f} K")

    chains = load_chains(args.thin)
    rows, md = [], []
    md.append(f"# Greenland slow-channel reparameterisation — which T-bar?\n\n"
              f"`{TAG}` posterior, within-chain, thin {args.thin}; driver "
              f"`{CELL.DRIVER_ZONE}`; commit `{COMMIT}`.\n")

    # -------------------------------------------------------------- A. rails
    print("\n[A] RAIL OCCUPANCY — the handoff's premise, checked rather than inherited")
    railrows = []
    for s, d in chains.items():
        fa = float((d.gis_alpha_s <= RAIL_TOL_A).mean())
        fb = float((d.gis_beta_s <= RAIL_TOL_B).mean())
        railrows.append((s, fa, fb))
        print(f"  seed{s}  alpha_s <= {RAIL_TOL_A:g}: {fa:6.2%}   "
              f"beta_s <= {RAIL_TOL_B:g}: {fb:6.2%}")
    ctx, theta0, names, nlp0 = offline_ctx_and_theta()
    ia, ib = names.index("alpha_s"), names.index("beta_s")
    print(f"  offline {FIT_CELL} optimum on record: alpha_s={theta0[ia]:.6g}, "
          f"beta_s={theta0[ib]:.6g}  (nlp {nlp0:.4f})")
    at_a = theta0[ia] <= RAIL_TOL_A
    at_b = theta0[ib] <= RAIL_TOL_B
    print(f"  -> the OPTIMUM rails {'alpha_s' if at_a else ''}"
          f"{'beta_s' if at_b else ''}{'neither' if not (at_a or at_b) else ''}")
    md.append(f"\n## A. Which rail is actually occupied\n\n"
              f"Posterior draws within tolerance of a bound, per chain: alpha_s "
              + ", ".join(f"{f:.2%}" for _, f, _ in railrows)
              + "; beta_s " + ", ".join(f"{f:.2%}" for _, _, f in railrows)
              + f". The offline `{FIT_CELL}` optimum on record sits at "
              f"alpha_s={theta0[ia]:.6g}, beta_s={theta0[ib]:.6g}, i.e. it rails "
              f"**{'beta_s' if at_b else 'alpha_s' if at_a else 'neither'}**.\n")

    # ------------------------------------------- B. within-chain conditioning
    print("\n[B] WITHIN-CHAIN |corr| BETWEEN THE TWO SAMPLED COORDINATES")
    print("    (lower = better conditioned; the pooled value is a MIXTURE, "
          "reported but not used)")
    hdr = f"  {'coordinates':34s}" + "".join(f"  seed{s}" for s in SEEDS) + \
          f"{'mean':>8s}{'pooled':>9s}"
    print(hdr)

    def report(label, fn):
        per = []
        for s, d in chains.items():
            x, y = fn(d.gis_alpha_s.to_numpy(), d.gis_beta_s.to_numpy())
            per.append(abs(np.corrcoef(x, y)[0, 1]))
        allc = pd.concat(chains.values())
        X, Y = fn(allc.gis_alpha_s.to_numpy(), allc.gis_beta_s.to_numpy())
        pooled = abs(np.corrcoef(X, Y)[0, 1])
        print(f"  {label:34s}" + "".join(f"{v:8.3f}" for v in per)
              + f"{np.mean(per):8.3f}{pooled:9.3f}")
        rows.append(dict(coordinates=label, **{f"seed{s}": v for s, v in zip(SEEDS, per)},
                         mean_abs_corr=float(np.mean(per)), pooled_abs_corr=float(pooled)))
        return float(np.mean(per))

    base = report("(alpha_s, beta_s)  [as sampled]", lambda a, b: (a, b))
    best = {}
    for name, tb in TBARS.items():
        for tilt, tl in (("w", "tilt=w"), ("alpha", "tilt=alpha_s")):
            lab = f"(log r_s, {tl})  T-bar={tb:.3f}"
            best[(name, tilt)] = report(lab, lambda a, b, tb=tb, tilt=tilt:
                                        to_reparam(a, b, tb, tilt))

    # ------------------------------------------------- C. the decorrelating T-bar
    print("\n[C] SCAN — is there a T-bar that decorrelates the pair, and where do the")
    print("    candidates sit relative to it? (mean within-chain |corr|, tilt=w)")
    scan = []
    for tb in TBAR_SCAN:
        v = np.mean([abs(np.corrcoef(*to_reparam(d.gis_alpha_s.to_numpy(),
                                                 d.gis_beta_s.to_numpy(), tb, "w"))[0, 1])
                     for d in chains.values()])
        scan.append(v)
    scan = np.array(scan)
    tb_opt = float(TBAR_SCAN[np.argmin(scan)])
    print(f"    minimum |corr| {scan.min():.3f} at T-bar = {tb_opt:.3f} K")
    for name, tb in TBARS.items():
        print(f"    {name:28s} T-bar {tb:.3f} K -> |corr| "
              f"{np.interp(tb, TBAR_SCAN, scan):.3f}")

    # ----------------------------------------------------- D. the offline refit
    print(f"\n[D] OFFLINE REFIT of the {FIT_CELL} cell in each parameterisation")
    print("    Same feasible set in every arm (the native alpha_s/beta_s bounds),")
    print("    seeded at the optimum on record, so a reparameterisation can only")
    print("    match or beat it -- anything worse is a broken transform.")
    def nlp_native(th):
        return CELL.neg_log_post(FIT_CELL, th, ctx)

    def make_obj(tb, tilt):
        """Optimise in (ell, tilt) but score in the native coordinates, over the
        NATIVE feasible set so no arm wins by being allowed more room.

        FEAS_TOL exists because the seed point sits exactly ON the beta_s bound
        (the optimum on record rails it), and beta_s reconstructed through
        exp(log(.)) lands a float below 1e-6 -- without the tolerance every
        reparameterised arm is rejected at its own seed and returns the penalty.
        Values inside the tolerance are clipped back onto the bound, not passed
        through."""
        def obj(z):
            th = z.copy()
            a, b = from_reparam(z[ia], z[ib], tb, tilt)
            if (a < A_LO - FEAS_TOL or a > A_HI + FEAS_TOL
                    or b < B_LO - FEAS_TOL or b > B_HI + FEAS_TOL):
                return 1e12
            th[ia], th[ib] = np.clip(a, A_LO, A_HI), np.clip(b, B_LO, B_HI)
            # Nelder-Mead is unbounded, so the other six parameters need the
            # same guard or an arm could "win" by leaving their bounds.
            for k, n in enumerate(names):
                lo, hi = CELL.PBOUNDS[n]
                if k not in (ia, ib) and not (lo - FEAS_TOL <= th[k] <= hi + FEAS_TOL):
                    return 1e12
            return nlp_native(th)
        return obj

    print(f"    {'arm':38s} {'nlp':>10s} {'alpha_s':>11s} {'beta_s':>11s}  rails")
    print(f"    {'native (as fitted, on record)':38s} {nlp0:10.4f} "
          f"{theta0[ia]:11.6g} {theta0[ib]:11.6g}  "
          f"{'beta_s' if at_b else 'alpha_s' if at_a else '-'}")
    refit = [dict(arm="native", nlp=nlp0, alpha_s=theta0[ia], beta_s=theta0[ib])]
    for name, tb in TBARS.items():
        for tilt in ("w", "alpha"):
            z0 = theta0.copy()
            z0[ia], z0[ib] = to_reparam(theta0[ia], theta0[ib], tb, tilt)
            r = minimize(make_obj(tb, tilt), z0, method="Nelder-Mead",
                         options=dict(maxfev=40000, xatol=1e-10, fatol=1e-10))
            a, b = from_reparam(r.x[ia], r.x[ib], tb, tilt)
            rail = ("alpha_s" if a <= RAIL_TOL_A else "") + \
                   ("beta_s" if b <= RAIL_TOL_B else "")
            lab = f"{name} tilt={tilt}"
            print(f"    {lab:38s} {r.fun:10.4f} {a:11.6g} {b:11.6g}  {rail or '-'}")
            refit.append(dict(arm=lab, nlp=float(r.fun), alpha_s=float(a),
                              beta_s=float(b), rails=rail or "-"))
    worse = [d for d in refit[1:] if d["nlp"] > nlp0 + 1e-3]
    print(f"    GATE: no reparameterised arm is worse than the native optimum ... "
          f"{'FAIL ' + str([d['arm'] for d in worse]) if worse else 'PASS'}")

    # --------------------------------------------------- E. the induced prior
    print("\n[E] WHAT THE CURRENT PRIORS BECOME under each T-bar (tilt=w)")
    print("    The priors are N(mu, sigma) truncated to the native bounds; the")
    print("    question is whether log r_s(T-bar) inherits a sane, proper shape.")
    rng = np.random.default_rng(2026)
    a = rng.normal(*PRIOR["alpha_s"], PRIOR_N)
    b = rng.normal(*PRIOR["beta_s"], PRIOR_N)
    keep = (a >= A_LO) & (a <= A_HI) & (b >= B_LO) & (b <= B_HI)
    a, b = a[keep], b[keep]
    print(f"    {'T-bar':30s} {'ell p05':>9s} {'ell p50':>9s} {'ell p95':>9s} "
          f"{'w p05':>7s} {'w p50':>7s} {'w p95':>7s} {'|corr|':>7s}")
    for name, tb in TBARS.items():
        ell, w = to_reparam(a, b, tb, "w")
        qe = np.percentile(ell, [5, 50, 95]); qw = np.percentile(w, [5, 50, 95])
        c = abs(np.corrcoef(ell, w)[0, 1])
        print(f"    {name:30s} {qe[0]:9.3f} {qe[1]:9.3f} {qe[2]:9.3f} "
              f"{qw[0]:7.3f} {qw[1]:7.3f} {qw[2]:7.3f} {c:7.3f}")
        rows.append(dict(coordinates=f"PRIOR induced, T-bar={tb:.3f}",
                         mean_abs_corr=float(c), pooled_abs_corr=np.nan))
    print(f"    (prior draws inside the native bounds: {keep.mean():.1%} of "
          f"{PRIOR_N:,})")

    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)
    md.append(f"\n## B. Conditioning (within-chain mean |corr|)\n\n"
              f"as sampled `(alpha_s, beta_s)` **{base:.3f}**; "
              + "; ".join(f"`{n}` tilt=w **{best[(n,'w')]:.3f}** / tilt=alpha_s "
                          f"{best[(n,'alpha')]:.3f}" for n in TBARS)
              + f". Scan minimum {scan.min():.3f} at T-bar {tb_opt:.3f} K.\n")
    md.append(f"\n## D. Offline refit\n\n"
              f"Native optimum nlp {nlp0:.4f}. "
              + "; ".join(f"{d['arm']} {d['nlp']:.4f}" for d in refit[1:])
              + f". Gate (no arm worse than native): "
              f"**{'FAIL' if worse else 'PASS'}**.\n")
    with open(OUT_MD, "w") as fh:
        fh.write("".join(md))
    make_figure(chains, TBARS, TBAR_SCAN, scan, tb_opt)
    for p in (OUT_CSV, OUT_MD, OUT_PNG):
        print(f"wrote {os.path.relpath(p, REPO)}")


def make_figure(chains, tbars, scan_x, scan_y, tb_opt):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(1, 3, figsize=(15, 4.4))
    a = ax[0]
    for s, d in chains.items():
        a.plot(d.gis_alpha_s, d.gis_beta_s, ".", ms=1.2, alpha=0.3, label=f"seed{s}")
    a.axvline(0, color="crimson", lw=1.0, ls="--")
    a.axhline(1e-6, color="crimson", lw=1.0, ls="--")
    a.set_xlabel(r"$\alpha_s$"); a.set_ylabel(r"$\beta_s$")
    a.set_title("as sampled — red = the two rails")
    a.legend(fontsize=7, markerscale=8); a.grid(alpha=0.3)

    a = ax[1]
    tb = list(tbars.values())[0]
    for s, d in chains.items():
        ell, w = to_reparam(d.gis_alpha_s.to_numpy(), d.gis_beta_s.to_numpy(), tb, "w")
        a.plot(ell, w, ".", ms=1.2, alpha=0.3)
    a.set_xlabel(r"$\ell=\log r_s(\bar T)$"); a.set_ylabel(r"tilt $w$")
    a.set_title(f"reparameterised, T-bar={tb:.3f} K\nboth rails are now w=0 and w=1")
    a.grid(alpha=0.3)

    a = ax[2]
    a.plot(scan_x, scan_y, lw=1.6)
    for n, v in tbars.items():
        a.axvline(v, ls="--", lw=1.2, label=f"{n} ({v:.2f} K)")
    a.axvline(tb_opt, color="k", lw=1.0, ls=":", label=f"scan min ({tb_opt:.2f} K)")
    a.set_xlabel(r"$\bar T$ (K)"); a.set_ylabel(r"mean within-chain $|corr(\ell,w)|$")
    a.set_title("which T-bar decorrelates level from tilt")
    a.legend(fontsize=7); a.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    main()
