#!/usr/bin/env python3
"""
v11_paper_number_diff.py -- every GMD-draft number that Ladrillo v1.1 can move: printed -> v1.0 file -> v1.1 file.

    python python/v11_paper_number_diff.py
Writes outputs/v11_paper_number_diff_20261008.csv (+ provenance) and prints a markdown table.

PRINTED is the value in Tony's returned copy (deliverables/GMD.Ladrillo.v1_forTonyreview_TW1.docx, read with pandoc,
changes accepted). That copy still carries the pre-CMIP7 van Vuuren numbers: the 10-07 diff
(notes/vv_cmip7_paper_number_diff_2026-10-07.md) was never applied, so "printed -> v1.1" folds BOTH rounds together and
"v1.0 file -> v1.1 file" isolates v1.1.
V1.0 FILE = the v1.0 output: the copy in the quarantine snapshot (run_ladrillo_v11_rerun_20261008.sh), or the canonical
file when the prune found it unchanged. V1.1 FILE = the canonical output after the rerun.
The quantity map (source file, filter, statistic, the text's rounding) was built 2026-10-08 by reading the draft against
the CHANGELOG and the redline scripts; the inline Sect. 4.1 arithmetic follows deliverables/redline/apply_edits_r6_l27.py
L100-124 and the refit-precision arithmetic apply_edits_r7_precision.py L13-25.
"""
import os, math, subprocess, datetime
import numpy as np, pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = os.path.join(REPO, "outputs/quarantine/20261008_ladrillo_v10_superseded/outputs")
OUT = os.path.join(REPO, "outputs/v11_paper_number_diff_20261008.csv")
TAP = "_tap4p69K_V5p64m_tau800"
LAB = {"ssp126": "SSP1-2.6", "ssp245": "SSP2-4.5", "ssp585": "SSP5-8.5"}

def path(f, ver):
    q, c = os.path.join(Q, f), os.path.join(REPO, "outputs", f)
    return (q if os.path.exists(q) else c) if ver == "v1.0" else c
_cache = {}
def rd(f, ver):
    k = (f, ver)
    if k not in _cache:
        _cache[k] = pd.read_csv(path(f, ver), float_precision="round_trip")
    return _cache[k]

## ---- accessors ------------------------------------------------------------------------------------------------
def cells(f, comp, H, ver, stat="med_cm", arm="joint"):
    d = rd(f, ver); r = d[(d.component == comp) & (d.horizon == H) & (d.arm == arm)]
    assert len(r) == 1, (f, comp, H, arm, len(r)); return float(r[stat].iloc[0])
def width(f, comp, H, ver): return cells(f, comp, H, ver, "p95_cm") - cells(f, comp, H, ver, "p05_cm")
LAD = lambda s: f"scope_slr_fairunc_cells_{s}_spliced_L27{TAP}.csv"
LADNT = lambda s: f"scope_slr_fairunc_cells_{s}_spliced_L27.csv"
LADM = lambda s: f"scope_slr_fairunc_cells_{s}_spliced_magiccclim_L27{TAP}.csv"
BRK = lambda s: f"scope_slr_fairunc_cells_{s}_spliced_oldbrick.csv"
BRKM = lambda s: f"scope_slr_fairunc_cells_{s}_spliced_oldbrick_magiccclim.csv"
def panel(tag, ssp, comp, year, ver):
    d = rd(f"ssps_components_2300_{tag}{TAP}_n2_ws.csv", ver)
    r = d[(d.ssp == LAB[ssp]) & (d.component == comp) & (d.year == year)]
    assert len(r) == 1; return float(r.med.iloc[0])
def lev(ssp, ver, share=False):
    d = rd("diag_ais_amp_leverage_L27.csv", ver)
    r = d[(d.ssp == ssp) & (d.horizon == 2300) & (d.definition == "perturbation") & (d.sigma_kind == "prior")]
    assert len(r) == 1; r = r.iloc[0]
    return 100 * r.leverage_mean_cm / r.total_med_cm if share else float(r.leverage_mean_cm)
