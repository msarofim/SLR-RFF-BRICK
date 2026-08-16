#!/usr/bin/env python3
"""
gis_offline_cell.py — the Greenland pass-1 offline cell: fit stock / A / B /
A+B / A+B+C against the historical target plus the Mouginot partition, under
gates pre-registered before any fitting.

This is step 4 of notes/handoff_2026-08-10_greenland_pass1.md. It is the
offline reference the Julia surgery is later validated against at 1e-9, the
way python/ladrillo_data.py is for the glacier blocks.

-----------------------------------------------------------------------------
THE CELLS
-----------------------------------------------------------------------------
Everything is a relaxation of cumulative loss L (cm SLE) toward a committed
loss L_eq, in BRICK's own rate form 1/tau = alpha*T + beta:

    stock    rate driver GMST,     L_eq linear in GMST,        1 channel
    A        rate driver REGIONAL, L_eq linear in regional,    1 channel
    B        rate driver GMST,     L_eq linear in GMST,        2 channels
    A+B      rate driver REGIONAL, L_eq linear in regional,    2 channels
    A+B+C    rate driver REGIONAL, L_eq = PISM ladder(GMT-dT), 2 channels
    A+B+C+D  as A+B+C,   plus a THROUGHPUT CAP on both channels   (q_f, q_s)
    A+B'+C+D as A+B'+C,  plus a THROUGHPUT CAP on the slow channel (q_s)

Option D (added 2026-08-16) is the piece pass 1 lacked. A proportional
relaxation cannot serve both a 6 cm historical loss against a 71 cm commitment
AND a 742 cm post-threshold commitment: as L_eq grows 20x the proportional rate
grows with it, which is why A+B+C broke the hindcast (RMSE 1.675) and projected
72 cm at 2100. D clips the annual flux to +/- q cm/yr, so past the threshold
loss is limited by ice THROUGHPUT rather than by the disequilibrium. Each D cell
nests its C counterpart bit-for-bit at q = CAP_INERT_CM_YR; see _throughput.

Two channels means the commitment splits, fraction f realised fast (surface
mass balance) and 1-f slow (dynamic discharge), each with its own alpha, beta.
The regional driver enters through the RATE, not through the equilibrium:
local temperature governs how fast melt is realised, while the ladder's
equilibrium is a function of the large-scale state (see fit_gis_veq_pism.py).

The V/V0 damping of stock SIMPLE is DROPPED from every cell. Measured in
scoping §3: it changes the 2100 scenario spread by 0.0 cm, because only ~1% of
the ice sheet is gone by 2100 so V/V0 ~ 0.99. It is also the wrong sign
physically (scoping §10 option D). Keeping it would only add a parameter.

-----------------------------------------------------------------------------
CONSTRAINTS
-----------------------------------------------------------------------------
GIS target   outputs/recalib_targets_ext.csv, Frederikse 2020 spliced to
             GRACE-FO, 1900-2025, cm, re-referenced 1995-2005. Sigma from the
             90% band exactly as calibrate_mcmc_ext.jl builds it.
Mouginot     data/observations/greenland_partition_mouginot2019.csv. The extra
             loss of 2000-2018 over 1972-1990 is 73.5% surface / 26.5% dynamic
             (verified here from the file, closure exact to 0.000 Gt/yr). This
             is what makes the two-channel split identifiable -- without it f
             and the timescales trade off freely.
dT prior     outputs/gis_dt_prior.csv, Normal(-0.63, 0.55) truncated
             [-1.58, +0.22], from Bochow 2023 + Armstrong McKay 2022 with a
             Box 2022 observational floor. See python/set_gis_dt_prior.py.

ISMIP6 IS EVALUATION-ONLY, PERMANENTLY (handoff decision 4). It is a transient
intercomparison of the same quantity we predict, so fitting to it would make
Ladrillo's Greenland a second-hand FACTS FittedISMIP and destroy the
comparison's independence. The 2100 scenario spread is therefore REPORTED
against FACTS/MAGICC and never enters the objective.

  python3 python/gis_offline_cell.py
Writes:
  outputs/gis_offline_cell_fits.csv     per-cell parameters, gates, diagnostics
  outputs/gis_offline_cell_series.csv   per-cell hindcast and projections
  outputs/gis_offline_cell_ridge.csv    the separability profiles
  figures/gis_offline_cell.png
"""
import os
import subprocess

import numpy as np
import pandas as pd
from scipy.optimize import minimize

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBS = os.path.join(REPO, "data/observations")
TARGETS_CSV = os.path.join(REPO, "outputs/recalib_targets_ext.csv")
DRIVER_CSV = os.path.join(OBS, "t_gis_zones.csv")
MOUGINOT_CSV = os.path.join(OBS, "greenland_partition_mouginot2019.csv")
LADDER_CURVE_CSV = os.path.join(REPO, "outputs/gis_veq_pism_curve.csv")
AMP_PRIOR_CSV = os.path.join(REPO, "outputs/gis_amp_prior.csv")

OUT_FITS = os.path.join(REPO, "outputs/gis_offline_cell_fits.csv")
OUT_SERIES = os.path.join(REPO, "outputs/gis_offline_cell_series.csv")
OUT_RIDGE = os.path.join(REPO, "outputs/gis_offline_cell_ridge.csv")
OUT_FIG = os.path.join(REPO, "figures/gis_offline_cell.png")

# ---- frame ------------------------------------------------------------------
Y0, Y1 = 1850, 2300
REF_WIN = (1995, 2005)          # display/target baseline, as calibrate_mcmc_ext.jl
BASE_WIN = (1850, 1900)         # anomaly baseline of every temperature series
FIT_WIN = (1900, 2025)          # the GIS target's span
V0_CM = 742.0                   # Greenland volume, cm SLE
# Option-D throughput cap at which the cap is PROVABLY INERT: no annual
# relaxation increment can exceed L_eq, and L_eq <= V0_CM everywhere. Setting a
# cap here reproduces the uncapped cell bit-for-bit, which is what makes the
# D cells exact containers of the C cells.
CAP_INERT_CM_YR = V0_CM
DRIVER_ZONE = "south"           # Marcus 2026-08-10; "all" is the sensitivity arm
SIGMA_FLOOR_CM = 0.05           # matches epsband() in calibrate_mcmc_ext.jl
BAND_Z = 1.645                  # the target bands are 90%

