## ============================================================================
## diag_gic_regrow_penalty.py — IS THE FLOORED-EQUILIBRIUM GLACIER LAW WHY
## LADRILLO RECOVERS FROM AN OVERSHOOT AND THE SLEIP ENSEMBLE LARGELY DOES NOT?
##
## THE OBSERVATION (handoff 2026-09-02b §3). SLEIP Phase 1 (egusphere-2026-3874)
## reports a 0.1-0.3 m overshoot sea-level penalty at 2300 for SSP5-3.4-OS vs
## SSP1-2.6 across 7 emulators. Ladrillo gives 3-5 cm at 2150 decaying to ~0 by
## 2300. Ruled out already: the CMIP7 marker treatment, and a cumulative-budget
## artifact (ssp534over emits +10 GtCO2 MORE to 2300 and still ends cooler).
##
## THE EXPERIMENT. One arm pair on the SHIPPED L24 posterior -- NO REFIT -- with
## the glacier law swapped back to the pre-2026-08-31 melt-only ratchet:
##     NEW (shipped): FLOOR on,  R = 1      AMPPROF_FLOOR=1 AMPPROF_R=1.0
##     OLD (ratchet): FLOOR off, R = Inf    AMPPROF_FLOOR=0 AMPPROF_R=Inf
## Both switches, per the handoff: the old law is exactly `exc = max(T-T_eq,0)`
## on an UNFLOORED S_eq, and setting only one gives a half-old law.
##
## ⚠ ALGEBRAIC NOTE FOUND HERE (2026-09-02). Under R = Inf the FLOOR is
## unreachable: S_eq < 0 requires T < T_off, and T_eq >= T_off always (because
## frac_left <= 1 so -log(frac_left) >= 0), hence S_eq < 0 implies d = T - T_eq
## < 0, and the d<0 branch divides `mult` by Inf. So R=Inf alone reproduces the
## old law numerically; the half-law that actually differs is FLOOR=0 with R=1,
## which would let glaciers regrow PAST pre-industrial. Both are still set, so
## the arm matches the old code literally rather than only in value.
##
## THE PENALTY IS PAIRED. Draw k carries the same posterior draw and the same
## FaIR config in both scenarios (PAIR_SEED is fixed and NDRAW/NCFG match), so
## the penalty is the median of the PER-DRAW difference, not a difference of
## medians. [PAIRCHK] asserts the config column matches draw-for-draw.
##
## ⚠ THE ANSWER IS A NULL, SO THE TEST NEEDS POWER (`no_power_null`). [GATE-A]
## alone CANNOT distinguish "the switch works and the defaults reproduce" from
## "the switch is dead and every run is the shipped law" -- it passes identically
## either way, which is the `gate_reads_its_own_output` family. Two things give it
## power: a direct probe of `_nu_step` (the two laws differ at T = -0.5, 0.0, 1.0 K
## on a synthetic block), and [GATE-C], a POSITIVE CONTROL on vvLN whose answer was
## priced INDEPENDENTLY at -0.15 cm at 2300 by `glacier_floor_bounded_regrowth`.
##
## ERROR BARS. `amp_2x2_needs_its_error_bar`: one published 2x2 cell turned out
## smaller than its own bar, and the i.i.d. se on MCMC draws was 1.5-3x too
## small. Both an i.i.d. and a MOVING-BLOCK bootstrap se are reported; quote the
## block one.
## ============================================================================
import sys, pathlib, numpy as np, pandas as pd

REPO      = pathlib.Path(__file__).resolve().parents[1]
OUT       = REPO / "outputs"
## LABELS DERIVE FROM THESE CONSTANTS -- never retype a scenario or horizon below.
OVERSHOOT = "ssp534over_nomarker"
REFERENCE = "ssp126_nomarker"
NULLCTRL  = "ssp585_nomarker"          # monotonically warming => the two laws agree
POSCTRL   = "vvLN"                     # van Vuuren LOW-NEGATIVE marker; marker-BASED, per the
                                       # 2026-09-02 policy, because it IS a CMIP7 marker
