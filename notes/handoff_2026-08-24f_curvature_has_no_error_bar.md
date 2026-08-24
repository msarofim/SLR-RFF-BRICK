# Handoff — the post-splice halving is half fiat and not resolvable, and the whole curvature arc has been running without error bars

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, commits **`306b348`** (the
diagnostic), **`28240c7`** (CHANGELOG `2026-08-24m`) and **`d219b76`** (this note). Written 2026-08-24,
to be picked up cold. **Continues** `handoff_2026-08-24e_items4and5_closed.md`, whose §8 open
item **1 is now half-closed and half-REFRAMED**. Everything in `-24e` §1–§7 stands unchanged.

**No chains were read.** This is target-side arithmetic on `outputs/recalib_targets_ext.csv`
and `data/observations/frederikse2020_gmsl_total.csv`. Runtime ~4 s.

---

## 0. THE ONE-PARAGRAPH VERSION

I set out to settle the flag carried since `-24d` §1 — *"real post-2018 slowdown vs splice
artifact: NOT established"* — and it settles as **both, in a 52/48 split, and neither is
resolvable**: LWS's hold-flat is charged **52.3%** of the drop, the independent Dangendorf
total decelerates too, and **the drop is 1.78 σ (p 0.073)**. On the way, three things that were
not the question turned out to matter more. **The shipped window label is wrong** — 0.003533 is
**1993–2023**, not 1993–2024, because `gsic` ends 2023. **"Dangendorf's acceleration is 1.83×
Frederikse's" is a one-window artifact of a noisy denominator** — sweep the start year and the
ratio spans 0.53–1.53, the difference changes sign, and Dangendorf is *lower* in **10 of 13**
windows. And **nothing in this arc has ever carried an error bar**: with one attached, the 1.3%
closure is **0.02 σ with a bar 78% of the value being closed**, the 1.83× is **0.97 σ**, and the
"agrees to 5%" pre-check is precision the data cannot support.

---

## 1. WHAT WAS BUILT

`python/diag_curvature_postsplice_halving.py` — eight numbered blocks, three gates, ~4 s, no
chains. Outputs `outputs/diag_curvature_postsplice_{decomp,arms,windows,recon,sweep,se}_L14.csv`
and `outputs/log_curvature_postsplice_L14.txt`.

**Gates, all passed and all worth keeping:**

* **[IDENT]** reproduces the shipped **0.007189** / **0.003533** cm/yr² exactly. The estimator is
  transcribed from `julia/diag_curvature_deficit_2x2.jl:84`, not reinvented, so every number here
  is on the same estimator as the 0.65× / 0.727× deficits.
* **[LINEARITY]** `accel(Σ components) == Σ accel(component)` to **3.6e-17**. OLS on a fixed
  design is linear in the response, so §3's decomposition is an **identity**, not an
  approximation — that is what licenses charging one component a share of the drop.
* **[SE-MC]** the analytic error bar is checked against a matched AR(1) Monte Carlo on the same
  design (20 000 draws, fixed seed) and **required to be conservative**: 1.10× / 1.03× / 1.22×.
  Without this the §6 verdicts would rest on a rule of thumb.

---

## 2. [WINDOW] THE SHIPPED LABEL IS WRONG, AND IT TRAVELLED

**`0.003533` is 1993–2023, NOT 1993–2024.** `gsic` ends **2023**, so the five-component sum has
no 2024 value at all and `accel_of` returns NaN there — correctly, because it NaNs on any missing
value inside the window rather than silently dropping a component. The wrong label is in
`handoff_2026-08-24d` §1, `handoff_2026-08-24e` §8 and a CHANGELOG entry.

*This is only detectable because the estimator refuses to average over a hole.* An estimator that
dropped the NaN would have returned a four-component number under a five-component label.

---

## 3. THE DECOMPOSITION — LWS IS CHARGED HALF THE DROP

sum5 **+0.007189 → +0.003533**, drop **−0.003655**, ratio **0.492 (= 1/2.03)**.

| component | 1993–2018 | 1993–2023 | delta | share of drop |
|---|---|---|---|---|
| `lws` | +0.001925 | +0.000013 | −0.001912 | **+52.3%** |
| `gis` | +0.003786 | +0.001764 | −0.002023 | **+55.3%** |
| `ais` | +0.002076 | +0.001032 | −0.001043 | +28.5% |
| `gsic` | +0.000205 | +0.000436 | +0.000231 | −6.3% |
| `steric` | −0.000804 | +0.000288 | +0.001092 | −29.9% |