# ---- Mouginot partition constraint -----------------------------------------
MOUG_REF_WIN = (1972, 1990)     # the near-balance reference period
MOUG_LATE_WIN = (2000, 2018)    # the modern loss period
MOUG_SURFACE_SHARE = 0.735      # verified from the file, not assumed
MOUG_SHARE_SIGMA = 0.05

# ---- dT prior (python/set_gis_dt_prior.py) ---------------------------------
DT_PRIOR = dict(mu=-0.63, sigma=0.55, lo=-1.58, hi=0.22)

# ---- amplification, for the projection splice only -------------------------
# Headline full-window (1901-2024) cross-product mean from build_t_gis.py.
# NOTE the correction: the scoping note's N(2.9, 0.2) was a masking artifact.
AMP_MEAN = 1.92
SPLICE_ANCHOR_YEARS = 11        # the anchor-preserving splice window, as ladrillo_projection.jl

# =============================================================================
# PRE-REGISTERED GATES -- stated here, before any fit is run
# =============================================================================
# G1 modern rate. Observed 2003-2018 is 0.841 mm/yr SLE; a cell passes within
#    +/-25%, which is wider than the target's own uncertainty and is meant to
#    catch structural failure, not to rank close calls.
GATE_RATE_WIN = (2003, 2018)
GATE_RATE_OBS_MMYR = 0.841
GATE_RATE_TOL_FRAC = 0.25
# G2 the 1942-1982 window -- the only contiguous miss in the Ladrillo fit,
#    currently 0.5-0.7 cm. A cell passes at a mean absolute bias below 0.30 cm.
GATE_MIDCEN_WIN = (1942, 1982)
GATE_MIDCEN_TOL_CM = 0.30
# G3 mid-century SHAPE: the observed melt rate FALLS across that window. A cell
#    that gets the level by accident but the trend backwards has not fixed it.
GATE_SHAPE_REQUIRE_NEGATIVE_TREND = True
# G4 EVALUATION ONLY, never in the objective. 2100 SSP1-2.6 -> SSP5-8.5 spread.
#    Ladrillo extC is 2.16 cm today; MAGICC-SLR 7.09, FACTS FittedISMIP 6.34,
#    emuGrIS 7.26, bamber19 7.23 (outputs/ladrillo_model_comparison_L10_spread.csv).
GATE_SPREAD_RANGE_CM = (6.3, 7.3)
PROJ_SCENARIOS = {"SSP1-2.6": "ssp126", "SSP2-4.5": "ssp245", "SSP5-8.5": "ssp585"}
PROJ_YEAR = 2100
PROJ_REF_WIN = (1995, 2014)     # the frame the comparison arms use

# ---- fitting protocol -------------------------------------------------------
# CORRECTED 2026-08-12. The first version drew all starts UNIFORMLY over bounds
# that span five orders of magnitude on the rate axes, ran 60 of them, and took
# the best Nelder-Mead result without a restart. NM collapses its simplex on a
# flat log-scaled objective and stops early, so that protocol returned points
# up to 24.7 nlp units above the optimum -- the tell was that 214 of the 225
# points in the A+B (f, beta_f) ridge, which FIX two parameters and re-optimise
# the rest with a WEAKER inner optimiser, scored BELOW the reported
# 8-parameter optimum. A constrained fit cannot beat an unconstrained one.
# The three changes: log-uniform draws on the rate axes, more starts, and a
# restart-until-no-improvement polish. python/diag_gis_g_betaf.py is the audit.
FIT_SEED = 2026
N_MULTISTART = 240
MAXFEV = 20000
LOG_AXES = ("alpha", "beta", "alpha_f", "beta_f", "alpha_s", "beta_s",
            "q_f", "q_s")
POLISH_ROUNDS = 12              # NM restarts from the incumbent best
POLISH_TOL = 1e-9
BASIN_ROUNDS = 40               # basin-hopping jitters around the incumbent best
BASIN_LOG_SD = 0.8              # jitter sd, natural log units, on the rate axes
BASIN_LIN_FRAC = 0.08           # jitter sd as a fraction of the bound width, level axes
REPAIR_TOL = 1e-3               # a ridge point below the optimum by more than this
                                # triggers a refit seeded at that point
RIDGE_N = 11                    # grid per axis for the separability profiles
RIDGE_MAXFEV = 6000
RIDGE_RESTARTS = 2              # random restarts per grid point, ON TOP of the
                                # seed at the converged optimum
RIDGE_LOCAL_FRAC = 0.25         # half-width on the linear axis, as a fraction of its bounds
RIDGE_LOCAL_DECADES = 30.0      # multiplicative half-span on the log axis
RIDGE_DELTA = 2.30              # chi2(2 dof) 68% -- the "1 sigma" contour in 2 parameters

COMMIT = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True).stdout.strip()
_rng = np.random.default_rng(FIT_SEED)
YEARS = np.arange(Y0, Y1 + 1)
_yi = {y: i for i, y in enumerate(YEARS)}


# =============================================================================
# inputs
# =============================================================================
def _yearmap(path, col):
    d = pd.read_csv(path)
    return pd.Series(d[col].to_numpy(float), index=d["year"].to_numpy(int))


def rebase(s, win=BASE_WIN):
    return s - s.loc[win[0]:win[1]].mean()


def load_gmst(tag=None):
    f = "fair_mean_gmst.csv" if tag is None else f"fair_mean_gmst_{tag}.csv"
    return rebase(_yearmap(os.path.join(OBS, f), "gmst_C"))


def extend(s):
    """Onto the model year axis, holding the last value (only the tail beyond
    the source's end is affected; every source covers the fit window)."""
    v = s.reindex(YEARS)
    return v.ffill().bfill().to_numpy(float)


def load_target():
    t = pd.read_csv(TARGETS_CSV).set_index("year")
    g = t[["gis", "gis_lo", "gis_hi"]].dropna()
    g = g.loc[FIT_WIN[0]:FIT_WIN[1]]
    sigma = np.maximum((g["gis_hi"] - g["gis_lo"]) / (2 * BAND_Z), SIGMA_FLOOR_CM)
    return g.index.to_numpy(int), g["gis"].to_numpy(float), sigma.to_numpy(float)


def load_ladder():
    c = pd.read_csv(LADDER_CURVE_CSV)
    return c["gmt_K"].to_numpy(float), c["pchip"].to_numpy(float) * 100.0   # -> cm


