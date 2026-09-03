#!/usr/bin/env python3
"""Glacier melt to 2300 under the seven van Vuuren CMIP7 markers: BRICK 2.0 (Wigley-Raper) vs Ladrillo L21.

The two models we actually ship, on one forcing set. Sibling of
plot_ssps_gsic_wr_vs_mengel.py, which draws the SSPs and still carries the plain-Mengel arms.

⚠ WHAT CHANGED 2026-08-31, AND WHY IT WAS NOT A RENAME.
This figure used to compare Wigley-Raper against "Mengel" -- meaning `glaciers_mengel`
(julia/glaciers_mengel_component.jl) on the `parameters_subsample_brick_mengel_extA108.csv`
posterior. THAT IS NOT LADRILLO. It is the single-reservoir Mengel-2016 emulator inside BRICK
(BRICK-AM), Ladrillo's PREDECESSOR on the glacier axis:

  extA108 plain Mengel                     Ladrillo L21 (this figure)
  ONE global reservoir pair (fast/slow)    THREE reservoirs: R19 / SLOWP / FAST
  S_eq = a(1-exp(-b(T - T_lia)))           S_eq,b = a_b(1-exp(-b_b(T_b - T_off_b))) per block
  fixed tau_fast / tau_slow, split by f    dS_b = min(kappa_b exc^nu_b, 1)(S_eq,b - S_b)
  driven by global GMST                    driven by per-block glacier-frame temperature
  posterior parameters_subsample_..._extA108   posterior = the L21 chains

So the arms differ in STRUCTURE, RATE LAW, DRIVER FRAME and POSTERIOR -- four axes, not a label.
Ladrillo's glacier module is the 3-reservoir Nauels-nu component (`glaciers_nu3`), built through
`build_brick_nu3*` (ladrillo_projection.jl:696) and read out as `gsic_r19/slowp/fast` (:832).
Mengel-2016 is the ancestor of the EQUILIBRIUM FORM only, so calling this arm "Mengel" would
misname the model in a figure whose whole point is which model is which.

The two extA108 arms (posterior b->0.89 and the b=0.52 counterfactual) are DROPPED here on
Marcus's call 2026-08-31: b->0.89 is a failed intermediate and b=0.52 is its counterfactual, both
properties of a calibration neither shipped model uses. Their van Vuuren outputs
(outputs/vv_gsic_2300_mengel{,_b052}.csv) are KEPT ON DISK as provenance, just not plotted.

VERSION NAMING. The Ladrillo arm is **L21** -- L14's config on the calib 1.6.0 + CMIP7 drivers,
champion since 2026-08-28, carrying its OWN chain set (outputs/mcmc/chain_L21_seed*_n2000000.csv),
NOT the parameters_subsample_brick_mengel_L14.csv thinning. ⚠ SLR@2100 = 45.01 cm is an L14 number
and stays labelled L14.

BOTH ARMS ARE POSTERIOR-PARAMETER SPREAD ON MEAN FORCING (the `fixed` arm), so their widths are
like-for-like. Ladrillo's `joint` arm exists in the same files and is DELIBERATELY not used here:
it carries FaIR climate uncertainty that the Wigley-Raper arm has no counterpart for, and mixing
the two would compare a climate+parameter band against a parameter-only one (`like_for_like_forcing`).

⚠ THE DRIVER IS THE SAME GMST, WITH A STATED MAPPING. Wigley-Raper takes the marker's mean GMST
directly. Ladrillo maps it to each block's glacier-frame temperature as `amp_b * GMST`, spliced to
preserve the observed mean over the last 11 observed years (ladrillo_projection.jl:740). So "the
same temperatures drive both" is true of the FORCING, not of the numbers each component sees, and
the caption says so rather than implying a raw common driver.

Reads outputs/vv_gsic_2300.csv (WR) and
      outputs/scope_slr_fairunc_paths_vv<M>_spliced_<L21 tap stem>.csv (Ladrillo).
"""
import os
import subprocess
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gis_targets  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

LADRILLO_TAG = next((a[len("--tag="):] for a in sys.argv[1:]
                     if a.startswith("--tag=")), "L21")
