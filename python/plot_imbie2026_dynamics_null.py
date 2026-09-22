"""
plot_imbie2026_dynamics_null.py -- candidate appendix figure for the IMBIE 2026 out-of-sample test.

Panel A  the reconciled record's own decomposition: the 2018-23 slowdown in the Antarctic TOTAL is
         surface mass balance; the dynamics anomaly accelerates straight through it.
Panel B  Ladrillo's dynamics misfit against that record, with and without the additional discharge
         response -- the response closes the late windows, and the level channel still rejects it.

House palette note: the paper's existing figures use #1b7837 green alongside #b2182b red. That pair is
OKLab dE 2.7 under deuteranopia (indistinguishable). This figure uses blue / red / grey only, whose
worst CVD separation across all pairs is 12.8.

  python python/plot_imbie2026_dynamics_null.py [--tag=L30]
Writes figures/diag_imbie2026_dynamics_null_<tag>.png
"""
import os, sys, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = next((a.split("=")[1] for a in sys.argv[1:] if a.startswith("--tag=")), "L30")

# ---- named constants: every label below derives from these -------------------------------------
IMBIE_FILE   = os.path.join(REPO, "data/observations/raw/imbie2026/imbie3_antarctica_Gt_partitioned.csv")
PROFILE_FILE = os.path.join(REPO, "outputs", "diag_ais_dynamics_channel_profile_%s.csv" % TAG)
SHIPPED_TAG  = "L27"                                  # the posterior the paper ships
SHIPPED_FILE = os.path.join(REPO, "outputs", "diag_ais_dynamics_channel_profile_%s.csv" % SHIPPED_TAG)
NDRAW_NOTE   = "100 posterior draws"                  # every number below is a mean over these
OUT          = os.path.join(REPO, "figures", "diag_imbie2026_dynamics_null_%s.png" % TAG)
WINDOWS      = [(1979, 1991), (1992, 2002), (2003, 2010), (2011, 2017), (2018, 2023)]
REF_WIN      = (1979, 2008)
IMBIE_CITE   = "IMBIE 2026 (Otosaka et al., Sci. Data 13:1301)"
UNITS        = "Gt yr$^{-1}$"
SIGN_NOTE    = "ice-mass sign: negative = loss"
RAMP_SHOWN   = [(0.60, 3.0e-4), (0.75, 6.0e-4)]      # cells drawn in panel B
# n = 100 draws, mean +- SE (CHANGELOG 09-22h; the 09-22f/g values were 3-5 draws and unstable)
LEVEL_DLL    = {3.0e-4: (-3.52, 0.60), 6.0e-4: (-10.62, 0.73)}
DYN_DLL_IND  = {3.0e-4: (+2.83, 0.44), 6.0e-4: (+1.83, 0.58)}

C_BLUE, C_RED, C_GREY = "#2166ac", "#b2182b", "#7f7f7f"
C_TOTAL, C_SMB, C_DYN = "#333333", C_BLUE, C_RED
DPI = 180

# ---- data ---------------------------------------------------------------------------------------
raw = pd.read_csv(IMBIE_FILE, comment="#")
raw["year"] = pd.to_datetime(raw["Date"]).dt.year
ann = raw.groupby("year").agg(
    mb=("Mass balance (Gt/yr)", "mean"),
    smb=("Surface mass balance anomaly (Gt/yr)", "mean"),
    smb_sig=("Surface mass balance anomaly uncertainty (Gt/yr)", "mean"),
    dyn=("Dynamics mass balance anomaly (Gt/yr)", "mean"),
    dyn_sig=("Dynamics mass balance anomaly uncertainty (Gt/yr)", "mean"),
    mb_sig=("Mass balance uncertainty (Gt/yr)", "mean")).reset_index()

def wmean(col):
    return np.array([ann.loc[(ann.year >= a) & (ann.year <= b), col].mean() for a, b in WINDOWS])
def wsig(col):
    return np.array([ann.loc[(ann.year >= a) & (ann.year <= b), col].mean() /
                     np.sqrt(((ann.year >= a) & (ann.year <= b)).sum()) for a, b in WINDOWS])

prof = pd.read_csv(PROFILE_FILE)
ship = pd.read_csv(SHIPPED_FILE)

# ---- figure -------------------------------------------------------------------------------------
fig, (axA, axB) = plt.subplots(1, 2, figsize=(12.6, 4.8))
edges = [WINDOWS[0][0]] + [b for _, b in WINDOWS]

def stepdraw(ax, y, color, label, lw=2.0, z=3):
    ax.step(edges, np.r_[y, y[-1]], where="post", color=color, lw=lw, label=label, zorder=z)

# ---- Panel A: the record decomposes -------------------------------------------------------------
for col, c, lab in ((\
    "mb", C_TOTAL, "total mass balance"), ("smb", C_SMB, "surface mass balance anomaly"),
    ("dyn", C_DYN, "dynamics anomaly")):
    y, s = wmean(col), wsig(col + "_sig" if col != "mb" else "mb_sig")
    stepdraw(axA, y, c, lab)
    mids = [(a + b) / 2 for a, b in WINDOWS]
    axA.errorbar(mids, y, yerr=s, fmt="none", ecolor=c, elinewidth=1.1, capsize=2.5, alpha=0.65, zorder=2)