`prep_recalib_targets_ext.py:311` holds LWS **exactly constant** at its 2018 value from 2019.
A series held flat inside a fitted window is not missing data — **it is a measurement the fit
believes**, and it pulls the quadratic term down mechanically.

---

## 4. BOTH HALVES ARE REAL, AND THE FIAT IS BOUNDED

* **The independent total decelerates too.** Dangendorf 2024 + NOAA STAR is not built from our
  components, carries no LWS construction, and is real data across both windows: ratio **0.729**.
  With **LWS removed from both windows** the component sum's ratio is **0.669**, against **0.492**
  as shipped. Deceleration is in the observations.
* **The fiat is worth 0.001912 cm/yr² = 52.3% of the drop.** LWS counterfactual arms move the
  1993–2023 value +0.003533 → **+0.004317** (linear continuation of 1993–2018) → **+0.005445**
  (quadratic). ⚠ **These are extrapolations, not data.** No post-2018 TWS product is on disk —
  Frederikse's ends 2018 and IGCC 2024 carries no land-water term — so the arms bound the
  artifact's size and cannot be quoted as a measurement.
* **Matched-length windows INVERT the worry.** A longer window sees more of the curve, so the
  drop could have been a window-length effect. It is the opposite: 1993–2018 vs **1998–2023**
  (both 25 yr) gives sum5 **+0.007189 → +0.000372** and dang **+0.013350 → +0.007168**. The
  extended-window comparison *understates* the recent deceleration.
* ⚠ On that matched window `dang/sum5` reaches **19.26** — purely a collapsed denominator. The
  **difference** moves only **1.10×** across all three windows. Quote the difference
  (`ratio_needs_its_base`).

---

## 5. THE 1.83× DOES NOT SURVIVE ITS OWN WINDOW

Sweeping start years over windows **ending 2018** (both reconstructions real throughout, no LWS
fiat inside any of them — pure reconstruction vs reconstruction):

* the ratio spans **0.53–1.53**;
* the difference **changes sign**;
* **Dangendorf's acceleration is LOWER than Frederikse's in 10 of 13 windows**;
* Frederikse's own total accel swings **3.7×** (to **+0.023315** at 1998–2018).

**Why.** Frederikse's *total* is an observed GMSL reconstruction and carries **2.8× the
year-to-year scatter** of either smooth series — first-difference sd **0.674 cm** against
**0.244** (our component sum) and **0.252** (Dangendorf). A 26-year quadratic coefficient on that
series is noise-dominated, and the **1.83× sat on a spike in its denominator**.

⚠ **A hypothesis I formed and killed in the same test.** Three nested windows showed the
`dang − sum5` difference nearly constant (1.10× spread) against a ratio spanning 1.86 → 19.26, so
I proposed the gap was an **additive** acceleration offset rather than a factor. The sweep
**refutes it**: the difference changes sign across windows. Neither framing describes the gap.
Had I stopped at three nested windows, "the gap is a constant +0.0062 offset" would have shipped.

---

## 6. THE HEADLINE — NOTHING HERE IS RESOLVED AT 2σ

AR(1)-inflated OLS se of 2·b₂. **A lower bound**: it counts only scatter about the quadratic and
**not** the reconstructions' own published bands, so every verdict below is conservative.

| series | 1993–2018 | se | σ |
|---|---|---|---|
| our 5-component sum | +0.007189 | 0.002648 | 2.71 |
| Frederikse's own total | +0.007285 | 0.004932 | **1.48** |
| Dangendorf total | +0.013350 | 0.003870 | 3.45 |

| claim the arc rests on | difference | σ | verdict |
|---|---|---|---|
| "the components close on their own total to **1.3%**" | −0.000096 ± 0.005598 | **0.02** | UNRESOLVED — bar is **78%** of the value being closed |
| "Dangendorf is **1.83×** Frederikse" | +0.006066 ± 0.006269 | **0.97** | UNRESOLVED |
| "our sum falls short of Dangendorf" | −0.006162 ± 0.004689 | **1.31** | UNRESOLVED |
| the **halving** itself (nested-window null) | +0.003655 | **1.78** (p 0.073) | not resolved |

The halving is **1.44 σ** with LWS removed and **1.43 σ** on the independent total.

⚠ **"Closes to 1.3%" is precision theatre.** The data are equally consistent with agreement and
with a 78% disagreement. A small percentage difference between two noisy estimates is not
evidence of agreement — and this one was load-bearing.