def pp_mean(col, y0, y1, ver, tag="L27"):
    d = rd(f"postpred_{tag}_components_timeseries.csv", ver)
    return float(d[(d.year >= y0) & (d.year <= y1)][col].mean())
def score(window, comp, ver):
    d = rd("scope_ladrillo_vs_brick20_scorecard_L27.csv", ver)
    g = lambda a: float(d[(d.window == window) & (d.component == comp) & (d.arm == a)].rmse.iloc[0])
    return g("Ladrillo") / g("BRICK 2.0")
def score_rmse(window, comp, arm, ver):
    d = rd("scope_ladrillo_vs_brick20_scorecard_L27.csv", ver)
    return float(d[(d.window == window) & (d.component == comp) & (d.arm == arm)].rmse.iloc[0])
def imbie(col, ver):
    d = rd("diag_imbie2026_vs_targets_windows_L27.csv", ver)
    r = d[(d.component == "AIS") & (d.y0 == 1979) & (d.y1 == 2023)]
    assert len(r) == 1; return float(r[col].iloc[0])
def refit_proj(ver):
    cellsr = [("ssp245", 2100), ("ssp245", 2300), ("ssp585", 2100), ("ssp585", 2300), ("ssp126", 2300)]
    return max(abs(panel("L27r", s, "ais", y, ver) - panel("L27", s, "ais", y, ver)) for s, y in cellsr)
def refit_hind(ver):
    a, b = rd("postpred_L27_components_timeseries.csv", ver), rd("postpred_L27r_components_timeseries.csv", ver)
    def rmse(d, c):
        x = d[(d.year >= 1900) & (d.year <= 2026)][[f"{c}_p50", f"{c}_obs"]].dropna()
        return math.sqrt(((x.iloc[:, 0] - x.iloc[:, 1]) ** 2).mean())
    return max(abs(rmse(b, c) - rmse(a, c)) for c in ("glaciers", "ais", "gis", "te"))
def resp(comp, H, src_cells, ver):
    return cells(src_cells("vvH"), comp, H, ver) - cells(src_cells("vvVL"), comp, H, ver)
def ais_gap(scen, ver): return cells(BRK(scen), "ais", 2300, ver) - cells(LAD(scen), "ais", 2300, ver)
TAPP = "diag_tap_paired_contribution_L27.csv"     # python/diag_tap_paired_contribution.py; carries both versions
def tapp(scen, stat, ver, H=2300, comp="total"):
    d = pd.read_csv(os.path.join(REPO, "outputs", TAPP), float_precision="round_trip")
    r = d[(d.version == ver) & (d.scenario == scen) & (d.horizon == H) & (d.component == comp)]
    assert len(r) == 1, (scen, stat, ver, H, comp, len(r)); return float(r[stat].iloc[0])

## ---- the quoted numbers -------------------------------------------------------------------------------------------
## (where, quantity, printed, fmt, function(ver), exposure)  exposure: A+B Ladrillo AIS/total; B BRICK 2.0 AIS/total;
## PP posterior-predictive hindcast (2021-2026 only); U-bit component bit-identical (listed only where already stale)
fmt = {"int": lambda v: f"{v:.0f}", "1dp": lambda v: f"{v:.1f}", "2dp": lambda v: f"{v:.2f}",
       "3dp": lambda v: f"{v:.3f}", "3up": lambda v: f"{math.ceil(v * 1000 - 1e-9) / 1000:.3f}"}