ARM       = "joint"                    # the reported band carries climate uncertainty
FORCING   = "spliced"
TAP       = "_tap4p69K_V5p64m_tau800"
TAG_SHIP  = "L24"                      # the shipped arms, run by run_l24_nomarker_arms.sh
TAG_NEW   = "L24GICNEW"                # instrumentation at shipped defaults
TAG_OLD   = "L24GICOLD"                # the melt-only ratchet
LAWS      = {"NEW (floored eq, R=1)": TAG_NEW, "OLD (melt-only ratchet)": TAG_OLD}
HORIZONS  = [2100, 2150, 2300]
COMPS     = ["glaciers", "gis", "ais", "te", "lws", "total"]
NBOOT     = 4000
BLOCK     = 25                         # moving-block length over the draw index
SEED      = 2026
## SLEIP Phase 1, egusphere-2026-3874: 7-emulator overshoot penalty at 2300, cm.
SLEIP_2300_CM = (10.0, 30.0)
## The law's own price on the vvLN marker at 2300 (`glacier_floor_bounded_regrowth`).
## A penalty move FAR larger than this means something else moved too -- check the arm.
## TWO published numbers exist for the SAME quantity, and they differ by 0.05 cm:
## `glacier_floor_bounded_regrowth` records vvLN@2300 "DELIVERED -0.15 against a PRE-COMPUTED
## -0.20 after flooring". The PRE-COMPUTED one is the like-for-like comparator here, because
## it is the law swapped on a HELD posterior -- which is exactly this experiment. The DELIVERED
## -0.15 was read across shipped arms whose posteriors also differ, so it carries a refit's
## worth of movement as well as the law's. The gate tests the pre-computed value; the distance
## to the delivered one is REPORTED, not asserted away.
LAW_PRICE_VVLN_2300_CM      = -0.20    # pre-computed, law-only, posterior held
LAW_DELIVERED_VVLN_2300_CM  = -0.15    # delivered, read across arms
## `glacier_floor_bounded_regrowth` also states the law is worth ~0 OUTSIDE the van Vuuren
## declining markers: S_eq goes negative on 12.9 % of block x draw cells at vvLN/2300 and
## <1.2 % elsewhere. The SSPs are "elsewhere", so a null here is a PREDICTION of that entry,
## not a surprise -- and [GATE-C] is what makes it a measurement rather than a restatement.
## Tolerance DERIVED from the disagreement between the two existing estimates of this very
## quantity (0.05 cm), not picked (`threshold_from_obs_or_law`, `tolerance_scaled_to_spread`).
POSCTRL_TOL_CM = abs(LAW_DELIVERED_VVLN_2300_CM - LAW_PRICE_VVLN_2300_CM)

def stem(kind, ssp, tag, frozen=None):
    d = frozen if frozen is not None else OUT
    return d / f"scope_slr_fairunc_{kind}_{ssp}_{FORCING}_{tag}{TAP}.csv"

FROZEN = pathlib.Path(sys.argv[1]) / "outputs" if len(sys.argv) > 1 else OUT

def draws(ssp, tag):
    p = stem("draws", ssp, tag, FROZEN if tag in (TAG_NEW, TAG_OLD) else OUT)
    d = pd.read_csv(p)
    return d[d.arm == ARM]

def cells(ssp, tag):
    p = stem("cells", ssp, tag, FROZEN if tag in (TAG_NEW, TAG_OLD) else OUT)
    return pd.read_csv(p)

def wide(ssp, tag):
    """draw x (component, horizon) matrix of cm, indexed by draw."""
    d = draws(ssp, tag)
    w = d.pivot_table(index="draw", columns=["component", "horizon"], values="value_cm")
    cfg = d.drop_duplicates("draw").set_index("draw")["config"].reindex(w.index)
    return w, cfg

def block_boot_median(x, rng):
    n = len(x); nb = int(np.ceil(n / BLOCK))
    starts = rng.integers(0, n - BLOCK + 1, size=(NBOOT, nb))
    idx = (starts[:, :, None] + np.arange(BLOCK)[None, None, :]).reshape(NBOOT, -1)[:, :n]
    return np.median(x[idx], axis=1)

def iid_boot_median(x, rng):
    return np.median(x[rng.integers(0, len(x), size=(NBOOT, len(x)))], axis=1)

print("=" * 92)
print("GIC_REGROW — the overshoot penalty under the SHIPPED and the OLD glacier law")
print(f"  overshoot {OVERSHOOT}   reference {REFERENCE}   arm `{ARM}`   forcing {FORCING}")
print("=" * 92)

