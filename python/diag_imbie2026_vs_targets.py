#!/usr/bin/env python3
"""
diag_imbie2026_vs_targets.py -- does the IMBIE 2026 reconciled ice-sheet record (Otosaka et al. 2026, Sci Data
13:1301; Greenland 1972-2023, Antarctica 1979-2023, with an SMB / dynamics split) move Ladrillo's ice-sheet
TARGETS, and how do the L27 and BRICK 2.0 hindcasts sit against it?

Four questions, each with BOTH error bars:
  1. TARGET vs IMBIE: the change in our AIS / GIS target (Frederikse 2020 through 2018, GRACE-FO mascons after)
     over IMBIE's windows, against IMBIE's cumulative change. Our bar = the Frederikse 5000-member ensemble's
     spread of the SAME difference (members re-referenced per member, so the correlated level error cancels);
     past 2018 the GRACE splice's typed sigma is added in quadrature. IMBIE's bar = its own cumulative sigma.
  2. MODEL vs IMBIE: the L27 and BRICK 2.0 posterior-predictive medians and 5-95 bands over the same windows.
  3. THE 1979-2008 NET BALANCE (the window of the A5 Rignot anchor): IMBIE's reconciled mean total mass balance over
     1979-2008 against our target's and the models' net rate over the same window, in Gt/yr. NB the A5 anchor itself
     scores the ABSOLUTE SMB flux (beta_total, 1863 +/- 118 Gt/yr area-scaled from Rignot 2019's 2098 +/- 133); IMBIE
     publishes SMB / dynamics ANOMALIES only (relative to a balanced reference), so it cannot replace that anchor --
     what it adds is the reconciled NET series, which the AIS time-series target already carries.
  4. THE MOUGINOT PARTITION (GISB / MOUG_SHARE): the surface share of Greenland's extra loss rate in 2000-2018 over
     1972-1990 is scored at MOUG_SHARE +/- MOUG_SHARE_SD. IMBIE's SMB and dynamics anomalies give the same share.

Sign convention: IMBIE 'mass balance' is ice mass (negative = loss); sea level = -(mass balance). Everything here
is in cm SLE, positive = sea-level rise, and level anomalies are re-referenced to REF (the targets' window).

Writes outputs/diag_imbie2026_vs_targets_<TAG>.csv (+ _windows_, _anchors_) and figures/diag_imbie2026_vs_targets_<TAG>.png.
  python python/diag_imbie2026_vs_targets.py --tag=L27
"""
import os, sys, argparse, subprocess
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
import ladrillo_figs as lf

ap = argparse.ArgumentParser(); ap.add_argument("--tag", default="L27"); TAG = ap.parse_args().tag
SCRIPT = os.path.basename(__file__)
REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
RAW = os.path.join(REPO, "data/observations/raw"); IMB = os.path.join(RAW, "imbie2026")
OUT = os.path.join(REPO, "outputs"); FIG = os.path.join(REPO, "figures")
REF = (1995, 2005)                       # the targets' reference window
GT_PER_MM = 361.8                        # Gt per mm SLE (IMBIE's own mm files are used where they exist)
FRED_END = 2018                          # last Frederikse year; GRACE splice after
GRACE_SIG_CM = {"ais": 0.05, "gis": 0.03}   # typed splice sigma per year past FRED_END, cm (conservative; the mascon
                                            # series' own annual sigma is ~0.03 AIS / ~0.02 GIS), added in quadrature
RIGNOT_WIN = (1979, 2008)                # the A5 anchor's window (calibrate_mcmc_ext.jl SMB_Y0..SMB_Y1)
CM_TO_GT = -10.0 * GT_PER_MM             # cm SLE of rise -> Gt of ice mass (negative = loss)
MOUG_SHARE, MOUG_SHARE_SD = 0.735, 0.05  # GISB partition term (calibrate_mcmc_ext.jl)
MOUG_REF_WIN, MOUG_LATE_WIN = (1972, 1990), (2000, 2018)
WINDOWS = {"ais": [(1979, 2023), (1979, 2008), (1979, 1991), (1992, 2002), (1992, 2020), (2003, 2010), (2011, 2017), (2018, 2023), (2020, 2023)],
           "gis": [(1972, 2023), (1972, 1991), (1992, 2002), (1992, 2020), (2003, 2010), (2011, 2017), (2018, 2023)]}