ROWS = [
 ("Abstract", "AIS RMSE reduction vs BRICK 2.0, full window (%)", "94", "int", lambda v: 100 * (1 - score("full", "AIS", v)), "PP"),
 ("Intro", "glacier responsiveness ratio Ladrillo/BRICK 2.0 (vvH-vvVL, 2300) [STALE since 10-07]", "1.3", "1dp",
  lambda v: resp("glaciers", 2300, LAD, v) / resp("glaciers", 2300, BRK, v), "U-bit"),
 ("Intro", "AIS responsiveness Ladrillo (vvH-vvVL, 2300)", "(=TE)", "1dp", lambda v: resp("ais", 2300, LAD, v), "A+B"),
 ("Intro", "AIS responsiveness BRICK 2.0 (vvH-vvVL, 2300)", "(=TE)", "1dp", lambda v: resp("ais", 2300, BRK, v), "B"),
 ("Intro", "AIS responsiveness Ladrillo (vvH-vvVL, 2100)", "(< BRICK)", "1dp", lambda v: resp("ais", 2100, LAD, v), "A+B"),
 ("Intro", "AIS responsiveness BRICK 2.0 (vvH-vvVL, 2100)", "(< BRICK)", "1dp", lambda v: resp("ais", 2100, BRK, v), "B"),
 ("2.2.2", "tap contribution SSP5-8.5 total 2300 (difference of the total medians, joint) [superseded 10-08]", "36.5", "1dp",
  lambda v: cells(LAD("ssp585"), "total", 2300, v) - cells(LADNT("ssp585"), "total", 2300, v), "A+B"),
 ("2.2.2", "tap contribution SSP2-4.5 total 2300 [superseded 10-08]", "0.3", "1dp",
  lambda v: cells(LAD("ssp245"), "total", 2300, v) - cells(LADNT("ssp245"), "total", 2300, v), "A+B"),
 ("2.2.2", "tap contribution SSP1-2.6 total 2300 [superseded 10-08]", "0", "2dp",
  lambda v: cells(LAD("ssp126"), "total", 2300, v) - cells(LADNT("ssp126"), "total", 2300, v), "A+B"),
 ## RULED 10-08 (decision 4): 2.2.2 quotes the PAIRED statistics below instead of the difference of medians above.
 ("2.2.2", "tap [RULED 10-08] share of draws in which it fires, SSP5-8.5 2300 (%)", "(new)", "2dp",
  lambda v: 100 * tapp("ssp585", "fires_share", v), "A+B"),
 ("2.2.2", "tap [RULED 10-08] paired mean contribution, SSP5-8.5 total 2300", "(new)", "1dp",
  lambda v: tapp("ssp585", "paired_mean_cm", v), "A+B"),
 ("2.2.2", "tap [RULED 10-08] share of draws in which it fires, SSP2-4.5 2300 (%)", "(new)", "2dp",
  lambda v: 100 * tapp("ssp245", "fires_share", v), "A+B"),
 ("2.2.2", "tap [RULED 10-08] paired mean contribution, SSP2-4.5 total 2300", "(new)", "1dp",
  lambda v: tapp("ssp245", "paired_mean_cm", v), "A+B"),
 ("2.2.2", "tap [RULED 10-08] share of draws in which it fires, SSP1-2.6 2300 (%)", "(new)", "2dp",
  lambda v: 100 * tapp("ssp126", "fires_share", v), "A+B"),
 ("2.2.2", "tap [RULED 10-08] paired mean contribution, SSP1-2.6 total 2300", "(new)", "2dp",
  lambda v: tapp("ssp126", "paired_mean_cm", v), "A+B"),
 ("2.2.3", "amp leverage, +1 prior sd, mean, SSP2-4.5 AIS 2300 (fixed)", "46", "int", lambda v: lev("ssp245", v), "A+B"),
 ("2.2.3", "  as % of the SSP2-4.5 total", "17", "int", lambda v: lev("ssp245", v, True), "A+B"),
 ("2.2.3", "amp leverage, SSP5-8.5 AIS 2300 (fixed)", "20", "int", lambda v: lev("ssp585", v), "A+B"),
 ("2.2.3", "  as % of the SSP5-8.5 total", "4", "int", lambda v: lev("ssp585", v, True), "A+B"),
 ("2.2.3", "1.196 reversion, SSP2-4.5 total 2100 (fixed)", "15", "int",
  lambda v: panel("L27aisamp1p196", "ssp245", "total", 2100, v) - panel("L27", "ssp245", "total", 2100, v), "A+B"),
 ("2.2.3", "1.196 reversion, SSP2-4.5 total 2300", "32", "int",
  lambda v: panel("L27aisamp1p196", "ssp245", "total", 2300, v) - panel("L27", "ssp245", "total", 2300, v), "A+B"),
 ("2.2.3", "1.196 reversion, SSP5-8.5 total 2100", "6", "int",
  lambda v: panel("L27aisamp1p196", "ssp585", "total", 2100, v) - panel("L27", "ssp585", "total", 2100, v), "A+B"),
 ("2.2.3", "1.196 reversion, SSP5-8.5 total 2300", "13", "int",
  lambda v: panel("L27aisamp1p196", "ssp585", "total", 2300, v) - panel("L27", "ssp585", "total", 2300, v), "A+B"),
 ("3.1", "AIS 1979-2023 vs IMBIE, z (Ladrillo postpred)", "-2.6", "1dp", lambda v: imbie("z_ladrillo_vs_imbie", v), "PP"),
 ("3.1", "AIS 1979-2023 Ladrillo - IMBIE (cm)", "-0.38", "2dp",
  lambda v: imbie("ladrillo_cm", v) - imbie("imbie_cm", v), "PP"),
 ("3.2", "refit precision: max |AIS med L27r - L27| over 5 fixed-panel cells (cm)", "1.3", "1dp", refit_proj, "A+B"),
 ("3.2", "refit precision: hindcast max |RMSE L27r - L27| (cm, rounded up)", "0.005", "3up", refit_hind, "PP"),
 ("4.1 Table 4", "AIS RMSE ratio 1993-2025", "1.077", "3dp", lambda v: score("1993-2025", "AIS", v), "PP"),
 ("4.1 Table 4", "AIS RMSE ratio full", "0.059", "3dp", lambda v: score("full", "AIS", v), "PP"),
 ("4.1 Table 4", "Total RMSE ratio 1993-2025", "0.677", "3dp", lambda v: score("1993-2025", "TOTAL", v), "PP"),
 ("4.1 Table 4", "Total RMSE ratio full", "0.546", "3dp", lambda v: score("full", "TOTAL", v), "PP"),
 ("4.1", "AIS RMSE 1993-2025, Ladrillo (cm; 'within 0.1 cm')", "<0.1", "3dp",
  lambda v: score_rmse("1993-2025", "AIS", "Ladrillo", v), "PP"),
 ("4.1", "Ladrillo cumulative rise, mean 2020-24 minus mean 1900-04 (cm)", "20.41", "2dp",
  lambda v: pp_mean("total_p50", 2020, 2024, v) - pp_mean("total_p50", 1900, 1904, v), "PP"),
 ("4.1", "Ladrillo level, mean 2022-24 (cm)", "7.88", "2dp", lambda v: pp_mean("total_p50", 2022, 2024, v), "PP"),
 ("4.3 High", "Ladrillo total 2100", "71", "int", lambda v: cells(LAD("vvH"), "total", 2100, v), "A+B"),
 ("4.3 High", "BRICK 2.0 total 2100", "82", "int", lambda v: cells(BRK("vvH"), "total", 2100, v), "B"),
 ("4.3 High", "Ladrillo total 2300", "422", "int", lambda v: cells(LAD("vvH"), "total", 2300, v), "A+B"),
 ("4.3 High", "BRICK 2.0 total 2300", "414", "int", lambda v: cells(BRK("vvH"), "total", 2300, v), "B"),
 ("4.3 High", "Ladrillo AIS 2300", "244", "int", lambda v: cells(LAD("vvH"), "ais", 2300, v), "A+B"),
 ("4.3 High", "BRICK 2.0 AIS 2300", "248", "int", lambda v: cells(BRK("vvH"), "ais", 2300, v), "B"),
 ("4.3 High", "Ladrillo on MAGICC climate, total 2300", "407", "int", lambda v: cells(LADM("vvH"), "total", 2300, v), "A+B"),
 ("4.3 High", "BRICK 2.0 on MAGICC climate, total 2300", "392", "int", lambda v: cells(BRKM("vvH"), "total", 2300, v), "B"),
 ("4.3 High", "climate swap decrease, Ladrillo (cm)", "15", "int",
  lambda v: cells(LAD("vvH"), "total", 2300, v) - cells(LADM("vvH"), "total", 2300, v), "A+B"),
 ("4.3 High", "climate swap decrease, BRICK 2.0 (cm)", "22", "int",
  lambda v: cells(BRK("vvH"), "total", 2300, v) - cells(BRKM("vvH"), "total", 2300, v), "B"),
 ("4.3 High", "AIS 5-95% width 2300, Ladrillo", "274", "int", lambda v: width(LAD("vvH"), "ais", 2300, v), "A+B"),
 ("4.3 High", "AIS 5-95% width 2300, BRICK 2.0", "332", "int", lambda v: width(BRK("vvH"), "ais", 2300, v), "B"),
 ("4.3 Low", "Very Low total 2300, Ladrillo", "60", "int", lambda v: cells(LAD("vvVL"), "total", 2300, v), "A+B"),
 ("4.3 Low", "Very Low total 2300, BRICK 2.0", "81", "int", lambda v: cells(BRK("vvVL"), "total", 2300, v), "B"),
 ("4.3 Low", "Very Low total 2300 width, Ladrillo", "137", "int", lambda v: width(LAD("vvVL"), "total", 2300, v), "A+B"),
 ("4.3 Low", "Very Low total 2300 width, BRICK 2.0", "182", "int", lambda v: width(BRK("vvVL"), "total", 2300, v), "B"),
 ("Concl.", "'up to 31 cm': BRICK 2.0 - Ladrillo AIS, SSP2-4.5 2300", "31", "int", lambda v: ais_gap("ssp245", v), "A+B"),
 ("Concl.", "  the same, High-to-Low (the second-largest)", "(2nd)", "int", lambda v: ais_gap("vvHL", v), "A+B"),
 ("Concl.", "  max over the 3 SSPs and 7 vv markers", "31", "int",
  lambda v: max(ais_gap(s, v) for s in ["ssp126", "ssp245", "ssp585", "vvVL", "vvL", "vvLN", "vvML", "vvM", "vvHL", "vvH"]), "A+B"),
]

