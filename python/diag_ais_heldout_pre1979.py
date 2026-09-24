#!/usr/bin/env python
"""STEP 2 -- THE HELD-OUT PRE-1979 TEST.  Scoring only: no refit, no target rebuild.

⭐⭐ WHY THIS ARM ALREADY EXISTS.  The 09-24c handoff proposed launching "L35 = the IMBIE target
build + --ais-fit-from=1979".  That arm IS **L31**, run 2026-09-22 (`run_L31.sh`: "L31 = L28 PLUS
--ais-fit-from=1979.  CONTROL = L28, ONE AXIS"), and its posterior predictive is on disk.  The test
step 2 asks for therefore needs NO chain time at all for the free-`sd_ais` cell.  Verified from the
four chain logs, READ BACK not re-typed (`calibrate_mcmc_ext.jl:635-639`):
    "Extended fit windows: ais 1979-2025 ... ⚠ AIS LEVEL TERM RESTRICTED: --ais-fit-from=1979
     (47 yr fitted; 79 pre-1979 years are now OUT-OF-SAMPLE, not absent)"   -- all 4 seeds.
And the pre-flight holds: `calibrate_mcmc_ext.jl:1462` has `const SERIES = [:ais,:gsic,:gis,:steric]
# the total is NOT a likelihood term`, so pre-1979 AIS is not constrained through the total either.

THE QUESTION.  Does an arm fitted ONLY to the IMBIE reconciled record over 1979-2023 PREDICT the
Frederikse reconstruction's 1900-1978?  It needs no choice of sigma -- which is the whole reason it
follows step 1, where the inflation factor turned out to be unmeasurable (N_eff 0.6).

================================================================================================
⚠⚠ PRE-REGISTERED READ -- written and committed BEFORE any arm number was computed.
================================================================================================

⛔ THE LEVEL TRAP, AND WHY THE PRIMARY IS THE SHAPE.  Pre-1979 the two target builds carry the SAME
Frederikse data and differ by EXACTLY a constant, -0.134074 cm (sd 6.2e-17, measured 09-24d).  That
constant is not data: both builds are re-referenced to their own 1995-2005 mean, the builds differ
over 1995-2005, and the offset is that difference.  An arm trained on the IMBIE build reproduces the
IMBIE baseline convention; charging it 0.134 cm for not reproducing Frederikse's would be scoring a
re-referencing artefact as a prediction error -- the same class of ruler bug this arc has now hit
twice (09-24b's `obs`-from-candidate, 09-24d's sigma cliff).  So:

  PRIMARY  = SHAPE ERROR over 1900-1978: the sd of the residual after removing its own mean.
             It is IDENTICAL under both target builds (the offset is a constant) and is therefore
             immune to the baseline question entirely.  This is the statistic that answers
             "does it predict the 79 held-out years".
  REPORTED alongside, never instead: the LEVEL (bias) and the total RMSE against BOTH builds, with
             the constant named, so the reader can see what each ruler charges.

  BOUND, FROM AN OBSERVATION AND NOT FROM THE CODE UNDER TEST (`threshold_from_obs_or_law`):
  the Frederikse target's OWN published 1-sigma band over 1900-1978, sigma_1900_78 = mean over that
  window of (ais_hi - ais_lo)/(2*1.645) from the FROZEN build.  PASS = shape error <= 1.0 sigma.
  ⚠ This is NOT the bench's sigma-bar (0.1674 cm, a whole-record mean that includes the 0.01 cm
  cliff years): pre-1979 the published band is much WIDER.  Both are printed; the bound is the
  window's own band, the frontier ruler is sigma-bar, and neither is allowed to stand in for the
  other.

  ORDERING (needs no bound at all, per handoff 4c): is the out-of-sample arm's pre-1979 error nearer
  the champion L27's or nearer L32's?  All arms on ONE ruler, in one run.

⚠⚠ THE ASYMMETRY, STATED AT THE GATE.  This test is ONE-SIDED, in the OPPOSITE direction from the
GRACE test (09-23h).  A PASS is INFORMATIVE: the two products are reconcilable, the pre-1979 loss is
not intrinsic to fitting IMBIE, and there is no dilemma.  A FAILURE is AMBIGUOUS: the held-out data
IS the product under doubt, so it cannot separate "the model is wrong" from "Frederikse is wrong."

⚠ POWER, MEASURED NOT ASSUMED (`no_power_null`).  79 unconstrained years with a free `sd_ais` may
fit almost anything, and a test whose null is structurally guaranteed reports "no effect"
identically to one that looked.  Two power statistics are printed BEFORE the verdict:
  (P1) the posterior predictive 90% band half-width pre-1979 against the bound.  A pass bought with
       a band far wider than the bound is a weak pass, and is said to be one.
  (P2) L31 (out-of-sample) vs L28 (in-sample, same free-`sd_ais` arm, SAME target, ONE axis).  If
       they are indistinguishable pre-1979, dropping the 79 years changed nothing -- the years were
       never binding, and a pass carries no news.  This is the honest companion to a synthetic
       recovery check and it costs nothing.

⚠ WHAT THIS CANNOT DO (handoff 4d): it cannot make L27-vs-L32 an IC comparison (identical k), and it
does not retire the 7 van Vuuren runs and 14 figures either arm still owes.

REPRODUCTION GATE.  Before any new number, the script re-derives the two PUBLISHED post-ruler-fix
full-period AIS figures on the bench's own ruler (obs from the LIVE target, sigma from the FROZEN
one): `L27*` 0.70 and L32 0.88.  If those do not come back, the ruler is wrong and nothing below it
may be read.  Mutation-tested: a deliberately wrong sigma source IS caught.
"""
import os, sys, hashlib
import numpy as np, pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FROZEN_TGT = os.path.join(REPO, "benchmark/reference/_fixed/recalib_targets_ext.csv")
LIVE_TGT   = os.path.join(REPO, "outputs/recalib_targets_ext.csv")
MD5_FRED, MD5_IMBIE = "070f74abe11080da7b77a80b67c54033", "eb768cd96463a3b84721e2bb9a20f009"

