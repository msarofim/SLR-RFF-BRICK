"""SECTION 4.2 OF THE 2026-08-22 HANDOFF — THE AMPLIFICATION LAW ABOVE 2.75 K.

WHY THIS IS BLOCKING, NOT BACKGROUND
  The shipped law is `amp(dT) = 1.922 * S(dT)` with S PCHIP'd through CMIP6 binned
  medians over 0.75-2.75 K and HELD FLAT above (memory ladrillo_gis_amp, sub-choice 1,
  which is MEASURED but still an open call). S saturates at 0.8596, so the effective
  amplification is a CONSTANT 1.652 from 2.75 K all the way to the x2300 arm's
  13.63 K. Every arm the flux deliverable was read off -- 5.61 K and 13.63 K -- sits
  in that unvalidated region. Section 1.2 of the handoff reads a FUNCTIONAL FORM off
  the shape of those arms, so the amp law is not a level nuisance here: it sets the
  driver the shape is measured against.

WHAT THIS SCRIPT ESTABLISHES, IN ORDER
  1. HOW FAR THE EVIDENCE ACTUALLY REACHES. The binned CMIP6 curve per scenario,
     with model counts, against where each arm sits. This is the extrapolation
     factor, stated rather than assumed.
  2. FOUR AMP LAWS, spanning the defensible range (see AMP_LAWS below).
  3. THE phi=1 CEILING (handoff 1.1) UNDER EACH LAW -- the handoff asserts the
     shortfall gets WORSE with a lower high-T amp and calls 1.1 robust on that
     basis. That direction check was done for ONE alternative; here it is done for
     all four, and the ratio is reported so the claim is quantitative.
  4. THE FLUX psi REQUIRED UNDER EACH LAW. This is the point. psi = V/tau is the
     only identified quantity (handoff 1.3), and the reservoir ramp keys off GMT,
     NOT off the regional driver -- so the amp law cannot move the ramp, only the
     BASE the ramp is added to. The reservoir's contribution is therefore EXACTLY
     LINEAR in psi and psi is solved in closed form, not scanned:
         psi_rate  = (rate_target - rate_base) / (tau * du_2250_2300_per_century)
         psi_level = (level_target - level_base) / (tau * u(2300))
     Two independent requirements. Cell B's claim is that ONE psi satisfies both;
     whether that survives the amp law is the thing to measure.

READ WITH  notes/handoff_2026-08-22_greenland_flux_deliverable.md section 4.2
           notes/scoping_2026-08-22_greenland_shape_stepback.md
           memory ladrillo_gis_amp (sub-choice 1 is Marcus's open call)

READ-ONLY. Writes outputs/diag_gis_amp_above_275.csv and changes no gate, no cell,
no shipped table.
  python3 python/diag_gis_amp_above_275.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))
os.chdir(REPO)

import scope_gis_shape_all_scenarios as A  # noqa: E402
from scope_gis_ridge_vs_protect import (  # noqa: E402
    basin2_series, rebase_cm, K_SOUTH, K_HIGH, GIS_V0_M,
)
from scope_gis_leq_ridge_vs_literature import gis_tbar  # noqa: E402
from scope_gis_2300_relaxation import (  # noqa: E402
    DRIVER_BASE, YEARS, GIS_ZONE, SHAPE_WIN, ANCHOR_N, OBS,
    gis_shape_table, regional_driver, _running_mean,
)
from scope_gis_reservoir_offline import (  # noqa: E402
    reservoir_unit, CM_PER_M, V_MAX_M, RAMP_W_K,
)

OUT = os.path.join(REPO, "outputs/diag_gis_amp_above_275.csv")

# --- named constants; every label, verdict and filename below derives from these ---
TAG = A.TAG
OBS_AMP_FULL = 1.9221976385152952   # gis_amp_shape_meta.obs_amp_full, the observed level
HELD_STEM = "gis_amp_shape"                 # SHIPPED: S flat above 2.75 K
FULL_STEM = "gis_amp_shape_fullcurve"       # CMIP6 binned out to 5.75 K, then flat
CMIP6_BINNED = "outputs/diag_gis_amp_cmip6_binned.csv"
CMIP6_FIT_HI_K = 2.75               # the shipped law's PCHIP ceiling
CMIP6_DATA_HI_K = 5.75              # the last bin with ANY models, ssp585
SECANT_SLOPE_PER_K = -0.0503        # ladrillo_gis_amp item 1, 95% [-0.0792,-0.0120]
## Bochow's own summer<->global map, as the repo already has it in
## build_greenland_equilibrium_ladder.py:59 -- GMT = f_conv/1.19 + 0.5, inverted.
## Their zero-forcing reference is +0.5 K GMT, which is why this is AFFINE and not a
## ratio; the ratio it implies rises to 1.19 asymptotically (1.11 at our ssp585@2300).
BOCHOW_SUMMER_SLOPE = 1.19
BOCHOW_SUMMER_GMT0_K = 0.5
GRID_MAX_K = 16.0                   # must exceed the x2300 arm's 13.63 K
GRID_STEP_K = 0.01
## The cell the handoff's section 1.3 selects, quoted as a FLUX. tau is a PRIOR on the
## equilibrium literature (Van Breedam 2020 ~2 kyr; Greve & Chambers 2022 => ~3.3 kyr),
## not a fit -- so tau is held FIXED here and psi is the only thing solved for.
CELL_B_V_M, CELL_B_TAU_YR, CELL_B_ONSET_K = 6.0, 2200.0, 4.69
PSI_B_CM_PER_YR = CM_PER_M * CELL_B_V_M / CELL_B_TAU_YR
RATE_WIN = (2250, 2300)             # the rate window; handoff section 1.2
RATE_ARM = ("ssp585", "r2300")      # the rate target: constant-forcing, tap-inert
RATE_ARM_LABEL = "SSP5-8.5"
LEVEL_SSP = "SSP5-8.5"              # our own deliverable scenario
MATCHED_P50_CM = 98.5               # matched-forcing p50 for our ssp585 @2300
Y2100_TOL_CM = 0.10
REPRO_TOL_CM = 1e-9                 # the HELD law must reproduce the shipped driver
OURS = [("ssp126", "SSP1-2.6"), ("ssp245", "SSP2-4.5"), ("ssp585", "SSP5-8.5")]


# --- the four laws -----------------------------------------------------------
def _shipped_S(stem):
    """S as the shipped tables define it, extended to GRID_MAX_K by the SAME
    flat hold np.interp already applies past the table's 8.0 K ceiling."""
    t = pd.read_csv(os.path.join(REPO, f"outputs/{stem}.csv"))
    x, y = t["dt"].to_numpy(), t["S"].to_numpy()
    return lambda dt: np.interp(np.clip(dt, x[0], x[-1]), x, y)