COMMIT = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
PROV = ("%s | tag %s | IMBIE 2026 (Otosaka et al. Sci Data 13:1301; PDC 10.5285/128c5e33) annual means of monthly rates | "
        "targets recalib_targets_ext.csv (Frederikse 2020 <= %d, GRACE-FO after) | target bar = Frederikse ensemble spread of the "
        "difference (+ %.2f/%.2f cm/yr GRACE sigma in quadrature past %d) | model postpred_%s / postpred_oldbrick | cm SLE, +=rise, "
        "rel %d-%d | commit %s" % (SCRIPT, TAG, FRED_END, GRACE_SIG_CM["ais"], GRACE_SIG_CM["gis"], FRED_END, TAG, REF[0], REF[1], COMMIT))

# ---- IMBIE: annual series in cm SLE, +=rise ------------------------------------------------------------
def imbie(region, unit):
    f = os.path.join(IMB, "imbie3_%s_%s_partitioned.csv" % (region, unit))
    d = pd.read_csv(f, comment="#"); d["year"] = pd.to_datetime(d.Date).dt.year
    d = d[(d.year <= 2023) & (d.year >= 1972)]              # Greenland starts 1971-07; 2024 has no complete year
    rate = d.groupby("year").agg(mb=("Mass balance (%s/yr)" % unit, "mean"), mb_sig=("Mass balance uncertainty (%s/yr)" % unit, "mean"),
                                 smb=("Surface mass balance anomaly (%s/yr)" % unit, "mean"), smb_sig=("Surface mass balance anomaly uncertainty (%s/yr)" % unit, "mean"),
                                 dyn=("Dynamics mass balance anomaly (%s/yr)" % unit, "mean"), dyn_sig=("Dynamics mass balance anomaly uncertainty (%s/yr)" % unit, "mean"),
                                 n=("Date", "size"))
    # December value of the cumulative anomaly = end-of-year level; its sigma likewise
    dec = d[pd.to_datetime(d.Date).dt.month == 12].set_index("year")
    rate["cum"] = dec["Cumulative mass balance anomaly (%s)" % unit]
    rate["cum_sig"] = dec["Cumulative mass balance anomaly uncertainty (%s)" % unit]
    rate["cum_smb"] = dec["Cumulative surface mass balance anomaly (%s)" % unit]
    rate["cum_dyn"] = dec["Cumulative dynamics mass balance anomaly (%s)" % unit]
    assert (rate.n == 12).all(), "%s %s: incomplete years %s" % (region, unit, list(rate.index[rate.n != 12]))
    return rate
IM = {"ais": imbie("antarctica", "mm"), "gis": imbie("greenland", "mm")}
IMG = {"ais": imbie("antarctica", "Gt"), "gis": imbie("greenland", "Gt")}
for k in IM:   # ice mass -> sea level, mm -> cm; sigmas unchanged in magnitude
    for c in ("mb", "smb", "dyn", "cum", "cum_smb", "cum_dyn"):
        IM[k][c] = -IM[k][c] / 10.0
    for c in ("mb_sig", "smb_sig", "dyn_sig", "cum_sig"):
        IM[k][c] = IM[k][c] / 10.0
    assert np.allclose(IM[k].mb, IM[k].smb + IM[k].dyn, atol=1e-6), "IMBIE %s: SMB + dynamics != total" % k

