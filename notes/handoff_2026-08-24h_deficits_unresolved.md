# Handoff — the curvature arc closes: all three deficits are UNRESOLVED, and the bar was never ours

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, commit **`c4f63b6`** and the
CHANGELOG entry `2026-08-24o`. Written 2026-08-24, to be picked up cold. **Continues**
`handoff_2026-08-24g_lws_grace_extension.md`, whose §7 open items **1 and 2 are now CLOSED**;
items 3-7 are unchanged and re-ranked in §7 below.

**One chain read** (2000 draws x 4 seeds, ~25 min). Everything else is arithmetic.

---

## 0. THE ONE-PARAGRAPH VERSION

`-24f` §9 item 1 asked whether the three deficits that started this whole arc survive an error
bar, and warned that if they are 1 σ effects the conclusion changes *"from 'explained by the
reconstruction gap' to 'never measurable in the first place'."* **It is the second branch.**
gis **0.629× = −0.27 σ**, ais **0.727× = −0.37 σ**, total **0.571× = −1.39 σ**, and none crosses
2 σ even on the *least* conservative bar the gate permits. The reason is not that our model is
uncertain — it is the opposite. **Our posterior is up to 27× TIGHTER than the observation's own
bar**, so *all 2000 draws sit below observed* and *the difference is 0.27 σ* are both true at
once. Item 2 closed on the way: the GIA conventions **do** differ (Caron-2018 vs ICE-6G_D) and
the mismatch is **0.024 mm/yr**, 0.6% of the LWS trend.

---

## 1. WHAT WAS BUILT

* `julia/diag_curvature_deficit_2x2.jl` — **extended additively.** It ran 2000 draws and then
  collapsed them to a **median trajectory** before measuring, so the model's posterior width
  never reached the ratios. It now also writes `outputs/diag_curvature_deficit_perdraw_L14.csv`
  (per-draw rate + accel + originating chain, on the **same** per-series window). **`OUT` is
  untouched** and two gates say so.
* `python/diag_curvature_deficit_errorbar.py` — 6 blocks, ~40 s, no chains.
  Outputs `outputs/diag_curvature_deficit_errorbar_{summary,ratio,chain}_L14.csv` + its log.

**Gates, all passing and all worth keeping:**

* **[IDENT]** (Julia) the shipped panel reproduces at **0.000e+00** — the per-draw addition is
  provably additive. **[IDENT]** (Python) the obs accel reproduces the shipped panel exactly.
* **[SHIFT]** rate and accel are shift-invariant to **2.6e-17** under a +7.3 cm offset — which
  is *why* the per-draw path can skip the median path's baselining rather than reproduce it.
* **[SE-MC]** the analytic AR(1) se is required to be **conservative** against a matched Monte
  Carlo; it is, at **1.05–2.73×**.
* **[EXCH]** a permutation test on the between-chain median range (§5).

---

## 2. THE ANSWER

| component | shipped | ours med | **[A] our sd** | obs | z_A (model-only) | **z_B** | z_BC | z_MC | verdict |
|---|---|---|---|---|---|---|---|---|---|
| **gis** | 0.629× | +0.000918 | **0.000074** | +0.001458 | **−7.3** | **−0.27** | −0.27 | −0.74 | **UNRESOLVED** |
| **ais** | 0.727× | +0.000585 | 0.000260 | +0.000826 | −0.9 | **−0.37** | −0.35 | −0.45 | **UNRESOLVED** |
| **total** | 0.571× | +0.005178 | 0.000393 | +0.009093 | **−10.0** | **−1.39** | −0.95 | −1.67 | **UNRESOLVED** |
| gsic_hind | 3.086× | +0.001362 | 0.000295 | +0.000436 | +3.1 | +2.87 | +1.64 | +2.89 | BAR-DEPENDENT |
| te | 3.624× | +0.001488 | 0.000070 | +0.000411 | **+15.4** | +1.16 | +1.03 | +1.27 | UNRESOLVED |

cm/yr², 1993–2024 (gsic 1993–2023 — its target ends 2023).

**Three bars, and the verdict survives all of them.**
**[A]** our per-draw posterior spread — the bar item 1 asked for.
**[B]** the AR(1)-inflated OLS se of 2·b₂, **transcribed** from
`diag_curvature_postsplice_halving.py` so these numbers compose with `-24f` §6.
**[C]** the targets' published `_lo`/`_hi`, **bracketed** by the perfectly-correlated arm (a
common z — non-zero, because these bands *pinch* near 2019 and so carry their own curvature)
and the perfectly-independent arm. `z_MC` re-runs everything on the **least** conservative bar
`[SE-MC]` permits: gis 0.27 → 0.74, total 1.39 → 1.67. **Nothing crosses 2 σ.**

