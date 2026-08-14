#!/usr/bin/env python3
"""
diag_d1_vs_l10.py — what the D1 arm (total stream dropped) changes, and the two
questions it was run to answer.

D1 short chains: `calibrate_mcmc_ext.jl <n> <seed> --drop-total --overdisperse
--tag=D1`, 4 seeds, 53 sampled parameters (55 minus sd_dang/rho_dang).

QUESTION 1 (spec_2026-08-14_next_calibration.md §7.2) — the decisive R19 test.
Dropping the total leaves the R19 glacier block with no sea-level-timeseries
constraint at all: it is excluded from HIND_BLOCKS, so it has no gsic-component
term and, since the GlaMBIE restructure, no absolute modern-rate term either.
Only its GlacierMIP3 rung likelihood, the A2 inventory term and its priors remain.
The spec's width-ratio argument (posterior sd / prior sd = 0.95 on gic_b_R19)
CANNOT distinguish "the total constrains R19 weakly" from "rung + inventory
already do it". This chain can: if the R19 marginals move materially, the drop
needs an R19 replacement term before production.

QUESTION 2 (Marcus 2026-08-14) — thermal expansion. TE is the ONE module where
Ladrillo is worse than BRICK 2.0 (RMSE ratio 1.32 / 1.25 / 0.73 over
1920-1949 / 1950-1992 / 1993-2026), with a positive bias in all three windows,
and it has the worst band coverage (29% against nominal 90%). `thermal_alpha`
sits at 0.0986 against 0.1043 observationally implied. The question is whether
the total stream was pulling it, i.e. whether D1 fixes TE for free.

THE TE ALGEBRA IS EXACT, WHICH MAKES THIS FREE. MimiBRICK's thermal_expansion is

    te_sea_level[t] = te_sea_level[t-1] + Δ_oceanheat[t] · te_α / (te_A · te_C · te_ρ²)

i.e. te_sea_level = te_s₀ + te_α · S(t) with S fixed by the OHC forcing alone,
and te_s₀ = 0.0 in MimiBRICK's own defaults and not sampled. Re-referencing to
1995-2005 removes any constant anyway. So the modelled steric anomaly is EXACTLY
PROPORTIONAL to `thermal_alpha`, and the median is too (the median is equivariant
under the monotone map α ↦ cα, including c < 0). The steric bias in any window is
therefore an exact linear function of `thermal_alpha` — no model run needed, and
the α that zeroes any bias metric is solvable in closed form.

That proportionality is GATED here against the recorded L10 posterior-predictive
rather than assumed.

  source ~/climate-env/bin/activate
  python3 python/diag_d1_vs_l10.py
Writes outputs/diag_d1_vs_l10.csv
"""
import glob
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBS = os.path.join(REPO, "data/observations")
OUT = os.path.join(REPO, "outputs/diag_d1_vs_l10.csv")