# ---- targets, model, Frederikse ensemble ---------------------------------------------------------------
T = pd.read_csv(os.path.join(OUT, "recalib_targets_ext.csv")).set_index("year")
L = pd.read_csv(os.path.join(OUT, "postpred_%s_components_timeseries.csv" % TAG)).set_index("year")
B = pd.read_csv(os.path.join(OUT, "postpred_oldbrick_components_timeseries.csv")).set_index("year")
ENS = xr.open_dataset(os.path.join(RAW, "frederikse2020_GMSL_ensembles.nc"))
ENS_VAR = {"ais": "AIS", "gis": "GrIS"}
w = ENS.likelihood.values; w = w / w.sum()

def diff(s, y0, y1):        # level change from end of y0-1 to end of y1 (annual level series)
    return float(s.loc[y1] - s.loc[y0 - 1])
def target_diff(comp, y0, y1):
    """Our target's change over [y0, y1] and its 1-sigma bar (ensemble spread of the difference + GRACE quadrature)."""
    val = diff(T[comp], y0, y1)
    a = ENS[ENS_VAR[comp]].values                        # (member, time) cm? -> check units below
    yrs = ENS.time.values
    e0, e1 = max(y0 - 1, yrs.min()), min(y1, FRED_END)
    if e1 > e0:
        dd = a[:, np.searchsorted(yrs, e1)] - a[:, np.searchsorted(yrs, e0)]
        m = np.sum(w * dd); sd_f = np.sqrt(np.sum(w * (dd - m) ** 2)) / 10.0   # ensemble is in mm
    else:
        sd_f = 0.0
    n_grace = max(0, y1 - max(y0 - 1, FRED_END))
    return val, np.sqrt(sd_f ** 2 + n_grace * GRACE_SIG_CM[comp] ** 2)
def imbie_diff(comp, y0, y1):
    d = IM[comp]; v = float(d.cum.loc[y1] - (d.cum.loc[y0 - 1] if y0 - 1 in d.index else 0.0))
    s1 = float(d.cum_sig.loc[y1]); s0 = float(d.cum_sig.loc[y0 - 1]) if y0 - 1 in d.index else 0.0
    return v, np.sqrt(max(s1 ** 2 - s0 ** 2, (s1 - s0) ** 2))   # cumulative sigma is a random walk from the start
def model_diff(P, comp, y0, y1, p="p50"):
    return diff(P["%s_%s" % (comp, p)], y0, y1)

# ---- 1 + 2: windows ---------------------------------------------------------------------------------
rows = []
for comp in ("ais", "gis"):
    for (y0, y1) in WINDOWS[comp]:
        n = y1 - y0 + 1
        iv, isd = imbie_diff(comp, y0, y1); tv, tsd = target_diff(comp, y0, y1)
        lm = model_diff(L, comp, y0, y1); l5, l95 = model_diff(L, comp, y0, y1, "p05"), model_diff(L, comp, y0, y1, "p95")
        bm = model_diff(B, comp, y0, y1, "p50"); b5, b95 = model_diff(B, comp, y0, y1, "p5"), model_diff(B, comp, y0, y1, "p95")
        z_t = (tv - iv) / np.sqrt(tsd ** 2 + isd ** 2)
        lsd = (l95 - l5) / 3.29; bsd = (b95 - b5) / 3.29
        rows.append(dict(component=comp.upper(), y0=y0, y1=y1, years=n, imbie_cm=iv, imbie_sd=isd, target_cm=tv, target_sd=tsd,
                         z_target_vs_imbie=z_t, ladrillo_cm=lm, ladrillo_p05=l5, ladrillo_p95=l95, z_ladrillo_vs_imbie=(lm - iv) / np.sqrt(lsd ** 2 + isd ** 2),
                         brick20_cm=bm, brick20_p05=b5, brick20_p95=b95, z_brick20_vs_imbie=(bm - iv) / np.sqrt(bsd ** 2 + isd ** 2),
                         imbie_rate_cm_yr=iv / n, target_rate_cm_yr=tv / n, ladrillo_rate_cm_yr=lm / n, brick20_rate_cm_yr=bm / n, provenance=PROV))