FORCING = "spliced"
ARM = "fixed"                    # see the like-for-like note in the docstring
WR_CSV = "outputs/vv_gsic_2300.csv"
LAD_PATHS = "outputs/scope_slr_fairunc_paths_{m}_%s_{stem}.csv" % FORCING
LAD_GATES = "outputs/scope_slr_fairunc_gates_{m}_%s_{stem}.csv" % FORCING
OUTPNG = "figures/vv_gsic_wr_vs_ladrillo_2300.png"

MARKERS = [
    ("Very Low",      "vvVL", "#00a9cf", True),
    ("Low-to-Neg",    "vvLN", "#1f78b4", True),
    ("Low",           "vvL",  "#003466", False),
    ("Medium-to-Low", "vvML", "#f69320", True),
    ("Medium",        "vvM",  "#c8a000", False),
    ("High-to-Low",   "vvHL", "#df0000", True),
    ("High",          "vvH",  "#7a0002", False),
]
LABELS = [m[0] for m in MARKERS]
KEY = {m[0]: m[1] for m in MARKERS}
COL = {m[0]: m[2] for m in MARKERS}
DECLINE = [m[0] for m in MARKERS if m[3]]
SPREAD_LO, SPREAD_HI = "Very Low", "High"
X0, X1 = 2000, 2300
WR_NAME = "BRICK 2.0 (Wigley–Raper)"
LAD_NAME = "Ladrillo %s (3-reservoir ν)" % LADRILLO_TAG



def _lf_gate_verdicts_ok():
    """The accepted gate verdicts, from ladrillo_figs so the set has ONE definition."""
    import os as _os, sys as _sys
    _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    import ladrillo_figs as _lf
    return _lf.GATE_VERDICTS_OK
def joint_stem(tag):
    """Mirrors `const TAP_TAG` in scope_slr_fair_uncertainty.jl (~:162) off the same
    GIS_TAP_CELL, so the two cannot drift. Shorter than gis_targets.tap_tag(): the joint
    driver omits the `_n<stages>_ws` suffix the shipped-panel name carries."""
    c = gis_targets.tap_cell()
    return (f"{tag}_tap{str(c['onset_K']).replace('.', 'p')}K"
            f"_V{str(c['V_m']).replace('.', 'p')}m_tau{int(c['tau_yr'])}")


STEM = joint_stem(LADRILLO_TAG)

## ---------------------------------------------------------------------------
## GATE 1 -- the WR arm's own forcing vintage. Its file carries a `gmst` column, so the
## forcing it was actually built on is checkable against the current fair_mean drivers.
## No invented tolerance, no mtime guessing. The row count is printed so a gate that
## matches nothing cannot report a pass.
if not os.path.exists(WR_CSV):
    raise SystemExit("missing %s -- produce it with\n"
                     "  julia --project=julia_v2 julia/project_ssps_gsic_2300.jl --set=vv" % WR_CSV)
WR = pd.read_csv(WR_CSV)
_worst, _n = 0.0, 0
for _lab, _g in WR.drop_duplicates(["ssp", "year"]).groupby("ssp"):
    _f = "data/observations/fair_mean_gmst_%s.csv" % KEY.get(_lab, "")
    if not os.path.exists(_f):
        continue
    _m = pd.read_csv(_f).set_index("year")["gmst_C"].reindex(_g.year.values).values
    _ok = ~np.isnan(_m)
    if _ok.any():
        _worst = max(_worst, float(np.nanmax(np.abs(_g.gmst.values[_ok] - _m[_ok]))))
        _n += int(_ok.sum())
if _n == 0:
    raise SystemExit("[VINTAGE] compared ZERO rows for the WR arm -- vacuous, not passing.")
## ⚠ ABSOLUTE, not a spread across arms. The SSP figure's gate compares its three arms
## against EACH OTHER and is therefore blind to all of them being stale together (found
## 2026-08-31 by mutation-testing: a mutation put 1.4074 K on every arm and it still
## passed -- `two_statistics_can_be_blind`). With only two arms here, and the Ladrillo one
## carrying no gmst column, the absolute check is the only one with any power.
if _worst > 1e-6:
    raise SystemExit(
        "[VINTAGE] the WR arm is stale against the current fair_mean drivers by %.4f K "
        "(%d rows), so 'the same GMST drives both' is FALSE:\n"
        "  Regenerate with --set=vv. Do NOT relax this gate." % (_worst, _n))
