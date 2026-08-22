# Addendum to `handoff_2026-08-22_greenland_flux_deliverable.md` — §4.2 discharged, stages 1a/1b run

Written 2026-08-22. Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`.
Commits: `3f920fb` (§4.2), `c087ba2` (stages 1a+1b), CHANGELOG `2026-08-22c`.

**§4.1 — the NPV/SC-GHG sensitivity to τ — was deliberately NOT run** (Marcus set it
aside for this session). It remains the one unrun item of the parent handoff's §4, and
it is still the cheapest thing on the list.

**This addendum SUPERSEDES the parent handoff's §1.2 ranking and its §5 stage-1a/1b
entries. §1.1, §1.3, §1.4, §2, §3 and §7 are UNCHANGED** — §1.1 and §1.3 are in fact
confirmed below, with their domains of validity now measured rather than asserted.

---

## 0. THE ONE-PARAGRAPH VERSION

The amplification question is **discharged and it does not bite**: across four laws
spanning a **1.48×** range in effective amplification at our own ssp585@2300, the
required flux moves **1.01×** (ψ = 0.279–0.282 cm/yr), and the law above 2.75 K is
**exactly hindcast-inert** so it stays revisable with no refit. **But stage 1b
overturns the parent handoff's cell ranking.** Applied as a *band* rather than as a
*point*, the rate criterion cuts 526 admissible cells to **7**, and the survivor is
**cell A (ψ = 0.125)** — the cell §1.2 demoted. Two structural reasons, and the second
is the one that matters for wiring: the PROTECT rate band spans **4.3× on 35 runs that
are only 5 GCM clusters**, so it holds cell A and cell B alike; and since **ψ = 100·V/τ**,
the 2.73 m NO+NE inventory caps ψ at **0.124 cm/yr at τ = 2200 yr** against the 0.273 cell B
needs — **cell B is a whole-sheet object, not a high-basin tap, and no scan setting changes
that.** Stage 1a is a **STOP**.

---

## 1. §4.2 — THE AMPLIFICATION LAW ABOVE 2.75 K (`python/diag_gis_amp_above_275.py`)

Gated: the local driver reproduces `regional_driver` under the shipped law to
**3.6e-15 K**, so the other three laws differ *only* in the amp field.

| law | amp @7.81 K | amp @13.63 K | base 2300 | **ψ_rate** | ψ_level | ratio |
|---|---|---|---|---|---|---|
| `held` S flat above 2.75 K **[SHIPPED]** | 1.652 | 1.652 | 49.9 | **0.279** | 0.269 | 0.97 |
| `full` CMIP6 binned to 5.75 K, then flat | 1.586 | 1.586 | 47.7 | **0.280** | 0.282 | 1.01 |
| `decl` full + the −0.0503/K decline *continued* | 1.453 | 1.077 | 43.8 | **0.280** | 0.304 | 1.08 |
| `summer` Bochow melt-relevant, `GMT = f_conv/1.19 + 0.5` inverted | 1.114 | 1.146 | 38.1 | **0.282** | 0.335 | 1.19 |

ψ in cm/yr at fixed τ = 2200 yr, solved in closed form (the reservoir ramp keys off
GMT, not the regional driver, so its contribution is exactly linear in ψ — no scan).

**Three findings.**

1. **ψ is invariant — 1.01× across a 1.48× amp spread.** The base's own 2250-2300 rate
   is 2.6–2.9 cm/century against a 26.5 target, so the reservoir supplies ~90 % of it
   under every law and the amp cannot move what is already nearly dead.
2. **The LEVEL requirement is not invariant, and that is the real caveat.** Base 2300
   moves 49.9 → 38.1 cm (1.31×), so the level/rate agreement cell B rests on degrades
   **0.97× → 1.19×**. One flux satisfies both requirements under `held` and `full`;
   under the two lower-amp laws it no longer quite does.
3. **Exactly hindcast-inert.** The bisected rate scale is identical to all printed
   digits across all four laws (1.015246, spread **1.000000×**) — the driver is observed
   south-Greenland T through 2024 and only spliced after. **Sub-choice 1 of
   `ladrillo_gis_amp` stays revisable at projection time with no refit.**

**§1.1 confirmed and now quantitative:** the φ=1 ceiling ratio on the warm arms stays
above 1 under every law, **1.93×–3.81×**. The parent handoff predicted 2.41 → ~3.4;
`decl` (3.81) and `summer` (3.23) bracket it. ⚠ **The summer law pushes ssp126 r2300 to
1.11×**, so "the cool arms are at or above their ceiling" is amp-law dependent in a way
the warm-arm reading is not.

**Where the evidence stops:** CMIP6 has ≥20 models only to **4.75 K** and any models
only to **5.75 K**. Our ssp585@2300 (7.81 K) is **1.4× beyond any data**; the x2300 arm
(13.63 K) is **2.4× beyond**.

---

## 2. STAGES 1a + 1b (`python/scope_gis_reservoir_rate_rank.py`)

1080 cells = the shipped 216 × a 5-point `RAMP_W_K` axis. Two gates: the
w-parameterised ramp is **bit-identical** to the shipped one at w=1, and the w=1 slice
reproduces the shipped **(135 all_pass, 86 also clearing both 2150 bands) exactly**.

### 2.1 Stage 1a — **STOP**, and the verdict had to be taken off the level score

| w (K) | pass_2150 | + r2300 rate | best rms_all | τ of best |
|---|---|---|---|---|
| 0.5 | 81 | 3 | 0.2992 | 400 |
| **1.0** | **86** | **4** | 0.3015 | 800 |
| 2.0 | 95 | **0** | 0.2911 | 800 |
| 4.0 | 117 | **0** | 0.2836 | 400 |
| 8.0 | 147 | **0** | 0.2807 | 400 |

Widening the ramp improves `rms_all` by **1.074×**, so an `rms_all`-only reading returns
GO. But `rms_all` is a **LEVEL** score and the criterion the model *fails* is the
**RATE**: passing cells go **4 → 0** for every w > 1, and every w>1 winner sits at
**τ ≤ 400 yr** against the equilibrium literature's 2–3 kyr. Since `RAMP_W_K` **is** a
common-τ ladder's `v(θ)` half (parent §2 identity), **a ladder cannot pay for its extra
parameters either. Do not build N>1.**

### 2.2 Stage 1b — the criterion is powerful, and it re-opens the selection the *other* way

| criterion | cells |
|---|---|
| 2100 + 2300 bands + shape + inventory | 740/1080 |
| … + both ssp585 2150 bands | 526 |
| … + the **r2300 rate band** | **7** |
| … + the **x2300 rate band** | **0** |

**0/1080 on x2300 confirms parent §3.1 over the full grid** rather than by argument.
The 7 survivors carry **ψ 0.094–0.125 cm/yr**, and the re-ranked winner is
**V=1 m / onset 4.69 K / τ=800 yr — cell A.**

**Why this differs from §1.2, and neither is wrong:**

* **POINT vs BAND.** Cell A's 12.0 cm/century is **2.2× below the PROTECT median 26.5**
  (§1.2's demotion) and **inside the run-level band 9.7–41.5** (this scan's winner).
  The band spans **4.3× on 35 runs that are only 5 GCM clusters**; the clustered band
  (11.6–36.9, 3.2×) still holds both cells. ⇒ **the rate criterion narrows the set hard
  but does not pin ψ to better than ~2×.** §1.3's "the rate criterion identifies the
  flux" holds against the **median**, not the band.
* **THE INVENTORY CEILING EXCLUDES CELL B, and this is the wiring statement.**
  `ψ = 100·V/τ`, so a hard cap on V is a τ-dependent cap on ψ:

  | τ (yr) | ψ_max at V_MAX = 2.73 m | × short of 0.273 |
  |---|---|---|
  | 800 | 0.341 | 0.80× |
  | 1600 | 0.171 | 1.60× |
  | **2200** | **0.124** | **2.20×** |
  | 3200 | 0.085 | 3.20× |

  **At the handoff's own τ the high basin cannot supply the handoff's own flux, short by
  2.2×.** Cell B is not merely outside this grid — it is outside the high basin. The flux
  and the literature τ *together* force a whole-sheet object.

### 2.3 §1.3 confirmed, with its domain measured

Within one ψ, `rms_all` varies by **≤2.872× over all τ**, **≤1.244× at τ≥800**, and
**≤1.150× at τ≥800 with w fixed** — exactly as the O((s/τ)²) curvature argument
requires. **The degeneracy is a long-τ statement, not a property of the grid.**

---

## 3. TWO CHOICES FLAGGED, NOT RESOLVED — both are Marcus's call

1. **Rate-band basis.** Built **run-level** to match how the shipped LEVEL bands are
   built, which makes it the *narrower* and therefore *stricter* of the two.
   `RATE_BAND_BASIS` switches it to GCM-clustered; both are printed. A run is one of 5
   percentile variants of a GCM × RCM pair, so the honest n is 5, not 35 — the same trap
   the parent handoff's §7 flags for "35/35 runs".
2. **Promotion.** Both new files write their own CSVs;
   `scope_gis_reservoir_offline.py` and `outputs/scope_gis_reservoir_offline.csv` are
   **untouched**, because folding the rate criterion in would overwrite the provenance
   for 86/216 and for the shipped cell's selection. **Promotion moves a cell.**

---

## 4. WHAT THIS CHANGES ABOUT THE DELIVERABLE

The parent handoff's quotable result was *"a sustained flux ψ ≈ 0.27 cm/yr opening
above ~4.7 K, with (V, τ) by prior."* After this session:

* **The ψ ≈ 0.28 number is robust to the amplification question** — that was the stated
  blocker and it is discharged.
* **But ψ ≈ 0.27 and "a high-basin tap" are not simultaneously available.** Either the
  flux is charged to the whole sheet (V ≈ 6 m at τ = 2200), or the high basin caps it at
  **ψ ≤ 0.124** and the model lands on cell A's ψ ≈ 0.125 with a 2250-2300 rate at the
  **bottom** of the PROTECT band rather than at its median.
* **The x2300 arm is untouched by any of this** — 0/1080 cells, exactly as §3.1 said.

## 5. NEXT

1. **§4.1, the NPV sensitivity to τ** — still unrun, still the cheapest item, and it may
   retire the τ question outright.
2. **Decide the two flagged choices in §3.** The band basis changes how many cells pass;
   the promotion decision moves a cell.
3. **Decide whether the flux is a high-basin or whole-sheet object** (§2.2). This is now
   the fork, and it is a physics/wiring call, not a scan call. Stage 2 of the parent
   handoff (pricing the reservoir against a convex slow-channel `L_eq` for x2300) should
   wait on it, because a whole-sheet reservoir re-opens the capacity clamp.