## ---- run -----------------------------------------------------------------------------------------------------------
rows = []
for where, q, printed, f, fn, exp in ROWS:
    try:
        o, n = fn("v1.0"), fn("v1.1")
    except Exception as e:                          # a missing producer must be visible, not silently skipped
        rows.append(dict(where=where, quantity=q, printed=printed, v10=np.nan, v11=np.nan, delta=np.nan,
                         v10_text="ERROR", v11_text=f"ERROR: {type(e).__name__}: {e}"[:120], exposure=exp, changes=""))
        continue
    t0, t1 = fmt[f](o), fmt[f](n)
    rows.append(dict(where=where, quantity=q, printed=printed, v10=o, v11=n, delta=n - o, v10_text=t0, v11_text=t1,
                     exposure=exp, changes=("PRINT->v1.1" if printed.lstrip("-") .replace(".", "", 1).isdigit()
                                            and t1 != printed else "") + (" v1.0->v1.1" if t0 != t1 else "")))
df = pd.DataFrame(rows)
commit = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
df["provenance"] = (f"v11_paper_number_diff.py | SLR-RFF-BRICK {commit} | v1.0 = {os.path.relpath(Q, REPO)} (else canonical, "
                    f"unchanged) | v1.1 = outputs/ canonical | Ladrillo L27, FaIR 2.2.4 (calib 1.6.0) CMIP7 basis, joint "
                    f"arm unless the quantity says fixed | cm rel 1995-2014 | {datetime.date.today()}")
df.to_csv(OUT, index=False)
print("| where | quantity | printed | v1.0 file | v1.1 | Δ (v1.1 − v1.0) | exposure | changes |")
print("|---|---|---|---|---|---|---|---|")
for r in df.itertuples():
    print(f"| {r.where} | {r.quantity} | {r.printed} | {r.v10_text} | {r.v11_text} | "
          f"{'' if pd.isna(r.delta) else f'{r.delta:+.3f}'} | {r.exposure} | {r.changes} |")
print("wrote", os.path.relpath(OUT, REPO))
