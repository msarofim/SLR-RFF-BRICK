# Note 2026-08-09 — D1e (Option-D ledger) verdict: P1/P2 confirmed, ANCH/MID now 4/4 gates on the honest target; P3 falsified — the FREE arm's high early melt is flow-driven, not Leclercq-driven

Script `python/d1e_dside_ledger.py` (commit 0646571); outputs
`outputs/d1e_dside_ledger.csv`, `figures/d1e_dside_ledger.png`. Spec + P&M receipts:
`memo_2026-08-09_d_ledger_target_spec.md`. Sanity 4/4 (obs_adj invariants; structures
reproduce `d1d_blocks.csv` to 5e-6; stored d1d θ evaluation identity to 0.035;
ledger arithmetic). Pathological comparators with matched (U_pre, S_r5) freedom are
statistically unchanged from d1d (Δ ≤ 0.04) — their fitted U_pre rails at 0 (a free
single-reservoir already puts S(1900) where the datum wants it).

## 1. Results (datum untouched at N(20, 9); gate g_lec |z| ≤ 2)

| row | deficit (d1d) | ledger = S_inv + S_r5 + U_pre | z | legacy (box) | rate vs 0.766 | npass |
|---|---|---|---|---|---|---|
| **ANCH/unc_t5d (HEADLINE)** | **8.22 (8.21)** | 8.1 + 2.5 + 9.4 = 20.0 | −0.00 | 8.1 (OUT) | 0.966 | **4/4** |
| MID/unc_t5d | 6.79 (6.58) | 7.0 + 2.5 + 10.5 = 20.0 | −0.00 | 7.0 (OUT) | 0.832 | 4/4 |
| FREE/unc_t5d | 0.60 (0.47) | 26.3 + 2.1 + 0.0 = 28.4 | +0.93 | 26.3 (in) | 0.769 | 3/4 (spr−) |
| ANCH/unc_sx2 | 7.30 (7.34) | 8.1 + 2.5 + 9.4 = 20.0 | +0.00 | 8.1 (OUT) | 0.966 | 4/4 |
| MID/unc_sx2 | 5.32 (5.07) | 7.1 + 2.5 + 10.4 = 20.0 | −0.00 | 7.1 (OUT) | 0.839 | 4/4 |
| FREE/unc_sx2 | −0.33 (−0.38) | 27.1 + 2.0 + 0.0 = 29.1 | +1.01 | 27.1 (in) | 0.764 | 3/4 (spr−) |

**0/6 feasible (expected — D changes the target's honesty, not the flow deficit).**
Minimal bar (deficit ≤ 8.4, |δ| ≤ 1σ, 4/4): NOT MET **solely on δ = 1.00497σ vs the
≤ 1.0 edge** — the third-decimal box-edge miss predicted in the T1 memo; deficit and
gates now pass.

## 2. Pre-registered outcomes

- **P1 CONFIRMED** — ANCH deficit 8.222 vs 8.211 ± 0.05: the ledger params are
  separable from the ANCH flow fit, exactly as argued.
- **P2 CONFIRMED** — every ANCH/MID row 4/4; U_pre fits interior at **9.4–10.5 mm**
  (comfortably inside the P&M-derived flat [0, 25], and *below* the prior mean 12.5 —
  the datum, not the prior, sets the value); S_r5 stays at its prior mean 2.5 (no
  pull — U_pre closes the gap at zero prior cost, so the Gaussian set-aside is left
  alone). The required pre-1900 uncharted melt for an inventory-scope model, ~9–10 mm,
  lands mid-range of the construction from P&M's own 1901 stock and rates. **Caveat
  stated plainly: unlike U (which fits at the Frederikse central against a wide flat
  prior on a target that verifiably contains uncharted melt), U_pre has NO independent
  constraint — "interior, not railed" is consistency with the literature bound, not
  corroboration by data.**
- **P3 FALSIFIED, informatively** — FREE keeps legacy S(1900) at 26.3–27.1 with U_pre
  railing to **0** (z +0.93/+1.01, still passing). So the d1d FREE arms' ~27–28 mm was
  ~95% flow-preference, not the N(20,9) pull as the T1/D1d notes inferred: **the free
  dynamics genuinely want ~26 mm of pre-1901 block melt to fit the century at noise
  level.** This RAISES the plausibility of the total-scope reading's larger U_pre
  values (the flow data independently like more early melt than the anchored
  structure produces) and slightly weakens the "ANCH-vs-datum tension is pure scope"
  story — worth one sentence of honesty in any write-up.
- **WATCH resolved** — MID/unc_sx2 lands at 5.32 (was 5.07): no feasibility flip. Both
  MID deficits worsen ~0.2–0.3 vs d1d because the old `ll_lec(s_all)` term's κ-up pull
  was mildly flow-aligned (d1d MID flow_win was ~0.3 better); the reshaped objective
  re-prices MID honestly. ANCH deficits are unchanged by construction.

## 3. New emitters (the T2 cheap items, now in the CSV)

- **Per-reservoir modern rates (2000–23, mm/yr; GlaMBIE 0.049/0.189/0.417 for
  R19/SLOWP/FAST):** ANCH 0.002/0.258/0.521 — the modern overshoot is in BOTH
  hindcast blocks (SLOWP +37%, FAST +25%), while model R19 is essentially inert
  (late-onset T_off; obs r19 is small anyway). MID: 0.003/0.187/0.487 — κ freedom
  puts SLOWP **dead on** GlaMBIE and takes FAST to +17%.
- **Era rates (headline, model hind+F vs obs_adj−δ):** 1900–19 0.46 vs 0.59;
  1920–49 0.62 vs 0.66; 1950–79 0.51 vs 0.41; 1980–99 0.46 vs 0.54; 2000–23 0.78 vs
  0.71 — small, mixed-sign residuals (no all-one-sign pathology left in the era
  structure).

## 4. State

Branch `brick-mengel-vnext`; nothing running. The D-ledger is now the operative
S(1900) treatment in the offline cells; `julia/calibrate_mcmc_ext.jl` carries the
spec + TODO at A2b for the extC surgery (change-together honored at the spec level;
the live pre-D term dies with the glacier-block replacement). Legacy 10–30 box
verdicts remain reported per the original-metric rule. Outstanding cheap arm:
obs-amp sensitivity. **Pending Marcus: extC green-light** (assets: D1d list + this
ledger + the T2 recommendation items).