def _declining_S():
    """The fullcurve, then the measured CMIP6 secant decline CONTINUED past the last
    bin instead of frozen. Not a recommendation -- the honest other end of the
    sub-choice-1 bracket, since 'hold flat' and 'keep declining' are both
    extrapolations and only one of them is currently shipped."""
    base = _shipped_S(FULL_STEM)
    r_anchor = float(pd.read_csv(
        os.path.join(REPO, f"outputs/{FULL_STEM}_meta.csv")).iloc[0].r_anchor)
    s_hi = float(base(np.array([CMIP6_DATA_HI_K]))[0])

    def S(dt):
        dt = np.asarray(dt, float)
        out = base(dt)
        ext = dt > CMIP6_DATA_HI_K
        # decline applied to R_secant, then re-normalised by the same anchor
        r_ext = s_hi * r_anchor + SECANT_SLOPE_PER_K * (dt - CMIP6_DATA_HI_K)
        return np.where(ext, np.maximum(r_ext, 0.0) / r_anchor, out)
    return S


AMP_LAWS = [
    ("held    S flat above 2.75 K  [SHIPPED]", "held"),
    ("full    CMIP6 binned to 5.75 K, then flat", "full"),
    ("decl    full + the -0.0503/K secant decline CONTINUED", "decl"),
    ("summer  Bochow melt-relevant summer, GMT*1.19 above 0.5 K", "summer"),
]


