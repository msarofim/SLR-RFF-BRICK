#!/usr/bin/env python3
"""Precompute the continuous FaIR-forcing PCA basis for the joint FaIR/BRICK calibration.

Produces outputs/forcing_pca_basis.csv + outputs/forcing_pca_meta.csv, which
julia/calibrate_mcmc_joint_cont.jl consumes to sample the FaIR forcing dimension
CONTINUOUSLY (NPC principal-component scores over the 841-member calib1.4.5 ensemble)
jointly with theta_BRICK in one RAM — recovering the te_alpha<->historical-OHC ridge
that the mean-forcing calibration (calibrate_mcmc_ext.jl) drops.

Construction (reproduces the committed basis to machine precision):
  1. Read the 841-member ensemble GMST + OHC over Y0..Y1 from the curv_wide wides.
     OHC is scaled by OHCS=0.1 to match the calibrator's 1e22-J units convention.
  2. Per-year ensemble means gmean(t), omean(t)  (a=0 reconstructs these == fair_mean).
  3. Standardize each block by a SCALAR pop-std: gs=std(GMST-gmean), os=std(OHC-omean),
     so GMST and OHC enter the joint SVD on a comparable footing.
  4. Joint SVD of Z = [ (GMST-gmean)/gs ; (OHC-omean)/os ]  (2*ny x nmem); keep K PCs.
     Gload_k/Oload_k = the GMST / OHC halves of left singular vector k (unit norm across
     the stacked vector); score a_k(member) = S_k * V_k(member).
  5. reconstruct(a): GMST = gmean + gs * sum_k a_k Gload_k ; OHC = omean + os * sum_k a_k Oload_k.

The per-PC sign is a free convention: flipping (Gload_k, Oload_k, a_k) together leaves
reconstruct() invariant and the score prior N(0,sstd_k) is symmetric, so ANY sign choice
yields an identical calibration. For byte-stable regeneration this script aligns each PC's
sign to the committed basis when it is present, else uses a max-abs-positive canonical sign.

K=3 rationale: PC1 ~74.5% of forcing variance (GMST/future-ECS dominated, little historical
OHC), PC2 ~22.2% and PC3 ~1.1% carry the historical-OHC coupling — d(OHC@2018)/da_k grows
0.058 -> 0.494 -> 3.171 (1e22 J per unit score), so PC2/PC3 (not PC1) are what the historical
SLR fit constrains and where the te_alpha coupling lives. K=3 captures ~91% of the historical
OHC spread; adding PC4 buys <1% and no new OHC coupling.

Usage:  python python/precompute_forcing_pca.py            # regenerate + self-check
        python python/precompute_forcing_pca.py --no-check # regenerate, skip committed-basis compare
"""
import os, sys
import numpy as np
import pandas as pd

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRC  = os.path.join(REPO, "..", "FaIRtoFrEDI",
                    "magicc_comparison", "processed", "curv_wide")
Y0, Y1 = 1850, 2300          # basis window (calibrator slices its fit window out of this)
OHCS   = 0.1                 # ensemble OHC (1e21 J) -> 1e22 J, matching the calibrator
K      = 3                   # number of retained forcing PCs
OUT_BASIS = os.path.join(REPO, "outputs", "forcing_pca_basis.csv")
OUT_META  = os.path.join(REPO, "outputs", "forcing_pca_meta.csv")


def load_wide(name, scale=1.0):
    df = pd.read_csv(os.path.join(FRC, name)).set_index("year")
    yrs = list(range(Y0, Y1 + 1))
    return df.reindex(yrs).values * scale, np.array(yrs)


def main():
    check = "--no-check" not in sys.argv
    G, yrs = load_wide("fair_gmst_base_wide.csv")
    O, _   = load_wide("fair_ohc_base_wide.csv", scale=OHCS)
    ny = len(yrs)
    assert not np.isnan(G).any() and not np.isnan(O).any(), "ensemble has gaps over Y0..Y1"

    gmean = G.mean(axis=1); omean = O.mean(axis=1)
    Ga = G - gmean[:, None]; Oa = O - omean[:, None]
    gs = Ga.std(); os_ = Oa.std()                       # scalar population std (ddof=0)
    Z = np.vstack([Ga / gs, Oa / os_])                  # (2*ny, nmem)
    U, S, Vt = np.linalg.svd(Z, full_matrices=False)

    # optional committed-basis reference for byte-stable sign alignment
    ref = pd.read_csv(OUT_BASIS) if os.path.exists(OUT_BASIS) else None

    cols = {"year": yrs, "gmean": gmean, "omean": omean}
    meta = {"pc": [], "sstd": [], "amin": [], "amax": [], "gs": [], "os": []}
    for k in range(K):
        Gl = U[:ny, k].copy(); Ol = U[ny:, k].copy()
        a = S[k] * Vt[k, :]
        if ref is not None:
            sgn = np.sign(np.dot(Gl, ref[f"Gload{k+1}"].values)) or 1.0
        else:                                            # max-abs-positive canonical fallback
            full = U[:, k]; sgn = np.sign(full[np.argmax(np.abs(full))]) or 1.0
        Gl *= sgn; Ol *= sgn; a *= sgn
        cols[f"Gload{k+1}"] = Gl; cols[f"Oload{k+1}"] = Ol
        meta["pc"].append(k + 1); meta["sstd"].append(a.std())
        meta["amin"].append(a.min()); meta["amax"].append(a.max())
        meta["gs"].append(gs); meta["os"].append(os_)

    basis = pd.DataFrame(cols)
    order = ["year", "gmean", "omean"] + sum([[f"Gload{k+1}", f"Oload{k+1}"] for k in range(K)], [])
    basis = basis[order]
    pd.DataFrame(meta).to_csv(OUT_META, index=False)
    basis.to_csv(OUT_BASIS, index=False)

    frac = (S**2 / (S**2).sum())[:K]
    print(f"K={K} PCs; variance fractions {np.round(frac,4)}  (sum {frac.sum():.4f})")
    dOHC = [float(os_ * U[ny:, k][yrs.tolist().index(2018)]) for k in range(K)]
    print(f"d(OHC@2018)/da_k (1e22 J/unit score) = {np.round(dOHC,3)}")
    print(f"gs={gs:.6f}  os={os_:.6f}")
    print(f"wrote {os.path.relpath(OUT_BASIS,REPO)} + {os.path.relpath(OUT_META,REPO)}")

    if check and ref is not None:
        md = max(np.max(np.abs(basis[c].values - ref[c].values)) for c in ref.columns)
        print(f"self-check vs committed basis: max|diff| = {md:.2e} "
              f"({'MATCH' if md < 1e-10 else 'DRIFT — investigate'})")


if __name__ == "__main__":
    main()
