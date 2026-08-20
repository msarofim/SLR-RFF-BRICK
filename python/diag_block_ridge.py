#!/usr/bin/env python3
"""
diag_block_ridge.py — WHERE are the unidentified directions, and what would a
reparameterisation have to be?

THE PROBLEM (Marcus, thread 3)
    The L10 posterior is accepted on the deliverable but 19 parameter marginals
    are not converged, led by `ais_iceflow0` (R-hat 2.359, ESS 12, tau 3.3e5)
    with four chains on nearly disjoint support. Four of seven Greenland
    parameters fail the same way, all in the SLOW channel
    (`gis_f` 1.335, `gis_alpha_s` 1.180, `gis_beta_s` 1.137, `gis_c0` 1.102)
    while the FAST channel converges cleanly. Running longer is not a plan --
    tau ~ 3.3e5 needs O(1e7-1e8) iterations. The productive move is to sample
    along the ridge instead of across it, as `ais_runoff_Ton` already did once:
    h0 and c enter the model only as hR = h0 + c*T_ant, so they rode an
    r = 0.9997 ridge until the pair was resampled as (T_on = -h0/c, c).

    This file finds the remaining ridges the same way that one was found, and
    says which coordinates a reparameterisation would have to be written in.

METHOD, and the three traps it avoids
    1. WITHIN-CHAIN, NEVER POOLED. The pooled posterior of a non-converged block
       is a MIXTURE of four chains that never merged; its correlation matrix
       describes the mixture, not the ridge. Every covariance here is computed
       per chain, and the cross-chain agreement is itself reported.
    2. CORRELATION, NOT COVARIANCE. The raw covariance of this block is
       ill-conditioned for a reason that is not physics -- the parameter scales
       span decades (the calibrator's own paleo prior says cond 5.2e13 raw vs
       2.75 standardised). Eigen-analysis is done on the correlation matrix,
       i.e. on z-scores, so "direction" means a combination of standardised
       parameters and the loadings are comparable.
    3. A RIDGE IS NOT THE SAME AS A WIDE MARGINAL. A parameter can be poorly
       determined on its own and perfectly well determined given the others, or
       vice versa. Both are reported: the eigenvector loadings say which
       COMBINATION is loose, and the posterior/prior width ratio says whether
       the block is data-constrained at all or is just returning its prior.

WHAT COMES OUT
    Per block and per chain: the eigen-spectrum of the standardised posterior,
    the loadings of the loosest and stiffest directions, the alignment of the
    loose direction across chains (|cos| — near 1 means all four chains see the
    SAME ridge, which is what makes a reparameterisation well posed), and the
    per-parameter posterior/prior width ratio. Plus the pairwise correlations
    above a threshold, which is what a reparameterisation is usually written
    from.

    Thread 2 rides along: `gis_beta_f`'s correlations answer whether re-bounding
    its prior to the data support can help, or whether it is riding a ridge with
    `gis_f` and only a reparameterisation will.

  python3 python/diag_block_ridge.py [--nrows=N]
Outputs:
  outputs/diag_block_ridge_pairs_<TAG>.csv     pairwise |r| above threshold, per block x chain
  outputs/diag_block_ridge_spectrum_<TAG>.csv  eigen-spectrum + loadings, per block x chain
  outputs/diag_block_ridge_<TAG>.md            the readable verdict per block

  ALL THREE CARRY THE TAG. They did not until 2026-08-20, so running this with
  --tag= overwrote the previous vintage's committed analysis in place. The
  pre-existing L10 artefacts keep their original vintage-free names for provenance;
  everything written from now on is vintage-scoped.
"""
import os
import subprocess
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAIN = os.path.join(REPO, "outputs/mcmc/chain_{tag}_seed{seed}_n{n}.csv")
TAG, NITER = "L10", 2000000          # overridable: --tag=, --niter=
SEEDS = [2026, 2027, 2028, 2029]
NBURN_FRAC = 0.5                  # discard the FIRST HALF, as postprocess does
THIN = 200                        # every THIN-th post-burn row; tau ~ 3e5 means
                                  # nothing is lost and the read stays cheap
