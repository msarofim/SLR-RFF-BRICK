#!/usr/bin/env python3
"""
doc_l14_vs_brick20.py — figures + tables for the Ladrillo/L14 documentation.

Produces, for the write-up:
  FIG 1  hindcast, L14 vs BRICK 2.0 vs OBSERVATIONS, per component, 1900-2026
  FIG 2  projections, L14 vs BRICK 2.0 vs FACTS vs MAGICC-SLR, like-for-like
  TAB    markdown tables backing both

⚠ THE BAND CAVEAT, carried into every caption and table (it is the single most
important like-for-like qualifier and ladrillo_model_comparison.py states it too):
Ladrillo and BRICK 2.0 run on MEAN climate forcing, so their bands are POSTERIOR-
PARAMETER spread ONLY. MAGICC and FACTS bands ALSO carry climate uncertainty.
MEDIANS are comparable; BAND WIDTHS ARE NOT.

⚠ MAGICC-SLR ends at 2100. Empty 2150/2300 cells are absence of data, not zero.

All sources are re-referenced to 1995-2014 by ladrillo_model_comparison.py, whose
frozen inputs are hashed in benchmark/reference/_fixed/manifest.json.

    source ~/climate-env/bin/activate
    python python/doc_l14_vs_brick20.py [--tag=L14]
"""
import os, sys, subprocess
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG  = next((a.split("=",1)[1] for a in sys.argv[1:] if a.startswith("--tag=")), "L14")

# ---- provenance: every label and filename derives from these -------------------
FIXED     = os.path.join(REPO, "benchmark/reference/_fixed")
POSTPRED  = os.path.join(REPO, f"outputs/postpred_{TAG}_components_timeseries.csv")
OLD_HIND  = os.path.join(FIXED, "postpred_oldbrick_components_timeseries.csv")
TARGETS   = os.path.join(FIXED, "recalib_targets_ext.csv")
COMPARE   = os.path.join(REPO, f"outputs/ladrillo_model_comparison_{TAG}.csv")
FIGDIR    = os.path.join(REPO, "figures")
OUT_F1    = os.path.join(FIGDIR, f"doc_hindcast_{TAG}_vs_brick20.png")
OUT_F2    = os.path.join(FIGDIR, f"doc_projection_{TAG}_vs_lit.png")
OUT_TAB   = os.path.join(REPO, f"outputs/doc_tables_{TAG}.md")
BAND_CAVEAT = ("Ladrillo and BRICK 2.0 run on MEAN forcing -> bands are posterior-parameter "
               "spread only; MAGICC/FACTS bands also carry climate uncertainty. "
               "MEDIANS comparable, WIDTHS not.")
BASIS      = "cm, re-referenced to 1995-2014"
HIND_BASIS = "cm, model baseline as in postpred (obs on the same re-reference)"
COMMIT = subprocess.check_output(["git","-C",REPO,"rev-parse","--short","HEAD"],text=True).strip()

C_L14, C_OLD, C_OBS = "tab:red", "0.55", "k"
C_SRC = {"Ladrillo": "tab:red", "BRICK 2.0": "0.55", "FACTS": "tab:blue", "MAGICC-SLR": "tab:green"}
os.makedirs(FIGDIR, exist_ok=True)

# ================= FIG 1 — hindcast vs BRICK 2.0 vs observations =================
hp = pd.read_csv(POSTPRED)
ho = pd.read_csv(OLD_HIND)
tg = pd.read_csv(TARGETS)

# component -> (L14 prefix, BRICK 2.0 prefix, target column, target lo, target hi, label)
COMPS = [("total",    "total",    "total",    "dang", "dang_lo", "dang_hi", "Total GMSL"),
         ("ais",      "ais",      "ais",      "ais",  "ais_lo",  "ais_hi",  "Antarctica"),
         ("gis",      "gis",      "gis",      "gis",  "gis_lo",  "gis_hi",  "Greenland"),
         ("glaciers", "glaciers", "gsic",     "gsic", "gsic_lo", "gsic_hi", "Glaciers"),
         ("te",       "te",       "te",       "steric","steric_lo","steric_hi","Thermal expansion")]