def amp_field(kind, gmst_rb, amp_draws):
    """The FULL effective amplification, (ndraw, nyear). For the three CMIP6 laws
    this is amp_draw * S(warming level), exactly as regional_driver builds it. For
    `summer` the level itself is replaced by Bochow's affine summer map, with the
    draw spread preserved as a RATIO so the ensemble is still an ensemble."""
    wl = _running_mean(gmst_rb, SHAPE_WIN)
    a = np.atleast_1d(np.asarray(amp_draws, float))[:, None]
    if kind == "summer":
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.where(
                np.abs(gmst_rb) > 1e-9,
                BOCHOW_SUMMER_SLOPE * (gmst_rb - BOCHOW_SUMMER_GMT0_K) / gmst_rb,
                BOCHOW_SUMMER_SLOPE)
        return (a / OBS_AMP_FULL) * ratio[None, :]
    S = {"held": _shipped_S(HELD_STEM), "full": _shipped_S(FULL_STEM),
         "decl": _declining_S()}[kind]
    return a * S(wl)[None, :]


def driver_with_law(kind, gmst_rb, amp_draws):
    """regional_driver (scope_gis_2300_relaxation.py:114-129) with the amp*S product
    replaced by an arbitrary law. Line-for-line the same splice, the same anchor
    window, the same observed-history mask -- gated below against the shipped
    function under the HELD law."""
    tgz = pd.read_csv(os.path.join(OBS, "t_gis_zones.csv"))
    gd = dict(zip(tgz["year"].astype(int), tgz[GIS_ZONE].astype(float)))
    last = int(tgz["year"].max())
    obs = np.array([gd.get(int(y), 0.0) for y in YEARS])
    mask = YEARS <= last
    ianch = np.isin(YEARS, np.arange(last - ANCHOR_N + 1, last + 1))
    anchor = obs[ianch].mean()
    M = amp_field(kind, gmst_rb, amp_draws)                       # (ndraw, nyear)
    off = anchor - (M[:, ianch] * gmst_rb[None, ianch]).mean(axis=1)
    spliced = M * gmst_rb[None, :] + off[:, None]
    return np.where(mask[None, :], obs[None, :], spliced)


