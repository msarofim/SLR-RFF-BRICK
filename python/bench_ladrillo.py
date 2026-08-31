#!/usr/bin/env python3
"""
bench_ladrillo.py — THE STANDING LADRILLO BENCHMARK. One command, four arms,
                    five blocks, a machine-readable CSV and a report.

Marcus 2026-08-25: *"make these comparisons durable. E.g. BRICK2.0 versus the full
observational period and against MAGICC and FACTS and other constraints for future
projections. Then whenever we update a Ladrillo module we can quickly see how it
matches that comparison. And keep the best performing Ladrillo module in the
comparison as well, so we can quickly check if any changes improve against that
best version."*

    source ~/climate-env/bin/activate
    python python/bench_ladrillo.py --tag=L15
    python python/bench_ladrillo.py --tag=L15 --freeze
    python python/bench_ladrillo.py --tag=L15 --promote --why="ssp126 tail fixed"

THE ARMS. candidate (live, `outputs/`), champion (FROZEN, `benchmark/reference/<tag>/`),
BRICK 2.0 and the literature (FROZEN, `benchmark/reference/_fixed/`). The comparators are
frozen COPIES on purpose: a benchmark whose reference arms move with `outputs/` cannot
compare a score from today with a score from six months ago.

WHAT IT DOES **NOT** DO. It runs no model and reads no chain. Every number is
post-processing over files a projection/hindcast run already wrote. Producing those files
for a new tag is the expensive step and is upstream of this script — see
benchmark/README.md for the four inputs a taggable arm must have on disk.

THE THREE CAVEATS THAT TRAVEL WITH EVERY VERDICT, re-printed in the report:
  * the hindcast is IN-SAMPLE for every Ladrillo arm and OUT-OF-SAMPLE for BRICK 2.0, so
    it RANKS IN ONE DIRECTION ONLY -- it can reject, it cannot certify;
  * Ladrillo-fixed and BRICK 2.0 bands are posterior-parameter spread; Ladrillo-JOINT,
    FACTS and MAGICC carry climate uncertainty. Only the joint band is scored against
    them (`like_for_like_forcing`);
  * part of the width is a PRIOR, not an inference (78% of ssp585 2300 AIS is
    `antarctic_lambda`), so narrowness is never scored as a win there.

Writes outputs/bench_ladrillo_<TAG>.csv and outputs/bench_ladrillo_<TAG>.md
"""
import collections
import hashlib
import json
import os
import shutil
import subprocess
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCH = os.path.join(REPO, "benchmark")
REF = os.path.join(BENCH, "reference")
FIXED = os.path.join(REF, "_fixed")
CHAMPIONS_JSON = os.path.join(BENCH, "champions.json")
# Comparator classification (see the file's own header for the line drawn and why).
# Anything not listed is class `model`.
CLASSES_CSV = os.path.join(BENCH, "comparator_classes.csv")
# Extra comparators the FACTS/MAGICC extraction does not carry, each with its citation.
# This is the extension slot: adding a literature constraint means adding rows here.
EXTRA_CSV = os.path.join(BENCH, "literature_extra.csv")

# ------------------------------------------------------------------ constants
# Every label, filename and console line below derives from these names, so a
# window or horizon cannot be changed without its label following it.
BENCH_VERSION = "1.0"
REF_WINDOW = (1995, 2005)          # hindcast re-reference, shared by both arms
PROJ_REF_WINDOW = (1995, 2014)     # AR6 projection re-reference
WINDOWS = [("full", None), ("1920-1949", (1920, 1949)),
           ("1950-1992", (1950, 1992)), ("1993-2026", (1993, 2026))]
RATE_WINDOW = (1993, 2026)         # the altimetry era: where a rate is measurable
ACCEL_WINDOW = (1900, 2026)        # the whole record: an acceleration needs the span
HORIZONS = [2100, 2150, 2300]
## FACTS covers 2100 and 2150; MAGICC-SLR covers 2100-2300 (its run always did -- our
## extractor was cutting it at 2100 until 2026-08-25). 2300 therefore has exactly ONE
## comparator and its verdicts are capped at WARN by MIN_LIT_FOR_MEDIAN.
LIT_HORIZONS = [2100, 2150, 2300]
SSPS = ["ssp126", "ssp245", "ssp585"]
SEP_LO, SEP_HI = "ssp126", "ssp585"
# How close to the literature bracket's EDGE still counts as inside it. Marcus's
# standing instruction is that a plausibility tolerance is scaled to the SAMPLED
# SPREAD, never picked as a bare number (`tolerance_scaled_to_spread`) -- so this is
# a fraction of the comparators' OWN range, and where there is only one comparator
# there is no range and no tolerance.
SEP_EDGE_TOL_FRAC = 0.25
# When the OBSERVED value of a statistic is itself within this many sigma of zero, the
# RATIO model/obs is not interpretable -- its denominator is consistent with zero, so the
# ratio is unbounded and "0.18x observed" reads as a deficit when it is arithmetic noise
# (`curvature_needs_an_error_bar`, `endpoint_division_is_not_a_ratio_band`). The
# DIFFERENCE model-obs is still perfectly gradeable in units of the same se, so the
# verdict stays on z and only the RATIO is suppressed. These are two different questions
# and conflating them either invents a finding or erases a real one.
TARGET_RESOLVED_SIGMA = 2.0
# A p05-p95 spread is ARITHMETICALLY BLIND to a mode carrying under 5% of the mass, and
# our ssp126 AIS band is exactly that: 3.75-6.30% of draws tip and the whole tipping tail
# sits outside the statistic (`diag_ais_ssp126_tail_anatomy.py`). Scoring such a cell as
# "0.24-0.33x the literature spread" reports a property of the QUANTILE, not of the model.
# The tell is generic and needs no tipping calculation: compare p05-p99 with p05-p95. For a
# GAUSSIAN that ratio is fixed at (z99+z05)/(z95+z05) = 1.207, so the reference is derived
# rather than picked, and a cell is flagged when it exceeds the Gaussian value by more than
# TAIL_RATIO_FLAG. Our unimodal cells sit at 1.28-1.50; the bimodal ssp126 ones at 3.55-8.45.
QTAIL = 99
TAIL_RATIO_GAUSSIAN = 1.207
TAIL_RATIO_FLAG = 2.0
# Below this many comparators, a "median spread" is not a summary of anything -- at n=2 it
# is the MEAN of the two, a width neither module produces. Such cells are still scored (the
# comparison is not worthless) but the verdict is capped at WARN and the note says n.
MIN_LIT_FOR_MEDIAN = 3
QLO, QHI = 5, 95                   # the spread definition, p05-p95, everywhere

# (key, label, Ladrillo postpred stem, BRICK 2.0 postpred stem, target column)
COMPONENTS = [("ais", "AIS", "ais", "ais", "ais"),
              ("glaciers", "glaciers", "glaciers", "gsic", "gsic"),
              ("gis", "Greenland", "gis", "gis", "gis"),
              ("te", "thermal exp.", "te", "te", "steric"),
              ("lws", "land water", None, None, "lws"),
              ("total", "TOTAL", "total", "total", "dang")]
COMP_LABEL = {k: lab for k, lab, *_ in COMPONENTS}

# Verdict thresholds, in the component's OWN target 1-sigma. A hindcast miss is only
# a failure relative to what the observations can resolve.
HIND_PASS_SIGMA, HIND_WARN_SIGMA = 1.0, 3.0
# Projection: a median inside the literature RANGE passes; outside it, the verdict is
# how far outside relative to the literature median.
PROJ_WARN_RATIO = 2.0
# Spread: scored against the literature MEDIAN spread. Both directions matter --
# too narrow is as wrong as too wide -- except where the width is a known prior.
SPREAD_PASS = (0.5, 2.0)
# ⚠ A MEDIAN SPREAD IS ONLY A SUMMARY IF THE COMPARATORS AGREE. At ssp585@2150 the four
# model-based AIS comparators span 8.4x (ar5AIS 48.7 cm to deconto21 408.4) and split into
# a no-MICI pair and a MICI/MAGICC pair; the median lands in the gap BETWEEN the two groups,
# so it belongs to neither. The exact test is to score against each comparator on its own
# and ask whether the median's verdict is one a MAJORITY of them share -- no threshold to
# pick, and it demotes cells where we look good (ssp245@2150) as readily as ones where we
# do not. Where it fails, the verdict is capped at WARN in BOTH directions: the median can
# no more earn a PASS than a FAIL. (`diag_total_spread_ssp585_2150.py`, 2026-08-25.)
SPREAD_MAJORITY_REQUIRED = True
# HEAD-TO-HEAD ON PROJECTION MEDIANS. Two rules stop the comparison over-reading itself:
#  * a difference in |ratio - 1| below this is a TIE, not a win. Without it the report
#    calls 1.455 vs 1.452 a loss.
#  * ⚠ A PROJECTION WIN BY AN ARM THAT FAILS THE OBSERVATIONS IS NOT A WIN. BRICK 2.0's
#    glaciers sit closer to the literature median at three cells -- while its glacier
#    hindcast misses by 3.30 sd and its 1993-2026 rate by z = +2.39. That is a
#    COMPENSATING ERROR, and reporting it as "better" would let a model be rewarded for
#    running hot in projection because it runs hot in hindcast too. Such cells are marked
#    WORSE(unearned) and the reason is printed.
H2H_TIE = 0.02
# Cells where narrowness must NOT be scored as a win: the width there is the
# antarctic_lambda paleo prior, 78% of it (`ais_spread_is_lambda_prior`).
PRIOR_WIDTH_CELLS = {("ais", "ssp585")}
LAMBDA_SHARE_2300 = 0.78
# Components whose spread is ZERO BY CONSTRUCTION, not by failure. LWS is a seeded
# constant with no forcing dependence (`handoff_2026-08-25` §E): scoring its width
# against a literature width would report a design decision as a defect every run.
ZERO_SPREAD_BY_CONSTRUCTION = {"lws"}
# IMBIE whole-sheet |loss|/sigma across four windows (diag_ais_region_lit_check.py):
# the reason the satellite era separates no two AIS models.
IMBIE_SNR = (0.95, 1.44)

