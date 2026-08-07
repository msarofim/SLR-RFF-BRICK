#!/usr/bin/env python3
"""
Per-draw gate evaluation for extB3-family tuning chains (handoff_2026-08-07 §3).

Applies the pre-registered gates to MCMC chain draws (2nd half), reusing the D0
machinery verbatim (d0_glacier_shootout.py, imported by exec like
d0_final_selfconsistent.py — no new math):

  A2 inventory   gic_a − S_raw(2000) ~ N(0.290, 0.060), |z| < 1
  A2b / S(1900)  S_raw(1900) in 10–30 mm
  GMIP3 ladder   committed % of 2020 mass at glacier-T = AMP_G×{1.2,1.5,2,3} K
                 inside likely ranges (evaluation-only, never in the likelihood)
  spread         glacier ΔS@2100 (rel 1995–2014) SSP1-2.6→5-8.5 in 4.5–13.5 cm
  bounds         gic params interior (>2% of range from lo/hi); gic_nu pile at 0
  mixing         acceptance vs 0.234; ESS with maxlag = full chain length
                 (feedback_mcmc_ess_maxlag_trap — never a default-capped maxlag)

Driver conventions (match calibrate_mcmc_ext.jl, NOT the shootout's ampfit tail):
  hindcast   = obs t_glac through 2024, then AMP_G × GMST anchor-preserving
               splice (anchor 2014–2024) — only affects the 2025–26 tail
  projection = obs t_glac + AMP_G × scenario-GMST splice, same anchor window

Wiggle-mode co-indicators (handoff §2 item 7): sd_gsic collapsing toward its
floor + gic_nu piling at 0 + S(1900) > 40 mm — reported, not gated.

Usage: eval_chain_gates.py [chain_csv] [--n-eval N] [--self-test]
Defaults to CHAIN_DEFAULT below. Outputs outputs/eval_gates_<tag>.csv +
figures/eval_gates_<tag>.png + console verdict table.
"""
import argparse
import os
import re
import subprocess

import numpy as np
import pandas as pd

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
SHOOTOUT = os.path.join(REPO, "python/d0_glacier_shootout.py")
CHAIN_DEFAULT = os.path.join(REPO, "outputs/mcmc/chain_extB3_seed2026_n500000.csv")
N_EVAL_DEFAULT = 2000          # per-draw forward sims (evenly spaced, 2nd half)
AMP_G = 1.8                    # calibrate_mcmc_ext.jl AMP_G (locked 2026-08-07)
BOUND_INTERIOR_FRAC = 0.02     # "interior" = >2% of range from lo/hi (gate table)
NU_PILE_EPS = 0.05             # gic_nu < this counts as "piled at 0"
S1900_WIGGLE_MM = 40.0         # S(1900) above this flags the wiggle-tracking mode

# calibrator sampling bounds (calibrate_mcmc_ext.jl FREE gic block) — NOT the
# shootout's offline BOUNDS, which differ for b and parameterize kappa linearly
CAL_BOUNDS = {
    "gic_a": (0.25, 0.70),
    "gic_b": (0.08, 0.70),
    "gic_T_off": (-2.00, -0.10),
    "gic_log10_kappa": (-4.00, -0.50),
    "gic_nu": (0.00, 2.50),
}
GIC_COLS = list(CAL_BOUNDS)
NOISE_COLS = ["sd_gsic", "rho_gsic"]

src = open(SHOOTOUT).read().split(
    "# ------------------------------------------------------------------ run all cells")[0]
exec(src.replace('print(f"D0', 'pass # print(f"D0'))

# NB: the exec rebinds OUT_CSV/OUT_FIG to the shootout's paths — ours are set in main()
COMMIT = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True).stdout.strip()

# hindcast driver, calibrator convention (AMP_G tail splice, anchor 2014–2024 =
# extend_obs's 11-yr window). DRIVERS["Tglac"] from the exec keeps the ampfit tail
# and is NOT used here.
DRV_CAL = extend_obs(tglac_obs, fair_rb, AMP_G)
TARR_CAL = DRV_CAL.to_numpy()[:-1]


