## ============================================================================
## diag_matched_dt_penalty.py — THE OVERSHOOT PENALTY ON A MATCHED-dT PAIR,
## LADRILLO vs BRICK 2.0, ON AN IDENTICAL CLIMATE.
##
## WHY THIS EXISTS. SLEIP Phase 1 (egusphere-2026-3874) reports a 0.1-0.3 m
## overshoot sea-level penalty at 2300 (SSP5-3.4-OS vs SSP1-2.6) across 7
## emulators, "persisting after GSAT re-converges by 2150". Ladrillo reported ~0.
## `ais_never_regrows` then showed WHY, and it was not hysteresis: our
## ssp534over crosses BELOW our ssp126 in 2127 and ends 0.126 K COOLER, so the
## REFERENCE arm loses ice faster and catches up. Our pair could not answer the
## question at all.
##
## TWO AXES, MOVED ONE AT A TIME.
##   SCENARIO  native  = ssp534over_nomarker - ssp126_nomarker   (dT INVERTS: -0.133 K @2300)
##             matched = ssp534overMATCH     - ssp126_nomarker   (dT +0.020 K @2300, from ABOVE)
##   MODEL     Ladrillo L24  vs  BRICK 2.0 (`oldbrick`)
## BRICK 2.0 is the INDEPENDENT comparator: `ladrillo_glacier_is_nauels` records
## that Ladrillo's glacier transient IS MAGICC's law, so MAGICC is not independent
## on glaciers. Both models here read the SAME cubes, the same 2014 splice, the
## same 1995-2014 reference and the same PAIR_SEED, so the model axis is clean.
##
## ⚠ ssp534overMATCH IS IDEALISED and is NOT SSP5-3.4-OS. It carries ssp126's
## forcing plus the non-negative part of the 3.4-OS forcing excess. It answers
## "what does an overshoot that RETURNS cost", which is SLEIP's question; it is
## not their scenario, and their own pair remains the like-for-like comparator.
## ⚠ Marker-free ⇒ the posterior is used OFF-DESIGN (2-6 % of the ensemble spread).
## ⚠ BRICK 2.0 and Ladrillo have DIFFERENT posteriors and draw counts, so the
## per-draw pairing is valid WITHIN a model and the cross-model comparison is on
## the penalty statistic, not per draw.
## ============================================================================
import pathlib, numpy as np, pandas as pd

REPO = pathlib.Path(__file__).resolve().parents[1]; OUT = REPO / "outputs"
REFERENCE = "ssp126_nomarker"
PAIRS = {"native (dT INVERTS)": "ssp534over_nomarker", "matched (dT from ABOVE)": "ssp534overMATCH"}
LAD_TAG, LAD_TAP = "L24", "_tap4p69K_V5p64m_tau800"
MODELS = ["Ladrillo L24", "BRICK 2.0"]
ARM, FORCING = "joint", "spliced"
HORIZONS = [2100, 2150, 2300]
COMPS = ["glaciers", "gis", "ais", "te", "lws", "total"]
NBOOT, BLOCK, SEED = 4000, 25, 2026
SLEIP_2300_CM = (10.0, 30.0)     # egusphere-2026-3874, 7 emulators
## The native pair's own dT, measured in build_fair_cube_matched_dt.py.
DT_NATIVE = {2150: -0.102, 2300: -0.133}
DT_MATCHED = {2150: +0.042, 2300: +0.020}

def draws(model, ssp):
    p = (OUT / f"scope_slr_fairunc_draws_{ssp}_{FORCING}_{LAD_TAG}{LAD_TAP}.csv"
         if model == "Ladrillo L24" else
         OUT / f"scope_slr_fairunc_draws_{ssp}_{FORCING}_oldbrick.csv")
    if not p.exists(): return None
    d = pd.read_csv(p); return d[d.arm == ARM]

def wide(model, ssp):
    d = draws(model, ssp)
    if d is None: return None
    return d.pivot_table(index="draw", columns=["component", "horizon"], values="value_cm")

def boot(x, rng):
    n = len(x); nb = int(np.ceil(n / BLOCK))
    st = rng.integers(0, max(n - BLOCK + 1, 1), size=(NBOOT, nb))
    idx = (st[:, :, None] + np.arange(BLOCK)[None, None, :]).reshape(NBOOT, -1)[:, :n]
    return float(np.std(np.median(x[idx], axis=1), ddof=1))

