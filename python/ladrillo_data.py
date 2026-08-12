#!/usr/bin/env python3
"""
ladrillo_data.py — assemble every observational and structural input Ladrillo's
glacier calibration depends on, and emit the three machine-generated artifacts
the Julia calibrator reads.

This is the readable, importable replacement for the exec-prefix chain that
produced the same artifacts during development (build_extc_inputs.py ->
d1f -> d1e -> d1d -> d0_glacier_shootout, ~1650 lines of source-splitting
`exec`). Nothing is re-derived: python/test_ladrillo_data.py asserts the
artifacts this module writes are IDENTICAL, to full float precision, to the
committed ones the chain produced. The research cells stay where they are as
provenance; this file is the production path.

-----------------------------------------------------------------------------
DATA SOURCES  (every input, with what it contributes)
-----------------------------------------------------------------------------
outputs/recalib_targets_ext.csv
    The calibration targets. Used here for the glacier (gsic) series: cumulative
    glacier sea-level contribution, cm, Frederikse 2020 (Marzeion-2015 early
    segment) spliced to GlaMBIE from 2019, re-referenced 1995-2005.
outputs/diag_constraint_anatomy_regions.csv
    Per-RGI-region inventory: ice mass (Gt), historical melt share (Hugonnet),
    and volume response times at +1.5 K and +3.0 K.
data/observations/t_glac_regions_hadcrut5.csv
    Per-RGI-region glacier-area-weighted HadCRUT5 surface temperature.
data/observations/t_glac_hadcrut5.csv
    Global HadCRUT5 annual mean (column gmst_hadcrut5_C), the denominator of
    the observational amplification fits.
data/observations/raw/glambie_data.zip
    GlaMBIE (Glacier Mass Balance Intercomparison Exercise) regional calendar-
    year mass change: glacier area (for the block weights), the 2000-2024
    modern rate and its error, cumulative loss to 2020, and the region-19
    annual series used for the target seam adjustment.
data/observations/raw/gmip3/3_shift_summary_region_characteristics*.csv
    GlacierMIP3 region characteristics: the ISIMIP3 regional-vs-global warming
    ratio and 2020 regional volume.
outputs/d1_block_ladder_cache.csv
    GlacierMIP3 committed-loss ladder per region set (committed % of 2020 mass
    at +1.2/1.5/2.0/3.0 K, with 17-83% bands), produced once by
    python/d1_multireservoir_cell.py from the GlacierMIP3 steady-state
    ensemble. Cached because the underlying LOWESS quantile fit needs the
    GlacierMIP3 NetCDF and the moepy package; this module reads the cache and
    fails loudly if a region set is missing from it.

-----------------------------------------------------------------------------
OUTPUTS
-----------------------------------------------------------------------------
data/observations/t_glac_blocks.csv       per-reservoir temperature drivers
outputs/extc_block_constants.csv          per-reservoir structural constants
outputs/recalib_targets_ext_gsicadj.csv   r19-seam-adjusted glacier target

All written at full precision (%.12f / %.12g): the Julia port validation
compares against them at 1e-9 and 6-decimal rounding broke it twice.

-----------------------------------------------------------------------------
KNOWN WART — RNG ORDER DEPENDENCE
-----------------------------------------------------------------------------
four_rung_fit() draws multi-start jitter from one module-level RNG, so the
fitted (b, T_off) depend on how many fits ran before them. `build_artifacts()`
therefore reproduces the development call sequence exactly, including two fits
whose results are discarded. This is preserved deliberately: changing it would
change the calibrator's inputs and invalidate the accepted posterior. The fix
for the next recalibration is a per-block seeded RNG; see FIT_RNG_SEED.
"""
import os
import zipfile

