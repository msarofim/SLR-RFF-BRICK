#!/usr/bin/env python3
"""Sea-level rise by component at one horizon — Ladrillo vs BRICK 2.0 vs FACTS vs MAGICC-SLR.

  python3 python/plot_model_comparison_components.py [--tag=L21] [--year=2100|2150|2300|all]

Writes figures/model_comparison_components_<TAG>_<year>.png, one per horizon.

WHAT THIS ADDS. The four-source comparison has existed as a TABLE since
`ladrillo_model_comparison.py` (outputs/ladrillo_model_comparison_<TAG>.csv) but had no
figure: `plot_b2_component_comparison.py` draws a per-component panel for BRICK-AM/extA108
(Ladrillo's PREDECESSOR, see handoff 2026-08-31c §1) against FACTS and AR6, and stops at
2150. `plot_future_components.py` draws Ladrillo vs BRICK 2.0 over time with no external
comparator at all. This is the first figure carrying all FOUR sources, and the first to
carry the 2300 horizon, where FACTS does not reach and MAGICC-SLR is the ONLY comparator.

THE YEAR IS THE FIGURE, the scenario is the x axis and the component is the panel. Chosen
so every panel of one figure shares a horizon and therefore a plausible y-scale; putting
the three horizons inside a panel lets 2300 squash 2100 flat, which is the readability
failure this layout avoids. It also matches `plot_b2_component_comparison.py`, so the two
per-component comparison figures read as the same object.

⚠ ALL FOUR BANDS ARE DRAWN, AND THAT IS THE POINT OF THE FIGURE. The first version of
this script drew bars for Ladrillo and BRICK 2.0 only, inheriting `ladrillo_figs.WIDTH_SRCS`
-- a set written when both our arms ran on MEAN forcing and were therefore
posterior-parameter spread only. That has not been true since 2026-08-30: the Ladrillo and
BRICK 2.0 joint arms propagate their posteriors across the SAME 841 FaIR configs, which is
precisely why they were built (`brick20_joint_band` -- "every column of the comparison now
carries climate uncertainty, so the WIDTHS are like-for-like for the first time"). Drawing
only two of the four suppressed the comparison the joint arms exist to make. Whether a band
may be drawn is now read from each row's OWN `band_basis` via
`ladrillo_figs.band_is_comparable`, so a cell that falls back to the fixed (mean-forcing)
arm loses its bar automatically and no source-name list can go stale again.

⚠ SAME KIND OF OBJECT IS NOT THE SAME ENSEMBLE. Ours is 841 FaIR configs, MAGICC-SLR's is a
600-member AR6 drawnset, FACTS uses its own internal ensembles -- and both joint arms are
PRIOR PROPAGATIONS (the posteriors were calibrated under fixed forcing), not refits. The
widths are comparable; they are not identical constructions, and the caption says so.
⚠ Narrowness is never a win at ais/ssp585, where 78% of our width is the antarctic_lambda
paleo prior rather than an inference.

⚠ FACTS IS NOT ONE NUMBER AND IS NOT DRAWN AS ONE. It is a stack of modules per component
(ar5AIS / larmip / deconto21 / bamber19 at Antarctica, FittedISMIP / emuGrIS / bamber19 at
Greenland, and the wf* workflows at the total), and they disagree by up to 8x -- so a
median across them summarises nothing (`median_needs_agreement`). Every module is plotted
as its own marker. The STRUCTURED-EXPERT-JUDGEMENT modules are drawn with an open marker,
classified from benchmark/comparator_classes.csv (the same file the benchmark scores from,
never a hand-typed list here), because their width is a deep-uncertainty envelope rather
than a model spread.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ladrillo_figs as lf  # noqa: E402

import textwrap

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402


def _arg(flag, default):
    return next((a[len(flag):] for a in sys.argv[1:] if a.startswith(flag)), default)


TAG = _arg("--tag=", "L21")
DESC = lf.tag_desc(TAG)
HORIZONS = [2100, 2150, 2300]
_y = _arg("--year=", "all")
YEARS = HORIZONS if _y == "all" else [int(_y)]
if any(y not in HORIZONS for y in YEARS):
    raise SystemExit("--year must be one of %s or 'all', not %r" % (HORIZONS, _y))

CMP_CSV = os.path.join(lf.REPO, "outputs", "ladrillo_model_comparison_%s.csv" % TAG)
FROZEN_LIT = os.path.join(lf.REPO, "benchmark/reference/_fixed/literature_rows.csv")
CLASSES_CSV = os.path.join(lf.REPO, "benchmark/comparator_classes.csv")

## Source order = plotting order = legend order, declared once. `Ladrillo` is the row this
## figure is about and is drawn leftmost in every slot.
SOURCES = ["Ladrillo", "BRICK 2.0", "MAGICC-SLR", "FACTS"]
SRC_LABEL = {"Ladrillo": "Ladrillo %s" % TAG, "BRICK 2.0": "BRICK 2.0",
             "MAGICC-SLR": "MAGICC-SLR (Nauels 2025)", "FACTS": "FACTS n200 (per module)"}
## Slot centres within one scenario group. FACTS gets the widest slot because it fans its
## modules out inside it; the others are single markers.
SLOT = {"Ladrillo": -0.30, "BRICK 2.0": -0.12, "MAGICC-SLR": 0.06, "FACTS": 0.30}
FACTS_FAN = 0.055        # module-to-module spacing inside the FACTS slot
MARK = {"Ladrillo": "s", "BRICK 2.0": "s", "MAGICC-SLR": "D", "FACTS": "o"}
SEJ_MARK = "^"           # open triangle: structured expert judgement, not a model spread

# --- data ------------------------------------------------------------------
if not os.path.exists(CMP_CSV):
    raise SystemExit(
        "no four-source comparison table for %s at %s\n  Produce it with:\n"
        "    python3 python/ladrillo_model_comparison.py --tag=%s"
        % (TAG, os.path.relpath(CMP_CSV, lf.REPO), TAG))
D = pd.read_csv(CMP_CSV)

missing_src = [s for s in SOURCES if s not in set(D.source)]
if missing_src:
    raise SystemExit("[DATA] %s carries no rows for %s -- this figure is defined by having "
                     "all four sources on one basis, so it must not be drawn with three."
                     % (os.path.relpath(CMP_CSV, lf.REPO), missing_src))

## Ladrillo's own module string must BE the tag being captioned. The comparison writer
## stamps it (`module=LADRILLO_TAG`), so a file copied or renamed to the wrong tag is
## caught here rather than mislabelling a whole figure -- the same class of error TAG_DESC
## exists to prevent on the caption side.
_lad_mod = sorted(set(D[D.source == "Ladrillo"].module.astype(str)))
if _lad_mod != [TAG]:
    raise SystemExit("[TAG] %s carries Ladrillo module(s) %s but this figure is captioned "
                     "%s. Refusing to draw." % (os.path.relpath(CMP_CSV, lf.REPO),
                                                _lad_mod, TAG))

# --- gate: the widths this figure DRAWS must be the same object -------------
## ⚠ THE CAPTION'S COMPARABILITY CLAIM IS DERIVED FROM THE DATA, NEVER TYPED. Ladrillo's
## loader falls back to the FIXED (mean-forcing) arm for any cell where the joint arm is
## the wrong Greenland arm, and BRICK 2.0 had NO joint arm at all before 2026-08-30. If
## either width source is not wholly on a joint basis then "the bars are comparable" is
## FALSE, so the claim is dropped and the actual mix is stamped instead of asserted away.
BASES = {s: sorted(set(D[D.source == s].band_basis.astype(str))) for s in SOURCES}
## ⚠ THE CAPTION'S COMPARABILITY CLAIM IS DERIVED FROM THE DATA, NEVER TYPED. Every row is
## asked whether ITS OWN basis carries climate uncertainty; the predicate raises on a basis
## string it does not recognise rather than guessing. Ladrillo's loader falls back to the
## FIXED (mean-forcing) arm for any cell where the joint arm is the wrong Greenland arm, and
## a fixed band is a narrower object for reasons that have nothing to do with the model -- so
## such a cell must lose its bar, and the claim must weaken, without anyone remembering to.
D["band_ok"] = D.band_basis.map(lf.band_is_comparable)
PARAM_ONLY = sorted({(r.source, b) for r, b in
                     zip(D[~D.band_ok].itertuples(), D[~D.band_ok].band_basis)})
WIDTHS_COMPARABLE = bool(D.band_ok.all())
if WIDTHS_COMPARABLE:
    WIDTH_NOTE = ("Bars are 17-83% (thick) and 5-95% (thin) and are drawn for ALL FOUR "
                  "sources, because all four now carry climate uncertainty -- which is "
                  "what the joint arms were built for and what makes these widths "
                  "comparable at all.")
else:
    WIDTH_NOTE = ("Bars are 17-83%% (thick) and 5-95%% (thin). ⚠ %d cell(s) are on a "
                  "PARAMETER-ONLY basis and are drawn as medians with NO bar, because a "
                  "fixed (mean-forcing) band is narrower than a joint one for reasons "
                  "that have nothing to do with the model: %s."
                  % ((~D.band_ok).sum(),
                     "; ".join("%s = %s" % (a, b) for a, b in PARAM_ONLY)))
for s in SOURCES:
    print("[BASIS] %-11s %s" % (s, " + ".join(BASES[s])))
print("[BASIS] every row carries climate uncertainty: %s"
      % ("YES -- all four bands drawn and comparable" if WIDTHS_COMPARABLE else
         "NO -- %d parameter-only cell(s) drawn WITHOUT a bar: %s"
         % ((~D.band_ok).sum(), PARAM_ONLY)))

# --- gate: the frozen literature arm has not moved under us -----------------
## The FACTS and MAGICC rows are tag-INDEPENDENT comparators, frozen under
## benchmark/reference/_fixed/ precisely so a re-extraction cannot move a comparator
## silently under every past score. This reads the FROZEN copy, which this script never
## writes -- a gate that read its own output would compare a convention against itself.
LIT_NOTE = ""
if not os.path.exists(FROZEN_LIT):
    LIT_NOTE = ("  ⚠ the FACTS/MAGICC comparators are NOT frozen (no %s), so nothing "
                "checks that a re-extraction has not moved them."
                % os.path.relpath(FROZEN_LIT, lf.REPO))
    print("[LIT] ⚠ no frozen literature arm at %s" % os.path.relpath(FROZEN_LIT, lf.REPO))
else:
    _k = ["source", "module", "scenario", "component", "year"]
    _live = D[D.source.isin(["FACTS", "MAGICC-SLR"])]
    _j = pd.read_csv(FROZEN_LIT).merge(_live, on=_k, suffixes=("_f", "_l"),
                                       how="outer", indicator=True)
    _moved = _j[(_j._merge != "both") | ((_j.med_f - _j.med_l).abs() > 1e-6)]
    if len(_moved):
        ## REPORTED AND STAMPED, not fatal: either copy could be the newer one, and which
        ## one is right is a decision, not a default. But a figure must not assert a
        ## frozen comparator it did not verify.
        LIT_NOTE = ("  ⚠ LITERATURE ARM MOVED: %d of %d FACTS/MAGICC rows differ from the "
                    "frozen copy (%s) — the comparators drawn here are the LIVE ones."
                    % (len(_moved), len(_j), os.path.relpath(FROZEN_LIT, lf.REPO)))
        print("[LIT] ! %d of %d rows differ from the frozen comparator arm:\n%s"
              % (len(_moved), len(_j), _moved[_k + ["med_f", "med_l"]].to_string(index=False)))
    else:
        print("[LIT] %d FACTS/MAGICC rows match the frozen comparator arm exactly"
              % len(_j))

# --- FACTS module classes ---------------------------------------------------
if not os.path.exists(CLASSES_CSV):
    raise SystemExit("[CLASS] no %s -- the structured-expert-judgement modules would then "
                     "be drawn as if they were model spreads. Refusing to draw."
                     % os.path.relpath(CLASSES_CSV, lf.REPO))
_c = pd.read_csv(CLASSES_CSV, comment="#")
CLASS = dict(zip(_c.module.astype(str), _c["class"].astype(str)))
SEJ = sorted(m for m in set(D[D.source == "FACTS"].module.astype(str))
             if CLASS.get(m, "model") == "sej")
print("[CLASS] FACTS modules classified `sej` (open markers; nothing is scored here, the\n        class only changes the marker): %s" % (", ".join(SEJ) or "none"))

# --- console: what each figure can and cannot show --------------------------
print("\n[COVERAGE] sources present per component and horizon")
for y in YEARS:
    for comp in lf.COMPONENTS:
        have = sorted(set(D[(D.year == y) & (D.component == comp)].source))
        gap = [s for s in SOURCES if s not in have]
        print("  @%d  %-20s %-28s %s" % (y, lf.COMP_TITLE[comp], ", ".join(have),
                                         ("MISSING: " + ", ".join(gap)) if gap else ""))


def _sum_check(y):
    """Sum-of-component-medians vs the median of `total`, per source and scenario.

    ⚠ REPORTED, NEVER GATED. The sum of per-component medians is not the median of the
    sum unless the components are comonotonic, so asserting equality would be asserting
    something false. A LARGE gap is real information about component dependence -- an
    exact zero would be the suspicious result."""
    parts = [c for c in lf.COMPONENTS if c != "total"]
    rows = []
    for src in SOURCES:
        for k, lab, _c2, _d in lf.scen_set("ssp"):
            s = D[(D.source == src) & (D.scenario == k) & (D.year == y)]
            if src == "FACTS":
                continue          # FACTS has no single module per component to sum
            got = {c: s[s.component == c].med for c in parts + ["total"]}
            if any(len(v) != 1 for v in got.values()):
                continue
            ssum = sum(float(got[c].iloc[0]) for c in parts)
            rows.append((src, lab, ssum, float(got["total"].iloc[0])))
    return rows


# --- figure -----------------------------------------------------------------
SCENS = lf.scen_set("ssp")
for YEAR in YEARS:
    OUT = os.path.join(lf.REPO, "figures",
                       "model_comparison_components_%s_%d.png" % (TAG, YEAR))
    absent = sorted({s for s in SOURCES
                     if D[(D.source == s) & (D.year == YEAR)].empty})
    partial = sorted({s for s in SOURCES if s not in absent and
                      set(D[(D.source == s) & (D.year == YEAR)].component)
                      != set(lf.COMPONENTS)})
    fig, axes = plt.subplots(2, 3, figsize=(14.5, 8.4))
    for ax, comp in zip(axes.ravel(), lf.COMPONENTS):
        for i, (k, lab, _col, _d) in enumerate(SCENS):
            cell = D[(D.scenario == k) & (D.component == comp) & (D.year == YEAR)]
            for src in SOURCES:
                s = cell[cell.source == src]
                if s.empty:
                    continue
                col = lf.SRC_COLOR[src]
                if src == "FACTS":
                    ## FACTS: one series per MODULE, fanned inside its slot, so the
                    ## DISAGREEMENT between modules is the thing the reader sees. A median
                    ## across them would summarise nothing (`median_needs_agreement`).
                    rows = [s[s.module == m].iloc[0] for m in sorted(s.module.astype(str))]
                    x0 = i + SLOT[src] - FACTS_FAN * (len(rows) - 1) / 2
                    xs = [x0 + j * FACTS_FAN for j in range(len(rows))]
                else:
                    rows, xs = [s.iloc[0]], [i + SLOT[src]]
                for r, x in zip(rows, xs):
                    is_sej = CLASS.get(str(r.module), "model") == "sej"
                    mk = SEJ_MARK if is_sej else MARK[src]
                    ms = (5.0 if src == "FACTS" else 6.5)
                    if r.band_ok:
                        ax.plot([x, x], [r.p05, r.p95], color=col,
                                lw=0.8 if src == "FACTS" else 1.0, alpha=0.7,
                                solid_capstyle="butt", zorder=2)
                        ax.errorbar(x, r.med, yerr=[[r.med - r.p17], [r.p83 - r.med]],
                                    fmt=mk, color=col, ms=ms,
                                    capsize=2.0 if src == "FACTS" else 3.5,
                                    lw=1.4 if src == "FACTS" else 2.2,
                                    mfc="none" if is_sej else col, mec=col,
                                    mew=1.4 if is_sej else 0.8, zorder=3)
                    else:
                        ## No bar: a parameter-only width next to three climate-inclusive
                        ## ones would read as a narrow model rather than a narrow arm.
                        ax.plot(x, r.med, mk, ms=ms, color=col,
                                mfc="none" if is_sej else col, mec=col,
                                mew=1.4 if is_sej else 0.8, zorder=3)
        ## Sources absent from THIS panel are named in the panel, not left as a silent
        ## gap -- but a source absent from the WHOLE figure is already stamped on the
        ## caption and dropped from the legend, and repeating it in all six panels is
        ## noise. So the panel note carries only the PARTIAL absences.
        gone = [s for s in SOURCES
                if s not in absent
                and D[(D.source == s) & (D.component == comp) & (D.year == YEAR)].empty]
        if gone:
            ax.text(0.985, 0.03, "no " + ", ".join(gone) + " at %d" % YEAR,
                    transform=ax.transAxes, ha="right", va="bottom",
                    fontsize=7.2, color="0.35", style="italic")
        ## ⚠ THE Y-AXIS IS SET BY THE SAMPLED SERIES, AND THE ELICITED ONE IS CLIPPED
        ## AND NAMED. bamber19's 5-95% at gis/ssp585/2100 spans 93.2 cm against 17.1 cm
        ## for the next-widest module: letting it drive the axis costs ~5x of the
        ## resolution every other comparison in the panel needs. It is NOT dropped and
        ## NOT quietly cut off -- the limits come from the sampling quantiles, and any
        ## elicited whisker that runs past them is annotated WITH ITS VALUE, so the
        ## reader is told exactly what is off the panel. (A structured expert judgement
        ## is a deep-uncertainty envelope, not a sampled quantile: the two are already
        ## different objects, which is why comparator_classes.csv exists at all.)
        pan = D[(D.component == comp) & (D.year == YEAR)]
        pan_sej = pan.module.astype(str).map(lambda m: CLASS.get(m, "model") == "sej")
        lo = pd.concat([pan[~pan_sej].p05, pan.med]).min()
        hi = pd.concat([pan[~pan_sej].p95, pan.med]).max()
        pad = 0.08 * max(hi - lo, 1e-6)
        ax.set_ylim(min(lo - pad, 0 if lo >= 0 else lo - pad), hi + pad)
        clipped = ["%s %s %.0f–%.0f" % (r.scenario.replace("ssp", "SSP"), r.module,
                                        r.p05, r.p95)
                   for r in pan[pan_sej].itertuples() if r.band_ok and r.p95 > hi + pad]
        if clipped:
            ax.text(0.015, 0.975,
                    "elicited 5–95% off panel (cm):\n  " + "\n  ".join(clipped),
                    transform=ax.transAxes, ha="left", va="top", fontsize=6.3,
                    linespacing=1.35, color=lf.SRC_COLOR["FACTS"])
        ## The one panel where two of the four arms are not independent gets told so.
        if comp == "glaciers":
            ax.text(0.985, 0.03, "Ladrillo transient = Nauels 2017 Eq. 3 = MAGICC's law",
                    transform=ax.transAxes, ha="right", va="bottom", fontsize=6.6,
                    style="italic", color="0.35")
        ax.axhline(0, color="0.85", lw=0.8, zorder=1)
        ax.set_xticks(range(len(SCENS)))
        ax.set_xticklabels([l for _k, l, _c2, _d in SCENS], fontsize=9)
        ax.set_xlim(-0.6, len(SCENS) - 0.4)
        ax.set_title(lf.COMP_TITLE[comp], fontsize=10, fontweight="bold", loc="left")
        ax.set_ylabel("cm SLE (rel. 1995–2014)", fontsize=8)
        ax.tick_params(labelsize=8)
        ax.grid(axis="y", alpha=0.25, lw=0.6)

    ## ⚠ THE LEGEND IS BUILT FROM WHAT WAS ACTUALLY DRAWN AT THIS HORIZON. Carrying the
    ## full source list into the 2300 figure advertised a FACTS series that has no marker
    ## anywhere on it -- a legend entry with nothing behind it reads as a series the
    ## reader failed to find, which is exactly backwards.
    drawn = [s for s in SOURCES if s not in absent]
    sej_drawn = sorted(set(D[(D.source == "FACTS") & (D.year == YEAR)].module.astype(str))
                       & set(SEJ))
    handles = [Line2D([], [], color=lf.SRC_COLOR[s], marker=MARK[s], ls="none",
                      ms=7, label=SRC_LABEL[s]) for s in drawn]
    if sej_drawn:
        handles += [Line2D([], [], color=lf.SRC_COLOR["FACTS"], marker=SEJ_MARK, ls="none",
                           mfc="none", mew=1.4, ms=7,
                           label="FACTS, structured expert judgement (%s)"
                                 % ", ".join(sej_drawn))]
    handles += [Line2D([], [], color="0.3", lw=2.2,
                       label="17–83% (thick) / 5–95% (thin), all sources"
                             if WIDTHS_COMPARABLE else
                             "17–83% / 5–95% — absent where the arm is parameter-only")]
    fig.legend(handles=handles, ncol=3, fontsize=8.5, frameon=False,
               loc="upper center", bbox_to_anchor=(0.5, 0.972))
    fig.suptitle("Sea-level rise by component at %d — %s vs BRICK 2.0 vs FACTS vs "
                 "MAGICC-SLR   [%s]" % (YEAR, DESC["model"], lf.commit_stamp()),
                 fontsize=12.5, fontweight="bold", y=0.999)
    fig.tight_layout(rect=[0, 0.115, 1, 0.925])

    ## ⚠ WRAP THE CAPTION BEFORE SAVING. An unwrapped fig.text is one long line and
    ## bbox_inches="tight" then stretches the canvas to fit it, squashing the panels.
    cap = (
        "%s — %s; %s; %s.  %s.  %s  %s  FACTS n200 is rel. baseyear 2005, treated as "
        "comparable to the 1995–2014 mean (the standing MAGICC-comparison convention); "
        "MAGICC-SLR is v7.5.3 + Nauels 2025 on a 600-member AR6 drawnset.  %s%s%s  %s"
        % (DESC["model"], DESC["calib"], DESC["glacier"], DESC["gis"],
           lf.PROJ_BASELINE.capitalize(), WIDTH_NOTE,
           lf.BAND_CAVEAT + "  " + lf.GLACIER_LINEAGE_NOTE,
           ("⚠ NOT DRAWN AT %d: %s. " % (YEAR, ", ".join(absent))) if absent else "",
           ("⚠ PARTIAL AT %d (some components only): %s. " % (YEAR, ", ".join(partial)))
           if partial else "",
           DESC["note"], LIT_NOTE.strip()))
    fig.text(0.5, 0.105, "\n".join(textwrap.wrap(cap, 178)),
             fontsize=7.2, ha="center", va="top", color="0.3")
    fig.savefig(OUT, dpi=150)
    plt.close(fig)
    print("\nwrote %s" % os.path.relpath(OUT, lf.REPO))

    print("  [SUM] sum-of-component-medians vs median-of-total @%d "
          "(medians do not add — reported, not gated)" % YEAR)
    for src, lab, ssum, tot in _sum_check(YEAR):
        print("        %-11s %-9s %8.2f vs %8.2f  (%+.2f cm)"
              % (src, lab, ssum, tot, ssum - tot))

# --- console summary: the numbers a caption would quote ---------------------
print("\nmedian cm, rel. 1995–2014.  Ladrillo %s / BRICK 2.0 / MAGICC-SLR / FACTS "
      "[min–max across modules, sej marked *]" % TAG)
for YEAR in YEARS:
    print("\n  @%d" % YEAR)
    for comp in lf.COMPONENTS:
        print("    %s" % lf.COMP_TITLE[comp])
        for k, lab, _c2, _d in SCENS:
            cell = D[(D.scenario == k) & (D.component == comp) & (D.year == YEAR)]
            def one(src):
                s = cell[cell.source == src]
                return "%8.1f" % s.med.iloc[0] if len(s) else "       –"
            f = cell[cell.source == "FACTS"]
            if len(f):
                star = "*" if any(CLASS.get(str(m), "model") == "sej" for m in f.module) else " "
                ftxt = "%7.1f–%-7.1f%s (n=%d)" % (f.med.min(), f.med.max(), star, len(f))
            else:
                ftxt = "            –"
            print("      %-9s %s %s %s  %s"
                  % (lab, one("Ladrillo"), one("BRICK 2.0"), one("MAGICC-SLR"), ftxt))