def theta_of(row):
    return dict(a=row["gic_a"], b=row["gic_b"], T_off=row["gic_T_off"],
                kappa=10.0 ** row["gic_log10_kappa"], nu=row["gic_nu"])


def draw_metrics(row):
    th = theta_of(row)
    s_raw = forward("N", TARR_CAL, th)
    s1900 = 1000 * s_raw[i1900]
    invz = (th["a"] - s_raw[i_inv] - INV_V) / INV_SIG
    com, sens = ladder(th, s_raw[i2020], AMP_G)
    ds = scenario_ds2100("N", "Tglac", th, AMP_G)
    spread = ds["ssp585"] - ds["ssp126"]
    gates = dict(
        g_s1900=S1900_GATE_MM[0] <= s1900 <= S1900_GATE_MM[1],
        g_inv=abs(invz) < 1,
        g_lad=all(GMIP3_LIKELY[L][0] <= com[L] <= GMIP3_LIKELY[L][1]
                  for L in GMIP3_LEVELS),
        g_spread=4.5 <= spread <= 13.5,
    )
    return dict(
        **{k: row[k] for k in GIC_COLS},
        S1900_mm=s1900, inv_z=invz, S2020_mm=1000 * s_raw[i2020],
        **{f"com{str(L).replace('.', 'p')}": com[L] for L in GMIP3_LEVELS},
        sens_mm=sens, ds126=ds["ssp126"], ds245=ds["ssp245"], ds585=ds["ssp585"],
        ds245_2150=ds["ssp245_2150"], spread=spread, **gates,
        npass=sum(gates.values()),
    )


def ess_geyer(x):
    """ESS via Geyer's initial monotone positive sequence, autocovariance by FFT
    over the FULL lag range (the maxlag trap: a capped default floors ESS)."""
    x = np.asarray(x, float)
    n = len(x)
    x = x - x.mean()
    if np.allclose(x, 0):
        return float(n)
    nfft = int(2 ** np.ceil(np.log2(2 * n)))
    f = np.fft.rfft(x, nfft)
    acov = np.fft.irfft(f * np.conj(f), nfft)[:n].real / n
    rho = acov / acov[0]
    # pair sums Γ_k = ρ(2k) + ρ(2k+1); keep while positive, enforce monotone decrease
    npair = n // 2
    gam = rho[0:2 * npair:2] + rho[1:2 * npair:2]
    pos = np.nonzero(gam <= 0)[0]
    gam = gam[:pos[0]] if len(pos) else gam
    gam = np.minimum.accumulate(gam)
    tau = max(-1.0 + 2.0 * gam.sum(), 1.0 / n)
    return n / tau