import numpy as np
import pandas as pd
from scipy.optimize import brentq, minimize

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- inputs ----------------------------------------------------------------
TARGETS_CSV = os.path.join(REPO, "outputs/recalib_targets_ext.csv")
REGIONS_CSV = os.path.join(REPO, "outputs/diag_constraint_anatomy_regions.csv")
TGLAC_REGIONS_CSV = os.path.join(REPO, "data/observations/t_glac_regions_hadcrut5.csv")
TGLAC_GLOBAL_CSV = os.path.join(REPO, "data/observations/t_glac_hadcrut5.csv")
GLAMBIE_ZIP = os.path.join(REPO, "data/observations/raw/glambie_data.zip")
REGCHAR_CSV = os.path.join(REPO, "data/observations/raw/gmip3",
                           "3_shift_summary_region_characteristicsFeb12_2024.csv")
LADDER_CACHE_CSV = os.path.join(REPO, "outputs/d1_block_ladder_cache.csv")

# ---- outputs ---------------------------------------------------------------
OUT_DRIVERS = os.path.join(REPO, "data/observations/t_glac_blocks.csv")
OUT_CONSTANTS = os.path.join(REPO, "outputs/extc_block_constants.csv")
OUT_GSIC_ADJ = os.path.join(REPO, "outputs/recalib_targets_ext_gsicadj.csv")

# ---- reservoir definition --------------------------------------------------
# Three reservoirs by response time (d1d structure C_both): the Antarctic
# periphery on its own (its observational target scope differs — see the seam
# adjustment below), the slow-responding regions, and everything else.
SPEC_3RES = {
    "R19":   ["19"],                                          # Antarctic periphery
    "SLOWP": ["03", "09", "07", "06"],                        # Arctic Canada N, Russian
                                                              # Arctic, Svalbard, Iceland
    "FAST":  ["01", "04", "17", "13", "14", "02", "15", "08",
              "10", "11", "16", "18", "12"],
}
# Two-block ablation structure. Its fits are discarded, but they consume RNG
# draws that the three-reservoir fits inherit — see the RNG note in the header.
SPEC_2BLK = {"SLOW": ["19", "03", "09", "07", "06"], "FAST": SPEC_3RES["FAST"]}

# ---- constants -------------------------------------------------------------
DRIVER_BASE = (1850, 1900)          # glacier-frame temperature anomaly baseline
FIT_START = 1900                    # first year of the glacier target
GMIP3_LEVELS = [1.2, 1.5, 2.0, 3.0]  # global warming levels of the committed ladder
RUNG_CORR = 0.6                     # cross-rung error correlation (same 4 models)
RUNG_SIGMA_FLOOR_PCT = 3.0          # floor on the band-derived rung sigma
GT_PER_MM_SLE = 361.8
GLAMBIE_AREA_YEAR = 2000.0          # year whose glacier area sets the block weights
GLAMBIE_RATE_WIN = (2000.0, 2024.0)  # modern-rate window
GLAMBIE_S2020_WIN = (2000.0, 2020.0)  # cumulative loss to the ladder denominator year
GLAMBIE_ERR_INFLATE = 1.5           # inflation on the reported GlaMBIE rate error
AMP_FIT_WIN = (1901, 2024)          # window of the observational amplification fit
AMP_RATIO_COL = "median_reg_vs_glob_temp_ch_1.5_3.0"   # ISIMIP3 regional/global ratio
# Total remaining inventory prior, m SLE (A2 in the calibrator), and the
# observed cumulative melt 1900-2000 it is measured against.
INV_V = 0.290
S2000_OBS = 0.093
FARINOTTI_NONR19 = (0.221, 0.057)   # m SLE excluding regions 5 and 19
FARINOTTI_R19 = (0.069, 0.018)      # m SLE, region 19 add-back
# Uncharted ice: glaciers in the observational budget but absent from the
# inventory (Parkes & Marzeion 2018). The book value is subtracted from the
# observed 1900-2000 melt before it is attributed to reservoirs.
UNCHARTED_BOUNDS_GLOBAL_MM = (16.7, 48.0)
R5_MELT_SHARE = 0.13                # region-5 share removed to match the model scope
UNCHARTED_SCOPE_FACTOR = 1 - R5_MELT_SHARE
UNCHARTED_BOOK_MM = sum(UNCHARTED_BOUNDS_GLOBAL_MM) / 2 * UNCHARTED_SCOPE_FACTOR
LADDER_RUNGS_SOLVE = (1.2, 2.0)     # the two rungs the exact anchor passes through
TAU_SOLVE_HORIZON = 6000            # years; cap on the tau50 integration
TAU_MATCH_TOL = 0.02                # relative tolerance on the anchored tau50 match
FIT_RNG_SEED = 2026
SEAM_START_YEAR = 2019              # first target year containing GlaMBIE region 19

