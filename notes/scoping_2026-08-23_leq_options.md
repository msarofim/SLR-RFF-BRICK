# Scoping — `L_eq` options, and whether CLIMBER-X should be dropped

Written 2026-08-23. Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, from `f04f213`.
Companion to `handoff_2026-08-23_greenland_targets.md`.

---

## 0. TWO CORRECTIONS TO WHAT I SAID EARLIER TODAY

**(a) CLIMBER-X is NOT the only source for the threshold location.** I wrote that in
`bc86c31` and `f04f213`. It is wrong. `data/observations/greenland_equilibrium_bochow2023.csv`
has been tracked in this repo since 2026-08-10 and carries **two** ice-sheet models
run to equilibrium (Bochow et al. 2023, Nature 622:528):

| source | threshold, GMT above PI | how located |
|---|---|---|
| Yelmo-REMBO (tracked ladder) | between **1.68 and 1.76 K** | 0.76 m → 4.90 m in one rung |
| PISM-dEBM (tracked ladder) | between **2.18 and 2.60 K** | 1.64 m → 6.28 m in one rung |
| CLIMBER-X (new today) | **1.44–2.24 K**, 8km ref 1.71 | half-sheet crossing, 9 configs |

CLIMBER-X lands between the two models we already had. It **corroborates and adds
nothing**.

**(b) The option space is far more explored than I implied.** Options C, D and 2 were
tried and killed between 2026-08-10 and 2026-08-22. Anything proposed below has to
clear that history, not restate it.

---

## 1. SHOULD CLIMBER-X BE DROPPED? — YES, AS A TARGET

Not because it is a bad model, but because it is **redundant and the weakest-gated of
the three**:

* It fails the priority-1 gate on the target: fastest first century **0.117 mm/yr at
  1.09 K** against an observed **0.593 mm/yr** — 5.1× slow (`diag_gis_climberx_commitment.py` §3b).
* Its only unique contribution was the threshold location, and §0(a) shows two better
  sources already had it.

**Keep it for exactly one thing** and label it that way: it is the only source here that
*scans stabilisation levels with a coupled climate*, so it is the evidence that the
threshold is a property of sustained GMT rather than of a particular SMB forcing file.
Demote it to a corroborating third voice in the docstrings; do not let any number
depend on it.

⚠ **The gate that killed it cannot be applied to the ladders at all.** Bochow's rungs
are equilibrium-only — there is no transient to compare with observations. So the
ladders are *unfalsifiable by priority 1*, which is a reason to use them for **shape**
and never for **rate**. **Greve/SICOPOLIS is the only commitment-relevant source that
reaches millennial horizons AND passes the observational gate.** It should be the anchor.

---

## 2. WHAT IS ALREADY DEAD, WITH RECEIPTS

| option | form | why it died |
|---|---|---|
| **C** | ladder `L_eq` inside proportional relaxation `r·(L_eq − L)` | the rate scales WITH `L_eq`; a 20× commitment gives a 20× near-term rate. Hindcast RMSE **1.675**, 72 cm @2100. Abandoned by Marcus 2026-08-16 (`ladrillo_option_c`) |
| **D** | throughput cap `min(r(L_eq − L), q)` | wherever the cap binds, `dL/dt` is **algebraically independent** of `L_eq`. Capped 99–100% of projection years ⇒ identical 2100 to 6 dp under all three SSPs |
| **2 (γ)** | state-dependent rate accelerator | bounded by **1/φ**, and φ(2300) is already **0.84–0.92** at L14 ⇒ ceiling ×1.125 against the 1.97× needed. Also moves 2100 by +4.7 cm and is not likelihood-inert |
| **monotone families** | Prony, stretched-exp, Mittag-Leffler, power-law, common-τ ladder | exact bound: any completely monotone response has `d ln τ_eff/d ln s < 1` (numerical max 0.9997); the warm arm needs **1.31** |
| **`RAMP_W_K`** | shaped ramp on the reservoir | buys 1.074× on LEVEL while the RATE pass count goes 4 → **0** |
| **T-space, single `c`** ⟵ **NEW, killed today** | `dL/dt = c·(T − Θ(L))₊`, `Θ = L_eq⁻¹`, `L_eq` = tracked ladder | ran `diag_gis_stepback_lit_leq.py`. `c` fitted to the 5 arms = 0.0297 ⇒ hindcast **0.47 cm vs observed 5.78 = 0.08×**. History alone wants `c` = 0.107, 3.6× larger, which then overshoots both cool arms. **No single melt constant serves history and the arms.** |

**They all failed the same way.** Every one of them couples the near-term rate to the
size of the commitment, so raising the commitment to what the physics demands raises
the near-term rate and breaks history and/or 2100. That is the (`L_eq`, τ) degeneracy
[[gis_leq_shape_refuted]] expressed as a design constraint:

> **Any admissible form must let the total commitment grow ~40× WITHOUT the near-term
> flux moving.** That single sentence kills C, D, γ and the T-space form on sight.

---

## 3. WHAT SURVIVES — AND TODAY'S EVIDENCE PICKS ITS FREE PARAMETER

**Option 3, the flux reservoir**, is the only structure that satisfies the constraint
above, because it separates the two: the near-term flux is **ψ = 100·V/τ** and the total
is **V**. The arc already found 86/216 cells clearing 2100 + all three matched 2300
bands + the 5-arm shape, with **only ψ identified**, not V and τ separately.

**The commitment evidence breaks that degeneracy from outside.** Greve's year-3001
losses require, per cell (flux years counted from the 4.69 K onset crossing):

| cell | onset yr | flux yr | Greve − ours (cm) | ψ required |
|---|---|---|---|---|
| CNRM-CM6-1 ssp585 | 2082 | 919 | 188.2 | **0.205** |
| UKESM1-0-LL ssp585 | 2069 | 932 | 260.8 | **0.280** |
| CESM2 ssp585 | 2078 | 923 | 314.9 | **0.341** |
| CNRM-ESM2-1 ssp585 | 2087 | 914 | 163.3 | **0.179** |

**ψ = 0.179–0.341 cm/yr, median 0.242** — against the **0.273–0.282** that the
2250–2300 *rate* criterion gave independently, and against the **0.125** the shipped
cell A carries. Two measurements ~900 years apart in horizon, agreeing to ~10%, and
both saying the shipped cell is ~2.2× short — which is exactly the "hits the 2300 LEVEL
and misses the rate 2.2×" already in memory.

At **V = the whole sheet (7.42 m)**, ψ = 0.273 ⇒ **τ ≈ 2700 yr**; ψ = 0.242 ⇒ **τ ≈ 3060 yr**.
That is the V = 6 m / τ = 2200 end of the ridge the arc could not choose between —
**and it is now chosen by evidence rather than by grid.**

> This is the payoff of today's work. The internal scan could only ever identify ψ.
> The commitment data identifies **V**, and V then fixes τ.

---

## 4. THE THING THIS SCOPING FOUND THAT NOBODY WAS LOOKING FOR

**The reservoir's onset is at 4.69 K GMST. Every equilibrium ladder puts the Greenland
threshold at 1.7–2.6 K.** The onset is **2.0–2.8× too high**, and the record is explicit
about where it came from: memory `gis_tap_priced_l13` — *"Bracket floor 4.69 K = exactly
the 'don't move 2100' constraint"*. It was chosen to protect 2100, not from evidence.

Two consequences:

1. **The protection was protecting a defect.** 16 ISMIP6 ice-sheet models say 2100 is
   already running **1.30× fast** [[gis_2100_fast_vs_ismip6]]. Holding the onset above
   every scenario's 2100 warming to keep 2100 fixed preserved a value that is wrong.
2. **It is why no cool-arm failure is repairable.** The reservoir is inert below onset,
   so ssp126/ssp245 never see it — and the Greve ssp126 cell still shows a **26.1 cm**
   gap at 3001 that nothing in the current structure can supply. Lowering the onset to
   the ladder's 1.7–2.6 K is the only thing that reaches the cool arms at all.

**This is the highest-value single change available, and it is a one-line prior move,
not new machinery.**

---

## 5. RECOMMENDED ORDER

1. **Re-scan onset over 1.5–3.0 K** (the ladder range) with V and τ free, scoring
   history + 2100(ISMIP6 median) + 2300(PROTECT+Greve) + 3000(Greve). Cheap; the scan
   exists. Expect 2100 to move — that is now a *feature*, and the ISMIP6 median is the
   target it should move toward.
2. **Pin V to the ladder** (95–100% of the sheet above ~2.5 K) and let τ follow from
   ψ ≈ 0.24–0.28. Tests whether the two-sided determination in §3 is self-consistent.
3. **Only if 1–2 fail**, consider a genuinely new form. Note that priority 5 (simpler is
   better) and §2's constraint together leave very little room: the flux reservoir is
   close to the *simplest* object that decouples total from rate.
4. **Do not re-propose** C, D, γ, any completely-monotone family, `RAMP_W_K`, or a
   single-constant T-space form.

**Still not run:** §4.1, the NPV/SC-GHG sensitivity to τ. It is now more relevant, not
less — τ moves from 800 to ~2700 yr under §3, and the discount factor at 2250 is 0.0012,
so this may show the whole τ question is worth ~nothing to the deliverable. **Run it
before step 1**, not after: it decides how much any of this is worth.