# ⚠ GLACIERS ARE SCORED AGAINST A DELTA-CORRECTED TARGET, NOT THE RAW SERIES.
# posterior_predictive_ladrillo.jl:206 — "the glacier target the model is actually compared
# against is delta-corrected per draw; report its posterior median so the overlay is
# self-consistent". Plotting the RAW `gsic` column instead makes L14 look ~1.8 cm biased at
# 1900 when it is not: the raw series and the scored series are different objects.
GLAC_OBS_COL = "glaciers_obs_delta_corrected"

fig, axes = plt.subplots(1, 5, figsize=(19, 3.9), constrained_layout=True)
for ax, (key, pn, on, tc, tlo, thi, lbl) in zip(axes, COMPS):
    yr = hp["year"].values
    if f"{pn}_p50" in hp:
        ax.fill_between(yr, hp[f"{pn}_p05"], hp[f"{pn}_p95"], color=C_L14, alpha=.20, lw=0)
        ax.plot(yr, hp[f"{pn}_p50"], color=C_L14, lw=1.6, label=f"Ladrillo {TAG}", zorder=3)
    # BRICK 2.0 uses p5/p95 and 'gsic' for glaciers
    if f"{on}_p50" in ho:
        ax.fill_between(ho["year"], ho[f"{on}_p5"], ho[f"{on}_p95"], color=C_OLD, alpha=.22, lw=0)
        ax.plot(ho["year"], ho[f"{on}_p50"], color=C_OLD, lw=1.4, ls="--", label="BRICK 2.0", zorder=2)
    if key == "glaciers" and GLAC_OBS_COL in hp:
        m = hp[GLAC_OBS_COL].notna()
        ax.plot(hp.loc[m,"year"], hp.loc[m,GLAC_OBS_COL], color=C_OBS, lw=0, marker="o", ms=2.1,
                label="observations", zorder=4)
        ax.text(.03,.03,"obs = delta-corrected target\n(the series actually scored)",
                transform=ax.transAxes, fontsize=6.5, color="0.35")
    elif tc in tg:
        m = tg[tc].notna()
        ax.plot(tg.loc[m,"year"], tg.loc[m,tc], color=C_OBS, lw=0, marker="o", ms=2.1,
                label="observations", zorder=4)
        if tlo in tg and thi in tg:
            ax.fill_between(tg.loc[m,"year"], tg.loc[m,tlo], tg.loc[m,thi],
                            color=C_OBS, alpha=.16, lw=0, zorder=1)
    ax.set_title(lbl, fontsize=10)
    ax.set_xlabel("year", fontsize=8); ax.tick_params(labelsize=8)
    ax.axhline(0, color="0.8", lw=.6, zorder=0)
axes[0].set_ylabel("cm", fontsize=9)
axes[0].legend(fontsize=7.5, loc="upper left", framealpha=.9)
fig.suptitle(f"FIG 1 — Hindcast: Ladrillo {TAG} vs BRICK 2.0 vs observations, 1900-2026  "
             f"({HIND_BASIS})   [commit {COMMIT}]", fontsize=10.5)
fig.savefig(OUT_F1, dpi=150)
plt.close(fig)
print("wrote", os.path.relpath(OUT_F1, REPO))

# ================= FIG 2 — projections vs FACTS / MAGICC / BRICK 2.0 =============
cmp_ = pd.read_csv(COMPARE)
SSPS = ["ssp126","ssp245","ssp585"]
YEARS = [2100, 2150, 2300]

