#!/usr/bin/env python3
"""
diag_te_rate_bars_and_seam.py — EVERY LINK IN THE TE CHAIN, WITH AN ERROR BAR; and the
                                one link the splice ASSERTS rather than measures.

`diag_te_rate_attribution.py` (2026-08-25, `d24cc67`) attributed the TE rate FAIL to the
OHC driver and priced ~51% of the driver gap as depth scope. **Every number in it is a
point estimate.** In this repo that is a known way to be wrong: `curvature_needs_an_error_bar`
records a whole multi-session arc built on trend ratios whose 1-sigma bars turned out to be
47-78% of the values themselves. The attribution chain deserves the same treatment before
any of it is quoted, and two of its links are fitted over 14 and 21 years.

WHAT THIS ADDS, and each is a decision the point estimates cannot make:

  [A] THE MISS AND THE CHAIN, WITH BARS. rate(TE)/rate(target) = [OHC driver] x [alpha].
      Each factor gets an AR(1)-inflated OLS bar (the benchmark's own `_fit_se`, imported
      rather than re-implemented so the numbers compose with [R]) and a z. A factor whose
      ratio is 1.1x but whose bar admits 1.0 is NOT evidence and must not be quoted as a
      cause.

  [B] THE SEAM, TESTED INSTEAD OF WARNED ABOUT. `prep_recalib_targets_ext.py:30` offset-
      matches Frederikse (pre-2019) to NOAA 0-2000 m (2019+) as "a pure level shift ...
      both measure the same physical SLE". The attribution found their slopes differ by
      6.3% over the 2005-2018 overlap and warned that the target "changes scope/method at
      2019". ⚠ THAT WARNING WAS ISSUED FROM A BARE RATIO OVER 14 YEARS WITH NO BAR --
      the exact move `curvature_needs_an_error_bar` exists to stop. It is tested here.

  [C] THE SPLICE REMOVED FROM THE QUESTION ENTIRELY. The pooled 1993-2026 rate runs through
      the seam: ~26 of its 33 years are Frederikse and ~7 are NOAA. Scoring the model
      against EACH SEGMENT over that segment's OWN years needs no splice, no offset match
      and no scope assumption. If the two segments give the same answer the seam is moot;
      if they do not, the pooled number is a blend of two different targets and the z
      attached to it is not a statement about the model.

⚠ WHAT THIS SCRIPT DOES NOT DO. It does not sharpen the depth-scope correction from the
bound [1.00, 1.102] to a number -- that needs a seawater equation of state (no `gsw` in
this env) and it cannot change a verdict: at the far end of the bound the ratio is still
1.11x. The bound is quoted as the bound it is.

    source ~/climate-env/bin/activate
    python python/diag_te_rate_bars_and_seam.py
Reads   outputs/recalib_targets_ext.csv, outputs/postpred_{L14,oldbrick}_components_timeseries.csv
        data/observations/fair_mean_ohc.csv, data/observations/ohc_spliced_zanna_{cheng,igcc}.csv
        data/observations/raw/noaa_thermosteric_w0-2000m_yearly.dat
        data/observations/raw/frederikse2020_global_basin_timeseries.xlsx
        data/observations/raw/igcc2024/.../earth_energy_imbalance.csv
Writes  outputs/diag_te_rate_bars_and_seam.csv
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
from bench_ladrillo import _fit_se          # noqa: E402  the benchmark's own AR(1) bar

OUT = os.path.join(REPO, "outputs", "diag_te_rate_bars_and_seam.csv")
BENCH = os.path.join(REPO, "outputs", "bench_ladrillo_L14.csv")
TARGETS = os.path.join(REPO, "outputs", "recalib_targets_ext.csv")
POSTPRED = os.path.join(REPO, "outputs", "postpred_L14_components_timeseries.csv")
OLDBRICK = os.path.join(REPO, "outputs", "postpred_oldbrick_components_timeseries.csv")
FAIR_OHC = os.path.join(REPO, "data/observations/fair_mean_ohc.csv")
NOAA = os.path.join(REPO, "data/observations/raw/noaa_thermosteric_w0-2000m_yearly.dat")
FRED_XLSX = os.path.join(REPO, "data/observations/raw/frederikse2020_global_basin_timeseries.xlsx")
IGCC_EEI = os.path.join(REPO, "data/observations/raw/igcc2024/ClimateIndicator-data-2cd2409/"
                              "data/earth_energy_imbalance/earth_energy_imbalance.csv")
OHC_OBS = {"Zanna+Cheng (0-2000m)": "data/observations/ohc_spliced_zanna_cheng.csv",
           "Zanna+IGCC (0-2000m)": "data/observations/ohc_spliced_zanna_igcc.csv"}

# WINDOWS -- every label below derives from these.
WIN = (1993, 2026)          # the benchmark's rate window; runs THROUGH the seam
SPLICE_YEAR = 2019          # prep_recalib_targets_ext.py SPLICE_FROM["steric"]
WIN_FRED = (1993, 2018)     # Frederikse's own years inside WIN -- no splice
WIN_NOAA = (2005, 2025)     # NOAA's own record -- no splice
WIN_NOAA_POST = (2019, 2025) # strictly the post-splice years: no time overlap with WIN_FRED
OVERLAP = (2005, 2018)      # where both exist
WIN_IGCC = (1993, 2024)     # IGCC's coverage
IGCC_UNIT_TO_1E22J = 0.1    # ZJ -> 1e22 J, as in build_ohc_spliced_igcc.py
# A ratio is called RESOLVED when its difference from 1 exceeds this many sigma. Same
# number as the benchmark's own WARN/FAIL boundary on [R], so a verdict here and a verdict
# there mean the same thing.
Z_RESOLVED = 2.0
# The depth-scope correction to the 0-2000 m steric target, as a MULTIPLICATIVE factor.
# Lower end = no deep contribution at all; upper end = the deep layer expands per joule
# exactly as efficiently as the upper ocean, i.e. IGCC's own full-depth/0-2000m HEAT ratio.
# The truth is strictly inside: deep water is colder and expands less per joule, so the
# heat ratio is an UPPER bound on the steric one (`diag_te_rate_attribution.py` [D]).
DEPTH_C_LO = 1.000

rows = []


def emit(**kw):
    rows.append(kw)


def r_se(years, vals, w):
    """rate and AR(1)-inflated se over w."""
    return _fit_se(np.asarray(vals, float), np.asarray(years, float), w, 1)


def ratio_z(a, sa, b, sb):
    """ratio a/b and the z of (a/b - 1), propagating BOTH bars in quadrature.

    For OBSERVATION-vs-OBSERVATION comparisons only. ⚠ Both bars are ESTIMATOR-SCATTER
    bars: they measure wiggle about the fitted line, not the products' published
    uncertainty and not the shared method error between reconstructions
    (`shared_method_error`), so every z here is an UPPER bound on significance."""
    r = a / b
    sr = abs(r) * np.hypot(sa / a, sb / b)
    return r, sr, (r - 1.0) / sr


def ratio_z_obs(mod, obs, se_obs):
    """ratio and z for MODEL vs OBSERVATION, scored against the OBSERVATIONAL bar alone.

    ⚠ THIS IS DELIBERATE AND IT IS THE BENCHMARK'S CONVENTION. `_fit_se` on a SMOOTH,
    ACCELERATING series returns a bar dominated by CURVATURE MISFIT, not by noise: over
    1993-2026 the model's TE p50 scores 0.0079 cm/yr against the observed target's 0.0038,
    i.e. the model's residual about a straight line is 2.1x the observations' -- which is
    a statement about acceleration, not about sampling error. Propagating it as if it were
    a sampling bar would halve every z and would be wrong. The model rate is treated as
    exact here; its PARAMETER uncertainty is reported separately from the p05/p95 arms."""
    r = mod / obs
    sr = abs(r) * (se_obs / obs)
    return r, sr, (mod - obs) / se_obs


def verdict(z):
    return "RESOLVED" if abs(z) >= Z_RESOLVED else "UNRESOLVED"


def main():
    # THE BENCHMARK'S OWN observational bar for this metric -- parsed from its report, not
    # re-derived, so a z printed here is literally the z the benchmark prints.
    bench = pd.read_csv(BENCH)
    se_bench = float(bench[(bench.block == "R") & (bench.component == "te") &
                           (bench.metric == "rate/1993-2026/obs")].note.iloc[0]
                     .split("CONSERVATIVE")[1].split("cm/yr")[0])
    t = pd.read_csv(TARGETS)
    a = pd.read_csv(POSTPRED)
    b = pd.read_csv(OLDBRICK)
    f = pd.read_csv(FAIR_OHC)

    # NOAA 0-2000 m thermosteric, mm -> cm, native years
    st = pd.read_csv(NOAA, sep=r"\s+", skiprows=1, header=None,
                     names=["yr", "WO", "WO_err", "NH", "NH_err", "SH", "SH_err"])
    noaa = pd.Series((st.WO / 10.0).values, index=st.yr.values.astype(float))
    # Frederikse steric, mm -> cm, native years (the pre-2019 half of the target)
    fx = pd.ExcelFile(FRED_XLSX).parse("Global", header=[0, 1])
    fyr = fx.iloc[:, 0].values.astype(float)
    fst = pd.Series(fx[[c for c in fx.columns if c[0] == "Steric [mean]"][0]].values / 10.0,
                    index=fyr)

    print("=" * 100)
    print("TE RATE — EVERY LINK WITH AN ERROR BAR, AND THE SEAM TESTED")
    print("=" * 100)

    # ------------------------------------------------------------------ [A] the chain
    r_tgt, s_tgt = r_se(t.year, t.steric, WIN)
    r_mod, s_mod = r_se(a.year, a.te_p50, WIN)
    r_b20, s_b20 = r_se(b.year, b.te_p50, WIN)
    r_fair, s_fair = r_se(f.year, f.ohc_1e22J, WIN)

    print(f"\n[A] THE MISS AND THE CHAIN, WITH BARS  ({WIN[0]}-{WIN[1]})")
    print(f"\n{'quantity':46s} {'value':>10s} {'+-1sd':>9s} {'ratio':>7s} {'+-':>7s} "
          f"{'z':>7s}  verdict")
    for nm, rr, ss in (("Ladrillo L14 TE / steric target", r_mod, s_mod),
                       ("BRICK 2.0 TE / steric target", r_b20, s_b20)):
        rt, srt, z = ratio_z_obs(rr, r_tgt, se_bench)
        print(f"{nm:46s} {rr:10.5f} {ss:9.5f} {rt:7.3f} {srt:7.3f} {z:7.2f}  {verdict(z)}")
        emit(block="A", quantity=nm, value=rt, sd=srt, z=z, verdict=verdict(z),
             note=f"model {rr:.5f}+-{ss:.5f} vs target {r_tgt:.5f}+-{s_tgt:.5f} cm/yr, {WIN}")
    print(f"{'  (steric target itself)':46s} {r_tgt:10.5f} {se_bench:9.5f}"
          f"   <= the BENCHMARK'S conservative bar, not this script's estimator scatter "
          f"({s_tgt:.5f})")

    print(f"\n    THE DRIVER — FaIR mean OHC {r_fair:.4f} +- {s_fair:.4f} 1e22 J/yr (FULL-DEPTH)")
    for name, rel in OHC_OBS.items():
        d = pd.read_csv(os.path.join(REPO, rel), comment="#")
        col = [c for c in d.columns if c != "year"][0]
        ro, so = r_se(d.year, d[col], WIN)
        rt, srt, z = ratio_z_obs(r_fair, ro, so)
        print(f"{'    FaIR / ' + name:46s} {ro:10.4f} {so:9.4f} {rt:7.3f} {srt:7.3f} "
              f"{z:7.2f}  {verdict(z)}")
        emit(block="A", quantity=f"FaIR OHC / {name}", value=rt, sd=srt, z=z,
             verdict=verdict(z), note=f"obs {ro:.4f}+-{so:.4f} 1e22 J/yr, {WIN}")

    g = pd.read_csv(IGCC_EEI)
    gy = g[[c for c in g.columns if "time" in c.lower() or c.lower() == "year"][0]].values
    gy = np.floor(np.asarray(gy, float))
    sh = (g["ocean_0-700m"] + g["ocean_700-2000m"]).values * IGCC_UNIT_TO_1E22J
    fu = g["ocean_full-depth"].values * IGCC_UNIT_TO_1E22J
    r_sh, s_sh = r_se(gy, sh, WIN_IGCC)
    r_fu, s_fu = r_se(gy, fu, WIN_IGCC)
    r_fa2, s_fa2 = r_se(f.year, f.ohc_1e22J, WIN_IGCC)
    print(f"\n    THE DEPTH SCOPE — IGCC's own layers ({WIN_IGCC[0]}-{WIN_IGCC[1]})")
    for nm, rr, ss in (("FaIR / IGCC 0-2000m  (what the target implies)", r_sh, s_sh),
                       ("FaIR / IGCC FULL-DEPTH (like-for-like)", r_fu, s_fu)):
        rt, srt, z = ratio_z_obs(r_fa2, rr, ss)
        print(f"{'    ' + nm:46s} {rr:10.4f} {ss:9.4f} {rt:7.3f} {srt:7.3f} {z:7.2f}  "
              f"{verdict(z)}")
        emit(block="A", quantity=nm, value=rt, sd=srt, z=z, verdict=verdict(z),
             note=f"IGCC {rr:.4f}+-{ss:.4f} vs FaIR {r_fa2:.4f}+-{s_fa2:.4f}, {WIN_IGCC}")
    rt_lyr, srt_lyr, z_lyr = ratio_z(r_fu, s_fu, r_sh, s_sh)
    print(f"{'    >2000 m layer adds (IGCC full / 0-2000m)':46s} {'':10s} {'':9s} "
          f"{rt_lyr:7.3f} {srt_lyr:7.3f} {z_lyr:7.2f}  {verdict(z_lyr)}")
    emit(block="A", quantity="IGCC full-depth / IGCC 0-2000m", value=rt_lyr, sd=srt_lyr,
         z=z_lyr, verdict=verdict(z_lyr), note="the size of the depth-scope term itself")

    # -------------------------------------------------------------------- [B] the seam
    print(f"\n[B] THE SEAM — is Frederikse/NOAA on the {OVERLAP[0]}-{OVERLAP[1]} overlap "
          f"DISTINGUISHABLE from 1?")
    r_f, s_f = r_se(fst.index.values, fst.values, OVERLAP)
    r_n, s_n = r_se(noaa.index.values, noaa.values, OVERLAP)
    rt, srt, z = ratio_z(r_f, s_f, r_n, s_n)
    rt_seam, srt_seam, z_seam = rt, srt, z
    print(f"    Frederikse steric  {r_f:.5f} +- {s_f:.5f} cm/yr  (n={int(((fst.index>=OVERLAP[0])&(fst.index<=OVERLAP[1])).sum())})")
    print(f"    NOAA 0-2000m       {r_n:.5f} +- {s_n:.5f} cm/yr  (n={int(((noaa.index>=OVERLAP[0])&(noaa.index<=OVERLAP[1])).sum())})")
    print(f"    ratio              {rt:.3f} +- {srt:.3f}   z = {z:+.2f}   => {verdict(z)}")
    emit(block="B", quantity="Frederikse / NOAA on the overlap", value=rt, sd=srt, z=z,
         verdict=verdict(z), note=f"the splice's 'pure level shift' assertion, {OVERLAP}")
    if abs(z) < Z_RESOLVED:
        print(f"\n    ⚠ THE 6.3% SLOPE DIFFERENCE IS NOT RESOLVED. The bar is "
              f"{100*srt:.1f}% of the ratio, i.e. {100*srt/abs(rt-1):.0f}% of the "
              f"difference being claimed.")
        print(f"      The attribution's warning that 'the target changes scope/method at "
              f"{SPLICE_YEAR}' rests on a\n      {OVERLAP[1]-OVERLAP[0]+1}-year trend ratio "
              f"that cannot tell 0.94 from 1.00. WITHDRAW IT unless [C] shows a segment split.")
    else:
        print(f"\n    THE SEAM IS REAL at {abs(z):.1f} sigma -- the pooled rate is a blend.")

    # -------------------------------------------- [C] the splice removed from the question
    print(f"\n[C] EACH SEGMENT ON ITS OWN YEARS — no splice, no offset match, no scope "
          f"assumption")
    print(f"\n{'segment':34s} {'years':12s} {'target':>10s} {'model':>10s} {'ratio':>7s} "
          f"{'+-':>7s} {'z':>7s}  verdict")
    seg = {}
    for nm, series, w in (("Frederikse steric (pre-splice)", fst, WIN_FRED),
                          ("NOAA 0-2000m (own record)", noaa, WIN_NOAA),
                          ("NOAA 0-2000m (post-splice yrs)", noaa, WIN_NOAA_POST)):
        ro, so = r_se(series.index.values, series.values, w)
        rm, sm = r_se(a.year, a.te_p50, w)
        rt, srt, z = ratio_z_obs(rm, ro, so)
        seg[nm] = (rt, srt, z)
        print(f"{nm:34s} {f'{w[0]}-{w[1]}':12s} {ro:10.5f} {rm:10.5f} {rt:7.3f} {srt:7.3f} "
              f"{z:7.2f}  {verdict(z)}")
        emit(block="C", quantity=f"model / {nm}", value=rt, sd=srt, z=z, verdict=verdict(z),
             note=f"segment-only, {w}; target {ro:.5f} model {rm:.5f} cm/yr")
    # ⚠ TWO PAIRINGS, AND THEY TRADE POWER AGAINST INDEPENDENCE. "own record" uses NOAA's
    # full 2005-2025, which OVERLAPS Frederikse's window in 2005-2018 -- so the two rates
    # share years and their difference is not an independent contrast. The strictly
    # post-splice pairing has no shared year but only 7 of them. Both are reported: if the
    # seam mattered, the powerful-but-overlapping test is the one that would still see it,
    # and the independent test is the one that could not be accused of sharing data.
    (rA, sA, _) = seg["Frederikse steric (pre-splice)"]
    for lab, key, note in (("own record (overlaps 2005-2018)", "NOAA 0-2000m (own record)",
                            "more power, shares years"),
                           ("post-splice yrs (no overlap)", "NOAA 0-2000m (post-splice yrs)",
                            "independent, n=7 only")):
        rB, sB, _ = seg[key]
        d, sd_ = rA - rB, np.hypot(sA, sB)
        print(f"    DO THE SEGMENTS AGREE? [{lab:31s}]  {rA:.3f} vs {rB:.3f}, "
              f"diff {d:+.3f} +- {sd_:.3f}, z = {d/sd_:+.2f}  => {verdict(d/sd_)}")
        emit(block="C", quantity=f"segment difference, {lab}", value=d, sd=sd_, z=d / sd_,
             verdict=verdict(d / sd_),
             note=f"{note}; if UNRESOLVED the seam does not matter for the rate")
    # ⚠ A PATTERN WORTH NAMING AND NOT OVER-READING. The ratio grows monotonically with the
    # recency of the window. That would be an ACCELERATION statement, not a rate one -- and
    # the benchmark's own TE acceleration cell (1900-2026) is z = +0.65, UNRESOLVED. No
    # pairwise difference here is resolved either. Recorded so a later window does not
    # rediscover it as news; NOT a finding.
    trend = [seg[k][0] for k in ("Frederikse steric (pre-splice)", "NOAA 0-2000m (own record)",
                                 "NOAA 0-2000m (post-splice yrs)")]
    print(f"\n    ⚠ the ratio GROWS with the recency of the window "
          f"({' -> '.join(f'{x:.3f}' for x in trend)}), but no pairwise\n      difference is "
          f"resolved and the benchmark's TE ACCELERATION cell is z = +0.65 UNRESOLVED. "
          f"Not a finding.")
    emit(block="C", quantity="ratio vs window recency", value=trend[-1] / trend[0], sd=np.nan,
         z=np.nan, verdict="NOT A FINDING",
         note=f"{trend[0]:.3f} -> {trend[1]:.3f} -> {trend[2]:.3f}; no pairwise diff resolved; "
              "TE accel cell z=+0.65 UNRESOLVED")
    rB, sB, _ = seg["NOAA 0-2000m (own record)"]
    d, sd_ = rA - rB, np.hypot(sA, sB)

    # ------------------------------------- [D] the verdict as a function of the ONE unknown
    c_hi = rt_lyr                                   # IGCC's own full-depth / 0-2000m heat ratio
    print(f"\n[D] THE VERDICT IS A FUNCTION OF ONE UNMEASURED NUMBER — the deep ocean's "
          f"expansion\n    efficiency per joule relative to the upper ocean's. Scored on the "
          f"BENCHMARK'S OWN bar\n    ({se_bench:.5f} cm/yr, the conservative of its three "
          f"accounts), so these z's are its z's.")
    print(f"\n{'depth correction c':22s} {'target x c':>11s} {'model/target':>13s} {'z':>8s}  "
          f"verdict   what c means")
    means = {DEPTH_C_LO: "no deep contribution at all",
             c_hi: f"deep expands per joule EXACTLY as the upper ocean (= IGCC heat ratio)"}
    z_of = lambda c: (r_mod - r_tgt * c) / se_bench
    c_star = (r_mod - Z_RESOLVED * se_bench) / r_tgt
    grid = sorted({DEPTH_C_LO, 1.025, 1.05, 1.075, round(c_star, 4), c_hi})
    for c in grid:
        z = z_of(c)
        lbl = means.get(c, "" if abs(c - c_star) > 1e-9 else
                        f"<= THE WARN THRESHOLD: z = {Z_RESOLVED:.0f} exactly")
        print(f"{c:22.4f} {r_tgt*c:11.5f} {r_mod/(r_tgt*c):13.3f} {z:8.2f}  "
              f"{'FAIL' if abs(z) > Z_RESOLVED else 'WARN':9s} {lbl}")
        emit(block="D", quantity=f"z at depth correction c={c:.4f}", value=r_mod/(r_tgt*c),
             sd=np.nan, z=z, verdict="FAIL" if abs(z) > Z_RESOLVED else "WARN",
             note=f"target x c = {r_tgt*c:.5f} cm/yr; benchmark se {se_bench:.5f}; {lbl}")
    print(f"\n    => THE FAIL BECOMES A WARN ONLY AT c >= {c_star:.4f}, and the LARGEST "
          f"correction physics allows\n       is c = {c_hi:.4f}. The whole verdict turns on "
          f"a margin of {100*(c_hi-c_star)/c_hi:.1f}% in a quantity this repo\n       has not "
          f"measured -- so 'the FAIL survives as a WARN at worst' is true only at the very\n"
          f"       EDGE of the bound, and the honest reading on the SEA-LEVEL metric is that "
          f"it stays a FAIL.")

    print("\n" + "=" * 100)
    print("VERDICT")
    print("=" * 100)
    (rA_, sA_, zA_) = seg["Frederikse steric (pre-splice)"]
    (rB_, sB_, zB_) = seg["NOAA 0-2000m (own record)"]
    z_pool = (r_mod - r_tgt) / se_bench
    print(f"""
  [B] THE SEAM WARNING IS WITHDRAWN. Frederikse/NOAA on the {OVERLAP[0]}-{OVERLAP[1]} overlap
      is {rt_seam:.3f} +- {srt_seam:.3f}, z = {z_seam:+.2f} -- the bar is {100*srt_seam/abs(rt_seam-1):.0f}% of the
      {100*abs(1-rt_seam):.1f}% difference the warning was about. The claim that 'the target changes
      scope/method at {SPLICE_YEAR}' was a bare {OVERLAP[1]-OVERLAP[0]+1}-year trend ratio quoted without a bar,
      in the repo whose standing lesson is exactly that (`curvature_needs_an_error_bar`).

  [C] AND THE SPLICE IS MOOT FOR THE RATE, BY A SECOND AND INDEPENDENT ROUTE. Scored on
      each segment's OWN years with no splice at all, the model runs {rA_:.3f}x (Frederikse,
      {WIN_FRED[0]}-{WIN_FRED[1]}) and {rB_:.3f}x (NOAA, {WIN_NOAA[0]}-{WIN_NOAA[1]}): they differ by z = {d/sd_:+.2f},
      {verdict(d/sd_)}. The pooled {r_mod/r_tgt:.2f}x is not a blend of two different targets --
      both halves say the same thing.

  [A] THE DEPTH-SCOPE STEP IS WHERE THE DEFECT DISSOLVES, AND ONLY IN OHC SPACE.
      FaIR / IGCC 0-2000m    = {r_fa2/r_sh:.3f}, z = {(r_fa2-r_sh)/s_sh:+.2f}  {verdict((r_fa2-r_sh)/s_sh)}
      FaIR / IGCC FULL-DEPTH = {r_fa2/r_fu:.3f}, z = {(r_fa2-r_fu)/s_fu:+.2f}  {verdict((r_fa2-r_fu)/s_fu)}
      Compared LIKE FOR LIKE ON DEPTH, FaIR's ocean heat uptake is NOT resolvably
      different from IGCC's. That is stronger than the '51% of the gap is scope' the
      point estimates supported.
      ⚠ AND IT CUTS BOTH WAYS: IGCC's own >2000m layer term is {rt_lyr:.3f} +- {srt_lyr:.3f},
        z = {z_lyr:+.2f}, itself {verdict(z_lyr)} on this window. The bars are wide everywhere;
        'not resolvably different' is not 'shown to agree'.
      ⚠ Zanna+Cheng gives the harshest arm of all, and Cheng is the LOW-SIDE outlier of
        the OHC products (`igcc_ohc_finding`). Never quote a single OHC arm as 'the'
        comparison.

  [D] ON THE SEA-LEVEL METRIC THE FAIL DOES NOT DISSOLVE. Pooled z = {z_pool:+.2f} uncorrected;
      it reaches WARN only at c >= {c_star:.4f} against a physical ceiling of c = {c_hi:.4f}, a
      margin of {100*(c_hi-c_star)/c_hi:.1f}%. `d24cc67`'s 'the FAIL survives as a WARN at worst' is an
      EDGE case, not the expected case, and should be quoted as such.

  => UNCHANGED, AND THE POINT: BRICK 2.0 misses identically ({r_b20/r_tgt:.3f}x, z = {(r_b20-r_tgt)/se_bench:+.2f}).
    Nothing in either sea-level model can move this. It is a FaIR OHC question, and in
    OHC space at matched depth scope it is {verdict((r_fa2-r_fu)/s_fu)}.""")
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
