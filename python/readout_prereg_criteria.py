#!/usr/bin/env python3
"""
readout_prereg_criteria.py -- MECHANICAL read-out of the PRE-REGISTERED criteria for an arm.

WHY THIS EXISTS. The L34 criteria were fixed by Marcus on 2026-09-24 BEFORE any number existed
(CHANGELOG 09-24a). A criterion that is applied by eye AFTER the numbers are on screen is not a
pre-registered criterion -- it is a rationalisation with a timestamp. This script hard-codes the
thresholds as named constants and reads the products, so the verdict is produced the same way
whichever direction the numbers fall.

SCOPE. PRIMARY, COST A, COST B and GUARD are read from files. MECHANISM is NOT -- it needs
  julia --project=julia_v2 julia/diag_ais_channel_separation.jl 1000 --arms=REF,TAG
which must run with the IMBIE target live, and is reported separately.

*** THE LIKE-FOR-LIKE GATE IS THE POINT OF THIS SCRIPT, NOT A DECORATION. ***
COST A compares two postpred bias files written on DIFFERENT DAYS. If the target was rebuilt
between them, the `obs` column moves and the bias difference is an artefact of the ruler, not the
arm (the 09-23g class: two individually valid files, mutually invalid). The gate compares `obs`
year-by-year and REFUSES to grade COST A if they differ.

Provenance is stamped into the output, including the md5 of every input read.
"""
import argparse, hashlib, os, re, sys, datetime
import pandas as pd

SCRIPT = "readout_prereg_criteria.py"

# ---- PRE-REGISTERED CRITERIA (CHANGELOG 2026-09-24a; fixed before any number existed) ----------
PRIMARY_NAME      = "FULL-PERIOD AIS RMSE (sigma), live target, one run, vs the frozen champion"
PRIMARY_WIN_MAX   = 0.70     # WIN   if candidate <= this
PRIMARY_LOSS_MIN  = 0.80     # LOSS  if candidate >= this
                             # between the two: AMBIGUOUS, and it must be SAID SO
COSTA_NAME        = "AIS hindcast bias at the anchor years -- REPORT EITHER WAY, not a gate"
COSTA_YEARS       = [1900, 1950, 2018, 2025]
COSTB_NAME        = "SSP AIS p05-p95 -- a win that is ONLY a wider posterior is no win"
COSTB_YEARS       = [2100, 2300]
COSTB_SSPS        = ["ssp126", "ssp245", "ssp585"]
GUARD_NAME        = "non-Antarctic components unchanged"
GUARD_TOL_SIGMA   = 0.02     # "within ~0.02 sigma of the champion"
# COST B must quote the SAME champion the PRIMARY's ruler does -- the FROZEN snapshot, not the
# live outputs/ file. Measured 2026-09-24: outputs/ladrillo_model_comparison_L27.csv has DRIFTED
# from benchmark/reference/L27/model_comparison.csv (sha256_16 95614fc2058ea20c vs the manifest's
# c01da3f107437e1d). lws moved 0.47 cm and total 0.48 cm -- the 09-21 LWS_MODE :central ->
# :observed switch. The Ladrillo AIS medians ALSO moved, all 9 of them in the SAME direction
# (+0.0043 to +0.0080 cm, growing with horizon). The cause is NOT established; the magnitude is
# <= 0.0096% of band width, which is immaterial for a width ratio but is not a reason to quote
# the wrong file. Frozen first, live only as a fallback, and the fallback says so.
FROZEN_REF_TMPL   = "benchmark/reference/{ref}/model_comparison.csv"
HINDCAST_WINDOW   = "full"   # the PRIMARY is the FULL period, not a sub-window
DECOMP_NAME       = ("AIS sub-window decomposition -- DESCRIPTIVE, NOT A CRITERION. "
                     "Added 2026-09-24 08:30, BEFORE any candidate number existed.")
DECOMP_THIRD_ARM  = "L32"    # the arm that changed BOTH the target and the noise model
AIS_LABEL         = "AIS"
NOT_A_CRITERION   = "sd_ais sitting on its bound -- TRUE BY CONSTRUCTION, never evidence"