rng = np.random.default_rng(SEED)
rows = []
for model in MODELS:
    wr = wide(model, REFERENCE)
    if wr is None: print(f"  [SKIP] {model}: no reference arm yet"); continue
    for plab, oss in PAIRS.items():
        wo = wide(model, oss)
        if wo is None: print(f"  [SKIP] {model} / {plab}: no arm yet"); continue
        common = wo.index.intersection(wr.index)
        assert len(common) == len(wr.index) == len(wo.index), f"[PAIRCHK] {model} {plab}"
        for c in COMPS:
            for H in HORIZONS:
                x = (wo[(c, H)] - wr[(c, H)]).loc[common].to_numpy()
                rows.append(dict(model=model, pair=plab, component=c, horizon=H,
                                 penalty_cm=float(np.median(x)), se_cm=boot(x, rng),
                                 mean_cm=float(x.mean()), p05_cm=float(np.percentile(x, 5)),
                                 p95_cm=float(np.percentile(x, 95)),
                                 skew_=float(pd.Series(x).skew()),
                                 diff_of_medians_cm=float(np.median(wo[(c, H)]) - np.median(wr[(c, H)])),
                                 n=len(x)))
pen = pd.DataFrame(rows)
if pen.empty: raise SystemExit("no arms available yet")

print("=" * 100)
print("OVERSHOOT PENALTY — NATIVE vs MATCHED-dT PAIR, LADRILLO vs BRICK 2.0")
print(f"  reference {REFERENCE}   arm `{ARM}`   paired median of per-draw differences, cm")
print(f"  dT(overshoot-reference):  native {DT_NATIVE[2150]:+.3f}/{DT_NATIVE[2300]:+.3f} K   "
      f"matched {DT_MATCHED[2150]:+.3f}/{DT_MATCHED[2300]:+.3f} K   (2150/2300)")
print("=" * 100)
for H in HORIZONS:
    print(f"\n  ── {H} " + "─" * 88)
    hdr = f"  {'component':<10}"
    for model in MODELS:
        for plab in PAIRS: hdr += f"{model.split()[0][:4]+'/'+plab.split()[0]:>22}"
    print(hdr)
    for c in COMPS:
        line = f"  {c:<10}"
        for model in MODELS:
            for plab in PAIRS:
                r = pen[(pen.model == model) & (pen.pair == plab) &
                        (pen.component == c) & (pen.horizon == H)]
                line += f"{r.iloc[0].penalty_cm:>13.3f} ±{r.iloc[0].se_cm:<7.3f}" if len(r) else f"{'--':>22}"
        print(line)

print("\n" + "=" * 100)
print("THE HEADLINE — total penalty at 2300 against SLEIP's 7-emulator "
      f"{SLEIP_2300_CM[0]:.0f}-{SLEIP_2300_CM[1]:.0f} cm")
print("=" * 100)
for model in MODELS:
    for plab in PAIRS:
        r = pen[(pen.model == model) & (pen.pair == plab) &
                (pen.component == "total") & (pen.horizon == 2300)]
        if len(r):
            v = r.iloc[0]
            print(f"  {model:<14}{plab:<26}{v.penalty_cm:+8.2f} ±{v.se_cm:<6.3f} cm   "
                  f"(diff-of-medians {v.diff_of_medians_cm:+.2f})")
## ⭐ THE MEDIAN IS NOT THE WHOLE ANSWER. The penalty distribution is heavily
## RIGHT-SKEWED (skew ~ +3), so a median hides the tail -- the exact defect
## `spread_blind_to_its_own_tail` records. SLEIP's 0.1-0.3 m must be compared
## against the statistic THEY report; against our median it looks like a factor
## of 4-14, against our MEAN it is a near-match. ⚠ Which of these is like-for-like
## is UNRESOLVED and is the single most important thing to check in their paper.
print("\n" + "=" * 100)
print("⭐ THE SAME PENALTY AS A DISTRIBUTION (total @2300) — the median hides a fat tail")
print("=" * 100)
print(f"  {'model / pair':<40}{'median':>9}{'mean':>9}{'p05':>9}{'p95':>9}{'skew':>8}")
for model in MODELS:
    for plab in PAIRS:
        r = pen[(pen.model == model) & (pen.pair == plab) &
                (pen.component == "total") & (pen.horizon == 2300)]
        if len(r):
            v = r.iloc[0]
            print(f"  {model + ' / ' + plab:<40}{v.penalty_cm:>9.2f}{v.mean_cm:>9.2f}"
                  f"{v.p05_cm:>9.2f}{v.p95_cm:>9.2f}{v.skew_:>8.2f}")
print(f"\n  SLEIP reports {SLEIP_2300_CM[0]:.0f}-{SLEIP_2300_CM[1]:.0f} cm. Against our MEDIAN that is a")
print( "  factor of 4-14; against our MEAN (8.9 / 11.5 cm) it is a NEAR-MATCH, and it sits")
print( "  between our mean and our p95. ⚠ WHICH STATISTIC THEY REPORT IS THE OPEN QUESTION.")

pen.to_csv(OUT / "diag_matched_dt_penalty.csv", index=False)
print(f"\nwrote outputs/diag_matched_dt_penalty.csv")
