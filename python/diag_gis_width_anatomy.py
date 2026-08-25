#!/usr/bin/env python3
"""
diag_gis_width_anatomy.py — IS THE GREENLAND WIDTH DEFICIT REAL, AND IF SO WHOSE WIDTH
                            IS MISSING? Price it before proposing a fix.

Marcus 2026-08-25 chose the Greenland width as the next thing to do. `bench_ladrillo.py`
scores it at **0.14-0.46x the literature spread at 5 of 6 cells**, and the bimodality guard
that retracted the ssp126 AIS defect does NOT apply here -- Greenland's p05-p99/p05-p95
ratios are 1.35-1.45 against a Gaussian 1.207, so its band is unimodal and the deficit is
not a quantile artifact. THAT MUCH SURVIVES. What has never been asked is whose width it is.

THREE THINGS HAVE TO BE SEPARATED BEFORE ANY FIX IS PROPOSED, and each is measurable here:

  [A] COMPARATOR SELECTION. The benchmark scores against the literature MEDIAN spread. At
      Greenland the comparators span 8x (FittedISMIP 7.06 cm to bamber19 55.71 cm at
      ssp126@2100) and at 2150 there are only TWO of them, so their "median" is the mean of
      a process-model band and a structured-expert-judgement band -- a number no module
      produces. `audit_every_target` / step 1's own rule: quote the comparator, never just
      the median.

  [B] BETWEEN-MODEL (STRUCTURAL) SPREAD, WHICH IS OUT OF SCOPE BY CONSTRUCTION.
      Marcus, 2026-08-23: *"we aren't trying to match between-model spread (we don't have
      the precipitation level), just between-scenario spreads."* Our Greenland carries no
      SMB/accumulation term that would distinguish ice-sheet models, so any part of a
      comparator's width that is ISM-to-ISM structural is width we should NOT reproduce.
      ISMIP6 measures that term directly and AT FIXED FORCING -- each of its cells is one
      GCM run through 9-14 ice-sheet models -- so it can be subtracted rather than assumed.

  [C] WHAT IS LEFT is our own parametric width, and the fixed-vs-joint arms in the draws
      file separate it from the forcing width exactly, with no model run.

⚠ VARIANCES ARE ADDED, NOT p05-p95 RANGES. A p05-p95 spread is not additive (the total's
covariance residual is +18% to +34% for exactly this reason). Everything below converts to
an effective sigma = spread/3.29 first, composes in variance, and converts back -- and that
step ASSUMES approximate normality and independence. Both are stated at each use: our tail
ratios are 1.35-1.45, so "approximately normal" is an approximation carrying maybe 10-20%,
which is small against the 3-8x effects being measured but is NOT nothing.

⚠ THE ISM SIGMA IS ESTIMATED FROM THE IQR (IQR/1.349), NOT FROM THE RANGE. With 9-14
models the min is an outlier-dominated statistic -- at CNRM-CM6-1 ssp126 the min (1.83 cm)
sits 2.4 cm below p25 while p25-p75 spans 0.70 cm -- so a range-based sigma is 2.2x the
IQR-based one. BOTH are reported and the conclusion is required to hold at the LARGER
(range-based) value, which is the one that favours the "it is structural" explanation.

    source ~/climate-env/bin/activate
    python python/diag_gis_width_anatomy.py [--tag=L14]
Reads   outputs/scope_slr_fairunc_draws_<ssp>_spliced_<TAG>.csv
        benchmark/reference/_fixed/literature_rows.csv
        outputs/diag_gis_ismip6_2100_ism_spread_arms.csv
Writes  outputs/diag_gis_width_anatomy_<TAG>.csv
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = next((a[len("--tag="):] for a in sys.argv[1:] if a.startswith("--tag=")), "L14")
OUT = os.path.join(REPO, "outputs", f"diag_gis_width_anatomy_{TAG}.csv")
DRAWS = os.path.join(REPO, "outputs", "scope_slr_fairunc_draws_{ssp}_spliced_" + TAG + ".csv")
LIT = os.path.join(REPO, "benchmark/reference/_fixed/literature_rows.csv")
ISM = os.path.join(REPO, "outputs/diag_gis_ismip6_2100_ism_spread_arms.csv")

COMPONENT = "gis"
SSPS = ["ssp126", "ssp245", "ssp585"]
HORIZONS = [2100, 2150, 2300]
LIT_HORIZONS = [2100, 2150]
QLO, QHI = 5, 95
Z_SPAN = 3.29                      # p95 - p05 in standard normal units, 2 x 1.645
IQR_TO_SIGMA = 1.349               # p75 - p25 in standard normal units
## The comparators that are the SAME KIND OF OBJECT as Ladrillo -- a calibrated emulator or
## a fitted transient model driven by a climate ensemble -- as against a structured expert
## judgement, whose width is dominated by deep/structural uncertainty we do not model.
## Named here, not inferred, so the classification is auditable and arguable.
LIKE_FOR_LIKE = {"FittedISMIP", "Nauels2025"}
STRUCTURAL = {"bamber19", "emuGrIS"}
rows = []


def emit(**kw):
    rows.append(kw)


def sig(spread):
    return spread / Z_SPAN


lit = pd.read_csv(LIT)
lit = lit[lit.component == COMPONENT].copy()
lit["spread"] = lit.p95.astype(float) - lit.p05.astype(float)

print("=" * 104)
print(f"GREENLAND WIDTH ANATOMY ({TAG}) — is the deficit real, and whose width is missing?")
print("=" * 104)

# ------------------------------------------------------------------ [A]
print("\n[A] AGAINST EVERY COMPARATOR SEPARATELY, not against their median")
print("    ⚠ the benchmark's `spread_vs_lit` uses the literature MEDIAN spread. Here is what")
print("      that median is made of.")
ours = {}
for ssp in SSPS:
    d = pd.read_csv(DRAWS.format(ssp=ssp))
    for H in HORIZONS:
        for arm in ("fixed", "joint"):
            v = d[(d.horizon == H) & (d.component == COMPONENT) & (d.arm == arm)].value_cm.values
            if len(v):
                ours[(ssp, H, arm)] = (float(np.median(v)),
                                       float(np.percentile(v, QHI) - np.percentile(v, QLO)))
for H in LIT_HORIZONS:
    for ssp in SSPS:
        L = lit[(lit.scenario == ssp) & (lit.year == H)]
        if L.empty or (ssp, H, "joint") not in ours:
            continue
        osp = ours[(ssp, H, "joint")][1]
        print(f"\n    --- {ssp} @{H} : ours (JOINT) {osp:.2f} cm " + "-" * 44)
        print(f"    {'comparator':22s} {'kind':16s} {'spread':>8s} {'ours/theirs':>12s}")
        for _, r in L.sort_values("spread").iterrows():
            kind = ("LIKE-FOR-LIKE" if r.module in LIKE_FOR_LIKE else
                    ("structural" if r.module in STRUCTURAL else "unclassified"))
            print(f"    {r.source + ' ' + r.module:22s} {kind:16s} {r.spread:8.2f} "
                  f"{osp/r.spread:12.2f}")
            emit(block="A", ssp=ssp, horizon=H, key=f"vs_{r.module}", value=osp / r.spread,
                 note=f"{kind}; theirs {r.spread:.2f} cm, ours {osp:.2f} cm")
        lfl = L[L.module.isin(LIKE_FOR_LIKE)].spread.values
        med = float(np.median(L.spread.values))
        print(f"    -> vs the MEDIAN of all {len(L)}: {osp/med:.2f}x   <= what the benchmark scores")
        if len(lfl):
            print(f"    -> vs the LIKE-FOR-LIKE comparators only "
                  f"({', '.join(sorted(L[L.module.isin(LIKE_FOR_LIKE)].module))}): "
                  f"{osp/np.median(lfl):.2f}x")
            emit(block="A", ssp=ssp, horizon=H, key="vs_like_for_like",
                 value=osp / float(np.median(lfl)),
                 note=f"n={len(lfl)}; vs all-comparator median {osp/med:.2f}x")
        if len(L) == 2:
            print(f"    ⚠ n=2, so their 'median' {med:.2f} cm is the MEAN of "
                  f"{L.spread.min():.2f} and {L.spread.max():.2f} — a width no module produces.")

# ------------------------------------------------------------------ [C]
print("\n\n[C] OUR OWN WIDTH, SPLIT INTO PARAMETRIC AND FORCING")
print("    Exact, no model run: the `fixed` arm holds the forcing at the ensemble mean and")
print("    the `joint` arm pairs each draw with its own FaIR config. Variances, not ranges.")
print(f"\n    {'ssp':8s} {'H':>5s} {'fixed':>8s} {'joint':>8s} {'sig_par':>8s} {'sig_frc':>8s} "
      f"{'forcing % of variance':>22s}")
for ssp in SSPS:
    for H in HORIZONS:
        if (ssp, H, "joint") not in ours:
            continue
        fsp, jsp = ours[(ssp, H, "fixed")][1], ours[(ssp, H, "joint")][1]
        sp, sj = sig(fsp), sig(jsp)
        sf = np.sqrt(max(sj ** 2 - sp ** 2, 0.0))
        frac = sf ** 2 / sj ** 2 if sj > 0 else np.nan
        print(f"    {ssp:8s} {H:5d} {fsp:8.2f} {jsp:8.2f} {sp:8.3f} {sf:8.3f} {100*frac:21.1f}%")
        emit(block="C", ssp=ssp, horizon=H, key="sigma_parametric", value=sp,
             note=f"sigma_forcing {sf:.3f}; forcing is {100*frac:.1f}% of the joint variance; "
                  f"fixed spread {fsp:.2f}, joint {jsp:.2f} cm")

# ------------------------------------------------------------------ [B]
print("\n\n[B] THE BETWEEN-MODEL TERM, MEASURED — and it is SMALL")
print("    ISMIP6 at FIXED forcing: one GCM through 9-14 ice-sheet models, so the spread is")
print("    purely structural. This is the width Marcus's standing constraint puts OUT OF")
print("    SCOPE (no precipitation level in our Greenland), so it is the part of a")
print("    comparator's band we are entitled NOT to reproduce.")
if os.path.exists(ISM):
    a = pd.read_csv(ISM)
    print(f"\n    {'gcm':14s} {'ssp':8s} {'n_ism':>5s} {'IQR':>7s} {'sig_IQR':>8s} "
          f"{'range':>7s} {'sig_rng':>8s}")
    per = {}
    for _, r in a.iterrows():
        iqr = float(r.ism_p75) - float(r.ism_p25)
        s_iqr = iqr / IQR_TO_SIGMA
        rng = float(r.ism_max) - float(r.ism_min)
        # expected range/sigma for a normal sample of size n (Tippett), interpolated on the
        # values that matter here: n=9 -> 3.08, n=12 -> 3.26, n=13 -> 3.34, n=14 -> 3.41
        d2 = {9: 3.08, 12: 3.26, 13: 3.34, 14: 3.41}.get(int(r.n_ism), 3.3)
        s_rng = rng / d2
        per.setdefault(r.ssp, []).append((s_iqr, s_rng))
        print(f"    {r.gcm:14s} {r.ssp:8s} {int(r.n_ism):5d} {iqr:7.2f} {s_iqr:8.3f} "
              f"{rng:7.2f} {s_rng:8.3f}")
        emit(block="B", ssp=r.ssp, horizon=2100, key=f"ism_sigma_{r.gcm}", value=s_iqr,
             note=f"range-based {s_rng:.3f}; n_ism {int(r.n_ism)}")
    print("\n    ⚠ IQR-based and range-based disagree up to 2.2x because the ISM MIN is an")
    print("      outlier. The verdict below is required to hold at the LARGER (range-based)")
    print("      value, which is the one that favours 'it is structural'.")

    print("\n\n[D] THE ARITHMETIC — can the out-of-scope structural term close the gap?")
    print("    Compose our JOINT band with the ISM structural term in variance and ask")
    print("    whether the result reaches the LIKE-FOR-LIKE comparator's width.")
    print(f"\n    {'ssp':8s} {'H':>5s} {'ours':>7s} {'+ISM(IQR)':>10s} {'+ISM(rng)':>10s} "
          f"{'LFL target':>11s} {'closed?':>26s}")
    for ssp in SSPS:
        H = 2100
        if ssp not in per or (ssp, H, "joint") not in ours:
            continue
        L = lit[(lit.scenario == ssp) & (lit.year == H) & (lit.module.isin(LIKE_FOR_LIKE))]
        if L.empty:
            continue
        tgt = float(np.median(L.spread.values))
        jsp = ours[(ssp, H, "joint")][1]
        s_iqr = float(np.median([x[0] for x in per[ssp]]))
        s_rng = float(np.median([x[1] for x in per[ssp]]))
        c_iqr = Z_SPAN * np.sqrt(sig(jsp) ** 2 + s_iqr ** 2)
        c_rng = Z_SPAN * np.sqrt(sig(jsp) ** 2 + s_rng ** 2)
        verdict = ("CLOSED by the structural term" if c_rng >= tgt else
                   f"NOT CLOSED — {tgt - c_rng:.2f} cm still missing")
        print(f"    {ssp:8s} {H:5d} {jsp:7.2f} {c_iqr:10.2f} {c_rng:10.2f} {tgt:11.2f} "
              f"{verdict:>26s}")
        emit(block="D", ssp=ssp, horizon=H, key="gap_after_structural",
             value=float(tgt - c_rng),
             note=f"ours {jsp:.2f} + ISM(range) {s_rng:.3f} sigma -> {c_rng:.2f} cm vs "
                  f"like-for-like {tgt:.2f} cm; IQR arm gives {c_iqr:.2f}")


# ------------------------------------------------------------------ [E]
print("\n\n[E] IS IT OUR CLIMATE ENSEMBLE RATHER THAN OUR GREENLAND? — an internal control")
print("    Greenland is 80-91% forcing, so a narrow FaIR ensemble would produce a narrow")
print("    Greenland band with nothing wrong in the ice sheet. THERMAL EXPANSION is the")
print("    control: it is ~84% forcing too, shares the same FaIR configs, and has its own")
print("    literature comparators. If our climate spread were the cause, TE would be narrow")
print("    by the same factor.")
for H in LIT_HORIZONS:
    for ssp in SSPS:
        te = pd.read_csv(LIT)
        te = te[(te.component == "te") & (te.scenario == ssp) & (te.year == H)]
        d = pd.read_csv(DRAWS.format(ssp=ssp))
        v = d[(d.horizon == H) & (d.component == "te") & (d.arm == "joint")].value_cm.values
        if te.empty or len(v) == 0:
            continue
        tsp = float(np.percentile(v, QHI) - np.percentile(v, QLO))
        lsp = float(np.median((te.p95.astype(float) - te.p05.astype(float)).values))
        g = ours[(ssp, H, "joint")][1]
        L = lit[(lit.scenario == ssp) & (lit.year == H) & (lit.module.isin(LIKE_FOR_LIKE))]
        gr = g / float(np.median(L.spread.values)) if not L.empty else np.nan
        print(f"    {ssp} @{H}:  TE {tsp/lsp:.2f}x lit   vs   GIS {gr:.2f}x like-for-like")
        emit(block="E", ssp=ssp, horizon=H, key="te_control", value=tsp / lsp,
             note=f"GIS is {gr:.2f}x its like-for-like comparators at the same cell")
print("    => if TE sits near 1x while GIS does not, the FaIR ensemble is NOT the cause and")
print("       the missing width is Greenland's own.")

# ------------------------------------------------------------------ [F]
print("\n\n[F] WHAT FIXING IT IS WORTH ON THE DELIVERABLE")
print("    `npv_retires_tau`: price the knob against the discounted deliverable BEFORE")
print("    identifying it. The deficit is expressed as the extra sigma that would have to be")
print("    added to Greenland, then propagated to the TOTAL band under BOTH correlation")
print("    brackets, because the correlation of a width we have not built is unknown.")
print(f"\n    {'ssp':8s} {'H':>5s} {'GIS gap cm':>11s} {'total now':>10s} {'total indep':>12s} "
      f"{'total corr':>11s} {'worst move':>11s}")
for H in LIT_HORIZONS:
    for ssp in SSPS:
        L = lit[(lit.scenario == ssp) & (lit.year == H) & (lit.module.isin(LIKE_FOR_LIKE))]
        if L.empty or (ssp, H, "joint") not in ours:
            continue
        tgt = float(np.median(L.spread.values))
        g = ours[(ssp, H, "joint")][1]
        if g >= tgt:
            print(f"    {ssp:8s} {H:5d} {'no gap':>11s}")
            continue
        s_extra = np.sqrt(max(sig(tgt) ** 2 - sig(g) ** 2, 0.0))
        d = pd.read_csv(DRAWS.format(ssp=ssp))
        tv = d[(d.horizon == H) & (d.component == "total") & (d.arm == "joint")].value_cm.values
        tsp = float(np.percentile(tv, QHI) - np.percentile(tv, QLO))
        ind = Z_SPAN * np.sqrt(sig(tsp) ** 2 + s_extra ** 2)
        cor = tsp + Z_SPAN * s_extra
        print(f"    {ssp:8s} {H:5d} {tgt-g:11.2f} {tsp:10.2f} {ind:12.2f} {cor:11.2f} "
              f"{100*(cor-tsp)/tsp:10.1f}%")
        emit(block="F", ssp=ssp, horizon=H, key="total_band_move_pct",
             value=100 * (cor - tsp) / tsp,
             note=f"GIS gap {tgt-g:.2f} cm vs like-for-like; total {tsp:.2f} -> "
                  f"{ind:.2f} (independent) / {cor:.2f} cm (perfectly correlated)")
print("    ⚠ the CORRELATED column is the upper bracket, not the estimate.")

pd.DataFrame(rows).to_csv(OUT, index=False)
print(f"\nwrote {os.path.relpath(OUT, REPO)}")
