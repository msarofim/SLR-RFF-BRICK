#!/usr/bin/env python3
"""GATE 3.1 — resolve the component-vs-total target conflict before the joint
recalibration (notes/handoff_2026-08-11_greenland_pass1_complete.md §3.1,
notes/redteam_2026-08-11_brickf.md §0).

The finding under test: summing the five component targets in
outputs/recalib_targets_ext.csv gives +0.738 cm MORE sea level over 1950-1980
than the independent total target, in exactly the window where the new Greenland
A+B module wants to melt ~0.5-0.7 cm MORE ice.  If that residual is a component
we spliced, it is our bug.  If it is Dangendorf-vs-Frederikse at the total
level, it is a citable difference between two reconstructions and must be
handled on the data side (target sigma), not left for the sampler to split.

The decomposition is EXACT and additive, because every series is re-referenced
to the same window:

    Sigma_components - Dangendorf
        = (Sigma_components - Frederikse_GMSL)   <- budget closure, internal to Frederikse
        + (Frederikse_GMSL - Dangendorf)         <- reconstruction difference

Term 1 is scored against the Frederikse 5000-member ensemble's OWN per-member
budget residual (the members are jointly sampled, so this is the honest spread).
Term 2 is scored against Dangendorf's own per-year SE from the corrected
Global_v2.nc -- the same sigma the calibration likelihood uses.

Also reported: whether any spliced (post-2018) datum can reach the conflict
window at all, and the per-component sigma over the window, which is what
determines whether glaciers or TE could absorb the Greenland melt (red-team
outcome 2).

Outputs: outputs/diag_target_conflict.csv
         outputs/diag_target_conflict_summary.md
         figures/diag_target_conflict.png
"""
import os
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------- constants
# (every label, title and filename below derives from these)
REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
RAW = os.path.join(REPO, "data/observations/raw")
TARGETS_CSV = os.path.join(REPO, "outputs/recalib_targets_ext.csv")
FRED_ENS_NC = os.path.join(RAW, "frederikse2020_GMSL_ensembles.nc")
DANG_V2_NC = os.path.join(RAW, "dangendorf2024_KalmanSmootherHR_Global_v2.nc")

OUT_CSV = os.path.join(REPO, "outputs/diag_target_conflict.csv")
OUT_MD = os.path.join(REPO, "outputs/diag_target_conflict_summary.md")
OUT_PNG = os.path.join(REPO, "figures/diag_target_conflict.png")

BASE_Y0, BASE_Y1 = 1995, 2005          # re-reference window used by prep_recalib_targets_ext.py
CONFLICT_Y0, CONFLICT_Y1 = 1950, 1980  # the window the red team flagged
GIS_MISS_Y0, GIS_MISS_Y1 = 1942, 1982  # window where the GIS target sits above the model
WINDOWS = [(1900, 1930), (CONFLICT_Y0, CONFLICT_Y1), (GIS_MISS_Y0, GIS_MISS_Y1), (1993, 2018)]
COMPONENTS = ["ais", "gsic", "gis", "steric", "lws"]
# ensemble variable -> target column
ENS_VAR = {"ais": "AIS", "gsic": "Glaciers", "gis": "GrIS", "steric": "Steric", "lws": "TWS"}
ENS_TOTAL_VAR = "GMSL"
SPLICE_FIRST_YEAR = 2019               # earliest year any modern product enters a component
BAND_PCTL = (5.0, 95.0)

BASE_LABEL = f"{BASE_Y0}-{BASE_Y1}"
CONFLICT_LABEL = f"{CONFLICT_Y0}-{CONFLICT_Y1}"


def wmean_sd(x, w):
    m = np.average(x, weights=w)
    return m, float(np.sqrt(np.average((x - m) ** 2, weights=w)))


def wquantile(x, w, q):
    idx = np.argsort(x)
    xs, ws = x[idx], w[idx]
    cw = (np.cumsum(ws) - 0.5 * ws) / ws.sum()
    return np.interp(np.asarray(q, dtype=float) / 100.0, cw, xs)


def wmean(series, y0, y1):
    """Mean of a year-indexed series over [y0, y1]."""
    return float(series.loc[y0:y1].mean())


# ---------------------------------------------------------------- the targets as fed to the fit
tg = pd.read_csv(TARGETS_CSV).set_index("year")
comp_sum = tg[COMPONENTS].sum(axis=1, min_count=len(COMPONENTS))
total = tg["dang"]
resid = comp_sum - total

# ---------------------------------------------------------------- Frederikse ensemble
ens = xr.open_dataset(FRED_ENS_NC)
ey = ens["time"].values.astype(int)
w = ens["likelihood"].values.astype(float)
win = (ey >= BASE_Y0) & (ey <= BASE_Y1)