W = pd.DataFrame(rows); W.to_csv(os.path.join(OUT, "diag_imbie2026_vs_targets_windows_%s.csv" % TAG), index=False)

# ---- 3: the 1979-2008 net balance (Gt/yr, ice-mass sign: negative = loss) ------------------------------
g = IMG["ais"]; m = (g.index >= RIGNOT_WIN[0]) & (g.index <= RIGNOT_WIN[1]); nw = RIGNOT_WIN[1] - RIGNOT_WIN[0] + 1
im_net = float(g.mb[m].mean()); im_net_sd = float(np.sqrt((g.mb_sig[m] ** 2).sum()) / m.sum())   # independent-years sd of the mean
im_net_sd_corr = float(g.mb_sig[m].mean())                                                          # fully-correlated (conservative)
im_smb = float(g.smb[m].mean()); im_dyn = float(g.dyn[m].mean())
tv, tsd = target_diff("ais", *RIGNOT_WIN); t_net, t_net_sd = tv / nw * CM_TO_GT, tsd / nw * abs(CM_TO_GT)
l_net = model_diff(L, "ais", *RIGNOT_WIN) / nw * CM_TO_GT; b_net = model_diff(B, "ais", *RIGNOT_WIN) / nw * CM_TO_GT
# ---- 4: the Mouginot partition ----------------------------------------------------------------------
gg = IMG["gis"]
def win_mean(s, win): return float(s[(gg.index >= win[0]) & (gg.index <= win[1])].mean())
d_tot = win_mean(gg.mb, MOUG_LATE_WIN) - win_mean(gg.mb, MOUG_REF_WIN)
d_smb = win_mean(gg.smb, MOUG_LATE_WIN) - win_mean(gg.smb, MOUG_REF_WIN)
d_dyn = win_mean(gg.dyn, MOUG_LATE_WIN) - win_mean(gg.dyn, MOUG_REF_WIN)
im_share = d_smb / d_tot
# share sigma from IMBIE's per-year SMB / dynamics sigmas, two corners: independent years, fully correlated
def win_sd(sig, win, corr):
    v = sig[(gg.index >= win[0]) & (gg.index <= win[1])]
    return float(v.mean()) if corr else float(np.sqrt((v ** 2).sum()) / len(v))
def share_sd(corr):
    s_smb = np.sqrt(win_sd(gg.smb_sig, MOUG_LATE_WIN, corr) ** 2 + win_sd(gg.smb_sig, MOUG_REF_WIN, corr) ** 2)
    s_dyn = np.sqrt(win_sd(gg.dyn_sig, MOUG_LATE_WIN, corr) ** 2 + win_sd(gg.dyn_sig, MOUG_REF_WIN, corr) ** 2)
    # share = smb/(smb+dyn); delta method with smb, dyn independent
    return float(np.sqrt((d_dyn / d_tot ** 2 * s_smb) ** 2 + (d_smb / d_tot ** 2 * s_dyn) ** 2))
