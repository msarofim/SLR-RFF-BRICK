#!/usr/bin/env python3
"""
brickf_committed_ladder.py — the posterior's committed glacier loss against
GlacierMIP3, on both denominators.

"Committed loss" is the fraction of the 2020 glacier mass that is already
destined to melt at a sustained global warming level, the quantity GlacierMIP3
reports. For a reservoir with equilibrium curve S_eq(T) = a (1 - exp(-b(T-T_off)))
and stock already lost by 2020 S_2020,

    committed(L) = 100 * (S_eq(amp * L) - S_2020) / (a - S_2020).

S_2020 can be taken two ways, and they answer different questions:

  DATA basis   S_2020 from the observed GlaMBIE cumulative loss
               (outputs/extc_block_constants.csv). This is the denominator the
               calibration likelihood uses, so it is the basis on which the
               model was asked to match GlacierMIP3.
  MODEL basis  S_2020 as the calibrated model itself simulates it
               (outputs/eval_gates_extC_seed2026.csv, per chain draw). This is
               what the model would report as its own committed fraction.

The two differ because the posterior does not reproduce the observed 2020 stock
exactly; reporting only one of them hides that. Per-reservoir figures are also
given, because the likelihood constrains the ladder per reservoir, not in
aggregate.

  python3 python/brickf_committed_ladder.py
Writes outputs/brickf_committed_ladder.csv
"""
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTERIOR = os.path.join(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_extC.csv")
CONSTANTS = os.path.join(REPO, "outputs/extc_block_constants.csv")
GATES = os.path.join(REPO, "outputs/eval_gates_extC_seed2026.csv")
OUT = os.path.join(REPO, "outputs/brickf_committed_ladder.csv")

BLOCKS = ["R19", "SLOWP", "FAST"]
LEVELS = [1.2, 1.5, 2.0, 3.0]
# GlacierMIP3 assessed committed loss, scope-corrected to the reservoirs' region
# set (Zekollari 2025 / Zenodo 15046588; python/t2_gmip3_scope_anchor.py).
GMIP3_LIKELY = {1.2: (11.8, 54.0), 1.5: (17.2, 63.2),
                2.0: (41.5, 75.5), 3.0: (58.5, 83.9)}
GMIP3_CENTRAL = {1.2: 37.4, 1.5: 46.3, 2.0: 63.0, 3.0: 75.5}


def s_eq(a, b, T_off, T):
    return a * (1 - np.exp(-b * (T - T_off)))


def main():
    post = pd.read_csv(POSTERIOR)
    bc = pd.read_csv(CONSTANTS).set_index("block")
    gates = pd.read_csv(GATES)

    s2020_data = {b: float(bc.loc[b, "S2020_data"]) for b in BLOCKS}
    a = {b: post[f"gic_a_{b}"].to_numpy() for b in BLOCKS}
    rows = []

    print("Committed glacier loss, % of 2020 mass — BRICK-F* posterior "
          f"({len(post)} draws)\n")

    # ---- per reservoir, data basis (what the likelihood constrains) ----------
    print("PER RESERVOIR (data basis: observed 2020 stock)")
    print(f"  {'':7s} " + "  ".join(f"{L:>18.1f} K" for L in LEVELS))
    for b in BLOCKS:
        line = f"  {b:7s}"
        for L in LEVELS:
            eq = s_eq(a[b], post[f"gic_b_{b}"].to_numpy(),
                      post[f"gic_T_off_{b}"].to_numpy(),
                      post[f"gic_amp_{b}"].to_numpy() * L)
            com = 100 * (eq - s2020_data[b]) / (a[b] - s2020_data[b])
            q = np.percentile(com, [5, 50, 95])
            key = str(L).replace(".", "p")
            central = float(bc.loc[b, f"com{key}"])
            sigma = float(bc.loc[b, f"sig{key}"])
            z = (q[1] - central) / sigma
            line += f"  {q[1]:5.1f} [{q[0]:5.1f},{q[2]:5.1f}] z{z:+.2f}"
            rows.append(dict(scope=b, basis="data", level_K=L, med=q[1], p05=q[0], p95=q[2],
                             gmip3_central=central, gmip3_sigma=sigma, z=z))
        print(line)
    print("  z = (posterior median - GlacierMIP3 central) / rung sigma; the likelihood")
    print("  constrains exactly these per-reservoir rungs.")
    print()

    # ---- aggregate, both bases ----------------------------------------------
    a_total = sum(a[b] for b in BLOCKS)
    s2020_data_total = sum(s2020_data.values())
    s2020_model = gates["S2020_all_mm"].to_numpy() / 1000.0     # mm -> m SLE
    print(f"AGGREGATE — 2020 stock: data {1000 * s2020_data_total:.1f} mm, "
          f"model median {np.median(gates['S2020_all_mm']):.1f} mm "
          f"({len(gates)} chain draws)")
    print(f"  {'basis':12s} " + "  ".join(f"{L:>16.1f} K" for L in LEVELS))
    for basis in ("data", "model"):
        line = f"  {basis:12s}"
        for L in LEVELS:
            eq_total = sum(s_eq(a[b], post[f"gic_b_{b}"].to_numpy(),
                                post[f"gic_T_off_{b}"].to_numpy(),
                                post[f"gic_amp_{b}"].to_numpy() * L) for b in BLOCKS)
            if basis == "data":
                com = 100 * (eq_total - s2020_data_total) / (a_total - s2020_data_total)
            else:
                # model 2020 stock comes from a different (chain-draw) sample, so
                # pair its median with the posterior spread rather than element-wise
                s = np.median(s2020_model)
                com = 100 * (eq_total - s) / (a_total - s)
            q = np.percentile(com, [5, 50, 95])
            inside = GMIP3_LIKELY[L][0] <= q[1] <= GMIP3_LIKELY[L][1]
            line += f"  {q[1]:5.1f} [{q[0]:5.1f},{q[2]:5.1f}]{'' if inside else '*'}"
            rows.append(dict(scope="aggregate", basis=basis, level_K=L, med=q[1],
                             p05=q[0], p95=q[2], gmip3_central=GMIP3_CENTRAL[L],
                             gmip3_sigma=np.nan, z=np.nan))
        print(line)
    line = f"  {'GlacierMIP3':12s}"
    for L in LEVELS:
        line += f"  {GMIP3_CENTRAL[L]:5.1f} [{GMIP3_LIKELY[L][0]:5.1f},{GMIP3_LIKELY[L][1]:5.1f}]"
    print(line)
    print("  * median outside the GlacierMIP3 likely range")

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