CAVEATS = [
    "HINDCAST RANKS IN ONE DIRECTION ONLY -- in-sample for every Ladrillo arm, "
    "out-of-sample for BRICK 2.0. It can REJECT an arm; a small fitted bias is not skill.",
    "BANDS ARE NOT ONE OBJECT -- Ladrillo-fixed is posterior-parameter spread; "
    "Ladrillo-JOINT, FACTS and MAGICC carry climate uncertainty. Only the JOINT band is "
    "scored against the literature. NOTE 2026-08-30: BRICK 2.0 NOW HAS A JOINT ARM TOO "
    "(scope_slr_fairunc_oldbrick.jl), but THIS BENCHMARK still takes BRICK 2.0 from the "
    "shipped FIXED panel (brick20_projection), so BRICK widths here remain fixed-driver. "
    "ladrillo_model_comparison.py DOES use the joint arm. Do not read a width comparison "
    "against BRICK 2.0 out of this table -- read it out of the comparison.",
    f"SOME WIDTH IS A PRIOR, NOT AN INFERENCE -- {LAMBDA_SHARE_2300:.0%} of the ssp585 2300 "
    "AIS band is antarctic_lambda's paleo prior, so narrowness is never scored as a win "
    "at " + ", ".join(f"{c}/{s}" for c, s in sorted(PRIOR_WIDTH_CELLS)) + ".",
    f"WHERE THE OBSERVED STATISTIC IS UNDER {TARGET_RESOLVED_SIGMA} SIGMA FROM ZERO the "
    "RATIO model/obs is suppressed as uninterpretable, but the DIFFERENCE is still graded "
    "on z -- being 3 sigma from a value that is itself 1 sigma from zero is still a miss.",
    f"THE MODERN AIS RATE CANNOT REJECT ZERO -- IMBIE whole-sheet loss is "
    f"{IMBIE_SNR[0]}-{IMBIE_SNR[1]} sigma from zero, so the {RATE_WINDOW[0]}-{RATE_WINDOW[1]} "
    "window separates no two AIS models however different they are.",
    f"A p{QLO}-p{QHI} SPREAD IS BLIND TO A MODE UNDER {100-QHI}% OF THE MASS -- cells whose "
    f"p05-p{QTAIL}/p05-p{QHI} exceeds {TAIL_RATIO_FLAG}x the Gaussian {TAIL_RATIO_GAUSSIAN} are "
    "marked N/A(bimodal) and NOT scored on width; quote the mean and the tipped fraction there.",
    "ssp245@2300 IS A THRESHOLD ARTIFACT -- 48.3% of draws tip, so its MEDIAN is "
    "bimodal-fragile. Quote the mean and the tipped fraction there, never the bare median.",
]

# --------------------------------------------------------- arm file resolution
# One place that knows what a taggable arm needs on disk. Adding an input to the
# benchmark means adding it here, and both the freezer and the reader see it.
def live_paths(tag):
    o = os.path.join(REPO, "outputs")
    p = {"postpred": os.path.join(o, f"postpred_{tag}_components_timeseries.csv"),
         "comparison": os.path.join(o, f"ladrillo_model_comparison_{tag}.csv")}
    for s in SSPS:
        # ⚠ PREFER THE TAPPED JOINT DRAWS (2026-08-30). The benchmark scores the JOINT arm
        # (joint_stats), and ladrillo_model_comparison.py reports the TAPPED joint arm, so
        # taking the untapped draws here would freeze a snapshot whose `comparison` and
        # `draws` disagree about what Ladrillo's band IS -- the same arm mismatch that made
        # the joint band unusable for 6 cells. The Greenland tap is part of the shipped
        # module, so the tapped arm is the one the benchmark is meant to score.
        tapped = os.path.join(
            o, f"scope_slr_fairunc_draws_{s}_spliced_{tag}_tap4p69K_V5p64m_tau800.csv")
        untapped = os.path.join(o, f"scope_slr_fairunc_draws_{s}_spliced_{tag}.csv")
        p[f"draws_{s}"] = tapped if os.path.exists(tapped) else untapped
    return p


def frozen_paths(tag):
    d = os.path.join(REF, tag)
    p = {"postpred": os.path.join(d, "postpred_components_timeseries.csv"),
         "comparison": os.path.join(d, "model_comparison.csv")}
    for s in SSPS:
        p[f"draws_{s}"] = os.path.join(d, f"draws_{s}_spliced.csv.gz")
    return p


FIXED_FILES = {
    "targets": ("outputs/recalib_targets_ext.csv", "recalib_targets_ext.csv"),
    "brick20_hindcast": ("outputs/postpred_oldbrick_components_timeseries.csv",
                         "postpred_oldbrick_components_timeseries.csv"),
    "brick20_projection": ("outputs/ssps_components_2300_oldbrick.csv",
                           "ssps_components_2300_oldbrick.csv"),
    # The literature arm's SOURCES, frozen for provenance and hashed. The rows the
    # benchmark actually reads come from `literature` below, which is extracted once
    # from a comparison file; these two are kept so that a changed FACTS or MAGICC
    # release is VISIBLE as a hash change rather than silently re-scoring every arm.
    ## ⚠ REPOINTED 2026-08-31 to the SHARED-machinery extract. It was
    ## outputs/facts_components_n200.csv (FACTS on its OWN internal FaIR 1.6.4); the FACTS
    ## column now runs on the injected FaIR 2.2.4 calib 1.6.0 driver on BOTH scenario sets.
    ## The superseded arm is preserved verbatim, with the size of the move, under
    ## benchmark/reference/_fixed_archive_20260831_facts_internal_fair164/.
    "facts_source": ("outputs/facts_components_shared_n200.csv",
                     "facts_components_shared_n200.csv"),
    "magicc_source": ("data/comparison/magicc_nauels_components.csv",
                      "magicc_nauels_components.csv"),
    "literature": (None, "literature_rows.csv"),
}


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


def _git_head():
    try:
        return subprocess.check_output(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                                       text=True).strip()
    except Exception:
        return "unknown"


def freeze(tag):
    """Snapshot a tag's live outputs into benchmark/reference/<tag>/ with a manifest.

    The draws are gzipped (11 MB -> 3 MB). They are stored RAW rather than as
    pre-computed percentiles on purpose: if a metric definition here ever changes,
    the champion's score must be recomputable under the NEW definition, or the
    comparison silently mixes two metrics."""
    d = os.path.join(REF, tag)
    os.makedirs(d, exist_ok=True)
    man = {"tag": tag, "frozen_git_head": _git_head(),
           "bench_version": BENCH_VERSION, "files": {}}
    for key, src in live_paths(tag).items():
        if not os.path.exists(src):
            raise SystemExit(f"cannot freeze {tag}: missing {os.path.relpath(src, REPO)}")
        dst = frozen_paths(tag)[key]
        if dst.endswith(".gz"):
            import gzip
            with open(src, "rb") as fi, gzip.open(dst, "wb") as fo:
                shutil.copyfileobj(fi, fo)
        else:
            shutil.copyfile(src, dst)
        man["files"][key] = {"source": os.path.relpath(src, REPO), "sha256_16": _sha(src),
                             "frozen_as": os.path.relpath(dst, REPO)}
        print(f"  froze {key:16s} <- {os.path.relpath(src, REPO)}")
    with open(os.path.join(d, "manifest.json"), "w") as f:
        json.dump(man, f, indent=2)
    print(f"  wrote {os.path.relpath(os.path.join(d, 'manifest.json'), REPO)}")


def freeze_fixed(lit_from=None):
    """Snapshot the arms that never move: obs targets, BRICK 2.0, FACTS, MAGICC."""
    os.makedirs(FIXED, exist_ok=True)
    man = {"frozen_git_head": _git_head(), "bench_version": BENCH_VERSION, "files": {}}
    for key, (rel, name) in FIXED_FILES.items():
        if rel is None:
            continue
        src = os.path.join(REPO, rel)
        if not os.path.exists(src):
            print(f"  ! SKIP {key}: {rel} does not exist yet")
            continue
        shutil.copyfile(src, os.path.join(FIXED, name))
        man["files"][key] = {"source": rel, "sha256_16": _sha(src)}
        print(f"  froze {key:20s} <- {rel}")
    # The literature rows themselves, extracted once from a comparison file so that the
    # arm no longer rides inside a per-tag output.
    if lit_from and os.path.exists(lit_from):
        d = pd.read_csv(lit_from)
        d = d[~d.source.isin(["Ladrillo", "BRICK 2.0"])]
        d.to_csv(os.path.join(FIXED, FIXED_FILES["literature"][1]), index=False)
        man["files"]["literature"] = {"source": os.path.relpath(lit_from, REPO),
                                      "sha256_16": _sha(lit_from),
                                      "n_rows": int(len(d)),
                                      "sources": sorted(d.source.unique().tolist())}
        print(f"  froze {'literature':20s} <- {os.path.relpath(lit_from, REPO)} "
              f"({len(d)} rows)")
    with open(os.path.join(FIXED, "manifest.json"), "w") as f:
        json.dump(man, f, indent=2)