def mouginot_surface_share():
    m = pd.read_csv(MOUGINOT_CSV).set_index("year").dropna(subset=["discharge_gt"])
    ref, late = m.loc[slice(*MOUG_REF_WIN)], m.loc[slice(*MOUG_LATE_WIN)]
    d_smb = ref["smb_gt"].mean() - late["smb_gt"].mean()
    d_dis = late["discharge_gt"].mean() - ref["discharge_gt"].mean()
    return float(d_smb / (d_smb + d_dis))


# =============================================================================
# the model
# =============================================================================
LAD_T, LAD_L = load_ladder()


def leq_ladder(gmt, dT):
    return np.interp(gmt - dT, LAD_T, LAD_L)


def _throughput(delta, q):
    """OPTION D. Clip one year's relaxation flux to +/- q cm/yr.

    Past the threshold, loss is limited by how fast ice can physically leave the
    ice sheet -- outlet-glacier discharge capacity, surface melt throughput --
    NOT by the size of the disequilibrium. Proportional relaxation cannot serve
    both a 6 cm historical loss against a 71 cm commitment and a 742 cm
    post-threshold commitment (scoping, pass-1 failure): as L_eq grows 20x the
    proportional rate grows 20x with it, which is exactly why A+B+C broke the
    hindcast (RMSE 1.675) and gave 72 cm at 2100.

    The clip is SYMMETRIC: regrowth is throughput-limited too.

    q = CAP_INERT_CM_YR makes this provably inert -- no annual increment can
    exceed L_eq <= V0_CM -- so a D cell nests its C counterpart exactly."""
    return delta if q >= CAP_INERT_CM_YR else float(np.clip(delta, -q, q))


def integrate(t_rate, leq, params, two_channel, n=None):
    """Annual Euler on dL/dt = (L_eq - L) * (alpha*T + beta), per channel,
    optionally throughput-capped (option D, see _throughput).

    Returns (L_total, L_fast). L(Y0) = 0: the model starts in equilibrium with
    the 1850 climate, and the 1995-2005 re-referencing absorbs the offset.

    `n` truncates the integration; during fitting nothing past the target's last
    year is read, and the loop is the whole cost. Truncation is exact, not an
    approximation -- the recursion is causal."""
    n = len(YEARS) if n is None else n
    g = params.get("g", 1.0)          # fraction of the 1850 commitment already realised
    qf = params.get("q_f", CAP_INERT_CM_YR)   # option-D caps; inert unless the
    qs = params.get("q_s", CAP_INERT_CM_YR)   # cell declares them
    if not two_channel:
        alpha, beta = params["alpha"], params["beta"]
        r = np.maximum(alpha * t_rate + beta, 1e-9)
        L = np.zeros(n)
        L[0] = g * leq[0]
        for i in range(1, n):
            L[i] = L[i - 1] + _throughput(
                (leq[i - 1] - L[i - 1]) * min(r[i - 1], 1.0), qs)
        return L, np.zeros(n)
    rs = np.maximum(params["alpha_s"] * t_rate + params["beta_s"], 1e-9)
    Lf, Ls = np.zeros(n), np.zeros(n)
    if two_channel == "smbrate":
        # Surface mass balance as a DIRECT melt rate in the regional driver, not
        # as a relaxation toward a share of the multi-millennial commitment.
        # The share form cannot work with the ladder: L_eq today is 53-200 cm
        # against ~6 cm of observed loss since 1900, so any fast channel holding
        # a fixed fraction of it overshoots by an order of magnitude, and the
        # fit is forced to rail f at its floor. SMB physically responds to
        # temperature above a melt onset, which is what this is.
        # The fast channel here is ALREADY a throughput form -- a direct melt
        # flux in the regional driver, not a relaxation -- so option D adds a cap
        # only to the slow (dynamic) channel, which is the one that explodes when
        # L_eq reaches ~742 cm.
        k, t_on = params["k_smb"], params["t_on"]
        Ls[0] = g * leq[0]
        for i in range(1, n):
            Lf[i] = Lf[i - 1] + k * max(0.0, t_rate[i - 1] - t_on)
            Ls[i] = Ls[i - 1] + _throughput(
                (leq[i - 1] - Ls[i - 1]) * min(rs[i - 1], 1.0), qs)
            tot = Lf[i] + Ls[i]
            if tot > leq[i - 1]:            # cannot overshoot the commitment
                Lf[i], Ls[i] = Lf[i] * leq[i - 1] / tot, Ls[i] * leq[i - 1] / tot
        return Lf + Ls, Lf
    f = params["f"]
    rf = np.maximum(params["alpha_f"] * t_rate + params["beta_f"], 1e-9)
    Lf[0], Ls[0] = g * f * leq[0], g * (1 - f) * leq[0]
    for i in range(1, n):
        Lf[i] = Lf[i - 1] + _throughput(
            (f * leq[i - 1] - Lf[i - 1]) * min(rf[i - 1], 1.0), qf)
        Ls[i] = Ls[i - 1] + _throughput(
            ((1 - f) * leq[i - 1] - Ls[i - 1]) * min(rs[i - 1], 1.0), qs)
    return Lf + Ls, Lf


# ---- cell definitions -------------------------------------------------------
# rate_driver: which temperature drives the relaxation rate
# leq: "linear" in the rate driver, or "ladder" in GMT with a dT shift
CELLS = {
    # ACCEPTANCE TEST, not a candidate: stock SIMPLE held at the Ladrillo extC
    # posterior medians, NOT refitted. The harness has to reproduce the known
    # incumbent behaviour -- ~2.2 cm of 2100 scenario spread and the 1942-1982
    # miss -- before any "improvement" it reports means anything.
    # g = 0 is BRICK's actual initial condition: SIMPLE starts at V(1850) = v0,
    # i.e. ZERO realised loss and a full v0 - V_eq(T_1850) = 71 cm of
    # disequilibrium already present. Starting it in equilibrium (g = 1) makes
    # the modern rate 0.11 mm/yr instead of ~0.7 and fails the acceptance test.
    "incumbent": dict(rate_driver="gmst", leq="linear", two_channel=False,
                      fixed=dict(c1=15.785, c0=71.360, alpha=1.330e-4,
                                 beta=5.710e-4, g=0.0)),
    "stock":    dict(rate_driver="gmst", leq="linear", two_channel=False),
    "A":        dict(rate_driver="regional", leq="linear", two_channel=False),
    "B":        dict(rate_driver="gmst", leq="linear", two_channel="share"),
    "A+B":      dict(rate_driver="regional", leq="linear", two_channel="share"),
    "A+B'":     dict(rate_driver="regional", leq="linear", two_channel="smbrate"),
    "A+B+C":    dict(rate_driver="regional", leq="ladder", two_channel="share"),
    "A+B'+C":   dict(rate_driver="regional", leq="ladder", two_channel="smbrate"),
    # OPTION D, 2026-08-16. Throughput-capped relaxation (see _throughput). Each
    # nests its C counterpart exactly at q = CAP_INERT_CM_YR, so by the file's
    # nesting discipline neither can score worse than the cell it contains.
    "A+B+C+D":  dict(rate_driver="regional", leq="ladder", two_channel="share",
                     cap=("q_f", "q_s")),
    "A+B'+C+D": dict(rate_driver="regional", leq="ladder", two_channel="smbrate",
                     cap=("q_s",)),
}

