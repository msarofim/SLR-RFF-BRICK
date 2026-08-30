#!/usr/bin/env python3
"""
diag_gis_npv_tau_sensitivity.py -- §4.1, FINALLY RUN.

THE QUESTION (open since 2026-08-22, `scoping_2026-08-22_greenland_shape_stepback.md`
§22, re-raised as item 1 of `handoff_2026-08-23_commitment_evidence.md` §4):

    tau moves from 800 to ~2700 yr under the commitment evidence. The 3 %
    discount factor at 2250 is 0.0012. Is the tau question worth ANYTHING to a
    discounted (SC-GHG / NPV) deliverable, or does discounting retire it?

It is the cheapest item on the list and the ONLY one that can RETIRE work, so it
runs before the onset re-scan, before pinning V, and before any model change.

WHAT IT PRICES -- three structural knobs, not one, because they are separable and
their ranking is the actual decision:

  tau   at FIXED psi = 100*V/tau  (the near-term flux is held; only the reservoir's
        depletion curvature moves).  This is the §4.1 question as literally asked.
  psi   at FIXED tau               (cell A 0.125 -> the evidence's 0.273 cm/yr).
  onset 4.69 K -> 2.0 K            (`handoff` §5: 2.0-2.8x too high, and set to
        protect a 2100 that 16 ISMIP6 models say is 1.30x fast).

HOW THE DAMAGE CHOICE IS KEPT FROM BEING SILENTLY RESOLVED
  No damage function is asserted. The NPV integrand is `SLR(t)^ALPHA` weighted by
  `exp(-RHO_NET*(t-NPV_BASE_YEAR))`, and BOTH are scanned:
    ALPHA   1 (damages linear in SLR)  and  2 (the convex coastal case)
    RHO_NET 0.5 / 1 / 2 / 3 %  -- the NET rate, i.e. the consumption discount rate
            MINUS the growth rate of the exposed value the damages scale with.
            Monetised damages that grow with GDP at g, discounted at rho, give
            exactly RHO_NET = rho - g on the physical stream. 3 % net is therefore
            a HARSH case (it implies zero exposure growth), 0.5 % a generous one.
  A result that holds across the whole 4x2 block is a result about discounting,
  not about a damage-function choice. Where it does NOT hold, the block shows it.

THE MARGINAL (§4) IS COMPUTED, NOT ASSUMED
  A LEVEL screen can mislead for a THRESHOLD object: a pulse shifts the onset
  CROSSING YEAR, and dS/dGMT is largest right at the crossing, so the marginal
  response could in principle be spikier than the level response. §4 therefore
  finite-differences the reservoir against a real FaIR CO2-pulse GMT response
  (the near-STEP shape verified in §4a) at THREE perturbation sizes, and reports
  the CELL-TO-CELL RATIO of the marginal -- a magnitude-free quantity in which the
  unknown per-tonne scaling and the un-modelled AIS/TE/glacier marginals cancel.
  If tau's marginal ratio is ~1.00 while psi's and the onset's are not, the level
  verdict carries over to the per-tonne SC-GHG quantity.

INPUTS (all already on disk; nothing is refit, no model is run)
  outputs/ssps_components_2300_L14.csv     L14 vintage, UNTAPPED base, med
  data/observations/fair_mean_gmst_<ssp>.csv

WRITES outputs/diag_gis_npv_tau_sensitivity.csv  (+ _cells.csv)
  python3 python/diag_gis_npv_tau_sensitivity.py
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "python"))

## THE reservoir, imported rather than restated, so this file cannot drift from
## the object the scan actually scored (scope_gis_reservoir_offline.py, 86/216).
from scope_gis_reservoir_offline import reservoir_unit, CM_PER_M  # noqa: E402
import scope_gis_reservoir_offline as _RES  # noqa: E402
from scope_gis_2300_relaxation import DRIVER_BASE  # noqa: E402

# --- named constants (every label below derives from these) ------------------
COMP_CSV = os.path.join(REPO, "outputs/ssps_components_2300_L14.csv")
GMST_CSV = os.path.join(REPO, "data/observations/fair_mean_gmst_{ssp}.csv")
OUT = os.path.join(REPO, "outputs/diag_gis_npv_tau_sensitivity.csv")
OUT_CELLS = os.path.join(REPO, "outputs/diag_gis_npv_tau_sensitivity_cells.csv")
OUT_MARG = os.path.join(REPO, "outputs/diag_gis_npv_tau_sensitivity_marginal.csv")

LINEAGE = "L14 vintage (two-basin), untapped base, median trajectory"
NPV_BASE_YEAR = 2030          # SC-GHG pulse year; discounting is dated from here
NPV_END_YEAR = 2300           # the deliverable's horizon
SLR_BASE_WIN = (2015, 2025)   # 11-yr present-day datum (never a single year)
RHO_NET = [0.005, 0.010, 0.020, 0.030]
ALPHA = [1.0, 2.0]
TRUNC_YEARS = [2100, 2150, 2200, 2300]
## §4: the marginal. The GMT response to a CO2 pulse, taken from the FaIR
## v145 (calib 1.4.5) ssp245 paired-pulse run in the FaIRtoFrEDI repo. Its
## MAGNITUDE is irrelevant here and is normalised away (see IRF_NORM_YEAR /
## IRF_NORM_MK); only its SHAPE is used, and §4a verifies that shape is a
## near-step before anything is built on it.
IRF_REPO = os.path.join(os.path.dirname(REPO), "FaIRtoFrEDI", "fair_outputs")
IRF_BASE = os.path.join(IRF_REPO, "fair_baseline_gmst_v145_ssp245_pulse001_2030.csv")
IRF_PULS = os.path.join(IRF_REPO, "fair_policy_gmst_v145_ssp245_pulse001_2030.csv")
IRF_NORM_YEAR = 2100
IRF_NORM_MK = 1.0             # the IRF is rescaled to +1 mK of GMT at IRF_NORM_YEAR
## Three sizes, because a finite difference across a CLIPPED ramp on an ANNUAL
## axis is exactly the place a one-size derivative lies. Linearity across these
## is TESTED, not assumed.
PERT_SCALES_MK = [10.0, 100.0, 300.0]
## §4c: the SSP2-4.5 marginal is largest precisely because that scenario sits
## INSIDE the ramp, so it scales with 1/RAMP_W_K -- and RAMP_W_K is pinned at 1.0
## and has NEVER been scanned (memory `INDEX_slr`). The headline must not rest on
## an unscanned constant, so its sensitivity is measured here.
RAMP_W_SCAN_K = [0.5, 1.0, 2.0, 4.0]
SSPS = ["SSP1-2.6", "SSP2-4.5", "SSP5-8.5"]
SSP_KEY = {"SSP1-2.6": "ssp126", "SSP2-4.5": "ssp245", "SSP5-8.5": "ssp585"}

ONSET_SHIPPED_K = 4.69        # `gis_tap_priced_l13`: the "don't move 2100" floor
ONSET_LADDER_K = 2.0          # Bochow/CLIMBER-X threshold range is 1.7-2.6 K
V_WHOLE_SHEET_M = 7.42        # CLIMBER-X-checked GIS_V0_M, inside 7.30-7.68
PSI_SHIPPED = 0.125           # cell A, 100*V/tau = 100*1.0/800
PSI_EVIDENCE = 0.273          # 2250-2300 rate criterion; Greve@3001 gives 0.179-0.341

## Each cell is (label, V_m, onset_K, tau_yr). psi is DERIVED and printed, never
## typed, so a (V, tau) edit cannot silently desynchronise the flux it implies.
CELLS = [
    ("base (no reservoir)",        0.0,             ONSET_SHIPPED_K,  800.0),
    ("A shipped",                  1.0,             ONSET_SHIPPED_K,  800.0),
    ("A tau->2700 @fixed psi",     0.125 * 2700 / 100, ONSET_SHIPPED_K, 2700.0),
    ("B psi=0.273 tau=2200",       6.0,             ONSET_SHIPPED_K, 2200.0),
    ("B tau->2718 @fixed psi",     V_WHOLE_SHEET_M, ONSET_SHIPPED_K, 2718.0),
    ("A psi->0.273 @fixed tau",    0.273 * 800 / 100, ONSET_SHIPPED_K,  800.0),
    ("A onset->2.0K",              1.0,             ONSET_LADDER_K,   800.0),
    ("B onset->2.0K",              V_WHOLE_SHEET_M, ONSET_LADDER_K,  2718.0),
]

## The comparisons that answer the question. (label, cell_from, cell_to, knob)
CONTRASTS = [
    ("tau 800->2700 at psi=0.125", "A shipped",     "A tau->2700 @fixed psi", "tau"),
    ("tau 2200->2718 at psi=0.273", "B psi=0.273 tau=2200", "B tau->2718 @fixed psi", "tau"),
    ("psi 0.125->0.273 at tau=800", "A shipped",    "A psi->0.273 @fixed tau", "psi"),
    ("onset 4.69->2.0 K at cell A", "A shipped",    "A onset->2.0K",          "onset"),
    ("onset 4.69->2.0 K at cell B", "B tau->2718 @fixed psi", "B onset->2.0K", "onset"),
    ("reservoir off->cell A",       "base (no reservoir)", "A shipped",       "structure"),
    ("reservoir off->cell B",       "base (no reservoir)", "B tau->2718 @fixed psi", "structure"),
]


def load_total_and_gmst():
    """Total GMSL (cm, rebased to SLR_BASE_WIN) and GMST (K above DRIVER_BASE),
    both on the same annual axis, per SSP."""
    d = pd.read_csv(COMP_CSV)
    tot = d[d.component == "total"].pivot(index="year", columns="ssp", values="med")
    gis = d[d.component == "gis"].pivot(index="year", columns="ssp", values="med")
    years = tot.index.to_numpy()
    ib = (years >= SLR_BASE_WIN[0]) & (years <= SLR_BASE_WIN[1])
    if ib.sum() != SLR_BASE_WIN[1] - SLR_BASE_WIN[0] + 1:
        sys.exit(f"SLR_BASE_WIN {SLR_BASE_WIN} not fully covered by the L14 axis")
    tot = tot - tot[ib].mean()
    gmst = {}
    for s in SSPS:
        g = pd.read_csv(GMST_CSV.format(ssp=SSP_KEY[s])).set_index("year")["gmst_C"]
        gb = g.loc[DRIVER_BASE[0]:DRIVER_BASE[1]].mean()
        gmst[s] = (g.reindex(years) - gb).to_numpy()
        if not np.isfinite(gmst[s]).all():
            sys.exit(f"GMST for {s} does not cover the L14 axis {years[0]}-{years[-1]}")
    return years, tot, gis, gmst


def idxa(years, y):
    return int(np.where(years == y)[0][0])


def npv(slr_cm, years, rho, alpha, y0, y1):
    """Discounted integral of a damage stream proportional to SLR^alpha.
    SLR below the present-day datum contributes zero (no negative damages)."""
    m = (years >= y0) & (years <= y1)
    df = np.exp(-rho * (years[m] - NPV_BASE_YEAR))
    return float(np.sum(df * np.clip(slr_cm[m], 0.0, None) ** alpha))


def load_pulse_irf(years):
    """Shape of the GMT response to a CO2 pulse, normalised to IRF_NORM_MK at
    IRF_NORM_YEAR. Ensemble mean over the 841 FaIR configs; zero before the
    pulse year by construction."""
    for f in (IRF_BASE, IRF_PULS):
        if not os.path.exists(f):
            return None
    b = pd.read_csv(IRF_BASE).set_index("year")
    p = pd.read_csv(IRF_PULS).set_index("year")
    d = (p - b).mean(axis=1)
    d = d.reindex(years).ffill().fillna(0.0).to_numpy()
    d = np.where(years < NPV_BASE_YEAR, 0.0, d)
    ref = d[int(np.where(years == IRF_NORM_YEAR)[0][0])]
    if not np.isfinite(ref) or ref <= 0:
        sys.exit(f"pulse IRF is non-positive at {IRF_NORM_YEAR}: {ref!r}")
    return d / ref * (IRF_NORM_MK / 1000.0)      # K, = IRF_NORM_MK mK at norm year


def main():
    years, tot, gis, gmst = load_total_and_gmst()
    idx = {y: int(np.where(years == y)[0][0]) for y in TRUNC_YEARS + [2050]}

    print(f"diag_gis_npv_tau_sensitivity -- {LINEAGE}")
    print(f"  NPV base year {NPV_BASE_YEAR}, horizon {NPV_END_YEAR}, "
          f"SLR datum = mean({SLR_BASE_WIN[0]}-{SLR_BASE_WIN[1]}), "
          f"GMST rebased to {DRIVER_BASE}\n")

    # --- 0. the discounting facts that frame everything -----------------------
    print("=== 0. WHERE THE DISCOUNTED WEIGHT LIVES (weight = exp(-rho*(t-%d))) ==="
          % NPV_BASE_YEAR)
    hdr = "  rho_net  " + "".join(f"{y:>10d}" for y in TRUNC_YEARS)
    print(hdr)
    for rho in RHO_NET:
        row = "".join(f"{np.exp(-rho * (y - NPV_BASE_YEAR)):>10.4f}" for y in TRUNC_YEARS)
        print(f"  {rho * 100:5.1f}%  {row}")
    print("  share of the 2030-2300 UNWEIGHTED-SLR^1 NPV falling AFTER 2150, "
          "SSP5-8.5:")
    s585 = tot["SSP5-8.5"].to_numpy()
    for rho in RHO_NET:
        a = npv(s585, years, rho, 1.0, 2151, NPV_END_YEAR)
        b = npv(s585, years, rho, 1.0, NPV_BASE_YEAR, NPV_END_YEAR)
        print(f"    rho_net {rho * 100:4.1f}%  {100 * a / b:5.1f}%")
    print()

    # --- 1. the cells, in physical units first --------------------------------
    add, cellrows = {}, []
    for lab, V, on, tau in CELLS:
        psi = CM_PER_M * V / tau
        add[lab] = {s: CM_PER_M * V * reservoir_unit(gmst[s], on, tau) for s in SSPS}
        rec = dict(cell=lab, V_m=V, onset_K=on, tau_yr=tau, psi_cm_per_yr=psi)
        for s in SSPS:
            for y in TRUNC_YEARS:
                rec[f"add_{SSP_KEY[s]}_{y}_cm"] = add[lab][s][idx[y]]
                rec[f"tot_{SSP_KEY[s]}_{y}_cm"] = tot[s].to_numpy()[idx[y]] + \
                    add[lab][s][idx[y]]
        cellrows.append(rec)
    cells = pd.DataFrame(cellrows)
    cells.to_csv(OUT_CELLS, index=False)

    print("=== 1. THE CELLS -- reservoir ADD-ON in cm, and total GMSL (base+add) ===")
    print(f"  {'cell':<26}{'psi':>7}{'V_m':>7}{'tau':>7}  "
          + "".join(f"{'+' + str(y):>9}" for y in TRUNC_YEARS)
          + "   | SSP5-8.5 total@2300")
    for _, r in cells.iterrows():
        print(f"  {r.cell:<26}{r.psi_cm_per_yr:>7.3f}{r.V_m:>7.2f}{r.tau_yr:>7.0f}  "
              + "".join(f"{r[f'add_ssp585_{y}_cm']:>9.1f}" for y in TRUNC_YEARS)
              + f"   | {r['tot_ssp585_2300_cm']:>8.1f}")
    print("  (SSP1-2.6 never crosses either onset -- its add-on is exactly 0 "
          "in every cell.)")
    z = max(abs(add[l][ "SSP1-2.6"]).max() for l, *_ in CELLS)
    print(f"  VERIFIED: max |SSP1-2.6 add-on| over all cells = {z:.3e} cm\n")
    print("  SSP2-4.5 add-on at 2300 (0 at onset 4.69 K by construction):")
    for _, r in cells.iterrows():
        print(f"    {r.cell:<26}{r['add_ssp245_2300_cm']:>8.2f} cm")
    print()

    # --- 2. the NPV block -----------------------------------------------------
    rows = []
    for s in SSPS:
        base = tot[s].to_numpy()
        for alpha in ALPHA:
            for rho in RHO_NET:
                v = {lab: npv(base + add[lab][s], years, rho, alpha,
                              NPV_BASE_YEAR, NPV_END_YEAR) for lab, *_ in CELLS}
                for clab, cf, ct, knob in CONTRASTS:
                    rows.append(dict(
                        ssp=s, alpha=alpha, rho_net=rho, knob=knob, contrast=clab,
                        npv_from=v[cf], npv_to=v[ct],
                        d_npv_frac=(v[ct] - v[cf]) / v[cf]))
    res = pd.DataFrame(rows)
    res.to_csv(OUT, index=False)

    print("=== 2. FRACTIONAL CHANGE IN NPV, %s to %s ===" % (NPV_BASE_YEAR, NPV_END_YEAR))
    for s in SSPS:
        sub = res[res.ssp == s]
        if sub.d_npv_frac.abs().max() < 1e-12:
            print(f"\n  {s}: every contrast is EXACTLY 0 "
                  f"(GMST never reaches either onset).")
            continue
        print(f"\n  {s}")
        for alpha in ALPHA:
            print(f"    ALPHA={alpha:g}   " + "".join(
                f"{'rho ' + format(r * 100, '.1f') + '%':>13}" for r in RHO_NET))
            for clab, cf, ct, knob in CONTRASTS:
                cells_ = [sub[(sub.alpha == alpha) & (sub.rho_net == r)
                              & (sub.contrast == clab)].d_npv_frac.iloc[0]
                          for r in RHO_NET]
                print(f"      {clab:<30}" + "".join(f"{100 * c:>12.2f}%" for c in cells_))
    print()

    # --- 3. the ranking, which is the decision --------------------------------
    print("=== 3. RANKING THE THREE KNOBS (max |dNPV| over the whole ALPHA x rho "
          "block, warm arms only) ===")
    warm = res[res.ssp.isin(["SSP2-4.5", "SSP5-8.5"])]
    for s in ["SSP5-8.5", "SSP2-4.5"]:
        sub = warm[warm.ssp == s]
        print(f"  {s}")
        for knob in ["tau", "psi", "onset", "structure"]:
            k = sub[sub.knob == knob]
            if k.empty or k.d_npv_frac.abs().max() < 1e-12:
                print(f"    {knob:<10} exactly 0")
                continue
            print(f"    {knob:<10} |dNPV/NPV| ranges "
                  f"{100 * k.d_npv_frac.abs().min():6.2f}% to "
                  f"{100 * k.d_npv_frac.abs().max():6.2f}%")
    # --- 4. THE MARGINAL -- does a pulse behave like the level? ---------------
    irf = load_pulse_irf(years)
    if irf is None:
        print("=== 4. MARGINAL: SKIPPED -- FaIR pulse files not found at "
              f"{os.path.relpath(IRF_REPO, os.path.dirname(REPO))} ===")
    else:
        print("=== 4a. THE PULSE GMT RESPONSE IS A NEAR-STEP (FaIR v145 calib 1.4.5, "
              "ssp245 CO2 pulse 2030) ===")
        print(f"  normalised to {IRF_NORM_MK:g} mK at {IRF_NORM_YEAR}:  "
              + "  ".join(f"{y}: {1000 * irf[idxa(years, y)]:.3f} mK"
                          for y in [2035, 2050, 2100, 2200, 2300]))
        print("  A near-flat step is what matters: after the crossing year the "
              "reservoir sees a CONSTANT GMT offset,\n  so the pulse acts by moving "
              "the ONSET CROSSING and by scaling the ramp -- neither of which "
              "involves tau.\n")

        print("=== 4b. MARGINAL RESERVOIR SLR, and the CELL-TO-CELL RATIO ===")
        mrows = []
        for s in ["SSP5-8.5", "SSP2-4.5"]:
            print(f"\n  {s} -- d(reservoir add-on @2300) per +1 mK sustained GMT, cm/mK:")
            print(f"  {'cell':<26}" + "".join(f"{'@' + format(e, '.0f') + 'mK':>12}"
                                              for e in PERT_SCALES_MK) + "   linearity")
            marg = {}
            for lab, V, on, tau in CELLS:
                per = []
                for eps_mk in PERT_SCALES_MK:
                    g2 = gmst[s] + irf * (eps_mk / IRF_NORM_MK)
                    a2 = CM_PER_M * V * reservoir_unit(g2, on, tau)
                    per.append((a2[idx[2300]] - add[lab][s][idx[2300]]) / eps_mk)
                marg[lab] = per
                body = f"  {lab:<26}" + "".join(f"{v:>12.5f}" for v in per)
                print(body + (f"   {max(per) / min(per):>6.3f}x" if min(per) > 0
                              else "   (INERT -- contributes EXACTLY 0 per tonne)"))
            print(f"\n  RATIO of the marginal between the paired cells (magnitude-free: "
                  f"the unknown\n  per-tonne scaling and the un-modelled AIS/TE/glacier "
                  f"marginals cancel):")
            print(f"  {'contrast':<32}{'knob':<11}" + "".join(
                f"{'@' + format(e, '.0f') + 'mK':>12}" for e in PERT_SCALES_MK))
            for clab, cf, ct, knob in CONTRASTS:
                if min(marg[cf]) <= 0:
                    note = ("both cells inert" if max(marg[ct]) <= 0
                            else f"0 -> {marg[ct][0]:.5f} cm/mK: an INFINITE ratio, "
                                 f"i.e. the knob CREATES the marginal")
                    print(f"  {clab:<32}{knob:<11}   {note}")
                    mrows.append(dict(ssp=s, contrast=clab, knob=knob,
                                      **{f"marg_ratio_{e:.0f}mK": np.nan
                                         for e in PERT_SCALES_MK}))
                    continue
                r = [marg[ct][i] / marg[cf][i] for i in range(len(PERT_SCALES_MK))]
                mrows.append(dict(ssp=s, contrast=clab, knob=knob,
                                  **{f"marg_ratio_{e:.0f}mK": r[i]
                                     for i, e in enumerate(PERT_SCALES_MK)}))
                print(f"  {clab:<32}{knob:<11}" + "".join(f"{v:>12.3f}" for v in r))
        pd.DataFrame(mrows).to_csv(OUT_MARG, index=False)
        print(f"\nWROTE {os.path.relpath(OUT_MARG, REPO)}")

        print(f"\n=== 4c. DOES THE SSP2-4.5 RESULT REST ON THE UNSCANNED RAMP_W_K "
              f"(pinned {_RES.RAMP_W_K:g}, never scanned)? ===")
        print("  SSP2-4.5 marginal @2300, cell A onset->2.0 K, cm/mK at "
              f"+{PERT_SCALES_MK[0]:.0f} mK:")
        w0 = _RES.RAMP_W_K
        try:
            for w in RAMP_W_SCAN_K:
                _RES.RAMP_W_K = w
                m = {}
                for s in ["SSP2-4.5", "SSP5-8.5"]:
                    a1 = CM_PER_M * 1.0 * reservoir_unit(gmst[s], ONSET_LADDER_K, 800.0)
                    g2 = gmst[s] + irf * (PERT_SCALES_MK[0] / IRF_NORM_MK)
                    a2 = CM_PER_M * 1.0 * reservoir_unit(g2, ONSET_LADDER_K, 800.0)
                    m[s] = (a2[idx[2300]] - a1[idx[2300]]) / PERT_SCALES_MK[0]
                print(f"    RAMP_W_K={w:<4g} SSP2-4.5 {m['SSP2-4.5']:.5f}   "
                      f"SSP5-8.5 {m['SSP5-8.5']:.5f}   "
                      f"ratio 245/585 {m['SSP2-4.5'] / m['SSP5-8.5']:.2f}x")
        finally:
            _RES.RAMP_W_K = w0
        print("  The 245>585 ORDERING is what the verdict uses; the ratio's SIZE "
              "is RAMP_W_K-dependent.\n")

    # --- 5. the counterweight: is the onset move admissible at all? -----------
    print("=== 5. THE ONSET MOVE IS THE BIGGEST KNOB -- AND IT BREAKS THE COOL BAND ===")
    import gis_targets  # noqa: E402
    print(f"  {'ssp':<10}{'base gis@2300':>15}{'matched top':>13}{'headroom':>11}"
          f"{'  add @onset 2.0 K (cell A / cell B)':>38}")
    for s in SSPS:
        base_gis = gis[s].to_numpy()[idx[2300]]
        top = 100.0 * gis_targets.MATCHED_2300_M[s][1]
        hr = top - base_gis
        aA = add["A onset->2.0K"][s][idx[2300]]
        aB = add["B onset->2.0K"][s][idx[2300]]
        over = "" if aA <= hr else f"   OVER by {aA / hr:.1f}x / {aB / hr:.1f}x"
        print(f"  {s:<10}{base_gis:>15.1f}{top:>13.1f}{hr:>11.1f}"
              f"{aA:>20.1f}{aB:>10.1f}{over}")
    print("  NOTE, and it is NOT resolved here: this repo has already judged these "
          "cool bands\n  SPURIOUSLY PRECISE -- a sample-size-respecting t-PI makes "
          "them 3-9x WIDER (memory\n  `INDEX_slr`, band-basis step b). Whether the "
          "overshoot above is fatal or absorbed by\n  an honest band is a "
          "METHODOLOGICAL CHOICE and is left open.\n")
    print()

    print(f"\nWROTE {os.path.relpath(OUT, REPO)}")
    print(f"WROTE {os.path.relpath(OUT_CELLS, REPO)}")


if __name__ == "__main__":
    main()