_rng = np.random.default_rng(FIT_RNG_SEED)


# =============================================================================
# 1. observational inputs
# =============================================================================
def load_glacier_target():
    """The glacier (gsic) calibration target: contiguous years and values, cm."""
    tgt = pd.read_csv(TARGETS_CSV).set_index("year")
    have = tgt.index[(tgt.index >= FIT_START) & tgt["gsic"].notna()]
    years = np.arange(have.min(), have.max() + 1)
    assert np.all(np.isin(years, have)), "glacier target has a year gap"
    return years, tgt.loc[years, "gsic"].to_numpy()


def load_region_inventory():
    """Per-region ice mass, historical melt share, and volume response times."""
    regs = pd.read_csv(REGIONS_CSV, dtype={"reg": str})
    regs["reg"] = regs["reg"].str.zfill(2)
    return regs.set_index("reg")


def load_region_temperatures():
    """Per-region glacier-area-weighted HadCRUT5, and the global HadCRUT5 series."""
    regional = pd.read_csv(TGLAC_REGIONS_CSV).set_index("year")
    global_ = pd.read_csv(TGLAC_GLOBAL_CSV).set_index("year")["gmst_hadcrut5_C"]
    return regional, global_


def load_region_characteristics():
    """GlacierMIP3 region characteristics (ISIMIP3 amplification ratio, volumes)."""
    rc = pd.read_csv(REGCHAR_CSV, index_col=0)
    rc = rc[rc["rgi_reg"] != "All"].copy()
    rc["reg"] = rc["rgi_reg"].map(lambda r: f"{int(r):02d}")
    return rc.set_index("reg")


def load_glambie():
    """GlaMBIE regional calendar-year mass change, keyed by zero-padded region."""
    with zipfile.ZipFile(GLAMBIE_ZIP) as z:
        names = {int(os.path.basename(n).split("_")[0]): n
                 for n in z.namelist()
                 if "calendar_years/" in n and n.endswith(".csv")
                 and os.path.basename(n).split("_")[0].isdigit()
                 and int(os.path.basename(n).split("_")[0]) >= 1}
        return {f"{reg:02d}": pd.read_csv(z.open(n)) for reg, n in names.items()}


def load_ladder_cache():
    """GlacierMIP3 committed-loss ladder per region set (see the header)."""
    if not os.path.exists(LADDER_CACHE_CSV):
        raise FileNotFoundError(
            f"{LADDER_CACHE_CSV} missing — regenerate it with "
            "python/d1_multireservoir_cell.py (needs the GlacierMIP3 NetCDF + moepy)")
    return pd.read_csv(LADDER_CACHE_CSV)


# Module-level data, loaded once (this module is a build step, not a library
# that anyone imports lazily).
TARGET_YEARS, TARGET_GSIC = load_glacier_target()
REGIONS = load_region_inventory()
REGION_TEMP, GLOBAL_TEMP = load_region_temperatures()
REGION_CHAR = load_region_characteristics()
GLAMBIE = load_glambie()
LADDER = load_ladder_cache()

AREA_WEIGHT = {r: float(g.loc[np.isclose(g["start_dates"], GLAMBIE_AREA_YEAR),
                              "glacier_area"].iloc[0])
               for r, g in GLAMBIE.items()}