# Bounds are wide on purpose: a rail means the fit left the feasible set, which
# is information, and every rail is reported. 1/tau in [1e-6, 0.2] spans
# e-folding times from 5 yr to 1e6 yr.
PBOUNDS = {
    "c1": (0.0, 400.0), "c0": (-200.0, 400.0),
    "alpha": (0.0, 0.2), "beta": (1e-6, 0.2),
    "alpha_f": (0.0, 0.5), "beta_f": (1e-6, 0.5),
    "alpha_s": (0.0, 0.2), "beta_s": (1e-6, 0.2),
    "f": (0.02, 0.98), "dT": (DT_PRIOR["lo"], DT_PRIOR["hi"]),
    # SMB-rate channel: cm SLE per year per degree above a melt-onset anomaly.
    "k_smb": (0.0, 2.0), "t_on": (-2.0, 4.0),
    # Fraction of the 1850 commitment already realised at 1850. The linear cells
    # get this freedom through c0; the ladder cell has no free level parameter,
    # so without g it is forced to start 20-200 cm out of equilibrium and cannot
    # fit the hindcast at all. Same freedom for every cell, so the comparison is
    # like-for-like.
    "g": (0.0, 1.0),
    # OPTION D throughput caps, cm SLE per year, per channel. The floor is far
    # below the observed modern total rate (0.0841 cm/yr) and the ceiling is
    # CAP_INERT_CM_YR, at which the cap is provably inert -- no annual increment
    # can exceed L_eq <= V0_CM -- so the D cells nest the C cells EXACTLY.
    "q_f": (1e-4, V0_CM), "q_s": (1e-4, V0_CM),
}


# Nested warm starts. Each cell here CONTAINS the named one as a special case, so
# the container's optimum can never be worse and the simpler cell's solution is a
# guaranteed-good start. Enforcing this by construction is what finally made the
# two-channel fits reproducible: multi-start alone returned B at 234.92 on one run
# and 245.06 on the next, both above the 234.92 that stock -- which B nests -- had
# already achieved. NEST_MAP[cell] = (simpler cell, how to lift its parameters).
#   stock -> B / A -> A+B : one channel becomes two identical channels, and the
#   Mouginot share of two identical channels is exactly f, so f = the observed
#   share makes the extra penalty term zero at the lifted point.
def _lift_one_to_two(p):
    q = dict(p)
    q["f"] = MOUG_SURFACE_SHARE
    q["alpha_f"] = q["alpha_s"] = p["alpha"]
    q["beta_f"] = q["beta_s"] = p["beta"]
    del q["alpha"], q["beta"]
    return q


def _lift_uncapped(p):
    """Lift a C cell into its C+D container by switching the caps OFF. At
    CAP_INERT_CM_YR no annual increment can reach the cap, so the lifted point
    reproduces the C cell BIT-FOR-BIT and D's optimum cannot be worse. This is
    the whole reason D is expressed as a cap on the existing flux rather than as
    a replacement rate law -- it keeps the nesting, so a D-versus-C score
    difference is attributable to the cap and to nothing else."""
    return dict(p, q_f=CAP_INERT_CM_YR, q_s=CAP_INERT_CM_YR)


NEST_MAP = {"B": ("stock", _lift_one_to_two), "A+B": ("A", _lift_one_to_two),
            "A+B+C+D": ("A+B+C", _lift_uncapped),
            "A+B'+C+D": ("A+B'+C", _lift_uncapped)}


def cell_params(cell):
    s = CELLS[cell]
    if "fixed" in s:
        return []
    p = ["c1", "c0"] if s["leq"] == "linear" else ["dT"]
    if s["two_channel"] == "smbrate":
        p += ["k_smb", "t_on", "alpha_s", "beta_s"]
    elif s["two_channel"]:
        p += ["f", "alpha_f", "beta_f", "alpha_s", "beta_s"]
    else:
        p += ["alpha", "beta"]
    return p + ["g"] + list(s.get("cap", ()))


def run_cell(cell, theta, t_reg, t_gmst, n=None):
    s = CELLS[cell]
    p = dict(s["fixed"]) if "fixed" in s else dict(zip(cell_params(cell), theta))
    t_rate = t_reg if s["rate_driver"] == "regional" else t_gmst
    leq = (np.clip(p["c1"] * t_rate + p["c0"], 0.0, V0_CM) if s["leq"] == "linear"
           else leq_ladder(t_gmst, p["dT"]))
    return integrate(t_rate, leq, p, s["two_channel"], n)


# Last index any fit-time term reads: the target's final year.
N_FIT = _yi[FIT_WIN[1]] + 1


def reref(L, win=REF_WIN):
    i = [_yi[y] for y in range(win[0], win[1] + 1)]
    return L - L[i].mean()


# =============================================================================
# objective
# =============================================================================
def neg_log_post(cell, theta, ctx):
    p = dict(zip(cell_params(cell), theta))
    for k, v in p.items():
        lo, hi = PBOUNDS[k]
        if not (lo <= v <= hi):
            return 1e12
    if "fixed" in CELLS[cell]:
        p = dict(CELLS[cell]["fixed"])
    L, Lf = run_cell(cell, theta, ctx["t_reg"], ctx["t_gmst"], N_FIT)
    if not np.all(np.isfinite(L)):
        return 1e12
    mdl = reref(L)[ctx["ti"]]
    nlp = 0.5 * float(np.sum(((mdl - ctx["obs"]) / ctx["sig"]) ** 2))
    if CELLS[cell]["two_channel"]:
        share = model_surface_share(L, Lf)
        if np.isfinite(share):
            nlp += 0.5 * ((share - MOUG_SURFACE_SHARE) / MOUG_SHARE_SIGMA) ** 2
    if "dT" in p:
        nlp += 0.5 * ((p["dT"] - DT_PRIOR["mu"]) / DT_PRIOR["sigma"]) ** 2
    return nlp


