#!/usr/bin/env python3
"""Is the L27-vs-L32 full-period ranking SENSITIVE to the pre-1979 target sigma?

MOTIVATION (Marcus, 2026-09-24). If IMBIE-2026 is the better product over 1979-2023,
then Frederikse's AIS -- which supplies 62 % of the full-period scoring window, all of it
BEFORE 1979 where no satellite constraint exists -- carries a sigma that does not reflect
that doubt. L27's full-period win is earned almost entirely in that segment (1920-49:
0.08 sigma vs L32's 1.07). So: how much would the pre-1979 sigma have to be inflated
before L32 catches L27, and is that factor reachable from measured evidence?

THE STATISTIC. The benchmark reports  RMSE_cm(window) / sigma_bar , a SCALAR denominator
(bench_ladrillo.py:682, 1309). This generalises it to a per-year denominator:

    Z(F) = sqrt( mean_y [ ( (p50_y - obs_y) / sigma_y(F) )^2 ] ),
    sigma_y(F) = F * sigma_bar  for y <  SPLICE_START
                     sigma_bar  for y >= SPLICE_START

At F = 1 this is IDENTICALLY the published statistic, which is the gate below: if it does
not reproduce 0.70 / 0.88 the statistic is not understood and the run aborts.

CONVENTIONS MATCHED TO THE BENCH, NOT REINVENTED: obs from the LIVE target, sigma_bar from
the FROZEN _fixed copy (so sigma stays comparable across bench files), and the year index
intersected with BRICK 2.0's exactly as block [H] does.

This is a SCORING sensitivity, not a refit: it asks whether the RANKING is sigma-sensitive
before anyone spends a refit on it. It does NOT change the standing ruler.
"""
import hashlib, sys
import numpy as np, pandas as pd

# --- named constants; every label and message below derives from these -------------
SPLICE_START   = 1979          # first year the two target builds differ in DATA
CHECK_WINDOW   = (1979, 2017)  # where Frederikse's sigma is CHECKABLE against IMBIE:
                               # satellite-constrained and before the 2019 sigma cliff
FULL_WINDOW    = (1900, 2026)
EARLY_WINDOW   = (1920, 1949)
PUBLISHED      = {"L27*": 0.70, "L32": 0.88}   # the gate, from the 09-24 one-ruler table
GATE_TOL       = 0.005
F_GRID         = np.arange(1.0, 6.01, 0.005)
DEAD_BAND      = 0.02          # bench_ladrillo.py direction(): two arms within 2 % of a
                               # metric are NOT distinguishable by it. So the honest question
                               # is when the arms become INDISTINGUISHABLE, not when L32 "wins".
MIN_NEFF       = 2.0           # below this the inflation factor has no error bar worth the
                               # name and NO verdict on reachability may be printed
LIVE_TARGET    = "outputs/recalib_targets_ext.csv"
FROZEN_TARGET  = "benchmark/reference/_fixed/recalib_targets_ext.csv"
BRICK_POSTPRED = "benchmark/reference/_fixed/postpred_oldbrick_components_timeseries.csv"
ARMS = {"L27*": "benchmark/reference/L27/postpred_components_timeseries.csv",
        "L32":  "outputs/postpred_L32_components_timeseries.csv"}
ALT_CHECK_WINDOWS = [(1993, 2017), (1992, 2018), (1979, 2018)]
OUT_CSV = "outputs/diag_ais_prescore_sigma_sensitivity.csv"

md5 = lambda p: hashlib.md5(open(p, "rb").read()).hexdigest()[:12]

def z_rmse(resid, years, F, sigma_bar):
    """sigma-weighted RMSE; F inflates the pre-SPLICE_START denominator only."""
    s = np.where(years < SPLICE_START, F * sigma_bar, sigma_bar)
    return float(np.sqrt(np.mean((resid / s) ** 2)))

