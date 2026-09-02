# Handoff — GIC_REGROW is DONE and NEGATIVE; Antarctica is the live candidate

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, all pushed. Written 2026-09-02.
Supersedes `handoff_2026-09-02b_l24_champion_markers_and_the_regrow_test.md` (whose §1-§3 all
still stand; only its §4 is now closed).

⭐ **FIRST THING NEXT SESSION: the AIS hysteresis diagnostic (§3).** GIC_REGROW answered and the
answer was negative, and the decomposition it produced hands you the next target on evidence
rather than on a guess.

---

## 1. WHAT §4 OF THE LAST HANDOFF RETURNED

**The floored-equilibrium glacier law is NOT why Ladrillo recovers from an overshoot.** Full
detail in `notes/note_2026-09-02_gic_regrow_attribution.md`; memory
`gic_regrow_not_the_penalty`; reproduce with `python python/diag_gic_regrow_penalty.py` (no args).

Swapping back to the melt-only ratchet on the **held L24 posterior, no refit**, moves the penalty
by **≤ 6.2e-05 cm** anywhere, against a block-bootstrap bar of **±0.008 to ±0.068 cm**.

The null is **powered**, and getting it powered took three tries — see §2.

## 2. ⚠ THREE THINGS THE LAST HANDOFF GOT WRONG, AND ONE I GOT WRONG

* ⛔ **`R = Inf` ALONE *IS* the old law.** The ⚠⚠ warning was wrong in that direction. `S_eq < 0`
  requires `T < T_off`; `T_eq ≥ T_off` always (`frac_left ≤ 1` ⇒ `−log(frac_left) ≥ 0`); so
  `S_eq < 0` ⇒ `d < 0` ⇒ `mult /= Inf`. **The floor is unreachable under `R = Inf`.** Confirmed
  empirically: `S_eq<0` fired 219,602 times and `d<0 AND S_eq<0` fired 219,602 times — identical.
  The half-law that *does* differ is the other one, `FLOOR=0` with `R=1`.
* ⛔ **`scope_amp_likelihood_tilt_INSTRUMENTATION.patch` already carries a nu3 hunk** — it has two
  diff sections, not one. The "it instruments the WRONG MODULE" warning was mistaken.
* ⛔ **`glaciers_nu_component.jl` is DEAD CODE on the projection path** (`nu calls = 0`). Only nu3
  runs. The "the law lives in FOUR places" warning still holds for the port gates, but only one of
  the two Julia modules is live.
* ⛔ **MY OWN GATE-A WAS VACUOUS** and I reported it as a pass before noticing. "Defaults reproduce
  the shipped arms, 0.000e+00" passes *identically* whether the switch works or is ignored — it is
  a no-op check, not evidence. What rescued it: a direct `_nu_step` probe, branch counters
  (222,764 of 5,454,000 steps enter the cooling branch), and **GATE-C, a positive control on vvLN
  with an independently pre-computed answer of −0.20 cm, measured −0.2027, = 9,721× the SSP move.**
  ⇒ **Any future law-swap experiment must ship a positive control, not just a no-op check.**

## 3. ⭐ THE NEXT EXPERIMENT — AIS HYSTERESIS

**The evidence.** Penalty by component (paired median, `ssp534over_nomarker − ssp126_nomarker`,
joint arm, marker-free, cm):

| horizon | glaciers | gis | **ais** | te | total |
|---|---|---|---|---|---|
| 2150 | +0.569 | +0.345 | **+0.433** | +0.577 | +2.168 |
| 2300 | −0.064 | −0.365 | **+0.003** | −1.089 | −1.227 |

⛔ **CORRECTED, SAME DAY — do not read the 2300 row as hysteresis.** `python/diag_ais_regrowth.py`:
the AIS has **ZERO years of decline after 2100** on both SSPs and all seven van Vuuren markers
(2/2000 draws), so **it never regrows at all**. The penalty closes because our SSP5-3.4-OS crosses
BELOW our SSP1-2.6 in **2127** and stays **0.126 K cooler**, so the reference arm loses ice faster
and catches up — both arms lose mass throughout. **The 2300 AIS row is the dT bias, not recovery.**