def model_surface_share(L, Lf):
    """The model's fast-channel share of the EXTRA loss rate, matched to how the
    Mouginot number was computed (late-period rate minus reference-period rate)."""
    def rate(x, win):
        i0, i1 = _yi[win[0]], _yi[win[1]]
        return (x[i1] - x[i0]) / (win[1] - win[0])
    d_tot = rate(L, MOUG_LATE_WIN) - rate(L, MOUG_REF_WIN)
    d_fast = rate(Lf, MOUG_LATE_WIN) - rate(Lf, MOUG_REF_WIN)
    return d_fast / d_tot if abs(d_tot) > 1e-12 else np.nan


def draw_start(names):
    """Uniform on the level axes, LOG-uniform on the rate axes. A rate bound of
    [1e-6, 0.2] drawn uniformly puts 99.9995% of the mass above 1e-6 * 1e3, so
    the linear draw never explored the slow end at all."""
    x = np.empty(len(names))
    for i, n in enumerate(names):
        lo, hi = PBOUNDS[n]
        if n == "dT":
            x[i] = np.clip(DT_PRIOR["mu"] + _rng.normal(0, DT_PRIOR["sigma"]),
                           DT_PRIOR["lo"], DT_PRIOR["hi"])
        elif n in LOG_AXES:
            x[i] = np.exp(_rng.uniform(np.log(max(lo, 1e-6)), np.log(hi)))
        else:
            x[i] = _rng.uniform(lo, hi)
    return x


def _nm(obj, x0, maxfev, tol=1e-9):
    return minimize(obj, x0, method="Nelder-Mead",
                    options=dict(maxiter=maxfev, maxfev=maxfev,
                                 xatol=tol, fatol=tol))


def polish(obj, x, maxfev=MAXFEV):
    """Restart NM from its own answer until it stops improving. One NM call is
    not a converged minimisation on this objective; the simplex degenerates."""
    v = obj(x)
    for _ in range(POLISH_ROUNDS):
        r = _nm(obj, x, maxfev, tol=1e-11)
        if not (r.fun < v - POLISH_TOL):
            return (r.x, r.fun) if r.fun < v else (x, v)
        x, v = r.x, r.fun
    return x, v


def basin_polish(obj, x, names, maxfev=MAXFEV):
    """Basin hopping around the incumbent best: jitter, re-minimise, keep any
    improvement. Multi-start alone kept landing in the wrong basin on the
    two-channel cells -- the first corrected run still had B and A+B' beaten by
    their own constrained ridge points, by 2.74 and 1.73 nlp units. Jitter is
    MULTIPLICATIVE on the rate axes because those span decades."""
    x, v = polish(obj, x, maxfev)
    for _ in range(BASIN_ROUNDS):
        y = np.array(x, float)
        for i, n in enumerate(names):
            lo, hi = PBOUNDS[n]
            if n in LOG_AXES:
                y[i] = float(np.clip(y[i] * np.exp(_rng.normal(0, BASIN_LOG_SD)), lo, hi))
            else:
                y[i] = float(np.clip(y[i] + _rng.normal(0, BASIN_LIN_FRAC * (hi - lo)), lo, hi))
        r = _nm(obj, y, maxfev)
        if r.fun < v - POLISH_TOL:
            x, v = polish(obj, r.x, maxfev)
    return x, v


def fit_cell(cell, ctx, extra_starts=()):
    names = cell_params(cell)
    if not names:                       # the fixed-parameter acceptance cell
        return dict(CELLS[cell]["fixed"]), neg_log_post(cell, [], ctx)
    obj = lambda t: neg_log_post(cell, t, ctx)
    best, best_v = None, np.inf
    starts = [np.asarray(s, float) for s in extra_starts]
    starts += [draw_start(names) for _ in range(N_MULTISTART)]
    for x0 in starts:
        r = _nm(obj, x0, MAXFEV)
        if r.fun < best_v:
            best, best_v = r.x, r.fun
    best, best_v = basin_polish(obj, best, names)
    return dict(zip(names, best)), best_v


# =============================================================================
# gates + projection
# =============================================================================
def evaluate_gates(L, ctx):
    mdl = reref(L)
    i0, i1 = _yi[GATE_RATE_WIN[0]], _yi[GATE_RATE_WIN[1]]
    rate = (mdl[i1] - mdl[i0]) / (GATE_RATE_WIN[1] - GATE_RATE_WIN[0]) * 10.0  # cm->mm
    g1 = abs(rate - GATE_RATE_OBS_MMYR) <= GATE_RATE_TOL_FRAC * GATE_RATE_OBS_MMYR

    m = (ctx["ty"] >= GATE_MIDCEN_WIN[0]) & (ctx["ty"] <= GATE_MIDCEN_WIN[1])
    bias = float(np.mean(mdl[ctx["ti"]][m] - ctx["obs"][m]))
    g2 = abs(bias) < GATE_MIDCEN_TOL_CM

    yy = ctx["ty"][m]
    mr = np.gradient(mdl[ctx["ti"]][m])
    trend = float(np.polyfit(yy, mr, 1)[0])
    g3 = (trend < 0) if GATE_SHAPE_REQUIRE_NEGATIVE_TREND else True

    rmse = float(np.sqrt(np.mean((mdl[ctx["ti"]] - ctx["obs"]) ** 2)))
    return dict(rate_mmyr=rate, gate1_rate=g1, midcen_bias_cm=bias, gate2_midcen=g2,
                midcen_rate_trend=trend, gate3_shape=g3, rmse_cm=rmse)