R_REPORT = 0.80                   # |r| worth naming as a candidate pair
N_LOAD = 4                        # loadings printed per direction

# The blocks under test. AIS carries the 7 joint-paleo geometry parameters plus
# the AIS/ocean parameters that also failed; Greenland is the 7 sampled gis_*.
BLOCKS = {
    "ais_geometry": ["ais_mu", "ais_bedheight0", "ais_slope", "ais_iceflow0",
                     "ais_precip0_LOG", "ais_runoff_Ton", "ais_c"],
    "ais_other": ["ais_ocean_temperature₀", "antarctic_alpha", "antarctic_nu",
                  "antarctic_temp_threshold", "antarctic_lambda", "antarctic_gamma",
                  "antarctic_kappa", "anto_alpha", "anto_beta", "ais_gmst_amp"],
    # BOTH slow-channel coordinate sets are listed, plus the basin scales. Which
    # ones EXIST depends on the vintage: L10 carries native (alpha_s, beta_s);
    # L11+ carries the reparameterised (ell, w); L13 adds gis_s_mid + gis_s_high;
    # L14 (--gis-basins2) drops gis_s_mid. Blocks are intersected with the chain
    # header below and WHAT WAS DROPPED IS PRINTED — a block that silently shrinks
    # is an eigen-analysis of a different model than the label claims.
    "greenland": ["gis_c1", "gis_c0", "gis_f", "gis_alpha_f", "gis_beta_f",
                  "gis_alpha_s", "gis_beta_s", "gis_slow_ell", "gis_slow_w",
                  "gis_s_mid", "gis_s_high"],
}
# Prior sd from calibrate_mcmc_ext.jl (the Greenland block is written there
# literally; the AIS geometry block's sd comes from the paleo prior file).
GIS_PRIOR_SD = {"gis_c1": 0.050, "gis_c0": 0.100, "gis_f": 0.30,
                "gis_alpha_f": 0.020, "gis_beta_f": 0.050,
                "gis_alpha_s": 0.020, "gis_beta_s": 0.020,
                # L11+ reparameterised slow channel: GIS_ELL_SD = 1.0 in the
                # calibrator. gis_slow_w is pushed with sigma 1e3 on [0, 1], i.e.
                # EFFECTIVELY UNIFORM — its honest prior width is 1/sqrt(12),
                # not 1e3, and using 1e3 would make every width ratio ~0.
                "gis_slow_ell": 1.0, "gis_slow_w": 1.0 / (12 ** 0.5),
                # L13+ basin rate scales, sampled as log10 with sigma 0.5
                "gis_s_mid": 0.50, "gis_s_high": 0.50}
GEO_PRIOR_FILE = os.path.join(REPO, "outputs/paleo_geo_prior_ton.csv")

COMMIT = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True).stdout.strip()


def prior_sd():
    """Prior sd per parameter, from the same sources the calibrator reads."""
    sd = dict(GIS_PRIOR_SD)
    if os.path.exists(GEO_PRIOR_FILE):
        rows = [l.strip().split(",") for l in open(GEO_PRIOR_FILE)
                if l.strip() and not l.startswith("#")]
        # the file's key row is "names" (plural) — matching only "name" silently
        # dropped every AIS prior width and left the ratio table half empty
        names = next((r[1:] for r in rows if r[0] in ("name", "names")), None)
        vals = next((r[1:] for r in rows if r[0] == "sd"), None)
        if names and vals:
            sd.update({n: float(v) for n, v in zip(names, vals)})
        else:  # the file may carry sd positionally against BLOCKS order
            vals = next((r[1:] for r in rows if r[0] == "sd"), None)
            if vals and len(vals) == len(BLOCKS["ais_geometry"]):
                sd.update({n: float(v) for n, v in zip(BLOCKS["ais_geometry"], vals)})
    return sd