axA.plot(ann.year, ann.dyn, color=C_DYN, lw=0.7, alpha=0.28, zorder=1)
axA.plot(ann.year, ann.smb, color=C_SMB, lw=0.7, alpha=0.28, zorder=1)
axA.axhline(0, color="#999999", lw=0.8, zorder=0)
axA.axvspan(2018, 2023, color="#000000", alpha=0.045, zorder=0)
axA.annotate("total slows\n(snowfall)", xy=(2020.5, -104), xytext=(2007, 245),
             fontsize=8.5, color=C_TOTAL, ha="center",
             arrowprops=dict(arrowstyle="->", color=C_TOTAL, lw=0.9, alpha=0.85))
axA.annotate("dynamics keeps\naccelerating", xy=(2020.2, -249), xytext=(2004, -385),
             fontsize=8.5, color=C_DYN, ha="center",
             arrowprops=dict(arrowstyle="->", color=C_DYN, lw=0.9, alpha=0.85))
axA.set_title("A.  The 2018–23 slowdown is surface mass balance", fontsize=10.5, loc="left")
axA.set_ylabel("Antarctic mass balance (%s)" % UNITS, fontsize=9.5)
axA.legend(loc="upper left", fontsize=8.2, frameon=False)
axA.set_ylim(-500, 560)

# ---- Panel B: the model's dynamics misfit -------------------------------------------------------
def misfit(gon, slope, df=None):
    df = prof if df is None else df
    sub = df[np.isclose(df.slope, slope)] if slope > 0 else df[df.slope == 0.0]
    if slope > 0:
        sub = sub[np.isclose(sub.G_on, gon)]
    return np.array([sub["win_%d_%d" % (a, b)].mean() for a, b in WINDOWS])

# Two baselines, separated by LINESTYLE rather than a fourth hue: the paper's palette has only three
# CVD-safe hues (its #1b7837 green is dE 2.7 from #b2182b under deuteranopia), and identity should
# not rest on colour alone in any case.
stepdraw(axB, misfit(np.nan, 0.0, ship), C_GREY,
         "Ladrillo v1.0 (%s, shipped)" % SHIPPED_TAG, lw=2.6)
axB.step(edges, np.r_[misfit(np.nan, 0.0), misfit(np.nan, 0.0)[-1]], where="post",
         color=C_GREY, lw=1.8, ls="--", zorder=3,
         label="refitted to the IMBIE level (%s)" % TAG)
for (gon, s), c, ls in zip(RAMP_SHOWN, (C_BLUE, C_RED), ("-", "-")):
    stepdraw(axB, misfit(gon, s), c, "+ discharge response, %.0f×10$^{-4}$ above %.2f K"
             % (s * 1e4, gon), lw=1.9)
axB.axhline(0, color="#333333", lw=1.2, zorder=2)
axB.axvspan(2018, 2023, color="#000000", alpha=0.045, zorder=0)
axB.text(2004.5, 2.5, "IMBIE dynamics anomaly (perfect fit)", fontsize=8, color="#333333", va="bottom")
axB.set_ylim(-52, 128)
axB.set_title("B.  Fitting the IMBIE level degrades the dynamics fit", fontsize=10.5, loc="left")
axB.set_ylabel("model − observed dynamics anomaly (%s)" % UNITS, fontsize=9.5)
axB.legend(loc="lower left", fontsize=8.2, frameon=False)
# the verdict, as text rather than a third panel
vtxt = "\n".join(["Δ log-likelihood from the response (%s):" % NDRAW_NOTE] +
                 ["  %.0f×10$^{-4}$:  dynamics %+.2f±%.2f,  level %+.2f±%.2f" %
                  (s * 1e4, DYN_DLL_IND[s][0], DYN_DLL_IND[s][1],
                   LEVEL_DLL[s][0], LEVEL_DLL[s][1]) for _, s in RAMP_SHOWN])
axB.text(0.015, 0.97, vtxt, transform=axB.transAxes, fontsize=8, va="top", ha="left",
         color="#333333", linespacing=1.45,
         bbox=dict(boxstyle="round,pad=0.42", fc="white", ec="#cccccc", lw=0.8))

for ax in (axA, axB):
    ax.set_xlim(WINDOWS[0][0], WINDOWS[-1][1])
    ax.set_xlabel("year", fontsize=9.5)
    ax.grid(axis="y", color="#dddddd", lw=0.6, zorder=0)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(labelsize=8.5)

fig.suptitle("Antarctic dynamics against %s — window means, reference %d–%d, %s; %s"
             % (IMBIE_CITE, REF_WIN[0], REF_WIN[1], SIGN_NOTE, NDRAW_NOTE), fontsize=9.5, y=0.995)
fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig(OUT, dpi=DPI)
print("wrote", OUT)