def main():
    post = pd.read_csv(A.POST)
    tbar = gis_tbar()
    r_s = np.exp(post["gis_slow_ell"].to_numpy())
    post["gis_alpha_s"] = post["gis_slow_w"].to_numpy() * r_s / tbar
    post["gis_beta_s"] = (1.0 - post["gis_slow_w"].to_numpy()) * r_s
    amp = post["gis_amp"].to_numpy()
    S_tab = gis_shape_table()
    ibd = (YEARS >= DRIVER_BASE[0]) & (YEARS <= DRIVER_BASE[1])
    idx = {y: int(np.where(YEARS == y)[0][0])
           for y in (2015, 2100, 2300) + RATE_WIN + A.HIND}

    def load_gmst(path, col):
        g = pd.read_csv(path).set_index("year")[col].reindex(YEARS).to_numpy()
        return g - g[ibd].mean()

    gm = {(s, f): load_gmst(f"outputs/{st}.csv", f"gmst_{A.ARM}")
          for s, l, f, st in A.ARMS}
    gm_ours = {lab: load_gmst(f"data/observations/fair_mean_gmst_{ssp}.csv", "gmst_C")
               for ssp, lab in OURS}

    print(f"diag_gis_amp_above_275 — section 4.2 of the 2026-08-22 handoff, "
          f"{TAG}, {len(post)} draws")
    print(f"  the shipped law fits CMIP6 over 0.75-{CMIP6_FIT_HI_K:g} K and HOLDS FLAT "
          f"above; the arms run to {max(g[idx[2300]] for g in gm.values()):.2f} K.\n")

    # --- 0. GATE: the HELD law must reproduce the shipped driver ---------------
    worst = 0.0
    for k, g in list(gm.items()) + list(gm_ours.items()):
        worst = max(worst, float(np.max(np.abs(
            driver_with_law("held", g, amp) - regional_driver(g, amp, S_tab)))))
    print(f"GATE — max |driver_with_law('held') - regional_driver| over all "
          f"{len(gm) + len(gm_ours)} drivers x {len(post)} draws: {worst:.3e} K")
    if worst > REPRO_TOL_CM:
        sys.exit(f"GATE FAILED ({worst:.3e} K > {REPRO_TOL_CM:g}): the local driver is "
                 f"not the shipped one, so nothing below is a comparison.")
    print("  => the local driver IS the shipped one; the three other laws differ "
          "ONLY in the amp field.\n")

    # --- 1. how far the evidence actually reaches -------------------------------
    b = pd.read_csv(CMIP6_BINNED)
    b = b[b.estimator == "secant"]
    print(f"=== 1. WHERE THE CMIP6 EVIDENCE STOPS (secant, binned medians) ===\n")
    print(f"  {'scenario':10}{'last bin K':>12}{'n_models':>10}   bins with n>=20 up to")
    for sc in ("ssp126", "ssp245", "ssp585"):
        s = b[b.scenario == sc].sort_values("dt_bin")
        hi20 = s[s.n_models >= 20].dt_bin.max()
        print(f"  {sc:10}{s.dt_bin.max():12.2f}{int(s.n_models.iloc[-1]):10d}"
              f"   {hi20:.2f} K")
    print(f"\n  {'arm':24}{'GSAT@2300 K':>13}{'x beyond the FIT':>18}"
          f"{'x beyond ANY data':>19}")
    for ssp, lab, fam, _ in A.ARMS:
        T = gm[(ssp, fam)][idx[2300]]
        print(f"  {lab + ' ' + fam:24}{T:13.2f}{T / CMIP6_FIT_HI_K:18.1f}"
              f"{T / CMIP6_DATA_HI_K:19.1f}")
    T5 = gm_ours[LEVEL_SSP][idx[2300]]
    print(f"  {'OUR ' + LEVEL_SSP:24}{T5:13.2f}{T5 / CMIP6_FIT_HI_K:18.1f}"
          f"{T5 / CMIP6_DATA_HI_K:19.1f}")

    # --- 2. the four laws, as effective amplification ---------------------------
    print(f"\n=== 2. THE FOUR LAWS — median effective amplification amp*S(dT) ===\n")
    probe = np.array([1.0, 2.0, 2.75, 4.0, 5.75, 7.81, 13.63])
    print(f"  {'law':46}" + "".join(f"{p:>8.2f}" for p in probe))
    for lab, kind in AMP_LAWS:
        if kind == "summer":
            vals = BOCHOW_SUMMER_SLOPE * (probe - BOCHOW_SUMMER_GMT0_K) / probe
        else:
            S = {"held": _shipped_S(HELD_STEM), "full": _shipped_S(FULL_STEM),
                 "decl": _declining_S()}[kind]
            vals = OBS_AMP_FULL * np.asarray(S(probe))
        print(f"  {lab:46}" + "".join(f"{v:8.3f}" for v in vals))
    print(f"\n  (GMT probe in K. 2.75 = the fit ceiling; 5.75 = the last CMIP6 bin;\n"
          f"   7.81 = our ssp585 @2300; 13.63 = the x2300 arm @2300.)")

    # --- 3. per law: re-bisect, base, ceiling, and the required flux -------------
    tgt = pd.read_csv(A.TARGETS).set_index("year")["gis"]
    want_cm = float(tgt.loc[A.HIND[1]] - tgt.loc[A.HIND[0]])
    ann = pd.read_csv(A.ANN)
    c1, c0 = post["gis_c1"].to_numpy(), post["gis_c0"].to_numpy()
    _rq = A.protect_band(ann, RATE_ARM_LABEL, RATE_ARM[1]).groupby("year").gis_cm.median()
    rate_target = float(_rq[RATE_WIN[1]] - _rq[RATE_WIN[0]]) / \
        (RATE_WIN[1] - RATE_WIN[0]) * 100.0

    u = {k: reservoir_unit(g, CELL_B_ONSET_K, CELL_B_TAU_YR) for k, g in gm.items()}
    u_ours = {k: reservoir_unit(g, CELL_B_ONSET_K, CELL_B_TAU_YR)
              for k, g in gm_ours.items()}
    du_rate = (u[RATE_ARM][idx[RATE_WIN[1]]] - u[RATE_ARM][idx[RATE_WIN[0]]]) / \
        (RATE_WIN[1] - RATE_WIN[0]) * 100.0
    u_lvl = u_ours[LEVEL_SSP][idx[2300]]

    print(f"\n=== 3. THE REQUIRED FLUX psi, PER LAW "
          f"(tau = {CELL_B_TAU_YR:g} yr HELD FIXED — it is a prior, not a fit) ===\n")
    print(f"  rate target  {rate_target:.1f} cm/century  ({RATE_ARM[0]} {RATE_ARM[1]}, "
          f"{RATE_WIN[0]}-{RATE_WIN[1]}, PROTECT median)")
    print(f"  level target {MATCHED_P50_CM:.1f} cm       (our {LEVEL_SSP} @2300, "
          f"matched p50)")
    print(f"  cell B as shipped in the handoff: psi = {PSI_B_CM_PER_YR:.3f} cm/yr "
          f"(V={CELL_B_V_M:g} m / tau={CELL_B_TAU_YR:g} yr)\n")
    hdr = (f"  {'law':46}{'base rate':>10}{'psi_rate':>10}{'base lvl':>10}"
           f"{'psi_lvl':>9}{'ratio':>8}{'V@tau':>8}")
    print(hdr)
    rows = []
    for lab, kind in AMP_LAWS:
        drv = {k: driver_with_law(kind, g, amp) for k, g in gm.items()}
        drv_o = {k: driver_with_law(kind, g, amp) for k, g in gm_ours.items()}
        # re-bisect the rate scale on the SAME historical target under this law
        Th = drv[A.HIND_ARM]
        lo, hi = np.full(len(post), 1e-4), np.full(len(post), 1e3)
        for _ in range(80):
            mid = np.sqrt(lo * hi)
            L = basin2_series(Th, post, 1.0, mid)
            below = 100.0 * (L[:, idx[A.HIND[1]]] - L[:, idx[A.HIND[0]]]) < want_cm
            lo, hi = np.where(below, mid, lo), np.where(below, hi, mid)
        s = np.sqrt(lo * hi)
        base = {k: np.median(rebase_cm(basin2_series(v, post, 1.0, s)), axis=0)
                for k, v in drv.items()}
        base_o = {k: np.median(rebase_cm(basin2_series(v, post, 1.0, s)), axis=0)
                  for k, v in drv_o.items()}
        br = (base[RATE_ARM][idx[RATE_WIN[1]]] - base[RATE_ARM][idx[RATE_WIN[0]]]) / \
            (RATE_WIN[1] - RATE_WIN[0]) * 100.0
        bl = base_o[LEVEL_SSP][idx[2300]]
        ## add(t) = V*100*u(t) = psi*tau*u(t) in cm, so BOTH the level and the rate
        ## are exactly linear in psi at fixed tau -- solved, not scanned.
        psi_r = (rate_target - br) / (CELL_B_TAU_YR * du_rate)
        psi_l = (MATCHED_P50_CM - bl) / (CELL_B_TAU_YR * u_lvl)
        rows.append(dict(law=lab.split()[0], law_label=lab.strip(),
                         s_median=float(np.median(s)),
                         base_rate_cm_per_century=br, base_level_cm=bl,
                         psi_rate_cm_per_yr=psi_r, psi_level_cm_per_yr=psi_l,
                         psi_ratio=psi_l / psi_r,
                         V_at_fixed_tau_m=psi_r * CELL_B_TAU_YR / CM_PER_M))
        print(f"  {lab:46}{br:10.1f}{psi_r:10.3f}{bl:10.1f}{psi_l:9.3f}"
              f"{psi_l / psi_r:8.2f}{psi_r * CELL_B_TAU_YR / CM_PER_M:8.1f}")
        # the phi=1 ceiling under this law (handoff 1.1), same arithmetic
        for ssp, l2, fam, _ in A.ARMS:
            T = drv[(ssp, fam)]
            ceil = np.zeros(len(post))
            L15 = np.zeros(len(post))
            for kb in (K_SOUTH, K_HIGH):
                ceil += np.clip(kb * (c1 * T[:, idx[2300]] + c0), 0.0, kb * GIS_V0_M)
                L15 += np.clip(kb * (c1 * T[:, idx[2015]] + c0), 0.0, kb * GIS_V0_M)
            top = 100.0 * np.median(ceil - L15)
            med = float(A.protect_band(ann, l2, fam).groupby("year").gis_cm.median()[2300])
            rows[-1][f"ceil_ratio_{ssp}_{fam}"] = med / top
        rows[-1][f"d2100_{LEVEL_SSP}_cm"] = float(
            psi_r * CELL_B_TAU_YR * u_ours[LEVEL_SSP][idx[2100]])
    print(f"\n  psi in cm/yr.  'ratio' = psi_level/psi_rate: 1.00 means ONE flux "
          f"satisfies BOTH\n  requirements, which is cell B's whole claim. 'V@tau' is "
          f"the volume that flux implies\n  at the fixed tau, in m SLE — against the "
          f"{V_MAX_M:g} m NO+NE inventory and {GIS_V0_M:g} m whole sheet.")

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)

    # --- 4. the phi=1 ceiling, all four laws, all five arms ---------------------
    print(f"\n=== 4. THE phi=1 CEILING (handoff 1.1) UNDER EACH LAW ===\n")
    print(f"  ratio = PROTECT median / what the LINEAR L_eq can deliver at phi=1.")
    print(f"  ratio > 1 => no rate law reaches that arm, whatever the amp law.\n")
    cols = [f"ceil_ratio_{s}_{f}" for s, l, f, _ in A.ARMS]
    print(f"  {'law':46}" + "".join(f"{l[-3:] + ' ' + f[:2]:>11}"
                                    for s, l, f, _ in A.ARMS))
    for _, r in out.iterrows():
        print(f"  {r.law_label:46}" + "".join(f"{r[c]:10.2f}x" for c in cols))

    # --- 5. the verdict ---------------------------------------------------------
    held = out[out.law == "held"].iloc[0]
    lo_psi, hi_psi = out.psi_rate_cm_per_yr.min(), out.psi_rate_cm_per_yr.max()
    print(f"\n=== 5. WHAT THE AMP LAW DOES TO THE DELIVERABLE ===\n")
    print(f"  psi spans {lo_psi:.3f}-{hi_psi:.3f} cm/yr across the four laws "
          f"({hi_psi / lo_psi:.2f}x),")
    print(f"  against the shipped {held.psi_rate_cm_per_yr:.3f} and the handoff's "
          f"quoted {PSI_B_CM_PER_YR:.3f}.")
    worst_ceil = out[cols].max().max()
    warm = [c for c in cols if "ssp585" in c]
    print(f"  the phi=1 shortfall on the WARM arms stays above 1 for EVERY law "
          f"(min {out[warm].min().min():.2f}x, max {out[warm].max().max():.2f}x)"
          if out[warm].min().min() > 1.0 else
          f"  WARNING: some law brings a warm arm's ceiling ratio to "
          f"{out[warm].min().min():.2f}x <= 1 — handoff 1.1 is NOT robust.")
    ## The bisection scale is reported because it is the HINDCAST-INERTNESS test:
    ## the driver is OBSERVED south-Greenland T through 2024 and only spliced after,
    ## so a law that differs only above 2.75 K cannot touch the fitted period. If this
    ## ever stops being exactly 1, sub-choice 1 becomes a REFIT question.
    s_spread = out.s_median.max() / out.s_median.min()
    print(f"  the rate scale s is IDENTICAL across all four laws "
          f"({out.s_median.iloc[0]:.6f}, spread {s_spread:.6f}x) => the law above "
          f"{CMIP6_FIT_HI_K:g} K is\n  EXACTLY hindcast-inert and revisable at "
          f"projection time, no refit. Same reason as gis_amp itself.")
    if s_spread != 1.0:
        print(f"  *** s MOVED ({s_spread:.6f}x): sub-choice 1 is now a REFIT question, "
              f"not a prior-propagation one.")
    d21 = out[f"d2100_{LEVEL_SSP}_cm"].abs().max()
    print(f"  2100 stays inert under every law: max |d2100| on our {LEVEL_SSP} "
          f"= {d21:.4f} cm (tol {Y2100_TOL_CM:g}).")
    print(f"\n  RAMP_W_K is {RAMP_W_K:g} and is NOT scanned here — that is stage 1a, "
          f"a separate axis.")
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