def gate_report(res, chain2, accept, tag, n_second_half):
    print(f"\n=== gate verdicts ({tag}, 2nd half, {len(res)} evaluated draws) ===")
    gate_rows = [
        ("A2 inventory |z|<1", "inv_z", (-1, 1), "g_inv"),
        ("S(1900) 10-30 mm", "S1900_mm", S1900_GATE_MM, "g_s1900"),
        ("spread 4.5-13.5 cm", "spread", (4.5, 13.5), "g_spread"),
    ]
    for label, col, band, gcol in gate_rows:
        q = res[col].quantile([0.05, 0.5, 0.95])
        ok = band[0] <= q[0.5] <= band[1]
        print(f"  {label:24s} median {q[0.5]:8.2f} [{q[0.05]:7.2f},{q[0.95]:7.2f}]"
              f"  pass-frac {res[gcol].mean():.2f}  -> {'PASS' if ok else 'FAIL'} (median)")
    lad_ok = True
    for L in GMIP3_LEVELS:
        col = f"com{str(L).replace('.', 'p')}"
        lo, hi = GMIP3_LIKELY[L]
        q = res[col].quantile([0.05, 0.5, 0.95])
        ok = lo <= q[0.5] <= hi
        lad_ok &= ok
        print(f"  ladder @{L}K in [{lo},{hi}]"
              f"{'':<{max(0, 8 - len(str(L)))}} median {q[0.5]:8.1f}"
              f" [{q[0.05]:7.1f},{q[0.95]:7.1f}]  (lit central {GMIP3_CENTRAL[L]})"
              f"  -> {'PASS' if ok else 'FAIL'}")
    print(f"  ladder joint pass-frac {res['g_lad'].mean():.2f}"
          f"  -> {'PASS' if lad_ok else 'FAIL'} (all medians)")
    print(f"  sens 1.5->3K (report)    median {res['sens_mm'].median():8.1f} mm"
          f"  (lit ~{GMIP3_SENS_MM} mm)")
    print(f"  ds245@2100 (report)      median {res['ds245'].median():8.1f} cm"
          f"  (AR6 median {AR6_GLAC_2100['ssp245']})")
    print(f"  all-4 joint pass-frac    {(res['npass'] == 4).mean():.2f}")

    print("\n=== bounds & mixing ===")
    print(f"  acceptance {accept:.3f} (target ~0.234)")
    for c in GIC_COLS:
        lo, hi = CAL_BOUNDS[c]
        rng = hi - lo
        x = chain2[c]
        med = x.median()
        d_lo, d_hi = (med - lo) / rng, (hi - med) / rng
        frac_nb = (((x - lo) < BOUND_INTERIOR_FRAC * rng) |
                   ((hi - x) < BOUND_INTERIOR_FRAC * rng)).mean()
        interior = min(d_lo, d_hi) > BOUND_INTERIOR_FRAC
        ess = ess_geyer(x.to_numpy())
        print(f"  {c:16s} median {med:8.3f}  dist-to-bound {100 * min(d_lo, d_hi):5.1f}%"
              f"  near-bound frac {frac_nb:.3f}  ESS {ess:7.0f}"
              f"  -> {'PASS' if interior else 'FAIL'}")
    lp_ess = (ess_geyer(chain2["log_post"].to_numpy())
              if "log_post" in chain2 else np.nan)
    print(f"  log_post ESS {lp_ess:.0f}  (n 2nd-half = {n_second_half})")

    print("\n=== wiggle-mode co-indicators (report-only, handoff item 7) ===")
    print(f"  P(gic_nu < {NU_PILE_EPS}) = {(chain2['gic_nu'] < NU_PILE_EPS).mean():.3f}")
    for c in NOISE_COLS:
        if c in chain2:
            print(f"  {c} median {chain2[c].median():.4f}  q05 {chain2[c].quantile(0.05):.4f}")
    print(f"  P(S1900 > {S1900_WIGGLE_MM:.0f} mm) = {(res['S1900_mm'] > S1900_WIGGLE_MM).mean():.3f}")


def make_figure(res, out_fig, tag):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 4, figsize=(17, 4.2), constrained_layout=True)
    a1, a2, a3, a4 = axes
    a1.hist(res["S1900_mm"], bins=40, color="tab:green", alpha=0.8)
    a1.axvspan(*S1900_GATE_MM, color="tab:green", alpha=0.15)
    a1.set(xlabel="S(1900) mm (band = gate)", title="A2b")
    a2.hist(res["inv_z"], bins=40, color="tab:blue", alpha=0.8)
    a2.axvspan(-1, 1, color="tab:blue", alpha=0.15)
    a2.set(xlabel="inventory z (band = gate)", title="A2")
    for L in GMIP3_LEVELS:
        lo, hi = GMIP3_LIKELY[L]
        a3.fill_between([L - 0.08, L + 0.08], [lo] * 2, [hi] * 2, color="k", alpha=0.10)
        a3.plot([L - 0.08, L + 0.08], [GMIP3_CENTRAL[L]] * 2, color="k", lw=1.6)
    cols = [f"com{str(L).replace('.', 'p')}" for L in GMIP3_LEVELS]
    q = res[cols].quantile([0.05, 0.5, 0.95])
    a3.errorbar(GMIP3_LEVELS, q.loc[0.5],
                yerr=[q.loc[0.5] - q.loc[0.05], q.loc[0.95] - q.loc[0.5]],
                fmt="o-", color="tab:red", capsize=3, label="posterior median [5,95]")
    a3.set(xlabel="global warming level (K)", ylabel="committed % of 2020 mass",
           title=f"GlacierMIP3 ladder (amp {AMP_G})")
    a3.legend(fontsize=8)
    a4.hist(res["spread"], bins=40, color="tab:red", alpha=0.8)
    a4.axvspan(4.5, 13.5, color="tab:red", alpha=0.12)
    a4.set(xlabel="SSP126→585 ΔS@2100 spread, cm (band = gate)", title="scenario spread")
    fig.suptitle(f"chain gate evaluation — {tag} | commit {COMMIT} | "
                 f"{len(res)} draws (2nd half) | amp_g {AMP_G}", fontsize=10)
    fig.savefig(out_fig, dpi=150)