print("[VINTAGE] WR arm matches the current fair_mean drivers (delta %.4f K, %d rows)"
      % (_worst, _n))

## GATE 2 -- the Ladrillo arm has no gmst column, so its forcing is verified through the
## driver's OWN gates file instead. A MISSING gates file is a FAILURE, not a skip: an
## absent gate and a passing gate must not look the same. CONTROL is legitimately SKIPPED
## on every van Vuuren marker (no shipped panel row exists to compare against); a CONTROL
## verdict of CHECK or FAIL is still an error.
LAD = {}
for lab in LABELS:
    m = KEY[lab]
    gf = LAD_GATES.format(m=m, stem=STEM)
    pf = LAD_PATHS.format(m=m, stem=STEM)
    for f in (gf, pf):
        if not os.path.exists(f):
            raise SystemExit(
                "missing %s -- produce the Ladrillo van Vuuren arm with\n"
                "  julia --project=julia_v2 julia/scope_slr_fair_uncertainty.jl --ssp=%s "
                "--build-ssp=ssp245 --forcing=%s --tag=%s --tap" % (f, m, FORCING, LADRILLO_TAG))
    g = pd.read_csv(gf)
    bad = g[~g.verdict.isin(_lf_gate_verdicts_ok())]
    if len(bad):
        raise SystemExit("[GATE] %s: %d non-passing gate row(s):\n%s" % (m, len(bad), bad))
    if "CONTROL" not in set(g.gate):
        raise SystemExit("[GATE] %s: gates file has NO CONTROL row -- a gate that is absent "
                         "is not a gate that passed." % m)
    d = pd.read_csv(pf)
    d = d[(d.component == "glaciers") & (d.arm == ARM)].sort_values("year")
    if d.empty:
        raise SystemExit("[GATE] %s: no `glaciers`/`%s` rows in %s" % (m, ARM, pf))
    LAD[lab] = d.set_index("year")
_nc = int(pd.read_csv(LAD_GATES.format(m=KEY[LABELS[0]], stem=STEM))
          .query("gate=='PAIRING' and key=='configs_used'").value.iloc[0])
print("[GATE] all %d Ladrillo %s arms pass (arm=%s, %d configs, tap stem %s)"
      % (len(LABELS), LADRILLO_TAG, ARM, _nc, STEM))

## GATE 3 -- CROSS-MARKER PROVENANCE. All seven markers came from ONE run of
## build_fair_cube_vv_v160.py, so they must share a SINGLE driver commit. That is
## checkable without declaring anything and cannot rot the way the SSP figure's
## hand-typed _DRIVER_PROVENANCE table can -- which that figure needs only because its
## set genuinely straddles two calibrations.
_PROVENANCE_RULE = "all seven van Vuuren drivers share one commit (one build, one calibration)"
_actual = {lab: subprocess.run(
    ["git", "log", "-1", "--format=%h", "--",
     "data/observations/fair_mean_gmst_%s.csv" % KEY[lab]],
    capture_output=True, text=True).stdout.strip() for lab in LABELS}
_missing = sorted(l for l, v in _actual.items() if not v)
if _missing:
    raise SystemExit(
        "[PROVENANCE] git returned nothing for %d of %d driver(s), so the calibration is "
        "UNVERIFIED and this figure must not be drawn: %s\n"
        "  Run from inside the SLR-RFF-BRICK checkout, with the drivers committed."
        % (len(_missing), len(_actual), _missing))
_commits = sorted(set(_actual.values()))
if len(_commits) != 1:
    raise SystemExit(
        "[PROVENANCE] %s -- but %d commits are present, so the one-calibration claim is "
        "FALSE:\n%s\n  Rebuild the marker set in one run. Do NOT drop this gate."
        % (_PROVENANCE_RULE, len(_commits),
           "\n".join("    %-16s %s" % (l, c) for l, c in sorted(_actual.items()))))