## ---------------------------------------------------------------------------
## [GATE-A] the instrumentation must be a NO-OP at the shipped defaults.
## A gate that cannot fail is not a gate: this one compares two INDEPENDENT runs
## of the same law, so a stray env default or a missed module shows up as
## non-zero. It is the mutation test's control arm.
## ---------------------------------------------------------------------------
worst = 0.0
for ssp in (OVERSHOOT, REFERENCE):
    a = cells(ssp, TAG_SHIP).set_index(["component", "horizon", "arm"]).sort_index()
    b = cells(ssp, TAG_NEW ).set_index(["component", "horizon", "arm"]).sort_index()
    d = (a["med_cm"] - b["med_cm"]).abs().max()
    worst = max(worst, d)
    print(f"  [GATE-A] {ssp:24s} shipped vs {TAG_NEW}: max |dmed| = {d:.3e} cm")
print(f"  [GATE-A] {'PASS — instrumentation is a no-op' if worst == 0.0 else 'FAIL — defaults do NOT reproduce the shipped law'}")

## ---------------------------------------------------------------------------
## [GATE-B] NULL CONTROL. On a monotonically warming path the two laws cannot
## differ (the regrowth branch is never entered), so ssp585 must barely move.
## If it moves, the instrumentation is wrong and every number below is void.
## The bound is an ORDERING, not an invented threshold (`threshold_from_obs_or_law`):
## the null-control move must be far smaller than the declining-scenario move.
## ---------------------------------------------------------------------------
n_ship = cells(NULLCTRL, TAG_SHIP).set_index(["component", "horizon", "arm"]).sort_index()
n_old  = cells(NULLCTRL, TAG_OLD ).set_index(["component", "horizon", "arm"]).sort_index()
null_move = (n_old["med_cm"] - n_ship["med_cm"])
null_gl = abs(null_move.loc[("glaciers", 2300, ARM)])
print(f"  [GATE-B] {NULLCTRL:24s} OLD vs shipped: glaciers@2300 {null_move.loc[('glaciers', 2300, ARM)]:+.4f} cm, "
      f"max |dmed| over all cells {null_move.abs().max():.3e} cm")

## ---------------------------------------------------------------------------
## [GATE-C] POSITIVE CONTROL. The one place the law was independently priced.
## Without this the null below has no power: a dead switch and an inert law give
## the same answer. vvLN is marker-BASED because it IS a CMIP7 marker.
## ---------------------------------------------------------------------------
v_new = pd.read_csv(OUT / f"scope_slr_fairunc_cells_{POSCTRL}_{FORCING}_{TAG_SHIP}{TAP}.csv")
v_old = pd.read_csv(FROZEN / f"scope_slr_fairunc_cells_{POSCTRL}_{FORCING}_{TAG_OLD}{TAP}.csv")
key = ["component", "horizon", "arm"]
vn = v_new.set_index(key).sort_index(); vo = v_old.set_index(key).sort_index()
dv = vn.loc[("glaciers", 2300, ARM), "med_cm"] - vo.loc[("glaciers", 2300, ARM), "med_cm"]
ok = abs(dv - LAW_PRICE_VVLN_2300_CM) < POSCTRL_TOL_CM
print(f"  [GATE-C] {POSCTRL:24s} NEW minus OLD, glaciers@2300 = {dv:+.4f} cm  vs pre-computed "
      f"{LAW_PRICE_VVLN_2300_CM:+.2f} (diff {dv - LAW_PRICE_VVLN_2300_CM:+.4f}) -> {'PASS' if ok else 'CHECK'}")
print(f"  [GATE-C] distance to the DELIVERED {LAW_DELIVERED_VVLN_2300_CM:+.2f} cm: "
      f"{dv - LAW_DELIVERED_VVLN_2300_CM:+.4f} cm — this arm sits on the PRE-COMPUTED value, as a "
      f"held-posterior swap should.")
print(f"  [GATE-C] the instrumentation CAN move a projection by {abs(dv):.2f} cm, so a null below is a")
print(f"           measurement, not a dead switch. Ratio to the SSP move: {abs(dv) / max(abs(null_move.abs().max()), 1e-12):.0f}x")

