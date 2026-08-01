#!/usr/bin/env python3
"""Split-R-hat convergence diagnostic for the continuous joint FaIR/BRICK calibration chains.

Reads the 4 production chains (chain_jcont_seed{2026..2029}_n{N}.csv) chunked + thinned
(never loads a full 3.4 GB file), drops the first half as burn-in, computes split-R-hat
(Gelman-Rubin, each chain split in two -> 8 half-chains) per column, and reports the pooled
posterior summaries + the te_alpha<->forcing-PC coupling. Convergence gate: R-hat < 1.05 on all
sampled parameters (esp. te_alpha + the 3 forcing scores fpc1-3).

Usage: python python/rhat_joint_cont.py [NITER]   (default 4000000)
"""
import sys, os
import numpy as np
import pandas as pd

REPO   = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MCMC   = os.path.join(REPO, "outputs", "mcmc")
SEEDS  = [2026, 2027, 2028, 2029]
NITER  = int(sys.argv[1]) if len(sys.argv) > 1 else 4_000_000
THIN   = 100                      # every 100th post-burn draw (R-hat is robust to thinning)
BURN   = NITER // 2               # discard first half
KEY    = ["thermal_alpha", "fpc1", "fpc2", "fpc3", "ais_ocean_temperature₀",
          "ais_gmst_amp", "log_post"]


def load_thinned(seed):
    path = os.path.join(MCMC, f"chain_jcont_seed{seed}_n{NITER}.csv")
    parts, seen = [], 0
    for chunk in pd.read_csv(path, chunksize=500_000):
        n = len(chunk); gidx = np.arange(seen, seen + n)
        mask = (gidx >= BURN) & ((gidx - BURN) % THIN == 0)
        if mask.any():
            parts.append(chunk.loc[mask])
        seen += n
    df = pd.concat(parts, ignore_index=True)
    return df


def split_rhat(cols):
    """cols: list of 1D arrays, one per chain. Split each in half -> 2M half-chains."""
    halves = []
    for c in cols:
        m = len(c) // 2
        halves.append(np.asarray(c[:m], float))
        halves.append(np.asarray(c[m:2 * m], float))
    N = min(len(h) for h in halves)
    halves = np.array([h[:N] for h in halves])           # (M, N)
    M = halves.shape[0]
    means = halves.mean(axis=1); vars = halves.var(axis=1, ddof=1)
    W = vars.mean(); B = N * means.var(ddof=1)
    if W <= 0:
        return np.nan
    Vhat = (N - 1) / N * W + B / N
    return float(np.sqrt(Vhat / W))


def main():
    print(f"loading 4 chains (NITER={NITER}, burn={BURN}, thin={THIN}) ...", flush=True)
    dfs = {s: load_thinned(s) for s in SEEDS}
    ndraws = {s: len(dfs[s]) for s in SEEDS}
    print(f"post-burn thinned draws/chain: {ndraws}")
    cols = [c for c in dfs[SEEDS[0]].columns if c not in ("accept_rate",)]

    rhats = {}
    for c in cols:
        rhats[c] = split_rhat([dfs[s][c].values for s in SEEDS])

    finite = {c: r for c, r in rhats.items() if np.isfinite(r)}
    worst = sorted(finite.items(), key=lambda kv: -kv[1])[:8]
    n_bad = sum(1 for r in finite.values() if r >= 1.05)

    print("\n=== split-R-hat ===")
    print(f"params evaluated: {len(finite)}   R-hat >= 1.05: {n_bad}   "
          f"max R-hat: {max(finite.values()):.4f}")
    print("\nworst 8:")
    for c, r in worst:
        print(f"  {c:28s} {r:.4f}")
    print("\nkey params:")
    for c in KEY:
        if c in rhats:
            print(f"  {c:28s} R-hat {rhats[c]:.4f}")

    # pooled posterior + coupling
    pool = pd.concat([dfs[s] for s in SEEDS], ignore_index=True)
    print("\n=== pooled posterior (4 chains, post-burn, thinned) ===")
    for c in ["thermal_alpha", "fpc1", "fpc2", "fpc3", "ais_gmst_amp"]:
        if c in pool:
            q = pool[c].quantile([.05, .5, .95]).values
            print(f"  {c:28s} median {q[1]:+.4f}   [5,95]=[{q[0]:+.4f}, {q[2]:+.4f}]   sd {pool[c].std():.4f}")
    te = pool["thermal_alpha"].values
    print("\n=== te_alpha <-> forcing coupling (pooled) ===")
    for k in (1, 2, 3):
        print(f"  corr(te_alpha, fpc{k}) = {np.corrcoef(te, pool[f'fpc{k}'].values)[0,1]:+.3f}")

    verdict = "PASS (all R-hat < 1.05)" if n_bad == 0 else f"CHECK — {n_bad} params R-hat >= 1.05"
    print(f"\nCONVERGENCE: {verdict}")
    out = os.path.join(MCMC, "rhat_jcont_summary.csv")
    pd.DataFrame({"param": list(rhats.keys()), "rhat": list(rhats.values())}).to_csv(out, index=False)
    print(f"wrote {os.path.relpath(out, REPO)}")


if __name__ == "__main__":
    main()