MELT_SHARE = REGIONS.melt_share.to_dict()
NON_R19 = [r for r in REGIONS.index if r != "19"]
GT_NON_R19 = {r: REGIONS.loc[r, "mass_gt"] for r in NON_R19}
GT_NON_R19_TOTAL = sum(GT_NON_R19.values())
MELT_NON_R19_TOTAL = sum(MELT_SHARE[r] for r in NON_R19)
GT_SHARE = (REGIONS.mass_gt / REGIONS.mass_gt.sum()).to_dict()


# =============================================================================
# 2. per-reservoir aggregation
# =============================================================================
def glambie_block_stats(members):
    """Modern melt rate (mm SLE/yr), its inflated error, and cumulative loss to
    2020 (m SLE), summed over a reservoir's regions."""
    total_gt, var_gt, cum2020_gt, n_years = 0.0, 0.0, 0.0, None
    for r in members:
        g = GLAMBIE[r]
        sel = (g.start_dates >= GLAMBIE_RATE_WIN[0]) & (g.end_dates <= GLAMBIE_RATE_WIN[1])
        total_gt += -g.loc[sel, "combined_gt"].sum()
        var_gt += (g.loc[sel, "combined_gt_errors"] ** 2).sum()
        n_years = sel.sum() if n_years is None else n_years
        assert sel.sum() == n_years, f"GlaMBIE year-count mismatch in region {r}"
        s20 = (g.start_dates >= GLAMBIE_S2020_WIN[0]) & (g.end_dates <= GLAMBIE_S2020_WIN[1])
        cum2020_gt += -g.loc[s20, "combined_gt"].sum()
    rate = total_gt / GT_PER_MM_SLE / n_years
    rate_sd = np.sqrt(var_gt) / GT_PER_MM_SLE / n_years * GLAMBIE_ERR_INFLATE
    return rate, rate_sd, cum2020_gt / GT_PER_MM_SLE / 1000.0


def block_ladder(members):
    """Committed loss (% of 2020 mass) and its 17-83% band, per warming level."""
    key = "-".join(sorted(members))
    sub = LADDER[LADDER.key == key]
    if sub.empty:
        raise KeyError(f"region set {key} is not in {os.path.basename(LADDER_CACHE_CSV)} "
                       "— regenerate the cache with python/d1_multireservoir_cell.py")
    sub = sub.set_index("level_K")
    return ({L: float(sub.loc[L, "central"]) for L in GMIP3_LEVELS},
            {L: (float(sub.loc[L, "lo"]), float(sub.loc[L, "hi"])) for L in GMIP3_LEVELS})


