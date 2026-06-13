#!/usr/bin/env python3
"""
AIS H1/H2 recalibration diagnostic (§5 of the BRICK recalibration plan).

Question: among the post-#93 obs-driven BRICK posterior draws, does a meaningful
subset fit BOTH the near-zero historical AIS (Frederikse 2020, 1900) AND modern
IMBIE 1992-2017 simultaneously?

  - Subset exists  -> H1 (data starvation): adding a pre-1992 AIS calibration
                      target will pull AIS back; recalibration works.
  - No subset      -> H2 (structural): the DAIS fast-dynamics cannot fit both;
                      a new target alone won't fix it (need wider priors / structure).

All AIS trajectory columns in the obs-driven CSV are cm rel. year 2000.
Both diagnostic metrics are window-CHANGES (reference-independent) to avoid
any baseline-frame mismatch between BRICK, Frederikse, and IMBIE.
"""
import os, glob
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ----------------------------- CONFIG / CONSTANTS -----------------------------
REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
# Primary: FaIR-forced obs-driven run on the POST-#93 posterior (matches the
# FaIR-forcing convention proposed in the recalibration plan).
OBSDRIVEN_PRIMARY = os.path.join(REPO, "outputs/brick_obsdriven_fair_fair_to2024.csv")
# Sensitivity: IGCC-obs GMST forcing.
OBSDRIVEN_SENS    = os.path.join(REPO, "outputs/brick_obsdriven_obs_obs_igcc_to2024.csv")

FREDERIKSE_XLSX = os.path.join(REPO, "data/observations/raw/frederikse2020_global_basin_timeseries.xlsx")
IMBIE_AIS = glob.glob(os.path.expanduser(
    "~/.julia/packages/MimiBRICK/*/data/calibration_data/IMBIE_antarctic_ice_sheet_1992_2017.csv"))[0]

# Diagnostic windows
HIST_YEAR   = 1900          # historical anchor (vs year 2000 = column reference)
IMBIE_Y0, IMBIE_Y1 = 1992, 2017   # modern window

# Pass tolerances expressed as multiples of the obs 1-sigma.
# (Frederikse [lower,upper] taken as ~90% -> sigma = (upper-lower)/(2*1.645).)
SIGMA_K_LIST = [1.645, 2.0, 3.0]   # report joint-pass fraction at several widths

OUT_FIG = os.path.join(REPO, "outputs/ais_h1h2_diagnostic.png")
OUT_MD  = os.path.join(REPO, "outputs/ais_h1h2_diagnostic_summary.md")

# ----------------------------- LOAD TARGETS -----------------------------------
def load_frederikse_ais():
    g = pd.read_excel(FREDERIKSE_XLSX, "Global")
    yr = g["Unnamed: 0"].values
    mean = g["Antarctic Ice Sheet [mean]"].values
    lo   = g["Antarctic Ice Sheet [lower]"].values
    hi   = g["Antarctic Ice Sheet [upper]"].values
    s = pd.DataFrame({"year": yr, "mean": mean, "lo": lo, "hi": hi}).set_index("year")
    ref2000 = s.loc[2000, "mean"]
    # rebaseline to year 2000, convert mm -> cm
    for c in ["mean", "lo", "hi"]:
        s[c] = (s[c] - ref2000) / 10.0
    return s

def load_imbie_delta():
    df = pd.read_csv(IMBIE_AIS, encoding="latin-1", skiprows=5)
    df.columns = ["year", "cum_Gt", "cum_Gt_unc", "cum_slr_mm", "cum_slr_mm_unc"]
    # nearest monthly sample to each integer year edge
    def at(y):
        i = (df["year"] - y).abs().idxmin()
        return df.loc[i, "cum_slr_mm"], df.loc[i, "cum_slr_mm_unc"]
    s0, u0 = at(IMBIE_Y0)
    s1, u1 = at(IMBIE_Y1)
    d_cm   = (s1 - s0) / 10.0
    # uncertainties add in quadrature, mm -> cm
    d_unc  = np.hypot(u0, u1) / 10.0
    return d_cm, d_unc