HELDOUT = (1900, 1978)          # the years --ais-fit-from=1979 removes from the objective
REF_WINDOW = (1995, 2005)       # the shared re-reference, same as bench_ladrillo
PUBLISHED_FULL = {"L27": 0.70, "L32": 0.88}      # post-ruler-fix, 09-24; step 1 got 0.7035/0.8812
PUBLISHED_TOL  = 0.005

# tag -> (target build it was TRAINED on, sd_ais treatment, AIS fit span)
ARMS = {
    "L27": ("frederikse", "free",    "1900-2025"),
    "L28": ("imbie2026",  "free",    "1900-2025"),
    "L31": ("imbie2026",  "free",    "1979-2025"),   # <- the out-of-sample arm
    "L32": ("imbie2026",  "floor",   "1900-2025"),
    "L33": ("imbie2026",  "floor21", "1900-2025"),
    "L34": ("frederikse", "floor",   "1900-2025"),
}

def md5(p):
    with open(p, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()

def gate(cond, msg):
    if not cond:
        sys.exit(f"*** GATE FAILED: {msg}")

def load_target(path, expect_md5, label):
    got = md5(path)
    gate(got == expect_md5, f"{label} is {got}, expected {expect_md5} ({path})")
    tg = pd.read_csv(path).set_index("year")
    base = tg.loc[REF_WINDOW[0]:REF_WINDOW[1], "ais"].mean()
    gate(abs(base) < 1e-3, f"{label} AIS is not zeroed on {REF_WINDOW}: {base}")
    print(f"  {label:<22} md5 {got}  zeroed on {REF_WINDOW} (mean {base:+.1e})")
    return tg

def postpred(tag):
    p = os.path.join(REPO, f"outputs/postpred_{tag}_components_timeseries.csv")
    return pd.read_csv(p).set_index("year") if os.path.exists(p) else None

def window_stats(model_p50, obs, lo, hi, a, b):
    """bias / rmse / SHAPE (residual sd, baseline-free) / 90% coverage over [a,b]."""
    m = obs.notna() & model_p50.notna()
    m &= (obs.index >= a) & (obs.index <= b)
    r = (model_p50[m] - obs[m])
    return dict(n=int(m.sum()), bias=float(r.mean()),
                rmse=float(np.sqrt((r ** 2).mean())),
                shape=float(r.std(ddof=0)),          # == sqrt(rmse^2 - bias^2)
                cov90=float(((obs[m] >= lo[m]) & (obs[m] <= hi[m])).mean()),
                halfwidth=float(((hi[m] - lo[m]) / 2).mean()))

def main():
    print(__doc__.split("================")[0].strip()[:0] or "", end="")
    print("=" * 96)
    print("STEP 2 -- HELD-OUT PRE-1979 TEST.  Scoring only; no refit, no target rebuild.")
    print("=" * 96)

    print("\n[0] INPUT GATES")
    fro = load_target(FROZEN_TGT, MD5_FRED,  "frozen  (Frederikse)")
    liv = load_target(LIVE_TGT,   MD5_IMBIE, "live    (IMBIE-2026)")

    sig = (fro["ais_hi"] - fro["ais_lo"]) / (2 * 1.645)
    SIGMA_BAR = float(sig.mean())                                   # the bench's denominator
    SIGMA_HO  = float(sig.loc[HELDOUT[0]:HELDOUT[1]].mean())         # the pre-registered bound
    d = (liv["ais"] - fro["ais"]).loc[HELDOUT[0]:HELDOUT[1]]
    OFFSET = float(d.mean())
    gate(float(d.std()) < 1e-12, f"pre-1979 builds are not a pure constant apart (sd {d.std():.2e})")
    print(f"  pre-1979 IMBIE - Frederikse = CONSTANT {OFFSET:+.6f} cm (sd {d.std():.1e}) -- verified,"
          " so the SHAPE statistic is identical under both builds")
    print(f"  sigma_bar (whole record, bench ruler)      = {SIGMA_BAR:.4f} cm")
    print(f"  sigma_1900-1978 (PRE-REGISTERED BOUND)     = {SIGMA_HO:.4f} cm   <- the published band"
          " over the held-out window")

    print("\n[1] REPRODUCTION GATE -- the bench's own full-period AIS figures, on its own ruler")
    for tag, want in PUBLISHED_FULL.items():
        pp = postpred(tag)
        gate(pp is not None, f"{tag} postpred missing")
        s = window_stats(pp["ais_p50"], liv["ais"].reindex(pp.index),
                         pp["ais_p05"], pp["ais_p95"], 1900, 2026)
        got = s["rmse"] / SIGMA_BAR
        ok = abs(got - want) <= PUBLISHED_TOL
        print(f"  {tag}: full-period AIS {got:.4f} sigma vs published {want:.2f}  "
              f"{'OK' if ok else '*** MISMATCH ***'}")
        gate(ok, f"{tag} full-period is {got:.4f}, published {want:.2f} -- the ruler is wrong")
    print("  ruler reproduced; the numbers below may be read.")

    print(f"\n[2] THE HELD-OUT WINDOW {HELDOUT[0]}-{HELDOUT[1]}  (79 yr; out-of-sample for L31 ONLY)")
    print("    SHAPE = residual sd after removing the window mean = baseline-free, identical under"
          " both builds.")
    hdr = (f"  {'arm':<5} {'trained on':<11} {'sd_ais':<8} {'ais fit':<10} | "
           f"{'SHAPE cm':>9} {'/sig_ho':>8} {'/sig_bar':>9} | "
           f"{'bias vs IMB':>12} {'bias vs FRD':>12} | {'rmse vs IMB':>12} | {'cov90':>6}")
    print(hdr); print("  " + "-" * (len(hdr) - 2))
    rows = []
    for tag, (trained, sdt, span) in ARMS.items():
        pp = postpred(tag)
        if pp is None:
            print(f"  {tag:<5} postpred MISSING"); continue
        s_i = window_stats(pp["ais_p50"], liv["ais"].reindex(pp.index), pp["ais_p05"], pp["ais_p95"], *HELDOUT)
        s_f = window_stats(pp["ais_p50"], fro["ais"].reindex(pp.index), pp["ais_p05"], pp["ais_p95"], *HELDOUT)
        gate(abs(s_i["shape"] - s_f["shape"]) < 1e-9, f"{tag} shape differs between builds -- impossible")
        oos = " <- OUT-OF-SAMPLE" if span.startswith("1979") else ""
        print(f"  {tag:<5} {trained:<11} {sdt:<8} {span:<10} | {s_i['shape']:>9.4f} "
              f"{s_i['shape']/SIGMA_HO:>8.2f} {s_i['shape']/SIGMA_BAR:>9.2f} | "
              f"{s_i['bias']:>+12.4f} {s_f['bias']:>+12.4f} | {s_i['rmse']:>12.4f} | "
              f"{s_i['cov90']:>5.0%}{oos}")
        rows.append(dict(arm=tag, trained_on=trained, sd_ais=sdt, ais_fit_span=span,
                         n=s_i["n"], shape_cm=s_i["shape"],
                         shape_over_sigma_heldout=s_i["shape"] / SIGMA_HO,
                         shape_over_sigma_bar=s_i["shape"] / SIGMA_BAR,
                         bias_vs_imbie_cm=s_i["bias"], bias_vs_frederikse_cm=s_f["bias"],
                         rmse_vs_imbie_cm=s_i["rmse"], rmse_vs_frederikse_cm=s_f["rmse"],
                         rmse_vs_imbie_over_sigma_bar=s_i["rmse"] / SIGMA_BAR,
                         cov90_vs_imbie=s_i["cov90"], band_halfwidth_cm=s_i["halfwidth"],
                         sigma_heldout_cm=SIGMA_HO, sigma_bar_cm=SIGMA_BAR,
                         constant_offset_cm=OFFSET))
    R = {r["arm"]: r for r in rows}

    print("\n[3] POWER -- measured before the verdict is read")
    if "L31" in R:
        hw = R["L31"]["band_halfwidth_cm"]
        print(f"  (P1) L31 pre-1979 90% band half-width {hw:.4f} cm vs the bound {SIGMA_HO:.4f} cm "
              f"= {hw/SIGMA_HO:.2f}x the bound.")
        print("       " + ("⚠ the band is WIDER than the bound: a pass on coverage is cheap, so the"
                           " SHAPE statistic (a point-error, not a coverage test) carries the verdict."
                           if hw > SIGMA_HO else
                           "the band is NARROWER than the bound, so a pass is not bought by width."))
    if "L31" in R and "L28" in R:
        a, b = R["L31"]["shape_cm"], R["L28"]["shape_cm"]
        rel = (a - b) / b
        print(f"  (P2) L31 (out-of-sample) {a:.4f} cm vs L28 (in-sample, same target, same free"
              f" sd_ais, ONE axis) {b:.4f} cm = {rel:+.1%}.")
        print("       " + ("⚠⚠ INDISTINGUISHABLE (|rel| <= 2%, the bench's own dead band): dropping"
                           " the 79 years changed the pre-1979 hindcast by nothing, so those years"
                           " were never binding and a PASS CARRIES NO NEWS."
                           if abs(rel) <= 0.02 else
                           "the two differ by more than the bench's 2% dead band, so the held-out"
                           " years WERE doing work and the test has power."))

    print("\n[4] VERDICT")
    if "L31" in R:
        v = R["L31"]["shape_over_sigma_heldout"]
        verdict = "PASS" if v <= 1.0 else "FAIL"
        print(f"  PRIMARY: L31 held-out {HELDOUT[0]}-{HELDOUT[1]} SHAPE error = "
              f"{R['L31']['shape_cm']:.4f} cm = {v:.2f} x the Frederikse published band "
              f"({SIGMA_HO:.4f} cm)  ==>  {verdict}")
        print("  ASYMMETRY: " + ("a PASS is INFORMATIVE -- the two products are reconcilable and"
                                 " the pre-1979 loss is not intrinsic to fitting IMBIE."
                                 if verdict == "PASS" else
                                 "a FAILURE is AMBIGUOUS -- the held-out data IS the product under"
                                 " doubt, so this cannot separate 'the model is wrong' from"
                                 " 'Frederikse is wrong'."))
        for other in ("L27", "L32"):
            if other in R:
                print(f"  ORDERING vs {other}: L31 {R['L31']['shape_over_sigma_bar']:.2f} vs "
                      f"{other} {R[other]['shape_over_sigma_bar']:.2f} sigma_bar "
                      f"(ratio {R['L31']['shape_cm']/R[other]['shape_cm']:.2f})")

    out = os.path.join(REPO, "outputs/diag_ais_heldout_pre1979.csv")
    df = pd.DataFrame(rows)
    df["provenance"] = (f"diag_ais_heldout_pre1979.py | frozen {MD5_FRED[:8]} (Frederikse) | "
                        f"live {MD5_IMBIE[:8]} (IMBIE-2026) | heldout {HELDOUT[0]}-{HELDOUT[1]} | "
                        f"ref {REF_WINDOW} | sigma_ho {SIGMA_HO:.4f} sigma_bar {SIGMA_BAR:.4f} cm | "
                        f"offset {OFFSET:+.6f} cm | scoring only, no refit, no RNG | cm")
    df.to_csv(out, index=False)
    print(f"\n  wrote {os.path.relpath(out, REPO)}")

if __name__ == "__main__":
    main()