sh_sd_i, sh_sd_c = share_sd(False), share_sd(True)
A = pd.DataFrame([
    dict(anchor="AIS net balance %d-%d (Gt/yr, ice mass): our TARGET" % RIGNOT_WIN, ours_mu=t_net, ours_sd=t_net_sd,
         imbie_value=im_net, imbie_sd_indep=im_net_sd, imbie_sd_corr=im_net_sd_corr, imbie_smb_anom=im_smb, imbie_dyn_anom=im_dyn,
         z_indep=(t_net - im_net) / np.sqrt(t_net_sd ** 2 + im_net_sd ** 2), z_corr=(t_net - im_net) / np.sqrt(t_net_sd ** 2 + im_net_sd_corr ** 2), provenance=PROV),
    dict(anchor="AIS net balance %d-%d (Gt/yr, ice mass): Ladrillo %s median" % (RIGNOT_WIN + (TAG,)), ours_mu=l_net, ours_sd=np.nan,
         imbie_value=im_net, imbie_sd_indep=im_net_sd, imbie_sd_corr=im_net_sd_corr, imbie_smb_anom=im_smb, imbie_dyn_anom=im_dyn,
         z_indep=(l_net - im_net) / im_net_sd, z_corr=(l_net - im_net) / im_net_sd_corr, provenance=PROV),
    dict(anchor="AIS net balance %d-%d (Gt/yr, ice mass): BRICK 2.0 median" % RIGNOT_WIN, ours_mu=b_net, ours_sd=np.nan,
         imbie_value=im_net, imbie_sd_indep=im_net_sd, imbie_sd_corr=im_net_sd_corr, imbie_smb_anom=im_smb, imbie_dyn_anom=im_dyn,
         z_indep=(b_net - im_net) / im_net_sd, z_corr=(b_net - im_net) / im_net_sd_corr, provenance=PROV),
    dict(anchor="GISB Mouginot surface share of the extra loss %d-%d over %d-%d" % (MOUG_LATE_WIN + MOUG_REF_WIN), ours_mu=MOUG_SHARE, ours_sd=MOUG_SHARE_SD,
         imbie_value=im_share, imbie_sd_indep=sh_sd_i, imbie_sd_corr=sh_sd_c, imbie_smb_anom=d_smb, imbie_dyn_anom=d_dyn,
         z_indep=(im_share - MOUG_SHARE) / np.sqrt(MOUG_SHARE_SD ** 2 + sh_sd_i ** 2), z_corr=(im_share - MOUG_SHARE) / np.sqrt(MOUG_SHARE_SD ** 2 + sh_sd_c ** 2), provenance=PROV)])
A.to_csv(os.path.join(OUT, "diag_imbie2026_vs_targets_anchors_%s.csv" % TAG), index=False)

# ---- the annual overlay table (cm rel REF) ----------------------------------------------------------
def rebase(s): return s - s.loc[REF[0]:REF[1]].mean()
ov = []
for comp in ("ais", "gis"):
    d = IM[comp]; lvl = rebase(d.cum)
    ov.append(pd.DataFrame(dict(year=d.index, component=comp.upper(), imbie_level_cm=lvl.values, imbie_level_sd=d.cum_sig.values,
                                imbie_rate_cm_yr=d.mb.values, imbie_smb_rate=d.smb.values, imbie_dyn_rate=d.dyn.values,
                                target_level_cm=rebase(T[comp]).reindex(d.index).values,
                                ladrillo_p50=rebase(L[comp + "_p50"]).reindex(d.index).values,
                                brick20_p50=rebase(B[comp + "_p50"]).reindex(d.index).values, provenance=PROV)))
OV = pd.concat(ov); OV.to_csv(os.path.join(OUT, "diag_imbie2026_vs_targets_%s.csv" % TAG), index=False)

