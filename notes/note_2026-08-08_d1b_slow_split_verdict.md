# Note 2026-08-08 — D1b: splitting/reassigning the SLOW block does NOT recover the century integral; the cap is topology-invariant

**Context.** Marcus (2026-08-08): the D1 SLOW block is inert until ~1990 yet data-assigned
~33 mm of historical melt — "maybe it should not be one single block, or some of it should
be reassigned to the fast block." D1b tests both, plus the per-member diagnostic, against
the unchanged D1 pre-registered criteria. Script `python/d1b_slow_split.py`; outputs
`outputs/d1b_slow_split.csv`, `d1b_blocks.csv`, `d1b_member_twoparam.csv`,
`figures/d1b_slow_split.png`. Sanity: 3-block sum identity 5.6e-17, reproducibility PASS;
both pathological references reproduce D1 exactly (52.82 / 52.23).

## 1. Per-member two-rung diagnostic (the direct test)

Singleton exact composites (diagnostic-grade fixed frac 0.25), per-region partitions
(sub-decision H defaults one level down):

| reg | com@1.2/1.5/2/3K | amp_b | tau50 1.5/3.0 | b | T_off (glac-K) |
|---|---|---|---|---|---|
| r19 | 31/45/60/70 | 1.03 | 828/213 | 0.67 | **+0.55** |
| r03 | 28/32/46/66 | 1.74 | 644/154 | 0.20 | **−0.69** |
| r09 | 54/68/96/100 | 1.83 | 445/70 | 1.62 | **+1.63** |
| r07 | 45/63/86/97 | 1.63 | 318/70 | 1.05 | **+1.12** |
| r06 | 64/67/79/97 | 0.94 | 316/56 | 0.73 | **−0.93** |

The heterogeneity is REAL — but it does **not** map onto the τ50 axis. The high-committed
mid-τ regions (r09, r07) get their commitment from STEEP b (threshold-like S_eq: ~96%
loss by +2K) with T_off still high, not from a low T_off; the actual historical melters
inside old SLOW are r03 and r06 (negative T_off) — whose τ50 (644/316 yr) is too slow for
that to matter (r03's anchored-dynamics early flow ≈ 0.06 mm/yr). No blocking by τ can
group "equilibrium-proximity" coherently: the two axes are independent in the data.
(Caveats: diagnostic-grade estimator; r19 carries the Marzeion rate-upscale caveat; r09's
amp 1.83 is the largest in regchar.)

## 2. Variant results (same gates + flow criterion; D1 refs in brackets)

- **3BLOCK** POLAR {19,03} (T_off +0.20, κ/ν anchored 0.00083/1.44) / SUBPOLAR {09,07,06}
  (T_off +1.18, a=0.065, 0.00206/1.33) / FAST unchanged: **essentially identical to D1** —
  ANCH deficit 20.6 sx2 [20.7] / 12.0 t5d [11.5], 4/4 gates, S2020 59 mm [57], era rates
  unchanged (0.23/0.35/0.22/0.34/0.75). MID and FREE also within ~0.3 of D1.
- **REASSIGN** (τ*≈500: r09/r07/r06 → FAST): **much worse** — merged FASTX two-rung gives
  T_off −0.08 (the subpolar members drag the composite up from −1.53), which kills the
  FAST block's early excess AND overshoots modern (ANCH: 1/4 gates, rate 1.15, era-1900s
  0.01 mm/yr, deficit 17.3–67.8; inventory/S1900/ladder all fail). The one-pool shape
  failure resurrected *inside* FASTX — lumping across both axes breaks the block that was
  working.
- **0/12 feasible.** Verdict unchanged from D1.

## 3. Reading

Three block topologies (D1 2-block, 3-block, τ*500 reassign) + κ-freedom (MID, both runs)
all land on the same missing ~45–50 mm of pre-2000 melt. **The century-integral cap is
topology-invariant: it is set by GlacierMIP3's response times + committed ladders + the
exponential S_eq form, not by how regions are grouped.** Escape routes remain exactly the
§6 menu of `handoff_2026-08-07_d1_multireservoir_verdict.md`: trust modern+projections and
discount the early historical target (T5c or T5d-extended), or distrust the GlacierMIP3
response-time anchors for HISTORICAL (bigger, differently-shaped) glaciers — a physical
argument that present-geometry τ50s overstate early-century response times, which would be
a labeled κ(t)/geometry-drift variant, i.e. new scope. Reassignment is off the menu.