def build_reservoir(name, members, farinotti_basis):
    """Aggregate one reservoir's driver, inventory, response times and ladder.

    `farinotti_basis=True` (the three-reservoir structure) takes region 19's
    inventory from the Farinotti region-19 value and splits the rest by ice-mass
    share; `False` (the two-block ablation) partitions the total inventory prior
    by mass share. Historical melt is split over the non-r19 regions by Hugonnet
    share, applied to the observed 1900-2000 melt net of uncharted ice.
    """
    s2000_inventory = S2000_OBS - UNCHARTED_BOOK_MM / 1000.0
    weight_sum = sum(AREA_WEIGHT[r] for r in members)
    driver = sum(AREA_WEIGHT[r] / weight_sum * REGION_TEMP[f"r{r}"] for r in members).dropna()
    driver = driver - driver.loc[DRIVER_BASE[0]:DRIVER_BASE[1]].mean()
    amp = float(np.average([REGION_CHAR.loc[r, AMP_RATIO_COL] for r in members],
                           weights=[AREA_WEIGHT[r] for r in members]))
    mass = REGIONS.loc[members, "mass_gt"]
    tau15 = float(np.average(REGIONS.loc[members, "resp_time_15C_yr"], weights=mass))
    tau30 = float(np.average(REGIONS.loc[members, "resp_time_30C_yr"], weights=mass))
    rate, rate_sd, cum2020 = glambie_block_stats(members)

    s2000 = (sum(MELT_SHARE[r] for r in members if r != "19")
             / MELT_NON_R19_TOTAL * s2000_inventory) if members != ["19"] else 0.0
    if farinotti_basis:
        if members == ["19"]:
            volume, volume_sd = FARINOTTI_R19
        else:
            share = sum(GT_NON_R19[r] for r in members) / GT_NON_R19_TOTAL
            volume, volume_sd = share * FARINOTTI_NONR19[0], share * FARINOTTI_NONR19[1]
    else:
        volume = sum(GT_SHARE[r] for r in members) * INV_V
        volume_sd = np.sqrt(
            (sum(GT_NON_R19.get(r, 0) for r in members) / GT_NON_R19_TOTAL
             * FARINOTTI_NONR19[1]) ** 2
            + (FARINOTTI_R19[1] if "19" in members else 0.0) ** 2)

    committed, bands = block_ladder(members)
    rung_sig = {L: max((bands[L][1] - bands[L][0]) / 2.0, RUNG_SIGMA_FLOOR_PCT)
                for L in GMIP3_LEVELS}
    return dict(name=name, members=members, driver_obs=driver, amp_b=amp,
                tau15=tau15, tau30=tau30, glambie_rate=rate, glambie_rate_sd=rate_sd,
                a0=volume + s2000, a0_sig=volume_sd,
                S2000_data=s2000, S2020_data=s2000 + cum2020,
                com=committed, com_bands=bands, rung_sig=rung_sig)


def observational_amp(block):
    """Through-origin fit of the block driver on global HadCRUT5, both relative
    to 1850-1900, over AMP_FIT_WIN. The alternative to the ISIMIP3 ratio."""
    lo, hi = AMP_FIT_WIN
    gx = GLOBAL_TEMP.loc[lo:hi].to_numpy()
    by = block["driver_obs"].loc[lo:hi].to_numpy()
    assert len(gx) == len(by), "driver/global window mismatch"
    return float((gx * by).sum() / (gx ** 2).sum())


# =============================================================================
# 3. equilibrium curve S_eq(T) = a (1 - exp(-b (T - T_off)))
# =============================================================================
def two_rung_anchor(block):
    """Exact (b, T_off) through the two solve rungs — the fit's starting point."""
    a, s2020 = block["a0"], block["S2020_data"]
    L1, L2 = LADDER_RUNGS_SOLVE
    S1 = s2020 + block["com"][L1] / 100 * (a - s2020)
    S2 = s2020 + block["com"][L2] / 100 * (a - s2020)
    T1, T2 = block["amp_b"] * L1, block["amp_b"] * L2
    b = (np.log(1 - S1 / a) - np.log(1 - S2 / a)) / (T2 - T1)
    return dict(block, a=a, b=b, T_off=T1 + np.log(1 - S1 / a) / b, fit_mode="2rung",
                rung_z={L: 0.0 for L in GMIP3_LEVELS})