def fixed(key):
    p = os.path.join(FIXED, FIXED_FILES[key][1])
    return p if os.path.exists(p) else os.path.join(REPO, FIXED_FILES[key][0])


def literature_rows(cand_comparison):
    """The FACTS + MAGICC-SLR rows, from the FROZEN copy when one exists.

    These rows do not depend on the Ladrillo tag -- they are the same literature in
    every comparison file -- but until they were frozen they travelled INSIDE each
    candidate's own `ladrillo_model_comparison_<TAG>.csv`, so a regenerated FACTS or
    MAGICC extraction would have moved the comparator under every past score without
    leaving a trace. Frozen once, checked against the candidate's copy on every run:
    a disagreement is REPORTED, never silently resolved, because either file could be
    the newer one and that is a decision, not a default."""
    live = pd.read_csv(cand_comparison)
    live = live[~live.source.isin(["Ladrillo", "BRICK 2.0"])]
    def add_extra(df):
        if not os.path.exists(EXTRA_CSV):
            return df
        e = pd.read_csv(EXTRA_CSV, comment="#")
        if e.empty:
            return df
        print(f"  + {len(e)} extra comparator row(s) from "
              f"{os.path.relpath(EXTRA_CSV, REPO)}: "
              f"{', '.join(sorted(e.module.unique()))}")
        return pd.concat([df, e[[c for c in df.columns if c in e.columns]]],
                         ignore_index=True)

    p = fixed("literature")
    if not os.path.exists(p):
        return add_extra(live), "live (not yet frozen -- run --freeze-fixed)"
    frozen = pd.read_csv(p)
    k = ["source", "module", "scenario", "component", "year"]
    j = frozen.merge(live, on=k, suffixes=("_f", "_l"), how="outer", indicator=True)
    moved = j[(j._merge != "both") |
              ((j.med_f - j.med_l).abs() > 1e-6)]
    if len(moved):
        print(f"! LITERATURE ARM MOVED: {len(moved)} of {len(j)} rows differ between the "
              f"frozen copy and {os.path.basename(cand_comparison)}. Scoring on the FROZEN "
              "copy. Re-freeze deliberately if the new extraction is the one you want.")
    return add_extra(frozen), "frozen"


def _b20_obs_fail(rows, comp):
    """Which OBSERVATIONAL block BRICK 2.0 fails for this component, as a phrase, or ""."""
    bad = [r for r in rows if r["arm"] == "BRICK 2.0" and r["verdict"] == "FAIL" and
           r["component"] == comp and r["block"] in ("H", "R")]
    if not bad:
        return ""
    blocks = sorted({("its hindcast" if r["block"] == "H" else "its observed rate/accel")
                     for r in bad})
    return " and ".join(blocks) + " FAILs"


def _h2h_verdict(ours, theirs, rows, comp):
    """BETTER / SAME / WORSE on |ratio - 1|, with the two rules above applied."""
    d = abs(ours - 1.0) - abs(theirs - 1.0)
    if abs(d) < H2H_TIE:
        return "SAME"
    if d < 0:
        return "BETTER"
    return "WORSE(unearned)" if _b20_obs_fail(rows, comp) else "WORSE"


def spread_side(ratio):
    """Which side of the SPREAD_PASS band a model/comparator width ratio falls on."""
    return ("in" if SPREAD_PASS[0] <= ratio <= SPREAD_PASS[1]
            else ("low" if ratio < SPREAD_PASS[0] else "high"))


def spread_majority(ours_cm, comparator_spreads, median_ratio):
    """Does the MEDIAN comparator's verdict have a majority among the comparators scored
    ONE AT A TIME? Returns (has_majority, per-comparator sides). A median spread is a
    summary only if the set it summarises agrees; where it does not, the median lands
    between groups and belongs to neither, and the verdict is capped at WARN in BOTH
    directions -- see SPREAD_MAJORITY_REQUIRED."""
    per = [spread_side(ours_cm / x) for x in comparator_spreads]
    return per.count(spread_side(median_ratio)) * 2 > len(per), per


def _selftest():
    """⚠ MUTATION TEST. A gate that has only ever fired in one direction has not been
    shown to work -- as of L14 every cell the majority rule touches is a DEMOTION
    (PASS -> WARN), so the other directions are exercised here instead of by the data."""
    ok, why = True, []

    def chk(label, got, want):
        nonlocal ok
        ok &= got == want
        why.append(f"    {'ok  ' if got == want else 'FAIL'} {label}: {got} (want {want})")

    # [1] DEMOTE. The real total ssp585@2150 set: the median says `in`, but scored one at
    # a time 2 of 4 say `low`, so `in` is not a majority and the PASS is not earned.
    chk("demote PASS->WARN (real total ssp585@2150)",
        spread_majority(147.38, [77.93, 150.61, 414.71, 403.38], 0.532),
        (False, ["in", "in", "low", "low"]))
    # [2] RESCUE a FAIL. Median comparator is huge, but half the set puts us inside the
    # band -- the FAIL is as unearned as the PASS in [1], and is capped the same way.
    chk("rescue FAIL->WARN (median low, no majority)",
        spread_majority(10.0, [11.0, 12.0, 100.0, 105.0], 10.0 / 56.0),
        (False, ["in", "in", "low", "low"]))
    # [3] A SUPPORTED FAIL MUST SURVIVE. This is Greenland ssp126@2100: 2 of 3 comparators
    # agree we are too narrow, so the rule must NOT touch it.
    chk("supported FAIL survives (real gis ssp126@2100)",
        spread_majority(4.69, [7.06, 9.57, 17.14], 4.69 / 9.57)[0], True)
    # [4] AN AGREEING SET IS NEVER CAPPED.
    chk("agreeing set untouched", spread_majority(10.0, [11.0, 12.0, 13.0], 10.0 / 12.0)[0], True)
    # [5] ⚠ THE RULE CANNOT INVENT A PASS. A strict `in` majority forces both middle
    # comparators inside the band, hence the median inside it too, so "no majority" is the
    # only way the rule ever fires -- it can cap a verdict, never upgrade one. Asserted so
    # that a future edit which does upgrade one is caught here.
    # ⚠ THE FIRST VERSION OF THIS CHECK WAS WRONG AND ITS FAILURE WAS INFORMATIVE: it
    # flagged [11, 100, 105], where a majority DOES agree with the median -- that is a
    # SUPPORTED FAIL (case [3]), not an upgrade. The property actually being asserted is
    # that a strict `in` majority cannot coexist with a median outside the band, because
    # it forces both middle comparators inside it. That is why the rule can only ever cap.
    def _in_majority_but_median_outside(c):
        r = 10.0 / float(np.median(c))
        _, per = spread_majority(10.0, c, r)
        return per.count("in") * 2 > len(per) and spread_side(r) != "in"
    chk("never upgrades: no (`in` majority, median outside band) set exists",
        any(_in_majority_but_median_outside(c)
            for c in ([11, 12, 100, 105], [11, 12, 13, 100, 105, 110],
                      [11, 12, 13, 100, 105], [11, 100, 105],
                      [11, 12, 13, 14, 100, 105], [11, 12, 13, 14, 15, 100, 105])), False)

    print("SELFTEST " + ("PASS" if ok else "FAIL") +
          " -- spread majority rule: caps in both directions, leaves agreeing sets and "
          "supported FAILs alone, never upgrades")
    print("\n".join(why))
    return 0 if ok else 1


def comparator_classes():
    """{module: class} from benchmark/comparator_classes.csv; anything absent is `model`."""
    if not os.path.exists(CLASSES_CSV):
        return {}
    d = pd.read_csv(CLASSES_CSV, comment="#")
    return dict(zip(d.module.astype(str), d["class"].astype(str)))


def champions():
    with open(CHAMPIONS_JSON) as f:
        return json.load(f)


# ------------------------------------------------------------------- estimators
def _fit_se(v, yrs, w, deg):
    """(coef, AR(1)-inflated se) of the deg-th polynomial term over window w.

    deg=1 -> rate (cm/yr); deg=2 -> acceleration, returned as 2*b2 (cm/yr^2), the
    same estimator as diag_curvature_postsplice_halving.accel_se, so numbers here
    compose with the curvature arc's. The AR(1) inflation is what makes an
    'acceleration deficit' state whether it is resolved at all
    (`curvature_needs_an_error_bar`)."""
    m = (yrs >= w[0]) & (yrs <= w[1]) & np.isfinite(v)
    if m.sum() < deg + 3:
        return np.nan, np.nan
    x = (yrs[m] - w[0]).astype(float)
    y = np.asarray(v[m], dtype=float)
    A = np.vstack([x ** k for k in range(deg + 1)]).T
    b = np.linalg.lstsq(A, y, rcond=None)[0]
    r = y - A @ b
    s2 = r @ r / (len(x) - (deg + 1))
    se = np.sqrt(s2 * np.linalg.inv(A.T @ A)[deg, deg])
    rho = np.corrcoef(r[:-1], r[1:])[0, 1] if len(r) > 3 else 0.0
    infl = np.sqrt(max((1 + rho) / (1 - rho), 1.0)) if np.isfinite(rho) and rho < 1 else 1.0
    scale = 2.0 if deg == 2 else 1.0
    return scale * b[deg], scale * se * infl


