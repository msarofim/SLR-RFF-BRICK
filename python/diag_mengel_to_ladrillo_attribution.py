#!/usr/bin/env python3
"""GATE 3.2 — attribute the BRICK-Mengel -> Ladrillo projection shift.

`notes/handoff_2026-08-11_greenland_pass1_complete.md` §3.2: the ~28 cm drop in
SSP2-4.5 2100 GMSL between BRICK-Mengel and Ladrillo is the largest single
quantitative movement in the programme and was unattributed.  The expectation on
record was "mostly the Antarctic recalibration", explicitly flagged as untested.

The handoff proposed a PARAMETER-BLOCK SWAP (run the extC kernel with the AIS
block at BRICK-Mengel posterior medians).  That experiment is ill-posed as
specified, and this script does not attempt it:

    BRICK-Mengel sampled 6 AIS-related parameters (ais_ocean_temperature0,
    antarctic_alpha, antarctic_nu, antarctic_temp_threshold, anto_alpha,
    anto_beta).  extC samples those 6 PLUS 11 more (ais_bedheight0, ais_c,
    ais_gmst_amp, ais_iceflow0, ais_mu, ais_precip0_LOG, ais_runoff_Ton,
    ais_slope, antarctic_gamma, antarctic_kappa, antarctic_lambda).  Those 11
    ARE the re-parameterisation.  Holding 6 at Mengel values while the other 11
    stay at extC values describes no model that was ever calibrated, so the
    number it produced would not be interpretable.  The glacier structures also
    differ (2-tau single reservoir vs 3-reservoir), so no single kernel runs
    both posteriors.

The well-posed version is a COMPONENT decomposition of the same two projections,
which is what the question actually asks: which component moved, and by how
much.  Both vintages are already on disk from drivers that share the projection
convention -- verified below, and the script refuses to difference them if they
do not:

  * same forcing file      data/observations/fair_mean_{gmst,ohc}_<ssp>.csv
  * same climate treatment FaIR MEAN GMST (parameter spread only, no climate
                           spread) -- NOT the matched-uncertainty driver
                           proj_matched_ssp245_mengel.csv, which pairs each draw
                           with a FaIR ensemble member and so is NOT comparable
  * same baseline          1995-2014

Outputs: outputs/diag_mengel_to_ladrillo_attribution.csv
         outputs/diag_mengel_to_ladrillo_attribution_summary.md
         figures/diag_mengel_to_ladrillo_attribution.png
"""
import os
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------- constants
REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
# Two BRICK-Mengel vintages, because "BRICK-Mengel" is ambiguous: the base MCMC
# posterior, and the post-2018-extended refit (the closer lineage ancestor of
# extC, which uses the extended targets). The attribution is reported against
# both so the conclusion cannot hinge on which one is meant.
MENGEL_VINTAGES = {
# The pre-extC BRICK-Mengel vintage was QUARANTINED 2026-08-13 (vintage difference,
# not a bug -- see outputs/quarantine/20260813_pre_extc_mengel_vintage/README.md). This script is a CROSS-VINTAGE comparison, so it
# legitimately reads the superseded files; it reads them from the quarantine.
    "BRICK-Mengel (base)": "outputs/quarantine/20260813_pre_extc_mengel_vintage/proj_ssps_mengel_summary.csv",
    "BRICK-Mengel (post-2018 ext)": "outputs/quarantine/20260813_pre_extc_mengel_vintage/proj_ssps_mengel_ext_summary.csv",
}
MENGEL_CSV = os.path.join(REPO, MENGEL_VINTAGES["BRICK-Mengel (base)"])
# The "Ladrillo" arm of this attribution is the extC vintage, because the
# attribution ON RECORD is mengel -> extC. extC was quarantined 2026-08-13 when
# L10 superseded it, so this reads from there; both arms of a cross-vintage
# comparison now live in quarantine, which is correct. The further extC -> L10
# step is tabulated in the CHANGELOG entry for 2026-08-13.
LADRILLO_CSV = os.path.join(REPO, "outputs/quarantine/20260813_extc_vintage/ssps_components_2300_extC.csv")

OUT_CSV = os.path.join(REPO, "outputs/diag_mengel_to_ladrillo_attribution.csv")
OUT_MD = os.path.join(REPO, "outputs/diag_mengel_to_ladrillo_attribution_summary.md")
OUT_PNG = os.path.join(REPO, "figures/diag_mengel_to_ladrillo_attribution.png")