def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def parse_bench(path):
    """Rows of the [H] table: module | target 1sigma | window | arm | RMSE cm | RMSE sigma | note"""
    rows, in_h = [], False
    for line in open(path, encoding="utf-8"):
        if line.startswith("## [H]"):
            in_h = True; continue
        if in_h and line.startswith("## ") and not line.startswith("## [H]"):
            break
        if not in_h or not line.startswith("|"):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 6 or c[0] in ("module", "---") or set(c[0]) <= {"-"}:
            continue
        try:
            rows.append(dict(module=c[0], sigma=float(c[1]), window=c[2], arm=c[3],
                             rmse_cm=float(c[4]), rmse_sd=float(c[5]), note=c[6] if len(c) > 6 else ""))
        except ValueError:
            continue
    return pd.DataFrame(rows)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True, help="candidate arm, e.g. L34")
    ap.add_argument("--ref", default="L27", help="frozen champion arm (bench column is <ref>*)")
    ap.add_argument("--outdir", default="outputs")
    a = ap.parse_args()
    TAG, REF, OUT = a.tag, a.ref, a.outdir
    REF_COL = REF + "*"                       # the bench's re-scored frozen snapshot -- the ONLY valid ruler
    inputs, lines, fails = {}, [], 0

    def emit(s=""): lines.append(s)
    def need(p):
        if not os.path.exists(p):
            emit(f"  *** MISSING {p} -- cannot grade this criterion ***"); return False
        inputs[p] = md5(p); return True

    emit(f"# Pre-registered criteria read-out -- `{TAG}` against `{REF_COL}`")
    emit()
    emit(f"*{SCRIPT}, {datetime.date.today()}. Thresholds are the constants at the top of this "
         f"script, fixed 2026-09-24 before any {TAG} number existed.*")
    emit()
    emit(f"> NOT A CRITERION: {NOT_A_CRITERION}")
    emit()

    # ---- PRIMARY + GUARD, both out of the bench's [H] table ------------------------------------
    bench = f"{OUT}/bench_ladrillo_{TAG}.md"
    emit(f"## PRIMARY -- {PRIMARY_NAME}")
    emit()
    if need(bench):
        h = parse_bench(bench)
        full = h[h.window == HINDCAST_WINDOW]
        ais = full[full.module == AIS_LABEL]
        cand = ais[ais.arm == TAG]; ref = ais[ais.arm == REF_COL]
        if cand.empty or ref.empty:
            emit(f"  *** no `{AIS_LABEL}`/`{HINDCAST_WINDOW}` row for `{TAG}` and/or `{REF_COL}` "
                 f"in {bench} -- the ruler is absent, NOT a pass ***"); fails += 1
        else:
            cv, rv = float(cand.rmse_sd.iloc[0]), float(ref.rmse_sd.iloc[0])
            verdict = ("WIN" if cv <= PRIMARY_WIN_MAX else
                       "LOSS" if cv >= PRIMARY_LOSS_MIN else "AMBIGUOUS")
            emit(f"| arm | AIS RMSE (cm) | **AIS RMSE (sigma)** | note |")
            emit(f"|---|---|---|---|")
            for _, r in ais.iterrows():
                star = " **<-- candidate**" if r.arm == TAG else (" (ruler)" if r.arm == REF_COL else "")
                emit(f"| {r.arm}{star} | {r.rmse_cm:.4f} | **{r.rmse_sd:.2f}** | {r.note} |")
            emit()
            emit(f"**{TAG} = {cv:.2f} sigma** vs **{REF_COL} = {rv:.2f}**. "
                 f"Pre-registered: WIN <= {PRIMARY_WIN_MAX}, LOSS >= {PRIMARY_LOSS_MIN}, "
                 f"{PRIMARY_WIN_MAX}-{PRIMARY_LOSS_MIN} AMBIGUOUS.")
            emit()
            emit(f"### ==> PRIMARY VERDICT: **{verdict}**"
                 + ("  (and the band must be reported AS ambiguous, not rounded to a side)"
                    if verdict == "AMBIGUOUS" else ""))
        emit()
        emit(f"## GUARD -- {GUARD_NAME} (within {GUARD_TOL_SIGMA} sigma of {REF_COL})")
        emit()
        emit("| module | " + TAG + " (sigma) | " + REF_COL + " (sigma) | delta | within tol |")
        emit("|---|---|---|---|---|")
        worst, guard_ok = 0.0, True
        for mod in [m for m in full.module.unique() if m != AIS_LABEL]:
            c = full[(full.module == mod) & (full.arm == TAG)]
            r = full[(full.module == mod) & (full.arm == REF_COL)]
            if c.empty or r.empty:
                emit(f"| {mod} | - | - | (row absent) | ? |"); continue
            d = float(c.rmse_sd.iloc[0]) - float(r.rmse_sd.iloc[0])
            ok = abs(d) <= GUARD_TOL_SIGMA
            if mod != "TOTAL":
                worst = max(worst, abs(d)); guard_ok = guard_ok and ok
            emit(f"| {mod} | {float(c.rmse_sd.iloc[0]):.2f} | {float(r.rmse_sd.iloc[0]):.2f} | "
                 f"{d:+.3f} | {'yes' if ok else '**NO**'} |")
        emit()
        emit(f"### ==> GUARD: **{'PASS' if guard_ok else 'FAIL'}** "
             f"(largest non-Antarctic, non-TOTAL move {worst:.3f} sigma; tol {GUARD_TOL_SIGMA}). "
             f"TOTAL is a composite and is reported, not graded.")
    else:
        fails += 1
    emit()

    # ---- DECOMPOSITION: explicitly NOT a criterion ---------------------------------------------
    # WHY THIS IS HERE. L32 changed TWO things at once -- the AIS target AND the noise model --
    # and won the satellite era (1993-2026: 1.01 vs L27's 1.27) while losing the full period
    # (0.88 vs 0.70). L34 isolates the noise fix on the champion's own target, so the SUB-WINDOW
    # rows are what actually answer "which of the two changes bought which result". The PRIMARY
    # is the full period and nothing here displaces it.
    #
    # *** THIS BLOCK IS DESCRIPTIVE AND MUST NEVER BE READ AS A CRITERION. *** It was written
    # before any candidate number existed, which is the only thing that makes it honest; a
    # sub-window promoted to a decider AFTER the full period disappoints is the classic move
    # this whole read-out exists to prevent.
    if os.path.exists(bench):
        emit(f"## {DECOMP_NAME}")
        emit()
        h = parse_bench(bench)
        # Suppress the third column when the candidate IS that arm -- a self-comparison is not a
        # decomposition, and printing it invites reading noise as signal.
        third = f"{OUT}/bench_ladrillo_{DECOMP_THIRD_ARM}.md"
        h3 = (parse_bench(third) if (os.path.exists(third) and TAG != DECOMP_THIRD_ARM)
              else pd.DataFrame(columns=h.columns))
        wins = [w for w in h.window.unique() if w != HINDCAST_WINDOW]
        emit(f"| window | {TAG} | {REF_COL} | {DECOMP_THIRD_ARM} (both changes) | reading |")
        emit("|---|---|---|---|---|")
        for w in [HINDCAST_WINDOW] + sorted(wins):
            def g(df, arm):
                r = df[(df.module == AIS_LABEL) & (df.window == w) & (df.arm == arm)]
                return float(r.rmse_sd.iloc[0]) if len(r) else None
            cv, rv = g(h, TAG), g(h, REF_COL)
            tv = g(h3, DECOMP_THIRD_ARM)
            if cv is None or rv is None:
                emit(f"| {w} | - | - | - | (rows absent) |"); continue
            # who is closest to the observations in this window
            cands = {TAG: cv, REF: rv}
            if tv is not None:
                cands[DECOMP_THIRD_ARM] = tv
            best = min(cands, key=cands.get)
            emit(f"| {'**' + w + '**' if w == HINDCAST_WINDOW else w} | {cv:.2f} | {rv:.2f} | "
                 f"{'-' if tv is None else f'{tv:.2f}'} | best = **{best}** |")
        emit()
        if len(h3):
            emit(f"⚠ `{DECOMP_THIRD_ARM}` is scored here out of its OWN bench file, which is a "
                 f"different run of the ruler; treat its column as indicative and re-score it in "
                 f"one run before quoting a {TAG}-vs-{DECOMP_THIRD_ARM} difference as a result.")
            emit()
        emit(f"**What this block can and cannot say.** If `{TAG}` picks up the satellite era "
             f"while keeping the full period, the noise fix alone bought `{DECOMP_THIRD_ARM}`'s "
             f"win and the target swap was not needed. If it does not, the win was the target. "
             f"Either way this is a DESCRIPTION of the decomposition, not a promotion criterion.")
        emit()

    # ---- COST A, with the like-for-like gate ---------------------------------------------------
    emit(f"## COST A -- {COSTA_NAME}")
    emit()
    pc, pr = f"{OUT}/postpred_{TAG}_bias.csv", f"{OUT}/postpred_{REF}_bias.csv"
    if need(pc) and need(pr):
        dc = pd.read_csv(pc); dr = pd.read_csv(pr)
        # postpred_*_bias.csv lists 2025 TWICE -- once in the anchor block and once in the
        # recent-years block. The rows are byte-identical, so dedupe is safe, but it is ASSERTED
        # rather than assumed: a non-identical duplicate would mean two different scorings.
        def ais_rows(d, who):
            d = d[d.component == "ais"]
            dup = d[d.year.duplicated(keep=False)]
            for y in sorted(set(dup.year)):
                g = d[d.year == y]
                if g.drop_duplicates().shape[0] > 1:
                    emit(f"  *** {who}: year {y} appears {len(g)}x with DIFFERENT values -- "
                         f"two scorings in one file; not deduped, COST A unsafe ***")
            return d.drop_duplicates(subset="year", keep="first").set_index("year")
        dc = ais_rows(dc, TAG); dr = ais_rows(dr, REF)
        yrs = [y for y in COSTA_YEARS if y in dc.index and y in dr.index]
        # *** THE GATE ***
        bad = [(y, float(dc.loc[y, "obs"]), float(dr.loc[y, "obs"]))
               for y in yrs if abs(float(dc.loc[y, "obs"]) - float(dr.loc[y, "obs"])) > 1e-9]
        if bad:
            emit("  *** LIKE-FOR-LIKE GATE FAILED -- the two postpred files were scored against "
                 "DIFFERENT observation targets. COST A IS NOT GRADED. ***")
            for y, o1, o2 in bad:
                emit(f"      {y}: {TAG} obs {o1:.6f}  vs  {REF} obs {o2:.6f}")
            emit("  Rebuild the champion's postpred on the live target before reading any bias "
                 "difference; the difference below would be a property of the ruler.")
            fails += 1
        else:
            emit(f"Like-for-like gate PASSED: `obs` identical at {yrs} in both files "
                 f"(max |delta| < 1e-9), so the bias difference is a property of the ARM.")
            emit()
            emit(f"| year | obs (cm) | {TAG} bias | in90 | {REF} bias | in90 | change |")
            emit("|---|---|---|---|---|---|---|")
            for y in yrs:
                bc, br = float(dc.loc[y, "bias"]), float(dr.loc[y, "bias"])
                mv = "closer to obs" if abs(bc) < abs(br) else ("further" if abs(bc) > abs(br) else "same")
                emit(f"| {y} | {float(dc.loc[y,'obs']):+.4f} | {bc:+.4f} | "
                     f"{'yes' if bool(dc.loc[y,'in90']) else '**no**'} | {br:+.4f} | "
                     f"{'yes' if bool(dr.loc[y,'in90']) else '**no**'} | {mv} ({abs(bc)-abs(br):+.4f}) |")
            emit()
            emit("### ==> COST A is REPORTED, not graded. A prediction about its direction is not a criterion.")
    else:
        fails += 1
    emit()

    # ---- COST B --------------------------------------------------------------------------------
    emit(f"## COST B -- {COSTB_NAME}")
    emit()
    mc = f"{OUT}/ladrillo_model_comparison_{TAG}.csv"
    frozen_mr = FROZEN_REF_TMPL.format(ref=REF)
    if os.path.exists(frozen_mr):
        mr, mr_kind = frozen_mr, "FROZEN snapshot (same champion the PRIMARY ruler uses)"
    else:
        mr, mr_kind = f"{OUT}/ladrillo_model_comparison_{REF}.csv", \
            "*** live outputs/ file -- the frozen snapshot is MISSING, so this may be a " \
            "DIFFERENT vintage of the champion than the PRIMARY ruler ***"
    if need(mc) and need(mr):
        emit(f"Champion source: `{mr}` -- {mr_kind}.")
        emit()
        def band(p):
            d = pd.read_csv(p)
            d = d[(d.source.str.lower() == "ladrillo") & (d.component == "ais")]
            return d.set_index(["scenario", "year"]), sorted(set(d.band_basis))
        (bc, bbc), (br, bbr) = band(mc), band(mr)
        # The two files are SEPARATE RUNS on different days. A width ratio across them is only a
        # property of the arms if the band is the same KIND of object in both (fixed-driver vs
        # joint). Checked, not assumed. The AIS component is insulated from the LWS mode, which
        # is the other thing that moved between these vintages.
        if bbc != bbr:
            emit(f"  *** BAND-BASIS MISMATCH -- `{TAG}` is {bbc}, `{REF}` is {bbr}. "
                 f"These are different kinds of band; the ratio below is NOT a property of the "
                 f"arms. COST B unsafe. ***"); fails += 1
        else:
            emit(f"Band basis identical in both files: {bbc[0]}. "
                 f"Written {datetime.datetime.fromtimestamp(os.path.getmtime(mc)):%Y-%m-%d %H:%M} "
                 f"(`{TAG}`) and "
                 f"{datetime.datetime.fromtimestamp(os.path.getmtime(mr)):%Y-%m-%d %H:%M} "
                 f"(`{REF}`) -- separate runs.")
            emit()
            emit("⚠ The AIS component is NOT fully insulated from a re-run: between the frozen "
                 "L27 snapshot and the live outputs/ file, all 9 Ladrillo AIS medians moved in "
                 "the SAME direction (+0.004 to +0.008 cm, growing with horizon). Cause not "
                 "established; <= 0.01% of band width, so immaterial to a width ratio. Quoted "
                 "here so the uniformity is on the record rather than rediscovered.")
            emit()
        emit(f"| scenario | year | {TAG} med | {REF} med | {TAG} p05-p95 | {REF} p05-p95 | ratio |")
        emit("|---|---|---|---|---|---|---|")
        ratios = []
        for s in COSTB_SSPS:
            for y in COSTB_YEARS:
                if (s, y) not in bc.index or (s, y) not in br.index:
                    emit(f"| {s} | {y} | - | - | - | - | (absent) |"); continue
                rc, rr = bc.loc[(s, y)], br.loc[(s, y)]
                wc = float(rc.p95) - float(rc.p05); wr = float(rr.p95) - float(rr.p05)
                ratios.append(wc / wr if wr else float("nan"))
                emit(f"| {s} | {y} | {float(rc.med):.2f} | {float(rr.med):.2f} | {wc:.2f} | "
                     f"{wr:.2f} | **{wc/wr:.2f}x** |" if wr else
                     f"| {s} | {y} | {float(rc.med):.2f} | {float(rr.med):.2f} | {wc:.2f} | 0 | n/a |")
        if ratios:
            emit()
            emit(f"### ==> COST B: width ratio {min(ratios):.2f}x-{max(ratios):.2f}x. "
                 f"⚠ If the PRIMARY is a win AND these are all >1, the win is bought with band width "
                 f"and is NOT a win on the pre-registered reading.")
    else:
        fails += 1
    emit()

    # ---- MECHANISM: not from a file ------------------------------------------------------------
    emit("## MECHANISM -- 2018-23 dynamics anomaly (confirms the floor fired; does NOT decide promotion)")
    emit()
    emit("Not read from a product. Run, with the **IMBIE** target live:")
    emit()
    emit("```")
    emit(f"julia --project=julia_v2 julia/diag_ais_channel_separation.jl 1000 --arms={REF},{TAG}")
    emit("```")
    emit()
    emit(f"and compare `dis_trend_anom` against {REF}'s and IMBIE's. ⚠ The LEVEL channel in that "
         f"script is evaluated at a COMMON (sigma, rho); read the arm-to-arm difference under BOTH "
         f"settings, and remember a bounded sigma is not comparable to a free one.")
    emit()

    # ---- provenance ----------------------------------------------------------------------------
    emit("---")
    emit()
    emit("## Provenance")
    emit()
    emit(f"| input | md5 |")
    emit("|---|---|")
    for p in sorted(inputs):
        emit(f"| `{p}` | `{inputs[p]}` |")
    emit()
    emit(f"*{SCRIPT} | tag {TAG} | ref {REF_COL} | thresholds WIN<={PRIMARY_WIN_MAX} "
         f"LOSS>={PRIMARY_LOSS_MIN} GUARD={GUARD_TOL_SIGMA}sigma | "
         f"{datetime.datetime.now():%Y-%m-%d %H:%M} | {fails} ungraded criterion(a)*")

    txt = "\n".join(lines) + "\n"
    dest = f"{OUT}/readout_prereg_criteria_{TAG}.md"
    open(dest, "w", encoding="utf-8").write(txt)
    print(txt)
    print(f"Wrote {dest}", file=sys.stderr)
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
