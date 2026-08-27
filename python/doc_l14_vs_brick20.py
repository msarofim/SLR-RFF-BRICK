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

# ================= FIG 2 — projections vs FACTS / MAGICC / BRICK 2.0 / AR6 =======
cmp_ = pd.read_csv(COMPARE)
SSPS = ["ssp126","ssp245","ssp585"]
YEARS = [2100, 2150, 2300]

# ---- BRICK 2.0: READ THE FULL-COMPONENT FILE, NOT THE COMPARISON'S GLACIER-ONLY SOURCE ----
# ⚠ ladrillo_model_comparison.py:62 still reads outputs/ssps_gsic_2300.csv — glaciers only,
# lo/hi = 5-95%. That is WHY every non-glacier BRICK 2.0 cell was blank and why its bracket
# was a 90% interval. project_ssps_components_oldbrick.jl was written specifically to fix
# this ("every AIS / Greenland / TE / total cell of the comparison therefore had a BLANK
# where the reference model should be") and it DOES emit p17/p83 for all six components to
# 2300. bench_ladrillo.py uses it; the comparison script was never repointed.
# We read it directly here. NOT patching ladrillo_model_comparison.py: its output is hashed
# in benchmark/reference/_fixed/manifest.json, so repointing it is a benchmark-affecting
# change and belongs in its own commit with a re-freeze. FLAGGED, not silently done.
OLDBRICK = os.path.join(REPO, "outputs/ssps_components_2300_oldbrick.csv")
ob = pd.read_csv(OLDBRICK)
SSP_LABEL = {"ssp126":"SSP1-2.6", "ssp245":"SSP2-4.5", "ssp585":"SSP5-8.5"}

# ---- AR6 WG1 Ch9 Table 9.9 (Fox-Kemper 2021 p.1302), cm rel 1995-2014, median (17-83%) ----
# Transcribed in python/plot_b2_component_comparison.py, "verified from the chapter PDF
# 2026-08-05". This is THE IPCC ASSESSED NUMBER, not a FACTS workflow standing in for one.
# 2150 is TOTALS ONLY; there is no AR6 2300 row.
AR6 = {
 2100: {"te":{"ssp126":(14,11,18),"ssp245":(20,16,24),"ssp585":(30,24,36)},
        "gis":{"ssp126":(6,1,10),"ssp245":(8,4,13),"ssp585":(13,9,18)},
        "ais":{"ssp126":(11,3,27),"ssp245":(11,3,29),"ssp585":(12,3,34)},
        "glaciers":{"ssp126":(9,7,11),"ssp245":(12,10,15),"ssp585":(18,15,21)},
        "lws":{"ssp126":(3,1,4),"ssp245":(3,1,4),"ssp585":(3,1,4)},
        "total":{"ssp126":(44,32,62),"ssp245":(56,44,76),"ssp585":(77,63,101)}},
 2150: {"total":{"ssp126":(68,46,99),"ssp245":(92,66,133),"ssp585":(132,98,188)}},
}

# ---- FACTS workflows, IDENTIFIED FROM THE DATA (CHANGELOG "THE FACTS WORKFLOWS ARE NOW
# IDENTIFIED FROM THE DATA, NOT FROM THE AR6 TAXONOMY"), each 3/3 on three statistics:
#   wf1f = ar5AIS   + FittedISMIP        process, AR5-style AIS
#   wf2f = larmip   + FittedISMIP        process, no MICI and no expert elicitation
#   wf3f = deconto21 (MICI) + FittedISMIP
#   wf4  = bamber19 in BOTH ice sheets   the SEJ envelope
SEJ_MODULES = {"wf4", "bamber19"}
WF_NOTE = {"wf1f":"ar5AIS+FittedISMIP", "wf2f":"larmip+FittedISMIP",
           "wf3f":"deconto21/MICI+FittedISMIP", "wf4":"bamber19 both — SEJ"}

def _facts(ssp, comp, year, modules=None, sej=None):
    r = cmp_[(cmp_.source=="FACTS")&(cmp_.scenario==ssp)&(cmp_.component==comp)&(cmp_.year==year)]
    if r.empty: return r
    if modules is not None: return r[r.module.astype(str).isin(modules)]
    if sej is not None:
        m = r.module.astype(str).isin(SEJ_MODULES)
        return r[m] if sej else r[~m]
    return r

def cell(ssp, comp, year, src):
    """(median, lo, hi) — see the per-source bracket note in the table footnote."""
    if src == "FACTS range":                          # min-max of model-class workflow MEDIANS
        r = _facts(ssp, comp, year, sej=False)         # ⚠ MUST precede the startswith("FACTS ")
        if r.empty: return None                        # branch — "FACTS range" matches it too
        return (float(r.med.median()), float(r.med.min()), float(r.med.max()))
    if src.startswith("FACTS "):                      # a single named workflow
        wf = src.split()[1]
        r = _facts(ssp, comp, year, modules={wf})
        if r.empty: return None
        r = r.iloc[0]; return (float(r["med"]), float(r["p17"]), float(r["p83"]))
    if src == "AR6 T9.9":
        v = AR6.get(year, {}).get(comp, {}).get(ssp)
        return None if v is None else (float(v[0]), float(v[1]), float(v[2]))
    if src == "BRICK 2.0":
        r = ob[(ob.ssp==SSP_LABEL[ssp])&(ob.component==comp)&(ob.year==year)]
        if r.empty: return None
        r = r.iloc[0]; return (float(r["med"]), float(r["p17"]), float(r["p83"]))
    r = cmp_[(cmp_.source==src)&(cmp_.scenario==ssp)&(cmp_.component==comp)&(cmp_.year==year)]
    if r.empty: return None
    r = r.iloc[0]; return (float(r["med"]), float(r["p17"]), float(r["p83"]))