def _indep_se(yrs, w, sigma_y, deg):
    """se of the deg-th term under INDEPENDENT per-year observational error sigma_y.

    The third account of the observational uncertainty, and the one that usually
    dominates. [B] estimator scatter measures wiggle about the fitted curve; [C-corr]
    refits the published _lo/_hi envelope, which is very nearly PARALLEL to the central
    series, so the level uncertainty cancels and the rate se it implies is far too
    tight; [C-indep] propagates the SAME published band as independent per-year error
    through the same design matrix. [C-corr] and [C-indep] BRACKET the truth -- the
    year-to-year correlation of a reconstruction's band is unknown -- exactly as
    diag_curvature_deficit_errorbar.py brackets it, and the benchmark takes the
    CONSERVATIVE end so that a 'FAIL' means the miss survives the widest honest bar.
    ⚠ All three omit SHARED-METHOD error across reconstructions, which is rank-one and
    cancels in none of them (`shared_method_error`): every bar here is a lower bound."""
    m = (yrs >= w[0]) & (yrs <= w[1])
    if m.sum() < deg + 3 or not np.isfinite(sigma_y):
        return np.nan
    x = (yrs[m] - w[0]).astype(float)
    A = np.vstack([x ** k for k in range(deg + 1)]).T
    scale = 2.0 if deg == 2 else 1.0
    return scale * sigma_y * np.sqrt(np.linalg.inv(A.T @ A)[deg, deg])


def score_window(p50, lo, hi, obs, window):
    m = obs.notna() & p50.notna()
    if window is not None:
        m &= (obs.index >= window[0]) & (obs.index <= window[1])
    if m.sum() == 0:
        return None
    r = p50[m] - obs[m]
    return dict(n=int(m.sum()), bias=float(r.mean()),
                rmse=float(np.sqrt((r ** 2).mean())), max_abs=float(r.abs().max()),
                coverage90=float(((obs[m] >= lo[m]) & (obs[m] <= hi[m])).mean()))


def verdict_sigma(x):
    a = abs(x)
    return "PASS" if a <= HIND_PASS_SIGMA else ("WARN" if a <= HIND_WARN_SIGMA else "FAIL")


def direction(cand, champ, lower_is_better=True):
    """BETTER / SAME / WORSE against the champion, with a 2% dead band.

    The dead band exists because two arms differing by 1% of a metric are not
    distinguishable by it, and a benchmark that reports every rounding difference
    as a movement trains you to ignore it."""
    if not (np.isfinite(cand) and np.isfinite(champ)):
        return "n/a"
    if abs(champ) < 1e-12:
        return "SAME" if abs(cand) < 1e-12 else ("WORSE" if lower_is_better else "BETTER")
    rel = (cand - champ) / abs(champ)
    if abs(rel) < 0.02:
        return "SAME"
    return ("BETTER" if rel < 0 else "WORSE") if lower_is_better else \
           ("BETTER" if rel > 0 else "WORSE")


# ------------------------------------------------------------------ block [H]
def block_hindcast(rows, cand_tag, champ_tag, cand_p, champ_p, sigma):
    """Every Ladrillo arm and BRICK 2.0 against the full observational record."""
    a = pd.read_csv(cand_p["postpred"]).set_index("year")
    c = pd.read_csv(champ_p["postpred"]).set_index("year") if champ_p else None
    b = pd.read_csv(fixed("brick20_hindcast")).set_index("year")
    tg = pd.read_csv(fixed("targets")).set_index("year")
    base = tg.loc[REF_WINDOW[0]:REF_WINDOW[1], ["ais", "gsic", "gis", "steric"]].mean()
    if base.abs().max() > 1e-3:
        raise SystemExit(f"targets are not zeroed on {REF_WINDOW}: {base.to_dict()} -- "
                         "the arms would not share a baseline")
    yrs = a.index.intersection(b.index)
    out = []
    for key, label, lst, bst, tcol in COMPONENTS:
        if lst is None:
            continue
        obs = (a[f"{lst}_obs"] if f"{lst}_obs" in a else tg[tcol].reindex(a.index)).reindex(yrs)
        arms = [(cand_tag, a, lst, "p05"), ("BRICK 2.0", b, bst, "p5")]
        if c is not None and champ_tag != cand_tag:
            arms.insert(1, (f"{champ_tag}*", c, lst, "p05"))
        for wname, win in WINDOWS:
            got = {}
            for arm, df, stem, plo in arms:
                if f"{stem}_p50" not in df:
                    continue
                s = score_window(df[f"{stem}_p50"].reindex(yrs), df[f"{stem}_{plo}"].reindex(yrs),
                                 df[f"{stem}_p95"].reindex(yrs), obs, win)
                if s is None:
                    continue
                got[arm] = s
                rows.append(dict(block="H", component=key, scenario="", horizon="",
                                 metric=f"hindcast/{wname}", arm=arm, value=s["rmse"],
                                 unit="cm", value_sigma=s["rmse"] / sigma[key],
                                 note=(f"bias {s['bias']:+.4f} cm = {s['bias']/sigma[key]:+.2f} sd; "
                                       f"cov90 {s['coverage90']:.0%}; n={s['n']}"),
                                 verdict=verdict_sigma(s["bias"] / sigma[key])))
            if cand_tag in got:
                for other in [k for k in got if k != cand_tag]:
                    out.append((key, wname, other,
                                got[cand_tag]["rmse"] / got[other]["rmse"],
                                direction(got[cand_tag]["rmse"], got[other]["rmse"])))
    for key, wname, other, ratio, d in out:
        rows.append(dict(block="H", component=key, scenario="", horizon="",
                         metric=f"rmse_ratio/{wname}", arm=f"{cand_tag} vs {other}",
                         value=ratio, unit="ratio", value_sigma=np.nan,
                         note="<1 means the candidate is closer to the observations",
                         verdict=d))


# ------------------------------------------------------------------ block [R]
def block_rate_accel(rows, cand_tag, champ_tag, cand_p, champ_p, sigma):
    """The SLOPE, not just the level -- with an error bar on the observations.

    A cell can sit inside the level band at the last horizon and carry the wrong
    slope there (`score_the_rate_not_the_level`); and a curvature quoted without its
    bar has repeatedly turned out to be unresolved (`curvature_needs_an_error_bar`),
    so every z here is (model - obs) / se(obs) and the verdict names the resolution."""
    a = pd.read_csv(cand_p["postpred"]).set_index("year")
    c = pd.read_csv(champ_p["postpred"]).set_index("year") if champ_p else None
    b = pd.read_csv(fixed("brick20_hindcast")).set_index("year")
    tg = pd.read_csv(fixed("targets")).set_index("year")
    for stat, deg, win, unit in (("rate", 1, RATE_WINDOW, "cm/yr"),
                                 ("accel", 2, ACCEL_WINDOW, "cm/yr2")):
        for key, label, lst, bst, tcol in COMPONENTS:
            if lst is None:
                continue
            obs_s = (a[f"{lst}_obs"] if f"{lst}_obs" in a else tg[tcol].reindex(a.index)).dropna()
            o, ose = _fit_se(obs_s.values, obs_s.index.values.astype(float), win, deg)
            if not np.isfinite(o):
                continue
            # TWO ACCOUNTS OF THE SAME OBSERVATIONAL UNCERTAINTY, and the larger
            # carries the verdict. [B] estimator scatter about the fit is a LOWER
            # bound because it omits the reconstruction's own published band; [C]
            # refits the statistic on the target's _lo/_hi series, which is the
            # perfectly-correlated arm the curvature work used as a bracket
            # (`curvature_needs_an_error_bar`, `diag_curvature_deficit_errorbar.py`).
            # They are NOT independent, so they are never added in quadrature.
            bse = np.nan
            if f"{tcol}_lo" in tg and f"{tcol}_hi" in tg:
                bl = tg[f"{tcol}_lo"].dropna(); bh = tg[f"{tcol}_hi"].dropna()
                rl, _ = _fit_se(bl.values, bl.index.values.astype(float), win, deg)
                rh, _ = _fit_se(bh.values, bh.index.values.astype(float), win, deg)
                if np.isfinite(rl) and np.isfinite(rh):
                    bse = abs(rh - rl) / (2 * 1.645)
            ise = _indep_se(obs_s.index.values.astype(float), win, sigma.get(key, np.nan), deg)
            cse = np.nanmax([ose, bse, ise])
            rows.append(dict(block="R", component=key, scenario="", horizon="",
                             metric=f"{stat}/{win[0]}-{win[1]}/obs", arm="observations",
                             value=o, unit=unit, value_sigma=np.nan,
                             note=f"se: estimator {ose:.4g}, band-correlated {bse:.4g}, "
                                  f"band-independent {ise:.4g}; CONSERVATIVE {cse:.4g} "
                                  f"{unit}; |obs|/se = {abs(o)/cse:.2f}", verdict=""))
            ose = cse
            arms = [(cand_tag, a, lst), ("BRICK 2.0", b, bst)]
            if c is not None and champ_tag != cand_tag:
                arms.insert(1, (f"{champ_tag}*", c, lst))
            for arm, df, stem in arms:
                if f"{stem}_p50" not in df:
                    continue
                s = df[f"{stem}_p50"].dropna()
                v, _ = _fit_se(s.values, s.index.values.astype(float), win, deg)
                if not np.isfinite(v):
                    continue
                z = (v - o) / ose if ose > 0 else np.nan
                resolved = abs(o) / cse >= TARGET_RESOLVED_SIGMA
                rows.append(dict(
                    block="R", component=key, scenario="", horizon="",
                    metric=f"{stat}/{win[0]}-{win[1]}", arm=arm, value=v,
                    unit=unit, value_sigma=z,
                    note=(f"{v/o:.2f}x obs; " if resolved else
                          f"ratio NOT INTERPRETABLE (obs is {abs(o)/cse:.2f} se from zero); ")
                         + f"z={z:+.2f} vs the obs error bar",
                    verdict=("UNRESOLVED" if abs(z) <= 1 else
                             ("WARN" if abs(z) <= 2 else "FAIL"))))