def four_rung_fit(block):
    """(a, b, T_off) by correlated-Gaussian fit to all four committed rungs plus
    a soft Farinotti inventory prior. Multi-start Nelder-Mead; see the RNG note
    in the header."""
    s2020 = block["S2020_data"]
    levels = list(GMIP3_LEVELS)
    y = np.array([block["com"][L] for L in levels])
    sig = np.array([block["rung_sig"][L] for L in levels])
    cov = np.outer(sig, sig) * (RUNG_CORR + (1 - RUNG_CORR) * np.eye(len(levels)))
    cov_inv = np.linalg.inv(cov)

    def committed(a, b, T_off):
        return np.array([100 * (a * (1 - np.exp(-b * (block["amp_b"] * L - T_off))) - s2020)
                         / max(a - s2020, 1e-9) for L in levels])

    a_lo = s2020 + 0.2 * (block["a0"] - s2020)
    a_hi = s2020 + 3.0 * (block["a0"] - s2020)
    unpack = lambda z: (a_lo + (a_hi - a_lo) / (1 + np.exp(-z[0])),
                        0.05 + 2.95 / (1 + np.exp(-z[1])),
                        -3.0 + 6.0 / (1 + np.exp(-z[2])))

    def objective(z):
        a, b, T_off = unpack(z)
        r = committed(a, b, T_off) - y
        return 0.5 * r @ cov_inv @ r + 0.5 * ((a - block["a0"]) / block["a0_sig"]) ** 2

    def pack(a, b, T_off):
        fr = [np.clip((a - a_lo) / (a_hi - a_lo), 1e-4, 1 - 1e-4),
              np.clip((b - 0.05) / 2.95, 1e-4, 1 - 1e-4),
              np.clip((T_off + 3.0) / 6.0, 1e-4, 1 - 1e-4)]
        return np.array([np.log(v / (1 - v)) for v in fr])

    anchor = two_rung_anchor(block)
    starts = [pack(anchor["a"], np.clip(anchor["b"], 0.06, 2.9),
                   np.clip(anchor["T_off"], -2.9, 2.9)),
              pack(block["a0"] * 1.2, 0.6, -0.5),
              pack(block["a0"], 0.3, 0.5)]
    seeded = list(starts)
    while len(starts) < 8:
        starts.append(seeded[_rng.integers(len(seeded))] + _rng.normal(0, 0.7, 3))

    best = None
    for z0 in starts:
        r = minimize(objective, z0, method="Nelder-Mead",
                     options=dict(xatol=1e-9, fatol=1e-11, maxiter=6000))
        if best is None or r.fun < best.fun:
            best = r
    a, b, T_off = unpack(best.x)
    resid = committed(a, b, T_off) - y
    return dict(block, a=a, b=b, T_off=T_off, fit_mode="4rung",
                rung_z={L: float(resid[i] / sig[i]) for i, L in enumerate(levels)},
                a_prior_z=float((a - block["a0"]) / block["a0_sig"]))


# =============================================================================
# 4. transient response: anchor (kappa, nu) to the two response times
# =============================================================================
def tau50_of(block, kappa, nu, level):
    """Years for the reservoir to cover half the gap to its equilibrium at a
    sustained global warming `level`, under dS = min(kappa exc^nu, 1)(S_eq - S)."""
    a, b, T_off = block["a"], block["b"], block["T_off"]
    T = block["amp_b"] * level
    s_eq = a * (1 - np.exp(-b * (T - T_off)))
    S = block["S2020_data"]
    if s_eq <= S:
        return np.inf
    target, prev = S + 0.5 * (s_eq - S), S
    for k in range(1, TAU_SOLVE_HORIZON + 1):
        T_eq = T_off - np.log(max(1.0 - S / a, 1e-12)) / b
        S += min(kappa * max(T - T_eq, 0.0) ** nu, 1.0) * (s_eq - S)
        if S >= target:
            return (k - 1) + (target - prev) / max(S - prev, 1e-30)
        prev = S
    return float(2 * TAU_SOLVE_HORIZON)


