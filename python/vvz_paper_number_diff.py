#!/usr/bin/env python3
"""
vvz_paper_number_diff.py -- what the 2026-10-08 rerun moves: van Vuuren on the PUBLISHED emissions (variant b) + record
conditioning of Ladrillo's FaIR joint arms. OLD = before this rerun (Ladrillo v1.1 as shipped 10-08), NEW = canonical.

    python python/vvz_paper_number_diff.py
Writes outputs/vvz_paper_number_diff_20261008.csv (+ provenance) and prints a markdown table.

OLD sources (each the pre-rerun bytes):
  Ladrillo / BRICK 2.0 arms   outputs/quarantine/20261008_vv_zenodo_conditioning_arms/outputs/<f> (else canonical:
                              the prune found it unchanged)
  MAGICC-SLR own vv run       outputs/quarantine/20261008_vv_harmonized_tail_cubes/data_comparison/
  FACTS                       facts/quarantine/20261008_vv_harmonized_tail/
PRINTED is the number in the GMD draft as last edited (the 10-08 v1.1 round, notes/ladrillo_v11_paper_number_diff_2026-10-08.md),
where it is quoted; "-" where the quantity is not printed. Units cm rel 1995-2014 except FACTS (cm rel 2005, its own).
Exposure: V = van Vuuren emissions; C = record conditioning (Ladrillo FaIR joint arms only).
"""
import os, subprocess, datetime, math
import numpy as np, pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACTS_REPO = os.path.join(os.path.dirname(REPO), "facts")
Q = os.path.join(REPO, "outputs/quarantine/20261008_vv_zenodo_conditioning_arms/outputs")
QC = os.path.join(REPO, "outputs/quarantine/20261008_vv_harmonized_tail_cubes/data_comparison")
QF = os.path.join(FACTS_REPO, "quarantine/20261008_vv_harmonized_tail")
OUT = os.path.join(REPO, "outputs/vvz_paper_number_diff_20261008.csv")
TAP = "_tap4p69K_V5p64m_tau800"
VV = ["vvVL", "vvLN", "vvL", "vvML", "vvM", "vvHL", "vvH"]
SSPS = ["ssp126", "ssp245", "ssp585"]
FACTS_TOTAL_WF = "wf1f"                       # FACTS's default workflow for the total
_c = {}


def rd(path):
    if path not in _c:
        _c[path] = pd.read_csv(path, float_precision="round_trip")
    return _c[path]


def out_path(f, ver):
    q, c = os.path.join(Q, f), os.path.join(REPO, "outputs", f)
    return (q if os.path.exists(q) else c) if ver == "old" else c


def cells(f, comp, H, ver, stat="med_cm", arm="joint"):
    d = rd(out_path(f, ver)); r = d[(d.component == comp) & (d.horizon == H) & (d.arm == arm)]
    assert len(r) == 1, (f, comp, H, arm, len(r)); return float(r[stat].iloc[0])


def width(f, comp, H, ver): return cells(f, comp, H, ver, "p95_cm") - cells(f, comp, H, ver, "p05_cm")


LAD = lambda s: f"scope_slr_fairunc_cells_{s}_spliced_L27{TAP}.csv"
LADM = lambda s: f"scope_slr_fairunc_cells_{s}_spliced_magiccclim_L27{TAP}.csv"
BRK = lambda s: f"scope_slr_fairunc_cells_{s}_spliced_oldbrick.csv"
BRKM = lambda s: f"scope_slr_fairunc_cells_{s}_spliced_oldbrick_magiccclim.csv"


def magicc(scen, comp, year, ver):
    p = os.path.join(QC if ver == "old" else os.path.join(REPO, "data/comparison"), "magicc_nauels_components_vv.csv")
    d = rd(p); r = d[(d.scenario == scen) & (d.component == comp) & (d.year == year)]
    assert len(r) == 1, (scen, comp, year, len(r)); return float(r.med.iloc[0])


def facts(scen, comp, module, year, ver, stat="med"):
    p = os.path.join(QF if ver == "old" else os.path.join(REPO, "outputs"), "facts_components_shared_n200.csv")
    d = rd(p); r = d[(d.scenario == scen) & (d.component == comp) & (d.module == module) & (d.year == year)]
    assert len(r) == 1, (scen, comp, module, year, len(r)); return float(r[stat].iloc[0])


def receipt(arm, ver):
    f = "diag_facts_gis_extrap_receipt_vvHL2300.csv"
    p = os.path.join(QF, f) if ver == "old" else os.path.join(REPO, "outputs", f)
    d = rd(p); r = d[(d.arm == arm) & (d.horizon == 2300)]
    assert len(r) == 1, (arm, len(r)); return float(r.p50.iloc[0])


def ais_gap(s, v): return cells(BRK(s), "ais", 2300, v) - cells(LAD(s), "ais", 2300, v)


ROWS = []   # (where, quantity, printed, fmt, fn(ver), exposure)
for s in SSPS:
    for comp in ("ais", "total"):
        for H in (2100, 2300):
            ROWS.append(("SSP joint", f"Ladrillo {s} {comp} {H} median", "-", "1dp",
                         (lambda s=s, c=comp, H=H: lambda v: cells(LAD(s), c, H, v))(), "C"))
    ROWS.append(("SSP joint", f"Ladrillo {s} total 2300 5-95% width", "-", "1dp",
                 (lambda s=s: lambda v: width(LAD(s), "total", 2300, v))(), "C"))
