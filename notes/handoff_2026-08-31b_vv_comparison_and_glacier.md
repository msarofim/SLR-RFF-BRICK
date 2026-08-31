# Handoff — the two van Vuuren NEXT items are done, and one headline needed a different statistic

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, commits `2459ab1` and `d9e5e8e`.
Written 2026-08-30 (session date) picking up cold from
`handoff_2026-08-31_vanvuuren_cubes.md`, whose §6 NEXT list this closes. That handoff's §4
(`ais @2300` over CONTROL tolerance) and the five `[MARCUS —]` placeholders are UNTOUCHED and
still the open items.

---

## 0. VERIFIED FIRST, AS §5 ASKED

All 7 Ladrillo runs present, all `PAIRING` PASS + `SUM` PASS + `[CONTROL] SKIPPED`, 841 configs
each. All 7 BRICK 2.0 (`oldbrick`) runs present. **Both models' `draw -> config` permutations agree
element-wise**, which is now gated rather than assumed.

---

## 1. `python/vv_model_comparison.py` — the SIBLING, not a flag (commit `2459ab1`)

Two sources x seven markers. `ladrillo_model_comparison.py` stays four-sources-x-three-SSPs. The
banner prints WHY MAGICC-SLR and FACTS are absent, so an empty column can never be read as "no
data" when the truth is "not drivable".

Writes `outputs/vv_model_comparison_L21{,_width,_gmst,_pathdep}.csv`.

**Gates, all four mutation-tested and caught** (gates file deleted / a verdict flipped to CHECK /
the CONTROL row removed / one config id altered; fixtures restored bit-identical):
a missing gates file is a FAILURE not a skip, and the pairing gate compares the two drivers'
permutations element-wise — because a width ratio between arms that saw different forcing subsets
means nothing.

### ⚠ THE PATH-DEPENDENCE HEADLINE NEEDED A DIFFERENT STATISTIC

The previous handoff's §5 reported High-to-Low EXCEEDING High at 2100 by **+3.02 cm** and called it
"THE RESULT THAT JUSTIFIES THE WHOLE EXERCISE". It was a BRICK 2.0 **median** difference, written
before the Ladrillo runs finished. On medians **Ladrillo says the opposite: −4.90 cm.**

**The disagreement is the STATISTIC, not the models.** Both markers run the same `PAIR_SEED = 2026`
permutation, so draw *k* is the same posterior draw under the same FaIR config in both files — the
difference is PAIRED and most of the spread cancels. Clustered to the 841 configs:

| @2100 | Ladrillo paired | BRICK 2.0 paired | Lad median | B20 median |
|---|---|---|---|---|
| ais | **+0.537 ± 0.110** | **+1.237 ± 0.173** | −6.47 | +3.01 |
| te | **−0.745 ± 0.028** | **−0.699 ± 0.028** | −0.94 | −0.98 |
| total | −0.254 ± 0.158 | +0.642 ± 0.195 | −4.90 | +2.62 |

* **AIS is POSITIVE in BOTH models, at 4.9σ and 7.1σ.** High-to-Low's EARLIER warming (warmer than
  High ~2040-2090, +0.18 K at 2073) leaves more ice-sheet response at 2100 though it ends 5.3 K
  cooler. **The signal is real and REPLICATES across two independent ice-sheet modules — a stronger
  claim than the median version ever made.**
* **TE is negative in both and near-identical between them** (they share the OHC forcing).
* ⚠ **The NET is the small residual of two larger opposing terms, so its SIGN is model-dependent.**
  Quote the COMPONENT SPLIT, never the total.
* **Why the median fails here:** Ladrillo's AIS@2100 is a tipping distribution and q50 lands in the
  sparse valley between its modes — **q25 −0.32, q50 −6.47, q60 −0.25 cm**. A 6 cm excursion
  bracketed by 0.3 cm either side is the median falling into a hole in the density. Tipping
  fractions say it directly: **AIS@2100 > 30 cm in 30.1% of HL draws vs 24.2% of H.**
* **2100 is the ONLY readable horizon.** At 2150/2300 every component is strongly negative in both
  models once the endpoint gap dominates.

### The under-dispersion, now a seven-point gradient