def solve_anchored(block):
    """(kappa, nu) reproducing the region's tau50 at BOTH +1.5 K and +3.0 K.

    nu is the exponent on the temperature excess: it controls how much faster a
    reservoir responds in a warmer climate, which is exactly what a single
    response time cannot express. Solved by a sign change in nu, falling back to
    a least-squares match if the two response times cannot be met exactly.
    """
    def kappa_for(nu):
        f = lambda lk: tau50_of(block, np.exp(lk), nu, 1.5) - block["tau15"]
        lo, hi = np.log(1e-7), np.log(20.0)
        if f(lo) < 0 or f(hi) > 0:
            return None
        return np.exp(brentq(f, lo, hi, xtol=1e-10))

    def residual30(nu):
        k = kappa_for(nu)
        return np.nan if k is None else tau50_of(block, k, nu, 3.0) - block["tau30"]

    nus = np.linspace(0.0, 4.0, 17)
    rs = np.array([residual30(v) for v in nus])
    ok = np.isfinite(rs)
    bracket = next(((nus[i], nus[i + 1]) for i in range(len(nus) - 1)
                    if ok[i] and ok[i + 1] and rs[i] * rs[i + 1] < 0), None)
    if bracket:
        nu = brentq(residual30, *bracket, xtol=1e-6)
        kappa, exact = kappa_for(nu), True
    else:
        def loss(v):
            k = kappa_for(v[0])
            return np.inf if k is None else \
                np.log(tau50_of(block, k, v[0], 3.0) / block["tau30"]) ** 2
        best = min((minimize(loss, [v0], method="Nelder-Mead") for v0 in [0.5, 1.0, 2.0]),
                   key=lambda r: r.fun)
        nu = float(np.clip(best.x[0], 0.0, 4.0))
        kappa, exact = kappa_for(nu), False
    t15, t30 = tau50_of(block, kappa, nu, 1.5), tau50_of(block, kappa, nu, 3.0)
    return dict(kappa=kappa, nu=nu, tau15_ach=t15, tau30_ach=t30, exact=exact,
                match_ok=(abs(t15 / block["tau15"] - 1) < TAU_MATCH_TOL
                          and abs(t30 / block["tau30"] - 1) < TAU_MATCH_TOL))


# =============================================================================
# 5. the region-19 target seam
# =============================================================================
def gsic_target_without_r19():
    """The glacier target with observed region-19 melt removed from 2019 on.

    The target's Frederikse segment assumes zero region-19 melt; the GlaMBIE
    splice that extends it from 2019 includes region 19. Removing the observed
    GlaMBIE region-19 cumulative makes the whole series one scope — the model's
    hindcast scope, SLOWP + FAST — so the seam does not appear as a spurious
    acceleration.
    """
    g19 = GLAMBIE["19"]
    annual_cm = pd.Series((-g19.combined_gt.to_numpy()) / GT_PER_MM_SLE / 10.0,
                          index=g19.start_dates.astype(int).to_numpy())
    adjusted, cumulative = TARGET_GSIC.copy(), 0.0
    for i, year in enumerate(TARGET_YEARS):
        if year >= SEAM_START_YEAR:
            if (year - 1) in annual_cm.index:
                cumulative += float(annual_cm.loc[year - 1])
            adjusted[i] = TARGET_GSIC[i] - cumulative
    return adjusted