def load_chains(cols, nrows=None):
    """Post-burn, thinned draws per chain. Returns {seed: DataFrame}."""
    out = {}
    for sd in SEEDS:
        f = CHAIN.format(tag=TAG, seed=sd, n=NITER)
        if not os.path.exists(f):
            sys.exit(f"missing chain {f}")
        d = pd.read_csv(f, usecols=cols, nrows=nrows)
        d = d.iloc[int(len(d) * NBURN_FRAC)::THIN]
        out[sd] = d[cols]
        print(f"  seed{sd}: {len(d)} thinned post-burn draws", flush=True)
    return out


def spectrum(df):
    """Eigen-decomposition of the CORRELATION matrix (i.e. of the z-scored
    posterior). Returns (eigenvalues desc, eigenvectors as columns, corr)."""
    c = df.corr().values
    w, v = np.linalg.eigh(c)
    order = np.argsort(w)[::-1]
    return w[order], v[:, order], c


def mixing_directions(chains, cols):
    """THE decisive object: the directions in which the four chains DISAGREE.

    Within-chain covariance cannot find the worst-mixing direction, because a
    chain with ESS 12 on an axis has not moved along it — its own covariance
    describes the slice it is stuck in. What names the problem is the
    generalised eigenproblem

        B v = lambda W v

    with W the mean WITHIN-chain covariance and B the BETWEEN-chain covariance of
    the chain means, both on z-scores. lambda is the between/within variance
    ratio along v, i.e. a directional R-hat: the top eigenvector is the direction
    the sampler fails to mix, and it is the coordinate a reparameterisation has to
    be written in. (With 4 chains B has rank <= 3, so at most 3 lambdas are
    non-zero — we want the first.)

    Returns (lambdas desc, eigenvectors as columns) in the z-scored basis."""
    Z = [(chains[s][cols] - pd.concat([chains[t][cols] for t in chains]).mean())
         / pd.concat([chains[t][cols] for t in chains]).std() for s in chains]
    W = np.mean([z.cov().values for z in Z], axis=0)
    M = np.array([z.mean().values for z in Z])
    B = np.cov(M.T, bias=True)
    # symmetric solve via a whitening transform of W (W is full rank here)
    Lw = np.linalg.cholesky(W + 1e-12 * np.eye(len(cols)))
    A = np.linalg.solve(Lw, np.linalg.solve(Lw, B.T).T)
    lam, U = np.linalg.eigh(A)
    order = np.argsort(lam)[::-1]
    V = np.linalg.solve(Lw.T, U[:, order])
    V = V / np.linalg.norm(V, axis=0)
    return lam[order], V


def loadings_str(vec, names, k=N_LOAD):
    idx = np.argsort(np.abs(vec))[::-1][:k]
    return "  ".join(f"{names[i]} {vec[i]:+.2f}" for i in idx)