PANEL_SRCS = ["Ladrillo", "AR6 T9.9", "FACTS wf1f", "FACTS wf2f", "FACTS wf3f",
              "FACTS wf4", "MAGICC-SLR", "BRICK 2.0"]
C_SRC.update({"AR6 T9.9":"k", "FACTS wf1f":"tab:blue", "FACTS wf2f":"tab:cyan",
              "FACTS wf3f":"tab:olive", "FACTS wf4":"tab:purple", "FACTS range":"tab:blue"})

fig, axes = plt.subplots(1, 3, figsize=(16.5, 5.0), constrained_layout=True)
for ax, ssp in zip(axes, SSPS):
    for si, src in enumerate(PANEL_SRCS):
        xs, ys, lo, hi = [], [], [], []
        for yi, y in enumerate(YEARS):
            c = cell(ssp, "total", y, src)
            if c is None: continue
            med, a, b = c
            xs.append(yi + (si-3.5)*0.105); ys.append(med)
            lo.append(max(med-a,0)); hi.append(max(b-med,0))
        if not xs: continue
        mk = "s" if src=="AR6 T9.9" else "o"
        ax.errorbar(xs, ys, yerr=[lo,hi], fmt=mk, ms=5, capsize=2.5, lw=1.3,
                    color=C_SRC[src], label=src if ax is axes[0] else None)
    ax.set_xticks(range(len(YEARS))); ax.set_xticklabels(YEARS, fontsize=9)
    ax.set_title(ssp, fontsize=10); ax.axhline(0, color="0.8", lw=.6)
    ax.tick_params(labelsize=8); ax.set_yscale("symlog", linthresh=100)
axes[0].set_ylabel(f"total GMSL ({BASIS})  [symlog, linear below 100]", fontsize=8.5)
axes[0].legend(fontsize=7, loc="upper left", ncol=2)
fig.suptitle("FIG 2 — Total GMSL, medians with 17-83%. AR6 Table 9.9 (black squares) is the "
             "IPCC ASSESSED number, not a workflow proxy; it has NO 2300 row and only totals "
             "at 2150.\nFACTS workflows shown individually: wf1f=ar5AIS, wf2f=larmip (no MICI, "
             "no SEJ), wf3f=deconto21/MICI, wf4=bamber19 both = SEJ. FACTS has no 2300.\n"
             f"⚠ {BAND_CAVEAT}   [commit {COMMIT}]", fontsize=8.5)
fig.savefig(OUT_F2, dpi=150)
plt.close(fig)
print("wrote", os.path.relpath(OUT_F2, REPO))

# ================= TABLES =======================================================
def fmt(v): return "—" if v is None or pd.isna(v) else f"{v:.1f}"

lines = [f"# Comparison tables — Ladrillo {TAG}", "",
         f"Basis: **{BASIS}**. Commit `{COMMIT}`.", "",
         f"> ⚠ **{BAND_CAVEAT}**", "",
         "> **AR6 T9.9** = IPCC AR6 WG1 Ch9 Table 9.9 (Fox-Kemper 2021 p.1302), median and "
         "*likely* (17–83%) range, medium confidence — the **assessed IPCC number itself**, not "
         "a FACTS workflow standing in for one. **2150 is totals only; there is no AR6 2300 row.**", "",
         "> **FACTS workflows, identified from the data** (not from the AR6 taxonomy): "
         "`wf1f` = ar5AIS + FittedISMIP; `wf2f` = larmip + FittedISMIP (**no MICI, no expert "
         "elicitation** — the pure process workflow); `wf3f` = deconto21/**MICI** + FittedISMIP; "
         "`wf4` = **bamber19 in both ice sheets = the structured-expert-judgement envelope**. "
         "`FACTS range` = min–max across the six model-class workflow medians.", "",
         "> ⚠ **Coverage.** FACTS stops at **2150**. AR6 has no **2300**. MAGICC-SLR and "
         "BRICK 2.0 run to **2300**. Blanks are *absence of data*, not zero.", "",
         "> ✅ **BRICK 2.0 now has proper 17–83% bands for every component.** Earlier versions "
         "showed it only for glaciers at 5–95%, because `ladrillo_model_comparison.py:62` reads "
         "the superseded glacier-only `ssps_gsic_2300.csv`. These tables read "
         "`outputs/ssps_components_2300_oldbrick.csv` (all six components to 2300, p17/p83), "
         "which `project_ssps_components_oldbrick.jl` was written to produce for exactly this "
         "reason. **No BRICK 2.0 re-run was needed.**", ""]

TAB_SRCS = ["Ladrillo", "AR6 T9.9", "FACTS wf1f", "FACTS wf2f", "FACTS wf3f", "FACTS wf4",
            "FACTS range", "MAGICC-SLR", "BRICK 2.0"]
for comp, cl in [("total","Total GMSL"),("ais","Antarctica"),("gis","Greenland"),
                 ("glaciers","Glaciers"),("te","Thermal expansion"),("lws","Land water storage")]:
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
    lines += ["", "Brackets: **17–83%** for Ladrillo, AR6 T9.9, each FACTS workflow, MAGICC-SLR "
              "and BRICK 2.0. `FACTS range` bracket is **min–max across workflow medians** — a "
              "between-workflow spread, not a probabilistic band.", ""]
open(OUT_TAB,"w").write("\n".join(lines))
print("wrote", os.path.relpath(OUT_TAB, REPO))