---

## 3. THE THING TO ACTUALLY REMEMBER — the bar is OBSERVATIONAL

For Greenland our posterior sd is **0.000074** against an observational bar of **0.001969**:
**27×**. Our acceleration is *extremely* well determined; the **31-year observed** acceleration
is not. That makes two readings that look contradictory both true and compatible:

* **All 2000 draws** sit below observed for `gis` and `total` (obs percentile **100.0%**), and
  `z_A` — the same difference over our posterior sd *alone* — is **−7.3** / **−10.0**.
* Against the observation's own bar it is **0.27 σ** / **1.39 σ**.

⇒ *The deficit is enormous against the MODEL's width and invisible against the OBSERVATION's.*
**The second governs**, because the comparison being made is model-vs-observation. Print `z_A`
and `z_B` side by side or the next reader will re-derive the wrong one.

⚠ **The AR(1) inflation is not a formality.** The Greenland residuals carry **ρ = +0.918**
(inflation **4.83×**), ais +0.718, total +0.638. A cumulative series' residuals about a
quadratic are strongly persistent **by construction** — never quote a bare OLS se on one.

---

## 4. TWO ESTIMATOR CHOICES THAT DID NOT MATTER, AND ONE OBJECT THAT IS SIMPLY WRONG

* **accel(MEDIAN trajectory) vs median(accel per draw)** — a choice never previously flagged.
  Measured: **≤2.68%** (ais), 0.23% (total), **0.10%** (gis). **Immaterial**, both are carried.
  Check it, don't assume it.
* **The RATIOS cannot carry a band at all.** Scored by Monte Carlo — never by dividing two
  bands' endpoints — the **denominator changes sign** in **9.8%** (ais), **23.0%** (gis),
  **34.6%** (te) of draws. `total` is the only row under 2% (1.29%) and its band is still
  **[0.276, 2.874]**, 1.0 comfortably inside. ⇒ **The DIFFERENCE carries the verdict. A ratio
  is the wrong object for this comparison and always was.**

---

## 5. [EXCH] — and it makes the verdict STRONGER, not weaker

A permutation test on the between-chain median range, reported in **cm/yr²** rather than as an
R-hat column: pool the draws, relabel them at random, recompute the 4 chain medians, 4000 times.

| component | chain-median range | × the null | p | |
|---|---|---|---|---|
| **ais** | 0.000312 | **10.0×** | **0.0000** | **NOT MIXED** |
| **total** | 0.000305 | **7.7×** | **0.0000** | **NOT MIXED** |
| gis | 0.000016 | 2.2× | 0.0070 | NOT MIXED |
| gsic_hind | 0.000023 | 0.9× | 0.6192 | mixed |
| te | 0.000009 | 1.3× | 0.2015 | mixed |

⚠ For `ais` and `total` the **[A]** bar is therefore **UNDER**-stated — which only strengthens
UNRESOLVED. Consistent with the known `ais_iceflow0` R-hat **2.244**.

---

## 6. ITEM 2 CLOSED — the GIA convention, with a number

**The conventions DO differ.** JPL mascons remove GIA with **ICE-6G_D** (Peltier et al. 2017).
**Frederikse 2020** uses the **Caron et al. 2018** ensemble — one prediction drawn per member
from **128,000**, likelihood-weighted by GNSS vertical velocities and palaeo sea level (Methods,
"Contemporary mass redistribution"). They ran **ICE-6G_D (VM5a) as an explicit sensitivity**
(Extended Data Fig. 5) and report basin-mean sea-level GIA differences up to **0.3 mm/yr**,
inside their own CI. Their 2003–2018 mass term is the **same JPL RL06 solution we used**.

| 2003–2018 LWS trend | |
|---|---|
| ours (GRACE, ICE-6G_D) | **+0.3600 ± 0.0872** cm/decade |
| Frederikse (Caron 2018) | **+0.3843 ± 0.0875** cm/decade |
| **difference** | **−0.0242 ± 0.0111** cm/decade = **2.19 σ** = **0.024 mm/yr** |

⇒ **0.6% of the LWS trend, ~1/12 of the paper's own basin-scale figure. Does NOT gate the
post-2018 LWS trend. Flag closed.**