D1_GLOB = os.path.join(REPO, "outputs/mcmc/chain_D1_seed*.csv")
L10_SUB = os.path.join(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_L10.csv")
L10_CHAINS = os.path.join(REPO, "outputs/mcmc/chain_L10_seed*.csv")
L10_POSTPRED = os.path.join(REPO, "outputs/postpred_L10_components_timeseries.csv")
TARGETS = os.path.join(REPO, "outputs/recalib_targets_ext.csv")
FORCING_TAG = "ssp245harm"                 # must match calibrate_mcmc_ext.jl
OHC_CSV = os.path.join(OBS, f"fair_mean_ohc_{FORCING_TAG}.csv")

BURN_FRAC = 0.5                            # discard the first half of each D1 chain
FIT_REF = (1995, 2005)                     # calibration re-reference window
R19_PARAMS = ["gic_a_R19", "gic_b_R19", "gic_T_off_R19", "gic_log10_kappa_R19",
              "gic_amp_R19"]
MOVE_SIGMA_FLAG = 0.5                      # |shift| in L10 sd above which we flag
# A flagged shift is only REPORTABLE if it also exceeds the between-chain
# disagreement in both arms by this factor. Without this gate a parameter the
# chains have not agreed on (ais_iceflow0, R-hat 2.359) reads as a finding.
MIX_RATIO_MIN = 2.0
# MimiBRICK v2.0.0 thermal_expansion constants (src/MimiBRICK.jl L121-125)
TE_A, TE_C, TE_RHO, TE_S0 = 3.619e14, 3991.86795711963, 1027.0, 0.0
WINDOWS = [("1920-1949", (1920, 1949)), ("1950-1992", (1950, 1992)),
           ("1993-2026", (1993, 2026)), ("full", (1900, 2026))]


def per_chain_medians(pattern, param, stride=1):
    """Post-burn median of `param` in each chain separately — the only way to tell
    a real posterior shift from a parameter the chains have not agreed on."""
    out = {}
    for f in sorted(glob.glob(pattern)):
        d = pd.read_csv(f, usecols=[param])
        d = d.iloc[len(d) // 2::stride]
        out[os.path.basename(f).split("seed")[1][:4]] = float(d[param].median())
    return out


def mixing_verdict(param, shift_abs):
    """Is a between-arm shift bigger than the between-CHAIN disagreement in either
    arm? If not, the shift is not resolved at this chain length and must not be
    reported as a finding. L10 is read at stride 100 (2.2 GB chains)."""
    d1 = per_chain_medians(D1_GLOB, param)
    l10 = per_chain_medians(L10_CHAINS, param, stride=100)
    spread = max(max(d1.values()) - min(d1.values()),
                 max(l10.values()) - min(l10.values()))
    ratio = shift_abs / spread if spread > 0 else np.inf
    return d1, l10, spread, ratio


def load_d1():
    files = sorted(glob.glob(D1_GLOB))
    if not files:
        raise SystemExit(f"no D1 chains at {D1_GLOB} — run the --drop-total chains first")
    parts = []
    for f in files:
        d = pd.read_csv(f)
        parts.append(d.iloc[int(len(d) * BURN_FRAC):])
    out = pd.concat(parts, ignore_index=True)
    print(f"  D1: {len(files)} chains, {len(out)} post-burn draws "
          f"({int(BURN_FRAC * 100)}% burn), {out.shape[1]} columns")
    for c in ("sd_dang", "rho_dang"):
        if c in out.columns:
            raise SystemExit(f"D1 chain still carries {c} — the flag did not take")
    return out


def steric_shape():
    """S(t) in the re-referenced frame: te_sea_level/te_α, cm, rel FIT_REF."""
    o = pd.read_csv(OHC_CSV).set_index("year")["ohc_1e22J"]
    yrs = np.arange(1850, 2027)
    ohc = o.reindex(yrs).to_numpy()
    if not np.isfinite(ohc).all():
        raise SystemExit(f"{os.path.basename(OHC_CSV)} does not cover 1850-2026")
    # the component's own recursion, with te_α factored out
    dq = np.diff(ohc, prepend=ohc[0]) * 1e22
    s_m = TE_S0 + np.cumsum(dq) / (TE_A * TE_C * TE_RHO ** 2)
    s_cm = 100.0 * s_m
    ib = (yrs >= FIT_REF[0]) & (yrs <= FIT_REF[1])
    return pd.Series(s_cm - s_cm[ib].mean(), index=yrs)


def main():
    print("D1 (total stream dropped) vs L10\n")
    d1 = load_d1()
    l10 = pd.read_csv(L10_SUB)
    print(f"  L10: {len(l10)} subsample draws\n")

    rows = []
    print("  QUESTION 1 — R19 marginals (the block that loses its last SLR constraint)")
    print(f"  {'parameter':22s} {'L10 med':>10s} {'D1 med':>10s} {'shift/L10sd':>12s} "
          f"{'sd ratio':>9s}")
    for p in R19_PARAMS:
        if p not in d1.columns or p not in l10.columns:
            print(f"  {p:22s}  MISSING")
            continue
        lm, ls = float(l10[p].median()), float(l10[p].std())
        dm, ds = float(d1[p].median()), float(d1[p].std())
        shift = (dm - lm) / ls if ls > 0 else np.nan
        rows.append(dict(question="R19", parameter=p, l10_med=lm, l10_sd=ls,
                         d1_med=dm, d1_sd=ds, shift_in_l10_sd=shift,
                         sd_ratio=ds / ls if ls > 0 else np.nan))
        flag = "  <-- MOVED" if abs(shift) > MOVE_SIGMA_FLAG else ""
        print(f"  {p:22s} {lm:10.4f} {dm:10.4f} {shift:+12.2f} "
              f"{ds / ls:9.2f}{flag}")

    moved = [r for r in rows if abs(r["shift_in_l10_sd"]) > MOVE_SIGMA_FLAG]
    print(f"\n  {len(moved)} of {len(rows)} R19 marginals move more than "
          f"{MOVE_SIGMA_FLAG} L10 sd. Mixing gate on each:")
    real = []
    for r in moved:
        d1c, l10c, spread, ratio = mixing_verdict(r["parameter"],
                                                  abs(r["d1_med"] - r["l10_med"]))
        ok = ratio >= MIX_RATIO_MIN
        real.append(ok)
        print(f"    {r['parameter']}: shift {abs(r['d1_med'] - r['l10_med']):.3f} vs "
              f"worst between-chain spread {spread:.3f}  ->  {ratio:.1f}x  "
              f"{'REAL' if ok else 'NOT RESOLVED at this chain length'}")
        print(f"      D1  per chain: " +
              ", ".join(f"{k} {v:+.3f}" for k, v in d1c.items()))
        print(f"      L10 per chain: " +
              ", ".join(f"{k} {v:+.3f}" for k, v in l10c.items()))
    print("\n  VERDICT: " + ("The width-ratio reading in spec §2.2 HOLDS — the total "
          "was not constraining R19." if not any(real) else
          "The drop DOES move R19, and the move survives the mixing gate.\n  "
          "Spec §2.2's width-ratio reading was the wrong one: D1 needs an R19\n  "
          "replacement term before production."))

    # ---- everything else that moved, so the R19 answer is not read in isolation
    print(f"\n  Other parameters moving more than {MOVE_SIGMA_FLAG} L10 sd")
    common = [c for c in l10.columns if c in d1.columns and c not in R19_PARAMS]
    others = []
    for p in common:
        ls = float(l10[p].std())
        if ls <= 0:
            continue
        shift = (float(d1[p].median()) - float(l10[p].median())) / ls
        others.append((abs(shift), p, shift, float(d1[p].std()) / ls))
    others.sort(reverse=True)
    print("  (each also passed through the mixing gate — a shift smaller than the")
    print(f"   between-chain disagreement is NOT a finding)")
    for a, p, shift, sdr in others:
        if a <= MOVE_SIGMA_FLAG:
            continue
        lm, dm = float(l10[p].median()), float(d1[p].median())
        _, _, spread, ratio = mixing_verdict(p, abs(dm - lm))
        ok = ratio >= MIX_RATIO_MIN
        print(f"  {p:22s} shift {shift:+6.2f} L10 sd   sd ratio {sdr:5.2f}   "
              f"mixing {ratio:4.1f}x  {'REAL' if ok else 'NOT RESOLVED'}")
        rows.append(dict(question="other" if ok else "other_unresolved", parameter=p,
                         l10_med=lm, l10_sd=float(l10[p].std()), d1_med=dm,
                         d1_sd=float(d1[p].std()), shift_in_l10_sd=shift, sd_ratio=sdr))
    if not any(a > MOVE_SIGMA_FLAG for a, *_ in others):
        print("  (none)")

    # ---- QUESTION 2: thermal expansion, exactly ------------------------------
    S = steric_shape()
    pp = pd.read_csv(L10_POSTPRED).set_index("year")
    a_l10 = float(l10["thermal_alpha"].median())
    a_d1 = float(d1["thermal_alpha"].median())

    # GATE: the recorded L10 te_p50 must equal a_l10 * S(t) if the algebra holds
    yrs = pp.index.intersection(S.index)
    pred = a_l10 * S.reindex(yrs)
    err = float((pp.loc[yrs, "te_p50"] - pred).abs().max())
    print(f"\n  QUESTION 2 — thermal expansion")
    print(f"  proportionality gate: max |te_p50 - alpha_L10 * S(t)| = {err:.4f} cm")
    if err > 0.05:
        raise SystemExit("GATE FAILED — te_sea_level is not behaving as "
                         "alpha * S(t); the closed-form TE result below would be "
                         "unsound, so it is not printed.")
    print("  PASSED — the steric series is exactly proportional to thermal_alpha, "
          "so the\n  bias below is exact, not simulated.")

    obs = pd.read_csv(TARGETS).set_index("year")["steric"].reindex(yrs)
    print(f"\n  thermal_alpha: L10 {a_l10:.5f} -> D1 {a_d1:.5f} "
          f"({(a_d1 - a_l10) / float(l10['thermal_alpha'].std()):+.2f} L10 sd)")
    print(f"  {'window':12s} {'L10 bias':>10s} {'D1 bias':>10s} {'alpha* (zero bias)':>20s}")
    for wn, (y0, y1) in WINDOWS:
        m = (yrs >= y0) & (yrs <= y1) & obs.notna()
        if m.sum() == 0:
            continue
        s, o = S.reindex(yrs)[m], obs[m]
        b_l10, b_d1 = float((a_l10 * s - o).mean()), float((a_d1 * s - o).mean())
        astar = float(o.mean() / s.mean()) if s.mean() != 0 else np.nan
        rows.append(dict(question="TE", parameter=wn, l10_med=b_l10, l10_sd=np.nan,
                         d1_med=b_d1, d1_sd=np.nan, shift_in_l10_sd=np.nan,
                         sd_ratio=astar))
        print(f"  {wn:12s} {b_l10:+10.3f} {b_d1:+10.3f} {astar:20.5f}")
    print("  (alpha* is the thermal_alpha that would zero that window's mean bias)")

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