Ladrillo/BRICK 2.0 p05-p95 width ratio, total: **0.26-0.34** at the three cool-peaking markers,
0.67-0.83 mid, **0.95-1.17** at Medium/High. Componentwise **almost entirely AIS** (0.06-0.12 cool
vs 0.63-1.06 warm); **TE is flat at 0.79-1.02 across all seven** and glaciers 0.96-1.09 at 2100.
Spearman vs PEAK **+0.93**, vs ENDPOINT **+0.64** — ⚠ **n = 7, a direction, NOT a test.**

---

## 2. The glacier commitment figure, moved to van Vuuren (commit `d9e5e8e`)

`--set=ssp|vv` on both `project_ssps_gsic_2300{,_mengel}.jl`; scenario list, output stem and spread
pair all from one `SCEN_SETS` entry. Stem is `vv_gsic_2300`, NOT `ssps_gsic_2300_vv`. Drawn by
`python/plot_vv_gsic_wr_vs_mengel.py` -> `figures/vv_gsic_wr_vs_mengel_2300.png`.

**THE REFACTOR IS PROVABLY INERT** — `--set=ssp` on both drivers reproduces all three committed SSP
outputs **bit-identically**.

* Four decline pathways at four PEAK levels (1.76/1.90/2.37/2.96 K) vs ssp119 alone.
* **Low-to-Neg returns to +0.29 K and Wigley-Raper still adds +9.74 cm over 2100→2300.**
* ⚠ **The WR melt rate at 2300 is NOT monotone in endpoint warming — that is the MECHANISM.** Very
  Low (1.20 K) is FASTEST at **4.75 cm/century**; High (6.66 K) SLOWEST at **0.23**. High has
  exhausted its reservoir; Low-to-Neg (1.69) has dropped toward `teq` so `dV/dt ∝ (T − teq)` shuts
  down. **The commitment signal is strongest in the MIDDLE** — worth saying out loud in any caption,
  because "cooler ⇒ less melt" is the natural misreading.
* **The mixed-vintage caveat DISSOLVES** (all 7 from one build, driver commit `6cc34b6`), so panel
  (c) carries no dagger. The gate ASSERTS "all seven share ONE commit" instead of declaring a mix.

### ⚠ A gate defect found by mutation-testing, fixed in BOTH figures

Pointing one marker at an SSP driver put a **1.4074 K** delta on EVERY arm and the vintage gate
still printed *"all 3 ARMS share a forcing vintage"* — **it compares the arms against each other and
is blind to all of them being stale together**; only the provenance gate caught it. An ABSOLUTE
check now runs beside the spread test in the van Vuuren figure AND in the SSP figure, which had the
identical blind spot. Both measure 0.0000 K today, so it is inert now. Mutation-tested in turn.

---

## 3. PRE-EXISTING, found here, NOT fixed here

`data/observations/fair_mean_*.csv` carries a **2301** row that the per-config cube does not —
the builder's `END_YEAR = 2301` / `CUBE_LAST_YEAR = 2300` (FaIR timebounds run one past the last
timepoint), identical on the SSP means, so not a van Vuuren defect. But 2300 is the ratified end
year and Medium/High are still rising, so an unclamped peak search reports "peak @2301".
`vv_model_comparison.py` clamps to 2300; **the asymmetry itself is untouched** — worth a decision
about whether the mean files should be truncated at build time.

---

## 4. FOR MARCUS — three decisions, none taken here

1. **`ais @2300` CONTROL exceedance** (−0.518 cm vs `CONTROL_TOL_CM = 0.5`), carried over from the
   previous handoff §4. Still open: is the tolerance wrong, or the cross-driver gap? AIS@2300 is a
   headline number in the model document.
2. **The path-dependence claim as it will be WRITTEN.** The defensible sentence is about the
   COMPONENT SPLIT (AIS + vs TE −, replicated in two models), not about High-to-Low's total
   exceeding High's. If the total is wanted, it needs the model-dependence stated with it.
3. **`INDEX_slr.md` is 15.6 KB against a 14 KB soft budget** (it was already 15.4 KB before this
   session). Under the 18 KB hard ceiling, so no restructure is forced — flagging it per the rule.

The five `[MARCUS —]` placeholders remain the model document's only blocker.