_COMMIT = _commits[0]
print("[PROVENANCE] %s: %s (%d drivers verified)" % (_PROVENANCE_RULE, _COMMIT, len(_actual)))


def wr(lab):
    d = WR[WR.ssp == lab].sort_values("year")
    return d[d.year >= X0]


def lad(lab):
    d = LAD[lab]
    return d[d.index >= X0]


fig, ax = plt.subplots(4, 1, figsize=(8.6, 12.2), sharex=True,
                       gridspec_kw=dict(height_ratios=[0.85, 1.2, 1.2, 0.95], hspace=0.13))

# ---- (a) GMST forcing ----
for s in LABELS:
    d = wr(s)
    ax[0].plot(d.year.values, d.gmst.values, color=COL[s], lw=1.8, label=s)
ax[0].set_ylabel("GMST (°C rel. PI)")
ax[0].set_title("Glacier melt to 2300 — %s vs %s, seven van Vuuren CMIP7 markers"
                % (WR_NAME, LAD_NAME), fontsize=11, fontweight="bold", loc="left")
ax[0].legend(ncol=4, fontsize=7.5, frameon=False, loc="upper left")
_pk = {s: (wr(s).set_index("year").gmst.loc[2015:2300].idxmax(),
           wr(s).set_index("year").gmst.loc[2015:2300].max()) for s in DECLINE}
ax[0].annotate("%d peak-and-decline pathways\n(peaks %.2f–%.2f °C, %d–%d)"
               % (len(DECLINE), min(v for _, v in _pk.values()),
                  max(v for _, v in _pk.values()),
                  min(y for y, _ in _pk.values()), max(y for y, _ in _pk.values())),
               xy=(2235, 2.55), fontsize=7.5, color="0.3", ha="center")

ymax = max(WR.gsic_hi.max(), max(lad(s).p95_cm.max() for s in LABELS)) * 1.02

# ---- (b) Wigley-Raper ----
for s in LABELS:
    d = wr(s)
    ax[1].plot(d.year.values, d.gsic_med.values, color=COL[s], lw=1.9)
    if s == SPREAD_LO:
        ax[1].fill_between(d.year.values, d.gsic_lo.values, d.gsic_hi.values,
                           color=COL[s], alpha=0.15, lw=0)
ax[1].text(0.012, 0.93, "(b)  %s — keeps melting toward a common ceiling even where T declines"
           % WR_NAME, transform=ax[1].transAxes, fontsize=9.5, fontweight="bold", va="top")

# ---- (c) Ladrillo L21 ----
for s in LABELS:
    d = lad(s)
    ax[2].plot(d.index.values, d.med_cm.values, color=COL[s], lw=1.9)
    if s == SPREAD_LO:
        ax[2].fill_between(d.index.values, d.p05_cm.values, d.p95_cm.values,
                           color=COL[s], alpha=0.15, lw=0)
ax[2].text(0.012, 0.93, "(c)  %s — the 3 reservoirs equilibrate, so declining T slows the melt"
           % LAD_NAME, transform=ax[2].transAxes, fontsize=9.5, fontweight="bold", va="top")
sp_wr = (wr(SPREAD_HI).set_index("year").gsic_med.loc[2300]
         - wr(SPREAD_LO).set_index("year").gsic_med.loc[2300])
sp_lad = lad(SPREAD_HI).med_cm.loc[2300] - lad(SPREAD_LO).med_cm.loc[2300]
## NO DAGGER. On the SSP figure this number straddles two calibrations and must carry one;
## the provenance gate above has proved that it does not here.
## ⚠ LADRILLO'S SCENARIO SPREAD IS THE WIDER ONE, and that is the point. Wigley-Raper
## saturates toward a common ceiling, which COMPRESSES its spread; Ladrillo keeps tracking
## temperature, so its markers stay separated. It is also why dropping the extA108 arms
## costs nothing: the b=0.52 counterfactual existed only to restore a spread that plain
## Mengel's b->0.89 had collapsed (3.5 cm), and the shipped model never collapses it.
ax[2].legend(handles=[Line2D([], [], color="none",
                             label=f"{SPREAD_LO}→{SPREAD_HI} spread @2300:"),
                      Line2D([], [], color="none",
                             label=f"   {WR_NAME}  {sp_wr:.1f} cm"),
                      Line2D([], [], color="none",
                             label=f"   {LAD_NAME}  {sp_lad:.1f} cm  ← WIDER")],
             fontsize=8, loc="lower right", handlelength=0, handletextpad=0,
             frameon=True, framealpha=0.88, edgecolor="none", facecolor="white")