def main():
    global TAG, NITER, BLOCKS
    nrows = None
    for a in sys.argv[1:]:
        if a.startswith("--nrows="):
            nrows = int(a.split("=")[1])
        elif a.startswith("--tag="):
            TAG = a.split("=", 1)[1]
        elif a.startswith("--niter="):
            NITER = int(a.split("=")[1])

    # INTERSECT THE BLOCKS WITH THE ACTUAL CHAIN HEADER, and say what went. The
    # vintages in this line do not share a parameter set (L10 native slow channel,
    # L11+ reparameterised, L13 +2 basin scales, L14 +1), so a fixed block list
    # either crashes on a missing column or — worse, once anyone adds a try/except —
    # quietly analyses a smaller block under the old label.
    probe = CHAIN.format(tag=TAG, seed=SEEDS[0], n=NITER)
    if not os.path.exists(probe):
        sys.exit(f"no chain for --tag={TAG}: {probe}")
    have = set(pd.read_csv(probe, nrows=0).columns)
    print(f"tag {TAG}: chain header carries {len(have)} columns", flush=True)
    for b, v in list(BLOCKS.items()):
        keep = [c for c in v if c in have]
        drop = [c for c in v if c not in have]
        BLOCKS[b] = keep
        if drop:
            print(f"  block {b}: dropped {len(drop)} column(s) absent from this "
                  f"vintage — {', '.join(drop)}", flush=True)
        if not keep:
            print(f"  block {b}: EMPTY for this vintage, skipped", flush=True)
    BLOCKS = {b: v for b, v in BLOCKS.items() if len(v) >= 2}

    psd = prior_sd()
    cols = sorted({c for v in BLOCKS.values() for c in v})
    print(f"reading {len(cols)} columns from {len(SEEDS)} chains "
          f"(burn {NBURN_FRAC:.0%}, thin {THIN})", flush=True)
    chains = load_chains(cols, nrows)

    pair_rows, spec_rows = [], []
    lines = [f"# Where the unidentified directions are (block ridge diagnostic)", "",
             f"- commit `{COMMIT}`; tag `{TAG}`; {len(SEEDS)} chains, first "
             f"{NBURN_FRAC:.0%} burned, thinned 1-in-{THIN}",
             f"- eigen-analysis on the CORRELATION matrix (z-scores), computed "
             f"WITHIN each chain — the pooled posterior of a non-converged block is a "
             f"mixture, not a ridge", ""]

    for bname, bcols in BLOCKS.items():
        lines += [f"## {bname}  ({len(bcols)} parameters)", ""]
        tops, spectra = {}, {}
        for sd, df in chains.items():
            sub = df[bcols]
            w, v, c = spectrum(sub)
            tops[sd] = v[:, 0]
            spectra[sd] = w
            for i in range(len(w)):
                spec_rows.append(dict(block=bname, seed=sd, rank=i + 1,
                                      eigenvalue=w[i], var_frac=w[i] / w.sum(),
                                      loadings=loadings_str(v[:, i], bcols, len(bcols))))
            for i in range(len(bcols)):
                for j in range(i + 1, len(bcols)):
                    if abs(c[i, j]) >= R_REPORT:
                        pair_rows.append(dict(block=bname, seed=sd, a=bcols[i],
                                              b=bcols[j], r=c[i, j]))
        # ---- eigen-spectrum, averaged over chains (they agree or they do not) --
        wbar = np.mean([spectra[s] for s in SEEDS], axis=0)
        lines += [f"Eigen-spectrum (mean over chains, % of standardised variance): " +
                  ", ".join(f"{100 * x / wbar.sum():.0f}%" for x in wbar),
                  f"Condition number of the correlation matrix: "
                  f"{wbar[0] / max(wbar[-1], 1e-12):.0f}", ""]
        # ---- is it the SAME ridge in every chain? ------------------------------
        base = tops[SEEDS[0]]
        cosines = [abs(float(np.dot(base, tops[s]))) for s in SEEDS[1:]]
        same = all(x > 0.9 for x in cosines)
        lines += [f"**Loosest direction, chain-to-chain alignment |cos| = "
                  f"{', '.join(f'{x:.3f}' for x in cosines)}** — "
                  + ("all four chains see the SAME loose direction, so a "
                     "reparameterisation along it is well posed."
                     if same else
                     "the chains do NOT agree on the loose direction; they are in "
                     "different places, and a single reparameterisation may not serve "
                     "all four."), ""]
        lines += ["| direction | % var | loadings (largest first) |", "|---|---|---|"]
        for i in (0, 1, len(bcols) - 1):
            v0 = np.mean([spectrum(chains[s][bcols])[1][:, i] *
                          np.sign(spectrum(chains[s][bcols])[1][0, i]) for s in SEEDS], axis=0)
            tag = "loosest" if i == 0 else ("2nd loosest" if i == 1 else "STIFFEST")
            lines.append(f"| {tag} | {100 * wbar[i] / wbar.sum():.0f}% | "
                         f"{loadings_str(v0, bcols)} |")
        lines.append("")
        # ---- WHERE THE CHAINS DISAGREE (the decisive diagnostic) --------------
        lam, V = mixing_directions(chains, bcols)
        worst = 100 * lam[0] / lam.sum()
        lines += ["**Worst-mixing directions — where the four chains DISAGREE.** "
                  "Within-chain covariance cannot see these (a chain with ESS 12 on an "
                  "axis has not moved along it); this is the generalised eigenproblem "
                  "`B v = lambda W v`, i.e. a directional R-hat.", "",
                  "| rank | between/within | loadings |", "|---|---|---|"]
        for i in range(min(3, len(bcols))):
            lines.append(f"| {i + 1} | {lam[i]:.2f} | {loadings_str(V[:, i], bcols)} |")
        lines += ["",
                  f"The top direction carries {worst:.0f}% of all between-chain variance. "
                  + ("It is CONCENTRATED, so one reparameterisation addresses most of the "
                     "non-mixing." if worst > 60 else
                     "It is NOT concentrated — the non-mixing is spread over several "
                     "directions, and one reparameterisation will not fix it."), "",
                  "Per-parameter share of that direction "
                  "(|loading|, z-scored — what a new coordinate must be built from):", "",
                  "| param | |loading| on worst direction |", "|---|---|"]
        for i in np.argsort(np.abs(V[:, 0]))[::-1]:
            lines.append(f"| {bcols[i]} | {abs(V[i, 0]):.2f} |")
        lines.append("")

        # ---- pairwise correlations worth naming --------------------------------
        pb = pd.DataFrame([r for r in pair_rows if r["block"] == bname])
        if not pb.empty:
            agg = (pb.groupby(["a", "b"]).r.agg(["mean", "min", "max", "count"])
                     .reset_index().sort_values("mean", key=abs, ascending=False))
            lines += [f"Pairs with |r| >= {R_REPORT} in at least one chain:", "",
                      "| pair | mean r | range | chains |", "|---|---|---|---|"]
            for _, r in agg.iterrows():
                lines.append(f"| {r.a} — {r.b} | {r['mean']:+.3f} | "
                             f"[{r['min']:+.3f}, {r['max']:+.3f}] | {int(r['count'])}/4 |")
        else:
            lines.append(f"No pair reaches |r| >= {R_REPORT} in any chain — the loose "
                         f"direction is not a two-parameter ridge.")
        lines.append("")
        # ---- posterior vs prior width -----------------------------------------
        have = [c for c in bcols if c in psd]
        if have:
            lines += ["Posterior/prior width (mean over chains) — < 1 means the data "
                      "constrain it, ~1 means the marginal is the prior:", "",
                      "| param | post sd / prior sd |", "|---|---|"]
            for c in have:
                ratio = np.mean([chains[s][c].std() / psd[c] for s in SEEDS])
                lines.append(f"| {c} | {ratio:.2f} |")
            lines.append("")

    pd.DataFrame(pair_rows).to_csv(
        os.path.join(REPO, f"outputs/diag_block_ridge_pairs_{TAG}.csv"), index=False)
    pd.DataFrame(spec_rows).to_csv(
        os.path.join(REPO, f"outputs/diag_block_ridge_spectrum_{TAG}.csv"), index=False)
    # TAG-SCOPED, 2026-08-20. These were nameless: running with --tag=L14 overwrote
    # the COMMITTED L10 analysis (7c42573) in place, with no warning and a valid-looking
    # file left behind. A vintage-specific artefact at a vintage-free path is the same
    # defect class as a nameless covariance — see memory `nameless_matrix_order`.
    out_md = os.path.join(REPO, f"outputs/diag_block_ridge_{TAG}.md")
    with open(out_md, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote {out_md}", flush=True)


if __name__ == "__main__":
    main()