# ------------------------------------------------------------------ block [P]
def joint_stats(path, component, horizon, arm="joint"):
    """(median, mean, p05-p95 spread, p05-p99 spread) of the per-draw joint band."""
    if not os.path.exists(path):
        return (np.nan,) * 4
    d = pd.read_csv(path)
    v = d[(d.horizon == horizon) & (d.component == component) & (d.arm == arm)].value_cm.values
    if len(v) == 0:
        return (np.nan,) * 4
    return (float(np.median(v)), float(np.mean(v)),
            float(np.percentile(v, QHI) - np.percentile(v, QLO)),
            float(np.percentile(v, QTAIL) - np.percentile(v, QLO)))


def block_projection(rows, cand_tag, champ_tag, cand_p, champ_p):
    """Level and spread against FACTS, MAGICC-SLR and BRICK 2.0, on the JOINT band."""
    cmp_, _src = literature_rows(cand_p["comparison"])
    b20 = pd.read_csv(fixed("brick20_projection")) if os.path.exists(fixed("brick20_projection")) else None
    LBL = {"ssp126": "SSP1-2.6", "ssp245": "SSP2-4.5", "ssp585": "SSP5-8.5"}
    for key, label, *_ in COMPONENTS:
        for ssp in SSPS:
            for H in HORIZONS:
                cm, cmean, csp, csp99 = joint_stats(cand_p[f"draws_{ssp}"], key, H)
                if not np.isfinite(cm):
                    continue
                rows.append(dict(block="P", component=key, scenario=ssp, horizon=H,
                                 metric="median_joint", arm=cand_tag, value=cm, unit="cm",
                                 value_sigma=np.nan, note=f"mean {cmean:.2f} cm", verdict=""))
                rows.append(dict(block="P", component=key, scenario=ssp, horizon=H,
                                 metric="spread_joint", arm=cand_tag, value=csp, unit="cm",
                                 value_sigma=np.nan, note=f"p{QLO}-p{QHI}", verdict=""))
                if champ_p and champ_tag != cand_tag:
                    hm, _, hsp, _ = joint_stats(champ_p[f"draws_{ssp}"], key, H)
                    rows.append(dict(block="P", component=key, scenario=ssp, horizon=H,
                                     metric="median_joint", arm=f"{champ_tag}*", value=hm,
                                     unit="cm", value_sigma=np.nan, note="champion", verdict=""))
                    rows.append(dict(block="P", component=key, scenario=ssp, horizon=H,
                                     metric="spread_joint", arm=f"{champ_tag}*", value=hsp,
                                     unit="cm", value_sigma=np.nan, note="champion", verdict=""))
                b20_med = np.nan
                if b20 is not None:
                    hit = b20[(b20.ssp == LBL[ssp]) & (b20.component == key) & (b20.year == H)]
                    if not hit.empty:
                        r = hit.iloc[0]
                        b20_med = float(r.med)
                        rows.append(dict(block="P", component=key, scenario=ssp, horizon=H,
                                         metric="median_fixed", arm="BRICK 2.0",
                                         value=b20_med, unit="cm", value_sigma=np.nan,
                                         note=f"spread {float(r.p95)-float(r.p05):.2f} cm "
                                              "(parameter only)", verdict=""))
                if H not in LIT_HORIZONS:
                    continue
                lit = cmp_[(cmp_.component == key) & (cmp_.scenario == ssp) &
                           (cmp_.year == H)]
                if lit.empty:
                    continue
                # SCORE ON THE MODEL-BASED COMPARATORS; REPORT THE FULL RANGE ALWAYS.
                # A structured-expert-judgement envelope is a deep-uncertainty width, not
                # one a calibrated model could reproduce, so including it in the median
                # scores us against an object we are not.
                cls = comparator_classes()
                lit_all = lit
                lit_m = lit[~lit.module.astype(str).map(lambda m: cls.get(m, "model")).eq("sej")]
                lit = lit_m if len(lit_m) else lit_all
                n_excl = len(lit_all) - len(lit)
                meds = lit.med.astype(float).values
                sps = (lit.p95.astype(float) - lit.p05.astype(float)).dropna().values
                sps_all = (lit_all.p95.astype(float) - lit_all.p05.astype(float)).dropna().values
                # ⚠ PER METRIC, not per cell. A comparator can supply a MEDIAN without a
                # BAND (Coulon's published 5-95% is pooled across its two models, so it is
                # attached to neither row), so the two comparisons can have different n and
                # a single `thin` flag silently un-caps the one that is still thin.
                thin = len(meds) < MIN_LIT_FOR_MEDIAN
                thin_sp = len(sps) < MIN_LIT_FOR_MEDIAN
                inside = float(np.min(meds)) <= cm <= float(np.max(meds))
                ratio = cm / float(np.median(meds)) if np.median(meds) != 0 else np.nan
                # On a bimodal cell the MEDIAN is a valid statistic but it sits entirely
                # inside the near mode, so it under-represents a distribution the
                # literature's unimodal median does not have to. The mean is reported
                # beside it -- not substituted for it -- so the reader sees both.
                tailr0 = csp99 / csp if csp > 0 else np.nan
                bim0 = np.isfinite(tailr0) and tailr0 > TAIL_RATIO_FLAG * TAIL_RATIO_GAUSSIAN
                rows.append(dict(
                    block="P", component=key, scenario=ssp, horizon=H,
                    metric="median_vs_lit", arm=cand_tag, value=ratio, unit="x lit median",
                    value_sigma=np.nan,
                    note=f"ours {cm:.2f} cm vs lit {np.min(meds):.2f}-{np.max(meds):.2f} "
                         f"(median {np.median(meds):.2f}), n_lit={len(meds)}" +
                         (f" [{n_excl} SEJ comparator(s) excluded from the score; full "
                          f"range {lit_all.med.min():.2f}-{lit_all.med.max():.2f}]"
                          if n_excl else "") +
                         (f" ⚠ n_lit={len(meds)} < {MIN_LIT_FOR_MEDIAN}: a median of so few "
                          "is not a summary" +
                          ("; verdict CAPPED at WARN" if not inside else "") if thin else "") +
                         (f"; ⚠ BIMODAL cell -- our MEAN is {cmean:.2f} cm = "
                          f"{cmean/np.median(meds):.2f}x the literature median, and the "
                          "median sits entirely inside the near mode" if bim0 else ""),
                    verdict=("PASS" if inside else
                             ("WARN" if (thin or 1/PROJ_WARN_RATIO <= ratio <= PROJ_WARN_RATIO)
                              else "FAIL"))))
                # ⚠ SCORE BRICK 2.0's MEDIAN AGAINST THE SAME LITERATURE. Until 2026-08-25
                # [P] and [S] carried BRICK 2.0 as an unscored `median_fixed` row, so
                # "is Ladrillo measurably better than BRICK 2.0?" -- the standing stopping
                # question -- could only be answered for [H] and [R]. MEDIANS are
                # comparable across the two arms (a joint band moves a median <=5.4%,
                # `climate_uncertainty_widens`); SPREADS ARE NOT, because ours is the JOINT
                # band and BRICK 2.0's is parameter-only, and scoring one against the other
                # is the `like_for_like_forcing` error. So the median is scored head to
                # head and the spread deliberately is NOT.
                if np.isfinite(b20_med):
                    b_ratio = b20_med / float(np.median(meds))
                    b_inside = float(np.min(meds)) <= b20_med <= float(np.max(meds))
                    better = abs(ratio - 1.0) < abs(b_ratio - 1.0)
                    rows.append(dict(
                        block="P", component=key, scenario=ssp, horizon=H,
                        metric="median_vs_lit", arm="BRICK 2.0", value=b_ratio,
                        unit="x lit median", value_sigma=np.nan,
                        note=f"BRICK 2.0 {b20_med:.2f} cm vs the same lit median "
                             f"{np.median(meds):.2f}; ⚠ FIXED-driver median, scored on "
                             f"medians only -- its parameter-only SPREAD is not comparable "
                             f"with our joint band",
                        verdict=("PASS" if b_inside else
                                 ("WARN" if (thin or 1/PROJ_WARN_RATIO <= b_ratio <=
                                             PROJ_WARN_RATIO) else "FAIL"))))
                    rows.append(dict(
                        block="P", component=key, scenario=ssp, horizon=H,
                        metric="median_vs_lit_delta", arm=f"{cand_tag} vs BRICK 2.0",
                        value=abs(ratio - 1.0) - abs(b_ratio - 1.0), unit="|ratio-1| diff",
                        value_sigma=np.nan,
                        note=f"{cand_tag} {ratio:.3f}x vs BRICK 2.0 {b_ratio:.3f}x of the "
                             f"lit median; closer to 1 is better" +
                             (f"; ⚠ BRICK 2.0 is closer here but {_b20_obs_fail(rows, key)} "
                              "-- a compensating error, not skill"
                              if _h2h_verdict(ratio, b_ratio, rows,
                                              key).endswith("(unearned)") else ""),
                        verdict=_h2h_verdict(ratio, b_ratio, rows, key)))
                if len(sps):
                    sr = csp / float(np.median(sps))
                    sr_all = csp / float(np.median(sps_all)) if len(sps_all) else np.nan
                    prior = (key, ssp) in PRIOR_WIDTH_CELLS
                    tailr = csp99 / csp if csp > 0 else np.nan
                    bimodal = (np.isfinite(tailr) and
                               tailr > TAIL_RATIO_FLAG * TAIL_RATIO_GAUSSIAN)
                    # EXACT COMPARATOR-AGREEMENT TEST: score against each comparator on
                    # its own, and record whether the median's verdict has a majority.
                    majority, per_v = spread_majority(csp, sps, sr)
                    if key in ZERO_SPREAD_BY_CONSTRUCTION:
                        v = "N/A(by construction)"
                    elif bimodal:
                        v = "N/A(bimodal)"
                    elif thin_sp:
                        v = ("PASS" if SPREAD_PASS[0] <= sr <= SPREAD_PASS[1] else "WARN")
                    else:
                        v = ("PASS" if SPREAD_PASS[0] <= sr <= SPREAD_PASS[1] else
                             ("PASS(prior)" if prior and sr > SPREAD_PASS[1] else "FAIL"))
                        if SPREAD_MAJORITY_REQUIRED and not majority:
                            v = "WARN"
                    # SELF-AUDIT: what the classification is worth, per cell. Excluding an
                    # SEJ envelope always makes us look better on width, so the size of that
                    # effect is recorded on every row rather than left implicit.
                    if n_excl:
                        rows.append(dict(
                            block="P", component=key, scenario=ssp, horizon=H,
                            metric="spread_vs_lit_ALL", arm=cand_tag, value=sr_all,
                            unit="x lit spread", value_sigma=np.nan,
                            note=f"the same cell scored against ALL {len(sps_all)} comparators "
                                 f"including the SEJ envelope; the score reported above is "
                                 f"{sr:.3f} => the classification is worth {sr/sr_all:.2f}x here",
                            verdict=""))
                    rows.append(dict(
                        block="P", component=key, scenario=ssp, horizon=H,
                        metric="spread_vs_lit", arm=cand_tag, value=sr, unit="x lit spread",
                        value_sigma=np.nan,
                        note=f"ours {csp:.2f} cm vs model-based lit {np.min(sps):.2f}-"
                             f"{np.max(sps):.2f} (median {np.median(sps):.2f}, n={len(sps)})" +
                             (f"; ALL comparators {np.min(sps_all):.2f}-{np.max(sps_all):.2f}"
                              if n_excl else "") +
                             ((f"; ⚠ THE COMPARATORS DO NOT AGREE -- scored one at a time "
                               f"they give {'/'.join(f'{n}x{w}' for w, n in sorted(collections.Counter(per_v).items()))} "
                               f"and the median's '{spread_side(sr)}' is not a majority, so the "
                               "median is not a summary here; verdict CAPPED at WARN")
                              if (SPREAD_MAJORITY_REQUIRED and not majority
                                  and not thin_sp and not bimodal
                                  and key not in ZERO_SPREAD_BY_CONSTRUCTION) else "") +
                             (f"; ⚠ n={len(sps)} < {MIN_LIT_FOR_MEDIAN} comparators WITH A "
                              "BAND, so this median is not a summary" +
                              ("; verdict CAPPED at WARN"
                               if not SPREAD_PASS[0] <= sr <= SPREAD_PASS[1] else "")
                              if thin_sp else "") +
                             ("; width here is the antarctic_lambda PRIOR -- do NOT narrow"
                              if prior else "") +
                             ("; LWS is a seeded constant -- zero spread is the DESIGN,"
                              " not a defect" if key in ZERO_SPREAD_BY_CONSTRUCTION else "") +
                             (f"; ⚠ p05-p{QTAIL}/p05-p{QHI} = {tailr:.2f} vs Gaussian "
                              f"{TAIL_RATIO_GAUSSIAN} => BIMODAL, and p{QHI} is blind to the "
                              f"far mode (p05-p{QTAIL} = {csp99:.2f} cm). The p{QLO}-p{QHI} "
                              "ratio is a property of the QUANTILE here, not of the model"
                              if bimodal else ""),
                        verdict=v))