**Hypothesis (untested).** `INDEX_ais` records that **MICI needs `antarctic_lambda` above the paleo
prior's maximum and is therefore outside our representable set.** MICI is a mechanism that cannot
be undone once triggered — so its absence is *precisely* an absence of hysteresis. If that is the
story, our near-zero 2300 penalty is a structural consequence of the DAIS parameterisation, not a
result about overshoots.

**Design.** A component-wise hysteresis diagnostic, **not** another law swap:
1. For each draw, find the AIS state at the GMST peak and at the GMST re-convergence date, and
   measure whether AIS returns to the ssp126 trajectory or holds an offset.
2. Split draws by `antarctic_lambda` and by whether the DAIS retreat threshold was crossed. The
   prediction is that the penalty at 2300 is carried *entirely* by threshold-crossing draws and is
   ~0 for the rest — if instead it is ~0 in both, the mechanism is not threshold retreat.
3. ⚠ **Measure the POWER first.** `spread_blind_to_its_own_tail` already caught a "0.000 cm"
   ssp126 AIS result that was the statistic, not the model. Use the tail, not the p05-p95 spread.

⚠ **Do not read the 2300 total (−1.227 cm) as physics.** Our SSP5-3.4-OS ends 0.06-0.13 K COOLER
than our SSP1-2.6, which drags `te` to −1.089 and `gis` to −0.365. The AIS row is the informative
one because it is near zero from *both* directions.

## 4. ⚠ "THE PENALTY" IS TWO STATISTICS AND THEY DIFFER BY 1 cm

The last handoff's headline numbers are **differences of medians**; the table in §3 is the
**median of paired differences**. Marker-free total: +3.169 vs +2.168 at 2150, −1.035 vs −1.227 at
2300. The gap is real skew in the joint distribution. Diff-of-medians is the like-for-like
comparator against SLEIP (which reports per-scenario medians); the paired median answers "what does
an overshoot cost a GIVEN world". **State which one you are quoting.** Both are printed by the
diagnostic. Everything in §1 holds under either.

## 5. GOTCHAS CARRIED FORWARD

* Everything in the previous handoff's §5 still applies (chain sizes, tapped arms, dropped flags,
  L23-vs-L24 prior confusion).
* **Frozen-worktree recipe that worked**, if you need another held-posterior swap: copy `julia/`
  and `julia_v2/`, **symlink** `data/`, and make `outputs/` a real directory of symlinks to the
  repo's — then a write under a NEW tag creates a new real file and cannot clobber anything.
  Drive with `--tag=<NEWTAG> --chain-tag=L24`, and pre-place a
  `ssps_components_2300_<NEWTAG>_tap..._n2_ws.csv` symlink or the driver errors at const time.
* `outputs/gic_regrow_INSTRUMENTATION.patch` is the exact diff used, against the shipped modules.
* ✅ **Memory consolidated 2026-09-02.** ⚠ **Budgets are measured on CONTENT, not the file** — strip
  the HTML comment blocks first, or you "fix" a compliant index (MEMORY.md is 16.0 KB as a file and
  11.6 KB as content, i.e. compliant). `INDEX_slr` trimmed 15.4 → 14.7 KB content. Still over SOFT,
  none over hard: `INDEX_ccx_arch` +1982, `INDEX_ccx` +1521, `INDEX_slr` +372, `INDEX_cmp` +327.
  ⭐ The two CCX ones were left for a session with CCX context loaded — and there is a specific lead:
  `INDEX_ccx_arch` (an ARCHIVE, "provenance only, never live state") cites **6 targets that the LIVE
  `INDEX_ccx` also cites**, including `ccx_one_basin_at_25_par` and `ccx_gate_ledger_power`, which
  MEMORY.md carries as CURRENT rulings. An archive holding live state is the thing to check first.