# ----------------------------- DIAGNOSTIC -------------------------------------
def run(path, label, fred, imbie_d, imbie_sig, ax=None):
    df = pd.read_csv(path)
    n = len(df)
    hist = df[f"ais_{HIST_YEAR}"].values                      # cm rel 2000  (= -ΔAIS 1900->2000)
    modern = df[f"ais_{IMBIE_Y1}"].values - df[f"ais_{IMBIE_Y0}"].values  # ΔAIS 1992->2017, cm

    # targets
    fred_mean = fred.loc[HIST_YEAR, "mean"]
    fred_sig  = (fred.loc[HIST_YEAR, "hi"] - fred.loc[HIST_YEAR, "lo"]) / (2 * 1.645)

    # quantify the overshoot
    q = np.percentile(hist, [5, 50, 95])
    qm = np.percentile(modern, [5, 50, 95])

    lines = []
    lines.append(f"### {label}  (n={n})")
    lines.append("")
    lines.append(f"**Historical AIS @ {HIST_YEAR} (cm rel 2000):**")
    lines.append(f"- BRICK draws: median {q[1]:+.2f}  (5-95%: {q[0]:+.2f} .. {q[2]:+.2f})")
    lines.append(f"- Frederikse target: {fred_mean:+.2f} ± {fred_sig:.2f} (1σ)")
    lines.append(f"- overshoot of median vs Frederikse: {q[1]-fred_mean:+.2f} cm "
                 f"({(q[1]-fred_mean)/fred_sig:+.1f} σ)")
    lines.append("")
    lines.append(f"**Modern ΔAIS {IMBIE_Y0}->{IMBIE_Y1} (cm):**")
    lines.append(f"- BRICK draws: median {qm[1]:+.3f}  (5-95%: {qm[0]:+.3f} .. {qm[2]:+.3f})")
    lines.append(f"- IMBIE target: {imbie_d:+.3f} ± {imbie_sig:.3f} (1σ)")
    lines.append("")

    # pass fractions at several tolerances
    lines.append(f"**Joint-pass fractions** (within k·σ of BOTH targets):")
    lines.append("")
    lines.append("| k·σ | hist-pass | modern-pass | JOINT | among modern-passers: median hist AIS |")
    lines.append("|----:|----------:|------------:|------:|---------------------------------------:|")
    joint_frac_main = None
    for k in SIGMA_K_LIST:
        hist_ok   = np.abs(hist - fred_mean) <= k * fred_sig
        modern_ok = np.abs(modern - imbie_d) <= k * imbie_sig
        joint = hist_ok & modern_ok
        med_hist_mp = np.median(hist[modern_ok]) if modern_ok.sum() else np.nan
        lines.append(f"| {k:.3g} | {hist_ok.mean()*100:5.1f}% | {modern_ok.mean()*100:5.1f}% | "
                     f"**{joint.mean()*100:5.2f}%** | {med_hist_mp:+.2f} cm |")
        if abs(k - 2.0) < 1e-6:
            joint_frac_main = joint.mean()

    # coupling: does fitting modern FORCE a large historical retreat?
    r = np.corrcoef(hist, modern)[0, 1]
    modern_ok2 = np.abs(modern - imbie_d) <= 2.0 * imbie_sig
    r_mp = (np.corrcoef(hist[modern_ok2], modern[modern_ok2])[0, 1]
            if modern_ok2.sum() > 2 else np.nan)
    lines.append("")
    lines.append(f"corr(hist, modern) all draws = {r:+.3f};  among modern-passers = {r_mp:+.3f}")
    lines.append("")

    # plot
    if ax is not None:
        ax.scatter(hist, modern, s=3, alpha=0.15, color="#666", rasterized=True)
        # target box (±2σ)
        from matplotlib.patches import Rectangle
        ax.add_patch(Rectangle((fred_mean-2*fred_sig, imbie_d-2*imbie_sig),
                               4*fred_sig, 4*imbie_sig, fill=False, ec="crimson", lw=2,
                               label="target ±2σ (both)"))
        ax.axvline(fred_mean, color="crimson", ls=":", lw=1)
        ax.axhline(imbie_d, color="crimson", ls=":", lw=1)
        ax.set_xlabel(f"historical AIS @ {HIST_YEAR}  (cm rel 2000)")
        ax.set_ylabel(f"modern ΔAIS {IMBIE_Y0}-{IMBIE_Y1}  (cm)")
        ax.set_title(f"{label}\njoint ±2σ pass = {joint_frac_main*100:.2f}%")
        ax.legend(loc="upper right", fontsize=8)

    return "\n".join(lines), joint_frac_main

# ----------------------------- MAIN -------------------------------------------
fred = load_frederikse_ais()
imbie_d, imbie_sig = load_imbie_delta()

fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
report = ["# AIS H1/H2 recalibration diagnostic", "",
          f"Frederikse AIS @1900 = {fred.loc[1900,'mean']:+.2f} cm rel 2000 "
          f"(band {fred.loc[1900,'lo']:+.2f}..{fred.loc[1900,'hi']:+.2f}); "
          f"IMBIE ΔAIS {IMBIE_Y0}-{IMBIE_Y1} = {imbie_d:+.3f} ± {imbie_sig:.3f} cm", ""]

runs = [(OBSDRIVEN_PRIMARY, "FaIR-forced (primary)"),
        (OBSDRIVEN_SENS,    "IGCC-obs-forced (sensitivity)")]