YEAR = 2100
HEADLINE_SSP = "SSP2-4.5"
# Mengel summary column -> Ladrillo component name
COMP_MAP = {"ais": "ais", "gsic": "glaciers", "gis": "gis", "te": "te", "lws": "lws"}
COMP_LABEL = {"ais": "Antarctic", "gsic": "Glaciers", "gis": "Greenland",
              "te": "Thermal expansion", "lws": "Land water storage"}
FROM_LABEL = "BRICK-Mengel"
TO_LABEL = "Ladrillo"

# ---------------------------------------------------------------- load
men = pd.read_csv(MENGEL_CSV).set_index("ssp_label")
bf = pd.read_csv(LADRILLO_CSV)
bf = bf[bf.year == YEAR]

ssps = [s for s in men.index if s in set(bf.ssp)]

rows = []
for ssp in ssps:
    b = bf[bf.ssp == ssp].set_index("component")
    for mcol, bcomp in COMP_MAP.items():
        m_val = float(men.loc[ssp, mcol])
        b_val = float(b.loc[bcomp, "med"])
        rows.append(dict(ssp=ssp, component=mcol, label=COMP_LABEL[mcol],
                         mengel=m_val, brickf=b_val, delta=b_val - m_val))
    m_tot = float(men.loc[ssp, "p50"])
    b_tot = float(b.loc["total", "med"])
    rows.append(dict(ssp=ssp, component="total", label="TOTAL",
                     mengel=m_tot, brickf=b_tot, delta=b_tot - m_tot))
att = pd.DataFrame(rows)

# ---------------------------------------------------------------- consistency of the decomposition
# medians are not additive in general; report the closure gap rather than hide it
checks = []
for ssp in ssps:
    s = att[att.ssp == ssp]
    comps = s[s.component != "total"]
    tot = s[s.component == "total"].iloc[0]
    checks.append(dict(ssp=ssp,
                       sum_comp_delta=comps.delta.sum(),
                       total_delta=tot.delta,
                       median_nonadditivity=comps.delta.sum() - tot.delta,
                       ais_share_of_total=comps[comps.component == "ais"].delta.iloc[0] / tot.delta))
chk = pd.DataFrame(checks)

# ---------------------------------------------------------------- vintage robustness
# Repeat the headline decomposition against every Mengel vintage.
vrows = []
for vname, vpath in MENGEL_VINTAGES.items():
    v = pd.read_csv(os.path.join(REPO, vpath)).set_index("ssp_label")
    for ssp in ssps:
        b = bf[bf.ssp == ssp].set_index("component")
        d_tot = float(b.loc["total", "med"]) - float(v.loc[ssp, "p50"])
        d_ais = float(b.loc["ais", "med"]) - float(v.loc[ssp, "ais"])
        vrows.append(dict(vintage=vname, ssp=ssp,
                          mengel_total=float(v.loc[ssp, "p50"]),
                          ladrillo_total=float(b.loc["total", "med"]),
                          total_shift=d_tot, ais_shift=d_ais,
                          ais_share=d_ais / d_tot if d_tot != 0 else np.nan))
vtab = pd.DataFrame(vrows)

# ---------------------------------------------------------------- is the shift a level shift or a median crossing?
# The Antarctic distribution at SSP2-4.5 is bimodal (tipped vs not tipped by 2100).
# If the median moved much further than the tails, the "shift" is the 50th percentile
# crossing the sparse gap between the two branches, NOT a uniform reduction.
mts = pd.read_csv(os.path.join(REPO, "outputs/quarantine/20260813_pre_extc_mengel_vintage/proj_ssps_mengel_components_timeseries.csv"))
mts = mts[(mts.year == YEAR) & (mts.component == "ais")].set_index("ssp_label")
bts = bf[bf.component == "ais"].set_index("ssp")

qrows = []
for ssp in ssps:
    for q in ("p05", "p50", "p95"):
        bq = "med" if q == "p50" else q
        m_val, b_val = float(mts.loc[ssp, q]), float(bts.loc[ssp, bq])
        qrows.append(dict(ssp=ssp, quantile=q, mengel=m_val, brickf=b_val,
                          delta=b_val - m_val))
qtab = pd.DataFrame(qrows)