# =============================================================================
# 6. build the artifacts
# =============================================================================
def build_artifacts(write=True, out_drivers=OUT_DRIVERS, out_constants=OUT_CONSTANTS,
                    out_gsic_adj=OUT_GSIC_ADJ):
    """Emit the three calibrator inputs. Returns the three DataFrames.

    The call sequence below is load-bearing: four_rung_fit consumes the shared
    RNG, so the discarded two-block fits must run, in this order, for the
    three-reservoir constants to reproduce. See the header.
    """
    res3 = {n: build_reservoir(n, m, farinotti_basis=True) for n, m in SPEC_3RES.items()}
    blk2 = {n: build_reservoir(n, m, farinotti_basis=False) for n, m in SPEC_2BLK.items()}
    _ = {n: four_rung_fit(b) for n, b in blk2.items()}        # discarded; RNG parity
    _ = {n: two_rung_anchor(b) for n, b in res3.items()}      # discarded; no RNG
    fit_isimip = {n: four_rung_fit(b) for n, b in res3.items()}
    anchor_isimip = {n: solve_anchored(b) for n, b in fit_isimip.items()}

    res3_obs = {}
    for name, members in SPEC_3RES.items():
        block = build_reservoir(name, members, farinotti_basis=True)
        block["amp_b"] = observational_amp(block)
        res3_obs[name] = block
    fit_obs = {n: four_rung_fit(b) for n, b in res3_obs.items()}
    anchor_obs = {n: solve_anchored(b) for n, b in fit_obs.items()}
    for n in SPEC_3RES:
        assert anchor_isimip[n]["match_ok"] and anchor_obs[n]["match_ok"], \
            f"{n}: anchored (kappa, nu) failed to match both response times"

    # -- 1. per-reservoir temperature drivers
    drivers = pd.DataFrame({"year": fit_isimip["R19"]["driver_obs"].index})
    for name in SPEC_3RES:
        drivers[name] = fit_isimip[name]["driver_obs"].reindex(drivers["year"]).to_numpy()
    assert not drivers.isna().any().any(), "a block driver has gaps"

    # -- 2. per-reservoir constants, on both amplification bases
    rows = []
    for name in SPEC_3RES:
        isimip, obs = fit_isimip[name], fit_obs[name]
        row = dict(block=name, members="|".join(SPEC_3RES[name]),
                   a0=isimip["a0"], a0_sig=isimip["a0_sig"],
                   S2000_data=isimip["S2000_data"], S2020_data=isimip["S2020_data"],
                   tau15=isimip["tau15"], tau30=isimip["tau30"],
                   glambie_rate=isimip["glambie_rate"],
                   glambie_rate_sd=isimip["glambie_rate_sd"],
                   amp_regchar=isimip["amp_b"], amp_obsfit=obs["amp_b"],
                   b_fit_regchar=isimip["b"], T_off_fit_regchar=isimip["T_off"],
                   b_fit_obsfit=obs["b"], T_off_fit_obsfit=obs["T_off"],
                   kappa_anch_regchar=anchor_isimip[name]["kappa"],
                   nu_anch_regchar=anchor_isimip[name]["nu"],
                   kappa_anch_obsfit=anchor_obs[name]["kappa"],
                   nu_anch_obsfit=anchor_obs[name]["nu"])
        for L in GMIP3_LEVELS:
            key = str(L).replace(".", "p")
            row[f"com{key}"] = isimip["com"][L]
            row[f"sig{key}"] = isimip["rung_sig"][L]
        rows.append(row)
    constants = pd.DataFrame(rows)

    # -- 3. r19-seam-adjusted glacier target
    adjusted = gsic_target_without_r19()
    pre_seam = TARGET_YEARS < SEAM_START_YEAR
    assert np.array_equal(adjusted[pre_seam], TARGET_GSIC[pre_seam]), \
        "the seam adjustment touched years before the seam"
    net_removed_mm = 10 * (TARGET_GSIC[-1] - adjusted[-1])
    assert net_removed_mm > 0, "net region-19 removal must be positive at the series end"
    gsic_adj = pd.DataFrame({"year": TARGET_YEARS, "gsic_adj": adjusted})

    if write:
        # Full precision: the Julia port validation compares at 1e-9.
        drivers.to_csv(out_drivers, index=False, float_format="%.12f")
        constants.to_csv(out_constants, index=False, float_format="%.12g")
        gsic_adj.to_csv(out_gsic_adj, index=False, float_format="%.12g")

    return drivers, constants, gsic_adj


def main():
    drivers, constants, gsic_adj = build_artifacts()
    print(f"ladrillo_data | {len(SPEC_3RES)} reservoirs | "
          f"drivers {int(drivers.year.min())}-{int(drivers.year.max())} | "
          f"target {int(gsic_adj.year.min())}-{int(gsic_adj.year.max())}")
    show = ["block", "a0", "S2020_data", "tau15", "tau30", "amp_regchar", "amp_obsfit",
            "kappa_anch_obsfit", "nu_anch_obsfit"]
    print(constants[show].to_string(index=False,
                                    float_format=lambda v: f"{v:.5g}"))
    print(f"  net region-19 removal at the target end: "
          f"{10 * (TARGET_GSIC[-1] - gsic_adj.gsic_adj.to_numpy()[-1]):.3f} mm")
    for path in (OUT_DRIVERS, OUT_CONSTANTS, OUT_GSIC_ADJ):
        print(f"  wrote {os.path.relpath(path, REPO)}")


if __name__ == "__main__":
    main()