for a in (ax[1], ax[2]):
    a.set_ylim(0, ymax)
    a.axvline(2100, color="0.6", lw=0.8, ls=":")
    a.set_ylabel("cumulative glacier\nmelt (cm SLE, rel 1995–2014)")

# ---- (d) melt rate on the four decline pathways ----
## THE COMMITMENT PANEL, built from the DECLINE flag in MARKERS rather than a typed list,
## so it cannot fall out of step with panel (a).
for s in DECLINE:
    d = wr(s)
    ax[3].plot(d.year.values, np.gradient(d.gsic_med.values, d.year.values) * 100,
               color=COL[s], lw=1.8, ls="-")
    e = lad(s)
    ax[3].plot(e.index.values, np.gradient(e.med_cm.values, e.index.values) * 100,
               color=COL[s], lw=1.8, ls="--")
ax[3].axhline(0, color="0.6", lw=0.8)
ax[3].axvline(2100, color="0.6", lw=0.8, ls=":")
ax[3].set_ylabel("melt rate\n(cm / century)")
ax[3].set_xlabel("year")
ax[3].set_xlim(X0, X1)
ax[3].text(0.012, 0.93, "(d)  melt rate on the %d peak-and-decline pathways — WR solid stays "
           "high, Ladrillo dashed falls toward zero" % len(DECLINE),
           transform=ax[3].transAxes, fontsize=9.5, fontweight="bold", va="top")
ax[3].legend(handles=[Line2D([], [], color=COL[s], label=s) for s in DECLINE]
             + [Line2D([], [], color="0.3", ls="-", label="Wigley–Raper"),
                Line2D([], [], color="0.3", ls="--", label="Ladrillo %s" % LADRILLO_TAG)],
             fontsize=8, frameon=False, loc="upper right",
             bbox_to_anchor=(1.0, 0.80), ncol=3)

fig.text(0.5, 0.004,
         "BRICK 2.0 WR posterior (parameters_subsample_brick.csv, 1000 draws) vs Ladrillo %s "
         "3-reservoir ν glaciers (%s chains, `%s` arm) — BOTH posterior-parameter spread on MEAN "
         "forcing, so the widths are like-for-like.\nFaIR 2.2.4 (calib 1.6.0) van Vuuren marker "
         "GMST; one build, one calibration throughout (driver commit %s), each marker on its OWN "
         "CMIP7 land-use, irrigation and volcanic/solar forcing.\nWR takes GMST directly; Ladrillo "
         "maps it to each block's glacier frame as amp_b·GMST with an anchor-preserving splice — "
         "the same forcing, not the same per-component temperature."
         % (LADRILLO_TAG, LADRILLO_TAG, ARM, _COMMIT),
         fontsize=6.6, ha="center", color="0.35")
fig.savefig(OUTPNG, dpi=150, bbox_inches="tight")
print("wrote " + OUTPNG)

print("\n%-16s %8s %8s %10s %10s %12s %12s"
      % ("marker", "peak K", "@yr", "WR@2300", "Lad@2300", "WR rate@2300", "Lad rate@2300"))
for s in LABELS:
    g = wr(s).set_index("year").gmst.loc[2015:2300]
    d, e = wr(s), lad(s)
    print("%-16s %8.2f %8d %10.2f %10.2f %12.2f %12.2f"
          % (s, g.max(), g.idxmax(),
             d.set_index("year").gsic_med.loc[2300], e.med_cm.loc[2300],
             np.gradient(d.gsic_med.values, d.year.values)[-1] * 100,
             np.gradient(e.med_cm.values, e.index.values)[-1] * 100))