# ------------------------------------------------------------------ block [S]
def block_separation(rows, cand_tag, champ_tag, cand_p, champ_p):
    """ssp585/ssp126 median ratio against the FULL literature range.

    Marcus 2026-08-25: ours lying BETWEEN FACTS and MAGICC is acceptable -- so the
    verdict is BRACKET MEMBERSHIP, not distance from a literature median. Where the
    bracket does not exist (MAGICC-SLR carries only 2100), the report says so rather
    than silently scoring against the FACTS side alone.

    ⚠ THE VERDICT IS DIRECTIONAL (Marcus 2026-08-31, ruling on the glaciers/2150 cell that
    the shared-machinery move flipped): *"I'm okay with L21 having a wider future range
    than FACTS: that's not a failure the way that not matching observations or having a
    non-physical trend would be."* Separating the scenarios MORE than every comparator is
    a difference between models on an unobservable future, not a defect -- it is reported
    as `CHECK(wide)` and does NOT fail the [V] roll-up. Separating them LESS is the
    under-response direction and keeps its FAIL: a model that answers a forcing change by
    less than every comparator is making a claim the comparators contradict in the
    direction that matters.

    ⚠ AND THE BRACKET'S OWN WIDTH IS REPORTED WITH THE EXCEEDANCE, because it can be
    thinner than the miss: the cell that prompted this ruling was 0.14 outside a
    two-point bracket spanning 0.14, i.e. 105% of its own range.
    """
    cmp_, _src = literature_rows(cand_p["comparison"])
    for key, label, *_ in COMPONENTS:
        for H in HORIZONS:
            lo, _, _, _ = joint_stats(cand_p[f"draws_{SEP_LO}"], key, H)
            hi, _, _, _ = joint_stats(cand_p[f"draws_{SEP_HI}"], key, H)
            if not (np.isfinite(lo) and np.isfinite(hi)) or lo <= 0:
                continue
            ours = hi / lo
            lit = {}
            for src in ("FACTS", "MAGICC-SLR"):
                rs = []
                s = cmp_[(cmp_.component == key) & (cmp_.year == H) & (cmp_.source == src)]
                for mod in sorted(set(s[s.scenario == SEP_LO].module) &
                                  set(s[s.scenario == SEP_HI].module)):
                    a = float(s[(s.module == mod) & (s.scenario == SEP_HI)].med.iloc[0])
                    b_ = float(s[(s.module == mod) & (s.scenario == SEP_LO)].med.iloc[0])
                    if b_ > 0:
                        rs.append(a / b_)
                if rs:
                    lit[src] = (min(rs), max(rs), len(rs))
            if not lit:
                continue
            allr = [x for v in lit.values() for x in v[:2]]
            inside = min(allr) <= ours <= max(allr)
            bracketed = len(lit) > 1
            tol = SEP_EDGE_TOL_FRAC * (max(allr) - min(allr)) if len(allr) > 1 else 0.0
            near = (not inside) and (min(allr) - tol <= ours <= max(allr) + tol)
            margin = (0.0 if inside else
                      min(abs(ours - min(allr)), abs(ours - max(allr))))
            rows.append(dict(
                block="S", component=key, scenario=f"{SEP_HI}/{SEP_LO}", horizon=H,
                metric="separation", arm=cand_tag, value=ours, unit="x",
                value_sigma=np.nan,
                note="; ".join(f"{k} {v[0]:.2f}-{v[1]:.2f} (n={v[2]})" for k, v in lit.items())
                     + (f"; {margin:.2f} outside the bracket = "
                        f"{margin/(max(allr)-min(allr)):.0%} of its own range"
                        if margin > 0 and max(allr) > min(allr) else "")
                     + ("" if bracketed else "  [NO UPPER COMPARATOR AT THIS HORIZON]"),
                verdict=("PASS" if inside else
                         ("PASS(edge)" if near else
                          ("WARN" if not bracketed else
                           ("CHECK(wide)" if ours > max(allr) else "FAIL"))))))
            if champ_p and champ_tag != cand_tag:
                clo, _, _, _ = joint_stats(champ_p[f"draws_{SEP_LO}"], key, H)
                chi, _, _, _ = joint_stats(champ_p[f"draws_{SEP_HI}"], key, H)
                if np.isfinite(clo) and clo > 0:
                    rows.append(dict(block="S", component=key,
                                     scenario=f"{SEP_HI}/{SEP_LO}", horizon=H,
                                     metric="separation", arm=f"{champ_tag}*",
                                     value=chi / clo, unit="x", value_sigma=np.nan,
                                     note="champion", verdict=""))