def splice_regional(t_reg_obs, gmst_hist, gmst_scen, last_obs_year):
    """Anchor-preserving splice, the same construction as ladrillo_projection.jl:
    observed regional temperature through last_obs_year, then AMP_MEAN * GMST
    offset so the two agree in the mean over the last SPLICE_ANCHOR_YEARS."""
    anchor = np.arange(last_obs_year - SPLICE_ANCHOR_YEARS + 1, last_obs_year + 1)
    ai = [_yi[y] for y in anchor]
    off = t_reg_obs[ai].mean() - AMP_MEAN * gmst_hist[ai].mean()
    out = t_reg_obs.copy()
    fut = YEARS > last_obs_year
    out[fut] = AMP_MEAN * gmst_scen[fut] + off
    return out


def project(cell, theta, t_reg_obs, gmst_hist, last_obs_year):
    out = {}
    for label, tag in PROJ_SCENARIOS.items():
        g = extend(load_gmst(tag))
        tr = splice_regional(t_reg_obs, gmst_hist, g, last_obs_year)
        L, _ = run_cell(cell, theta, tr, g)
        out[label] = reref(L, PROJ_REF_WIN)[_yi[PROJ_YEAR]]
    return out


# =============================================================================
# separability
# =============================================================================
def ridge_profile(cell, theta, ctx, ax1, ax2):
    """Profile the objective over two parameters, re-optimising the rest. A
    ridge shows up as a long valley: the two are not separately identified.

    CORRECTED 2026-08-12 along with fit_cell. Each grid point is now seeded at
    the converged optimum and restarted, instead of running one weak NM from a
    fixed base -- the old version's point-to-point scatter was +/-6 nlp units,
    itself larger than the RIDGE_DELTA = 2.30 threshold being applied to it.
    The grid is still LOCAL by construction (see RIDGE_LOCAL_*), so read a
    "flat over 100% of the range" verdict as a statement about that window and
    nothing wider: for the A+B beta_f axis the window is 1e-6 to 3e-5, while
    the value the fit is flat against a literature SMB rate over spans four
    more decades. python/diag_gis_g_betaf.py profiles the full prior range."""
    names = cell_params(cell)
    if ax1 not in names or ax2 not in names:
        return None
    i1, i2 = names.index(ax1), names.index(ax2)
    base = np.array([theta[n] for n in names])
    # LOCAL grids around the optimum. Spanning the full bounds put the whole
    # 1-unit region inside one grid cell and reported an uninformative "0%".
    lo1, hi1 = PBOUNDS[ax1]
    half = RIDGE_LOCAL_FRAC * (hi1 - lo1)
    g1 = np.linspace(max(lo1, theta[ax1] - half), min(hi1, theta[ax1] + half), RIDGE_N)
    b2 = max(theta[ax2], 1e-6)
    g2 = np.geomspace(max(PBOUNDS[ax2][0], b2 / RIDGE_LOCAL_DECADES),
                      min(PBOUNDS[ax2][1], b2 * RIDGE_LOCAL_DECADES), RIDGE_N)
    free = [i for i in range(len(names)) if i not in (i1, i2)]
    free_names = [names[i] for i in free]
    rows = []
    for v1 in g1:
        for v2 in g2:
            def obj(fx):
                t = base.copy()
                t[i1], t[i2] = v1, v2
                t[free] = fx
                return neg_log_post(cell, t, ctx)
            starts = [base[free]] + [draw_start(free_names)
                                     for _ in range(RIDGE_RESTARTS)]
            bx, bv = None, np.inf
            for x0 in starts:
                r = _nm(obj, x0, RIDGE_MAXFEV)
                if r.fun < bv:
                    bx, bv = r.x, r.fun
            bx, bv = polish(obj, bx, maxfev=RIDGE_MAXFEV)
            full = base.copy()
            full[i1], full[i2] = v1, v2
            full[free] = bx
            rows.append(dict(cell=cell, ax1=ax1, ax2=ax2, v1=v1, v2=v2, nlp=bv,
                             params="; ".join(f"{n}={full[k]:.9g}"
                                              for k, n in enumerate(names))))
    return pd.DataFrame(rows)