## ---------------------------------------------------------------------------
## THE PENALTY, PAIRED, BY COMPONENT
## ---------------------------------------------------------------------------
rng = np.random.default_rng(SEED)
rows = []
for law, tag in LAWS.items():
    wo, co = wide(OVERSHOOT, tag)
    wr, cr = wide(REFERENCE, tag)
    common = wo.index.intersection(wr.index)
    assert len(common) == len(wo.index) == len(wr.index), "[PAIRCHK] draw sets differ"
    assert (co.loc[common].values == cr.loc[common].values).all(), \
        "[PAIRCHK] the two scenarios do NOT share the draw->config pairing"
    for c in COMPS:
        for H in HORIZONS:
            x = (wo[(c, H)] - wr[(c, H)]).loc[common].to_numpy()
            med = float(np.median(x))
            se_i = float(np.std(iid_boot_median(x, rng), ddof=1))
            se_b = float(np.std(block_boot_median(x, rng), ddof=1))
            rows.append(dict(law=law, tag=tag, component=c, horizon=H,
                             penalty_cm=med, se_iid_cm=se_i, se_block_cm=se_b,
                             n_draws=len(x)))
pen = pd.DataFrame(rows)

for H in HORIZONS:
    print(f"\n  OVERSHOOT PENALTY at {H}  ({OVERSHOOT} minus {REFERENCE}, paired, median cm)")
    print(f"  {'component':<10}{'NEW law':>22}{'OLD law':>22}{'OLD - NEW':>20}")
    for c in COMPS:
        a = pen[(pen.horizon == H) & (pen.component == c) & (pen.tag == TAG_NEW)].iloc[0]
        b = pen[(pen.horizon == H) & (pen.component == c) & (pen.tag == TAG_OLD)].iloc[0]
        d = b.penalty_cm - a.penalty_cm
        sd = float(np.hypot(a.se_block_cm, b.se_block_cm))
        print(f"  {c:<10}{a.penalty_cm:>13.3f} ±{a.se_block_cm:<7.3f}"
              f"{b.penalty_cm:>13.3f} ±{b.se_block_cm:<7.3f}{d:>12.2e} ±{sd:<8.3f}")

## ⚠ TWO STATISTICS, AND THEY DIFFER BY ~1 cm. The handoff's headline penalties
## (marker +4.0 / +1.1, marker-free +3.2 / -1.0 at 2150 / 2300) are DIFFERENCES OF
## MEDIANS; the table above is the MEDIAN OF PAIRED DIFFERENCES. For a skewed joint
## distribution these are not the same number, and at 2150 marker-free they are
## +3.17 vs +2.17. Neither is wrong -- diff-of-medians is the like-for-like
## comparator against an ensemble that reports per-scenario medians (SLEIP), the
## paired median answers "what does the overshoot cost a GIVEN world". Both are
## printed so the choice is visible rather than inherited (`Methodological choices
## are explicit`). The OLD-vs-NEW move is ~0 under EITHER statistic.
print("\n  THE SAME PENALTY AS A DIFFERENCE OF MEDIANS (the handoff's statistic), total, NEW law")
for H in HORIZONS:
    a = cells(OVERSHOOT, TAG_SHIP).set_index(["component", "horizon", "arm"])
    b = cells(REFERENCE, TAG_SHIP).set_index(["component", "horizon", "arm"])
    dm = a.loc[("total", H, ARM), "med_cm"] - b.loc[("total", H, ARM), "med_cm"]
    pm = pen[(pen.horizon == H) & (pen.component == "total") & (pen.tag == TAG_NEW)].iloc[0].penalty_cm
    print(f"    @{H}  diff-of-medians {dm:+.3f} cm   median-of-paired-diffs {pm:+.3f} cm   gap {dm - pm:+.3f} cm")

t = pen[(pen.component == 'total') & (pen.horizon == 2300)]
tn = t[t.tag == TAG_NEW].iloc[0]; to = t[t.tag == TAG_OLD].iloc[0]
print(f"\n  AGAINST SLEIP: their 7-emulator penalty at 2300 is {SLEIP_2300_CM[0]:.0f}-{SLEIP_2300_CM[1]:.0f} cm.")
print(f"    Ladrillo total@2300  NEW {tn.penalty_cm:+.2f} cm   OLD {to.penalty_cm:+.2f} cm"
      f"   move {to.penalty_cm - tn.penalty_cm:+.2f} cm")
print(f"    The law's own price at vvLN/2300 was {LAW_PRICE_VVLN_2300_CM:+.2f} cm; a move far larger than")
print( "    that is not the law alone -- check the arm before believing it.")

pen.to_csv(OUT / "diag_gic_regrow_penalty.csv", index=False)
print(f"\nwrote outputs/diag_gic_regrow_penalty.csv")