for m in VV:
    for H in (2100, 2300):
        ROWS.append(("4.2-4.3", f"Ladrillo {m} total {H}", "-", "int", (lambda m=m, H=H: lambda v: cells(LAD(m), "total", H, v))(), "V+C"))
        ROWS.append(("4.2-4.3", f"BRICK 2.0 {m} total {H}", "-", "int", (lambda m=m, H=H: lambda v: cells(BRK(m), "total", H, v))(), "V"))
        ROWS.append(("4.2-4.3", f"MAGICC-SLR {m} total {H} (own climate)", "-", "1dp", (lambda m=m, H=H: lambda v: magicc(m, "total", H, v))(), "V"))
        ROWS.append(("4.2-4.3", f"FACTS {m} total {H} ({FACTS_TOTAL_WF}; cm rel 2005)", "-", "int",
                     (lambda m=m, H=H: lambda v: facts(m, "total", FACTS_TOTAL_WF, H, v))(), "V"))
    ROWS.append(("4.2-4.3", f"Ladrillo {m} AIS 2300", "-", "int", (lambda m=m: lambda v: cells(LAD(m), "ais", 2300, v))(), "V+C"))
    ROWS.append(("4.2-4.3", f"BRICK 2.0 {m} AIS 2300", "-", "int", (lambda m=m: lambda v: cells(BRK(m), "ais", 2300, v))(), "V"))
ROWS += [
    ("4.3 High", "Ladrillo on MAGICC climate, vvH total 2300", "407", "int", lambda v: cells(LADM("vvH"), "total", 2300, v), "V+MAGICC"),
    ("4.3 High", "BRICK 2.0 on MAGICC climate, vvH total 2300", "392", "int", lambda v: cells(BRKM("vvH"), "total", 2300, v), "V+MAGICC"),
    ("4.3 High", "AIS 5-95% width 2300, Ladrillo vvH", "274", "int", lambda v: width(LAD("vvH"), "ais", 2300, v), "V+C"),
    ("4.3 High", "AIS 5-95% width 2300, BRICK 2.0 vvH", "332", "int", lambda v: width(BRK("vvH"), "ais", 2300, v), "V"),
    ("4.3 Low", "Very Low total 2300 width, Ladrillo", "163", "int", lambda v: width(LAD("vvVL"), "total", 2300, v), "V+C"),
    ("4.3 Low", "Very Low total 2300 width, BRICK 2.0", "-", "int", lambda v: width(BRK("vvVL"), "total", 2300, v), "V"),
    ("Concl.", "'up to N cm': BRICK 2.0 - Ladrillo AIS, max over 3 SSPs + 7 vv, 2300", "30", "int",
     lambda v: max(ais_gap(s, v) for s in SSPS + VV), "V+C"),
    ("FACTS", "FittedISMIP Greenland vvHL 2300, default extrapolation (cm rel 2005)", "47", "int",
     lambda v: facts("vvHL", "gis", "FittedISMIP", 2300, v), "V"),
    ("FACTS", "FittedISMIP Greenland vvHL 2300, fit evaluated to 2300 (receipt)", "112", "int", lambda v: receipt("fit2300", v), "V"),
]
fmt = {"int": lambda x: f"{x:.0f}", "1dp": lambda x: f"{x:.1f}"}

rows = []
for where, q, printed, f, fn, exp in ROWS:
    try:
        o, n = fn("old"), fn("new")
    except Exception as e:                      # a missing producer must be visible, not silently skipped
        rows.append(dict(where=where, quantity=q, printed=printed, old=np.nan, new=np.nan, delta=np.nan,
                         old_text="ERROR", new_text=f"ERROR: {type(e).__name__}: {e}"[:140], exposure=exp, changes=""))
        continue
    t0, t1 = fmt[f](o), fmt[f](n)
    rows.append(dict(where=where, quantity=q, printed=printed, old=o, new=n, delta=n - o, old_text=t0, new_text=t1,
                     exposure=exp, changes=("PRINT->new " if printed.replace(".", "", 1).isdigit() and t1 != printed else "")
                     + ("old->new" if t0 != t1 else "")))
df = pd.DataFrame(rows)
commit = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
df["provenance"] = (f"vvz_paper_number_diff.py | SLR-RFF-BRICK {commit} | old = {os.path.relpath(Q, REPO)} (else canonical), "
                    f"{os.path.relpath(QC, REPO)}, facts/{os.path.relpath(QF, FACTS_REPO)} | new = canonical | Ladrillo L27 "
                    f"v1.1 + record conditioning, FaIR 2.2.4 (calib 1.6.0), vv on the published Zenodo v1.1.1 emissions | "
                    f"{datetime.date.today()}")
df.to_csv(OUT, index=False)
print("| where | quantity | printed | old | new | Δ | exposure | changes |")
print("|---|---|---|---|---|---|---|---|")
for r in df.itertuples():
    print(f"| {r.where} | {r.quantity} | {r.printed} | {r.old_text} | {r.new_text} | "
          f"{'' if pd.isna(r.delta) else f'{r.delta:+.2f}'} | {r.exposure} | {r.changes} |")
print("wrote", os.path.relpath(OUT, REPO))