# =============================================================================
def main():
    print(f"gis_offline_cell | commit={COMMIT} | zone={DRIVER_ZONE} | "
          f"fit {FIT_WIN[0]}-{FIT_WIN[1]}")
    share_obs = mouginot_surface_share()
    assert abs(share_obs - MOUG_SURFACE_SHARE) < 0.01, \
        f"Mouginot surface share {share_obs:.3f} != the constant {MOUG_SURFACE_SHARE}"
    print(f"  Mouginot surface share verified from file: {share_obs:.3f}")

    drv = pd.read_csv(DRIVER_CSV).set_index("year")[DRIVER_ZONE]
    last_obs_year = int(drv.index.max())
    t_reg = extend(drv)
    gmst_hist = extend(load_gmst())
    ty, obs, sig = load_target()
    ctx = dict(t_reg=t_reg, t_gmst=gmst_hist, ty=ty, obs=obs, sig=sig,
               ti=[_yi[y] for y in ty])
    print(f"  driver {DRIVER_ZONE} {drv.index.min()}-{last_obs_year}; "
          f"target {ty[0]}-{ty[-1]} ({len(ty)} yr)")
    print(f"\n  PRE-REGISTERED GATES")
    print(f"    G1 modern rate  {GATE_RATE_WIN}: {GATE_RATE_OBS_MMYR} mm/yr "
          f"+/-{GATE_RATE_TOL_FRAC:.0%}")
    print(f"    G2 {GATE_MIDCEN_WIN} mean |bias| < {GATE_MIDCEN_TOL_CM} cm")
    print(f"    G3 {GATE_MIDCEN_WIN} melt-rate trend negative")
    print(f"    G4 EVAL ONLY 2100 spread in {GATE_SPREAD_RANGE_CM} cm "
          f"(Ladrillo extC today: 2.16)")

    def summarise(cell, theta, nlp):
        order = [theta[n] for n in cell_params(cell)]
        L, Lf = run_cell(cell, order, t_reg, gmst_hist)
        g = evaluate_gates(L, ctx)
        proj = project(cell, order, t_reg, gmst_hist, last_obs_year)
        spread = proj["SSP5-8.5"] - proj["SSP1-2.6"]
        share = model_surface_share(L, Lf) if CELLS[cell]["two_channel"] else np.nan
        rails = "|".join(n for n in cell_params(cell)
                         if abs(theta[n] - PBOUNDS[n][0]) < 1e-9
                         or abs(theta[n] - PBOUNDS[n][1]) < 1e-9)
        row = dict(cell=cell, n_par=len(theta), neg_log_post=nlp, railed=rails, **g,
                   surface_share=share, spread_2100_cm=spread,
                   gate4_spread=GATE_SPREAD_RANGE_CM[0] <= spread
                   <= GATE_SPREAD_RANGE_CM[1],
                   **{f"proj_{k}": v for k, v in proj.items()},
                   params="; ".join(f"{k}={v:.6g}" for k, v in theta.items()))
        return row, reref(L)

    rows, series, ridges, solved = [], {"year": YEARS}, [], {}
    for cell in CELLS:
        warm = []
        if cell in NEST_MAP:
            simpler, lift = NEST_MAP[cell]
            if simpler in solved:
                q = lift(solved[simpler])
                warm = [[q[n] for n in cell_params(cell)]]
        theta, nlp = fit_cell(cell, ctx, extra_starts=warm)
        row, hind = summarise(cell, theta, nlp)
        rows.append(row)
        solved[cell] = theta
        series[f"{cell}_hindcast_cm"] = hind
        print(f"  fitted {cell:8s} nlp={nlp:10.1f}  rmse={row['rmse_cm']:.3f} cm  "
              f"spread={row['spread_2100_cm']:5.2f} cm"
              + (f"   [warm start from {NEST_MAP[cell][0]}]" if warm else ""))

        cell_ridges = []
        for ax1, ax2 in (("f", "beta_f"), ("k_smb", "beta_s"), ("dT", "beta_s")):
            r = ridge_profile(cell, theta, ctx, ax1, ax2)
            if r is not None:
                cell_ridges.append(r)
        ridges += cell_ridges

        # REPAIR PASS. Every ridge point is a constrained fit, so any point that
        # scores below the optimum is a WITNESS that the optimum is not one. Use
        # it as a start rather than only asserting on it -- the assert in
        # convergence_check() then fires only when the repair also fails.
        if cell_ridges:
            # reset_index: two ridges on one cell (A+B+C has both) concatenate to
            # duplicate labels, and .loc on a duplicated label returns a frame.
            allr = pd.concat(cell_ridges).reset_index(drop=True)
            best = allr.loc[allr.nlp.idxmin()]
            if best.nlp < nlp - REPAIR_TOL:
                x0 = [float(kv.split("=")[1]) for kv in best.params.split("; ")]
                print(f"    repair {cell:8s} a ridge point scored {best.nlp:.4f} "
                      f"< {nlp:.4f}; refitting from it")
                theta, nlp = fit_cell(cell, ctx, extra_starts=[x0] + warm)
                row, hind = summarise(cell, theta, nlp)
                rows[-1], series[f"{cell}_hindcast_cm"] = row, hind
                solved[cell] = theta
                print(f"    repair {cell:8s} nlp={nlp:10.4f}  rmse={row['rmse_cm']:.3f} cm  "
                      f"spread={row['spread_2100_cm']:5.2f} cm")

    fit = pd.DataFrame(rows)
    fit.to_csv(OUT_FITS, index=False)
    pd.DataFrame(series).to_csv(OUT_SERIES, index=False, float_format="%.9g")
    if ridges:
        pd.concat(ridges).to_csv(OUT_RIDGE, index=False, float_format="%.9g")

    report(fit, ridges)
    make_figure(series, ctx, fit)
    for p in (OUT_FITS, OUT_SERIES, OUT_RIDGE, OUT_FIG):
        print(f"wrote {os.path.relpath(p, REPO)}")


def convergence_check(fit, ridges):
    """THE INVARIANT THAT CAUGHT THE ORIGINAL BUG, now enforced every run.

    A ridge point fixes two parameters and re-optimises the rest, so its score
    can never be below the unconstrained optimum. If it is, the reported
    optimum is not one. Tolerance is the inner optimiser's own scatter."""
    # Nesting: a container cell's optimum can never exceed the cell it nests
    # (see NEST_MAP). Free, and independent of the ridge check below.
    print(f"\nNESTING CHECK -- a container cell cannot score above the cell it nests")
    nest_bad = 0.0
    for cell, (simpler, _) in NEST_MAP.items():
        got = fit.loc[fit.cell == cell, "neg_log_post"]
        ref = fit.loc[fit.cell == simpler, "neg_log_post"]
        if got.empty or ref.empty:
            continue
        gap = float(got.iloc[0]) - float(ref.iloc[0])
        nest_bad = max(nest_bad, gap)
        print(f"  {cell:10s} {float(got.iloc[0]):10.4f}  <=  {simpler:8s} "
              f"{float(ref.iloc[0]):10.4f}   gap {gap:+8.4f}  "
              f"{'OK' if gap <= REPAIR_TOL else 'NOT CONVERGED'}")
    assert nest_bad <= REPAIR_TOL, (
        f"a nested cell beat its container by {nest_bad:.4f} nlp units -- "
        f"the container's fit has not converged")

    if not ridges:
        return
    tol = REPAIR_TOL
    worst = 0.0
    print(f"\nCONVERGENCE CHECK -- no constrained ridge point may beat the optimum")
    for cell, grp in pd.concat(ridges).groupby("cell"):
        opt = float(fit.loc[fit.cell == cell, "neg_log_post"].iloc[0])
        gap = opt - float(grp.nlp.min())
        worst = max(worst, gap)
        print(f"  {cell:10s} optimum {opt:10.4f}  best ridge point {grp.nlp.min():10.4f}  "
              f"gap {gap:+8.4f}  {'OK' if gap <= tol else 'NOT CONVERGED'}")
    assert worst <= tol, (
        f"a constrained ridge point beat the reported optimum by {worst:.4f} nlp "
        f"units -- the fit has not converged; see the fitting-protocol note")