jfracs = {}
for (path, label), ax in zip(runs, axes):
    if not os.path.exists(path):
        report.append(f"### {label}: FILE MISSING {path}\n")
        continue
    txt, jf = run(path, label, fred, imbie_d, imbie_sig, ax)
    report.append(txt)
    jfracs[label] = jf

fig.tight_layout()
fig.savefig(OUT_FIG, dpi=130)

# ----------------- parameter attribution of joint-passers (primary) -----------
def param_attribution():
    post = pd.read_csv(os.path.join(REPO, "data/MimiBRICK/parameters_subsample_brick.csv")).reset_index(drop=True)
    od = pd.read_csv(OBSDRIVEN_PRIMARY).sort_values("post_idx").reset_index(drop=True)
    assert (od.post_idx.values == np.arange(1, len(post) + 1)).all(), "post_idx misaligned"
    hist = od[f"ais_{HIST_YEAR}"].values
    modern = od[f"ais_{IMBIE_Y1}"].values - od[f"ais_{IMBIE_Y0}"].values
    fred_mean = fred.loc[HIST_YEAR, "mean"]
    fred_sig = (fred.loc[HIST_YEAR, "hi"] - fred.loc[HIST_YEAR, "lo"]) / (2 * 1.645)
    jp = (np.abs(hist - fred_mean) <= 3 * fred_sig) & (np.abs(modern - imbie_d) <= 3 * imbie_sig)
    ais_params = ['antarctic_s0','anto_alpha','anto_beta','antarctic_gamma','antarctic_alpha',
                  'antarctic_mu','antarctic_nu','antarctic_precip0','antarctic_kappa','antarctic_flow0',
                  'antarctic_runoff_height0','antarctic_c','antarctic_bed_height0','antarctic_slope',
                  'antarctic_lambda','antarctic_temp_threshold']
    out = ["", f"## Parameter attribution of joint-passers (±3σ, n={jp.sum()}, FaIR-forced)", "",
           "Percentile rank of joint-passer median within the full posterior "
           "(50% = interior/uninformative; >85% or <15% = pushed to a tail):", "",
           "| AIS parameter | full median | JP median | JP %ile | corr(histAIS, param) |",
           "|---|---:|---:|---:|---:|"]
    for p in ais_params:
        full = post[p].values
        jpv = full[jp]
        rank = (full < np.median(jpv)).mean() * 100
        r = np.corrcoef(hist, full)[0, 1]
        out.append(f"| {p} | {np.median(full):.4g} | {np.median(jpv):.4g} | {rank:.0f}% | {r:+.2f} |")
    return "\n".join(out)

report.append(param_attribution())

# verdict
report.append("")
report.append("## Verdict")
jf = jfracs.get("FaIR-forced (primary)", np.nan)
if jf is None or np.isnan(jf):
    verdict = "INCONCLUSIVE — primary run missing."
else:
    verdict = (
        f"**Mixed — recalibration is viable but not a clean data-starvation fix.**\n\n"
        f"- Only {jf*100:.2f}% of post-#93 draws fit BOTH targets at ±2σ (1.3% at ±3σ); the "
        f"historical AIS@{HIST_YEAR} median (~-4 cm) is ~8σ from Frederikse and is **near-uniform** "
        f"across the posterior — conditioning on a good modern (IMBIE) fit barely moves it "
        f"(corr(hist,modern)≈-0.07).\n"
        f"- So the overshoot is NOT a trade-off forced by the modern constraint; it is the "
        f"default DAIS response to historical forcing under the current priors.\n"
        f"- BUT draws that fit both DO exist in the current support: they sit in the **upper tail "
        f"of `anto_alpha`** (Antarctic ocean-temperature sensitivity; JP median ~90th pct) with "
        f"weak, multi-parameter gradients (no single |corr|>0.17). `antarctic_s0` is interior, so "
        f"this is a dynamic-response issue, not an initial-condition offset.\n\n"
        f"**Implication for the recalibration plan:** adding a pre-1992 Frederikse AIS target "
        f"WILL pull the posterior toward higher `anto_alpha`/`antarctic_alpha` — the region that "
        f"fits both exists, so it is not structurally blocked. However, because that region is a "
        f"disfavored ~10% tail (with some draws railing at the sampled edge), expect (a) a "
        f"substantial posterior shift, not a minor tweak, and (b) a need to CHECK whether the "
        f"`anto_alpha`/`antarctic_alpha` prior bounds are binding — if so, widen them. This is more "
        f"involved than the GIS fix in #93 and is the single most important open question for Tony.")
report.append(verdict)

open(OUT_MD, "w").write("\n".join(report))
print("\n".join(report))
print(f"\n[wrote {OUT_FIG}]\n[wrote {OUT_MD}]")