def reref_ens(var):
    m = ens[var].values / 10.0                       # mm -> cm
    return m - m[:, win].mean(axis=1, keepdims=True)  # per-member single offset


ens_comp = sum(reref_ens(v) for v in ENS_VAR.values())   # (member, year) budget, cm
ens_gmsl = reref_ens(ENS_TOTAL_VAR)                      # (member, year) observed GMSL, cm
ens_close = ens_comp - ens_gmsl                          # per-member budget closure residual

fred_gmsl_med = np.array([wquantile(ens_gmsl[:, i], w, 50.0) for i in range(len(ey))])
fred_gmsl_s = pd.Series(fred_gmsl_med, index=ey)
fred_comp_med = pd.Series([wquantile(ens_comp[:, i], w, 50.0) for i in range(len(ey))], index=ey)

# ---------------------------------------------------------------- Dangendorf's own SE
with xr.open_dataset(DANG_V2_NC) as dv2:
    dang_sig = pd.Series(dv2["GMSLHRSE"].values.ravel() * 100.0,       # m -> cm
                         index=dv2["t"].values.ravel().astype(int))

# ---------------------------------------------------------------- exact two-term split
term_closure = comp_sum - fred_gmsl_s.reindex(comp_sum.index)   # Sigma comps - Frederikse GMSL
term_recon = fred_gmsl_s.reindex(comp_sum.index) - total        # Frederikse GMSL - Dangendorf

# ---------------------------------------------------------------- per-window table
rows = []
for y0, y1 in WINDOWS:
    sel_e = (ey >= y0) & (ey <= y1)
    if sel_e.sum() == 0:
        continue
    # window-mean budget closure across ensemble members (cm)
    close_win = ens_close[:, sel_e].mean(axis=1)
    close_med = float(wquantile(close_win, w, 50.0))
    close_lo, close_hi = wquantile(close_win, w, list(BAND_PCTL))
    _, close_sd = wmean_sd(close_win, w)

    r_close = wmean(term_closure, y0, y1)
    r_recon = wmean(term_recon, y0, y1)
    dsig = float(dang_sig.loc[y0:y1].mean())
    rows.append(dict(
        window=f"{y0}-{y1}",
        sum_comp=wmean(comp_sum, y0, y1),
        total=wmean(total, y0, y1),
        residual=wmean(resid, y0, y1),
        closure=r_close,
        recon=r_recon,
        closure_ens_med=close_med,
        closure_ens_sd=close_sd,
        closure_ens_lo=close_lo,
        closure_ens_hi=close_hi,
        closure_z=(r_close - close_med) / close_sd if close_sd > 0 else np.nan,
        dang_sigma=dsig,
        recon_z=r_recon / dsig if dsig > 0 else np.nan,
    ))
tab = pd.DataFrame(rows)

# ---------------------------------------------------------------- per-component window stats
comp_rows = []
for c in COMPONENTS:
    sig = (tg[c + "_hi"] - tg[c + "_lo"]) / (2 * 1.645)     # sigma as the likelihood sees it
    comp_rows.append(dict(
        component=c,
        mean_cm=wmean(tg[c], CONFLICT_Y0, CONFLICT_Y1),
        sigma_cm=wmean(sig, CONFLICT_Y0, CONFLICT_Y1),
        span_cm=wmean(tg[c], CONFLICT_Y0, CONFLICT_Y1) - wmean(tg[c], BASE_Y0, BASE_Y1),
    ))
comp_tab = pd.DataFrame(comp_rows)
comp_tab["sigma_share"] = comp_tab.sigma_cm / comp_tab.sigma_cm.sum()

# ---------------------------------------------------------------- splice reachability check
splice_reaches = SPLICE_FIRST_YEAR <= CONFLICT_Y1
dang_covers = bool(np.isfinite(tg.loc[CONFLICT_Y0:CONFLICT_Y1, "dang"]).all())

# ---------------------------------------------------------------- figure
fig, axes = plt.subplots(2, 1, figsize=(9, 8), sharex=True,
                         gridspec_kw={"height_ratios": [2, 1.2]})
ax = axes[0]
ax.plot(comp_sum.index, comp_sum.values, color="tab:cyan", lw=1.6,
        label="Sigma of 5 component targets (Frederikse-derived)")
ax.plot(fred_comp_med.index, fred_comp_med.values, color="tab:blue", lw=1.0, ls=":",
        label="Frederikse ensemble component sum (weighted median)")
ax.plot(fred_gmsl_s.index, fred_gmsl_s.values, color="tab:blue", lw=1.4,
        label="Frederikse observed GMSL (weighted median)")
ax.plot(total.index, total.values, color="tab:red", lw=1.6,
        label="Total target: Dangendorf 2024 + NOAA STAR")