# ------------------------------------------------------------------ block [V]
def block_verdicts(rows, cand_tag, champ_tag):
    """Per-module roll-up: the worst verdict in each block, and the delta vs champion."""
    df = pd.DataFrame(rows)
    ## CHECK(wide) ranks WITH the passes, not above them: a wider-than-every-comparator
    ## scenario separation is surfaced, never suppressed, but it does not fail a block
    ## (Marcus 2026-08-31; see block_separation's docstring for the reasoning).
    order = {"PASS": 0, "PASS(prior)": 0, "PASS(edge)": 0, "UNRESOLVED": 0,
             "CHECK(wide)": 0,
             "N/A(by construction)": -1, "N/A(bimodal)": -1,
             "WARN": 1, "FAIL": 2, "": -1,
             "BETTER": -1, "SAME": -1, "WORSE": -1, "n/a": -1}
    out = []
    for key, label, *_ in COMPONENTS:
        for blk, name in (("H", "hindcast"), ("R", "rate/accel"),
                          ("P", "projection"), ("S", "separation")):
            s = df[(df.block == blk) & (df.component == key) &
                   (df.arm.isin([cand_tag, "observations"])) & (df.verdict != "")]
            s = s[s.verdict.map(lambda v: order.get(v, -1)) >= 0]
            if s.empty:
                continue
            worst = s.loc[s.verdict.map(lambda v: order.get(v, -1)).idxmax()]
            out.append(dict(block="V", component=key, scenario="", horizon="",
                            metric=name, arm=cand_tag, value=np.nan, unit="",
                            value_sigma=np.nan,
                            note=f"worst cell: {worst.metric} "
                                 f"{worst.scenario}{'@' if worst.horizon else ''}"
                                 f"{worst.horizon} = {worst.value:.3g} {worst.unit}",
                            verdict=worst.verdict))
        if champ_tag != cand_tag:
            d = df[(df.block == "H") & (df.component == key) &
                   (df.metric.str.startswith("rmse_ratio")) &
                   (df.arm == f"{cand_tag} vs {champ_tag}*")]
            if not d.empty:
                better = (d.verdict == "BETTER").sum()
                worse = (d.verdict == "WORSE").sum()
                out.append(dict(block="V", component=key, scenario="", horizon="",
                                metric="vs champion (hindcast)", arm=cand_tag,
                                value=float(d.value.mean()), unit="mean RMSE ratio",
                                value_sigma=np.nan,
                                note=f"{better} windows BETTER, {worse} WORSE, "
                                     f"{len(d)-better-worse} SAME",
                                verdict=("BETTER" if better > worse else
                                         ("WORSE" if worse > better else "SAME"))))
    # ⚠ IS A BETTER TOTAL EARNED BY BETTER COMPONENTS, OR BY CANCELLATION? A total-level
    # WORSE is uninterpretable without this. Step 4 already established that the total is
    # NOT the conjunction of its components (covariance residual +18% to +34%), and the
    # same arithmetic lets an arm with LARGER component errors land a CLOSER total when
    # those errors happen to have opposite signs. Reported per cell so a total-level win
    # can never be quoted as component skill.
    for ssp in SSPS:
        for H in HORIZONS:
            def _err(arm):
                e = []
                for key, *_ in COMPONENTS:
                    if key == "total":
                        continue
                    r = df[(df.block == "P") & (df.metric == "median_vs_lit") &
                           (df.arm == arm) & (df.component == key) &
                           (df.scenario == ssp) & (df.horizon == H)]
                    if not r.empty and np.isfinite(float(r.value.iloc[0])):
                        e.append(abs(float(r.value.iloc[0]) - 1.0))
                return (float(np.sum(e)), len(e)) if e else (np.nan, 0)

            def _tot(arm):
                r = df[(df.block == "P") & (df.metric == "median_vs_lit") &
                       (df.arm == arm) & (df.component == "total") &
                       (df.scenario == ssp) & (df.horizon == H)]
                return np.nan if r.empty else abs(float(r.value.iloc[0]) - 1.0)
            cl, n = _err(cand_tag)
            cb, _ = _err("BRICK 2.0")
            tl, tb = _tot(cand_tag), _tot("BRICK 2.0")
            if not (np.isfinite(cl) and np.isfinite(cb) and np.isfinite(tl) and np.isfinite(tb)):
                continue
            cancel = cl < cb and tl > tb
            rows.append(dict(
                block="V", component="total", scenario=ssp, horizon=H,
                metric="component-error sum vs total error", arm=f"{cand_tag} vs BRICK 2.0",
                value=cl - cb, unit="sum |ratio-1| diff", value_sigma=np.nan,
                note=f"sum over {n} components of |ratio-1|: {cand_tag} {cl:.3f} vs "
                     f"BRICK 2.0 {cb:.3f}; TOTAL error {tl:.3f} vs {tb:.3f}" +
                     ("; ⚠ BRICK 2.0's total is closer DESPITE larger component errors "
                      "-- CANCELLATION, not skill" if cancel else ""),
                verdict="CANCELLATION" if cancel else ("BETTER" if cl < cb else "WORSE")))

    rows.extend(out)


# ------------------------------------------------------------------- reporting
def write_report(path, df, cand_tag, champ_tag, sigma, meta):
    L = []
    w = L.append
    w(f"# Ladrillo benchmark — `{cand_tag}`\n")
    w(f"*benchmark v{BENCH_VERSION}, {meta['date']}, repo `{meta['git']}`. "
      f"Champion arm: **{champ_tag}**" +
      (" (the candidate IS the champion — no delta column)" if champ_tag == cand_tag else "") +
      ".*\n")
    w("Arms: **candidate** (live `outputs/`), **champion\\*** (frozen), "
      "**BRICK 2.0** (stock MimiBRICK v2.0.0, own posterior), **literature** "
      "(FACTS + MAGICC-SLR, frozen).\n")
    w("## Caveats that travel with every verdict\n")
    for c in CAVEATS:
        w(f"* {c}")
    w("")
    w("## [V] Roll-up\n")
    v = df[df.block == "V"]
    w("| module | hindcast | rate/accel | projection | separation | vs champion |")
    w("|---|---|---|---|---|---|")
    for key, label, *_ in COMPONENTS:
        s = v[v.component == key]
        if s.empty:
            continue
        g = lambda m: (s[s.metric == m].verdict.iloc[0] if not s[s.metric == m].empty else "—")
        w(f"| **{label}** | {g('hindcast')} | {g('rate/accel')} | {g('projection')} | "
          f"{g('separation')} | {g('vs champion (hindcast)')} |")
    w("")
    w(f"## [H] Hindcast — the full observational period, scaled to each component's own "
      f"target 1-sigma\n")
    w("| module | target 1σ (cm) | window | arm | RMSE (cm) | RMSE (σ) | note |")
    w("|---|---|---|---|---|---|---|")
    h = df[(df.block == "H") & (df.metric.str.startswith("hindcast"))]
    for key, label, *_ in COMPONENTS:
        for _, r in h[h.component == key].iterrows():
            w(f"| {label} | {sigma.get(key, float('nan')):.4f} | "
              f"{r.metric.split('/')[1]} | {r.arm} | {r.value:.4f} | "
              f"{r.value_sigma:.2f} | {r.note} |")
    w("")
    w(f"## [R] Rate ({RATE_WINDOW[0]}-{RATE_WINDOW[1]}) and acceleration "
      f"({ACCEL_WINDOW[0]}-{ACCEL_WINDOW[1]}), with an error bar on the observations\n")
    w("| module | statistic | arm | value | unit | z vs obs bar | note |")
    w("|---|---|---|---|---|---|---|")
    for _, r in df[df.block == "R"].iterrows():
        z = "—" if not np.isfinite(r.value_sigma) else f"{r.value_sigma:+.2f}"
        w(f"| {COMP_LABEL.get(r.component, r.component)} | {r.metric.split('/')[0]} | "
          f"{r.arm} | {r.value:.5g} | {r.unit} | {z} | {r.note} |")
    w("")
    w("## [P] Projections vs the literature — scored on the JOINT band\n")
    w("| module | ssp | horizon | metric | value | verdict | note |")
    w("|---|---|---|---|---|---|---|")
    p = df[(df.block == "P") & (df.metric.str.endswith("_vs_lit"))]
    for _, r in p.iterrows():
        w(f"| {COMP_LABEL.get(r.component, r.component)} | {r.scenario} | {r.horizon} | "
          f"{r.metric} | {r.value:.3f} {r.unit} | **{r.verdict}** | {r.note} |")
    w("")
    w("## [P] Levels — every arm side by side (cm)\n")
    w("| module | ssp | horizon | candidate (joint) | champion (joint) | BRICK 2.0 (fixed) |")
    w("|---|---|---|---|---|---|")
    lv = df[(df.block == "P") & (df.metric.isin(["median_joint", "median_fixed"]))]
    for key, label, *_ in COMPONENTS:
        for ssp in SSPS:
            for H in HORIZONS:
                s = lv[(lv.component == key) & (lv.scenario == ssp) & (lv.horizon == H)]
                if s.empty:
                    continue
                g = lambda a: (f"{s[s.arm == a].value.iloc[0]:.2f}"
                               if not s[s.arm == a].empty else "—")
                w(f"| {label} | {ssp} | {H} | {g(cand_tag)} | "
                  f"{g(champ_tag + '*') if champ_tag != cand_tag else '(is champion)'} | "
                  f"{g('BRICK 2.0')} |")
    w("")
    w(f"## [S] Scenario separation — {SEP_HI}/{SEP_LO} median ratio\n")
    w("| module | horizon | ours | verdict | literature |")
    w("|---|---|---|---|---|")
    for _, r in df[(df.block == "S") & (df.arm == cand_tag)].iterrows():
        w(f"| {COMP_LABEL.get(r.component, r.component)} | {r.horizon} | {r.value:.2f}x | "
          f"**{r.verdict}** | {r.note} |")
    w("")
    w("---\n")
    w(f"*Machine-readable: `outputs/bench_ladrillo_{cand_tag}.csv`. "
      f"Regenerate: `python python/bench_ladrillo.py --tag={cand_tag}`.*")
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")