def self_test():
    """Plumbing check against the D0-final C_nu1.0 row (SC point, fitted κ at
    ν=1): hindcast metrics must match EXACTLY (S1900 21.309 mm, inv_z 0.353 —
    the driver-tail and amp conventions only differ after 2024), ladder/spread
    must pass their gates (evaluated at amp 1.8 here vs ampfit in the D0 row)."""
    sc = dict(gic_a=0.383, gic_b=0.28634, gic_T_off=-0.95661,
              gic_log10_kappa=np.log10(0.00607), gic_nu=1.0)
    m = draw_metrics(sc)
    com1850 = seq_of(theta_of(sc), 0.0)
    print(f"self-test @ D0 C_nu1.0 point: committed@1850 = {com1850:.3f} m (expect ~0.094)")
    for k in ["S1900_mm", "inv_z", "com1p2", "com2p0", "sens_mm",
              "ds245", "spread", "npass"]:
        print(f"  {k:10s} {m[k]:8.3f}")
    assert abs(m["S1900_mm"] - 21.309) < 0.05, "S1900 mismatch vs d0_final C_nu1.0"
    assert abs(m["inv_z"] - 0.353) < 0.01, "inv_z mismatch vs d0_final C_nu1.0"
    assert m["npass"] == 4, "C_nu1.0 point must pass all 4 gates (D0-final result)"
    print("self-test PASS (hindcast metrics match d0_final; 4/4 gates)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("chain", nargs="?", default=CHAIN_DEFAULT)
    ap.add_argument("--n-eval", type=int, default=N_EVAL_DEFAULT)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return

    m = re.search(r"chain_(.+?)_seed(\d+)_n(\d+)\.csv", os.path.basename(args.chain))
    tag = f"{m.group(1)}_seed{m.group(2)}" if m else "chain"
    out_csv = os.path.join(REPO, f"outputs/eval_gates_{tag}.csv")
    out_fig = os.path.join(REPO, f"figures/eval_gates_{tag}.png")

    chain = pd.read_csv(args.chain)
    chain2 = chain.iloc[len(chain) // 2:].reset_index(drop=True)
    accept = (float(chain["accept_rate"].iloc[-1]) if "accept_rate" in chain
              else float("nan"))
    idx = np.unique(np.linspace(0, len(chain2) - 1, args.n_eval).astype(int))
    print(f"eval_chain_gates | commit={COMMIT} | chain={os.path.relpath(args.chain, REPO)}"
          f"\n  {len(chain)} iters -> 2nd half {len(chain2)}, evaluating {len(idx)} draws"
          f" | driver: t_glac obs + {AMP_G}xGMST splice (calibrator convention)")

    res = pd.DataFrame([draw_metrics(chain2.iloc[i]) for i in idx])
    res.to_csv(out_csv, index=False, float_format="%.5f")
    gate_report(res, chain2, accept, tag, len(chain2))
    make_figure(res, out_fig, tag)
    print(f"\nWrote {os.path.relpath(out_csv, REPO)} and {os.path.relpath(out_fig, REPO)}")


if __name__ == "__main__":
    main()