def main():
    tg_live = pd.read_csv(LIVE_TARGET).set_index("year")
    tg_froz = pd.read_csv(FROZEN_TARGET).set_index("year")
    sigma_bar = float(((tg_froz.ais_hi - tg_froz.ais_lo) / (2 * 1.645)).mean())
    brick = pd.read_csv(BRICK_POSTPRED).set_index("year")

    print(f"AIS pre-{SPLICE_START} sigma sensitivity of the L27-vs-L32 full-period ranking")
    print(f"  live target   {LIVE_TARGET} md5 {md5(LIVE_TARGET)}   (obs)")
    print(f"  frozen target {FROZEN_TARGET} md5 {md5(FROZEN_TARGET)}   (sigma_bar)")
    print(f"  sigma_bar = {sigma_bar:.4f} cm   (mean per-year AIS sigma, whole record)\n")

    res, rows = {}, []
    for tag, path in ARMS.items():
        a = pd.read_csv(path).set_index("year")
        yrs = a.index.intersection(brick.index)                 # as block [H] does
        obs = tg_live.ais.reindex(yrs)
        p50 = a.ais_p50.reindex(yrs)
        m = obs.notna() & p50.notna()
        m &= (obs.index >= FULL_WINDOW[0]) & (obs.index <= FULL_WINDOW[1])
        res[tag] = (np.asarray((p50[m] - obs[m]).values, float),
                    np.asarray(obs[m].index.values, int))
        print(f"  {tag:5s}: n={m.sum()}  RMSE {np.sqrt((res[tag][0]**2).mean()):.4f} cm  "
              f"pre-{SPLICE_START} n={(res[tag][1] < SPLICE_START).sum()}")

    # ---- GATE: F=1 must reproduce the published one-ruler numbers -------------
    print(f"\nGATE -- at F=1 the statistic must reproduce the published sigma values:")
    bad = []
    for tag in ARMS:
        got = z_rmse(*res[tag], 1.0, sigma_bar)
        ok = abs(got - PUBLISHED[tag]) <= GATE_TOL
        print(f"  {tag:5s}: got {got:.4f}  published {PUBLISHED[tag]:.2f}  "
              f"{'OK' if ok else '*** MISMATCH ***'}")
        if not ok:
            bad.append(tag)
    if bad:
        sys.exit(f"GATE FAILED for {bad} -- the statistic is not the published one; STOP.")
    # ⚠ WHAT THIS GATE IS BLIND TO, mutation-tested 2026-09-24: it catches a wrong published
    # value or a wrong sigma_bar, but it CANNOT catch a wrong SPLICE_START -- at F = 1 the
    # denominator is uniform, so the splice year does not enter. SPLICE_START = 1979 is verified
    # independently by diag_target_divergence_frederikse_vs_imbie.py, which measures the two
    # builds as identical up to a CONSTANT before 1979 and divergent after. Do not read a pass
    # here as confirmation of the splice year.
    print("  => gate passed; the generalisation is exact at F=1\n")

    # ---- the measured inflation factor, from where Frederikse IS checkable ----
    # ⚠ THE TRAP THIS BLOCK EXISTS TO AVOID. The obvious move is RMS((IMBIE-Frederikse)/sigma)
    # over the checkable window and a comparison of that number against the break-even. But the
    # difference between two systematically-offset reconstructions is ONE SLOW CURVE, not N
    # independent samples: its lag-1 autocorrelation is ~0.97, so 39 years carry N_eff < 1 and the
    # point estimate has a 1-sd bar comparable to itself. A reachability verdict off the point
    # estimate alone is exactly the error ~/.claude/CLAUDE.md warns about, so it is GATED on N_eff.
    d = tg_live.ais - tg_froz.ais
    sig_f = (tg_froz.ais_hi - tg_froz.ais_lo) / (2 * 1.645)
    w = (d.index >= CHECK_WINDOW[0]) & (d.index <= CHECK_WINDOW[1])
    z = (d[w] / sig_f[w]).dropna().values
    rms_z = float(np.sqrt(np.mean(z ** 2)))
    rho = float(np.corrcoef(z[:-1], z[1:])[0, 1])
    n_eff = len(z) * (1 - rho) / (1 + rho)
    rse = 1 / np.sqrt(2 * max(n_eff, 1e-9))
    print(f"MEASURED inflation factor, from {CHECK_WINDOW[0]}-{CHECK_WINDOW[1]} "
          f"(satellite-constrained, pre-cliff):")
    print(f"  RMS( (IMBIE - Frederikse) / sigma_Frederikse ) = {rms_z:.2f}")
    print(f"  (1.00 if sigma is correctly sized; sqrt(2)={np.sqrt(2):.2f} if the two products were")
    print(f"   equally uncertain and independent -- so the factor is {rms_z/np.sqrt(2):.2f}-{rms_z:.2f})")
    print(f"  ⚠ lag-1 rho = {rho:.3f} over n = {len(z)} yr  =>  N_eff = {n_eff:.1f}")
    print(f"  ⚠ 1-sd bar on the factor: +/- {rms_z*rse:.2f}  =>  range "
          f"{max(rms_z-rms_z*rse,0):.2f} - {rms_z+rms_z*rse:.2f}")
    if n_eff < MIN_NEFF:
        print(f"  ⛔ N_eff {n_eff:.1f} < {MIN_NEFF} -- the discrepancy between two systematically")
        print(f"     offset products is ONE CURVE, not {len(z)} samples. This factor CANNOT be")
        print(f"     measured this way and NO reachability verdict is printed below.")
    print()

    print(f"  robustness of the factor to the checkable window:")
    for a_, b_ in ALT_CHECK_WINDOWS:
        ww = (d.index >= a_) & (d.index <= b_)
        zz = (d[ww] / sig_f[ww]).dropna().values
        print(f"    {a_}-{b_}: RMS z = {float(np.sqrt(np.mean(zz**2))):.2f}")
    print()

    # ---- the break-even sweep ------------------------------------------------
    cross = None
    for F in F_GRID:
        zs = {t: z_rmse(*res[t], F, sigma_bar) for t in ARMS}
        rows.append(dict(F=F, **{f"z_{t}": zs[t] for t in ARMS},
                         leader=min(zs, key=zs.get)))
        if cross is None and zs["L32"] <= zs["L27*"]:
            cross = F
    df = pd.DataFrame(rows)
    df["provenance"] = (f"diag_ais_prescore_sigma_sensitivity.py | obs {md5(LIVE_TARGET)} | "
                        f"sigma_bar {sigma_bar:.4f} from {md5(FROZEN_TARGET)} | "
                        f"F inflates pre-{SPLICE_START} sigma only | scoring-only, no refit")
    df.to_csv(OUT_CSV, index=False)

    print("SWEEP -- full-period sigma-weighted RMSE as the pre-1979 sigma is inflated:")
    print(f"  {'F':>5} {'L27*':>8} {'L32':>8}   leader")
    for F in (1.0, 1.25, 1.5, 1.72, 2.0, 2.5, 3.0, 4.0, 5.0):
        r = df.iloc[(df.F - F).abs().argmin()]
        print(f"  {r.F:5.2f} {r['z_L27*']:8.3f} {r.z_L32:8.3f}   {r.leader}")
    print()
    same = next((float(r.F) for _, r in df.iterrows()
                 if abs((r.z_L32 - r["z_L27*"]) / abs(r["z_L27*"])) < DEAD_BAND), None)
    print(f"  the bench's own dead band is {DEAD_BAND:.0%}, so the arms stop being")
    print(f"  DISTINGUISHABLE on the full period before either 'wins':")
    print(f"    F at which the gap enters the {DEAD_BAND:.0%} dead band : "
          f"{'none' if same is None else f'{same:.2f}'}")
    print(f"    F at which L32 becomes the outright leader    : "
          f"{'none' if cross is None else f'{cross:.2f}'}")
    print()
    print(f"  MECHANISM -- whose score moves as the pre-{SPLICE_START} sigma is relaxed:")
    for t in ARMS:
        z1, z3 = z_rmse(*res[t], 1.0, sigma_bar), z_rmse(*res[t], 3.0, sigma_bar)
        print(f"    {t:5s}: {z1:.3f} -> {z3:.3f}  ({100*(z3/z1-1):+.0f} %)")

    print()
    if cross is None:
        print(f"*** THE RANKING IS NOT SIGMA-SENSITIVE: no crossover for F up to "
              f"{F_GRID[-1]:.1f}. L27's full-period win does not rest on the pre-{SPLICE_START} "
              f"sigma being tight. ***")
    else:
        print(f"*** THE RANKING IS SIGMA-SENSITIVE. L32 catches L27 at F = {cross:.2f} and the "
              f"two are indistinguishable from F = {same:.2f}. L32's score improves "
              f"{abs(100*(z_rmse(*res['L32'],3.0,sigma_bar)/z_rmse(*res['L32'],1.0,sigma_bar)-1)):.0f} % "
              f"under relaxation against L27's "
              f"{abs(100*(z_rmse(*res['L27*'],3.0,sigma_bar)/z_rmse(*res['L27*'],1.0,sigma_bar)-1)):.0f} %, "
              f"which confirms the win is EARNED pre-{SPLICE_START}. ***")
        if n_eff < MIN_NEFF:
            print(f"*** BUT NO VERDICT ON REACHABILITY: N_eff = {n_eff:.1f} < {MIN_NEFF}, so the "
                  f"factor needed ({cross:.2f}) cannot be compared against a measured one. The "
                  f"point estimate {rms_z:.2f} sits AT the break-even, which settles nothing. "
                  f"This test cannot decide the arms; it only shows WHERE the decision lives. ***")
        else:
            print(f"*** measured factor {rms_z:.2f} +/- {rms_z*rse:.2f} vs break-even {cross:.2f}: "
                  f"{'REACHABLE' if rms_z + rms_z*rse >= cross else 'NOT reachable'}. ***")

    print(f"\nwrote {OUT_CSV}")

if __name__ == "__main__":
    sys.exit(main())