def main():
    args = sys.argv[1:]
    if "--selftest" in args:
        sys.exit(_selftest())
    tag = next((a[len("--tag="):] for a in args if a.startswith("--tag=")), None)
    if tag is None:
        raise SystemExit(__doc__)
    if "--freeze-fixed" in args:
        print("freezing the fixed comparator arms:")
        freeze_fixed(lit_from=live_paths(tag)["comparison"])
    if "--freeze" in args:
        print(f"freezing {tag} as a comparable arm:")
        freeze(tag)
    ch = champions()
    if "--promote" in args:
        why = next((a[len("--why="):] for a in args if a.startswith("--why=")), None)
        if not why:
            raise SystemExit("--promote requires --why='one line'. Promotion is a "
                             "judgement, not a threshold: a tag that improves one metric "
                             "and loses another is not automatically better.")
        mods = next((a[len("--modules="):].split(",") for a in args
                     if a.startswith("--modules=")), [k for k, *_ in COMPONENTS])
        if not os.path.exists(os.path.join(REF, tag, "manifest.json")):
            raise SystemExit(f"cannot promote {tag}: no frozen snapshot. Run --freeze first.")
        import datetime
        for m in mods:
            ch["champions"][m] = {"tag": tag,
                                  "since": datetime.date.today().isoformat(), "why": why}
            print(f"  promoted {m} -> {tag}")
        with open(CHAMPIONS_JSON, "w") as f:
            json.dump(ch, f, indent=2)

    champ_tags = {v["tag"] for v in ch["champions"].values()}
    champ_tag = sorted(champ_tags)[0] if len(champ_tags) == 1 else \
        next((a[len("--champion="):] for a in args if a.startswith("--champion=")),
             sorted(champ_tags)[0])
    if len(champ_tags) > 1:
        print(f"! champions.json names {sorted(champ_tags)}; scoring against {champ_tag}. "
              "Pass --champion= to pick another.")

    cand_p = live_paths(tag)
    missing = [k for k, v in cand_p.items() if not os.path.exists(v)]
    if missing:
        raise SystemExit(f"{tag} is missing benchmark inputs: {missing}\n" +
                         "\n".join(f"  {k}: {os.path.relpath(cand_p[k], REPO)}"
                                   for k in missing))
    champ_p = frozen_paths(champ_tag) if champ_tag != tag and \
        os.path.exists(os.path.join(REF, champ_tag, "manifest.json")) else None
    if champ_tag != tag and champ_p is None:
        print(f"! champion {champ_tag} has no frozen snapshot; scoring without a delta column")

    tg = pd.read_csv(fixed("targets"))
    sigma = {}
    for key, label, lst, bst, tcol in COMPONENTS:
        lo, hi = f"{tcol}_lo", f"{tcol}_hi"
        sigma[key] = float(((tg[hi] - tg[lo]) / (2 * 1.645)).mean()) if lo in tg else np.nan

    rows = []
    block_hindcast(rows, tag, champ_tag, cand_p, champ_p, sigma)
    block_rate_accel(rows, tag, champ_tag, cand_p, champ_p, sigma)
    block_projection(rows, tag, champ_tag, cand_p, champ_p)
    block_separation(rows, tag, champ_tag, cand_p, champ_p)
    block_verdicts(rows, tag, champ_tag)

    df = pd.DataFrame(rows)
    import datetime
    meta = {"date": datetime.date.today().isoformat(), "git": _git_head()}
    out_csv = os.path.join(REPO, "outputs", f"bench_ladrillo_{tag}.csv")
    out_md = os.path.join(REPO, "outputs", f"bench_ladrillo_{tag}.md")
    df.to_csv(out_csv, index=False)
    write_report(out_md, df, tag, champ_tag, sigma, meta)

    print("=" * 96)
    print(f"LADRILLO BENCHMARK v{BENCH_VERSION} — candidate {tag}, champion {champ_tag}")
    print("=" * 96)
    v = df[df.block == "V"]
    print(f"  {'module':13s} {'hindcast':12s} {'rate/accel':12s} {'projection':12s} "
          f"{'separation':12s} {'vs champion':12s}")
    for key, label, *_ in COMPONENTS:
        s = v[v.component == key]
        if s.empty:
            continue
        g = lambda m: (s[s.metric == m].verdict.iloc[0] if not s[s.metric == m].empty else "-")
        print(f"  {label:13s} {g('hindcast'):12s} {g('rate/accel'):12s} "
              f"{g('projection'):12s} {g('separation'):12s} "
              f"{g('vs champion (hindcast)'):12s}")
    # THE CANDIDATE'S failures and the COMPARATORS' are printed apart on purpose: a
    # BRICK 2.0 FAIL is the benchmark working (it is the arm being ranked against),
    # and mixing the two lists reads as 37 problems with the candidate.
    bad = df[df.verdict.isin(["FAIL", "WORSE"])]
    mine = bad[bad.arm.astype(str).str.startswith(tag)]
    theirs = bad[~bad.arm.astype(str).str.startswith(tag)]
    print(f"\n  {len(mine)} FAIL/WORSE cells for the CANDIDATE:")
    for _, r in mine.iterrows():
        print(f"    [{r.block}] {COMP_LABEL.get(r.component, r.component):12s} "
              f"{str(r.scenario):8s} {str(r.horizon):5s} {r.metric:26s} "
              f"{r.arm:16s} {r.value:9.3f} {r.unit}")
    print(f"\n  {len(theirs)} FAIL cells for the COMPARATOR arms "
          f"(this is the benchmark working, not a defect of {tag}):")
    for _, r in theirs.iterrows():
        print(f"    [{r.block}] {COMP_LABEL.get(r.component, r.component):12s} "
              f"{str(r.scenario):8s} {str(r.horizon):5s} {r.metric:26s} "
              f"{r.arm:16s} {r.value:9.3f} {r.unit}")
    ## CHECK cells are NOT failures and must NOT be silent either -- a three-valued verdict
    ## that only prints on FAIL is a verdict that hides its middle value
    ## (`gate_bound_matches_its_claim`). They are listed separately, with the ruling named.
    chk = df[df.verdict.astype(str).str.startswith("CHECK")]
    chk = chk[chk.arm.astype(str).str.startswith(tag)]
    if len(chk):
        print(f"\n  {len(chk)} CHECK cells for the CANDIDATE (surfaced, not failing -- "
              f"Marcus 2026-08-31: separating the scenarios MORE than every comparator is a "
              f"model difference on an unobservable future, not a defect):")
        for _, r in chk.iterrows():
            print(f"    [{r.block}] {COMP_LABEL.get(r.component, r.component):12s} "
                  f"{str(r.scenario):8s} {str(r.horizon):5s} {r.metric:26s} "
                  f"{r.arm:16s} {r.value:9.3f} {r.unit}  {r.verdict}")
            print(f"        {r.note}")
    a = df[(df.metric == "spread_vs_lit")].set_index(["component", "scenario", "horizon"])
    b = df[(df.metric == "spread_vs_lit_ALL")].set_index(["component", "scenario", "horizon"])
    if len(b):
        j = a.join(b, rsuffix="_all", how="inner").dropna(subset=["value_all"])
        worst = (j.value / j.value_all).max()
        print(f"\n  ⚠ COMPARATOR CLASSIFICATION AUDIT: {len(j)} spread cells are scored with "
              f"the SEJ\n    envelope excluded (benchmark/comparator_classes.csv). It improves "
              f"the score by up\n    to {worst:.2f}x. Cells whose VERDICT depends on it:")
        chg = 0
        for idx, r in j.iterrows():
            v_all = ("PASS" if SPREAD_PASS[0] <= r.value_all <= SPREAD_PASS[1] else "FAIL")
            if str(r.verdict).startswith("PASS") and v_all == "FAIL":
                chg += 1
                print(f"      {COMP_LABEL.get(idx[0], idx[0]):12s} {idx[1]:8s} {idx[2]:5.0f}  "
                      f"{r.value:.3f} ({r.verdict}) vs {r.value_all:.3f} (FAIL) with SEJ in")
        if chg == 0:
            print("      none -- every verdict is the same either way")
    print(f"\nwrote outputs/bench_ladrillo_{tag}.csv")
    print(f"wrote outputs/bench_ladrillo_{tag}.md")



if __name__ == "__main__":
    main()