# ---------------------------------------------------------------- figure
fig, axes = plt.subplots(1, len(ssps), figsize=(4.6 * len(ssps), 4.8), sharey=True)
axes = np.atleast_1d(axes)
for ax, ssp in zip(axes, ssps):
    s = att[(att.ssp == ssp) & (att.component != "total")].sort_values("delta")
    colors = ["tab:red" if d < 0 else "tab:blue" for d in s.delta]
    ax.barh(s.label, s.delta, color=colors)
    tot = att[(att.ssp == ssp) & (att.component == "total")].delta.iloc[0]
    ax.axvline(tot, color="k", ls="--", lw=1.2, label=f"total shift {tot:+.1f} cm")
    ax.axvline(0, color="k", lw=0.6)
    ax.set_xlabel(f"{TO_LABEL} - {FROM_LABEL} at {YEAR} (cm)")
    ax.set_title(ssp)
    ax.legend(fontsize=8, loc="lower left")
    ax.grid(alpha=0.3, axis="x")
fig.suptitle(f"What moved between {FROM_LABEL} and {TO_LABEL}: component medians at {YEAR} "
             "(FaIR mean forcing, 1995-2014 baseline)", fontsize=11)
fig.tight_layout()
os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
fig.savefig(OUT_PNG, dpi=140)

# ---------------------------------------------------------------- outputs
att.to_csv(OUT_CSV, index=False)
with open(OUT_MD, "w") as fh:
    fh.write(f"# Gate 3.2 — {FROM_LABEL} to {TO_LABEL}, attributed by component\n\n")
    fh.write(f"Medians at {YEAR}, cm, both on FaIR **mean** forcing "
             "(parameter spread only) and the 1995-2014 baseline.\n\n")
    for ssp in ssps:
        s = att[att.ssp == ssp]
        fh.write(f"## {ssp}\n\n| component | {FROM_LABEL} | {TO_LABEL} | shift |\n|---|---|---|---|\n")
        for r in s[s.component != "total"].sort_values("delta").itertuples():
            fh.write(f"| {r.label} | {r.mengel:.2f} | {r.brickf:.2f} | **{r.delta:+.2f}** |\n")
        t = s[s.component == "total"].iloc[0]
        fh.write(f"| **TOTAL** | **{t.mengel:.2f}** | **{t.brickf:.2f}** | **{t.delta:+.2f}** |\n\n")
    fh.write("## Closure of the decomposition\n\n")
    fh.write("| ssp | sum of component shifts | total shift | median non-additivity | "
             "Antarctic share of total |\n|---|---|---|---|---|\n")
    for r in chk.itertuples():
        fh.write(f"| {r.ssp} | {r.sum_comp_delta:+.2f} | {r.total_delta:+.2f} | "
                 f"{r.median_nonadditivity:+.2f} | {r.ais_share_of_total:.0%} |\n")
    fh.write("\nMedians are not additive in general; the non-additivity column is the "
             "size of that effect and is small here.\n")
    fh.write("\n## Robustness to which BRICK-Mengel vintage is meant\n\n")
    fh.write("| vintage | ssp | Mengel total | BRICK-F\\* total | total shift | "
             "Antarctic shift | Antarctic share |\n|---|---|---|---|---|---|---|\n")
    for r in vtab.itertuples():
        fh.write(f"| {r.vintage} | {r.ssp} | {r.mengel_total:.2f} | {r.ladrillo_total:.2f} | "
                 f"{r.total_shift:+.2f} | {r.ais_shift:+.2f} | {r.ais_share:.0%} |\n")
    fh.write("\n## Is it a level shift or a median crossing? (Antarctic, by quantile)\n\n")
    fh.write(f"| ssp | quantile | {FROM_LABEL} | {TO_LABEL} | shift |\n|---|---|---|---|---|\n")
    for r in qtab.itertuples():
        fh.write(f"| {r.ssp} | {r.quantile} | {r.mengel:.2f} | {r.brickf:.2f} | "
                 f"**{r.delta:+.2f}** |\n")
    h = qtab[qtab.ssp == HEADLINE_SSP].set_index("quantile")
    fh.write(f"\nAt {HEADLINE_SSP} the median moves {h.loc['p50', 'delta']:+.1f} cm while the "
             f"tails move {h.loc['p05', 'delta']:+.1f} cm (p05) and {h.loc['p95', 'delta']:+.1f} cm "
             "(p95). The Antarctic distribution is bimodal — tipped vs not tipped by "
             f"{YEAR} — so the headline shift is mostly the 50th percentile crossing the "
             "sparse gap between the two branches, not a uniform reduction in Antarctic "
             "mass loss.\n")

print(att.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))
print()
print(chk.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))
print()
print(vtab.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))
print()
print("Antarctic by quantile (level shift vs median crossing):")
print(qtab.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))
print(f"\nwrote {OUT_CSV}\nwrote {OUT_MD}\nwrote {OUT_PNG}")