⚠ **Two traps.** The **level** agreement is *by construction* —
`build_lws_grace_extension.py:86` offset-matches over exactly this window — so only the
**TREND** is informative. And **0.024 mm/yr is an UPPER BOUND** on the GIA effect: glacier
partitioning (their Parkes-based splitting vs our GlaMBIE subtraction) and mascon leakage
handling are lumped into the same difference.

---

## 7. OPEN, IN PRIORITY ORDER

1. **The reconstruction mixing** (was `-24g` item 3) — real, Marcus's call, and **§2 above
   demotes it further**: at these window lengths the estimator resolves nothing either way, so
   the choice cannot be justified by "it will fix the deficit". There is no deficit to fix.
2. **The anchored net's counterintuitive sign** at ssp585 @2300 (`-24e` §8 item 2) — contrast
   0.249, unexplained. The per-draw table is on disk; joining parameters needs a cheap
   column-only chain extraction, **not** the 12-min diagnostic read.
3. **Wire the LWS GRACE extension into `prep_recalib_targets_ext.py`** — still deferred by
   Marcus ("wait until we have something else worth recalibrating"), and §6 removes the last
   technical objection to doing so. ⚠ **`lws_lo`/`lws_hi` must be replaced at the same time.**
4. **Widen the hindcast-vs-projection independence measurement** to the whole `S.ais` 1900–2018
   stream (`-24e` §8 item 3). Needs model runs.
5. **`ais` chain mixing** — NEW, promoted out of §5. The AIS chains are 10.0× the permutation
   null on a quantity we report. `-24k` established the *projection* converges (ssp585 AIS@2300
   R-hat 1.026) and that the lever is proposal scaling; this is a second, independent
   measurement pointing the same way.
6. **Re-read the other shipped Antarctic headlines at 2100/2150** (`-24e` §8 item 4), in
   particular `UNRESOLVED_AMPLIFICATION`'s λ = 0.014280.
7. **The AIS observed driver**, **FrEDI linearity**, **Marcus's prose** — unchanged.

---

## 8. NON-OBVIOUS STATE

* `diag_curvature_deficit_2x2.jl`'s **[IDENT]** gate reads the prior panel **before**
  `CSV.write` overwrites it (`const REF`, near `const TGT`). Move that read and the gate
  silently compares the file to itself.
* **[IDENT] is reported but NOT asserted under `--maxrows`** — a SMOKE reference on disk was
  written at whatever row count was in force then. Only the full run gates.
* `SE_MC_SEED = 2026`, `SE_MC_N = 20000`, `PERM_N = 4000`, `RATIO_MC_N = 200000` are **gate
  parameters, not tuning knobs**.
* The per-draw path deliberately **omits** the median path's `- s[i0]` baselining. That is
  licensed by **[SHIFT]**, not by inspection — if either statistic is ever changed to something
  shift-*variant*, [SHIFT] fails first and correctly.
* Every trap in `-24g` §4/§6, `-24f` §8, `-24e` §7, `-24d` §4, `-24c` §4 and `-24b` §3 still
  applies. **No recalibration was run; `outputs/recalib_targets_ext.csv` is UNCHANGED** and
  still carries the LWS hold-flat fiat.

---

## 9. FILES AND COMMITS

**New:** `python/diag_curvature_deficit_errorbar.py`,
`outputs/diag_curvature_deficit_perdraw_L14.csv`,
`outputs/diag_curvature_deficit_errorbar_{summary,ratio,chain}_L14.csv`,
`outputs/log_curvature_deficit_errorbar_L14.txt`.
**Modified:** `julia/diag_curvature_deficit_2x2.jl` (additive), `CHANGELOG.md` (`2026-08-24o`),
`outputs/log_diag_curvature_deficit_2x2.txt`. `diag_curvature_deficit_2x2_L14.csv` is
**byte-identical** — that is the [IDENT] gate, visible in `git status`.
**Memories:** `deficits_are_unresolved` (new), `gia_convention_bounded` (new);
`curvature_deficit_is_recon_gap`, `gis_obs_accel_deficit` and `ais_curvature_deficit_shared`
**revised** — the latter two now carry a RETIRED-AS-AN-EFFECT banner; `INDEX_slr.md` two lines
rewritten + two added; `MEMORY.md` SLR live-state and working-conventions lines extended.
**Commits:** `c4f63b6`, and this note.