ax.axvspan(CONFLICT_Y0, CONFLICT_Y1, color="grey", alpha=0.15)
ax.set_ylabel(f"sea level (cm, rel. {BASE_LABEL})")
ax.legend(fontsize=8, loc="upper left")
ax.set_title(f"Target conflict decomposition (grey = {CONFLICT_LABEL} conflict window)")
ax.grid(alpha=0.3)

ax = axes[1]
ax.plot(resid.index, resid.values, color="k", lw=1.8, label="residual: Sigma comps - total")
ax.plot(term_closure.index, term_closure.values, color="tab:green", lw=1.2,
        label="budget closure: Sigma comps - Frederikse GMSL")
ax.plot(term_recon.index, term_recon.values, color="tab:orange", lw=1.2,
        label="reconstruction: Frederikse GMSL - Dangendorf")
ax.fill_between(dang_sig.index, -1.645 * dang_sig.values, 1.645 * dang_sig.values,
                color="tab:red", alpha=0.15, label="Dangendorf +/- 1.645 sigma (own SE)")
ax.axhline(0, color="k", lw=0.5)
ax.axvspan(CONFLICT_Y0, CONFLICT_Y1, color="grey", alpha=0.15)
ax.set_ylabel("cm")
ax.set_xlabel("year")
ax.legend(fontsize=8, loc="upper left")
ax.grid(alpha=0.3)
fig.tight_layout()
os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
fig.savefig(OUT_PNG, dpi=140)

# ---------------------------------------------------------------- outputs
out = pd.DataFrame({
    "year": comp_sum.index,
    "sum_components": comp_sum.values,
    "total_target": total.values,
    "residual": resid.values,
    "term_budget_closure": term_closure.values,
    "term_reconstruction": term_recon.values,
    "frederikse_gmsl": fred_gmsl_s.reindex(comp_sum.index).values,
    "dang_sigma": dang_sig.reindex(comp_sum.index).values,
})
out.to_csv(OUT_CSV, index=False)

with open(OUT_MD, "w") as fh:
    fh.write("# Gate 3.1 — component-vs-total target conflict, decomposed\n\n")
    fh.write(f"All series relative to {BASE_LABEL}. Positive residual = the component "
             "budget carries MORE sea level than the independent total target.\n\n")
    fh.write("## Exact decomposition by window (cm)\n\n")
    fh.write("| window | Sigma comps | total | residual | = closure | + reconstruction | "
             "closure z (vs F ens) | recon z (vs Dang SE) |\n")
    fh.write("|---|---|---|---|---|---|---|---|\n")
    for r in tab.itertuples():
        fh.write(f"| {r.window} | {r.sum_comp:+.3f} | {r.total:+.3f} | {r.residual:+.3f} | "
                 f"{r.closure:+.3f} | {r.recon:+.3f} | {r.closure_z:+.2f} | {r.recon_z:+.2f} |\n")
    fh.write("\n## Frederikse's own budget closure (ensemble, window means)\n\n")
    fh.write(f"| window | our closure | ensemble median | ensemble {BAND_PCTL[0]:.0f}-"
             f"{BAND_PCTL[1]:.0f}% | ensemble sd |\n|---|---|---|---|---|\n")
    for r in tab.itertuples():
        fh.write(f"| {r.window} | {r.closure:+.3f} | {r.closure_ens_med:+.3f} | "
                 f"[{r.closure_ens_lo:+.3f}, {r.closure_ens_hi:+.3f}] | {r.closure_ens_sd:.3f} |\n")
    fh.write(f"\n## Component target sigma over {CONFLICT_LABEL} "
             "(what could absorb a Greenland change)\n\n")
    fh.write("| component | mean (cm) | sigma (cm) | share of summed sigma |\n|---|---|---|---|\n")
    for r in comp_tab.itertuples():
        fh.write(f"| {r.component} | {r.mean_cm:+.3f} | {r.sigma_cm:.3f} | "
                 f"{r.sigma_share:.1%} |\n")
    fh.write("\n## Provenance checks\n\n")
    fh.write(f"- earliest spliced (modern-product) year in any component: {SPLICE_FIRST_YEAR}; "
             f"reaches the {CONFLICT_LABEL} window: **{splice_reaches}**\n")
    fh.write(f"- Dangendorf total target finite throughout {CONFLICT_LABEL}: **{dang_covers}** "
             "(so the total is the reconstruction, not the STAR splice)\n")

print(tab.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))
print()
print(comp_tab.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
print(f"\nsplice reaches conflict window: {splice_reaches}; "
      f"Dangendorf covers it: {dang_covers}")
print(f"wrote {OUT_CSV}\nwrote {OUT_MD}\nwrote {OUT_PNG}")