# ⚠ THREE COVERAGE FACTS THAT THE FIGURE MUST NOT PAPER OVER, all verified from the data:
#  1. BRICK 2.0 in this comparison is GLACIERS ONLY — it is the legacy glacier arm
#     (ladrillo_model_comparison.py header). It CANNOT appear in a total-GMSL panel.
#     Its absence there is a scope limit, not missing data.
#  2. MAGICC-SLR runs to 2300, NOT to 2100. The comparison script's docstring says
#     "Ends at 2100"; the file (data/comparison/magicc_nauels_components.csv) carries
#     2000-2300. The docstring is STALE — verified 2026-08-27.
#  3. FACTS has NO 2300. It stops at 2150.
#
# ⚠ FACTS `total` IS SEVEN AR6 WORKFLOWS, NOT ONE NUMBER (wf1e/1f/2e/2f/3e/3f/wf4), and
# `wf4` IS STRUCTURED EXPERT JUDGEMENT — benchmark/comparator_classes.csv classifies it
# `sej` because it is bamber19 in BOTH ice sheets. The house rule (bench_ladrillo.py:701)
# SCORES against model-class comparators and reports SEJ separately, because an SEJ
# envelope is a deep-uncertainty width no calibrated model could reproduce. Taking
# `.iloc[0]` over the seven would silently report whichever workflow sorted first.
SEJ_MODULES = {"wf4", "bamber19"}

def facts_rows(ssp, comp, year, sej):
    r = cmp_[(cmp_.source=="FACTS")&(cmp_.scenario==ssp)&(cmp_.component==comp)&(cmp_.year==year)]
    if r.empty: return r
    m = r.module.astype(str).isin(SEJ_MODULES)
    return r[m] if sej else r[~m]

def cell(ssp, comp, year, src):
    """(median, lo, hi, note) on the panel's own convention."""
    if src == "FACTS":
        r = facts_rows(ssp, comp, year, sej=False)
        if r.empty: return None
        return (float(r.med.median()), float(r.med.min()), float(r.med.max()),
                f"{len(r)} model-class wf")
    if src == "FACTS-SEJ":
        r = facts_rows(ssp, comp, year, sej=True)
        if r.empty: return None
        return (float(r.med.median()), float(r.p17.median()), float(r.p83.median()), "wf4 SEJ")
    r = cmp_[(cmp_.source==src)&(cmp_.scenario==ssp)&(cmp_.component==comp)&(cmp_.year==year)]
    if r.empty: return None
    r = r.iloc[0]
    # ⚠ BRICK 2.0 carries p05/p95 but NOT p17/p83 in this comparison file. Emitting dashes
    # would read as "no band"; emitting p05/p95 UNLABELLED would silently compare a 90%
    # interval against everyone else's 66%. Use p05-p95 and SAY SO in the footnote.
    if pd.isna(r["p17"]) and not pd.isna(r["p05"]):
        return (float(r["med"]), float(r["p05"]), float(r["p95"]), "5-95%")
    return (float(r["med"]), float(r["p17"]), float(r["p83"]), "17-83%")

PANEL_SRCS = ["Ladrillo", "FACTS", "FACTS-SEJ", "MAGICC-SLR", "BRICK 2.0"]
C_SRC["FACTS-SEJ"] = "tab:purple"

fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.6), constrained_layout=True)
for ax, ssp in zip(axes, SSPS):
    for si, src in enumerate(PANEL_SRCS):
        xs, ys, lo, hi = [], [], [], []
        for yi, y in enumerate(YEARS):
            c = cell(ssp, "total", y, src)
            if c is None: continue
            med, a, b, _ = c
            xs.append(yi + (si-2)*0.15); ys.append(med)
            lo.append(max(med-a, 0)); hi.append(max(b-med, 0))
        if not xs: continue
        ax.errorbar(xs, ys, yerr=[lo,hi], fmt="o", ms=5, capsize=3, lw=1.4,
                    color=C_SRC[src], label=src if ax is axes[0] else None)
    ax.set_xticks(range(len(YEARS))); ax.set_xticklabels(YEARS, fontsize=9)
    ax.set_title(ssp, fontsize=10); ax.axhline(0, color="0.8", lw=.6)
    ax.tick_params(labelsize=8); ax.set_yscale("symlog", linthresh=100)