# ---- figure ----------------------------------------------------------------------------------------
C_LAD, C_BRK = lf.SRC_COLOR["Ladrillo"], lf.SRC_COLOR["BRICK 2.0"]; C_OBS, C_IMB = "#1b7837", "#762a83"
fig, axes = plt.subplots(2, 2, figsize=(11, 7.2), gridspec_kw=dict(height_ratios=[1.35, 1]))
for j, comp in enumerate(("ais", "gis")):
    d = IM[comp]; y = d.index; ax = axes[0, j]
    lvl = rebase(d.cum)
    ax.fill_between(y, lvl - d.cum_sig, lvl + d.cum_sig, color=C_IMB, alpha=0.15, lw=0)
    ax.plot(y, lvl, color=C_IMB, lw=2.0, label="IMBIE 2026 (±1σ)")
    tt = rebase(T[comp]).loc[1960:2026]
    ax.plot(tt.index, tt.values, color=C_OBS, lw=1.6, label="current target (Frederikse ≤%d, GRACE after)" % FRED_END)
    ll = L.loc[1960:2026]; bb = B.loc[1960:2026]
    ax.fill_between(ll.index, rebase(L[comp + "_p05"]).loc[1960:2026], rebase(L[comp + "_p95"]).loc[1960:2026], color=C_LAD, alpha=0.12, lw=0)
    ax.plot(ll.index, rebase(L[comp + "_p50"]).loc[1960:2026], color=C_LAD, lw=1.9, label="Ladrillo %s (median, 5–95%%)" % TAG)
    ax.plot(bb.index, rebase(B[comp + "_p50"]).loc[1960:2026], color=C_BRK, lw=1.5, ls="--", label="BRICK 2.0 (median)")
    ax.axvline(FRED_END + 0.5, color="0.7", lw=0.8, ls=":")
    ax.set_title("%s — level, cm SLE rel. %d–%d" % (comp.upper(), *REF), fontsize=10, loc="left")
    ax.grid(alpha=0.25); ax.set_xlim(1960, 2026)
    if j == 0: ax.legend(fontsize=7.5, loc="upper left", frameon=False)
    ax = axes[1, j]
    ax.bar(y, d.smb, color="#5aae61", width=1.0, label="IMBIE SMB anomaly")
    ax.bar(y, d.dyn, bottom=np.where(d.dyn * d.smb > 0, d.smb, 0), color="#9970ab", width=1.0, label="IMBIE dynamics anomaly")
    ax.plot(y, d.mb, color=C_IMB, lw=1.6, label="IMBIE total rate")
    tr = T[comp].diff().loc[y.min():2026]; ax.plot(tr.index, tr.values, color=C_OBS, lw=1.2, label="target rate")
    lr = L[comp + "_p50"].diff().loc[y.min():2026]; ax.plot(lr.index, lr.values, color=C_LAD, lw=1.4, label="Ladrillo rate")
    ax.axhline(0, color="0.5", lw=0.6); ax.grid(alpha=0.25); ax.set_xlim(1960, 2026)
    ax.set_title("%s — rate, cm SLE yr⁻¹ (+ = sea-level rise)" % comp.upper(), fontsize=10, loc="left")
    if j == 0: ax.legend(fontsize=7.5, loc="upper left", frameon=False, ncol=2)
fig.suptitle("IMBIE 2026 against Ladrillo's ice-sheet targets and the %s / BRICK 2.0 hindcasts" % TAG, fontsize=11)
fig.text(0.01, 0.005, PROV, fontsize=5.2, color="0.45")
fig.tight_layout(rect=(0, 0.02, 1, 0.97))
png = os.path.join(FIG, "diag_imbie2026_vs_targets_%s.png" % TAG); fig.savefig(png, dpi=160)

# ---- report ---------------------------------------------------------------------------------------
pd.set_option("display.width", 220)
print(PROV, "\n")
print("WINDOWS (cm over the window; z uses BOTH bars; model sd = (p95-p05)/3.29):")
print(W[["component", "y0", "y1", "imbie_cm", "imbie_sd", "target_cm", "target_sd", "z_target_vs_imbie", "ladrillo_cm", "z_ladrillo_vs_imbie", "brick20_cm", "z_brick20_vs_imbie"]]
      .round(3).to_string(index=False))
print("\nRATES (cm/yr):")
print(W[["component", "y0", "y1", "imbie_rate_cm_yr", "target_rate_cm_yr", "ladrillo_rate_cm_yr", "brick20_rate_cm_yr"]].round(4).to_string(index=False))
print("\nANCHOR WINDOWS (ice-mass sign; z_indep / z_corr = IMBIE per-year sigmas treated as independent / fully correlated):")
print(A.drop(columns="provenance").round(3).to_string(index=False))
print("\nwrote", os.path.relpath(png, REPO), "and outputs/diag_imbie2026_vs_targets{,_windows,_anchors}_%s.csv" % TAG)