def report(fit, ridges):
    convergence_check(fit, ridges)
    print(f"\nFIT QUALITY AND GATES")
    print(f"  {'cell':10s} {'npar':>4s} {'RMSE cm':>8s} {'rate':>7s} {'G1':>3s} "
          f"{'bias cm':>8s} {'G2':>3s} {'trend':>9s} {'G3':>3s} {'surf':>6s}  railed")
    for _, r in fit.iterrows():
        yn = lambda b: "OK" if b else "--"
        sh = f"{r.surface_share:6.2f}" if np.isfinite(r.surface_share) else "     -"
        print(f"  {r.cell:10s} {r.n_par:4d} {r.rmse_cm:8.3f} {r.rate_mmyr:7.3f} "
              f"{yn(r.gate1_rate):>3s} {r.midcen_bias_cm:+8.3f} {yn(r.gate2_midcen):>3s} "
              f"{r.midcen_rate_trend:+9.2e} {yn(r.gate3_shape):>3s} {sh}  {r.railed}")

    print(f"\nG4 EVALUATION ONLY -- 2100 GIS, cm rel {PROJ_REF_WIN[0]}-{PROJ_REF_WIN[1]}")
    print(f"  {'cell':10s} " + "".join(f"{s:>11s}" for s in PROJ_SCENARIOS) +
          f"{'spread':>9s} {'G4':>4s}")
    for _, r in fit.iterrows():
        print(f"  {r.cell:10s} " +
              "".join(f"{r['proj_' + s]:11.2f}" for s in PROJ_SCENARIOS) +
              f"{r.spread_2100_cm:9.2f} {'OK' if r.gate4_spread else '--':>4s}")
    print(f"  targets: MAGICC-SLR 7.09, FACTS FittedISMIP 6.34, emuGrIS 7.26, "
          f"bamber19 7.23; Ladrillo extC today 2.16")

    print(f"\nSEPARABILITY -- pre-registered question: do the fast fraction and the "
          f"fast\n  timescale identify jointly, or ride a ridge?")
    for r in ridges:
        cell = r.cell.iloc[0]
        best = r.loc[r.nlp.idxmin()]
        # width of the region within 1 unit of nlp (~1 sigma) along each axis
        near = r[r.nlp <= best.nlp + RIDGE_DELTA]
        w1 = (near.v1.max() - near.v1.min()) / (r.v1.max() - r.v1.min())
        w2 = (np.log10(near.v2.max()) - np.log10(near.v2.min())) / \
             (np.log10(r.v2.max()) - np.log10(r.v2.min()))
        corr = (np.corrcoef(near.v1, np.log10(near.v2))[0, 1]
                if len(near) > 3 and near.v1.nunique() > 1 else np.nan)
        verdict = ("RIDGE" if (np.isfinite(corr) and abs(corr) > 0.7
                               and min(w1, w2) > 0.25) else
                   "identified" if max(w1, w2) < 0.5 else "weakly identified")
        print(f"  {cell:8s} {best.ax1}-{best.ax2}: best ({best.v1:.3f}, "
              f"{best.v2:.2e})  d<{RIDGE_DELTA} region spans {w1:.0%} of the "
              f"{best.ax1} axis, {w2:.0%} of log10 {best.ax2}, corr {corr:+.2f}"
              f"  -> {verdict}")
    print(f"  ridge = wide region (>25% of both local axes) with |corr| > 0.7; "
          f"grids are LOCAL around each optimum")


def make_figure(series, ctx, fit):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    t = pd.read_csv(TARGETS_CSV).set_index("year")
    g = t[["gis", "gis_lo", "gis_hi"]].dropna().loc[FIT_WIN[0]:FIT_WIN[1]]
    s = pd.DataFrame(series).set_index("year")
    style = {c: dict(color=col, ls=ls, lw=lw) for c, col, ls, lw in [
        ("incumbent", "C6", "--", 2.2), ("stock", "0.55", "-", 1.3),
        ("A", "C0", "-", 1.8), ("B", "C1", "-", 1.3), ("A+B", "C2", "-", 2.0),
        ("A+B'", "C4", "-", 1.8), ("A+B+C", "C3", ":", 1.3),
        ("A+B'+C", "C5", ":", 1.3)]}

    fig, axes = plt.subplots(1, 3, figsize=(18, 5.4))
    for ax, (x0, x1) in zip(axes[:2], [FIT_WIN, GATE_MIDCEN_WIN]):
        ax.fill_between(g.index, g.gis_lo, g.gis_hi, color="0.85",
                        label="Frederikse GIS target, 90%")
        ax.plot(g.index, g.gis, "k-", lw=2.4, label="target", zorder=6)
        for cell in CELLS:
            ax.plot(s.index, s[f"{cell}_hindcast_cm"], label=cell, **style[cell])
        ax.axvspan(*GATE_MIDCEN_WIN, color="tab:blue", alpha=0.07, zorder=0)
        ax.set_xlim(x0, x1)
        seg = g.loc[x0:x1]
        pad = 0.35 * (seg.gis_hi.max() - seg.gis_lo.min())
        ax.set_ylim(seg.gis_lo.min() - pad, seg.gis_hi.max() + pad)
        ax.set_xlabel("year")
        ax.set_ylabel(f"GIS contribution, cm rel {REF_WIN[0]}-{REF_WIN[1]}")
        ax.grid(alpha=0.3)
    axes[0].set_title(f"Greenland offline cell -- hindcast, driver = {DRIVER_ZONE} "
                      f"({FIT_WIN[0]}-{FIT_WIN[1]})")
    axes[1].set_title(f"the {GATE_MIDCEN_WIN[0]}-{GATE_MIDCEN_WIN[1]} gate window "
                      f"(G2 tol {GATE_MIDCEN_TOL_CM} cm)")
    axes[0].legend(fontsize=7.5, ncol=2, loc="upper left")

    ax = axes[2]
    cells = [c for c in CELLS]
    x = np.arange(len(cells))
    sp = [float(fit[fit.cell == c].spread_2100_cm.iloc[0]) for c in cells]
    cols = ["C3" if v > GATE_SPREAD_RANGE_CM[1] or v < GATE_SPREAD_RANGE_CM[0]
            else "C2" for v in sp]
    ax.bar(x, sp, color=cols)
    ax.axhspan(*GATE_SPREAD_RANGE_CM, color="C2", alpha=0.15,
               label=f"FACTS / MAGICC band {GATE_SPREAD_RANGE_CM}")
    for xi, v in zip(x, sp):
        ax.text(xi, min(v, 20) + 0.4, f"{v:.1f}", ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(cells, rotation=30, ha="right", fontsize=8)
    ax.set_ylim(0, 20)
    ax.set_ylabel(f"{PROJ_YEAR} SSP1-2.6 -> SSP5-8.5 spread, cm")
    ax.set_title(f"G4 EVALUATION ONLY -- {PROJ_YEAR} scenario spread\n"
                 f"(bars above 20 cm are clipped; C cells reach 52 and 13)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(OUT_FIG, dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    main()