axes[0].set_ylabel(f"total GMSL ({BASIS})  [symlog, linear below 100]", fontsize=8.5)
axes[0].legend(fontsize=7.5, loc="upper left")
fig.suptitle("FIG 2 — Total GMSL, medians. Ladrillo/MAGICC bars = 17-83%; FACTS bar = SPREAD "
             "ACROSS ITS 6 MODEL-CLASS WORKFLOWS.\nFACTS has no 2300. BRICK 2.0 is GLACIERS-ONLY "
             f"here, so it cannot appear in a total panel. wf4 (SEJ) shown separately.\n⚠ {BAND_CAVEAT}"
             f"   [commit {COMMIT}]", fontsize=9)
fig.savefig(OUT_F2, dpi=150)
plt.close(fig)
print("wrote", os.path.relpath(OUT_F2, REPO))

# ================= TABLES =======================================================
def fmt(v): return "—" if v is None or pd.isna(v) else f"{v:.1f}"

lines = [f"# Comparison tables — Ladrillo {TAG}", "",
         f"Basis: **{BASIS}**. Commit `{COMMIT}`. Frozen inputs hashed in "
         f"`benchmark/reference/_fixed/manifest.json`.", "",
         f"> ⚠ **{BAND_CAVEAT}**", "",
         "> ⚠ **Coverage is not uniform, and blanks mean *no data*, not zero.** "
         "FACTS stops at **2150**. MAGICC-SLR runs to **2300** (the comparison script's "
         "docstring saying it ends at 2100 is stale — verified against the file). "
         "**BRICK 2.0 appears only for glaciers**: in this comparison it is the legacy "
         "glacier-only arm, so it is absent from every other component by scope, not by omission.", "",
         "> ⚠ **FACTS is seven AR6 workflows, not one number.** The FACTS column is the "
         "**median of its 6 model-class workflows**, with the **min–max across them** in "
         "brackets — a between-workflow spread, NOT a probabilistic band. `wf4` is "
         "structured expert judgement (bamber19 in both ice sheets) and is reported on its "
         "own row, per `benchmark/comparator_classes.csv` and the house rule that SEJ "
         "envelopes are not scored against a calibrated model.", ""]

TAB_SRCS = ["Ladrillo", "FACTS", "FACTS-SEJ", "MAGICC-SLR", "BRICK 2.0"]
for comp, cl in [("total","Total GMSL"),("ais","Antarctica"),("gis","Greenland"),
                 ("glaciers","Glaciers"),("te","Thermal expansion")]:
    lines += [f"## {cl}", "",
              "| scenario | horizon | " + " | ".join(TAB_SRCS) + " |",
              "|---|---|" + "---|"*len(TAB_SRCS)]
    for ssp in SSPS:
        for y in YEARS:
            cells=[]
            for src in TAB_SRCS:
                c = cell(ssp, comp, y, src)
                cells.append("—" if c is None else f"{fmt(c[0])} [{fmt(c[1])}, {fmt(c[2])}]")
            lines.append(f"| {ssp} | {y} | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("Brackets: Ladrillo / MAGICC-SLR = **17–83%**; FACTS = **min–max across its 6 "
                 "model-class workflows** (a between-workflow spread, not a probabilistic band); "
                 "FACTS-SEJ = wf4, median of its 17–83%; **BRICK 2.0 = 5–95%**, because this "
                 "comparison file carries no p17/p83 for it — a WIDER interval than the others, "
                 "so do not read its bracket as comparable.")
    lines.append("")
open(OUT_TAB,"w").write("\n".join(lines))
print("wrote", os.path.relpath(OUT_TAB, REPO))