---

## 7. WHAT THIS DOES TO OPEN ITEM 1's FIRST HALF (Marcus's call)

`-24e` §8 item 1 was **blocking** on the ground that *"until this is settled no curvature score
means anything."* §6 says something stronger and more useful: **on 26–31-year windows the
estimator does not resolve the differences the arc has been reasoning about at all, whichever
reconstruction is chosen.** The mixing is still a real methodological defect and still worth
fixing — but **it is no longer the blocker**, because fixing it would move a number by less than
its own error bar.

**The methodological choice is unchanged and still yours** (score components against Frederikse's
own total, or move them onto Dangendorf). What has changed is that it is no longer urgent, and
that **whichever is chosen, curvature at these window lengths cannot carry the weight the arc put
on it.** Two better-determined alternatives exist and neither has been tried: score the **rate**
over the same windows (far better determined), or score curvature over a **longer** window where
the coefficient is actually identified.

---

## 8. NON-OBVIOUS STATE

* The estimator **NaNs on any missing value in the window, deliberately** — that is what exposed
  the 2024 label. Do not "fix" it to skip NaNs.
* `SE_MC_SEED = 2026` and `SE_MC_N = 20000` are **gate parameters**, not tuning knobs; changing
  them changes whether [SE-MC] can fail.
* The se treats the quadratic as the true model, so genuine higher-order structure is counted as
  noise. That **inflates** the bar — the same direction as the "lower bound" caveat, so the
  UNRESOLVED verdicts hold either way.
* §6's contrasts add the two ses **in quadrature**, i.e. treat the two reconstructions as
  independent. A shared-method correlation would only **shrink** the bar; it is flagged in the
  file rather than modelled (`shared_method_error`).
* [8]'s null generates AR(1) noise on the **whole** 1993–2023 span and differences the two nested
  sub-window estimates, so the correlation between them is handled by construction. The [7] bars
  **cannot** be differenced to get it.
* Every trap in `-24e` §7, `-24d` §4, `-24c` §4 and `-24b` §3 still applies.

---

## 9. OPEN, IN PRIORITY ORDER

1. **NEW, and it is now the top item: re-measure the model's own deficits WITH an error bar.**
   The **0.65×** (gis), **0.727×** (ais) and **0.571×** (total) started this whole arc and their
   point values sit *inside* the bars in §6. If they are 1σ effects the arc's conclusion changes
   from "explained by the reconstruction gap" to "never measurable in the first place". Needs a
   chain read; `diag_curvature_deficit_2x2.jl` already produces the ensemble, so this is an
   error-bar pass over an existing output plus a per-draw spread.
2. **The reconstruction mixing** (`-24e` §8 item 1, first half) — still a real defect, **no longer
   blocking** (§7). Methodological choice, awaiting Marcus. Consider scoring the **rate** instead.
3. **The anchored net's counterintuitive sign** at ssp585 @2300 (`-24e` §8 item 2) — contrast
   0.249, unexplained. The per-draw table is on disk; joining the parameters needs a cheap
   column-only chain extraction (~9 GB across 4 files, rows at deterministic indices), **not** the
   12-min diagnostic read.
4. **Widen the hindcast-vs-projection independence measurement** to the whole `S.ais` 1900–2018
   stream (`-24e` §8 item 3). Needs model runs.
5. **Re-read the other shipped Antarctic headlines at 2100/2150** (`-24e` §8 item 4), in
   particular `UNRESOLVED_AMPLIFICATION`'s λ = 0.014280.
6. **The AIS observed driver**, **FrEDI linearity**, **Marcus's prose** — unchanged from `-24e`.

---

## 10. FILES AND COMMITS

**New:** `python/diag_curvature_postsplice_halving.py`,
`outputs/diag_curvature_postsplice_{decomp,arms,windows,recon,sweep,se}_L14.csv`,
`outputs/log_curvature_postsplice_L14.txt`.
**Modified:** `CHANGELOG.md` (entry `2026-08-24m`).
**Memories:** `curvature_needs_an_error_bar` (a working convention, promoted to the root index),
`postsplice_halving_priced`; **`curvature_deficit_is_recon_gap` REVISED** — its description, its
"still unquantified" bullet and a new CORRECTION section; `INDEX_slr.md` line rewritten in place
(section was at budget) and `MEMORY.md` working-conventions section extended.
**Commits:** `306b348` (diagnostic), CHANGELOG, this note.
